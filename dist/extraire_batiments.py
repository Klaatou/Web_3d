#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extraire_batiments.py : sort d'une région OpenSim (un OAR et son GLB fabriqué par oar2glb.py) un GLB par groupe d'objets (bâtiment, meuble, arbre...), recentré.

Ne modifie ni l'OAR ni le GLB : il écrit seulement dans le dossier de sortie et dans son cache (dossier courant). Importe glb2tiles.py et oar2glb.py,
cherchés dans le dossier de --tools, sinon de la variable WEB3D_TOOLS, sinon à côté de ce script. Tous les messages et l'aide : --lang fr|en|auto (python extraire_batiments.py --help).
"""
import argparse, hashlib, json, os, pickle, re, shutil, struct, sys
from pathlib import Path

# ---- langue des messages (v36) : textes intégrés par build.py (src/i18n/*.json, clés py.*) ; --lang fr|en|auto ou WEB3D_LANG ----
import json as _json, locale as _locale, os as _os, pathlib as _pl, sys as _sys

# fabrication (build.py) : la ligne suivante devient I18N_DATA = { "fr": {...}, "en": {...} }
I18N_DATA = _json.loads(r'''{"en":{"_name":"English","py.common.help":"show this help message and exit","py.common.lang_help":"language of the messages and of this help: fr, en or auto (default: the system's language; environment variable WEB3D_LANG is equivalent). Available: {0}","py.common.optionals":"options","py.common.positionals":"arguments","py.common.version_mark":"{0}, fingerprint {1}","py.common.version":"show the version and exit","py.extraire.err_outils":"ERROR: glb2tiles.py and oar2glb.py not found in {0}. Give their folder with --tools FOLDER (or the WEB3D_TOOLS variable), or keep this script next to them (dist or tools of the repository).","py.extraire.cache_illisible":"unreadable cache ({0}): {1}; it is rebuilt","py.extraire.cache_ecrit":"cache written: {0}","py.extraire.cache_non_ecrit":"cache not written ({0}): {1}","py.extraire.groupes_lus_cache":"groups: read from the cache","py.extraire.mesure_lue_cache":"GLB measurement: read from the cache","py.extraire.niv3":"same words","py.extraire.niv2":"name included","py.extraire.niv1":"common words","py.extraire.l_boite":" | BOX","py.extraire.l_nom_vide":" | empty name","py.extraire.l_aucun":" | neighbour: none (name within {0:g} m, position within {1:g} m)","py.extraire.l_par_nom":" | by NAME ({0})","py.extraire.l_par_position":" | by POSITION only","py.extraire.l_voisin":" | neighbour {0} {1} ({2} parts) at {3:.1f} m","py.extraire.l_autres":" (+{0} other(s) of the same rank)","py.extraire.ligne":"{0:5d} | {1:<50} | {2:5d} parts | {3:5d} nodes | pos ({4:.0f}, {5:.0f}, {6:.1f}) | scale ({7:g}, {8:g}, {9:g})","py.extraire.n_affiches":"{0} group(s) shown out of {1}","py.extraire.dont_boites":", including {0} box(es)","py.extraire.bilan_voisins":"boxes: {0} matched by name (same words {1}, name included {2}, common words {3}; {4} with several candidates of the same rank, the nearest is shown), {5} by position only ({6} with several neighbours), {7} without neighbour; {8} box(es) without a name (name radius {9:g} m, position radius {10:g} m, neighbours of at least {11} parts)","py.extraire.sans_nom":"unnamed","py.extraire.groupe_n":"group {0}","py.extraire.aucun_noeud":"[{0}] no GLB node matches this group: skipped","py.extraire.aucune_geometrie":"[{0}] no geometry: skipped","py.extraire.hierarchie":"[{0}] skipped: the root objects of the GLB contain {1} more nodes than the group (hierarchy different from the expected one)","py.extraire.ignore_erreur":"[{0}] skipped: {1}","py.extraire.sol_terrain":"OAR terrain under the middle of the building","py.extraire.sol_bas":"lowest point (no terrain in the OAR)","py.extraire.taille_ordre":"width x, depth y, height z (OpenSim)","py.extraire.ecrit":"[{0}] ({1}/{2}) {3}: {4} objects, {5} triangles, {6:.1f} MB","py.extraire.sans_geo":" ({0} node(s) without geometry)","py.extraire.sol_m":"; ground {0:.2f} m ({1})","py.extraire.fichiers_ecrits":"{0} file(s) written in {1}","py.extraire.cache_supprime":"cache deleted","py.extraire.err_oar_glb":"the OAR and the GLB are required","py.extraire.err_voisin":"--neighbor needs --list and --box (example: --list --box RAKis --neighbor)","py.extraire.err_rayon":"--radius must be positive","py.extraire.err_rayon_nom":"--name-radius must be positive","py.extraire.err_intervalle":"ERROR: reversed range: {0}","py.extraire.err_numero":"ERROR: unreadable group number: {0} (examples: 12, 12,15, 100-150)","py.extraire.err_inconnus":"ERROR: unknown group number(s): {0}","py.extraire.err_tous":"ERROR: --all without --min-parts would also take single-part groups (rails, signs, ...): add --min-parts N, or --yes to take everything","py.extraire.simule":"{0} group(s) would be extracted ({1} parts in total)","py.extraire.err_rien":"ERROR: nothing to extract (--group, --name or --all; --list to see the groups)","py.extraire.err_glb":"ERROR: {0}","py.extraire.desc":"extraire_batiments.py {0}: extracts from an OpenSim region (an OAR and its GLB made by oar2glb.py) one GLB per object group (building, furniture, tree...), re-centred. The name comes from the buildings of a large OAR, but the tool extracts any object group. It changes neither the OAR nor the GLB.","py.extraire.epilog":"Examples:\n  python extraire_batiments.py OAR GLB --list --filter REGEX --min-parts 5 --box RAKis\n  python extraire_batiments.py OAR GLB --list --box RAKis --neighbor\n  python extraire_batiments.py OAR GLB --group 12 --group 15,18,100-150 -o FOLDER --ground 5\n  python extraire_batiments.py OAR GLB --name \"Jewel Box House\"\n  python extraire_batiments.py OAR GLB --group 12 --group 15 --merge \"House and garage\"\n  python extraire_batiments.py OAR GLB --all --min-parts 5 --box RAKis --exclude \"Rail|Train\" --dry-run\n  (same line without --dry-run: extracts everything left)\n\nA group number is its rank in the OAR (it does not change while the OAR is the same). Each chosen group gives NNNN_name.glb and NNNN_name.json; with --merge, all chosen groups give ONE file named after the argument.\nThe GLB is re-centred: middle of the building at x = z = 0, ground at y = 0 (height of the OAR terrain under that middle, otherwise the lowest point). The .json next to it keeps the original OpenSim coordinates (x, y of the middle, ground altitude), the size and the groups.\n--ground MARGIN adds a flat slab (plain colour, 0.3 m thick, top at -2 cm) that sticks out of the building by MARGIN metres: a test ground you can walk on; the node is named \"sol d'essai\" (extras.essai) so it can be removed afterwards.\nCache: the first time, reading the OAR and measuring the GLB are slow; the result is kept in the extraire_batiments.cache folder, created in the current folder (where you run the command), and reused while the OAR, the GLB, glb2tiles.py and oar2glb.py have not changed (path, size, date). You can move this folder along with your command. --no-cache ignores it, --clear-cache deletes it. The cache files are pickles: do not take them from another source.\nglb2tiles.py and oar2glb.py: looked up in the folder given by --tools, otherwise by the WEB3D_TOOLS variable, otherwise next to this script.\nOld option names (French), still accepted: --rayon-nom (--name-radius), --parties-voisin (--neighbor-parts), --min-parties (--min-parts), --sans-cache (--no-cache), --vider-cache (--clear-cache), --filtre (--filter), --boite (--box), --voisin (--neighbor), --rayon (--radius), --groupe (--group), --nom (--name), --tous (--all), --exclure (--exclude), --limite (--limit), --simuler (--dry-run), --oui (--yes), --fusionner (--merge), --sol (--ground), --sortie (--output).","py.extraire.help.oar":"OpenSim region backup (.oar)","py.extraire.help.glb":"GLB made by oar2glb.py from this OAR","py.extraire.help.tools":"folder of glb2tiles.py and oar2glb.py (default: WEB3D_TOOLS variable, otherwise the folder of this script)","py.extraire.help.list":"lists the groups of the OAR","py.extraire.help.filtre":"with --list: keeps the groups whose root name matches (regular expression, case ignored)","py.extraire.help.min_parties":"minimum number of parts of a group (default 1)","py.extraire.help.boite":"marks (--list) or skips (--all) delivery boxes: 1.2 m cube whose name matches","py.extraire.help.voisin":"with --list and --box: for each box, the nearest neighbour group in x and y and how many others are in the radius; the name comes before the position: the box is matched to the group with the same building name (box name without the RAKis Freebies suffix), within --name-radius metres, otherwise the position alone; display only","py.extraire.help.rayon":"with --neighbor: maximum distance in metres, in x and y (default 25, estimate to be calibrated)","py.extraire.help.rayon_nom":"with --neighbor: maximum distance in metres for a neighbour of the same name (default 80, estimate to be calibrated)","py.extraire.help.parties_voisin":"with --neighbor: minimum number of parts of a neighbour group (default 5, estimate)","py.extraire.help.groupe":"group number(s) to extract: 12, 12,15 or a range 100-150 (repeatable)","py.extraire.help.nom":"extracts every group whose root name matches (regular expression)","py.extraire.help.tous":"extracts every group (with --min-parts, --box, --exclude, --limit)","py.extraire.help.exclure":"with --all: skips the groups whose name matches (repeatable)","py.extraire.help.limite":"with --all: takes only the first N","py.extraire.help.simuler":"with --all: only says how many groups would be extracted","py.extraire.help.oui":"with --all: also accepts to extract single-part groups","py.extraire.help.fusionner":"a single file, with this name, for all the chosen groups","py.extraire.help.sol":"adds a test ground that sticks out of the building by MARGIN metres","py.extraire.help.sortie":"output folder (default: batiments)","py.extraire.help.sans_cache":"neither reads nor writes the cache","py.extraire.help.vider_cache":"deletes the cache (extraire_batiments.cache folder of the current folder) then continues"},"fr":{"_name":"Français","py.common.help":"afficher ce message d'aide et quitter","py.common.lang_help":"langue des messages et de l'aide : fr, en ou auto (défaut : langue du système ; variable d'environnement WEB3D_LANG équivalente). Disponibles : {0}","py.common.optionals":"options","py.common.positionals":"arguments","py.common.version_mark":"{0}, empreinte {1}","py.common.version":"afficher la version et quitter","py.extraire.err_outils":"ERREUR : glb2tiles.py et oar2glb.py introuvables dans {0}. Indique leur dossier avec --tools DOSSIER (ou la variable WEB3D_TOOLS), ou range ce script à côté d'eux (dist ou tools du dépôt).","py.extraire.cache_illisible":"cache illisible ({0}) : {1} ; il est refait","py.extraire.cache_ecrit":"cache écrit : {0}","py.extraire.cache_non_ecrit":"cache non écrit ({0}) : {1}","py.extraire.groupes_lus_cache":"groupes : lus dans le cache","py.extraire.mesure_lue_cache":"mesure du GLB : lue dans le cache","py.extraire.niv3":"mêmes mots","py.extraire.niv2":"nom inclus","py.extraire.niv1":"mots communs","py.extraire.l_boite":" | BOÎTE","py.extraire.l_nom_vide":" | nom vide","py.extraire.l_aucun":" | voisin : aucun (nom à {0:g} m, position à {1:g} m)","py.extraire.l_par_nom":" | par NOM ({0})","py.extraire.l_par_position":" | par POSITION seule","py.extraire.l_voisin":" | voisin {0} {1} ({2} parties) à {3:.1f} m","py.extraire.l_autres":" (+{0} autre(s) de même rang)","py.extraire.ligne":"{0:5d} | {1:<50} | {2:5d} parties | {3:5d} nœuds | pos ({4:.0f}, {5:.0f}, {6:.1f}) | échelle ({7:g}, {8:g}, {9:g})","py.extraire.n_affiches":"{0} groupe(s) affiché(s) sur {1}","py.extraire.dont_boites":", dont {0} boîte(s)","py.extraire.bilan_voisins":"boîtes : {0} appariées par nom (mêmes mots {1}, nom inclus {2}, mots communs {3} ; {4} avec plusieurs candidats de même rang, le plus proche est affiché), {5} par position seule ({6} avec plusieurs voisins), {7} sans voisin ; {8} boîte(s) sans nom (rayon nom {9:g} m, rayon position {10:g} m, voisins de {11} parties au moins)","py.extraire.sans_nom":"sans_nom","py.extraire.groupe_n":"groupe {0}","py.extraire.aucun_noeud":"[{0}] aucun nœud du GLB ne correspond à ce groupe : ignoré","py.extraire.aucune_geometrie":"[{0}] aucune géométrie : ignoré","py.extraire.hierarchie":"[{0}] ignoré : les objets racine du GLB contiennent {1} nœuds de plus que le groupe (hiérarchie différente de celle attendue)","py.extraire.ignore_erreur":"[{0}] ignoré : {1}","py.extraire.sol_terrain":"terrain de l'OAR sous le milieu du bâtiment","py.extraire.sol_bas":"point le plus bas (pas de terrain dans l'OAR)","py.extraire.taille_ordre":"largeur x, profondeur y, hauteur z (OpenSim)","py.extraire.ecrit":"[{0}] ({1}/{2}) {3} : {4} objets, {5} triangles, {6:.1f} Mo","py.extraire.sans_geo":" ({0} nœud(s) sans géométrie)","py.extraire.sol_m":" ; sol {0:.2f} m ({1})","py.extraire.fichiers_ecrits":"{0} fichier(s) écrit(s) dans {1}","py.extraire.cache_supprime":"cache supprimé","py.extraire.err_oar_glb":"l'OAR et le GLB sont obligatoires","py.extraire.err_voisin":"--neighbor demande --list et --box (exemple : --list --box RAKis --neighbor)","py.extraire.err_rayon":"--radius doit être positif","py.extraire.err_rayon_nom":"--name-radius doit être positif","py.extraire.err_intervalle":"ERREUR : intervalle à l'envers : {0}","py.extraire.err_numero":"ERREUR : numéro de groupe illisible : {0} (exemples : 12, 12,15, 100-150)","py.extraire.err_inconnus":"ERREUR : numéro(s) de groupe inconnu(s) : {0}","py.extraire.err_tous":"ERREUR : --all sans --min-parts prendrait aussi les groupes d'une seule partie (rails, panneaux, ...) : ajoute --min-parts N, ou --yes pour tout prendre","py.extraire.simule":"{0} groupe(s) seraient extraits ({1} parties au total)","py.extraire.err_rien":"ERREUR : rien à extraire (--group, --name ou --all ; --list pour voir les groupes)","py.extraire.err_glb":"ERREUR : {0}","py.extraire.desc":"extraire_batiments.py {0} : sort d'une région OpenSim (un OAR et son GLB fabriqué par oar2glb.py) un GLB par groupe d'objets (bâtiment, meuble, arbre...), recentré. Le nom vient des bâtiments d'un gros OAR, mais l'outil extrait n'importe quel groupe d'objets. Ne modifie ni l'OAR ni le GLB.","py.extraire.epilog":"Exemples :\n  python extraire_batiments.py OAR GLB --list --filter REGEX --min-parts 5 --box RAKis\n  python extraire_batiments.py OAR GLB --list --box RAKis --neighbor\n  python extraire_batiments.py OAR GLB --group 12 --group 15,18,100-150 -o DOSSIER --ground 5\n  python extraire_batiments.py OAR GLB --name \"Jewel Box House\"\n  python extraire_batiments.py OAR GLB --group 12 --group 15 --merge \"Maison et garage\"\n  python extraire_batiments.py OAR GLB --all --min-parts 5 --box RAKis --exclude \"Rail|Train\" --dry-run\n  (même ligne sans --dry-run : extrait tout ce qui reste)\n\nLe numéro d'un groupe est son rang dans l'OAR (il ne change pas tant que l'OAR est le même). Chaque groupe choisi donne NNNN_nom.glb et NNNN_nom.json ; avec --merge, tous les groupes choisis donnent UN fichier nommé d'après l'argument.\nLe GLB est recentré : milieu du bâtiment en x et z à 0, sol à y = 0 (hauteur du terrain de l'OAR sous ce milieu, sinon le point le plus bas). Le .json voisin garde les coordonnées d'origine OpenSim (x, y du milieu, altitude du sol), la taille et les groupes.\n--ground MARGIN ajoute une dalle plane (couleur unie, 0,3 m d'épaisseur, dessus à -2 cm) qui dépasse du bâtiment de MARGIN mètres : sol d'essai, on peut marcher dessus ; le nœud s'appelle « sol d'essai » (extras.essai) pour le retirer ensuite.\nCache : la première fois, la lecture de l'OAR et la mesure du GLB sont longues ; leur résultat est gardé dans le dossier extraire_batiments.cache, créé dans le dossier courant (là où tu lances la commande), et réutilisé tant que l'OAR, le GLB, glb2tiles.py et oar2glb.py n'ont pas changé (chemin, taille, date). Tu peux déplacer ce dossier avec ta commande. --no-cache l'ignore, --clear-cache le supprime. Les fichiers du cache sont des « pickle » : ne les récupère pas d'une autre source.\nglb2tiles.py et oar2glb.py : cherchés dans le dossier de --tools, sinon de la variable WEB3D_TOOLS, sinon à côté de ce script.\nAnciens noms des options (français), toujours acceptés : --rayon-nom (--name-radius), --parties-voisin (--neighbor-parts), --min-parties (--min-parts), --sans-cache (--no-cache), --vider-cache (--clear-cache), --filtre (--filter), --boite (--box), --voisin (--neighbor), --rayon (--radius), --groupe (--group), --nom (--name), --tous (--all), --exclure (--exclude), --limite (--limit), --simuler (--dry-run), --oui (--yes), --fusionner (--merge), --sol (--ground), --sortie (--output).","py.extraire.help.oar":"sauvegarde de région OpenSim (.oar)","py.extraire.help.glb":"GLB fabriqué par oar2glb.py à partir de cet OAR","py.extraire.help.tools":"dossier de glb2tiles.py et oar2glb.py (défaut : variable WEB3D_TOOLS, sinon le dossier de ce script)","py.extraire.help.list":"liste les groupes de l'OAR","py.extraire.help.filtre":"avec --list : garde les groupes dont le nom racine correspond (expression régulière, casse ignorée)","py.extraire.help.min_parties":"nombre minimal de parties d'un groupe (défaut 1)","py.extraire.help.boite":"marque (--list) ou saute (--all) les boîtes de livraison : cube de 1,2 m dont le nom correspond","py.extraire.help.voisin":"avec --list et --box : pour chaque boîte, le groupe voisin le plus proche en x et y et combien d'autres sont dans le rayon ; le nom passe avant la position : la boîte est appariée au groupe qui porte le même nom de bâtiment (nom de la boîte sans le suffixe RAKis Freebies), à moins de --name-radius mètres, sinon la position seule ; affichage seulement","py.extraire.help.rayon":"avec --neighbor : distance maximale en mètres, en x et y (défaut 25, estimation à calibrer)","py.extraire.help.rayon_nom":"avec --neighbor : distance maximale en mètres pour un voisin de même nom (défaut 80, estimation à calibrer)","py.extraire.help.parties_voisin":"avec --neighbor : nombre minimal de parties d'un groupe voisin (défaut 5, estimation)","py.extraire.help.groupe":"numéro(s) de groupe à extraire : 12, 12,15 ou un intervalle 100-150 (répétable)","py.extraire.help.nom":"extrait tous les groupes dont le nom racine correspond (expression régulière)","py.extraire.help.tous":"extrait tous les groupes (avec --min-parts, --box, --exclude, --limit)","py.extraire.help.exclure":"avec --all : saute les groupes dont le nom correspond (répétable)","py.extraire.help.limite":"avec --all : ne prend que les N premiers","py.extraire.help.simuler":"avec --all : dit seulement combien de groupes seraient extraits","py.extraire.help.oui":"avec --all : accepte d'extraire aussi les groupes d'une seule partie","py.extraire.help.fusionner":"un seul fichier, de ce nom, pour tous les groupes choisis","py.extraire.help.sol":"ajoute un sol d'essai qui dépasse du bâtiment de MARGIN mètres","py.extraire.help.sortie":"dossier de sortie (défaut : batiments)","py.extraire.help.sans_cache":"ne lit ni n'écrit le cache","py.extraire.help.vider_cache":"supprime le cache (dossier extraire_batiments.cache du dossier courant) puis continue"}}''')


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


VERSION = "1.6.3 (06/11/2026)"      # remplacé par build.py (fichier VERSION) dans dist/extraire_batiments.py
MARK = "39cec2f4"      # empreinte du fichier fabriqué, inscrite par build.py ; reste telle quelle depuis tools/

ICI = Path(__file__).resolve().parent
NOM_CACHE = "extraire_batiments.cache"
FORMAT_CACHE = 1
DOSSIER_OUTILS = None          # dossier de glb2tiles.py et oar2glb.py, fixé par charger_outils()
oar2glb = glb2tiles = None     # modules importés par charger_outils() (après la lecture des options : --help marche sans eux)

for _s in (sys.stdout, sys.stderr):      # noms d'objets hors de la page de code de la console : remplacés au lieu de faire planter
    try:
        _s.reconfigure(errors="replace")
    except Exception:
        pass


def version_tag():
    return VERSION if MARK.startswith("__") else _tr("py.common.version_mark", VERSION, MARK)


def charger_outils(choix=None):
    """importe glb2tiles.py et oar2glb.py : dossier donné par --tools, sinon variable WEB3D_TOOLS, sinon dossier de ce script"""
    global DOSSIER_OUTILS, oar2glb, glb2tiles
    d = Path(choix or os.environ.get("WEB3D_TOOLS") or ICI).expanduser()
    if not ((d / "glb2tiles.py").is_file() and (d / "oar2glb.py").is_file()):
        sys.exit(_tr("py.extraire.err_outils", d))
    sys.path.insert(0, str(d.resolve()))
    DOSSIER_OUTILS = d.resolve()
    import oar2glb as _o, glb2tiles as _g
    oar2glb, glb2tiles = _o, _g


def dossier_cache():
    """le cache est dans le dossier courant (là où la commande est lancée), jamais à côté du script : dist\\ est suivi par git"""
    return Path.cwd() / NOM_CACHE


def cle_cache(oar, glb_chemin):
    h = hashlib.sha1(str(FORMAT_CACHE).encode())
    for p in (Path(oar), Path(glb_chemin), DOSSIER_OUTILS / "glb2tiles.py", DOSSIER_OUTILS / "oar2glb.py"):
        st = p.stat()
        h.update(f"|{p.resolve()}|{st.st_size}|{st.st_mtime_ns}".encode("utf-8", "replace"))
    return h.hexdigest()[:20]


def lire_cache(nom):
    f = dossier_cache() / nom
    if not f.exists():
        return None
    try:
        with open(f, "rb") as fh:
            return pickle.load(fh)
    except Exception as e:
        print(_tr("py.extraire.cache_illisible", nom, e))
        return None


def ecrire_cache(nom, obj):
    try:
        dc = dossier_cache()
        dc.mkdir(exist_ok=True)
        tmp = dc / (nom + ".tmp")
        with open(tmp, "wb") as fh:
            pickle.dump(obj, fh, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, dc / nom)
        print(_tr("py.extraire.cache_ecrit", dc / nom))
    except Exception as e:
        print(_tr("py.extraire.cache_non_ecrit", nom, e))


def charger(oar, glb_chemin, cache):
    """(terrain, glb, groupes) ; la lecture de l'OAR et la correspondance avec le GLB sont gardées en cache"""
    glb = glb2tiles.Glb(glb_chemin)
    nom = cle_cache(oar, glb_chemin) + ".groupes.pkl"
    d = lire_cache(nom) if cache else None
    if d is not None:
        print(_tr("py.extraire.groupes_lus_cache"))
        return d["terrain"], glb, d["groupes"]
    scan = oar2glb.oar_scan(Path(oar))
    corr = oar2glb.match_nodes(glb.g, scan)
    groupes = []
    for i, grp in enumerate(scan["groups"], 1):
        parts = grp["parts"]
        racine = parts[0]
        noeuds = sorted({corr[p["uuid"]][0] for p in parts if p["uuid"] in corr})
        groupes.append({"n": i, "nom": racine["name"] or "", "parties": len(parts), "noeuds": noeuds,
                        "pos": racine["gpos"], "echelle": racine["scale"]})
    terrain = scan.get("terrain")
    if cache:
        ecrire_cache(nom, {"terrain": terrain, "groupes": groupes})
    return terrain, glb, groupes


