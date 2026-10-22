#!/usr/bin/env python3
"""Tests v31 : images invalides remplacées (glb2tiles), sortie de promenade (F), vue d'ensemble légère (X.overview.glb).

Hors navigateur : image de 0 octet / tronquée / autre format remplacée par un seul PNG gris par tuile (matériaux et UV inchangés, compteurs dans
--analyse, le rapport et X.tiles.json) ; vue d'ensemble : un nœud par tuile, aucune image, un matériau, couleurs (moyenne de texture avec Pillow,
couleur de base sans), terrain sans fente ni écart de hauteur, objets petits / translucides / à squelette omis, budgets respectés, chaque primitive
unique simplifiée une seule fois (instances multiples), lecture par morceaux, option --vue-ensemble-seule, tuiles d'une exécution précédente retirées.
Navigateur (Chromium sans tête) : toutes les images des tuiles se décodent (les images d'origine cassées échouent : témoin), aucune erreur
« Couldn't load texture » ; sortie de promenade (cible sous l'avatar, même décalage de caméra, avec et sans tuiles, tuiles autour de l'avatar conservées) ;
vue d'ensemble dans la coquille : une cellule masquée si et seulement si sa tuile est affichée, cadrage de toute la région, double-clic sur la vue d'ensemble,
information à part, panne de la vue d'ensemble sans conséquence, ancien X.tiles.json sans vue d'ensemble, jamais utilisée pour le sol.

Prérequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v31.py
"""
import asyncio, importlib.util, json, math, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import glbfab
from glbfab import hauteur, couleur_sol

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST, DATA = ROOT / "dist", ROOT / "tests" / "data"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_v31_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


def run(script, *a, ok=True, cwd=None, env=None):
    r = subprocess.run([sys.executable, str(script), *map(str, a)], capture_output=True, text=True, cwd=cwd or tmp, env=env)
    if ok and r.returncode:
        sys.exit(f"[ECHEC] {script.name} {' '.join(map(str, a))}\n{r.stdout}{r.stderr}")
    return r


def tuiles(glb, *opts, ok=True, script=None, env=None):
    return run(script or DIST / "glb2tiles.py", glb, "--nopause", *opts, ok=ok, env=env)


def lire_glb(chemin):
    d = pathlib.Path(chemin).read_bytes()
    n = struct.unpack("<I", d[12:16])[0]
    js = json.loads(d[20:20 + n])
    bn = struct.unpack("<I", d[20 + n:24 + n])[0] if len(d) > 20 + n else 0
    return js, d[28 + n:28 + n + bn]


def png_ok(d):
    """Indépendant de l'outil : PNG complet (blocs chaînés jusqu'à IEND)."""
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        return False
    p = 8
    while p + 12 <= len(d):
        ln, typ = struct.unpack(">I4s", d[p:p + 8])
        p += 12 + ln
        if typ == b"IEND":
            return p <= len(d)
    return False


def image_octets(js, bn, i):
    bv = js["bufferViews"][js["images"][i]["bufferView"]]
    return bn[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]]


def lire_prims(js, bn):
    """Pour chaque primitive : (positions [(x,y,z)], couleurs [(r,v,b,a)] ou None, triangles [(a,b,c)])."""
    out = []
    for m in js.get("meshes", []):
        for pr in m["primitives"]:
            def acc(i):
                a = js["accessors"][i]
                bv = js["bufferViews"][a["bufferView"]]
                return a, bn[bv.get("byteOffset", 0) + a.get("byteOffset", 0):]
            a, d = acc(pr["attributes"]["POSITION"])
            pos = [struct.unpack_from("<3f", d, 12 * k) for k in range(a["count"])]
            col = None
            if "COLOR_0" in pr["attributes"]:
                ac, dc = acc(pr["attributes"]["COLOR_0"])
                col = [struct.unpack_from("<4B", dc, 4 * k) for k in range(ac["count"])]
            ai, di = acc(pr["indices"])
            f, sz = ("<H", 2) if ai["componentType"] == 5123 else ("<I", 4)
            ix = [struct.unpack_from(f, di, sz * k)[0] for k in range(ai["count"])]
            out.append((pos, col, [tuple(ix[k:k + 3]) for k in range(0, len(ix), 3)]))
    return out


