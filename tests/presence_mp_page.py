#!/usr/bin/env python3
"""Tests 1.12.30 : messages prives, cote page (vrai presence_server.py, vraie page, Chromium).

1. un MP recu ouvre une fenetre reduite, qui clignote, sans prendre le focus ; l'agrandir lit le texte ; repondre arrive chez l'autre et s'affiche (echo) ;
2. fermer la fenetre ne supprime pas le texte (il est la a la reouverture, y compris les messages recus fenetre fermee) ;
3. clic sur un pseudo du chat = MP ; commande /mp pseudo message ; une fenetre par correspondant ;
4. Ignorer : fenetre cachee, chat public, bulle et MP de cette cle masques ; memorise (rechargement) ; /unignore rend tout ; le texte deja echange reste ;
5. Enregistrer : fichier texte UTF-8 avec BOM contenant la conversation ;
6. serveur --no-dm : aucune fonction (/mp refuse, aucune fenetre) ; aucune erreur de page.
Non teste ici : Windows, Edge, ecran tactile. Lancer : python tests/presence_mp_page.py (apres python build.py)
"""
import asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37


async def client(url, nom, room="mpp"):
    import websockets.asyncio.client
    ws = await websockets.asyncio.client.connect(url)
    await ws.send(json.dumps({"t": "hello", "room": room, "name": nom, "uid": (nom * 8)[:24].encode().hex()[:24], "spectator": False}))
    w = json.loads(await asyncio.wait_for(ws.recv(), 5))
    return ws, w


async def recevoir(ws, t="dm", delai=3.0):
    fin = asyncio.get_event_loop().time() + delai
    while True:
        reste = fin - asyncio.get_event_loop().time()
        if reste <= 0:
            return None
        try:
            m = json.loads(await asyncio.wait_for(ws.recv(), reste))
        except asyncio.TimeoutError:
            return None
        if m.get("t") == t and not m.get("self"):   # l'écho de ses propres envois (self) est ignoré
            return m


FEN = "[...document.querySelectorAll('.mpWin')]"
INFO = """() => [...document.querySelectorAll('.mpWin')].map(w => ({ titre: w.querySelector('.mpTitle').textContent, cache: w.hidden, min: w.classList.contains('min'), blink: w.classList.contains('blink'),
  lignes: [...w.querySelectorAll('.mpLog > div')].map(d => d.textContent), focus: w.contains(document.activeElement) }))"""
