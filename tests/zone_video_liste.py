#!/usr/bin/env python3
"""Ecrans video, listes de lecture (1.12.12) : folder / tracks / <dossier>/playlist.json comme une zone audio. Verifie : nettoyage JavaScript = Python (folder, tracks) ;
glb2html.py --video-list (ordre naturel, seulement les extensions video, --dry-run n'ecrit rien) ; lecture de la premiere piste, enchainement a la fin d'une piste, retour a la
premiere apres la derniere, piste illisible sautee, rapport largeur / hauteur propre a chaque piste ; clic sur le bord droit = suivante, bord gauche = precedente, ailleurs = pause ;
une seule piste : boucle ; liste vide ou toutes pistes illisibles : l'ecran disparait ; infobulle ; un ecran a fichier unique garde pause / lecture sur ses bords ; aucune erreur JavaScript.
Prerequis : pip install playwright ; ffmpeg ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/zone_video_liste.py
"""
import math, os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, importlib.util, json, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_vliste_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def sol_glb(path):
    pos = struct.pack("<12f", -60, 0, -60, 60, 0, -60, 60, 0, 60, -60, 0, 60)
    blob = pos + struct.pack("<6H", 0, 2, 1, 0, 3, 2) + b"\0\0"
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-60, 0, -60], "max": [60, 0, 60]},
                       {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * ((4 - len(js) % 4) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob))
                     + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def clip(path, size, secondes=2):
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"testsrc=size={size}:rate=15", "-t", str(secondes), "-c:v", "libvpx", "-b:v", "200k", str(path)], capture_output=True, text=True)
    if r.returncode:
        sys.exit("[ECHEC] ffmpeg : " + r.stderr[-300:])


def serveur(dossier):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=dossier, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close(); return proc, port
        except OSError:
            time.sleep(0.1)
    sys.exit("[ECHEC] serveur http")


def zones():
    V = lambda i, x, **k: dict({"id": i, "type": "video", "label": "Ecran " + i, "x": x, "y": 16.6, "z": -20, "radius": 12, "w": 2.4, "h": 0, "yaw": 0}, **k)
    return [V("liste", 0, folder="clips"),                                                    # liste lue dans clips/playlist.json
            V("ins", 30, folder="clips", tracks=["1-a.webm", "absent-zzz.webm", "10-c.webm"]),   # liste ecrite dans la zone, une piste absente
            V("vide", -30, folder="vide"),                                                    # liste vide
            V("mauvais", -60, folder="clips", tracks=["x1.webm", "x2.webm"]),                 # aucune piste lisible
            V("seul", 60, folder="seul"),                                                     # une seule piste : boucle
            V("fich", 90, target="clips/1-a.webm")]                                           # fichier unique : les bords restent pause / lecture


DIAG = "() => Object.fromEntries(window.__v.videoDiag().map(d => [d.id, d]))"
ELEM = """(id) => { let r = null; window.__v.scene.traverse(n => { const s = n.userData && n.userData.vid; if (s && n.parent && n.parent.userData.zoneId === id) r = { ready: s.ready, failed: s.failed, vis: n.visible, sy: n.scale.y,
    v: s.v ? { paused: s.v.paused, loop: s.v.loop, t: s.v.currentTime, w: s.v.videoWidth } : null }; }); return r; }"""
# point de l'ecran a l'abscisse u (0 a 1) en pixels, pour cliquer sur un bord
PIX = """([id, u]) => { let pl = null; window.__v.scene.traverse(n => { const s = n.userData && n.userData.vid; if (s && n.parent && n.parent.userData.zoneId === id) pl = n; });
    const v = new window.__v.camera.position.constructor(u - 0.5, 0, 0).applyMatrix4(pl.matrixWorld).project(window.__v.camera), r = window.__v.renderer.domElement.getBoundingClientRect();
    return [r.left + (v.x + 1) / 2 * r.width, r.top + (1 - v.y) / 2 * r.height]; }"""


async def pret(pg):
    await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
    await pg.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
    try:
        await pg.wait_for_function("!!document.getElementById('metalAskNo')", timeout=4000)
        await pg.evaluate("document.getElementById('metalAskNo').click()")
    except Exception:
        pass
    await pg.evaluate("window.__v.walkStart({ pos: [0, 15, 0], yaw: 0 })"); await pg.wait_for_timeout(400)


async def aller(pg, x, z, yaw=0):
    await pg.evaluate(f"window.__v.teleportTo([{x}, 15, {z}], {yaw})"); await pg.wait_for_timeout(300)


async def diag(pg, i):
    return (await pg.evaluate(DIAG)).get(i, {})


async def attendre(pg, i, cond, ms=9000):
    t0 = time.time()
    while time.time() - t0 < ms / 1000:
        if cond(await diag(pg, i)):
            return True
        await pg.wait_for_timeout(120)
    return False


def outil(*args):
    return subprocess.run([sys.executable, str(DIST / "glb2html.py"), *map(str, args)], capture_output=True, text=True)


