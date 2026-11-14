#!/usr/bin/env python3
"""oars2site.py : un dossier d'OAR devient un site web Web_3d (faux convoar, aucun .exe ; utilise dist\\, donc lancer python build.py avant).

Un dossier de quatre OAR (dont un nom a espace, un qui echoue, un dont le GLB existe deja a cote) : deux regions converties, deux en echec sans bloquer les autres,
site complet (coquille, lib, default.json, regions.json), journaux et fichiers de travail hors du site, rapport JSON, OAR et GLB d'entree intacts ; second passage :
les regions faites sont sautees ; --force avec tuiles puis retour a un GLB seul (aucun ancien fichier) ; vignettes ; --tex-size, --tex-quality ; --keep-work ; --reuse-glb ;
--dry-run (rien d'ecrit) ; controle de version de oar2glb.py ; erreurs (dossier absent, vide, noms en double, outils introuvables, valeurs refusees) ; delai depasse ;
langues (--lang fr, --lang en, journaux dans la meme langue) ; --version ; carte.html copiee au debut si elle manque (jamais ecrasee) ; echec de glb2html sans
dossier a moitie fait (une region deja la reste intacte).
Prerequis : pip install pillow ; python build.py ; variable THREE_DIR hors ligne. Lancer : python tests/oars2site.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import hashlib, io, json, os, pathlib, random, shutil, struct, subprocess, sys, tarfile, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
OUTIL = DIST / "oars2site.py"
from PIL import Image  # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="oars2site_"))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


def executer(args, **kw):
    return subprocess.run(args, capture_output=True, encoding="utf-8", errors="replace", env=ENV, cwd=tmp, stdin=subprocess.DEVNULL, **kw)


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


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


def lire_glb(chemin):
    d = pathlib.Path(chemin).read_bytes()
    assert d[:4] == b"glTF" and struct.unpack_from("<I", d, 8)[0] == len(d)
    ln = struct.unpack_from("<I", d, 12)[0]
    g = json.loads(d[20:20 + ln].decode("utf-8"))
    blob = d[28 + ln:]
    imgs = []
    for im in g.get("images", []):
        v = g["bufferViews"][im["bufferView"]]
        imgs.append(blob[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]])
    return g, imgs


# ---------- les OAR et le faux convoar ----------
FAKE = '''#!/usr/bin/env python3
import sys, shutil, pathlib
a = sys.argv[1:]
if "bad" in " ".join(a):
    print("convoar : lecture impossible"); sys.exit(1)
out = pathlib.Path(a[a.index("--outputdir") + 1]); out.mkdir(exist_ok=True)
for f in pathlib.Path(__file__).with_name("fake_out").iterdir():
    shutil.copy(f, out / f.name)
print("fake convoar")
'''
zone = tmp / "convoar"; zone.mkdir()
fo = zone / "fake_out"; fo.mkdir()
(fo / "grande.png").write_bytes(octets(photo(512, 384), "PNG")); (fo / "feuille.png").write_bytes(octets(disque(512, 512), "PNG")); (fo / "petite.png").write_bytes(octets(photo(64, 64), "PNG"))
(fo / "scene.bin").write_bytes(struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0))
(fo / "scene.gltf").write_text(json.dumps({
    "asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0, "name": "Boite"}],
    "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "material": i} for i in range(3)]}],
    "materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": i}}} for i in range(3)], "textures": [{"source": i} for i in range(3)],
    "images": [{"uri": "grande.png"}, {"uri": "feuille.png"}, {"uri": "petite.png"}],
    "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3", "min": [0, 0, 0], "max": [1, 1, 0]}],
    "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36}], "buffers": [{"byteLength": 36, "uri": "scene.bin"}]}), encoding="utf-8")
fake = zone / "convoar_fake.py"; fake.write_text(FAKE); fake.chmod(0o755)
ARGS_CONVOAR = ["--oar2glb-arg=--convoar=" + str(fake), "--oar2glb-arg=--no-pbr"]


def faire_oar(chemin):
    with tarfile.open(chemin, "w:gz") as t:
        data = b"<archive><region_info><size_in_meters>256,256</size_in_meters></region_info></archive>"
        ti = tarfile.TarInfo("archive.xml"); ti.size = len(data)
        t.addfile(ti, io.BytesIO(data))


oars = tmp / "oars"; oars.mkdir()
for n in ("Alpha", "Beta Beach", "bad", "Gamma"):
    faire_oar(oars / (n + ".oar"))
(oars / "Gamma.glb").write_bytes(b"un GLB deja la")
sha_gamma = sha(oars / "Gamma.glb")
site = tmp / "site"
travail = tmp / "site_work"


def lancer(*args, dossier=oars, cible=site, tools=None):
    cmd = [sys.executable, str(OUTIL), str(dossier), str(cible), *vend, *ARGS_CONVOAR, *args]
    if tools:
        cmd += ["--tools", str(tools)]
    return executer(cmd)


def rapport_json():
    return {r["region"]: r for r in json.loads((travail / "conversion_report.json").read_text(encoding="utf-8"))["regions"]}


# ---------- --dry-run : rien d'ecrit ----------
r = lancer("--dry-run", "--lang", "fr")
rapport(r.returncode == 0 and "à convertir : Alpha.oar" in r.stdout and "à convertir : Beta Beach.oar" in r.stdout and not site.exists() and not travail.exists(), "--dry-run : liste les quatre OAR, n'ecrit rien (ni site ni dossier de travail)", (r.returncode, r.stdout[-400:], r.stderr[-200:]))
r = lancer("--dry-run", "--lang", "en")
rapport(r.returncode == 0 and "to convert: Alpha.oar" in r.stdout and "OAR(s)" in r.stdout, "--lang en : les messages sont en anglais", r.stdout[-300:])

# ---------- premier passage ----------
r = lancer("--lang", "en")
sortie = r.stdout
rapport(r.returncode == 1 and "[1/4]" in sortie and "[4/4]" in sortie and "done: 2 converted, 0 skipped, 2 failed" in sortie, "premier passage : 2 converties, 2 en echec, code de sortie 1", (r.returncode, sortie[-600:], r.stderr[-300:]))
rapport(all((site / n).exists() for n in ("index.html", "lib", "default.json", "regions.json")), "site : coquille commune, lib, default.json et regions.json a la racine", sorted(p.name for p in site.iterdir()) if site.exists() else None)
rapport((site / "Alpha" / "Alpha.glb").exists() and (site / "Alpha" / "Alpha.config.json").exists() and (site / "Beta_Beach" / "Beta_Beach.glb").exists(), "regions Alpha et Beta_Beach (nom a espace reduit en Beta_Beach) : GLB et config ecrits")
rapport(not (site / "bad").exists() and not (site / "Gamma").exists(), "regions en echec : aucun dossier dans le site")
rep = rapport_json() if (travail / "conversion_report.json").exists() else {}
rapport({k: v["status"] for k, v in rep.items()} == {"Alpha": "ok", "Beta_Beach": "ok", "bad": "failed", "Gamma": "failed"}, "rapport JSON : etats ok, ok, failed, failed", {k: v["status"] for k, v in rep.items()})
rapport("Gamma.glb already exists" in rep.get("Gamma", {}).get("message", "") and "oar2glb failed" in rep.get("bad", {}).get("message", ""), "messages d'echec : GLB deja present a cote ; oar2glb a echoue", {k: v["message"] for k, v in rep.items() if v["status"] == "failed"})
rapport(rep.get("Alpha", {}).get("address") == "index.html?region=Alpha/Alpha" and rep.get("Alpha", {}).get("mode") == "glb", "rapport : adresse de la region et mode glb")
regions = (site / "regions.json").read_text(encoding="utf-8") if (site / "regions.json").exists() else ""
rapport("Alpha" in regions and "Beta_Beach" in regions and "Gamma" not in regions, "regions.json : les deux regions converties, pas les autres", regions[:200])
rapport(not any(p.name.endswith("_work") or p.suffix == ".log" for p in site.rglob("*")), "journaux et dossier de travail : hors du site")
log = (travail / "logs" / "Alpha.log").read_text(encoding="utf-8") if (travail / "logs" / "Alpha.log").exists() else ""
rapport("[textures] 3 ordinary textures" in log and "glb2html" in log, "journal de la region : tableau des textures en anglais, appel de glb2html", log[:300])
rapport(not (travail / "Alpha").exists() and not (travail / "bad").exists(), "dossiers de travail des regions supprimes (aussi apres un echec)")
rapport(sha(oars / "Gamma.glb") == sha_gamma and not (oars / "Alpha.glb").exists() and not (oars / "Beta Beach.glb").exists(), "dossier d'entree : GLB d'origine intact, aucun GLB oublie a cote des OAR")

# ---------- second passage ----------
r = lancer("--lang", "en")
rapport(r.returncode == 1 and r.stdout.count("SKIPPED") == 2 and "done: 0 converted, 2 skipped, 2 failed" in r.stdout, "second passage : les deux regions faites sont sautees, les deux en echec echouent encore", r.stdout[-500:])

# ---------- --force, tuiles puis retour a un GLB seul ----------
r = lancer("--only", "^Alpha$", "--force", "--split", "always", "--lang", "en")
rapport(r.returncode == 0 and (site / "Alpha" / "Alpha.tiles.json").exists() and (site / "Alpha" / "Alpha.overview.glb").exists() and not (site / "Alpha" / "Alpha.glb").exists() and rapport_json()["Alpha"]["mode"] == "tiles", "--force --split always : tuiles et vue d'ensemble, plus de GLB seul", (r.returncode, r.stdout[-400:], sorted(p.name for p in (site / "Alpha").iterdir())))
r = lancer("--only", "^Alpha$", "--force", "--split", "never", "--lang", "en")
reste = sorted(p.name for p in (site / "Alpha").iterdir())
rapport(r.returncode == 0 and (site / "Alpha" / "Alpha.glb").exists() and not any("tiles" in n or "overview" in n for n in reste), "--force --split never : retour a un GLB seul, aucune ancienne tuile ni vue d'ensemble", reste)

# ---------- carte.html ; echec de glb2html ----------
carte_dist = DIST / "carte.html"
rapport((site / "carte.html").exists() and sha(site / "carte.html") == sha(carte_dist), "carte.html : copiee a la racine du site (celle de dist)")
(site / "carte.html").write_text("ma carte a moi", encoding="utf-8")
r = lancer("--only", "^Alpha$", "--force", "--lang", "en")
rapport(r.returncode == 0 and (site / "carte.html").read_text(encoding="utf-8") == "ma carte a moi" and "carte.html copied" not in r.stdout, "carte.html deja presente : jamais ecrasee, pas de message de copie", (r.returncode, r.stdout[-300:]))
(site / "carte.html").unlink()
r = lancer("--only", "^Alpha$", "--lang", "en")
rapport(r.returncode == 0 and sha(site / "carte.html") == sha(carte_dist) and "carte.html copied into the site" in r.stdout, "carte.html supprimee : recopiee au passage suivant, avec son message", (r.returncode, r.stdout[-300:]))
r = lancer("--dry-run", "--lang", "en", cible=tmp / "site_dry")
rapport(r.returncode == 0 and "to copy: carte.html" in r.stdout and not (tmp / "site_dry").exists(), "--dry-run : annonce la copie de carte.html, n'ecrit rien", (r.returncode, r.stdout[-300:]))
sans_carte = tmp / "outils_sans_carte"; sans_carte.mkdir()
for n in ("glb2html.py", "glb2tiles.py", "oar2glb.py", "glb-stats.py"):
    shutil.copy(DIST / n, sans_carte / n)
r = lancer("--only", "^Alpha$", "--lang", "en", cible=tmp / "site_sans_carte", tools=sans_carte)
rapport(r.returncode == 0 and "carte.html not found" in r.stdout and not (tmp / "site_sans_carte" / "carte.html").exists() and (tmp / "site_sans_carte" / "Alpha" / "Alpha.glb").exists(), "outils sans carte.html : avertissement, la conversion continue, pas de carte", (r.returncode, r.stdout[-400:]))
vide = tmp / "vendor_vide"; vide.mkdir()      # three.js absent : glb2html echoue apres avoir cree le dossier de la region
r = lancer("--only", "^Alpha$", "--lang", "en", "--vendor", str(vide), cible=tmp / "site_echec")
rapport(r.returncode == 1 and "glb2html failed" in r.stdout and not (tmp / "site_echec" / "Alpha").exists(), "glb2html echoue sur une region nouvelle : aucun dossier a moitie fait dans le site", (r.returncode, r.stdout[-300:], sorted(p.name for p in (tmp / "site_echec").iterdir()) if (tmp / "site_echec").exists() else None))
avant = {n: sha(site / "Alpha" / n) for n in ("Alpha.glb", "Alpha.config.json", "Alpha.zones.json")}
r = lancer("--only", "^Alpha$", "--force", "--lang", "en", "--html-arg=--option-inexistante")      # le site a deja sa lib : l'echec vient de l'option refusee par glb2html
apres = {n: sha(site / "Alpha" / n) for n in ("Alpha.glb", "Alpha.config.json", "Alpha.zones.json") if (site / "Alpha" / n).exists()}
rapport(r.returncode == 1 and apres == avant, "glb2html echoue sur une region deja la : ses fichiers restent tels quels (rien supprime avant la reussite)", (r.returncode, avant, apres))

# ---------- vignettes, textures ----------
miniatures = tmp / "vignettes"; miniatures.mkdir()
(miniatures / "Alpha.jpg").write_bytes(octets(photo(40, 30), "JPEG"))
r = lancer("--only", "^Alpha$", "--force", "--thumbs", str(miniatures), "--lang", "en")
rapport(r.returncode == 0 and (site / "Alpha" / "Alpha.jpg").exists() and "Alpha/Alpha.jpg" in (site / "regions.json").read_text(encoding="utf-8"), "--thumbs : la vignette est copiee a cote de la region et reprise par la carte", (r.returncode, r.stdout[-300:]))
r = lancer("--only", "^Alpha$", "--force", "--tex-size", "128", "--lang", "en")
g, imgs = lire_glb(site / "Alpha" / "Alpha.glb") if (site / "Alpha" / "Alpha.glb").exists() else ({}, [])
tailles = [max(Image.open(io.BytesIO(x)).size) for x in imgs]
rapport(r.returncode == 0 and tailles == [128, 128, 64], "--tex-size 128 : textures reduites dans le GLB du site (128, 128, 64)", (r.returncode, tailles, r.stdout[-300:]))
log = (travail / "logs" / "Alpha.log").read_text(encoding="utf-8")
rapport("2 of 3 reduced to 128 pixels" in log, "journal : compte rendu de la reduction")
r = lancer("--only", "^Alpha$", "--force", "--tex-quality", "40", "--lang", "en")
g, imgs = lire_glb(site / "Alpha" / "Alpha.glb")
tailles = [Image.open(io.BytesIO(x)).size for x in imgs]
rapport(r.returncode == 0 and tailles == [(512, 384), (512, 512), (64, 64)] and [i["mimeType"] for i in g["images"]] == ["image/jpeg", "image/png", "image/jpeg"], "--tex-quality 40 seul : pixels d'origine, JPEG pour les opaques, transparente inchangee", (r.returncode, tailles, [i["mimeType"] for i in g["images"]]))

# ---------- --keep-work, --reuse-glb ----------
r = lancer("--only", "^Alpha$", "--force", "--keep-work", "--lang", "en")
rapport(r.returncode == 0 and (travail / "Alpha" / "Alpha.glb").exists(), "--keep-work : le GLB de travail est garde", (r.returncode, list(travail.glob("*"))))
shutil.copy(site / "Alpha" / "Alpha.glb", oars / "Gamma.glb")
sha_g2 = sha(oars / "Gamma.glb")
r = lancer("--only", "^Gamma$", "--reuse-glb", "--lang", "en")
rapport(r.returncode == 0 and (site / "Gamma" / "Gamma.glb").exists() and sha(oars / "Gamma.glb") == sha_g2, "--reuse-glb : le GLB present a cote de l'OAR est utilise, et laisse en place (copie, pas deplacement)", (r.returncode, r.stdout[-400:]))

# ---------- langues ----------
r = lancer("--only", "^Alpha$", "--force", "--lang", "fr")
log = (travail / "logs" / "Alpha.log").read_text(encoding="utf-8")
rapport(r.returncode == 0 and "terminé : 1 convertie(s), 0 sautée(s), 0 en échec" in r.stdout and "OK (glb" in r.stdout and "textures ordinaires" in log.split("=== ")[-1], "--lang fr : messages du script et journal des outils en francais", (r.stdout[-300:], log[-300:]))

# ---------- controle de version de oar2glb.py ----------
vieux = tmp / "outils_vieux"; vieux.mkdir()
for n in ("glb2html.py", "glb2tiles.py", "glb-stats.py"):
    shutil.copy(DIST / n, vieux / n)


def faux_oar2glb(version):
    (vieux / "oar2glb.py").write_text("import sys\nif '--version' in sys.argv:\n    print('oar2glb %s (13/11/2026), fingerprint abcd1234')\n    sys.exit(0)\nprint('ne fait rien')\n" % version, encoding="utf-8")


faux_oar2glb("1.10.19")
r = lancer("--tex-size", "128", "--dry-run", "--lang", "en", tools=vieux)
rapport(r.returncode != 0 and "1.10.19" in (r.stdout + r.stderr) and "1.10.20" in (r.stdout + r.stderr) and "too old for --tex-size" in (r.stdout + r.stderr), "oar2glb 1.10.19 + --tex-size : refuse, dit la version trouvee et la version requise", (r.returncode, (r.stdout + r.stderr)[-300:]))
faux_oar2glb("1.10.20")
r1 = lancer("--tex-size", "128", "--dry-run", "--lang", "en", tools=vieux)
r2 = lancer("--tex-quality", "40", "--dry-run", "--lang", "en", tools=vieux)
rapport(r1.returncode == 0 and r2.returncode != 0 and "1.10.21" in (r2.stdout + r2.stderr), "oar2glb 1.10.20 : --tex-size accepte, --tex-quality refuse (1.10.21 requise)", (r1.returncode, r2.returncode, (r2.stdout + r2.stderr)[-200:]))
faux_oar2glb("1.10.21")
r = lancer("--tex-quality", "40", "--dry-run", "--lang", "en", tools=vieux)
rapport(r.returncode == 0, "oar2glb 1.10.21 : --tex-quality accepte", (r.returncode, (r.stdout + r.stderr)[-200:]))
(vieux / "oar2glb.py").write_text("print('sans version')\n", encoding="utf-8")
r = lancer("--tex-size", "128", "--dry-run", "--lang", "en", tools=vieux)
rapport(r.returncode != 0 and "unknown version" in (r.stdout + r.stderr), "oar2glb sans numero de version lisible : refuse avec « unknown version »", (r.returncode, (r.stdout + r.stderr)[-200:]))
r = lancer("--dry-run", "--lang", "en", tools=vieux)
rapport(r.returncode == 0, "sans option de textures : aucun controle de version", (r.returncode, (r.stdout + r.stderr)[-200:]))

# ---------- delai depasse ----------
(vieux / "oar2glb.py").write_text("import time\ntime.sleep(20)\n", encoding="utf-8")
travail2 = tmp / "site_delai_work"
r = executer([sys.executable, str(OUTIL), str(oars), str(tmp / "site_delai"), "--only", "^Alpha$", "--timeout-min", "0.03", "--tools", str(vieux), "--lang", "en"])
log2 = (travail2 / "logs" / "Alpha.log").read_text(encoding="utf-8") if (travail2 / "logs" / "Alpha.log").exists() else ""
rapport(r.returncode == 1 and "TIMEOUT after 0.03 min" in log2 and "FAILED" in r.stdout, "--timeout-min : une etape trop longue est arretee, notee dans le journal, la region echoue", (r.returncode, r.stdout[-300:], log2[-200:]))

# ---------- erreurs ----------
def erreur(args, attendu, nom):
    r = executer([sys.executable, str(OUTIL), *args, "--lang", "en"])
    rapport(r.returncode != 0 and attendu in (r.stdout + r.stderr), nom, (r.returncode, (r.stdout + r.stderr)[-250:]))


vide = tmp / "vide"; vide.mkdir()
erreur([str(tmp / "absent"), str(tmp / "s1")], "not a folder", "dossier d'OAR absent : message clair")
erreur([str(vide), str(tmp / "s2")], "no .oar or .tgz file", "dossier sans OAR : message clair")
dou = tmp / "doubles"; dou.mkdir(); faire_oar(dou / "A b.oar"); faire_oar(dou / "A_b.oar")
erreur([str(dou), str(tmp / "s3")], "several OARs give the same region name", "deux OAR de meme nom de region : refuse avant tout travail")
erreur([str(oars), str(tmp / "s4"), "--tools", str(vide)], "not found", "outils introuvables : message clair")
erreur([str(oars), str(tmp / "s5"), "--tex-size", "5"], "--tex-size must be 0", "--tex-size 5 refuse")
erreur([str(oars), str(tmp / "s6"), "--tex-quality", "0"], "--tex-quality must be between 1 and 95", "--tex-quality 0 refuse")
rapport(not any((tmp / n).exists() for n in ("s1", "s2", "s3", "s4", "s5", "s6")), "erreurs : aucun site cree")

# ---------- --version, aide ----------
r = executer([sys.executable, str(OUTIL), "--version"])
rapport(r.returncode == 0 and r.stdout.startswith("oars2site "), "--version : oars2site et son numero", r.stdout + r.stderr)
r = executer([sys.executable, str(OUTIL), "--help", "--lang", "fr"])
aide = " ".join(r.stdout.split())
rapport(r.returncode == 0 and "--tex-size" in aide and "--dry-run" in aide and "docs/fr/CONVERTIR_OARS.md" in aide and "py.oars2site" not in aide, "--help en francais : options, exemple, renvoi vers le mode d'emploi, aucune cle brute", aide[:300])

print("\nRÉSULTAT : " + ("tout est passé" if not bad else f"ÉCHEC ({bad})"))
sys.exit(1 if bad else 0)
