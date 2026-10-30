#!/usr/bin/env python3
"""WebGL indisponible (acceleration materielle coupee, repli logiciel refuse par les navigateurs recents) : un message clair a la place de « Chargement… ».

Chromium sans tete lance sans GPU ni 3D (--disable-gpu --disable-3d-apis --disable-software-rasterizer) : la page de region affiche le message dans #msg
(plus « Chargement… »), le viewer affiche le meme message sur toute la page ; la seule erreur JavaScript est celle de la creation du contexte.
Avec WebGL (rendu logiciel autorise) : la page se charge normalement.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/webgl_absent.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_webgl_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def sol_glb(path):
    pos = struct.pack("<12f", -20, 0, -20, 20, 0, -20, 20, 0, 20, -20, 0, 20)
    blob = pos + struct.pack("<6H", 0, 2, 1, 0, 3, 2) + b"\0\0"
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-20, 0, -20], "max": [20, 0, 20]},
                       {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * (-len(js) % 4)
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


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    sol_glb(tmp / "sol.glb")
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(site / "page.html"), "--no-sea", *vend], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    shutil.copy(DIST / "glb-viewer.html", site / "glb-viewer.html")
    proc, port = serveur(site)
    kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
    try:
        async with async_playwright() as p:
            sans = await p.chromium.launch(args=["--disable-gpu", "--disable-3d-apis", "--disable-software-rasterizer"], **kw)
            for nom, url, lire in (("page de region", f"http://127.0.0.1:{port}/page.html", "document.getElementById('msg').textContent"),
                                   ("viewer", f"http://127.0.0.1:{port}/glb-viewer.html", "document.body.innerText")):
                pg = await sans.new_page(locale="fr-FR"); errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                await pg.goto(url); await pg.wait_for_timeout(3500)
                t = await pg.evaluate(lire)
                rapport("WebGL est indisponible" in t and "Firefox" in t and "--enable-unsafe-swiftshader" in t and "edge://gpu" in t, f"{nom} : message clair sans WebGL", t[:200])
                rapport("Chargement" not in t if nom == "page de region" else True, f"{nom} : plus de « Chargement… »", t[:80])
                rapport(all("WebGL context" in e for e in errs), f"{nom} : seule erreur JavaScript, celle de la creation du contexte", errs)
                await pg.close()
            await sans.close()
            avec = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            pg = await avec.new_page(locale="fr-FR"); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{port}/page.html")
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
            rapport(not errs, "avec WebGL : la page se charge normalement, aucune erreur", errs)
            await avec.close()
    finally:
        proc.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
