#!/usr/bin/env python3
"""Version 1.0.1 et « Copier le diagnostic » : une ligne par zone image (cible, fichier lu, legende et sa source).
Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/image_diag.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, socket, struct, subprocess, sys, tempfile, time, zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_diag_"))
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
    path.parent.mkdir(exist_ok=True)
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


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    sol_glb(tmp / "sol.glb")
    png(site / "medias" / "12-Cezanne - Apples and Oranges.png"); png(site / "7.png")
    (site / "7.txt").write_text("Titre sept\n", encoding="utf-8")
    zj = tmp / "z.json"; zj.write_text(json.dumps([zone("z12", "12-Cezanne - Apples and Oranges.png"), zone("z7", "7"), zone("zx", "absente")]), encoding="utf-8")
    out = site / "p.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--no-sea", "--zones", str(zj), *vend], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    rapport(version.startswith("1.0.1 ") and version in r.stdout, "VERSION = 1.0.1 et la ligne [OK] du generateur l'affiche", (version, r.stdout[-200:]))
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            errs = []
            pg = await br.new_page(viewport={"width": 900, "height": 600}, locale="fr-FR"); pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{port}/p.html")
            await pg.wait_for_function("document.getElementById('msg') === null && window.__v && window.__v.model", timeout=60000)
            await pg.wait_for_timeout(3500)
            d = sorted(await pg.evaluate("window.__v.imageDiag()"), key=lambda x: x["id"])
            att = [{"id": "z12", "target": "12-Cezanne - Apples and Oranges.png", "loaded": "medias/12-Cezanne - Apples and Oranges.png", "cap": "Cezanne - Apples and Oranges", "src": "name", "vis": True},
                   {"id": "z7", "target": "7", "loaded": "7.png", "cap": "Titre sept", "src": "txt", "vis": True},
                   {"id": "zx", "target": "absente", "loaded": "", "cap": "", "src": "", "vis": False}]
            rapport(sorted(att, key=lambda x: x["id"]) == d, "imageDiag : fichier lu (medias puis racine), legende et source (nom ou texte), image absente", d)
            await pg.click("#diagBtn"); await pg.wait_for_timeout(800)
            txt = await pg.evaluate("document.getElementById('diagOut').value")
            rapport(version in txt and "Cezanne - Apples and Oranges" in txt and "Titre sept" in txt and "fichier texte" in txt, "« Copier le diagnostic » contient la version et les lignes image", txt[:700])
            await pg.close()
            rapport(not errs, "aucune erreur JavaScript", errs)
            await br.close()
    finally:
        proc.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
