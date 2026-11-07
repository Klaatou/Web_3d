#!/usr/bin/env python3
"""Paquets prets a l'emploi (galerie-photos, region-simple) : fabrication, contenu, ouverture dans Chromium sans tete.

Fabrique avec fabriquer_paquets.py (dans un dossier temporaire), puis pour chaque zip : structure et fichiers attendus, JSON valides, zones et region
coherentes avec leurs fichiers, aucune adresse file:// ni nom d'hote reel dans les textes, presence eteinte dans les config, .bat/.ps1 en ASCII et CRLF, .sh/.command en ASCII, LF et executables, lanceur et renommage Linux/macOS essayes en direct (sh),
copie fidele de presence_server.py. Navigateur : la galerie s'ouvre et le panneau d'aide ouvre galerie.html ; la region s'ouvre et la promenade pose les yeux sur le sol.

Prerequis : python build.py ; pip install playwright. Variables facultatives : THREE_DIR (racine d'un paquet npm three, hors ligne), CHROMIUM. Lancer : python tests/paquets.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, re, socket, subprocess, sys, tempfile, time, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_paquets_"))
echecs = 0


def jpeg_taille(b):
    """(largeur, hauteur) d'un JPEG, lue dans son premier marqueur SOF ; None si illisible"""
    i = 2
    while i + 9 < len(b) and b[0:2] == b"\xff\xd8":
        if b[i] != 0xFF:
            return None
        m = b[i + 1]
        if m in (0xC0, 0xC1, 0xC2):
            return (b[i + 7] << 8 | b[i + 8], b[i + 5] << 8 | b[i + 6])
        i += 2 + (b[i + 2] << 8 | b[i + 3])
    return None


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
    for f in ("site/index.html", "site/carte.html", "site/regions.json", "site/vignette.jpg", "site/default.json", "site/favicon.ico", "site/lib/three-0.160.0/three.module.js", "site/lib/three-0.160.0/draco/draco_decoder.wasm",
              "presence/presence_server.py", "presence/README.txt", "README.txt", "VERSION.txt"):
        rapport((p / f).is_file(), f"{nom} : {f}")
    # region ouverte par default.json : ses trois fichiers
    reg = json.loads((site / "default.json").read_text(encoding="utf-8"))["region"]
    rapport((site / f"{reg}.glb").is_file() and (site / f"{reg}.config.json").is_file(), f"{nom} : default.json designe « {reg} », avec son .glb et son .config.json")
    cfg = json.loads((site / f"{reg}.config.json").read_text(encoding="utf-8"))
    rapport(cfg.get("version") == (ROOT / "VERSION").read_text(encoding="utf-8").strip(), f"{nom} : la version de la config est celle de la release (fenetre Aide)", (cfg.get("version"), (ROOT / "VERSION").read_text(encoding="utf-8").strip()))
    rapport(cfg.get("presenceUrl") == "" and cfg.get("chat") is False, f"{nom} : presence eteinte dans la config", (cfg.get("presenceUrl"), cfg.get("chat")))
    # 1.4.13 : la carte du paquet : une fiche (celle de la region), une vignette carree de 320 x 320 pixels
    rj = json.loads((site / "regions.json").read_text(encoding="utf-8")) if (site / "regions.json").is_file() else {}
    fiches = rj.get("regions", []); f0 = fiches[0] if fiches else {}
    rapport(len(fiches) == 1 and f0.get("id") == reg and f0.get("room") == cfg.get("room") == reg and f0.get("url") == f"index.html?region={reg}" and f0.get("thumb") == "vignette.jpg" and f0.get("presence") == "",
            f"{nom} : regions.json : une fiche, celle de « {reg} » (id, salon, adresse relative, vignette, presence eteinte)", f0)
    jb = (site / "vignette.jpg").read_bytes() if (site / "vignette.jpg").is_file() else b""
    rapport(jb[:2] == b"\xff\xd8" and jpeg_taille(jb) == (320, 320) and len(jb) < 60 * 1024, f"{nom} : vignette.jpg : JPEG de 320 x 320 pixels, moins de 60 Ko", (jpeg_taille(jb), len(jb)))
    zf = site / f"{reg}.zones.json"
    zones = json.loads(zf.read_text(encoding="utf-8")) if zf.is_file() else []
    def cible_fichier(t):   # 1.6.18 : une cible sans extension ("30") se resout comme dans la page : jpg, jpeg, png, webp, gif, avif, dans cet ordre, dans medias/ ; avec extension : ce fichier
        if "." in t: return (site / "medias" / t) if (site / "medias" / t).is_file() else None
        return next((site / "medias" / f"{t}.{e}" for e in ("jpg", "jpeg", "png", "webp", "gif", "avif") if (site / "medias" / f"{t}.{e}").is_file()), None)
    absentes = [z["target"] for z in zones if z.get("type") == "image" and not cible_fichier(z["target"])]
    hop = [z for z in zones if z.get("target") in ("hop", "hop.jpg")]
    jh = cible_fichier("hop").read_bytes() if cible_fichier("hop") else b""
    rapport(len(hop) == 1 and hop[0].get("type") == "image" and str(hop[0].get("link", "")).startswith("hop://") and jh[:2] == b"\xff\xd8" and jpeg_taille(jh) == (1200, 600),
            f"{nom} : zone image « zhop » : lien hop://, image hop.jpg (« Lien vers OpenSim », JPEG de 1200 x 600)", (hop, jpeg_taille(jh)))
    rapport(not absentes, f"{nom} : chaque zone image a son fichier dans medias", absentes)
    # aide des visiteurs (aide.html), documentation du createur, zone d'aide, script de renommage
    doc = "galerie.html" if nom == "galerie-photos" else "readme.html"
    rapport((site / "aide.html").is_file() and (site / doc).is_file(), f"{nom} : site/aide.html et site/{doc}")
    aide = (site / "aide.html").read_text(encoding="utf-8")
    dc = (site / doc).read_text(encoding="utf-8")
    rapport(dc.count("carte.html") >= 2 and dc.count("vignette.jpg") >= 2 and dc.count("regions.json</code>") >= 4 and "27.6" not in dc, f"{nom} : {doc} decrit la carte du paquet (FR et EN), le renommage de la fiche, et renvoie au manuel § 11.6", (dc.count("carte.html"), dc.count("vignette.jpg"), "27.6" in dc))
    rapport(f'href="{doc}"' in aide and 'id="doc-createur"' in aide, f"{nom} : aide.html commence par le cadre qui renvoie vers {doc}")
    liens = [z for z in zones if z.get("link") and z.get("target") not in ("hop", "hop.jpg")]
    rapport(len(liens) == 1 and liens[0]["link"] == "aide.html" and liens[0]["target"] in ("aide", "aide.jpg"), f"{nom} : une zone image « aide.jpg » ouvre aide.html", [(z["id"], z.get("link")) for z in liens])
    rapport(all((p / f).is_file() for f in (f"renommer-{'galerie' if nom == 'galerie-photos' else 'region'}.bat", f"renommer-{'galerie' if nom == 'galerie-photos' else 'region'}.ps1")), f"{nom} : script de renommage")
    rd = (p / "README.txt").read_text(encoding="utf-8")
    rapport("PARAMETRES" not in rd and not (p / "LISEZMOI.txt").exists(), f"{nom} : README.txt (plus de LISEZMOI.txt ni d'ancien document)")
    rapport("aide.html" in rd and doc in rd and "panneau" in rd and "carte.html" in rd and "vignette.jpg" in rd, f"{nom} : README.txt donne l'adresse de l'aide, celle de {doc}, celle de la carte (carte.html, vignette.jpg) et l'emplacement du panneau d'aide")
    rapport("hop.jpg" in rd and "hop.jpg" in dc and "hop://" in dc and "yaw" in dc and "zhop" in dc and "PROCEDURES.md" in dc, f"{nom} : README.txt et {doc} expliquent comment personnaliser le panneau hop (image, position, yaw, lien)")
    # copie fidele du serveur de presence (fins de ligne ignorees)
    lf = lambda b: b.replace(b"\r\n", b"\n")
    rapport(lf((p / "presence" / "presence_server.py").read_bytes()) == lf((DIST / "presence_server.py").read_bytes()), f"{nom} : presence_server.py identique a dist/")
    rapport("__VERSION_PRESENCE__" not in (p / "presence" / "README.txt").read_text(encoding="utf-8"), f"{nom} : version du serveur de presence ecrite dans sa notice")
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
    rapport("CODE SOURCE" in lp and "releases/latest" in lp and "index.html" in lp and "exit 1" in lp, f"{nom} : le lanceur Windows refuse le dossier source du depot et indique le paquet a telecharger")


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
                # 1.4.13 : carte.html : une tuile, qui mene a la region, avec sa vignette chargee
                regn = json.loads((cible[nom] / "site" / "default.json").read_text(encoding="utf-8"))["region"]
                cp = await br.new_page(locale="fr-FR", viewport={"width": 900, "height": 600}); cerrs = []
                cp.on("pageerror", lambda e: cerrs.append(str(e)))
                await cp.goto(f"http://127.0.0.1:{port}/carte.html")
                try:
                    await cp.wait_for_function("document.querySelectorAll('a.tile').length > 0", timeout=20000)
                except Exception:
                    pass
                await cp.wait_for_timeout(800)
                tuiles = await cp.evaluate("[...document.querySelectorAll('a.tile')].map(a => ({ href: a.getAttribute('href'), w: a.querySelector('img') ? a.querySelector('img').naturalWidth : -1, nom: a.innerText }))")
                rapport(len(tuiles) == 1 and tuiles[0]["href"].split("#")[0].rsplit("/", 1)[-1] == f"index.html?region={regn}" and tuiles[0]["href"].endswith("#spawn=default") and tuiles[0]["w"] == 320 and not cerrs, f"{nom} : carte.html : une tuile qui mene a la region, avec sa vignette (320 px) chargee", (tuiles, cerrs[:2]))
                liens = await cp.evaluate("[...document.querySelectorAll('#foot a')].map(a => a.getAttribute('href'))")   # 1.6.10 : mention de Web_3d en pied de la carte et dans aide.html
                rapport(liens == ["https://github.com/Klaatou/Web_3d"], f"{nom} : carte.html : le pied de page renvoie au depot Web_3d", liens)
                aide_txt = (cible[nom] / "site" / "aide.html").read_text(encoding="utf-8")
                rapport(aide_txt.count('href="https://github.com/Klaatou/Web_3d"') == 2, f"{nom} : aide.html : la mention de Web_3d, en francais et en anglais", aide_txt.count('href="https://github.com/Klaatou/Web_3d"'))
                await cp.close()
                if nom == "galerie-photos":
                    await pg.evaluate("(() => { const b = document.getElementById('aboutClose'), o = document.getElementById('aboutOverlay'); if (b && o && !o.hidden) b.click(); })()")   # le paquet a un fichier about : le panneau « A propos » s'ouvre a l'entree et capterait le clic
                    await pg.keyboard.press("h"); await pg.wait_for_timeout(300)
                    sx, sy = await pg.evaluate("""([x, y, z]) => { const v = window.__v; v.camera.updateMatrixWorld(true); const p = v.camera.position.clone().set(x, y, z).project(v.camera), r = v.renderer.domElement.getBoundingClientRect(); return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; }""", [1.7, 12.26, 0.285])
                    await pg.mouse.move(sx, sy); await pg.wait_for_timeout(300); await pg.mouse.click(sx, sy); await pg.wait_for_timeout(600)
                    op = await pg.evaluate("window.__opened")
                    diag = await pg.evaluate("([x, y]) => { const v = window.__v, zs = v.getZones ? v.getZones() : [], pk = v.zonePickAt ? v.zonePickAt(x, y) : null; return { fenetre: [innerWidth, innerHeight, devicePixelRatio], about_ouvert: (document.getElementById('aboutOverlay') || {}).hidden === false, en_promenade: !!v.walking, zones: zs.length, zone_sous_clic: pk ? pk.id : null, images: (v.imageDiag ? v.imageDiag() : []).map(d => d.id + ':' + (d.loaded || 'non charge')) }; }", [sx, sy])   # 1.6.11 : zones connues, zone sous le clic, images chargees
                    rapport(len(op) == 1 and op[0].endswith("/aide.html"), "galerie-photos : un clic sur le panneau d'aide du comptoir ouvre aide.html", {"ouvert": op, "clic": [round(sx), round(sy)], **diag})
                else:
                    await pg.keyboard.press("f"); await pg.wait_for_function("window.__v.walking", timeout=10000); await pg.wait_for_timeout(800)
                    pos = await pg.evaluate("window.__v.camera.position.toArray()")
                    cible_xz = json.loads((cible[nom] / "site" / "region.config.json").read_text(encoding="utf-8"))["target"]   # 1.6.9 : la promenade commence au point cible de la region (22,5 ; 18,5 depuis que la maison a ete deplacee), plus en (0, 0)
                    rapport(abs(pos[0] - cible_xz[0]) < 0.01 and abs(pos[2] - cible_xz[2]) < 0.01 and not (-14.5 < pos[0] < -4.5 and -10 < pos[2] < -2), "region-simple : le point d'arrivee en promenade est le point cible de la region, hors de la maison d'exemple", pos)
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



