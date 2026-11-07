#!/usr/bin/env python3
"""GIF animes sur les zones image (lot 1.6.15) : un GIF d'au moins deux images s'anime, un GIF d'une image ou un PNG restent fixes ; rien de plus quand le plan est hors du champ, trop petit a l'ecran ou quand
l'utilisateur demande moins d'animations. Le GIF d'essai est ecrit a la main : 1 pixel, deux images (rouge puis bleu, 200 ms chacune), et un GIF fixe d'une image.
Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/gif_anim.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, socket, struct, subprocess, sys, tempfile, time, zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_gif_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"), flush=True)
    echecs += not ok


def sol_glb(path):
    v = [(-20, 0, -20), (20, 0, -20), (20, 0, 20), (-20, 0, 20)]
    pos = b"".join(struct.pack("<3f", *p) for p in v)
    idx = struct.pack("<6H", 0, 1, 2, 0, 2, 3)
    blob = pos + idx + bytes(-(len(pos) + 12) % 4)
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos)}, {"buffer": 0, "byteOffset": len(pos), "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-20, 0, -20], "max": [20, 0, 20]}, {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}], "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * (-len(js) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def png(path):
    def ch(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(b"\x00\xc8\x28\x28")) + ch(b"IEND", b""))


def gif(path, couleurs):
    """GIF de 1 pixel ; une image par couleur de la liste (0 = rouge, 1 = bleu), 200 ms chacune, boucle infinie"""
    img = {0: b"\x02\x02\x44\x01\x00", 1: b"\x02\x02\x4c\x01\x00"}
    d = b"GIF89a" + struct.pack("<HHBBB", 1, 1, 0x80, 0, 0) + bytes([255, 0, 0, 0, 0, 255])
    if len(couleurs) > 1:
        d += b"\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00"
    for c in couleurs:
        d += b"\x21\xf9\x04\x00" + struct.pack("<H", 20) + b"\x00\x00" + b"\x2c" + struct.pack("<HHHHB", 0, 0, 1, 1, 0) + img[c]
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(d + b"\x3b")


def moyenne(p):
    """couleur moyenne (r, v, b) d'un PNG de capture d'ecran (8 bits, RGB ou RGBA, sans entrelacement)"""
    i, idat, w, h, ct = 8, b"", 0, 0, 2
    while i < len(p):
        n, t = struct.unpack(">I4s", p[i:i + 8]); d = p[i + 8:i + 8 + n]; i += 12 + n
        if t == b"IHDR": w, h, _bd, ct = struct.unpack(">IIBB", d[:10])
        elif t == b"IDAT": idat += d
    bpp = {2: 3, 6: 4}[ct]; raw = zlib.decompress(idat); stride = w * bpp; prev = bytearray(stride); q = 0; tot = [0, 0, 0]
    for _ in range(h):
        ft = raw[q]; line = bytearray(raw[q + 1:q + 1 + stride]); q += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0; b = prev[x]; c = prev[x - bpp] if x >= bpp else 0
            if ft == 1: line[x] = (line[x] + a) & 255
            elif ft == 2: line[x] = (line[x] + b) & 255
            elif ft == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif ft == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else (b if pb <= pc else c))) & 255
        for x in range(w):
            for k in range(3): tot[k] += line[x * bpp + k]
        prev = line
    return [t / (w * h) for t in tot]


def zone(i, cible, x=0, y=3, z=0, w=6):
    return {"id": i, "type": "image", "label": i, "x": x, "y": y, "z": z, "yaw": 0, "shape": "ring", "trigger": "click", "radius": 2, "w": w, "h": 0, "target": cible, "spawn": "", "confirm": False, "private": False, "showName": False, "mesh": "", "link": ""}


def serveur(dossier):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=dossier, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close(); return proc, port
        except OSError:
            time.sleep(0.1)
    sys.exit("[ECHEC] serveur http")


def fabrique(site, nom, zones):
    zj = tmp / (nom + ".z.json"); zj.write_text(json.dumps(zones), encoding="utf-8")
    out = site / (nom + ".html")
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--no-sea", "--zones", str(zj), *vend], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation {nom}\n{r.stdout}{r.stderr}")
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")


CENTRE = """(id) => { let m = null; window.__v.scene.traverse(n => { if (n.userData && n.userData.diag && n.userData.diag.id === id) m = n; });
  const v = new window.__v.camera.position.constructor(); m.getWorldPosition(v); v.project(window.__v.camera); const r = window.__v.renderer.domElement.getBoundingClientRect();
  return [r.left + (v.x + 1) / 2 * r.width, r.top + (1 - v.y) / 2 * r.height]; }"""


async def couleurs(pg, id_, n=12, pas=150):
    x, y = await pg.evaluate(CENTRE, id_)
    vus = []
    for _ in range(n):
        r, g, b = moyenne(await pg.screenshot(clip={"x": x - 4, "y": y - 4, "width": 8, "height": 8}, type="png"))
        vus.append("rouge" if r > b + 80 else ("bleu" if b > r + 80 else "autre"))
        await pg.wait_for_timeout(pas)
    return vus


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    sol_glb(tmp / "sol.glb")
    gif(site / "medias" / "20.gif", [0, 1]); gif(site / "medias" / "21.gif", [0]); png(site / "medias" / "22.png")
    fabrique(site, "p", [zone("a", "20.gif"), zone("b", "21.gif", x=10), zone("c", "22.png", x=-10)])
    fabrique(site, "d", [zone("a", "20.gif", x=300), zone("t", "20.gif", w=0.3)])
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            errs = []

            async def ouvre(nom, reduit=False):
                ctx = await br.new_context(viewport={"width": 900, "height": 600}, reduced_motion="reduce" if reduit else "no-preference")
                pg = await ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
                await pg.goto(f"http://127.0.0.1:{port}/{nom}.html")
                await pg.wait_for_function("document.getElementById('msg') === null && window.__v && window.__v.model", timeout=60000)
                await pg.wait_for_function("window.__v.imageDiag().filter(d => d.loaded).length >= 1", timeout=30000)
                await pg.wait_for_timeout(1500)
                return pg

            pg = await ouvre("p")
            info = await pg.evaluate("window.__v.animInfo()")
            rapport(info["planes"] == 1, "un seul plan est anime : le GIF de deux images (le GIF d'une image et le PNG restent fixes)", info)
            vus = await couleurs(pg, "a")
            rapport("rouge" in vus and "bleu" in vus, "le GIF anime change de couleur a l'ecran (rouge puis bleu)", vus)
            t1 = (await pg.evaluate("window.__v.animInfo()"))["ticks"]
            await pg.wait_for_timeout(600)
            t2 = (await pg.evaluate("window.__v.animInfo()"))["ticks"]
            rapport(t2 - t1 >= 2, "l'image change dans la texture tant que le plan est visible (au moins 2 fois en 0,6 s)", (t1, t2))
            fixe = await couleurs(pg, "b", n=6)
            rapport(set(fixe) == {"rouge"}, "le GIF d'une seule image reste fixe", fixe)
            await pg.context.close()

            pg = await ouvre("p", reduit=True)
            info = await pg.evaluate("window.__v.animInfo()")
            vus = await couleurs(pg, "a", n=8)
            t = (await pg.evaluate("window.__v.animInfo()"))["ticks"]
            rapport(info["planes"] == 1 and t == 0 and len(set(vus)) == 1, "reglage « moins d'animations » du systeme : le GIF reste sur sa premiere image", (info, t, vus))
            await pg.context.close()

            pg = await ouvre("d")
            await pg.wait_for_timeout(1200)
            info = await pg.evaluate("window.__v.animInfo()")
            rapport(info["planes"] == 2 and info["ticks"] == 0, "un GIF hors du champ de la camera (300 m de cote) et un GIF trop petit a l'ecran (moins de 8 px) ne font aucun travail", info)
            await pg.context.close()
            rapport(not errs, "aucune erreur JavaScript", errs[:2])
            await br.close()
    finally:
        proc.kill()
    print("\nRESULTAT : " + ("tout est passe" if not echecs else f"{echecs} echec(s)"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