def charger_module():
    spec = importlib.util.spec_from_file_location("g2t_test", DIST / "glb2tiles.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.LOG_PATH = None
    return m


OPTS_TUILES = ["--forcer", "--budget-tri", "900", "--min", "64"]

# =====================================================================================================
print("--- 1. images vides ou invalides")
d1 = tmp / "img"
d1.mkdir()
glbfab.region(d1 / "Cass.glb", images_cassees=True)
r = tuiles(d1 / "Cass.glb", "--analyse")
rapport("Images vides ou invalides remplacées par un PNG gris de 128 : 2 distincte(s)" in r.stdout, "--analyse : nombre d'images remplacées (distinctes et occurrences)",
        [l for l in r.stdout.splitlines() if "Images" in l])
r = tuiles(d1 / "Cass.glb", *OPTS_TUILES, "--sans-vue-ensemble")
doc1 = json.loads((d1 / "Cass.tiles.json").read_text(encoding="utf-8"))
ri = doc1["replacedImages"]
occ_fiches = sum(t["replacedImages"] for t in doc1["tiles"])
rapport(ri["distinct"] == 2 and ri["occurrences"] == occ_fiches and ri["occurrences"] >= 2 and ri["grey"] == 128, "X.tiles.json : replacedImages (distinctes, occurrences = somme des tuiles)", ri)
rapport(f"{ri['distinct']} distincte(s), {ri['occurrences']} occurrence(s)" in r.stdout, "rapport final : mêmes nombres", [l for l in r.stdout.splitlines() if "Images" in l])
src_js, src_bn = lire_glb(d1 / "Cass.glb")
ok_img = ok_gris = ok_part = ok_mat = True
dims = set()
for t in doc1["tiles"]:
    js, bn = lire_glb(d1 / t["file"])
    imgs = js.get("images", [])
    ok_img &= all(png_ok(image_octets(js, bn, i)) or image_octets(js, bn, i)[:3] == b"\xff\xd8\xff" for i in range(len(imgs)))
    gris = [i for i, im in enumerate(imgs) if im.get("name") == "image-remplacee"]
    ok_gris &= len(gris) <= 1
    if gris:
        g = image_octets(js, bn, gris[0])
        w, h = struct.unpack(">II", g[16:24])
        dims.add((w, h))
        ok_gris &= w <= 4 and h <= 4
    # textures des matériaux « vide » et « tronquee » : toutes sur l'image grise unique ; matériaux et UV inchangés
    for mt in js.get("materials", []):
        if mt.get("name") in ("vide", "tronquee"):
            ti = mt["pbrMetallicRoughness"]["baseColorTexture"]["index"]
            ok_part &= gris and js["textures"][ti]["source"] == gris[0]
            ok_mat &= mt["pbrMetallicRoughness"] == {"baseColorTexture": {"index": ti}}
    for m in js["meshes"]:
        pr = m["primitives"][0]
        mt = js["materials"][pr["material"]] if "material" in pr else None
        if mt and mt.get("name") in ("vide", "tronquee"):
            ok_mat &= "TEXCOORD_0" in pr["attributes"]
rapport(ok_img, "aucune image vide ni tronquée dans les tuiles produites")
rapport(ok_gris and dims and all(w * h <= 16 for w, h in dims), f"un seul PNG gris par tuile, au plus 4 x 4 ({sorted(dims)})")
rapport(ok_part, "les deux textures cassées partagent l'image grise de la tuile")
rapport(ok_mat, "matériaux et coordonnées de texture inchangés")
png_gris_vu = False
for t in doc1["tiles"]:
    js, bn = lire_glb(d1 / t["file"])
    for i, im in enumerate(js.get("images", [])):
        if im.get("name") == "image-remplacee":
            g = image_octets(js, bn, i)
            import zlib
            p = 8
            while p < len(g):
                ln, typ = struct.unpack(">I4s", g[p:p + 8])
                if typ == b"IDAT":
                    raw = zlib.decompress(g[p + 8:p + 8 + ln])
                    png_gris_vu = set(raw[1::13]) <= {128} or raw[1] == 128
                p += 12 + ln
rapport(png_gris_vu, "le gris est 128 (celui de oar2glb.py --reencode)")
# image d'un autre format : remplacée aussi
b2 = glbfab.B()
b2.j["images"] = []
b2.image(b"GIF89a" + bytes(40), "image/gif")
b2.j["samplers"] = [{}]
b2.j["textures"] = [{"source": 0, "sampler": 0}]
b2.j["materials"] = [{"name": "gif", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}]
b2.noeud("Cube", b2.mesh(glbfab.cube(0, 0, 0, 2, 2, 2), glbfab.CUBE_IDX, mat=0, uv=True))
b2.ecrire(tmp / "gif.glb")
r = tuiles(tmp / "gif.glb", "--forcer", "--sans-vue-ensemble", "--sortie", tmp / "gifout")
dj = json.loads((tmp / "gifout" / "gif.tiles.json").read_text(encoding="utf-8"))
rapport(dj["replacedImages"]["distinct"] == 1, "image GIF (ni PNG, ni JPEG, ni WebP) remplacée", dj["replacedImages"])
# région sans image cassée : zéro
r = tuiles(glbfab.region(d1 / "Ok.glb") and d1 / "Ok.glb", *OPTS_TUILES, "--sans-vue-ensemble", "--sortie", d1 / "ok")
dok = json.loads((d1 / "ok" / "Ok.tiles.json").read_text(encoding="utf-8"))
rapport(dok["replacedImages"]["distinct"] == 0 and dok["replacedImages"]["occurrences"] == 0, "région saine : 0 image remplacée", dok["replacedImages"])

# =====================================================================================================
print("--- 2. vue d'ensemble : contenu du fichier")
d2 = tmp / "vue"
d2.mkdir()
glbfab.region(d2 / "Syn.glb")
r = tuiles(d2 / "Syn.glb", *OPTS_TUILES)
doc2 = json.loads((d2 / "Syn.tiles.json").read_text(encoding="utf-8"))
ov = doc2["overview"]
TUILES = [t["file"] for t in doc2["tiles"]]
rapport(len(TUILES) >= 4 and ov["file"] == "Syn.overview.glb" and (d2 / ov["file"]).is_file(), f"vue d'ensemble écrite par le découpage, référencée dans X.tiles.json ({len(TUILES)} tuiles)", ov)
js, bn = lire_glb(d2 / "Syn.overview.glb")
noms = [n["name"] for n in js["nodes"]]
rapport(set(noms) <= set(TUILES) and len(noms) == len(set(noms)) and len(noms) >= len(TUILES) - 1 and all(n["extras"]["tile"] == n["name"] for n in js["nodes"]), "un nœud par fichier de tuile, mêmes clés", (len(noms), len(TUILES)))
rapport(not any(k in js for k in ("images", "textures", "samplers")) and len(js["materials"]) == 1, "aucune image, texture ni sampler ; un seul matériau")
prims = lire_prims(js, bn)
tri_total = sum(len(p[2]) for p in prims)
rapport(tri_total == ov["triangles"] and (d2 / "Syn.overview.glb").stat().st_size == ov["bytes"], "triangles et octets du rapport = ceux du fichier", (tri_total, ov["triangles"]))
rapport(all(p[1] is not None for p in prims), "couleurs de sommets (COLOR_0) partout")
rapport(ov["objects"] == 24 + 40 and ov["omitted"]["small"] == 12 and ov["omitted"]["skinned"] == 1 and ov["omitted"]["translucentPrimitives"] == 1 and ov["omitted"]["budget"] == 0,
        "objets : maisons et instances gardées ; 12 petits, 1 à squelette, 1 primitive translucide omis", (ov["objects"], ov["omitted"]))
rapport("Vue d'ensemble Syn.overview.glb" in r.stdout and "objets omis" in r.stdout and "[vue d'ensemble : primitives]" in r.stdout, "rapport et progression affichés", r.stdout[-600:])
# terrain : hauteurs et couleurs
ter = ov["terrainTriangles"]
rapport(ter == 96 * 96 * 2, f"terrain : 96 x 96 cases de 4 m ({ter} triangles)", ter)
pire_h = pire_c = 0
n_ter = 0
rouge = bleu = 0
for pos, col, tri in prims:
    for (x, y, z), c in zip(pos, col):
        if abs(y - hauteur(x, z)) < 1.0 and abs(c[0] - couleur_sol(hauteur(x, z))[0]) < 40 and c[:3] != (255, 0, 0) and c[:3] != (0, 0, 255):
            n_ter += 1
            pire_h = max(pire_h, abs(y - hauteur(x, z)))
            pire_c = max(pire_c, max(abs(c[k] - couleur_sol(hauteur(x, z))[k]) for k in range(3)))
        rouge += c[:3] == (255, 0, 0)
        bleu += c[:3] == (0, 0, 255)
rapport(n_ter > 9000 and pire_h < 0.05 and pire_c <= 3, "terrain : hauteurs (écart < 5 cm) et couleurs de sommets conservées", (n_ter, pire_h, pire_c))
rapport(rouge > 0 and bleu > 0, "couleurs unies : moyenne de la texture (rouge) avec Pillow, couleur de base (bleu)", (rouge, bleu))
# sans Pillow : couleur de base (blanc)
d2b = tmp / "vue_sanspil"
d2b.mkdir()
shutil.copy(d2 / "Syn.glb", d2b / "Syn.glb")
lanceur = "import sys, runpy; sys.modules['PIL'] = None; sys.argv = ['glb2tiles.py'] + sys.argv[1:]; runpy.run_path(sys.argv[0] if False else %r, run_name='__main__')" % str(DIST / "glb2tiles.py")
r = subprocess.run([sys.executable, "-c", lanceur, str(d2b / "Syn.glb"), "--nopause", *OPTS_TUILES], capture_output=True, text=True, cwd=tmp)
js_b, bn_b = lire_glb(d2b / "Syn.overview.glb")
blanc = sum(c[:3] == (255, 255, 255) for p in lire_prims(js_b, bn_b) for c in p[1])
rouge_b = sum(c[:3] == (255, 0, 0) for p in lire_prims(js_b, bn_b) for c in p[1])
rapport(r.returncode == 0 and blanc > 0 and rouge_b == 0 and "Pillow absent" in r.stdout, "sans Pillow : couleur de base du matériau (repli), signalé dans le rapport", (r.returncode, blanc, rouge_b, r.stdout[-300:]))
# couleur moyenne exacte d'une texture 2 x 2 (2 rouges, 2 bleus) : moyenne en espace linéaire
b3 = glbfab.B()
b3.j["images"] = []
import zlib
def png2x2():
    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    raw = b"\x00" + bytes([255, 0, 0, 0, 0, 255]) + b"\x00" + bytes([255, 0, 0, 0, 0, 255])
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw)) + ch(b"IEND", b"")
b3.image(png2x2())
b3.j["samplers"] = [{}]
b3.j["textures"] = [{"source": 0, "sampler": 0}]
b3.j["materials"] = [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}]
b3.noeud("Cube", b3.mesh(glbfab.cube(0, 0, 0, 10, 10, 10), glbfab.CUBE_IDX, mat=0, uv=True))
b3.ecrire(tmp / "moy.glb")
tuiles(tmp / "moy.glb", "--forcer", "--sortie", tmp / "moyout")
js_m, bn_m = lire_glb(tmp / "moyout" / "moy.overview.glb")
cm = lire_prims(js_m, bn_m)[0][1][0]
rapport(cm[0] in (127, 128) and cm[1] == 0 and cm[2] in (127, 128), "couleur moyenne d'une texture rouge/bleue = (0,5 ; 0 ; 0,5) en linéaire", cm)

