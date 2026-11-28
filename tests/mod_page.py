#!/usr/bin/env python3
"""Tests 1.13.24 : moderation depuis la page (vrai presence_server.py, vraie page, deux Chromium).

Verifie :
1.  sans cle memorisee ni #mod : pas de bouton Moderation ; avec #mod dans l'adresse : le bouton apparait ; avec une cle memorisee (localStorage web3d.vkey) aussi ;
2.  le bouton ouvre la fenetre ; mauvaise cle : message, rien ne change ; bonne cle : la liste montre le visiteur ;
3.  Ejecter : le visiteur est ejecte (etat kicked) ; Bannir (minutes + motif) : le visiteur est banni (etat banned) et la fenetre montre le ban ; Debannir : le ban disparait ;
Lancer : python tests/mod_page.py (apres python build.py)
"""
import asyncio, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

SALON, CLE, SEL = "moderation", "ABCD-EFGH-JKMN", "sel-de-test"
V = "window.__viewer."
ETAT = V + "getPresence().state"


def nom(n):
    return "try { localStorage.setItem('glb2html_name', '%s'); } catch (e) {}" % n


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    sol_glb(site / "sol.glb", demi=150.0)
    (tmp / "z.json").write_text(json.dumps([{"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0.0}]), encoding="utf-8")
    cles = tmp / "cles.json"
    cles.write_text(json.dumps({"rooms": {SALON: {"salt": SEL, "hash": hashlib.sha256((SEL + CLE.replace("-", "")).encode()).hexdigest(), "added": 0}}}), encoding="utf-8")
    ps, port_v = lancer_presence("--visits-keys", str(cles), "--bans", str(tmp / "bans.json"))
    html(site / "sol.glb", "-o", site / "Mod.html", "--shared-shell", "--zones", tmp / "z.json", "--no-sea", "--target", "0,0,0", "--presence-url", f"ws://127.0.0.1:{port_v}", "--room", SALON, "--title", "Ile Test")
    srv, port = serveur(site)
    url = lambda h="": f"http://127.0.0.1:{port}/index.html?region=Mod#spawn=default{h}"
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        try:
            ctxa = await br.new_context(viewport={"width": 1000, "height": 700}, locale=LOC)
            ctxb = await br.new_context(viewport={"width": 1000, "height": 700}, locale=LOC)
            ctxc = await br.new_context(viewport={"width": 1000, "height": 700}, locale=LOC)
            a = await Onglet(br).ouvrir(url(), init=STUB + nom("Crea"), ctx=ctxa)
            b = await Onglet(br).ouvrir(url(), init=STUB + nom("Bob"), ctx=ctxb)
            for o in (a, b):
                await o.attendre(V + "walking && " + ETAT + " === 'online'", 40)
            await a.pg.wait_for_timeout(2200)
            rapport(await a.ev("document.getElementById('modBtn').hidden"), "sans cle memorisee ni #mod : pas de bouton Moderation")
            # createur avec #mod
            c = await Onglet(br).ouvrir(url("&mod"), init=STUB + nom("Chef"), ctx=ctxc)
            await c.attendre(V + "walking && " + ETAT + " === 'online'", 40)
            await c.pg.wait_for_timeout(2200)
            rapport(await c.ev("!document.getElementById('modBtn').hidden"), "avec #mod dans l'adresse : le bouton apparait")
            await c.ev("document.getElementById('modBtn').click()")
            rapport(await c.ev("[...document.querySelectorAll('.vcWin')].some(w => !w.hidden && w.textContent.includes('Mod'))"), "le bouton ouvre la fenetre Moderation")
            # mauvaise cle
            await c.ev("(() => { const w = [...document.querySelectorAll('.vcWin')].find(x => !x.hidden); const i = w.querySelector('input[type=password]'); i.value = 'AAAA-AAAA-AAAA'; i.dispatchEvent(new Event('input')); [...w.querySelectorAll('button')].find(b => b.textContent === 'Actualiser').click(); })()")
            await c.pg.wait_for_timeout(900)
            rapport("refus" in (await c.ev("document.body.innerText")).lower(), "mauvaise cle : message de refus")
            await c.pg.wait_for_timeout(500)
            # bonne cle
            await c.ev("(() => { const w = [...document.querySelectorAll('.vcWin')].find(x => !x.hidden); const i = w.querySelector('input[type=password]'); i.value = '%s'; i.dispatchEvent(new Event('input')); [...w.querySelectorAll('button')].find(b => b.textContent === 'Actualiser').click(); })()" % CLE)
            await c.pg.wait_for_timeout(1200)
            W = "[...document.querySelectorAll('.vcWin')].find(x => !x.hidden)"
            rapport("Bob" in await c.ev(W + ".textContent"), "bonne cle : la liste montre le visiteur Bob")
            # bouton memorise : apres une cle bonne, un onglet sans #mod le voit
            rapport(await c.ev("localStorage.getItem('web3d.vkey') === '%s'" % CLE), "la cle est memorisee (comme pour le mode orateur)")
            # ejecter
            await c.ev("(() => { const w = %s; const r = [...w.querySelectorAll('.vcRow')].find(x => x.textContent.includes('Bob')); [...r.querySelectorAll('button')].find(b => b.textContent === 'Éjecter').click(); })()" % W)
            await b.attendre(ETAT + " === 'kicked'", 8)
            rapport(await b.ev(ETAT) == "kicked", "Ejecter : le visiteur est ejecte (etat kicked)")
            # Bob revient, puis ban 30 min avec motif
            b2 = await Onglet(br).ouvrir(url(), init=STUB + nom("Bob"), ctx=ctxb)
            await b2.attendre(V + "walking && " + ETAT + " === 'online'", 40)
            await c.pg.wait_for_timeout(1000)
            await c.ev("(() => { const w = %s; const t = [...w.querySelectorAll('input[type=text]')]; t[0].value = '30'; t[0].dispatchEvent(new Event('input')); t[1].value = 'bruit'; t[1].dispatchEvent(new Event('input')); [...w.querySelectorAll('button')].find(b => b.textContent === 'Actualiser').click(); })()" % W)
            await c.pg.wait_for_timeout(900)
            await c.ev("(() => { const w = %s; const r = [...w.querySelectorAll('.vcRow')].find(x => x.textContent.includes('Bob')); [...r.querySelectorAll('button')].find(b => b.textContent === 'Bannir').click(); })()" % W)
            await b2.attendre(ETAT + " === 'banned'", 8)
            rapport(await b2.ev(ETAT) == "banned", "Bannir : le visiteur est banni (etat banned)")
            await c.pg.wait_for_timeout(800)
            txt = await c.ev(W + ".textContent")
            rapport("Bob" in txt and "bruit" in txt and "Débannir" in txt, "la fenetre montre le bannissement (nom, motif, bouton Debannir)", txt[-200:])
            await c.ev("(() => { const w = %s; [...w.querySelectorAll('button')].find(b => b.textContent === 'Débannir').click(); })()" % W)
            await c.pg.wait_for_timeout(900)
            txt = await c.ev(W + ".textContent")
            rapport("Aucun bannissement" in txt and "Débannir" not in txt, "Debannir : le ban disparait", txt[-200:])
            b3 = await Onglet(br).ouvrir(url(), init=STUB + nom("Bob"), ctx=ctxb)
            await b3.attendre(V + "walking && " + ETAT + " === 'online'", 40)
            rapport(await b3.ev(ETAT) == "online", "apres Debannir, Bob peut revenir")
            # un onglet sans #mod mais avec la cle memorisee voit le bouton (meme contexte que c)
            d = await Onglet(br).ouvrir(url(), init=STUB + nom("Chef2"), ctx=ctxc)
            await d.attendre(V + "walking && " + ETAT + " === 'online'", 40)
            await d.pg.wait_for_timeout(2200)
            rapport(await d.ev("!document.getElementById('modBtn').hidden"), "avec une cle memorisee : le bouton apparait sans #mod")
        finally:
            await br.close()
    ps.terminate(); srv.terminate()


asyncio.run(main())
sys.exit(1 if resultat() else 0)
