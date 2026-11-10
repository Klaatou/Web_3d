#!/usr/bin/env python3
"""Test 1.8.5 : le bouton « Promenade (P) » clignote en vue globale apres 8 s sans action ; lien Discord dans la fenetre Aide.

Verifie : au chargement le bouton ne clignote pas ; apres 8 s sans action il clignote (classe pulse, fond alternativement noir et clair, donc sans
dependre de la couleur) ; un mouvement de souris l'arrete, 8 s d'inactivite le relancent ; la touche P entre en promenade (bouton cache, plus de
clignotement) et, une fois revenu en vue globale, il ne clignote plus ; avec « mouvement reduit » : pas d'animation, bordure de 3 px ; le lien Discord
de la fenetre Aide existe (nouvel onglet, noopener), en francais et en anglais ; aucune erreur JavaScript.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Dure environ 1 minute.
Lancer : python tests/bouton_promenade.py
"""
import asyncio, os, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import DIST, html, rapport, resultat, serveur, sol_glb, tmp

src = tmp / "src"
src.mkdir()
sol_glb(src / "Pulse.glb")
site = tmp / "site"
site.mkdir()
html(src / "Pulse.glb", "-o", site / "Pulse.html", "--shared-shell")
shutil.copy(DIST / "index.html", site / "index.html")
errs = []
BTN = "document.getElementById('walkBtn')"
PULSE = "(() => { const b = " + BTN + "; return b.classList.contains('pulse'); })()"
FOND = "getComputedStyle(" + BTN + ").backgroundColor"


async def ouvrir(br, port, locale, **kw):
    ctx = await br.new_context(locale=locale, viewport={"width": 900, "height": 650}, **kw)
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(f"http://127.0.0.1:{port}/index.html?region=Pulse")
    await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
    return ctx, pg


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        http, port = serveur(site)
        try:
            ctx, pg = await ouvrir(br, port, "fr-FR")
            rapport(await pg.evaluate("!" + BTN + ".hidden") and await pg.evaluate(BTN + ".textContent") == "Promenade (P)", "vue globale : bouton « Promenade (P) » visible")
            rapport(not await pg.evaluate(PULSE), "juste apres le chargement : le bouton ne clignote pas")
            await pg.wait_for_timeout(5500)
            rapport(not await pg.evaluate(PULSE), "apres 5 s sans action : pas encore de clignotement (delai de 8 s)")
            await pg.wait_for_function(PULSE, timeout=8000)
            rapport(True, "apres 8 s sans action : le bouton clignote")
            vus = set()
            for _ in range(16):
                vus.add(await pg.evaluate(FOND))
                await pg.wait_for_timeout(100)
            clair = [v for v in vus if v in ("rgba(255, 255, 255, 0.94)", "rgb(255, 255, 255)")]
            rapport("rgb(0, 0, 0)" in vus and clair, "le fond alterne entre noir et clair (sans dependre de la couleur)", vus)
            rapport(await pg.evaluate("getComputedStyle(" + BTN + ").animationName") == "walkPulse", "animation walkPulse en cours")
            await pg.mouse.move(300, 300)
            await pg.wait_for_timeout(300)
            rapport(not await pg.evaluate(PULSE), "un mouvement de souris arrete le clignotement")
            await pg.wait_for_timeout(5000)
            rapport(not await pg.evaluate(PULSE), "5 s apres : toujours arrete")
            await pg.wait_for_function(PULSE, timeout=8000)
            rapport(True, "8 s d'inactivite : le clignotement reprend")
            await pg.keyboard.press("p")
            await pg.wait_for_function("document.getElementById('walkBtn').hidden === true", timeout=20000)
            rapport(not await pg.evaluate(PULSE), "touche P : promenade, bouton cache, plus de clignotement")
            await pg.keyboard.press("p")
            await pg.wait_for_function("document.getElementById('walkBtn').hidden === false", timeout=20000)
            await pg.wait_for_timeout(10500)
            rapport(not await pg.evaluate(PULSE), "revenu en vue globale apres une promenade : il ne clignote plus")
            LIEN = "(() => { const a = document.getElementById('discordLink'); return a ? [a.getAttribute('href'), a.target, a.rel, a.textContent] : null; })()"
            rapport(await pg.evaluate(LIEN) == ["https://discord.gg/BDG9r5gXwr", "_blank", "noopener", "Discord (questions, aide, nouveautés)"], "fenetre Aide (fr) : lien Discord, nouvel onglet, noopener", await pg.evaluate(LIEN))
            await ctx.close()

            ctx, pg = await ouvrir(br, port, "en-US", reduced_motion="reduce")
            rapport(await pg.evaluate(BTN + ".textContent") == "Walk (P)", "anglais : bouton « Walk (P) »")
            await pg.wait_for_timeout(9000)
            etat = await pg.evaluate("(() => { const b = " + BTN + ", cs = getComputedStyle(b); return [b.classList.contains('pulse'), cs.animationName, cs.borderTopWidth]; })()")
            rapport(etat == [True, "none", "3px"], "mouvement reduit : pas d'animation, bordure de 3 px", etat)
            LIEN_EN = await pg.evaluate(LIEN)
            rapport(LIEN_EN and LIEN_EN[3] == "Discord (questions, help, news)", "fenetre Aide (en) : lien Discord", LIEN_EN)
            await ctx.close()
        finally:
            http.kill()
        await br.close()


asyncio.run(main())
rapport(not errs, "aucune erreur JavaScript", errs)
sys.exit(1 if resultat() else 0)
