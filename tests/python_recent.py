#!/usr/bin/env python3
"""Python recent (lot 1.10.4) : les outils doivent s'ouvrir avec les versions recentes de Python, pas seulement la 3.10.

Contexte : sous Python 3.14, argparse.BooleanOptionalAction n'accepte plus metavar, type ni choices (deprecies des la 3.12). glb2html.py passait metavar
a --sea et --anim : il s'arretait par « TypeError » des l'ouverture, et le lanceur graphique ne pouvait plus lire ses options. Le defaut ne se voyait
que sous Python 3.14.
Verifie :
1. (toute version de Python) aucun add_argument(action=BooleanOptionalAction) des sources ne passe metavar, type ni choices ; lecture du code, sans l'executer ;
2. avec la version qui lance ce test : --help de chaque outil, les avertissements « deprecie » comptant comme des erreurs (la 3.12 et suivantes les emettent) ;
3. avec d'autres versions : si la variable WEB3D_PYTHONS donne des interpreteurs (separes par ; sous Windows, : ailleurs), --help de chaque outil avec chacun.
Lancer : python tests/python_recent.py    ou    $env:WEB3D_PYTHONS="C:\\...\\python3.14.exe"; python tests/python_recent.py
"""
import ast, os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
bad = 0
OUTILS = [ROOT / "src" / "gen_tpl.py", ROOT / "tools" / "oar2glb.py", ROOT / "tools" / "glb2tiles.py", ROOT / "tools" / "glb-stats.py",
          ROOT / "tools" / "extraire_batiments.py", ROOT / "tools" / "iar2oar.py", ROOT / "tools" / "oars2site.py"]      # diag_carte.py et le serveur de presence : websockets, pas d'option en cause
RETIRES = {"metavar", "type", "choices"}


def rapport(ok, titre, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else "  " + str(detail)[:300]))


def booleens():
    """[(fichier, ligne, options passees)] : add_argument(..., action=...BooleanOptionalAction, ...) avec un argument retire en 3.14"""
    mauvais, vus = [], 0
    for f in sorted(list((ROOT / "src").glob("*.py")) + list((ROOT / "tools").glob("*.py"))):
        arbre = ast.parse(f.read_text(encoding="utf-8"), str(f))
        for n in ast.walk(arbre):
            if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "add_argument":
                for k in n.keywords:
                    if k.arg == "action" and getattr(k.value, "attr", getattr(k.value, "id", "")) == "BooleanOptionalAction":
                        vus += 1
                        pris = sorted(RETIRES & {x.arg for x in n.keywords})
                        if pris:
                            mauvais.append((f.name, n.lineno, pris))
    return mauvais, vus


def aide(python, outil, avertissements=False):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", WEB3D_LANG="en")
    cmd = [python, "-u"] + (["-W", "error::DeprecationWarning"] if avertissements else []) + [str(outil), "--help", "--nopause"]
    r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, env=env, cwd=str(ROOT), timeout=120)
    sortie = r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
    derniere = next((l for l in reversed(sortie.splitlines()) if "Error" in l or "Warning" in l), "")
    return r.returncode == 0 and "Traceback" not in sortie, derniere


mauvais, vus = booleens()
rapport(vus >= 10 and not mauvais, f"BooleanOptionalAction : {vus} options lues, aucune ne passe metavar, type ni choices", mauvais)
v = "%d.%d" % sys.version_info[:2]
for o in OUTILS:
    ok, d = aide(sys.executable, o, avertissements=True)
    rapport(ok, f"{o.name} --help avec Python {v}, avertissements « deprecie » = erreurs", d)
autres = [p for p in os.environ.get("WEB3D_PYTHONS", "").split(os.pathsep) if p.strip()]
if not autres:
    print("[IGNORE] autres versions de Python non essayees (variable WEB3D_PYTHONS vide) ; version de ce test : " + v)
for p in autres:
    try:
        nom = subprocess.run([p, "-c", "import sys;print('%d.%d.%d' % sys.version_info[:3])"], capture_output=True, text=True, timeout=30).stdout.strip() or p
    except OSError as e:
        rapport(False, f"interpreteur {p} introuvable", e)
        continue
    for o in OUTILS:
        ok, d = aide(p, o)
        rapport(ok, f"{o.name} --help avec Python {nom}", d)
print("\nRESULTAT :", "tout est passe" if not bad else f"{bad} echec(s)")
sys.exit(1 if bad else 0)
