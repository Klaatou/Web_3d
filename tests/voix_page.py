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
8.  serveur --no-voice : aucun bouton Voix.
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
        finally:
            await br.close()
    ps.terminate(); pn.terminate(); srv.terminate()


asyncio.run(main())
sys.exit(1 if resultat() else 0)
