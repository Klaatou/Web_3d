#!/usr/bin/env python3
"""Tests v32 : poser des zones dans une région en tuiles (viewer en mode tuiles) et zones liées à un objet.

Région synthétique (tests/glbfab.py : terrain 6 x 6 patches, maisons, objet « Village » réparti sur 4 tuiles, « Statue », deux « Banc »)
découpée par glb2tiles (16 tuiles). Hors navigateur : extras.ref / extras.box dans les tuiles (nom unique = nom, nom partagé = nom#index,
boîte de l'objet ENTIER dans chaque morceau), `nodeRefs` dans X.tiles.json, --sans-references, avertissements pour d'anciennes tuiles.
Chromium sans tête : glb-viewer.html ouvert depuis le disque, dossier de la région choisi (c'est ce que fera JJ) ou ?tuiles= en http ;
création d'une zone libre, d'un portail, d'une arrivée et de zones liées (« Statue », « Banc » partagé) par clics sur les tuiles chargées ; clic hors
tuile chargée = message et chargement ; coordonnées du point visé et de la cible, copie ; export de X.zones.json et de la commande ; réimport ;
puis glb2html.py --tiles avec ce fichier et contrôle dans la coquille : chaque zone à la bonne position (0,05 m), la zone liée n'apparaît qu'au
chargement de la tuile de son objet, la zone liée à un objet réparti suit la boîte de l'objet entier, arrivée par lien, position affichée dans le
panneau d'aide. Anciennes tuiles : zones liées ignorées avec l'avertissement.

Prérequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v32.py
"""
import asyncio, json, math, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import glbfab
from glbfab import hauteur

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_v32_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


def run(script, *a, ok=True):
    r = subprocess.run([sys.executable, str(script), *map(str, a)], capture_output=True, text=True, cwd=tmp)
    if ok and r.returncode:
        sys.exit(f"[ECHEC] {script.name} {' '.join(map(str, a))}\n{r.stdout}{r.stderr}")
    return r


def lire_glb(chemin):
    d = pathlib.Path(chemin).read_bytes()
    n = struct.unpack("<I", d[12:16])[0]
    return json.loads(d[20:20 + n])


def proche(a, b, tol=0.05):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


OPTS = ["--forcer", "--budget-tri", "900", "--min", "64", "--entier-etendue", "50"]
# ---------- 1. tuiles : références d'objets ----------
print("--- 1. extras.ref / extras.box dans les tuiles")
src = tmp / "region"
src.mkdir()
glbfab.region(src / "Syn.glb", village=True)
r = run(DIST / "glb2tiles.py", src / "Syn.glb", "--nopause", *OPTS)
doc = json.loads((src / "Syn.tiles.json").read_text(encoding="utf-8"))
TILES = doc["tiles"]
rapport(len(TILES) >= 16 and doc["nodeRefs"] == 1 and "Références d'objets" in r.stdout, f"{len(TILES)} tuiles (au moins 16), nodeRefs = 1 dans X.tiles.json, rapport", (len(TILES), doc.get("nodeRefs")))
par_ref = {}
for t in TILES:
    for n in lire_glb(src / t["file"])["nodes"]:
        ex = n.get("extras", {})
        if "ref" in ex:
            par_ref.setdefault(ex["ref"], []).append((t["file"], ex.get("box")))
