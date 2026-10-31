#!/usr/bin/env python3
"""Fabrique glb2html.py, glb-viewer.html, presence_server.py, oar2glb.py, glb2tiles.py (et glb-stats.py) dans dist/ à partir de src/ et tools/.

Usage :  python build.py                  (télécharge three@0.160.0 depuis jsDelivr dans .cache/ au premier lancement)
         python build.py --vendor DOSSIER (racine d'un paquet npm three déjà présent : hors ligne)
         python build.py --out DOSSIER    (sortie ailleurs que dist/)
"""
import argparse, base64, hashlib, json, pathlib, sys, types, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
THREE_VERSION = "0.160.0"
CDN = f"https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/"

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--vendor", type=pathlib.Path, help="racine d'un paquet npm three (sinon cache .cache/ + téléchargement)")
ap.add_argument("--out", type=pathlib.Path, default=ROOT / "dist", help="dossier de sortie (défaut : dist/)")
ap.add_argument("--i18n", type=pathlib.Path, default=SRC / "i18n", help="dossier des fichiers de langue <code>.json (défaut : src/i18n/) : ajouter une langue = ajouter un fichier")
ap.add_argument("--empreintes", type=pathlib.Path, help="écrit dans ce fichier l'empreinte neutre (sans numéro de version) de chaque fichier à numéro, puis s'arrête : sert à reconstituer VERSIONS.json depuis l'historique")
args = ap.parse_args()
OUT = args.out
OUT.mkdir(parents=True, exist_ok=True)
CACHE = ROOT / ".cache" / f"three@{THREE_VERSION}"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


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

def jsq(s):  # littéral JS sûr dans <script>
    return json.dumps(s).replace("</", "<\\/")


# Version par fichier : chaque fichier de dist/ qui porte un numéro de version affiche le sien, qui ne change que si le contenu de CE fichier change.
# Principe : on fabrique tout avec un numéro neutre (NEUTRE), on empreinte chaque fichier, on compare à VERSIONS.json (dernière empreinte et numéro du lot
# qui l'a modifié) ; seul un fichier dont l'empreinte a changé prend le numéro du lot courant (fichier VERSION) ; puis on refabrique avec les vrais numéros.
NEUTRE = "0.0.0 (00/00/0000)"
FICHIERS_VERSION = ["glb2html.py", "index.html", "carte.html", "glb-viewer.html", "presence_server.py", "oar2glb.py", "glb2tiles.py"]


def fabrique(ver):
    """Tous les fichiers de dist/ fabriqués à partir des sources, chacun avec son propre numéro de version (ver[nom]) : rend {nom: texte}."""
    sortie = {}
    py = inline_i18n_py((SRC / "gen_tpl.py").read_text(encoding="utf-8"))
    py = py.replace("__HTML_TEMPLATE__", template).replace("__DRACO_JS__", draco_js).replace("__MESHOPT_JS__", meshopt_js)
    py = py.replace("__I18N__", I18N_RT)
    py = py.replace("__VERSION__", ver["glb2html.py"]).replace("__SHELL_VERSION__", ver["index.html"]).replace("__MAP_VERSION__", ver["carte.html"])
    assert "__I18N" not in py
    sortie["glb2html.py"] = py
    # la coquille modulaire et la carte sont fabriquées par glb2html.py lui-même (build_shell, build_map_shell) : le viewer en met une copie identique dans son .zip
    gen = types.ModuleType("glb2html_build")
    exec(compile(py, "glb2html.py", "exec"), gen.__dict__)
    shell = gen.build_shell()
    sortie["index.html"] = shell   # v45 : la coquille prête (dossier lib : ./lib), identique octet pour octet à celle de glb2html.py ; à copier à la place de --update (la ligne « const LIB » est à reporter si le dossier lib est ailleurs)
    sortie["carte.html"] = gen.build_map_shell()   # v47 : la page de carte universelle (lit regions.json à côté d'elle)
    shell_modules, shell_draco = gen.shell_lib_files()
    shell_lib = {"dir": gen.LIB_REL, "modules": shell_modules, "draco": shell_draco}
    for nom, chemin in (("presence_server.py", SRC / "presence_server.py"), ("oar2glb.py", ROOT / "tools" / "oar2glb.py"), ("glb2tiles.py", ROOT / "tools" / "glb2tiles.py")):
        sortie[nom] = inline_i18n_py(chemin.read_text(encoding="utf-8")).replace("__VERSION__", ver[nom])   # glb2tiles.py : fonctions communes avec glb-stats.py, doit rester à côté
    sortie["glb-stats.py"] = inline_i18n_py((ROOT / "tools" / "glb-stats.py").read_text(encoding="utf-8"))   # fonctions communes de glb2tiles.py : doit rester à côté
    vv = ver["glb-viewer.html"]
    v = (SRC / "viewer_tpl.html").read_text(encoding="utf-8")
    v = v.replace("__CORE__", core).replace("__I18N__", I18N_RT_VIEWER).replace("__CORE_VERSION__", vv)  # core avant le reste : pas de placeholder dedans
    v = v.replace("__TEMPLATE_JSON__", jsq(template.replace("__CORE_VERSION__", vv))).replace("__PY_JSON__", jsq(py))   # glb2html.py intégré : identique à dist/glb2html.py (ses marqueurs restent)
    v = v.replace("__DRACO_JS_JSON__", jsq(draco_js)).replace("__MESHOPT_JS_JSON__", jsq(meshopt_js))
    v = v.replace("__LIBS_JSON__", json.dumps(libs)).replace("__IMPORTMAP_JSON__", json.dumps(importmap))
    v = v.replace("__SHELL_JSON__", jsq(shell)).replace("__SHELL_LIB_JSON__", json.dumps(shell_lib))
    v = v.replace("__VERSION__", vv)
    sortie["glb-viewer.html"] = v
    return sortie


