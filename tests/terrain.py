#!/usr/bin/env python3
"""Tests du terrain complet de tools/oar2glb.py (OAR et GLB synthétiques fabriqués ici, aucun gros fichier, aucun .exe).

  - carte de hauteurs 512 x 512 sur une région de 512 m : 64 patches de 64 m « Terrain i,j », hauteurs égales à la carte
    en tous les sommets, bords partagés identiques (positions, normales, couleurs), normales de longueur 1 et conformes
    aux différences centrées, triangles tournés vers le haut, indices 16 bits, un seul matériau « terrain »
  - patch plus petit en bout de rangée quand n-1 n'est pas multiple du côté (--terrain-patch 100)
  - couleurs : eau, pente (roche), herbe et sable sec sont quatre couleurs différentes ; niveau d'eau lu dans settings/ ou 20 par défaut
  - chaîne convoar (faux convoar) : terrain incomplet remplacé, patches présents, objets conservés, patches non retirés par drop_far
  - région de 256 m ou terrain déjà complet : GLB identique octet pour octet à celui de --terrain non
  - --terrain-seul : tout le reste du GLB conservé (JSON et chunk binaire), ancien terrain absent de la scène, original intact,
    lecture par morceaux (compteur d'octets), sortie X-terrain.glb, aucune pause, jamais d'écrasement de l'original
  - glb2tiles.py sur le résultat avec un petit budget : chaque patch dans une tuile, aucun mesh coupé
  - OAR sans carte de hauteurs : message clair, aucune erreur
Lancer : python tests/terrain.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"   # outils Python en français (v36)
import hashlib, io, json, math, pathlib, shutil, struct, subprocess, sys, tarfile, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent

def copie_i18n(dossier):
    """les sources des outils (tools/, src/) cherchent i18n_py.py et i18n/ à côté ou dans src/ : on les copie avec la copie du script"""
    shutil.copy(ROOT / "src" / "i18n_py.py", pathlib.Path(dossier) / "i18n_py.py")
    shutil.copytree(ROOT / "src" / "i18n", pathlib.Path(dossier) / "i18n", dirs_exist_ok=True)

TOOL = ROOT / "tools" / "oar2glb.py"
sys.path.insert(0, str(ROOT / "tools"))
import oar2glb as T  # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="terrain_"))
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


# ---------- fabrication ----------
def hauteur(x, y):
    if x < 100:
        return 10.0                                  # sous l'eau (niveau 20)
    if x < 130:
        return 10.0 + (x - 100) * 1.5                # rampe de 56 degrés : roche
    if y >= 400:
        return 20.5                                  # plateau 0,5 m au-dessus de l'eau : sable sec
    return 55.0 + 0.002 * (y % 7)                    # plaine presque plate : herbe


def carte(n, f=hauteur):
    return [f(x, y) for y in range(n) for x in range(n)]


def make_oar(chemin, n, taille, eau=None, avec_carte=True, f=hauteur):
    with tarfile.open(chemin, "w:gz") as t:
        def add(nom, data):
            ti = tarfile.TarInfo(nom)
            ti.size = len(data)
            t.addfile(ti, io.BytesIO(data))
        add("archive.xml", f"<archive><region_info><size_in_meters>{taille},{taille}</size_in_meters></region_info></archive>".encode())
        if eau is not None:
            add("settings/Test.xml", f"<RegionSettings><General/><Terrain><WaterHeight>{eau}</WaterHeight></Terrain></RegionSettings>".encode())
        if avec_carte:
            add("terrains/heightmap.r32", struct.pack(f"<{n * n}f", *carte(n, f)))


def glb_synthetique(chemin, couvre, remplissage=300_000):
    """GLB avec un nœud « Terrain » (couvre = (xmax, ymax) en mètres OpenSim, repère local tourné de -90° autour de X comme convoar),
    une « Maison » et un tampon de remplissage ; retourne les octets du chunk binaire d'origine."""
    blob, views, accs = bytearray(), [], []
    def vue(data, target=None):
        bv = {"buffer": 0, "byteOffset": len(blob), "byteLength": len(data)}
        if target:
            bv["target"] = target
        views.append(bv)
        blob.extend(data + b"\x00" * (-len(data) % 4))
        return len(views) - 1
    def quad(x0, y0, x1, y1, z):
        v = [(x0, y0, z), (x1, y0, z), (x0, y1, z), (x1, y1, z)]
        pa = vue(b"".join(struct.pack("<3f", *p) for p in v), 34962)
        ia = vue(struct.pack("<6H", 0, 1, 2, 1, 3, 2), 34963)
        accs.append({"bufferView": pa, "componentType": 5126, "count": 4, "type": "VEC3",
                     "min": [min(p[k] for p in v) for k in range(3)], "max": [max(p[k] for p in v) for k in range(3)]})
        accs.append({"bufferView": ia, "componentType": 5123, "count": 6, "type": "SCALAR"})
        return {"primitives": [{"attributes": {"POSITION": len(accs) - 2}, "indices": len(accs) - 1}]}
    m_ter = quad(-12.75, -10.0, couvre[0], couvre[1], 5.0)
    m_mai = quad(-1, -1, 1, 1, 0.0)
    vue(bytes((i * 7 + 3) & 255 for i in range(remplissage)))
    g = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0, 1]}],
         "nodes": [{"name": "Terrain", "mesh": 0, "rotation": [-0.7071068, 0, 0, 0.7071068]},
                   {"name": "Maison", "mesh": 1, "translation": [400, 30, -400]}],
         "meshes": [{"name": "Terrain", **m_ter}, {"name": "Maison", **m_mai}], "accessors": accs, "bufferViews": views,
         "buffers": [{"byteLength": len(blob)}]}
    ecrire_glb(chemin, g, bytes(blob))
    return bytes(blob)


