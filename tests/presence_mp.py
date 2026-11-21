#!/usr/bin/env python3
"""Tests 1.12.29 : messages prives entre promeneurs, cote serveur (vrai presence_server.py).

Message {t:'dm', to:id, text} -> le destinataire recoit {t:'dm', id, name, k, text, ts} ; l'expediteur recoit le meme message avec self:true
(id, nom et cle du destinataire). Erreurs : {t:'dmerr', to, why} avec why = off, rate, gone ou self. Jamais diffuse a la salle, jamais dans
l'historique, jamais ecrit dans la console (seulement l'evenement). Option --no-dm ; le message « welcome » porte dm (vrai sauf --no-dm).
Verifie :
1.  A ecrit a B : B recoit id, nom, cle (12 hexadecimaux), texte nettoye (controles et espaces doubles), heure ; A recoit l'echo self:true ;
2.  un tiers de la meme salle ne recoit rien (ni dm ni chat) ; la reponse de B a A porte la meme cle de B que l'echo de A ;
3.  to inconnu, to = soi-meme, to = spectateur, to dans un autre salon : dmerr gone / self / gone / gone, et rien chez l'autre salon ;
4.  to invalide (booleen, texte, absent) et texte vide : ignores sans reponse ; un spectateur ne peut pas ecrire ;
5.  la cle d'un visiteur reste la meme apres reconnexion avec le meme uid, et differe d'un visiteur a l'autre ;
6.  l'historique du salon ne contient pas le MP ;
7.  cadence : deux MP a moins de --chat-gap : le second est refuse (dmerr rate), un autre apres le delai passe ;
8.  --no-dm : welcome dm faux, tout MP repond dmerr off et rien n'arrive ; serveur par defaut : welcome dm vrai ;
9.  la console ne contient pas le texte du MP, et montre l'evenement (expediteur -> destinataire).
Sur le main d'origine (1.12.28) : echec des le premier test (le message « dm » est ignore).

Prerequis : pip install websockets ; python build.py avant. Lancer : python tests/presence_mp.py
"""
import asyncio, json, os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import websockets

SALON = "mp"


def connect(port):
    return websockets.connect(f"ws://127.0.0.1:{port}")


async def recv_t(ws, t, delai=1.0):
    """attend un message de type t ; None si rien dans le delai"""
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
    ws = await connect(port).__aenter__()
    await ws.send(json.dumps({"t": "hello", "room": salon, "name": nom, "uid": uid * 20, "spectator": spectateur}))
    w = await recv_t(ws, "welcome")
    return ws, w


async def dm(ws, to, text):
    await ws.send(json.dumps({"t": "dm", "to": to, "text": text}))


async def fonctions(port):
    res = []
    a, wa = await entrer(port, "Alice", "a")
    b, wb = await entrer(port, "Bob", "b")
    d, wd = await entrer(port, "Dave", "d")          # tiers, meme salon
    s, ws_ = await entrer(port, "Spec", "s", spectateur=True)
    c, wc = await entrer(port, "Carol", "c", salon="autre")
    ia, ib, id_, is_, ic = wa["id"], wb["id"], wd["id"], ws_["id"], wc["id"]
    res.append((bool(wa.get("dm") is True), "welcome porte dm vrai", wa.get("dm")))
    # 1 et 2
    await dm(a, ib, "Salut\x01  Bob")
    mb = await recv_t(b, "dm")
    ea = await recv_t(a, "dm")
    res.append((bool(mb and mb["id"] == ia and mb["name"].startswith("Alice") and mb["text"] == "Salut Bob" and isinstance(mb["ts"], int)
                     and re.fullmatch(r"[0-9a-f]{12}", mb["k"] or "") and not mb.get("self")), "B recoit id, nom, cle, texte nettoye, heure", mb))
    res.append((bool(ea and ea["self"] is True and ea["id"] == ib and ea["name"].startswith("Bob") and ea["text"] == "Salut Bob"
                     and ea["ts"] == (mb or {}).get("ts") and re.fullmatch(r"[0-9a-f]{12}", ea["k"] or "")), "A recoit l'echo self:true avec le destinataire", ea))
    k_alice, k_bob = (mb or {}).get("k"), (ea or {}).get("k")      # mb : message de A vu par B (cle de A) ; ea : echo de A (cle de B)
    tiers = await recv_t(d, "dm", 0.6), await recv_t(d, "chat", 0.3), await recv_t(s, "dm", 0.3), await recv_t(c, "dm", 0.3)
    res.append((tiers == (None, None, None, None), "ni le tiers, ni le spectateur, ni l'autre salon ne recoivent rien", tiers))
    await dm(b, ia, "Reponse")
    ra = await recv_t(a, "dm")
    eb = await recv_t(b, "dm")
    res.append((bool(ra and ra["id"] == ib and eb and eb["self"] and ra["k"] == k_bob and eb["k"] == k_alice),
                "la reponse de B porte la cle de B vue dans l'echo ; l'echo de B porte la cle de A", (ra, eb)))
    # 3
    for to, why, nom in ((999999, "gone", "to inconnu"), (ia, "self", "to = soi-meme"), (is_, "gone", "to = spectateur"), (ic, "gone", "to dans un autre salon")):
        await dm(a, to, "x")
        e = await recv_t(a, "dmerr")
        res.append((bool(e and e["why"] == why and e["to"] == to), f"dmerr {why} : {nom}", e))
    res.append((await recv_t(c, "dm", 0.4) is None and await recv_t(s, "dm", 0.2) is None, "rien chez l'autre salon ni chez le spectateur", ""))
    # 4
    for to, texte, nom in ((True, "x", "to booleen"), ("5", "x", "to texte"), (None, "x", "to absent"), (ib, "   ", "texte vide"), (ib, "\x01\x02", "texte de controles")):
        await a.send(json.dumps({"t": "dm", "to": to, "text": texte}) if to is not None else json.dumps({"t": "dm", "text": texte}))
        e, m = await recv_t(a, "dmerr", 0.4), await recv_t(b, "dm", 0.2)
        res.append((e is None and m is None, f"ignore sans reponse : {nom}", (e, m)))
    await dm(s, ib, "je suis spectateur")
    res.append((await recv_t(b, "dm", 0.5) is None and await recv_t(s, "dmerr", 0.2) is None, "un spectateur ne peut pas ecrire", ""))
    # 5
    await b.close()
    b2, wb2 = await entrer(port, "Bob", "b")
    await dm(a, wb2["id"], "retour")
    e2 = await recv_t(a, "dm")
    d2 = await recv_t(a, "dm", 0.2)
    await dm(a, id_, "pour Dave")
    ed = await recv_t(a, "dm")
    res.append((bool(wb2["id"] != ib and e2 and e2["k"] == k_bob), "meme uid apres reconnexion : meme cle, autre id", (e2 and e2["k"], k_bob)))
    res.append((bool(ed and ed["k"] != k_bob and ed["k"] != k_alice and k_alice != k_bob), "visiteurs differents : cles differentes", (ed and ed["k"], k_alice, k_bob)))
    # 6
    e, we = await entrer(port, "Eve", "e")
    hist = json.dumps(we.get("history"))
    res.append(("Salut" not in hist and "Reponse" not in hist and "retour" not in hist, "l'historique du salon ne contient aucun MP", hist[:100]))
    for w in (a, b2, d, s, c, e):
        await w.close()
    return res