def charger_plan(glb, glb_chemin, oar, cache):
    nom = cle_cache(oar, glb_chemin) + ".plan.pkl"
    plan = lire_cache(nom) if cache else None
    if plan is not None:
        plan.glb = glb
        print(_tr("py.extraire.mesure_lue_cache"))
        return plan
    plan = glb2tiles.Plan(glb, glb2tiles.Params(references=False))
    if cache:
        plan.glb = None                    # le fichier ouvert ne se garde pas
        try:
            ecrire_cache(nom, plan)
        finally:
            plan.glb = glb
    return plan


def est_boite(gr, rx):
    return bool(rx) and all(abs(s - 1.2) < 0.01 for s in gr["echelle"]) and bool(rx.search(gr["nom"]))


RX_SUFFIXE = re.compile(r"\s*-?\s*RAKis\s+Freebies.*$", re.IGNORECASE)
PARTIES_NOM_MIN = 1      # un groupe de meme nom doit avoir au moins 1 partie : les batiments de decor sont des meshes uniques


def mots_nom(texte):
    """mots du nom d'un batiment : sans le suffixe de boite (RAKis Freebies ...), sans accents, en minuscules"""
    import unicodedata
    t = unicodedata.normalize("NFKD", RX_SUFFIXE.sub("", texte or ""))
    t = "".join(c for c in t if not unicodedata.combining(c)).casefold()
    return re.findall(r"[^\W_]+", t, flags=re.UNICODE)


