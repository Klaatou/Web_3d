#!/usr/bin/env python3
"""Tests v35 : aide en groupes et panneaux repliables, commandes à la Firestorm (F / P / E / Page Haut / C / course / M / Ctrl+M / Alt / Fin),
vol par appui long, troisième personne (caméra qui orbite, avatar qui se tourne vers sa marche, orientation transmise), distance des infobulles
de zones, copie dans le presse-papiers sans contexte sécurisé, glb2html.py --maj avec la carte des mondes.

Pages ouvertes dans Chromium sans tête (sol plat synthétique, coquille commune, vrai presence_server.py). Le verrouillage du pointeur est simulé.

Prérequis : pip install playwright websockets ; python build.py avant.
Variables facultatives : THREE_DIR (paquet npm three, hors ligne), CHROMIUM (chemin de l'exécutable).
Lancer : python tests/v35.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"   # outils Python en français (v36)
import asyncio, json, math, os, pathlib, re, shutil, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
import glbfab

DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_v35_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)), flush=True)


def run(script, *a, cwd=None, ok=True):
    r = subprocess.run([sys.executable, str(script), *map(str, a)], capture_output=True, text=True, cwd=cwd or tmp)
    if ok and r.returncode:
        sys.exit(f"[ECHEC] {script.name} {' '.join(map(str, a))}\n{r.stdout}{r.stderr}")
    return r


def html(*a, ok=True, cwd=None):
    return run(DIST / "glb2html.py", *a, *vend, ok=ok, cwd=cwd)


def port_libre():
    with socket.socket() as so:
        so.bind(("127.0.0.1", 0))
        return so.getsockname()[1]


def attendre_port(port, proc, nom):
    for _ in range(80):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return
        except OSError:
            time.sleep(0.1)
    proc.kill()
    sys.exit(f"[ECHEC] {nom} ne démarre pas")


def serveur(dossier):
    port = port_libre()
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=dossier, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    attendre_port(port, proc, "http.server")
    return proc, port


def lancer_presence():
    port = port_libre()
    proc = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--host", "127.0.0.1", "--port", str(port), "--identities", ""],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=tmp)
    attendre_port(port, proc, "presence_server")
    return proc, port


def sol_glb(path):
    pos = struct.pack("<12f", -20, 0, -20, 20, 0, -20, 20, 0, 20, -20, 0, 20)
    blob = pos + struct.pack("<6H", 0, 2, 1, 0, 3, 2) + b"\0\0"
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-20, 0, -20], "max": [20, 0, 20]},
                       {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def ecart(a, b):
    """écart angulaire en radians, entre 0 et pi"""
    d = (a - b) % (2 * math.pi)
    return min(d, 2 * math.pi - d)


FLOOR = 15   # le cadrage relève le sol de la région synthétique à 15 m


# ---------- fabrication ----------
print("--- 0. fabrication des pages")
presence, pport = lancer_presence()
PURL = f"ws://127.0.0.1:{pport}"
site = tmp / "site"
site.mkdir()
sol_glb(site / "sol.glb")
ZL = [
    {"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0.0},
    {"id": "lien", "type": "url", "label": "Lien test", "target": "https://example.org/", "x": 0, "y": 15, "z": -14, "radius": 3},
    {"id": "dist", "type": "url", "label": "Zone D", "target": "https://example.org/d", "x": 0, "y": 15, "z": -4.2, "radius": 4},
    {"id": "pres", "type": "url", "label": "Zone au sol", "target": "https://example.org/p", "x": 10, "y": 15, "z": 10, "radius": 3},
    {"id": "porte", "type": "portal", "label": "Portail entrée", "target": "", "spawn": "default", "x": -10, "y": 15, "z": 10, "radius": 2, "trigger": "enter"},
    {"id": "nomProche", "type": "url", "label": "Nom proche", "target": "https://example.org/n1", "x": 0, "y": 15, "z": 30, "radius": 2, "showName": True},
    {"id": "nomLoin", "type": "url", "label": "Nom loin", "target": "https://example.org/n2", "x": 0, "y": 15, "z": -60, "radius": 2, "showName": True},
]
(tmp / "z.json").write_text(json.dumps(ZL), encoding="utf-8")
base = ["--shared-shell", "--zones", tmp / "z.json", "--no-sea", "--target", "0,0,0", "--presence-url", PURL, "--room", "t35", *vend]
html(site / "sol.glb", "-o", site / "Portee.html", *base, "--zone-marker", "portee", "--register", site / "regions.json", "--region-name", "Test 35", "--map-page", "carte.html")
html(site / "sol.glb", "-o", site / "Discret.html", *base)
html(site / "sol.glb", "-o", site / "NoFly.html", *base, "--no-fly")
html(site / "sol.glb", "-o", site / "Court.html", *base, "--zone-info-dist", "10", "--zone-marker", "portee")
html(site / "sol.glb", "-o", site / "Long.html", *base, "--zone-info-dist", "60", "--zone-marker", "portee")
for nom, val in (("Haut", "500"), ("Bas", "1")):
    html(site / "sol.glb", "-o", site / f"Borne{nom}.html", *base, "--zone-info-dist", val)
rapport(True, "pages générées (portée, discret, sans vol, distance 10, bornes)")

STUB = """(() => {
  let el = null; window.__plCalls = 0;
  Object.defineProperty(document, 'pointerLockElement', { get: () => el, configurable: true });
  Element.prototype.requestPointerLock = function () { window.__plCalls++; el = this; setTimeout(() => document.dispatchEvent(new Event('pointerlockchange')), 0); };
  document.exitPointerLock = () => { el = null; setTimeout(() => document.dispatchEvent(new Event('pointerlockchange')), 0); };
  window.__open = []; window.open = (u) => { window.__open.push(u); return null; };
  window.__sent = []; const s = WebSocket.prototype.send;
  WebSocket.prototype.send = function (d) { try { window.__sent.push(JSON.parse(d)); } catch (e) {} return s.call(this, d); };
})();"""


class Onglet:
    def __init__(self, br):
        self.br, self.errs = br, []

    async def ouvrir(self, url, init=STUB, ctx=None, viewer=True):
        self.ctx = ctx or await self.br.new_context(locale="fr-FR", viewport={"width": 1000, "height": 700})
        if init:
            await self.ctx.add_init_script(init)
        self.pg = await self.ctx.new_page()
        self.pg.on("pageerror", lambda e: self.errs.append(str(e)))
        self.pg.on("console", lambda m: self.errs.append("console.error " + m.text) if m.type == "error" and "WebSocket" not in m.text and "404" not in m.text else None)
        await self.pg.goto(url)
        if viewer:
            await self.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
        return self

    async def ev(self, js, arg=None):
        return await self.pg.evaluate(js, arg)

    async def walk(self, pos=(0, 0, 0), yaw=0):
        await self.ev("([p, y]) => window.__viewer.walkStart({ pos: p, yaw: y })", [list(pos), yaw])
        await self.pg.wait_for_function("window.__viewer.walking", timeout=10000)

    async def gw(self):
        return await self.ev("window.__viewer.getWalk()")

    async def key(self, type_, code, **mods):
        return await self.ev("([t, c, m]) => window.dispatchEvent(new KeyboardEvent(t, Object.assign({ code: c, cancelable: true, bubbles: true }, m)))", [type_, code, mods])

    async def touche(self, code, **mods):
        await self.key("keydown", code, **mods)
        await self.key("keyup", code, **mods)

    async def ticks(self, n, dt=0.05):
        return await self.ev("([n, dt]) => { const v = window.__viewer; for (let i = 0; i < n; i++) v.walkTick(dt); return v.getWalk(); }", [n, dt])

    async def tenir(self, touches, n, dt=0.1):
        return await self.ev("""([keys, n, dt]) => { const v = window.__viewer, out = [], k = (t, c) => window.dispatchEvent(new KeyboardEvent(t, { code: c }));
            keys.forEach(c => k('keydown', c));
            for (let i = 0; i < n; i++) { v.walkTick(dt); const w = v.getWalk(); out.push({ pos: w.pos, flying: w.flying, grounded: w.grounded, running: w.running }); }
            keys.forEach(c => k('keyup', c));
            return out; }""", [touches, n, dt])

    async def txt(self, ident):
        return await self.ev("(i) => document.getElementById(i).textContent", ident)

    async def souris(self, dx, dy):
        await self.ev("""([dx, dy]) => { const c = window.__viewer.renderer.domElement;
            c.dispatchEvent(new MouseEvent('mousedown', { bubbles: true })); window.dispatchEvent(new MouseEvent('mousemove', { movementX: dx, movementY: dy }));
            window.dispatchEvent(new MouseEvent('mouseup')); }""", [dx, dy])


async def tip(pg):
    return await pg.evaluate("(() => { const e = document.getElementById('zoneTip'); return e && !e.hidden ? e.innerText : null; })()")


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        proc, port = serveur(site)
        base_url = f"http://127.0.0.1:{port}/index.html?region="
        try:
            # ================= 1. aide en groupes, panneaux repliables =================
            print("--- 1. aide en groupes, panneaux repliables")
            o = await Onglet(br).ouvrir(base_url + "Discret")
            rapport(await o.txt("walkBtn") == "Promenade (P)" and await o.ev("!document.getElementById('walkBtn').hidden"), "vue globale : bouton « Promenade (P) »", await o.txt("walkBtn"))
            glob = await o.ev("[...document.querySelectorAll('#helpBody .grp b')].map(b => b.textContent)")
            rapport("Vue globale" in glob and "Promenade" in glob, "vue globale : groupes de l'aide", glob)
            await o.walk()
            titres = await o.ev("[...document.querySelectorAll('#helpBody .grp b')].map(b => b.textContent)")
            rapport(titres[:4] == ["Déplacement", "Vol", "Vue", "Souris"] and "Chat" in titres and "Zones" in titres and titres[-1] == "Page", "promenade : groupes Déplacement, Vol, Vue, Souris, Chat, Zones, Page", titres)
            aide = await o.txt("helpBody")
            rapport("Ctrl+C" not in aide and "sélectionnable" not in aide and "Ctrl+C copie" not in aide, "plus de mention « Ctrl+C copie » ni d'explication de la sélection", aide[:500])
            rapport(all(s in aide for s in ("Début : voler / atterrir", "Page Haut ou Espace maintenu", "Page Bas ou C", "Maj ou double appui", "M : subjective / 3e personne", "Alt + glisser", "Fin ou Alt + clic", "P ou F : quitter la promenade")), "l'aide donne les touches Firestorm", aide[:900])
            rapport(await o.ev("document.getElementById('walkBtn').hidden"), "en promenade : plus de bouton « Quitter la promenade »")
            rapport("Quitter la promenade (F)" not in await o.ev("document.body.innerText"), "le texte « Quitter la promenade (F) » n'existe plus")
            r = await o.ev("() => { const e = document.querySelector('#helpBody .grp'), b = e.getBoundingClientRect(); return [b.left + 40, b.top + b.height / 2]; }")
            await o.pg.mouse.click(r[0], r[1], click_count=3)
            sel = await o.ev("window.getSelection().toString()")
            rapport(len(sel.strip()) > 8, "le texte de l'aide reste sélectionnable", sel)
            # replier / déplier
            for tete, corps, nom in (("helpHead", "helpBody", "aide"), ("stateHead", "stateBody", "état")):
                rapport(await o.ev("(c) => !document.getElementById(c).hidden", corps), f"{nom} : dépliée au départ")
                await o.pg.click("#" + tete)
                rapport(await o.ev("([t, c]) => document.getElementById(c).hidden && document.getElementById(t).getAttribute('aria-expanded') === 'false' && document.getElementById(t).textContent.startsWith('▸')", [tete, corps]), f"{nom} : un clic sur le titre la replie (flèche et aria-expanded, pas de couleur)")
            rapport(await o.ev("!document.getElementById('walkHint').hidden && !document.getElementById('stateInfo').hidden"), "repliés, les panneaux restent là (seul le titre)")
            await o.pg.reload()
            await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            await o.walk()
            rapport(await o.ev("document.getElementById('helpBody').hidden && document.getElementById('stateBody').hidden"), "l'état replié est mémorisé après rechargement")
            await o.pg.click("#helpHead")
            await o.pg.click("#stateHead")
            rapport(await o.ev("!document.getElementById('helpBody').hidden && !document.getElementById('stateBody').hidden"), "un second clic les déplie")
            await o.pg.reload()
            await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            await o.walk()
            rapport(await o.ev("!document.getElementById('helpBody').hidden && !document.getElementById('stateBody').hidden"), "dépliés : mémorisé aussi")
            await o.touche("KeyH")
            rapport(await o.ev("document.getElementById('walkHint').hidden && !document.getElementById('stateInfo').hidden"), "H masque l'aide entière")
            await o.touche("KeyI")
            rapport(await o.ev("document.getElementById('stateInfo').hidden"), "I masque l'état entier")
            await o.touche("KeyI"); await o.touche("KeyH")
            rapport(not o.errs, "aucune erreur JavaScript", o.errs)
            await o.ctx.close()

            # ================= 2. commandes à la Firestorm =================
            print("--- 2. commandes à la Firestorm")
            o = await Onglet(br).ouvrir(base_url + "Portee")
            # F entre en promenade en vue globale ; P entre / sort
            await o.touche("KeyF")
            await o.pg.wait_for_function("window.__viewer.walking", timeout=10000)
            rapport(True, "vue globale : F entre en promenade")
            await o.touche("KeyP")
            rapport(not await o.ev("window.__viewer.walking"), "P sort de la promenade")
            await o.touche("KeyP")
            rapport(await o.ev("window.__viewer.walking"), "P entre en promenade")
            rapport("Ctrl+M : carte des mondes" in await o.txt("helpBody"), "l'aide d'une page avec carte donne « Ctrl+M : carte des mondes »")
            await o.touche("KeyF")
            rapport(not await o.ev("window.__viewer.walking"), "en promenade : F sort de la promenade (v36 : F ne fait plus basculer le vol)")
            await o.touche("KeyF")
            rapport(await o.ev("window.__viewer.walking"), "F entre de nouveau")
            await o.touche("Home")
            w = await o.gw()
            rapport(w["flying"] and await o.txt("modeInfo") == "Mode : en vol", "Début : vole", w)
            await o.touche("Home")
            rapport(not (await o.gw())["flying"] and await o.txt("modeInfo") == "Mode : à pied", "Début de nouveau : atterrir")
            await o.touche("Home")
            rapport((await o.gw())["flying"], "Début bascule aussi le vol")
            await o.touche("Home")
            rapport(not (await o.gw())["flying"], "Début de nouveau : atterrir")
            # F avec Ctrl : pas d'effet
            await o.touche("KeyF", ctrlKey=True)
            rapport(not (await o.gw())["flying"], "Ctrl+F n'est pas intercepté")
            await o.ev("window.__viewer.teleportTo([0, 0, 0], 0)")
            await o.ticks(20)
            # appui bref sur Page Haut = saut, sans décollage (v36 : E ne saute plus)
            for code in ("PageUp",):
                await o.ticks(30, 0.05)
                out = await o.tenir([code], 3, 0.1)
                haut = max(s["pos"][1] for s in out)
                rapport(haut > FLOOR + 0.05 and not out[-1]["flying"] and not out[-1]["grounded"], f"{code} bref (0,3 s) : saut, pas de décollage", out[-1])
                out2 = await o.tenir([], 30, 0.1)
                rapport(out2[-1]["grounded"] and not out2[-1]["flying"] and abs(out2[-1]["pos"][1] - FLOOR) < 0.05, f"{code} bref : l'avatar retombe", out2[-1])
            # maintenu plus de 0,4 s au sol = décollage + montée
            for code in ("PageUp",):
                await o.ticks(30, 0.05)
                out = await o.tenir([code], 14, 0.1)
                rapport(out[-1]["flying"] and await o.txt("modeInfo") == "Mode : en vol", f"{code} maintenu 1,4 s au sol : décollage, « Mode : en vol »", out[-1])
                rapport(out[-1]["pos"][1] > out[6]["pos"][1] + 0.5 and out[-1]["pos"][1] > FLOOR + 2, f"{code} maintenu : l'altitude monte (y = {out[-1]['pos'][1]:.1f} m)", [s["pos"][1] for s in out])
                # C maintenu : descente puis atterrissage automatique
                out = await o.tenir(["KeyC"], 80, 0.1)
                rapport(not out[-1]["flying"] and out[-1]["grounded"] and abs(out[-1]["pos"][1] - FLOOR) < 0.05, f"C maintenu : descend et atterrit tout seul (après {code})", out[-1])
            # Page Bas aussi
            await o.key("keydown", "Home"); await o.key("keyup", "Home")
            await o.tenir(["PageUp"], 8, 0.1)
            out = await o.tenir(["PageDown"], 80, 0.1)
            rapport(not out[-1]["flying"] and out[-1]["grounded"], "Page Bas maintenu : descend et atterrit")
            # sans vol (--no-fly) : maintenu, pas de décollage
            o2 = await Onglet(br).ouvrir(base_url + "NoFly")
            await o2.walk()
            out = await o2.tenir(["PageUp"], 14, 0.1)
            rapport(not out[-1]["flying"] and await o2.ev("document.getElementById('flyBtn').hidden"), "--no-fly : Page Haut maintenu ne décolle pas, pas de bouton de vol")
            await o2.touche("Home")
            rapport(not (await o2.gw())["flying"], "--no-fly : Début ne fait pas voler")
            await o2.ctx.close()
            # course par double appui
            await o.ev("window.__viewer.teleportTo([0, 0, 15], 0)")
            await o.ticks(30)
            simple = await o.tenir(["KeyW"], 3, 0.1)
            pas_simple = math.hypot(simple[2]["pos"][0] - simple[1]["pos"][0], simple[2]["pos"][2] - simple[1]["pos"][2])
            rapport(not simple[-1]["running"], "un seul appui sur W : pas de course")
            await o.ev("window.__viewer.teleportTo([0, 0, 15], 0)")
            await o.ticks(30)
            await o.key("keydown", "KeyW"); await o.key("keyup", "KeyW")
            await o.pg.wait_for_timeout(120)
            await o.key("keydown", "KeyW")
            out = await o.ev("() => { const v = window.__viewer, o = []; for (let i = 0; i < 3; i++) { v.walkTick(0.1); const w = v.getWalk(); o.push({ pos: w.pos, running: w.running }); } return o; }")
            await o.key("keyup", "KeyW")
            pas_course = math.hypot(out[2]["pos"][0] - out[1]["pos"][0], out[2]["pos"][2] - out[1]["pos"][2])
            rapport(out[-1]["running"] and pas_course > pas_simple * 2, f"double appui rapide sur W (120 ms) : course ({pas_course:.2f} m par pas contre {pas_simple:.2f})", (out, pas_simple))
            await o.ticks(2)
            rapport(not (await o.gw())["running"], "touche relâchée : la course s'arrête")
            await o.ev("window.__viewer.teleportTo([0, 0, 15], 0)")
            await o.ticks(30)
            await o.key("keydown", "ArrowUp"); await o.key("keyup", "ArrowUp")
            await o.pg.wait_for_timeout(450)
            await o.key("keydown", "ArrowUp")
            w = await o.ticks(2, 0.1)
            await o.key("keyup", "ArrowUp")
            rapport(not w["running"], "deux appuis à plus de 300 ms : pas de course (↑)")
            await o.key("keydown", "ArrowDown"); await o.key("keyup", "ArrowDown")
            await o.pg.wait_for_timeout(100)
            await o.key("keydown", "ArrowDown")
            w = await o.ticks(2, 0.1)
            await o.key("keyup", "ArrowDown")
            rapport(w["running"], "double appui rapide sur ↓ : course")
            await o.key("keydown", "KeyA"); await o.key("keyup", "KeyA")
            await o.pg.wait_for_timeout(100)
            await o.key("keydown", "KeyA")
            w = await o.ticks(2, 0.1)
            await o.key("keyup", "KeyA")
            rapport(not w["running"], "double appui sur A : pas de course (réservé à W, S, ↑, ↓)")
            sh = await o.tenir(["ShiftLeft", "KeyW"], 2, 0.1)
            rapport(sh[-1]["running"], "Maj reste une course")
            # M : bascule subjective / troisième personne ; Ctrl+M : carte
            await o.touche("KeyM", key="m")
            rapport(await o.ev("window.__viewer.view") == "tps" and not await o.ev("document.getElementById('mapOverlay').hidden === false"), "en promenade : M passe à la troisième personne, sans ouvrir la carte")
            await o.touche("KeyM", key="m")
            rapport(await o.ev("window.__viewer.view") == "fps", "M de nouveau : vue subjective")
            await o.touche("KeyV")
            rapport(await o.ev("window.__viewer.view") == "tps", "V fait toujours tourner les vues")
            await o.touche("KeyV"); await o.touche("KeyV")
            rapport(await o.ev("window.__viewer.view") == "fps", "V : subjective -> 3e personne -> libre -> subjective")
            await o.touche("KeyM", key="m", ctrlKey=True)
            rapport(not await o.ev("document.getElementById('mapOverlay').hidden"), "Ctrl+M ouvre la carte des mondes en promenade")
            rapport(await o.ev("window.__viewer.view") == "fps", "Ctrl+M ne change pas la vue")
            await o.touche("KeyM", key="m", ctrlKey=True)
            rapport(await o.ev("document.getElementById('mapOverlay').hidden"), "Ctrl+M la referme")
            await o.touche("KeyP")
            rapport(not await o.ev("window.__viewer.walking"), "P : retour en vue globale")
            await o.touche("KeyM", key="m")
            rapport(not await o.ev("document.getElementById('mapOverlay').hidden"), "hors promenade : M ouvre la carte des mondes (comportement conservé)")
            await o.touche("KeyM", key="m")
            rapport(await o.ev("document.getElementById('mapOverlay').hidden"), "M la referme")
            await o.touche("KeyM", key="m", ctrlKey=True)
            rapport(not await o.ev("document.getElementById('mapOverlay').hidden"), "hors promenade, Ctrl+M ouvre aussi la carte")
            await o.touche("KeyM", key="m", ctrlKey=True)
            rapport(await o.ev("document.getElementById('mapBtn').textContent") == "Carte (M)", "bouton « Carte (M) » hors promenade")
            # v36 : E déclenche de nouveau la zone proche ; l'entrée dans un portail « enter » les déclenche toujours
            await o.walk((10, 0, 10), 0)
            await o.ticks(5)
            await o.ev("window.__open.length = 0")
            near = await o.ev("(() => { const e = document.getElementById('zonePrompt'); return e && !e.hidden ? e.textContent : null; })()")
            rapport(near is not None and near.startswith("clic ou E :"), "près d'une zone : l'invite dit « clic ou E : … »", near)
            await o.touche("KeyE")
            await o.ticks(5)
            ouvert = await o.ev("window.__open.length")
            toast = await o.ev("(() => { const e = document.getElementById('toast'); return e && !e.hidden ? e.textContent : ''; })()")
            rapport(ouvert == 1 and "Ouverture" in toast, "E près d'une zone de lien : le lien s'ouvre (v36)", (ouvert, toast))
            await o.ev("window.__viewer.teleportTo([-10, 0, 13.6], 0)")
            await o.ticks(5)
            await o.tenir(["KeyW"], 8, 0.1)   # on marche jusque dans le rayon du portail
            await o.pg.wait_for_timeout(1200)
            w = await o.gw()
            rapport(math.hypot(w["pos"][0], w["pos"][2]) < 1.0, "entrer dans le rayon d'un portail « enter » le déclenche (retour à l'arrivée)", w["pos"])
            await o.ctx.close()

            # ================= 3. troisième personne =================
            print("--- 3. troisième personne : caméra qui orbite, avatar qui se tourne vers sa marche")
            o = await Onglet(br).ouvrir(base_url + "Discret")
            await o.walk((0, 0, 0), 0)
            await o.touche("KeyM", key="m")
            w = await o.gw()
            rapport(w["view"] == "tps" and ecart(w["camYaw"], w["yaw"]) < 1e-6 and w["cam"][2] > 3, "3e personne : la caméra est derrière l'avatar", w)
            await o.pg.wait_for_timeout(500)
            n0 = await o.ev("window.__sent.filter(m => m.t === 'pos').length")
            await o.souris(-math.pi / 0.0022, 0)
            await o.ticks(2)
            w = await o.gw()
            rapport(ecart(w["camYaw"], math.pi) < 0.02 and ecart(w["yaw"], 0) < 1e-6, "la souris fait tourner la caméra de 180° sans tourner l'avatar", (w["camYaw"], w["yaw"]))
            rapport(w["cam"][2] < -3, "la caméra est maintenant devant l'avatar : on voit son devant", w["cam"])
            await o.pg.wait_for_timeout(600)
            msgs = await o.ev("window.__sent.filter(m => m.t === 'pos')")
            rapport(len(msgs) >= 1 and all(ecart(m["yaw"], 0) < 0.02 for m in msgs), f"orientation transmise : inchangée après 180° de caméra ({len(msgs)} message(s))", msgs[-3:])
            # la marche avant va dans la direction de la caméra
            z0 = (await o.gw())["pos"][2]
            s1 = await o.tenir(["KeyW"], 1, 0.05)
            w1 = await o.gw()
            rapport(0 < ecart(w1["yaw"], 0) < math.pi - 0.1, "marche : l'avatar commence à se tourner, sans sauter à la nouvelle orientation (lissage)", w1["yaw"])
            await o.tenir(["KeyW"], 30, 0.05)
            w = await o.gw()
            rapport(w["pos"][2] > z0 + 3 and ecart(w["yaw"], math.pi) < 0.1, f"W avance dans la direction de la caméra (z : {z0:.1f} -> {w['pos'][2]:.1f}) et l'avatar se tourne dedans", (w["pos"], w["yaw"]))
            rapport(ecart(w["camYaw"], math.pi) < 0.02, "la caméra, elle, n'a pas bougé")
            await o.pg.wait_for_timeout(600)
            msgs = await o.ev("window.__sent.filter(m => m.t === 'pos')")
            rapport(any(ecart(m["yaw"], math.pi) < 0.15 for m in msgs), "l'orientation transmise suit alors la marche", msgs[-3:])
            # à l'arrêt, l'avatar garde son orientation
            y1 = (await o.gw())["yaw"]
            await o.souris(500, 100)
            await o.ticks(20)
            w = await o.gw()
            rapport(ecart(w["yaw"], y1) < 1e-6 and ecart(w["camYaw"], math.pi) > 0.5, "à l'arrêt : la caméra tourne, l'avatar garde son orientation")
            # Alt + clic et Fin recentrent derrière l'avatar
            await o.ev("""() => { const c = window.__viewer.renderer.domElement;
                c.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, altKey: true })); window.dispatchEvent(new MouseEvent('mouseup'));
                c.dispatchEvent(new MouseEvent('click', { bubbles: true, altKey: true })); }""")
            w = await o.gw()
            rapport(ecart(w["camYaw"], w["yaw"]) < 1e-6, "Alt + clic : la caméra revient derrière l'avatar", (w["camYaw"], w["yaw"]))
            await o.souris(-300, 0)
            rapport(ecart((await o.gw())["camYaw"], (await o.gw())["yaw"]) > 0.3, "(la caméra a de nouveau tourné)")
            await o.ev("""() => { const c = window.__viewer.renderer.domElement;
                c.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, altKey: true })); window.dispatchEvent(new MouseEvent('mousemove', { movementX: 40, movementY: 0, altKey: true }));
                window.dispatchEvent(new MouseEvent('mouseup')); c.dispatchEvent(new MouseEvent('click', { bubbles: true, altKey: true })); }""")
            w = await o.gw()
            rapport(ecart(w["camYaw"], w["yaw"]) > 0.1, "Alt + glisser orbite sans recentrer à la fin du geste")
            await o.touche("End")
            w = await o.gw()
            rapport(ecart(w["camYaw"], w["yaw"]) < 1e-6, "Fin : la caméra revient derrière l'avatar")
            # marcher vers la gauche : l'orientation change, la caméra non
            await o.walk((0, 0, 0), 0) if not await o.ev("window.__viewer.walking") else None
            await o.ev("window.__viewer.teleportTo([0, 0, 0], 0)")
            await o.ticks(20)
            await o.touche("End")
            await o.pg.wait_for_timeout(500)
            avant = await o.ev("window.__sent.filter(m => m.t === 'pos').length")
            c0 = (await o.gw())["camYaw"]
            out = await o.tenir(["KeyA"], 30, 0.05)
            w = await o.gw()
            rapport(ecart(w["yaw"], math.pi / 2) < 0.1 and ecart(w["camYaw"], c0) < 1e-6, "A (vers la gauche de la caméra) : l'avatar se tourne vers la gauche, la caméra reste", (w["yaw"], w["camYaw"]))
            await o.pg.wait_for_timeout(600)
            msgs = await o.ev("window.__sent.filter(m => m.t === 'pos')")
            rapport(any(ecart(m["yaw"], math.pi / 2) < 0.15 for m in msgs[avant:]), "marcher vers la gauche change l'orientation transmise", msgs[-3:])
            # vue subjective inchangée : la souris tourne la vue et l'avatar (même yaw)
            await o.touche("KeyM", key="m")
            await o.souris(-200, 0)
            w = await o.gw()
            rapport(w["view"] == "fps" and ecart(w["camYaw"], w["yaw"]) < 1e-6, "vue subjective : la souris tourne la vue (inchangé)")
            # caméra libre : inchangée
            await o.touche("KeyV"); await o.touche("KeyV")
            w = await o.gw()
            rapport(w["view"] == "free", "V atteint la caméra libre")
            await o.touche("KeyV")
            rapport(await o.ev("window.__viewer.view") == "fps" and await o.ev("window.__viewer.walking"), "en caméra libre, V rend la main à l'avatar (v36 : F sort de la promenade)")
            rapport(not o.errs, "aucune erreur JavaScript", o.errs)
            await o.ctx.close()

            # ================= 3 bis. molette, caméra libre =================
            print("--- 3 bis. molette, vitesse et orbite de la caméra libre")
            o = await Onglet(br).ouvrir(base_url + "Discret")
            await o.walk((0, 0, 0), 0)
            DIST_AV = """() => { const w = window.__viewer.getWalk(); return Math.hypot(w.cam[0] - w.pos[0], w.cam[1] - (w.pos[1] + 1.7), w.cam[2] - w.pos[2]); }"""
            WHEEL = """(d) => { const e = new WheelEvent('wheel', { deltaY: d, bubbles: true, cancelable: true }); window.__viewer.renderer.domElement.dispatchEvent(e); return e.defaultPrevented; }"""
            prev = await o.ev(WHEEL, 100)
            w = await o.gw()
            rapport(prev and w["view"] == "fps" and ecart(w["camYaw"], 0) < 1e-6, "vue subjective : la molette ne fait rien, mais la page ne défile pas (preventDefault)")
            await o.touche("KeyM", key="m")
            w = await o.gw()
            rapport(abs(w["tpsDist"] - 4) < 1e-6 and abs(await o.ev(DIST_AV) - 4) < 0.05, "3e personne : distance par défaut 4 m", (w["tpsDist"], await o.ev(DIST_AV)))
            await o.ev(WHEEL, 100)
            d1 = (await o.gw())["tpsDist"]
            await o.ev(WHEEL, 100)
            d2 = (await o.gw())["tpsDist"]
            rapport(d1 > 4 and d2 > d1 and abs(await o.ev(DIST_AV) - d2) < 0.1, f"3e personne : la molette éloigne la caméra (4 -> {d1:.2f} -> {d2:.2f} m)")
            for _ in range(60):
                await o.ev(WHEEL, 100)
            rapport((await o.gw())["tpsDist"] <= 30.0001, "3e personne : la distance reste au plus 30 m", (await o.gw())["tpsDist"])
            for _ in range(120):
                await o.ev(WHEEL, -100)
            rapport(abs((await o.gw())["tpsDist"] - 1) < 1e-6, "3e personne : la distance reste au moins 1 m")
            await o.ev(WHEEL, 100); await o.ev(WHEEL, 100)
            m = await o.ev("localStorage.getItem('glb2html_tpsDist')")
            rapport(m is not None and abs(float(m) - (await o.gw())["tpsDist"]) < 1e-6, "la distance est mémorisée dans le navigateur", m)
            await o.pg.reload()
            await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            await o.walk((0, 0, 0), 0)
            await o.touche("KeyM", key="m")
            rapport(abs((await o.gw())["tpsDist"] - float(m)) < 1e-6, "elle est relue après rechargement")
            await o.touche("End")
            w = await o.gw()
            rapport(abs(w["tpsDist"] - 4) < 1e-6 and abs(await o.ev(DIST_AV) - 4) < 0.05, "Fin à la 3e personne : distance par défaut, derrière l'avatar", w["tpsDist"])
            # caméra libre
            await o.touche("KeyV")
            w = await o.gw()
            rapport(w["view"] == "free", "V : caméra libre")
            c0 = await o.ev(DIST_AV)
            await o.ev(WHEEL, 100)
            c1 = await o.ev(DIST_AV)
            await o.ev(WHEEL, 100)
            c2 = await o.ev(DIST_AV)
            rapport(c1 > c0 + 0.4 and c2 > c1 + 0.4, f"caméra libre : un cran recule, deux crans reculent davantage ({c0:.2f} -> {c1:.2f} -> {c2:.2f} m)")
            await o.ev(WHEEL, -100)
            c3 = await o.ev(DIST_AV)
            rapport(c3 < c2 - 0.4, "caméra libre : molette dans l'autre sens, on avance")
            for _ in range(40):
                await o.ev(WHEEL, 100)
            hh = (await o.gw())["cam"][1]
            for _ in range(80):
                await o.ev(WHEEL, -100)
            rapport((await o.gw())["cam"][1] >= FLOOR + 0.3 - 1e-6, "caméra libre : jamais sous le sol", (await o.gw())["cam"])
            # pas : proportionnel, 20 m au plus par cran
            await o.touche("End")
            for _ in range(30):
                await o.ev(WHEEL, 100)
            ca = await o.ev(DIST_AV)
            await o.ev(WHEEL, 100)
            cb = await o.ev(DIST_AV)
            rapport(0.5 <= cb - ca <= 20.0001 and cb - ca > 5, f"caméra libre : pas proportionnel à la distance ({cb - ca:.2f} m à {ca:.1f} m), au plus 20 m")
            # vitesse des touches
            await o.touche("End")
            for _ in range(20):
                await o.ev(WHEEL, 100)
            dd = await o.ev(DIST_AV)
            p0 = (await o.gw())["cam"]
            await o.tenir(["KeyW"], 1, 0.1)
            p1 = (await o.gw())["cam"]
            v = math.dist(p0, p1) / 0.1
            rapport(abs(v - min(60, 0.5 * dd)) < 0.5 * dd * 0.1 + 0.3 and v > 3.5 * 2, f"caméra libre : vitesse des touches = 0,5 x distance ({v:.1f} m/s pour {dd:.1f} m)", (v, dd))
            p0 = (await o.gw())["cam"]
            await o.tenir(["ShiftLeft", "KeyW"], 1, 0.1)
            p1 = (await o.gw())["cam"]
            v3 = math.dist(p0, p1) / 0.1
            rapport(v3 > v * 2.5 or v3 >= 59, f"Maj multiplie par 3 ({v3:.1f} m/s)", (v, v3))
            for _ in range(40):
                await o.ev(WHEEL, 100)
            p0 = (await o.gw())["cam"]
            await o.tenir(["KeyW"], 1, 0.5)
            p1 = (await o.gw())["cam"]
            rapport(math.dist(p0, p1) / 0.5 <= 60.01, "vitesse plafonnée à 60 m/s", math.dist(p0, p1) / 0.5)
            # Alt + glisser : orbite à distance constante, regard sur l'avatar
            await o.touche("End")
            for _ in range(3):
                await o.ev(WHEEL, 100)
            da = await o.ev(DIST_AV)
            ca0 = (await o.gw())["cam"]
            await o.ev("""() => { const c = window.__viewer.renderer.domElement;
                c.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, altKey: true }));
                for (let i = 0; i < 5; i++) window.dispatchEvent(new MouseEvent('mousemove', { movementX: 60, movementY: 10, altKey: true }));
                window.dispatchEvent(new MouseEvent('mouseup')); }""")
            db = await o.ev(DIST_AV)
            w = await o.gw()
            ex = [w["pos"][0], w["pos"][1] + 1.7, w["pos"][2]]
            fx, fy, fz = (ex[i] - w["cam"][i] for i in range(3))
            fl = math.sqrt(fx * fx + fy * fy + fz * fz)
            regard = (-math.sin(w["camYaw"]) * math.cos(w["camPitch"]), math.sin(w["camPitch"]), -math.cos(w["camYaw"]) * math.cos(w["camPitch"]))
            rapport(abs(db - da) < 0.05 and math.dist(ca0, w["cam"]) > 0.5, f"Alt + glisser : la caméra orbite et garde sa distance ({da:.2f} -> {db:.2f} m)", (da, db))
            rapport(all(abs(regard[i] - (fx, fy, fz)[i] / fl) < 0.02 for i in range(3)), "Alt + glisser : le regard reste dirigé vers l'avatar", (regard, (fx / fl, fy / fl, fz / fl)))
            await o.touche("End")
            rapport(abs(await o.ev(DIST_AV) - 4) < 0.05 and ecart((await o.gw())["camYaw"], (await o.gw())["yaw"]) < 1e-6, "Fin en caméra libre : derrière l'avatar, distance par défaut")
            rapport(not o.errs, "aucune erreur JavaScript", o.errs)
            await o.ctx.close()

            # ================= 4. distance des infobulles =================
            print("--- 4. infobulle des zones : 40 m par défaut, réglable")
            cfg_d = json.loads((site / "Discret.config.json").read_text(encoding="utf-8"))
            cfg_c = json.loads((site / "Court.config.json").read_text(encoding="utf-8"))
            cfg_h = json.loads((site / "BorneHaut.config.json").read_text(encoding="utf-8"))
            cfg_b = json.loads((site / "BorneBas.config.json").read_text(encoding="utf-8"))
            rapport(cfg_d["zoneInfoDist"] == 40.0 and cfg_c["zoneInfoDist"] == 10.0 and cfg_h["zoneInfoDist"] == 200.0 and cfg_b["zoneInfoDist"] == 5.0, "config : zoneInfoDist 40 par défaut, 10 donné, bornes 5 et 200", (cfg_d["zoneInfoDist"], cfg_c["zoneInfoDist"], cfg_h["zoneInfoDist"], cfg_b["zoneInfoDist"]))

            async def survol_a(page_nom, dist):
                o = await Onglet(br).ouvrir(base_url + page_nom)
                await o.walk((0, 0, 0), 0)
                await o.key("keydown", "Home"); await o.key("keyup", "Home")   # v36 : Début fait voler (F sort de la promenade)
                delta = dist * math.sin(1.45)
                y = FLOOR + 0.06 + delta - 1.7
                await o.ev("""(yy) => { const v = window.__viewer; const k = (t, c) => window.dispatchEvent(new KeyboardEvent(t, { code: c }));
                    k('keydown', 'PageUp'); for (let i = 0; i < 2000 && v.getWalk().pos[1] < yy; i++) v.walkTick(0.05); k('keyup', 'PageUp'); }""", y)
                await o.souris(0, 1.45 / 0.0022)
                await o.ticks(2)
                w = await o.gw()
                await o.pg.mouse.move(400, 300)
                await o.pg.wait_for_timeout(80)
                await o.pg.mouse.move(500, 350)
                await o.pg.wait_for_timeout(150)
                await o.pg.mouse.move(501, 350)
                await o.pg.wait_for_timeout(250)
                t = await tip(o.pg)
                return o, t, w

            o, t, w = await survol_a("Portee", 35)
            rapport(abs(w["pitch"] + 1.45) < 0.02 and w["flying"], "(mise en place : en vol, regard vers le bas)", w["pitch"])
            rapport(t is not None and t.split("\n")[0] == "Zone D", "valeur par défaut (40 m) : infobulle à 35 m", t)
            await o.ctx.close()
            o, t, w = await survol_a("Portee", 45)
            rapport(t is None or t.split("\n")[0] != "Zone D", "valeur par défaut (40 m) : aucune infobulle à 45 m", t)
            await o.ctx.close()
            o, t, w = await survol_a("Long", 45)
            rapport(t is not None and t.split("\n")[0] == "Zone D", "contre-épreuve : avec --zone-info-dist 60, l'infobulle est bien là à 45 m (la géométrie du test est bonne)", t)
            await o.ctx.close()
            o, t, w = await survol_a("Court", 8)
            rapport(t is not None and t.split("\n")[0] == "Zone D", "--zone-info-dist 10 : infobulle à 8 m", t)
            await o.ctx.close()
            o, t, w = await survol_a("Court", 14)
            rapport(t is None or t.split("\n")[0] != "Zone D", "--zone-info-dist 10 : aucune infobulle à 14 m", t)
            await o.ctx.close()
            # clic à 35 m (ouvre le lien) et à 45 m (rien)
            for dist, attendu_ouvert in ((35, 1), (45, 0)):
                o = await Onglet(br).ouvrir(base_url + "Portee")
                await o.walk((0, 0, 0), 0)
                await o.key("keydown", "Home"); await o.key("keyup", "Home")   # v36 : Début fait voler (F sort de la promenade)
                y = FLOOR + 0.06 + dist * math.sin(1.45) - 1.7
                await o.ev("""(yy) => { const v = window.__viewer; const k = (t, c) => window.dispatchEvent(new KeyboardEvent(t, { code: c }));
                    k('keydown', 'PageUp'); for (let i = 0; i < 2000 && v.getWalk().pos[1] < yy; i++) v.walkTick(0.05); k('keyup', 'PageUp'); }""", y)
                await o.souris(0, 1.45 / 0.0022)
                await o.ticks(2)
                await o.pg.mouse.click(500, 350)
                await o.pg.wait_for_timeout(300)
                n = await o.ev("window.__open.length")
                rapport(n == attendu_ouvert, f"clic sur la zone à {dist} m en promenade : {'lien ouvert' if attendu_ouvert else 'rien'}", n)
                await o.ctx.close()
            # noms affichés (showName) : mêmes distances
            o = await Onglet(br).ouvrir(base_url + "Discret")
            LAB = """() => { const v = window.__viewer, r = {}; v.scene.traverse(q => { if (q.isSprite && q.parent && q.parent.userData && q.parent.userData.zoneId) r[q.parent.userData.zoneId] = q.visible; }); return r; }"""
            avant = await o.ev(LAB)
            rapport(avant.get("nomproche") is True and avant.get("nomloin") is True, "vue globale : tous les noms affichés comme avant", avant)
            await o.walk((0, 0, 0), 0)
            await o.ticks(3)
            lab = await o.ev(LAB)
            rapport(lab.get("nomproche") is True and lab.get("nomloin") is False, "promenade : le nom à 30 m est affiché, celui à 60 m masqué", lab)
            await o.ev("window.__viewer.walkStop()")
            lab = await o.ev(LAB)
            rapport(lab.get("nomloin") is True, "retour en vue globale : le nom lointain réapparaît", lab)
            await o.ctx.close()

            # ================= 5. copie dans le presse-papiers =================
            print("--- 5. copie dans le presse-papiers sans contexte sécurisé")
            NOCLIP = """(() => {
              Object.defineProperty(window, 'isSecureContext', { value: false, configurable: true });
              Object.defineProperty(navigator, 'clipboard', { value: undefined, configurable: true });
              window.__ex = [];
              document.execCommand = c => {
                const ta = [...document.querySelectorAll('body > textarea')].map(t => [t.value, t.value.slice(t.selectionStart, t.selectionEnd)]);
                window.__ex.push([c, ta]); return window.__execOk !== false;
              };
            })();"""

            async def lire_toast(o):
                return await o.ev("(() => { const e = document.getElementById('toast'); return e && !e.hidden ? e.textContent : ''; })()")

            o = await Onglet(br).ouvrir(base_url + "Discret", init=STUB + NOCLIP)
            await o.walk((1, 0, 2), 0.5)
            await o.ev("document.getElementById('visLinkBtn').click()")
            await o.pg.wait_for_timeout(300)
            ex = await o.ev("window.__ex")
            champ = await o.ev("document.getElementById('visLinkOut').value")
            rapport(len(ex) == 1 and ex[0][0] == "copy" and ex[0][1] and ex[0][1][0][0] == champ == ex[0][1][0][1] and "key=" in champ, "http : lien personnel copié par le repli (textarea hors écran, sélection complète, execCommand('copy'))", ex)
            rapport(await lire_toast(o) == "Copié", "« Copié » affiché", await lire_toast(o))
            rapport(await o.ev("document.querySelectorAll('body > textarea').length") == 0, "le textarea temporaire est supprimé")
            await o.ev("document.getElementById('linkBtn').click()")
            await o.pg.wait_for_timeout(300)
            ex = await o.ev("window.__ex")
            rapport(len(ex) == 2 and "#pos=" in ex[1][1][0][0] and await lire_toast(o) == "Copié", "http : lien de ma position copié aussi", ex[-1])
            await o.ev("window.__execOk = false")
            await o.ev("document.getElementById('visLinkBtn').click()")
            await o.pg.wait_for_timeout(300)
            etat = await o.ev("(() => { const f = document.getElementById('visLinkOut'); return { hidden: f.hidden, sel: f.value.slice(f.selectionStart, f.selectionEnd) === f.value && f.value.length > 10, ta: document.querySelectorAll('body > textarea').length }; })()")
            rapport(await lire_toast(o) == "Copie impossible : le texte est sélectionné, fais Ctrl+C" and not etat["hidden"] and etat["sel"] and etat["ta"] == 0, "tout échoue : champ affiché et sélectionné, message imposé", (etat, await lire_toast(o)))
            await o.ev("document.getElementById('linkBtn').click()")
            await o.pg.wait_for_timeout(300)
            etat = await o.ev("(() => { const f = document.getElementById('linkOut'); return { sel: f.value.slice(f.selectionStart, f.selectionEnd) === f.value && f.value.length > 10 }; })()")
            rapport(await lire_toast(o) == "Copie impossible : le texte est sélectionné, fais Ctrl+C" and etat["sel"], "tout échoue (lien de position) : champ sélectionné, même message")
            rapport(not o.errs, "aucune erreur JavaScript", o.errs)
            await o.ctx.close()
            # contexte sécurisé : navigator.clipboard.writeText
            CLIP = """(() => { window.__cw = []; window.__ex = [];
              Object.defineProperty(navigator, 'clipboard', { value: { writeText: async t => { window.__cw.push(t); } }, configurable: true });
              document.execCommand = c => { window.__ex.push(c); return true; }; })();"""
            o = await Onglet(br).ouvrir(base_url + "Discret", init=STUB + CLIP)
            await o.walk((1, 0, 2), 0.5)
            await o.ev("document.getElementById('visLinkBtn').click()")
            await o.pg.wait_for_timeout(300)
            cw, ex = await o.ev("window.__cw"), await o.ev("window.__ex")
            rapport(len(cw) == 1 and "key=" in cw[0] and not ex and await lire_toast(o) == "Copié", "contexte sécurisé : navigator.clipboard.writeText utilisé, pas de repli", (cw, ex))
            await o.ctx.close()
            # le viewer
            ctx = await br.new_context(locale="fr-FR", viewport={"width": 1000, "height": 700})
            await ctx.add_init_script(NOCLIP)
            pg = await ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto((DIST / "glb-viewer.html").as_uri())
            await pg.wait_for_function("window.__viewer", timeout=40000)
            await pg.click("#bCopyTarget")
            await pg.wait_for_timeout(300)
            st = await pg.inner_text("#stat")
            ex = await pg.evaluate("window.__ex")
            rapport(re.match(r"Copié\. Cible copiée : -?\d+\.\d, -?\d+\.\d, -?\d+\.\d$", st) is not None and len(ex) == 1, "viewer, http : copie de la cible par le repli", (st, ex))
            await pg.evaluate("window.__execOk = false")
            await pg.click("#bCopyTarget")
            await pg.wait_for_timeout(300)
            st = await pg.inner_text("#stat")
            sel = await pg.evaluate("(() => { const f = document.getElementById('copyField'); return !f.hidden && f.value.slice(f.selectionStart, f.selectionEnd) === f.value && f.value.length > 4; })()")
            rapport(st == "Copie impossible : le texte est sélectionné, fais Ctrl+C" and sel, "viewer, tout échoue : champ sélectionné et message imposé", (st, sel))
            rapport(not errs, "viewer : aucune erreur JavaScript", errs)
            await ctx.close()
        finally:
            proc.kill()
            await br.close()


# ================= 6. --maj et la carte des mondes =================
def test_maj():
    print("--- 6. glb2html.py --maj avec la carte des mondes")
    src = tmp / "region"
    src.mkdir()
    glbfab.region(src / "Syn.glb")
    run(DIST / "glb2tiles.py", src / "Syn.glb", "--nopause", "--forcer", "--budget-tri", "900", "--min", "64", "--entier-etendue", "50")
    mj = tmp / "maj" / "tuiles"
    mj.mkdir(parents=True)
    zonesm = [{"id": "default", "type": "spawn", "x": 3, "y": 15, "z": 4, "yaw": 0.5}]
    (tmp / "zm.json").write_text(json.dumps(zonesm), encoding="utf-8")
    html("-o", mj / "Syn.html", "--shared-shell", "--tiles", src / "Syn.tiles.json", "--zones", tmp / "zm.json", "--presence-url", "ws://ADRESSE:9", "--room", "salonm", "--wave", "1.5")
    cfgp = mj / "Syn.config.json"
    avant = json.loads(cfgp.read_text(encoding="utf-8"))
    zavant = (mj / "Syn.zones.json").read_bytes()
    leurre = tmp / "regions.json"
    leurre.write_text("[]", encoding="utf-8")   # un regions.json dans le dossier de lancement : --maj ne doit pas l'utiliser
    (mj / "mini.png").write_bytes(bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360f8cfc0f01f0005000201a5f645400000000049454e44ae426082"))
    r = html("--maj", "-o", mj / "Syn.html", "--shared-shell", "--register", "regions.json", "--region-name", "Free House Gallery 4X4", "--region-xy", "1000,1001",
             "--thumb", "mini.png", "--map-page", "carte.html", "--map-url", "https://ADRESSE/regions.json", cwd=tmp)
    reg = mj / "regions.json"
    rapport(reg.is_file(), "--maj --register chemin relatif : regions.json apparaît à côté de la page", r.stdout + r.stderr)
    rapport(not (DIST / "regions.json").exists() and leurre.read_text(encoding="utf-8") == "[]", "rien n'est écrit dans le dossier des outils ni dans le dossier de lancement")
    data = json.loads(reg.read_text(encoding="utf-8")) if reg.is_file() else []
    e = data[0] if data else {}
    rapport(len(data) == 1 and e.get("name") == "Free House Gallery 4X4" and e.get("room") == "salonm" and e.get("url") == "index.html?region=Syn" and e.get("x") == 1000 and e.get("y") == 1001
            and str(e.get("thumb", "")).startswith("data:image/") and e.get("presence") == "ws://ADRESSE:9", "la fiche : nom, salon de la config, adresse de la coquille commune, position, vignette lue à côté de la page, présence de la config", e)
    nouv = json.loads(cfgp.read_text(encoding="utf-8"))
    diff = {k for k in set(avant) | set(nouv) if avant.get(k) != nouv.get(k)}
    rapport(diff == {"map", "mapUrl"} and nouv["map"] and nouv["mapUrl"] == "https://ADRESSE/regions.json", "la config est inchangée, hors la carte (map, mapUrl)", diff)
    rapport((mj / "Syn.zones.json").read_bytes() == zavant, "les zones sont conservées telles quelles")
    carte = mj / "carte.html"
    rapport(carte.is_file() and "Free House Gallery 4X4" in carte.read_text(encoding="utf-8") and "index.html?region=Syn" in carte.read_text(encoding="utf-8"), "--map-page produit carte.html à côté de la page, avec la région")
    rapport("relatifs au dossier de la page" in r.stdout and str(mj.resolve()) in r.stdout, "le message de fin dit que les chemins relatifs sont ceux de la page", r.stdout[-500:])
    # seconde passe : sans --register, la carte et la fiche restent
    r = html("--maj", "-o", mj / "Syn.html", "--shared-shell", "--sea-y", "7", cwd=tmp)
    nouv2 = json.loads(cfgp.read_text(encoding="utf-8"))
    rapport(nouv2["map"] == nouv["map"] and nouv2["seaY"] == 7.0, "--maj sans --register ensuite : la carte de la config est gardée")
    # --map FICHIER relatif : relatif à la page
    (mj / "autre.json").write_text(json.dumps([{"id": "x", "name": "Autre région", "url": "https://ADRESSE/x.html", "x": 5, "y": 5, "room": "x"}]), encoding="utf-8")
    r = html("--maj", "-o", mj / "Syn.html", "--shared-shell", "--map", "autre.json", "--map-page", "carte2.html", cwd=tmp)
    rapport((mj / "carte2.html").is_file() and "Autre région" in (mj / "carte2.html").read_text(encoding="utf-8"), "--maj --map FICHIER relatif lu à côté de la page ; --map-page générée", r.stdout + r.stderr)
    # options région sans --register : avertissement
    r = html("--maj", "-o", mj / "Syn.html", "--shared-shell", "--region-name", "Oublié", cwd=tmp)
    rapport("ne servent qu'avec --register" in r.stderr and r.returncode == 0, "--region-name sans --register : avertissement", r.stderr)
    # chemin absolu : respecté
    ab = tmp / "ailleurs" / "r.json"
    html("--maj", "-o", mj / "Syn.html", "--shared-shell", "--register", ab, cwd=tmp)
    rapport(ab.is_file(), "--register avec un chemin absolu : écrit là")
    # sans --maj : ancien comportement, avec une ligne qui dit où le fichier est écrit
    page2 = tmp / "gen" / "p"
    page2.mkdir(parents=True)
    (tmp / "rel.json").write_text("[]", encoding="utf-8")   # existe dans le dossier de lancement : c'est lui qui est utilisé (comportement documenté)
    sol_glb(tmp / "s.glb")
    r = html(tmp / "s.glb", "-o", page2 / "S.html", "--register", "rel.json", "--no-sea", cwd=tmp)
    ecrit = json.loads((tmp / "rel.json").read_text(encoding="utf-8"))
    rapport(len(ecrit) == 1 and not (page2 / "rel.json").exists() and "n'est pas à côté de la page" in r.stdout and "--maj" in r.stdout, "sans --maj : comportement d'avant conservé et une ligne dit où regions.json est écrit", r.stdout)


if __name__ == "__main__":
    try:
        asyncio.run(main())
        test_maj()
    finally:
        presence.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not bad else f"{bad} échec(s)"))
    sys.exit(1 if bad else 0)
