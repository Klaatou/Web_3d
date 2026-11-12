#!/usr/bin/env python3
"""Test 1.10.7 : reflets metalliques (Chromium).

Pourquoi : un materiau metallique (metalness 1) ne recoit pas la lumiere d'ambiance, il ne reflete que son environnement, et la scene n'en avait pas :
les metaux PBR d'OpenSim etaient bien plus sombres dans la page que dans Blender (mesure : sphere grise metallique de rugosite 0,7 : 52 sur 255 vue de face, la meme non metallique 114).
Le viewer donne maintenant un petit environnement filtre aux SEULS materiaux metalliques ; cfg.metalEnv (%) regle l'intensite, 0 = aucun reflet et aucun cout (defaut ; mesure : une surface metallique avec reflets coute environ 3 fois plus par image sous SwiftShader) ; la page PROPOSE 60 % quand elle voit des metaux (section 8, 1.10.10) ;
un curseur « Reflets metalliques » de Reglages le regle.

Verifie : trois spheres (non metallique, metallique rugosite 0,7, metallique rugosite 0,3) ; materiaux metalliques avec envMap et intensite 0,6, le non metallique
sans environnement ; clarte mesuree sur une capture d'ecran (un metal a au moins 1,6 fois sa clarte sans reflet, le non metallique ne bouge pas, a 200 % plus clair qu'a 60 %) ;
le curseur (valeur de depart, 0 = aucun reflet, retenu apres rechargement, « Valeurs d'origine ») ; l'environnement partage survit au remplacement du modele ;
mode tuiles : les materiaux metalliques des tuiles ont l'environnement ; la proposition (oui, non, curseur, region sans metal, tuiles, anglais) ; francais et anglais ; aucune erreur de page.
Vrai navigateur graphique, Edge, Windows et comparaison avec Blender ou un viewer OpenSim : non testes ici.

Prerequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/reflets_metal.py
"""
import asyncio, base64, json, math, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37


