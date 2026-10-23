#!/usr/bin/env python3
"""glb-stats.py : analyse rapide d'un GLB, quelle que soit sa taille.

Lit uniquement l'en-tête JSON du fichier (jamais les données binaires ni les textures) : quelques secondes
et très peu de mémoire, même pour un GLB de plusieurs Go.

Usage : python glb-stats.py "Region.glb" [--bloc 256] [--sortie rapport.txt]

Donne : poids par catégorie, instances de meshes, étendue de la région, objets plus grands qu'un bloc,
et la répartition par blocs carrés (nœuds, triangles, Mo de textures, Mo de géométrie) pour juger d'un
découpage en tuiles. Plan horizontal = X et Z (glTF est Y vers le haut).
"""
import argparse
import collections
import json
import math
import os
import struct
import sys

# <<I18N_PY>>
def _i18n_boot():   # depuis les sources : charge src/i18n_py.py ; fabriqué par build.py (dist\) : ce bloc est remplacé par le texte de i18n_py.py avec les langues intégrées
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
    acc, bvs, meshes, nodes, mats = m["acc"], m["bvs"], m["meshes"], m["nodes"], m["mats"]
    imgs, texs, acc_octets, img_octets = m["imgs"], m["texs"], m["acc_octets"], m["img_octets"]
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
    ap.add_argument("--bloc", type=float, default=256.0, help=_tr("py.stats.cote_des_blocs_en_metres_defaut"))
    ap.add_argument("--sortie", help=_tr("py.stats.ecrit_aussi_le_rapport_dans_ce"))
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


if __name__ == "__main__":
    main()
