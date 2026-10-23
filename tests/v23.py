#!/usr/bin/env python3
"""Tests de la v23, dans Chromium sans tête :

  - clic simple : nom + point touché (2 décimales), la cible et le cercle d'atterrissage ne bougent pas ; double-clic : ils bougent ;
  - « Placer ici (dernier point cliqué) » copie le dernier point dans la zone ;
  - liaison : deux meshes de même nom à 100 m l'un de l'autre, seul celui qui est cliqué est lié (référence nom#index) ;
    même règle dans le viewer et dans glb2html.py (resolve_mesh_ref) ; un mesh de 30 m est refusé (limite 10 m) ;
  - mémoire : « Réglages restaurés depuis la mémoire du navigateur (N zone(s)) » au rechargement ;
  - rotation de la région (180°) : zones, trou, cible suivent ; une zone posée sur un mesh au nord reste dessus ;
    rotation mémorisée (localStorage, .reglages.json, config du .zip) ; `--rotate 180` donne la même page que le viewer.

Prérequis : pip install playwright ; python build.py avant.
Variables facultatives : THREE_DIR (paquet npm three, hors ligne), CHROMIUM (chemin de l'exécutable).
"""
import asyncio, importlib.util, json, os, pathlib, re, socket, struct, subprocess, sys, tempfile, time, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_v23_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


IDX = [0, 1, 3, 0, 3, 2, 4, 6, 7, 4, 7, 5, 0, 4, 5, 0, 5, 1, 2, 3, 7, 2, 7, 6, 0, 2, 6, 0, 6, 4, 1, 5, 7, 1, 7, 3]


def make_glb(path, meshes, nodes):
    """meshes : [(nom, [boîte, ...])] (une primitive par boîte) ; nodes : [(nom ou None, indice de mesh, translation)].
    Three.js rend uniques les noms de nœuds (« _instance_N », « _1 »), mais les ENFANTS d'un mesh à plusieurs primitives instancié
    par deux nœuds sans nom sont clonés avec le même nom : c'est là que naissent les doublons (OAR : prims répétés)."""
    binb, views, accs, mdefs, mats = b"", [], [], [], []
    for i, (nom, boxes) in enumerate(meshes):
        prims = []
        for j, (x0, y0, z0, x1, y1, z1) in enumerate(boxes):
            verts = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
            pos = b"".join(struct.pack("<3f", *v) for v in verts)
            ind = struct.pack("<36H", *IDX)
            views.append({"buffer": 0, "byteOffset": len(binb), "byteLength": len(pos), "target": 34962}); binb += pos
            accs.append({"bufferView": len(views) - 1, "componentType": 5126, "count": 8, "type": "VEC3", "min": [x0, y0, z0], "max": [x1, y1, z1]})
            views.append({"buffer": 0, "byteOffset": len(binb), "byteLength": len(ind), "target": 34963}); binb += ind
            accs.append({"bufferView": len(views) - 1, "componentType": 5123, "count": 36, "type": "SCALAR"})
            mats.append({"name": "m%d_%d" % (i, j), "doubleSided": True, "pbrMetallicRoughness": {"baseColorFactor": [0.6, 0.6, 0.6, 1], "metallicFactor": 0}})
            prims.append({"attributes": {"POSITION": len(accs) - 2}, "indices": len(accs) - 1, "material": len(mats) - 1})
        mdefs.append({"name": nom, "primitives": prims})
    ndefs = []
    for nom, mi, t in nodes:
        d = {"mesh": mi, "translation": list(t)}
        if nom:
            d["name"] = nom
        ndefs.append(d)
    gltf = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": list(range(len(ndefs)))}], "nodes": ndefs, "meshes": mdefs,
            "materials": mats, "accessors": accs, "bufferViews": views, "buffers": [{"byteLength": len(binb)}]}
    js = json.dumps(gltf).encode()
    js += b" " * (-len(js) % 4)
    binb += b"\0" * (-len(binb) % 4)
    total = 12 + 8 + len(js) + 8 + len(binb)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(binb), b"BIN\0") + binb)


