#!/usr/bin/env python3
"""Tests v48 : journal des visites.

Serveur (vrai presence_server.py) : une ligne JSON par visite (salon, arrivée, durée, promenade, empreinte), jamais d'IP,
pseudo seulement avec --visits-names ; reconnexion du même navigateur fusionnée ; clé créée par la commande de console
« visits-key », seule son empreinte est gardée ; clé saisie en minuscules ou avec des espaces acceptée ; mauvaise clé refusée,
5 refus par minute au plus ; « visits-key SALON off » ; purge des visites trop anciennes ; arrêt propre : visite en cours écrite.
Page : fenêtre « Journal des visites » ouverte par #visits, clé refusée, résumé, CSV, clé retenue puis oubliée, Échap,
page sans présence, serveur sans --visits, ancien serveur, serveur absent, anglais, page sans #visits.

Prérequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v48.py
"""
import asyncio, json, os, re, signal, subprocess, sys, threading, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37
import websockets


def serveur_visites(*extra, nom="srv"):
    """serveur de présence avec une console (stdin) : renvoie (processus, port, dossier)"""
    port = port_libre()
    d = tmp / nom
    d.mkdir(exist_ok=True)
    extra = [str(d / x) if x.endswith(".jsonl") else x for x in extra]      # chemins relatifs : relatifs au dossier du script (dist), d'où le chemin complet
    proc = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--host", "127.0.0.1", "--port", str(port), "--identities", str(d / "id.json"),
                             "--bans", str(d / "bans.json"), "--visits-keys", str(d / "keys.json"), *extra],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=d, bufsize=1)
    attendre_port(port, proc, "presence_server")
    proc.lu = []                     # sortie de la console, lue par un fil à part (lecture bloquante)
    threading.Thread(target=lambda: [proc.lu.append(x) for x in proc.stdout], daemon=True).start()
    return proc, port, d


def console(proc, ligne, motif, s=10):
    """tape une commande dans la console du serveur et attend une sortie qui contient le motif"""
    debut = len(proc.lu)
    proc.stdin.write(ligne + "\n")
    proc.stdin.flush()
    out = ""
    for _ in range(int(s / 0.1)):
        out = "".join(proc.lu[debut:])
        m = re.search(motif, out)
        if m:
            return m, out
        time.sleep(0.1)
    return None, out


async def visite(port, nom, spectateur, secs, uid, marcher_apres=None, salon="galerie"):
    async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
        await ws.send(json.dumps({"t": "hello", "room": salon, "name": nom, "uid": uid, "spectator": spectateur}))
        await ws.recv()
        if marcher_apres is not None:
            await asyncio.sleep(marcher_apres)
            await ws.send(json.dumps({"t": "role", "walker": True, "name": nom}))
        await asyncio.sleep(secs)


async def demander(port, cle, salon="galerie"):
    async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
        await ws.send(json.dumps({"t": "visits", "room": salon, "key": cle}))
        return json.loads(await ws.recv())


def lignes(path):
    return [json.loads(x) for x in open(path, encoding="utf-8").read().splitlines() if x.strip()]


