#!/usr/bin/env python3
"""Test des zones url en fenetre flottante (1.12.3, cle frame) : le lien s'affiche dans un cadre de la page au lieu d'un nouvel onglet.

Verifie l'adresse donnee au cadre (le bac a sable n'atteint ni YouTube ni les autres sites : l'affichage reel est a essayer chez Klaatou) :
 - lien YouTube (watch, t=, youtu.be, shorts) -> lecteur youtube-nocookie.com/embed/ID, autoplay au clic ou a E, pas en marchant dedans ;
 - autre adresse https, et http depuis une page qui n'est pas en https -> cadre ; hop:// -> comme avant ; zone sans frame -> comme avant ;
 - page en https : http (contenu mixte) et meme origine -> pas de cadre (nouvel onglet) ;
 - en marchant dedans : rien n'est charge avant le clic sur le bouton ; une seule fenetre a la fois ; deplacement ; croix ;
 - la cle frame n'est gardee que vraie et seulement pour une zone url, en Python (clean_zones) et en JavaScript (cleanZone, setZones).

Prerequis : pip install playwright && playwright install chromium ; python build.py avant.
Variable facultative : THREE_DIR (paquet npm three, hors ligne), CHROMIUM.
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, importlib.util, json, mimetypes, os, pathlib, struct, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_frame_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0
HOP = "hop://exemple.invalid:9000/Atoll/128/128/25"
YTL = "https://www.youtube.com/watch?v=Qp7TR1RAjXc&list=RDQp7TR1RAjXc"   # lien d'un mix : video dans sa liste
YT = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42"


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def sol_glb(path):
    pos = struct.pack("<12f", -20, 0, -20, 20, 0, -20, 20, 0, 20, -20, 0, 20)
    blob = pos + struct.pack("<6H", 0, 2, 1, 0, 3, 2) + b"\0\0"
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-20, 0, -20], "max": [20, 0, 20]},
                       {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * ((4 - len(js) % 4) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob))
                     + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def zones():
    Z = lambda i, t, x, z, **k: dict({"id": i, "type": t, "label": "Zone " + i, "x": x, "y": 15, "z": z, "radius": 2}, **k)
    return [Z("yt", "url", -15, -15, target=YT, trigger="click", frame=True),
            Z("yt2", "url", -15, 15, target="https://youtu.be/dQw4w9WgXcQ", trigger="click", frame=True),
            Z("gen", "url", -5, -15, target="https://exemple.invalid/page", trigger="click", frame=True),
            Z("htp", "url", 5, -15, target="http://exemple.invalid/x", trigger="click", frame=True),
            Z("hop", "url", 15, -15, target=HOP, trigger="click", frame=True),
            Z("plain", "url", -15, 0, target="https://exemple.invalid/p", trigger="click"),
            Z("ent", "url", 0, 10, target="https://exemple.invalid/e", trigger="enter", frame=True),
            Z("same", "url", 15, 0, target="https://web3d.test/autre", trigger="click", frame=True),
            Z("port", "portal", 10, 10, target="", trigger="click", frame=True),
            Z("txt", "url", 5, 5, target="https://exemple.invalid/t", trigger="click", frame="oui"),
            Z("pl1", "url", -5, 15, target=YTL, trigger="click", frame=True),
            Z("pl2", "url", 5, 15, target="https://www.youtube.com/playlist?list=PLabcdefghijkl", trigger="click", frame=True),
            Z("pl3", "url", -8, 5, target="https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=x%3Cb", trigger="click", frame=True),
            Z("pl4", "url", -10, -8, target="https://www.youtube.com/playlist?list=a", trigger="click", frame=True)]


def page():
    (tmp / "z.json").write_text(json.dumps(zones()), encoding="utf-8")
    out = tmp / "p.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--zones", str(tmp / "z.json"), "--no-sea", *vend],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    return out


async def pret(pg):
    await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
    await pg.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
    await pg.evaluate("(window.open = (...a) => { (window.__op = window.__op || []).push(a); return null; }, 0)")
    await pg.evaluate("window.__v.walkStart({ pos: [0, 15, 30], yaw: 0 })"); await pg.wait_for_timeout(400)


async def aller(pg, x, z):
    await pg.evaluate(f"window.__v.teleportTo([{x}, 15, {z}], 0)"); await pg.wait_for_timeout(500)


async def etat(pg):
    return await pg.evaluate("""(() => { const w = document.getElementById('frameWin'); if (!w) return null;
        const f = w.querySelector('iframe'); return { n: document.querySelectorAll('#frameWin').length, src: f ? f.getAttribute('src') : null,
        title: w.querySelector('.fwTitle').textContent, sandbox: f ? f.getAttribute('sandbox') : null, load: !!w.querySelector('.fwLoad'),
        loadTxt: w.querySelector('.fwLoad') ? w.querySelector('.fwLoad').textContent : '' }; })()""")


async def ouvrir_e(pg, x, z):
    await pg.evaluate("window.__op = []; (document.getElementById('frameWin') || {remove(){}}).remove()")
    await aller(pg, x, z + 2)
    await pg.keyboard.press("KeyE"); await pg.wait_for_timeout(300)
    return await etat(pg), json.loads(await pg.evaluate("JSON.stringify(window.__op)"))


async def main():
    from playwright.async_api import async_playwright
    sol_glb(tmp / "sol.glb")
    out = page()
    async with async_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
        br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
        pg = await br.new_page(locale="fr-FR"); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(out.as_uri()); await pret(pg)

        zs = {z["id"]: z for z in await pg.evaluate("window.__v.getZones()")}
        rapport(all(zs[k].get("frame") is True for k in ("yt", "yt2", "gen", "htp", "hop", "ent", "same")), "page : frame conserve sur les zones url", {k: v.get("frame") for k, v in zs.items()})
        rapport("frame" not in zs["plain"] and "frame" not in zs["port"] and "frame" not in zs["txt"],
                "page : pas de frame sur une zone sans frame, un portail, ni une valeur autre que vrai", {k: zs[k].get("frame") for k in ("plain", "port", "txt")})

        e, op = await ouvrir_e(pg, -15, -15)
        rapport(bool(e and e["src"] and e["src"].startswith("https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?") and "autoplay=1" in e["src"] and "start=42" in e["src"]),
                "YouTube watch?v=...&t=42 avec E : lecteur youtube-nocookie, autoplay, depart a 42 s", e)
        rapport(e and not op and e["title"] == "Zone yt" and "allow-scripts" in (e["sandbox"] or "") and e["n"] == 1, "fenetre : titre de la zone, sandbox, aucun nouvel onglet", (e, op))
        # position d'ouverture (1.12.6) : a gauche, centree en hauteur ; le symetrique du lecteur par rapport a la ligne mediane (fantome d'Edge sans acceleration materielle) tombe dans la fenetre
        g = await pg.evaluate("(() => { const w = document.getElementById('frameWin').getBoundingClientRect(), f = document.querySelector('#frameWin iframe').getBoundingClientRect(); return { H: innerHeight, wt: w.top, wb: w.bottom, wl: w.left, ft: f.top, fb: f.bottom }; })()")
        rapport(abs(g["wl"] - 16) < 2 and g["H"] - g["fb"] >= g["wt"] - 1 and g["H"] - g["ft"] <= g["wb"] + 1,
                "ouverture : a gauche, centree en hauteur (le symetrique du lecteur tombe dans la fenetre)", g)
        r0 = await pg.evaluate("(() => { const r = document.querySelector('#frameWin .fwHead').getBoundingClientRect(); return [r.x + 40, r.y + 10]; })()")
        await pg.mouse.move(r0[0], r0[1]); await pg.mouse.down(); await pg.mouse.move(r0[0] + 150, r0[1] - 100, steps=4); await pg.mouse.up()
        r1 = await pg.evaluate("(() => { const r = document.querySelector('#frameWin').getBoundingClientRect(); return [r.x, r.y]; })()")
        r2 = await pg.evaluate("(() => { const r = document.querySelector('#frameWin .fwHead').getBoundingClientRect(); return [r.x + 40, r.y + 10]; })()")
        rapport(abs(r2[0] - (r0[0] + 150)) < 3 and abs(r2[1] - (r0[1] - 100)) < 3, "fenetre : se deplace en glissant l'en-tete", (r0, r1, r2))
        # une seule fenetre, remplacee par celle d'une autre zone ; la meme zone ne la rouvre pas
        await aller(pg, -5, -13); await pg.keyboard.press("KeyE"); await pg.wait_for_timeout(300)
        e = await etat(pg)
        rapport(e and e["n"] == 1 and e["title"] == "Zone gen" and e["src"] == "https://exemple.invalid/page", "autre zone https : une seule fenetre, adresse telle quelle", e)
        await pg.keyboard.press("KeyE"); await pg.wait_for_timeout(200)
        rapport((await etat(pg))["n"] == 1, "E de nouveau sur la meme zone : toujours une seule fenetre")
        # croix
        await pg.evaluate("document.querySelectorAll('#frameWin .fwHead button')[1].click()"); await pg.wait_for_timeout(100)
        rapport(await etat(pg) is None, "croix : la fenetre se ferme")
        # bouton nouvel onglet
        await pg.keyboard.press("KeyE"); await pg.wait_for_timeout(200)
        await pg.evaluate("window.__op = []; document.querySelectorAll('#frameWin .fwHead button')[0].click()")
        op = json.loads(await pg.evaluate("JSON.stringify(window.__op)"))
        rapport(len(op) == 1 and op[0][0] == "https://exemple.invalid/page" and op[0][1] == "_blank", "bouton ↗ : ouvre l'adresse d'origine dans un nouvel onglet", op)
        rapport(await etat(pg) is None, "bouton ↗ : la mini fenetre se ferme aussi (1.12.6)")

        e, op = await ouvrir_e(pg, -15, 15)
        rapport(e and e["src"].startswith("https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?") and "start" not in e["src"], "youtu.be/ID : lecteur youtube-nocookie", e)
        e, op = await ouvrir_e(pg, -5, 15)
        rapport(bool(e and e["src"].startswith("https://www.youtube-nocookie.com/embed/Qp7TR1RAjXc?") and "list=RDQp7TR1RAjXc" in e["src"] and "autoplay=1" in e["src"]),
                "watch?v=ID&list=RD... : lecteur sur la video, dans sa liste", e)
        e, op = await ouvrir_e(pg, 5, 15)
        rapport(bool(e and e["src"].startswith("https://www.youtube-nocookie.com/embed/videoseries?") and "list=PLabcdefghijkl" in e["src"]), "playlist?list=PL... : lecteur de la liste (videoseries)", e)
        e, op = await ouvrir_e(pg, -8, 5)
        rapport(bool(e and e["src"].startswith("https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?") and "list" not in e["src"]), "liste invalide (caracteres interdits) : ignoree, la video seule", e)
        e, op = await ouvrir_e(pg, -10, -8)
        rapport(bool(e and e["src"] == "https://www.youtube.com/playlist?list=a"), "playlist sans liste valide : pas de lecteur, adresse telle quelle", e)
        e, op = await ouvrir_e(pg, 5, -15)
        rapport(e and e["src"] == "http://exemple.invalid/x" and not op, "http depuis une page qui n'est pas en https : cadre", (e, op))
        e, op = await ouvrir_e(pg, 15, -15)
        rapport(e is None and len(op) == 1 and op[0][0] == HOP and op[0][1] == "_self", "hop:// avec frame : pas de cadre, comme avant (meme onglet)", (e, op))
        e, op = await ouvrir_e(pg, -15, 0)
        rapport(e is None and len(op) == 1 and op[0][1] == "_blank", "zone sans frame : nouvel onglet, comme avant", (e, op))

        # en marchant dedans : rien n'est charge avant le clic
        await pg.evaluate("window.__op = []; (document.getElementById('frameWin') || {remove(){}}).remove()")
        await aller(pg, 0, 16)   # une arrivee dans le cercle (teleportation) ne declenche pas : il faut y marcher
        if await pg.evaluate("document.body.classList.contains('padOn')"):
            await pg.keyboard.press("KeyK"); await pg.wait_for_timeout(200)
        await pg.keyboard.down("ArrowUp")
        try:
            await pg.wait_for_function("!!document.getElementById('frameWin')", timeout=15000)
        except Exception:
            pass
        await pg.keyboard.up("ArrowUp")
        e = await etat(pg)
        rapport(e and e["src"] is None and e["load"] and "exemple.invalid" in e["loadTxt"], "enter : fenetre avec bouton « Charger (contacte ...) », aucun cadre charge", e)
        await pg.evaluate("document.querySelector('#frameWin .fwLoad').click()"); await pg.wait_for_timeout(200)
        e = await etat(pg)
        rapport(e and e["src"] == "https://exemple.invalid/e" and not e["load"], "enter : le clic sur le bouton charge la page", e)

        # miroir JavaScript de la validation
        js = await pg.evaluate("""(() => { window.__v.setZones([
            { id: 'a', type: 'url', target: 'https://x.invalid/', frame: true }, { id: 'b', type: 'url', target: 'https://x.invalid/', frame: false },
            { id: 'c', type: 'portal', frame: true }, { id: 'd', type: 'url', target: 'https://x.invalid/', frame: 'oui' }, { id: 'e', type: 'image', frame: true },
            { id: 'f', type: 'ha', target: 'http://x.invalid/', frame: true }, { id: 'g', type: 'url', target: 'https://x.invalid/' }]);
            return window.__v.getZones().map(z => [z.id, z.frame === true ? 1 : ('frame' in z ? 2 : 0)]); })()""")
        rapport(js == [["a", 1], ["b", 0], ["c", 0], ["d", 0], ["e", 0], ["f", 0], ["g", 0]], "JavaScript (setZones) : frame gardee vraie et seulement pour une zone url", js)
        rapport(not errs, "aucune erreur JavaScript", errs)

        # Python (clean_zones) : meme resultat
        spec = importlib.util.spec_from_file_location("g2h", DIST / "glb2html.py"); g2h = importlib.util.module_from_spec(spec); spec.loader.exec_module(g2h)
        cz = g2h.clean_zones([{"id": "a", "type": "url", "target": "https://x.invalid/", "frame": True}, {"id": "b", "type": "url", "target": "https://x.invalid/", "frame": False},
                              {"id": "c", "type": "portal", "frame": True}, {"id": "d", "type": "url", "target": "https://x.invalid/", "frame": "oui"},
                              {"id": "e", "type": "image", "frame": True}, {"id": "f", "type": "ha", "target": "http://x.invalid/", "frame": True},
                              {"id": "g", "type": "url", "target": "https://x.invalid/"}], "private")
        py = [[z["id"], 1 if z.get("frame") is True else (2 if "frame" in z else 0)] for z in cz]
        rapport(py == js, "Python (clean_zones) : meme resultat que JavaScript", py)

        # page en https : http (contenu mixte) et meme origine -> pas de cadre
        ctx = await br.new_context(locale="fr-FR")
        async def servir(route):
            u = route.request.url
            if u.startswith("https://web3d.test/"):
                nom = u[len("https://web3d.test/"):].split("?")[0] or "p.html"
                f = tmp / nom
                if f.is_file():
                    return await route.fulfill(body=f.read_bytes(), content_type=mimetypes.guess_type(nom)[0] or "application/octet-stream")
            await route.abort()
        await ctx.route("**/*", servir)
        ps = await ctx.new_page(); errs2 = []
        ps.on("pageerror", lambda e: errs2.append(str(e)))
        await ps.goto("https://web3d.test/p.html"); await pret(ps)
        e, op = await ouvrir_e(ps, 5, -15)
        rapport(e is None and len(op) == 1 and op[0][0] == "http://exemple.invalid/x" and op[0][1] == "_blank", "page https : lien http (contenu mixte) -> pas de cadre, nouvel onglet", (e, op))
        e, op = await ouvrir_e(ps, 15, 0)
        rapport(e is None and len(op) == 1 and op[0][0] == "https://web3d.test/autre" and op[0][1] == "_blank", "page https : meme origine -> pas de cadre, nouvel onglet", (e, op))
        e, op = await ouvrir_e(ps, -5, -15)
        rapport(e and e["src"] == "https://exemple.invalid/page" and not op, "page https : autre site https -> cadre", (e, op))
        rapport(not errs2, "aucune erreur JavaScript (page https)", errs2)
        await br.close()
    print("\nRESULTAT : " + ("tout est passe" if not echecs else f"ECHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
