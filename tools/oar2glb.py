#!/usr/bin/env python3
"""
oar2glb.py - OAR OpenSim -> GLB unique (convoar + réparation + empaquetage)

Usage :  python oar2glb.py --version
         python oar2glb.py "P:\\chemin\\MaRegion.oar" [--reencode] [--max 600] [--convoar chemin\\convoar.exe] [--keep] [--keep-invisible] [--markers]
         python oar2glb.py "P:\\chemin\\MaRegion.oar" --diag [--glb MaRegion.glb]     (ne modifie rien, ne lance pas convoar)

Étapes :
 1. (option --reencode) textures J2K de l'OAR décodées puis réencodées proprement avec Pillow
    dans un OAR temporaire -> supprime les "unhandled number of components: 0" de convoar.
 2. convoar lancé via un petit lanceur convoar_inv.exe (compilé une fois avec le csc.exe de Windows)
    qui force la culture invariante : nombres en 0.5 et pas 0,5, sans toucher aux réglages Windows.
 3. Réparation du .gltf (backslashes orphelins) + contrôle de cohérence (tailles des vecteurs).
 4. Retrait des objets hors région (skybox à 3000 m...) : |coordonnée| > --max mètres.
 5. Meshes riggés (animesh) : bloc skin lu dans assets/*_mesh.llmesh ; échelle du prim ignorée, bind_shape_matrix
    appliquée aux sommets, modèle posé au sol (terrain de l'OAR) à la position de la racine de l'objet.
    Prims entièrement transparents (faces alpha 0 ou texture invisible standard) retirés (--keep-invisible pour les garder).
 6. Empaquetage en un seul .glb (buffers + textures intégrés), pur Python.
Sortie : MaRegion.glb à côté de l'OAR.
"""
import argparse, base64, io, json, math, os, re, shutil, struct, subprocess, sys, tarfile, time, traceback, uuid, zlib
from pathlib import Path

# <<I18N_PY>>
def _i18n_boot():   # depuis les sources : charge src/i18n_py.py ; fabriqué par build.py (dist\) : ce bloc est remplacé par le texte de i18n_py.py avec les langues intégrées
    import importlib.util, pathlib
    here = pathlib.Path(__file__).resolve().parent
    for p in (here / "i18n_py.py", here.parent / "src" / "i18n_py.py"):
        if p.is_file():
            spec = importlib.util.spec_from_file_location("i18n_py", p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            return m
    raise SystemExit("i18n_py.py not found / introuvable")


_I18N = _i18n_boot()
_tr, i18n_add_common = _I18N._tr, _I18N.i18n_add_common
# <</I18N_PY>>

VERSION = "__VERSION__"      # remplacé par build.py (fichier VERSION) dans dist/oar2glb.py
DEFAULT_CONVOAR = r"P:\_OpenSim\SL&OS\MOSES\convoar-master\dist\convoar.exe"

LAUNCHER_CS = r"""
using System; using System.Globalization; using System.IO; using System.Threading;
class ConvoarInvariant {
  static int Main(string[] a) {
    CultureInfo c = CultureInfo.InvariantCulture;
    CultureInfo.DefaultThreadCurrentCulture = c; CultureInfo.DefaultThreadCurrentUICulture = c;
    Thread.CurrentThread.CurrentCulture = c; Thread.CurrentThread.CurrentUICulture = c;
    return AppDomain.CurrentDomain.ExecuteAssembly(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "convoar.exe"), a);
  }
}
"""


# ---------- 1. réencodage des textures ----------
def reencode_one(data):
    # décode une texture J2K et la réencode proprement ; None si illisible (laissée telle quelle)
    from PIL import Image
    try:
        im = Image.open(io.BytesIO(data)); im.load()
        if im.mode not in ("L", "LA", "RGB", "RGBA"):
            im = im.convert("RGBA")
        n = max(1, min(6, int(math.log2(max(1, min(im.size)))) + 1))
        buf = io.BytesIO()
        im.save(buf, "JPEG2000", num_resolutions=n, no_jp2=True)   # codestream J2C brut, comme les assets OpenSim
        return buf.getvalue()
    except Exception:
        return None


def neutral_texture():
    # petit J2K gris, même format que reencode_one : remplace une texture que Pillow ne sait pas lire
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), (128, 128, 128)).save(buf, "JPEG2000", num_resolutions=3, no_jp2=True)
    return buf.getvalue()


REENC_BATCH = 512      # textures envoyées aux workers par lot : borne la mémoire (ex.map sur tout enverrait tout d'un coup)


