#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iar2oar.py : transforme une archive d'inventaire OpenSim (IAR) en OAR minimal, pour la chaîne habituelle (oar2glb.py, puis extraire_batiments.py).

Ne modifie jamais l'IAR : il écrit seulement l'OAR de sortie. N'importe rien de glb2tiles.py ni d'oar2glb.py. Tous les messages et l'aide : --lang fr|en|auto
(python iar2oar.py --help).
"""
import argparse, io, math, re, sys, tarfile, time
import xml.etree.ElementTree as ET

# ---- langue des messages (v36) : textes intégrés par build.py (src/i18n/*.json, clés py.*) ; --lang fr|en|auto ou WEB3D_LANG ----
import json as _json, locale as _locale, os as _os, pathlib as _pl, sys as _sys

# fabrication (build.py) : la ligne suivante devient I18N_DATA = { "fr": {...}, "en": {...} }
I18N_DATA = _json.loads(r'''{"en":{"_name":"English","py.common.help":"show this help message and exit","py.common.lang_help":"language of the messages and of this help: fr, en or auto (default: the system's language; environment variable WEB3D_LANG is equivalent). Available: {0}","py.common.optionals":"options","py.common.positionals":"arguments","py.common.version_mark":"{0}, fingerprint {1}","py.common.version":"show the version and exit","py.iar2oar.element_illisible":"unreadable item: {0} ({1})","py.iar2oar.objet_illisible":"unreadable object: {0} ({1})","py.iar2oar.sans_nom":"unnamed","py.iar2oar.err_iar":"ERROR: unreadable IAR: {0}","py.iar2oar.err_vide":"ERROR: no object in the inventory of this IAR (inventory/ folder missing or empty)","py.iar2oar.err_rien":"ERROR: nothing to convert (filter too strict, or the object assets are missing from the IAR)","py.iar2oar.ligne":"{0:4d} | {1:<60} | {2:4d} group(s) | {3:5d} parts | {4:5d} meshes","py.iar2oar.l_combine":" | coalesced","py.iar2oar.l_imbrique":" | nested level {0}","py.iar2oar.bilan":"{0} object(s), {1} group(s), {2} part(s); region of {3} m x {3} m","py.iar2oar.manquants":"{0} item(s) without an object asset in the IAR (ignored): {1}","py.iar2oar.ecrit":"OAR written: {0} ({1} groups, {2} assets copied)","py.iar2oar.desc":"iar2oar.py {0}: turns an OpenSim inventory archive (IAR) into a minimal OAR, for the usual chain (oar2glb.py, then extraire_batiments.py). Never changes the IAR: only writes the output OAR.","py.iar2oar.epilog":"Examples:\n  python iar2oar.py MY.iar --list --filter REGEX\n  python iar2oar.py MY.iar -o inventory.oar --filter REGEX --no-nested --margin 4\n\nThen, as for a region:\n  python oar2glb.py inventory.oar            (makes the GLB with convoar)\n  python extraire_batiments.py inventory.oar inventory.glb --list\n  python extraire_batiments.py inventory.oar inventory.glb --group 12 -o buildings\n\nWhat the script does:\n- each inventory object (object.xml asset) becomes one or more groups of the OAR; the group name is the inventory item name (the root of the object is renamed), so that --name and --filter work;\n- a coalesced object (CoalescedObject) is split into its groups, which keep their relative layout (offsetx/y/z offsets);\n- objects held in the contents of another one (boxes: TaskInventory) are added too, up to 3 levels, once each (--no-nested ignores them); their name is \"parent / name\";\n- the original positions overlap: each group (or each coalesced object) gets a cell on a grid, without terrain (the ground of an extract is then its lowest point); the region size (archive.xml) grows by steps of 256 m when needed;\n- the null byte that ends the XML files of the IAR is removed;\n- only the assets useful for 3D are copied: meshes, textures, materials.\nESTIMATE: the extent of a group for its cell is computed from the positions and scales of the parts, without rotations.\nNOT TESTED: convoar on the produced OAR; attachments and clothing are not supported (no avatar).\nOld option names (French), still accepted: --liste (--list), --filtre (--filter), --sans-imbriques (--no-nested), --marge (--margin), --sortie (--output).","py.iar2oar.help.iar":"OpenSim inventory archive (.iar)","py.iar2oar.help.output":"OAR to write (default: inventaire.oar)","py.iar2oar.help.list":"lists the objects found, writes nothing","py.iar2oar.help.filter":"keeps the inventory items whose name matches (regular expression, case ignored)","py.iar2oar.help.no_nested":"ignores the objects held inside others (boxes)","py.iar2oar.help.margin":"space between two grid cells, in metres (default 4)"},"fr":{"_name":"Français","py.common.help":"afficher ce message d'aide et quitter","py.common.lang_help":"langue des messages et de l'aide : fr, en ou auto (défaut : langue du système ; variable d'environnement WEB3D_LANG équivalente). Disponibles : {0}","py.common.optionals":"options","py.common.positionals":"arguments","py.common.version_mark":"{0}, empreinte {1}","py.common.version":"afficher la version et quitter","py.iar2oar.element_illisible":"élément illisible : {0} ({1})","py.iar2oar.objet_illisible":"objet illisible : {0} ({1})","py.iar2oar.sans_nom":"sans_nom","py.iar2oar.err_iar":"ERREUR : IAR illisible : {0}","py.iar2oar.err_vide":"ERREUR : aucun objet dans l'inventaire de cet IAR (dossier inventory/ absent ou vide)","py.iar2oar.err_rien":"ERREUR : rien à convertir (filtre trop strict, ou assets des objets absents de l'IAR)","py.iar2oar.ligne":"{0:4d} | {1:<60} | {2:4d} groupe(s) | {3:5d} parties | {4:5d} meshes","py.iar2oar.l_combine":" | combiné","py.iar2oar.l_imbrique":" | imbriqué niveau {0}","py.iar2oar.bilan":"{0} objet(s), {1} groupe(s), {2} partie(s) ; région de {3} m x {3} m","py.iar2oar.manquants":"{0} élément(s) sans asset objet dans l'IAR (ignorés) : {1}","py.iar2oar.ecrit":"OAR écrit : {0} ({1} groupes, {2} assets copiés)","py.iar2oar.desc":"iar2oar.py {0} : transforme une archive d'inventaire OpenSim (IAR) en OAR minimal, pour la chaîne habituelle (oar2glb.py, puis extraire_batiments.py). Ne modifie jamais l'IAR : écrit seulement l'OAR de sortie.","py.iar2oar.epilog":"Exemples :\n  python iar2oar.py MON.iar --list --filter REGEX\n  python iar2oar.py MON.iar -o inventaire.oar --filter REGEX --no-nested --margin 4\n\nPuis, comme pour une région :\n  python oar2glb.py inventaire.oar            (fabrique le GLB avec convoar)\n  python extraire_batiments.py inventaire.oar inventaire.glb --list\n  python extraire_batiments.py inventaire.oar inventaire.glb --group 12 -o batiments\n\nCe que fait le script :\n- chaque objet d'inventaire (asset object.xml) devient un ou plusieurs groupes de l'OAR ; le nom du groupe est celui de l'élément d'inventaire (la racine de l'objet est renommée), pour que --name et --filter fonctionnent ;\n- un objet « combiné » (CoalescedObject) est séparé en ses groupes, qui gardent leur disposition relative (décalages offsetx/y/z) ;\n- les objets contenus dans le contenu d'un autre (boîtes : TaskInventory) sont ajoutés aussi, jusqu'à 3 niveaux, une seule fois chacun (--no-nested les ignore) ; leur nom est « parent / nom » ;\n- les positions d'origine se chevauchent : chaque groupe (ou chaque objet combiné) reçoit une case sur une grille, sans terrain (le sol d'un extrait est alors son point le plus bas) ; la taille de la région (archive.xml) grandit par pas de 256 m si nécessaire ;\n- l'octet nul qui termine les XML de l'IAR est retiré ;\n- seuls les assets utiles à la 3D sont copiés : meshes, textures, matériaux.\nESTIMATION : l'étendue d'un groupe pour sa case est calculée à partir des positions et échelles des parties, sans les rotations.\nNON TESTÉ : convoar sur l'OAR produit ; attachements et vêtements ne sont pas pris en charge (pas d'avatar).\nAnciens noms des options (français), toujours acceptés : --liste (--list), --filtre (--filter), --sans-imbriques (--no-nested), --marge (--margin), --sortie (--output).","py.iar2oar.help.iar":"archive d'inventaire OpenSim (.iar)","py.iar2oar.help.output":"OAR à écrire (défaut : inventaire.oar)","py.iar2oar.help.list":"liste les objets trouvés, n'écrit rien","py.iar2oar.help.filter":"garde les éléments d'inventaire dont le nom correspond (expression régulière, casse ignorée)","py.iar2oar.help.no_nested":"ignore les objets contenus dans d'autres (boîtes)","py.iar2oar.help.margin":"espace entre deux cases de la grille, en mètres (défaut 4)"}}''')


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


VERSION = "1.6.4 (06/11/2026)"      # remplacé par build.py (fichier VERSION) dans dist/iar2oar.py
MARK = "dde6ae11"      # empreinte du fichier fabriqué, inscrite par build.py ; reste telle quelle depuis tools/

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(errors="replace")
    except Exception:
        pass

# noms d'options français d'origine -> noms actuels (anglais) ; les anciens restent acceptés, jamais de rupture pour les commandes déjà écrites
OLD_OPTIONS = {"--liste": "--list", "--filtre": "--filter", "--sans-imbriques": "--no-nested", "--marge": "--margin", "--sortie": "--output"}


def anciens_noms(argv):
    """les noms français des options (avant leur passage en anglais) restent acceptés : --marge 4 marche comme --margin 4 (aussi --marge=4)"""
    out = []
    for x in argv:
        k, eq, v = str(x).partition("=")
        out.append(OLD_OPTIONS.get(k, k) + eq + v if k.startswith("--") else x)
    return out


def version_tag():
    return VERSION if MARK.startswith("__") else _tr("py.common.version_mark", VERSION, MARK)


NIVEAU_MAX = 3
ASSETS_GARDES = ("_mesh.llmesh", "_texture.jp2", "_material.xml")
Z_BASE = 20.0
RX_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def texte(el, chemin):
    e = el.find(chemin)
    return (e.text or "").strip() if e is not None else ""


def lire_xml(octets):
    return ET.fromstring(octets.rstrip(b"\x00").lstrip(b"\xef\xbb\xbf"))


def lire_inventaire(t):
    """liste des elements d'inventaire de type objet : {nom, asset, dossier}"""
    items = []
    for m in t:
        if not (m.isfile() and m.name.startswith("inventory/") and m.name.endswith(".xml")):
            continue
        raw = t.extractfile(m).read()
        try:
            x = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig", "replace")
            x = re.sub(r"^<\?xml[^>]*\?>", "", x.lstrip("\ufeff")).strip()
            r = ET.fromstring(x)
        except Exception as e:
            print(_tr("py.iar2oar.element_illisible", m.name, e))
            continue
        if texte(r, "AssetType") != "6":
            continue
        nom = texte(r, "Name") or texte(r, "n")
        items.append({"nom": nom, "asset": texte(r, "AssetID").lower(), "dossier": "/".join(m.name.split("/")[1:-1])})
    return items


