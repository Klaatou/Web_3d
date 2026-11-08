#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""web3d_gui.py : lanceur graphique des outils Web_3d (glb2html, glb2tiles, oar2glb, extraire_batiments, iar2oar, diag_carte).

Une liste pour choisir l'outil, puis une ligne par option, l'aide de l'option sous le curseur, la ligne de commande qui en résulte, un bouton pour lancer l'outil et sa sortie.
Les options sont lues dans l'outil lui-même (rien ne peut manquer, l'outil n'est pas modifié). Nécessite tkinter (livré avec Python sous Windows).
Tous les messages et l'aide : --lang fr|en|auto (python web3d_gui.py --help).
"""
import argparse, contextlib, io, os, queue, re, runpy, subprocess, sys, threading
from pathlib import Path

# <<I18N_PY>>
def _i18n_boot():   # depuis les sources : charge src/i18n_py.py ; fabriqué par build.py (dist\\) : ce bloc est remplacé par le texte de i18n_py.py avec les langues intégrées
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
_tr, i18n_add_common, I18N_LANG = _I18N._tr, _I18N.i18n_add_common, _I18N.I18N_LANG
# <</I18N_PY>>

VERSION = "__VERSION__"      # remplacé par build.py (fichier VERSION) dans dist/web3d_gui.py
MARK = "__MARK__"      # empreinte du fichier fabriqué, inscrite par build.py ; reste telle quelle depuis tools/

OUTILS = (("glb2html", "glb2html.py"), ("glb2tiles", "glb2tiles.py"), ("oar2glb", "oar2glb.py"), ("extraire_batiments", "extraire_batiments.py"),
          ("iar2oar", "iar2oar.py"), ("diag_carte", "diag_carte.py"))      # (nom, fichier) ; un outil de plus : une ligne ici
MOTS_CHEMIN = ("FILE", "FOLDER", "DIR")      # un métavar qui contient l'un de ces mots, ou qui finit par .html / .json : un fichier ou un dossier
DEST_CHEMIN = ("input", "o", "register", "thumb", "oar", "glb", "iar")      # arguments sans métavar qui sont des chemins


def version_tag():
    return VERSION if MARK.startswith("__") else _tr("py.common.version_mark", VERSION, MARK)


# ---------------------------------------------------------------- lecture des options de l'outil

def trouver_outil(fichier):
    """à côté de ce script, sinon dans le dossier dist voisin (quand le script est lancé depuis tools/)"""
    ici = Path(__file__).resolve().parent
    for p in (ici / fichier, ici.parent / "dist" / fichier):
        if p.is_file():
            return p
    return None


def lire_parser(chemin, langue=None):
    """exécute l'outil jusqu'à son parse_args, récupère le parser, n'exécute rien d'autre"""
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
    sys.argv = [str(chemin), "--help", "--nopause"]
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


def texte_defaut(a):
    d = a.default
    if d is None or d is argparse.SUPPRESS:
        return ""
    if isinstance(d, int) and not isinstance(d, bool) and "color" in a.dest:
        return f"{d:06x}"                                   # couleurs en hexadécimal, comme dans l'aide de l'outil
    if isinstance(d, (tuple, list)):
        return ", ".join(str(x) for x in d)
    return str(d)


def defaut_dans_aide(c):
    """vrai si l'option n'a pas de valeur par défaut chiffrée mais que son texte d'aide en parle (ex. --spectate : actif dès qu'une adresse de présence est donnée ; -o : « <nom> - Offline.html » à côté du .glb)"""
    return c["defaut"] == "" and bool(re.search(r"d[ée]faut|default", c["aide"] or "", re.I))


def champs_depuis(parser):
    """un champ (dictionnaire) par argument du parser, dans l'ordre de l'outil, sauf l'aide, la version et --lang"""
    res, vus = [], set()
    for a in parser._actions:
        if isinstance(a, (argparse._HelpAction, argparse._VersionAction)) or a.dest in ("help", "lang") or id(a) in vus:
            continue
        vus.add(id(a))
        mv = a.metavar if isinstance(a.metavar, str) else (" ".join(a.metavar) if a.metavar else "")
        opts = list(a.option_strings)
        if isinstance(a, argparse._AppendAction):
            genre = "multiple"
        elif isinstance(a, argparse.BooleanOptionalAction):
            genre = "tri"
        elif isinstance(a, (argparse._StoreTrueAction, argparse._StoreFalseAction)):
            genre = "flag"
        elif a.choices:
            genre = "choix"
        elif a.type is float or a.type is int:
            genre = "nombre"
        elif a.type is Path or any(k in mv.upper() for k in MOTS_CHEMIN) or mv.lower().endswith((".html", ".json")) or a.dest in DEST_CHEMIN:
            genre = "chemin"
        else:
            genre = "texte"
        if genre in ("texte", "chemin", "nombre", "choix") and opts and a.nargs == "?":
            genre = "facultatif" if genre != "choix" else genre
        res.append({"dest": a.dest, "options": opts, "genre": genre, "metavar": mv, "aide": a.help if a.help and a.help is not argparse.SUPPRESS else "",
                    "defaut": texte_defaut(a), "choix": [str(c) for c in a.choices] if a.choices else [], "positionnel": not opts,
                    "obligatoire": bool(getattr(a, "required", False)) or (not opts and a.nargs is None),
                    "nombre": "int" if a.type is int else "float" if a.type is float else "", "ptype": a.type is Path})
    return res


