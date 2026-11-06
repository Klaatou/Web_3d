#!/usr/bin/env python3
"""glb-images-check.py : contrôle, en lecture seule, des images embarquées dans un GLB
ou dans tous les GLB d'un dossier (tuiles). Pour chaque image : type déclaré (mimeType),
type réel (premiers octets), décodage par Pillow si installé. Les images identiques
(même contenu) ne sont comptées qu'une fois.

  python glb-images-check.py "P:\\...\\X.tiles"
  python glb-images-check.py "P:\\...\\X.glb"
"""
import sys, json, struct, hashlib, pathlib, io, collections, base64

try:
    from PIL import Image
except ImportError:
    Image = None

def vrai_type(b):
    if b.startswith(b"\x89PNG\r\n\x1a\n"): return "image/png"
    if b.startswith(b"\xff\xd8\xff"): return "image/jpeg"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP": return "image/webp"
    if b.startswith(b"\xff\x4f\xff\x51"): return "J2K (JPEG 2000 brut)"
    if b[4:8] == b"jP  ": return "JP2 (JPEG 2000)"
    if b.startswith(b"GIF8"): return "image/gif"
    if b.startswith(b"BM"): return "image/bmp"
    if len(b) == 0: return "vide"
    return "inconnu"

SOF = {0xC0: "base", 0xC1: "étendu", 0xC2: "progressif", 0xC3: "sans perte", 0xC5: "diff", 0xC6: "diff prog",
       0xC7: "diff sans perte", 0xC9: "arithmétique", 0xCA: "arith. prog", 0xCB: "arith. sans perte",
       0xCD: "arith. diff", 0xCE: "arith. diff prog", 0xCF: "arith. diff sans perte"}

def jpeg_info(b):
    # (codage, précision en bits, largeur, hauteur, composantes) lus dans le premier SOF ; None si introuvable
    i = 2
    while i + 4 <= len(b):
        if b[i] != 0xFF: return None
        m = b[i + 1]
        if m == 0xFF: i += 1; continue
        if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7: i += 2; continue
        n = struct.unpack_from(">H", b, i + 2)[0]
        if m in SOF and i + 10 <= len(b):
            prec, h, w, nc = b[i + 4], *struct.unpack_from(">HH", b, i + 5), b[i + 9]
            return SOF[m], prec, w, h, nc
        if m == 0xDA: return None
        i += 2 + n
    return None

def particularite(b, vt):
    # ce qui peut faire refuser une image par un navigateur alors que Pillow la lit
    if vt == "image/jpeg":
        ji = jpeg_info(b)
        if ji is None: return "JPEG sans SOF lisible"
        cod, prec, w, h, nc = ji
        r = []
        if cod not in ("base", "étendu", "progressif"): r.append("codage " + cod)
        if prec != 8: r.append(f"précision {prec} bits")
        if nc not in (1, 3, 4): r.append(f"{nc} composantes")
        if max(w, h) > 8192: r.append(f"{w}x{h}")
        if w == 0 or h == 0: r.append(f"dimensions {w}x{h}")
        return ", ".join(r)
    if vt == "image/png" and len(b) >= 33:
        w, h = struct.unpack_from(">II", b, 16)
        if max(w, h) > 8192 or w == 0 or h == 0: return f"{w}x{h}"
    return ""

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

def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    cible = pathlib.Path(sys.argv[1])
    fichiers = sorted(cible.glob("*.glb")) if cible.is_dir() else [cible]
    if not fichiers:
        print("Aucun .glb trouvé."); return
    if Image is None:
        print("Pillow absent : seul le contrôle des octets est fait (pip install pillow).")
    vus = {}                       # hash -> (verdict, mime, vrai, nom, fichier)
    par_tuile = collections.Counter()
    total = 0
    for f in fichiers:
        try:
            js, binc = lire_glb(f)
        except Exception as e:
            print(f"{f.name} : illisible ({e})"); continue
        bvs = js.get("bufferViews", [])
        for i, im in enumerate(js.get("images", [])):
            total += 1
            uri = str(im.get("uri", ""))
            if "bufferView" not in im and uri.startswith("data:") and "," in uri:
                b = base64.b64decode(uri.split(",", 1)[1] + "==")
                h = hashlib.sha1(b).hexdigest()
            elif "bufferView" not in im:
                h = "uri:" + uri
                b = b""
            else:
                bv = bvs[im["bufferView"]]
                o = bv.get("byteOffset", 0)
                b = binc[o: o + bv["byteLength"]]
                h = hashlib.sha1(b).hexdigest()
            if h not in vus:
                mime = im.get("mimeType", "(absent)")
                vt = vrai_type(b) if ("bufferView" in im or b) else "uri externe : " + uri[:60]
                if "bufferView" not in im and b: vt = "data URI, " + vt
                ok = vt == mime
                err = particularite(b, vrai_type(b)) if b else ""
                if err: ok = False
                if Image is not None and b:
                    try:
                        Image.open(io.BytesIO(b)).load()
                    except Exception as e:
                        ok, err = False, type(e).__name__ + ": " + str(e)[:80]
                vus[h] = (ok, mime, vt, im.get("name", f"#{i}"), f.name, len(b), err)
            if not vus[h][0]:
                par_tuile[f.name] += 1
    mauvais = [v for v in vus.values() if not v[0]]
    print(f"Fichiers : {len(fichiers)}  images (avec doublons) : {total}  images distinctes : {len(vus)}")
    print(f"Images distinctes en défaut : {len(mauvais)}")
    hors = collections.Counter(("bufferView" if not x[2].startswith(("data URI", "uri externe")) else x[2].split(",")[0].split(" :")[0]) for x in vus.values())
    print("Origine des images distinctes : " + ", ".join(f"{k} {n}" for k, n in hors.items()))
    print("\nPar type (déclaré -> réel : particularité) :")
    for (m, v, e), n in collections.Counter((x[1], x[2][:40], x[6].split(":")[0]) for x in mauvais).most_common():
        print(f"  {n:6d}  {m} -> {v} : {e}")
    tailles = sorted(x[5] for x in mauvais)
    if tailles:
        print(f"\nTaille des images en défaut : min {tailles[0]} o, médiane {tailles[len(tailles)//2]} o, max {tailles[-1]} o")
    print("\n20 premiers exemples :")
    for ok, m, v, nom, fic, n, err in mauvais[:20]:
        print(f"  {fic}  {nom}  {n} o  déclaré {m}  réel {v}  {err}")
    print("\nTuiles les plus touchées (images en défaut, doublons compris) :")
    for fic, n in par_tuile.most_common(10):
        print(f"  {n:6d}  {fic}")

if __name__ == "__main__":
    main()
