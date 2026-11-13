#!/usr/bin/env python3
"""oar2glb.py --tex-only GLB : appliquer --tex-size / --tex-quality a un GLB deja fait (OAR minimal et faux convoar pour fabriquer le GLB, aucun .exe).

Bout en bout : un GLB fait par la conversion (trois textures : 512 x 384 opaque, 512 x 512 transparente, 64 x 64), puis --tex-only avec --tex-size, --tex-quality, les
deux : fichier de sortie nomme NOM-tex128.glb / NOM-q40.glb / NOM-tex128-q40.glb (ou --output), images reduites ou recompressees comme a la conversion (memes octets que
--tex-size donne directement a la conversion), reste du JSON et donnees de geometrie inchangees, original jamais modifie, GLB valide (longueurs, alignements).
GLB fait a la main : image PBR (pbr-) intacte, image hors du GLB intacte, deux images sur la meme vue, zone EXT_meshopt_compression dans le tampon 0 recopiee et
repointee, rien a modifier (aucun fichier ecrit), lecture par petits morceaux identique, fichier invalide ou tronque, Pillow absent, valeurs et combinaisons refusees.
Prerequis : pip install pillow. Lancer : python tests/tex_seul.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import hashlib, io, json, os, pathlib, random, struct, subprocess, sys, tarfile, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "oar2glb.py"
sys.path.insert(0, str(ROOT / "tools"))
import oar2glb as T  # noqa: E402
from PIL import Image  # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="tex_seul_"))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")      # sortie des outils toujours en UTF-8 et lue en UTF-8
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


def executer(args, **kw):
    return subprocess.run(args, capture_output=True, encoding="utf-8", errors="replace", env=ENV, cwd=tmp, stdin=subprocess.DEVNULL, **kw)


def octets(im, fmt, **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return b.getvalue()


def photo(w, h):
    rnd = random.Random(w * 1000 + h)
    im = Image.new("RGB", (w, h))
    px = im.load()
    ok = lambda v: min(255, max(0, v))
    for y in range(h):
        for x in range(w):
            r, g, b = (x * 255) // max(w - 1, 1), (y * 255) // max(h - 1, 1), ((x + y) * 255) // max(w + h - 2, 1)
            px[x, y] = (ok(r + rnd.randint(-8, 8)), ok(g + rnd.randint(-8, 8)), ok(b + rnd.randint(-8, 8)))
    return im


def disque(w, h):
    im = photo(w, h).convert("RGBA")
    a = Image.new("L", (w, h), 0)
    ap = a.load()
    for y in range(h):
        for x in range(w):
            if (x - w / 2) ** 2 + (y - h / 2) ** 2 <= (min(w, h) / 2 - 2) ** 2:
                ap[x, y] = 255
    im.putalpha(a)
    return im


def empreinte(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def pad4(b, c=b"\x00"):
    return b + c * ((4 - len(b) % 4) % 4)


def lire_glb(chemin):
    """(JSON, donnees binaires) d'un GLB, en verifiant sa structure : longueur totale, chunks alignes, tampon 0 = chunk BIN, vues dans le tampon, decalages alignes sur 4"""
    d = pathlib.Path(chemin).read_bytes()
    mag, ver, total = struct.unpack_from("<4sII", d, 0)
    assert mag == b"glTF" and ver == 2 and total == len(d), ("en-tete", mag, ver, total, len(d))
    ln, typ = struct.unpack_from("<I4s", d, 12)
    assert typ == b"JSON" and ln % 4 == 0
    g = json.loads(d[20:20 + ln].decode("utf-8"))
    pos = 20 + ln
    ln2, typ2 = struct.unpack_from("<I4s", d, pos)
    assert typ2 == b"BIN\x00" and ln2 % 4 == 0 and pos + 8 + ln2 == len(d), "chunk BIN"
    blob = d[pos + 8:pos + 8 + ln2]
    assert g["buffers"][0]["byteLength"] == len(blob), ("buffers[0].byteLength", g["buffers"][0]["byteLength"], len(blob))
    for v in g.get("bufferViews", []):
        if v.get("buffer", 0) == 0:
            assert v.get("byteOffset", 0) % 4 == 0 and v.get("byteOffset", 0) + v["byteLength"] <= len(blob), ("vue", v)
    return g, blob


def vue(g, blob, i):
    v = g["bufferViews"][i]
    return blob[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]]


