#!/usr/bin/env python3
"""Numeros des zones image : case « Numeros des zones image (reperage) » des Reglages de la page exportee (Chromium sans tete).

La case n'existe que si la region a une zone image ; elle est decochee a l'ouverture et jamais memorisee ; cochee, un numero apparait devant chaque zone image
(meme si son image manque), tire du nom de fichier vise (12, 12.jpg, 12-Titre.jpg -> 12 ; paintings/painting-1.jpg -> 1), sinon du nom affiche, sinon de l'id ;
masque par le decor (depthTest) ; decochee, ils disparaissent. Le viewer (editeur) n'en dessine pas.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/zones_numeros.py
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



COUNT = """() => { const out = []; window.__v.scene.traverse(o => { if (o.isMesh && o.userData && o.userData.zoneNum !== undefined) out.push([o.userData.zoneNum, o.material.depthTest, o.material.depthWrite]); }); return out; }"""

PLAT = """() => { const res = []; window.__v.scene.traverse(g => { if (!g.userData || !g.userData.zoneId) return; const n = g.children.find(o => o.userData && o.userData.zoneNum !== undefined); const p = g.children.find(o => o.isMesh && !(o.userData && o.userData.zoneNum !== undefined)); if (!n || !p) return; const a = n.getWorldQuaternion(n.quaternion.clone()), b = p.getWorldQuaternion(p.quaternion.clone()); res.push([n.isSprite === true, Math.abs(a.dot(b))]); }); return res; }"""


def img(id_, x, target, label=""):
    return {"id": id_, "type": "image", "label": label, "target": target, "x": x, "y": 17, "z": -4.98, "yaw": 0, "w": 1.2, "h": 0}


async def ouvrir(br, url, errs):
    pg = await br.new_page(locale="fr-FR", viewport={"width": 1100, "height": 700})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(url)
    await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
    await pg.wait_for_timeout(1500)
    return pg


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    mur_glb(tmp / "salle.glb"); shutil.copy(tmp / "salle.glb", site / "salle.glb")
    (site / "tableau.png").write_bytes(png(8, 4))
    shutil.copy(DIST / "glb-viewer.html", site / "glb-viewer.html")
    zones = [img("a", 0, "12-Titre.jpg"), dict(img("b", 3, "7"), yaw=0.5), img("c", -3, "paintings/painting-1.jpg"), img("d", 6, "", label="Vide"), img("e", -6, "sans-chiffre.png"),
             {"id": "p", "type": "portal", "label": "Porte", "target": "", "x": 8, "y": 15, "z": 0, "yaw": 0, "radius": 2}]
    (tmp / "zones.json").write_text(json.dumps(zones), encoding="utf-8")
    (tmp / "zones_sans.json").write_text(json.dumps([zones[-1]]), encoding="utf-8")
    for nom, zf in (("page", "zones.json"), ("sans", "zones_sans.json")):
        out = site / (nom + ".html")
        r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "salle.glb"), "-o", str(out), "--zones", str(tmp / zf), "--no-sea", *vend], capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
        out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw); errs = []
            base = f"http://127.0.0.1:{port}"
            pg = await ouvrir(br, base + "/page.html", errs)
            rapport(await pg.evaluate("!!document.getElementById('visZoneNums')"), "la case existe quand la region a des zones image")
            rapport(await pg.evaluate("document.getElementById('visZoneNums').checked") is False and await pg.evaluate(COUNT) == [], "decochee a l'ouverture : aucun numero")
            lab = await pg.evaluate("document.getElementById('visZoneNums').closest('label').textContent")
            rapport("zones image" in lab and "tableau" not in lab.lower(), "libelle : « zones image », sans parler de tableaux", lab)
            await pg.evaluate("document.getElementById('visZoneNums').click()"); await pg.wait_for_timeout(500)
            c = await pg.evaluate(COUNT)
            rapport(sorted(x[0] for x in c) == sorted(["12", "7", "1", "Vide", "e"]), "cochee : un numero par zone image (nom de fichier, sinon nom affiche, sinon id) ; pas pour le portail", c)
            rapport(c and all(x[1] is True and x[2] is False for x in c), "numeros masques par le decor (depthTest) et sans ecriture de profondeur", c)
            pl = await pg.evaluate(PLAT)
            rapport(len(pl) == 5 and all(not s and d > 0.9999 for s, d in pl), "numeros a plat : meme orientation que l'image de leur zone, pas d'etiquette tournee vers la camera", pl)
            await pg.evaluate("document.getElementById('visZoneNums').click()"); await pg.wait_for_timeout(400)
            rapport(await pg.evaluate(COUNT) == [], "decochee : les numeros disparaissent")
            await pg.evaluate("document.getElementById('visZoneNums').click()"); await pg.wait_for_timeout(400)
            await pg.close()
            pg = await ouvrir(br, base + "/page.html", errs)
            rapport(await pg.evaluate("document.getElementById('visZoneNums').checked") is False and await pg.evaluate(COUNT) == [], "apres rechargement : decochee, pas memorisee")
            await pg.close()
            pg = await ouvrir(br, base + "/sans.html", errs)
            rapport(await pg.evaluate("!document.getElementById('visZoneNums')"), "region sans zone image : pas de case")
            await pg.close()
            rapport(not errs, "aucune erreur JavaScript", errs)
            await br.close()
    finally:
        proc.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