def groupes_de(racine):
    """(element SceneObjectGroup standard, decalage (x, y, z) ou None, taille combinee ou None) pour chaque groupe d'un asset"""
    if racine.tag != "CoalescedObject":
        return [(racine, None, None)]
    taille = tuple(float(racine.get(k) or 0) for k in "xyz")
    res = []
    for enfant in racine:
        if enfant.tag != "SceneObjectGroup":
            continue
        interne = enfant.find("SceneObjectGroup")
        g = interne if (interne is not None and enfant.find("RootPart") is None) else enfant
        off = tuple(float(enfant.get("offset" + k) or 0) for k in "xyz")
        res.append((g, off, taille))
    return res


def parties(g):
    return list(g.iter("SceneObjectPart"))


def vec(el, chemin):
    e = el.find(chemin)
    if e is None:
        return None
    try:
        return [float(e.findtext(k) or 0) for k in "XYZ"]
    except ValueError:
        return None


def etendue(g):
    """(min, max) approximatifs du groupe autour de sa racine, sans rotation (estimation)"""
    lo, hi = [0.0] * 3, [0.0] * 3
    for p in parties(g):
        off = vec(p, "OffsetPosition") or [0.0] * 3
        ech = vec(p, "Scale") or [0.5] * 3
        for k in range(3):
            lo[k] = min(lo[k], off[k] - ech[k] / 2)
            hi[k] = max(hi[k], off[k] + ech[k] / 2)
    return lo, hi


