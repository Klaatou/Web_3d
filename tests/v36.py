#!/usr/bin/env python3
"""Tests v36 (lot A) : touches F / P / E / Début / Page Haut / Espace / T / M, disposition du clavier (AZERTY / QWERTY), aide et informations en trois temps,
arrivée occupée (deux navigateurs, vrai presence_server.py), repères de portail (cônes), sons (espion Web Audio), copie de la position et « Aller à ».

Le lot B (langue) a ses propres tests : tests/v36_lang.py.

Prérequis : pip install playwright websockets ; python build.py avant.
Variables facultatives : THREE_DIR (paquet npm three, hors ligne), CHROMIUM (chemin de l'exécutable).
Lancer : python tests/v36.py
"""
import asyncio, json, math, os, pathlib, re, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
os.environ["WEB3D_LANG"] = "fr"

DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_v36_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
LOC = "fr-FR"   # le Chromium de test est en anglais : on fixe la locale française du contexte (voir new_context)
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


def lancer_presence(*extra):
    port = port_libre()
    proc = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--host", "127.0.0.1", "--port", str(port), "--identities", "", *extra],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=tmp)
    attendre_port(port, proc, "presence_server")
    return proc, port


def sol_glb(path, demi=20.0):
    pos = struct.pack("<12f", -demi, 0, -demi, demi, 0, -demi, demi, 0, demi, -demi, 0, demi)
    blob = pos + struct.pack("<6H", 0, 2, 1, 0, 3, 2) + b"\0\0"
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-demi, 0, -demi], "max": [demi, 0, demi]},
                       {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


FLOOR = 15   # le cadrage relève le sol de la région synthétique à 15 m

# ---------- fabrication ----------
print("--- 0. fabrication des pages")
presence, pport = lancer_presence("--chat-burst", "100", "--chat-gap", "0.1")
PURL = f"ws://127.0.0.1:{pport}"
site = tmp / "site"
site.mkdir()
sol_glb(site / "sol.glb")
sol_glb(site / "minuscule.glb", 0.6)
ZL = [
    {"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0.0},
    {"id": "autre", "type": "spawn", "x": 6, "y": 15, "z": 6, "yaw": 0.0},
    {"id": "lien", "type": "url", "label": "Lien test", "target": "https://example.org/", "x": 0, "y": 15, "z": -4.2, "radius": 4},
    {"id": "porte", "type": "portal", "label": "Portail entrée", "target": "", "spawn": "autre", "x": -10, "y": 15, "z": 10, "radius": 2, "trigger": "enter"},
    {"id": "duo", "type": "portal", "label": "Portail double", "target": "", "spawn": "autre", "x": 10, "y": 15, "z": -10, "radius": 2, "trigger": "both"},
]
(tmp / "z.json").write_text(json.dumps(ZL), encoding="utf-8")
base = ["--shared-shell", "--zones", tmp / "z.json", "--no-sea", "--target", "0,0,0", "--presence-url", PURL, "--room", "t36", "--chat", *vend]
html(site / "sol.glb", "-o", site / "Cone.html", *base, "--register", site / "regions.json", "--region-name", "Test 36", "--map-page", "carte.html")
html(site / "sol.glb", "-o", site / "NoCone.html", *base, "--no-zone-cone")
html(site / "sol.glb", "-o", site / "Proche.html", *base, "--zone-info-dist", "10")
html(site / "sol.glb", "-o", site / "Spawns.html", *base, "--show-spawns")
html(site / "sol.glb", "-o", site / "NoSpec.html", *base, "--no-spectate")
(tmp / "zp.json").write_text(json.dumps([{"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0.0}]), encoding="utf-8")
html(site / "minuscule.glb", "-o", site / "Petit.html", "--shared-shell", "--zones", tmp / "zp.json", "--no-sea", "--target", "0,0,0", "--presence-url", PURL, "--room", "t36p", *vend)
cfg_cone = json.loads((site / "Cone.config.json").read_text(encoding="utf-8"))
cfg_no = json.loads((site / "NoCone.config.json").read_text(encoding="utf-8"))
rapport(cfg_cone.get("zoneCone") is True and cfg_no.get("zoneCone") is False, "config : zoneCone vrai par défaut, faux avec --no-zone-cone", (cfg_cone.get("zoneCone"), cfg_no.get("zoneCone")))
aide = run(DIST / "glb2html.py", "--help").stdout
rapport("--zone-cone" in aide and "--no-zone-cone" in aide, "--help liste --zone-cone / --no-zone-cone")

STUB = """(() => {
  let el = null; window.__plCalls = 0;
  Object.defineProperty(document, 'pointerLockElement', { get: () => el, configurable: true });
  Element.prototype.requestPointerLock = function () { window.__plCalls++; el = this; setTimeout(() => document.dispatchEvent(new Event('pointerlockchange')), 0); };
  document.exitPointerLock = () => { el = null; setTimeout(() => document.dispatchEvent(new Event('pointerlockchange')), 0); };
  window.__open = []; window.open = (u) => { window.__open.push(u); return null; };
  window.__sent = []; const s = WebSocket.prototype.send;
  WebSocket.prototype.send = function (d) { try { window.__sent.push(JSON.parse(d)); } catch (e) {} return s.call(this, d); };
})();"""

# espion Web Audio : contextes créés, oscillateurs (fréquences) et crêtes de gain
AUDIO = """(() => {
  window.__au = { ctx: 0, osc: [], peaks: [] };
  window.AudioContext = class {
    constructor() { window.__au.ctx++; this.state = 'running'; this.currentTime = 0; this.destination = {}; }
    resume() {}
    createOscillator() { const o = { type: '', frequency: { value: 0 }, connect() {}, start() {}, stop() {} }; window.__au.osc.push(o); return o; }
    createGain() { return { gain: { setValueAtTime() {}, exponentialRampToValueAtTime(v) { window.__au.peaks.push(v); } }, connect() {} }; }
  };
})();"""

# retarde la réception des messages de présence (le contrôle d'arrivée occupée doit alors attendre la liste des visiteurs)
DELAY = """(() => {
  const N = window.WebSocket; window.__wsDelay = 0;
  function WS(u, p) {
    const ws = p === undefined ? new N(u) : new N(u, p); let h = null;
    Object.defineProperty(ws, 'onmessage', { configurable: true, get: () => h, set: f => { h = f; ws.addEventListener('message', ev => { setTimeout(() => { if (h) h(ev); }, window.__wsDelay); }); } });
    return ws;
  }
  WS.prototype = N.prototype; for (const k of ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED']) WS[k] = N[k];
  window.WebSocket = WS;
})();"""


class Onglet:
    def __init__(self, br):
        self.br, self.errs = br, []

    async def ouvrir(self, url, init=STUB, ctx=None, viewer=True, locale=LOC, **ctxopts):
        self.ctx = ctx or await self.br.new_context(viewport={"width": 1000, "height": 700}, locale=locale, **ctxopts)
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
            for (let i = 0; i < n; i++) { v.walkTick(dt); const w = v.getWalk(); out.push({ pos: w.pos, flying: w.flying, grounded: w.grounded }); }
            keys.forEach(c => k('keyup', c));
            return out; }""", [touches, n, dt])

    async def txt(self, ident):
        return await self.ev("(i) => document.getElementById(i).textContent", ident)

    async def attendre(self, js, s=30):
        await self.pg.wait_for_function(js, timeout=s * 1000)


def dist_h(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


async def main():
    from playwright.async_api import async_playwright
    import websockets, websockets.asyncio.client
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        proc, port = serveur(site)
        base_url = f"http://127.0.0.1:{port}/index.html?region="
        try:
            # ================= 1. touches =================
            print("--- 1. F / P entrent et sortent ; Début vole ; Page Haut, Espace ; E = zone ; T ; M")
            o = await Onglet(br).ouvrir(base_url + "Cone")
            await o.touche("KeyF")
            await o.pg.wait_for_function("window.__viewer.walking", timeout=10000)
            rapport(True, "vue globale : F entre en promenade")
            await o.touche("KeyF")
            rapport(not await o.ev("window.__viewer.walking"), "promenade : F en sort")
            await o.touche("KeyP")
            rapport(await o.ev("window.__viewer.walking"), "P entre")
            await o.touche("KeyP")
            rapport(not await o.ev("window.__viewer.walking"), "P sort")
            await o.touche("KeyF", ctrlKey=True)
            rapport(not await o.ev("window.__viewer.walking"), "Ctrl+F n'est pas intercepté")
            await o.walk((0, 0, 0), 0)
            await o.touche("KeyF")
            rapport(not await o.ev("window.__viewer.walking"), "F ne fait plus basculer le vol : il sort de la promenade")
            await o.walk((0, 0, 0), 0)
            await o.ticks(20)
            await o.touche("Home")
            rapport((await o.gw())["flying"], "Début : vole")
            await o.touche("Home")
            rapport(not (await o.gw())["flying"], "Début de nouveau : atterrit")
            # Espace maintenu en vol : monte
            await o.touche("Home")
            out = await o.tenir(["Space"], 12, 0.1)
            rapport(out[-1]["flying"] and out[-1]["pos"][1] > out[2]["pos"][1] + 2 and out[-1]["pos"][1] > FLOOR + 2, f"en vol, Espace maintenu monte (y = {out[-1]['pos'][1]:.1f} m)", [s["pos"][1] for s in out])
            out = await o.tenir(["PageUp"], 8, 0.1)
            rapport(out[-1]["pos"][1] > out[0]["pos"][1] + 1, "en vol, Page Haut monte")
            out = await o.tenir(["KeyC"], 120, 0.1)
            rapport(not out[-1]["flying"] and out[-1]["grounded"] and abs(out[-1]["pos"][1] - FLOOR) < 0.05, "C maintenu : descend et atterrit tout seul", out[-1])
            w = await o.ticks(30)
            rapport(w["grounded"] and not w["flying"], "après l'atterrissage Espace tenu pendant le vol ne fait pas sauter l'avatar")
            # sur le sol : Espace bref = saut ; Page Haut bref = saut ; Page Haut maintenu = décollage ; E = rien
            out = await o.tenir(["Space"], 3, 0.1)
            rapport(max(s["pos"][1] for s in out) > FLOOR + 0.05 and not out[-1]["flying"], "Espace bref au sol : saut")
            await o.ticks(30)
            await o.tenir(["PageUp"], 3, 0.1)
            out = await o.tenir([], 1, 0.05)
            await o.ticks(30)
            out = await o.tenir(["PageUp"], 3, 0.1)
            rapport(max(s["pos"][1] for s in out) > FLOOR + 0.05 and not out[-1]["flying"], "Page Haut bref au sol : saut, pas de décollage")
            await o.ticks(30)
            out = await o.tenir(["KeyE"], 3, 0.1)
            rapport(max(s["pos"][1] for s in out) < FLOOR + 0.02 and not out[-1]["flying"], "E bref au sol : l'avatar ne saute pas", out[-1])
            out = await o.tenir(["KeyE"], 14, 0.1)
            rapport(not out[-1]["flying"] and out[-1]["pos"][1] < FLOOR + 0.02, "E maintenu au sol : ni décollage ni montée", out[-1])
            out = await o.tenir(["PageUp"], 14, 0.1)
            rapport(out[-1]["flying"] and out[-1]["pos"][1] > FLOOR + 2, "Page Haut maintenu plus de 0,4 s au sol : décollage", out[-1])
            await o.touche("Home")
            await o.ticks(80)
            # E : zone proche
            await o.ev("window.__viewer.teleportTo([0, 0, -2], 0)")
            await o.ticks(5)
            near = await o.ev("(() => { const e = document.getElementById('zonePrompt'); return e && !e.hidden ? e.textContent : null; })()")
            rapport(near == "clic ou E : Lien test", "près d'une zone : l'invite dit « clic ou E : Lien test »", near)
            await o.ev("window.__open.length = 0")
            await o.touche("KeyE")
            await o.ticks(2)
            rapport(await o.ev("window.__open.length") == 1 and "example.org" in (await o.ev("window.__open[0]")), "E déclenche la zone proche (le lien s'ouvre)", await o.ev("window.__open"))
            await o.ev("window.__open.length = 0")
            await o.touche("KeyE", ctrlKey=True)
            rapport(await o.ev("window.__open.length") == 0, "Ctrl+E ne déclenche rien")
            await o.touche("Home")
            await o.ticks(3)
            await o.touche("KeyE")
            rapport(await o.ev("window.__open.length") == 1, "E déclenche aussi la zone en vol")
            await o.touche("Home")
            await o.ticks(80)
            # T : repères
            rapport(await o.ev("window.__viewer.cones") is True, "T : repères affichés au départ (défaut)")
            await o.touche("KeyT")
            rapport(await o.ev("window.__viewer.cones") is False and all(not c["visible"] for c in await o.ev("window.__viewer.getCones()")), "T masque tous les cônes")
            await o.pg.reload()
            await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            rapport(await o.ev("window.__viewer.cones") is False, "le choix est mémorisé après rechargement")
            await o.touche("KeyT")
            rapport(await o.ev("window.__viewer.cones") is True and all(c["visible"] for c in await o.ev("window.__viewer.getCones()")), "T de nouveau : affichés")
            await o.walk((0, 0, 0), 0)
            # M : lettre imprimée
            await o.touche("KeyM", key=",")
            rapport(await o.ev("window.__viewer.view") == "fps", "touche de code KeyM mais imprimant « , » (AZERTY) : ne bascule PAS la vue")
            await o.touche("Semicolon", key="m")
            rapport(await o.ev("window.__viewer.view") == "tps", "touche imprimant « m » (code Semicolon, AZERTY) : bascule la vue")
            await o.touche("KeyM", key="m")
            rapport(await o.ev("window.__viewer.view") == "fps", "touche de code KeyM imprimant « m » (QWERTY) : bascule aussi")
            await o.touche("KeyM", key="M", shiftKey=True)
            await o.touche("KeyM", key="m")
            await o.touche("Semicolon", key="m", ctrlKey=True)
            rapport(not await o.ev("document.getElementById('mapOverlay').hidden"), "Ctrl+« m » ouvre la carte en promenade")
            await o.touche("Semicolon", key="m", ctrlKey=True)
            rapport(await o.ev("document.getElementById('mapOverlay').hidden"), "et la referme")
            rapport(not o.errs, "aucune erreur JavaScript", o.errs)
            await o.ctx.close()

            # ================= 2. disposition du clavier =================
            print("--- 2. disposition du clavier")
            for loc, att, nom in (("fr-FR", "ZQSD", "fr-FR"), ("fr-BE", "ZQSD", "fr-BE"), ("en-US", "WASD", "en-US"), ("fr-CA", "WASD", "fr-CA"), ("de-DE", "WASD", "de-DE")):
                o = await Onglet(br).ouvrir(base_url + "Cone", init=STUB + "Object.defineProperty(navigator, 'keyboard', { value: undefined, configurable: true });", locale=loc)
                await o.walk((0, 0, 0), 0)
                aide = await o.txt("helpBody")
                etat = await o.txt("kbInfo")
                ok = (att in aide.replace(" ", "")) and (("WASD" if att == "ZQSD" else "ZQSD") not in aide.replace(" ", ""))
                rapport(ok and att[0] in etat, f"locale {nom} sans getLayoutMap : {att} (l'autre disposition n'apparaît pas)", (aide[:160], etat))
                await o.ctx.close()
            # getLayoutMap
            GLM = "navigator.keyboard = { getLayoutMap: () => Promise.resolve(new Map([['KeyW', 'z'], ['KeyQ', 'a']])) };"
            GLM = "Object.defineProperty(navigator, 'keyboard', { value: { getLayoutMap: () => Promise.resolve(new Map([['KeyW', 'z'], ['KeyQ', 'a']])) }, configurable: true });"
            o = await Onglet(br).ouvrir(base_url + "Cone", init=STUB + GLM, locale="en-US")
            await o.walk((0, 0, 0), 0)
            await o.attendre("document.getElementById('helpBody').textContent.replace(/ /g, '').includes('ZQSD')", 10)
            rapport(True, "getLayoutMap lit KeyW = z : AZERTY même avec une locale anglaise")
            # réglage explicite
            await o.ev("document.getElementById('optsBtn').click()")
            await o.ev("(() => { const s = document.getElementById('visLayout'); s.value = 'qwerty'; s.dispatchEvent(new Event('change')); })()")
            aide = (await o.txt("helpBody")).replace(" ", "")
            rapport("WASD" in aide and "ZQSD" not in aide and "W" in await o.txt("kbInfo"), "réglage « QWERTY » : l'aide change aussitôt", aide[:120])
            await o.ev("(() => { const s = document.getElementById('visLayout'); s.value = 'azerty'; s.dispatchEvent(new Event('change')); })()")
            aide = (await o.txt("helpBody")).replace(" ", "")
            rapport("ZQSD" in aide and "WASD" not in aide, "réglage « AZERTY » : l'aide change aussitôt")
            await o.pg.reload()
            await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            await o.walk((0, 0, 0), 0)
            rapport(await o.ev("document.getElementById('visLayout') === null ? null : (document.getElementById('optsBtn').click(), document.getElementById('visLayout').value)") == "azerty", "le réglage est mémorisé")
            # la marche reste sur les codes physiques
            await o.ticks(20)
            z0 = (await o.gw())["pos"][2]
            await o.tenir(["KeyW"], 5, 0.1)
            rapport((await o.gw())["pos"][2] < z0 - 0.5, "la marche reste sur le code physique KeyW")
            await o.ctx.close()

            # ================= 3. aide et informations en trois temps =================
            print("--- 3. H et I : masquée -> déployée, réduite -> déployée, déployée -> masquée")
            o = await Onglet(br).ouvrir(base_url + "Cone")
            await o.walk((0, 0, 0), 0)
            rapport("Informations / État" in await o.txt("stateHead"), "la fenêtre s'appelle « Informations / État »", await o.txt("stateHead"))
            for touche, wrap, body, nom in (("KeyH", "walkHint", "helpBody", "aide"), ("KeyI", "stateInfo", "stateBody", "informations")):
                etat = lambda: o.ev("([w, b]) => [document.getElementById(w).hidden, document.getElementById(b).hidden]", [wrap, body])
                rapport(await etat() == [False, False], f"{nom} : déployée au départ")
                await o.touche(touche)
                rapport(await etat() == [True, False] or (await etat())[0], f"{nom} : déployée -> masquée")
                await o.touche(touche)
                rapport(await etat() == [False, False], f"{nom} : masquée -> déployée")
                await o.pg.click("#" + ("helpHead" if wrap == "walkHint" else "stateHead"))
                rapport(await etat() == [False, True], f"{nom} : clic sur le titre -> réduite")
                await o.touche(touche)
                rapport(await etat() == [False, False], f"{nom} : réduite -> DÉPLOYÉE (pas masquée)")
                await o.touche(touche)
                await o.touche(touche)
                rapport(await etat() == [False, False], f"{nom} : déployée -> masquée -> déployée")
                # réduit mémorisé
                await o.pg.click("#" + ("helpHead" if wrap == "walkHint" else "stateHead"))
            await o.pg.reload()
            await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            await o.walk((0, 0, 0), 0)
            rapport(await o.ev("document.getElementById('helpBody').hidden && document.getElementById('stateBody').hidden && !document.getElementById('walkHint').hidden"), "réduit reste mémorisé après rechargement")
            await o.pg.click("#helpHead"); await o.pg.click("#stateHead")
            await o.touche("KeyH"); await o.touche("KeyI")
            await o.pg.reload()
            await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            await o.walk((0, 0, 0), 0)
            rapport(await o.ev("document.getElementById('walkHint').hidden && document.getElementById('stateInfo').hidden"), "masqué reste mémorisé après rechargement")
            await o.touche("KeyH"); await o.touche("KeyI")
            rapport(await o.ev("!document.getElementById('walkHint').hidden && !document.getElementById('helpBody').hidden"), "H : masquée -> déployée")
            await o.ctx.close()

            # ================= 4. repères de portail =================
            print("--- 4. repères de portail (cônes)")
            o = await Onglet(br).ouvrir(base_url + "Cone")
            cones = await o.ev("window.__viewer.getCones()")
            ids = sorted(c["id"] for c in cones)
            rapport(ids == ["duo", "porte"], "un cône au-dessus de chaque portail (enter et both), aucun sur la zone « clic » ni sur les arrivées", ids)
            c_porte = next(c for c in cones if c["id"] == "porte")
            rapport(abs(c_porte["pos"][0] + 10) < 0.01 and abs(c_porte["pos"][2] - 10) < 0.01 and abs(c_porte["pos"][1] - (15 + 2.25)) < 0.01, "centre du cône à 0,25 m sous un sommet situé 2,0 m au-dessus du centre de la zone", c_porte)
            geo = await o.ev("""() => { let r = null; window.__viewer.scene.traverse(o => { if (o.userData && o.userData.cone && !r) { const g = o.geometry.parameters; r = [g.radius * 2, g.height, o.rotation.x, o.material.color.getHex(), o.children.length]; } }); return r; }""")
            rapport(abs(geo[0] - 0.35) < 0.01 and abs(geo[1] - 0.5) < 0.01 and abs(geo[2] - math.pi) < 1e-6 and geo[4] == 1, "cône de 0,35 m x 0,5 m, pointe vers le bas, avec un contour (arêtes)", geo)
            rapport(geo[3] == 0xe8e8e8, "teinte neutre claire", hex(geo[3]))
            # infobulle au survol (vue globale, cadrage serré sur le cône)
            await o.ev("window.__viewer.frame([0, 0.25, 1], [-10, 17.25, 10], 0.08)")
            await o.pg.wait_for_timeout(300)
            PROJ = """() => { const v = window.__viewer, V = v.camera.position.constructor; v.controls.update(); v.camera.updateMatrixWorld(true); const p = new V(-10, 17.25, 10).project(v.camera), r = v.renderer.domElement.getBoundingClientRect();
                return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; }"""
            tip = None
            for essai in range(8):   # le survol est limité à une mesure toutes les 50 ms ; le rendu logiciel peut être lent
                xy = await o.ev(PROJ)
                await o.pg.mouse.move(xy[0] - 30, xy[1] + 30)
                await o.pg.wait_for_timeout(120)
                await o.pg.mouse.move(xy[0], xy[1], steps=3)
                await o.pg.wait_for_timeout(200)
                await o.pg.mouse.move(xy[0] + 0.5, xy[1])
                await o.pg.wait_for_timeout(200)
                tip = await o.ev("(() => { const e = document.getElementById('zoneTip'); return e && !e.hidden ? e.innerText : null; })()")
                if tip:
                    break
            rapport(tip is not None and "Portail entrée" in tip and "Région" in tip, "survoler le cône affiche la même infobulle que la zone (nom et destination)", tip)
            await o.touche("KeyT")
            await o.pg.mouse.move(xy[0] - 40, xy[1] + 40)
            await o.pg.mouse.move(xy[0], xy[1], steps=4)
            await o.pg.wait_for_timeout(200)
            tip = await o.ev("(() => { const e = document.getElementById('zoneTip'); return e && !e.hidden ? e.innerText : null; })()")
            rapport(tip is None, "cônes masqués par T : plus d'infobulle sur le cône", tip)
            await o.touche("KeyT")
            await o.ctx.close()
            # --no-zone-cone : masqués au départ, T les affiche
            o = await Onglet(br).ouvrir(base_url + "NoCone")
            rapport(await o.ev("window.__viewer.cones") is False and all(not c["visible"] for c in await o.ev("window.__viewer.getCones()")), "--no-zone-cone : cônes masqués au départ")
            await o.touche("KeyT")
            rapport(all(c["visible"] for c in await o.ev("window.__viewer.getCones()")), "… et T les affiche")
            await o.ctx.close()
            # distance zoneInfoDist
            o = await Onglet(br).ouvrir(base_url + "Proche")
            await o.walk((0, 0, 0), 0)
            await o.ticks(3)
            vis = {c["id"]: c["visible"] for c in await o.ev("window.__viewer.getCones()")}
            rapport(vis == {"porte": False, "duo": False}, "avatar à 14 m des portails, --zone-info-dist 10 : cônes masqués", vis)
            await o.ev("window.__viewer.teleportTo([-10, 0, 6], 0)")
            await o.ticks(3)
            vis = {c["id"]: c["visible"] for c in await o.ev("window.__viewer.getCones()")}
            rapport(vis == {"porte": True, "duo": False}, "à 4 m du portail « porte » : son cône apparaît, l'autre reste masqué", vis)
            await o.ctx.close()
            # arrivées : cône seulement avec --show-spawns
            o = await Onglet(br).ouvrir(base_url + "Spawns")
            ids = sorted(c["id"] for c in await o.ev("window.__viewer.getCones()"))
            rapport(ids == ["autre", "default", "duo", "porte"], "--show-spawns : les arrivées ont aussi leur cône", ids)
            await o.ctx.close()

            # ================= 5. copier ma position, « Aller à » =================
            print("--- 5. copier ma position (URL / xyz) et « Aller à »")
            o = await Onglet(br).ouvrir(base_url + "Cone")
            await o.walk((0, 0, 0), 0)
            await o.ev("window.__viewer.teleportTo([7.34, 0, -3.21], 1.25)")
            await o.ticks(30)
            rapport(await o.txt("linkBtn") == "Copier ma position", "le bouton s'appelle « Copier ma position »", await o.txt("linkBtn"))
            rapport(await o.ev("document.getElementById('linkFmt').value") == "url", "format par défaut : URL")
            await o.ev("document.getElementById('linkBtn').click()")
            await o.pg.wait_for_timeout(200)
            url = await o.ev("document.getElementById('linkOut').value")
            rapport("#pos=" in url, "format URL : adresse avec #pos=", url)
            await o.ev("(() => { const s = document.getElementById('linkFmt'); s.value = 'xyz'; s.dispatchEvent(new Event('change')); document.getElementById('linkBtn').click(); })()")
            await o.pg.wait_for_timeout(200)
            xyz = await o.ev("document.getElementById('linkOut').value")
            rapport(re.fullmatch(r"-?\d+\.\d, -?\d+\.\d, -?\d+\.\d", xyz) is not None, "format xyz : « x, y, z » avec une décimale", xyz)
            pos = (await o.gw())["pos"]
            rapport(xyz == ", ".join(f"{round(v * 10) / 10:.1f}" for v in pos), "xyz = la position à 0,1 m", (xyz, pos))
            await o.pg.reload()
            await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            rapport(await o.ev("document.getElementById('linkFmt').value") == "xyz", "le format choisi est mémorisé")
            await o.walk((0, 0, 0), 0)
            await o.ticks(20)
            for texte, nom in ((xyz, "xyz"), (url, "adresse complète")):
                await o.ev("window.__viewer.teleportTo([-15, 0, 15], 0)")
                await o.ticks(20)
                await o.ev("(t) => { const i = document.getElementById('gotoIn'); i.value = t; document.getElementById('gotoBtn').click(); }", texte)
                await o.ticks(20)
                w = await o.gw()
                rapport(abs(w["pos"][0] - 7.3) < 0.1 and abs(w["pos"][2] + 3.2) < 0.1, f"« Aller à » accepte le format {nom} : même point", w["pos"])
                if nom != "xyz":
                    rapport(abs(w["yaw"] - 1.25) < 0.01, "… et l'adresse apporte aussi l'orientation", w["yaw"])
            await o.ctx.close()

            # ================= 6. sons =================
            print("--- 6. sons (espion Web Audio)")
            VIS_OFF = lambda **k: "try { localStorage.setItem('glb2html_visitor', " + json.dumps(json.dumps(k)) + "); } catch (e) {}"

            async def ws_client(nom, uid, salon="t36"):
                ws = await websockets.asyncio.client.connect(PURL)
                await ws.send(json.dumps({"t": "hello", "room": salon, "name": nom, "uid": uid, "spectator": False}))
                await asyncio.wait_for(ws.recv(), 5)
                await ws.send(json.dumps({"t": "pos", "p": [14, 15, 14], "yaw": 0}))
                return ws

            async def ecoute(ws):
                try:
                    async for _ in ws:
                        pass
                except Exception:
                    pass
            # liste initiale : pas de son
            ws0 = await ws_client("Present", "P" * 24)
            t0 = asyncio.ensure_future(ecoute(ws0))
            a = await Onglet(br).ouvrir(base_url + "Cone", init=STUB + AUDIO + "try { localStorage.setItem('glb2html_name', 'Alice'); } catch (e) {}")
            rapport(await a.ev("window.__au.ctx") == 0, "contexte audio : pas créé avant la première action de l'utilisateur")
            await a.pg.keyboard.press("KeyG")   # première action de l'utilisateur
            await a.walk((0, 0, 0), 0)
            await a.attendre("window.__viewer.getPresence().state === 'online' && window.__viewer.getPresence().peers.length >= 1", 30)
            await a.pg.wait_for_timeout(600)
            rapport(await a.ev("window.__au.osc.length") == 0, "visiteur déjà présent à mon arrivée (liste initiale) : aucun son", await a.ev("window.__au.osc.length"))
            rapport(await a.ev("window.__au.ctx") >= 1, "le contexte audio démarre à la première action de l'utilisateur", await a.ev("window.__au.ctx"))
            # arrivée
            ws1 = await ws_client("Bob", "B" * 24)
            t1 = asyncio.ensure_future(ecoute(ws1))
            await a.attendre("window.__au.osc.length >= 2", 10)
            freq = await a.ev("window.__au.osc.map(o => o.frequency.value)")
            rapport(freq == [660, 880], "arrivée d'un visiteur en promenade : deux notes montantes 660 puis 880 Hz", freq)
            pk = await a.ev("window.__au.peaks")
            rapport(abs(pk[0] - 0.125) < 1e-6, "volume 50 : crête de gain 0,125", pk)
            # deuxième arrivée dans les 2 s : pas de nouveau son
            ws2 = await ws_client("Carl", "C" * 24)
            t2 = asyncio.ensure_future(ecoute(ws2))
            await a.attendre("window.__viewer.getPresence().peers.length >= 3", 10)
            await a.pg.wait_for_timeout(400)
            rapport(await a.ev("window.__au.osc.length") == 2, "deux arrivées à moins de 2 s : un seul son", await a.ev("window.__au.osc.length"))
            # départ
            await asyncio.sleep(2.1)
            await ws1.close()
            await a.attendre("window.__au.osc.length >= 4", 10)
            freq = await a.ev("window.__au.osc.map(o => o.frequency.value)")
            rapport(freq[2:4] == [880, 660], "départ : deux notes descendantes 880 puis 660 Hz", freq)
            # spectateur : ni son à l'arrivée ni au départ
            n0 = await a.ev("window.__au.osc.length")
            wss = await websockets.asyncio.client.connect(PURL)
            await wss.send(json.dumps({"t": "hello", "room": "t36", "name": "", "uid": "S" * 24, "spectator": True}))
            await asyncio.wait_for(wss.recv(), 5)
            await asyncio.sleep(0.6)
            await wss.close()
            await asyncio.sleep(0.6)
            rapport(await a.ev("window.__au.osc.length") == n0, "un spectateur (vue globale) qui arrive et part : aucun son", (n0, await a.ev("window.__au.osc.length")))
            # citation
            await asyncio.sleep(2.1)
            n0 = await a.ev("window.__au.osc.length")
            await ws2.send(json.dumps({"t": "chat", "text": "salut Alice, ça va ?"}))
            await a.attendre(f"window.__au.osc.length > {n0}", 10)
            rapport(await a.ev("window.__au.osc.map(o => o.frequency.value).slice(-1)[0]") == 880, "message qui cite mon pseudo : bip", await a.ev("window.__au.osc.length"))
            # réglages : cases et volume
            await a.ev("document.getElementById('optsBtn').click()")
            et = await a.ev("({ sons: document.getElementById('visSounds').checked, vol: document.getElementById('visVolume').value, cite: document.getElementById('visSoundCite').checked, join: document.getElementById('visSoundJoin').checked, leave: document.getElementById('visSoundLeave').checked })")
            rapport(et == {"sons": True, "vol": "50", "cite": True, "join": True, "leave": True}, "réglages visiteur : Sons cochée, volume 50, trois cases cochées par défaut", et)
            lib = await a.ev("[...document.querySelectorAll('#optsPanel label')].map(l => l.textContent)")
            rapport("Bip quand un message cite mon pseudo" in lib and "Son à l'arrivée d'un visiteur" in lib and "Son au départ d'un visiteur" in lib and not any("sonore" in l for l in lib), "libellés des cases (« sonore » disparu)", lib)
            await a.ev("(() => { const r = document.getElementById('visVolume'); r.value = 100; r.dispatchEvent(new Event('input')); r.dispatchEvent(new Event('change')); })()")
            await asyncio.sleep(2.1)
            ws3 = await ws_client("Dora", "D" * 24)
            t3 = asyncio.ensure_future(ecoute(ws3))
            await a.attendre("window.__au.peaks.length >= 7", 10)
            rapport(abs(max((await a.ev("window.__au.peaks"))[-3:]) - 0.25) < 1e-6, "volume 100 : crête de gain 0,25", await a.ev("window.__au.peaks.slice(-3)"))
            mem = await a.ev("JSON.parse(localStorage.getItem('glb2html_visitor'))")
            rapport(mem.get("volume") == 100 and mem.get("sounds") is True, "volume mémorisé", mem)
            # Sons décoché : plus aucun son
            await a.ev("(() => { const c = document.getElementById('visSounds'); c.checked = false; c.dispatchEvent(new Event('change')); })()")
            rapport(await a.ev("document.getElementById('visVolume').disabled"), "Sons décoché : le volume est grisé")
            n0 = await a.ev("window.__au.osc.length")
            await asyncio.sleep(2.1)
            ws4 = await ws_client("Eve", "E" * 24)
            t4 = asyncio.ensure_future(ecoute(ws4))
            await a.attendre("window.__viewer.getPresence().peers.some(p => p.name === 'Eve')", 10)
            await ws4.send(json.dumps({"t": "chat", "text": "Alice ?"}))
            await ws3.close()
            await a.pg.wait_for_timeout(700)
            rapport(await a.ev("window.__au.osc.length") == n0, "« Sons » décoché : ni arrivée, ni départ, ni citation", (n0, await a.ev("window.__au.osc.length")))
            # cases individuelles
            await a.ev("(() => { const c = document.getElementById('visSounds'); c.checked = true; c.dispatchEvent(new Event('change')); const j = document.getElementById('visSoundJoin'); j.checked = false; j.dispatchEvent(new Event('change')); })()")
            n0 = await a.ev("window.__au.osc.length")
            await asyncio.sleep(2.1)
            ws5 = await ws_client("Fred", "F" * 24)
            t5 = asyncio.ensure_future(ecoute(ws5))
            await a.attendre("window.__viewer.getPresence().peers.some(p => p.name === 'Fred')", 10)
            await a.pg.wait_for_timeout(400)
            rapport(await a.ev("window.__au.osc.length") == n0, "case « arrivée » décochée : pas de son à l'arrivée", (n0, await a.ev("window.__au.osc.length")))
            await ws5.close()
            await a.attendre(f"window.__au.osc.length > {n0}", 10)
            rapport(True, "… mais le départ sonne encore")
            rapport(not a.errs, "aucune erreur JavaScript", a.errs)
            await a.ctx.close()
            for w_ in (ws0, ws2, ws4):
                await w_.close()
            for t_ in (t0, t1, t2, t3, t4, t5):
                t_.cancel()
            # anciens réglages ignorés
            b = await Onglet(br).ouvrir(base_url + "Cone", init=STUB + AUDIO + VIS_OFF(color=None, bold=True, blink=True, sound=False))
            await b.ev("document.getElementById('optsBtn').click()")
            rapport(await b.ev("document.getElementById('visSoundCite').checked") is True, "l'ancien réglage « sound » est ignoré : la nouvelle valeur par défaut (cochée) s'applique")
            await b.ctx.close()

            # ================= 7. arrivée occupée =================
            print("--- 7. arrivée occupée (deux navigateurs, vrai presence_server.py)")
            A = await Onglet(br).ouvrir(base_url + "Cone#spawn=default", init=STUB + "try { localStorage.setItem('glb2html_name', 'Alice'); } catch (e) {}")
            await A.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await A.pg.wait_for_timeout(1300)   # le serveur reçoit la position (rappel toutes les secondes)
            pa = (await A.gw())["pos"]
            rapport(dist_h(pa, (0, 0, 0)) < 0.2, "le premier arrive à l'arrivée et ne bouge pas", pa)
            B = await Onglet(br).ouvrir(base_url + "Cone#spawn=default", init=STUB + "try { localStorage.setItem('glb2html_name', 'Bob'); } catch (e) {}")
            await B.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await B.pg.wait_for_timeout(1500)
            pb = (await B.gw())["pos"]
            rapport(dist_h(pb, pa) >= 1.0 and dist_h(pb, pa) < 2.0 and abs(pb[1] - FLOOR) < 1.01, f"le second arrive au même point : décalé à {dist_h(pb, pa):.2f} m du premier (anneau de 1,2 m)", (pa, pb))
            pa2 = (await A.gw())["pos"]
            rapport(dist_h(pa2, pa) < 0.01, "le premier n'a pas bougé", (pa, pa2))
            # R
            await B.ev("window.__viewer.teleportTo([12, 0, 12], 0)")
            await B.ticks(20)
            rapport(dist_h((await B.gw())["pos"], pa) > 5, "(Bob s'éloigne)")
            await B.touche("KeyR")
            await B.ticks(20)
            pb = (await B.gw())["pos"]
            rapport(dist_h(pb, pa) >= 1.0 and dist_h(pb, (0, 0, 0)) < 2.0, f"R : retour à l'arrivée occupée, décalé à {dist_h(pb, pa):.2f} m", pb)
            # Aller à vers le point du premier
            await B.ev("window.__viewer.teleportTo([12, 0, 12], 0)")
            await B.ticks(20)
            await B.ev("(t) => { const i = document.getElementById('gotoIn'); i.value = t; document.getElementById('gotoBtn').click(); }", f"{pa[0]:.1f}, {pa[1]:.1f}, {pa[2]:.1f}")
            await B.ticks(20)
            pb = (await B.gw())["pos"]
            rapport(dist_h(pb, pa) >= 1.0 and dist_h(pb, pa) < 2.0, f"« Aller à » vers le point du premier : décalé à {dist_h(pb, pa):.2f} m", pb)
            # portail interne vers une arrivée occupée
            await A.ev("window.__viewer.teleportTo([6, 0, 6], 0)")
            await A.ticks(20)
            await A.pg.wait_for_timeout(1300)
            await B.ev("window.__viewer.teleportTo([-10, 0, 13.6], 0)")
            await B.ticks(20)
            await B.tenir(["KeyW"], 8, 0.1)   # on entre dans le rayon du portail « porte » : arrivée « autre » (6, 6), occupée par Alice
            await B.pg.wait_for_timeout(1500)
            await B.ticks(20)
            pb = (await B.gw())["pos"]
            rapport(dist_h(pb, (6, 15, 6)) < 2.5 and dist_h(pb, (await A.gw())["pos"]) >= 1.0, f"portail interne vers une arrivée occupée : décalé à {dist_h(pb, (await A.gw())['pos']):.2f} m", pb)
            await A.ctx.close(); await B.ctx.close()
            # attente de la liste : déplacement seulement si l'avatar n'a pas bougé de plus de 0,3 m
            A = await Onglet(br).ouvrir(base_url + "Cone#spawn=default", init=STUB)
            await A.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await A.pg.wait_for_timeout(1300)
            pa = (await A.gw())["pos"]
            C1 = await Onglet(br).ouvrir(base_url + "NoSpec", init=STUB + DELAY, viewer=True)
            await C1.ev("window.__wsDelay = 2500")
            await C1.ev("window.__viewer.walkStart({ pos: [0, 15, 0], yaw: 0 })")
            await C1.attendre("window.__viewer.walking", 10)
            p0 = (await C1.gw())["pos"]
            await C1.pg.wait_for_timeout(5000)
            await C1.attendre("window.__viewer.getPresence().peers.length >= 1", 20)
            p1 = (await C1.gw())["pos"]
            rapport(dist_h(p0, (0, 0, 0)) < 0.1 and dist_h(p1, pa) >= 1.0, f"liste reçue après la pose (retard de 2,5 s), avatar immobile : déplacé à {dist_h(p1, pa):.2f} m", (p0, p1))
            await C1.ctx.close()
            C2 = await Onglet(br).ouvrir(base_url + "NoSpec", init=STUB + DELAY, viewer=True)
            await C2.ev("window.__wsDelay = 3000")
            await C2.ev("window.__viewer.walkStart({ pos: [0, 15, 0], yaw: 0 })")
            await C2.attendre("window.__viewer.walking", 10)
            await C2.tenir(["KeyW"], 10, 0.1)   # marche pendant l'attente
            pm = (await C2.gw())["pos"]
            await C2.attendre("window.__viewer.getPresence().peers.length >= 1", 20)
            await C2.ticks(2)
            pm2 = (await C2.gw())["pos"]
            rapport(dist_h(pm, (0, 0, 0)) > 1 and dist_h(pm2, pm) < 0.5, "quelqu'un qui marche n'est jamais déplacé à la réception de la liste", (pm, pm2))
            await C2.ctx.close(); await A.ctx.close()
            # sans place libre : pas de blocage
            A = await Onglet(br).ouvrir(base_url + "Petit#spawn=default", init=STUB)
            await A.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await A.pg.wait_for_timeout(1300)
            B = await Onglet(br).ouvrir(base_url + "Petit#spawn=default", init=STUB)
            await B.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await B.pg.wait_for_timeout(1500)
            pa, pb = (await A.gw())["pos"], (await B.gw())["pos"]
            rapport(dist_h(pb, (0, 0, 0)) < 0.2, "sol minuscule, aucune place libre à moins de 3,6 m : le nouvel arrivant est posé à l'endroit demandé (pas de blocage)", (pa, pb))
            await A.ctx.close(); await B.ctx.close()
        finally:
            proc.terminate()
            await br.close()
    print("\nRÉSULTAT : " + ("tout est passé" if not bad else f"{bad} échec(s)"))
    presence.terminate()
    sys.exit(1 if bad else 0)


asyncio.run(main())