def images(g, blob):
    return [vue(g, blob, im["bufferView"]) for im in g["images"] if "bufferView" in im]


def ouvrir(data):
    im = Image.open(io.BytesIO(data)); im.load(); return im


def hors_images(g):
    """le JSON sans ce que --tex-only a le droit de changer : decalages et longueurs des vues, longueur du tampon, types MIME des images"""
    c = json.loads(json.dumps(g))
    for v in c.get("bufferViews", []):
        v.pop("byteOffset", None); v.pop("byteLength", None)
        ext = (v.get("extensions") or {}).get("EXT_meshopt_compression")
        if ext:
            ext.pop("byteOffset", None); ext.pop("byteLength", None)
    for im in c.get("images", []):
        im.pop("mimeType", None)
    c["buffers"][0].pop("byteLength", None)
    return c


# ---------- fabrication d'un GLB par la conversion (faux convoar) ----------
opaque, alpha, petite = octets(photo(512, 384), "PNG"), octets(disque(512, 512), "PNG"), octets(photo(64, 64), "PNG")
FAKE = '''#!/usr/bin/env python3
import sys, shutil, pathlib
a = sys.argv[1:]
out = pathlib.Path(a[a.index("--outputdir") + 1]); out.mkdir(exist_ok=True)
for f in pathlib.Path(__file__).with_name("fake_out").iterdir():
    shutil.copy(f, out / f.name)
print("fake convoar")
'''


