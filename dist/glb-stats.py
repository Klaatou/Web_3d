#!/usr/bin/env python3
"""glb-stats.py : analyse rapide d'un GLB, quelle que soit sa taille.

Lit uniquement l'en-tête JSON du fichier (jamais les données binaires ni les textures) : quelques secondes
et très peu de mémoire, même pour un GLB de plusieurs Go.

Usage : python glb-stats.py "Region.glb" [--block 256] [--output rapport.txt]

Donne : poids par catégorie, instances de meshes, étendue de la région, objets plus grands qu'un bloc,
et la répartition par blocs carrés (nœuds, triangles, Mo de textures, Mo de géométrie) pour juger d'un
découpage en tuiles. Plan horizontal = X et Z (glTF est Y vers le haut).
"""
import argparse
import collections
import json
import os
import struct
import sys

# ---- langue des messages (v36) : textes intégrés par build.py (src/i18n/*.json, clés py.*) ; --lang fr|en|auto ou WEB3D_LANG ----
import json as _json, locale as _locale, os as _os, pathlib as _pl, sys as _sys

# fabrication (build.py) : la ligne suivante devient I18N_DATA = { "fr": {...}, "en": {...} }
I18N_DATA = _json.loads(r'''{"en":{"_name":"English","py.common.help":"show this help message and exit","py.common.lang_help":"language of the messages and of this help: fr, en or auto (default: the system's language; environment variable WEB3D_LANG is equivalent). Available: {0}","py.common.optionals":"options","py.common.positionals":"arguments","py.common.version_mark":"{0}, fingerprint {1}","py.common.version":"show the version and exit","py.stats.0_16_mediane_1_1f_90":"{0:>16}: median {1:,.1f} | 90 % of blocks under {2:,.1f} | maximum {3:,.1f}","py.stats.attention_geometrie_compressee_0_les_mo":"Warning: compressed geometry ({0}): the MB of geometry above are the decoded size, not the file's.","py.stats.aucun_mesh_positionnable_accessors_sans_min":"No placeable mesh (accessors without min/max?).","py.stats.bloc_0_1_2_1f_mo":"  block {0},{1}: {2:.1f} MB of geometry, {3} triangles, {4} instances, {5:.1f} MB of textures","py.stats.blocs_de_0_0f_m_1":"== Blocks of {0:.0f} m: {1} non-empty (instance center; geometry and textures without duplicates within the block) ==","py.stats.ce_fichier_n_est_pas_un":"This file is not a GLB.","py.stats.cote_des_blocs_en_metres_defaut":"block side in meters (default 256)","py.stats.cout_de_la_reutilisation_entre_blocs":"== Cost of reuse between blocks ==","py.stats.desc":"glb-stats.py: quick analysis of a GLB, whatever its size. Reads only the JSON header (never the binary data or the textures): a few seconds and very little memory.","py.stats.ecrit_aussi_le_rapport_dans_ce":"also writes the report to this file (UTF-8)","py.stats.etendue":"== Extent ==","py.stats.fichier_0_1_1f_mo_en":"File: {0} ({1:,.1f} MB; JSON header read: {2:,.1f} MB)","py.stats.geometrie_accessors_uniques_0_1f_mo":"Geometry (unique accessors): {0:,.1f} MB | Embedded textures: {1:,.1f} MB | Rest: {2:,.1f} MB","py.stats.geometrie_mo":"geometry (MB)","py.stats.geometrie_utilisee_par_plusieurs_blocs_0":"Geometry used by several blocks: {0:,.1f} MB ({1:.0f} % of the total) | textures used by several blocks: {2:,.1f} MB ({3:.0f} % of the total): size of a shared library loaded once.","py.stats.help.glb":"the .glb file to analyze","py.stats.le_premier_bloc_du_glb_n":"The first GLB chunk is not JSON.","py.stats.les_5_blocs_les_plus_lourds":"The 5 blocks heaviest in geometry:","py.stats.meshes_reutilises_plusieurs_fois_0_materiaux":"Meshes reused several times: {0} | materials: {1} | textures (images): {2} (used: {3})","py.stats.nud_0_1_2_0f_m":"  - node {0} \"{1}\": {2:.0f} m, {3} mesh(es)","py.stats.nuds_parcourus_0_meshes_1_utilises":"Nodes visited: {0} | meshes: {1} (used: {2}) | mesh instances: {3}","py.stats.objets_racine_0_plus_grands_qu":"Root objects: {0} | larger than a {1:.0f} m block: {2}","py.stats.poids_estime_octets_lus_dans_l":"== Estimated weight (bytes read from the header, without decoding) ==","py.stats.somme_des_blocs_geometrie_0_1f":"Sum of blocks: geometry {0:,.1f} MB (against {1:,.1f} MB without duplicates across the whole file): difference = extra cost if shared meshes are duplicated in each block.","py.stats.sommets_uniques_0_sommets_rendus_instances":"Unique vertices: {0:,} | rendered vertices (instances included): {1:,} | rendered triangles: {2:,}","py.stats.taux_de_reutilisation_sommets_rendus_uniques":"Reuse ratio (rendered / unique vertices): {0:.1f}","py.stats.x_0_1f_a_1_1f":"X: {0:.1f} to {1:.1f} ({2:.0f} m) | Z: {3:.1f} to {4:.1f} ({5:.0f} m) | height Y: {6:.1f} to {7:.1f}"},"fr":{"_name":"Français","py.common.help":"afficher ce message d'aide et quitter","py.common.lang_help":"langue des messages et de l'aide : fr, en ou auto (défaut : langue du système ; variable d'environnement WEB3D_LANG équivalente). Disponibles : {0}","py.common.optionals":"options","py.common.positionals":"arguments","py.common.version_mark":"{0}, empreinte {1}","py.common.version":"afficher la version et quitter","py.stats.0_16_mediane_1_1f_90":"{0:>16} : médiane {1:,.1f} | 90 % des blocs sous {2:,.1f} | maximum {3:,.1f}","py.stats.attention_geometrie_compressee_0_les_mo":"Attention : géométrie compressée ({0}) : les Mo de géométrie ci-dessus sont la taille décodée, pas celle du fichier.","py.stats.aucun_mesh_positionnable_accessors_sans_min":"Aucun mesh positionnable (accessors sans min/max ?).","py.stats.bloc_0_1_2_1f_mo":"  bloc {0},{1} : {2:.1f} Mo de géométrie, {3} triangles, {4} instances, {5:.1f} Mo de textures","py.stats.blocs_de_0_0f_m_1":"== Blocs de {0:.0f} m : {1} non vides (centre des instances ; géométrie et textures sans doublon dans le bloc) ==","py.stats.ce_fichier_n_est_pas_un":"Ce fichier n'est pas un GLB.","py.stats.cote_des_blocs_en_metres_defaut":"côté des blocs en mètres (défaut 256)","py.stats.cout_de_la_reutilisation_entre_blocs":"== Coût de la réutilisation entre blocs ==","py.stats.desc":"glb-stats.py : analyse rapide d'un GLB, quelle que soit sa taille. Lit uniquement l'en-tête JSON (jamais les données binaires ni les textures) : quelques secondes et très peu de mémoire.","py.stats.ecrit_aussi_le_rapport_dans_ce":"écrit aussi le rapport dans ce fichier (UTF-8)","py.stats.etendue":"== Étendue ==","py.stats.fichier_0_1_1f_mo_en":"Fichier : {0} ({1:,.1f} Mo ; en-tête JSON lu : {2:,.1f} Mo)","py.stats.geometrie_accessors_uniques_0_1f_mo":"Géométrie (accessors uniques) : {0:,.1f} Mo | Textures embarquées : {1:,.1f} Mo | Reste : {2:,.1f} Mo","py.stats.geometrie_mo":"géométrie (Mo)","py.stats.geometrie_utilisee_par_plusieurs_blocs_0":"Géométrie utilisée par plusieurs blocs : {0:,.1f} Mo ({1:.0f} % du total) | textures utilisées par plusieurs blocs : {2:,.1f} Mo ({3:.0f} % du total) : taille d'une bibliothèque commune chargée une fois.","py.stats.help.glb":"fichier .glb à analyser","py.stats.le_premier_bloc_du_glb_n":"Le premier bloc du GLB n'est pas du JSON.","py.stats.les_5_blocs_les_plus_lourds":"Les 5 blocs les plus lourds en géométrie :","py.stats.meshes_reutilises_plusieurs_fois_0_materiaux":"Meshes réutilisés plusieurs fois : {0} | matériaux : {1} | textures (images) : {2} (utilisées : {3})","py.stats.nud_0_1_2_0f_m":"  - nœud {0} « {1} » : {2:.0f} m, {3} mesh(es)","py.stats.nuds_parcourus_0_meshes_1_utilises":"Nœuds parcourus : {0} | meshes : {1} (utilisés : {2}) | instances de meshes : {3}","py.stats.objets_racine_0_plus_grands_qu":"Objets racine : {0} | plus grands qu'un bloc de {1:.0f} m : {2}","py.stats.poids_estime_octets_lus_dans_l":"== Poids estimé (octets lus dans l'en-tête, sans décoder) ==","py.stats.somme_des_blocs_geometrie_0_1f":"Somme des blocs : géométrie {0:,.1f} Mo (contre {1:,.1f} Mo sans doublon dans tout le fichier) : écart = surcoût si les meshes partagés sont dupliqués dans chaque bloc.","py.stats.sommets_uniques_0_sommets_rendus_instances":"Sommets uniques : {0:,} | sommets rendus (instances comprises) : {1:,} | triangles rendus : {2:,}","py.stats.taux_de_reutilisation_sommets_rendus_uniques":"Taux de réutilisation (sommets rendus / uniques) : {0:.1f}","py.stats.x_0_1f_a_1_1f":"X : {0:.1f} à {1:.1f} ({2:.0f} m) | Z : {3:.1f} à {4:.1f} ({5:.0f} m) | hauteur Y : {6:.1f} à {7:.1f}"}}''')


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


