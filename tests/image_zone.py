#!/usr/bin/env python3
"""Zone « image » : un tableau plaque contre un mur (Chromium sans tete).

Page exportee (glb2html --zones) servie en http : l'image se charge, la hauteur vient du rapport de l'image quand h = 0, une hauteur donnee est respectee,
une image introuvable ne laisse rien dans la page ; ouverte depuis le disque (file://) : le navigateur refuse l'image, rien n'est dessine, aucune erreur.
Viewer (glb-viewer.html, editeur de zones ; le cadrage releve le modele de 15 m) : un clic sur un mur pose l'image a plat contre lui (2 cm devant, tournee d'apres la face touchee) ; un clic sur le
sol est refuse ; une zone image lue dans un fichier de zones se dessine, avec son image, et se selectionne par clic.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/image_zone.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time, zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_image_"))
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


LIRE = """() => { const out = {}; window.__v.scene.traverse(o => { if (o.isMesh && o.parent && o.parent.userData && o.parent.userData.zoneId) {
    const m = o.material.map; out[o.parent.userData.zoneId] = { visible: o.visible, sx: o.scale.x, sy: o.scale.y, image: !!(m && m.image && m.image.width), iw: m && m.image ? m.image.width : 0,
      pos: o.parent.position.toArray(), yaw: o.parent.rotation.y }; } }); return out; }"""
PROJ = """([x, y, z]) => { const v = window.__viewer; v.camera.updateMatrixWorld(true);
    const p = v.camera.position.clone().set(x, y, z).project(v.camera), r = v.renderer.domElement.getBoundingClientRect();
    return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; }"""


async def page_exportee(br, url, titre, attendu_charge):
    pg = await br.new_page(locale="fr-FR"); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console.error " + m.text) if m.type == "error" and "Failed to load resource" not in m.text and "blocked by CORS" not in m.text else None)
    await pg.goto(url)
    await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
    if attendu_charge:
        await pg.wait_for_function("(" + LIRE + ")().tab && (" + LIRE + ")().tab.image", timeout=20000)
    else:
        await pg.wait_for_timeout(2500)
    z = await pg.evaluate("(" + LIRE + ")()")
    if attendu_charge:
        t, f, m = z.get("tab", {}), z.get("fixe", {}), z.get("manque", {})
        rapport(t.get("image") and t.get("iw") == 8 and abs(t["sx"] - 2) < 1e-6 and abs(t["sy"] - 1) < 1e-6, f"{titre} : h = 0, hauteur d'apres l'image (8 x 4 -> 2 x 1 m)", t)
        rapport(abs(f.get("sy", 0) - 0.4) < 1e-6 and abs(f.get("sx", 0) - 1) < 1e-6 and f.get("image"), f"{titre} : hauteur donnee respectee (1 x 0,4 m)", f)
        rapport(t.get("pos") == [0, 2, -4.98] and abs(f.get("yaw", 0) - 0.5) < 1e-6, f"{titre} : position et orientation de la zone", (t.get("pos"), f.get("yaw")))
        rapport(m.get("visible") is False and not m.get("image"), f"{titre} : image introuvable, rien d'affiche dans la page", m)
    else:
        rapport(z and all(v["visible"] is False and not v["image"] for v in z.values()), f"{titre} : depuis le disque, images refusees, rien d'affiche", z)
    rapport(not errs, f"{titre} : aucune erreur JavaScript", errs)
    await pg.close()


async def viewer(br, port):
    pg = await br.new_page(locale="fr-FR", viewport={"width": 1000, "height": 700}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(f"http://127.0.0.1:{port}/glb-viewer.html")
    await pg.wait_for_function("window.__viewer", timeout=60000)
    await pg.set_input_files("#fGlb", str(tmp / "salle.glb"))
    await pg.wait_for_function("window.__viewer.model", timeout=60000)
    await pg.evaluate("window.__viewer.frame([0, 0.15, 1], [0, 18, -5], 0.5)")
    await pg.wait_for_timeout(600)
    n0 = len(await pg.evaluate("window.__viewer.getZones()"))
    # clic sur le sol : refuse
    await pg.select_option("#zNewType", "image"); await pg.click("#bZoneAdd")
    sx, sy = await pg.evaluate(PROJ, [0, 15, 3])
    await pg.mouse.click(sx, sy); await pg.wait_for_timeout(300)
    zs = await pg.evaluate("window.__viewer.getZones()")
    msg = await pg.evaluate("document.body.innerText")
    rapport(len(zs) == n0 and "Clique sur un mur" in msg, "clic sur le sol : aucune image posee, message", (len(zs), n0))
    # clic sur le mur : pose
    sx, sy = await pg.evaluate(PROJ, [1.0, 18, -5])
    await pg.mouse.click(sx, sy); await pg.wait_for_timeout(400)
    zs = await pg.evaluate("window.__viewer.getZones()")
    z = zs[-1] if len(zs) > n0 else {}
    rapport(z.get("type") == "image" and abs(z["x"] - 1.0) < 0.15 and abs(z["y"] - 18) < 0.15 and abs(z["z"] + 4.98) < 0.01 and abs(z["yaw"]) < 1e-6,
            "clic sur le mur : image a plat, 2 cm devant, tournee vers +z", z)
    rapport(z.get("w") == 1.2 and z.get("h") == 0 and z.get("target") == "", "valeurs par defaut : 1,2 m de large, hauteur d'apres l'image", z)
    # mur tourne : normale vers -x, l'image est tournee de -90 degres et se trouve 2 cm devant
    await pg.evaluate("window.__viewer.frame([-1, 0.15, 0.3], [8, 18, 0], 0.5)"); await pg.wait_for_timeout(600)
    await pg.select_option("#zNewType", "image"); await pg.click("#bZoneAdd")
    sx, sy = await pg.evaluate(PROJ, [8, 18, 0.5])
    await pg.mouse.click(sx, sy); await pg.wait_for_timeout(400)
    zs = await pg.evaluate("window.__viewer.getZones()")
    z = zs[-1] if len(zs) == n0 + 2 else {}
    rapport(z.get("type") == "image" and abs(z["x"] - 7.98) < 0.01 and abs(z["yaw"] + 1.5707963) < 1e-3 and abs(z["z"] - 0.5) < 0.15, "mur tourne : image a plat, orientee d'apres la face (yaw = -90 degres)", z)
    # zone lue dans un fichier, avec son image
    (tmp / "z.json").write_text(json.dumps([{"id": "tab", "type": "image", "label": "Essai", "target": "tableau.png", "x": 0, "y": 18, "z": -4.98, "yaw": 0, "w": 2, "h": 0}]), encoding="utf-8")
    await pg.set_input_files("#fZones", str(tmp / "z.json"))
    await pg.wait_for_function("window.__viewer.getZones().length === 1", timeout=10000)
    await pg.wait_for_function("window.__viewer.scene.children.length > 0", timeout=5000)
    async def plans():
        return await pg.evaluate("""() => { let n = 0, ok = 0; window.__viewer.scene.traverse(o => { if (o.isMesh && o.parent && o.parent.userData.zoneId === 'tab') { n++; if (o.material.map && o.material.map.image && o.material.map.image.width === 8) ok++; } }); return [n, ok]; }""")
    for _ in range(40):
        if (await plans())[1]:
            break
        await pg.wait_for_timeout(250)
    rapport(await plans() == [1, 1], "editeur : la zone image est dessinee avec son image", await plans())
    etiq = await pg.evaluate("""() => { let r = null; window.__viewer.scene.traverse(o => { if (o.isSprite && o.parent && o.parent.userData.zoneId === 'tab') r = [o.material.depthTest, o.renderOrder]; }); return r; }""")
    rapport(etiq == [False, 999], "editeur : l'etiquette de l'image n'est pas coupee par les reliefs du mur (test de profondeur coupe)", etiq)
    sx, sy = await pg.evaluate(PROJ, [0, 18, -4.98])
    await pg.mouse.click(sx, sy); await pg.wait_for_timeout(400)
    sel = await pg.evaluate("document.querySelector('#zoneList details[open] summary') && document.querySelector('#zoneList details[open] summary').textContent")
    rapport(bool(sel) and "Essai" in sel, "editeur : un clic sur l'image la selectionne", sel)
    champs = await pg.evaluate("[...document.querySelectorAll('#zoneList details[open] label')].map(l => l.textContent)")
    rapport(any("Image (nom de fichier" in c for c in champs) and any("0 = d'apr" in c for c in champs) and not any("Rayon" in c or "Confirm" in c for c in champs), "editeur : champs image, largeur, hauteur (0 = auto), sans portee ni confirmation", champs)
    ou = await pg.evaluate("[...document.querySelectorAll('#zoneList details[open] small')].map(s => s.textContent)")
    rapport(any("Cherchée à : http://127.0.0.1:" in t and t.endswith("/tableau.png") for t in ou), "editeur : l'adresse ou l'image est cherchee est affichee sous le champ", ou)
    rapport(not errs, "viewer : aucune erreur JavaScript", errs)
    await pg.close()


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    mur_glb(tmp / "salle.glb"); shutil.copy(tmp / "salle.glb", site / "salle.glb")
    (site / "tableau.png").write_bytes(png(8, 4))
    shutil.copy(DIST / "glb-viewer.html", site / "glb-viewer.html")
    shutil.copytree(DIST / "lib", site / "lib") if (DIST / "lib").exists() else None
    zones = [{"id": "tab", "type": "image", "label": "Essai", "target": "tableau.png", "x": 0, "y": 2, "z": -4.98, "yaw": 0, "w": 2, "h": 0},
             {"id": "fixe", "type": "image", "target": "tableau.png", "x": 3, "y": 2, "z": -4.98, "yaw": 0.5, "w": 1, "h": 0.4},
             {"id": "manque", "type": "image", "target": "absent.png", "x": -3, "y": 2, "z": -4.98, "w": 1, "h": 1}]
    (tmp / "zones.json").write_text(json.dumps(zones), encoding="utf-8")
    out = site / "page.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "salle.glb"), "-o", str(out), "--zones", str(tmp / "zones.json"), "--no-sea", *vend], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    # region dans un sous-dossier (reg/), images a cote du .glb : page du dossier, puis coquille a la racine (?region=reg/salle)
    reg = site / "reg"; reg.mkdir()
    (reg / "reg-only.png").write_bytes(png(8, 4))   # cette image n'existe QUE dans le dossier de la region : la page de la racine ne la trouve pas a cote d'elle
    zr = [dict(z, target="reg-only.png" if z["target"] == "tableau.png" else z["target"]) for z in zones]
    (tmp / "zones_reg.json").write_text(json.dumps(zr), encoding="utf-8")
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "salle.glb"), "-o", str(reg / "salle.html"), "--modular", "--zones", str(tmp / "zones_reg.json"), "--no-sea", *vend], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation modulaire\n{r.stdout}{r.stderr}")
    coquille = (reg / "salle.html").read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1)
    (reg / "salle.html").write_text(coquille, encoding="utf-8")
    (site / "index.html").write_text(coquille, encoding="utf-8")
    shutil.copytree(reg / "lib", site / "lib")
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            await page_exportee(br, f"http://127.0.0.1:{port}/page.html", "page exportee en http", True)
            await page_exportee(br, out.as_uri(), "page exportee ouverte du disque", False)
            await page_exportee(br, f"http://127.0.0.1:{port}/reg/salle.html", "region en sous-dossier, page du dossier", True)
            await page_exportee(br, f"http://127.0.0.1:{port}/index.html?region=reg/salle", "region en sous-dossier, coquille a la racine", True)
            await viewer(br, port)
            await br.close()
    finally:
        proc.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