print("--- 3. terrain sans fente")
for pas in (4, 5):
    d3 = tmp / f"ter{pas}"
    d3.mkdir()
    glbfab.region(d3 / "T.glb", maisons=0, instances=0, petits=0, verre=False, squelette=False)
    tuiles(d3 / "T.glb", *OPTS_TUILES, "--ov-terrain-pas", pas)
    js_t, bn_t = lire_glb(d3 / "T.overview.glb")
    aretes = {}
    for pos, col, tri in lire_prims(js_t, bn_t):
        for a, b_, c in tri:
            for u, v in ((a, b_), (b_, c), (c, a)):
                pu = tuple(round(k, 3) for k in pos[u])
                pv = tuple(round(k, 3) for k in pos[v])
                k = (pu, pv) if pu < pv else (pv, pu)
                aretes[k] = aretes.get(k, 0) + 1
    xs = {p[0] for k in aretes for p in k}
    zs = {p[2] for k in aretes for p in k}
    bord = [k for k, n in aretes.items() if n == 1]
    ext = lambda q: (min(q), max(q))
    ok = all(((p[0] in ext(xs)) and (q[0] == p[0])) or ((p[2] in ext(zs)) and (q[2] == p[2])) for p, q in bord)
    rapport(ok and len(bord) > 0 and max(aretes.values()) <= 2 and ext(xs)[0] == 100.0 and ext(zs)[0] == -300.0,
            f"pas {pas} m : arêtes ouvertes seulement sur le contour de la région, aucune fente entre patches", (len(bord), ext(xs), ext(zs)))

