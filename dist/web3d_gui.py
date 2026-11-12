#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""web3d_gui.py : lanceur graphique des outils Web_3d (glb2html, glb2tiles, oar2glb, extraire_batiments, iar2oar, diag_carte).

Une liste pour choisir l'outil, une liste d'exemples d'usages de base (elle remplit les champs), puis une ligne par option, l'aide de l'option sous le curseur, la ligne de commande qui en résulte, un bouton pour lancer l'outil et sa sortie.
Les options sont lues dans l'outil lui-même (rien ne peut manquer, l'outil n'est pas modifié). Nécessite tkinter (livré avec Python sous Windows).
Tous les messages et l'aide : --lang fr|en|auto (python web3d_gui.py --help).
"""
import argparse, contextlib, io, os, queue, re, runpy, subprocess, sys, tempfile, threading
from pathlib import Path

# ---- langue des messages (v36) : textes intégrés par build.py (src/i18n/*.json, clés py.*) ; --lang fr|en|auto ou WEB3D_LANG ----
import json as _json, locale as _locale, os as _os, pathlib as _pl, sys as _sys

# fabrication (build.py) : la ligne suivante devient I18N_DATA = { "fr": {...}, "en": {...} }
I18N_DATA = _json.loads(r'''{"en":{"_name":"English","py.common.help":"show this help message and exit","py.common.lang_help":"language of the messages and of this help: fr, en or auto (default: the system's language; environment variable WEB3D_LANG is equivalent). Available: {0}","py.common.optionals":"options","py.common.positionals":"arguments","py.common.version_mark":"{0}, fingerprint {1}","py.common.version":"show the version and exit","py.gui.desc":"web3d_gui.py {0}: graphical launcher for the Web_3d tools (glb2html, glb2tiles, oar2glb, extraire_batiments, iar2oar, diag_carte). A list to choose the tool, a list of basic-use examples that fills the fields, one line per option, the help of each option, the resulting command, a button to run the tool and its output. The options are read from the tool itself: it is not modified.","py.gui.epilog":"Examples:\n  python web3d_gui.py\n  python web3d_gui.py --tool oar2glb\n  python web3d_gui.py --shortcuts --dry-run\n  python web3d_gui.py --shortcuts\n  python web3d_gui.py --lang fr\nNeeds tkinter. Paths are chosen with the File... and Folder... buttons; the help of the option under the pointer shows at the bottom. The Examples list fills the fields with a basic use of the tool: replace the example names with your own.","py.gui.no_tk":"ERROR: tkinter not found. On Windows it is installed with Python (reinstall Python if needed); on Linux, install the python3-tk package.","py.gui.no_tool":"ERROR: {0} not found (looked next to this script, then in the dist folder). Run 'python build.py' or copy web3d_gui.py next to {0}.","py.gui.read_error":"ERROR: cannot read the options of {0}.","py.gui.title":"Web_3d: launcher ({0})","py.gui.tool":"Tool:","py.gui.search":"Search an option:","py.gui.count":"{0} option(s) shown out of {1}","py.gui.help_title":"Help for the option:","py.gui.help_none":"Move the pointer over an option, or click in its field: its help shows here.","py.gui.examples":"Examples:","py.gui.examples_pick":"(pick a basic use: it fills the fields below)","py.gui.example_loaded":"Example loaded.","py.gui.example_hint":"Replace the example names (files, address, key) with your own, then click Run. You can edit the fields first.","py.gui.example_invalid":"This example does not match the installed tool (unknown option: {0}): use up-to-date versions of the tool and of the launcher.","py.gui.ex.glb2html.1":"Simple web page from a GLB","py.gui.ex.glb2html.2":"Tuned page: output file, hole radius, waves, framing","py.gui.ex.glb2html.3":"Region with visitors: shared shell and presence server","py.gui.ex.glb2html.4":"Update an existing region (keeps its configuration and zones)","py.gui.ex.glb2html.5":"Page without the sea","py.gui.ex.glb2tiles.1":"Analyse the GLB without writing anything (measures and planned split)","py.gui.ex.glb2tiles.2":"Split into tiles with the default settings","py.gui.ex.glb2tiles.3":"Split with a budget per tile (MB and triangles)","py.gui.ex.glb2tiles.4":"Redo only the overview","py.gui.ex.oar2glb.1":"Convert a region (OAR to GLB)","py.gui.ex.oar2glb.2":"Convert and keep the intermediate files","py.gui.ex.oar2glb.3":"Diagnostic only: changes nothing, does not run convoar","py.gui.ex.oar2glb.4":"Add the full terrain to an existing GLB (no convoar)","py.gui.ex.oar2glb.5":"Convert a region that has PBR materials, 256 px PBR textures (lighter GLB)","py.gui.ex.extraire_batiments.1":"List the groups of the OAR","py.gui.ex.extraire_batiments.2":"List filtered by name, groups of at least 5 parts","py.gui.ex.extraire_batiments.3":"Extract one group by its number","py.gui.ex.extraire_batiments.4":"Extract the groups that have a given name","py.gui.ex.extraire_batiments.5":"Merge several groups into one file","py.gui.ex.extraire_batiments.6":"Simulate extracting everything (without delivery boxes or rails), writes nothing","py.gui.ex.iar2oar.1":"List the contents of an IAR","py.gui.ex.iar2oar.2":"List filtered by name","py.gui.ex.iar2oar.3":"Make an OAR from an IAR","py.gui.ex.iar2oar.4":"Filtered OAR, without the objects contained in others, cells 4 m apart","py.gui.ex.diag_carte.1":"Query a presence server (address and names key)","py.gui.ex.diag_carte.2":"wss:// server with the page origin","py.gui.default":"default: {0}","py.gui.default_none":"no default value","py.gui.choices":"possible values: {0}","py.gui.positional":"Argument without an option name.","py.gui.optional_value":"The value is optional: tick \"option alone\" to write the option without a value.","py.gui.flag_on":"When ticked, the option is added to the command.","py.gui.tri_hint":"Choose \"yes\" or \"no\" to write the option or its opposite; \"(default)\" writes nothing.","py.gui.tri_default":"(default)","py.gui.tri_yes":"yes","py.gui.tri_no":"no","py.gui.alone":"option alone","py.gui.browse_file":"File...","py.gui.browse_dir":"Folder...","py.gui.command":"Equivalent command (for information: the Run button runs it for you):","py.gui.copy":"Copy the command","py.gui.run":"Run (Ctrl+Enter)","py.gui.stop":"Stop","py.gui.reset":"Clear all","py.gui.output":"Tool output:","py.gui.status_ready":"Ready.","py.gui.status_running":"Running...","py.gui.status_done":"Finished, return code {0}.","py.gui.status_stopped":"Stop requested.","py.gui.status_copied":"Command copied.","py.gui.status_invalid":"To fix before running (lines marked \"!\"): {0}","py.gui.problem_required":"{0}: value required","py.gui.problem_number":"{0}: unreadable number ({1})","py.gui.problem_choice":"{0}: value not in the list ({1})","py.gui.start_failed":"Cannot start the tool: {0}","py.gui.multi_hint":"Repeatable option: one value per line, the option is written once per line.","py.gui.help.tool":"tool shown at start (one of: {0})","py.gui.default_in_help":"default: see the help","py.gui.default_above":"Default value: see the text above.","py.gui.help.shortcuts":"creates Windows shortcuts (.lnk) on the desktop: one for the window, one per tool; --dry-run shows what would be done","py.gui.help.remove_shortcuts":"removes the shortcuts created by --shortcuts (only those)","py.gui.help.shortcuts_folder":"folder of the shortcuts (default: the Windows desktop)","py.gui.help.dry_run":"with --shortcuts or --remove-shortcuts: says what would be done, without writing or deleting anything","py.gui.sc_name_all":"Web_3d - launcher","py.gui.sc_desc":"Graphical launcher for the Web_3d tools","py.gui.sc_windows_only":"Shortcuts (.lnk) can only be created on Windows. Here, --dry-run shows what would be done.","py.gui.sc_console":"pythonw.exe not found next to python.exe: the shortcuts will also open a black console window.","py.gui.sc_create":"to create: {0} -> {1}","py.gui.sc_would_create":"would be created: {0} -> {1}","py.gui.sc_removed":"removed: {0}","py.gui.sc_would_remove":"would be removed: {0}","py.gui.sc_ps_fail":"PowerShell could not create the shortcuts: {0}","py.gui.sc_summary_done":"{0} shortcut(s) created in {1}. If Python is moved or reinstalled, run --shortcuts again.","py.gui.sc_summary_dry":"{0} shortcut(s) would be created in {1} (nothing was written).","py.gui.sc_summary_remove":"{0} shortcut(s) concerned in {1}.","py.gui.sc_icon":"shortcut icon: {0}","py.gui.sc_no_icon":"favicon.ico not found: the shortcuts will keep Python's icon."},"fr":{"_name":"Français","py.common.help":"afficher ce message d'aide et quitter","py.common.lang_help":"langue des messages et de l'aide : fr, en ou auto (défaut : langue du système ; variable d'environnement WEB3D_LANG équivalente). Disponibles : {0}","py.common.optionals":"options","py.common.positionals":"arguments","py.common.version_mark":"{0}, empreinte {1}","py.common.version":"afficher la version et quitter","py.gui.desc":"web3d_gui.py {0} : lanceur graphique des outils Web_3d (glb2html, glb2tiles, oar2glb, extraire_batiments, iar2oar, diag_carte). Une liste pour choisir l'outil, une liste d'exemples d'usages de base qui remplit les champs, une ligne par option, l'aide de chaque option, la commande qui en résulte, un bouton pour lancer l'outil et sa sortie. Les options sont lues dans l'outil : il n'est pas modifié.","py.gui.epilog":"Exemples :\n  python web3d_gui.py\n  python web3d_gui.py --tool oar2glb\n  python web3d_gui.py --shortcuts --dry-run\n  python web3d_gui.py --shortcuts\n  python web3d_gui.py --lang en\nNécessite tkinter. Les chemins se choisissent avec les boutons Fichier… et Dossier… ; l'aide de l'option sous le curseur s'affiche en bas. La liste Exemples remplit les champs avec un usage de base de l'outil : remplace les noms d'exemple par les tiens.","py.gui.no_tk":"ERREUR : tkinter est introuvable. Sous Windows il est installé avec Python (réinstallez Python si besoin) ; sous Linux, installez le paquet python3-tk.","py.gui.no_tool":"ERREUR : {0} est introuvable (cherché à côté de ce script, puis dans le dossier dist). Lancez 'python build.py' ou copiez web3d_gui.py à côté de {0}.","py.gui.read_error":"ERREUR : impossible de lire les options de {0}.","py.gui.title":"Web_3d : lanceur ({0})","py.gui.tool":"Outil :","py.gui.search":"Chercher une option :","py.gui.count":"{0} option(s) affichée(s) sur {1}","py.gui.help_title":"Aide de l'option :","py.gui.help_none":"Passe la souris sur une option, ou clique dans son champ : son aide s'affiche ici.","py.gui.examples":"Exemples :","py.gui.examples_pick":"(choisis un usage de base : il remplit les champs ci-dessous)","py.gui.example_loaded":"Exemple chargé.","py.gui.example_hint":"Remplace les noms d'exemple (fichiers, adresse, clé) par les tiens, puis clique sur Lancer. Tu peux modifier les champs avant.","py.gui.example_invalid":"Cet exemple ne correspond pas à l'outil installé (option inconnue : {0}) : utilise des versions à jour de l'outil et du lanceur.","py.gui.ex.glb2html.1":"Page web simple à partir d'un GLB","py.gui.ex.glb2html.2":"Page réglée : fichier de sortie, rayon du trou, vagues, cadrage","py.gui.ex.glb2html.3":"Région avec visiteurs : coquille commune et serveur de présence","py.gui.ex.glb2html.4":"Mettre à jour une région déjà fabriquée (garde sa configuration et ses zones)","py.gui.ex.glb2html.5":"Page sans mer","py.gui.ex.glb2tiles.1":"Analyser le GLB sans rien écrire (mesures et découpage prévu)","py.gui.ex.glb2tiles.2":"Découper en tuiles avec les réglages par défaut","py.gui.ex.glb2tiles.3":"Découper avec un budget par tuile (Mo et triangles)","py.gui.ex.glb2tiles.4":"Refaire seulement la vue d'ensemble","py.gui.ex.oar2glb.1":"Convertir une région (OAR vers GLB)","py.gui.ex.oar2glb.2":"Convertir en gardant les fichiers intermédiaires","py.gui.ex.oar2glb.3":"Diagnostic seul : ne modifie rien, ne lance pas convoar","py.gui.ex.oar2glb.4":"Ajouter le terrain complet à un GLB existant (sans convoar)","py.gui.ex.oar2glb.5":"Convertir une région qui a des matériaux PBR, textures PBR de 256 px (GLB plus léger)","py.gui.ex.extraire_batiments.1":"Lister les groupes de l'OAR","py.gui.ex.extraire_batiments.2":"Lister en filtrant par nom, groupes de 5 parties au moins","py.gui.ex.extraire_batiments.3":"Extraire un groupe par son numéro","py.gui.ex.extraire_batiments.4":"Extraire les groupes qui portent un nom","py.gui.ex.extraire_batiments.5":"Réunir plusieurs groupes en un seul fichier","py.gui.ex.extraire_batiments.6":"Simuler l'extraction de tout (sans les boîtes ni les rails), sans rien écrire","py.gui.ex.iar2oar.1":"Lister le contenu d'un IAR","py.gui.ex.iar2oar.2":"Lister en filtrant par nom","py.gui.ex.iar2oar.3":"Fabriquer un OAR à partir d'un IAR","py.gui.ex.iar2oar.4":"OAR filtré, sans les objets contenus dans d'autres, cases espacées de 4 m","py.gui.ex.diag_carte.1":"Interroger un serveur de présence (adresse et clé des pseudos)","py.gui.ex.diag_carte.2":"Serveur en wss:// avec l'origine de la page","py.gui.default":"défaut : {0}","py.gui.default_none":"pas de valeur par défaut","py.gui.choices":"valeurs possibles : {0}","py.gui.positional":"Argument sans nom d'option.","py.gui.optional_value":"La valeur est facultative : coche « option seule » pour écrire l'option sans valeur.","py.gui.flag_on":"Cochée, l'option est ajoutée à la commande.","py.gui.tri_hint":"Choisis « oui » ou « non » pour écrire l'option ou son contraire ; « (défaut) » n'écrit rien.","py.gui.tri_default":"(défaut)","py.gui.tri_yes":"oui","py.gui.tri_no":"non","py.gui.alone":"option seule","py.gui.browse_file":"Fichier…","py.gui.browse_dir":"Dossier…","py.gui.command":"Commande équivalente (à titre d'information : le bouton Lancer l'exécute pour vous) :","py.gui.copy":"Copier la commande","py.gui.run":"Lancer (Ctrl+Entrée)","py.gui.stop":"Arrêter","py.gui.reset":"Tout effacer","py.gui.output":"Sortie de l'outil :","py.gui.status_ready":"Prêt.","py.gui.status_running":"En cours…","py.gui.status_done":"Terminé, code de retour {0}.","py.gui.status_stopped":"Arrêt demandé.","py.gui.status_copied":"Commande copiée.","py.gui.status_invalid":"À corriger avant de lancer (lignes marquées « ! ») : {0}","py.gui.problem_required":"{0} : valeur obligatoire","py.gui.problem_number":"{0} : nombre illisible ({1})","py.gui.problem_choice":"{0} : valeur hors de la liste ({1})","py.gui.start_failed":"Impossible de lancer l'outil : {0}","py.gui.multi_hint":"Option répétable : une valeur par ligne, l'option est écrite une fois par ligne.","py.gui.help.tool":"outil affiché à l'ouverture (parmi : {0})","py.gui.default_in_help":"défaut : voir l'aide","py.gui.default_above":"Valeur par défaut : voir le texte ci-dessus.","py.gui.help.shortcuts":"crée des raccourcis Windows (.lnk) sur le bureau : un pour la fenêtre, un par outil ; --dry-run montre ce qui serait fait","py.gui.help.remove_shortcuts":"supprime les raccourcis créés par --shortcuts (seulement ceux-là)","py.gui.help.shortcuts_folder":"dossier des raccourcis (défaut : le bureau de Windows)","py.gui.help.dry_run":"avec --shortcuts ou --remove-shortcuts : dit ce qui serait fait, sans rien écrire ni supprimer","py.gui.sc_name_all":"Web_3d - lanceur","py.gui.sc_desc":"Lanceur graphique des outils Web_3d","py.gui.sc_windows_only":"Les raccourcis (.lnk) ne se créent que sous Windows. Ici, --dry-run montre ce qui serait fait.","py.gui.sc_console":"pythonw.exe est introuvable à côté de python.exe : les raccourcis ouvriront aussi une fenêtre console noire.","py.gui.sc_create":"à créer : {0} -> {1}","py.gui.sc_would_create":"serait créé : {0} -> {1}","py.gui.sc_removed":"supprimé : {0}","py.gui.sc_would_remove":"serait supprimé : {0}","py.gui.sc_ps_fail":"PowerShell n'a pas pu créer les raccourcis : {0}","py.gui.sc_summary_done":"{0} raccourci(s) créé(s) dans {1}. Si Python est déplacé ou réinstallé, relancez --shortcuts.","py.gui.sc_summary_dry":"{0} raccourci(s) seraient créés dans {1} (rien n'a été écrit).","py.gui.sc_summary_remove":"{0} raccourci(s) concerné(s) dans {1}.","py.gui.sc_icon":"icône des raccourcis : {0}","py.gui.sc_no_icon":"favicon.ico est introuvable : les raccourcis garderont l'icône de Python."}}''')


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


VERSION = "1.9.17 (11/11/2026)"      # remplacé par build.py (fichier VERSION) dans dist/web3d_gui.py
MARK = "3dcd14a2"      # empreinte du fichier fabriqué, inscrite par build.py ; reste telle quelle depuis tools/

OUTILS = (("glb2html", "glb2html.py"), ("glb2tiles", "glb2tiles.py"), ("oar2glb", "oar2glb.py"), ("extraire_batiments", "extraire_batiments.py"),
          ("iar2oar", "iar2oar.py"), ("diag_carte", "diag_carte.py"))      # (nom, fichier) ; un outil de plus : une ligne ici
MOTS_CHEMIN = ("FILE", "FOLDER", "DIR")      # un métavar qui contient l'un de ces mots, ou qui finit par .html / .json : un fichier ou un dossier
DEST_CHEMIN = ("input", "o", "output", "sortie", "convoar", "register", "thumb", "oar", "glb", "iar")      # arguments sans métavar qui sont des chemins

# exemples d'usages de base, par outil : (clé du titre dans src/i18n, arguments comme dans une console) ; les noms (Atoll.glb, ADRESSE, MA_CLE...) sont à remplacer par les siens ;
# tests/gui.py vérifie que le vrai parseur de chaque outil accepte chaque exemple et que la fenêtre le remet à l'identique
EXEMPLES = {
    "glb2html": (
        ("py.gui.ex.glb2html.1", ["Atoll.glb"]),
        ("py.gui.ex.glb2html.2", ["Atoll.glb", "-o", "Atoll.html", "--hole", "90", "--wave", "1.2", "--zoom", "1.3"]),
        ("py.gui.ex.glb2html.3", ["Atoll.glb", "-o", "Atoll.html", "--shared-shell", "--presence-url", "ws://ADRESSE:8765"]),
        ("py.gui.ex.glb2html.4", ["-o", "Atoll.html", "--update"]),
        ("py.gui.ex.glb2html.5", ["Atoll.glb", "--no-sea"]),
    ),
    "glb2tiles": (
        ("py.gui.ex.glb2tiles.1", ["Region.glb", "--analyse"]),
        ("py.gui.ex.glb2tiles.2", ["Region.glb"]),
        ("py.gui.ex.glb2tiles.3", ["Region.glb", "--budget", "32", "--budget-triangles", "1500000"]),
        ("py.gui.ex.glb2tiles.4", ["Region.glb", "--overview-only"]),
    ),
    "oar2glb": (
        ("py.gui.ex.oar2glb.1", ["Atoll.oar"]),
        ("py.gui.ex.oar2glb.2", ["Atoll.oar", "--keep"]),
        ("py.gui.ex.oar2glb.3", ["Atoll.oar", "--diag"]),
        ("py.gui.ex.oar2glb.4", ["Atoll.oar", "--terrain-only", "Atoll.glb"]),
        ("py.gui.ex.oar2glb.5", ["Atoll.oar", "--pbr-size", "256"]),
    ),
    "extraire_batiments": (
        ("py.gui.ex.extraire_batiments.1", ["Atoll.oar", "Atoll.glb", "--list"]),
        ("py.gui.ex.extraire_batiments.2", ["Atoll.oar", "Atoll.glb", "--list", "--filter", "House", "--min-parts", "5"]),
        ("py.gui.ex.extraire_batiments.3", ["Atoll.oar", "Atoll.glb", "--group", "12", "-o", "batiments"]),
        ("py.gui.ex.extraire_batiments.4", ["Atoll.oar", "Atoll.glb", "--name", "Jewel Box House", "-o", "batiments"]),
        ("py.gui.ex.extraire_batiments.5", ["Atoll.oar", "Atoll.glb", "--group", "12", "--group", "15", "--merge", "Maison et garage"]),
        ("py.gui.ex.extraire_batiments.6", ["Atoll.oar", "Atoll.glb", "--all", "--min-parts", "5", "--box", "RAKis", "--exclude", "Rail|Train", "--dry-run"]),
    ),
    "iar2oar": (
        ("py.gui.ex.iar2oar.1", ["Inventaire.iar", "--list"]),
        ("py.gui.ex.iar2oar.2", ["Inventaire.iar", "--list", "--filter", "House"]),
        ("py.gui.ex.iar2oar.3", ["Inventaire.iar", "-o", "inventaire.oar"]),
        ("py.gui.ex.iar2oar.4", ["Inventaire.iar", "-o", "inventaire.oar", "--filter", "House", "--no-nested", "--margin", "4"]),
    ),
    "diag_carte": (
        ("py.gui.ex.diag_carte.1", ["ws://ADRESSE:8765", "MA_CLE"]),
        ("py.gui.ex.diag_carte.2", ["wss://ADRESSE", "MA_CLE", "https://VOTRE-SITE"]),
    ),
}


def version_tag():
    return VERSION if MARK.startswith("__") else _tr("py.common.version_mark", VERSION, MARK)


# ---------------------------------------------------------------- lecture des options de l'outil

def trouver_outil(fichier):
    """à côté de ce script, sinon dans le dossier dist voisin (quand le script est lancé depuis tools/)"""
    ici = Path(__file__).resolve().parent
    for p in (ici / fichier, ici.parent / "dist" / fichier):
        if p.is_file():
            return p
    return None


def lire_parser(chemin, langue=None):
    """exécute l'outil jusqu'à son parse_args, récupère le parser, n'exécute rien d'autre ; une erreur de l'outil avant son parse_args
    ne remonte pas (la fenêtre resterait muette) : le parser vaut alors None et lire_parser.erreur dit pourquoi"""
    pris = {}
    lire_parser.erreur = ""

    def faux(self, *a, **k):
        pris["p"] = self
        raise SystemExit(0)

    orig_pa, orig_pka = argparse.ArgumentParser.parse_args, argparse.ArgumentParser.parse_known_args
    argparse.ArgumentParser.parse_args = faux
    argparse.ArgumentParser.parse_known_args = faux
    argv, path = sys.argv, list(sys.path)
    env_avant = os.environ.get("WEB3D_LANG")
    if langue:
        os.environ["WEB3D_LANG"] = langue
    sys.argv = [str(chemin), "--help", "--nopause"]
    sys.path.insert(0, str(chemin.parent))
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            try:
                runpy.run_path(str(chemin), run_name="__main__")
            except SystemExit:
                pass
            except Exception as e:
                lire_parser.erreur = f"{type(e).__name__} : {e}"
    finally:
        argparse.ArgumentParser.parse_args, argparse.ArgumentParser.parse_known_args = orig_pa, orig_pka
        sys.argv, sys.path[:] = argv, path
        if langue:
            if env_avant is None:
                os.environ.pop("WEB3D_LANG", None)
            else:
                os.environ["WEB3D_LANG"] = env_avant
    return pris.get("p")


def texte_defaut(a):
    d = a.default
    if d is None or d is argparse.SUPPRESS:
        return ""
    if isinstance(d, int) and not isinstance(d, bool) and "color" in a.dest:
        return f"{d:06x}"                                   # couleurs en hexadécimal, comme dans l'aide de l'outil
    if isinstance(d, (tuple, list)):
        return ", ".join(str(x) for x in d)
    return str(d)


def defaut_dans_aide(c):
    """vrai si l'option n'a pas de valeur par défaut chiffrée mais que son texte d'aide en parle (ex. --spectate : actif dès qu'une adresse de présence est donnée ; -o : « <nom> - Offline.html » à côté du .glb)"""
    return c["defaut"] == "" and bool(re.search(r"d[ée]faut|default", c["aide"] or "", re.I))


def champs_depuis(parser):
    """un champ (dictionnaire) par argument du parser, dans l'ordre de l'outil, sauf l'aide, la version et --lang"""
    res, vus = [], set()
    for a in parser._actions:
        if isinstance(a, (argparse._HelpAction, argparse._VersionAction)) or a.dest in ("help", "lang") or id(a) in vus:
            continue
        vus.add(id(a))
        mv = a.metavar if isinstance(a.metavar, str) else (" ".join(a.metavar) if a.metavar else "")
        opts = list(a.option_strings)
        if isinstance(a, argparse._AppendAction):
            genre = "multiple"
        elif isinstance(a, argparse.BooleanOptionalAction):
            genre = "tri"
        elif isinstance(a, (argparse._StoreTrueAction, argparse._StoreFalseAction)):
            genre = "flag"
        elif a.choices:
            genre = "choix"
        elif a.type is float or a.type is int:
            genre = "nombre"
        elif a.type is Path or any(k in mv.upper() for k in MOTS_CHEMIN) or mv.lower().endswith((".html", ".json")) or a.dest in DEST_CHEMIN:
            genre = "chemin"
        else:
            genre = "texte"
        if genre in ("texte", "chemin", "nombre", "choix") and opts and a.nargs == "?":
            genre = "facultatif" if genre != "choix" else genre
        res.append({"dest": a.dest, "options": opts, "genre": genre, "metavar": mv, "aide": a.help if a.help and a.help is not argparse.SUPPRESS else "",
                    "defaut": texte_defaut(a), "choix": [str(c) for c in a.choices] if a.choices else [], "positionnel": not opts,
                    "obligatoire": bool(getattr(a, "required", False)) or (not opts and a.nargs is None),
                    "nombre": "int" if a.type is int else "float" if a.type is float else "", "ptype": a.type is Path})
    return res


