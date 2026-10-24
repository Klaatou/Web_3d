#!/usr/bin/env python3
"""Tests v42 : rendu léger. Case « Rendu léger » dans Réglages et sous-fenêtre des réglages fins (résolution, images par seconde,
vue d'ensemble seule, rayon des tuiles, anticrénelage, valeurs préconisées), réglages en direct et retenus ; proposition quand le rendu
est logiciel (Chromium sans tête : SwiftShader) ; plafond d'images par seconde ; vue d'ensemble seule en vue globale (région en tuiles) ;
« Valeurs d'origine » ; option --light (et --maj) ; diagnostic ; note de couleur de l'avatar sur deux lignes ; lignes du viewer.

Prérequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v42.py
"""
import asyncio, json, os, shutil, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37


def damier_glb(path, n=3, cote=40.0):
    """n x n dalles séparées (un nœud par dalle) : de quoi découper plusieurs tuiles (copie de tests/v39.py)"""
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
site = tmp / "site42"; site.mkdir()
sol_glb(site / "sol.glb")
(tmp / "z42.json").write_text(json.dumps([{"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0}]), encoding="utf-8")
html(site / "sol.glb", "-o", site / "Sol.html", "--shared-shell", "--target", "0,0,0", "--zones", tmp / "z42.json", "--presence-url", f"ws://127.0.0.1:{pport}", "--room", "t42", "--chat")
html(site / "sol.glb", "-o", site / "Leg.html", "--shared-shell", "--no-sea", "--target", "0,0,0", "--room", "t42b", "--light")
cfg = json.loads((site / "Leg.config.json").read_text(encoding="utf-8"))
rapport(cfg.get("light") is True, "--light : « light » dans la config", cfg.get("light"))
html("-o", site / "Leg.html", "--maj", "--shared-shell", "--no-light")
cfg = json.loads((site / "Leg.config.json").read_text(encoding="utf-8"))
rapport(cfg.get("light") is False, "--maj --no-light : « light » remplacé", cfg.get("light"))
html("-o", site / "Leg.html", "--maj", "--shared-shell", "--light")
damier_glb(tmp / "Damier.glb")
r = run(DIST / "glb2tiles.py", tmp / "Damier.glb", "--forcer", "--budget-tri", "4", "--min", "16", "--nopause", "--sans-references", ok=False)
TILES = tmp / "Damier.tiles.json"
rapport(TILES.is_file() and (tmp / "Damier.overview.glb").is_file(), "glb2tiles : région en tuiles et vue d'ensemble", (r.stdout + r.stderr)[-400:])
html("-o", tmp / "Damier.html", "--shared-shell", "--tiles", TILES, "--room", "t42c")
for f in tmp.iterdir():
    if f.name.startswith("Damier") and f.is_file() and f.suffix in (".glb", ".json") and f.name != "Damier.glb":
        shutil.copy(f, site / f.name)
for f in tmp.glob("Damier*/"):
    if f.is_dir():
        shutil.copytree(f, site / f.name, dirs_exist_ok=True)
http, hport = serveur(site)
BASE = f"http://127.0.0.1:{hport}/index.html"
RECT = "(id) => { const e = document.getElementById(id); if (!e || e.hidden || !e.getClientRects().length) return null; const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }"
ST = "() => ({ pr: window.__viewer.renderer.getPixelRatio(), fps: window.__viewer.cfg.fpsMax, ov: window.__viewer.cfg.ovOnly, rad: window.__viewer.cfg.tileRadius, aa: window.__viewer.renderer.getContext().getContextAttributes().antialias })"


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
        ctx = await br.new_context(locale=LOC, viewport={"width": 1000, "height": 700})
        o = await Onglet(br).ouvrir(BASE + "?region=Sol", ctx=ctx)

        print("--- 1. proposition (rendu logiciel)")
        await o.attendre("!!document.getElementById('lightAsk')", 10)
        t = await o.ev("document.getElementById('lightAsk').textContent")
        rapport("sans carte graphique" in t and "rendu léger" in t, "la page propose le rendu léger", t)
        s0 = await o.ev(ST)
        rapport(s0["pr"] == 1 and s0["fps"] == 0 and s0["aa"] is True, "avant : rendu normal (résolution 1, sans limite, anticrénelage)", s0)
        await o.ev("document.getElementById('lightAskYes').click()")
        s1 = await o.ev(ST)
        rapport(s1["pr"] == 0.5 and s1["fps"] == 15 and s1["ov"] is True, "Oui : valeurs préconisées appliquées aussitôt", s1)
        rapport(await o.ev("!document.getElementById('lightAsk')"), "la proposition disparaît")
        ls = json.loads(await o.ev("localStorage.getItem('glb2html_light_t42')"))
        rapport(ls["asked"] and ls["on"] and ls["aa"] is False, "choix retenu par le navigateur", ls)

        print("--- 2. rechargement : pas de nouvelle proposition, anticrénelage coupé")
        await o.pg.reload(); await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
        await o.pg.wait_for_timeout(500)
        s2 = await o.ev(ST)
        rapport(await o.ev("!document.getElementById('lightAsk')"), "aucune proposition après une réponse")
        rapport(s2["pr"] == 0.5 and s2["fps"] == 15 and s2["aa"] is False, "réglages repris, anticrénelage coupé au chargement", s2)

        print("--- 3. Réglages : case, sous-fenêtre, réglages en direct")
        await o.touche("KeyO")
        rapport(await o.ev("document.getElementById('lightOn').checked"), "case « Rendu léger » cochée")
        order = await o.ev("(() => { const a = [...document.querySelectorAll('#optsPanel input')]; return [a.findIndex(i => i.id === 'lightOn'), a.findIndex(i => i.type === 'checkbox')]; })()")
        rapport(order[0] == 1, "la case suit « Haute résolution »", order)
        rapport(await o.ev(RECT, "lightPanel") is None, "sous-fenêtre fermée au départ")
        await o.pg.click("#lightFineBtn")
        rp, ro = await o.ev(RECT, "lightPanel"), await o.ev(RECT, "optsPanel")
        rapport(rp is not None and rp[0] + rp[2] <= ro[0] + 1 and rp[0] >= 0, "sous-fenêtre ouverte à gauche de Réglages, dans l'écran", (rp, ro))
        await o.ev("(() => { const r = document.getElementById('lightScale'); r.value = 75; r.dispatchEvent(new Event('input')); })()")
        await o.ev("(() => { const r = document.getElementById('lightFps'); r.value = 65; r.dispatchEvent(new Event('input')); })()")
        s3 = await o.ev(ST)
        rapport(s3["pr"] == 0.75 and s3["fps"] == 0, "résolution 75 % et « sans limite » appliqués en direct", s3)
        rapport(await o.txt("lightScaleV") == "75 %" and await o.txt("lightFpsV") == "sans limite", "valeurs affichées", [await o.txt("lightScaleV"), await o.txt("lightFpsV")])
        rapport(await o.ev("document.getElementById('lightOv') === null || !document.getElementById('lightOv').isConnected"), "pas de réglage de tuiles sur une région sans tuiles")
        await o.pg.click("#lightPreset")
        s4 = await o.ev(ST)
        rapport(s4["pr"] == 0.5 and s4["fps"] == 15, "« Valeurs préconisées » rétablit 50 % et 15 images/s", s4)
        await o.pg.click("#lightOn")
        s5 = await o.ev(ST)
        rapport(s5["pr"] == 1 and s5["fps"] == 0 and not s5["ov"], "case décochée : rendu normal", s5)
        await o.pg.click("#lightOn")
        await o.touche("KeyO")
        rapport(await o.ev(RECT, "lightPanel") is None, "Réglages fermé : la sous-fenêtre est cachée aussi")
        await o.touche("KeyO")
        rapport(await o.ev(RECT, "lightPanel") is not None, "Réglages rouvert : la sous-fenêtre revient")
        await o.pg.click("#lightClose")
        rapport(await o.ev(RECT, "lightPanel") is None, "bouton de fermeture")

        print("--- 4. note de couleur sur deux lignes, largeur de Réglages")
        n = await o.ev("(() => { const s = document.querySelector('#optsPanel small.two'); const lh = parseFloat(getComputedStyle(s).lineHeight); return Math.round(s.getBoundingClientRect().height / lh); })()")
        rapport(n == 2, "note de couleur : deux lignes", n)
        rr = await o.ev(RECT, "optsPanel")
        rapport(rr[2] <= 420.5, "Réglages : 420 px de large au plus", rr)
        rapport(rr[1] + rr[3] <= 700, "Réglages tient dans la hauteur de l'écran (défilement au-delà)", rr)
        print(f"        (Réglages : {rr[2]:.0f} x {rr[3]:.0f} px)")

        sec = await o.ev("(() => { const s = document.getElementById('laySec'), t = s && s.querySelector('.secT'); return s ? [t.textContent, getComputedStyle(t).fontWeight, s.querySelectorAll('button').length, getComputedStyle(s).borderTopStyle] : null; })()")
        rapport(sec and sec[0] == "Disposition des fenêtres" and int(sec[1]) >= 600 and sec[2] == 3 and sec[3] == "solid", "Disposition des fenêtres : vraie section (titre en gras, filet, trois boutons)", sec)
        rapport(await o.ev("document.getElementById('optsPanel').lastElementChild.id === 'optsNote'"), "la note « En promenade, Échap… » est tout en bas de Réglages")

        print("--- 5. plafond d'images par seconde")
        await o.ev("window.__viewer.setCfg({ anim: true })")
        await o.pg.wait_for_timeout(5500)
        r15 = (await o.ev("window.__viewer.renderStats()"))
        rapport(0 < r15["rate"] <= 16 and "sea" in r15["causes"], "mer animée, plafond 15 : au plus 15 images/s", r15)
        await o.ev("window.__viewer.setCfg({ fpsMax: 5 })")
        await o.pg.wait_for_timeout(5500)
        r5 = (await o.ev("window.__viewer.renderStats()"))
        rapport(0 < r5["rate"] <= 5.5, "plafond 5 : au plus 5 images/s", r5)
        d = await diag(o)
        rapport("Rendu léger" in d and "Images rendues par seconde" in d and "mer animée" in d, "diagnostic : réglages et images rendues", d[:200])

        print("--- 6. Valeurs d'origine")
        await o.ev("window.__viewer.setCfg({ anim: false })")
        await o.ev("(() => { const b = [...document.querySelectorAll('#optsPanel button')].find(b => b.textContent === 'Valeurs d\\'origine'); b.click(); })()")
        s6 = await o.ev(ST)
        rapport(s6["pr"] == 1 and s6["fps"] == 0 and not await o.ev("document.getElementById('lightOn').checked"), "« Valeurs d'origine » : rendu normal (page sans --light)", s6)
        rapport(json.loads(await o.ev("localStorage.getItem('glb2html_light_t42')")) == {"asked": True}, "réglages fins effacés, réponse gardée")

        print("--- 7. page --light")
        o2 = await Onglet(br).ouvrir(BASE + "?region=Leg", ctx=ctx)
        await o2.pg.wait_for_timeout(500)
        s7 = await o2.ev(ST)
        rapport(s7["pr"] == 0.5 and s7["fps"] == 15 and s7["aa"] is False, "--light : la page s'ouvre en rendu léger", s7)
        rapport(await o2.ev("!document.getElementById('lightAsk')"), "--light : aucune proposition")

        print("--- 8. région en tuiles : vue d'ensemble seule en vue globale")
        o3 = await Onglet(br).ouvrir(BASE + "?region=Damier", ctx=ctx)
        await o3.attendre("window.__viewer.tilesState().loaded > 0", 30)
        await o3.ev("document.getElementById('lightAskYes') && document.getElementById('lightAskYes').click()")
        await o3.attendre("window.__viewer.tilesState().loaded === 0", 10)
        rapport(True, "Oui : les tuiles détaillées sont déchargées en vue globale")
        await o3.touche("KeyO"); await o3.pg.click("#lightFineBtn")
        rapport(await o3.ev("!!document.getElementById('lightOv') && document.getElementById('lightOv').checked"), "case « vue d'ensemble seule » présente et cochée")
        await o3.ev("(() => { const r = document.getElementById('lightRadius'); r.value = 60; r.dispatchEvent(new Event('input')); })()")
        rapport(await o3.ev("window.__viewer.tilesState().radius") == 60, "rayon des tuiles changé en direct", await o3.ev("window.__viewer.tilesState().radius"))
        await o3.ev("window.__viewer.walkStart({ pos: [0, 2, 0], yaw: 0 })")
        await o3.attendre("window.__viewer.walking", 30)
        rapport(await o3.ev("window.__viewer.tilesState().loaded") > 0, "promenade : les tuiles se chargent")
        await o3.ev("window.__viewer.walkStop()")
        await o3.attendre("window.__viewer.tilesState().loaded === 0", 10)
        rapport(True, "retour en vue globale : déchargées")
        await o3.pg.click("#lightOv")
        await o3.attendre("window.__viewer.tilesState().loaded > 0", 30)
        rapport(True, "case décochée : les tuiles reviennent en vue globale")

        print("--- 9. viewer")
        o4 = await Onglet(br).ouvrir(f"http://127.0.0.1:{hport}/glb-viewer.html", viewer=False, ctx=ctx) if (site / "glb-viewer.html").is_file() else None
        if o4 is None:
            shutil.copy(DIST / "glb-viewer.html", site / "glb-viewer.html")
            o4 = await Onglet(br).ouvrir(f"http://127.0.0.1:{hport}/glb-viewer.html", viewer=False, ctx=ctx)
        await o4.attendre("!!window.__viewer", 30)
        body = await o4.ev("document.body.innerText")
        rapport(all(x in body for x in ["Résolution du rendu (1 = normale)", "Images/s au plus (0 = sans limite)", "Page exportée ouverte en rendu léger (--light)"]), "viewer : lignes du rendu léger")
        await o4.ev("window.__viewer.setCfg({ pixelScale: 0.5 })")
        rapport(await o4.ev("window.__viewer.renderer.getPixelRatio()") == 0.5, "viewer : résolution réglable")

        errs = o.errs + o2.errs + o3.errs + o4.errs
        rapport(not errs, "aucune erreur JavaScript", errs[:5])
        await br.close()


asyncio.run(main())
http.kill(); presence.kill()
print("\nRÉSULTAT : " + ("tout est passé" if not h37.bad else f"{h37.bad} échec(s)"))
sys.exit(1 if h37.bad else 0)
