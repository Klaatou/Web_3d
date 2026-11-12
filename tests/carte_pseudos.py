#!/usr/bin/env python3
"""Carte des mondes : pseudos protégés par une clé (option --map-names-key du serveur de présence, #pseudos=CLE sur la carte) et nombres sans doublon.

Vérifie avec de vrais serveurs de présence et Chromium :
- le serveur : sans clé ou avec une mauvaise clé, aucun pseudo ; avec la bonne clé, « names » (promeneurs, le plus récent d'abord) et « viewers »
  (visiteurs en vue globale, y compris un promeneur qui y est repassé) ; 5 clés refusées par minute et par adresse ; clé de 8 caractères au moins ;
  l'ancienne option --map-names ne donne plus aucun pseudo (avertissement) ;
- la carte : sans #pseudos= seulement les nombres ; avec la bonne clé les pseudos (français, anglais, carte ouverte par M) ; mauvaise clé : rien ;
  « 1 promeneur » (tous les visiteurs marchent : un seul nombre), « 2 visiteurs, dont 1 en promenade », « 1 visiteur », « aucun visiteur » ;
  cinq pseudos au plus puis « et 2 autres » ; le total suit la même règle ;
- un pseudo piégé (« <b>x</b> ») venu d'un serveur quelconque reste du texte, jamais du HTML.

Prérequis : python build.py ; pip install playwright websockets. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/carte_pseudos.py
"""
import asyncio, json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

CLE = "CLE_SECRETE_12"
print("--- 0. montage")
site = tmp / "site"; site.mkdir()
sol_glb(site / "sol.glb")
sans, p_sans = lancer_presence()                                           # serveur sans l'option
avec, p_avec = lancer_presence("--map-names-key", CLE, "--max-per-ip", "50")   # serveur avec la clé (une seule adresse pour tous les clients : on lève la limite par adresse)
fport = port_libre()
S, A, F = (f"ws://127.0.0.1:{p}" for p in (p_sans, p_avec, fport))


def fiche(nom, room, x, y, presence):
    return {"name": nom, "url": f"{nom.lower()}.html", "x": x, "y": y, "spawn": "", "room": room, "thumb": "", "presence": presence}


REGS = [fiche("Alpha", "ca", 0, 0, S), fiche("Beta", "cb", 1, 0, A), fiche("Gamma", "cc", 2, 0, A), fiche("Delta", "cd", 3, 0, A),
        fiche("Epsilon", "ce", 4, 0, A), fiche("Zeta", "cz", 5, 0, F), fiche("Eta", "ch", 6, 0, A), fiche("Phi", "cf", 7, 0, A)]