def texte_aide(c):
    t = "  /  ".join(c["options"]) if c["options"] else c["dest"]
    if c["metavar"] and c["genre"] not in ("flag", "tri"):
        t += " " + c["metavar"]
    t += "\n" + (c["aide"] or "")
    if c["positionnel"]:
        t += "\n" + _tr("py.gui.positional")
    if c["genre"] == "flag":
        t += "\n" + _tr("py.gui.flag_on")
    elif c["genre"] == "tri":
        t += "\n" + _tr("py.gui.tri_hint")
    elif c["genre"] == "facultatif":
        t += "\n" + _tr("py.gui.optional_value")
    elif c["genre"] == "multiple":
        t += "\n" + _tr("py.gui.multi_hint")
    if c["choix"]:
        t += "\n" + _tr("py.gui.choices", ", ".join(c["choix"]))
    t += "\n" + (_tr("py.gui.default", c["defaut"]) if c["defaut"] != "" else _tr("py.gui.default_above") if defaut_dans_aide(c) else _tr("py.gui.default_none"))
    return t


# ---------------------------------------------------------------- valeurs, vérification, ligne de commande (sans fenêtre : testables)

def valeur_vide(c):
    """valeur d'un champ qu'on n'a pas touché"""
    return False if c["genre"] == "flag" else ("", False) if c["genre"] == "facultatif" else ""


