#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tout.py : lance TOUS les tests du dossier tests, un par un (jamais deux en meme temps), et dit lesquels echouent.

  python .\\tests\\tout.py                   toute la suite
  python .\\tests\\tout.py --liste           montre ce qui serait lance, sans rien lancer
  python .\\tests\\tout.py --seulement REGEX ne lance que les tests dont le nom correspond (ex. : "pbr|mono|v52")
  python .\\tests\\tout.py --sauf REGEX      saute ceux dont le nom correspond
  python .\\tests\\tout.py --reprendre       ne relance pas les tests reussis lors du dernier passage (apres une correction)
  python .\\tests\\tout.py --arreter         s'arrete au premier echec
  python .\\tests\\tout.py --delai 600       limite par test, en secondes (defaut 1500)

Un test est en ECHEC si : son code de retour n'est pas 0 ; ou il affiche une ligne « [ECHEC] » meme avec le code 0 ; ou il depasse le delai (DELAI).
Il est SUSPECT s'il reussit mais affiche une trace d'erreur Python (« Traceback »). « partie(s) ignoree(s) » compte les lignes « [IGNORE] »
(un test qui saute une partie faute de navigateur, d'ecran ou de module) : ce n'est pas un echec, mais la partie n'a pas ete essayee.

Chaque test tourne en sortie non tamponnee (python -u pour ce seul processus) : le journal est dans l'ordre. Il ecrit sa sortie complete dans tests_logs\\NOM.log ; le resume est dans tests_logs\\resume.txt. Le dossier tests_logs est ignore par git.
Prerequis des tests eux-memes : voir docs\\fr\\DEVELOPPEMENT.md (Chromium et playwright, websockets, python build.py avant). Code de retour : 0 si tout passe, 1 sinon.
"""
import argparse, json, os, re, subprocess, sys, time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(errors="replace")
    except Exception:
        pass

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
AIDES = {"h37", "glbfab", "vider_tube", "tout"}          # modules d'aide importes par d'autres tests, et ce script : pas des tests
# Environnement UTF-8, comme au premier passage complet sous Windows (83 tests OK). Sans ces deux variables, neuf tests de plus echouent : un
# programme fils ecrit sa sortie dans l'encodage de la page de code de Windows (cp1252) ou en UTF-8 selon l'outil, et le test, qui la relit avec
# l'encodage par defaut, ne retrouve pas ses accents ; un outil peut aussi planter sur un caractere comme la fleche « → » quand sa sortie va dans
# un tube. Pour un test seul, sous Windows :   $env:PYTHONUTF8="1"; python .\tests\NOM.py
ENVIRONNEMENT = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
RX_ECHEC = re.compile(r"^\s*\[(ECHEC|ÉCHEC)\]", re.IGNORECASE | re.MULTILINE)
RX_IGNORE = re.compile(r"^\s*\[IGNORE\]", re.IGNORECASE | re.MULTILINE)


def duree(s):
    return f"{int(s // 60)} min {int(s % 60):02d} s" if s >= 60 else f"{s:.0f} s"


def lancer(chemin, delai, dossier_logs):
    """(statut, secondes, sortie, nb_ignores)"""
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, "-u", str(chemin)], cwd=str(RACINE), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=delai, env=ENVIRONNEMENT)
        sortie = r.stdout.decode("utf-8", "replace")
        statut = "OK" if r.returncode == 0 else "ECHEC"
        if r.returncode == 0 and RX_ECHEC.search(sortie):
            statut = "ECHEC"                                  # echec affiche mais code de retour 0
        elif r.returncode == 0 and "Traceback (most recent call last)" in sortie:
            statut = "SUSPECT"
    except subprocess.TimeoutExpired as e:
        sortie = (e.stdout or b"").decode("utf-8", "replace") + f"\n[DELAI] arrete apres {delai} s\n"
        statut = "DELAI"
    dossier_logs.mkdir(exist_ok=True)
    (dossier_logs / (chemin.stem + ".log")).write_text(sortie, encoding="utf-8", errors="replace")
    return statut, time.time() - t0, sortie, len(RX_IGNORE.findall(sortie))


def fin_de_sortie(sortie, n=14):
    """lignes [ECHEC] d'abord, puis le DERNIER bloc « Traceback » (jusqu'a 24 lignes) s'il y en a un, sinon la fin de la sortie"""
    lignes = [l for l in sortie.splitlines() if l.strip()]
    echecs = [l for l in lignes if RX_ECHEC.match(l)]
    trace = [i for i, l in enumerate(lignes) if l.startswith("Traceback (most recent call last)")]
    if trace:
        bloc = lignes[trace[-1]:trace[-1] + 24]
    else:
        bloc = [l for l in lignes if l not in echecs][-max(3, n - len(echecs)):]
    return echecs[:8] + ([""] if echecs else []) + bloc


