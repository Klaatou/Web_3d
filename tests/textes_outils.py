#!/usr/bin/env python3
"""Test 1.4.10 : chaque outil Python de dist/ n'embarque que ses propres textes (py.<outil>.*), les textes communs (py.common.*) et _name.

Verifie, pour glb2html.py, glb2tiles.py, oar2glb.py, presence_server.py et glb-stats.py : aucun texte d'un autre outil ; chaque texte que la source de
l'outil cite existe en francais et en anglais ; --help marche en francais et en anglais sans afficher de cle brute (« py. ») ; glb2tiles.py --analyse
(qui charge glb-stats.py a cote de lui) marche sans cle brute.

Prerequis : python build.py avant. Lancer : python tests/textes_outils.py
"""
import json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
sys.path.insert(0, str(ROOT / "tests"))
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)[:400]))


OUTILS = {"glb2html.py": ("glb2html", ROOT / "src" / "gen_tpl.py"), "glb2tiles.py": ("glb2tiles", ROOT / "tools" / "glb2tiles.py"),
          "oar2glb.py": ("oar2glb", ROOT / "tools" / "oar2glb.py"), "presence_server.py": ("presence", ROOT / "src" / "presence_server.py"),
          "glb-stats.py": ("stats", ROOT / "tools" / "glb-stats.py"), "extraire_batiments.py": ("extraire", ROOT / "tools" / "extraire_batiments.py"), "iar2oar.py": ("iar2oar", ROOT / "tools" / "iar2oar.py"), "diag_carte.py": ("diag", ROOT / "tools" / "diag_carte.py"), "web3d_gui.py": ("gui", ROOT / "tools" / "web3d_gui.py")}
RX_DATA = re.compile(r"I18N_DATA = _json\.loads\(r'''(.*?)'''\)", re.S)
RX_CLE = re.compile(r"""["'](py\.[A-Za-z0-9_]+\.[A-Za-z0-9_.]*)""")

for nom, (outil, source) in OUTILS.items():
    texte = (DIST / nom).read_text(encoding="utf-8")
    m = RX_DATA.search(texte)
    if not m:
        rapport(False, f"{nom} : table des textes introuvable")
        continue
    data = json.loads(m.group(1))
    autorise = ("py." + outil + ".", "py.common.")
    for lang in ("fr", "en"):
        etrangers = sorted(k for k in data.get(lang, {}) if k != "_name" and not k.startswith(autorise))
        rapport(not etrangers, f"{nom} ({lang}) : aucun texte d'un autre outil", etrangers[:5])
    cites = set(RX_CLE.findall(source.read_text(encoding="utf-8"))) | set(RX_CLE.findall((ROOT / "src" / "i18n_py.py").read_text(encoding="utf-8")))
    manque = []
    for k in sorted(cites):
        for lang in ("fr", "en"):
            d = data.get(lang, {})
            ok = (any(x.startswith(k) for x in d) if k.endswith(".") else k in d)   # « py.presence.rawkind. » : prefixe complete a l'execution
            if not ok:
                manque.append(f"{lang}:{k}")
    rapport(not manque, f"{nom} : les {len(cites)} textes cites par la source sont presents en francais et en anglais", manque[:5])
    for lang in ("fr", "en"):
        r = subprocess.run([sys.executable, str(DIST / nom), "--help"], capture_output=True, text=True, env=dict(os.environ, WEB3D_LANG=lang), timeout=60)
        sortie = r.stdout + r.stderr
        rapport(r.returncode == 0 and "py." not in sortie and len(sortie) > 50, f"{nom} --help ({lang}) : marche, aucune cle brute", (r.returncode, sortie[-300:]))

import glbfab   # GLB d'essai
import tempfile
tmp = Path(tempfile.mkdtemp(prefix="textes_outils_"))
glbfab.region(tmp / "Essai.glb")
for lang in ("fr", "en"):
    r = subprocess.run([sys.executable, str(DIST / "glb2tiles.py"), str(tmp / "Essai.glb"), "--analyse", "--nopause"], capture_output=True, text=True,
                       env=dict(os.environ, WEB3D_LANG=lang), timeout=120)
    sortie = r.stdout + r.stderr
    rapport(r.returncode == 0 and "py." not in sortie, f"glb2tiles.py --analyse ({lang}, avec glb-stats.py) : marche, aucune cle brute", (r.returncode, sortie[-300:]))

print()
print("RESULTAT : " + ("tout est passe" if not bad else f"ECHEC ({bad})"))
sys.exit(1 if bad else 0)
