#!/usr/bin/env python3
"""oar2glb.py : lecture du .gltf de convoar et OAR abimé (lot 1.12.27).

convoar n'ecrit pas double la barre oblique inverse qui termine un nom ("name": "banc\\",) : le JSON est invalide. load_gltf repare ces lignes (une barre ajoutee) et
n'y touche pas si le fichier est valide ; les chemins a barres doublees au milieu d'un nom ("C:\\\\x") restent intacts ; un autre defaut JSON reste une erreur claire.
Un OAR abime (flux gzip invalide, fichier tronque, fichier vide) donne le message « OAR abime » (sortie propre), jamais une trace.
Lancer : python tests/gltf_barre_finale.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import io, pathlib, sys, tarfile, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import oar2glb as T  # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="gltf_barre_"))
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


def ecrire(nom, txt):
    p = tmp / nom
    p.write_text(txt, encoding="utf-8", newline="")
    return p


def noms(g):
    return [n["name"] for n in g["nodes"]]


BS = "\\"
cass = '{\n "nodes": [\n  {\n   "name": "' + BS + '",\n   "mesh": 0\n  },\n  {\n   "name": "Monk bankje rock bench' + BS + '",\n   "mesh": 1\n  },\n  {"name": "C:' + BS * 2 + 'x' + BS * 2 + '", "mesh": 2}\n ]\n}\n'
g = T.load_gltf(ecrire("cass.gltf", cass))
rapport(noms(g) == [BS, "Monk bankje rock bench" + BS, "C:" + BS + "x" + BS], "noms casses reparés (barre finale), chemin à barres doublées intact", noms(g))
rapport([n["mesh"] for n in g["nodes"]] == [0, 1, 2], "le reste des champs est lu")

g = T.load_gltf(ecrire("crlf.gltf", cass.replace("\n", "\r\n")))
rapport(noms(g)[:2] == [BS, "Monk bankje rock bench" + BS], "fins de ligne CRLF : réparé aussi", noms(g))

bon = '{"nodes": [{"name": "banc' + BS * 2 + '"}, {"name": "a\\"b"}, {"name": "x\\u00e9\\n"}]}'
g = T.load_gltf(ecrire("bon.gltf", bon))
rapport(noms(g) == ["banc" + BS, 'a"b', "x\u00e9\n"], "fichier valide : lu tel quel (barre doublée, guillemet, \\u, \\n)", noms(g))

g = T.load_gltf(ecrire("isole.gltf", '{"nodes": [{"name": "a' + BS + 'zb"}]}'))
rapport(noms(g) == ["a" + BS + "zb"], "barre isolée au milieu : doublée comme avant", noms(g))

try:
    T.load_gltf(ecrire("faux.gltf", '{"nodes": [ {"name": "x" '))
    rapport(False, "JSON réellement invalide : sortie en erreur")
except SystemExit as e:
    rapport("invalide" in str(e) and "ligne" in str(e), "JSON réellement invalide : erreur claire", e)

for nom, octets in (("zlib.oar", b"\x1f\x8b\x08\x00" + b"garbage" * 60), ("vide.oar", b""), ("texte.oar", b"ceci n'est pas une archive")):
    (tmp / nom).write_bytes(octets)
    try:
        T.oar_scan(str(tmp / nom))
        rapport(False, "OAR abîmé « " + nom + " » : sortie en erreur")
    except SystemExit as e:
        rapport("abîmé" in str(e) and nom in str(e) and "Traceback" not in str(e), "OAR abîmé « " + nom + " » : message clair", str(e)[:90])

buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as t:
    d = b"x" * 100000
    ti = tarfile.TarInfo("archive.xml"); ti.size = len(d); t.addfile(ti, io.BytesIO(d))
(tmp / "tronque.oar").write_bytes(buf.getvalue()[:len(buf.getvalue()) // 2])
try:
    T.oar_scan(str(tmp / "tronque.oar"))
    rapport(False, "OAR tronqué : sortie en erreur")
except SystemExit as e:
    rapport("abîmé" in str(e), "OAR tronqué : message clair", str(e)[:90])

print("\n" + ("TOUT BON" if not bad else "%d ECHEC(S)" % bad))
sys.exit(1 if bad else 0)
