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

ROOMS: dict[str, dict[int, "Peer"]] = {}
HISTORY: dict[str, collections.deque] = {}
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


class FrFormatter(logging.Formatter):
    def format(self, record):
        return time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(record.created)) + " | " + record.getMessage()


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
    line = f"{kind:<11} | salon={room} | {who}"
    if extra:
        line += " | " + re.sub(r"[\r\n]+", " ", str(extra))
    LOG.info(line)


class Peer:
    __slots__ = ("id", "ws", "name", "color", "p", "yaw", "last", "ip", "chat_times", "spectator", "uidh", "t0", "zone_t", "room")

    def __init__(self, pid, ws, name, color, ip, spectator, uidh, room):
        self.id, self.ws, self.name, self.color, self.ip = pid, ws, name, color, ip
        self.spectator, self.uidh, self.room = spectator, uidh, room
        self.p, self.yaw, self.last, self.zone_t = None, 0.0, 0.0, 0.0
        self.chat_times = []
        self.t0 = time.monotonic()

    def public(self):
        d = {"id": self.id, "name": self.name, "color": self.color}
        if self.p is not None:
            d["p"], d["yaw"] = self.p, self.yaw
        return d

    def who(self):
        return f"{self.name or '(spectateur)'} [id {self.id}, clé {self.uidh[:6]}, ip {ip_for_log(self.ip)}]"


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
                print(f"[!] registre illisible ({path}) : démarrage à vide")
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
            print(f"[!] fichier de bannissements illisible ({OPTS.bans}) : ignoré")


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
    return "définitif" if not u else time.strftime("%d/%m/%Y %H:%M", time.localtime(u))


HELP = """commandes (tape-les ici, puis Entrée) :
  liste                           visiteurs connectés (n°, nom, rôle, salon, durée, IP)
  ejecter <n°|nom> [raison]       déconnecte le visiteur (il peut revenir)
  bannir <n°|nom> [minutes] [raison]   éjecte et interdit sa clé et son IP (défaut 60 min ; 0 = définitif)
  bans                            bannissements en cours
  debannir <n° de bans>           lève un bannissement
  aide                            ce message
  (un nom contenant des espaces : utilise le n° de « liste »)"""


