#!/usr/bin/env python3
"""Test 1.4.9 : panneau « A propos de la region » : liens cliquables, bouton « Aide des visiteurs », libelle du bouton de l'aide avec la touche ?.

Trois sites servis par http.server, la meme region : « avec » (a propos + aide.html), « sans » (a propos, pas d'aide.html), « aide » (aide.html, pas d'a propos).
Verifie : les adresses http(s):// du texte deviennent des liens (nouvel onglet, rel noopener), la ponctuation finale reste du texte, le texte affiche est
identique au fichier, une adresse javascript: et une balise <a> ecrite dans le texte restent du texte ; le bouton « Aide des visiteurs » n'existe qu'avec
aide.html et ouvre aide.html dans un nouvel onglet ; le lien « Aide des visiteurs » de la fenetre Aide (touche H) existe avec aide.html, meme sans a propos, et
disparait sans aide.html ; le bouton de l'aide dit « (touche ?) » ; le panneau n'assombrit pas la page (fond transparent, la page reste atteignable
derriere, seul le cadre recoit la souris) ; aucune erreur JavaScript.

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
for nom, aide, apropos in (("avec", True, True), ("sans", False, True), ("aide", True, False)):
    d = tmp / nom
    d.mkdir()
    html(src / "Liens.glb", "-o", d / "Liens.html", "--shared-shell")
    shutil.copy(DIST / "index.html", d / "index.html")
    if apropos:
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
                if nom == "aide":
                    await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
                else:
                    await pg.wait_for_function("!document.getElementById('aboutOverlay').hidden", timeout=60000)
                await pg.wait_for_timeout(600)   # le test d'existence d'aide.html est asynchrone
                LIEN = "(() => { const a = document.getElementById('aideLink'); return a ? [!a.parentElement.hidden, a.getAttribute('href').split('/').pop(), a.textContent] : null; })()"
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
                    fond = await pg.evaluate("""(() => { const o = document.getElementById('aboutOverlay'), b = document.getElementById('aboutBox'), cs = getComputedStyle(o);
                        const r = b.getBoundingClientRect(), hors = document.elementFromPoint(3, 3), dedans = document.elementFromPoint(r.left + r.width / 2, r.top + 12);
                        return { fond: cs.backgroundColor, evt: cs.pointerEvents, boite: getComputedStyle(b).pointerEvents, horsOverlay: !!hors && hors.id !== 'aboutOverlay' && !o.contains(hors), dedans: b.contains(dedans), modal: b.getAttribute('aria-modal') }; })()""")
                    rapport(fond["fond"] in ("rgba(0, 0, 0, 0)", "transparent") and fond["evt"] == "none" and fond["boite"] == "auto" and fond["horsOverlay"] and fond["dedans"] and fond["modal"] == "false",
                            "le panneau n'assombrit pas la page : fond transparent, page atteignable derriere, cadre cliquable", fond)
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
                    rapport(await pg.evaluate(LIEN) == [True, "aide.html", "Aide des visiteurs"], "fenetre Aide : lien « Aide des visiteurs » visible (avec aide.html)", await pg.evaluate(LIEN))
                elif nom == "sans":
                    rapport(await pg.evaluate("document.getElementById('aboutHelp').hidden"), "sans aide.html : pas de bouton « Aide des visiteurs »")
                    rapport((await pg.evaluate(LIEN) or [True])[0] is False, "fenetre Aide : lien « Aide des visiteurs » cache (sans aide.html)", await pg.evaluate(LIEN))
                else:
                    rapport(await pg.evaluate("!document.getElementById('aboutBtn') && !document.getElementById('aboutOverlay').offsetParent"), "aide seule : pas d'a propos (ni bouton, ni panneau)")
                    rapport(await pg.evaluate(LIEN) == [True, "aide.html", "Aide des visiteurs"], "aide seule : le lien « Aide des visiteurs » est dans la fenetre Aide", await pg.evaluate(LIEN))
                await ctx.close()
            finally:
                http.kill()
        await br.close()


asyncio.run(main())
rapport(not errs, "aucune erreur JavaScript", errs)
sys.exit(1 if resultat() else 0)
