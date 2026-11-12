#!/usr/bin/env python3
"""Pause « Entree » des outils (lot 1.10.3) : glb2tiles.py et oar2glb.py n'attendent plus Entree apres --help, et l'attendent toujours apres un vrai passage.

L'entree des outils est un faux terminal (pty), seul moyen de reproduire une console : isatty() est vrai.
1. --help : l'outil se termine seul (code 0) sans qu'on appuie sur Entree ; -h pareil ;
2. sens oppose : sans --help (un fichier inexistant, erreur immediate), l'outil attend Entree : il est encore la apres 4 s, puis se termine quand on appuie.
Linux et macOS seulement (le module pty n'existe pas sous Windows : la partie est ignoree, dite clairement).
Lancer : python tests/aide_sans_pause.py
"""
import os, pathlib, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
bad = 0


def rapport(ok, titre, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else "  " + str(detail)[:300]))


try:
    import pty
except ImportError:
    print("[IGNORE] pas de pty sous Windows : pause non essayee ici (a regarder a la main : python glb2tiles.py --help ne doit plus attendre Entree)")
    print("\nRESULTAT : tout est passe")
    sys.exit(0)

env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", WEB3D_LANG="en")


def lancer(outil, args):
    maitre, esclave = pty.openpty()
    p = subprocess.Popen([sys.executable, "-u", str(ROOT / "tools" / outil)] + args, stdin=esclave, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, cwd=str(ROOT))
    os.close(esclave)
    return p, maitre


def attendre(p, delai):
    t = time.time()
    while time.time() - t < delai:
        if p.poll() is not None:
            return p.returncode
        time.sleep(0.1)
    return None


for outil in ("glb2tiles.py", "oar2glb.py"):
    for aide in ("--help", "-h"):
        p, m = lancer(outil, [aide])
        code = attendre(p, 20)
        if code is None:
            p.kill()
            p.wait()
        os.close(m)
        rapport(code == 0, f"{outil} {aide} : se termine seul, sans attendre Entree", "toujours la apres 20 s (code %r)" % (code,))
    p, m = lancer(outil, ["fichier_inexistant_pour_le_test"])
    vivant = attendre(p, 4) is None
    rapport(vivant, f"{outil} sans --help : attend toujours Entree apres le passage", "il s'est termine seul")
    if vivant:
        os.write(m, b"\n")
        code = attendre(p, 20)
        rapport(code is not None, f"{outil} : se termine apres Entree", "toujours la apres Entree")
        if code is None:
            p.kill()
            p.wait()
    os.close(m)

print("\nRESULTAT :", "tout est passe" if not bad else f"{bad} echec(s)")
sys.exit(1 if bad else 0)
