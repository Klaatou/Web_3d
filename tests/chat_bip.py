#!/usr/bin/env python3
"""Chat : un bip à chaque message d'un autre visiteur quand la page n'a pas le focus (Chromium sans tête + vrai serveur de présence).

Un faux contexte audio (injecté avant la page) compte les notes jouées ; document.hasFocus() est piloté par le test.
Vérifie : page sans focus -> un bip (988 Hz) ; page avec focus -> aucun ; au plus un bip toutes les 2 s ; ses propres messages -> aucun ;
l'historique rechargé à la connexion -> aucun ; message qui cite mon pseudo -> seulement le bip « cite » (880 Hz) ; case décochée -> aucun.

Prérequis : python build.py ; pip install playwright websockets. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/chat_bip.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_bip_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def sol_glb(path):
    v = [(-20, 0, -20), (20, 0, -20), (20, 0, 20), (-20, 0, 20)]
    pos = b"".join(struct.pack("<3f", *p) for p in v); idx = struct.pack("<6H", 0, 2, 1, 0, 3, 2); blob = pos + idx
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos)}, {"buffer": 0, "byteOffset": len(pos), "byteLength": len(idx)}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-20, 0, -20], "max": [20, 0, 20]}, {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}], "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * (-len(js) % 4); blob += bytes(-len(blob) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def port_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); return s.getsockname()[1]


# faux contexte audio : enregistre les fréquences des notes ; focus piloté par window.__focus
FAUX = """
window.__beeps = []; window.__focus = true;
document.hasFocus = () => window.__focus;
window.AudioContext = window.webkitAudioContext = class {
  constructor() { this.state = 'running'; this.currentTime = 0; this.destination = {}; }
  resume() {}
  createGain() { return { gain: { setValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect() {} }; }
  createOscillator() { return { type: '', frequency: { set value(v) { window.__beeps.push(v); } }, connect() {}, start() {}, stop() {} }; }
};
"""


async def main():
    import websockets.asyncio.client
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    sol_glb(tmp / "sol.glb")
    pport, wport = port_libre(), port_libre()
    if subprocess.run([sys.executable, "-c", "import websockets"], capture_output=True).returncode:
        sys.exit("[ECHEC] la bibliotheque « websockets » n'est pas installee (pip install websockets).")
    pres = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--host", "127.0.0.1", "--port", str(pport),
                             "--identities", str(tmp / "id.json"), "--bans", str(tmp / "bans.json")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(site / "page.html"), "--no-sea", "--presence-url", f"ws://127.0.0.1:{pport}", "--room", "t", "--chat", *vend], capture_output=True, text=True)
    if r.returncode:
        pres.kill(); sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    for _ in range(60):
        try:
            socket.create_connection(("127.0.0.1", pport), timeout=0.3).close(); break
        except OSError:
            time.sleep(0.2)
    web = subprocess.Popen([sys.executable, "-m", "http.server", str(wport), "--bind", "127.0.0.1"], cwd=site, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    ouverts = []
    try:
        bob = await websockets.asyncio.client.connect(f"ws://127.0.0.1:{pport}"); ouverts.append(bob)
        await bob.send(json.dumps({"t": "hello", "room": "t", "uid": os.urandom(12).hex(), "spectator": False, "name": "Bob"})); await bob.recv()

        async def dire(texte):
            await bob.send(json.dumps({"t": "chat", "text": texte})); await asyncio.sleep(0.6)

        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)

            async def ouvrir(focus=True):
                ctx = await br.new_context(locale="fr-FR", viewport={"width": 1100, "height": 650})
                await ctx.add_init_script(FAUX + f"window.__focus = {'true' if focus else 'false'};")
                pg = await ctx.new_page(); errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                await pg.goto(f"http://127.0.0.1:{wport}/page.html#name=Zoe")
                await pg.wait_for_function("document.getElementById('msg') === null", timeout=90000); await pg.wait_for_timeout(2000)
                await pg.keyboard.press("f"); await pg.wait_for_timeout(1500)      # première action de l'utilisateur : le son est autorisé
                await pg.wait_for_function("document.getElementById('chatHelp') && document.getElementById('chatHelp').textContent.length > 0", timeout=20000)
                await pg.wait_for_timeout(1500)
                return ctx, pg, errs

            beeps = lambda pg: pg.evaluate("window.__beeps.slice()")
            ctx, pg, errs = await ouvrir(focus=True)
            await dire("bonjour (page avec focus)")
            rapport(await beeps(pg) == [], "page avec focus : aucun bip", await beeps(pg))
            await pg.evaluate("window.__focus = false")
            await dire("salut (page sans focus)")
            rapport(await beeps(pg) == [988], "page sans focus : un bip (une note, 988 Hz)", await beeps(pg))
            await asyncio.sleep(2.2)
            await bob.send(json.dumps({"t": "chat", "text": "un"})); await asyncio.sleep(0.2)
            await bob.send(json.dumps({"t": "chat", "text": "deux"})); await asyncio.sleep(0.2)
            await bob.send(json.dumps({"t": "chat", "text": "trois"})); await asyncio.sleep(0.8)
            rapport(await beeps(pg) == [988, 988], "trois messages en moins de 2 s : un seul bip de plus", await beeps(pg))
            await asyncio.sleep(2.2)
            await dire("Zoe, tu m'entends ?")
            b = await beeps(pg)
            rapport(b == [988, 988, 880], "message qui cite mon pseudo : seulement le bip « cite » (880 Hz), pas deux bips", b)
            # mes propres messages : aucun bip
            n = len(await beeps(pg))
            await pg.keyboard.press("Enter"); await pg.wait_for_timeout(400)
            await pg.keyboard.type("mon message"); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(1000)
            rapport(len(await beeps(pg)) == n, "mon propre message : aucun bip", await beeps(pg))
            await pg.keyboard.press("Escape")
            # case décochée : aucun bip (le réglage est dans le panneau des réglages)
            await pg.evaluate("document.getElementById('visSoundCite') && (document.getElementById('visSoundCite').checked = false, document.getElementById('visSoundCite').dispatchEvent(new Event('change')))")
            await asyncio.sleep(2.2)
            await pg.evaluate("(() => { const c = document.getElementById('visSoundMsg'); c.checked = false; c.dispatchEvent(new Event('change')); })()")
            n = len(await beeps(pg))
            await dire("encore un message")
            rapport(len(await beeps(pg)) == n, "case « Bip à chaque message… » décochée : aucun bip", await beeps(pg))
            rapport(not errs, "aucune erreur JavaScript", errs)
            await ctx.close()

            # historique rechargé à la connexion : aucun bip (page ouverte sans focus, le salon a déjà des messages)
            ctx, pg, errs = await ouvrir(focus=False)
            b = await beeps(pg)
            rapport(b == [], "historique rechargé à la connexion : aucun bip", b)
            await ctx.close()
            await br.close()
    finally:
        for c in ouverts:
            try:
                await c.close()
            except Exception:
                pass
        pres.kill(); web.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
