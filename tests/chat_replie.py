#!/usr/bin/env python3
"""Tests 1.11.1 : bloc de chat replié (touche B) et fenêtre Aide (touches en gras, titres en majuscules). Vrai presence_server.py, vraie page.

1. le chat est déplié par défaut ; B le replie (#chat caché, mémorisé) puis le déplie ;
2. un message d'un autre visiteur le déplie ; une arrivée ; un départ ; l'historique rejoué à l'arrivée, non (page rechargée repliée : reste repliée) ;
3. Entrée le déplie et ouvre la saisie ; Échap ferme la saisie et laisse le chat déplié ; B tapé dans la saisie s'écrit dans le texte (ne replie pas) ;
4. Aide (page en français) : la ligne « B : replier / déplier le bloc de chat », les touches (avant le premier « : ») dans des éléments en gras, titres de groupe en majuscules, texte inchangé.
Non testé ici : écran tactile (« Fermer » replie), Windows. Lancer : python tests/chat_replie.py (après python build.py)
"""
import asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37


async def client(url, nom, room="rep"):
    import websockets.asyncio.client
    ws = await websockets.asyncio.client.connect(url)
    await ws.send(json.dumps({"t": "hello", "room": room, "name": nom, "uid": (nom * 8)[:24].encode().hex()[:24], "spectator": False}))
    json.loads(await asyncio.wait_for(ws.recv(), 5))
    return ws


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    sol_glb(site / "sol.glb")
    (tmp / "z.json").write_text(json.dumps([{"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0.0}]), encoding="utf-8")
    ph, porth = lancer_presence("--chat-burst", "100000", "--chat-gap", "0")
    uh = f"ws://127.0.0.1:{porth}"
    html(site / "sol.glb", "-o", site / "Rep.html", "--shared-shell", "--zones", tmp / "z.json", "--no-sea", "--target", "0,0,0", "--presence-url", uh, "--room", "rep", "--title", "Ile Test", "--chat", *vend)
    seed = await client(uh, "Seed")
    await seed.send(json.dumps({"t": "chat", "text": "ancien message"})); await asyncio.sleep(0.3)
    srv, port = serveur(site)
    base_url = f"http://127.0.0.1:{port}/index.html?region=Rep#spawn=default"
    DANA = "try { localStorage.setItem('glb2html_name', 'Dana'); } catch (e) {}"
    visible = "!document.getElementById('chat').hidden"
    cache = "document.getElementById('chat').hidden"
    stock = "localStorage.getItem('web3d.chat.fold')"
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        try:
            o = await Onglet(br).ouvrir(base_url, init=STUB + DANA)
            await o.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await o.pg.wait_for_timeout(1200)
            rapport(await o.ev(visible), "chat déplié par défaut")
            await o.pg.keyboard.press("b")
            rapport(await o.ev(cache) and await o.ev(stock) == "1", "B : chat replié et mémorisé", (await o.ev(cache), await o.ev(stock)))
            await o.pg.keyboard.press("b")
            rapport(await o.ev(visible) and await o.ev(stock) == "0", "B encore : chat déplié")
            print("--- un message, une arrivée, un départ déplient")
            await o.pg.keyboard.press("b")
            await seed.send(json.dumps({"t": "chat", "text": "bonjour Dana"})); await o.pg.wait_for_timeout(700)
            rapport(await o.ev(visible) and await o.ev(stock) == "0", "message d'un autre visiteur : chat déplié")
            await o.pg.keyboard.press("b")
            tom = await client(uh, "Tom"); await o.pg.wait_for_timeout(700)
            rapport(await o.ev(visible), "arrivée d'un visiteur : chat déplié")
            await o.pg.keyboard.press("b")
            await tom.close(); await o.pg.wait_for_timeout(900)
            rapport(await o.ev(visible), "départ d'un visiteur : chat déplié")
            print("--- Entrée, Échap, B dans la saisie")
            await o.pg.keyboard.press("b")
            rapport(await o.ev(cache), "replié avant Entrée")
            await o.pg.keyboard.press("Enter")
            await o.attendre("!document.getElementById('chatInput').hidden", 10)
            rapport(await o.ev(visible) and await o.ev(stock) == "0", "Entrée : chat déplié, saisie ouverte")
            await o.pg.wait_for_timeout(300)
            await o.pg.keyboard.type("b")
            rapport(await o.ev("document.getElementById('chatInput').value") == "b" and await o.ev(visible), "B tapé dans la saisie : s'écrit, ne replie pas", await o.ev("[document.getElementById('chatInput').value, document.activeElement && document.activeElement.id, document.hasFocus()]"))
            await o.pg.keyboard.press("Escape")
            await o.attendre("document.getElementById('chatInput').hidden", 10)
            rapport(await o.ev(visible), "Échap : saisie fermée, chat toujours déplié")
            await o.pg.keyboard.press("b")
            rapport(await o.ev(cache), "B : replié")
            print("--- l'historique rejoué ne déplie pas")
            await o.pg.reload(); await o.attendre("document.getElementById('msg') === null && window.__viewer && window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await o.pg.wait_for_timeout(1500)
            rapport(await o.ev(cache) and await o.ev(stock) == "1", "page rechargée repliée : l'historique (« ancien message ») ne la déplie pas", (await o.ev(cache), await o.ev(stock)))
            print("--- fenêtre Aide")
            await o.ev("document.getElementById('walkHint').hidden = false; document.getElementById('helpBody').hidden = false")
            info = await o.ev("""() => { const b = document.getElementById('helpBody'), ks = [...b.querySelectorAll('.grp .hk')], ts = [...b.querySelectorAll('.grp b.gt')];
                return { txt: b.textContent, nk: ks.length, kfw: ks.length ? getComputedStyle(ks[0]).fontWeight : '', tt: ts.length ? getComputedStyle(ts[0]).textTransform : '', nt: ts.length,
                         keys: ks.map(k => k.textContent) }; }""")
            rapport("B : replier / déplier le bloc de chat" in info["txt"], "ligne « B : replier / déplier le bloc de chat » dans le groupe Chat", info["txt"][:300])
            rapport(info["nk"] >= 10 and int(info["kfw"]) >= 600, f"touches et gestes en gras ({info['nk']} éléments, graisse {info['kfw']})", info["keys"])
            rapport(info["nt"] >= 5 and info["tt"] == "uppercase", f"titres de groupe en majuscules ({info['nt']} titres)", info["tt"])
            rapport("H : aide" in info["txt"] and "flèches : marcher" in info["txt"], "texte inchangé (« H : aide », « flèches : marcher »)")
        finally:
            srv.terminate()
            await br.close()
    await seed.close(); ph.terminate()
    print("\nRÉSULTAT : " + ("tout est passé" if not h37.bad else f"{h37.bad} échec(s)"))
    sys.exit(1 if h37.bad else 0)

asyncio.run(main())
