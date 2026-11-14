#!/usr/bin/env python3
"""Test 1.10.26 : mer automatique (Chromium) : le niveau d'eau de l'OAR devient la hauteur de la mer des pages, en repere de la region (seaM).

oar2glb.py inscrit le WaterHeight de l'OAR (ou 20 par defaut, avec un avertissement) dans asset.extras du GLB ; glb2tiles.py le reprend dans l'index des tuiles ;
glb2html.py en fait la cle seaM de la config (sauf --sea-y explicite ; --sea-m et --water-from priment) ; la page place la mer a seaM + decalage du modele ;
le curseur de Reglages part de cette valeur, le choix du visiteur la remplace, « Valeurs d'origine » y revient. --update --water-from corrige une region deja
convertie (seaY de la page garde) ; --update --sea-y retire seaM ; les pages anciennes (seaY seul) ne changent pas. Mode tuiles : repere d'origine, sans decalage.
Non teste ici : vrai navigateur graphique, Edge, Windows.

Prerequis : pip install playwright pillow ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/mer_auto.py
"""
import asyncio, io, json, os, shutil, sys, tarfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

DECAL = 15.0        # sol_glb : un seul mesh d'origine (0, 0, 0) : le viewer le decale de +15 en hauteur
MER_Y = "window.__viewer.sea ? window.__viewer.sea.position.y : null"
LIGNE = """(t) => { const l = [...document.querySelectorAll('#optsPanel label')].find(x => x.textContent.includes(t));
  if (!l) return null; const r = l.querySelector('input'); return { valeur: parseFloat(r.value), grise: r.disabled, texte: l.textContent.trim() }; }"""
REGLER = """([t, v]) => { const r = [...document.querySelectorAll('#optsPanel label')].find(x => x.textContent.includes(t)).querySelector('input');
  r.value = v; r.dispatchEvent(new Event('input', { bubbles: true })); }"""
CLIC = "([panneau, texte]) => [...document.querySelectorAll('#optsPanel ' + panneau)].find(x => x.textContent.includes(texte)).%s"


def pad4(b, c=b"\x00"):
    return b + c * ((4 - len(b) % 4) % 4)


def lire_glb(p):
    d = pathlib.Path(p).read_bytes()
    ln = struct.unpack_from("<I", d, 12)[0]
    return json.loads(d[20:20 + ln].decode("utf-8")), d[28 + ln:]


def ecrire_glb(p, g, blob):
    js = pad4(json.dumps(g).encode("utf-8"), b" ")
    blob = pad4(blob)
    pathlib.Path(p).write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js
                                + struct.pack("<I4s", len(blob), b"BIN\x00") + blob)


def avec_eau(src, dst, eau):
    g, blob = lire_glb(src)
    g.setdefault("asset", {})["extras"] = {"waterHeight": eau, "waterSource": "oar"}
    ecrire_glb(dst, g, blob)


def faire_oar(chemin, eau=None):
    with tarfile.open(chemin, "w:gz") as t:
        for nom, data in (("archive.xml", b"<archive><region_info><size_in_meters>256,256</size_in_meters></region_info></archive>"),
                          ) + ((("settings/Region.xml", ("<RegionSettings><General><WaterHeight>%s</WaterHeight></General></RegionSettings>" % eau).encode()),) if eau is not None else ()):
            ti = tarfile.TarInfo(nom); ti.size = len(data); t.addfile(ti, io.BytesIO(data))


