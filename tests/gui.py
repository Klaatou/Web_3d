#!/usr/bin/env python3
"""Test 1.7.14 puis 1.7.17 : web3d_gui.py, lanceur graphique des outils (dist/web3d_gui.py).

Sans fenetre : les options sont lues dans glb2html.py ; chaque option donne une ligne de commande que le vrai parseur de glb2html.py accepte (toutes, une par une) ;
valeurs : drapeau, oui/non, choix, nombre a virgule, valeur negative, argument sans nom, option sans valeur ; verification des champs.
Avec fenetre (tkinter et un ecran, par exemple xvfb-run) : une ligne par option, ligne de commande, filtre, aide au survol, lancement de l'outil et sortie.
Sans tkinter ou sans ecran, la partie fenetre est ignoree (dit clairement). Prerequis : python build.py avant. Lancer : python tests/gui.py
"""
import argparse, contextlib, importlib.util, io, os, pathlib, sys, time
os.environ["WEB3D_LANG"] = "en"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)[:400]))


spec = importlib.util.spec_from_file_location("web3d_gui", DIST / "web3d_gui.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
chemin = DIST / "glb2html.py"
parser = g.lire_parser(chemin, "en")
rapport(parser is not None, "les options sont lues dans glb2html.py")
champs = g.champs_depuis(parser)
vues = {o for c in champs for o in c["options"]}
attendues = {o for a in parser._actions for o in a.option_strings if o not in ("-h", "--help", "--version", "--lang")}
rapport(vues == attendues, "chaque option de glb2html.py a sa ligne, aucune en trop", sorted(vues ^ attendues)[:6])
rapport(sum(c["positionnel"] for c in champs) >= 1 and champs[0]["positionnel"], "l'argument sans nom (le GLB) est la premiere ligne")
genres = {c["genre"] for c in champs}
rapport({"flag", "tri", "choix", "nombre", "chemin", "texte", "facultatif"} <= genres, "tous les genres de champ sont representes", sorted(genres))
rapport(all(c["aide"] for c in champs), "chaque option a un texte d'aide", [c["dest"] for c in champs if not c["aide"]])


def accepte(argv, p=None):
    try:
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            (p or parser).parse_args(argv)
        return True
    except SystemExit:
        return False


# chaque option, seule, avec une valeur d'essai : le parseur de l'outil doit accepter la ligne
refus = []
for c in champs:
    gen = c["genre"]
    if gen == "flag":
        vals = [True]
    elif gen == "tri":
        vals = ["yes", "no"]
    elif gen == "choix":
        vals = c["choix"][:1]
    elif gen == "facultatif":
        vals = [("", True), ("essai", False)]
    else:
        vals = [c["defaut"] or ("1" if gen == "nombre" else "essai")]
    for v in vals:
        argv = g.construire([c], {c["dest"]: v})
        if not argv or not accepte(argv):
            refus.append((c["dest"], v, argv))
rapport(not refus, f"les {len(champs)} options, une par une : ligne acceptee par le vrai parseur de glb2html.py", refus[:3])

# tous les outils de la liste : chaque option, seule (avec les arguments obligatoires), est acceptee par le vrai parseur de son outil
for nom_outil, fichier in g.OUTILS:
    p = g.lire_parser(DIST / fichier, "en")
    rapport(p is not None, f"{fichier} : les options sont lues")
    if p is None:
        continue
    cs = g.champs_depuis(p)
    vus_o = {o for c in cs for o in c["options"]}
    att_o = {o for a in p._actions for o in a.option_strings if o not in ("-h", "--help", "--version", "--lang")}
    rapport(vus_o == att_o, f"{fichier} : chaque option a sa ligne, aucune en trop", sorted(vus_o ^ att_o)[:6])
    base = {c["dest"]: "x" for c in cs if c["obligatoire"]}
    refus_o = []
    for c in cs:
        gen = c["genre"]
        if gen == "flag":
            vals = [True]
        elif gen == "tri":
            vals = ["yes", "no"]
        elif gen == "choix":
            vals = c["choix"][:1]
        elif gen == "facultatif":
            vals = [("", True), ("essai", False)]
        else:
            vals = [c["defaut"] or ("1" if gen == "nombre" else "12" if gen == "multiple" else "essai")]
        for v in vals:
            argv = g.construire(cs, dict(base, **{c["dest"]: v}))
            if not accepte(argv, p):
                refus_o.append((c["dest"], v, argv))
    rapport(not refus_o, f"{fichier} : les {len(cs)} options, une par une : ligne acceptee par le vrai parseur", refus_o[:3])

par = {c["dest"]: c for c in champs}
sp = par["spectate"]
rapport(g.defaut_dans_aide(sp) and g.defaut_dans_aide(par["output"]) and not g.defaut_dans_aide(par["zones"]) and not g.defaut_dans_aide(par["walk"]),
        "defaut decrit dans l'aide (--spectate, -o) signale ; pas de faux signalement")
rapport("see the text above" in g.texte_aide(sp) and "no default" not in g.texte_aide(sp), "texte d'aide : « voir le texte ci-dessus » quand l'aide decrit le defaut", g.texte_aide(sp)[-120:])
sel = [par[d] for d in ("input", "walk", "rotate", "sea_y", "zones_only", "settings", "zone_info_dist", "hole")]
args = g.construire(sel, {"input": "a b.glb", "walk": "no", "rotate": "90", "sea_y": "-12,5", "zones_only": True, "settings": ("", True), "hole": "  "})
rapport(args[0] == "a b.glb" and "--no-walk" in args and "--sea-y=-12.5" in args and "--settings" in args and "--zones-only" in args and "--hole" not in args and args[args.index("--rotate") + 1] == "90",
        "construire : positionnel d'abord, oui/non, virgule decimale, valeur negative, option seule, champ vide ignore", args)
rapport(g.construire(champs, {}) == [], "aucun champ touche : aucune option ecrite")
rapport(g.construire([par["walk"]], {"walk": "yes"}) == ["--walk"], "oui : l'option")
pb = g.verifier(champs, {"rotate": "45", "hole": "abc", "zoom": "1,5"})
rapport(len(pb) == 2 and {d for d, _t in pb} == {"rotate", "hole"}, "verifier : choix hors liste et nombre illisible signales, virgule acceptee", pb)
rapport("python glb2html.py" in g.ligne_commande("glb2html.py", ["x.glb"]), "la ligne affichee commence par python glb2html.py")
rapport("--walk" in g.texte_aide(par["walk"]) and "default" in g.texte_aide(par["walk"]), "texte d'aide : option, aide, valeur par defaut")

# ------------------------------------------------------------- avec fenetre
try:
    import tkinter as tk
    from tkinter import ttk, filedialog
    racine = tk.Tk()
    racine.destroy()
except Exception as e:
    print(f"[IGNORE] partie fenetre : pas de tkinter ou pas d'ecran ({type(e).__name__}) ; lancer avec xvfb-run pour la faire")
    print("\nRESULTAT :", "tout est passe" if not bad else f"{bad} echec(s)")
    sys.exit(1 if bad else 0)

f = g.fenetre([(n, DIST / fn) for n, fn in g.OUTILS], tk, ttk, filedialog)
r = f.root
r.update()
rapport(len(f.lignes) == len(champs), "la fenetre a une ligne par option", (len(f.lignes), len(champs)))
rapport(f.cmd.get("1.0", "end").strip() == "python glb2html.py", "au depart la commande est vide d'options", f.cmd.get("1.0", "end"))
f.vars["input"].set("C:/regions/Atoll.glb")
f.vars["zones_only"].set(True)
f.vars["walk"].set("no")
f.vars["sea_y"].set("-5,5")
r.update()
rapport(f.cmd.get("1.0", "end").strip() == "python glb2html.py C:/regions/Atoll.glb --zones-only --sea-y=-5.5 --no-walk", "la commande suit les champs", f.cmd.get("1.0", "end"))
f.vars["rotate"].set("45")
r.update()
rapport(f.lignes["rotate"][0].cget("text") == "!", "une valeur a corriger est marquee d'un signe (pas par la couleur)")
f.vars["rotate"].set("")
r.update()
rapport(f.lignes["rotate"][0].cget("text").strip() == "", "le signe disparait quand c'est corrige")
f.filtre.set("sea-")
r.update()
visibles = [d for d, (m, cases) in f.lignes.items() if cases[1].winfo_manager()]
rapport(0 < len(visibles) < len(champs) and all("sea" in d for d in visibles), "le filtre ne garde que les options qui correspondent", visibles)
f.filtre.set("")
r.update()
rapport(len([1 for d, (m, cases) in f.lignes.items() if cases[1].winfo_manager()]) == len(champs), "filtre vide : toutes les options reviennent")
etiq = f.lignes["walk"][1][1]
etiq.event_generate("<Enter>")
r.update()
rapport("--walk" in f.aide.get("1.0", "end") and "default" in f.aide.get("1.0", "end"), "l'aide de l'option s'affiche au survol", f.aide.get("1.0", "end"))
# lancement reel de l'outil : une entree introuvable doit donner un message et un code de retour
f.vars["zones_only"].set(False)
f.vars["walk"].set("(default)")
f.vars["input"].set("inexistant-xyz.glb")
r.update()
f.lancer()
fin = time.time() + 60
while f.proc is not None and time.time() < fin:
    r.update()
    time.sleep(0.05)
for _ in range(10):
    r.update()
sortie = f.sortie.get("1.0", "end")
rapport(f.proc is None and "return code" in f.etat.cget("text"), "l'outil est lance, le code de retour s'affiche", f.etat.cget("text"))
rapport(sortie.startswith("> python glb2html.py inexistant-xyz.glb") and "not found" in sortie.lower(), "la sortie de l'outil s'affiche dans la fenetre", sortie[:300])
f.vars["sea_y"].set("abc")
r.update()
f.lancer()
rapport(f.proc is None and "!" in f.etat.cget("text") and "sea-y" in f.etat.cget("text"), "un champ illisible empeche le lancement et le dit", f.etat.cget("text"))
# changer d'outil : lignes refaites, option repetable (une ligne = une repetition)
rapport(f.changer("extraire_batiments") and f.chemin.name == "extraire_batiments.py" and len(f.lignes) == len(f.champs) > 5, "la liste d'outils change l'outil affiche", (f.chemin.name, len(f.lignes)))
grp = next(c for c in f.champs if "--group" in c["options"])
f.vars[grp["dest"]].set("12\n15,18\n\n")
f.vars[next(c["dest"] for c in f.champs if "--list" in c["options"])].set(True)
r.update()
cmd = f.cmd.get("1.0", "end").strip()
rapport(cmd == "python extraire_batiments.py --list --group 12 --group 15,18", "option repetable : une ligne, une repetition ; ligne vide ignoree", cmd)
rapport(f.changer("glb2html") and len(f.lignes) == len(champs) and f.cmd.get("1.0", "end").strip() == "python glb2html.py", "retour a glb2html : options remises a zero")
r.destroy()
print("\nRESULTAT :", "tout est passe" if not bad else f"{bad} echec(s)")
sys.exit(1 if bad else 0)
