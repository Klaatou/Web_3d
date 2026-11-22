#!/usr/bin/env python3
"""Test 1.11.20 : radio a plusieurs flux (urls, labels) et lignes Musique / Radio de la fenetre Etat.
- glb2html.py --zones convertit urls + labels (ancienne forme) et garde streams (nouvelle forme : paires [label, url]) (clean_zones de gen_tpl.py, comme cleanZone de core.js : meme resultat sur des valeurs sales) ;
- liste des flux : visible avec les labels, un flux casse n'empeche pas de choisir un autre flux, le choix du flux casse le reessaie,
  la liste n'est pas refaite a chaque pas (une liste ouverte ne se refermerait pas), retour a 0 en quittant la zone ;
- case « couper le son » de la fenetre Etat : meme action que Reglages (une seule source) ;
- boutons ⏮ ⏭ et compteur n/N de la playlist (boucle aux deux bouts).
Prerequis : pip install playwright websockets && playwright install chromium ; python build.py avant. Variables : THREE_DIR, CHROMIUM.
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, functools, http.server, json, math, os, pathlib, struct, subprocess, sys, tempfile, threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_cast_"))
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


def wav(path, secondes=40):
    n = 8000 * secondes
    data = bytes(int(128 + 100 * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(n))
    path.write_bytes(b"RIFF" + struct.pack("<I", 36 + n) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 8000, 8000, 1, 8) + b"data" + struct.pack("<I", n) + data)


DEMANDES = []   # chemins demandes au serveur (compte des reessais)


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        DEMANDES.append(self.path)
        super().do_GET()


def serveur(dossier):
    h = functools.partial(Handler, directory=str(dossier))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def page(port):
    u = lambda n: f"http://127.0.0.1:{port}/{n}"
    Z = lambda i, t, x, z, **k: dict({"id": i, "type": t, "label": "Zone " + i, "x": x, "y": 15, "z": z}, **k)
    zones = [Z("multi", "cast", 0, 0, radius=40, urls=[u("absent.mp3"), u("flux.wav"), u("flux.wav")], labels=["Casse", "Bon", "Autre"]),
             Z("seul", "cast", -50, 0, radius=5, target=u("flux.wav")),
             Z("sale", "cast", 0, 50, radius=5, urls=["  " + u("a.wav") + "\u0001 ", "", 5, u("b.wav")], labels=["", "Vide", None, "B\u0002x"], target="ignore"),
             Z("paires", "cast", 0, -50, radius=5, streams=[["  Un\u0001 ", u("a.wav")], ["", u("b.wav")], u("c.wav"), ["Seul"], [], ["Vide", ""], ["X", 5]]),
             Z("multi2", "cast", 50, -50, radius=5, streams=[["Casse", u("absent.mp3")], ["Bon", u("flux.wav")], ["Autre", u("flux.wav")]]),
             Z("mus", "audio", 50, 0, radius=8, folder="audio", tracks=["1-a.wav", "2-b.wav", "3-c.wav"])]
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
    return out, zones


async def main():
    from playwright.async_api import async_playwright
    sol_glb(tmp / "sol.glb"); wav(tmp / "flux.wav")
    srv = serveur(tmp)
    out, brut = page(srv.server_address[1])
    async with async_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
        br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
        pg = await br.new_page(locale="fr-FR"); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(out.as_uri())
        await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
        await pg.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
        zs = {z["id"]: z for z in await pg.evaluate("window.__v.getZones()")}
        port = srv.server_address[1]
        m = zs["multi"]
        flux = lambda n: f"http://127.0.0.1:{port}/{n}"
        rapport(m.get("streams") == [["Casse", flux("absent.mp3")], ["Bon", flux("flux.wav")], ["Autre", flux("flux.wav")]] and not any(k in m for k in ("urls", "labels")) and m["target"] == "",
                "glb2html --zones : l'ancienne forme (urls + labels) est convertie en streams ; ni urls ni labels n'est ecrit", m)
        rapport(zs["multi2"].get("streams") == m.get("streams"), "la nouvelle forme (paires) et l'ancienne donnent le meme resultat", zs["multi2"])
        rapport(zs["seul"].get("streams") == [["", flux("flux.wav")]], "zone radio avec target seul : un seul flux, sans label", zs["seul"])
        # meme resultat en Python (page generee) et en JavaScript (setZones) sur des valeurs sales
        js = {z["id"]: z for z in await pg.evaluate("(z) => window.__v.setZones(z, { editor: true })", brut)}
        pj, jj = zs["sale"], js["sale"]
        rapport(pj.get("streams") == jj.get("streams") and pj["streams"] == [["", flux("a.wav")], ["", "5"], ["Bx", flux("b.wav")]], "valeurs sales (ancienne forme) : Python (gen_tpl) et JavaScript (core.js) donnent le meme resultat",
                (pj.get("streams"), jj.get("streams")))
        pp, jp = zs["paires"], js["paires"]
        rapport(pp.get("streams") == jp.get("streams") and pp["streams"] == [["Un", flux("a.wav")], ["", flux("b.wav")], ["", flux("c.wav")], ["", "Seul"], ["X", "5"]], "valeurs sales (paires) : Python et JavaScript donnent le meme resultat, label d'abord", (pp.get("streams"), jp.get("streams")))
        await pg.goto(out.as_uri())
        await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
        await pg.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
        rinfo = lambda: pg.evaluate("(() => { const e = document.getElementById('radioInfo'); return e.hidden ? '' : e.textContent; })()")
        minfo = lambda: pg.evaluate("(() => { const e = document.getElementById('musicInfo'); return e.hidden ? '' : e.textContent; })()")
        async def jouer(fn):
            try:
                await pg.wait_for_function(fn, timeout=15000)
            except Exception:
                pass
        await pg.evaluate("window.__v.walkStart({ pos: [0, 15, 60], yaw: 0 })"); await pg.wait_for_timeout(400)
        # ---- musique : boutons et compteur
        await pg.evaluate("window.__v.teleportTo([50, 15, 3], 0)"); await pg.wait_for_timeout(400)
        await pg.keyboard.press("ControlLeft"); await jouer("window.__m.playing()")
        cnt = lambda: pg.evaluate("document.getElementById('musicCount').textContent.trim()")
        vis = await pg.evaluate("['musicPrev', 'musicCount', 'musicNext'].map(i => !document.getElementById(i).hidden)")
        rapport(await pg.evaluate("window.__m.playing()") and vis == [True, True, True] and await cnt() == "1/3", "musique de 3 pistes : boutons et compteur « 1/3 » visibles", (vis, await cnt()))
        click = lambda i: pg.evaluate(f"document.getElementById('{i}').click()")
        await click("musicNext"); await pg.wait_for_timeout(300); a = await cnt()
        await click("musicNext"); await click("musicNext"); await pg.wait_for_timeout(300); b = await cnt()
        rapport(a == "2/3" and b == "1/3", "suivant : 2/3, puis 3/3 et retour a 1/3 (boucle)", (a, b))
        await click("musicPrev"); await pg.wait_for_timeout(300); c = await cnt()
        await click("musicPrev"); await pg.wait_for_timeout(300); d = await cnt()
        rapport(c == "3/3" and d == "2/3", "precedent depuis la premiere piste : va a la derniere (3/3), puis 2/3", (c, d))
        await jouer("window.__m.playing()")
        rapport(await pg.evaluate("window.__m.playing()") and await pg.evaluate("window.__m.trackIndex()") == 1, "la lecture continue sur la piste choisie (2e)", await pg.evaluate("window.__m.trackIndex()"))
        # ---- radio : liste des flux
        await pg.evaluate("window.__v.teleportTo([0, 15, 10], 0)")
        await jouer("/illisible/.test(document.getElementById('radioInfo').textContent)")
        opts = await pg.evaluate("(() => { const s = document.getElementById('radioSel'); return [s.hidden, [...s.options].map(o => o.textContent), s.value]; })()")
        rapport(opts[0] is False and opts[1] == ["Casse", "Bon", "Autre"] and opts[2] == "0", "liste des flux : visible, avec les labels, premier flux choisi", opts)
        t = await rinfo()
        rapport("Casse" in t and "illisible" in t, "premier flux casse : la ligne dit « Casse » et l'erreur", t)
        await pg.evaluate("(() => { const s = document.getElementById('radioSel'); s.value = '1'; s.dispatchEvent(new Event('change')); })()")
        await jouer("window.__r.playing()")
        t = await rinfo()
        rapport(await pg.evaluate("window.__r.playing()") and "Bon" in t and "illisible" not in t, "un flux casse n'empeche pas de choisir un autre flux : le deuxieme joue", t)
        await pg.evaluate("(() => { const s = document.getElementById('radioSel'); s.value = '0'; s.dispatchEvent(new Event('change')); })()")
        await jouer("/illisible/.test(document.getElementById('radioInfo').textContent)")
        t = await rinfo()
        rapport(not await pg.evaluate("window.__r.playing()") and "Casse" in t and "illisible" in t, "choisir de nouveau le flux casse : il est reessaye", t)
        await pg.evaluate("(() => { const s = document.getElementById('radioSel'); s.value = '1'; s.dispatchEvent(new Event('change')); })()")
        await jouer("window.__r.playing()")
        await pg.evaluate("window.__n = 0; new MutationObserver(l => { window.__n += l.length; }).observe(document.getElementById('radioSel'), { childList: true })")
        for z in (11, 12, 13, 14, 15, 16):
            await pg.evaluate(f"window.__v.teleportTo([0, 15, {z}], 0)"); await pg.wait_for_timeout(120)
        rapport(await pg.evaluate("window.__n") == 0 and await pg.evaluate("document.getElementById('radioSel').value") == "1", "la liste des flux n'est pas refaite a chaque pas (et le choix reste)", await pg.evaluate("window.__n"))
        # ---- case de la fenetre Etat
        rapport(await pg.evaluate("document.getElementById('stateRadioCk').checked && document.getElementById('stateMusicCk').checked"), "fenetre Etat : les deux cases sont cochees au depart")
        await pg.evaluate("document.getElementById('stateRadioCk').click()"); await pg.wait_for_timeout(400)
        t = await rinfo()
        rapport(not await pg.evaluate("window.__r.playing()") and not await pg.evaluate("document.getElementById('visRadio').checked") and "coup" in t, "case Radio decochee (fenetre Etat) : la radio s'arrete, la case de Reglages suit", t)
        await pg.evaluate("document.getElementById('stateRadioCk').click()")
        await jouer("window.__r.playing()")
        rapport(await pg.evaluate("window.__r.playing()") and not await pg.evaluate("document.getElementById('stateMusicCk').checked || document.getElementById('visMusic').checked"), "case Radio recochee : la radio reprend, la musique est decochee partout (une seule source)")
        # ---- quitter la zone puis y revenir : le flux choisi est retrouve (1.13.3 ; avant : retour au premier flux)
        avant = await pg.evaluate("document.getElementById('radioSel').value")
        await pg.evaluate("window.__v.teleportTo([0, 15, 100], 0)"); await pg.wait_for_timeout(400)
        await pg.evaluate("window.__v.teleportTo([0, 15, 10], 0)"); await pg.wait_for_timeout(600)
        rapport(avant != "0" and await pg.evaluate("document.getElementById('radioSel').value") == avant, "quitter la zone puis y revenir : le flux choisi est retrouve (1.13.3)", (avant, await pg.evaluate("document.getElementById('radioSel').value")))
        # editeur du viewer : avec plusieurs flux, la saisie de la premiere adresse change celle du premier flux (meme forme de correctif que viewer_tpl.html)
        r = await pg.evaluate("(() => { const l = window.__v.getZones(); const z = l.find(x => x.id === 'multi'); const v = 'http://nouveau.invalid/x'; Object.assign(z, { streams: [[z.streams && z.streams[0] ? z.streams[0][0] : '', v], ...(z.streams || []).slice(1)] }); const o = window.__v.setZones(l, { editor: true }).find(x => x.id === 'multi'); return [o.streams.length, o.streams[0][1], o.streams[0][0]]; })()")
        rapport(r == [3, "http://nouveau.invalid/x", "Casse"] and "...(z.streams || []).slice(1)" in (DIST / "glb-viewer.html").read_text(encoding="utf-8"), "editeur : modifier la premiere adresse change le premier flux (3 flux, label garde) ; le viewer contient le correctif", r)
        rapport(not errs, "aucune erreur JavaScript", errs)
        await br.close()
    srv.shutdown()
    print("\nRESULTAT : " + ("tout est passe" if not echecs else f"ECHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
