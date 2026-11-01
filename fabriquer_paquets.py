#!/usr/bin/env python3
"""Fabrique les paquets prets a l'emploi (zips) a partir de paquets/ et de dist/.

Usage :  python fabriquer_paquets.py                  (zips dans paquets-zip/ ; lib/ telechargee de jsDelivr au premier lancement)
         python fabriquer_paquets.py --vendor DOSSIER (racine d'un paquet npm three deja present : hors ligne)
         python fabriquer_paquets.py --out DOSSIER    (sortie ailleurs que paquets-zip/)

Chaque dossier de paquets/ (galerie-photos, region-simple...) contient les sources du paquet (notices, scripts, config, zones, GLB, images).
Y sont ajoutes a la fabrication : site/index.html et site/favicon.ico (dist/), site/lib/three-X/ (ecrit par glb2html), presence/presence_server.py (dist/),
VERSION.txt ; la marque __VERSION_PRESENCE__ des notices est remplacee par la version du serveur de presence ; les .bat et .ps1 sont ecrits en CRLF.
Prerequis : python build.py (dist/ a jour : python tests/dist_a_jour.py).
"""
import argparse, pathlib, re, shutil, sys, zipfile

ROOT = pathlib.Path(__file__).resolve().parent
DIST = ROOT / "dist"
SRC = ROOT / "paquets"

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--vendor", type=pathlib.Path, help="racine d'un paquet npm three (sinon telechargement dans le cache de glb2html)")
ap.add_argument("--out", type=pathlib.Path, default=ROOT / "paquets-zip", help="dossier de sortie (defaut : paquets-zip/)")
args = ap.parse_args()

for f in ("index.html", "favicon.ico", "presence_server.py", "glb2html.py"):
    if not (DIST / f).is_file():
        sys.exit(f"ERREUR : dist/{f} introuvable : lance python build.py d'abord.")
if not SRC.is_dir():
    sys.exit("ERREUR : dossier paquets/ introuvable.")

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
m = re.search(r"\((\d\d)/(\d\d)/(\d{4})\)", version)
date_zip = (int(m[3]), int(m[2]), int(m[1]), 0, 0, 0) if m else (2026, 1, 1, 0, 0, 0)   # date de la version : zips reproductibles
mv = re.search(r'^VERSION = "(.+)"', (DIST / "presence_server.py").read_text(encoding="utf-8"), re.M)
version_presence = mv[1] if mv else "?"

sys.path.insert(0, str(DIST))
import glb2html   # noqa: E402  (ecrit lib/three-X/ comme le fait --shared-shell)

TEXTES = {".txt", ".md", ".html", ".json", ".bat", ".ps1"}
args.out.mkdir(parents=True, exist_ok=True)
tmp_racine = args.out / "_assemblage"
if tmp_racine.exists():
    shutil.rmtree(tmp_racine)

for paquet in sorted(p for p in SRC.iterdir() if p.is_dir()):
    nom = paquet.name
    tmp = tmp_racine / nom
    shutil.copytree(paquet, tmp)
    (tmp / "site").mkdir(exist_ok=True)
    (tmp / "presence").mkdir(exist_ok=True)
    shutil.copy2(DIST / "index.html", tmp / "site" / "index.html")
    shutil.copy2(DIST / "favicon.ico", tmp / "site" / "favicon.ico")
    shutil.copy2(DIST / "presence_server.py", tmp / "presence" / "presence_server.py")
    glb2html.write_modular_lib(tmp / "site", args.vendor)
    (tmp / "VERSION.txt").write_text(f"Web_3d {version}\nserveur de presence : {version_presence}\n", encoding="utf-8")
    for f in tmp.rglob("*"):
        if f.is_file() and f.suffix.lower() in (".txt", ".md") and f.name != "presence_server.py":
            t = f.read_bytes().decode("utf-8")
            if "__VERSION_PRESENCE__" in t:
                f.write_bytes(t.replace("__VERSION_PRESENCE__", version_presence).encode("utf-8"))
    zip_path = args.out / f"{nom}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(p for p in tmp.rglob("*") if p.is_file()):
            data = f.read_bytes()
            if f.suffix.lower() in (".bat", ".ps1"):
                data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")   # Windows : fins de ligne CRLF
            zi = zipfile.ZipInfo(f"{nom}/{f.relative_to(tmp).as_posix()}", date_time=date_zip)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, data)
    print(f"[OK] {zip_path} ({zip_path.stat().st_size / 1048576:.2f} Mo, {sum(1 for _ in tmp.rglob('*') if _.is_file())} fichiers)")
shutil.rmtree(tmp_racine)
