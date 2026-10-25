#!/usr/bin/env python3
"""Tests v52 : carte.html (total, surveillance sonore, delais, agrandissement de la vignette), « promeneur », case « Afficher la mer ».

Verifie : lignes « N visiteurs · N promeneurs » (francais, anglais) ; ligne « Total : ... » (chaque salon une fois, ancien serveur : promeneurs seulement) ;
surveillance sonore : aucun son au premier releve, aucun son case decochee, deux notes 660 puis 880 Hz sur une hausse de visiteurs, rien sur un depart,
case et etat memorises (son en attente du premier clic) ; constantes POLL_MS et POLL_ALERT_MS ; vignette agrandie au survol (carte.html et carte ouverte par M),
absente sans vignette, gardee apres un nouveau dessin ; case « Afficher la mer » (mer retiree et remise, Mer animee et Vagues grises, choix retenu,
Valeurs d'origine, page --no-sea sans la case et ignorant un ancien choix). Le son reel, un vrai telephone, Edge et Windows : non testes ici.

Prerequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v52.py
"""
import asyncio, base64, json, os, re, shutil, struct, sys, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37


def png(w, h):
    raw = b"".join(b"\x00" + bytes([200, 120, 40]) * w for _ in range(h))
    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw)) + ch(b"IEND", b"")


THUMB = "data:image/png;base64," + base64.b64encode(png(400, 300)).decode("ascii")
FAKE_AUDIO = """(() => {
  window.__beeps = [];
  class FakeAC { constructor() { this.currentTime = 0; this.state = 'running'; this.destination = {}; }
    resume() {}
    createOscillator() { const o = { type: '', frequency: { value: 0 }, connect() {}, start() { window.__beeps.push(o.frequency.value); }, stop() {} }; return o; }
    createGain() { return { gain: { setValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect() {} }; } }
  window.AudioContext = FakeAC;
})();"""

print("--- 0. fabrication des pages")
site = tmp / "site"; site.mkdir()
sol_glb(site / "sol.glb")
pres, pport = lancer_presence()
PRES = f"ws://127.0.0.1:{pport}"


def fiche(nom, room, x, y, presence=PRES, thumb=""):
    return {"name": nom, "url": f"{nom.lower()}.html", "x": x, "y": y, "spawn": "", "room": room, "thumb": thumb, "presence": presence}


REGS = [fiche("Alpha", "v52a", 0, 0, thumb=THUMB), fiche("Beta", "v52b", 1, 0), fiche("Gamma", "v52c", 2, 0)]
(site / "regions.json").write_text(json.dumps({"showUrl": False, "regions": REGS}), encoding="utf-8")
brut = (DIST / "carte.html").read_text(encoding="utf-8")
rapport("const POLL_MS = 10000;" in brut and "const POLL_ALERT_MS = 5000;" in brut, "carte.html : POLL_MS = 10000 et POLL_ALERT_MS = 5000 en tete du script (a modifier a la main)")
rapport(brut.count("setInterval(fetchCounts") == 0 and "POLL_ALERT_MS : POLL_MS" in brut, "carte.html : le delai est lu a chaque tour (plus de setInterval fixe)")
(site / "carte.html").write_text(brut.replace("const POLL_MS = 10000;", "const POLL_MS = 1200;").replace("const POLL_ALERT_MS = 5000;", "const POLL_ALERT_MS = 600;"), encoding="utf-8")
html(site / "sol.glb", "-o", site / "Gamma.html", "--shared-shell", "--no-sea", "--target", "0,0,0", "--presence-url", PRES, "--room", "v52c", "--map-url", "regions.json")
html(site / "sol.glb", "-o", site / "Mer.html", "--shared-shell", "--target", "0,0,0")
html(site / "sol.glb", "-o", site / "Sec.html", "--shared-shell", "--no-sea", "--target", "0,0,0")
http, hport = serveur(site)
BASE = f"http://127.0.0.1:{hport}/"
INIT = STUB + "\n" + FAKE_AUDIO

