#!/usr/bin/env python3
"""Console de moderation : sequences d'echappement du terminal, commande « version », empreinte (vrai presence_server.py).

Verifie : une ligne precedee de reponses du terminal (tmux), de fleches, de molette, d'une sequence OSC ou SS3 est executee comme si elle etait propre
(avant, « commande inconnue ») ; « version » et « aide » donnent la version et l'empreinte du fichier (inscrite par build.py) ;
--version de dist\ la donne aussi ; lance depuis src\ (rien n'a ete inscrit), seule la version est donnee.

Prerequis : pip install websockets ; python build.py avant. Lancer : python tests/console.py
"""
import os, subprocess, sys, threading, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

import re
REV = re.search(r'^MARK = "([0-9a-f]{8})"', (DIST / "presence_server.py").read_text(encoding="utf-8"), re.M).group(1)   # empreinte inscrite par build.py
SEQ = {
    "reponses du terminal (tmux)": b"\x1b[?61;4;6;7;14;21;22;23;24;28;32;42;52c\x1b[>0;10;1c",
    "fleches": b"\x1b[A\x1b[B\x1b[D",
    "molette (souris SGR)": b"\x1b[<64;10;5M\x1b[<65;10;5M",
    "souris ancienne": b"\x1b[M`!!",
    "touches en mode application (SS3)": b"\x1bOA\x1bOB",
    "couleur du texte (OSC 10)": b"\x1b]10;rgb:cccc/cccc/cccc\x1b\\",
}


def session(entrees):
    port = port_libre()
    proc = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--lang", "fr", "--host", "127.0.0.1", "--port", str(port), "--identities", ""],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            env=dict(os.environ, PYTHONIOENCODING="utf-8"))   # Windows : la sortie d'un tube est en cp1252 sans cela (le test la lit en UTF-8)
    attendre_port(port, proc, "presence_server")
    morceaux = []

    def lire():   # sortie lue pendant le test : un tube de Windows ne garde que 4 Ko, le serveur s'y bloque sinon (l'aide en fait 2) ; sous Linux 64 Ko suffisent
        while True:
            d = proc.stdout.read1(65536)
            if not d:
                break
            morceaux.append(d)
    fil = threading.Thread(target=lire, daemon=True)
    fil.start()
    for e in entrees:
        proc.stdin.write(e)
        proc.stdin.flush()
        time.sleep(0.4)
    proc.kill()
    proc.wait()
    fil.join(10)
    proc.stdin.close()
    return b"".join(morceaux).decode("utf-8", "replace")


out = session([s + b"aide\n" for s in SEQ.values()] + [b"version\n", b"VERSION\n", b"\x1b[Aver\n"])
n_aide = out.count("commandes (tape-les ici, puis Entrée) :")
rapport(n_aide == len(SEQ), f"« aide » reconnue derriere chacune des {len(SEQ)} sortes de sequences", f"{n_aide} sur {len(SEQ)}, fin de la sortie : {out[-900:]!r}")
rapport("commande inconnue" not in out, "aucune « commande inconnue »", [l for l in out.splitlines() if "inconnue" in l][:2])
tete = [l for l in out.splitlines() if l.startswith("presence_server ")]
rapport(len(tete) == len(SEQ) + 3 and all(l == tete[0] for l in tete) and "empreinte " + REV in tete[0], "« aide » et « version » donnent la version et l'empreinte", (len(tete), len(SEQ) + 3, tete[:2]))
v = subprocess.run([sys.executable, str(DIST / "presence_server.py"), "--lang", "fr", "--version"], capture_output=True, text=True, timeout=30)
rapport(v.returncode == 0 and "empreinte " + REV in v.stdout, "--version (dist) donne l'empreinte", v.stdout)
v = subprocess.run([sys.executable, str(ROOT / "src" / "presence_server.py"), "--lang", "fr", "--version"], capture_output=True, text=True, timeout=30, cwd=str(ROOT / "src"))
rapport(v.returncode == 0 and "empreinte" not in v.stdout and "presence_server" in v.stdout, "--version (src) : pas d'empreinte inventee", v.stdout + v.stderr[-120:])
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