def fabriquer(dossier):
    dossier.mkdir()
    oar = dossier / "R.oar"
    with tarfile.open(oar, "w:gz") as t:
        ti = tarfile.TarInfo("archive.xml"); data = b"<archive><region_info><size_in_meters>256,256</size_in_meters></region_info></archive>"; ti.size = len(data)
        t.addfile(ti, io.BytesIO(data))
    fo = dossier / "fake_out"; fo.mkdir()
    (fo / "grande.png").write_bytes(opaque); (fo / "feuille.png").write_bytes(alpha); (fo / "petite.png").write_bytes(petite)
    (fo / "scene.bin").write_bytes(struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0))
    g = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0, "name": "Boite"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "material": i} for i in range(3)]}],
         "materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": i}}} for i in range(3)], "textures": [{"source": i} for i in range(3)],
         "images": [{"uri": "grande.png"}, {"uri": "feuille.png"}, {"uri": "petite.png"}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3", "min": [0, 0, 0], "max": [1, 1, 0]}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36}], "buffers": [{"byteLength": 36, "uri": "scene.bin"}]}
    (fo / "scene.gltf").write_text(json.dumps(g), encoding="utf-8")
    fake = dossier / "convoar_fake.py"; fake.write_text(FAKE); fake.chmod(0o755)
    return oar, fake


def convertir(dossier, *extra):
    oar, fake = fabriquer(tmp / dossier)
    r = executer([sys.executable, str(TOOL), str(oar), "--convoar", str(fake), "--nopause", "--no-pbr", *extra])
    return r, oar.with_suffix(".glb")


r0, glb = convertir("base")
rapport(r0.returncode == 0 and glb.exists(), "GLB de depart fabrique par la conversion (sans option)", (r0.returncode, (r0.stdout + r0.stderr)[-300:]))
g0, b0 = lire_glb(glb)
im0 = images(g0, b0)
rapport([max(ouvrir(x).size) for x in im0] == [512, 512, 64], "GLB de depart : textures de 512, 512 et 64 pixels", [ouvrir(x).size for x in im0])
sha0 = empreinte(glb)


def tex_seul(*args):
    return executer([sys.executable, str(TOOL), "--tex-only", str(glb), *args])


# ---------- --tex-size ----------
r = tex_seul("--tex-size", "128")
out_t = glb.with_name("R-tex128.glb")
rapport(r.returncode == 0 and out_t.exists() and "[textures] 2 sur 3 modifi" in r.stdout and "[OK]" in r.stdout, "--tex-size 128 : fichier R-tex128.glb ecrit, bilan « 2 sur 3 modifiées »", (r.returncode, r.stdout[-500:], r.stderr[-200:]))
g1, b1 = lire_glb(out_t)
im1 = images(g1, b1)
d1 = [ouvrir(x) for x in im1]
rapport([i.size for i in d1] == [(128, 96), (128, 128), (64, 64)] and [i["mimeType"] for i in g1["images"]] == ["image/jpeg", "image/png", "image/png"] and d1[1].convert("RGBA").getchannel("A").getextrema()[0] == 0 and im1[2] == petite,
        "--tex-size 128 : opaque en JPEG 128, transparente en PNG 128 (alpha gardee), petite inchangee (memes octets)", ([i.size for i in d1], [i["mimeType"] for i in g1["images"]]))
rapport(hors_images(g1) == hors_images(g0), "--tex-size 128 : le reste du JSON est inchange (noeuds, meshes, materiaux, accessors, textures)")
rapport(vue(g1, b1, 0) == vue(g0, b0, 0) if "bufferView" not in g1["images"][0] else True, "controle de structure")
geo0 = [i for i in range(len(g0["bufferViews"])) if i not in [im["bufferView"] for im in g0["images"]]]
rapport(geo0 and all(vue(g1, b1, i) == vue(g0, b0, i) for i in geo0), "--tex-size 128 : les donnees de geometrie sont recopiees a l'identique", geo0)
rapport(out_t.stat().st_size < glb.stat().st_size, "--tex-size 128 : le GLB est plus leger", (out_t.stat().st_size, glb.stat().st_size))
rapport(empreinte(glb) == sha0, "--tex-size 128 : le GLB d'origine n'est jamais modifie")

# ---------- equivalence avec la conversion directe ----------
rd, glb_d = convertir("direct_tex", "--tex-size", "128")
gd, bd = lire_glb(glb_d)
rapport(rd.returncode == 0 and images(gd, bd) == im1, "--tex-size 128 : memes octets d'image que --tex-size 128 donne directement a la conversion", rd.returncode)

# ---------- --tex-quality ----------
r = tex_seul("--tex-quality", "40")
out_q = glb.with_name("R-q40.glb")
g2, b2 = lire_glb(out_q) if out_q.exists() else (None, None)
rapport(r.returncode == 0 and out_q.exists() and "[textures] 2 sur 3 modifi" in r.stdout, "--tex-quality 40 : fichier R-q40.glb ecrit", (r.returncode, r.stdout[-400:], r.stderr[-200:]))
if g2:
    im2 = images(g2, b2); d2 = [ouvrir(x) for x in im2]
    rapport([i.size for i in d2] == [(512, 384), (512, 512), (64, 64)] and [i["mimeType"] for i in g2["images"]] == ["image/jpeg", "image/png", "image/jpeg"] and im2[1] == alpha,
            "--tex-quality 40 : pixels d'origine, JPEG pour les deux opaques, transparente inchangee", ([i.size for i in d2], [i["mimeType"] for i in g2["images"]]))
    rapport(out_q.stat().st_size < glb.stat().st_size and hors_images(g2) == hors_images(g0), "--tex-quality 40 : plus leger, reste du JSON inchange")
    rq, glb_q = convertir("direct_q", "--tex-quality", "40")
    gq, bq = lire_glb(glb_q)
    rapport(images(gq, bq) == im2, "--tex-quality 40 : memes octets d'image que la conversion directe")

# ---------- les deux ----------
r = tex_seul("--tex-size", "128", "--tex-quality", "40")
out_tq = glb.with_name("R-tex128-q40.glb")
g3, b3 = lire_glb(out_tq) if out_tq.exists() else (None, None)
rapport(r.returncode == 0 and out_tq.exists(), "les deux : fichier R-tex128-q40.glb ecrit", (r.returncode, r.stdout[-400:], r.stderr[-200:]))
if g3:
    im3 = images(g3, b3)
    rapport([ouvrir(x).size for x in im3] == [(128, 96), (128, 128), (64, 64)] and [i["mimeType"] for i in g3["images"]] == ["image/jpeg", "image/png", "image/jpeg"], "les deux : 128 pixels, JPEG pour les opaques, PNG pour la transparente",
            [ouvrir(x).size for x in im3])
    rd2, glb_d2 = convertir("direct_les_deux", "--tex-size", "128", "--tex-quality", "40")
    gd2, bd2 = lire_glb(glb_d2)
    rapport(images(gd2, bd2) == im3, "les deux : memes octets d'image que la conversion directe")
    rapport(out_tq.stat().st_size < out_t.stat().st_size, "les deux : plus leger que la taille seule", (out_tq.stat().st_size, out_t.stat().st_size))

# ---------- --output, refus ----------
perso = tmp / "dossier_sortie"; perso.mkdir()
r = tex_seul("--tex-size", "128", "--output", str(perso / "autre nom.glb"))
rapport(r.returncode == 0 and (perso / "autre nom.glb").exists() and empreinte(perso / "autre nom.glb") == empreinte(out_t), "--output : le fichier est ecrit sous le nom demande, meme contenu", (r.returncode, r.stdout[-300:]))
r = tex_seul("--tex-size", "128", "--output", str(glb))
rapport(r.returncode != 0 and "jamais écrasé" in (r.stdout + r.stderr) and empreinte(glb) == sha0, "--output = le GLB d'origine : refuse, l'original reste intact", (r.returncode, (r.stdout + r.stderr)[-300:]))
r = tex_seul()
rapport(r.returncode != 0 and "--tex-size et/ou --tex-quality" in (r.stdout + r.stderr), "sans --tex-size ni --tex-quality : refuse avec un message clair", (r.returncode, (r.stdout + r.stderr)[-300:]))
r = executer([sys.executable, str(TOOL), "--tex-only", str(glb), "--tex-size", "128", "--terrain-only", str(glb)])
rapport(r.returncode != 0 and "ne se combinent pas" in (r.stdout + r.stderr), "avec --terrain-only : refuse", (r.returncode, (r.stdout + r.stderr)[-300:]))
for opt, val in (("--tex-size", "5"), ("--tex-size", "9000"), ("--tex-quality", "0"), ("--tex-quality", "96")):
    r = tex_seul(opt, val)
    rapport(r.returncode != 0 and "[ERREUR]" in (r.stdout + r.stderr), f"{opt} {val} refuse", (r.returncode, (r.stdout + r.stderr)[-200:]))
r = executer([sys.executable, str(TOOL), "--nopause"])
rapport(r.returncode != 0 and "OAR est obligatoire" in (r.stdout + r.stderr), "sans --tex-only et sans OAR : message clair (l'OAR n'est plus exige par l'analyseur)", (r.returncode, (r.stdout + r.stderr)[-300:]))
r = executer([sys.executable, str(TOOL), "--tex-only", str(tmp / "absent.glb"), "--tex-size", "128"])
rapport(r.returncode != 0 and "introuvable" in (r.stdout + r.stderr), "GLB introuvable : message clair", (r.returncode, (r.stdout + r.stderr)[-200:]))

# ---------- GLB invalides ----------
faux = tmp / "faux.glb"; faux.write_bytes(b"ceci n'est pas un GLB du tout" * 3)
r = executer([sys.executable, str(TOOL), "--tex-only", str(faux), "--tex-size", "128"])
rapport(r.returncode != 0 and "n'est pas un GLB" in (r.stdout + r.stderr) and not faux.with_name("faux-tex128.glb").exists(), "fichier qui n'est pas un GLB : message clair, rien d'ecrit", (r.returncode, (r.stdout + r.stderr)[-200:]))
tronque = tmp / "tronque.glb"; tronque.write_bytes(glb.read_bytes()[:-5000])
r = executer([sys.executable, str(TOOL), "--tex-only", str(tronque), "--tex-size", "128"])
rapport(r.returncode != 0 and "tronqu" in (r.stdout + r.stderr) and not tronque.with_name("tronque-tex128.glb").exists() and not list(tmp.glob("tronque*.part")), "GLB tronque : message clair, ni sortie ni fichier .part", (r.returncode, (r.stdout + r.stderr)[-200:], list(tmp.glob("tronque*"))))

# ---------- lecture par petits morceaux ----------
petit = tmp / "petit_chunk.glb"
T.tex_seul(glb, petit, 128, None, chunk=777)
rapport(petit.read_bytes() == out_t.read_bytes(), "lecture par morceaux de 777 octets : sortie identique a celle par morceaux de 8 Mo")

# ---------- GLB fait a la main ----------
def assembler(parts):
    blob = bytearray(); offs = []
    for p in parts:
        blob += b"\x00" * (-len(blob) % 4); offs.append(len(blob)); blob += p
    return bytes(blob), offs


def ecrire(chemin, g, blob):
    g = json.loads(json.dumps(g)); g["buffers"][0]["byteLength"] = len(blob) + (-len(blob) % 4)
    blob = pad4(blob)
    js = pad4(json.dumps(g).encode(), b" ")
    pathlib.Path(chemin).write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js
                                     + struct.pack("<I4s", len(blob), b"BIN\x00") + blob)