LOGTXT = "document.getElementById('chatLog').textContent"
TOAST = "document.getElementById('toast').textContent"


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    sol_glb(site / "sol.glb")
    (tmp / "z.json").write_text(json.dumps([{"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0.0}]), encoding="utf-8")
    ph, porth = lancer_presence("--chat-burst", "100000", "--chat-gap", "0")
    pn, portn = lancer_presence("--no-dm")
    uh, un = f"ws://127.0.0.1:{porth}", f"ws://127.0.0.1:{portn}"
    for nom, u, room in (("Mpp", uh, "mpp"), ("Nodm", un, "nodm")):
        html(site / "sol.glb", "-o", site / (nom + ".html"), "--shared-shell", "--zones", tmp / "z.json", "--no-sea", "--target", "0,0,0", "--presence-url", u, "--room", room, "--title", "Ile Test", "--chat")
    srv, port = serveur(site)
    url = lambda n: f"http://127.0.0.1:{port}/index.html?region={n}#spawn=default"
    DANA = "try { localStorage.setItem('glb2html_name', 'Dana'); if (!sessionStorage.getItem('mpinit')) { localStorage.removeItem('web3d.ignore'); sessionStorage.setItem('mpinit', '1'); } } catch (e) {}"
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        try:
            o = await Onglet(br).ouvrir(url("Mpp"), init=STUB + DANA)
            await o.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await o.pg.wait_for_timeout(800)
            dana = await o.ev("window.__viewer.getPresence().id")
            tom, wt = await client(uh, "Tom")
            seed, ws_ = await client(uh, "Seed")
            await o.pg.wait_for_timeout(800)
            rapport(await o.ev("document.body.classList.contains('dmOn')"), "serveur avec MP : pseudos cliquables (dmOn)")
            rapport(await o.ev(FEN + ".length") == 0, "aucune fenetre MP au depart")
            rapport(await o.ev("window.__viewer.getPresence().peers.every(p => /^[0-9a-f]{12}$/.test(p.k))"), "la page connait la cle k de chaque visiteur")

            print("--- reception : fenetre reduite, clignotante, sans focus")
            await tom.send(json.dumps({"t": "dm", "to": dana, "text": "salut Dana"})); await o.pg.wait_for_timeout(600)
            f = await o.ev(INFO)
            rapport(len(f) == 1 and not f[0]["cache"] and f[0]["min"] and f[0]["blink"] and not f[0]["focus"], "MP recu : fenetre ouverte reduite, clignote, sans focus", f)
            rapport(f and "Tom" in f[0]["titre"] and "(1)" in f[0]["titre"], "titre : nom et nombre de non lus", f and f[0]["titre"])
            await o.ev("document.querySelector('.mpWin .mpHead button').click()")
            f = await o.ev(INFO)
            rapport(f[0]["lignes"] == ["Tom : salut Dana"] and not f[0]["min"] and not f[0]["blink"], "agrandie : texte lu, clignotement arrete", f)
            print("--- reponse")
            await o.ev("document.querySelector('.mpWin .mpIn').focus()")
            await o.pg.keyboard.type("bien recu"); await o.pg.keyboard.press("Enter")
            m = await recevoir(tom)
            rapport(m is not None and m["text"] == "bien recu" and m["name"] == "Dana", "la reponse arrive chez Tom", m)
            await o.pg.wait_for_timeout(300)
            f = await o.ev(INFO)
            rapport(f[0]["lignes"] == ["Tom : salut Dana", "Dana : bien recu"], "echo de ma reponse dans la fenetre", f[0]["lignes"])
            rapport(await o.ev("document.querySelector('.mpWin .mpIn').value") == "", "saisie videe apres l'envoi")
            print("--- fermer ne supprime pas le texte")
            await o.ev("document.querySelectorAll('.mpWin .mpHead button')[1].click()")
            f = await o.ev(INFO)
            rapport(f[0]["cache"] and len(f[0]["lignes"]) == 2, "fermee : cachee, texte toujours dans la page", f)
            await tom.send(json.dumps({"t": "dm", "to": dana, "text": "encore"})); await o.pg.wait_for_timeout(600)
            f = await o.ev(INFO)
            rapport(not f[0]["cache"] and f[0]["min"] and f[0]["lignes"] == ["Tom : salut Dana", "Dana : bien recu", "Tom : encore"], "nouveau MP : meme fenetre rouverte, les trois lignes", f)
            await o.ev("document.querySelector('.mpWin .mpHead button').click()")

            print("--- clic sur l'avatar (avec confirmation)")
            gw = await o.gw(); base = gw["pos"]; trouve = None
            for dx, dz in ((0, -4), (0, 4), (4, 0), (-4, 0)):
                await tom.send(json.dumps({"t": "pos", "p": [base[0] + dx, base[1], base[2] + dz], "yaw": 0})); await o.pg.wait_for_timeout(500)
                s = await o.ev("(() => { const q = window.__viewer.getPresence().peers.find(p => p.name === 'Tom'); return q && q.visible ? q.screen : null; })()")
                if s and s["front"] and 0 < s["sx"] < 1000 and 0 < s["sy"] < 700:
                    trouve = s; break
            rapport(trouve is not None, "Tom est visible a l'ecran (test du clic)", trouve)
            if trouve:
                await o.ev("document.querySelectorAll('.mpWin').forEach(w => { w.hidden = true; })")
                await o.pg.mouse.click(trouve["sx"], trouve["sy"]); await o.pg.wait_for_timeout(700)
                rapport(await o.ev("!!document.getElementById('mpAsk') && document.getElementById('mpAsk').textContent.includes('Tom')"), "clic sur l'avatar : question de confirmation avec le nom", await o.ev("document.getElementById('mpAsk') && document.getElementById('mpAsk').textContent"))
                rapport(await o.ev(FEN + ".every(w => w.hidden)"), "aucune fenetre tant qu'on n'a pas confirme")
                await o.ev("document.querySelectorAll('#mpAsk button')[1].click()")
                rapport(await o.ev("!document.getElementById('mpAsk')") and await o.ev(FEN + ".every(w => w.hidden)"), "Non : la question disparait, rien ne s'ouvre")
                await o.pg.mouse.click(trouve["sx"], trouve["sy"]); await o.pg.wait_for_timeout(700)
                await o.ev("document.querySelectorAll('#mpAsk button')[0].click()")
                f = await o.ev(INFO)
                rapport(any("Tom" in w["titre"] and not w["cache"] and not w["min"] for w in f), "Oui : la fenetre de Tom s'ouvre", f)
                await o.ev("document.querySelectorAll('.mpWin').forEach(w => { w.hidden = true; })")

            print("--- clic sur un pseudo, commande /mp")
            await seed.send(json.dumps({"t": "chat", "text": "hello tous"})); await o.pg.wait_for_timeout(600)
            await o.ev("[...document.querySelectorAll('#chatLog b[data-pid]')].find(b => b.textContent.startsWith('Seed')).click()")
            f = await o.ev(INFO)
            rapport(len(f) == 2 and any("Seed" in w["titre"] and not w["min"] and not w["cache"] for w in f), "clic sur le pseudo Seed : sa fenetre s'ouvre (une fenetre par correspondant)", f)
            await o.ev("document.activeElement && document.activeElement.blur()")
            await o.pg.keyboard.press("Enter")
            await o.attendre("!document.getElementById('chatInput').hidden", 10)
            await o.pg.keyboard.type("/mp Seed coucou toi"); await o.pg.keyboard.press("Enter")
            m = await recevoir(seed)
            rapport(m is not None and m["text"] == "coucou toi" and m["name"] == "Dana", "/mp Seed coucou toi : arrive chez Seed", m)
            await o.pg.keyboard.type("/mp Inconnu salut"); await o.pg.keyboard.press("Enter"); await o.pg.wait_for_timeout(300)
            rapport("Inconnu" in await o.ev(TOAST), "pseudo inconnu : message d'erreur", await o.ev(TOAST))
            await o.pg.keyboard.press("Escape")

            print("--- enregistrer")
            async with o.pg.expect_download() as dl:
                await o.ev("[...document.querySelectorAll('.mpWin')].find(w => w.querySelector('.mpTitle').textContent.includes('Tom')).querySelector('.mpB').click()")
            d = await dl.value
            data = open(await d.path(), "rb").read()
            txt = data.decode("utf-8")
            rapport(data[:3] == b"\xef\xbb\xbf" and d.suggested_filename.startswith("mp_Tom_") and all(s in txt for s in ("| Tom | salut Dana", "| Dana | bien recu", "| Tom | encore")), "fichier .txt UTF-8 avec BOM et les 3 lignes", (d.suggested_filename, txt[:300]))

            print("--- ignorer")
            await o.ev("[...document.querySelectorAll('.mpWin')].find(w => w.querySelector('.mpTitle').textContent.includes('Tom')).querySelectorAll('.mpB')[1].click()")
            rapport(await o.ev("JSON.parse(localStorage.getItem('web3d.ignore')).length") == 1, "Tom est dans la liste des ignores (navigateur)")
            f = await o.ev(INFO); ft = [w for w in f if "Tom" in w["titre"]][0]
            rapport(ft["cache"] and len(ft["lignes"]) == 3, "sa fenetre est cachee, le texte deja echange reste", ft)
            await tom.send(json.dumps({"t": "chat", "text": "bruit public"})); await tom.send(json.dumps({"t": "dm", "to": dana, "text": "bruit prive"})); await o.pg.wait_for_timeout(700)
            f = await o.ev(INFO); ft = [w for w in f if "Tom" in w["titre"]][0]
            rapport(ft["cache"] and len(ft["lignes"]) == 3, "MP d'un ignore : rien ne s'affiche", ft)
            rapport("bruit public" not in await o.ev(LOGTXT), "chat public d'un ignore : masque")
            rapport(await o.ev("window.__viewer.getPresence().peers.find(p => p.name === 'Tom').bubble") is False, "bulle d'un ignore : aucune")
            await seed.send(json.dumps({"t": "chat", "text": "visible"})); await o.pg.wait_for_timeout(500)
            rapport("visible" in await o.ev(LOGTXT), "un autre visiteur reste affiche")
            await o.pg.reload(); await o.attendre("document.getElementById('msg') === null && window.__viewer && window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await o.pg.wait_for_timeout(1200)
            await tom.send(json.dumps({"t": "chat", "text": "bruit apres rechargement"})); await o.pg.wait_for_timeout(600)
            rapport("apres rechargement" not in await o.ev(LOGTXT), "ignore memorise apres rechargement")
            await o.pg.keyboard.press("Enter")
            await o.attendre("!document.getElementById('chatInput').hidden", 10)
            await o.pg.keyboard.type("/unignore Tom"); await o.pg.keyboard.press("Enter"); await o.pg.wait_for_timeout(300)
            rapport(await o.ev("JSON.parse(localStorage.getItem('web3d.ignore')).length") == 0, "/unignore Tom : liste videe")
            await tom.send(json.dumps({"t": "chat", "text": "de retour"})); await o.pg.wait_for_timeout(600)
            rapport("de retour" in await o.ev(LOGTXT), "Tom de nouveau affiche")
            rapport(not o.errs, "aucune erreur de page", o.errs[:3])

            print("--- serveur --no-dm")
            o2 = await Onglet(br).ouvrir(url("Nodm"), init=STUB + "try { localStorage.setItem('glb2html_name', 'Eve'); } catch (e) {}")
            await o2.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            zoe, _ = await client(un, "Zoe", "nodm"); await o2.pg.wait_for_timeout(800)
            await zoe.send(json.dumps({"t": "chat", "text": "salut"})); await o2.pg.wait_for_timeout(600)
            rapport(not await o2.ev("document.body.classList.contains('dmOn')") and await o2.ev("window.__viewer.dmOK") is False, "--no-dm : fonction absente (dmOn faux)")
            await o2.pg.keyboard.press("Enter")
            await o2.attendre("!document.getElementById('chatInput').hidden", 10)
            await o2.pg.keyboard.type("/mp Zoe test"); await o2.pg.keyboard.press("Enter"); await o2.pg.wait_for_timeout(400)
            rapport(await o2.ev(FEN + ".length") == 0 and "indisponibles" in await o2.ev(TOAST), "--no-dm : /mp refuse, aucune fenetre", await o2.ev(TOAST))
            rapport(not o2.errs, "aucune erreur de page (--no-dm)", o2.errs[:3])
            await zoe.close()
        finally:
            srv.terminate()
            await br.close()
    ph.terminate(); pn.terminate()
    print("\nRÉSULTAT : " + ("tout est passé" if not h37.bad else f"{h37.bad} échec(s)"))
    sys.exit(1 if h37.bad else 0)

asyncio.run(main())
