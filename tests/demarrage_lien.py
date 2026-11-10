#!/usr/bin/env python3
"""Test 1.8.6 : ouverture par un lien avec une arrivee (#spawn=default) : plus d'ecran noir sur une region en tuiles.

Region synthetique (tests/glbfab.py region) decoupee par glb2tiles.py ; les reponses des tuiles sont retenues avec page.route (aucun reseau).
Verifie, region en tuiles : tant que les tuiles sont retenues, le fond noir (#fade) n'est pas pose (opacite 0), le texte « Chargement du sol… »
est affiche avec le temps ecoule, la vue d'ensemble n'est pas cachee ; quand les tuiles arrivent la promenade demarre au point d'arrivee et le texte
disparait. Region en GLB unique : le fondu noir est conserve pendant le chargement, puis retire quand la promenade demarre. Sans lien (vue globale) :
ni noir ni promenade. Aucune erreur JavaScript.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/demarrage_lien.py
"""
import asyncio, json, os, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import DIST, html, rapport, resultat, run, serveur, tmp
import glbfab

src = tmp / "src"
src.mkdir()
glbfab.region(src / "Reg.glb")
run(DIST / "glb2tiles.py", src / "Reg.glb", "--forcer", "--budget-tri", "700", "--min", "64", "--nopause", "--sans-references")
doc = json.loads((src / "Reg.tiles.json").read_text(encoding="utf-8"))
TILES = doc["tiles"]
rapport(len(TILES) >= 2, f"glb2tiles : {len(TILES)} tuiles (au moins 2)", len(TILES))
t0 = TILES[0]
SX, SZ = (t0["min"][0] + t0["max"][0]) / 2, (t0["min"][2] + t0["max"][2]) / 2
SY = glbfab.hauteur(SX, SZ)
(tmp / "z.json").write_text(json.dumps([{"id": "default", "type": "spawn", "x": SX, "y": SY, "z": SZ, "yaw": 0.0}]), encoding="utf-8")
site = tmp / "site"
site.mkdir()
html("-o", site / "Reg.html", "--shared-shell", "--tiles", src / "Reg.tiles.json", "--zones", tmp / "z.json")
shutil.copy(src / "Reg.glb", tmp / "Plein.glb")
html(tmp / "Plein.glb", "-o", site / "Plein.html", "--shared-shell")
errs = []
FADE = "document.getElementById('fade').classList.contains('on')"
OPAC = "getComputedStyle(document.getElementById('fade')).opacity"
GW = "(() => { const g = document.getElementById('groundWait'); return g.hidden ? '' : g.textContent; })()"


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        http, port = serveur(site)
        try:
            async def ouvrir(page, hash_, retenir):
                ctx = await br.new_context(locale="fr-FR", viewport={"width": 700, "height": 500})
                pg = await ctx.new_page()
                pg.on("pageerror", lambda e: errs.append(str(e)))
                ev = asyncio.Event()

                async def route(r):
                    nom = r.request.url.split("/")[-1]
                    if retenir(nom):
                        await ev.wait()
                    try:
                        await r.continue_()
                    except Exception:
                        pass
                await pg.route("**/*.glb", route)
                await pg.goto(f"http://127.0.0.1:{port}/index.html?region={page}{hash_}")
                return ctx, pg, ev

            # 1. region en tuiles, lien #spawn=default, tuiles retenues (la vue d'ensemble, s'il y en a une, passe)
            ctx, pg, ev = await ouvrir("Reg", "#spawn=default&name=Test", lambda n: n.startswith("Reg.tiles") is False and n.endswith(".glb") and "overview" not in n)
            await pg.wait_for_function("window.__viewer && !document.getElementById('groundWait').hidden", timeout=30000)
            await pg.wait_for_timeout(1500)
            rapport(not await pg.evaluate(FADE) and await pg.evaluate(OPAC) == "0", "tuiles : pas de fond noir pendant l'attente (lien #spawn=default)", await pg.evaluate(OPAC))
            txt = await pg.evaluate(GW)
            rapport(txt.startswith("Chargement du sol…") and " s" in txt, "tuiles : le texte « Chargement du sol… » est affiche avec le temps ecoule", txt)
            rapport(not await pg.evaluate("window.__viewer.walking"), "tuiles : pas encore en promenade tant que la tuile n'est pas prete")
            ev.set()
            await pg.wait_for_function("window.__viewer.walking", timeout=60000)
            w = await pg.evaluate("window.__viewer.getWalk().pos")
            rapport(abs(w[0] - SX) < 1 and abs(w[2] - SZ) < 1, "tuiles : promenade au point d'arrivee des que la tuile arrive", w)
            await pg.wait_for_function("document.getElementById('groundWait').hidden", timeout=20000)
            rapport(not await pg.evaluate(FADE), "tuiles : promenade demarree, texte retire, pas de noir")
            await ctx.close()

            # 2. region en GLB unique : le noir est conserve pendant le chargement
            ctx, pg, ev = await ouvrir("Plein", "#spawn=default&name=Test", lambda n: n == "Plein.glb")
            await pg.wait_for_function("document.getElementById('fade') && document.getElementById('fade').classList.contains('on')", timeout=30000)
            await pg.wait_for_timeout(1000)
            rapport(await pg.evaluate(FADE) and not await pg.evaluate("window.__viewer && window.__viewer.walking"), "GLB unique : fondu noir conserve pendant le chargement")
            ev.set()
            await pg.wait_for_function("window.__viewer && window.__viewer.walking", timeout=60000)
            await pg.wait_for_function("!document.getElementById('fade').classList.contains('on')", timeout=10000)
            rapport(True, "GLB unique : promenade demarree, noir retire")
            await ctx.close()

            # 3. sans lien : ni noir ni promenade
            ctx, pg, ev = await ouvrir("Reg", "", lambda n: False)
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
            rapport(not await pg.evaluate(FADE) and not await pg.evaluate("window.__viewer.walking"), "sans lien : ni noir ni promenade")
            await ctx.close()
        finally:
            http.kill()
        await br.close()


asyncio.run(main())
rapport(not errs, "aucune erreur JavaScript", errs)
sys.exit(1 if resultat() else 0)