def texte_aide(c):
    t = "  /  ".join(c["options"]) if c["options"] else c["dest"]
    if c["metavar"] and c["genre"] not in ("flag", "tri"):
        t += " " + c["metavar"]
    t += "\n" + (c["aide"] or "")
    if c["positionnel"]:
        t += "\n" + _tr("py.gui.positional")
    if c["genre"] == "flag":
        t += "\n" + _tr("py.gui.flag_on")
    elif c["genre"] == "tri":
        t += "\n" + _tr("py.gui.tri_hint")
    elif c["genre"] == "facultatif":
        t += "\n" + _tr("py.gui.optional_value")
    elif c["genre"] == "multiple":
        t += "\n" + _tr("py.gui.multi_hint")
    if c["choix"]:
        t += "\n" + _tr("py.gui.choices", ", ".join(c["choix"]))
    t += "\n" + (_tr("py.gui.default", c["defaut"]) if c["defaut"] != "" else _tr("py.gui.default_above") if defaut_dans_aide(c) else _tr("py.gui.default_none"))
    return t


# ---------------------------------------------------------------- valeurs, vérification, ligne de commande (sans fenêtre : testables)

def valeur_vide(c):
    """valeur d'un champ qu'on n'a pas touché"""
    return False if c["genre"] == "flag" else ("", False) if c["genre"] == "facultatif" else ""


def nom_champ(c):
    return c["options"][0] if c["options"] else c["dest"]


def verifier(champs, valeurs):
    """[(dest, texte)] : champ obligatoire vide, nombre illisible, valeur hors de la liste"""
    pb = []
    for c in champs:
        v = valeurs.get(c["dest"], valeur_vide(c))
        txt = (v[0] if isinstance(v, tuple) else v) if not isinstance(v, bool) else ""
        txt = txt.strip()
        if c["obligatoire"] and not txt and not (isinstance(v, tuple) and v[1]):
            pb.append((c["dest"], _tr("py.gui.problem_required", nom_champ(c))))
        elif txt and c["genre"] == "nombre":
            try:
                (int if c["nombre"] == "int" else float)(txt.replace(",", "."))
            except ValueError:
                pb.append((c["dest"], _tr("py.gui.problem_number", nom_champ(c), txt)))
        elif txt and c["genre"] == "choix" and txt not in c["choix"]:
            pb.append((c["dest"], _tr("py.gui.problem_choice", nom_champ(c), txt)))
    return pb


