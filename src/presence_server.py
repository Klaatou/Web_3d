#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
presence_server - serveur de présence pour les pages générées par glb2html.

Modération : tape des commandes dans cette console (liste, ejecter, bannir, bans, debannir ; « aide » pour le détail).
Relaie les positions des visiteurs en promenade, leurs messages de chat, et les "spectateurs"
(visiteurs en vue globale qui voient les autres sans apparaître).
Noms réservés : chaque navigateur a une clé aléatoire ; le premier à prendre un nom le garde,
les suivants reçoivent "Nom#CODE" (code court dérivé de leur clé). Pas de compte, pas de mot de passe.

Installation :  pip install websockets
Lancement    :  python presence_server.py
                python presence_server.py --log presence.log --log-days 30
                python presence_server.py --cert fullchain.pem --key privkey.pem      (wss:// directement)
                python presence_server.py --proxy-header X-Forwarded-For              (derrière nginx / caddy / Cloudflare)

Journal (--log) : une ligne par évènement, dates JJ/MM/AAAA, fichier tourné chaque nuit (--log-days jours conservés).
Les adresses IP y sont masquées par défaut (--log-ip hash) ; chat et pseudos y figurent : informe tes visiteurs
et limite la durée de conservation (données personnelles).

Journal des visites (--visits, v48) : une ligne JSON par visite (salon, arrivée, durée, temps de promenade, empreinte du
navigateur ; pseudo seulement avec --visits-names ; jamais d'IP). Le créateur d'une région le consulte depuis sa page
(adresse suivie de #visits) avec la clé donnée par la commande de console « visits-key ROOM ».

Créateurs (--creators, v51) : fichier JSON relu à chaud ; chaque créateur déclare les origines de ses pages (adresses
https://nom.exemple) et un préfixe de salon (« alice. ») ; une page d'une autre origine, ou un salon hors du préfixe,
est refusée avec une raison que la page affiche. Sans --creators, tout le monde est accepté comme avant.
"""
from __future__ import annotations

VERSION = "__VERSION__"

import argparse
import asyncio
import base64
import collections
import colorsys
import hashlib
import hmac
import json
import logging
import logging.handlers
import math
import os
import random
import re
import secrets
import signal
import ssl
import sys
import tempfile
import threading
import time
import unicodedata

import websockets

# <<I18N_PY>>
def _i18n_boot():   # depuis les sources : charge src/i18n_py.py ; fabriqué par build.py (dist\) : ce bloc est remplacé par le texte de i18n_py.py avec les langues intégrées
    import importlib.util, pathlib
    here = pathlib.Path(__file__).resolve().parent
    for p in (here / "i18n_py.py", here.parent / "src" / "i18n_py.py"):
        if p.is_file():
            spec = importlib.util.spec_from_file_location("i18n_py", p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            return m
    raise SystemExit("i18n_py.py not found / introuvable")


_I18N = _i18n_boot()
_tr, i18n_add_common = _I18N._tr, _I18N.i18n_add_common
# <</I18N_PY>>

ROOMS: dict[str, dict[int, "Peer"]] = {}
HISTORY: dict[str, collections.deque] = {}
HIST_N = 0              # numéro du dernier message enregistré (croissant, repris du fichier d'historique au démarrage)
HIST_MEM = 20000        # messages gardés en mémoire par salon quand --history-file est actif (les plus anciens restent dans le fichier)
PER_IP: dict[str, int] = {}
NEXT_ID = 1
OPTS = None
REG = None
LOG = logging.getLogger("presence")


# ----------------------------------------------------------------- utilitaires
def lan_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def here(path):
    """Chemin relatif -> relatif au dossier de ce script (et non au dossier de lancement)."""
    if not path:
        return path
    path = os.path.expanduser(path)
    return path if os.path.isabs(path) else os.path.join(os.path.dirname(os.path.abspath(__file__)), path)


def clean_name(s, fallback=""):
    s = re.sub(r"[\x00-\x1f<>#]", "", str(s or "")).strip()[:24]
    return s or fallback


def clean_text(s, limit):
    s = re.sub(r"[\x00-\x1f\x7f]", " ", str(s or ""))
    return re.sub(r"\s+", " ", s).strip()[:limit]


def clean_room(s):
    s = re.sub(r"[^\w .\-]", "", str(s or "")).strip()[:64]
    return s or "default"


def norm_name(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def finite_list(v, n, lim=1e5):
    if not isinstance(v, list) or len(v) != n:
        return None
    out = []
    for x in v:
        if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or abs(x) > lim:
            return None
        out.append(round(float(x), 2))
    return out


def random_color():
    r, g, b = colorsys.hsv_to_rgb(random.random(), 0.65, 0.85)
    return (int(r * 255) << 16) | (int(g * 255) << 8) | int(b * 255)


def announced_color(v):
    """Couleur annoncée par le client dans « hello » (v33) : un entier entre 0 et 0xFFFFFF, sinon None (rejet silencieux : couleur tirée au hasard).
    Un ancien client n'envoie rien : même résultat. Les anciens serveurs ignorent simplement ce champ."""
    if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 0xFFFFFF:
        return None
    return v


class FrFormatter(logging.Formatter):
    def format(self, record):
        return time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(record.created)) + " | " + record.getMessage()


def hist_add(room, pid, name, text):
    """v37 : enregistre un message (mémoire, et fichier d'historique si --history-file). Jamais d'adresse IP. Retourne l'entrée (n = numéro, t = heure en secondes)."""
    global HIST_N
    HIST_N += 1
    now = time.time()
    e = {"n": HIST_N, "t": int(now), "id": pid, "name": name, "text": text}
    keep = HIST_MEM if OPTS.history_file else OPTS.history
    if keep > 0:
        dq = HISTORY.setdefault(room, collections.deque(maxlen=keep))
        dq.append(e)
    if OPTS.history_file:
        try:
            line = json.dumps({"n": HIST_N, "t": int(now), "d": time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(now)), "room": room, "name": name, "text": text}, ensure_ascii=False, separators=(",", ":"))
            with open(OPTS.history_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError as ex:
            LOG.warning(_tr("py.presence.history_write_error", ex))
    return e


def hist_load():
    """v37 : relit --history-file au démarrage : ignore les lignes illisibles et les messages de plus de --history-days jours (0 = tout garder), puis réécrit le fichier sans eux."""
    global HIST_N
    path = OPTS.history_file
    if not path or not os.path.isfile(path):
        return
    limit = time.time() - OPTS.history_days * 86400 if OPTS.history_days > 0 else None
    kept, total = [], 0
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                d = json.loads(line)
                n, t, room, name, text = int(d["n"]), int(d["t"]), str(d["room"]), str(d["name"]), str(d["text"])
            except (ValueError, KeyError, TypeError):
                continue
            if limit is not None and t < limit:
                continue
            kept.append((n, t, room, name, text, line))
    kept.sort(key=lambda x: x[0])
    for n, t, room, name, text, _ in kept:
        HIST_N = max(HIST_N, n)
        HISTORY.setdefault(room, collections.deque(maxlen=HIST_MEM)).append({"n": n, "t": t, "id": 0, "name": name, "text": text})
    if len(kept) != total:
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write("".join(k[5] + "\n" for k in kept))
        os.replace(tmp_path, path)
    LOG.info(_tr("py.presence.history_loaded", len(kept), total - len(kept), path))


def setup_log():
    LOG.setLevel(logging.INFO)
    LOG.propagate = False
    handlers = [logging.StreamHandler()]
    if OPTS.log:
        handlers.append(logging.handlers.TimedRotatingFileHandler(OPTS.log, when="midnight", backupCount=OPTS.log_days, encoding="utf-8"))
    for h in handlers:
        h.setFormatter(FrFormatter())
        LOG.addHandler(h)
    logging.getLogger("websockets.server").addFilter(EmptyConnFilter())


# v51 : connexion TCP ouverte puis fermée sans requête (préconnexion d'un navigateur, test de port, robot) : websockets 14 et 15
# l'écrivent en trace complète (« opening handshake failed », EOFError) ; une ligne courte au journal, au plus une par minute et par adresse
EMPTY: dict = {}         # IP -> [instant de la dernière ligne écrite, connexions vides depuis]


def caused_by_eof(exc):
    for _ in range(10):
        if exc is None:
            return False
        if isinstance(exc, EOFError):
            return True
        exc = exc.__cause__ or exc.__context__
    return False


def caused_by_header(exc):
    """v52 : requete HTTP bien formee mais qui n'ouvre pas de WebSocket (InvalidUpgrade, « invalid Connection header: keep-alive », ...) : InvalidHeader et ses sous-classes"""
    try:
        from websockets.exceptions import InvalidHeader
    except Exception:
        return False
    for _ in range(10):
        if exc is None:
            return False
        if isinstance(exc, InvalidHeader):
            return True
        exc = exc.__cause__ or exc.__context__
    return False


def conn_request():
    """v52 : (chemin, hote, agent) de la requete recue, lus dans la pile d'appels de websockets (variable connection) ; None si introuvable"""
    f = sys._getframe(1)
    while f is not None:
        c = f.f_locals.get("connection")
        rq = getattr(c, "request", None) if c is not None else None
        if rq is not None:
            try:
                h = rq.headers
                return tuple(str(v).replace("|", "/")[:n] for v, n in ((rq.path, 80), (h.get("Host", "?"), 80), (h.get("User-Agent", "-"), 100)))
            except Exception:
                pass
        f = f.f_back
    return None


def empty_conn_ip():
    """adresse de l'appelant, lue dans la pile d'appels de websockets (variable connection) ; « ? » si introuvable"""
    f = sys._getframe(1)
    while f is not None:
        c = f.f_locals.get("connection")
        try:
            ra = getattr(c, "remote_address", None) if c is not None else None
            if ra:
                return str(ra[0])[:64]
        except Exception:
            pass
        f = f.f_back
    return "?"


class EmptyConnFilter(logging.Filter):
    def filter(self, record):
        ei = record.exc_info
        if not ei:
            return True
        eof = caused_by_eof(ei[1])
        if not eof and not caused_by_header(ei[1]):
            return True              # toute autre erreur de websockets reste affichée en entier
        try:
            ip, now = empty_conn_ip(), time.monotonic()
            if len(EMPTY) > 1000:
                EMPTY.clear()
            e = EMPTY.setdefault(ip if eof else "http|" + ip, [-1e9, 0])
            e[1] += 1
            if now - e[0] >= 60:
                ipl = f"ip {ip_for_log(ip) if ip != '?' else '?'}"
                if eof:
                    log(_tr("py.presence.ev.empty"), "-", ipl, _tr("py.presence.empty", e[1]))
                else:   # v52 : requete HTTP ordinaire (navigateur qui ouvre l'adresse du serveur, robot, test) : la ligne dit laquelle
                    rq = conn_request() or ("?", "?", "-")
                    log(_tr("py.presence.ev.http"), "-", ipl, _tr("py.presence.http", e[1], rq[0], rq[1], rq[2], str(ei[1])[:100]))
                e[0], e[1] = now, 0
        except Exception:
            pass
        return False


def ip_for_log(ip):
    if OPTS.log_ip == "raw":
        return ip
    if OPTS.log_ip == "none":
        return "-"
    return hashlib.sha256((REG.salt + ip).encode()).hexdigest()[:8]


def log(kind, room, who, extra=""):
    line = _tr("py.presence.log_line", kind, room, who)
    if extra:
        line += " | " + re.sub(r"[\r\n]+", " ", str(extra))
    LOG.info(line)


class Peer:
    __slots__ = ("id", "ws", "name", "color", "p", "yaw", "last", "ip", "chat_times", "spectator", "uidh", "t0", "zone_t", "room", "color_t", "hist_t",
                 "wall0", "walk_s", "walk0", "vname")

    def __init__(self, pid, ws, name, color, ip, spectator, uidh, room):
        self.id, self.ws, self.name, self.color, self.ip = pid, ws, name, color, ip
        self.spectator, self.uidh, self.room = spectator, uidh, room
        self.p, self.yaw, self.last, self.zone_t, self.color_t, self.hist_t = None, 0.0, 0.0, 0.0, 0.0, 0.0
        self.chat_times = []
        self.t0 = time.monotonic()
        self.wall0, self.walk_s, self.vname = time.time(), 0.0, ""      # v48 : journal des visites
        self.walk0 = None if spectator else self.t0

    def walk_mark(self, walking):
        """v48 : début ou fin de promenade (temps de promenade du journal des visites)"""
        now = time.monotonic()
        if walking and self.walk0 is None:
            self.walk0 = now
        elif not walking and self.walk0 is not None:
            self.walk_s += now - self.walk0
            self.walk0 = None

    def public(self):
        d = {"id": self.id, "name": self.name, "color": self.color}
        if self.p is not None:
            d["p"], d["yaw"] = self.p, self.yaw
        return d

    def who(self):
        return _tr("py.presence.0_id_1_cle_2_ip", self.name or '(spectateur)', self.id, self.uidh[:6], ip_for_log(self.ip))


# ----------------------------------------------------------------- registre des noms
class Registry:
    """Nom -> clé de navigateur (hachée). Persistant. Un nom inutilisé depuis --name-ttl-days est libéré."""

    def __init__(self, path, ttl_days, reserved):
        self.path, self.ttl, self.dirty = path, ttl_days * 86400, False
        self.reserved = {norm_name(x) for x in reserved if norm_name(x)}
        self.salt, self.names, self.users = secrets.token_hex(8), {}, {}
        if path and os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    d = json.load(f)
                self.salt = d.get("salt") or self.salt
                self.names, self.users = d.get("names", {}), d.get("users", {})
            except (OSError, ValueError):
                print(_tr("py.presence.registre_illisible_0_demarrage_a_vide", path))
        self.dirty = True
        self.save()

    def hash(self, uid):
        return hashlib.sha256((self.salt + str(uid)).encode()).hexdigest()

    @staticmethod
    def code(uidh):
        return base64.b32encode(bytes.fromhex(uidh[:10]))[:4].decode()

    def save(self):
        if not self.path or not self.dirty:
            return
        d = os.path.dirname(os.path.abspath(self.path))
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"salt": self.salt, "names": self.names, "users": self.users}, f, ensure_ascii=False, indent=1)
        os.replace(tmp, self.path)
        self.dirty = False

    def resolve(self, uidh, requested, persistent=True):
        """Renvoie (nom affiché, nom réservé ?)."""
        now = time.time()
        base = clean_name(requested)
        key = norm_name(base)
        suffix = "#" + self.code(uidh)
        if not base or not key:
            return "Visiteur" + suffix, False
        owner = self.names.get(key)
        if owner and owner != uidh:
            u = self.users.get(owner)
            if not u or now - u.get("last", 0) > self.ttl:
                self.names.pop(key, None); self.users.pop(owner, None); owner = None; self.dirty = True; self.save()
        if owner == uidh:
            self.users.setdefault(uidh, {"name": base, "key": key, "first": now})["last"] = now
            self.users[uidh]["name"] = base
            self.dirty = True
            return base, True
        if owner is None and key not in self.reserved and persistent:
            prev = self.users.get(uidh, {}).get("key")
            if prev and prev != key and self.names.get(prev) == uidh:
                del self.names[prev]
            self.names[key] = uidh
            self.users[uidh] = {"name": base, "key": key, "first": self.users.get(uidh, {}).get("first", now), "last": now}
            self.dirty = True
            self.save()
            return base, True
        return base[:18] + suffix, False


# ----------------------------------------------------------------- créateurs (v51)
CREATORS = None          # None : sans --creators (tout le monde est accepté) ; sinon la liste des créateurs valides du fichier
CR_STAT = {"mtime": None, "checked": 0.0}
CR_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


def origin_norm(o):
    return str(o or "").strip().rstrip("/").lower()[:200]


def cr_int(v):
    return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v > 0 else 0


def creators_parse(d):
    """créateurs valides du fichier ; une entrée invalide est signalée dans la console et ignorée"""
    items = d.get("creators") if isinstance(d, dict) else None
    if not isinstance(items, list):
        raise ValueError("creators")
    out, ids, pres, owner = [], set(), set(), {}
    for i, e in enumerate(items, 1):
        if not isinstance(e, dict) or not CR_ID_RE.match(str(e.get("id") or "")):
            print(_tr("py.presence.cr.bad", i))
            continue
        cid = e["id"]
        pre = e.get("prefix", cid)
        pre = "" if pre is None else str(pre)
        if pre and (clean_room(pre) != pre or "." in pre):
            print(_tr("py.presence.cr.badprefix", i, pre))
            continue
        if cid.lower() in ids or pre.lower() in pres:
            print(_tr("py.presence.cr.dup", i, cid if cid.lower() in ids else pre or '""'))
            continue
        ids.add(cid.lower())
        pres.add(pre.lower())
        origins = []
        for o in e.get("origins") if isinstance(e.get("origins"), list) else []:
            o = origin_norm(o)
            if not o or o in origins:
                continue
            if o in owner:
                print(_tr("py.presence.cr.origindup", o, owner[o], cid))
                continue
            owner[o] = cid
            origins.append(o)
        out.append({"id": cid, "prefix": pre, "plow": pre.lower(), "origins": origins, "maxWalkers": cr_int(e.get("maxWalkers")),
                    "maxRooms": cr_int(e.get("maxRooms")), "off": e.get("off") is True, "note": str(e.get("note") or "")})
    return out


def creators_reload(force=False):
    """relit le fichier des créateurs s'il a changé (au plus une fois toutes les 2 s, à l'arrivée d'une connexion) ;
    fichier absent : toute connexion refusée ; fichier illisible : la liste précédente est gardée"""
    global CREATORS
    if not OPTS.creators:
        return
    now = time.monotonic()
    if not force and now - CR_STAT["checked"] < 2:
        return
    CR_STAT["checked"] = now
    try:
        mt = os.path.getmtime(OPTS.creators)
    except OSError:
        if CR_STAT["mtime"] != "missing" or force:
            print(_tr("py.presence.cr.missing", OPTS.creators))
        CR_STAT["mtime"], CREATORS = "missing", []
        return
    if mt == CR_STAT["mtime"] and not force:
        return
    CR_STAT["mtime"] = mt
    try:
        with open(OPTS.creators, encoding="utf-8") as f:
            lst = creators_parse(json.load(f))
    except (OSError, ValueError) as e:
        if CREATORS is None:
            CREATORS = []
        print(_tr("py.presence.cr.unreadable", OPTS.creators, e))
        return
    CREATORS = lst
    print(_tr("py.presence.cr.loaded", len(lst), OPTS.creators))


def creator_by_origin(origin):
    o = origin_norm(origin)
    return next((c for c in CREATORS or () if o and o in c["origins"]), None)


def creator_of_room(room):
    """créateur à qui appartient un salon : celui dont le préfixe suivi d'un point commence le nom (sans tenir compte de la casse),
    sinon celui qui n'a pas de préfixe (l'hôte du serveur), sinon personne"""
    low, free = str(room).lower(), None
    for c in CREATORS or ():
        if c["prefix"] and low.startswith(c["plow"] + "."):
            return c
        if not c["prefix"] and free is None:
            free = c
    return free


def creator_rooms(cid):
    return [r for r, ps in ROOMS.items() if ps and (creator_of_room(r) or {}).get("id") == cid]


def creator_full(cr):
    """vrai si le créateur a atteint son nombre de promeneurs (valeur du fichier relu, tous ses salons)"""
    if cr is None:
        return False
    cur = next((c for c in CREATORS or () if c["id"] == cr["id"]), cr)
    return bool(cur["maxWalkers"]) and sum(len(walkers(r)) for r in creator_rooms(cur["id"])) >= cur["maxWalkers"]


def creators_command():
    """creators : créateurs du fichier (relu), préfixe, état, salons ouverts, promeneurs, origines"""
    if not OPTS.creators:
        print(_tr("py.presence.cr.off"))
        return
    creators_reload(force=True)
    if not CREATORS:
        print(_tr("py.presence.cr.none", OPTS.creators))
    for c in CREATORS or ():
        rooms = creator_rooms(c["id"])
        print(_tr("py.presence.cr.line", c["id"], c["prefix"] + "." if c["prefix"] else _tr("py.presence.cr.noprefix"),
                  _tr("py.presence.cr.suspended") if c["off"] else _tr("py.presence.cr.active"),
                  len(rooms), _tr("py.presence.cr.max", c["maxRooms"]) if c["maxRooms"] else "",
                  sum(len(walkers(r)) for r in rooms), _tr("py.presence.cr.max", c["maxWalkers"]) if c["maxWalkers"] else ""))
        print(_tr("py.presence.cr.origins", ", ".join(c["origins"]) or "-"))


async def refuse(ws, why, room, ip, detail):
    """v51 : refus d'un créateur (origine, suspendu, salon, salons) : message à la page, journal, fermeture 4003"""
    await send_safe(ws, json.dumps({"t": "refused", "why": why}))
    log(_tr("py.presence.ev.refuse"), room or "-", f"ip {ip_for_log(ip)}", detail)
    try:
        await ws.close(code=4003, reason=why)
    except Exception:
        pass


# ----------------------------------------------------------------- journal des visites (v48)
VKEYS: dict = {}         # salon -> {"salt", "hash", "added"} : empreinte de la clé d'accès, jamais la clé
VTRY: dict = {}          # IP -> instants des derniers essais de clé refusés (5 par minute au plus)
VISIT_GAP = 120          # s : une reconnexion du même navigateur dans le même salon moins de 2 min après la fin = même visite
VISIT_RECENT_DAYS, VISIT_RECENT_MAX = 30, 1000
VKEY_ALPHA = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def vkey_norm(k):
    return re.sub(r"[^A-Z0-9]", "", str(k or "").upper())[:32]


def vkey_hash(salt, key):
    return hashlib.sha256((salt + vkey_norm(key)).encode()).hexdigest()


def vkeys_load():
    VKEYS.clear()
    if OPTS.visits_keys and os.path.exists(OPTS.visits_keys):
        try:
            with open(OPTS.visits_keys, encoding="utf-8") as f:
                d = json.load(f)
            for room, e in (d.get("rooms") or {}).items():
                if isinstance(e, dict) and e.get("salt") and e.get("hash"):
                    VKEYS[clean_room(room)] = {"salt": str(e["salt"]), "hash": str(e["hash"]), "added": e.get("added", 0)}
        except (OSError, ValueError, AttributeError):
            print(_tr("py.presence.vkey.unreadable", OPTS.visits_keys))


def vkeys_save():
    if not OPTS.visits_keys:
        return
    d = os.path.dirname(os.path.abspath(OPTS.visits_keys))
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"rooms": VKEYS}, f, ensure_ascii=False, indent=1)
    os.replace(tmp, OPTS.visits_keys)