def score_nom(mb, mg):
    """3 = memes mots ; 2 = l'un des noms contient la suite de mots de l'autre (2 mots au moins, ou 4 lettres au moins) ;
    1 = au moins 2 mots communs et la moitie des mots ; 0 = rien"""
    if not mb or not mg:
        return 0
    if mb == mg:
        return 3
    court, long_ = (mb, mg) if len(mb) <= len(mg) else (mg, mb)
    n = len(court)
    if any(long_[i:i + n] == court for i in range(len(long_) - n + 1)) and (n >= 2 or (len(court[0]) >= 4 and court is mb)):
        return 2
    eb, eg = set(mb), set(mg)
    comm = eb & eg
    if any(any(c.isdigit() for c in w) for w in eb ^ eg):
        return 0                 # variantes numerotees (Shop 03 / Shop 04) : batiments differents
    if len(comm) >= 2 and len(comm) * 2 >= len(eb | eg):
        return 1
    return 0


def voisins(groupes, a, rb):
    """pour chaque boite (numero du groupe) : le groupe qui est probablement son batiment, ou None.
    1) par NOM : groupes non boite d'au moins PARTIES_NOM_MIN parties dont le nom de batiment (suffixe retire) a le meme nom
       (niveau 3), contient ou est contenu (niveau 2) a moins de a.rayon_nom metres, ou partage des mots (niveau 1) a moins de a.rayon ;
       on garde le meilleur niveau, puis le plus proche ;
    2) sinon par POSITION : le groupe d'au moins a.parties_voisin parties le plus proche a moins de a.rayon (x et y).
    Resultat par boite : {mode: nom|position, niveau, d, g, autres} ; autres = candidats de meme rang qui restent (ambigu si > 0).
    Decision sur le nom, la position et le nombre de parties, jamais sur l'etendue d'un mesh"""
    cand = [g for g in groupes if not est_boite(g, rb)]
    mots = {g["n"]: mots_nom(g["nom"]) for g in cand}
    res = {}
    for b in groupes:
        if not est_boite(b, rb):
            continue
        bx, by = b["pos"][0], b["pos"][1]
        mb = mots_nom(b["nom"])
        noms, pos = [], []
        for g in cand:
            d = ((g["pos"][0] - bx) ** 2 + (g["pos"][1] - by) ** 2) ** 0.5
            if mb and g["parties"] >= PARTIES_NOM_MIN:
                s = score_nom(mb, mots[g["n"]])
                if (s >= 2 and d <= a.rayon_nom) or (s == 1 and d <= a.rayon):
                    noms.append((-s, d, g["n"], g))
            if g["parties"] >= a.parties_voisin and d <= a.rayon:
                pos.append((d, g["n"], g))
        if noms:
            noms.sort(key=lambda t: t[:3])
            s, d, _, g = noms[0]
            res[b["n"]] = {"mode": "nom", "niveau": -s, "d": d, "g": g, "autres": sum(1 for t in noms[1:] if t[0] == s)}
        elif pos:
            pos.sort(key=lambda t: t[:2])
            d, _, g = pos[0]
            res[b["n"]] = {"mode": "position", "niveau": 0, "d": d, "g": g, "autres": len(pos) - 1}
        else:
            res[b["n"]] = None
    return res


