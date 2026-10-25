#!/usr/bin/env python3
"""Tests v51 : créateurs sur le serveur de présence (--creators).

Serveur (vrai presence_server.py) : sans --creators, tout est accepté comme avant ; avec le fichier : connexion sans origine
ou d'une origine non déclarée refusée (message « refused », code 4003), créateur suspendu refusé, salon hors du préfixe refusé,
préfixe sans tenir compte de la casse, hôte sans préfixe (tous les autres salons, pas ceux d'un créateur), nombre de salons
ouverts et de promeneurs par créateur (arrivée et passage en promenade), requête « rooms » d'une origine déclarée, aucun salon
vide laissé par un refus, relecture à chaud (créateur suspendu, fichier illisible : liste gardée, fichier absent : tout refusé),
commande de console « creators », message de démarrage, journal, entrées invalides signalées.
Page : refus affiché (salon hors préfixe, origine non déclarée), connexion acceptée, anglais, viewer (origine « null »).

Prérequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v51.py
"""
import asyncio, json, os, re, subprocess, sys, threading, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37
import websockets

A, B, C = "https://hote.exemple", "https://alice.exemple", "https://bob.exemple"


def ecrire(path, d):
    path.write_text(json.dumps(d, ensure_ascii=False) if not isinstance(d, str) else d, encoding="utf-8")
    t = time.time() + 1          # date de modification nettement différente (relecture à chaud)
    os.utime(path, (t, t))


def serveur_cr(*extra, nom="srv"):
    port = port_libre()
    d = tmp / nom
    d.mkdir(exist_ok=True)
    proc = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--host", "127.0.0.1", "--port", str(port), "--identities", str(d / "id.json"),
                             "--bans", str(d / "bans.json"), "--visits-keys", str(d / "keys.json"), "--log", str(d / "presence.log"), *extra],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=d, bufsize=1)
    attendre_port(port, proc, "presence_server")
    proc.lu = []
    threading.Thread(target=lambda: [proc.lu.append(x) for x in proc.stdout], daemon=True).start()
    return proc, port, d


def console(proc, ligne, motif, s=10):
    debut = len(proc.lu)
    proc.stdin.write(ligne + "\n")
    proc.stdin.flush()
    out = ""
    for _ in range(int(s / 0.1)):
        out = "".join(proc.lu[debut:])
        if re.search(motif, out):
            return True, out
        time.sleep(0.1)
    return False, out


def sortie(proc, motif, s=10):
    for _ in range(int(s / 0.1)):
        if re.search(motif, "".join(proc.lu)):
            return True
        time.sleep(0.1)
    return False


async def essai(port, origine, salon, spectateur=False, garder=None, uid=None):
    """se connecte (avec l'en-tête Origin donné) et renvoie (premier message, code de fermeture) ; garder : liste où laisser la connexion ouverte"""
    kw = {"origin": origine} if origine else {}
    ws = await websockets.connect(f"ws://127.0.0.1:{port}", **kw)
    try:
        await ws.send(json.dumps({"t": "hello", "room": salon, "name": "T", "uid": uid or os.urandom(12).hex(), "spectator": spectateur}))
    except websockets.ConnectionClosed:
        pass
    try:
        m = json.loads(await asyncio.wait_for(ws.recv(), 5))
    except websockets.ConnectionClosed:
        m = None
    if garder is not None and m and m.get("t") == "welcome":
        garder.append(ws)
        return m, None
    try:
        await asyncio.wait_for(ws.wait_closed(), 5)
    except asyncio.TimeoutError:
        pass
    code = ws.close_code
    await ws.close()
    return m, code


