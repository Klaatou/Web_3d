#!/usr/bin/env python3
"""Tests v45 : la page dit pourquoi la connexion de présence s'est fermée.

Vérifie : serveur absent (« jamais établie », ouverte : non, code 1006), serveur qui ferme avec un code et une raison (code 4001 et raison affichés,
ouverte : oui), constructeur WebSocket refusé (SecurityError), anglais, viewer, adresse masquée dans le diagnostic.

Prérequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v45.py
"""
import asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

print("--- 0. fabrication des pages")
site = tmp / "site"; site.mkdir()
sol_glb(site / "sol.glb")
mort = port_libre()          # port sur lequel personne n'écoute
ferme = port_libre()         # port d'un faux serveur qui ferme avec un code
html(site / "sol.glb", "-o", site / "Mort.html", "--shared-shell", "--no-sea", "--target", "0,0,0", "--presence-url", f"ws://127.0.0.1:{mort}", "--room", "t45")
html(site / "sol.glb", "-o", site / "Ferme.html", "--shared-shell", "--no-sea", "--target", "0,0,0", "--presence-url", f"ws://127.0.0.1:{ferme}", "--room", "t45")
http, hport = serveur(site)
BASE = f"http://127.0.0.1:{hport}/"


async def diag(o):
    await o.ev("document.getElementById('diagBtn').click()")
    await o.attendre("document.getElementById('diagOut').value.length > 0", 10)
    return await o.ev("document.getElementById('diagOut').value")


async def diag_avec(o, morceau, s=15):
    """relit le diagnostic jusqu'à ce qu'il contienne le morceau (la page se reconnecte toute seule : l'état change)"""
    t = ""
    for _ in range(int(s / 0.3)):
        t = await diag(o)
        if morceau in t:
            return t
        await o.pg.wait_for_timeout(300)
    return t


async def main():
    import websockets.asyncio.server
    recus = []

    async def faux(ws):
        try:
            recus.append(json.loads(await asyncio.wait_for(ws.recv(), 5)))
        except Exception:
            pass
        await ws.close(4001, "ejecte pour le test")

    srv = await websockets.asyncio.server.serve(faux, "127.0.0.1", ferme)
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)

        print("--- 1. serveur absent (français)")
        o = await Onglet(br).ouvrir(BASE + "index.html?region=Mort#name=Zoe")
        await o.attendre("document.getElementById('presenceStatus').textContent.includes('jamais établie')", 20)
        s = await o.txt("presenceStatus")
        rapport("présence interrompue" in s and "connexion jamais établie" in s and "nouvelle tentative" in s, "texte : jamais établie, pas « injoignable »", s)
        t = await diag_avec(o, "dernier code : 1006")
        rapport("Connexion de présence : s'est ouverte : non, dernier code : 1006, raison : \u2014" in t, "diagnostic : jamais ouverte, code 1006, pas de raison", t[-700:])
        rapport("Présence : ws · " in t and "127.0.0.1" not in t, "diagnostic : adresse masquée, ligne Présence inchangée")
        pr = await o.ev("window.__viewer.getPresence()")
        rapport(pr.get("opened") is False and pr.get("closeCode") == 1006, "getPresence : opened false, closeCode 1006", pr)
        await o.ctx.close()

        print("--- 2. serveur qui ferme avec un code et une raison")
        o = await Onglet(br).ouvrir(BASE + "index.html?region=Ferme#name=Zoe")
        await o.attendre("document.getElementById('presenceStatus').textContent.includes('4001')", 20)
        s = await o.txt("presenceStatus")
        rapport("connexion ouverte puis fermée (code 4001) : ejecte pour le test" in s, "texte : code et raison du serveur", s)
        t = await diag_avec(o, "dernier code : 4001")
        rapport("s'est ouverte : oui, dernier code : 4001, raison : ejecte pour le test" in t, "diagnostic : ouverte oui, code 4001, raison", t[-700:])
        rapport(len(recus) >= 1 and recus[0].get("t") == "hello", "le faux serveur a bien reçu le hello (la connexion s'était ouverte)", recus[:1])
        await o.ctx.close()

        print("--- 3. constructeur refusé (SecurityError)")
        refus = h37.STUB + "\nwindow.WebSocket = function () { throw new DOMException('refus', 'SecurityError'); };"
        o = await Onglet(br).ouvrir(BASE + "index.html?region=Mort#name=Zoe", init=refus)
        await o.attendre("document.getElementById('presenceStatus').textContent.includes('refusé par le navigateur')", 20)
        s = await o.txt("presenceStatus")
        rapport("page https avec ws://" in s, "texte : refusé par le navigateur", s)
        await o.ctx.close()

        print("--- 4. anglais")
        o = await Onglet(br).ouvrir(BASE + "index.html?region=Mort#lang=en", locale="en-US")
        await o.attendre("document.getElementById('presenceStatus').textContent.includes('never established')", 20)
        s = await o.txt("presenceStatus")
        rapport(s.startswith("presence interrupted (") and "retrying" in s, "texte anglais", s)
        t = await diag_avec(o, "last code: 1006")
        rapport("Presence connection: was opened: no, last code: 1006, reason: \u2014" in t, "diagnostic anglais", t[-500:])
        await o.ctx.close()

        print("--- 5. viewer")
        o = await Onglet(br).ouvrir((DIST / "glb-viewer.html").as_uri(), init=None, viewer=False)
        await o.attendre("!!document.getElementById('presInfo')", 20)
        await o.ev(f"""(() => {{ const i = [...document.querySelectorAll('input[type=text]')].find(x => x.placeholder === 'ws://127.0.0.1:8765'); i.value = 'ws://127.0.0.1:{mort}'; i.onchange(); }})()""")
        await o.attendre("document.getElementById('presInfo').textContent.includes('jamais établie')", 20)
        s = await o.txt("presInfo")
        rapport(s.startswith("présence : connexion jamais établie") and "nouvelle tentative" in s, "viewer : raison affichée", s)
        await o.ctx.close()
        await br.close()
    srv.close()


try:
    asyncio.run(main())
finally:
    http.kill()
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