COMP = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}


def lire_json(chemin):
    with open(chemin, "rb") as f:
        magic, _, _ = struct.unpack("<4sII", f.read(12))
        if magic != b"glTF":
            sys.exit(_tr("py.stats.ce_fichier_n_est_pas_un"))
        n, typ = struct.unpack("<II", f.read(8))
        if typ != 0x4E4F534A:
            sys.exit(_tr("py.stats.le_premier_bloc_du_glb_n"))
        return json.loads(f.read(n)), n


def mat_mul(a, b):
    return [sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4)) for c in range(4) for r in range(4)]


def mat_noeud(n):
    if "matrix" in n:
        return n["matrix"]
    t = n.get("translation", [0, 0, 0])
    x, y, z, w = n.get("rotation", [0, 0, 0, 1])
    s = n.get("scale", [1, 1, 1])
    r = [1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w),
         2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w),
         2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)]
    return [r[0] * s[0], r[1] * s[0], r[2] * s[0], 0, r[3] * s[1], r[4] * s[1], r[5] * s[1], 0,
            r[6] * s[2], r[7] * s[2], r[8] * s[2], 0, t[0], t[1], t[2], 1]


def coins_monde(m, lo, hi):
    pts = []
    for cx in (lo[0], hi[0]):
        for cy in (lo[1], hi[1]):
            for cz in (lo[2], hi[2]):
                pts.append((m[0] * cx + m[4] * cy + m[8] * cz + m[12],
                            m[1] * cx + m[5] * cy + m[9] * cz + m[13],
                            m[2] * cx + m[6] * cy + m[10] * cz + m[14]))
    return pts


