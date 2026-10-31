#!/usr/bin/env python3
"""Mode « numero seul » : la page cherche 12.jpg, 12.png... et le titre dans 12.txt ; cle imageExts de la config.
Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/image_numero.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, socket, struct, subprocess, sys, tempfile, time, zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_numero_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
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
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(b"\x00\xc8\x28\x28")) + ch(b"IEND", b""))


def zone(i, cible):
    return {"id": i, "type": "image", "label": i, "x": 0, "y": 2, "z": 0, "yaw": 0, "shape": "ring", "trigger": "click", "radius": 2, "w": 1.2, "h": 0, "target": cible, "spawn": "", "confirm": False, "private": False, "showName": False}


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


IMGS = """() => window.__v.imageDiag().map(d => (d.loaded || '').split('/').pop()).filter(Boolean).sort()"""   # fichier lu (diagnostic des images) : l'adresse de l'image est blob:
LEGS = """() => { const o = []; window.__v.scene.traverse(n => { if (n.userData && n.userData.caption) o.push([n.userData.caption, n.visible]); }); return o.sort(); }"""


def fabrique(site, nom, zones, *opt):
    zj = tmp / (nom + ".z.json"); zj.write_text(json.dumps(zones), encoding="utf-8")
    out = site / (nom + ".html")
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--no-sea", "--zones", str(zj), *opt, *vend], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation {nom}\n{r.stdout}{r.stderr}")
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    sol_glb(tmp / "sol.glb")
    for n in ("12.png", "9.jpg", "9.png", "5.png", "3-Titre.png", "8.png", "8.webp"):
        png(site / n)
    (site / "12.txt").write_text("\ufeff\n  Titre douze  \nsuite ignoree\n", encoding="utf-8")
    (site / "3-Titre.txt").write_text("Autre titre\n", encoding="utf-8")
    fabrique(site, "p", [zone("a", "12"), zone("b", "9"), zone("c", "5"), zone("d", "absente"), zone("e", "3-Titre.png")])
    fabrique(site, "q", [zone("f", "8")], "--modular")
    cfgq = site / "q.config.json"; c = json.loads(cfgq.read_text(encoding="utf-8")); c["imageExts"] = "webp"; cfgq.write_text(json.dumps(c), encoding="utf-8")
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            errs = []

            async def ouvre(nom):
                pg = await br.new_page(viewport={"width": 900, "height": 600}); pg.on("pageerror", lambda e: errs.append(str(e)))
                await pg.goto(f"http://127.0.0.1:{port}/{nom}.html")
                await pg.wait_for_function("document.getElementById('msg') === null && window.__v && window.__v.model", timeout=60000)
                await pg.wait_for_timeout(3500)
                return pg

            pg = await ouvre("p")
            im = await pg.evaluate(IMGS)
            rapport(im == ["12.png", "3-Titre.png", "5.png", "9.jpg"], "« 12 » -> 12.png, « 5 » -> 5.png, « 9 » -> 9.jpg (jpg avant png), « absente » : rien, nom complet intact", im)
            lg = await pg.evaluate(LEGS)
            rapport(lg == [["Autre titre", True], ["Titre douze", True]], "titre : 1re ligne non vide de 12.txt (BOM ignore), 3-Titre.txt l'emporte sur le tiret du nom, aucune legende sans fichier texte", lg)
            await pg.close()

            pg = await ouvre("q")
            im = await pg.evaluate(IMGS)
            rapport(im == ["8.webp"], "imageExts = webp : « 8 » prend 8.webp et ignore 8.png", im)
            await pg.close()
            rapport(not errs, "aucune erreur JavaScript", errs)
            await br.close()
    finally:
        proc.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
