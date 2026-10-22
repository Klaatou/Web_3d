#!/usr/bin/env python3
"""Tests v33 : démarrage avec une arrivée (tuiles lourdes), arrivée par défaut, retour, #pos=, « Aller à », vol, trois vues de caméra,
chat persistant / enregistré / pseudo cité / complétion, couleur (client et serveur), --log-ip raw, marqueurs de zones, zones enregistrées dans le dossier.

Région synthétique de 16 tuiles (tests/glbfab.py region_lourde) dont DEUX tuiles de plus d'un million de triangles (23 Mo chacune) :
« Chateau » (arrivée #spawn=chateau, coin de la région, loin de la cible de caméra par défaut) et « Cathedrale » (arrivée « default », près du centre).
Le serveur de présence est le vrai (dist/presence_server.py) ; les pages sont ouvertes dans Chromium sans tête.

Prérequis : pip install playwright websockets ; python build.py avant.
Variables facultatives : THREE_DIR (paquet npm three, hors ligne), CHROMIUM (chemin de l'exécutable).
Lancer : python tests/v33.py
"""
import asyncio, json, math, os, pathlib, re, shutil, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
import glbfab
from glbfab import hauteur

DIST, DATA = ROOT / "dist", ROOT / "tests" / "data"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_v33_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
bad = 0
MESURES = []


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)), flush=True)


def run(script, *a, cwd=None, ok=True, stdin=None):
    r = subprocess.run([sys.executable, str(script), *map(str, a)], capture_output=True, text=True, cwd=cwd or tmp, input=stdin)
    if ok and r.returncode:
        sys.exit(f"[ECHEC] {script.name} {' '.join(map(str, a))}\n{r.stdout}{r.stderr}")
    return r


def html(*a, ok=True):
    return run(DIST / "glb2html.py", *a, *vend, ok=ok)


def port_libre():
    with socket.socket() as so:
        so.bind(("127.0.0.1", 0))
        return so.getsockname()[1]


def serveur(dossier):
    port = port_libre()
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=dossier, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return proc, port
        except OSError:
            time.sleep(0.1)
    proc.kill()
    sys.exit("[ECHEC] http.server ne démarre pas")


def lancer_presence(*extra, script=None):
    port = port_libre()
    proc = subprocess.Popen([sys.executable, str(script or DIST / "presence_server.py"), "--host", "127.0.0.1", "--port", str(port), "--identities", "", *extra],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=tmp)
    for _ in range(80):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return proc, port
        except OSError:
            time.sleep(0.1)
    proc.kill()
    sys.exit("[ECHEC] presence_server ne démarre pas")


def proche(a, b, tol=0.5):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


# ---------- fabrication : GLB de tuiles lourdes -> tuiles -> pages ----------
print("--- 0. région synthétique de tuiles lourdes")
src = tmp / "source"
src.mkdir()
centres = glbfab.region_lourde(src / "Lourde.glb")
r = run(DIST / "glb2tiles.py", src / "Lourde.glb", "--forcer", "--budget-tri", "300", "--min", "160", "--entier-poids", "64", "--nopause")
doc = json.loads((src / "Lourde.tiles.json").read_text(encoding="utf-8"))
TILES = doc["tiles"]
lourdes = [t for t in TILES if t["triangles"] > 1_000_000]
rapport(len(TILES) == 16 and len(lourdes) == 2, f"{len(TILES)} tuiles dont {len(lourdes)} de plus d'un million de triangles", (len(TILES), [t["triangles"] for t in TILES]))


def boite(t, x, z, m=0.5):
    return t["min"][0] - m <= x <= t["max"][0] + m and t["min"][2] - m <= z <= t["max"][2] + m


def tuile_de(x, z):
    return next(t["file"] for t in TILES if boite(t, x, z))


CHX, CHY, CHZ = centres["Chateau"]
DFX, DFY, DFZ = centres["Cathedrale"]
T_CHATEAU, T_DEFAUT = tuile_de(CHX, CHZ), tuile_de(DFX, DFZ)
NOM = lambda f: f.split("/")[-1]
ZL = [
    {"id": "chateau", "type": "spawn", "x": CHX, "y": CHY, "z": CHZ, "yaw": 0.0},
    {"id": "default", "type": "spawn", "x": DFX, "y": DFY, "z": DFZ, "yaw": 1.0},
    {"id": "libre", "type": "url", "label": "Lien libre", "target": "https://example.org/", "x": DFX + 12, "y": DFY, "z": DFZ, "radius": 3},
    {"id": "p1", "type": "portal", "label": "Vers le château", "target": "", "spawn": "chateau", "trigger": "enter", "x": DFX - 10, "y": DFY, "z": DFZ, "radius": 2.5},
]
(tmp / "zl.json").write_text(json.dumps(ZL), encoding="utf-8")
(tmp / "vide.json").write_text("[]", encoding="utf-8")
site = tmp / "site"
site.mkdir()
html("-o", site / "Lourde.html", "--shared-shell", "--tiles", src / "Lourde.tiles.json", "--zones", tmp / "zl.json")
TJ = site / "Lourde.tiles.json"
html("-o", site / "Cible.html", "--shared-shell", "--tiles", TJ, "--zones", tmp / "zl.json", "--target", "300,20,0")
html("-o", site / "Libre.html", "--shared-shell", "--tiles", TJ, "--zones", tmp / "vide.json")
html("-o", site / "MarkP.html", "--shared-shell", "--tiles", TJ, "--zones", tmp / "zl.json", "--zone-marker", "portee")
html("-o", site / "MarkA.html", "--shared-shell", "--tiles", TJ, "--zones", tmp / "zl.json", "--zone-marker", "aucun")
html("-o", site / "MarkS.html", "--shared-shell", "--tiles", TJ, "--zones", tmp / "zl.json", "--show-spawns")
html("-o", site / "NoFly.html", "--shared-shell", "--tiles", TJ, "--zones", tmp / "zl.json", "--no-fly")
# configuration d'avant la v33 (aucune des clés nouvelles) : comportement d'avant
vieux = json.loads((site / "Lourde.config.json").read_text(encoding="utf-8"))
for k in ("zoneMarker", "showSpawns", "fly", "targetExplicit"):
    vieux.pop(k)
vieux["target"] = [300, 20, 0]
(site / "Vieux.config.json").write_text(json.dumps(vieux), encoding="utf-8")
shutil.copy(site / "Lourde.zones.json", site / "Vieux.zones.json")
cfg = json.loads((site / "Lourde.config.json").read_text(encoding="utf-8"))
rapport(cfg["zoneMarker"] == "discret" and cfg["showSpawns"] is False and cfg["fly"] is True and cfg["targetExplicit"] is False, "config par défaut : zoneMarker discret, showSpawns faux, fly vrai, targetExplicit faux", {k: cfg.get(k) for k in ("zoneMarker", "showSpawns", "fly", "targetExplicit")})
cc = json.loads((site / "Cible.config.json").read_text(encoding="utf-8"))
rapport(cc["targetExplicit"] is True and cc["target"] == [300, 20, 0], "--target explicite : targetExplicit vrai", cc["targetExplicit"])
cp = json.loads((site / "MarkP.config.json").read_text(encoding="utf-8"))
cs = json.loads((site / "MarkS.config.json").read_text(encoding="utf-8"))
rapport(cp["zoneMarker"] == "portee" and cs["showSpawns"] is True and json.loads((site / "NoFly.config.json").read_text(encoding="utf-8"))["fly"] is False, "--zone-marker, --show-spawns, --no-fly : écrits dans la config")
r = html("-o", site / "X.html", "--shared-shell", "--tiles", TJ, "--zone-marker", "gros", ok=False)
rapport(r.returncode != 0 and "zone-marker" in r.stderr, "--zone-marker avec une valeur inconnue : refusé", r.stderr[-200:])
r = html("--help")
rapport(all(o in r.stdout for o in ("--zone-marker", "--show-spawns", "--fly")), "--help décrit --zone-marker, --show-spawns, --fly")

# sol plat pour les essais en mode GLB unique
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


glbdir = tmp / "glb"
glbdir.mkdir()
sol_glb(glbdir / "sol.glb")
(glbdir / "z.json").write_text(json.dumps([{"id": "default", "type": "spawn", "x": 12, "y": 15, "z": -12, "yaw": 1.0}]), encoding="utf-8")
run(DIST / "glb2html.py", glbdir / "sol.glb", "-o", glbdir / "defaut.html", "--zones", glbdir / "z.json", "--no-sea", *vend)
run(DIST / "glb2html.py", glbdir / "sol.glb", "-o", glbdir / "cible.html", "--zones", glbdir / "z.json", "--no-sea", "--target", "1,15,1", *vend)


class Onglet:
    """Une page ouverte ; garde[fichier] = Event à lever pour libérer la réponse ; retard[fichier] = secondes ; logs = lignes console « [tuile] »."""

    def __init__(self, br):
        self.br, self.errs, self.logs, self.demandes, self.garde, self.retard = br, [], [], [], {}, {}

    async def ouvrir(self, url, cpu=1, init=None, viewport=(900, 600), downloads=False):
        self.ctx = await self.br.new_context(viewport={"width": viewport[0], "height": viewport[1]}, accept_downloads=downloads)
        if init:
            await self.ctx.add_init_script(init)
        self.pg = await self.ctx.new_page()
        self.pg.on("pageerror", lambda e: self.errs.append(str(e)))
        self.pg.on("console", lambda m: self.logs.append(m.text) if m.text.startswith("[tuile]") else (self.errs.append("console.error " + m.text) if m.type == "error" and "404" not in m.text and "WebSocket" not in m.text else None))
        if cpu > 1:
            cdp = await self.ctx.new_cdp_session(self.pg)
            await cdp.send("Emulation.setCPUThrottlingRate", {"rate": cpu})
        await self.pg.route("**/*.glb", self.route)
        self.t0 = time.time()
        await self.pg.goto(url)
        return self

    async def route(self, route):
        nom = route.request.url.split("/")[-1]
        self.demandes.append(nom)
        if nom in self.retard:
            await asyncio.sleep(self.retard[nom])
        if nom in self.garde:
            await self.garde[nom].wait()
        try:
            await route.continue_()
        except Exception:
            pass

    async def ev(self, js, arg=None):
        return await self.pg.evaluate(js, arg)

    async def attendre(self, cond, timeout=60):
        await self.pg.wait_for_function(cond, timeout=timeout * 1000)

    async def marcheur(self, timeout=120):
        await self.attendre("window.__viewer && window.__viewer.walking", timeout)
        return time.time() - self.t0

    async def walk(self):
        return await self.ev("window.__viewer.getWalk()")

    async def tenir(self, touches, n, dt=0.1):
        """Enfonce les touches (codes), n pas de walkTick(dt), les relâche ; rend la liste des {pos, cam, flying, view}."""
        return await self.ev("""([keys, n, dt]) => { const v = window.__viewer, out = [], k = (t, c) => window.dispatchEvent(new KeyboardEvent(t, { code: c }));
            keys.forEach(c => k('keydown', c));
            for (let i = 0; i < n; i++) { v.walkTick(dt); const w = v.getWalk(); out.push({ pos: w.pos, cam: w.cam, yaw: w.yaw, flying: w.flying, grounded: w.grounded }); }
            keys.forEach(c => k('keyup', c));
            return out; }""", [touches, n, dt])

    async def touche(self, code):
        await self.ev("(c) => window.dispatchEvent(new KeyboardEvent('keydown', { code: c }))", code)
        await self.ev("(c) => window.dispatchEvent(new KeyboardEvent('keyup', { code: c }))", code)

    async def tp(self, x, y, z, yaw=0, attente=40):
        """Téléportation (attend la tuile) ; rend quand l'avatar est arrivé."""
        await self.ev("([x, y, z, yaw]) => window.__viewer.teleportTo([x, y, z], yaw)", [x, y, z, yaw])
        await self.attendre(f"(() => {{ const w = window.__viewer.getWalk().pos; return Math.hypot(w[0] - {x}, w[2] - {z}) < 1; }})()", attente)

    async def fermer(self):
        await self.ctx.close()


