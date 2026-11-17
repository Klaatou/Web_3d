#!/usr/bin/env python3
"""Test 1.11.17 et 1.11.18 : les lignes « Radio » et « Musique » de la fenetre Etat donnent la distance a la source et la portee de la zone (« 10 m / 40 m »),
mise a jour quand les metres entiers changent, sans autre changement d'etat ; pas de distance en erreur ; 1.11.18 : la ligne reste hors de portee jusqu'a 2 fois la portee (distance qui clignote), puis disparait.
Prerequis : pip install playwright websockets && playwright install chromium ; python build.py avant. Variables : THREE_DIR, CHROMIUM.
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, functools, http.server, json, math, os, pathlib, struct, subprocess, sys, tempfile, threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_cast_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def sol_glb(path):
    pos = struct.pack("<12f", -60, 0, -60, 60, 0, -60, 60, 0, 60, -60, 0, 60)
    blob = pos + struct.pack("<6H", 0, 2, 1, 0, 3, 2) + b"\0\0"
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-60, 0, -60], "max": [60, 0, 60]},
                       {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * ((4 - len(js) % 4) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob))
                     + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def wav(path, secondes=40):
    n = 8000 * secondes
    data = bytes(int(128 + 100 * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(n))
    path.write_bytes(b"RIFF" + struct.pack("<I", 36 + n) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 8000, 8000, 1, 8) + b"data" + struct.pack("<I", n) + data)


DEMANDES = []   # chemins demandes au serveur (compte des reessais)


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        DEMANDES.append(self.path)
        super().do_GET()


def serveur(dossier):
    h = functools.partial(Handler, directory=str(dossier))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def page(port):
    Z = lambda i, t, x, z, **k: dict({"id": i, "type": t, "label": "Zone " + i, "x": x, "y": 15, "z": z}, **k)
    zones = [Z("salle", "cast", 0, 0, radius=40, target=f"http://127.0.0.1:{port}/flux.wav"),
             Z("casse", "cast", -50, 0, radius=5, target=f"http://127.0.0.1:{port}/absent.mp3"),
             Z("zik", "audio", 50, 0, radius=8, folder="audio", tracks=["1-a.wav"])]
    (tmp / "audio").mkdir(); wav(tmp / "audio" / "1-a.wav", 40)
    (tmp / "z.json").write_text(json.dumps(zones), encoding="utf-8")
    out = tmp / "p.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--zones", str(tmp / "z.json"), "--no-sea", *vend],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    t = out.read_text(encoding="utf-8")
    for a, b in (("const viewer = createViewer(", "const viewer = window.__v = createViewer("), ("const RADIO = (() => {", "const RADIO = window.__r = (() => {"), ("const MUSIC = (() => {", "const MUSIC = window.__m = (() => {")):
        if a not in t:
            sys.exit(f"[ECHEC] marqueur absent de la page : {a}")
        t = t.replace(a, b, 1)
    out.write_text(t, encoding="utf-8")
    return out


async def main():
    from playwright.async_api import async_playwright
    sol_glb(tmp / "sol.glb"); wav(tmp / "flux.wav")
    srv = serveur(tmp)
    out = page(srv.server_address[1])
    async with async_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
        br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
        pg = await br.new_page(locale="fr-FR"); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(out.as_uri())
        await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
        await pg.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
        rinfo = lambda: pg.evaluate("(() => { const e = document.getElementById('radioInfo'); return e.hidden ? '' : e.textContent; })()")
        minfo = lambda: pg.evaluate("(() => { const e = document.getElementById('musicInfo'); return e.hidden ? '' : e.textContent; })()")
        async def jouer(fn):
            try:
                await pg.wait_for_function(fn, timeout=15000)
            except Exception:
                pass
        await pg.evaluate("window.__v.walkStart({ pos: [0, 15, 60], yaw: 0 })"); await pg.wait_for_timeout(400)
        await pg.evaluate("window.__v.teleportTo([0, 15, 10], 0)"); await pg.wait_for_timeout(400)
        await pg.keyboard.press("ControlLeft"); await jouer("window.__r.playing()")
        t = await rinfo()
        rapport(await pg.evaluate("window.__r.playing()") and "(10 m / 40 m)" in t, "radio : la ligne donne la distance et la portee", t)
        bulle = lambda ident: pg.evaluate("document.getElementById('" + ident + "').title")
        b = await bulle('radioInfo')
        rapport("Zone radio : Zone salle" in b and "Distance : 10 m (portée 40 m), à portée" in b and "Case : couper" in b and "Liste" not in b, "radio : info-bulle de la ligne (zone, distance, portee, commandes ; pas de liste avec un seul flux)", b)
        await pg.evaluate("window.__v.teleportTo([0, 15, 25], 0)"); await pg.wait_for_timeout(400)
        t = await rinfo()
        rapport(await pg.evaluate("window.__r.playing()") and "(25 m / 40 m)" in t, "radio : la distance suit la marche, sans changement d'etat", t)
        n = []
        for z in (26, 27.4, 29):
            await pg.evaluate(f"window.__v.teleportTo([0, 15, {z}], 0)"); await pg.wait_for_timeout(250)
            n.append(await rinfo())
        rapport("(26 m" in n[0] and "(27 m" in n[1] and "(29 m" in n[2], "radio : mise a jour a chaque metre entier", n)
        await pg.evaluate("window.__v.teleportTo([0, 15, 45], 0)"); await pg.wait_for_timeout(400)
        t = await rinfo()
        far = await pg.evaluate("(() => { const s = document.querySelector('#radioInfo .srcFar'); return s ? [s.textContent, getComputedStyle(s).animationName, getComputedStyle(s).fontWeight] : null; })()")
        rapport("hors de port" in t and "(45 m / 40 m)" in t and not await pg.evaluate("window.__r.playing()"), "hors de portee : la ligne reste, dit « hors de portee » avec la distance, le flux est arrete", t)
        b = await bulle('radioInfo')
        rapport("Distance : 45 m (portée 40 m), hors de portée" in b, "hors de portee : l'info-bulle suit la distance et dit « hors de portee »", b)
        rapport(bool(far) and "45 m" in far[0] and far[1] != "none" and int(far[2]) >= 600, "hors de portee : la distance est dans un span qui clignote (animation) et en gras", far)
        await pg.evaluate("window.__v.teleportTo([0, 15, 30], 0)"); await jouer("window.__r.playing()")
        t = await rinfo()
        rapport(await pg.evaluate("window.__r.playing()") and "(30 m / 40 m)" in t and "hors de port" not in t and await pg.evaluate("!document.querySelector('#radioInfo .srcFar')"), "retour dans la portee : le flux reprend, plus de clignotement", t)
        await pg.evaluate("window.__v.teleportTo([0, 15, 45], 0)"); await pg.wait_for_timeout(300)
        await pg.evaluate("window.__v.teleportTo([0, 15, 100], 0)"); await pg.wait_for_timeout(400)
        rapport(await rinfo() == "", "au-dela de 2 fois la portee : ligne cachee", await rinfo())
        await pg.emulate_media(reduced_motion="reduce")
        await pg.evaluate("window.__v.teleportTo([0, 15, 45], 0)"); await pg.wait_for_timeout(400)
        red = await pg.evaluate("(() => { const s = document.querySelector('#radioInfo .srcFar'); return s ? [getComputedStyle(s).animationName, getComputedStyle(s).textDecorationLine] : null; })()")
        rapport(bool(red) and red[0] == "none" and "underline" in red[1], "mouvement reduit : pas de clignotement, texte souligne", red)
        await pg.emulate_media(reduced_motion="no-preference")
        await pg.evaluate("window.__v.teleportTo([-50, 15, 1], 0)")
        await jouer("/illisible/.test(document.getElementById('radioInfo').textContent)")
        t = await rinfo()
        rapport("illisible" in t and " m / " not in t, "flux illisible : pas de distance", t)
        await pg.evaluate("window.__v.teleportTo([50, 15, 3], 0)")
        await jouer("window.__m.playing()")
        t = await minfo()
        rapport(await pg.evaluate("window.__m.playing()") and "(3 m / 8 m)" in t, "musique : la ligne donne la distance et la portee", t)
        await pg.evaluate("window.__v.teleportTo([50, 15, 6], 0)"); await pg.wait_for_timeout(400)
        t = await minfo()
        rapport("(6 m / 8 m)" in t, "musique : la distance suit la marche", t)
        b = await bulle('musicInfo')
        rapport("Zone musique : Zone zik" in b and "Piste : 1-a.wav (1/1)" in b and "Distance : 6 m (portée 8 m), à portée" in b and "Case : couper" in b and "⏮" not in b, "musique : info-bulle de la ligne (zone, piste, distance, commandes ; pas de boutons avec une seule piste)", b)
        await pg.evaluate("window.__v.teleportTo([50, 15, 12], 0)"); await pg.wait_for_timeout(400)
        t = await minfo()
        rapport("hors de port" in t and "(12 m / 8 m)" in t and not await pg.evaluate("window.__m.playing()") and await pg.evaluate("!!document.querySelector('#musicInfo .srcFar')"), "musique hors de portee : ligne conservee avec la distance qui clignote, piste arretee", t)
        await pg.evaluate("window.__v.teleportTo([50, 15, 30], 0)"); await pg.wait_for_timeout(400)
        rapport(await minfo() == "", "musique : au-dela de 2 fois la portee, ligne cachee", await minfo())
        rapport(not errs, "aucune erreur JavaScript", errs)
        await br.close()
    srv.shutdown()
    print("\nRESULTAT : " + ("tout est passe" if not echecs else f"ECHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