def lister(groupes, a):
    rx = re.compile(a.filtre, re.IGNORECASE) if a.filtre else None
    rb = re.compile(a.boite, re.IGNORECASE) if a.boite else None
    vois = voisins(groupes, a, rb) if a.voisin else {}
    LIB = {3: _tr("py.extraire.niv3"), 2: _tr("py.extraire.niv2"), 1: _tr("py.extraire.niv1")}
    n = nb = sans = sans_nom = amb_nom = amb_pos = 0
    niv = {3: 0, 2: 0, 1: 0}
    par_pos = 0
    for gr in groupes:
        if gr["parties"] < a.min_parties or (rx and not rx.search(gr["nom"])):
            continue
        p, e = gr["pos"], gr["echelle"]
        boite = est_boite(gr, rb)
        nb += boite
        n += 1
        fin = ""
        if boite:
            fin = _tr("py.extraire.l_boite")
            if a.voisin:
                v = vois.get(gr["n"])
                if not mots_nom(gr["nom"]):
                    sans_nom += 1
                    fin += _tr("py.extraire.l_nom_vide")
                if v is None:
                    sans += 1
                    fin += _tr("py.extraire.l_aucun", a.rayon_nom, a.rayon)
                else:
                    g = v["g"]
                    if v["mode"] == "nom":
                        niv[v["niveau"]] += 1
                        amb_nom += v["autres"] > 0
                        fin += _tr("py.extraire.l_par_nom", LIB[v["niveau"]])
                    else:
                        par_pos += 1
                        amb_pos += v["autres"] > 0
                        fin += _tr("py.extraire.l_par_position")
                    fin += _tr("py.extraire.l_voisin", g["n"], g["nom"][:40], g["parties"], v["d"]) + (_tr("py.extraire.l_autres", v["autres"]) if v["autres"] else "")
        print(_tr("py.extraire.ligne", gr["n"], gr["nom"][:50], gr["parties"], len(gr["noeuds"]), p[0], p[1], p[2], e[0], e[1], e[2]) + fin)
    print(_tr("py.extraire.n_affiches", n, len(groupes)) + (_tr("py.extraire.dont_boites", nb) if rb else ""))
    if a.voisin:
        npar = sum(niv.values())
        print(_tr("py.extraire.bilan_voisins", npar, niv[3], niv[2], niv[1], amb_nom, par_pos, amb_pos, sans, sans_nom, a.rayon_nom, a.rayon, a.parties_voisin))


