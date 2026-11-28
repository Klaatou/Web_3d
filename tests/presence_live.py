#!/usr/bin/env python3
"""Tests 1.13.21 : micros coupes pendant un DJ en direct (zone radio) et commandes de console orateur / muet (vrai presence_server.py, faux Icecast).

Le faux Icecast sert /status-json.xsl : aucune source, la source de base (/autodj) seule, ou la source de base et le montage direct (/live), en objet seul
ou en liste, ou une erreur 500. Le fichier --live donne l'adresse du flux direct. La page envoie {t:'live', urls:[...]} (flux de la zone radio ou se trouve
le visiteur, a portee, qu'il ecoute ou non) et recoit {t:'live', on:true|false} quand son etat change.
Verifie :
1.  un visiteur dans la zone d'un flux direct quand le DJ est deja la : recoit on:true tout de suite ; un visiteur qui n'est dans aucune zone, un flux
    absent du fichier --live, un spectateur et un autre message : rien ; un arrivant dans la zone recoit on:true ; rien tant que le DJ n'est pas la (pas de on:false inutile) ;
2.  le DJ part : tous ceux de la zone recoivent on:false (au plus --live-every secondes plus tard) et personne d'autre ; il revient : on:true ;
3.  un visiteur qui sort de la zone (urls vide) recoit on:false tout de suite, l'autre garde on:true ; deux messages a moins d'une seconde : le second est ignore ;
4.  statut en liste ou en objet seul : lu pareil ; statut illisible une fois : l'etat est garde ; deux fois de suite : micros rendus ; le serveur survit au depart d'un visiteur en zone ;
5.  console : orateurs liste les salons (orateur, micros du public, micros coupes par un DJ) ; orateur N donne la parole (le salon la recoit) ; muet SALON on
    sans orateur est refuse, avec un orateur coupe les micros (mute vrai dans le message), off les rend ; orateur off SALON retire l'orateur ; un spectateur ne
    peut pas etre orateur ; salon inconnu ou casse differente ; aide et ligne de moderation citent les nouvelles commandes.
Prerequis : pip install websockets ; python build.py avant. Lancer : python tests/presence_live.py
"""
import asyncio, http.server, json, os, subprocess, sys, threading, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import websockets

SALON = "dj"
ETAT = {"mode": "off"}      # off : aucune source ; base : /autodj seul ; direct : /autodj et /live (liste) ; seul : /live seul en objet ; erreur : 500


class Faux(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        m = ETAT["mode"]
        if self.path != "/status-json.xsl" or m == "erreur":
            self.send_response(500)
            self.end_headers()
            return
        base = {"listenurl": "http://interne:8000/autodj", "server_name": "base"}
        live = {"listenurl": "http://interne:8000/live", "server_name": "dj"}
        src = {"off": None, "base": base, "direct": [base, live], "seul": live}[m]
        ice = {"admin": "x"}
        if src is not None:
            ice["source"] = src
        corps = json.dumps({"icestats": ice}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)


def faux_icecast():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Faux)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


async def recv_t(ws, t, delai=1.0):
    fin = time.monotonic() + delai
    while True:
        reste = fin - time.monotonic()
        if reste <= 0:
            return None
        try:
            m = json.loads(await asyncio.wait_for(ws.recv(), reste))
        except asyncio.TimeoutError:
            return None
        if m.get("t") == t:
            return m


async def entrer(port, nom, uid, salon=SALON, spectateur=False):
    ws = await websockets.connect(f"ws://127.0.0.1:{port}")
    await ws.send(json.dumps({"t": "hello", "room": salon, "name": nom, "uid": uid * 20, "spectator": spectateur}))
    w = await recv_t(ws, "welcome")
    return ws, w


async def envoyer(ws, **m):
    await ws.send(json.dumps(m))


def lancer(*extra):
    port = port_libre()
    proc = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--lang", "fr", "--host", "127.0.0.1", "--port", str(port), "--identities", "",
                             "--max-per-ip", "50", "--chat-gap", "0.05", *extra],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", cwd=tmp, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    vider(proc)
    attendre_port(port, proc, "presence_server")
    return proc, port


def commande(proc, ligne):
    proc.stdin.write(ligne + "\n")
    proc.stdin.flush()


async def sortie_apres(proc, ligne, attente=0.5):
    """lance la commande et rend ce que la console a ecrit en reponse"""
    avant = len("".join(proc.stdout.morceaux)) if hasattr(proc.stdout, "morceaux") else 0
    commande(proc, ligne)
    await asyncio.sleep(attente)
    return "".join(proc.stdout.morceaux)[avant:]


