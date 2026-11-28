#!/usr/bin/env python3
"""Tests 1.13.15 : voix, cote page (vrai presence_server.py, vraie page, deux Chromium avec micro simule).

Verifie :
1.  bouton Voix visible en promenade (serveur avec voix) ; fenetre Voix ; micro refuse = message, rien ne demarre ;
2.  deux visiteurs proches activent micro + ecoute : un lien WebRTC 'link' de chaque cote, un seul lien par paire ;
3.  l'audio circule (octets recus > 0), dans les DEUX sens (1.13.18 : le repondeur a l'offre n'envoyait rien) ; parler = micro ouvert (touche X tenue), relache = ferme ;
4.  son spatial : le lien est sur le chemin de proximite (spatial vrai, gain proximite 1, gain orateur 0) ;
5.  s'eloigner au-dela de 36 m ferme le lien, revenir le rouvre ;
6.  mode orateur : mauvaise cle refusee (message) ; bonne cle : orateur annonce aux deux, son direct (spatial faux), meme a 100 m ; fin de l'orateur ;
7.  couper la voix ferme les liens des deux cotes ; ecoute seule recoit sans envoyer ; aucune erreur de page ;
8.  serveur --no-voice : aucun bouton Voix ;
9.  1.13.19 muet du public : sans orateur rien ne change ; l'orateur coupe les micros (case) : micro et touche X bloques chez le public, aucun son du public joue,
    l'orateur s'entend toujours ; un arrivant est muet des l'accueil ; la parole donnee garde le muet ; rendre, fin de l'orateur : tout est libre.
10. 1.13.26 fenetre Voix : « Micro ouvert en continu » noircit le bouton Parler tout de suite et durablement, la case du muet affiche son etat tout de suite,
    chaque bouton, case et champ a sa bulle (« Donner la parole » nomme le visiteur).
Non teste ici : Windows, Edge, vrai reseau et serveur STUN, tactile. Lancer : python tests/voix_page.py (apres python build.py)
"""
import asyncio, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

SALON, CLE, SEL = "voix", "ABCD-EFGH-JKMN", "sel-de-test"
V = "window.__viewer."
LINKS = "window.__viewer.voiceInfo().peers.filter(p => p.state === 'link').length"


