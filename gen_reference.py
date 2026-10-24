#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_reference.py : écrit REFERENCE_OPTIONS.md, la liste COMPLÈTE des options des quatre outils
(glb2html, glb2tiles, oar2glb, presence_server), lue dans les outils eux-mêmes : rien ne peut manquer.

Usage (depuis le dossier qui contient gen_reference.py ; le dossier des outils est dist\\) :
    python gen_reference.py                       (outils dans .\\dist, sortie .\\REFERENCE_OPTIONS.md)
    python gen_reference.py --outils "P:\\...\\dist" --sortie "P:\\...\\REFERENCE_OPTIONS.md"
    python gen_reference.py --verifier docs/fr/MANUEL.md    (liste les options absentes de ce fichier)

presence_server.py demande « pip install websockets » pour être lu.
"""
import argparse, contextlib, io, os, pathlib, runpy, sys, time

OUTILS = [
    ("glb2html", "glb2html.py",
     ("Fabrique la page web d'une région (GLB unique ou tuiles), met une région à jour, enregistre une région dans la carte des mondes et génère la page carte.",
      "Builds a region's web page (single GLB or tiles), updates a region, registers a region in the world map and generates the map page.")),
    ("glb2tiles", "glb2tiles.py",
     ("Découpe un GLB énorme en tuiles autonomes et fabrique la vue d'ensemble légère.",
      "Splits a huge GLB into self-contained tiles and builds the light overview.")),
    ("oar2glb", "oar2glb.py",
     ("Convertit une sauvegarde de région OpenSim (.oar) en GLB, refait le terrain complet.",
      "Converts an OpenSim region backup (.oar) into a GLB and rebuilds the full terrain.")),
    ("presence_server", "presence_server.py",
     ("Serveur de présence : positions des visiteurs, chat, modération.",
      "Presence server: visitor positions, chat, moderation.")),
]


def lire_parser(chemin: pathlib.Path, langue=None):
    """Exécute l'outil jusqu'à son parse_args, récupère le parser, n'exécute rien d'autre."""
    pris = {}

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
    sys.argv = [str(chemin), "--help", "--nopause"]   # v43 : oar2glb ne demande plus « Entrée pour fermer »
    sys.path.insert(0, str(chemin.parent))
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            try:
                runpy.run_path(str(chemin), run_name="__main__")
            except SystemExit:
                pass
    finally:
        argparse.ArgumentParser.parse_args, argparse.ArgumentParser.parse_known_args = orig_pa, orig_pka
        sys.argv, sys.path[:] = argv, path
        if langue:
            if env_avant is None:
                os.environ.pop("WEB3D_LANG", None)
            else:
                os.environ["WEB3D_LANG"] = env_avant
    return pris.get("p")


def cellule(t):
    return str(t).replace("|", "\\|").replace("\n", " ").strip()


def lignes(parser):
    """(options, valeur, défaut, effet) pour chaque argument, dans l'ordre de l'outil."""
    sortie = []
    vus = set()
    for a in parser._actions:
        if isinstance(a, argparse._HelpAction) or a.dest == "help":
            continue
        if id(a) in vus:
            continue
        vus.add(id(a))
        opts = " / ".join(f"`{o}`" for o in a.option_strings) if a.option_strings else f"`{a.dest}` (obligatoire / required)" if a.nargs not in ("?", "*") else f"`{a.dest}` (facultatif / optional)"
        if a.option_strings and isinstance(a, argparse._VersionAction):
            val, defaut = "", ""
        elif isinstance(a, (argparse._StoreTrueAction, argparse._StoreFalseAction)) or getattr(a, "nargs", None) == 0:
            val, defaut = "(aucune) / (none)", ""
        else:
            if a.choices:
                val = " / ".join(str(c) for c in a.choices)
            elif a.metavar:
                val = str(a.metavar if isinstance(a.metavar, str) else " ".join(a.metavar))
            else:
                val = a.dest.upper() if a.option_strings else ""
            d = a.default
            if isinstance(d, int) and not isinstance(d, bool) and "color" in a.dest:
                d = f"{d:06x}"                                   # couleurs affichées en hexadécimal, comme dans l'aide
            defaut = "" if d is None or d is argparse.SUPPRESS else (f"`{d}`" if d != "" else "(vide) / (empty)")
        aide = a.help if a.help and a.help is not argparse.SUPPRESS else ""
        sortie.append((opts, cellule(val), cellule(defaut), cellule(aide)))
    return sortie


def generer(dossier: pathlib.Path):
    """Texte du fichier et, par outil, la liste des options ; descriptions manquantes dans `manques`."""
    md = ["# Référence complète des options / Complete option reference", "",
          f"*Générée le {time.strftime('%d/%m/%Y')} par `gen_reference.py`, à partir des outils eux-mêmes : "
          "toute option qui existe dans un outil figure ici. Ne la modifie pas à la main : relance le script.*<br>"
          "*Generated by `gen_reference.py` from the tools themselves: every option of a tool is listed here. "
          "Do not edit by hand: run the script again.*", ""]
    tout, manques = {}, []
    for nom, fichier, resume in OUTILS:
        chemin = dossier / fichier
        md += [f"## {fichier}", "", resume[0] + "<br>" + resume[1], ""]
        if not chemin.exists():
            md += [f"*(fichier introuvable / file not found : {chemin})*", ""]
            continue
        try:
            p_fr = lire_parser(chemin, "fr")
            p_en = lire_parser(chemin, "en")
        except Exception as e:                                   # presence_server sans websockets, par exemple
            md += [f"*(lecture impossible / cannot read : {type(e).__name__} {e})*", ""]
            continue
        if p_fr is None or p_en is None:
            md += ["*(aucun parseur d'arguments trouvé / no argument parser found)*", ""]
            continue
        lf, le = lignes(p_fr), lignes(p_en)
        if [x[0] for x in lf] != [x[0] for x in le]:
            manques.append(f"{nom} : options différentes entre le français et l'anglais")
        tout[nom] = [x[0] for x in lf]
        md += ["| Option | Valeur / Value | Défaut / Default | Effet / Effect |", "|---|---|---|---|"]
        for (o, v, d, af), (_o, _v, _d, ae) in zip(lf, le):
            if not af or not ae:
                manques.append(f"{nom} {o} : description absente ({'fr' if not af else 'en'})")
            md.append(f"| {o} | {v} | {d} | {af}<br>{ae} |")
        md.append("")
    return "\n".join(md) + "\n", tout, manques


def main():
    ap = argparse.ArgumentParser(description="Écrit REFERENCE_OPTIONS.md depuis les outils.")
    ap.add_argument("--outils", default=None, help="dossier des outils (défaut : dist à côté du script)")
    ap.add_argument("--sortie", default=None, help="fichier écrit (défaut : REFERENCE_OPTIONS.md à côté du script)")
    ap.add_argument("--verifier", metavar="FICHIER.md", default=None, help="liste les options absentes de ce fichier (code retour 1 s'il en manque)")
    a = ap.parse_args()
    ici = pathlib.Path(__file__).resolve().parent
    dossier = pathlib.Path(a.outils) if a.outils else ici / "dist"
    texte, tout, manques = generer(dossier)
    sortie = pathlib.Path(a.sortie) if a.sortie else ici / "REFERENCE_OPTIONS.md"
    sortie.write_text(texte, encoding="utf-8")
    nb = sum(len(v) for v in tout.values())
    print(f"[ok] {nb} arguments décrits -> {sortie}")
    for m in manques:
        print(f"[manque] {m}")
    if manques:
        sys.exit(1)
    if a.verifier:
        doc = pathlib.Path(a.verifier).read_text(encoding="utf-8")
        manque = {}
        for nom, liste in tout.items():
            for cell in liste:
                for o in [x.strip("` ") for x in cell.split(" / ")]:
                    if o.startswith("--") and o != "--help" and o not in doc:
                        manque.setdefault(nom, []).append(o)
        for nom, l in manque.items():
            print(f"[absentes de {a.verifier}] {nom} : {' '.join(l)}")
        if not manque:
            print(f"[ok] toutes les options figurent dans {a.verifier}")
        sys.exit(1 if manque else 0)


if __name__ == "__main__":
    main()