def config(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


FAKE = '''#!/usr/bin/env python3
import sys, shutil, pathlib
a = sys.argv[1:]
out = pathlib.Path(a[a.index("--outputdir") + 1]); out.mkdir(exist_ok=True)
for f in pathlib.Path(__file__).with_name("fake_out").iterdir():
    shutil.copy(f, out / f.name)
print("fake convoar")
'''
zone = tmp / "convoar"; zone.mkdir(); fo = zone / "fake_out"; fo.mkdir()
(fo / "scene.bin").write_bytes(struct.pack("<9f", 0, 20, 0, 1, 20, 0, 0, 21, 0))
(fo / "scene.gltf").write_text(json.dumps({
    "asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0, "name": "Boite"}], "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "material": 0}]}],
    "materials": [{"pbrMetallicRoughness": {}}], "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3", "min": [0, 20, 0], "max": [1, 21, 0]}],
    "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36}], "buffers": [{"byteLength": 36, "uri": "scene.bin"}]}), encoding="utf-8")
fake = zone / "convoar_fake.py"; fake.write_text(FAKE); fake.chmod(0o755)


def convertir(nom, eau):
    d = tmp / nom; d.mkdir()
    oar = d / "R.oar"; faire_oar(oar, eau)
    r = run(DIST / "oar2glb.py", oar, "--convoar", fake, "--nopause", "--no-pbr")
    return r, oar.with_suffix(".glb")


print("--- 0. oar2glb : le niveau d'eau de l'OAR est inscrit dans le GLB")
r, glb_eau = convertir("c_eau", 9)
g, _ = lire_glb(glb_eau)
rapport((g["asset"].get("extras") or {}) == {"waterHeight": 9.0, "waterSource": "oar"}, "OAR avec WaterHeight 9 : asset.extras = waterHeight 9.0, source oar", g["asset"])
rapport("[eau] niveau d'eau de la région : 9 m (lu dans settings/Region.xml)" in r.stdout and "ATTENTION" not in r.stdout, "compte rendu : niveau 9 m lu dans settings/Region.xml, pas d'avertissement", r.stdout[-400:])
r, glb_def = convertir("c_def", None)
g, _ = lire_glb(glb_def)
rapport((g["asset"].get("extras") or {}) == {"waterHeight": 20.0, "waterSource": "default"} and "ATTENTION : l'OAR n'a pas de WaterHeight" in r.stdout, "OAR sans WaterHeight : 20.0, source default, avertissement visible", (g["asset"], r.stdout[-300:]))
r = run(DIST / "oar2glb.py", "--tex-only", glb_eau, "--tex-size", "128", "--output", tmp / "c_eau" / "R-tex.glb", ok=False)
rapport(not (tmp / "c_eau" / "R-tex.glb").exists() or (lire_glb(tmp / "c_eau" / "R-tex.glb")[0]["asset"].get("extras") or {}).get("waterHeight") == 9.0, "--tex-only : le niveau d'eau du GLB est conserve (ou rien d'ecrit quand rien ne change)")

print("--- 1. glb2tiles : l'index des tuiles garde le niveau d'eau")
site0 = tmp / "pages"; site0.mkdir()
sol_glb(site0 / "sol.glb")
avec_eau(site0 / "sol.glb", site0 / "eau.glb", 9.0)
tuiles = tmp / "tuiles"; tuiles.mkdir(); shutil.copy(site0 / "eau.glb", tuiles / "eau.glb")
run(DIST / "glb2tiles.py", tuiles / "eau.glb", "--force", "--nopause")
doc = json.loads((tuiles / "eau.tiles.json").read_text(encoding="utf-8"))
rapport(doc.get("waterHeight") == 9.0, "eau.tiles.json : waterHeight 9.0", {k: doc[k] for k in doc if k != "tiles"})
shutil.copy(site0 / "sol.glb", tuiles / "sol.glb")
run(DIST / "glb2tiles.py", tuiles / "sol.glb", "--force", "--nopause")
rapport("waterHeight" not in json.loads((tuiles / "sol.tiles.json").read_text(encoding="utf-8")), "GLB sans niveau d'eau : pas de waterHeight dans l'index")