def nom_champ(c):
    return c["options"][0] if c["options"] else c["dest"]


def verifier(champs, valeurs):
    """[(dest, texte)] : champ obligatoire vide, nombre illisible, valeur hors de la liste"""
    pb = []
    for c in champs:
        v = valeurs.get(c["dest"], valeur_vide(c))
        txt = (v[0] if isinstance(v, tuple) else v) if not isinstance(v, bool) else ""
        txt = txt.strip()
        if c["obligatoire"] and not txt and not (isinstance(v, tuple) and v[1]):
            pb.append((c["dest"], _tr("py.gui.problem_required", nom_champ(c))))
        elif txt and c["genre"] == "nombre":
            try:
                (int if c["nombre"] == "int" else float)(txt.replace(",", "."))
            except ValueError:
                pb.append((c["dest"], _tr("py.gui.problem_number", nom_champ(c), txt)))
        elif txt and c["genre"] == "choix" and txt not in c["choix"]:
            pb.append((c["dest"], _tr("py.gui.problem_choice", nom_champ(c), txt)))
    return pb


def construire(champs, valeurs):
    """liste d'arguments de l'outil : les arguments sans nom d'abord, puis les options ; un champ vide ou non touché n'écrit rien"""
    pos, opt = [], []
    for c in champs:
        v = valeurs.get(c["dest"], valeur_vide(c))
        o = c["options"][0] if c["options"] else None
        if c["genre"] == "flag":
            if v and o:
                opt.append(o)
            continue
        if c["genre"] == "tri":
            if v in ("yes", "no") and o:
                opt.append(o if v == "yes" else next((x for x in c["options"] if x.startswith("--no-")), "--no-" + o[2:]))
            continue
        if c["genre"] == "multiple":
            for ligne in (v or "").splitlines():
                ligne = ligne.strip()
                if ligne and o:
                    opt += [f"{o}={ligne}"] if ligne.startswith("-") else [o, ligne]
            continue
        seul = False
        if isinstance(v, tuple):
            v, seul = v
        v = (v or "").strip()
        if c["genre"] == "nombre":
            v = v.replace(",", ".")
        if not v and not seul:
            continue
        if not o:
            pos.append(v)
        elif not v:
            opt.append(o)
        elif v.startswith("-"):
            opt.append(f"{o}={v}")
        else:
            opt += [o, v]
    return pos + opt


