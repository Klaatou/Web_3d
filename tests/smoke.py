#!/usr/bin/env python3
"""Test de fumée : génère des pages depuis tests/data/*.glb (brut, Draco, Meshopt), les ouvre dans Chromium sans tête
et vérifie : aucune erreur JavaScript, message « Chargement… » disparu (= modèle chargé). Teste aussi --register / --map-page.

Prérequis : pip install playwright && playwright install chromium ; python build.py avant.
Variables facultatives : THREE_DIR (paquet npm three, hors ligne), CHROMIUM (chemin de l'exécutable).
"""
import asyncio, json, os, pathlib, subprocess, sys, tempfile

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


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        bad = 0
        for page_file in pages + [carte]:
            pg = await (await br.new_context(viewport={"width": 900, "height": 600})).new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(page_file.as_uri())
            await pg.wait_for_timeout(2500)
            loaded = True if page_file == carte else await pg.evaluate("document.getElementById('msg') === null")
            ok = loaded and not errs
            bad += not ok
            print(("[OK]    " if ok else "[ECHEC] ") + page_file.name + ("" if ok else f"  chargé={loaded} erreurs={errs}"))
            await pg.close()
        await br.close()
        return bad


bad = asyncio.run(main())
(DIST / "regions.json").unlink(missing_ok=True)   # le test ne laisse rien derrière lui
sys.exit(1 if bad else 0)
