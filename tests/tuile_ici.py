#!/usr/bin/env python3
"""Test 1.4.2 : la ligne « Tuiles » du panneau d'etat donne le nom de la tuile (ou des tuiles) sous l'avatar.

Region synthetique (sol plat, 8 x 8 patches de 64 m) decoupee par glb2tiles.py en plusieurs tuiles. Verifie : en promenade, state().here et la
ligne de la page (#tilesInfo) donnent exactement les tuiles dont la boite contient l'avatar (calcul independant, tolerance 0,5 m) apres chaque
tronçon de marche de 300 m qui franchit des frontieres ; la ligne se met a jour sans autre evenement (chargement) ; apres une teleportation ;
hors promenade (vue globale) la mention disparait ; aucune erreur JavaScript.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM.
Lancer : python tests/tuile_ici.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, math, os, pathlib, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_tuile_ici_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


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



X0, Z0, P, NP, NQ = 100.0, -300.0, 64.0, 8, 8


def fabriquer_glb(chemin):
    b = B()
    for i in range(NP):
        for j in range(NP):
            v, idx = [], []
            for q in range(NQ + 1):
                for p in range(NQ + 1):
                    v.append((X0 + P * i + P * p / NQ, 12.0, Z0 + P * j + P * q / NQ))
            for q in range(NQ):
                for p in range(NQ):
                    a = q * (NQ + 1) + p
                    idx += [a, a + 1, a + NQ + 1, a + 1, a + NQ + 2, a + NQ + 1]
            b.noeud(f"Terrain {i},{j}", b.mesh(v, idx), {"terrain": True})
    b.ecrire(chemin)


def run(script, *a):
    r = subprocess.run([sys.executable, str(script), *map(str, a)], capture_output=True, text=True, cwd=tmp)
    if r.returncode:
        sys.exit(f"[ECHEC] {script.name} {' '.join(map(str, a))}\n{r.stdout}{r.stderr}")
    return r


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
    sys.exit("[ECHEC] http.server ne demarre pas")


src = tmp / "source"
src.mkdir()
fabriquer_glb(src / "Tuilee.glb")
run(DIST / "glb2tiles.py", src / "Tuilee.glb", "--forcer", "--budget-tri", "700", "--min", "64", "--nopause", "--sans-references")
TILES = json.loads((src / "Tuilee.tiles.json").read_text(encoding="utf-8"))["tiles"]
rapport(len(TILES) >= 4, f"glb2tiles : {len(TILES)} tuiles (au moins 4)", len(TILES))
site = tmp / "site"
site.mkdir()
(site / "Tuilee.zones.json").write_text(json.dumps([{"id": "default", "type": "spawn", "x": 130, "y": 12, "z": -100, "yaw": -math.pi / 2}]), encoding="utf-8")
run(DIST / "glb2html.py", "-o", site / "Tuilee.html", "--shared-shell", "--tiles", src / "Tuilee.tiles.json", "--rotate", "0", "--tile-radius", "100", "--tile-margin", "30",
    "--zones", site / "Tuilee.zones.json", *vend)


def attendu(x, z):
    """tuiles dont la boite (x, z) contient le point, a 0,5 m pres : meme definition que le test, calculee ici sans le code de la page"""
    m = 0.5
    return sorted(t["file"].split("/")[-1] for t in TILES if t["min"][0] - m <= x <= t["max"][0] + m and t["min"][2] - m <= z <= t["max"][2] + m)


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        proc, port = serveur(site)
        errs = []
        try:
            ctx = await br.new_context(locale="fr-FR", viewport={"width": 700, "height": 500})
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{port}/index.html?region=Tuilee#spawn=default&name=Test")
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
            await pg.wait_for_function("window.__viewer.walking", timeout=30000)

            lags = []

            async def lire():
                """(position, state().here, texte de la ligne de la page) : attend au plus 5 s que la ligne rattrape l'etat (la mise a jour des tuiles se fait
                toutes les 250 ms, au rythme des images) et note ce retard ; une ligne qui ne rattrape jamais l'etat est un echec"""
                t0 = time.time()
                await pg.wait_for_timeout(300)
                try:
                    await pg.wait_for_function("""() => { const v = window.__viewer, h = v.tilesState().here, l = document.getElementById('tilesInfo').textContent;
                        return h.length ? l.includes("sous l'avatar : " + h.join(', ')) : !l.includes("sous l'avatar"); }""", timeout=5000)
                except Exception:
                    pass
                lags.append(round((time.time() - t0) * 1000))
                return await pg.evaluate("""() => { const v = window.__viewer; return { pos: v.getWalk().pos, here: v.tilesState().here || [], ligne: document.getElementById('tilesInfo').textContent }; }""")

            def ligne_ok(r):
                noms = ", ".join(r["here"])
                return (("sous l'avatar : " + noms) in r["ligne"]) if r["here"] else ("sous l'avatar" not in r["ligne"])

            r = await lire()
            exp = attendu(r["pos"][0], r["pos"][2])
            rapport(exp and r["here"] == exp and ligne_ok(r), "a l'arrivee : la ligne donne la tuile sous l'avatar", (r, exp))
            vus, ok_all, details = set(), True, []
            for k in range(12):
                await pg.evaluate("""() => { const v = window.__viewer, k = c => window.dispatchEvent(new KeyboardEvent('keydown', { code: c }));
                    k('KeyW'); k('ShiftLeft'); for (let i = 0; i < 25; i++) v.walkTick(0.1);
                    ['KeyW', 'ShiftLeft'].forEach(c => window.dispatchEvent(new KeyboardEvent('keyup', { code: c }))); }""")
                r = await lire()
                exp = attendu(r["pos"][0], r["pos"][2])
                vus.add(tuple(r["here"]))
                if not (r["here"] == sorted(r["here"]) and sorted(r["here"]) == exp and ligne_ok(r)):
                    ok_all = False
                    details.append((k, r["pos"][0], r["here"], exp, r["ligne"][-90:]))
            rapport(ok_all, "marche de 300 m : apres chaque troncon, la ligne = les tuiles dont la boite contient l'avatar", details[:3])
            rapport(len(vus) >= 2, "la marche franchit au moins une frontiere (le nom change)", sorted(vus))
            # teleportation vers une tuile eloignee
            cible = max(TILES, key=lambda t: abs((t["min"][0] + t["max"][0]) / 2 - r["pos"][0]) + abs((t["min"][2] + t["max"][2]) / 2 - r["pos"][2]))
            cx, cz = (cible["min"][0] + cible["max"][0]) / 2, (cible["min"][2] + cible["max"][2]) / 2
            await pg.evaluate("([x, z]) => window.__viewer.teleportTo([x, 40, z], 0)", [cx, cz])
            await pg.wait_for_function("([x]) => Math.abs(window.__viewer.getWalk().pos[0] - x) < 3", arg=[cx], timeout=40000)
            r = await lire()
            exp = attendu(r["pos"][0], r["pos"][2])
            rapport(exp and r["here"] == exp and ligne_ok(r) and cible["file"].split("/")[-1] in r["here"], "apres teleportation : la ligne suit", (r, exp))
            # hors promenade : la mention disparait
            await pg.keyboard.press("KeyF")
            await pg.wait_for_function("!window.__viewer.walking", timeout=15000)
            r = await lire()
            rapport(r["here"] == [] and "sous l'avatar" not in r["ligne"] and "Tuiles : " in r["ligne"], "hors promenade : la mention disparait, le reste de la ligne reste", r)
            rapport(max(lags) < 4000, "la ligne rattrape l'etat (retard max %d ms, mediane %d ms)" % (max(lags), sorted(lags)[len(lags) // 2]), lags)
            rapport(not errs, "aucune erreur JavaScript", errs)
        finally:
            proc.kill()
            await br.close()


asyncio.run(main())
print()
print("RESULTAT : " + ("tout est passe" if not bad else f"ECHEC ({bad})"))
sys.exit(1 if bad else 0)