async def essai(port, proc, icecast):
    res = []
    URL = f"http://127.0.0.1:{icecast}/live"
    AUTRE = f"http://127.0.0.1:{icecast}/pas-dans-le-fichier"
    a, wa = await entrer(port, "Alice", "a")
    b, wb = await entrer(port, "Bob", "b")
    d, wd = await entrer(port, "Dave", "d")          # dans le salon, pas dans la zone
    s, ws_ = await entrer(port, "Spec", "s", spectateur=True)
    ia, ib, idd, isp = wa["id"], wb["id"], wd["id"], ws_["id"]

    # 1 -- rien tant que le DJ n'est pas la
    ETAT["mode"] = "base"
    await envoyer(a, t="live", urls=[URL])
    r = await recv_t(a, "live", 1.5)
    res.append((r is None, "DJ absent (seule la source de base) : pas de message on:false inutile", r))
    ETAT["mode"] = "direct"
    r = await recv_t(a, "live", 7)
    res.append((r == {"t": "live", "on": True}, "le DJ arrive : on:true chez A (liste de sources)", r))
    await envoyer(b, t="live", urls=[URL])
    r = await recv_t(b, "live", 3)
    res.append((r == {"t": "live", "on": True}, "B entre dans la zone pendant le direct : on:true tout de suite", r))
    await envoyer(d, t="live", urls=[])
    await envoyer(s, t="live", urls=[URL])
    await asyncio.sleep(1.2)
    await envoyer(d, t="live", urls=[AUTRE])
    r = [await recv_t(d, "live", 1.5), await recv_t(s, "live", 0.3)]
    res.append((r == [None, None], "D hors zone, flux absent du fichier, spectateur : aucun message", r))
    await asyncio.sleep(1.2)
    await envoyer(d, t="live", urls="pas une liste")
    await asyncio.sleep(1.2)
    await envoyer(d, t="live")
    r = await recv_t(d, "live", 0.5)
    res.append((r is None, "urls invalide ou absent : ignore", r))

    # 2 -- le DJ part, puis revient
    ETAT["mode"] = "off"
    ra, rb, rd = await recv_t(a, "live", 8), await recv_t(b, "live", 1), await recv_t(d, "live", 0.3)
    res.append(((ra, rb, rd) == ({"t": "live", "on": False}, {"t": "live", "on": False}, None), "le DJ part : on:false chez A et B, rien chez D", (ra, rb, rd)))
    ETAT["mode"] = "seul"
    ra, rb = await recv_t(a, "live", 8), await recv_t(b, "live", 1)
    res.append(((ra, rb) == ({"t": "live", "on": True}, {"t": "live", "on": True}), "le DJ revient (montage direct seul, en objet) : on:true chez A et B", (ra, rb)))

    # 3 -- sortie de la zone ; cadence
    await envoyer(a, t="live", urls=[])
    ra, rb = await recv_t(a, "live", 2), await recv_t(b, "live", 0.5)
    res.append(((ra, rb) == ({"t": "live", "on": False}, None), "A sort de la zone : on:false tout de suite, B garde son micro coupe", (ra, rb)))
    await asyncio.sleep(1.2)
    await envoyer(a, t="live", urls=[URL])
    await envoyer(a, t="live", urls=[])
    r = await recv_t(a, "live", 1.5)
    res.append((r == {"t": "live", "on": True}, "deux messages a moins d'une seconde : le premier compte, le second est ignore", r))
    await asyncio.sleep(1.2)
    await envoyer(a, t="live", urls=[])
    await recv_t(a, "live", 1.5)

    # 4 -- statut illisible
    ETAT["mode"] = "erreur"
    r = await recv_t(b, "live", 6.5)
    res.append((r is None, "statut illisible une fois : l'etat est garde", r))
    r = await recv_t(b, "live", 7)
    res.append((r == {"t": "live", "on": False}, "statut illisible deux fois de suite : micros rendus", r))
    ETAT["mode"] = "direct"
    r = await recv_t(b, "live", 8)
    res.append((r == {"t": "live", "on": True}, "le statut revient : on:true", r))
    await b.close()
    await asyncio.sleep(0.3)
    e, we = await entrer(port, "Eve", "e")
    res.append((we is not None, "le serveur survit au depart d'un visiteur en zone", we))
    await e.close()

    # 5 -- console
    out = await sortie_apres(proc, "orateurs")
    res.append((SALON in out and "orateur : (personne)" in out and "libres" in out and "coupés par un DJ : 0" in out, "orateurs : le salon, personne, micros libres, 0 coupe", out))
    await envoyer(a, t="live", urls=[URL])
    await recv_t(a, "live", 3)
    out = await sortie_apres(proc, "orateurs")
    res.append(("coupés par un DJ : 1" in out, "orateurs : un visiteur coupe par un DJ", out))
    out = await sortie_apres(proc, "muet dj on")
    res.append(("pas d'orateur" in out, "muet on sans orateur : refuse", out))
    r = await recv_t(d, "speaker", 0.3)
    res.append((r is None, "muet refuse : rien de diffuse", r))
    out = await sortie_apres(proc, f"orateur {idd}")
    r = [await recv_t(x, "speaker") for x in (a, d, s)]
    res.append((r == [{"t": "speaker", "id": idd}] * 3 and "parole donnée à Dave" in out, f"orateur {idd} : le salon (spectateur compris) recoit l'orateur", (r, out)))
    out = await sortie_apres(proc, "muet DJ on")
    r = [await recv_t(x, "speaker") for x in (a, d, s)]
    res.append((r == [{"t": "speaker", "id": idd, "mute": True}] * 3 and "micros du public coupés" in out, "muet DJ on (casse differente) : mute vrai pour tout le salon", (r, out)))
    out = await sortie_apres(proc, "orateurs")
    res.append(("Dave" in out and "coupés " in out, "orateurs : Dave orateur, micros du public coupes", out))
    out = await sortie_apres(proc, "muet dj off")
    r = [await recv_t(x, "speaker") for x in (a, d, s)]
    res.append((r == [{"t": "speaker", "id": idd}] * 3 and "rendus" in out, "muet off : mute absent, micros rendus", (r, out)))
    out = await sortie_apres(proc, f"orateur {isp}")
    r = await recv_t(a, "speaker", 0.3)
    res.append(("spectateur" in out and r is None, "un spectateur ne peut pas etre orateur", (out, r)))
    out = await sortie_apres(proc, "orateur Alice")
    r = await recv_t(d, "speaker")
    res.append((r == {"t": "speaker", "id": ia}, "orateur Alice (par le nom) : la parole passe a Alice", (r, out)))
    out = await sortie_apres(proc, "orateur off dj")
    r = await recv_t(d, "speaker")
    res.append((r == {"t": "speaker", "id": 0}, "orateur off dj : plus d'orateur", (r, out)))
    out = await sortie_apres(proc, "orateur off nulle-part")
    res.append(("aucun salon" in out, "salon inconnu : message", out))
    out = await sortie_apres(proc, "muet dj peut-etre")
    res.append(("usage : muet" in out, "muet sans on ou off : usage", out))
    out = await sortie_apres(proc, "orateur 99999")
    res.append(("personne ne correspond" in out, "orateur d'un numero inconnu : message", out))
    out = await sortie_apres(proc, "aide")
    res.append(("orateurs " in out and "orateur off <salon>" in out and "muet <salon> on|off" in out, "aide : les trois commandes", out[-600:]))
    for x in (a, d, s):
        await x.close()
    return res


