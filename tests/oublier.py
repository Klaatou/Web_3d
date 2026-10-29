#!/usr/bin/env python3
"""Tests : commande de console « oublier <pseudo> » (vrai presence_server.py) : libere un pseudo reserve sans arreter le serveur ni toucher au fichier.

Verifie : un pseudo pris par un navigateur est refuse a un autre (suffixe #CODE) ; « oublier » le libere, le premier qui le demande ensuite l'obtient ;
le fichier du registre est a jour (le pseudo et son proprietaire n'y sont plus) ; un pseudo inconnu et l'absence d'argument donnent un message ;
le message signale un proprietaire encore connecte.

Prerequis : pip install websockets ; python build.py avant. Lancer : python tests/oublier.py
"""
import asyncio, json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37
import websockets

port = port_libre()
reg = tmp / "identites.json"
sortie_chemin = tmp / "sortie.txt"
sortie = open(sortie_chemin, "w", encoding="utf-8")
proc = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--lang", "fr", "--host", "127.0.0.1", "--port", str(port), "--identities", str(reg), "--bans", str(tmp / "bans.json")],
                        stdin=subprocess.PIPE, stdout=sortie, stderr=subprocess.STDOUT, text=True, env=dict(os.environ, PYTHONUNBUFFERED="1"))
attendre_port(port, proc, "presence_server")


def uid(n):
    return f"{n:020x}"


async def venir(u, name):
    ws = await websockets.connect(f"ws://127.0.0.1:{port}")
    await ws.send(json.dumps({"t": "hello", "room": "salon", "name": name, "uid": u, "spectator": False}))
    m = json.loads(await asyncio.wait_for(ws.recv(), 5))
    return ws, m


def commande(c):
    n = len(sortie_texte())
    proc.stdin.write(c + "\n"); proc.stdin.flush()
    time.sleep(0.8)
    return sortie_texte()[n:]


def sortie_texte():
    return sortie_chemin.read_text(encoding="utf-8", errors="replace")


async def main():
    print("--- 0. pseudos : la liste est vide au depart")
    r = commande("pseudos")
    rapport("(aucun pseudo réservé)" in r, "aucun pseudo reserve : message", r)
    print("--- 1. un pseudo pris est refuse a un autre navigateur")
    wa, ma = await venir(uid(1), "Zoé Test")
    rapport(ma.get("name") == "Zoé Test", "le premier navigateur obtient le pseudo", ma.get("name"))
    wb, mb = await venir(uid(2), "zoe test")
    rapport(mb.get("name", "").startswith("zoe test#"), "un autre navigateur recoit le pseudo avec un suffixe #CODE", mb.get("name"))
    await wb.close()
    d = json.loads(reg.read_text(encoding="utf-8"))
    rapport("zoetest" in d["names"] and len(d["users"]) >= 1, "le registre contient le pseudo simplifie « zoetest »", list(d["names"]))

    print("--- 1b. pseudos : la liste")
    r = commande("pseudos")
    rapport("pseudos réservés (1) :" in r and "Zoé Test" in r and "(connecté)" in r and "libre le" in r, "un pseudo reserve, son proprietaire connecte, date de liberation", r)
    m = __import__("re").search(r"#([A-Z2-7]{4})", r)
    rapport(bool(m), "le code #XXXX du proprietaire est affiche", r)
    r = commande("pseudos zoe")
    rapport("Zoé Test" in r, "filtre : « zoe » trouve « Zoé Test »", r)
    r = commande("pseudos zzz")
    rapport("aucun pseudo réservé ne correspond à « zzz »" in r, "filtre sans resultat : message", r)
    print("--- 2. oublier : messages")
    commande("oublier")
    rapport("usage : oublier" in sortie_texte(), "sans argument : l'usage s'affiche")
    commande("oublier inconnu")
    rapport("aucun pseudo réservé ne correspond à « inconnu »" in sortie_texte(), "pseudo inconnu : message")

    print("--- 3. oublier libere le pseudo")
    commande("oublier ZOÉ  test")
    t = sortie_texte()
    rapport("pseudo « Zoé Test » libéré" in t, "confirmation avec le pseudo tel qu'ecrit", t[-300:])
    rapport("connecté" in t.split("libéré")[-1], "le message signale que son proprietaire est encore connecte")
    d = json.loads(reg.read_text(encoding="utf-8"))
    rapport("zoetest" not in d["names"] and not any(u.get("key") == "zoetest" for u in d["users"].values()), "le fichier du registre ne contient plus ni le pseudo ni son proprietaire", d)
    wc, mc = await venir(uid(3), "Zoé Test")
    rapport(mc.get("name") == "Zoé Test", "le premier qui le demande ensuite l'obtient", mc.get("name"))
    d = json.loads(reg.read_text(encoding="utf-8"))
    rapport(d["names"].get("zoetest") not in (None, ""), "il est de nouveau reserve (par le nouveau navigateur)")
    for w in (wa, wc):
        await w.close()
    await asyncio.sleep(0.4)
    commande("oublier zoe test")
    rapport(sortie_texte().count("libéré") >= 2 and "connecté" not in sortie_texte().rsplit("libéré", 1)[-1], "proprietaire deconnecte : liberation sans la mention « connecte »")


try:
    asyncio.run(main())
finally:
    proc.terminate()
    try:
        proc.wait(5)
    except Exception:
        proc.kill()
    sortie.close()
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
