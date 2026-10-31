#!/usr/bin/env python3
"""Cache du navigateur, cas du fichier PLUS VIEUX : image, legende (.txt) et .glb (page modulaire) remplaces par un fichier dont la date est ANTERIEURE a celle
que le navigateur a vue (dossier precedent remis en place) ; fichier inchange non retelecharge ; serveur sans Last-Modified (repli sur le telechargement complet).
Serveur http.server dans le processus (comptage des requetes GET et HEAD). Prerequis : pip install playwright ; python build.py avant.
Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/image_cache_vieux.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, functools, http.server, json, os, pathlib, struct, subprocess, sys, tempfile, threading, time, zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_vieux_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def date(path, jours):
    t = time.time() - jours * 86400
    os.utime(path, (t, t))


def sol_glb(path, r=20):
    v = [(-r, 0, -r), (r, 0, -r), (r, 0, r), (-r, 0, r)]
    pos = b"".join(struct.pack("<3f", *p) for p in v)
    idx = struct.pack("<6H", 0, 1, 2, 0, 2, 3)
    blob = pos + idx + bytes(-(len(pos) + 12) % 4)
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos)}, {"buffer": 0, "byteOffset": len(pos), "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-r, 0, -r], "max": [r, 0, r]}, {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}], "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * (-len(js) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def png(path, rgb):
    def ch(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(b"\x00" + bytes(rgb))) + ch(b"IEND", b""))


def zone(i, cible):
    return {"id": i, "type": "image", "label": i, "x": 0, "y": 2, "z": 0, "yaw": 0, "shape": "ring", "trigger": "click", "radius": 2, "w": 1.2, "h": 0, "target": cible, "spawn": "", "confirm": False, "private": False, "showName": False}


JOURNAL = []   # (methode, chemin) de chaque requete recue par les serveurs ci-dessous


class Normal(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self): JOURNAL.append(("GET", self.path)); super().do_GET()
    def do_HEAD(self): JOURNAL.append(("HEAD", self.path)); super().do_HEAD()


class SansDate(Normal):
    """serveur sans Last-Modified ni ETag : le navigateur n'a aucune empreinte, la page doit tout retelecharger"""
    def send_header(self, k, v):
        if k.lower() not in ("last-modified", "etag"):
            super().send_header(k, v)


