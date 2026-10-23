#!/usr/bin/env python3
"""Test de fumée : génère des pages depuis tests/data/*.glb (brut, Draco, Meshopt), les ouvre dans Chromium sans tête
et vérifie : aucune erreur JavaScript, message « Chargement… » disparu (= modèle chargé). Teste aussi --register / --map-page.
Teste enfin le mode modulaire (--modular, --config-only) servi par http.server : chargement, cfg identique à celui de la page
autonome, modification de <page>.config.json puis rechargement, et message clair à l'ouverture depuis le disque.

Prérequis : pip install playwright && playwright install chromium ; python build.py avant.
Variables facultatives : THREE_DIR (paquet npm three, hors ligne), CHROMIUM (chemin de l'exécutable).
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"   # outils Python en français (v36)
import asyncio, json, os, pathlib, re, socket, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST, DATA = ROOT / "dist", ROOT / "tests" / "data"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_smoke_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []


def run(*a):
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), *map(str, a), *vend], capture_output=True, text=True, cwd=tmp)
    if r.returncode:
        sys.exit(f"[ECHEC] {' '.join(map(str, a))}\n{r.stdout}{r.stderr}")
    return r.stdout


pages = []
for name in ("walk3", "draco", "meshopt"):
    out = tmp / f"{name}.html"
    run(DATA / f"{name}.glb", "-o", out, "--register", "regions.json", "--region-name", name, "--region-url", f"{name}.html",
        "--region-xy", f"{len(pages)},0", "--room", name, "--map-page", "carte.html")
    pages.append(out)
carte = tmp / "carte.html"
assert carte.exists(), "carte.html non générée"
assert (DIST / "regions.json").exists(), "regions.json attendu à côté du script (dist/)"
n = len(json.loads((DIST / "regions.json").read_text(encoding="utf-8")))
assert n >= 3, f"regions.json devrait contenir 3 régions, {n} trouvée(s)"


# --- mode modulaire : pages + glb + config.json + lib/ servis par http.server ---
mod = tmp / "modulaire"
mod_pages = []
for name in ("walk3", "draco", "meshopt"):
    run(DATA / f"{name}.glb", "-o", mod / f"{name}.html", "--modular", "--room", name)
    mod_pages.append(mod / f"{name}.html")
    std = re.search(r'id="cfg">(.*?)</script>', (tmp / f"{name}.html").read_text(encoding="utf-8"), re.S).group(1)
    std_cfg = json.loads(std.replace("<\\/", "</"))
    mod_cfg = json.loads((mod / f"{name}.config.json").read_text(encoding="utf-8"))
    std_cfg.pop("map"), mod_cfg.pop("map")   # la page autonome embarque la carte du --register ci-dessus
    assert std_cfg == mod_cfg, f"{name} : cfg modulaire différent de cfg autonome"
assert (mod / "lib" / "three-0.160.0" / "draco" / "draco_decoder.wasm").is_file(), "décodeur Draco absent de lib/"
assert not any(f.suffix == ".tmp" for f in mod.rglob("*")), "fichier .tmp oublié"


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


async def test_modulaire(br):
    bad = 0
    proc, port = serveur(mod)
    base = f"http://127.0.0.1:{port}/"

    async def ouvrir(url):
        pg = await (await br.new_context(locale="fr-FR", viewport={"width": 900, "height": 600})).new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(url)
        await pg.wait_for_timeout(2500)
        return pg, errs

    def rapport(ok, nom, detail=""):
        nonlocal bad
        bad += not ok
        print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + detail))

    try:
        for f in mod_pages:
            pg, errs = await ouvrir(base + f.name)
            loaded = await pg.evaluate("document.getElementById('msg') === null")
            rapport(loaded and not errs, "http " + f.name, f"chargé={loaded} erreurs={errs}")
            await pg.close()
        # modification de config.json puis rechargement : le bouton Réglages (cfg.panel) disparaît
        cfg_file = mod / "walk3.config.json"
        pg, errs = await ouvrir(base + "walk3.html")
        avant = await pg.evaluate("!document.getElementById('optsBtn').hidden")
        cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
        cfg["panel"] = not cfg["panel"]
        cfg_file.write_text(json.dumps(cfg), encoding="utf-8")
        await pg.reload()
        await pg.wait_for_timeout(2500)
        apres = await pg.evaluate("!document.getElementById('optsBtn').hidden")
        rapport(avant != apres and not errs, "config.json modifié puis rechargé", f"avant={avant} après={apres} erreurs={errs}")
        await pg.close()
        # --config-only : réécrit la config sans toucher ni au glb ni à la coquille
        glb0, html0 = (mod / "walk3.glb").read_bytes(), (mod / "walk3.html").read_bytes()
        run("-o", mod / "walk3.html", "--config-only", "--no-panel", "--wave", "3")
        cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
        rapport(cfg["wave"] == 3.0 and cfg["panel"] is False and cfg["room"] == "walk3", "--config-only réécrit la config", str(cfg))
        rapport((mod / "walk3.glb").read_bytes() == glb0 and (mod / "walk3.html").read_bytes() == html0, "--config-only laisse glb et coquille intacts")
        pg, errs = await ouvrir(base + "walk3.html")
        rapport(await pg.evaluate("document.getElementById('msg') === null") and not errs and not await pg.evaluate("!document.getElementById('optsBtn').hidden"), "rechargement après --config-only", str(errs))
        await pg.close()
        # config absente : message d'erreur clair
        (mod / "meshopt.config.json").rename(mod / "meshopt.config.off")
        pg, errs = await ouvrir(base + "meshopt.html")
        texte = await pg.evaluate("document.getElementById('msg') ? document.getElementById('msg').textContent : ''")
        rapport("introuvable" in texte, "config absente : message clair", texte)
        await pg.close()
        # depuis le disque : message explicatif
        pg, errs = await ouvrir((mod / "draco.html").as_uri())
        texte = await pg.evaluate("document.getElementById('msg') ? document.getElementById('msg').textContent : ''")
        rapport("http" in texte, "ouverture depuis le disque : message clair", texte)
        await pg.close()
    finally:
        proc.kill()
    return bad


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        bad = 0
        for page_file in pages + [carte]:
            pg = await (await br.new_context(locale="fr-FR", viewport={"width": 900, "height": 600})).new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(page_file.as_uri())
            await pg.wait_for_timeout(2500)
            loaded = True if page_file == carte else await pg.evaluate("document.getElementById('msg') === null")
            ok = loaded and not errs
            bad += not ok
            print(("[OK]    " if ok else "[ECHEC] ") + page_file.name + ("" if ok else f"  chargé={loaded} erreurs={errs}"))
            await pg.close()
        bad += await test_modulaire(br)
        await br.close()
        return bad


bad = asyncio.run(main())
(DIST / "regions.json").unlink(missing_ok=True)   # le test ne laisse rien derrière lui
sys.exit(1 if bad else 0)