def mo(o):
    return o / 1048576


def fmt(n):
    return f"{n:,}".replace(",", " ")


def modele(g):
    """Mesures communes (utilisées aussi par glb2tiles.py) : accessors, images, boîtes par mesh, instances de meshes."""
    acc, bvs = g.get("accessors", []), g.get("bufferViews", [])
    meshes, nodes, mats = g.get("meshes", []), g.get("nodes", []), g.get("materials", [])
    imgs, texs = g.get("images", []), g.get("textures", [])
    def acc_octets(i):
        x = acc[i]
        return x.get("count", 0) * NCOMP.get(x.get("type"), 1) * COMP.get(x.get("componentType"), 4)

    # images : octets par image (bufferView embarqué)
    img_octets = [bvs[i["bufferView"]].get("byteLength", 0) if "bufferView" in i else 0 for i in imgs]
    # matériau -> images
    def imgs_materiau(mi):
        s = set()
        pbr = mats[mi].get("pbrMetallicRoughness", {})
        for t in (pbr.get("baseColorTexture"), pbr.get("metallicRoughnessTexture"), mats[mi].get("normalTexture"),
                  mats[mi].get("occlusionTexture"), mats[mi].get("emissiveTexture")):
            if t and "index" in t and t["index"] < len(texs):
                src = texs[t["index"]].get("source")
                if src is not None:
                    s.add(src)
        return s

    # par mesh : bbox locale, sommets, triangles, octets de géométrie, accessors, images
    info = []
    for me in meshes:
        lo, hi = [1e30] * 3, [-1e30] * 3
        tri = 0
        pos_accs, accs, im = set(), set(), set()
        for pr in me.get("primitives", []):
            at = pr.get("attributes", {})
            if "POSITION" in at:
                x = acc[at["POSITION"]]
                pos_accs.add(at["POSITION"])
                if "min" in x and "max" in x:
                    lo = [min(lo[k], x["min"][k]) for k in range(3)]
                    hi = [max(hi[k], x["max"][k]) for k in range(3)]
                n_idx = acc[pr["indices"]].get("count", 0) if "indices" in pr else x.get("count", 0)
                tri += n_idx // 3 if pr.get("mode", 4) == 4 else 0
            for ai in list(at.values()) + ([pr["indices"]] if "indices" in pr else []):
                accs.add(ai)
            if "material" in pr and pr["material"] < len(mats):
                im |= imgs_materiau(pr["material"])
        som = sum(acc[i].get("count", 0) for i in pos_accs)
        info.append({"lo": lo, "hi": hi, "som": som, "tri": tri, "accs": accs, "imgs": im,
                     "geo": sum(acc_octets(i) for i in accs)})

    # parcours de la scène : une entrée par nœud portant un mesh
    sc = g.get("scenes", [{}])[g.get("scene", 0)] if g.get("scenes") else {}
    racines = sc.get("nodes", list(range(len(nodes))))
    inst = []   # (mesh, racine, coins monde)
    pile = [(r, [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1], r) for r in racines]
    vus = 0
    while pile:
        ni, parent, racine = pile.pop()
        vus += 1
        n = nodes[ni]
        m = mat_mul(parent, mat_noeud(n))
        if "mesh" in n and n["mesh"] < len(info):
            d = info[n["mesh"]]
            if d["lo"][0] < 1e29:
                inst.append((n["mesh"], racine, coins_monde(m, d["lo"], d["hi"])))
        for c in n.get("children", []):
            pile.append((c, m, racine))

    utilises = {mi for mi, _, _ in inst}
    acc_uniques = set().union(*[info[i]["accs"] for i in utilises]) if utilises else set()
    img_utilisees = set().union(*[info[i]["imgs"] for i in utilises]) if utilises else set()
    geo_total = sum(acc_octets(i) for i in acc_uniques)
    img_total = sum(img_octets[i] for i in img_utilisees)
    pos_uniques = set()
    for i in utilises:
        for pr in meshes[i].get("primitives", []):
            if "POSITION" in pr.get("attributes", {}):
                pos_uniques.add(pr["attributes"]["POSITION"])
    som_uniques = sum(acc[i]["count"] for i in pos_uniques)
    som_rendus = sum(info[mi]["som"] for mi, _, _ in inst)
    tri_rendus = sum(info[mi]["tri"] for mi, _, _ in inst)
    return {"acc": acc, "bvs": bvs, "meshes": meshes, "nodes": nodes, "mats": mats, "imgs": imgs, "texs": texs,
            "acc_octets": acc_octets, "img_octets": img_octets, "imgs_materiau": imgs_materiau, "info": info,
            "racines": racines, "inst": inst, "vus": vus, "utilises": utilises, "img_utilisees": img_utilisees,
            "geo_total": geo_total, "img_total": img_total, "som_uniques": som_uniques, "som_rendus": som_rendus,
            "tri_rendus": tri_rendus}