async def partie_serveur():
    print("--- 1. sans --creators : tout est accepté (comme avant)")
    proc, port, d = serveur_cr(nom="libre")
    m, _ = await essai(port, None, "galerie")
    rapport(m and m.get("t") == "welcome", "sans origine ni fichier : accueilli", m)
    ok, out = console(proc, "creators", "--creators")
    rapport(ok and "toutes les pages sont acceptées" in out, "console creators : fichier absent signalé", out)
    proc.kill()

    print("--- 2. avec le fichier des créateurs")
    d = tmp / "cr"; d.mkdir()
    f = d / "presence_creators.json"
    base = {"creators": [
        {"id": "jj", "prefix": "", "origins": [A + "/", "null"], "note": "hôte"},
        {"id": "alice", "origins": [B], "maxWalkers": 2, "maxRooms": 1},
        {"id": "bob", "origins": [C], "off": True},
        {"id": "mauvais id"},
        {"id": "carl", "prefix": "c.d", "origins": ["https://carl.exemple"]},
        {"id": "dan", "origins": [B.upper()]},
    ]}
    ecrire(f, base)
    proc, port, d2 = serveur_cr("--creators", str(f), nom="cr")
    rapport(sortie(proc, r"créateurs : 4 lus dans"), "démarrage : 4 créateurs valides lus (id et préfixe invalides ignorés)", "".join(proc.lu)[-800:])
    txt = "".join(proc.lu)
    rapport("entrée 4 ignorée" in txt and "entrée 5 ignorée" in txt and "appartient déjà à alice, ignorée pour dan" in txt, "entrées invalides et origine en double signalées", txt[-900:])
    rapport(sortie(proc, r"serveur : créateurs .*presence_creators\.json \(4\)"), "message de démarrage : fichier et nombre de créateurs")

    m, code = await essai(port, None, "galerie")
    rapport(m == {"t": "refused", "why": "origin"} and code == 4003, "sans origine : refus « origin », code 4003", (m, code))
    m, code = await essai(port, "https://inconnu.exemple", "galerie")
    rapport(m == {"t": "refused", "why": "origin"} and code == 4003, "origine non déclarée : refusée", (m, code))
    m, code = await essai(port, C, "bob.galerie")
    rapport(m == {"t": "refused", "why": "off"}, "créateur suspendu : refus « off »", m)
    m, code = await essai(port, B, "zzz.vide")
    rapport(m == {"t": "refused", "why": "room"} and code == 4003, "salon hors du préfixe : refus « room »", (m, code))
    ok, out = console(proc, "rooms", r"salon|room|aucun")
    rapport("zzz.vide" not in out, "un refus ne laisse pas de salon vide", out)

    gardes = []
    m, _ = await essai(port, B, "alice.galerie", garder=gardes)
    rapport(m and m.get("t") == "welcome", "alice dans alice.galerie : accueillie", m)
    m, _ = await essai(port, B, "ALICE.galerie")
    rapport(m == {"t": "refused", "why": "rooms"}, "ALICE.galerie appartient bien à alice (casse du préfixe ignorée) : autre salon, donc refus « rooms »", m)
    m, code = await essai(port, B, "alice.autre")
    rapport(m == {"t": "refused", "why": "rooms"}, "maxRooms 1 : deuxième salon ouvert refusé", m)
    m, _ = await essai(port, B, "alice.galerie", garder=gardes)
    rapport(m and m.get("t") == "welcome", "promeneurs : 2e dans alice.galerie accepté", m)
    m, _ = await essai(port, B, "alice.galerie")
    rapport(m == {"t": "full"}, "maxWalkers 2 : 3e promeneur refusé (salon complet)", m)
    m, _ = await essai(port, B, "alice.galerie", spectateur=True, garder=gardes)
    rapport(m and m.get("t") == "welcome", "spectateur accepté malgré maxWalkers", m)
    sp = gardes[-1]
    await sp.send(json.dumps({"t": "role", "walker": True, "name": "S"}))
    m = json.loads(await asyncio.wait_for(sp.recv(), 5))
    rapport(m == {"t": "full"}, "passage en promenade refusé à la limite du créateur", m)

    m, _ = await essai(port, A, "galerie", garder=gardes)
    rapport(m and m.get("t") == "welcome", "hôte sans préfixe : salon libre accepté", m)
    m, _ = await essai(port, "null", "disque", garder=gardes)
    rapport(m and m.get("t") == "welcome", "origine « null » déclarée par l'hôte : acceptée", m)
    m, _ = await essai(port, A, "alice.x")
    rapport(m == {"t": "refused", "why": "room"}, "hôte : salon d'un créateur refusé", m)

    async with websockets.connect(f"ws://127.0.0.1:{port}", origin=A) as ws:
        await ws.send(json.dumps({"t": "rooms"}))
        m = json.loads(await ws.recv())
    rapport(m.get("t") == "rooms" and m["rooms"].get("alice.galerie") == 2 and m["rooms"].get("galerie") == 1, "requête rooms : salons de tous les créateurs", m)

    ok, out = console(proc, "creators", r"bob")
    rapport(ok and re.search(r"alice\s+préfixe : alice\.\s+actif\s+salons ouverts : 1 / 1 au plus\s+promeneurs : 2 / 2 au plus", out)
            and "préfixe : (aucun : tous les autres salons)" in out and "suspendu" in out and "origines : https://alice.exemple" in out,
            "console creators : préfixe, état, salons, promeneurs, origines", out)

    print("--- 3. relecture à chaud")
    base["creators"][1]["off"] = True
    ecrire(f, base)
    time.sleep(2.2)
    m, _ = await essai(port, B, "alice.galerie")
    rapport(m == {"t": "refused", "why": "off"}, "alice suspendue sans relancer le serveur", m)
    rapport(sortie(proc, r"créateurs : 4 lus dans.*\n(.|\n)*créateurs : 4 lus dans"), "relecture annoncée dans la console")
    rapport(all(w.state.name == "OPEN" for w in gardes[:2]), "les connexions déjà ouvertes restent")
    ecrire(f, "{ pas du json")
    time.sleep(2.2)
    m, _ = await essai(port, A, "galerie2")
    rapport(m and m.get("t") == "welcome", "fichier illisible : liste précédente gardée", m)
    rapport(sortie(proc, r"fichier des créateurs illisible"), "fichier illisible signalé")
    f.unlink()
    time.sleep(2.2)
    m, _ = await essai(port, A, "galerie3")
    rapport(m == {"t": "refused", "why": "origin"}, "fichier absent : tout refusé", m)
    rapport(sortie(proc, r"fichier des créateurs absent"), "fichier absent signalé")
    for w in gardes:
        await w.close()
    proc.kill()
    log = "".join(open(p, encoding="utf-8").read() for p in d2.glob("presence.log*"))
    rapport("origine non déclarée : https://inconnu.exemple" in log and "créateur bob suspendu" in log and "salon zzz.vide hors des salons de alice" in log,
            "journal : refus avec leur raison", log[-900:])