def construire(champs, valeurs):
    """liste d'arguments de l'outil : les arguments sans nom d'abord, puis les options ; un champ vide ou non touché n'écrit rien"""
    pos, opt = [], []
    for c in champs:
        v = valeurs.get(c["dest"], valeur_vide(c))
        o = c["options"][0] if c["options"] else None
        if c["genre"] == "flag":
            if v and o:
                opt.append(o)
            continue
        if c["genre"] == "tri":
            if v in ("yes", "no") and o:
                opt.append(o if v == "yes" else next((x for x in c["options"] if x.startswith("--no-")), "--no-" + o[2:]))
            continue
        if c["genre"] == "multiple":
            for ligne in (v or "").splitlines():
                ligne = ligne.strip()
                if ligne and o:
                    opt += [f"{o}={ligne}"] if ligne.startswith("-") else [o, ligne]
            continue
        seul = False
        if isinstance(v, tuple):
            v, seul = v
        v = (v or "").strip()
        if c["genre"] == "nombre":
            v = v.replace(",", ".")
        if not v and not seul:
            continue
        if not o:
            pos.append(v)
        elif not v:
            opt.append(o)
        elif v.startswith("-"):
            opt.append(f"{o}={v}")
        else:
            opt += [o, v]
    return pos + opt


def ligne_commande(fichier, args):
    q = subprocess.list2cmdline if os.name == "nt" else __import__("shlex").join
    return "python " + q([fichier] + list(args))


# ---------------------------------------------------------------- la fenêtre

class _TexteVar:
    """un champ de texte à plusieurs lignes (option répétable) qui répond comme une variable tkinter : get, set, trace_add"""
    def __init__(self, w, rappel):
        self.w, self.rappel = w, rappel
        w.bind("<KeyRelease>", lambda e: rappel())

    def get(self):
        return self.w.get("1.0", "end").strip("\n")

    def set(self, v):
        self.w.delete("1.0", "end")
        self.w.insert("1.0", v)
        self.rappel()

    def trace_add(self, *a):
        pass


