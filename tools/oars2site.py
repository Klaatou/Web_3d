#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""oars2site.py : transforme un dossier de sauvegardes de région OpenSim (.oar, .tgz) en un site web fait avec Web_3d, une région après l'autre.

Pour chaque OAR, il lance les outils existants : oar2glb.py (OAR vers GLB), glb2tiles.py (qui décide seul s'il faut des tuiles), glb2html.py avec
--shared-shell (le dossier de la région), puis, à la fin, glb2html.py --scan-sites (la carte des mondes). Il ne modifie ni les OAR ni les outils.
Une région déjà convertie (son NOM.config.json est plus récent que l'OAR) est sautée ; une région qui échoue est notée dans son journal et la suivante
continue. Journaux et fichiers de travail sont écrits hors du dossier du site. Tous les messages et l'aide : --lang fr|en|auto (python oars2site.py --help).
Mode d'emploi : docs/fr/CONVERTIR_OARS.md (anglais : docs/en/CONVERT_OARS.md).
"""
import argparse, datetime, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

# <<I18N_PY>>
def _i18n_boot():   # depuis les sources : charge src/i18n_py.py ; fabriqué par build.py (dist\\) : ce bloc est remplacé par le texte de i18n_py.py avec les langues intégrées
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

VERSION = "__VERSION__"      # remplacé par build.py (fichier VERSION) dans dist/oars2site.py
MARK = "__MARK__"      # empreinte du fichier fabriqué, inscrite par build.py ; reste telle quelle depuis tools/

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(errors="replace")
    except Exception:
        pass

ICI = Path(__file__).resolve().parent
OUTILS = ("oar2glb.py", "glb2tiles.py", "glb2html.py")
VERSION_TEX_SIZE = (1, 10, 20)      # première version de oar2glb.py qui connaît --tex-size
VERSION_TEX_QUALITY = (1, 10, 21)   # première version qui connaît --tex-quality seul


def version_tag():
    return VERSION if MARK.startswith("__") else _tr("py.common.version_mark", VERSION, MARK)


def trouver_outils(arg):
    cands = [Path(arg)] if arg else [ICI, ICI / "dist", ICI / "web_3d" / "dist", Path.cwd(), Path.cwd() / "dist"]
    for d in cands:
        if all((d / o).exists() for o in OUTILS):
            return d.resolve()
    sys.exit(_tr("py.oars2site.erreur_outils_introuvables", ", ".join(str(c) for c in cands)))


def nom_region(oar):
    """nom de fichier -> nom de région : lettres, chiffres, _ et - seulement (c'est un nom de dossier et une partie de l'adresse web)"""
    n = re.sub(r"[^A-Za-z0-9_-]+", "_", oar.name.split(".")[0]).strip("_")
    return n or "region"


def lister_oars(dossier, only):
    rx = re.compile(only, re.IGNORECASE) if only else None
    out = []
    for p in sorted(Path(dossier).iterdir()):
        if p.is_file() and p.suffix.lower() in (".oar", ".tgz") and (not rx or rx.search(p.stem)):
            out.append(p)
    return out


class Journal:
    def __init__(self, chemin):
        chemin.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(chemin, "a", encoding="utf-8", errors="replace")

    def ecrire(self, texte):
        self.f.write(texte)
        self.f.flush()

    def fermer(self):
        self.f.close()


def langue_courante():
    """code de la langue des messages (--lang) : dans dist\\ le texte de i18n_py.py est intégré à ce fichier (I18N_LANG est une de ses variables) ;
    depuis les sources, c'est celle du module chargé (_I18N)"""
    try:
        return I18N_LANG
    except NameError:
        return _I18N.I18N_LANG


def env_outils():
    """environnement des outils lancés : sans console, en UTF-8, dans la langue de ce script"""
    return dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", WEB3D_LANG=langue_courante())


def lancer(cmd, journal, timeout_min, cwd=None):
    """lance un outil : pas de saisie (entrée fermée), UTF-8, même langue ; la sortie est ajoutée au journal ; rend (code, secondes)"""
    journal.ecrire("\n$ " + " ".join('"%s"' % c if " " in c else c for c in cmd) + "\n")
    t0 = time.time()
    try:
        r = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env_outils(), cwd=cwd,
                           timeout=(timeout_min * 60 if timeout_min else None))
        journal.ecrire(r.stdout.decode("utf-8", "replace"))
        code = r.returncode
    except subprocess.TimeoutExpired as e:
        journal.ecrire((e.stdout or b"").decode("utf-8", "replace") + "\n" + _tr("py.oars2site.journal_delai", timeout_min) + "\n")
        code = 124
    return code, time.time() - t0


def convertir(oar, a, outils, site, travail, journal):
    """une région ; rend un dict pour le rapport"""
    nom = nom_region(oar)
    rep = {"oar": oar.name, "region": nom, "status": "failed", "address": "index.html?region=%s/%s" % (nom, nom), "seconds": 0, "mode": None, "message": ""}
    t0 = time.time()
    config = site / nom / (nom + ".config.json")
    if config.exists() and not a.force and config.stat().st_mtime >= oar.stat().st_mtime:
        rep.update(status="skipped", message=_tr("py.oars2site.msg_deja_fait"))
        return rep
    py = sys.executable
    tr = a.timeout_min
    glb_voisin = oar.with_suffix(".glb")
    if glb_voisin.exists() and not a.reuse_glb:
        rep["message"] = _tr("py.oars2site.msg_glb_voisin", glb_voisin.name)
        return rep
    w = travail / nom
    if w.exists():
        shutil.rmtree(w)
    w.mkdir(parents=True)
    glb = w / (nom + ".glb")
    if a.reuse_glb and glb_voisin.exists():
        shutil.copy2(glb_voisin, glb)
        journal.ecrire("\n" + _tr("py.oars2site.journal_reutilise", glb_voisin) + "\n")
    else:
        cmd = [py, str(outils / "oar2glb.py"), str(oar), "--nopause", "--pbr-size", str(a.pbr_size)]
        cmd += (["--tex-size", str(a.tex_size)] if a.tex_size else []) + (["--tex-quality", str(a.tex_quality)] if a.tex_quality is not None else []) + a.oar2glb_arg
        code, _ = lancer(cmd, journal, tr)
        if not glb_voisin.exists() or glb_voisin.stat().st_size == 0:
            rep["message"] = _tr("py.oars2site.msg_oar2glb_echec", code)
            return rep
        shutil.move(str(glb_voisin), str(glb))                      # oar2glb écrit son GLB à côté de l'OAR : on le déplace dans le dossier de travail
        if code:
            journal.ecrire("\n" + _tr("py.oars2site.journal_code_garde", code) + "\n")
    mode = "glb"
    entree = [str(glb)]
    if a.split != "never":
        cmd = [py, str(outils / "glb2tiles.py"), str(glb), "--nopause"] + (["--force"] if a.split == "always" else [])
        code, _ = lancer(cmd, journal, tr)
        tuiles = w / (nom + ".tiles.json")
        if code:
            rep["message"] = _tr("py.oars2site.msg_glb2tiles_echec", code)
            return rep
        if tuiles.exists():
            mode, entree = "tiles", ["--tiles", str(tuiles)]
    rep["mode"] = mode
    dest = site / nom
    if dest.exists():                    # un passage précédent a pu utiliser l'autre mode : jamais d'ancien GLB complet (ni d'anciennes tuiles) dans le site
        for v in (dest / (nom + ".glb"), dest / (nom + ".overview.glb"), dest / (nom + ".tiles.json")):
            if v.exists():
                v.unlink()
        shutil.rmtree(dest / (nom + ".tiles"), ignore_errors=True)
    cmd = [py, str(outils / "glb2html.py")] + entree + ["--shared-shell", str(site / "index.html"), "-o", str(site / nom / (nom + ".html"))]
    if a.vendor:
        cmd += ["--vendor", a.vendor]
    cmd += a.html_arg
    code, _ = lancer(cmd, journal, tr)
    if code or not config.exists():
        rep["message"] = _tr("py.oars2site.msg_glb2html_echec", code)
        return rep
    if a.thumbs:
        for ext in (".jpg", ".png", ".webp"):
            v = Path(a.thumbs) / (nom + ext)
            if v.exists():
                shutil.copy2(v, site / nom / (nom + ext))
                break
    rep.update(status="ok", message="")
    rep["seconds"] = round(time.time() - t0, 1)
    return rep


def version_outil(outils, nom):
    """(majeur, mineur, correctif) lu avec --version de l'outil, ou None"""
    r = subprocess.run([sys.executable, str(outils / nom), "--version"], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env_outils())
    m = re.search(rb"(\d+)\.(\d+)\.(\d+)", r.stdout)
    return tuple(int(x) for x in m.groups()) if m else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=_tr("py.oars2site.desc", version_tag()), epilog=_tr("py.oars2site.epilog"),
                                 formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False)
    i18n_add_common(ap)
    ap.add_argument("--version", action="version", version=f"oars2site {version_tag()}", help=_tr("py.common.version"))
    ap.add_argument("oars", help=_tr("py.oars2site.help.oars"))
    ap.add_argument("site", help=_tr("py.oars2site.help.site"))
    ap.add_argument("--tools", help=_tr("py.oars2site.help.tools"))
    ap.add_argument("--only", help=_tr("py.oars2site.help.only"))
    ap.add_argument("--pbr-size", type=int, default=512, metavar="N", help=_tr("py.oars2site.help.pbr_size"))
    ap.add_argument("--tex-size", type=int, default=0, metavar="N", help=_tr("py.oars2site.help.tex_size"))
    ap.add_argument("--tex-quality", type=int, default=None, metavar="Q", help=_tr("py.oars2site.help.tex_quality"))
    ap.add_argument("--split", choices=("auto", "never", "always"), default="auto", help=_tr("py.oars2site.help.split"))
    ap.add_argument("--thumbs", help=_tr("py.oars2site.help.thumbs"))
    ap.add_argument("--vendor", help=_tr("py.oars2site.help.vendor"))
    ap.add_argument("--work", help=_tr("py.oars2site.help.work"))
    ap.add_argument("--timeout-min", type=float, default=0, metavar="MIN", help=_tr("py.oars2site.help.timeout"))
    ap.add_argument("--force", action="store_true", help=_tr("py.oars2site.help.force"))
    ap.add_argument("--reuse-glb", action="store_true", help=_tr("py.oars2site.help.reuse_glb"))
    ap.add_argument("--keep-work", action="store_true", help=_tr("py.oars2site.help.keep_work"))
    ap.add_argument("--oar2glb-arg", action="append", default=[], metavar="ARG", help=_tr("py.oars2site.help.oar2glb_arg"))
    ap.add_argument("--html-arg", action="append", default=[], metavar="ARG", help=_tr("py.oars2site.help.html_arg"))
    ap.add_argument("--dry-run", action="store_true", help=_tr("py.oars2site.help.dry_run"))
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)

    outils = trouver_outils(a.tools)
    if a.tex_size or a.tex_quality is not None:
        if a.tex_size and not 16 <= a.tex_size <= 8192:
            sys.exit(_tr("py.oars2site.erreur_tex_size"))
        if a.tex_quality is not None and not 1 <= a.tex_quality <= 95:
            sys.exit(_tr("py.oars2site.erreur_tex_quality"))
        besoin = VERSION_TEX_QUALITY if a.tex_quality is not None else VERSION_TEX_SIZE
        version = version_outil(outils, "oar2glb.py")
        if version is None or version < besoin:
            sys.exit(_tr("py.oars2site.erreur_oar2glb_ancien", ".".join(str(x) for x in version) if version else _tr("py.oars2site.version_inconnue"),
                         "--tex-quality" if a.tex_quality is not None else "--tex-size", ".".join(str(x) for x in besoin)))
    oars_dir = Path(a.oars)
    if not oars_dir.is_dir():
        sys.exit(_tr("py.oars2site.erreur_pas_un_dossier", oars_dir))
    site = Path(a.site).resolve()
    travail = Path(a.work).resolve() if a.work else site.with_name(site.name + "_work")
    oars = lister_oars(oars_dir, a.only)
    if not oars:
        sys.exit(_tr("py.oars2site.erreur_aucun_oar", oars_dir))
    noms = {}
    for o in oars:
        noms.setdefault(nom_region(o), []).append(o.name)
    dup = {n: f for n, f in noms.items() if len(f) > 1}
    if dup:
        sys.exit(_tr("py.oars2site.erreur_noms_en_double", "; ".join("%s <- %s" % (n, ", ".join(f)) for n, f in dup.items())))
    print(_tr("py.oars2site.banniere", outils, site, travail, len(oars)))
    if a.dry_run:
        for o in oars:
            fait = (site / nom_region(o) / (nom_region(o) + ".config.json")).exists() and not a.force
            print(_tr("py.oars2site.dry_saute", o.name, site, nom_region(o)) if fait else _tr("py.oars2site.dry_convertir", o.name, site, nom_region(o)))
        return 0
    site.mkdir(parents=True, exist_ok=True)
    (travail / "logs").mkdir(parents=True, exist_ok=True)
    rapport = []
    for k, o in enumerate(oars, 1):
        journal = Journal(travail / "logs" / (nom_region(o) + ".log"))
        journal.ecrire("=== %s : %s ===\n" % (datetime.datetime.now().isoformat(timespec="seconds"), o))
        print(_tr("py.oars2site.progres", k, len(oars), o.name), flush=True)
        try:
            r = convertir(o, a, outils, site, travail, journal)
        except Exception as e:                       # une région ne doit jamais arrêter les autres
            r = {"oar": o.name, "region": nom_region(o), "status": "failed", "message": _tr("py.oars2site.msg_inattendue", e), "seconds": 0, "mode": None, "address": ""}
        journal.fermer()
        if not a.keep_work:
            shutil.rmtree(travail / nom_region(o), ignore_errors=True)      # aussi après un échec (le journal suffit à comprendre, un GLB peut être énorme)
        rapport.append(r)
        mot = {"ok": _tr("py.oars2site.statut_ok"), "skipped": _tr("py.oars2site.statut_saute"), "failed": _tr("py.oars2site.statut_echec")}[r["status"]]
        detail = " (%s, %.0f s)" % (r["mode"], r["seconds"]) if r["status"] == "ok" else ""
        print("        " + mot + detail + (" : " + r["message"] if r["message"] else ""), flush=True)
    if any(r["status"] == "ok" for r in rapport):
        journal = Journal(travail / "logs" / "_scan-sites.log")
        code, _ = lancer([sys.executable, str(outils / "glb2html.py"), "--scan-sites", str(site)], journal, a.timeout_min)
        journal.fermer()
        print(_tr("py.oars2site.scan_ok") if code == 0 else _tr("py.oars2site.scan_echec", code, travail / "logs" / "_scan-sites.log"))
    (travail / "conversion_report.json").write_text(json.dumps(
        {"date": datetime.datetime.now().isoformat(timespec="seconds"), "site": str(site), "regions": rapport}, indent=2, ensure_ascii=False), encoding="utf-8")
    ok = sum(r["status"] == "ok" for r in rapport)
    sk = sum(r["status"] == "skipped" for r in rapport)
    ko = sum(r["status"] == "failed" for r in rapport)
    print(_tr("py.oars2site.bilan", ok, sk, ko, travail))
    return 1 if ko else 0


if __name__ == "__main__":
    sys.exit(main())