def nom(n):
    return "try { localStorage.setItem('glb2html_name', '%s'); } catch (e) {}" % n


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    sol_glb(site / "sol.glb", demi=150.0)
    (tmp / "z.json").write_text(json.dumps([{"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0.0}]), encoding="utf-8")
    cles = tmp / "cles.json"
    cles.write_text(json.dumps({"rooms": {SALON: {"salt": SEL, "hash": hashlib.sha256((SEL + CLE.replace("-", "")).encode()).hexdigest(), "added": 0}}}), encoding="utf-8")
    ps, port_v = lancer_presence("--visits-keys", str(cles))
    pn, port_n = lancer_presence("--no-voice")
    for n, u, room in (("Voix", f"ws://127.0.0.1:{port_v}", SALON), ("Muet", f"ws://127.0.0.1:{port_n}", "muet")):
        html(site / "sol.glb", "-o", site / (n + ".html"), "--shared-shell", "--zones", tmp / "z.json", "--no-sea", "--target", "0,0,0", "--presence-url", u, "--room", room, "--title", "Ile Test")
    srv, port = serveur(site)
    url = lambda n: f"http://127.0.0.1:{port}/index.html?region={n}#spawn=default"
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream", "--autoplay-policy=no-user-gesture-required"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        try:
            ctxa = await br.new_context(viewport={"width": 1000, "height": 700}, permissions=["microphone"])
            ctxb = await br.new_context(viewport={"width": 1000, "height": 700}, permissions=["microphone"])
            a = await Onglet(br).ouvrir(url("Voix"), init=STUB + nom("Ana"), ctx=ctxa)
            b = await Onglet(br).ouvrir(url("Voix"), init=STUB + nom("Ben"), ctx=ctxb)
            for o in (a, b):
                await o.attendre(V + "walking && " + V + "getPresence().state === 'online'", 40)
            await a.pg.wait_for_timeout(1500)
            rapport(await a.ev(V + "voiceOK") and await b.ev(V + "voiceOK"), "serveur avec voix : voiceOK des deux cotes")
            await a.pg.wait_for_timeout(1200)
            rapport(await a.ev("!document.getElementById('voiceBtn').hidden"), "bouton Voix visible en promenade")
            GRP = "[...document.querySelectorAll('.grp .gt')].map(e => e.textContent).join('|')"
            rapport(await a.ev("/Voix|Voice/.test(" + GRP + ")"), "1.13.23 : l'aide (H) a un groupe Voix quand la voix est disponible")
            await a.ev("document.getElementById('voiceBtn').click()")
            rapport(await a.ev("!!document.querySelector('.vcWin') && !document.querySelector('.vcWin').hidden"), "le bouton ouvre la fenetre Voix")

            print("--- liens")
            ra = await a.ev(V + "voiceStart(true)"); rb = await b.ev(V + "voiceStart(true)")
            rapport(ra["ok"] and rb["ok"] and ra["mic"] and rb["mic"], "micro + ecoute demarrent (micro simule)", (ra, rb))
            try:
                await a.attendre(LINKS + " === 1", 30); await b.attendre(LINKS + " === 1", 30)
                ok = True
            except Exception:
                ok = False
            rapport(ok, "un lien 'link' de chaque cote", (await a.ev(V + "voiceInfo()"), await b.ev(V + "voiceInfo()")))
            rapport(len(await a.ev(V + "voiceInfo().peers")) == 1 and len(await b.ev(V + "voiceInfo().peers")) == 1, "un seul lien par paire")
            await a.ev(V + "voiceTalk(true)"); await a.pg.wait_for_timeout(2500)
            sb = await b.ev(V + "voiceStats()"); sa = await a.ev(V + "voiceStats()")
            rapport(sb and sb[0]["received"] > 0 and sa[0]["sent"] > 0, "l'audio circule (octets envoyes par Ana, recus par Ben)", (sa, sb))
            rapport(sb[0]["spatial"] is True, "lien sur le chemin de proximite (spatial)")
            await b.ev(V + "voiceTalk(true)"); await a.pg.wait_for_timeout(2500)
            sb2 = await b.ev(V + "voiceStats()"); sa2 = await a.ev(V + "voiceStats()")
            rapport(bool(sa2) and bool(sb2) and sa2[0]["received"] > 0 and sb2[0]["sent"] > 0, "l'audio circule aussi dans l'autre sens (Ben, qui repond a l'offre, vers Ana)", (sa2, sb2))
            await b.ev(V + "voiceTalk(false)")
            await a.ev(V + "voiceTalk(false)")
            await a.touche("KeyX"); 
            await a.key("keydown", "KeyX"); await a.pg.wait_for_timeout(200)
            rapport(await a.ev(V + "voiceInfo().talk"), "touche X tenue : micro ouvert")
            await a.key("keyup", "KeyX"); await a.pg.wait_for_timeout(200)
            rapport(not await a.ev(V + "voiceInfo().talk"), "touche X relachee : micro ferme")

            print("--- distance")
            await b.ev("window.__viewer.teleportTo([60, 15, 0], 0)"); await b.pg.wait_for_timeout(1500)
            try:
                await a.attendre(LINKS + " === 0", 15); ok = True
            except Exception:
                ok = False
            rapport(ok, "au-dela de 36 m : le lien est ferme", await a.ev(V + "voiceInfo()"))
            await b.ev("window.__viewer.teleportTo([5, 15, 0], 0)")
            try:
                await a.attendre(LINKS + " === 1", 40); await b.attendre(LINKS + " === 1", 40); ok = True
            except Exception:
                ok = False
            rapport(ok, "retour a portee : le lien se rouvre", (await a.ev(V + "voiceInfo()"), await b.ev(V + "voiceInfo()")))

            print("--- mode orateur")
            await b.ev(V + "voiceSpeaker('MAUVAISE-CLE-00')"); await b.pg.wait_for_timeout(700)
            rapport(await b.ev(V + "voiceInfo().speaker") == 0, "mauvaise cle : pas d'orateur")
            rapport("cl" in (await b.txt("toast")).lower() or "key" in (await b.txt("toast")).lower(), "mauvaise cle : message affiche", await b.txt("toast"))
            await b.ev(V + "voiceSpeaker(%s)" % json.dumps(CLE)); await b.pg.wait_for_timeout(800)
            ida, idb = await a.ev(V + "voiceInfo().me"), await b.ev(V + "voiceInfo().me")
            rapport(await a.ev(V + "voiceInfo().speaker") == idb and await b.ev(V + "voiceInfo().speaker") == idb, "bonne cle : Ben est orateur pour les deux", (ida, idb))
            sa = await a.ev(V + "voiceStats()")
            rapport(sa and sa[0]["spatial"] is False, "chez Ana : son de l'orateur direct (non spatial)", sa)
            await b.ev("window.__viewer.teleportTo([100, 15, 0], 0)"); await b.pg.wait_for_timeout(2500)
            rapport(await a.ev(LINKS) == 1, "orateur a 100 m : le lien reste ouvert", await a.ev(V + "voiceInfo()"))
            await b.ev(V + "voiceSpeakerOff(%s)" % json.dumps(CLE)); await b.pg.wait_for_timeout(800)
            rapport(await a.ev(V + "voiceInfo().speaker") == 0, "fin de l'orateur annoncee")
            try:
                await a.attendre(LINKS + " === 0", 15); ok = True
            except Exception:
                ok = False
            rapport(ok, "fin de l'orateur et distance : le lien se ferme", await a.ev(V + "voiceInfo()"))

            print("--- coupure")
            await b.ev("window.__viewer.teleportTo([5, 15, 0], 0)")
            await a.attendre(LINKS + " === 1", 40)
            await a.ev(V + "voiceStop()"); await a.pg.wait_for_timeout(800)
            rapport(not await a.ev(V + "voiceOn") and await b.ev(LINKS) == 0, "couper la voix ferme le lien des deux cotes", await b.ev(V + "voiceInfo()"))
            ras = await a.ev(V + "voiceStart(false)")
            rapport(ras["ok"] and not ras["mic"], "ecoute seule : demarre sans micro", ras)
            try:
                await a.attendre(LINKS + " === 1", 30); ok = True
            except Exception:
                ok = False
            rapport(ok, "ecoute seule : le lien s'etablit", (await a.ev(V + "voiceInfo()"), await b.ev(V + "voiceInfo()"), await b.ev(V + "voiceStats()")))
            rapport(not (a.errs + b.errs), "aucune erreur de page", (a.errs + b.errs)[:5])

            print("--- trois visiteurs")
            ctx3 = await br.new_context(viewport={"width": 1000, "height": 700}, permissions=["microphone"])
            t3 = await Onglet(br).ouvrir(url("Voix"), init=STUB + nom("Eva"), ctx=ctx3)
            await t3.attendre(V + "walking && " + V + "voiceOK", 40)
            await t3.ev(V + "voiceStart(true)")
            try:
                for o in (a, b, t3):
                    await o.attendre(LINKS + " === 2", 40)
                ok = True
            except Exception:
                ok = False
            rapport(ok, "3 visiteurs proches : chacun a 2 liens (maillage complet)", [await o.ev(V + "voiceInfo().peers.map(p => p.state)") for o in (a, b, t3)])
            await t3.ev("window.__viewer.teleportTo([40, 15, 0], 0)"); await b.ev("window.__viewer.teleportTo([20, 15, 0], 0)")
            await a.ev("window.__viewer.teleportTo([0, 15, 0], 0)"); await a.pg.wait_for_timeout(3000)
            rapport(await a.ev(LINKS) == 1 and await b.ev(LINKS) == 2 and await t3.ev(LINKS) == 1, "A(0) B(20) E(40) : B entend les deux, A et E ne s'entendent pas",
                    [await o.ev(V + "voiceInfo().peers.map(p => p.name + ':' + p.state)") for o in (a, b, t3)])

            print("--- public muet")
            idb, ide = await b.ev(V + "voiceInfo().me"), await t3.ev(V + "voiceInfo().me")
            await a.ev(V + "voiceStop()"); await a.pg.wait_for_timeout(800); await a.ev(V + "voiceStart(true)")      # Ana revient avec un micro (public qui peut parler)
            await a.attendre(LINKS + " === 1", 40); await b.attendre(LINKS + " === 2", 40)
            await b.ev(V + "voiceMute(%s, true)" % json.dumps(CLE)); await b.pg.wait_for_timeout(700)
            rapport(not await b.ev(V + "voiceInfo().mute"), "muet sans orateur : sans effet")
            await b.ev(V + "voiceSpeaker(%s)" % json.dumps(CLE)); await b.pg.wait_for_timeout(800)
            rapport(await a.ev(V + "voiceInfo().speaker") == idb and not await a.ev(V + "voiceInfo().muted"), "orateur sans muet : le public parle librement")
            await a.ev(V + "voiceTalk(true)"); await a.pg.wait_for_timeout(500)
            await b.ev(V + "voiceMute(%s, true)" % json.dumps(CLE)); await b.pg.wait_for_timeout(1000)
            etat = [(await o.ev(V + "voiceInfo().mute"), await o.ev(V + "voiceInfo().muted")) for o in (a, b, t3)]
            rapport(etat == [(True, True), (True, False), (True, True)], "muet : le public est muet, l'orateur non", etat)
            rapport(await a.ev(V + "voiceInfo().talk") and not await a.ev(V + "voiceInfo().speaking"), "chez le public : micro demande ouvert mais ferme (ne parle pas)")
            await a.key("keydown", "KeyX"); await a.pg.wait_for_timeout(300); await a.key("keyup", "KeyX")
            rapport("coup" in (await a.txt("toast")).lower() or "muted" in (await a.txt("toast")).lower(), "touche X chez le public : message micro coupe", await a.txt("toast"))
            await b.ev(V + "voiceTalk(true)"); await b.pg.wait_for_timeout(2500)
            sb = await b.ev(V + "voiceStats()"); sa = await a.ev(V + "voiceStats()")
            rapport(bool(sb) and all(not x["heard"] for x in sb), "chez l'orateur : la voix du public n'est pas jouee", sb)
            rapport(bool(sa) and any(x["heard"] and not x["spatial"] for x in sa) and all(x["heard"] or x["spatial"] for x in sa), "chez le public : la voix de l'orateur est jouee", sa)
            rapport(any(x["received"] > 0 for x in sa), "l'audio de l'orateur arrive au public", sa)
            ctx4 = await br.new_context(viewport={"width": 1000, "height": 700}, permissions=["microphone"])
            t4 = await Onglet(br).ouvrir(url("Voix"), init=STUB + nom("Zoe"), ctx=ctx4)
            await t4.attendre(V + "walking && " + V + "voiceOK", 40)
            await t4.pg.wait_for_timeout(800)
            rapport(await t4.ev(V + "voiceInfo().mute") and await t4.ev(V + "voiceInfo().muted"), "un arrivant est muet des l'accueil", await t4.ev(V + "voiceInfo()"))
            await t4.ev(V + "voiceStart(true)"); await t4.ev(V + "voiceTalk(true)"); await t4.pg.wait_for_timeout(500)
            rapport(not await t4.ev(V + "voiceInfo().speaking"), "l'arrivant ne peut pas parler")
            await b.ev(V + "voiceSpeaker(%s, %d)" % (json.dumps(CLE), ide)); await b.pg.wait_for_timeout(1000)
            etat = [(await o.ev(V + "voiceInfo().speaker") == ide, await o.ev(V + "voiceInfo().mute"), await o.ev(V + "voiceInfo().muted")) for o in (a, b, t3, t4)]
            rapport(etat == [(True, True, True), (True, True, True), (True, True, False), (True, True, True)], "la parole passe a Eva : le muet reste, elle seule est libre", etat)
            await b.ev(V + "voiceSpeaker(%s)" % json.dumps(CLE)); await b.pg.wait_for_timeout(1000)
            await b.ev(V + "voiceMute(%s, false)" % json.dumps(CLE)); await b.pg.wait_for_timeout(1000)
            etat = [(await o.ev(V + "voiceInfo().mute"), await o.ev(V + "voiceInfo().muted")) for o in (a, b, t3, t4)]
            rapport(etat == [(False, False)] * 4, "mute:false : tout le monde est libre", etat)
            await b.ev(V + "voiceMute(%s, true)" % json.dumps(CLE)); await b.pg.wait_for_timeout(800)
            await b.ev(V + "voiceSpeakerOff(%s)" % json.dumps(CLE)); await b.pg.wait_for_timeout(1000)
            etat = [(await o.ev(V + "voiceInfo().speaker"), await o.ev(V + "voiceInfo().mute"), await o.ev(V + "voiceInfo().muted")) for o in (a, b, t3, t4)]
            rapport(etat == [(0, False, False)] * 4, "fin de l'orateur : tout est libre", etat)
            print("--- fenetre Voix : bouton Parler et bulles (1.13.26)")
            WIN = "document.querySelector('.vcWin:not([hidden])')"
            HOLD = WIN + ".querySelector('button.hold')"
            CLIC = "(() => { const c = document.querySelectorAll('.vcWin input[type=checkbox]')[%d]; c.focus(); c.click(); })()"      # focus puis clic : la case garde le focus, comme sous la souris
            await b.ev(V + "voiceTalk(false)")
            await b.pg.click("#voiceBtn"); await b.pg.wait_for_timeout(700)
            rapport(await b.ev("!!" + WIN), "la fenetre Voix s'ouvre")
            rapport(not await b.ev("!!" + HOLD), "micro ferme : le bouton Parler n'est pas noirci")
            await b.ev(CLIC % 0); await b.pg.wait_for_timeout(500)
            rapport(await b.ev("!!" + HOLD), "micro ouvert en continu : le bouton Parler est noirci tout de suite")
            await b.pg.wait_for_timeout(2500)
            rapport(await b.ev("!!" + HOLD) and await b.ev(V + "voiceInfo().talk"), "... et le reste apres les redessins")
            await b.ev(CLIC % 0); await b.pg.wait_for_timeout(500)
            rapport(not await b.ev("!!" + HOLD) and not await b.ev(V + "voiceInfo().talk"), "case decochee : le bouton redevient normal, micro ferme")
            await b.ev(V + "voiceSpeaker(%s)" % json.dumps(CLE)); await b.pg.wait_for_timeout(1500)
            n = await b.ev(WIN + ".querySelectorAll('input[type=checkbox]').length")
            rapport(n == 2, "orateur : la case « Couper les micros du public » apparait", n)
            await b.ev("(() => { const k = document.querySelector('.vcWin input[type=password]'); k.value = %s; k.dispatchEvent(new Event('change')); })()" % json.dumps(CLE))      # la cle tapee dans le champ
            await b.pg.wait_for_timeout(1300)
            await b.ev(CLIC % 1); await b.pg.wait_for_timeout(1500)
            rapport(await b.ev(V + "voiceInfo().mute") and await b.ev("[...%s.querySelectorAll('.vcTip')].some(e => /public coup|Audience microphones are muted/i.test(e.textContent))" % WIN),
                    "case du muet cochee : l'etat s'affiche tout de suite dans la fenetre")
            tips = await b.ev("[...%s.querySelectorAll('button, input[type=password], label')].filter(e => !e.closest('.mpHead')).map(e => [e.textContent.trim().slice(0, 30), e.title])" % WIN)
            vides = [t for t in tips if not t[1]]
            rapport(len(tips) >= 7 and not vides, "chaque bouton, case et champ de la fenetre Voix a sa bulle", vides or len(tips))
            rapport(any("Ana" in t[1] for t in tips), "la bulle de « Donner la parole » nomme le visiteur designe", [t for t in tips if "Ana" in t[1]])
            await b.ev(V + "voiceMute(%s, false)" % json.dumps(CLE)); await b.pg.wait_for_timeout(800)
            await b.ev(V + "voiceSpeakerOff(%s)" % json.dumps(CLE)); await b.pg.wait_for_timeout(1000)
            rapport(not (a.errs + b.errs + t3.errs + t4.errs), "aucune erreur de page", (a.errs + b.errs + t3.errs + t4.errs)[:5])

            print("--- micro refuse")
            ctxc = await br.new_context(viewport={"width": 1000, "height": 700})
            c = await Onglet(br).ouvrir(url("Voix"), init=STUB + nom("Cyd") + "; navigator.mediaDevices.getUserMedia = () => Promise.reject(Object.assign(new Error('x'), { name: 'NotAllowedError' }));", ctx=ctxc)
            await c.attendre(V + "walking && " + V + "voiceOK", 40)
            rc = await c.ev(V + "voiceStart(true)")
            rapport(not rc["ok"] and rc["why"] == "denied" and not await c.ev(V + "voiceOn"), "micro refuse : rien ne demarre, raison denied", rc)

            print("--- serveur sans voix")
            d = await Onglet(br).ouvrir(url("Muet"), init=STUB + nom("Dan"))
            await d.attendre(V + "walking && " + V + "getPresence().state === 'online'", 40)
            await d.pg.wait_for_timeout(2500)
            rapport(not await d.ev(V + "voiceOK") and await d.ev("document.getElementById('voiceBtn').hidden"), "--no-voice : pas de bouton Voix")
            rapport(not await d.ev("/Voix|Voice/.test(" + GRP + ")"), "1.13.23 : --no-voice : pas de groupe Voix dans l'aide")
        finally:
            await br.close()
    ps.terminate(); pn.terminate(); srv.terminate()


asyncio.run(main())
sys.exit(1 if resultat() else 0)
