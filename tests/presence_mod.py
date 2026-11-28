#!/usr/bin/env python3
"""Tests 1.13.24 : moderation depuis la page, partie serveur (vrai presence_server.py).

Message {t:'mod', key, act, ...} avec la cle du salon (celle du journal des visites et du mode orateur) :
  act 'list' -> {t:'mod', ok, peers:[{id, name, spectator}], bans:[{at, name, until, reason}]} ; act 'kick' / 'ban' avec to:id (ban : minutes, 0 = definitif, defaut 60 ; reason) ;
  act 'unban' avec at. Erreurs {t:'moderr', why} : off (--no-mod), key, rate, gone, self. Reste dans le salon de l'appelant ; un ban pose ainsi ne vaut que pour ce salon.
Verifie :
1.  list : les autres visiteurs du salon (spectateur compris, marque), ni soi-meme, ni l'autre salon ; bans vide ;
2.  mauvaise cle : moderr key ; sans cle ou act inconnu : rien ; un spectateur (createur en vue globale) avec la bonne cle peut lister ;
3.  kick : la cible recoit kicked et la connexion se ferme ; le demandeur recoit la liste sans elle ; soi-meme : self ; inconnu et visiteur d'un autre salon : gone ;
4.  ban (30 min, motif) : la cible recoit banned avec le motif ; la liste porte le ban ; son retour dans CE salon est refuse (cle de visiteur) ; dans un AUTRE salon il est accepte
    (meme adresse, meme cle) ; le fichier --bans porte room ;
5.  unban : le ban disparait, le visiteur peut revenir ; at inconnu : gone ; un ban d'un autre salon ne peut pas etre leve d'ici ;
6.  minutes 0 : definitif (until 0) ; minutes invalides : 60 par defaut ;
7.  cadence : deux demandes en moins de 0,3 s : la seconde repond rate ; 5 cles refusees par minute et par adresse : la sixieme repond rate meme avec la bonne cle ;
8.  --no-mod : off ;
9.  la console n'ecrit aucune cle et montre les evenements (ban, ejection) avec « depuis la page ».
Prerequis : pip install websockets ; python build.py avant. Lancer : python tests/presence_mod.py
"""
import asyncio, hashlib, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import websockets

SALON, AUTRE = "mod", "ailleurs"
CLE, MAUVAISE, SEL = "ABCD-EFGH-JKMN", "AAAA-AAAA-AAAA", "sel-de-test"


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
        except websockets.ConnectionClosed:
            return None
        if m.get("t") == t:
            return m


async def entrer(port, nom, uid, salon=SALON, spectateur=False):
    ws = await websockets.connect(f"ws://127.0.0.1:{port}")
    await ws.send(json.dumps({"t": "hello", "room": salon, "name": nom, "uid": uid * 20, "spectator": spectateur}))
    msg = None
    fin = time.monotonic() + 2
    while time.monotonic() < fin:
        try:
            m = json.loads(await asyncio.wait_for(ws.recv(), 2))
        except Exception:
            break
        if m.get("t") in ("welcome", "banned", "full", "refused"):
            msg = m
            break
    return ws, msg


async def mod(ws, act, cle=CLE, attente=0.35, **kw):
    """envoie une demande de moderation (apres la cadence propre) et rend la reponse mod ou moderr"""
    await asyncio.sleep(attente)
    await ws.send(json.dumps(dict(t="mod", key=cle, act=act, **kw)))
    fin = time.monotonic() + 1.0
    while time.monotonic() < fin:
        try:
            m = json.loads(await asyncio.wait_for(ws.recv(), max(0.05, fin - time.monotonic())))
        except Exception:
            return None
        if m.get("t") in ("mod", "moderr"):
            return m
    return None


def fichier_cles():
    h = hashlib.sha256((SEL + CLE.replace("-", "")).encode()).hexdigest()
    p = tmp / "cles_mod.json"
    p.write_text(json.dumps({"rooms": {SALON: {"salt": SEL, "hash": h, "added": 0}, AUTRE: {"salt": SEL, "hash": h, "added": 0}}}), encoding="utf-8")
    return str(p)


