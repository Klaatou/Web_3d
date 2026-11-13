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

# ---- langue des messages (v36) : textes intégrés par build.py (src/i18n/*.json, clés py.*) ; --lang fr|en|auto ou WEB3D_LANG ----
import json as _json, locale as _locale, os as _os, pathlib as _pl, sys as _sys

# fabrication (build.py) : la ligne suivante devient I18N_DATA = { "fr": {...}, "en": {...} }
I18N_DATA = _json.loads(r'''{"en":{"_name":"English","py.common.help":"show this help message and exit","py.common.lang_help":"language of the messages and of this help: fr, en or auto (default: the system's language; environment variable WEB3D_LANG is equivalent). Available: {0}","py.common.optionals":"options","py.common.positionals":"arguments","py.common.version_mark":"{0}, fingerprint {1}","py.common.version":"show the version and exit","py.oars2site.banniere":"tools: {0} | site: {1} | work and logs: {2} | {3} OAR(s)","py.oars2site.bilan":"done: {0} converted, {1} skipped, {2} failed. Report and logs: {3}","py.oars2site.desc":"oars2site.py {0}: turns a folder of OpenSim region backups (.oar, .tgz) into a Web_3d web site, one region after the other (oar2glb.py, glb2tiles.py, glb2html.py, then the world map).","py.oars2site.dry_convertir":"  to convert: {0} -> {1}/{2}/","py.oars2site.dry_saute":"  skipped (already converted): {0} -> {1}/{2}/","py.oars2site.epilog":"Examples:\n  python oars2site.py \"P:\\path\\OARS\" \"P:\\path\\site\"\n  python oars2site.py \"P:\\path\\OARS\" \"P:\\path\\site\" --dry-run        (lists what would be done, writes nothing)\n  python oars2site.py \"P:\\path\\OARS\" \"P:\\path\\site\" --only \"Beach|Castle\" --tex-size 1024\n\nEach region is then at  site/index.html?region=NAME/NAME  (any static web server). The published GLB can be downloaded by any visitor: see docs/en/CONVERT_OARS.md.","py.oars2site.erreur_aucun_oar":"[ERROR] no .oar or .tgz file to convert in {0}.","py.oars2site.erreur_noms_en_double":"[ERROR] several OARs give the same region name: {0}","py.oars2site.erreur_oar2glb_ancien":"[ERROR] this oar2glb.py ({0}) is too old for {1}: update Web_3d ({2} or later).","py.oars2site.erreur_outils_introuvables":"[ERROR] oar2glb.py, glb2tiles.py and glb2html.py not found (looked in: {0}). Use --tools FOLDER.","py.oars2site.erreur_pas_un_dossier":"[ERROR] not a folder: {0}","py.oars2site.erreur_tex_quality":"[ERROR] --tex-quality must be between 1 and 95","py.oars2site.erreur_tex_size":"[ERROR] --tex-size must be 0 (no reduction) or between 16 and 8192","py.oars2site.help.dry_run":"only lists what would be done, writes nothing","py.oars2site.help.force":"redoes the regions already converted (overwrites that region's config and zones)","py.oars2site.help.html_arg":"extra argument for glb2html.py (repeatable), for example --html-arg=--no-credit","py.oars2site.help.keep_work":"keeps the work files of each region (GLB, tiles)","py.oars2site.help.oar2glb_arg":"extra argument for oar2glb.py (repeatable), for example --oar2glb-arg=--no-pbr","py.oars2site.help.oars":"folder holding the .oar or .tgz files to convert","py.oars2site.help.only":"regular expression: only the OARs whose name matches (case ignored)","py.oars2site.help.pbr_size":"maximum side, in pixels, of the PBR textures (default 512, as in oar2glb.py; 0 = original size)","py.oars2site.help.reuse_glb":"if NAME.glb already sits beside NAME.oar, uses it instead of running oar2glb.py","py.oars2site.help.site":"site folder (created if needed); the shell index.html, lib/, default.json and regions.json are at its root","py.oars2site.help.split":"auto: glb2tiles.py decides by itself whether tiles are needed (default); never: a single GLB; always: tiles in every case","py.oars2site.help.tex_quality":"compresses the ordinary textures as JPEG of quality Q, from 1 (heavily degraded, very light) to 95 (close to the original), without changing their pixels; alone, recompresses every opaque texture; with --tex-size, also sets the quality of the reduced textures (85 if absent); needs oar2glb.py 1.10.21 or later","py.oars2site.help.tex_size":"reduces the ordinary textures to N pixels on a side at most (0 = no reduction, otherwise 16 to 8192, for example 1024, 512, 256); needs oar2glb.py 1.10.20 or later","py.oars2site.help.thumbs":"folder of thumbnails NAME.jpg, NAME.png or NAME.webp (140 KB at most each), copied beside the region for the world map","py.oars2site.help.timeout":"stops one step after this many minutes (default 0: no limit)","py.oars2site.help.tools":"folder of oar2glb.py, glb2tiles.py and glb2html.py (default: beside this script, then dist, web_3d/dist, the current folder)","py.oars2site.help.vendor":"local three.js folder passed to glb2html.py (offline work); default: glb2html.py's own behaviour","py.oars2site.help.work":"folder for work files and logs (default: SITE_FOLDER_work, beside the site folder, so it is never served by the web server)","py.oars2site.journal_code_garde":"[note] oar2glb returned code {0} but wrote a GLB: kept","py.oars2site.journal_delai":"[TIMEOUT after {0} min]","py.oars2site.journal_reutilise":"[reuse] {0} used as is (oar2glb not run)","py.oars2site.msg_deja_fait":"already converted (--force to redo)","py.oars2site.msg_glb2html_echec":"glb2html failed (code {0}): see the log","py.oars2site.msg_glb2tiles_echec":"glb2tiles failed (code {0}): see the log","py.oars2site.msg_glb_voisin":"{0} already exists beside the OAR: oar2glb would overwrite it (move it, or use --reuse-glb to use it as is)","py.oars2site.msg_inattendue":"unexpected error: {0}","py.oars2site.msg_oar2glb_echec":"oar2glb failed (code {0}), no GLB written: see the log","py.oars2site.progres":"[{0}/{1}] {2} ...","py.oars2site.scan_echec":"WARNING: --scan-sites failed (code {0}): see {1}","py.oars2site.scan_ok":"regions.json updated","py.oars2site.statut_echec":"FAILED","py.oars2site.statut_ok":"OK","py.oars2site.statut_saute":"SKIPPED","py.oars2site.version_inconnue":"unknown version"},"fr":{"_name":"Français","py.common.help":"afficher ce message d'aide et quitter","py.common.lang_help":"langue des messages et de l'aide : fr, en ou auto (défaut : langue du système ; variable d'environnement WEB3D_LANG équivalente). Disponibles : {0}","py.common.optionals":"options","py.common.positionals":"arguments","py.common.version_mark":"{0}, empreinte {1}","py.common.version":"afficher la version et quitter","py.oars2site.banniere":"outils : {0} | site : {1} | travail et journaux : {2} | {3} OAR","py.oars2site.bilan":"terminé : {0} convertie(s), {1} sautée(s), {2} en échec. Rapport et journaux : {3}","py.oars2site.desc":"oars2site.py {0} : transforme un dossier de sauvegardes de région OpenSim (.oar, .tgz) en un site web Web_3d, une région après l'autre (oar2glb.py, glb2tiles.py, glb2html.py, puis la carte des mondes).","py.oars2site.dry_convertir":"  à convertir : {0} -> {1}/{2}/","py.oars2site.dry_saute":"  sauté (déjà converti) : {0} -> {1}/{2}/","py.oars2site.epilog":"Exemples :\n  python oars2site.py \"P:\\chemin\\OAR\" \"P:\\chemin\\site\"\n  python oars2site.py \"P:\\chemin\\OAR\" \"P:\\chemin\\site\" --dry-run        (liste ce qui serait fait, sans rien écrire)\n  python oars2site.py \"P:\\chemin\\OAR\" \"P:\\chemin\\site\" --only \"Plage|Chateau\" --tex-size 1024\n\nChaque région est ensuite à l'adresse  site/index.html?region=NOM/NOM  (n'importe quel serveur web statique). Le GLB publié peut être téléchargé par tout visiteur : voir docs/fr/CONVERTIR_OARS.md.","py.oars2site.erreur_aucun_oar":"[ERREUR] aucun fichier .oar ou .tgz à convertir dans {0}.","py.oars2site.erreur_noms_en_double":"[ERREUR] plusieurs OAR donnent le même nom de région : {0}","py.oars2site.erreur_oar2glb_ancien":"[ERREUR] cet oar2glb.py ({0}) est trop ancien pour {1} : mets Web_3d à jour ({2} ou plus récent).","py.oars2site.erreur_outils_introuvables":"[ERREUR] oar2glb.py, glb2tiles.py et glb2html.py introuvables (cherchés dans : {0}). Utilise --tools DOSSIER.","py.oars2site.erreur_pas_un_dossier":"[ERREUR] ce n'est pas un dossier : {0}","py.oars2site.erreur_tex_quality":"[ERREUR] --tex-quality doit être compris entre 1 et 95","py.oars2site.erreur_tex_size":"[ERREUR] --tex-size doit valoir 0 (pas de réduction) ou être compris entre 16 et 8192","py.oars2site.help.dry_run":"liste seulement ce qui serait fait, sans rien écrire","py.oars2site.help.force":"refait les régions déjà converties (écrase la config et les zones de cette région)","py.oars2site.help.html_arg":"argument supplémentaire pour glb2html.py (répétable), par exemple --html-arg=--no-credit","py.oars2site.help.keep_work":"garde les fichiers de travail de chaque région (GLB, tuiles)","py.oars2site.help.oar2glb_arg":"argument supplémentaire pour oar2glb.py (répétable), par exemple --oar2glb-arg=--no-pbr","py.oars2site.help.oars":"dossier qui contient les fichiers .oar ou .tgz à convertir","py.oars2site.help.only":"expression régulière : seulement les OAR dont le nom correspond (casse ignorée)","py.oars2site.help.pbr_size":"côté maximal, en pixels, des textures PBR (défaut 512, comme oar2glb.py ; 0 = taille d'origine)","py.oars2site.help.reuse_glb":"si NOM.glb existe déjà à côté de NOM.oar, l'utilise au lieu de lancer oar2glb.py","py.oars2site.help.site":"dossier du site (créé si besoin) ; la coquille index.html, lib/, default.json et regions.json sont à sa racine","py.oars2site.help.split":"auto : glb2tiles.py décide seul s'il faut des tuiles (défaut) ; never : un seul GLB ; always : des tuiles dans tous les cas","py.oars2site.help.tex_quality":"compresse les textures ordinaires en JPEG de qualité Q, de 1 (très dégradé, très léger) à 95 (proche de l'original), sans changer leurs pixels ; seul, recompresse toutes les textures opaques ; avec --tex-size, règle aussi la qualité des textures réduites (85 si absent) ; demande oar2glb.py 1.10.21 ou plus récent","py.oars2site.help.tex_size":"réduit les textures ordinaires à N pixels de côté au plus (0 = pas de réduction, sinon de 16 à 8192, par exemple 1024, 512, 256) ; demande oar2glb.py 1.10.20 ou plus récent","py.oars2site.help.thumbs":"dossier de vignettes NOM.jpg, NOM.png ou NOM.webp (140 Ko au plus chacune), copiées à côté de la région pour la carte des mondes","py.oars2site.help.timeout":"arrête une étape après ce nombre de minutes (défaut 0 : pas de limite)","py.oars2site.help.tools":"dossier de oar2glb.py, glb2tiles.py et glb2html.py (défaut : à côté de ce script, puis dist, web_3d/dist, le dossier courant)","py.oars2site.help.vendor":"dossier local de three.js transmis à glb2html.py (travail hors ligne) ; défaut : le comportement de glb2html.py","py.oars2site.help.work":"dossier des fichiers de travail et des journaux (défaut : DOSSIER_SITE_work, à côté du dossier du site, donc jamais servi par le serveur web)","py.oars2site.journal_code_garde":"[note] oar2glb a rendu le code {0} mais a écrit un GLB : gardé","py.oars2site.journal_delai":"[DÉLAI dépassé : {0} min]","py.oars2site.journal_reutilise":"[réutilisation] {0} utilisé tel quel (oar2glb non lancé)","py.oars2site.msg_deja_fait":"déjà converti (--force pour refaire)","py.oars2site.msg_glb2html_echec":"glb2html a échoué (code {0}) : voir le journal","py.oars2site.msg_glb2tiles_echec":"glb2tiles a échoué (code {0}) : voir le journal","py.oars2site.msg_glb_voisin":"{0} existe déjà à côté de l'OAR : oar2glb l'écraserait (déplace-le, ou utilise --reuse-glb pour l'utiliser tel quel)","py.oars2site.msg_inattendue":"erreur inattendue : {0}","py.oars2site.msg_oar2glb_echec":"oar2glb a échoué (code {0}), aucun GLB écrit : voir le journal","py.oars2site.progres":"[{0}/{1}] {2} ...","py.oars2site.scan_echec":"ATTENTION : --scan-sites a échoué (code {0}) : voir {1}","py.oars2site.scan_ok":"regions.json mis à jour","py.oars2site.statut_echec":"ÉCHEC","py.oars2site.statut_ok":"OK","py.oars2site.statut_saute":"SAUTÉ","py.oars2site.version_inconnue":"version inconnue"}}''')