print("--- 4. budgets, une seule simplification par primitive unique, lecture par morceaux")
sauve = {f.name: f.stat().st_mtime_ns for f in (d2 / "Syn.tiles").glob("*.glb")}
r = tuiles(d2 / "Syn.glb", *OPTS_TUILES, "--vue-ensemble-seule", "--ov-budget-tri", "20000", "--ov-budget", "0.2")
doc4 = json.loads((d2 / "Syn.tiles.json").read_text(encoding="utf-8"))
ov4 = doc4["overview"]
rapport(ov4["triangles"] <= 20000 and ov4["bytes"] <= 0.2 * 1048576 and ov4["effectiveTerrainStep"] > 4 and ov4["terrainTriangles"] < ter and "terrain trop lourd" in r.stdout,
        "budgets 20 000 triangles et 0,2 Mo respectés : le terrain (plus de la moitié du budget) passe à un réseau plus grossier, signalé", (ov4["triangles"], ov4["bytes"], ov4["effectiveTerrainStep"], ov4["omitted"]))
tuiles(d2 / "Syn.glb", *OPTS_TUILES, "--vue-ensemble-seule", "--ov-terrain-pas", "32", "--ov-budget-tri", "1000")
ov4 = json.loads((d2 / "Syn.tiles.json").read_text(encoding="utf-8"))["overview"]
rapport(ov4["triangles"] <= 1000 and ov4["effectiveTerrainStep"] == 32 and ov4["terrainTriangles"] == 288 and 40 <= ov4["objects"] < 64 and ov4["omitted"]["budget"] == 64 - ov4["objects"] and ov4["effectiveMinExtent"] == 6,
        "budget de 1 000 triangles : terrain intact, plus grands objets d'abord (8 m puis 6 m), le reste compté « par le budget »", (ov4["triangles"], ov4["objects"], ov4["omitted"], ov4["effectiveMinExtent"]))
rapport(sauve == {f.name: f.stat().st_mtime_ns for f in (d2 / "Syn.tiles").glob("*.glb")}, "--vue-ensemble-seule : les tuiles ne sont pas réécrites")
r = tuiles(d2 / "Syn.glb", "--forcer", "--budget-tri", "300", "--min", "64", "--vue-ensemble-seule", ok=False)
rapport(r.returncode == 2 and "ne correspond pas" in r.stdout, "--vue-ensemble-seule avec d'autres paramètres de découpage : refusé", r.stdout[-300:])
tuiles(d2 / "Syn.glb", *OPTS_TUILES, "--vue-ensemble-seule")
r = tuiles(d2 / "Syn.glb", *OPTS_TUILES, "--sans-vue-ensemble", "--vue-ensemble-seule", ok=False)
rapport(r.returncode != 0, "--sans-vue-ensemble et --vue-ensemble-seule s'excluent")
doc4 = json.loads((d2 / "Syn.tiles.json").read_text(encoding="utf-8"))
rapport(doc4["overview"]["triangles"] == ov["triangles"], "défauts rétablis : même vue d'ensemble que le découpage d'origine", (doc4["overview"]["triangles"], ov["triangles"]))
# seuil
tuiles(d2 / "Syn.glb", *OPTS_TUILES, "--vue-ensemble-seule", "--ov-seuil", "7")
ov5 = json.loads((d2 / "Syn.tiles.json").read_text(encoding="utf-8"))["overview"]
rapport(ov5["objects"] == 40 and ov5["omitted"]["small"] > 12 and ov5["effectiveMinExtent"] >= 7, "--ov-seuil 7 : maisons de 6 m omises, cubes partagés de 8 m gardés", (ov5["objects"], ov5["omitted"]))
tuiles(d2 / "Syn.glb", *OPTS_TUILES, "--vue-ensemble-seule")
# une seule simplification par primitive unique
g2t = charger_module()
ap = []
orig = g2t.regrouper
g2t.regrouper = lambda *a, **k: (ap.append(1), orig(*a, **k))[1]
glb = g2t.Glb(d2 / "Syn.glb")
try:
    plan = g2t.Plan(glb, g2t.Params(budget_tri=900, cote_min=64))
    tl = plan.decouper()
    ov_ = g2t.vue_ensemble(plan, tl, [f"Syn.tiles/{t.nom}.glb" for t in tl], g2t.ParamsOv(), tmp / "x.overview.glb")
    inst_gardees = ov_["objects"]
    rapport(len(ap) == 25 and inst_gardees == 64, f"chaque primitive unique simplifiée une seule fois : {len(ap)} simplifications pour {inst_gardees} instances (24 maisons + 1 cube partagé)", (len(ap), inst_gardees))
    rapport(glb.plus_grande_lecture <= g2t.BLOC_LECTURE and glb.nb_lectures > 0, f"lecture du GLB par morceaux de {g2t.BLOC_LECTURE} octets au plus (plus grande lecture {glb.plus_grande_lecture})")