def verifier(res):
    for ok, nom, det in res:
        rapport(ok, nom, "" if ok else det)


RES = []


async def essai_principal(port):
    res = RES; del res[:]
    cre, wc = await entrer(port, "Crea", "c")
    bob, wb = await entrer(port, "Bob", "b")
    spec, ws_ = await entrer(port, "", "s", spectateur=True)
    cat, wk = await entrer(port, "Cat", "k", salon=AUTRE)
    ic, ib, is_, ik = wc["id"], wb["id"], ws_["id"], wk["id"]
    r = await mod(cre, "list")
    ids = {p["id"]: p for p in (r or {}).get("peers", [])}
    res.append((bool(r) and r.get("t") == "mod" and r.get("ok") is True and set(ids) == {ib, is_} and ids[is_]["spectator"] is True and ids[ib]["name"] == "Bob" and r["bans"] == [],
                "list : les autres visiteurs du salon (spectateur marque), ni soi-meme ni l'autre salon", r))
    r = await mod(cre, "list", cle=MAUVAISE)
    res.append((r == {"t": "moderr", "why": "key"}, "mauvaise cle : moderr key", r))
    await asyncio.sleep(0.4); await cre.send(json.dumps({"t": "mod", "act": "list"}))
    await asyncio.sleep(0.4); await cre.send(json.dumps({"t": "mod", "key": CLE, "act": "autre"}))
    res.append((await recv_t(cre, "moderr", 0.5) is None and await recv_t(cre, "mod", 0.1) is None, "sans cle ou act inconnu : rien", ""))
    r = await mod(spec, "list")
    res.append((bool(r) and r.get("t") == "mod" and {p["id"] for p in r["peers"]} == {ic, ib}, "un spectateur avec la bonne cle peut lister", r))
    # kick
    r = await mod(cre, "kick", to=ic)
    res.append((r == {"t": "moderr", "why": "self"}, "kick de soi-meme : self", r))
    r = await mod(cre, "kick", to=9999)
    res.append((r == {"t": "moderr", "why": "gone"}, "kick d'un inconnu : gone", r))
    r = await mod(cre, "kick", to=ik)
    res.append((r == {"t": "moderr", "why": "gone"}, "kick d'un visiteur d'un autre salon : gone", r))
    r = await mod(cre, "kick", to=ib, reason="calme")
    k = await recv_t(bob, "kicked", 1.0)
    res.append((bool(r) and r.get("t") == "mod" and ib not in {p["id"] for p in r["peers"]} and k is not None and k.get("reason") == "calme", "kick : la cible recoit kicked avec le motif, la liste ne la montre plus", (r, k)))
    await bob.close()
    # ban
    dan, wd = await entrer(port, "Dan", "d")
    idd = wd["id"]
    r = await mod(cre, "ban", to=idd, minutes=30, reason="bruit")
    b = await recv_t(dan, "banned", 1.0)
    bans = (r or {}).get("bans", [])
    res.append((b is not None and b.get("reason") == "bruit" and len(bans) == 1 and bans[0]["name"] == "Dan" and bans[0]["reason"] == "bruit" and 1700 < bans[0]["until"] - time.time() < 1900,
                "ban : la cible recoit banned avec le motif, la liste porte le ban (30 min)", (r, b)))
    await dan.close()
    d2, m2 = await entrer(port, "Dan", "d")
    res.append((m2 is not None and m2.get("t") == "banned", "son retour dans CE salon est refuse", m2))
    d3, m3 = await entrer(port, "Dan", "d", salon=AUTRE)
    res.append((m3 is not None and m3.get("t") == "welcome", "dans un AUTRE salon (meme adresse, meme cle) il est accepte", m3))
    await d3.close()
    fb = json.loads((tmp / "bans_mod.json").read_text(encoding="utf-8"))
    res.append((len(fb) == 1 and fb[0].get("room") == SALON, "le fichier --bans porte room", fb))
    # un ban pose depuis l'autre salon n'est pas visible ici
    cat2, _ = await entrer(port, "Eve", "e", salon=AUTRE)
    r = await mod(cat, "list")
    res.append((bool(r) and r.get("bans") == [], "le salon voisin ne voit pas les bans de ce salon", r))
    # unban
    r = await mod(cre, "unban", at=12345.0)
    res.append((r == {"t": "moderr", "why": "gone"}, "unban d'un at inconnu : gone", r))
    at = bans[0]["at"] if bans else 0.0
    r = await mod(cat, "unban", at=at)
    res.append((r == {"t": "moderr", "why": "gone"}, "un ban d'un autre salon ne peut pas etre leve depuis le salon voisin", r))
    r = await mod(cre, "unban", at=at)
    res.append((bool(r) and r.get("t") == "mod" and r["bans"] == [], "unban : le ban disparait", r))
    d4, m4 = await entrer(port, "Dan", "d")
    res.append((m4 is not None and m4.get("t") == "welcome", "apres unban le visiteur peut revenir", m4))
    # minutes 0 / invalides
    r = await mod(cre, "ban", to=m4["id"], minutes=0)
    res.append((bool(r) and len(r["bans"]) == 1 and r["bans"][0]["until"] == 0, "minutes 0 : definitif (until 0)", r))
    at0 = r["bans"][0]["at"] if r else 0
    await mod(cre, "unban", at=at0)
    d5, m5 = await entrer(port, "Dan", "d")
    r = await mod(cre, "ban", to=m5["id"], minutes="beaucoup")
    res.append((bool(r) and len(r["bans"]) == 1 and 3500 < r["bans"][0]["until"] - time.time() < 3700, "minutes invalides : 60 par defaut", r))
    # cadence
    await asyncio.sleep(0.4)
    await cre.send(json.dumps({"t": "mod", "key": CLE, "act": "list"})); await cre.send(json.dumps({"t": "mod", "key": CLE, "act": "list"}))
    a = await recv_t(cre, "mod", 1.0); e = await recv_t(cre, "moderr", 1.0)
    res.append((a is not None and e == {"t": "moderr", "why": "rate"}, "deux demandes en moins de 0,3 s : la seconde repond rate", (a, e)))
    for x in (cre, spec, cat, cat2, d4, d5):
        try: await x.close()
        except Exception: pass
    return res