png_grand, png_pbr = octets(photo(400, 300), "PNG"), octets(photo(300, 300), "PNG")
geom = bytes(range(256)) * 3                                  # 768 octets de "geometrie"
blob, offs = assembler([png_grand, png_pbr, geom, b"\x07" * 61])
g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": 0}],
     "bufferViews": [{"buffer": 0, "byteOffset": offs[0], "byteLength": len(png_grand)}, {"buffer": 0, "byteOffset": offs[1], "byteLength": len(png_pbr)},
                     {"buffer": 0, "byteOffset": offs[2], "byteLength": len(geom), "byteStride": 12, "target": 34962}, {"buffer": 0, "byteOffset": offs[3], "byteLength": 61}],
     "images": [{"bufferView": 0, "mimeType": "image/png"}, {"bufferView": 1, "mimeType": "image/png"}, {"uri": "ailleurs.png"}, {"bufferView": 0, "mimeType": "image/png"}],
     "textures": [{"source": 0}, {"source": 1}, {"source": 2}],
     "materials": [{"name": "ordinaire", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}, {"name": "pbr-ab12cd34", "pbrMetallicRoughness": {"baseColorTexture": {"index": 1}}, "normalTexture": {"index": 1}}],
     "accessors": [{"bufferView": 2, "componentType": 5126, "count": 64, "type": "VEC3"}]}
