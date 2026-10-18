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
import struct
import sys
import urllib.request

# <<DEFAULTS>>
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
# <</DEFAULTS>>

SEA_SIZE = 4000

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
            "confirm": bool(z.get("confirm")), "private": bool(z.get("private")),
        })
    return out


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


def find_beside(path):
    """Chemin absolu : tel quel. Relatif : d'abord le dossier de lancement, puis le dossier de ce script."""
    path = pathlib.Path(path).expanduser()
    if path.is_absolute():
        return path if path.is_file() else None
    for base in (pathlib.Path.cwd(), pathlib.Path(__file__).resolve().parent):
        if (base / path).is_file():
            return base / path
    return None


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


def js_data_url(src: bytes) -> str:
    # les imports relatifs ne se résolvent pas depuis une URL data: -> spécificateurs nus de l'importmap
    txt = src.decode("utf-8").replace("'../utils/BufferGeometryUtils.js'", "'three/addons/utils/BufferGeometryUtils.js'")
    return "data:text/javascript;base64," + base64.b64encode(txt.encode("utf-8")).decode("ascii")


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


def build_html(glb: bytes, name: str, vendor_dir=None, *, hole=HOLE_RADIUS, hole_fade=HOLE_FADE, hole_x=HOLE_X, hole_z=HOLE_Z, wave=WAVE_AMP,
               sea_y=SEA_Y, zoom=ZOOM_RATIO, cam_dir=CAM_DIR, target=TARGET, sea_enabled=SEA_ENABLED,
               anim_enabled=ANIM_ENABLED, retina=RETINA_ENABLED, foliage_cutout=FOLIAGE_CUTOUT,
               sea_color=SEA_COLOR, sky_color=SKY_COLOR, sea_segments=SEA_SEGMENTS, walk=WALK_ENABLED, eye_height=EYE_HEIGHT, walk_speed=WALK_SPEED, walk_ignore=WALK_IGNORE, names=NAMES_ENABLED, presence_url=PRESENCE_URL, room=ROOM, chat=CHAT_ENABLED, chat_fade=CHAT_FADE, zones=None, profile=PROFILE, spectate=SPECTATE, panel=PANEL, zones_live=ZONES_LIVE, title=None) -> str:
    used = inspect_glb(glb, name)
    presence_url = fix_presence_url(presence_url)
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

    cfg = {
        "hole": float(hole), "holeFade": float(hole_fade), "holeX": float(hole_x), "holeZ": float(hole_z), "wave": float(wave), "seaY": float(sea_y),
        "zoom": float(zoom), "camDir": list(map(float, cam_dir)), "target": list(map(float, target)),
        "sea": bool(sea_enabled), "anim": bool(anim_enabled), "retina": bool(retina),
        "foliageCutout": float(foliage_cutout), "seaSize": SEA_SIZE, "seaSegments": int(sea_segments),
        "seaColor": int(sea_color), "skyColor": int(sky_color),
        "walk": bool(walk), "eyeHeight": float(eye_height), "walkSpeed": float(walk_speed), "walkIgnore": str(walk_ignore),
        "names": bool(names), "chat": bool(chat), "profile": profile, "version": VERSION, "panel": bool(panel), "zonesLive": str(zones_live or ""), "spectate": bool(presence_url) if spectate is None else bool(spectate),
        "zones": clean_zones(json.loads(ZONES_JSON) if zones is None else zones, profile), "chatFade": float(chat_fade), "presenceUrl": str(presence_url), "room": str(room) or pathlib.Path(name).stem,
    }
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


def generate(glb_path: pathlib.Path, out_path: pathlib.Path, vendor_dir, **kw):
    data = glb_path.read_bytes()
    if kw.get("zones_live"):
        kw = dict(kw, zones_live=live_zones_name(out_path, kw["zones_live"]))
    try:
        page = build_html(data, glb_path.name, vendor_dir, **kw)
    except ValueError as e:
        print(f"[ERREUR] {e}", file=sys.stderr)
        return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")
    write_live_zones(out_path, dict(kw, zones_live=kw.get("zones_live") or ""))
    print(f"[OK] {glb_path.name} -> {out_path} ({len(data) / 2**20:.2f} Mo glb, {len(page) / 2**20:.2f} Mo html) [glb2html {VERSION}]")
    return True


def vec3(s: str):
    v = tuple(float(x) for x in s.split(","))
    if len(v) != 3:
        raise argparse.ArgumentTypeError("format attendu : x,y,z")
    return v