async def partie_serveur():
    print("--- 1. serveur : écriture, fusion, clé, limite")
    proc, port, d = serveur_visites("--visits", "visites.jsonl", "--log-ip", "raw")
    vf = d / "visites.jsonl"
    try:
        m, out = console(proc, "visits-key galerie", r"([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})")
        rapport(m is not None, "console : visits-key affiche une clé", out[-300:])
        cle = m.group(1) if m else "AAAA-BBBB-CCCC"
        keys = (d / "keys.json").read_text(encoding="utf-8")
        rapport(cle not in keys and cle.replace("-", "") not in keys and '"galerie"' in keys, "fichier des clés : empreinte seulement", keys)
        await visite(port, "Bob", False, 1.5, "b" * 20)
        await visite(port, "Bob", False, 1.0, "b" * 20)                     # reconnexion : même visite
        await visite(port, "", True, 1.0, "a" * 20, marcher_apres=1.0)     # spectateur puis promeneur
        await visite(port, "", True, 1.0, "c" * 20)                         # spectateur seul
        await asyncio.sleep(0.5)
        L = lignes(vf)
        rapport(len(L) == 4, "4 connexions écrites", L)
        texte = vf.read_text(encoding="utf-8")
        rapport("127.0.0.1" not in texte and "Bob" not in texte and all("name" not in x for x in L), "jamais d'IP ; pas de pseudo sans --visits-names", texte)
        rapport(all(set(x) == {"room", "start", "dur", "walk", "v"} for x in L), "champs : room, start, dur, walk, v", L[:1])
        rapport(L[0]["v"] == L[1]["v"] and L[0]["v"] != L[2]["v"] and len(L[0]["v"]) == 10, "empreinte : même navigateur, même empreinte", L)
        rapport(L[2]["walk"] >= 1 and L[2]["walk"] < L[2]["dur"] + 1 and L[3]["walk"] == 0, "temps de promenade : spectateur puis promeneur, spectateur seul", L)
        r = await demander(port, cle.lower().replace("-", " "))
        rapport(r.get("ok") is True, "clé en minuscules et avec espaces : acceptée", r)
        rapport(r.get("visits") == 3 and r.get("visitors") == 3, "reconnexion fusionnée : 3 visites, 3 visiteurs distincts", r)
        jour = (r.get("days") or [{}])[0]
        rapport(jour.get("visits") == 3 and jour.get("walked") == 2 and re.match(r"^\d\d/\d\d/\d{4}$", jour.get("date", "")), "résumé par jour (date jj/mm/aaaa, avec promenade 2)", jour)
        rec = r.get("recent") or []
        rapport(len(rec) == 3 and re.match(r"^\d\d/\d\d/\d{4} \d\d:\d\d$", rec[0].get("start", "")) and "name" not in rec[0], "visites récentes : 3, sans pseudo", rec)
        rapport(r.get("keep") == 365 and r.get("names") is False, "conservation 365 jours par défaut, pseudos non", r)
        r = await demander(port, cle, salon="hobbit")
        rapport(r == {"t": "visits", "ok": False, "why": "key"}, "autre salon : clé refusée", r)
        for i in range(4):
            r = await demander(port, "FAUX")
        rapport(r.get("why") == "key", "mauvaise clé : refusée", r)
        r = await demander(port, cle)
        rapport(r.get("why") == "rate", "après 5 refus en une minute : trop d'essais, même avec la bonne clé", r)
        _, out = console(proc, "visits-key", r"galerie")
        rapport("galerie" in out and cle not in out, "visits-key seul : liste des salons sans la clé", out[-200:])
        m, out = console(proc, "visits-key Galerie", r"attention|warning")
        rapport(m is not None and "autre casse : galerie." in out, "visits-key Galerie : avertissement, salon connu « galerie » (la casse compte)", out[-300:])
        n0 = len(proc.lu)
        m, out = console(proc, "visits-key hobbit", r"([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})")
        time.sleep(0.5)
        apres = "".join(proc.lu[n0:])
        rapport(m is not None and "attention" not in apres, "salon neuf sans autre casse : pas d'avertissement", apres)
        m, out = console(proc, "visits-key galerie off", r"retir|removed")
        rapport(m is not None and "galerie" not in json.loads((d / "keys.json").read_text(encoding="utf-8"))["rooms"], "visits-key galerie off : clé retirée", out[-200:])
        # arrêt propre : la visite en cours est écrite
        ws = await websockets.connect(f"ws://127.0.0.1:{port}")
        await ws.send(json.dumps({"t": "hello", "room": "galerie", "name": "Zoe", "uid": "z" * 20, "spectator": False}))
        await ws.recv()
        await asyncio.sleep(1)
        proc.send_signal(signal.SIGINT)
        for _ in range(100):            # attente sans bloquer la boucle : le client doit répondre à la fermeture du serveur
            if proc.poll() is not None:
                break
            await asyncio.sleep(0.1)
        rapport(len(lignes(vf)) == 5, "arrêt propre (Ctrl+C) : la visite en cours est écrite", len(lignes(vf)))
    finally:
        if proc.poll() is None:
            proc.kill()

    print("--- 2. serveur : pseudos, purge, sans --visits")
    d2 = tmp / "srv2"
    d2.mkdir()
    vieux = int(time.time()) - 3 * 86400
    (d2 / "v.jsonl").write_text(json.dumps({"room": "galerie", "start": vieux, "dur": 60, "walk": 0, "v": "0123456789"}) + "\n"
                                + json.dumps({"room": "galerie", "start": int(time.time()) - 3600, "dur": 120, "walk": 30, "v": "9876543210"}) + "\n"
                                + "ligne abîmée\n", encoding="utf-8")
    proc, port, d = serveur_visites("--visits", "v.jsonl", "--visits-days", "1", "--visits-names", nom="srv2")
    try:
        L = lignes(d / "v.jsonl")
        rapport(len(L) == 1 and L[0]["v"] == "9876543210", "purge au démarrage : visite de plus d'un jour et ligne abîmée retirées", L)
        m, _ = console(proc, "visits-key galerie", r"([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})")
        await visite(port, "Ann", True, 0.8, "n" * 20, marcher_apres=0.5)
        await asyncio.sleep(0.5)
        L = lignes(d / "v.jsonl")
        rapport(L[-1].get("name") == "Ann", "--visits-names : pseudo du promeneur noté", L[-1])
        r = await demander(port, m.group(1))
        rapport(r.get("ok") and r.get("names") is True and any(x.get("name") == "Ann" for x in r.get("recent", [])) and r.get("keep") == 1, "résumé avec pseudos", r)
    finally:
        proc.kill()
    proc, port, d = serveur_visites(nom="srv3")
    try:
        m, out = console(proc, "visits-key galerie", r"([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})")
        rapport("--visits" in out, "sans --visits : la commande prévient que le journal est inactif", out[-250:])
        r = await demander(port, m.group(1) if m else "X")
        rapport(r.get("why") == "off", "sans --visits : réponse off", r)
    finally:
        proc.kill()


