#!/usr/bin/env python3
"""Option --tex-size / --tex-quality de tools/oar2glb.py : reduction des textures ordinaires du GLB (OAR minimal et faux convoar, aucun .exe).

Unites : tex_reduire (grande texture opaque -> JPEG a la bonne taille ; grande texture a transparence -> PNG avec son canal alpha, dont une palette ;
petite texture, octets illisibles -> octets d'origine) ; pack_glb sans reduction : images identiques aux fichiers (sens inverse).
Bout en bout : le faux convoar fournit un glTF avec une grande texture opaque, une grande texture a transparence et une petite ; avec --tex-size
les deux grandes sont reduites (type MIME, taille en pixels, alpha gardee), la petite ne change pas, le GLB est plus leger ; sans l'option le GLB
garde les octets d'origine ; valeurs refusees (--tex-size 5, --tex-quality 0), Pillow absent : message clair avant toute conversion.
Prerequis : pip install pillow. Lancer : python tests/tex_size.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import io, json, pathlib, struct, subprocess, sys, tarfile, tempfile

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
    """image de test : degrade et bruit deterministe (compressible, pas unie)"""
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = ((x * 255) // max(w - 1, 1), (y * 255) // max(h - 1, 1), (x * 7 + y * 13) % 256)
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
d, red = T.tex_reduire(petite, 128, 85)
rapport(d == petite and not red, "texture deja assez petite : octets d'origine, non reduite")
d, red = T.tex_reduire(opaque, 512, 85)
rapport(d == opaque and not red, "taille egale a la limite : octets d'origine, non reduite")
d, red = T.tex_reduire(b"pas une image", 128, 85)
rapport(d == b"pas une image" and not red, "octets illisibles : rendus tels quels, sans erreur")
fort = len(T.tex_reduire(opaque, 128, 95)[0]); faible = len(T.tex_reduire(opaque, 128, 30)[0])
rapport(faible < fort, "la qualite agit sur la taille du JPEG", (faible, fort))

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
T.pack_glb(gltf_pack(), base, tmp / "avec.glb", (128, 85))
js, blob = lire_glb(tmp / "avec.glb")
ims = [lire(blob[js["bufferViews"][i["bufferView"]]["byteOffset"]:][:js["bufferViews"][i["bufferView"]]["byteLength"]]) for i in js["images"]]
rapport([i["mimeType"] for i in js["images"]] == ["image/jpeg", "image/png", "image/png"] and [max(i.size) for i in ims] == [128, 128, 64],
        "pack_glb avec reduction : types MIME et tailles (JPEG 128, PNG 128, petite PNG 64 inchangee)", ([i["mimeType"] for i in js["images"]], [i.size for i in ims]))
rapport(T.TEX_STATS["reduites"] == 2 and T.TEX_STATS["total"] == 3 and T.TEX_STATS["apres"] < T.TEX_STATS["avant"], "pack_glb : decompte (2 reduites sur 3, octets en moins)", T.TEX_STATS)
rapport((tmp / "avec.glb").stat().st_size < (tmp / "sans.glb").stat().st_size, "pack_glb : le GLB reduit est plus leger")

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

# ---------- valeurs refusees, Pillow absent ----------
for opt, val in (("--tex-size", "5"), ("--tex-size", "9000"), ("--tex-size", "-1"), ("--tex-quality", "0"), ("--tex-quality", "96")):
    o, f = fabriquer(tmp / ("v" + opt[2:5] + val.replace("-", "m")))
    r = lancer(o, f, opt, val, *(["--tex-size", "128"] if opt == "--tex-quality" else []))
    rapport(r.returncode != 0 and "[ERREUR]" in (r.stdout + r.stderr) and not o.with_suffix(".glb").exists(), f"{opt} {val} refuse avant toute conversion", (r.returncode, (r.stdout + r.stderr)[-200:]))
o, f = fabriquer(tmp / "sanspil")
code = ("import sys, runpy; sys.modules['PIL'] = None; sys.modules['PIL.Image'] = None; sys.argv = %r; runpy.run_path(%r, run_name='__main__')"
        % ([str(TOOL), str(o), "--convoar", str(f), "--nopause", "--no-pbr", "--tex-size", "128"], str(TOOL)))
r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=tmp)
rapport(r.returncode != 0 and "Pillow" in (r.stdout + r.stderr) and not o.with_suffix(".glb").exists(), "Pillow absent : message clair, aucune conversion", (r.returncode, (r.stdout + r.stderr)[-300:]))
r = subprocess.run([sys.executable, str(TOOL), "--help"], capture_output=True, text=True, cwd=tmp, stdin=subprocess.DEVNULL)
rapport("--tex-size" in r.stdout and "--tex-quality" in r.stdout, "l'aide cite --tex-size et --tex-quality")

print("\nRÉSULTAT : " + ("tout est passé" if not bad else f"ÉCHEC ({bad})"))
sys.exit(1 if bad else 0)
