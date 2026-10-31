#!/usr/bin/env python3
"""Lien d'un tableau (zone « image », cle facultative link) (Chromium sans tete).

Page exportee en http : un tableau avec lien ouvre sa page au clic et a la touche E (invite « clic ou E : ... ») ; un tableau sans lien ne reagit pas
(ni clic, ni curseur main, ni invite : c'etait le defaut « clic ou E : Image 8 » qui ne faisait rien) ; un lien javascript: est refuse ;
un tableau dont l'image est introuvable n'est pas cliquable ; les zones url gardent leur comportement ; link n'est ecrit que s'il est rempli et est limite a 600 caracteres.
Viewer (editeur de zones) : champ « Lien » pour une zone image, valeur gardee, vide = cle absente.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/lien_image.py
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


PROJ = """([x, y, z]) => { const v = window.__v || window.__viewer; v.camera.updateMatrixWorld(true);
    const p = v.camera.position.clone().set(x, y, z).project(v.camera), r = v.renderer.domElement.getBoundingClientRect();
    return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; }"""
STUB = "window.__opened = []; window.open = (u) => { window.__opened.push(String(u)); return null; };"
LONG = "a" * 700


def image(id_, x, link=None, target="tableau.png", w=1.5, h=0, label="", y=17):
    z = {"id": id_, "type": "image", "label": label, "target": target, "x": x, "y": y, "z": -4.98, "yaw": 0, "w": w, "h": h}
    if link is not None:
        z["link"] = link
    return z


ZONES = [image("avec", 0, "cible.html", label="Essai"), image("sans", 3), image("mauvais", -3, "javascript:window.__pwn=1", label="Piege"),
         image("manque", 6, "cible.html", target="absent.png", w=1, h=1), image("abs", -6, "https://example.org/x", label="Absolu"),
         image("long", 8.5, "http://example.org/" + LONG, w=1),
         {"id": "u", "type": "url", "label": "Lien url", "target": "https://example.org/u", "x": -8, "y": 15, "z": 0, "yaw": 0, "radius": 2}]


async def ouvertes(pg):
    return await pg.evaluate("window.__opened")


async def cliquer(pg, pt):
    await pg.wait_for_timeout(700)   # deux clics rapproches = double-clic (choix du point d'arrivee) : on les espace
    await pg.evaluate("window.__opened.length = 0")
    sx, sy = await pg.evaluate(PROJ, pt)
    await pg.mouse.click(sx, sy); await pg.wait_for_timeout(350)
    return await ouvertes(pg)


async def curseur(pg, pt):
    sx, sy = await pg.evaluate(PROJ, pt)
    await pg.mouse.move(sx - 3, sy - 3); await pg.wait_for_timeout(120)
    await pg.mouse.move(sx, sy); await pg.wait_for_timeout(250)
    return await pg.evaluate("window.__v.renderer.domElement.style.cursor")


async def page_exportee(br, base):
    pg = await br.new_page(locale="fr-FR", viewport={"width": 1500, "height": 700}); errs = []   # large : le panneau d'aide (a gauche) ne couvre pas les tableaux
    await pg.add_init_script(STUB)
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console.error " + m.text) if m.type == "error" and "Failed to load resource" not in m.text and "blocked by CORS" not in m.text else None)
    await pg.goto(base + "/page.html")
    await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
    await pg.wait_for_function("""(() => { let ok = 0; window.__v.scene.traverse(o => { if (o.isMesh && o.parent && o.parent.userData && ['avec', 'sans'].includes(o.parent.userData.zoneId) && o.material.map && o.material.map.image) ok++; }); return ok === 2; })()""", timeout=20000)
    await pg.evaluate("window.__v.frame([0, 0.12, 1], [0, 17, -5], 0.5)")
    await pg.wait_for_timeout(600)
    zs = {z["id"]: z for z in await pg.evaluate("window.__v.getZones()")}
    rapport(zs["avec"].get("link") == "cible.html" and zs["abs"].get("link") == "https://example.org/x", "zones : link relatif et absolu gardes", (zs["avec"].get("link"), zs["abs"].get("link")))
    rapport("link" not in zs["sans"] and "link" not in zs["u"], "zones : pas de cle link quand il est vide (fichiers existants inchanges)", [k for k in ("link",) if k in zs["sans"]])
    rapport(len(zs["long"].get("link", "")) == 600, "zones : link limite a 600 caracteres", len(zs["long"].get("link", "")))
    # clic, curseur (vue globale)
    rapport(await cliquer(pg, [0, 17, -4.98]) == [base + "/cible.html"], "clic sur un tableau avec lien : sa page s'ouvre (onglet, adresse relative a la page)", await ouvertes(pg))
    rapport(await cliquer(pg, [-6, 17, -4.98]) == ["https://example.org/x"], "clic sur un tableau avec lien absolu : l'adresse s'ouvre", await ouvertes(pg))
    rapport(await cursor_ok(pg), "survol : curseur main sur un tableau avec lien, pas sur un tableau sans lien")
    rapport(await cliquer(pg, [3, 17, -4.98]) == [], "clic sur un tableau sans lien : rien ne s'ouvre", await ouvertes(pg))
    rapport(await cliquer(pg, [6, 17, -4.98]) == [], "clic sur un tableau dont l'image est introuvable : rien ne s'ouvre (plan invisible, pas cliquable)", await ouvertes(pg))
    res = await cliquer(pg, [-3, 17, -4.98])
    rapport(res == [] and await pg.evaluate("window.__pwn") is None and "Lien invalide" in await pg.evaluate("document.body.innerText"), "lien javascript: refuse (rien d'execute ni d'ouvert, message « Lien invalide »)", (res, await pg.evaluate("window.__pwn")))
    # promenade : invite et touche E
    await pg.keyboard.press("f"); await pg.wait_for_timeout(900)
    async def invite(x, z):
        await pg.evaluate("([x, z]) => window.__v.teleportTo([x, 15, z], 0)", [x, z]); await pg.wait_for_timeout(700)
        await pg.evaluate("window.__opened.length = 0")
        return await pg.evaluate("[!document.getElementById('zonePrompt').hidden, document.getElementById('zonePrompt').textContent]")
    vis, txt = await invite(0, -2)
    await pg.keyboard.press("e"); await pg.wait_for_timeout(350)
    rapport(vis and txt.startswith("clic ou E :") and "Essai" in txt and await ouvertes(pg) == [base + "/cible.html"], "promenade devant un tableau avec lien : invite « clic ou E : Essai » et E ouvre la page", (vis, txt, await ouvertes(pg)))
    vis, txt = await invite(3, -2)
    await pg.keyboard.press("e"); await pg.wait_for_timeout(350)
    rapport(not vis and await ouvertes(pg) == [], "promenade devant un tableau SANS lien : pas d'invite, E ne fait rien (le defaut d'origine)", (vis, txt, await ouvertes(pg)))
    vis, txt = await invite(6, -2)
    rapport(not vis, "promenade devant un tableau sans image : pas d'invite", (vis, txt))
    vis, txt = await invite(-3, -2)
    await pg.keyboard.press("e"); await pg.wait_for_timeout(350)
    rapport(vis and await ouvertes(pg) == [] and "Lien invalide" in await pg.evaluate("document.body.innerText"), "promenade devant un lien javascript: : invite, mais E refuse le lien", (vis, txt, await ouvertes(pg)))
    vis, txt = await invite(-8, 0)
    await pg.keyboard.press("e"); await pg.wait_for_timeout(350)
    rapport(vis and "Lien url" in txt and await ouvertes(pg) == ["https://example.org/u"], "contre-epreuve : une zone url garde invite et E", (vis, txt, await ouvertes(pg)))
    rapport(not errs, "page exportee : aucune erreur JavaScript", errs)
    await pg.close()


async def cursor_ok(pg):
    a = await curseur(pg, [0, 17, -4.98]); b = await curseur(pg, [3, 17, -4.98])
    ok = a == "pointer" and b != "pointer"
    if not ok:
        print("   curseurs : avec =", repr(a), " sans =", repr(b))
    return ok


async def viewer(br, port):
    pg = await br.new_page(locale="fr-FR", viewport={"width": 1000, "height": 700}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(f"http://127.0.0.1:{port}/glb-viewer.html")
    await pg.wait_for_function("window.__viewer", timeout=60000)
    await pg.set_input_files("#fGlb", str(tmp / "salle.glb"))
    await pg.wait_for_function("window.__viewer.model", timeout=60000)
    await pg.evaluate("window.__viewer.frame([0, 0.15, 1], [0, 18, -5], 0.5)")
    await pg.wait_for_timeout(600)
    (tmp / "z.json").write_text(json.dumps([image("tab", 0, "galerie.html", label="Essai", w=2, y=18), image("nu", 3, w=1, y=18)]), encoding="utf-8")
    await pg.set_input_files("#fZones", str(tmp / "z.json"))
    await pg.wait_for_function("window.__viewer.getZones().length === 2", timeout=10000)
    await pg.wait_for_timeout(800)
    zs = {z["id"]: z for z in await pg.evaluate("window.__viewer.getZones()")}
    rapport(zs["tab"].get("link") == "galerie.html" and "link" not in zs["nu"], "editeur : le lien d'une zone lue dans un fichier est garde (absent sinon)", zs)
    sx, sy = await pg.evaluate(PROJ, [0, 18, -4.98])
    await pg.mouse.click(sx, sy); await pg.wait_for_timeout(400)
    sel = await pg.evaluate("document.querySelector('#zoneList details[open] summary') && document.querySelector('#zoneList details[open] summary').textContent")
    rapport(bool(sel) and "Essai" in sel, "editeur : un clic sur un tableau avec lien le selectionne (il n'ouvre rien)", sel)
    champs = await pg.evaluate("[...document.querySelectorAll('#zoneList details[open] label')].map(l => l.textContent)")
    rapport(any(c.startswith("Lien (page ouverte") for c in champs), "editeur : champ « Lien » dans les champs d'un tableau", champs)
    val = await pg.evaluate("""() => { const l = [...document.querySelectorAll('#zoneList details[open] label')].find(x => x.textContent.startsWith('Lien (page ouverte')); return l ? l.nextSibling.value : null; }""")
    rapport(val == "galerie.html", "editeur : le champ montre le lien de la zone", val)
    champ = pg.locator("#zoneList details[open] .row", has=pg.locator("label", has_text="Lien (page ouverte")).locator("input")
    await champ.fill("autre.html"); await champ.press("Tab"); await pg.wait_for_timeout(400)
    zs = {z["id"]: z for z in await pg.evaluate("window.__viewer.getZones()")}
    rapport(zs["tab"].get("link") == "autre.html", "editeur : saisir un lien l'enregistre dans la zone", zs["tab"].get("link"))
    champ = pg.locator("#zoneList details[open] .row", has=pg.locator("label", has_text="Lien (page ouverte")).locator("input")
    await champ.fill(""); await champ.press("Tab"); await pg.wait_for_timeout(400)
    zs = {z["id"]: z for z in await pg.evaluate("window.__viewer.getZones()")}
    rapport("link" not in zs["tab"], "editeur : vider le champ supprime la cle link", zs["tab"])
    rapport(not errs, "viewer : aucune erreur JavaScript", errs)
    await pg.close()


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    mur_glb(tmp / "salle.glb"); shutil.copy(tmp / "salle.glb", site / "salle.glb")
    (site / "tableau.png").write_bytes(png(8, 4))
    shutil.copy(DIST / "glb-viewer.html", site / "glb-viewer.html")
    shutil.copytree(DIST / "lib", site / "lib") if (DIST / "lib").exists() else None
    (tmp / "zones.json").write_text(json.dumps(ZONES), encoding="utf-8")
    out = site / "page.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "salle.glb"), "-o", str(out), "--zones", str(tmp / "zones.json"), "--no-sea", *vend], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            await page_exportee(br, f"http://127.0.0.1:{port}")
            await viewer(br, port)
            await br.close()
    finally:
        proc.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