def ids_imbriques(g):
    ids = []
    for it in g.iter("TaskInventoryItem"):
        a = (it.findtext("AssetID/UUID") or it.findtext("AssetID") or "").strip().lower()
        if RX_UUID.fullmatch(a):
            ids.append((a, (it.findtext("Name") or "").strip()))
    return ids


def collecter(t, items, imbriques, filtre):
    """liste d'unites : {label, groupes: [(element, decalage)], taille, imb}"""
    assets = {m.name[7:43].lower(): m for m in t if m.isfile() and m.name.startswith("assets/") and m.name.endswith("_object.xml")}
    vus = set()
    unites = []
    manquants = []

    def ajouter(asset, label, niveau):
        if asset in vus:
            return
        m = assets.get(asset)
        if m is None:
            return
        vus.add(asset)
        try:
            racine = lire_xml(t.extractfile(m).read())
        except Exception as e:
            print(_tr("py.iar2oar.objet_illisible", label, e))
            return
        gs = groupes_de(racine)
        if not gs:
            return
        taille = gs[0][2]
        unites.append({"label": label, "groupes": [(g, off) for g, off, _ in gs], "taille": taille, "niveau": niveau, "asset": asset})
        if imbriques and niveau < NIVEAU_MAX:
            for g, _, _ in gs:
                for a, nom in ids_imbriques(g):
                    ajouter(a, f"{label} / {nom or a[:8]}", niveau + 1)

    for it in items:
        if filtre and not filtre.search(it["nom"]):
            continue
        if it["asset"] not in assets:
            manquants.append(it["nom"])
            continue
        ajouter(it["asset"], it["nom"], 0)
    return unites, manquants


