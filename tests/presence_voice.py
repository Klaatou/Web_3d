#!/usr/bin/env python3
"""Tests 1.13.14 : voix, partie serveur (vrai presence_server.py).

Signalisation {t:'rtc', to:id, d:{...}} : le destinataire recoit {t:'rtc', id, d} ; l'expediteur ne recoit rien. Erreurs {t:'rtcerr', to, why} avec why =
off, rate, gone ou self. Jamais diffuse, jamais garde, contenu jamais ecrit dans la console. d : 3000 caracteres (JSON) au plus ; 200 messages par 10 s.
Mode orateur {t:'speaker', key, to?} (cle du salon, celle du journal des visites) : le salon recoit {t:'speaker', id} (0 : personne) ; erreurs
{t:'speakererr', why} avec why = off, key, rate ou gone. Options --no-voice et --ice ; le message welcome porte voice, ice et speaker.
Verifie :
1.  welcome : voice vrai, ice vide, speaker 0 ;
2.  A ecrit a B : B recoit id et d identiques ; ni A, ni le tiers, ni le spectateur, ni l'autre salon ne recoivent rien ;
3.  to inconnu, soi-meme, spectateur, autre salon : rtcerr gone / self / gone / gone ; to ou d invalides, d trop gros, spectateur expediteur : ignores ;
4.  cadence : 205 messages d'affilee : 200 relayes, puis rtcerr rate ;
5.  --no-voice : welcome voice faux, rtc et speaker repondent off ; --ice : welcome porte les adresses ; --ice invalide : le serveur refuse de demarrer ;
6.  mode orateur : mauvaise cle refusee ; bonne cle : tout le salon (spectateur compris) recoit l'orateur, un arrivant le trouve dans welcome ; la cle avec to
    donne la parole a un autre (to inconnu ou spectateur : gone) ; l'orateur arrete sans cle, un autre non ; la cle arrete celle d'un autre ; la parole se
    perd quand l'orateur part ou devient spectateur ; un salon sans cle refuse ;
7.  5 cles refusees par minute et par adresse : la sixieme repond rate meme avec la bonne cle ;
8.  la console ne contient ni le contenu d'un message rtc, ni une cle, et montre l'evenement orateur.
9.  1.13.19 muet du public : sans orateur, {t:'speaker', key, mute} repond nospeaker ; mauvaise cle refusee ; avec un orateur, le salon (spectateur compris) recoit
    {t:'speaker', id, mute:true}, un arrivant trouve mute vrai dans welcome ; la parole donnee a un autre garde le muet ; mute:false le rend (mute absent) ;
    la fin de l'orateur, son depart ou son passage en spectateur le rend ; un nouvel orateur n'est pas muet ; la console montre l'evenement sans cle.
Sur le main d'origine (1.13.13) : echec des le premier test (welcome sans voice).

Prerequis : pip install websockets ; python build.py avant. Lancer : python tests/presence_voice.py
"""
import asyncio, hashlib, json, os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import websockets

SALON = "voix"
CLE = "ABCD-EFGH-JKMN"
MAUVAISE = "AAAA-AAAA-AAAA"
SEL = "sel-de-test"


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


async def envoyer(ws, **m):
    await ws.send(json.dumps(m))


def fichier_cles():
    """fichier de cles de salon comme celui de la commande visits-key : la cle CLE pour le salon SALON"""
    h = hashlib.sha256((SEL + CLE.replace("-", "")).encode()).hexdigest()
    p = tmp / "cles_voix.json"
    p.write_text(json.dumps({"rooms": {SALON: {"salt": SEL, "hash": h, "added": 0}}}), encoding="utf-8")
    return str(p)


async def fermer(*ws):
    for w in ws:
        await w.close()


