#!/usr/bin/env python3
"""Carte des mondes : pseudos des promeneurs (option --map-names du serveur de presence) et nombres sans doublon (visiteurs, promeneurs).

Verifie avec de vrais serveurs de presence (un sans l'option, un avec) et Chromium :
- sans --map-names : la reponse « rooms » ne contient aucun pseudo ; la carte n'en affiche pas ;
- avec --map-names : « names » donne les pseudos des promeneurs par salon, du plus recent au plus ancien, sans les spectateurs ;
- tuiles : « 1 promeneur » (tous les visiteurs marchent : un seul nombre), « 2 visiteurs, dont 1 en promenade », « 1 visiteur » (spectateur seul),
  « aucun visiteur » ; cinq pseudos au plus puis « et 2 autres » ; le total suit la meme regle ; anglais ; carte ouverte par M dans une region ;
- un pseudo piege (« <b>x</b> », « <img> ») venu d'un serveur quelconque reste du texte, jamais du HTML.

Prerequis : python build.py ; pip install playwright websockets. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/carte_pseudos.py
"""
import asyncio, json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

print("--- 0. montage")
site = tmp / "site"; site.mkdir()
sol_glb(site / "sol.glb")
sans, p_sans = lancer_presence()
avec, p_avec = lancer_presence("--map-names", "--max-per-ip", "50")     # une seule adresse pour tous les clients : on leve la limite de connexions par adresse
fport = port_libre()
S, A, F = (f"ws://127.0.0.1:{p}" for p in (p_sans, p_avec, fport))


def fiche(nom, room, x, y, presence):
    return {"name": nom, "url": f"{nom.lower()}.html", "x": x, "y": y, "spawn": "", "room": room, "thumb": "", "presence": presence}


REGS = [fiche("Alpha", "ca", 0, 0, S), fiche("Beta", "cb", 1, 0, A), fiche("Gamma", "cc", 2, 0, A), fiche("Delta", "cd", 3, 0, A),
        fiche("Epsilon", "ce", 4, 0, A), fiche("Zeta", "cz", 5, 0, F), fiche("Eta", "ch", 6, 0, A)]
(site / "regions.json").write_text(json.dumps({"showUrl": False, "regions": REGS}), encoding="utf-8")
shutil.copy(DIST / "carte.html", site / "carte.html")
html(site / "sol.glb", "-o", site / "Page.html", "--shared-shell", "--no-sea", "--target", "0,0,0", "--presence-url", A, "--room", "cx", "--map-url", "regions.json")
http, hport = serveur(site)
BASE = f"http://127.0.0.1:{hport}/"
TUILES = """() => [...document.querySelectorAll('.tile')].map(t => ({ nom: t.querySelector('b').textContent, ligne: (t.querySelector('span') || {}).textContent || '', nb: t.querySelectorAll('b').length, imgs: t.querySelectorAll('img').length }))"""


