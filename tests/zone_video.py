#!/usr/bin/env python3
"""Zone « video » (1.12.7) : un ecran sur un mur dont la texture est un fichier video (mp4, webm), qui joue a portee, sans son.
Verifie : nettoyage JavaScript = Python ; rien n'est telecharge hors de portee ; nom sans extension (medias/ puis .mp4, .webm...) ; lecture muette en boucle a portee,
pause en s'eloignant et en tournant le dos (apres une seconde de grace), reprise au retour ; hauteur d'apres le rapport de la video ; fichier absent ou adresse interdite ;
au plus 8 videos a la fois ; mouvement reduit demande au systeme : premiere image seulement ; aucune erreur JavaScript.
Prerequis : pip install playwright ; ffmpeg ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/zone_video.py
"""
import math, os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, importlib.util, json, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_video_"))
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


def video(path, codec):
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=15", "-t", "4", *codec, str(path)], capture_output=True, text=True)
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
    V = lambda i, x, z, **k: dict({"id": i, "type": "video", "label": "Ecran " + i, "x": x, "y": 16.6, "z": z, "radius": 12, "w": 2.4, "h": 0, "yaw": 0}, **k)
    zs = [V("clip", 0, -20, target="clip"),                      # nom nu : medias/clip.mp4 (absent), puis medias/clip.webm
          V("loin", 40, -20, target="loin.webm"),               # jamais a portee tant qu'on n'y va pas : rien ne doit etre demande
          V("nul", -20, -20, target="inexistant"),               # fichier absent
          V("js", -30, -20, target="javascript:alert(1)"),       # adresse interdite
          V("film", 20, -20, target="film.mp4")]                 # mp4 (H.264) : essai seulement si le navigateur sait le lire
    zs += [V("s1", 80, -20, target="clip.webm", sound=True), V("s2", 86, -20, target="clip.webm", sound=True), V("s3", 83, -20, target="clip.webm")]   # 1.12.9 : deux ecrans a son et un muet
    for k in range(10):                                          # dix ecrans serres : au plus 8 jouent
        zs.append(V("m%d" % k, -50 + k * 0.8, 40, target="clip.webm", radius=60, w=0.6))
    return zs


async def pret(pg):
    await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
    await pg.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
    try:   # question « reflets metalliques » : elle arrive un peu apres le chargement ; on la ferme (elle masquerait le bas de l'ecran)
        await pg.wait_for_function("!!document.getElementById('metalAskNo')", timeout=4000)
        await pg.evaluate("document.getElementById('metalAskNo').click()")
    except Exception:
        pass
    await pg.evaluate("window.__v.walkStart({ pos: [0, 15, 0], yaw: 0 })"); await pg.wait_for_timeout(400)


async def aller(pg, x, z, yaw=0):
    await pg.evaluate(f"window.__v.teleportTo([{x}, 15, {z}], {yaw})"); await pg.wait_for_timeout(300)


DIAG = "() => Object.fromEntries(window.__v.videoDiag().map(d => [d.id, d]))"
ELEM = """(id) => { let r = null; window.__v.scene.traverse(n => { const s = n.userData && n.userData.vid; if (s && n.parent && n.parent.userData.zoneId === id) r = { ready: s.ready, failed: s.failed, vis: n.visible, sy: n.scale.y, sx: n.scale.x,
    v: s.v ? { paused: s.v.paused, muted: s.v.muted, vol: s.v.volume, loop: s.v.loop, t: s.v.currentTime, w: s.v.videoWidth } : null }; }); return r; }"""


async def etat(pg, i):
    return (await pg.evaluate(DIAG)).get(i, {}).get("state")


async def attendre(pg, i, voulu, ms=8000):
    t0 = time.time()
    while time.time() - t0 < ms / 1000:
        if await etat(pg, i) == voulu:
            return True
        await pg.wait_for_timeout(150)
    return False


def page_html(site):
    (site / "z.json").write_text(json.dumps(zones()), encoding="utf-8")
    out = site / "p.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(site / "sol.glb"), "-o", str(out), "--zones", str(site / "z.json"), "--no-sea", *vend], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")


