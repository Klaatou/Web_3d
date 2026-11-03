#!/usr/bin/env python3
"""Test 1.4.5 : panneau « A propos de la region » (NOM.about.<langue>.txt, repli NOM.about.txt).

Regions synthetiques servies par http.server : sans fichier ; avec fichiers fr et en ; avec le seul fichier de repli ; texte contenant du HTML ; region en tuiles.
Verifie : aucun fichier = ni panneau, ni bouton, ni case, ni reaction a « ? » ; fichier de la langue (fr, #lang=en) puis repli ; panneau a l'entree
(role=dialog, titre = premiere ligne, texte brut : une balise reste litterale) ; « Ne plus afficher » puis rechargement : absent ; case des reglages recochee :
present ; « ? » (key '?' avec code Comma = AZERTY, puis Slash = QWERTY) ouvre et ferme ; « ? » tape dans un champ : rien ; Echap ferme ; bouton de l'aide ;
region en tuiles ; sans localStorage la page marche et le panneau s'affiche a chaque entree ; aucune erreur JavaScript.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM.
Lancer : python tests/apropos.py
"""
import asyncio, json, os, shutil, sys

from h37 import DIST, html, rapport, resultat, run, serveur, sol_glb, tmp
import glbfab

NOMS = ["Sans", "Bilingue", "Repli", "Balise", "Tuilee"]
site = tmp / "site"
site.mkdir()
src = tmp / "src"
src.mkdir()

FR = "Bienvenue sur la région\nPremier paragraphe en français.\n\nSecond paragraphe."
EN = "Welcome to the region\nFirst paragraph in English.\n\nSecond paragraph."
GEN = "Titre du repli\nTexte du fichier de repli."
HTML = "Titre <i>sans effet</i>\nUne balise <b>x</b> reste visible telle quelle.\n<script>window.__xss = 1</script>"

for n in ["Sans", "Bilingue", "Repli", "Balise"]:
    sol_glb(src / (n + ".glb"))
    html(src / (n + ".glb"), "-o", site / (n + ".html"), "--shared-shell")
(site / "Bilingue.about.fr.txt").write_text(FR, encoding="utf-8")
(site / "Bilingue.about.en.txt").write_text(EN, encoding="utf-8")
(site / "Bilingue.about.txt").write_text(GEN, encoding="utf-8")   # la langue prime sur le repli
(site / "Repli.about.txt").write_text(GEN, encoding="utf-8")
(site / "Balise.about.txt").write_text(HTML, encoding="utf-8")

# region en tuiles : sol de 4 x 4 patches de 64 m, decoupe par glb2tiles.py
b = glbfab.B()
P = 64.0
for i in range(4):
    for j in range(4):
        v = [(100 + P * i + P * p, 12.0, -300 + P * j + P * q) for q in (0, 1) for p in (0, 1)]
        b.noeud(f"Terrain {i},{j}", b.mesh(v, [0, 1, 2, 1, 3, 2]), extras={"terrain": True})
b.ecrire(src / "Tuilee.glb")
run(DIST / "glb2tiles.py", src / "Tuilee.glb", "--forcer", "--budget-tri", "700", "--min", "64", "--nopause", "--sans-references")
html("-o", site / "Tuilee.html", "--shared-shell", "--tiles", src / "Tuilee.tiles.json", "--rotate", "0")
for f in (src / "Tuilee.tiles.json",):
    shutil.copy(f, site / f.name)
shutil.copytree(src / "Tuilee.tiles", site / "Tuilee.tiles", dirs_exist_ok=True)
(site / "Tuilee.about.en.txt").write_text(EN, encoding="utf-8")
shutil.copy(DIST / "index.html", site / "index.html")   # coquille commune (au cas ou --shared-shell ne l'aurait pas posee)

