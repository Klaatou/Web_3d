#!/usr/bin/env python3
"""Test des zones radio (type cast, 1.10.32) : le flux de la zone a portee joue en promenade, volume selon la distance, une seule zone a la fois,
arret hors portee et en vue globale, case « Radio des zones » de Reglages, flux illisible dit dans le bloc d'etat, zone ni cliquable ni « invite E »,
portee jusqu'a 200 m (les autres zones restent a 50) ; le viewer propose le type.

Le flux est un WAV servi en local (le Chromium du bac a sable n'a pas de decodeur MP3 ; un vrai flux Icecast n'est pas joignable d'ici).
Prerequis : pip install playwright && playwright install chromium ; python build.py avant.
Variable facultative : THREE_DIR (paquet npm three, hors ligne), CHROMIUM.
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


def serveur(dossier):
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(dossier))
    h.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def page(port):
    # le centre du sol est releve a 15 m par le cadrage : zones posees a cette hauteur
    Z = lambda i, t, x, z, **k: dict({"id": i, "type": t, "label": "Zone " + i, "x": x, "y": 15, "z": z}, **k)
    zones = [Z("salle", "cast", 0, 0, radius=10, target=f"http://127.0.0.1:{port}/flux.wav"),
             Z("bar", "cast", 30, 0, radius=5, target=f"http://127.0.0.1:{port}/flux.wav"),
             Z("casse", "cast", -30, 0, radius=5, target=f"http://127.0.0.1:{port}/absent.mp3"),
             Z("grande", "cast", 200, 0, radius=150, target=f"http://127.0.0.1:{port}/flux.wav"),   # loin : sa portee de 150 m ne couvre pas le sol
             Z("lien", "url", 0, 40, radius=150, target="https://exemple.invalid/", trigger="click")]   # 150 : ramene a 50
    (tmp / "z.json").write_text(json.dumps(zones), encoding="utf-8")
    out = tmp / "p.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--zones", str(tmp / "z.json"), "--no-sea", *vend],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    t = out.read_text(encoding="utf-8")
    for a, b in (("const viewer = createViewer(", "const viewer = window.__v = createViewer("), ("const RADIO = (() => {", "const RADIO = window.__r = (() => {")):
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
    v = (DIST / "glb-viewer.html").read_text(encoding="utf-8")
    rapport('value="cast"' in v and "castTry" in v, "viewer : le type Radio est propose et le bouton d'essai existe")
    async with async_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
        br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
        pg = await br.new_page(locale="fr-FR"); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(out.as_uri())
        await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
        await pg.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
        zs = {z["id"]: z for z in await pg.evaluate("window.__v.getZones()")}
        rapport(zs["grande"]["radius"] == 150 and zs["lien"]["radius"] == 50 and zs["salle"]["radius"] == 10, "portee : jusqu'a 200 m pour une radio, 50 pour les autres",
                {k: z["radius"] for k, z in zs.items()})
        rapport(all(z["type"] == "cast" and z["mesh"] == "" and z["trigger"] == "click" for k, z in zs.items() if k != "lien"), "zone radio : type conserve, jamais liee a un element")
        info = lambda: pg.evaluate("(() => { const e = document.getElementById('radioInfo'); return e.hidden ? '' : e.textContent; })()")
        playing = lambda: pg.evaluate("window.__r.playing()")
        level = lambda: pg.evaluate("window.__r.level()")
        rapport(await pg.evaluate("document.getElementById('visRadio') !== null && document.getElementById('visSounds') !== null"), "Reglages : cases « Sons » et « Radio des zones » presentes sans serveur de presence")
        # vue globale : rien ; promenade hors portee : rien
        rapport(await info() == "" and not await playing(), "vue globale : pas de radio")
        await pg.evaluate("window.__v.walkStart({ pos: [0, 15, 20], yaw: 0 })"); await pg.wait_for_timeout(500)
        rapport(await info() == "" and not await playing(), "promenade hors portee : pas de radio", await info())
        # a portee avant toute action du visiteur : la ligne le dit, rien ne joue
        await pg.evaluate("window.__v.teleportTo([0, 15, 8], 0)"); await pg.wait_for_timeout(500)
        t = await info()
        rapport("Zone salle" in t and "clic" in t and not await playing(), "a portee avant la premiere action : « un clic ou une touche », rien ne joue", t)
        rapport(await pg.evaluate("document.getElementById('zonePrompt').hidden || !/salle/.test(document.getElementById('zonePrompt').textContent)"), "zone radio : pas d'invite « clic ou E »", await pg.evaluate("document.getElementById('zonePrompt').textContent"))
        # premiere action : le flux demarre
        await pg.keyboard.press("ControlLeft")
        try:
            await pg.wait_for_function("window.__r.playing()", timeout=15000)
        except Exception:
            pass
        rapport(await playing() and "Zone salle" in await info() and "clic" not in await info(), "apres une touche : le flux joue, la ligne « Radio » le dit", await info())
        l_bord = await level()
        await pg.evaluate("window.__v.teleportTo([0, 15, 1], 0)"); await pg.wait_for_timeout(400)
        l_centre = await level()
        rapport(0.4 < l_centre <= 0.5 and l_bord < 0.15 and l_bord > 0, "volume : 0,45 au centre (gain 0,9 x volume 50 %), presque nul au bord", (l_centre, l_bord))
        # hors portee : arret ; autre zone : son flux
        await pg.evaluate("window.__v.teleportTo([0, 15, 15], 0)"); await pg.wait_for_timeout(500)
        rapport(not await playing() and await info() == "", "sortie de la portee : le flux s'arrete, la ligne disparait", await info())
        await pg.evaluate("window.__v.teleportTo([30, 15, 1], 0)")
        try:
            await pg.wait_for_function("window.__r.playing()", timeout=15000)
        except Exception:
            pass
        rapport(await playing() and "Zone bar" in await info(), "autre zone radio : son flux joue", await info())
        # Reglages : la case coupe et relance
        await pg.evaluate("(() => { const c = document.getElementById('visRadio'); c.checked = false; c.dispatchEvent(new Event('change')); })()"); await pg.wait_for_timeout(300)
        rapport(not await playing() and "coup" in await info(), "case « Radio des zones » decochee : arret, la ligne dit « son coupe »", await info())
        await pg.evaluate("(() => { const c = document.getElementById('visRadio'); c.checked = true; c.dispatchEvent(new Event('change')); })()")
        try:
            await pg.wait_for_function("window.__r.playing()", timeout=15000)
        except Exception:
            pass
        rapport(await playing(), "case recochee : le flux reprend")
        await pg.evaluate("(() => { const r = document.getElementById('visVolume'); r.value = 100; r.dispatchEvent(new Event('input')); })()"); await pg.wait_for_timeout(200)
        rapport(abs(await level() - 0.8) < 0.1, "volume des Sons a 100 : niveau 0,8 (gain 0,8 a 1 m sur 5)", await level())
        # flux illisible
        await pg.evaluate("window.__v.teleportTo([-30, 15, 1], 0)")
        try:
            await pg.wait_for_function("/illisible/.test(document.getElementById('radioInfo').textContent)", timeout=15000)
        except Exception:
            pass
        rapport("illisible" in await info() and not await playing(), "flux illisible : la ligne le dit, rien ne joue", await info())
        # vue globale : arret
        await pg.evaluate("window.__v.teleportTo([30, 15, 1], 0)")
        try:
            await pg.wait_for_function("window.__r.playing()", timeout=15000)
        except Exception:
            pass
        await pg.evaluate("window.__v.toggleWalk()"); await pg.wait_for_timeout(400)
        rapport(not await playing() and await info() == "", "retour en vue globale : arret, ligne cachee", await info())
        rapport(not errs, "aucune erreur JavaScript", errs)
        await br.close()
    srv.shutdown()
    print("\nRESULTAT : " + ("tout est passe" if not echecs else f"ECHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
