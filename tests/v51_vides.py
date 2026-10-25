#!/usr/bin/env python3
"""Tests v51 (suite, livrée d'abord en v52) : connexions ouvertes puis fermées sans requête (vrai presence_server.py).

websockets 14 et 15 écrivaient une trace complète (« opening handshake failed », EOFError) pour chaque connexion TCP fermée sans requête
(préconnexion d'un navigateur, test de port, robot). Vérifie : aucune trace ; une seule ligne « vide » avec l'adresse pour 5 connexions
(au plus une par minute et par adresse) ; une requête mal formée garde son message d'erreur ; un visiteur normal est toujours accueilli.
Avec la version de websockets installée, puis, si la variable WS_OLD donne un dossier contenant websockets 14 ou 15
(pip install --target DOSSIER "websockets==14.2"), avec cette version.

Prérequis : pip install websockets ; python build.py avant. Lancer : python tests/v51_vides.py
"""
import asyncio, json, os, socket, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37
import websockets


def essai(pythonpath, nom):
    port = port_libre()
    env = dict(os.environ)
    if pythonpath:
        env["PYTHONPATH"] = pythonpath
    proc = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--lang", "fr", "--host", "127.0.0.1", "--port", str(port), "--identities", "", "--log-ip", "raw"],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    attendre_port(port, proc, "presence_server")
    ver = subprocess.run([sys.executable, "-c", "import websockets; print(websockets.__version__)"], capture_output=True, text=True, env=env).stdout.strip()
    print(f"--- {nom} (websockets {ver})")
    for _ in range(5):
        socket.create_connection(("127.0.0.1", port)).close()
    s = socket.create_connection(("127.0.0.1", port))
    s.sendall(b"bonjour\r\n\r\n")
    time.sleep(0.5)
    s.close()

    async def visiteur():
        async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
            await ws.send(json.dumps({"t": "hello", "room": "galerie", "name": "T", "uid": "0123456789abcdef0123", "spectator": True}))
            return json.loads(await ws.recv())
    m = asyncio.run(visiteur())
    time.sleep(1)
    proc.kill()
    out = proc.communicate()[0]
    rapport(m.get("t") == "welcome", "visiteur normal accueilli", m)
    vides = [l for l in out.splitlines() if "| vide" in l]
    trace_eof = "stream ends after 0 bytes" in out
    rapport(not trace_eof, "aucune trace pour les connexions sans requête", out[-800:])
    old = ver.split(".")[0] in ("14", "15")      # 13 et avant (serveur legacy) et 16 et après : rien à filtrer
    if old:
        rapport(len(vides) == 1 and "ip 127.0.0.1" in vides[0] and "connexion ouverte puis fermée sans requête" in vides[0],
                "une seule ligne « vide » avec l'adresse pour 5 connexions", vides)
        rapport("did not receive a valid HTTP request" in out or "invalid" in out.lower(), "requête mal formée : son erreur reste affichée", out[-600:])
    else:
        rapport(not vides, "websockets récent : rien à filtrer, aucune ligne « vide »", vides)


essai("", "version installée")
if os.environ.get("WS_OLD"):
    essai(os.environ["WS_OLD"], "ancienne version (WS_OLD)")
else:
    print("(WS_OLD absent : ancienne version de websockets non essayée)")
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