async def main():
    from playwright.async_api import async_playwright
    if not shutil.which("ffmpeg"):
        sys.exit("[ECHEC] ffmpeg absent (necessaire pour fabriquer les videos d'essai)")
    site = tmp / "site"; (site / "medias").mkdir(parents=True)
    sol_glb(site / "sol.glb")
    video(site / "medias" / "clip.webm", ["-c:v", "libvpx", "-b:v", "200k"])
    shutil.copy(site / "medias" / "clip.webm", site / "medias" / "loin.webm")
    video(site / "medias" / "film.mp4", ["-c:v", "libx264", "-pix_fmt", "yuv420p"])
    page_html(site)
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--autoplay-policy=user-gesture-required"], **kw)
            pg = await br.new_page(locale="fr-FR"); errs = []; reqs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("request", lambda r: reqs.append(r.url))
            await pg.add_init_script("window.__plays = []; const p0 = HTMLMediaElement.prototype.play; HTMLMediaElement.prototype.play = function () { window.__plays.push({ muted: this.muted, vol: this.volume }); return p0.apply(this, arguments); };")   # 1.12.13 : etat du son a chaque demarrage
            await pg.goto(f"http://127.0.0.1:{port}/p.html"); await pret(pg)

            # nettoyage : valeurs par defaut et champs ecartes
            zs = {z["id"]: z for z in await pg.evaluate("window.__v.getZones()")}
            z = zs["clip"]
            rapport(z["type"] == "video" and z["radius"] == 12 and z["w"] == 2.4 and z["h"] == 0 and z["mesh"] == "" and "cone" not in z and z["trigger"] == "click" and "link" not in z, "page : zone video conservee (portee, largeur, hauteur 0, ni mesh, ni cone, ni lien)", z)
            spec = importlib.util.spec_from_file_location("g2h", DIST / "glb2html.py"); g2h = importlib.util.module_from_spec(spec); spec.loader.exec_module(g2h)
            test = [{"id": "d", "type": "video", "target": "a"}, {"id": "e", "type": "video", "target": "a", "cone": True, "mesh": "m", "link": "https://x.invalid/", "radius": 500, "w": 99, "h": 99, "trigger": "enter"},
                    {"id": "f", "type": "video", "target": "a", "radius": 0, "w": 0, "h": -2}]
            await pg.evaluate("(l) => window.__v.setZones(l)", test)
            js = await pg.evaluate("window.__v.getZones()")
            py = g2h.clean_zones(test, "private")
            rapport(js == py, "JavaScript (cleanZone) et Python (clean_zones) : meme resultat pour la zone video", (js, py))
            rapport(js[0]["radius"] == 20 and js[1]["radius"] == 200 and js[1]["w"] == 10 and js[1]["h"] == 6 and js[2]["radius"] == 0.5 and js[2]["w"] == 0.1 and js[2]["h"] == 0, "bornes : portee 20 par defaut (0,5 a 200), largeur 0,1 a 10, hauteur 0 a 6", js)
            await pg.evaluate("(l) => window.__v.setZones(l)", zones())
            await pg.wait_for_timeout(300)

            # rien n'est demande hors de portee
            hors = [u for u in reqs if "medias/" in u]
            rapport(not hors, "hors de portee : aucun fichier video demande", hors)
            e0 = await pg.evaluate(ELEM, "clip")
            rapport(await etat(pg, "clip") == "wait" and e0 and e0["v"] is None, "hors de portee : aucun lecteur cree (etat : pas encore charge)", (await pg.evaluate(DIAG), e0))

            # a portee : nom nu -> medias/clip.mp4 absent, puis medias/clip.webm ; joue muet en boucle
            await aller(pg, 0, -14, 0)
            ok = await attendre(pg, "clip", "play")
            d = (await pg.evaluate(DIAG)).get("clip", {})
            rapport(ok and d.get("loaded") == "medias/clip.webm", "a portee : le nom nu cherche clip.mp4 puis trouve medias/clip.webm, la video joue", d)
            await pg.wait_for_timeout(600)
            e1 = await pg.evaluate(ELEM, "clip"); await pg.wait_for_timeout(800); e2 = await pg.evaluate(ELEM, "clip")
            rapport(e1 and e1["v"] and e1["v"]["muted"] and e1["v"]["loop"] and not e1["v"]["paused"] and e2["v"]["t"] != e1["v"]["t"], "lecture muette, en boucle, le temps avance", (e1, e2))
            rapport(abs(e2["sy"] - 2.4 * 180 / 320) < 0.01 and e2["v"]["w"] == 320, "hauteur d'apres le rapport de la video (h = 0)", e2)
            rapport(not any("loin" in u for u in reqs), "l'ecran lointain n'a toujours rien demande", [u for u in reqs if "loin" in u])

            # la video est bien dessinee a l'ecran : des couleurs variees au centre (la mire d'essai), pas le sombre d'attente
            try:
                from PIL import Image
                import io
                im = Image.open(io.BytesIO(await pg.screenshot())).convert("RGB"); W, H = im.size
                zone = im.crop((W // 2 - 60, H // 2 - 30, W // 2 + 60, H // 2 + 30))
                cols = {(r // 32, g // 32, b // 32) for r, g, b in zone.getdata()}
                rapport(len(cols) >= 5, "la video est dessinee a l'ecran (couleurs variees au centre)", len(cols))
            except ImportError:
                print("[--]    Pillow absent : controle des pixels ignore")

            # tourner le dos : pause apres une seconde de grace ; revenir face a l'ecran : reprise
            await aller(pg, 0, -14, 3.14159)
            await pg.wait_for_timeout(500)
            encore = await etat(pg, "clip")
            ok2 = await attendre(pg, "clip", "pause", 4000)
            rapport(encore == "play" and ok2, "dos tourne : encore en lecture pendant la grace, puis en pause", (encore, ok2))
            await aller(pg, 0, -14, 0)
            rapport(await attendre(pg, "clip", "play", 4000), "face a l'ecran de nouveau : la lecture reprend")

            # clic sur l'ecran (1.12.10) : pause, puis lecture ; sortir de la portee annule la pause
            vs = pg.viewport_size; cx, cy = vs["width"] // 2, vs["height"] // 2
            await pg.mouse.move(cx, cy); await pg.wait_for_timeout(300)
            tip = await pg.evaluate("(() => { const e = document.getElementById('zoneTip'); return e && !e.hidden ? e.textContent : ''; })()")
            rapport("pause" in tip.lower() or "lecture" in tip.lower(), "infobulle au survol : clic = pause / lecture", tip)
            await pg.mouse.click(cx, cy); await pg.wait_for_timeout(400)
            ev = (await pg.evaluate(ELEM, "clip"))["v"]
            rapport(ev["paused"] and await etat(pg, "clip") == "user", "clic sur l'ecran : la video s'arrete (etat : arretee par un clic)", (ev, await etat(pg, "clip")))
            await pg.wait_for_timeout(1500)
            rapport(await etat(pg, "clip") == "user", "arretee par clic : elle ne repart pas toute seule (a portee, en vue)")
            await pg.mouse.click(cx, cy); await pg.wait_for_timeout(500)
            rapport(await attendre(pg, "clip", "play", 3000), "deuxieme clic : la lecture reprend")
            await pg.mouse.click(cx, cy); await pg.wait_for_timeout(300)
            await aller(pg, 0, 30, 0); await pg.wait_for_timeout(400); await aller(pg, 0, -14, 0)
            rapport(await attendre(pg, "clip", "play", 4000), "arretee par clic, puis sortie de portee et retour : elle rejoue")
            await aller(pg, 40, -14, 0); await pg.wait_for_timeout(300)
            await aller(pg, 0, -14, 0)
            await pg.mouse.click(cx, cy); await pg.wait_for_timeout(300); await pg.mouse.click(cx, cy); await pg.wait_for_timeout(300)

            # vue libre : la camera reste devant l'ecran, c'est le visiteur qui s'eloigne -> pause ; il revient -> reprise
            await pg.evaluate("window.__v.setView('free')"); await pg.wait_for_timeout(300)
            c0 = (await pg.evaluate("window.__v.getWalk()"))["cam"]
            await aller(pg, 0, 30, 0)
            c1 = (await pg.evaluate("window.__v.getWalk()"))["cam"]
            rapport(max(abs(c0[i] - c1[i]) for i in range(3)) < 0.01, "vue libre : la camera n'a pas suivi le visiteur", (c0, c1))
            rapport(await attendre(pg, "clip", "pause", 4000), "vue libre, visiteur loin, camera pres de l'ecran : pause", await pg.evaluate(DIAG))
            await aller(pg, 0, -14, 0)
            rapport(await attendre(pg, "clip", "play", 4000), "vue libre, visiteur revenu a portee : lecture")
            await pg.evaluate("window.__v.setView('fps')"); await pg.wait_for_timeout(300)

            # s'eloigner : pause ; l'ecran lointain, une fois a portee, se charge
            await aller(pg, 0, 30, 0)
            rapport(await attendre(pg, "clip", "pause", 4000), "hors de portee : pause (la video reste chargee)")
            await aller(pg, 40, -14, 0)
            rapport(await attendre(pg, "loin", "play"), "l'ecran lointain se charge et joue seulement quand on s'en approche", await pg.evaluate(DIAG))

            # son (1.12.9) : muet par defaut ; seul l'ecran a son le plus proche parle, au volume (1 - distance / portee) x niveau de la page ; le navigateur peut refuser le son sans geste
            await pg.mouse.click(10, 10); await pg.evaluate("window.__v.videoSound = () => 0.8; window.__plays = []")   # geste de l'utilisateur, niveau 0,8, puis on approche des trois ecrans
            await aller(pg, 82, -14, 0)
            for i in ("s1", "s2", "s3"):
                await attendre(pg, i, "play")
            pl = await pg.evaluate("window.__plays")
            rapport(len(pl) == 3 and sum(1 for x in pl if not x["muted"]) == 1 and all(0 < x["vol"] <= 1 for x in pl if not x["muted"]), "le son est regle avant le demarrage : seul l'ecran a son le plus proche demarre non muet, pas de demarrage muet suivi d'un rattrapage", pl)
            await pg.evaluate("window.__v.videoSound = () => 0"); await pg.wait_for_timeout(500)
            m = [(await pg.evaluate(ELEM, i))["v"] for i in ("s1", "s2", "s3")]
            rapport(all(x["muted"] for x in m) and all(not x["paused"] for x in m), "niveau 0 : les trois ecrans jouent, muets", m)
            await pg.mouse.click(10, 10)   # geste de l'utilisateur (la politique du navigateur l'exige pour le son)
            await pg.evaluate("window.__v.videoSound = () => 0.8"); await pg.wait_for_timeout(700)
            e = [(await pg.evaluate(ELEM, i))["v"] for i in ("s1", "s2", "s3")]
            att = (1 - math.hypot(2, 6.1) / 12) * 0.8
            rapport(not e[0]["muted"] and e[1]["muted"] and e[2]["muted"], "deux ecrans a son a portee : seul le plus proche (s1) parle ; s2 (a son, plus loin) et s3 (sans son) restent muets", e)
            rapport(abs(e[0]["vol"] - att) < 0.06, "volume = (1 - distance / portee) x niveau", (e[0]["vol"], att))
            rapport(all(not x["paused"] for x in e), "les trois ecrans continuent de jouer", e)
            await aller(pg, 85, -14, 0); await pg.wait_for_timeout(700)
            e = [(await pg.evaluate(ELEM, i))["v"] for i in ("s1", "s2", "s3")]
            rapport(e[0]["muted"] and not e[1]["muted"] and e[2]["muted"], "on se rapproche de s2 : c'est lui qui parle, s1 se tait", e)
            await aller(pg, 85, -3, 0)
            for i in ("s1", "s2", "s3"):
                await attendre(pg, i, "pause", 4000)   # une seconde de grace avant la pause
            e = [(await pg.evaluate(ELEM, i))["v"] for i in ("s1", "s2", "s3")]
            rapport(all(x["muted"] for x in e) and all(x["paused"] for x in e), "hors de portee : tous en pause et muets", e)
            dg = await pg.evaluate(DIAG)
            rapport(dg["s2"]["sound"] is True and dg["s3"]["sound"] is False, "diagnostic : cle sound lue par ecran", dg["s2"])

            # le navigateur refuse le son sans geste (NotAllowedError, simule) : l'ecran joue quand meme, muet ; le son est retente 5 s plus tard (1.12.14)
            pg2 = await br.new_page()
            await pg2.add_init_script("window.__refuse = true; const p1 = HTMLMediaElement.prototype.play; HTMLMediaElement.prototype.play = function () { if (window.__refuse && !this.muted) return Promise.reject(new DOMException('refus', 'NotAllowedError')); return p1.apply(this, arguments); };")
            await pg2.goto(f"http://127.0.0.1:{port}/p.html"); await pret(pg2)
            await pg2.evaluate("window.__v.videoSound = () => 0.8")
            await aller(pg2, 82, -14, 0)
            ok = await attendre(pg2, "s1", "play"); await pg2.wait_for_timeout(500)
            e = (await pg2.evaluate(ELEM, "s1"))["v"]
            rapport(ok and e["muted"] and not e["paused"], "navigateur qui refuse le son : l'ecran joue quand meme, muet", e)
            await pg2.evaluate("window.__refuse = false"); await pg2.wait_for_timeout(6000)
            e = (await pg2.evaluate(ELEM, "s1"))["v"]
            rapport(not e["muted"] and not e["paused"], "refus leve : le son est retente et passe (5 s plus tard)", e)
            await pg2.close()

            # fichier absent, adresse interdite
            await aller(pg, -20, -14, 0)
            rapport(await attendre(pg, "nul", "fail"), "fichier absent : echec, l'ecran disparait", await pg.evaluate(DIAG))
            en = await pg.evaluate(ELEM, "nul"); ej = await pg.evaluate(ELEM, "js")
            rapport(en and en["failed"] and not en["vis"], "fichier absent : ecran masque", en)
            rapport(ej and ej["failed"] and not ej["vis"] and not any("alert" in u for u in reqs), "javascript: : refuse, rien demande, ecran masque", (ej, [u for u in reqs if "alert" in u]))

            # mp4 (H.264) : seulement si le navigateur sait le lire
            h264 = await pg.evaluate("document.createElement('video').canPlayType('video/mp4; codecs=\"avc1.42E01E\"') !== ''")
            if h264:
                await aller(pg, 20, -14, 0)
                rapport(await attendre(pg, "film", "play"), "mp4 (H.264) : joue", await pg.evaluate(DIAG))
            else:
                print("[--]    mp4 (H.264) : non lisible par ce navigateur, essai ignore")

            # dix ecrans serres : au plus 8 jouent
            await aller(pg, -46, 52, 0)
            t0 = time.time(); n = 0
            while time.time() - t0 < 8:
                d = await pg.evaluate(DIAG); n = sum(1 for k, v in d.items() if k.startswith("m") and v["state"] == "play")
                if n >= 8:
                    break
                await pg.wait_for_timeout(200)
            await pg.wait_for_timeout(1200)
            d = await pg.evaluate(DIAG); n2 = sum(1 for k, v in d.items() if k.startswith("m") and v["state"] == "play")
            rapport(n >= 8 and n2 == 8, "dix ecrans a portee : exactement 8 jouent (les plus proches)", (n, n2, {k: v["state"] for k, v in d.items() if k.startswith("m")}))

            # reconstruction des zones : les lecteurs sont arretes
            await pg.evaluate("(l) => window.__v.setZones(l)", [])
            await pg.wait_for_timeout(300)
            rapport(not await pg.evaluate(DIAG), "zones retirees : plus aucun ecran video", await pg.evaluate(DIAG))
            rapport(not errs, "aucune erreur JavaScript", errs)

            # mouvement reduit demande au systeme : la premiere image seulement
            ctx = await br.new_context(locale="fr-FR", reduced_motion="reduce")
            pr = await ctx.new_page(); errs3 = []
            pr.on("pageerror", lambda e: errs3.append(str(e)))
            await pr.goto(f"http://127.0.0.1:{port}/p.html"); await pret(pr)
            await aller(pr, 0, -14, 0)
            ok3 = await attendre(pr, "clip", "pause")
            await pr.wait_for_timeout(800)
            e = await pr.evaluate(ELEM, "clip")
            rapport(ok3 and e and e["ready"] and e["v"]["paused"] and e["v"]["t"] == 0, "mouvement reduit : la premiere image s'affiche, la video ne joue pas", e)
            rapport(not errs3, "aucune erreur JavaScript (mouvement reduit)", errs3)
            await br.close()
    finally:
        proc.terminate()
    print("\nRESULTAT : " + ("tout est passe" if not echecs else f"ECHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
