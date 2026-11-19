#!/usr/bin/env python3
"""Test 1.12.21 (complete au 1.12.22) : arbitrage commun du son (radio, musique, ecrans video, fenetre flottante), ligne Video de la fenetre Son, bouton muet et touche N.
- la source la plus proche (gain) parle ; un geste du visiteur (clic sur un ecran, flux choisi) la rend prioritaire ; cocher une source decoche les autres ;
- ligne Video dans la fenetre Son ; muet (touche N, bouton) coupe radio et sons video sans changer les cases ; une fenetre flottante chargee (iframe) les efface.
Le gain video est simule par le rappel onVideoTalk de la page (la portee est calculee dans core.js, testee par zone_video.py).
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
    zones = [{"id": "radio", "type": "cast", "label": "Zone radio", "x": 0, "y": 15, "z": 0, "radius": 40, "streams": [["Un", u("flux.wav")], ["Deux", u("flux.wav")]]}]
    (tmp / "z.json").write_text(json.dumps(zones), encoding="utf-8")
    out = tmp / "p.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--zones", str(tmp / "z.json"), "--no-sea", *vend],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    t = out.read_text(encoding="utf-8")
    for a, b in (("const viewer = createViewer(", "const viewer = window.__v = createViewer("), ("const RADIO = (() => {", "const RADIO = window.__r = (() => {"),
                 ("const SRC = {", "const SRC = window.__s = {"), ("viewer.onVideoTalk = (z, g, d) =>", "window.__vt = viewer.onVideoTalk = (z, g, d) =>"),
                 ("viewer.onVideoAct = z =>", "window.__va = viewer.onVideoAct = z =>"), ("const frameOpen = (z, u, how, label) => {", "const frameOpen = window.__fo = (z, u, how, label) => {"), ("viewer.videoSound = () =>", "window.__vs = viewer.videoSound = () =>")):
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
        ctx = await br.new_context(locale="fr-FR", viewport={"width": 1000, "height": 700})
        pg = await ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(out.as_uri())
        await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
        ev = pg.evaluate
        await ev("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
        hid = lambda i: ev(f"document.getElementById('{i}').hidden")
        chk = lambda i: ev(f"document.getElementById('{i}').checked")
        ECR = "{id: 'ecran', label: 'Ecran test', radius: 10, sound: true}"
        await ev("(() => { window.tick = i => { const c = document.getElementById(i); c.checked = true; c.onchange(); }; })()")
        await ev("window.__v.walkStart({ pos: [0, 15, 60], yaw: 0 })"); await pg.wait_for_timeout(300)
        await ev("window.__v.teleportTo([0, 15, 10], 0)"); await pg.wait_for_timeout(600)
        await pg.keyboard.press("ControlLeft")
        try:
            await pg.wait_for_function("window.__r.playing()", timeout=15000)
        except Exception:
            pass
        rapport(await ev("window.__r.playing()") and await ev("window.__s.win") == "radio", "radio seule a portee : elle joue", await ev("window.__s.win"))
        rapport(await ev("window.__vs()") == 0, "aucun ecran : le son video est a 0")

        print("--- 1. arbitrage par proximite")
        await ev(f"window.__vt({ECR}, 0.2, 14)"); await pg.wait_for_timeout(400)
        rapport(await ev("window.__s.win") == "radio" and await ev("window.__r.playing()") and await ev("window.__vs()") == 0, "ecran a 14 m, radio a 10 m : la plus proche en metres parle, la radio (1.12.25)", await ev("window.__s.win"))
        await ev(f"window.__vt({ECR}, 0.2, 8)"); await pg.wait_for_timeout(300)
        rapport(await ev("window.__s.win") == "video" and not await ev("window.__r.playing()") and await ev("window.__vs()") > 0, "ecran a 8 m, radio a 10 m : l'ecran, plus proche, parle", await ev("window.__s.win"))
        rl = await ev("[document.getElementById('radioInfo').hidden, document.getElementById('radioInfo').textContent, document.getElementById('soundRadioInfo').hidden, document.getElementById('radioSel').hidden]")
        rapport(rl[0] is False and "une autre source parle" in rl[1] and rl[2] is False and rl[3] is False, "la ligne Radio et le choix du flux restent affiches (une autre source parle)", rl)
        await ev(f"window.__vt({ECR}, 0.99, 0.1)"); await pg.wait_for_timeout(500)
        rapport(await ev("window.__s.win") == "video" and not await ev("window.__r.playing()") and await ev("window.__vs()") > 0, "ecran plus proche : il parle, la radio se tait", (await ev("window.__s.win"), await ev("window.__vs()")))
        rapport(not await hid("soundVideoInfo") and "Ecran test" in await ev("document.getElementById('soundVideoInfo').textContent") and await hid("soundNone"), "fenetre Son : ligne Video avec le nom de l'ecran, « aucune source » masque")
        await ev("window.__v.teleportTo([0, 15, 10], 0)")

        print("--- 2. geste du visiteur : priorite")
        await ev(f"window.__vt({ECR}, 0.2, 8)"); await pg.wait_for_timeout(300)
        rapport(await ev("window.__s.win") == "video", "ecran a son : il parle")
        await ev("window.__r.setIdx(0)"); await pg.wait_for_timeout(300)
        rapport(await ev("window.__s.win") == "radio" and await ev("window.__vs()") == 0, "geste sur la radio (flux choisi dans la liste, encore affichee) : elle reprend la parole")
        await ev(f"window.__va({ECR})"); await pg.wait_for_timeout(400)
        rapport(await ev("window.__s.win") == "video" and await ev("window.__vs()") > 0 and not await ev("window.__r.playing()"), "clic sur l'ecran : il passe devant la radio, meme plus loin", await ev("window.__s.win"))
        await ev("window.__r.setIdx(0)"); await pg.wait_for_timeout(400)
        rapport(await ev("window.__s.win") == "radio", "choisir un flux de la radio : elle reprend la priorite")
        await ev("window.__vt(null, 0, 0)"); await pg.wait_for_timeout(300)
        await ev(f"window.__vt({ECR}, 0.2, 8)"); await pg.wait_for_timeout(400)
        rapport(await ev("window.__s.win") == "video", "on se detourne puis on s'approche de nouveau de l'ecran : la priorite collee de la radio est effacee (1.12.25)", await ev("window.__s.win"))
        await ev("window.__vt(null, 0, 0)"); await pg.wait_for_timeout(300)
        rapport(await hid("soundVideoInfo"), "ecran parti : la ligne Video disparait")

        print("--- 4. muet : bouton et touche N")
        await ev("window.__vt(null, 0, 0)"); await pg.wait_for_timeout(200)
        
        try:
            await pg.wait_for_function("window.__r.playing()", timeout=15000)
        except Exception:
            pass
        okr = await ev("window.__r.playing()")
        await pg.keyboard.press("n"); await pg.wait_for_timeout(500)
        rapport(await ev("document.getElementById('soundMute').innerHTML") != await ev("document.getElementById('soundVolBtn').innerHTML"), "l'icone du bouton muet n'est pas celle du volume")
        rapport(okr and await ev("window.__s.mute") and not await ev("window.__r.playing()"), "touche N : la radio s'arrete (muet)", (okr, await ev("window.__s.mute")))
        rapport(await chk("visRadio") and await ev("document.getElementById('soundMute').getAttribute('aria-pressed')") == "true", "les cases ne changent pas ; le bouton est enfonce")
        await ev(f"window.__vt({ECR}, 0.99, 0.1)"); await ev(f"window.__va({ECR})"); await pg.wait_for_timeout(300)
        rapport(await ev("window.__vs()") == 0, "muet : le son video est a 0")
        await ev("document.getElementById('soundMute').click()"); await pg.wait_for_timeout(400)
        rapport(not await ev("window.__s.mute") and await ev("window.__vs()") > 0, "bouton : le son revient (video)", await ev("window.__vs()"))
        await ev("window.__vt(null, 0, 0)"); await pg.wait_for_timeout(300)
        try:
            await pg.wait_for_function("window.__r.playing()", timeout=15000)
        except Exception:
            pass
        rapport(await ev("window.__r.playing()"), "la radio reprend")

        print("--- 5. fenetre flottante : seule une page YouTube coupe les sources")
        await ev("window.__vt(null, 0, 0)"); await pg.wait_for_timeout(400)
        rapport(await ev("window.__r.playing()"), "radio qui joue avant la fenetre")
        await ev("window.__fo({ id: 'o' }, new URL('https://example.org/'), 'click', 'Autre page')"); await pg.wait_for_timeout(700)
        rapport(await ev("window.__r.playing()") and await ev("document.querySelector('#frameWin iframe') !== null"), "page autre que YouTube : la radio continue")
        await ev("window.__fo({ id: 'y' }, new URL('https://www.youtube.com/watch?v=dQw4w9WgXcQ'), 'click', 'YouTube')"); await pg.wait_for_timeout(700)
        rapport(not await ev("window.__r.playing()") and "YouTube" in await ev("document.getElementById('radioInfo').textContent"), "fenetre YouTube ouverte : la radio s'arrete tout de suite (ligne « son coupe »)", await ev("document.getElementById('radioInfo').textContent"))
        rapport(await ev("(() => { document.querySelector('#frameWin iframe').focus(); return document.activeElement.tagName; })()") == "IFRAME", "essai : le lecteur prend le focus clavier")
        await pg.wait_for_timeout(1500)
        rapport(await ev("document.activeElement.tagName") != "IFRAME", "la page reprend le focus clavier (E et la marche continuent de marcher)", await ev("document.activeElement.tagName"))
        await ev(f"window.__vt({ECR}, 0.99, 0.1)"); await ev(f"window.__va({ECR})")
        rapport(await ev("window.__vs()") > 0, "clic sur un ecran = geste : le son video revient malgre la fenetre YouTube")
        await ev("window.__vt(null, 0, 0)"); await pg.wait_for_timeout(300)
        await ev("window.__fo({ id: 'y' }, new URL('https://www.youtube.com/watch?v=dQw4w9WgXcQ'), 'click', 'YouTube')"); await pg.wait_for_timeout(500)
        rapport(not await ev("window.__r.playing()"), "fenetre YouTube rouverte : radio coupee de nouveau")
        await ev("document.getElementById('visRadio').checked = false; document.getElementById('visRadio').onchange()"); await pg.wait_for_timeout(300)
        await ev("window.tick('visRadio')")
        try:
            await pg.wait_for_function("window.__r.playing()", timeout=15000)
        except Exception:
            pass
        rapport(await ev("window.__r.playing()"), "decocher puis recocher la radio pendant la fenetre YouTube : le son revient (cocher = geste)")
        src = await ev("document.querySelector('#frameWin iframe').src")
        rapport("youtube-nocookie.com/embed/" in src and "enablejsapi" not in src and "autoplay=1" in src, "adresse du lecteur YouTube : integre, autoplay, sans enablejsapi", src)
        await ev("document.getElementById('frameWin').querySelector('button:last-child').click()"); await pg.wait_for_timeout(300)
        rapport(await ev("document.getElementById('frameWin')") is None, "fenetre fermee")
        await ev("window.__vt(null, 0, 0)"); await pg.wait_for_timeout(300)

        print("--- 3. cases : une seule source a la fois")
        await ev(f"window.__vt({ECR}, 0.2, 8)"); await pg.wait_for_timeout(300)
        await ev("window.tick('visVideo')"); await pg.wait_for_timeout(300)
        rapport(await chk("visVideo") and not await chk("visRadio") and not await chk("soundRadioCk") and not await chk("stateRadioCk") and not await chk("visMusic"), "cocher Videos (Reglages) decoche radio et musique, partout")
        rapport(await ev("window.__s.win") == "video", "seule la video est cochee : elle parle", await ev("window.__s.win"))
        await ev("window.tick('soundRadioCk')"); await pg.wait_for_timeout(300)
        rapport(await chk("visRadio") and not await chk("visVideo") and not await chk("soundVideoCk") and await ev("window.__s.win") == "radio", "cocher Radio (fenetre Son) decoche la video : la radio parle", await ev("window.__s.win"))

        rapport(not errs, "aucune erreur JavaScript", errs)
        await br.close()
    srv.shutdown()


asyncio.run(main())
print("\nRESULTAT : " + ("tout est passe" if not echecs else f"{echecs} echec(s)"))
sys.exit(1 if echecs else 0)
