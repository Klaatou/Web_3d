#!/usr/bin/env python3
"""Zone « model » : apercu depuis le dossier de la region, dans l'editeur du viewer (1.13.12) (Chromium sans tete).

Le vrai selecteur de dossier ne se pilote pas ici : showDirectoryPicker est remplace par un dossier OPFS (meme API : getFileHandle, queryPermission...).
Verifie : sans dossier, un modele n'est lu qu'a cote de la page (un fichier absent n'affiche rien, sans erreur) ; un dossier qui ne contient pas le .glb
est refuse ; le bon dossier fait lire les modeles dans le dossier (sous-dossier compris) et ce fichier PASSE AVANT celui qui est a cote de la page ;
un modele absent du dossier garde l'adresse habituelle ; apres rechargement, le dossier memorise est reutilise sans rien demander ; le bouton est
dans la fiche d'un modele.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/modele_dossier.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_mdldir_"))
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def glb(path, nodes):
    """sol de 40 x 40 m (normale vers le haut) ; avec nodes > 1 : un petit triangle repete `nodes` fois (un objet par noeud = un mesh par noeud)"""
    if nodes == 0:
        v = [(-20, 0, -20), (20, 0, -20), (20, 0, 20), (-20, 0, 20)]; idx = struct.pack("<6H", 0, 2, 1, 0, 3, 2); n = 6
    else:
        v = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]; idx = struct.pack("<3H", 0, 1, 2); n = 3
    pos = b"".join(struct.pack("<3f", *p) for p in v)
    blob = pos + idx
    mn, mx = [min(p[i] for p in v) for i in range(3)], [max(p[i] for p in v) for i in range(3)]
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos)}, {"buffer": 0, "byteOffset": len(pos), "byteLength": len(idx)}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": len(v), "type": "VEC3", "min": mn, "max": mx},
                       {"bufferView": 1, "componentType": 5123, "count": n, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}]}
    k = max(1, nodes)
    g["nodes"] = [{"mesh": 0, "name": "o%d" % i, "translation": [i * 2, 0, 0]} for i in range(k)]
    g["scenes"] = [{"nodes": list(range(k))}]; g["scene"] = 0
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


PREP = """async ([salle, deux, un]) => {
  const root = await navigator.storage.getDirectory();
  for (const n of ['region', 'vide']) { try { await root.removeEntry(n, { recursive: true }); } catch (e) {} }
  const reg = await root.getDirectoryHandle('region', { create: true });
  await root.getDirectoryHandle('vide', { create: true });
  const put = async (d, name, bytes) => { const w = await (await d.getFileHandle(name, { create: true })).createWritable(); await w.write(new Uint8Array(bytes)); await w.close(); };
  await put(reg, 'salle.glb', salle); await put(reg, 'poste.glb', deux);
  const sub = await reg.getDirectoryHandle('sous', { create: true }); await put(sub, 'boite.glb', un);
}"""
CHOISIR = """async (nom) => { const root = await navigator.storage.getDirectory(); window.showDirectoryPicker = async () => root.getDirectoryHandle(nom); }"""
CLIQUE = """() => { const b = [...document.querySelectorAll('#zoneList button')].find(x => x.textContent.includes('Choisir le dossier de la région')); if (!b) return false; b.click(); return true; }"""
LIRE = """() => { const out = {}; window.__viewer.scene.traverse(o => { if (o.userData && o.userData.zoneId && o.children.length) {
    let n = 0; o.children[0].traverse(q => { if (q.isMesh) n++; }); out[o.userData.zoneId] = n; } }); return out; }"""
EGAUX = "(a) => { const o = (%s)(); return Object.keys(a).every(k => o[k] === a[k]); }" % LIRE


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


async def attendre(pg, attendu, delai=8000):
    try:
        await pg.wait_for_function(EGAUX, arg=attendu, timeout=delai); return True
    except Exception:
        return False


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    glb(tmp / "salle.glb", 0); glb(tmp / "deux.glb", 2); glb(tmp / "un.glb", 1)
    shutil.copy(tmp / "un.glb", site / "poste.glb")        # a cote de la page : 1 objet ; dans le dossier de la region : 2 objets
    shutil.copy(tmp / "un.glb", site / "web.glb")          # seulement a cote de la page
    shutil.copy(DIST / "glb-viewer.html", site / "glb-viewer.html")
    shutil.copytree(DIST / "lib", site / "lib") if (DIST / "lib").exists() else None
    zs = [{"id": "poste", "model": "poste.glb", "x": -6, "y": 0, "z": -3}, {"id": "sousm", "model": "sous/boite.glb", "x": -2, "y": 0, "z": -3},
          {"id": "web", "model": "web.glb", "x": 2, "y": 0, "z": -3}, {"id": "nulle", "model": "absent.glb", "x": 6, "y": 0, "z": -3}]
    (tmp / "z.json").write_text(json.dumps(zs), encoding="utf-8")
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            ctx = await br.new_context(locale="fr-FR", viewport={"width": 1000, "height": 700})   # meme contexte : OPFS et IndexedDB survivent au rechargement
            pg, errs = await ouvrir(ctx, port)
            await pg.evaluate(PREP, [list((tmp / "salle.glb").read_bytes()), list((tmp / "deux.glb").read_bytes()), list((tmp / "un.glb").read_bytes())])
            ok = await attendre(pg, {"poste": 1, "web": 1})
            await pg.wait_for_timeout(800)
            l = await pg.evaluate(LIRE)
            rapport(ok and l.get("poste") == 1 and l.get("web") == 1 and l.get("sousm") == 0 and l.get("nulle") == 0,
                    "sans dossier : seuls les modeles a cote de la page sont lus, un fichier absent n'affiche rien", l)
            # la fiche d'un modele porte le bouton
            rapport(await pg.evaluate("[...document.querySelectorAll('#zoneList details')][0].querySelectorAll('button').length >= 1 && !![...document.querySelectorAll('#zoneList details')][0].textContent.includes('Choisir le dossier de la région')"),
                    "la fiche d'un modele a le bouton « Choisir le dossier de la région »")
            # dossier qui ne contient pas le .glb de la region : refuse
            await pg.evaluate(CHOISIR, "vide")
            rapport(await pg.evaluate(CLIQUE), "le bouton est cliquable")
            await pg.wait_for_timeout(800)
            stat = await pg.evaluate("document.getElementById('stat').textContent")
            l = await pg.evaluate(LIRE)
            rapport("ne contient pas salle.glb" in stat and l.get("poste") == 1 and l.get("sousm") == 0, "mauvais dossier : refuse, message, rien ne change", (stat, l))
            # bon dossier : le fichier du dossier passe avant celui de la page (2 objets au lieu de 1), le sous-dossier est lu, l'absent reste absent
            await pg.evaluate(CHOISIR, "region")
            await pg.evaluate(CLIQUE)
            ok = await attendre(pg, {"poste": 2, "sousm": 1, "web": 1})
            l = await pg.evaluate(LIRE)
            rapport(ok and l.get("nulle") == 0, "bon dossier : modeles lus dans le dossier (le fichier du dossier passe avant celui de la page, sous-dossier compris), l'autre garde l'adresse habituelle", l)
            rapport(not errs, "aucune erreur JavaScript", errs)
            await pg.close()
            # rechargement : le dossier memorise (IndexedDB) est reutilise sans clic
            pg, errs = await ouvrir(ctx, port)
            ok = await attendre(pg, {"poste": 2, "sousm": 1, "web": 1})
            rapport(ok, "apres rechargement : dossier memorise reutilise sans rien demander", await pg.evaluate(LIRE))
            rapport(not errs, "rechargement : aucune erreur JavaScript", errs)
            await pg.close(); await br.close()
    finally:
        proc.kill()
    shutil.rmtree(tmp, ignore_errors=True)
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
