#!/usr/bin/env python3
"""Editeur de zones du viewer : nom par langue (labels) et titre de lien (linkTitle) (1.13.11) (Chromium sans tete).

Viewer (glb-viewer.html) : la fiche de chaque zone propose « Nom affiche en francais » et « Nom affiche en anglais » ; les zones qui ouvrent un lien
(url, tableau avec lien, ecran video a action lien) proposent « Titre du lien », les autres non. Les valeurs sont gardees dans la zone (getZones),
la saisie d'une langue ne perd pas l'autre, vider les deux champs retire la cle (sens inverse). Bout en bout : les zones sorties de l'editeur sont donnees a
glb2html.py, la page generee garde les memes valeurs et le fichier X.zones.json porte labels et linkTitle, seulement quand ils sont remplis.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/editeur_labels.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_edlab_"))
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


def zones_depart():
    """cinq zones : lien, tableau avec lien, ecran video a action lien, ecran video sans action, portail, arrivee"""
    return [
        {"id": "u", "type": "url", "label": "Lien", "target": "https://exemple.invalid/a", "x": 0, "y": 0, "z": 0, "shape": "ring", "radius": 2},
        {"id": "i", "type": "image", "label": "Tableau", "target": "photo", "link": "https://exemple.invalid/b", "x": 6, "y": 2, "z": 0, "w": 1.2, "h": 0},
        {"id": "v", "type": "video", "label": "Ecran", "target": "clip.mp4", "act": "url", "atarget": "https://exemple.invalid/c", "x": -6, "y": 2, "z": 0, "radius": 20, "w": 2.4, "h": 0},
        {"id": "w", "type": "video", "label": "Ecran nu", "target": "clip.mp4", "x": -12, "y": 2, "z": 0, "radius": 20, "w": 2.4, "h": 0},
        {"id": "p", "type": "portal", "label": "Portail", "target": "", "spawn": "arr", "x": 12, "y": 0, "z": 0, "shape": "ring", "radius": 2, "trigger": "enter"},
        {"id": "arr", "type": "spawn", "label": "Arrivee", "x": 0, "y": 0, "z": 10},
    ]


def generer(site, nom, zones):
    (tmp / (nom + ".json")).write_text(json.dumps(zones), encoding="utf-8")
    out = site / (nom + ".html")
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--zones", str(tmp / (nom + ".json")), "--no-sea", *vend],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
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
            pg = await br.new_page(locale="fr-FR", viewport={"width": 1000, "height": 900}); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{port}/glb-viewer.html")
            await pg.wait_for_function("window.__viewer", timeout=60000)
            await pg.set_input_files("#fGlb", str(tmp / "sol.glb"))
            await pg.wait_for_function("window.__viewer.model", timeout=60000)
            (tmp / "z.json").write_text(json.dumps(zones_depart()), encoding="utf-8")
            await pg.set_input_files("#fZones", str(tmp / "z.json"))
            await pg.wait_for_function("window.__viewer.getZones().length === 6", timeout=10000)
            await pg.wait_for_timeout(600)
            Z = lambda: pg.evaluate("Object.fromEntries(window.__viewer.getZones().map(z => [z.id, z]))")
            ids = ["u", "i", "v", "w", "p", "arr"]

            async def ouvrir(zid):
                i = ids.index(zid)
                if not await pg.evaluate("document.querySelectorAll('#zoneList details')[%d].open" % i):
                    await pg.locator("#zoneList details summary").nth(i).click(); await pg.wait_for_timeout(500)
                return pg.locator("#zoneList details").nth(i)

            async def etiquettes(zid):
                d = await ouvrir(zid)
                return await d.locator("div.row label").all_inner_texts()

            async def champ(zid, etiquette, valeur):
                d = await ouvrir(zid)
                ligne = d.locator("div.row").filter(has=pg.locator("label", has_text=etiquette)).first
                await ligne.locator("input").fill(str(valeur)); await ligne.locator("input").dispatch_event("change"); await pg.wait_for_timeout(400)

            FR, EN, LT = "Nom affiché en français", "Nom affiché en anglais", "Titre du lien"
            # presence des champs : nom par langue partout, titre du lien seulement quand la zone ouvre un lien
            attendu = {"u": True, "i": True, "v": True, "w": False, "p": False, "arr": False}
            for zid in ids:
                e = await etiquettes(zid)
                rapport(any(t.startswith(FR) for t in e) and any(t.startswith(EN) for t in e), f"zone {zid} : les champs « {FR} » et « {EN} » apparaissent", e)
                rapport(any(t.startswith(LT) for t in e) == attendu[zid], f"zone {zid} : « {LT} » {'present' if attendu[zid] else 'absent'}", e)
            # saisie : francais puis anglais (la seconde ne doit pas effacer la premiere), titres des trois liens
            await champ("u", FR, "Page d'accueil"); await champ("u", EN, "Home page")
            await champ("i", FR, "Photo"); await champ("i", EN, "Picture"); await champ("i", LT, "Une photo de la region")
            await champ("u", LT, "Titre de la page")
            await champ("v", LT, "Film d'accueil")
            await champ("arr", FR, "Entree")
            await champ("w", FR, "x" * 70)
            zs = await Z()
            rapport(zs["u"].get("labs") == {"fr": "Page d'accueil", "en": "Home page"} and zs["u"].get("label") == "Lien",
                    "editeur : francais puis anglais : les deux noms sont gardes, `label` intact", {k: zs["u"].get(k) for k in ("label", "labs")})
            rapport(zs["i"].get("labs") == {"fr": "Photo", "en": "Picture"} and zs["i"].get("ltitle") == "Une photo de la region",
                    "editeur : tableau : noms par langue et titre du lien gardes", {k: zs["i"].get(k) for k in ("labs", "ltitle")})
            rapport(zs["u"].get("ltitle") == "Titre de la page" and zs["v"].get("ltitle") == "Film d'accueil" and zs["v"].get("act") == "url",
                    "editeur : lien et ecran video a action lien : titre du lien garde", {k: (zs[k].get("ltitle"), zs[k].get("act")) for k in "uv"})
            rapport(zs["arr"].get("labs") == {"fr": "Entree"}, "editeur : point d'arrivee : un seul nom par langue suffit", zs["arr"].get("labs"))
            rapport(len((zs["w"].get("labs") or {}).get("fr", "")) <= 60, "editeur : un nom de plus de 60 caracteres est coupe a 60", zs["w"].get("labs"))
            # sens inverse : vider un nom garde l'autre, vider les deux retire la cle ; vider le titre retire la cle
            await champ("u", FR, ""); zs = await Z()
            rapport(zs["u"].get("labs") == {"en": "Home page"}, "editeur : francais vide : l'anglais reste", zs["u"].get("labs"))
            await champ("u", EN, ""); await champ("u", LT, ""); zs = await Z()
            rapport(not zs["u"].get("labs") and not zs["u"].get("ltitle"), "editeur : tout vide : plus de labs ni de ltitle", {k: zs["u"].get(k) for k in ("labs", "ltitle")})
            await champ("w", FR, "")
            # le nom de la langue de la page est montre (zoneLabel) : francais dans ce viewer
            nom = await pg.evaluate("(() => { const z = window.__viewer.getZones().find(q => q.id === 'i'); return window.__viewer.zoneLabel(z); })()")
            rapport(nom == "Photo", "viewer : zoneLabel donne le nom de la langue du viewer", nom)
            sortie = await pg.evaluate("window.__viewer.getZones()")
            rapport(not errs, "viewer : aucune erreur JavaScript", errs)
            await pg.close()

            # page generee : memes zones
            generer(site, "sortie", sortie)
            p2 = await br.new_page(viewport={"width": 1000, "height": 700}); e2 = []
            p2.on("pageerror", lambda e: e2.append(str(e)))
            await p2.goto(f"http://127.0.0.1:{port}/sortie.html")
            await p2.wait_for_function("window.__v && window.__v.model", timeout=60000)
            js = {z["id"]: z for z in await p2.evaluate("window.__v.getZones()")}
            rapport(js["i"].get("labs") == {"fr": "Photo", "en": "Picture"} and js["i"].get("ltitle") == "Une photo de la region" and js["v"].get("ltitle") == "Film d'accueil"
                    and js["arr"].get("labs") == {"fr": "Entree"} and not js["u"].get("labs") and not js["u"].get("ltitle"),
                    "page generee : noms par langue et titres de lien gardes, rien d'ajoute aux zones videes", {k: (js[k].get("labs"), js[k].get("ltitle")) for k in ids})
            rapport(not e2, "page generee : aucune erreur JavaScript", e2)
            await br.close()
    finally:
        proc.kill()
    # fichier zones au nouveau format : labels et linkTitle seulement quand ils sont remplis
    (tmp / "w.json").write_text(json.dumps(sortie), encoding="utf-8")
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(site / "Mod.html"), "--zones", str(tmp / "w.json"), "--shared-shell", "--no-sea", *vend],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    ecrit = {z["id"]: z for z in json.loads((site / "Mod.zones.json").read_text(encoding="utf-8"))} if (site / "Mod.zones.json").exists() else {}
    rapport(r.returncode == 0 and ecrit.get("i", {}).get("labels") == {"fr": "Photo", "en": "Picture"} and ecrit["i"].get("linkTitle") == "Une photo de la region"
            and ecrit.get("v", {}).get("linkTitle") == "Film d'accueil" and ecrit.get("arr", {}).get("labels") == {"fr": "Entree"}
            and "labels" not in ecrit.get("u", {}) and "linkTitle" not in ecrit.get("u", {}) and "linkTitle" not in ecrit.get("w", {}) and "labels" not in ecrit.get("w", {})
            and "linkTitle" not in ecrit.get("p", {}),
            "Mod.zones.json : labels et linkTitle ecrits quand ils sont remplis, absents sinon (zones videes, ecran nu, portail)", ecrit)
    shutil.rmtree(tmp, ignore_errors=True)
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
