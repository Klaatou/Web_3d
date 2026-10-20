#!/usr/bin/env python3
"""
oar2glb.py - OAR OpenSim -> GLB unique (convoar + réparation + empaquetage)

Usage :  python oar2glb.py "P:\\chemin\\MaRegion.oar" [--reencode] [--max 600] [--convoar chemin\\convoar.exe] [--keep]

Étapes :
 1. (option --reencode) textures J2K de l'OAR décodées puis réencodées proprement avec Pillow
    dans un OAR temporaire -> supprime les "unhandled number of components: 0" de convoar.
 2. convoar lancé via un petit lanceur convoar_inv.exe (compilé une fois avec le csc.exe de Windows)
    qui force la culture invariante : nombres en 0.5 et pas 0,5, sans toucher aux réglages Windows.
 3. Réparation du .gltf (backslashes orphelins) + contrôle de cohérence (tailles des vecteurs).
 4. Retrait des objets hors région (skybox à 3000 m...) : |coordonnée| > --max mètres.
 5. Empaquetage en un seul .glb (buffers + textures intégrés), pur Python.
Sortie : MaRegion.glb à côté de l'OAR.
"""
import argparse, base64, io, json, math, os, re, shutil, struct, subprocess, sys, tarfile, traceback
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


# ---------- diagnostic : positions lues directement dans l'OAR ----------
def oar_info(oar):
    import html as _html
    num = r"\s*<{0}>([^<]+)</{0}>"
    rx_pos = re.compile(r"<GroupPosition>" + num.format("X") + num.format("Y") + num.format("Z"))
    rx_rot = re.compile(r"<RotationOffset>" + num.format("X") + num.format("Y") + num.format("Z") + num.format("W"))
    rx_name = re.compile(r"<Name>([^<]*)</Name>")
    objs, size = [], (256.0, 256.0)
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
                x = t.extractfile(m).read().decode("utf-8", "replace")
                mp = rx_pos.search(x)
                if not mp:
                    continue
                mr, mn = rx_rot.search(x), rx_name.search(x)
                objs.append({"pos": [float(v) for v in mp.groups()],
                             "rot": [float(v) for v in mr.groups()] if mr else None,
                             "name": _html.unescape(mn.group(1)) if mn else ""})
    print(f"[OAR] région {size[0]:g} x {size[1]:g} m")
    if objs:
        pts = [o["pos"] for o in objs]
        lo = [round(min(p[k] for p in pts), 1) for k in range(3)]
        hi = [round(max(p[k] for p in pts), 1) for k in range(3)]
        print(f"[OAR] {len(objs)} objets de {lo} à {hi}  (X, Y, Z OpenSim, Z = hauteur)")
    return size, objs


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
        print(f"[GLB] texture {name} absente : remplacée par du gris")
        return GREY_PNG
    files = sorted(base.rglob("*"))
    bufs = [x for x in files if x.suffix.lower() == ".buf"]
    sys.exit(f"[ERREUR] {name} introuvable (annoncé par le .gltf).\n  {base} contient {len(files)} fichier(s), dont {len(bufs)} .buf : "
             + ", ".join(f"{x.name} ({x.stat().st_size} o)" for x in bufs[:10])
             + f"\n  Espace libre sur {base.anchor} : {shutil.disk_usage(base).free / 2**30:.1f} Go")


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
    ap.add_argument("--nopause", action="store_true", help="ne pas attendre Entrée à la fin")
    a = ap.parse_args()

    oar = Path(a.oar).resolve()
    if not oar.exists():
        sys.exit(f"[ERREUR] {oar} introuvable")
    if not Path(a.convoar).exists():
        sys.exit(f"[ERREUR] convoar introuvable : {a.convoar} (utilise --convoar)")
    size, objs = oar_info(oar)
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

    gltfs = sorted(outdir.glob("*.gltf"), key=lambda p: p.stat().st_mtime)
    if not gltfs:
        sys.exit(f"[ERREUR] aucun .gltf produit dans {outdir}")
    g = load_gltf(gltfs[-1])
    check(g)
    if objs and any(not (0 <= o["pos"][0] <= 256 and 0 <= o["pos"][1] <= 256) for o in objs):
        fix_positions(g, objs)
    n = drop_far(g, a.max, size)
    size = pack_glb(g, outdir, out)
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
    log = Path(__file__).resolve().with_name("oar2glb.log")
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
