#!/usr/bin/env python3
"""Le generateur complete les noms d'image sans extension (« 12 » -> « 12-Titre.jpg ») d'apres le dossier de la page : generation, --zones-only, doublons, noms sans fichier, noms intacts.
Prerequis : python build.py avant. Variable facultative : THREE_DIR. Lancer : python tests/image_noms_gen.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import json, os, pathlib, struct, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_noms_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def sol_glb(path):
    v = [(-20, 0, -20), (20, 0, -20), (20, 0, 20), (-20, 0, 20)]
    pos = b"".join(struct.pack("<3f", *p) for p in v)
    idx = struct.pack("<6H", 0, 1, 2, 0, 2, 3)
    blob = pos + idx + bytes(-(len(pos) + 12) % 4)
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos)}, {"buffer": 0, "byteOffset": len(pos), "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-20, 0, -20], "max": [20, 0, 20]}, {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}], "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * (-len(js) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def zone(i, cible):
    return {"id": i, "type": "image", "label": i, "x": 0, "y": 2, "z": 0, "yaw": 0, "shape": "ring", "trigger": "click", "radius": 2, "w": 1.2, "h": 0, "target": cible, "spawn": "", "confirm": False, "private": False, "showName": False}


def gen(*args):
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), *args, *vend], capture_output=True, text=True, cwd=str(tmp))
    return r.returncode, r.stdout + r.stderr


def cibles(zfile):
    return [z["target"] for z in json.loads(zfile.read_text(encoding="utf-8"))]


site = tmp / "site"; site.mkdir()
sol_glb(site / "sol.glb")
for n in ("12-Cezanne - Apples and Oranges.jpg", "1-aaa.webp", "1-Soleil.png", "120-autre.png", "7.PNG", "notes.txt"):
    (site / n).write_bytes(b"x")
(site / "sous").mkdir(); (site / "sous" / "9.jpg").write_bytes(b"x")
liste = ["12", "1", "120", "7", "99", "x.jpg", "sous/9", "http://h/12", "12"]
zj = tmp / "z.json"; zj.write_text(json.dumps([zone(f"z{i}", c) for i, c in enumerate(liste, 1)]), encoding="utf-8")
att = ["12-Cezanne - Apples and Oranges.jpg", "1-aaa.webp", "120-autre.png", "7.PNG", "99", "x.jpg", "sous/9", "http://h/12", "12-Cezanne - Apples and Oranges.jpg"]

code, sortie = gen(str(site / "sol.glb"), "-o", str(site / "p.html"), "--modular", "--no-sea", "--zones", str(zj))
rapport(code == 0, "generation modulaire", sortie[-300:])
res = cibles(site / "p.zones.json")
rapport(res == att, "zones modulaires : « 12 » complete, « 1 » = premier par ordre alphabetique sans tenir compte de la casse (1-aaa avant 1-Soleil), « 120 » distinct, « 7 » -> 7.PNG, introuvable et chemin, extension, adresse intacts", res)
rapport("[image]" in sortie and "12-Cezanne - Apples and Oranges.jpg" in sortie, "le generateur annonce le nom complete", sortie[-400:])
rapport("« 99 »" in sortie and "tel quel" in sortie, "le generateur signale « 99 » sans fichier", sortie[-400:])
rapport("2 fichiers" in sortie or "2 files" in sortie, "le generateur signale les doublons (« 1 »)", sortie[-400:])

zj2 = tmp / "z2.json"; zj2.write_text(json.dumps([zone("a", "12"), zone("b", "7")]), encoding="utf-8")
(site / "p.zones.json").write_text("[]", encoding="utf-8")
code, sortie = gen("-o", str(site / "p.html"), "--zones-only", "--zones", str(zj2))
rapport(code == 0 and cibles(site / "p.zones.json") == ["12-Cezanne - Apples and Oranges.jpg", "7.PNG"], "--zones-only complete aussi les noms", (code, sortie[-300:]))

print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
sys.exit(1 if echecs else 0)