async def cadence(port):
    a, wa = await entrer(port, "Alice", "a")
    b, wb = await entrer(port, "Bob", "b")
    await dm(a, wb["id"], "un")
    m1 = await recv_t(b, "dm")
    await dm(a, wb["id"], "deux")
    e = await recv_t(a, "dmerr")
    m2 = await recv_t(b, "dm", 0.4)
    await asyncio.sleep(0.9)
    await dm(a, wb["id"], "trois")
    m3 = await recv_t(b, "dm")
    r = [(bool(m1 and e and e["why"] == "rate" and m2 is None and m3 and m3["text"] == "trois"), "cadence : le second MP a moins de --chat-gap est refuse, le suivant passe", (m1, e, m2, m3))]
    await a.close()
    await b.close()
    return r


async def sans_dm(port):
    a, wa = await entrer(port, "Alice", "a")
    b, wb = await entrer(port, "Bob", "b")
    await dm(a, wb["id"], "x")
    e = await recv_t(a, "dmerr")
    m = await recv_t(b, "dm", 0.4)
    await a.close()
    await b.close()
    return [(bool(wa.get("dm") is False and e and e["why"] == "off" and m is None), "--no-dm : welcome dm faux, dmerr off, rien n'arrive", (wa.get("dm"), e, m))]


async def secret(port):
    a, wa = await entrer(port, "Alice", "a")
    b, wb = await entrer(port, "Bob", "b")
    await dm(a, wb["id"], "motdepasse42")
    await recv_t(b, "dm")
    await asyncio.sleep(0.3)
    await a.close()
    await b.close()


def verifier(res):
    for ok, nom, det in res:
        rapport(ok, nom, "" if ok else det)


proc, port = lancer_presence("--lang", "fr", "--chat-gap", "0.05", "--chat-burst", "100", "--max-per-ip", "50")
try:
    verifier(asyncio.run(fonctions(port)))
finally:
    proc.kill()
    proc.communicate()

proc, port = lancer_presence("--lang", "fr", "--max-per-ip", "50")
try:
    verifier(asyncio.run(cadence(port)))
finally:
    proc.kill()
    proc.communicate()

proc, port = lancer_presence("--lang", "fr", "--no-dm", "--max-per-ip", "50")
try:
    verifier(asyncio.run(sans_dm(port)))
finally:
    proc.kill()
    proc.communicate()

port = port_libre()
proc = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--lang", "fr", "--host", "127.0.0.1", "--port", str(port), "--identities", "",
                         "--max-per-ip", "50"], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=tmp,
                        env=dict(os.environ, PYTHONIOENCODING="utf-8"))
attendre_port(port, proc, "presence_server")
asyncio.run(secret(port))
time.sleep(0.3)
proc.kill()
out = proc.communicate()[0]
lignes = [l for l in out.splitlines() if "Alice" in l and "Bob" in l]
rapport("motdepasse42" not in out, "la console ne contient pas le texte du MP", "" if "motdepasse42" not in out else out[-300:])
rapport(bool(lignes) and "MP" in lignes[0] and "->" in lignes[0], "la console montre l'evenement (expediteur -> destinataire)", lignes[:2] or out[-300:])

sys.exit(1 if resultat() else 0)
