#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""inspecter_objets.py : dit ce que contiennent les objets d'un OAR dont le nom correspond (forme, parametres de prim, materiaux).

Script isole, hors du depot, en lecture seule, messages en francais sans accents. Il lit l'OAR en continu (une seule lecture, objects/ seulement).

  python inspecter_objets.py OAR [--noms REGEX] [--max N] [--exemples K]

Par nom d'objet (parties de tous les objets dont le nom RACINE ou le nom de la PARTIE correspond a REGEX, casse ignoree ; defaut : tous),
il affiche : nombre de parties ; types de parametres supplementaires presents (0x80 = materiau PBR) ; nombre de parties avec <MatOvrd> ;
nombre de parties dont le TextureEntry porte un MaterialID non nul (ancien materiau) ; les formes les plus frequentes
(ProfileCurve, PathCurve, coupes PathBegin/PathEnd/ProfileBegin/ProfileEnd, creux ProfileHollow, sculpt/mesh) ; echelle min et max ;
et quelques fichiers d'exemple.
"""
import argparse, base64, collections, re, struct, sys, tarfile, time, uuid
from pathlib import Path
import xml.etree.ElementTree as ET

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(errors="replace")
    except Exception:
        pass

NUL = str(uuid.UUID(int=0))


def txt(el, chemin):
    e = el.find(chemin)
    return (e.text or "").strip() if e is not None and e.text else ""


def types_extra(b64):
    """types (hexa) des parametres supplementaires d'une prim"""
    try:
        d = base64.b64decode(b64)
        i, out = 1, []
        for _ in range(d[0]):
            typ, taille = struct.unpack_from("<Hi", d, i)
            out.append("0x%02x" % typ)
            i += 6 + taille
        return out
    except Exception:
        return []


def materiaux_te(b64):
    """UUID non nuls du champ MaterialID du TextureEntry (derniere section : 16 octets par valeur)"""
    try:
        d = base64.b64decode(b64)
    except Exception:
        return set()
    p = 0
    try:
        def section(taille):
            nonlocal p
            vals = {d[p:p + taille]}
            p += taille
            while p < len(d):
                bits, fini = 0, False
                while not fini:
                    b = d[p]
                    bits = (bits << 7) | (b & 0x7F)
                    p += 1
                    fini = not b & 0x80
                if bits == 0:
                    break
                vals.add(d[p:p + taille])
                p += taille
            return vals
        res = set()
        for t in (16, 4, 4, 4, 2, 2, 2, 1, 1, 1, 16):
            v = section(t)
            if t == 16:
                res = v
        return {str(uuid.UUID(bytes=bytes(x))) for x in res if len(x) == 16} - {NUL}
    except Exception:
        return set()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Inspecte les objets d'un OAR (voir l'en-tete du script).")
    ap.add_argument("oar")
    ap.add_argument("--noms", default="", help="expression reguliere sur le nom de l'objet ou de la partie (defaut : tous)")
    ap.add_argument("--max", type=int, default=15, help="nombre maximal de noms affiches (defaut 15)")
    ap.add_argument("--exemples", type=int, default=2, help="fichiers d'exemple par nom (defaut 2)")
    a = ap.parse_args(argv)
    rx = re.compile(a.noms, re.IGNORECASE) if a.noms else None
    chemin = Path(a.oar)
    if not chemin.is_file():
        sys.exit(f"ERREUR : OAR introuvable : {chemin}")
    groupes = collections.OrderedDict()
    t0 = dernier = time.time()
    n_obj = 0
    with open(chemin, "rb") as brut:
        with tarfile.open(fileobj=brut, mode="r|gz") as tar:
            for m in tar:
                if time.time() - dernier > 15:
                    dernier = time.time()
                    print(f"  ... {n_obj} objets lus, {brut.tell() / 1048576:.0f} Mo ({time.time() - t0:.0f} s)", flush=True)
                if not (m.isfile() and m.name.startswith("objects/") and m.name.endswith(".xml")):
                    continue
                n_obj += 1
                try:
                    racine = ET.fromstring(tar.extractfile(m).read().lstrip(b"\xef\xbb\xbf"))
                except ET.ParseError:
                    continue
                parts = list(racine.iter("SceneObjectPart"))
                if not parts:
                    continue
                nom_racine = txt(parts[0], "Name")
                for el in parts:
                    nom = txt(el, "Name")
                    if rx and not (rx.search(nom) or rx.search(nom_racine)):
                        continue
                    sh = el.find("Shape")
                    if sh is None:
                        continue
                    g = groupes.setdefault(nom or "(sans nom)", {"n": 0, "types": collections.Counter(), "ovr": 0, "mat": 0, "formes": collections.Counter(),
                                                                  "ech": [None, None], "ex": []})
                    g["n"] += 1
                    ep = txt(sh, "ExtraParams")
                    for t in set(types_extra(ep)) if ep else ():
                        g["types"][t] += 1
                    g["ovr"] += bool(txt(sh, "MatOvrd"))
                    te = txt(sh, "TextureEntry")
                    g["mat"] += bool(te and materiaux_te(te))
                    forme = (txt(sh, "ProfileShape") or txt(sh, "ProfileCurve"), "chemin " + txt(sh, "PathCurve"),
                             "coupe chemin %s-%s" % (txt(sh, "PathBegin") or "0", txt(sh, "PathEnd") or "0"),
                             "coupe profil %s-%s" % (txt(sh, "ProfileBegin") or "0", txt(sh, "ProfileEnd") or "0"),
                             "creux " + (txt(sh, "ProfileHollow") or "0"),
                             "torsion %s/%s" % (txt(sh, "PathTwist") or "0", txt(sh, "PathTwistBegin") or "0"),
                             "sculpt/mesh " + (txt(sh, "SculptType") if txt(sh, "SculptEntry").lower() == "true" else "non"))
                    g["formes"][forme] += 1
                    try:
                        s = [float(txt(el, "Scale/" + k)) for k in "XYZ"]
                        g["ech"][0] = s if g["ech"][0] is None else [min(x, y) for x, y in zip(g["ech"][0], s)]
                        g["ech"][1] = s if g["ech"][1] is None else [max(x, y) for x, y in zip(g["ech"][1], s)]
                    except ValueError:
                        pass
                    if len(g["ex"]) < a.exemples and m.name not in g["ex"]:
                        g["ex"].append(m.name)
    print(f"{n_obj} objets lus en {time.time() - t0:.0f} s ; {len(groupes)} nom(s) de partie correspondant")
    for nom, g in sorted(groupes.items(), key=lambda t: -t[1]["n"])[:a.max]:
        print()
        print(f"== {nom[:60]} : {g['n']} partie(s)")
        print(f"   parametres supplementaires (parties qui en ont) : {dict(g['types']) or 'aucun'} ; <MatOvrd> : {g['ovr']} ; MaterialID non nul dans le TextureEntry : {g['mat']}")
        for f, k in g["formes"].most_common(4):
            print(f"   {k:5d} x " + " | ".join(f))
        if g["ech"][0]:
            print("   echelle min " + str([round(x, 2) for x in g["ech"][0]]) + " max " + str([round(x, 2) for x in g["ech"][1]]))
        for ex in g["ex"]:
            print("   exemple : " + ex[-90:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
