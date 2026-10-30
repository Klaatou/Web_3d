#!/usr/bin/env python3
"""Materiaux rendus opaques (--solid-materials / solidMaterials) : un materiau BLEND garde depthWrite = false (GLTFLoader) et laisse voir a travers ;
le texte donne le passe en opaque (transparent = false, depthWrite = true), « =nom » est un nom exact, setCfg le change a chaud et le remet a l'origine.
Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/solid_materiaux.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_solid_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def mur_glb(path):
    """sol, mur (materiau « mur-solide », BLEND) et vitre (materiau « vitre », BLEND)"""
    quads = [[(-20, 0, -20), (20, 0, -20), (20, 0, 20), (-20, 0, 20)], [(-5, 0, -5), (5, 0, -5), (5, 4, -5), (-5, 4, -5)], [(-2, 0, -8), (2, 0, -8), (2, 3, -8), (-2, 3, -8)]]
    v = [p for q in quads for p in q]
    pos = b"".join(struct.pack("<3f", *p) for p in v)
    idx = b"".join(struct.pack("<6H", 4 * i, 4 * i + 1, 4 * i + 2, 4 * i, 4 * i + 2, 4 * i + 3) for i in range(3))
    blob = pos + idx
    mat = lambda nom: {"name": nom, "pbrMetallicRoughness": {"baseColorFactor": [0.6, 0.6, 0.6, 1]}, "alphaMode": "BLEND", "doubleSided": True}
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos)}] + [{"buffer": 0, "byteOffset": len(pos) + 12 * i, "byteLength": 12} for i in range(3)],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 12, "type": "VEC3", "min": [-20, 0, -20], "max": [20, 4, 20]}] + [{"bufferView": 1 + i, "componentType": 5123, "count": 6, "type": "SCALAR"} for i in range(3)],
         "materials": [mat("sol-plein"), mat("mur-solide"), mat("vitre")],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1 + i, "material": i}]} for i in range(3)],
         "nodes": [{"mesh": i, "name": nom} for i, nom in enumerate(["sol", "mur", "vitre"])], "scenes": [{"nodes": [0, 1, 2]}], "scene": 0}
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


ETAT = """() => { const out = {}; window.__v.scene.traverse(o => { if (o.isMesh && o.material && o.material.name) { const m = o.material; out[m.name] = [m.transparent, m.depthWrite]; } }); return out; }"""


def fabrique(site, nom, *opt):
    out = site / (nom + ".html")
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "mur.glb"), "-o", str(out), "--no-sea", *opt, *vend], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation {nom}\n{r.stdout}{r.stderr}")
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    mur_glb(tmp / "mur.glb")
    fabrique(site, "sans")
    fabrique(site, "avec", "--solid-materials", "mur")
    fabrique(site, "exact", "--solid-materials", "=vitre")
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            errs = []

            async def ouvre(nom):
                pg = await br.new_page(viewport={"width": 800, "height": 500})
                pg.on("pageerror", lambda e: errs.append(str(e)))
                await pg.goto(f"http://127.0.0.1:{port}/{nom}.html")
                await pg.wait_for_function("document.getElementById('msg') === null && window.__v && window.__v.model", timeout=60000)
                return pg

            pg = await ouvre("sans"); e = await pg.evaluate(ETAT)
            rapport(e["mur-solide"] == [True, False] and e["vitre"] == [True, False], "sans l'option : les materiaux BLEND gardent transparent = true et depthWrite = false (comportement de GLTFLoader)", e)
            await pg.evaluate("window.__v.setCfg({ solidMaterials: 'mur' })"); e = await pg.evaluate(ETAT)
            rapport(e["mur-solide"] == [False, True] and e["vitre"] == [True, False] and e["sol-plein"] == [True, False], "setCfg « mur » : seul « mur-solide » devient opaque", e)
            await pg.evaluate("window.__v.setCfg({ solidMaterials: '' })"); e = await pg.evaluate(ETAT)
            rapport(e["mur-solide"] == [True, False], "setCfg « » : le materiau retrouve son etat d'origine", e)
            await pg.close()

            pg = await ouvre("avec"); e = await pg.evaluate(ETAT)
            rapport(e["mur-solide"] == [False, True] and e["vitre"] == [True, False] and e["sol-plein"] == [True, False], "page fabriquee avec --solid-materials mur : « mur-solide » opaque, « vitre » et « sol-plein » inchanges", e)
            await pg.close()

            pg = await ouvre("exact"); e = await pg.evaluate(ETAT)
            rapport(e["vitre"] == [False, True] and e["mur-solide"] == [True, False], "=vitre : nom exact", e)
            await pg.evaluate("window.__v.setCfg({ solidMaterials: '=vit' })"); e = await pg.evaluate(ETAT)
            rapport(e["vitre"] == [True, False], "=vit n'est pas le nom exact : rien n'est opaque", e)
            await pg.close()
            rapport(not errs, "aucune erreur JavaScript", errs)
            await br.close()
    finally:
        proc.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
