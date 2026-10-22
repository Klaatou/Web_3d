#!/usr/bin/env python3
"""Tests de tools/glb2tiles.py sur des GLB synthétiques fabriqués ici (aucun gros fichier, aucun navigateur).

  - GLB léger : --analyse répond « pas de découpage nécessaire », rien n'est écrit (même sans --analyse)
  - plusieurs meshes qui partagent un accessor : le compactage réduit le poids, les triangles restent identiques
  - objet racine de 80 m, léger (50 enfants dont un prim géant) : reste entier dans une seule tuile
  - objet racine de 600 m, 1 000 enfants, plus lourd que --entier-poids : réparti, ancêtres recopiés à l'identique
  - mesh unique plus lourd que le budget : avertissement, pas d'erreur
  - mesh réutilisé dans deux tuiles : dupliqué dans chacune
  - objet avec skin : jamais réparti (joint hors de l'objet recopié, inverseBindMatrices recopiées)
  - instance à 3 km du reste : pas d'erreur, signalée par --analyse
  - relecture de chaque tuile : JSON valide, chunks alignés, min/max exacts, somme des triangles = GLB d'origine,
    poids et triangles identiques à ceux du plan
  - GLB compressé Draco refusé avec un message clair, rien d'écrit
  - compteur d'octets lus : la lecture se fait par morceaux ; --version (source et dist/)
Lancer : python tests/glb2tiles.py   (GLB2TILES_GARDER=1 garde les fichiers produits)
"""
import contextlib, io, json, math, os, pathlib, shutil, struct, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "glb2tiles.py"
sys.path.insert(0, str(ROOT / "tools"))
import glb2tiles as T  # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2tiles_"))
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


# ---------- fabrication de GLB ----------
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
FMT = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}


