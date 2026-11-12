#!/usr/bin/env python3
"""Test 1.9.11 : sous Linux, oar2glb.py lance convoar.exe avec Mono (hors navigateur ; un FAUX mono, aucun vrai convoar n'est lance).

Verifie : commande = mono + chemin absolu de convoar.exe + --outputdir DOSSIER + OAR, executee dans le dossier de l'OAR ;
LC_ALL=C et LD_LIBRARY_PATH (dossier de convoar.exe en tete, l'ancienne valeur gardee) ; chemin relatif de convoar.exe rendu absolu ;
mono absent : arret avec le message (apt-get install ...) ; un programme sans .exe (script, convoar du PATH) est lance tel quel, sans mono.
Sous Windows : ignore (le lanceur convoar_inv.exe est un autre chemin).

Lancer : python tests/mono_linux.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import os, pathlib, shutil, stat, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import oar2glb as T  # noqa: E402

bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)), flush=True)


# --- Windows (simule par le parametre windows=True, donc essayable partout) : seul un .exe passe par le lanceur convoar_inv.exe
t, e = T.commande_convoar("C:/x/convoar_fake.py", windows=True)
rapport(t == [sys.executable, str(pathlib.Path("C:/x/convoar_fake.py"))] and e is None, "Windows : un script .py est lance avec python (le lanceur convoar_inv.exe demande un vrai .exe)", t)
t, e = T.commande_convoar("C:/x/convoar.cmd", windows=True)
rapport(t == [str(pathlib.Path("C:/x/convoar.cmd"))] and e is None, "Windows : un .cmd (ou tout autre programme) est lance tel quel", t)

if os.name == "nt":
    print("[IGNORE] sous Windows : convoar passe par le lanceur convoar_inv.exe (autre chemin)")
    sys.exit(0)

tmp = pathlib.Path(tempfile.mkdtemp(prefix="mono_linux_")).resolve()
PATH0 = os.environ.get("PATH", "")
LD0 = os.environ.get("LD_LIBRARY_PATH")


def faux(chemin, trace):
    """script qui note ses arguments, LC_ALL, LD_LIBRARY_PATH et son dossier courant dans trace"""
    chemin.write_text('#!/bin/sh\n{ for a in "$@"; do echo "ARG:$a"; done; echo "LC:$LC_ALL"; echo "LD:$LD_LIBRARY_PATH"; echo "PWD:$(pwd)"; } > "%s"\n' % trace, encoding="ascii")
    chemin.chmod(chemin.stat().st_mode | stat.S_IXUSR)


def lire(trace):
    d = {"ARG": []}
    for ligne in pathlib.Path(trace).read_text(encoding="utf-8").splitlines():
        k, _, v = ligne.partition(":")
        if k == "ARG":
            d["ARG"].append(v)
        else:
            d[k] = v
    return d


try:
    bindir = tmp / "bin"
    bindir.mkdir()
    cv = tmp / "mon convoar"                      # un espace : le chemin doit rester un seul argument
    cv.mkdir()
    exe = cv / "convoar.exe"
    exe.write_bytes(b"MZ")
    wd = tmp / "regions"
    wd.mkdir()
    oar = wd / "Atoll.oar"
    oar.write_bytes(b"x")
    outdir = wd / "Atoll-GLTF"
    trace = tmp / "trace.txt"
    faux(bindir / "mono", trace)

    # 1. mono present
    os.environ["PATH"] = str(bindir) + os.pathsep + PATH0
    os.environ["LD_LIBRARY_PATH"] = "/ancien/chemin"
    T.run_convoar(str(exe), oar, outdir)
    d = lire(trace)
    rapport(d["ARG"] == [str(exe), "--outputdir", "Atoll-GLTF", "Atoll.oar"], "commande : mono CONVOAR.EXE --outputdir DOSSIER OAR (options avant le fichier)", d["ARG"])
    rapport(d["LC"] == "C", "LC_ALL=C", d["LC"])
    rapport(d["LD"] == str(cv) + os.pathsep + "/ancien/chemin", "LD_LIBRARY_PATH : dossier de convoar.exe en tete, ancienne valeur gardee", d["LD"])
    rapport(pathlib.Path(d["PWD"]).resolve() == wd, "execute dans le dossier de l'OAR", d["PWD"])
    del os.environ["LD_LIBRARY_PATH"]
    T.run_convoar(str(exe), oar, outdir)
    rapport(lire(trace)["LD"] == str(cv), "LD_LIBRARY_PATH sans ancienne valeur : le dossier seul (pas de ':' en trop)", lire(trace)["LD"])

    # 2. chemin relatif
    cwd0 = os.getcwd()
    os.chdir(tmp)
    try:
        tete, env = T.commande_convoar(os.path.join("mon convoar", "convoar.exe"))
    finally:
        os.chdir(cwd0)
    rapport(tete[1] == str(exe) and env["LC_ALL"] == "C", "chemin relatif de convoar.exe rendu absolu", tete)

    # 3. mono absent
    vide = tmp / "vide"
    vide.mkdir()
    os.environ["PATH"] = str(vide)
    try:
        T.commande_convoar(str(exe))
        rapport(False, "mono absent : arret avec un message")
    except SystemExit as e:
        m = str(e.code)
        rapport("Mono" in m and "apt-get install" in m and str(exe) in m and m.startswith("[ERREUR]"), "mono absent : arret avec le message (Mono, apt-get install, chemin)", m)

    # 4. programme sans .exe : lance tel quel, sans mono
    os.environ["PATH"] = str(bindir) + os.pathsep + PATH0
    prog = tmp / "convoar"
    trace2 = tmp / "trace2.txt"
    faux(prog, trace2)
    T.run_convoar(str(prog), oar, outdir)
    d2 = lire(trace2)
    rapport(d2["ARG"] == ["--outputdir", "Atoll-GLTF", "Atoll.oar"] and d2["LC"] == "" and d2["LD"] == "", "convoar sans .exe : lance tel quel (ni mono, ni LC_ALL, ni LD_LIBRARY_PATH)", d2)
finally:
    os.environ["PATH"] = PATH0
    if LD0 is None:
        os.environ.pop("LD_LIBRARY_PATH", None)
    else:
        os.environ["LD_LIBRARY_PATH"] = LD0
    shutil.rmtree(tmp, ignore_errors=True)

print("\n%s" % ("TOUT PASSE" if not bad else "%d ECHEC(S)" % bad))
sys.exit(1 if bad else 0)