# sol 240 m ; pilier (2 × 4 × 2 m + chapeau, 2 primitives) partagé par deux nœuds sans nom, à -50 et +50 m ;
# « nord » au nord (z = -60) ; « grand » 30 × 5 × 30 m
make_glb(tmp / "ile.glb",
         [("sol", [(-120, -0.2, -120, 120, 0, 120)]), ("pilier", [(-1, 0, -1, 1, 4, 1), (-1, 4, -1, 1, 5, 1)]), ("nord", [(-2, 0, -62, 2, 3, -58)]), ("grand", [(-20, 0, 40, 10, 5, 70)])],
         [("sol", 0, (0, 0, 0)), (None, 1, (-50, 0, 0)), (None, 1, (50, 0, 0)), ("nord", 2, (0, 0, 0)), ("grand", 3, (0, 0, 0))])

spec = importlib.util.spec_from_file_location("glb2html_dist", DIST / "glb2html.py")
g2h = importlib.util.module_from_spec(spec); spec.loader.exec_module(g2h)

ZONES = [
    {"id": "a", "type": "url", "label": "A", "target": "http://127.0.0.1/a", "shape": "board", "x": 0, "y": 0, "z": 0, "yaw": 0.5},
    {"id": "n", "type": "url", "label": "Nord", "target": "http://127.0.0.1/n", "shape": "ring", "x": 0, "y": 3, "z": -60, "radius": 2},
    {"id": "l", "type": "url", "label": "Lié nord", "target": "http://127.0.0.1/l", "mesh": "nord", "radius": 3},
    {"id": "arr", "type": "spawn", "label": "Arrivée", "x": 30, "y": 0, "z": 10, "yaw": 0},
]
(tmp / "zones.json").write_text(json.dumps(ZONES), encoding="utf-8")

PROJ = """(([ref, f]) => { const v = window.__viewer, i = v.meshInfo(ref), P = v.camera.position.constructor;
    const p = new P(...[0, 1, 2].map(k => i.min[k] + (i.max[k] - i.min[k]) * f[k])).project(v.camera), r = v.renderer.domElement.getBoundingClientRect();
    return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; })"""
