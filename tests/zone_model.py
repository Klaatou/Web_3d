#!/usr/bin/env python3
"""Zone « model » (1.12.39) : un fichier .glb pose a part, avec position, cap (yaw), inclinaisons (pitch, roll), taille (scale) et option solid (Chromium sans tete).

Page exportee (glb2html --zones) servie en http : le modele de zone se charge a moins de modelLazy metres (150), pas au-dela ; --model-lazy 0 charge tout au depart ;
taille, cap, pitch et roll sont appliques ; un fichier introuvable ne laisse rien et ne casse rien ; un modele avec un lien est cliquable ;
solid : on ne traverse pas le modele, sans solid on le traverse ; au plus 16 modeles charges quand la distance compte (le plus loin est libere).
Viewer (glb-viewer.html) : type « Modele 3D » dans la liste, champs fichier, taille, inclinaisons, solide ; la zone ecrite au format du fichier (model, scale, pitch, roll, solid).

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/zone_model.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_model_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def ecrire_glb(path, v, idx, nom):
    pos = b"".join(struct.pack("<3f", *p) for p in v)
    ib = struct.pack("<%dH" % len(idx), *idx)
    blob = pos + ib
    mn = [min(p[k] for p in v) for k in range(3)]; mx = [max(p[k] for p in v) for k in range(3)]
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos)}, {"buffer": 0, "byteOffset": len(pos), "byteLength": len(ib)}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": len(v), "type": "VEC3", "min": mn, "max": mx},
                       {"bufferView": 1, "componentType": 5123, "count": len(idx), "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": nom}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * (-len(js) % 4)
    blob += bytes(-len(blob) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js
                     + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def sol_glb(path):
    """sol plat de 60 x 60 m, normale vers le haut"""
    ecrire_glb(path, [(-30, 0, -30), (30, 0, -30), (30, 0, 30), (-30, 0, 30)], [0, 2, 1, 0, 3, 2], "sol")


def cube_glb(path):
    """pilier de 1 x 2 x 1 m, origine au milieu du pied"""
    v = [(-.5, 0, -.5), (.5, 0, -.5), (.5, 0, .5), (-.5, 0, .5), (-.5, 2, -.5), (.5, 2, -.5), (.5, 2, .5), (-.5, 2, .5)]
    idx = [0, 1, 2, 0, 2, 3, 4, 6, 5, 4, 7, 6, 0, 4, 5, 0, 5, 1, 1, 5, 6, 1, 6, 2, 2, 6, 7, 2, 7, 3, 3, 7, 4, 3, 4, 0]
    ecrire_glb(path, v, idx, "pilier")


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


# le modele de la region est recentre : le sol est a y = 15 dans le repere de la page (voir REPRISE, « Mer »)
# etat d'une zone model : groupe de la zone, son « hold » (premier enfant) : nombre de meshes charges, echelle, rotation
LIRE = """() => { const out = {}; window.__v.scene.traverse(o => { if (o.userData && o.userData.zoneId && o.children.length) {
    const h = o.children[0]; let n = 0; h.traverse(q => { if (q.isMesh) n++; });
    out[o.userData.zoneId] = { meshes: n, s: h.scale.x, rx: h.rotation.x, ry: h.rotation.y, rz: h.rotation.z, pos: o.position.toArray() }; } }); return out; }"""
PROJ = """([x, y, z]) => { const v = window.__v; v.camera.updateMatrixWorld(true);
    const p = v.camera.position.clone().set(x, y, z).project(v.camera), r = v.renderer.domElement.getBoundingClientRect();
    return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; }"""

ZONES = [
    {"id": "deco", "model": "pilier.glb", "pos": [8, 15, 8], "yaw": 0.5, "scale": 2, "pitch": 0.25, "roll": -0.25},
    {"id": "lien", "model": "pilier.glb", "link": "https://example.org/", "x": -4, "y": 15, "z": 6, "radius": 3},
    {"id": "loin", "model": "pilier.glb", "x": 900, "y": 15, "z": 900},
    {"id": "radio", "model": "pilier.glb", "radio": [["Test", "http://127.0.0.1:9/flux"]], "x": -10, "y": 15, "z": 6, "radius": 6},
    {"id": "musique", "model": "pilier.glb", "music": "audio", "x": 12, "y": 15, "z": 6, "radius": 6},
    {"id": "rate", "model": "absent.glb", "x": 0, "y": 15, "z": 12},
    {"id": "mur", "model": "pilier.glb", "x": 0, "y": 15, "z": -2, "scale": 3, "solid": True},
    {"id": "fantome", "model": "pilier.glb", "x": 6, "y": 15, "z": -2, "scale": 3},
]


async def ouvrir(br, url, errs):
    pg = await br.new_page(locale="fr-FR", viewport={"width": 900, "height": 600})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console.error " + m.text) if m.type == "error" and "Failed to load resource" not in m.text and "404" not in m.text else None)
    await pg.goto(url)
    await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
    return pg


async def attendre(pg, ids, delai=15000):
    cond = "(() => { const z = (" + LIRE + ")(); return " + " && ".join(f"z['{i}'] && z['{i}'].meshes > 0" for i in ids) + "; })()"
    await pg.wait_for_function(cond, timeout=delai)


async def marcher(pg, x, z, touche, duree):
    """promenade : place le visiteur en (x, 0, z), cap vers -z, avance (touche W) pendant `duree` ms ; rend sa position finale"""
    if not await pg.evaluate("window.__v.walking"):
        await pg.evaluate("window.__v.toggleWalk()")
        await pg.wait_for_function("window.__v.walking", timeout=10000)
    await pg.evaluate("([x, z]) => window.__v.teleportTo([x, 15, z], 0)", [x, z])
    await pg.wait_for_timeout(400)
    await pg.keyboard.down(touche); await pg.wait_for_timeout(duree); await pg.keyboard.up(touche)
    await pg.wait_for_timeout(300)
    return await pg.evaluate("window.__v.getWalk().pos")


async def page_exportee(br, port):
    errs = []
    pg = await ouvrir(br, f"http://127.0.0.1:{port}/page.html", errs)
    await attendre(pg, ["deco", "lien", "mur", "fantome", "radio", "musique"])
    z = await pg.evaluate("(" + LIRE + ")()")
    d = z.get("deco", {})
    rapport(d.get("meshes") == 1 and abs(d["s"] - 2) < 1e-6 and abs(d["rx"] - 0.25) < 1e-6 and abs(d["ry"] - 0.5) < 1e-6 and abs(d["rz"] + 0.25) < 1e-6 and d["pos"] == [8, 15, 8],
            "page exportee : modele charge, taille 2, cap 0,5, pitch 0,25, roll -0,25, position [8, 15, 8] (pos)", d)
    rapport(z.get("loin", {}).get("meshes") == 0, "page exportee : un modele a 1 km n'est pas charge (modelLazy 150 m)", z.get("loin"))
    rapport(z.get("rate", {}).get("meshes") == 0, "page exportee : fichier introuvable, rien d'affiche", z.get("rate"))
    rapport(not errs, "page exportee : aucune erreur JavaScript", errs)
    # clic sur le modele porteur d'un lien : la zone se declenche
    await pg.evaluate("window.__v.toggleWalk()")
    await pg.wait_for_function("window.__v.walking", timeout=10000)
    await pg.evaluate("window.__v.teleportTo([-4, 15, 9], 0)")
    await pg.wait_for_timeout(600)
    await pg.evaluate("window.__fired = []; window.__v.onZone = (z, how) => window.__fired.push([z.id, how]); 0")
    sx, sy = await pg.evaluate(PROJ, [-4, 16, 6])
    await pg.mouse.move(sx, sy); await pg.wait_for_timeout(200)
    await pg.mouse.click(sx, sy); await pg.wait_for_timeout(700)
    fired = await pg.evaluate("window.__fired")
    rapport(any(f[0] == "lien" for f in fired), "page exportee : un clic sur le modele d'une zone « link » la declenche", fired)
    # 1.12.40 : le modele d'une radio ou d'une musique est cliquable comme son cone (ouvre / ferme la fenetre Son)
    for zid, cx in (("radio", -10), ("musique", 12)):
        await pg.evaluate(f"window.__v.teleportTo([{cx}, 15, 9], 0)")
        await pg.wait_for_timeout(600)
        await pg.evaluate("window.__fired = []; 0")
        sx, sy = await pg.evaluate(PROJ, [cx, 16, 6])
        await pg.mouse.move(sx, sy); await pg.wait_for_timeout(200)
        await pg.mouse.click(sx, sy); await pg.wait_for_timeout(700)
        fired = await pg.evaluate("window.__fired")
        rapport(any(f[0] == zid for f in fired), f"page exportee : un clic sur le modele d'une zone « {zid} » la declenche (fenetre Son)", fired)
    await pg.evaluate("window.__v.toggleWalk()")
    # solid : on ne traverse pas ; sans solid on traverse (depart a z = 4, vers -z ; le pilier solide occupe z de -3,5 a -0,5)
    arret = await marcher(pg, 0, 4, "KeyW", 3500)
    rapport(arret[2] > -0.3, "solid : le visiteur s'arrete devant le modele (z final > -0,3)", arret)
    libre = await marcher(pg, 6, 4, "KeyW", 3500)
    rapport(libre[2] < -4, "sans solid : le visiteur traverse le modele (z final < -4)", libre)
    await pg.close()
    # --model-lazy 0 : tout charge au depart, y compris le modele a 1 km
    pg = await ouvrir(br, f"http://127.0.0.1:{port}/tout.html", errs)
    await attendre(pg, ["deco", "loin"], 20000)
    rapport(True, "--model-lazy 0 : le modele a 1 km est charge des le depart")
    rapport(not errs, "--model-lazy 0 : aucune erreur JavaScript", errs)
    await pg.close()


async def plafond(br, port):
    """20 modeles proches : 16 charges au plus (le plus loin est libere), tous charges avec --model-lazy 0"""
    errs = []
    pg = await ouvrir(br, f"http://127.0.0.1:{port}/vingt.html", errs)
    await pg.wait_for_timeout(5000)
    n = await pg.evaluate("(" + LIRE + ")()")
    charges = sum(1 for v in n.values() if v["meshes"] > 0)
    rapport(charges == 16, "plafond : 20 modeles proches, 16 charges en meme temps", charges)
    rapport(not errs, "plafond : aucune erreur JavaScript", errs)
    await pg.close()


async def viewer(br, port):
    pg = await br.new_page(locale="fr-FR", viewport={"width": 1000, "height": 700}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(f"http://127.0.0.1:{port}/glb-viewer.html")
    await pg.wait_for_function("window.__viewer", timeout=60000)
    await pg.set_input_files("#fGlb", str(tmp / "sol.glb"))
    await pg.wait_for_function("window.__viewer.model", timeout=60000)
    opts = await pg.evaluate("[...document.querySelectorAll('#zNewType option')].map(o => o.value)")
    rapport("model" in opts, "viewer : « Modele 3D » dans la liste des types", opts)
    (tmp / "z.json").write_text(json.dumps([ZONES[0], ZONES[1]]), encoding="utf-8")
    await pg.set_input_files("#fZones", str(tmp / "z.json"))
    await pg.wait_for_function("window.__viewer.getZones().length === 2", timeout=10000)
    zs = await pg.evaluate("window.__viewer.getZones()")
    rapport(zs[0]["type"] == "model" and zs[0]["mdl"] == "pilier.glb" and zs[0]["mscale"] == 2 and zs[1]["type"] == "url" and zs[1]["mdl"] == "pilier.glb",
            "viewer : zone model lue (type model, mdl) et zone lien avec modele (type url, mdl)", zs)
    sortie = await pg.evaluate("window.__viewer.getZones().map(window.__viewer.zoneOut)")
    rapport(sortie[0].get("model") == "pilier.glb" and sortie[0].get("scale") == 2 and sortie[0].get("pitch") == 0.25 and sortie[0].get("roll") == -0.25 and "type" not in sortie[0] and "radius" not in sortie[0]
            and sortie[1].get("model") == "pilier.glb" and sortie[1].get("link") == "https://example.org/" and "target" not in sortie[1],
            "viewer : ecrit au format du fichier (model, scale, pitch, roll ; lien avec model)", sortie)
    await pg.select_option("#zNewType", "model")
    champs = await pg.evaluate("(() => { const d = [...document.querySelectorAll('#zoneList details')][0]; d.open = true; return [...d.querySelectorAll('label')].map(l => l.textContent); })()")
    rapport(any("Fichier du mod" in c for c in champs) and any("Taille" in c for c in champs) and any("avant / arri" in c for c in champs) and any("sur le c" in c for c in champs) and any("Solide" in c for c in champs),
            "viewer : champs fichier, taille, inclinaisons et solide", champs)
    # 1.12.41 : une radio, un portail et une musique poses depuis le viewer n'ecrivent pas de cone (faux par defaut) ; le choix « toujours » l'ecrit
    await pg.evaluate("window.__viewer.walkStart({ pos: [0, 0, 0], yaw: 0 })")
    await pg.wait_for_function("window.__viewer.walking", timeout=10000)
    for typ in ("cast", "portal", "audio"):
        await pg.evaluate("(t) => { document.getElementById('zNewType').value = t; window.dispatchEvent(new KeyboardEvent('keydown', { code: 'KeyP', cancelable: true, bubbles: true })); window.dispatchEvent(new KeyboardEvent('keyup', { code: 'KeyP' })); }", typ)
    await pg.evaluate("window.__viewer.walkStop()")
    neuves = await pg.evaluate("window.__viewer.getZones().slice(-3).map(z => ({ type: z.type, cone: z.cone, out: window.__viewer.zoneOut(z).cone }))")
    rapport(len(neuves) == 3 and all(n["cone"] is False and n["out"] is None for n in neuves),
            "viewer : radio, portail et musique poses : cone faux, rien d'ecrit dans le fichier", neuves)
    rapport(not errs, "viewer : aucune erreur JavaScript", errs)
    await pg.close()


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    sol_glb(tmp / "sol.glb"); cube_glb(site / "pilier.glb")
    (tmp / "zones.json").write_text(json.dumps(ZONES), encoding="utf-8")
    vingt = [{"id": f"v{i:02d}", "model": "pilier.glb", "x": -20 + (i % 10) * 4, "y": 15, "z": -10 - (i // 10) * 4} for i in range(20)]
    (tmp / "vingt.json").write_text(json.dumps(vingt), encoding="utf-8")
    def fabriquer(nom, zones, *extra):
        out = site / nom
        r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--zones", str(zones), "--no-sea", *extra, *vend], capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        if r.returncode:
            sys.exit(f"[ECHEC] generation {nom}\n{r.stdout}{r.stderr}")
        out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
        return r.stdout
    fabriquer("page.html", tmp / "zones.json")
    fabriquer("tout.html", tmp / "zones.json", "--model-lazy", "0")
    fabriquer("vingt.html", tmp / "vingt.json")
    proc_site, port = serveur(site)
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), "--help"], capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    rapport("--model-lazy" in r.stdout, "option --model-lazy dans l'aide de glb2html.py")
    proc_view, port_view = serveur(DIST)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            await page_exportee(br, port)
            await plafond(br, port)
            await viewer(br, port_view)
            await br.close()
    finally:
        proc_site.kill(); proc_view.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
