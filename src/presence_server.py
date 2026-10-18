#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
presence_server - serveur de présence pour les pages générées par glb2html.
Relaie uniquement les positions des visiteurs en promenade (aucune donnée stockée sur disque).

Installation :  pip install websockets
Lancement    :  python presence_server.py                       (écoute sur ws://0.0.0.0:8765)
                python presence_server.py --port 9000 --max-per-room 30
                python presence_server.py --cert fullchain.pem --key privkey.pem    (wss:// directement)
                python presence_server.py --origins https://monsite.fr,https://www.monsite.fr

Page hébergée en https -> l'URL doit être en wss:// (certificat requis : --cert/--key,
ou reverse proxy nginx/caddy qui termine le TLS et transmet vers ws://127.0.0.1:8765).
Dans la page : python glb2html.py ile.glb --presence-url wss://monsite.fr/presence --room mon-ile
"""
from __future__ import annotations

import argparse
import asyncio
import colorsys
import json
import math
import random
import re
import ssl
import time

import websockets

ROOMS: dict[str, dict[int, "Peer"]] = {}
PER_IP: dict[str, int] = {}
NEXT_ID = 1
OPTS = None


class Peer:
    __slots__ = ("id", "ws", "name", "color", "p", "yaw", "last", "ip")

    def __init__(self, pid, ws, name, color, ip):
        self.id, self.ws, self.name, self.color, self.ip = pid, ws, name, color, ip
        self.p, self.yaw, self.last = None, 0.0, 0.0

    def public(self):
        d = {"id": self.id, "name": self.name, "color": self.color}
        if self.p is not None:
            d["p"], d["yaw"] = self.p, self.yaw
        return d


def clean_name(s, fallback):
    s = re.sub(r"[\x00-\x1f<>]", "", str(s or "")).strip()[:24]
    return s or fallback


def clean_room(s):
    s = re.sub(r"[^\w .\-]", "", str(s or "")).strip()[:64]
    return s or "default"


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


def remote_ip(ws):
    try:
        return str(ws.remote_address[0])
    except Exception:
        return "?"


async def handler(ws):
    global NEXT_ID
    peer, room, counted = None, None, False
    ip = remote_ip(ws)
    try:
        if PER_IP.get(ip, 0) >= OPTS.max_per_ip:
            await ws.send(json.dumps({"t": "full"}))
            return
        PER_IP[ip] = PER_IP.get(ip, 0) + 1
        counted = True
        raw = await asyncio.wait_for(ws.recv(), 10)
        msg = json.loads(raw)
        if not isinstance(msg, dict) or msg.get("t") != "hello":
            return
        room = clean_room(msg.get("room"))
        peers = ROOMS.setdefault(room, {})
        total = sum(len(r) for r in ROOMS.values())
        if len(peers) >= OPTS.max_per_room or total >= OPTS.max_total:
            await ws.send(json.dumps({"t": "full"}))
            return
        pid, NEXT_ID = NEXT_ID, NEXT_ID + 1
        peer = Peer(pid, ws, clean_name(msg.get("name"), f"Visiteur{pid % 1000:03d}"), random_color(), ip)
        existing = [p.public() for p in peers.values()]
        peers[pid] = peer
        await ws.send(json.dumps({"t": "welcome", "id": pid, "name": peer.name, "color": peer.color, "peers": existing},
                                 separators=(",", ":")))
        await broadcast(room, dict(peer.public(), t="join"), exclude=peer)
        print(f"[+] {peer.name} ({ip}) -> salon '{room}' ({len(peers)})")
        async for raw in ws:
            try:
                m = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(m, dict):
                continue
            t = m.get("t")
            if t == "pos":
                now = time.monotonic()
                if now - peer.last < 0.04:
                    continue
                p = finite_list(m.get("p"), 3)
                yaw = m.get("yaw", 0)
                if p is None or isinstance(yaw, bool) or not isinstance(yaw, (int, float)) or not math.isfinite(yaw):
                    continue
                peer.last, peer.p, peer.yaw = now, p, round(float(yaw), 2)
                await broadcast(room, {"t": "pos", "id": pid, "p": p, "yaw": peer.yaw}, exclude=peer)
            elif t == "name":
                peer.name = clean_name(m.get("name"), peer.name)
                await broadcast(room, {"t": "name", "id": pid, "name": peer.name}, exclude=peer)
    except (websockets.ConnectionClosed, asyncio.TimeoutError, ValueError):
        pass
    finally:
        if peer is not None and room in ROOMS:
            ROOMS[room].pop(peer.id, None)
            await broadcast(room, {"t": "leave", "id": peer.id})
            print(f"[-] {peer.name} ({ip}) <- salon '{room}' ({len(ROOMS[room])})")
            if not ROOMS[room]:
                del ROOMS[room]
        if counted and PER_IP.get(ip):
            PER_IP[ip] -= 1
            if PER_IP[ip] <= 0:
                del PER_IP[ip]


async def main():
    global OPTS
    ap = argparse.ArgumentParser(description="Serveur de présence glb2html (WebSocket)")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--max-per-room", type=int, default=50)
    ap.add_argument("--max-total", type=int, default=500)
    ap.add_argument("--max-per-ip", type=int, default=10, help="connexions simultanées par adresse IP")
    ap.add_argument("--origins", help="origines autorisées, séparées par des virgules (défaut : toutes)")
    ap.add_argument("--cert", help="certificat TLS (wss://)")
    ap.add_argument("--key", help="clé privée TLS")
    OPTS = ap.parse_args()
    ctx = None
    if OPTS.cert:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(OPTS.cert, OPTS.key)
    origins = [o.strip() for o in OPTS.origins.split(",")] if OPTS.origins else None
    async with websockets.serve(handler, OPTS.host, OPTS.port, max_size=4096, origins=origins, ssl=ctx):
        print(f"présence : {'wss' if ctx else 'ws'}://{OPTS.host}:{OPTS.port}  (Ctrl+C pour arrêter)")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
