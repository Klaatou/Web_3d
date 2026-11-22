#!/usr/bin/env python3
"""Test de la bulle d'une zone radio (1.13.2) : la 2e ligne donne le NOM du flux (pas son adresse) ; celui du flux choisi quand c'est la radio ecoutee,
sinon celui du flux retenu (1.13.3 ; le premier si aucun) ; sans nom, l'adresse ; plus de « ... +N ». Meme famille que zone_cast.

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


PORT = [0]


def page():
    u = lambda n: f"http://127.0.0.1:{PORT[0]}/{n}.wav"
    # le centre du sol est releve a 15 m par le cadrage : zones posees a cette hauteur
    Z = lambda i, x, z, st: {"id": i, "type": "cast", "label": "Zone " + i, "x": x, "y": 15, "z": z, "radius": 10, "cone": True, "streams": st}
    zones = [Z("salle", 0, 0, [["Jazz", u("a")], ["Rock", u("b")], ["", u("c")]]),
             Z("bar", 30, 0, [["Classique", u("d")]]),
             Z("nu", 30, 25, [["", u("e")]])]
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


async def bulle(pg, zid):
    """texte de la bulle quand la souris est sur le cone de la zone (None si pas de bulle)"""
    c = [c for c in await pg.evaluate("window.__v.getCones()") if c["id"] == zid][0]
    await pg.mouse.move(c["sx"], c["sy"]); await pg.wait_for_timeout(150)
    await pg.mouse.move(c["sx"] + 1, c["sy"]); await pg.wait_for_timeout(150)
    return await pg.evaluate("(() => { const e = document.getElementById('zoneTip'); return e && !e.hidden ? e.innerText : null; })()")


async def main():
    from playwright.async_api import async_playwright
    sol_glb(tmp / "sol.glb")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    PORT[0] = srv.server_address[1]
    out = page()
    async with async_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
        br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
        pg = await br.new_page(locale="fr-FR", viewport={"width": 1000, "height": 700}); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(out.as_uri())
        await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
        await pg.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
        # vue globale : aucune radio n'est ecoutee : le premier flux de chaque zone
        t = await bulle(pg, "salle")
        rapport(t is not None and "Zone salle" in t and "Jazz" in t and "http" not in t and " … +" not in t, "vue globale : la bulle de la radio donne le nom du premier flux, pas l'adresse, pas de « +N »", t)
        t = await bulle(pg, "bar")
        rapport(t is not None and "Classique" in t and "http" not in t, "radio a un seul flux : son nom", t)
        t = await bulle(pg, "nu")
        rapport(t is not None and "127.0.0.1" in t, "flux sans nom : l'adresse (la bulle n'est pas vide)", t)
        # promenade dans la salle : le flux choisi est celui de la bulle
        await pg.evaluate("window.__v.walkStart({ pos: [0, 15, 8], yaw: 0 })"); await pg.wait_for_timeout(500)
        await pg.evaluate("window.__r.setIdx(1)"); await pg.wait_for_timeout(300)
        t = await bulle(pg, "salle")
        rapport(t is not None and "Rock" in t and "Jazz" not in t, "radio ecoutee, 2e flux choisi : la bulle donne « Rock »", t)
        await pg.evaluate("window.__r.setIdx(2)"); await pg.wait_for_timeout(300)
        t = await bulle(pg, "salle")
        rapport(t is not None and "127.0.0.1" in t and "Rock" not in t and "Jazz" not in t, "3e flux, sans nom : son adresse (pas le nom d'un autre flux)", t)
        await pg.evaluate("window.__r.setIdx(1)"); await pg.wait_for_timeout(300)
        await pg.evaluate("window.__v.toggleWalk()"); await pg.wait_for_timeout(400)
        t = await bulle(pg, "salle")
        rapport(t is not None and "Rock" in t and "Jazz" not in t, "retour en vue globale (plus de radio ecoutee) : la bulle donne le flux retenu (1.13.3 ; avant : le premier)", t)
        rapport(not errs, "aucune erreur JavaScript", errs)
        await br.close()
    print()
    print("RESULTAT : " + ("tout est passe" if not echecs else f"{echecs} echec(s)"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