def ligne_commande(fichier, args):
    q = subprocess.list2cmdline if os.name == "nt" else __import__("shlex").join
    return "python " + q([fichier] + list(args))


def lire_exemple(champs, args):
    """l'inverse de construire : les valeurs des champs pour une liste d'arguments de console ; ValueError si une option n'existe pas dans l'outil"""
    par_option = {o: c for c in champs for o in c["options"]}
    sans_nom = [c for c in champs if c["positionnel"]]
    vals, k, i = {}, 0, 0
    while i < len(args):
        a, v = args[i], None
        i += 1
        if a.startswith("--") and "=" in a:
            a, v = a.split("=", 1)
        c = par_option.get(a)
        if c is None:
            if a.startswith("-") or k >= len(sans_nom):
                raise ValueError(a)
            vals[sans_nom[k]["dest"]] = a
            k += 1
            continue
        d, genre = c["dest"], c["genre"]
        if genre == "flag":
            vals[d] = True
        elif genre == "tri":
            vals[d] = "no" if a.startswith("--no-") else "yes"
        else:
            if v is None:
                if genre == "facultatif" and (i >= len(args) or args[i].startswith("-")):
                    vals[d] = ("", True)
                    continue
                if i >= len(args):
                    raise ValueError(a)
                v = args[i]
                i += 1
            if genre == "multiple":
                vals[d] = (vals[d] + "\n" if d in vals else "") + v
            else:
                vals[d] = (v, False) if genre == "facultatif" else v
    return vals