def reencode_oar(src, dst):
    try:
        import PIL  # noqa: F401
    except ImportError:
        sys.exit(_tr("py.oar2glb.erreur_reencode_demande_pillow_absent_de", sys.executable, sys.executable))
    import time
    from concurrent.futures import ProcessPoolExecutor
    t0 = time.time()
    print(_tr("py.oar2glb.textures_lecture_de_0", src.name))
    members = []
    with tarfile.open(src, "r:*") as tin:
        for m in tin:
            f = tin.extractfile(m) if m.isfile() else None
            members.append((m, f.read() if f else None))
    sculpts = set()
    for m, d in members:
        if d is not None and m.name.startswith("objects/") and m.name.endswith(".xml"):
            sculpts.update(re.findall(r"<SculptTexture>\s*(?:<(?:UUID|Guid)>)?\s*([0-9a-fA-F-]{36})", d.decode("utf-8", "replace")))
    sculpts = {u.lower() for u in sculpts}
    idx = [i for i, (m, d) in enumerate(members)
           if d is not None and m.name.startswith("assets/") and m.name.endswith("_texture.jp2")
           and m.name[7:43].lower() not in sculpts]
    print(_tr("py.oar2glb.textures_0_sculpt_maps_laissees_intactes", len(sculpts)))
    workers = max(1, min(8, (os.cpu_count() or 2) - 1))   # 8 au plus : chaque worker garde ses textures décodées en mémoire
    print(_tr("py.oar2glb.textures_0_textures_a_reencoder_sur", len(idx), workers, time.time() - t0))
    ok = bad = k = 0
    grey, illisibles = neutral_texture(), []
    step = max(1, len(idx) // 20)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for b in range(0, len(idx), REENC_BATCH):
            sub = idx[b:b + REENC_BATCH]
            for i, res in zip(sub, ex.map(reencode_one, [members[i][1] for i in sub], chunksize=8)):
                k += 1
                m, _ = members[i]
                if res is None:      # illisible pour Pillow : le décodeur de convoar peut planter dessus, on met un gris neutre
                    bad += 1
                    illisibles.append(m.name)
                    res = grey
                else:
                    ok += 1
                m.size = len(res)
                members[i] = (m, res)
                if k % step == 0 or k == len(idx):
                    print(_tr("py.oar2glb.textures_0_1_2_3_0f", k, len(idx), 100 * k // len(idx), time.time() - t0), flush=True)
    print(_tr("py.oar2glb.textures_ecriture_de_0", dst.name))
    with tarfile.open(dst, "w:gz", compresslevel=1) as tout:
        for m, d in members:
            tout.addfile(m, io.BytesIO(d) if d is not None else None)
    liste = dst.with_name(dst.stem + "-illisibles.txt")
    if illisibles:
        liste.write_text("\n".join(illisibles) + "\n", encoding="utf-8")
    print(_tr("py.oar2glb.textures_0_reencodees_1_illisibles_remplacee", ok, bad)
          + (_tr("py.oar2glb.list_paren", liste.name) if illisibles else "") + f" - {time.time() - t0:.0f} s")


# ---------- lecture de l'OAR : objets, blocs skin des meshes, terrain ----------
# Textures « invisibles » standard (SL/OpenSim) : « Transparent » du sélecteur et IMG_INVISIBLE (invisiprim)
INVISIBLE_TEX = {"8dcd4a48-2d37-4909-9f78-f7a9eb4ef903", "3a367d1c-bef1-6d43-7595-e88c1e3aadb3"}
UUID_RX = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def llsd_bin(d, p=0):
    # LLSD binaire (en-têtes et blocs des .llmesh) -> (valeur, position suivante)
    t = d[p:p + 1]
    p += 1
    if t == b"{":
        n = struct.unpack_from(">I", d, p)[0]
        p += 4
        out = {}
        for _ in range(n):
            if d[p:p + 1] != b"k":
                raise ValueError(_tr("py.oar2glb.cle_llsd_attendue"))
            ln = struct.unpack_from(">I", d, p + 1)[0]
            key = d[p + 5:p + 5 + ln].decode("utf-8", "replace")
            out[key], p = llsd_bin(d, p + 5 + ln)
        if d[p:p + 1] != b"}":
            raise ValueError(_tr("py.oar2glb.fin_de_table_llsd_attendue"))
        return out, p + 1
    if t == b"[":
        n = struct.unpack_from(">I", d, p)[0]
        p += 4
        out = []
        for _ in range(n):
            v, p = llsd_bin(d, p)
            out.append(v)
        if d[p:p + 1] != b"]":
            raise ValueError(_tr("py.oar2glb.fin_de_tableau_llsd_attendue"))
        return out, p + 1
    if t == b"!":
        return None, p
    if t == b"1":
        return True, p
    if t == b"0":
        return False, p
    if t == b"i":
        return struct.unpack_from(">i", d, p)[0], p + 4
    if t == b"r":
        return struct.unpack_from(">d", d, p)[0], p + 8
    if t == b"d":
        return struct.unpack_from(">d", d, p)[0], p + 8
    if t == b"u":
        return d[p:p + 16], p + 16
    if t in (b"s", b"l", b"b"):
        ln = struct.unpack_from(">I", d, p)[0]
        v = d[p + 4:p + 4 + ln]
        return (v if t == b"b" else v.decode("utf-8", "replace")), p + 4 + ln
    raise ValueError(_tr("py.oar2glb.type_llsd_inconnu_0_r", t))


def llmesh_skin(data):
    # (skin, erreur) : skin = dict du bloc skin (zlib + LLSD), None si le mesh n'en a pas
    try:
        start = data.find(b"\n") + 1 if data[:2] == b"<?" else 0
        hdr, end = llsd_bin(data, start)
        sk = hdr.get("skin")
        if not isinstance(sk, dict) or not sk.get("size"):
            return None, None
        off, size = int(sk.get("offset", 0)), int(sk["size"])
        for base in (end, end + 1):     # les décalages partent de la fin de l'en-tête (un \n éventuel)
            try:
                skin, _ = llsd_bin(zlib.decompress(data[base + off:base + off + size]), 0)
                if isinstance(skin, dict):
                    return skin, None
            except Exception:
                continue
        return None, _tr("py.oar2glb.bloc_skin_present_mais_illisible")
    except Exception as e:
        return None, _tr("py.oar2glb.en_tete_du_mesh_illisible_0", e)


def llmesh_domains(data, n=256):
    # domaines de position (min, max) des premiers sous-maillages du plus haut niveau de détail ; [] si illisible
    try:
        start = data.find(b"\n") + 1 if data[:2] == b"<?" else 0
        hdr, end = llsd_bin(data, start)
        hl = hdr.get("high_lod")
        if not isinstance(hl, dict) or not hl.get("size"):
            return []
        for base in (end, end + 1):
            try:
                subs, _ = llsd_bin(zlib.decompress(data[base + int(hl.get("offset", 0)):base + int(hl.get("offset", 0)) + int(hl["size"])]), 0)
                out = []
                for sm in subs[:n]:
                    d = sm.get("PositionDomain") or {}
                    if "Min" in d and "Max" in d:
                        out.append((d["Min"], d["Max"]))
                return out
            except Exception:
                continue
    except Exception:
        pass
    return []


def llmesh_geometry(data, lod="high_lod"):
    # géométrie du plus haut niveau de détail d'un .llmesh : liste (une entrée par face, None si vide) de
    # {"pos": [(x, y, z)], "nor": [...] ou None, "uv": [(u, v)] ou None, "tri": [indices]} ; None si illisible
    import array
    try:
        start = data.find(b"\n") + 1 if data[:2] == b"<?" else 0
        hdr, end = llsd_bin(data, start)
        blk = hdr.get(lod)
        if not isinstance(blk, dict) or not blk.get("size"):
            return None
        off, size = int(blk.get("offset", 0)), int(blk["size"])
        subs = None
        for base in (end, end + 1):
            try:
                subs, _ = llsd_bin(zlib.decompress(data[base + off:base + off + size]), 0)
                break
            except Exception:
                continue
        if not isinstance(subs, list):
            return None

        def u16(b):
            a = array.array("H")
            a.frombytes(bytes(b[:len(b) // 2 * 2]))
            if sys.byteorder == "big":
                a.byteswap()
            return a
        out = []
        for sm in subs:
            if not isinstance(sm, dict) or sm.get("NoGeometry") or not sm.get("Position") or not sm.get("TriangleList"):
                out.append(None)
                continue
            d = sm.get("PositionDomain") or {}
            mn, mx = d.get("Min", [-0.5] * 3), d.get("Max", [0.5] * 3)
            a = u16(sm["Position"])
            n = len(a) // 3
            pos = [tuple(mn[k] + a[3 * i + k] / 65535.0 * (mx[k] - mn[k]) for k in range(3)) for i in range(n)]
            nor = None
            if sm.get("Normal"):
                b = u16(sm["Normal"])
                if len(b) >= 3 * n:
                    nor = [tuple(b[3 * i + k] / 65535.0 * 2.0 - 1.0 for k in range(3)) for i in range(n)]
            uv = None
            if sm.get("TexCoord0"):
                t = u16(sm["TexCoord0"])
                td = sm.get("TexCoord0Domain") or {}
                tmn, tmx = td.get("Min", [0.0, 0.0]), td.get("Max", [1.0, 1.0])
                if len(t) >= 2 * n:
                    uv = [tuple(tmn[k] + t[2 * i + k] / 65535.0 * (tmx[k] - tmn[k]) for k in range(2)) for i in range(n)]
            tri = list(u16(sm["TriangleList"]))
            tri = tri[:len(tri) // 3 * 3]
            out.append({"pos": pos, "nor": nor, "uv": uv, "tri": tri})
        return out
    except Exception:
        return None


def bind_shape(skin):
    m = skin.get("bind_shape_matrix") if skin else None
    if isinstance(m, list) and len(m) == 16 and all(isinstance(v, (int, float)) for v in m):
        return [float(v) for v in m]
    return None


def parse_texture_entry(b64):
    # TextureEntry OpenSim -> ({face: texture UUID}, {face: alpha 0..255}), clé None = face par défaut
    try:
        d = base64.b64decode(b64)
    except Exception:
        return None
    p = 0

    def faces():
        nonlocal p
        if p >= len(d):
            return None
        bits = 0
        while True:
            b = d[p]
            bits = (bits << 7) | (b & 0x7F)
            p += 1
            if not b & 0x80 or p >= len(d):
                break
        return [f for f in range(32) if bits >> f & 1] if bits else None

    def section(size, conv):
        nonlocal p
        out = {}
        if p + size > len(d):
            raise ValueError
        out[None] = conv(d[p:p + size])
        p += size
        while True:
            fs = faces()
            if fs is None:
                break
            if p + size > len(d):
                raise ValueError
            v = conv(d[p:p + size])
            p += size
            for f in fs:
                out[f] = v
        return out
    try:
        tex = section(16, lambda s: str(uuid.UUID(bytes=bytes(s))))
        col = section(4, lambda s: 255 - s[3])      # couleur stockée inversée : alpha = 255 - octet
        return tex, col
    except Exception:
        return None


def part_invisible(tex_entry):
    # vrai si CHAQUE face (0..31) est entièrement transparente ou porte une texture invisible standard
    if not tex_entry:
        return False
    tex, col = tex_entry
    for f in range(32):
        t = tex.get(f, tex[None])
        a = col.get(f, col[None])
        if not (a == 0 or t.lower() in INVISIBLE_TEX):
            return False
    return True


def tex_summary(tex_entry):
    if not tex_entry:
        return _tr("py.oar2glb.sans_textureentry")
    tex, col = tex_entry
    n = len({f for f in list(tex) + list(col) if f is not None})
    return _tr("py.oar2glb.texture_0_alpha_1_2f", tex[None][:8], col[None] / 255) + (_tr("py.oar2glb.0_face_s_a_part", n) if n else "")


def _txt(el, path):
    e = el.find(path)
    return (e.text or "").strip() if e is not None and e.text else ""


def _vec(el, path, keys="XYZ"):
    e = el.find(path)
    if e is None:
        return None
    try:
        return [float(_txt(e, k)) for k in keys]
    except ValueError:
        return None


def parse_object(xml_bytes):
    # un fichier objects/*.xml -> liste de parties (la première est la racine)
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_bytes.lstrip(b"\xef\xbb\xbf"))
    els = list(root.iter("SceneObjectPart"))
    parts = []
    for el in els:
        sh = el.find("Shape")
        mesh = None
        if sh is not None and (int(float(_txt(sh, "SculptType") or 0)) & 7) == 5:
            mesh = (_txt(sh, "SculptTexture/Guid") or _txt(sh, "SculptTexture/UUID") or _txt(sh, "SculptTexture")).lower() or None
        te = _txt(sh, "TextureEntry") if sh is not None else ""
        tex_e = parse_texture_entry(te) if te else None
        parts.append({
            "uuid": (_txt(el, "UUID/Guid") or _txt(el, "UUID/UUID") or _txt(el, "UUID")).lower(),
            "name": _txt(el, "Name"),
            "gpos": _vec(el, "GroupPosition"), "off": _vec(el, "OffsetPosition"),
            "rot": _vec(el, "RotationOffset", "XYZW"), "scale": _vec(el, "Scale"),
            "mesh": mesh, "invisible": part_invisible(tex_e), "tex": tex_summary(tex_e),
        })
    return parts


def oar_scan(oar, terrain_seul=False):
    # terrain_seul : ne lit que archive.xml, settings/ et terrains/ (ni objets ni meshes)
    size, groups, skins, terrain, water = (256.0, 256.0), [], {}, None, None
    with tarfile.open(oar, "r:*") as t:
        for m in t:
            if not m.isfile():
                continue
            if m.name == "archive.xml":
                x = t.extractfile(m).read().decode("utf-8", "replace")
                ms = re.search(r"<size_in_meters>\s*([\d.]+)\s*,\s*([\d.]+)", x)
                if ms:
                    size = (float(ms.group(1)), float(ms.group(2)))
            elif m.name.startswith("settings/") and m.name.endswith(".xml") and water is None:
                mw = re.search(r"<WaterHeight>\s*([-+0-9.eE]+)\s*</WaterHeight>", t.extractfile(m).read().decode("utf-8", "replace"))
                if mw:
                    try:
                        water = (float(mw.group(1)), m.name)
                    except ValueError:
                        pass
            elif terrain_seul and not m.name.startswith("terrains/"):
                continue
            elif m.name.startswith("objects/") and m.name.endswith(".xml"):
                try:
                    parts = parse_object(t.extractfile(m).read())
                except Exception as e:
                    print(_tr("py.oar2glb.oar_0_illisible_1", m.name, e))
                    continue
                if parts and parts[0]["gpos"]:
                    groups.append({"file": m.name, "parts": parts})
            elif m.name.startswith("assets/") and m.name.endswith("_mesh.llmesh"):
                raw = t.extractfile(m).read()
                skin, err = llmesh_skin(raw)
                if skin is not None or err:
                    skins[m.name[7:43].lower()] = {"skin": skin, "err": err, "bsm": bind_shape(skin),
                                                   "dom": llmesh_domains(raw) if skin is not None else [],
                                                   "raw": raw if skin is not None else None}
            elif m.name.startswith("terrains/") and m.name.endswith(".r32") and terrain is None:
                raw = t.extractfile(m).read()
                n = int(math.isqrt(len(raw) // 4))
                if n * n * 4 == len(raw):
                    terrain = (n, struct.unpack(f"<{n * n}f", raw))
    # position monde des parties (la racine : GroupPosition ; les autres : racine + décalage tourné)
    for g in groups:
        r = g["parts"][0]
        for i, p in enumerate(g["parts"]):
            gp = p["gpos"] or r["gpos"]
            if i == 0 or not p["off"]:
                p["wpos"] = list(gp)
            else:
                q = r["rot"] or [0, 0, 0, 1]
                o = p["off"]
                tq = [2 * (q[1] * o[2] - q[2] * o[1]), 2 * (q[2] * o[0] - q[0] * o[2]), 2 * (q[0] * o[1] - q[1] * o[0])]
                rv = [o[0] + q[3] * tq[0] + (q[1] * tq[2] - q[2] * tq[1]),
                      o[1] + q[3] * tq[1] + (q[2] * tq[0] - q[0] * tq[2]),
                      o[2] + q[3] * tq[2] + (q[0] * tq[1] - q[1] * tq[0])]
                p["wpos"] = [gp[k] + rv[k] for k in range(3)]
            p["gpos"] = gp
    return {"size": size, "groups": groups, "skins": skins, "terrain": terrain, "water": water}


def oar_info(scan):
    # objets racines au format utilisé par fix_positions : pos, rot, nom
    objs = [{"pos": g["parts"][0]["gpos"], "rot": g["parts"][0]["rot"], "name": g["parts"][0]["name"]}
            for g in scan["groups"]]
    size = scan["size"]
    print(_tr("py.oar2glb.oar_region_0_g_x_1", size[0], size[1]))
    if objs:
        pts = [o["pos"] for o in objs]
        lo = [round(min(p[k] for p in pts), 1) for k in range(3)]
        hi = [round(max(p[k] for p in pts), 1) for k in range(3)]
        print(_tr("py.oar2glb.oar_0_objets_de_1_a", len(objs), lo, hi))
    return size, objs


def terrain_height(terrain, x, y):
    # hauteur du sol (interpolation bilinéaire, 1 échantillon par mètre) ; None sans terrain
    if not terrain:
        return None
    n, h = terrain
    x = min(max(x, 0.0), n - 1.001)
    y = min(max(y, 0.0), n - 1.001)
    i, j = int(x), int(y)
    fx, fy = x - i, y - j
    a, b = h[j * n + i], h[j * n + i + 1]
    c, d = h[(j + 1) * n + i], h[(j + 1) * n + i + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


# ---------- var-region : convoar ramène tout dans 256 m, on remet les vraies positions ----------
def fix_positions(g, objs):
    # glTF = (X, Z, -Y) OpenSim ; la hauteur n'est jamais tronquée, X/Y le sont aux bords 0..256
    def ok(n, o):
        if 0.0 <= o <= 256.0:
            return abs(n - o) < 0.05
        return n > 254.0 if o > 256.0 else n < 2.0
    def qdot(a, b):
        return abs(sum(x * y for x, y in zip(a, b)))
    roots = [i for sc in g.get("scenes", []) for i in sc.get("nodes", [])]
    cand = {}
    for i in roots:
        n = g["nodes"][i]
        tx, ty, tz = node_pos(n)
        cs = [j for j, o in enumerate(objs)
              if abs(ty - o["pos"][2]) < 0.05 and ok(tx, o["pos"][0]) and ok(-tz, o["pos"][1])]
        nm = n.get("name", "")
        same = [j for j in cs if objs[j]["name"] and objs[j]["name"] == nm]
        if same:
            cs = same
        q = n.get("rotation")
        if q and len(cs) > 1:
            cs.sort(key=lambda j: -qdot(q, [objs[j]["rot"][0], objs[j]["rot"][2], -objs[j]["rot"][1], objs[j]["rot"][3]])
                    if objs[j]["rot"] else 0)
        cand[i] = cs
    used, moved, lost = set(), 0, 0
    for i in sorted(roots, key=lambda i: len(cand[i])):
        j = next((j for j in cand[i] if j not in used), None)
        if j is None:
            lost += 1
            continue
        used.add(j)
        x, y, z = objs[j]["pos"]
        new = [x, z, -y]
        n = g["nodes"][i]
        old = node_pos(n)
        if any(abs(a - b) > 0.01 for a, b in zip(old, new)):
            if "matrix" in n:
                n["matrix"][12:15] = new
            else:
                n["translation"] = new
            moved += 1
    print(_tr("py.oar2glb.var_region_0_objet_s_replace", moved, len(used), lost))


# ---------- 2. lanceur culture invariante ----------
def pe_platform(exe):
    d = Path(exe).read_bytes()
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    machine, nsec = struct.unpack_from("<HH", d, pe + 4)
    optsz = struct.unpack_from("<H", d, pe + 20)[0]
    opt = pe + 24
    magic = struct.unpack_from("<H", d, opt)[0]
    rva, size = struct.unpack_from("<II", d, opt + (96 if magic == 0x10B else 112) + 14 * 8)
    if machine == 0x8664:
        return "x64"
    if not rva:
        return "x86"
    sec = opt + optsz
    for i in range(nsec):
        vsz, va, rsz, raw = struct.unpack_from("<IIII", d, sec + i * 40 + 8)
        if va <= rva < va + max(vsz, rsz):
            flags = struct.unpack_from("<I", d, rva - va + raw + 16)[0]
            return "x86" if flags & 0x20002 else "anycpu"
    return "anycpu"


def ensure_config(convoar, launcher):
    # config du lanceur = config de convoar + loadFromRemoteSources (dist issu d'un ZIP téléchargé = "zone internet")
    src = convoar.with_name("convoar.exe.config")
    txt = src.read_text(encoding="utf-8-sig") if src.exists() else "<?xml version=\"1.0\"?>\n<configuration>\n</configuration>\n"
    tag = '<loadFromRemoteSources enabled="true"/>'
    if "loadFromRemoteSources" not in txt:
        if re.search(r"<runtime\s*>", txt):
            txt = re.sub(r"<runtime\s*>", "<runtime>\n    " + tag, txt, count=1)
        else:
            txt = txt.replace("</configuration>", "  <runtime>\n    " + tag + "\n  </runtime>\n</configuration>")
    dst = launcher.with_name("convoar_inv.exe.config")
    if not dst.exists() or dst.read_text(encoding="utf-8-sig") != txt:
        dst.write_text(txt, encoding="utf-8")
        print(_tr("py.oar2glb.lanceur_0_mis_a_jour_loadfromremotesources", dst.name))


def ensure_launcher(convoar):
    convoar = Path(convoar)
    launcher = convoar.with_name("convoar_inv.exe")
    if launcher.exists():
        ensure_config(convoar, launcher)
        return launcher
    win = os.environ.get("WINDIR", r"C:\Windows")
    csc = next((p for p in (Path(win, r"Microsoft.NET\Framework64\v4.0.30319\csc.exe"),
                            Path(win, r"Microsoft.NET\Framework\v4.0.30319\csc.exe")) if p.exists()), None)
    if not csc:
        sys.exit(_tr("py.oar2glb.erreur_csc_exe_net_framework_4"))
    plat = pe_platform(convoar)
    src = convoar.with_name("convoar_inv.cs")
    src.write_text(LAUNCHER_CS, encoding="utf-8")
    r = subprocess.run([str(csc), "/nologo", "/target:exe", f"/platform:{plat}", f"/out:{launcher}", str(src)],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(_tr("py.oar2glb.erreur_compilation_du_lanceur_0_1", r.stdout, r.stderr))
    ensure_config(convoar, launcher)
    print(_tr("py.oar2glb.lanceur_0_compile_1", launcher, plat))
    return launcher


def run_convoar(convoar, oar, outdir):
    exe = ensure_launcher(convoar) if os.name == "nt" else Path(convoar)
    args = [str(exe), "--outputdir", outdir.name, oar.name]   # options AVANT le fichier
    print(_tr("py.oar2glb.convoar"), " ".join(f'"{a}"' if " " in a else a for a in args))
    enc = "oem" if os.name == "nt" else "utf-8"
    p = subprocess.Popen(args, cwd=oar.parent, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding=enc, errors="replace")
    for line in p.stdout:
        print(line.rstrip())
    p.wait()
    print(_tr("py.oar2glb.convoar_code_retour_0", p.returncode))


# ---------- 3. lecture + contrôle ----------
MAX_RETRY = 2


def missing_images(outdir):
    gl = sorted(Path(outdir).glob("*.gltf"), key=lambda q: q.stat().st_mtime)
    if not gl:
        return []
    from urllib.parse import unquote
    g = load_gltf(gl[-1])
    return sorted({unquote(i["uri"]) for i in g.get("images", []) if "uri" in i and not i["uri"].startswith("data:")
                   and find_file(Path(outdir), unquote(i["uri"])) is None})


def load_gltf(path):
    txt = path.read_text(encoding="utf-8", errors="replace")
    txt = re.sub(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'\\\\', txt)
    try:
        return json.loads(txt)
    except json.JSONDecodeError as e:
        line = txt.splitlines()[e.lineno - 1] if e.lineno <= len(txt.splitlines()) else ""
        sys.exit(_tr("py.oar2glb.erreur_gltf_invalide_0_ligne_1", e, e.lineno, line.strip()[:120]))


def check(g):
    tl = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}
    errs = []
    for i, n in enumerate(g.get("nodes", [])):
        for k, l in (("translation", 3), ("rotation", 4), ("scale", 3), ("matrix", 16)):
            if k in n and len(n[k]) != l:
                errs.append(f"node {i} {k} = {n[k]}")
    for i, a in enumerate(g.get("accessors", [])):
        for k in ("min", "max"):
            if k in a and len(a[k]) != tl.get(a["type"], len(a[k])):
                errs.append(f"accessor {i} {k} = {a[k]}")
    if errs:
        sys.exit(_tr("py.oar2glb.erreur_0_vecteurs_de_mauvaise_taille", len(errs))
                 + "\n  ".join(errs[:5]))


def node_pos(n):
    if "translation" in n:
        return n["translation"]
    if "matrix" in n:
        return n["matrix"][12:15]
    return [0, 0, 0]


# ---------- matrices glTF (colonnes d'abord : indice = colonne * 4 + ligne) ----------
def quat_mat(q, s=(1, 1, 1), t=(0, 0, 0)):
    x, y, z, w = q
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    m = [0.0] * 16
    for c in range(3):
        for k in range(3):
            m[c * 4 + k] = r[k][c] * s[c]
    m[12:15] = t
    m[15] = 1.0
    return m


def node_local(n):
    if "matrix" in n:
        return list(n["matrix"])
    return quat_mat(n.get("rotation", [0, 0, 0, 1]), n.get("scale", [1, 1, 1]), n.get("translation", [0, 0, 0]))


def mat_mul(a, b):
    return [sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4)) for c in range(4) for r in range(4)]


def mat_inv(m):
    a = [[m[c * 4 + r] for c in range(4)] + [1.0 if r == i else 0.0 for i in range(4)] for r in range(4)]
    for i in range(4):
        piv = max(range(i, 4), key=lambda r: abs(a[r][i]))
        if abs(a[piv][i]) < 1e-12:
            return None
        a[i], a[piv] = a[piv], a[i]
        d = a[i][i]
        a[i] = [v / d for v in a[i]]
        for r in range(4):
            if r != i:
                f = a[r][i]
                a[r] = [v - f * w for v, w in zip(a[r], a[i])]
    return [a[r][4 + c] for c in range(4) for r in range(4)]


def mat_trs(m):
    # matrice -> (translation, rotation quaternion, échelle), sans cisaillement
    s = [math.sqrt(sum(m[c * 4 + r] ** 2 for r in range(3))) or 1.0 for c in range(3)]
    r = [[m[c * 4 + k] / s[c] for c in range(3)] for k in range(3)]
    tr = r[0][0] + r[1][1] + r[2][2]
    if tr > 0:
        k = math.sqrt(tr + 1) * 2
        q = [(r[2][1] - r[1][2]) / k, (r[0][2] - r[2][0]) / k, (r[1][0] - r[0][1]) / k, k / 4]
    elif r[0][0] > r[1][1] and r[0][0] > r[2][2]:
        k = math.sqrt(1 + r[0][0] - r[1][1] - r[2][2]) * 2
        q = [k / 4, (r[0][1] + r[1][0]) / k, (r[0][2] + r[2][0]) / k, (r[2][1] - r[1][2]) / k]
    elif r[1][1] > r[2][2]:
        k = math.sqrt(1 + r[1][1] - r[0][0] - r[2][2]) * 2
        q = [(r[0][1] + r[1][0]) / k, k / 4, (r[1][2] + r[2][1]) / k, (r[0][2] - r[2][0]) / k]
    else:
        k = math.sqrt(1 + r[2][2] - r[0][0] - r[1][1]) * 2
        q = [(r[0][2] + r[2][0]) / k, (r[1][2] + r[2][1]) / k, k / 4, (r[1][0] - r[0][1]) / k]
    return list(m[12:15]), q, s


def rot_vec(q, v):
    m = quat_mat(q)
    return [sum(m[c * 4 + r] * v[c] for c in range(3)) for r in range(3)]


class Tree:
    # parents et matrices monde des nœuds d'un glTF
    def __init__(self, g):
        self.g, self.parent, self._w = g, {}, {}
        for i, n in enumerate(g.get("nodes", [])):
            for c in n.get("children", []):
                self.parent[c] = i

    def world(self, i):
        if i not in self._w:
            m = node_local(self.g["nodes"][i])
            self._w[i] = mat_mul(self.world(self.parent[i]), m) if i in self.parent else m
        return self._w[i]

    def pos_os(self, i):
        w = self.world(i)
        return [w[12], -w[14], w[13]]       # glTF (X, Y, Z) -> OpenSim (x, y, z) = (X, -Z, Y)


# ---------- correspondance nœud GLB <-> objets de l'OAR ----------
def node_uuids(g):
    # UUID lisibles dans chaque nœud : nom, extras, nom/extras du mesh, matériaux, images
    out = {}
    for i, n in enumerate(g.get("nodes", [])):
        s = [n.get("name", ""), json.dumps(n.get("extras", ""))]
        if "mesh" in n:
            me = g["meshes"][n["mesh"]]
            s += [me.get("name", ""), json.dumps(me.get("extras", ""))]
            for pr in me.get("primitives", []):
                if "material" in pr:
                    s.append(json.dumps(g["materials"][pr["material"]]))
        for u in UUID_RX.findall(" ".join(map(str, s))):
            out.setdefault(u.lower(), []).append(i)
    return out


def match_nodes(g, scan):
    # {uuid de la partie: (nœud, méthode)} ; méthodes : « UUID du prim », « UUID du mesh », « nom + position »
    tree, uu = Tree(g), node_uuids(g)
    names = {}
    for i, n in enumerate(g.get("nodes", [])):
        if n.get("name"):
            names.setdefault(n["name"], []).append(i)
    res, used = {}, set()
    for grp in scan["groups"]:
        for p in grp["parts"]:
            cand, how = [], None
            if p["uuid"] in uu:
                cand, how = uu[p["uuid"]], _tr("py.oar2glb.uuid_du_prim")
            elif p["mesh"] and p["mesh"] in uu:
                cand, how = uu[p["mesh"]], _tr("py.oar2glb.uuid_du_mesh")
            elif p["name"] in names:
                cand, how = names[p["name"]], "nom + position"
            if not cand:
                continue
            if how == "UUID du prim" and len(cand) == 1:
                res[p["uuid"]] = (cand[0], how)
                used.add(cand[0])
                continue
            def dist(i):
                q = tree.pos_os(i)
                return min(math.dist(q, p["wpos"]), math.dist(q, grp["parts"][0]["gpos"]))
            free = [i for i in cand if i not in used] or cand
            best = min(free, key=lambda i: (round(dist(i), 2), i))      # à égalité : ordre des nœuds = ordre de l'OAR
            if dist(best) <= 2.0:
                res[p["uuid"]] = (best, how)
                used.add(best)
    return res


# ---------- matériaux invisibles ----------
def material_invisible(g, mi, cache):
    if mi not in cache:
        m = g["materials"][mi]
        a = (m.get("pbrMetallicRoughness") or {}).get("baseColorFactor")
        inv = bool(a and len(a) == 4 and a[3] <= 0.004)
        if not inv:
            s = [json.dumps(m)]
            ti = ((m.get("pbrMetallicRoughness") or {}).get("baseColorTexture") or {}).get("index")
            if ti is not None and ti < len(g.get("textures", [])):
                src = g["textures"][ti].get("source")
                if src is not None and src < len(g.get("images", [])):
                    s.append(json.dumps({k: v for k, v in g["images"][src].items() if k != "uri" or not str(v).startswith("data:")}))
            inv = any(u in " ".join(s).lower() for u in INVISIBLE_TEX)
        cache[mi] = inv
    return cache[mi]


def node_all_invisible(g, n, cache):
    if "mesh" not in n:
        return False
    prims = g["meshes"][n["mesh"]].get("primitives", [])
    return bool(prims) and all("material" in p and material_invisible(g, p["material"], cache) for p in prims)


def remove_node(g, i):
    n = g["nodes"][i]
    if n.get("children"):
        n.pop("mesh", None)         # les enfants restent
        return
    for sc in g.get("scenes", []):
        sc["nodes"] = [k for k in sc.get("nodes", []) if k != i]
    for o in g["nodes"]:
        if i in o.get("children", []):
            o["children"] = [k for k in o["children"] if k != i]
    n.pop("mesh", None)


def rig_box_roots(scan):
    # boîtes racines d'animesh : prim simple (pas un mesh) racine d'un objet dont TOUTES les autres parties sont des meshes
    # riggés. Invisible en jeu (cadre de l'animal), mais pas forcément alpha 0 dans l'OAR : convoar la sort en boîte laiteuse.
    out = set()
    for grp in scan["groups"]:
        ps = grp["parts"]
        sk = lambda q: bool(q["mesh"] and (scan["skins"].get(q["mesh"]) or {}).get("bsm"))
        if len(ps) > 1 and ps[0]["mesh"] is None and all(sk(q) for q in ps[1:]):
            out.add(ps[0]["uuid"])
    return out


def remove_invisible(g, scan, match):
    # prims entièrement transparents : par l'OAR (faces alpha 0 / texture invisible), par les matériaux du GLB,
    # et boîtes racines d'animesh. convoar sort un nœud par partie : on retire le nœud de la partie.
    cache, victims = {}, {}
    boxes = rig_box_roots(scan)
    for grp in scan["groups"]:
        for p in grp["parts"]:
            if p["uuid"] in match and (p["invisible"] or p["uuid"] in boxes):
                victims.setdefault(match[p["uuid"]][0], _tr("py.oar2glb.boite_racine_d_animesh") if p["uuid"] in boxes and not p["invisible"] else "transparent (OAR)")
    for i, n in enumerate(g.get("nodes", [])):
        if i not in victims and node_all_invisible(g, n, cache):
            victims[i] = _tr("py.oar2glb.materiaux_transparents_glb")
    for i in sorted(victims):
        print(_tr("py.oar2glb.invisible_node_0_1_retire_2", i, g['nodes'][i].get('name', '?'), victims[i]))
        remove_node(g, i)
    return len(victims)


# ---------- meshes riggés ----------
class ExtraBuffer:
    # données ajoutées en mémoire (accesseurs recalculés), placées dans un buffer final en data: URI
    def __init__(self, g):
        self.g, self.data, self.idx = g, bytearray(), len(g.get("buffers", []))

    def add_vec3(self, pts):
        g = self.g
        g.setdefault("bufferViews", []).append({"buffer": self.idx, "byteOffset": len(self.data), "byteLength": len(pts) * 12, "target": 34962})
        for p in pts:
            self.data += struct.pack("<3f", *p)
        acc = {"bufferView": len(g["bufferViews"]) - 1, "componentType": 5126, "count": len(pts), "type": "VEC3"}
        if pts:
            acc["min"] = [min(p[k] for p in pts) for k in range(3)]
            acc["max"] = [max(p[k] for p in pts) for k in range(3)]
        g.setdefault("accessors", []).append(acc)
        return len(g["accessors"]) - 1

    def add_vec2(self, pts):
        g = self.g
        g.setdefault("bufferViews", []).append({"buffer": self.idx, "byteOffset": len(self.data), "byteLength": len(pts) * 8, "target": 34962})
        for p in pts:
            self.data += struct.pack("<2f", *p)
        g.setdefault("accessors", []).append({"bufferView": len(g["bufferViews"]) - 1, "componentType": 5126, "count": len(pts), "type": "VEC2"})
        return len(g["accessors"]) - 1

    def add_indices(self, idx):
        g = self.g
        big = bool(idx) and max(idx) > 65535
        fmt, size, ct = ("I", 4, 5125) if big else ("H", 2, 5123)
        g.setdefault("bufferViews", []).append({"buffer": self.idx, "byteOffset": len(self.data), "byteLength": len(idx) * size, "target": 34963})
        self.data += struct.pack(f"<{len(idx)}{fmt}", *idx)
        self.data += b"\x00" * ((4 - len(self.data) % 4) % 4)
        g.setdefault("accessors", []).append({"bufferView": len(g["bufferViews"]) - 1, "componentType": ct, "count": len(idx), "type": "SCALAR"})
        return len(g["accessors"]) - 1

    def finish(self):
        if self.data:
            self.g.setdefault("buffers", []).append({"byteLength": len(self.data),
                                                     "uri": "data:application/octet-stream;base64," + base64.b64encode(bytes(self.data)).decode()})


def read_vec3(g, base, cache, ai):
    a = g["accessors"][ai]
    if a.get("componentType") != 5126 or a.get("type") != "VEC3" or "sparse" in a or "bufferView" not in a:
        raise ValueError(_tr("py.oar2glb.accesseur_0_non_gere_float_vec3", ai))
    bv = g["bufferViews"][a["bufferView"]]
    bi = bv.get("buffer", 0)
    if bi not in cache:
        cache[bi] = read_uri(g["buffers"][bi]["uri"], base)
    data, stride = cache[bi], bv.get("byteStride") or 12
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    return [struct.unpack_from("<3f", data, off + k * stride) for k in range(a["count"])]


def inv3(a):
    c = [[a[1][1] * a[2][2] - a[1][2] * a[2][1], a[0][2] * a[2][1] - a[0][1] * a[2][2], a[0][1] * a[1][2] - a[0][2] * a[1][1]],
         [a[1][2] * a[2][0] - a[1][0] * a[2][2], a[0][0] * a[2][2] - a[0][2] * a[2][0], a[0][2] * a[1][0] - a[0][0] * a[1][2]],
         [a[1][0] * a[2][1] - a[1][1] * a[2][0], a[0][1] * a[2][0] - a[0][0] * a[2][1], a[0][0] * a[1][1] - a[0][1] * a[1][0]]]
    det = a[0][0] * c[0][0] + a[0][1] * c[1][0] + a[0][2] * c[2][0]
    return None if abs(det) < 1e-12 else [[v / det for v in row] for row in c]


def rigged_scale_mode(node, scale):
    # comment convoar a appliqué l'échelle du prim : « nœud » (scale du nœud GLB), « cuite » (dans les sommets) ou « aucune »
    exp = (scale[0], scale[2], scale[1])        # axes glTF
    s = node.get("scale")
    if "matrix" in node:
        s = mat_trs(node["matrix"])[2]
    if s and any(abs(v - 1) > 1e-4 for v in s):
        return _tr("py.oar2glb.nud")
    return "cuite" if any(abs(v - 1) > 1e-4 for v in exp) else _tr("py.oar2glb.aucune")


def union_domain(dom):
    # (min, max) englobant les domaines de position des sous-maillages, ou None
    if not dom:
        return None
    lo = [min(d[0][k] for d in dom) for k in range(3)]
    hi = [max(d[1][k] for d in dom) for k in range(3)]
    return lo, hi


def read_acc(g, base, cache, ai, n):
    a = g["accessors"][ai]
    if a.get("componentType") != 5126 or a.get("type") != f"VEC{n}" or "sparse" in a or "bufferView" not in a:
        raise ValueError(_tr("py.oar2glb.accesseur_0_non_gere", ai))
    bv = g["bufferViews"][a["bufferView"]]
    bi = bv.get("buffer", 0)
    if bi not in cache:
        cache[bi] = read_uri(g["buffers"][bi]["uri"], base)
    stride = bv.get("byteStride") or 4 * n
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    return [struct.unpack_from(f"<{n}f", cache[bi], off + k * stride) for k in range(a["count"])]


def rig_mesh(g, base, cache, part, bsm, ni, raw):
    # Un mesh riggé est reconstruit depuis son .llmesh dans l'OAR (positions, normales, UV, triangles, domaine de position) :
    # la géométrie que convoar écrit pour ces meshes est inutilisable (mêmes étendues et mêmes nombres de sommets pour des
    # animaux différents, échelle cuite inconnue de l'OAR). L'échelle du prim est ignorée ; bind_shape_matrix s'applique.
    # Les matériaux viennent du nœud GLB (face i du mesh = primitive i). -> (mesh, points, "asset") ou message d'erreur
    node = g["nodes"][ni]
    if "mesh" not in node:
        return _tr("py.oar2glb.le_nud_n_a_pas_de")
    geo = llmesh_geometry(raw) if raw else None
    if not geo or not any(geo):
        return _tr("py.oar2glb.geometrie_du_llmesh_illisible")
    lin = [[bsm[0], bsm[4], bsm[8]], [bsm[1], bsm[5], bsm[9]], [bsm[2], bsm[6], bsm[10]]]
    t = bsm[12:15]
    li = inv3(lin)
    if li is None:
        return _tr("py.oar2glb.bind_shape_matrix_non_inversible")
    old = g["meshes"][node["mesh"]]
    oprims = old.get("primitives", [])
    prims, allp, nv = [], [], 0
    for i, sm in enumerate(geo):
        if not sm:
            continue
        pts = []
        for x, y, z in sm["pos"]:
            pts.append([lin[0][0] * x + lin[0][1] * y + lin[0][2] * z + t[0],
                        lin[2][0] * x + lin[2][1] * y + lin[2][2] * z + t[2],
                        -(lin[1][0] * x + lin[1][1] * y + lin[1][2] * z + t[1])])
        pr = {"attributes": {}, "_pts": pts, "_idx": [k for k in sm["tri"] if k < len(pts)]}
        if sm["nor"]:
            ns = []
            for v in sm["nor"]:
                nx, ny, nz = (sum(li[j][k] * v[j] for j in range(3)) for k in range(3))
                ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
                ns.append([nx / ln, nz / ln, -ny / ln])
            pr["_nrm"] = ns
        if sm["uv"]:
            flip = True                      # UV de Second Life : v vers le haut ; glTF : v vers le bas
            if i < len(oprims) and "TEXCOORD_0" in oprims[i].get("attributes", {}):
                try:
                    cu = read_acc(g, base, cache, oprims[i]["attributes"]["TEXCOORD_0"], 2)
                    if len(cu) == len(sm["uv"]):
                        m = min(len(cu), 16)
                        e_raw = sum(abs(cu[k][1] - sm["uv"][k][1]) for k in range(m))
                        e_flip = sum(abs(cu[k][1] - (1 - sm["uv"][k][1])) for k in range(m))
                        flip = e_flip <= e_raw
                except Exception:
                    pass
            pr["_uv"] = [(u, 1.0 - v if flip else v) for u, v in sm["uv"]]
        mat = oprims[i] if i < len(oprims) else (oprims[-1] if oprims else None)
        if mat is not None and "material" in mat:
            pr["material"] = mat["material"]
        prims.append(pr)
        allp += pts
        nv += len(pts)
    if not allp:
        return _tr("py.oar2glb.aucune_geometrie")
    mesh = {k: v for k, v in old.items() if k != "primitives"}
    mesh["primitives"] = prims
    oldn = sum(g["accessors"][pr["attributes"]["POSITION"]]["count"] for pr in oprims if "POSITION" in pr.get("attributes", {}))
    print(_tr("py.oar2glb.rigge_0_reconstruit_depuis_l_oar", part['name'], len(prims), nv, sum(len(p['_idx']) for p in prims) // 3, len(oprims), oldn, fmt3(part['scale'] or [1, 1, 1]), fmt3([math.sqrt(sum(bsm[c * 4 + r] ** 2 for r in range(3))) for c in range(3)])))
    return mesh, allp, "asset"


PLACED = []
PLACED_NODES = set()


def node_aabb(g, tree, i):
    # boîte englobante monde (glTF) d'un nœud d'après les min/max de ses accesseurs POSITION, sans lire les sommets
    n = g["nodes"][i]
    if "mesh" not in n:
        return None
    lo, hi = [1e30] * 3, [-1e30] * 3
    for pr in g["meshes"][n["mesh"]].get("primitives", []):
        a = g["accessors"][pr["attributes"]["POSITION"]] if "POSITION" in pr.get("attributes", {}) else None
        if not a or "min" not in a or "max" not in a:
            continue
        lo = [min(lo[k], a["min"][k]) for k in range(3)]
        hi = [max(hi[k], a["max"][k]) for k in range(3)]
    if lo[0] > hi[0]:
        return None
    w = tree.world(i)
    pts = [[w[r] * x + w[4 + r] * y + w[8 + r] * z + w[12 + r] for r in range(3)] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    return [min(p[k] for p in pts) for k in range(3)], [max(p[k] for p in pts) for k in range(3)]


def report_buried(g):
    # pour chaque animal posé : objets du GLB dont la boîte englobante contient le centre de l'animal (animal enfoui ?)
    tree = Tree(g)
    boxes = {}
    for i, n in enumerate(g["nodes"]):
        if n.get("name", "").startswith("REPERE") or i in PLACED_NODES:
            continue
        b = node_aabb(g, tree, i)
        if b:
            boxes[i] = b
    for name, gx, gy, ground, ext in PLACED:
        c = [gx, ground + ext[2] / 2, -gy]
        inside = sorted(((math.prod(b[1][k] - b[0][k] for k in range(3)), i) for i, b in boxes.items()
                         if all(b[0][k] <= c[k] <= b[1][k] for k in range(3))))
        txt = ", ".join(f"'{g['nodes'][i].get('name', '?')[:30]}' (sommet {boxes[i][1][1]:.1f} m)" for _, i in inside[:3])
        print(_tr("py.oar2glb.controle_0_pieds_a_1_2f", name, ground, c[1]) + (_tr("py.oar2glb.dans_la_boite_de_0_objet", len(inside), txt) if inside else _tr("py.oar2glb.libre_aucune_boite_d_objet_ne")))


def add_beacons(g, ebuf):
    # option --markers : un mât rouge de 15 m à chaque animal posé, pour le retrouver dans le viewer
    g.setdefault("materials", []).append({"name": "repere", "pbrMetallicRoughness": {"baseColorFactor": [1, 0, 0, 1], "metallicFactor": 0},
                                          "emissiveFactor": [1, 0, 0], "doubleSided": True})
    mat = len(g["materials"]) - 1
    h, w = 15.0, 0.15
    pts = [(x, y, z) for x in (-w, w) for y in (0, h) for z in (-w, w)]
    idx = [0, 1, 3, 0, 3, 2, 4, 6, 7, 4, 7, 5, 0, 4, 5, 0, 5, 1, 2, 3, 7, 2, 7, 6, 0, 2, 6, 0, 6, 4, 1, 5, 7, 1, 7, 3]
    pa = ebuf.add_vec3(pts)
    g["bufferViews"].append({"buffer": ebuf.idx, "byteOffset": len(ebuf.data), "byteLength": len(idx) * 2, "target": 34963})
    ebuf.data += struct.pack(f"<{len(idx)}H", *idx)
    ebuf.data += b"\x00\x00" * (len(idx) % 2)
    g["accessors"].append({"bufferView": len(g["bufferViews"]) - 1, "componentType": 5123, "count": len(idx), "type": "SCALAR"})
    g["meshes"].append({"name": "repere", "primitives": [{"attributes": {"POSITION": pa}, "indices": len(g["accessors"]) - 1, "material": mat}]})
    mi = len(g["meshes"]) - 1
    for name, gx, gy, ground, ext in PLACED:
        g["nodes"].append({"name": f"REPERE {name} ({ext[0]:.1f} x {ext[2]:.1f} x {ext[1]:.1f} m)", "mesh": mi, "translation": [gx, ground, -gy]})
        g["scenes"][0]["nodes"].append(len(g["nodes"]) - 1)
    print(_tr("py.oar2glb.reperes_0_mat_s_rouge_s", len(PLACED)))


MAX_ANIMAL, MIN_ANIMAL = 12.0, 0.1       # garde-fou : un animal fait entre 10 cm et 12 m dans sa plus grande dimension


def place_rigged_group(g, base, cache, extra, tree, grp, items):
    # items : [(partie riggée, bind_shape, nœud GLB)] d'UN objet. Les morceaux d'un même animal (chacun avec sa
    # bind_shape_matrix) partagent le même repère : on les déplace ENSEMBLE (même décalage, même rotation), sans
    # jamais les poser séparément. Retourne le nombre de morceaux corrigés.
    built = []
    for part, bsm, ni, raw in items:
        r = rig_mesh(g, base, cache, part, bsm, ni, raw)
        if isinstance(r, str):
            print(_tr("py.oar2glb.rigge_0_1_non_corrige", part['name'], r))
        else:
            built.append((part, ni) + r)
    if not built:
        return 0
    allp = [p for b in built for p in b[3]]
    lo = [min(p[k] for p in allp) for k in range(3)]
    hi = [max(p[k] for p in allp) for k in range(3)]
    root = grp["parts"][0]
    ext = [hi[k] - lo[k] for k in range(3)]
    if max(ext) > MAX_ANIMAL or max(ext) < MIN_ANIMAL:
        print(_tr("py.oar2glb.rigge_0_taille_obtenue_1_2f", root['name'], ext[0], ext[2], ext[1], MIN_ANIMAL, MAX_ANIMAL))
        return 0
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2          # centré à l'horizontale sur la racine
    gx, gy, gz = root["gpos"]
    q = root["rot"] or [0, 0, 0, 1]
    pq = built[0][0]["rot"] if built[0][0] is not root and built[0][0]["rot"] else [0, 0, 0, 1]
    a, b = q, pq                                                 # rotation monde du 1er morceau = racine x enfant
    q = [a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1], a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0],
         a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3], a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2]]
    rot = [q[0], q[2], -q[1], q[3]]                              # repère glTF, appliquée à tous les morceaux
    corners = [rot_vec(rot, [x, y, z]) for x in (lo[0] - cx, hi[0] - cx) for y in (lo[1], hi[1]) for z in (lo[2] - cz, hi[2] - cz)]
    yoff = min(c[1] for c in corners)
    # sol : le dessous de la boîte racine (prim simple posé au sol) ; racine elle-même riggée : sa position
    if root["mesh"] is None and root["scale"]:
        ground, src = gz - root["scale"][2] / 2, _tr("py.oar2glb.dessous_de_la_boite_racine")
    else:
        ground, src = gz, _tr("py.oar2glb.altitude_de_la_racine")
    for part, ni, mesh, pts, mode in built:
        for pr in mesh["primitives"]:
            if "_pts" in pr:
                pr["attributes"]["POSITION"] = extra.add_vec3([[p[0] - cx, p[1], p[2] - cz] for p in pr.pop("_pts")])
            if "_nrm" in pr:
                pr["attributes"]["NORMAL"] = extra.add_vec3(pr.pop("_nrm"))
            if "_uv" in pr:
                pr["attributes"]["TEXCOORD_0"] = extra.add_vec2(pr.pop("_uv"))
            if "_idx" in pr:
                pr["indices"] = extra.add_indices(pr.pop("_idx"))
        g["meshes"].append(mesh)
        node = g["nodes"][ni]
        PLACED_NODES.add(ni)
        node["mesh"] = len(g["meshes"]) - 1
        w = quat_mat(rot, t=[gx, ground - yoff, -gy])
        if ni in tree.parent:
            inv = mat_inv(tree.world(tree.parent[ni]))
            if inv:
                w = mat_mul(inv, w)
        tr, qq, _ = mat_trs(w)
        node.pop("matrix", None)
        node.pop("scale", None)
        node["translation"], node["rotation"] = tr, qq
        tree._w.clear()
    ext = [hi[k] - lo[k] for k in range(3)]
    PLACED.append((root["name"], gx, gy, ground, ext))
    print(_tr("py.oar2glb.rigge_0_1_morceau_x_echelle", root['name'], len(built), built[0][4], ext[0], ext[2], ext[1], gx, gy, ground, src))
    return len(built)


def repair(g, base, scan, keep_invisible, reperes=False):
    match = match_nodes(g, scan)
    extra, cache, tree = ExtraBuffer(g), {}, Tree(g)
    n_rig = n_inv = 0
    for grp in scan["groups"]:
        items = []
        for p in grp["parts"]:
            sk = scan["skins"].get(p["mesh"]) if p["mesh"] else None
            if not sk or not sk["bsm"]:
                if sk and sk["err"]:
                    print(_tr("py.oar2glb.rigge_0_1_ignore", p['name'], sk['err']))
                continue
            if p["uuid"] not in match:
                print(_tr("py.oar2glb.rigge_0_1_nud_glb_introuvable", p['name'], p['uuid']))
                continue
            items.append((p, sk["bsm"], match[p["uuid"]][0], sk.get("raw")))
        if items:
            n_rig += place_rigged_group(g, base, cache, extra, tree, grp, items)
    if reperes and PLACED:
        add_beacons(g, extra)
    extra.finish()
    if not keep_invisible:
        n_inv = remove_invisible(g, scan, match)
    if PLACED:
        report_buried(g)
    print(_tr("py.oar2glb.correctif_0_mesh_es_rigge_s", n_rig, n_inv))
    return n_rig, n_inv


# ---------- --diag ----------
def read_glb_json(path):
    path = Path(path)
    if path.suffix.lower() == ".gltf":
        return load_gltf(path)
    d = path.read_bytes()
    if d[:4] != b"glTF":
        sys.exit(_tr("py.oar2glb.erreur_0_n_est_pas_un", path))
    ln, kind = struct.unpack_from("<I4s", d, 12)
    return json.loads(d[20:20 + ln].decode("utf-8"))


def fmt3(v):
    return "(" + ", ".join(f"{x:.3g}" for x in v) + ")" if v else "?"


def diag(scan, g, glb_label, base=None):
    match = match_nodes(g, scan) if g else {}
    parts = [(grp, p) for grp in scan["groups"] for p in grp["parts"]]
    print(_tr("py.oar2glb.diag_0_objet_s_1_partie", len(scan['groups']), len(parts), 'oui' if scan['terrain'] else 'non', 'GLB ' + glb_label if g else _tr('py.oar2glb.pas_de_glb_correspondance_non_evaluee')))
    nr = ni = nm = 0
    boxes = rig_box_roots(scan)
    for k, (grp, p) in enumerate(parts, 1):
        sk = scan["skins"].get(p["mesh"]) if p["mesh"] else None
        if sk and sk["bsm"]:
            rig, nr = "oui", nr + 1
        elif sk:
            rig = "oui (" + (sk["err"] or _tr("py.oar2glb.sans_bind_shape_matrix")) + ")"
        else:
            rig = "non" if p["mesh"] else _tr("py.oar2glb.non_pas_un_mesh")
        bsm = sk["bsm"] if sk and sk["bsm"] else None
        bs = fmt3([math.sqrt(sum(bsm[c * 4 + r] ** 2 for r in range(3))) for c in range(3)]) if bsm else "-"
        ni += p["invisible"]
        if g:
            if p["uuid"] in match:
                n, how = match[p["uuid"]]
                nm += 1
                node = g["nodes"][n]
                sc = node.get("scale") or (mat_trs(node["matrix"])[2] if "matrix" in node else None)
                gl = _tr("py.oar2glb.nud_0_1_2_echelle_du", n, node.get('name', ''), how, fmt3(sc) if sc else 'aucune') + (_tr("py.oar2glb.echelle_du_prim_appliquee_0", rigged_scale_mode(node, p['scale'] or [1, 1, 1])) if bsm else "")
            else:
                gl = _tr("py.oar2glb.nud_introuvable")
        else:
            gl = "-"
        racine = "racine" if p is grp["parts"][0] else "enfant"
        print(_tr("py.oar2glb.0_5d_1_2_3_rigge", k, p['name'] or '(sans nom)', p['uuid'], racine, rig, fmt3(p['scale']), bs, 'oui' if p['invisible'] else 'non', 'oui' if p['uuid'] in boxes else 'non', gl))
        if bsm or p["uuid"] in boxes or p["invisible"]:
            gz = terrain_height(scan["terrain"], p["gpos"][0], p["gpos"][1])
            print(_tr("py.oar2glb.diag_pos", fmt3(p['gpos']), ('%.2f m' % gz) if gz is not None else _tr("py.oar2glb.unknown"), p['tex']) + (_tr("py.oar2glb.translation_bind_shape_0", fmt3(bsm[12:15])) if bsm else ""))
            if bsm:
                sk = scan["skins"][p["mesh"]]
                print(_tr("py.oar2glb.bind_shape_matrix_0", [round(v, 4) for v in bsm]))
                ud = union_domain(sk["dom"])
                print(_tr("py.oar2glb.domaine_de_position_du_mesh_0", len(sk['dom'])) + (f"{fmt3(ud[0])} .. {fmt3(ud[1])}" if ud else _tr("py.oar2glb.unreadable")))
                if g and base is not None and p["uuid"] in match and "mesh" in g["nodes"][match[p["uuid"]][0]]:
                    try:
                        pts, cc = [], {}
                        for pr in g["meshes"][g["nodes"][match[p["uuid"]][0]]["mesh"]].get("primitives", []):
                            pts += read_vec3(g, base, cc, pr["attributes"]["POSITION"])
                        lo_ = [min(q[k] for q in pts) for k in range(3)]
                        hi_ = [max(q[k] for q in pts) for k in range(3)]
                        pa = g["meshes"][g["nodes"][match[p["uuid"]][0]]["mesh"]]["primitives"][0]["attributes"]["POSITION"]
                        ac = g["accessors"][pa]
                        bv = g["bufferViews"][ac["bufferView"]]
                        bf = g["buffers"][bv.get("buffer", 0)]
                        print(_tr("py.oar2glb.accesseur_position_0_bufferview_1_buffer", ac, bv, str(bf.get('uri'))[:60], bf.get('byteLength'), pts[:3]))
                        print(_tr("py.oar2glb.sommets_du_glb_axes_opensim_x", fmt3([lo_[0], -hi_[2], lo_[1]]), fmt3([hi_[0], -lo_[2], hi_[1]]), fmt3([hi_[0] - lo_[0], hi_[2] - lo_[2], hi_[1] - lo_[1]]), len(pts)))
                    except Exception as e:
                        print(_tr("py.oar2glb.sommets_du_glb_illisibles_0", e))
            if g and p["uuid"] in match:
                node = g["nodes"][match[p["uuid"]][0]]
                if "mesh" in node:
                    for pr in g["meshes"][node["mesh"]].get("primitives", [])[:3]:
                        m = g["materials"][pr["material"]] if "material" in pr else {}
                        ti = ((m.get("pbrMetallicRoughness") or {}).get("baseColorTexture") or {}).get("index")
                        im = ""
                        if ti is not None and ti < len(g.get("textures", [])):
                            src = g["textures"][ti].get("source")
                            if src is not None and src < len(g.get("images", [])):
                                im = str(g["images"][src].get("uri") or g["images"][src].get("name") or "")[:60]
                        print(_tr("py.oar2glb.materiau_glb_0_r_couleur_1", m.get('name'), (m.get('pbrMetallicRoughness') or {}).get('baseColorFactor'), m.get('alphaMode', 'OPAQUE'), im or '-'))
    print(_tr("py.oar2glb.diag_rigges_0_transparents_1_boites", nr, ni, len(boxes), nm, len(parts)))
    if g:
        cache, nv = {}, 0
        for n in g.get("nodes", []):
            nv += node_all_invisible(g, n, cache)
        print(_tr("py.oar2glb.diag_nuds_glb_dont_tous_les", nv))
        print(_tr("py.oar2glb.diag_uuid_lisibles_dans_les_nuds", len(node_uuids(g))))
        for i, n in enumerate(g.get("nodes", [])[:6]):
            print(_tr("py.oar2glb.node_0_nom_1_r_extras", i, n.get('name'), json.dumps(n.get('extras'))[:100], sorted(k for k in n if k not in ('name', 'extras'))))


# ---------- 4. hors région ----------
def drop_far(g, vmax, size):
    # hors région : au-delà de la taille de la région (+10 m) en horizontal, ou de --max en hauteur
    sx, sy = size
    n = 0
    for sc in g.get("scenes", []):
        keep = []
        for i in sc.get("nodes", []):
            p = node_pos(g["nodes"][i])
            if g["nodes"][i].get("extras", {}).get("terrain"):
                keep.append(i)         # patches de terrain : jamais retirés
            elif not (-10 <= p[0] <= sx + 10 and -10 <= -p[2] <= sy + 10 and abs(p[1]) <= vmax):
                print(_tr("py.oar2glb.hors_region_node_0_1_a", i, g['nodes'][i].get('name', '?'), [round(c, 1) for c in p]))
                n += 1
            else:
                keep.append(i)
        sc["nodes"] = keep
    pts = [node_pos(g["nodes"][i]) for sc in g.get("scenes", []) for i in sc["nodes"]]
    if pts:
        lo = [round(min(p[k] for p in pts), 1) for k in range(3)]
        hi = [round(max(p[k] for p in pts), 1) for k in range(3)]
        print(_tr("py.oar2glb.etendue_0_objets_de_1_a", len(pts), lo, hi))
    return n


# ---------- 5. GLB ----------
GREY_PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNoAAAAggCBd81ytgAAAABJRU5ErkJggg==")


def find_file(base, name):
    names = [name]
    # convoar écrit parfois le hash en signé et l'annonce en non signé 64 bits (18446744071783355852 = -1926195764)
    m = re.match(r"^(\d{19,20})(_.*)$", name)
    if m and int(m.group(1)) >= 2**63:
        v = int(m.group(1)) - 2**64
        names += [f"{v}{m.group(2)}", f"{v % 2**32}{m.group(2)}"]
    for n in names:
        if (base / n).exists():
            return base / n
    for n in names:
        for root in (base, base.parent):
            hit = next(root.rglob(n), None)
            if hit:
                return hit
    return None


def read_uri(uri, base, image=False):
    if uri.startswith("data:"):
        return base64.b64decode(uri.split(",", 1)[1])
    from urllib.parse import unquote
    name = unquote(uri)
    hit = find_file(base, name)
    if hit:
        if hit.name != Path(name).name or hit.parent != (base / name).parent:
            print(_tr("py.oar2glb.glb_0_1", name, hit.name))
        return hit.read_bytes()
    if image:
        MISSING.append(name)
        return GREY_PNG
    files = sorted(base.rglob("*"))
    bufs = [x for x in files if x.suffix.lower() == ".buf"]
    sys.exit(_tr("py.oar2glb.erreur_0_introuvable_annonce_par_le", name, base, len(files), len(bufs))
             + ", ".join(f"{x.name} ({x.stat().st_size} o)" for x in bufs[:10])
             + _tr("py.oar2glb.espace_libre_sur_0_1_1f", base.anchor, shutil.disk_usage(base).free / 2**30))


MISSING = []


def report_missing(base, total):
    if not MISSING:
        return
    from collections import Counter
    files = [f for f in Path(base).rglob("*") if f.is_file()]
    ext = Counter(f.suffix.lower() for f in files)
    print(_tr("py.oar2glb.glb_0_texture_s_absente_s", len(MISSING), total) + ", ".join(MISSING[:3]))
    print(_tr("py.oar2glb.glb_0_contient_1_fichier_s", base, len(files)) + ", ".join(f"{k or _tr('py.oar2glb.sans_extension')} {v}" for k, v in ext.most_common(8)))
    print(_tr("py.oar2glb.glb_fichiers_images_presents_exemples") + ", ".join(f.name for f in files if f.suffix.lower() in (".jpg", ".png"))[:300])


def pad4(b, fill=b"\x00"):
    return b + fill * ((4 - len(b) % 4) % 4)


def pack_glb(g, base, out):
    blob, offs = bytearray(), []
    for b in g.get("buffers", []):
        offs.append(len(blob))
        blob += pad4(read_uri(b["uri"], base))
    for bv in g.get("bufferViews", []):
        bv["byteOffset"] = bv.get("byteOffset", 0) + offs[bv.get("buffer", 0)]
        bv["buffer"] = 0
    g.setdefault("bufferViews", [])
    for img in g.get("images", []):
        if "uri" not in img:
            continue
        data = read_uri(img["uri"], base, image=True)
        img["mimeType"] = "image/png" if data[:4] == b"\x89PNG" else "image/jpeg"
        g["bufferViews"].append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data)})
        img["bufferView"] = len(g["bufferViews"]) - 1
        del img["uri"]
        blob += pad4(data)
    g["buffers"] = [{"byteLength": len(blob)}]
    js = pad4(json.dumps(g, separators=(",", ":")).encode("utf-8"), b" ")
    total = 12 + 8 + len(js) + 8 + len(blob)
    with open(out, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total))
        f.write(struct.pack("<I4s", len(js), b"JSON") + js)
        f.write(struct.pack("<I4s", len(blob), b"BIN\x00") + blob)
    return total


# ---------- 6. terrain complet (régions de plus de 256 m) ----------
# convoar ne produit qu'un morceau de terrain sur les grandes régions : on le remplace par des carrés (patches)
# construits depuis la carte de hauteurs de l'OAR (terrains/*.r32, 1 échantillon par mètre).
TERRAIN_PATCH = 64            # côté d'un patch en mètres (--terrain-patch)
TERRAIN_COUVERT_MIN = 0.95    # le terrain de convoar est gardé s'il couvre au moins cette part de la carte
EAU_DEFAUT = 20.0             # WaterHeight par défaut d'OpenSim
LECTURE = 8 * 1024 * 1024     # taille des lectures du GLB en mode --terrain-only
PENTE_ROCHE = (32.0, 38.0)    # degrés : la roche apparaît à 32, pleine à 38 (environ 35)
# palette (rouge, vert, bleu) : documentée dans docs/fr/MANUEL.md § 15
SABLE_SEC, SABLE_HUMIDE = (214, 196, 142), (166, 150, 104)
HERBE_BASSE, HERBE_HAUTE, ROCHE = (98, 146, 66), (132, 140, 78), (122, 120, 116)


def mix(a, b, t):
    t = min(max(t, 0.0), 1.0)
    return [a[k] + (b[k] - a[k]) * t for k in range(3)]


def couleur_terrain(h, pente, eau):
    # h : altitude (m), pente : degrés, eau : niveau d'eau (m) -> (r, v, b) entiers
    alt = h - eau
    if alt <= 0:
        c = list(SABLE_HUMIDE)                                           # sous l'eau : sable humide
    else:
        herbe = mix(HERBE_BASSE, HERBE_HAUTE, (alt - 4.0) / 76.0)        # dégradé léger de 4 m à 80 m au-dessus de l'eau
        c = mix(SABLE_SEC, herbe, (alt - 1.0) / 3.0)                     # sable jusqu'à 1 m, herbe à partir de 4 m
    c = mix(c, ROCHE, (pente - PENTE_ROCHE[0]) / (PENTE_ROCHE[1] - PENTE_ROCHE[0]))
    return int(c[0] + 0.5), int(c[1] + 0.5), int(c[2] + 0.5)


def terrain_patch_data(h, n, x0, y0, x1, y1, eau):
    # patch couvrant les échantillons x0..x1, y0..y1 (bornes comprises) ; repère glTF : X = x, hauteur = h, Z = -y.
    # Normales et pente par différences centrées sur TOUTE la carte : les bords partagés sont identiques des deux côtés.
    nx, ny = x1 - x0 + 1, y1 - y0 + 1
    pos, nor, col = [], [], bytearray()
    lo, hi = [math.inf] * 3, [-math.inf] * 3
    for y in range(y0, y1 + 1):
        yl, yh = max(y - 1, 0), min(y + 1, n - 1)
        r0, rl, rh = y * n, yl * n, yh * n
        for x in range(x0, x1 + 1):
            xl, xh = max(x - 1, 0), min(x + 1, n - 1)
            v = h[r0 + x]
            hx = (h[r0 + xh] - h[r0 + xl]) / (xh - xl)
            hy = (h[rh + x] - h[rl + x]) / (yh - yl)
            g = math.sqrt(hx * hx + hy * hy)
            ln = math.sqrt(g * g + 1.0)
            pos += (x, v, -y)
            nor += (-hx / ln, 1.0 / ln, hy / ln)
            col += bytes(couleur_terrain(v, math.degrees(math.atan(g)), eau)) + b"\xff"
            if v < lo[1]:
                lo[1] = v
            if v > hi[1]:
                hi[1] = v
    lo[0], hi[0], lo[2], hi[2] = x0, x1, -y1, -y0
    idx = []
    for cy in range(ny - 1):
        for cx in range(nx - 1):
            a = cy * nx + cx
            b, c = a + 1, a + nx
            idx += (a, b, c, b, c + 1, c)            # triangles tournés vers le haut (+Y)
    return {"nv": nx * ny, "pos": struct.pack(f"<{len(pos)}f", *pos), "nor": struct.pack(f"<{len(nor)}f", *nor),
            "col": bytes(col), "idx": struct.pack(f"<{len(idx)}H", *idx), "ni": len(idx), "min": lo, "max": hi}


def terrain_donnees(terrain, eau, P):
    # tous les patches : tampon binaire + vues + accesseurs + meshes + nœuds, indices RELATIFS (voir terrain_ajouter)
    n, h = terrain
    blob, views, accs, meshes, nodes = bytearray(), [], [], [], []
    def vue(data, target):
        views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data), "target": target})
        blob.extend(data)
        blob.extend(b"\x00" * ((4 - len(blob) % 4) % 4))
        return len(views) - 1
    nv = 0
    for j, y0 in enumerate(range(0, n - 1, P)):
        for i, x0 in enumerate(range(0, n - 1, P)):
            d = terrain_patch_data(h, n, x0, y0, min(x0 + P, n - 1), min(y0 + P, n - 1), eau)
            nv += d["nv"]
            a0 = len(accs)
            accs.append({"bufferView": vue(d["pos"], 34962), "componentType": 5126, "count": d["nv"], "type": "VEC3", "min": d["min"], "max": d["max"]})
            accs.append({"bufferView": vue(d["nor"], 34962), "componentType": 5126, "count": d["nv"], "type": "VEC3"})
            accs.append({"bufferView": vue(d["col"], 34962), "componentType": 5121, "normalized": True, "count": d["nv"], "type": "VEC4"})
            accs.append({"bufferView": vue(d["idx"], 34963), "componentType": 5123, "count": d["ni"], "type": "SCALAR"})
            nom = f"Terrain {i},{j}"
            meshes.append({"name": nom, "primitives": [{"attributes": {"POSITION": a0, "NORMAL": a0 + 1, "COLOR_0": a0 + 2},
                                                        "indices": a0 + 3, "material": 0, "mode": 4}]})
            nodes.append({"name": nom, "mesh": len(meshes) - 1, "extras": {"terrain": True}})
    return {"blob": blob, "views": views, "accessors": accs, "meshes": meshes, "nodes": nodes, "vertices": nv}


