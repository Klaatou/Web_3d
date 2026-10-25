#!/usr/bin/env python3
"""Tests v47 : carte des mondes (visiteurs et promeneurs, adresse facultative, en-tête de regions.json, carte.html universelle).

Vérifie : le serveur de présence répond « visitors » par salon (promeneurs et spectateurs) en plus de « rooms » (promeneurs) ; regions.json en liste simple
ou en objet {"showUrl", "regions"} (carte universelle, carte autonome, carte ouverte par M dans une région) ; --register garde l'en-tête et la forme du
fichier ; tuile : nom, « N visiteurs · N en promenade » ou « aucun visiteur », bulle au survol, aucune adresse par défaut ; case « Afficher les
adresses » (état de départ = showUrl, choix du visiteur mémorisé et prioritaire) ; ancien serveur (sans « visitors ») : promeneurs seulement ;
regions.json absent : message précis ; ouverture depuis le disque : « serveur web » ; anglais. Un vrai téléphone, Edge et Windows : non testés ici.

Prérequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v47.py
"""
import asyncio, json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

print("--- 0. fabrication des pages")
site = tmp / "site"; site.mkdir()
sol_glb(site / "sol.glb")
pres, pport = lancer_presence()
PRES = f"ws://127.0.0.1:{pport}"


def fiche(nom, room, x, y, presence=PRES):
    return {"name": nom, "url": f"{nom.lower()}.html", "x": x, "y": y, "spawn": "", "room": room, "thumb": "", "presence": presence}


REGS = [fiche("Alpha", "v47a", 0, 0), fiche("Beta", "v47b", 1, 0), fiche("Gamma", "v47c", 2, 0)]
(site / "regions.json").write_text(json.dumps({"showUrl": False, "regions": REGS}), encoding="utf-8")
shutil.copy(DIST / "carte.html", site / "carte.html")
rapport((DIST / "carte.html").is_file(), "build.py dépose dist/carte.html")
page = (site / "carte.html").read_text(encoding="utf-8")
rapport('"mapUrl": "regions.json"' in page and '"map": []' in page and not any(x in page for x in ("__CONFIG__", "__TITLE", "__I18N__", "__VERSION__")), "carte.html universelle : aucune région dedans, lit regions.json")

# région : la carte ouverte par M (en-tête dans regions.json)
html(site / "sol.glb", "-o", site / "Gamma.html", "--shared-shell", "--no-sea", "--target", "0,0,0", "--presence-url", PRES, "--room", "v47c", "--map-url", "regions.json")

# --register : garde l'en-tête et la forme du fichier
objf = tmp / "obj.json"; objf.write_text(json.dumps({"showUrl": True, "regions": REGS[:2]}), encoding="utf-8")
html(site / "sol.glb", "-o", tmp / "Reg.html", "--shared-shell", "--no-sea", "--register", objf, "--region-name", "Delta", "--room", "v47d")
d = json.loads(objf.read_text(encoding="utf-8"))
rapport(isinstance(d, dict) and d.get("showUrl") is True and [r["name"] for r in d["regions"]] == ["Alpha", "Beta", "Delta"], "--register : l'en-tête showUrl et la forme objet sont gardés", d if not isinstance(d, dict) else list(d))
lstf = tmp / "liste.json"; lstf.write_text(json.dumps(REGS[:2]), encoding="utf-8")
html(site / "sol.glb", "-o", tmp / "Reg2.html", "--shared-shell", "--no-sea", "--register", lstf, "--region-name", "Delta", "--room", "v47d")
d = json.loads(lstf.read_text(encoding="utf-8"))
rapport(isinstance(d, list) and len(d) == 3, "--register : un fichier en liste simple reste une liste", type(d).__name__)

# carte autonome (liste figée) lue depuis un fichier en objet
html("--map", objf, "--map-page", site / "autonome.html")
cfgj = json.loads(re.search(r'id="cfg">(.*?)</script>', (site / "autonome.html").read_text(encoding="utf-8"), re.S).group(1))
rapport(cfgj.get("showUrl") is True and len(cfgj["map"]) == 3, "carte autonome : regions.json en objet lu, showUrl repris", (cfgj.get("showUrl"), len(cfgj["map"])))

# site sans regions.json, et site avec une liste simple
site3 = tmp / "site3"; site3.mkdir(); shutil.copy(DIST / "carte.html", site3 / "carte.html")
site2 = tmp / "site2"; site2.mkdir(); shutil.copy(DIST / "carte.html", site2 / "carte.html")
(site2 / "regions.json").write_text(json.dumps(REGS[:2]), encoding="utf-8")
http, hport = serveur(site); http2, hport2 = serveur(site2); http3, hport3 = serveur(site3)
BASE = f"http://127.0.0.1:{hport}/"

TUILES = """() => [...document.querySelectorAll('.tile')].map(t => ({ nom: t.querySelector('b').textContent, ligne: (t.querySelector('span') || {}).textContent || '', adresse: !!t.querySelector('small'), bulle: t.title }))"""


