#!/usr/bin/env python3
"""Tests v46 : commandes à l'écran (ligne d'état, flèches, mode tactile).

Vérifie, dans Chromium : ordinateur (1440 x 900) : ligne d'état en bas au centre (vue globale, promenade, course), pavé de flèches de la vue
globale (déplacer, tourner, rapprocher, recentrer au centre) et de la promenade (avancer, tourner, courir, monter en vol), appui maintenu à la
souris, touche K et bouton « Flèches (K) » (le bouton « Recentrer la vue » ne revient que si les flèches sont cachées), bulles, réglages,
diagnostic, invites remontées au-dessus du pavé. Écran tactile simulé (téléphone 390 x 844, à l'horizontale 844 x 390, tablette 1180 x 820) :
colonne de boutons, barre cachée, fenêtres réduites à l'ouverture avec un ✕, ligne d'état sous le bloc du pseudo, vrais gestes tactiles
(Input.dispatchTouchEvent) : glisser pour regarder, appui maintenu sur une flèche, appui long = bulle sans action, menu, chat (Envoyer,
Fermer). Anglais. Un vrai téléphone et une vraie tablette ne sont pas testables ici.

Prérequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v46.py
"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *

print("--- 0. fabrication des pages")
site = tmp / "site"; site.mkdir()
sol_glb(site / "sol.glb")
pres, pport = lancer_presence()
html(site / "sol.glb", "-o", site / "R.html", "--shared-shell", "--no-sea", "--target", "0,0,0", "--presence-url", f"ws://127.0.0.1:{pport}", "--room", "t46", "--chat")
http, hport = serveur(site)
URL = f"http://127.0.0.1:{hport}/index.html?region=R"
TEL = dict(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)

RECT = "(i) => { const e = document.getElementById(i); if (!e || e.hidden || !e.getClientRects().length) return null; const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; }"


def disjoint(a, b):
    return a is None or b is None or a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]


async def rect(o, i):
    return await o.ev(RECT, i)


async def mouse_hold(o, ident, ms):
    r = await rect(o, ident)
    await o.pg.mouse.move((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)
    await o.pg.mouse.down()
    await o.pg.wait_for_timeout(ms)
    await o.pg.mouse.up()


class Doigt:
    """vrais évènements tactiles (Chromium : Input.dispatchTouchEvent), donc de vrais pointerdown / pointermove de type « touch »"""
    def __init__(self, o):
        self.o = o

    async def init(self):
        self.cdp = await self.o.ctx.new_cdp_session(self.o.pg)
        return self

    async def ev(self, t, pts):
        await self.cdp.send("Input.dispatchTouchEvent", {"type": t, "touchPoints": [{"x": x, "y": y, "id": 1} for x, y in pts]})

    async def tenir(self, ident, ms):
        r = await rect(self.o, ident)
        x, y = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        await self.ev("touchStart", [(x, y)])
        await self.o.pg.wait_for_timeout(ms)
        await self.ev("touchEnd", [])

    async def tap(self, ident):
        await self.tenir(ident, 60)
        await self.o.pg.wait_for_timeout(150)

    async def glisser(self, x0, y0, dx, dy, n=10):
        await self.ev("touchStart", [(x0, y0)])
        for i in range(1, n + 1):
            await self.ev("touchMove", [(x0 + dx * i / n, y0 + dy * i / n)])
            await self.o.pg.wait_for_timeout(16)
        await self.ev("touchEnd", [])


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)

        print("--- 1. ordinateur, vue globale")
        o = await Onglet(br).ouvrir(URL + "#name=Zoe", viewport={"width": 1440, "height": 900})
        await o.pg.wait_for_timeout(300)
        st = await o.ev("({ txt: document.getElementById('statusLine').textContent, touch: document.body.classList.contains('touch'), pad: !document.getElementById('pad').hidden, g: !document.getElementById('padGlobal').hidden, w: !document.getElementById('padWalk').hidden, cb: document.getElementById('centerBtn').hidden, pb: document.getElementById('padBtn').textContent, pbp: document.getElementById('padBtn').getAttribute('aria-pressed'), tcol: document.getElementById('tcol').hidden })")
        rapport("Vue globale" in st["txt"] and "cible x" in st["txt"], "ligne d'état en vue globale", st["txt"])
        rapport(not st["touch"] and st["tcol"], "souris : pas de mode tactile, pas de colonne de boutons", st)
        rapport(st["pad"] and st["g"] and not st["w"], "pavé de la vue globale affiché par défaut", st)
        rapport(st["cb"], "le bouton « Recentrer la vue » cède la place au centre du pavé", st)
        rapport(st["pb"] == "Flèches (K)" and st["pbp"] == "true", "bouton « Flèches (K) » enfoncé", st)
        sl, pd, bar, chat = await rect(o, "statusLine"), await rect(o, "pad"), await rect(o, "bar"), await rect(o, "chat")
        rapport(sl and abs((sl[0] + sl[2]) / 2 - 720) < 2 and 880 <= sl[3] <= 890, "ligne d'état en bas au centre", sl)
        rapport(pd and pd[3] <= sl[1] and abs((pd[0] + pd[2]) / 2 - 720) < 2, "pavé au-dessus de la ligne d'état", [pd, sl])
        rapport(disjoint(bar, pd) and disjoint(bar, sl), "la barre de boutons ne touche ni le pavé ni la ligne d'état", [bar, pd, sl])
        cam0 = await o.ev("(() => { const v = window.__viewer; return { t: v.controls.target.toArray(), c: v.camera.position.toArray() }; })()")
        d0 = math.dist(cam0["t"], cam0["c"])
        await mouse_hold(o, "padFwd", 500)
        cam1 = await o.ev("(() => { const v = window.__viewer; return { t: v.controls.target.toArray(), c: v.camera.position.toArray() }; })()")
        mv = math.dist(cam0["t"], cam1["t"])
        rapport(mv > 1 and abs(math.dist(cam1["t"], cam1["c"]) - d0) < 0.5 and abs(cam1["t"][1] - cam0["t"][1]) < 1e-6, f"flèche « avant » tenue 0,5 s : la vue avance de {mv:.1f} m, à hauteur et distance constantes", [cam0, cam1])
        az = lambda c: math.atan2(c["c"][0] - c["t"][0], c["c"][2] - c["t"][2])
        await mouse_hold(o, "padTurnL", 400)
        cam2 = await o.ev("(() => { const v = window.__viewer; return { t: v.controls.target.toArray(), c: v.camera.position.toArray() }; })()")
        rapport(abs(az(cam2) - az(cam1)) > 0.1 and math.dist(cam2["t"], cam1["t"]) < 1e-6, "tourner la vue : la caméra tourne autour de la cible", [az(cam1), az(cam2)])
        await mouse_hold(o, "padIn", 400)
        cam3 = await o.ev("(() => { const v = window.__viewer; return { t: v.controls.target.toArray(), c: v.camera.position.toArray() }; })()")
        rapport(math.dist(cam3["t"], cam3["c"]) < math.dist(cam2["t"], cam2["c"]) - 0.5, "rapprocher : la distance diminue", [math.dist(cam2["t"], cam2["c"]), math.dist(cam3["t"], cam3["c"])])
        await o.pg.click("#padCenter"); await o.pg.wait_for_timeout(300)
        cam4 = await o.ev("window.__viewer.controls.target.toArray()")
        rapport(math.dist(cam4, cam0["t"]) < 0.5, "centre du pavé : la vue est recentrée", [cam4, cam0["t"]])
        tips = await o.ev("['padFwd', 'padCenter', 'walkBtn', 'homeBtn', 'mapBtn', 'padBtn', 'grabBtn', 'flyBtn'].map(i => document.getElementById(i).title)")
        rapport(all(tips) and "Maintenir" in tips[0], "bulles sur les flèches et les boutons de la barre", tips)
        await o.touche("KeyK"); await o.pg.wait_for_timeout(100)
        k1 = await o.ev("({ pad: document.getElementById('pad').hidden, cb: document.getElementById('centerBtn').hidden, pb: document.getElementById('padBtn').textContent, ls: JSON.parse(localStorage.getItem('glb2html_visitor')).pad, chk: document.getElementById('visPad').checked })")
        rapport(k1["pad"] and not k1["cb"] and k1["pb"] == "Flèches (K) : cachées" and k1["ls"] is False and not k1["chk"], "K cache les flèches ; « Recentrer la vue » revient ; réglage retenu", k1)
        await o.pg.click("#padBtn")
        k2 = await o.ev("({ pad: document.getElementById('pad').hidden, cb: document.getElementById('centerBtn').hidden, chk: document.getElementById('visPad').checked })")
        rapport(not k2["pad"] and k2["cb"] and k2["chk"], "le bouton « Flèches (K) » les remet", k2)
        hlp = await o.txt("helpBody")
        rapport("K : flèches à l'écran" in hlp, "aide : touche K")

        print("--- 2. ordinateur, promenade")
        await o.walk()
        await o.pg.wait_for_timeout(300)
        st = await o.ev("({ txt: document.getElementById('statusLine').textContent, g: document.getElementById('padGlobal').hidden, w: !document.getElementById('padWalk').hidden, fu: getComputedStyle(document.getElementById('padFlyUp')).visibility, zp: getComputedStyle(document.getElementById('zonePrompt')).bottom, la: (() => { const e = document.createElement('div'); e.id = 'lightAsk'; e.style.visibility = 'hidden'; if (!document.getElementById('lightAsk')) { document.body.append(e); const b = getComputedStyle(e).bottom; e.remove(); return b; } return getComputedStyle(document.getElementById('lightAsk')).bottom; })() })")
        rapport("Promenade" in st["txt"] and "à pied" in st["txt"] and "subjective" in st["txt"] and "x 0.0" in st["txt"], "ligne d'état en promenade : mode, allure, vue, position", st["txt"])
        rapport(st["g"] and st["w"] and st["fu"] == "hidden", "pavé de promenade (monter caché au sol)", st)
        rapport(st["zp"] == "220px" and st["la"] == "192px", "invite de zone et proposition de rendu léger au-dessus du pavé", st)
        g0 = await o.gw()
        await mouse_hold(o, "padUp", 700)
        g1 = await o.gw()
        rapport(dist_h(g0["pos"], g1["pos"]) > 0.5, f"flèche « avancer » tenue : l'avatar avance de {dist_h(g0['pos'], g1['pos']):.1f} m", [g0["pos"], g1["pos"]])
        await o.pg.wait_for_timeout(200)
        g2 = await o.gw()
        rapport(dist_h(g1["pos"], g2["pos"]) < 0.3, "relâchée : l'avatar s'arrête", [g1["pos"], g2["pos"]])
        await mouse_hold(o, "padLeft", 400)
        g3 = await o.gw()
        rapport(g3["yaw"] - g2["yaw"] > 0.2, "flèche « tourner à gauche » tenue", [g2["yaw"], g3["yaw"]])
        lay = await o.ev("[...document.getElementById('padWalk').children].map(e => e.id)")
        rapport(lay == ["padLeft", "padUp", "padRight", "padSideL", "padRun", "padSideR", "padFlyUp", "padDown", "padFlyDown"], "pavé : tourner en haut, pas de côté au milieu, monter / descendre en bas", lay)
        t0 = await o.gw()
        await mouse_hold(o, "padSideL", 600)
        t1 = await o.gw()
        dx, dz = t1["pos"][0] - t0["pos"][0], t1["pos"][2] - t0["pos"][2]
        fx, fz = -math.sin(t0["yaw"]), -math.cos(t0["yaw"])   # avant = (-sin yaw, -cos yaw)
        lat = dx * fz - dz * fx   # composante à gauche de l'avant (repère vu d'en haut)
        rapport(abs(t1["yaw"] - t0["yaw"]) < 1e-6 and lat > 0.4 and abs(dx * fx + dz * fz) < 0.2, f"pas de côté à gauche tenu : {dist_h(t0['pos'], t1['pos']):.1f} m de côté, sans tourner", [t0, t1, lat])
        tsl = await o.ev("document.getElementById('padSideL').title")
        rapport(tsl.startswith("Pas de côté à gauche (") and "Maintenir" in tsl, "bulle du pas de côté (lettre selon le clavier)", tsl)
        await o.pg.click("#padRun"); await o.pg.wait_for_timeout(300)
        r1 = await o.ev("({ p: document.getElementById('padRun').getAttribute('aria-pressed'), run: window.__viewer.getWalk().running, txt: document.getElementById('statusLine').textContent })")
        rapport(r1["p"] == "true" and r1["run"] and "course" in r1["txt"], "« Courir » allumé d'un clic (bord épais, mot « course » dans la ligne d'état)", r1)
        await o.pg.click("#padRun"); await o.pg.wait_for_timeout(300)
        rapport(not await o.ev("window.__viewer.getWalk().running"), "« Courir » éteint d'un second clic")
        await o.ev("window.__viewer.toggleFly()"); await o.pg.wait_for_timeout(300)
        rapport(await o.ev("getComputedStyle(document.getElementById('padFlyUp')).visibility") == "visible", "en vol : flèches monter et descendre")
        y0 = (await o.gw())["pos"][1]
        await mouse_hold(o, "padFlyUp", 500)
        y1 = (await o.gw())["pos"][1]
        rapport(y1 - y0 > 0.3, f"monter tenu : +{y1 - y0:.1f} m", [y0, y1])
        dg = await o.ev("""(async () => { document.getElementById('diagBtn').click(); await new Promise(r => setTimeout(r, 300)); return document.getElementById('diagOut').value; })()""")
        rapport("Commandes tactiles : non (réglage : auto" in dg, "diagnostic : ligne « Commandes tactiles »", dg[-400:])
        await o.ev("(() => { const s = document.getElementById('visTouch'); s.value = 'on'; s.onchange(); })()")
        rapport(await o.ev("document.body.classList.contains('touch') && !document.getElementById('tcol').hidden"), "réglage « Commandes tactiles : Oui » : mode tactile à la souris")
        await o.ev("(() => { const s = document.getElementById('visTouch'); s.value = 'auto'; s.onchange(); })()")
        rapport(not o.errs, "aucune erreur (ordinateur)", o.errs[:3])
        await o.ctx.close()

        print("--- 3. téléphone (écran tactile simulé, vrais gestes)")
        o = await Onglet(br).ouvrir(URL + "#name=Tom", **TEL)
        f = await Doigt(o).init()
        await o.pg.wait_for_timeout(300)
        st = await o.ev("({ touch: document.body.classList.contains('touch'), bar: getComputedStyle(document.getElementById('bar')).display, tcol: !document.getElementById('tcol').hidden, walk: document.getElementById('tWalk').textContent, chat: document.getElementById('tChat').hidden, fold: document.getElementById('stateHead').getAttribute('aria-expanded'), x: getComputedStyle(document.querySelector('#stateInfo .winX')).display, ls: localStorage.getItem('glb2html_stateFold'), pb: !document.getElementById('padBtn').getClientRects().length })")
        rapport(st["touch"] and st["bar"] == "none" and st["tcol"], "écran tactile détecté : colonne de boutons, barre cachée", st)
        rapport(st["walk"] == "Promenade" and st["chat"], "vue globale : « Promenade » ; pas de chat", st)
        rapport(st["fold"] == "false" and st["x"] == "block" and st["ls"] != "1", "fenêtres réduites à l'ouverture (sans changer le réglage retenu), ✕ visible", st)
        pr, sl, dk = await rect(o, "presence"), await rect(o, "statusLine"), await rect(o, "dock")
        rapport(sl[1] >= pr[3] and dk[1] >= sl[3], "ligne d'état sous le bloc du pseudo, fenêtres dessous", [pr, sl, dk])
        pd, tc = await rect(o, "pad"), await rect(o, "tcol")
        rapport(disjoint(pd, tc) and pd[2] - pd[0] >= 3 * 56, "flèches en grand, sans chevaucher la colonne", [pd, tc])
        await f.tap("tWalk")
        await o.pg.wait_for_function("window.__viewer.walking", timeout=10000)
        await o.attendre("window.__viewer.getPresence().state === 'online'", 30)
        await o.pg.wait_for_timeout(400)
        st = await o.ev("({ walk: document.getElementById('tWalk').textContent, chat: document.getElementById('tChat').hidden, jump: document.getElementById('tJump').hidden, toast: document.getElementById('toast').textContent })")
        rapport(st["walk"] == "Sortir" and not st["chat"] and not st["jump"], "en promenade : Sortir, Sauter, Chat", st)
        rapport("Glisse le doigt" in st["toast"], "bulle « Glisse le doigt… » à la première promenade", st["toast"])
        y0 = (await o.gw())["yaw"]
        sur = await o.ev("document.elementFromPoint(120, 560).tagName")   # un point libre de la scène (ni fenêtre, ni flèches, ni colonne)
        rapport(sur == "CANVAS", "le point de départ du glissé est sur la scène", sur)
        await f.glisser(120, 560, 100, 0)
        y1 = (await o.gw())["yaw"]
        rapport(y1 - y0 > 0.25, f"glisser le doigt vers la droite : le regard tourne à gauche ({y1 - y0:.2f} rad)", [y0, y1])
        g0 = await o.gw()
        await f.tenir("padUp", 700)
        g1 = await o.gw()
        rapport(dist_h(g0["pos"], g1["pos"]) > 0.5, "flèche tenue au doigt : l'avatar avance", [g0["pos"], g1["pos"]])
        v0 = await o.ev("window.__viewer.view")
        await f.tenir("tView", 700)
        await o.pg.wait_for_timeout(150)
        lp = await o.ev("({ v: window.__viewer.view, tip: document.getElementById('tipBox').hidden ? '' : document.getElementById('tipBox').textContent })")
        rapport(lp["v"] == v0 and "Changer de vue" in lp["tip"], "appui long : la bulle s'affiche, la vue ne change pas", lp)
        await f.tap("tView")
        rapport(await o.ev("window.__viewer.view") != v0, "appui court : la vue change")
        await f.tap("tMenu")
        mn = await o.ev("({ open: !document.getElementById('tmenu').hidden, ex: document.getElementById('tMenu').getAttribute('aria-expanded'), full: document.getElementById('mFull').hidden, fsok: !!(document.fullscreenEnabled || document.webkitFullscreenEnabled), center: document.getElementById('mCenter').hidden, home: document.getElementById('mHome').hidden })")
        rapport(mn["open"] and mn["ex"] == "true" and mn["full"] == (not mn["fsok"]) and mn["center"] and not mn["home"], "menu : ouvert, plein écran selon le navigateur, retour à l'arrivée", mn)
        await f.tap("mInfo")
        mi = await o.ev("({ menu: document.getElementById('tmenu').hidden, info: !document.getElementById('stateInfo').hidden && document.getElementById('stateHead').getAttribute('aria-expanded') })")
        rapport(mi["menu"] and mi["info"] == "true", "menu « Informations » : la fenêtre se déploie, le menu se ferme", mi)
        await f.tap("tChat")
        await o.pg.wait_for_timeout(200)
        ch = await o.ev("({ inp: !document.getElementById('chatInput').hidden, foc: document.activeElement && document.activeElement.id, cls: document.body.classList.contains('chatOpen'), pad: getComputedStyle(document.getElementById('pad')).display, ct: !document.getElementById('chatTouch').hidden })")
        rapport(ch["inp"] and ch["foc"] == "chatInput" and ch["cls"] and ch["pad"] == "none" and ch["ct"], "bouton Chat : vrai champ de saisie (focus), Envoyer / Fermer, flèches masquées", ch)
        await o.pg.fill("#chatInput", "bonjour du tel")
        await f.tap("chatSend")
        await o.attendre("[...document.getElementById('chatLog').children].some(e => e.textContent.includes('bonjour du tel'))", 10)
        rapport(await o.ev("document.getElementById('chatInput').value === '' && !document.getElementById('chatInput').hidden"), "Envoyer : message parti, saisie restée ouverte")
        await f.tap("chatClose")
        rapport(await o.ev("document.getElementById('chatInput').hidden && !document.body.classList.contains('chatOpen') && getComputedStyle(document.getElementById('pad')).display !== 'none'"), "Fermer : saisie fermée, flèches revenues")
        await o.ev("document.querySelector('#stateInfo .winX').click()")
        rapport(await o.ev("document.getElementById('stateInfo').hidden && localStorage.getItem('glb2html_state') === '0'"), "✕ : la fenêtre se ferme (retenu)")
        rapport(not o.errs, "aucune erreur (téléphone)", o.errs[:3])
        await o.ctx.close()

        print("--- 4. à l'horizontale, tablette, anglais")
        for vp, cols in (({"width": 844, "height": 390}, 3), ({"width": 1180, "height": 820}, 2)):
            o = await Onglet(br).ouvrir(URL, viewport=vp, has_touch=True, is_mobile=True)
            await o.walk(); await o.pg.wait_for_timeout(300)
            n = await o.ev("getComputedStyle(document.getElementById('tcol')).gridTemplateColumns.split(' ').length")
            pd, tc, sl = await rect(o, "pad"), await rect(o, "tcol"), await rect(o, "statusLine")
            rapport(n == cols and disjoint(pd, tc) and disjoint(pd, sl) and disjoint(tc, sl), f"{vp['width']} x {vp['height']} : colonne sur {cols} colonnes, rien ne se chevauche", [n, pd, tc, sl])
            rapport(not o.errs, f"aucune erreur ({vp['width']} x {vp['height']})", o.errs[:3])
            await o.ctx.close()
        o = await Onglet(br).ouvrir(URL + "#lang=en", viewport={"width": 1440, "height": 900}, locale="en-US")
        en = await o.ev("({ s: document.getElementById('statusLine').textContent, b: document.getElementById('padBtn').textContent, t: document.getElementById('padFwd').title, sl: document.getElementById('padSideL').title })")
        rapport(en["s"].startswith("Overview") and en["b"] == "Arrows (K)" and "Hold" in en["t"] and en["sl"].startswith("Step left ("), "anglais", en)
        await o.ctx.close()
        await br.close()


try:
    asyncio.run(main())
finally:
    http.kill(); pres.kill()
n = resultat()
print("\nRÉSULTAT : " + ("tout est passé" if not n else f"{n} échec(s)"))
sys.exit(1 if n else 0)
