#!/usr/bin/env python3
"""Test des zones audio (type audio, 1.11.4) : les fichiers son d'un dossier jouent dans l'ordre alphabetique, en boucle, en promenade a portee.

Hors navigateur : glb2html.py --audio-list (liste playlist.json : ordre alphabetique, nombres comparés comme des nombres, fichiers son seulement, --dry-run,
dossier absent) et nettoyage des zones (dossier, pistes, portee jusqu'a 200 m).
Dans Chromium : liste lue (<mediaDir>/<dossier> avant <dossier>), lecture dans l'ordre puis en boucle, volume selon la distance, arret hors portee et reprise a la piste
quittee, piste illisible sautee, toutes illisibles / liste absente / liste vide dites dans la ligne « Musique », case « Musique des zones » exclusive avec « Radio des zones »,
la radio gagne a egalite ; viewer : type Audio, bouton « Mettre a jour la liste » (dossier simule), meme ordre que la commande.

Les pistes sont des WAV d'une seconde servis en local (le Chromium du bac a sable n'a pas de decodeur MP3).
Prerequis : pip install playwright && playwright install chromium ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM.
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, functools, http.server, json, math, os, pathlib, struct, subprocess, sys, tempfile, threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_audio_"))
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


def wav(path, secondes=1, hz=440):
    n = 8000 * secondes
    data = bytes(int(128 + 100 * math.sin(2 * math.pi * hz * i / 8000)) for i in range(n))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"RIFF" + struct.pack("<I", 36 + n) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 8000, 8000, 1, 8) + b"data" + struct.pack("<I", n) + data)


def outil(*args):
    return subprocess.run([sys.executable, str(DIST / "glb2html.py"), *map(str, args)], capture_output=True, text=True)


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serveur(dossier):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(dossier)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def page(port):
    Z = lambda i, t, x, z, **k: dict({"id": i, "type": t, "label": "Zone " + i, "x": x, "y": 15, "z": z}, **k)
    zones = [Z("zik", "audio", 0, 0, radius=10, folder="audio"),
             Z("rad", "cast", 0, -12, radius=10, target=f"http://127.0.0.1:{port}/flux.wav"),
             Z("casse", "audio", 30, 0, radius=5, tracks=["absent.wav", "audio/1-a.wav"]),         # liste ecrite dans la zone : la premiere piste manque, elle est sautee
             Z("med", "audio", -30, 0, radius=5, folder="mus"),                                   # liste dans le sous-dossier medias
             Z("sansliste", "audio", 0, 30, radius=5, folder="absent"),
             Z("vide", "audio", 0, 45, radius=5, folder="vide"),
             Z("mort", "audio", 45, 45, radius=5, tracks=["x1.wav", "x2.wav"]),
             Z("grande", "audio", 150, -150, radius=500, folder="audio"),
             Z("mauvaise", "audio", 45, -45, radius=5, folder="../secret", tracks=["javascript:alert(1)", "../x.mp3", "ok.wav", 5, "C:\\x.wav", "https://exemple.invalid/a.mp3"]),
             Z("lien", "url", 0, 55, radius=150, target="https://exemple.invalid/", trigger="click")]
    (tmp / "z.json").write_text(json.dumps(zones), encoding="utf-8")
    out = tmp / "p.html"
    r = outil(tmp / "sol.glb", "-o", out, "--zones", tmp / "z.json", "--no-sea", *vend)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    t = out.read_text(encoding="utf-8")
    for a, b in (("const viewer = createViewer(", "const viewer = window.__v = createViewer("), ("const RADIO = (() => {", "const RADIO = window.__r = (() => {"),
                 ("const MUSIC = (() => {", "const MUSIC = window.__m = (() => {")):
        if a not in t:
            sys.exit(f"[ECHEC] marqueur absent de la page : {a}")
        t = t.replace(a, b, 1)
    out.write_text(t, encoding="utf-8")
    return out


FAKE = """
class FakeFile { constructor(n, t) { this.kind = 'file'; this.name = n; this.t = t; } async createWritable() { const s = this; return { write: async x => { s.t = x; }, close: async () => {} }; } async getFile() { return { text: async () => this.t, name: this.name }; } }
class FakeDir {
  constructor(n) { this.kind = 'directory'; this.name = n; this.m = new Map(); }
  async *entries() { for (const [k, v] of this.m) yield [k, v]; }
  async getDirectoryHandle(n) { const v = this.m.get(n); if (!v || v.kind !== 'directory') { const e = new Error('absent'); e.name = 'NotFoundError'; throw e; } return v; }
  async getFileHandle(n, o) { let v = this.m.get(n); if (!v) { if (!(o && o.create)) { const e = new Error('absent'); e.name = 'NotFoundError'; throw e; } v = new FakeFile(n, ''); this.m.set(n, v); } return v; }
  async queryPermission() { return 'granted'; }
}
window.__fake = (spec) => { const root = new FakeDir('region'); for (const [p, t] of Object.entries(spec)) { const parts = p.split('/'); let d = root; for (const s of parts.slice(0, -1)) { if (!d.m.has(s)) d.m.set(s, new FakeDir(s)); d = d.m.get(s); } d.m.set(parts[parts.length - 1], new FakeFile(parts[parts.length - 1], t)); } return root; };
"""


async def main():
    from playwright.async_api import async_playwright
    sol_glb(tmp / "sol.glb")
    # ---- hors navigateur : --audio-list
    for n in ("10-c.wav", "2-b.wav", "1-a.wav"):
        wav(tmp / "audio" / n, 1, 300 + 100 * len(n))
    (tmp / "audio" / "notes.txt").write_text("x"); (tmp / "audio" / ".cache.wav").write_bytes(b"x"); (tmp / "audio" / "cover.jpg").write_bytes(b"x"); (tmp / "audio" / "sous").mkdir()
    r = outil("--audio-list", tmp / "audio")
    pl = json.loads((tmp / "audio" / "playlist.json").read_text(encoding="utf-8")) if (tmp / "audio" / "playlist.json").exists() else {}
    rapport(r.returncode == 0 and pl.get("tracks") == ["1-a.wav", "2-b.wav", "10-c.wav"], "--audio-list : fichiers son seulement (ni .txt, .jpg, cache, sous-dossier), 2 avant 10", (r.stdout, r.stderr, pl))
    tri = ["É.wav", "e.wav", "B.wav", "a10.wav", "a2.wav", "10.wav", "9.wav", "A1.mp3", "Piste 3.ogg", "Piste 12.ogg"]
    for n in tri:
        (tmp / "tri").mkdir(exist_ok=True); (tmp / "tri" / n).write_bytes(b"x")
    r = outil("--audio-list", tmp / "tri")
    ordre_py = json.loads((tmp / "tri" / "playlist.json").read_text(encoding="utf-8"))["tracks"]
    rapport(r.returncode == 0 and sorted(ordre_py) == sorted(tri) and ordre_py.index("9.wav") < ordre_py.index("10.wav") < ordre_py.index("A1.mp3"), "--audio-list : tri naturel sans tenir compte des majuscules", ordre_py)
    (tmp / "sec").mkdir(); (tmp / "sec" / "a.wav").write_bytes(b"x")
    r = outil("--audio-list", tmp / "sec", "--dry-run")
    rapport(r.returncode == 0 and not (tmp / "sec" / "playlist.json").exists() and "rien n'a été écrit" in r.stdout, "--audio-list --dry-run : rien n'est ecrit", (r.stdout, r.stderr))
    r = outil("--audio-list", tmp / "nexiste-pas")
    rapport(r.returncode != 0 and "introuvable" in (r.stdout + r.stderr), "--audio-list : dossier absent : erreur claire", (r.returncode, r.stdout, r.stderr))
    (tmp / "vide").mkdir()
    r = outil("--audio-list", tmp / "vide")
    rapport(r.returncode == 0 and json.loads((tmp / "vide" / "playlist.json").read_text(encoding="utf-8")) == {"tracks": []} and "aucun fichier son" in r.stderr, "--audio-list : dossier sans son : liste vide ecrite, avertissement", (r.stdout, r.stderr))
    wav(tmp / "flux.wav", 40)
    wav(tmp / "medias" / "mus" / "m1.wav", 1, 700)
    (tmp / "medias" / "mus" / "playlist.json").write_text(json.dumps(["m1.wav"]), encoding="utf-8")          # ancien format : un simple tableau
    wav(tmp / "x" / "y.wav", 1)
    wav(tmp / "audio" / "1-a.wav", 1, 500)
    r = outil("--audio-list", tmp / "audio")
    srv = serveur(tmp)
    out = page(srv.server_address[1])
    v = (DIST / "glb-viewer.html").read_text(encoding="utf-8")
    rapport('value="audio"' in v and "updateAudioList" in v and "audioTry" in v, "viewer : le type Musique est propose, le bouton de mise a jour de la liste existe")
    async with async_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
        br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--autoplay-policy=no-user-gesture-required"], **kw)
        pg = await br.new_page(locale="fr-FR"); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/p.html")
        await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
        await pg.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
        zs = {z["id"]: z for z in await pg.evaluate("window.__v.getZones()")}
        rapport(zs["zik"]["radius"] == 10 and zs["grande"]["radius"] == 200 and zs["lien"]["radius"] == 50, "portee : jusqu'a 200 m pour une zone audio, 50 pour les autres", {k: z["radius"] for k, z in zs.items()})
        rapport(all(z["type"] == "audio" and z["mesh"] == "" and z["trigger"] == "click" for k, z in zs.items() if k in ("zik", "casse", "med")) and zs["zik"]["folder"] == "audio", "zone audio : type et dossier conserves, jamais liee a un element")
        mv = zs["mauvaise"]
        rapport("folder" not in mv and mv.get("tracks") == ["ok.wav", "https://exemple.invalid/a.mp3"], "nettoyage : dossier avec « .. » refuse ; pistes javascript:, « .. », lecteur Windows et non-texte retirees", mv)
        cones = sorted(c["id"] for c in await pg.evaluate("window.__v.getCones()"))
        rapport("zik" in cones and "med" in cones and "lien" not in cones, "zone audio : un cone par defaut, pas pour la zone url au clic", cones)
        info = lambda: pg.evaluate("(() => { const e = document.getElementById('musicInfo'); return e.hidden ? '' : e.textContent; })()")
        rinfo = lambda: pg.evaluate("(() => { const e = document.getElementById('radioInfo'); return e.hidden ? '' : e.textContent; })()")
        mplay = lambda: pg.evaluate("window.__m.playing()")
        rplay = lambda: pg.evaluate("window.__r.playing()")
        piste = lambda: pg.evaluate("window.__m.track()")
        rapport(await pg.evaluate("['visMusic', 'visRadio', 'visSounds'].every(i => document.getElementById(i) !== null)"), "Reglages : cases « Sons », « Radio des zones » et « Musique des zones » presentes")
        rapport(await info() == "" and not await mplay(), "vue globale : pas de musique")
        await pg.evaluate("window.__v.walkStart({ pos: [0, 15, 20], yaw: 0 })"); await pg.wait_for_timeout(500)
        rapport("hors de port" in await info() and not await mplay(), "promenade hors portee (dans 2 fois la portee) : rien ne joue, la ligne dit « hors de portee » (1.11.18)", await info())
        await pg.evaluate("window.__v.teleportTo([0, 15, 8], 0)"); await pg.wait_for_timeout(1200)
        t = await info()
        rapport("Zone zik" in t and "clic" in t and not await mplay(), "a portee avant la premiere action : « un clic ou une touche », rien ne joue", t)
        rapport(await pg.evaluate("document.getElementById('zonePrompt').hidden || !/zik/.test(document.getElementById('zonePrompt').textContent)"), "zone audio : pas d'invite « clic ou E »")
        await pg.keyboard.press("ControlLeft")
        try:
            await pg.wait_for_function("window.__m.playing()", timeout=15000)
        except Exception:
            pass
        rapport(await mplay() and "Zone zik" in await info() and await piste() == "1-a.wav", "apres une touche : la premiere piste joue (1-a.wav), la ligne « Musique » le dit", (await info(), await piste()))
        # ordre puis boucle : 1-a, 2-b, 10-c, 1-a
        vus = [await piste()]
        for _ in range(180):
            await pg.wait_for_timeout(100)
            n = await piste()
            if n != vus[-1]:
                vus.append(n)
            if len(vus) >= 4:
                break
        rapport(vus == ["1-a.wav", "2-b.wav", "10-c.wav", "1-a.wav"], "lecture : dans l'ordre (2 avant 10) puis en boucle sur toute la liste", vus)
        await pg.evaluate("window.__v.teleportTo([0, 15, 1], 0)"); await pg.wait_for_timeout(500)
        niv = await pg.evaluate("window.__m.level()")
        rapport(0.4 < niv <= 0.5, "volume : 0,45 au centre (gain 0,9 x volume 50 %)", niv)
        await pg.evaluate("window.__v.teleportTo([0, 15, 9], 0)"); await pg.wait_for_timeout(500)
        rapport(0 < await pg.evaluate("window.__m.level()") < 0.1, "volume : presque nul au bord", await pg.evaluate("window.__m.level()"))
        # reprise a la piste quittee
        for _ in range(120):
            if await piste() == "2-b.wav":
                break
            await pg.wait_for_timeout(100)
        avant = await piste()
        await pg.evaluate("window.__v.teleportTo([0, 15, 20], 0)"); await pg.wait_for_timeout(600)
        rapport(not await mplay() and "hors de port" in await info(), "sortie de la portee : la musique s'arrete, la ligne reste « hors de portee » (1.11.18)", await info())
        await pg.evaluate("window.__v.teleportTo([0, 15, 4], 0)"); await pg.wait_for_timeout(300)
        try:
            await pg.wait_for_function("window.__m.playing()", timeout=10000)
        except Exception:
            pass
        rapport(await mplay() and await piste() == avant, "retour dans la zone : la lecture reprend a la piste quittee", (avant, await piste()))
        # liste dans la zone, premiere piste absente : sautee
        await pg.evaluate("window.__v.teleportTo([30, 15, 2], 0)")
        try:
            await pg.wait_for_function("window.__m.playing() && window.__m.track() === '1-a.wav'", timeout=15000)
        except Exception:
            pass
        rapport(await mplay() and await piste() == "1-a.wav" and "Zone casse" in await info(), "piste illisible : sautee, la suivante joue (liste ecrite dans la zone)", (await info(), await piste()))
        # sous-dossier medias d'abord
        await pg.evaluate("window.__v.teleportTo([-30, 15, 2], 0)")
        try:
            await pg.wait_for_function("window.__m.playing() && window.__m.track() === 'm1.wav'", timeout=15000)
        except Exception:
            pass
        rapport(await piste() == "m1.wav" and "Zone med" in await info(), "dossier cherche dans medias/ d'abord ; liste au format « tableau de noms »", (await info(), await piste()))
        # liste absente / vide / toutes illisibles
        for (x, z, zone_id, mot, titre) in ((0, 30, "sansliste", "introuvable", "liste absente"), (0, 45, "vide", "vide", "liste vide"), (45, 45, "mort", "illisibles", "toutes les pistes illisibles")):
            await pg.evaluate(f"window.__v.teleportTo([{x}, 15, {z}], 0)")
            try:
                await pg.wait_for_function(f"/{mot}/.test(document.getElementById('musicInfo').textContent)", timeout=15000)
            except Exception:
                pass
            t = await info()
            rapport(f"Zone {zone_id}" in t and mot in t and not await mplay(), f"{titre} : dite dans la ligne « Musique », rien ne joue", t)
        # exclusion avec la radio : a egalite (deux cases cochees) la radio gagne
        await pg.evaluate("window.__v.teleportTo([0, 15, -6], 0)"); await pg.wait_for_timeout(1200)
        coches = lambda: pg.evaluate("[document.getElementById('visRadio').checked, document.getElementById('visMusic').checked]")
        rapport(await coches() == [True, True], "Reglages : les deux cases sont cochees au depart", await coches())
        try:
            await pg.wait_for_function("window.__r.playing()", timeout=15000)
        except Exception:
            pass
        rapport(await rplay() and not await mplay(), "les deux cases cochees, les deux zones a egalite : une seule joue (la radio)", (await rplay(), await mplay()))
        await pg.evaluate("document.getElementById('visRadio').click()"); await pg.wait_for_timeout(500)
        try:
            await pg.wait_for_function("window.__m.playing()", timeout=15000)
        except Exception:
            pass
        rapport(await coches() == [False, True] and await mplay() and not await rplay(), "radio decochee : la musique joue", (await coches(), await mplay(), await rplay()))
        await pg.evaluate("document.getElementById('visRadio').click()"); await pg.wait_for_timeout(500)
        try:
            await pg.wait_for_function("window.__r.playing()", timeout=15000)
        except Exception:
            pass
        rapport(await coches() == [True, False] and await rplay() and not await mplay(), "radio recochee : la case Musique se decoche, la radio joue (exclusion)", (await coches(), await mplay(), await rplay()))
        await pg.evaluate("document.getElementById('visMusic').click()"); await pg.wait_for_timeout(500)
        try:
            await pg.wait_for_function("window.__m.playing()", timeout=15000)
        except Exception:
            pass
        rapport(await coches() == [False, True] and await mplay() and not await rplay(), "musique recochee : la case Radio se decoche, la musique joue (exclusion)", (await coches(), await mplay(), await rplay()))
        rapport(not errs, "page : aucune erreur JavaScript", errs)
        await pg.close()

        # ---- viewer : type Musique, bouton de mise a jour (dossier simule), meme ordre que la commande
        vw = tmp / "viewer"; vw.mkdir()
        vt = v.replace("async function audioTry(z) {", "window.__au = { audioFolderIn, audioFilesIn, updateAudioList, natCmp, setDir: h => { zonesDirHandle = h; } };\nasync function audioTry(z) {", 1)
        assert "window.__au" in vt
        (vw / "glb-viewer.html").write_text(vt, encoding="utf-8")
        import shutil
        shutil.copy(tmp / "sol.glb", vw / "sol.glb")
        srv2 = serveur(vw)
        pv = await br.new_page(locale="fr-FR", viewport={"width": 1000, "height": 800}); ev = []
        pv.on("pageerror", lambda e: ev.append(str(e)))
        await pv.goto(f"http://127.0.0.1:{srv2.server_address[1]}/glb-viewer.html")
        await pv.wait_for_function("window.__viewer", timeout=60000)
        await pv.set_input_files("#fGlb", str(tmp / "sol.glb"))
        await pv.wait_for_function("window.__viewer.model", timeout=60000)
        await pv.add_script_tag(content=FAKE)
        (tmp / "zv.json").write_text(json.dumps([{"id": "m", "type": "audio", "label": "Musique", "x": 0, "y": 15, "z": 0, "radius": 20, "folder": "audio"}]), encoding="utf-8")
        await pv.set_input_files("#fZones", str(tmp / "zv.json"))
        await pv.wait_for_function("window.__viewer.getZones().length === 1", timeout=10000)
        await pv.wait_for_timeout(500)
        await pv.locator("#zoneList details summary").first.click(); await pv.wait_for_timeout(500)
        txt = await pv.evaluate("document.querySelector('#zoneList details').innerText")
        rapport("Dossier des pistes" in txt and "Mettre à jour la liste" in txt and "Essayer la première piste" in txt and "Portée" in txt, "viewer : zone Musique : dossier, bouton de mise a jour, essai, portee", txt[:300])
        sel = await pv.evaluate("[...document.querySelectorAll('#zNewType option')].map(o => o.value)")
        rapport("audio" in sel, "viewer : le menu des types propose Musique", sel)
        spec = {"sol.glb": "x", "audio/B.mp3": "x", "audio/a10.wav": "x", "audio/a2.wav": "x", "audio/.cache.wav": "x", "audio/notes.txt": "x", "audio/É.wav": "x", "audio/e.wav": "x",
                "audio/10.wav": "x", "audio/9.wav": "x", "audio/A1.mp3": "x", "audio/Piste 3.ogg": "x", "audio/Piste 12.ogg": "x"}
        await pv.evaluate("(spec) => window.__au.setDir(window.__fake(spec))", spec)
        await pv.evaluate("window.__au.updateAudioList({ folder: 'audio' })"); await pv.wait_for_timeout(400)
        etat = await pv.evaluate("document.getElementById('stat').textContent")
        ecrit = await pv.evaluate("(async () => { const d = await window.__fake_last_dir(); return d; })()") if False else None
        # relire ce que le bouton a ecrit : refaire la meme chose sur un dossier connu
        resultat = await pv.evaluate("""async (spec) => {
            const d = window.__fake(spec); window.__au.setDir(d);
            await window.__au.updateAudioList({ folder: 'audio' });
            const a = await d.getDirectoryHandle('audio'); const f = await a.getFileHandle('playlist.json');
            return JSON.parse(await (await f.getFile()).text());
        }""", spec)
        # la commande, sur les memes noms
        for n in spec:
            if n.startswith("audio/"):
                (tmp / "vtri").mkdir(exist_ok=True); (tmp / "vtri" / n.split("/")[1]).write_bytes(b"x")
        outil("--audio-list", tmp / "vtri")
        cmd = json.loads((tmp / "vtri" / "playlist.json").read_text(encoding="utf-8"))
        rapport(resultat == cmd and len(cmd["tracks"]) == 10, "viewer : la liste ecrite par le bouton est identique a celle de --audio-list (meme ordre, memes fichiers)", (resultat, cmd))
        rapport("Liste écrite" in etat and "audio/playlist.json" in etat, "viewer : la ligne d'etat dit ce qui a ete ecrit", etat)
        await pv.evaluate("window.__au.setDir(window.__fake({ 'sol.glb': 'x', 'medias/audio/a.wav': 'x' }))")
        await pv.evaluate("window.__au.updateAudioList({ folder: 'audio' })"); await pv.wait_for_timeout(300)
        r2 = await pv.evaluate("(async () => { const d = window.__fake({ 'sol.glb': 'x', 'medias/audio/a.wav': 'x' }); window.__au.setDir(d); await window.__au.updateAudioList({ folder: 'audio' }); const m = await (await d.getDirectoryHandle('medias')).getDirectoryHandle('audio'); return await (await (await m.getFileHandle('playlist.json')).getFile()).text(); })()")
        rapport('"a.wav"' in r2, "viewer : le dossier du sous-dossier medias est utilise d'abord (comme la page)", r2)
        await pv.evaluate("window.__au.setDir(window.__fake({ 'sol.glb': 'x' }))")
        await pv.evaluate("window.__au.updateAudioList({ folder: 'inconnu' })"); await pv.wait_for_timeout(300)
        etat = await pv.evaluate("document.getElementById('stat').textContent")
        rapport("introuvable" in etat, "viewer : dossier absent dit clairement", etat)
        await pv.evaluate("window.__au.updateAudioList({ folder: '' })"); await pv.wait_for_timeout(200)
        etat = await pv.evaluate("document.getElementById('stat').textContent")
        rapport("nom du dossier" in etat, "viewer : dossier non renseigne dit clairement", etat)
        rapport(not ev, "viewer : aucune erreur JavaScript", ev)
        await br.close()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
