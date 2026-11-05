#!/usr/bin/env python3
"""Panneaux, tableaux et légendes de zones : lisibles des deux côtés, sans miroir (Chromium sans tête).

Avant la 1.5.4, un panneau (zone url, forme board), un tableau (zone image) et sa légende étaient UN plan visible des deux côtés (DoubleSide) : vu de derrière, le texte
et l'image étaient en miroir. Maintenant chacun est fait de deux plans dos à dos, chacun visible de son seul côté (FrontSide), le second tourné de 180 degrés.
Vérifie : les deux plans existent (même matière, même forme, normales opposées) ; un clic depuis derrière ouvre le lien comme un clic devant ;
un lien hop:// donne au panneau le sous-titre « Monde virtuel » (autre texture qu'un lien http, identique entre deux liens http) ; aucune erreur JavaScript.

Prérequis : python build.py avant ; pip install playwright. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/double_face.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time, zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_double_"))
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


PROJ = """([x, y, z]) => { const v = window.__v || window.__viewer; v.camera.updateMatrixWorld(true);
    const p = v.camera.position.clone().set(x, y, z).project(v.camera), r = v.renderer.domElement.getBoundingClientRect();
    return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; }"""
STUB = "window.__opened = []; window.open = (u) => { window.__opened.push(String(u)); return null; };"
LONG = "a" * 700



def board(id_, x, target):
    return {"id": id_, "type": "url", "label": "Lien", "target": target, "shape": "board", "trigger": "click", "showName": True,
            "x": x, "y": 15, "z": 6, "yaw": 0, "radius": 2, "w": 2, "h": 1}


HOP = "hop://grid.example.org:8002"
ZONES = [board("b1", 4, "https://example.org/b"), board("b2", 8, HOP), board("b3", 12, "https://example.org/b"),
         {"id": "libre", "type": "image", "label": "", "target": "1-Legende.png", "link": "cible.html", "x": 0, "y": 17, "z": 8, "yaw": 0, "w": 2, "h": 0}]

async def ouvertes(pg):
    return await pg.evaluate("window.__opened")


async def cliquer(pg, pt):
    await pg.wait_for_timeout(700)   # deux clics rapproches = double-clic (choix du point d'arrivee) : on les espace
    await pg.evaluate("window.__opened.length = 0")
    sx, sy = await pg.evaluate(PROJ, pt)
    await pg.mouse.click(sx, sy); await pg.wait_for_timeout(350)
    return await ouvertes(pg)



SCAN = """(id) => { const v = window.__v, out = {}; v.scene.traverse(o => { if (!o.isMesh || !o.parent || o.parent.userData.zoneId !== id || !o.material.map) return; const b = o.userData.bk, V = o.position.constructor;
    out.plane = { tex: o.material.map.image && o.material.map.image.toDataURL ? o.material.map.image.toDataURL() : null, side: o.material.side };
    if (b) { const n1 = o.getWorldDirection(new V()), n2 = b.getWorldDirection(new V()); Object.assign(out.plane, { backSide: b.material.side, sameMat: b.material === o.material, sameGeo: b.geometry === o.geometry, ry: b.rotation.y, dot: n1.dot(n2) }); }
    if (o.userData.cap) { const c = o.userData.cap; out.cap = c.userData.bk ? { side: c.material.side, backSide: c.userData.bk.material.side, ry: c.userData.bk.rotation.y, sameMat: c.userData.bk.material === c.material } : { nobk: true }; }
  }); return out; }"""


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    mur_glb(tmp / "salle.glb"); shutil.copy(tmp / "salle.glb", site / "salle.glb")
    (site / "1-Legende.png").write_bytes(png(8, 4))
    (tmp / "zones.json").write_text(json.dumps(ZONES), encoding="utf-8")
    out = site / "page.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "salle.glb"), "-o", str(out), "--zones", str(tmp / "zones.json"), "--no-sea", *vend], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    proc, port = serveur(site)
    base = f"http://127.0.0.1:{port}"
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            pg = await br.new_page(locale="fr-FR", viewport={"width": 1300, "height": 700}); errs = []
            await pg.add_init_script(STUB)
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append("console.error " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
            await pg.goto(base + "/page.html")
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
            await pg.wait_for_function("""(() => { let ok = 0; window.__v.scene.traverse(o => { if (o.isMesh && o.parent && o.parent.userData.zoneId === 'libre' && o.material.map && o.material.map.image) ok++; }); return ok >= 1; })()""", timeout=30000)
            await pg.wait_for_timeout(500)
            for i in ("b1", "b2", "libre"):
                d = (await pg.evaluate(SCAN, i)).get("plane")
                ok = bool(d) and "dot" in d and d["side"] == 0 and d["backSide"] == 0 and d["sameMat"] and d["sameGeo"] and abs(abs(d["ry"]) - 3.14159265) < 1e-6 and d["dot"] < -0.99
                rapport(ok, f"{i} : deux plans dos à dos, chacun visible de son seul côté, normales opposées", {k: v for k, v in (d or {}).items() if k != "tex"})
            sc = await pg.evaluate(SCAN, "libre")
            rapport(bool(sc.get("cap")) and "side" in sc["cap"] and sc["cap"]["side"] == 0 and sc["cap"]["backSide"] == 0 and sc["cap"]["sameMat"] and abs(abs(sc["cap"]["ry"]) - 3.14159265) < 1e-6, "légende du tableau : deux plans dos à dos aussi", sc.get("cap"))
            t1, t2, t3 = [(await pg.evaluate(SCAN, i))["plane"]["tex"] for i in ("b1", "b2", "b3")]
            rapport(t1 and t2 and t1 != t2, "lien hop:// : le panneau n'a pas le même sous-titre qu'un lien http (« Monde virtuel »)", (bool(t1), bool(t2)))
            rapport(t1 and t1 == t3, "contre-épreuve : deux liens http donnent exactement le même panneau", (bool(t1), bool(t3)))
            for nom, pt, attendu in (("panneau b1", [4, 16.4, 6], "https://example.org/b"), ("tableau avec lien", [0, 17 + 0.0, 8], base + "/cible.html")):
                for cote, cam in (("devant", [0, 0.12, 1]), ("derrière", [0, 0.12, -1])):
                    await pg.evaluate("([c, t]) => window.__v.frame(c, t, 0.3)", [cam, pt]); await pg.wait_for_timeout(600)
                    res = await cliquer(pg, pt)
                    rapport(res == [attendu], f"clic sur le {nom}, vu de {cote} : le lien s'ouvre", res)
            rapport(not errs, "aucune erreur JavaScript", errs)
            await br.close()
    finally:
        proc.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