def terrain_ajouter(g, td, buffer_index, base):
    # ajoute les patches au glTF : tampon n° buffer_index, données placées à partir de l'octet base ; retourne les nœuds ajoutés
    g.setdefault("materials", []).append({"name": "terrain", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 1},
                                          "doubleSided": False})
    mat = len(g["materials"]) - 1
    vo, ao, mo = len(g.setdefault("bufferViews", [])), len(g.setdefault("accessors", [])), len(g.setdefault("meshes", []))
    for v in td["views"]:
        g["bufferViews"].append({**v, "buffer": buffer_index, "byteOffset": v["byteOffset"] + base})
    for a in td["accessors"]:
        g["accessors"].append({**a, "bufferView": a["bufferView"] + vo})
    for m in td["meshes"]:
        pr = m["primitives"][0]
        g["meshes"].append({"name": m["name"], "primitives": [{**pr, "attributes": {k: v + ao for k, v in pr["attributes"].items()},
                                                               "indices": pr["indices"] + ao, "material": mat}]})
    first = len(g.setdefault("nodes", []))
    for nd in td["nodes"]:
        g["nodes"].append({**nd, "mesh": nd["mesh"] + mo})
    if not g.get("scenes"):
        g["scenes"] = [{"nodes": []}]
    g["scenes"][g.get("scene", 0)].setdefault("nodes", []).extend(range(first, len(g["nodes"])))
    return list(range(first, len(g["nodes"])))