async def main():
    from playwright.async_api import async_playwright
    if not shutil.which("ffmpeg"):
        sys.exit("[ECHEC] ffmpeg absent (necessaire pour fabriquer les videos d'essai)")
    site = tmp / "site"; cl = site / "medias" / "clips"; cl.mkdir(parents=True); (site / "medias" / "vide").mkdir(); (site / "medias" / "seul").mkdir()
    sol_glb(site / "sol.glb")
    clip(cl / "1-a.webm", "320x180"); clip(cl / "2-b.webm", "320x240"); clip(cl / "10-c.webm", "160x90")
    (cl / "3-bad.webm").write_bytes(b"ceci n'est pas une video" * 50); (cl / "notes.txt").write_text("x", encoding="utf-8"); (cl / ".cache.webm").write_bytes(b"x")
    shutil.copy(cl / "1-a.webm", site / "medias" / "seul" / "unique.webm")
    # outil : --video-list
    r = outil("--video-list", cl, "--dry-run")
    rapport(r.returncode == 0 and not (cl / "playlist.json").exists(), "--video-list --dry-run : n'ecrit rien", r.stdout + r.stderr)
    r = outil("--video-list", cl)
    pl = json.loads((cl / "playlist.json").read_text(encoding="utf-8")) if (cl / "playlist.json").exists() else {}
    rapport(r.returncode == 0 and pl.get("tracks") == ["1-a.webm", "2-b.webm", "3-bad.webm", "10-c.webm"], "--video-list : videos seules, ordre naturel (2 avant 10), ni notes.txt ni fichier cache", pl)
    r = outil("--video-list", site / "medias" / "vide")
    rapport(r.returncode == 0 and json.loads((site / "medias" / "vide" / "playlist.json").read_text(encoding="utf-8")) == {"tracks": []}, "--video-list : dossier sans video = liste vide", r.stdout + r.stderr)
    r = outil("--video-list", site / "medias" / "seul")
    (site / "z.json").write_text(json.dumps(zones()), encoding="utf-8")
    out = site / "p.html"
    r = outil(site / "sol.glb", "-o", out, "--zones", site / "z.json", "--no-sea", *vend)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--autoplay-policy=user-gesture-required"], **kw)
            pg = await br.new_page(locale="fr-FR"); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{port}/p.html"); await pret(pg)
            # nettoyage JS = Python
            spec = importlib.util.spec_from_file_location("g2h", DIST / "glb2html.py"); g2h = importlib.util.module_from_spec(spec); spec.loader.exec_module(g2h)
            test = [{"id": "a", "type": "video", "folder": "\\clips\\x/", "tracks": ["1-a.webm", "../evil.webm", "sub/2.webm", "http://h.invalid/c.webm", "javascript:alert(1)", 5, ""]},
                    {"id": "b", "type": "video", "folder": "../hors", "tracks": []}, {"id": "c", "type": "video", "target": "x.webm"}, {"id": "d", "type": "image", "target": "i.png", "folder": "nope", "tracks": ["a"]}]
            await pg.evaluate("(l) => window.__v.setZones(l)", test)
            js = await pg.evaluate("window.__v.getZones()"); py = g2h.clean_zones(test, "private")
            rapport(js == py, "JavaScript (cleanZone) et Python (clean_zones) : meme resultat pour folder et tracks d'un ecran", (js, py))
            rapport(js[0].get("folder") == "clips/x" and js[0].get("tracks") == ["1-a.webm", "sub/2.webm", "http://h.invalid/c.webm"] and "folder" not in js[1] and "tracks" not in js[1] and "folder" not in js[3], "folder nettoye, tracks filtrees (pas de .., pas de javascript:), rien de tout cela sur une image", js)
            await pg.evaluate("(l) => window.__v.setZones(l)", zones()); await pg.wait_for_timeout(300)

            # liste lue dans playlist.json : piste 1, puis enchainement
            await aller(pg, 0, -14, 0)
            ok = await attendre(pg, "liste", lambda d: d.get("state") == "play" and d.get("n") == 4)
            d = await diag(pg, "liste")
            rapport(ok and d["ti"] == 0 and d["name"] == "1-a.webm", "liste : 4 pistes lues dans playlist.json, la premiere joue", d)
            e = await pg.evaluate(ELEM, "liste")
            rapport(e["v"] and not e["v"]["loop"] and abs(e["sy"] - 2.4 * 180 / 320) < 0.01, "liste de plusieurs pistes : pas de boucle sur une piste ; hauteur d'apres la piste 1", e)
            ok = await attendre(pg, "liste", lambda d: d.get("ti") == 1 and d.get("state") == "play")
            e = await pg.evaluate(ELEM, "liste")
            rapport(ok and abs(e["sy"] - 2.4 * 240 / 320) < 0.01, "fin de la piste 1 : la piste 2 s'enchaine, avec son propre rapport largeur / hauteur", (await diag(pg, "liste"), e))
            ok = await attendre(pg, "liste", lambda d: d.get("ti") == 3 and d.get("state") == "play")
            e = await pg.evaluate(ELEM, "liste")
            rapport(ok and abs(e["sy"] - 2.4 * 90 / 160) < 0.01, "la piste 3 est illisible : sautee, la piste 4 joue", (await diag(pg, "liste"), e))
            ok = await attendre(pg, "liste", lambda d: d.get("ti") == 0 and d.get("state") == "play")
            rapport(ok, "apres la derniere piste : retour a la premiere (la piste illisible reste sautee)", await diag(pg, "liste"))

            # clics sur les bords : suivante / precedente ; au milieu : pause
            tip = await pg.evaluate("(() => { const e = document.getElementById('zoneTip'); return e && !e.hidden ? e.textContent : ''; })()")
            x, y = await pg.evaluate(PIX, ["liste", 0.5]); await pg.mouse.move(x, y); await pg.wait_for_timeout(300)
            tip = await pg.evaluate("(() => { const e = document.getElementById('zoneTip'); return e && !e.hidden ? e.textContent : ''; })()")
            rapport("bord" in tip, "infobulle d'une liste : explique les bords", tip)
            await pg.mouse.click(*await pg.evaluate(PIX, ["liste", 0.93])); await pg.wait_for_timeout(500)
            d = await diag(pg, "liste")
            rapport(d["ti"] == 1 and d["state"] in ("play", "wait"), "clic sur le bord droit : piste suivante", d)
            await pg.mouse.click(*await pg.evaluate(PIX, ["liste", 0.07])); await pg.wait_for_timeout(500)
            d = await diag(pg, "liste")
            rapport(d["ti"] == 0, "clic sur le bord gauche : piste precedente", d)
            await pg.mouse.click(*await pg.evaluate(PIX, ["liste", 0.07])); await pg.wait_for_timeout(500)
            d = await diag(pg, "liste")
            rapport(d["ti"] == 3, "precedente depuis la premiere : la derniere lisible (la piste illisible est sautee)", d)
            await pg.mouse.click(*await pg.evaluate(PIX, ["liste", 0.5])); await pg.wait_for_timeout(400)
            d = await diag(pg, "liste")
            rapport(d["state"] == "user", "clic au milieu : pause", d)
            await pg.mouse.click(*await pg.evaluate(PIX, ["liste", 0.93])); await pg.wait_for_timeout(600)
            d = await diag(pg, "liste")
            rapport(d["ti"] == 0 and await attendre(pg, "liste", lambda q: q.get("state") == "play", 4000), "en pause, clic sur le bord : la piste change et la lecture reprend", d)

            # liste ecrite dans la zone, avec une piste absente
            await aller(pg, 30, -14, 0)
            ok = await attendre(pg, "ins", lambda d: d.get("state") == "play" and d.get("n") == 3)
            d = await diag(pg, "ins")
            rapport(ok and d["name"] == "1-a.webm", "tracks ecrites dans la zone : lues sans playlist.json", d)
            ok = await attendre(pg, "ins", lambda d: d.get("ti") == 2 and d.get("state") == "play")
            rapport(ok, "piste absente au milieu : sautee, la derniere joue", await diag(pg, "ins"))

            # liste vide, aucune piste lisible, une seule piste
            await aller(pg, -30, -14, 0)
            ok = await attendre(pg, "vide", lambda d: d.get("state") == "fail")
            e = await pg.evaluate(ELEM, "vide")
            rapport(ok and e and e["failed"] and not e["vis"], "liste vide : l'ecran disparait", (await diag(pg, "vide"), e))
            await aller(pg, -60, -14, 0)
            ok = await attendre(pg, "mauvais", lambda d: d.get("state") == "fail")
            rapport(ok, "aucune piste lisible : l'ecran disparait", await diag(pg, "mauvais"))
            await aller(pg, 60, -14, 0)
            ok = await attendre(pg, "seul", lambda d: d.get("state") == "play")
            e = await pg.evaluate(ELEM, "seul")
            rapport(ok and e["v"] and e["v"]["loop"], "liste d'une seule piste : elle joue en boucle", (await diag(pg, "seul"), e))
            await pg.mouse.click(*await pg.evaluate(PIX, ["seul", 0.93])); await pg.wait_for_timeout(400)
            d = await diag(pg, "seul")
            rapport(d["state"] == "user" and d["ti"] == 0, "une seule piste : le bord ne change rien d'autre qu'une pause / lecture", d)

            # fichier unique : les bords restent pause / lecture
            await aller(pg, 90, -14, 0)
            ok = await attendre(pg, "fich", lambda d: d.get("state") == "play")
            await pg.mouse.click(*await pg.evaluate(PIX, ["fich", 0.93])); await pg.wait_for_timeout(400)
            d = await diag(pg, "fich")
            rapport(ok and d["state"] == "user" and d["n"] == 1, "fichier unique : un clic sur le bord = pause (pas de piste suivante)", d)
            rapport(not errs, "aucune erreur JavaScript", errs)
            await br.close()
    finally:
        proc.terminate()
    print("\nRESULTAT : " + ("tout est passe" if not echecs else f"ECHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
