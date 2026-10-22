#!/usr/bin/env python3
"""Tests v30 : la coquille charge une région découpée en tuiles par tools/glb2tiles.py (mode tuiles, champ « tiles » de X.config.json).

Région synthétique fabriquée ici : sol de 8 x 8 patches de 64 m (objets racine « Terrain i,j », bords communs, hauteur continue,
hors de l'origine), 24 maisons (cubes, un matériau texturé), découpée par glb2tiles.py en plus de 4 tuiles. Pages générées par
glb2html.py --shared-shell -o X.html --tiles X.tiles.json, servies par http.server, ouvertes dans Chromium sans tête.
Les réponses des tuiles sont retenues, retardées ou remplacées avec page.route (aucun réseau).

Vérifie : génération (config, rien de copié si les tuiles sont à côté de la page, copie sinon, noms refusés) ; au démarrage seules les
tuiles proches sont chargées ; marcher sur 300 m charge les suivantes et décharge les lointaines (groupes, renderer.info.memory) ;
hauteur du sol continue aux frontières, jamais sous le sol ; déplacement bloqué tant que la tuile n'est pas prête, puis repris ;
F attend la tuile ; téléportation vers une zone non chargée ; budget tileMaxTri ; tuile en 404 ou corrompue sans plantage puis nouvelle
tentative ; ?rayon= ; rotation ; ?region=NOM avec une autre région sans tuiles dans le même dossier ; zones libres oui, zones liées ignorées ;
aucune erreur JavaScript ; sans « tiles » la config ne change pas.

Prérequis : pip install playwright ; python build.py avant.
Variables facultatives : THREE_DIR (paquet npm three, hors ligne), CHROMIUM (chemin de l'exécutable).
Lancer : python tests/tuiles.py
"""
import asyncio, json, math, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST, DATA = ROOT / "dist", ROOT / "tests" / "data"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_tuiles_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


# ---------- fabrication du GLB synthétique ----------
FMT = {5123: "H", 5125: "I", 5126: "f"}


