#!/usr/bin/env python3
"""Tests v41 : bulles des fenêtres H, I, L, O ; fenêtres déplaçables (pile de gauche, pile de droite sous Réglages, libre),
double-clic de retour, mémoire du navigateur, fichier de disposition (enregistrer, charger, refus), disposition d'origine.

Prérequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v41.py
"""
import asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

print("--- 0. fabrication de la page")
site = tmp / "site41"; site.mkdir()
sol_glb(site / "sol.glb")
zones = [{"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0}, {"id": "b", "type": "spawn", "x": 5, "y": 15, "z": 5, "yaw": 0}]
(tmp / "z41.json").write_text(json.dumps(zones), encoding="utf-8")
html(site / "sol.glb", "-o", site / "Arr.html", "--shared-shell", "--no-sea", "--zones", tmp / "z41.json")
http, hport = serveur(site)
URL = f"http://127.0.0.1:{hport}/index.html?region=Arr"

PARENT = "(id) => { const e = document.getElementById(id), p = e.parentElement; return p === document.body ? 'body' : p.id; }"
RECT = "(id) => { const r = document.getElementById(id).getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }"


async def glisser(o, head, x, y):
    r = await o.ev(RECT, head)
    await o.pg.mouse.move(r[0] + 30, r[1] + r[3] / 2)
    await o.pg.mouse.down()
    await o.pg.mouse.move(r[0] + 40, r[1] + r[3] / 2 + 10, steps=3)
    await o.pg.mouse.move(x, y, steps=8)
    await o.pg.mouse.up()
    await o.pg.wait_for_timeout(100)


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        ctx = await br.new_context(locale=LOC, viewport={"width": 1000, "height": 700}, accept_downloads=True)
        o = await Onglet(br).ouvrir(URL, ctx=ctx)
        await o.attendre("document.querySelectorAll('#spawnBody button').length === 2", 15)

        print("--- 1. bulles")
        t = await o.ev("['helpHead', 'stateHead', 'spawnHead', 'optsBtn'].map(i => document.getElementById(i).title)")
        rapport(t[0].startswith("Aide : ") and "H : afficher, déployer, masquer." in t[0] and "Glisser le titre : déplacer" in t[0], "bulle de H : rôle, touche, déplacement", t[0])
        rapport("I : afficher" in t[1] and "Informations" in t[1], "bulle de I", t[1])
        rapport("points de téléportation disponibles (TP)" in t[2] and "L : afficher" in t[2], "bulle de L", t[2])
        rapport(t[3].startswith("Réglages") and "O : ouvrir, fermer." in t[3], "bulle de O", t[3])

        print("--- 2. glisser l'aide au milieu : libre")
        await glisser(o, "helpHead", 500, 250)
        par = await o.ev(PARENT, "walkHint")
        lay = json.loads(await o.ev("localStorage.getItem('glb2html_layout')"))
        rapport(par == "body" and lay["wins"]["H"]["pile"] == "F", "l'aide est libre, retenue par le navigateur", (par, lay["wins"]["H"]))
        rapport(await o.ev("!document.getElementById('helpBody').hidden"), "le glisser ne replie pas la fenêtre")
        r = await o.ev(RECT, "helpHead")
        await o.pg.mouse.click(r[0] + 30, r[1] + r[3] / 2)
        f0 = await o.ev("document.getElementById('helpBody').hidden")
        await o.pg.wait_for_timeout(350)
        f1 = await o.ev("document.getElementById('helpBody').hidden")
        await o.ev("document.getElementById('helpHead').click()")
        rapport(f0 is False and f1 is True and await o.ev("!document.getElementById('helpBody').hidden"), "un clic à la souris replie (après 250 ms), un clic au clavier déplie aussitôt", (f0, f1))
        posH = await o.ev(RECT, "walkHint")

        print("--- 3. glisser les arrivées sous Réglages : pile de droite")
        await glisser(o, "spawnHead", 940, 60)
        rapport(await o.ev(PARENT, "spawnInfo") == "hudR", "les arrivées s'accrochent à la pile de droite", await o.ev(PARENT, "spawnInfo"))
        y0 = (await o.ev(RECT, "spawnInfo"))[1]
        await o.ev("document.getElementById('optsBtn').click()")
        await o.pg.wait_for_timeout(100)
        y1 = (await o.ev(RECT, "spawnInfo"))[1]
        await o.ev("document.getElementById('optsBtn').click()")
        await o.pg.wait_for_timeout(100)
        y2 = (await o.ev(RECT, "spawnInfo"))[1]
        rapport(y1 > y0 + 50 and abs(y2 - y0) < 1, "Réglages ouvert pousse la pile de droite, fermé la remonte", (y0, y1, y2))
        rapport(await o.ev("!document.getElementById('spawnInfo').hidden && getComputedStyle(document.getElementById('spawnInfo')).textAlign") == "left", "texte de la fenêtre aligné à gauche dans la pile de droite")

        print("--- 4. rechargement : disposition retrouvée")
        await o.pg.reload()
        await o.attendre("document.getElementById('msg') === null && window.__viewer && document.querySelectorAll('#spawnBody button').length === 2", 30)
        r2 = await o.ev(RECT, "walkHint")
        rapport(await o.ev(PARENT, "walkHint") == "body" and abs(r2[0] - posH[0]) < 2 and abs(r2[1] - posH[1]) < 2, "aide libre au même endroit", (posH, r2))
        rapport(await o.ev(PARENT, "spawnInfo") == "hudR", "arrivées toujours dans la pile de droite")

        print("--- 5. double-clic : retour à la dernière pile")
        r = await o.ev(RECT, "helpHead")
        await o.pg.mouse.dblclick(r[0] + 30, r[1] + r[3] / 2)
        await o.pg.wait_for_timeout(100)
        ordre = await o.ev("[...document.getElementById('hudL').children].map(e => e.id)")
        rapport(ordre[:2] == ["walkHint", "stateInfo"] and await o.ev("!document.getElementById('helpBody').hidden"), "l'aide revient en tête de la pile de gauche, dépliée", ordre)
        r = await o.ev(RECT, "spawnHead")
        await glisser(o, "spawnHead", 560, 420)
        rapport(await o.ev(PARENT, "spawnInfo") == "body", "arrivées sorties de la pile de droite : libres")
        r = await o.ev(RECT, "spawnHead")
        await o.pg.mouse.dblclick(r[0] + 30, r[1] + r[3] / 2)
        await o.pg.wait_for_timeout(100)
        rapport(await o.ev(PARENT, "spawnInfo") == "hudR" and await o.ev("!document.getElementById('spawnBody').hidden"), "double-clic : retour à la pile de droite (la dernière), sans replier")

        print("--- 6. enregistrer, origine, charger")
        async with o.pg.expect_download() as dl:
            await o.ev("document.getElementById('laySave').click()")
        d = await dl.value
        chemin = tmp / "disposition.json"
        await d.save_as(str(chemin))
        js = json.loads(chemin.read_text(encoding="utf-8"))
        rapport(d.suggested_filename == "disposition.json" and js.get("app") == "web3d-layout" and js["layout"]["wins"]["L"]["pile"] == "R", "fichier disposition.json enregistré", js)
        await o.ev("document.getElementById('layReset').click()")
        ordre = await o.ev("[...document.getElementById('hudL').children].map(e => e.id)")
        rapport(ordre == ["walkHint", "stateInfo", "spawnInfo"] and await o.txt("toast") == "Disposition d'origine rétablie", "disposition d'origine : tout dans la pile de gauche", ordre)
        await o.pg.set_input_files("#layFile", str(chemin))
        await o.pg.wait_for_timeout(300)
        rapport(await o.ev(PARENT, "spawnInfo") == "hudR" and await o.txt("toast") == "Disposition chargée", "charger le fichier : arrivées de nouveau à droite")
        mauvais = tmp / "faux.json"; mauvais.write_text('{"a": 1}', encoding="utf-8")
        await o.pg.set_input_files("#layFile", str(mauvais))
        await o.pg.wait_for_timeout(300)
        rapport(await o.txt("toast") == "Ce fichier n'est pas une disposition de fenêtres" and await o.ev(PARENT, "spawnInfo") == "hudR", "fichier étranger refusé, rien ne change")

        print("--- 7. fenêtre libre gardée dans l'écran")
        await glisser(o, "stateHead", 900, 640)
        await o.pg.set_viewport_size({"width": 600, "height": 450})
        await o.pg.wait_for_timeout(200)
        r = await o.ev(RECT, "stateInfo")
        rapport(await o.ev(PARENT, "stateInfo") == "body" and r[0] >= 0 and r[0] + min(r[2], 600) <= 600.5 and r[1] <= 450 - 30, "après rétrécissement, la fenêtre libre reste atteignable", r)
        rapport(not o.errs, "aucune erreur JavaScript", o.errs)
        await ctx.close()
        await br.close()


try:
    asyncio.run(main())
finally:
    http.kill()
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