def spheres_glb(chemin, metal=True):
    """trois spheres de rayon 1 (normales justes), alignees sur x : non metallique, metallique rugosite 0,7, metallique rugosite 0,3"""
    nlat, nlon = 16, 24
    pos, nor, idx = [], [], []
    for i in range(nlat + 1):
        th = math.pi * i / nlat
        for j in range(nlon + 1):
            ph = 2 * math.pi * j / nlon
            n = (math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph))
            pos.append(n)
            nor.append(n)
    for i in range(nlat):
        for j in range(nlon):
            a = i * (nlon + 1) + j
            b = a + nlon + 1
            if i > 0:
                idx += [a, b, a + 1]      # aux poles les deux rangees de sommets se confondent : pas de triangle d'aire nulle
            if i < nlat - 1:
                idx += [a + 1, b, b + 1]
    blob = b"".join(struct.pack("<3f", *p) for p in pos) + b"".join(struct.pack("<3f", *n) for n in nor) + struct.pack("<%dH" % len(idx), *idx)
    blob += b"\0" * (-len(blob) % 4)
    npos = len(pos)
    mats = [(0.0, 0.7), (1.0, 0.7), (1.0, 0.3)] if metal else [(0.0, 0.7)] * 3
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": npos * 12, "target": 34962},
                         {"buffer": 0, "byteOffset": npos * 12, "byteLength": npos * 12, "target": 34962},
                         {"buffer": 0, "byteOffset": npos * 24, "byteLength": len(idx) * 2, "target": 34963}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": npos, "type": "VEC3", "min": [-1, -1, -1], "max": [1, 1, 1]},
                       {"bufferView": 1, "componentType": 5126, "count": npos, "type": "VEC3"},
                       {"bufferView": 2, "componentType": 5123, "count": len(idx), "type": "SCALAR"}],
         "materials": [{"name": f"M{i}", "pbrMetallicRoughness": {"baseColorFactor": [0.43, 0.43, 0.43, 1], "metallicFactor": m, "roughnessFactor": r}} for i, (m, r) in enumerate(mats)],
         "meshes": [{"name": f"S{i}", "primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1}, "indices": 2, "material": i}]} for i in range(3)],
         "nodes": [{"name": f"S{i}", "mesh": i, "translation": [(i - 1) * 2.6, 1, 0]} for i in range(3)], "scenes": [{"nodes": [0, 1, 2]}], "scene": 0}
    js = json.dumps(g).encode()
    js += b" " * (-len(js) % 4)
    chemin.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


print("--- 0. fabrication des pages")
site = tmp / "site"; site.mkdir()
src = tmp / "src"; src.mkdir()
spheres_glb(site / "metal.glb")
spheres_glb(site / "plat.glb", metal=False)      # trois spheres sans aucun metal
spheres_glb(src / "Metal.glb")
html(site / "metal.glb", "-o", site / "Metal.html", "--no-sea")
html(site / "plat.glb", "-o", site / "Plat.html", "--no-sea")
html(site / "plat.glb", "-o", site / "PlatMer.html")                      # 1.10.14 : avec la mer (animee par defaut)
html(site / "plat.glb", "-o", site / "PlatMerFixe.html", "--no-anim")     # 1.10.14 : mer non animee = materiau standard, metalness 0,1
run(DIST / "glb2tiles.py", src / "Metal.glb", "--forcer", "--budget-tri", "700", "--min", "4", "--nopause", "--sans-references")
html("-o", site / "Tuilee.html", "--shared-shell", "--tiles", src / "Metal.tiles.json", "--no-sea")
http, hport = serveur(site)
BASE = f"http://127.0.0.1:{hport}/"

# clarte moyenne (0 a 255) autour du centre de chaque sphere, lue sur une capture d'ecran de la page (ce que voit le visiteur)
CENTRES = """() => { const v = window.__viewer, R = v.renderer.domElement.getBoundingClientRect(), out = []; v.camera.updateMatrixWorld();
  for (const nom of ['S0', 'S1', 'S2']) { let m = null; v.scene.traverse(o => { if (o.isMesh && (o.name === nom || (o.parent && o.parent.name === nom))) m = o; });
    const p = m.getWorldPosition(new v.camera.position.constructor()); p.project(v.camera); out.push([R.left + (p.x + 1) / 2 * R.width, R.top + (1 - p.y) / 2 * R.height]); }
  return { centres: out, w: innerWidth, h: innerHeight }; }"""
MOYENNE = """async (b64) => { const img = new Image(); img.src = 'data:image/png;base64,' + b64; await img.decode(); const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
  const g = c.getContext('2d'); g.drawImage(img, 0, 0); const d = g.getImageData(0, 0, c.width, c.height).data; let s = 0; for (let i = 0; i < d.length; i += 4) s += (d[i] + d[i + 1] + d[i + 2]) / 3; return s / (d.length / 4); }"""


async def clarte(o):
    """[clarte de S0, S1, S2] ; attend qu'une image soit redessinee ; les trois spheres doivent etre dans la fenetre (sinon la mesure ne vaut rien)"""
    await asyncio.sleep(0.6)
    c = await o.ev(CENTRES)
    assert all(6 < x < c["w"] - 6 and 6 < y < c["h"] - 6 for x, y in c["centres"]), ("sphere hors de la fenetre", c)
    out = []
    for x, y in c["centres"]:
        png = await o.pg.screenshot(clip={"x": x - 6, "y": y - 6, "width": 12, "height": 12})
        out.append(await o.ev(MOYENNE, base64.b64encode(png).decode()))
    return out


MATS = """() => { const r = {}; window.__viewer.scene.traverse(o => { if (o.isMesh) { const m = Array.isArray(o.material) ? o.material[0] : o.material;
  const k = o.name || (o.parent && o.parent.name) || '?'; r[k] = { metal: m.metalness, env: !!m.envMap, k: m.envMapIntensity }; } }); return r; }"""
METAUX = """() => { const r = []; window.__viewer.scene.traverse(o => { if (o.isMesh) for (const m of (Array.isArray(o.material) ? o.material : [o.material]))
  if (m && m.isMeshStandardMaterial && m.metalness > 0.5) r.push({ env: !!m.envMap, k: m.envMapIntensity, tuile: !!(o.parent && o.parent.name) }); }); return r; }"""
LIGNE = """(t) => { const l = [...document.querySelectorAll('#optsPanel label')].find(x => x.textContent.includes(t));
  if (!l) return null; const r = l.querySelector('input'); return { valeur: parseFloat(r.value), texte: l.textContent.trim() }; }"""
REGLER = """([t, v]) => { const r = [...document.querySelectorAll('#optsPanel label')].find(x => x.textContent.includes(t)).querySelector('input');
  r.value = v; r.dispatchEvent(new Event('input', { bubbles: true })); }"""
PRET = "window.__viewer && document.getElementById('msg') === null"


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)

        print("--- 1. materiaux : seuls les metaux recoivent l'environnement")
        o = await Onglet(br).ouvrir(BASE + "Metal.html", locale="fr-FR")
        rapport(await o.ev("window.__viewer.cfg.metalEnv") == 0 and not await o.ev("window.__viewer.metalEnvReady()") and not any(x["env"] for x in (await o.ev(MATS)).values()),
                "reflets a 0 % par defaut : aucun environnement cree, aucun cout (la page propose de les activer, voir la section 8)")
        await o.ev("window.__viewer.setCfg({ metalEnv: 60 })")
        m = await o.ev(MATS)
        rapport(all(m[k]["env"] and abs(m[k]["k"] - 0.6) < 1e-9 for k in ("S1", "S2")) and not m["S0"]["env"], "reflets a 60 % : metaux avec envMap et intensite 0,6 ; non metallique : aucun environnement", m)

        print("--- 2. clarte mesuree sur l'image")
        c60 = await clarte(o)
        await o.ev("window.__viewer.setCfg({ metalEnv: 0 })")
        c0 = await clarte(o)
        m = await o.ev(MATS)
        rapport(not any(x["env"] for x in m.values()), "metalEnv = 0 : plus aucun environnement sur aucun materiau", m)
        rapport(min(c60 + c0) > 10, "la mesure est valable : les trois spheres se voient (clarte > 10 sur 255)", (c60, c0))
        rapport(c60[1] >= 1.6 * c0[1] and c60[2] >= 1.6 * c0[2], "metaux : au moins 1,6 fois plus clairs avec les reflets qu'avec 0 %", (c60, c0))
        rapport(abs(c60[0] - c0[0]) <= 1.0, "le materiau non metallique ne change pas (a 1 pres)", (c60[0], c0[0]))
        rapport(c60[2] > c60[1] > 2 * c0[1], "a 60 % : le metal rugueux est plus de 2 fois plus clair que sans reflet, le brillant (rugosite 0,3) reste le plus clair (point lumineux)", (c60, c0))
        await o.ev("window.__viewer.setCfg({ metalEnv: 200 })")
        c200 = await clarte(o)
        rapport(c200[1] > c60[1] and c200[2] > c60[2] and abs(c200[0] - c60[0]) <= 1.0, "a 200 % les metaux sont plus clairs qu'a 60 %, le non metallique pareil", (c200, c60))
        await o.ev("window.__viewer.setCfg({ metalEnv: 60 })")

        print("--- 3. l'environnement partage survit au remplacement du modele")
        await o.ev("async () => { const b = await (await fetch('metal.glb')).arrayBuffer(); await window.__viewer.loadBuffer(b); }")
        c_apres = await clarte(o)
        m = await o.ev(MATS)
        rapport(all(m[k]["env"] for k in ("S1", "S2")) and c_apres[1] >= 1.6 * c0[1] and c_apres[2] >= 1.6 * c0[2], "apres un nouveau modele (l'ancien est libere) : les metaux ont toujours leurs reflets", (c_apres, c0, m))
        rapport(not o.errs, "aucune erreur de page", o.errs)

        print("--- 4. le curseur « Reflets metalliques » de Reglages")
        await o.pg.reload(); await o.attendre(PRET, 40)      # etat neuf : la valeur de la page, sans le reglage fait par l'API
        await o.ev("document.getElementById('optsBtn').click()")
        e = await o.ev(LIGNE, "Reflets métalliques")
        rapport(e is not None and abs(e["valeur"] - 0) < 0.01 and "0 %" in e["texte"], "curseur present, valeur de depart 0 % (rendu logiciel)", e)
        await o.ev(REGLER, ["Reflets métalliques", 60])
        e = await o.ev(LIGNE, "Reflets métalliques")
        m = await o.ev(MATS)
        rapport("60 %" in e["texte"] and all(m[k]["env"] and abs(m[k]["k"] - 0.6) < 1e-9 for k in ("S1", "S2")), "curseur a 60 % : les metaux recoivent l'environnement", (e, m))
        await o.ev(REGLER, ["Reflets métalliques", 0])
        e = await o.ev(LIGNE, "Reflets métalliques")
        m = await o.ev(MATS)
        c = await clarte(o)
        rapport("0 %" in e["texte"] and not any(x["env"] for x in m.values()) and c[1] <= 1.2 * c0[1], "curseur a 0 % : plus de reflets, metaux revenus a leur clarte d'avant", (e, c, c0))
        await o.ev(REGLER, ["Reflets métalliques", 140])
        m = await o.ev(MATS)
        rapport(all(m[k]["env"] and abs(m[k]["k"] - 1.4) < 1e-9 for k in ("S1", "S2")), "curseur a 140 % : intensite 1,4", m)
        st = json.loads(await o.ev("localStorage.getItem(Object.keys(localStorage).find(k => k.startsWith('glb2html_opts_')))"))
        rapport(st.get("metal") == 140, "le choix est memorise avec les autres reglages", st)
        await o.pg.reload(); await o.attendre(PRET, 40)
        await o.ev("document.getElementById('optsBtn').click()")
        e = await o.ev(LIGNE, "Reflets métalliques")
        m = await o.ev(MATS)
        rapport(abs(e["valeur"] - 140) < 0.01 and all(abs(m[k]["k"] - 1.4) < 1e-9 for k in ("S1", "S2")), "apres rechargement : 140 % reaffiche et applique", (e, m))
        await o.ev("[...document.querySelectorAll('#optsPanel button')].find(x => x.textContent.includes(\"Valeurs d'origine\")).click()")
        e = await o.ev(LIGNE, "Reflets métalliques")
        m = await o.ev(MATS)
        rapport(abs(e["valeur"] - 0) < 0.01 and not any(x["env"] for x in m.values()), "« Valeurs d'origine » : retour a la valeur de la page (0 % en rendu logiciel), plus d'environnement", (e, m))
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()

        print("--- 5. anglais")
        o = await Onglet(br).ouvrir(BASE + "Metal.html", locale="en-US")
        await o.ev("document.getElementById('optsBtn').click()")
        e = await o.ev(LIGNE, "Metal reflections")
        rapport(e is not None and "Metal reflections: 0 %" in e["texte"], "anglais : « Metal reflections: 0 % » (rendu logiciel)", e)
        await o.ctx.close()

        print("--- 6. mode tuiles")
        o = await Onglet(br).ouvrir(BASE + "index.html?region=Tuilee", locale="fr-FR")
        await o.attendre("window.__viewer.tilesState().total > 0 && window.__viewer.tilesState().ready.length > 0", 40)
        await o.attendre("window.__viewer.tilesState().loadingFiles.length === 0", 40)
        mets = await o.ev(METAUX)
        rapport(len(mets) >= 2 and not any(v["env"] for v in mets), "tuiles, rendu logiciel : 0 % par defaut, aucun environnement sur les 2 spheres metalliques au moins", mets)
        await o.ev("window.__viewer.setCfg({ metalEnv: 60 })")
        mets = await o.ev(METAUX)
        rapport(len(mets) >= 2 and all(v["env"] and abs(v["k"] - 0.6) < 1e-9 for v in mets), "tuiles : a 60 % les materiaux metalliques ont l'environnement", mets)
        await o.ev("window.__viewer.setCfg({ metalEnv: 0 })")
        mets = await o.ev(METAUX)
        rapport(len(mets) >= 2 and not any(v["env"] for v in mets), "tuiles : metalEnv = 0 retire l'environnement", mets)
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()

        print("--- 7. ligne « Reflets metalliques » du diagnostic (1.10.8)")
        async def diag(o):
            await o.ev("document.getElementById('diagBtn').click()")
            await o.pg.wait_for_timeout(400)
            return await o.ev("document.getElementById('diagOut').value")
        o = await Onglet(br).ouvrir(BASE + "Metal.html", locale="fr-FR")
        t = await diag(o)
        rapport("Reflets métalliques : 0 % ; matériaux métalliques chargés : 2 sur 3, dont 0 avec reflets" in t, "diagnostic (rendu logiciel, 0 %) : 2 materiaux metalliques sur 3, aucun avec reflets", [l for l in t.splitlines() if "flets" in l])
        await o.ev("window.__viewer.setCfg({ metalEnv: 60 })")
        t = await diag(o)
        rapport("Reflets métalliques : 60 % ; matériaux métalliques chargés : 2 sur 3, dont 2 avec reflets" in t, "a 60 % : 2 materiaux sur 3 ont les reflets", [l for l in t.splitlines() if "flets" in l])
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()
        o = await Onglet(br).ouvrir(BASE + "Metal.html", locale="en-US")
        t = await diag(o)
        rapport("Metal reflections" in t and "0 % ; metallic materials loaded: 2 of 3, of which 0 with reflections" in t, "anglais : « Metal reflections ... 2 of 3 »", [l for l in t.splitlines() if "eflections" in l])
        await o.ctx.close()

        print("--- 8. la page propose les reflets quand elle voit des metaux (1.10.10)")
        BARRE = "document.getElementById('metalAsk') && document.getElementById('metalAskText').textContent"
        SOFT = " Rendu sans carte graphique : cela peut ralentir."      # SwiftShader : rendu logiciel
        o = await Onglet(br).ouvrir(BASE + "Metal.html", locale="fr-FR")
        await o.attendre("!!document.getElementById('metalAsk')", 15)
        texte = await o.ev(BARRE)
        rapport(texte == "Cette région contient 2 matériaux métalliques (PBR). Activer les reflets à 60 % ?" + SOFT, "2 metaux vus, reflets a 0 % : la barre propose 60 % (et previent d'un ralentissement en rendu logiciel)", texte)
        await o.ev("document.getElementById('metalAskYes').click()")
        m = await o.ev(MATS)
        st = json.loads(await o.ev("localStorage.getItem(Object.keys(localStorage).find(k => k.startsWith('glb2html_opts_')))"))
        rapport(not await o.ev("!!document.getElementById('metalAsk')") and abs(await o.ev("window.__viewer.cfg.metalEnv") - 60) < 1e-9 and all(m[k]["env"] for k in ("S1", "S2")) and st.get("metal") == 60,
                "« Oui » : la barre disparait, reflets a 60 % sur les metaux, choix memorise avec les reglages", (m, st))
        await o.pg.reload(); await o.attendre(PRET, 40); await o.pg.wait_for_timeout(2500)
        rapport(not await o.ev("!!document.getElementById('metalAsk')") and abs(await o.ev("window.__viewer.cfg.metalEnv") - 60) < 1e-9, "apres rechargement : pas de nouvelle question, reflets toujours a 60 %")
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()

        o = await Onglet(br).ouvrir(BASE + "Metal.html", locale="fr-FR")
        await o.attendre("!!document.getElementById('metalAsk')", 15)
        await o.ev("document.getElementById('metalAskNo').click()")
        await o.pg.reload(); await o.attendre(PRET, 40); await o.pg.wait_for_timeout(2500)
        rapport(not await o.ev("!!document.getElementById('metalAsk')") and await o.ev("window.__viewer.cfg.metalEnv") == 0, "« Non » : retenu, plus de question au rechargement, reflets a 0 %")
        await o.ctx.close()

        o = await Onglet(br).ouvrir(BASE + "Metal.html", locale="fr-FR")
        await o.attendre("!!document.getElementById('metalAsk')", 15)
        await o.ev("document.getElementById('optsBtn').click()")
        await o.ev(REGLER, ["Reflets métalliques", 25])
        rapport(not await o.ev("!!document.getElementById('metalAsk')"), "toucher au curseur vaut reponse : la barre disparait")
        await o.pg.reload(); await o.attendre(PRET, 40); await o.pg.wait_for_timeout(2500)
        rapport(not await o.ev("!!document.getElementById('metalAsk')") and abs(await o.ev("window.__viewer.cfg.metalEnv") - 25) < 1e-9, "apres rechargement : pas de question, le choix 25 % est repris")
        await o.ev("document.getElementById('optsBtn').click()")
        await o.ev("[...document.querySelectorAll('#optsPanel button')].find(x => x.textContent.includes(\"Valeurs d'origine\")).click()")
        await o.attendre("!!document.getElementById('metalAsk')", 10)
        rapport(await o.ev("window.__viewer.cfg.metalEnv") == 0 and await o.ev("!!document.getElementById('metalAsk')") and await o.ev("Object.keys(localStorage).filter(k => k.startsWith('glb2html_metal_asked_')).length") == 0,
                "« Valeurs d'origine » : reflets a 0 %, la reponse retenue est effacee et la proposition revient")
        await o.ev("document.getElementById('metalAskNo').click()")
        await o.ctx.close()

        o = await Onglet(br).ouvrir(BASE + "Plat.html", locale="fr-FR")
        await o.pg.wait_for_timeout(5000)
        rapport(not await o.ev("!!document.getElementById('metalAsk')") and await o.ev("window.__viewer.metalInfo().metal") == 0, "region sans metal : aucune proposition")
        await o.ctx.close()
        for nom_m, titre_m in (("PlatMer.html", "avec la mer"), ("PlatMerFixe.html", "avec la mer non animee")):      # 1.10.14 : la mer n'est pas un materiau de la region
            o = await Onglet(br).ouvrir(BASE + nom_m, locale="fr-FR")
            await o.pg.wait_for_timeout(5000)
            if nom_m == "PlatMerFixe.html":
                rapport(await o.ev("(() => { let n = 0; window.__viewer.scene.traverse(x => { if (x.isMesh && x.material && x.material.isMeshStandardMaterial && x.material.metalness > 0.05) n++; }); return n; })()") >= 1, "mer non animee : la scene a bien un materiau standard de metalness > 0,05 (la mer)")
            rapport(not await o.ev("!!document.getElementById('metalAsk')") and await o.ev("window.__viewer.metalInfo().metal") == 0, f"region sans metal {titre_m} : aucune proposition, aucun materiau metallique compte")
            await o.ctx.close()

        o = await Onglet(br).ouvrir(BASE + "Metal.html", locale="en-US")
        await o.attendre("!!document.getElementById('metalAsk')", 15)
        texte = await o.ev(BARRE)
        rapport(texte == "This region contains 2 metallic (PBR) materials. Turn on the reflections at 60 %? Rendering without a graphics card: this may slow things down.", "anglais : texte de la proposition", texte)
        await o.ctx.close()

        o = await Onglet(br).ouvrir(BASE + "index.html?region=Tuilee", locale="fr-FR")
        await o.attendre("window.__viewer.tilesState().total > 0 && window.__viewer.tilesState().ready.length > 0", 40)
        await o.attendre("!!document.getElementById('metalAsk')", 20)
        await o.ev("document.getElementById('metalAskYes').click()")
        mets = await o.ev(METAUX)
        rapport(len(mets) >= 2 and all(v["env"] for v in mets), "mode tuiles : la proposition apparait quand les tuiles metalliques sont chargees ; « Oui » donne les reflets", mets)
        await o.ctx.close()
        await br.close()


try:
    asyncio.run(main())
finally:
    http.kill()
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