# ---------------------------------------------------------------- la fenêtre

class _TexteVar:
    """un champ de texte à plusieurs lignes (option répétable) qui répond comme une variable tkinter : get, set, trace_add"""
    def __init__(self, w, rappel):
        self.w, self.rappel = w, rappel
        w.bind("<KeyRelease>", lambda e: rappel())

    def get(self):
        return self.w.get("1.0", "end").strip("\n")

    def set(self, v):
        self.w.delete("1.0", "end")
        self.w.insert("1.0", v)
        self.rappel()

    def trace_add(self, *a):
        pass


def fenetre(outils, tk, ttk, filedialog, depart=None):
    """crée la fenêtre ; outils = [(nom, chemin du fichier)] ; rend un objet : .root, .champs, .vars, .valeurs(), .changer(nom), .lancer() ..."""
    chemins = dict(outils)
    root = tk.Tk()
    root.title(_tr("py.gui.title", version_tag()))
    root.geometry("1000x760")
    root.minsize(760, 520)

    class F:
        pass
    f = F()
    f.root, f.vars, f.lignes, f.proc, f.file = root, {}, {}, None, queue.Queue()
    f.nom, f.chemin, f.champs, f.cache = None, None, [], {}

    # ---- haut : choix de l'outil, recherche et compteur
    haut = ttk.Frame(root, padding=(8, 6))
    haut.pack(fill="x")
    ttk.Label(haut, text=_tr("py.gui.tool")).pack(side="left")
    f.outil = tk.StringVar()
    f.choix_outil = ttk.Combobox(haut, textvariable=f.outil, state="readonly", width=26, values=[chemins[n].name for n, _c in outils])
    f.choix_outil.pack(side="left", padx=(4, 0))
    ttk.Label(haut, text="   " + _tr("py.gui.search")).pack(side="left")
    f.filtre = tk.StringVar()
    ttk.Entry(haut, textvariable=f.filtre, width=28).pack(side="left", padx=4)
    f.compteur = ttk.Label(haut, text="")
    f.compteur.pack(side="left", padx=10)
    ligne_ex = ttk.Frame(root, padding=(8, 0, 8, 4))
    ligne_ex.pack(fill="x")
    ttk.Label(ligne_ex, text=_tr("py.gui.examples")).pack(side="left")
    f.exemple = tk.StringVar()
    f.choix_exemple = ttk.Combobox(ligne_ex, textvariable=f.exemple, state="readonly", width=70)
    f.choix_exemple.pack(side="left", padx=(4, 0), fill="x", expand=True)
    f.liste_ex = []

    # ---- bas d'abord (pour qu'il garde sa place), puis le milieu qui s'étire
    bas = ttk.Frame(root, padding=(8, 4))
    bas.pack(side="bottom", fill="both")
    ttk.Label(bas, text=_tr("py.gui.help_title")).pack(anchor="w")
    f.aide = tk.Text(bas, height=4, wrap="word", state="disabled", relief="solid", borderwidth=1)
    f.aide.pack(fill="x", pady=(0, 4))
    ttk.Label(bas, text=_tr("py.gui.command")).pack(anchor="w")
    f.cmd = tk.Text(bas, height=3, wrap="word", state="disabled", relief="solid", borderwidth=1)
    f.cmd.pack(fill="x", pady=(0, 4))
    boutons = ttk.Frame(bas)
    boutons.pack(fill="x", pady=(0, 4))
    f.b_copier = ttk.Button(boutons, text=_tr("py.gui.copy"))
    f.b_lancer = ttk.Button(boutons, text=_tr("py.gui.run"))
    f.b_stop = ttk.Button(boutons, text=_tr("py.gui.stop"), state="disabled")
    f.b_reset = ttk.Button(boutons, text=_tr("py.gui.reset"))
    for b in (f.b_lancer, f.b_stop, f.b_copier, f.b_reset):
        b.pack(side="left", padx=(0, 6))
    f.etat = ttk.Label(boutons, text=_tr("py.gui.status_ready"))
    f.etat.pack(side="left", padx=10)
    ttk.Label(bas, text=_tr("py.gui.output")).pack(anchor="w")
    sortie = ttk.Frame(bas)
    sortie.pack(fill="both")
    f.sortie = tk.Text(sortie, height=7, wrap="word", state="disabled", relief="solid", borderwidth=1)
    ys = ttk.Scrollbar(sortie, orient="vertical", command=f.sortie.yview)
    f.sortie.configure(yscrollcommand=ys.set)
    f.sortie.pack(side="left", fill="both", expand=True)
    ys.pack(side="right", fill="y")

    # ---- milieu : les options, dans une zone qui défile
    milieu = ttk.Frame(root)
    milieu.pack(fill="both", expand=True, padx=8)
    cv = tk.Canvas(milieu, highlightthickness=0)
    sb = ttk.Scrollbar(milieu, orient="vertical", command=cv.yview)
    grille = ttk.Frame(cv)
    grille.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
    fen = cv.create_window((0, 0), window=grille, anchor="nw")
    cv.bind("<Configure>", lambda e: cv.itemconfigure(fen, width=e.width))
    cv.configure(yscrollcommand=sb.set)
    cv.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    def molette(e):
        cv.yview_scroll(-1 if (getattr(e, "num", 0) == 4 or getattr(e, "delta", 0) > 0) else 1, "units")
    root.bind_all("<MouseWheel>", molette)
    root.bind_all("<Button-4>", molette)
    root.bind_all("<Button-5>", molette)
    grille.columnconfigure(4, weight=1)

    def ecrire(widget, texte, ajout=False):
        widget.configure(state="normal")
        if not ajout:
            widget.delete("1.0", "end")
        widget.insert("end", texte)
        widget.configure(state="disabled")
        widget.see("end") if ajout else None

    def montrer_aide(c):
        ecrire(f.aide, texte_aide(c))

    def valeurs():
        v = {}
        for c in f.champs:
            x = f.vars[c["dest"]]
            if c["genre"] == "flag":
                v[c["dest"]] = bool(x.get())
            elif c["genre"] == "tri":
                v[c["dest"]] = {_tr("py.gui.tri_yes"): "yes", _tr("py.gui.tri_no"): "no"}.get(x.get(), "")
            elif c["genre"] == "facultatif":
                v[c["dest"]] = (x[0].get(), bool(x[1].get()))
            else:
                v[c["dest"]] = x.get()
        return v
    f.valeurs = valeurs

    def maj_commande(*_):
        if not f.champs:
            return
        pb = {d for d, _t in verifier(f.champs, valeurs())}
        for d, (marque, _c) in f.lignes.items():
            marque.configure(text="!" if d in pb else " ")      # le signe « ! » : l'état ne dépend pas de la couleur
        ecrire(f.cmd, ligne_commande(f.chemin.name, construire(f.champs, valeurs())))
    f.maj = maj_commande

    def choisir(var, dossier):
        p = filedialog.askdirectory() if dossier else filedialog.askopenfilename()
        if p:
            var.set(p)

    # ---- les lignes de l'outil choisi (refaites à chaque changement d'outil)
    def lignes_construire():
        for w in grille.winfo_children():
            w.destroy()
        f.vars, f.lignes = {}, {}
        for i, c in enumerate(f.champs):
            marque = ttk.Label(grille, text=" ", width=2, font=("TkDefaultFont", 10, "bold"))
            marque.grid(row=i, column=0, sticky="w")
            etiq = ttk.Label(grille, text="  /  ".join(c["options"]) if c["options"] else c["dest"], width=30, font="TkFixedFont", anchor="w")
            etiq.grid(row=i, column=1, sticky="w", padx=(0, 6))
            cases = [marque, etiq]
            extra = ttk.Frame(grille)
            extra.grid(row=i, column=3, sticky="w", padx=4)
            if c["genre"] == "flag":
                var = tk.BooleanVar(value=False)
                w = ttk.Checkbutton(grille, variable=var)
            elif c["genre"] == "tri":
                var = tk.StringVar(value=_tr("py.gui.tri_default"))
                w = ttk.Combobox(grille, textvariable=var, state="readonly", width=12, values=(_tr("py.gui.tri_default"), _tr("py.gui.tri_yes"), _tr("py.gui.tri_no")))
            elif c["genre"] == "choix":
                var = tk.StringVar(value="")
                w = ttk.Combobox(grille, textvariable=var, state="readonly", width=12, values=[""] + c["choix"])
            elif c["genre"] == "facultatif":
                t, seul = tk.StringVar(value=""), tk.BooleanVar(value=False)
                var = (t, seul)
                w = ttk.Entry(grille, textvariable=t)
                ttk.Checkbutton(extra, text=_tr("py.gui.alone"), variable=seul).pack(side="left")
            elif c["genre"] == "multiple":
                w = tk.Text(grille, height=3, width=40, relief="solid", borderwidth=1)
                var = _TexteVar(w, maj_commande)
            else:
                var = tk.StringVar(value="")
                w = ttk.Entry(grille, textvariable=var, width=14 if c["genre"] == "nombre" else 40)
            if c["genre"] in ("chemin", "facultatif") and (c["genre"] == "chemin" or c["ptype"] or any(k in c["metavar"].upper() for k in MOTS_CHEMIN) or c["metavar"].lower().endswith((".html", ".json"))):
                vv = var[0] if isinstance(var, tuple) else var
                ttk.Button(extra, text=_tr("py.gui.browse_file"), command=lambda v=vv: choisir(v, False)).pack(side="left", padx=2)
                ttk.Button(extra, text=_tr("py.gui.browse_dir"), command=lambda v=vv: choisir(v, True)).pack(side="left", padx=2)
            w.grid(row=i, column=2, sticky="we" if c["genre"] in ("texte", "chemin", "facultatif", "multiple") else "w")
            cases += [w, extra]
            dfl = ttk.Label(grille, text=(_tr("py.gui.default", c["defaut"]) if c["defaut"] != "" else _tr("py.gui.default_in_help") if defaut_dans_aide(c) else ""), foreground="#555555", wraplength=180, justify="left")
            dfl.grid(row=i, column=4, sticky="w", padx=(6, 0))
            cases.append(dfl)
            for x in cases:
                x.bind("<Enter>", lambda e, c=c: montrer_aide(c), add="+")
            w.bind("<FocusIn>", lambda e, c=c: montrer_aide(c), add="+")
            f.vars[c["dest"]] = var
            f.lignes[c["dest"]] = (marque, cases)
            for v in (var if isinstance(var, tuple) else (var,)):
                v.trace_add("write", maj_commande)
        f.filtrer()

    def filtrer(*_):
        mot = f.filtre.get().strip().lower()
        n = 0
        for c in f.champs:
            if c["dest"] not in f.lignes:
                continue
            ok = (not mot) or mot in (" ".join(c["options"]) + " " + c["dest"] + " " + c["aide"]).lower()
            for x in f.lignes[c["dest"]][1]:
                x.grid() if ok else x.grid_remove()
            n += ok
        f.compteur.configure(text=_tr("py.gui.count", n, len(f.champs)))
    f.filtre.trace_add("write", filtrer)
    f.filtrer = filtrer

    def changer(nom):
        """affiche les options de l'outil `nom` (refusé pendant qu'un outil tourne) ; rend True si le changement a eu lieu"""
        if f.proc is not None or nom not in chemins:
            f.outil.set(f.chemin.name if f.chemin else "")
            return False
        chemin = chemins[nom]
        champs = f.cache.get(nom)
        if champs is None:
            parser = lire_parser(chemin, I18N_LANG)
            if parser is None:
                f.etat.configure(text=_tr("py.gui.read_error", chemin.name) + (" (" + lire_parser.erreur + ")" if getattr(lire_parser, "erreur", "") else ""))
                f.outil.set(f.chemin.name if f.chemin else "")
                return False
            champs = f.cache[nom] = champs_depuis(parser)
        f.filtre.set("")      # avant le changement : le filtre se vide sur les lignes de l'outil précédent
        f.nom, f.chemin, f.champs = nom, chemin, champs
        f.outil.set(chemin.name)
        f.liste_ex = [(_tr(cle), args) for cle, args in EXEMPLES.get(nom, ())]
        f.choix_exemple.configure(values=[t for t, _a in f.liste_ex], state="readonly" if f.liste_ex else "disabled")
        f.exemple.set(_tr("py.gui.examples_pick") if f.liste_ex else "")
        lignes_construire()
        ecrire(f.aide, _tr("py.gui.help_none"))
        ecrire(f.sortie, "")
        f.etat.configure(text=_tr("py.gui.status_ready"))
        cv.yview_moveto(0)
        maj_commande()
        return True
    f.changer = changer
    f.choix_outil.bind("<<ComboboxSelected>>", lambda e: changer(next((n for n, c in outils if c.name == f.outil.get()), None)))

    # ---- boutons
    def copier():
        root.clipboard_clear()
        root.clipboard_append(ligne_commande(f.chemin.name, construire(f.champs, valeurs())))
        f.etat.configure(text=_tr("py.gui.status_copied"))
    f.b_copier.configure(command=copier)

    def effacer():
        for c in f.champs:
            x = f.vars[c["dest"]]
            if c["genre"] == "flag":
                x.set(False)
            elif c["genre"] == "tri":
                x.set(_tr("py.gui.tri_default"))
            elif c["genre"] == "facultatif":
                x[0].set("")
                x[1].set(False)
            else:
                x.set("")
    f.b_reset.configure(command=effacer)
    f.effacer = effacer

    def appliquer(vals):
        """remet dans les champs les valeurs rendues par lire_exemple"""
        for c in f.champs:
            if c["dest"] not in vals:
                continue
            v, x = vals[c["dest"]], f.vars[c["dest"]]
            if c["genre"] == "flag":
                x.set(bool(v))
            elif c["genre"] == "tri":
                x.set({"yes": _tr("py.gui.tri_yes"), "no": _tr("py.gui.tri_no")}.get(v, _tr("py.gui.tri_default")))
            elif c["genre"] == "facultatif":
                x[0].set(v[0])
                x[1].set(bool(v[1]))
            else:
                x.set(v)

    def choisir_exemple(_e=None):
        i = f.choix_exemple.current()
        if f.proc is not None or not 0 <= i < len(f.liste_ex):
            return
        titre, args = f.liste_ex[i]
        try:
            vals = lire_exemple(f.champs, args)
        except ValueError as e:
            f.etat.configure(text=_tr("py.gui.example_invalid", e))
            return
        effacer()
        f.filtre.set("")
        appliquer(vals)
        ecrire(f.aide, titre + "\n" + _tr("py.gui.example_hint"))
        f.etat.configure(text=_tr("py.gui.example_loaded"))
        maj_commande()
    f.choisir_exemple = choisir_exemple
    f.choix_exemple.bind("<<ComboboxSelected>>", choisir_exemple)

    def lire(proc):
        for ligne in iter(proc.stdout.readline, b""):
            f.file.put(("txt", ligne.decode("utf-8", "replace")))
        f.file.put(("fin", proc.wait()))

    def pomper():
        try:
            while True:
                genre, x = f.file.get_nowait()
                if genre == "txt":
                    ecrire(f.sortie, x, ajout=True)
                else:
                    f.proc = None
                    f.b_lancer.configure(state="normal")
                    f.b_stop.configure(state="disabled")
                    f.choix_outil.configure(state="readonly")
                    f.choix_exemple.configure(state="readonly" if f.liste_ex else "disabled")
                    f.etat.configure(text=_tr("py.gui.status_done", x))
                    return
        except queue.Empty:
            pass
        if f.proc is not None:
            root.after(80, pomper)

    def lancer(_e=None):
        if f.proc is not None:
            return
        pb = verifier(f.champs, valeurs())
        if pb:
            f.etat.configure(text=_tr("py.gui.status_invalid", " ; ".join(t for _d, t in pb)))
            maj_commande()
            return
        args = construire(f.champs, valeurs())
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1", WEB3D_LANG=I18N_LANG)
        kw = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        ecrire(f.sortie, "> " + ligne_commande(f.chemin.name, args) + "\n")
        try:
            f.proc = subprocess.Popen([sys.executable, str(f.chemin)] + args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, **kw)
        except OSError as e:
            f.proc = None
            ecrire(f.sortie, _tr("py.gui.start_failed", e), ajout=True)
            return
        f.b_lancer.configure(state="disabled")
        f.b_stop.configure(state="normal")
        f.choix_outil.configure(state="disabled")
        f.choix_exemple.configure(state="disabled")
        f.etat.configure(text=_tr("py.gui.status_running"))
        threading.Thread(target=lire, args=(f.proc,), daemon=True).start()
        root.after(80, pomper)
    f.lancer = lancer
    f.b_lancer.configure(command=lancer)
    root.bind("<Control-Return>", lancer)

    def arreter():
        if f.proc is not None:
            f.proc.terminate()
            f.etat.configure(text=_tr("py.gui.status_stopped"))
    f.b_stop.configure(command=arreter)

    def fermer():
        if f.proc is not None:
            f.proc.terminate()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", fermer)

    changer(depart if depart in chemins else outils[0][0])
    return f


