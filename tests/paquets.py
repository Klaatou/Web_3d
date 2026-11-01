#!/usr/bin/env python3
"""Paquets prets a l'emploi (galerie-photos, region-simple) : fabrication, contenu, ouverture dans Chromium sans tete.

Fabrique avec fabriquer_paquets.py (dans un dossier temporaire), puis pour chaque zip : structure et fichiers attendus, JSON valides, zones et region
coherentes avec leurs fichiers, aucune adresse file:// ni nom d'hote reel dans les textes, presence eteinte dans les config, .bat/.ps1 en ASCII et CRLF,
copie fidele de presence_server.py. Navigateur : la galerie s'ouvre et le panneau d'aide ouvre galerie.html ; la region s'ouvre et la promenade pose les yeux sur le sol.

Prerequis : python build.py ; pip install playwright. Variables facultatives : THREE_DIR (racine d'un paquet npm three, hors ligne), CHROMIUM. Lancer : python tests/paquets.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, re, socket, subprocess, sys, tempfile, time, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_paquets_"))
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


cmd = [sys.executable, str(ROOT / "fabriquer_paquets.py"), "--out", str(tmp / "zips")] + (["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else [])
r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
rapport(r.returncode == 0, "fabrication des zips", (r.stdout + r.stderr)[-300:])
if r.returncode:
    sys.exit(1)
cible = {}
for nom in ("galerie-photos", "region-simple"):
    zp = tmp / "zips" / f"{nom}.zip"
    rapport(zp.is_file(), f"{nom}.zip existe")
    zipfile.ZipFile(zp).extractall(tmp / "x")
    p = tmp / "x" / nom
    cible[nom] = p
    site = p / "site"
    for f in ("site/index.html", "site/default.json", "site/favicon.ico", "site/lib/three-0.160.0/three.module.js", "site/lib/three-0.160.0/draco/draco_decoder.wasm",
              "presence/presence_server.py", "presence/LISEZMOI.txt", "LISEZMOI.txt", "VERSION.txt"):
        rapport((p / f).is_file(), f"{nom} : {f}")
    # region ouverte par default.json : ses trois fichiers
    reg = json.loads((site / "default.json").read_text(encoding="utf-8"))["region"]
    rapport((site / f"{reg}.glb").is_file() and (site / f"{reg}.config.json").is_file(), f"{nom} : default.json designe « {reg} », avec son .glb et son .config.json")
    cfg = json.loads((site / f"{reg}.config.json").read_text(encoding="utf-8"))
    rapport(cfg.get("presenceUrl") == "" and cfg.get("chat") is False, f"{nom} : presence eteinte dans la config", (cfg.get("presenceUrl"), cfg.get("chat")))
    zf = site / f"{reg}.zones.json"
    zones = json.loads(zf.read_text(encoding="utf-8")) if zf.is_file() else []
    absentes = [z["target"] for z in zones if z.get("type") == "image" and not (site / "medias" / z["target"]).is_file()]
    rapport(not absentes, f"{nom} : chaque zone image a son fichier dans medias", absentes)
    # aide des visiteurs (aide.html), documentation du createur, zone d'aide, script de renommage
    doc = "galerie.html" if nom == "galerie-photos" else "lisezmoi.html"
    rapport((site / "aide.html").is_file() and (site / doc).is_file(), f"{nom} : site/aide.html et site/{doc}")
    aide = (site / "aide.html").read_text(encoding="utf-8")
    rapport(f'href="{doc}"' in aide and 'id="doc-createur"' in aide, f"{nom} : aide.html commence par le cadre qui renvoie vers {doc}")
    liens = [z for z in zones if z.get("link")]
    rapport(len(liens) == 1 and liens[0]["link"] == "aide.html" and liens[0]["target"] == "aide.jpg", f"{nom} : une zone image « aide.jpg » ouvre aide.html", [(z["id"], z.get("link")) for z in liens])
    rapport(all((p / f).is_file() for f in (f"renommer-{'galerie' if nom == 'galerie-photos' else 'region'}.bat", f"renommer-{'galerie' if nom == 'galerie-photos' else 'region'}.ps1")), f"{nom} : script de renommage")
    rapport("PARAMETRES" not in (p / "LISEZMOI.txt").read_text(encoding="utf-8"), f"{nom} : le LISEZMOI ne cite plus d'ancien document")
    # copie fidele du serveur de presence (fins de ligne ignorees)
    lf = lambda b: b.replace(b"\r\n", b"\n")
    rapport(lf((p / "presence" / "presence_server.py").read_bytes()) == lf((DIST / "presence_server.py").read_bytes()), f"{nom} : presence_server.py identique a dist/")
    rapport("__VERSION_PRESENCE__" not in (p / "presence" / "LISEZMOI.txt").read_text(encoding="utf-8"), f"{nom} : version du serveur de presence ecrite dans sa notice")
    # textes lisibles par un debutant : pas de file://, pas de nom d'hote reel
    mauvais = []
    for f in p.rglob("*"):
        if f.is_file() and f.suffix.lower() in (".txt", ".md", ".html") and "lib" not in f.parts and f.name != "index.html":   # index.html = code de la page (il detecte file: pour afficher son message)
            t = f.read_text(encoding="utf-8")
            if "file://" in t or re.search(r"ts\.net|tailce", t):
                mauvais.append(f.name)
    rapport(not mauvais, f"{nom} : aucun file:// ni nom d'hote reel dans les textes", mauvais)
    # lanceurs : ASCII et CRLF
    for f in list(p.glob("*.bat")) + list(p.glob("*.ps1")):
        b = f.read_bytes()
        rapport(all(c < 128 for c in b) and b"\r\n" in b and b"\n" not in b.replace(b"\r\n", b""), f"{nom} : {f.name} en ASCII et CRLF")
    lp = next(p.glob("lancer-*.ps1")).read_text(encoding="ascii")
    rapport("8000..8020" in lp and "'site'" in lp, f"{nom} : le lanceur sert site\\ sur les ports 8000 a 8020")


def serveur(d):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    return subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL), port


async def main():
    from playwright.async_api import async_playwright
    for nom in cible:   # un petit crochet pour lire la scene (copie de test, pas le paquet)
        idx = cible[nom] / "site" / "index.html"
        idx.write_text(idx.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    procs = {n: serveur(cible[n] / "site") for n in cible}
    time.sleep(1.5)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            for nom, (proc, port) in procs.items():
                pg = await br.new_page(locale="fr-FR", viewport={"width": 1200, "height": 700}); errs = []
                await pg.add_init_script("window.__opened = []; window.open = (u) => { window.__opened.push(String(u)); return null; };")
                pg.on("pageerror", lambda e: errs.append(str(e)))
                await pg.goto(f"http://127.0.0.1:{port}/")
                try:
                    await pg.wait_for_function("document.getElementById('msg') === null", timeout=90000); ok = True
                except Exception:
                    ok = False
                await pg.wait_for_timeout(3500)
                rapport(ok and not errs, f"{nom} : la page s'ouvre sans erreur", errs[:2])
                if nom == "galerie-photos":
                    await pg.keyboard.press("h"); await pg.wait_for_timeout(300)
                    sx, sy = await pg.evaluate("""([x, y, z]) => { const v = window.__v; v.camera.updateMatrixWorld(true); const p = v.camera.position.clone().set(x, y, z).project(v.camera), r = v.renderer.domElement.getBoundingClientRect(); return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; }""", [1.7, 12.26, 0.285])
                    await pg.mouse.move(sx, sy); await pg.wait_for_timeout(300); await pg.mouse.click(sx, sy); await pg.wait_for_timeout(600)
                    op = await pg.evaluate("window.__opened")
                    rapport(len(op) == 1 and op[0].endswith("/aide.html"), "galerie-photos : un clic sur le panneau d'aide du comptoir ouvre aide.html", op)
                else:
                    await pg.keyboard.press("f"); await pg.wait_for_function("window.__v.walking", timeout=10000); await pg.wait_for_timeout(800)
                    pos = await pg.evaluate("window.__v.camera.position.toArray()")
                    rapport(abs(pos[0]) < 0.01 and abs(pos[2]) < 0.01 and not (-14.5 < pos[0] < -4.5 and -10 < pos[2] < -2), "region-simple : le point d'arrivee en promenade est hors de la maison d'exemple", pos)
                    await pg.evaluate("window.__v.teleportTo([20, 0, 30], 0)"); await pg.wait_for_timeout(1500)
                    y = await pg.evaluate("window.__v.camera.position.y")
                    rapport(abs(y - 16.7) < 0.3, "region-simple : en promenade, les yeux sont a 1,7 m au-dessus du sol (sol a 15 m)", y)
                    await pg.evaluate("window.__v.teleportTo([1.5, 0, -6], 1.5708)"); await pg.wait_for_timeout(1800)
                    sx, sy = await pg.evaluate("""([x, y, z]) => { const v = window.__v; v.camera.updateMatrixWorld(true); const p = v.camera.position.clone().set(x, y, z).project(v.camera), r = v.renderer.domElement.getBoundingClientRect(); return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; }""", [-4.48, 17.2, -6.0])
                    await pg.evaluate("window.__opened.length = 0")
                    await pg.mouse.move(sx, sy); await pg.wait_for_timeout(300); await pg.mouse.click(sx, sy); await pg.wait_for_timeout(700)
                    op = await pg.evaluate("window.__opened")
                    rapport(len(op) == 1 and op[0].endswith("/aide.html"), "region-simple : en promenade face a la maison, un clic sur le panneau d'aide du mur ouvre aide.html", op)
                await pg.close()
            await br.close()
    finally:
        for proc, _ in procs.values():
            proc.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
