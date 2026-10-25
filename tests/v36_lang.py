#!/usr/bin/env python3
"""Tests v36 (lot B) : langue de la page (fr et en).

- Auto : la première langue de navigator.languages qui est disponible, sinon l'anglais ;
- en anglais, aucun texte visible de l'interface ne contient de lettre accentuée française (hors saisies de l'utilisateur et noms de zones) ;
- réglage « Langue / Language » (liste construite à partir des fichiers présents), #lang= prioritaire et mémorisé ;
- clé absente d'une langue : anglais, puis français, puis la clé ; une langue ajoutée par un simple fichier (build.py --i18n).

Les autres tests fixent la locale française des contextes de navigateur (new_context(locale="fr-FR", ...)) : le Chromium de test est en anglais
et ferait sinon passer les pages en anglais.

Prérequis : pip install playwright websockets ; python build.py avant.
Variables facultatives : THREE_DIR (paquet npm three, hors ligne), CHROMIUM (chemin de l'exécutable).
Lancer : python tests/v36_lang.py
"""
import asyncio, json, os, pathlib, re, shutil, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.environ["WEB3D_LANG"] = "fr"
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_v36lang_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
bad = 0
ACC = re.compile(r"[éèêëàâùûôîïçœÉÈÀÙÎÔ]")


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)), flush=True)


def run(script, *a, cwd=None, ok=True):
    r = subprocess.run([sys.executable, str(script), *map(str, a)], capture_output=True, text=True, cwd=cwd or tmp)
    if ok and r.returncode:
        sys.exit(f"[ECHEC] {pathlib.Path(script).name} {' '.join(map(str, a))}\n{r.stdout}{r.stderr}")
    return r


def port_libre():
    with socket.socket() as so:
        so.bind(("127.0.0.1", 0))
        return so.getsockname()[1]


def attendre_port(port, proc, nom):
    for _ in range(80):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return
        except OSError:
            time.sleep(0.1)
    proc.kill()
    sys.exit(f"[ECHEC] {nom} ne démarre pas")


def serveur(dossier):
    port = port_libre()
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=dossier, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    attendre_port(port, proc, "http.server")
    return proc, port


def lancer_presence():
    port = port_libre()
    proc = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--host", "127.0.0.1", "--port", str(port), "--identities", ""],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=tmp)
    attendre_port(port, proc, "presence_server")
    return proc, port


