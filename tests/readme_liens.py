#!/usr/bin/env python3
"""Liens et images locaux des README (fr et en) et des documents de docs/ : chaque cible relative doit exister dans le depot.

Garde contre la suppression d'un fichier qu'un document montre ou cite (cas du GIF de demonstration, supprime par erreur le 07/11/2026).
Ignore : liens http(s), mailto, ancres seules, blocs de code. Une ancre ou une requete apres le chemin est retiree avant le test.
Lancer : python tests/readme_liens.py
"""
import pathlib, re, sys
from urllib.parse import unquote

ROOT = pathlib.Path(__file__).resolve().parent.parent
docs = [ROOT / "README.md", ROOT / "README.fr.md"] + sorted((ROOT / "docs").rglob("*.md"))
RX = re.compile(r'!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+"[^"]*")?\s*\)|<img[^>]+src="([^"]+)"', re.I)
echecs = 0
manque = []
n = 0
for d in docs:
    if not d.exists():
        manque.append((d.relative_to(ROOT).as_posix(), "document absent"))
        continue
    fence = False
    for no, ligne in enumerate(d.read_text(encoding="utf-8").splitlines(), 1):
        if ligne.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        for m in RX.finditer(ligne):
            cible = (m.group(1) or m.group(2)).strip()
            if re.match(r"^([a-z][a-z0-9+.-]*:|#|//)", cible, re.I):
                continue
            chemin = unquote(re.split(r"[#?]", cible)[0])
            if not chemin:
                continue
            n += 1
            base = ROOT if chemin.startswith("/") else d.parent
            if not (base / chemin.lstrip("/")).exists():
                manque.append((f"{d.relative_to(ROOT).as_posix()}:{no}", chemin))
print(f"{len(docs)} document(s), {n} lien(s) ou image(s) locaux verifies")
for ou, c in manque:
    print(f"[ECHEC] {ou} : cible absente : {c}")
echecs = len(manque)
if not echecs:
    print("[OK]    toutes les cibles locales existent")
print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
sys.exit(1 if echecs else 0)