def ecrire_glb(chemin, g, blob):
    js = T.pad4(json.dumps(g, separators=(",", ":")).encode(), b" ")
    with open(chemin, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)))
        f.write(struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\x00") + blob)


def lire_glb(chemin):
    d = pathlib.Path(chemin).read_bytes()
    ln = struct.unpack_from("<I", d, 12)[0]
    return json.loads(d[20:20 + ln]), d[20 + ln + 8:]


def acc(g, blob, ai):
    a = g["accessors"][ai]
    bv = g["bufferViews"][a["bufferView"]]
    nc = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[a["type"]]
    fmt = {5126: "f", 5123: "H", 5121: "B"}[a["componentType"]]
    flat = struct.unpack_from(f"<{a['count'] * nc}{fmt}", blob, bv["byteOffset"] + a.get("byteOffset", 0))
    return [flat[k * nc:(k + 1) * nc] for k in range(a["count"])]


def patches(g, blob):
    out = {}
    for sc in g["scenes"]:
        for i in sc["nodes"]:
            nd = g["nodes"][i]
            if nd.get("extras", {}).get("terrain"):
                pr = g["meshes"][nd["mesh"]]["primitives"][0]
                out[nd["name"]] = {"pos": acc(g, blob, pr["attributes"]["POSITION"]), "nor": acc(g, blob, pr["attributes"]["NORMAL"]),
                                   "col": acc(g, blob, pr["attributes"]["COLOR_0"]), "idx": acc(g, blob, pr["indices"]), "prim": pr, "node": nd}
    return out


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def lancer(*args, cwd=None):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, cwd=cwd or tmp, stdin=subprocess.DEVNULL, timeout=600)


