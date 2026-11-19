#!/usr/bin/env python3
"""Test 1.12.26 : pochette (poster) et lien (link) des zones radio (cast) et musique (audio), montres dans la fenetre Son.
Hors navigateur : clean_zones (Python) garde poster et link sur audio et cast seulement, nettoyes (caracteres de controle, 600 caracteres), cles absentes si vides.
Dans Chromium : la pochette de la zone qui parle s'affiche (radio, puis musique), un clic l'ouvre sur le lien, sans lien elle n'est pas cliquable,
image introuvable : rien, zone sans pochette : rien ; cleanZone (JavaScript) donne les memes cles que clean_zones ; viewer : champs Pochette et Lien.
Prerequis : pip install playwright websockets && playwright install chromium ; python build.py avant. Variables : THREE_DIR, CHROMIUM.
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, functools, http.server, json, math, os, pathlib, runpy, struct, subprocess, sys, tempfile, threading, zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_pochette_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def sol_glb(path):
    pos = struct.pack("<12f", -150, 0, -150, 150, 0, -150, 150, 0, 150, -150, 0, 150)
    blob = pos + struct.pack("<6H", 0, 2, 1, 0, 3, 2) + b"\0\0"
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-150, 0, -150], "max": [150, 0, 150]},
                       {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * ((4 - len(js) % 4) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob))
                     + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def wav(path, secondes=20):
    n = 8000 * secondes
    data = bytes(int(128 + 100 * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(n))
    path.write_bytes(b"RIFF" + struct.pack("<I", 36 + n) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 8000, 8000, 1, 8) + b"data" + struct.pack("<I", n) + data)


def png(path, w=200, h=120):
    ligne = b"\0" + bytes([200, 60, 60]) * w
    brut = ligne * h
    def bloc(t, d):
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + bloc(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + bloc(b"IDAT", zlib.compress(brut)) + bloc(b"IEND", b""))


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


class Serveur(http.server.ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        if not isinstance(sys.exc_info()[1], (ConnectionError, TimeoutError)):
            super().handle_error(request, client_address)


def serveur(dossier):
    srv = Serveur(("127.0.0.1", 0), functools.partial(Handler, directory=str(dossier)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


print("--- 1. clean_zones (Python)")
G = runpy.run_path(str(DIST / "glb2html.py"))
base = {"x": 1, "y": 2, "z": 3}
zs = [dict(base, id="r1", type="cast", streams=[["A", "https://h/f"]], poster="  cover.png ", link="https://h/album"),
      dict(base, id="m1", type="audio", folder="audio", poster="a\x01b.jpg", link="hop://h/r/1/2/3"),
      dict(base, id="r2", type="cast", streams=[["A", "https://h/f"]]),
      dict(base, id="r3", type="cast", streams=[["A", "https://h/f"]], poster="   ", link=""),
      dict(base, id="u1", type="url", target="https://h/", poster="x.png", link="https://h/y"),
      dict(base, id="p1", type="portal", poster="x.png", link="https://h/y"),
      dict(base, id="v1", type="video", target="v.mp4", poster="x.png", link="https://h/y"),
      dict(base, id="long", type="audio", folder="a", poster="p" * 700, link="l" * 700)]
out = {z["id"]: z for z in G["clean_zones"](zs, "private")}
rapport(out["r1"].get("poster") == "cover.png" and out["r1"].get("link") == "https://h/album", "radio : poster nettoye (espaces) et link gardes", out["r1"])
rapport(out["m1"].get("poster") == "ab.jpg" and out["m1"].get("link") == "hop://h/r/1/2/3", "musique : caracteres de controle retires, lien hop gardé", out["m1"])
rapport("poster" not in out["r2"] and "link" not in out["r2"] and "poster" not in out["r3"] and "link" not in out["r3"], "vides ou absents : les cles ne sont pas ecrites")
rapport(all("poster" not in out[i] for i in ("u1", "p1", "v1")) and "link" not in out["p1"] and "link" not in out["v1"] and out["u1"].get("link") is None, "lien, portail, video : ni poster ni link", {i: out[i] for i in ("u1", "p1", "v1")})
rapport(len(out["long"]["poster"]) == 600 and len(out["long"]["link"]) == 600, "600 caracteres au plus")
rapport(G["clean_zones"](list(out.values()), "private") == list(out.values()), "idempotent")


def page(port):
    u = lambda n: f"http://127.0.0.1:{port}/{n}"
    zones = [{"id": "radio", "type": "cast", "label": "Zone radio", "x": 0, "y": 15, "z": 0, "radius": 30, "streams": [["Un", u("flux.wav")]], "poster": "cover.png", "link": "https://example.org/album"},
             {"id": "radio2", "type": "cast", "label": "Radio sans image", "x": 100, "y": 15, "z": 0, "radius": 30, "streams": [["Un", u("flux.wav")]], "poster": "absente.png", "link": "https://example.org/x"},
             {"id": "musique", "type": "audio", "label": "Zone musique", "x": -100, "y": 15, "z": 0, "radius": 30, "tracks": ["piste.wav"], "poster": "cover.png"},
             {"id": "radio3", "type": "cast", "label": "Radio nue", "x": 0, "y": 15, "z": 100, "radius": 30, "streams": [["Un", u("flux.wav")]]},
             {"id": "radio4", "type": "cast", "label": "Radio lien mauvais", "x": 0, "y": 15, "z": -100, "radius": 30, "streams": [["Un", u("flux.wav")]], "poster": "cover.png", "link": "javascript:alert(1)"}]
    (tmp / "z.json").write_text(json.dumps(zones), encoding="utf-8")
    out = tmp / "p.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--zones", str(tmp / "z.json"), "--no-sea", *vend], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    t = out.read_text(encoding="utf-8")
    for a, b in (("const viewer = createViewer(", "const viewer = window.__v = createViewer("), ("const SRC = {", "const SRC = window.__s = {")):
        if a not in t:
            sys.exit(f"[ECHEC] marqueur absent de la page : {a}")
        t = t.replace(a, b, 1)
    out.write_text(t, encoding="utf-8")
    return out


async def main():
    from playwright.async_api import async_playwright
    sol_glb(tmp / "sol.glb"); wav(tmp / "flux.wav"); wav(tmp / "piste.wav"); png(tmp / "cover.png")
    srv = serveur(tmp)
    page(srv.server_address[1])
    async with async_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
        br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
        ctx = await br.new_context(locale="fr-FR", viewport={"width": 1000, "height": 700})
        pg = await ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/p.html")
        await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
        ev = pg.evaluate
        await ev("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
        await ev("window.__o = []; window.open = (...a) => { window.__o.push(a); return null; }; 0")   # sans « ; 0 » evaluate appellerait la fonction renvoyee par l'expression
        etat = lambda: ev("(() => { const b = document.getElementById('soundPoster'), i = b.querySelector('img'); return { hidden: b.hidden, src: i.getAttribute('src') || '', w: i.naturalWidth, role: b.getAttribute('role'), tab: b.getAttribute('tabindex'), title: b.title, alt: i.alt }; })()")
        async def aller(x, z, attendre=True):
            await ev(f"window.__v.teleportTo([{x}, 15, {z}], 0)")
            await pg.wait_for_timeout(700)
        await ev("window.__v.walkStart({ pos: [0, 15, 250], yaw: 0 })"); await pg.wait_for_timeout(400)

        print("--- 2. la pochette suit la zone qui parle")
        e = await etat()
        rapport(e["hidden"] and e["src"] == "", "hors de toute zone : pas de pochette", e)
        await aller(0, 10)
        try:
            await pg.wait_for_function("document.getElementById('soundPoster').querySelector('img').naturalWidth > 0", timeout=8000)
        except Exception:
            pass
        e = await etat()
        rapport(await ev("window.__s.win") == "radio", "radio a portee : elle parle", await ev("window.__s.win"))
        rapport(not e["hidden"] and e["src"].endswith("/cover.png") and e["w"] == 200, "radio avec pochette : image montree", e)
        rapport(e["role"] == "button" and e["tab"] == "0" and "Zone radio" in e["title"] and "Zone radio" in e["alt"], "avec un lien : bouton accessible, titre et texte alternatif", e)
        await ev("document.getElementById('soundPoster').click()"); await pg.wait_for_timeout(200)
        o = await ev("window.__o")
        rapport(len(o) == 1 and o[0][0] == "https://example.org/album" and o[0][1] == "_blank" and "noopener" in o[0][2], "clic : le lien s'ouvre dans un nouvel onglet (noopener)", o)
        await ev("document.getElementById('soundPoster').dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))"); await pg.wait_for_timeout(200)
        rapport(len(await ev("window.__o")) == 2, "Entree sur la pochette : meme action")

        await aller(100, 10)
        await pg.wait_for_timeout(500)
        e = await etat()
        rapport(await ev("window.__s.win") == "radio" and e["hidden"], "image introuvable : rien n'est montre", e)

        await aller(-100, 10)
        try:
            await pg.wait_for_function("document.getElementById('soundPoster').querySelector('img').naturalWidth > 0", timeout=8000)
        except Exception:
            pass
        e = await etat()
        n0 = len(await ev("window.__o"))
        rapport(await ev("window.__s.win") == "music" and not e["hidden"] and e["src"].endswith("/cover.png"), "musique a portee : sa pochette est montree", (await ev("window.__s.win"), e))
        rapport(e["role"] is None and e["tab"] is None and e["title"] == "", "sans lien : ni bouton ni titre", e)
        await ev("document.getElementById('soundPoster').click()"); await pg.wait_for_timeout(200)
        rapport(len(await ev("window.__o")) == n0, "sans lien : le clic n'ouvre rien")

        await aller(0, 110)
        e = await etat()
        rapport(await ev("window.__s.win") == "radio" and e["hidden"] and e["src"] == "", "radio sans pochette : rien", e)

        await aller(0, -90)
        try:
            await pg.wait_for_function("document.getElementById('soundPoster').querySelector('img').naturalWidth > 0", timeout=8000)
        except Exception:
            pass
        e = await etat()
        n0 = len(await ev("window.__o"))
        await ev("document.getElementById('soundPoster').click()"); await pg.wait_for_timeout(200)
        rapport(not e["hidden"] and e["role"] is None and len(await ev("window.__o")) == n0, "lien non permis (javascript:) : pochette montree mais rien ne s'ouvre", (e, await ev("window.__o")))

        await aller(0, 250)
        e = await etat()
        rapport(e["hidden"] and e["src"] == "", "on s'eloigne de tout : la pochette disparait", e)

        print("--- 3. cleanZone (JavaScript) = clean_zones (Python)")
        await pg.evaluate("(l) => window.__v.setZones(l)", zs)
        js = {z["id"]: z for z in await ev("window.__v.getZones()")}
        cles = lambda z: {k: z[k] for k in ("poster", "link") if k in z}
        rapport(all(cles(js[i]) == cles(out[i]) for i in out), "memes poster et link dans les deux nettoyeurs", {i: (cles(js[i]), cles(out[i])) for i in out if cles(js[i]) != cles(out[i])})
        rapport(not errs, "aucune erreur JavaScript", errs)
        await br.close()
    srv.shutdown()
    print("ECHECS : %d" % echecs if echecs else "TOUT PASSE")
    return echecs

if __name__ == "__main__":
    sys.exit(1 if asyncio.run(main()) else 0)
