#!/usr/bin/env python3
"""Adresse des lignes « requête http » derriere un relais (--proxy-header) : vrai presence_server.py.

Avant : ces lignes (EmptyConnFilter, empty_conn_ip) donnaient toujours l'adresse du relais (127.0.0.1 derriere Tailscale Funnel), alors que les
connexions WebSocket donnaient la vraie (remote_ip). Verifie : avec --proxy-header, la requete HTTP est attribuee a la premiere adresse de l'en-tete ;
sans l'en-tete dans la requete, a celle du relais ; sans --proxy-header, l'en-tete est ignore ; le client recoit toujours 426.
websockets 14 et 15 seulement ecrivent la ligne (voir v52_http.py) : avec une version plus recente, rien a verifier ici.
Avec la version installee, puis, si WS_OLD donne un dossier contenant websockets 14 ou 15 (pip install --target DOSSIER "websockets==15.0.1"), avec celle-ci.

Prerequis : pip install websockets ; python build.py avant. Lancer : python tests/http_proxy.py
"""
import os, socket, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37


def requete(pythonpath, proxy, entetes):
    port = port_libre()
    env = dict(os.environ)
    if pythonpath:
        env["PYTHONPATH"] = pythonpath
    cmd = [sys.executable, str(DIST / "presence_server.py"), "--lang", "fr", "--host", "127.0.0.1", "--port", str(port), "--identities", "", "--log-ip", "raw"]
    if proxy:
        cmd += ["--proxy-header", "X-Forwarded-For"]
    proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    attendre_port(port, proc, "presence_server")
    s = socket.create_connection(("127.0.0.1", port))
    s.sendall((f"GET /ai.json HTTP/1.1\r\nHost: exemple.test:{port}\r\nUser-Agent: essai relais\r\nConnection: keep-alive\r\n" + entetes + "\r\n").encode())
    time.sleep(0.4)
    rep = s.recv(300).decode("latin1").split("\r\n")[0]
    s.close()
    time.sleep(0.6)
    proc.kill()
    out = proc.communicate()[0]
    return rep, [l for l in out.splitlines() if "| requête http" in l]


def essai(pythonpath, nom):
    ver = subprocess.run([sys.executable, "-c", "import websockets; print(websockets.__version__)"], capture_output=True, text=True,
                         env=dict(os.environ, **({"PYTHONPATH": pythonpath} if pythonpath else {}))).stdout.strip()
    print(f"--- {nom} (websockets {ver})")
    if ver.split(".")[0] not in ("14", "15"):
        print("(cette version n'ecrit pas la ligne « requête http » : rien a verifier ici)")
        return
    xff = "X-Forwarded-For: 203.0.113.7, 10.0.0.1\r\n"
    rep, l = requete(pythonpath, True, xff)
    rapport(rep.startswith("HTTP/1.1 426") and len(l) == 1 and "ip 203.0.113.7 " in l[0] and "127.0.0.1" not in l[0].split("GET")[0],
            "--proxy-header : la ligne donne la premiere adresse de l'en-tete", l)
    rep, l = requete(pythonpath, True, "")
    rapport(len(l) == 1 and "ip 127.0.0.1 " in l[0], "--proxy-header sans l'en-tete dans la requete : adresse du relais", l)
    rep, l = requete(pythonpath, False, xff)
    rapport(rep.startswith("HTTP/1.1 426") and len(l) == 1 and "ip 127.0.0.1 " in l[0], "sans --proxy-header : l'en-tete est ignore", l)
    rep, l = requete(pythonpath, True, "X-Forwarded-For:  \r\n")
    rapport(len(l) == 1 and "ip 127.0.0.1 " in l[0], "--proxy-header avec un en-tete vide : adresse du relais", l)


essai("", "version installee")
for var in ("WS_OLD", "WS_OLD2"):
    if os.environ.get(var):
        essai(os.environ[var], f"ancienne version ({var})")
if not os.environ.get("WS_OLD"):
    print("(WS_OLD absent : websockets 14 ou 15 non essaye)")
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