VX, VZ = glbfab.VILLAGE_X0, glbfab.VILLAGE_Z
haut = [hauteur(VX + 45 * k, VZ) for k in range(8)]
BOX_VILLAGE = [VX - 3, min(haut), VZ - 3, VX + 45 * 7 + 3, max(haut) + 4, VZ + 3]
v = par_ref.get("Village", [])
rapport(len({f for f, _ in v}) >= 2 and all(proche(b, BOX_VILLAGE, 0.01) for _, b in v), f"« Village » réparti sur {len({f for f, _ in v})} tuiles : même boîte (celle de l'objet entier) dans chacune", v[:2])
sx, sz = glbfab.STATUE
rapport(len(par_ref.get("Statue", [])) == 1 and proche(par_ref["Statue"][0][1], [sx - 1, hauteur(sx, sz), sz - 1, sx + 1, hauteur(sx, sz) + 5, sz + 1], 0.01), "« Statue » : nom unique = référence, boîte exacte", par_ref.get("Statue"))
rapport(len(par_ref.get("Banc#0", [])) == 1 and len(par_ref.get("Banc#1", [])) == 1 and "Banc" not in par_ref, "deux nœuds « Banc » : références Banc#0 et Banc#1 (même règle que nom#index)", [k for k in par_ref if k.startswith("Banc")])
rapport("Hutte 3" in par_ref and "Terrain 2,2" in par_ref, "autres nœuds nommés référencés (Hutte 3, Terrain 2,2)")
# ancien format
old = tmp / "old"
old.mkdir()
shutil.copy(src / "Syn.glb", old / "Syn.glb")
run(DIST / "glb2tiles.py", old / "Syn.glb", "--nopause", *OPTS, "--sans-references")
doc_old = json.loads((old / "Syn.tiles.json").read_text(encoding="utf-8"))
ex_old = [n.get("extras", {}) for n in lire_glb(old / doc_old["tiles"][0]["file"])["nodes"]]
rapport(doc_old["nodeRefs"] == 0 and not any("ref" in e for e in ex_old), "--sans-references : format de la v31 (nodeRefs 0, aucun extras.ref)")
r = run(DIST / "glb2tiles.py", old / "Syn.glb", "--nopause", *OPTS, "--vue-ensemble-seule")
rapport("sans les références d'objets" in r.stdout and "Refaire le découpage" in r.stdout, "--vue-ensemble-seule sur d'anciennes tuiles : signale qu'il faut redécouper", r.stdout[-300:])

r = run(DIST / "glb2tiles.py", old / "Syn.glb", "--nopause", *OPTS, "--analyse")
rapport("ne portent pas les références d'objets" in r.stdout, "--analyse à côté d'anciennes tuiles : signale qu'il faut redécouper", r.stdout[-300:])
r = run(DIST / "glb2tiles.py", src / "Syn.glb", "--nopause", *OPTS, "--analyse")
rapport("ne portent pas les références" not in r.stdout, "--analyse à côté de tuiles v32 : pas d'avertissement")

# ---------- 2. zones à enregistrer plus tard (pour l'ancien format) ----------
ZL = [{"id": "liee", "type": "url", "label": "Lien statue", "target": "https://example.org/", "mesh": "Statue", "x": 300, "y": 16.4, "z": 40, "radius": 3}]
(tmp / "zl.json").write_text(json.dumps(ZL), encoding="utf-8")
site_old = tmp / "site_old"
site_old.mkdir()
r = run(DIST / "glb2html.py", "-o", site_old / "Syn.html", "--shared-shell", "--tiles", old / "Syn.tiles.json", "--zones", tmp / "zl.json", *vend)
rapport("redécouper" in r.stderr.lower() or "Refaire le découpage" in r.stderr, "glb2html --tiles, anciennes tuiles + zone liée : avertissement « redécouper »", r.stderr[-300:])
r = run(DIST / "glb2html.py", "-o", tmp / "site_new_try" / "Syn.html", "--shared-shell", "--tiles", src / "Syn.tiles.json", "--zones", tmp / "zl.json", *vend)
rapport("[AVERTISSEMENT]" not in r.stderr and "liées à un objet" in r.stdout, "glb2html --tiles, tuiles v32 + zone liée : pas d'avertissement, la zone sera placée avec l'objet", (r.stdout[-300:], r.stderr[-200:]))


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


def boite_contient(t, x, z):
    return t["min"][0] - 0.5 <= x <= t["max"][0] + 0.5 and t["min"][2] - 0.5 <= z <= t["max"][2] + 0.5


def tuile_de(x, z):
    return next(t["file"] for t in TILES if boite_contient(t, x, z))


PROJ = """([x, y, z]) => { const v = window.__viewer; v.camera.updateMatrixWorld(true);
    const p = v.camera.position.clone().set(x, y, z).project(v.camera), r = v.renderer.domElement.getBoundingClientRect();
    return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; }"""

