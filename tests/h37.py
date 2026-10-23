"""Aide commune des tests v37 (copie des outils de tests/v36.py : fabrication, serveurs, onglet de navigateur)."""
import asyncio, json, math, os, pathlib, re, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
os.environ["WEB3D_LANG"] = "fr"

DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_v37_"))
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
        self.br, self.errs, self.logs = br, [], []

    async def ouvrir(self, url, init=STUB, ctx=None, viewer=True, locale=LOC, **ctxopts):
        ctxopts.setdefault("viewport", {"width": 1000, "height": 700})
        self.ctx = ctx or await self.br.new_context(locale=locale, **ctxopts)
        if init:
            await self.ctx.add_init_script(init)
        self.pg = await self.ctx.new_page()
        self.pg.on("pageerror", lambda e: self.errs.append(str(e)))
        self.pg.on("console", lambda m: self.errs.append("console.error " + m.text) if m.type == "error" and "WebSocket" not in m.text and "404" not in m.text else None)
        self.pg.on("console", lambda m: self.logs.append(m.text))
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


def resultat():
    return bad
