#!/usr/bin/env python3
"""Tests v49 : glb2html.py --scan-sites (hors navigateur).

Vérifie, sur une arborescence de sites fabriquée ici (coquille à la racine, une région par dossier) : une fiche par NOM.config.json
(adresse index.html?region=dossier/NOM, salon, serveur de présence), vignette NOM.jpg / .png / .webp à côté (chemin relatif encodé),
fiche reconnue par son salon puis par son adresse, nom / place / arrivée gardés, en-tête showUrl gardé, fiches externes intactes,
orpheline signalée et gardée, nouvelle région sur une case libre (jamais 0,0 en double), dossiers lib et _bak ignorés, --dry-run n'écrit
rien, deuxième passage sans changement, liste simple gardée en liste, dossier absent refusé, avertissement sans index.html, anglais.

Prérequis : python build.py avant. Lancer : python tests/v49.py
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37


def scan(*a, ok=True, lang="fr"):
    env = dict(os.environ, WEB3D_LANG=lang)
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), "--scan-sites", *map(str, a)], capture_output=True, text=True, env=env)
    if ok and r.returncode:
        sys.exit(f"[ECHEC] --scan-sites {a}\n{r.stdout}{r.stderr}")
    return r


S = tmp / "Sites"
for d in ("houses", "hobbit", "lib", "_bak", "galerie/salle"):
    (S / d).mkdir(parents=True)
(S / "index.html").write_text("x", encoding="utf-8")
(S / "houses" / "Maison (4X4).config.json").write_text(json.dumps({"room": "Maison4X4", "presenceUrl": "ws://ADRESSE:8765"}), encoding="utf-8")
(S / "houses" / "Maison (4X4).png").write_bytes(b"png")
(S / "hobbit" / "hobbit.config.json").write_text(json.dumps({"room": "Hobbit", "presenceUrl": "ws://ADRESSE:8765"}), encoding="utf-8")
(S / "hobbit" / "hobbit.jpg").write_bytes(b"jpg")
(S / "galerie" / "salle" / "expo.config.json").write_text(json.dumps({"room": "", "presenceUrl": ""}), encoding="utf-8")
(S / "lib" / "piege.config.json").write_text(json.dumps({"room": "piege"}), encoding="utf-8")
(S / "_bak" / "copie.config.json").write_text(json.dumps({"room": "copie"}), encoding="utf-8")
(S / "hobbit" / "pas-une-region.config.json").write_text(json.dumps({"autre": 1}), encoding="utf-8")
DEPART = {"showUrl": True, "regions": [
    {"id": "hobbit", "name": "Hobbit Land", "url": "index.html?region=hobbit/hobbit", "x": 1, "y": 0, "spawn": "porte", "room": "Hobbit", "thumb": "", "presence": ""},
    {"id": "marie", "name": "Expo de Marie", "url": "https://galerie.example/index.html?region=expo", "x": 0, "y": 0, "spawn": "", "room": "marie-expo", "thumb": "https://galerie.example/expo.jpg", "presence": "wss://ADRESSE"},
    {"id": "vieille", "name": "Ancienne", "url": "index.html?region=old/old", "x": 2, "y": 0, "spawn": "", "room": "old", "thumb": "", "presence": ""}]}
REG = S / "regions.json"
REG.write_text(json.dumps(DEPART), encoding="utf-8")

print("--- 1. --dry-run")
r = scan(S, "--dry-run")
rapport(json.loads(REG.read_text(encoding="utf-8")) == DEPART and "rien n'a été écrit" in r.stdout, "--dry-run : fichier inchangé, message clair", r.stdout[-200:])
rapport("+ Maison (4X4)" in r.stdout and "~ Hobbit Land : presence, thumb" in r.stdout and "? Ancienne" in r.stdout, "--dry-run : ajouts, mises à jour et orphelines affichés", r.stdout)

print("--- 2. mise à jour")
r = scan(S)
d = json.loads(REG.read_text(encoding="utf-8"))
f = {x["name"]: x for x in d["regions"]}
rapport(isinstance(d, dict) and d.get("showUrl") is True, "en-tête showUrl gardé")
rapport(set(f) == {"Hobbit Land", "Expo de Marie", "Ancienne", "Maison (4X4)", "expo"}, "une fiche par région trouvée, lib, _bak et fichiers sans salon ignorés", sorted(f))
h = f["Hobbit Land"]
rapport(h["x"] == 1 and h["spawn"] == "porte" and h["thumb"] == "hobbit/hobbit.jpg" and h["presence"] == "ws://ADRESSE:8765", "fiche existante : nom, place, arrivée gardés ; vignette et serveur repris", h)
m = f["Maison (4X4)"]
rapport(m["url"] == "index.html?region=houses/Maison (4X4)" and m["room"] == "Maison4X4" and m["thumb"] == "houses/Maison%20%284X4%29.png", "nouvelle fiche : adresse, salon, vignette .png encodée", m)
rapport(f["expo"]["url"] == "index.html?region=galerie/salle/expo" and f["expo"]["thumb"] == "", "région dans un sous-dossier, sans salon ni image", f["expo"])
rapport(f["Expo de Marie"] == DEPART["regions"][1], "fiche externe (créateur) intacte")
rapport(f["Ancienne"] == DEPART["regions"][2], "orpheline gardée telle quelle")
places = [(x["x"], x["y"]) for x in d["regions"]]
rapport(len(set(places)) == len(places), "chaque fiche a sa case (aucune place en double)", places)
rapport("1 externe(s) gardée(s), 1 orpheline(s)" in r.stdout, "résumé", r.stdout[-200:])

print("--- 3. deuxième passage, liste simple, erreurs, anglais")
r = scan(S)
rapport(json.loads(REG.read_text(encoding="utf-8")) == d and "0 ajoutée(s), 0 mise(s) à jour" in r.stdout, "deuxième passage : rien ne change")
(S / "hobbit" / "hobbit.jpg").unlink()
scan(S)
rapport({x["name"]: x for x in json.loads(REG.read_text(encoding="utf-8"))["regions"]}["Hobbit Land"]["thumb"] == "hobbit/hobbit.jpg", "image retirée du dossier : la vignette déjà notée est gardée")
REG.write_text(json.dumps(DEPART["regions"][:1]), encoding="utf-8")
scan(S)
rapport(isinstance(json.loads(REG.read_text(encoding="utf-8")), list), "un regions.json en liste simple reste une liste")
REG.unlink()
scan(S)
d = json.loads(REG.read_text(encoding="utf-8"))
rapport(isinstance(d, dict) and d.get("showUrl") is False and len(d["regions"]) == 3, "sans regions.json : fichier créé avec l'en-tête showUrl", d if not isinstance(d, dict) else len(d["regions"]))
r = scan(tmp / "absent", ok=False)
rapport(r.returncode != 0 and "dossier introuvable" in r.stderr, "dossier absent : refusé", r.stderr)
(S / "index.html").unlink()
r = scan(S, lang="en")
rapport("no index.html" in r.stderr and "regions.json:" in r.stdout and "ajout" not in r.stdout, "sans index.html : avertissement ; messages en anglais", (r.stderr, r.stdout[-120:]))

print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
