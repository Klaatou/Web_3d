#!/usr/bin/env python3
"""Tests v34 : panneau d'aide sélectionnable et bloc d'état, zone de survol des marqueurs, vol (Page Haut / Page Bas, atterrissage, bouton),
souris libre après Échap, couleur en direct (vrai presence_server.py), lien personnel (#name= / #key=), pseudo de la page carte, glb2html.py --maj.

Pages ouvertes dans Chromium sans tête (région plate synthétique, coquille commune). Le verrouillage du pointeur est simulé par un
faux requestPointerLock / exitPointerLock (déterministe) : ce que fait le vrai navigateur à Échap est reproduit par exitPointerLock().

Prérequis : pip install playwright websockets ; python build.py avant.
Variables facultatives : THREE_DIR (paquet npm three, hors ligne), CHROMIUM (chemin de l'exécutable).
Lancer : python tests/v34.py
"""
import asyncio, json, os, pathlib, re, shutil, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
import glbfab

DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_v34_"))
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


def html(*a, ok=True):
    return run(DIST / "glb2html.py", *a, *vend, ok=ok)


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


# ---------- fabrication ----------
print("--- 0. fabrication des pages")
presence, pport = lancer_presence()
PURL = f"ws://127.0.0.1:{pport}"
site = tmp / "site"
site.mkdir()
sol_glb(site / "sol.glb")
ZL = [
    {"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0.0},
    {"id": "lien", "type": "url", "label": "Lien test", "target": "https://example.org/", "x": 0, "y": 15, "z": -8, "radius": 3},
    {"id": "hover", "type": "url", "label": "Zone survol", "target": "https://example.org/h", "x": 12, "y": 15, "z": 12, "radius": 3},
]
(tmp / "z.json").write_text(json.dumps(ZL), encoding="utf-8")
base = ["--shared-shell", "--zones", tmp / "z.json", "--no-sea", "--target", "0,0,0", "--presence-url", PURL, "--room", "t34", *vend]
html(site / "sol.glb", "-o", site / "Portee.html", *base, "--zone-marker", "portee", "--register", site / "regions.json", "--map-page", "carte.html")
html(site / "sol.glb", "-o", site / "Discret.html", *base)
html(site / "sol.glb", "-o", site / "NoFly.html", *base, "--no-fly")
shell_txt = (site / "index.html").read_text(encoding="utf-8")
rapport(True, "pages générées (portée, discret, sans vol)")

STUB = """(() => {
  let el = null; window.__plCalls = 0;
  Object.defineProperty(document, 'pointerLockElement', { get: () => el, configurable: true });
  Element.prototype.requestPointerLock = function () { window.__plCalls++; el = this; setTimeout(() => document.dispatchEvent(new Event('pointerlockchange')), 0); };
  document.exitPointerLock = () => { el = null; setTimeout(() => document.dispatchEvent(new Event('pointerlockchange')), 0); };
  window.__open = []; window.open = (u) => { window.__open.push(u); return null; };
})();"""
PROJ = """(p) => { const c = window.__viewer.camera; c.updateMatrixWorld(true); const v = new c.position.constructor(p[0], p[1], p[2]).project(c);
  return [(v.x + 1) / 2 * innerWidth, (1 - v.y) / 2 * innerHeight]; }"""


class Onglet:
    def __init__(self, br):
        self.br, self.errs = br, []

    async def ouvrir(self, url, init=STUB, ctx=None, viewer=True):
        self.ctx = ctx or await self.br.new_context(viewport={"width": 1000, "height": 700})
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

    async def walk(self, pos=(0, 15, 0), yaw=0):
        await self.ev("([p, y]) => window.__viewer.walkStart({ pos: p, yaw: y })", [list(pos), yaw])
        await self.pg.wait_for_function("window.__viewer.walking", timeout=10000)

    async def gw(self):
        return await self.ev("window.__viewer.getWalk()")

    async def tenir(self, touches, n, dt=0.1):
        return await self.ev("""([keys, n, dt]) => { const v = window.__viewer, out = [], k = (t, c) => window.dispatchEvent(new KeyboardEvent(t, { code: c }));
            keys.forEach(c => k('keydown', c));
            for (let i = 0; i < n; i++) { v.walkTick(dt); const w = v.getWalk(); out.push({ pos: w.pos, flying: w.flying, grounded: w.grounded }); }
            keys.forEach(c => k('keyup', c));
            return out; }""", [touches, n, dt])

    async def txt(self, ident):
        return await self.ev("(i) => document.getElementById(i).textContent", ident)


async def tip(pg):
    return await pg.evaluate("(() => { const e = document.getElementById('zoneTip'); return e && !e.hidden ? e.innerText : null; })()")


async def survol(pg, pos):
    pt = await pg.evaluate(PROJ, pos)
    await pg.mouse.move(pt[0] - 40, pt[1] - 40)
    await pg.wait_for_timeout(80)
    await pg.mouse.move(*pt)
    await pg.wait_for_timeout(120)
    await pg.mouse.move(pt[0] + 1, pt[1])
    await pg.wait_for_timeout(120)
    return await tip(pg)


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
            # ================= 1. panneau d'aide et bloc d'état =================
            print("--- 1. panneau d'aide sélectionnable, bloc d'état")
            o = await Onglet(br).ouvrir(base_url + "Discret")
            await o.walk()
            aide, etat = await o.txt("walkHint"), await o.txt("stateInfo")
            rapport(all(s not in aide for s in ("Vue :", "Mode :", "Position", "Tuiles", "Souris :")), "l'aide ne contient plus ni vue, ni mode, ni position, ni tuiles", aide[:300])
            rapport("Vue : subjective" in etat and "Mode : à pied" in etat and "Position avatar : x" in etat and "Souris :" in etat, "le bloc d'état contient vue, mode, souris, position", etat)
            rapport("· au sol" not in etat and "· au sol" not in aide, "plus d'étiquette « Vue : … · au sol »")
            rapport(await o.ev("document.getElementById('viewInfo').textContent === 'Vue : subjective' && document.getElementById('modeInfo').textContent === 'Mode : à pied'"), "étiquettes séparées « Vue : … » et « Mode : à pied »")
            pe = await o.ev("({ h: getComputedStyle(document.getElementById('walkHint')).pointerEvents, s: getComputedStyle(document.getElementById('stateInfo')).pointerEvents, us: getComputedStyle(document.getElementById('walkHint')).userSelect })")
            rapport(pe["h"] != "none" and pe["s"] != "none" and pe["us"] != "none", "l'aide et l'état reçoivent la souris et ne bloquent pas la sélection", pe)
            for ident in ("walkHint", "stateInfo"):
                r = await o.ev("(i) => { const e = document.getElementById(i).children[1].firstElementChild, b = e.getBoundingClientRect(); return [b.left + 20, b.top + b.height / 2]; }", ident)
                await o.pg.mouse.click(r[0], r[1], click_count=3)
                sel = await o.ev("window.getSelection().toString()")
                rapport(len(sel.strip()) > 8, f"triple-clic dans #{ident} : texte sélectionné ({len(sel.strip())} caractères)", sel)
            # Ctrl+C : la touche C ne doit pas être bloquée (preventDefault) ; la touche C seule oui (descendre)
            res = await o.ev("""() => { const mk = (ctrl) => new KeyboardEvent('keydown', { code: 'KeyC', ctrlKey: ctrl, cancelable: true, bubbles: true });
                const a = window.dispatchEvent(mk(true)), b = window.dispatchEvent(mk(false)); window.dispatchEvent(new KeyboardEvent('keyup', { code: 'KeyC' })); return [a, b]; }""")
            rapport(res == [True, False], "Ctrl+C n'est pas intercepté (copie possible) ; C seule reste interceptée", res)
            # H masque l'aide, l'état reste ; I masque l'état
            await o.pg.keyboard.press("h")
            rapport(await o.ev("document.getElementById('walkHint').hidden && !document.getElementById('stateInfo').hidden"), "H masque l'aide, le bloc d'état reste affiché")
            await o.pg.keyboard.press("i")
            rapport(await o.ev("document.getElementById('stateInfo').hidden"), "I masque le bloc d'état")
            await o.pg.keyboard.press("i")
            await o.pg.keyboard.press("h")
            rapport(await o.ev("!document.getElementById('stateInfo').hidden && !document.getElementById('walkHint').hidden"), "I puis H les réaffichent")
            rapport("I : informations" in aide and "G : reprendre" in aide and "Page Haut" in aide and "Page Bas" in aide, "l'aide liste I, G, Page Haut / Page Bas (v35 : groupes courts, plus d'explication de la sélection)", aide[:900])
            rapport(not o.errs, "aucune erreur JavaScript", o.errs)
            await o.ctx.close()

            # ================= 2. survol des marqueurs =================
            print("--- 2. zone de survol et de clic des marqueurs")
            for nom, tests in (("Portee", [(1.5, True), (2.8, True), (4.0, False)]), ("Discret", [(0.8, True), (2.0, False)])):
                o = await Onglet(br).ouvrir(base_url + nom)
                await o.ev("(() => { const v = window.__viewer; v.camera.position.set(0, 45, -5); v.controls.target.set(0, 15, -8); v.controls.update(); v.camera.updateMatrixWorld(true); })()")
                await o.pg.wait_for_timeout(400)
                for d, attendu in tests:
                    t = await survol(o.pg, [d, 15.06, -8])
                    ok = (t is not None and t.split("\n")[0] == "Lien test") == attendu
                    rapport(ok, f"marqueur « {nom.lower()} » : survol à {d} m du centre (rayon 3 m) : infobulle {'attendue' if attendu else 'absente'}", t)
                await o.ctx.close()

            # ================= 3. vol =================
            print("--- 3. vol : Page Haut / Page Bas, atterrissage, bouton")
            o = await Onglet(br).ouvrir(base_url + "Discret")
            rapport(await o.ev("document.getElementById('flyBtn').hidden && document.getElementById('grabBtn').hidden"), "boutons de vol et de souris cachés hors promenade")
            await o.walk()
            rapport(await o.ev("!document.getElementById('flyBtn').hidden && !document.getElementById('grabBtn').hidden"), "boutons « Voler / Atterrir » et « Capturer la souris » visibles en promenade")
            prevenu = await o.ev("() => [window.dispatchEvent(new KeyboardEvent('keydown', { code: 'PageUp', cancelable: true })), window.dispatchEvent(new KeyboardEvent('keydown', { code: 'PageDown', cancelable: true }))]")
            await o.ev("window.dispatchEvent(new KeyboardEvent('keyup', { code: 'PageUp' })); window.dispatchEvent(new KeyboardEvent('keyup', { code: 'PageDown' }))")
            rapport(prevenu == [False, False], "Page Haut et Page Bas : preventDefault pendant la promenade (pas de défilement)", prevenu)
            await o.ev("window.dispatchEvent(new KeyboardEvent('keydown', { code: 'Home' })); window.dispatchEvent(new KeyboardEvent('keyup', { code: 'Home' }))")
            w = await o.gw()
            rapport(w["flying"] and await o.txt("modeInfo") == "Mode : en vol" and await o.txt("viewInfo") == "Vue : subjective", "Début : vol, « Mode : en vol », la vue ne change pas", await o.txt("modeInfo"))
            m = await o.tenir(["PageUp"], 20)
            monte = m[-1]["pos"][1] - m[0]["pos"][1]
            rapport(6.0 <= monte <= 8.0, f"Page Haut monte (+{monte:.2f} m en 2 s à 3,5 m/s)", monte)
            m = await o.tenir(["PageDown"], 10)
            desc = m[0]["pos"][1] - m[-1]["pos"][1]
            rapport(2.5 <= desc <= 4.0 and m[-1]["flying"], f"Page Bas descend (-{desc:.2f} m en 1 s), toujours en vol", desc)
            m = await o.tenir(["PageDown"], 40)
            fin = m[-1]
            rapport(not fin["flying"] and fin["grounded"] and abs(fin["pos"][1] - 15) < 0.01 and min(q["pos"][1] for q in m) >= 14.999, "descendre jusqu'au sol : atterrissage automatique, jamais sous le sol", (fin, min(q["pos"][1] for q in m)))
            rapport(await o.txt("modeInfo") == "Mode : à pied", "après atterrissage : « Mode : à pied »")
            m = await o.tenir(["KeyW"], 10)
            rapport(not m[-1]["flying"], "marcher ensuite : toujours à pied")
            await o.ev("document.getElementById('flyBtn').click()")
            w = await o.gw()
            rapport(w["flying"] and await o.txt("modeInfo") == "Mode : en vol" and await o.ev("document.getElementById('flyBtn').getAttribute('aria-pressed')") == "true", "bouton « Voler / Atterrir » : décolle")
            m = await o.tenir(["PageUp"], 10)
            rapport(m[-1]["pos"][1] - m[0]["pos"][1] > 2.5, "Page Haut monte (v36 : E ne monte plus)")
            m = await o.tenir(["KeyC"], 40)
            rapport(not m[-1]["flying"] and abs(m[-1]["pos"][1] - 15) < 0.01, "C jusqu'au sol : atterrit aussi")
            await o.ev("document.getElementById('flyBtn').click()")
            await o.ev("document.getElementById('flyBtn').click()")
            rapport(not (await o.gw())["flying"], "bouton deux fois : décolle puis atterrit")
            rapport(not o.errs, "aucune erreur JavaScript", o.errs)
            await o.ctx.close()
            o = await Onglet(br).ouvrir(base_url + "NoFly")
            await o.walk()
            rapport(await o.ev("document.getElementById('flyBtn').hidden") and "Page Haut" not in await o.txt("walkHint"), "--no-fly : pas de bouton de vol, l'aide ne propose pas Page Haut")
            await o.ctx.close()

            # ================= 4. souris libre =================
            print("--- 4. souris libre après Échap")
            o = await Onglet(br).ouvrir(base_url + "Discret")
            await o.walk()
            rapport(await o.ev("window.__viewer.mouseState") == "idle" and "Souris : clic dans la vue" in await o.txt("mouseInfo"), "entrée en promenade : souris ni capturée ni libre (« clic dans la vue »)", await o.txt("mouseInfo"))
            await o.pg.mouse.click(500, 350)
            await o.pg.wait_for_timeout(100)
            rapport(await o.ev("window.__plCalls") == 1 and await o.ev("window.__viewer.mouseState") == "captured" and "capturée" in await o.txt("mouseInfo"), "premier clic : verrouillage demandé (comportement d'avant)", await o.ev("[window.__plCalls, window.__viewer.mouseState, document.elementFromPoint(500, 350).outerHTML.slice(0, 160)]"))
            await o.ev("document.exitPointerLock()")   # ce que fait Échap
            await o.pg.wait_for_timeout(100)
            rapport(await o.ev("window.__viewer.mouseState") == "free" and "Souris : libre" in await o.txt("mouseInfo"), "Échap : état « souris libre » affiché dans le bloc d'état", await o.txt("mouseInfo"))
            n0 = await o.ev("window.__plCalls")
            await o.pg.mouse.click(500, 350)
            await o.pg.wait_for_timeout(500)
            rapport(await o.ev("window.__plCalls") == n0, "souris libre : un clic simple ne redemande pas le verrouillage")
            # zone « Lien test » en (0, 0, -8) : clic sur la zone
            pt = await o.pg.evaluate(PROJ, [0, 15.06, -8])
            await o.pg.mouse.click(*pt)
            await o.pg.wait_for_timeout(200)
            rapport(await o.ev("window.__open.length") == 1 and await o.ev("window.__plCalls") == n0, "souris libre : clic sur une zone fonctionne, sans verrouillage", await o.ev("window.__open"))
            # double-clic loin : téléportation à l'endroit du curseur
            cible = [-6, 15, -6]
            pt = await o.pg.evaluate(PROJ, cible)
            await o.pg.wait_for_timeout(500)
            await o.pg.mouse.dblclick(*pt)
            await o.pg.wait_for_timeout(300)
            w = await o.gw()
            rapport(abs(w["pos"][0] - cible[0]) < 1.0 and abs(w["pos"][2] - cible[2]) < 1.0 and await o.ev("window.__plCalls") == n0, f"souris libre : double-clic = téléportation à l'endroit du curseur (x {w['pos'][0]:.2f}, z {w['pos'][2]:.2f}), pointeur non reverrouillé", w["pos"])
            rapport(await o.ev("window.__viewer.mouseState") == "free", "l'état reste « libre »")
            # glisser-déposer : la vue tourne
            y0 = (await o.gw())["yaw"]
            await o.ev("""() => { const cv = document.querySelector('canvas'); cv.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: 500, clientY: 300 }));
                window.dispatchEvent(new MouseEvent('mousemove', { movementX: 60, movementY: 0 })); window.dispatchEvent(new MouseEvent('mouseup')); }""")
            y1 = (await o.gw())["yaw"]
            rapport(abs(y1 - y0) > 0.05, f"souris libre : glisser-déposer bouton enfoncé tourne la vue (Δyaw {y1 - y0:.3f})")
            # déplacement de la souris sans bouton : la vue ne tourne pas
            await o.ev("window.dispatchEvent(new MouseEvent('mousemove', { movementX: 60, movementY: 0 }))")
            rapport(abs((await o.gw())["yaw"] - y1) < 1e-9, "souris libre sans bouton : la vue ne tourne pas")
            await o.pg.keyboard.press("g")
            await o.pg.wait_for_timeout(100)
            rapport(await o.ev("window.__plCalls") == n0 + 1 and await o.ev("window.__viewer.mouseState") == "captured", "touche G : recapture la souris")
            await o.ev("document.exitPointerLock()")
            await o.pg.wait_for_timeout(100)
            await o.ev("document.getElementById('grabBtn').click()")
            await o.pg.wait_for_timeout(100)
            rapport(await o.ev("window.__plCalls") == n0 + 2 and await o.ev("window.__viewer.mouseState") == "captured", "bouton « Capturer la souris » : recapture")
            await o.ev("document.exitPointerLock()")
            await o.pg.wait_for_timeout(100)
            await o.ev("window.__viewer.walkStop()")
            await o.pg.wait_for_timeout(100)
            await o.walk()
            rapport(await o.ev("window.__viewer.mouseState") == "idle", "nouvelle entrée en promenade : l'état « libre » est réinitialisé")
            await o.pg.mouse.click(500, 350)
            await o.pg.wait_for_timeout(100)
            rapport(await o.ev("window.__plCalls") == n0 + 3, "…et le premier clic redemande le verrouillage")
            rapport(not o.errs, "aucune erreur JavaScript", o.errs)
            await o.ctx.close()

            # ================= 5. couleur en direct =================
            print("--- 5. couleur en direct (vrai presence_server.py)")
            A = await Onglet(br).ouvrir(base_url + "Discret#name=Alice")
            B = await Onglet(br).ouvrir(base_url + "Discret#name=Bob")
            await A.walk((0, 15, 0))
            await B.walk((3, 15, 0))
            for x in (A, B):
                await x.pg.wait_for_function("window.__viewer.getPresence().state === 'online'", timeout=15000)
            await A.pg.wait_for_function("window.__viewer.getPresence().peers.length === 1", timeout=15000)
            await B.pg.wait_for_function("window.__viewer.getPresence().peers.length === 1", timeout=15000)
            c0 = (await B.ev("window.__viewer.getPresence().peers[0].color"))
            await A.ev("""() => { const cb = document.getElementById('visColorOn'); cb.checked = true; cb.dispatchEvent(new Event('change'));
                const i = document.getElementById('visColor'); i.value = '#ff2200'; i.dispatchEvent(new Event('input')); }""")
            try:
                await B.pg.wait_for_function("window.__viewer.getPresence().peers[0].color === 0xff2200", timeout=10000)
            except Exception:
                print("DEBUG", await A.ev("[localStorage.getItem('glb2html_visitor'), window.__viewer.getPresence().state, document.getElementById('visColorOn').checked]"), await B.ev("window.__viewer.getPresence().peers"))
                presence.terminate(); print(presence.stdout.read()[-1500:]); raise
            teintes = await B.ev("""() => { const o = []; window.__viewer.scene.traverse(n => { if (n.userData && n.userData.tint && n.material) o.push(n.material.color.getHex()); }); return o; }""")
            rapport(c0 != 0xff2200 and teintes.count(0xff2200) >= 2, "B voit l'avatar de A changer de couleur en direct (corps et losange)", (hex(c0), teintes))
            await A.ev("window.__viewer.setView('tps')")
            teintes = await A.ev("""() => { const o = []; window.__viewer.scene.traverse(n => { if (n.userData && n.userData.tint && n.material) o.push(n.material.color.getHex()); }); return o; }""")
            rapport(0xff2200 in teintes and await A.ev("window.__viewer.getWalk().selfVisible"), "l'avatar de A (troisième personne) prend la couleur choisie", teintes)
            # un nouveau venu voit la couleur courante (hello / join)
            C = await Onglet(br).ouvrir(base_url + "Discret#name=Carl")
            await C.walk((5, 15, 0))
            await C.pg.wait_for_function("window.__viewer.getPresence().peers.length === 2", timeout=15000)
            cols = await C.ev("window.__viewer.getPresence().peers.map(q => [q.name, q.color])")
            rapport(any(n == "Alice" and c == 0xff2200 for n, c in cols), "un visiteur qui arrive ensuite voit la couleur courante de A", cols)
            rapport(not (A.errs or B.errs or C.errs), "aucune erreur JavaScript", A.errs + B.errs + C.errs)
            for x in (A, B, C):
                await x.ctx.close()
            # serveur : messages bruts
            import websockets

            async def raw(name, uid):
                ws = await websockets.connect(PURL)
                await ws.send(json.dumps({"t": "hello", "room": "t34raw", "name": name, "uid": uid * 20}))
                w = json.loads(await ws.recv())
                return ws, w

            async def lire(ws, t=0.6):
                out = []
                try:
                    while True:
                        out.append(json.loads(await asyncio.wait_for(ws.recv(), t)))
                except Exception:
                    return out

            w1, m1 = await raw("Ann", "a")
            w2, m2 = await raw("Ben", "b")
            await lire(w1)
            await lire(w2)
            await w1.send(json.dumps({"t": "color", "color": 0x123456}))
            recu = [m for m in await lire(w2) if m.get("t") == "color"]
            rapport(recu and recu[0]["color"] == 0x123456 and recu[0]["id"] == m1["id"], "serveur : {t:'color'} valide diffusé aux autres, avec l'identifiant de l'auteur", recu)
            await lire(w1)
            for faux in ("rouge", -1, 0x1000000, True, 1.5, None, [1], {"a": 1}):
                await w1.send(json.dumps({"t": "color", "color": faux}))
                await asyncio.sleep(0.25)
            recu = [m for m in await lire(w2) if m.get("t") == "color"]
            rapport(not recu, "serveur : valeurs invalides (texte, négatif, > 0xFFFFFF, booléen, flottant, null, liste, objet) ignorées sans bruit", recu)
            w3, m3 = await raw("Cat", "c")
            peers = {q["name"]: q["color"] for q in m3["peers"]}
            rapport(peers.get("Ann") == 0x123456, "serveur : le nouveau venu reçoit la couleur à jour dans « welcome »", peers)
            await w1.send(json.dumps({"t": "color", "color": 0x654321}))
            await w1.send(json.dumps({"t": "color", "color": 0x111111}))   # trop rapproché (< 0,2 s) : ignoré
            recu = [m["color"] for m in await lire(w2) if m.get("t") == "color"]
            rapport(recu == [0x654321], "serveur : au plus un changement toutes les 0,2 s", recu)
            wa = await websockets.connect(PURL)
            await wa.send(json.dumps({"t": "hello", "room": "t34raw", "name": "Spec", "uid": "s" * 20, "spectator": True}))
            await wa.recv()
            await wa.send(json.dumps({"t": "color", "color": 0x0A0B0C}))
            await asyncio.sleep(0.3)
            rapport(not [m for m in await lire(w2, 0.4) if m.get("t") == "color"], "serveur : un spectateur qui change de couleur ne diffuse rien")
            for x in (w1, w2, w3, wa):
                await x.close()

            # ================= 6. lien personnel =================
            print("--- 6. lien personnel (#name= et #key=)")
            A = await Onglet(br).ouvrir(base_url + "Discret#name=Lola", init=None)
            await A.walk((0, 15, 0))
            await A.pg.wait_for_function("window.__viewer.getPresence().state === 'online'", timeout=15000)
            uidA = await A.ev("localStorage.getItem('glb2html_uid')")
            rapport(re.fullmatch(r"[0-9a-f]{32}", uidA or "") is not None, "A : clé d'identité du navigateur (32 caractères hexadécimaux)", uidA)
            nomA = await A.ev("window.__viewer.getName()")
            rapport(nomA == "Lola", "#name=Lola règle le pseudo (déjà géré par la coquille)", nomA)
            await A.ev("document.getElementById('optsBtn').click()")
            await A.ev("document.getElementById('visLinkBtn').click()")
            lien = await A.ev("document.getElementById('visLinkOut').value")
            rapport(lien.endswith(f"#name=Lola&key={uidA}") and "?region=Discret" in lien, "« Copier mon lien personnel » : adresse de la page + #name=PSEUDO&key=CLE", lien)
            panneau = await A.ev("document.getElementById('optsPanel').textContent")
            rapport("secret" in panneau and "prend ton identité" in panneau, "le panneau dit que ce lien est un secret")
            # B : navigateur vierge qui ouvre le lien
            B = await Onglet(br).ouvrir(lien, init=None)
            uidB = await B.ev("localStorage.getItem('glb2html_uid')")
            rapport(uidB == uidA, "B (navigateur vierge) adopte la clé du lien", (uidA, uidB))
            rapport(await B.ev("location.hash") == "#name=Lola" and "key" not in await B.ev("location.href"), "la clé est retirée de l'adresse visible (le pseudo reste)", await B.ev("location.href"))
            await B.walk((4, 15, 0))
            await B.pg.wait_for_function("window.__viewer.getPresence().state === 'online'", timeout=15000)
            rapport(await B.ev("window.__viewer.getName()") == "Lola", "B obtient le même nom réservé « Lola » alors que A est connecté", await B.ev("window.__viewer.getName()"))
            # C : autre navigateur vierge, même pseudo mais sa propre clé : nom différent
            C = await Onglet(br).ouvrir(base_url + "Discret#name=Lola", init=None)
            await C.walk((8, 15, 0))
            await C.pg.wait_for_function("window.__viewer.getPresence().state === 'online'", timeout=15000)
            nomC = await C.ev("window.__viewer.getName()")
            rapport(nomC != "Lola" and nomC.startswith("Lola"), "contre-épreuve : un autre navigateur avec #name=Lola obtient un nom différent", nomC)
            # D : navigateur qui a déjà une clé différente : confirmation à l'écran
            D = await Onglet(br).ouvrir(base_url + "Discret", init=None)
            uidD = await D.ev("localStorage.getItem('glb2html_uid')")
            await D.pg.goto("about:blank"); await D.pg.goto(lien)
            await D.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            visible = await D.ev("!document.getElementById('modal').hidden")
            texte = await D.ev("document.getElementById('modalText').textContent")
            rapport(visible and "remplace" in texte and await D.ev("localStorage.getItem('glb2html_uid')") == uidD, "clé différente déjà présente : message de confirmation à l'écran, rien n'est changé avant la réponse", texte)
            rapport("key" not in await D.ev("location.href"), "…et la clé est déjà retirée de l'adresse visible")
            await D.ev("document.getElementById('modalNo').click()")
            rapport(await D.ev("localStorage.getItem('glb2html_uid')") == uidD and await D.ev("document.getElementById('modal').hidden"), "Annuler : la clé du navigateur est gardée")
            await D.pg.goto("about:blank"); await D.pg.goto(lien)
            await D.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            await D.ev("document.getElementById('modalYes').click()")
            rapport(await D.ev("localStorage.getItem('glb2html_uid')") == uidA and await D.ev("window.__viewer.getUid()") == uidA, "Oui : la clé du navigateur devient celle du lien")
            E = await Onglet(br).ouvrir(base_url + "Discret#name=Eve&key=pas-une-cle", init=None)
            uidE = await E.ev("localStorage.getItem('glb2html_uid')")
            rapport(re.fullmatch(r"[0-9a-f]{32}", uidE) is not None and "key" not in await E.ev("location.href") and await E.ev("document.getElementById('modal').hidden"), "clé au mauvais format : ignorée, retirée de l'adresse, aucune confirmation", uidE)
            rapport(not (A.errs or B.errs or C.errs or D.errs or E.errs), "aucune erreur JavaScript", A.errs + B.errs + C.errs + D.errs + E.errs)
            for x in (A, B, C, D, E):
                await x.ctx.close()

            # ================= 7. page carte =================
            print("--- 7. page carte : pseudo")
            o = await Onglet(br).ouvrir(f"http://127.0.0.1:{port}/carte.html", init=None, viewer=False)
            await o.pg.wait_for_selector("a.tile")
            href0 = await o.ev("document.querySelector('a.tile').href")
            rapport("name=" not in href0 and "spawn=default" in href0, "sans pseudo : le lien garde seulement #spawn=", href0)
            await o.pg.fill("#pseudo", "Zoé & Cie")
            href1 = await o.ev("document.querySelector('a.tile').href")
            rapport(href1.endswith("spawn=default&name=" + "Zo%C3%A9%20%26%20Cie"), "pseudo saisi : #spawn=…&name=PSEUDO (encodé)", href1)
            await o.pg.reload()
            await o.pg.wait_for_selector("a.tile")
            rapport(await o.ev("document.getElementById('pseudo').value") == "Zoé & Cie" and "name=Zo%C3%A9" in await o.ev("document.querySelector('a.tile').href"), "le pseudo est mémorisé dans le navigateur")
            rapport(not o.errs, "aucune erreur JavaScript", o.errs)
            await o.ctx.close()
        finally:
            proc.kill()
            presence.kill()
            await br.close()


# ================= 8. --maj =================
print("--- 8. glb2html.py --maj")
src = tmp / "region"
src.mkdir()
glbfab.region(src / "Syn.glb")
run(DIST / "glb2tiles.py", src / "Syn.glb", "--nopause", "--forcer", "--budget-tri", "900", "--min", "64", "--entier-etendue", "50")
mj = tmp / "maj"
mj.mkdir()
zonesm = [{"id": "default", "type": "spawn", "x": 3, "y": 15, "z": 4, "yaw": 0.5}, {"id": "u", "type": "url", "label": "Lien", "target": "https://example.org/", "x": 9, "y": 15, "z": 9, "radius": 2}]
(tmp / "zm.json").write_text(json.dumps(zonesm), encoding="utf-8")
html("-o", mj / "Syn.html", "--shared-shell", "--tiles", src / "Syn.tiles.json", "--zones", tmp / "zm.json", "--presence-url", "ws://ADRESSE:9", "--room", "salonm", "--wave", "1.5")
fresh = (mj / "index.html").read_bytes()
cfgp, zp = mj / "Syn.config.json", mj / "Syn.zones.json"
cfg0 = json.loads(cfgp.read_text(encoding="utf-8"))
# modifications à la main : valeurs et clé inconnue ; zones modifiées à la main ; ancienne coquille
cfg0.update(hole=99.0, walkSpeed=5.0, seaY=3.0, version="v33 (22/10/2026)", zzCustom={"a": [1, 2]}, zoneMarker="portee")
cfgp.write_text(json.dumps(cfg0, indent=1), encoding="utf-8")
zdoc = json.loads(zp.read_text(encoding="utf-8"))
zdoc.append({"id": "main", "type": "url", "label": "Ajoutée à la main", "target": "https://example.org/m", "x": 1, "y": 15, "z": 1, "radius": 2})
zp.write_text(json.dumps(zdoc, indent=1), encoding="utf-8")
zbytes = zp.read_bytes()
vieille = b"<!-- coquille v33 -->" + fresh
(mj / "index.html").write_bytes(vieille)
(mj / "Autre.config.json").write_text("{}", encoding="utf-8")
libdir = mj / "lib"
lib_avant = sorted(str(q.relative_to(mj)) for q in libdir.rglob("*") if q.is_file())
r = html("--maj", "-o", mj / "Syn.html", "--shared-shell", "--tiles", src / "Syn.tiles.json", "--sea-y", "12")
cfg1 = json.loads(cfgp.read_text(encoding="utf-8"))
diff = {k for k in set(cfg0) | set(cfg1) if cfg0.get(k) != cfg1.get(k)}
rapport(diff == {"seaY", "version"} and cfg1["seaY"] == 12.0, "--maj --sea-y 12 : seules seaY et la version changent dans X.config.json", (diff, r.stdout[-400:]))
rapport(cfg1["hole"] == 99.0 and cfg1["walkSpeed"] == 5.0 and cfg1["zzCustom"] == {"a": [1, 2]} and cfg1["zoneMarker"] == "portee" and cfg1["presenceUrl"] == "ws://ADRESSE:9" and cfg1["room"] == "salonm" and cfg1["wave"] == 1.5,
        "valeurs modifiées à la main, clé inconnue, salon, présence et vagues : conservés")
rapport(cfg1["version"] == (ROOT / "VERSION").read_text(encoding="utf-8").strip() and cfg1["tiles"] == cfg0["tiles"], "version courante écrite, champ « tiles » conservé", cfg1["version"])
rapport(zp.read_bytes() == zbytes, "X.zones.json : octet pour octet identique (zones ajoutées à la main gardées)")
sauv = sorted(mj.glob("index.avant-*.html"))
rapport(len(sauv) == 1 and sauv[0].read_bytes() == vieille, "l'ancienne coquille est gardée sous un nom daté", [q.name for q in sauv])
rapport((mj / "index.html").read_bytes() == fresh, "la coquille est renouvelée (identique à celle de la version courante)")
rapport("renouvelée" in r.stdout and "partagée par les autres régions" in r.stdout and sauv and sauv[0].name in r.stdout, "le compte rendu le dit en clair (coquille partagée, copie gardée)", r.stdout)
rapport(sorted(str(q.relative_to(mj)) for q in libdir.rglob("*") if q.is_file()) == lib_avant and (mj / "Autre.config.json").read_text() == "{}", "lib/ et les autres régions du dossier : inchangés")
rapport("seaY" in r.stdout and "12" in r.stdout, "le compte rendu liste les clés changées", r.stdout)
# valeur égale au défaut mais donnée explicitement : appliquée
r = html("--maj", "-o", mj / "Syn.html", "--shared-shell", "--sea-y", "-50")
cfg2 = json.loads(cfgp.read_text(encoding="utf-8"))
rapport(cfg2["seaY"] == -50.0 and cfg2["hole"] == 99.0 and len(list(mj.glob("index.avant-*.html"))) == 1, "--sea-y -50 (valeur par défaut, mais donnée) : appliquée ; coquille à jour : pas de nouvelle copie", cfg2["seaY"])
# aucune option : seule la version
cfgp.write_text(json.dumps(dict(cfg2, version="v33 (22/10/2026)"), indent=1), encoding="utf-8")
html("--maj", "-o", mj / "Syn.html", "--shared-shell")
cfg3 = json.loads(cfgp.read_text(encoding="utf-8"))
rapport({k for k in set(cfg2) | set(cfg3) if cfg2.get(k) != cfg3.get(k)} == set(), "--maj sans autre option : tout est conservé, version remise à jour")
# présence : la vue globale suit l'adresse
html("--maj", "-o", mj / "Syn.html", "--shared-shell", "--presence-url", "ws://ADRESSE:10", "--room", "autre")
cfg4 = json.loads(cfgp.read_text(encoding="utf-8"))
rapport(cfg4["presenceUrl"] == "ws://ADRESSE:10" and cfg4["room"] == "autre" and cfg4["spectate"] is True and cfg4["hole"] == 99.0, "--maj --presence-url / --room : appliqués")
# sans config : échec avec la commande sans --maj
r = html("--maj", "-o", mj / "Inconnue.html", "--shared-shell", "--tiles", src / "Syn.tiles.json", ok=False)
rapport(r.returncode != 0 and "sans --maj" in r.stderr and "--tiles" in r.stderr and not (mj / "Inconnue.config.json").exists(), "sans X.config.json : échec, message qui propose la commande sans --maj", r.stderr)
r = html("--maj", ok=False)
rapport(r.returncode != 0 and "-o" in r.stderr, "--maj sans -o : refusé", r.stderr)
r = html("--maj", "--settings", "x.json", "-o", mj / "Syn.html", ok=False)
rapport(r.returncode != 0 and "s'excluent" in r.stderr, "--maj avec --settings : refusé", r.stderr)
# page sans coquille commune : refus clair si la page est absente
r = html("--maj", "-o", mj / "Syn.html", ok=False)
rapport(r.returncode != 0 and "--shared-shell" in r.stderr, "--maj sans --shared-shell alors que Syn.html n'existe pas : message qui propose --shared-shell", r.stderr)
# --zones donné : réécrit
html("--maj", "-o", mj / "Syn.html", "--shared-shell", "--zones", tmp / "zm.json")
rapport(len(json.loads(zp.read_text(encoding="utf-8"))) == 2, "--maj --zones FICHIER : réécrit X.zones.json")
# la page mise à jour s'ouvre (tuiles) sans erreur
async def ouvrir_maj():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        proc, port = serveur(mj)
        try:
            o = await Onglet(br).ouvrir(f"http://127.0.0.1:{port}/index.html?region=Syn", init=None)
            await o.pg.wait_for_function("window.__viewer.tilesState && window.__viewer.tilesState().loaded > 0", timeout=60000)
            rapport(not o.errs, "région en tuiles mise à jour par --maj : la page s'ouvre, des tuiles se chargent, aucune erreur JavaScript", o.errs)
            await o.ctx.close()
        finally:
            proc.kill()
            await br.close()



if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(ouvrir_maj())
    print("\nRÉSULTAT : " + ("tout est passé" if not bad else f"{bad} échec(s)"))
    sys.exit(1 if bad else 0)