def empreinte(texte):
    return hashlib.sha256(texte.encode("utf-8")).hexdigest()


neutre = fabrique({n: NEUTRE for n in FICHIERS_VERSION})
if args.empreintes:   # sert à reconstituer VERSIONS.json depuis l'historique : empreintes neutres de chaque fichier, rien n'est écrit dans dist/
    args.empreintes.write_text(json.dumps({n: empreinte(neutre[n]) for n in FICHIERS_VERSION}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    sys.exit(0)
VERSIONS_FILE = ROOT / "VERSIONS.json"
versions = json.loads(VERSIONS_FILE.read_text(encoding="utf-8")) if VERSIONS_FILE.is_file() else {}
ver, modifies = {}, []
for n in FICHIERS_VERSION:
    h, e = empreinte(neutre[n]), versions.get(n)
    if e and e.get("hash") == h:
        ver[n] = e["version"]
    else:
        ver[n] = VERSION
        versions[n] = {"version": VERSION, "hash": h}
        modifies.append(n)
sortie = fabrique(ver)
for n in ("index.html", "carte.html", "presence_server.py", "oar2glb.py", "glb2tiles.py"):   # contrôle : hors son numéro, un fichier est identique à sa fabrication neutre
    assert sortie[n].replace(ver[n], NEUTRE) == neutre[n], n
for n, t in sortie.items():
    if n in ("index.html", "carte.html"):
        (OUT / n).write_bytes(t.encode("utf-8"))
    else:
        (OUT / n).write_text(t, encoding="utf-8")
(OUT / "favicon.ico").write_bytes((SRC / "favicon.ico").read_bytes())   # icone par defaut des pages (a copier a cote de index.html ; la remplacer par la sienne change l'icone, sans refaire les pages)
py, v, shell = sortie["glb2html.py"], sortie["glb-viewer.html"], sortie["index.html"]
print(f"[OK] coquille -> {OUT / 'index.html'} ({len(shell) // 1024} Ko) ; carte -> {OUT / 'carte.html'}")
print(f"[OK] lot {VERSION} -> {OUT} (glb2html.py {len(py) // 1024} Ko, glb-viewer.html {len(v) // 1024} Ko)")
print("version de chaque fichier (ne change que si le contenu du fichier change) :")
for n in FICHIERS_VERSION:
    print(f"  {n:<22} {ver[n]}" + ("   <- modifié dans ce lot" if n in modifies else ""))
if modifies:
    if OUT.resolve() == (ROOT / "dist").resolve():
        VERSIONS_FILE.write_text(json.dumps(versions, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    else:
        print("(VERSIONS.json non modifié : sortie ailleurs que dist/)")


# marque de chaque fichier fabrique : 8 premiers caracteres de l'empreinte SHA-256 du fichier, calculee avec la marque vide (les fichiers qui
# l'affichent : presence_server.py, oar2glb.py, glb2tiles.py) ; elle ne change que si le fichier change. Verification : dans ces fichiers, remplacer la marque (entre guillemets) par """" puis calculer le SHA-256.
def marquer(dossier):
    marques = {}
    for f in sorted(dossier.iterdir()):
        if not f.is_file():
            continue
        d = f.read_bytes()
        m = hashlib.sha256(d.replace(b"__MARK__", b"")).hexdigest()[:8]
        if b"__MARK__" in d:
            f.write_bytes(d.replace(b"__MARK__", m.encode()))
        marques[f.name] = m
    return marques


print("marques (empreinte de chaque fichier fabriqué) :")
for nom_f, m in marquer(OUT).items():
    print(f"  {nom_f:<22} {m}")
