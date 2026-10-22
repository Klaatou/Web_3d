"""Fabrication de GLB synthétiques pour les tests v31 (Python standard seulement).

B() : tampon, vues, accessors, meshes, nœuds ; ecrire(chemin) écrit un GLB valide.
Région d'essai : terrain en patches « Terrain i,j » (extras.terrain, COLOR_0), maisons texturées, petits objets, verre, objet à squelette.
"""
import json, math, struct, zlib

FMT = {5123: "H", 5125: "I", 5126: "f"}


class B:
    def __init__(self):
        self.bin = bytearray()
        self.j = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": []}], "nodes": [], "meshes": [], "accessors": [], "bufferViews": []}

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

    def acc(self, v, comp, count, typ, mn=None, mx=None, norm=False):
        a = {"bufferView": v, "componentType": comp, "count": count, "type": typ}
        if mn is not None:
            a["min"], a["max"] = mn, mx
        if norm:
            a["normalized"] = True
        self.j["accessors"].append(a)
        return len(self.j["accessors"]) - 1

    def mesh(self, verts, idx, mat=None, uv=False, colors=None, nom=None, skin=False):
        d = b"".join(struct.pack("<3f", *v) for v in verts)
        pos = self.acc(self.vue(d, 34962), 5126, len(verts), "VEC3", [min(v[k] for v in verts) for k in range(3)], [max(v[k] for v in verts) for k in range(3)])
        nor = self.acc(self.vue(struct.pack("<3f", 0, 1, 0) * len(verts), 34962), 5126, len(verts), "VEC3")
        ix = self.acc(self.vue(struct.pack("<%dH" % len(idx), *idx), 34963), 5123, len(idx), "SCALAR")
        at = {"POSITION": pos, "NORMAL": nor}
        if uv:
            at["TEXCOORD_0"] = self.acc(self.vue(b"".join(struct.pack("<2f", i % 2, (i // 2) % 2) for i in range(len(verts))), 34962), 5126, len(verts), "VEC2")
        if colors is not None:
            at["COLOR_0"] = self.acc(self.vue(b"".join(bytes(c) + b"\xff" for c in colors), 34962), 5121, len(verts), "VEC4", norm=True)
        if skin:
            at["JOINTS_0"] = self.acc(self.vue(b"\x00\x00\x00\x00" * len(verts), 34962), 5121, len(verts), "VEC4")
            at["WEIGHTS_0"] = self.acc(self.vue(struct.pack("<4f", 1, 0, 0, 0) * len(verts), 34962), 5126, len(verts), "VEC4")
        pr = {"attributes": at, "indices": ix}
        if mat is not None:
            pr["material"] = mat
        m = {"primitives": [pr]}
        if nom:
            m["name"] = nom
        self.j["meshes"].append(m)
        return len(self.j["meshes"]) - 1

    def noeud(self, nom, mesh=None, t=None, s=None, extras=None, enfants=None, racine=True, skin=None):
        n = {"name": nom}
        if mesh is not None:
            n["mesh"] = mesh
        if t:
            n["translation"] = list(t)
        if s:
            n["scale"] = list(s)
        if extras:
            n["extras"] = extras
        if enfants:
            n["children"] = enfants
        if skin is not None:
            n["skin"] = skin
        self.j["nodes"].append(n)
        k = len(self.j["nodes"]) - 1
        if racine:
            self.j["scenes"][0]["nodes"].append(k)
        return k

    def image(self, data, mime="image/png"):
        self.j.setdefault("images", []).append({"bufferView": self.vue(data), "mimeType": mime})
        return len(self.j["images"]) - 1

    def ecrire(self, chemin):
        j = dict(self.j)
        j["buffers"] = [{"byteLength": len(self.bin) + (-len(self.bin) % 4)}]
        jb = json.dumps(j).encode()
        jb += b" " * (-len(jb) % 4)
        bn = bytes(self.bin) + bytes(-len(self.bin) % 4)
        with open(chemin, "wb") as f:
            f.write(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(jb) + 8 + len(bn)))
            f.write(struct.pack("<II", len(jb), 0x4E4F534A) + jb + struct.pack("<II", len(bn), 0x004E4942) + bn)


def png(rgb=(255, 0, 0), cote=1):
    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    ligne = b"\x00" + bytes(rgb) * cote
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", cote, cote, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(ligne * cote)) + ch(b"IEND", b"")


CUBE_IDX = [0, 1, 3, 0, 3, 2, 4, 6, 7, 4, 7, 5, 0, 4, 5, 0, 5, 1, 2, 3, 7, 2, 7, 6, 0, 2, 6, 0, 6, 4, 1, 5, 7, 1, 7, 3]


def cube(cx, y, cz, lx, ly, lz):
    """Sommets d'une boîte posée en y (dessous), centrée en cx, cz."""
    return [(cx + dx * lx / 2, y + dy * ly, cz + dz * lz / 2) for dy in (0, 1) for dz in (-1, 1) for dx in (-1, 1)]


X0, Z0, PATCH, NP, NQ = 100.0, -300.0, 64.0, 6, 8      # coin, côté d'un patch (m), patches par côté, cases par côté de patch


def hauteur(x, z):
    return 12 + 3 * math.sin(x / 37) + 2 * math.cos(z / 53)


def couleur_sol(h):
    t = max(0.0, min(1.0, (h - 8) / 10))
    return (int(90 + 60 * t), int(150 - 30 * t), int(70 + 20 * t))


VILLAGE_X0, VILLAGE_Z, STATUE, BANCS = 130.0, 60.0, (300.0, 40.0), [(200.0, 20.0), (400.0, 20.0)]


def region(chemin, maisons=24, instances=40, petits=12, verre=True, squelette=True, images_cassees=False, village=False):
    """Terrain NP x NP patches ; `maisons` maisons rouges (texture PNG 1 pixel) ; un cube partagé par `instances` nœuds ; `petits` cubes de 0,5 m ;
    un cube de verre (BLEND) ; un objet à squelette ; images_cassees : deux matériaux qui pointent une image de 0 octet et une image tronquée."""
    b = B()
    b.j["materials"] = []
    for i in range(NP):
        for j in range(NP):
            v, idx, col = [], [], []
            for q in range(NQ + 1):
                for p in range(NQ + 1):
                    x, z = X0 + PATCH * i + PATCH * p / NQ, Z0 + PATCH * j + PATCH * q / NQ
                    v.append((x, hauteur(x, z), z))
                    col.append(couleur_sol(hauteur(x, z)))
            for q in range(NQ):
                for p in range(NQ):
                    a = q * (NQ + 1) + p
                    idx += [a, a + NQ + 1, a + 1, a + 1, a + NQ + 1, a + NQ + 2]      # dessus vers +Y : un clic (lancer de rayon, face avant seulement) touche le sol
            b.noeud(f"Terrain {i},{j}", b.mesh(v, idx, colors=col), extras={"terrain": True})
    b.j["images"] = []
    b.image(png((255, 0, 0)))
    b.j["samplers"] = [{}]
    b.j["textures"] = [{"source": 0, "sampler": 0}]
    b.j["materials"].append({"name": "brique", "doubleSided": True, "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}})        # 0 : texture rouge
    b.j["materials"].append({"name": "verre", "alphaMode": "BLEND", "pbrMetallicRoughness": {"baseColorFactor": [0.5, 0.8, 1, 0.3]}})      # 1
    b.j["materials"].append({"name": "bleu", "doubleSided": True, "pbrMetallicRoughness": {"baseColorFactor": [0.0, 0.0, 1.0, 1]}})      # 2 : couleur de base seule
    if images_cassees:
        vide = b.image(b"")
        tronque = b.image(png((0, 255, 0), cote=40)[:-30])
        b.j["textures"] += [{"source": vide, "sampler": 0}, {"source": tronque, "sampler": 0}]
        b.j["materials"].append({"name": "vide", "doubleSided": True, "pbrMetallicRoughness": {"baseColorTexture": {"index": 1}}})      # 3
        b.j["materials"].append({"name": "tronquee", "doubleSided": True, "pbrMetallicRoughness": {"baseColorTexture": {"index": 2}}})      # 4
    for k in range(maisons):
        cx, cz = X0 + 40 + (k % 6) * 60 + (k // 6) * 7, Z0 + 40 + (k // 6) * 80 + (k % 3) * 11
        mat = 0
        if images_cassees and k % 4 in (2, 3):
            mat = 3 + (k % 4 - 2)       # 3 (vide) ou 4 (tronquée)
        b.noeud(f"Maison {k}", b.mesh(cube(cx, hauteur(cx, cz), cz, 6, 4, 6), CUBE_IDX, mat=mat, uv=True, nom=f"maison{k}"))
    if instances:
        partage = b.mesh(cube(0, 0, 0, 8, 6, 8), CUBE_IDX, mat=2, nom="cube-partage")
        for k in range(instances):
            cx, cz = X0 + 20 + (k % 8) * 45, Z0 + 20 + (k // 8) * 70
            b.noeud(f"Partage {k}", partage, t=(cx, hauteur(cx, cz), cz))
    for k in range(petits):
        cx, cz = X0 + 30 + k * 25, Z0 + 15
        b.noeud(f"Petit {k}", b.mesh(cube(cx, hauteur(cx, cz), cz, 0.5, 0.5, 0.5), CUBE_IDX, mat=2))
    if verre:
        cx, cz = X0 + 200, Z0 + 200
        b.noeud("Verre", b.mesh(cube(cx, hauteur(cx, cz), cz, 5, 5, 5), CUBE_IDX, mat=1))
    if squelette:
        cx, cz = X0 + 150, Z0 + 150
        joint = b.noeud("os", None, t=(0, 0, 0), racine=False)
        corps = b.noeud("corps", b.mesh(cube(cx, hauteur(cx, cz), cz, 6, 6, 6), CUBE_IDX, mat=2, skin=True), racine=False, skin=0)
        b.j["skins"] = [{"joints": [joint]}]
        b.noeud("Animal", None, enfants=[joint, corps])
    if village:
        # v32 : objet « Village » (racine sans mesh, 8 huttes enfants réparties sur 315 m : réparti sur plusieurs tuiles avec --entier-etendue 50),
        # « Statue » (nom unique), deux « Banc » (même nom : références Banc#0 et Banc#1)
        huttes = []
        for k in range(8):
            cx, cz = VILLAGE_X0 + 45 * k, VILLAGE_Z
            huttes.append(b.noeud(f"Hutte {k}", b.mesh(cube(cx, hauteur(cx, cz), cz, 6, 4, 6), CUBE_IDX, mat=2), racine=False))
        b.noeud("Village", None, enfants=huttes)
        b.noeud("Statue", b.mesh(cube(STATUE[0], hauteur(*STATUE), STATUE[1], 2, 5, 2), CUBE_IDX, mat=2))
        for k, (bx, bz) in enumerate(BANCS):
            b.noeud("Banc", b.mesh(cube(bx, hauteur(bx, bz), bz, 3, 1, 1), CUBE_IDX, mat=2))
    b.ecrire(chemin)
    return b