finally:
    glb.fermer()

print("--- 5. tuiles d'une exécution précédente")
d5 = tmp / "stale"
d5.mkdir()
shutil.copy(d2 / "Syn.glb", d5 / "Syn.glb")
tuiles(d5 / "Syn.glb", *OPTS_TUILES, "--sans-vue-ensemble")
avant = {f.name for f in (d5 / "Syn.tiles").glob("*.glb")}
(d5 / "Syn.tiles" / "autre.glb").write_bytes(b"x")
r = tuiles(d5 / "Syn.glb", "--forcer", "--budget-tri", "100000", "--min", "64", "--sans-vue-ensemble")
apres = {f.name for f in (d5 / "Syn.tiles").glob("T_*.glb")}
index = {pathlib.Path(t["file"]).name for t in json.loads((d5 / "Syn.tiles.json").read_text(encoding="utf-8"))["tiles"]}
rapport(len(avant) > len(index) and apres == index and (d5 / "Syn.tiles" / "autre.glb").is_file() and "supprimé(s)" in r.stdout, f"tuiles absentes du nouvel index supprimées ({len(avant)} -> {len(index)}), signalé ; autres fichiers intouchés", (avant - index, apres))

print("--- 6. glb2html : vue d'ensemble placée avec les tuiles, refus d'une adresse dangereuse")
site = tmp / "site"
site.mkdir()
r = run(DIST / "glb2html.py", "-o", site / "Syn.html", "--shared-shell", "--tiles", d2 / "Syn.tiles.json", *vend)
rapport((site / "Syn.overview.glb").is_file() and (site / "Syn.overview.glb").stat().st_size == ov["bytes"] and "vue d'ensemble Syn.overview.glb" in r.stdout, "la vue d'ensemble est copiée avec les tuiles", r.stdout[-300:])
mauvais = json.loads((d2 / "Syn.tiles.json").read_text(encoding="utf-8"))
mauvais["overview"]["file"] = "../evil.glb"
(tmp / "mauvais.tiles.json").write_text(json.dumps(mauvais), encoding="utf-8")
r = run(DIST / "glb2html.py", "-o", tmp / "m" / "M.html", "--shared-shell", "--tiles", tmp / "mauvais.tiles.json", *vend, ok=False)
rapport(r.returncode != 0 and "overview" in r.stdout + r.stderr and not (tmp / "m").exists(), "adresse de vue d'ensemble avec .. refusée, rien d'écrit", r.stderr)

# =====================================================================================================
print("--- 7. navigateur")
# région sans vue d'ensemble (ancien index) et région avec images cassées, dans leurs sites
site_old = tmp / "site_old"
site_old.mkdir()
shutil.copytree(site / "lib", site_old / "lib")
shutil.copy(site / "index.html", site_old / "index.html")
d7 = tmp / "old"
d7.mkdir()
shutil.copy(d2 / "Syn.glb", d7 / "Syn.glb")
tuiles(d7 / "Syn.glb", *OPTS_TUILES, "--sans-vue-ensemble")
run(DIST / "glb2html.py", "-o", site_old / "Syn.html", "--shared-shell", "--tiles", d7 / "Syn.tiles.json", *vend)
site_cass = tmp / "site_cass"
site_cass.mkdir()
shutil.copytree(site / "lib", site_cass / "lib")
shutil.copy(site / "index.html", site_cass / "index.html")
run(DIST / "glb2html.py", "-o", site_cass / "Cass.html", "--shared-shell", "--tiles", d1 / "Cass.tiles.json", *vend)
# témoin : la même région en un seul GLB (images cassées intactes)
run(DIST / "glb2html.py", d1 / "Cass.glb", "-o", site_cass / "Brut.html", "--shared-shell", *vend)
TILES_DOC = json.loads((site / "Syn.tiles.json").read_text(encoding="utf-8"))
TILES = TILES_DOC["tiles"]