# ---------- région de 512 m, carte 512 x 512 ----------
print("--- patches d'une région de 512 m")
N = 512
oar = tmp / "R512.oar"
make_oar(oar, N, 512, eau=None)
scan = T.oar_scan(oar, terrain_seul=True)
rapport(scan["water"] is None and T.terrain_eau(scan)[0] == 20.0 and "défaut" in T.terrain_eau(scan)[1], "sans settings/ : niveau d'eau 20 (défaut d'OpenSim), journalisé comme tel", T.terrain_eau(scan))
oar_eau = tmp / "R512eau.oar"
make_oar(oar_eau, 8, 7, eau=31.5)
s_eau = T.oar_scan(oar_eau, terrain_seul=True)
rapport(s_eau["water"] and s_eau["water"][0] == 31.5 and T.terrain_eau(s_eau)[0] == 31.5 and "settings/Test.xml" in T.terrain_eau(s_eau)[1], "WaterHeight lu dans settings/*.xml", s_eau["water"])
rapport(T.oar_scan(oar_eau)["water"] == s_eau["water"], "même niveau d'eau avec la lecture complète de l'OAR")

td = T.terrain_donnees(scan["terrain"], 20.0, 64)
rapport(len(td["nodes"]) == 64, "64 patches calculés")
g = {"asset": {"version": "2.0"}, "scenes": [{"nodes": []}], "nodes": [], "buffers": [{"byteLength": 0}]}
T.terrain_ajouter(g, td, 0, 0)
blob = bytes(td["blob"])
P = patches(g, blob)
# n-1 = 511 = 7 x 64 + 63 : 8 patches par rangée, le dernier de 63 m
rapport(len(P) == 64 and set(P) == {f"Terrain {i},{j}" for i in range(8) for j in range(8)}, "64 patches nommés « Terrain i,j »", sorted(P)[:3])
rapport(all(len(g["scenes"][0]["nodes"]) == 64 and "mesh" in g["nodes"][i] for i in g["scenes"][0]["nodes"]), "chaque patch est un objet racine de la scène")
h = scan["terrain"][1]
ok_h = ok_dim = True
dims = {}
for nom, p in P.items():
    i, j = map(int, nom.split()[1].split(","))
    for (x, v, z) in p["pos"]:
        ok_h &= v == h[int(-z) * N + int(x)] and x == int(x) and z == int(z)
    xs = sorted({q[0] for q in p["pos"]})
    zs = sorted({q[2] for q in p["pos"]})
    dims[nom] = (len(xs) - 1, len(zs) - 1)
    ok_dim &= xs[0] == i * 64 and zs[-1] == -j * 64 and p["prim"].get("mode", 4) == 4
rapport(ok_h, "hauteur de chaque sommet = carte de hauteurs (X = x, Z = -y)")
rapport(dims["Terrain 0,0"] == (64, 64) and dims["Terrain 7,7"] == (63, 63) and dims["Terrain 7,0"] == (63, 64) and ok_dim, "patches de 64 m, derniers de 63 m, origine de chaque patch", (dims["Terrain 7,7"], dims["Terrain 7,0"]))
rapport(sum(len(p["pos"]) for p in P.values()) == td["vertices"] == sum((a + 1) * (b + 1) for a, b in dims.values()), "somme des sommets cohérente", td["vertices"])
lens = [math.sqrt(sum(c * c for c in q)) for p in P.values() for q in p["nor"]]
rapport(max(abs(l - 1) for l in lens) < 1e-5, "normales de longueur 1", max(abs(l - 1) for l in lens))
# normale d'un sommet intérieur = différences centrées sur la carte
x, y = 115, 200
p = P["Terrain 1,3"]
k = next(k for k, q in enumerate(p["pos"]) if q[0] == x and q[2] == -y)
hx, hy = (h[y * N + x + 1] - h[y * N + x - 1]) / 2, (h[(y + 1) * N + x] - h[(y - 1) * N + x]) / 2
ln = math.sqrt(hx * hx + hy * hy + 1)
rapport(all(abs(a - b) < 1e-5 for a, b in zip(p["nor"][k], (-hx / ln, 1 / ln, hy / ln))), "normale = différences centrées sur toute la carte", (p["nor"][k], (-hx / ln, 1 / ln, hy / ln)))
# bords partagés : la colonne de droite de (i,j) = colonne de gauche de (i+1,j) ; ligne du bas de (i,j) = ligne du haut de (i,j+1)
def bord(p, axe, val):
    return sorted((q for q in range(len(p["pos"])) if p["pos"][q][axe] == val), key=lambda q: p["pos"][q][2 - axe])