def verifier(res):
    for ok, nom, detail in res:
        rapport(ok, nom, detail)


# 1. fichier --live : adresse par defaut du statut, objet avec adresse de statut, entrees invalides ignorees
srv, port_ice = faux_icecast()
fichier = tmp / "live.json"
fichier.write_text(json.dumps([f"http://127.0.0.1:{port_ice}/live", "pas une adresse", 42, {"url": "ftp://x/live"}]), encoding="utf-8")
proc, port = lancer("--live", str(fichier), "--live-every", "5")
try:
    verifier(asyncio.run(essai(port, proc, port_ice)))
finally:
    time.sleep(0.3)
    proc.kill()
    out = proc.stdout.texte() if hasattr(proc.stdout, "texte") else ""
rapport("direct" in out and "DJ en direct" in out, "la console du serveur montre le debut et la fin du direct", out[-400:])
rapport("serveur : 1 flux direct" in out, "au demarrage, la console dit combien de flux direct", out[:600])

# 2. sans --live : la page n'est jamais coupee
proc, port = lancer()
try:
    async def sans():
        a, wa = await entrer(port, "Alice", "a")
        await envoyer(a, t="live", urls=[f"http://127.0.0.1:{port_ice}/live"])
        r = await recv_t(a, "live", 1.5)
        await a.close()
        return [(r is None, "sans --live : aucun message", r)]
    verifier(asyncio.run(sans()))
finally:
    proc.kill()

# 3. adresse de statut donnee dans le fichier (autre que ORIGINE/status-json.xsl)
ETAT["mode"] = "direct"
fichier.write_text(json.dumps([{"url": "http://127.0.0.1:9/live", "status": f"http://127.0.0.1:{port_ice}/status-json.xsl"}]), encoding="utf-8")
proc, port = lancer("--live", str(fichier), "--live-every", "5")
try:
    async def statut():
        a, wa = await entrer(port, "Alice", "a")
        await envoyer(a, t="live", urls=["http://127.0.0.1:9/live"])
        r = await recv_t(a, "live", 4)
        await a.close()
        return [(r == {"t": "live", "on": True}, "objet {url, status} : le statut est lu a l'adresse donnee", r)]
    verifier(asyncio.run(statut()))
finally:
    proc.kill()

# 4. fichier --live absent ou illisible : le serveur demarre quand meme
proc, port = lancer("--live", str(tmp / "absent.json"))
try:
    out_ok = proc.poll() is None
finally:
    proc.kill()
rapport(out_ok, "fichier --live absent : le serveur demarre", "")
srv.shutdown()
sys.exit(1 if resultat() else 0)