def rapport(chemin, bloc=256.0, g=None, njson=0):
    """Rapport texte (liste de lignes) ; `g` et `njson` : JSON déjà lu (sinon relu depuis `chemin`)."""
    taille = os.path.getsize(chemin)
    if g is None:
        g, njson = lire_json(chemin)
    m = modele(g)
    meshes, nodes, mats = m["meshes"], m["nodes"], m["mats"]
    imgs, acc_octets, img_octets = m["imgs"], m["acc_octets"], m["img_octets"]
    info, inst, vus = m["info"], m["inst"], m["vus"]
    utilises, img_utilisees, geo_total, img_total = m["utilises"], m["img_utilisees"], m["geo_total"], m["img_total"]
    som_uniques, som_rendus, tri_rendus = m["som_uniques"], m["som_rendus"], m["tri_rendus"]
    out = []
    p = out.append

    p(_tr("py.stats.fichier_0_1_1f_mo_en", os.path.basename(chemin), mo(taille), mo(njson)).replace(",", " "))
    p("")
    p("== Contenu ==")
    p(_tr("py.stats.nuds_parcourus_0_meshes_1_utilises", vus, len(meshes), len(utilises), len(inst)))
    reutil = sum(1 for v in collections.Counter(mi for mi, _, _ in inst).values() if v > 1)
    p(_tr("py.stats.meshes_reutilises_plusieurs_fois_0_materiaux", reutil, len(mats), len(imgs), len(img_utilisees)))
    p(_tr("py.stats.sommets_uniques_0_sommets_rendus_instances", som_uniques, som_rendus, tri_rendus).replace(",", " "))
    if som_uniques:
        p(_tr("py.stats.taux_de_reutilisation_sommets_rendus_uniques", som_rendus / som_uniques))
    p("")
    p(_tr("py.stats.poids_estime_octets_lus_dans_l"))
    autres = max(0, taille - njson - geo_total - img_total)
    p(_tr("py.stats.geometrie_accessors_uniques_0_1f_mo", mo(geo_total), mo(img_total), mo(autres)).replace(",", " "))

    comp = [e for e in g.get("extensionsUsed", []) if e in ("KHR_draco_mesh_compression", "EXT_meshopt_compression", "KHR_meshopt_compression")]
    if comp:
        p(_tr("py.stats.attention_geometrie_compressee_0_les_mo", ', '.join(comp)))
    if not inst:
        p(_tr("py.stats.aucun_mesh_positionnable_accessors_sans_min"))
    else:
        xs = [c[0] for _, _, cs in inst for c in cs]
        ys = [c[1] for _, _, cs in inst for c in cs]
        zs = [c[2] for _, _, cs in inst for c in cs]
        x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
        p("")
        p(_tr("py.stats.etendue"))
        p(_tr("py.stats.x_0_1f_a_1_1f", x0, x1, x1 - x0, z0, z1, z1 - z0, min(ys), max(ys)))

        # racines plus grandes qu'un bloc
        par_racine = {}
        for mi, r, cs in inst:
            b = par_racine.setdefault(r, [1e30, -1e30, 1e30, -1e30, 0])
            b[0] = min(b[0], min(c[0] for c in cs)); b[1] = max(b[1], max(c[0] for c in cs))
            b[2] = min(b[2], min(c[2] for c in cs)); b[3] = max(b[3], max(c[2] for c in cs)); b[4] += 1
        gros = sorted(((max(b[1] - b[0], b[3] - b[2]), r, b[4]) for r, b in par_racine.items() if max(b[1] - b[0], b[3] - b[2]) > bloc), reverse=True)
        p(_tr("py.stats.objets_racine_0_plus_grands_qu", len(par_racine), bloc, len(gros)))
        for etendue, r, nb in gros[:5]:
            p(_tr("py.stats.nud_0_1_2_0f_m", r, nodes[r].get('name', '')[:40], etendue, nb))

        # répartition par blocs (centre de chaque instance)
        blocs = {}
        acc_blocs, img_blocs = collections.defaultdict(set), collections.defaultdict(set)
        for mi, _, cs in inst:
            cx = sum(c[0] for c in cs) / 8
            cz = sum(c[2] for c in cs) / 8
            k = (int((cx - x0) // bloc), int((cz - z0) // bloc))
            b = blocs.setdefault(k, {"n": 0, "tri": 0, "meshes": set(), "imgs": set()})
            b["n"] += 1
            b["tri"] += info[mi]["tri"]
            b["meshes"].add(mi)
            b["imgs"] |= info[mi]["imgs"]
            for ai in info[mi]["accs"]:
                acc_blocs[ai].add(k)
            for ii in info[mi]["imgs"]:
                img_blocs[ii].add(k)
        lignes = []
        for k in sorted(blocs):
            b = blocs[k]
            ga = set().union(*[info[i]["accs"] for i in b["meshes"]])
            lignes.append((k, b["n"], b["tri"], mo(sum(acc_octets(i) for i in ga)), mo(sum(img_octets[i] for i in b["imgs"]))))
        p("")
        p(_tr("py.stats.blocs_de_0_0f_m_1", bloc, len(blocs)))
        if len(lignes) <= 60:
            p(f"{'bloc (x,z)':>10} {'instances':>10} {'triangles':>12} {'géom. Mo':>9} {'text. Mo':>9}")
            for k, n_, tri_, g_, t_ in lignes:
                p(f"{str(k[0]) + ',' + str(k[1]):>10} {n_:>10} {fmt(tri_):>12} {g_:>9.1f} {t_:>9.1f}")
        else:
            def quant(v, q):
                v = sorted(v)
                return v[min(len(v) - 1, int(q * len(v)))]
            for nom, idx in ((_tr("py.stats.geometrie_mo"), 3), ("triangles", 2), ("textures (Mo)", 4)):
                v = [l[idx] for l in lignes]
                p(_tr("py.stats.0_16_mediane_1_1f_90", nom, quant(v, 0.5), quant(v, 0.9), max(v)).replace(",", " "))
            p(_tr("py.stats.les_5_blocs_les_plus_lourds"))
            for k, n_, tri_, g_, t_ in sorted(lignes, key=lambda l: -l[3])[:5]:
                p(_tr("py.stats.bloc_0_1_2_1f_mo", k[0], k[1], g_, fmt(tri_), n_, t_))
        tot_geo = sum(l[3] for l in lignes)
        bib_geo = mo(sum(acc_octets(i) for i, bs in acc_blocs.items() if len(bs) > 1))
        bib_img = mo(sum(img_octets[i] for i, bs in img_blocs.items() if len(bs) > 1))
        p("")
        p(_tr("py.stats.cout_de_la_reutilisation_entre_blocs"))
        p(_tr("py.stats.somme_des_blocs_geometrie_0_1f", tot_geo, mo(geo_total)).replace(",", " "))
        p(_tr("py.stats.geometrie_utilisee_par_plusieurs_blocs_0", bib_geo, 100 * bib_geo / max(mo(geo_total), 1e-9), bib_img, 100 * bib_img / max(mo(img_total), 1e-9)).replace(",", " "))

    return out


def main():
    ap = argparse.ArgumentParser(description=_tr("py.stats.desc"), add_help=False)
    i18n_add_common(ap)
    ap.add_argument("glb", help=_tr("py.stats.help.glb"))
    ap.add_argument("--block", metavar="BLOCK", dest="bloc", type=float, default=256.0, help=_tr("py.stats.cote_des_blocs_en_metres_defaut"))
    ap.add_argument("--output", metavar="OUTPUT", dest="sortie", help=_tr("py.stats.ecrit_aussi_le_rapport_dans_ce"))
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    texte = "\n".join(rapport(a.glb, a.bloc))
    print(texte)
    if a.sortie:
        with open(a.sortie, "w", encoding="utf-8") as f:
            f.write(texte + "\n")


# v43 : anciens noms d'options (avant la v43), toujours acceptés
OLD_OPTIONS = {"--bloc": "--block", "--sortie": "--output"}


def old_options(argv):
    """Remplace les anciens noms d'options par les nouveaux (« --nom=valeur » compris)."""
    out = []
    for x in argv:
        k, eq, v = str(x).partition("=")
        out.append(OLD_OPTIONS.get(k, k) + eq + v if k.startswith("--") else x)
    return out


if __name__ == "__main__":
    sys.argv = old_options(sys.argv)
    main()
