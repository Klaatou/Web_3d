#!/usr/bin/env python3
"""Test 1.11.24 : fenetre Son et pave de fleches deplacable.
- fenetre Son : fermee au depart ; la fleche des lignes Radio / Musique de la fenetre Etat l'ouvre ET ferme la fenetre Etat ; elle reprend le texte, le choix du flux,
  les boutons et le compteur de la musique, les cases (une seule source) ; la croix la ferme (l'Etat reste ferme) ; le clic sur le cone d'une zone radio / audio a portee
  l'affiche ou la ferme, un clic sur le cone d'une zone hors de portee ne fait rien ; elle est dans le fichier de disposition (quatrieme fenetre) ;
- pave de fleches : poignee, glisser = deplacer, position gardee apres rechargement, recadree dans l'ecran, double-clic = retour a la place d'origine,
  dans le fichier de disposition.
Prerequis : pip install playwright websockets && playwright install chromium ; python build.py avant. Variables : THREE_DIR, CHROMIUM.
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, functools, http.server, json, math, os, pathlib, struct, subprocess, sys, tempfile, threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_son_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def sol_glb(path):
    pos = struct.pack("<12f", -120, 0, -120, 120, 0, -120, 120, 0, 120, -120, 0, 120)
    blob = pos + struct.pack("<6H", 0, 2, 1, 0, 3, 2) + b"\0\0"
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-120, 0, -120], "max": [120, 0, 120]},
                       {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * ((4 - len(js) % 4) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob))
                     + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def wav(path, secondes=40):
    n = 8000 * secondes
    data = bytes(int(128 + 100 * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(n))
    path.write_bytes(b"RIFF" + struct.pack("<I", 36 + n) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 8000, 8000, 1, 8) + b"data" + struct.pack("<I", n) + data)


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


class Serveur(http.server.ThreadingHTTPServer):
    def handle_error(self, request, client_address):   # le navigateur coupe le flux audio quand la radio s'arrete : sous Windows, ce n'est pas une erreur du test
        if not isinstance(sys.exc_info()[1], (ConnectionError, TimeoutError)):
            super().handle_error(request, client_address)


def serveur(dossier):
    h = functools.partial(Handler, directory=str(dossier))
    srv = Serveur(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def page(port):
    u = lambda n: f"http://127.0.0.1:{port}/{n}"
    Z = lambda i, t, x, z, **k: dict({"id": i, "type": t, "label": "Zone " + i, "x": x, "y": 15, "z": z}, **k)
    zones = [Z("multi", "cast", 0, 0, radius=40, streams=[["Un", u("flux.wav")], ["Deux", u("flux.wav")], ["Trois", u("flux.wav")]]),
             Z("sans", "cast", -100, 0, radius=8, label="", streams=[["Alpha", u("flux.wav")], ["Beta", u("flux.wav")]]),
             Z("mus", "audio", 100, 0, radius=8, folder="audio", tracks=["1-a.wav", "2-b.wav", "3-c.wav"])]
    (tmp / "audio").mkdir(); [wav(tmp / "audio" / n, 40) for n in ("1-a.wav", "2-b.wav", "3-c.wav")]
    (tmp / "z.json").write_text(json.dumps(zones), encoding="utf-8")
    out = tmp / "p.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--zones", str(tmp / "z.json"), "--no-sea", *vend],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    t = out.read_text(encoding="utf-8")
    for a, b in (("const viewer = createViewer(", "const viewer = window.__v = createViewer("), ("const RADIO = (() => {", "const RADIO = window.__r = (() => {"), ("const MUSIC = (() => {", "const MUSIC = window.__m = (() => {")):
        if a not in t:
            sys.exit(f"[ECHEC] marqueur absent de la page : {a}")
        t = t.replace(a, b, 1)
    out.write_text(t, encoding="utf-8")
    return out


async def main():
    from playwright.async_api import async_playwright
    sol_glb(tmp / "sol.glb"); wav(tmp / "flux.wav")
    srv = serveur(tmp)
    out = page(srv.server_address[1])
    async with async_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
        br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
        ctx = await br.new_context(locale="fr-FR", viewport={"width": 1000, "height": 700}, accept_downloads=True)
        pg = await ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))

        async def ouvrir():
            await pg.goto(out.as_uri())
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
            await pg.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")

        ev = pg.evaluate
        hid = lambda i: ev(f"document.getElementById('{i}').hidden")
        txt = lambda i: ev(f"(() => {{ const e = document.getElementById('{i}'); return e.hidden ? '' : e.textContent; }})()")
        await ouvrir()
        await ev("window.__v.walkStart({ pos: [0, 15, 60], yaw: 0 })"); await pg.wait_for_timeout(400)

        print("--- 1. fenetre Son fermee au depart ; la fleche l'ouvre et ferme l'Etat")
        rapport(await hid("soundInfo") and not await hid("stateInfo"), "Son fermee, Etat ouverte au depart")
        await ev("window.__v.teleportTo([0, 15, 10], 0)"); await pg.wait_for_timeout(600)
        try:
            await pg.wait_for_function("!document.getElementById('radioInfo').hidden", timeout=15000)
        except Exception:
            pass
        rapport(not await hid("soundUpRadio") and "Radio" in await txt("radioInfo"), "fenetre Etat : ligne Radio et fleche visibles a portee", await txt("radioInfo"))
        await ev("document.getElementById('soundUpRadio').click()"); await pg.wait_for_timeout(200)
        rapport(not await hid("soundInfo") and await hid("stateInfo"), "fleche : Son ouverte ET Etat fermee", (await hid("soundInfo"), await hid("stateInfo")))
        rt, st = await txt("radioInfo"), await txt("soundRadioInfo")
        rapport(st != "" and st.replace("▲", "").strip() == rt.replace("▲", "").strip(), "Son reprend la ligne Radio de la fenetre Etat", (rt, st))
        tt = (await ev("document.getElementById('soundHead').textContent")).strip()
        rapport(tt.endswith("Son \u00b7 Radio"), "titre de Son : le type de la zone active (Radio)", tt)
        opts = await ev("(() => { const s = document.getElementById('soundRadioSel'); return [s.hidden, [...s.options].map(o => o.textContent), s.value]; })()")
        rapport(opts[0] is False and opts[1] == ["Un", "Deux", "Trois"] and opts[2] == "0", "Son : choix du flux avec les labels", opts)
        await ev("(() => { const s = document.getElementById('soundRadioSel'); s.value = '2'; s.dispatchEvent(new Event('change')); })()"); await pg.wait_for_timeout(300)
        rapport(await ev("document.getElementById('radioSel').value") == "2", "choisir un flux dans Son change celui de la radio (liste de l'Etat suit)", await ev("document.getElementById('radioSel').value"))

        print("--- 2. cases de Son : meme action que celles de l'Etat")
        await pg.keyboard.press("ControlLeft")
        try:
            await pg.wait_for_function("window.__r.playing()", timeout=15000)
        except Exception:
            pass
        ok0 = await ev("window.__r.playing()")
        await ev("document.getElementById('soundRadioCk').click()"); await pg.wait_for_timeout(400)
        rapport(ok0 and not await ev("window.__r.playing()") and not await ev("document.getElementById('visRadio').checked") and not await ev("document.getElementById('stateRadioCk').checked"),
                "case Radio de Son decochee : la radio s'arrete, Reglages et Etat suivent", (ok0, await ev("window.__r.playing()")))
        await ev("document.getElementById('soundRadioCk').click()")
        try:
            await pg.wait_for_function("window.__r.playing()", timeout=15000)
        except Exception:
            pass
        rapport(await ev("window.__r.playing()") and await ev("document.getElementById('soundRadioCk').checked && document.getElementById('stateRadioCk').checked"), "case recochee : la radio reprend, les cases sont cochees")

        print("--- 3. musique : boutons et compteur dans Son")
        await ev("window.__v.teleportTo([100, 15, 3], 0)"); await pg.wait_for_timeout(500)
        await ev("document.getElementById('soundMusicCk').click()"); await pg.wait_for_timeout(300)
        rapport(not await ev("document.getElementById('soundRadioCk').checked") and not await ev("document.getElementById('visRadio').checked") and await ev("document.getElementById('stateMusicCk').checked"),
                "case Musique de Son cochee : la radio est decochee (une seule source), l'Etat et Reglages suivent")
        await pg.keyboard.press("ControlLeft")
        try:
            await pg.wait_for_function("window.__m.playing()", timeout=15000)
        except Exception:
            pass
        rapport("Musique" in await txt("soundMusicInfo") or "usique" in await txt("soundMusicInfo"), "Son : ligne Musique", await txt("soundMusicInfo"))
        tt = (await ev("document.getElementById('soundHead').textContent")).strip()
        rapport(tt.endswith("Son \u00b7 PL Audio"), "titre de Son : PL Audio pour une zone audio", tt)
        vis = await ev("['soundMusicPrev', 'soundMusicCount', 'soundMusicNext'].map(i => !document.getElementById(i).hidden)")
        c0 = (await ev("document.getElementById('soundMusicCount').textContent")).strip()
        await ev("document.getElementById('soundMusicNext').click()"); await pg.wait_for_timeout(300)
        c1 = (await ev("document.getElementById('soundMusicCount').textContent")).strip()
        rapport(vis == [True, True, True] and c0 == "1/3" and c1 == "2/3", "Son : precedent, compteur et suivant (1/3 puis 2/3)", (vis, c0, c1))

        print("--- 4. la croix ferme Son (l'Etat reste ferme)")
        await ev("document.getElementById('soundClose').click()"); await pg.wait_for_timeout(150)
        rapport(await hid("soundInfo") and await hid("stateInfo") and await ev("localStorage.getItem('glb2html_sound')") == "0", "Son fermee, Etat toujours fermee, etat retenu")

        print("--- 5. clic sur le cone d'une zone a portee")
        await ev("window.__v.teleportTo([0, 15, 12], 0)"); await pg.wait_for_timeout(700)
        cones = await ev("window.__v.getCones()")
        cm = [c for c in cones if c["id"] == "multi"]
        rapport(len(cm) == 1 and cm[0]["visible"], "cone de la zone radio present", cones)
        if cm:
            async def cliquer(c):
                await pg.mouse.click(c["sx"], c["sy"]); await pg.wait_for_timeout(300)
            await cliquer(cm[0])
            rapport(not await hid("soundInfo"), "clic sur le cone de la radio a portee : Son s'affiche", (cm[0]["sx"], cm[0]["sy"]))
            cm = [c for c in await ev("window.__v.getCones()") if c["id"] == "multi"]
            await cliquer(cm[0])
            rapport(await hid("soundInfo"), "second clic sur le cone : Son se ferme")
            rapport(await hid("stateInfo"), "le clic sur le cone ne touche pas a l'Etat")
        await ev("window.__v.teleportTo([-80, 15, 90], 0)"); await pg.wait_for_timeout(700)
        cones = await ev("window.__v.getCones()")
        cm = [c for c in cones if c["id"] == "multi" and 0 < c["sx"] < 1000 and 0 < c["sy"] < 700]
        if cm and await hid("radioInfo"):
            await pg.mouse.click(cm[0]["sx"], cm[0]["sy"]); await pg.wait_for_timeout(300)
            rapport(await hid("soundInfo"), "clic sur le cone d'une zone hors de portee : rien", cm[0])
        else:
            print("[INFO]  cone hors de portee non visible depuis ce point : controle saute")

        print("--- 6. Son dans le fichier de disposition")
        await ev("window.__v.teleportTo([0, 15, 12], 0)"); await pg.wait_for_timeout(600)
        await ev("document.getElementById('soundUpRadio') && document.getElementById('soundUpRadio').click()"); await pg.wait_for_timeout(200)
        lay = json.loads(await ev("localStorage.getItem('glb2html_layout') || 'null'") or "null")
        await ev("document.getElementById('optsBtn').click()"); await pg.wait_for_timeout(150)
        async with pg.expect_download() as dl:
            await ev("document.getElementById('laySave').click()")
        d = await dl.value
        fic = json.loads(pathlib.Path(await d.path()).read_text(encoding="utf-8"))
        rapport("S" in fic["layout"]["wins"] and "S" in fic["layout"]["order"]["L"] + fic["layout"]["order"]["R"] + [k for k, w in fic["layout"]["wins"].items() if w["pile"] == "F"]
                and fic["ls"].get("glb2html_sound") == "1", "fichier de disposition : Son presente et son ouverture enregistree", fic)
        await ev("document.getElementById('layReset').click()"); await pg.wait_for_timeout(200)
        await ev("document.getElementById('optsBtn').click()")

        print("--- 7. pave de fleches deplacable")
        if await ev("document.getElementById('pad').hidden"):
            await ev("document.getElementById('visPad').click()")
        await pg.wait_for_timeout(300)
        R = lambda i: ev(f"(() => {{ const r = document.getElementById('{i}').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }})()")
        p0 = await R("pad")
        g0 = await R("padGrip")
        rapport(not await ev("document.getElementById('pad').hidden") and g0[3] > 8 and g0[1] < p0[1], "pave visible, poignee au-dessus", (p0, g0))
        await pg.mouse.move(g0[0] + g0[2] / 2, g0[1] + g0[3] / 2); await pg.mouse.down()
        await pg.mouse.move(g0[0] + g0[2] / 2 + 20, g0[1] + g0[3] / 2 - 30, steps=3); await pg.mouse.move(300, 300, steps=8); await pg.mouse.up(); await pg.wait_for_timeout(150)
        p1 = await R("pad")
        k = await ev("localStorage.getItem('glb2html_padPos')")
        rapport(await ev("document.getElementById('pad').classList.contains('padFree')") and abs(p1[0] - p0[0]) > 100 and k is not None, "glisser la poignee deplace le pave, position retenue", (p0, p1, k))
        await ouvrir(); await ev("window.__v.walkStart({ pos: [0, 15, 60], yaw: 0 })"); await pg.wait_for_timeout(500)
        p2 = await R("pad")
        rapport(abs(p2[0] - p1[0]) < 3 and abs(p2[1] - p1[1]) < 3, "apres rechargement le pave reste ou il etait", (p1, p2))
        await ev("localStorage.setItem('glb2html_padPos', JSON.stringify({ x: 5000, y: 5000 }))"); await ev("window.dispatchEvent(new Event('resize'))")
        await ouvrir(); await ev("window.__v.walkStart({ pos: [0, 15, 60], yaw: 0 })"); await pg.wait_for_timeout(500)
        p3 = await R("pad")
        rapport(p3[0] + p3[2] <= 1001 and p3[1] + p3[3] <= 701 and p3[0] >= 0 and p3[1] >= 0, "position hors ecran : le pave est recadre dans la fenetre", p3)
        g3 = await R("padGrip")
        await pg.mouse.dblclick(g3[0] + g3[2] / 2, g3[1] + g3[3] / 2); await pg.wait_for_timeout(200)
        p4 = await R("pad")
        rapport(not await ev("document.getElementById('pad').classList.contains('padFree')") and await ev("localStorage.getItem('glb2html_padPos')") is None and abs(p4[0] - p0[0]) < 3 and abs(p4[1] - p0[1]) < 3,
                "double-clic sur la poignee : retour a la place d'origine", (p0, p4))
        await ev("localStorage.setItem('glb2html_padPos', JSON.stringify({ x: 200, y: 200 }))")
        await ev("document.getElementById('optsBtn').click()"); await pg.wait_for_timeout(150)
        async with pg.expect_download() as dl2:
            await ev("document.getElementById('laySave').click()")
        fic2 = json.loads(pathlib.Path(await (await dl2.value).path()).read_text(encoding="utf-8"))
        rapport(json.loads(fic2["ls"].get("glb2html_padPos") or "null") == {"x": 200, "y": 200}, "la position du pave est dans le fichier de disposition", fic2["ls"])
        await ev("document.getElementById('layReset').click()"); await pg.wait_for_timeout(200)
        rapport(await ev("localStorage.getItem('glb2html_padPos')") is None and not await ev("document.getElementById('pad').classList.contains('padFree')"), "disposition d'origine : le pave revient a sa place")

        print("--- 8. bulle de la ligne Radio : le label du flux, pas l'id de la zone")
        await ev("window.__v.teleportTo([0, 15, 12], 0)"); await pg.wait_for_timeout(600)
        b1 = await ev("document.getElementById('radioInfo').title")
        rapport(b1.split("\n")[0] == "Zone radio : Zone multi" and b1.split("\n")[1].startswith("Flux : "), "zone avec label : Zone radio puis Flux", b1)
        await ev("window.__v.teleportTo([-100, 15, 3], 0)"); await pg.wait_for_timeout(700)
        b2 = await ev("document.getElementById('radioInfo').title")
        rapport(b2.split("\n")[0] == "Flux : Alpha (1/2)" and "Zone radio" not in b2, "zone sans label : la bulle commence par le flux (Alpha), ni id ni zone", b2)
        print("--- 9. volume propre a la radio et a la musique (curseur escamotable de Son)")
        await ev("window.__v.teleportTo([0, 15, 12], 0)"); await pg.wait_for_timeout(600)
        await ev("(() => { const u = document.getElementById('soundUpRadio'); if (document.getElementById('soundInfo').hidden && u) u.click(); })()"); await pg.wait_for_timeout(200)
        await ev("(() => { const c = document.getElementById('stateRadioCk'); if (c && !c.checked) c.click(); })()")   # une etape precedente a pu decocher la radio
        try:
            await pg.wait_for_function("window.__r.playing()", timeout=15000)
        except Exception:
            pass
        v0 = await ev("(() => { const r = document.getElementById('soundVol'); return [document.getElementById('soundVolRow').hidden, r.min, r.value, document.getElementById('soundVolBtn').getAttribute('aria-expanded')]; })()")
        rapport(v0 == [True, "1", "100", "false"], "curseur replie au depart, de 1 a 100, a 100 (sans changement)", v0)
        l0, ic100 = await ev("window.__r.level()"), await ev("document.getElementById('soundVolBtn').textContent")
        await ev("document.getElementById('soundVolBtn').click()")
        v1 = await ev("[document.getElementById('soundVolRow').hidden, document.getElementById('soundVolBtn').getAttribute('aria-expanded')]")
        rapport(v1 == [False, "true"], "l'icone haut-parleur deplie le curseur", v1)
        setv = lambda n: ev("(() => { const r = document.getElementById('soundVol'); r.value = '%d'; r.dispatchEvent(new Event('input')); return document.getElementById('soundVolBtn').textContent; })()" % n)
        ic50 = await setv(50); await pg.wait_for_timeout(300)
        l1 = await ev("window.__r.level()")
        rapport(l0 > 0 and 0.45 <= l1 / l0 <= 0.55, "curseur a 50 : le volume reel de la radio est divise par deux", (l0, l1))
        vis = json.loads(await ev("localStorage.getItem('glb2html_visitor')"))
        rapport(vis.get("srcVolume") == 50 and vis.get("volume") == 50, "valeur retenue (srcVolume) ; le volume des Sons de Reglages ne change pas", vis)
        ic10 = await setv(10)
        rapport(len({ic100, ic50, ic10}) == 3, "le dessin de l'icone change avec le niveau (3 niveaux)", (ic100, ic50, ic10))
        await ev("document.getElementById('soundVol').dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))")
        rapport(await hid("soundVolRow"), "Echap replie le curseur")
        await setv(100)
        rapport(not errs, "aucune erreur JavaScript", errs)
        await br.close()
    srv.shutdown()
    print("\nRESULTAT : " + ("tout est passe" if not echecs else f"ECHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
