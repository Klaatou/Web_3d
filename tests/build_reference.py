#!/usr/bin/env python3
"""Test 1.8.9 : python build.py refait docs/REFERENCE_OPTIONS.md (hors navigateur).

Le depot est copie dans un dossier temporaire (build.py travaille a cote de lui). Verifie : fichier absent -> recree, avec les outils ; relance
sans changement -> fichier laisse tel quel (octets identiques, date comprise) ; date seule differente -> pas reecrit ; contenu different -> reecrit ;
fins de ligne LF ; aucun journal (*.log) laisse dans dist/ ; --out ailleurs que dist/ -> rien n'est ecrit dans docs/ ; sans gen_reference.py -> avertissement,
build reussi.

Prerequis : pip install websockets (lecture de presence_server.py). Variable facultative : THREE_DIR (paquet npm three, hors ligne). Lancer : python tests/build_reference.py
"""
import os, pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
tmp = pathlib.Path(tempfile.mkdtemp(prefix="web3d_buildref_"))
rep = tmp / "repo"
rep.mkdir()
for f in ("build.py", "gen_reference.py", "VERSION", "VERSIONS.json"):
    shutil.copy(ROOT / f, rep / f)
for d in ("src", "tools"):
    shutil.copytree(ROOT / d, rep / d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
(rep / "docs").mkdir()
REF = rep / "docs" / "REFERENCE_OPTIONS.md"
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)), flush=True)


def build(*extra):
    cmd = [sys.executable, str(rep / "build.py")] + (["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []) + list(extra)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(rep),
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))   # Windows : sortie d'un tube en cp1252 sans cela
    return r, r.stdout + r.stderr


r, out = build()
rapport(r.returncode == 0 and "REFERENCE_OPTIONS.md : refait" in out, "dist/ fabrique, fichier absent : docs/REFERENCE_OPTIONS.md est recree", out[-300:])
texte = REF.read_bytes() if REF.is_file() else b""
rapport(b"\r" not in texte, "fins de ligne LF")
noms = re.findall(rb"^## (\S+)$", texte, flags=re.M)
rapport({b"glb2html.py", b"glb2tiles.py", b"oar2glb.py", b"presence_server.py"} <= set(noms), "les outils principaux sont dans le fichier (glb2html, glb2tiles, oar2glb, presence_server)", noms)
rapport(not [p.name for p in (rep / "dist").iterdir() if p.suffix == ".log"], "aucun journal laisse dans dist/", [p.name for p in (rep / "dist").iterdir() if p.suffix == ".log"])

r, out = build()
rapport(r.returncode == 0 and "REFERENCE_OPTIONS.md : \u00e0 jour (inchang\u00e9)" in out and REF.read_bytes() == texte, "relance sans changement : fichier laisse tel quel")

vieux = re.sub(rb"G\xc3\xa9n\xc3\xa9r\xc3\xa9e le \d\d/\d\d/\d{4}", "G\u00e9n\u00e9r\u00e9e le 01/01/2020".encode("utf-8"), texte)
rapport(vieux != texte, "(controle : la date a bien ete changee dans la copie d'essai)")
REF.write_bytes(vieux)
r, out = build()
rapport(r.returncode == 0 and REF.read_bytes() == vieux and "inchang\u00e9" in out, "date seule differente : pas reecrit", out[-200:])

REF.write_bytes(texte.replace(b"`--walk`", b"`--marche`", 1))
r, out = build()
rapport(r.returncode == 0 and "refait" in out and re.sub(rb"G\xc3\xa9n\xc3\xa9r\xc3\xa9e le \d\d/\d\d/\d{4}", b"", REF.read_bytes()) == re.sub(rb"G\xc3\xa9n\xc3\xa9r\xc3\xa9e le \d\d/\d\d/\d{4}", b"", texte), "contenu different : reecrit", out[-200:])

REF.unlink()
r, out = build("--out", str(tmp / "ailleurs"))
rapport(r.returncode == 0 and not REF.exists() and "non refait : sortie ailleurs" in out, "--out ailleurs que dist/ : rien n'est ecrit dans docs/", out[-200:])

(rep / "gen_reference.py").unlink()
r, out = build()
rapport(r.returncode == 0 and "[AVERTISSEMENT] docs/REFERENCE_OPTIONS.md non refait" in out and not REF.exists(), "sans gen_reference.py : avertissement, le build reussit", out[-300:])

shutil.rmtree(tmp, ignore_errors=True)
print("\nR\u00c9SULTAT : " + ("tout est pass\u00e9" if not bad else f"\u00c9CHEC ({bad})"))
sys.exit(1 if bad else 0)
