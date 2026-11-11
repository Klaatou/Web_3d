#!/usr/bin/env python3
"""Test 1.9.15 : curseur « Hauteur de la mer » de Réglages (Chromium).

Pourquoi : le viewer recentre le modèle (setModel : moyenne des origines de meshes à y = 15) ; seaY est dans ce repère décalé et dépend du
modèle (sur un GLB dont les objets sont hauts, la mer se retrouvait au-dessus du terrain). Le curseur donne la hauteur dans le repère de la région.

Verifie : curseur present (page avec mer), valeur de depart = seaY - decalage du modele, la mer suit le curseur (repere de la region + decalage),
choix retenu apres rechargement, « Valeurs d'origine », curseur grise quand la mer est masquee, textes francais et anglais, absent d'une page
--no-sea, aucune erreur de page. Mode tuiles, vrai navigateur graphique, Edge et Windows : non testes ici.

Prerequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/mer_hauteur.py
"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

print("--- 0. fabrication des pages")
site = tmp / "site"; site.mkdir()
sol_glb(site / "sol.glb")                    # un seul mesh, origine (0, 0, 0) : le viewer le decale de +15 en hauteur
html(site / "sol.glb", "-o", site / "Mer.html", "--sea-y", "10", "--target", "0,0,0")
html(site / "sol.glb", "-o", site / "Sec.html", "--no-sea", "--target", "0,0,0")
http, hport = serveur(site)
BASE = f"http://127.0.0.1:{hport}/"

LIGNE = """(t) => { const l = [...document.querySelectorAll('#optsPanel label')].find(x => x.textContent.includes(t));
  if (!l) return null; const r = l.querySelector('input'); return { valeur: parseFloat(r.value), grise: r.disabled, texte: l.textContent.trim() }; }"""
REGLER = """([t, v]) => { const r = [...document.querySelectorAll('#optsPanel label')].find(x => x.textContent.includes(t)).querySelector('input');
  r.value = v; r.dispatchEvent(new Event('input', { bubbles: true })); }"""
MER_Y = "window.__viewer.sea ? window.__viewer.sea.position.y : null"
CLIC = "([panneau, texte]) => [...document.querySelectorAll('#optsPanel ' + panneau)].find(x => x.textContent.includes(texte)).%s"


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)

        print("--- 1. page avec mer (--sea-y 10)")
        o = await Onglet(br).ouvrir(BASE + "Mer.html", locale="fr-FR")
        decal = await o.ev("window.__viewer.seaShift()")
        rapport(abs(decal - 15) < 1e-6, "decalage vertical du modele : +15 (origine du seul mesh a 0)", decal)
        rapport(abs(await o.ev(MER_Y) - 10) < 1e-6, "mer a seaY = 10 dans la scene")
        await o.ev("document.getElementById('optsBtn').click()")
        e = await o.ev(LIGNE, "Hauteur de la mer")
        rapport(e is not None and abs(e["valeur"] - (-5.0)) < 0.01 and "-5.0 m" in e["texte"] and not e["grise"], "curseur present, valeur de depart seaY - decalage = -5.0 m", e)

        print("--- 2. le curseur deplace la mer (repere de la region + decalage)")
        await o.ev(REGLER, ["Hauteur de la mer", 20])
        e = await o.ev(LIGNE, "Hauteur de la mer")
        rapport(abs(await o.ev(MER_Y) - 35) < 1e-6 and "20.0 m" in e["texte"], "curseur a 20 m : mer a 20 + 15 = 35 dans la scene, valeur affichee « 20.0 m »", e)
        await o.ev(REGLER, ["Hauteur de la mer", -12.5])
        rapport(abs(await o.ev(MER_Y) - 2.5) < 1e-6, "curseur a -12,5 m : mer a 2,5 dans la scene (valeurs negatives permises)")

        print("--- 3. choix retenu apres rechargement")
        await o.ev(REGLER, ["Hauteur de la mer", 20])
        await o.pg.reload(); await o.attendre("window.__viewer && document.getElementById('msg') === null", 40)
        rapport(abs(await o.ev(MER_Y) - 35) < 1e-6, "apres rechargement : mer toujours a 20 m (35 dans la scene)", await o.ev(MER_Y))
        await o.ev("document.getElementById('optsBtn').click()")
        e = await o.ev(LIGNE, "Hauteur de la mer")
        rapport(abs(e["valeur"] - 20) < 0.01 and "20.0 m" in e["texte"], "curseur reaffiche a 20.0 m", e)

        print("--- 4. « Valeurs d'origine » et mer masquee")
        await o.ev(CLIC % "click()", ["button", "Valeurs d'origine"])
        e = await o.ev(LIGNE, "Hauteur de la mer")
        rapport(abs(await o.ev(MER_Y) - 10) < 1e-6 and abs(e["valeur"] - (-5.0)) < 0.01, "« Valeurs d'origine » : mer et curseur reviennent a la page (10 dans la scene, -5.0 m)", e)
        await o.ev(CLIC % "querySelector('input').click()", ["label", "Afficher la mer"])
        e = await o.ev(LIGNE, "Hauteur de la mer")
        rapport(e["grise"] is True, "mer decochee : curseur grise", e)
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()

        print("--- 5. anglais et page sans mer")
        o = await Onglet(br).ouvrir(BASE + "Mer.html", locale="en-US")
        await o.ev("document.getElementById('optsBtn').click()")
        e = await o.ev(LIGNE, "Sea height")
        rapport(e is not None and "-5.0 m" in e["texte"], "anglais : « Sea height: -5.0 m »", e)
        await o.ctx.close()
        o = await Onglet(br).ouvrir(BASE + "Sec.html", locale="fr-FR")
        await o.ev("localStorage.setItem('glb2html_opts_x', JSON.stringify({ seaM: 30 }))")
        await o.pg.reload(); await o.attendre("window.__viewer && document.getElementById('msg') === null", 40)
        await o.ev("document.getElementById('optsBtn').click()")
        rapport(await o.ev(LIGNE, "Hauteur de la mer") is None and await o.ev("window.__viewer.sea") is None, "page --no-sea : ni curseur ni mer, meme avec un ancien choix memorise")
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()
        await br.close()


try:
    asyncio.run(main())
finally:
    http.kill()
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
