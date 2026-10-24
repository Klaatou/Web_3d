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
import time
import sys
import urllib.parse
import urllib.request

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
LIGHT_ENABLED = False
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
ZONE_MARKER = "dot"
SHOW_SPAWNS = False
ZONE_CONE = True
FLY_ENABLED = True
ZONE_INFO_DIST = 150.0
COMPASS = True
NORTH_DEG = 0.0
TARGET_EXPLICIT = False
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
ZONE_MARKERS = ("dot", "range", "none")
# v43 : anciennes valeurs (avant v43), toujours acceptées et converties
ZONE_MARKER_OLD = {"discret": "dot", "portee": "range", "aucun": "none"}
# v43 : profil « perso » renommé « private » (ancienne valeur acceptée et convertie)
PROFILE_OLD = {"perso": "private"}
# v43 : anciens noms d'options (avant la v43), toujours acceptés : remplacés avant la lecture de la ligne de commande
OLD_OPTIONS = {"--maj": "--update", "--tile-max-mo": "--tile-max-mb", "--tile-max-tri": "--tile-max-triangles"}


def old_options(argv):
    """Remplace les anciens noms d'options par les nouveaux (« --nom=valeur » compris)."""
    out = []
    for x in argv:
        k, eq, v = str(x).partition("=")
        out.append(OLD_OPTIONS.get(k, k) + eq + v if k.startswith("--") else x)
    return out


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
        if z.get("private") and profile not in ("private", "perso"):
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
        print(_tr("py.glb2html.avertissement_presence_url_doit_commencer_pa", u), file=sys.stderr)
        return u
    fixed = re.sub(r"^(wss?://)(0\.0\.0\.0)(?=[:/]|$)", r"\g<1>127.0.0.1", u, flags=re.I)
    if fixed != u:
        print(_tr("py.glb2html.avertissement_0_0_0_0_est", fixed), file=sys.stderr)
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
#who{margin:8px 0}
#who input{font:inherit;width:200px;border:2px solid #000;border-radius:6px;padding:4px 6px}
</style>
</head>
<body><script>
__I18N__
</script><main>
<h1 __TITLE_ATTR__>__TITLE__</h1>
<div id="who"><label><span data-i18n="map.pseudo">Mon pseudo : </span><input id="pseudo" maxlength="24" placeholder="Visiteur" data-i18n-ph="map.visitor" autocomplete="nickname"></label> <small data-i18n="map.pseudo.note">mémorisé dans ce navigateur ; transmis aux régions que tu visites</small></div>
<div id="grid"></div>
<footer id="foot">glb2html __VERSION__</footer>
</main>
<script type="application/json" id="cfg">__CONFIG__</script>
<script>
(() => {
  const C = JSON.parse(document.getElementById('cfg').textContent);
  let MAP = C.map || [];
  applyI18n(); document.getElementById('foot').textContent = tr('map.footer', '__VERSION__');
  if (document.querySelector('h1[data-i18n]')) document.title = tr('map.title');
  const grid = document.getElementById('grid'), counts = {}; let known = false;
  // v34 : pseudo mémorisé (même clé que les régions) ; les liens des cartes reçoivent #name=PSEUDO
  const pin = document.getElementById('pseudo');
  const pseudo = () => pin.value.replace(/[\u0000-\u001f<>]/g, '').trim().slice(0, 24);
  try { pin.value = localStorage.getItem('glb2html_name') || ''; } catch (e) {}
  pin.addEventListener('input', () => { try { localStorage.setItem('glb2html_name', pseudo()); } catch (e) {} draw(); });
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
      const u = okUrl(r.url); if (u) u.hash = 'spawn=' + encodeURIComponent(r.spawn || 'default') + (pseudo() ? '&name=' + encodeURIComponent(pseudo()) : '');
      const t = document.createElement(u ? 'a' : 'div'); t.className = 'tile';
      if (u) { t.href = u.href; t.rel = 'noopener'; }
      if (placed) { t.style.gridColumn = String(mx.get(r.x | 0) + 1); t.style.gridRow = String(rows - my.get(r.y | 0)); }
      if (r.thumb && safeThumb(r.thumb)) { const im = document.createElement('img'); im.src = r.thumb; im.alt = ''; im.referrerPolicy = 'no-referrer'; t.append(im); } else { const ph = document.createElement('div'); ph.className = 'ph'; t.append(ph); }
      const b = document.createElement('b'); b.textContent = r.name; t.append(b);
      const n = counts[srvOf(r) + '|' + (r.room || '')];
      const s = document.createElement('span'); s.textContent = tr('map.visit') + (known && r.room && srvOf(r) ? ' · ' + tr('map.walking', n || 0) : ''); t.append(s);
      const l = document.createElement('small'); l.textContent = u ? u.href : tr('map.badurl'); t.append(l);
      grid.append(t);
    }
    if (!list.length) grid.textContent = tr('map.empty');
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


def page_path(arg, base):
    """--update : chemin relatif d'un fichier de carte -> relatif au dossier de la page (-o), jamais au dossier de lancement ni à celui des outils."""
    p = pathlib.Path(arg).expanduser()
    return p if p.is_absolute() else pathlib.Path(base) / p


def where_note(reg, out):
    """Hors --update : une ligne qui dit où le fichier de carte est écrit quand ce n'est pas à côté de la page (-o)."""
    if out and pathlib.Path(reg).resolve().parent != pathlib.Path(out).resolve().parent:
        print(_tr("py.glb2html.carte_0_n_est_pas_a", reg, out))


def thumb_data_url(arg):
    if re.match(r"^https?://", str(arg), re.I):
        return str(arg)[:600]
    p = find_beside(arg)
    if p is None:
        print(_tr("py.glb2html.avertissement_vignette_introuvable_0", arg), file=sys.stderr)
        return ""
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(p.suffix.lower())
    b = p.read_bytes()
    if not mime or len(b) > 140000:
        print(_tr("py.glb2html.avertissement_vignette_ignoree_jpg_png_webp", p), file=sys.stderr)
        return ""
    return f"data:{mime};base64," + base64.b64encode(b).decode("ascii")


def register_region(path, entry):
    """Ajoute ou met à jour (par salon) une région dans le fichier de carte ; les champs non fournis gardent leur valeur."""
    data = []
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            sys.exit(_tr("py.glb2html.erreur_0_illisible_1", path, e))
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
    page = (MAP_PAGE_TEMPLATE.replace("__TITLE_ATTR__", "" if title else 'data-i18n="map.title"').replace("__TITLE__", html.escape(title or _tr("py.glb2html.carte_des_mondes"))).replace("__VERSION__", VERSION)
            .replace("__CONFIG__", json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/")))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")
    print(_tr("py.glb2html.carte_page_carte_0_region_s", len(cfg['map']), path))


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
                          ("sea", "sea_enabled", bool), ("retina", "retina", bool), ("light", "light", bool), ("walk", "walk", bool), ("eyeHeight", "eye_height", float),
                          ("walkSpeed", "walk_speed", float), ("walkIgnore", "walk_ignore", str), ("names", "names", bool), ("chat", "chat", bool),
                          ("chatFade", "chat_fade", float), ("presenceUrl", "presence_url", str), ("room", "room", str), ("spectate", "spectate", bool),
                          ("panel", "panel", bool), ("mapUrl", "map_url", str), ("zoneMarker", "zone_marker", str), ("showSpawns", "show_spawns", bool), ("zoneCone", "zone_cone", bool), ("fly", "fly", bool), ("zoneInfoDist", "zone_info_dist", float), ("compass", "compass", bool), ("northDeg", "north", float), ("libUrl", "lib_url", str)):
        put(dest, c.get(k), conv)
    put("target_explicit", S.get("targetExplicit"), bool)
    put("zoom", cam.get("zoom"), float)
    put("cam_dir", cam.get("camDir"), vec)
    put("target", cam.get("target"), vec)
    if S.get("profile") in ("public", "private", "perso"):
        d["profile"] = PROFILE_OLD.get(S["profile"], S["profile"])
    return d


def vendor_bytes(rel: str, vendor_dir: pathlib.Path | None) -> bytes:
    if vendor_dir:
        p = vendor_dir / rel
        if not p.is_file():
            sys.exit(_tr("py.glb2html.erreur_0_introuvable_vendor_doit_pointer", p))
        return p.read_bytes()
    p = CACHE_DIR / rel
    if not p.is_file():
        p.parent.mkdir(parents=True, exist_ok=True)
        print(_tr("py.glb2html.cache_telechargement_0", CDN + rel))
        try:
            with urllib.request.urlopen(CDN + rel, timeout=60) as r:
                data = r.read()
        except Exception as e:
            sys.exit(_tr("py.glb2html.erreur_telechargement_impossible_0_utilise_v", e))
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
        raise ValueError(_tr("py.glb2html.0_pas_un_glb_magic_absent", name))
    version, total = struct.unpack_from("<II", data, 4)
    if version != 2:
        raise ValueError(_tr("py.glb2html.0_gltf_version_1_non_supportee", name, version))
    if total != len(data):
        raise ValueError(_tr("py.glb2html.0_taille_annoncee_1_taille_fichier", name, total, len(data)))
    clen, ctype = struct.unpack_from("<II", data, 12)
    if ctype != 0x4E4F534A:
        raise ValueError(_tr("py.glb2html.0_premier_chunk_non_json", name))
    gltf = json.loads(data[20:20 + clen].decode("utf-8"))
    used = set(gltf.get("extensionsUsed", [])) | set(gltf.get("extensionsRequired", []))
    ext_refs = [x.get("uri") for x in gltf.get("buffers", []) + gltf.get("images", [])
                if x.get("uri") and not x["uri"].startswith("data:")]
    if ext_refs:
        raise ValueError(_tr("py.glb2html.0_reference_des_fichiers_externes_1", name, ext_refs[:3]))
    if "KHR_texture_basisu" in used:
        raise ValueError(_tr("py.glb2html.0_textures_ktx2_basis_non_gerees", name))
    return used


HTML_TEMPLATE = r"""__HTML_TEMPLATE__"""

DRACO_JS = r"""__DRACO_JS__"""

MESHOPT_JS = r"""__MESHOPT_JS__"""


def build_cfg(name: str, *, rotate=ROTATE, hole=HOLE_RADIUS, hole_fade=HOLE_FADE, hole_x=HOLE_X, hole_z=HOLE_Z, wave=WAVE_AMP,
               sea_y=SEA_Y, zoom=ZOOM_RATIO, cam_dir=CAM_DIR, target=TARGET, sea_enabled=SEA_ENABLED,
               anim_enabled=ANIM_ENABLED, retina=RETINA_ENABLED, light=LIGHT_ENABLED, foliage_cutout=FOLIAGE_CUTOUT,
               sea_color=SEA_COLOR, sky_color=SKY_COLOR, sea_segments=SEA_SEGMENTS, walk=WALK_ENABLED, eye_height=EYE_HEIGHT, walk_speed=WALK_SPEED, walk_ignore=WALK_IGNORE, names=NAMES_ENABLED, presence_url=PRESENCE_URL, room=ROOM, chat=CHAT_ENABLED, chat_fade=CHAT_FADE, zones=None, profile=PROFILE, spectate=SPECTATE, panel=PANEL, zones_live=ZONES_LIVE, map_entries=None, map_url=MAP_URL, modular=False, zone_marker=ZONE_MARKER, show_spawns=SHOW_SPAWNS, zone_cone=ZONE_CONE, fly=FLY_ENABLED, zone_info_dist=ZONE_INFO_DIST, compass=COMPASS, north=NORTH_DEG, lib_url="", make_default=False, target_explicit=TARGET_EXPLICIT, tiles=None, tile_radius=TILE_RADIUS, tile_margin=TILE_MARGIN, tile_max_mo=TILE_MAX_MO, tile_max_tri=TILE_MAX_TRI, tile_concurrency=TILE_CONCURRENCY) -> dict:
    """Le dictionnaire de réglages `cfg` : identique dans la page autonome et dans <page>.config.json (mode modulaire),
    sauf que le mode modulaire garde les zones hors de la config (fichier <page>.zones.json, relu à chaque ouverture)."""
    presence_url = fix_presence_url(presence_url)
    cfg = {
        "rotate": clean_rotate(rotate), "hole": float(hole), "holeFade": float(hole_fade), "holeX": float(hole_x), "holeZ": float(hole_z), "wave": float(wave), "seaY": float(sea_y),
        "zoom": float(zoom), "camDir": list(map(float, cam_dir)), "target": list(map(float, target)),
        "sea": bool(sea_enabled), "anim": bool(anim_enabled), "retina": bool(retina), "light": bool(light),
        "foliageCutout": float(foliage_cutout), "seaSize": SEA_SIZE, "seaSegments": int(sea_segments),
        "seaColor": int(sea_color), "skyColor": int(sky_color),
        "walk": bool(walk), "eyeHeight": float(eye_height), "walkSpeed": float(walk_speed), "walkIgnore": str(walk_ignore),
        "names": bool(names), "chat": bool(chat), "profile": PROFILE_OLD.get(profile, profile), "version": VERSION, "panel": bool(panel), "zonesLive": str(zones_live or ""),
        "map": clean_map(json.loads(MAP_JSON) if map_entries is None else map_entries), "mapUrl": str(map_url or "")[:1200], "spectate": bool(presence_url) if spectate is None else bool(spectate),
        "zones": clean_zones(json.loads(ZONES_JSON) if zones is None else zones, profile), "chatFade": float(chat_fade), "presenceUrl": str(presence_url), "room": str(room) or pathlib.Path(name).stem,
        "zoneMarker": ZONE_MARKER_OLD.get(zone_marker, zone_marker) if ZONE_MARKER_OLD.get(zone_marker, zone_marker) in ZONE_MARKERS else "dot", "showSpawns": bool(show_spawns), "zoneCone": bool(zone_cone), "fly": bool(fly), "targetExplicit": bool(target_explicit),
        "zoneInfoDist": max(5.0, min(500.0, float(zone_info_dist))), "compass": bool(compass), "northDeg": float(north) % 360.0, "libUrl": str(lib_url or ""),
    }
    if modular:
        cfg["zones"], cfg["zonesLive"] = [], ""
    if tiles:
        # mode tuiles : clés présentes seulement dans ce cas (sans « tiles », la config est celle d'avant)
        cfg.update({"tiles": str(tiles), "tileRadius": float(tile_radius), "tileMargin": float(tile_margin), "tileMaxMB": float(tile_max_mo),
                    "tileMaxTriangles": int(tile_max_tri), "tileConcurrency": int(tile_concurrency)})
    return cfg


SHELL_BOOT_OLD = "const C = JSON.parse(document.getElementById('cfg').textContent);"
SHELL_MSG_OLD = '<div id="msg" data-i18n="page.loading">Chargement…</div>\n'
# script classique : depuis le disque, les modules sont bloqués par le navigateur et le module de la page ne s'exécute jamais
SHELL_MSG_NEW = SHELL_MSG_OLD + """<script>
if (location.protocol === 'file:') document.getElementById('msg').textContent = tr('page.shell.file', decodeURIComponent(location.pathname.split('/').pop()) + location.search);
</script>
"""
# la coquille ne contient aucun nom : X.html charge X.config.json, X.glb, X.zones.json (puis zones.json) du même dossier
SHELL_BOOT_NEW = r"""// fichiers frères : par défaut déduits du nom de la page (copier X.html en Y.html et ses frères en Y.* suffit) ;
// avec ?region=NOM, de NOM : une seule coquille peut servir plusieurs régions du même dossier
const BOOT = await (async () => {
  const fail = raison => { document.getElementById('msg').textContent = tr('page.shell.error', raison); throw new Error(raison); };
  // même règle que valid_region_name (gen_tpl.py), à garder identique : un nom simple = un seul nom de fichier ; dossier/nom ou a/b/nom = segments de lettres, chiffres,
  // point (pas au début), tiret, souligné, espace et parenthèses ; jamais « .. », « : », « \ », « ? », « # », ni chemin commençant par « / »
  const okRegion = nom => {
    if (!nom || nom.length > 200) return false;
    if (!nom.includes('/')) return !/[\/\\:?#\x00-\x1f]/.test(nom) && !nom.includes('..') && !nom.startsWith('.');
    return nom.split('/').every(s => /^[\p{L}\p{N}_()\- ][\p{L}\p{N}_()\- .]*$/u.test(s) && s.trim() !== '' && !s.includes('..'));
  };
  const clean = s => String(s || '').replace(/\.html?$/i, '');
  // fichiers de la région NOM (ou a/b/NOM) : tous relatifs au dossier de la région (dir) ; les zones se cherchent aussi dans zones.json de ce dossier
  const mk = nom => {
    const i = nom.lastIndexOf('/'), dir = i < 0 ? '' : nom.slice(0, i).split('/').map(encodeURIComponent).join('/') + '/', e = dir + encodeURIComponent(nom.slice(i + 1));
    return { dir, config: e + '.config.json', glb: e + '.glb', zones: [e + '.zones.json', dir + 'zones.json'] };
  };
  const q = new URLSearchParams(location.search);
  if (q.has('region')) {
    // NOM ne peut être ni une adresse ni un chemin vers un dossier parent (aucune requête avant ce contrôle)
    const nom = clean(q.get('region'));
    if (!okRegion(nom)) fail(tr('page.shell.badregion', nom));
    return mk(nom);
  }
  // sans ?region= : (a) X.config.json du nom de la page ; (b) default.json {"region": "NOM"} ; (c) la première entrée de regions.json d'adresse relative ; (d) message
  let f = location.pathname.split('/').pop() || '';
  try { f = decodeURIComponent(f); } catch (x) {}
  const own = mk(clean(f) || 'index');
  const probe = async b => { try { const r = await fetch(b.config, { cache: 'no-store' }); if (r.ok) { b.res = r; return b; } } catch (x) {} return null; };
  const relRegion = u => {
    u = String(u || '');
    if (/^[a-z][a-z0-9+.\-]*:/i.test(u) || /^[\/\\]/.test(u)) return null;
    try { const nom = clean(new URL(u, 'http://x/').searchParams.get('region')); return okRegion(nom) ? nom : null; } catch (x) { return null; }
  };
  const a = await probe(own); if (a) return a;
  try {
    const r = await fetch('default.json', { cache: 'no-store' });
    if (r.ok) { const d = await r.json(); const nom = clean(d && d.region); if (okRegion(nom)) { const b = await probe(mk(nom)); if (b) return b; } }
  } catch (x) {}
  try {
    const r = await fetch('regions.json', { cache: 'no-store' });
    if (r.ok) {
      const d = await r.json(), liste = Array.isArray(d) ? d : (d && Array.isArray(d.regions) ? d.regions : []);
      for (const e of liste) { const nom = relRegion(e && e.url); if (nom) { const b = await probe(mk(nom)); if (b) return b; } }
    }
  } catch (x) {}
  document.getElementById('msg').textContent = tr('page.shell.noregion', own.config);
  throw new Error('region');
})();
const C = await (async () => {
  const fail = (nom, raison) => { document.getElementById('msg').textContent = tr('page.shell.notfound', nom, raison); throw new Error(nom + ' : ' + raison); };
  let r = BOOT.res;
  if (!r) {
    try { r = await fetch(BOOT.config, { cache: 'no-store' }); } catch (e) { fail(BOOT.config, tr('page.shell.network')); }
    if (!r.ok) fail(BOOT.config, 'HTTP ' + r.status);
  }
  const cfg = await r.json();
  if (cfg.tiles && BOOT.dir) cfg.tiles = BOOT.dir + cfg.tiles;   // région dans un sous-dossier : les chemins de la config sont relatifs à ce dossier
  // zones relues à chaque ouverture : X.zones.json, sinon zones.json du même dossier, sinon aucune
  cfg.zones = [];
  for (const nom of BOOT.zones) {
    try {
      const rz = await fetch(nom, { cache: 'no-store' }); if (!rz.ok) continue;
      const liste = await rz.json(); if (!Array.isArray(liste)) continue;
      cfg.zones = liste.filter(z => z && (cfg.profile === 'private' || cfg.profile === 'perso' || !z.private)); break;
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
    // région en tuiles (X.tiles.json, voir docs/fr/MANUEL.md § 17 bis) : pas de X.glb ; ?radius=NNN remplace tileRadius (essais).
    // Arrivée demandée (lien #spawn= ou #pos=) : cadrage et chargement d'abord sur ce point. Sans lien, arrivée « default » si la région en a une
    // (sauf --target explicite) ; sinon la cible de la configuration. La page continue après 15 s même si la tuile n'est pas prête.
    const rayon = Number(new URLSearchParams(location.search).get('radius') || new URLSearchParams(location.search).get('rayon'));   // v43 : ?radius= ; l'ancien ?radius= reste lu
    const A = startPoint(), D = A ? null : defaultArrival(), at = A || (D && !keepTarget ? D : null);
    await viewer.loadTiles(C.tiles, { anchor: at ? at.pos : undefined, target: at ? at.pos : undefined, radius: rayon > 0 ? rayon : undefined });
  } else {
    const rGlb = await fetch(BOOT.glb);
    if (!rGlb.ok) throw new Error(BOOT.glb + ' : HTTP ' + rGlb.status);
    await viewer.loadBuffer(await rGlb.arrayBuffer());
  }"""
SHELL_TITLE_OLD = "<title>__TITLE__</title>"
LIB_REL = "lib/three-" + THREE_VERSION
DRACO_PATH_OLD = "draco.setDecoderPath('');"
# v45 : la table d'import de la coquille est construite par un script classique (avant tout module) a partir d'UNE ligne, const LIB, modifiable a la main
SHELL_IMPORTMAP_OLD = '<script type="importmap">\n__IMPORTMAP__\n</script>'
SHELL_IMPORTMAP_NEW = """<script>
// LIB : dossier de lib (seule ligne a modifier) / folder of lib (the only line to edit)
const LIB = '__LIB__';
(function () {
  const F = __FILES__;
  const im = {};
  for (const k in F) im[k] = LIB + '/three-__THREE__/' + F[k];
  const s = document.createElement('script'); s.type = 'importmap'; s.textContent = JSON.stringify({ imports: im });
  document.head.appendChild(s);
})();
</script>"""
LIB_LINE_RE = re.compile(r"^const LIB = '([^'\r\n]*)';\r?$", re.M)
SHELL_SKY = "87ceeb"   # fond provisoire, remplacé par skyColor dès que la config est lue
# la coquille connaît tous les modules (Draco et Meshopt compris) : elle ne dépend d'aucun .glb
SHELL_MODULES = {**CORE_FILES, **DRACO_FILES, **MESHOPT_FILES}


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError(_tr("py.glb2html.gabarit_modulaire_cible_introuvable_ou_multi", old[:50]))
    return text.replace(old, new)


def lib_name(rel):
    return rel.rsplit("/", 1)[-1]


def write_atomic(path: pathlib.Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def write_modular_lib(out_dir: pathlib.Path, vendor_dir, lib_url=None):
    """Écrit lib/three-X/ à côté des pages (partagé par toutes les pages du dossier) : modules à plat, imports réécrits,
    Draco et Meshopt toujours présents (la coquille ne sait pas ce que contient le .glb). v37 : lib_url déplace le dossier (rien n'est écrit pour une adresse complète)."""
    lib = lib_dir_of(out_dir, lib_url)
    if lib is None:
        return
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
    """Même règle que la coquille (?region=NOM), à garder identique au JS (okRegion dans SHELL_BOOT_NEW). Un nom simple : un seul nom de fichier, sans / \\ : ? # ni ..,
    sans point au début. v37, chemin descendant dossier/nom ou a/b/nom : chaque segment fait de lettres, chiffres, point (pas au début), tiret, souligné, espace et
    parenthèses ; jamais « .. », « : », « \\ », « ? », « # », ni chemin commençant par « / »."""
    name = re.sub(r"\.html?$", "", str(name or ""), flags=re.I)
    if "/" not in name:
        return bool(name) and not re.search(r"[/\\:?#\x00-\x1f]", name) and ".." not in name and not name.startswith(".")
    return len(name) <= 200 and all(re.fullmatch(r"[\w()\- ][\w()\- .]*", seg) is not None and seg.strip() != "" and ".." not in seg for seg in name.split("/"))


def shell_page_address(shell_name: str, region: str) -> str:
    """Adresse d'une région servie par une coquille commune : COQUILLE.html?region=NOM (le #spawn= s'ajoute après)."""
    return f"{shell_name}?region={urllib.parse.quote(region, safe='/')}"


class ShellRef(str):
    """Nom de la coquille commune (le texte), avec son dossier si --shared-shell a reçu un chemin (v37 : région dans un sous-dossier de la coquille)."""
    dir = None


def shell_file(shell, out_path: pathlib.Path) -> pathlib.Path:
    """Fichier de la coquille : dans le dossier donné par l'option, sinon à côté de la région."""
    return (shell.dir if getattr(shell, "dir", None) else out_path.parent) / str(shell)


def shell_dir_of(shell, out_path: pathlib.Path) -> pathlib.Path:
    return shell.dir if (shell is not None and getattr(shell, "dir", None)) else out_path.parent


def region_of(shell, out_path: pathlib.Path):
    """Nom de la région vu de la coquille : chemin de la page sans extension, relatif au dossier de la coquille (a/b/X) ; None si la page est ailleurs."""
    base = shell_dir_of(shell, out_path)
    try:
        return out_path.resolve().with_suffix("").relative_to(base.resolve()).as_posix()
    except ValueError:
        return None


def clean_lib_url(v):
    """--lib-url : chemin relatif (../lib) ou adresse http(s) complète ; rend (texte normalisé, est_distant) ou lève ValueError."""
    v = str(v or "").strip()
    if not v:
        return "", False
    if re.search(r"[\\?#\x00-\x1f\"'<>`]", v):
        raise ValueError(v)
    if re.match(r"https?://", v, re.I):
        return v.rstrip("/"), True
    if re.match(r"[a-zA-Z][a-zA-Z0-9+.\-]*:", v) or v.startswith(("/", "//")):
        raise ValueError(v)
    v = v.rstrip("/")
    return v, False


def lib_prefix(lib_url) -> str:
    """Début des adresses de la table d'import : ./lib par défaut (octet pour octet comme avant), ../lib, ./sous/lib, ou l'adresse complète."""
    v, remote = clean_lib_url(lib_url)
    v = urllib.parse.quote(v, safe="/:%@+=,()-._~")
    if not v:
        return "./lib"
    if remote or v.startswith("./") or v.startswith("../") or v in (".", ".."):
        return v
    return "./" + v


def lib_dir_of(shell_dir: pathlib.Path, lib_url):
    """Dossier lib/three-X/ à écrire (None si lib_url est une adresse complète : rien n'est copié)."""
    v, remote = clean_lib_url(lib_url)
    if remote:
        return None
    return shell_dir / (v or "lib") / ("three-" + THREE_VERSION)


def lib_from_shell(shell_path: pathlib.Path):
    """v45 : valeur de la ligne `const LIB = '...';` d'une coquille existante (texte tel qu'ecrit), ou None si le fichier est absent, sans cette ligne
    (coquille d'avant la v45) ou si la valeur est refusee par clean_lib_url."""
    try:
        m = LIB_LINE_RE.search(pathlib.Path(shell_path).read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError):
        return None
    if not m:
        return None
    try:
        clean_lib_url(m.group(1))
    except ValueError:
        return None
    return m.group(1)


def effective_lib_url(shell_path: pathlib.Path, lib_url, explicit):
    """v45 : dossier lib a utiliser. Ordre : --lib-url donne (explicit) ; la ligne const LIB d'une coquille existante si elle n'est pas le defaut ./lib ;
    lib_url (la config pour --update) ; sinon vide (= ./lib). Ainsi une coquille modifiee a la main garde son dossier."""
    if explicit:
        return lib_url
    cur = lib_from_shell(shell_path)
    if cur is not None and lib_prefix(cur) != "./lib":
        return cur
    return lib_url


def same_shell(existing: bytes, new: bytes) -> bool:
    """Meme coquille, a la fin de ligne pres (un editeur Windows peut enregistrer en CRLF)."""
    return existing.replace(b"\r\n", b"\n") == new


def lib_missing(out_dir: pathlib.Path, lib_url=None):
    """Fichiers de lib/three-X/ absents (la coquille commune et les pages déjà publiées les partagent)."""
    mods, draco = shell_lib_files()
    lib = lib_dir_of(out_dir, lib_url)
    if lib is None:
        return []
    return [str(lib / n) for n in list(mods.values()) + ["draco/" + n for n in draco] if not (lib / n).is_file()]


def build_shell(lib_url=None) -> str:
    """La coquille universelle du mode modulaire : même texte, octet pour octet, pour toutes les régions (le viewer en met
    une copie dans son .zip). Elle charge <nom de la page>.config.json / .glb / .zones.json du même dossier et lib/three-X/.
    Aucun nom, aucun titre, aucune couleur propre à une région n'y est écrit."""
    files = {spec: lib_name(rel) for spec, rel in SHELL_MODULES.items()}
    decoders = [replace_once(DRACO_JS.replace("__DRACO_LIBS__", "{}"), DRACO_PATH_OLD, "draco.setDecoderPath(LIB + '/three-" + THREE_VERSION + "/draco/');"), MESHOPT_JS]
    tpl = HTML_TEMPLATE
    tpl = replace_once(tpl, SHELL_IMPORTMAP_OLD, SHELL_IMPORTMAP_NEW.replace("__LIB__", lib_prefix(lib_url)).replace("__FILES__", json.dumps(files, indent=1)).replace("__THREE__", THREE_VERSION))
    tpl = replace_once(tpl, SHELL_TITLE_OLD, "<title>Chargement…</title>")
    tpl = replace_once(tpl, SHELL_MSG_OLD, SHELL_MSG_NEW)
    tpl = replace_once(tpl, SHELL_CFG_TAG, "")
    tpl = replace_once(tpl, SHELL_GLB_TAG, "")
    tpl = replace_once(tpl, SHELL_BOOT_OLD, SHELL_BOOT_NEW)
    tpl = replace_once(tpl, SHELL_LOAD_OLD, SHELL_LOAD_NEW)
    out = tpl.replace("__SKY_HEX__", SHELL_SKY).replace("__DECODERS__", "\n".join(decoders))
    left = re.findall(r"__(?:TITLE|SKY_HEX|IMPORTMAP|CONFIG|DECODERS|GLB_B64|CORE)__", out)
    if left:
        raise RuntimeError(_tr("py.glb2html.coquille_modulaire_marqueur_s_non_remplace", sorted(set(left))))
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
    print(_tr("py.glb2html.zones_0_zone_s_profil_1", len(zones), kw.get('profile', PROFILE), target))


def zones_given(kw):
    """Vrai si une source de zones a été donnée (--zones, --settings ou ZONES_JSON du script exporté par le viewer)."""
    return kw.get("zones") is not None or bool(json.loads(ZONES_JSON))


def write_modular_zones(zones_path: pathlib.Path, kw):
    """Écrit <page>.zones.json (zones nettoyées, filtrées selon le profil), relu par la page à chaque ouverture."""
    profile = kw.get("profile", PROFILE)
    zones = clean_zones(json.loads(ZONES_JSON) if kw.get("zones") is None else kw["zones"], profile)
    write_atomic(zones_path, json.dumps(zones, ensure_ascii=False, indent=1).encode("utf-8"))
    print(_tr("py.glb2html.zones_0_zone_s_profil_1", len(zones), profile, zones_path))


def write_default_json(shell_dir: pathlib.Path, region: str, force=False):
    """v37 : default.json {"region": NOM} à côté de la coquille = région ouverte quand l'adresse n'a pas de ?region=. Écrit la première fois, ou avec --default."""
    path = shell_dir / "default.json"
    if path.is_file() and not force:
        return
    write_atomic(path, (json.dumps({"region": region}, ensure_ascii=False) + "\n").encode("utf-8"))
    print(_tr("py.glb2html.default_json_ecrit", path, region))


def write_shell_page(out_path: pathlib.Path, shell, page: str):
    """Écrit la coquille : X.html (modulaire simple) ou COQUILLE.html à côté de la région, jamais écrasée si elle existe et diffère."""
    if shell:
        shell_path = shell_file(shell, out_path)
        if not shell_path.is_file():
            write_atomic(shell_path, page.encode("utf-8"))
            print(_tr("py.glb2html.coquille_0_ecrite", shell_path))
        elif same_shell(shell_path.read_bytes(), page.encode("utf-8")):
            print(_tr("py.glb2html.coquille_0_deja_presente_et_identique", shell_path))
        else:
            print(_tr("py.glb2html.avertissement_0_existe_et_differe_de", shell_path), file=sys.stderr)
    else:
        write_atomic(out_path, page.encode("utf-8"))


def generate(glb_path: pathlib.Path, out_path: pathlib.Path, vendor_dir, modular=False, shell=None, **kw):
    """shell : nom de la coquille commune (COQUILLE.html). Alors out_path désigne la région (NOM = son nom sans extension) :
    seuls NOM.glb, NOM.config.json et NOM.zones.json sont écrits, plus la coquille et lib/ s'ils sont absents."""
    data = glb_path.read_bytes()
    make_default = kw.pop("make_default", False)
    rname = out_path.stem
    if shell:
        modular = True
        rname = region_of(shell, out_path)
        if rname is None or not valid_region_name(rname):
            print(_tr("py.glb2html.erreur_nom_de_region_0_refuse", rname or out_path.stem), file=sys.stderr)
            return False
    if modular:
        if kw.get("title"):
            print(_tr("py.glb2html.avertissement_title_est_ignore_en_mode"), file=sys.stderr)
        if kw.get("zones_live"):
            print(_tr("py.glb2html.avertissement_zones_live_est_ignore_en"), file=sys.stderr)
        kw = dict(kw, zones_live="")
        kw = dict(kw, lib_url=effective_lib_url(shell_file(shell, out_path) if shell else out_path, kw.get("lib_url") or "", bool(kw.get("lib_url"))))
    elif kw.get("zones_live"):
        kw = dict(kw, zones_live=live_zones_name(out_path, kw["zones_live"]))
    try:
        used = inspect_glb(data, glb_path.name)
        page = build_shell(kw.get("lib_url")) if modular else build_html(data, glb_path.name, vendor_dir, **kw)
    except ValueError as e:
        print(_tr("py.glb2html.erreur_0", e), file=sys.stderr)
        return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if modular:
        glb_out, cfg_out, zones_out = modular_names(out_path)
        if not shell or lib_missing(shell_dir_of(shell, out_path), kw.get("lib_url")):
            write_modular_lib(shell_dir_of(shell, out_path), vendor_dir, kw.get("lib_url"))
        write_atomic(glb_out, data)
        write_config(cfg_out, glb_path.name, kw)
        # sans source de zones, un X.zones.json existant (peut-être modifié à la main) n'est pas écrasé
        if zones_given(kw) or not zones_out.is_file():
            write_modular_zones(zones_out, kw)
    write_shell_page(out_path, shell, page)
    if shell:
        write_default_json(shell_dir_of(shell, out_path), rname, make_default)
    if not modular:
        write_live_zones(out_path, dict(kw, zones_live=kw.get("zones_live") or ""))
    if shell:
        print(_tr("py.glb2html.ok_0_1_2_3_coquille", glb_path.name, glb_out.name, cfg_out.name, zones_out.name, shell, shell_page_address(shell, rname), VERSION))
    elif modular:
        print(_tr("py.glb2html.ok_0_1_modulaire_coquille_2", glb_path.name, out_path, len(page) / 1024, glb_out.name, len(data) / 2**20, cfg_out.name, zones_out.name, lib_prefix(kw.get("lib_url")).lstrip("./") + "/three-" + THREE_VERSION, VERSION))
    else:
        print(_tr("py.glb2html.ok_0_1_2_2f_mo", glb_path.name, out_path, len(data) / 2**20, len(page) / 2**20, VERSION))
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
        sys.exit(_tr("py.glb2html.erreur_0_illisible_1", path, e))
    tiles = doc.get("tiles") if isinstance(doc, dict) else None
    if not isinstance(tiles, list) or not tiles:
        sys.exit(_tr("py.glb2html.erreur_0_liste_tiles_absente_ou", path))
    for t in tiles:
        ok = isinstance(t, dict) and safe_rel_path(t.get("file")) and str(t["file"]).lower().endswith(".glb")
        for k in ("min", "max"):
            ok = ok and isinstance(t.get(k), list) and len(t[k]) == 3 and all(isinstance(v, (int, float)) and math.isfinite(v) for v in t[k])
        if not ok:
            sys.exit(_tr("py.glb2html.erreur_0_entree_de_tuile_invalide", path, str(t)[:120]))
    ov = doc.get("overview")
    if ov is not None and not (isinstance(ov, dict) and safe_rel_path(ov.get("file")) and str(ov["file"]).lower().endswith(".glb")):
        sys.exit(_tr("py.glb2html.erreur_0_overview_invalide_1_file", path, str(ov)[:120]))
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
        print(_tr("py.glb2html.avertissement_0_tuile_s_listee_s", len(absent), tiles_path.name, absent[0]), file=sys.stderr)
    if ov_file and not (src / ov_file).is_file():
        print(_tr("py.glb2html.avertissement_vue_d_ensemble_0_introuvable", ov_file, tiles_path.name), file=sys.stderr)
    ov_txt = _tr("py.glb2html.vue_d_ensemble_0_placee_avec", ov_file) if ov_file else ""
    if src == dst:
        print(_tr("py.glb2html.tuiles_0_tuile_s_et_1", len(files), tiles_path.name, ov_txt))
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
    print(_tr("py.glb2html.tuiles_0_copie_dans_1_tuiles", tiles_path.name, dst, copied, size / 2**20, same, ov_txt))
    return tiles_path.name


def generate_tiles(tiles_path: pathlib.Path, doc, out_path: pathlib.Path, vendor_dir, shell=None, **kw):
    """Région en tuiles : comme generate() en mode modulaire, mais sans .glb : écrit X.config.json (champ « tiles »), X.zones.json,
    la coquille et lib/ ; X.tiles.json et ses tuiles ne sont copiés que s'ils ne sont pas déjà à côté de la page."""
    make_default = kw.pop("make_default", False)
    rname = out_path.stem
    if shell:
        rname = region_of(shell, out_path)
        if rname is None or not valid_region_name(rname):
            print(_tr("py.glb2html.erreur_nom_de_region_0_refuse", rname or out_path.stem), file=sys.stderr)
            return False
    if kw.get("title"):
        print(_tr("py.glb2html.avertissement_title_est_ignore_en_mode"), file=sys.stderr)
    if kw.get("zones_live"):
        print(_tr("py.glb2html.avertissement_zones_live_est_ignore_en"), file=sys.stderr)
    kw = dict(kw, zones_live="")
    page = build_shell(kw.get("lib_url"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    kw["tiles"] = place_tiles(tiles_path, doc, out_path.parent)
    zones_keep = kw.pop("zones_keep", False)   # --zones désigne déjà X.zones.json de destination : jamais réécrit
    _, cfg_out, zones_out = modular_names(out_path)
    if not shell or lib_missing(shell_dir_of(shell, out_path), kw.get("lib_url")):
        write_modular_lib(shell_dir_of(shell, out_path), vendor_dir, kw.get("lib_url"))
    write_config(cfg_out, out_path.stem, kw)
    if (zones_given(kw) and not zones_keep) or not zones_out.is_file():
        write_modular_zones(zones_out, kw)
    write_shell_page(out_path, shell, page)
    if shell:
        write_default_json(shell_dir_of(shell, out_path), rname, make_default)
    n = len(doc["tiles"])
    if any(z.get("mesh") for z in clean_zones(json.loads(ZONES_JSON) if kw.get("zones") is None else kw["zones"], kw.get("profile", PROFILE))):
        if doc.get("nodeRefs"):
            print(_tr("py.glb2html.tuiles_des_zones_sont_liees_a"))
        else:
            print(_tr("py.glb2html.avertissement_des_zones_sont_liees_a", tiles_path.name), file=sys.stderr)
    adr = shell_page_address(shell, rname) if shell else out_path.name
    print(_tr("py.glb2html.ok_0_tuile_s_1_2", n, cfg_out.name, zones_out.name) + (_tr("py.glb2html.coquille_commune_0_adresse_1", shell, adr) if shell else _tr("py.glb2html.shell_name", out_path.name)) + f" [glb2html {VERSION}]")
    return True


def write_config(cfg_path: pathlib.Path, name: str, kw):
    """Écrit <page>.config.json = le dictionnaire cfg de la page modulaire (carte comprise, zones exclues), JSON sans BOM."""
    cfg = build_cfg(name, **{k: v for k, v in kw.items() if k != "title"}, modular=True)
    write_atomic(cfg_path, json.dumps(cfg, ensure_ascii=False, indent=1).encode("utf-8"))
    return cfg


# --update : option de la ligne de commande (dest argparse) -> clés de la config qu'elle remplace. Les autres clés de la config existante sont gardées telles quelles.
MAJ_KEYS = {
    "rotate": ("rotate",), "hole": ("hole",), "hole_fade": ("holeFade",), "hole_x": ("holeX",), "hole_z": ("holeZ",), "wave": ("wave",), "sea_y": ("seaY",),
    "zoom": ("zoom",), "cam_dir": ("camDir",), "target": ("target", "targetExplicit"), "foliage_cutout": ("foliageCutout",), "sea_color": ("seaColor",),
    "sky_color": ("skyColor",), "sea_segments": ("seaSegments",), "walk": ("walk",), "eye_height": ("eyeHeight",), "walk_speed": ("walkSpeed",),
    "walk_ignore": ("walkIgnore",), "names": ("names",), "presence_url": ("presenceUrl",), "chat": ("chat",), "chat_fade": ("chatFade",), "profile": ("profile",),
    "spectate": ("spectate",), "panel": ("panel",), "map_url": ("mapUrl",), "room": ("room",), "sea_enabled": ("sea",), "anim_enabled": ("anim",), "retina": ("retina",), "light": ("light",),
    "zone_marker": ("zoneMarker",), "show_spawns": ("showSpawns",), "zone_cone": ("zoneCone",), "fly": ("fly",), "zone_info_dist": ("zoneInfoDist",), "compass": ("compass",), "north": ("northDeg",), "lib_url": ("libUrl",), "tile_radius": ("tileRadius",), "tile_margin": ("tileMargin",),
    "tile_max_mo": ("tileMaxMB",), "tile_max_tri": ("tileMaxTriangles",), "tile_concurrency": ("tileConcurrency",), "tiles": ("tiles",),
    "map": ("map",), "register": ("map",),
}


def explicit_dests(ap):
    """Options réellement données sur la ligne de commande (et non remplies par leur valeur par défaut) : on relit la ligne avec des défauts « absents"."""
    saved = [(act, act.default) for act in ap._actions]
    saved_def = dict(ap._defaults)
    try:
        for act in ap._actions:
            act.default = argparse.SUPPRESS
        ap._defaults.clear()
        return set(vars(ap.parse_args()))
    finally:
        for act, d in saved:
            act.default = d
        ap._defaults.update(saved_def)


def merge_maj_cfg(old: dict, new: dict, explicit) -> tuple:
    """Config existante + seulement les clés des options explicites ; la version est toujours celle du script. Rend (config, [(clé, ancienne, nouvelle)])."""
    out = dict(old)
    changes = []
    keys = []
    for d in explicit:
        keys += list(MAJ_KEYS.get(d, ()))
    if "presenceUrl" in keys and "spectate" not in keys:
        keys.append("spectate")   # sans --spectate explicite, la vue globale suit l'adresse de présence (comme à la génération)
    for k in keys:
        if k in new and old.get(k) != new[k]:
            changes.append((k, old.get(k), new[k]))
            out[k] = new[k]
    if old.get("version") != VERSION:
        changes.append(("version", old.get("version"), VERSION))
    out["version"] = VERSION
    out.pop("zones", None)
    out["zones"] = []
    return out, changes


def renew_shell(shell_path: pathlib.Path, page: str):
    """--update : écrit la coquille de cette version si elle est absente ou différente (l'ancienne est gardée sous un nom daté). Rend un texte pour le compte rendu."""
    new = page.encode("utf-8")
    if not shell_path.is_file():
        write_atomic(shell_path, new)
        return _tr("py.glb2html.coquille_0_absente_ecrite", shell_path.name)
    if same_shell(shell_path.read_bytes(), new):
        return _tr("py.glb2html.coquille_0_deja_a_jour_identique", shell_path.name, VERSION)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    bak = shell_path.with_name(f"{shell_path.stem}.avant-{stamp}{shell_path.suffix}")
    shutil.copyfile(shell_path, bak)
    write_atomic(shell_path, new)
    return (_tr("py.glb2html.coquille_0_plus_ancienne_que_1", shell_path.name, VERSION, bak.name))


def run_maj(a, kw, explicit, S_reg):
    """glb2html.py --update : met à jour une région déjà générée en mode modulaire. N'applique que les options données, garde le reste de X.config.json
    et X.zones.json (réécrit seulement avec --zones), écrit la version courante et renouvelle la coquille si elle est plus ancienne."""
    if not a.output:
        sys.exit(_tr("py.glb2html.erreur_maj_demande_o_region_html"))
    out = pathlib.Path(a.output)
    if out.is_dir() or str(a.output).endswith(("/", "\\")):
        sys.exit(_tr("py.glb2html.erreur_avec_maj_o_designe_la"))
    if not out.suffix:
        out = out.with_suffix(".html")
    glb_out, cfg_out, zones_out = modular_names(out)
    if not cfg_out.is_file():
        cmd = "glb2html.py " + ("--tiles X.tiles.json" if a.tiles else "X.glb") + f" -o {out.name}" + (f" --shared-shell {a.shared_shell}" if a.shared_shell else "") + " [options]"
        sys.exit(_tr("py.glb2html.erreur_maj_0_introuvable_la_region", cfg_out, cmd))
    try:
        old = json.loads(cfg_out.read_text(encoding="utf-8-sig"))
        if not isinstance(old, dict):
            raise ValueError(_tr("py.glb2html.ce_n_est_pas_un_objet"))
    except (OSError, ValueError) as e:
        sys.exit(_tr("py.glb2html.erreur_0_illisible_1", cfg_out, e))
    shell_path = shell_file(a.shared_shell, out) if a.shared_shell else out
    rname = out.stem
    if not a.shared_shell and not out.is_file():
        sys.exit(_tr("py.glb2html.erreur_maj_0_introuvable_si_la", out, DEFAULT_SHELL))
    if a.shared_shell:
        rname = region_of(a.shared_shell, out)
        if rname is None or not valid_region_name(rname):
            sys.exit(_tr("py.glb2html.erreur_nom_de_region_0_refuse_2", rname or out.stem))
    kw.pop("make_default", None)
    if a.input and a.tiles:
        sys.exit(_tr("py.glb2html.erreur_tiles_remplace_le_glb_ne"))
    explicit = set(explicit) - {"input", "output", "maj", "vendor", "shared_shell", "modular", "config_only", "zones_only", "zones_live", "title", "zones", "map_page", "thumb", "default",
                                  "region_name", "region_url", "region_xy", "region_spawn"}
    kw.update(tile_radius=clamp(a.tile_radius, 10, 5000), tile_margin=clamp(a.tile_margin, 0, 5000), tile_max_mo=clamp(a.tile_max_mo, 1, 100000),
              tile_max_tri=int(clamp(a.tile_max_tri, 1000, 10**9)), tile_concurrency=int(clamp(a.tile_concurrency, 1, 16)))
    if "room" not in explicit:
        kw["room"] = str(old.get("room") or "")
    if "lib_url" not in explicit:
        kw["lib_url"] = str(old.get("libUrl") or "")   # v37 : le choix du dossier lib est retenu dans la config
    cfg_lib = kw["lib_url"]
    kw["lib_url"] = effective_lib_url(shell_path, cfg_lib, "lib_url" in explicit)   # v45 : la ligne const LIB de la coquille existante (modifiee a la main) l'emporte sur la config
    if kw["lib_url"] != cfg_lib:
        explicit.add("lib_url")
        print(_tr("py.glb2html.maj_lib_repris", kw["lib_url"]))
    tdoc = None
    if a.tiles:
        tp = find_beside(a.tiles)
        if tp is None:
            sys.exit(_tr("py.glb2html.erreur_0_introuvable_cherche_dans_1", a.tiles, pathlib.Path.cwd(), pathlib.Path(__file__).resolve().parent))
        tdoc = read_tiles_index(tp)
        kw["tiles"] = place_tiles(tp, tdoc, out.parent)
        explicit.add("tiles")
    if a.register:
        a2 = argparse.Namespace(**vars(a))
        a2.presence_url = a.presence_url or old.get("presenceUrl") or ""
        if a2.thumb and not re.match(r"^https?://", str(a2.thumb), re.I) and page_path(a2.thumb, out.parent).is_file():
            a2.thumb = str(page_path(a2.thumb, out.parent))
        entry = region_entry(a2, S_reg, kw["room"] or out.stem, out.stem, page_name_of(a, out))
        reg = page_path(a.register, out.parent)
        kw["map_entries"] = register_region(reg, entry)
        print(_tr("py.glb2html.carte_0_ajoutee_ou_mise_a", entry['name'], reg, len(kw['map_entries'])))
        explicit.add("register")
    elif a.map:
        explicit.add("map")
    elif a.region_name or a.region_url or a.region_xy or a.region_spawn or a.thumb:
        print(_tr("py.glb2html.avertissement_region_name_region_url_region"), file=sys.stderr)
    if not a.register and not a.map and "map" not in explicit:
        kw["map_entries"] = old.get("map") if isinstance(old.get("map"), list) else []
    new = build_cfg(out.stem, **{k: v for k, v in kw.items() if k != "title"}, modular=True)
    cfg, changes = merge_maj_cfg(old, new, explicit)
    if a.input:
        inp = pathlib.Path(a.input)
        if not inp.is_file():
            sys.exit(_tr("py.glb2html.0_introuvable", inp))
        try:
            inspect_glb(inp.read_bytes(), inp.name)
        except ValueError as e:
            sys.exit(_tr("py.glb2html.erreur_0", e))
        write_atomic(glb_out, inp.read_bytes())
        print(_tr("py.glb2html.maj_0_remplace_par_1", glb_out.name, inp.name))
    elif not a.tiles and not old.get("tiles") and not glb_out.is_file():
        print(_tr("py.glb2html.avertissement_0_introuvable_a_cote_de", glb_out.name), file=sys.stderr)
    write_atomic(cfg_out, json.dumps(cfg, ensure_ascii=False, indent=1).encode("utf-8"))
    print(_tr("py.glb2html.maj_0_mis_a_jour_glb2html", cfg_out.name, VERSION) + (_tr("py.glb2html.0_cle_s_changee_s", len(changes)) if changes else _tr("py.glb2html.aucune_cle_changee")) + _tr("py.glb2html.0_gardee_s_telle_s_quelle", len(old) - len([c for c in changes if c[0] in old])))
    for k, o, n in changes:
        print(f"  {k} : {json.dumps(o, ensure_ascii=False)[:80]} -> {json.dumps(n, ensure_ascii=False)[:80]}")
    if "profile" in explicit:
        print(_tr("py.glb2html.maj_le_profil_ne_filtre_les"))
    if a.zones:
        zf = find_beside(a.zones)
        if zf is None:
            sys.exit(_tr("py.glb2html.erreur_0_introuvable", a.zones))
        try:
            kw["zones"] = json.loads(zf.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as e:
            sys.exit(_tr("py.glb2html.erreur_0_illisible_1", zf, e))
        if zones_out.is_file() and zf.resolve() == zones_out.resolve():
            print(_tr("py.glb2html.zones_zones_deja_en_place_0", zones_out))
        else:
            write_modular_zones(zones_out, kw)
    else:
        print(_tr("py.glb2html.maj_0_conserve_tel_quel", zones_out.name) + ("" if zones_out.is_file() else _tr("py.glb2html.absent_paren")))
    lib_url = kw.get("lib_url") or ""
    libtxt = lib_prefix(lib_url).lstrip("./") + "/three-" + THREE_VERSION
    print("[update] " + renew_shell(shell_path, build_shell(lib_url)))
    sdir = shell_dir_of(a.shared_shell, out) if a.shared_shell else out.parent
    if lib_missing(sdir, lib_url):
        write_modular_lib(sdir, a.vendor, lib_url)
        print(_tr("py.glb2html.maj_0_absent_ou_incomplet_ecrit", libtxt))
    else:
        print(_tr("py.glb2html.maj_0_present_conserve", libtxt))
    if a.shared_shell and a.default:   # --update n'écrase jamais default.json sans --default
        write_default_json(sdir, rname, True)
    if a.map_page:
        entries = cfg.get("map") or []
        if clean_map(entries):
            mp = pathlib.Path(a.map_page)
            write_map_page(mp if mp.is_absolute() else out.parent / mp, entries, cfg.get("presenceUrl", ""), cfg.get("mapUrl", ""), a.title or _tr("py.glb2html.carte_des_mondes"))
        else:
            print(_tr("py.glb2html.avertissement_map_page_ignore_aucune_region"), file=sys.stderr)
    if a.register or a.map_page or a.thumb or a.map:
        print(_tr("py.glb2html.carte_avec_maj_les_chemins_relatifs", out.parent.resolve()))
    adr = shell_page_address(a.shared_shell, rname) if a.shared_shell else out.name
    print(_tr("py.glb2html.ok_region_mise_a_jour_adresse", adr, VERSION))
    sys.exit(0)


def vec3(s: str):
    v = tuple(float(x) for x in s.split(","))
    if len(v) != 3:
        raise argparse.ArgumentTypeError(_tr("py.glb2html.format_attendu_x_y_z"))
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
            sys.exit(_tr("py.glb2html.erreur_region_xy_attend_deux_nombres"))
    return entry


def page_name_of(a, out):
    """Adresse relative de la région pour la carte : la page elle-même, ou COQUILLE.html?region=NOM avec une coquille commune."""
    return shell_page_address(a.shared_shell, region_of(a.shared_shell, out) or out.stem) if a.shared_shell else out.name


def main():
    ap = argparse.ArgumentParser(description=_tr("py.glb2html.desc", VERSION), epilog=_tr("py.glb2html.epilog"), formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False)
    i18n_add_common(ap)
    ap.add_argument("--version", action="version", version=f"glb2html {VERSION}", help=_tr("py.common.version"))
    ap.add_argument("input", nargs="?", help=_tr("py.glb2html.fichier_glb_ou_dossier_de_glb"))
    ap.add_argument("--zones-live", nargs="?", const="auto", default=(ZONES_LIVE or None), metavar="NAME", help=_tr("py.glb2html.la_page_recharge_ses_zones_a"))
    ap.add_argument("--zones-only", action="store_true", help=_tr("py.glb2html.reecrit_seulement_les_zones_sans_regenerer"))
    ap.add_argument("-o", "--output", help=_tr("py.glb2html.sortie_fichier_html_ou_dossier_cree"))
    ap.add_argument("--rotate", type=int, choices=(0, 90, 180, 270), default=ROTATE, help=_tr("py.glb2html.rotation_de_la_region_autour_de"))
    ap.add_argument("--hole", type=float, default=HOLE_RADIUS, help=_tr("py.glb2html.rayon_du_trou_30_600_zone"))
    ap.add_argument("--hole-fade", type=float, default=HOLE_FADE, help=_tr("py.glb2html.demi_largeur_du_fondu_du_trou"))
    ap.add_argument("--hole-x", type=float, default=HOLE_X, help=_tr("py.glb2html.position_x_du_centre_du_trou"))
    ap.add_argument("--hole-z", type=float, default=HOLE_Z, help=_tr("py.glb2html.position_z_du_centre_du_trou"))
    ap.add_argument("--wave", type=float, default=WAVE_AMP, help=_tr("py.glb2html.amplitude_vagues_0_10"))
    ap.add_argument("--sea-y", type=float, default=SEA_Y, help=_tr("py.glb2html.hauteur_mer_150_60"))
    ap.add_argument("--zoom", type=float, default=ZOOM_RATIO, help=_tr("py.glb2html.ratio_de_cadrage_1_cadrage_auto"))
    ap.add_argument("--cam-dir", type=vec3, default=CAM_DIR, help=_tr("py.glb2html.direction_camera_x_y_z"))
    ap.add_argument("--target", type=vec3, default=TARGET, help=_tr("py.glb2html.cible_camera_x_y_z"))
    ap.add_argument("--foliage-cutout", type=float, default=FOLIAGE_CUTOUT, help=_tr("py.glb2html.seuil_alpha_feuillage_0_0_5"))
    ap.add_argument("--sea-color", type=hexcolor, default=SEA_COLOR, help=_tr("py.glb2html.couleur_mer_ex_3a9ad9"))
    ap.add_argument("--sky-color", type=hexcolor, default=SKY_COLOR, help=_tr("py.glb2html.couleur_ciel_ex_87ceeb"))
    ap.add_argument("--sea-segments", type=int, default=SEA_SEGMENTS, help=_tr("py.glb2html.finesse_du_maillage_de_la_mer"))
    ap.add_argument("--walk", action=argparse.BooleanOptionalAction, default=WALK_ENABLED, help=_tr("py.glb2html.inclure_le_mode_promenade_touche_f"))
    ap.add_argument("--eye-height", type=float, default=EYE_HEIGHT, help=_tr("py.glb2html.hauteur_des_yeux_en_m_promenade"))
    ap.add_argument("--walk-speed", type=float, default=WALK_SPEED, help=_tr("py.glb2html.vitesse_de_marche_en_m_s"))
    ap.add_argument("--walk-ignore", default=WALK_IGNORE, help=_tr("py.glb2html.noms_a_ignorer_en_collision_separes"))
    ap.add_argument("--names", action=argparse.BooleanOptionalAction, default=NAMES_ENABLED, help=_tr("py.glb2html.afficher_le_nom_de_l_element"))
    ap.add_argument("--presence-url", default=PRESENCE_URL, help=_tr("py.glb2html.serveur_de_presence_ws_ou_wss"))
    ap.add_argument("--chat", action=argparse.BooleanOptionalAction, default=CHAT_ENABLED, help=_tr("py.glb2html.chat_entre_visiteurs_necessite_presence_url"))
    ap.add_argument("--chat-fade", type=float, default=CHAT_FADE, help=_tr("py.glb2html.secondes_avant_disparition_des_messages_et"))
    ap.add_argument("--zones", type=pathlib.Path, help=_tr("py.glb2html.fichier_json_de_zones_exporte_par"))
    ap.add_argument("--profile", type=lambda v: PROFILE_OLD.get(v, v), choices=("public", "private"), default=PROFILE, help=_tr("py.glb2html.public_retire_les_zones_privees_ex"))
    ap.add_argument("--spectate", action=argparse.BooleanOptionalAction, default=SPECTATE, help=_tr("py.glb2html.voir_les_visiteurs_en_promenade_depuis"))
    ap.add_argument("--panel", action=argparse.BooleanOptionalAction, default=PANEL, help=_tr("py.glb2html.panneau_de_reglages_pour_les_visiteurs"))
    ap.add_argument("--map", type=pathlib.Path, help=_tr("py.glb2html.fichier_regions_json_carte_des_mondes"))
    ap.add_argument("--map-url", default=MAP_URL, help=_tr("py.glb2html.adresse_s_de_regions_json_partage"))
    ap.add_argument("--register", help=_tr("py.glb2html.fichier_regions_json_a_mettre_a"))
    ap.add_argument("--region-name", help=_tr("py.glb2html.nom_affiche_dans_la_carte_defaut"))
    ap.add_argument("--region-url", help=_tr("py.glb2html.adresse_de_la_page_de_cette"))
    ap.add_argument("--region-xy", metavar="X,Y", help=_tr("py.glb2html.position_sur_la_grille_comme_opensim"))
    ap.add_argument("--region-spawn", help=_tr("py.glb2html.identifiant_du_point_d_arrivee_des"))
    ap.add_argument("--thumb", help=_tr("py.glb2html.vignette_de_la_region_fichier_jpg"))
    ap.add_argument("--map-page", metavar="FILE.html", help=_tr("py.glb2html.genere_aussi_une_page_web_carte"))
    ap.add_argument("--settings", nargs="?", const="auto", default=None, metavar="FILE", help=_tr("py.glb2html.reprend_tous_les_reglages_enregistres_par"))
    ap.add_argument("--modular", action="store_true", help=_tr("py.glb2html.mode_modulaire_ecrit_une_coquille_page"))
    ap.add_argument("--shared-shell", nargs="?", const=DEFAULT_SHELL, default=None, metavar="SHELL.html", help=_tr("py.glb2html.mode_modulaire_a_coquille_commune_une", DEFAULT_SHELL))
    ap.add_argument("--tiles", type=pathlib.Path, metavar="X.tiles.json", help=_tr("py.glb2html.region_decoupee_en_tuiles_par_glb2tiles"))
    ap.add_argument("--tile-radius", type=float, default=TILE_RADIUS, help=_tr("py.glb2html.m_charger_les_tuiles_dont_la"))
    ap.add_argument("--tile-margin", type=float, default=TILE_MARGIN, help=_tr("py.glb2html.m_decharger_les_tuiles_au_dela"))
    ap.add_argument("--tile-max-mb", metavar="TILE_MAX_MB", dest="tile_max_mo", type=float, default=TILE_MAX_MO, help=_tr("py.glb2html.mo_de_tuiles_chargees_en_meme"))
    ap.add_argument("--tile-max-triangles", metavar="TILE_MAX_TRIANGLES", dest="tile_max_tri", type=int, default=TILE_MAX_TRI, help=_tr("py.glb2html.triangles_de_tuiles_chargees_en_meme"))
    ap.add_argument("--tile-concurrency", type=int, default=TILE_CONCURRENCY, help=_tr("py.glb2html.telechargements_simultanes_defaut_default_d"))
    ap.add_argument("--config-only", action="store_true", help=_tr("py.glb2html.reecrit_seulement_page_config_json_d"))
    ap.add_argument("--zone-marker", type=lambda v: ZONE_MARKER_OLD.get(v, v), choices=ZONE_MARKERS, default=ZONE_MARKER, help=_tr("py.glb2html.marqueur_des_portails_et_zones_libres"))
    ap.add_argument("--zone-cone", action=argparse.BooleanOptionalAction, default=ZONE_CONE, help=_tr("py.glb2html.petit_cone_pointe_vers_le_bas"))
    ap.add_argument("--show-spawns", action=argparse.BooleanOptionalAction, default=SHOW_SPAWNS, help=_tr("py.glb2html.dessine_aussi_les_arrivees_dans_la"))
    ap.add_argument("--zone-info-dist", type=float, default=ZONE_INFO_DIST, metavar="M", help=_tr("py.glb2html.distance_5_a_200_m_defaut"))
    ap.add_argument("--lib-url", default="", metavar="PATH", help=_tr("py.glb2html.lib_url"))
    ap.add_argument("--default", action="store_true", help=_tr("py.glb2html.default_region"))
    ap.add_argument("--compass", action=argparse.BooleanOptionalAction, default=COMPASS, help=_tr("py.glb2html.compass"))
    ap.add_argument("--north", type=float, default=NORTH_DEG, metavar="DEGREES", help=_tr("py.glb2html.north"))
    ap.add_argument("--fly", action=argparse.BooleanOptionalAction, default=FLY_ENABLED, help=_tr("py.glb2html.vol_en_promenade_touche_f_ou"))
    ap.add_argument("--update", dest="maj", action="store_true", help=_tr("py.glb2html.met_a_jour_une_region_deja"))
    ap.add_argument("--room", default=ROOM, help=_tr("py.glb2html.salon_de_presence_defaut_nom_du"))
    ap.add_argument("--sea", metavar="SEA", dest="sea_enabled", action=argparse.BooleanOptionalAction, default=SEA_ENABLED, help=_tr("py.glb2html.help.sea"))
    ap.add_argument("--anim", metavar="ANIM", dest="anim_enabled", action=argparse.BooleanOptionalAction, default=ANIM_ENABLED, help=_tr("py.glb2html.help.anim"))
    ap.add_argument("--retina", action=argparse.BooleanOptionalAction, default=RETINA_ENABLED, help=_tr("py.glb2html.haute_resolution_rendu_x2_minimum_supersampl"))
    ap.add_argument("--light", action=argparse.BooleanOptionalAction, default=LIGHT_ENABLED, help=_tr("py.glb2html.help.light"))
    ap.add_argument("--title", help=_tr("py.glb2html.titre_de_la_page"))
    ap.add_argument("--vendor", type=pathlib.Path, help=_tr("py.glb2html.racine_d_un_paquet_npm_three"))
    a = ap.parse_args()
    S = {}
    if a.maj and a.settings:
        sys.exit(_tr("py.glb2html.erreur_maj_et_settings_s_excluent"))
    if a.settings:
        if str(a.settings).lower().endswith((".glb", ".gltf")) and not a.input:
            a.input, a.settings = a.settings, "auto"
        if a.settings == "auto":
            if not a.input:
                sys.exit(_tr("py.glb2html.erreur_settings_sans_nom_demande_le"))
            wanted = pathlib.Path(a.input).stem + ".reglages.json"
        else:
            wanted = a.settings
        sp = find_beside(wanted)
        if sp is None:
            sys.exit(_tr("py.glb2html.erreur_fichier_de_reglages_0_introuvable", wanted, pathlib.Path.cwd(), pathlib.Path(__file__).resolve().parent))
        try:
            S = json.loads(sp.read_text(encoding="utf-8"))
            if not isinstance(S, dict) or not isinstance(S.get("cfg"), dict):
                raise ValueError(_tr("py.glb2html.ce_n_est_pas_un_fichier"))
        except (OSError, ValueError) as e:
            sys.exit(_tr("py.glb2html.erreur_0_illisible_1", sp, e))
        defaults = settings_defaults(S)
        ap.set_defaults(**defaults)
        keep_input = a.input
        a = ap.parse_args()
        if str(a.settings).lower().endswith((".glb", ".gltf")) and not a.input:
            a.input, a.settings = a.settings, "auto"
        if not a.input:
            a.input = keep_input
        print(_tr("py.glb2html.reglages_0_parametre_s_repris_de", len(defaults), sp))
    if a.shared_shell:
        raw = str(a.shared_shell)
        sp = pathlib.PurePath(raw.replace("\\", "/"))
        if not sp.name.lower().endswith((".html", ".htm")):
            sys.exit(_tr("py.glb2html.erreur_shared_shell_attend_un_nom", raw))
        a.shared_shell = ShellRef(sp.name)
        if "/" in raw.replace("\\", "/"):
            a.shared_shell.dir = pathlib.Path(raw).parent   # v37 : --shared-shell DOSSIER/index.html, régions en sous-dossiers
        a.modular = True
    try:
        clean_lib_url(a.lib_url)
    except ValueError:
        sys.exit(_tr("py.glb2html.erreur_lib_url_refuse", a.lib_url))
    if a.default and not a.shared_shell:
        print(_tr("py.glb2html.avertissement_default_ignore_sans_shared_shell"), file=sys.stderr)
    S_reg = S.get("thisReg") if isinstance(S.get("thisReg"), dict) else {}
    S_cmd = S.get("cmd") if isinstance(S.get("cmd"), dict) else {}
    if S and not a.output and S_cmd.get("dest"):
        a.output = S_cmd["dest"]
    if S and not a.map_page and S_cmd.get("mapPage"):
        a.map_page = S_cmd["mapPage"]

    map_arg = None
    if a.map and a.maj and a.output and not pathlib.Path(a.map).is_absolute() and page_path(a.map, pathlib.Path(a.output).parent).is_file():
        a.map = str(page_path(a.map, pathlib.Path(a.output).parent))   # --update : chemin relatif = relatif au dossier de la page
    if a.map:
        mf = find_beside(a.map)
        if mf is None:
            sys.exit(_tr("py.glb2html.erreur_0_introuvable_cherche_dans_1", a.map, pathlib.Path.cwd(), pathlib.Path(__file__).resolve().parent))
        try:
            map_arg = json.loads(mf.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            sys.exit(_tr("py.glb2html.erreur_0_illisible_1", mf, e))
        print(_tr("py.glb2html.carte_0_region_s_lue_s", len(clean_map(map_arg)), mf))
    zones_arg = S.get("zones") if (S and not a.zones and isinstance(S.get("zones"), list)) else None
    if a.zones:
        zf = find_beside(a.zones)
        if zf is None:
            sys.exit(_tr("py.glb2html.erreur_0_introuvable_cherche_dans_1", a.zones, pathlib.Path.cwd(), pathlib.Path(__file__).resolve().parent))
        try:
            zones_arg = json.loads(zf.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            sys.exit(_tr("py.glb2html.erreur_0_illisible_1", zf, e))
        print(_tr("py.glb2html.zones_0_zone_s_lue_s", len(zones_arg) if isinstance(zones_arg, list) else 0, zf))

    kw = dict(rotate=a.rotate, hole=clamp(a.hole, 30, 600), hole_fade=max(0.0, a.hole_fade), hole_x=a.hole_x, hole_z=a.hole_z, wave=clamp(a.wave, 0, 10),
              sea_y=clamp(a.sea_y, -150, 60), zoom=clamp(a.zoom, 0.05, 100), cam_dir=a.cam_dir, target=a.target,
              foliage_cutout=clamp(a.foliage_cutout, 0, 1), sea_color=a.sea_color, sky_color=a.sky_color, sea_segments=int(clamp(a.sea_segments, 8, 1000)), walk=a.walk, walk_ignore=a.walk_ignore, zones_live=a.zones_live or "", map_entries=map_arg, map_url=a.map_url, names=a.names, presence_url=a.presence_url, room=a.room, chat=a.chat, chat_fade=clamp(a.chat_fade, 0, 3600), zones=zones_arg, profile=a.profile, spectate=a.spectate, panel=a.panel, eye_height=clamp(a.eye_height, 0.3, 5), walk_speed=clamp(a.walk_speed, 0.5, 30),
              sea_enabled=a.sea_enabled, anim_enabled=a.anim_enabled, retina=a.retina, light=a.light, title=a.title,
              zone_marker=a.zone_marker, show_spawns=a.show_spawns, zone_cone=a.zone_cone, fly=a.fly, zone_info_dist=clamp(a.zone_info_dist, 5, 500), compass=a.compass, north=a.north, lib_url=clean_lib_url(a.lib_url)[0], make_default=a.default,
              target_explicit=bool(tuple(a.target) != tuple(TARGET) or TARGET_EXPLICIT or getattr(a, "target_explicit", False)))

    if a.maj:
        run_maj(a, kw, explicit_dests(ap), S_reg)
    if a.zones_live and not a.input and str(a.zones_live).lower().endswith((".glb", ".gltf")):
        a.input, a.zones_live = a.zones_live, "auto"
        kw["zones_live"] = "auto"
    if a.zones_only:
        if not a.output:
            sys.exit(_tr("py.glb2html.erreur_zones_only_demande_o_page"))
        out = pathlib.Path(a.output)
        if a.zones_live:   # page autonome qui recharge ses zones
            write_live_zones(out, dict(kw, zones_live=a.zones_live))
            sys.exit(0)
        if not out.suffix:
            out = out.with_suffix(".html")
        if not (modular_names(out)[1].is_file() or a.modular):
            sys.exit(_tr("py.glb2html.erreur_zones_only_demande_zones_live", modular_names(out)[1].name))
        if zones_arg is None:
            sys.exit(_tr("py.glb2html.erreur_zones_only_demande_zones_fichier"))
        write_modular_zones(modular_names(out)[2], kw)
        sys.exit(0)
    if a.config_only and not a.tiles:
        if not a.output:
            sys.exit(_tr("py.glb2html.erreur_config_only_demande_o_page"))
        out = pathlib.Path(a.output)
        if not out.suffix:
            out = out.with_suffix(".html")
        glb_out, cfg_out, zones_out = modular_names(out)
        if a.shared_shell:
            if not glb_out.is_file() or not shell_file(a.shared_shell, out).is_file():
                sys.exit(_tr("py.glb2html.erreur_0_ou_1_introuvable_genere", a.shared_shell, glb_out.name))
        elif not out.is_file() or not glb_out.is_file():
            sys.exit(_tr("py.glb2html.erreur_0_ou_1_introuvable_genere_2", out, glb_out.name))
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
            print(_tr("py.glb2html.carte_0_ajoutee_ou_mise_a", entry['name'], reg, len(kw['map_entries'])))
            where_note(reg, a.output)
        write_config(cfg_out, name, kw)
        print(_tr("py.glb2html.ok_reglages_0_coquille_et_glb", cfg_out, VERSION))
        if a.zones:   # les zones ne sont touchées que si --zones est donné
            write_modular_zones(zones_out, kw)
        else:
            print(_tr("py.glb2html.zones_0_non_modifie_donne_zones", zones_out.name))
        if a.map_page and kw.get("map_entries") is not None and clean_map(kw["map_entries"]):
            mp = pathlib.Path(a.map_page)
            write_map_page(mp if mp.is_absolute() else out.parent / mp, kw["map_entries"], kw.get("presence_url", ""), kw.get("map_url", ""), a.title or _tr("py.glb2html.carte_des_mondes"))
        sys.exit(0)
    if a.tiles:
        if a.input:
            sys.exit(_tr("py.glb2html.erreur_tiles_remplace_le_glb_ne"))
        if not a.output:
            sys.exit(_tr("py.glb2html.erreur_tiles_demande_o_region_html"))
        out = pathlib.Path(a.output)
        if out.is_dir() or str(a.output).endswith(("/", "\\")):
            sys.exit(_tr("py.glb2html.erreur_avec_tiles_o_designe_la"))
        if not out.suffix:
            out = out.with_suffix(".html")
        tp = find_beside(a.tiles)
        if tp is None:
            sys.exit(_tr("py.glb2html.erreur_0_introuvable_cherche_dans_1", a.tiles, pathlib.Path.cwd(), pathlib.Path(__file__).resolve().parent))
        tdoc = read_tiles_index(tp)
        if a.target == TARGET:
            kw["target"] = tiles_default_target(tdoc, a.rotate)
            print(_tr("py.glb2html.tuiles_cible_de_camera_par_defaut", kw['target']))
        if a.sea_y == SEA_Y:
            kw["sea_y"] = 20.0
            print(_tr("py.glb2html.tuiles_hauteur_de_la_mer_par"))
        kw.update(tile_radius=clamp(a.tile_radius, 10, 5000), tile_margin=clamp(a.tile_margin, 0, 5000), tile_max_mo=clamp(a.tile_max_mo, 1, 100000),
                  tile_max_tri=int(clamp(a.tile_max_tri, 1000, 10**9)), tile_concurrency=int(clamp(a.tile_concurrency, 1, 16)))
        if a.shared_shell and not valid_region_name(region_of(a.shared_shell, out) or ""):
            sys.exit(_tr("py.glb2html.erreur_nom_de_region_0_refuse_3", region_of(a.shared_shell, out) or out.stem))
        if a.register:
            entry = region_entry(a, S_reg, a.room or out.stem, out.stem, page_name_of(a, out))
            reg = data_path(a.register)
            kw["map_entries"] = register_region(reg, entry)
            print(_tr("py.glb2html.carte_0_ajoutee_ou_mise_a", entry['name'], reg, len(kw['map_entries'])))
            where_note(reg, a.output)
        if a.zones and zf is not None:
            zdest = modular_names(out)[2]
            if zdest.is_file() and zf.resolve() == zdest.resolve():
                kw["zones_keep"] = True
                print(_tr("py.glb2html.zones_zones_deja_en_place_0_2", zdest))
        ok = generate_tiles(tp, tdoc, out, a.vendor, shell=a.shared_shell, **kw)
        if ok and a.map_page:
            entries = kw["map_entries"] if kw.get("map_entries") is not None else json.loads(MAP_JSON)
            if clean_map(entries):
                mp = pathlib.Path(a.map_page)
                write_map_page(mp if mp.is_absolute() else out.parent / mp, entries, kw.get("presence_url", ""), kw.get("map_url", ""), a.title or _tr("py.glb2html.carte_des_mondes"))
            else:
                print(_tr("py.glb2html.avertissement_map_page_ignore_aucune_region_2"), file=sys.stderr)
        sys.exit(0 if ok else 1)
    if a.register and not a.input:
        if not (a.region_name and a.region_url and a.room):
            sys.exit(_tr("py.glb2html.erreur_enregistrer_une_region_sans_glb"))
        entry = {"id": _slug(a.room) or "region", "name": a.region_name, "url": a.region_url, "room": a.room,
                 "spawn": a.region_spawn or None, "thumb": thumb_data_url(a.thumb) if a.thumb else "",
                 "presence": fix_presence_url(a.presence_url) if a.presence_url else None}
        if a.region_xy:
            try:
                x, y = (int(float(v)) for v in a.region_xy.split(","))
                entry["x"], entry["y"] = x, y
            except ValueError:
                sys.exit(_tr("py.glb2html.erreur_region_xy_attend_deux_nombres"))
        reg = data_path(a.register)
        data = register_region(reg, entry)
        print(_tr("py.glb2html.carte_0_ajoutee_ou_mise_a", entry['name'], reg, len(data)))
        if a.map_page:
            write_map_page(pathlib.Path(a.map_page), data, a.presence_url, a.map_url, a.title or _tr("py.glb2html.carte_des_mondes"))
        sys.exit(0)
    if a.map_page and not a.input:
        entries = map_arg if map_arg is not None else json.loads(MAP_JSON)
        if not clean_map(entries):
            sys.exit(_tr("py.glb2html.erreur_aucune_region_a_afficher_donne"))
        write_map_page(pathlib.Path(a.map_page), entries, a.presence_url, a.map_url, a.title or _tr("py.glb2html.carte_des_mondes"))
        sys.exit(0)
    if not a.input:
        ap.error(_tr("py.glb2html.le_fichier_glb_ou_le_dossier"))
    inp = pathlib.Path(a.input)
    if inp.is_dir() and (a.register or a.map_page):
        print(_tr("py.glb2html.avertissement_register_et_map_page_ne"), file=sys.stderr)
    if inp.is_dir():
        files = sorted(p for p in inp.iterdir() if p.suffix.lower() == ".glb")
        if not files:
            sys.exit(_tr("py.glb2html.aucun_glb_dans_0", inp))
        outdir = pathlib.Path(a.output) if a.output else None
        ok = sum(generate(f, (outdir or f.parent) / (f.stem + (".html" if a.shared_shell else " - Offline.html")), a.vendor, modular=a.modular, shell=a.shared_shell, **kw) for f in files)
        print(_tr("py.glb2html.0_1_fichiers_generes", ok, len(files)))
        sys.exit(0 if ok == len(files) else 1)
    if not inp.is_file():
        sys.exit(_tr("py.glb2html.0_introuvable", inp))
    if inp.suffix.lower() == ".gltf":
        sys.exit(_tr("py.glb2html.entree_gltf_repacker_d_abord_en"))
    if a.output:
        out = pathlib.Path(a.output)
        if out.is_dir() or str(a.output).endswith(("/", "\\")):
            out = out / (inp.stem + (".html" if a.shared_shell else " - Offline.html"))
        elif not out.suffix:
            out = out.with_suffix(".html")
    else:
        out = inp.with_name(inp.stem + (".html" if a.shared_shell else " - Offline.html"))
    if a.shared_shell and not valid_region_name(region_of(a.shared_shell, out) or ""):
        sys.exit(_tr("py.glb2html.erreur_nom_de_region_0_refuse_3", region_of(a.shared_shell, out) or out.stem))
    if a.register:
        entry = region_entry(a, S_reg, a.room or inp.stem, inp.stem, page_name_of(a, out))
        reg = data_path(a.register)
        kw["map_entries"] = register_region(reg, entry)
        print(_tr("py.glb2html.carte_0_ajoutee_ou_mise_a", entry['name'], reg, len(kw['map_entries'])))
        where_note(reg, a.output)
    ok = generate(inp, out, a.vendor, modular=a.modular, shell=a.shared_shell, **kw)
    if ok and a.map_page:
        entries = kw["map_entries"] if kw.get("map_entries") is not None else json.loads(MAP_JSON)
        if not clean_map(entries):
            print(_tr("py.glb2html.avertissement_map_page_ignore_aucune_region_2"), file=sys.stderr)
        else:
            mp = pathlib.Path(a.map_page)
            write_map_page(mp if mp.is_absolute() else out.parent / mp, entries, kw.get("presence_url", ""), kw.get("map_url", ""), a.title or _tr("py.glb2html.carte_des_mondes"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    sys.argv = old_options(sys.argv)
    main()