async def signalisation(port):
    res = []
    a, wa = await entrer(port, "Alice", "a")
    b, wb = await entrer(port, "Bob", "b")
    d, wd = await entrer(port, "Dave", "d")          # tiers, meme salon
    s, ws_ = await entrer(port, "Spec", "s", spectateur=True)
    c, wc = await entrer(port, "Carol", "c", salon="autre")
    ia, ib, is_, ic = wa["id"], wb["id"], ws_["id"], wc["id"]
    res.append((wa.get("voice") is True and wa.get("ice") == [] and wa.get("speaker") == 0, "welcome : voice vrai, ice vide, speaker 0",
                (wa.get("voice"), wa.get("ice"), wa.get("speaker"))))
    offre = {"type": "offer", "sdp": "v=0 secret-sdp-42"}
    await envoyer(a, t="rtc", to=ib, d=offre)
    mb = await recv_t(b, "rtc")
    res.append((mb == {"t": "rtc", "id": ia, "d": offre}, "B recoit id de A et d identique", mb))
    tiers = [await recv_t(x, "rtc", 0.3) for x in (a, d, s, c)]
    res.append((tiers == [None] * 4, "ni l'expediteur, ni le tiers, ni le spectateur, ni l'autre salon ne recoivent rien", tiers))
    for to, why in ((9999, "gone"), (ia, "self"), (is_, "gone"), (ic, "gone")):
        await envoyer(a, t="rtc", to=to, d=offre)
        e = await recv_t(a, "rtcerr")
        res.append((e == {"t": "rtcerr", "to": to, "why": why}, f"to = {to} : rtcerr {why}", e))
    rien = []
    for m in ({"to": True, "d": {}}, {"to": "x", "d": {}}, {"d": {}}, {"to": ib, "d": [1]}, {"to": ib, "d": "texte"}, {"to": ib},
              {"to": ib, "d": {"sdp": "x" * 3100}}):
        await envoyer(a, t="rtc", **m)
        rien.append((await recv_t(a, "rtcerr", 0.2), await recv_t(b, "rtc", 0.2)))
    res.append((rien == [(None, None)] * 7, "to ou d invalides et d trop gros : ignores, sans reponse", rien))
    await envoyer(a, t="rtc", to=ib, d={"n": 1})
    res.append(((await recv_t(b, "rtc") or {}).get("d") == {"n": 1}, "la connexion reste ouverte apres un message trop gros", None))
    await envoyer(s, t="rtc", to=ia, d={"n": 2})
    res.append(((await recv_t(a, "rtc", 0.3), await recv_t(s, "rtcerr", 0.3)) == (None, None), "un spectateur ne peut pas envoyer", None))
    await fermer(a, b, d, s, c)
    return res


async def cadence(port):
    a, wa = await entrer(port, "Alice", "a")
    b, wb = await entrer(port, "Bob", "b")
    for i in range(205):
        await envoyer(a, t="rtc", to=wb["id"], d={"n": i})
    err = await recv_t(a, "rtcerr", 2.0)
    n = 0
    while await recv_t(b, "rtc", 0.5):
        n += 1
    await fermer(a, b)
    return [(bool(err) and err["why"] == "rate" and n == 200, "205 messages d'affilee : 200 relayes puis rate", (err, n))]


async def sans_voix(port, cle):
    a, wa = await entrer(port, "Alice", "a")
    b, wb = await entrer(port, "Bob", "b")
    res = [(wa.get("voice") is False and wa.get("ice") == [] and wa.get("speaker") == 0, "--no-voice : welcome voice faux, ice vide", wa)]
    await envoyer(a, t="rtc", to=wb["id"], d={"n": 1})
    e = await recv_t(a, "rtcerr")
    res.append((e == {"t": "rtcerr", "to": wb["id"], "why": "off"} and await recv_t(b, "rtc", 0.3) is None, "--no-voice : rtc repond off, rien chez l'autre", e))
    await envoyer(a, t="speaker", key=cle)
    e = await recv_t(a, "speakererr")
    res.append((e == {"t": "speakererr", "why": "off"} and await recv_t(b, "speaker", 0.3) is None, "--no-voice : speaker repond off meme avec la bonne cle", e))
    await fermer(a, b)
    return res


async def avec_ice(port):
    a, wa = await entrer(port, "Alice", "a")
    await fermer(a)
    return [(wa.get("voice") is True and wa.get("ice") == ["stun:127.0.0.1:3478", "stuns:127.0.0.1:5349"], "--ice : welcome porte les deux adresses", wa.get("ice"))]


