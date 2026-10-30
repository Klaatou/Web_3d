#!/usr/bin/env python3
"""Pointeur : l'etiquette de la page exportee (--names) donne le nom de l'objet racine (batiment), le sous-element en petit.

GLB d'essai a hierarchie imbriquee, comme Fashion_Store.glb (noeud racine « Maison Rouge » qui porte un enfant « prim0-mesh »). Le chargeur de three remplace les espaces par _ : le nom affiche est celui d'origine (userData.name).
Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/pointeur_objet.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time, zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_pointeur_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def png(w, h, rgb=(200, 20, 20)):
    brut = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    def ch(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(brut)) + ch(b"IEND", b"")


def mur_glb(path):
    """sol de 40 x 40 m (normale vers le haut) un mur de 20 x 6 m en z = -5 (normale vers +z) et un mur en x = 8 (normale vers -x)"""
    v = [(-20, 0, -20), (20, 0, -20), (20, 0, 20), (-20, 0, 20), (-10, 0, -5), (10, 0, -5), (10, 6, -5), (-10, 6, -5), (8, 0, -10), (8, 0, 10), (8, 6, 10), (8, 6, -10)]
    pos = b"".join(struct.pack("<3f", *p) for p in v)
    idx = struct.pack("<18H", 0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7, 8, 9, 10, 8, 10, 11)
    blob = pos + idx
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos)}, {"buffer": 0, "byteOffset": len(pos), "byteLength": len(idx)}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 12, "type": "VEC3", "min": [-20, 0, -20], "max": [20, 6, 20]},
                       {"bufferView": 1, "componentType": 5123, "count": 18, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "salle"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * (-len(js) % 4)
    blob += bytes(-len(blob) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js
                     + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


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


LIRE = """() => { const out = {}; window.__v.scene.traverse(o => { if (o.isMesh && o.parent && o.parent.userData && o.parent.userData.zoneId) {
    const m = o.material.map; out[o.parent.userData.zoneId] = { visible: o.visible, sx: o.scale.x, sy: o.scale.y, image: !!(m && m.image && m.image.width), iw: m && m.image ? m.image.width : 0,
      pos: o.parent.position.toArray(), yaw: o.parent.rotation.y }; } }); return out; }"""
PROJ = """([x, y, z]) => { const v = window.__viewer; v.camera.updateMatrixWorld(true);
    const p = v.camera.position.clone().set(x, y, z).project(v.camera), r = v.renderer.domElement.getBoundingClientRect();
    return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; }"""


PROJ = """([x, y, z]) => { const v = window.__v; v.camera.updateMatrixWorld(true);
    const p = v.camera.position.clone().set(x, y, z).project(v.camera), r = v.renderer.domElement.getBoundingClientRect();
    return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; }"""

def maison_glb(path):
    """grand mur en z = -5 (noeud racine « Maison Rouge ») et un petit panneau en z = -4,5, enfant « prim0-mesh »"""
    v = [(-10, 0, -5), (10, 0, -5), (10, 6, -5), (-10, 6, -5), (-1, 1, -4.5), (1, 1, -4.5), (1, 3, -4.5), (-1, 3, -4.5)]
    pos = b"".join(struct.pack("<3f", *p) for p in v)
    idx = struct.pack("<12H", 0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7)
    blob = pos + idx
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos)}, {"buffer": 0, "byteOffset": len(pos), "byteLength": 12}, {"buffer": 0, "byteOffset": len(pos) + 12, "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 8, "type": "VEC3", "min": [-10, 0, -5], "max": [10, 6, -4.5]},
                       {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}, {"bufferView": 2, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}, {"primitives": [{"attributes": {"POSITION": 0}, "indices": 2}]}],
         "nodes": [{"mesh": 0, "name": "Maison Rouge", "children": [1]}, {"mesh": 1, "name": "prim0-mesh"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * (-len(js) % 4)
    blob += bytes(-len(blob) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js
                     + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


TAG = """() => { const t = document.getElementById('nameTag'); return t.hidden ? null : { gras: t.querySelector('b').textContent, petit: [...t.querySelectorAll('div')].map(d => d.textContent).join(' | ') }; }"""


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    maison_glb(tmp / "maison.glb")
    out = site / "page.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "maison.glb"), "-o", str(out), "--names", "--no-sea", *vend], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            pg = await br.new_page(locale="fr-FR", viewport={"width": 1000, "height": 700}); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{port}/page.html")
            await pg.wait_for_function("document.getElementById('msg') === null && window.__v && window.__v.model", timeout=60000)
            await pg.evaluate("window.__v.frame([0, 0.15, 1], [0, 18, -5], 0.5)")
            await pg.wait_for_timeout(800)
            sx, sy = await pg.evaluate(PROJ, [0, 17, -4.5])
            await pg.mouse.click(sx, sy); await pg.wait_for_timeout(500)
            t = await pg.evaluate(TAG)
            rapport(bool(t) and t["gras"] == "Maison Rouge" and "élément : prim0-mesh" in t["petit"], "clic sur le panneau (enfant) : le nom de l'objet racine en gras (avec ses espaces), le sous-element en petit", t)
            sx, sy = await pg.evaluate(PROJ, [6, 17, -5])
            await pg.mouse.click(sx, sy); await pg.wait_for_timeout(500)
            t = await pg.evaluate(TAG)
            rapport(bool(t) and t["gras"] == "Maison Rouge" and "élément" not in t["petit"], "clic sur le grand mur (le noeud racine lui-meme) : un seul nom, pas de ligne element", t)
            rapport(not errs, "aucune erreur JavaScript", errs)
            await pg.close(); await br.close()
    finally:
        proc.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