def serveur(classe, dossier):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(classe, directory=str(dossier)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


PIX = """() => { let r = null; window.__v.scene.traverse(n => { if (n.isMesh && !(n.userData && n.userData.caption) && n.material && n.material.map && n.material.map.image && n.material.map.image.width) { const c = document.createElement('canvas'); c.width = c.height = 1; const x = c.getContext('2d'); x.drawImage(n.material.map.image, 0, 0); r = Array.from(x.getImageData(0, 0, 1, 1).data).slice(0, 3); } }); return r; }"""
LEGS = """() => { const o = []; window.__v.scene.traverse(n => { if (n.userData && n.userData.caption) o.push(n.userData.caption); }); return o.sort(); }"""
MAXX = """() => { let m = -1e9; window.__v.model.traverse(n => { if (n.isMesh) { n.geometry.computeBoundingBox(); m = Math.max(m, n.geometry.boundingBox.max.x); } }); return Math.round(m); }"""


def fabrique(site, nom, zones, *opt):
    zj = tmp / (nom + ".z.json"); zj.write_text(json.dumps(zones), encoding="utf-8")
    out = site / (nom + ".html")
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--no-sea", "--zones", str(zj), *opt, *vend], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation {nom}\n{r.stdout}{r.stderr}")
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    sol_glb(tmp / "sol.glb")
    m = site / "medias"
    png(m / "1.png", (255, 0, 0)); (m / "1.txt").write_text("Avant\n", encoding="utf-8")
    for f in (m / "1.png", m / "1.txt"): date(f, 10)
    fabrique(site, "p", [zone("a", "1")])
    fabrique(site, "q", [], "--modular")
    date(site / "q.glb", 10)
    srv1, port1 = serveur(Normal, site)
    srv2, port2 = serveur(SansDate, site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            errs = []
            attente = "document.getElementById('msg') === null && window.__v && window.__v.model"

            async def charge(pg, url=None):
                if url: await pg.goto(url)
                else: await pg.reload()
                await pg.wait_for_function(attente, timeout=60000); await pg.wait_for_timeout(3500)

            def nouvelle():
                return br.new_page(viewport={"width": 900, "height": 600})

            # 1. serveur normal : ouverture, fichier inchange, puis remplacement par des fichiers PLUS VIEUX
            pg = await nouvelle(); pg.on("pageerror", lambda e: errs.append(str(e)))
            await charge(pg, f"http://127.0.0.1:{port1}/p.html")
            pix, lg = await pg.evaluate(PIX), await pg.evaluate(LEGS)
            rapport(pix == [255, 0, 0] and lg == ["Avant"], "1re ouverture : image rouge et legende « Avant »", (pix, lg))
            JOURNAL.clear()
            await charge(pg)
            gets = [r for r in JOURNAL if r[0] == "GET" and r[1].startswith("/medias/1.")]
            heads = [r for r in JOURNAL if r[0] == "HEAD" and r[1].startswith("/medias/1.")]
            rapport(not gets and len(heads) >= 2, "fichiers inchanges : l'image et la legende ne sont pas retelechargees (HEAD seulement)", (gets, heads))
            png(m / "1.png", (0, 0, 255)); (m / "1.txt").write_text("Apres\n", encoding="utf-8")
            for f in (m / "1.png", m / "1.txt"): date(f, 60)      # PLUS VIEUX que la copie vue par le navigateur (10 jours)
            await charge(pg)
            pix, lg = await pg.evaluate(PIX), await pg.evaluate(LEGS)
            rapport(pix == [0, 0, 255], "image remplacee par un fichier plus vieux : la page montre la nouvelle (bleue)", pix)
            rapport(lg == ["Apres"], "legende remplacee par un fichier plus vieux : la page montre « Apres »", lg)
            await pg.close()

            pg = await nouvelle(); pg.on("pageerror", lambda e: errs.append(str(e)))
            await charge(pg, f"http://127.0.0.1:{port1}/q.html")
            mx = await pg.evaluate(MAXX)
            rapport(mx == 20, "page modulaire : 1re ouverture, sol de 20 m de demi-cote", mx)
            sol_glb(site / "q.glb", 30); date(site / "q.glb", 60)
            await charge(pg)
            mx = await pg.evaluate(MAXX)
            rapport(mx == 30, ".glb remplace par un fichier plus vieux : la page modulaire montre le nouveau sol (30 m)", mx)
            await pg.close()

            # 2. serveur sans Last-Modified : repli sur le telechargement complet, toujours a jour
            png(m / "1.png", (255, 0, 0)); (m / "1.txt").write_text("Avant\n", encoding="utf-8")
            for f in (m / "1.png", m / "1.txt"): date(f, 10)
            pg = await nouvelle(); pg.on("pageerror", lambda e: errs.append(str(e)))
            await charge(pg, f"http://127.0.0.1:{port2}/p.html")
            pix, lg = await pg.evaluate(PIX), await pg.evaluate(LEGS)
            rapport(pix == [255, 0, 0] and lg == ["Avant"], "serveur sans Last-Modified : 1re ouverture, image rouge et legende « Avant »", (pix, lg))
            png(m / "1.png", (0, 255, 0)); (m / "1.txt").write_text("Apres sans date\n", encoding="utf-8")
            for f in (m / "1.png", m / "1.txt"): date(f, 90)
            await charge(pg)
            pix, lg = await pg.evaluate(PIX), await pg.evaluate(LEGS)
            rapport(pix == [0, 255, 0] and lg == ["Apres sans date"], "serveur sans Last-Modified : fichiers plus vieux, la page montre quand meme les nouveaux", (pix, lg))
            await pg.close()
            rapport(not errs, "aucune erreur JavaScript", errs)
            await br.close()
    finally:
        srv1.shutdown(); srv2.shutdown()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
