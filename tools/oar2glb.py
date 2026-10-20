#!/usr/bin/env python3
"""
oar2glb.py - OAR OpenSim -> GLB unique (convoar + réparation + empaquetage)

Usage :  python oar2glb.py "P:\\chemin\\MaRegion.oar" [--reencode] [--max 600] [--convoar chemin\\convoar.exe] [--keep] [--keep-invisible]
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


def reencode_oar(src, dst):
    try:
        import PIL  # noqa: F401
    except ImportError:
        sys.exit(f'[ERREUR] --reencode demande Pillow, absent de ce Python ({sys.executable}).\n  Installe-le dans ce Python précis : & "{sys.executable}" -m pip install pillow')
    import time
    from concurrent.futures import ProcessPoolExecutor
    t0 = time.time()
    print(f"[textures] lecture de {src.name}...")
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
    print(f"[textures] {len(sculpts)} sculpt maps laissées intactes")
    workers = max(1, (os.cpu_count() or 2) - 1)
    print(f"[textures] {len(idx)} textures à réencoder sur {workers} cœurs ({time.time() - t0:.0f} s)")
    ok = bad = 0
    step = max(1, len(idx) // 20)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for k, (i, res) in enumerate(zip(idx, ex.map(reencode_one, [members[i][1] for i in idx], chunksize=8)), 1):
            if res is None:
                bad += 1
            else:
                m, _ = members[i]
                m.size = len(res)
                members[i] = (m, res)
                ok += 1
            if k % step == 0 or k == len(idx):
                print(f"[textures] {k}/{len(idx)} ({100 * k // len(idx)} %) - {time.time() - t0:.0f} s", flush=True)
    print(f"[textures] écriture de {dst.name}...")
    with tarfile.open(dst, "w:gz", compresslevel=1) as tout:
        for m, d in members:
            tout.addfile(m, io.BytesIO(d) if d is not None else None)
    print(f"[textures] {ok} réencodées, {bad} illisibles (laissées telles quelles) - {time.time() - t0:.0f} s")


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
                raise ValueError("clé LLSD attendue")
            ln = struct.unpack_from(">I", d, p + 1)[0]
            key = d[p + 5:p + 5 + ln].decode("utf-8", "replace")
            out[key], p = llsd_bin(d, p + 5 + ln)
        if d[p:p + 1] != b"}":
            raise ValueError("fin de table LLSD attendue")
        return out, p + 1
    if t == b"[":
        n = struct.unpack_from(">I", d, p)[0]
        p += 4
        out = []
        for _ in range(n):
            v, p = llsd_bin(d, p)
            out.append(v)
        if d[p:p + 1] != b"]":
            raise ValueError("fin de tableau LLSD attendue")
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
    raise ValueError(f"type LLSD inconnu {t!r}")


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
        return None, "bloc skin présent mais illisible"
    except Exception as e:
        return None, f"en-tête du mesh illisible ({e})"


def llmesh_domains(data, n=4):
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
        return "sans TextureEntry"
    tex, col = tex_entry
    n = len({f for f in list(tex) + list(col) if f is not None})
    return f"texture {tex[None][:8]} alpha {col[None] / 255:.2f}" + (f" (+{n} face(s) à part)" if n else "")


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


def oar_scan(oar):
    import html as _html  # noqa: F401
    size, groups, skins, terrain = (256.0, 256.0), [], {}, None
    with tarfile.open(oar, "r:*") as t:
        for m in t:
            if not m.isfile():
                continue
            if m.name == "archive.xml":
                x = t.extractfile(m).read().decode("utf-8", "replace")
                ms = re.search(r"<size_in_meters>\s*([\d.]+)\s*,\s*([\d.]+)", x)
                if ms:
                    size = (float(ms.group(1)), float(ms.group(2)))
            elif m.name.startswith("objects/") and m.name.endswith(".xml"):
                try:
                    parts = parse_object(t.extractfile(m).read())
                except Exception as e:
                    print(f"[OAR] {m.name} illisible ({e})")
                    continue
                if parts and parts[0]["gpos"]:
                    groups.append({"file": m.name, "parts": parts})
            elif m.name.startswith("assets/") and m.name.endswith("_mesh.llmesh"):
                raw = t.extractfile(m).read()
                skin, err = llmesh_skin(raw)
                if skin is not None or err:
                    skins[m.name[7:43].lower()] = {"skin": skin, "err": err, "bsm": bind_shape(skin),
                                                   "dom": llmesh_domains(raw) if skin is not None else []}
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
    return {"size": size, "groups": groups, "skins": skins, "terrain": terrain}


def oar_info(scan):
    # objets racines au format utilisé par fix_positions : pos, rot, nom
    objs = [{"pos": g["parts"][0]["gpos"], "rot": g["parts"][0]["rot"], "name": g["parts"][0]["name"]}
            for g in scan["groups"]]
    size = scan["size"]
    print(f"[OAR] région {size[0]:g} x {size[1]:g} m")
    if objs:
        pts = [o["pos"] for o in objs]
        lo = [round(min(p[k] for p in pts), 1) for k in range(3)]
        hi = [round(max(p[k] for p in pts), 1) for k in range(3)]
        print(f"[OAR] {len(objs)} objets de {lo} à {hi}  (X, Y, Z OpenSim, Z = hauteur)")
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
    print(f"[var-region] {moved} objet(s) replacé(s) à leur vraie position, {len(used)} reconnu(s), {lost} non reconnu(s)")


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
        print(f"[lanceur] {dst.name} mis à jour (loadFromRemoteSources)")


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
        sys.exit("[ERREUR] csc.exe (.NET Framework 4) introuvable")
    plat = pe_platform(convoar)
    src = convoar.with_name("convoar_inv.cs")
    src.write_text(LAUNCHER_CS, encoding="utf-8")
    r = subprocess.run([str(csc), "/nologo", "/target:exe", f"/platform:{plat}", f"/out:{launcher}", str(src)],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ERREUR] compilation du lanceur :\n{r.stdout}{r.stderr}")
    ensure_config(convoar, launcher)
    print(f"[lanceur] {launcher} compilé ({plat})")
    return launcher


def run_convoar(convoar, oar, outdir):
    exe = ensure_launcher(convoar) if os.name == "nt" else Path(convoar)
    args = [str(exe), "--outputdir", outdir.name, oar.name]   # options AVANT le fichier
    print("[convoar]", " ".join(f'"{a}"' if " " in a else a for a in args))
    enc = "oem" if os.name == "nt" else "utf-8"
    p = subprocess.Popen(args, cwd=oar.parent, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding=enc, errors="replace")
    for line in p.stdout:
        print(line.rstrip())
    p.wait()
    print(f"[convoar] code retour {p.returncode}")


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
        sys.exit(f"[ERREUR] .gltf invalide : {e}\n  ligne {e.lineno} : {line.strip()[:120]}")


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
        sys.exit(f"[ERREUR] {len(errs)} vecteurs de mauvaise taille : nombres écrits avec virgule décimale.\n  "
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
                cand, how = uu[p["uuid"]], "UUID du prim"
            elif p["mesh"] and p["mesh"] in uu:
                cand, how = uu[p["mesh"]], "UUID du mesh"
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
                victims.setdefault(match[p["uuid"]][0], "boîte racine d'animesh" if p["uuid"] in boxes and not p["invisible"] else "transparent (OAR)")
    for i, n in enumerate(g.get("nodes", [])):
        if i not in victims and node_all_invisible(g, n, cache):
            victims[i] = "matériaux transparents (GLB)"
    for i in sorted(victims):
        print(f"[invisible] node {i} '{g['nodes'][i].get('name', '?')}' retiré : {victims[i]}")
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

    def finish(self):
        if self.data:
            self.g.setdefault("buffers", []).append({"byteLength": len(self.data),
                                                     "uri": "data:application/octet-stream;base64," + base64.b64encode(bytes(self.data)).decode()})


def read_vec3(g, base, cache, ai):
    a = g["accessors"][ai]
    if a.get("componentType") != 5126 or a.get("type") != "VEC3" or "sparse" in a or "bufferView" not in a:
        raise ValueError(f"accesseur {ai} non géré (float VEC3 simple attendu)")
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
        return "nœud"
    return "cuite" if any(abs(v - 1) > 1e-4 for v in exp) else "aucune"


def rig_mesh(g, base, cache, part, bsm, ni):
    # copie du mesh du nœud, sommets/normales ramenés dans l'espace du skin (échelle du prim ignorée, bind_shape appliquée)
    # -> (mesh, points) ou message d'erreur (str)
    node = g["nodes"][ni]
    if "mesh" not in node:
        return "le nœud n'a pas de mesh"
    sx, sy, sz = part["scale"] or [1, 1, 1]
    mode = rigged_scale_mode(node, (sx, sy, sz))
    lin = [[bsm[0], bsm[4], bsm[8]], [bsm[1], bsm[5], bsm[9]], [bsm[2], bsm[6], bsm[10]]]
    t = bsm[12:15]
    li = inv3(lin)
    if li is None:
        return "bind_shape_matrix non inversible"
    mesh = json.loads(json.dumps(g["meshes"][node["mesh"]]))
    allp, raw = [], []
    for pr in mesh.get("primitives", []):
        if "POSITION" not in pr.get("attributes", {}):
            continue
        out = []
        for X, Y, Z in read_vec3(g, base, cache, pr["attributes"]["POSITION"]):
            x, y, z = X, -Z, Y
            raw.append((x, y, z))
            if mode == "cuite":
                x, y, z = x / sx, y / sy, z / sz
            x, y, z = (lin[0][0] * x + lin[0][1] * y + lin[0][2] * z + t[0],
                       lin[1][0] * x + lin[1][1] * y + lin[1][2] * z + t[1],
                       lin[2][0] * x + lin[2][1] * y + lin[2][2] * z + t[2])
            out.append([x, z, -y])
        pr["_pts"] = out
        allp += out
        if "NORMAL" in pr["attributes"]:
            ns = []
            for X, Y, Z in read_vec3(g, base, cache, pr["attributes"]["NORMAL"]):
                x, y, z = X, -Z, Y
                if mode == "cuite":
                    x, y, z = x * sx, y * sy, z * sz
                v = (x, y, z)
                nx, ny, nz = (sum(li[i][k] * v[i] for i in range(3)) for k in range(3))
                l = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
                ns.append([nx / l, nz / l, -ny / l])
            pr["_nrm"] = ns
    if not allp:
        return "aucune géométrie lisible"
    rext = [max(r[k] for r in raw) - min(r[k] for r in raw) for k in range(3)]
    print(f"[riggé] mesure : '{part['name']}' sommets bruts du GLB {rext[0]:.3g} x {rext[1]:.3g} x {rext[2]:.3g} (axes OpenSim), "
          f"échelle du prim {fmt3([sx, sy, sz])}, échelle de bind_shape {fmt3([math.sqrt(sum(bsm[c * 4 + r] ** 2 for r in range(3))) for c in range(3)])}, "
          f"{len(raw)} sommets")
    return mesh, allp, mode


MAX_ANIMAL, MIN_ANIMAL = 12.0, 0.1       # garde-fou : un animal fait entre 10 cm et 12 m dans sa plus grande dimension


def place_rigged_group(g, base, cache, extra, tree, grp, items):
    # items : [(partie riggée, bind_shape, nœud GLB)] d'UN objet. Les morceaux d'un même animal (chacun avec sa
    # bind_shape_matrix) partagent le même repère : on les déplace ENSEMBLE (même décalage, même rotation), sans
    # jamais les poser séparément. Retourne le nombre de morceaux corrigés.
    built = []
    for part, bsm, ni in items:
        r = rig_mesh(g, base, cache, part, bsm, ni)
        if isinstance(r, str):
            print(f"[riggé] '{part['name']}' : {r}, non corrigé")
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
        print(f"[riggé] '{root['name']}' : taille obtenue {ext[0]:.2f} x {ext[2]:.2f} x {ext[1]:.2f} m implausible "
              f"(hors de {MIN_ANIMAL:g} à {MAX_ANIMAL:g} m), laissé tel que convoar l'a produit (voir --diag)")
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
        ground, src = gz - root["scale"][2] / 2, "dessous de la boîte racine"
    else:
        ground, src = gz, "altitude de la racine"
    for part, ni, mesh, pts, mode in built:
        for pr in mesh["primitives"]:
            if "_pts" in pr:
                pr["attributes"]["POSITION"] = extra.add_vec3([[p[0] - cx, p[1], p[2] - cz] for p in pr.pop("_pts")])
            if "_nrm" in pr:
                pr["attributes"]["NORMAL"] = extra.add_vec3(pr.pop("_nrm"))
        g["meshes"].append(mesh)
        node = g["nodes"][ni]
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
    print(f"[riggé] '{root['name']}' : {len(built)} morceau(x), échelle du prim {built[0][4]}, {ext[0]:.2f} x {ext[2]:.2f} x {ext[1]:.2f} m "
          f"(L x l x h), centré en ({gx:.1f}, {gy:.1f}), pieds à {ground:.2f} m ({src})")
    return len(built)


def repair(g, base, scan, keep_invisible):
    match = match_nodes(g, scan)
    extra, cache, tree = ExtraBuffer(g), {}, Tree(g)
    n_rig = n_inv = 0
    for grp in scan["groups"]:
        items = []
        for p in grp["parts"]:
            sk = scan["skins"].get(p["mesh"]) if p["mesh"] else None
            if not sk or not sk["bsm"]:
                if sk and sk["err"]:
                    print(f"[riggé] '{p['name']}' : {sk['err']}, ignoré")
                continue
            if p["uuid"] not in match:
                print(f"[riggé] '{p['name']}' ({p['uuid']}) : nœud GLB introuvable, non corrigé (voir --diag)")
                continue
            items.append((p, sk["bsm"], match[p["uuid"]][0]))
        if items:
            n_rig += place_rigged_group(g, base, cache, extra, tree, grp, items)
    extra.finish()
    if not keep_invisible:
        n_inv = remove_invisible(g, scan, match)
    print(f"[correctif] {n_rig} mesh(es) riggé(s) remis à l'échelle, {n_inv} prim(s) invisible(s) retiré(s)")
    return n_rig, n_inv


# ---------- --diag ----------
def read_glb_json(path):
    path = Path(path)
    if path.suffix.lower() == ".gltf":
        return load_gltf(path)
    d = path.read_bytes()
    if d[:4] != b"glTF":
        sys.exit(f"[ERREUR] {path} n'est pas un GLB")
    ln, kind = struct.unpack_from("<I4s", d, 12)
    return json.loads(d[20:20 + ln].decode("utf-8"))


def fmt3(v):
    return "(" + ", ".join(f"{x:.3g}" for x in v) + ")" if v else "?"


def diag(scan, g, glb_label, base=None):
    match = match_nodes(g, scan) if g else {}
    tree = Tree(g) if g else None
    parts = [(grp, p) for grp in scan["groups"] for p in grp["parts"]]
    print(f"[diag] {len(scan['groups'])} objet(s), {len(parts)} partie(s) ; terrain {'oui' if scan['terrain'] else 'non'} ; "
          f"{'GLB ' + glb_label if g else 'pas de GLB : correspondance non évaluée (--glb)'}")
    nr = ni = nm = 0
    boxes = rig_box_roots(scan)
    for k, (grp, p) in enumerate(parts, 1):
        sk = scan["skins"].get(p["mesh"]) if p["mesh"] else None
        if sk and sk["bsm"]:
            rig, nr = "oui", nr + 1
        elif sk:
            rig = "oui (" + (sk["err"] or "sans bind_shape_matrix") + ")"
        else:
            rig = "non" if p["mesh"] else "non (pas un mesh)"
        bsm = sk["bsm"] if sk and sk["bsm"] else None
        bs = fmt3([math.sqrt(sum(bsm[c * 4 + r] ** 2 for r in range(3))) for c in range(3)]) if bsm else "-"
        ni += p["invisible"]
        if g:
            if p["uuid"] in match:
                n, how = match[p["uuid"]]
                nm += 1
                node = g["nodes"][n]
                sc = node.get("scale") or (mat_trs(node["matrix"])[2] if "matrix" in node else None)
                gl = f"nœud {n} '{node.get('name', '')}' [{how}] ; échelle du nœud {fmt3(sc) if sc else 'aucune'}" + (f" ; échelle du prim appliquée : {rigged_scale_mode(node, p['scale'] or [1, 1, 1])}" if bsm else "")
            else:
                gl = "nœud introuvable"
        else:
            gl = "-"
        racine = "racine" if p is grp["parts"][0] else "enfant"
        print(f"{k:5d} | {p['name'] or '(sans nom)'} | {p['uuid']} | {racine} | riggé : {rig} | échelle du prim {fmt3(p['scale'])} | "
              f"échelle bind_shape {bs} | transparent : {'oui' if p['invisible'] else 'non'} | "
              f"boîte racine d'animesh : {'oui' if p['uuid'] in boxes else 'non'} | GLB : {gl}")
        if bsm or p["uuid"] in boxes or p["invisible"]:
            gz = terrain_height(scan["terrain"], p["gpos"][0], p["gpos"][1])
            print(f"      position {fmt3(p['gpos'])} ; terrain {'%.2f m' % gz if gz is not None else 'inconnu'} ; "
                  f"{p['tex']}" + (f" ; translation bind_shape {fmt3(bsm[12:15])}" if bsm else ""))
            if bsm:
                sk = scan["skins"][p["mesh"]]
                print(f"      bind_shape_matrix : {[round(v, 4) for v in bsm]}")
                print(f"      domaine de position du mesh : " + ("; ".join(f"{fmt3(a)} .. {fmt3(b)}" for a, b in sk["dom"]) or "illisible"))
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
                        print(f"      accesseur POSITION {ac} ; bufferView {bv} ; buffer {str(bf.get('uri'))[:60]} {bf.get('byteLength')} o ; 3 premiers sommets {pts[:3]}")
                        print(f"      sommets du GLB (axes OpenSim x, y, z) : de {fmt3([lo_[0], -hi_[2], lo_[1]])} à {fmt3([hi_[0], -lo_[2], hi_[1]])} "
                              f"soit {fmt3([hi_[0] - lo_[0], hi_[2] - lo_[2], hi_[1] - lo_[1]])} m, {len(pts)} sommets")
                    except Exception as e:
                        print(f"      sommets du GLB illisibles ({e})")
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
                        print(f"      matériau GLB : {m.get('name')!r} couleur {(m.get('pbrMetallicRoughness') or {}).get('baseColorFactor')} "
                              f"mode {m.get('alphaMode', 'OPAQUE')} image {im or '-'}")
    print(f"[diag] riggés : {nr} ; transparents : {ni} ; boîtes racines d'animesh : {len(boxes)} ; nœuds GLB trouvés : {nm}/{len(parts)}")
    if g:
        cache, nv = {}, 0
        for n in g.get("nodes", []):
            nv += node_all_invisible(g, n, cache)
        print(f"[diag] nœuds GLB dont tous les matériaux sont transparents : {nv}")
        print(f"[diag] UUID lisibles dans les nœuds GLB : {len(node_uuids(g))} ; exemples de nœuds :")
        for i, n in enumerate(g.get("nodes", [])[:6]):
            print(f"       node {i} : nom={n.get('name')!r} extras={json.dumps(n.get('extras'))[:100]} "
                  f"clés={sorted(k for k in n if k not in ('name', 'extras'))}")


# ---------- 4. hors région ----------
def drop_far(g, vmax, size):
    # hors région : au-delà de la taille de la région (+10 m) en horizontal, ou de --max en hauteur
    sx, sy = size
    n = 0
    for sc in g.get("scenes", []):
        keep = []
        for i in sc.get("nodes", []):
            p = node_pos(g["nodes"][i])
            if not (-10 <= p[0] <= sx + 10 and -10 <= -p[2] <= sy + 10 and abs(p[1]) <= vmax):
                print(f"[hors région] node {i} '{g['nodes'][i].get('name', '?')}' à {[round(c, 1) for c in p]} retiré")
                n += 1
            else:
                keep.append(i)
        sc["nodes"] = keep
    pts = [node_pos(g["nodes"][i]) for sc in g.get("scenes", []) for i in sc["nodes"]]
    if pts:
        lo = [round(min(p[k] for p in pts), 1) for k in range(3)]
        hi = [round(max(p[k] for p in pts), 1) for k in range(3)]
        print(f"[étendue] {len(pts)} objets de {lo} à {hi}  (glTF : X, hauteur, -Y)")
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
            print(f"[GLB] {name} -> {hit.name}")
        return hit.read_bytes()
    if image:
        MISSING.append(name)
        return GREY_PNG
    files = sorted(base.rglob("*"))
    bufs = [x for x in files if x.suffix.lower() == ".buf"]
    sys.exit(f"[ERREUR] {name} introuvable (annoncé par le .gltf).\n  {base} contient {len(files)} fichier(s), dont {len(bufs)} .buf : "
             + ", ".join(f"{x.name} ({x.stat().st_size} o)" for x in bufs[:10])
             + f"\n  Espace libre sur {base.anchor} : {shutil.disk_usage(base).free / 2**30:.1f} Go")


MISSING = []


def report_missing(base, total):
    if not MISSING:
        return
    from collections import Counter
    files = [f for f in Path(base).rglob("*") if f.is_file()]
    ext = Counter(f.suffix.lower() for f in files)
    print(f"[GLB] {len(MISSING)} texture(s) absente(s) sur {total}, remplacée(s) par du gris. Exemples : " + ", ".join(MISSING[:3]))
    print(f"[GLB] {base} contient {len(files)} fichier(s) : " + ", ".join(f"{k or '(sans extension)'} {v}" for k, v in ext.most_common(8)))
    print("[GLB] fichiers images présents, exemples : " + ", ".join(f.name for f in files if f.suffix.lower() in (".jpg", ".png"))[:300])


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("oar")
    ap.add_argument("--reencode", action="store_true", help="réencoder les textures J2K avant convoar")
    ap.add_argument("--max", type=float, default=600.0, help="hauteur max (m) d'un objet racine (skybox au-delà), défaut 600")
    ap.add_argument("--convoar", default=shutil.which("convoar") or DEFAULT_CONVOAR)
    ap.add_argument("--keep", action="store_true", help="garder les fichiers intermédiaires")
    ap.add_argument("--keep-invisible", action="store_true", help="garder les prims entièrement transparents (retirés par défaut)")
    ap.add_argument("--diag", action="store_true", help="ne rien modifier : lister les objets de l'OAR, leur skin et le nœud GLB correspondant")
    ap.add_argument("--glb", help="avec --diag : GLB ou .gltf à comparer ; défaut : le .gltf du dossier <oar>-GLTF (conservé par --keep), sinon le .glb voisin")
    ap.add_argument("--nopause", action="store_true", help="ne pas attendre Entrée à la fin")
    a = ap.parse_args()

    oar = Path(a.oar).resolve()
    if not oar.exists():
        sys.exit(f"[ERREUR] {oar} introuvable")
    if a.diag:
        scan = oar_scan(oar)
        auto = sorted((oar.parent / (oar.stem + "-GLTF")).glob("*.gltf"), key=lambda q: q.stat().st_mtime)
        glb = Path(a.glb) if a.glb else (auto[-1] if auto else oar.with_suffix(".glb"))
        diag(scan, read_glb_json(glb) if glb.exists() else None, glb.name, glb.parent if glb.suffix.lower() == ".gltf" else None)
        return
    if not Path(a.convoar).exists():
        sys.exit(f"[ERREUR] convoar introuvable : {a.convoar} (utilise --convoar)")
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
        print(f"[convoar] {len(miss)} image(s) annoncée(s) par le .gltf mais absente(s) du dossier (exemples : {', '.join(miss[:2])}) : "
              f"nouvel essai {essai}/{MAX_RETRY}, les images déjà écrites sont conservées")
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
        print(f"[convoar] {n_rec} image(s) récupérée(s) de l'essai précédent")
        if not a.keep:
            shutil.rmtree(old, ignore_errors=True)

    gltfs = sorted(outdir.glob("*.gltf"), key=lambda p: p.stat().st_mtime)
    if not gltfs:
        sys.exit(f"[ERREUR] aucun .gltf produit dans {outdir}")
    g = load_gltf(gltfs[-1])
    check(g)
    if objs and any(not (0 <= o["pos"][0] <= 256 and 0 <= o["pos"][1] <= 256) for o in objs):
        fix_positions(g, objs)
    repair(g, outdir, scan, a.keep_invisible)
    n = drop_far(g, a.max, size)
    size = pack_glb(g, outdir, out)
    report_missing(outdir, len(g.get("images", [])))
    print(f"[OK] {out}  ({size/1048576:.1f} Mo, {len(g.get('meshes', []))} meshes, "
          f"{len(g.get('images', []))} textures, {n} objet(s) hors région retiré(s))")
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


if __name__ == "__main__":
    log = Path(__file__).resolve().with_name("oar2glb.diag.log" if "--diag" in sys.argv else "oar2glb.log")
    lf = open(log, "w", encoding="utf-8")
    sys.stdout, sys.stderr = Tee(sys.__stdout__, lf), Tee(sys.__stderr__, lf)
    print("[args]", sys.argv[1:])
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
    print(f"[log] {log}")
    if "--nopause" not in sys.argv:
        input("Entrée pour fermer...")
    sys.exit(code)