(site / "regions.json").write_text(json.dumps({"showUrl": False, "regions": REGS}), encoding="utf-8")
shutil.copy(DIST / "carte.html", site / "carte.html")
html(site / "sol.glb", "-o", site / "Page.html", "--shared-shell", "--no-sea", "--target", "0,0,0", "--presence-url", A, "--room", "cx", "--map-url", "regions.json")
http, hport = serveur(site)
BASE = f"http://127.0.0.1:{hport}/"
TUILES = """() => [...document.querySelectorAll('.tile')].map(t => ({ nom: t.querySelector('b').textContent, ligne: (t.querySelector('span') || {}).textContent || '', nb: t.querySelectorAll('b').length, ni: t.querySelectorAll('i').length, imgs: t.querySelectorAll('img').length }))"""
extra_procs = []


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

    async def rooms(url, key=None):
        c = await websockets.asyncio.client.connect(url)
        await c.send(json.dumps({"t": "rooms", "key": key} if key is not None else {"t": "rooms"}))
        m = json.loads(await asyncio.wait_for(c.recv(), 5)); await c.close(); return m

    recus = []      # 1.10.5 : les cles recues par le faux serveur (None : requete sans cle)

    async def faux(ws):      # un serveur quelconque, qui donne des pseudos pièges avec la bonne clé
        m = json.loads(await ws.recv())
        if m.get("t") == "rooms":
            recus.append(m.get("key"))
            rep = {"t": "rooms", "rooms": {"cz": 1}, "visitors": {"cz": 1}, "spectators": 0}
            if m.get("key") == CLE:
                rep.update(names={"cz": ["<b>x</b>", "A<img src=x>"]}, viewers={"cz": ["<i>y</i>"]})
            await ws.send(json.dumps(rep))
    fs = await websockets.asyncio.server.serve(faux, "127.0.0.1", fport)

    await venir(S, "ca", "Ana")                                      # serveur sans l'option : un promeneur
    await venir(A, "cb", "Ana"); await venir(A, "cb", "Cléo", True)   # un promeneur et un visiteur en vue globale
    await venir(A, "cc", "Dan", True)                                # un visiteur en vue globale seul
    await venir(A, "cd", "Bob")                                      # un promeneur seul
    for i in range(1, 8):                                            # sept promeneurs, arrivée dans l'ordre
        await venir(A, "ce", f"W{i}"); await asyncio.sleep(0.05)
    eva = await venir(A, "cf", "Eva")                                # un promeneur qui repasse en vue globale : son pseudo ne doit pas disparaître
    await eva.send(json.dumps({"t": "role", "walker": False})); await asyncio.sleep(0.4)

    print("--- 1. le serveur : clé, names et viewers")
    m = await rooms(S, CLE)
    rapport("names" not in m and "viewers" not in m and m.get("rooms") == {"ca": 1}, "serveur sans option : aucun pseudo, même avec une clé", m)
    m = await rooms(A)
    rapport("names" not in m and "viewers" not in m, "sans clé : aucun pseudo", m)
    m = await rooms(A, "MAUVAISE_CLE_1")
    rapport("names" not in m and "viewers" not in m, "mauvaise clé : aucun pseudo, même réponse que sans clé", m)
    m = await rooms(A, CLE)
    rapport(m.get("names") == {"cb": ["Ana"], "cd": ["Bob"], "ce": ["W7", "W6", "W5", "W4", "W3", "W2", "W1"]}, "bonne clé : pseudos des promeneurs, le plus récent d'abord, sans salon sans promeneur", m.get("names"))
    rapport(m.get("viewers") == {"cb": ["Cléo"], "cc": ["Dan"], "cf": ["Eva"]}, "bonne clé : visiteurs en vue globale, dont celui qui a cessé de marcher (Eva)", m.get("viewers"))
    rapport(m.get("visitors", {}).get("cb") == 2 and m.get("rooms", {}).get("cb") == 1, "les nombres (visitors, rooms) ne changent pas", m)

    print("--- 2. serveur : clé trop courte, ancienne option")
    r = subprocess.run([sys.executable, str(DIST / "presence_server.py"), "--map-names-key", "abc"], capture_output=True, text=True, timeout=30, cwd=tmp)
    rapport(r.returncode == 2 and "8 caract" in r.stderr, "clé de moins de 8 caractères : le serveur refuse de démarrer", (r.returncode, r.stderr[-160:]))
    vieux, p_vieux = lancer_presence("--map-names"); extra_procs.append(vieux)
    m = await rooms(f"ws://127.0.0.1:{p_vieux}", CLE)
    vieux.kill(); sortie = vieux.stdout.read()
    rapport("names" not in m and "n'existe plus" in sortie, "ancienne option --map-names : aucun pseudo et un avertissement", (list(m), sortie[-200:]))

    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        cond = "[...document.querySelectorAll('.tile')].filter(t => t.querySelector('span')).length === 8"

        async def pret(o):
            try:
                await o.attendre(cond, 25)
            except Exception:
                print("   tuiles au moment de l'échec :", [(x["nom"], x["ligne"]) for x in await o.ev(TUILES)], o.errs[:3])
                raise

        async def lire(url, locale="fr-FR"):
            o = await Onglet(br).ouvrir(url, locale=locale, viewer=False)
            await pret(o)
            return o, {x["nom"]: x for x in await o.ev(TUILES)}

        print("--- 3. carte.html sans clé (visiteur ordinaire) : seulement les nombres")
        o, t = await lire(BASE + "carte.html")
        attendu = {"Alpha": "1 promeneur", "Beta": "2 visiteurs, dont 1 en promenade", "Gamma": "1 visiteur", "Delta": "1 promeneur", "Epsilon": "7 promeneurs", "Zeta": "1 promeneur", "Eta": "aucun visiteur", "Phi": "1 visiteur"}
        rapport({k: v["ligne"] for k, v in t.items()} == attendu, "sans clé : un seul nombre par tuile, aucun pseudo", {k: v["ligne"] for k, v in t.items()})
        tot = await o.ev("document.getElementById('total').textContent")
        rapport(tot == "8 régions · Total : 14 visiteurs, dont 11 en promenade", "total sur la même règle", tot)
        await o.ctx.close()

        print("--- 4. carte.html avec une mauvaise clé : rien de plus")
        o, t = await lire(BASE + "carte.html#pseudos=MAUVAISE_CLE_1")
        rapport({k: v["ligne"] for k, v in t.items()} == attendu, "mauvaise clé : exactement la même carte que sans clé", {k: v["ligne"] for k, v in t.items()})
        await o.ctx.close()

        print("--- 5. carte.html avec la bonne clé (français)")
        o, t = await lire(BASE + "carte.html#pseudos=" + CLE)
        await o.attendre("[...document.querySelectorAll('.tile span')].some(s => s.textContent.includes('autres'))", 25)
        t = {x["nom"]: x for x in await o.ev(TUILES)}
        L = {k: v["ligne"] for k, v in t.items()}
        rapport(L["Alpha"] == "1 promeneur", "serveur sans option : jamais de pseudo", L["Alpha"])
        rapport(L["Beta"] == "2 visiteurs, dont 1 en promenade\nAna\nen vue globale : Cléo", "promeneur puis visiteur en vue globale", L["Beta"])
        rapport(L["Gamma"] == "1 visiteur\nen vue globale : Dan", "visiteur en vue globale seul : son pseudo est donné", L["Gamma"])
        rapport(L["Delta"] == "1 promeneur\nBob", "un promeneur seul : « 1 promeneur » (pas de visiteur en double) puis son pseudo", L["Delta"])
        rapport(L["Epsilon"] == "7 promeneurs\nW7, W6, W5, W4, W3 et 2 autres", "sept promeneurs : cinq pseudos puis « et 2 autres »", L["Epsilon"])
        rapport(L["Phi"] == "1 visiteur\nen vue globale : Eva", "un promeneur repassé en vue globale garde son pseudo sur la carte", L["Phi"])
        rapport(L["Eta"] == "aucun visiteur", "salon vide : « aucun visiteur »", L["Eta"])
        z = t["Zeta"]
        rapport(z["ligne"] == "1 promeneur\n<b>x</b>, A<img src=x>\nen vue globale : <i>y</i>" and z["nb"] == 1 and z["ni"] == 0 and z["imgs"] == 0, "pseudos pièges : du texte, ni <b>, ni <i>, ni <img> dans la tuile", z)
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()

        print("--- 5b. carte.html avec deux # (#name=...#pseudos=...)")
        o, _ = await lire(BASE + "carte.html#name=Klaatou#pseudos=" + CLE)
        await o.attendre("[...document.querySelectorAll('.tile span')].some(s => s.textContent.includes('autres'))", 25)
        L2 = {x["nom"]: x["ligne"] for x in await o.ev(TUILES)}
        rapport(L2["Beta"] == "2 visiteurs, dont 1 en promenade\nAna\nen vue globale : Cléo", "adresse avec deux # : la clé est bien lue", L2["Beta"])
        await o.ctx.close()

        print("--- 6. carte.html avec la bonne clé (anglais)")
        o, t = await lire(BASE + "carte.html#pseudos=" + CLE, "en-GB")
        await o.attendre("[...document.querySelectorAll('.tile span')].some(s => s.textContent.includes('others'))", 25)
        t = {x["nom"]: x["ligne"] for x in await o.ev(TUILES)}
        rapport(t["Beta"] == "2 visitors, 1 walking\nAna\nglobal view: Cléo" and t["Delta"] == "1 walker\nBob" and t["Epsilon"] == "7 walkers\nW7, W6, W5, W4, W3 and 2 others",
                "anglais : « 2 visitors, 1 walking », « global view: », « and 2 others »", (t["Beta"], t["Delta"], t["Epsilon"]))
        await o.ctx.close()

        print("--- 7. carte ouverte par M dans une région")
        for hash_, avec_pseudos in (("#name=Zoe", False), ("#name=Zoe&pseudos=" + CLE, True)):
            o = await Onglet(br).ouvrir(BASE + "index.html?region=Page" + hash_)
            await o.ev("document.getElementById('mapBtn').click()")
            await o.attendre("document.querySelectorAll('#mapGrid .mapTile').length === 8", 20)
            await o.attendre("[...document.querySelectorAll('#mapGrid .mapTile')].filter(b => b.querySelector('span')).length === 8", 25)
            if avec_pseudos:
                await o.attendre("[...document.querySelectorAll('#mapGrid .mapTile')].some(b => b.textContent.includes('autres'))", 25)
            tl = {b["nom"]: b["ligne"] for b in await o.ev("() => [...document.querySelectorAll('#mapGrid .mapTile')].map(b => ({ nom: b.querySelector('b').textContent, ligne: (b.querySelector('span') || {}).textContent || '' }))")}
            if avec_pseudos:
                rapport(tl["Beta"] == "2 visiteurs, dont 1 en promenade\nAna\nen vue globale : Cléo" and tl["Phi"] == "1 visiteur\nen vue globale : Eva" and tl["Epsilon"] == "7 promeneurs\nW7, W6, W5, W4, W3 et 2 autres",
                        "carte de la région avec #pseudos= : mêmes lignes", tl)
            else:
                rapport(tl["Beta"] == "2 visiteurs, dont 1 en promenade" and tl["Epsilon"] == "7 promeneurs" and tl["Phi"] == "1 visiteur", "carte de la région sans clé : seulement les nombres", tl)
            rapport(not o.errs, "aucune erreur de page", o.errs)
            await o.ctx.close()

        print("--- 7b. clé des pseudos : champ, mémoire, état (1.10.5)")
        ETAT = "document.getElementById('keyState').textContent"
        AUTRES = "[...document.querySelectorAll('.tile span')].some(s => s.textContent.includes('autres'))"

        async def saisir(o, v):
            await o.pg.fill("#mapkey", v)
            await o.pg.dispatch_event("#mapkey", "change")

        async def lignes(o):
            return {x["nom"]: x["ligne"] for x in await o.ev(TUILES)}

        o, _ = await lire(BASE + "carte.html")
        rapport(await o.ev(ETAT) == "" and await o.ev("() => !document.getElementById('keyrow').hidden && document.getElementById('mapkey').type === 'password' && document.getElementById('mapkey').value === ''"),
                "sans clé : la rangée « Clé des pseudos » est là, champ masqué et vide, aucun état")
        await o.ev("document.getElementById('keyshow').click()")
        t1 = await o.ev("document.getElementById('mapkey').type")
        await o.ev("document.getElementById('keyshow').click()")
        rapport(t1 == "text" and await o.ev("document.getElementById('mapkey').type") == "password", "« Afficher la clé » montre le champ en clair, puis le masque de nouveau", t1)
        await saisir(o, CLE)
        await o.attendre(AUTRES, 25)
        await o.attendre("document.getElementById('keyState').textContent.includes('une partie')", 25)
        etat = await o.ev(ETAT)
        rapport(etat == "clé saisie (14 caractères) ; acceptée par une partie des serveurs seulement", "clé saisie : état « acceptée par une partie des serveurs » (celui qui n'a pas l'option la refuse)", etat)
        rapport(await o.ev("localStorage.getItem('glb2html_map_key')") == CLE, "la clé saisie est mémorisée dans ce navigateur")
        L = await lignes(o)
        rapport(L["Beta"] == "2 visiteurs, dont 1 en promenade\nAna\nen vue globale : Cléo" and L["Epsilon"] == "7 promeneurs\nW7, W6, W5, W4, W3 et 2 autres", "avec la clé du champ : les mêmes pseudos qu'avec #pseudos=", L["Beta"])
        n0 = recus.count(CLE)
        await o.ev("document.getElementById('alert').click()")      # relevé toutes les 5 s
        await asyncio.sleep(6.5)
        rapport(recus.count(CLE) - n0 >= 2, "une clé acceptée est renvoyée à chaque relevé", (n0, recus.count(CLE)))

        await o.pg.reload()
        await pret(o)
        await o.attendre(AUTRES, 25)
        await o.attendre("document.getElementById('keyState').textContent.includes('une partie')", 25)
        rapport(await o.ev(ETAT) == "clé mémorisée dans ce navigateur (14 caractères) ; acceptée par une partie des serveurs seulement" and await o.ev("document.getElementById('mapkey').value") == CLE,
                "après rechargement sans # : la clé mémorisée est reprise (champ rempli, pseudos, état « mémorisée »)", await o.ev(ETAT))

        o2 = await Onglet(br).ouvrir(BASE + "index.html?region=Page#name=Zoe", ctx=o.ctx)      # même navigateur : la carte de la région (touche M) reprend la clé mémorisée
        await o2.ev("document.getElementById('mapBtn').click()")
        await o2.attendre("[...document.querySelectorAll('#mapGrid .mapTile')].some(b => b.textContent.includes('autres'))", 30)
        tl = {b["nom"]: b["ligne"] for b in await o2.ev("() => [...document.querySelectorAll('#mapGrid .mapTile')].map(b => ({ nom: b.querySelector('b').textContent, ligne: (b.querySelector('span') || {}).textContent || '' }))")}
        rapport(tl["Beta"] == "2 visiteurs, dont 1 en promenade\nAna\nen vue globale : Cléo", "la carte de la région (touche M) reprend la clé mémorisée par la carte", tl["Beta"])
        await o2.pg.close()

        await saisir(o, "")
        await o.attendre("!document.body.textContent.includes('Cléo')", 15)
        rapport(await o.ev(ETAT) == "" and await o.ev("localStorage.getItem('glb2html_map_key')") is None, "champ vidé : plus de pseudos, plus d'état, la clé est oubliée")

        n0 = recus.count("MAUVAISE_CLE_1")
        await saisir(o, "MAUVAISE_CLE_1")
        await o.attendre("document.getElementById('keyState').textContent.includes('non acceptée')", 25)
        etat = await o.ev(ETAT)
        rapport(etat.startswith("clé saisie (14 caractères) ; non acceptée") and "elle n'est plus renvoyée" in etat, "mauvaise clé : état « non acceptée », avec la raison possible et ce qu'on peut faire", etat)
        await asyncio.sleep(6.5)      # relevés toutes les 5 s (alerte cochée) : au moins un de plus
        rapport(recus.count("MAUVAISE_CLE_1") - n0 == 1, "une clé refusée n'est plus renvoyée : une seule fois malgré plusieurs relevés", recus.count("MAUVAISE_CLE_1") - n0)
        rapport(not o.errs, "aucune erreur de page", o.errs)

        await o.pg.evaluate("localStorage.setItem('glb2html_map_key', 'AUTRE_CLE_0123')")
        await o.pg.goto(BASE + "carte.html?v=2#pseudos=" + CLE)
        await pret(o)
        await o.attendre(AUTRES, 25)
        await o.attendre("document.getElementById('keyState').textContent.includes('une partie')", 25)
        rapport(await o.ev(ETAT) == "clé lue dans l'adresse (14 caractères) ; acceptée par une partie des serveurs seulement" and await o.ev("localStorage.getItem('glb2html_map_key')") == "AUTRE_CLE_0123",
                "#pseudos= l'emporte sur la clé mémorisée et ne l'écrase pas", await o.ev(ETAT))
        await o.ctx.close()

        o, _ = await lire(BASE + "carte.html#pseudos=" + CLE, "en-GB")
        await o.attendre("document.getElementById('keyState').textContent.includes('only some')", 25)
        etat = await o.ev(ETAT)
        rapport(etat == "key read from the address (14 characters); accepted by only some of the servers" and await o.ev("document.querySelector('#keyrow span').textContent") == "Names key: ", "anglais : textes du champ et de l'état", etat)
        await o.ctx.close()

        await br.close()
    fs.close()

    print("--- 8. 5 clés refusées par minute : la sixième demande, même juste, n'est plus écoutée")
    frais, p_frais = lancer_presence("--map-names-key", CLE); extra_procs.append(frais)
    U = f"ws://127.0.0.1:{p_frais}"
    await venir(U, "cr", "Ida")
    m = await rooms(U, CLE)
    rapport(m.get("names") == {"cr": ["Ida"]}, "bonne clé avant les essais : pseudos donnés", m.get("names"))
    for _ in range(5):
        await rooms(U, "MAUVAISE_CLE_1")
    m = await rooms(U, CLE)
    rapport("names" not in m and m.get("rooms") == {"cr": 1}, "après 5 clés refusées : plus de pseudos, mais les nombres restent donnés", m)
    for c in ouverts:
        await c.close()


try:
    asyncio.run(main())
finally:
    for pr in [http, sans, avec] + extra_procs:
        pr.kill()
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