def essai_lanceurs_unix():
    """lanceurs et renommage Linux/macOS : fichiers, droits dans le zip, syntaxe, lancement reel (sous Linux et macOS seulement)"""
    import http.client, select, shutil, signal
    noms = (("galerie-photos", "galerie"), ("region-simple", "region"))
    lisez = ROOT / "paquets" / "README.txt"
    rapport(lisez.is_file() and "releases/latest" in lisez.read_text(encoding="ascii") and "Download ZIP" in lisez.read_text(encoding="ascii"), "paquets/README.txt : dit que ce sont des sources et ou telecharger le paquet")
    for nom, court in noms:
        modes = {pathlib.PurePosixPath(i.filename).name: (i.external_attr >> 16) & 0o777 for i in zipfile.ZipFile(tmp / "zips" / f"{nom}.zip").infolist()}
        for f in (f"lancer-{court}.sh", f"renommer-{court}.sh", f"lancer-{court}.command", f"renommer-{court}.command"):
            b = (cible[nom] / f).read_bytes()
            rapport(b.startswith(b"#!/bin/sh\n") and all(c < 128 for c in b) and b"\r" not in b, f"{nom} : {f} en ASCII, LF, #!/bin/sh")
            rapport(modes.get(f) == 0o755, f"{nom} : {f} executable (0755) dans le zip", oct(modes.get(f) or 0))
    if os.name == "nt" or not shutil.which("sh"):
        print("[--]    lanceurs Linux/macOS : essai en direct ignore (pas de shell sh sur cette machine)")
        return
    for nom, court in noms:
        p = cible[nom]
        for f in (f"lancer-{court}.sh", f"renommer-{court}.sh", f"lancer-{court}.command", f"renommer-{court}.command"):
            r = subprocess.run(["sh", "-n", str(p / f)], capture_output=True, text=True)
            rapport(r.returncode == 0, f"{nom} : sh -n {f}", r.stderr[-200:])
        # lance depuis le dossier SOURCE du depot (ni index.html ni lib) : message clair, code 3, pas de serveur
        r = subprocess.run(["sh", str(ROOT / "paquets" / nom / f"lancer-{court}.sh")], capture_output=True, text=True, timeout=20, env=dict(os.environ, BROWSER="true"))
        rapport(r.returncode == 3 and "CODE SOURCE" in r.stdout and "releases/latest" in r.stdout and "localhost:" not in r.stdout, f"{nom} : lance depuis le dossier source du depot, le lanceur sh dit de telecharger le paquet (pas de 404)", (r.returncode, r.stdout[-200:]))
        # lancement reel : deux lanceurs a la suite doivent prendre deux ports differents
        env = dict(os.environ, BROWSER="true")
        procs, ports = [], []
        try:
            for _ in range(2):
                pr = subprocess.Popen(["sh", str(p / f"lancer-{court}.sh")], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, cwd=p)
                procs.append(pr)
                ok = select.select([pr.stdout], [], [], 20)[0]
                ligne = pr.stdout.readline() if ok else ""
                m = re.search(r"localhost:(\d+)", ligne)
                ports.append(int(m.group(1)) if m else None)
            rapport(all(ports) and ports[0] != ports[1] and all(8000 <= x <= 8020 for x in ports if x), f"{nom} : le lanceur sh choisit un port de 8000 a 8020, puis le suivant s'il est pris", ports)
            if ports[0]:
                def get(chemin):
                    c = http.client.HTTPConnection("localhost", ports[0], timeout=10); c.request("GET", chemin)
                    r = c.getresponse(); r.read(); out = (r.status, r.getheader("Content-Type") or ""); c.close(); return out
                s, ct = get("/"); rapport(s == 200 and "text/html" in ct, f"{nom} : lanceur sh : la page est servie (text/html)", (s, ct))
                s, ct = get(f"/{court}.glb"); rapport(s == 200 and ct == "model/gltf-binary", f"{nom} : lanceur sh : le GLB est servi en model/gltf-binary", (s, ct))
                s, ct = get("/lib/three-0.160.0/three.module.js"); rapport(s == 200 and "javascript" in ct, f"{nom} : lanceur sh : les modules JavaScript sont servis en javascript", (s, ct))
                s, ct = get("/lib/three-0.160.0/draco/draco_decoder.wasm"); rapport(s == 200 and ct == "application/wasm", f"{nom} : lanceur sh : le decodeur Draco est servi en application/wasm", (s, ct))
                rapport(get("/../README.txt")[0] == 404 and get("/%2e%2e/README.txt")[0] == 404 and get("/absent.txt")[0] == 404, f"{nom} : lanceur sh : rien en dehors de site/, 404 pour un fichier absent")
        finally:
            for pr in procs:
                pr.send_signal(signal.SIGINT)
            fins = []
            for pr in procs:
                try:
                    pr.wait(timeout=8); fins.append(True)
                except subprocess.TimeoutExpired:
                    pr.kill(); fins.append(False)
            rapport(all(fins), f"{nom} : Ctrl+C arrete le serveur", fins)
        # renommage : nom refuse, renommage complet, conflit, retour au nom d'origine
        d = tmp / "renommage" / nom
        shutil.copytree(p, d)
        site = d / "site"
        def lancer(*args, entree=None):
            return subprocess.run(["sh", str(d / f"renommer-{court}.sh"), *args], capture_output=True, text=True, input=entree)
        avant = sorted(x.name for x in site.iterdir())
        r = lancer("a b"); rapport(r.returncode == 1 and sorted(x.name for x in site.iterdir()) == avant, f"{nom} : renommage : un nom avec espace est refuse sans rien changer", r.stdout[-200:])
        r = lancer(court); rapport(r.returncode == 0 and "deja le nom actuel" in r.stdout, f"{nom} : renommage : le meme nom ne fait rien", r.stdout[-200:])
        r = lancer("Essai_1")
        cfg = (site / "Essai_1.config.json").read_text(encoding="utf-8") if (site / "Essai_1.config.json").is_file() else ""
        rapport(r.returncode == 0 and all((site / f"Essai_1{e}").is_file() for e in (".glb", ".config.json", ".zones.json")) and not (site / f"{court}.glb").exists()
                and json.loads((site / "default.json").read_text(encoding="utf-8")) == {"region": "Essai_1"} and f'"room": "Essai_1"' in cfg, f"{nom} : renommage : fichiers, default.json et salon (room) changes", r.stdout[-300:])
        fr1 = json.loads((site / "regions.json").read_text(encoding="utf-8"))["regions"][0] if (site / "regions.json").is_file() else {}
        rapport(fr1.get("id") == "Essai_1" and fr1.get("room") == "Essai_1" and fr1.get("url") == "index.html?region=Essai_1" and fr1.get("thumb") == "vignette.jpg" and (site / "vignette.jpg").is_file(),
                f"{nom} : renommage : la fiche de regions.json suit (id, salon, adresse), la vignette garde son nom", fr1)
        (site / "Autre.glb").write_bytes(b"x")
        r = lancer("Autre"); rapport(r.returncode == 1 and (site / "Essai_1.glb").is_file(), f"{nom} : renommage : un fichier du nouveau nom existe deja, abandon sans rien changer", r.stdout[-200:])
        (site / "Autre.glb").unlink()
        r = lancer(entree=f"{court}\n")
        rapport(r.returncode == 0 and (site / f"{court}.glb").is_file() and f'"room": "{court}"' in (site / f"{court}.config.json").read_text(encoding="utf-8")
                and json.loads((site / "default.json").read_text(encoding="utf-8")) == {"region": court}, f"{nom} : renommage : sans argument le nom est demande ; retour au nom d'origine", r.stdout[-300:])
        fr2 = json.loads((site / "regions.json").read_text(encoding="utf-8"))["regions"][0]
        rapport(fr2.get("id") == court and fr2.get("room") == court and fr2.get("url") == f"index.html?region={court}", f"{nom} : renommage : la fiche revient au nom d'origine", fr2)


essai_lanceurs_unix()
asyncio.run(main())