def fenetre(outils, tk, ttk, filedialog, depart=None):
    """crée la fenêtre ; outils = [(nom, chemin du fichier)] ; rend un objet : .root, .champs, .vars, .valeurs(), .changer(nom), .lancer() ..."""
    chemins = dict(outils)
    root = tk.Tk()
    root.title(_tr("py.gui.title", version_tag()))
    root.geometry("1000x760")
    root.minsize(760, 520)

    class F:
        pass
    f = F()
    f.root, f.vars, f.lignes, f.proc, f.file = root, {}, {}, None, queue.Queue()
    f.nom, f.chemin, f.champs, f.cache = None, None, [], {}

    # ---- haut : choix de l'outil, recherche et compteur
    haut = ttk.Frame(root, padding=(8, 6))
    haut.pack(fill="x")
    ttk.Label(haut, text=_tr("py.gui.tool")).pack(side="left")
    f.outil = tk.StringVar()
    f.choix_outil = ttk.Combobox(haut, textvariable=f.outil, state="readonly", width=26, values=[chemins[n].name for n, _c in outils])
    f.choix_outil.pack(side="left", padx=(4, 0))
    ttk.Label(haut, text="   " + _tr("py.gui.search")).pack(side="left")
    f.filtre = tk.StringVar()
    ttk.Entry(haut, textvariable=f.filtre, width=28).pack(side="left", padx=4)
    f.compteur = ttk.Label(haut, text="")
    f.compteur.pack(side="left", padx=10)

    # ---- bas d'abord (pour qu'il garde sa place), puis le milieu qui s'étire
    bas = ttk.Frame(root, padding=(8, 4))
    bas.pack(side="bottom", fill="both")
    ttk.Label(bas, text=_tr("py.gui.help_title")).pack(anchor="w")
    f.aide = tk.Text(bas, height=4, wrap="word", state="disabled", relief="solid", borderwidth=1)
    f.aide.pack(fill="x", pady=(0, 4))
    ttk.Label(bas, text=_tr("py.gui.command")).pack(anchor="w")
    f.cmd = tk.Text(bas, height=3, wrap="word", state="disabled", relief="solid", borderwidth=1)
    f.cmd.pack(fill="x", pady=(0, 4))
    boutons = ttk.Frame(bas)
    boutons.pack(fill="x", pady=(0, 4))
    f.b_copier = ttk.Button(boutons, text=_tr("py.gui.copy"))
    f.b_lancer = ttk.Button(boutons, text=_tr("py.gui.run"))
    f.b_stop = ttk.Button(boutons, text=_tr("py.gui.stop"), state="disabled")
    f.b_reset = ttk.Button(boutons, text=_tr("py.gui.reset"))
    for b in (f.b_lancer, f.b_stop, f.b_copier, f.b_reset):
        b.pack(side="left", padx=(0, 6))
    f.etat = ttk.Label(boutons, text=_tr("py.gui.status_ready"))
    f.etat.pack(side="left", padx=10)
    ttk.Label(bas, text=_tr("py.gui.output")).pack(anchor="w")
    sortie = ttk.Frame(bas)
    sortie.pack(fill="both")
    f.sortie = tk.Text(sortie, height=7, wrap="word", state="disabled", relief="solid", borderwidth=1)
    ys = ttk.Scrollbar(sortie, orient="vertical", command=f.sortie.yview)
    f.sortie.configure(yscrollcommand=ys.set)
    f.sortie.pack(side="left", fill="both", expand=True)
    ys.pack(side="right", fill="y")

    # ---- milieu : les options, dans une zone qui défile
    milieu = ttk.Frame(root)
    milieu.pack(fill="both", expand=True, padx=8)
    cv = tk.Canvas(milieu, highlightthickness=0)
    sb = ttk.Scrollbar(milieu, orient="vertical", command=cv.yview)
    grille = ttk.Frame(cv)
    grille.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
    fen = cv.create_window((0, 0), window=grille, anchor="nw")
    cv.bind("<Configure>", lambda e: cv.itemconfigure(fen, width=e.width))
    cv.configure(yscrollcommand=sb.set)
    cv.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    def molette(e):
        cv.yview_scroll(-1 if (getattr(e, "num", 0) == 4 or getattr(e, "delta", 0) > 0) else 1, "units")
    root.bind_all("<MouseWheel>", molette)
    root.bind_all("<Button-4>", molette)
    root.bind_all("<Button-5>", molette)
    grille.columnconfigure(4, weight=1)

    def ecrire(widget, texte, ajout=False):
        widget.configure(state="normal")
        if not ajout:
            widget.delete("1.0", "end")
        widget.insert("end", texte)
        widget.configure(state="disabled")
        widget.see("end") if ajout else None

    def montrer_aide(c):
        ecrire(f.aide, texte_aide(c))

    def valeurs():
        v = {}
        for c in f.champs:
            x = f.vars[c["dest"]]
            if c["genre"] == "flag":
                v[c["dest"]] = bool(x.get())
            elif c["genre"] == "tri":
                v[c["dest"]] = {_tr("py.gui.tri_yes"): "yes", _tr("py.gui.tri_no"): "no"}.get(x.get(), "")
            elif c["genre"] == "facultatif":
                v[c["dest"]] = (x[0].get(), bool(x[1].get()))
            else:
                v[c["dest"]] = x.get()
        return v
    f.valeurs = valeurs

    def maj_commande(*_):
        if not f.champs:
            return
        pb = {d for d, _t in verifier(f.champs, valeurs())}
        for d, (marque, _c) in f.lignes.items():
            marque.configure(text="!" if d in pb else " ")      # le signe « ! » : l'état ne dépend pas de la couleur
        ecrire(f.cmd, ligne_commande(f.chemin.name, construire(f.champs, valeurs())))
    f.maj = maj_commande

    def choisir(var, dossier):
        p = filedialog.askdirectory() if dossier else filedialog.askopenfilename()
        if p:
            var.set(p)

    # ---- les lignes de l'outil choisi (refaites à chaque changement d'outil)
    def lignes_construire():
        for w in grille.winfo_children():
            w.destroy()
        f.vars, f.lignes = {}, {}
        for i, c in enumerate(f.champs):
            marque = ttk.Label(grille, text=" ", width=2, font=("TkDefaultFont", 10, "bold"))
            marque.grid(row=i, column=0, sticky="w")
            etiq = ttk.Label(grille, text="  /  ".join(c["options"]) if c["options"] else c["dest"], width=30, font="TkFixedFont", anchor="w")
            etiq.grid(row=i, column=1, sticky="w", padx=(0, 6))
            cases = [marque, etiq]
            extra = ttk.Frame(grille)
            extra.grid(row=i, column=3, sticky="w", padx=4)
            if c["genre"] == "flag":
                var = tk.BooleanVar(value=False)
                w = ttk.Checkbutton(grille, variable=var)
            elif c["genre"] == "tri":
                var = tk.StringVar(value=_tr("py.gui.tri_default"))
                w = ttk.Combobox(grille, textvariable=var, state="readonly", width=12, values=(_tr("py.gui.tri_default"), _tr("py.gui.tri_yes"), _tr("py.gui.tri_no")))
            elif c["genre"] == "choix":
                var = tk.StringVar(value="")
                w = ttk.Combobox(grille, textvariable=var, state="readonly", width=12, values=[""] + c["choix"])
            elif c["genre"] == "facultatif":
                t, seul = tk.StringVar(value=""), tk.BooleanVar(value=False)
                var = (t, seul)
                w = ttk.Entry(grille, textvariable=t)
                ttk.Checkbutton(extra, text=_tr("py.gui.alone"), variable=seul).pack(side="left")
            elif c["genre"] == "multiple":
                w = tk.Text(grille, height=3, width=40, relief="solid", borderwidth=1)
                var = _TexteVar(w, maj_commande)
            else:
                var = tk.StringVar(value="")
                w = ttk.Entry(grille, textvariable=var, width=14 if c["genre"] == "nombre" else 40)
            if c["genre"] in ("chemin", "facultatif") and (c["genre"] == "chemin" or c["ptype"] or any(k in c["metavar"].upper() for k in MOTS_CHEMIN) or c["metavar"].lower().endswith((".html", ".json"))):
                vv = var[0] if isinstance(var, tuple) else var
                ttk.Button(extra, text=_tr("py.gui.browse_file"), command=lambda v=vv: choisir(v, False)).pack(side="left", padx=2)
                ttk.Button(extra, text=_tr("py.gui.browse_dir"), command=lambda v=vv: choisir(v, True)).pack(side="left", padx=2)
            w.grid(row=i, column=2, sticky="we" if c["genre"] in ("texte", "chemin", "facultatif", "multiple") else "w")
            cases += [w, extra]
            dfl = ttk.Label(grille, text=(_tr("py.gui.default", c["defaut"]) if c["defaut"] != "" else _tr("py.gui.default_in_help") if defaut_dans_aide(c) else ""), foreground="#555555", wraplength=180, justify="left")
            dfl.grid(row=i, column=4, sticky="w", padx=(6, 0))
            cases.append(dfl)
            for x in cases:
                x.bind("<Enter>", lambda e, c=c: montrer_aide(c), add="+")
            w.bind("<FocusIn>", lambda e, c=c: montrer_aide(c), add="+")
            f.vars[c["dest"]] = var
            f.lignes[c["dest"]] = (marque, cases)
            for v in (var if isinstance(var, tuple) else (var,)):
                v.trace_add("write", maj_commande)
        f.filtrer()

    def filtrer(*_):
        mot = f.filtre.get().strip().lower()
        n = 0
        for c in f.champs:
            if c["dest"] not in f.lignes:
                continue
            ok = (not mot) or mot in (" ".join(c["options"]) + " " + c["dest"] + " " + c["aide"]).lower()
            for x in f.lignes[c["dest"]][1]:
                x.grid() if ok else x.grid_remove()
            n += ok
        f.compteur.configure(text=_tr("py.gui.count", n, len(f.champs)))
    f.filtre.trace_add("write", filtrer)
    f.filtrer = filtrer

    def changer(nom):
        """affiche les options de l'outil `nom` (refusé pendant qu'un outil tourne) ; rend True si le changement a eu lieu"""
        if f.proc is not None or nom not in chemins:
            f.outil.set(f.chemin.name if f.chemin else "")
            return False
        chemin = chemins[nom]
        champs = f.cache.get(nom)
        if champs is None:
            parser = lire_parser(chemin, I18N_LANG)
            if parser is None:
                f.etat.configure(text=_tr("py.gui.read_error", chemin.name))
                f.outil.set(f.chemin.name if f.chemin else "")
                return False
            champs = f.cache[nom] = champs_depuis(parser)
        f.filtre.set("")      # avant le changement : le filtre se vide sur les lignes de l'outil précédent
        f.nom, f.chemin, f.champs = nom, chemin, champs
        f.outil.set(chemin.name)
        lignes_construire()
        ecrire(f.aide, _tr("py.gui.help_none"))
        ecrire(f.sortie, "")
        f.etat.configure(text=_tr("py.gui.status_ready"))
        cv.yview_moveto(0)
        maj_commande()
        return True
    f.changer = changer
    f.choix_outil.bind("<<ComboboxSelected>>", lambda e: changer(next((n for n, c in outils if c.name == f.outil.get()), None)))

    # ---- boutons
    def copier():
        root.clipboard_clear()
        root.clipboard_append(ligne_commande(f.chemin.name, construire(f.champs, valeurs())))
        f.etat.configure(text=_tr("py.gui.status_copied"))
    f.b_copier.configure(command=copier)

    def effacer():
        for c in f.champs:
            x = f.vars[c["dest"]]
            if c["genre"] == "flag":
                x.set(False)
            elif c["genre"] == "tri":
                x.set(_tr("py.gui.tri_default"))
            elif c["genre"] == "facultatif":
                x[0].set("")
                x[1].set(False)
            else:
                x.set("")
    f.b_reset.configure(command=effacer)

    def lire(proc):
        for ligne in iter(proc.stdout.readline, b""):
            f.file.put(("txt", ligne.decode("utf-8", "replace")))
        f.file.put(("fin", proc.wait()))

    def pomper():
        try:
            while True:
                genre, x = f.file.get_nowait()
                if genre == "txt":
                    ecrire(f.sortie, x, ajout=True)
                else:
                    f.proc = None
                    f.b_lancer.configure(state="normal")
                    f.b_stop.configure(state="disabled")
                    f.choix_outil.configure(state="readonly")
                    f.etat.configure(text=_tr("py.gui.status_done", x))
                    return
        except queue.Empty:
            pass
        if f.proc is not None:
            root.after(80, pomper)

    def lancer(_e=None):
        if f.proc is not None:
            return
        pb = verifier(f.champs, valeurs())
        if pb:
            f.etat.configure(text=_tr("py.gui.status_invalid", " ; ".join(t for _d, t in pb)))
            maj_commande()
            return
        args = construire(f.champs, valeurs())
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1", WEB3D_LANG=I18N_LANG)
        kw = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        ecrire(f.sortie, "> " + ligne_commande(f.chemin.name, args) + "\n")
        try:
            f.proc = subprocess.Popen([sys.executable, str(f.chemin)] + args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, **kw)
        except OSError as e:
            f.proc = None
            ecrire(f.sortie, _tr("py.gui.start_failed", e), ajout=True)
            return
        f.b_lancer.configure(state="disabled")
        f.b_stop.configure(state="normal")
        f.choix_outil.configure(state="disabled")
        f.etat.configure(text=_tr("py.gui.status_running"))
        threading.Thread(target=lire, args=(f.proc,), daemon=True).start()
        root.after(80, pomper)
    f.lancer = lancer
    f.b_lancer.configure(command=lancer)
    root.bind("<Control-Return>", lancer)

    def arreter():
        if f.proc is not None:
            f.proc.terminate()
            f.etat.configure(text=_tr("py.gui.status_stopped"))
    f.b_stop.configure(command=arreter)

    def fermer():
        if f.proc is not None:
            f.proc.terminate()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", fermer)

    changer(depart if depart in chemins else outils[0][0])
    return f


def main(argv=None):
    ap = argparse.ArgumentParser(description=_tr("py.gui.desc", version_tag()), epilog=_tr("py.gui.epilog"),
                                 formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False)
    i18n_add_common(ap)
    ap.add_argument("--version", action="version", version=f"web3d_gui {version_tag()}", help=_tr("py.common.version"))
    ap.add_argument("--tool", choices=[n for n, _f in OUTILS], default=OUTILS[0][0], metavar="NAME", help=_tr("py.gui.help.tool", ", ".join(n for n, _f in OUTILS)))
    a = ap.parse_args(argv)
    try:
        import tkinter as tk
        from tkinter import filedialog, ttk
    except ImportError:
        print(_tr("py.gui.no_tk"))
        return 2
    trouves = [(nom, p) for nom, fichier in OUTILS for p in [trouver_outil(fichier)] if p is not None]
    if not trouves:
        print(_tr("py.gui.no_tool", OUTILS[0][1]))
        return 1
    f = fenetre(trouves, tk, ttk, filedialog, depart=a.tool)
    f.root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