async def orateur(port):
    res = []
    a, wa = await entrer(port, "Alice", "a")
    b, wb = await entrer(port, "Bob", "b")
    c, wc = await entrer(port, "Carol", "c")
    s, ws_ = await entrer(port, "Spec", "s", spectateur=True)
    z, wz = await entrer(port, "Zoe", "z", salon="autre")
    ia, ib, ic, is_ = wa["id"], wb["id"], wc["id"], ws_["id"]
    tous = (a, b, c, s)

    async def vu(attendu, nom, qui=tous):
        r = [await recv_t(x, "speaker") for x in qui]
        res.append((r == [{"t": "speaker", "id": attendu}] * len(qui), nom, r))

    async def rien(nom, qui=tous):
        r = [await recv_t(x, "speaker", 0.2) for x in qui]
        res.append((r == [None] * len(qui), nom, r))

    await envoyer(a, t="speaker", key=MAUVAISE)
    e = await recv_t(a, "speakererr")
    res.append((e == {"t": "speakererr", "why": "key"}, "mauvaise cle : speakererr key", e))
    await rien("mauvaise cle : personne ne devient orateur")
    await envoyer(a, t="speaker", key=CLE.lower())
    await vu(ia, "bonne cle (en minuscules) sans to : A est l'orateur, vu par tout le salon et le spectateur")
    e1, wn = await entrer(port, "Eve", "e")
    res.append((wn.get("speaker") == ia, "un arrivant trouve l'orateur dans welcome", wn.get("speaker")))
    await envoyer(b, t="speaker", key=CLE, to=ic)
    await vu(ic, "cle avec to : la parole passe a C", tous)
    await envoyer(b, t="speaker", key=CLE, to=9999)
    e = await recv_t(b, "speakererr")
    res.append((e == {"t": "speakererr", "why": "gone"}, "to inconnu : gone", e))
    await envoyer(b, t="speaker", key=CLE, to=is_)
    e = await recv_t(b, "speakererr")
    res.append((e == {"t": "speakererr", "why": "gone"}, "to spectateur : gone", e))
    await rien("to refuse : l'orateur ne change pas")
    await envoyer(a, t="speaker", off=True)
    await rien("off sans cle par un autre que l'orateur : ignore")
    res.append((await recv_t(a, "speakererr", 0.2) is None, "off sans cle par un autre : aucune reponse", None))
    await envoyer(c, t="speaker", off=True)
    await vu(0, "l'orateur arrete sans cle : personne")
    await envoyer(b, t="speaker", key=CLE)
    await vu(ib, "B devient orateur", tous)
    await envoyer(a, t="speaker", key=CLE, off=True)
    await vu(0, "la cle arrete l'orateur d'un autre")
    await envoyer(a, t="speaker", key=CLE)
    await vu(ia, "A orateur", tous)
    await a.close()
    await vu(0, "l'orateur part : plus d'orateur", (b, c, s))
    await envoyer(b, t="speaker", key=CLE)
    await vu(ib, "B orateur", (b, c, s))
    await envoyer(b, t="role", walker=False)
    await vu(0, "l'orateur devient spectateur : plus d'orateur", (b, c, s))
    await envoyer(z, t="speaker", key=CLE)
    e = await recv_t(z, "speakererr")
    res.append((e == {"t": "speakererr", "why": "key"}, "un salon sans cle refuse (la cle d'un autre salon ne sert pas)", e))
    await fermer(b, c, s, z, e1)
    return res


async def public_muet(port):
    res = []
    a, wa = await entrer(port, "Alice", "a")
    b, wb = await entrer(port, "Bob", "b")
    c, wc = await entrer(port, "Carol", "c")
    s, ws_ = await entrer(port, "Spec", "s", spectateur=True)
    ia, ib, ic = wa["id"], wb["id"], wc["id"]
    tous = [a, b, c, s]
    res.append((wa.get("mute") is False, "welcome : mute faux sans orateur", wa.get("mute")))

    async def vu(attendu, nom, qui=None):
        qui = tous if qui is None else qui
        r = [await recv_t(x, "speaker") for x in qui]
        res.append((r == [attendu] * len(qui), nom, r))

    await envoyer(a, t="speaker", key=CLE, mute=True)
    e = await recv_t(a, "speakererr")
    res.append((e == {"t": "speakererr", "why": "nospeaker"}, "muet sans orateur : nospeaker", e))
    await envoyer(a, t="speaker", key=CLE)
    await vu({"t": "speaker", "id": ia}, "A orateur : pas de mute dans le message")
    await envoyer(b, t="speaker", key=MAUVAISE, mute=True)
    e = await recv_t(b, "speakererr")
    res.append((e == {"t": "speakererr", "why": "key"}, "muet avec une mauvaise cle : key", e))
    res.append(((await recv_t(a, "speaker", 0.2)) is None, "muet refuse : rien de diffuse", None))
    await envoyer(b, t="speaker", key=CLE, mute=True)
    await vu({"t": "speaker", "id": ia, "mute": True}, "muet par la cle : tout le salon, spectateur compris, recoit mute vrai")
    e1, wn = await entrer(port, "Eve", "e")
    tous.append(e1)
    res.append((wn.get("speaker") == ia and wn.get("mute") is True, "un arrivant trouve l'orateur et mute vrai dans welcome", (wn.get("speaker"), wn.get("mute"))))
    await envoyer(b, t="speaker", key=CLE, to=ic)
    await vu({"t": "speaker", "id": ic, "mute": True}, "la parole passe a C : le muet reste", tous)
    await envoyer(b, t="speaker", key=CLE, mute=False)
    await vu({"t": "speaker", "id": ic}, "mute:false : micros rendus (mute absent)", tous)
    await envoyer(b, t="speaker", key=CLE, mute=True)
    await vu({"t": "speaker", "id": ic, "mute": True}, "muet de nouveau", tous)
    await envoyer(c, t="speaker", off=True)
    await vu({"t": "speaker", "id": 0}, "fin de l'orateur : micros rendus (mute absent)", tous)
    e2, wn2 = await entrer(port, "Fay", "f")
    tous.append(e2)
    res.append((wn2.get("speaker") == 0 and wn2.get("mute") is False, "apres la fin : welcome mute faux", (wn2.get("speaker"), wn2.get("mute"))))
    await envoyer(a, t="speaker", key=CLE)
    await vu({"t": "speaker", "id": ia}, "un nouvel orateur n'est pas muet", (a, b, c, s, e1, e2))
    await envoyer(b, t="speaker", key=CLE, mute=True)
    await vu({"t": "speaker", "id": ia, "mute": True}, "muet", (a, b, c, s, e1, e2))
    await a.close()
    await vu({"t": "speaker", "id": 0}, "l'orateur part : micros rendus", (b, c, s, e1, e2))
    await envoyer(b, t="speaker", key=CLE)
    await vu({"t": "speaker", "id": ib}, "B orateur", (b, c, s, e1, e2))
    await envoyer(b, t="speaker", key=CLE, mute=True)
    await vu({"t": "speaker", "id": ib, "mute": True}, "muet", (b, c, s, e1, e2))
    await envoyer(b, t="role", walker=False)
    await vu({"t": "speaker", "id": 0}, "l'orateur devient spectateur : micros rendus", (b, c, s, e1, e2))
    await fermer(b, c, s, e1, e2)
    return res


