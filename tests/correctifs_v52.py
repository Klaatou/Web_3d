#!/usr/bin/env python3
"""Tests du lot correctif apres l'audit du 26/10/2026 (vrai presence_server.py, git).

Verifie : une requete HTTP dont le chemin contient des caracteres de controle (echappement de terminal, sonnerie) ne les fait pas entrer
dans le journal (websockets 14 ou 15 par WS_OLD, la ou cette ligne existe) ; un createur avec une origine null JSON (sans guillemets)
donne un avertissement et l'origine est ignoree ; .gitignore ecarte les fichiers de zones reels, l'historique du chat et le journal des
visites, mais pas les exemples de docs/samples.

Prerequis : pip install websockets ; python build.py avant. Lancer : python tests/correctifs_v52.py
"""
import json, os, pathlib, socket, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37


def serveur(pythonpath, *opts):
    port = port_libre()
    env = dict(os.environ)
    if pythonpath:
        env["PYTHONPATH"] = pythonpath
    proc = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--lang", "fr", "--host", "127.0.0.1", "--port", str(port), "--identities", "", "--log-ip", "raw", *opts],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    attendre_port(port, proc, "presence_server")
    return proc, port


print("--- 1. journal sans caracteres de controle")
if os.environ.get("WS_OLD"):
    proc, port = serveur(os.environ["WS_OLD"])
    s = socket.create_connection(("127.0.0.1", port))
    s.sendall(b"GET /\x1b[31mROUGE\x07 HTTP/1.1\r\nHost: exemple.test\r\nUser-Agent: essai\r\nConnection: keep-alive\r\n\r\n")
    time.sleep(0.5)
    s.recv(200)
    s.close()
    time.sleep(0.5)
    proc.kill()
    out = proc.communicate()[0]
    lignes = [l for l in out.split(b"\n") if "requête http".encode() in l]
    rapport(len(lignes) == 1 and b"ROUGE" in lignes[0], "la requete donne bien sa ligne « requête http »", lignes)
    rapport(not any(c in out for c in (b"\x1b", b"\x07")), "aucun caractere d'echappement ni de sonnerie dans le journal", [l[:120] for l in lignes])
else:
    print("(WS_OLD absent : websockets 14 ou 15 non essaye, la ligne « requête http » n'existe qu'avec eux)")

print("--- 2. createurs : origine null sans guillemets")
cr = tmp / "createurs.json"
cr.write_text(json.dumps({"creators": [{"id": "jj2", "prefix": "", "origins": ["http://localhost:8000", None]}]}), encoding="utf-8")
proc, port = serveur("", "--creators", str(cr))
time.sleep(1)
proc.kill()
out = proc.communicate()[0].decode("utf-8", "replace")
rapport("origine null écrite sans guillemets" in out and "jj2" in out, "avertissement : null sans guillemets, ignore", out[-500:])
rapport("(1)" in out, "l'autre origine du createur reste prise en compte (1 createur lu)", out[-300:])

print("--- 3. .gitignore")
racine = pathlib.Path(__file__).resolve().parent.parent
if (racine / ".git").exists():
    def ignore(nom):
        return subprocess.run(["git", "check-ignore", "-q", nom], cwd=racine).returncode == 0
    for nom in ("Houses.zones.json", "sites/hobbit/hobbit.zones.json", "zones.json", "chat.jsonl", "visits.jsonl", "presence_creators.json"):
        rapport(ignore(nom), f"ignore par git : {nom}")
    for nom in ("docs/samples/visits.sample.jsonl", "docs/samples/region.zones.sample.json", "src/i18n/fr.json"):
        rapport(not ignore(nom), f"suivi par git : {nom}")
else:
    print("(pas de depot git ici : controle de .gitignore non fait)")

print("--- 4. oar2glb : convoar introuvable")
oar_vide = tmp / "vide.oar"
oar_vide.write_bytes(b"")
URL = "https://github.com/Misterblue/convoar/tree/master/bin"
outil = str(DIST / "oar2glb.py")
r = subprocess.run([sys.executable, outil, str(oar_vide), "--nopause", "--convoar", str(tmp / "absent" / "convoar.exe")], capture_output=True, text=True)
sortie = r.stdout + r.stderr
rapport(r.returncode != 0 and URL in sortie and "--convoar CHEMIN" in sortie, "convoar absent : le message donne l'adresse de telechargement et l'option --convoar CHEMIN", sortie[-300:])
env = dict(os.environ, CONVOAR=str(tmp / "autre" / "convoar.exe"))
r = subprocess.run([sys.executable, outil, str(oar_vide), "--nopause"], capture_output=True, text=True, env=env)
rapport(str(tmp / "autre" / "convoar.exe") in r.stdout + r.stderr, "la variable CONVOAR est utilisee quand --convoar n'est pas donne", (r.stdout + r.stderr)[-200:])
env = {k: v for k, v in os.environ.items() if k != "CONVOAR"}
env["PATH"] = str(tmp)
r = subprocess.run([sys.executable, outil, str(oar_vide), "--nopause"], capture_output=True, text=True, env=env)
rapport(str(DIST / "convoar.exe") in r.stdout + r.stderr, "sans option ni variable ni PATH : convoar.exe a cote de oar2glb.py", (r.stdout + r.stderr)[-200:])
aide = subprocess.run([sys.executable, outil, "--help"], capture_output=True, text=True).stdout
rapport("MOSES" not in aide and "CONVOAR" in aide and URL in aide, "l'aide : aucun chemin personnel, variable CONVOAR et adresse de telechargement")
src = (pathlib.Path(__file__).resolve().parent.parent / "tools" / "oar2glb.py").read_text(encoding="utf-8")
rapport("MOSES" not in src and "P:\\_OpenSim" not in src, "le code d'oar2glb.py ne contient plus de chemin personnel")

print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