ok_b = True
for i in range(7):
    for j in range(8):
        a, b = P[f"Terrain {i},{j}"], P[f"Terrain {i + 1},{j}"]
        ka, kb = bord(a, 0, (i + 1) * 64), bord(b, 0, (i + 1) * 64)
        ok_b &= len(ka) == len(kb) and all(a["pos"][u] == b["pos"][v] and a["nor"][u] == b["nor"][v] and a["col"][u] == b["col"][v] for u, v in zip(ka, kb))
for i in range(8):
    for j in range(7):
        a, b = P[f"Terrain {i},{j}"], P[f"Terrain {i},{j + 1}"]
        ka, kb = bord(a, 2, -(j + 1) * 64), bord(b, 2, -(j + 1) * 64)
        ok_b &= len(ka) == len(kb) and all(a["pos"][u] == b["pos"][v] and a["nor"][u] == b["nor"][v] and a["col"][u] == b["col"][v] for u, v in zip(ka, kb))
rapport(ok_b, "bords partagés identiques entre patches voisins (positions, normales, couleurs : aucune fissure, éclairage continu)")
# triangles vers le haut, indices valides, 16 bits
ok_t = True
for p in P.values():
    pos = p["pos"]
    for t in range(0, len(p["idx"]), 3 * 40):
        a, b, c = (pos[p["idx"][t + u][0]] for u in range(3))
        e1, e2 = [b[k] - a[k] for k in range(3)], [c[k] - a[k] for k in range(3)]
        ok_t &= e1[2] * e2[0] - e1[0] * e2[2] > 0          # composante Y du produit vectoriel : > 0 = face vers le haut
    ok_t &= max(q[0] for q in p["idx"]) < len(pos)
rapport(ok_t, "triangles tournés vers le haut, indices dans les bornes")
ac = g["accessors"]
rapport(all(a["componentType"] == 5123 for a in ac if a["type"] == "SCALAR") and all(a["componentType"] == 5121 and a.get("normalized") for a in ac if a["type"] == "VEC4"),
        "indices uint16, COLOR_0 en VEC4 octets normalisés")
rapport(len(g["materials"]) == 1 and g["materials"][0] == {"name": "terrain", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 1}, "doubleSided": False}
        and all("TEXCOORD_0" not in p["prim"]["attributes"] for p in P.values()), "un seul matériau « terrain » simple face, pas de coordonnées de texture")
mn = P["Terrain 2,2"]
rapport(all(a["min"][0] == 128 and a["max"][0] == 192 for a in [ac[g["meshes"][mn["node"]["mesh"]]["primitives"][0]["attributes"]["POSITION"]]]), "min/max de l'accesseur POSITION exacts")

# couleurs : eau, pente, herbe, sable sec
def couleur_en(x, y):
    for nom, p in P.items():
        for q, c in zip(p["pos"], p["col"]):
            if q[0] == x and q[2] == -y:
                return tuple(c[:3]), c[3]