# ---------------------------------------------------------------- raccourcis (Windows : fichiers .lnk sur le bureau)

def dossier_bureau(dossier=None):
    """le dossier demandé ; sinon le bureau de Windows (demandé à PowerShell : il suit une redirection OneDrive) ; à défaut ~/Desktop"""
    if dossier:
        return Path(dossier).expanduser()
    if os.name == "nt":
        try:
            r = subprocess.run(["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"], capture_output=True, text=True, timeout=30)
            if r.returncode == 0 and r.stdout.strip():
                return Path(r.stdout.strip())
        except (OSError, subprocess.SubprocessError):
            pass
    return Path.home() / "Desktop"


def trouver_icone():
    """l'icône du projet (favicon.ico, la même image que « Réalisé avec Web_3d ») : à côté de ce script (dist), sinon dans src/ ; None si absente"""
    ici = Path(__file__).resolve().parent
    for p in (ici / "favicon.ico", ici.parent / "dist" / "favicon.ico", ici.parent / "src" / "favicon.ico"):
        if p.is_file():
            return p
    return None


def raccourcis_prevus(dossier):
    """[(fichier .lnk, arguments)] : un raccourci pour la fenêtre (premier outil), puis un par outil trouvé à côté de ce script"""
    ce_script = str(Path(__file__).resolve())
    prevus = [(Path(dossier) / (_tr("py.gui.sc_name_all") + ".lnk"), [ce_script])]
    for nom, fichier in OUTILS:
        if trouver_outil(fichier) is not None:
            prevus.append((Path(dossier) / ("Web_3d - " + nom + ".lnk"), [ce_script, "--tool", nom]))
    return prevus