OV = "!document.getElementById('aboutOverlay').hidden"
errs = []


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        proc, port = serveur(site)
        try:
            async def page(nom, lang="fr-FR", frag="", ctx=None, init=None):
                ctx = ctx or await br.new_context(locale=lang, viewport={"width": 800, "height": 600})
                if init:
                    await ctx.add_init_script(init)
                pg = await ctx.new_page()
                pg.on("pageerror", lambda e: errs.append(str(e)))
                await pg.goto(f"http://127.0.0.1:{port}/index.html?region={nom}{frag}")
                await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
                await pg.wait_for_timeout(700)   # l'ouverture se fait apres le chargement : on lui laisse le temps (le « non » se prouve par l'attente)
                return ctx, pg

            ouvert = lambda pg: pg.evaluate(OV)

            async def touche(pg, key, code):
                await pg.evaluate("([key, code]) => window.dispatchEvent(new KeyboardEvent('keydown', { key, code, shiftKey: true, bubbles: true }))", [key, code])
                await pg.wait_for_timeout(150)

            # 1. aucun fichier : ni panneau, ni bouton, ni case, rien sur « ? »
            ctx, pg = await page("Sans")
            rapport(not await ouvert(pg), "sans fichier : pas de panneau a l'entree")
            await touche(pg, "?", "Comma")
            rapport(not await ouvert(pg), "sans fichier : « ? » n'ouvre rien")
            rapport(await pg.evaluate("!document.getElementById('aboutBtn') && !document.getElementById('aboutOpt')"), "sans fichier : ni bouton ni case")
            aide = await pg.evaluate("document.getElementById('helpBody').textContent")
            rapport("à propos" not in aide, "sans fichier : l'aide ne parle pas de « ? »", aide[-120:])
            await ctx.close()

            # 2. fichier de la langue (fr) : panneau a l'entree, dialogue, titre, texte
            ctx, pg = await page("Bilingue")
            rapport(await ouvert(pg), "fr : le panneau s'ouvre a l'entree")
            d = await pg.evaluate("""() => { const b = document.getElementById('aboutBox'); return { role: b.getAttribute('role'), modal: b.getAttribute('aria-modal'), titre: document.getElementById('aboutTitle').textContent,
                texte: document.getElementById('aboutText').textContent, ws: getComputedStyle(document.getElementById('aboutText')).whiteSpace, btn: !!document.getElementById('aboutBtn'), opt: !!document.getElementById('aboutOpt') }; }""")
            rapport(d["role"] == "dialog" and d["modal"] == "true", "le panneau est un dialogue", d)
            rapport(d["titre"] == "Bienvenue sur la région" and d["texte"] == "Premier paragraphe en français.\n\nSecond paragraphe.", "fr : titre = premiere ligne, reste en paragraphes (fichier .fr.txt, pas le repli)", d)
            rapport(d["ws"] == "pre-wrap" and d["btn"] and d["opt"], "texte en pre-wrap ; bouton de l'aide et case des reglages presents", d)
            aide = await pg.evaluate("document.getElementById('helpBody').textContent")
            rapport("? : à propos de la région" in aide, "l'aide donne la touche « ? »", aide[-160:])

            # 3. Echap ferme ; « ? » AZERTY puis QWERTY ouvre et ferme ; un champ de saisie garde son « ? »
            await pg.keyboard.press("Escape")
            rapport(not await ouvert(pg), "Echap ferme le panneau")
            await touche(pg, "?", "Comma")
            rapport(await ouvert(pg), "« ? » (code Comma, AZERTY) ouvre")
            await touche(pg, "?", "Comma")
            rapport(not await ouvert(pg), "« ? » (code Comma) ferme (bascule)")
            await touche(pg, "?", "Slash")
            rapport(await ouvert(pg), "« ? » (code Slash, QWERTY) ouvre")
            await touche(pg, "?", "Slash")
            rapport(not await ouvert(pg), "« ? » (code Slash) ferme")
            await pg.evaluate("window.dispatchEvent(new KeyboardEvent('keydown', { key: '?', code: 'Slash', shiftKey: true, ctrlKey: true }))")
            await pg.evaluate("window.dispatchEvent(new KeyboardEvent('keydown', { key: '?', code: 'Slash', shiftKey: true, repeat: true }))")
            await pg.wait_for_timeout(150)
            rapport(not await ouvert(pg), "« ? » avec Ctrl, ou repete : rien")
            await pg.evaluate("() => { const i = document.createElement('input'); i.id = 'essai'; document.body.append(i); i.focus(); }")
            await pg.keyboard.type("?")
            rapport(not await ouvert(pg) and await pg.evaluate("document.getElementById('essai').value") == "?", "« ? » tape dans un champ : saisi, sans ouvrir le panneau")
            await pg.evaluate("document.getElementById('essai').remove()")
            await pg.evaluate("document.getElementById('aboutBtn').click()")
            rapport(await ouvert(pg), "le bouton de l'aide ouvre le panneau")
            await pg.evaluate("document.getElementById('aboutClose').click()")
            rapport(not await ouvert(pg), "le bouton Fermer ferme")

            # 4. « Ne plus afficher » puis rechargement : absent ; case recochee : present ; « ? » ouvre quand meme
            await pg.evaluate("document.getElementById('aboutBtn').click()")
            await pg.evaluate("document.getElementById('aboutHide').click()")
            rapport(not await ouvert(pg), "« Ne plus afficher » ferme le panneau")
            await pg.reload()
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
            await pg.wait_for_timeout(700)
            rapport(not await ouvert(pg), "apres « Ne plus afficher » et rechargement : absent a l'entree")
            rapport(await pg.evaluate("!document.getElementById('aboutOpt').checked"), "la case des reglages est decochee")
            await touche(pg, "?", "Comma")
            rapport(await ouvert(pg), "« ? » ouvre malgre « Ne plus afficher »")
            await pg.keyboard.press("Escape")
            await pg.evaluate("() => { const c = document.getElementById('aboutOpt'); c.checked = true; c.dispatchEvent(new Event('change')); }")
            await pg.reload()
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
            await pg.wait_for_timeout(700)
            rapport(await ouvert(pg), "case recochee : le panneau revient a l'entree")
            # memorisation par region : une autre region n'est pas touchee
            await pg.evaluate("document.getElementById('aboutHide').click()")
            await pg.goto(f"http://127.0.0.1:{port}/index.html?region=Repli")
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
            await pg.wait_for_timeout(700)
            rapport(await ouvert(pg), "« Ne plus afficher » est propre a la region (Repli s'ouvre)")
            await ctx.close()

            # 5. anglais : fichier .en.txt
            ctx, pg = await page("Bilingue", lang="en-US", frag="#lang=en")
            t = await pg.evaluate("document.getElementById('aboutTitle').textContent")
            rapport(await ouvert(pg) and t == "Welcome to the region", "#lang=en : fichier .en.txt", t)
            bt = await pg.evaluate("[document.getElementById('aboutClose').textContent, document.getElementById('aboutHide').textContent]")
            rapport(bt == ["Close (Esc)", "Don't show again"], "textes du panneau en anglais", bt)
            await ctx.close()

            # 6. repli sur NOM.about.txt
            ctx, pg = await page("Repli")
            t = await pg.evaluate("document.getElementById('aboutTitle').textContent")
            rapport(await ouvert(pg) and t == "Titre du repli", "repli sur NOM.about.txt (aucun fichier de langue)", t)
            await ctx.close()

            # 7. texte brut : une balise reste litterale, aucun script
            ctx, pg = await page("Balise")
            d = await pg.evaluate("""() => ({ texte: document.getElementById('aboutText').textContent, titre: document.getElementById('aboutTitle').textContent,
                enfants: document.querySelectorAll('#aboutText *, #aboutTitle *').length, xss: window.__xss || 0 })""")
            rapport("<b>x</b>" in d["texte"] and "<script>" in d["texte"] and d["enfants"] == 0 and not d["xss"] and d["titre"] == "Titre <i>sans effet</i>", "HTML non interprete : balises visibles telles quelles", d)
            await ctx.close()

            # 8. region en tuiles
            ctx, pg = await page("Tuilee", lang="en-US")
            rapport(await ouvert(pg) and await pg.evaluate("window.__viewer.tiled"), "region en tuiles : le panneau s'ouvre a l'entree")
            await ctx.close()

            # 9. sans localStorage : la page marche, le panneau s'affiche a chaque entree
            casse = "Object.defineProperty(window, 'localStorage', { get() { throw new Error('stockage bloque'); } });"
            ctx, pg = await page("Bilingue", init=casse)
            rapport(await ouvert(pg), "stockage indisponible : le panneau s'ouvre")
            await pg.evaluate("document.getElementById('aboutHide').click()")
            rapport(not await ouvert(pg), "stockage indisponible : « Ne plus afficher » ferme sans erreur")
            await pg.reload()
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
            await pg.wait_for_timeout(700)
            rapport(await ouvert(pg), "stockage indisponible : il revient a chaque entree")
            await ctx.close()

            rapport(not errs, "aucune erreur JavaScript", errs)
        finally:
            proc.kill()
            await br.close()


asyncio.run(main())
bad = resultat()
print()
print("RESULTAT : " + ("tout est passe" if not bad else f"ECHEC ({bad})"))
sys.exit(1 if bad else 0)