coul = {"eau": couleur_en(50, 200), "roche": couleur_en(115, 200), "herbe": couleur_en(300, 200), "sable": couleur_en(300, 450)}
rapport(len({v[0] for v in coul.values()}) == 4 and all(v[1] == 255 for v in coul.values()), "quatre couleurs différentes (eau, pente, herbe, sable sec), alpha 255", coul)
r_, v_, b_ = coul["roche"][0]
rapport(abs(r_ - v_) < 10 and abs(v_ - b_) < 10, "la pente de plus de 35 degrés donne un gris (composantes proches)", coul["roche"])
r_, v_, b_ = coul["herbe"][0]
rapport(v_ > r_ and v_ > b_, "l'herbe est dominée par le vert", coul["herbe"])
r_, v_, b_ = coul["sable"][0]
rapport(r_ > v_ > b_ and r_ - b_ > 50, "le sable sec est dominé par le rouge puis le vert", coul["sable"])
h20 = T.couleur_terrain(25.0, 0.0, 20.0)
rapport(T.couleur_terrain(25.0, 0.0, 30.0) != h20 and T.couleur_terrain(25.0, 0.0, 24.0) != h20, "le niveau d'eau change la couleur d'un même point")
rapport(T.couleur_terrain(60, 34.0, 20) != T.couleur_terrain(60, 40.0, 20) and T.couleur_terrain(60, 40.0, 20) == T.couleur_terrain(60, 80.0, 20), "la roche s'impose entre 32 et 38 degrés")

# patch de 100 m : 511 = 5 x 100 + 11
td100 = T.terrain_donnees(scan["terrain"], 20.0, 100)
g100 = {"asset": {"version": "2.0"}, "scenes": [{"nodes": []}], "nodes": [], "buffers": [{"byteLength": 0}]}
T.terrain_ajouter(g100, td100, 0, 0)
P100 = patches(g100, bytes(td100["blob"]))
rapport(len(P100) == 36 and len({q[0] for q in P100["Terrain 5,0"]["pos"]}) == 12 and len({q[0] for q in P100["Terrain 0,0"]["pos"]}) == 101,
        "--terrain-patch 100 : 36 patches, dernier de 11 m", len(P100))
vp = subprocess.run([sys.executable, str(TOOL), str(oar), "--terrain-patch", "300", "--terrain-seul", str(tmp / "x.glb")], capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60)
rapport(vp.returncode != 0 and "--terrain-patch" in (vp.stdout + vp.stderr) and "Traceback" not in vp.stderr, "--terrain-patch hors bornes refusé avec un message")

# drop_far ne retire pas les patches, mais retire un objet ordinaire au même endroit
gg = {"nodes": [{"name": "Terrain 0,0", "translation": [5000, 0, 0], "extras": {"terrain": True}}, {"name": "Lointain", "translation": [5000, 0, 0]}], "scenes": [{"nodes": [0, 1]}]}
T.drop_far(gg, 600.0, (512.0, 512.0))
rapport(gg["scenes"][0]["nodes"] == [0], "drop_far épargne les patches de terrain et retire l'objet ordinaire", gg["scenes"][0]["nodes"])

# ---------- chaîne convoar (faux convoar) ----------
print("--- chaîne convoar")
FAKE = '''#!/usr/bin/env python3
import sys, shutil, pathlib
a = sys.argv[1:]
out = pathlib.Path(a[a.index("--outputdir") + 1]); out.mkdir(exist_ok=True)
for f in pathlib.Path(__file__).with_name("fake_out").iterdir():
    shutil.copy(f, out / f.name)
print("fake convoar")
'''


def gltf_convoar(d, couvre):
    d.mkdir()
    glb_synthetique(d / "x.glb", couvre, remplissage=64)
    g, blob = lire_glb(d / "x.glb")
    g["buffers"][0]["uri"] = "scene.bin"
    (d / "scene.bin").write_bytes(blob)
    (d / "scene.gltf").write_text(json.dumps(g))


def chaine(nom, n, taille, couvre, *extra, avec_carte=True):
    d = tmp / nom
    d.mkdir()
    make_oar(d / "R.oar", n, taille, avec_carte=avec_carte, f=(lambda x, y: 30.0 + 0.01 * x))
    (d / "convoar_fake.py").write_text(FAKE)
    (d / "convoar_fake.py").chmod(0o755)
    gltf_convoar(d / "fake_out", couvre)
    shutil.copy(TOOL, d / "oar2glb.py")
    copie_i18n(d)
    r = lancer(d / "oar2glb.py", d / "R.oar", "--convoar", d / "convoar_fake.py", "--nopause", *extra, cwd=d)
    return r, d / "R.glb"