def visit_write(peer):
    """écrit la visite qui se termine (appelé à la déconnexion) ; jamais d'IP, pseudo seulement avec --visits-names"""
    if not OPTS.visits:
        return
    peer.walk_mark(False)
    d = {"room": peer.room, "start": int(peer.wall0), "dur": int(time.monotonic() - peer.t0), "walk": int(peer.walk_s),
         "v": hashlib.sha256(("visit:" + peer.uidh).encode()).hexdigest()[:10]}
    if OPTS.visits_names and peer.vname:
        d["name"] = peer.vname
    try:
        with open(OPTS.visits, "a", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False, separators=(",", ":")) + "\n")
    except OSError as e:
        print(_tr("py.presence.visits_write_err", OPTS.visits, e))


def visits_read(room=None):
    out = []
    if not OPTS.visits or not os.path.exists(OPTS.visits):
        return out
    limit = time.time() - OPTS.visits_days * 86400 if OPTS.visits_days > 0 else 0
    with open(OPTS.visits, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
                if not isinstance(d, dict) or (room is not None and d.get("room") != room):
                    continue
                d["start"], d["dur"], d["walk"] = int(d["start"]), max(0, int(d.get("dur", 0))), max(0, int(d.get("walk", 0)))
            except (ValueError, TypeError, KeyError):
                continue
            if d["start"] >= limit:
                out.append(d)
    return out


def visits_purge():
    """retire les visites plus anciennes que --visits-days (au démarrage, puis toutes les 6 h)"""
    if not OPTS.visits or OPTS.visits_days <= 0 or not os.path.exists(OPTS.visits):
        return
    limit = time.time() - OPTS.visits_days * 86400
    with open(OPTS.visits, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    keep = []
    for line in lines:
        try:
            if int(json.loads(line)["start"]) >= limit:
                keep.append(line)
        except (ValueError, TypeError, KeyError):
            continue
    if len(keep) != len(lines):
        d = os.path.dirname(os.path.abspath(OPTS.visits))
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.writelines(keep)
        os.replace(tmp, OPTS.visits)


def visits_merge(rows):
    """visites d'UN salon, reconnexions du même navigateur (moins de VISIT_GAP s) fusionnées"""
    merged, last = [], {}
    for d in sorted(rows, key=lambda x: x["start"]):
        m = last.get(d["v"])
        if m is not None and d["start"] <= m["end"] + VISIT_GAP:
            m["end"] = max(m["end"], d["start"] + d["dur"])
            m["walk"] += d["walk"]
            m["name"] = d.get("name") or m["name"]
            continue
        m = {"start": d["start"], "end": d["start"] + d["dur"], "walk": d["walk"], "v": d["v"], "name": d.get("name") or ""}
        merged.append(m)
        last[d["v"]] = m
    return merged


def visits_summary(room):
    """résumé d'un salon : visites fusionnées (reconnexions), par jour, et liste des 30 derniers jours"""
    merged = visits_merge(visits_read(room))
    days = collections.OrderedDict()
    for m in merged:
        m["dur"] = m["end"] - m["start"]
        days.setdefault(time.strftime("%d/%m/%Y", time.localtime(m["start"])), []).append(m)
    rows = []
    for day, ms in reversed(days.items()):
        durs = sorted(x["dur"] for x in ms)
        n = len(durs)
        med = durs[n // 2] if n % 2 else (durs[n // 2 - 1] + durs[n // 2]) // 2
        rows.append({"date": day, "visits": n, "visitors": len({x["v"] for x in ms}), "total": sum(durs), "median": med,
                     "walked": sum(1 for x in ms if x["walk"] > 0)})
    since = time.time() - VISIT_RECENT_DAYS * 86400
    recent = [{"start": time.strftime("%d/%m/%Y %H:%M", time.localtime(m["start"])), "dur": m["dur"], "walk": m["walk"] > 0,
               **({"name": m["name"]} if OPTS.visits_names and m["name"] else {})}
              for m in reversed(merged) if m["start"] >= since]
    return {"t": "visits", "ok": True, "room": room, "visits": len(merged), "visitors": len({m["v"] for m in merged}),
            "keep": OPTS.visits_days, "names": bool(OPTS.visits_names), "days": rows,
            "recent": recent[:VISIT_RECENT_MAX], "recentAll": len(recent)}


def visits_answer(ip, msg):
    """réponse à {"t": "visits", "room", "key"} : le résumé si la clé du salon est juste ; 5 clés refusées par minute et par IP au plus"""
    room = clean_room(msg.get("room"))
    if not OPTS.visits:
        return {"t": "visits", "ok": False, "why": "off"}
    now = time.time()
    tries = [x for x in VTRY.get(ip, []) if now - x < 60]
    VTRY[ip] = tries
    if len(tries) >= 5:
        log(_tr("py.presence.ev.visits"), room, f"ip {ip_for_log(ip)}", _tr("py.presence.visits.rate"))
        return {"t": "visits", "ok": False, "why": "rate"}
    e = VKEYS.get(room)
    if not e or not hmac.compare_digest(e["hash"], vkey_hash(e["salt"], msg.get("key"))):
        tries.append(now)
        log(_tr("py.presence.ev.visits"), room, f"ip {ip_for_log(ip)}", _tr("py.presence.visits.badkey"))
        return {"t": "visits", "ok": False, "why": "key"}
    log(_tr("py.presence.ev.visits"), room, f"ip {ip_for_log(ip)}", _tr("py.presence.visits.granted"))
    return visits_summary(room)


def rooms_command():
    """rooms : salons connus (connectés, fichier des visites, clés), casse exacte ; un salon jamais visité et sans clé n'y est pas"""
    per = {}
    for d in visits_read():
        if isinstance(d.get("room"), str):
            per.setdefault(d["room"], []).append(d)
    names = sorted(set(ROOMS) | set(per) | set(VKEYS), key=lambda r: (r.lower(), r))
    if not names:
        print(_tr("py.presence.rooms.none"))
    for r in names:
        peers = list(ROOMS.get(r, {}).values())
        merged = visits_merge(per.get(r, []))
        seen = _tr("py.presence.rooms.last", time.strftime("%d/%m/%Y", time.localtime(merged[-1]["start"]))) if merged else ""
        print(_tr("py.presence.rooms.line", r, len(peers), sum(1 for p in peers if not p.spectator), len(merged), seen,
                  _tr("py.presence.visits.yes") if r in VKEYS else _tr("py.presence.visits.no")))
    if not OPTS.visits:
        print(_tr("py.presence.rooms.novisits"))
    print(_tr("py.presence.rooms.note"))


def vkey_command(rest):
    """visits-key SALON : nouvelle clé (remplace l'ancienne) ; visits-key SALON off : la retire ; visits-key : liste"""
    parts = rest.split()
    if not parts:
        if not VKEYS:
            print(_tr("py.presence.vkey.none"))
        for room, e in sorted(VKEYS.items()):
            print(_tr("py.presence.vkey.line", room, time.strftime("%d/%m/%Y", time.localtime(e.get("added") or 0))))
        return
    room = clean_room(parts[0])
    if len(parts) > 1 and parts[1].lower() in ("off", "non", "retirer", "remove"):
        if VKEYS.pop(room, None) is None:
            print(_tr("py.presence.vkey.unknown", room))
            return
        vkeys_save()
        print(_tr("py.presence.vkey.off", room))
        return
    key = "-".join("".join(secrets.choice(VKEY_ALPHA) for _ in range(4)) for _ in range(3))
    salt = secrets.token_hex(8)
    VKEYS[room] = {"salt": salt, "hash": vkey_hash(salt, key), "added": time.time()}
    vkeys_save()
    print(_tr("py.presence.vkey.new", room, key))
    if not OPTS.visits:
        print(_tr("py.presence.vkey.inactive"))
    # la casse du salon compte partout (clean_room la garde) : prévenir si ce nom n'existe qu'avec une autre casse
    known = set(ROOMS) | {d.get("room") for d in visits_read()}
    if room not in known:
        near = sorted(r for r in known if isinstance(r, str) and r != room and r.lower() == room.lower())
        if near:
            print(_tr("py.presence.vkey.case", room, ", ".join(near)))


# ----------------------------------------------------------------- modération (console du serveur)
BANS: list = []          # {"key": hash de clé, "ip": hash d'IP, "until": epoch (0 = définitif), "name", "reason", "added"}


def bans_load():
    BANS.clear()
    if OPTS.bans and os.path.exists(OPTS.bans):
        try:
            with open(OPTS.bans, encoding="utf-8") as f:
                BANS.extend(json.load(f))
        except (OSError, ValueError):
            print(_tr("py.presence.fichier_de_bannissements_illisible_0_ignore", OPTS.bans))


def bans_save():
    if not OPTS.bans:
        return
    d = os.path.dirname(os.path.abspath(OPTS.bans))
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(BANS, f, ensure_ascii=False, indent=1)
    os.replace(tmp, OPTS.bans)


def is_banned(uidh, ip):
    now = time.time()
    gone = [e for e in BANS if e.get("until") and e["until"] <= now]
    if gone:
        for e in gone:
            BANS.remove(e)
        bans_save()
    iph = REG.hash("ip:" + ip)
    for e in BANS:
        if (e.get("key") and e["key"] == uidh) or e.get("ip") == iph:
            return e
    return None


def all_peers():
    return [p for r in ROOMS.values() for p in r.values()]


def find_peers(target):
    if target.isdigit():
        return [p for p in all_peers() if p.id == int(target)]
    key = norm_name(target)
    return [p for p in all_peers() if p.name and key and norm_name(p.name) == key]


async def kick_peer(peer, reason, banned=False):
    await send_safe(peer.ws, json.dumps({"t": "banned" if banned else "kicked", "reason": reason}))
    try:
        await peer.ws.close(code=4002 if banned else 4001, reason=reason[:100])
    except Exception:
        pass


def fmt_until(u):
    return _tr("py.presence.definitif") if not u else time.strftime("%d/%m/%Y %H:%M", time.localtime(u))


HELP = _tr("py.presence.commandes_tape_les_ici_puis_entree")


async def run_command(line):
    line = line.strip()
    if not line:
        return
    cmd, _, rest = line.partition(" ")
    cmd, rest = cmd.lower(), rest.strip()
    if cmd in ("aide", "help", "?"):
        print(HELP)
    elif cmd in ("liste", "list", "who", "l"):
        peers = sorted(all_peers(), key=lambda p: p.id)
        if not peers:
            print(_tr("py.presence.nobody"))
        for p in peers:
            dur = int(time.monotonic() - p.t0)
            print(_tr("py.presence.list_line", p.id, p.name or _tr("py.presence.spectator_paren"), _tr("py.presence.role.spectator") if p.spectator else _tr("py.presence.role.walker"), p.room, dur // 60, dur % 60, p.ip))
    elif cmd in ("ejecter", "éjecter", "kick", "k", "bannir", "ban", "b"):
        ban = cmd in ("bannir", "ban", "b")
        target, _, tail = rest.partition(" ")
        if not target:
            print(_tr("py.presence.usage_ban") if ban else _tr("py.presence.usage_kick"))
            return
        found = find_peers(target)
        if not found:
            print(_tr("py.presence.personne_ne_correspond_a_0_tape", target))
            return
        if len(found) > 1:
            print(_tr("py.presence.plusieurs_visiteurs_correspondent_utilise_le"), ", ".join(f"n°{p.id}" for p in found))
            return
        peer = found[0]
        minutes = 60.0
        tail = tail.strip()
        if ban:
            first, _, after = tail.partition(" ")
            try:
                minutes = float(first.replace(",", "."))
                tail = after.strip()
            except ValueError:
                pass
        reason = tail or (_tr("py.presence.comportement_inapproprie") if ban else _tr("py.presence.ejecte_par_l_hote"))
        if ban:
            until = 0 if minutes <= 0 else time.time() + minutes * 60
            BANS.append({"key": "" if peer.uidh.startswith("anon-") else peer.uidh, "ip": REG.hash("ip:" + peer.ip), "until": until,
                         "name": peer.name or _tr("py.presence.spectator_paren"), "reason": reason, "added": time.time()})
            bans_save()
            log(_tr("py.presence.ev.ban"), peer.room, peer.who(), f"{fmt_until(until)} : {reason}")
            asyncio.create_task(kick_peer(peer, reason, banned=True))
            print(_tr("py.presence.banned_line", peer.name or _tr("py.presence.spectator_paren"), _tr("py.presence.definitif") if not until else _tr("py.presence.until_date", fmt_until(until))))
        else:
            log(_tr("py.presence.ev.kick"), peer.room, peer.who(), reason)
            asyncio.create_task(kick_peer(peer, reason))
            print(_tr("py.presence.0_ejecte", peer.name or _tr('py.presence.spectator_paren')))
    elif cmd in ("rooms", "salons"):
        rooms_command()
    elif cmd in ("creators", "createurs", "créateurs"):
        creators_command()
    elif cmd in ("visits-key", "cle-visites"):
        vkey_command(rest)
    elif cmd == "bans":
        now = time.time()
        live = [e for e in BANS if not e.get("until") or e["until"] > now]
        if not live:
            print(_tr("py.presence.aucun_bannissement"))
        for i, e in enumerate(live, 1):
            print(_tr("py.presence.0_1_20_jusqu_au_2", i, e.get('name', '?'), fmt_until(e.get('until', 0)), e.get('reason', '')))
    elif cmd in ("debannir", "unban"):
        now = time.time()
        live = [e for e in BANS if not e.get("until") or e["until"] > now]
        if not rest.isdigit() or not (1 <= int(rest) <= len(live)):
            print(_tr("py.presence.usage_unban"))
            return
        e = live[int(rest) - 1]
        BANS.remove(e)
        bans_save()
        log(_tr("py.presence.ev.ban"), "-", f"{e.get('name', '?')}", _tr("py.presence.leve"))
        print(_tr("py.presence.bannissement_de_0_leve", e.get('name', '?')))
    else:
        print(_tr("py.presence.commande_inconnue_0_tape_aide", cmd))


async def console_loop():
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    if sys.stdin is None:
        return

    def reader():
        try:
            for line in sys.stdin:
                loop.call_soon_threadsafe(queue.put_nowait, line)
        except (OSError, ValueError):
            pass
        loop.call_soon_threadsafe(queue.put_nowait, None)

    threading.Thread(target=reader, daemon=True).start()
    while True:
        line = await queue.get()
        if line is None:
            return
        try:
            await run_command(line)
        except Exception as e:  # une commande ratée ne doit jamais arrêter le serveur
            print(_tr("py.presence.erreur_de_commande_0", e))


# ----------------------------------------------------------------- réseau
async def send_safe(ws, text):
    try:
        await ws.send(text)
    except Exception:
        pass


async def broadcast(room, msg, exclude=None):
    text = json.dumps(msg, separators=(",", ":"))
    peers = [p for p in ROOMS.get(room, {}).values() if p is not exclude]
    if peers:
        await asyncio.gather(*(send_safe(p.ws, text) for p in peers))


def walkers(room):
    return [p for p in ROOMS.get(room, {}).values() if not p.spectator]


def ws_origin(ws):
    """en-tête Origin de la connexion (donné par le navigateur ; « null » pour une page ouverte depuis le disque)"""
    try:
        req = getattr(ws, "request", None)
        headers = getattr(req, "headers", None) or getattr(ws, "request_headers", None)
        return str(headers.get("Origin") or "")[:200] if headers is not None else ""
    except Exception:
        return ""


def remote_ip(ws):
    if OPTS is not None and OPTS.proxy_header:
        try:
            req = getattr(ws, "request", None)
            headers = getattr(req, "headers", None) or getattr(ws, "request_headers", None)
            v = headers.get(OPTS.proxy_header) if headers is not None else None
            if v:
                return v.split(",")[0].strip()[:64]
        except Exception:
            pass
    try:
        return str(ws.remote_address[0])
    except Exception:
        return "?"


async def become_walker(peer, requested_name):
    peer.name, _ = REG.resolve(peer.uidh, requested_name, persistent=not peer.uidh.startswith("anon-"))
    peer.spectator = False
    peer.p = None


async def handler(ws):
    global NEXT_ID
    peer, room, counted = None, None, False
    ip = remote_ip(ws)
    try:
        eb = is_banned("", ip)
        if eb:
            await ws.send(json.dumps({"t": "banned", "reason": eb.get("reason", ""), "until": eb.get("until", 0)}))
            log(_tr("py.presence.ev.refuse"), "-", f"ip {ip_for_log(ip)}", _tr("py.presence.ban_ip"))
            return
        if PER_IP.get(ip, 0) >= OPTS.max_per_ip:
            await ws.send(json.dumps({"t": "full"}))
            log(_tr("py.presence.ev.refuse"), "-", f"ip {ip_for_log(ip)}", _tr("py.presence.limite_de_connexions_par_ip"))
            return
        PER_IP[ip] = PER_IP.get(ip, 0) + 1
        counted = True
        cr = None
        if OPTS.creators:      # v51 : la page doit venir d'une origine déclarée par un créateur actif
            creators_reload()
            org = ws_origin(ws)
            cr = creator_by_origin(org)
            if cr is None or cr["off"]:
                await refuse(ws, "origin" if cr is None else "off", "-", ip,
                             _tr("py.presence.cr.refuse.origin", org or _tr("py.presence.cr.noorigin")) if cr is None else _tr("py.presence.cr.refuse.off", cr["id"]))
                return
        msg = json.loads(await asyncio.wait_for(ws.recv(), 10))
        if isinstance(msg, dict) and msg.get("t") == "visits":     # v48 : journal des visites, demandé par la page avec #visits
            await ws.send(json.dumps(visits_answer(ip, msg), ensure_ascii=False, separators=(",", ":")))
            return
        if isinstance(msg, dict) and msg.get("t") == "rooms":
            await ws.send(json.dumps({"t": "rooms", "rooms": {name: len(walkers(name)) for name in ROOMS if walkers(name)},
                                      "visitors": {name: len(peers_in) for name, peers_in in ROOMS.items() if peers_in},   # v47 : promeneurs et spectateurs, par salon
                                      "spectators": sum(1 for p in all_peers() if p.spectator)}, separators=(",", ":")))
            return
        if not isinstance(msg, dict) or msg.get("t") != "hello":
            return
        room = clean_room(msg.get("room"))
        if cr is not None:     # v51 : seulement un salon du créateur, et pas plus de salons ouverts que permis
            if (creator_of_room(room) or {}).get("id") != cr["id"]:
                await refuse(ws, "room", room, ip, _tr("py.presence.cr.refuse.room", room, cr["id"]))
                return
            if cr["maxRooms"] and not ROOMS.get(room) and len(creator_rooms(cr["id"])) >= cr["maxRooms"]:
                await refuse(ws, "rooms", room, ip, _tr("py.presence.cr.refuse.rooms", cr["id"], cr["maxRooms"]))
                return
        uid = str(msg.get("uid") or "")[:128]
        uidh = REG.hash(uid) if len(uid) >= 16 else "anon-" + secrets.token_hex(8)
        spectator = bool(msg.get("spectator"))
        eb = is_banned(uidh, ip)
        if eb:
            await ws.send(json.dumps({"t": "banned", "reason": eb.get("reason", ""), "until": eb.get("until", 0)}))
            log(_tr("py.presence.ev.refuse"), room, _tr("py.presence.cle_0_ip_1", uidh[:6], ip_for_log(ip)), _tr("py.presence.banned"))
            return
        if spectator:
            if sum(1 for r in ROOMS.values() for p in r.values() if p.spectator) >= OPTS.max_spectators:
                await ws.send(json.dumps({"t": "full"}))
                log(_tr("py.presence.ev.refuse"), room, f"ip {ip_for_log(ip)}", _tr("py.presence.trop_de_spectateurs"))
                return
        elif len(walkers(room)) >= OPTS.max_per_room or sum(len(r) for r in ROOMS.values()) >= OPTS.max_total or creator_full(cr):
            await ws.send(json.dumps({"t": "full"}))
            log(_tr("py.presence.ev.refuse"), room, f"ip {ip_for_log(ip)}", _tr("py.presence.salon_plein"))
            return
        pid, NEXT_ID = NEXT_ID, NEXT_ID + 1
        color = announced_color(msg.get("color"))
        peer = Peer(pid, ws, "", random_color() if color is None else color, ip, spectator, uidh, room)
        if not spectator:
            peer.name, _ = REG.resolve(uidh, msg.get("name"), persistent=not uidh.startswith("anon-"))
            peer.vname = peer.name
        existing = [p.public() for p in walkers(room)]
        peers = ROOMS.setdefault(room, {})      # v51 : créé ici seulement (un refus plus haut ne laisse plus de salon vide)
        peers[pid] = peer
        await ws.send(json.dumps({"t": "welcome", "id": pid, "name": peer.name, "color": peer.color, "peers": existing,
                                  "history": list(HISTORY.get(room, ()))[-OPTS.history:] if OPTS.history > 0 else [], "role": "spectator" if spectator else "walker"},
                                 separators=(",", ":")))
        log(_tr("py.presence.ev.connect"), room, peer.who(), "spectateur" if spectator else _tr("py.presence.promeneur_0_dans_le_salon", len(walkers(room))))
        if not spectator:
            await broadcast(room, dict(peer.public(), t="join"), exclude=peer)
        async for raw in ws:
            try:
                m = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(m, dict):
                continue
            t = m.get("t")
            if t == "role":
                want_walker = bool(m.get("walker"))
                if want_walker and peer.spectator:
                    if len(walkers(room)) >= OPTS.max_per_room or creator_full(cr):
                        await send_safe(ws, json.dumps({"t": "full"}))
                        continue
                    await become_walker(peer, m.get("name"))
                    peer.walk_mark(True)
                    peer.vname = peer.name
                    await send_safe(ws, json.dumps({"t": "you", "name": peer.name}))
                    await broadcast(room, dict(peer.public(), t="join"), exclude=peer)
                    log(_tr("py.presence.ev.walk"), room, peer.who(), _tr("py.presence.debut"))
                elif not want_walker and not peer.spectator:
                    peer.spectator, peer.p = True, None
                    peer.walk_mark(False)
                    await broadcast(room, {"t": "leave", "id": pid}, exclude=peer)
                    log(_tr("py.presence.ev.walk"), room, peer.who(), _tr("py.presence.ev.end"))
                    peer.name = ""
            elif t == "color":
                # v34 : changement de couleur en cours de connexion ; valeur invalide ignorée sans bruit, au plus un changement toutes les 0,2 s
                c = announced_color(m.get("color"))
                now = time.monotonic()
                if c is None or now - peer.color_t < 0.2:
                    continue
                peer.color_t = now
                if c != peer.color:
                    peer.color = c
                    if not peer.spectator:
                        await broadcast(room, {"t": "color", "id": pid, "color": c}, exclude=peer)
            elif peer.spectator:
                continue
            elif t == "pos":
                now = time.monotonic()
                if now - peer.last < 0.04:
                    continue
                p = finite_list(m.get("p"), 3)
                yaw = m.get("yaw", 0)
                if p is None or isinstance(yaw, bool) or not isinstance(yaw, (int, float)) or not math.isfinite(yaw):
                    continue
                peer.last, peer.p, peer.yaw = now, p, round(float(yaw), 2)
                await broadcast(room, {"t": "pos", "id": pid, "p": p, "yaw": peer.yaw}, exclude=peer)
            elif t == "chat":
                text = clean_text(m.get("text"), OPTS.max_chat)
                if not text:
                    continue
                now = time.monotonic()
                peer.chat_times = [x for x in peer.chat_times if now - x < 10]
                if peer.chat_times and now - peer.chat_times[-1] < OPTS.chat_gap:
                    continue
                if len(peer.chat_times) >= OPTS.chat_burst:
                    await send_safe(ws, json.dumps({"t": "notice", "text": _tr("py.presence.trop_de_messages_patiente_quelques_secondes")}))
                    continue
                peer.chat_times.append(now)
                ent = hist_add(room, pid, peer.name, text) if (OPTS.history > 0 or OPTS.history_file) else {"n": 0, "t": int(time.time())}
                log(_tr("py.presence.chat"), room, peer.who(), text)
                await broadcast(room, {"t": "chat", "id": pid, "name": peer.name, "text": text, "n": ent["n"], "ts": ent["t"]})
            elif t == "history":
                # v37 : page plus ancienne de l'historique du salon : {t:'history', before: n, n: 50} -> {t:'history', msgs:[...], more:bool}
                now = time.monotonic()
                if now - peer.hist_t < 0.2:
                    continue
                peer.hist_t = now
                before, cnt = m.get("before"), m.get("n")
                if isinstance(before, bool) or not isinstance(before, (int, float)) or isinstance(cnt, bool) or not isinstance(cnt, (int, float)):
                    continue
                cnt = max(1, min(100, int(cnt)))
                older = [e for e in HISTORY.get(room, ()) if e["n"] < before]
                await send_safe(ws, json.dumps({"t": "history", "msgs": older[-cnt:], "more": len(older) > cnt}, separators=(",", ":")))
            elif t == "name":
                old = peer.name
                peer.name, _ = REG.resolve(peer.uidh, m.get("name"), persistent=not peer.uidh.startswith("anon-"))
                if peer.name != old:
                    await send_safe(ws, json.dumps({"t": "you", "name": peer.name}))
                    await broadcast(room, {"t": "name", "id": pid, "name": peer.name}, exclude=peer)
                    log(_tr("py.presence.ev.name"), room, peer.who(), _tr("py.presence.old_name", old))
            elif t == "zone":
                now = time.monotonic()
                if now - peer.zone_t < 0.5:
                    continue
                peer.zone_t = now
                log(_tr("py.presence.zone"), room, peer.who(), f"{clean_text(m.get('type'), 12)} « {clean_text(m.get('label') or m.get('id'), 60)} »")
    except (websockets.ConnectionClosed, asyncio.TimeoutError, ValueError):
        pass
    finally:
        if peer is not None and room in ROOMS:
            ROOMS[room].pop(peer.id, None)
            if not peer.spectator:
                await broadcast(room, {"t": "leave", "id": peer.id})
            dur = int(time.monotonic() - peer.t0)
            log(_tr("py.presence.deconnexion"), room, peer.who(), _tr("py.presence.duree_0_min_1_02d_s", dur // 60, dur % 60))
            visit_write(peer)
            if not ROOMS[room]:
                del ROOMS[room]
                if not OPTS.history_file:
                    HISTORY.pop(room, None)
        if counted and PER_IP.get(ip):
            PER_IP[ip] -= 1
            if PER_IP[ip] <= 0:
                del PER_IP[ip]


async def flush_loop():
    n = 0
    while True:
        await asyncio.sleep(20)
        REG.save()
        n += 1
        if n % 1080 == 0:     # v48 : toutes les 6 h
            try:
                visits_purge()
            except OSError:
                pass


async def main():
    global OPTS, REG
    ap = argparse.ArgumentParser(description=_tr("py.presence.serveur_de_presence_glb2html_websocket", VERSION), add_help=False)
    i18n_add_common(ap)
    ap.add_argument("--version", action="version", version=f"presence_server {VERSION}", help=_tr("py.common.version"))
    ap.add_argument("--host", default="0.0.0.0", help=_tr("py.presence.help.host"))
    ap.add_argument("--port", type=int, default=8765, help=_tr("py.presence.help.port"))
    ap.add_argument("--max-per-room", type=int, default=50, help=_tr("py.presence.promeneurs_max_par_salon"))
    ap.add_argument("--max-spectators", type=int, default=100, help=_tr("py.presence.spectateurs_vue_globale_max_tous_salons"))
    ap.add_argument("--max-total", type=int, default=500, help=_tr("py.presence.help.maxtotal"))
    ap.add_argument("--max-per-ip", type=int, default=10, help=_tr("py.presence.connexions_simultanees_par_adresse_ip"))
    ap.add_argument("--max-chat", type=int, default=200, help=_tr("py.presence.longueur_max_d_un_message_de"))
    ap.add_argument("--chat-gap", type=float, default=0.7, help=_tr("py.presence.delai_mini_entre_deux_messages_d"))
    ap.add_argument("--chat-burst", type=int, default=5, help=_tr("py.presence.messages_max_par_fenetre_de_10"))
    ap.add_argument("--history", type=int, default=200, help=_tr("py.presence.derniers_messages_rejoues_aux_nouveaux_arriv"))
    ap.add_argument("--identities", default="presence_identities.json", help=_tr("py.presence.registre_des_noms_reserves_vide_en"))
    ap.add_argument("--name-ttl-days", type=int, default=365, help=_tr("py.presence.un_nom_non_utilise_depuis_ce"))
    ap.add_argument("--reserved", default="", help=_tr("py.presence.noms_interdits_a_la_reservation_separes"))
    ap.add_argument("--log", help=_tr("py.presence.fichier_de_journal_tourne_chaque_nuit"))
    ap.add_argument("--history-file", default="", metavar="FILE", help=_tr("py.presence.history_file"))
    ap.add_argument("--history-days", type=int, default=30, metavar="N", help=_tr("py.presence.history_days"))
    ap.add_argument("--log-days", type=int, default=30, help=_tr("py.presence.jours_de_journal_conserves"))
    ap.add_argument("--log-ip", choices=("hash", "raw", "none"), default="hash", help=_tr("py.presence.adresses_ip_dans_le_journal_masquees"))
    ap.add_argument("--proxy-header", help=_tr("py.presence.derriere_un_reverse_proxy_en_tete"))
    ap.add_argument("--bans", default="presence_bans.json", help=_tr("py.presence.fichier_des_bannissements_chemin_relatif_dos"))
    ap.add_argument("--origins", help=_tr("py.presence.origines_autorisees_separees_par_des_virgule"))
    ap.add_argument("--visits", default="", metavar="FILE", help=_tr("py.presence.help.visits"))
    ap.add_argument("--visits-days", type=int, default=365, metavar="N", help=_tr("py.presence.help.visits_days"))
    ap.add_argument("--visits-names", action="store_true", help=_tr("py.presence.help.visits_names"))
    ap.add_argument("--visits-keys", default="presence_visits_keys.json", metavar="FILE", help=_tr("py.presence.help.visits_keys"))
    ap.add_argument("--creators", default="", metavar="FILE", help=_tr("py.presence.help.creators"))
    ap.add_argument("--cert", help=_tr("py.presence.certificat_tls_wss"))
    ap.add_argument("--key", help=_tr("py.presence.cle_privee_tls"))
    OPTS = ap.parse_args()
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass
    OPTS.log = here(OPTS.log)
    OPTS.identities = here(OPTS.identities)
    OPTS.bans = here(OPTS.bans)
    OPTS.history_file = here(OPTS.history_file) if OPTS.history_file else ""
    OPTS.visits = here(OPTS.visits) if OPTS.visits else ""
    OPTS.visits_keys = here(OPTS.visits_keys) if OPTS.visits_keys else ""
    OPTS.creators = here(OPTS.creators) if OPTS.creators else ""
    REG = Registry(OPTS.identities or None, OPTS.name_ttl_days, [x for x in OPTS.reserved.split(",")])
    setup_log()
    bans_load()
    hist_load()
    vkeys_load()
    creators_reload(force=True)
    if OPTS.visits:
        try:
            visits_purge()
        except OSError:
            pass
    ctx = None
    if OPTS.cert:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(OPTS.cert, OPTS.key)
    origins = [o.strip() for o in OPTS.origins.split(",")] if OPTS.origins else None
    flusher = asyncio.create_task(flush_loop())
    console = asyncio.create_task(console_loop())
    stop = asyncio.Event()
    try:
        asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, stop.set)
    except (NotImplementedError, AttributeError, RuntimeError):
        pass
    try:
        async with websockets.serve(handler, OPTS.host, OPTS.port, max_size=4096, origins=origins, ssl=ctx):
            scheme = "wss" if ctx else "ws"
            LOG.info(_tr("py.presence.serveur_presence_server_0_ecoute_sur", VERSION, OPTS.host, OPTS.port))
            if OPTS.host in ("0.0.0.0", "::", ""):
                ip = lan_ip()
                LOG.info(_tr("py.presence.serveur_adresses_a_donner_a_presence", scheme, OPTS.port) + (_tr("py.presence.0_1_2_autres_appareils_du", scheme, ip, OPTS.port) if ip else ""))
                LOG.info(_tr("py.presence.serveur_n_utilise_jamais_0_0"))
                LOG.info(_tr("py.presence.star_hint", scheme, OPTS.port))     # v51 : « * » = le même nom que la page
            else:
                LOG.info(_tr("py.presence.serveur_adresse_a_donner_a_presence", scheme, OPTS.host, OPTS.port))
            LOG.info(_tr("py.presence.serveur_journal_0_registre_des_noms", OPTS.log or '(aucun : option --log)', OPTS.identities or '(en mémoire)'))
            if OPTS.visits:
                LOG.info(_tr("py.presence.visits_on", OPTS.visits, OPTS.visits_days, _tr("py.presence.visits.yes") if OPTS.visits_names else _tr("py.presence.visits.no")))
            if OPTS.creators:
                LOG.info(_tr("py.presence.cr.on", OPTS.creators, len(CREATORS or ())))
            print(_tr("py.presence.moderation_tape_aide_pour_la_liste"))
            await stop.wait()
    finally:
        flusher.cancel()
        console.cancel()
        REG.save()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
