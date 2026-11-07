#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Version de la page (lot 1.6.17) : la fenetre Etat (touche I) affiche « Version : page X · configuration Y » ; X est la version de index.html (VERSIONS.json), Y la cle `version` de la
configuration du paquet ; la fenetre Aide n'affiche plus la version de la configuration sous le nom « glb2html » (elle trompait : elle ne change pas quand on remplace index.html).
Verifie aussi que la ligne figure dans « Copier le diagnostic ». Paquet region-simple fabrique ; en francais puis en anglais.
Prerequis : python build.py. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/version_page.py
"""
import asyncio, json, os, pathlib, socket, subprocess, sys, tempfile, time, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_verpage_"))
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {str(detail)[:400]}"), flush=True)
    echecs += not ok


cmd = [sys.executable, str(ROOT / "fabriquer_paquets.py"), "--out", str(tmp / "zips")] + (["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else [])
r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
rapport(r.returncode == 0, "fabrication des zips", (r.stdout + r.stderr)[-300:])
if r.returncode:
    sys.exit(1)
zipfile.ZipFile(tmp / "zips" / "region-simple.zip").extractall(tmp / "x")
site = tmp / "x" / "region-simple" / "site"
page = json.loads((ROOT / "VERSIONS.json").read_text(encoding="utf-8"))["index.html"]["version"]
conf = json.loads((site / "region.config.json").read_text(encoding="utf-8"))["version"]


def serveur(d):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    return subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL), port


async def main():
    from playwright.async_api import async_playwright
    proc, port = serveur(site)
    time.sleep(1.5)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            for loc, attendu in (("fr-FR", f"Version : page {page} · configuration {conf}"), ("en-US", f"Version: page {page} · configuration {conf}")):
                pg = await br.new_page(locale=loc, viewport={"width": 1200, "height": 700}); errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                await pg.goto(f"http://127.0.0.1:{port}/index.html")
                await pg.wait_for_function("document.getElementById('msg') === null", timeout=90000)
                await pg.wait_for_timeout(1500)
                ver = await pg.evaluate("(document.getElementById('verInfo') || {}).textContent || ''")
                rapport(ver == attendu, f"{loc} : la fenetre Etat affiche la version de la page et celle de la configuration", [ver, attendu])
                aide = await pg.evaluate("document.getElementById('helpBody').textContent")
                rapport("glb2html" not in aide and conf not in aide, f"{loc} : la fenetre Aide n'affiche plus la version de la configuration sous le nom glb2html", aide[-160:])
                await pg.click("#diagBtn"); await pg.wait_for_timeout(500)
                diag = await pg.evaluate("document.getElementById('diagOut').value")
                rapport(page in diag and conf in diag, f"{loc} : « Copier le diagnostic » contient les deux versions", diag[:200])
                rapport(not errs, f"{loc} : aucune erreur JavaScript", errs[:2])
                await pg.close()
            await br.close()
    finally:
        proc.terminate()


asyncio.run(main())
print("\nRESULTAT : " + ("tout est passe" if not echecs else f"{echecs} echec(s)"))
sys.exit(1 if echecs else 0)