r, sortie = chaine("c512", 512, 512, (257.0, 257.0))
rapport(r.returncode == 0 and sortie.is_file(), "région 512 m : la chaîne aboutit", r.stdout[-400:] + r.stderr[-300:])
if sortie.is_file():
    g2, b2 = lire_glb(sortie)
    noms = [g2["nodes"][i]["name"] for i in g2["scenes"][0]["nodes"]]
    rapport("Terrain" not in noms and "Maison" in noms and len([x for x in noms if x.startswith("Terrain ")]) == 64, "ancien « Terrain » retiré de la scène, objets conservés, 64 patches", noms[:4])
    rapport("[terrain] terrain de convoar incomplet" in r.stdout and "64 patch(es) de 64 m" in r.stdout and "niveau d'eau 20 m" in r.stdout and "carte 512 x 512" in r.stdout and "Mo ajoutés" in r.stdout and r.stdout.count("sommets") >= 1,
            "journal : couverture, patches, sommets, octets, niveau d'eau, taille de la carte, durée", [l for l in r.stdout.splitlines() if "[terrain]" in l])
    rapport(len(g2["buffers"]) == 1 and "uri" not in g2["buffers"][0] and g2["buffers"][0]["byteLength"] == len(b2), "un seul tampon dans le GLB empaqueté")
    pp = patches(g2, b2)
    rapport(len(pp) == 64 and all(v == 30.0 + 0.01 * x or abs(v - (30.0 + 0.01 * x)) < 1e-4 for q in [pp["Terrain 3,3"]] for (x, v, z) in q["pos"]), "hauteurs des patches lues dans le GLB final")

r0, s0 = chaine("c512non", 512, 512, (257.0, 257.0), "--terrain", "non")
rapport(r0.returncode == 0 and "[terrain] désactivé" in r0.stdout and not [n for n in lire_glb(s0)[0]["nodes"] if n["name"].startswith("Terrain ")], "--terrain non : rien ajouté")
r1, s1 = chaine("c512oui", 512, 512, (512.0, 512.0), "--terrain", "oui")
rapport(r1.returncode == 0 and len([n for n in lire_glb(s1)[0]["nodes"] if n["name"].startswith("Terrain ")]) == 64 and "forcé" in r1.stdout, "--terrain oui : patches même si le terrain de convoar est complet")
r2, s2 = chaine("c512complet", 512, 512, (512.0, 512.0))
rapport(r2.returncode == 0 and "terrain de convoar complet" in r2.stdout and sha(s2) == sha(chaine("c512complet2", 512, 512, (512.0, 512.0), "--terrain", "non")[1]), "terrain déjà complet : GLB identique à --terrain non (octet pour octet)")

# non-régression : région de 256 m
ra, sa = chaine("c256", 256, 256, (257.0, 257.0))
rb, sb = chaine("c256non", 256, 256, (257.0, 257.0), "--terrain", "non")
rapport(ra.returncode == 0 and "complet" in ra.stdout and sha(sa) == sha(sb), "région de 256 m : GLB identique à --terrain non (octet pour octet)", [l for l in ra.stdout.splitlines() if "[terrain]" in l])
gn = lire_glb(sa)[0]
rapport("Terrain" in [gn["nodes"][i]["name"] for i in gn["scenes"][0]["nodes"]], "région de 256 m : le terrain de convoar reste dans la scène")

# ---------- OAR sans carte de hauteurs ----------
print("--- OAR sans carte de hauteurs")
rs, ss = chaine("sans", 512, 512, (257.0, 257.0), avec_carte=False)
rapport(rs.returncode == 0 and "n'a pas de carte de hauteurs" in rs.stdout and "Traceback" not in rs.stderr + rs.stdout and ss.is_file()
        and not [n for n in lire_glb(ss)[0]["nodes"] if n["name"].startswith("Terrain ")], "chaîne convoar : message clair, aucune erreur, GLB sans patches", rs.stdout[-300:])
