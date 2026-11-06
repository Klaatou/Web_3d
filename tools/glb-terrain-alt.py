#!/usr/bin/env python3
"""glb-terrain-alt.py : altitudes réelles (repère du monde) des sommets du terrain dans un GLB ou
dans tous les GLB d'un dossier de tuiles. Le terrain = nœuds marqués extras.terrain par oar2glb.py,
sinon nœuds dont le nom contient « terrain ». Lecture seule.

  python glb-terrain-alt.py "P:\\...\\X.tiles"
  python glb-terrain-alt.py "P:\\...\\X.tiles" --mer 10
"""
import sys, json, struct, pathlib, math

def lire_glb(p):
    d = p.read_bytes()
    if d[:4] != b"glTF": raise ValueError("pas un GLB")
    off, js, binc = 12, None, b""
    while off < len(d):
        n, t = struct.unpack_from("<II", d, off)
        c = d[off + 8: off + 8 + n]
        if t == 0x4E4F534A: js = json.loads(c)
        elif t == 0x004E4942: binc = c
        off += 8 + n
    return js, binc

def mat_noeud(n):
    if "matrix" in n:
        m = n["matrix"]   # colonne par colonne
        return [[m[0], m[4], m[8], m[12]], [m[1], m[5], m[9], m[13]], [m[2], m[6], m[10], m[14]], [0, 0, 0, 1]]
    tx, ty, tz = n.get("translation", [0, 0, 0])
    x, y, z, w = n.get("rotation", [0, 0, 0, 1])
    sx, sy, sz = n.get("scale", [1, 1, 1])
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return [[r[0][0] * sx, r[0][1] * sy, r[0][2] * sz, tx], [r[1][0] * sx, r[1][1] * sy, r[1][2] * sz, ty],
            [r[2][0] * sx, r[2][1] * sy, r[2][2] * sz, tz], [0, 0, 0, 1]]

def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); return
    mer = None
    if "--mer" in args:
        k = args.index("--mer"); mer = float(args[k + 1]); del args[k:k + 2]
    cible = pathlib.Path(args[0])
    fichiers = sorted(cible.glob("*.glb")) if cible.is_dir() else [cible]
    tranches = {}            # tranche de 5 m -> nombre de sommets
    total, sous, nb_noeuds = 0, 0, 0
    ymin, ymax = math.inf, -math.inf
    for f in fichiers:
        js, binc = lire_glb(f)
        nodes = js.get("nodes", [])
        parent = {}
        for i, n in enumerate(nodes):
            for c in n.get("children", []): parent[c] = i
        def monde(i):
            m = mat_noeud(nodes[i])
            while i in parent:
                i = parent[i]; m = mul(mat_noeud(nodes[i]), m)
            return m
        acc, bvs = js.get("accessors", []), js.get("bufferViews", [])
        for i, n in enumerate(nodes):
            est = n.get("extras", {}).get("terrain") if isinstance(n.get("extras"), dict) else None
            if not est and "terrain" not in str(n.get("name", "")).lower(): continue
            if "mesh" not in n: continue
            nb_noeuds += 1
            m = monde(i)
            for pr in js["meshes"][n["mesh"]]["primitives"]:
                a = acc[pr["attributes"]["POSITION"]]
                bv = bvs[a["bufferView"]]
                o = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
                st = bv.get("byteStride", 12)
                for v in range(a["count"]):
                    x, y, z = struct.unpack_from("<3f", binc, o + v * st)
                    wy = m[1][0] * x + m[1][1] * y + m[1][2] * z + m[1][3]
                    total += 1
                    ymin, ymax = min(ymin, wy), max(ymax, wy)
                    t = math.floor(wy / 5) * 5
                    tranches[t] = tranches.get(t, 0) + 1
                    if mer is not None and wy < mer: sous += 1
    if not total:
        print("Aucun nœud de terrain trouvé."); return
    print(f"Fichiers : {len(fichiers)}  nœuds de terrain : {nb_noeuds}  sommets : {total}")
    print(f"Altitude du terrain : min {ymin:.2f} m  max {ymax:.2f} m")
    print("Répartition par tranche de 5 m :")
    for t in sorted(tranches):
        print(f"  {t:7.0f} à {t + 5:7.0f} m : {tranches[t]:9d}  ({100 * tranches[t] / total:5.1f} %)")
    if mer is not None:
        print(f"Sommets sous {mer:g} m : {sous} ({100 * sous / total:.1f} %)")

if __name__ == "__main__":
    main()
