#!/usr/bin/env python3
"""Fabrique glb2html.py, glb-viewer.html, presence_server.py, oar2glb.py, glb2tiles.py (et glb-stats.py) dans dist/ à partir de src/ et tools/.

Usage :  python build.py                  (télécharge three@0.160.0 depuis jsDelivr dans .cache/ au premier lancement)
         python build.py --vendor DOSSIER (racine d'un paquet npm three déjà présent : hors ligne)
         python build.py --out DOSSIER    (sortie ailleurs que dist/)
"""
import argparse, base64, json, pathlib, sys, types, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
THREE_VERSION = "0.160.0"
CDN = f"https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/"

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--vendor", type=pathlib.Path, help="racine d'un paquet npm three (sinon cache .cache/ + téléchargement)")
ap.add_argument("--out", type=pathlib.Path, default=ROOT / "dist", help="dossier de sortie (défaut : dist/)")
ap.add_argument("--i18n", type=pathlib.Path, default=SRC / "i18n", help="dossier des fichiers de langue <code>.json (défaut : src/i18n/) : ajouter une langue = ajouter un fichier")
args = ap.parse_args()
OUT = args.out
OUT.mkdir(parents=True, exist_ok=True)
CACHE = ROOT / ".cache" / f"three@{THREE_VERSION}"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
REVISION = (ROOT / "REVISION").read_text(encoding="utf-8").strip() if (ROOT / "REVISION").exists() else ""   # date jj/mm/aaaa + lettre : change a chaque patch du code (affichee par presence_server.py)


def vendor(rel):
    if args.vendor:
        p = args.vendor / rel
        if not p.is_file():
            sys.exit(f"[ERREUR] {p} introuvable (--vendor doit pointer sur la racine du paquet npm three)")
        return p.read_bytes()
    p = CACHE / rel
    if not p.is_file():
        p.parent.mkdir(parents=True, exist_ok=True)
        print(f"[cache] téléchargement {CDN + rel}")
        try:
            with urllib.request.urlopen(CDN + rel, timeout=60) as r:
                p.write_bytes(r.read())
        except Exception as e:
            sys.exit(f"[ERREUR] téléchargement impossible ({e}). Utilise --vendor <dossier three>.")
    return p.read_bytes()


# ---- langues (v36) : un fichier src/i18n/<code>.json par langue ; les clés « py.* » vont aux outils Python, les autres aux pages
LANGS = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(args.i18n.glob("*.json"))}
for need in ("fr", "en"):
    if need not in LANGS:
        sys.exit(f"[ERREUR] {args.i18n / (need + '.json')} manque (le français et l'anglais servent de repli)")
for code, d in LANGS.items():
    if not isinstance(d.get("_name"), str):
        sys.exit(f"[ERREUR] {code}.json : la clé _name (nom de la langue dans sa langue) manque")


def jsonjs(o):   # JSON sûr dans <script> et dans une chaîne Python r"""..."""
    return json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


WEB_I18N = {c: {k: v for k, v in d.items() if not k.startswith(("py.", "viewer."))} for c, d in LANGS.items()}      # pages exportées, coquille, page « carte »
VIEWER_I18N = {c: {k: v for k, v in d.items() if not k.startswith("py.")} for c, d in LANGS.items()}                # + les textes du viewer
PY_I18N = {c: {k: v for k, v in d.items() if k.startswith("py.") or k == "_name"} for c, d in LANGS.items()}
I18N_SRC = (SRC / "i18n.js").read_text(encoding="utf-8")
I18N_RT = I18N_SRC.replace("__I18N_DATA__", jsonjs(WEB_I18N))


def inline_i18n_py(text):
    """outils Python : le bloc « # <<I18N_PY>> … # <</I18N_PY>> » (qui charge src/i18n_py.py depuis les sources) devient le texte de i18n_py.py avec les langues intégrées"""
    mod = (SRC / "i18n_py.py").read_text(encoding="utf-8")
    mod = mod[mod.index('"""', mod.index('"""') + 3) + 3:].lstrip("\n")   # sans le docstring du module
    data = json.dumps(PY_I18N, ensure_ascii=False, separators=(",", ":"))
    assert "'''" not in data and not data.endswith("\\")
    assert "I18N_DATA = None  # __I18N_PY_DATA__" in mod
    mod = mod.replace("I18N_DATA = None  # __I18N_PY_DATA__", "I18N_DATA = _json.loads(r'''" + data + "''')")
    a, b = text.index("# <<I18N_PY>>"), text.index("# <</I18N_PY>>")
    return text[:a] + "# ---- langue des messages (v36) : textes intégrés par build.py (src/i18n/*.json, clés py.*) ; --lang fr|en|auto ou WEB3D_LANG ----\n" + mod + text[b + len("# <</I18N_PY>>"):]
I18N_RT_VIEWER = I18N_SRC.replace("__I18N_DATA__", jsonjs(VIEWER_I18N))

core = (SRC / "core.js").read_text(encoding="utf-8")
template = (SRC / "template.html").read_text(encoding="utf-8").replace("__CORE__", core).replace("__I18N__", I18N_RT)
draco_js = (SRC / "draco.js.txt").read_text(encoding="utf-8").rstrip("\n")
meshopt_js = (SRC / "meshopt.js.txt").read_text(encoding="utf-8").rstrip("\n")
for name, t in [("template", template), ("draco", draco_js), ("meshopt", meshopt_js)]:
    assert '"""' not in t, name          # ces textes sont insérés dans des chaînes Python r"""..."""
    assert not t.endswith("\\"), name


