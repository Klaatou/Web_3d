#!/usr/bin/env python3
"""Marque (empreinte) de chaque fichier fabrique par build.py.

Verifie : deux fabrications donnent les memes marques ; les trois fichiers qui l'affichent (presence_server.py, oar2glb.py, glb2tiles.py) la portent
dans leur ligne MARK et la donnent avec --version ; la marque est bien les 8 premiers caracteres du SHA-256 du fichier dont la marque est vide ;
les autres fichiers ont les 8 premiers caracteres de leur propre SHA-256 ; aucun repere « a remplacer » ne reste ; modifier UN fichier source
ne change que la marque du fichier fabrique qui en vient.

Prerequis : python build.py possible (variable THREE_DIR hors ligne). Lancer : python tests/marque.py
"""
import hashlib, os, pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_marque_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def fabriquer(racine, sortie):
    r = subprocess.run([sys.executable, str(racine / "build.py"), "--out", str(sortie), *vend], capture_output=True, text=True, cwd=racine)
    if r.returncode:
        sys.exit(f"[ECHEC] build.py\n{r.stdout}{r.stderr}")
    marques, vu = {}, False
    for l in r.stdout.splitlines():
        if l.startswith("marques"):
            vu = True
        elif vu and l.strip():
            nom, m = l.split()
            marques[nom] = m
    return marques


m1 = fabriquer(ROOT, tmp / "d1")
m2 = fabriquer(ROOT, tmp / "d2")
rapport(len(m1) >= 8 and m1 == m2, "deux fabrications : les memes marques pour les memes sources", (m1, m2))
tous = sorted(p.name for p in (tmp / "d1").iterdir() if p.is_file())
rapport(sorted(m1) == tous, "une marque pour chaque fichier fabrique", (sorted(m1), tous))
rapport(all(b"__MARK__" not in (tmp / "d1" / n).read_bytes() for n in tous), "aucun repere a remplacer ne reste dans les fichiers fabriques")
for nom in ("presence_server.py", "oar2glb.py", "glb2tiles.py"):
    txt = (tmp / "d1" / nom).read_text(encoding="utf-8")
    mm = re.search(r'^MARK = "([0-9a-f]{8})"', txt, re.M)
    vide = txt.replace('"%s"' % m1[nom], '""')
    calc = hashlib.sha256(vide.encode("utf-8")).hexdigest()[:8]
    rapport(bool(mm) and mm.group(1) == m1[nom] == calc, f"{nom} : la ligne MARK, la liste du build et le calcul (marque vide) donnent la meme marque", (mm and mm.group(1), m1[nom], calc))
    v = subprocess.run([sys.executable, str(tmp / "d1" / nom), "--version"], capture_output=True, text=True, timeout=30)
    rapport(v.returncode == 0 and ("empreinte " + m1[nom]) in v.stdout, f"{nom} --version donne l'empreinte", v.stdout + v.stderr[-100:])
for nom in tous:
    if nom not in ("presence_server.py", "oar2glb.py", "glb2tiles.py"):
        rapport(hashlib.sha256((tmp / "d1" / nom).read_bytes()).hexdigest()[:8] == m1[nom], f"{nom} : marque = 8 premiers caracteres de son SHA-256")
# modifier un seul fichier source : une seule marque change
copie = tmp / "depot"
shutil.copytree(ROOT, copie, ignore=shutil.ignore_patterns(".git", "dist", "_bak", ".cache", "__pycache__", "tests", "extraire_batiments.cache"))
with open(copie / "tools" / "oar2glb.py", "a", encoding="utf-8") as f:
    f.write("\n# modification d'essai\n")
m3 = fabriquer(copie, tmp / "d3")
diff = sorted(n for n in m1 if m1[n] != m3.get(n))
rapport(diff == ["oar2glb.py"], "un commentaire ajoute a tools/oar2glb.py : seule la marque d'oar2glb.py change", diff)
print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
sys.exit(1 if echecs else 0)
