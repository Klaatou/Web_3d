#!/usr/bin/env python3
"""Tests v52 (suite) : requete HTTP ordinaire sur le port du serveur de presence (vrai presence_server.py).

websockets 14 et 15 ecrivaient une trace complete (« opening handshake failed », InvalidUpgrade, « invalid Connection header: keep-alive ») pour une requete
HTTP qui n'ouvre pas de WebSocket (navigateur qui ouvre l'adresse du serveur, robot, test), alors que le client recoit bien « 426 Upgrade Required ».
Verifie : le client recoit toujours 426 ; aucune trace ; une seule ligne « requete http » (adresse, chemin, hote, agent, raison) pour 3 requetes
(au plus une par minute et par adresse) ; une requete illisible donne une ligne courte ; un visiteur normal est toujours accueilli.
Avec la version de websockets installee, puis, si WS_OLD donne un dossier contenant websockets 14 ou 15 (pip install --target DOSSIER "websockets==14.2"),
avec cette version. Les versions recentes (16 et apres) n'ecrivent pas cette trace : rien a filtrer, aucune ligne.

Prerequis : pip install websockets ; python build.py avant. Lancer : python tests/v52_http.py
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
    reps = []
    for chemin in ("/", "/favicon.ico", "/robots.txt"):
        s = socket.create_connection(("127.0.0.1", port))
        s.sendall(f"GET {chemin} HTTP/1.1\r\nHost: exemple.test:{port}\r\nUser-Agent: Mozilla/5.0 (essai v52)\r\nConnection: keep-alive\r\n\r\n".encode())
        time.sleep(0.3)
        reps.append(s.recv(300).decode("latin1").split("\r\n")[0])
        s.close()
    s = socket.create_connection(("127.0.0.1", port))
    s.sendall(b"bonjour\r\n\r\n")
    time.sleep(0.5)
    s.close()
    for sonde in (b"\x03\x00\x00/*\xe0\x00\x00\x00\x00\x00Cookie: mstshash=Administr\r\n", b"\x16\x03\x01\x02\x00\x01\x00\x01\xfc\x03\x03" + bytes(40) + b"\r\n"):   # sondage RDP, debut d'une connexion TLS
        s = socket.create_connection(("127.0.0.1", port))
        s.sendall(sonde)
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
    rapport(all(r.startswith("HTTP/1.1 426") for r in reps), "le client recoit toujours « 426 Upgrade Required »", reps)
    rapport(m.get("t") == "welcome", "visiteur normal accueilli", m)
    lignes = [l for l in out.splitlines() if "| requête http" in l]
    old = ver.split(".")[0] in ("14", "15")      # 13 et avant (serveur legacy) et 16 et apres : rien a filtrer
    if old:
        rapport(len(lignes) == 1, "une seule ligne « requête http » pour 3 requetes", lignes)
        l = lignes[0] if lignes else ""
        rapport("ip 127.0.0.1" in l and "GET /" in l and f"exemple.test:{port}" in l and "Mozilla/5.0 (essai v52)" in l and "invalid Connection header: keep-alive" in l,
                "la ligne dit l'adresse, le chemin, l'hote, l'agent et la raison", l)
        rapport(out.count("opening handshake failed") == 0, "plus aucune trace complete : ni les 3 GET ni les requetes illisibles", out.count("opening handshake failed"))
        illis = [l for l in out.splitlines() if "| requête illisible" in l]
        rapport(len(illis) == 3, "trois lignes « requête illisible » : bonjour, sondage RDP, connexion TLS (une par sorte et par adresse)", illis)
        rapport(any("sondage du Bureau à distance Windows (RDP)" in l and "mstshash" in l for l in illis) and any("connexion chiffrée (https)" in l for l in illis) and any("bonjour" in l and "ce n'est pas une requête HTTP" in l for l in illis),
                "chaque sorte est reconnue et montre son debut", illis)
    else:
        rapport(not lignes, "websockets recent : rien a filtrer, aucune ligne « requête http »", lignes)


essai("", "version installee")
for var in ("WS_OLD", "WS_OLD2"):
    if os.environ.get(var):
        essai(os.environ[var], f"ancienne version ({var})")
if not os.environ.get("WS_OLD"):
    print("(WS_OLD absent : ancienne version de websockets non essayee)")
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