async def run_command(line):
    line = line.strip()
    if not line:
        return
    cmd, _, rest = line.partition(" ")
    cmd, rest = cmd.lower(), rest.strip()
    if cmd in ("aide", "help", "?"):
        print(HELP)
    elif cmd in ("liste", "who", "l"):
        peers = sorted(all_peers(), key=lambda p: p.id)
        if not peers:
            print("(personne)")
        for p in peers:
            dur = int(time.monotonic() - p.t0)
            print(f"  n°{p.id:<4} {(p.name or '(spectateur)'):<26} {'spectateur' if p.spectator else 'promeneur':<10} salon={p.room:<16} {dur // 60} min {dur % 60:02d} s   ip {p.ip}")
    elif cmd in ("ejecter", "éjecter", "kick", "k", "bannir", "ban", "b"):
        ban = cmd in ("bannir", "ban", "b")
        target, _, tail = rest.partition(" ")
        if not target:
            print("usage : " + ("bannir <n°|nom> [minutes] [raison]" if ban else "ejecter <n°|nom> [raison]"))
            return
        found = find_peers(target)
        if not found:
            print(f"personne ne correspond à « {target} » (tape « liste »)")
            return
        if len(found) > 1:
            print("plusieurs visiteurs correspondent, utilise le n° :", ", ".join(f"n°{p.id}" for p in found))
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
        reason = tail or ("comportement inapproprié" if ban else "éjecté par l'hôte")
        if ban:
            until = 0 if minutes <= 0 else time.time() + minutes * 60
            BANS.append({"key": "" if peer.uidh.startswith("anon-") else peer.uidh, "ip": REG.hash("ip:" + peer.ip), "until": until,
                         "name": peer.name or "(spectateur)", "reason": reason, "added": time.time()})
            bans_save()
            log("bannissement", peer.room, peer.who(), f"{fmt_until(until)} : {reason}")
            asyncio.create_task(kick_peer(peer, reason, banned=True))
            print(f"{peer.name or '(spectateur)'} banni ({'définitif' if not until else 'jusqu’au ' + fmt_until(until)})")
        else:
            log("éjection", peer.room, peer.who(), reason)
            asyncio.create_task(kick_peer(peer, reason))
            print(f"{peer.name or '(spectateur)'} éjecté")
    elif cmd == "bans":
        now = time.time()
        live = [e for e in BANS if not e.get("until") or e["until"] > now]
        if not live:
            print("(aucun bannissement)")
        for i, e in enumerate(live, 1):
            print(f"  {i}. {e.get('name', '?'):<20} jusqu'au {fmt_until(e.get('until', 0)):<17} {e.get('reason', '')}")
    elif cmd in ("debannir", "unban"):
        now = time.time()
        live = [e for e in BANS if not e.get("until") or e["until"] > now]
        if not rest.isdigit() or not (1 <= int(rest) <= len(live)):
            print("usage : debannir <n° de « bans »>")
            return
        e = live[int(rest) - 1]
        BANS.remove(e)
        bans_save()
        log("bannissement", "-", f"{e.get('name', '?')}", "levé")
        print(f"bannissement de {e.get('name', '?')} levé")
    else:
        print(f"commande inconnue : {cmd} (tape « aide »)")


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
            print(f"[erreur de commande] {e}")


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
            log("refus", "-", f"ip {ip_for_log(ip)}", "banni (IP)")
            return
        if PER_IP.get(ip, 0) >= OPTS.max_per_ip:
            await ws.send(json.dumps({"t": "full"}))
            log("refus", "-", f"ip {ip_for_log(ip)}", "limite de connexions par IP")
            return
        PER_IP[ip] = PER_IP.get(ip, 0) + 1
        counted = True
        msg = json.loads(await asyncio.wait_for(ws.recv(), 10))
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
            log("refus", room, f"clé {uidh[:6]} ip {ip_for_log(ip)}", "banni")
            return
        if spectator:
            if sum(1 for r in ROOMS.values() for p in r.values() if p.spectator) >= OPTS.max_spectators:
                await ws.send(json.dumps({"t": "full"}))
                log("refus", room, f"ip {ip_for_log(ip)}", "trop de spectateurs")
                return
        elif len(walkers(room)) >= OPTS.max_per_room or sum(len(r) for r in ROOMS.values()) >= OPTS.max_total:
            await ws.send(json.dumps({"t": "full"}))
            log("refus", room, f"ip {ip_for_log(ip)}", "salon plein")
            return
        pid, NEXT_ID = NEXT_ID, NEXT_ID + 1
        peer = Peer(pid, ws, "", random_color(), ip, spectator, uidh, room)
        if not spectator:
            peer.name, _ = REG.resolve(uidh, msg.get("name"), persistent=not uidh.startswith("anon-"))
        existing = [p.public() for p in walkers(room)]
        peers[pid] = peer
        await ws.send(json.dumps({"t": "welcome", "id": pid, "name": peer.name, "color": peer.color, "peers": existing,
                                  "history": list(HISTORY.get(room, ())), "role": "spectator" if spectator else "walker"},
                                 separators=(",", ":")))
        log("connexion", room, peer.who(), "spectateur" if spectator else f"promeneur ({len(walkers(room))} dans le salon)")
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
                    log("promenade", room, peer.who(), "début")
                elif not want_walker and not peer.spectator:
                    peer.spectator, peer.p = True, None
                    await broadcast(room, {"t": "leave", "id": pid}, exclude=peer)
                    log("promenade", room, peer.who(), "fin")
                    peer.name = ""
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
                    await send_safe(ws, json.dumps({"t": "notice", "text": "Trop de messages, patiente quelques secondes."}))
                    continue
                peer.chat_times.append(now)
                if OPTS.history > 0:
                    HISTORY.setdefault(room, collections.deque(maxlen=OPTS.history)).append({"id": pid, "name": peer.name, "text": text})
                log("chat", room, peer.who(), text)
                await broadcast(room, {"t": "chat", "id": pid, "name": peer.name, "text": text})
            elif t == "name":
                old = peer.name
                peer.name, _ = REG.resolve(peer.uidh, m.get("name"), persistent=not peer.uidh.startswith("anon-"))
                if peer.name != old:
                    await send_safe(ws, json.dumps({"t": "you", "name": peer.name}))
                    await broadcast(room, {"t": "name", "id": pid, "name": peer.name}, exclude=peer)
                    log("nom", room, peer.who(), f"ancien : {old}")
            elif t == "zone":
                now = time.monotonic()
                if now - peer.zone_t < 0.5:
                    continue
                peer.zone_t = now
                log("zone", room, peer.who(), f"{clean_text(m.get('type'), 12)} « {clean_text(m.get('label') or m.get('id'), 60)} »")
    except (websockets.ConnectionClosed, asyncio.TimeoutError, ValueError):
        pass
    finally:
        if peer is not None and room in ROOMS:
            ROOMS[room].pop(peer.id, None)
            if not peer.spectator:
                await broadcast(room, {"t": "leave", "id": peer.id})
            dur = int(time.monotonic() - peer.t0)
            log("déconnexion", room, peer.who(), f"durée {dur // 60} min {dur % 60:02d} s")
            if not ROOMS[room]:
                del ROOMS[room]
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
    ap = argparse.ArgumentParser(description="Serveur de présence glb2html (WebSocket)")
    ap.add_argument("--version", action="version", version=f"presence_server {VERSION}")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--max-per-room", type=int, default=50, help="promeneurs max par salon")
    ap.add_argument("--max-spectators", type=int, default=100, help="spectateurs (vue globale) max, tous salons")
    ap.add_argument("--max-total", type=int, default=500)
    ap.add_argument("--max-per-ip", type=int, default=10, help="connexions simultanées par adresse IP")
    ap.add_argument("--max-chat", type=int, default=200, help="longueur max d'un message de chat")
    ap.add_argument("--chat-gap", type=float, default=0.7, help="délai mini entre deux messages d'un visiteur (s)")
    ap.add_argument("--chat-burst", type=int, default=5, help="messages max par fenêtre de 10 s et par visiteur")
    ap.add_argument("--history", type=int, default=20, help="derniers messages rejoués aux nouveaux arrivants (mémoire seulement, 0 = aucun)")
    ap.add_argument("--identities", default="presence_identities.json", help="registre des noms réservés (vide = en mémoire seulement) ; chemin relatif = dossier du script")
    ap.add_argument("--name-ttl-days", type=int, default=365, help="un nom non utilisé depuis ce nombre de jours est libéré")
    ap.add_argument("--reserved", default="", help="noms interdits à la réservation, séparés par des virgules (ex. admin,moderateur)")
    ap.add_argument("--log", help="fichier de journal (tourné chaque nuit) ; chemin relatif = dossier du script")
    ap.add_argument("--log-days", type=int, default=30, help="jours de journal conservés")
    ap.add_argument("--log-ip", choices=("hash", "raw", "none"), default="hash", help="adresses IP dans le journal : masquées (défaut), en clair, ou absentes")
    ap.add_argument("--proxy-header", help="derrière un reverse proxy : en-tête portant l'IP réelle du visiteur (ex. X-Forwarded-For, CF-Connecting-IP) ; à n'activer que si le serveur n'est joignable que par ce proxy")
    ap.add_argument("--bans", default="presence_bans.json", help="fichier des bannissements ; chemin relatif = dossier du script")
    ap.add_argument("--origins", help="origines autorisées, séparées par des virgules (défaut : toutes)")
    ap.add_argument("--cert", help="certificat TLS (wss://)")
    ap.add_argument("--key", help="clé privée TLS")
    OPTS = ap.parse_args()
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass
    OPTS.log = here(OPTS.log)
    OPTS.identities = here(OPTS.identities)
    OPTS.bans = here(OPTS.bans)
    REG = Registry(OPTS.identities or None, OPTS.name_ttl_days, [x for x in OPTS.reserved.split(",")])
    setup_log()
    bans_load()
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
            LOG.info(f"serveur | presence_server {VERSION} | écoute sur {OPTS.host}:{OPTS.port}  (Ctrl+C pour arrêter)")
            if OPTS.host in ("0.0.0.0", "::", ""):
                ip = lan_ip()
                LOG.info(f"serveur | adresses à donner à --presence-url : {scheme}://127.0.0.1:{OPTS.port} (cette machine)" + (f" · {scheme}://{ip}:{OPTS.port} (autres appareils du réseau)" if ip else ""))
                LOG.info("serveur | n'utilise jamais 0.0.0.0 dans --presence-url : c'est une adresse d'écoute, pas une destination")
            else:
                LOG.info(f"serveur | adresse à donner à --presence-url : {scheme}://{OPTS.host}:{OPTS.port}")
            LOG.info(f"serveur | journal : {OPTS.log or '(aucun : option --log)'} | registre des noms : {OPTS.identities or '(en mémoire)'}")
            print("modération : tape « aide » pour la liste des commandes (liste, ejecter, bannir, bans, debannir)")
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