async def partie_page():
    print("--- 3. page : fabrication")
    proc, port, d = serveur_visites("--visits", "visites.jsonl", nom="srvp")
    m, _ = console(proc, "visits-key galerie", r"([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})")
    cle = m.group(1)
    await visite(port, "Bob", False, 1.0, "b" * 20)
    off, _, _ = serveur_visites(nom="srvoff")
    off_port = int(off.args[off.args.index("--port") + 1])
    mort = port_libre()
    ancien = port_libre()

    async def faux(ws):           # ancien serveur : tout message autre que hello ferme la connexion
        try:
            await asyncio.wait_for(ws.recv(), 5)
        except Exception:
            pass
    import websockets.asyncio.server
    fsrv = await websockets.asyncio.server.serve(faux, "127.0.0.1", ancien)
    site = tmp / "site"
    site.mkdir()
    sol_glb(site / "sol.glb")
    commun = ["--shared-shell", "--no-sea", "--target", "0,0,0"]
    html(site / "sol.glb", "-o", site / "Galerie.html", *commun, "--presence-url", f"ws://127.0.0.1:{port}", "--room", "galerie")
    html(site / "sol.glb", "-o", site / "Sans.html", *commun)
    html(site / "sol.glb", "-o", site / "Off.html", *commun, "--presence-url", f"ws://127.0.0.1:{off_port}", "--room", "galerie")
    html(site / "sol.glb", "-o", site / "Ancien.html", *commun, "--presence-url", f"ws://127.0.0.1:{ancien}", "--room", "galerie")
    html(site / "sol.glb", "-o", site / "Mort.html", *commun, "--presence-url", f"ws://127.0.0.1:{mort}", "--room", "galerie")
    http, hport = serveur(site)
    BASE = f"http://127.0.0.1:{hport}/index.html?region="
    from playwright.async_api import async_playwright
    try:
        async with async_playwright() as p:
            kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            if os.environ.get("CHROMIUM"):
                kw["executable_path"] = os.environ["CHROMIUM"]
            br = await p.chromium.launch(**kw)

            print("--- 4. page : français")
            ctx = await br.new_context(locale="fr-FR", viewport={"width": 1000, "height": 700}, accept_downloads=True)
            o = await Onglet(br).ouvrir(BASE + "Galerie#visits", ctx=ctx)
            rapport(await o.ev("!document.getElementById('visitsOverlay').hidden"), "#visits : fenêtre ouverte")
            rapport("Journal des visites" in await o.txt("visitsTitle"), "titre en français", await o.txt("visitsTitle"))
            await o.ev("document.getElementById('visitsGo').click()")
            rapport("Entre la clé" in await o.txt("visitsStatus"), "clé vide : message", await o.txt("visitsStatus"))
            await o.ev("document.getElementById('visitsKey').value = 'FAUX'; document.getElementById('visitsGo').click()")
            await o.attendre("document.getElementById('visitsStatus').textContent.includes('refusée')", 15)
            rapport(await o.ev("localStorage.getItem('glb2html_visits_galerie')") is None, "clé refusée : rien de retenu")
            await o.pg.fill("#visitsKey", cle.lower())
            await o.pg.press("#visitsKey", "Enter")
            await o.attendre("document.querySelectorAll('#visitsOut table').length === 2", 15)
            st = await o.txt("visitsStatus")
            rapport("Salon « galerie »" in st and "visites 1" in st and "365 jours" in st, "résumé : salon, nombre de visites, conservation", st)
            t = await o.txt("visitsOut")
            rapport("Par jour" in t and "Visites des 30 derniers jours" in t and "Avec promenade" in t and "oui" in t and "Pseudo" not in t, "tableaux en français, sans colonne Pseudo", t[:400])
            rapport(await o.ev("localStorage.getItem('glb2html_visits_galerie')") == cle.lower(), "clé acceptée : retenue par le navigateur")
            async with o.pg.expect_download() as dl:
                await o.ev("document.getElementById('visitsCsv').click()")
            f = await (await dl.value).path()
            nom = (await dl.value).suggested_filename
            csv = open(f, encoding="utf-8").read()
            rapport(re.match(r"^visites_galerie_\d{8}\.csv$", nom) is not None, "CSV : nom du fichier", nom)
            rapport(csv.startswith("\ufeff\"Par jour\"") and '"Date";"Visites";"Visiteurs distincts";"Durée totale (s)"' in csv and '"oui"' in csv, "CSV : BOM, séparateur ;, durées en secondes", csv[:300])
            await o.pg.reload()
            await o.pg.wait_for_function("document.querySelectorAll('#visitsOut table').length === 2", timeout=40000)
            rapport(True, "rechargement : résumé affiché sans ressaisir la clé")
            await o.ev("document.getElementById('visitsForget').click()")
            rapport(await o.ev("localStorage.getItem('glb2html_visits_galerie') === null && document.getElementById('visitsOut').textContent === '' && document.getElementById('visitsCsv').hidden"), "Oublier la clé : effacée, tableau vidé")
            await o.pg.keyboard.press("Escape")
            rapport(await o.ev("document.getElementById('visitsOverlay').hidden"), "Échap ferme la fenêtre")
            rapport(not o.errs, "aucune erreur de page", o.errs)
            await ctx.close()

            for region, attendu, nom_cas in (("Sans", "pas de serveur de présence", "page sans présence"), ("Off", "n'enregistre pas les visites", "serveur sans --visits"),
                                             ("Ancien", "trop ancien", "ancien serveur"), ("Mort", "ne répond pas", "serveur absent")):
                o = await Onglet(br).ouvrir(BASE + region + "#visits")
                if region != "Sans":
                    await o.pg.fill("#visitsKey", "ABCD")
                    await o.pg.press("#visitsKey", "Enter")
                    await o.attendre(f"document.getElementById('visitsStatus').textContent.includes({json.dumps(attendu)})", 20)
                s = await o.txt("visitsStatus")
                rapport(attendu in s and (region != "Sans" or await o.ev("document.getElementById('visitsForm').hidden")), nom_cas, s)
                await o.ctx.close()

            o = await Onglet(br).ouvrir(BASE + "Galerie")
            rapport(await o.ev("document.getElementById('visitsOverlay').hidden"), "sans #visits : fenêtre cachée")
            await o.ctx.close()

            print("--- 5. page : anglais")
            ctx = await br.new_context(locale="en-US", viewport={"width": 1000, "height": 700}, accept_downloads=True)
            o = await Onglet(br).ouvrir(BASE + "Galerie#visits&lang=en", ctx=ctx, locale="en-US")
            await o.pg.fill("#visitsKey", cle)
            await o.pg.press("#visitsKey", "Enter")
            await o.attendre("document.querySelectorAll('#visitsOut table').length === 2", 15)
            st, t = await o.txt("visitsStatus"), await o.txt("visitsOut")
            rapport('Room "galerie"' in st and "Per day" in t and "Distinct visitors" in t and "yes" in t, "textes anglais", st + " / " + t[:200])
            async with o.pg.expect_download() as dl:
                await o.ev("document.getElementById('visitsCsv').click()")
            csv = open(await (await dl.value).path(), encoding="utf-8").read()
            rapport((await dl.value).suggested_filename.startswith("visits_galerie_") and '"Date","Visits","Distinct visitors"' in csv, "CSV anglais : nom et séparateur ,", csv[:200])
            await ctx.close()
            await br.close()
    finally:
        http.kill()
        proc.kill()
        off.kill()
        fsrv.close()


async def main():
    await partie_serveur()
    await partie_page()


asyncio.run(main())
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
