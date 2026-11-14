#!/usr/bin/env python3
"""Tests 1.10.28 : registre des pseudos borne, cadence des changements de pseudo, derniere adresse de l'en-tete du relais (vrai presence_server.py).

Un script pouvait inscrire des pseudos sans fin (tout uid de 16 caracteres est persistant, le message « name » n'avait aucun delai,
chaque pseudo nouveau reecrivait le registre) ; avec --proxy-header, la premiere adresse de l'en-tete etait prise, qu'un client peut
ecrire lui-meme (nginx, Caddy, Cloudflare ajoutent la vraie adresse a la FIN). Verifie :
1. deux messages « name » a la suite : le second est ignore (pas de « you »), un troisieme apres 2,2 s est pris ;
2. --max-names 3 (le test 1 a deja reserve un pseudo) : les deux uid suivants reservent leur pseudo (nom sans suffixe), le troisieme garde un nom suffixe (#code) ;
3. --proxy-header X-Forwarded-For sur une connexion WebSocket : le journal montre la derniere adresse de l'en-tete, pas la premiere.
Sur le main d'origine (1.10.27) : les 3 echouent (lancer avec SANS_MAXNAMES=1 : l'option --max-names n'y existe pas).

Prerequis : pip install websockets ; python build.py avant. Lancer : python tests/presence_noms.py
"""
import asyncio, json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import websockets


def connect(port, entetes=None):
    kw = {}
    if entetes:
        kw["additional_headers" if int(websockets.__version__.split(".")[0]) >= 14 else "extra_headers"] = entetes
    return websockets.connect(f"ws://127.0.0.1:{port}", **kw)


async def recv_t(ws, t, delai=1.0):
    """attend un message de type t ; None si rien dans le delai"""
    fin = time.monotonic() + delai
    while True:
        reste = fin - time.monotonic()
        if reste <= 0:
            return None
        try:
            m = json.loads(await asyncio.wait_for(ws.recv(), reste))
        except asyncio.TimeoutError:
            return None
        if m.get("t") == t:
            return m


async def cadence(port):
    async with connect(port) as ws:
        await ws.send(json.dumps({"t": "hello", "room": "noms", "name": "Un", "uid": "a" * 20, "spectator": False}))
        w = await recv_t(ws, "welcome")
        await ws.send(json.dumps({"t": "name", "name": "Deux"}))
        y1 = await recv_t(ws, "you")
        await ws.send(json.dumps({"t": "name", "name": "Trois"}))
        y2 = await recv_t(ws, "you", 0.8)
        await asyncio.sleep(2.2)
        await ws.send(json.dumps({"t": "name", "name": "Quatre"}))
        y3 = await recv_t(ws, "you")
        return w and w["name"] == "Un" and y1 and y1["name"] == "Deux" and y2 is None and y3 and y3["name"] == "Quatre", (w, y1, y2, y3)


async def plafond(port):
    noms = []
    for i, nom in enumerate(("Alpha", "Beta", "Gamma")):
        async with connect(port) as ws:
            await ws.send(json.dumps({"t": "hello", "room": "noms", "name": nom, "uid": chr(98 + i) * 20, "spectator": False}))
            w = await recv_t(ws, "welcome")
            noms.append(w and w["name"])
    return noms[0] == "Alpha" and noms[1] == "Beta" and noms[2] and noms[2].startswith("Gamma#"), noms


async def relais(port):
    async with connect(port, {"X-Forwarded-For": "203.0.113.7, 10.0.0.1"}) as ws:
        await ws.send(json.dumps({"t": "hello", "room": "noms", "name": "Relais", "uid": "f" * 20, "spectator": False}))
        await recv_t(ws, "welcome")


# 1 et 2 : meme serveur, --max-names 3 (le test 1 reserve un pseudo : ses changements remplacent la meme entree)
proc, port = lancer_presence("--lang", "fr", *([] if os.environ.get("SANS_MAXNAMES") else ["--max-names", "3"]))
try:
    ok, det = asyncio.run(cadence(port))
    rapport(ok, "changement de pseudo : le second message « name » a la suite est ignore, le suivant apres 2 s est pris", det)
    ok, det = asyncio.run(plafond(port))
    rapport(ok, "--max-names 3 : le quatrieme pseudo du registre n'est pas reserve (nom suffixe)", det)
finally:
    proc.kill()
    proc.communicate()

# 3 : --proxy-header, journal en clair
port = port_libre()
proc = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--lang", "fr", "--host", "127.0.0.1", "--port", str(port), "--identities", "",
                         "--log-ip", "raw", "--proxy-header", "X-Forwarded-For"], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=tmp)
attendre_port(port, proc, "presence_server")
asyncio.run(relais(port))
time.sleep(0.5)
proc.kill()
out = proc.communicate()[0]
lignes = [l for l in out.splitlines() if "Relais" in l]
rapport(lignes and all("ip 10.0.0.1" in l and "203.0.113.7" not in l for l in lignes), "--proxy-header : la derniere adresse de l'en-tete est retenue (pas celle que le client ecrit)", lignes[:2] or out[-500:])

sys.exit(1 if resultat() else 0)
