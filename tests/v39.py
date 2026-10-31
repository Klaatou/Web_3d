#!/usr/bin/env python3
"""Tests v39 : bouton « Copier le diagnostic » (page exportée, région en tuiles, viewer).

Vérifie : bouton présent sous la fenêtre Informations / État, texte copié ou affiché sélectionné, version, carte graphique, rendu,
lignes d'état de la page, présence (adresse masquée), erreurs récentes (adresse IP et hôte masqués, # de l'adresse absent),
durées des tuiles, même bouton dans le viewer, en français et en anglais.

Prérequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v39.py
"""
import asyncio, json, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

VER = __import__("json").loads((ROOT / "VERSIONS.json").read_text(encoding="utf-8"))["index.html"]["version"]   # page ouverte par la coquille (?region=) : version de index.html
VER_V = __import__("json").loads((ROOT / "VERSIONS.json").read_text(encoding="utf-8"))["glb-viewer.html"]["version"]   # viewer


def damier_glb(path, n=3, cote=40.0):
    """n x n dalles séparées (un nœud par dalle) : de quoi découper plusieurs tuiles"""
    pos, idx, views, accs, meshes, nodes = b"", b"", [], [], [], []
    for i in range(n):
        for j in range(n):
            x0, z0 = i * cote - n * cote / 2, j * cote - n * cote / 2
            p = struct.pack("<12f", x0, 0, z0, x0 + cote, 0, z0, x0 + cote, 0, z0 + cote, x0, 0, z0 + cote)
            k = len(meshes)
            views.append({"buffer": 0, "byteOffset": len(pos), "byteLength": 48}); pos += p
            accs.append({"bufferView": 2 * k, "componentType": 5126, "count": 4, "type": "VEC3", "min": [x0, 0, z0], "max": [x0 + cote, 0, z0 + cote]})
            views.append(None); accs.append(None)
            meshes.append(None); nodes.append({"mesh": k, "name": f"dalle_{i}_{j}"})
    off = len(pos)
    ib = struct.pack("<6H", 0, 2, 1, 0, 3, 2) + b"\0\0"
    for k in range(len(meshes)):
        views[2 * k + 1] = {"buffer": 0, "byteOffset": off + 8 * k, "byteLength": 12}
        accs[2 * k + 1] = {"bufferView": 2 * k + 1, "componentType": 5123, "count": 6, "type": "SCALAR"}
        meshes[k] = {"primitives": [{"attributes": {"POSITION": 2 * k}, "indices": 2 * k + 1}]}
        idx += ib
    blob = pos + idx
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}], "bufferViews": views, "accessors": accs, "meshes": meshes,
         "nodes": nodes, "scenes": [{"nodes": list(range(len(nodes)))}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * ((4 - len(js) % 4) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


print("--- 0. fabrication des pages")
presence, pport = lancer_presence()
site = tmp / "site"; site.mkdir()
sol_glb(site / "sol.glb")
html(site / "sol.glb", "-o", site / "Sol.html", "--shared-shell", "--no-sea", "--target", "0,0,0", "--presence-url", f"ws://127.0.0.1:{pport}", "--room", "t39", "--chat")
damier_glb(tmp / "Damier.glb")
r = run(DIST / "glb2tiles.py", tmp / "Damier.glb", "--forcer", "--budget-tri", "4", "--min", "16", "--nopause", "--sans-references", ok=False)
TILES = tmp / "Damier.tiles.json"
rapport(TILES.is_file(), "glb2tiles : région en tuiles fabriquée", (r.stdout + r.stderr)[-400:])
if TILES.is_file():
    html("-o", tmp / "Damier.html", "--shared-shell", "--tiles", TILES)
    import shutil
    for f in tmp.iterdir():
        if f.name.startswith("Damier") and f.is_file() and f.suffix in (".glb", ".json") and f.name != "Damier.glb":
            shutil.copy(f, site / f.name)
    for f in tmp.glob("Damier*/"):
        if f.is_dir():
            shutil.copytree(f, site / f.name, dirs_exist_ok=True)
http, hport = serveur(site)
BASE = f"http://127.0.0.1:{hport}/index.html"


async def diag(o):
    await o.ev("document.getElementById('diagBtn').click()")
    await o.attendre("document.getElementById('diagOut').value.length > 0", 10)
    return await o.ev("document.getElementById('diagOut').value")


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)

        print("--- 1. page exportée (français)")
        o = await Onglet(br).ouvrir(BASE + "?region=Sol#name=Zoe&key=secretkey123")
        await o.attendre("document.getElementById('presenceStatus').textContent.length > 0", 15)
        b = await o.ev("(() => { const b = document.getElementById('diagBtn'); return b && { txt: b.textContent, inState: !!b.closest('#stateInfo'), visible: !!(b.offsetWidth || b.offsetHeight) }; })()")
        rapport(b and b.get("txt") == "Copier le diagnostic" and b["inState"] and b["visible"], "bouton « Copier le diagnostic » visible dans la fenêtre Informations / État", b)
        await o.ev("console.error(new Error('essai http://192.168.1.20:9000/x et wss://monhote.example:8443'))")
        await o.ev("setTimeout(() => { throw new Error('erreur non attrapée 10.0.0.7'); }, 0)")
        await o.pg.wait_for_timeout(200)
        t = await diag(o)
        rapport(t.startswith("Diagnostic Web 3d") and f"Version : {VER}" in t, "titre et version du code", t[:120])
        rapport("Carte graphique : " in t and "WebGL" in t and "Rendu (dernière image) : " in t, "carte graphique et rendu", t[:600])
        rapport("Position" in t or "position" in t, "lignes d'état de la page (position)", t)
        rapport("Présence : ws · " in t and "127.0.0.1" not in t, "présence : protocole seul, adresse masquée")
        rapport("essai http://ADRESSE/x" in t and "wss://ADRESSE" in t and "192.168" not in t and "monhote" not in t, "erreur console : adresses masquées")
        rapport("[error] " in t and "10.0.0.7" not in t and "erreur non attrapée ADRESSE" in t, "erreur non attrapée capturée, IP masquée")
        rapport("secretkey123" not in t and "Zoe" not in t.split("État affiché")[0], "le # de l'adresse (pseudo, clé) n'est pas copié")
        rapport("Page : http://ADRESSE/index.html?region=Sol" in t, "page : hôte masqué, chemin et ?region= gardés")
        toast = await o.txt("toast")
        rapport(toast in ("Diagnostic copié", "Copie impossible : le texte est sélectionné, fais Ctrl+C"), "message après la copie", toast)
        foc = await o.ev("document.activeElement && document.activeElement.id")
        rapport(foc != "diagBtn" or toast.startswith("Copie impossible"), "le bouton ne garde pas le focus", foc)
        rapport(not o.errs or all("essai" in e or "non attrapée" in e for e in o.errs), "aucune autre erreur JavaScript", o.errs)
        await o.ctx.close()

        print("--- 2. page exportée (anglais)")
        o = await Onglet(br).ouvrir(BASE + "?region=Sol#lang=en", locale="en-US")
        t = await diag(o)
        b = await o.txt("diagBtn")
        rapport(b == "Copy diagnostics" and t.startswith("Web 3d diagnostics") and "Graphics card: " in t and "Recent errors and warnings (" in t, "textes en anglais", (b, t[:200]))
        await o.ctx.close()

        if TILES.is_file():
            print("--- 3. région en tuiles : durées")
            o = await Onglet(br).ouvrir(BASE + "?region=Damier")
            await o.attendre("(() => { const s = window.__viewer.tilesState(); return s.loaded > 0 && !s.loading; })()", 30)
            t = await diag(o)
            rapport("Tuiles : " in t and " prêtes sur " in t, "ligne des tuiles", t)
            rapport("Durées des tuiles : première prête à " in t and "téléchargement" in t, "durées des tuiles", t)
            await o.ctx.close()

        print("--- 4. viewer")
        o = await Onglet(br).ouvrir((DIST / "glb-viewer.html").as_uri(), init=None, viewer=False)
        await o.attendre("!!document.getElementById('bDiag')", 15)
        await o.pg.wait_for_timeout(500)
        b = await o.txt("bDiag")
        await o.ev("document.getElementById('bDiag').click()")
        await o.pg.wait_for_timeout(500)
        st = await o.txt("stat")
        val = await o.ev("document.getElementById('diagOut').value")
        rapport(b == "Copier le diagnostic", "viewer : bouton présent", b)
        rapport(st in ("Diagnostic copié", "Copie impossible : le texte est sélectionné, fais Ctrl+C"), "viewer : message après la copie", st)
        if st.startswith("Copie impossible"):
            rapport(val.startswith("Diagnostic Web 3d") and f"Version : {VER_V}" in val, "viewer : texte affiché sélectionné", val[:200])
        else:
            rapport(val == "", "viewer : copie réussie, rien d'affiché")
        await o.ctx.close()
        await br.close()


try:
    asyncio.run(main())
finally:
    http.kill(); presence.kill()
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