NUM = re.compile(r"-?\d+\.\d\d")


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


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        ctx = await br.new_context(locale="fr-FR", viewport={"width": 1300, "height": 800}, accept_downloads=True)
        pg = await ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto((DIST / "glb-viewer.html").as_uri())
        await pg.set_input_files("#fGlb", str(tmp / "ile.glb"))
        await pg.wait_for_function("!document.getElementById('bZip').disabled", timeout=20000)
        await pg.wait_for_timeout(800)
        await pg.select_option("#profileSel", "perso")
        await pg.set_input_files("#fZones", str(tmp / "zones.json"))
        await pg.wait_for_timeout(300)
        ev = pg.evaluate

        async def cadrer(ref, zoom=0.05):
            await ev("(([ref, z]) => { const v = window.__viewer, i = v.meshInfo(ref); v.frame([0, 0.6, 1], i.center, z); })", [ref, zoom])
            await pg.wait_for_timeout(250)

        async def zones():
            return await ev("window.__viewer.getZones()")

        # ---------- A. clic simple / double-clic
        pos_cercle = """(() => { const g = window.__viewer.scene.children.find(c => c.isGroup && c.children.length === 2 && c.children[0].geometry && c.children[0].geometry.type === 'RingGeometry'); return g ? g.position.toArray().map(v => Math.round(v * 1000) / 1000) : null; })()"""
        etat = """[window.__viewer.controls.target.toArray().map(v => Math.round(v * 1000) / 1000), """ + pos_cercle + "]"
        await ev("window.__viewer.setCfg({ holeX: 100, holeZ: 20 })")
        await cadrer("sol", 0.9)
        await pg.wait_for_timeout(500)
        avant = await ev(etat)
        pt = await ev(PROJ + "(['sol', [0.15, 1, 0.5]])")
        await pg.mouse.click(*pt)
        await pg.wait_for_timeout(700)
        apres = await ev(etat)
        picked = await pg.inner_text("#picked")
        stat = await pg.inner_text("#stat")
        rapport(avant == apres and avant[1] is not None, "clic simple : ni la cible ni le cercle d'atterrissage ne bougent", (avant, apres))
        m = re.search(r"point \(m\) : (-?\d+\.\d\d), (-?\d+\.\d\d), (-?\d+\.\d\d)", picked)
        rapport(bool(m) and "mesh : sol" in picked and "point" in stat, "clic simple : nom du mesh et point touché (x, y, z, 2 décimales) dans « picked » et la barre d'état", (picked, stat))
        rapport(m and abs(float(m.group(1)) + 84) < 3, "le point affiché est bien celui du clic (x ≈ -84 sur le sol)", picked)
        await pg.mouse.dblclick(*pt)
        await pg.wait_for_timeout(700)
        dbl = await ev(etat)
        rapport(dbl[0] != avant[0] and abs(dbl[0][0] + 84) < 3 and dbl[1] != avant[1], "double-clic : la cible et le cercle d'atterrissage se déplacent", (avant, dbl))

        # ---------- A2. Placer ici
        await pg.click("#zoneList summary")
        await pg.get_by_role("button", name="Placer ici (dernier point cliqué)").first.click()
        await pg.wait_for_timeout(200)
        za = (await zones())[0]
        pts = [float(v) for v in NUM.findall(picked.split("point (m) :")[1])]
        rapport(za["id"] == "a" and [za["x"], za["y"], za["z"]] == pts, "« Placer ici » copie x, y, z du dernier clic simple dans la zone", (za, pts))

        # ---------- B. liaison au morceau cliqué
        noms = await ev("(() => { const o = [], n = []; window.__viewer.model.traverse(c => { o.push(c); n.push(c.name); }); return { n, refs: o.map(c => c.name ? window.__viewer.meshRef(c) : '') }; })()")
        rapport(noms["refs"][noms["n"].index("pilier")] == "pilier#0" and "pilier#1" in noms["refs"] and "pilier_1#1" in noms["refs"] and "sol" in noms["refs"] and "nord" in noms["refs"], "références : nom unique = le nom, nom partagé = nom#index", noms["refs"])
        ok = all(i in g2h.resolve_mesh_ref(noms["n"], r) for i, r in enumerate(noms["refs"]) if r) and g2h.resolve_mesh_ref(noms["n"], "pilier#2") == [] and g2h.resolve_mesh_ref(noms["n"], "sol") == [noms["n"].index("sol")]
        rapport(ok, "glb2html.py (resolve_mesh_ref) résout chaque référence du viewer vers le même objet", noms)
        i0, i1 = await ev("[window.__viewer.meshInfo('pilier#0'), window.__viewer.meshInfo('pilier#1')]")
        rapport(abs(i0["center"][0] + 50) < 0.01 and abs(i1["center"][0] - 50) < 0.01 and i0["count"] == 1 and i1["count"] == 1, "pilier#0 et pilier#1 désignent chacun un seul morceau, à 100 m l'un de l'autre", (i0["center"], i1["center"]))
        await pg.get_by_role("button", name="Lier à un élément").click()
        await cadrer("grand", 0.9)
        await pg.mouse.click(*(await ev(PROJ + "(['grand', [0.5, 1, 0.5]])")))
        await pg.wait_for_timeout(500)
        stat = await pg.inner_text("#stat")
        rapport("Élément trop grand (30 × 30 × 5 m)" in stat and "fusionné avec un bâtiment dans l'OAR" in stat and "zone cercle" in stat and (await zones())[0]["mesh"] == "", "mesh de 30 m refusé, message explicite (L × l × h)", stat)
        await cadrer("pilier#1")
        await pg.mouse.click(*(await ev(PROJ + "(['pilier#1', [0.5, 0.6, 0.5]])")))
        await pg.wait_for_timeout(900)
        za = (await zones())[0]
        rapport(za["mesh"] == "pilier#1" and abs(za["x"] - 50) < 0.05, "deux meshes de même nom à 100 m : seul le cliqué est lié (pilier#1, x = 50)", za)
        rapport(await ev("window.__viewer.meshInfo(window.__viewer.getZones()[0].mesh).count") == 1, "la zone liée ne couvre qu'un morceau")

        # ---------- rotation 180° : état avant
        nord0 = await ev("window.__viewer.meshInfo('nord')")
        await cadrer("nord", 0.6)
        tgt0 = await ev("window.__viewer.controls.target.toArray()")
        ZA = await zones()
        zn = next(z for z in ZA if z["id"] == "n")
        dans = lambda z, i: i["min"][0] <= z["x"] <= i["max"][0] and i["min"][2] <= z["z"] <= i["max"][2]
        rapport(dans(zn, nord0) and abs(nord0["center"][2] + 60) < 0.01, "avant rotation : la zone n est sur le mesh nord (z = -60)", (zn, nord0))
        await pg.select_option("#selRotate", "180")
        await pg.wait_for_timeout(500)
        stat = await pg.inner_text("#stat")
        nord1 = await ev("window.__viewer.meshInfo('nord')")
        ZB = await zones()
        zn1 = next(z for z in ZB if z["id"] == "n")
        rapport("Région tournée de 180° : 4 zone(s) déplacée(s). Recapture la vignette." in stat, "barre d'état de la rotation", stat)
        rapport(abs(nord1["center"][2] - 60) < 0.01 and abs(nord1["center"][0]) < 0.01, "le modèle a tourné de 180° (nord passe de z = -60 à +60)", nord1["center"])
        rapport(dans(zn1, nord1) and abs(zn1["z"] - 60) < 1e-6 and abs(zn1["y"] - 3) < 1e-6, "une zone posée sur le mesh nord reste dessus", (zn1, nord1))
        zl = next(z for z in ZB if z["id"] == "l")
        rapport(zl["mesh"] == "nord" and abs((await ev("window.__viewer.meshInfo('nord').center[2]")) - 60) < 0.01, "la zone liée suit son élément", zl)
        za1 = next(z for z in ZB if z["id"] == "a")
        i1b = await ev("window.__viewer.meshInfo('pilier#1')")
        rapport(abs(i1b["center"][0] + 50) < 0.01 and abs(za1["x"] + 50) < 0.05 and za1["mesh"] == "pilier#1", "pilier#1 (zone liée) passe de x = +50 à -50", (i1b["center"], za1))
        arr0, arr1 = next(z for z in ZA if z["id"] == "arr"), next(z for z in ZB if z["id"] == "arr")
        rapport(abs(arr1["x"] + arr0["x"]) < 1e-6 and abs(arr1["z"] + arr0["z"]) < 1e-6 and abs(abs(arr1["yaw"]) - 3.14159265) < 1e-6, "point d'arrivée : position et orientation tournées de 180°", (arr0, arr1))
        tgt1 = await ev("window.__viewer.controls.target.toArray()")
        rapport(abs(tgt1[0] + tgt0[0]) < 1e-4 and abs(tgt1[2] + tgt0[2]) < 1e-4 and abs(tgt1[1] - tgt0[1]) < 1e-4, "la cible (donc le cercle d'atterrissage) tourne du même angle", (tgt0, tgt1))
        rapport(await ev("[window.__viewer.cfg.holeX, window.__viewer.cfg.holeZ]") == [-100, -20] and await ev("window.__viewer.cfg.rotate") == 180, "le trou tourne aussi", await ev("[window.__viewer.cfg.holeX, window.__viewer.cfg.holeZ]"))

        # ---------- mémorisation partout
        await pg.wait_for_timeout(2200)
        mem = await ev("(() => { const k = Object.keys(localStorage).filter(k => k.startsWith('glb2html_set_')); return k.length ? JSON.parse(localStorage.getItem(k[0])) : null; })()")
        rapport(mem and mem["cfg"].get("rotate") == 180, "rotation mémorisée dans le navigateur (localStorage)", mem and mem["cfg"].get("rotate"))
        async with pg.expect_download() as d:
            await pg.click("#bSetSave")
        sp = tmp / "ile.reglages.json"
        await (await d.value).save_as(sp)
        rapport(json.loads(sp.read_text(encoding="utf-8"))["cfg"]["rotate"] == 180, "rotation dans le .reglages.json")
        async with pg.expect_download() as d:
            await pg.click("#bZip")
        zp = tmp / "ile.modulaire.zip"
        await (await d.value).save_as(zp)
        zc = json.loads(zipfile.ZipFile(zp).read("ile.config.json"))
        rapport(zc["rotate"] == 180, "rotation dans X.config.json du .zip", zc.get("rotate"))
        await pg.click("#bCmd")
        cmd = await ev("document.getElementById('cmdOut').value")
        rapport("--rotate 180" in cmd, "la commande générée reprend --rotate 180", cmd)

        # ---------- C. restauration au rechargement
        await pg.reload()
        await pg.set_input_files("#fGlb", str(tmp / "ile.glb"))
        await pg.wait_for_function("!document.getElementById('bZip').disabled", timeout=20000)
        await pg.wait_for_timeout(800)
        stat = await pg.inner_text("#stat")
        rapport(stat == "Réglages restaurés depuis la mémoire du navigateur (4 zone(s))", "barre d'état au rechargement : réglages restaurés (N zone(s))", stat)
        nord2 = await ev("window.__viewer.meshInfo('nord')")
        rapport(await pg.input_value("#selRotate") == "180" and abs(nord2["center"][2] - 60) < 0.01 and len(await zones()) == 4, "après rechargement : rotation 180 appliquée, zones restaurées", nord2["center"])
        ZC = await zones()
        rapport([(z["id"], z["x"], z["z"]) for z in ZC] == [(z["id"], z["x"], z["z"]) for z in ZB], "les zones restaurées sont celles du repère tourné")

        # ---------- « Oublier les réglages de ce fichier » : la mémoire reste vide tant que rien ne change
        await pg.click("#bSetForget")
        await pg.wait_for_timeout(2500)
        reste = await ev("Object.keys(localStorage).filter(k => k.startsWith('glb2html_set_')).length")
        rapport(reste == 0, "« Oublier les réglages de ce fichier » : la mémoire n'est pas réécrite aussitôt", reste)

        # ---------- page générée avec --rotate 180 = viewer
        site = tmp / "site"
        site.mkdir()
        (tmp / "zv.json").write_text(json.dumps(ZC), encoding="utf-8")
        r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "ile.glb"), "-o", str(site / "ile.html"), "--modular", "--rotate", "180", "--zones", str(tmp / "zv.json"), "--profile", "perso", "--no-sea", *vend], capture_output=True, text=True, cwd=tmp)
        rapport(r.returncode == 0 and json.loads((site / "ile.config.json").read_text(encoding="utf-8"))["rotate"] == 180, "glb2html.py --rotate 180 écrit rotate dans la config", r.stdout + r.stderr)
        r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "ile.glb"), "-o", str(tmp / "auto.html"), "--rotate", "180", "--settings", str(sp), *vend], capture_output=True, text=True, cwd=tmp)
        rapport(r.returncode == 0 and '"rotate": 180' in (tmp / "auto.html").read_text(encoding="utf-8")[:20000000].split('id="cfg">')[1][:4000], "page autonome : rotate dans la config intégrée (--settings relu aussi)", r.stdout + r.stderr)
        r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "ile.glb"), "-o", str(tmp / "set.html"), "--settings", str(sp), *vend], capture_output=True, text=True, cwd=tmp)
        rapport(r.returncode == 0 and '"rotate": 180' in (tmp / "set.html").read_text(encoding="utf-8").split('id="cfg">')[1][:4000], "--settings reprend la rotation du fichier de réglages", r.stdout + r.stderr)
        zcfg = json.loads((site / "ile.config.json").read_text(encoding="utf-8"))
        rapport(set(zcfg) == set(zc), "mêmes clés de config entre le .zip du viewer et le script", sorted(set(zcfg) ^ set(zc)))
        proc, port = serveur(site)
        try:
            ctx2 = await br.new_context(locale="fr-FR", viewport={"width": 900, "height": 600})

            async def patch(route):
                resp = await route.fetch()
                body = (await resp.text()).replace("const viewer = createViewer(", "const viewer = window.__viewer = createViewer(")
                await route.fulfill(response=resp, body=body)
            await ctx2.route("**/ile.html", patch)
            pg2 = await ctx2.new_page()
            errs2 = []
            pg2.on("pageerror", lambda e: errs2.append(str(e)))
            await pg2.goto(f"http://127.0.0.1:{port}/ile.html")
            await pg2.wait_for_function("document.getElementById('msg') === null", timeout=20000)
            await pg2.wait_for_timeout(700)
            for ref in ("nord", "pilier#0", "pilier#1", "sol"):
                a, b = await ev("(r) => window.__viewer.meshInfo(r)", ref), await pg2.evaluate("(r) => window.__viewer.meshInfo(r)", ref)
                rapport(all(abs(x - y) < 1e-3 for k in ("min", "max", "center") for x, y in zip(a[k], b[k])), f"page générée --rotate 180 : « {ref} » aux mêmes positions que le viewer", (a["center"], b["center"]))
            zp2 = await pg2.evaluate("window.__viewer.getZones().map(z => [z.id, z.x, z.z, z.yaw, z.mesh])")
            rapport(zp2 == [[z["id"], z["x"], z["z"], z["yaw"], z["mesh"]] for z in ZC], "page générée : mêmes zones (positions, orientation, éléments liés)", zp2)
            nb = await pg2.evaluate("(() => { const v = window.__viewer; return v.model.children.length; })()")
            rapport(not errs2 and nb > 0, "page générée : aucune erreur JavaScript", errs2)
        finally:
            proc.kill()
        rapport(not errs, "viewer : aucune erreur JavaScript", errs)
        await br.close()


asyncio.run(main())
print("\nRÉSULTAT :", "ÉCHEC (%d)" % bad if bad else "tout est passé")
sys.exit(1 if bad else 0)