def nom_fichier(texte):
    return re.sub(r"[^\w.\-]+", "_", texte, flags=re.UNICODE).strip("_")[:60] or _tr("py.extraire.sans_nom")


def boite_sol(demi_x, demi_z, y_haut=-0.02, epaisseur=0.3):
    """24 sommets, normales, 36 indices d'une dalle centree sur x = z = 0"""
    lo, hi = (-demi_x, y_haut - epaisseur, -demi_z), (demi_x, y_haut, demi_z)
    c = lambda i, j, k: (hi[0] if i else lo[0], hi[1] if j else lo[1], hi[2] if k else lo[2])
    faces = [((0, 1, 0), [c(0, 1, 0), c(0, 1, 1), c(1, 1, 1), c(1, 1, 0)]), ((0, -1, 0), [c(0, 0, 0), c(1, 0, 0), c(1, 0, 1), c(0, 0, 1)]),
             ((1, 0, 0), [c(1, 0, 0), c(1, 1, 0), c(1, 1, 1), c(1, 0, 1)]), ((-1, 0, 0), [c(0, 0, 0), c(0, 0, 1), c(0, 1, 1), c(0, 1, 0)]),
             ((0, 0, 1), [c(0, 0, 1), c(1, 0, 1), c(1, 1, 1), c(0, 1, 1)]), ((0, 0, -1), [c(0, 0, 0), c(0, 1, 0), c(1, 1, 0), c(1, 0, 0)])]
    verts, norm, idx = [], [], []
    for n, cs in faces:
        u = [cs[1][k] - cs[0][k] for k in range(3)]
        v = [cs[2][k] - cs[0][k] for k in range(3)]
        cr = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        if sum(cr[k] * n[k] for k in range(3)) < 0:
            cs = cs[::-1]
        b = len(verts)
        verts += cs
        norm += [n] * 4
        idx += [b, b + 1, b + 2, b, b + 2, b + 3]
    return verts, norm, idx, lo, hi


