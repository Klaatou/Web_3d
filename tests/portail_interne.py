#!/usr/bin/env python3
"""Test du portail interne (v22) : un portail sans destination, ou dont la destination est la page elle-même,
pose l'avatar sur le point d'arrivée de la même région, sans recharger la page.

Prérequis : pip install playwright && playwright install chromium ; python build.py avant.
Variable facultative : THREE_DIR (paquet npm three, hors ligne).
"""
import asyncio, json, os, pathlib, struct, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_portail_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def sol_glb(path):
    # sol plat de 40 x 40 m centré sur l'origine
    pos = struct.pack("<12f", -20, 0, -20, 20, 0, -20, 20, 0, 20, -20, 0, 20)
    blob = pos + struct.pack("<6H", 0, 2, 1, 0, 3, 2) + b"\0\0"
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-20, 0, -20], "max": [20, 0, 20]},
                       {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * ((4 - len(js) % 4) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob))
                     + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def page(name, target):
    # le centre du sol est relevé à 15 m par le cadrage : zones posées à cette hauteur
    zones = [{"id": "loin", "type": "spawn", "x": 12, "y": 15, "z": -12, "yaw": 1.0},
             {"id": "p1", "type": "portal", "label": "Vers loin", "target": target, "spawn": "loin", "trigger": "click",
              "x": 0, "y": 15, "z": 0, "radius": 2}]
    (tmp / f"{name}.zones.json").write_text(json.dumps(zones), encoding="utf-8")
    out = tmp / f"{name}.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out),
                        "--zones", str(tmp / f"{name}.zones.json"), "--no-sea", *vend], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] génération\n{r.stdout}{r.stderr}")
    # accès au viewer pour lire la position de l'avatar
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    return out


async def essai(br, out, titre):
    pg = await br.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(out.as_uri())
    await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
    await pg.keyboard.press("KeyF"); await pg.wait_for_timeout(400)
    invite = await pg.evaluate("document.getElementById('zonePrompt').textContent")
    await pg.evaluate("window.__marque = 1")
    await pg.keyboard.press("KeyE")
    try:
        await pg.wait_for_function("window.__v.getWalk().pos[0] > 6 && document.getElementById('fade').className === ''", timeout=15000)
    except Exception:
        pass
    w = await pg.evaluate("window.__v.getWalk()")
    pos = [round(v, 2) for v in w["pos"]]
    rapport(invite == "E : Vers loin", f"{titre} : le portail est proposé (touche E)", invite)
    rapport(pos == [12, 15, -12] and abs(w["yaw"] - 1.0) < 1e-6, f"{titre} : avatar posé sur l'arrivée, orienté comme elle", (pos, w["yaw"]))
    rapport(await pg.evaluate("window.__marque === 1 && window.__v.walking"), f"{titre} : sans rechargement, toujours en promenade")
    rapport(await pg.evaluate("document.getElementById('fade').className") == "", f"{titre} : fondu retiré")
    rapport(not errs, f"{titre} : aucune erreur JavaScript", errs)
    await pg.close()


async def main():
    from playwright.async_api import async_playwright
    sol_glb(tmp / "sol.glb")
    vide, meme = page("vide", ""), page("meme", "meme.html")
    async with async_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
        br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
        await essai(br, vide, "destination vide")
        await essai(br, meme, "destination = la page elle-même")
        await br.close()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
