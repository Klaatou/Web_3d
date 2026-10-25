#!/usr/bin/env python3
"""Tests v50 : boutons « Importer / Exporter regions.json » et « Ajouter / mettre à jour cette région » du viewer.

Vérifie : import de la forme objet (v47) avec en-tête, export identique (en-tête, champs presence et inconnus gardés),
en-tête retenu après rechargement du viewer, « Ajouter » qui met à jour la fiche du même salon sur place sans effacer
presence ni la vignette, import d'une liste simple exportée en liste, fichier refusé avec un message clair (FR et EN).

Prérequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v50.py
"""
import asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

sol_glb(tmp / "sol.glb")
A = {"id": "hobbit", "name": "Hobbit Land", "url": "index.html?region=hobbit/hobbit", "x": 1, "y": 0, "spawn": "porte", "room": "Hobbit",
     "thumb": "hobbit/hobbit.jpg", "presence": "ws://ADRESSE:8765", "note": "champ inconnu gardé"}
B = {"id": "sol", "name": "Ancien nom", "url": "index.html?region=sol", "x": 3, "y": 2, "spawn": "", "room": "sol",
     "thumb": "sol.jpg", "presence": "wss://ADRESSE"}
OBJ = {"showUrl": True, "titre": "en-tête inconnu gardé", "regions": [A, B]}
(tmp / "obj.json").write_text(json.dumps(OBJ), encoding="utf-8")
(tmp / "liste.json").write_text(json.dumps([A]), encoding="utf-8")
(tmp / "mauvais.json").write_text(json.dumps({"a": 1}), encoding="utf-8")
URL = (DIST / "glb-viewer.html").as_uri()


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        ctx = await br.new_context(locale=LOC, accept_downloads=True)
        errs = []

        async def ouvrir():
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(URL)
            await pg.wait_for_function("window.__viewer", timeout=40000)
            return pg

        async def bouton(pg, texte):
            await pg.evaluate("(t) => [...document.querySelectorAll('#mapUi button')].find(b => b.textContent === t).click()", texte)

        async def exporter(pg):
            async with pg.expect_download() as dl:
                await bouton(pg, "Exporter regions.json")
            d = await dl.value
            return json.loads(open(await d.path(), encoding="utf-8").read())

        stat = lambda pg: pg.evaluate("document.getElementById('stat').textContent")

        print("--- 1. forme objet")
        pg = await ouvrir()
        await pg.set_input_files("#fMap", str(tmp / "obj.json"))
        await pg.wait_for_timeout(300)
        rapport(await stat(pg) == "Carte importée : 2 région(s)", "import de la forme objet accepté", await stat(pg))
        d = await exporter(pg)
        rapport(d == OBJ, "export : même en-tête (showUrl, champ inconnu), mêmes fiches (presence, champ inconnu)", d)

        print("--- 2. rechargement du viewer")
        await pg.wait_for_timeout(1700)   # la carte est mémorisée toutes les 1,5 s
        await pg.close()
        pg = await ouvrir()
        d = await exporter(pg)
        rapport(d == OBJ, "après rechargement : en-tête et fiches retrouvés", d)

        print("--- 3. Ajouter / mettre à jour cette région")
        await pg.set_input_files("#fGlb", str(tmp / "sol.glb"))
        await pg.wait_for_function("!document.getElementById('bZip').disabled", timeout=20000)
        await pg.wait_for_timeout(500)
        await pg.evaluate("""() => { const i = document.querySelectorAll('#mapUi input');
            i[0].value = 'Nouveau nom'; i[0].dispatchEvent(new Event('change')); i[1].value = 'index.html?region=sol'; i[1].dispatchEvent(new Event('change')); }""")
        await bouton(pg, "Ajouter / mettre à jour cette région dans la carte")
        d = await exporter(pg)
        r = d.get("regions", [{}, {}])
        rapport(len(r) == 2 and r[0] == A, "fiche d'un autre salon intacte, ordre gardé", r)
        b = r[1] if len(r) == 2 else {}
        rapport(b.get("name") == "Nouveau nom" and b.get("presence") == "wss://ADRESSE" and b.get("thumb") == "sol.jpg" and b.get("room") == "sol",
                "même salon : mise à jour sur place, presence et vignette gardées", b)
        rapport(d.get("showUrl") is True, "en-tête gardé après « Ajouter »")

        print("--- 4. liste simple, fichier refusé, anglais")
        await pg.set_input_files("#fMap", str(tmp / "liste.json"))
        await pg.wait_for_timeout(300)
        d = await exporter(pg)
        rapport(d == [A], "liste simple : exportée en liste", d)
        await pg.set_input_files("#fMap", str(tmp / "mauvais.json"))
        await pg.wait_for_timeout(300)
        s = await stat(pg)
        rapport("liste de régions, ou objet" in s, "fichier sans régions : message clair", s)
        await pg.close()
        ctx2 = await br.new_context(locale="en-US")
        pe = await ctx2.new_page()
        pe.on("pageerror", lambda e: errs.append(str(e)))
        await pe.goto(URL + "#lang=en")
        await pe.wait_for_function("window.__viewer", timeout=40000)
        await pe.set_input_files("#fMap", str(tmp / "mauvais.json"))
        await pe.wait_for_timeout(300)
        s = await stat(pe)
        rapport("list of regions, or object" in s, "message en anglais", s)
        rapport(not errs, "aucune erreur JavaScript", errs)
        await br.close()


asyncio.run(main())
n = h37.resultat()
print("\n" + ("TOUS LES TESTS v50 PASSENT" if not n else f"{n} ÉCHEC(S)"))
sys.exit(1 if n else 0)
