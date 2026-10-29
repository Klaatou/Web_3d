#!/usr/bin/env python3
"""Tests : les essais de connexion a la presence s'arretent (jusqu'au rechargement de la page) au lieu de continuer sans fin.

Verifie : serveur absent -> 5 essais en tout (le premier compris), puis le message « essais arretes » (francais et anglais), plus aucun essai ensuite ;
connexion ouverte puis perdue (serveur arrete) -> la page continue d'essayer au-dela de 5 fois (jusqu'a 12) et n'a pas abandonne.

Prerequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/essais_presence.py (une minute)
"""
import asyncio, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

COMPTE = STUB + """
(() => { window.__ws = []; const W = window.WebSocket;
  window.WebSocket = function (u, p) { window.__ws.push(String(u)); return p === undefined ? new W(u) : new W(u, p); };
  window.WebSocket.prototype = W.prototype; for (const k of ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED']) window.WebSocket[k] = W[k]; })();"""

print("--- 0. fabrication des pages")
site = tmp / "site"; site.mkdir()
sol_glb(site / "sol.glb")
mort = port_libre()          # personne n'ecoute
vivant = port_libre()        # un vrai serveur, arrete ensuite
html(site / "sol.glb", "-o", site / "Mort.html", "--shared-shell", "--no-sea", "--target", "0,0,0", "--presence-url", f"ws://127.0.0.1:{mort}", "--room", "e52")
html(site / "sol.glb", "-o", site / "Vivant.html", "--shared-shell", "--no-sea", "--target", "0,0,0", "--presence-url", f"ws://127.0.0.1:{vivant}", "--room", "e52v")
http, hport = serveur(site)
BASE = f"http://127.0.0.1:{hport}/"
srv = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--lang", "fr", "--host", "127.0.0.1", "--port", str(vivant), "--identities", ""],
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
attendre_port(vivant, srv, "presence_server")


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        fr = await Onglet(br).ouvrir(BASE + "index.html?region=Mort#name=Zoe", init=COMPTE, locale="fr-FR")
        en = await Onglet(br).ouvrir(BASE + "index.html?region=Mort#name=Zoe", init=COMPTE, locale="en-US")
        vi = await Onglet(br).ouvrir(BASE + "index.html?region=Vivant#name=Zoe", init=COMPTE, locale="fr-FR")
        print("--- 1. serveur absent : les essais s'arretent")
        await fr.attendre("document.getElementById('presenceStatus').textContent.includes('essais arrêtés')", 60)
        await en.attendre("document.getElementById('presenceStatus').textContent.includes('attempts stopped')", 60)
        n_fr = await fr.ev("window.__ws.length")
        rapport(n_fr == 5, f"francais : 5 essais en tout, puis arret (comptes : {n_fr})")
        s = await fr.txt("presenceStatus")
        rapport("connexion jamais établie" in s and "recharge la page" in s and "nouvelle tentative" not in s, "francais : le message dit la cause et demande de recharger, sans « nouvelle tentative »", s)
        s = await en.txt("presenceStatus")
        rapport("connection never established" in s and "reload the page" in s and "retrying" not in s, "anglais : message equivalent", s)
        pr = await fr.ev("window.__viewer.getPresence()")
        rapport(pr.get("stopped") is True, "getPresence : stopped vrai", pr.get("stopped"))
        await asyncio.sleep(12)
        n2 = await fr.ev("window.__ws.length")
        rapport(n2 == n_fr and "essais arrêtés" in await fr.txt("presenceStatus"), f"douze secondes plus tard : plus aucun essai (comptes : {n2})")

        print("--- 2. connexion ouverte puis perdue : la page continue d'essayer")
        await vi.attendre("document.getElementById('presenceStatus').textContent.length > 0 && window.__viewer.getPresence().id !== null", 20)
        rapport(await vi.ev("window.__viewer.getPresence().state") == "online", "la page est connectee au vrai serveur", await vi.txt("presenceStatus"))
        avant = await vi.ev("window.__ws.length")
        srv.terminate(); srv.wait(5)
        await asyncio.sleep(36)
        apres = await vi.ev("window.__ws.length")
        s = await vi.txt("presenceStatus")
        rapport(apres - avant >= 6 and "essais arrêtés" not in s, f"36 s apres l'arret du serveur : {apres - avant} nouveaux essais (plus de 5, pas d'abandon)", s)
        await br.close()


try:
    asyncio.run(main())
finally:
    try:
        srv.terminate()
    except Exception:
        pass
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