def finaliser(chemin, nom, t, dalle=None):
    """ajoute un nœud parent (nom, translation t) au-dessus des nœuds de la scène ; avec dalle = (demi_x, demi_z), ajoute le sol d'essai ;
    le GLB est lu et reecrit en une fois"""
    d = Path(chemin).read_bytes()
    ln, _ = struct.unpack_from("<I4s", d, 12)
    js = json.loads(d[20:20 + ln].decode("utf-8"))
    binlen = struct.unpack_from("<I", d, 20 + ln)[0]
    data = bytearray(d[28 + ln:28 + ln + binlen])
    racines = js["scenes"][0]["nodes"]
    js["nodes"].append({"name": nom, "translation": [round(v, 4) for v in t], "children": racines})
    js["scenes"][0]["nodes"] = [len(js["nodes"]) - 1]
    if dalle:
        verts, norm, idx, lo, hi = boite_sol(*dalle)
        def vue(octets, cible):
            while len(data) % 4:
                data.append(0)
            js.setdefault("bufferViews", []).append({"buffer": 0, "byteOffset": len(data), "byteLength": len(octets), "target": cible})
            data.extend(octets)
            return len(js["bufferViews"]) - 1
        def acc(v, comp, n, typ, mn=None, mx=None):
            a = {"bufferView": v, "componentType": comp, "count": n, "type": typ}
            if mn is not None:
                a["min"], a["max"] = mn, mx
            js.setdefault("accessors", []).append(a)
            return len(js["accessors"]) - 1
        ap = acc(vue(b"".join(struct.pack("<3f", *p) for p in verts), 34962), 5126, len(verts), "VEC3", list(lo), list(hi))
        an = acc(vue(b"".join(struct.pack("<3f", *p) for p in norm), 34962), 5126, len(norm), "VEC3")
        ai = acc(vue(struct.pack("<%dH" % len(idx), *idx), 34963), 5123, len(idx), "SCALAR")
        js.setdefault("materials", []).append({"name": "sol d'essai", "pbrMetallicRoughness": {"baseColorFactor": [0.36, 0.46, 0.30, 1.0],
                                                                                          "metallicFactor": 0.0, "roughnessFactor": 1.0}})
        js.setdefault("meshes", []).append({"name": "sol d'essai", "primitives": [{"attributes": {"POSITION": ap, "NORMAL": an}, "indices": ai,
                                                                                    "material": len(js["materials"]) - 1}]})
        js["nodes"].append({"name": "sol d'essai", "mesh": len(js["meshes"]) - 1, "extras": {"essai": True}})
        js["scenes"][0]["nodes"].append(len(js["nodes"]) - 1)
    while len(data) % 4:
        data.append(0)
    js["buffers"] = [{"byteLength": len(data)}]
    jb = json.dumps(js, separators=(",", ":")).encode("utf-8")
    jb += b" " * (-len(jb) % 4)
    total = 12 + 8 + len(jb) + 8 + len(data)
    Path(chemin).write_bytes(struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<II", len(jb), 0x4E4F534A) + jb
                             + struct.pack("<II", len(data), 0x004E4942) + bytes(data))


