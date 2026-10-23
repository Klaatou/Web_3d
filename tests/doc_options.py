#!/usr/bin/env python3
"""REFERENCE_OPTIONS.md (v36, hors navigateur) : toutes les options des quatre outils y figurent, avec une description non vide en français ET en anglais,
et le fichier du dépôt est à jour (même contenu que gen_reference.py, hors ligne de date). Lancer python build.py d'abord (gen_reference lit dist/)."""
import pathlib, re, sys, tempfile, subprocess, argparse
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import gen_reference as G
NB = 0
def rapport(ok, msg, detail=""):
    global NB
    print(("[OK]    " if ok else "[ECHEC] ") + msg + ("" if ok else "  " + str(detail)))
    if not ok: NB += 1
dist = ROOT / "dist"
texte, tout, manques = G.generer(dist)
rapport(not manques, "chaque option a une description en français et en anglais, mêmes options dans les deux langues", manques[:6])
rapport(sorted(tout) == sorted(n for n, _, _ in G.OUTILS), "les quatre outils sont lus", sorted(tout))
for nom, fichier, _ in G.OUTILS:
    p = G.lire_parser(dist / fichier, "en")
    opts = [o for a in p._actions for o in a.option_strings if o.startswith("--") and o != "--help"]
    absentes = [o for o in opts if f"`{o}`" not in texte]
    rapport(not absentes, f"{fichier} : {len(opts)} options, toutes dans la référence", absentes[:5])
    for lg in ("fr", "en"):
        q = G.lire_parser(dist / fichier, lg)
        vides = [a.option_strings[0] if a.option_strings else a.dest for a in q._actions if not (a.help and a.help.strip())]
        rapport(not vides, f"{fichier} ({lg}) : aucune description vide", vides[:5])
def sans_date(t):
    return re.sub(r"Générée le \d\d/\d\d/\d{4}", "Générée le", t)
repo = (ROOT / "REFERENCE_OPTIONS.md").read_text(encoding="utf-8")
rapport(sans_date(repo) == sans_date(texte), "REFERENCE_OPTIONS.md est à jour (python gen_reference.py)")
# bilingue : chaque ligne de tableau porte le français puis l'anglais séparés par <br>
lignes = [l for l in texte.splitlines() if l.startswith("| `")]
rapport(lignes and all("<br>" in l for l in lignes), f"{len(lignes)} lignes d'options, chacune avec <br> entre le français et l'anglais")
rapport("*" not in re.sub(r"\*[^*\n]*\*", "", texte).replace("**", ""), "plus de description de secours marquée *")
print("\nRÉSULTAT :", "tout est passé" if not NB else f"{NB} échec(s)")
sys.exit(1 if NB else 0)