async def cadence_cles(port):
    a, wa = await entrer(port, "Alice", "a")
    r = []
    for _ in range(5):
        await envoyer(a, t="speaker", key=MAUVAISE)
        r.append((await recv_t(a, "speakererr") or {}).get("why"))
    await envoyer(a, t="speaker", key=CLE)
    r.append((await recv_t(a, "speakererr") or {}).get("why"))
    fin = await recv_t(a, "speaker", 0.3)
    await fermer(a)
    return [(r == ["key"] * 5 + ["rate"] and fin is None, "5 cles refusees : la sixieme repond rate meme avec la bonne cle", r)]


def verifier(res):
    for ok, nom, det in res:
        rapport(ok, nom, "" if ok else det)


def serveur_et_essai(essai, *extra, sortie=False):
    proc, port = lancer_presence("--lang", "fr", "--max-per-ip", "50", "--chat-gap", "0.05", *extra)
    try:
        verifier(asyncio.run(essai(port)))
    finally:
        time.sleep(0.3)
        proc.kill()
        out = proc.communicate()[0]
    return out if sortie else None


cles = fichier_cles()
out = serveur_et_essai(signalisation, "--visits-keys", cles, sortie=True)
rapport("secret-sdp-42" not in out, "la console ne contient pas le contenu d'un message rtc", out[-300:] if "secret-sdp-42" in out else "")
serveur_et_essai(cadence, "--visits-keys", cles)
serveur_et_essai(lambda p: sans_voix(p, CLE), "--no-voice", "--visits-keys", cles)
serveur_et_essai(avec_ice, "--ice", "stun:127.0.0.1:3478", "--ice", "stuns:127.0.0.1:5349")
out = serveur_et_essai(orateur, "--visits-keys", cles, sortie=True)
fuite = [k for k in (CLE, CLE.replace("-", ""), MAUVAISE) if k.lower() in out.lower()]
rapport(not fuite, "la console ne contient aucune cle (ni bonne, ni refusee)", fuite)
rapport(bool(re.search(r"orateur.*Alice", out)), "la console montre l'evenement orateur", out[-300:])
serveur_et_essai(cadence_cles, "--visits-keys", cles)
out = serveur_et_essai(public_muet, "--visits-keys", cles, sortie=True)
fuite = [k for k in (CLE, CLE.replace("-", ""), MAUVAISE) if k.lower() in out.lower()]
rapport(not fuite, "muet du public : la console ne contient aucune cle", fuite)
rapport(bool(re.search(r"orateur.*micros du public", out)), "muet du public : la console montre l'evenement", out[-300:])

for ice in (["http://exemple"], ["stun:a:1"] * 5, ["stun:"], ["turn:127.0.0.1:3478"]):
    args = [x for u in ice for x in ("--ice", u)]
    r = subprocess.run([sys.executable, str(DIST / "presence_server.py"), "--lang", "fr", "--host", "127.0.0.1", "--port", str(port_libre()), "--identities", "", *args],
                       capture_output=True, text=True, cwd=tmp, timeout=20, stdin=subprocess.DEVNULL)
    rapport(r.returncode == 2 and "--ice" in r.stderr, f"--ice invalide {ice[:2]} : le serveur refuse de demarrer", (r.returncode, r.stderr[-200:]))

sys.exit(1 if resultat() else 0)