class B:
    def __init__(self):
        self.bin = bytearray()
        self.j = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": []}], "nodes": [], "meshes": [],
                  "accessors": [], "bufferViews": []}

    def vue(self, data, target=None, stride=None):
        while len(self.bin) % 4:
            self.bin.append(0)
        v = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": len(data)}
        if target:
            v["target"] = target
        if stride:
            v["byteStride"] = stride
        self.bin += data
        self.j["bufferViews"].append(v)
        return len(self.j["bufferViews"]) - 1

    def acc(self, v, comp, count, typ, off=0, mn=None, mx=None, norm=False):
        a = {"bufferView": v, "componentType": comp, "count": count, "type": typ}
        if off:
            a["byteOffset"] = off
        if mn is not None:
            a["min"], a["max"] = mn, mx
        if norm:
            a["normalized"] = True
        self.j["accessors"].append(a)
        return len(self.j["accessors"]) - 1

    def positions(self, verts):
        d = b"".join(struct.pack("<3f", *v) for v in verts)
        mn = [min(v[k] for v in verts) for k in range(3)]
        mx = [max(v[k] for v in verts) for k in range(3)]
        return self.acc(self.vue(d, 34962), 5126, len(verts), "VEC3", mn=mn, mx=mx)

    def indices(self, idx, comp=5123, off_vertex=0):
        d = struct.pack("<%d%s" % (len(idx), FMT[comp]), *[i + off_vertex for i in idx])
        return self.acc(self.vue(d, 34963), comp, len(idx), "SCALAR")

    def normales(self, n):
        return self.acc(self.vue(struct.pack("<3f", 0, 1, 0) * n, 34962), 5126, n, "VEC3")

    def uv(self, n):
        return self.acc(self.vue(b"".join(struct.pack("<2f", (i % 10) / 10, (i // 10) / 10) for i in range(n)), 34962), 5126, n, "VEC2")

    def couleurs(self, n):
        """COLOR_0 VEC3 octets normalisés, rangées de 4 octets (valide : élément aligné sur 4)."""
        d = b"".join(bytes([i % 251, (i * 3) % 251, (i * 7) % 251, 0]) for i in range(n))
        return self.acc(self.vue(d, 34962, stride=4), 5121, n, "VEC3", norm=True)

    def mesh(self, pos, idx=None, nor=None, col=None, mat=None, nom=None, extra=None):
        pr = {"attributes": {"POSITION": pos}}
        if nor is not None:
            pr["attributes"]["NORMAL"] = nor
        if col is not None:
            pr["attributes"]["COLOR_0"] = col
        if extra:
            pr["attributes"].update(extra)
        if idx is not None:
            pr["indices"] = idx
        if mat is not None:
            pr["material"] = mat
        m = {"primitives": [pr]}
        if nom:
            m["name"] = nom
        self.j["meshes"].append(m)
        return len(self.j["meshes"]) - 1

    def noeud(self, nom, mesh=None, t=None, s=None, enfants=None, racine=False, skin=None):
        n = {"name": nom}
        if mesh is not None:
            n["mesh"] = mesh
        if skin is not None:
            n["skin"] = skin
        if t:
            n["translation"] = list(t)
        if s:
            n["scale"] = list(s)
        if enfants:
            n["children"] = enfants
        self.j["nodes"].append(n)
        k = len(self.j["nodes"]) - 1
        if racine:
            self.j["scenes"][0]["nodes"].append(k)
        return k

    def ecrire(self, chemin, ext=None):
        j = dict(self.j)
        for k in ("meshes", "accessors", "bufferViews", "nodes"):
            if not j[k]:
                del j[k]
        if ext:
            j["extensionsUsed"] = ext
        j["buffers"] = [{"byteLength": len(self.bin) + (-len(self.bin) % 4)}]
        jb = json.dumps(j).encode()
        jb += b" " * (-len(jb) % 4)
        bn = bytes(self.bin) + bytes(-len(self.bin) % 4)
        with open(chemin, "wb") as f:
            f.write(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(jb) + 8 + len(bn)))
            f.write(struct.pack("<II", len(jb), 0x4E4F534A) + jb + struct.pack("<II", len(bn), 0x004E4942) + bn)


def grille(n, taille=1.0, ox=0.0, oy=0.0, oz=0.0):
    verts = [(ox + taille * i / n, oy, oz + taille * j / n) for j in range(n + 1) for i in range(n + 1)]
    idx = []
    for j in range(n):
        for i in range(n):
            a = j * (n + 1) + i
            idx += [a, a + 1, a + n + 1, a + 1, a + n + 2, a + n + 1]
    return verts, idx


def mesh_grille(b, n, taille=1.0, **kw):
    v, i = grille(n, taille, **{k: kw.pop(k) for k in ("ox", "oy", "oz") if k in kw})
    return b.mesh(b.positions(v), b.indices(i), **kw)


# PNG 1x1 valide (le validateur glTF l'ouvre ; glb2tiles ne le décode jamais)
def _png():
    import zlib

    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(b"\x00\xff\x00\x00")) + ch(b"IEND", b"")


PNG = _png()


# ---------- relecture indépendante ----------
def lire(chemin):
    d = pathlib.Path(chemin).read_bytes()
    magic, ver, ln = struct.unpack_from("<4sII", d, 0)
    ok = magic == b"glTF" and ver == 2 and ln == len(d)
    off, ch = 12, []
    while off < len(d):
        n, t = struct.unpack_from("<II", d, off)
        ch.append((t, n, d[off + 8:off + 8 + n]))
        off += 8 + n
    ok = ok and off == len(d) and all(n % 4 == 0 for _, n, _ in ch) and ch[0][0] == 0x4E4F534A
    return json.loads(ch[0][2]), (ch[1][2] if len(ch) > 1 else b""), ok, ch


def lignes(j, b, i):
    a = j["accessors"][i]
    bv = j["bufferViews"][a["bufferView"]]
    nc = NC[a["type"]]
    f = FMT[a["componentType"]]
    es = nc * struct.calcsize("<" + f)
    stride = bv.get("byteStride", es)
    base = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    return [struct.unpack_from("<" + f * nc, b, base + k * stride) for k in range(a["count"])]


def triangles(j, b, n):
    out = []
    for pr in j["meshes"][n["mesh"]]["primitives"]:
        at = {k: lignes(j, b, v) for k, v in pr["attributes"].items()}
        idx = [r[0] for r in lignes(j, b, pr["indices"])] if "indices" in pr else list(range(len(at["POSITION"])))
        noms = sorted(at)
        for t in range(0, len(idx) - 2, 3):
            out.append(tuple(tuple(at[k][idx[t + q]] for k in noms) for q in range(3)))
    return sorted(out)


def noeuds_mesh(j, b):
    return {n["name"]: triangles(j, b, n) for n in j.get("nodes", []) if "mesh" in n}


def tout(args, chemin):
    """Lance main() dans le processus ; renvoie (code ou exception, texte)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            r = T.main([str(chemin)] + args + ["--nopause"])
        except T.ErreurGlb as e:
            r = e
    return r, buf.getvalue()


def verifier(nom, chemin, args):
    """Découpe puis contrôle toutes les invariantes ; renvoie (doc, dossier, tuiles lues)."""
    chemin = pathlib.Path(chemin)
    r, texte = tout(args, chemin)
    rapport(r == 0, f"{nom} : découpage sans erreur", (r, texte[-400:]))
    doc = json.loads((chemin.parent / (chemin.stem + ".tiles.json")).read_text(encoding="utf-8"))
    dossier = chemin.parent
    # origine
    j0, b0, ok0, _ = lire(chemin)
    orig = noeuds_mesh(j0, b0)
    tri0 = sum(len(v) for v in orig.values())
    # tuiles
    vu, tri_somme, ok_tout, mm_ok, geo_ok, fichier_ok = {}, 0, True, True, True, True
    lus = []
    for f in doc["tiles"]:
        j, b, ok, ch = lire(dossier / f["file"])
        ok_tout &= ok and f["bytes"] == (dossier / f["file"]).stat().st_size
        lus.append((f, j, b))
        for nm, tr in noeuds_mesh(j, b).items():
            vu.setdefault(nm, []).append(tr)
            tri_somme += len(tr)
        for a in j.get("accessors", []):
            if "min" in a:
                rows = lignes(j, b, j["accessors"].index(a))
                for k in range(len(a["min"])):
                    mm_ok &= min(r[k] for r in rows) == a["min"][k] and max(r[k] for r in rows) == a["max"][k]
        geo_ok &= f["geometryBytes"] + f["imageBytes"] == len(b)
        fichier_ok &= all(v["byteOffset"] % 4 == 0 and v["byteOffset"] + v["byteLength"] <= len(b) for v in j.get("bufferViews", []))
        fichier_ok &= f["min"][0] <= f["max"][0] and j["asset"]["version"] == "2.0"
    rapport(ok_tout, f"{nom} : en-tête, chunks alignés sur 4 octets, taille du fichier = tiles.json")
    rapport(mm_ok, f"{nom} : min/max des accessors exacts")
    rapport(geo_ok and fichier_ok, f"{nom} : vues alignées, octets de géométrie + d'images = tampon")
    rapport(tri_somme == tri0 == sum(f["triangles"] for f in doc["tiles"]), f"{nom} : somme des triangles des tuiles = GLB d'origine ({tri0})", (tri_somme, tri0))
    memes = all(nm in vu and all(t == orig[nm] for t in vu[nm]) for nm in orig)
    rapport(memes and set(vu) == set(orig), f"{nom} : mêmes triangles (positions et attributs) pour chaque instance")
    # le plan (poids, triangles) est celui qui a été écrit
    glb = T.Glb(chemin)
    try:
        P = T.Params(*[float(args[args.index(k) + 1]) if k in args else d for k, d in (
            ("--budget", 32.0), ("--budget-tri", 1500000), ("--min", 16.0), ("--entier-poids", 16.0), ("--entier-etendue", 256.0))])
        plan = T.Plan(glb, P)
        tuiles = plan.decouper()
        st = plan.stats_tuiles(tuiles)
    finally:
        glb.fermer()
    egal = len(tuiles) == len(doc["tiles"]) and all(
        f["geometryBytes"] == s[0] and f["imageBytes"] == s[1] and f["triangles"] == s[2] for f, s in zip(doc["tiles"], st))
    rapport(egal, f"{nom} : poids et triangles écrits = poids et triangles du plan", [(f["geometryBytes"], s) for f, s in zip(doc["tiles"], st)][:3])
    return doc, dossier, lus


# ---------- 1. GLB léger ----------
print("--- GLB léger")
d = tmp / "leger"
d.mkdir()
b = B()
m = mesh_grille(b, 4, nor=None)
for k in range(3):
    b.noeud(f"n{k}", m, t=(k * 5, 0, 0), racine=True)
b.ecrire(d / "leger.glb")
r, txt = tout(["--analyse"], d / "leger.glb")
rapport(r == 0 and "pas de découpage nécessaire" in txt, "--analyse : « pas de découpage nécessaire »", txt[-300:])
rapport(sorted(os.listdir(d)) == ["leger.glb"], "--analyse n'écrit rien", os.listdir(d))
r, txt = tout([], d / "leger.glb")
rapport(r == 0 and "pas de découpage nécessaire" in txt and sorted(os.listdir(d)) == ["leger.glb"], "sans --analyse : même réponse, rien d'écrit", (r, os.listdir(d)))

# ---------- 2. accessor partagé : le compactage réduit le poids ----------
print("--- accessor partagé")
d = tmp / "partage"
d.mkdir()
b = B()
tout_v, tout_i, parts = [], [], []
for q in range(4):
    v, i = grille(10, 4.0, ox=q * 10.0)
    parts.append((len(tout_v), i))
    tout_v += v
pos = b.positions(tout_v)
nor = b.normales(len(tout_v))
col = b.couleurs(len(tout_v))
b.j["materials"] = [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}]
b.j["textures"] = [{"source": 0, "sampler": 0}]
b.j["samplers"] = [{"magFilter": 9729}]
b.j["images"] = [{"bufferView": b.vue(PNG), "mimeType": "image/png"}]
uv = b.uv(len(tout_v))
mA = b.mesh(pos, b.indices(parts[0][1], off_vertex=parts[0][0]), nor=nor, col=col, mat=0, nom="A", extra={"TEXCOORD_0": uv})
mB = b.mesh(pos, b.indices(parts[1][1], off_vertex=parts[1][0]), nor=nor, col=col, mat=0, nom="B", extra={"TEXCOORD_0": uv})   # parts 2 et 3 : jamais utilisées
for k in range(5):
    b.noeud(f"a{k}", mA, t=(k * 300, 0, 0), racine=True)
    b.noeud(f"b{k}", mB, t=(k * 300, 0, 40), racine=True)
b.ecrire(d / "partage.glb")
glb = T.Glb(d / "partage.glb")
plan = T.Plan(glb, T.Params())
S = T.stats()
acc_brut = S.modele(glb.g)["geo_total"]
compact = sum(plan.cb[k] for k in plan.prims)
glb.fermer()
rapport(compact < 0.6 * acc_brut, "le compactage réduit le poids (sommets utilisés seulement)", (compact, acc_brut))
doc, dos, lus = verifier("partage", d / "partage.glb", ["--forcer", "--budget", "0.004", "--min", "16"])
rapport(len(doc["tiles"]) >= 3, "partage : plusieurs tuiles", len(doc["tiles"]))
fa = next(f for f, jj, _ in lus if any(n["name"] == "a0" for n in jj["nodes"]))
rapport(abs(fa["min"][0]) < 1e-6 and abs(fa["max"][0] - 4.0) < 1e-6 and abs(fa["max"][2] - 4.0) < 1e-6,
        "partage : boîte de la tuile = sommets réellement utilisés (pas la boîte de l'accessor partagé)", (fa["min"], fa["max"]))
j, bb = lus[0][1], lus[0][2]
rapport("images" in j and "textures" in j and "samplers" in j and j["images"][0]["mimeType"] == "image/png" and
        bb[j["bufferViews"][j["images"][0]["bufferView"]]["byteOffset"]:][:len(PNG)] == PNG, "partage : matériau, texture, sampler et image recopiés")
cols = [a for a in j["accessors"] if a["componentType"] == 5121]
rapport(cols and all(j["bufferViews"][a["bufferView"]].get("byteStride") == 4 and a.get("normalized") for a in cols), "partage : COLOR_0 (3 octets normalisés, alignés sur 4) conservé")

# ---------- 3. objet racine de 80 m léger : reste entier ----------
print("--- objet racine de 80 m")
d = tmp / "r80"
d.mkdir()
b = B()
m = mesh_grille(b, 2, 2.0)
enf = [b.noeud(f"c80_{k}", m, t=((k % 10) * 8.0, 0, (k // 10) * 8.0)) for k in range(49)]
enf.append(b.noeud("c80_geant", m, s=(35, 1, 35), t=(0, 0, 0)))     # un prim géant dans un linkset léger
b.noeud("R80", None, t=(100, 0, 100), enfants=enf, racine=True)
for k in range(30):
    b.noeud(f"autre{k}", m, t=(k * 60.0 - 500, 0, (k % 5) * 90.0), racine=True)
b.ecrire(d / "r80.glb")
doc, dos, lus = verifier("r80", d / "r80.glb", ["--forcer", "--budget", "0.0001", "--min", "16"])
tuiles_r80 = {f["file"] for f, j, _ in lus if any(n["name"].startswith("c80_") for n in j["nodes"])}
rapport(len(tuiles_r80) == 1 and doc["roots"]["whole"] >= 31 and len(doc["tiles"]) > 3, "R80 : les 50 enfants dans une seule tuile (objet gardé entier)", (tuiles_r80, doc["roots"], len(doc["tiles"])))
nb = [sum(1 for n in j["nodes"] if n["name"].startswith("c80_")) for f, j, _ in lus]
rapport(max(nb) == 50, "R80 : 50 enfants, dont le prim géant", nb)

# ---------- 4. objet racine de 600 m, 1000 enfants : réparti ----------
print("--- objet racine de 600 m")
d = tmp / "r600"
d.mkdir()
b = B()
enf = []
for k in range(1000):
    x0 = k * 0.6
    p = b.positions([(x0, 0, 0), (x0 + 0.5, 0, 0), (x0, 0, 0.5), (x0 + 0.5, 0, 0.5)])
    mk = b.mesh(p, b.indices([0, 1, 2, 1, 3, 2]), nom=f"q{k}")
    enf.append(b.noeud(f"c600_{k}", mk, t=(0, 0, (k % 7) * 5.0)))
rr = b.noeud("R600", None, t=(10, 0, 20), s=(1, 1, 1), enfants=enf, racine=True)
b.j["nodes"][rr]["rotation"] = [0, 0, 0, 1]
b.ecrire(d / "r600.glb")
doc, dos, lus = verifier("r600", d / "r600.glb", ["--forcer", "--budget", "0.005", "--entier-poids", "0.03", "--min", "16"])
avec = [(f, j) for f, j, _ in lus if any(n["name"].startswith("c600_") for n in j["nodes"])]
rapport(len(avec) > 2 and doc["roots"]["split"] == 1, "R600 : réparti entre plusieurs tuiles", (len(avec), doc["roots"]))
ok = all(any(n["name"] == "R600" and n.get("translation") == [10, 0, 20] and n.get("rotation") == [0, 0, 0, 1] and "mesh" not in n
             for n in j["nodes"]) for f, j in avec)
rapport(ok, "R600 : le nœud racine (sans mesh) est recopié à l'identique dans chaque tuile")
rapport(sum(sum(1 for n in j["nodes"] if n["name"].startswith("c600_")) for f, j in avec) == 1000, "R600 : les 1 000 enfants présents une seule fois")

# ---------- 5. mesh unique plus lourd que le budget ----------
print("--- mesh unique hors budget")
d = tmp / "gros"
d.mkdir()
b = B()
mg = mesh_grille(b, 60, 200.0, nom="Terrain")
ms = mesh_grille(b, 2, 2.0)
b.noeud("Terrain", mg, t=(0, 0, 0), racine=True)
for k in range(6):
    b.noeud(f"p{k}", ms, t=(k * 40.0, 3, 50), racine=True)
b.ecrire(d / "gros.glb")
doc, dos, lus = verifier("gros", d / "gros.glb", ["--forcer", "--budget", "0.02", "--min", "16"])
rapport(any("hors budget" in w and "Terrain" in w for w in doc["warnings"]), "avertissement « hors budget » avec le nom du mesh", doc["warnings"])

# ---------- 6. mesh réutilisé dans deux tuiles ----------
print("--- mesh réutilisé")
d = tmp / "reuse"
d.mkdir()
b = B()
mm = mesh_grille(b, 8, 3.0, nom="Reuse")
mo_ = mesh_grille(b, 3, 3.0, nom="Autre")
b.noeud("m_gauche", mm, t=(0, 0, 0), racine=True)
b.noeud("m_droite", mm, t=(900, 0, 0), racine=True)
b.noeud("o", mo_, t=(450, 0, 0), racine=True)
b.ecrire(d / "reuse.glb")
doc, dos, lus = verifier("reuse", d / "reuse.glb", ["--forcer", "--budget", "0.001", "--min", "16"])
avec = [f for f, j, _ in lus if any(m.get("name") == "Reuse" for m in j.get("meshes", []))]
rapport(len(avec) == 2 and doc["duplication"] > 1.0, "le mesh partagé est dupliqué dans chaque tuile qui l'utilise", (len(avec), doc["duplication"]))

# ---------- 7. objet avec skin ----------
print("--- objet avec skin")
d = tmp / "skin"
d.mkdir()
b = B()
v, i = grille(6, 4.0)
pos = b.positions(v)
jo = b.acc(b.vue(bytes([0, 1, 0, 0]) * len(v), 34962), 5121, len(v), "VEC4")
we = b.acc(b.vue(struct.pack("<4f", 0.5, 0.5, 0, 0) * len(v), 34962), 5126, len(v), "VEC4")
ibm = b.acc(b.vue(struct.pack("<32f", *([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1] * 2))), 5126, 2, "MAT4")
msk = b.mesh(pos, b.indices(i), extra={"JOINTS_0": jo, "WEIGHTS_0": we}, nom="Peau")
mp = mesh_grille(b, 2, 2.0)
jA = b.noeud("jointA", None, t=(0, 1, 0))
jOut = b.noeud("Jout", None, t=(50, 0, 50), racine=True)             # joint hors de l'objet
b.j["skins"] = [{"joints": [jA, jOut], "inverseBindMatrices": ibm, "name": "squelette"}]
sk = b.noeud("peau", msk, skin=0)
loin = b.noeud("loin", mp, t=(400, 0, 0))                            # enfant très éloigné du même objet
b.noeud("Rskin", None, t=(0, 0, 0), enfants=[jA, sk, loin], racine=True)
for k in range(8):
    b.noeud(f"x{k}", mp, t=(k * 200.0 - 700, 0, 300), racine=True)
b.ecrire(d / "skin.glb")
doc, dos, lus = verifier("skin", d / "skin.glb", ["--forcer", "--budget", "0.001", "--entier-poids", "0.0001", "--entier-etendue", "10", "--min", "16"])
ts = [(f, j, bb) for f, j, bb in lus if any(n["name"] == "Rskin" for n in j["nodes"])]
j = ts[0][1]
noms = {n["name"] for n in j["nodes"]}
rapport(len(ts) == 1 and {"peau", "loin", "jointA", "Jout"} <= noms, "skin : l'objet reste entier dans une seule tuile (joint extérieur compris)", (len(ts), noms))
sk0 = j["skins"][0]
rapport([j["nodes"][k]["name"] for k in sk0["joints"]] == ["jointA", "Jout"] and sk0["inverseBindMatrices"] is not None and
        j["accessors"][sk0["inverseBindMatrices"]]["count"] == 2 and "mesh" not in next(n for n in j["nodes"] if n["name"] == "Jout"),
        "skin : joints, inverseBindMatrices recopiés ; le joint extérieur est sans mesh", sk0)
rapport(sum(1 for f, jj, _ in lus if any(n["name"] == "peau" for n in jj["nodes"])) == 1 and doc["roots"]["whole"] >= 1, "skin : jamais réparti")

# ---------- 8. instance à 3 km ----------
print("--- valeur aberrante")
d = tmp / "loin"
d.mkdir()
b = B()
m = mesh_grille(b, 3, 2.0)
for k in range(20):
    b.noeud(f"proche{k}", m, t=(k * 10.0, 0, (k % 4) * 10.0), racine=True)
b.noeud("Lointain", m, t=(3000, 0, 20), racine=True)
b.ecrire(d / "loin.glb")
r, txt = tout(["--analyse", "--seuil", "0"], d / "loin.glb")
rapport(r == 0 and "aberrante" in txt and "Lointain" in txt and "découper" in txt, "--analyse : l'instance à 3 km est signalée sans erreur", txt[-500:])
doc, dos, lus = verifier("loin", d / "loin.glb", ["--forcer", "--budget", "0.001", "--min", "16"])
rapport(any("aberrante" in w for w in doc["warnings"]) and doc["extent"]["max"][0] >= 3000, "tiles.json : avertissement et étendue globale")

# ---------- 9. GLB compressé ----------
print("--- GLB compressé")
d = tmp / "draco"
d.mkdir()
b = B()
m = mesh_grille(b, 2)
b.noeud("n", m, racine=True)
b.ecrire(d / "draco.glb", ext=["KHR_draco_mesh_compression"])
r, txt = tout(["--forcer"], d / "draco.glb")
rapport(isinstance(r, T.ErreurGlb) and "compressé" in str(r) and "KHR_draco_mesh_compression" in str(r) and os.listdir(d) == ["draco.glb"], "Draco refusé avec un message clair, rien d'écrit", (r, os.listdir(d)))

# ---------- 10. lecture par morceaux ----------
print("--- lecture par morceaux")
d = tmp / "morceaux"
d.mkdir()
b = B()
b.j["images"] = [{"bufferView": b.vue(bytes(600000)), "mimeType": "image/png"}]
b.j["textures"] = [{"source": 0}]
b.j["materials"] = [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}]
m = mesh_grille(b, 150, 50.0, mat=0)
b.noeud("grand", m, racine=True)
b.ecrire(d / "morceaux.glb")
ancien = T.BLOC_LECTURE
T.BLOC_LECTURE = 4096
try:
    glb = T.Glb(d / "morceaux.glb")
    plan = T.Plan(glb, T.Params())
    taille, lus_o, gr, nb = glb.taille, glb.octets_lus, glb.plus_grande_lecture, glb.nb_lectures
    glb.fermer()
finally:
    T.BLOC_LECTURE = ancien
rapport(gr <= 4096 and nb > 50, "chaque lecture ≤ 4096 octets, en nombreux morceaux", (gr, nb))
rapport(lus_o < taille - 500000, "l'image (600 000 octets) et les positions ne sont pas lues pendant l'analyse", (lus_o, taille))
rapport(plan.insts[0].tri == 150 * 150 * 2, "triangles comptés par lecture des indices", plan.insts[0].tri)

# ---------- 10 bis. --exclure : boîtes de livraison d'un catalogue ----------
print("--- --exclure")
d = tmp / "exclure"
d.mkdir()
b = B()
CUBE_V = [(x, y, z) for x in (0, 1) for y in (0, 1) for z in (0, 1)]
CUBE_I = [0, 1, 3, 0, 3, 2, 4, 6, 7, 4, 7, 5, 0, 4, 5, 0, 5, 1, 2, 3, 7, 2, 7, 6, 0, 2, 6, 0, 6, 4, 1, 5, 7, 1, 7, 3]
# tampon de sommets partagé : le cube n'en utilise que 8 mais la boîte de l'accessor s'étend sur 80 m (boîte gonflée)
pos_part = b.positions(CUBE_V + [(80.0, 40.0, 80.0), (-40.0, 0.0, -40.0)])
cube_part = b.mesh(pos_part, b.indices(CUBE_I))
v4, i4 = grille(4, 2.0)
m30 = b.mesh(b.positions(v4), b.indices(i4[:90]))             # 30 triangles


def cube_propre():
    return b.mesh(b.positions(CUBE_V), b.indices(CUBE_I))


b.noeud("Box A - RAKis Freebies 2019", cube_part, t=(5, 0, 5), racine=True)
b.noeud("City Stores - Box - RAKis Freebies 2019", cube_propre(), t=(20, 0, 5), racine=True)
b.noeud("Box trente triangles - RAKis Freebies", m30, t=(30, 0, 5), racine=True)
b.noeud("Autre Box - FOURNISSEUR Gratuit", cube_propre(), t=(40, 0, 5), racine=True)
b.noeud("Maison simple", cube_propre(), t=(50, 0, 5), racine=True)
cm = cube_propre()
enf = [b.noeud(f"piece{k}", cm, t=(k % 12, 0, k // 12)) for k in range(143)]
b.noeud("Jewel Box House V17 with Stairs - RAKis Freebies 2", None, t=(60, 0, 20), enfants=enf, racine=True)
b.ecrire(d / "exclure.glb")
j0, b0, _, _ = lire(d / "exclure.glb")
tri_orig = 12 * 3 + 30 + 12 + 12 * 143       # Box A, City Stores, Autre Box ; trente ; Maison ; bâtiment


def noms_tuiles(chemin, extra):
    """Découpe et renvoie (nombre de triangles écrits, noms de racines présents, texte)."""
    r, txt = tout(["--forcer", *extra], chemin)
    doc = json.loads((chemin.parent / (chemin.stem + ".tiles.json")).read_text(encoding="utf-8"))
    tri, noms = 0, set()
    for f in doc["tiles"]:
        j, bb, _, _ = lire(chemin.parent / f["file"])
        tri += sum(len(v) for v in noeuds_mesh(j, bb).values())
        noms |= {n["name"] for n in j["nodes"]}
    return r, tri, noms, txt, doc


r, tri, noms, txt, doc = noms_tuiles(d / "exclure.glb", ["--exclure", "freebies"])
rapport(r == 0 and "City Stores - Box - RAKis Freebies 2019" not in noms and "Box A - RAKis Freebies 2019" not in noms, "objet de 12 triangles au nom du fournisseur : exclu (insensible à la casse)", (r, sorted(noms)[:4]))
rapport("Jewel Box House V17 with Stairs - RAKis Freebies 2" in noms and "piece142" in noms, "bâtiment du même fournisseur à 143 meshes : conservé avec tous ses descendants")
rapport("Box trente triangles - RAKis Freebies" in noms, "objet de même nom avec 30 triangles : conservé (garde-fou --exclure-max-tri)")
rapport({"Maison simple", "Autre Box - FOURNISSEUR Gratuit"} <= noms, "les autres objets ne changent pas")
rapport(tri == tri_orig - 24, "somme des triangles des tuiles = GLB d'origine moins les exclus", (tri, tri_orig - 24))
rapport(doc["excluded"]["count"] == 2 and doc["excluded"]["triangles"] == 24 and doc["excluded"]["bytesSaved"] > 0 and "excluded" in doc, "tiles.json : décompte, triangles et octets gagnés", doc.get("excluded"))
rapport("Objets exclus (--exclure" in txt and ": 2 |" in txt and "RAKis Freebies 2019" in txt and "2 objet(s) au nom correspondant conservé(s)" in txt, "rapport final : décompte, noms, garde-fous", txt[-700:])
# le poids des exclus n'entre pas dans les calculs : tuiles et poids du plan
glb = T.Glb(d / "exclure.glb")
try:
    pl_sans = T.Plan(glb, T.Params())
    pl_avec = T.Plan(glb, T.Params(exclure=["freebies"]))
    ok_p = len(pl_avec.racines) == len(pl_sans.racines) - 2 and sum(i.tri for i in pl_avec.insts) == sum(i.tri for i in pl_sans.insts) - 24
    ok_o = pl_avec.octets_exclus > 0 and len(pl_avec.exclus) == 2 and pl_sans.exclus == []
finally:
    glb.fermer()
rapport(ok_p and ok_o, "plan : racines, instances et triangles sans les exclus ; octets gagnés calculés", (len(pl_avec.racines), pl_avec.octets_exclus))
# garde-fous réglables
r, tri, noms, txt, doc = noms_tuiles(d / "exclure.glb", ["--exclure", "freebies", "--exclure-max-tri", "30"])
rapport("Box trente triangles - RAKis Freebies" not in noms and doc["excluded"]["count"] == 3, "--exclure-max-tri 30 : l'objet de 30 triangles est exclu", doc["excluded"])
# deux --exclure cumulent
r, tri, noms, txt, doc = noms_tuiles(d / "exclure.glb", ["--exclure", "freebies", "--exclure", "fournisseur"])
rapport(doc["excluded"]["count"] == 3 and "Autre Box - FOURNISSEUR Gratuit" not in noms and "Maison simple" in noms and tri == tri_orig - 36, "deux --exclure cumulent leurs effets", doc["excluded"])
# expression invalide
r, txt = tout(["--analyse", "--exclure", "(freebies"], d / "exclure.glb")
rapport(isinstance(r, T.ErreurGlb) and "Expression régulière invalide" in str(r) and "(freebies" in str(r), "expression invalide : message clair", r)
# --analyse : décompte des exclus
r, txt = tout(["--analyse", "--exclure", "freebies", "--exclure", "fournisseur"], d / "exclure.glb")
rapport(r == 0 and "Objets exclus (--exclure" in txt and "3 | triangles retirés : 36" in txt and "octets gagnés" in txt and "1 x « City Stores - Box - RAKis Freebies 2019 »" in txt, "--analyse : nombre d'exclus, récapitulatif par nom, octets gagnés", txt[-900:])
r, txt = tout(["--analyse"], d / "exclure.glb")
rapport(r == 0 and "Objets exclus" not in txt, "sans --exclure : aucune ligne d'exclusion")

# ---------- 10 ter. pause : pas de console ----------
print("--- sans console")
copie_p = tmp / "copie_pause"
copie_p.mkdir()
shutil.copy(TOOL, copie_p / "glb2tiles.py")
shutil.copy(ROOT / "tools" / "glb-stats.py", copie_p / "glb-stats.py")
r = subprocess.run([sys.executable, str(copie_p / "glb2tiles.py"), str(tmp / "leger" / "leger.glb"), "--analyse"], capture_output=True, text=True, cwd=tmp, timeout=60, stdin=subprocess.DEVNULL)
rapport(r.returncode == 0 and "EOFError" not in r.stderr + r.stdout and "Traceback" not in r.stderr, "sans console (stdin fermé) et sans --nopause : pas d'EOFError, code 0", (r.returncode, r.stderr[-300:]))
r = subprocess.run([sys.executable, str(copie_p / "glb2tiles.py"), str(tmp / "leger" / "leger.glb"), "--analyse", "--nopause"], capture_output=True, text=True, cwd=tmp, timeout=60, stdin=subprocess.DEVNULL)
rapport(r.returncode == 0 and "Traceback" not in r.stderr, "--nopause accepté", (r.returncode, r.stderr[-300:]))

# ---------- 11. version, journal, dist ----------
print("--- version")
v = subprocess.run([sys.executable, str(TOOL), "--version"], capture_output=True, text=True, cwd=tmp, timeout=30)
rapport(v.returncode == 0 and v.stdout.strip() == "glb2tiles __VERSION__" and not v.stderr, "--version (source) : affiche la version et rend la main, sans pause", (v.returncode, v.stdout, v.stderr))
vfile = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
dist = ROOT / "dist" / "glb2tiles.py"
if dist.is_file():
    txt = dist.read_text(encoding="utf-8")
    v = subprocess.run([sys.executable, str(dist), "--version"], capture_output=True, text=True, cwd=tmp, timeout=30)
    rapport("__VERSION__" not in txt and v.returncode == 0 and v.stdout.strip() == "glb2tiles " + vfile, "--version (dist) : version du fichier VERSION", (v.returncode, v.stdout, vfile))
    rapport((ROOT / "dist" / "glb-stats.py").is_file(), "dist/ contient aussi glb-stats.py (fonctions communes)")
    copie = tmp / "copie_dist"
    copie.mkdir()
    shutil.copy(dist, copie / "glb2tiles.py")
    shutil.copy(ROOT / "dist" / "glb-stats.py", copie / "glb-stats.py")
    r = subprocess.run([sys.executable, str(copie / "glb2tiles.py"), str(tmp / "leger" / "leger.glb"), "--analyse", "--nopause"], capture_output=True, text=True, cwd=tmp, timeout=60)
    lignes_log = (copie / "glb2tiles.log").read_text(encoding="utf-8").splitlines()
    rapport(r.returncode == 0 and r.stdout.splitlines()[:1] == ["[glb2tiles] " + vfile] and lignes_log[:1] == ["[glb2tiles] " + vfile] and
            "pas de découpage nécessaire" in r.stdout, "le journal commence par la version (dist, lancé hors du dépôt)", (r.stdout[:200], lignes_log[:2], r.stderr[-300:]))
else:
    print("[--]    dist/glb2tiles.py absent : lancer python build.py")
copie = tmp / "copie_src"
copie.mkdir()
shutil.copy(TOOL, copie / "glb2tiles.py")
shutil.copy(ROOT / "tools" / "glb-stats.py", copie / "glb-stats.py")
r = subprocess.run([sys.executable, str(copie / "glb2tiles.py"), str(tmp / "leger" / "leger.glb"), "--analyse", "--nopause"], capture_output=True, text=True, cwd=tmp, timeout=60)
rapport(r.returncode == 0 and (copie / "glb2tiles.log").read_text(encoding="utf-8").splitlines()[:1] == ["[glb2tiles] __VERSION__"], "source : le journal est écrit à côté du script, version en première ligne", (r.stdout[:200], r.stderr[-300:]))
copie2 = tmp / "sans_stats"
copie2.mkdir()
shutil.copy(TOOL, copie2 / "glb2tiles.py")
r = subprocess.run([sys.executable, str(copie2 / "glb2tiles.py"), str(tmp / "leger" / "leger.glb"), "--analyse", "--nopause"], capture_output=True, text=True, cwd=tmp, timeout=60)
rapport(r.returncode != 0 and "glb-stats.py introuvable" in r.stdout, "sans glb-stats.py à côté : message clair", (r.returncode, r.stdout[-300:]))

if os.environ.get("GLB2TILES_GARDER"):      # garder les fichiers pour les ouvrir (ex. validateur glTF)
    print("fichiers gardés dans", tmp)
else:
    shutil.rmtree(tmp, ignore_errors=True)
print("\n" + ("Tous les tests passent." if not bad else f"{bad} test(s) en échec."))
sys.exit(1 if bad else 0)
