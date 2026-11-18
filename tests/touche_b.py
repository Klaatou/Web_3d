#!/usr/bin/env python3
"""Test 1.12.20 : touche B, Entree et Echap quand la saisie du chat est restee ouverte SANS le focus.
Cause : apres un envoi avec Entree la saisie reste ouverte ; un clic sur la scene retire le focus au champ sans la fermer, et les trois touches n'agissaient plus.
- B replie / deplie ; apres un choix de flux de radio, apres des clics sur la scene, apres la marche, apres une attente ;
- message envoye, clic sur la scene : B ferme la saisie et replie le bloc ; Entree rend le focus ; Echap ferme la saisie ;
- dans le champ (focus), B s'ecrit toujours dans le texte.
Prerequis : pip install playwright websockets ; python build.py avant. Variables : THREE_DIR, CHROMIUM.
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
    import wave
    site = tmp / "site"; site.mkdir()
    sol_glb(site / "sol.glb")
    with wave.open(str(site / "a.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000); w.writeframes(b"\0\0" * 8000 * 30)
    srv, port = serveur(site)
    S = f"http://127.0.0.1:{port}/a.wav"
    (tmp / "z.json").write_text(json.dumps([{"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0.0},
        {"id": "radio", "type": "cast", "label": "Radio", "x": 0, "y": 15, "z": 0, "radius": 30, "streams": [["Un", S], ["Deux", S + "?2"], ["Trois", S + "?3"]]}]), encoding="utf-8")
    ph, porth = lancer_presence("--chat-burst", "100000", "--chat-gap", "0", "--idle-walk", "0")
    uh = f"ws://127.0.0.1:{porth}"
    html(site / "sol.glb", "-o", site / "Rep.html", "--shared-shell", "--zones", tmp / "z.json", "--no-sea", "--target", "0,0,0", "--presence-url", uh, "--room", "rep", "--title", "Ile Test", "--chat", *vend)
    base_url = f"http://127.0.0.1:{port}/index.html?region=Rep#spawn=default"
    DANA = "try { localStorage.setItem('glb2html_name', 'Dana'); } catch (e) {}"
    cache = "document.getElementById('chat').hidden"
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--autoplay-policy=no-user-gesture-required"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        try:
            o = await Onglet(br).ouvrir(base_url, init=STUB + DANA)
            await o.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await o.pg.wait_for_timeout(1500)
            async def essai(nom):
                a = await o.ev(cache)
                await o.pg.keyboard.press("b"); await o.pg.wait_for_timeout(250)
                b = await o.ev(cache)
                etat = await o.ev("[document.activeElement && document.activeElement.tagName, window.__viewer.walking, document.getElementById('chatInput').hidden]")
                rapport(a != b, "B bascule : " + nom, (a, b, etat))
                await o.pg.keyboard.press("b"); await o.pg.wait_for_timeout(250)
            await essai("depart")
            for sid in ("radioSel",):
                if await o.ev(f"!!document.getElementById('{sid}') && !document.getElementById('{sid}').hidden"):
                    await o.pg.select_option("#" + sid, index=1); await o.pg.wait_for_timeout(500)
                    await o.pg.mouse.click(500, 350); await o.pg.wait_for_timeout(300)
                    await essai("apres choix de flux " + sid + " et clic sur la scene")
            for i in range(6):
                await o.pg.mouse.click(300 + 40 * i, 300); await o.pg.wait_for_timeout(200)
            await essai("apres clics sur la scene")
            for i in range(4):
                await o.pg.keyboard.down("ArrowUp"); await o.pg.wait_for_timeout(400); await o.pg.keyboard.up("ArrowUp")
            await essai("apres marche")
            await o.pg.wait_for_timeout(5000)
            await essai("apres 5 s d'attente")
            ouverte = "!document.getElementById('chatInput').hidden"
            print("--- saisie restee ouverte sans focus (cas du constat)")
            async def envoyer_et_cliquer():
                await o.pg.keyboard.press("Enter"); await o.pg.wait_for_timeout(300)
                await o.pg.keyboard.type("salut"); await o.pg.keyboard.press("Enter"); await o.pg.wait_for_timeout(400)
                await o.pg.mouse.click(500, 350); await o.pg.wait_for_timeout(300)
            await envoyer_et_cliquer()
            rapport(await o.ev(ouverte) and await o.ev("document.activeElement.tagName") == "BODY", "etat : saisie ouverte, focus sur la page")
            await o.pg.keyboard.press("b"); await o.pg.wait_for_timeout(300)
            rapport(not await o.ev(ouverte) and await o.ev(cache), "B : ferme la saisie et replie le bloc", (await o.ev(ouverte), await o.ev(cache)))
            await o.pg.keyboard.press("b"); await o.pg.wait_for_timeout(300)
            rapport(not await o.ev(cache), "B encore : bloc deplie")
            await envoyer_et_cliquer()
            await o.pg.keyboard.press("Enter"); await o.pg.wait_for_timeout(300)
            rapport(await o.ev("document.activeElement.id") == "chatInput", "Entree : rend le focus a la saisie", await o.ev("document.activeElement.tagName"))
            await o.pg.keyboard.type("b"); await o.pg.wait_for_timeout(200)
            rapport(await o.ev("document.getElementById('chatInput').value") == "b" and not await o.ev(cache), "B tape dans la saisie : s'ecrit, ne replie pas")
            await o.pg.keyboard.press("Escape"); await o.pg.wait_for_timeout(300)
            rapport(not await o.ev(ouverte), "Echap dans la saisie : fermee")
            await envoyer_et_cliquer()
            await o.pg.keyboard.press("Escape"); await o.pg.wait_for_timeout(300)
            rapport(not await o.ev(ouverte) and not await o.ev(cache), "Echap (sans focus) : saisie fermee, bloc deplie")
            await essai("apres tout cela")
        finally:
            await br.close(); ph.terminate()
    return h37.bad

sys.exit(1 if asyncio.run(main()) else 0)