async def partie_page():
    site = tmp / "site"; site.mkdir()
    sol_glb(site / "sol.glb")
    http, hport = serveur(site)
    org = f"http://127.0.0.1:{hport}"
    f = tmp / "page_creators.json"
    ecrire(f, {"creators": [{"id": "alice", "origins": [org]}]})
    proc, port, _ = serveur_cr("--creators", str(f), nom="page")
    for nom, salon in (("Hors", "t51"), ("Bon", "alice.t51")):
        html(site / "sol.glb", "-o", site / f"{nom}.html", "--shared-shell", "--no-sea", "--target", "0,0,0", "--presence-url", f"ws://127.0.0.1:{port}", "--room", salon)
    from playwright.async_api import async_playwright
    try:
        async with async_playwright() as p:
            kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            if os.environ.get("CHROMIUM"):
                kw["executable_path"] = os.environ["CHROMIUM"]
            br = await p.chromium.launch(**kw)
            print("--- 4. page : salon hors du préfixe")
            o = await Onglet(br).ouvrir(org + "/index.html?region=Hors#name=Zoe")
            await o.attendre("document.getElementById('presenceStatus').textContent.includes('refusée')", 20)
            s = await o.txt("presenceStatus")
            rapport(s == "présence refusée : le salon de cette page n'appartient pas à son créateur sur ce serveur (recharge la page une fois corrigé)", "texte du refus (salon)", s)
            pr = await o.ev("window.__viewer.getPresence()")
            rapport(pr["state"] == "refused" and pr["closeCode"] == 4003, "état refused, code 4003", pr)
            await asyncio.sleep(3)
            n = sum("| refus " in x for x in open(tmp / "page" / "presence.log", encoding="utf-8"))
            rapport(n == 1, "pas de nouvelle tentative après un refus", n)
            await o.ctx.close()
            print("--- 5. page : salon du créateur")
            o = await Onglet(br).ouvrir(org + "/index.html?region=Bon#name=Zoe")
            await o.attendre("window.__viewer.getPresence().state === 'online'", 20)
            rapport(True, "connexion acceptée (alice.t51)")
            await o.ctx.close()
            print("--- 6. page : origine non déclarée (localhost au lieu de 127.0.0.1), anglais")
            o = await Onglet(br).ouvrir(f"http://localhost:{hport}/index.html?region=Bon#lang=en", locale="en-US")
            await o.attendre("document.getElementById('presenceStatus').textContent.includes('refused')", 20)
            s = await o.txt("presenceStatus")
            rapport(s == "presence refused: this page is not declared on this presence server (reload the page once fixed)", "texte anglais (origine)", s)
            await o.ctx.close()
            print("--- 7. viewer (origine « null » non déclarée)")
            o = await Onglet(br).ouvrir((DIST / "glb-viewer.html").as_uri(), init=None, viewer=False)
            await o.attendre("!!document.getElementById('presInfo')", 20)
            await o.ev(f"""(() => {{ const i = [...document.querySelectorAll('input[type=text]')].find(x => x.placeholder === 'ws://127.0.0.1:8765'); i.value = 'ws://127.0.0.1:{port}'; i.onchange(); }})()""")
            await o.attendre("document.getElementById('presInfo').textContent.includes('refusée')", 20)
            s = await o.txt("presInfo")
            rapport(s == "présence : refusée : cette page n'est pas déclarée sur ce serveur de présence", "viewer : refus affiché", s)
            await o.ctx.close()
            await br.close()
    finally:
        http.kill()
        proc.kill()


asyncio.run(partie_serveur())
if "--serveur" not in sys.argv:
    asyncio.run(partie_page())
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