def terrain_boite(g, tree, i):
    # boîte monde (glTF) du mesh du nœud i d'après les min/max de ses accesseurs POSITION ; None si inconnue
    pts = []
    for pr in g["meshes"][g["nodes"][i]["mesh"]].get("primitives", []):
        a = g["accessors"][pr["attributes"]["POSITION"]]
        if "min" not in a or "max" not in a:
            return None
        pts += [(x, y, z) for x in (a["min"][0], a["max"][0]) for y in (a["min"][1], a["max"][1]) for z in (a["min"][2], a["max"][2])]
    if not pts:
        return None
    w = tree.world(i)
    pw = [[w[r] * p[0] + w[4 + r] * p[1] + w[8 + r] * p[2] + w[12 + r] for r in range(3)] for p in pts]
    return [min(q[k] for q in pw) for k in range(3)], [max(q[k] for q in pw) for k in range(3)]


def terrain_decision(g, terrain, mode):
    # (action, nœuds convoar à retirer, message) ; action : "ajouter" ou "rien"
    n = terrain[0]
    if any(x.get("name", "").startswith("Terrain ") and x.get("extras", {}).get("terrain") for x in g.get("nodes", [])):
        return _tr("py.oar2glb.rien"), [], _tr("py.oar2glb.les_patches_de_terrain_sont_deja")
    tree = Tree(g)
    anciens = [i for i, x in enumerate(g.get("nodes", [])) if x.get("name") == "Terrain" and "mesh" in x]
    if mode == "yes":
        return "ajouter", anciens, _tr("py.oar2glb.force_terrain_oui")
    if not anciens:
        return _tr("py.oar2glb.rien"), [], _tr("py.oar2glb.pas_de_nud_terrain_de_convoar")
    surf, couvert = (n - 1.0) ** 2, 0.0
    for i in anciens:
        b = terrain_boite(g, tree, i)
        if b is None:
            return _tr("py.oar2glb.rien"), [], _tr("py.oar2glb.nud_terrain_sans_min_max_d")
        (x0, _, z0), (x1, _, z1) = b
        couvert += max(0.0, min(x1, n - 1.0) - max(x0, 0.0)) * max(0.0, min(z1, 0.0) - max(z0, -(n - 1.0)))
    part = couvert / surf
    if part >= TERRAIN_COUVERT_MIN:
        return _tr("py.oar2glb.rien"), [], _tr("py.oar2glb.terrain_de_convoar_complet_couvre_0", part * 100)
    return "ajouter", anciens, _tr("py.oar2glb.terrain_de_convoar_incomplet_couvre_0", part * 100)


