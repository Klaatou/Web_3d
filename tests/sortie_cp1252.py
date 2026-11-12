#!/usr/bin/env python3
"""Sortie redirigee dans un tube ou un fichier Windows en cp1252 (lot 1.10.2).

Verifie, pour glb2html.py, oar2glb.py, diag_carte.py et presence_server.py (sources de src\\ et tools\\) :
1. sortie en cp1252 : un caractere hors de cette page de code (la fleche, U+2192) est remplace, l'outil ne s'arrete pas sur UnicodeEncodeError ;
2. sens oppose : sortie en UTF-8, la fleche est conservee telle quelle (le correctif ne remplace rien quand le flux sait l'ecrire).
glb2html.py : le message a fleche (« [image] ... -> ... ») ne sort que depuis des zones liees a des images ; le test execute donc le vrai
bloc « __main__ » du script en remplacant seulement l'appel final a main() par l'ecriture de la fleche.
Prerequis : pip install websockets (serveur de presence). Lancer : python tests/sortie_cp1252.py
"""
import atexit, os, pathlib, shutil, socket, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
FLECHE = "\u2192"
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else "  " + detail))
    echecs += not ok


def env(codage):
    e = dict(os.environ, PYTHONIOENCODING=codage, PYTHONUTF8="0", WEB3D_LANG="en")
    e.pop("PYTHONSTARTUP", None)
    return e


def lancer(args, codage, delai=8, arreter=False):
    """lance, sortie vers des fichiers (comme '> journal.txt'), rend (code, stdout en octets, stderr en texte)"""
    with tempfile.TemporaryDirectory() as t:
        fo, fe = pathlib.Path(t, "o"), pathlib.Path(t, "e")
        with open(fo, "wb") as o, open(fe, "wb") as e:
            p = subprocess.Popen([sys.executable, "-u"] + args, stdin=subprocess.DEVNULL, stdout=o, stderr=e, env=env(codage), cwd=str(ROOT))
            try:
                code = p.wait(delai)
            except subprocess.TimeoutExpired:
                p.terminate()
                try:
                    p.wait(5)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait()
                code = "arrete" if arreter else "delai"
        return code, fo.read_bytes(), fe.read_text("utf-8", "replace")


def port_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def gen_args():
    """glb2html.py : le bloc __main__ du script, main() remplace par l'ecriture de la fleche"""
    chemin = ROOT / "src" / "gen_tpl.py"
    src = chemin.read_text("utf-8").replace("\r\n", "\n")
    fin = "    sys.argv = old_options(sys.argv)\n    main()"
    if src.count(fin) != 1:
        return None
    code = src.replace(fin, "    sys.argv = old_options(sys.argv)\n    print(chr(0x2192) + ' fin')")
    pilote = ("import sys\nc = compile(open(sys.argv[1], encoding='utf-8').read(), sys.argv[2], 'exec')\n"
              "sys.argv = [sys.argv[2]]\nexec(c, {'__name__': '__main__', '__file__': sys.argv[0]})\n")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="sortie_cp1252_"))
    atexit.register(shutil.rmtree, str(tmp), True)
    (tmp / "src.py").write_text(code, "utf-8")
    (tmp / "pilote.py").write_text(pilote, "utf-8")
    return ["-c", pilote, str(tmp / "src.py"), str(chemin)]


CAS = [
    ("glb2html.py", gen_args, False),
    ("oar2glb.py", lambda: [str(ROOT / "tools" / "oar2glb.py"), FLECHE + ".oar", "--nopause"], False),
    ("diag_carte.py", lambda: [str(ROOT / "tools" / "diag_carte.py"), "ws://127.0.0.1:1/" + FLECHE, "CLE_DE_TEST"], False),
    ("presence_server.py", lambda: [str(ROOT / "src" / "presence_server.py"), "--host", "127.0.0.1", "--port", str(port_libre()),
                                    "--creators", FLECHE + ".json"], True),
]

for nom, f, serveur in CAS:
    args = f()
    if args is None:
        rapport(False, nom + " : bloc __main__ introuvable dans src/gen_tpl.py")
        continue
    code, out, err = lancer(args, "cp1252", arreter=serveur)
    plante = "UnicodeEncodeError" in err
    rapport(not plante and code != "delai", nom + " : sortie cp1252, pas de UnicodeEncodeError", err.strip().splitlines()[-1] if err.strip() else str(code))
    rapport(len(out) > 0 and b"?" in out and FLECHE.encode("utf-8") not in out, nom + " : sortie cp1252, la fleche est remplacee par '?'", repr(out[:120]))
    code, out, err = lancer(args, "utf-8", arreter=serveur)
    rapport("UnicodeEncodeError" not in err and FLECHE.encode("utf-8") in out, nom + " : sortie UTF-8, la fleche est conservee", repr(out[:120]) + " " + err.strip()[-120:])

print("ECHECS : %d" % echecs if echecs else "TOUT PASSE")
sys.exit(1 if echecs else 0)