d_sans = tmp / "sans"
orig = tmp / "sans_orig.glb"
glb_synthetique(orig, (257.0, 257.0))
rs2 = lancer(d_sans / "oar2glb.py", d_sans / "R.oar", "--terrain-seul", orig)
rapport(rs2.returncode == 0 and "n'a pas de carte de hauteurs" in rs2.stdout and "Traceback" not in rs2.stderr and not (tmp / "sans_orig-terrain.glb").exists(), "--terrain-seul : message clair, code 0, aucun fichier écrit", rs2.stdout[-300:] + rs2.stderr[-300:])

# ---------- --terrain-seul ----------
print("--- --terrain-seul")
orig = tmp / "Gros.glb"
blob0 = glb_synthetique(orig, (257.0, 257.0), remplissage=400_000)
h0 = sha(orig)
copie = tmp / "copie_seul"
copie.mkdir()
shutil.copy(TOOL, copie / "oar2glb.py")
copie_i18n(copie)
rs = lancer(copie / "oar2glb.py", oar, "--terrain-seul", orig, cwd=copie)       # sans --nopause : aucune pause « Entrée »
out = tmp / "Gros-terrain.glb"
rapport(rs.returncode == 0 and out.is_file() and "Traceback" not in rs.stderr, "--terrain-seul : écrit Gros-terrain.glb, sans pause", rs.stdout[-400:] + rs.stderr[-300:])
rapport(sha(orig) == h0 and not list(tmp.glob("Gros*.part")), "l'original est intact, aucun fichier temporaire")
if out.is_file():
    go, bo = lire_glb(orig)
    gn, bn = lire_glb(out)
    rapport(bn[:len(blob0)] == blob0 and len(bn) % 4 == 0 and gn["buffers"][0]["byteLength"] == len(bn), "chunk binaire d'origine recopié à l'identique, patches ajoutés à la fin")
    scene = [gn["nodes"][i]["name"] for i in gn["scenes"][0]["nodes"]]
    rapport("Terrain" not in scene and "Maison" in scene and len([x for x in scene if x.startswith("Terrain ")]) == 64, "ancien terrain absent de la scène, maison conservée, 64 patches", scene[:3])
    ident = all(gn[k][:len(go[k])] == go[k] for k in ("meshes", "accessors", "bufferViews", "materials") if k in go) \
        and gn["nodes"][1] == go["nodes"][1] and {k: v for k, v in gn["nodes"][0].items()} == {k: v for k, v in go["nodes"][0].items() if k != "mesh"}
    rapport(ident, "meshes, accesseurs, vues et nœuds d'origine conservés (seul le mesh du nœud « Terrain » est détaché ; les nouveaux éléments sont ajoutés derrière)")
    rapport(all(gn[k] == go[k] for k in ("asset", "scene")), "reste du JSON identique")
    pn = patches(gn, bn)
    rapport(len(pn) == 64 and all(abs(v - hauteur(int(x), int(-z))) < 1e-4 for q in [pn["Terrain 1,1"], pn["Terrain 7,7"]] for (x, v, z) in q["pos"]), "hauteurs des patches lues dans le GLB final")
rapport("Mo ajoutés" in rs.stdout and "niveau d'eau 20 m" in rs.stdout and "64 patch(es)" in rs.stdout, "journal : patches, sommets, octets, eau, carte, durée", [l for l in rs.stdout.splitlines() if "[terrain]" in l])

