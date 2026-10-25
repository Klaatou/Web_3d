#!/usr/bin/env python3
"""Tests v52 (suite) : region en tuiles renommee (dossiers, fichiers et chemins de l'index), vue d'ensemble toujours reliee aux tuiles.

Le fichier X.overview.glb porte, dans chaque noeud, le chemin de sa tuile tel qu'il etait au decoupage (extras.tile, « X.tiles/T_3_0_0.glb »). Apres un renommage
fait a la main (index reecrit, binaire intact), plus aucun noeud n'etait relie : la vue d'ensemble restait visible sous les tuiles detaillees (moirures).
Verifie : region intacte (toutes les cellules reliees, cellule masquee = tuile affichee) ; region renommee (meme resultat, meme nombre de cellules masquees) ;
un nom de tuile qui n'existe pas dans l'index laisse sa cellule visible (pas de trou).

Prerequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v52_renom.py
"""
import asyncio, json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37
import glbfab

print("--- 0. fabrication : decoupage, puis copie sous un autre nom")
src = tmp / "src"; src.mkdir()
glbfab.region(src / "Syn.glb")
run(DIST / "glb2tiles.py", src / "Syn.glb", "--nopause", "--forcer", "--budget-tri", "900", "--min", "64")
site = tmp / "site"; site.mkdir()
NB = len(json.loads((src / "Syn.tiles.json").read_text(encoding="utf-8"))["tiles"])


def copie(nom, retirer=None):
    shutil.copytree(src / "Syn.tiles", site / f"{nom}.tiles")
    shutil.copy(src / "Syn.overview.glb", site / f"{nom}.overview.glb")
    doc = json.loads((src / "Syn.tiles.json").read_text(encoding="utf-8"))
    if nom != "Syn":   # renommage « a la main » : dossiers, fichiers ET chemins ecrits dans l'index ; le binaire de la vue d'ensemble n'est pas touche
        for t in doc["tiles"]:
            t["file"] = t["file"].replace("Syn.tiles/", f"{nom}.tiles/")
        doc["overview"]["file"] = f"{nom}.overview.glb"
    (site / f"{nom}.tiles.json").write_text(json.dumps(doc), encoding="utf-8")
    html("--tiles", site / f"{nom}.tiles.json", "-o", site / f"{nom}.html", "--shared-shell", "--no-sea", "--target", "0,0,0")


copie("Syn")
copie("Syn-terrain")
copie("Houses-terrain")
http, hp = serveur(site)
BASE = f"http://127.0.0.1:{hp}/"


async def etat(br, nom):
    o = await Onglet(br).ouvrir(BASE + f"index.html?region={nom}", locale="fr-FR")
    await o.attendre("window.__viewer.tilesState().overview.state === 'ready'", 30)
    await asyncio.sleep(3)
    e = (await o.ev("window.__viewer.tilesState()"))["overview"]
    errs = o.errs
    await o.ctx.close()
    return e, errs


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        print("--- 1. region intacte et regions renommees")
        e0, er0 = await etat(br, "Syn")
        rapport(e0["cells"] == NB and 0 < len(e0["hidden"]) < NB and len(e0["hidden"]) + len(e0["visible"]) == NB, f"intacte : {NB} cellules reliees, une cellule masquee par tuile affichee", (e0["cells"], len(e0["hidden"]), len(e0["visible"])))
        for nom in ("Syn-terrain", "Houses-terrain"):
            e1, er1 = await etat(br, nom)
            rapport(e1["cells"] == NB, f"{nom} : les {NB} cellules de la vue d'ensemble sont reliees aux tuiles malgre le renommage", e1["cells"])
            rapport(len(e1["hidden"]) == len(e0["hidden"]) and len(e1["visible"]) == len(e0["visible"]), f"{nom} : meme nombre de cellules masquees que la region intacte (plus de recouvrement)", (len(e1["hidden"]), len(e0["hidden"])))
            rapport(not er1, "aucune erreur de page", er1)
        print("--- 2. une cellule dont la tuile n'existe plus reste visible")
        doc = json.loads((site / "Syn-terrain.tiles.json").read_text(encoding="utf-8"))
        doc["tiles"].pop()
        (site / "Syn-terrain.tiles.json").write_text(json.dumps(doc), encoding="utf-8")
        e2, _ = await etat(br, "Syn-terrain")
        rapport(e2["cells"] == NB - 1 and len(e2["hidden"]) + len(e2["visible"]) == NB, "tuile absente de l'index : une cellule de moins reliee, la cellule orpheline reste visible (aucun trou)", (e2["cells"], len(e2["hidden"]), len(e2["visible"])))
        await br.close()


try:
    asyncio.run(main())
finally:
    http.kill()
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
