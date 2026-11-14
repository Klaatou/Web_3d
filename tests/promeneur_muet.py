#!/usr/bin/env python3
"""Tests 1.10.37 : promeneur muet (vrai presence_server.py, --idle-walk).

Une page de promeneur restee ouverte en arriere-plan n'envoie plus de position (boucle d'animation gelee par le navigateur) mais garde
sa connexion : le visiteur restait compte et montre aux autres jusqu'a la deconnexion. Verifie, avec --idle-walk 0.05 (3 s) :
1. un promeneur sans position depuis 3 s : les autres recoivent « leave », un nouveau venu ne le voit pas dans « welcome »,
   la requete « rooms » ne le compte plus ; le promeneur actif reste compte ;
2. il garde sa place : avec --max-per-room 2, un troisieme promeneur est refuse (« full ») pendant qu'il est muet ;
3. sa premiere position suivante : les autres recoivent « join » avec sa position, il est de nouveau compte ;
4. un muet qui se deconnecte : aucun second « leave » ;
5. --idle-walk 0 : jamais muet (meme silence de 4 s, toujours compte).
Sur le main d'origine (1.10.36) : lancer avec SANS_IDLE=1 (l'option --idle-walk n'y existe pas) : 1, 3 et 4 echouent, 2 et 5 passent.

Prerequis : pip install websockets ; python build.py avant. Lancer : python tests/promeneur_muet.py
"""
import asyncio, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import websockets

SANS = bool(os.environ.get("SANS_IDLE"))


def connect(port):
    return websockets.connect(f"ws://127.0.0.1:{port}")


async def recv_t(ws, t, delai=1.0, pred=None):
    """attend un message de type t (et pred(m) vrai) ; None si rien dans le delai"""
    fin = time.monotonic() + delai
    while True:
        reste = fin - time.monotonic()
        if reste <= 0:
            return None
        try:
            m = json.loads(await asyncio.wait_for(ws.recv(), reste))
        except asyncio.TimeoutError:
            return None
        if m.get("t") == t and (pred is None or pred(m)):
            return m


async def hello(ws, nom, uid, spectator=False):
    await ws.send(json.dumps({"t": "hello", "room": "muet", "name": nom, "uid": uid * 20, "spectator": spectator}))
    return await recv_t(ws, "welcome", 2.0)


async def pos(ws, x):
    await ws.send(json.dumps({"t": "pos", "p": [x, 0, 0], "yaw": 0}))


async def rooms(port):
    async with connect(port) as ws:
        await ws.send(json.dumps({"t": "rooms"}))
        return (await recv_t(ws, "rooms", 2.0) or {}).get("rooms", {})


async def actif(ws, duree):
    """envoie une position toutes les 0,5 s pendant duree secondes et retourne les messages recus"""
    recus = []
    fin = time.monotonic() + duree
    while time.monotonic() < fin:
        await pos(ws, 1.0)
        try:
            recus.append(json.loads(await asyncio.wait_for(ws.recv(), 0.5)))
        except asyncio.TimeoutError:
            pass
    return recus


async def scenario(port):
    r = {}
    async with connect(port) as a, connect(port) as b:
        wa = await hello(a, "Muet", "a")
        wb = await hello(b, "Actif", "b")
        ida = wa["id"]
        await pos(a, 5.0)
        await pos(b, 1.0)
        await asyncio.sleep(0.3)
        # 1 : A se tait, B continue
        recus = await actif(b, 5.0)
        r["leave"] = any(m.get("t") == "leave" and m.get("id") == ida for m in recus)
        async with connect(port) as c:
            wc = await hello(c, "", "c", spectator=True)
            r["welcome_sans_muet"] = wc is not None and [p["id"] for p in wc.get("peers", [])] == [wb["id"]]
        r["rooms_1"] = (await rooms(port)).get("muet") == 1
        # 2 : place gardee (--max-per-room 2)
        async with connect(port) as d:
            await d.send(json.dumps({"t": "hello", "room": "muet", "name": "Trois", "uid": "d" * 20, "spectator": False}))
            r["full"] = await recv_t(d, "full", 2.0) is not None
        # 3 : retour
        await pos(a, 6.0)
        j = await recv_t(b, "join", 2.0, lambda m: m.get("id") == ida)
        r["join"] = j is not None and j.get("p") == [6.0, 0, 0]
        r["rooms_2"] = (await rooms(port)).get("muet") == 2
        # 4 : muet puis deconnexion : un seul leave
        recus = await actif(b, 5.0)
        r["leave_bis"] = any(m.get("t") == "leave" and m.get("id") == ida for m in recus)
        await a.close()
        recus = await actif(b, 1.5)
        r["pas_second_leave"] = not any(m.get("t") == "leave" and m.get("id") == ida for m in recus)
    return r


async def jamais(port):
    async with connect(port) as a, connect(port) as b:
        wa = await hello(a, "Muet", "a")
        await hello(b, "Actif", "b")
        await pos(a, 5.0)
        recus = await actif(b, 4.0)
        return not any(m.get("t") == "leave" and m.get("id") == wa["id"] for m in recus) and (await rooms(port)).get("muet") == 2


proc, port = lancer_presence("--lang", "fr", "--max-per-room", "2", *([] if SANS else ["--idle-walk", "0.05"]))
try:
    r = asyncio.run(scenario(port))
    rapport(r["leave"] and r["welcome_sans_muet"] and r["rooms_1"], "promeneur sans position depuis 3 s : « leave » recu par l'autre, absent du « welcome » d'un nouveau venu, « rooms » ne compte que l'actif", r)
    rapport(r["full"], "le muet garde sa place : --max-per-room 2, troisieme promeneur refuse", r)
    rapport(r["join"] and r["rooms_2"], "premiere position apres le silence : « join » avec la position, de nouveau compte", r)
    rapport(r["leave_bis"] and r["pas_second_leave"], "muet puis deconnecte : un seul « leave »", r)
finally:
    proc.kill()
    out = proc.communicate()[0]
rapport(SANS or ("muet (aucune position depuis 0 min)" in out and "de retour (position reçue)" in out), "journal : lignes « muet » et « de retour »", out[-600:])

proc, port = lancer_presence("--lang", "fr", *([] if SANS else ["--idle-walk", "0"]))
try:
    rapport(asyncio.run(jamais(port)), "--idle-walk 0 : jamais muet apres 4 s de silence")
finally:
    proc.kill()
    proc.communicate()

sys.exit(1 if resultat() else 0)