EXPORT = {}


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)

        # ---------- 3. viewer en mode tuiles : dossier choisi ----------
        print("--- 3. viewer : région en tuiles")
        ctx = await br.new_context(locale="fr-FR", viewport={"width": 1300, "height": 800}, accept_downloads=True)
        pg = await ctx.new_page()
        errs, warns = [], []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: warns.append(m.text) if m.type in ("warning", "error") else None)
        ev = pg.evaluate
        await pg.goto((DIST / "glb-viewer.html").as_uri())
        await pg.set_input_files("#fTiles", str(src))
        await pg.wait_for_function("window.__viewer.tiled && window.__viewer.tilesState().ready.length > 0 && window.__viewer.tilesState().overview.state === 'ready'", timeout=60000)
        await pg.wait_for_timeout(500)
        info = await pg.inner_text("#tilesInfoV")
        rapport(f"{len(TILES)} tuile(s)" in info and "vue d'ensemble oui" in info and "références d'objets oui" in info and "aucun recentrage" in info, "région ouverte par le dossier : texte d'information", info)
        e0 = await ev("window.__viewer.tilesState()")
        ext = doc["extent"]
        cx, cz = (ext["min"][0] + ext["max"][0]) / 2, (ext["min"][2] + ext["max"][2]) / 2
        tg = await ev("window.__viewer.controls.target.toArray()")
        rapport(abs(tg[0] - cx) < 60 and abs(tg[2] - cz) < 60 and e0["overview"]["state"] == "ready", "la caméra vise la région (vue d'ensemble affichée) ; repère d'origine", (tg, cx, cz))
        rapport(await ev("document.getElementById('bHtml').disabled && document.getElementById('bZip').disabled && document.getElementById('selRotate').disabled"), "export HTML autonome et .zip désactivés, rotation non proposée")
        rapport(not errs, "aucune erreur JavaScript à l'ouverture", errs)

        async def cadrer(x, y, z, zoom=0.12):
            await ev("(([x, y, z, zm]) => window.__viewer.frame([0, 0.8, 1], [x, y, z], zm))", [x, y, z, zoom])
            f = tuile_de(x, z)
            await pg.wait_for_function("f => window.__viewer.tilesState().ready.includes(f)", arg=f, timeout=40000)
            await pg.wait_for_timeout(300)

        async def poser(type_, x, z, id_=None):
            await cadrer(x, hauteur(x, z), z)
            await pg.select_option("#zNewType", type_)
            await pg.click("#bZoneAdd")
            sx_, sy_ = await ev(PROJ, [x, hauteur(x, z), z])
            await pg.mouse.click(sx_, sy_)
            await pg.wait_for_timeout(300)
            zs = await ev("window.__viewer.getZones()")
            return zs[-1]

        z1 = await poser("url", 300, -120)
        rapport(z1["type"] == "url" and abs(z1["x"] - 300) < 0.6 and abs(z1["z"] + 120) < 0.6 and abs(z1["y"] - hauteur(z1["x"], z1["z"])) < 0.1, "zone libre posée par clic sur une tuile chargée (sur le sol)", z1)
        z2 = await poser("portal", 350, -120)
        rapport(z2["type"] == "portal" and abs(z2["x"] - 350) < 0.6 and abs(z2["z"] + 120) < 0.6, "portail posé", z2)
        z3 = await poser("spawn", 250, -120)
        rapport(z3["type"] == "spawn" and abs(z3["x"] - 250) < 0.6 and abs(z3["z"] + 120) < 0.6 and abs(z3["y"] - hauteur(z3["x"], z3["z"])) < 0.1, "arrivée posée", z3)
        # identifiants lisibles : arrivée « depart », portail vers cette arrivée
        await pg.evaluate("""() => { const ds = [...document.querySelectorAll('#zoneList details')]; const set = (d, v) => { const i = d.querySelector('input[type=text]'); i.value = v; i.dispatchEvent(new Event('change')); };
            set(ds[2], 'depart'); }""")
        await pg.wait_for_timeout(200)

        async def lier(id_pos, nom_attendu, x, y, z, zoom=0.06):
            """Pose une zone libre puis la lie à l'objet cliqué en (x, y, z)."""
            await cadrer(x, y, z, zoom)
            await pg.select_option("#zNewType", "url")
            await pg.click("#bZoneAdd")
            sx0, sy0 = await ev(PROJ, [x, hauteur(x, z), z])
            await pg.mouse.click(sx0, sy0)
            await pg.wait_for_timeout(300)
            await pg.click("#zoneList details[open] button:text('Lier à un élément')")
            sx_, sy_ = await ev(PROJ, [x, y, z])
            await pg.mouse.click(sx_, sy_)
            await pg.wait_for_timeout(500)
            zs = await ev("window.__viewer.getZones()")
            return zs[-1]

        yst = hauteur(sx, sz)
        z4 = await lier(0, "Statue", sx, yst + 2.5, sz)
        rapport(z4["mesh"] == "Statue" and proche([z4["x"], z4["y"], z4["z"]], [sx, yst, sz], 0.05), "zone liée à l'objet cliqué « Statue » (tuiles) : référence et position = boîte de l'objet", z4)
        bx, bz = glbfab.BANCS[1]
        z5 = await lier(0, "Banc#1", bx, hauteur(bx, bz) + 1.0, bz, 0.04)
        rapport(z5["mesh"] == "Banc#1" and proche([z5["x"], z5["z"]], [bx, bz], 0.05), "zone liée à un nom partagé : référence Banc#1", z5)
        stt = await pg.inner_text("#stat")
        rapport("Banc#1" in stt, "message de liaison", stt)
        rapport(not errs, "aucune erreur JavaScript pendant l'édition", errs)

        # zone liée à un objet dont la tuile n'est pas chargée : texte clair, pas de plantage (la zone « Statue » reste visible tant que la tuile l'est)
        zs = await ev("window.__viewer.getZoneState()")
        rapport(next(z for z in zs if z["mesh"] == "Statue")["linked"] and next(z for z in zs if z["mesh"] == "Banc#1")["linked"], "les deux zones liées sont résolues sur les tuiles chargées", zs[-2:])

        # clic hors tuile chargée : message, puis chargement
        far = max((t for t in TILES), key=lambda t: math.hypot((t["min"][0] + t["max"][0]) / 2 - bx, (t["min"][2] + t["max"][2]) / 2 - bz))
        fx, fz = (far["min"][0] + far["max"][0]) / 2, (far["min"][2] + far["max"][2]) / 2
        await ev("(([x, y, z]) => window.__viewer.frame([0, 0.8, 1], [x, y, z], 1.0))", [bx, 15, bz])   # vue éloignée : tout dans l'image, tuile lointaine non chargée
        await pg.wait_for_timeout(1500)
        pret = await ev("window.__viewer.tilesState().ready")
        rapport(far["file"] not in pret, "tuile lointaine non chargée avant le test", (far["file"], pret))
        await pg.select_option("#zNewType", "url")
        await pg.click("#bZoneAdd")
        sx_, sy_ = await ev(PROJ, [fx, hauteur(fx, fz), fz])
        await pg.mouse.click(sx_, sy_)
        await pg.wait_for_timeout(400)
        stt = await pg.inner_text("#stat")
        nz = len(await ev("window.__viewer.getZones()"))
        rapport("Pas de tuile détaillée chargée à cet endroit" in stt and nz == 5, "clic sur la vue d'ensemble : message en texte, aucune zone posée", (stt, nz))
        await pg.wait_for_function("f => window.__viewer.tilesState().ready.includes(f) || window.__viewer.tilesState().loadingFiles.includes(f)", arg=far["file"], timeout=40000)
        rapport(True, "la tuile du point cliqué est chargée (ou en cours)")
        await pg.click("#bZoneAdd")   # désarme le mode de pose

        # coordonnées et copie
        await cadrer(330, hauteur(330, -128), -128)
        await pg.mouse.click(*(await ev(PROJ, [330, hauteur(330, -128), -128])))   # loin de toute zone : un clic sur une zone la sélectionne au lieu de viser le modèle
        await pg.wait_for_timeout(300)
        ci = await pg.inner_text("#coordInfo")
        import re
        rapport(re.search(r"point visé \(clic simple\) : x -?\d+\.\d · y -?\d+\.\d · z -?\d+\.\d m", ci) and re.search(r"cible .*: x -?\d+\.\d · y -?\d+\.\d · z -?\d+\.\d m", ci), "coordonnées du point visé et de la cible : x, y, z en m, une décimale", ci)
        await pg.click("#bCopyPick")
        await pg.wait_for_timeout(400)
        st1 = await pg.inner_text("#stat")
        await pg.click("#bCopyTarget")
        await pg.wait_for_timeout(400)
        st2 = await pg.inner_text("#stat")
        rapport(re.search(r"Point visé copié : -?\d+\.\d, -?\d+\.\d, -?\d+\.\d", st1) and re.search(r"Cible copiée : -?\d+\.\d, -?\d+\.\d, -?\d+\.\d", st2), "boutons de copie (point visé, cible)", (st1, st2))

        # export des zones et de la commande
        async with pg.expect_download() as dl:
            await pg.click("#bZoneExp")
        d_ = await dl.value
        rapport(d_.suggested_filename == "Syn.zones.json", "export : nom du fichier X.zones.json", d_.suggested_filename)
        EXPORT["zones"] = json.loads(pathlib.Path(await d_.path()).read_text(encoding="utf-8"))
        zl_ = EXPORT["zones"]
        rapport(len(zl_) == 5 and [z["type"] for z in zl_] == ["url", "portal", "spawn", "url", "url"] and zl_[3]["mesh"] == "Statue" and zl_[4]["mesh"] == "Banc#1", "zones exportées : libre, portail, arrivée, deux zones liées", [(z["type"], z["mesh"]) for z in zl_])
        await pg.select_option("#profileSel", "perso")
        await pg.fill("#cmdScript", "glb2html.py")
        await pg.click("#bCmd")
        cmd = await pg.input_value("#cmdOut")
        rapport("--tiles 'Syn.tiles.json'" in cmd and "--zones 'Syn.zones.json'" in cmd and "-o 'Syn.html'" in cmd and "--shared-shell" in cmd and "--profile perso" in cmd and "'Syn.glb'" not in cmd and "--rotate" not in cmd, "récapitulatif de commande : --tiles, --zones X.zones.json, -o, coquille commune", cmd)
        notes = await pg.inner_text("#cmdNote")
        rapport("Région en tuiles" in notes, "notes de la commande en mode tuiles", notes[:200])
        rapport(not errs, "aucune erreur JavaScript", errs)
        await pg.close()

        # ---------- réimport dans une nouvelle session (compléter une région) ----------
        pg = await ctx.new_page()
        errs.clear()
        pg.on("pageerror", lambda e: errs.append(str(e)))
        ev = pg.evaluate
        await pg.goto((DIST / "glb-viewer.html").as_uri())
        await pg.set_input_files("#fTiles", str(src))
        await pg.wait_for_function("window.__viewer.tiled && window.__viewer.tilesState().ready.length > 0", timeout=60000)
        f_st = tuile_de(sx, sz)
        await pg.wait_for_timeout(4300)   # fin du point de départ forcé
        await pg.evaluate("window.__viewer.controls.target.set(150, 15, -280)")   # loin de la statue : sa tuile se décharge
        await pg.wait_for_function("f => !window.__viewer.tilesState().ready.includes(f) && !window.__viewer.tilesState().loadingFiles.includes(f)", arg=f_st, timeout=30000)
        (tmp / "export.zones.json").write_text(json.dumps(EXPORT["zones"]), encoding="utf-8")
        await pg.set_input_files("#fZones", str(tmp / "export.zones.json"))
        await pg.wait_for_timeout(500)
        zs = await ev("window.__viewer.getZones()")
        rapport(len(zs) == 5 and zs[3]["mesh"] == "Statue" and proche([zs[0]["x"], zs[0]["y"], zs[0]["z"]], [EXPORT["zones"][0][k] for k in "xyz"], 1e-6), "réimport du X.zones.json : les 5 zones sont là, prêtes à être complétées", [z["id"] for z in zs])
        st = await ev("window.__viewer.getZoneState()")
        rapport(not next(z for z in st if z["mesh"] == "Statue")["linked"] and next(z for z in st if z["mesh"] == "Statue")["off"], "zone liée dont la tuile n'est pas chargée : absente de la scène (linked faux)", st[3])
        await pg.click("#zoneList summary >> nth=3")
        await pg.wait_for_timeout(200)
        txt = await pg.inner_text("#zoneList details[open]")
        rapport("tuile non chargée" in txt, "fiche de la zone liée : texte « tuile non chargée »", txt[:200])
        await pg.evaluate("window.__viewer.controls.target.set(300, 15, 40)")
        await pg.wait_for_function("window.__viewer.getZoneState().find(z => z.mesh === 'Statue').linked", timeout=40000)
        rapport(True, "la zone liée se résout dès que la tuile de la statue est chargée")
        await pg.close()

        # ---------- retour à un GLB unique après une région en tuiles ----------
        pg = await ctx.new_page()
        errs.clear()
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto((DIST / "glb-viewer.html").as_uri())
        await pg.set_input_files("#fTiles", str(src))
        await pg.wait_for_function("window.__viewer.tiled && window.__viewer.tilesState().ready.length > 0", timeout=60000)
        await pg.set_input_files("#fGlb", str(ROOT / "tests" / "data" / "walk3.glb"))
        await pg.wait_for_function("!document.getElementById('bZip').disabled", timeout=30000)
        st = await pg.evaluate("({ tiled: window.__viewer.tiled, seaY: window.__viewer.cfg.seaY, kids: window.__viewer.scene.children.filter(c => c.name === 'tiles' || c.name === 'overview').length, bHtml: document.getElementById('bHtml').disabled, rot: document.getElementById('selRotate').disabled })")
        rapport(not st["tiled"] and st["kids"] == 0 and not st["bHtml"] and not st["rot"] and st["seaY"] == -50 and not errs, "ouvrir un .glb après une région en tuiles : mode tuiles quitté, tuiles et vue d'ensemble retirées, exports et rotation rétablis", (st, errs))
        await pg.close()

        # ---------- ouverture par adresse (?tuiles=) ----------
        vsite = tmp / "vsite"
        shutil.copytree(src, vsite / "regions")
        shutil.copy(DIST / "glb-viewer.html", vsite / "glb-viewer.html")
        proc, port = serveur(vsite)
        try:
            pg = await ctx.new_page()
            errs.clear()
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{port}/glb-viewer.html?tuiles=regions/Syn.tiles.json")
            await pg.wait_for_function("window.__viewer.tiled && window.__viewer.tilesState().ready.length > 0", timeout=60000)
            rapport(await pg.evaluate("window.__viewer.tilesState().total") == len(TILES) and not errs, "glb-viewer.html?tuiles=… (http) : région ouverte", errs)
            await pg.close()
            # glisser-déposer d'un dossier : entrées de dossier simulées (sous-dossier, lecture par lots), fichiers lus par http
            pg = await ctx.new_page()
            errs.clear()
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{port}/glb-viewer.html")
            await pg.evaluate("""async ([files, base]) => {
                const mkFile = async p => new File([await (await fetch(base + p)).arrayBuffer()], p.split('/').pop());
                const fe = p => ({ isFile: true, isDirectory: false, name: p.split('/').pop(), file: (ok, ko) => mkFile(p).then(ok, ko) });
                const de = (name, kids) => ({ isFile: false, isDirectory: true, name, createReader() { let given = false; return { readEntries: ok => { if (given) return ok([]); given = true; ok(kids); } }; } });
                const root = de('regions', [fe('Syn.tiles.json'), fe('Syn.overview.glb'), de('Syn.tiles', files.map(fe))]);
                const e = new Event('drop', { bubbles: true, cancelable: true });
                e.dataTransfer = { items: [{ webkitGetAsEntry: () => root }], files: [] };
                window.dispatchEvent(e); }""", [[t["file"] for t in TILES], "regions/"])
            await pg.wait_for_function("window.__viewer.tiled && window.__viewer.tilesState().ready.length > 0", timeout=60000)
            rapport(await pg.evaluate("window.__viewer.tilesState().total") == len(TILES) and not errs, "glisser-déposer du dossier de la région : ouverte (sous-dossier et vue d'ensemble compris)", errs)
            await pg.close()
            pg = await ctx.new_page()
            await pg.goto(f"http://127.0.0.1:{port}/glb-viewer.html?tuiles=../secret.tiles.json")
            await pg.wait_for_timeout(800)
            rapport("refusée" in await pg.inner_text("#stat") and not await pg.evaluate("window.__viewer.tiled"), "?tuiles= avec « .. » : refusé, rien n'est lu")
            await pg.close()
        finally:
            proc.kill()

        # ---------- 4. coquille : zones à la bonne position, zone liée au chargement de la tuile ----------
        print("--- 4. coquille")
        village = {"id": "village", "type": "url", "label": "Village", "target": "https://example.org/", "mesh": "Village", "x": 0, "y": 0, "z": 0, "radius": 3}
        zfinal = EXPORT["zones"] + [village]
        (tmp / "zfinal.json").write_text(json.dumps(zfinal), encoding="utf-8")
        site = tmp / "site"
        site.mkdir()
        shutil.copytree(src / "Syn.tiles", site / "Syn.tiles")
        shutil.copy(src / "Syn.tiles.json", site / "Syn.tiles.json")
        shutil.copy(src / "Syn.overview.glb", site / "Syn.overview.glb")
        run(DIST / "glb2html.py", "-o", site / "Syn.html", "--shared-shell", "--tiles", site / "Syn.tiles.json", "--zones", tmp / "zfinal.json", "--profile", "perso", *vend)
        proc, port = serveur(site)
        base = f"http://127.0.0.1:{port}/index.html?region=Syn&rayon=60"

        class Onglet:
            def __init__(self):
                self.errs, self.warns, self.garde = [], [], {}

            async def ouvrir(self, url):
                c = await br.new_context(locale="fr-FR", viewport={"width": 800, "height": 560})
                self.pg = await c.new_page()
                self.pg.on("pageerror", lambda e: self.errs.append(str(e)))
                self.pg.on("console", lambda m: self.warns.append(m.text) if m.type in ("warning", "error") else None)
                await self.pg.route("**/*.glb", self.route)
                await self.pg.goto(url)
                return self

            async def route(self, route):
                nom = route.request.url.split("/")[-1]
                if nom in self.garde:
                    await self.garde[nom].wait()
                try:
                    await route.continue_()
                except Exception:
                    pass

            async def ev(self, js, arg=None):
                return await self.pg.evaluate(js, arg)

            async def zs(self):
                return {z["id"]: z for z in await self.ev("window.__viewer.getZoneState()")}

        try:
            o = Onglet()
            f_statue = tuile_de(sx, sz)
            o.garde[pathlib.Path(f_statue).name] = asyncio.Event()
            await o.ouvrir(base)
            await o.pg.wait_for_function("window.__viewer && window.__viewer.tilesState().ready.length > 0", timeout=60000)
            await o.pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
            await o.pg.wait_for_timeout(4300)   # fin du point de départ forcé
            Z = await o.zs()
            libre, portail = EXPORT["zones"][0], EXPORT["zones"][1]
            rapport(proche(Z[libre["id"]]["pos"], [libre[k] for k in "xyz"]) and proche(Z[portail["id"]]["pos"], [portail[k] for k in "xyz"]), "zone libre et portail : à la position exportée (0,05 m)", (Z[libre["id"]]["pos"], [libre[k] for k in "xyz"]))
            arr = EXPORT["zones"][2]
            rapport(proche(Z[arr["id"]]["pos"], [arr[k] for k in "xyz"]), "arrivée : à la position exportée", Z[arr["id"]]["pos"])
            ids_lies = [z["id"] for z in EXPORT["zones"] if z["mesh"]]
            rapport(all(not Z[i]["linked"] and Z[i]["off"] for i in ids_lies) and not Z["village"]["linked"], "zones liées : absentes tant que la tuile de leur objet n'est pas chargée", [(i, Z[i]["linked"]) for i in ids_lies])
            await o.ev("window.__viewer.controls.target.set(%f, 15, %f)" % (sx, sz))
            await o.pg.wait_for_timeout(2500)
            Z = await o.zs()
            rapport(not Z[ids_lies[0]]["linked"], "tuile de la statue chargée seulement à moitié (réponse retenue) : zone toujours absente", Z[ids_lies[0]])
            o.garde[pathlib.Path(f_statue).name].set()
            await o.pg.wait_for_function("window.__viewer.getZoneState().find(z => z.mesh === 'Statue').linked", timeout=40000)
            Z = await o.zs()
            zst = Z[ids_lies[0]]
            rapport(zst["linked"] and zst["shown"] and proche(zst["pos"], [sx, yst, sz]) and proche(zst["box"], [sx - 1, yst, sz - 1, sx + 1, yst + 5, sz + 1]), "la zone liée apparaît au chargement de la tuile : position et boîte de la statue (0,05 m)", zst)
            # objet réparti : Village, avec le morceau de la hutte 0 seulement
            await o.ev("window.__viewer.controls.target.set(%f, 15, %f)" % (VX, VZ))
            await o.pg.wait_for_function("window.__viewer.getZoneState().find(z => z.id === 'village').linked", timeout=40000)
            await o.pg.wait_for_timeout(1500)
            Z = await o.zs()
            e = await o.ev("window.__viewer.tilesState()")
            tv = {f for f, _ in par_ref["Village"]}
            rapport(Z["village"]["linked"] and proche(Z["village"]["box"], BOX_VILLAGE) and len(tv & set(e["ready"])) < len(tv), f"objet réparti : la zone suit la boîte de l'objet entier ({len(tv & set(e['ready']))} tuile(s) sur {len(tv)} chargées)", (Z["village"]["box"], BOX_VILLAGE))
            # panneau d'aide : position de la cible
            await o.ev("window.__viewer.controls.target.set(123.46, 15.04, -77.74)")
            await o.pg.wait_for_timeout(600)
            pi = await o.pg.inner_text("#posInfo")
            rapport(pi == "Position cible (vue globale) : x 123.5 · y 15.0 · z -77.7 m", "panneau d'aide : position de la cible (une décimale)", pi)
            # tout décharger : les zones liées disparaissent
            await o.ev("window.__viewer.controls.target.set(9000, 20, 9000)")
            await o.pg.wait_for_function("window.__viewer.tilesState().ready.length === 0", timeout=30000)
            await o.pg.wait_for_timeout(600)
            Z = await o.zs()
            rapport(all(not Z[i]["linked"] for i in ids_lies + ["village"]), "tuiles déchargées : les zones liées disparaissent", {i: Z[i]["linked"] for i in ids_lies + ["village"]})
            rapport(not o.errs, "aucune erreur JavaScript dans la coquille", o.errs)
            await o.pg.context.close()
            # arrivée par lien : l'avatar apparaît à la position de l'arrivée ; panneau : position de l'avatar
            o = Onglet()
            await o.ouvrir(base + f"#spawn={arr['id']}&name=Test")
            await o.pg.wait_for_function("window.__viewer && window.__viewer.walking", timeout=60000)
            w = await o.ev("window.__viewer.getWalk().pos")
            rapport(proche([w[0], w[2]], [arr["x"], arr["z"]]) and abs(w[1] - arr["y"]) < 0.3, "arrivée par lien : l'avatar apparaît à la position de l'arrivée", (w, arr))
            await o.pg.wait_for_timeout(600)
            pi = await o.pg.inner_text("#posInfo")
            rapport(pi.startswith("Position avatar : x ") and f"{w[0]:.1f}" in pi and f"{w[2]:.1f}" in pi, "panneau d'aide : position de l'avatar en promenade", (pi, w))
            await o.pg.context.close()
        finally:
            proc.kill()

        # ---------- 5. anciennes tuiles : zones liées ignorées ----------
        print("--- 5. anciennes tuiles")
        proc, port = serveur(site_old)
        try:
            o = Onglet()
            await o.ouvrir(f"http://127.0.0.1:{port}/index.html?region=Syn&rayon=60")
            await o.pg.wait_for_function("window.__viewer && window.__viewer.tilesState().ready.length > 0", timeout=60000)
            await o.pg.wait_for_timeout(1000)
            zs_ = await o.ev("window.__viewer.getZones().map(z => z.id)")
            rapport(zs_ == [] and any("liee" in w and "ignorée" in w and "redécouper" in w for w in o.warns) and not o.errs, "anciennes tuiles : zone liée ignorée avec l'avertissement (redécouper avec glb2tiles v32)", (zs_, o.warns[:3], o.errs))
            await o.pg.context.close()
        finally:
            proc.kill()
        await br.close()


asyncio.run(main())
shutil.rmtree(tmp, ignore_errors=True)
print("\nRÉSULTAT :", "tout est passé" if not bad else f"{bad} échec(s)")
sys.exit(1 if bad else 0)