def jsurl(rel):
    txt = vendor(rel).decode("utf-8")
    txt = txt.replace("'../utils/BufferGeometryUtils.js'", "'three/addons/utils/BufferGeometryUtils.js'")
    txt = txt.replace("'./../utils/TextureUtils.js'", "'three/addons/utils/TextureUtils.js'")
    txt = txt.replace("'../utils/TextureUtils.js'", "'three/addons/utils/TextureUtils.js'")
    return "data:text/javascript;base64," + base64.b64encode(txt.encode()).decode()


mods = {
    "three": "build/three.module.js",
    "three/addons/controls/OrbitControls.js": "examples/jsm/controls/OrbitControls.js",
    "three/addons/loaders/GLTFLoader.js": "examples/jsm/loaders/GLTFLoader.js",
    "three/addons/utils/BufferGeometryUtils.js": "examples/jsm/utils/BufferGeometryUtils.js",
    "three/addons/loaders/DRACOLoader.js": "examples/jsm/loaders/DRACOLoader.js",
    "three/addons/libs/meshopt_decoder.module.js": "examples/jsm/libs/meshopt_decoder.module.js",
    "three/addons/exporters/GLTFExporter.js": "examples/jsm/exporters/GLTFExporter.js",
    "three/addons/utils/TextureUtils.js": "examples/jsm/utils/TextureUtils.js",
}
importmap = {"imports": {k: jsurl(v) for k, v in mods.items()}}
libs = {
    "draco_wasm_wrapper.js": "data:text/javascript;base64," + base64.b64encode(vendor("examples/jsm/libs/draco/gltf/draco_wasm_wrapper.js")).decode(),
    "draco_decoder.wasm": "data:application/wasm;base64," + base64.b64encode(vendor("examples/jsm/libs/draco/gltf/draco_decoder.wasm")).decode(),
}

py = inline_i18n_py((SRC / "gen_tpl.py").read_text(encoding="utf-8"))
py = py.replace("__HTML_TEMPLATE__", template).replace("__DRACO_JS__", draco_js).replace("__MESHOPT_JS__", meshopt_js)
py = py.replace("__I18N__", I18N_RT).replace("__VERSION__", VERSION)
assert "__I18N" not in py
(OUT / "glb2html.py").write_text(py, encoding="utf-8")
# la coquille modulaire est fabriquée par glb2html.py lui-même (build_shell) : le viewer en met une copie identique dans son .zip
gen = types.ModuleType("glb2html_build")
exec(compile(py, "glb2html.py", "exec"), gen.__dict__)
shell = gen.build_shell()
(OUT / "carte.html").write_bytes(gen.build_map_shell().encode("utf-8"))   # v47 : la page de carte universelle (lit regions.json à côté d'elle)
(OUT / "index.html").write_bytes(shell.encode("utf-8"))   # v45 : la coquille prête (dossier lib : ./lib), identique octet pour octet à celle de glb2html.py ; à copier à la place de --update (la ligne « const LIB » est à reporter si le dossier lib est ailleurs)
(OUT / "favicon.ico").write_bytes((SRC / "favicon.ico").read_bytes())   # icone par defaut des pages (a copier a cote de index.html ; la remplacer par la sienne change l'icone, sans refaire les pages)
shell_modules, shell_draco = gen.shell_lib_files()
shell_lib = {"dir": gen.LIB_REL, "modules": shell_modules, "draco": shell_draco}
(OUT / "presence_server.py").write_text(inline_i18n_py((SRC / "presence_server.py").read_text(encoding="utf-8")).replace("__VERSION__", VERSION).replace("__REVISION__", REVISION), encoding="utf-8")
(OUT / "oar2glb.py").write_text(inline_i18n_py((ROOT / "tools" / "oar2glb.py").read_text(encoding="utf-8")).replace("__VERSION__", VERSION), encoding="utf-8")
(OUT / "glb2tiles.py").write_text(inline_i18n_py((ROOT / "tools" / "glb2tiles.py").read_text(encoding="utf-8")).replace("__VERSION__", VERSION), encoding="utf-8")   # fonctions communes de glb2tiles.py : doit rester à côté


(OUT / "glb-stats.py").write_text(inline_i18n_py((ROOT / "tools" / "glb-stats.py").read_text(encoding="utf-8")), encoding="utf-8")   # fonctions communes de glb2tiles.py : doit rester à côté


def jsq(s):  # littéral JS sûr dans <script>
    return json.dumps(s).replace("</", "<\\/")


v = (SRC / "viewer_tpl.html").read_text(encoding="utf-8")
v = v.replace("__CORE__", core).replace("__I18N__", I18N_RT_VIEWER)  # core avant le reste : pas de placeholder dedans
v = v.replace("__TEMPLATE_JSON__", jsq(template)).replace("__PY_JSON__", jsq(py))
v = v.replace("__DRACO_JS_JSON__", jsq(draco_js)).replace("__MESHOPT_JS_JSON__", jsq(meshopt_js))
v = v.replace("__LIBS_JSON__", json.dumps(libs)).replace("__IMPORTMAP_JSON__", json.dumps(importmap))
v = v.replace("__SHELL_JSON__", jsq(shell)).replace("__SHELL_LIB_JSON__", json.dumps(shell_lib))
v = v.replace("__VERSION__", VERSION)
(OUT / "glb-viewer.html").write_text(v, encoding="utf-8")
print(f"[OK] coquille -> {OUT / 'index.html'} ({len(shell) // 1024} Ko) ; carte -> {OUT / 'carte.html'}")
print(f"[OK] {VERSION} -> {OUT} (glb2html.py {len(py) // 1024} Ko, glb-viewer.html {len(v) // 1024} Ko)")