def _ps(s):
    """chaîne PowerShell entre apostrophes : l'apostrophe se double"""
    return "'" + str(s).replace("'", "''") + "'"


def script_powershell(prevus, programme, depart, icone=None):
    """texte du script PowerShell qui crée les raccourcis ; le programme est pythonw.exe (pas de fenêtre console) ; icone : fichier .ico (sinon l'icône de Python)"""
    lignes = ["$ErrorActionPreference = 'Stop'", "$sh = New-Object -ComObject WScript.Shell"]
    for lnk, args in prevus:
        lignes += ["$s = $sh.CreateShortcut(" + _ps(lnk) + ")", "$s.TargetPath = " + _ps(programme),
                   "$s.Arguments = " + _ps(subprocess.list2cmdline(args)), "$s.WorkingDirectory = " + _ps(depart),
                   "$s.Description = " + _ps(_tr("py.gui.sc_desc"))] + (["$s.IconLocation = " + _ps(str(icone) + ",0")] if icone else []) + ["$s.Save()"]
    return "\r\n".join(lignes) + "\r\n"


def gerer_raccourcis(creer, dossier, simuler):
    """crée (ou, avec creer=False, supprime) les raccourcis ; rend le code de sortie : 0 bon, 1 échec, 2 pas sous Windows"""
    if creer and os.name != "nt" and not simuler:
        print(_tr("py.gui.sc_windows_only"))
        return 2
    dossier = dossier_bureau(dossier)
    prevus = raccourcis_prevus(dossier)
    if not creer:
        n = 0
        for lnk, _a in prevus:
            if lnk.is_file():
                n += 1
                print(_tr("py.gui.sc_would_remove" if simuler else "py.gui.sc_removed", lnk))
                if not simuler:
                    lnk.unlink()
        print(_tr("py.gui.sc_summary_remove", n, dossier))
        return 0
    programme = Path(sys.executable).with_name("pythonw.exe") if os.name == "nt" else Path(sys.executable)
    if os.name == "nt" and not programme.is_file():
        print(_tr("py.gui.sc_console"))
        programme = Path(sys.executable)
    icone = trouver_icone()
    print(_tr("py.gui.sc_icon", icone) if icone else _tr("py.gui.sc_no_icon"))
    for lnk, args in prevus:
        print(_tr("py.gui.sc_would_create" if simuler else "py.gui.sc_create", lnk, subprocess.list2cmdline([str(programme)] + args)))
    if simuler:
        print(_tr("py.gui.sc_summary_dry", len(prevus), dossier))
        return 0
    dossier.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        ps1 = Path(tmp) / "raccourcis.ps1"
        ps1.write_text(script_powershell(prevus, programme, Path(__file__).resolve().parent, icone), encoding="utf-8-sig")   # BOM : PowerShell 5 lit ainsi les accents des chemins
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)], capture_output=True, text=True)
    if r.returncode != 0:
        print(_tr("py.gui.sc_ps_fail", (r.stderr or r.stdout).strip()))
        return 1
    print(_tr("py.gui.sc_summary_done", len(prevus), dossier))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=_tr("py.gui.desc", version_tag()), epilog=_tr("py.gui.epilog"),
                                 formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False)
    i18n_add_common(ap)
    ap.add_argument("--version", action="version", version=f"web3d_gui {version_tag()}", help=_tr("py.common.version"))
    ap.add_argument("--tool", choices=[n for n, _f in OUTILS], default=OUTILS[0][0], metavar="NAME", help=_tr("py.gui.help.tool", ", ".join(n for n, _f in OUTILS)))
    ap.add_argument("--shortcuts", action="store_true", help=_tr("py.gui.help.shortcuts"))
    ap.add_argument("--remove-shortcuts", action="store_true", help=_tr("py.gui.help.remove_shortcuts"))
    ap.add_argument("--shortcuts-folder", metavar="FOLDER", help=_tr("py.gui.help.shortcuts_folder"))
    ap.add_argument("--dry-run", action="store_true", help=_tr("py.gui.help.dry_run"))
    a = ap.parse_args(argv)
    if a.shortcuts or a.remove_shortcuts:
        return gerer_raccourcis(a.shortcuts and not a.remove_shortcuts, a.shortcuts_folder, a.dry_run)
    try:
        import tkinter as tk
        from tkinter import filedialog, ttk
    except ImportError:
        print(_tr("py.gui.no_tk"))
        return 2
    trouves = [(nom, p) for nom, fichier in OUTILS for p in [trouver_outil(fichier)] if p is not None]
    if not trouves:
        print(_tr("py.gui.no_tool", OUTILS[0][1]))
        return 1
    f = fenetre(trouves, tk, ttk, filedialog, depart=a.tool)
    f.root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
