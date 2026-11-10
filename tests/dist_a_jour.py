#!/usr/bin/env python3
"""dist/ est-il a jour ? Fabrique dans un dossier temporaire (python build.py --out ...) et compare avec dist/ (fins de ligne LF/CRLF ignorees).

dist/ est suivi par git : il doit toujours correspondre a src/ et tools/. Apres chaque lot : python build.py, puis git add -A dist.
Le test ne touche ni dist/ ni VERSIONS.json (restaure apres la fabrication). Variable facultative : THREE_DIR (racine d'un paquet npm three, hors ligne).
Lancer : python tests/dist_a_jour.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import os, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
VERS = ROOT / "VERSIONS.json"
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def liste(d):
    return {p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix not in (".pyc", ".log") and p.relative_to(d).parts[0] != "convoar"}   # dist/convoar : copie fournie, pas fabriquee par build.py


tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_dist_"))
avant = VERS.read_bytes() if VERS.exists() else None
cmd = [sys.executable, str(ROOT / "build.py"), "--out", str(tmp)] + (["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else [])
try:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
finally:
    if avant is not None:
        VERS.write_bytes(avant)
rapport(r.returncode == 0, "fabrication dans un dossier temporaire", (r.stdout + r.stderr)[-300:])
if not DIST.is_dir():
    rapport(False, "dist/ existe", "dossier absent : lancer python build.py")
elif r.returncode == 0:
    neuf, actuel = liste(tmp), liste(DIST)
    rapport(not (neuf - actuel), "tous les fichiers fabriques sont dans dist/", sorted(neuf - actuel))
    rapport(not (actuel - neuf), "dist/ ne contient aucun fichier que la fabrication ne produit plus", sorted(actuel - neuf))
    lf = lambda p: p.read_bytes().replace(b"\r\n", b"\n")   # .gitattributes : git normalise les fins de ligne en LF, un build sous Windows peut ecrire du CRLF
    diff = [f for f in sorted(neuf & actuel) if lf(tmp / f) != lf(DIST / f)]
    rapport(not diff, "chaque fichier de dist/ est identique a une fabrication neuve (fins de ligne ignorees)", diff)
print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs}) : lancer python build.py puis git add -A dist"))
sys.exit(1 if echecs else 0)