def _load():
    if I18N_DATA is not None:
        return I18N_DATA
    here = _pl.Path(__file__).resolve().parent
    for d in (here / "i18n", here.parent / "src" / "i18n"):
        if d.is_dir():
            return {p.stem: _json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json"))}
    return {}


_DATA = _load()
I18N_CODES = sorted(_DATA)


def _match(tag):
    c = str(tag or "").lower().replace("-", "_").split("_")[0]
    return c if c in _DATA else None


def i18n_system_lang():
    """langue du système (variables d'environnement, locale Python, langue d'interface de Windows) ; None si inconnue"""
    for v in ("LC_ALL", "LC_MESSAGES", "LANGUAGE", "LANG"):
        c = _match(_os.environ.get(v, "").split(":")[0])
        if c:
            return c
    try:
        c = _match((_locale.getlocale()[0] or ""))
        if c:
            return c
    except Exception:
        pass
    try:
        import ctypes
        lid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        c = _match(_locale.windows_locale.get(lid, ""))
        if c:
            return c
    except Exception:
        pass
    return None


def i18n_detect_lang(argv=None):
    """--lang CODE ou --lang=CODE dans argv, sinon WEB3D_LANG, sinon la langue du système, sinon l'anglais ('auto' = laisser le système décider)"""
    argv = list(_sys.argv[1:] if argv is None else argv)
    want = None
    for i, a in enumerate(argv):
        if a == "--lang" and i + 1 < len(argv):
            want = argv[i + 1]
        elif a.startswith("--lang="):
            want = a.split("=", 1)[1]
    for cand in (want, _os.environ.get("WEB3D_LANG")):
        if cand and cand.lower() != "auto" and _match(cand):
            return _match(cand)
    return i18n_system_lang() or ("en" if "en" in _DATA else (I18N_CODES[0] if I18N_CODES else "en"))


I18N_LANG = i18n_detect_lang()


def i18n_set_lang(code):
    global I18N_LANG
    I18N_LANG = _match(code) or I18N_LANG


def _tr(key, *a):
    """texte de la clé dans la langue courante (anglais, français, clé en repli) ; avec des arguments : str.format"""
    s = None
    for lg in (I18N_LANG, "en", "fr"):
        v = _DATA.get(lg, {}).get(key)
        if isinstance(v, str):
            s = v
            break
    if s is None:
        s = key
    return s.format(*a) if a else s


def i18n_lang_help():
    """texte d'aide de l'option --lang (codes disponibles)"""
    return _tr("py.common.lang_help", ", ".join(I18N_CODES))


def i18n_add_common(ap):
    """ajoute -h/--help traduit et --lang à un parseur créé avec add_help=False ; titres des groupes traduits"""
    ap.add_argument("-h", "--help", action="help", help=_tr("py.common.help"))
    ap.add_argument("--lang", default="auto", metavar="CODE", help=i18n_lang_help())
    try:
        ap._positionals.title = _tr("py.common.positionals")
        ap._optionals.title = _tr("py.common.optionals")
    except Exception:
        pass


VERSION = "1.10.24 (13/11/2026)"      # remplacé par build.py (fichier VERSION) dans dist/oars2site.py
MARK = "f2dbb58f"      # empreinte du fichier fabriqué, inscrite par build.py ; reste telle quelle depuis tools/

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