async def main():
    import websockets.asyncio.client, websockets.asyncio.server
    ouverts = []

    async def venir(url, room, nom, spectateur=False):
        c = await websockets.asyncio.client.connect(url); ouverts.append(c)
        h = {"t": "hello", "room": room, "uid": os.urandom(12).hex(), "spectator": spectateur}
        if nom:
            h["name"] = nom
        await c.send(json.dumps(h)); await asyncio.wait_for(c.recv(), 5)
        return c

    async def rooms(url):
        c = await websockets.asyncio.client.connect(url)
        await c.send(json.dumps({"t": "rooms"}))
        m = json.loads(await asyncio.wait_for(c.recv(), 5)); await c.close(); return m

    async def faux(ws):
        m = json.loads(await ws.recv())
        if m.get("t") == "rooms":
            await ws.send(json.dumps({"t": "rooms", "rooms": {"cz": 1}, "visitors": {"cz": 1}, "spectators": 0, "names": {"cz": ["<b>x</b>", "A<img src=x>"]}}))
    fs = await websockets.asyncio.server.serve(faux, "127.0.0.1", fport)

    await venir(S, "ca", "Ana")                                   # serveur sans option : un promeneur
    await venir(A, "cb", "Ana"); await venir(A, "cb", None, True)    # un promeneur et un spectateur
    await venir(A, "cc", None, True)                              # un spectateur seul
    await venir(A, "cd", "Bob")                                   # un promeneur seul
    for i in range(1, 8):                                         # sept promeneurs, arrivee dans l'ordre
        await venir(A, "ce", f"W{i}"); await asyncio.sleep(0.05)

    print("--- 1. serveurs : le champ names")
    m = await rooms(S)
    rapport("names" not in m and m.get("rooms") == {"ca": 1}, "sans --map-names : aucun pseudo dans la reponse", m)
    m = await rooms(A)
    rapport(m.get("names") == {"cb": ["Ana"], "cd": ["Bob"], "ce": ["W7", "W6", "W5", "W4", "W3", "W2", "W1"]}, "avec --map-names : pseudos des promeneurs, le plus recent d'abord, sans spectateurs ni salon vide", m.get("names"))
    rapport(m.get("visitors", {}).get("cb") == 2 and m.get("rooms", {}).get("cb") == 1, "les nombres (visitors, rooms) ne changent pas", m)

    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        cond = "[...document.querySelectorAll('.tile')].filter(t => t.querySelector('span')).length === 7"

        async def pret(o):
            try:
                await o.attendre(cond, 25)
            except Exception:
                print("   tuiles au moment de l'echec :", [(x["nom"], x["ligne"]) for x in await o.ev(TUILES)], o.errs[:3])
                raise

        print("--- 2. carte.html (francais)")
        o = await Onglet(br).ouvrir(BASE + "carte.html", locale="fr-FR", viewer=False)
        await pret(o)
        t = {x["nom"]: x for x in await o.ev(TUILES)}
        rapport(t["Alpha"]["ligne"] == "1 promeneur", "sans option : « 1 promeneur » seul, aucun pseudo", t["Alpha"]["ligne"])
        rapport(t["Beta"]["ligne"] == "2 visiteurs, dont 1 en promenade\nAna", "« 2 visiteurs, dont 1 en promenade » puis le pseudo", t["Beta"]["ligne"])
        rapport(t["Gamma"]["ligne"] == "1 visiteur", "spectateur seul : « 1 visiteur », pas de pseudo", t["Gamma"]["ligne"])
        rapport(t["Delta"]["ligne"] == "1 promeneur\nBob", "un promeneur seul : « 1 promeneur » (pas de visiteur en double) puis son pseudo", t["Delta"]["ligne"])
        rapport(t["Epsilon"]["ligne"] == "7 promeneurs\nW7, W6, W5, W4, W3 et 2 autres", "sept promeneurs : cinq pseudos puis « et 2 autres »", t["Epsilon"]["ligne"])
        rapport(t["Eta"]["ligne"] == "aucun visiteur", "salon vide : « aucun visiteur »", t["Eta"]["ligne"])
        rapport(t["Zeta"]["ligne"] == "1 promeneur\n<b>x</b>, A<img src=x>" and t["Zeta"]["nb"] == 1 and t["Zeta"]["imgs"] == 0, "pseudos pieges : du texte, ni <b> ni <img> dans la tuile", t["Zeta"])
        tot = await o.ev("document.getElementById('total').textContent")
        rapport(tot == "7 régions · Total : 13 visiteurs, dont 11 en promenade", "total sur la meme regle", tot)
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()

        print("--- 3. carte.html (anglais)")
        o = await Onglet(br).ouvrir(BASE + "carte.html", locale="en-GB", viewer=False)
        await pret(o)
        t = {x["nom"]: x for x in await o.ev(TUILES)}
        rapport(t["Beta"]["ligne"] == "2 visitors, 1 walking\nAna" and t["Delta"]["ligne"] == "1 walker\nBob" and t["Epsilon"]["ligne"] == "7 walkers\nW7, W6, W5, W4, W3 and 2 others",
                "anglais : « 2 visitors, 1 walking », « 1 walker », « and 2 others »", (t["Beta"]["ligne"], t["Delta"]["ligne"], t["Epsilon"]["ligne"]))
        await o.ctx.close()

        print("--- 4. carte ouverte par M dans une region")
        o = await Onglet(br).ouvrir(BASE + "index.html?region=Page#name=Zoe")
        await o.ev("document.getElementById('mapBtn').click()")
        await o.attendre("document.querySelectorAll('#mapGrid .mapTile').length === 7", 20)
        await o.attendre("[...document.querySelectorAll('#mapGrid .mapTile')].some(b => b.textContent.includes('autres'))", 25)
        tl = {b["nom"]: b["ligne"] for b in await o.ev("() => [...document.querySelectorAll('#mapGrid .mapTile')].map(b => ({ nom: b.querySelector('b').textContent, ligne: (b.querySelector('span') || {}).textContent || '' }))")}
        rapport(tl["Beta"] == "2 visiteurs, dont 1 en promenade\nAna" and tl["Delta"] == "1 promeneur\nBob" and tl["Epsilon"] == "7 promeneurs\nW7, W6, W5, W4, W3 et 2 autres" and tl["Alpha"] == "1 promeneur",
                "carte de la region : memes lignes", tl)
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()
        await br.close()
    fs.close()
    for c in ouverts:
        await c.close()


try:
    asyncio.run(main())
finally:
    for pr in (http, sans, avec):
        pr.kill()
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
