#!/usr/bin/env python3
"""Editeur de zones du viewer : menus « Declenchement » (trigger) et « Repere (cone) » (cone) d'une zone url (Chromium sans tete).

Viewer (glb-viewer.html) : une zone url ouverte dans la liste, un menu change le declenchement (enter, click, both), l'autre le cone
(auto : cle absente, on : cone true, off : cone false) ; les valeurs sont gardees dans la zone (getZones). Le viewer n'affiche jamais
les cones (mode editeur, voulu depuis la v36) : on le verifie. Bout en bout : les zones sorties de l'editeur sont donnees a glb2html.py,
la page generee montre le cone de la zone « click + on » et pas celui de la zone « enter + off » ; « click + auto » n'en a pas,
« enter + auto » en a un.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/editeur_cone.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_edcone_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def sol_glb(path):
    """sol de 40 x 40 m (normale vers le haut)"""
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


def zone(id_, x, trigger="click", **plus):
    z = {"id": id_, "type": "url", "label": id_, "shape": "ring", "trigger": trigger, "target": "https://example.org", "x": x, "y": 17, "z": 0, "radius": 2}
    z.update(plus)
    return z


def generer(site, nom, zones):
    (tmp / (nom + ".json")).write_text(json.dumps(zones), encoding="utf-8")
    out = site / (nom + ".html")
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--zones", str(tmp / (nom + ".json")), "--no-sea", *vend],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    sol_glb(tmp / "sol.glb"); shutil.copy(tmp / "sol.glb", site / "sol.glb")
    shutil.copy(DIST / "glb-viewer.html", site / "glb-viewer.html")
    generer(site, "vide", [])                                  # fabrique aussi lib\ a cote des pages
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            pg = await br.new_page(locale="fr-FR", viewport={"width": 1000, "height": 700}); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{port}/glb-viewer.html")
            await pg.wait_for_function("window.__viewer", timeout=60000)
            await pg.set_input_files("#fGlb", str(tmp / "sol.glb"))
            await pg.wait_for_function("window.__viewer.model", timeout=60000)
            (tmp / "z.json").write_text(json.dumps([zone("a", 0), zone("b", 6), zone("c", -6), zone("d", 12)]), encoding="utf-8")
            await pg.set_input_files("#fZones", str(tmp / "z.json"))
            await pg.wait_for_function("window.__viewer.getZones().length === 4", timeout=10000)
            await pg.wait_for_timeout(600)

            async def regler(i, trig, cone):
                """ouvre la zone i par un clic sur son titre (comme l'utilisateur), puis regle les deux menus"""
                if not await pg.evaluate("document.querySelectorAll('#zoneList details')[%d].open" % i):
                    await pg.locator("#zoneList details summary").nth(i).click(); await pg.wait_for_timeout(500)
                d = pg.locator("#zoneList details").nth(i)           # la zone i seulement : ouvrir une zone ne ferme pas les autres avant le prochain rendu
                t = d.locator("select").filter(has=pg.locator("option[value=both]"))
                await t.select_option(trig); await pg.wait_for_timeout(500)
                c = d.locator("select").filter(has=pg.locator("option[value=auto]"))
                await c.select_option(cone); await pg.wait_for_timeout(500)

            await regler(0, "click", "on")
            await regler(1, "enter", "off")
            await regler(2, "click", "auto")
            await regler(3, "enter", "auto")
            zs = {z["id"]: z for z in await pg.evaluate("window.__viewer.getZones()")}
            rapport(zs["a"]["trigger"] == "click" and zs["a"].get("cone") is True, "editeur : « au clic » + cone « toujours » : trigger click, cone true", zs["a"])
            rapport(zs["b"]["trigger"] == "enter" and zs["b"].get("cone") is False, "editeur : « en marchant dedans » + cone « jamais » : trigger enter, cone false", zs["b"])
            rapport(zs["c"]["trigger"] == "click" and "cone" not in zs["c"], "editeur : cone « selon le declenchement » : cle cone absente", zs["c"])
            rapport(zs["d"]["trigger"] == "enter" and "cone" not in zs["d"], "editeur : « en marchant dedans » + cone auto : cle cone absente", zs["d"])
            await regler(0, "both", "auto")
            za = (await pg.evaluate("window.__viewer.getZones()"))[0]
            rapport(za["trigger"] == "both" and "cone" not in za, "editeur : « les deux » enregistre ; repasser le cone sur auto retire la cle (sens inverse)", za)
            await regler(0, "click", "on")
            n = await pg.evaluate("window.__viewer.getCones().length")
            rapport(n == 0, "editeur : aucun cone affiche dans le viewer (mode editeur, voulu)", n)
            sortie = await pg.evaluate("window.__viewer.getZones()")
            rapport(not errs, "viewer : aucune erreur JavaScript", errs)
            await pg.close()

            generer(site, "sortie", sortie)
            p2 = await br.new_page(viewport={"width": 1000, "height": 700}); e2 = []
            p2.on("pageerror", lambda e: e2.append(str(e)))
            await p2.goto(f"http://127.0.0.1:{port}/sortie.html")
            await p2.wait_for_function("window.__v && window.__v.model", timeout=60000)
            await p2.wait_for_timeout(1500)
            ids = sorted(c["id"] for c in await p2.evaluate("window.__v.getCones()"))
            rapport(ids == ["a", "d"], "page generee : cone sur a (click + on) et d (enter + auto) ; pas sur b (enter + off) ni c (click + auto)", ids)
            rapport(not e2, "page generee : aucune erreur JavaScript", e2)
            await br.close()
    finally:
        proc.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