def sol_glb(path, demi=20.0):
    pos = struct.pack("<12f", -demi, 0, -demi, demi, 0, -demi, demi, 0, demi, -demi, 0, demi)
    blob = pos + struct.pack("<6H", 0, 2, 1, 0, 3, 2) + b"\0\0"
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-demi, 0, -demi], "max": [demi, 0, demi]},
                       {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


print("--- 0. fabrication")
presence, pport = lancer_presence()
PURL = f"ws://127.0.0.1:{pport}"
site = tmp / "site"
site.mkdir()
sol_glb(site / "sol.glb")
ZL = [  # noms de zones sans accent : ce sont des saisies de l'utilisateur, jamais traduites
    {"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0.0},
    {"id": "lien", "type": "url", "label": "Link test", "target": "https://example.org/", "x": 0, "y": 15, "z": -4.2, "radius": 4},
    {"id": "porte", "type": "portal", "label": "Entry portal", "target": "", "spawn": "default", "x": -10, "y": 15, "z": 10, "radius": 2, "trigger": "enter"},
    {"id": "cmd", "type": "ha", "label": "Lamp", "target": "https://example.org/ha", "confirm": True, "x": 8, "y": 15, "z": 8, "radius": 2},
]
(tmp / "z.json").write_text(json.dumps(ZL), encoding="utf-8")
r = run(DIST / "glb2html.py", site / "sol.glb", "-o", site / "Page.html", "--shared-shell", "--zones", tmp / "z.json", "--no-sea", "--target", "0,0,0",
        "--presence-url", PURL, "--room", "lang", "--chat", "--register", site / "regions.json", "--region-name", "Test", "--map-page", "carte.html", *vend)
STUB = """(() => {
  let el = null;
  Object.defineProperty(document, 'pointerLockElement', { get: () => el, configurable: true });
  Element.prototype.requestPointerLock = function () { el = this; setTimeout(() => document.dispatchEvent(new Event('pointerlockchange')), 0); };
  document.exitPointerLock = () => { el = null; setTimeout(() => document.dispatchEvent(new Event('pointerlockchange')), 0); };
  window.open = () => null;
})();"""


class Onglet:
    def __init__(self, br):
        self.br, self.errs = br, []

    async def ouvrir(self, url, locale="en-US", init=STUB, viewer=True, langs=None):
        self.ctx = await self.br.new_context(viewport={"width": 1100, "height": 760}, locale=locale)
        scripts = init
        if langs is not None:
            scripts += f"Object.defineProperty(Navigator.prototype, 'languages', {{ get: () => {json.dumps(langs)}, configurable: true }});"
        await self.ctx.add_init_script(scripts)
        self.pg = await self.ctx.new_page()
        self.pg.on("pageerror", lambda e: self.errs.append(str(e)))
        await self.pg.goto(url)
        if viewer:
            await self.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
        return self

    async def ev(self, js, arg=None):
        return await self.pg.evaluate(js, arg)

    async def walk(self):
        await self.ev("window.__viewer.walkStart({ pos: [0, 15, 0], yaw: 0 })")
        await self.pg.wait_for_function("window.__viewer.walking", timeout=10000)

    async def key(self, code, **mods):
        for t in ("keydown", "keyup"):
            await self.ev("([t, c, m]) => window.dispatchEvent(new KeyboardEvent(t, Object.assign({ code: c, cancelable: true, bubbles: true }, m)))", [t, code, mods])

    async def visible(self):
        """tout le texte visible : le corps, les champs, les placeholders, les infobulles du document"""
        return await self.ev("""() => {
          const lg = document.getElementById('visLang'), sv = lg ? lg.style.display : ''; if (lg) lg.style.display = 'none';
          const out = [document.body.innerText]; if (lg) lg.style.display = sv;
          for (const e of document.querySelectorAll('input,textarea,select,button,[title],[aria-label]')) {
            const cs = getComputedStyle(e); if (cs.display === 'none') continue;
            for (const a of ['placeholder', 'title', 'aria-label', 'value']) { const v = e.getAttribute(a); if (v && a !== 'value') out.push(v); }
            if (e.tagName === 'SELECT' && e.id !== 'visLang') out.push([...e.options].map(o => o.text).join(' '));   // le nom d'une langue s'écrit dans cette langue (Français)
          }
          return out.join('\\n');
        }""")


def sans_accent(txt):
    return [l for l in txt.split("\n") if ACC.search(l)]


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        proc, port = serveur(site)
        url = f"http://127.0.0.1:{port}/index.html?region=Page"
        try:
            # ================= 1. choix automatique =================
            print("--- 1. Auto : navigator.languages")
            cas = [("en-US", None, "en", "locale en-US"), ("fr-FR", None, "fr", "locale fr-FR"), ("es-ES", None, "en", "langue indisponible (es) : anglais"),
                   ("en-US", ["de-DE", "fr-FR", "en"], "fr", "['de', 'fr', 'en'] : la première langue disponible est le français"),
                   ("fr-FR", ["de-DE", "es"], "en", "['de', 'es'] : rien de disponible : anglais"),
                   ("en-US", ["EN-gb"], "en", "casse et région ignorées (EN-gb)")]
            for loc, langs, att, nom in cas:
                o = await Onglet(br).ouvrir(url, locale=loc, langs=langs)
                lang = await o.ev("[document.documentElement.lang, LANG, LANG_PREF]")
                rapport(lang[0] == att and lang[1] == att and lang[2] == "auto", f"Auto, {nom} -> {att}", lang)
                await o.ctx.close()

            # ================= 2. aucun accent français en anglais =================
            print("--- 2. en anglais, aucun texte visible avec une lettre accentuée française")
            o = await Onglet(br).ouvrir(url, locale="en-US")
            textes = {}
            textes["vue globale"] = await o.visible()
            await o.ev("document.getElementById('optsBtn').click()")
            textes["réglages"] = await o.visible()
            await o.ev("document.getElementById('optsBtn').click()")
            await o.key("KeyM")
            textes["carte des mondes"] = await o.visible()
            await o.key("KeyM")
            await o.walk()
            textes["promenade (aide, informations)"] = await o.visible()
            await o.ev("window.__viewer.teleportTo([0, 0, -2], 0)")
            await o.ev("(() => { const v = window.__viewer; for (let i = 0; i < 5; i++) v.walkTick(0.05); })()")
            textes["zone proche"] = await o.visible()
            await o.key("KeyT")
            textes["repères (T)"] = await o.visible()
            await o.ev("document.getElementById('gotoIn').value = 'abc'; document.getElementById('gotoBtn').click()")
            textes["Aller à, saisie invalide"] = await o.visible()
            await o.ev("document.getElementById('linkBtn').click()")
            await o.pg.wait_for_timeout(300)
            textes["copie"] = await o.visible()
            await o.ev("window.__viewer.teleportTo([8, 0, 5.5], 0)")
            await o.ev("(() => { const v = window.__viewer; for (let i = 0; i < 5; i++) v.walkTick(0.05); })()")
            await o.key("KeyE")
            await o.pg.wait_for_timeout(200)
            textes["commande avec confirmation"] = await o.visible()
            await o.key("KeyV"); await o.key("KeyH"); await o.key("KeyI")
            textes["H et I"] = await o.visible()
            await o.key("KeyH"); await o.key("KeyI")
            await o.pg.wait_for_function("window.__viewer.getPresence().state === 'online'", timeout=30000)
            await o.key("Enter")
            textes["chat ouvert"] = await o.visible()
            await o.pg.keyboard.press("Escape")
            textes["présence"] = await o.visible()
            for nom, t in textes.items():
                fautes = sans_accent(t)
                rapport(not fautes, f"anglais, {nom} : aucune lettre accentuée française", fautes[:5])
            rapport("Walk" in textes["vue globale"] and "Settings" in textes["vue globale"] and "Help" in textes["vue globale"], "vue globale : « Walk (P) », « Settings », « Help (H) »", textes["vue globale"][:200])
            rapport("Information / Status" in textes["promenade (aide, informations)"] and "Page Up" in textes["promenade (aide, informations)"] and "Movement" in textes["promenade (aide, informations)"], "promenade : aide en anglais (Movement, Page Up, Information / Status)")
            rapport("click or E: Link test" in textes["zone proche"], "invite d'une zone : « click or E: Link test » (le nom de la zone n'est pas traduit)", textes["zone proche"][-300:])
            rapport("Send the command" in textes["commande avec confirmation"], "confirmation d'une commande : en anglais", textes["commande avec confirmation"][-300:])
            rapport(not o.errs, "aucune erreur JavaScript", o.errs)
            # messages internes (console ou construits) en anglais aussi
            msgs = await o.ev("""() => [tr('core.zone.norefs', 'a', 'b'), tr('core.pick.mesh', 'x') + tr('core.pick.parents', 'y') + tr('core.pick.material', 'z') + tr('core.pick.size', '1') + tr('core.pick.point', '2'),
              trn('page.chat.saved', 2), trn('page.tiles.main', 2, 5, '10', '1 M'), trn('page.pres.count', 3), trn('page.wait.tiles', 1, 1), trn('page.wait.tiles', 4, 2),
              tr('core.tile.ready', 'f.glb', 1, 2, 3, 4, 5, 6, 7, 8, 9), tr('core.tile.badpath', 'x'), tr('core.ov.unavailable', 'o', 'e'), tr('page.pres.error', 'ws://x'), tr('core.view.tps')].join('\\n')""")
            rapport(not sans_accent(msgs), "messages internes (références, description d'objet, tuiles, journal) : en anglais", sans_accent(msgs))
            await o.ctx.close()

            # ================= 3. le français garde ses accents =================
            print("--- 3. français")
            o = await Onglet(br).ouvrir(url, locale="fr-FR")
            await o.walk()
            t = await o.visible()
            rapport("Déplacement" in t and "Informations / État" in t and "Page Haut" in t and len(sans_accent(t)) > 3, "locale fr-FR : l'interface est en français")
            await o.ctx.close()

            # ================= 4. réglage de langue et #lang= =================
            print("--- 4. réglage « Langue / Language », #lang=")
            o = await Onglet(br).ouvrir(url, locale="en-US")
            await o.ev("document.getElementById('optsBtn').click()")
            opts = await o.ev("[...document.getElementById('visLang').options].map(x => [x.value, x.text])")
            rapport(opts == [["auto", "Auto"], ["en", "English"], ["fr", "Français"]], "la liste propose Auto puis chaque langue présente, avec son nom", opts)
            rapport(await o.ev("document.getElementById('visLang').value") == "auto", "Auto est choisi au départ")
            async with o.pg.expect_navigation():
                await o.ev("(() => { const s = document.getElementById('visLang'); s.value = 'fr'; s.dispatchEvent(new Event('change')); })()")
            await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            rapport(await o.ev("document.documentElement.lang") == "fr" and "Promenade (P)" in await o.ev("document.getElementById('walkBtn').textContent"), "choisir « Français » : la page se recharge en français", await o.ev("document.documentElement.lang"))
            rapport(await o.ev("localStorage.getItem('glb2html_lang')") == "fr", "le choix est mémorisé")
            await o.ev("document.getElementById('optsBtn').click()")
            rapport(await o.ev("document.getElementById('visLang').value") == "fr", "la liste montre le choix mémorisé")
            async with o.pg.expect_navigation():
                await o.ev("(() => { const s = document.getElementById('visLang'); s.value = 'auto'; s.dispatchEvent(new Event('change')); })()")
            await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            rapport(await o.ev("document.documentElement.lang") == "en", "retour à Auto : la langue du navigateur (anglais)")
            await o.ctx.close()
            # #lang=
            o = await Onglet(br).ouvrir(url + "#lang=fr", locale="en-US")
            rapport(await o.ev("document.documentElement.lang") == "fr" and await o.ev("localStorage.getItem('glb2html_lang')") == "fr", "#lang=fr dans une page d'un navigateur anglais : prioritaire et mémorisé")
            await o.pg.goto(url)
            await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            rapport(await o.ev("document.documentElement.lang") == "fr", "sans #lang=, la page reste en français (mémorisé)")
            await o.pg.goto(url + "#lang=en")
            await o.pg.reload()
            await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            rapport(await o.ev("document.documentElement.lang") == "en" and await o.ev("localStorage.getItem('glb2html_lang')") == "en", "#lang=en remplace le choix mémorisé")
            await o.pg.goto(url + "#lang=xx")
            await o.pg.reload()
            await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            rapport(await o.ev("document.documentElement.lang") == "en", "#lang=xx (langue absente) : ignoré, le choix mémorisé reste")
            await o.pg.goto(url + "#lang=auto")
            await o.pg.reload()
            await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            rapport(await o.ev("localStorage.getItem('glb2html_lang')") == "auto", "#lang=auto remet le choix automatique")
            await o.ctx.close()
            # #lang= avec d'autres paramètres du lien (spawn, name)
            o = await Onglet(br).ouvrir(url + "#spawn=default&lang=fr&name=Zoe", locale="en-US")
            rapport(await o.ev("document.documentElement.lang") == "fr" and await o.ev("window.__viewer.walking"), "#lang= avec #spawn= et #name= : les trois sont pris en compte")
            await o.ctx.close()

            # ================= 5. page carte =================
            print("--- 5. page carte (carte.html)")
            o = await Onglet(br).ouvrir(f"http://127.0.0.1:{port}/carte.html", locale="en-US", viewer=False)
            await o.pg.wait_for_timeout(500)
            t = await o.visible()
            rapport(not sans_accent(t) and "My nickname" in t and "Show addresses" in t, "page carte en anglais, sans accent français", t[:300])
            await o.ctx.close()
            o = await Onglet(br).ouvrir(f"http://127.0.0.1:{port}/carte.html", locale="fr-FR", viewer=False)
            await o.pg.wait_for_timeout(500)
            t = await o.visible()
            rapport("Mon pseudo" in t and "Afficher les adresses" in t, "page carte en français avec la locale fr-FR", t[:300])
            await o.ctx.close()
            # coquille : message d'erreur dans la langue
            o = await Onglet(br).ouvrir(f"http://127.0.0.1:{port}/index.html?region=..%2Fx", locale="en-US", viewer=False)
            await o.pg.wait_for_timeout(500)
            t = await o.ev("document.getElementById('msg').textContent")
            rapport(t.startswith("Error:") and "region parameter refused" in t and not sans_accent(t), "coquille : paramètre region refusé, message en anglais", t)
            await o.ctx.close()
            o = await Onglet(br).ouvrir(f"http://127.0.0.1:{port}/index.html?region=..%2Fx", locale="fr-FR", viewer=False)
            await o.pg.wait_for_timeout(500)
            t = await o.ev("document.getElementById('msg').textContent")
            rapport(t.startswith("Erreur :") and "paramètre region refusé" in t, "… et en français", t)
            await o.ctx.close()

            # ================= 6. clé absente, langue ajoutée par un fichier =================
            print("--- 6. repli (anglais, français, clé) et langue ajoutée par un fichier")
            i18n2 = tmp / "i18n2"
            i18n2.mkdir()
            fr = json.loads((ROOT / "src" / "i18n" / "fr.json").read_text(encoding="utf-8"))
            en = json.loads((ROOT / "src" / "i18n" / "en.json").read_text(encoding="utf-8"))
            en.pop("page.help.title"); en.pop("page.opt.sounds"); fr.pop("page.opt.sounds")   # « Aide » n'existe plus qu'en français ; « Sons » nulle part
            (i18n2 / "fr.json").write_text(json.dumps(fr, ensure_ascii=False), encoding="utf-8")
            (i18n2 / "en.json").write_text(json.dumps(en, ensure_ascii=False), encoding="utf-8")
            de = {"_name": "Deutsch", "page.btn.walk": "Spaziergang (P)", "page.opts": "Einstellungen", "page.help.g.move": "Bewegung"}
            (i18n2 / "de.json").write_text(json.dumps(de, ensure_ascii=False), encoding="utf-8")
            dist2 = tmp / "dist2"
            run(ROOT / "build.py", "--out", dist2, "--i18n", i18n2, *vend)
            site2 = tmp / "site2"
            site2.mkdir()
            shutil.copy(site / "sol.glb", site2 / "sol.glb")
            run(dist2 / "glb2html.py", site2 / "sol.glb", "-o", site2 / "Page.html", "--shared-shell", "--zones", tmp / "z.json", "--no-sea", "--target", "0,0,0", *vend)
            proc2, port2 = serveur(site2)
            try:
                url2 = f"http://127.0.0.1:{port2}/index.html?region=Page"
                o = await Onglet(br).ouvrir(url2 + "#lang=de", locale="en-US")
                rapport(await o.ev("document.documentElement.lang") == "de" and "Spaziergang (P)" in await o.ev("document.getElementById('walkBtn').textContent") and await o.ev("document.getElementById('optsBtn').textContent") == "Einstellungen", "langue ajoutée par un simple fichier de.json : choisie par #lang=de")
                await o.walk()
                t = await o.ev("document.getElementById('helpBody').textContent")
                rapport("Bewegung" in t and "Space: jump" in t, "clé absente de l'allemand : repli sur l'anglais (« Space: jump »)", t[:200])
                rapport(await o.ev("document.getElementById('helpHead').textContent") == "▾ Aide", "clé absente de l'allemand ET de l'anglais : repli sur le français (« Aide »)", await o.ev("document.getElementById('helpHead').textContent"))
                rapport(await o.ev("tr('page.opt.sounds')") == "page.opt.sounds" and await o.ev("tr('inexistante.cle')") == "inexistante.cle", "clé absente partout : la clé elle-même")
                await o.ev("document.getElementById('optsBtn').click()")
                opts = await o.ev("[...document.getElementById('visLang').options].map(x => [x.value, x.text])")
                rapport(opts == [["auto", "Auto"], ["de", "Deutsch"], ["en", "English"], ["fr", "Français"]], "la liste de langues contient la langue ajoutée", opts)
                await o.ctx.close()
                o = await Onglet(br).ouvrir(url2, locale="de-DE")
                rapport(await o.ev("document.documentElement.lang") == "de", "Auto avec la locale de-DE : la langue ajoutée est choisie")
                await o.ctx.close()
            finally:
                proc2.terminate()
        finally:
            proc.terminate()
            await br.close()
    print("\nRÉSULTAT : " + ("tout est passé" if not bad else f"{bad} échec(s)"))
    presence.terminate()
    sys.exit(1 if bad else 0)


asyncio.run(main())
