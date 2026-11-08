#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diag_carte.py (hors navigateur) : lance depuis tools/ (sources) et depuis dist/ (fabrique), contre un faux serveur de presence.

Verifie : aide et version en francais et en anglais (aucune cle brute, aucun accent francais en anglais) ; arguments manquants refuses ; pour chaque cas
le code de sortie et la phrase du resultat dans les deux langues : serveur bon (0), personne en ligne (0), ancien serveur qui donne les pseudos sans cle (2),
aucun pseudo avec la cle (3), origine refusee (4), serveur injoignable (1).
Prerequis : pip install websockets. Lancer : python build.py puis python tests/diag_carte.py
"""
import os, pathlib, re, socket, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTILS = {"tools": ROOT / "tools" / "diag_carte.py", "dist": ROOT / "dist" / "diag_carte.py"}
ACC = re.compile(r"[éèêëàâùûôîïçœÉÈÀÙÎÔ]")
bad = 0

STUB = r'''
import asyncio, json, sys
cas, port = sys.argv[1], int(sys.argv[2])
try:
    from websockets.asyncio.server import serve
except ImportError:
    from websockets import serve

async def h(ws, *a):
    msg = json.loads(await ws.recv())
    cle = msg.get("key")
    r = {"rooms": ["salle"], "visitors": 1}
    if cas == "bon" and cle == "K":
        r.update(names=["alice"], viewers=[])
    elif cas == "origine" and cle == "K":
        r.update(names=["alice"], viewers=[])
    elif cas == "personne" and cle == "K":
        r.update(names=[], viewers=[])
    elif cas == "ancien":
        r.update(names=["alice"], viewers=[])
    await ws.send(json.dumps(r))

async def main():
    kw = {"origins": ["https://permis.example"]} if cas == "origine" else {}
    async with serve(h, "127.0.0.1", port, **kw):
        print("pret", flush=True)
        await asyncio.Future()

asyncio.run(main())
'''


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)[:500]), flush=True)


def port_libre():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def port_avec_403():
    for p in range(40300, 40400):
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", p)); s.close(); return p
        except OSError:
            s.close()
    return 40399


def lancer(outil, *args, lang="fr"):
    e = dict(os.environ, WEB3D_LANG=lang, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, str(outil), *args], capture_output=True, text=True, encoding="utf-8", env=e, stdin=subprocess.DEVNULL, timeout=60)
    return r.returncode, r.stdout + r.stderr


def faux_serveur(cas):
    port = port_libre()
    p = subprocess.Popen([sys.executable, "-c", STUB, cas, str(port)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    t0 = time.time()
    while time.time() - t0 < 15:
        if p.stdout.readline().strip() == "pret":
            return p, port
    p.kill()
    sys.exit("[ECHEC] le faux serveur ne demarre pas (pip install websockets ?)")


# (cas, arguments apres l'adresse, code attendu, phrase francaise, phrase anglaise)
CAS = [("bon", ["K"], 0, "le serveur est BON : la clé est acceptée", "the server is FINE: the key is accepted"),
       ("personne", ["K"], 0, "personne n'est connecté", "nobody is connected"),
       ("ancien", ["K"], 2, "SANS clé", "WITHOUT a key"),
       ("bon", ["MAUVAISE"], 3, "AUCUN pseudo", "NO nickname"),
       ("origine", ["K"], 4, "REFUSE l'origine", "REFUSES the origin")]

for nom, outil in OUTILS.items():
    if not outil.is_file():
        rapport(False, f"{nom} : fichier absent ({outil}) : python build.py d'abord")
        continue
    for lang in ("fr", "en"):
        c, s = lancer(outil, "--help", lang=lang)
        rapport(c == 0 and "usage:" in s and "py." not in s and "--lang" in s, f"{nom} --help ({lang}) : s'affiche, aucune cle brute", (c, s[-200:]))
        rapport(bool(ACC.search(s)) == (lang == "fr"), f"{nom} --help ({lang}) : dans la bonne langue", s[:200])
        c, s = lancer(outil, "--version", lang=lang)
        rapport(c == 0 and s.startswith("diag_carte "), f"{nom} --version ({lang})", s)
    c, s = lancer(outil)
    rapport(c == 2 and "usage:" in s, f"{nom} : sans argument, refuse avec l'usage", (c, s[-150:]))
    for cas, args, code, fr, en in CAS:
        p, port = faux_serveur(cas)
        try:
            adr = f"ws://127.0.0.1:{port}"
            for lang, phrase in (("fr", fr), ("en", en)):
                c, s = lancer(outil, adr, *args, lang=lang)
                rapport(c == code and phrase in s and "py." not in s, f"{nom} : cas {cas} {args} ({lang}) : code {code} et « {phrase} »", (c, s[-300:]))
            if cas == "origine":
                c, s = lancer(outil, adr, "K", "https://permis.example", lang="fr")
                rapport(c == 0 and "origine annoncée : https://permis.example" in s, f"{nom} : avec l'origine permise, le serveur repond", (c, s[-300:]))
        finally:
            p.kill(); p.wait()
    for port in (port_libre(), port_avec_403()):   # le second contient « 403 » : ce n'est pas un refus d'origine
        for lang, phrase in (("fr", "impossible de questionner"), ("en", "cannot query")):
            c, s = lancer(outil, f"ws://127.0.0.1:{port}", "K", lang=lang)
            rapport(c == 1 and phrase in s and "REFUSE" not in s and "REFUSES" not in s, f"{nom} : serveur injoignable, port {port} ({lang}) : code 1", (c, s[-300:]))
print("\nRÉSULTAT :", "tout est passé" if not bad else f"ÉCHEC ({bad})")
sys.exit(1 if bad else 0)