def sol_lourde(x, z):
    """Hauteur du sol attendue (terrain, ou dalle des tuiles lourdes : +3 m)."""
    h = hauteur(x, z)
    for cx, cz in ((CHX, CHZ), (DFX, DFZ)):
        if abs(x - cx) <= 50 and abs(z - cz) <= 50:
            return h + 0.1
    return h


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        proc, port = serveur(site)
        base = f"http://127.0.0.1:{port}/index.html?region="
        try:
            # ================= 1. démarrage avec #spawn= (tuiles lourdes) =================
            print("--- 1. démarrage #spawn=chateau, tuiles lourdes, processeur ralenti (x6)")
            o = Onglet(br)
            await o.ouvrir(base + "Lourde#spawn=chateau", cpu=6)
            await o.attendre("window.__viewer && !document.getElementById('groundWait').hidden", 20)
            txt = await o.ev("document.getElementById('groundWait').textContent")
            noir = await o.ev("document.getElementById('fade').classList.contains('on')")
            rapport(noir and re.search(r"^Chargement du sol… .*\d+ s", txt) is not None, "écran noir : le texte « Chargement du sol… » est affiché dès le début, avec le temps écoulé", txt)
            try:
                await o.attendre("/Chargement du sol… \\d+\\/\\d+ tuile/.test(document.getElementById('groundWait').textContent)", 20)
                txt = await o.ev("document.getElementById('groundWait').textContent")
                ok_txt = True
            except Exception:
                ok_txt = False
            rapport(ok_txt, "le texte donne les tuiles prêtes sur les tuiles attendues (n/m tuile)", txt)
            etat = await o.ev("window.__viewer.tilesState()")
            rapport(etat["anchor"] is not None and [NOM(f) for f in etat["anchor"]["files"]] == [NOM(T_CHATEAU)], "pendant l'attente, la référence du chargeur est l'arrivée (tuile du château), pas la cible de caméra", etat["anchor"])
            tps = await o.marcheur(120)
            w = await o.walk()
            rapport(tps < 60 and proche([w["pos"][0], w["pos"][2]], [CHX, CHZ], 0.6), f"l'avatar arrive au bon point après {tps:.1f} s (processeur x6) — avant la correction : plus de 120 s à x10", (tps, w["pos"]))
            etat = await o.ev("window.__viewer.tilesState()")
            log = etat["log"]
            rapport(log and NOM(log[0]["file"]) == NOM(T_CHATEAU), "la tuile de l'arrivée est la première prête", [NOM(x["file"]) for x in log[:3]])
            first = log[0]["at"] if log else 0
            rapport(all(x["startAt"] >= first - 5 for x in log[1:]), "aucune autre tuile ne démarre avant que celle de l'arrivée soit prête", [(NOM(x["file"]), x["startAt"], first) for x in log[1:4]])
            rapport(o.demandes.count(NOM(T_CHATEAU)) == 1, "la tuile de l'arrivée n'est demandée qu'une fois (pas d'annulation, pas de nouvelle tentative)", o.demandes)
            await o.attendre("!document.getElementById('fade').classList.contains('on')", 10)
            rapport(etat["anchor"] is None, "promenade démarrée : l'ancre est libérée, le fondu est retiré")
            lourd = next((x for x in log if x["file"].endswith(NOM(T_CHATEAU))), None)
            rapport(lourd is not None and all(k in lourd for k in ("downloadMs", "parseMs", "queueMs", "gridMs", "gridWallMs", "startWaitMs", "totalMs", "tri", "bytes")), "journal par tuile : octets, triangles, téléchargement, analyse, attente en file, construction de la grille", lourd)
            ligne = next((l for l in o.logs if NOM(T_CHATEAU) in l and "prête" in l), "")
            rapport(all(m in ligne for m in ("Mo", "triangles", "téléchargement", "analyse du GLB", "attente en file de grille", "construction de la grille", "total")), "console : une ligne [tuile] par tuile prête, avec tous les temps", ligne)
            if lourd:
                MESURES.append(("x6", lourd))
            # grille de la tuile de l'avatar d'abord (même si d'autres sont arrivées avant dans la file)
            await o.attendre("window.__viewer.tilesState().loadingFiles.length === 0 && window.__viewer.tilesState().gridQueue === 0", 60)
            n0 = len((await o.ev("window.__viewer.tilesState()"))["log"])
            await o.ev("window.__viewer.refreshCollision()")
            await o.attendre(f"window.__viewer.tilesState().log.length > {n0}", 60)
            nouv = (await o.ev("window.__viewer.tilesState().log"))[n0:]
            rapport(NOM(nouv[0]["file"]) == NOM(T_CHATEAU), "file des grilles : la tuile qui contient l'avatar passe avant les autres (5 tuiles prêtes, la sienne en 4e position)", [NOM(x["file"]) for x in nouv[:4]])
            rapport(not o.errs, "aucune erreur JavaScript", o.errs)
            await o.fermer()

            print("--- 1 bis. tuile d'arrivée lente (6 s de réseau, au-delà des 4 s d'avant)")
            o = Onglet(br)
            o.retard[NOM(T_CHATEAU)] = 6
            await o.ouvrir(base + "Lourde#spawn=chateau")
            tps = await o.marcheur(60)
            w = await o.walk()
            rapport(tps < 30 and proche([w["pos"][0], w["pos"][2]], [CHX, CHZ], 0.6), f"réseau lent : l'avatar arrive au bon point ({tps:.1f} s)", (tps, w["pos"]))
            rapport(o.demandes.count(NOM(T_CHATEAU)) == 1, "réseau lent : la tuile n'est pas abandonnée puis redemandée", o.demandes)
            await o.fermer()

            print("--- 1 ter. tuile retenue plus de 15 s : le noir est retiré, le texte reste, la promenade démarre dès qu'elle est prête")
            o = Onglet(br)
            o.garde[NOM(T_CHATEAU)] = asyncio.Event()
            await o.ouvrir(base + "Lourde#spawn=chateau")
            await asyncio.sleep(3)
            rapport(await o.ev("document.getElementById('fade').classList.contains('on') && !document.getElementById('groundWait').hidden"), "à 3 s : écran noir, avec le texte")
            await o.attendre("!document.getElementById('fade').classList.contains('on')", 30)
            t_noir = time.time() - o.t0
            etat = await o.ev("({ ov: window.__viewer.tilesState().overview, walking: window.__viewer.walking, gw: !document.getElementById('groundWait').hidden, txt: document.getElementById('groundWait').textContent })")
            rapport(14 <= t_noir <= 25 and etat["ov"]["state"] == "ready" and etat["ov"]["visible"] and not etat["walking"] and etat["gw"] and "Chargement du sol…" in etat["txt"],
                    f"après {t_noir:.1f} s : noir retiré, vue d'ensemble visible, texte « Chargement du sol… » toujours là", etat)
            m = re.search(r"(\d+) s", etat["txt"])
            rapport(m is not None and int(m.group(1)) >= 12, "le texte donne le temps écoulé", etat["txt"])
            o.garde[NOM(T_CHATEAU)].set()
            await o.marcheur(60)
            w = await o.walk()
            rapport(proche([w["pos"][0], w["pos"][2]], [CHX, CHZ], 0.6), "tuile libérée : la promenade démarre au bon point", w["pos"])
            await o.attendre("document.getElementById('groundWait').hidden", 10)
            await o.fermer()

            # ================= 2. arrivée par défaut, retour, #pos, aller à, vol, vues =================
            print("--- 2. ouverture sans lien : arrivée « default »")
            o = Onglet(br)
            await o.ouvrir(base + "Lourde")
            await o.attendre("document.getElementById('msg') === null", 60)
            tgt = await o.ev("window.__viewer.controls.target.toArray()")
            rapport(proche([tgt[0], tgt[2]], [DFX, DFZ], 0.01) and abs(tgt[1] - DFY) < 0.01, "sans lien : la page est cadrée sur l'arrivée « default » (la cible devient sa position)", tgt)
            await o.attendre(f"window.__viewer.tilesState().ready.some(f => f.endsWith('{NOM(T_DEFAUT)}'))", 60)
            etat = await o.ev("window.__viewer.tilesState()")
            rapport(NOM(etat["log"][0]["file"]) == NOM(T_DEFAUT) and all(x["startAt"] >= etat["log"][0]["at"] - 5 for x in etat["log"][1:]), "la tuile de cette arrivée est chargée la première, avant toute autre", [NOM(x["file"]) for x in etat["log"][:3]])
            await o.touche("KeyF")
            await o.attendre("window.__viewer.walking", 20)
            w = await o.walk()
            rapport(proche([w["pos"][0], w["pos"][2]], [DFX, DFZ], 0.3) and abs(w["yaw"] - 1.0) < 1e-6, "F démarre au point de l'arrivée « default », avec son orientation", (w["pos"], w["yaw"]))
            aide = await o.ev("document.getElementById('walkHint').textContent")
            rapport(all(s in aide for s in ("Début : voler", "V : changer de vue", "R : retour à l'arrivée", "Aller à x, y, z", "repère du modèle d'origine")) and await o.ev("document.getElementById('viewInfo').textContent === 'Vue : subjective' && document.getElementById('modeInfo').textContent === 'Mode : à pied'"), "l'aide donne les touches (Début, E/C, V, R) et le champ « Aller à » avec son repère ; la vue et le mode sont dans le bloc d'état (v34)", aide[:600])

            print("--- 3. retour à l'arrivée")
            await o.tenir(["KeyW", "ShiftLeft"], 60)
            w = await o.walk()
            loin = math.hypot(w["pos"][0] - DFX, w["pos"][2] - DFZ)
            await o.touche("KeyR")
            await o.attendre(f"Math.hypot(window.__viewer.getWalk().pos[0] - {DFX}, window.__viewer.getWalk().pos[2] - {DFZ}) < 0.3", 20)
            w = await o.walk()
            rapport(loin > 20 and abs(w["yaw"] - 1.0) < 1e-6, f"touche R en promenade : retour à l'arrivée (parti à {loin:.0f} m), orientation de l'arrivée", (loin, w["yaw"]))
            await o.tp(CHX, CHY, CHZ, 0)
            await o.ev("window.__viewer.releaseKeys()")
            await o.attendre(f"window.__viewer.tilesState().ready.some(f => f.endsWith('{NOM(T_CHATEAU)}'))", 30)
            await o.attendre(f"!window.__viewer.tilesState().ready.some(f => f.endsWith('{NOM(T_DEFAUT)}'))", 30)
            await o.ev("document.getElementById('homeBtn').click()")
            vu = False
            for _ in range(200):
                if await o.ev("!document.getElementById('groundWait').hidden && /Chargement du sol…/.test(document.getElementById('groundWait').textContent)"):
                    vu = True
                    break
                if await o.ev(f"Math.hypot(window.__viewer.getWalk().pos[0] - {DFX}, window.__viewer.getWalk().pos[2] - {DFZ}) < 0.3"):
                    break
                await asyncio.sleep(0.05)
            await o.attendre(f"Math.hypot(window.__viewer.getWalk().pos[0] - {DFX}, window.__viewer.getWalk().pos[2] - {DFZ}) < 0.3", 40)
            rapport(vu, "bouton « Retour à l'arrivée » vers une tuile déchargée : « Chargement du sol… » pendant l'attente, puis l'avatar arrive")
            # vue globale : recadre
            await o.touche("KeyP")   # v35 : F bascule le vol, P sort de la promenade
            await o.attendre("!window.__viewer.walking", 10)
            await o.ev("window.__viewer.goTo([500, 15, -100])")
            t1 = await o.ev("window.__viewer.controls.target.toArray()")
            await o.touche("KeyR")
            t2 = await o.ev("window.__viewer.controls.target.toArray()")
            rapport(proche([t1[0], t1[2]], [500, -100], 0.01) and proche([t2[0], t2[2]], [DFX, DFZ], 0.01), "vue globale : R recadre la cible sur l'arrivée", (t1, t2))
            rapport(await o.ev("document.getElementById('walkHint').textContent.includes('R : recadrer')"), "aide en vue globale : « R : recadrer » (v35 : groupes courts)")
            rapport(not o.errs, "aucune erreur JavaScript", o.errs)
            await o.fermer()

            print("--- 3 bis. --target explicite, configuration d'avant, région sans arrivée")
            o = Onglet(br)
            await o.ouvrir(base + "Cible")
            await o.attendre("document.getElementById('msg') === null", 60)
            tgt = await o.ev("window.__viewer.controls.target.toArray()")
            rapport(proche(tgt, [300, 20, 0], 0.01), "--target explicite : le cadrage reste la cible (priorité sur l'arrivée « default »)", tgt)
            await o.fermer()
            o = Onglet(br)
            await o.ouvrir(base + "Vieux")
            await o.attendre("document.getElementById('msg') === null", 60)
            tgt = await o.ev("window.__viewer.controls.target.toArray()")
            rapport(proche(tgt, [300, 20, 0], 0.01), "configuration d'avant la v33 (sans targetExplicit) : comportement d'avant, cadrage sur la cible", tgt)
            await o.fermer()
            o = Onglet(br)
            await o.ouvrir(base + "Libre")
            await o.attendre("document.getElementById('msg') === null", 60)
            t_libre = await o.ev("window.__viewer.controls.target.toArray()")
            cfg_libre = json.loads((site / "Libre.config.json").read_text(encoding="utf-8"))
            rapport(proche(t_libre, cfg_libre["target"], 0.01), "région sans arrivée : cadrage sur la cible de la configuration", (t_libre, cfg_libre["target"]))
            await o.attendre("window.__viewer.tilesState().ready.length > 0", 60)
            await o.touche("KeyF")
            await o.attendre("window.__viewer.walking", 30)
            w0 = await o.walk()
            await o.tenir(["KeyW", "ShiftLeft"], 40)
            await o.touche("KeyR")
            await o.attendre(f"Math.hypot(window.__viewer.getWalk().pos[0] - {w0['pos'][0]}, window.__viewer.getWalk().pos[2] - {w0['pos'][2]}) < 0.5", 20)
            rapport(True, "sans arrivée « default » : R ramène à la cible de départ")
            await o.fermer()

            print("--- 3 ter. mode GLB unique")
            for nom, attendu, expl in (("defaut", [12, 15, -12], False), ("cible", [1, 15, 1], True)):
                o = Onglet(br)
                await o.ouvrir((glbdir / f"{nom}.html").as_uri())
                await o.attendre("document.getElementById('msg') === null", 60)
                tgt = await o.ev("window.__viewer.controls.target.toArray()")
                rapport(proche(tgt, attendu, 0.05), f"GLB unique ({'--target explicite' if expl else 'arrivée default'}) : cadrage {attendu}", tgt)
                await o.touche("KeyF")
                await o.attendre("window.__viewer.walking", 10)
                w = await o.walk()
                if not expl:
                    rapport(proche([w["pos"][0], w["pos"][2]], [12, -12], 0.05) and abs(w["yaw"] - 1.0) < 1e-6, "GLB unique : F démarre à l'arrivée « default » avec son orientation", (w["pos"], w["yaw"]))
                    await o.tenir(["KeyW"], 10)
                    await o.touche("KeyR")
                    w = await o.walk()
                    rapport(proche([w["pos"][0], w["pos"][2]], [12, -12], 0.05), "GLB unique : R en promenade, retour à l'arrivée", w["pos"])
                    rapport("repère de cette page" in await o.ev("document.getElementById('walkHint').textContent"), "GLB unique : l'aide indique le repère de la page pour « Aller à »")
                else:
                    rapport(proche([w["pos"][0], w["pos"][2]], [1, 1], 0.05), "GLB unique, --target explicite : F démarre à la cible", w["pos"])
                await o.fermer()

            print("--- 4. #pos=, lien de position, aller à")
            o = Onglet(br)
            o.retard[NOM(tuile_de(620.5, -200))] = 1.2
            await o.ouvrir(base + "Lourde#pos=500,13,-100,1.5")
            await o.attendre("!document.getElementById('groundWait').hidden", 20)
            t = await o.marcheur(60)
            w = await o.walk()
            rapport(proche([w["pos"][0], w["pos"][2]], [500, -100], 0.3) and abs(w["yaw"] - 1.5) < 1e-6, f"#pos=500,13,-100,1.5 : arrivée anonyme à ce point, orientée ({t:.1f} s)", (w["pos"], w["yaw"]))
            etat = await o.ev("window.__viewer.tilesState()")
            rapport(etat["log"] and etat["log"][0]["file"].endswith(NOM(tuile_de(500, -100))), "#pos= : la tuile du point est la première chargée", [NOM(x["file"]) for x in etat["log"][:2]])
            # copier le lien
            await o.ev("document.getElementById('linkBtn').click()")
            await asyncio.sleep(0.5)
            lien = await o.ev("document.getElementById('linkOut').value")
            rapport(re.fullmatch(r"http://127\.0\.0\.1:\d+/index\.html\?region=Lourde#pos=-?[\d.]+,-?[\d.]+,-?[\d.]+,-?[\d.]+", lien) is not None, "« Copier le lien de ma position » : adresse de la page + #pos=x,y,z,yaw", lien)
            await o.tenir(["KeyW"], 15)
            w1 = await o.walk()
            await o.ev("document.getElementById('linkBtn').click()")
            await asyncio.sleep(0.5)
            lien = await o.ev("document.getElementById('linkOut').value")
            o2 = Onglet(br)
            await o2.ouvrir(lien)
            await o2.marcheur(60)
            w2 = await o2.walk()
            rapport(proche([w2["pos"][0], w2["pos"][2]], [w1["pos"][0], w1["pos"][2]], 0.02) and abs(w2["yaw"] - w1["yaw"]) < 0.01, "le lien copié rouvre la page exactement à la même position et orientation", (w1["pos"], w2["pos"]))
            await o2.fermer()
            # aller à (promenade)
            await o.ev("document.getElementById('gotoIn').value = '340,5 ; 15,0 ; 90,5'; document.getElementById('gotoBtn').click()")
            await o.attendre("Math.abs(window.__viewer.getWalk().pos[0] - 340.5) < 0.5 && Math.abs(window.__viewer.getWalk().pos[2] - 90.5) < 0.5", 40)
            rapport(True, "« Aller à » : « 340,5 ; 15,0 ; 90,5 » (décimale virgule, point-virgule) téléporte en x 340,5 z 90,5 (attente de la tuile comprise)")
            await o.attendre(f"!window.__viewer.tilesState().ready.some(f => f.endsWith('{NOM(T_CHATEAU)}'))", 30)
            await o.ev("document.getElementById('gotoIn').value = '620.5, 15, -200'; document.getElementById('gotoBtn').click()")
            vu = False
            for _ in range(100):
                if await o.ev("!document.getElementById('groundWait').hidden && /\\d+\\/\\d+ tuile/.test(document.getElementById('groundWait').textContent)"):
                    vu = True
                    break
                await asyncio.sleep(0.05)
            await o.attendre("Math.abs(window.__viewer.getWalk().pos[0] - 620.5) < 0.5", 40)
            rapport(vu, "« Aller à » vers une tuile non chargée : « Chargement du sol… n/m tuile » pendant l'attente, puis arrivée")
            await o.ev("document.getElementById('gotoIn').value = 'abc'; document.getElementById('gotoBtn').click()")
            rapport("Trois nombres" in await o.ev("document.getElementById('gotoMsg').textContent"), "« Aller à » : valeur invalide refusée avec un message")
            for bon, mauvais in (("1, 2, 3", False), ("1 2 3", False), ("1;2", True), ("1,2", True), ("", True)):
                rep = await o.ev("""(s) => { document.getElementById('gotoMsg').textContent = ''; document.getElementById('gotoIn').value = s; document.getElementById('gotoBtn').click(); return document.getElementById('gotoMsg').textContent; }""", bon)
                if not mauvais:
                    await asyncio.sleep(0.05)
                rapport(("Trois nombres" in rep) == mauvais, f"« Aller à » : « {bon} » {'refusé' if mauvais else 'accepté'}", rep)
            await o.touche("KeyP")   # v35 : F bascule le vol, P sort de la promenade
            await o.attendre("!window.__viewer.walking", 10)
            await o.ev("document.getElementById('gotoIn').value = '300.25, 14, 60.75'; document.getElementById('gotoBtn').click()")
            tt = await o.ev("window.__viewer.controls.target.toArray()")
            rapport(proche(tt, [300.25, 14, 60.75], 0.01), "« Aller à » en vue globale : la cible se déplace", tt)
            await o.ev("document.getElementById('linkBtn').click()")
            await asyncio.sleep(0.3)
            rapport("#pos=300.25,14,60.75," in await o.ev("document.getElementById('linkOut').value"), "lien de position en vue globale : la cible", await o.ev("document.getElementById('linkOut').value"))
            await o.fermer()
            o = Onglet(br)
            await o.ouvrir(base + "Lourde#pos=abc")
            await o.attendre("document.getElementById('msg') === null", 60)
            rapport(not await o.ev("window.__viewer.walking") and not await o.ev("document.getElementById('fade').classList.contains('on')"), "#pos= invalide : ignoré (pas d'arrivée)")
            await o.fermer()
            o = Onglet(br)
            await o.ouvrir(base + "Lourde#pos=1e9,2,3")
            await o.attendre("document.getElementById('msg') === null", 60)
            rapport(not await o.ev("window.__viewer.walking"), "#pos= hors bornes : ignoré")
            await o.fermer()

            # ---------- 5. vol, vues ----------
            print("--- 5. vol et vues de caméra")
            o = Onglet(br)
            await o.ouvrir(base + "Lourde#spawn=default")
            await o.marcheur(90)
            y0 = (await o.walk())["pos"][1]
            await o.touche("Home")
            w = await o.walk()
            rapport(w["flying"] and "Mode : en vol" in await o.ev("document.getElementById('modeInfo').textContent") and await o.ev("document.getElementById('viewInfo').textContent") == "Vue : subjective", "touche Début : décollage, indiqué en texte dans le bloc d'état (« Mode : en vol »)")
            m = await o.tenir(["KeyE"], 20)
            monte = m[-1]["pos"][1] - y0
            rapport(6.5 <= monte <= 7.5, f"en vol, E monte (+{monte:.2f} m en 2 s à 3,5 m/s)", monte)
            m = await o.tenir([], 30)
            rapport(abs(m[-1]["pos"][1] - m[0]["pos"][1]) < 1e-6 and not m[-1]["grounded"], "en vol, pas de gravité")
            await o.tenir(["KeyC"], 120)
            w = await o.walk()
            sol = sol_lourde(w["pos"][0], w["pos"][2])
            rapport(w["pos"][1] >= sol - 0.2 and w["pos"][1] <= sol + 0.6, f"en vol, C descend mais jamais sous le sol (y {w['pos'][1]:.2f}, sol {sol:.2f})", (w["pos"], sol))
            # v34 : descendre jusqu'au sol pose l'avatar tout seul (le second Début de la v33 n'est plus nécessaire)
            m = await o.tenir([], 30)
            w = await o.walk()
            rapport(not w["flying"] and w["grounded"] and abs(w["pos"][1] - sol_lourde(w["pos"][0], w["pos"][2])) < 0.6, "C jusqu'au sol : atterrissage automatique (v34), au sol", (w["flying"], w["grounded"], w["pos"][1]))
            # murs : Maison 0 (140, -240), cube 6 x 4 x 6 m, mur ouest à x = 137
            await o.tp(120, hauteur(120, -240), -240, -math.pi / 2)
            await o.touche("Home")
            g0 = hauteur(120, -240)
            await o.tenir(["KeyE"], 2)
            m = await o.tenir(["KeyW"], 120)
            xs = max(s["pos"][0] for s in m)
            rapport(120 < xs < 137.2, f"en vol bas (à {m[-1]['pos'][1] - hauteur(120, -240):.1f} m du sol) : le mur de la maison arrête l'avatar (x max {xs:.2f}, mur à 137)", xs)
            await o.tenir(["KeyE"], 25)
            m = await o.tenir(["KeyW"], 120)
            rapport(m[-1]["pos"][0] > 150, f"en vol haut (au-dessus du toit) : l'avatar passe (x {m[-1]['pos'][0]:.1f})", m[-1]["pos"])
            await o.touche("Home")
            await o.tenir([], 120)
            w = await o.walk()
            rapport(w["grounded"] and abs(w["pos"][1] - hauteur(w["pos"][0], w["pos"][2])) < 0.5, "atterrissage après la maison : posé sur le sol", (w["pos"], hauteur(w["pos"][0], w["pos"][2])))
            rapport(not o.errs, "vol : aucune erreur JavaScript", o.errs)

            print("--- 5 bis. trois vues de caméra")
            await o.tp(DFX, DFY, DFZ, 1.0)
            w = await o.walk()
            rapport(w["view"] == "fps" and not w["selfVisible"], "vue subjective au départ, avatar non dessiné")
            await o.touche("KeyV")
            w = await o.walk()
            d = math.hypot(w["cam"][0] - w["pos"][0], w["cam"][2] - w["pos"][2])
            rapport(w["view"] == "tps" and w["selfVisible"] and 3 < d < 4.1 and "troisième personne" in await o.ev("document.getElementById('viewInfo').textContent"), f"V : troisième personne (caméra à {d:.1f} m, avatar visible, vue indiquée en texte)", w)
            await o.ev("""() => { const c = window.__viewer.renderer.domElement; c.dispatchEvent(new MouseEvent('mousedown', { bubbles: true })); window.dispatchEvent(new MouseEvent('mousemove', { movementY: -800 })); window.dispatchEvent(new MouseEvent('mouseup')); }""")
            await o.tenir([], 2)
            w = await o.walk()
            sol_cam = sol_lourde(w["cam"][0], w["cam"][2])
            rapport(w["cam"][1] >= sol_cam + 0.25, f"troisième personne, regard vers le haut : la caméra ne traverse pas le sol (y {w['cam'][1]:.2f}, sol {sol_cam:.2f})", (w["cam"], sol_cam))
            await o.ev("""() => { const c = window.__viewer.renderer.domElement; c.dispatchEvent(new MouseEvent('mousedown', { bubbles: true })); window.dispatchEvent(new MouseEvent('mousemove', { movementY: 800 })); window.dispatchEvent(new MouseEvent('mouseup')); }""")
            await o.touche("KeyV")
            w = await o.walk()
            rapport(w["view"] == "free" and "caméra libre" in await o.ev("document.getElementById('viewInfo').textContent"), "V : caméra libre, indiquée en texte")
            p0, c0 = w["pos"], w["cam"]
            m = await o.tenir(["KeyW", "ArrowLeft"], 15)
            w = await o.walk()
            rapport(proche(w["pos"], p0, 1e-6) and math.dist(w["cam"], c0) > 3 and abs(w["yaw"] - 1.0) < 1e-6, "caméra libre : la caméra se déplace et tourne, l'avatar reste sur place", (w["pos"], w["cam"], w["yaw"]))
            await o.tenir(["KeyC"], 200)
            w = await o.walk()
            rapport(w["cam"][1] >= sol_lourde(w["cam"][0], w["cam"][2]) + 0.25, "caméra libre : ne traverse pas le sol", w["cam"])
            await o.touche("KeyF")
            w = await o.walk()
            rapport(w["view"] == "fps" and await o.ev("window.__viewer.walking"), "F en caméra libre : rend la main à l'avatar (reste en promenade)")
            for attendu in ("tps", "free", "fps"):
                await o.touche("KeyV")
            rapport((await o.walk())["view"] == "fps", "V fait tourner subjective, troisième personne, caméra libre, subjective")
            # mur derrière l'avatar en troisième personne
            await o.tp(146, hauteur(146, -240), -240, -math.pi / 2)
            await o.touche("KeyV")
            w = await o.walk()
            rapport(w["cam"][0] > 143.0 and math.hypot(w["cam"][0] - w["pos"][0], w["cam"][2] - w["pos"][2]) < 3.5, "troisième personne contre un mur : la caméra se rapproche et reste hors du mur", (w["cam"], w["pos"]))
            await o.touche("KeyV"); await o.touche("KeyV")
            rapport(not o.errs, "vues : aucune erreur JavaScript", o.errs)
            await o.fermer()

            print("--- 5 ter. vol vers une tuile pas prête")
            o = Onglet(br)
            suiv = NOM(tuile_de(DFX + 130, DFZ))
            o.garde[suiv] = asyncio.Event()
            await o.ouvrir(base + "Lourde&rayon=30#spawn=default")
            await o.marcheur(90)
            await o.touche("Home")
            await o.tenir(["KeyE"], 8)
            await o.ev("window.__viewer.releaseKeys()")
            await o.ev("([x, z, yaw]) => window.__viewer.teleportTo([x, 30, z], yaw)", [DFX + 40, DFZ, -math.pi / 2])
            m = await o.tenir(["KeyW"], 200)
            fin = max(s["pos"][0] for s in m)
            limite = next(t for t in TILES if t["file"].endswith(suiv))["min"][0]
            etat = await o.ev("window.__viewer.tilesState()")
            rapport(fin <= limite + 0.05 and etat["waiting"], f"en vol vers une tuile pas prête : l'avatar s'arrête au bord (x {fin:.2f} ≤ {limite}), « Chargement du sol… »", (fin, limite, etat["waiting"]))
            o.garde[suiv].set()
            await o.attendre(f"window.__viewer.tilesState().ready.some(f => f.endsWith('{suiv}'))", 60)
            m = await o.tenir(["KeyW"], 40)
            rapport(max(s["pos"][0] for s in m) > limite + 1, "tuile prête : l'avatar la traverse")
            await o.fermer()

            print("--- 5 quater. --no-fly")
            o = Onglet(br)
            await o.ouvrir(base + "NoFly#spawn=default")
            await o.marcheur(90)
            await o.touche("Home")
            rapport(not (await o.walk())["flying"] and "Début : voler" not in await o.ev("document.getElementById('walkHint').textContent"), "--no-fly : Début ne décolle pas, l'aide ne le propose pas")
            await o.fermer()

            # ---------- 6. marqueurs ----------
            print("--- 6. marqueurs de zones")
            async def marqueurs(region):
                o = Onglet(br)
                await o.ouvrir(base + region)
                await o.attendre("document.getElementById('msg') === null", 60)
                mk = await o.ev("window.__viewer.getMarkers()")
                nb_cyl = await o.ev("(() => { let n = 0; window.__viewer.scene.traverse(o => { if (o.geometry && o.geometry.type === 'CylinderGeometry') n++; }); return n; })()")
                clic = await o.ev("window.__viewer.getZoneState().length")
                await o.fermer()
                return {m["id"]: m for m in mk}, nb_cyl
            mk, cyl = await marqueurs("Lourde")
            rapport(set(mk["libre"]["kinds"]) == {"disc", "ring"} and set(mk["p1"]["kinds"]) == {"disc", "ring"} and "chateau" not in mk and "default" not in mk and cyl == 0, "discret (défaut) : disque et anneau fin, arrivées non dessinées, aucun cylindre", mk)
            mk, cyl = await marqueurs("MarkP")
            rapport(set(mk["libre"]["kinds"]) == {"range"} and abs(mk["libre"]["radius"] - 3) < 1e-9 and abs(mk["p1"]["radius"] - 2.5) < 1e-9 and cyl == 0 and "chateau" not in mk, "portee : anneau net au rayon réel de chaque zone (3 et 2,5 m), sans cylindre, arrivées non dessinées", mk)
            mk, cyl = await marqueurs("MarkA")
            rapport(all(not m["kinds"] for m in mk.values()) and cyl == 0, "aucun : aucun marqueur", mk)
            mk, cyl = await marqueurs("MarkS")
            rapport(set(mk["chateau"]["kinds"]) == {"spawn"} and set(mk["default"]["kinds"]) == {"spawn"} and set(mk["libre"]["kinds"]) == {"disc", "ring"}, "--show-spawns : un petit marqueur discret par arrivée, les zones gardent le leur", mk)
            # une zone « aucun » reste cliquable : survol = curseur main et infobulle
            o = Onglet(br)
            await o.ouvrir(base + "MarkA")
            await o.attendre("document.getElementById('msg') === null", 60)
            await o.attendre(f"window.__viewer.tilesState().ready.some(f => f.endsWith('{NOM(T_DEFAUT)}'))", 60)
            await o.ev("""([x, y, z]) => { const v = window.__viewer; v.camera.position.set(x + 4, y + 14, z + 10); v.controls.target.set(x, y, z); v.controls.update(); v.camera.updateMatrixWorld(true); }""", [DFX + 12, DFY, DFZ])
            pt = await o.ev("""([x, y, z]) => { const v = window.__viewer; v.camera.updateMatrixWorld(true); const p = v.camera.position.clone().set(x, y, z).project(v.camera), r = v.renderer.domElement.getBoundingClientRect(); return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; }""", [DFX + 12, DFY + 0.06, DFZ])
            await o.pg.mouse.move(*pt)
            await o.pg.wait_for_timeout(150)
            await o.pg.mouse.move(pt[0] + 1, pt[1])
            await o.pg.wait_for_timeout(200)
            cur = await o.ev("document.querySelector('canvas').style.cursor")
            rapport(cur == "pointer", "marqueur « aucun » : la zone reste cliquable (curseur main au survol)", cur)
            await o.fermer()
        finally:
            proc.kill()

        # ================= 7. serveur de présence : couleur, --log-ip =================
        print("--- 7. serveur de présence : couleur annoncée")
        import websockets, websockets.asyncio.client
        pres, pport = lancer_presence()

        async def hello(room, name, color="absent", uid=None, spectator=False):
            ws = await websockets.asyncio.client.connect(f"ws://127.0.0.1:{pport}")
            m = {"t": "hello", "room": room, "name": name, "uid": uid or (name + "0123456789abcdef")[:20], "spectator": spectator}
            if color != "absent":
                m["color"] = color
            await ws.send(json.dumps(m))
            return ws, json.loads(await asyncio.wait_for(ws.recv(), 5))
        try:
            obs, w0 = await hello("couleurs", "Obs")
            res = {}
            for etiq, val in (("valide", 0xFF8800), ("noir", 0), ("blanc", 0xFFFFFF), ("negatif", -1), ("trop", 0x1000000), ("flottant", 1.5), ("texte", "#ff0000"), ("booleen", True), ("nul", None), ("liste", [1])):
                ws, w = await hello("couleurs", "P" + etiq, val)
                j = None
                while True:
                    j = json.loads(await asyncio.wait_for(obs.recv(), 5))
                    if j.get("t") == "join" and j.get("name") == "P" + etiq:
                        break
                res[etiq] = (w["color"], j["color"])
                await ws.close()
            rapport(res["valide"] == (0xFF8800, 0xFF8800) and res["noir"] == (0, 0) and res["blanc"] == (0xFFFFFF, 0xFFFFFF), "serveur : couleur valide acceptée (0xFF8800, 0, 0xFFFFFF), annoncée à la bienvenue et diffusée aux autres", res)
            rapport(all(res[k][0] != v and 0 <= res[k][0] <= 0xFFFFFF and res[k][0] == res[k][1] for k, v in (("negatif", -1), ("trop", 0x1000000), ("flottant", 1.5), ("texte", "#ff0000"), ("booleen", 1), ("nul", None), ("liste", [1]))), "serveur : -1, 0x1000000, 1,5, texte, booléen, null, liste → rejet silencieux, couleur tirée au hasard", res)
            ws, w = await hello("couleurs", "Ancien")
            rapport(0 <= w["color"] <= 0xFFFFFF, "client sans couleur (ancien client) : couleur tirée au hasard, rien ne casse")
            await ws.close()
            await obs.close()
            # un client vu d'un ancien serveur : le serveur de la v32 ignore le champ
            ancien = subprocess.run(["git", "show", "HEAD:src/presence_server.py"], capture_output=True, text=True, cwd=ROOT).stdout
            if ancien and "announced_color" not in ancien:
                (tmp / "presence_ancien.py").write_text(ancien.replace("__VERSION__", "ancien"), encoding="utf-8")
                pa, paport = lancer_presence(script=tmp / "presence_ancien.py")
                ws = await websockets.asyncio.client.connect(f"ws://127.0.0.1:{paport}")
                await ws.send(json.dumps({"t": "hello", "room": "x", "name": "N", "uid": "N" * 20, "color": 0xFF8800}))
                w = json.loads(await asyncio.wait_for(ws.recv(), 5))
                rapport(w.get("t") == "welcome" and w["color"] != 0xFF8800, "ancien serveur (v32) : ignore le champ color, répond normalement", w)
                await ws.close()
                pa.kill()
        finally:
            pres.kill()

        print("--- 7 bis. --log-ip raw")
        logf = tmp / "p_raw.log"
        pr, prport = lancer_presence("--log", str(logf), "--log-ip", "raw")
        try:
            ws = await websockets.asyncio.client.connect(f"ws://127.0.0.1:{prport}")
            await ws.send(json.dumps({"t": "hello", "room": "ip", "name": "Visiteur", "uid": "V" * 20}))
            await asyncio.wait_for(ws.recv(), 5)
            await asyncio.sleep(0.5)
            await ws.close()
            await asyncio.sleep(0.3)
        finally:
            pr.terminate()
            sortie = pr.communicate(timeout=10)[0]
        contenu = logf.read_text(encoding="utf-8") if logf.exists() else ""
        rapport(re.search(r"connexion\s+\| salon=ip \| .*ip 127\.0\.0\.1\]", contenu) is not None, "--log-ip raw : l'IP est écrite en clair dans le journal à la connexion", contenu[:300])
        rapport(re.search(r"connexion\s+\| salon=ip \| .*ip 127\.0\.0\.1\]", sortie) is not None, "--log-ip raw : et dans la console", sortie[-300:])
        logh = tmp / "p_hash.log"
        ph, phport = lancer_presence("--log", str(logh))
        try:
            ws = await websockets.asyncio.client.connect(f"ws://127.0.0.1:{phport}")
            await ws.send(json.dumps({"t": "hello", "room": "ip", "name": "Visiteur", "uid": "V" * 20}))
            await asyncio.wait_for(ws.recv(), 5)
            await asyncio.sleep(0.5)
            await ws.close()
            await asyncio.sleep(0.3)
        finally:
            ph.terminate()
            ph.communicate(timeout=10)
        ch = logh.read_text(encoding="utf-8")
        lc = [l for l in ch.splitlines() if "| salon=ip |" in l and "connexion" in l]
        rapport(lc and "127.0.0.1" not in lc[0] and re.search(r"ip [0-9a-f]{8}\]", lc[0]) is not None, "défaut : l'IP est masquée (empreinte de 8 caractères)", lc)

        # ================= 8. chat, pseudo cité, complétion, enregistrement, couleur (navigateur + vrai serveur) =================
        print("--- 8. chat persistant, enregistré, pseudo cité, complétion, couleur")
        pchat, cport = lancer_presence("--chat-burst", "100", "--chat-gap", "0.1")
        html("-o", site / "Chat.html", "--shared-shell", "--tiles", TJ, "--zones", tmp / "zl.json", "--presence-url", f"ws://127.0.0.1:{cport}", "--chat", "--room", "salon33")
        proc2, port2 = serveur(site)
        base2 = f"http://127.0.0.1:{port2}/index.html?region="
        AUDIO = "window.__beeps = 0; window.AudioContext = class { constructor() { this.state = 'running'; this.currentTime = 0; this.destination = {}; } resume() {} createOscillator() { window.__beeps++; return { type: '', frequency: { value: 0 }, connect() {}, start() {}, stop() {} }; } createGain() { return { gain: { setValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect() {} }; } };"

        def init(nom, vis=None):
            return AUDIO + f" try {{ localStorage.setItem('glb2html_name', {json.dumps(nom)}); " + (f"localStorage.setItem('glb2html_visitor', {json.dumps(json.dumps(vis))});" if vis else "") + " } catch (e) {}"

        async def visiteur(nom, x, vis=None, downloads=False):
            v = Onglet(br)
            await v.ouvrir(base2 + f"Chat#pos={x},13,-100,0", init=init(nom, vis), downloads=downloads)
            await v.marcheur(90)
            await v.attendre("window.__viewer.getPresence().state === 'online'", 30)
            return v
        try:
            A = await visiteur("Alice", 500, downloads=True)
            B = await visiteur("Bob", 504)
            await A.attendre("window.__viewer.getPresence().peers.some(p => p.name === 'Bob')", 30)
            extras, lecteurs = [], []

            async def vider(ws):   # lit sans fin : un client qui ne lit pas finit par être déconnecté par le serveur
                try:
                    async for _ in ws:
                        pass
                except Exception:
                    pass
            for nom in ("Bobby", "Boris", "Carl", "Cora", "Dan"):
                ws = await websockets.asyncio.client.connect(f"ws://127.0.0.1:{cport}")
                await ws.send(json.dumps({"t": "hello", "room": "salon33", "name": nom, "uid": (nom * 8)[:24], "spectator": False}))
                await asyncio.wait_for(ws.recv(), 5)
                extras.append(ws)
                lecteurs.append(asyncio.ensure_future(vider(ws)))
            await A.attendre("window.__viewer.getPresence().peers.length >= 6", 30)

            inp_visible = "!document.getElementById('chatInput').hidden"
            await A.pg.keyboard.press("Enter")
            rapport(await A.ev(inp_visible), "Entrée ouvre la saisie du chat")
            await A.pg.keyboard.type("bonjour")
            await A.pg.keyboard.press("Enter")
            await B.attendre("document.getElementById('chatLog').textContent.includes('Alice : bonjour')", 15)
            rapport(await A.ev(inp_visible) and await A.ev("document.getElementById('chatInput').value") == "", "Entrée envoie le message ET garde la saisie ouverte (champ vidé)")
            await asyncio.sleep(0.8)
            await A.pg.keyboard.type("deuxième message")
            await A.pg.keyboard.press("Enter")
            await B.attendre("document.getElementById('chatLog').textContent.includes('Alice : deuxième message')", 15)
            rapport(await A.ev(inp_visible), "second message envoyé, la saisie reste ouverte")
            aide = await A.ev("document.getElementById('walkHint').textContent")
            rapport("Entrée : écrire" in aide and "Échap : fermer" in aide, "l'aide donne les touches du chat (Entrée : écrire, Échap : fermer ; v35 : groupes courts)")
            # lettres dans le texte, flèches pour l'avatar
            p0 = (await A.walk())
            await A.pg.keyboard.down("ArrowLeft")
            m = await A.ev("() => { const v = window.__viewer; v.walkTick(0.5); return v.getWalk().yaw; }")
            await A.pg.keyboard.up("ArrowLeft")
            rapport(m - p0["yaw"] > 0.5, "saisie ouverte : la flèche gauche tourne l'avatar", (p0["yaw"], m))
            await A.pg.keyboard.down("ArrowUp")
            m = await A.ev("() => { const v = window.__viewer; const a = v.getWalk().pos.slice(); v.walkTick(0.5); return [a, v.getWalk().pos]; }")
            await A.pg.keyboard.up("ArrowUp")
            rapport(math.dist(m[0], m[1]) > 0.5, "saisie ouverte : la flèche haut avance l'avatar", m)
            await A.pg.keyboard.down("w")
            m = await A.ev("() => { const v = window.__viewer; const a = v.getWalk().pos.slice(); v.walkTick(0.5); return [a, v.getWalk().pos, document.getElementById('chatInput').value]; }")
            await A.pg.keyboard.up("w")
            rapport(math.dist(m[0], m[1]) < 1e-9 and m[2] == "w", "saisie ouverte : les lettres vont dans le texte, l'avatar ne bouge pas", m)
            await A.ev("document.getElementById('chatInput').value = ''")
            await A.pg.keyboard.press("Escape")
            rapport(not await A.ev(inp_visible), "Échap ferme la saisie")
            await A.pg.keyboard.down("w")
            m = await A.ev("() => { const v = window.__viewer; const a = v.getWalk().pos.slice(); v.walkTick(0.5); return [a, v.getWalk().pos]; }")
            await A.pg.keyboard.up("w")
            rapport(math.dist(m[0], m[1]) > 0.5, "Échap rend les touches à la promenade (W avance)", m)

            # enregistrement du chat
            await B.ev("window.__viewer.sendChat('réponse de Bob')")
            await A.attendre("document.getElementById('chatLog').textContent.includes('Bob : réponse de Bob')", 15)
            async with A.pg.expect_download() as dl:
                await A.pg.click("#chatSave")
            d = await dl.value
            chemin = tmp / "chat_a.txt"
            await d.save_as(str(chemin))
            brut = chemin.read_bytes()
            texte = brut.decode("utf-8-sig")
            lignes = texte.splitlines()
            rapport(brut.startswith(b"\xef\xbb\xbf") and "Chat de la région « salon33 »" in lignes[0] and re.search(r"\d\d/\d\d/\d{4} \d\d:\d\d:\d\d", lignes[0]) is not None, "fichier du chat : UTF-8, titre avec la date jj/mm/aaaa", lignes[:2])
            rapport(any(re.fullmatch(r"\d\d/\d\d/\d{4} \d\d:\d\d:\d\d \| Alice \| bonjour", l) for l in lignes) and any(re.fullmatch(r"\d\d/\d\d/\d{4} \d\d:\d\d:\d\d \| Alice \| deuxième message", l) for l in lignes) and any(l.endswith("| Bob | réponse de Bob") for l in lignes), "fichier du chat : messages envoyés et reçus, avec l'heure locale, le nom et le texte (accents conservés)", lignes)
            rapport(d.suggested_filename.startswith("chat_salon33_") and d.suggested_filename.endswith(".txt"), "nom du fichier proposé", d.suggested_filename)
            # un nouvel arrivant : l'historique rejoué par le serveur n'est pas dans son fichier
            C = await visiteur("Clara", 508, downloads=True)
            await C.attendre("document.getElementById('chatLog').textContent.includes('bonjour')", 15)
            rapport(True, "nouvel arrivant : le serveur lui rejoue les derniers messages (historique en mémoire du serveur)")
            await asyncio.sleep(0.8)
            await C.ev("window.__viewer.sendChat('premier message de Clara')")
            await C.attendre("document.getElementById('chatLog').textContent.includes('Clara : premier message de Clara')", 15)
            async with C.pg.expect_download() as dl:
                await C.pg.click("#chatSave")
            d = await dl.value
            await d.save_as(str(tmp / "chat_c.txt"))
            tc = (tmp / "chat_c.txt").read_text(encoding="utf-8-sig")
            rapport("premier message de Clara" in tc and "bonjour" not in tc and "réponse de Bob" not in tc, "le fichier de l'arrivant ne contient que ce qu'il a vu depuis son arrivée (pas l'historique)", tc)
            await C.fermer()

            # pseudo cité
            await asyncio.sleep(0.8)
            await A.pg.bring_to_front()
            await B.ev("window.__viewer.sendChat('salut @alice, ça va ?')")
            await A.attendre("document.getElementById('chatLog').textContent.includes('ça va ?')", 15)
            await asyncio.sleep(2.6)
            r = await A.ev("""() => { const ls = [...document.querySelectorAll('#chatLog div')].filter(d => d.textContent.includes('ça va ?')); const d = ls[ls.length - 1];
                const p = window.__viewer.getPresence().peers.find(q => q.name === 'Bob');
                return { bold: getComputedStyle(d).fontWeight, txt: d.textContent, cite: d.dataset.cite, hidden: p.blinkHidden, visible: p.bubbleVisible, blinking: p.blinking, beeps: window.__beeps }; }""")
            rapport(int(r["bold"]) >= 700 and r["txt"].startswith("@ Bob : salut @alice") and r["cite"] == "1", "pseudo cité (@alice) : message en gras, précédé de « @ »", r)
            rapport(r["hidden"] >= 1 and r["visible"] and not r["blinking"], "la bulle de l'auteur a clignoté (au moins un passage caché mesuré à la cadence de rendu logiciel), puis est restée visible", r)
            seq = await A.ev("""() => { const v = window.__viewer, id = v.getPresence().peers.find(q => q.name === 'Bob').id, t = performance.now(), seq = [];
                v.blinkBubble(id);
                for (let k = 0; k <= 45; k++) { v.tickPresence(0.05, t + 2 + k * 50); seq.push(v.getPresence().peers.find(q => q.id === id).bubbleVisible ? 1 : 0); }
                return seq; }""")
            flips = sum(1 for a, b in zip(seq, seq[1:]) if a == 1 and b == 0)
            rapport(flips == 6 and all(seq[36:]) and seq[0] == 1, "clignotement : exactement 6 passages cachés de 150 ms sur 300 ms (pas de présence simulé à 50 ms), puis visible", seq)
            rapport(r["beeps"] == 0, "son décoché par défaut : aucun bip", r["beeps"])
            for texte_msg, attendu in (("Alicex et xalice", False), ("ALICE, viens", True), ("coucou @Alice", True), ("alice's", True), ("Alicia", False), ("l'alice", True)):
                await asyncio.sleep(0.8)
                await B.ev("(t) => window.__viewer.sendChat(t)", texte_msg)
                await A.attendre(f"[...document.querySelectorAll('#chatLog div')].some(d => d.textContent.includes({json.dumps(texte_msg)}))", 15)
                gras = await A.ev("(t) => { const d = [...document.querySelectorAll('#chatLog div')].filter(x => x.textContent.includes(t)).pop(); return d.dataset.cite === '1'; }", texte_msg)
                rapport(gras == attendu, f"pseudo cité en mot entier : « {texte_msg} » {'cité' if attendu else 'non cité'}", gras)
            # cases décochées : rien
            A2 = await visiteur("Zoe", 512, vis={"color": None, "bold": False, "blink": False, "sound": False})
            await A2.pg.wait_for_timeout(500)
            await asyncio.sleep(0.8)
            await B.ev("window.__viewer.sendChat('encore @Zoe')")
            await A2.attendre("document.getElementById('chatLog').textContent.includes('encore @Zoe')", 15)
            await asyncio.sleep(2.6)
            r = await A2.ev("""() => { const d = [...document.querySelectorAll('#chatLog div')].filter(x => x.textContent.includes('encore @Zoe')).pop(); const p = window.__viewer.getPresence().peers.find(q => q.name === 'Bob');
                return { bold: getComputedStyle(d).fontWeight, txt: d.textContent, hidden: p.blinkHidden, beeps: window.__beeps }; }""")
            rapport(int(r["bold"]) < 700 and r["txt"].startswith("Bob : ") and r["hidden"] == 0 and r["beeps"] == 0, "trois cases décochées : ni gras ni « @ », ni clignotement, ni bip", r)
            await A2.fermer()
            # son : seulement après une première interaction
            A3 = await visiteur("Yan", 516, vis={"color": None, "bold": True, "blink": True, "sound": True})
            await asyncio.sleep(0.8)
            await B.ev("window.__viewer.sendChat('premier @Yan')")
            await A3.attendre("document.getElementById('chatLog').textContent.includes('premier @Yan')", 15)
            b0 = await A3.ev("window.__beeps")
            await A3.pg.keyboard.press("Shift")
            await asyncio.sleep(0.8)
            await B.ev("window.__viewer.sendChat('second @Yan')")
            await A3.attendre("document.getElementById('chatLog').textContent.includes('second @Yan')", 15)
            b1 = await A3.ev("window.__beeps")
            rapport(b0 == 0 and b1 == 1, "son coché : aucun bip avant la première interaction, un bip après", (b0, b1))
            # panneau de réglages visiteur
            await A3.ev("document.getElementById('optsBtn').click()")
            et = await A3.ev("({ bold: document.getElementById('visBold').checked, blink: document.getElementById('visBlink').checked, sound: document.getElementById('visSound').checked, col: document.getElementById('visColorOn').checked })")
            rapport(et == {"bold": True, "blink": True, "sound": True, "col": False}, "Réglages visiteur : trois cases (gras, clignotement, son) et la couleur reflètent le stockage", et)
            await A3.ev("document.getElementById('visBlink').click()")
            mem = await A3.ev("JSON.parse(localStorage.getItem('glb2html_visitor'))")
            rapport(mem["blink"] is False and mem["bold"] is True and mem["sound"] is True, "les réglages sont mémorisés dans le navigateur", mem)
            await A3.fermer()
            # défauts des cases : tout coché sauf le son
            et = await A.ev("document.getElementById('optsBtn').click() || ({ bold: document.getElementById('visBold').checked, blink: document.getElementById('visBlink').checked, sound: document.getElementById('visSound').checked })")
            rapport(et == {"bold": True, "blink": True, "sound": False}, "défauts : gras et clignotement cochés, son décoché", et)
            await A.ev("document.getElementById('optsBtn').click()")

            # complétion
            await A.pg.keyboard.press("Enter")
            await A.pg.keyboard.type("salut @Bo")
            liste = await A.ev("({ vis: !document.getElementById('chatComplete').hidden, items: [...document.querySelectorAll('#chatComplete [role=option]')].map(d => d.textContent.trim().replace('▶ ', '')), sel: [...document.querySelectorAll('#chatComplete [role=option]')].map(d => d.getAttribute('aria-selected')) })")
            rapport(liste["vis"] and sorted(liste["items"]) == ["Bob", "Bobby", "Boris"] and liste["sel"][0] == "true", "@Bo : liste de 3 pseudos (Bob, Bobby, Boris), le premier choisi", (liste, await A.ev("window.__viewer.getPresence().peers.map(p => p.name)")))
            await A.pg.keyboard.down("ArrowDown")
            m = await A.ev("() => { const v = window.__viewer; const a = v.getWalk().pos.slice(); v.walkTick(0.5); return [a, v.getWalk().pos]; }")
            await A.pg.keyboard.up("ArrowDown")
            sel = await A.ev("[...document.querySelectorAll('#chatComplete [role=option]')].map(d => d.getAttribute('aria-selected'))")
            rapport(sel[1] == "true" and math.dist(m[0], m[1]) < 1e-9, "flèche bas : change le choix (et ne déplace pas l'avatar)", (sel, m))
            nom2 = await A.ev("document.querySelector('#chatComplete [aria-selected=true]').textContent.trim().replace('▶ ', '')")
            await A.pg.keyboard.press("Tab")
            val = await A.ev("document.getElementById('chatInput').value")
            rapport(val == f"salut @{nom2} " and await A.ev("document.getElementById('chatComplete').hidden"), "Tab insère le pseudo choisi suivi d'une espace", val)
            await A.ev("document.getElementById('chatInput').value = ''")
            await A.pg.keyboard.type("@Bor")
            n_avant = await B.ev("document.querySelectorAll('#chatLog div').length")
            await A.pg.keyboard.press("Enter")
            val = await A.ev("document.getElementById('chatInput').value")
            await asyncio.sleep(0.5)
            rapport(val == "@Boris " and await B.ev("document.querySelectorAll('#chatLog div').length") == n_avant, "Entrée avec la liste ouverte insère le pseudo et n'envoie pas le message", val)
            await A.ev("document.getElementById('chatInput').value = ''")
            await A.pg.keyboard.type("@C")
            liste = await A.ev("[...document.querySelectorAll('#chatComplete [role=option]')].map(d => d.textContent.trim().replace('▶ ', ''))")
            await A.pg.keyboard.press("Escape")
            rapport(sorted(liste) == ["Carl", "Cora"] and await A.ev("document.getElementById('chatComplete').hidden") and await A.ev(inp_visible), "Échap ferme la liste sans fermer la saisie", liste)
            await A.ev("document.getElementById('chatInput').value = ''")
            await A.pg.keyboard.type("@")
            nb = await A.ev("document.querySelectorAll('#chatComplete [role=option]').length")
            rapport(nb == 5, "« @ » seul : cinq pseudos au plus (six visiteurs en ligne)", nb)
            await A.ev("document.getElementById('chatInput').value = ''")
            await A.pg.keyboard.type("@Zz")
            rapport(await A.ev("document.getElementById('chatComplete').hidden"), "liste vide : rien n'est affiché")
            await A.pg.keyboard.press("Escape")
            rapport(not await A.ev(inp_visible), "Échap sans liste ferme la saisie")
            rapport(not A.errs and not B.errs, "chat : aucune erreur JavaScript", A.errs + B.errs)

            # couleur
            print("--- 8 bis. couleur de l'avatar dans le navigateur")
            await A.fermer(); await B.fermer()
            ACol = await visiteur("Eva", 500, vis={"color": 0x00AA55, "bold": True, "blink": True, "sound": False})
            BCol = await visiteur("Fred", 504)
            await BCol.attendre("window.__viewer.getPresence().peers.some(p => p.name === 'Eva')", 30)
            vu = await BCol.ev("window.__viewer.getPresence().peers.find(p => p.name === 'Eva')")
            rapport(vu["color"] == 0x00AA55 and vu["stack"]["label"] is not None, "la couleur choisie (0x00AA55) est envoyée dans hello et diffusée ; le nom reste affiché (étiquette)", vu["color"])
            vu2 = await ACol.ev("window.__viewer.getPresence().peers.find(p => p.name === 'Fred')")
            rapport(0 <= vu2["color"] <= 0xFFFFFF and vu2["color"] != 0x00AA55, "sans choix : couleur tirée au hasard par le serveur", vu2["color"])
            await ACol.ev("document.getElementById('optsBtn').click()")
            et = await ACol.ev("({ on: document.getElementById('visColorOn').checked, v: document.getElementById('visColor').value })")
            rapport(et == {"on": True, "v": "#00aa55"}, "Réglages visiteur : le sélecteur de couleur reflète le choix mémorisé", et)
            await ACol.ev("document.getElementById('visColorOn').click()")
            rapport((await ACol.ev("JSON.parse(localStorage.getItem('glb2html_visitor'))"))["color"] is None, "décocher la couleur la remet au hasard (mémorisé)")
            await ACol.fermer(); await BCol.fermer()
            inval = await visiteur("Dora", 500, vis={"color": 99999999, "bold": True, "blink": True, "sound": False})
            rapport(await inval.ev("(() => { const q = window.__viewer.getPresence(); return q.state; })()") == "online", "couleur mémorisée invalide : ignorée, la connexion se fait quand même")
            await inval.fermer()
            for t in lecteurs:
                t.cancel()
            for ws in extras:
                await ws.close()
        finally:
            proc2.kill()
            pchat.kill()

        # ================= 9. viewer : enregistrement des zones dans le dossier, réglages d'export =================
        print("--- 9. viewer : zones enregistrées dans le dossier de la région")
        vreg = tmp / "vreg"
        (vreg / "regions").mkdir(parents=True)
        glbfab.region(vreg / "regions" / "Syn.glb")
        run(DIST / "glb2tiles.py", vreg / "regions" / "Syn.glb", "--nopause", "--forcer", "--budget-tri", "900", "--min", "64", "--entier-etendue", "50")
        shutil.copy(DIST / "glb-viewer.html", vreg / "glb-viewer.html")
        vproc, vport = serveur(vreg)
        FAKE_FS = r"""
        window.__fs = { files: {'Syn.tiles.json': '{}'}, other: {'autre.txt': 'x'}, picks: 0, writes: [], mode: 'ok' };
        const mk = (files, name) => ({ name,
          async getFileHandle(n, o) {
            if (!(n in files)) { if (!(o && o.create)) throw new DOMException('absent', 'NotFoundError'); files[n] = ''; }
            return { async getFile() { return { async text() { return files[n]; } }; },
                     async createWritable() { let b = ''; return { async write(t) { b += t; }, async close() { files[n] = b; window.__fs.writes.push(name + '/' + n); } }; } };
          },
          async queryPermission() { return 'granted'; }, async requestPermission() { return 'granted'; } });
        window.__fs.dir = mk(window.__fs.files, 'tuiles'); window.__fs.wrong = mk(window.__fs.other, 'mauvais');
        window.showDirectoryPicker = async () => {
          window.__fs.picks++;
          if (window.__fs.mode === 'denied') throw new DOMException('refusé', 'NotAllowedError');
          if (window.__fs.mode === 'abort') throw new DOMException('annulé', 'AbortError');
          return window.__fs.mode === 'wrong' ? window.__fs.wrong : window.__fs.dir;
        };
        """
        NOAPI = "window.showDirectoryPicker = undefined;"
        Z1 = [{"id": "a", "type": "url", "label": "Un", "target": "https://example.org/", "x": 1, "y": 2, "z": 3, "radius": 2}]
        Z2 = Z1 + [{"id": "b", "type": "url", "label": "Deux", "target": "https://example.org/b", "x": 4, "y": 5, "z": 6, "radius": 2}]
        Z3 = Z2 + [{"id": "c", "type": "url", "label": "Trois", "target": "https://example.org/c", "x": 7, "y": 8, "z": 9, "radius": 2}]
        for i, z in enumerate((Z1, Z2, Z3), 1):
            (tmp / f"z{i}.json").write_text(json.dumps(z), encoding="utf-8")
        PHRASE = "enregistre ce fichier dans le dossier de la région, sous le nom Syn.zones.json, en remplaçant l'ancien"
        try:
            async def viewer_page(init_js, downloads=True):
                ctx = await br.new_context(viewport={"width": 1300, "height": 800}, accept_downloads=downloads)
                await ctx.add_init_script(init_js)
                pg = await ctx.new_page()
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                await pg.goto(f"http://127.0.0.1:{vport}/glb-viewer.html?tuiles=regions/Syn.tiles.json")
                await pg.wait_for_function("window.__viewer.tiled && window.__viewer.tilesState().ready.length > 0", timeout=60000)
                return ctx, pg, errs
            ctx, pg, errs = await viewer_page(FAKE_FS)
            try:
                await pg.wait_for_selector("#bZoneDir", state="visible", timeout=15000)
            except Exception:
                pass
            rapport(await pg.is_visible("#bZoneDir"), "viewer en mode tuiles : bouton « Enregistrer les zones dans le dossier de la région »")
            await pg.set_input_files("#fZones", str(tmp / "z1.json"))
            await pg.click("#bZoneDir")
            await pg.wait_for_function("window.__fs.writes.length >= 1", timeout=10000)
            fs = await pg.evaluate("({ files: window.__fs.files, picks: window.__fs.picks, info: document.getElementById('zDirInfo').textContent })")
            ids = lambda t: [z["id"] for z in json.loads(t or "[]")]
            premier = fs["files"].get("Syn.zones.json")
            rapport(ids(premier) == ["a"] and "Syn.zones.bak.json" not in fs["files"] and fs["picks"] == 1, "premier enregistrement : Syn.zones.json écrit dans le dossier choisi, pas d'ancien fichier, dossier demandé une fois", fs["files"])
            rapport(re.search(r"dossier « tuiles », fichier Syn\.zones\.json, le \d\d/\d\d/\d{4} à \d\d:\d\d:\d\d", fs["info"]) is not None and "F5 suffit" in fs["info"], "le dossier, le fichier et la date jj/mm/aaaa à l'heure sont affichés en texte, avec « F5 suffit »", fs["info"])
            await pg.set_input_files("#fZones", str(tmp / "z2.json"))
            await pg.click("#bZoneDir")
            await pg.wait_for_function("window.__fs.writes.length >= 3", timeout=10000)
            fs = await pg.evaluate("({ files: window.__fs.files, picks: window.__fs.picks, info: document.getElementById('zDirInfo').textContent })")
            second = fs["files"]["Syn.zones.json"]
            rapport(ids(second) == ["a", "b"] and fs["files"]["Syn.zones.bak.json"] == premier and fs["picks"] == 1, "second enregistrement : l'ancien est gardé sous Syn.zones.bak.json, la poignée du dossier est réutilisée (une seule demande)", fs["files"])
            await pg.set_input_files("#fZones", str(tmp / "z3.json"))
            await pg.click("#bZoneDir")
            await pg.wait_for_function("window.__fs.writes.length >= 5", timeout=10000)
            fs = await pg.evaluate("window.__fs.files")
            rapport(ids(fs["Syn.zones.json"]) == ["a", "b", "c"] and fs["Syn.zones.bak.json"] == second, "troisième : une seule copie, écrasée à chaque enregistrement (le .bak contient la version précédente)")
            rapport(not errs, "viewer : aucune erreur JavaScript", errs)
            # export du réglage : ligne de commande et script
            await pg.evaluate("window.__viewer.setCfg({ zoneMarker: 'portee', showSpawns: true, fly: false })")
            await pg.click("#bCmd")
            cmd = await pg.evaluate("document.getElementById('cmdOut').value")
            rapport("--zone-marker portee" in cmd and "--show-spawns" in cmd and "--no-fly" in cmd, "récapitulatif de la ligne de commande : --zone-marker portee, --show-spawns, --no-fly", cmd)
            async with pg.expect_download() as dl:
                await pg.click("#bPy")
            dpy = await dl.value
            await dpy.save_as(str(tmp / "glb2html_exporte.py"))
            exp = (tmp / "glb2html_exporte.py").read_text(encoding="utf-8")
            rapport('ZONE_MARKER = "portee"' in exp and "SHOW_SPAWNS = True" in exp and "FLY_ENABLED = False" in exp and "TARGET_EXPLICIT = False" in exp, "script Python exporté par le viewer : les réglages sont dans le bloc des défauts")
            run(tmp / "glb2html_exporte.py", "-o", tmp / "vout" / "V.html", "--shared-shell", "--tiles", vreg / "regions" / "Syn.tiles.json", *vend)
            cv = json.loads((tmp / "vout" / "V.config.json").read_text(encoding="utf-8"))
            rapport(cv["zoneMarker"] == "portee" and cv["showSpawns"] is True and cv["fly"] is False and cv["targetExplicit"] is False, "la page générée par ce script reprend ces réglages", {k: cv.get(k) for k in ("zoneMarker", "showSpawns", "fly", "targetExplicit")})
            await ctx.close()
            # dossier qui n'est pas celui de la région
            ctx, pg, errs = await viewer_page(FAKE_FS)
            await pg.evaluate("window.__fs.mode = 'wrong'")
            await pg.set_input_files("#fZones", str(tmp / "z1.json"))
            await pg.click("#bZoneDir")
            await pg.wait_for_function("document.getElementById('zDirInfo').textContent.includes('Rien écrit')", timeout=10000)
            fs = await pg.evaluate("({ other: window.__fs.other, writes: window.__fs.writes, info: document.getElementById('zDirInfo').textContent })")
            rapport(fs["writes"] == [] and list(fs["other"]) == ["autre.txt"] and "ne contient pas Syn.tiles.json" in fs["info"], "dossier sans Syn.tiles.json : rien n'est écrit, message clair", fs["info"])
            await ctx.close()
            # refus et annulation
            ctx, pg, errs = await viewer_page(FAKE_FS)
            await pg.evaluate("window.__fs.mode = 'denied'")
            await pg.set_input_files("#fZones", str(tmp / "z2.json"))
            async with pg.expect_download() as dl:
                await pg.click("#bZoneDir")
            d = await dl.value
            await d.save_as(str(tmp / "refus.json"))
            st = await pg.evaluate("document.getElementById('stat').textContent")
            rapport(d.suggested_filename == "Syn.zones.json" and [z["id"] for z in json.loads((tmp / "refus.json").read_text(encoding="utf-8"))] == ["a", "b"] and PHRASE in st, "accès refusé : repli sur le téléchargement, avec la phrase attendue", st)
            await pg.evaluate("window.__fs.mode = 'abort'")
            tel = []
            pg.on("download", lambda d: tel.append(d))
            await pg.click("#bZoneDir")
            await pg.wait_for_function("document.getElementById('stat').textContent.includes('annulé')", timeout=10000)
            await asyncio.sleep(0.5)
            rapport(not tel, "choix du dossier annulé : rien n'est écrit ni téléchargé")
            await ctx.close()
            # API absente
            ctx, pg, errs = await viewer_page(NOAPI)
            await pg.set_input_files("#fZones", str(tmp / "z3.json"))
            async with pg.expect_download() as dl:
                await pg.click("#bZoneDir")
            d = await dl.value
            await d.save_as(str(tmp / "noapi.json"))
            st = await pg.evaluate("document.getElementById('stat').textContent")
            rapport(d.suggested_filename == "Syn.zones.json" and [z["id"] for z in json.loads((tmp / "noapi.json").read_text(encoding="utf-8"))] == ["a", "b", "c"] and PHRASE in st, "sans l'API (Firefox, Safari) : téléchargement et phrase « enregistre ce fichier dans le dossier de la région… »", st)
            rapport(not errs, "viewer sans API : aucune erreur JavaScript", errs)
            await ctx.close()
            ctx = await br.new_context(viewport={"width": 1300, "height": 800})
            pg = await ctx.new_page()
            await pg.goto((DIST / "glb-viewer.html").as_uri())
            await pg.wait_for_selector("#bZoneAdd", state="attached", timeout=15000)
            rapport(not await pg.is_visible("#bZoneDir"), "viewer sans région en tuiles : le bouton d'enregistrement dans le dossier est masqué")
            await ctx.close()
        finally:
            vproc.kill()

        # ================= 10. glb2html --tiles --zones déjà en place =================
        print("--- 10. glb2html --tiles --zones : fichier déjà en place")
        dest = site / "Lourde.zones.json"
        perso = [{"id": "secret", "type": "url", "label": "Privé", "target": "https://example.org/", "x": 1, "y": 2, "z": 3, "private": True}] + ZL
        dest.write_text(json.dumps(perso, indent=1), encoding="utf-8")
        avant, mt = dest.read_bytes(), dest.stat().st_mtime_ns
        time.sleep(0.05)
        r = html("-o", site / "Lourde.html", "--shared-shell", "--tiles", TJ, "--zones", dest)
        rapport(r.returncode == 0 and "zones déjà en place" in r.stdout and dest.read_bytes() == avant and dest.stat().st_mtime_ns == mt, "même chemin que X.zones.json : « zones déjà en place », fichier intact (zone privée conservée), code 0", r.stdout[-300:] + r.stderr[-200:])
        r = run(DIST / "glb2html.py", "-o", "Lourde.html", "--shared-shell", "--tiles", "Lourde.tiles.json", "--zones", "Lourde.zones.json", *vend, cwd=site)
        rapport(r.returncode == 0 and "zones déjà en place" in r.stdout and dest.read_bytes() == avant, "chemins relatifs depuis le dossier de la région : reconnu aussi", r.stdout[-300:])
        r = html("-o", site / "Lourde.html", "--shared-shell", "--tiles", TJ)
        rapport(r.returncode == 0 and dest.read_bytes() == avant, "sans --zones : X.zones.json existant conservé")
        copie = tmp / "autre_zones.json"
        copie.write_text(json.dumps(perso), encoding="utf-8")
        r = html("-o", site / "Lourde.html", "--shared-shell", "--tiles", TJ, "--zones", copie)
        zz = json.loads(dest.read_text(encoding="utf-8"))
        rapport("zones déjà en place" not in r.stdout and not any(z["id"] == "secret" for z in zz), "un autre fichier : copié comme avant (profil public : la zone privée est retirée)", r.stdout[-200:])

        # ================= 11. la commande de JJ : nom de région avec parenthèses, dossier avec « & », coquille à renouveler, zones conservées =================
        print("--- 11. région « OAR-Free_House_Gallery_I(4X4)-terrain » dans un dossier « SL&OS » : coquille renouvelée, zones existantes conservées")
        nom = "OAR-Free_House_Gallery_I(4X4)-terrain"
        jj = tmp / "SL&OS" / "tuiles"
        jj.mkdir(parents=True)
        shutil.copy(src / "Lourde.glb", jj / (nom + ".glb"))
        run(DIST / "glb2tiles.py", jj / (nom + ".glb"), "--forcer", "--budget-tri", "300", "--min", "160", "--entier-poids", "64", "--nopause")
        (jj / (nom + ".zones.json")).write_text(json.dumps(ZL, indent=1), encoding="utf-8")
        zavant = (jj / (nom + ".zones.json")).read_bytes()
        (jj / "index.html").write_text("<!-- coquille d'une ancienne version -->", encoding="utf-8")
        (jj / "index.html").unlink()   # Remove-Item de la commande PowerShell
        cmd = ["-o", jj / (nom + ".html"), "--shared-shell", "--tiles", jj / (nom + ".tiles.json"), "--sea-y", "18.5", "--presence-url", "ws://ADRESSE:8765", "--chat", "--target", "392,68,-373"]
        r = html(*cmd)
        cj = json.loads((jj / (nom + ".config.json")).read_text(encoding="utf-8"))
        rapport(r.returncode == 0 and (jj / (nom + ".zones.json")).read_bytes() == zavant and "rien n'est copié" in r.stdout, "commande sans --zones : tuiles non copiées, X.zones.json existant conservé octet pour octet", r.stdout[-300:])
        rapport(cj["target"] == [392, 68, -373] and cj["targetExplicit"] is True and cj["seaY"] == 18.5 and cj["chat"] is True and cj["presenceUrl"].startswith("ws://") and "0.0.0.0" not in cj["presenceUrl"], "la config reprend --target, --sea-y, --presence-url, --chat", {k: cj[k] for k in ("target", "targetExplicit", "seaY", "chat", "presenceUrl")})
        rapport((jj / "index.html").is_file() and "Chargement du sol" in (jj / "index.html").read_text(encoding="utf-8"), "la coquille est celle de cette version")
        proc3, port3 = serveur(jj)
        try:
            o = Onglet(br)
            await o.ouvrir(f"http://127.0.0.1:{port3}/index.html?region={nom}#spawn=default")
            await o.marcheur(90)
            w = await o.walk()
            rapport(proche([w["pos"][0], w["pos"][2]], [DFX, DFZ], 0.6) and not o.errs, "nom de région avec parenthèses : la page s'ouvre et l'avatar arrive à l'arrivée du lien", (w["pos"], o.errs))
            await o.fermer()
        finally:
            proc3.kill()

        await br.close()


asyncio.run(main())
print("\nMESURES (journal par tuile lourde) :")
for etiq, m in MESURES:
    print(f"  {etiq} {m['file'].split('/')[-1]} : {m['bytes'] / 1048576:.1f} Mo, {m['tri']} triangles, démarrage différé {m['startWaitMs']} ms, téléchargement {m['downloadMs']} ms, analyse {m['parseMs']} ms, attente en file {m['queueMs']} ms, grille {m['gridMs']} ms (écoulé {m['gridWallMs']} ms), total {m['totalMs']} ms")
print("\nRÉSULTAT : " + ("tout est passé" if not bad else f"ÉCHEC ({bad})"))
sys.exit(1 if bad else 0)
