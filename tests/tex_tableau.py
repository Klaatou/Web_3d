#!/usr/bin/env python3
"""Tableau des tailles de textures : fin de conversion de tools/oar2glb.py et rapport de tools/glb-stats.py (Chromium inutile ; Pillow pour fabriquer les images).

Unites : taille_image lit largeur et hauteur dans l'en-tete d'un PNG, d'un JPEG (dont progressif, avec de gros segments avant la taille), d'un GIF, d'un BMP, sans decoder ;
None pour des octets inconnus ou tronques ; les deux outils donnent les memes resultats (code duplique). tex_tranches : bornes 256, 512, 1024, 2048 (256 dans la premiere
tranche, 257 dans la deuxieme, etc.), images de taille non lue a part. glb-stats : un GLB fabrique a la main (images ordinaires, image d'un materiau pbr-, image hors du GLB).
Bout en bout : le faux convoar fournit trois textures (512 x 384, 512 x 512 transparente, 64 x 64) ; oar2glb affiche le tableau des tailles d'origine (avec et sans
--tex-size, sans Pillow aussi) et glb-stats donne la repartition du GLB obtenu (reduit ou non).
Prerequis : pip install pillow. Lancer : python tests/tex_tableau.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import importlib.util, io, json, os, pathlib, random, struct, subprocess, sys, tarfile, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "oar2glb.py"
sys.path.insert(0, str(ROOT / "tools"))
import oar2glb as T  # noqa: E402
from PIL import Image  # noqa: E402

spec = importlib.util.spec_from_file_location("glb_stats", ROOT / "tools" / "glb-stats.py")
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

tmp = pathlib.Path(tempfile.mkdtemp(prefix="tex_tableau_"))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")      # sortie des outils toujours en UTF-8 et lue en UTF-8 (sous Windows, la console est en cp1252 : --help aurait un autre codage)
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


def octets(im, fmt, **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return b.getvalue()


def photo(w, h):
    """degrade doux avec un leger bruit deterministe (le PNG est lourd, le JPEG beaucoup moins)"""
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


def executer(args, **kw):
    return subprocess.run(args, capture_output=True, encoding="utf-8", errors="replace", env=ENV, cwd=tmp, **kw)


def lecteur(data):
    return lambda p, k: data[p:p + k]


# ---------- unites : taille_image ----------
jpg = octets(photo(123, 77), "JPEG", quality=80)
app = lambda n, c: b"\xff" + bytes([c]) + struct.pack(">H", 2 + n) + b"x" * n
echantillons = {
    "PNG 300 x 200": (octets(photo(300, 200), "PNG"), (300, 200)),
    "JPEG 123 x 77": (jpg, (123, 77)),
    "JPEG progressif 90 x 140": (octets(photo(90, 140), "JPEG", progressive=True), (90, 140)),
    "JPEG avec deux gros segments avant la taille": (jpg[:2] + app(5000, 0xE1) + app(9000, 0xE2) + jpg[2:], (123, 77)),
    "GIF 17 x 9": (octets(photo(17, 9).quantize(32), "GIF"), (17, 9)),
    "BMP 40 x 30": (octets(photo(40, 30), "BMP"), (40, 30)),
}
for nom, (data, attendu) in echantillons.items():
    a = S.taille_image(lecteur(data), len(data)); b = T.taille_image(lecteur(data), len(data))
    rapport(a is not None and b is not None and tuple(a) == attendu and tuple(b) == attendu, "taille_image : " + nom + " (glb-stats et oar2glb)", (a, b, attendu))
jpg_tronque = jpg[:2] + app(5000, 0xE1)
for nom, data in (("octets inconnus", b"ceci n'est pas une image du tout, rien a lire"), ("vide", b""), ("PNG tronque", b"\x89PNG\r\n\x1a\n\x00\x00"),
                  ("JPEG tronque avant la taille", jpg_tronque), ("JPEG qui finit avant la taille", b"\xff\xd8\xff\xd9")):
    a = S.taille_image(lecteur(data), len(data)); b = T.taille_image(lecteur(data), len(data))
    rapport(a is None and b is None, "taille_image : " + nom + " : None, sans erreur", (a, b))

# ---------- unites : tex_tranches ----------
tailles = [(256, 10), (257, 20), (512, 30), (1024, 40), (2048, 50), (2049, 60), (3000, 1), (None, 5), (100, 2)]
attendu = [(0, 256, 2, 12), (256, 512, 2, 50), (512, 1024, 1, 40), (1024, 2048, 1, 50), (2048, None, 2, 61), (None, None, 1, 5)]
rapport(S.tex_tranches(tailles) == attendu and T.tex_tranches(tailles) == attendu, "tex_tranches : bornes 256 / 512 / 1024 / 2048 (la borne haute est dans sa tranche), au-dela, non lues", (S.tex_tranches(tailles), T.tex_tranches(tailles)))
rapport(S.tex_tranches([(300, 1)]) == [(256, 512, 1, 1)], "tex_tranches : une seule tranche non vide", S.tex_tranches([(300, 1)]))
rapport(S.tex_tranches([]) == [] and T.tex_tranches([]) == [], "tex_tranches : aucune image, aucune tranche")
rapport(T.tex_tableau([]) == [], "tex_tableau : aucune texture, aucune ligne")

# ---------- unite : glb-stats sur un GLB fait a la main ----------
png512, jpg100, png256 = octets(photo(512, 512), "PNG"), octets(photo(100, 100), "JPEG"), octets(photo(256, 200), "PNG")


def pad4(b, c=b"\x00"):
    return b + c * ((4 - len(b) % 4) % 4)


def ecrire_glb(chemin, images, materiaux, textures, uri_en_plus=False):
    blob = bytearray(); vues = []
    for d in images:
        vues.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(d)})
        blob += pad4(d)
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}], "bufferViews": vues,
         "images": [{"bufferView": i, "mimeType": "image/png"} for i in range(len(images))] + ([{"uri": "ailleurs.png"}] if uri_en_plus else []),
         "textures": textures, "materials": materiaux}
    js = pad4(json.dumps(g).encode(), b" ")
    chemin.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js
                       + struct.pack("<I4s", len(blob), b"BIN\0") + bytes(blob))
    return len(js)


glb_main = tmp / "main.glb"
nj = ecrire_glb(glb_main, [png512, jpg100, png256],
                [{"name": "ordinaire", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}},
                 {"name": "autre", "pbrMetallicRoughness": {"baseColorTexture": {"index": 1}}},
                 {"name": "pbr-abcd1234", "pbrMetallicRoughness": {"baseColorTexture": {"index": 2}}, "normalTexture": {"index": 2}}],
                [{"source": 0}, {"source": 1}, {"source": 2}], uri_en_plus=True)
g = json.loads(glb_main.read_bytes()[20:20 + nj])
lignes = S.tableau_textures(str(glb_main), g, nj)
texte = "\n".join(lignes)
rapport("Textures ordinaires : 3," in texte and "plus grand côté : 512 px" in texte, "glb-stats : 3 textures ordinaires (dont une hors du GLB), plus grand côté 512", texte)
rapport("jusqu'à 256 px : 1 images" in texte and "257 à 512 px : 1 images" in texte and "taille non lue : 1 images" in texte, "glb-stats : tranches des ordinaires (100 px, 512 px, image hors du GLB non lue)", texte)
rapport("Images de matériaux PBR : 1," in texte and "plus grand côté : 256 px" in texte, "glb-stats : l'image du matériau pbr- est comptée à part (256 px)", texte)
rapport("Aucune image" in "\n".join(S.tableau_textures(str(glb_main), {"images": []}, nj)), "glb-stats : GLB sans image : le dit")

# ---------- bout en bout : OAR minimal, faux convoar ----------
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


def lancer(oar, fake, *extra):
    return executer([sys.executable, str(TOOL), str(oar), "--convoar", str(fake), "--nopause", "--no-pbr", *extra])


def stats(glb):
    r = executer([sys.executable, str(ROOT / "tools" / "glb-stats.py"), str(glb)])
    return r.returncode, r.stdout + r.stderr


oar1, fake1 = fabriquer(tmp / "e1")
r1 = lancer(oar1, fake1)
sortie = r1.stdout
rapport(r1.returncode == 0 and "[textures] 3 textures ordinaires" in sortie and "(plus grand côté : 512 px)" in sortie, "bout en bout : l'en-tête du tableau (3 textures, plus grand côté 512)", sortie[-700:])
rapport("jusqu'à 256 px : 1 textures" in sortie and "257 à 512 px : 2 textures" in sortie and "513 à 1024" not in sortie, "bout en bout : 1 texture jusqu'à 256 px, 2 de 257 à 512 px, aucune autre tranche", sortie[-700:])
code, texte = stats(oar1.with_suffix(".glb"))
rapport(code == 0 and "257 à 512 px : 2 images" in texte and "jusqu'à 256 px : 1 images" in texte and "Textures ordinaires : 3" in texte, "bout en bout : glb-stats du GLB obtenu donne la meme repartition", texte[-600:])
rapport("PBR" not in texte.split("Tailles des textures")[-1], "bout en bout : sans matériau PBR, glb-stats n'ajoute pas de ligne PBR", texte[-300:])

oar2, fake2 = fabriquer(tmp / "e2")
r2 = lancer(oar2, fake2, "--tex-size", "128")
rapport(r2.returncode == 0 and "257 à 512 px : 2 textures" in r2.stdout and "[textures] 2 sur 3 réduite" in r2.stdout, "bout en bout --tex-size 128 : le tableau garde les tailles d'origine, puis le compte rendu de la réduction", r2.stdout[-800:])
code, texte = stats(oar2.with_suffix(".glb"))
rapport(code == 0 and "jusqu'à 256 px : 3 images" in texte and "257 à 512" not in texte, "bout en bout --tex-size 128 : glb-stats du GLB réduit : les 3 images sont maintenant sous 256 px", texte[-600:])

o3, f3 = fabriquer(tmp / "e3")
code_pil = ("import sys, runpy; sys.modules['PIL'] = None; sys.modules['PIL.Image'] = None; sys.argv = %r; runpy.run_path(%r, run_name='__main__')"
            % ([str(TOOL), str(o3), "--convoar", str(f3), "--nopause", "--no-pbr"], str(TOOL)))
r3 = executer([sys.executable, "-c", code_pil])
rapport(r3.returncode == 0 and "257 à 512 px : 2 textures" in r3.stdout, "bout en bout sans Pillow : le tableau s'affiche quand même (lecture des en-têtes seulement)", (r3.returncode, (r3.stdout + r3.stderr)[-500:]))

r = executer([sys.executable, str(ROOT / "tools" / "glb-stats.py"), "--help"], stdin=subprocess.DEVNULL)
aide = " ".join(r.stdout.split())
rapport("jamais la géométrie ni les pixels des textures" in aide, "l'aide de glb-stats dit qu'il lit le début de chaque image (plus « uniquement l'en-tête JSON »)", aide[:400])

print("\nRÉSULTAT : " + ("tout est passé" if not bad else f"ÉCHEC ({bad})"))
sys.exit(1 if bad else 0)