# lecture par morceaux : compteur d'octets
out2 = tmp / "Gros-morceaux.glb"
m = T.terrain_seul(orig, scan, out2, "auto", 64, chunk=4096)
taille_json = struct.unpack_from("<I", orig.read_bytes(), 12)[0]
rapport(m is not None and m["lecture_max"] <= max(4096, taille_json) and m["lecture_max"] < len(blob0) // 10, "lecture par morceaux : plus grande lecture bien inférieure au chunk binaire", m)
rapport(m is not None and m["lu"] <= orig.stat().st_size + 64, "chaque octet du GLB lu au plus une fois", (m or {}).get("lu"))
rapport(sha(out2) == sha(out), "même résultat avec des morceaux de 4 Ko et de 8 Mo")

# jamais d'écrasement de l'original
re_ = lancer(copie / "oar2glb.py", oar, "--terrain-seul", orig, "--sortie", orig, cwd=copie)
rapport(re_.returncode != 0 and "jamais écrasé" in re_.stdout + re_.stderr and sha(orig) == h0, "--sortie = original : refusé, original intact")
rs3 = lancer(copie / "oar2glb.py", oar, "--terrain-seul", orig, "--sortie", tmp / "ailleurs.glb", cwd=copie)
rapport(rs3.returncode == 0 and (tmp / "ailleurs.glb").is_file() and sha(tmp / "ailleurs.glb") == sha(out), "--sortie : fichier choisi")
# relancé sur le résultat : pas de doublon
rs4 = lancer(copie / "oar2glb.py", oar, "--terrain-seul", out, "--sortie", tmp / "deux.glb", cwd=copie)
rapport(rs4.returncode == 0 and not (tmp / "deux.glb").exists() and "déjà dans ce GLB" in rs4.stdout, "GLB déjà muni de patches : inchangé, aucun fichier")
# terrain de convoar déjà complet : rien d'écrit
complet = tmp / "Complet.glb"
glb_synthetique(complet, (512.0, 512.0))
rs5 = lancer(copie / "oar2glb.py", oar, "--terrain-seul", complet, cwd=copie)
rapport(rs5.returncode == 0 and "complet" in rs5.stdout and not (tmp / "Complet-terrain.glb").exists(), "terrain de convoar complet : aucun fichier écrit")

# ---------- glb2tiles sur le résultat ----------
print("--- glb2tiles sur le résultat")
copie2 = tmp / "copie_tiles"
copie2.mkdir()
for f in ("glb2tiles.py", "glb-stats.py"):
    shutil.copy(ROOT / "tools" / f, copie2 / f)
copie_i18n(copie2)
rt = lancer(copie2 / "glb2tiles.py", out, "--budget", "0.4", "--forcer", "--nopause", cwd=copie2)
doc_p = tmp / "Gros-terrain.tiles.json"
rapport(rt.returncode == 0 and doc_p.is_file(), "glb2tiles s'exécute sur le GLB avec patches", rt.stdout[-500:] + rt.stderr[-300:])
if doc_p.is_file():
    doc = json.loads(doc_p.read_text(encoding="utf-8"))
    vus, tri, ok_nu = {}, 0, True
    for t in doc["tiles"]:
        gt, bt = lire_glb(tmp / t["file"])
        for sc in gt["scenes"]:
            for i in sc["nodes"]:
                nm = gt["nodes"][i].get("name", "")
                if nm.startswith("Terrain "):
                    vus[nm] = vus.get(nm, 0) + 1
                    pr = gt["meshes"][gt["nodes"][i]["mesh"]]["primitives"]
                    ok_nu &= len(pr) == 1
                    tri += gt["accessors"][pr[0]["indices"]]["count"] // 3
    attendu = sum(len(p["idx"]) // 3 for p in P.values())
    rapport(len(doc["tiles"]) > 1 and sorted(vus) == sorted(P) and set(vus.values()) == {1}, f"{len(doc['tiles'])} tuiles : chaque patch dans une seule tuile", {k: v for k, v in vus.items() if v != 1} or len(vus))
    rapport(ok_nu and tri == attendu, "aucun patch coupé : mêmes triangles qu'avant le découpage", (tri, attendu))

shutil.rmtree(tmp, ignore_errors=True) if "--garder" not in sys.argv else print("fichiers gardés dans", tmp)
print("\n" + ("TOUT PASSE" if not bad else f"{bad} ÉCHEC(S)"))
sys.exit(1 if bad else 0)