def serveur(dossier):
    with socket.socket() as so:
        so.bind(("127.0.0.1", 0))
        port = so.getsockname()[1]
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=dossier, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return proc, port
        except OSError:
            time.sleep(0.1)
    proc.kill()
    sys.exit("[ECHEC] http.server ne démarre pas")


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)

        class Onglet:
            def __init__(self):
                self.errs, self.warns, self.garde, self.faux = [], [], {}, {}

            async def ouvrir(self, url):
                ctx = await br.new_context(viewport={"width": 700, "height": 500})
                self.pg = await ctx.new_page()
                self.pg.on("pageerror", lambda e: self.errs.append(str(e)))
                self.pg.on("console", lambda m: self.warns.append(m.text) if m.type in ("warning", "error") else None)
                await self.pg.route("**/*.glb", self.route)
                await self.pg.goto(url)
                return self

            async def route(self, route):
                nom = route.request.url.split("/")[-1]
                if nom in self.faux:
                    st, corps = self.faux[nom]
                    return await route.fulfill(status=st, body=corps)
                if nom in self.garde:
                    await self.garde[nom].wait()
                try:
                    await route.continue_()
                except Exception:
                    pass

            async def ev(self, js, arg=None):
                return await self.pg.evaluate(js, arg)

            async def etat(self):
                return await self.ev("window.__viewer.tilesState()")

            async def attendre(self, cond_js, timeout=40):
                await self.pg.wait_for_function(cond_js, timeout=timeout * 1000)

            async def charge(self, timeout=60):
                await self.attendre("document.getElementById('msg') === null", timeout)

            async def marcher(self, n, dt=0.1):
                return await self.ev("""([n, dt]) => {
                    const v = window.__viewer, out = [], k = c => window.dispatchEvent(new KeyboardEvent('keydown', { code: c }));
                    k('KeyW'); k('ShiftLeft');
                    for (let i = 0; i < n; i++) { v.walkTick(dt); const w = v.getWalk(); out.push(w.pos.concat([w.grounded])); }
                    ['KeyW', 'ShiftLeft'].forEach(c => window.dispatchEvent(new KeyboardEvent('keyup', { code: c })));
                    return out; }""", [n, dt])

        # ---------- A. images : tout se décode ----------
        proc, port = serveur(site_cass)
        try:
            # témoin : images d'origine cassées -> createImageBitmap échoue ; images des tuiles -> tout se décode
            o = Onglet()
            await o.ouvrir(f"http://127.0.0.1:{port}/index.html?region=Cass")
            await o.charge()
            src_imgs = [image_octets(src_js, src_bn, i) for i in range(len(src_js["images"]))]
            tuile_imgs = []
            for t in doc1["tiles"]:
                js_, bn_ = lire_glb(d1 / t["file"])
                tuile_imgs += [image_octets(js_, bn_, i) for i in range(len(js_.get("images", [])))]
            import base64
            dec = """async (l) => { const out = []; for (const b64 of l) { const bin = atob(b64), u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
                try { await createImageBitmap(new Blob([u], { type: 'image/png' })); out.push(true); } catch (e) { out.push(false); } } return out; }"""
            res_src = await o.ev(dec, [base64.b64encode(x).decode() for x in src_imgs])
            res_t = await o.ev(dec, [base64.b64encode(x).decode() for x in tuile_imgs])
            rapport(res_src.count(False) == 2 and res_src.count(True) == len(src_imgs) - 2, "témoin : dans le GLB d'origine, l'image vide et l'image tronquée échouent au décodage de Chromium", res_src)
            rapport(res_t and all(res_t), f"toutes les images des tuiles produites se décodent ({len(res_t)} images)", res_t.count(False))
            rapport(not any("Couldn't load texture" in w for w in o.warns) and not o.errs, "région en tuiles : aucune erreur de texture ni de JavaScript", (o.warns[:3], o.errs))
            await o.pg.close()
            o = Onglet()
            await o.ouvrir(f"http://127.0.0.1:{port}/index.html?region=Brut")
            for _ in range(60):     # le GLB d'origine ne se charge pas en entier : on attend seulement le message
                if any("Couldn't load texture" in w for w in o.warns):
                    break
                await o.pg.wait_for_timeout(500)
            rapport(any("Couldn't load texture" in w for w in o.warns), "témoin : le GLB d'origine produit bien « Couldn't load texture »", o.warns[:3])
            await o.pg.close()
        finally:
            proc.kill()

        # ---------- B. sortie de promenade, sans tuiles ----------
        site_b = tmp / "site_b"
        site_b.mkdir()
        run(DIST / "glb2html.py", DATA / "walk3.glb", "-o", site_b / "Plat.html", "--shared-shell", *vend)
        proc, port = serveur(site_b)
        try:
            o = Onglet()
            await o.ouvrir(f"http://127.0.0.1:{port}/index.html?region=Plat")
            await o.charge()
            av = await o.ev("""(() => { const v = window.__viewer; v.camera.updateMatrixWorld(true);
                return { off: v.camera.position.clone().sub(v.controls.target).toArray(), tg: v.controls.target.toArray(), fov: v.camera.fov }; })()""")
            await o.ev("window.__viewer.walkStart()")
            await o.attendre("window.__viewer.walking", 20)
            await o.marcher(25, 0.1)
            w = await o.ev("window.__viewer.getWalk()")
            await o.ev("window.__viewer.walkStop()")
            ap = await o.ev("""(() => { const v = window.__viewer; return { off: v.camera.position.clone().sub(v.controls.target).toArray(), tg: v.controls.target.toArray(), fov: v.camera.fov, walking: v.walking }; })()""")
            d_ = math.hypot(ap["tg"][0] - w["pos"][0], ap["tg"][2] - w["pos"][2])
            rapport(not ap["walking"] and d_ < 0.01 and abs(ap["tg"][1] - w["pos"][1]) < 0.2, "sortie de promenade : la cible est sous la dernière position de l'avatar, au sol", (ap["tg"], w["pos"]))
            rapport(max(abs(a - b) for a, b in zip(ap["off"], av["off"])) < 1e-3 and abs(ap["fov"] - av["fov"]) < 1e-6, "la caméra garde le même décalage (distance et direction) que avant la promenade, champ de vision rétabli", (ap["off"], av["off"]))
            rapport(math.hypot(av["tg"][0] - w["pos"][0], av["tg"][2] - w["pos"][2]) > 0.5, "le test a bien déplacé l'avatar (la cible a changé)", (av["tg"], w["pos"]))
            rapport(not o.errs, "aucune erreur JavaScript", o.errs)
            await o.pg.close()
        finally:
            proc.kill()

        # ---------- C. coquille avec vue d'ensemble ----------
        proc, port = serveur(site)
        base = f"http://127.0.0.1:{port}/index.html?region=Syn"
        try:
            o = Onglet()
            for t in TILES:
                o.garde[t["file"].split("/")[-1]] = asyncio.Event()
            await o.ouvrir(base)
            await o.attendre("window.__viewer && window.__viewer.tilesState().total > 0 && window.__viewer.tilesState().overview.state === 'ready'")
            e = await o.etat()
            cellules = e["overview"]["cells"]
            rapport(e["overview"]["state"] == "ready" and cellules >= len(TILES) - 1 and not e["ready"], f"la vue d'ensemble est chargée avant toute tuile ({cellules} cellules)", e["overview"])
            rapport(sorted(e["overview"]["visible"]) <= sorted(t["file"] for t in TILES) and not e["overview"]["hidden"], "tuiles retenues : toutes les cellules de la vue d'ensemble sont visibles (pas de trou)", e["overview"])
            ligne = await o.ev("document.getElementById('tilesInfo').textContent")
            rapport("Vue d'ensemble (à part)" in ligne and "Mo" in ligne and "triangles" in ligne, "ligne d'information : vue d'ensemble comptée à part (texte)", ligne)
            # cadrage : les huit coins de l'étendue entrent dans l'image
            proj = await o.ev("""(ext) => { const v = window.__viewer; v.camera.updateMatrixWorld(true); const out = [];
                for (const x of [ext.min[0], ext.max[0]]) for (const z of [ext.min[2], ext.max[2]]) for (const y of [ext.min[1], ext.max[1]]) { const p = v.camera.position.clone().set(x, y, z).project(v.camera); out.push([p.x, p.y, p.z]); }
                return out; }""", TILES_DOC["extent"])
            rapport(all(abs(a) <= 1 and abs(b) <= 1 and 0 < c < 1 for a, b, c in proj), "vue globale : toute la région est dans l'image dès le départ", proj)
            for ev_ in o.garde.values():
                ev_.set()
            await o.charge()
            await o.attendre("window.__viewer.tilesState().loadingFiles.length === 0", 30)
            e = await o.etat()
            inv = await o.ev("""() => { const v = window.__viewer, s = v.tilesState(); const g = new Set(s.groups.map(n => n.replace('tile:', '')));
                return { hidden: s.overview.hidden.slice().sort(), groups: [...g].sort() }; }""")
            rapport(e["ready"] and inv["hidden"] == inv["groups"] and 0 < len(inv["groups"]) < len(TILES), "cellule masquée si et seulement si sa tuile détaillée est affichée", inv)
            # sol : jamais la vue d'ensemble
            tri_prets = sum(t["triangles"] for t in TILES if t["file"] in e["ready"] or t["file"] in e["loadingFiles"])
            rapport(e["tri"] == tri_prets and e["overview"]["tri"] > 0 and e["ov"]["tri"] == e["overview"]["tri"], "compteurs de tuiles hors vue d'ensemble (budget tileMaxMo / tileMaxTri)", (e["tri"], tri_prets, e["ov"]))
            rapport(not o.errs and not [w for w in o.warns if "Couldn't" in w], "aucune erreur JavaScript", (o.errs, o.warns[:3]))
            # double-clic sur la vue d'ensemble : un point lointain devient la cible
            lointaine = [t for t in TILES if t["file"] not in e["ready"]]
            t = max(lointaine, key=lambda q: math.hypot((q["min"][0] + q["max"][0]) / 2 - e["radius"], 0)) if lointaine else None
            cx, cz = (t["min"][0] + t["max"][0]) / 2, (t["min"][2] + t["max"][2]) / 2
            sc = await o.ev("""([x, z]) => { const v = window.__viewer; v.camera.updateMatrixWorld(true);
                const y = 14; const p = v.camera.position.clone().set(x, y, z).project(v.camera), r = v.renderer.domElement.getBoundingClientRect();
                return [r.left + (p.x + 1) / 2 * r.width, r.top + (1 - p.y) / 2 * r.height]; }""", [cx, cz])
            await o.pg.mouse.dblclick(sc[0], sc[1])
            await o.pg.wait_for_timeout(300)
            tg = await o.ev("window.__viewer.controls.target.toArray()")
            rapport(t is not None and math.hypot(tg[0] - cx, tg[2] - cz) < 40, "double-clic sur la vue d'ensemble : la cible se place sur le point lointain", (tg, cx, cz))
            await o.attendre("window.__viewer.tilesState().ready.some(f => f === %s)" % json.dumps(t["file"]), 40)
            rapport(True, "les tuiles de ce point se chargent ensuite")
            await o.pg.close()

            # C2. sortie de promenade en mode tuiles : les tuiles autour de l'avatar restent chargées (?rayon=60, marge 60 : décharge au-delà de 120 m)
            o = Onglet()
            await o.ouvrir(base + "&rayon=60")
            await o.charge()
            c0 = await o.ev("window.__viewer.controls.target.toArray()")
            await o.pg.wait_for_timeout(4200)      # fin du point de départ forcé
            await o.ev("window.__viewer.controls.target.set(120, 20, -120)")
            await o.attendre("window.__viewer.tilesState().ready.length > 0 && window.__viewer.tilesState().loadingFiles.length === 0", 40)
            off0 = await o.ev("window.__viewer.camera.position.clone().sub(window.__viewer.controls.target).toArray()")
            await o.ev("window.__viewer.walkStart({ pos: [120, 15, -120], yaw: -Math.PI / 2 })")
            await o.attendre("window.__viewer.walking", 20)
            w0 = await o.ev("window.__viewer.getWalk().pos")
            for _ in range(120):
                pts = await o.marcher(20)
                await o.pg.wait_for_timeout(100)
                if pts[-1][0] >= w0[0] + 330:
                    break
            await o.attendre("window.__viewer.tilesState().loadingFiles.length === 0", 30)
            w = await o.ev("window.__viewer.getWalk().pos")
            avant = (await o.etat())["ready"]
            rapport(w[0] > w0[0] + 300 and math.hypot(w[0] - c0[0], w[2] - c0[2]) > 120, "avatar à plus de rayon + marge du centre de la région (point de départ de la vue globale)", (w0, w, c0))
            await o.ev("window.__viewer.walkStop()")
            await o.pg.wait_for_timeout(1500)
            apres = await o.etat()
            tg = await o.ev("window.__viewer.controls.target.toArray()")
            off1 = await o.ev("window.__viewer.camera.position.clone().sub(window.__viewer.controls.target).toArray()")
            rapport(math.hypot(tg[0] - w[0], tg[2] - w[2]) < 0.01 and abs(tg[1] - w[1]) < 0.3, "mode tuiles : la cible de la vue globale est sous l'avatar", (tg, w))
            rapport(max(abs(a - b) for a, b in zip(off0, off1)) < 1e-3, "mode tuiles : même décalage de caméra qu'avant l'entrée en promenade", (off0, off1))
            proches = {t["file"] for t in TILES if math.hypot(max(t["min"][0] - w[0], 0, w[0] - t["max"][0]), max(t["min"][2] - w[2], 0, w[2] - t["max"][2])) <= apres["radius"] - 10}
            rapport(proches and proches <= set(apres["ready"]) and set(avant) & proches <= set(apres["ready"]), "les tuiles autour de l'avatar ne sont pas déchargées à la sortie (avec la cible de la v30 elles partiraient)", (len(proches), len(apres["ready"]), sorted(proches - set(apres["ready"]))))
            inv = await o.ev("() => { const s = window.__viewer.tilesState(); return { hidden: s.overview.hidden.slice().sort(), groups: s.groups.map(n => n.replace('tile:', '')).sort() }; }")
            rapport(inv["hidden"] == inv["groups"] and inv["groups"], "après la sortie : cellules masquées = tuiles affichées", inv)
            rapport(not o.errs, "aucune erreur JavaScript", o.errs)
            # la promenade attend toujours la tuile (la vue d'ensemble n'est pas un sol)
            lointaine = next(t for t in TILES if t["file"] not in apres["ready"])
            o.garde[lointaine["file"].split("/")[-1]] = asyncio.Event()
            px, pz = (lointaine["min"][0] + lointaine["max"][0]) / 2, (lointaine["min"][2] + lointaine["max"][2]) / 2
            await o.ev("window.__viewer.controls.target.set(%f, 20, %f)" % (px, pz))
            await o.ev("window.__viewer.walkStart()")
            st = await o.ev("({ walking: window.__viewer.walking, waiting: window.__viewer.tilesState().waiting })")
            rapport(not st["walking"] and st["waiting"], "tuile retenue : pas de promenade sur la vue d'ensemble, indicateur « Chargement du sol… » actif", st)
            inv = await o.ev("() => { const s = window.__viewer.tilesState(); return s.overview.visible.includes(%s); }" % json.dumps(lointaine["file"]))
            rapport(inv, "pendant l'attente, la cellule de cette tuile reste visible (pas de trou)")
            o.garde[lointaine["file"].split("/")[-1]].set()
            await o.attendre("window.__viewer.walking", 40)
            inv = await o.ev("() => { const s = window.__viewer.tilesState(); return s.overview.hidden.includes(%s); }" % json.dumps(lointaine["file"]))
            rapport(inv, "tuile prête : la cellule correspondante est masquée")
            await o.pg.close()

            # C3. la vue d'ensemble tombe en panne : la région fonctionne comme en v30
            o = Onglet()
            o.faux["Syn.overview.glb"] = (404, b"")
            await o.ouvrir(base)
            await o.charge()
            e = await o.etat()
            ligne = await o.ev("document.getElementById('tilesInfo').textContent")
            rapport(e["overview"]["state"] == "failed" and e["ready"] and any("vue d'ensemble" in w for w in o.warns) and "indisponible" in ligne and not o.errs, "vue d'ensemble introuvable : avertissement, tuiles chargées, aucune erreur", (e["overview"], o.warns[:2], ligne))
            await o.pg.close()
        finally:
            proc.kill()

        # ---------- D. ancien X.tiles.json (sans vue d'ensemble) ----------
        proc, port = serveur(site_old)
        try:
            o = Onglet()
            await o.ouvrir(f"http://127.0.0.1:{port}/index.html?region=Syn")
            await o.charge()
            e = await o.etat()
            f_old = await o.ev("window.__viewer.fit")
            rapport(e["overview"]["state"] == "none" and e["ready"] and not o.errs and not o.warns, "sans vue d'ensemble : comportement de la v30 (tuiles seules, cadrage sur le rayon), aucun avertissement", (e["overview"], o.warns[:2], o.errs))
            ligne = await o.ev("document.getElementById('tilesInfo').textContent")
            rapport("Vue d'ensemble" not in ligne, "sans vue d'ensemble : pas de mention dans la ligne d'information", ligne)
            await o.pg.close()
        finally:
            proc.kill()
        await br.close()


asyncio.run(main())
shutil.rmtree(tmp, ignore_errors=True)
print("\nRÉSULTAT :", "tout est passé" if not bad else f"{bad} échec(s)")
sys.exit(1 if bad else 0)
