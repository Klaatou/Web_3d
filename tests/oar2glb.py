#!/usr/bin/env python3
"""Tests de tools/oar2glb.py sur un OAR synthétique et un faux convoar (aucun vrai OAR, aucun .exe).

  - cheval en 2 morceaux riggés (bind_shape différentes, même nom, même position) : déplacés ensemble ;
    boîte racine d'animesh non transparente dans l'OAR : retirée
  - hippopotame (animesh enfant d'une racine invisible, échelle de prim aberrante 30 m, échelle portée par le nœud GLB)
  - antilope (animesh, échelle de prim 0,05 m, échelle cuite dans les sommets du GLB)
  - racines invisibles (faces alpha 0 ; texture invisible standard), boîte vitrée alpha 0,5 conservée, rocher mesh sans skin
  - nœud GLB sans prim dans l'OAR mais matériau alpha 0
  - deux variantes de GLB : UUID dans les extras / noms seuls (correspondance par nom + position)
  - --keep-invisible, --diag (n'écrit rien), analyse du TextureEntry et du bloc skin
Lancer : python tests/oar2glb.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"   # outils Python en français (v36)
import base64, io, json, math, os, pathlib, struct, subprocess, sys, tarfile, tempfile, uuid, zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "oar2glb.py"
sys.path.insert(0, str(ROOT / "tools"))
import oar2glb as T  # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="oar2glb_"))
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


def U():
    return str(uuid.uuid4())


# ---------- fabrication des assets ----------
def llsd(v):
    if isinstance(v, dict):
        return b"{" + struct.pack(">I", len(v)) + b"".join(b"k" + struct.pack(">I", len(k)) + k.encode() + llsd(x) for k, x in v.items()) + b"}"
    if isinstance(v, list):
        return b"[" + struct.pack(">I", len(v)) + b"".join(llsd(x) for x in v) + b"]"
    if isinstance(v, bytes):
        return b"b" + struct.pack(">I", len(v)) + v
    if isinstance(v, bool):
        return b"1" if v else b"0"
    if isinstance(v, int):
        return b"i" + struct.pack(">i", v)
    if isinstance(v, float):
        return b"r" + struct.pack(">d", v)
    return b"s" + struct.pack(">I", len(v)) + v.encode()


def box_sub(lo=(-0.5, -0.5, -0.5), hi=(0.5, 0.5, 0.5)):
    # sous-maillage : boîte remplissant son domaine de position, avec normales et UV
    pts = [(x, y, z) for x in (0, 1) for y in (0, 1) for z in (0, 1)]
    pos = b"".join(struct.pack("<3H", *[65535 * c for c in p]) for p in pts)
    nor = b"".join(struct.pack("<3H", 32768, 32768, 65535) for _ in pts)
    uv = b"".join(struct.pack("<2H", 65535 * p[0], 65535 * p[1]) for p in pts)
    idx = [0, 1, 3, 0, 3, 2, 4, 6, 7, 4, 7, 5, 0, 4, 5, 0, 5, 1, 2, 3, 7, 2, 7, 6, 0, 2, 6, 0, 6, 4, 1, 5, 7, 1, 7, 3]
    return {"PositionDomain": {"Min": list(lo), "Max": list(hi)}, "Position": pos, "Normal": nor, "TexCoord0Domain": {"Min": [0.0, 0.0], "Max": [1.0, 1.0]},
            "TexCoord0": uv, "TriangleList": b"".join(struct.pack("<3H", *idx[i:i + 3]) for i in range(0, 36, 3))}


def llmesh(skin=None, geom=None):
    geo = zlib.compress(llsd(geom if geom is not None else [{"NoGeometry": True}]))
    blocks = {"high_lod": geo}
    if skin:
        blocks["skin"] = zlib.compress(llsd(skin))
    hdr, off = {}, 0
    for k, b in blocks.items():
        hdr[k] = {"offset": off, "size": len(b)}
        off += len(b)
    return b"<? LLSD/Binary ?>\n" + llsd(hdr) + b"".join(blocks.values())


def tex_entry(default_tex, default_alpha, faces=None):
    # faces : {n: (tex, alpha)} ; format OpenSim (couleur inversée)
    def u(s):
        return uuid.UUID(s).bytes
    out = u(default_tex)
    ov = faces or {}
    for f, (t, a) in ov.items():
        out += bytes([1 << f]) + u(t)
    out += b"\x00" + bytes([255, 255, 255, 255 - default_alpha])
    for f, (t, a) in ov.items():
        out += bytes([1 << f]) + bytes([255, 255, 255, 255 - a])
    out += b"\x00"
    return base64.b64encode(out).decode()


PLY = "5748decc-f629-461c-9a36-a35a221fe21f"
INVT = "8dcd4a48-2d37-4909-9f78-f7a9eb4ef903"     # « Transparent » du sélecteur de textures
GRAD = "e97cf410-8e61-7005-ec06-629eba4cd1fb"     # dégradé alpha : VISIBLE


def part_xml(pid, name, gpos, off, rot, scale, mesh=None, te=None):
    sh = "<Shape>" + (f"<SculptType>5</SculptType><SculptTexture><Guid>{mesh}</Guid></SculptTexture>" if mesh else "<SculptType>0</SculptType>")
    sh += (f"<TextureEntry>{te}</TextureEntry>" if te else "") + "</Shape>"
    v = lambda t, a, k="XYZ": f"<{t}>" + "".join(f"<{c}>{x}</{c}>" for c, x in zip(k, a)) + f"</{t}>"
    return (f"<SceneObjectPart><UUID><Guid>{pid}</Guid></UUID><Name>{name}</Name>{v('GroupPosition', gpos)}"
            f"{v('OffsetPosition', off)}{v('RotationOffset', rot, 'XYZW')}{v('Scale', scale)}{sh}</SceneObjectPart>")


def group_xml(parts):
    return ("<SceneObjectGroup><RootPart>" + parts[0] + "</RootPart><OtherParts>" + "".join(parts[1:]) + "</OtherParts></SceneObjectGroup>")


I4 = [0, 0, 0, 1]
HIPPO_MESH, ANTE_MESH, ROCK_MESH, HA_MESH, HB_MESH, COL_MESH, GIR_MESH = U(), U(), U(), U(), U(), U(), U()
ID = dict(gir=U(), colo=U(), croot=U(), ca=U(), cb=U(), hroot=U(), hippo=U(), aroot=U(), ante=U(), ghost2=U(), glass=U(), rock=U(), ghost1=U())
BSM_H = [3, 0, 0, 0, 0, 1.4, 0, 0, 0, 0, 1.6, 0, 0, 0, 0.8, 1]          # raw [-0.5,0.5]^3 -> 3 x 1.4 x 1.6, pieds à 0
BSM_A = [1.2, 0, 0, 0, 0, 0.5, 0, 0, 0, 0, 1.4, 0, 0, 0, 0.7, 1]
BSM_HA = [2, 0, 0, 0, 0, 0.6, 0, 0, 0, 0, 1, 0, 0, 0, 1.0, 1]            # x[-1,1] y[-.3,.3] z[.5,1.5]
BSM_HB = [0.4, 0, 0, 0, 0, 0.4, 0, 0, 0, 0, 1, 0, 0.8, 0, 0.5, 1]        # x[.6,1] y[-.2,.2] z[0,1]

GRP = [  # (fichier, parties)
    ("h", [(ID["hroot"], "BoiteHippo", [100, 120, 25], [0, 0, 0], [0, 0, 0.7071, 0.7071], [3, 3, 3], None, tex_entry(PLY, 0)),
           (ID["hippo"], "Hippo", [100, 120, 25], [0, 0, 0.5], I4, [30, 30, 30], HIPPO_MESH, None)]),
    ("a", [(ID["aroot"], "BoiteAntilope", [60, 40, 24], [0, 0, 0], I4, [2, 2, 2], None, tex_entry(INVT, 255)),
           (ID["ante"], "Antilope", [60, 40, 24], [0, 0, 0.3], [0, 0, 0.7071, 0.7071], [0.05, 0.05, 0.05], ANTE_MESH, None)]),
    ("g2", [(ID["ghost2"], "Fantome", [200, 200, 30], [0, 0, 0], I4, [1, 1, 1], None, tex_entry(PLY, 255, {1: (INVT, 255)}) and tex_entry(INVT, 255))]),
    ("c", [(ID["croot"], "BoiteCheval", [80, 80, 26], [0, 0, 0], I4, [2, 2, 2], None, tex_entry(PLY, 255)),
           (ID["ca"], "Cheval", [80, 80, 26], [0, 0, 0.1], I4, [1, 1, 1], HA_MESH, None),
           (ID["cb"], "Cheval", [80, 80, 26], [0.5, 0, 0.2], I4, [1, 1, 1], HB_MESH, None)]),
    ("gi", [(ID["gir"], "Girafe", [180, 180, 28], [0, 0, 0], I4, [1, 1, 1], GIR_MESH, None)]),
    ("k", [(ID["colo"], "Colosse", [150, 150, 30], [0, 0, 0], I4, [1, 1, 1], COL_MESH, None)]),
    ("v", [(ID["glass"], "Vitre", [30, 30, 22], [0, 0, 0], I4, [2, 2, 2], None, tex_entry(PLY, 128))]),
    ("r", [(ID["rock"], "Rocher", [150, 20, 22], [0, 0, 0], I4, [4, 4, 4], ROCK_MESH, None)]),
    ("g1", [(ID["ghost1"], "Fantome0", [220, 30, 30], [0, 0, 0], I4, [1, 1, 1], None, tex_entry(PLY, 0, {2: (PLY, 255)}) and tex_entry(PLY, 0))]),
]


def terrain():
    n = 256
    return struct.pack(f"<{n * n}f", *[20.0 + 0.01 * x for y in range(n) for x in range(n)])


def make_oar(path):
    with tarfile.open(path, "w:gz") as t:
        def add(name, data):
            ti = tarfile.TarInfo(name)
            ti.size = len(data)
            t.addfile(ti, io.BytesIO(data))
        add("archive.xml", b"<archive><region_info><size_in_meters>256,256</size_in_meters></region_info></archive>")
        for i, (f, parts) in enumerate(GRP):
            add(f"objects/{f}_{i}.xml", ('<?xml version="1.0" encoding="utf-8"?>' + group_xml([part_xml(*p) for p in parts])).encode())
        add(f"assets/{HIPPO_MESH}_mesh.llmesh", llmesh({"joint_names": ["mPelvis", "mTorso"], "bind_shape_matrix": [float(v) for v in BSM_H],
                                                      "inverse_bind_matrix": [[1.0] * 16], "pelvis_offset": 0.0}, [box_sub()]))
        add(f"assets/{ANTE_MESH}_mesh.llmesh", llmesh({"joint_names": ["mPelvis"], "bind_shape_matrix": [float(v) for v in BSM_A]}, [box_sub()]))
        add(f"assets/{HA_MESH}_mesh.llmesh", llmesh({"joint_names": ["mPelvis"], "bind_shape_matrix": [float(v) for v in BSM_HA]}, [box_sub()]))
        add(f"assets/{HB_MESH}_mesh.llmesh", llmesh({"joint_names": ["mPelvis"], "bind_shape_matrix": [float(v) for v in BSM_HB]}, [box_sub()]))
        add(f"assets/{GIR_MESH}_mesh.llmesh", llmesh({"joint_names": ["mPelvis"], "bind_shape_matrix": [1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1]},
                                                    [box_sub((-1.0, -0.4, 0.0), (1.0, 0.4, 2.4))]))     # mesh non normalisé, bind_shape neutre
        add(f"assets/{COL_MESH}_mesh.llmesh", llmesh({"joint_names": ["mPelvis"], "bind_shape_matrix": [50.0, 0, 0, 0, 0, 50.0, 0, 0, 0, 0, 50.0, 0, 0, 0, 0, 1]}, [box_sub()]))
        add(f"assets/{ROCK_MESH}_mesh.llmesh", llmesh())
        add("terrains/heightmap.r32", terrain())


# ---------- faux convoar : copie le glTF préparé ----------
FAKE = '''#!/usr/bin/env python3
import sys, shutil, pathlib
a = sys.argv[1:]
out = pathlib.Path(a[a.index("--outputdir") + 1]); out.mkdir(exist_ok=True)
for f in pathlib.Path(__file__).with_name("fake_out").iterdir():
    shutil.copy(f, out / f.name)
print("fake convoar")
'''


def box(lo, hi):
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    v = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    idx = [0, 1, 3, 0, 3, 2, 4, 6, 7, 4, 7, 5, 0, 4, 5, 0, 5, 1, 2, 3, 7, 2, 7, 6, 0, 2, 6, 0, 6, 4, 1, 5, 7, 1, 7, 3]
    n = []
    for (x, y, z) in v:
        l = math.sqrt(x * x + y * y + z * z) or 1
        n.append((x / l, y / l, z / l))
    return v, n, idx


def gos(p):          # OpenSim -> glTF
    return (p[0], p[2], -p[1])


def make_gltf(d, variant):
    d.mkdir()
    blob = bytearray()
    views, accs, meshes, nodes, mats = [], [], [], [], []

    def add(data, target, kind, count, mm=None, comp=5126):
        views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data), "target": target})
        blob.extend(data + b"\x00" * ((4 - len(data) % 4) % 4))
        a = {"bufferView": len(views) - 1, "componentType": comp, "count": count, "type": kind}
        if mm:
            a["min"], a["max"] = mm
        accs.append(a)
        return len(accs) - 1

    def mk_mesh(name, lo, hi, mat):
        v, n, idx = box(lo, hi)
        g = [gos(p) for p in v]
        gn = [gos(p) for p in n]
        pa = add(b"".join(struct.pack("<3f", *p) for p in g), 34962, "VEC3", len(g), ([min(p[k] for p in g) for k in range(3)], [max(p[k] for p in g) for k in range(3)]))
        na = add(b"".join(struct.pack("<3f", *p) for p in gn), 34962, "VEC3", len(gn))
        ia = add(struct.pack(f"<{len(idx)}H", *idx), 34963, "SCALAR", len(idx), comp=5123)
        meshes.append({"name": name, "primitives": [{"attributes": {"POSITION": pa, "NORMAL": na}, "indices": ia, "material": mat}]})
        return len(meshes) - 1

    def mat(name, alpha=1.0):
        mats.append({"name": name, "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, alpha]}, "alphaMode": "BLEND" if alpha < 1 else "OPAQUE"})
        return len(mats) - 1

    m_ok, m_half, m_zero = mat("opaque"), mat("verre", 0.5), mat("invisible", 0.0)
    r2 = [0, 0, 0.7071, 0.7071]

    def node(name, pos, mesh, pid=None, scale=None, rot=None, children=None):
        n = {"name": name, "translation": list(gos(pos)), "mesh": mesh}
        if scale:
            n["scale"] = [scale[0], scale[2], scale[1]]
        if rot:
            n["rotation"] = [rot[0], rot[2], -rot[1], rot[3]]
        if pid and variant == "uuid":
            n["extras"] = {"uuid": pid}
        if children:
            n["children"] = children
        nodes.append(n)
        return len(nodes) - 1

    # boîtes racines (invisibles in-world) : matériau convoar « opaque » avec alpha 0 pour la variante uuid,
    # texture invisible standard (nom d'image) pour l'autre
    box_h = mk_mesh("BoiteHippo", (-1.5, -1.5, -1.5), (1.5, 1.5, 1.5), m_zero)
    box_a = mk_mesh("BoiteAntilope", (-1, -1, -1), (1, 1, 1), m_zero)
    hip = mk_mesh("Hippo", (-35.0, -16.0, -38.0), (35.0, 16.0, 38.0), m_ok)       # géométrie fausse de convoar (étendue inventée)
    ant = mk_mesh("Antilope", (-0.5 * 3.7, -0.5 * 2.1, -0.5 * 5.3), (0.5 * 3.7, 0.5 * 2.1, 0.5 * 5.3), m_ok)   # échelle cuite inconnue de l'OAR (comme convoar sur Jungle_Isle)
    gl = mk_mesh("Vitre", (-1, -1, -1), (1, 1, 1), m_half)
    rk = mk_mesh("Rocher", (-2, -2, -2), (2, 2, 2), m_ok)
    orph = mk_mesh("Orphelin", (-1, -1, -1), (1, 1, 1), m_zero)
    c1 = node("Hippo", (0, 0, 0.5), hip, ID["hippo"], scale=(30, 30, 30))
    r1 = node("BoiteHippo", (100, 120, 25), box_h, ID["hroot"], rot=[0, 0, 0.7071, 0.7071], children=[c1])
    c2 = node("Antilope", (0, 0, 0.3), ant, ID["ante"], rot=[0, 0, 0.7071, 0.7071])
    r2n = node("BoiteAntilope", (60, 40, 24), box_a, ID["aroot"], children=[c2])
    bx_c = mk_mesh("BoiteCheval", (-1, -1, -1), (1, 1, 1), m_ok)      # boîte racine visible dans le GLB (alpha 1)
    ha = mk_mesh("Cheval", (-0.5, -0.5, -0.5), (0.5, 0.5, 0.5), m_ok)
    hb = mk_mesh("Cheval", (-0.5, -0.5, -0.5), (0.5, 0.5, 0.5), m_ok)
    cha = node("Cheval", (0, 0, 0.1), ha, ID["ca"])
    chb = node("Cheval", (0.5, 0, 0.2), hb, ID["cb"])
    rc = node("BoiteCheval", (80, 80, 26), bx_c, ID["croot"], children=[cha, chb])
    gir = mk_mesh("Girafe", (-7, -7, -7), (7, 7, 7), m_ok)         # géométrie fausse de convoar
    rgir = node("Girafe", (180, 180, 28), gir, ID["gir"])
    col = mk_mesh("Colosse", (-0.5, -0.5, -0.5), (0.5, 0.5, 0.5), m_ok)
    rcol = node("Colosse", (150, 150, 30), col, ID["colo"])
    r3 = node("Vitre", (30, 30, 22), gl, ID["glass"])
    r4 = node("Rocher", (150, 20, 22), rk, ID["rock"])
    r5 = node("Fantome", (200, 200, 30), orph, ID["ghost2"])
    r6 = node("Fantome0", (220, 30, 30), orph, ID["ghost1"])
    r7 = node("Orphelin", (10, 10, 25), orph)
    g = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [r1, r2n, rc, rgir, rcol, r3, r4, r5, r6, r7]}], "nodes": nodes, "meshes": meshes,
         "materials": mats, "accessors": accs, "bufferViews": views, "buffers": [{"byteLength": len(blob), "uri": "scene.bin"}]}
    (d / "scene.bin").write_bytes(bytes(blob))
    (d / "scene.gltf").write_text(json.dumps(g), encoding="utf-8")


def read_glb(path):
    d = pathlib.Path(path).read_bytes()
    ln = struct.unpack_from("<I", d, 12)[0]
    js = json.loads(d[20:20 + ln])
    off = 20 + ln + 8
    return js, d[off:]


def world_boxes_node(js, bin_, i):
    n, tree, pts = js["nodes"][i], T.Tree(js), []
    w = tree.world(i)
    for pr in js["meshes"][n["mesh"]]["primitives"]:
        a = js["accessors"][pr["attributes"]["POSITION"]]
        bv = js["bufferViews"][a["bufferView"]]
        for k in range(a["count"]):
            x, y, z = struct.unpack_from("<3f", bin_, bv["byteOffset"] + a.get("byteOffset", 0) + k * 12)
            pts.append([w[r] * x + w[4 + r] * y + w[8 + r] * z + w[12 + r] for r in range(3)])
    return [min(p[k] for p in pts) for k in range(3)], [max(p[k] for p in pts) for k in range(3)]


def world_boxes(js, bin_):
    # étendue monde (glTF) de chaque nœud avec mesh, en suivant parents/enfants
    tree = T.Tree(js)
    out = {}
    for i, n in enumerate(js["nodes"]):
        if "mesh" not in n:
            continue
        w = tree.world(i)
        pts = []
        for pr in js["meshes"][n["mesh"]]["primitives"]:
            a = js["accessors"][pr["attributes"]["POSITION"]]
            bv = js["bufferViews"][a["bufferView"]]
            for k in range(a["count"]):
                x, y, z = struct.unpack_from("<3f", bin_, bv["byteOffset"] + a.get("byteOffset", 0) + k * 12)
                pts.append([w[r] * x + w[4 + r] * y + w[8 + r] * z + w[12 + r] for r in range(3)])
        out[n.get("name", "").replace(" (retiré)", "")] = ([min(p[k] for p in pts) for k in range(3)], [max(p[k] for p in pts) for k in range(3)], i)
    return out


def run_tool(oar, *extra, fake):
    return subprocess.run([sys.executable, str(TOOL), str(oar), "--convoar", str(fake), "--nopause", *extra], capture_output=True, text=True, cwd=tmp)


# ---------- unités : TextureEntry, skin ----------
te = T.parse_texture_entry(tex_entry(PLY, 0))
rapport(T.part_invisible(te), "TextureEntry : toutes faces alpha 0 = invisible")
rapport(not T.part_invisible(T.parse_texture_entry(tex_entry(PLY, 0, {2: (PLY, 255)}))), "TextureEntry : une face visible = visible")
rapport(T.part_invisible(T.parse_texture_entry(tex_entry(INVT, 255))), "TextureEntry : texture invisible standard")
rapport(not T.part_invisible(T.parse_texture_entry(tex_entry(PLY, 128))), "TextureEntry : alpha 0,5 = visible")
rapport(not T.part_invisible(T.parse_texture_entry(tex_entry(GRAD, 255))), "TextureEntry : le dégradé alpha e97cf410 est VISIBLE")
sk, err = T.llmesh_skin(llmesh({"joint_names": ["a"], "bind_shape_matrix": [float(v) for v in BSM_H]}))
rapport(sk and T.bind_shape(sk) == [float(v) for v in BSM_H], "bloc skin : bind_shape_matrix lue", (sk, err))
rapport(T.llmesh_skin(llmesh())[0] is None, "mesh sans skin : None")

# ---------- bout en bout ----------
oar = tmp / "R.oar"
make_oar(oar)
fake = tmp / "convoar_fake.py"
fake.write_text(FAKE)
fake.chmod(0o755)
for variant in ("uuid", "nom"):
    print(f"--- variante GLB : {variant}")
    od = tmp / variant
    od.mkdir()
    o = od / "R.oar"
    o.write_bytes(oar.read_bytes())
    sub = od / "convoar_fake.py"
    sub.write_text(FAKE)
    sub.chmod(0o755)
    make_gltf(od / "fake_out", variant)
    # le faux convoar copie fake_out à côté de lui
    r = run_tool(o, fake=sub)
    log = r.stdout + r.stderr
    rapport(r.returncode == 0 and (od / "R.glb").exists(), "oar2glb : GLB produit", log[-800:])
    rapport("5 mesh(es) riggé(s) remis à l'échelle, 6 prim(s) invisible(s) retiré(s)" in log, "journal récapitulatif", [l for l in log.splitlines() if "correctif" in l])
    js, bin_ = read_glb(od / "R.glb")
    bx = world_boxes(js, bin_)
    names = {js["nodes"][v[2]]["name"] for v in bx.values()}
    rapport("Hippo" in bx and "Antilope" in bx, "animaux présents")
    for nm, dims, c in (("Hippo", (1.4, 1.6, 3.0), (100, -120)), ("Antilope", None, (60, -40))):
        lo, hi, _ = bx[nm]
        sz = [hi[k] - lo[k] for k in range(3)]
        # Antilope tournée de 90° : largeur et longueur permutées dans le monde
        exp = dims if nm == "Hippo" else (0.5, 1.4, 1.2)
        sx = (sz[0], sz[1], sz[2])
        rapport(all(abs(sx[k] - exp[k]) < 0.02 for k in range(3)), f"{nm} : taille réaliste {sx}", exp)
        rapport(abs((lo[0] + hi[0]) / 2 - c[0]) < 0.05 and abs((lo[2] + hi[2]) / 2 - c[1]) < 0.05, f"{nm} : centré sur la racine ({(lo[0] + hi[0]) / 2:.2f}, {(lo[2] + hi[2]) / 2:.2f})")
        gnd = 23.5 if nm == "Hippo" else 23.0           # dessous de la boîte racine (z - échelle/2), le terrain (21) est ignoré
        rapport(abs(lo[1] - gnd) < 0.02, f"{nm} : pieds au dessous de la boîte racine (pied à {lo[1]:.3f}, attendu {gnd})")
    ch = [n for n in js["nodes"] if n.get("name") == "Cheval"]
    chm = [world_boxes_node(js, bin_, js["nodes"].index(n)) for n in ch]
    ulo = [min(b[0][k] for b in chm) for k in range(3)]
    uhi = [max(b[1][k] for b in chm) for k in range(3)]
    rapport(len(ch) == 2 and abs(uhi[0] - ulo[0] - 2.0) < 0.02 and abs(uhi[1] - ulo[1] - 1.5) < 0.02,
            f"cheval en 2 morceaux : taille de l'ensemble {[round(uhi[k] - ulo[k], 3) for k in range(3)]}")
    rapport(abs((ulo[0] + uhi[0]) / 2 - 80) < 0.02 and abs(ulo[1] - 25.0) < 0.02, f"cheval : ensemble centré sur la racine, pieds à {ulo[1]:.3f} (attendu 25)")
    d = (chm[1][0][0] + chm[1][1][0]) / 2 - (chm[0][0][0] + chm[0][1][0]) / 2
    rapport(abs(d - 0.8) < 0.02, f"cheval : les morceaux gardent leur position relative ({d:.3f} m, attendu 0.8)")
    rapport(not any(js["nodes"][i].get("scale") for i in (v[2] for k, v in bx.items() if k in ("Hippo", "Antilope"))), "animaux : plus d'échelle de nœud")
    for gone in ("BoiteHippo", "BoiteAntilope", "BoiteCheval", "Fantome", "Fantome0", "Orphelin"):
        rapport(gone not in bx, f"{gone} retiré")
    lo, hi, gi_ = bx["Girafe"]
    rapport(abs(hi[0] - lo[0] - 2.0) < 0.01 and abs(hi[2] - lo[2] - 0.8) < 0.01 and abs(hi[1] - lo[1] - 2.4) < 0.01 and abs(lo[1] - 28.0) < 0.01,
            f"mesh non normalisé, racine riggée : taille du domaine, pieds à l'altitude de la racine ({[round(hi[k] - lo[k], 3) for k in range(3)]}, pied {lo[1]:.3f})")
    gp = js["meshes"][js["nodes"][gi_]["mesh"]]["primitives"][0]
    rapport("TEXCOORD_0" in gp["attributes"] and "NORMAL" in gp["attributes"] and js["accessors"][gp["indices"]]["count"] == 36,
            "mesh reconstruit : normales, UV et 12 triangles")
    lo, hi, _ = bx["Colosse"]
    rapport(abs(hi[0] - lo[0] - 1) < 1e-3 and "Colosse" in log and "implausible" in log, "taille implausible (50 m) : mesh laissé tel que convoar l'a produit")
    rapport("Vitre" in bx and "Rocher" in bx, "vitre alpha 0,5 et rocher conservés")
    lo, hi, _ = bx["Rocher"]
    rapport(abs(hi[0] - lo[0] - 4) < 1e-3, "rocher sans skin : taille inchangée")
    rapport(not any(k.startswith("Boite") for k in bx), "plus aucune boîte autour des animaux")
    # --keep-invisible
    od2 = tmp / (variant + "_keep")
    od2.mkdir()
    (od2 / "R.oar").write_bytes(oar.read_bytes())
    s2 = od2 / "convoar_fake.py"
    s2.write_text(FAKE)
    s2.chmod(0o755)
    make_gltf(od2 / "fake_out", variant)
    r = run_tool(od2 / "R.oar", "--keep-invisible", fake=s2)
    js2, bin2 = read_glb(od2 / "R.glb")
    bx2 = world_boxes(js2, bin2)
    rapport("5 mesh(es) riggé(s) remis à l'échelle, 0 prim(s) invisible(s) retiré(s)" in r.stdout and "BoiteHippo" in bx2 and "Orphelin" in bx2,
            "--keep-invisible garde les prims invisibles", r.stdout[-500:])
    # --reperes
    od3 = tmp / (variant + "_rep")
    od3.mkdir()
    (od3 / "R.oar").write_bytes(oar.read_bytes())
    s3 = od3 / "convoar_fake.py"
    s3.write_text(FAKE)
    s3.chmod(0o755)
    make_gltf(od3 / "fake_out", variant)
    r = run_tool(od3 / "R.oar", "--reperes", fake=s3)
    js3, bin3 = read_glb(od3 / "R.glb")
    rep = [n for n in js3["nodes"] if n.get("name", "").startswith("REPERE")]
    rapport(len(rep) == 4 and "[repères] 4" in r.stdout and any(abs(n["translation"][0] - 100) < 0.01 and abs(n["translation"][1] - 23.5) < 0.01 for n in rep),
            f"--reperes : un mât par animal, au pied de l'animal ({len(rep)} trouvés)", r.stdout[-400:])
    # --diag
    before = (od / "R.glb").read_bytes()
    r = run_tool(o, "--diag", "--glb", str(od / "fake_out" / "scene.gltf"), fake=sub)
    out = r.stdout
    rapport(r.returncode == 0 and "riggé : oui" in out and "transparent : oui" in out, "--diag : liste les objets", out[-800:])
    rapport((od / "R.glb").read_bytes() == before, "--diag ne modifie rien")
    n_ok = sum(1 for l in out.splitlines() if "Hippo" in l and "nœud introuvable" not in l and "GLB : nœud" in l)
    rapport(n_ok >= 1 and "nœuds GLB trouvés : 13/13" in out, f"--diag : correspondance des nœuds ({variant})", [l for l in out.splitlines() if "trouvés" in l])
    if variant == "uuid":
        print("\n".join(l for l in out.splitlines() if "[diag]" in l or "Hippo" in l))

# ---------- images absentes : nouvel essai de convoar ----------
print("--- images absentes")
od = tmp / "retry"
od.mkdir()
(od / "R.oar").write_bytes(oar.read_bytes())
make_gltf(od / "fake_out", "uuid")
gj = json.loads((od / "fake_out" / "scene.gltf").read_text())
gj["images"] = [{"uri": "AA11_256_256.png"}, {"uri": "BB22_256_256.png"}]
(od / "fake_out" / "scene.gltf").write_text(json.dumps(gj))
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGD4DwABBAEAHMBXQAAAAABJRU5ErkJggg==")
(od / "fake_out" / "AA11_256_256.png").write_bytes(PNG)
(od / "fake_out" / "BB22_256_256.png.tard").write_bytes(PNG)      # n'est renommée qu'au 2e essai
RETRY = FAKE.replace('print("fake convoar")', 'n = pathlib.Path(__file__).with_name("n.txt")\nk = int(n.read_text()) + 1 if n.exists() else 1\nn.write_text(str(k))\n'
                     'f = out / "BB22_256_256.png.tard"\nif k == 1:\n    f.unlink()\nelse:\n    f.rename(out / "BB22_256_256.png")\nprint("fake convoar essai", k)')
rs = od / "convoar_fake.py"
rs.write_text(RETRY)
rs.chmod(0o755)
r = run_tool(od / "R.oar", fake=rs)
rapport("nouvel essai 1/2" in r.stdout and "absente(s) sur" not in r.stdout and (od / "R.glb").exists(),
        "image manquante : convoar relancé, texture récupérée", r.stdout[-700:])

# ---------- réencodage des textures : illisibles remplacées par un gris, sculpt maps intactes ----------
print("--- réencodage")
from PIL import Image  # noqa: E402
def j2k(color, size=(32, 32)):
    b = io.BytesIO(); Image.new("RGB", size, color).save(b, "JPEG2000", no_jp2=True); return b.getvalue()
u_ok, u_bad, u_sc = U(), U(), U()
sculpt_xml = ("<SceneObjectGroup><SceneObjectPart><Shape><SculptTexture><UUID>%s</UUID></SculptTexture></Shape></SceneObjectPart></SceneObjectGroup>" % u_sc).encode()
cassee = b"ceci n'est pas du JPEG2000" * 20
reenc_src, reenc_dst = tmp / "RE.oar", tmp / "RE-reenc.oar"
with tarfile.open(reenc_src, "w:gz") as t:
    for nom, data in ((f"assets/{u_ok}_texture.jp2", j2k((200, 30, 30))), (f"assets/{u_bad}_texture.jp2", cassee),
                      (f"assets/{u_sc}_texture.jp2", cassee), ("objects/sculpt.xml", sculpt_xml)):
        ti = tarfile.TarInfo(nom); ti.size = len(data); t.addfile(ti, io.BytesIO(data))
T.reencode_oar(reenc_src, reenc_dst)
with tarfile.open(reenc_dst) as t:
    out = {m.name: t.extractfile(m).read() for m in t if m.isfile()}
def lisible(d):
    try:
        im = Image.open(io.BytesIO(d)); im.load(); return im.size
    except Exception:
        return None
rapport(lisible(out[f"assets/{u_ok}_texture.jp2"]) == (32, 32), "texture valide : réencodée, lisible")
rapport(lisible(out[f"assets/{u_bad}_texture.jp2"]) == (4, 4), "texture illisible : remplacée par un gris 4x4 lisible", lisible(out[f"assets/{u_bad}_texture.jp2"]))
rapport(out[f"assets/{u_sc}_texture.jp2"] == cassee, "sculpt map : laissée intacte")
liste = reenc_dst.with_name("RE-reenc-illisibles.txt")
rapport(liste.is_file() and liste.read_text(encoding="utf-8").split() == [f"assets/{u_bad}_texture.jp2"], "liste des illisibles écrite (une seule, hors sculpt map)")

# ---------- version ----------
print("--- version")
vfile = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
v = subprocess.run([sys.executable, str(TOOL), "--version"], capture_output=True, text=True, cwd=tmp, timeout=30)   # le délai prouve qu'aucune pause « Entrée » n'attend
rapport(v.returncode == 0 and v.stdout.strip() == "oar2glb __VERSION__" and not v.stderr, "--version (source) : affiche la version et rend la main, sans pause", (v.returncode, v.stdout, v.stderr))
dist = ROOT / "dist" / "oar2glb.py"
rapport(dist.is_file(), "dist/oar2glb.py fabriqué par build.py (lancer python build.py avant)")
if dist.is_file():
    txt = dist.read_text(encoding="utf-8")
    v = subprocess.run([sys.executable, str(dist), "--version"], capture_output=True, text=True, cwd=tmp, timeout=30)
    rapport("__VERSION__" not in txt and v.returncode == 0 and v.stdout.strip().startswith("oar2glb " + vfile), "--version (dist) : version du fichier VERSION", (v.returncode, v.stdout, vfile))
    r = subprocess.run([sys.executable, str(dist), str(tmp / "R.oar"), "--convoar", str(fake), "--nopause"], capture_output=True, text=True, cwd=tmp)
    log = dist.with_name("oar2glb.log")
    lignes = log.read_text(encoding="utf-8").splitlines() if log.is_file() else []
    rapport((r.stdout.splitlines() or [""])[0].startswith("[oar2glb] " + vfile) and (lignes or [""])[0].startswith("[oar2glb] " + vfile), "le journal commence par la version", (r.stdout[:120], lignes[:2]))
    log.unlink(missing_ok=True)

print("\n" + ("TOUT PASSE" if not bad else f"{bad} ÉCHEC(S)"))
sys.exit(1 if bad else 0)
