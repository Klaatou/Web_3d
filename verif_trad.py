#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verif_trad.py : compare un document Markdown français et sa traduction anglaise.

Usage (depuis la racine du dépôt) :
    python verif_trad.py PROCEDURES.md docs\\en\\PROCEDURES.md
    python verif_trad.py ORIGINAL TRADUCTION --glossaire termes.json   (ajoute ou remplace des termes {"français": "anglais"})
    python verif_trad.py ORIGINAL TRADUCTION --details                  (montre tous les avertissements, pas seulement les 15 premiers)

ERREUR (code de sortie 1) :
  - titres : même suite de niveaux (#, ##, ###...) ;
  - tableaux : même nombre de tableaux, de lignes et de colonnes par ligne ;
  - listes : même nombre d'éléments ;
  - blocs de code (```) et code en ligne (`...`) : même nombre ; ceux qui ne contiennent pas de français
    se retrouvent à l'identique ; dans ceux qui en contiennent (messages des outils, commentaires),
    les options (--xxx), noms de fichiers, chemins et nombres sont conservés ;
  - liens vers une adresse http(s) : tous conservés ;
  - glossaire : un terme de l'interface présent dans l'original a sa traduction dans le document traduit.
AVERTISSEMENT (code de sortie 0) :
  - liens internes (#ancre, .md) : à revoir, les ancres changent avec les titres traduits ;
  - lignes du texte traduit qui semblent encore en français ;
  - terme du glossaire moins souvent présent dans la traduction que dans l'original.
Outil de développement (comme gen_reference.py) : non fabriqué dans dist\\.
"""
import argparse, json, pathlib, re, sys
from collections import Counter

# Termes de l'interface (src/i18n/fr.json -> en.json). Clé : expression régulière française (sans accent de casse),
# valeur : expression régulière anglaise. Pluriels acceptés.
GLOSSAIRE = {
    r"portails?": r"portals?",
    r"arriv[ée]es?": r"arrivals?",
    r"promenade": r"walk",
    r"r[ée]glages": r"settings",
    r"pseudos?": r"nicknames?",
    r"visiteurs?": r"visitors?",
    r"vue globale": r"global view",
    r"cam[ée]ra libre": r"free camera",
    r"troisi[èe]me personne": r"third person",
    r"vue subjective": r"first person",
    r"liens? web": r"web links?",
    r"informations / [ée]tat": r"information / status",
    r"carte des mondes": r"world map",
    r"tuiles?": r"tiles?",
    r"vue d'ensemble": r"overview",
    r"coquille": r"shell",
    r"salons? de pr[ée]sence": r"presence rooms?",
    r"d[ée]clenchement": r"trigger",
    r"boussole": r"compass",
    r"voler / atterrir": r"fly / land",
    r"mer anim[ée]e": r"animated sea",
    r"capturer la souris": r"capture the mouse",
    r"zones?": r"zones?",
}

FR_MOTS = set("le la les des du une un et est sont pas dans avec pour cette ces depuis aux sur ou mais qui que "
              "rien carte nom taille sommets pieds dessous morceau retir lu fichier dossier sous raison tuile "
              "de liste aide ejecter bannir debannir absente".split())
FR_FORTS = FR_MOTS - set("le la les des du une un et est sont pas ou mais qui que de aux sur ces nom lu".split())   # un seul suffit
ACCENTS = re.compile(r"[àâçéèêëîïôûùüÿœÀÂÇÉÈÊËÎÏÔÛÙÜŒ]")
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE = re.compile(r"`([^`\n]+)`")
LIEN = re.compile(r"\[[^\]]*\]\(([^)\s]+)[^)]*\)")
JETON = re.compile(r"--[A-Za-z][\w-]*|[\w./\\-]+\.(?:py|json|jsonl|html|glb|md|oar|log|png|js|txt|ps1)\b|\b\d+(?:[.,]\d+)?\b")


def est_francais(t):
    if ACCENTS.search(t) or " : " in t:   # typographie française : espace avant le deux-points
        return True
    mots = re.findall(r"[a-zA-Z']+", t.lower())
    n = sum(1 for m in mots if m in FR_MOTS)
    return n >= 2 or any(m in FR_FORTS for m in mots) or (len(mots) == 1 and n == 1)


def analyser(texte):
    """découpe le document : titres, tableaux, éléments de liste, blocs de code, code en ligne, liens, prose"""
    r = {"titres": [], "tableaux": [], "listes": 0, "blocs": [], "inline": [], "liens": [], "prose": []}
    lignes = texte.replace("\r\n", "\n").split("\n")
    dans_bloc, bloc, tab = False, [], None
    for n, l in enumerate(lignes, 1):
        if FENCE.match(l):
            if dans_bloc:
                r["blocs"].append("\n".join(bloc))
                bloc = []
            dans_bloc = not dans_bloc
            continue
        if dans_bloc:
            bloc.append(l)
            continue
        s = l.strip()
        if s.startswith("|"):
            if tab is None:
                tab = []
                r["tableaux"].append(tab)
            tab.append(len([c for c in s.strip("|").split("|")]))
        else:
            tab = None
        m = re.match(r"^(#{1,6})\s", l)
        if m:
            r["titres"].append(len(m.group(1)))
        if re.match(r"^\s*([-*+]|\d+[.)])\s", l):
            r["listes"] += 1
        r["inline"] += INLINE.findall(l)
        r["liens"] += LIEN.findall(l)
        r["prose"].append((n, INLINE.sub("C", l)))   # "C" : garde « `x`: » distinct de « x : »
    if dans_bloc:
        r["blocs"].append("\n".join(bloc))
    return r


def jetons(textes):
    c = Counter()
    for t in textes:
        c.update(x.replace(",", ".") for x in JETON.findall(t))   # 0,5 = 0.5
    return c


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Compare un document français et sa traduction anglaise.")
    ap.add_argument("original")
    ap.add_argument("traduction")
    ap.add_argument("--glossaire", help="fichier JSON {\"regex française\": \"regex anglaise\"} ajouté au glossaire intégré")
    ap.add_argument("--details", action="store_true", help="tous les avertissements")
    a = ap.parse_args()
    gl = dict(GLOSSAIRE)
    if a.glossaire:
        gl.update(json.loads(pathlib.Path(a.glossaire).read_text(encoding="utf-8")))
    o = analyser(pathlib.Path(a.original).read_text(encoding="utf-8"))
    t = analyser(pathlib.Path(a.traduction).read_text(encoding="utf-8"))
    err, avert = [], []

    if o["titres"] != t["titres"]:
        err.append("titres : %d dans l'original, %d dans la traduction (ou niveaux dans un autre ordre)" % (len(o["titres"]), len(t["titres"])))
    if o["tableaux"] != t["tableaux"]:
        err.append("tableaux : lignes par tableau %s / %s" % ([len(x) for x in o["tableaux"]], [len(x) for x in t["tableaux"]]))
    if o["listes"] != t["listes"]:
        err.append("listes : %d éléments dans l'original, %d dans la traduction" % (o["listes"], t["listes"]))

    for nom, cle in (("blocs de code", "blocs"), ("code en ligne", "inline")):
        oo, tt = o[cle], t[cle]
        if len(oo) != len(tt):
            err.append("%s : %d dans l'original, %d dans la traduction" % (nom, len(oo), len(tt)))
        manquants = Counter(x for x in oo if not est_francais(x)) - Counter(tt)
        for x in manquants:
            err.append("%s absent ou modifié : %s" % (nom, x if len(x) < 120 else x[:117] + "..."))
        perdus = jetons([x for x in oo if est_francais(x)]) - jetons(tt)
        if perdus:
            err.append("%s traduits : jetons perdus (options, fichiers, nombres) : %s" % (nom, " ".join(sorted(perdus))))

    lo, lt = Counter(o["liens"]), Counter(t["liens"])
    for u in lo - lt:
        (err if u.startswith("http") else avert).append("lien absent : %s" % u)
    internes = sorted(set(u for u in lt if not u.startswith("http")))
    if internes:
        avert.append("liens internes à vérifier (ancres et noms de fichiers) : %s" % " ".join(internes))

    prose_o = "\n".join(x for _, x in o["prose"]).lower()
    prose_t = "\n".join(x for _, x in t["prose"]).lower()
    for fr, en in gl.items():
        n_o = len(re.findall(r"\b%s\b" % fr, prose_o))
        if not n_o:
            continue
        n_t = len(re.findall(r"\b%s\b" % en, prose_t))
        if n_t == 0:
            err.append("glossaire : « %s » (%d fois) n'a aucune traduction « %s »" % (fr, n_o, en))
        elif n_t < n_o:
            avert.append("glossaire : « %s » %d fois, « %s » %d fois" % (fr, n_o, en, n_t))

    restes = [n for n, x in t["prose"] if x.strip() and est_francais(x)]
    if restes:
        avert.append("%d ligne(s) qui semblent en français : %s" % (len(restes), " ".join(map(str, restes[:40]))))

    print("Original    : %s" % a.original)
    print("Traduction  : %s" % a.traduction)
    print("Structure   : %d titres, %d tableaux, %d éléments de liste, %d blocs de code, %d codes en ligne, %d liens"
          % (len(o["titres"]), len(o["tableaux"]), o["listes"], len(o["blocs"]), len(o["inline"]), len(o["liens"])))
    lim = None if a.details else 15
    for e in err[:lim]:
        print("ERREUR      : " + e)
    if lim and len(err) > lim:
        print("ERREUR      : ... %d autres (--details)" % (len(err) - lim))
    for w in avert[:lim]:
        print("AVERTISSEMENT : " + w)
    if lim and len(avert) > lim:
        print("AVERTISSEMENT : ... %d autres (--details)" % (len(avert) - lim))
    print("Résultat    : %s (%d erreur(s), %d avertissement(s))" % ("ÉCHEC" if err else "OK", len(err), len(avert)))
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
