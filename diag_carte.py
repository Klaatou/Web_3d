#!/usr/bin/env python3
# -*- coding: ascii -*-
"""Diagnostic des pseudos de la carte : interroge le serveur de presence comme le fait la carte, avec et sans la cle, et dit ce qui manque.
Usage : python diag_carte.py ws://HOTE:PORT CLE [ORIGINE]
  ws://HOTE:PORT : la meme adresse (ws:// ou wss://) que dans la configuration de vos regions
  ORIGINE        : l'adresse de VOTRE SITE, sans chemin (par exemple https://klaatou.github.io), si le serveur n'accepte que certains sites (--origins, --creators)
Necessite : pip install websockets. Ne modifie rien."""
import asyncio, json, sys


async def demander(url, cle, origine):
    try:
        from websockets.asyncio.client import connect
    except ImportError:
        from websockets import connect
    async with connect(url, open_timeout=10, **({"origin": origine} if origine else {})) as ws:
        await ws.send(json.dumps({"t": "rooms", "key": cle} if cle is not None else {"t": "rooms"}))
        return json.loads(await asyncio.wait_for(ws.recv(), 10))


async def main(url, cle, origine):
    print("Serveur :", url, ("(origine annoncee : %s)" % origine) if origine else "(aucune origine annoncee)")
    try:
        sans = await demander(url, None, origine)
        avec = await demander(url, cle, origine)
    except Exception as e:
        print("ERREUR : impossible de questionner le serveur (%s : %s)." % (type(e).__name__, e))
        if "4003" in str(e) or "403" in str(e) or "origin" in str(e).lower():
            print("  -> le serveur REFUSE l'origine : il n'accepte que les pages de certains sites (--origins ou --creators).")
            print("     Relancez en ajoutant en 3e argument l'adresse de votre site, par exemple : python diag_carte.py ADRESSE CLE https://klaatou.github.io")
            return 4
        print("  -> adresse ou port faux, serveur arrete, pare-feu, ou adresse ws:// au lieu de wss:// (ou l'inverse).")
        return 1
    print("Sans cle   : salons %s, visiteurs %s, pseudos : %s" % (sans.get("rooms"), sans.get("visitors"), sans.get("names", "(aucun champ names)")))
    print("Avec la cle : salons %s, visiteurs %s" % (avec.get("rooms"), avec.get("visitors")))
    print("              pseudos des promeneurs : %s" % avec.get("names", "(aucun champ names)"))
    print("              pseudos en vue globale : %s" % avec.get("viewers", "(aucun champ viewers)"))
    print()
    if "names" in sans:
        print("RESULTAT : ce serveur donne les pseudos SANS cle : c'est l'ancien fichier presence_server.py (1.3.1, pseudos publics).")
        print("  -> copiez le nouveau presence_server.py (dossier dist du depot) sur le serveur et relancez-le avec --map-names-key VOTRE_CLE")
        return 2
    if "names" not in avec:
        print("RESULTAT : avec la cle, le serveur ne donne AUCUN pseudo. Trois causes possibles :")
        print("  1. le serveur n'a pas ete lance avec --map-names-key VOTRE_CLE (l'ancienne option --map-names est sans effet) : verifiez la ligne de lancement,")
        print("     puis la console au demarrage : elle doit dire que les pseudos sont donnes aux cartes qui presentent la cle ;")
        print("  2. la cle tapee ici n'est pas exactement celle du lancement (majuscules, espaces, guillemets) ;")
        print("  3. le fichier presence_server.py du serveur est une version trop ancienne.")
        print("  (apres 5 cles fausses en une minute le serveur n'ecoute plus : attendez une minute avant de reessayer)")
        return 3
    if not (avec.get("names") or avec.get("viewers")):
        print("RESULTAT : le serveur est BON (la cle est acceptee), mais personne n'est connecte en ce moment : aucun pseudo a montrer.")
        print("  -> ouvrez une region de ce serveur dans un autre navigateur (promenade avec la touche P), puis relancez ce diagnostic.")
        return 0
    print("RESULTAT : le serveur est BON : la cle est acceptee et des pseudos sont donnes.")
    print("  Si la carte n'en affiche pas, le probleme est du cote de la page :")
    print("  1. le fichier carte.html du serveur web n'est pas la version a jour : recopiez dist\\carte.html (et dist\\index.html pour la carte ouverte par M) ;")
    print("  2. l'adresse ouverte doit se terminer par #pseudos=VOTRE_CLE (par exemple .../carte.html#pseudos=VOTRE_CLE) ;")
    print("  3. une cle avec & + % # ou des espaces est mal lue dans l'adresse : prenez des lettres et des chiffres ;")
    print("  4. rechargez la page en forcant le cache (Ctrl+F5).")
    return 0


if len(sys.argv) not in (3, 4):
    sys.exit(__doc__)
sys.exit(asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) == 4 else None)))
