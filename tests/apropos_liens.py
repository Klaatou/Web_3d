#!/usr/bin/env python3
"""Test 1.4.9 : panneau « A propos de la region » : liens cliquables, bouton « Aide des visiteurs », libelle du bouton de l'aide avec la touche ?.

Deux sites servis par http.server, la meme region : l'un avec aide.html a cote de la coquille, l'autre sans.
Verifie : les adresses http(s):// du texte deviennent des liens (nouvel onglet, rel noopener), la ponctuation finale reste du texte, le texte affiche est
identique au fichier, une adresse javascript: et une balise <a> ecrite dans le texte restent du texte ; le bouton « Aide des visiteurs » n'existe qu'avec
aide.html et ouvre aide.html dans un nouvel onglet ; le bouton de l'aide dit « (touche ?) » ; aucune erreur JavaScript.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM.
Lancer : python tests/apropos_liens.py
"""
import asyncio, os, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import DIST, html, rapport, resultat, serveur, sol_glb, tmp

TEXTE = ("Bienvenue\nSite : https://exemple.org/page?a=1&b=2. Fin de phrase.\n"
         "(Voir http://autre.example/chemin), puis la suite.\n"
         "Pas un lien : javascript:alert(1) et <a href=\"https://piege.example\">x</a> reste ecrit.")
CORPS = TEXTE.split("\n", 1)[1]
src = tmp / "src"
src.mkdir()
sol_glb(src / "Liens.glb")
sites = {}
for nom, aide in (("avec", True), ("sans", False)):
    d = tmp / nom
    d.mkdir()
    html(src / "Liens.glb", "-o", d / "Liens.html", "--shared-shell")
    shutil.copy(DIST / "index.html", d / "index.html")
    (d / "Liens.about.fr.txt").write_text(TEXTE, encoding="utf-8")
    if aide:
        (d / "aide.html").write_text("<!doctype html><title>Aide</title><p>aide des visiteurs</p>", encoding="utf-8")
    sites[nom] = d

errs = []


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        for nom, d in sites.items():
            http, port = serveur(d)
            try:
                ctx = await br.new_context(locale="fr-FR", viewport={"width": 900, "height": 650})
                pg = await ctx.new_page()
                pg.on("pageerror", lambda e: errs.append(str(e)))
                await pg.goto(f"http://127.0.0.1:{port}/index.html?region=Liens")
                await pg.wait_for_function("!document.getElementById('aboutOverlay').hidden", timeout=60000)
                await pg.wait_for_timeout(600)   # le test d'existence d'aide.html est asynchrone
                if nom == "avec":
                    liens = await pg.evaluate("[...document.querySelectorAll('#aboutText a')].map(a => [a.getAttribute('href'), a.target, a.rel, a.textContent])")
                    rapport(liens == [["https://exemple.org/page?a=1&b=2", "_blank", "noopener noreferrer", "https://exemple.org/page?a=1&b=2"],
                                      ["http://autre.example/chemin", "_blank", "noopener noreferrer", "http://autre.example/chemin"],
                                      ["https://piege.example", "_blank", "noopener noreferrer", "https://piege.example"]],
                            "chaque adresse http(s) devient un lien, la ponctuation finale et les guillemets restent du texte", liens)
                    rapport(await pg.evaluate("document.getElementById('aboutText').textContent") == CORPS, "texte affiche identique au fichier", await pg.evaluate("document.getElementById('aboutText').textContent"))
                    rapport(await pg.evaluate("!document.querySelector('#aboutText a[href^=\"javascript\"]') && ![...document.querySelectorAll('#aboutText a')].some(a => a.textContent === 'x') && !document.querySelector('#aboutText b, #aboutText script')"),
                            "javascript: n'est pas un lien ; une balise <a> ecrite dans le texte reste du texte (seule son adresse est cliquable)")
                    rapport(await pg.evaluate("getComputedStyle(document.querySelector('#aboutText a')).textDecorationLine.includes('underline')"), "liens soulignes (pas seulement colores)")
                    vis = await pg.evaluate("(() => { const b = document.getElementById('aboutHelp'); return !b.hidden && b.textContent; })()")
                    rapport(vis == "Aide des visiteurs", "avec aide.html : bouton « Aide des visiteurs » visible", vis)
                    async with ctx.expect_page() as nouv:
                        await pg.click("#aboutHelp")
                    np = await nouv.value
                    await np.wait_for_load_state()
                    rapport(np.url.endswith("/aide.html"), "le bouton ouvre aide.html dans un nouvel onglet", np.url)
                    await np.close()
                    await pg.keyboard.press("Escape")
                    await pg.keyboard.press("h")
                    await pg.wait_for_timeout(300)
                    lab = await pg.evaluate("(document.getElementById('aboutBtn') || {}).textContent || ''")
                    rapport(lab == "À propos de la région (touche ?)", "bouton de l'aide : « À propos de la région (touche ?) »", lab)
                else:
                    rapport(await pg.evaluate("document.getElementById('aboutHelp').hidden"), "sans aide.html : pas de bouton « Aide des visiteurs »")
                await ctx.close()
            finally:
                http.kill()
        await br.close()


asyncio.run(main())
rapport(not errs, "aucune erreur JavaScript", errs)
sys.exit(1 if resultat() else 0)
