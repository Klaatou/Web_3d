#!/usr/bin/env python3
"""Test 1.8.11 : convoar est fourni dans dist/convoar/ (hors navigateur, hors Windows : convoar n'est pas lance).

Verifie : le manifeste SHA256SUMS.txt (chaque fichier present, empreinte identique ; seuls convoar_inv.* peuvent s'y ajouter : fabriques par
oar2glb.py a la premiere conversion) ; ni *.pdb ni NLog.xml ; convoar.exe, sa config, LICENSE, ORIGINE.txt et les licences tierces presents ;
oar2glb.py choisit convoar : la variable CONVOAR d'abord, puis convoar du PATH, puis convoar/convoar.exe a cote de lui, puis convoar.exe a cote de lui,
sinon il cite convoar/convoar.exe dans son message ; git : fins de ligne intactes (-text), convoar_inv.* ignores, le reste suivi.

Lancer : python tests/convoar_dist.py
"""
import hashlib, importlib.util, os, pathlib, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CV = ROOT / "dist" / "convoar"
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)), flush=True)


rapport(CV.is_dir(), "dist/convoar existe", "decompresser convoar-dist.zip dans dist/")
if not CV.is_dir():
    sys.exit(1)
# 1. manifeste
man = {}
for ligne in (CV / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines():
    h, _, nom = ligne.partition("  ")
    man[nom] = h
rapport(len(man) > 100 and "convoar.exe" in man, f"manifeste lu : {len(man)} fichiers", len(man))
manque = [n for n in man if not (CV / n).is_file()]
rapport(not manque, "chaque fichier du manifeste est present", manque[:5])
autres = [h for n, h in man.items() if (CV / n).is_file() and hashlib.sha256((CV / n).read_bytes()).hexdigest() != h]
rapport(not autres, "chaque fichier a l'empreinte SHA-256 du manifeste (fins de ligne, copie, git)", [n for n, h in man.items() if (CV / n).is_file() and hashlib.sha256((CV / n).read_bytes()).hexdigest() != h][:5])
presents = {p.relative_to(CV).as_posix() for p in CV.rglob("*") if p.is_file()}
en_plus = sorted(presents - set(man) - {"SHA256SUMS.txt"})
rapport(all(n.startswith("convoar_inv.") for n in en_plus), "aucun fichier hors manifeste (sauf convoar_inv.*, fabriques par oar2glb.py)", en_plus[:5])
# 2. contenu
rapport(not [n for n in presents if n.endswith(".pdb") or n == "NLog.xml"], "ni fichiers de debogage (*.pdb) ni NLog.xml")
for n in ("convoar.exe", "convoar.exe.config", "LICENSE", "ORIGINE.txt", "SHA256SUMS.txt"):
    rapport(n in presents, f"{n} present")
tiers = sorted(n for n in presents if n.startswith("THIRDPARTYLICENSES/"))
rapport(len(tiers) == 6, "les six licences tierces de convoar sont presentes (THIRDPARTYLICENSES/)", tiers)
rapport("Apache License" in (CV / "LICENSE").read_text(encoding="utf-8", errors="replace")[:400], "LICENSE : Apache License")
rapport("be7abbedc0d7d295a76800b2fe2e1fc9a58a7934" in (CV / "ORIGINE.txt").read_text(encoding="utf-8"), "ORIGINE.txt : commit indique")

# 3. choix de convoar par oar2glb.py (copie isolee : le dossier convoar du depot ne compte pas)
tmp = pathlib.Path(tempfile.mkdtemp(prefix="web3d_convoar_")).resolve()
isole = tmp / "outil"
isole.mkdir()
shutil.copy(ROOT / "dist" / "oar2glb.py", isole / "oar2glb.py")
vide = tmp / "vide"
vide.mkdir()
avant = {k: os.environ.get(k) for k in ("CONVOAR", "PATH")}
os.environ.pop("CONVOAR", None)
os.environ["PATH"] = str(vide)
try:
    spec = importlib.util.spec_from_file_location("oar2glb_isole", isole / "oar2glb.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    choix = lambda: pathlib.Path(mod.default_convoar())
    rapport(choix() == isole / "convoar" / "convoar.exe", "rien de fourni : le message cite convoar/convoar.exe a cote de oar2glb.py", choix())
    (isole / "convoar.exe").write_bytes(b"x")
    rapport(choix() == isole / "convoar.exe", "convoar.exe a cote de oar2glb.py (ancien emplacement) est utilise", choix())
    (isole / "convoar").mkdir()
    (isole / "convoar" / "convoar.exe").write_bytes(b"x")
    rapport(choix() == isole / "convoar" / "convoar.exe", "convoar/convoar.exe passe avant convoar.exe a cote", choix())
    (vide / "convoar.exe").write_bytes(b"x")
    (vide / "convoar").write_bytes(b"x")
    os.chmod(vide / "convoar", 0o755)
    rapport(pathlib.Path(choix()).parent == vide, "convoar du PATH passe avant les deux", choix())
    os.environ["CONVOAR"] = str(tmp / "ailleurs" / "convoar.exe")
    rapport(choix() == tmp / "ailleurs" / "convoar.exe", "la variable CONVOAR passe avant tout", choix())
finally:
    for k, v in avant.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(tmp, ignore_errors=True)
rapport("tree/master/dist" in mod.CONVOAR_URL and "master/bin" not in mod.CONVOAR_URL, "adresse de source : dossier dist (pas bin)", mod.CONVOAR_URL)

# 4. git
if shutil.which("git") and (ROOT / ".git").exists():
    def git(*a):
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    attr = git("check-attr", "text", "--", "dist/convoar/convoar.exe.config", "dist/convoar/LICENSE").stdout
    rapport(attr.count("text: unset") == 2, "git : fins de ligne intactes dans dist/convoar (text: unset)", attr)
    rapport(git("check-ignore", "-q", "dist/convoar/convoar_inv.exe").returncode == 0 and git("check-ignore", "-q", "dist/convoar/convoar_inv.cs").returncode == 0, "git : convoar_inv.* ignores")
    rapport(all(git("check-ignore", "-q", "dist/convoar/" + n).returncode == 1 for n in ("convoar.exe", "convoar.exe.config", "OpenMetaverse.dll", "LICENSE", "SHA256SUMS.txt", "libopenjpeg-dotnet-2-1.5.0-dotnet-1-x86_64.so")), "git : le reste de dist/convoar n'est pas ignore")
else:
    print("(pas de depot git ici : controles git non faits)")
print("\nR\u00c9SULTAT : " + ("tout est pass\u00e9" if not bad else f"\u00c9CHEC ({bad})"))
sys.exit(1 if bad else 0)
