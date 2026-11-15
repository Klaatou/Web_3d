#!/usr/bin/env python3
"""Carte des mondes : le nombre de colonnes de vignettes suit la largeur de la page (disposition automatique, regions sans position distincte).

Verifie dans Chromium, avec 14 regions : page etroite (800 px) 4 colonnes au plus ; page large (1900 px) au moins 9 colonnes (avant : 5 au plus,
la zone utile de la page etait plafonnee a 1000 px) ; le nombre de colonnes augmente avec la largeur.

Prerequis : python build.py ; pip install playwright. Variable facultative : CHROMIUM. Lancer : python tests/carte_largeur.py
"""
import asyncio, json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *

site = tmp / "site"; site.mkdir()
REGS = [{"name": f"Region{i}", "url": f"r{i}.html", "x": 0, "y": 0, "spawn": "", "room": "", "thumb": "", "presence": ""} for i in range(14)]
(site / "regions.json").write_text(json.dumps({"showUrl": False, "regions": REGS}), encoding="utf-8")
shutil.copy(DIST / "carte.html", site / "carte.html")
http, hport = serveur(site)
COLS = "() => new Set([...document.querySelectorAll('.tile')].map(t => Math.round(t.getBoundingClientRect().left))).size"


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        res = {}
        for larg in (800, 1300, 1900):
            pg = await (await br.new_context(viewport={"width": larg, "height": 900}, locale=LOC)).new_page()
            await pg.goto(f"http://127.0.0.1:{hport}/carte.html")
            await pg.wait_for_function("document.querySelectorAll('.tile').length === 14", timeout=15000)
            res[larg] = await pg.evaluate(COLS)
        await br.close()
    print("colonnes par largeur :", res)
    rapport(res[800] <= 4, "800 px : 4 colonnes au plus", res)
    rapport(res[1900] >= 9, "1900 px : 9 colonnes au moins (avant : 5 au plus)", res)
    rapport(res[800] < res[1300] < res[1900], "le nombre de colonnes augmente avec la largeur", res)

try:
    asyncio.run(main())
finally:
    http.kill()
sys.exit(1 if resultat() else 0)