def extraire(plan, terrain, ensembles, sortie, marge_sol):
    sortie.mkdir(parents=True, exist_ok=True)
    rac_de = {}
    for r in plan.racines:
        for n in r.nodes:
            rac_de[n] = r
    faits = 0
    for k, (base, nom, grs) in enumerate(ensembles, 1):
        noeuds = set()
        for gr in grs:
            noeuds.update(gr["noeuds"])
        if not noeuds:
            print(_tr("py.extraire.aucun_noeud", base))
            continue
        racs, sans_geo = [], 0
        for n in sorted(noeuds):
            r = rac_de.get(n)
            if r is None:
                sans_geo += 1
            elif not r.terrain and r not in racs:
                racs.append(r)
        if not racs:
            print(_tr("py.extraire.aucune_geometrie", base))
            continue
        en_trop = sum(len(r.nodes) for r in racs) - len(noeuds)
        if en_trop > 50 + 3 * len(noeuds):
            print(_tr("py.extraire.hierarchie", base, en_trop))
            continue
        ids = {id(r) for r in racs}
        units = [u for u in plan.unites if id(u.racine) in ids and (u.entier or u.node in noeuds)]
        chemin = sortie / (base + ".glb")
        try:
            fiche = glb2tiles.ecrire_tuile(plan, glb2tiles.Tuile(0, 0, 0, units), chemin)
        except glb2tiles.ErreurGlb as e:
            print(_tr("py.extraire.ignore_erreur", base, e))
            continue
        lo, hi = fiche["min"], fiche["max"]
        cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
        sol = oar2glb.terrain_height(terrain, cx, -cz)
        source = _tr("py.extraire.sol_terrain")
        if sol is None:
            sol, source = lo[1], _tr("py.extraire.sol_bas")
        dalle = ((hi[0] - lo[0]) / 2 + marge_sol, (hi[2] - lo[2]) / 2 + marge_sol) if marge_sol else None
        finaliser(chemin, nom, (-cx, -sol, -cz), dalle)
        info = {"nom": nom, "groupes": [g["n"] for g in grs], "noeuds": len(noeuds), "triangles": fiche["triangles"],
                "origine_opensim": {"x": round(cx, 3), "y": round(-cz, 3), "sol": round(sol, 3)}, "sol_source": source,
                "taille": [round(hi[0] - lo[0], 2), round(hi[2] - lo[2], 2), round(hi[1] - lo[1], 2)],
                "taille_ordre": _tr("py.extraire.taille_ordre"), "sol_d_essai_marge_m": marge_sol or None}
        Path(chemin).with_suffix(".json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
        faits += 1
        print(_tr("py.extraire.ecrit", base, k, len(ensembles), chemin, fiche["instances"], fiche["triangles"], fiche["bytes"] / 1048576)
              + (_tr("py.extraire.sans_geo", sans_geo) if sans_geo else "") + _tr("py.extraire.sol_m", sol, source))
    print(_tr("py.extraire.fichiers_ecrits", faits, sortie))


# noms d'options français d'origine -> noms actuels (anglais) ; les anciens restent acceptés, jamais de rupture pour les commandes déjà écrites
OLD_OPTIONS = {"--rayon-nom": "--name-radius", "--parties-voisin": "--neighbor-parts", "--min-parties": "--min-parts", "--sans-cache": "--no-cache", "--vider-cache": "--clear-cache", "--filtre": "--filter", "--boite": "--box", "--voisin": "--neighbor", "--rayon": "--radius", "--groupe": "--group", "--nom": "--name", "--tous": "--all", "--exclure": "--exclude", "--limite": "--limit", "--simuler": "--dry-run", "--oui": "--yes", "--fusionner": "--merge", "--sol": "--ground", "--sortie": "--output"}


def anciens_noms(argv):
    """les noms français des options (avant leur passage en anglais) restent acceptés : --groupe 12 marche comme --group 12 (aussi --groupe=12)"""
    out = []
    for x in argv:
        k, eq, v = str(x).partition("=")
        out.append(OLD_OPTIONS.get(k, k) + eq + v if k.startswith("--") else x)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=_tr("py.extraire.desc", version_tag()), epilog=_tr("py.extraire.epilog"),
                                 formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False)
    i18n_add_common(ap)
    ap.add_argument("--version", action="version", version=f"extraire_batiments {version_tag()}", help=_tr("py.common.version"))
    ap.add_argument("oar", nargs="?", help=_tr("py.extraire.help.oar"))
    ap.add_argument("glb", nargs="?", help=_tr("py.extraire.help.glb"))
    ap.add_argument("--tools", metavar="FOLDER", help=_tr("py.extraire.help.tools"))
    ap.add_argument("--list", action="store_true", help=_tr("py.extraire.help.list"))
    ap.add_argument("--filter", dest="filtre", help=_tr("py.extraire.help.filtre"))
    ap.add_argument("--min-parts", dest="min_parties", type=int, default=1, help=_tr("py.extraire.help.min_parties"))
    ap.add_argument("--box", dest="boite", help=_tr("py.extraire.help.boite"))
    ap.add_argument("--neighbor", dest="voisin", action="store_true", help=_tr("py.extraire.help.voisin"))
    ap.add_argument("--radius", dest="rayon", type=float, default=25.0, help=_tr("py.extraire.help.rayon"))
    ap.add_argument("--name-radius", dest="rayon_nom", type=float, default=80.0, help=_tr("py.extraire.help.rayon_nom"))
    ap.add_argument("--neighbor-parts", dest="parties_voisin", type=int, default=5, help=_tr("py.extraire.help.parties_voisin"))
    ap.add_argument("--group", dest="groupe", action="append", default=[], help=_tr("py.extraire.help.groupe"))
    ap.add_argument("--name", dest="nom", help=_tr("py.extraire.help.nom"))
    ap.add_argument("--all", dest="tous", action="store_true", help=_tr("py.extraire.help.tous"))
    ap.add_argument("--exclude", dest="exclure", action="append", default=[], help=_tr("py.extraire.help.exclure"))
    ap.add_argument("--limit", dest="limite", type=int, help=_tr("py.extraire.help.limite"))
    ap.add_argument("--dry-run", dest="simuler", action="store_true", help=_tr("py.extraire.help.simuler"))
    ap.add_argument("--yes", dest="oui", action="store_true", help=_tr("py.extraire.help.oui"))
    ap.add_argument("--merge", dest="fusionner", help=_tr("py.extraire.help.fusionner"))
    ap.add_argument("--ground", dest="sol", type=float, metavar="MARGIN", help=_tr("py.extraire.help.sol"))
    ap.add_argument("-o", "--output", dest="sortie", default="batiments", help=_tr("py.extraire.help.sortie"))
    ap.add_argument("--no-cache", dest="sans_cache", action="store_true", help=_tr("py.extraire.help.sans_cache"))
    ap.add_argument("--clear-cache", dest="vider_cache", action="store_true", help=_tr("py.extraire.help.vider_cache"))
    a = ap.parse_args(anciens_noms(sys.argv[1:] if argv is None else argv))
    if a.vider_cache and dossier_cache().exists():
        shutil.rmtree(dossier_cache())
        print(_tr("py.extraire.cache_supprime"))
        if not a.oar:
            return 0
    if not (a.oar and a.glb):
        ap.error(_tr("py.extraire.err_oar_glb"))
    cache = not a.sans_cache
    if a.voisin and not (a.list and a.boite):
        ap.error(_tr("py.extraire.err_voisin"))
    if a.rayon <= 0:
        ap.error(_tr("py.extraire.err_rayon"))
    if a.rayon_nom <= 0:
        ap.error(_tr("py.extraire.err_rayon_nom"))
    charger_outils(a.tools)
    try:
        terrain, glb, groupes = charger(a.oar, a.glb, cache)
        if a.list:
            lister(groupes, a)
            return 0
        nums = []
        for t in a.groupe:
            for s in re.split(r"[,; ]+", t):
                m = re.fullmatch(r"(\d+)-(\d+)", s)
                if m:
                    if int(m[2]) < int(m[1]):
                        sys.exit(_tr("py.extraire.err_intervalle", s))
                    nums += range(int(m[1]), int(m[2]) + 1)
                elif s:
                    if not s.isdigit():
                        sys.exit(_tr("py.extraire.err_numero", s))
                    nums.append(int(s))
        inconnus = set(nums) - {g["n"] for g in groupes}
        if inconnus:
            sys.exit(_tr("py.extraire.err_inconnus", ", ".join(str(n) for n in sorted(inconnus))))
        choisis = [g for g in groupes if g["n"] in nums]
        if a.nom:
            rx = re.compile(a.nom, re.IGNORECASE)
            choisis += [g for g in groupes if rx.search(g["nom"]) and g not in choisis]
        if a.tous:
            if a.min_parties < 2 and not a.oui:
                sys.exit(_tr("py.extraire.err_tous"))
            rb = re.compile(a.boite, re.IGNORECASE) if a.boite else None
            ex = [re.compile(x, re.IGNORECASE) for x in a.exclure]
            tous = [g for g in groupes if g["parties"] >= a.min_parties and not est_boite(g, rb) and not any(r.search(g["nom"]) for r in ex)
                    and g["noeuds"] and g not in choisis]
            choisis += tous[:a.limite] if a.limite else tous
            if a.simuler:
                print(_tr("py.extraire.simule", len(choisis), sum(g["parties"] for g in choisis)))
                return 0
        if not choisis:
            sys.exit(_tr("py.extraire.err_rien"))
        plan = charger_plan(glb, a.glb, a.oar, cache)
        if a.fusionner:
            ensembles = [(nom_fichier(a.fusionner), a.fusionner, choisis)]
        else:
            ensembles = [(f"{g['n']:04d}_{nom_fichier(g['nom'])}", g["nom"] or _tr("py.extraire.groupe_n", g["n"]), [g]) for g in choisis]
        extraire(plan, terrain, ensembles, Path(a.sortie), a.sol)
        return 0
    except glb2tiles.ErreurGlb as e:
        sys.exit(_tr("py.extraire.err_glb", e))


if __name__ == "__main__":
    sys.exit(main())
