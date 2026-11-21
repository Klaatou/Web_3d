#!/usr/bin/env python3
"""Editeur de zones du viewer : menu « Action de l'ecran » d'un ecran video (1.12.42) (Chromium sans tete).

Viewer (glb-viewer.html) : une zone video ouverte dans la liste ; le menu d'action propose aucune, lien, portail, commande ; chaque choix montre ses champs
(adresse, fenetre flottante, point d'arrivee, confirmation, distance de declenchement) et les valeurs sont gardees dans la zone (getZones) ; repasser sur « aucune »
retire l'action (sens inverse). Bout en bout : les zones sorties de l'editeur sont donnees a glb2html.py, la page generee garde les memes zones et le fichier
X.zones.json ecrit au nouveau format porte link / portal / ha et actionRadius, sans cone ni trigger.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/editeur_video_action.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_edvact_"))
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


def ecran(id_, x):
    return {"id": id_, "type": "video", "label": id_, "target": "clip.mp4", "x": x, "y": 17, "z": -5, "radius": 20, "w": 2.4, "h": 0}


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
            (tmp / "z.json").write_text(json.dumps([ecran("a", 0), ecran("b", 6), ecran("c", -6), ecran("d", 12)]), encoding="utf-8")
            await pg.set_input_files("#fZones", str(tmp / "z.json"))
            await pg.wait_for_function("window.__viewer.getZones().length === 4", timeout=10000)
            await pg.wait_for_timeout(600)
            Z = lambda: pg.evaluate("Object.fromEntries(window.__viewer.getZones().map(z => [z.id, z]))")

            async def ouvrir(i):
                if not await pg.evaluate("document.querySelectorAll('#zoneList details')[%d].open" % i):
                    await pg.locator("#zoneList details summary").nth(i).click(); await pg.wait_for_timeout(500)
                return pg.locator("#zoneList details").nth(i)

            async def action(i, valeur):
                d = await ouvrir(i)
                await d.locator("select").filter(has=pg.locator("option[value=portal]")).select_option(valeur); await pg.wait_for_timeout(500)

            async def champ(i, etiquette, valeur):
                """champ texte ou nombre dont l'etiquette commence par `etiquette`"""
                d = await ouvrir(i)
                ligne = d.locator("div.row").filter(has=pg.locator("label", has_text=etiquette)).first
                await ligne.locator("input").fill(str(valeur)); await ligne.locator("input").dispatch_event("change"); await pg.wait_for_timeout(500)

            async def case(i, etiquette):
                d = await ouvrir(i)
                await d.locator("div.row").filter(has=pg.locator("label", has_text=etiquette)).first.locator("input").check(); await pg.wait_for_timeout(500)

            # lien : adresse + fenetre flottante
            await action(0, "url")
            d0 = await ouvrir(0)
            etiq = await d0.locator("div.row label").all_inner_texts()
            rapport(any("fenêtre flottante" in t for t in etiq) and any(t.startswith("Adresse web") for t in etiq), "action « lien » : les champs « Adresse web » et « fenetre flottante » apparaissent", etiq)
            await champ(0, "Adresse web", "https://exemple.invalid/v"); await case(0, "fenêtre flottante")
            # portail : destination, arrivee, distance
            await action(1, "portal"); await champ(1, "Page de destination", "https://exemple.invalid/p.html"); await champ(1, "Point d'arrivée", "arr"); await champ(1, "Distance de déclenchement", 5)
            # commande : adresse, confirmation, distance par defaut
            await action(2, "ha"); await champ(2, "Adresse du webhook", "http://exemple.invalid/api"); await case(2, "Demander confirmation")
            # lien puis retour a « aucune » : l'action est retiree
            await action(3, "url"); await action(3, "")
            zs = await Z()
            rapport(zs["a"].get("act") == "url" and zs["a"].get("atarget") == "https://exemple.invalid/v" and zs["a"].get("frame") is True and zs["a"]["trigger"] == "click",
                    "editeur : action « lien » : act url, adresse et fenetre flottante gardees, declenchement au clic", {k: zs["a"].get(k) for k in ("act", "atarget", "frame", "trigger")})
            rapport(zs["b"].get("act") == "portal" and zs["b"].get("atarget") == "https://exemple.invalid/p.html" and zs["b"].get("spawn") == "arr" and zs["b"].get("aradius") == 5 and zs["b"]["trigger"] == "enter",
                    "editeur : action « portail » : destination, point d'arrivee, distance 5 m, declenchement a l'approche", {k: zs["b"].get(k) for k in ("act", "atarget", "spawn", "aradius", "trigger")})
            rapport(zs["c"].get("act") == "ha" and zs["c"].get("atarget") == "http://exemple.invalid/api" and zs["c"].get("confirm") is True and zs["c"]["trigger"] == "enter",
                    "editeur : action « commande » : adresse, confirmation, declenchement a l'approche", {k: zs["c"].get(k) for k in ("act", "atarget", "confirm", "trigger")})
            rapport("act" not in zs["d"] and "atarget" not in zs["d"] and zs["d"]["trigger"] == "click",
                    "editeur : lien puis « aucune » : l'action est retiree (sens inverse)", {k: zs["d"].get(k) for k in ("act", "atarget", "trigger")})
            sortie = await pg.evaluate("window.__viewer.getZones()")
            rapport(not errs, "viewer : aucune erreur JavaScript", errs)
            await pg.close()

            # page generee : memes zones, fichier zones au nouveau format
            generer(site, "sortie", sortie)
            p2 = await br.new_page(viewport={"width": 1000, "height": 700}); e2 = []
            p2.on("pageerror", lambda e: e2.append(str(e)))
            await p2.goto(f"http://127.0.0.1:{port}/sortie.html")
            await p2.wait_for_function("window.__v && window.__v.model", timeout=60000)
            js = {z["id"]: z for z in await p2.evaluate("window.__v.getZones()")}
            rapport(all(js[k].get("act") == zs[k].get("act") and js[k].get("atarget") == zs[k].get("atarget") and js[k].get("aradius") == zs[k].get("aradius") for k in "abcd"),
                    "page generee : les actions des quatre ecrans sont gardees", {k: (js[k].get("act"), js[k].get("atarget"), js[k].get("aradius")) for k in "abcd"})
            rapport(not e2, "page generee : aucune erreur JavaScript", e2)
            await br.close()
    finally:
        proc.kill()
    # fichier zones au nouveau format
    (tmp / "w.json").write_text(json.dumps(sortie), encoding="utf-8")
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(site / "Mod.html"), "--zones", str(tmp / "w.json"), "--shared-shell", "--no-sea", *vend],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    ecrit = {z["id"]: z for z in json.loads((site / "Mod.zones.json").read_text(encoding="utf-8"))} if (site / "Mod.zones.json").exists() else {}
    rapport(r.returncode == 0 and ecrit.get("a", {}).get("link") == "https://exemple.invalid/v" and ecrit["a"].get("frame") is True
            and ecrit.get("b", {}).get("portal") == "https://exemple.invalid/p.html" and ecrit["b"].get("actionRadius") == 5 and ecrit["b"].get("spawn") == "arr"
            and ecrit.get("c", {}).get("ha") == "http://exemple.invalid/api" and ecrit["c"].get("confirm") is True and "actionRadius" not in ecrit["c"]
            and all("cone" not in z and "trigger" not in z and "type" not in z for z in ecrit.values()) and "link" not in ecrit.get("d", {}) and "portal" not in ecrit.get("d", {}),
            "Mod.zones.json : link / portal / ha et actionRadius ecrits au nouveau format, sans cone, trigger ni type ; l'ecran sans action n'en a pas", ecrit)
    shutil.rmtree(tmp, ignore_errors=True)
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