async def tuiles(o, attente="document.querySelector('.tile span')"):
    await o.attendre(attente, 20)
    return {t["nom"]: t for t in await o.ev(TUILES)}


async def main():
    import websockets.asyncio.client, websockets.asyncio.server
    # --- 1. le serveur : visitors (promeneurs + spectateurs) et rooms (promeneurs)
    print("--- 1. serveur de présence : visitors")
    marcheur = await websockets.asyncio.client.connect(PRES)
    await marcheur.send(json.dumps({"t": "hello", "name": "Zoe", "room": "v47a", "uid": "abcdef0123456789abcdef01", "spectator": False}))
    await asyncio.wait_for(marcheur.recv(), 5)
    spectateur = await websockets.asyncio.client.connect(PRES)
    await spectateur.send(json.dumps({"t": "hello", "room": "v47a", "uid": "0123456789abcdef01234567", "spectator": True}))
    await asyncio.wait_for(spectateur.recv(), 5)
    q = await websockets.asyncio.client.connect(PRES)
    await q.send(json.dumps({"t": "rooms"}))
    m = json.loads(await asyncio.wait_for(q.recv(), 5))
    rapport(m.get("rooms") == {"v47a": 1} and m.get("visitors") == {"v47a": 2} and m.get("spectators") == 1, "rooms = promeneurs, visitors = promeneurs + spectateurs, par salon", m)
    await q.close()

    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)

        # --- 2. carte universelle (français)
        print("--- 2. carte.html universelle (français)")
        o = await Onglet(br).ouvrir(BASE + "carte.html", locale="fr-FR", viewer=False)
        t = await tuiles(o, "document.querySelector('.tile span')")
        rapport(set(t) == {"Alpha", "Beta", "Gamma"}, "trois tuiles lues dans regions.json (objet avec en-tête)", list(t))
        rapport(t["Alpha"]["ligne"] == "2 visiteurs · 1 en promenade", "Alpha : « 2 visiteurs · 1 en promenade »", t["Alpha"]["ligne"])
        rapport(t["Beta"]["ligne"] == "aucun visiteur", "Beta : « aucun visiteur »", t["Beta"]["ligne"])
        corps = await o.ev("document.body.innerText")
        rapport("visiter" not in corps, "plus de mot « visiter → » sur les tuiles")
        rapport(not any(x["adresse"] for x in t.values()), "aucune adresse affichée par défaut")
        rapport(all("Cliquer pour entrer dans la région" in x["bulle"] for x in t.values()) and "arrivée : default" in t["Alpha"]["bulle"], "bulle au survol sur chaque tuile", t["Alpha"]["bulle"])
        rapport(await o.ev("document.getElementById('showurl').checked") is False and "Afficher les adresses" in corps, "case « Afficher les adresses » décochée (showUrl faux dans le fichier)")
        await o.ev("document.getElementById('showurl').click()")
        t = await tuiles(o)
        rapport(all(x["adresse"] for x in t.values()), "case cochée : les adresses apparaissent")
        adr = await o.ev("document.querySelector('.tile small').textContent")
        rapport(adr.startswith("http://127.0.0.1:") and adr.endswith("#spawn=default"), "l'adresse affichée est celle du lien", adr)
        await o.pg.reload()
        t = await tuiles(o)
        rapport(await o.ev("document.getElementById('showurl').checked") and all(x["adresse"] for x in t.values()), "choix du visiteur mémorisé après rechargement")
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()

        # en-tête showUrl vrai : état de départ coché ; le choix du visiteur l'emporte
        (site / "regions.json").write_text(json.dumps({"showUrl": True, "regions": REGS}), encoding="utf-8")
        o = await Onglet(br).ouvrir(BASE + "carte.html", locale="fr-FR", viewer=False)
        t = await tuiles(o)
        rapport(await o.ev("document.getElementById('showurl').checked") and all(x["adresse"] for x in t.values()), "showUrl vrai dans l'en-tête : adresses visibles et case cochée au départ")
        await o.ev("document.getElementById('showurl').click()")
        await o.pg.reload()
        t = await tuiles(o)
        rapport(not await o.ev("document.getElementById('showurl').checked") and not any(x["adresse"] for x in t.values()), "le choix du visiteur (décocher) l'emporte sur l'en-tête")
        await o.ctx.close()
        (site / "regions.json").write_text(json.dumps({"showUrl": False, "regions": REGS}), encoding="utf-8")

        # --- 3. anglais
        print("--- 3. anglais")
        o = await Onglet(br).ouvrir(BASE + "carte.html", locale="en-US", viewer=False)
        t = await tuiles(o)
        corps = await o.ev("document.body.innerText")
        rapport(t["Alpha"]["ligne"] == "2 visitors · 1 walking" and t["Beta"]["ligne"] == "no visitors" and "Show addresses" in corps, "anglais : « 2 visitors · 1 walking », « no visitors », « Show addresses »", (t["Alpha"]["ligne"], t["Beta"]["ligne"]))
        rapport("Click to enter the region" in t["Alpha"]["bulle"], "bulle en anglais", t["Alpha"]["bulle"])
        await o.ctx.close()

        # --- 4. liste simple, fichier absent, ouverture depuis le disque
        print("--- 4. liste simple, regions.json absent, ouverture depuis le disque")
        o = await Onglet(br).ouvrir(f"http://127.0.0.1:{hport2}/carte.html", locale="fr-FR", viewer=False)
        t = await tuiles(o, "document.querySelector('.tile')")
        rapport(set(t) == {"Alpha", "Beta"}, "regions.json en liste simple : toujours lu", list(t))
        await o.ctx.close()
        o = await Onglet(br).ouvrir(f"http://127.0.0.1:{hport3}/carte.html", locale="fr-FR", viewer=False)
        await o.attendre("document.getElementById('grid').textContent.includes('Impossible de lire')", 15)
        rapport("regions.json" in await o.ev("document.getElementById('grid').textContent"), "regions.json absent : message précis", await o.ev("document.getElementById('grid').textContent"))
        await o.ctx.close()
        o = await Onglet(br).ouvrir((site3 / "carte.html").as_uri(), locale="fr-FR", viewer=False)
        await o.pg.wait_for_timeout(600)
        g = await o.ev("document.getElementById('grid').textContent")
        rapport("serveur web" in g, "ouverte depuis le disque : demande un serveur web", g)
        await o.ctx.close()
        o = await Onglet(br).ouvrir((site / "autonome.html").as_uri(), locale="fr-FR", viewer=False)
        t = await tuiles(o, "document.querySelector('.tile')")
        rapport(set(t) == {"Alpha", "Beta", "Delta"} and all(x["adresse"] for x in t.values()), "carte autonome (liste figée) : marche depuis le disque, showUrl de l'en-tête repris", list(t))
        await o.ctx.close()

        # --- 5. ancien serveur : seulement les promeneurs
        print("--- 5. ancien serveur (sans visitors)")
        vieux = port_libre()

        async def faux(ws):
            async for raw in ws:
                await ws.send(json.dumps({"t": "rooms", "rooms": {"v47a": 2}, "spectators": 0}))

        srv = await websockets.asyncio.server.serve(faux, "127.0.0.1", vieux)
        site4 = tmp / "site4"; site4.mkdir(); shutil.copy(DIST / "carte.html", site4 / "carte.html")
        (site4 / "regions.json").write_text(json.dumps([fiche("Alpha", "v47a", 0, 0, f"ws://127.0.0.1:{vieux}"), fiche("Beta", "v47b", 1, 0, f"ws://127.0.0.1:{vieux}")]), encoding="utf-8")
        http4, hport4 = serveur(site4)
        o = await Onglet(br).ouvrir(f"http://127.0.0.1:{hport4}/carte.html", locale="fr-FR", viewer=False)
        t = await tuiles(o)
        rapport(t["Alpha"]["ligne"] == "2 en promenade" and t["Beta"]["ligne"] == "0 en promenade", "ancien serveur : « 2 en promenade », « 0 en promenade » (pas de visiteurs inventés)", (t["Alpha"]["ligne"], t["Beta"]["ligne"]))
        await o.ctx.close()
        http4.kill(); srv.close()

        # --- 6. carte ouverte par M dans une région (en-tête dans regions.json)
        print("--- 6. carte ouverte dans une région")
        o = await Onglet(br).ouvrir(BASE + "index.html?region=Gamma#name=Zoe")
        await o.ev("document.getElementById('mapBtn').click()")
        await o.attendre("document.querySelectorAll('#mapGrid .mapTile').length === 3", 20)
        await o.attendre("[...document.querySelectorAll('#mapGrid .mapTile')].some(b => b.textContent.includes('2 visiteurs'))", 20)
        tl = {b["nom"]: b for b in await o.ev("() => [...document.querySelectorAll('#mapGrid .mapTile')].map(b => ({ nom: b.querySelector('b').textContent, ligne: (b.querySelector('span') || {}).textContent || '', bulle: b.title }))")}
        rapport(tl["Alpha"]["ligne"] == "2 visiteurs · 1 en promenade" and tl["Beta"]["ligne"] == "aucun visiteur", "carte de la région : visiteurs et promeneurs en texte", (tl["Alpha"]["ligne"], tl["Beta"]["ligne"]))
        rapport(tl["Gamma"]["ligne"].startswith("● vous êtes ici") and "un clic ferme la carte" in tl["Gamma"]["bulle"], "région courante : « ● vous êtes ici » et sa bulle", tl["Gamma"])
        rapport("Cliquer pour entrer dans la région" in tl["Alpha"]["bulle"] and "visiter" not in await o.ev("document.getElementById('mapGrid').innerText"), "bulle au survol, plus de « visiter → »")
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()
        await br.close()
    for c in (marcheur, spectateur):
        await c.close()


try:
    asyncio.run(main())
finally:
    for pr in (http, http2, http3, pres):
        pr.kill()
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
