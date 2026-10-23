#!/usr/bin/env python3
"""Tests du mode modulaire universel (v20), dans Chromium sans tête :

  - la coquille <page>.html est la même, octet pour octet, pour toutes les régions, et ne contient aucun nom de région ;
  - copier la page sous un autre nom, avec ses trois fichiers frères renommés, fonctionne ; titre = salon, fond = skyColor ;
  - zones relues à chaque rechargement : <page>.zones.json, sinon zones.json du dossier, sinon aucune (sans erreur) ;
  - --config-only ne touche pas <page>.zones.json sauf avec --zones ; --zones-only marche sur une page modulaire ;
  - zones liées à un élément (champ mesh) : curseur main au survol, clic, touche E, portail à l'approche ;
    un élément traversable (walkIgnore) ne bloque pas le clic ;
  - coquille unique (v26) : index.html?region=NOM sert plusieurs régions d'un même dossier (--shared-shell), région simple
    inchangée, NOM refusé sans aucune requête réseau (../x, https://..., a/b, vide...), carte, portails et #spawn= ;
  - viewer : « Exporter HTML autonome » et « Exporter la structure modulaire (.zip) » côte à côte, les deux exports
    fonctionnent, la coquille du .zip est identique à celle de glb2html.py --modular, « Lier à un élément » / « Délier ».

Prérequis : pip install playwright ; python build.py avant.
Variables facultatives : THREE_DIR (paquet npm three, hors ligne), CHROMIUM (chemin de l'exécutable).
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"   # outils Python en français (v36)
import asyncio, hashlib, importlib.util, json, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST, DATA = ROOT / "dist", ROOT / "tests" / "data"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_modulaire_"))
site = tmp / "site"
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


def run(*a, ok=True):
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), *map(str, a), *vend], capture_output=True, text=True, cwd=tmp)
    if ok and r.returncode:
        sys.exit(f"[ECHEC] {' '.join(map(str, a))}\n{r.stdout}{r.stderr}")
    return r


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


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
make_glb(tmp / "boite.glb", [("sol", "sol", (-12, -0.2, -12, 12, 0, 12), 1.0), ("boite", "mur", (4, 0, -2, 8, 4, 2), 1.0),
                              ("door_voile", "verre", (2, 0, 4, 10, 6, 4.05), 0.3)])

# ---------- génération
ZA = [{"id": "b", "type": "url", "label": "Boîte A", "target": "http://127.0.0.1/a", "mesh": "boite", "radius": 8}]
ZB = [{"id": "b", "type": "url", "label": "Boîte B", "target": "http://127.0.0.1/b", "mesh": "boite", "radius": 8}]
FALLBACK = [{"id": "b", "type": "url", "label": "Secours", "target": "http://127.0.0.1/secours", "mesh": "boite", "radius": 8}]
PORTAIL = [{"id": "p", "type": "portal", "label": "Portail", "trigger": "enter", "target": "WALK3_URL", "mesh": "boite", "radius": 2}]
(tmp / "za.json").write_text(json.dumps(ZA), encoding="utf-8")
for nom in ("walk3", "draco", "meshopt"):
    run(DATA / f"{nom}.glb", "-o", site / f"{nom}.html", "--modular", "--room", nom)
run(tmp / "boite.glb", "-o", site / "boite.html", "--modular", "--zones", tmp / "za.json", "--sky-color", "336699", "--no-sea")

coques = {nom: (site / f"{nom}.html").read_bytes() for nom in ("walk3", "draco", "meshopt", "boite")}
rapport(len(set(coques.values())) == 1, "coquille identique pour toutes les régions (octet pour octet)", {k: len(v) for k, v in coques.items()})
txt = coques["walk3"].decode("utf-8")
rapport(all(n not in txt for n in ("walk3", "boite", "Ankh", "meshopt.glb", "draco.glb")) and "BOOT" in txt, "aucun nom de région écrit dans la coquille")
lib = site / "lib" / "three-0.160.0"
rapport(all((lib / f).is_file() for f in ("DRACOLoader.js", "meshopt_decoder.module.js", "draco/draco_decoder.wasm", "draco/draco_wasm_wrapper.js", "three.module.js")), "lib/ contient toujours Draco et Meshopt (même pour un .glb brut)")
for nom in ("walk3", "boite"):
    cfg = json.loads((site / f"{nom}.config.json").read_text(encoding="utf-8"))
    rapport(cfg["zones"] == [] and cfg["zonesLive"] == "", f"{nom}.config.json ne contient pas de zones")
rapport(json.loads((site / "boite.zones.json").read_text(encoding="utf-8"))[0]["mesh"] == "boite", "zones écrites dans boite.zones.json (champ mesh conservé)")
rapport(json.loads((site / "walk3.zones.json").read_text(encoding="utf-8")) == [], "sans zones données : walk3.zones.json vide créé")

# clean_zones : validation du champ mesh
spec = importlib.util.spec_from_file_location("glb2html_dist", DIST / "glb2html.py")
g2h = importlib.util.module_from_spec(spec); spec.loader.exec_module(g2h)
cz = g2h.clean_zones([{"id": "a", "type": "url", "mesh": "m\x00o\x1fnt" + "x" * 300}, {"id": "s", "type": "spawn", "mesh": "boite"}, {"id": "c", "type": "url"}, {"id": "n", "type": "url", "mesh": 42}], "perso")
rapport(len(cz[0]["mesh"]) == 200 and cz[0]["mesh"].startswith("mont") and cz[1]["mesh"] == "" and cz[2]["mesh"] == "" and cz[3]["mesh"] == "42", "clean_zones valide mesh (longueur, caractères de contrôle, arrivée sans mesh)", [z["mesh"][:8] for z in cz])

# --zones-only / --config-only
zones0, cfg0, html0, glb0 = sha(site / "boite.zones.json"), sha(site / "boite.config.json"), sha(site / "boite.html"), sha(site / "boite.glb")
run("-o", site / "boite.html", "--config-only", "--wave", "2")
rapport(sha(site / "boite.zones.json") == zones0 and sha(site / "boite.config.json") != cfg0 and sha(site / "boite.html") == html0 and sha(site / "boite.glb") == glb0, "--config-only ne touche ni zones, ni coquille, ni glb")
(tmp / "zb.json").write_text(json.dumps(ZB), encoding="utf-8")
run("-o", site / "boite.html", "--config-only", "--zones", tmp / "zb.json")
z = json.loads((site / "boite.zones.json").read_text(encoding="utf-8"))
cfg = json.loads((site / "boite.config.json").read_text(encoding="utf-8"))
rapport(z[0]["label"] == "Boîte B" and cfg["zones"] == [], "--config-only --zones réécrit boite.zones.json (et la config reste sans zones)")
cfg1 = sha(site / "boite.config.json")
run("-o", site / "boite.html", "--zones-only", "--zones", tmp / "za.json")
rapport(json.loads((site / "boite.zones.json").read_text(encoding="utf-8"))[0]["label"] == "Boîte A" and sha(site / "boite.html") == html0 and sha(site / "boite.config.json") == cfg1, "--zones-only sur une page modulaire (config et coquille intactes)")
r = run("-o", site / "inconnue.html", "--zones-only", "--zones", tmp / "za.json", ok=False)
rapport(r.returncode != 0 and "modulaire" in (r.stdout + r.stderr), "--zones-only refuse une page non modulaire")
run(tmp / "boite.glb", "-o", site / "boite.html", "--modular", "--no-sea", "--sky-color", "336699")   # régénération sans source de zones
rapport(json.loads((site / "boite.zones.json").read_text(encoding="utf-8"))[0]["label"] == "Boîte A", "régénérer sans zones n'écrase pas boite.zones.json existant")


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


STUB = "window.__opened = []; window.open = (...a) => { window.__opened.push(String(a[0])); return null; };"


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        proc, port = serveur(site)
        base = f"http://127.0.0.1:{port}/"
        pages = []

        async def ouvrir(url, attendre=True):
            ctx = await br.new_context(locale="fr-FR", viewport={"width": 900, "height": 600})
            await ctx.add_init_script(STUB)
            pg = await ctx.new_page()
            pg.errs = []
            pg.on("pageerror", lambda e: pg.errs.append(str(e)))
            await pg.goto(url)
            if attendre:
                try:
                    await pg.wait_for_function("document.getElementById('msg') === null", timeout=15000)
                except Exception:
                    pass
                await pg.wait_for_timeout(700)
            pages.append(pg)
            return pg

        async def recharger(pg):
            await pg.reload()
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=15000)
            await pg.wait_for_timeout(700)

        async def curseur(pg, x, y):
            await pg.mouse.move(x, y)
            await pg.wait_for_timeout(110)
            return await pg.evaluate("document.querySelector('canvas').style.cursor")

        async def cliquer(pg, pt):
            await pg.evaluate("window.__opened.length = 0")
            await pg.mouse.click(*pt)
            await pg.wait_for_timeout(300)
            return await pg.evaluate("window.__opened")

        try:
            # ---- universalité : titre = salon, fond = skyColor
            pg = await ouvrir(base + "walk3.html")
            titre = await pg.title()
            fond = await pg.evaluate("getComputedStyle(document.body).backgroundColor")
            rapport(titre == "walk3" and not pg.errs, "titre = champ room de la config", (titre, pg.errs))
            pg = await ouvrir(base + "boite.html")
            fond = await pg.evaluate("getComputedStyle(document.body).backgroundColor")
            rapport(fond == "rgb(51, 102, 153)", "fond = skyColor de la config (336699)", fond)

            # ---- copie sous un autre nom (avec un espace et un accent) : rien n'est écrit en dur
            for ext in ("html", "glb", "config.json", "zones.json"):
                shutil.copy(site / f"boite.{ext}", site / f"copie région.{ext}")
            c = json.loads((site / "copie région.config.json").read_text(encoding="utf-8"))
            c["room"] = "Ma copie"; c["skyColor"] = 0x993333
            (site / "copie région.config.json").write_text(json.dumps(c), encoding="utf-8")
            pg = await ouvrir(base + "copie%20r%C3%A9gion.html")
            fond = await pg.evaluate("getComputedStyle(document.body).backgroundColor")
            rapport(await pg.evaluate("document.getElementById('msg') === null") and not pg.errs and await pg.title() == "Ma copie" and fond == "rgb(153, 51, 51)", "copie renommée : fonctionne, titre et fond tirés de SA config", (await pg.title(), fond, pg.errs))

            # ---- zones liées à un élément : survol, clic
            pg = await ouvrir(base + "boite.html")
            trouves = []
            for y in range(140, 441, 40):
                for x in range(440, 801, 40):
                    if await curseur(pg, x, y) == "pointer":
                        trouves.append((x, y))
            rapport(len(trouves) >= 2, "survol de l'élément lié : curseur main (voile traversable devant)", f"{len(trouves)} point(s)")
            if not trouves:
                return
            cx, cy = sum(t[0] for t in trouves) / len(trouves), sum(t[1] for t in trouves) / len(trouves)
            pt = min(trouves, key=lambda t: (t[0] - cx) ** 2 + (t[1] - cy) ** 2)
            rapport(await curseur(pg, 20, 20) != "pointer", "curseur normal hors de l'élément")
            await curseur(pg, *pt)
            rapport(await cliquer(pg, pt) == ["http://127.0.0.1/a"], "clic sur l'élément (à travers le voile traversable) : zone déclenchée")

            # ---- X.zones.json modifié puis rechargement
            (site / "boite.zones.json").write_text(json.dumps(ZB), encoding="utf-8")
            await recharger(pg)
            rapport(await cliquer(pg, pt) == ["http://127.0.0.1/b"], "modifier boite.zones.json puis recharger change les zones")

            # ---- secours : zones.json du dossier si X.zones.json est absent
            (site / "boite.zones.json").rename(site / "boite.zones.off")
            (site / "zones.json").write_text(json.dumps(FALLBACK), encoding="utf-8")
            await recharger(pg)
            rapport(await cliquer(pg, pt) == ["http://127.0.0.1/secours"], "X.zones.json absent : zones.json du dossier sert de secours")
            (site / "zones.json").write_text(json.dumps([dict(FALLBACK[0], target="http://127.0.0.1/secours2")]), encoding="utf-8")
            await recharger(pg)
            rapport(await cliquer(pg, pt) == ["http://127.0.0.1/secours2"], "modifier zones.json puis recharger change les zones")

            # ---- ni l'un ni l'autre : aucune zone, aucune erreur
            (site / "zones.json").unlink()
            await recharger(pg)
            rapport(await curseur(pg, *pt) != "pointer" and await cliquer(pg, pt) == [] and not pg.errs, "aucun fichier de zones : aucune zone, sans erreur", pg.errs)
            (site / "boite.zones.off").rename(site / "boite.zones.json")

            # ---- X.zones.json prioritaire sur zones.json
            (site / "zones.json").write_text(json.dumps(FALLBACK), encoding="utf-8")
            await recharger(pg)
            rapport(await cliquer(pg, pt) == ["http://127.0.0.1/b"], "X.zones.json présent l'emporte sur zones.json")
            (site / "zones.json").unlink()

            # ---- élément traversable : avec walkIgnore vide, le voile bloque le clic
            cfg_f = site / "boite.config.json"
            c = json.loads(cfg_f.read_text(encoding="utf-8")); ign = c["walkIgnore"]; c["walkIgnore"] = ""
            cfg_f.write_text(json.dumps(c), encoding="utf-8")
            await recharger(pg)
            rapport(await curseur(pg, *pt) != "pointer" and await cliquer(pg, pt) == [], "voile non traversable : il bloque le clic (contre-épreuve)")
            c["walkIgnore"] = ign
            cfg_f.write_text(json.dumps(c), encoding="utf-8")
            await recharger(pg)
            rapport(await cliquer(pg, pt) == ["http://127.0.0.1/b"], "voile traversable (walkIgnore) : le clic passe")

            # ---- touche E à moins de radius mètres de l'élément (bord à 4 m du point de départ)
            async def invite(pg):
                await pg.keyboard.press("f")
                await pg.wait_for_timeout(900)
                return await pg.evaluate("[!document.getElementById('zonePrompt').hidden, document.getElementById('zonePrompt').textContent]")
            (site / "boite.zones.json").write_text(json.dumps(ZB), encoding="utf-8")   # radius 8
            await recharger(pg)
            vis, txt = await invite(pg)
            await pg.evaluate("window.__opened.length = 0")
            await pg.keyboard.press("e")
            await pg.wait_for_timeout(300)
            rapport(vis and "Boîte B" in txt and txt.startswith("clic ou E :") and await pg.evaluate("window.__opened") == ["http://127.0.0.1/b"], "touche E à 4 m de l'élément (radius 8) : invite « clic ou E : … » et déclenchement (v36 : comme avant la v35)", (vis, txt))
            (site / "boite.zones.json").write_text(json.dumps([dict(ZB[0], radius=2)]), encoding="utf-8")
            await recharger(pg)
            vis, txt = await invite(pg)
            await pg.evaluate("window.__opened.length = 0")
            await pg.keyboard.press("e")
            await pg.wait_for_timeout(300)
            rapport(not vis and await pg.evaluate("window.__opened") == [], "touche E à 4 m de l'élément (radius 2) : trop loin, rien", (vis, txt))

            # ---- portail déclenché en s'approchant de l'élément
            (site / "boite.zones.json").write_text(json.dumps([dict(PORTAIL[0], target=base + "walk3.html")]), encoding="utf-8")
            await recharger(pg)
            await pg.keyboard.press("f")
            await pg.wait_for_timeout(900)
            rapport("walk3.html" not in pg.url, "portail à l'approche : pas déclenché au départ (élément à 4 m, radius 2)", pg.url)
            await pg.keyboard.down("d")
            t0 = time.time()
            while time.time() - t0 < 12 and "walk3.html" not in pg.url:
                await pg.wait_for_timeout(250)
            await pg.keyboard.up("d")
            rapport("walk3.html" in pg.url, "portail à l'approche : déclenché en marchant vers l'élément", pg.url)
            (site / "boite.zones.json").write_text(json.dumps(ZA), encoding="utf-8")

            # ---- viewer : deux exports côte à côte, structure modulaire, liaison
            await test_coquille_commune(br)
            await test_viewer(br, pages)
            await test_liaison(br)
        finally:
            proc.kill()
            await br.close()


async def test_coquille_commune(br):
    """Une seule coquille (index.html) pour plusieurs régions : glb2html.py --shared-shell, ?region=NOM, paramètres refusés."""
    from urllib.parse import quote
    site2 = tmp / "site2"
    reg = tmp / "regions2.json"
    zb = [{"id": "arr", "type": "spawn", "x": 0, "y": 5, "z": 0, "yaw": 0}]
    zw = [{"id": "arr", "type": "spawn", "x": 0, "y": 40, "z": 0, "yaw": 0}]
    (tmp / "zb2.json").write_text(json.dumps(zb), encoding="utf-8")
    (tmp / "zw2.json").write_text(json.dumps(zw), encoding="utf-8")
    comm = ["--shared-shell", "--register", reg]
    r = run(tmp / "boite.glb", "-o", site2 / "boite.html", *comm, "--room", "boite", "--region-name", "Boîte", "--region-xy", "1000,1000", "--zones", tmp / "zb2.json", "--no-sea")
    run(DATA / "walk3.glb", "-o", site2 / "walk3.html", *comm, "--room", "walk3", "--region-name", "Marche", "--region-xy", "1001,1000", "--zones", tmp / "zw2.json")
    run("-o", site2 / "boite.html", "--config-only", "--shared-shell", "--register", reg, "--room", "boite", "--region-name", "Boîte", "--region-xy", "1000,1000")   # la carte de boite connaît walk3
    noms = sorted(p.name for p in site2.iterdir())
    rapport(noms == ["boite.config.json", "boite.glb", "boite.zones.json", "default.json", "index.html", "lib", "walk3.config.json", "walk3.glb", "walk3.zones.json"], "--shared-shell : par région seulement X.glb, X.config.json, X.zones.json ; une coquille index.html et un lib/ partagés", noms)
    rapport((site2 / "index.html").read_bytes() == coques["boite"], "la coquille commune est identique, octet pour octet, à celle des pages modulaires")
    rapport("index.html?region=boite" in r.stdout, "la ligne [OK] donne l'adresse index.html?region=NOM", r.stdout[-300:])
    entrees = {e["room"]: e for e in json.loads(reg.read_text(encoding="utf-8"))}
    rapport(entrees["boite"]["url"] == "index.html?region=boite" and entrees["walk3"]["url"] == "index.html?region=walk3", "--register écrit COQUILLE.html?region=NOM dans regions.json", {k: v["url"] for k, v in entrees.items()})
    cfgb = json.loads((site2 / "boite.config.json").read_text(encoding="utf-8"))
    rapport(len(cfgb["map"]) == 2 and cfgb["room"] == "boite", "boite.config.json contient la carte des deux régions", len(cfgb["map"]))
    # une coquille existante n'est jamais écrasée (les autres régions la partagent)
    coque0 = (site2 / "index.html").read_bytes()
    (site2 / "index.html").write_bytes(coque0 + b"<!-- locale -->")
    r = run(DATA / "walk3.glb", "-o", site2 / "walk3.html", *comm, "--room", "walk3", "--region-name", "Marche", "--region-xy", "1001,1000")
    rapport((site2 / "index.html").read_bytes() == coque0 + b"<!-- locale -->" and "AVERTISSEMENT" in r.stderr, "coquille existante et différente : conservée, avec avertissement", r.stderr[-200:])
    (site2 / "index.html").write_bytes(coque0)
    zw0 = sha(site2 / "walk3.zones.json")
    rapport(json.loads((site2 / "walk3.zones.json").read_text(encoding="utf-8"))[0]["id"] == "arr" and zw0 == sha(site2 / "walk3.zones.json"), "régénérer sans zones n'écrase pas walk3.zones.json")
    # nom de région refusé aussi côté script
    r = run(tmp / "boite.glb", "-o", site2 / ".cache.html", "--shared-shell", ok=False)
    rapport(r.returncode != 0 and "refusé" in (r.stdout + r.stderr) and not (site2 / ".cache.glb").exists(), "le script refuse un nom de région que la coquille refuserait")

    proc, port = serveur(site2)
    base = f"http://127.0.0.1:{port}/"
    try:
        async def ouvrir(url, attendre=True):
            ctx = await br.new_context(locale="fr-FR", viewport={"width": 900, "height": 600})
            pg = await ctx.new_page()
            pg.ctx = ctx
            pg.errs, pg.reqs = [], []
            pg.on("pageerror", lambda e: pg.errs.append(str(e)))
            pg.on("request", lambda q: pg.reqs.append(q.url))
            await pg.goto(url)
            if attendre:
                try:
                    await pg.wait_for_function("document.getElementById('msg') === null", timeout=20000)
                except Exception:
                    pass
                await pg.wait_for_timeout(500)
            return pg

        # ---- deux régions, une seule coquille
        pa = await ouvrir(base + "index.html?region=boite")
        pb = await ouvrir(base + "index.html?region=walk3")
        rapport(await pa.title() == "boite" and await pb.title() == "walk3" and not pa.errs and not pb.errs, "index.html?region=boite et ?region=walk3 : chacune charge SA config (titre = salon), sans erreur", (await pa.title(), await pb.title(), pa.errs, pb.errs))
        await pb.ctx.close()   # les rendus logiciels se gênent : une page à la fois autant que possible
        rapport(all(base + n in pa.reqs for n in ("boite.config.json", "boite.glb", "boite.zones.json")) and not any("walk3" in u for u in pa.reqs), "région boite : demande boite.config.json, boite.glb, boite.zones.json, rien de walk3", [u for u in pa.reqs if "boite" in u or "walk3" in u])
        # NOM.html accepté (extension retirée)
        pc = await ouvrir(base + "index.html?region=boite.html")
        rapport(await pc.title() == "boite" and not pc.errs, "?region=boite.html : l'extension est retirée", (await pc.title(), pc.errs))
        await pc.ctx.close()

        # ---- région simple inchangée : sans paramètre, nom de la page
        shutil.copy(site2 / "boite.config.json", site2 / "index.config.json")
        shutil.copy(site2 / "boite.glb", site2 / "index.glb")
        pi = await ouvrir(base + "index.html")
        rapport(await pi.title() == "boite" and not pi.errs and base + "index.config.json" in pi.reqs, "sans paramètre region : comportement d'avant (index.html charge index.config.json, index.glb)", (await pi.title(), pi.errs))
        await pi.ctx.close()
        for f in ("index.config.json", "index.glb"):
            (site2 / f).unlink()
        # v37 : sans fichier correspondant, la coquille essaie default.json (écrit par glb2html.py à la première région) ; sans lui, un message clair
        pd = await ouvrir(base + "index.html")
        rapport(await pd.title() == "boite", "v37 : sans paramètre ni index.config.json, default.json désigne la région à ouvrir", await pd.title())
        await pd.ctx.close()
        djson = (site2 / "default.json").read_bytes()
        (site2 / "default.json").unlink()
        pn = await ouvrir(base + "index.html", attendre=False)
        await pn.wait_for_timeout(1200)
        msg = await pn.evaluate("document.getElementById('msg') && document.getElementById('msg').textContent")
        rapport(msg and "index.config.json" in msg and "default.json" in msg and "?region=" in msg, "sans paramètre, sans fichier correspondant ni default.json : message d'erreur clair (v37)", msg)
        await pn.ctx.close()
        (site2 / "default.json").write_bytes(djson)
        pm = await ouvrir(base + "index.html?region=inexistante")
        msg = await pm.evaluate("document.getElementById('msg') && document.getElementById('msg').textContent")
        rapport(msg and "inexistante.config.json" in msg and "introuvable" in msg, "?region=inexistante : message d'erreur clair (fichier cité)", msg)
        await pm.ctx.close()

        # ---- paramètres refusés : message dans la page, aucune requête réseau vers config, zones ou glb
        refuses = {"../x": "../x", "https://autre-site/x": "https://autre-site/x", "a\\b": "a\\b", "vide": "", ".secret": ".secret", "a..b": "a..b",
                   "a?b": "a?b", "a#b": "a#b", "a:b": "a:b", "//autre-site/x": "//autre-site/x", ".html": ".html", "tout point": ".."}
        for nom, val in refuses.items():
            pr = await ouvrir(base + "index.html?region=" + quote(val, safe="") , attendre=False)
            await pr.wait_for_timeout(600)
            msg = await pr.evaluate("document.getElementById('msg') && document.getElementById('msg').textContent")
            interdit = [u for u in pr.reqs if u.endswith((".config.json", ".glb", ".zones.json", "zones.json")) or not u.startswith(base)]
            rapport(bool(msg) and "refusé" in msg and not interdit, f"paramètre refusé ({nom}) : message dans la page, aucune requête config/zones/glb ni vers un autre site", (msg, interdit))
            await pr.ctx.close()
        for nom, brut in {"..%2fx encodé": "%2e%2e%2fx", "..\\x encodé": "..%5Cx", "https encodé": "https%3A%2F%2Fautre-site%2Fx"}.items():
            pr = await ouvrir(base + "index.html?region=" + brut, attendre=False)
            await pr.wait_for_timeout(600)
            msg = await pr.evaluate("document.getElementById('msg') && document.getElementById('msg').textContent")
            interdit = [u for u in pr.reqs if u.endswith((".config.json", ".glb", ".zones.json", "zones.json")) or not u.startswith(base)]
            rapport(bool(msg) and "refusé" in msg and not interdit, f"paramètre refusé ({nom}, pourcentage dans l'adresse) : aucune requête config/zones/glb", (msg, interdit))
            await pr.ctx.close()
        pr = await ouvrir(base + "index.html?region", attendre=False)
        await pr.wait_for_timeout(600)
        msg = await pr.evaluate("document.getElementById('msg') && document.getElementById('msg').textContent")
        rapport(bool(msg) and "refusé" in msg and not [u for u in pr.reqs if u.endswith((".json", ".glb"))], "?region sans valeur : refusé", msg)
        await pr.ctx.close()

        # ---- carte : « vous êtes ici », puis visite de l'autre région (#spawn= après la query string)
        await pa.click("#mapBtn", timeout=60000)
        await pa.wait_for_timeout(400)
        cartes = await pa.evaluate("[...document.querySelectorAll('#mapGrid > *')].map(e => e.innerText)")
        ici = [c for c in cartes if "vous êtes ici" in c]
        rapport(len(cartes) == 2 and len(ici) == 1 and "Boîte" in ici[0] and any("visiter" in c and "Marche" in c for c in cartes), "carte : « vous êtes ici » sur la région courante seulement (même coquille, autre ?region=)", cartes)
        await pa.locator("#mapGrid > *", has_text="Marche").click()
        try:
            await pa.wait_for_function("location.search === '?region=walk3'", timeout=8000)
        except Exception:
            pass
        rapport(pa.url.startswith(base + "index.html?region=walk3#spawn=default&name="), "carte : l'adresse visitée est index.html?region=walk3#spawn=default&name=…", pa.url)
        await pa.wait_for_function("document.getElementById('msg') === null", timeout=20000)
        await pa.wait_for_timeout(1200)
        rapport(await pa.title() == "walk3" and await pa.evaluate("window.__viewer.walking") and not pa.errs, "arrivée par la carte : la région chargée est walk3, en promenade", (await pa.title(), pa.errs))
        await pa.click("#mapBtn", timeout=60000)
        await pa.wait_for_timeout(400)
        cartes = await pa.evaluate("[...document.querySelectorAll('#mapGrid > *')].map(e => e.innerText)")
        ici = [c for c in cartes if "vous êtes ici" in c]
        rapport(len(ici) == 1 and "Marche" in ici[0], "carte, côté walk3 : « vous êtes ici » suit la région", cartes)

        # ---- portails (déclenchés en marchant vers l'élément « boite », comme plus haut) : même région, puis autre région de la même coquille
        await pa.ctx.close()
        spawn = zb[0]
        portail = lambda cible: [spawn, {"id": "p", "type": "portal", "label": "P", "trigger": "enter", "target": cible, "spawn": "arr", "mesh": "boite", "radius": 2}]

        async def marcher(pp, jusqu_a):
            await pp.keyboard.press("f")
            await pp.wait_for_timeout(900)
            await pp.keyboard.down("d")
            t0 = time.time()
            while time.time() - t0 < 14 and not jusqu_a():
                await pp.wait_for_timeout(250)
            await pp.keyboard.up("d")

        (site2 / "boite.zones.json").write_text(json.dumps(portail("index.html?region=boite")), encoding="utf-8")
        pp = await ouvrir(base + "index.html?region=boite")
        await marcher(pp, lambda: False)   # ~14 s de marche : le portail de la même région ne doit PAS naviguer
        toast = await pp.evaluate("document.getElementById('toast').hidden ? '' : document.getElementById('toast').textContent")
        rapport(pp.url == base + "index.html?region=boite" and "introuvable" not in toast and not pp.errs, "portail vers la même région (?region identique) : pas de navigation, arrivée trouvée", (pp.url, toast, pp.errs))
        await pp.ctx.close()
        (site2 / "boite.zones.json").write_text(json.dumps(portail("index.html?region=walk3")), encoding="utf-8")
        pp = await ouvrir(base + "index.html?region=boite")
        await marcher(pp, lambda: "region=walk3" in pp.url)
        rapport(pp.url.startswith(base + "index.html?region=walk3#spawn=arr&name="), "portail vers une autre région de la même coquille : …?region=walk3#spawn=arr&name=…", pp.url)
        await pp.wait_for_function("document.getElementById('msg') === null", timeout=60000)
        await pp.wait_for_timeout(1500)
        rapport(await pp.title() == "walk3" and await pp.evaluate("window.__viewer.walking") and not pp.errs, "arrivée par portail : walk3 chargée, en promenade", (await pp.title(), pp.errs))
        await pp.ctx.close()
    finally:
        proc.kill()


async def test_viewer(br, pages):
    ctx = await br.new_context(locale="fr-FR", viewport={"width": 1300, "height": 800}, accept_downloads=True)
    pg = await ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto((DIST / "glb-viewer.html").as_uri())
    await pg.set_input_files("#fGlb", str(tmp / "boite.glb"))
    await pg.wait_for_function("!document.getElementById('bZip').disabled", timeout=20000)
    await pg.wait_for_timeout(800)
    a, b = await pg.evaluate("[document.getElementById('bHtml'), document.getElementById('bZip')].map(e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.width]; })")
    rapport(abs(a[1] - b[1]) < 3 and b[0] > a[0] and not await pg.evaluate("document.getElementById('bHtml').disabled") and "Exporter HTML autonome" in await pg.inner_text("#bHtml") and "Exporter la structure modulaire (.zip)" in await pg.inner_text("#bZip"), "viewer : deux boutons côte à côte", (a, b))

    # zones importées, profil perso
    zi = [{"id": "z1", "type": "url", "label": "Boîte", "target": "http://127.0.0.1/x", "radius": 3}]
    (tmp / "zv.json").write_text(json.dumps(zi), encoding="utf-8")
    await pg.select_option("#profileSel", "perso")
    await pg.set_input_files("#fZones", str(tmp / "zv.json"))
    await pg.wait_for_timeout(300)

    # liaison : le clic ignore le voile traversable
    await pg.click("#zoneList summary")
    await pg.get_by_role("button", name="Lier à un élément").click()
    centre = await pg.evaluate("""(() => { const v = window.__viewer, i = v.meshInfo('boite'); const p = new v.camera.position.constructor(...i.center).project(v.camera); const r = v.renderer.domElement.getBoundingClientRect(); return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; })()""")
    await pg.mouse.click(*centre)
    await pg.wait_for_timeout(300)
    z = (await pg.evaluate("window.__viewer.getZones()"))[0]
    rapport(z["mesh"] == "boite" and abs(z["x"] - 6) < 0.05 and abs(z["z"]) < 0.05, "Lier à un élément : lie la boîte, pas le voile traversable", z)
    rapport("liée" in await pg.inner_text("#stat") and "boite" in await pg.inner_text("#zoneList"), "Lier : message et liste mis à jour")
    await pg.get_by_role("button", name="Délier").click()
    z = (await pg.evaluate("window.__viewer.getZones()"))[0]
    rapport(z["mesh"] == "", "Délier : la zone n'est plus liée", z)
    await pg.evaluate("window.__viewer.setCfg({ walkIgnore: '' })")      # contre-épreuve : sans traversable, c'est le voile qui serait lié
    await pg.get_by_role("button", name="Lier à un élément").click()
    await pg.mouse.click(*centre)
    await pg.wait_for_timeout(300)
    z = (await pg.evaluate("window.__viewer.getZones()"))[0]
    rapport(z["mesh"] == "door_voile", "contre-épreuve : sans walkIgnore, le clic lie le voile", z)
    await pg.evaluate("window.__viewer.setCfg({ walkIgnore: 'door, porte' })")
    await pg.get_by_role("button", name="Lier à un élément").click()
    await pg.mouse.click(*centre)
    await pg.wait_for_timeout(300)
    rapport((await pg.evaluate("window.__viewer.getZones()"))[0]["mesh"] == "boite", "relié à la boîte après remise de walkIgnore")

    # export autonome (inchangé) : une seule page qui s'ouvre depuis le disque
    async with pg.expect_download() as d:
        await pg.click("#bHtml")
    dl = await d.value
    auto = tmp / "export_autonome.html"
    await dl.save_as(str(auto))
    pa = await (await br.new_context(locale="fr-FR", viewport={"width": 900, "height": 600})).new_page()
    ea = []
    pa.on("pageerror", lambda e: ea.append(str(e)))
    await pa.goto(auto.as_uri())
    await pa.wait_for_function("document.getElementById('msg') === null", timeout=30000)
    rapport(await pa.evaluate("document.getElementById('msg') === null") and not ea and dl.suggested_filename.endswith("Offline perso.html"), "export HTML autonome : s'ouvre depuis le disque, sans erreur", (ea, dl.suggested_filename))
    rapport("<script type=\"application/octet-stream\" id=\"glb\">" in auto.read_text(encoding="utf-8") and "lib/three" not in auto.read_text(encoding="utf-8"), "export HTML autonome : toujours un fichier unique (glb et three.js intégrés)")

    # export modulaire
    async with pg.expect_download() as d:
        await pg.click("#bZip")
    dl = await d.value
    zp = tmp / "export.zip"
    await dl.save_as(str(zp))
    with zipfile.ZipFile(zp) as zf:
        rapport(zf.testzip() is None, "zip valide (CRC)")
        noms = set(zf.namelist())
        attendus = {"index.html", "boite.glb", "boite.config.json", "boite.zones.json"}
        rapport(attendus <= noms and all(n.startswith("lib/three-0.160.0/") for n in noms - attendus) and "lib/three-0.160.0/draco/draco_decoder.wasm" in noms and "lib/three-0.160.0/meshopt_decoder.module.js" in noms, "zip : index.html (coquille commune), X.glb, X.config.json, X.zones.json, lib/three-0.160.0/ (draco/ compris)", sorted(noms))
        rapport(zf.read("index.html") == (site / "boite.html").read_bytes(), "index.html du zip identique octet pour octet à la coquille de glb2html.py --modular")
        rapport(zf.read("boite.glb") == (tmp / "boite.glb").read_bytes(), "X.glb du zip = le modèle chargé")
        lib_ok = all(zf.read(n) == (site / n).read_bytes() for n in noms if n.startswith("lib/"))
        rapport(lib_ok, "lib/ du zip identique à celle de glb2html.py --modular", [n for n in noms if n.startswith("lib/") and zf.read(n) != (site / n).read_bytes()])
        zc = json.loads(zf.read("boite.config.json")); zz = json.loads(zf.read("boite.zones.json"))
        cli = json.loads((site / "boite.config.json").read_text(encoding="utf-8"))
        rapport(zc["zones"] == [] and zc["room"] == "boite" and zz and zz[0]["mesh"] == "boite" and set(cli) <= set(zc), "zip : config sans zones (mêmes clés que le script), zones dans X.zones.json avec mesh", (sorted(set(cli) ^ set(zc)), zz))
        out = tmp / "site_zip"
        zf.extractall(out)
    proc, port = serveur(out)
    try:
        pz = await (await br.new_context(locale="fr-FR", viewport={"width": 900, "height": 600})).new_page()
        ez = []
        pz.on("pageerror", lambda e: ez.append(str(e)))
        await pz.goto(f"http://127.0.0.1:{port}/index.html?region=boite")
        await pz.wait_for_function("document.getElementById('msg') === null", timeout=30000)
        rapport(await pz.evaluate("document.getElementById('msg') === null") and not ez and await pz.title() == "boite", "structure du zip servie en http : la page se charge, sans erreur", (ez, await pz.title()))
    finally:
        proc.kill()
    # générateur de ligne de commande : même structure que le zip
    await pg.check("#cmdModular")
    await pg.check("#cmdShared")
    await pg.fill("#cmdDest", "Region.html")
    await pg.click("#bCmd")
    cmd = await pg.input_value("#cmdOut")
    note = await pg.inner_text("#cmdNote")
    rapport("--shared-shell" in cmd and "--modular" not in cmd and "-o Region.html" in cmd.replace('"', "").replace("'", "") and "index.html?region=NOM" in note, "ligne de commande : « Coquille commune » donne --shared-shell (et plus --modular)", (cmd, note))
    await pg.uncheck("#cmdShared")
    await pg.click("#bCmd")
    cmd = await pg.input_value("#cmdOut")
    rapport("--modular" in cmd and "--shared-shell" not in cmd, "ligne de commande : sans la case, --modular comme avant", cmd)
    rapport(not errs, "viewer : aucune erreur JavaScript", errs)


async def test_liaison(br):
    """Lier à un élément sur un modèle dont la racine est décalée et mise à l'échelle (×2), avec un voile traversable devant
    la boîte et un sol géant : la boîte englobante doit être celle de la boîte (8 m), le mode est exclusif, un élément > 30 m est refusé."""
    make_glb(tmp / "decale.glb", [("sol", "sol", (-40, -0.2, -40, 40, 0, 40), 1.0), ("boite", "mur", (4, 0, -2, 8, 4, 2), 1.0),
                                  ("door_voile", "verre", (2, 0, 4, 10, 6, 4.05), 0.3)], racine=((500, 20, -300), 2.0))
    ctx = await br.new_context(locale="fr-FR", viewport={"width": 1300, "height": 800})
    pg = await ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto((DIST / "glb-viewer.html").as_uri())
    await pg.set_input_files("#fGlb", str(tmp / "decale.glb"))
    await pg.wait_for_function("!document.getElementById('bZip').disabled", timeout=20000)
    await pg.wait_for_timeout(800)
    await pg.select_option("#profileSel", "perso")
    await pg.set_input_files("#fZones", str(tmp / "zv.json"))
    await pg.wait_for_timeout(300)
    proj = """(([nom, f]) => { const v = window.__viewer, i = v.meshInfo(nom); const P = v.camera.position.constructor;
        const p = new P(...[0, 1, 2].map(k => i.min[k] + (i.max[k] - i.min[k]) * f[k])).project(v.camera); const r = v.renderer.domElement.getBoundingClientRect();
        return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; })"""
    centre = await pg.evaluate(proj + "(['boite', [0.5, 0.5, 0.5]])")
    sol = await pg.evaluate(proj + "(['sol', [0.15, 1, 0.5]])")
    cible = lambda: pg.evaluate("window.__viewer.controls.target.toArray().map(v => Math.round(v * 1000) / 1000)")
    t0 = await cible()
    holes0 = await pg.evaluate("[window.__viewer.cfg.holeX, window.__viewer.cfg.holeZ]")
    await pg.click("#zoneList summary")
    await pg.get_by_role("button", name="Lier à un élément").click()
    # le sol géant (160 m) est refusé, y compris au double-clic ; rien d'autre n'agit
    await pg.mouse.dblclick(*sol)
    await pg.wait_for_timeout(400)
    z = (await pg.evaluate("window.__viewer.getZones()"))[0]
    rapport(z["mesh"] == "" and "trop grand" in await pg.inner_text("#stat"), "liaison : un élément de plus de 30 m (sol géant) est refusé avec un message", (z["mesh"], await pg.inner_text("#stat")))
    rapport(await cible() == t0 and await pg.evaluate("[window.__viewer.cfg.holeX, window.__viewer.cfg.holeZ]") == holes0, "liaison exclusive : le double-clic ne déplace ni la cible (repère d'atterrissage) ni le trou", (t0, await cible()))
    # la boîte, derrière le voile traversable
    await pg.mouse.dblclick(*centre)
    await pg.wait_for_timeout(900)
    z = (await pg.evaluate("window.__viewer.getZones()"))[0]
    info = await pg.evaluate("window.__viewer.meshInfo('boite')")
    rapport(z["mesh"] == "boite", "racine décalée et mise à l'échelle, voile et sol géant : c'est la boîte qui est liée", z["mesh"])
    rapport(all(abs(v - 8) < 0.05 for v in info["size"]), "boîte englobante = taille de la boîte (8 × 8 × 8 m avec l'échelle ×2)", info["size"])
    mesures = await pg.evaluate("""(() => { const v = window.__viewer, B = v.camera.position.constructor, out = [];
        v.scene.traverse(c => { if (c.type === 'Box3Helper') out.push(c.box.getSize(new B()).toArray()); });
        return { contours: out }; })()""")
    rapport(mesures["contours"] and all(all(7.95 < v < 8.2 for v in c) for c in mesures["contours"]), "contour fil de fer affiché à la taille de la boîte, aucun cube parasite", mesures)
    rapport(abs(z["x"] - info["center"][0]) < 0.01 and abs(z["z"] - info["center"][2]) < 0.01 and abs(z["y"] - info["min"][1]) < 0.01, "zone posée au pied de l'élément, en coordonnées monde", z)
    stat = await pg.inner_text("#stat")
    rapport("boite" in stat and "8 × 8 × 8 m" in stat, "le viewer affiche le nom choisi et sa taille en mètres", stat)
    rapport(await cible() == t0 and await pg.evaluate("[window.__viewer.cfg.holeX, window.__viewer.cfg.holeZ]") == holes0, "après la liaison, le 2e clic du double-clic ne déplace rien", (t0, await cible()))
    rapport(not errs, "liaison : aucune erreur JavaScript", errs)
    await ctx.close()


asyncio.run(main())
print("\nRÉSULTAT :", "ÉCHEC (%d)" % bad if bad else "tout est passé")
sys.exit(1 if bad else 0)