print("--- 2. glb2html : la cle seaM")
r = html(site0 / "eau.glb", "-o", site0 / "Auto.html", "--target", "0,0,0")
rapport("mer automatique : niveau d'eau 9 m lu dans le GLB" in r.stdout, "page autonome : message « mer automatique »", r.stdout[-300:])
html(site0 / "eau.glb", "-o", site0 / "Y10.html", "--sea-y", "10", "--target", "0,0,0")
r = html(site0 / "eau.glb", "-o", site0 / "M12.html", "--sea-m", "12", "--target", "0,0,0")
html(site0 / "sol.glb", "-o", site0 / "Sans.html", "--target", "0,0,0")
ts = {n: (site0 / n).read_text(encoding="utf-8") for n in ("Auto.html", "Y10.html", "M12.html", "Sans.html")}
rapport('"seaM": 9.0' in ts["Auto.html"] and '"seaM"' not in ts["Y10.html"] and '"seaM": 12.0' in ts["M12.html"] and '"seaM"' not in ts["Sans.html"], "config embarquee : seaM 9.0 (auto), absent avec --sea-y et sans niveau d'eau, 12.0 avec --sea-m")

print("--- 3. la page : repere de la region + decalage du modele")
http, hport = serveur(site0)
BASE = f"http://127.0.0.1:{hport}/"


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        o = await Onglet(br).ouvrir(BASE + "Auto.html", locale="fr-FR")
        decal = await o.ev("window.__viewer.seaShift()")
        rapport(abs(decal - DECAL) < 1e-6 and await o.ev("window.__viewer.cfg.seaM") == 9.0 and await o.ev("window.__viewer.cfg.seaY") == -50.0, "page auto : seaM 9, seaY inchange (-50), decalage +15", (decal, await o.ev("window.__viewer.cfg.seaM")))
        rapport(abs(await o.ev(MER_Y) - (9 + DECAL)) < 1e-6, "mer a 9 + 15 = 24 dans la scene (niveau d'eau de l'OAR, repere de la region)", await o.ev(MER_Y))
        await o.ev("document.getElementById('optsBtn').click()")
        e = await o.ev(LIGNE, "Hauteur de la mer")
        rapport(e is not None and abs(e["valeur"] - 9) < 0.01 and "9.0 m" in e["texte"], "curseur de Reglages : part de 9.0 m (la meme valeur que dans la config)", e)
        await o.ev(REGLER, ["Hauteur de la mer", 20])
        rapport(abs(await o.ev(MER_Y) - 35) < 1e-6, "le visiteur deplace le curseur a 20 m : mer a 35 dans la scene")
        await o.pg.reload(); await o.attendre("window.__viewer && document.getElementById('msg') === null", 40)
        rapport(abs(await o.ev(MER_Y) - 35) < 1e-6, "apres rechargement : le choix du visiteur remplace seaM (35)")
        await o.ev("document.getElementById('optsBtn').click()")
        await o.ev(CLIC % "click()", ["button", "Valeurs d'origine"])
        e = await o.ev(LIGNE, "Hauteur de la mer")
        rapport(abs(await o.ev(MER_Y) - 24) < 1e-6 and abs(e["valeur"] - 9) < 0.01, "« Valeurs d'origine » : retour au niveau de la page (seaM 9 : 24 dans la scene, curseur 9.0 m)", (await o.ev(MER_Y), e))
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()

        o = await Onglet(br).ouvrir(BASE + "Y10.html", locale="fr-FR")
        rapport(abs(await o.ev(MER_Y) - 10) < 1e-6 and await o.ev("window.__viewer.cfg.seaM") in (None,), "--sea-y 10 explicite : pas de mer automatique, mer a 10 (ancien comportement)", (await o.ev(MER_Y), await o.ev("window.__viewer.cfg.seaM")))
        await o.ctx.close()
        o = await Onglet(br).ouvrir(BASE + "M12.html", locale="fr-FR")
        rapport(abs(await o.ev(MER_Y) - 27) < 1e-6, "--sea-m 12 : prime sur le niveau d'eau du GLB (9) : mer a 12 + 15 = 27", await o.ev(MER_Y))
        await o.ctx.close()
        o = await Onglet(br).ouvrir(BASE + "Sans.html", locale="fr-FR")
        rapport(abs(await o.ev(MER_Y) - (-50)) < 1e-6, "GLB sans niveau d'eau : comportement inchange (mer a seaY -50)", await o.ev(MER_Y))
        await o.ctx.close()

        print("--- 4. region deja convertie : --update --water-from (cas d'une page avec seaY 20 : repere de la page)")
        site = tmp / "site"; site.mkdir()
        sol_glb(site / "sol.glb")
        reg = site / "Reg"; reg.mkdir()
        shutil.copy(site / "sol.glb", reg / "Reg.glb")
        r = html(reg / "Reg.glb", "--shared-shell", site / "index.html", "-o", reg / "Reg.html", "--sea-y", "20", "--target", "0,0,0")
        c0 = config(reg / "Reg.config.json")
        rapport("seaM" not in c0 and c0["seaY"] == 20.0, "region de depart (comme celle de la boutique) : seaY 20, pas de seaM", {k: c0[k] for k in c0 if k.startswith("sea")})
        http2, p2 = serveur(site)
        U = f"http://127.0.0.1:{p2}/index.html?region=Reg/Reg"
        o = await Onglet(br).ouvrir(U, locale="fr-FR")
        rapport(abs(await o.ev(MER_Y) - 20) < 1e-6, "avant la correction : mer a seaY 20 dans la scene", await o.ev(MER_Y))
        await o.ctx.close()
        oar7 = tmp / "sept.oar"; faire_oar(oar7, 7)
        r = html("--update", "-o", reg / "Reg.html", "--shared-shell", site / "index.html", "--water-from", oar7)
        c1 = config(reg / "Reg.config.json")
        rapport(c1.get("seaM") == 7.0 and c1["seaY"] == 20.0 and "niveau d'eau 7 m lu dans settings/Region.xml (écrit en seaM)" in r.stdout, "--update --water-from : seaM 7.0 ecrit, seaY 20 garde, message", (c1.get("seaM"), c1["seaY"], r.stdout[-300:]))
        o = await Onglet(br).ouvrir(U, locale="fr-FR")
        rapport(abs(await o.ev(MER_Y) - (7 + DECAL)) < 1e-6, "region corrigee : mer a 7 + 15 = 22 dans la scene", await o.ev(MER_Y))
        await o.ctx.close()
        html("--update", "-o", reg / "Reg.html", "--shared-shell", site / "index.html", "--wave", "1")
        rapport(config(reg / "Reg.config.json").get("seaM") == 7.0, "--update d'une autre option : seaM conserve")
        html("--update", "-o", reg / "Reg.html", "--shared-shell", site / "index.html", "--sea-m", "5")
        rapport(config(reg / "Reg.config.json").get("seaM") == 5.0, "--update --sea-m 5 : seaM 5.0")
        r = html("--update", "-o", reg / "Reg.html", "--shared-shell", site / "index.html", "--sea-y", "12")
        c2 = config(reg / "Reg.config.json")
        rapport("seaM" not in c2 and c2["seaY"] == 12.0, "--update --sea-y 12 : seaM retire, la mer revient au repere de la page (seaY 12)", (c2.get("seaM"), c2["seaY"], r.stdout[-300:]))
        o = await Onglet(br).ouvrir(U, locale="fr-FR")
        rapport(abs(await o.ev(MER_Y) - 12) < 1e-6, "mer a 12 dans la scene apres --sea-y", await o.ev(MER_Y))
        await o.ctx.close()
        r = html("--update", "-o", reg / "Reg.html", "--shared-shell", site / "index.html", "--water-from", tmp / "c_def" / "R.oar", ok=False)
        rapport(r.returncode != 0 and "aucun WaterHeight dans les fichiers settings/" in (r.stdout + r.stderr), "--water-from sur un OAR sans WaterHeight : refuse avec un message clair", (r.returncode, (r.stdout + r.stderr)[-300:]))
        r = html("--update", "-o", reg / "Reg.html", "--shared-shell", site / "index.html", "--water-from", reg / "Reg.glb", ok=False)
        rapport(r.returncode != 0 and "n'est pas une archive OAR lisible" in (r.stdout + r.stderr), "--water-from sur un fichier qui n'est pas un OAR : refuse avec un message clair", (r.returncode, (r.stdout + r.stderr)[-300:]))
        http2.kill()

        print("--- 5. coquille commune : un GLB converti par oar2glb donne seaM tout seul")
        site3 = tmp / "site3"; (site3 / "Auto").mkdir(parents=True)
        shutil.copy(glb_eau, site3 / "Auto" / "Auto.glb")
        r = html(site3 / "Auto" / "Auto.glb", "--shared-shell", site3 / "index.html", "-o", site3 / "Auto" / "Auto.html")
        c3 = config(site3 / "Auto" / "Auto.config.json")
        rapport(c3.get("seaM") == 9.0 and "mer automatique : niveau d'eau 9 m lu dans le GLB" in r.stdout, "GLB d'oar2glb (eau 9) : seaM 9.0 dans la config de la region", (c3.get("seaM"), r.stdout[-300:]))
        http3, p3 = serveur(site3)
        o = await Onglet(br).ouvrir(f"http://127.0.0.1:{p3}/index.html?region=Auto/Auto", locale="fr-FR")
        sh = await o.ev("window.__viewer.seaShift()")
        rapport(abs(await o.ev(MER_Y) - (9 + sh)) < 1e-6, "la page de la region place la mer a 9 + decalage du modele", (await o.ev(MER_Y), sh))
        await o.ctx.close()
        http3.kill()

        print("--- 6. mode tuiles : niveau d'eau de l'index, repere de la region (aucun decalage)")
        site4 = tmp / "site4"; (site4 / "T").mkdir(parents=True)
        for f in tuiles.iterdir():
            if f.name.startswith("eau."):
                (shutil.copytree if f.is_dir() else shutil.copy)(f, site4 / "T" / f.name)
        r = html("--tiles", site4 / "T" / "eau.tiles.json", "--shared-shell", site4 / "index.html", "-o", site4 / "T" / "T.html")
        c4 = config(site4 / "T" / "T.config.json")
        rapport(c4.get("seaM") == 9.0 and "mer automatique : niveau d'eau 9 m lu dans l'index des tuiles" in r.stdout, "tuiles : seaM 9.0 pris dans l'index, message", (c4.get("seaM"), c4.get("seaY"), r.stdout[-300:]))
        http4, p4 = serveur(site4)
        o = await Onglet(br).ouvrir(f"http://127.0.0.1:{p4}/index.html?region=T/T", locale="fr-FR")
        await o.attendre("window.__viewer && window.__viewer.sea", 40)
        rapport(abs(await o.ev(MER_Y) - 9) < 1e-6 and abs(await o.ev("window.__viewer.seaShift()")) < 1e-9, "page en tuiles : mer a 9 dans la scene (decalage 0)", (await o.ev(MER_Y), await o.ev("window.__viewer.seaShift()")))
        await o.ctx.close()
        http4.kill()

        print("--- 7. textes")
        for lang, attendu in (("fr", ("--sea-m", "--water-from", "repère de la page")), ("en", ("--sea-m", "--water-from", "page's frame"))):
            r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), "--help", "--lang", lang], capture_output=True, text=True, encoding="utf-8", errors="replace",
                               env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1"), stdin=subprocess.DEVNULL, cwd=tmp)
            aide = " ".join(r.stdout.split())
            rapport(all(k in aide for k in attendu) and "py.glb2html" not in aide, f"aide de glb2html.py ({lang}) : --sea-m, --water-from, et --sea-y dit qu'il est dans le repere de la page", [k for k in attendu if k not in aide])
        await br.close()


try:
    asyncio.run(main())
finally:
    http.kill()
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
