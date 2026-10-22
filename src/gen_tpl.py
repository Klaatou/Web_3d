#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
glb2html - Génère une page HTML 100 % hors ligne à partir d'un .glb
(three.js + loaders + GLB intégrés dans le fichier, aucun accès réseau à l'ouverture).

Usage :
  python glb2html.py ile.glb
  python glb2html.py ile.glb -o ile.html --hole 90 --wave 1.2 --sea-y -30 --zoom 1.3
  python glb2html.py dossier_glb/ --no-sea
  python glb2html.py ile.glb --vendor C:\\chemin\\node_modules\\three   (aucun téléchargement)

Au premier lancement, les fichiers three.js nécessaires sont téléchargés une fois
dans ~/.cache/glb2html/three@VERSION, ensuite tout est local.
Draco et Meshopt gérés automatiquement (décodeurs intégrés seulement si le GLB en a besoin).
"""
from __future__ import annotations

VERSION = "__VERSION__"

import argparse
import base64
import html
import json
import math
import pathlib
import re
import shutil
import struct
import sys
import urllib.parse
import urllib.request

# <<DEFAULTS>>
ROTATE = 0
HOLE_RADIUS = 180.0
HOLE_FADE = 60.0
HOLE_X = 0.0
HOLE_Z = 0.0
WAVE_AMP = 0.5
SEA_Y = -50.0
ZOOM_RATIO = 1.0
CAM_DIR = (0.0, 0.25, 1.0)
TARGET = (0.0, 15.0, 0.0)
SEA_ENABLED = True
ANIM_ENABLED = False
RETINA_ENABLED = False
FOLIAGE_CUTOUT = 0.12
SEA_COLOR = 0x3A9AD9
SKY_COLOR = 0x87CEEB
SEA_SEGMENTS = 400
WALK_ENABLED = True
EYE_HEIGHT = 1.7
WALK_SPEED = 3.5
WALK_IGNORE = "door, porte"
NAMES_ENABLED = False
PRESENCE_URL = ""
ROOM = ""
CHAT_ENABLED = True
CHAT_FADE = 0.0
PROFILE = "public"
ZONES_JSON = "[]"
SPECTATE = None
PANEL = True
ZONES_LIVE = ""
MAP_JSON = "[]"
MAP_URL = ""
# <</DEFAULTS>>

SEA_SIZE = 4000
TILE_RADIUS = 150.0         # m : charger les tuiles dont la boîte est à moins de ce rayon de l'avatar (plan X,Z)
TILE_MARGIN = 60.0          # m : décharger au-delà de rayon + marge (hystérésis)
TILE_MAX_MO = 200.0         # Mo de tuiles chargées en même temps
TILE_MAX_TRI = 8000000      # triangles de tuiles chargées en même temps
TILE_CONCURRENCY = 4        # téléchargements simultanés

THREE_VERSION = "0.160.0"
CDN = f"https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/"
CACHE_DIR = pathlib.Path.home() / ".cache" / "glb2html" / f"three@{THREE_VERSION}"

CORE_FILES = {
    "three": "build/three.module.js",
    "three/addons/controls/OrbitControls.js": "examples/jsm/controls/OrbitControls.js",
    "three/addons/loaders/GLTFLoader.js": "examples/jsm/loaders/GLTFLoader.js",
    "three/addons/utils/BufferGeometryUtils.js": "examples/jsm/utils/BufferGeometryUtils.js",
}
DRACO_FILES = {"three/addons/loaders/DRACOLoader.js": "examples/jsm/loaders/DRACOLoader.js"}
DRACO_LIBS = {
    "draco_wasm_wrapper.js": "examples/jsm/libs/draco/gltf/draco_wasm_wrapper.js",
    "draco_decoder.wasm": "examples/jsm/libs/draco/gltf/draco_decoder.wasm",
}
MESHOPT_FILES = {"three/addons/libs/meshopt_decoder.module.js": "examples/jsm/libs/meshopt_decoder.module.js"}


ZONE_TYPES = ("url", "ha", "portal", "spawn")


def _slug(s):
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9_-]+", "-", str(s or "").lower()))[:40]


def clean_zones(zones, profile):
    """Valide les zones ; le profil 'public' retire toutes les zones privées (leurs adresses ne sont jamais écrites dans la page)."""
    def num(v, d, lo, hi):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return d
        return d if not math.isfinite(v) else min(hi, max(lo, v))
    out = []
    for i, z in enumerate(zones if isinstance(zones, list) else []):
        if not isinstance(z, dict):
            continue
        if z.get("private") and profile != "perso":
            continue
        t = z.get("type") if z.get("type") in ZONE_TYPES else "portal"
        out.append({
            "id": _slug(z.get("id")) or f"z{i + 1}", "type": t, "label": str(z.get("label") or "")[:60],
            "x": num(z.get("x"), 0, -1e5, 1e5), "y": num(z.get("y"), 0, -1e5, 1e5), "z": num(z.get("z"), 0, -1e5, 1e5),
            "yaw": num(z.get("yaw"), 0, -7, 7), "shape": "board" if z.get("shape") == "board" else "ring",
            "trigger": (z.get("trigger") if z.get("trigger") in ("click", "enter", "both") else "click") if t == "portal" else "click",
            "radius": num(z.get("radius"), 2, 0.5, 50), "w": num(z.get("w"), 2.4, 0.5, 10), "h": num(z.get("h"), 1.2, 0.3, 6),
            "target": str(z.get("target") or "")[:600], "spawn": _slug(z.get("spawn")),
            "confirm": bool(z.get("confirm")), "private": bool(z.get("private")), "showName": bool(z.get("showName")),
            "mesh": "" if t == "spawn" else re.sub(r"[\x00-\x1f]", "", str(z.get("mesh") or ""))[:200],
        })
    return out


def clean_rotate(v):
    """Rotation de la région : 0, 90, 180 ou 270 degrés (autre valeur : arrondie au quart de tour le plus proche), comme core.js."""
    try:
        return (round(float(v) / 90) * 90) % 360
    except (TypeError, ValueError, OverflowError):
        return 0


def resolve_mesh_ref(names, ref):
    """Indices (dans `names`, noms des objets du modèle dans l'ordre de parcours de three.js : pré-ordre, enfants dans l'ordre du fichier)
    désignés par le champ `mesh` d'une zone. Même règle que resolveMeshRef de core.js : le nom exact d'abord (zones anciennes, nom unique),
    sinon « base#index » = index-ième objet nommé « base ». Liste vide si introuvable."""
    if not ref:
        return []
    exact = [i for i, n in enumerate(names) if n == ref]
    if exact:
        return exact
    m = re.fullmatch(r"(.*)#(\d+)", ref, re.S)
    if not m:
        return []
    same = [i for i, n in enumerate(names) if n == m.group(1)]
    k = int(m.group(2))
    return [same[k]] if k < len(same) else []


def fix_presence_url(u):
    u = str(u or "").strip()
    if not u:
        return u
    if not re.match(r"^wss?://", u, re.I):
        print(f"[AVERTISSEMENT] --presence-url doit commencer par ws:// ou wss:// (reçu : {u})", file=sys.stderr)
        return u
    fixed = re.sub(r"^(wss?://)(0\.0\.0\.0)(?=[:/]|$)", r"\g<1>127.0.0.1", u, flags=re.I)
    if fixed != u:
        print(f"[AVERTISSEMENT] 0.0.0.0 est une adresse d'écoute du serveur, pas une destination : remplacée par 127.0.0.1 -> {fixed}", file=sys.stderr)
    return fixed


def clean_map(entries):
    """Valide les régions de la carte des mondes (adresses http/https ou relatives uniquement, vignettes d'image uniquement)."""
    def ival(v, lo=-1000000, hi=1000000):
        try:
            return max(lo, min(hi, int(float(v))))
        except (TypeError, ValueError):
            return 0
    def okurl(u):
        u = str(u or "").strip()[:600]
        return u if u and (re.match(r"^https?://", u, re.I) or not re.match(r"^[a-z][a-z0-9+.\-]*:", u, re.I)) else ""
    out, seen = [], set()
    for i, r in enumerate(entries if isinstance(entries, list) else []):
        if not isinstance(r, dict):
            continue
        name = str(r.get("name") or "").strip()[:60]
        url = okurl(r.get("url"))
        if not name or not url:
            continue
        thumb = str(r.get("thumb") or "")
        if re.match(r"^data:image/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+$", thumb):
            thumb = thumb if len(thumb) <= 200000 else ""
        else:
            thumb = okurl(thumb) if thumb and not thumb.startswith("data:") else ""
        rid = _slug(r.get("id") or name) or f"r{i + 1}"
        while rid in seen:
            rid += "-2"
        seen.add(rid)
        out.append({"id": rid, "name": name, "url": url, "x": ival(r.get("x")), "y": ival(r.get("y")),
                    "spawn": _slug(r.get("spawn")), "presence": (str(r.get("presence"))[:300] if re.match(r"^wss?://", str(r.get("presence") or ""), re.I) else ""), "room": re.sub(r"[^\w .\-]", "", str(r.get("room") or "")).strip()[:64], "thumb": thumb})
    return out


def find_beside(path):
    """Chemin absolu : tel quel. Relatif : d'abord le dossier de lancement, puis le dossier de ce script."""
    path = pathlib.Path(path).expanduser()
    if path.is_absolute():
        return path if path.is_file() else None
    for base in (pathlib.Path.cwd(), pathlib.Path(__file__).resolve().parent):
        if (base / path).is_file():
            return base / path
    return None


MAP_PAGE_TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>__TITLE__</title>
<style>
[hidden]{display:none!important}
body{margin:0;background:#fff;color:#000;font:14px/1.5 ui-monospace,Consolas,monospace}
main{max-width:1000px;margin:0 auto;padding:20px}
h1{font-size:20px;margin:0 0 4px}
#grid{display:grid;gap:12px;justify-content:start;margin:16px 0}
.tile{box-sizing:border-box;display:flex;flex-direction:column;gap:4px;width:170px;padding:6px;border:2px solid #000;border-radius:8px;background:#fff;color:#000;text-decoration:none}
a.tile:hover{background:#eee}
.tile img,.tile .ph{width:100%;aspect-ratio:1;object-fit:cover;background:#ccc;border:1px solid #000;display:block}
.tile b{word-break:break-word}
.tile small{font-size:11px;word-break:break-all;opacity:.8}
footer{font-size:11px;opacity:.7}
</style>
</head>
<body><main>
<h1>__TITLE__</h1>
<div id="grid"></div>
<footer>glb2html __VERSION__ : chaque carte est un lien qui emmène directement dans la région, à son point d'arrivée.</footer>
</main>
<script type="application/json" id="cfg">__CONFIG__</script>
<script>
(() => {
  const C = JSON.parse(document.getElementById('cfg').textContent);
  let MAP = C.map || [];
  const grid = document.getElementById('grid'), counts = {}; let known = false;
  const srvOf = r => (r.presence || C.presenceUrl || '');
  const okUrl = u => { try { const x = new URL(u, location.href); return (x.protocol === 'http:' || x.protocol === 'https:' || (location.protocol === 'file:' && x.protocol === 'file:')) ? x : null; } catch (e) { return null; } };
  const safeThumb = t => typeof t === 'string' && (/^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+\/=]+$/.test(t) || (!/^[a-z][a-z0-9+.-]*:/i.test(t) || /^https?:/i.test(t)));
  const remap = vals => { const u = [...new Set(vals)].sort((a, b) => a - b), m = new Map(); let pos = 0; u.forEach((v, i) => { if (i) pos += Math.min(v - u[i - 1], 2); m.set(v, pos); }); return m; };
  const draw = () => {
    grid.textContent = '';
    const list = MAP.filter(r => r && r.name);
    const mx = remap(list.map(r => r.x | 0)), my = remap(list.map(r => r.y | 0));
    const cols = list.length ? Math.max(...mx.values()) + 1 : 0, rows = list.length ? Math.max(...my.values()) + 1 : 0;
    const placed = list.length > 0 && new Set(list.map(r => (r.x | 0) + ',' + (r.y | 0))).size === list.length && cols <= 14 && rows <= 14;
    grid.style.gridTemplateColumns = placed ? 'repeat(' + cols + ', 170px)' : 'repeat(auto-fill, 170px)';
    for (const r of list) {
      const u = okUrl(r.url); if (u) u.hash = 'spawn=' + encodeURIComponent(r.spawn || 'default');
      const t = document.createElement(u ? 'a' : 'div'); t.className = 'tile';
      if (u) { t.href = u.href; t.rel = 'noopener'; }
      if (placed) { t.style.gridColumn = String(mx.get(r.x | 0) + 1); t.style.gridRow = String(rows - my.get(r.y | 0)); }
      if (r.thumb && safeThumb(r.thumb)) { const im = document.createElement('img'); im.src = r.thumb; im.alt = ''; im.referrerPolicy = 'no-referrer'; t.append(im); } else { const ph = document.createElement('div'); ph.className = 'ph'; t.append(ph); }
      const b = document.createElement('b'); b.textContent = r.name; t.append(b);
      const n = counts[srvOf(r) + '|' + (r.room || '')];
      const s = document.createElement('span'); s.textContent = 'visiter →' + (known && r.room && srvOf(r) ? ' · ' + (n || 0) + ' en promenade' : ''); t.append(s);
      const l = document.createElement('small'); l.textContent = u ? u.href : '(adresse invalide)'; t.append(l);
      grid.append(t);
    }
    if (!list.length) grid.textContent = 'Aucune région dans la carte.';
  };
  const queryServer = srv => {
    try {
      const ws = new WebSocket(srv), to = setTimeout(() => { try { ws.close(); } catch (e) {} }, 4000);
      ws.onopen = () => ws.send(JSON.stringify({ t: 'rooms' }));
      ws.onmessage = ev => {
        try { const m = JSON.parse(ev.data); if (m.t === 'rooms') { for (const k of Object.keys(counts)) if (k.startsWith(srv + '|')) delete counts[k]; for (const [room, n] of Object.entries(m.rooms || {})) counts[srv + '|' + room] = n; known = true; draw(); } } catch (e) {}
        try { ws.close(); } catch (e) {}
      };
      ws.onclose = () => clearTimeout(to); ws.onerror = () => {};
    } catch (e) {}
  };
  const fetchCounts = () => { for (const srv of new Set(MAP.map(srvOf).filter(Boolean))) queryServer(srv); };
  draw(); fetchCounts(); setInterval(fetchCounts, 10000);
  if (C.mapUrl && /^https?:$/.test(location.protocol)) {
    const urls = String(C.mapUrl).split(',').map(s => s.trim()).filter(Boolean);
    Promise.allSettled(urls.map(u => fetch(new URL(u, location.href).href, { cache: 'no-store' }).then(r => r.ok ? r.json() : Promise.reject(new Error('http ' + r.status))))).then(res => {
      const merged = [], seen = new Set();
      for (const x of res) if (x.status === 'fulfilled' && Array.isArray(x.value)) for (const r of x.value) {
        if (!r || typeof r.name !== 'string' || typeof r.url !== 'string') continue;
        const e = { name: r.name.slice(0, 60), url: r.url.slice(0, 600), x: Number(r.x) | 0, y: Number(r.y) | 0, spawn: String(r.spawn || '').slice(0, 40), room: String(r.room || '').slice(0, 64), presence: /^wss?:\/\//i.test(String(r.presence || '')) ? String(r.presence).slice(0, 300) : '', thumb: safeThumb(r.thumb) ? String(r.thumb).slice(0, 200000) : '' };
        const k = e.url + '|' + e.room; if (!seen.has(k)) { seen.add(k); merged.push(e); }
      }
      if (merged.length) { MAP = merged; draw(); fetchCounts(); }
    });
  }
})();
</script>
</body>
</html>
"""


def data_path(arg):
    """Fichier de données (carte) : chemin relatif -> dossier de lancement s'il y existe, sinon dossier du script (créé là si absent)."""
    p = pathlib.Path(arg).expanduser()
    if p.is_absolute():
        return p
    here = pathlib.Path.cwd() / p
    return here if here.is_file() else pathlib.Path(__file__).resolve().parent / p


def thumb_data_url(arg):
    if re.match(r"^https?://", str(arg), re.I):
        return str(arg)[:600]
    p = find_beside(arg)
    if p is None:
        print(f"[AVERTISSEMENT] vignette introuvable : {arg}", file=sys.stderr)
        return ""
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(p.suffix.lower())
    b = p.read_bytes()
    if not mime or len(b) > 140000:
        print(f"[AVERTISSEMENT] vignette ignorée (jpg/png/webp de 140 Ko maximum attendus) : {p}", file=sys.stderr)
        return ""
    return f"data:{mime};base64," + base64.b64encode(b).decode("ascii")


def register_region(path, entry):
    """Ajoute ou met à jour (par salon) une région dans le fichier de carte ; les champs non fournis gardent leur valeur."""
    data = []
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            sys.exit(f"[ERREUR] {path} illisible ({e})")
    data = [r for r in data if isinstance(r, dict)] if isinstance(data, list) else []
    i = next((k for k, r in enumerate(data) if (r.get("room") and r.get("room") == entry["room"]) or r.get("id") == entry["id"]), None)
    if i is None:
        data.append({"id": entry["id"], "name": entry["name"], "url": entry["url"], "x": 0, "y": 0, "spawn": "", "room": entry["room"], "thumb": ""})
        i = len(data) - 1
    for k, v in entry.items():
        if v is not None and v != "":
            data[i][k] = v
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


def write_map_page(path, entries, presence_url, map_url, title):
    cfg = {"map": clean_map(entries), "mapUrl": str(map_url or "")[:1200], "presenceUrl": fix_presence_url(presence_url)}
    page = (MAP_PAGE_TEMPLATE.replace("__TITLE__", html.escape(title or "Carte des mondes")).replace("__VERSION__", VERSION)
            .replace("__CONFIG__", json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/")))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")
    print(f"[carte] page carte ({len(cfg['map'])} région(s)) -> {path}")


def settings_defaults(S):
    """Valeurs par défaut tirées d'un fichier de réglages enregistré par le viewer (« Enregistrer dans un fichier »)."""
    c = S.get("cfg") if isinstance(S.get("cfg"), dict) else {}
    cam = S.get("camera") if isinstance(S.get("camera"), dict) else {}
    d = {}
    def put(dest, v, conv):
        if v is None:
            return
        try:
            d[dest] = conv(v)
        except (TypeError, ValueError, IndexError):
            pass
    vec = lambda v: tuple(float(x) for x in list(v)[:3]) if len(v) >= 3 else (_ for _ in ()).throw(ValueError())
    for k, dest, conv in (("rotate", "rotate", int), ("hole", "hole", float), ("holeFade", "hole_fade", float), ("holeX", "hole_x", float), ("holeZ", "hole_z", float),
                          ("wave", "wave", float), ("seaY", "sea_y", float), ("seaSegments", "sea_segments", int), ("seaColor", "sea_color", int),
                          ("skyColor", "sky_color", int), ("foliageCutout", "foliage_cutout", float), ("anim", "anim_enabled", bool),
                          ("sea", "sea_enabled", bool), ("retina", "retina", bool), ("walk", "walk", bool), ("eyeHeight", "eye_height", float),
                          ("walkSpeed", "walk_speed", float), ("walkIgnore", "walk_ignore", str), ("names", "names", bool), ("chat", "chat", bool),
                          ("chatFade", "chat_fade", float), ("presenceUrl", "presence_url", str), ("room", "room", str), ("spectate", "spectate", bool),
                          ("panel", "panel", bool), ("mapUrl", "map_url", str)):
        put(dest, c.get(k), conv)
    put("zoom", cam.get("zoom"), float)
    put("cam_dir", cam.get("camDir"), vec)
    put("target", cam.get("target"), vec)
    if S.get("profile") in ("public", "perso"):
        d["profile"] = S["profile"]
    return d


def vendor_bytes(rel: str, vendor_dir: pathlib.Path | None) -> bytes:
    if vendor_dir:
        p = vendor_dir / rel
        if not p.is_file():
            sys.exit(f"[ERREUR] {p} introuvable (--vendor doit pointer sur la racine du paquet npm three)")
        return p.read_bytes()
    p = CACHE_DIR / rel
    if not p.is_file():
        p.parent.mkdir(parents=True, exist_ok=True)
        print(f"[cache] téléchargement {CDN + rel}")
        try:
            with urllib.request.urlopen(CDN + rel, timeout=60) as r:
                data = r.read()
        except Exception as e:
            sys.exit(f"[ERREUR] téléchargement impossible ({e}). Utilise --vendor <dossier three>.")
        p.write_bytes(data)
    return p.read_bytes()


def fix_imports(src: bytes) -> str:
    # les imports relatifs ne se résolvent pas depuis une URL data: (ni depuis lib/ à plat) -> spécificateurs nus de l'importmap
    return src.decode("utf-8").replace("'../utils/BufferGeometryUtils.js'", "'three/addons/utils/BufferGeometryUtils.js'")


def js_data_url(src: bytes) -> str:
    return "data:text/javascript;base64," + base64.b64encode(fix_imports(src).encode("utf-8")).decode("ascii")


def bin_data_url(src: bytes, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(src).decode("ascii")


def inspect_glb(data: bytes, name: str) -> set:
    if len(data) < 20 or data[:4] != b"glTF":
        raise ValueError(f"{name} : pas un GLB (magic absent)")
    version, total = struct.unpack_from("<II", data, 4)
    if version != 2:
        raise ValueError(f"{name} : glTF version {version} non supportée")
    if total != len(data):
        raise ValueError(f"{name} : taille annoncée {total} != taille fichier {len(data)} (tronqué ?)")
    clen, ctype = struct.unpack_from("<II", data, 12)
    if ctype != 0x4E4F534A:
        raise ValueError(f"{name} : premier chunk non JSON")
    gltf = json.loads(data[20:20 + clen].decode("utf-8"))
    used = set(gltf.get("extensionsUsed", [])) | set(gltf.get("extensionsRequired", []))
    ext_refs = [x.get("uri") for x in gltf.get("buffers", []) + gltf.get("images", [])
                if x.get("uri") and not x["uri"].startswith("data:")]
    if ext_refs:
        raise ValueError(f"{name} : référence des fichiers externes {ext_refs[:3]} -> repacker en GLB autonome "
                         f"(npx @gltf-transform/cli copy in.gltf out.glb)")
    if "KHR_texture_basisu" in used:
        raise ValueError(f"{name} : textures KTX2/Basis non gérées hors ligne -> "
                         f"npx @gltf-transform/cli png in.glb out.glb")
    return used


HTML_TEMPLATE = r"""__HTML_TEMPLATE__"""

DRACO_JS = r"""__DRACO_JS__"""

MESHOPT_JS = r"""__MESHOPT_JS__"""


def build_cfg(name: str, *, rotate=ROTATE, hole=HOLE_RADIUS, hole_fade=HOLE_FADE, hole_x=HOLE_X, hole_z=HOLE_Z, wave=WAVE_AMP,
               sea_y=SEA_Y, zoom=ZOOM_RATIO, cam_dir=CAM_DIR, target=TARGET, sea_enabled=SEA_ENABLED,
               anim_enabled=ANIM_ENABLED, retina=RETINA_ENABLED, foliage_cutout=FOLIAGE_CUTOUT,
               sea_color=SEA_COLOR, sky_color=SKY_COLOR, sea_segments=SEA_SEGMENTS, walk=WALK_ENABLED, eye_height=EYE_HEIGHT, walk_speed=WALK_SPEED, walk_ignore=WALK_IGNORE, names=NAMES_ENABLED, presence_url=PRESENCE_URL, room=ROOM, chat=CHAT_ENABLED, chat_fade=CHAT_FADE, zones=None, profile=PROFILE, spectate=SPECTATE, panel=PANEL, zones_live=ZONES_LIVE, map_entries=None, map_url=MAP_URL, modular=False, tiles=None, tile_radius=TILE_RADIUS, tile_margin=TILE_MARGIN, tile_max_mo=TILE_MAX_MO, tile_max_tri=TILE_MAX_TRI, tile_concurrency=TILE_CONCURRENCY) -> dict:
    """Le dictionnaire de réglages `cfg` : identique dans la page autonome et dans <page>.config.json (mode modulaire),
    sauf que le mode modulaire garde les zones hors de la config (fichier <page>.zones.json, relu à chaque ouverture)."""
    presence_url = fix_presence_url(presence_url)
    cfg = {
        "rotate": clean_rotate(rotate), "hole": float(hole), "holeFade": float(hole_fade), "holeX": float(hole_x), "holeZ": float(hole_z), "wave": float(wave), "seaY": float(sea_y),
        "zoom": float(zoom), "camDir": list(map(float, cam_dir)), "target": list(map(float, target)),
        "sea": bool(sea_enabled), "anim": bool(anim_enabled), "retina": bool(retina),
        "foliageCutout": float(foliage_cutout), "seaSize": SEA_SIZE, "seaSegments": int(sea_segments),
        "seaColor": int(sea_color), "skyColor": int(sky_color),
        "walk": bool(walk), "eyeHeight": float(eye_height), "walkSpeed": float(walk_speed), "walkIgnore": str(walk_ignore),
        "names": bool(names), "chat": bool(chat), "profile": profile, "version": VERSION, "panel": bool(panel), "zonesLive": str(zones_live or ""),
        "map": clean_map(json.loads(MAP_JSON) if map_entries is None else map_entries), "mapUrl": str(map_url or "")[:1200], "spectate": bool(presence_url) if spectate is None else bool(spectate),
        "zones": clean_zones(json.loads(ZONES_JSON) if zones is None else zones, profile), "chatFade": float(chat_fade), "presenceUrl": str(presence_url), "room": str(room) or pathlib.Path(name).stem,
    }
    if modular:
        cfg["zones"], cfg["zonesLive"] = [], ""
    if tiles:
        # mode tuiles : clés présentes seulement dans ce cas (sans « tiles », la config est celle d'avant)
        cfg.update({"tiles": str(tiles), "tileRadius": float(tile_radius), "tileMargin": float(tile_margin), "tileMaxMo": float(tile_max_mo),
                    "tileMaxTri": int(tile_max_tri), "tileConcurrency": int(tile_concurrency)})
    return cfg


SHELL_BOOT_OLD = "const C = JSON.parse(document.getElementById('cfg').textContent);"
SHELL_MSG_OLD = '<div id="msg">Chargement…</div>\n'
# script classique : depuis le disque, les modules sont bloqués par le navigateur et le module de la page ne s'exécute jamais
SHELL_MSG_NEW = SHELL_MSG_OLD + """<script>
if (location.protocol === 'file:') document.getElementById('msg').textContent = 'Cette page est en mode modulaire : elle doit être servie en http ou https, pas ouverte depuis le disque. Pour la tester : python -m http.server dans son dossier, puis http://localhost:8000/' + decodeURIComponent(location.pathname.split('/').pop()) + location.search;
</script>
"""
# la coquille ne contient aucun nom : X.html charge X.config.json, X.glb, X.zones.json (puis zones.json) du même dossier
SHELL_BOOT_NEW = """// fichiers frères : par défaut déduits du nom de la page (copier X.html en Y.html et ses frères en Y.* suffit) ;
// avec ?region=NOM, de NOM : une seule coquille peut servir plusieurs régions du même dossier
const BOOT = (() => {
  const fail = raison => { document.getElementById('msg').textContent = 'Erreur : ' + raison; throw new Error(raison); };
  const q = new URLSearchParams(location.search);
  let e;
  if (q.has('region')) {
    // NOM doit être un seul nom de fichier du dossier : jamais d'adresse, de chemin ni de dossier parent (aucune requête avant ce contrôle)
    const nom = (q.get('region') || '').replace(/\\.html?$/i, '');
    if (!nom || /[\\/\\\\:?#\\x00-\\x1f]/.test(nom) || nom.includes('..') || nom.startsWith('.')) fail('paramètre region refusé « ' + nom + ' » (un seul nom de fichier, sans / \\ : ? # ni .., sans point au début)');
    e = encodeURIComponent(nom);
  } else {
    let f = location.pathname.split('/').pop() || '';
    try { f = decodeURIComponent(f); } catch (x) {}
    e = encodeURIComponent(f.replace(/\\.html?$/i, '') || 'index');
  }
  return { config: e + '.config.json', glb: e + '.glb', zones: [e + '.zones.json', 'zones.json'] };
})();
const C = await (async () => {
  const fail = (nom, raison) => { document.getElementById('msg').textContent = 'Erreur : ' + nom + ' introuvable (' + raison + ')'; throw new Error(nom + ' : ' + raison); };
  let r; try { r = await fetch(BOOT.config, { cache: 'no-store' }); } catch (e) { fail(BOOT.config, 'réseau'); }
  if (!r.ok) fail(BOOT.config, 'HTTP ' + r.status);
  const cfg = await r.json();
  // zones relues à chaque ouverture : X.zones.json, sinon zones.json du même dossier, sinon aucune
  cfg.zones = [];
  for (const nom of BOOT.zones) {
    try {
      const rz = await fetch(nom, { cache: 'no-store' }); if (!rz.ok) continue;
      const liste = await rz.json(); if (!Array.isArray(liste)) continue;
      cfg.zones = liste.filter(z => z && (cfg.profile === 'perso' || !z.private)); break;
    } catch (e) {}
  }
  return cfg;
})();
document.title = C.room || document.title;
{ const sky = '#' + (Number(C.skyColor) >>> 0).toString(16).padStart(6, '0'); document.documentElement.style.background = sky; document.body.style.background = sky; }"""
SHELL_CFG_TAG = '<script type="application/json" id="cfg">__CONFIG__</script>\n'
SHELL_GLB_TAG = '<script type="application/octet-stream" id="glb">__GLB_B64__</script>\n'
SHELL_LOAD_OLD = "await viewer.loadBuffer(await b64ToBuffer(document.getElementById('glb').textContent.trim()));"
SHELL_LOAD_NEW = """if (C.tiles) {
    // région en tuiles (X.tiles.json, voir MODE_EMPLOI § 17 bis) : pas de X.glb ; ?rayon=NNN remplace tileRadius (essais)
    const rayon = Number(new URLSearchParams(location.search).get('rayon'));
    await viewer.loadTiles(C.tiles, { spawn: arrival ? (H.get('spawn') || '') : undefined, radius: rayon > 0 ? rayon : undefined });
  } else {
    const rGlb = await fetch(BOOT.glb);
    if (!rGlb.ok) throw new Error(BOOT.glb + ' : HTTP ' + rGlb.status);
    await viewer.loadBuffer(await rGlb.arrayBuffer());
  }"""
SHELL_TITLE_OLD = "<title>__TITLE__</title>"
LIB_REL = "lib/three-" + THREE_VERSION
DRACO_PATH_OLD = "draco.setDecoderPath('');"
SHELL_SKY = "87ceeb"   # fond provisoire, remplacé par skyColor dès que la config est lue
# la coquille connaît tous les modules (Draco et Meshopt compris) : elle ne dépend d'aucun .glb
SHELL_MODULES = {**CORE_FILES, **DRACO_FILES, **MESHOPT_FILES}


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError(f"gabarit modulaire : cible introuvable ou multiple ({old[:50]}…)")
    return text.replace(old, new)


def lib_name(rel):
    return rel.rsplit("/", 1)[-1]


def write_atomic(path: pathlib.Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def write_modular_lib(out_dir: pathlib.Path, vendor_dir):
    """Écrit lib/three-X/ à côté des pages (partagé par toutes les pages du dossier) : modules à plat, imports réécrits,
    Draco et Meshopt toujours présents (la coquille ne sait pas ce que contient le .glb)."""
    lib = out_dir / LIB_REL
    for rel in SHELL_MODULES.values():
        write_atomic(lib / lib_name(rel), fix_imports(vendor_bytes(rel, vendor_dir)).encode("utf-8"))
    for rel in DRACO_LIBS.values():
        write_atomic(lib / "draco" / lib_name(rel), vendor_bytes(rel, vendor_dir))


def shell_lib_files():
    """Contenu attendu de lib/three-X/ pour le viewer : ({spécificateur: nom de fichier}, [fichiers de draco/])."""
    return {spec: lib_name(rel) for spec, rel in SHELL_MODULES.items()}, [lib_name(rel) for rel in DRACO_LIBS.values()]


def modular_names(out_path: pathlib.Path):
    """Fichiers frères de la page modulaire : (glb, config, zones)."""
    return out_path.with_suffix(".glb"), out_path.with_suffix(".config.json"), out_path.with_suffix(".zones.json")


DEFAULT_SHELL = "index.html"


def valid_region_name(name) -> bool:
    """Même règle que la coquille (?region=NOM) : un seul nom de fichier, sans / \\ : ? # ni .., sans point au début."""
    name = re.sub(r"\.html?$", "", str(name or ""), flags=re.I)
    return bool(name) and not re.search(r"[/\\:?#\x00-\x1f]", name) and ".." not in name and not name.startswith(".")


def shell_page_address(shell_name: str, region: str) -> str:
    """Adresse d'une région servie par une coquille commune : COQUILLE.html?region=NOM (le #spawn= s'ajoute après)."""
    return f"{shell_name}?region={urllib.parse.quote(region, safe='')}"


def lib_missing(out_dir: pathlib.Path):
    """Fichiers de lib/three-X/ absents (la coquille commune et les pages déjà publiées les partagent)."""
    mods, draco = shell_lib_files()
    lib = out_dir / LIB_REL
    return [str(lib / n) for n in list(mods.values()) + ["draco/" + n for n in draco] if not (lib / n).is_file()]


def build_shell() -> str:
    """La coquille universelle du mode modulaire : même texte, octet pour octet, pour toutes les régions (le viewer en met
    une copie dans son .zip). Elle charge <nom de la page>.config.json / .glb / .zones.json du même dossier et lib/three-X/.
    Aucun nom, aucun titre, aucune couleur propre à une région n'y est écrit."""
    importmap = {"imports": {spec: f"./{LIB_REL}/{lib_name(rel)}" for spec, rel in SHELL_MODULES.items()}}
    decoders = [replace_once(DRACO_JS.replace("__DRACO_LIBS__", "{}"), DRACO_PATH_OLD, f"draco.setDecoderPath('./{LIB_REL}/draco/');"), MESHOPT_JS]
    tpl = HTML_TEMPLATE
    tpl = replace_once(tpl, SHELL_TITLE_OLD, "<title>Chargement…</title>")
    tpl = replace_once(tpl, SHELL_MSG_OLD, SHELL_MSG_NEW)
    tpl = replace_once(tpl, SHELL_CFG_TAG, "")
    tpl = replace_once(tpl, SHELL_GLB_TAG, "")
    tpl = replace_once(tpl, SHELL_BOOT_OLD, SHELL_BOOT_NEW)
    tpl = replace_once(tpl, SHELL_LOAD_OLD, SHELL_LOAD_NEW)
    out = (tpl.replace("__SKY_HEX__", SHELL_SKY).replace("__IMPORTMAP__", json.dumps(importmap, indent=1))
           .replace("__DECODERS__", "\n".join(decoders)))
    left = re.findall(r"__(?:TITLE|SKY_HEX|IMPORTMAP|CONFIG|DECODERS|GLB_B64|CORE)__", out)
    if left:
        raise RuntimeError(f"coquille modulaire : marqueur(s) non remplacé(s) {sorted(set(left))}")
    return out


def build_html(glb: bytes, name: str, vendor_dir=None, **kw) -> str:
    """Page autonome : GLB en base64, three.js et décodeurs en data:, s'ouvre depuis le disque. (La page modulaire est build_shell.)
    Les réglages kw sont ceux de build_cfg + title."""
    title = kw.pop("title", None)
    cfg = build_cfg(name, **kw)
    hole, wave, sea_y, zoom, sky_color = cfg["hole"], cfg["wave"], cfg["seaY"], cfg["zoom"], cfg["skyColor"]
    used = inspect_glb(glb, name)
    need_draco = "KHR_draco_mesh_compression" in used
    need_meshopt = "EXT_meshopt_compression" in used

    modules = dict(CORE_FILES)
    if need_draco:
        modules.update(DRACO_FILES)
    if need_meshopt:
        modules.update(MESHOPT_FILES)
    importmap = {"imports": {spec: js_data_url(vendor_bytes(rel, vendor_dir)) for spec, rel in modules.items()}}

    decoders = []
    if need_draco:
        libs = {
            "draco_wasm_wrapper.js": bin_data_url(vendor_bytes(DRACO_LIBS["draco_wasm_wrapper.js"], vendor_dir), "text/javascript"),
            "draco_decoder.wasm": bin_data_url(vendor_bytes(DRACO_LIBS["draco_decoder.wasm"], vendor_dir), "application/wasm"),
        }
        decoders.append(DRACO_JS.replace("__DRACO_LIBS__", json.dumps(libs)))
    if need_meshopt:
        decoders.append(MESHOPT_JS)

    title = title or f"{pathlib.Path(name).stem} - trou {hole:g} amp {wave:g} y {sea_y:g} zoom {zoom:.2f}"
    out = (HTML_TEMPLATE
           .replace("__TITLE__", html.escape(title))
           .replace("__SKY_HEX__", f"{int(sky_color):06x}")
           .replace("__IMPORTMAP__", json.dumps(importmap, indent=1))
           .replace("__CONFIG__", json.dumps(cfg).replace("</", "<\\/"))
           .replace("__DECODERS__", "\n".join(decoders)))
    # GLB injecté en dernier : rien n'est rescanné dans les Mo de base64
    return out.replace("__GLB_B64__", base64.b64encode(glb).decode("ascii"))


def live_zones_name(out_path, zones_live):
    return out_path.stem + ".zones.json" if zones_live == "auto" else str(zones_live or "")


def write_live_zones(out_path, kw):
    """Écrit à côté de la page le fichier de zones rechargeable (filtré selon le profil : le profil public n'y met jamais de zone privée)."""
    name = live_zones_name(out_path, kw.get("zones_live"))
    if not name:
        return
    zones = kw.get("zones")
    zones = clean_zones(json.loads(ZONES_JSON) if zones is None else zones, kw.get("profile", PROFILE))
    target = out_path.with_name(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(zones, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[zones] {len(zones)} zone(s), profil {kw.get('profile', PROFILE)} -> {target}")


def zones_given(kw):
    """Vrai si une source de zones a été donnée (--zones, --settings ou ZONES_JSON du script exporté par le viewer)."""
    return kw.get("zones") is not None or bool(json.loads(ZONES_JSON))


def write_modular_zones(zones_path: pathlib.Path, kw):
    """Écrit <page>.zones.json (zones nettoyées, filtrées selon le profil), relu par la page à chaque ouverture."""
    profile = kw.get("profile", PROFILE)
    zones = clean_zones(json.loads(ZONES_JSON) if kw.get("zones") is None else kw["zones"], profile)
    write_atomic(zones_path, json.dumps(zones, ensure_ascii=False, indent=1).encode("utf-8"))
    print(f"[zones] {len(zones)} zone(s), profil {profile} -> {zones_path}")


def write_shell_page(out_path: pathlib.Path, shell, page: str):
    """Écrit la coquille : X.html (modulaire simple) ou COQUILLE.html à côté de la région, jamais écrasée si elle existe et diffère."""
    if shell:
        shell_path = out_path.with_name(shell)
        if not shell_path.is_file():
            write_atomic(shell_path, page.encode("utf-8"))
            print(f"[coquille] {shell_path} écrite")
        elif shell_path.read_bytes() == page.encode("utf-8"):
            print(f"[coquille] {shell_path} déjà présente et identique")
        else:
            print(f"[AVERTISSEMENT] {shell_path} existe et diffère de la coquille de cette version : conservée (les autres régions la partagent). Supprime-la pour la renouveler", file=sys.stderr)
    else:
        write_atomic(out_path, page.encode("utf-8"))


def generate(glb_path: pathlib.Path, out_path: pathlib.Path, vendor_dir, modular=False, shell=None, **kw):
    """shell : nom de la coquille commune (COQUILLE.html). Alors out_path désigne la région (NOM = son nom sans extension) :
    seuls NOM.glb, NOM.config.json et NOM.zones.json sont écrits, plus la coquille et lib/ s'ils sont absents."""
    data = glb_path.read_bytes()
    if shell:
        modular = True
        if not valid_region_name(out_path.stem):
            print(f"[ERREUR] nom de région « {out_path.stem} » refusé par la coquille commune (un seul nom de fichier, sans / \\ : ? # ni .., sans point au début)", file=sys.stderr)
            return False
    if modular:
        if kw.get("title"):
            print("[AVERTISSEMENT] --title est ignoré en mode modulaire : le titre de la page est le salon (--room) de la config", file=sys.stderr)
        if kw.get("zones_live"):
            print("[AVERTISSEMENT] --zones-live est ignoré en mode modulaire : les zones sont toujours relues dans <page>.zones.json", file=sys.stderr)
        kw = dict(kw, zones_live="")
    elif kw.get("zones_live"):
        kw = dict(kw, zones_live=live_zones_name(out_path, kw["zones_live"]))
    try:
        used = inspect_glb(data, glb_path.name)
        page = build_shell() if modular else build_html(data, glb_path.name, vendor_dir, **kw)
    except ValueError as e:
        print(f"[ERREUR] {e}", file=sys.stderr)
        return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if modular:
        glb_out, cfg_out, zones_out = modular_names(out_path)
        if not shell or lib_missing(out_path.parent):
            write_modular_lib(out_path.parent, vendor_dir)
        write_atomic(glb_out, data)
        write_config(cfg_out, glb_path.name, kw)
        # sans source de zones, un X.zones.json existant (peut-être modifié à la main) n'est pas écrasé
        if zones_given(kw) or not zones_out.is_file():
            write_modular_zones(zones_out, kw)
    write_shell_page(out_path, shell, page)
    if not modular:
        write_live_zones(out_path, dict(kw, zones_live=kw.get("zones_live") or ""))
    if shell:
        print(f"[OK] {glb_path.name} -> {glb_out.name} + {cfg_out.name} + {zones_out.name}, coquille commune {shell} ; adresse : {shell_page_address(shell, out_path.stem)} [glb2html {VERSION}]")
    elif modular:
        print(f"[OK] {glb_path.name} -> {out_path} (modulaire : coquille {len(page) / 1024:.0f} Ko + {glb_out.name} {len(data) / 2**20:.2f} Mo + {cfg_out.name} + {zones_out.name} + {LIB_REL}/) [glb2html {VERSION}]")
    else:
        print(f"[OK] {glb_path.name} -> {out_path} ({len(data) / 2**20:.2f} Mo glb, {len(page) / 2**20:.2f} Mo html) [glb2html {VERSION}]")
    return True


def safe_rel_path(p) -> bool:
    """Même règle que la coquille (safeRel) pour un chemin de tuile : relatif, sans .., sans : ? # \\, sans segment vide."""
    p = str(p or "")
    return bool(p) and len(p) < 400 and not re.match(r"[/\\]", p) and not re.search(r"[\\:?#\x00-\x1f]", p) and not any(x in ("", "..") for x in p.split("/"))


def read_tiles_index(path: pathlib.Path):
    """Lit X.tiles.json (écrit par glb2tiles.py) ; arrête avec un message clair si le fichier n'est pas utilisable."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        sys.exit(f"[ERREUR] {path} illisible ({e})")
    tiles = doc.get("tiles") if isinstance(doc, dict) else None
    if not isinstance(tiles, list) or not tiles:
        sys.exit(f"[ERREUR] {path} : liste « tiles » absente ou vide (fichier écrit par glb2tiles.py attendu)")
    for t in tiles:
        ok = isinstance(t, dict) and safe_rel_path(t.get("file")) and str(t["file"]).lower().endswith(".glb")
        for k in ("min", "max"):
            ok = ok and isinstance(t.get(k), list) and len(t[k]) == 3 and all(isinstance(v, (int, float)) and math.isfinite(v) for v in t[k])
        if not ok:
            sys.exit(f"[ERREUR] {path} : entrée de tuile invalide ({str(t)[:120]}) : « file » doit être un chemin relatif .glb (sans .. ni :), « min » et « max » trois nombres")
    ov = doc.get("overview")
    if ov is not None and not (isinstance(ov, dict) and safe_rel_path(ov.get("file")) and str(ov["file"]).lower().endswith(".glb")):
        sys.exit(f"[ERREUR] {path} : « overview » invalide ({str(ov)[:120]}) : « file » doit être un chemin relatif .glb (sans .. ni :)")
    return doc


def tiles_default_target(doc, rotate=0):
    """Cible de caméra par défaut en mode tuiles : centre de l'étendue en X,Z (repère déjà tourné), hauteur 20 m bornée à l'étendue."""
    lo = [min(t["min"][k] for t in doc["tiles"]) for k in range(3)]
    hi = [max(t["max"][k] for t in doc["tiles"]) for k in range(3)]
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    a = math.radians(clean_rotate(rotate))
    return (round(cx * math.cos(a) + cz * math.sin(a), 2), round(min(max(20.0, lo[1]), hi[1]), 2), round(-cx * math.sin(a) + cz * math.cos(a), 2))


def place_tiles(tiles_path: pathlib.Path, doc, page_dir: pathlib.Path):
    """Met X.tiles.json, ses tuiles et sa vue d'ensemble à côté de la page. Rien n'est copié si elles y sont déjà (une région fait plus d'un Go) ;
    sinon copie, fichier par fichier, ce qui manque ou a une autre taille. Rend le chemin relatif de X.tiles.json depuis la page."""
    src, dst = tiles_path.resolve().parent, page_dir.resolve()
    files = [t["file"] for t in doc["tiles"]]
    ov = doc.get("overview")
    ov_file = ov["file"] if isinstance(ov, dict) else None
    absent = [f for f in files if not (src / f).is_file()]
    if absent:
        print(f"[AVERTISSEMENT] {len(absent)} tuile(s) listée(s) dans {tiles_path.name} introuvable(s) à côté de lui (première : {absent[0]}) ; la page les signalera et réessaiera", file=sys.stderr)
    if ov_file and not (src / ov_file).is_file():
        print(f"[AVERTISSEMENT] vue d'ensemble {ov_file} introuvable à côté de {tiles_path.name} ; la page fonctionnera sans elle", file=sys.stderr)
    ov_txt = f" ; vue d'ensemble {ov_file} placée avec les tuiles" if ov_file else ""
    if src == dst:
        print(f"[tuiles] {len(files)} tuile(s) et {tiles_path.name} déjà à côté de la page : rien n'est copié{ov_txt}")
        return tiles_path.name
    copied = same = size = 0
    for f in files + ([ov_file] if ov_file else []):
        a, b = src / f, dst / f
        if not a.is_file():
            continue
        if b.is_file() and b.stat().st_size == a.stat().st_size:
            same += 1 if f != ov_file else 0
            continue
        b.parent.mkdir(parents=True, exist_ok=True)
        tmp = b.with_name(b.name + ".tmp")
        shutil.copyfile(a, tmp)
        tmp.replace(b)
        if f != ov_file:
            copied += 1
        size += a.stat().st_size
    write_atomic(dst / tiles_path.name, tiles_path.read_bytes())
    print(f"[tuiles] {tiles_path.name} copié dans {dst} ; tuiles : {copied} copiée(s) ({size / 2**20:.1f} Mo), {same} déjà présente(s) de même taille (ni vérifiées ni recopiées){ov_txt}")
    return tiles_path.name


def generate_tiles(tiles_path: pathlib.Path, doc, out_path: pathlib.Path, vendor_dir, shell=None, **kw):
    """Région en tuiles : comme generate() en mode modulaire, mais sans .glb : écrit X.config.json (champ « tiles »), X.zones.json,
    la coquille et lib/ ; X.tiles.json et ses tuiles ne sont copiés que s'ils ne sont pas déjà à côté de la page."""
    if shell and not valid_region_name(out_path.stem):
        print(f"[ERREUR] nom de région « {out_path.stem} » refusé par la coquille commune (un seul nom de fichier, sans / \\ : ? # ni .., sans point au début)", file=sys.stderr)
        return False
    if kw.get("title"):
        print("[AVERTISSEMENT] --title est ignoré en mode modulaire : le titre de la page est le salon (--room) de la config", file=sys.stderr)
    if kw.get("zones_live"):
        print("[AVERTISSEMENT] --zones-live est ignoré en mode modulaire : les zones sont toujours relues dans <page>.zones.json", file=sys.stderr)
    kw = dict(kw, zones_live="")
    page = build_shell()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    kw["tiles"] = place_tiles(tiles_path, doc, out_path.parent)
    _, cfg_out, zones_out = modular_names(out_path)
    if not shell or lib_missing(out_path.parent):
        write_modular_lib(out_path.parent, vendor_dir)
    write_config(cfg_out, out_path.stem, kw)
    if zones_given(kw) or not zones_out.is_file():
        write_modular_zones(zones_out, kw)
    write_shell_page(out_path, shell, page)
    n = len(doc["tiles"])
    if any(z.get("mesh") for z in clean_zones(json.loads(ZONES_JSON) if kw.get("zones") is None else kw["zones"], kw.get("profile", PROFILE))):
        if doc.get("nodeRefs"):
            print("[tuiles] des zones sont liées à un objet (champ mesh) : la page les place avec l'objet dès que la tuile qui le contient est chargée")
        else:
            print(f"[AVERTISSEMENT] des zones sont liées à un élément du modèle (champ mesh), mais {tiles_path.name} a été écrit sans références d'objets (glb2tiles avant la v32) : "
                  "ces zones seront ignorées par la page (avertissement en console). Refaire le découpage avec glb2tiles v32 pour en profiter.", file=sys.stderr)
    adr = shell_page_address(shell, out_path.stem) if shell else out_path.name
    print(f"[OK] {n} tuile(s) -> {cfg_out.name} + {zones_out.name}, " + (f"coquille commune {shell} ; adresse : {adr}" if shell else f"coquille {out_path.name}") + f" [glb2html {VERSION}]")
    return True


def write_config(cfg_path: pathlib.Path, name: str, kw):
    """Écrit <page>.config.json = le dictionnaire cfg de la page modulaire (carte comprise, zones exclues), JSON sans BOM."""
    cfg = build_cfg(name, **{k: v for k, v in kw.items() if k != "title"}, modular=True)
    write_atomic(cfg_path, json.dumps(cfg, ensure_ascii=False, indent=1).encode("utf-8"))
    return cfg


def vec3(s: str):
    v = tuple(float(x) for x in s.split(","))
    if len(v) != 3:
        raise argparse.ArgumentTypeError("format attendu : x,y,z")
    return v


def hexcolor(s: str) -> int:
    return int(s.lstrip("#"), 16)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def region_entry(a, S_reg, room, stem, page_name):
    """Fiche de région pour --register avec page (options --region-* > fichier de réglages > défauts)."""
    use_reg = bool(S_reg.get("name") and S_reg.get("url"))
    entry = {"id": _slug(room) or "region", "name": a.region_name or (S_reg.get("name") if use_reg else "") or stem,
             "url": a.region_url or (S_reg.get("url") if use_reg else "") or page_name, "room": room,
             "spawn": a.region_spawn or ((S_reg.get("spawn") if use_reg and S_reg.get("spawn") != "default" else None)) or None,
             "thumb": thumb_data_url(a.thumb) if a.thumb else (S_reg.get("thumb") if use_reg and str(S_reg.get("thumb") or "").startswith("data:image/") else ""),
             "presence": fix_presence_url(a.presence_url) if a.presence_url else None}
    if not a.region_xy and use_reg:
        try:
            entry["x"], entry["y"] = int(S_reg.get("x", 0)), int(S_reg.get("y", 0))
        except (TypeError, ValueError):
            pass
    if a.region_xy:
        try:
            x, y = (int(float(v)) for v in a.region_xy.split(","))
            entry["x"], entry["y"] = x, y
        except ValueError:
            sys.exit("[ERREUR] --region-xy attend deux nombres : X,Y")
    return entry


def page_name_of(a, out):
    """Adresse relative de la région pour la carte : la page elle-même, ou COQUILLE.html?region=NOM avec une coquille commune."""
    return shell_page_address(a.shared_shell, out.stem) if a.shared_shell else out.name


def main():
    ap = argparse.ArgumentParser(description="GLB -> HTML autonome hors ligne (three.js intégré)")
    ap.add_argument("--version", action="version", version=f"glb2html {VERSION}")
    ap.add_argument("input", nargs="?", help="fichier .glb ou dossier de .glb")
    ap.add_argument("--zones-live", nargs="?", const="auto", default=(ZONES_LIVE or None), metavar="NOM", help="la page recharge ses zones à chaque ouverture depuis un fichier .zones.json placé à côté d'elle (servie en http/https ; sinon les zones intégrées servent). Sans NOM : <page>.zones.json. Le fichier est écrit par le script, filtré selon --profile")
    ap.add_argument("--zones-only", action="store_true", help="réécrit seulement les zones, sans régénérer le HTML : <page>.zones.json d'une page modulaire déjà générée (avec --zones FICHIER), ou, avec --zones-live, le fichier de zones d'une page autonome")
    ap.add_argument("-o", "--output", help="sortie : fichier .html, ou dossier (créé si besoin). Entrée dossier : dossier de sortie. Défaut : \"<nom> - Offline.html\" à côté du .glb")
    ap.add_argument("--rotate", type=int, choices=(0, 90, 180, 270), default=ROTATE, help="rotation de la région autour de l'axe vertical (0, 90, 180 ou 270 degrés), appliquée au chargement avant le recentrage. Les zones, arrivées, cible et trou du fichier de zones / de réglages sont DÉJÀ dans le repère tourné (le viewer les fait tourner avec la région)")
    ap.add_argument("--hole", type=float, default=HOLE_RADIUS, help="rayon du trou 30..600 (zone plate = rayon - fondu)")
    ap.add_argument("--hole-fade", type=float, default=HOLE_FADE, help="demi-largeur du fondu du trou")
    ap.add_argument("--hole-x", type=float, default=HOLE_X, help="position X du centre du trou (monde)")
    ap.add_argument("--hole-z", type=float, default=HOLE_Z, help="position Z du centre du trou (monde)")
    ap.add_argument("--wave", type=float, default=WAVE_AMP, help="amplitude vagues 0..10")
    ap.add_argument("--sea-y", type=float, default=SEA_Y, help="hauteur mer -150..60")
    ap.add_argument("--zoom", type=float, default=ZOOM_RATIO, help="ratio de cadrage (1 = cadrage auto)")
    ap.add_argument("--cam-dir", type=vec3, default=CAM_DIR, help="direction caméra x,y,z")
    ap.add_argument("--target", type=vec3, default=TARGET, help="cible caméra x,y,z")
    ap.add_argument("--foliage-cutout", type=float, default=FOLIAGE_CUTOUT, help="seuil alpha feuillage 0..0.5")
    ap.add_argument("--sea-color", type=hexcolor, default=SEA_COLOR, help="couleur mer, ex 3a9ad9")
    ap.add_argument("--sky-color", type=hexcolor, default=SKY_COLOR, help="couleur ciel, ex 87ceeb")
    ap.add_argument("--sea-segments", type=int, default=SEA_SEGMENTS, help="finesse du maillage de la mer 8..1000 (maille = 4000/segments ; seulement avec --anim)")
    ap.add_argument("--walk", action=argparse.BooleanOptionalAction, default=WALK_ENABLED, help="inclure le mode promenade (touche F) dans la page")
    ap.add_argument("--eye-height", type=float, default=EYE_HEIGHT, help="hauteur des yeux en m (promenade)")
    ap.add_argument("--walk-speed", type=float, default=WALK_SPEED, help="vitesse de marche en m/s (Maj = x2.2)")
    ap.add_argument("--walk-ignore", default=WALK_IGNORE, help='noms à ignorer en collision, séparés par des virgules : "door" = début de mot, "=mesh_346_5" = nom exact ; "" = rien')
    ap.add_argument("--names", action=argparse.BooleanOptionalAction, default=NAMES_ENABLED, help="afficher le nom de l'élément cliqué")
    ap.add_argument("--presence-url", default=PRESENCE_URL, help="serveur de présence ws:// ou wss:// (voir presence_server.py) ; vide = désactivé")
    ap.add_argument("--chat", action=argparse.BooleanOptionalAction, default=CHAT_ENABLED, help="chat entre visiteurs (nécessite --presence-url ; touche Entrée en promenade)")
    ap.add_argument("--chat-fade", type=float, default=CHAT_FADE, help="secondes avant disparition des messages et bulles ; 0 = restent jusqu'à ce que de nouveaux messages les remplacent")
    ap.add_argument("--zones", type=pathlib.Path, help="fichier .json de zones exporté par le viewer ; chemin relatif : cherché dans le dossier de lancement, puis dans le dossier du script. Une zone peut porter un champ mesh (nom exact d'un élément du modèle) : l'élément devient cliquable")
    ap.add_argument("--profile", choices=("public", "perso"), default=PROFILE, help="public : retire les zones privées (ex. Home Assistant) ; perso : les garde")
    ap.add_argument("--spectate", action=argparse.BooleanOptionalAction, default=SPECTATE, help="voir les visiteurs en promenade depuis la vue globale (se connecte dès l'ouverture de la page ; actif par défaut dès qu'une --presence-url est donnée ; --no-spectate pour l'éviter)")
    ap.add_argument("--panel", action=argparse.BooleanOptionalAction, default=PANEL, help="panneau de réglages pour les visiteurs (haute résolution, mer animée, force des vagues), bouton en haut à droite")
    ap.add_argument("--map", type=pathlib.Path, help="fichier regions.json (carte des mondes : nom, adresse, position, vignette) exporté par le viewer ; chemin relatif : dossier de lancement, puis dossier du script")
    ap.add_argument("--map-url", default=MAP_URL, help="adresse(s) de regions.json partagé(s), séparées par des virgules : la page les relit à chaque ouverture (http/https), les fusionne et complète avec la carte intégrée. Un autre site doit autoriser l'accès (CORS)")
    ap.add_argument("--register", help="fichier regions.json à mettre à jour avec CETTE région (ajoutée ou mise à jour par salon) ; relatif : dossier de lancement s'il y existe, sinon dossier du script. La page générée embarque la carte à jour")
    ap.add_argument("--region-name", help="nom affiché dans la carte (défaut : nom du .glb)")
    ap.add_argument("--region-url", help="adresse de la page de cette région (défaut : le nom du fichier .html, relatif)")
    ap.add_argument("--region-xy", metavar="X,Y", help="position sur la grille, comme OpenSim (X vers l'est, Y vers le nord), ex. 1000,1001")
    ap.add_argument("--region-spawn", help="identifiant du point d'arrivée des visiteurs dans cette région (défaut : default)")
    ap.add_argument("--thumb", help="vignette de la région : fichier jpg/png/webp de 140 Ko maximum (intégré), ou adresse http(s) (gardée telle quelle, carte plus légère)")
    ap.add_argument("--map-page", metavar="FICHIER.html", help="génère aussi une page web « carte des mondes » (liens cliquables vers chaque région) ; sans .glb : génère seulement cette page depuis --map. Relatif : à côté de la page de la région")
    ap.add_argument("--settings", nargs="?", const="auto", default=None, metavar="FICHIER", help="reprend TOUS les réglages enregistrés par le viewer (bouton « Enregistrer dans un fichier » : trou, vagues, caméra, zones, fiche de région, vignette…). Sans nom : <nom du .glb>.reglages.json. Les options de la ligne de commande l'emportent. Relatif : dossier de lancement, puis dossier du script")
    ap.add_argument("--modular", action="store_true", help="mode modulaire : écrit une coquille <page>.html identique pour toutes les régions (elle déduit ses fichiers de son nom) + <page>.glb (octets bruts) + <page>.config.json (réglages) + <page>.zones.json (zones, relues à chaque ouverture ; à défaut zones.json du dossier) + lib/three-X/ partagé (Draco et Meshopt compris). Demande http(s) pour l'ouverture (pas depuis le disque)")
    ap.add_argument("--shared-shell", nargs="?", const=DEFAULT_SHELL, default=None, metavar="COQUILLE.html", help=f"mode modulaire à coquille commune : une seule coquille (défaut {DEFAULT_SHELL}) sert plusieurs régions du même dossier, à l'adresse COQUILLE.html?region=NOM. -o désigne la région (NOM = son nom sans extension, ex. -o Ankh.html) : seuls NOM.glb, NOM.config.json et NOM.zones.json sont écrits, plus la coquille et lib/three-X/ s'ils sont absents (une coquille existante n'est jamais écrasée). --register écrit cette adresse dans regions.json. Implique --modular")
    ap.add_argument("--tiles", type=pathlib.Path, metavar="X.tiles.json", help="région découpée en tuiles par glb2tiles.py : pas de .glb en entrée ; -o désigne la région. Écrit X.config.json (champ « tiles »), X.zones.json, la coquille et lib/ ; X.tiles.json et ses tuiles ne sont copiés que s'ils ne sont pas déjà à côté de la page. Implique --modular. Repère = celui du modèle d'origine (aucun recentrage) ; zones liées à un objet : possibles si les tuiles viennent de glb2tiles v32, ignorées sinon")
    ap.add_argument("--tile-radius", type=float, default=TILE_RADIUS, help="m : charger les tuiles dont la boîte est à moins de ce rayon de l'avatar, en plan X,Z (défaut %(default)g ; ?rayon=NNN dans l'adresse pour essayer)")
    ap.add_argument("--tile-margin", type=float, default=TILE_MARGIN, help="m : décharger les tuiles au-delà de rayon + marge (défaut %(default)g)")
    ap.add_argument("--tile-max-mo", type=float, default=TILE_MAX_MO, help="Mo de tuiles chargées en même temps (poids des fichiers ; défaut %(default)g) ; au-delà, les plus lointaines partent d'abord")
    ap.add_argument("--tile-max-tri", type=int, default=TILE_MAX_TRI, help="triangles de tuiles chargées en même temps (défaut %(default)d)")
    ap.add_argument("--tile-concurrency", type=int, default=TILE_CONCURRENCY, help="téléchargements simultanés (défaut %(default)d)")
    ap.add_argument("--config-only", action="store_true", help="réécrit seulement <page>.config.json d'une page modulaire déjà générée (indiquée par -o), sans toucher au .glb ni à la coquille ; les visiteurs rechargent. <page>.zones.json n'est réécrit que si --zones est donné. Avec --register, met aussi la carte à jour")
    ap.add_argument("--room", default=ROOM, help="salon de présence (défaut : nom du fichier)")
    ap.add_argument("--sea", dest="sea_enabled", action=argparse.BooleanOptionalAction, default=SEA_ENABLED)
    ap.add_argument("--anim", dest="anim_enabled", action=argparse.BooleanOptionalAction, default=ANIM_ENABLED)
    ap.add_argument("--retina", action=argparse.BooleanOptionalAction, default=RETINA_ENABLED, help="haute résolution : rendu x2 minimum (supersampling, plus net mais ~4x plus lourd)")
    ap.add_argument("--title", help="titre de la page")
    ap.add_argument("--vendor", type=pathlib.Path, help="racine d'un paquet npm three local (sinon cache + téléchargement)")
    a = ap.parse_args()
    S = {}
    if a.settings:
        if str(a.settings).lower().endswith((".glb", ".gltf")) and not a.input:
            a.input, a.settings = a.settings, "auto"
        if a.settings == "auto":
            if not a.input:
                sys.exit("[ERREUR] --settings sans nom demande le .glb (le fichier cherché est <nom du .glb>.reglages.json)")
            wanted = pathlib.Path(a.input).stem + ".reglages.json"
        else:
            wanted = a.settings
        sp = find_beside(wanted)
        if sp is None:
            sys.exit(f"[ERREUR] fichier de réglages {wanted} introuvable (cherché dans {pathlib.Path.cwd()} puis dans {pathlib.Path(__file__).resolve().parent})")
        try:
            S = json.loads(sp.read_text(encoding="utf-8"))
            if not isinstance(S, dict) or not isinstance(S.get("cfg"), dict):
                raise ValueError("ce n'est pas un fichier de réglages du viewer")
        except (OSError, ValueError) as e:
            sys.exit(f"[ERREUR] {sp} illisible ({e})")
        defaults = settings_defaults(S)
        ap.set_defaults(**defaults)
        keep_input = a.input
        a = ap.parse_args()
        if str(a.settings).lower().endswith((".glb", ".gltf")) and not a.input:
            a.input, a.settings = a.settings, "auto"
        if not a.input:
            a.input = keep_input
        print(f"[réglages] {len(defaults)} paramètre(s) repris de {sp}")
    if a.shared_shell:
        if "/" in a.shared_shell or "\\" in a.shared_shell or not a.shared_shell.lower().endswith((".html", ".htm")):
            sys.exit(f"[ERREUR] --shared-shell attend un nom de fichier .html sans dossier (reçu « {a.shared_shell} »)")
        a.modular = True
    S_reg = S.get("thisReg") if isinstance(S.get("thisReg"), dict) else {}
    S_cmd = S.get("cmd") if isinstance(S.get("cmd"), dict) else {}
    if S and not a.output and S_cmd.get("dest"):
        a.output = S_cmd["dest"]
    if S and not a.map_page and S_cmd.get("mapPage"):
        a.map_page = S_cmd["mapPage"]

    map_arg = None
    if a.map:
        mf = find_beside(a.map)
        if mf is None:
            sys.exit(f"[ERREUR] {a.map} introuvable (cherché dans {pathlib.Path.cwd()} puis dans {pathlib.Path(__file__).resolve().parent})")
        try:
            map_arg = json.loads(mf.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            sys.exit(f"[ERREUR] {mf} illisible ({e})")
        print(f"[carte] {len(clean_map(map_arg))} région(s) lue(s) dans {mf}")
    zones_arg = S.get("zones") if (S and not a.zones and isinstance(S.get("zones"), list)) else None
    if a.zones:
        zf = find_beside(a.zones)
        if zf is None:
            sys.exit(f"[ERREUR] {a.zones} introuvable (cherché dans {pathlib.Path.cwd()} puis dans {pathlib.Path(__file__).resolve().parent})")
        try:
            zones_arg = json.loads(zf.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            sys.exit(f"[ERREUR] {zf} illisible ({e})")
        print(f"[zones] {len(zones_arg) if isinstance(zones_arg, list) else 0} zone(s) lue(s) dans {zf}")

    kw = dict(rotate=a.rotate, hole=clamp(a.hole, 30, 600), hole_fade=max(0.0, a.hole_fade), hole_x=a.hole_x, hole_z=a.hole_z, wave=clamp(a.wave, 0, 10),
              sea_y=clamp(a.sea_y, -150, 60), zoom=clamp(a.zoom, 0.05, 100), cam_dir=a.cam_dir, target=a.target,
              foliage_cutout=clamp(a.foliage_cutout, 0, 1), sea_color=a.sea_color, sky_color=a.sky_color, sea_segments=int(clamp(a.sea_segments, 8, 1000)), walk=a.walk, walk_ignore=a.walk_ignore, zones_live=a.zones_live or "", map_entries=map_arg, map_url=a.map_url, names=a.names, presence_url=a.presence_url, room=a.room, chat=a.chat, chat_fade=clamp(a.chat_fade, 0, 3600), zones=zones_arg, profile=a.profile, spectate=a.spectate, panel=a.panel, eye_height=clamp(a.eye_height, 0.3, 5), walk_speed=clamp(a.walk_speed, 0.5, 30),
              sea_enabled=a.sea_enabled, anim_enabled=a.anim_enabled, retina=a.retina, title=a.title)

    if a.zones_live and not a.input and str(a.zones_live).lower().endswith((".glb", ".gltf")):
        a.input, a.zones_live = a.zones_live, "auto"
        kw["zones_live"] = "auto"
    if a.zones_only:
        if not a.output:
            sys.exit("[ERREUR] --zones-only demande -o <page.html>")
        out = pathlib.Path(a.output)
        if a.zones_live:   # page autonome qui recharge ses zones
            write_live_zones(out, dict(kw, zones_live=a.zones_live))
            sys.exit(0)
        if not out.suffix:
            out = out.with_suffix(".html")
        if not (modular_names(out)[1].is_file() or a.modular):
            sys.exit(f"[ERREUR] --zones-only demande --zones-live (page autonome) ou une page modulaire déjà générée ({modular_names(out)[1].name} introuvable à côté de la page)")
        if zones_arg is None:
            sys.exit("[ERREUR] --zones-only demande --zones FICHIER (ou --settings) : aucune zone à écrire")
        write_modular_zones(modular_names(out)[2], kw)
        sys.exit(0)
    if a.config_only and not a.tiles:
        if not a.output:
            sys.exit("[ERREUR] --config-only demande -o <page.html> (la page modulaire déjà générée)")
        out = pathlib.Path(a.output)
        if not out.suffix:
            out = out.with_suffix(".html")
        glb_out, cfg_out, zones_out = modular_names(out)
        if a.shared_shell:
            if not glb_out.is_file() or not out.with_name(a.shared_shell).is_file():
                sys.exit(f"[ERREUR] {a.shared_shell} ou {glb_out.name} introuvable : génère d'abord la région avec --shared-shell")
        elif not out.is_file() or not glb_out.is_file():
            sys.exit(f"[ERREUR] {out} ou {glb_out.name} introuvable : génère d'abord la page avec --modular")
        name = pathlib.Path(a.input).name if a.input else glb_out.name
        if not a.room and cfg_out.is_file():
            try:
                kw["room"] = str(json.loads(cfg_out.read_text(encoding="utf-8")).get("room") or "")
            except (OSError, ValueError):
                pass
        if a.register:
            entry = region_entry(a, S_reg, kw["room"] or pathlib.Path(name).stem, pathlib.Path(name).stem, page_name_of(a, out))
            reg = data_path(a.register)
            kw["map_entries"] = register_region(reg, entry)
            print(f"[carte] « {entry['name']} » ajoutée ou mise à jour dans {reg} ({len(kw['map_entries'])} région(s))")
        write_config(cfg_out, name, kw)
        print(f"[OK] réglages -> {cfg_out} (coquille et .glb inchangés) [glb2html {VERSION}]")
        if a.zones:   # les zones ne sont touchées que si --zones est donné
            write_modular_zones(zones_out, kw)
        else:
            print(f"[zones] {zones_out.name} non modifié (donne --zones FICHIER pour le réécrire)")
        if a.map_page and kw.get("map_entries") is not None and clean_map(kw["map_entries"]):
            mp = pathlib.Path(a.map_page)
            write_map_page(mp if mp.is_absolute() else out.parent / mp, kw["map_entries"], kw.get("presence_url", ""), kw.get("map_url", ""), a.title or "Carte des mondes")
        sys.exit(0)
    if a.tiles:
        if a.input:
            sys.exit("[ERREUR] --tiles remplace le .glb : ne donne pas de fichier .glb avec --tiles")
        if not a.output:
            sys.exit("[ERREUR] --tiles demande -o <Region.html> (son nom sans extension est celui de la région)")
        out = pathlib.Path(a.output)
        if out.is_dir() or str(a.output).endswith(("/", "\\")):
            sys.exit("[ERREUR] avec --tiles, -o désigne la région (ex. -o Region.html), pas un dossier")
        if not out.suffix:
            out = out.with_suffix(".html")
        tp = find_beside(a.tiles)
        if tp is None:
            sys.exit(f"[ERREUR] {a.tiles} introuvable (cherché dans {pathlib.Path.cwd()} puis dans {pathlib.Path(__file__).resolve().parent})")
        tdoc = read_tiles_index(tp)
        if a.target == TARGET:
            kw["target"] = tiles_default_target(tdoc, a.rotate)
            print(f"[tuiles] cible de caméra par défaut : {kw['target']} (centre de l'étendue, repère du modèle d'origine ; --target pour la changer)")
        if a.sea_y == SEA_Y:
            kw["sea_y"] = 20.0
            print("[tuiles] hauteur de la mer par défaut : 20 m (repère du modèle d'origine, comme l'eau d'OpenSim ; --sea-y pour la changer, --no-sea pour la retirer)")
        kw.update(tile_radius=clamp(a.tile_radius, 10, 5000), tile_margin=clamp(a.tile_margin, 0, 5000), tile_max_mo=clamp(a.tile_max_mo, 1, 100000),
                  tile_max_tri=int(clamp(a.tile_max_tri, 1000, 10**9)), tile_concurrency=int(clamp(a.tile_concurrency, 1, 16)))
        if a.shared_shell and not valid_region_name(out.stem):
            sys.exit(f"[ERREUR] nom de région « {out.stem} » refusé par la coquille commune (un seul nom de fichier, sans / \\ : ? # ni .., sans point au début) : choisis un autre -o")
        if a.register:
            entry = region_entry(a, S_reg, a.room or out.stem, out.stem, page_name_of(a, out))
            reg = data_path(a.register)
            kw["map_entries"] = register_region(reg, entry)
            print(f"[carte] « {entry['name']} » ajoutée ou mise à jour dans {reg} ({len(kw['map_entries'])} région(s))")
        ok = generate_tiles(tp, tdoc, out, a.vendor, shell=a.shared_shell, **kw)
        if ok and a.map_page:
            entries = kw["map_entries"] if kw.get("map_entries") is not None else json.loads(MAP_JSON)
            if clean_map(entries):
                mp = pathlib.Path(a.map_page)
                write_map_page(mp if mp.is_absolute() else out.parent / mp, entries, kw.get("presence_url", ""), kw.get("map_url", ""), a.title or "Carte des mondes")
            else:
                print("[AVERTISSEMENT] --map-page ignoré : aucune région à afficher (donne --register ou --map)", file=sys.stderr)
        sys.exit(0 if ok else 1)
    if a.register and not a.input:
        if not (a.region_name and a.region_url and a.room):
            sys.exit("[ERREUR] enregistrer une région sans .glb demande --region-name, --region-url et --room")
        entry = {"id": _slug(a.room) or "region", "name": a.region_name, "url": a.region_url, "room": a.room,
                 "spawn": a.region_spawn or None, "thumb": thumb_data_url(a.thumb) if a.thumb else "",
                 "presence": fix_presence_url(a.presence_url) if a.presence_url else None}
        if a.region_xy:
            try:
                x, y = (int(float(v)) for v in a.region_xy.split(","))
                entry["x"], entry["y"] = x, y
            except ValueError:
                sys.exit("[ERREUR] --region-xy attend deux nombres : X,Y")
        reg = data_path(a.register)
        data = register_region(reg, entry)
        print(f"[carte] « {entry['name']} » ajoutée ou mise à jour dans {reg} ({len(data)} région(s))")
        if a.map_page:
            write_map_page(pathlib.Path(a.map_page), data, a.presence_url, a.map_url, a.title or "Carte des mondes")
        sys.exit(0)
    if a.map_page and not a.input:
        entries = map_arg if map_arg is not None else json.loads(MAP_JSON)
        if not clean_map(entries):
            sys.exit("[ERREUR] aucune région à afficher : donne --map regions.json")
        write_map_page(pathlib.Path(a.map_page), entries, a.presence_url, a.map_url, a.title or "Carte des mondes")
        sys.exit(0)
    if not a.input:
        ap.error("le fichier .glb (ou le dossier) est obligatoire")
    inp = pathlib.Path(a.input)
    if inp.is_dir() and (a.register or a.map_page):
        print("[AVERTISSEMENT] --register et --map-page ne s'appliquent qu'à un fichier .glb, pas à un dossier", file=sys.stderr)
    if inp.is_dir():
        files = sorted(p for p in inp.iterdir() if p.suffix.lower() == ".glb")
        if not files:
            sys.exit(f"Aucun .glb dans {inp}")
        outdir = pathlib.Path(a.output) if a.output else None
        ok = sum(generate(f, (outdir or f.parent) / (f.stem + (".html" if a.shared_shell else " - Offline.html")), a.vendor, modular=a.modular, shell=a.shared_shell, **kw) for f in files)
        print(f"{ok}/{len(files)} fichiers générés")
        sys.exit(0 if ok == len(files) else 1)
    if not inp.is_file():
        sys.exit(f"{inp} introuvable")
    if inp.suffix.lower() == ".gltf":
        sys.exit("Entrée .gltf : repacker d'abord en .glb (npx @gltf-transform/cli copy in.gltf out.glb)")
    if a.output:
        out = pathlib.Path(a.output)
        if out.is_dir() or str(a.output).endswith(("/", "\\")):
            out = out / (inp.stem + (".html" if a.shared_shell else " - Offline.html"))
        elif not out.suffix:
            out = out.with_suffix(".html")
    else:
        out = inp.with_name(inp.stem + (".html" if a.shared_shell else " - Offline.html"))
    if a.shared_shell and not valid_region_name(out.stem):
        sys.exit(f"[ERREUR] nom de région « {out.stem} » refusé par la coquille commune (un seul nom de fichier, sans / \\ : ? # ni .., sans point au début) : choisis un autre -o")
    if a.register:
        entry = region_entry(a, S_reg, a.room or inp.stem, inp.stem, page_name_of(a, out))
        reg = data_path(a.register)
        kw["map_entries"] = register_region(reg, entry)
        print(f"[carte] « {entry['name']} » ajoutée ou mise à jour dans {reg} ({len(kw['map_entries'])} région(s))")
    ok = generate(inp, out, a.vendor, modular=a.modular, shell=a.shared_shell, **kw)
    if ok and a.map_page:
        entries = kw["map_entries"] if kw.get("map_entries") is not None else json.loads(MAP_JSON)
        if not clean_map(entries):
            print("[AVERTISSEMENT] --map-page ignoré : aucune région à afficher (donne --register ou --map)", file=sys.stderr)
        else:
            mp = pathlib.Path(a.map_page)
            write_map_page(mp if mp.is_absolute() else out.parent / mp, entries, kw.get("presence_url", ""), kw.get("map_url", ""), a.title or "Carte des mondes")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