TUILES = """() => [...document.querySelectorAll('.tile')].map(t => ({ nom: t.querySelector('b').textContent, ligne: (t.querySelector('span') || {}).textContent || '', thumb: !!t.querySelector('img') }))"""
ZOOM = """() => { const z = document.getElementById('zoom'), im = z.querySelector('img'), r = z.getBoundingClientRect(), b = im.getBoundingClientRect(); return { hidden: z.hidden, w: b.width, dedans: r.left >= 0 && r.top >= 0 && r.right <= innerWidth + 1 && r.bottom <= innerHeight + 1, src: (im.getAttribute('src') || '').slice(0, 22) }; }"""


async def tuiles(o, attente="document.querySelector('.tile span')"):
    await o.attendre(attente, 20)
    return {t["nom"]: t for t in await o.ev(TUILES)}


async def promeneur(websockets, room, nom):
    c = await websockets.asyncio.client.connect(PRES)
    await c.send(json.dumps({"t": "hello", "name": nom, "room": room, "uid": os.urandom(12).hex(), "spectator": False}))
    await asyncio.wait_for(c.recv(), 5)
    return c


async def main():
    import websockets.asyncio.client, websockets.asyncio.server
    ws = websockets
    zoe = await promeneur(ws, "v52a", "Zoe")
    spect = await ws.asyncio.client.connect(PRES)
    await spect.send(json.dumps({"t": "hello", "room": "v52a", "uid": os.urandom(12).hex(), "spectator": True}))
    await asyncio.wait_for(spect.recv(), 5)

    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)

        print("--- 1. carte.html : « promeneur » et total")
        o = await Onglet(br).ouvrir(BASE + "carte.html", init=INIT, locale="fr-FR", viewer=False)
        t = await tuiles(o)
        rapport(t["Alpha"]["ligne"] == "2 visiteurs\n1 promeneur" and t["Beta"]["ligne"] == "aucun visiteur", "tuiles : « 2 visiteurs / 1 promeneur » sur deux lignes, « aucun visiteur »", (t["Alpha"]["ligne"], t["Beta"]["ligne"]))
        tot = lambda: o.ev("document.getElementById('total').textContent")
        rapport(await o.ev("getComputedStyle(document.querySelector('.tile span')).whiteSpace") == 'pre-line', "tuile : le saut de ligne du français est affiché (white-space: pre-line)")
        await o.attendre("document.getElementById('total').textContent.includes('Total')", 10)
        rapport(await tot() == "3 régions · Total : 2 visiteurs · 1 promeneur", "decompte et total : « 3 régions · Total : 2 visiteurs · 1 promeneur »", await tot())
        await asyncio.sleep(2.2)
        rapport(await o.ev("window.__beeps.length") == 0, "premier releve et releves suivants sans changement : aucun son")

        print("--- 2. arrivee case decochee : total a jour, aucun son")
        ada = await promeneur(ws, "v52b", "Ada")
        await o.attendre("document.getElementById('total').textContent === '3 régions · Total : 3 visiteurs · 2 promeneurs'", 15)
        rapport(True, "le total suit l'arrivee d'Ada (« Total : 3 visiteurs · 2 promeneurs »)")
        await asyncio.sleep(2.5)
        rapport(await o.ev("window.__beeps.length") == 0, "case decochee : aucun son")
        rapport(await o.ev("document.querySelectorAll('.tile.arr').length") == 0, "case decochee : aucun repere visuel")
        await ada.close()
        await o.attendre("document.getElementById('total').textContent === '3 régions · Total : 2 visiteurs · 1 promeneur'", 15)
        rapport(True, "depart d'Ada : le total redescend")

        print("--- 3. surveillance sonore")
        rapport(await o.ev("document.getElementById('alertState').textContent") == "", "case decochee : aucun texte d'etat")
        await o.pg.click("#alert")
        etat = await o.ev("document.getElementById('alertState').textContent")
        rapport(etat.startswith("à l'écoute"), "case cochee (le clic donne le son) : « à l'écoute (relevé toutes les ... s) »", etat)
        bob = await promeneur(ws, "v52c", "Bob")
        await o.attendre("window.__beeps.length >= 2", 15)
        rapport(await o.ev("window.__beeps.slice(0, 2)") == [660, 880], "arrivee dans Gamma : deux notes montantes 660 puis 880 Hz", await o.ev("window.__beeps"))
        etat = await o.ev("document.getElementById('alertState').textContent")
        rapport("dernière arrivée : Gamma, " in etat and re.search(r"\d\d:\d\d", etat), "texte « dernière arrivée : Gamma, hh:mm »", etat)
        arr = await o.ev("[...document.querySelectorAll('.tile.arr')].map(t => t.querySelector('b').textContent + '|' + t.querySelector('.arrb').textContent)")
        rapport(len(arr) == 1 and arr[0].startswith("Gamma|● arrivée ") and re.search(r"\d\d:\d\d", arr[0]), "repere visuel : seule la tuile Gamma est marquee, avec le texte « ● arrivée hh:mm » (pas la couleur seule)", arr)
        rapport(await o.ev("getComputedStyle(document.querySelector('.tile.arr')).animationName") == "arrblink", "le repere clignote (animation) ; contour en pointilles et texte en plus")
        await o.pg.hover('.tile:has(b:text-is("Gamma"))')
        await o.attendre("document.querySelectorAll('.tile.arr').length === 0", 5)
        rapport(True, "survol de la tuile : arrivee vue, le repere disparait")
        n = await o.ev("window.__beeps.length")
        await bob.close()
        await asyncio.sleep(2.5)
        rapport(await o.ev("window.__beeps.length") == n, "un depart ne sonne pas")
        bea = await promeneur(ws, "v52b", "Bea")
        await o.attendre("document.querySelectorAll('.tile.arr').length === 1", 15)
        await o.pg.click("#alert")
        await o.attendre("document.querySelectorAll('.tile.arr').length === 0", 5)
        rapport(True, "case decochee : les reperes disparaissent")
        await o.pg.click("#alert")
        await bea.close()
        await o.pg.reload()
        await tuiles(o)
        etat = await o.ev("document.getElementById('alertState').textContent")
        rapport(await o.ev("document.getElementById('alert').checked") and "premier clic" in etat, "apres rechargement : case cochee (memorisee) et « le son démarre au premier clic »", etat)
        await o.pg.click("body", position={"x": 5, "y": 5})
        etat = await o.ev("document.getElementById('alertState').textContent")
        rapport(etat.startswith("à l'écoute"), "apres un clic dans la page : « à l'écoute »", etat)
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()

        print("--- 4. agrandissement de la vignette")
        o = await Onglet(br).ouvrir(BASE + "carte.html", init=INIT, locale="fr-FR", viewer=False)
        await tuiles(o)
        rapport((await o.ev(ZOOM))["hidden"], "au repos : aucune vignette agrandie")
        await o.pg.hover(".tile:has(img)")
        await o.attendre("!document.getElementById('zoom').hidden", 5)
        z = await o.ev(ZOOM)
        rapport(z["src"].startswith("data:image/png") and 320 < z["w"] <= 401 and z["dedans"], "survol d'Alpha : image agrandie (plus grande que la tuile, 400 px au plus), dans la fenetre", z)
        await asyncio.sleep(3)
        rapport(not (await o.ev(ZOOM))["hidden"], "toujours affichee apres plusieurs nouveaux dessins de la grille")
        await o.pg.mouse.move(900, 650)
        await o.attendre("document.getElementById('zoom').hidden", 5)
        rapport(True, "pointeur parti : l'agrandissement disparait")
        await o.pg.hover(".tile:not(:has(img))")
        await asyncio.sleep(0.4)
        rapport((await o.ev(ZOOM))["hidden"], "tuile sans vignette : rien a agrandir")
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()

        print("--- 5. ancien serveur (sans visitors) et anglais")
        vport = port_libre()
        async def vieux(c):
            async for m in c:
                if json.loads(m).get("t") == "rooms":
                    await c.send(json.dumps({"t": "rooms", "rooms": {"v52old": 2}}))
        sv = await ws.asyncio.server.serve(vieux, "127.0.0.1", vport)
        site2 = tmp / "site2"; site2.mkdir(); shutil.copy(site / "carte.html", site2 / "carte.html")
        (site2 / "regions.json").write_text(json.dumps([fiche("Old", "v52old", 0, 0, presence=f"ws://127.0.0.1:{vport}")]), encoding="utf-8")
        http2, hport2 = serveur(site2)
        o = await Onglet(br).ouvrir(f"http://127.0.0.1:{hport2}/carte.html", init=INIT, locale="fr-FR", viewer=False)
        t = await tuiles(o)
        await o.attendre("document.getElementById('total').textContent.includes('Total')", 10)
        rapport(t["Old"]["ligne"] == "2 promeneurs" and await o.ev("document.getElementById('total').textContent") == "1 région · Total : 2 promeneurs", "ancien serveur : « 2 promeneurs », « 1 région · Total : 2 promeneurs » (pas de visiteurs inventes)", (t["Old"]["ligne"], await o.ev("document.getElementById('total').textContent")))
        await o.ctx.close(); http2.kill(); sv.close()
        o = await Onglet(br).ouvrir(BASE + "carte.html", init=INIT, locale="en-US", viewer=False)
        t = await tuiles(o)
        await o.attendre("document.getElementById('total').textContent.includes('Total')", 10)
        corps = await o.ev("document.body.innerText")
        rapport(t["Alpha"]["ligne"] == "2 visitors · 1 walker" and await o.ev("document.getElementById('total').textContent") == "3 regions · Total: 2 visitors · 1 walker" and "Arrival alert" in corps, "anglais : « 2 visitors · 1 walker », « Total: 2 visitors · 1 walker », « Arrival alert »", (t["Alpha"]["ligne"], await o.ev("document.getElementById('total').textContent")))
        await o.ctx.close()

        print("--- 6. carte ouverte par M dans une region")
        o = await Onglet(br).ouvrir(BASE + "index.html?region=Gamma#name=Zoe")
        await o.ev("document.getElementById('mapBtn').click()")
        await o.attendre("[...document.querySelectorAll('#mapGrid .mapTile')].some(b => b.textContent.includes('2 visiteurs'))", 20)
        ligne = await o.ev("[...document.querySelectorAll('#mapGrid .mapTile')].find(b => b.querySelector('b').textContent === 'Alpha').querySelector('span').textContent")
        rapport(ligne == "2 visiteurs\n1 promeneur", "carte de la region : « 2 visiteurs / 1 promeneur » sur deux lignes", ligne)
        await o.pg.hover("#mapGrid .mapTile:has(img)")
        await o.attendre("!document.getElementById('zoom').hidden", 5)
        z = await o.ev(ZOOM)
        rapport(z["src"].startswith("data:image/png") and 320 < z["w"] <= 401 and z["dedans"], "carte M : vignette agrandie au survol, au-dessus de la carte", z)
        await o.pg.mouse.move(900, 650)
        await o.attendre("document.getElementById('zoom').hidden", 5)
        rapport(True, "carte M : pointeur parti, l'agrandissement disparait")
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()

        print("--- 7. case « Afficher la mer »")
        SEA = "() => window.__viewer.scene.children.some(o => o.userData && o.userData.isSea)"
        PANEL = """() => { const l = t => [...document.querySelectorAll('#optsPanel label')].find(x => x.textContent.includes(t)); const c = t => { const x = l(t); return x ? x.querySelector('input') : null; };
          const s = c('Afficher la mer'), a = c('Mer animée'), w = document.querySelector('#optsPanel input[type=range]');
          return { mer: s ? [s.checked, s.disabled] : null, anim: a ? [a.checked, a.disabled] : null, vagues: w ? w.disabled : null }; }"""
        o = await Onglet(br).ouvrir(BASE + "index.html?region=Mer", locale="fr-FR")
        await o.ev("document.getElementById('optsBtn').click()")
        e = await o.ev(PANEL)
        rapport(e["mer"] == [True, False] and e["anim"] == [False, False] and e["vagues"] is True and await o.ev(SEA), "page avec mer : « Afficher la mer » cochee, mer presente, « Mer animée » libre, vagues grisees (mer non animee)", e)
        await o.ev("[...document.querySelectorAll('#optsPanel label')].find(x => x.textContent.includes('Mer animée')).querySelector('input').click()")
        e = await o.ev(PANEL)
        rapport(e["anim"] == [True, False] and e["vagues"] is False, "mer animee cochee : curseur des vagues libre", e)
        await o.ev("[...document.querySelectorAll('#optsPanel label')].find(x => x.textContent.includes('Afficher la mer')).querySelector('input').click()")
        e = await o.ev(PANEL)
        rapport(not await o.ev(SEA) and e["mer"] == [False, False] and e["anim"][1] is True and e["vagues"] is True, "mer decochee : plus de mer dans la scene, « Mer animée » et vagues grises", e)
        await o.pg.reload(); await o.attendre("window.__viewer && document.getElementById('msg') === null", 40)
        await o.ev("document.getElementById('optsBtn').click()")
        e = await o.ev(PANEL)
        rapport(not await o.ev(SEA) and e["mer"] == [False, False], "apres rechargement : mer toujours masquee (choix retenu)", e)
        await o.ev("[...document.querySelectorAll('#optsPanel button')].find(x => x.textContent.includes(\"Valeurs d'origine\")).click()")
        e = await o.ev(PANEL)
        rapport(await o.ev(SEA) and e["mer"] == [True, False] and e["anim"] == [False, False], "« Valeurs d'origine » : mer remise, mer animee decochee", e)
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()
        o = await Onglet(br).ouvrir(BASE + "index.html?region=Mer", locale="en-US")
        await o.ev("document.getElementById('optsBtn').click()")
        rapport("Show the sea" in await o.ev("document.getElementById('optsPanel').innerText"), "anglais : « Show the sea »")
        await o.ctx.close()
        o = await Onglet(br).ouvrir(BASE + "index.html?region=Sec", locale="fr-FR")
        await o.ev("localStorage.setItem('glb2html_opts_x', JSON.stringify({ sea: true }))")
        await o.pg.reload(); await o.attendre("window.__viewer && document.getElementById('msg') === null", 40)
        await o.ev("document.getElementById('optsBtn').click()")
        e = await o.ev(PANEL)
        rapport(e["mer"] is None and e["anim"] is None and not await o.ev(SEA), "page --no-sea : ni « Afficher la mer » ni « Mer animée », et un ancien choix « mer » retenu est ignore", e)
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()
        print("--- 8. le delai est relu des que la case est cochee")
        (site / "lent.html").write_text(brut.replace("const POLL_MS = 10000;", "const POLL_MS = 60000;").replace("const POLL_ALERT_MS = 5000;", "const POLL_ALERT_MS = 500;"), encoding="utf-8")
        o = await Onglet(br).ouvrir(BASE + "lent.html", init=INIT, locale="fr-FR", viewer=False)
        await tuiles(o)
        await o.pg.click("#alert")
        await asyncio.sleep(1.5)
        dan = await promeneur(ws, "v52b", "Dan")
        await o.attendre("window.__beeps.length >= 2", 6)
        rapport(await o.ev("document.querySelectorAll('.tile.arr').length") == 1, "POLL_MS = 60000 : une fois la case cochee, l'arrivee sonne et marque la tuile en moins de 6 s")
        await dan.close(); await o.ctx.close()
        await br.close()
    for c in (zoe, spect):
        await c.close()


try:
    asyncio.run(main())
finally:
    for pr in (http, pres):
        pr.kill()
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
