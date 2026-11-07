#!/usr/bin/env python3
"""Decodeur GIF de la page (lot 1.6.15) : compare, pixel pour pixel, les images decodees par src/core.js (gifLzw, decodeGif) a celles que lit PIL, sur des GIF fabriques ici :
bruit (LZW), degrade de 256 couleurs entrelace, grande image, transparence avec dispositions 1, 2 et 3, durees. Sans navigateur : il faut Node et Pillow ; sinon l'essai est saute (code 0).
Lancer : python tests/gif_decode.py
"""
import json, pathlib, random, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
try:
    from PIL import Image, ImageDraw
except ImportError:
    print("[SAUTE] Pillow absent (pip install pillow) : decodeur GIF non compare"); sys.exit(0)
node = shutil.which("node")
if not node:
    print("[SAUTE] Node absent : decodeur GIF non compare"); sys.exit(0)
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_gifdec_"))
random.seed(7)


def pal_img(w, h, fn, ncol=16):
    im = Image.new("P", (w, h)); px = im.load()
    for y in range(h):
        for x in range(w): px[x, y] = fn(x, y) % ncol
    im.putpalette([v for i in range(256) for v in ((i * 37) % 256, (i * 91 + 50) % 256, (i * 53 + 120) % 256)])
    return im


fr = [pal_img(40, 30, lambda x, y: random.randrange(16)) for _ in range(4)]
fr[0].save(tmp / "bruit.gif", save_all=True, append_images=fr[1:], duration=[100, 200, 300, 50], loop=0, interlace=False)
fr = [pal_img(64, 64, lambda x, y, k=k: x * 3 + y * 5 + k * 40, 256) for k in range(3)]
fr[0].save(tmp / "degrade.gif", save_all=True, append_images=fr[1:], duration=120, loop=0, interlace=True)
fr = [pal_img(200, 150, lambda x, y: random.randrange(8), 8) for _ in range(3)]
fr[0].save(tmp / "grande.gif", save_all=True, append_images=fr[1:], duration=80, loop=0)
frames = []
for col, box in [((255, 0, 0, 255), (0, 0, 30, 20)), ((0, 255, 0, 255), (10, 10, 45, 35)), ((0, 0, 255, 255), (20, 5, 50, 30)), ((255, 255, 0, 255), (0, 20, 25, 40))]:
    im = Image.new("RGBA", (50, 40), (0, 0, 0, 0)); ImageDraw.Draw(im).rectangle(box, fill=col); frames.append(im)
for d in (1, 2, 3):
    kw = {"transparency": 0} if d > 1 else {}
    frames[0].save(tmp / f"disposition{d}.gif", save_all=True, append_images=frames[1:], duration=100, loop=0, disposal=d, **kw)
for f in sorted(tmp.glob("*.gif")):
    im = Image.open(f); out = []
    for i in range(im.n_frames):
        im.seek(i); out.append({"ms": im.info.get("duration", 0), "rgba": list(im.convert("RGBA").tobytes())})
    (tmp / (f.stem + ".json")).write_text(json.dumps({"w": im.size[0], "h": im.size[1], "frames": out}), encoding="utf-8")
js = r"""
const fs = require('fs'), src = fs.readFileSync(process.argv[2], 'utf8'), dir = process.argv[3];
const a = src.indexOf('  function gifLzw('), b = src.indexOf('  const gifAnime = u =>');
if (a < 0 || b < 0) { console.log('ECHEC decodeur introuvable dans src/core.js'); process.exit(1); }
eval('class ImageData { constructor(d, w, h) { this.data = d; this.width = w; this.height = h; } }\n' + src.slice(a, b) + '\nglobalThis.decodeGif = decodeGif;');
let bad = 0;
for (const f of fs.readdirSync(dir).filter(n => n.endsWith('.gif')).sort()) {
  const ref = JSON.parse(fs.readFileSync(dir + '/' + f.replace('.gif', '.json'))), an = decodeGif(new Uint8Array(fs.readFileSync(dir + '/' + f)), 64 * 1048576);
  if (!an) { console.log('ECHEC ' + f + ' : decodeGif ne rend rien'); bad++; continue; }
  let diff = 0;
  an.frames.forEach((fr, i) => { const r = ref.frames[i]; if (!r) { diff += 1e9; return; }
    for (let k = 0; k < r.rgba.length; k += 4) { const ar = r.rgba[k + 3], ad = fr.img.data[k + 3];
      if (!((ar === 0 && ad === 0) || (ar > 0 && ad > 0 && r.rgba[k] === fr.img.data[k] && r.rgba[k + 1] === fr.img.data[k + 1] && r.rgba[k + 2] === fr.img.data[k + 2]))) diff++; } });
  const okN = an.frames.length === ref.frames.length, okMs = an.frames.every((fr, i) => fr.ms === (ref.frames[i].ms <= 10 ? 100 : ref.frames[i].ms));
  const ok = diff === 0 && okN && okMs; if (!ok) bad++;
  console.log((ok ? 'OK    ' : 'ECHEC ') + f + ' ' + an.w + 'x' + an.h + ', ' + an.frames.length + ' images : ' + (ok ? 'identique a PIL' : diff + ' pixels differents ; images ' + okN + ' ; durees ' + okMs));
}
process.exit(bad ? 1 : 0);
"""
(tmp / "run.js").write_text(js, encoding="utf-8")
r = subprocess.run([node, str(tmp / "run.js"), str(ROOT / "src" / "core.js"), str(tmp)], capture_output=True, text=True)
for l in (r.stdout + r.stderr).splitlines():
    print(("[OK]    " if l.startswith("OK") else "[ECHEC] ") + l[6:] if l[:2] in ("OK", "EC") else l)
print("\nRESULTAT : " + ("tout est passe" if r.returncode == 0 else "echec"))
sys.exit(r.returncode)
