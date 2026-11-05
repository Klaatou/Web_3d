#!/usr/bin/env python3
"""Informations / Etat : la ligne « Position avatar » donne aussi le yaw (radians, 2 decimales), meme valeur que celui de « Copier ma position » (Chromium sans tete).

Page exportee (glb2html) servie en http, promenade lancee (F) : pour plusieurs orientations, la ligne finit par « yaw N rad » ; N a deux decimales et egale le yaw de l'adresse
copiee (#pos=x,y,z,yaw) ; un yaw tres proche de zero ne s'ecrit jamais « -0.00 » ; en vue globale la ligne « Position cible » n'a pas de yaw.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/yaw_etat.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, re, shutil, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_yaw_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def sol_glb(path):
    v = [(-20, 0, -20), (20, 0, -20), (20, 0, 20), (-20, 0, 20)]
    pos = b"".join(struct.pack("<3f", *p) for p in v)
    idx = struct.pack("<6H", 0, 2, 1, 0, 3, 2)
    blob = pos + idx
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos)}, {"buffer": 0, "byteOffset": len(pos), "byteLength": len(idx)}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-20, 0, -20], "max": [20, 0, 20]},
                       {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
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


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    sol_glb(tmp / "sol.glb")
    out = site / "page.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--no-sea", *vend], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            pg = await br.new_page(locale="fr-FR")
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{port}/page.html")
            await pg.wait_for_function("window.__v && window.__v.model", timeout=60000)
            await pg.wait_for_timeout(800)
            info = lambda: pg.evaluate("document.getElementById('posInfo').textContent")
            cible = await info()
            rapport(cible.startswith("Position cible (vue globale)") and "yaw" not in cible, "vue globale : « Position cible » sans yaw", cible)
            await pg.keyboard.press("f"); await pg.wait_for_function("window.__v.walking", timeout=10000)
            for yaw in (1.23456, -2.0, 3.14159, 0.0, -0.004, 0.005):
                await pg.evaluate("y => window.__v.teleportTo([3, 0, -4], y)", yaw); await pg.wait_for_timeout(700)
                texte = await info()
                m = re.fullmatch(r"Position avatar : x (-?\d+\.\d) · y (-?\d+\.\d) · z (-?\d+\.\d) m · yaw (-?\d+\.\d\d) rad", texte)
                rapport(bool(m), f"yaw {yaw} : la ligne a le format attendu (yaw a 2 decimales)", texte)
                await pg.evaluate("document.getElementById('linkBtn').click()"); await pg.wait_for_timeout(300)
                lien = await pg.evaluate("document.getElementById('linkOut').value")
                mh = re.search(r"#pos=([^&]+)", lien)
                yl = float(mh[1].split(",")[3]) if mh and len(mh[1].split(",")) == 4 else None
                rapport(bool(m) and yl is not None and abs(float(m[4]) - yl) < 1e-9, f"yaw {yaw} : meme valeur que le yaw de « Copier ma position »", (texte, lien))
                rapport(not (m and m[4].startswith("-") and float(m[4]) == 0), f"yaw {yaw} : jamais « -0.00 »", texte)
            rapport(not errs, "aucune erreur JavaScript", errs)
            await br.close()
    finally:
        proc.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