def main():
    ap = argparse.ArgumentParser(description="Lance tous les tests, un par un, et resume les echecs (voir l'en-tete du script).")
    ap.add_argument("--dossier", default=str(ICI), help="dossier des tests (defaut : celui de ce script)")
    ap.add_argument("--liste", action="store_true", help="montre la liste sans rien lancer")
    ap.add_argument("--seulement", help="expression reguliere : ne lance que les tests dont le nom correspond")
    ap.add_argument("--sauf", help="expression reguliere : saute les tests dont le nom correspond")
    ap.add_argument("--reprendre", action="store_true", help="saute les tests reussis lors du dernier passage")
    ap.add_argument("--arreter", action="store_true", help="s'arrete au premier echec")
    ap.add_argument("--delai", type=int, default=1500, help="limite par test, en secondes (defaut 1500)")
    a = ap.parse_args()
    dossier = Path(a.dossier).resolve()
    logs = RACINE / "tests_logs"
    tests = sorted(p for p in dossier.glob("*.py") if p.stem not in AIDES)
    if a.seulement:
        rx = re.compile(a.seulement, re.IGNORECASE)
        tests = [p for p in tests if rx.search(p.stem)]
    if a.sauf:
        rx = re.compile(a.sauf, re.IGNORECASE)
        tests = [p for p in tests if not rx.search(p.stem)]
    precedents = {}
    fichier_prec = logs / "derniers.json"
    if a.reprendre and fichier_prec.exists():
        try:
            precedents = json.loads(fichier_prec.read_text(encoding="utf-8"))
        except Exception:
            precedents = {}
    if a.liste:
        for p in tests:
            print(p.stem + ("   (reussi au dernier passage : saute avec --reprendre)" if a.reprendre and precedents.get(p.stem) == "OK" else ""))
        print(f"{len(tests)} test(s) dans {dossier}")
        return 0
    if not tests:
        print("Aucun test a lancer.")
        return 1
    logs.mkdir(exist_ok=True)
    (logs / ".gitignore").write_text("*\n", encoding="ascii")      # le dossier se cache lui-meme de git
    print(f"{len(tests)} test(s), un par un, delai {a.delai} s chacun ; sorties completes dans {logs}")
    print("Ctrl+C arrete proprement et donne le resume de ce qui a deja tourne.\n", flush=True)
    resultats, debut = [], time.time()
    resultats_json = dict(precedents)
    try:
        for i, p in enumerate(tests, 1):
            if a.reprendre and precedents.get(p.stem) == "OK":
                print(f"[{i:3d}/{len(tests)}] {p.stem:<28} saute (reussi au dernier passage)", flush=True)
                continue
            print(f"[{i:3d}/{len(tests)}] {p.stem:<28} ...", end=" ", flush=True)
            statut, s, sortie, ign = lancer(p, a.delai, logs)
            note = f" ; {ign} partie(s) ignoree(s)" if ign else ""
            print(f"{statut:<7} {duree(s)}{note}", flush=True)
            resultats.append((p.stem, statut, s, ign, sortie))
            resultats_json[p.stem] = "OK" if statut == "OK" else statut
            fichier_prec.write_text(json.dumps(resultats_json, indent=1), encoding="utf-8")
            if a.arreter and statut != "OK":
                print("--arreter : arret au premier echec.")
                break
    except KeyboardInterrupt:
        print("\nInterrompu par Ctrl+C.")
    total = time.time() - debut
    mauvais = [r for r in resultats if r[1] != "OK"]
    ignores = [r for r in resultats if r[3]]
    lignes = ["", "=" * 70, f"RESUME : {len(resultats)} test(s) lance(s) en {duree(total)} : {len(resultats) - len(mauvais)} OK, {len(mauvais)} a regarder"]
    if ignores:
        lignes.append(f"{len(ignores)} test(s) ont saute une partie ([IGNORE]) : " + ", ".join(f"{r[0]} ({r[3]})" for r in ignores))
    for nom, statut, s, ign, sortie in mauvais:
        etiquette = statut + (" (trace d'erreur affichee alors que le test se dit reussi)" if statut == "SUSPECT" else "")
        lignes += ["", f"--- {etiquette} : {nom}  ({duree(s)})   journal : {logs / (nom + '.log')}"] + ["    " + l[:200] for l in fin_de_sortie(sortie)]
    if not mauvais:
        lignes.append("TOUT PASSE")
    texte = "\n".join(lignes)
    print(texte)
    (logs / "resume.txt").write_text(texte + "\n", encoding="utf-8", errors="replace")
    print(f"\nResume enregistre : {logs / 'resume.txt'}")
    return 1 if mauvais else 0


if __name__ == "__main__":
    sys.exit(main())