def nom_sur(s):
    return re.sub(r"[^\w.\-]+", "_", s, flags=re.UNICODE).strip("_")[:50] or _tr("py.iar2oar.sans_nom")


def disposer(unites, marge):
    """donne a chaque unite une case (x, y) sur une grille ; renvoie la taille de la region (multiple de 256)"""
    for u in unites:
        if u["taille"]:
            u["case"] = (max(u["taille"][0], 1.0) + marge, max(u["taille"][1], 1.0) + marge)
            u["min"] = (0.0, 0.0)
        else:
            lo, hi = etendue(u["groupes"][0][0])
            u["case"] = (max(hi[0] - lo[0], 1.0) + marge, max(hi[1] - lo[1], 1.0) + marge)
            u["min"] = (lo[0], lo[1])
    plus_grand = max([max(u["case"]) for u in unites] + [1.0])
    aire = sum(u["case"][0] * u["case"][1] for u in unites)
    taille = max(256, int(math.ceil(max(plus_grand, math.sqrt(aire * 1.3)) / 256.0)) * 256)
    while True:
        x = y = hauteur = 0.0
        ok = True
        for u in sorted(unites, key=lambda v: -v["case"][1]):
            w, h = u["case"]
            if x + w > taille:
                x, y, hauteur = 0.0, y + hauteur, 0.0
            if y + h > taille:
                ok = False
                break
            u["origine"] = (x, y)
            x += w
            hauteur = max(hauteur, h)
        if ok:
            return taille
        taille += 256


def placer(u):
    """ecrit les noms et les positions dans les elements ; renvoie [(nom_fichier, octets)]"""
    sortie = []
    ox, oy = u["origine"]
    for k, (g, off) in enumerate(u["groupes"]):
        ps = parties(g)
        if not ps:
            continue
        if off is not None:
            pos = (ox + off[0], oy + off[1], Z_BASE + off[2])
            label = u["label"] if len(u["groupes"]) == 1 else f"{u['label']} [{k + 1}]"
        else:
            pos = (ox - u["min"][0] + 0.0, oy - u["min"][1] + 0.0, Z_BASE)
            label = u["label"]
        racine = ps[0]
        e = racine.find("Name")
        if e is None:
            e = ET.SubElement(racine, "Name")
        e.text = label
        for p in ps:
            gp = p.find("GroupPosition")
            if gp is None:
                gp = ET.SubElement(p, "GroupPosition")
            for kk, c in enumerate("XYZ"):
                ce = gp.find(c)
                if ce is None:
                    ce = ET.SubElement(gp, c)
                ce.text = repr(round(pos[kk], 5))
        uid = (texte(racine, "UUID/Guid") or texte(racine, "UUID/UUID") or texte(racine, "UUID") or f"{u['asset']}-{k}").lower()
        donnees = b'<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(g, encoding="utf-8")
        sortie.append((f"objects/{nom_sur(label)}_{pos[0]:.1f}-{pos[1]:.1f}-{pos[2]:.1f}_{uid}.xml", donnees, len(ps)))
    return sortie


