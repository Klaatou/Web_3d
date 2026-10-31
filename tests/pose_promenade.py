#!/usr/bin/env python3
"""Pose d'une zone par clic en promenade (viewer, Chromium sans tete).

Avant : en promenade le clic de pose etait ignore (le bouton restait sur « Pose ACTIVE »). Maintenant : zone image posee sur le mur vise par le centre de l'ecran quand la souris
est capturee (capture simulee), ou sous le pointeur sinon ; sans « Pose ACTIVE » un clic en promenade ne pose rien ; en vue globale la pose marche toujours.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/pose_promenade.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time, zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_lien_"))
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
    """sol de 40 x 40 m (normale vers le haut) et un mur de 20 x 6 m en z = -5 (normale vers +z) ; la page exportee releve le modele de 15 m (sol a y = 15) : zones a y = 17"""
    v = [(-20, 0, -20), (20, 0, -20), (20, 0, 20), (-20, 0, 20), (-10, 0, -5), (10, 0, -5), (10, 6, -5), (-10, 6, -5)]
    pos = b"".join(struct.pack("<3f", *p) for p in v)
    idx = struct.pack("<12H", 0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7)
    blob = pos + idx
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos)}, {"buffer": 0, "byteOffset": len(pos), "byteLength": len(idx)}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 8, "type": "VEC3", "min": [-20, 0, -20], "max": [20, 6, 20]},
                       {"bufferView": 1, "componentType": 5123, "count": 12, "type": "SCALAR"}],
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



LOCK = "Object.defineProperty(document, 'pointerLockElement', { configurable: true, get: () => window.__viewer.renderer.domElement })"
UNLOCK = "delete document.pointerLockElement"


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    mur_glb(tmp / "salle.glb")
    shutil.copy(DIST / "glb-viewer.html", site / "glb-viewer.html")
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            pg = await br.new_page(locale="fr-FR", viewport={"width": 1000, "height": 700}); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{port}/glb-viewer.html")
            await pg.wait_for_function("window.__viewer", timeout=60000)
            await pg.set_input_files("#fGlb", str(tmp / "salle.glb"))
            await pg.wait_for_function("window.__viewer.model", timeout=60000)
            await pg.wait_for_timeout(1200)
            await pg.select_option("#zNewType", "image")
            async def zones():
                return await pg.evaluate("window.__viewer.getZones()")
            async def label():
                return await pg.evaluate("document.getElementById('bZoneAdd').textContent")
            async def armer():
                if "ACTIVE" not in await label():
                    await pg.click("#bZoneAdd"); await pg.wait_for_timeout(200)
            async def clic(x, y):
                await pg.mouse.move(x, y); await pg.mouse.down(); await pg.mouse.up(); await pg.wait_for_timeout(600)
            async def clic_capture():
                """souris capturee : le pointeur est place AVANT la capture (un deplacement capture fait tourner la camera), puis clic sans bouger ; on remet la camera face au mur"""
                await pg.mouse.move(5, 5); await pg.wait_for_timeout(100)
                await pg.evaluate("window.__viewer.teleportTo([0, 15, -1], %s)" % yaw); await pg.wait_for_timeout(700)
                await pg.evaluate(LOCK)
                await pg.mouse.down(); await pg.mouse.up(); await pg.wait_for_timeout(600)
                await pg.evaluate(UNLOCK)
            # ---- vue globale : la pose marche toujours (contre-epreuve)
            await pg.evaluate("window.__viewer.frame([0, 0.15, 1], [0, 18, -5], 0.5)"); await pg.wait_for_timeout(700)
            await armer(); await clic(500, 350)
            zs = await zones()
            rapport(len(zs) == 1 and zs[0]["type"] == "image" and abs(zs[0]["z"] + 4.98) < 0.02, "vue globale : la pose par clic marche", zs)
            await pg.evaluate("window.__viewer.setZones([])"); await pg.wait_for_timeout(300)
            # ---- promenade
            await pg.keyboard.press("f"); await pg.wait_for_function("window.__viewer.walking", timeout=10000)
            await pg.evaluate("window.__viewer.teleportTo([0, 15, -1], 0)"); await pg.wait_for_timeout(900)
            dz = await pg.evaluate("(() => { const c = window.__viewer.camera, v = c.position.clone(); c.getWorldDirection(v); return v.z; })()")
            yaw = "0"
            if dz > 0:
                yaw = "Math.PI"
                await pg.evaluate("window.__viewer.teleportTo([0, 15, -1], Math.PI)"); await pg.wait_for_timeout(900)
            dz = await pg.evaluate("(() => { const c = window.__viewer.camera, v = c.position.clone(); c.getWorldDirection(v); return v.z; })()")
            rapport(dz < -0.5, "promenade : la camera regarde le mur", dz)
            if "ACTIVE" in await label():
                await pg.click("#bZoneAdd")
            await clic_capture()
            rapport(len(await zones()) == 0, "promenade, sans « Pose ACTIVE » : un clic ne pose rien", await zones())
            await armer()
            rapport("ACTIVE" in await label(), "promenade : le bouton est en « Pose ACTIVE »", await label())
            await clic_capture()   # souris capturee : clientX/clientY ne bougent pas, on vise le centre de l'ecran
            zs = await zones()
            z = zs[0] if zs else {}
            rapport(len(zs) == 1 and z.get("type") == "image" and abs(z["z"] + 4.98) < 0.02 and abs(z["x"]) < 0.8 and abs(z["yaw"]) < 1e-3, "promenade, souris capturee : la zone image se pose sur le mur vise (centre de l'ecran)", zs)
            rapport("ACTIVE" not in await label(), "promenade : le bouton revient a l'etat normal apres la pose", await label())
            await pg.evaluate("window.__viewer.setZones([])"); await pg.wait_for_timeout(300)
            await armer()
            await clic(500, 350)   # souris libre : sous le pointeur
            zs = await zones()
            rapport(len(zs) == 1 and zs[0]["type"] == "image", "promenade, souris libre : la zone se pose sous le pointeur", zs)
            rapport(not errs, "viewer : aucune erreur JavaScript", errs)
            await br.close()
    finally:
        proc.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
