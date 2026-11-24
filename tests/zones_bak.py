#!/usr/bin/env python3
"""Fichiers de zones et de config : sauvegarde .bak et fichier de destination donne comme source (1.13.13).

Verifie, sur une region en coquille commune (--shared-shell) :
  - --zones-only --zones <le NOM.zones.json de la region lui-meme> : fichier lu pour verification, JAMAIS reecrit (zone privee gardee, aucun .bak) ;
  - --zones-only avec une AUTRE source : l'ancien NOM.zones.json devient NOM.zones.json.bak, puis le nouveau est ecrit (profil public : zone privee retiree) ;
  - meme contenu : pas de .bak ; --config-only : l'ancien NOM.config.json devient NOM.config.json.bak ;
  - regenerer la region avec --zones <son NOM.zones.json> : zones intactes ; premiere ecriture : aucun .bak.
Prerequis : python build.py avant. Variable facultative : THREE_DIR.
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import json, os, pathlib, struct, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_zbak_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


def run(*a):
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), *map(str, a), *vend], capture_output=True, text=True, cwd=tmp)
    if r.returncode:
        sys.exit(f"[ECHEC] {' '.join(map(str, a))}\n{r.stdout}{r.stderr}")
    return r.stdout + r.stderr


def glb(path):
    v = [(-5, 0, -5), (5, 0, -5), (5, 0, 5), (-5, 0, 5)]
    pos = b"".join(struct.pack("<3f", *p) for p in v); ind = struct.pack("<6H", 0, 2, 1, 0, 3, 2)
    binb = pos + ind
    j = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}], "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-5, 0, -5], "max": [5, 0, 5]}, {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos)}, {"buffer": 0, "byteOffset": len(pos), "byteLength": len(ind)}], "buffers": [{"byteLength": len(binb)}]}
    js = json.dumps(j).encode(); js += b" " * (-len(js) % 4); binb += b"\0" * (-len(binb) % 4)
    path.write_bytes(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(binb)) + struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(binb), 0x004E4942) + binb)


def ids(p):
    return [z["id"] for z in json.loads(p.read_text(encoding="utf-8"))]


ZONES = [{"id": "default", "arrival": True, "x": 0, "y": 0, "z": 3}, {"id": "priv", "label": "Commande", "ha": "http://exemple.invalid/api", "private": True, "x": 1, "y": 0, "z": 1},
         {"id": "poste", "label": "Poste", "model": "poste.glb", "x": 2, "y": 0, "z": -2, "scale": 1.5, "solid": True}]
site = tmp / "site"; reg = site / "R"; reg.mkdir(parents=True)
glb(tmp / "R.glb")
zf = reg / "R.zones.json"; bak = reg / "R.zones.json.bak"; cbak = reg / "R.config.json.bak"
(tmp / "tous.json").write_text(json.dumps(ZONES), encoding="utf-8")

run(tmp / "R.glb", "--shared-shell", site / "index.html", "-o", reg / "R.html", "--no-sea", "--zones", tmp / "tous.json")
rapport(ids(zf) == ["default", "poste"] and not bak.exists() and not cbak.exists(), "premiere ecriture : zones publiques, aucun .bak", (ids(zf), bak.exists()))

# fichier de la region edite a la main : la zone privee y est, ainsi qu'une cle refusee
zf.write_text(json.dumps(ZONES), encoding="utf-8"); avant = zf.read_bytes()
sortie = run("-o", reg / "R.html", "--zones-only", "--zones", zf)
rapport(zf.read_bytes() == avant and not bak.exists() and "deja en place" in sortie.replace("déjà", "deja"), "--zones-only sur le fichier de la region : lu, jamais reecrit, aucun .bak", sortie)

run("-o", reg / "R.html", "--config-only", "--shared-shell", site / "index.html", "--zones", zf)
rapport(zf.read_bytes() == avant, "--config-only --zones sur le fichier de la region : zones intactes")
run(tmp / "R.glb", "--shared-shell", site / "index.html", "-o", reg / "R.html", "--no-sea", "--zones", zf)
rapport(zf.read_bytes() == avant and ids(zf) == ["default", "priv", "poste"], "regeneration avec --zones = fichier de la region : zones intactes")

# autre source : l'ancien devient .bak
(tmp / "autre.json").write_text(json.dumps(ZONES[:1] + ZONES[2:]), encoding="utf-8")
run("-o", reg / "R.html", "--zones-only", "--zones", tmp / "autre.json")
rapport(bak.is_file() and bak.read_bytes() == avant and ids(zf) == ["default", "poste"], "autre source : ancien fichier garde en .bak, nouveau ecrit en profil public", (bak.exists(), ids(zf)))
bak.unlink(missing_ok=True)
run("-o", reg / "R.html", "--zones-only", "--zones", tmp / "autre.json")
rapport(not bak.exists(), "meme contenu : pas de .bak")

# config
cfg = reg / "R.config.json"; c0 = cfg.read_bytes()
run("-o", reg / "R.html", "--config-only", "--shared-shell", site / "index.html", "--wave", "2")
rapport(cbak.is_file() and cbak.read_bytes() == c0 and cfg.read_bytes() != c0, "--config-only : ancien NOM.config.json garde en .bak")

cbak.unlink(missing_ok=True); c1 = cfg.read_bytes()
run("-o", reg / "R.html", "--update", "--shared-shell", site / "index.html", "--wave", "3")
rapport(cbak.is_file() and cbak.read_bytes() == c1 and cfg.read_bytes() != c1, "--update : ancien NOM.config.json garde en .bak")

print("\n" + ("TOUT PASSE" if not bad else f"{bad} ECHEC(S)"))
sys.exit(1 if bad else 0)