def archive_xml(taille):
    return (f'<?xml version="1.0" encoding="utf-8"?>\n<archive major_version="0" minor_version="8">\n'
            f'  <creation_info><datetime>{int(time.time())}</datetime><id>iar2oar</id></creation_info>\n'
            f'  <region_info><is_megaregion>false</is_megaregion><size_in_meters>{taille},{taille}</size_in_meters></region_info>\n'
            f'</archive>\n').encode("utf-8")


def ajouter_octets(tout, nom, octets):
    ti = tarfile.TarInfo(nom)
    ti.size = len(octets)
    ti.mtime = int(time.time())
    tout.addfile(ti, io.BytesIO(octets))


def main(argv=None):
    ap = argparse.ArgumentParser(description=_tr("py.iar2oar.desc", version_tag()), epilog=_tr("py.iar2oar.epilog"),
                                 formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False)
    i18n_add_common(ap)
    ap.add_argument("--version", action="version", version=f"iar2oar {version_tag()}", help=_tr("py.common.version"))
    ap.add_argument("iar", help=_tr("py.iar2oar.help.iar"))
    ap.add_argument("-o", "--output", dest="sortie", default="inventaire.oar", help=_tr("py.iar2oar.help.output"))
    ap.add_argument("--list", dest="liste", action="store_true", help=_tr("py.iar2oar.help.list"))
    ap.add_argument("--filter", dest="filtre", help=_tr("py.iar2oar.help.filter"))
    ap.add_argument("--no-nested", dest="sans_imbriques", action="store_true", help=_tr("py.iar2oar.help.no_nested"))
    ap.add_argument("--margin", dest="marge", type=float, default=4.0, help=_tr("py.iar2oar.help.margin"))
    a = ap.parse_args(anciens_noms(sys.argv[1:] if argv is None else argv))
    filtre = re.compile(a.filtre, re.IGNORECASE) if a.filtre else None
    try:
        t = tarfile.open(a.iar, "r:*")
    except Exception as e:
        sys.exit(_tr("py.iar2oar.err_iar", e))
    with t:
        items = lire_inventaire(t)
        if not items:
            sys.exit(_tr("py.iar2oar.err_vide"))
        unites, manquants = collecter(t, items, not a.sans_imbriques, filtre)
        if not unites:
            sys.exit(_tr("py.iar2oar.err_rien"))
        taille = disposer(unites, a.marge)
        total_g = total_p = 0
        fichiers = []
        for u in unites:
            fs = placer(u)
            fichiers += fs
            total_g += len(fs)
            total_p += sum(n for _, _, n in fs)
        if a.liste:
            for i, u in enumerate(unites, 1):
                np_ = sum(len(parties(g)) for g, _ in u["groupes"])
                nm = sum(1 for g, _ in u["groupes"] for p in parties(g) if (p.findtext("Shape/SculptType") or "0").split(".")[0].isdigit()
                         and (int(p.findtext("Shape/SculptType") or 0) & 7) == 5)
                print(_tr("py.iar2oar.ligne", i, u["label"][:60], len(u["groupes"]), np_, nm)
                      + (_tr("py.iar2oar.l_combine") if u["taille"] else "") + (_tr("py.iar2oar.l_imbrique", u["niveau"]) if u["niveau"] else ""))
        print(_tr("py.iar2oar.bilan", len(unites), total_g, total_p, taille))
        if manquants:
            print(_tr("py.iar2oar.manquants", len(manquants), " ; ".join(manquants[:8]) + (" ..." if len(manquants) > 8 else "")))
        if a.liste:
            return 0
        n_assets = 0
        with tarfile.open(a.sortie, "w:gz", compresslevel=1) as tout:
            ajouter_octets(tout, "archive.xml", archive_xml(taille))
            noms = set()
            for nom, donnees, _ in fichiers:
                while nom in noms:
                    nom = nom[:-4] + "_b.xml"
                noms.add(nom)
                ajouter_octets(tout, nom, donnees)
            for m in t:
                if m.isfile() and m.name.startswith("assets/") and m.name.endswith(ASSETS_GARDES):
                    f = t.extractfile(m)
                    ti = tarfile.TarInfo(m.name)
                    ti.size = m.size
                    ti.mtime = m.mtime
                    tout.addfile(ti, f)
                    n_assets += 1
        print(_tr("py.iar2oar.ecrit", a.sortie, total_g, n_assets))
    return 0


if __name__ == "__main__":
    sys.exit(main())