def terrain_eau(scan):
    w = scan.get("water")
    return (w[0], _tr("py.oar2glb.lu_dans") + w[1]) if w else (EAU_DEFAUT, _tr("py.oar2glb.defaut_d_opensim_aucun_waterheight_dans"))


def terrain_resume(terrain, scan, P, td, t0):
    n = terrain[0]
    eau = terrain_eau(scan)
    print(_tr("py.oar2glb.terrain_carte_0_x_1_echantillons", n, n, eau[0], eau[1], len(td['nodes']), P, td['vertices'], len(td['blob']) / 1048576, time.time() - t0))


def terrain_prepare(scan, mode):
    # contrôles communs ; retourne la carte ou None (message déjà écrit)
    if mode == "no":
        print(_tr("py.oar2glb.terrain_desactive_terrain_non"))
        return None
    t = scan.get("terrain")
    if not t or t[0] < 2:
        print(_tr("py.oar2glb.terrain_cet_oar_n_a_pas"))
        return None
    if t[0] != scan["size"][0] or t[0] != scan["size"][1]:
        print(_tr("py.oar2glb.terrain_attention_carte_de_0_x", t[0], t[0], scan['size'][0], scan['size'][1]))
    return t


def terrain_pipeline(g, scan, mode, P):
    # chaîne convoar : remplace le terrain incomplet ; les données vont dans un nouveau tampon (data: URI, lu par pack_glb)
    t0 = time.time()
    terrain = terrain_prepare(scan, mode)
    if not terrain:
        return
    action, anciens, msg = terrain_decision(g, terrain, mode)
    print(_tr("py.oar2glb.terrain_0", msg))
    if action == "rien":
        return
    td = terrain_donnees(terrain, terrain_eau(scan)[0], P)
    for i in anciens:
        remove_node(g, i)
    bi = len(g.setdefault("buffers", []))
    terrain_ajouter(g, td, bi, 0)
    g["buffers"].append({"byteLength": len(td["blob"]), "uri": "data:application/octet-stream;base64," + base64.b64encode(bytes(td["blob"])).decode()})
    terrain_resume(terrain, scan, P, td, t0)
    if anciens:
        print(_tr("py.oar2glb.terrain_0_nud_s_terrain_de", len(anciens)))