class B:
    def __init__(self):
        self.bin = bytearray()
        self.j = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": []}], "nodes": [], "meshes": [], "accessors": [], "bufferViews": []}

    def vue(self, data, target=None):
        while len(self.bin) % 4:
            self.bin.append(0)
        v = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": len(data)}
        if target:
            v["target"] = target
        self.bin += data
        self.j["bufferViews"].append(v)
        return len(self.j["bufferViews"]) - 1

    def acc(self, v, comp, count, typ, mn=None, mx=None):
        a = {"bufferView": v, "componentType": comp, "count": count, "type": typ}
        if mn is not None:
            a["min"], a["max"] = mn, mx
        self.j["accessors"].append(a)
        return len(self.j["accessors"]) - 1

    def mesh(self, verts, idx, mat=None, uv=False):
        d = b"".join(struct.pack("<3f", *v) for v in verts)
        pos = self.acc(self.vue(d, 34962), 5126, len(verts), "VEC3", [min(v[k] for v in verts) for k in range(3)], [max(v[k] for v in verts) for k in range(3)])
        nor = self.acc(self.vue(struct.pack("<3f", 0, 1, 0) * len(verts), 34962), 5126, len(verts), "VEC3")
        ix = self.acc(self.vue(struct.pack("<%dH" % len(idx), *idx), 34963), 5123, len(idx), "SCALAR")
        at = {"POSITION": pos, "NORMAL": nor}
        if uv:
            at["TEXCOORD_0"] = self.acc(self.vue(b"".join(struct.pack("<2f", (i % 2), (i // 2) % 2) for i in range(len(verts))), 34962), 5126, len(verts), "VEC2")
        pr = {"attributes": at, "indices": ix}
        if mat is not None:
            pr["material"] = mat
        self.j["meshes"].append({"primitives": [pr]})
        return len(self.j["meshes"]) - 1

    def noeud(self, nom, mesh, extras=None):
        n = {"name": nom, "mesh": mesh}
        if extras:
            n["extras"] = extras
        self.j["nodes"].append(n)
        self.j["scenes"][0]["nodes"].append(len(self.j["nodes"]) - 1)

    def ecrire(self, chemin):
        j = dict(self.j)
        j["buffers"] = [{"byteLength": len(self.bin) + (-len(self.bin) % 4)}]
        jb = json.dumps(j).encode()
        jb += b" " * (-len(jb) % 4)
        bn = bytes(self.bin) + bytes(-len(self.bin) % 4)
        with open(chemin, "wb") as f:
            f.write(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(jb) + 8 + len(bn)))
            f.write(struct.pack("<II", len(jb), 0x4E4F534A) + jb + struct.pack("<II", len(bn), 0x004E4942) + bn)


def png():
    import zlib

    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(b"\x00\xff\x00\x00")) + ch(b"IEND", b"")


X0, Z0, P, NP, NQ = 100.0, -300.0, 64.0, 8, 8     # coin de la région, patch (m), patches par côté, quads par côté de patch


def hauteur(x, z):
    """Hauteur du sol : continue, lisse, pente au plus 0,09 ; partagée par tous les patches (bords communs)."""
    return 12 + 3 * math.sin(x / 37) + 2 * math.cos(z / 53)


def fabriquer_glb(chemin):
    b = B()
    for i in range(NP):
        for j in range(NP):
            v, idx = [], []
            for q in range(NQ + 1):
                for p in range(NQ + 1):
                    x, z = X0 + P * i + P * p / NQ, Z0 + P * j + P * q / NQ
                    v.append((x, hauteur(x, z), z))
            for q in range(NQ):
                for p in range(NQ):
                    a = q * (NQ + 1) + p
                    idx += [a, a + 1, a + NQ + 1, a + 1, a + NQ + 2, a + NQ + 1]
            b.noeud(f"Terrain {i},{j}", b.mesh(v, idx), {"terrain": True})
    # 24 maisons : cubes de 6 x 4 x 6 m, posés sur le sol ; un matériau texturé
    b.j["images"] = [{"bufferView": b.vue(png()), "mimeType": "image/png"}]
    b.j["samplers"] = [{}]
    b.j["textures"] = [{"source": 0, "sampler": 0}]
    b.j["materials"] = [{"name": "brique", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}]
    for k in range(24):
        cx, cz = X0 + 40 + (k % 6) * 90 + (k // 6) * 7, Z0 + 40 + (k // 6) * 120 + (k % 3) * 11
        y = hauteur(cx, cz)
        v = [(cx + dx * 3, y + dy * 4, cz + dz * 3) for dy in (0, 1) for dz in (-1, 1) for dx in (-1, 1)]
        idx = [0, 1, 3, 0, 3, 2, 4, 6, 7, 4, 7, 5, 0, 4, 5, 0, 5, 1, 2, 3, 7, 2, 7, 6, 0, 2, 6, 0, 6, 4, 1, 5, 7, 1, 7, 3]
        b.noeud(f"Maison {k}", b.mesh(v, idx, mat=0, uv=True))
    b.ecrire(chemin)


def run(script, *a, cwd=None, ok=True):
    r = subprocess.run([sys.executable, str(script), *map(str, a)], capture_output=True, text=True, cwd=cwd or tmp)
    if ok and r.returncode:
        sys.exit(f"[ECHEC] {script.name} {' '.join(map(str, a))}\n{r.stdout}{r.stderr}")
    return r


def html(*a, ok=True):
    return run(DIST / "glb2html.py", *a, *vend, ok=ok)


# ---------- région : GLB -> tuiles -> pages ----------
src = tmp / "source"
src.mkdir()
fabriquer_glb(src / "Tuilee.glb")
run(DIST / "glb2tiles.py", src / "Tuilee.glb", "--forcer", "--budget-tri", "700", "--min", "64", "--nopause", "--sans-references")   # tuiles au format de la v31 : les zones liées y restent ignorées (v32 : tests/v32.py)
doc = json.loads((src / "Tuilee.tiles.json").read_text(encoding="utf-8"))
TILES = doc["tiles"]
rapport(len(TILES) >= 4 and all((src / t["file"]).is_file() for t in TILES), f"glb2tiles : {len(TILES)} tuiles (au moins 4)", len(TILES))

site = tmp / "site"
site.mkdir()
# 1. tuiles ailleurs : copiées ; relancer ne recopie rien
r = html("-o", site / "Tuilee.html", "--shared-shell", "--tiles", src / "Tuilee.tiles.json", "--rotate", "0")
rapport((site / "Tuilee.tiles.json").is_file() and (site / TILES[0]["file"]).is_file() and f"{len(TILES)} copiée(s)" in r.stdout, "tuiles ailleurs : copiées, message", r.stdout)
r = html("-o", site / "Tuilee.html", "--shared-shell", "--tiles", src / "Tuilee.tiles.json")
rapport(f"0 copiée(s) ({0.0:.1f} Mo), {len(TILES)} déjà présente(s)" in r.stdout, "relancer ne recopie pas", r.stdout)
cfg = json.loads((site / "Tuilee.config.json").read_text(encoding="utf-8"))
rapport(cfg["tiles"] == "Tuilee.tiles.json" and cfg["tileRadius"] == 150 and cfg["tileMargin"] == 60 and cfg["tileMaxMo"] == 200 and cfg["tileMaxTri"] == 8000000 and cfg["tileConcurrency"] == 4 and cfg["zones"] == [], "config : champ tiles et valeurs par défaut", cfg)
rapport(not (site / "Tuilee.glb").exists() and (site / "index.html").is_file() and (site / "lib").is_dir(), "pas de X.glb ; coquille et lib/ écrites")
# 2. tuiles déjà à côté de la page : rien n'est copié
r = html("-o", src / "Tuilee.html", "--shared-shell", "--tiles", src / "Tuilee.tiles.json")
rapport("déjà à côté de la page : rien n'est copié" in r.stdout, "tuiles à côté de la page : rien n'est copié", r.stdout)
shutil.rmtree(src / "lib"), (src / "index.html").unlink()
# 3. refus : nom de tuile dangereux, .glb en plus, sans -o
mauvais = json.loads(json.dumps(doc))
mauvais["tiles"][0]["file"] = "../evil.glb"
(tmp / "mauvais.tiles.json").write_text(json.dumps(mauvais), encoding="utf-8")
r = html("-o", tmp / "m" / "M.html", "--shared-shell", "--tiles", tmp / "mauvais.tiles.json", ok=False)
rapport(r.returncode != 0 and "entrée de tuile invalide" in r.stderr + r.stdout and not (tmp / "m").exists(), "nom de tuile avec .. refusé, rien d'écrit", r.stderr)
r = html(src / "Tuilee.glb", "-o", tmp / "m" / "M.html", "--tiles", src / "Tuilee.tiles.json", ok=False)
rapport(r.returncode != 0 and "ne donne pas de fichier .glb" in r.stderr + r.stdout, "--tiles avec un .glb refusé")
r = html("--tiles", src / "Tuilee.tiles.json", ok=False)
rapport(r.returncode != 0 and "demande -o" in r.stderr + r.stdout, "--tiles sans -o refusé")
# 4. région ordinaire dans le même dossier (coquille commune identique) : config sans aucune clé de tuiles
r = html(DATA / "walk3.glb", "-o", site / "Ordinaire.html", "--shared-shell")
rapport("déjà présente et identique" in r.stdout, "même coquille pour une région sans tuiles", r.stdout)
cfo = json.loads((site / "Ordinaire.config.json").read_text(encoding="utf-8"))
rapport(not any(k.startswith("tile") for k in cfo), "région sans tuiles : aucune clé de tuiles dans la config", [k for k in cfo if k.startswith("tile")])
# 5. variantes : rotation 90 et budget serré, chacune dans son dossier (mêmes tuiles par lien)
def variante(nom, *opts):
    d = tmp / nom
    d.mkdir()
    shutil.copytree(site / "lib", d / "lib")
    shutil.copy(site / "index.html", d / "index.html")
    for f in ("Tuilee.tiles.json", "Tuilee.zones.json"):
        shutil.copy(site / f, d / f)
    shutil.copytree(site / "Tuilee.tiles", d / "Tuilee.tiles")
    html("-o", d / "Tuilee.html", "--shared-shell", "--tiles", d / "Tuilee.tiles.json", *opts)
    return d


# zones : une zone libre, une zone liée à un élément (ignorée), une arrivée par défaut
ZONES = [
    {"id": "default", "type": "spawn", "x": 130, "y": hauteur(130, -100), "z": -100, "yaw": -math.pi / 2},
    {"id": "libre", "type": "url", "label": "Lien libre", "target": "https://example.org/", "x": 140, "y": hauteur(140, -100), "z": -100, "radius": 3},
    {"id": "liee", "type": "url", "label": "Lien lié", "target": "https://example.org/", "mesh": "Maison 3", "x": 0, "y": 0, "z": 0, "radius": 3},
]
(site / "Tuilee.zones.json").write_text(json.dumps(ZONES), encoding="utf-8")
VAR_ROT = variante("rot", "--rotate", "90", "--zones", site / "Tuilee.zones.json")
rapport(json.loads((VAR_ROT / "Tuilee.config.json").read_text(encoding="utf-8"))["target"][0] != json.loads((site / "Tuilee.config.json").read_text(encoding="utf-8"))["target"][0], "--rotate 90 : cible par défaut tournée")
max_tri = max(t["triangles"] for t in TILES)
VAR_BUD = variante("bud", "--tile-radius", "120", "--tile-margin", "30", "--tile-max-tri", str(int(max_tri * 4.5)), "--zones", site / "Tuilee.zones.json")
VAR_STD = variante("std", "--tile-radius", "100", "--tile-margin", "30", "--zones", site / "Tuilee.zones.json")
html("-o", site / "Tuilee.html", "--shared-shell", "--tiles", site / "Tuilee.tiles.json", "--tile-radius", "100", "--tile-margin", "30", "--zones", site / "Tuilee.zones.json")


def serveur(dossier):
    with socket.socket() as so:
        so.bind(("127.0.0.1", 0))
        port = so.getsockname()[1]
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=dossier, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return proc, port
        except OSError:
            time.sleep(0.1)
    proc.kill()
    sys.exit("[ECHEC] http.server ne démarre pas")


def boite_dist(t, x, z, rot=0):
    """Distance en plan de (x,z) à la boîte de la tuile t (repère d'origine tourné de rot degrés autour de Y)."""
    a = math.radians(rot)
    pts = [(x0 * math.cos(a) + z0 * math.sin(a), -x0 * math.sin(a) + z0 * math.cos(a)) for x0 in (t["min"][0], t["max"][0]) for z0 in (t["min"][2], t["max"][2])]
    lo, hi = [min(p[k] for p in pts) for k in (0, 1)], [max(p[k] for p in pts) for k in (0, 1)]
    return math.hypot(max(lo[0] - x, 0, x - hi[0]), max(lo[1] - z, 0, z - hi[1]))


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)

        class Onglet:
            """Une page ouverte sur la région ; garde[fichier] = Event à lever pour libérer la réponse ; faux[fichier] = (statut, corps)."""
            def __init__(self):
                self.errs, self.warns, self.garde, self.faux, self.demandes = [], [], {}, {}, []

            async def ouvrir(self, url, port=None):
                ctx = await br.new_context(viewport={"width": 700, "height": 500})
                self.pg = await ctx.new_page()
                self.pg.on("pageerror", lambda e: self.errs.append(str(e)))
                self.pg.on("console", lambda m: self.warns.append(m.text) if m.type == "warning" else None)
                await self.pg.route("**/*.glb", self.route)
                await self.pg.goto(url)
                return self

            async def route(self, route):
                nom = route.request.url.split("/")[-1]
                self.demandes.append(nom)
                if nom in self.faux:
                    st, corps = self.faux[nom]
                    return await route.fulfill(status=st, body=corps)
                if nom in self.garde:
                    await self.garde[nom].wait()
                try:
                    await route.continue_()
                except Exception:
                    pass

            async def ev(self, js, arg=None):
                return await self.pg.evaluate(js, arg)

            async def etat(self):
                return await self.ev("window.__viewer.tilesState()")

            async def attendre(self, cond_js, timeout=40):
                await self.pg.wait_for_function(cond_js, timeout=timeout * 1000)

            async def charge(self, timeout=60):
                await self.attendre("document.getElementById('msg') === null", timeout)

            async def marcher(self, n, dt=0.1, courir=True):
                """n pas de walkTick(dt) avec W (et Maj) enfoncées ; rend les positions [x, y, z, au sol]."""
                return await self.ev("""([n, dt, run]) => {
                    const v = window.__viewer, out = [], k = c => window.dispatchEvent(new KeyboardEvent('keydown', { code: c }));
                    k('KeyW'); if (run) k('ShiftLeft');
                    for (let i = 0; i < n; i++) { v.walkTick(dt); const w = v.getWalk(); out.push(w.pos.concat([w.grounded])); }
                    ['KeyW', 'ShiftLeft'].forEach(c => window.dispatchEvent(new KeyboardEvent('keyup', { code: c })));
                    return out; }""", [n, dt, courir])

            async def pos(self):
                return await self.ev("window.__viewer.getWalk().pos")

        proc, port = serveur(site)
        base = f"http://127.0.0.1:{port}/index.html?region=Tuilee"
        ROT = 0
        try:
            # ---------- A. démarrage : seules les tuiles proches ; mémoire de base ; info ----------
            o = Onglet()
            for t in TILES:   # tout retenu : mesure de la mémoire de base avant la moindre tuile
                o.garde[t["file"].split("/")[-1]] = asyncio.Event()
            await o.ouvrir(base)
            await o.attendre("window.__viewer && window.__viewer.tilesState().total > 0 && window.__viewer.tilesState().overview.state === 'ready'")
            await o.pg.wait_for_timeout(500)   # la vue d'ensemble (chargée avant les tuiles) est dessinée : sa géométrie fait partie de la base
            base_mem = await o.ev("({ g: window.__viewer.renderer.info.memory.geometries, t: window.__viewer.renderer.info.memory.textures })")
            e0 = await o.etat()
            rapport(e0["total"] == len(TILES) and not e0["ready"], "index lu, aucune tuile prête tant qu'elles sont retenues", e0)
            for ev_ in o.garde.values():
                ev_.set()
            await o.charge()
            e = await o.etat()
            tx, tz = await o.ev("[window.__viewer.controls.target.x, window.__viewer.controls.target.z]")
            proches = sorted(t["file"] for t in TILES if boite_dist(t, tx, tz) <= 100)
            loin = [t["file"] for t in TILES if boite_dist(t, tx, tz) > 130]
            rapport(proches and set(proches) <= set(e["ready"]) and not (set(loin) & set(e["ready"])) and len(e["ready"]) < len(TILES), "au démarrage : les tuiles proches sont chargées, les lointaines non",
                    (len(proches), len(e["ready"]), len(TILES)))
            rapport(sorted(g.replace("tile:", "") for g in e["groups"]) == sorted(e["ready"]) and all(g.startswith("tile:") for g in e["groups"]), "un groupe nommé par tuile chargée", e["groups"][:3])
            tri_prets = sum(t["triangles"] for t in TILES if t["file"] in e["ready"])
            rapport(e["tri"] == tri_prets and abs(e["bytes"] - sum(t["bytes"] for t in TILES if t["file"] in e["ready"])) < 1, "compteurs de l'état = somme des tuiles chargées", (e["tri"], tri_prets))
            ligne = await o.ev("document.getElementById('tilesInfo').textContent")
            rapport(ligne.startswith("Tuiles : ") and f"/ {len(TILES)}" in ligne and "triangles" in ligne and "Mo" in ligne and not await o.ev("document.getElementById('tilesInfo').hidden"), "ligne d'information : tuiles chargées / total, Mo, triangles", ligne)
            titre = await o.ev("document.title")
            rapport(titre == "Tuilee" and not o.errs, "titre = salon, aucune erreur JavaScript au démarrage", (titre, o.errs))
            # mémoire GPU : géométries et textures = base + celles des groupes
            mem = await o.ev("""(() => { const v = window.__viewer, G = new Set(), T = new Set();
                v.model.traverse(o => { if (o.geometry) G.add(o.geometry); if (o.material) for (const m of (Array.isArray(o.material) ? o.material : [o.material])) for (const k in m) if (m[k] && m[k].isTexture) T.add(m[k]); });
                return { g: v.renderer.info.memory.geometries, t: v.renderer.info.memory.textures, G: G.size, T: T.size }; })()""")
            rapport(mem["g"] == base_mem["g"] + mem["G"] and mem["t"] == base_mem["t"] + mem["T"] and mem["G"] > 0 and mem["T"] > 0, "renderer.info.memory = base + contenu des groupes", (mem, base_mem))
            # zones : libre oui, liée ignorée avec avertissement
            zs = await o.ev("window.__viewer.getZones().map(z => z.id)")
            rapport(zs == ["default", "libre"] and any("liee" in w and "ignorée" in w for w in o.warns), "zones : libres gardées, zone liée ignorée avec avertissement", (zs, o.warns))

            # ---------- B. décharge complète : mémoire de retour au niveau de base ----------
            await o.pg.wait_for_timeout(5000)   # fin du point de départ forcé
            await o.ev("window.__viewer.controls.target.set(9000, 20, 9000)")
            await o.attendre("window.__viewer.tilesState().ready.length === 0 && window.__viewer.tilesState().inflight === 0", 20)
            mem = await o.ev("({ g: window.__viewer.renderer.info.memory.geometries, t: window.__viewer.renderer.info.memory.textures, n: window.__viewer.model.children.length })")
            rapport(mem["n"] == 0 and mem["g"] == base_mem["g"] and mem["t"] == base_mem["t"], "tout déchargé : groupes 0, géométries et textures revenues au niveau de base", (mem, base_mem))
            await o.ev("window.__viewer.controls.target.set(%f, 20, %f)" % (tx, tz))
            await o.attendre("window.__viewer.tilesState().ready.length > 0", 30)
            rapport(not o.errs, "rechargement après décharge complète : aucune erreur JavaScript", o.errs)
            await o.pg.close()

            # ---------- C. marche de 300 m : chargement, déchargement, sol continu, jamais sous le sol ----------
            o = Onglet()
            await o.ouvrir(base + "#spawn=default&name=Test")
            await o.charge()
            await o.attendre("window.__viewer.walking", 30)
            w0 = await o.pos()
            rapport(abs(w0[0] - 130) < 1 and abs(w0[1] - hauteur(130, -100)) < 0.2, "arrivée #spawn=default : avatar au point d'arrivée, sur le sol", w0)
            echant, max_tri_vu, ok_budget_cfg = [], 0, True
            x_cible = w0[0] + 300
            frontieres = set()
            for _ in range(120):
                pts = await o.marcher(20)
                echant += pts
                s = await o.etat()
                max_tri_vu = max(max_tri_vu, s["tri"])
                await o.pg.wait_for_timeout(120)
                if pts[-1][0] >= x_cible:
                    break
            await o.pg.wait_for_timeout(600)
            fin = await o.pos()
            rapport(fin[0] >= x_cible - 1, f"l'avatar a avancé de 300 m (x {w0[0]:.0f} -> {fin[0]:.0f})", fin)
            # continuité : Δy proportionnel au déplacement, au sol ; vérité terrain
            ok_cont, pire = True, 0
            for a, b in zip(echant, echant[1:]):
                dx = math.hypot(b[0] - a[0], b[2] - a[2])
                if dx > 5:
                    continue          # saut entre deux appels (extra mouvement de la boucle réelle)
                pire = max(pire, abs(b[1] - a[1]) - 0.1 * dx)
                ok_cont &= abs(b[1] - a[1]) <= 0.1 * dx + 0.02
            rapport(ok_cont, "hauteur du sol continue (aucun saut de marche aux frontières de tuiles)", pire)
            sous = [pt for pt in echant if pt[1] < hauteur(pt[0], pt[2]) - 0.15]
            rapport(not sous and len(echant) > 200, "l'avatar ne tombe jamais sous le sol", sous[:2])
            cx = [t for t in TILES]
            croise = sum(1 for t in cx if w0[0] < t["max"][0] < fin[0])
            rapport(croise >= 2, f"{croise} frontières de tuiles franchies", croise)
            await o.attendre("window.__viewer.tilesState().loadingFiles.length === 0", 30)
            e = await o.etat()
            attendues = {t["file"] for t in TILES if boite_dist(t, fin[0], fin[2]) <= 100}
            trop_loin = {t["file"] for t in TILES if boite_dist(t, fin[0], fin[2]) > 130}
            rapport(attendues <= set(e["ready"]) and not (trop_loin & set(e["ready"])), "après 300 m : les tuiles proches sont chargées, les lointaines déchargées", (len(attendues), sorted(e["ready"])[:4]))
            depart = {t["file"] for t in TILES if boite_dist(t, w0[0], w0[2]) <= 100} - attendues
            rapport(depart and not (depart & set(e["ready"])), "les tuiles du départ ont été déchargées", sorted(depart & set(e["ready"])))
            mem = await o.ev("""(() => { const v = window.__viewer, G = new Set(), T = new Set();
                v.model.traverse(o => { if (o.geometry) G.add(o.geometry); if (o.material) for (const m of (Array.isArray(o.material) ? o.material : [o.material])) for (const k in m) if (m[k] && m[k].isTexture) T.add(m[k]); });
                return { g: v.renderer.info.memory.geometries, t: v.renderer.info.memory.textures, G: G.size, T: T.size, n: v.model.children.length }; })()""")
            rapport(mem["n"] == len(e["groups"]) == len(e["ready"]) and mem["g"] <= base_mem["g"] + mem["G"] and mem["t"] <= base_mem["t"] + mem["T"] and mem["g"] > base_mem["g"], "après déchargements : groupes = tuiles chargées, géométries et textures GPU bornées par celles des groupes (rien ne fuit ; seules les tuiles vues sont envoyées au GPU)", (mem, base_mem, len(e["ready"])))
            rapport(max_tri_vu <= 8000000, "budget par défaut (8 M triangles) respecté", max_tri_vu)
            rapport(not o.errs, "marche : aucune erreur JavaScript", o.errs)

            # ---------- D. téléportation vers une zone non chargée (portail interne) ----------
            cible = [560, hauteur(560, 150), 150]
            avant = await o.pos()
            await o.ev("window.__viewer.teleportTo(%s, 0)" % json.dumps(cible))
            apres = await o.pos()
            rapport(abs(apres[0] - avant[0]) < 5 and await o.ev("window.__viewer.tilesState().waiting"), "téléportation vers une tuile non chargée : l'avatar attend, indicateur actif", (avant, apres))
            await o.attendre("Math.abs(window.__viewer.getWalk().pos[0] - 560) < 3", 30)
            ap = await o.pos()
            rapport(abs(ap[1] - hauteur(560, 150)) < 0.2, "puis il arrive sur le sol de la destination", ap)
            await o.pg.close()

            # ---------- E. déplacement bloqué tant que la tuile n'est pas prête, puis repris ----------
            o = Onglet()
            await o.ouvrir(base + "#spawn=default&name=Test")
            await o.charge()
            await o.attendre("window.__viewer.walking", 30)
            P_ = (430.0, -100.0)
            tenues = [t for t in TILES if t["min"][0] - 0.5 <= P_[0] <= t["max"][0] + 0.5 and t["min"][2] - 0.5 <= P_[1] <= t["max"][2] + 0.5]
            bord = min(t["min"][0] for t in tenues)
            e = await o.etat()
            tenues = [t for t in tenues if t["file"] not in e["ready"]]
            for t in tenues:
                o.garde[t["file"].split("/")[-1]] = asyncio.Event()
            bord = min(t["min"][0] for t in tenues) if tenues else None
            rapport(bool(tenues), f"{len(tenues)} tuile(s) retenue(s) sur le chemin", tenues)
            for _ in range(60):
                await o.marcher(20)
                await o.pg.wait_for_timeout(100)
                if (await o.pos())[0] > bord - 2:
                    break
            await o.marcher(40)
            bloque = await o.pos()
            e = await o.etat()
            visible = await o.ev("!document.getElementById('groundWait').hidden && document.getElementById('groundWait').textContent")
            rapport(bloque[0] <= bord + 0.6 and bloque[0] > bord - 12, f"bloqué au bord de la tuile non prête (x {bloque[0]:.1f}, bord {bord:.1f})", (bloque, bord))
            rapport(visible == "Chargement du sol…" and e["waiting"], "indicateur texte « Chargement du sol… » affiché", visible)
            await o.marcher(60)
            rapport((await o.pos())[0] <= bord + 0.6 and not await o.ev("window.__viewer.getWalk().pos[1] < 0"), "toujours bloqué, ni chute ni saut", await o.pos())
            for t in tenues:
                o.garde[t["file"].split("/")[-1]].set()
            await o.attendre("window.__viewer.tilesState().ready.length > 0 && !window.__viewer.tilesState().loadingFiles.length", 30)
            await o.pg.wait_for_timeout(400)
            for _ in range(10):
                await o.marcher(10)
                await o.pg.wait_for_timeout(50)
            reprise = await o.pos()
            rapport(reprise[0] > bord + 3 and abs(reprise[1] - hauteur(reprise[0], reprise[2])) < 0.2, f"déplacement repris dès que la tuile est prête (x {reprise[0]:.1f})", reprise)
            await o.pg.wait_for_timeout(800)
            rapport(await o.ev("document.getElementById('groundWait').hidden"), "l'indicateur disparaît")
            rapport(not o.errs, "blocage : aucune erreur JavaScript", o.errs)
            await o.pg.close()

            # ---------- F. la touche F attend la tuile sous l'avatar ----------
            o = Onglet()
            for t in TILES:
                o.garde[t["file"].split("/")[-1]] = asyncio.Event()
            await o.ouvrir(base)
            await o.attendre("window.__viewer && window.__viewer.tilesState().total > 0")
            await o.pg.keyboard.press("KeyF")
            await o.pg.wait_for_timeout(300)
            marche, attente = await o.ev("[window.__viewer.walking, !document.getElementById('groundWait').hidden]")
            rapport(not marche and attente, "F avant la tuile : la promenade attend, indicateur affiché", (marche, attente))
            for ev_ in o.garde.values():
                ev_.set()
            await o.attendre("window.__viewer.walking", 40)
            w = await o.pos()
            rapport(abs(w[1] - hauteur(w[0], w[2])) < 0.2, "la promenade démarre sur le sol dès la tuile prête", w)
            await o.pg.keyboard.press("KeyF")
            await o.pg.wait_for_timeout(200)
            await o.pg.close()
            # F de nouveau pendant l'attente : annule
            o = Onglet()
            for t in TILES:
                o.garde[t["file"].split("/")[-1]] = asyncio.Event()
            await o.ouvrir(base)
            await o.attendre("window.__viewer && window.__viewer.tilesState().total > 0")
            await o.pg.keyboard.press("KeyF")
            await o.pg.wait_for_timeout(200)
            await o.pg.keyboard.press("KeyF")
            await o.pg.wait_for_timeout(200)
            for ev_ in o.garde.values():
                ev_.set()
            await o.charge()
            await o.pg.wait_for_timeout(500)
            rapport(not await o.ev("window.__viewer.walking") and await o.ev("document.getElementById('groundWait').hidden"), "F de nouveau pendant l'attente : annulée")
            await o.pg.close()

            # ---------- G. tuile en 404 et tuile corrompue : pas de plantage, nouvelle tentative ----------
            o = Onglet()
            vite = [t for t in TILES if boite_dist(t, tx, tz) <= 100]
            cass, corrompue = vite[0]["file"].split("/")[-1], vite[-1]["file"].split("/")[-1]
            o.faux[cass] = (404, b"absent")
            if corrompue != cass:
                o.faux[corrompue] = (200, b"ceci n'est pas un GLB")
            await o.ouvrir(base)
            await o.charge()
            await o.pg.wait_for_timeout(1500)
            e = await o.etat()
            toast = await o.ev("document.getElementById('toast').textContent")
            attendus = {cass, corrompue}
            rapport({f.split("/")[-1] for f in e["failedFiles"]} == attendus and len(e["ready"]) == len(vite) - len(attendus) and "nouvelle tentative" in toast and not o.errs,
                    "tuiles en échec : signalées (message), les autres chargées, page vivante", (e["failedFiles"], len(e["ready"]), toast, o.errs))
            ligne = await o.ev("document.getElementById('tilesInfo').textContent")
            rapport("en échec" in ligne, "ligne d'information : tuiles en échec", ligne)
            o.faux.clear()
            await o.attendre("window.__viewer.tilesState().failedFiles.length === 0 && window.__viewer.tilesState().ready.length >= %d" % len(vite), 30)
            rapport(not o.errs, "nouvelle tentative réussie une fois la tuile disponible", o.errs)
            # marcher vers une tuile en échec : bloqué, sans chute
            await o.pg.close()
            o = Onglet()
            o.faux[cass] = (404, b"absent")
            await o.ouvrir(base)
            await o.charge()
            deja = await o.etat()
            await o.ev("window.__viewer.walkStart({ pos: [%f, 30, %f], yaw: 0 })" % (tx, tz))
            await o.pg.wait_for_timeout(500)
            tfail = next(t for t in TILES if t["file"].endswith(cass))
            marche = await o.ev("window.__viewer.walking")
            rapport(marche == (boite_dist(tfail, tx, tz) > 0.5), "F au-dessus d'une tuile en échec : attend ; ailleurs démarre", (marche, boite_dist(tfail, tx, tz)))
            await o.pg.close()

            # ---------- H. ?rayon= ----------
            nb = {}
            for r_ in (30, 400):
                o = Onglet()
                await o.ouvrir(f"{base}&rayon={r_}")
                await o.charge()
                await o.pg.wait_for_timeout(1500)
                e = await o.etat()
                nb[r_] = (len(e["ready"]), e["radius"])
                await o.pg.close()
            rapport(nb[30][1] == 30 and nb[400][1] == 400 and nb[30][0] < nb[400][0], "?rayon=NNN : rayon pris en compte (moins de tuiles à 30 m qu'à 400 m)", nb)
            # config : tileRadius lu dans X.config.json sans ?rayon
            o = Onglet()
            await o.ouvrir(base)
            await o.charge()
            rapport((await o.etat())["radius"] == 100, "tileRadius lu dans X.config.json", (await o.etat())["radius"])
            await o.pg.close()

            # ---------- I. budget tileMaxTri ----------
            proc2, port2 = serveur(VAR_BUD)
            try:
                o = Onglet()
                await o.ouvrir(f"http://127.0.0.1:{port2}/index.html?region=Tuilee#spawn=default&name=Test")
                await o.charge()
                await o.attendre("window.__viewer.walking", 30)
                maxi, mx, ev_budget = 0, 0, await o.ev("window.__viewer.tilesState().maxTri")
                for _ in range(60):
                    pts = await o.marcher(20)
                    s = await o.etat()
                    maxi = max(maxi, s["tri"])
                    mx = max(mx, len(s["ready"]))
                    await o.pg.wait_for_timeout(100)
                    if pts[-1][0] > 420:
                        break
                await o.pg.wait_for_timeout(800)
                s = await o.etat()
                pos = await o.pos()
                rapport(ev_budget == int(max_tri * 4.5) and maxi <= ev_budget and mx >= 2, f"budget tileMaxTri respecté ({maxi} <= {ev_budget}, {mx} tuiles au plus)", (maxi, ev_budget, mx))
                dans_rayon = [t for t in TILES if boite_dist(t, pos[0], pos[2]) <= 120]
                rapport(len(s["ready"]) < len(dans_rayon), f"le budget a bien retenu des tuiles du rayon ({len(s['ready'])} chargées sur {len(dans_rayon)} dans le rayon)", (len(s["ready"]), len(dans_rayon)))
                touche = [t for t in TILES if boite_dist(t, pos[0], pos[2]) < 0.5]
                rapport(pos[0] > 300 and all(t["file"] in s["ready"] for t in touche), "avec le budget serré, la tuile sous l'avatar est toujours chargée et la marche continue", (pos, [t["file"] for t in touche if t["file"] not in s["ready"]]))
                rapport(not o.errs, "budget : aucune erreur JavaScript", o.errs)
                await o.pg.close()
            finally:
                proc2.kill()

            # ---------- J. rotation de la région (90°) ----------
            proc3, port3 = serveur(VAR_ROT)
            try:
                o = Onglet()
                await o.ouvrir(f"http://127.0.0.1:{port3}/index.html?region=Tuilee#spawn=default&name=Test")
                await o.charge()
                await o.attendre("window.__viewer.walking", 30)
                z0 = ZONES[0]
                a = math.radians(90)
                rx, rz = z0["x"] * math.cos(a) + z0["z"] * math.sin(a), -z0["x"] * math.sin(a) + z0["z"] * math.cos(a)
                # les zones sont déjà dans le repère tourné : l'arrivée est à (130, -100) tel quel ; le sol y est celui de la région tournée
                w = await o.pos()
                ox = w[0] * math.cos(-a) + w[2] * math.sin(-a)
                oz = -w[0] * math.sin(-a) + w[2] * math.cos(-a)
                rapport(abs(w[1] - hauteur(ox, oz)) < 0.2 and not o.errs, "rotation 90 : le sol sous l'avatar est celui de la région tournée", (w, ox, oz, o.errs))
                await o.pg.close()
            finally:
                proc3.kill()

            # ---------- K. région ordinaire du même dossier : coquille inchangée ----------
            o = Onglet()
            await o.ouvrir(f"http://127.0.0.1:{port}/index.html?region=Ordinaire")
            await o.charge()
            rapport(not await o.ev("window.__viewer.tiled") and not o.errs, "?region=Ordinaire (sans tuiles) : chargée comme avant, aucune erreur", o.errs)
            await o.pg.close()
            # refus de ?region= avec une adresse, même avec des tuiles
            o = Onglet()
            await o.ouvrir(f"http://127.0.0.1:{port}/index.html?region=https://exemple.org/x")
            await o.pg.wait_for_timeout(800)
            texte = await o.ev("document.getElementById('msg') ? document.getElementById('msg').textContent : ''")
            rapport("refusé" in texte and not [d for d in o.demandes], "?region= avec une adresse : refusé, aucune requête de tuile", (texte, o.demandes))
            await o.pg.close()
            # tiles dans la config avec un chemin dangereux : refus, aucune requête
            ccfg = json.loads((site / "Tuilee.config.json").read_text(encoding="utf-8"))
            for mauvais_chemin in ("../x.tiles.json", "https://exemple.org/x.json", "a:b.json"):
                (site / "Piege.config.json").write_text(json.dumps(dict(ccfg, tiles=mauvais_chemin)), encoding="utf-8")
                o = Onglet()
                await o.ouvrir(f"http://127.0.0.1:{port}/index.html?region=Piege")
                await o.pg.wait_for_timeout(700)
                texte = await o.ev("document.getElementById('msg') ? document.getElementById('msg').textContent : ''")
                rapport("refusée" in texte and not o.demandes, f"champ tiles « {mauvais_chemin} » refusé", (texte, o.demandes))
                await o.pg.close()
        finally:
            proc.kill()
            await br.close()


asyncio.run(main())
print("\nRÉSULTAT : " + ("tout est passé" if not bad else f"{bad} échec(s)"))
sys.exit(1 if bad else 0)