def hexcolor(s: str) -> int:
    return int(s.lstrip("#"), 16)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def main():
    ap = argparse.ArgumentParser(description="GLB -> HTML autonome hors ligne (three.js intégré)")
    ap.add_argument("--version", action="version", version=f"glb2html {VERSION}")
    ap.add_argument("input", nargs="?", help="fichier .glb ou dossier de .glb")
    ap.add_argument("--zones-live", nargs="?", const="auto", default=(ZONES_LIVE or None), metavar="NOM", help="la page recharge ses zones à chaque ouverture depuis un fichier .zones.json placé à côté d'elle (servie en http/https ; sinon les zones intégrées servent). Sans NOM : <page>.zones.json. Le fichier est écrit par le script, filtré selon --profile")
    ap.add_argument("--zones-only", action="store_true", help="réécrit seulement le fichier .zones.json à côté de la page indiquée par -o, sans régénérer le HTML (avec --zones-live)")
    ap.add_argument("-o", "--output", help="sortie : fichier .html, ou dossier (créé si besoin). Entrée dossier : dossier de sortie. Défaut : \"<nom> - Offline.html\" à côté du .glb")
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
    ap.add_argument("--zones", type=pathlib.Path, help="fichier .json de zones exporté par le viewer ; chemin relatif : cherché dans le dossier de lancement, puis dans le dossier du script")
    ap.add_argument("--profile", choices=("public", "perso"), default=PROFILE, help="public : retire les zones privées (ex. Home Assistant) ; perso : les garde")
    ap.add_argument("--spectate", action=argparse.BooleanOptionalAction, default=SPECTATE, help="voir les visiteurs en promenade depuis la vue globale (se connecte dès l'ouverture de la page ; actif par défaut dès qu'une --presence-url est donnée ; --no-spectate pour l'éviter)")
    ap.add_argument("--panel", action=argparse.BooleanOptionalAction, default=PANEL, help="panneau de réglages pour les visiteurs (haute résolution, mer animée, force des vagues), bouton en haut à droite")
    ap.add_argument("--room", default=ROOM, help="salon de présence (défaut : nom du fichier)")
    ap.add_argument("--sea", dest="sea_enabled", action=argparse.BooleanOptionalAction, default=SEA_ENABLED)
    ap.add_argument("--anim", dest="anim_enabled", action=argparse.BooleanOptionalAction, default=ANIM_ENABLED)
    ap.add_argument("--retina", action=argparse.BooleanOptionalAction, default=RETINA_ENABLED, help="haute résolution : rendu x2 minimum (supersampling, plus net mais ~4x plus lourd)")
    ap.add_argument("--title", help="titre de la page")
    ap.add_argument("--vendor", type=pathlib.Path, help="racine d'un paquet npm three local (sinon cache + téléchargement)")
    a = ap.parse_args()

    zones_arg = None
    if a.zones:
        zf = find_beside(a.zones)
        if zf is None:
            sys.exit(f"[ERREUR] {a.zones} introuvable (cherché dans {pathlib.Path.cwd()} puis dans {pathlib.Path(__file__).resolve().parent})")
        try:
            zones_arg = json.loads(zf.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            sys.exit(f"[ERREUR] {zf} illisible ({e})")
        print(f"[zones] {len(zones_arg) if isinstance(zones_arg, list) else 0} zone(s) lue(s) dans {zf}")

    kw = dict(hole=clamp(a.hole, 30, 600), hole_fade=max(0.0, a.hole_fade), hole_x=a.hole_x, hole_z=a.hole_z, wave=clamp(a.wave, 0, 10),
              sea_y=clamp(a.sea_y, -150, 60), zoom=clamp(a.zoom, 0.05, 100), cam_dir=a.cam_dir, target=a.target,
              foliage_cutout=clamp(a.foliage_cutout, 0, 1), sea_color=a.sea_color, sky_color=a.sky_color, sea_segments=int(clamp(a.sea_segments, 8, 1000)), walk=a.walk, walk_ignore=a.walk_ignore, zones_live=a.zones_live or "", names=a.names, presence_url=a.presence_url, room=a.room, chat=a.chat, chat_fade=clamp(a.chat_fade, 0, 3600), zones=zones_arg, profile=a.profile, spectate=a.spectate, panel=a.panel, eye_height=clamp(a.eye_height, 0.3, 5), walk_speed=clamp(a.walk_speed, 0.5, 30),
              sea_enabled=a.sea_enabled, anim_enabled=a.anim_enabled, retina=a.retina, title=a.title)

    if a.zones_live and not a.input and str(a.zones_live).lower().endswith((".glb", ".gltf")):
        a.input, a.zones_live = a.zones_live, "auto"
        kw["zones_live"] = "auto"
    if a.zones_only:
        if not a.output or not a.zones_live:
            sys.exit("[ERREUR] --zones-only demande -o <page.html> et --zones-live")
        out = pathlib.Path(a.output)
        write_live_zones(out, dict(kw, zones_live=a.zones_live))
        sys.exit(0)
    if not a.input:
        ap.error("le fichier .glb (ou le dossier) est obligatoire")
    inp = pathlib.Path(a.input)
    if inp.is_dir():
        files = sorted(p for p in inp.iterdir() if p.suffix.lower() == ".glb")
        if not files:
            sys.exit(f"Aucun .glb dans {inp}")
        outdir = pathlib.Path(a.output) if a.output else None
        ok = sum(generate(f, (outdir or f.parent) / (f.stem + " - Offline.html"), a.vendor, **kw) for f in files)
        print(f"{ok}/{len(files)} fichiers générés")
        sys.exit(0 if ok == len(files) else 1)
    if not inp.is_file():
        sys.exit(f"{inp} introuvable")
    if inp.suffix.lower() == ".gltf":
        sys.exit("Entrée .gltf : repacker d'abord en .glb (npx @gltf-transform/cli copy in.gltf out.glb)")
    if a.output:
        out = pathlib.Path(a.output)
        if out.is_dir() or str(a.output).endswith(("/", "\\")):
            out = out / (inp.stem + " - Offline.html")
        elif not out.suffix:
            out = out.with_suffix(".html")
    else:
        out = inp.with_name(inp.stem + " - Offline.html")
    sys.exit(0 if generate(inp, out, a.vendor, **kw) else 1)


if __name__ == "__main__":
    main()