def terrain_seul(glb, scan, out, mode, P, chunk=LECTURE):
    """Ajoute les patches à un GLB existant sans le charger : en-tête JSON réécrit, chunk binaire recopié par morceaux,
    nouveaux tampons ajoutés à la fin. Retourne un dict de mesures, ou None si rien n'est écrit."""
    t0 = time.time()
    terrain = terrain_prepare(scan, mode)
    if not terrain:
        return None
    mesures = {"lu": 0, "lecture_max": 0}
    with open(glb, "rb") as f:
        def lire(k):
            d = f.read(k)
            mesures["lu"] += len(d)
            mesures["lecture_max"] = max(mesures["lecture_max"], len(d))
            return d
        taille = os.fstat(f.fileno()).st_size
        mag, ver, _ = struct.unpack("<4sII", lire(12))
        if mag != b"glTF" or ver != 2:
            sys.exit(_tr("py.oar2glb.erreur_0_n_est_pas_un_2", glb))
        chunks, pos = [], 12
        while pos + 8 <= taille:
            f.seek(pos)
            ln, kind = struct.unpack("<I4s", lire(8))
            chunks.append((kind, pos + 8, ln))
            pos += 8 + ln + (-ln % 4)
        if not chunks or chunks[0][0] != b"JSON":
            sys.exit(_tr("py.oar2glb.erreur_0_le_premier_chunk_n", glb))
        f.seek(chunks[0][1])
        g = json.loads(lire(chunks[0][2]).decode("utf-8"))
        binc = next((c for c in chunks if c[0] == b"BIN\x00"), None)
        autres = [c for c in chunks[1:] if c is not binc]
        action, anciens, msg = terrain_decision(g, terrain, mode)
        print(_tr("py.oar2glb.terrain_0", msg))
        if action == "rien":
            return None
        td = terrain_donnees(terrain, terrain_eau(scan)[0], P)
        for i in anciens:
            remove_node(g, i)
        bin_len = binc[2] if binc else 0
        base = bin_len + (-bin_len % 4)
        if binc and (not g.get("buffers") or "uri" in g["buffers"][0]):
            sys.exit(_tr("py.oar2glb.erreur_0_le_tampon_0_n", glb))
        if not g.get("buffers"):
            g["buffers"] = [{"byteLength": 0}]
        terrain_ajouter(g, td, 0, base)
        bin_total = base + len(td["blob"])
        g["buffers"][0]["byteLength"] = bin_total
        js = pad4(json.dumps(g, separators=(",", ":")).encode("utf-8"), b" ")
        total = 12 + 8 + len(js) + 8 + bin_total + sum(8 + c[2] + (-c[2] % 4) for c in autres)
        part = Path(str(out) + ".part")
        try:
            with open(part, "wb") as o:
                o.write(struct.pack("<4sII", b"glTF", 2, total))
                o.write(struct.pack("<I4s", len(js), b"JSON") + js)
                o.write(struct.pack("<I4s", bin_total, b"BIN\x00"))
                def copier(debut, longueur):
                    f.seek(debut)
                    while longueur > 0:
                        d = lire(min(chunk, longueur))
                        if not d:
                            sys.exit(_tr("py.oar2glb.erreur_0_tronque", glb))
                        o.write(d)
                        longueur -= len(d)
                if binc:
                    copier(binc[1], bin_len)
                o.write(b"\x00" * (base - bin_len))
                o.write(bytes(td["blob"]))
                for kind, debut, ln in autres:
                    o.write(struct.pack("<I4s", ln, kind))
                    copier(debut, ln)
                    o.write(b"\x00" * (-ln % 4))
            os.replace(part, out)
        finally:
            part.unlink(missing_ok=True)
    terrain_resume(terrain, scan, P, td, t0)
    print(_tr("py.oar2glb.terrain_0_nud_s_terrain_retire", len(anciens), mesures['lu'] / 1048576, chunk // 1024))
    mesures.update(patches=len(td["nodes"]), sommets=td["vertices"], ajoutes=len(td["blob"]), retires=len(anciens))
    return mesures


def main():
    ap = argparse.ArgumentParser(description=_tr("py.oar2glb.desc", VERSION), epilog=_tr("py.oar2glb.epilog"), formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False)
    i18n_add_common(ap)
    ap.add_argument("--version", action="version", version=f"oar2glb {VERSION}", help=_tr("py.common.version"))
    ap.add_argument("oar", help=_tr("py.oar2glb.help.oar"))
    ap.add_argument("--reencode", action="store_true", help=_tr("py.oar2glb.reencoder_les_textures_j2k_avant_convoar"))
    ap.add_argument("--max", type=float, default=600.0, help=_tr("py.oar2glb.hauteur_max_m_d_un_objet"))
    ap.add_argument("--convoar", default=shutil.which("convoar") or DEFAULT_CONVOAR, help=_tr("py.oar2glb.help.convoar"))
    ap.add_argument("--keep", action="store_true", help=_tr("py.oar2glb.garder_les_fichiers_intermediaires"))
    ap.add_argument("--keep-invisible", action="store_true", help=_tr("py.oar2glb.garder_les_prims_entierement_transparents_re"))
    ap.add_argument("--markers", dest="reperes", action="store_true", help=_tr("py.oar2glb.ajouter_un_mat_rouge_de_15"))
    ap.add_argument("--diag", action="store_true", help=_tr("py.oar2glb.ne_rien_modifier_lister_les_objets"))
    ap.add_argument("--glb", help=_tr("py.oar2glb.avec_diag_glb_ou_gltf_a"))
    ap.add_argument("--nopause", action="store_true", help=_tr("py.oar2glb.ne_pas_attendre_entree_a_la"))
    ap.add_argument("--terrain", type=lambda v: {"oui": "yes", "non": "no"}.get(v, v), choices=("auto", "yes", "no"), default="auto",
                    help=_tr("py.oar2glb.terrain_complet_depuis_la_carte_de"))
    ap.add_argument("--terrain-patch", type=int, default=TERRAIN_PATCH, help=_tr("py.oar2glb.cote_d_un_patch_de_terrain", TERRAIN_PATCH))
    ap.add_argument("--terrain-only", dest="terrain_seul", metavar="GLB", help=_tr("py.oar2glb.ne_pas_lancer_convoar_ajouter_le"))
    ap.add_argument("--output", metavar="OUTPUT", dest="sortie", help=_tr("py.oar2glb.avec_terrain_seul_fichier_glb_de"))
    a = ap.parse_args()
    if not 2 <= a.terrain_patch <= 255:
        sys.exit(_tr("py.oar2glb.erreur_terrain_patch_doit_etre_compris"))

    oar = Path(a.oar).resolve()
    if not oar.exists():
        sys.exit(_tr("py.oar2glb.erreur_0_introuvable", oar))
    if a.terrain_seul:
        glb = Path(a.terrain_seul).resolve()
        if not glb.is_file():
            sys.exit(_tr("py.oar2glb.erreur_0_introuvable", glb))
        out = Path(a.sortie).resolve() if a.sortie else glb.with_name(glb.stem + "-terrain.glb")
        if out == glb:
            sys.exit(_tr("py.oar2glb.erreur_la_sortie_ne_peut_pas"))
        r = terrain_seul(glb, oar_scan(oar, terrain_seul=True), out, a.terrain, a.terrain_patch)
        print(f"[OK] {out}" if r else _tr("py.oar2glb.terrain_aucun_fichier_ecrit"))
        return
    if a.diag:
        scan = oar_scan(oar)
        auto = sorted((oar.parent / (oar.stem + "-GLTF")).glob("*.gltf"), key=lambda q: q.stat().st_mtime)
        glb = Path(a.glb) if a.glb else (auto[-1] if auto else oar.with_suffix(".glb"))
        diag(scan, read_glb_json(glb) if glb.exists() else None, glb.name, glb.parent if glb.suffix.lower() == ".gltf" else None)
        return
    if not Path(a.convoar).exists():
        sys.exit(_tr("py.oar2glb.erreur_convoar_introuvable_0_utilise_convoar", a.convoar))
    scan = oar_scan(oar)
    size, objs = oar_info(scan)
    src, tmp_oar = oar, None
    if a.reencode:
        tmp_oar = oar.with_name(oar.stem + "-reenc.oar")
        reencode_oar(oar, tmp_oar)
        src = tmp_oar
    out = oar.with_suffix(".glb")
    if out.exists():
        out.unlink()   # pas d'ancien GLB qui ferait croire à un succès si la suite échoue
    outdir = oar.parent / (oar.stem + "-GLTF")
    if outdir.exists():
        shutil.rmtree(outdir)

    run_convoar(a.convoar, src, outdir)
    for essai in range(1, MAX_RETRY + 1):
        time.sleep(3)                      # laisse finir les écritures de fichiers
        miss = missing_images(outdir)
        if not miss:
            break
        print(_tr("py.oar2glb.convoar_0_image_s_annoncee_s", len(miss), ', '.join(miss[:2]), essai, MAX_RETRY))
        old = outdir.with_name(outdir.name + f"-essai{essai}")
        shutil.rmtree(old, ignore_errors=True)
        outdir.rename(old)
        run_convoar(a.convoar, src, outdir)
        n_rec = 0
        for f in old.rglob("*"):
            if f.is_file() and f.suffix.lower() in (".jpg", ".png", ".gif", ".bmp"):
                dst = outdir / f.relative_to(old)
                if not dst.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dst)
                    n_rec += 1
        print(_tr("py.oar2glb.convoar_0_image_s_recuperee_s", n_rec))
        if not a.keep:
            shutil.rmtree(old, ignore_errors=True)

    gltfs = sorted(outdir.glob("*.gltf"), key=lambda p: p.stat().st_mtime)
    if not gltfs:
        sys.exit(_tr("py.oar2glb.erreur_aucun_gltf_produit_dans_0", outdir))
    g = load_gltf(gltfs[-1])
    check(g)
    if objs and any(not (0 <= o["pos"][0] <= 256 and 0 <= o["pos"][1] <= 256) for o in objs):
        fix_positions(g, objs)
    repair(g, outdir, scan, a.keep_invisible, a.reperes)
    n = drop_far(g, a.max, size)
    terrain_pipeline(g, scan, a.terrain, a.terrain_patch)      # après drop_far : les patches ne sont jamais retirés
    size = pack_glb(g, outdir, out)
    report_missing(outdir, len(g.get("images", [])))
    print(_tr("py.oar2glb.ok_0_1_1f_mo_2", out, size/1048576, len(g.get('meshes', [])), len(g.get('images', [])), n))
    if not a.keep:
        shutil.rmtree(outdir, ignore_errors=True)
        if tmp_oar:
            tmp_oar.unlink(missing_ok=True)


class Tee:
    def __init__(self, *s): self.s = s
    def write(self, x):
        for t in self.s:
            t.write(x); t.flush()
    def flush(self):
        for t in self.s:
            t.flush()


# v43 : anciens noms d'options (avant la v43), toujours acceptés : remplacés avant la lecture de la ligne de commande
OLD_OPTIONS = {"--reperes": "--markers", "--terrain-seul": "--terrain-only", "--sortie": "--output"}


def old_options(argv):
    """Remplace les anciens noms d'options par les nouveaux (« --nom=valeur » compris)."""
    out = []
    for x in argv:
        k, eq, v = str(x).partition("=")
        out.append(OLD_OPTIONS.get(k, k) + eq + v if k.startswith("--") else x)
    return out


if __name__ == "__main__":
    sys.argv = old_options(sys.argv)
    if "--version" in sys.argv[1:]:      # ni journal ni pause « Entrée »
        print(_tr("py.oar2glb.oar2glb_0_2", VERSION))
        sys.exit(0)
    log = Path(__file__).resolve().with_name("oar2glb.diag.log" if "--diag" in sys.argv else "oar2glb.log")
    lf = open(log, "w", encoding="utf-8")
    sys.stdout, sys.stderr = Tee(sys.__stdout__, lf), Tee(sys.__stderr__, lf)
    print(_tr("py.oar2glb.oar2glb_0", VERSION))
    print(_tr("py.oar2glb.args"), sys.argv[1:])
    code = 0
    try:
        main()
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code)
        code = e.code if isinstance(e.code, int) else 1
    except Exception:
        traceback.print_exc()
        code = 1
    print(_tr("py.oar2glb.log_0", log))
    if "--nopause" not in sys.argv and "--terrain-only" not in sys.argv and sys.stdin and sys.stdin.isatty():
        input(_tr("py.oar2glb.entree_pour_fermer"))
    sys.exit(code)
