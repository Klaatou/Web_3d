#!/usr/bin/env python3
"""Champ image souple et legende : « 1 » devient le vrai nom de fichier du dossier de la region (editeur), la legende est le texte entre le premier tiret et l'extension, sous l'image (editeur et page).
Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/image_legende.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, socket, struct, subprocess, sys, tempfile, time, zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_legende_"))
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


NOMS = """() => { const d = { name: 'reg', async *entries() { for (const n of ['1-Soleil_couchant.jpg', '1-aaa.webp', '10-autre.png', '2.PNG', 'texte.txt', '4-x.jpg']) yield [n, { kind: 'file' }]; yield ['sous-dossier', { kind: 'directory' }]; } };
  return Promise.all(['1', '10', '2', '3', '1.jpg', 'http://x/1', 'a/1', ' 4 '].map(v => window.__viewer.imageNameFromDir(v, d))); }"""
SANSDOSSIER = """() => window.__viewer.imageNameFromDir('1', null)"""
LEGENDES = """() => { const o = []; window.__viewer.scene.traverse(n => { if (n.userData && n.userData.caption) o.push([n.userData.caption, n.visible]); }); return o; }"""
LEGENDES_PAGE = """() => { const o = []; window.__v.scene.traverse(n => { if (n.userData && n.userData.caption) o.push([n.userData.caption, n.visible]); }); return o; }"""


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    sol_glb(tmp / "sol.glb"); png(site / "1-Soleil_couchant.png")
    (tmp / "z.json").write_text(json.dumps([zone("a", "1-Soleil_couchant.png"), zone("b", "absente-x.png"), zone("c", "sans_tiret.png")]), encoding="utf-8")
    out = site / "p.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--no-sea", "--zones", str(tmp / "z.json"), *vend], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            errs = []

            pv = await br.new_page(viewport={"width": 1300, "height": 800}); pv.on("pageerror", lambda e: errs.append(str(e)))
            await pv.goto((DIST / "glb-viewer.html").as_uri()); await pv.wait_for_function("window.__viewer", timeout=30000)
            res = await pv.evaluate(NOMS)
            att = [{"name": "1-aaa.webp", "n": 2}, {"name": "10-autre.png", "n": 1}, {"name": "2.PNG", "n": 1}, {"name": "3", "none": True, "dir": "reg"}, {"name": "1.jpg"}, {"name": "http://x/1"}, {"name": "a/1"}, {"name": "4-x.jpg", "n": 1}]
            rapport(res == att, "« 1 » : premier par ordre alphabetique, « 10 » n'est pas pris pour « 1 », casse et extension ignorees, introuvable signale, noms avec extension, chemins et adresses intacts", res)
            r2 = await pv.evaluate(SANSDOSSIER)
            rapport(r2 == {"name": "1", "nodir": True}, "sans dossier choisi : « 1 » reste tel quel et l'editeur le signale", r2)
            await pv.set_input_files("#fGlb", str(tmp / "sol.glb")); await pv.wait_for_function("window.__viewer.model", timeout=60000)
            await pv.evaluate("(z) => window.__viewer.setZones(z)", [zone("a", "1-Soleil_couchant.jpg"), zone("b", "3-La nuit étoilée.PNG"), zone("c", "a/b/2.jpg"), zone("d", "x-y-z.jpg"), zone("e", "data:image/png;base64,AAAA")])
            await pv.wait_for_timeout(1500)
            cap = sorted(c[0] for c in await pv.evaluate(LEGENDES))
            rapport(cap == ["La nuit étoilée", "Soleil couchant", "y-z"], "editeur : legende = texte entre le premier tiret et l'extension (« _ » en espace) ; sans tiret ou en data: : aucune", cap)
            await pv.close()

            pg = await br.new_page(viewport={"width": 900, "height": 600}); pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{port}/p.html")
            await pg.wait_for_function("document.getElementById('msg') === null && window.__v && window.__v.model", timeout=60000)
            await pg.wait_for_timeout(3000)
            cp = sorted(await pg.evaluate(LEGENDES_PAGE))
            rapport(cp == [["Soleil couchant", True], ["x", False]], "page exportee : legende visible quand l'image existe, masquee quand elle est introuvable", cp)
            await pg.close()
            rapport(not errs, "aucune erreur JavaScript", errs)
            await br.close()
    finally:
        proc.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
