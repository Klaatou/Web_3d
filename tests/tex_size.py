#!/usr/bin/env python3
"""Option --tex-size / --tex-quality de tools/oar2glb.py : reduction des textures ordinaires du GLB (OAR minimal et faux convoar, aucun .exe).

Unites : tex_reduire (grande texture opaque -> JPEG a la bonne taille ; grande texture a transparence -> PNG avec son canal alpha, dont une palette ;
petite texture, octets illisibles -> octets d'origine) ; pack_glb sans reduction : images identiques aux fichiers (sens inverse).
Bout en bout : le faux convoar fournit un glTF avec une grande texture opaque, une grande texture a transparence et une petite ; avec --tex-size
les deux grandes sont reduites (type MIME, taille en pixels, alpha gardee), la petite ne change pas, le GLB est plus leger ; sans l'option le GLB
garde les octets d'origine ; valeurs refusees (--tex-size 5, --tex-quality 0), Pillow absent : message clair avant toute conversion.
--tex-size (pixels) et --tex-quality (compression JPEG) sont independants : la qualite seule recompresse les textures opaques a leur taille ; avec les
deux, les textures trop grandes sont reduites puis compressees et les autres opaques recompressees ; une texture transparente n'est jamais recompressee.
Prerequis : pip install pillow. Lancer : python tests/tex_size.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import io, json, pathlib, random, struct, subprocess, sys, tarfile, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "oar2glb.py"
sys.path.insert(0, str(ROOT / "tools"))
import oar2glb as T  # noqa: E402
from PIL import Image  # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="tex_size_"))
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


def octets(im, fmt, **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return b.getvalue()


def degrade(w, h, mode="RGB"):
    """image de test : degrade doux avec un leger bruit deterministe (comme une photo : le PNG est lourd, le JPEG beaucoup moins)"""
    rnd = random.Random(w * 1000 + h)
    im = Image.new("RGB", (w, h))
    px = im.load()
    ok = lambda v: min(255, max(0, v))
    for y in range(h):
        for x in range(w):
            r, g, b = (x * 255) // max(w - 1, 1), (y * 255) // max(h - 1, 1), ((x + y) * 255) // max(w + h - 2, 1)
            px[x, y] = (ok(r + rnd.randint(-8, 8)), ok(g + rnd.randint(-8, 8)), ok(b + rnd.randint(-8, 8)))
    return im


def disque_alpha(w, h):
    """image RGBA : un disque opaque sur fond transparent"""
    im = degrade(w, h).convert("RGBA")
    a = Image.new("L", (w, h), 0)
    ap = a.load()
    cx, cy, r = w / 2, h / 2, min(w, h) / 2 - 2
    for y in range(h):
        for x in range(w):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                ap[x, y] = 255
    im.putalpha(a)
    return im


def lire(data):
    im = Image.open(io.BytesIO(data)); im.load(); return im


# ---------- unites : tex_reduire ----------
opaque = octets(degrade(512, 384), "PNG")
d, red = T.tex_reduire(opaque, 128, 85)
im = lire(d)
rapport(red and im.format == "JPEG" and max(im.size) == 128 and im.size == (128, 96), "grande texture opaque : JPEG, 128 pixels au plus, proportions gardees", (red, im.format, im.size))
rapport(len(d) < len(opaque), "grande texture opaque : plus legere", (len(d), len(opaque)))

alpha = octets(disque_alpha(512, 512), "PNG")
d, red = T.tex_reduire(alpha, 128, 85)
im = lire(d)
mini = im.convert("RGBA").getchannel("A").getextrema()[0]
rapport(red and im.format == "PNG" and im.size == (128, 128) and mini < 255, "grande texture a transparence : PNG 128 x 128, canal alpha gardee", (red, im.format, im.size, mini))
rapport(im.convert("RGBA").getpixel((64, 64))[3] == 255 and im.convert("RGBA").getpixel((1, 1))[3] == 0, "transparence : centre opaque, coin transparent", None)

pal = degrade(300, 300).quantize(64)
pal.info["transparency"] = 0
pal_png = octets(pal, "PNG", transparency=0)
d, red = T.tex_reduire(pal_png, 100, 85)
im = lire(d)
rapport(red and im.format == "PNG" and im.size == (100, 100) and im.convert("RGBA").getchannel("A").getextrema()[0] < 255, "palette avec transparence : PNG, transparence gardee", (red, im.format, im.size))

rgba_plein = octets(degrade(256, 256).convert("RGBA"), "PNG")
d, red = T.tex_reduire(rgba_plein, 64, 85)
rapport(red and lire(d).format == "JPEG", "RGBA entierement opaque : JPEG (pas de transparence a garder)", lire(d).format)

petite = octets(degrade(64, 64), "PNG")
d, red = T.tex_reduire(petite, 128, None)
rapport(d == petite and not red, "texture deja assez petite : octets d'origine, non reduite")
d, red = T.tex_reduire(opaque, 512, None)
rapport(d == opaque and not red, "taille egale a la limite : octets d'origine, non reduite")
d, red = T.tex_reduire(b"pas une image", 128, 85)
rapport(d == b"pas une image" and not red, "octets illisibles : rendus tels quels, sans erreur")
fort = len(T.tex_reduire(opaque, 128, 95)[0]); faible = len(T.tex_reduire(opaque, 128, 30)[0])
rapport(faible < fort, "la qualite agit sur la taille du JPEG", (faible, fort))

# ---------- unites : taille seule, qualite seule, les deux (independantes) ----------
d, red = T.tex_reduire(opaque, 128, None)
rapport(red and lire(d).format == "JPEG" and max(lire(d).size) == 128, "taille seule : texture reduite en JPEG (qualite par defaut)", (red, lire(d).format))
d, red = T.tex_reduire(opaque, 0, 40)
im = lire(d)
rapport(red and im.format == "JPEG" and im.size == (512, 384) and len(d) < len(opaque), "qualite seule : JPEG aux dimensions d'origine, plus leger que l'original", (red, im.format, im.size, len(d), len(opaque)))
q95 = octets(degrade(256, 256), "JPEG", quality=95)
d, red = T.tex_reduire(q95, 0, 20)
rapport(red and len(d) < len(q95), "qualite seule : un JPEG d'origine est recompresse plus bas", (red, len(d), len(q95)))
q20 = octets(degrade(256, 256), "JPEG", quality=20)
d, red = T.tex_reduire(q20, 0, 95)
rapport(d == q20 and not red, "qualite seule : si la version recompressee n'est pas plus legere, l'original est garde", (len(d), len(q20)))
d, red = T.tex_reduire(alpha, 0, 40)
rapport(d == alpha and not red, "qualite seule : une texture transparente n'est jamais recompressee")
d, red = T.tex_reduire(petite, 128, 40)
im = lire(d)
rapport(red and im.format == "JPEG" and im.size == (64, 64) and len(d) < len(petite), "taille et qualite : une texture sous la limite est recompressee a ses dimensions", (red, im.format, im.size))
d, red = T.tex_reduire(opaque, 128, 40)
d85, _ = T.tex_reduire(opaque, 128, 85)
rapport(red and max(lire(d).size) == 128 and len(d) < len(d85), "taille et qualite : une texture trop grande est reduite puis compressee a la qualite demandee", (len(d), len(d85)))
d, red = T.tex_reduire(alpha, 128, 40)
im = lire(d)
rapport(red and im.format == "PNG" and im.size == (128, 128), "taille et qualite : une texture transparente trop grande est reduite en PNG (pas de JPEG)", (red, im.format, im.size))

# ---------- unite : pack_glb (avec et sans reduction) ----------
base = tmp / "pack"; base.mkdir()
(base / "a.png").write_bytes(opaque); (base / "b.png").write_bytes(alpha); (base / "c.png").write_bytes(petite)
(base / "s.bin").write_bytes(b"\x00" * 16)


def gltf_pack():
    return {"asset": {"version": "2.0"}, "buffers": [{"byteLength": 16, "uri": "s.bin"}], "bufferViews": [{"buffer": 0, "byteLength": 16}],
            "images": [{"uri": "a.png"}, {"uri": "b.png"}, {"uri": "c.png"}]}


def lire_glb(p):
    d = pathlib.Path(p).read_bytes()
    ln = struct.unpack_from("<I", d, 12)[0]
    js = json.loads(d[20:20 + ln].decode("utf-8"))
    off = 20 + ln + 8
    return js, d[off:]


T.TEX_STATS.update(total=0, reduites=0, avant=0, apres=0)
T.pack_glb(gltf_pack(), base, tmp / "sans.glb")
js, blob = lire_glb(tmp / "sans.glb")
tel = all(blob[js["bufferViews"][i["bufferView"]]["byteOffset"]:][:js["bufferViews"][i["bufferView"]]["byteLength"]] == o for i, o in zip(js["images"], (opaque, alpha, petite)))
rapport(tel and T.TEX_STATS["reduites"] == 0 and T.TEX_STATS["total"] == 3, "pack_glb sans reduction : les trois images gardent leurs octets d'origine", T.TEX_STATS)
T.TEX_STATS.update(total=0, reduites=0, avant=0, apres=0)
T.pack_glb(gltf_pack(), base, tmp / "avec.glb", (128, None))
js, blob = lire_glb(tmp / "avec.glb")
ims = [lire(blob[js["bufferViews"][i["bufferView"]]["byteOffset"]:][:js["bufferViews"][i["bufferView"]]["byteLength"]]) for i in js["images"]]
rapport([i["mimeType"] for i in js["images"]] == ["image/jpeg", "image/png", "image/png"] and [max(i.size) for i in ims] == [128, 128, 64],
        "pack_glb avec reduction : types MIME et tailles (JPEG 128, PNG 128, petite PNG 64 inchangee)", ([i["mimeType"] for i in js["images"]], [i.size for i in ims]))
rapport(T.TEX_STATS["reduites"] == 2 and T.TEX_STATS["total"] == 3 and T.TEX_STATS["apres"] < T.TEX_STATS["avant"], "pack_glb : decompte (2 reduites sur 3, octets en moins)", T.TEX_STATS)
rapport((tmp / "avec.glb").stat().st_size < (tmp / "sans.glb").stat().st_size, "pack_glb : le GLB reduit est plus leger")

T.TEX_STATS.update(total=0, reduites=0, avant=0, apres=0)
T.pack_glb(gltf_pack(), base, tmp / "qual.glb", (0, 40))
js, blob = lire_glb(tmp / "qual.glb")
parts = [blob[js["bufferViews"][i["bufferView"]]["byteOffset"]:][:js["bufferViews"][i["bufferView"]]["byteLength"]] for i in js["images"]]
ims = [lire(x) for x in parts]
rapport([i["mimeType"] for i in js["images"]] == ["image/jpeg", "image/png", "image/jpeg"] and [i.size for i in ims] == [(512, 384), (512, 512), (64, 64)] and parts[1] == alpha,
        "pack_glb qualite seule : opaques recompressees a leurs dimensions, transparente inchangee", ([i["mimeType"] for i in js["images"]], [i.size for i in ims]))
rapport(T.TEX_STATS["reduites"] == 2 and T.TEX_STATS["apres"] < T.TEX_STATS["avant"], "pack_glb qualite seule : 2 images modifiees sur 3, octets en moins", T.TEX_STATS)

# ---------- bout en bout : OAR minimal, faux convoar ----------
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
    pos = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0)
    (fo / "scene.bin").write_bytes(pos)
    prims = [{"attributes": {"POSITION": 0}, "material": i} for i in range(3)]
    g = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0, "name": "Boite"}],
         "meshes": [{"primitives": prims}],
         "materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": i}}} for i in range(3)],
         "textures": [{"source": i} for i in range(3)],
         "images": [{"uri": "grande.png"}, {"uri": "feuille.png"}, {"uri": "petite.png"}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3", "min": [0, 0, 0], "max": [1, 1, 0]}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36}], "buffers": [{"byteLength": 36, "uri": "scene.bin"}]}
    (fo / "scene.gltf").write_text(json.dumps(g), encoding="utf-8")
    fake = dossier / "convoar_fake.py"; fake.write_text(FAKE); fake.chmod(0o755)
    return oar, fake


def lancer(oar, fake, *extra):
    return subprocess.run([sys.executable, str(TOOL), str(oar), "--convoar", str(fake), "--nopause", "--no-pbr", *extra], capture_output=True, text=True, cwd=tmp)


oar1, fake1 = fabriquer(tmp / "e1")
r1 = lancer(oar1, fake1)
glb1 = oar1.with_suffix(".glb")
rapport(r1.returncode == 0 and glb1.exists(), "bout en bout sans option : conversion reussie", (r1.returncode, (r1.stdout + r1.stderr)[-500:]))
if glb1.exists():
    js, blob = lire_glb(glb1)
    tel = [blob[js["bufferViews"][i["bufferView"]]["byteOffset"]:][:js["bufferViews"][i["bufferView"]]["byteLength"]] for i in js["images"]]
    rapport(tel == [opaque, alpha, petite], "bout en bout sans option : les textures gardent leurs octets d'origine", [len(x) for x in tel])
    rapport("[textures]" not in r1.stdout, "bout en bout sans option : aucune ligne « textures » dans le compte rendu")

oar2, fake2 = fabriquer(tmp / "e2")
r2 = lancer(oar2, fake2, "--tex-size", "128")
glb2 = oar2.with_suffix(".glb")
rapport(r2.returncode == 0 and glb2.exists(), "bout en bout --tex-size 128 : conversion reussie", (r2.returncode, (r2.stdout + r2.stderr)[-500:]))
if glb2.exists() and glb1.exists():
    js, blob = lire_glb(glb2)
    ims = [(i["mimeType"], lire(blob[js["bufferViews"][i["bufferView"]]["byteOffset"]:][:js["bufferViews"][i["bufferView"]]["byteLength"]])) for i in js["images"]]
    rapport([m for m, _ in ims] == ["image/jpeg", "image/png", "image/png"] and [max(i.size) for _, i in ims] == [128, 128, 64],
            "bout en bout --tex-size 128 : grande opaque en JPEG 128, grande a transparence en PNG 128, petite inchangee", [(m, i.size) for m, i in ims])
    rapport(ims[1][1].convert("RGBA").getchannel("A").getextrema()[0] == 0, "bout en bout : la transparence de la feuille est gardee", ims[1][1].mode)
    rapport(glb2.stat().st_size < glb1.stat().st_size, "bout en bout : le GLB reduit est plus leger", (glb2.stat().st_size, glb1.stat().st_size))
    rapport("[textures] 2 sur 3" in r2.stdout, "bout en bout : le compte rendu dit 2 textures sur 3 reduites", r2.stdout[-400:])
    rapport(len(js["images"]) == 3 and len(js["materials"]) == 3, "bout en bout : meme nombre d'images et de materiaux", (len(js["images"]), len(js["materials"])))

oar3, fake3 = fabriquer(tmp / "e3")
r3 = lancer(oar3, fake3, "--tex-quality", "40")
glb3 = oar3.with_suffix(".glb")
rapport(r3.returncode == 0 and glb3.exists(), "bout en bout --tex-quality 40 seul : conversion reussie", (r3.returncode, (r3.stdout + r3.stderr)[-500:]))
if glb3.exists() and glb1.exists():
    js, blob = lire_glb(glb3)
    parts = [blob[js["bufferViews"][i["bufferView"]]["byteOffset"]:][:js["bufferViews"][i["bufferView"]]["byteLength"]] for i in js["images"]]
    ims = [lire(x) for x in parts]
    rapport([i["mimeType"] for i in js["images"]] == ["image/jpeg", "image/png", "image/jpeg"] and [i.size for i in ims] == [(512, 384), (512, 512), (64, 64)] and parts[1] == alpha,
            "bout en bout --tex-quality 40 seul : dimensions d'origine, JPEG pour les opaques, texture transparente inchangee", ([i["mimeType"] for i in js["images"]], [i.size for i in ims]))
    rapport(glb3.stat().st_size < glb1.stat().st_size, "bout en bout --tex-quality 40 seul : le GLB est plus leger", (glb3.stat().st_size, glb1.stat().st_size))
    rapport("[textures] 2 sur 3 recompress" in r3.stdout, "bout en bout --tex-quality 40 seul : le compte rendu dit 2 textures sur 3 recompressees", r3.stdout[-400:])

oar4, fake4 = fabriquer(tmp / "e4")
r4 = lancer(oar4, fake4, "--tex-size", "128", "--tex-quality", "40")
glb4 = oar4.with_suffix(".glb")
rapport(r4.returncode == 0 and glb4.exists(), "bout en bout --tex-size 128 --tex-quality 40 : conversion reussie", (r4.returncode, (r4.stdout + r4.stderr)[-500:]))
if glb4.exists() and glb2.exists():
    js, blob = lire_glb(glb4)
    ims = [(i["mimeType"], lire(blob[js["bufferViews"][i["bufferView"]]["byteOffset"]:][:js["bufferViews"][i["bufferView"]]["byteLength"]])) for i in js["images"]]
    rapport([m for m, _ in ims] == ["image/jpeg", "image/png", "image/jpeg"] and [i.size for _, i in ims] == [(128, 96), (128, 128), (64, 64)],
            "bout en bout les deux : opaque reduite en JPEG, transparente reduite en PNG, petite opaque recompressee", [(m, i.size) for m, i in ims])
    rapport(glb4.stat().st_size < glb2.stat().st_size, "bout en bout les deux : plus leger que la taille seule", (glb4.stat().st_size, glb2.stat().st_size))
    rapport("[textures] 3 sur 3 modifi" in r4.stdout, "bout en bout les deux : le compte rendu dit 3 textures sur 3 modifiees", r4.stdout[-400:])

# ---------- valeurs refusees, Pillow absent ----------
for opt, val in (("--tex-size", "5"), ("--tex-size", "9000"), ("--tex-size", "-1"), ("--tex-quality", "0"), ("--tex-quality", "96")):
    o, f = fabriquer(tmp / ("v" + opt[2:5] + val.replace("-", "m")))
    r = lancer(o, f, opt, val)
    rapport(r.returncode != 0 and "[ERREUR]" in (r.stdout + r.stderr) and not o.with_suffix(".glb").exists(), f"{opt} {val} refuse avant toute conversion", (r.returncode, (r.stdout + r.stderr)[-200:]))
o, f = fabriquer(tmp / "sanspil")
code = ("import sys, runpy; sys.modules['PIL'] = None; sys.modules['PIL.Image'] = None; sys.argv = %r; runpy.run_path(%r, run_name='__main__')"
        % ([str(TOOL), str(o), "--convoar", str(f), "--nopause", "--no-pbr", "--tex-size", "128"], str(TOOL)))
r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=tmp)
rapport(r.returncode != 0 and "Pillow" in (r.stdout + r.stderr) and not o.with_suffix(".glb").exists(), "Pillow absent : message clair, aucune conversion", (r.returncode, (r.stdout + r.stderr)[-300:]))
o, f = fabriquer(tmp / "sanspil2")
code = ("import sys, runpy; sys.modules['PIL'] = None; sys.modules['PIL.Image'] = None; sys.argv = %r; runpy.run_path(%r, run_name='__main__')"
        % ([str(TOOL), str(o), "--convoar", str(f), "--nopause", "--no-pbr", "--tex-quality", "40"], str(TOOL)))
r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=tmp)
rapport(r.returncode != 0 and "Pillow" in (r.stdout + r.stderr) and not o.with_suffix(".glb").exists(), "Pillow absent avec --tex-quality seul : message clair, aucune conversion", (r.returncode, (r.stdout + r.stderr)[-300:]))
r = subprocess.run([sys.executable, str(TOOL), "--help"], capture_output=True, text=True, cwd=tmp, stdin=subprocess.DEVNULL)
aide = " ".join(r.stdout.split())
rapport("--tex-size" in aide and "--tex-quality" in aide, "l'aide cite --tex-size et --tex-quality")
rapport("de 16 à 8192" in aide and "0 (défaut)" in aide, "l'aide donne les valeurs de N : 0 (défaut), de 16 à 8192", aide[aide.find("--tex-size N"):][:300])
rapport("de 1 (" in aide and "à 95 (" in aide and "sans changer leurs dimensions" in aide, "l'aide donne la plage de la qualite (1 à 95) et dit qu'elle ne change pas les dimensions", aide[aide.find("--tex-quality Q"):][:300])

print("\nRÉSULTAT : " + ("tout est passé" if not bad else f"ÉCHEC ({bad})"))
sys.exit(1 if bad else 0)
