#!/usr/bin/env python3
"""Zone « image » : apercu depuis le dossier de la region (editeur, Chromium sans tete).

Le vrai selecteur de dossier ne se pilote pas ici : showDirectoryPicker est remplace par un dossier OPFS (meme API : getFileHandle, queryPermission...).
Verifie : sans dossier, l'image n'est cherchee que a cote de la page ; un dossier qui ne contient pas le .glb est refuse (message, rien ne change) ;
le bon dossier fait lire dans le dossier les images relatives (sous-dossier compris), une image absente du dossier garde l'adresse habituelle,
`..` est refuse ; apres rechargement, le dossier memorise est reutilise sans rien redemander.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/image_dossier.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time, zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_imgdir_"))
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def png(w, h, rgb=(200, 20, 20)):
    brut = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    def ch(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(brut)) + ch(b"IEND", b"")


def mur_glb(path):
    """sol de 40 x 40 m (normale vers le haut) un mur de 20 x 6 m en z = -5 (normale vers +z) et un mur en x = 8 (normale vers -x)"""
    v = [(-20, 0, -20), (20, 0, -20), (20, 0, 20), (-20, 0, 20), (-10, 0, -5), (10, 0, -5), (10, 6, -5), (-10, 6, -5), (8, 0, -10), (8, 0, 10), (8, 6, 10), (8, 6, -10)]
    pos = b"".join(struct.pack("<3f", *p) for p in v)
    idx = struct.pack("<18H", 0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7, 8, 9, 10, 8, 10, 11)
    blob = pos + idx
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos)}, {"buffer": 0, "byteOffset": len(pos), "byteLength": len(idx)}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 12, "type": "VEC3", "min": [-20, 0, -20], "max": [20, 6, 20]},
                       {"bufferView": 1, "componentType": 5123, "count": 18, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "salle"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * (-len(js) % 4)
    blob += bytes(-len(blob) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js
                     + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


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



PREP = """async ([glb, a, b]) => {
  const root = await navigator.storage.getDirectory();
  for (const n of ['region', 'vide']) { try { await root.removeEntry(n, { recursive: true }); } catch (e) {} }
  const reg = await root.getDirectoryHandle('region', { create: true });
  await root.getDirectoryHandle('vide', { create: true });
  const put = async (d, name, bytes) => { const w = await (await d.getFileHandle(name, { create: true })).createWritable(); await w.write(new Uint8Array(bytes)); await w.close(); };
  await put(reg, 'salle.glb', glb); await put(reg, 'dossier-only.png', a);
  const sub = await reg.getDirectoryHandle('sous', { create: true }); await put(sub, 'dossier-only2.png', b);
}"""
CHOISIR = """async (nom) => { const root = await navigator.storage.getDirectory(); window.showDirectoryPicker = async () => root.getDirectoryHandle(nom); }"""
CLIQUE = """() => { const b = [...document.querySelectorAll('#zoneList button')].find(x => x.textContent.includes('Choisir le dossier de la région')); if (!b) return false; b.click(); return true; }"""
LARGEURS = """() => { const o = {}; window.__viewer.scene.traverse(m => { if (m.isMesh && m.parent && m.parent.userData && m.parent.userData.zoneId) { const i = m.material.map && m.material.map.image; o[m.parent.userData.zoneId] = i && i.width ? i.width : 0; } }); return o; }"""


async def ouvrir(ctx, port):
    pg = await ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(f"http://127.0.0.1:{port}/glb-viewer.html")
    await pg.wait_for_function("window.__viewer", timeout=60000)
    await pg.set_input_files("#fGlb", str(tmp / "salle.glb"))
    await pg.wait_for_function("window.__viewer.model", timeout=60000)
    await pg.set_input_files("#fZones", str(tmp / "z.json"))
    await pg.wait_for_function("window.__viewer.getZones().length === 4", timeout=10000)
    return pg, errs


async def attendre(pg, cond, delai=8000):
    try:
        await pg.wait_for_function(cond, timeout=delai); return True
    except Exception:
        return False


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    mur_glb(tmp / "salle.glb")
    (site / "tableau.png").write_bytes(png(8, 4))
    shutil.copy(DIST / "glb-viewer.html", site / "glb-viewer.html")
    shutil.copytree(DIST / "lib", site / "lib") if (DIST / "lib").exists() else None
    base = {"type": "image", "y": 18, "z": -4.98, "yaw": 0, "w": 1.2, "h": 0}
    zs = [dict(base, id="tab", target="tableau.png", x=0), dict(base, id="dos", target="dossier-only.png", x=-4),
          dict(base, id="sous", target="sous/dossier-only2.png", x=4), dict(base, id="hors", target="sous/../dossier-only.png", x=7)]
    (tmp / "z.json").write_text(json.dumps(zs), encoding="utf-8")
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            ctx = await br.new_context(locale="fr-FR", viewport={"width": 1000, "height": 700})   # meme contexte : OPFS et IndexedDB survivent au rechargement
            pg, errs = await ouvrir(ctx, port)
            await pg.evaluate(PREP, [list((tmp / "salle.glb").read_bytes()), list(png(16, 2)), list(png(6, 3))])
            await attendre(pg, "window.__viewer.scene.children.length > 0")
            await pg.wait_for_timeout(1500)
            l = await pg.evaluate(LARGEURS)
            rapport(l.get("tab") == 8 and l.get("dos") != 16 and l.get("sous") != 6, "sans dossier : seule l'image a cote de la page est lue", l)
            # dossier qui ne contient pas le .glb : refuse
            await pg.evaluate(CHOISIR, "vide")
            rapport(await pg.evaluate(CLIQUE), "le bouton est present sous le champ Image")
            await pg.wait_for_timeout(800)
            stat = await pg.evaluate("document.getElementById('stat').textContent")
            l = await pg.evaluate(LARGEURS)
            rapport("ne contient pas salle.glb" in stat and l.get("dos") != 16, "mauvais dossier : refuse, message, rien ne change", (stat, l))
            # bon dossier
            await pg.evaluate(CHOISIR, "region")
            await pg.evaluate(CLIQUE)
            ok = await attendre(pg, "(() => { const o = {}; window.__viewer.scene.traverse(m => { if (m.isMesh && m.parent && m.parent.userData && m.parent.userData.zoneId) { const i = m.material.map && m.material.map.image; o[m.parent.userData.zoneId] = i && i.width ? i.width : 0; } }); return o.dos === 16 && o.sous === 6; })()")
            l = await pg.evaluate(LARGEURS)
            rapport(ok and l.get("tab") == 8, "bon dossier : images relatives lues dans le dossier (sous-dossier compris), l'autre garde l'adresse habituelle", l)
            rapport(l.get("hors") != 16, "cible avec .. : jamais lue dans le dossier", l.get("hors"))
            stat = await pg.evaluate("document.getElementById('stat').textContent")
            rapport("region" in stat and "lecture seule" in stat, "message : dossier choisi, lecture seule", stat)
            txt = await pg.evaluate("[...document.querySelectorAll('#zoneList small')].map(s => s.textContent)")
            rapport(any("Lue dans le dossier « region » : dossier-only.png" in t for t in txt), "editeur : la ligne dit que l'image est lue dans le dossier", txt)
            rapport(any("Absente du dossier « region »" in t and "tableau.png" in t for t in txt), "editeur : image absente du dossier, adresse habituelle indiquee", txt)
            rapport(not errs, "aucune erreur JavaScript", errs)
            await pg.close()
            # rechargement : le dossier memorise (IndexedDB) est reutilise sans clic
            pg, errs = await ouvrir(ctx, port)
            ok = await attendre(pg, "(() => { const o = {}; window.__viewer.scene.traverse(m => { if (m.isMesh && m.parent && m.parent.userData && m.parent.userData.zoneId) { const i = m.material.map && m.material.map.image; o[m.parent.userData.zoneId] = i && i.width ? i.width : 0; } }); return o.dos === 16 && o.sous === 6; })()", 12000)
            rapport(ok, "apres rechargement : dossier memorise reutilise sans rien demander", await pg.evaluate(LARGEURS))
            rapport(not errs, "rechargement : aucune erreur JavaScript", errs)
            await pg.close(); await br.close()
    finally:
        proc.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