main_glb = tmp / "main.glb"
ecrire(main_glb, g, blob)
r = executer([sys.executable, str(TOOL), "--tex-only", str(main_glb), "--tex-size", "100"])
sortie = tmp / "main-tex100.glb"
rapport(r.returncode == 0 and sortie.exists(), "GLB fait a la main : --tex-size 100 reussi", (r.returncode, (r.stdout + r.stderr)[-400:]))
if sortie.exists():
    gm, bm = lire_glb(sortie)
    rapport(max(ouvrir(vue(gm, bm, 0)).size) == 100 and gm["images"][0]["mimeType"] == "image/jpeg", "image ordinaire opaque reduite a 100 pixels, rangee en JPEG", (ouvrir(vue(gm, bm, 0)).size, gm["images"][0]["mimeType"]))
    rapport(vue(gm, bm, 1) == png_pbr, "image d'un materiau pbr- : intacte, memes octets (taille 300 laissee)")
    rapport(vue(gm, bm, 2) == geom and vue(gm, bm, 3) == b"\x07" * 61 and gm["bufferViews"][2].get("byteStride") == 12 and gm["bufferViews"][2].get("target") == 34962, "geometrie et vue de 61 octets recopiees, byteStride et target gardes")
    rapport(gm["images"][2] == {"uri": "ailleurs.png"}, "image hors du GLB (adresse) : intacte")
    rapport(gm["images"][3]["bufferView"] == 0 and gm["images"][3]["mimeType"] == gm["images"][0]["mimeType"], "deux images sur la meme vue : reduites une fois, type MIME mis a jour pour les deux")
    rapport(all(gm["bufferViews"][i].get("byteOffset", 0) % 4 == 0 for i in range(4)), "decalages de toutes les vues alignes sur 4 octets (vue de 61 octets comprise)")
    rapport("[textures] 1 sur 1 modifi" in r.stdout and "1 textures ordinaires" in r.stdout, "bilan : 1 image ordinaire, modifiee (l'image pbr- et l'image hors du GLB ne sont pas comptees ; la vue partagee compte une fois)", r.stdout[-300:])

# EXT_meshopt_compression : zone du tampon 0, vue de repli dans un autre tampon
zone_a, zone_b = b"\xaa" * 70, b"\xbb" * 33
blob, offs = assembler([zone_a, png_grand, zone_b])
g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": 0}, {"byteLength": 200, "uri": "data:application/octet-stream;base64,AAAA", "extensions": {"EXT_meshopt_fallback": {}}}],
     "bufferViews": [{"buffer": 1, "byteOffset": 0, "byteLength": 200, "extensions": {"EXT_meshopt_compression": {"buffer": 0, "byteOffset": offs[0], "byteLength": len(zone_a), "byteStride": 12, "mode": "ATTRIBUTES", "count": 5}}},
                     {"buffer": 0, "byteOffset": offs[1], "byteLength": len(png_grand)},
                     {"buffer": 1, "byteOffset": 0, "byteLength": 100, "extensions": {"EXT_meshopt_compression": {"buffer": 0, "byteOffset": offs[2], "byteLength": len(zone_b), "byteStride": 4, "mode": "TRIANGLES", "count": 3}}}],
     "images": [{"bufferView": 1, "mimeType": "image/png"}], "textures": [{"source": 0}], "materials": [{"name": "m", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}]}
