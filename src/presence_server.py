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
"""
from __future__ import annotations

VERSION = "__VERSION__"

import argparse
import asyncio
import base64
import collections
import colorsys
import hashlib
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
    __slots__ = ("id", "ws", "name", "color", "p", "yaw", "last", "ip", "chat_times", "spectator", "uidh", "t0", "zone_t", "room", "color_t", "hist_t")

    def __init__(self, pid, ws, name, color, ip, spectator, uidh, room):
        self.id, self.ws, self.name, self.color, self.ip = pid, ws, name, color, ip
        self.spectator, self.uidh, self.room = spectator, uidh, room
        self.p, self.yaw, self.last, self.zone_t, self.color_t, self.hist_t = None, 0.0, 0.0, 0.0, 0.0, 0.0
        self.chat_times = []
        self.t0 = time.monotonic()

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
        msg = json.loads(await asyncio.wait_for(ws.recv(), 10))
        if isinstance(msg, dict) and msg.get("t") == "rooms":
            await ws.send(json.dumps({"t": "rooms", "rooms": {name: len(walkers(name)) for name in ROOMS if walkers(name)},
                                      "spectators": sum(1 for p in all_peers() if p.spectator)}, separators=(",", ":")))
            return
        if not isinstance(msg, dict) or msg.get("t") != "hello":
            return
        room = clean_room(msg.get("room"))
        peers = ROOMS.setdefault(room, {})
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
        elif len(walkers(room)) >= OPTS.max_per_room or sum(len(r) for r in ROOMS.values()) >= OPTS.max_total:
            await ws.send(json.dumps({"t": "full"}))
            log(_tr("py.presence.ev.refuse"), room, f"ip {ip_for_log(ip)}", _tr("py.presence.salon_plein"))
            return
        pid, NEXT_ID = NEXT_ID, NEXT_ID + 1
        color = announced_color(msg.get("color"))
        peer = Peer(pid, ws, "", random_color() if color is None else color, ip, spectator, uidh, room)
        if not spectator:
            peer.name, _ = REG.resolve(uidh, msg.get("name"), persistent=not uidh.startswith("anon-"))
        existing = [p.public() for p in walkers(room)]
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
                    if len(walkers(room)) >= OPTS.max_per_room:
                        await send_safe(ws, json.dumps({"t": "full"}))
                        continue
                    await become_walker(peer, m.get("name"))
                    await send_safe(ws, json.dumps({"t": "you", "name": peer.name}))
                    await broadcast(room, dict(peer.public(), t="join"), exclude=peer)
                    log(_tr("py.presence.ev.walk"), room, peer.who(), _tr("py.presence.debut"))
                elif not want_walker and not peer.spectator:
                    peer.spectator, peer.p = True, None
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
            if not ROOMS[room]:
                del ROOMS[room]
                if not OPTS.history_file:
                    HISTORY.pop(room, None)
        if counted and PER_IP.get(ip):
            PER_IP[ip] -= 1
            if PER_IP[ip] <= 0:
                del PER_IP[ip]


async def flush_loop():
    while True:
        await asyncio.sleep(20)
        REG.save()


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
    ap.add_argument("--history-file", default="", metavar="FICHIER", help=_tr("py.presence.history_file"))
    ap.add_argument("--history-days", type=int, default=30, metavar="N", help=_tr("py.presence.history_days"))
    ap.add_argument("--log-days", type=int, default=30, help=_tr("py.presence.jours_de_journal_conserves"))
    ap.add_argument("--log-ip", choices=("hash", "raw", "none"), default="hash", help=_tr("py.presence.adresses_ip_dans_le_journal_masquees"))
    ap.add_argument("--proxy-header", help=_tr("py.presence.derriere_un_reverse_proxy_en_tete"))
    ap.add_argument("--bans", default="presence_bans.json", help=_tr("py.presence.fichier_des_bannissements_chemin_relatif_dos"))
    ap.add_argument("--origins", help=_tr("py.presence.origines_autorisees_separees_par_des_virgule"))
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
    REG = Registry(OPTS.identities or None, OPTS.name_ttl_days, [x for x in OPTS.reserved.split(",")])
    setup_log()
    bans_load()
    hist_load()
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
            else:
                LOG.info(_tr("py.presence.serveur_adresse_a_donner_a_presence", scheme, OPTS.host, OPTS.port))
            LOG.info(_tr("py.presence.serveur_journal_0_registre_des_noms", OPTS.log or '(aucun : option --log)', OPTS.identities or '(en mémoire)'))
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