async def essai_cadence_cles(port):
    cre, _ = await entrer(port, "Crea", "c")
    r = []
    for _ in range(5):
        r.append((await mod(cre, "list", cle=MAUVAISE) or {}).get("why"))
    r.append((await mod(cre, "list") or {}).get("why"))
    await cre.close()
    return [(r == ["key"] * 5 + ["rate"], "5 cles refusees par minute et par adresse : la sixieme repond rate meme avec la bonne cle", r)]


async def essai_no_mod(port):
    cre, _ = await entrer(port, "Crea", "c")
    r = await mod(cre, "list")
    await cre.close()
    return [(r == {"t": "moderr", "why": "off"}, "--no-mod : off", r)]


def lancer(essai, *extra, sortie=False):
    proc, port = lancer_presence("--lang", "fr", "--max-per-ip", "50", "--chat-gap", "0.05", *extra)
    try:
        try:
            res = asyncio.run(essai(port))
        except BaseException:
            verifier(RES)
            raise
        verifier(res)
    finally:
        time.sleep(0.3)
        proc.kill()
        out = proc.communicate()[0]
    return out if sortie else None


cles = fichier_cles()
bans_f = str(tmp / "bans_mod.json")
out = lancer(essai_principal, "--visits-keys", cles, "--bans", bans_f, sortie=True)
fuite = [k for k in (CLE, CLE.replace("-", ""), MAUVAISE) if k.lower() in out.lower()]
rapport(not fuite, "la console ne contient aucune cle (ni bonne, ni refusee)", fuite)
rapport("depuis la page" in out and "bruit" in out and "calme" in out, "la console montre les evenements ban et ejection « depuis la page »", out[-400:])
lancer(essai_cadence_cles, "--visits-keys", cles, "--bans", str(tmp / "bans_mod2.json"))
lancer(essai_no_mod, "--no-mod", "--visits-keys", cles, "--bans", str(tmp / "bans_mod3.json"))
sys.exit(1 if resultat() else 0)
