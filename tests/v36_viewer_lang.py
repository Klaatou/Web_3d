#!/usr/bin/env python3
"""Tests v36 (lot C) : langue du viewer (glb-viewer.html), mêmes fichiers de langue que la page exportée.

- en anglais (locale en-US), aucun texte du viewer (panneau, liste de zones, carte, messages d'état, lignes de commande et notes) ne contient
  de lettre accentuée française ; en français (fr-FR) il garde ses accents ;
- réglage « Langue / Language » (recharge), #lang=, disposition du clavier du viewer ;
- le viewer et la page exportée ont la même langue.

Prérequis : pip install playwright ; python build.py avant.
Lancer : python tests/v36_viewer_lang.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"   # outils Python en français (v36)
import asyncio, json, os, pathlib, re, struct, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_v36vl_"))
bad = 0
ACC = re.compile(r"[éèêëàâùûôîïçœÉÈÀÙÎÔ]")


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)), flush=True)


def sol_glb(path, demi=20.0):
    pos = struct.pack("<12f", -demi, 0, -demi, demi, 0, -demi, demi, 0, demi, -demi, 0, demi)
    blob = pos + struct.pack("<6H", 0, 2, 1, 0, 3, 2) + b"\0\0"
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-demi, 0, -demi], "max": [demi, 0, demi]},
                       {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "ground"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


sol_glb(tmp / "sol.glb")
(tmp / "mauvais.glb").write_bytes(b"pas un glb du tout, juste du texte")
STUB = """(() => {
  let el = null;
  Object.defineProperty(document, 'pointerLockElement', { get: () => el, configurable: true });
  Element.prototype.requestPointerLock = function () { el = this; setTimeout(() => document.dispatchEvent(new Event('pointerlockchange')), 0); };
  document.exitPointerLock = () => { el = null; setTimeout(() => document.dispatchEvent(new Event('pointerlockchange')), 0); };
})();"""
COLLECT = """() => {
  document.querySelectorAll('details').forEach(d => { d.open = true; });
  const lg = document.getElementById('langSel'); const sv = lg ? lg.style.display : ''; if (lg) lg.style.display = 'none';
  const out = [document.body.innerText, document.title];
  for (const e of document.querySelectorAll('input,textarea,select,button,[title],[aria-label]')) {
    for (const a of ['placeholder', 'title', 'aria-label']) { const v = e.getAttribute(a); if (v) out.push(v); }
    if (e.tagName === 'SELECT' && e.id !== 'langSel') out.push([...e.options].map(o => o.text).join(' '));
    if (e.tagName === 'TEXTAREA' || (e.tagName === 'INPUT' && e.readOnly)) out.push(e.value);
  }
  if (lg) lg.style.display = sv;
  return out.join('\\n');
}"""


def fautes(txt):
    return [l for l in txt.split("\n") if ACC.search(l)]


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        url = (DIST / "glb-viewer.html").as_uri()

        async def ouvrir(locale, suffixe="", init=STUB):
            ctx = await br.new_context(locale=locale, viewport={"width": 1300, "height": 850}, accept_downloads=True)
            await ctx.add_init_script(init)
            pg = await ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(url + suffixe)
            await pg.wait_for_function("window.__viewer", timeout=40000)
            return ctx, pg, errs

        print("--- 1. viewer en anglais : aucune lettre accentuée française")
        ctx, pg, errs = await ouvrir("en-US")
        ev = pg.evaluate
        textes = {}
        textes["au départ"] = await ev(COLLECT)
        textes["au départ"] += "\n" + await ev("document.getElementById('stat').textContent")
        await pg.set_input_files("#fGlb", str(tmp / "sol.glb"))
        await pg.wait_for_function("!document.getElementById('bZip').disabled", timeout=20000)
        await pg.wait_for_timeout(600)
        textes["modèle chargé"] = await ev(COLLECT) + "\n" + await ev("document.getElementById('stat').textContent")
        stat_loaded = await ev("document.getElementById('stat').textContent")
        # promenade et pose de zones (P) de chaque type
        await ev("window.__viewer.walkStart({ pos: [0, 0, 0], yaw: 0 })")
        await pg.wait_for_function("window.__viewer.walking", timeout=10000)
        textes["promenade"] = await ev("document.getElementById('stat').textContent") + "\n" + await ev("document.getElementById('bWalk').textContent")
        for typ in ("portal", "url", "ha", "spawn"):
            await ev("(t) => { document.getElementById('zNewType').value = t; window.dispatchEvent(new KeyboardEvent('keydown', { code: 'KeyP', cancelable: true, bubbles: true })); window.dispatchEvent(new KeyboardEvent('keyup', { code: 'KeyP' })); }", typ)
        await ev("window.__viewer.walkStop()")
        textes["zones posées"] = await ev(COLLECT) + "\n" + await ev("document.getElementById('stat').textContent")
        # liaison, passe-muraille, trou, rotation, aperçu
        await ev("document.getElementById('bZoneAdd').click()")
        textes["pose active"] = await ev("document.getElementById('stat').textContent + '\\n' + document.getElementById('bZoneAdd').textContent")
        await ev("document.getElementById('bZoneAdd').click()")
        await ev("document.querySelector('#zoneList details button').click()")   # « Lier à un élément »
        textes["lier"] = await ev(COLLECT) + "\n" + await ev("document.getElementById('stat').textContent")
        await ev("window.__viewer.linkMode = false")
        await ev("document.getElementById('bErase').click()")
        textes["passe-muraille"] = await ev("document.getElementById('stat').textContent + '\\n' + document.getElementById('bErase').textContent")
        await ev("document.getElementById('bErase').click()")
        await ev("document.getElementById('bUndoIgn').click()")
        textes["annuler"] = await ev("document.getElementById('stat').textContent")
        await ev("document.getElementById('bAddPick').click()")
        textes["ajouter"] = await ev("document.getElementById('stat').textContent")
        await ev("document.getElementById('bPlace').click()")
        textes["placer le trou"] = await ev("document.getElementById('stat').textContent + '\\n' + document.getElementById('bPlace').textContent")
        await ev("document.getElementById('bPlace').click()")
        await ev("(() => { const s = document.getElementById('selRotate'); s.value = '90'; s.dispatchEvent(new Event('change')); })()")
        textes["rotation"] = await ev("document.getElementById('stat').textContent")
        await ev("(() => { const s = document.getElementById('selRotate'); s.value = '0'; s.dispatchEvent(new Event('change')); })()")
        # carte des mondes : fiche, ajout, capture, enregistrement
        await ev("document.getElementById('bCopyPick').click()")
        textes["copier le point visé (rien visé)"] = await ev("document.getElementById('stat').textContent")
        await ev("document.getElementById('bCopyTarget').click()")
        await pg.wait_for_timeout(300)
        textes["copier la cible"] = await ev("document.getElementById('stat').textContent")
        rapport(textes["copier la cible"].startswith("Copied. Target copied: "), "copie de la cible : « Copied. Target copied: x, y, z »", textes["copier la cible"])
        await ev("""(() => { const ins = [...document.querySelectorAll('#mapUi input')];
            ins[0].value = 'Test region'; ins[0].dispatchEvent(new Event('change')); })()""")
        await ev("""(() => { const ins = [...document.querySelectorAll('#mapUi input')];
            ins[1].value = 'https://example.org/index.html?region=Test'; ins[1].dispatchEvent(new Event('change')); })()""")
        textes["fiche de région"] = await ev(COLLECT)
        await ev("[...document.querySelectorAll('#mapUi button')].find(b => b.textContent.startsWith('Capture')).click()")
        textes["vignette"] = await ev("document.getElementById('stat').textContent")
        await ev("[...document.querySelectorAll('#mapUi button')].find(b => b.textContent.startsWith('Add')).click()")
        textes["ajout à la carte"] = await ev(COLLECT) + "\n" + await ev("document.getElementById('stat').textContent")
        await ev("[...document.querySelectorAll('#mapUi button')].find(b => b.textContent.startsWith('Save the thumbnail')).click()")
        textes["vignette enregistrée"] = await ev("document.getElementById('stat').textContent")
        # ligne de commande : normale, courte, modulaire, commune, avec carte et zones
        notes = []
        for short, modular, shared in ((False, False, False), (True, False, False), (False, True, False), (False, False, True), (True, False, True)):
            await ev("([a, b, c]) => { document.getElementById('cmdShort').checked = a; document.getElementById('cmdModular').checked = b; document.getElementById('cmdShared').checked = c; document.getElementById('bCmd').click(); }", [short, modular, shared])
            notes.append(await ev("document.getElementById('cmdNote').textContent"))
        textes["notes de la commande"] = "\n".join(notes)
        rapport("option(s) added" in notes[0] and "Zones: first click on" in notes[0], "notes de la ligne de commande en anglais", notes[0][:300])
        await ev("document.getElementById('bCmdCopy').click()")
        await pg.wait_for_timeout(300)
        textes["copier la commande"] = await ev("document.getElementById('stat').textContent")
        # exports et réglages mémorisés
        await ev("document.getElementById('bSetSave').click()")
        textes["réglages enregistrés"] = await ev("document.getElementById('stat').textContent")
        await ev("document.getElementById('bSetForget').click()")
        textes["réglages oubliés"] = await ev("document.getElementById('stat').textContent")
        await ev("document.getElementById('bPy').click()")
        textes["script python"] = await ev("document.getElementById('stat').textContent")
        await ev("document.getElementById('bHtml').click()")
        await pg.wait_for_timeout(800)
        textes["export html"] = await ev("document.getElementById('stat').textContent")
        await ev("document.getElementById('bZip').click()")
        await pg.wait_for_timeout(800)
        textes["export zip"] = await ev("document.getElementById('stat').textContent")
        rapport(textes["export zip"].startswith("Modular export OK"), "export modulaire : « Modular export OK … »", textes["export zip"])
        await ev("document.getElementById('bReset').click()")
        await ev("document.getElementById('bFrame').click()")
        # erreurs d'ouverture
        await pg.set_input_files("#fGlb", str(tmp / "mauvais.glb"))
        await pg.wait_for_timeout(600)
        textes["fichier invalide"] = await ev("document.getElementById('stat').textContent")
        rapport(textes["fichier invalide"].startswith("Error: ") and "not a GLB" in textes["fichier invalide"], "fichier invalide : « Error: … not a GLB »", textes["fichier invalide"])
        # messages internes (tuiles, zones, gabarits de statut)
        textes["messages"] = await ev("""() => [tr('viewer.tiles.info', 5, tr('common.yes'), tr('viewer.tiles.refs.no')), tr('viewer.tiles.line', 1, 3, ' · ' + tr('page.tiles.loading', 1), '', 12.5),
            tr('viewer.miss.msg', '1.0', '2.0', tr('viewer.miss.none')), tr('viewer.zdir.saved', 3, 'dir', 'x.zones.json', '23/10/2026', '10:00:00', tr('viewer.zdir.nobak')), tr('viewer.zdir.fallback', tr('viewer.zdir.noapi'), 'x.zones.json'),
            tr('viewer.click.linked', 'z', 'obj', '1 × 2 × 3 m', tr('viewer.click.pieces', 2)), tr('viewer.click.toobig', '40 × 40 × 3 m'), tr('viewer.cmd.n.tiles', 'x.tiles.json'), tr('viewer.cmd.sharednote'),
            tr('viewer.guide.noflat', 10, 20, 30, tr('viewer.guide.cell', '9.0', tr('viewer.guide.cell.big'))), tr('viewer.tiles.badaddr', '../x'), tr('viewer.glb.external', 'a.glb', 'a.bin'), tr('viewer.walk.status', 'WASD')].join('\\n')""")
        for nom, t in textes.items():
            f = fautes(t)
            rapport(not f, f"anglais, {nom} : aucune lettre accentuée française", f[:4])
        rapport(not errs, "aucune erreur JavaScript", errs)
        # le statut après chargement contient bien « ready »
        rapport("ready" in stat_loaded, "statut après chargement : « … ready »", stat_loaded)
        await ctx.close()

        print("--- 2. viewer en français")
        ctx, pg, errs = await ouvrir("fr-FR")
        t = await pg.evaluate(COLLECT)
        rapport("Enregistrer dans un fichier" in t and "Exporter HTML autonome" in t and len(fautes(t)) > 3, "locale fr-FR : le viewer est en français")
        await pg.set_input_files("#fGlb", str(tmp / "sol.glb"))
        await pg.wait_for_function("!document.getElementById('bZip').disabled", timeout=20000)
        await pg.wait_for_timeout(500)
        st = await pg.evaluate("document.getElementById('stat').textContent")
        rapport(st.endswith("meshes • prêt"), "statut en français après chargement", st)
        rapport(await pg.evaluate("document.title") == "GLB → HTML autonome · réglages · " + (ROOT / "VERSION").read_text(encoding="utf-8").strip(), "titre de la page en français", await pg.evaluate("document.title"))
        await ctx.close()

        print("--- 3. réglage « Langue / Language », #lang=, disposition du clavier")
        ctx, pg, errs = await ouvrir("en-US")
        opts = await pg.evaluate("[...document.getElementById('langSel').options].map(o => [o.value, o.text])")
        rapport(opts == [["auto", "Auto"], ["en", "English"], ["fr", "Français"]], "la liste de langues : Auto puis chaque langue présente", opts)
        rapport(await pg.evaluate("document.documentElement.lang") == "en", "Auto + locale en-US : anglais")
        async with pg.expect_navigation():
            await pg.evaluate("(() => { const s = document.getElementById('langSel'); s.value = 'fr'; s.dispatchEvent(new Event('change')); })()")
        await pg.wait_for_function("window.__viewer", timeout=40000)
        rapport(await pg.evaluate("document.documentElement.lang") == "fr" and await pg.evaluate("document.getElementById('bGlb').textContent") == "Ouvrir .glb", "choisir « Français » : le viewer se recharge en français")
        rapport(await pg.evaluate("localStorage.getItem('glb2html_lang')") == "fr", "choix mémorisé")
        await pg.goto(url + "#lang=en")
        await pg.reload()
        await pg.wait_for_function("window.__viewer", timeout=40000)
        rapport(await pg.evaluate("document.documentElement.lang") == "en" and await pg.evaluate("document.getElementById('bGlb').textContent") == "Open .glb", "#lang=en prioritaire")
        # clavier
        await pg.evaluate("(() => { const s = document.getElementById('kbSel'); s.value = 'azerty'; s.dispatchEvent(new Event('change')); })()")
        await pg.set_input_files("#fGlb", str(tmp / "sol.glb"))
        await pg.wait_for_function("!document.getElementById('bZip').disabled", timeout=20000)
        await pg.evaluate("window.__viewer.walkStart({ pos: [0, 0, 0], yaw: 0 })")
        st = await pg.evaluate("document.getElementById('stat').textContent")
        rapport("ZQSD/arrows walk" in st, "clavier AZERTY forcé : le statut de la promenade dit ZQSD", st)
        await pg.evaluate("window.__viewer.walkStop()")
        await pg.evaluate("(() => { const s = document.getElementById('kbSel'); s.value = 'qwerty'; s.dispatchEvent(new Event('change')); })()")
        await pg.evaluate("window.__viewer.walkStart({ pos: [0, 0, 0], yaw: 0 })")
        st = await pg.evaluate("document.getElementById('stat').textContent")
        rapport("WASD/arrows walk" in st, "clavier QWERTY forcé : le statut dit WASD", st)
        rapport(await pg.evaluate("JSON.parse(localStorage.getItem('glb2html_visitor')).layout") == "qwerty", "la disposition est mémorisée")
        await ctx.close()
        await br.close()
    print("\nRÉSULTAT : " + ("tout est passé" if not bad else f"{bad} échec(s)"))
    sys.exit(1 if bad else 0)


asyncio.run(main())
