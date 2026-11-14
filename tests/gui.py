#!/usr/bin/env python3
"""Test 1.7.14 puis 1.7.17 : web3d_gui.py, lanceur graphique des outils (dist/web3d_gui.py).

Sans fenetre : les options sont lues dans glb2html.py ; chaque option donne une ligne de commande que le vrai parseur de glb2html.py accepte (toutes, une par une) ;
valeurs : drapeau, oui/non, choix, nombre a virgule, valeur negative, argument sans nom, option sans valeur ; verification des champs.
Exemples (1.8.17) : chaque exemple de chaque outil est accepte par le vrai parseur de son outil, a un titre en francais et en anglais, et lire_exemple puis construire donnent la meme analyse que l'exemple.
Avec fenetre (tkinter et un ecran, par exemple xvfb-run) : une ligne par option, ligne de commande, filtre, aide au survol, lancement de l'outil et sortie, liste d'exemples.
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
genres_outil = {}
for nom_outil, fichier in g.OUTILS:
    p = g.lire_parser(DIST / fichier, "en")
    rapport(p is not None, f"{fichier} : les options sont lues")
    if p is None:
        continue
    cs = g.champs_depuis(p)
    vus_o = {o for c in cs for o in c["options"]}
    att_o = {o for a in p._actions for o in a.option_strings if o not in ("-h", "--help", "--version", "--lang")}
    rapport(vus_o == att_o, f"{fichier} : chaque option a sa ligne, aucune en trop", sorted(vus_o ^ att_o)[:6])
    genres_outil[fichier] = {c["dest"]: c["genre"] for c in cs}
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

chemins_attendus = [("glb2html.py", "input"), ("glb2html.py", "output"), ("glb2tiles.py", "glb"), ("glb2tiles.py", "sortie"), ("oar2glb.py", "oar"), ("oar2glb.py", "convoar"),
                    ("oar2glb.py", "sortie"), ("extraire_batiments.py", "oar"), ("extraire_batiments.py", "glb"), ("extraire_batiments.py", "sortie"), ("iar2oar.py", "iar"),
                    ("glb2html.py", "water_from"), ("oar2glb.py", "terrain_seul"), ("oar2glb.py", "tex_seul")]      # 1.10.30 : metavars OAR et GLB
sans_boutons = [(f, d, genres_outil.get(f, {}).get(d)) for f, d in chemins_attendus if genres_outil.get(f, {}).get(d) != "chemin"]
rapport(not sans_boutons, "les champs fichier ou dossier (entrees, sorties, convoar) ont les boutons Fichier et Dossier", sans_boutons)
# 1.10.30 : la decision des boutons Fichier / Dossier (a_boutons_fichier) est la meme que le genre ; --lib-url (PATH, accepte une adresse web) reste un champ texte
boutons = {}
for nom_outil, fichier in g.OUTILS:
    p_o = g.lire_parser(DIST / fichier, "en")
    for c in (g.champs_depuis(p_o) if p_o is not None else []):
        boutons[(fichier, c["dest"])] = g.a_boutons_fichier(c)
rapport(all(boutons.get(k) for k in [("glb2html.py", "water_from"), ("oar2glb.py", "terrain_seul"), ("oar2glb.py", "tex_seul"), ("glb2html.py", "input")]),
        "--water-from, --terrain-only, --tex-only et l'entree de glb2html ont les boutons Fichier et Dossier", {k: v for k, v in boutons.items() if k[1] in ("water_from", "terrain_seul", "tex_seul")})
seuls = {k: g.fichier_seul(c) for nom_outil, fichier in g.OUTILS for c in (g.champs_depuis(g.lire_parser(DIST / fichier, "en")) or []) for k in [(fichier, c["dest"])]}
rapport(all(seuls.get(k) for k in [("glb2html.py", "water_from"), ("oar2glb.py", "terrain_seul"), ("oar2glb.py", "tex_seul")])
        and not any(seuls.get(k) for k in [("glb2html.py", "output"), ("oar2glb.py", "sortie"), ("oar2glb.py", "convoar")]),
        "1.10.31 : --water-from, --terrain-only et --tex-only n'ont que le bouton Fichier ; les sorties et convoar gardent Fichier et Dossier",
        {k: v for k, v in seuls.items() if k[1] in ("water_from", "terrain_seul", "tex_seul", "output", "sortie", "convoar")})
rapport(not boutons.get(("glb2html.py", "lib_url")) and not boutons.get(("glb2html.py", "title")) and not boutons.get(("glb2tiles.py", "exclude")),
        "--lib-url (PATH), --title et --exclude restent des champs sans boutons", [k for k in (("glb2html.py", "lib_url"), ("glb2html.py", "title"), ("glb2tiles.py", "exclude")) if boutons.get(k)])
rapport(all(not g.a_boutons_fichier(c) for c in champs if c["genre"] in ("flag", "tri", "choix", "nombre")), "aucun drapeau, choix ou nombre n'a de boutons Fichier et Dossier")
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

# ------------------------------------------------------------- 1.9.17 : sans console (pythonw.exe), et outil qui plante avant son parse_args
# Les raccourcis du lanceur utilisent pythonw.exe : pas de console, sys.__stdout__ et sys.__stderr__ valent None. oar2glb.py doublait
# sys.__stdout__ dans son journal et plantait a sa premiere ligne affichee : le lanceur ne pouvait pas ouvrir ses options.
_so, _se = sys.__stdout__, sys.__stderr__
sans = []
for _nom, _fichier in g.OUTILS:
    sys.__stdout__ = sys.__stderr__ = None
    try:
        _p = g.lire_parser(DIST / _fichier, "en")
    except BaseException as _e:
        _p, g.lire_parser.erreur = None, repr(_e)
    finally:
        sys.__stdout__, sys.__stderr__ = _so, _se
    if _p is None:
        sans.append((_fichier, getattr(g.lire_parser, "erreur", "")))
rapport(not sans, "sans console (pythonw.exe) : les options de chaque outil sont lues", sans)
import tempfile
with tempfile.TemporaryDirectory() as _d:
    _faux = pathlib.Path(_d) / "outil_casse.py"
    _faux.write_text("raise RuntimeError('boum')\n", encoding="ascii")
    _p = g.lire_parser(_faux, "en")
    rapport(_p is None and "RuntimeError" in g.lire_parser.erreur and "boum" in g.lire_parser.erreur,
            "outil qui plante avant son parse_args : pas d'exception dans le lanceur, raison gardee pour le message", (_p, g.lire_parser.erreur))
rapport(g.lire_parser(DIST / "glb2html.py", "en") is not None and g.lire_parser.erreur == "", "lecture reussie ensuite : raison remise a vide")

# ------------------------------------------------------------- exemples d'usages de base (sans fenetre)
rapport(set(g.EXEMPLES) == {n for n, _f in g.OUTILS} and all(len(v) >= 2 for v in g.EXEMPLES.values()), "chaque outil de la liste a au moins 2 exemples, aucun exemple pour un outil inconnu", sorted(g.EXEMPLES))
def titre(code, cle):
    return g._DATA[code].get(cle)
sans_titre = [(c, k) for v in g.EXEMPLES.values() for k, _a in v for c in ("fr", "en") if not titre(c, k)]
rapport(not sans_titre, "chaque exemple a un titre en francais et en anglais", sans_titre[:4])
rapport(len({titre("en", k) for v in g.EXEMPLES.values() for k, _a in v}) == sum(len(v) for v in g.EXEMPLES.values()), "les titres d'exemples sont tous differents")
mauvais, reflet = [], []
for nom_outil, fichier in g.OUTILS:
    p_o = g.lire_parser(DIST / fichier, "en")
    cs_o = g.champs_depuis(p_o)
    for cle, args in g.EXEMPLES[nom_outil]:
        if not accepte(args, p_o):
            mauvais.append((fichier, cle, args))
            continue
        try:
            retour = g.construire(cs_o, g.lire_exemple(cs_o, args))
        except ValueError as e:
            mauvais.append((fichier, cle, str(e)))
            continue
        with contextlib.redirect_stderr(io.StringIO()):
            if vars(p_o.parse_args(args)) != vars(p_o.parse_args(retour)):
                reflet.append((fichier, cle, args, retour))
rapport(not mauvais, "les exemples de tous les outils sont acceptes par le vrai parseur de leur outil", mauvais[:3])
rapport(not reflet, "lire_exemple puis construire redonnent la meme analyse que l'exemple (tous les outils)", reflet[:2])
cs_h = champs
rapport(g.lire_exemple(cs_h, ["a.glb", "--no-sea", "--shared-shell", "-o", "a.html", "--sea-y=-3", "--hole", "90"]) == {"input": "a.glb", "sea_enabled": "no", "shared_shell": ("", True), "output": "a.html", "sea_y": "-3", "hole": "90"},
        "lire_exemple : positionnel, non, option seule, valeur negative, valeur")
cs_e = g.champs_depuis(g.lire_parser(DIST / "extraire_batiments.py", "en"))
rapport(g.lire_exemple(cs_e, ["a.oar", "a.glb", "--group", "12", "--group", "15", "--merge", "M G"])["groupe"] == "12\n15" and g.lire_exemple(cs_e, ["a.oar", "a.glb"]) == {"oar": "a.oar", "glb": "a.glb"},
        "lire_exemple : option repetable sur plusieurs lignes, deux arguments sans nom dans l'ordre")
refus_le = []
for mauvais_args in (["a.glb", "--inconnue"], ["--hole"], ["a.glb", "b.glb"]):
    try:
        g.lire_exemple(cs_h, mauvais_args)
        refus_le.append(mauvais_args)
    except ValueError:
        pass
rapport(not refus_le, "lire_exemple : option inconnue, valeur manquante, argument en trop : ValueError", refus_le)

# ------------------------------------------------------------- raccourcis (les .lnk ne se creent que sous Windows : ici, le plan, le script PowerShell et la suppression)
import tempfile
dos = pathlib.Path(tempfile.mkdtemp(prefix="w3d_rac_"))
prevus = g.raccourcis_prevus(dos)
rapport(len(prevus) == 1 + len(g.OUTILS) and prevus[0][0].name == "Web_3d - launcher.lnk" and prevus[1][1][1:] == ["--tool", g.OUTILS[0][0]] and prevus[0][1][1:] == [],
        "raccourcis prevus : un pour la fenetre, un par outil, avec --tool", [(p.name, a[1:]) for p, a in prevus][:3])
ps = g.script_powershell([(pathlib.Path("C:/Bureau d'Anne/x.lnk"), ["C:/a b/web3d_gui.py", "--tool", "glb2html"])], "C:/Python 3/pythonw.exe", "C:/a b")
rapport("Bureau d''Anne" in ps and "$s.Arguments = '\"C:/a b/web3d_gui.py\" --tool glb2html'" in ps and "$s.TargetPath = 'C:/Python 3/pythonw.exe'" in ps and ps.count("$s.Save()") == 1 and "\r\n" in ps,
        "script PowerShell : apostrophe doublee, arguments entre guillemets, un Save par raccourci", ps)
ps_i = g.script_powershell([(pathlib.Path("C:/x.lnk"), ["C:/a/web3d_gui.py"])], "C:/P/pythonw.exe", "C:/a", "C:/a b/favicon.ico")
rapport("$s.IconLocation = 'C:/a b/favicon.ico,0'" in ps_i and ps_i.index("IconLocation") < ps_i.index("$s.Save()") and "IconLocation" not in ps, "script PowerShell : l'icone du projet est posee avant Save, et seulement si elle existe", ps_i)


def lance(*args):
    tampon = io.StringIO()
    with contextlib.redirect_stdout(tampon):
        code = g.main(list(args))
    return code, tampon.getvalue()


code, sortie_rac = lance("--shortcuts", "--dry-run", "--shortcuts-folder", str(dos))
rapport(code == 0 and sortie_rac.count("would be created:") == len(prevus) and not list(dos.glob("*.lnk")), "--shortcuts --dry-run : montre le plan, ne cree rien", (code, sortie_rac[:200]))
rapport("shortcut icon:" in sortie_rac and "favicon.ico" in sortie_rac, "--dry-run : dit quelle icone sera utilisee (favicon.ico de dist)", sortie_rac[:160])
if os.name != "nt":
    code, sortie_rac = lance("--shortcuts", "--shortcuts-folder", str(dos))
    rapport(code == 2 and not list(dos.glob("*.lnk")) and "only be created on Windows" in sortie_rac, "hors Windows : refus clair (code 2), rien d'ecrit", (code, sortie_rac[:200]))
for nom in ("Web_3d - launcher.lnk", "Web_3d - glb2html.lnk", "autre.lnk"):
    (dos / nom).write_text("x")
code, sortie_rac = lance("--remove-shortcuts", "--dry-run", "--shortcuts-folder", str(dos))
rapport(code == 0 and sortie_rac.count("would be removed") == 2 and len(list(dos.glob("*.lnk"))) == 3, "--remove-shortcuts --dry-run : rien n'est supprime", (code, sortie_rac[:200]))
code, sortie_rac = lance("--remove-shortcuts", "--shortcuts-folder", str(dos))
rapport(code == 0 and sorted(x.name for x in dos.glob("*.lnk")) == ["autre.lnk"], "--remove-shortcuts : seuls les raccourcis de web3d_gui sont supprimes", (code, sorted(x.name for x in dos.glob("*.lnk"))))

# ------------------------------------------------------------- avec fenetre
def sans_fenetre(e):
    print(f"[IGNORE] partie fenetre : pas de tkinter ou pas d'ecran ({type(e).__name__}) ; lancer avec xvfb-run pour la faire")
    print("\nRESULTAT :", "tout est passe" if not bad else f"{bad} echec(s)")
    sys.exit(1 if bad else 0)


# une seule fenetre Tk : pas de fenetre d'essai ouverte puis detruite avant (sous Windows, une tache de theme en attente s'executait ensuite : erreur Tcl « application has been destroyed »)
try:
    import tkinter as tk
    from tkinter import ttk, filedialog
except ImportError as e:
    sans_fenetre(e)
try:
    f = g.fenetre([(n, DIST / fn) for n, fn in g.OUTILS], tk, ttk, filedialog)
except tk.TclError as e:
    if "display" not in str(e).lower():      # une vraie erreur de la fenetre ne se confond pas avec l'absence d'ecran
        raise
    sans_fenetre(e)
r = f.root
r.update()
# ------------------------------------------------------------- 1.10.3 : icone du projet donnee a la fenetre
ico = g.trouver_icone()
rapport(ico is not None and ico.name == "favicon.ico", "l'icone du projet (favicon.ico) est trouvee a cote de web3d_gui.py", ico)
try:
    import PIL
    pil = True
except ImportError:
    pil = False
if sys.platform.startswith("win") or pil:
    rapport(g.appliquer_icone(r) is True and (sys.platform.startswith("win") or hasattr(r, "_icone_img")), "l'icone est appliquee a la fenetre (iconbitmap sous Windows, iconphoto avec Pillow ailleurs)")
else:
    print("[IGNORE] icone de la fenetre : Pillow absent (pip install pillow), seule l'icone par defaut reste")
_vrai = g.trouver_icone
g.trouver_icone = lambda: None
rapport(g.appliquer_icone(r) is False, "icone introuvable : False, la fenetre s'ouvre quand meme")
g.trouver_icone = _vrai
rapport(g.appliquer_icone(type("Fenetre", (), {})()) is False, "fenetre sans iconbitmap ni iconphoto : False, pas d'erreur")
rapport("glb-stats" in {n for n, _f in g.OUTILS} and g.trouver_outil("glb-stats.py") is not None, "glb-stats est dans la liste des outils et se trouve a cote du lanceur")
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
# liste d'exemples : choisir un exemple remplit les champs, la commande affichee est celle de l'exemple (tous les outils)
rapport(bool(f.liste_ex) and str(f.choix_exemple.cget("state")) == "readonly" and len(f.choix_exemple.cget("values")) == len(g.EXEMPLES["glb2html"]) and "basic" in f.exemple.get().lower(),
        "la liste d'exemples propose ceux de l'outil et invite a choisir", (f.exemple.get(), len(f.liste_ex)))
ecart = []
for nom_outil, fichier in g.OUTILS:
    f.changer(nom_outil)
    r.update()
    f.vars[next(iter(f.vars))].set("residu-a-effacer") if f.champs[0]["genre"] in ("chemin", "texte") else None
    for i, (cle, args) in enumerate(g.EXEMPLES[nom_outil]):
        f.choix_exemple.current(i)
        f.choix_exemple.event_generate("<<ComboboxSelected>>")
        r.update()
        affichee = f.cmd.get("1.0", "end").strip()
        import shlex
        morceaux = shlex.split(affichee)
        p_o = g.lire_parser(DIST / fichier, "en")
        with contextlib.redirect_stderr(io.StringIO()):
            ok = morceaux[:2] == ["python", fichier] and vars(p_o.parse_args(morceaux[2:])) == vars(p_o.parse_args(args))
        if not ok or "residu" in affichee or "!" in "".join(m.cget("text") for m, _c in f.lignes.values()):
            ecart.append((fichier, cle, affichee))
rapport(not ecart, "choisir un exemple (les 6 outils, tous les exemples) : la commande affichee equivaut a l'exemple, le champ touche avant est efface, aucun champ a corriger", ecart[:2])
f.changer("glb2html")
f.choix_exemple.current(2)
f.choix_exemple.event_generate("<<ComboboxSelected>>")
r.update()
rapport(f.vars["sea_enabled"].get() == "(default)" and f.vars["shared_shell"][1].get() is True and f.vars["presence_url"].get() == "ws://ADRESSE:8765" and "Example loaded." == f.etat.cget("text") and "Replace the example names" in f.aide.get("1.0", "end"),
        "un exemple remplit les champs (option seule cochee, texte), dit qu'il est charge et que les noms sont a remplacer", (f.etat.cget("text"), f.aide.get("1.0", "end")[:120]))
f.choix_exemple.current(4)
f.choix_exemple.event_generate("<<ComboboxSelected>>")
r.update()
rapport(f.vars["sea_enabled"].get() == "no" and f.vars["presence_url"].get() == "" and f.vars["shared_shell"][1].get() is False, "un autre exemple efface le precedent puis remplit : oui/non, champs vides", (f.vars["sea_enabled"].get(), f.vars["presence_url"].get()))
# ------------------------------------------------------------- 1.10.4 : la fonction principale de l'outil s'affiche
import re as _re
vues = {}
for nom_outil, fichier in g.OUTILS:
    f.changer(nom_outil)
    r.update()
    vues[nom_outil] = f.fonction.cget("text")
rapport(all(t.startswith("Function: ") and len(t) > 40 for t in vues.values()), "chaque outil affiche sa fonction principale sous le choix de l'outil", {k: v[:50] for k, v in vues.items() if not (v.startswith("Function: ") and len(v) > 40)})
rapport(not any(_re.search(r"empreinte|fingerprint|\d+\.\d+\.\d+ \(", t) for t in vues.values()), "la fonction n'a ni le numero de version ni l'empreinte du debut de la description", vues)
rapport(len(set(vues.values())) == len(vues), "chaque outil a sa propre fonction affichee", vues)
rapport(g.fonction_principale("") == "" and g.fonction_principale(None) == "" and g.fonction_principale("sans prefixe ni deux-points") == "sans prefixe ni deux-points"
        and g.fonction_principale("x.py 1.0.0 (01/01/2026), empreinte ab12 : fait ceci : et cela.") == "fait ceci : et cela.", "fonction_principale : vide, sans prefixe, et deux-points dans la phrase")
f.changer("diag_carte")
rapport(f.exemple.get() != "" and "glb2html" not in f.cmd.get("1.0", "end"), "changer d'outil remet la liste d'exemples a son invite", f.exemple.get())
r.destroy()
print("\nRESULTAT :", "tout est passe" if not bad else f"{bad} echec(s)")
sys.exit(1 if bad else 0)
