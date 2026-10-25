#!/usr/bin/env python3
"""Tests v40 : fenêtre « Arrivées » (touche L, téléportation au clic), bouton « Recentrer la vue », lien « Manuel complet »,
bulle du bouton « Copier le diagnostic » (page et viewer), aide mise à jour.

Prérequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v40.py
"""
import asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

print("--- 0. fabrication des pages")
site = tmp / "site40"; site.mkdir()
sol_glb(site / "sol.glb")
zones = [{"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0},
         {"id": "zeta", "type": "spawn", "x": 8, "y": 15, "z": 8, "yaw": 0},
         {"id": "alpha", "type": "spawn", "label": "Alpha", "x": -8, "y": 15, "z": -8, "yaw": 0}]
(tmp / "z40.json").write_text(json.dumps(zones), encoding="utf-8")
html(site / "sol.glb", "-o", site / "Arr.html", "--shared-shell", "--no-sea", "--zones", tmp / "z40.json")
html(site / "sol.glb", "-o", site / "Nue.html", "--shared-shell", "--no-sea")
http, hport = serveur(site)
BASE = f"http://127.0.0.1:{hport}/index.html"
TIP = "Liste des points de téléportation disponibles (TP)"


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)

        print("--- 1. fenêtre Arrivées")
        o = await Onglet(br).ouvrir(BASE + "?region=Arr")
        await o.attendre("document.querySelectorAll('#spawnBody button').length === 3", 15)
        noms = await o.ev("[...document.querySelectorAll('#spawnBody button')].map(b => b.textContent)")
        rapport(noms == ["default", "Alpha", "zeta"], "liste : « default » d'abord, puis par nom (étiquette si elle existe)", noms)
        st = await o.ev("(() => { const s = document.getElementById('spawnInfo'); return { vis: !s.hidden && !!s.offsetWidth, tip: s.title, head: document.getElementById('spawnHead').textContent }; })()")
        rapport(st["vis"] and st["tip"] == TIP and st["head"] == "▾ Arrivées", "fenêtre visible, titre et bulle", st)
        haut = await o.ev("[document.getElementById('walkHint').getBoundingClientRect().top, document.getElementById('bar').getBoundingClientRect().bottom, innerHeight]")
        rapport(haut[0] >= 0 and haut[1] <= haut[2], "aide, état, arrivées et barre tiennent dans une fenêtre de 700 px de haut", haut)
        aide = await o.txt("helpBody")
        rapport("L : arrivées (téléportation)" in aide and "R : centrer sur l'arrivée" in aide and "Recentrer la vue" in aide, "aide en vue globale : L, R, bouton Recentrer", aide)
        await o.touche("KeyL")
        h1 = await o.ev("document.getElementById('spawnInfo').hidden")
        await o.touche("KeyL")
        h2 = await o.ev("document.getElementById('spawnInfo').hidden")
        await o.ev("document.getElementById('spawnHead').click()")
        f1 = await o.ev("document.getElementById('spawnBody').hidden")
        await o.touche("KeyL")
        f2 = await o.ev("[document.getElementById('spawnInfo').hidden, document.getElementById('spawnBody').hidden]")
        rapport(h1 is True and h2 is False and f1 is True and f2 == [False, False], "L : déployée -> masquée -> déployée ; réduite -> déployée", (h1, h2, f1, f2))
        await o.ev("[...document.querySelectorAll('#spawnBody button')].find(b => b.textContent === 'Alpha').click()")
        await o.attendre("window.__viewer.walking", 10)
        w = await o.gw()
        rapport(dist_h(w["pos"], [-8, 15, -8]) < 0.5, "vue globale : clic sur « Alpha » -> promenade à cette arrivée", w["pos"])
        rapport(await o.ev("document.getElementById('centerBtn').hidden") is True, "bouton « Recentrer la vue » caché en promenade")
        aide = await o.txt("helpBody")
        rapport("L : arrivées (téléportation)" in aide, "aide en promenade : L")
        await o.ev("[...document.querySelectorAll('#spawnBody button')].find(b => b.textContent === 'zeta').click()")
        await o.pg.wait_for_timeout(300)
        w = await o.gw()
        rapport(dist_h(w["pos"], [8, 15, 8]) < 0.5 and await o.ev("window.__viewer.walking"), "promenade : clic sur « zeta » -> téléportation", w["pos"])
        rapport(await o.ev("document.activeElement === document.body || !document.activeElement || document.activeElement.tagName !== 'BUTTON'"), "les noms ne gardent pas le focus")
        print("--- 2. Recentrer la vue")
        await o.touche("KeyF")
        await o.attendre("!window.__viewer.walking", 10)
        # v46 : flèches à l'écran affichées (par défaut) : le centre du pavé recentre et le bouton est caché ; flèches cachées (K) : le bouton revient
        rapport(await o.ev("document.getElementById('centerBtn').hidden && !document.getElementById('padCenter').hidden"), "flèches affichées : le centre du pavé remplace le bouton")
        await o.touche("KeyK")
        rapport(await o.ev("!document.getElementById('centerBtn').hidden && document.getElementById('centerBtn').title === \"Revenir au cadrage d'ouverture de la région (vue globale)\""), "flèches cachées : bouton visible hors promenade, avec sa bulle")
        await o.touche("KeyK")
        await o.ev("window.__viewer.frame([1, 0.2, 0], [30, 15, 30], 0.3)")
        await o.ev("document.getElementById('centerBtn').click()")
        apres = await o.ev("window.__viewer.getCameraState()")
        rapport(apres["zoom"] > 0.5 and dist_h(apres["target"], [30, 15, 30]) > 5, "le bouton quitte la vue déplacée", apres)
        print("--- 3. diagnostic et manuel")
        d = await o.ev("[document.getElementById('diagBtn').title, document.getElementById('manualLink').href, document.getElementById('manualLink').target]")
        rapport(d[0].startswith("Copie l'état technique") and d[1] == "https://github.com/Klaatou/Web_3d/blob/main/docs/fr/MANUEL.md" and d[2] == "_blank", "bulle du diagnostic, lien vers le manuel français", d)
        rapport(not o.errs, "aucune erreur JavaScript", o.errs)
        await o.ctx.close()

        print("--- 4. cadrage d'ouverture exact")
        o = await Onglet(br).ouvrir(BASE + "?region=Arr")
        await o.attendre("document.querySelectorAll('#spawnBody button').length === 3", 15)
        ref = await o.ev("window.__viewer.getCameraState()")
        await o.ev("window.__viewer.frame([1, 0.2, 0], [30, 15, 30], 0.3)")
        await o.ev("document.getElementById('centerBtn').click()")
        apres = await o.ev("window.__viewer.getCameraState()")
        ecart = max(abs(a - b) for a, b in zip(ref["target"] + ref["camDir"] + [ref["zoom"]], apres["target"] + apres["camDir"] + [apres["zoom"]]))
        rapport(ecart < 1e-3, "« Recentrer la vue » rend exactement le cadrage d'ouverture", (ref, apres))
        await o.ctx.close()

        print("--- 5. région sans arrivée, anglais")
        o = await Onglet(br).ouvrir(BASE + "?region=Nue#lang=en", locale="en-US")
        await o.pg.wait_for_timeout(800)
        await o.touche("KeyL")
        await o.pg.wait_for_timeout(100)
        r = await o.ev("[document.getElementById('spawnInfo').hidden, document.getElementById('toast').textContent, document.getElementById('helpBody').textContent, document.getElementById('manualLink').href, document.getElementById('centerBtn').textContent]")
        rapport(r[0] is True and r[1] == "No arrival point in this region", "sans arrivée : fenêtre absente, L le dit", r[:2])
        rapport("L: arrivals" not in r[2] and r[3].endswith("/docs/en/MANUAL.md") and r[4] == "Recenter the view", "anglais : pas de L dans l'aide, manuel anglais, bouton traduit", r[2:])
        rapport(not o.errs, "aucune erreur JavaScript", o.errs)
        await o.ctx.close()

        print("--- 6. viewer")
        o = await Onglet(br).ouvrir((DIST / "glb-viewer.html").as_uri(), init=None, viewer=False)
        await o.attendre("!!document.getElementById('bDiag')", 15)
        await o.pg.wait_for_timeout(300)
        v = await o.ev("[document.getElementById('bDiag').title, document.getElementById('manualLink').href, document.getElementById('manualLink').textContent]")
        rapport(v[0].startswith("Copie l'état technique") and v[1].endswith("/docs/fr/MANUEL.md") and v[2] == "Manuel complet (en ligne)", "viewer : bulle du diagnostic et lien vers le manuel", v)
        await o.ctx.close()
        await br.close()


try:
    asyncio.run(main())
finally:
    http.kill()
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