mo = tmp / "meshopt.glb"
ecrire(mo, g, blob)
r = executer([sys.executable, str(TOOL), "--tex-only", str(mo), "--tex-size", "100"])
rapport(r.returncode == 0 and (tmp / "meshopt-tex100.glb").exists(), "GLB avec zones EXT_meshopt_compression : --tex-size 100 reussi", (r.returncode, (r.stdout + r.stderr)[-300:]))
if (tmp / "meshopt-tex100.glb").exists():
    gx, bx = lire_glb(tmp / "meshopt-tex100.glb")
    ea = gx["bufferViews"][0]["extensions"]["EXT_meshopt_compression"]; eb = gx["bufferViews"][2]["extensions"]["EXT_meshopt_compression"]
    rapport(bx[ea["byteOffset"]:ea["byteOffset"] + ea["byteLength"]] == zone_a and bx[eb["byteOffset"]:eb["byteOffset"] + eb["byteLength"]] == zone_b and ea["byteOffset"] % 4 == 0 and eb["byteOffset"] % 4 == 0,
            "zones meshopt du tampon 0 : recopiees a l'identique et repointees (decalage dans l'extension)", (ea, eb))
    rapport(gx["bufferViews"][0]["byteOffset"] == 0 and gx["bufferViews"][0]["byteLength"] == 200 and gx["bufferViews"][0]["buffer"] == 1 and gx["buffers"][1]["byteLength"] == 200, "vue de repli (tampon 1) : inchangee")
    rapport(max(ouvrir(vue(gx, bx, 1)).size) == 100, "image du meme GLB reduite")

# rien a modifier
png_petit = octets(photo(50, 40), "PNG")
blob, offs = assembler([png_petit])
g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": 0}], "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(png_petit)}], "images": [{"bufferView": 0, "mimeType": "image/png"}]}
rien = tmp / "rien.glb"
ecrire(rien, g, blob)
r = executer([sys.executable, str(TOOL), "--tex-only", str(rien), "--tex-size", "128"])
rapport(r.returncode == 0 and "rien à modifier" in r.stdout and not (tmp / "rien-tex128.glb").exists() and not list(tmp.glob("rien*.part")), "rien a modifier : le dit, aucun fichier ecrit", (r.returncode, r.stdout[-300:], list(tmp.glob("rien*"))))

# ---------- Pillow absent ----------
code_pil = ("import sys, runpy; sys.modules['PIL'] = None; sys.modules['PIL.Image'] = None; sys.argv = %r; runpy.run_path(%r, run_name='__main__')"
            % ([str(TOOL), "--tex-only", str(glb), "--tex-size", "128", "--output", str(tmp / "sans_pil.glb")], str(TOOL)))
r = executer([sys.executable, "-c", code_pil])
rapport(r.returncode != 0 and "Pillow" in (r.stdout + r.stderr) and not (tmp / "sans_pil.glb").exists(), "Pillow absent : message clair, aucun fichier", (r.returncode, (r.stdout + r.stderr)[-200:]))

# ---------- aide ----------
r = executer([sys.executable, str(TOOL), "--help"])
aide = " ".join(r.stdout.split())
rapport("--tex-only GLB" in aide and "sans refaire la conversion" in aide and "jamais modifié" in aide and "tex512.glb" in aide and "q60.glb" in aide, "l'aide decrit --tex-only (sans refaire la conversion, original jamais modifie, noms de sortie)", aide[aide.find("--tex-only"):][:300])
rapport("--terrain-only ou --tex-only" in aide, "l'aide de --output cite --tex-only")
rapport("--tex-only MaRegion.glb --tex-size 1024" in aide, "l'exemple de --tex-only figure dans l'aide")

print("\nRÉSULTAT : " + ("tout est passé" if not bad else f"ÉCHEC ({bad})"))
sys.exit(1 if bad else 0)
