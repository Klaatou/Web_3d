#!/usr/bin/env python3
"""Tests v24 : les liens se comportent comme sur le web.

  - page exportée (modulaire ET autonome) : aucun mesh de cylindre ; zone liée = aucun objet ajouté ;
    zone non liée = petit marqueur plat au sol ; infobulle au survol avec la destination exacte ; curseur main ;
    option « Toujours afficher le nom » (panneau permanent seulement si cochée) ;
  - viewer (édition) : cylindres toujours visibles pour toutes les zones, y compris les panneaux.

Prérequis : pip install playwright ; python build.py avant.
Variables facultatives : THREE_DIR (paquet npm three, hors ligne), CHROMIUM (chemin de l'exécutable).
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"   # outils Python en français (v36)
import asyncio, json, os, pathlib, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_v24_"))
site = tmp / "site"
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


def run(*a):
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), *map(str, a), *vend], capture_output=True, text=True, cwd=tmp)
    if r.returncode:
        sys.exit(f"[ECHEC] {' '.join(map(str, a))}\n{r.stdout}{r.stderr}")


# ---------- petit modèle de test : sol, une boîte, un voile traversable (nom « door… » = walkIgnore par défaut) devant la boîte
def make_glb(path, objets, racine=None):
    """objets : [(nom, matériau, (x0, y0, z0, x1, y1, z1), alpha)] -> GLB avec un nœud et un mesh par objet.
    racine : (translation, échelle) -> les objets deviennent les enfants d'un nœud « racine » décalé et mis à l'échelle."""
    idx_box = [0, 1, 3, 0, 3, 2, 4, 6, 7, 4, 7, 5, 0, 4, 5, 0, 5, 1, 2, 3, 7, 2, 7, 6, 0, 2, 6, 0, 6, 4, 1, 5, 7, 1, 7, 3]
    binb, views, accs, meshes, nodes, mats = b"", [], [], [], [], []
    for i, (nom, mat, (x0, y0, z0, x1, y1, z1), alpha) in enumerate(objets):
        verts = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        pos = b"".join(struct.pack("<3f", *v) for v in verts)
        ind = struct.pack("<36H", *idx_box)
        views.append({"buffer": 0, "byteOffset": len(binb), "byteLength": len(pos), "target": 34962}); binb += pos
        accs.append({"bufferView": len(views) - 1, "componentType": 5126, "count": 8, "type": "VEC3", "min": [x0, y0, z0], "max": [x1, y1, z1]})
        views.append({"buffer": 0, "byteOffset": len(binb), "byteLength": len(ind), "target": 34963}); binb += ind
        accs.append({"bufferView": len(views) - 1, "componentType": 5123, "count": 36, "type": "SCALAR"})
        m = {"name": mat, "doubleSided": True, "pbrMetallicRoughness": {"baseColorFactor": [0.6, 0.6, 0.6, alpha], "metallicFactor": 0}}
        if alpha < 1:
            m["alphaMode"] = "BLEND"
        mats.append(m)
        meshes.append({"name": nom, "primitives": [{"attributes": {"POSITION": len(accs) - 2}, "indices": len(accs) - 1, "material": i}]})
        nodes.append({"name": nom, "mesh": i})
    tops = list(range(len(nodes)))
    if racine:
        nodes.append({"name": "racine", "translation": list(racine[0]), "scale": [racine[1]] * 3, "children": tops})
        tops = [len(nodes) - 1]
    gltf = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": tops}], "nodes": nodes, "meshes": meshes,
            "materials": mats, "accessors": accs, "bufferViews": views, "buffers": [{"byteLength": len(binb)}]}
    js = json.dumps(gltf).encode()
    js += b" " * (-len(js) % 4)
    binb += b"\0" * (-len(binb) % 4)
    total = 12 + 8 + len(js) + 8 + len(binb)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(binb), b"BIN\0") + binb)



tmp.mkdir(exist_ok=True)
make_glb(tmp / "boite.glb", [("sol", "sol", (-12, -0.2, -12, 12, 0, 12), 1.0), ("boite", "mur", (4, 0, -2, 8, 4, 2), 1.0)])

URL_L, URL_M, URL_N = "https://exemple.org/lien?a=1&b=2", "https://exemple.org/sol", "https://exemple.org/nom"
ZONES = [
    {"id": "lie", "type": "url", "label": "Boîte liée", "target": URL_L, "mesh": "boite", "radius": 4},
    {"id": "sol", "type": "url", "label": "Lien au sol", "target": URL_M, "x": -3, "y": 15, "z": 3, "radius": 2},
    {"id": "pan", "type": "url", "label": "Ancien panneau", "target": "https://exemple.org/pan", "shape": "board", "x": -6, "y": 15, "z": 3, "radius": 2},
    {"id": "nom", "type": "url", "label": "Nom permanent", "target": URL_N, "x": 0, "y": 15, "z": 7, "radius": 2, "showName": True},
    {"id": "ha", "type": "ha", "label": "Lumière salon", "target": "http://homeassistant.local:8123/api/webhook/secret", "x": 3, "y": 15, "z": 6, "radius": 2},
    {"id": "por", "type": "portal", "label": "Portail", "trigger": "click", "target": "https://autre.example/region.html", "spawn": "quai", "x": -3, "y": 15, "z": 7, "radius": 2},
    {"id": "arr", "type": "spawn", "label": "Arrivée", "x": 0, "y": 15, "z": 0},
    {"id": "cache", "type": "url", "label": "Sous le sol", "target": "https://exemple.org/cache", "x": 6, "y": 0, "z": 4},
]
(tmp / "z.json").write_text(json.dumps(ZONES), encoding="utf-8")
run(tmp / "boite.glb", "-o", site / "mod.html", "--modular", "--zones", tmp / "z.json", "--profile", "perso", "--no-sea")
run(tmp / "boite.glb", "-o", site / "auto.html", "--zones", tmp / "z.json", "--profile", "perso", "--no-sea")
STUB = "try { localStorage.setItem('glb2html_help', '0'); } catch (e) {} window.__opened = []; window.open = (...a) => { window.__opened.push(String(a[0])); return null; };"

SCAN = """(() => {
  const v = window.__viewer, o = { cyl: 0, circles: 0, planes: 0, sprites: 0 };
  v.scene.traverse(n => { if (n.isSprite && n.parent && n.parent.userData.zoneId) o.sprites++; const t = n.geometry && n.geometry.type; if (!n.isMesh || !t) return;
    if (t === 'CylinderGeometry') o.cyl++; if (t === 'CircleGeometry') o.circles++; if (t === 'PlaneGeometry') o.planes++; });
  const zg = v.scene.children.filter(c => c.children.some(k => k.userData && k.userData.zoneId));
  o.groups = zg.length ? Object.fromEntries(zg[0].children.map(g => [g.userData.zoneId, g.children.length])) : {};
  return o; })()"""
# position écran d'un point monde
PROJ = """([x, y, z]) => { const v = window.__viewer; v.camera.updateMatrixWorld(true); const p = new v.camera.position.constructor(x, y, z).project(v.camera);
  const r = v.renderer.domElement.getBoundingClientRect(); return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; }"""
def serveur(dossier):
    with socket.socket() as so:
        so.bind(("127.0.0.1", 0))
        port = so.getsockname()[1]
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=dossier, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return proc, port
        except OSError:
            time.sleep(0.1)
    proc.kill()
    sys.exit("[ECHEC] http.server ne démarre pas")




async def tip(pg):
    return await pg.evaluate("(() => { const e = document.getElementById('zoneTip'); return e && !e.hidden ? e.innerText : null; })()")


async def sur(pg, pos):
    pt = await pg.evaluate(PROJ, pos)
    await pg.mouse.move(*pt)
    await pg.wait_for_timeout(150)
    await pg.mouse.move(pt[0] + 1, pt[1])
    await pg.wait_for_timeout(150)
    return pt, await pg.evaluate("document.querySelector('canvas').style.cursor"), await tip(pg)


async def verifier(br, url, etiquette):
    ctx = await br.new_context(locale="fr-FR", viewport={"width": 1000, "height": 700})
    await ctx.add_init_script(STUB)
    pg = await ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(url)
    await pg.wait_for_function("document.getElementById('msg') === null", timeout=20000)
    await pg.wait_for_timeout(800)
    # vue d'ensemble de dessus pour que tous les points soient visibles
    await pg.evaluate("(() => { const v = window.__viewer; v.camera.position.set(0, 41, 22); v.controls.target.set(0, 15, 2); v.controls.update(); v.camera.updateMatrixWorld(true); })()")
    await pg.wait_for_timeout(300)
    sc = await pg.evaluate(SCAN)
    rapport(sc["cyl"] == 0, f"{etiquette} : aucun mesh de cylindre dans la page exportée", sc)
    rapport(sc["planes"] == 0 or sc["groups"].get("pan", 0) <= 1, f"{etiquette} : l'ancien panneau (forme board) n'est plus dessiné sans l'option", sc)
    rapport("lie" not in sc["groups"], f"{etiquette} : zone liée à un élément = aucun objet ajouté", sc["groups"])
    rapport(sc["circles"] >= 6, f"{etiquette} : marqueurs plats au sol pour les zones non liées", sc)
    rapport(sc["sprites"] == 1, f"{etiquette} : un seul nom permanent, celui de la zone cochée « Toujours afficher le nom »", sc)

    # survol : zone liée (curseur + infobulle exacte)
    haut = await pg.evaluate("window.__viewer.meshInfo('boite')")
    centre = [haut["center"][0], haut["center"][1] + haut["size"][1] / 2, haut["center"][2]]
    _, cur, t = await sur(pg, centre)
    rapport(cur == "pointer" and t is not None and t.split("\n")[0] == "Boîte liée" and t.split("\n")[1] == URL_L, f"{etiquette} : survol de l'élément lié : main + infobulle (nom, adresse exacte)", (cur, t))
    # survol : marqueur au sol (lien, portail, commande)
    for ident, pos, attendu in [("sol", [-3, 15.04, 3], ("Lien au sol", URL_M)), ("nom", [0, 15.04, 7], ("Nom permanent", URL_N)),
                                ("ha", [3, 15.04, 6], ("Lumière salon", "Commande : Lumière salon")),
                                ("por", [-3, 15.04, 7], ("Portail", "Région : https://autre.example/region.html #quai")),
                                ("pan", [-6, 15.04, 3], ("Ancien panneau", "https://exemple.org/pan"))]:
        _, cur, t = await sur(pg, pos)
        rapport(cur == "pointer" and t is not None and tuple(t.split("\n")) == attendu, f"{etiquette} : survol du marqueur « {ident} » : main + infobulle", (cur, t))
    rapport("secret" not in (t or "") and "homeassistant" not in await pg.evaluate("document.getElementById('zoneTip').innerText"), f"{etiquette} : l'infobulle d'une commande n'affiche pas le webhook")
    # contre-épreuve : un marqueur caché sous le sol n'est pas survolé (le relief le masque)
    _, cur, t = await sur(pg, [6, 0.04, 4])
    rapport(cur != "pointer" and t is None, f"{etiquette} : marqueur masqué par le relief : ni main ni infobulle", (cur, t))
    # hors zone : plus d'infobulle, curseur normal
    await pg.mouse.move(12, 12)
    await pg.wait_for_timeout(150)
    await pg.mouse.move(14, 12)
    await pg.wait_for_timeout(150)
    rapport(await tip(pg) is None and await pg.evaluate("document.querySelector('canvas').style.cursor") != "pointer", f"{etiquette} : hors zone, infobulle masquée et curseur normal")
    # clic = suivre le lien
    await pg.evaluate("window.__opened.length = 0")
    pt, _, _ = await sur(pg, [-3, 15.04, 3])
    await pg.mouse.click(*pt)
    await pg.wait_for_timeout(300)
    rapport(await pg.evaluate("window.__opened") == [URL_M], f"{etiquette} : clic sur le marqueur = ouvre le lien", await pg.evaluate("window.__opened"))
    await pg.evaluate("window.__opened.length = 0")
    pt, _, _ = await sur(pg, centre)
    await pg.mouse.click(*pt)
    await pg.wait_for_timeout(300)
    rapport(await pg.evaluate("window.__opened") == [URL_L], f"{etiquette} : clic sur l'élément lié = ouvre le lien")
    rapport(not errs, f"{etiquette} : aucune erreur JavaScript", errs)
    await ctx.close()


async def viewer_edition(br):
    ctx = await br.new_context(locale="fr-FR", viewport={"width": 1300, "height": 800})
    pg = await ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto((DIST / "glb-viewer.html").as_uri())
    await pg.set_input_files("#fGlb", str(tmp / "boite.glb"))
    await pg.wait_for_function("!document.getElementById('bZip').disabled", timeout=20000)
    await pg.select_option("#profileSel", "perso")
    await pg.set_input_files("#fZones", str(tmp / "z.json"))
    await pg.wait_for_timeout(500)
    sc = await pg.evaluate(SCAN)
    # sol, pan, nom, ha, por : cylindres ; lie (liée) : contour ; arr : cône
    rapport(sc["cyl"] == 6, "viewer : un cylindre pour chaque zone non liée (panneaux compris), toujours visible", sc)
    rapport(await pg.evaluate("document.querySelector('canvas').style.cursor") != "pointer" and await tip(pg) is None, "viewer : pas d'infobulle en édition")
    # « Toujours afficher le nom » : décochée pour la zone « sol », cochée pour la zone « nom », modifiable
    boite = lambda i: pg.locator("#zoneList details").nth(i).get_by_text("Toujours afficher le nom").locator("xpath=following-sibling::input[1]")
    for i in (1, 3):
        await pg.locator("#zoneList details").nth(i).locator("summary").click()
    rapport(not await boite(1).is_checked() and await boite(3).is_checked(), "viewer : « Toujours afficher le nom » : décochée par défaut, cochée si la zone le demande")
    await boite(1).check()
    await pg.wait_for_timeout(200)
    rapport((await pg.evaluate("window.__viewer.getZones()[1].showName")) is True, "viewer : cocher l'option la conserve dans la zone")
    await ctx.close()
    rapport(not errs, "viewer : aucune erreur JavaScript", errs)




async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        proc, port = serveur(site)
        try:
            await verifier(br, f"http://127.0.0.1:{port}/mod.html", "modulaire")
            await verifier(br, (site / "auto.html").as_uri(), "autonome")
            await viewer_edition(br)
        finally:
            proc.kill()
            await br.close()


asyncio.run(main())
print("\nRÉSULTAT :", "ÉCHEC (%d)" % bad if bad else "tout est passé")
sys.exit(1 if bad else 0)
