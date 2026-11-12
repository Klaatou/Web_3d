#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diag_carte.py : diagnostic des pseudos de la carte. Interroge le serveur de présence comme le fait la carte, avec et sans la clé, et dit ce qui manque.

Ne modifie rien. Nécessite : pip install websockets. Tous les messages et l'aide : --lang fr|en|auto (python diag_carte.py --help).
Codes de sortie : 0 serveur bon, 1 serveur injoignable, 2 ancien serveur (pseudos sans clé), 3 aucun pseudo avec la clé, 4 origine refusée.
"""
import argparse, asyncio, json, sys

# ---- langue des messages (v36) : textes intégrés par build.py (src/i18n/*.json, clés py.*) ; --lang fr|en|auto ou WEB3D_LANG ----
import json as _json, locale as _locale, os as _os, pathlib as _pl, sys as _sys

# fabrication (build.py) : la ligne suivante devient I18N_DATA = { "fr": {...}, "en": {...} }
I18N_DATA = _json.loads(r'''{"en":{"_name":"English","py.common.help":"show this help message and exit","py.common.lang_help":"language of the messages and of this help: fr, en or auto (default: the system's language; environment variable WEB3D_LANG is equivalent). Available: {0}","py.common.optionals":"options","py.common.positionals":"arguments","py.common.version_mark":"{0}, fingerprint {1}","py.common.version":"show the version and exit","py.diag.desc":"diag_carte.py {0}: diagnoses the nicknames of the map. Asks the presence server the way the map does, with and without the key, and says what is missing. Changes nothing. Requires: pip install websockets. Exit codes: 0 server fine, 1 server unreachable, 2 old server (nicknames without key), 3 no nickname with the key, 4 origin refused.","py.diag.epilog":"Examples:\n  python diag_carte.py ws://ADDRESS:8765 MY_KEY\n  python diag_carte.py wss://ADDRESS MY_KEY https://YOUR-SITE","py.diag.help.url":"address of the presence server (ws:// or wss://), the same as in the configuration of your regions","py.diag.help.key":"the nicknames key (--map-names-key of the server)","py.diag.help.origin":"the address of YOUR SITE, without a path (for example https://YOUR-SITE), if the server only accepts certain sites (--origins, --creators)","py.diag.server_origin":"Server: {0} (announced origin: {1})","py.diag.server_noorigin":"Server: {0} (no origin announced)","py.diag.err_ask":"ERROR: cannot query the server ({0}: {1}).","py.diag.err_origin":"  -> the server REFUSES the origin: it only accepts the pages of certain sites (--origins or --creators).\n     Run it again with the address of your site as 3rd argument, for example: python diag_carte.py {0} KEY https://YOUR-SITE","py.diag.err_other":"  -> wrong address or port, server stopped, firewall, or ws:// address instead of wss:// (or the opposite).","py.diag.no_names_field":"(no names field)","py.diag.no_viewers_field":"(no viewers field)","py.diag.no_key":"Without key: rooms {0}, visitors {1}, nicknames: {2}","py.diag.with_key":"With the key: rooms {0}, visitors {1}\n              nicknames of the walkers: {2}\n              nicknames in global view: {3}","py.diag.res_old":"RESULT: this server gives the nicknames WITHOUT a key: it is the old presence_server.py file (1.3.1, public nicknames).\n  -> copy the new presence_server.py (dist folder of the repository) to the server and restart it with --map-names-key YOUR_KEY","py.diag.res_nokey":"RESULT: with the key, the server gives NO nickname. Three possible causes:\n  1. the server was not started with --map-names-key YOUR_KEY (the old --map-names option has no effect): check the launch line,\n     then the console at startup: it must say that nicknames are given to the maps that present the key;\n  2. the key typed here is not exactly the one used at launch (capitals, spaces, quotes);\n  3. the presence_server.py file of the server is too old a version.\n  (after 5 wrong keys in a minute the server stops listening: wait a minute before trying again)","py.diag.res_nobody":"RESULT: the server is FINE (the key is accepted), but nobody is connected right now: no nickname to show.\n  -> open a region of this server in another browser (walk with the P key), then run this diagnosis again.","py.diag.res_ok":"RESULT: the server is FINE: the key is accepted and nicknames are given.\n  If the map shows none, the problem is on the page side:\n  1. the carte.html file of the web server is not the up-to-date version: copy dist\\\\carte.html again (and dist\\\\index.html for the map opened with M);\n  2. the address you open must end with #pseudos=YOUR_KEY (for example .../carte.html#pseudos=YOUR_KEY);\n  3. a key with & + % # or spaces is misread in the address: use letters and digits;\n  4. reload the page bypassing the cache (Ctrl+F5)."},"fr":{"_name":"Français","py.common.help":"afficher ce message d'aide et quitter","py.common.lang_help":"langue des messages et de l'aide : fr, en ou auto (défaut : langue du système ; variable d'environnement WEB3D_LANG équivalente). Disponibles : {0}","py.common.optionals":"options","py.common.positionals":"arguments","py.common.version_mark":"{0}, empreinte {1}","py.common.version":"afficher la version et quitter","py.diag.desc":"diag_carte.py {0} : diagnostic des pseudos de la carte. Interroge le serveur de présence comme le fait la carte, avec et sans la clé, et dit ce qui manque. Ne modifie rien. Nécessite : pip install websockets. Codes de sortie : 0 serveur bon, 1 serveur injoignable, 2 ancien serveur (pseudos sans clé), 3 aucun pseudo avec la clé, 4 origine refusée.","py.diag.epilog":"Exemples :\n  python diag_carte.py ws://ADRESSE:8765 MA_CLE\n  python diag_carte.py wss://ADRESSE MA_CLE https://VOTRE-SITE","py.diag.help.url":"adresse du serveur de présence (ws:// ou wss://), la même que dans la configuration de vos régions","py.diag.help.key":"la clé des pseudos (--map-names-key du serveur)","py.diag.help.origin":"l'adresse de VOTRE SITE, sans chemin (par exemple https://VOTRE-SITE), si le serveur n'accepte que certains sites (--origins, --creators)","py.diag.server_origin":"Serveur : {0} (origine annoncée : {1})","py.diag.server_noorigin":"Serveur : {0} (aucune origine annoncée)","py.diag.err_ask":"ERREUR : impossible de questionner le serveur ({0} : {1}).","py.diag.err_origin":"  -> le serveur REFUSE l'origine : il n'accepte que les pages de certains sites (--origins ou --creators).\n     Relancez en ajoutant en 3e argument l'adresse de votre site, par exemple : python diag_carte.py {0} CLE https://VOTRE-SITE","py.diag.err_other":"  -> adresse ou port faux, serveur arrêté, pare-feu, ou adresse ws:// au lieu de wss:// (ou l'inverse).","py.diag.no_names_field":"(aucun champ names)","py.diag.no_viewers_field":"(aucun champ viewers)","py.diag.no_key":"Sans clé    : salons {0}, visiteurs {1}, pseudos : {2}","py.diag.with_key":"Avec la clé : salons {0}, visiteurs {1}\n              pseudos des promeneurs : {2}\n              pseudos en vue globale : {3}","py.diag.res_old":"RESULTAT : ce serveur donne les pseudos SANS clé : c'est l'ancien fichier presence_server.py (1.3.1, pseudos publics).\n  -> copiez le nouveau presence_server.py (dossier dist du dépôt) sur le serveur et relancez-le avec --map-names-key VOTRE_CLE","py.diag.res_nokey":"RESULTAT : avec la clé, le serveur ne donne AUCUN pseudo. Trois causes possibles :\n  1. le serveur n'a pas été lancé avec --map-names-key VOTRE_CLE (l'ancienne option --map-names est sans effet) : vérifiez la ligne de lancement,\n     puis la console au démarrage : elle doit dire que les pseudos sont donnés aux cartes qui présentent la clé ;\n  2. la clé tapée ici n'est pas exactement celle du lancement (majuscules, espaces, guillemets) ;\n  3. le fichier presence_server.py du serveur est une version trop ancienne.\n  (après 5 clés fausses en une minute le serveur n'écoute plus : attendez une minute avant de réessayer)","py.diag.res_nobody":"RESULTAT : le serveur est BON (la clé est acceptée), mais personne n'est connecté en ce moment : aucun pseudo à montrer.\n  -> ouvrez une région de ce serveur dans un autre navigateur (promenade avec la touche P), puis relancez ce diagnostic.","py.diag.res_ok":"RESULTAT : le serveur est BON : la clé est acceptée et des pseudos sont donnés.\n  Si la carte n'en affiche pas, le problème est du côté de la page :\n  1. le fichier carte.html du serveur web n'est pas la version à jour : recopiez dist\\\\carte.html (et dist\\\\index.html pour la carte ouverte par M) ;\n  2. l'adresse ouverte doit se terminer par #pseudos=VOTRE_CLE (par exemple .../carte.html#pseudos=VOTRE_CLE) ;\n  3. une clé avec & + % # ou des espaces est mal lue dans l'adresse : prenez des lettres et des chiffres ;\n  4. rechargez la page en forçant le cache (Ctrl+F5)."}}''')


def _load():
    if I18N_DATA is not None:
        return I18N_DATA
    here = _pl.Path(__file__).resolve().parent
    for d in (here / "i18n", here.parent / "src" / "i18n"):
        if d.is_dir():
            return {p.stem: _json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json"))}
    return {}


_DATA = _load()
I18N_CODES = sorted(_DATA)


def _match(tag):
    c = str(tag or "").lower().replace("-", "_").split("_")[0]
    return c if c in _DATA else None


def i18n_system_lang():
    """langue du système (variables d'environnement, locale Python, langue d'interface de Windows) ; None si inconnue"""
    for v in ("LC_ALL", "LC_MESSAGES", "LANGUAGE", "LANG"):
        c = _match(_os.environ.get(v, "").split(":")[0])
        if c:
            return c
    try:
        c = _match((_locale.getlocale()[0] or ""))
        if c:
            return c
    except Exception:
        pass
    try:
        import ctypes
        lid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        c = _match(_locale.windows_locale.get(lid, ""))
        if c:
            return c
    except Exception:
        pass
    return None


def i18n_detect_lang(argv=None):
    """--lang CODE ou --lang=CODE dans argv, sinon WEB3D_LANG, sinon la langue du système, sinon l'anglais ('auto' = laisser le système décider)"""
    argv = list(_sys.argv[1:] if argv is None else argv)
    want = None
    for i, a in enumerate(argv):
        if a == "--lang" and i + 1 < len(argv):
            want = argv[i + 1]
        elif a.startswith("--lang="):
            want = a.split("=", 1)[1]
    for cand in (want, _os.environ.get("WEB3D_LANG")):
        if cand and cand.lower() != "auto" and _match(cand):
            return _match(cand)
    return i18n_system_lang() or ("en" if "en" in _DATA else (I18N_CODES[0] if I18N_CODES else "en"))


I18N_LANG = i18n_detect_lang()


def i18n_set_lang(code):
    global I18N_LANG
    I18N_LANG = _match(code) or I18N_LANG


def _tr(key, *a):
    """texte de la clé dans la langue courante (anglais, français, clé en repli) ; avec des arguments : str.format"""
    s = None
    for lg in (I18N_LANG, "en", "fr"):
        v = _DATA.get(lg, {}).get(key)
        if isinstance(v, str):
            s = v
            break
    if s is None:
        s = key
    return s.format(*a) if a else s


def i18n_lang_help():
    """texte d'aide de l'option --lang (codes disponibles)"""
    return _tr("py.common.lang_help", ", ".join(I18N_CODES))


def i18n_add_common(ap):
    """ajoute -h/--help traduit et --lang à un parseur créé avec add_help=False ; titres des groupes traduits"""
    ap.add_argument("-h", "--help", action="help", help=_tr("py.common.help"))
    ap.add_argument("--lang", default="auto", metavar="CODE", help=i18n_lang_help())
    try:
        ap._positionals.title = _tr("py.common.positionals")
        ap._optionals.title = _tr("py.common.optionals")
    except Exception:
        pass


VERSION = "1.10.2 (12/11/2026)"      # remplacé par build.py (fichier VERSION) dans dist/diag_carte.py
MARK = "8e3103b7"      # empreinte du fichier fabriqué, inscrite par build.py ; reste telle quelle depuis tools/


def version_tag():
    return VERSION if MARK.startswith("__") else _tr("py.common.version_mark", VERSION, MARK)


async def demander(url, cle, origine):
    try:
        from websockets.asyncio.client import connect
    except ImportError:
        from websockets import connect
    async with connect(url, open_timeout=10, **({"origin": origine} if origine else {})) as ws:
        await ws.send(json.dumps({"t": "rooms", "key": cle} if cle is not None else {"t": "rooms"}))
        return json.loads(await asyncio.wait_for(ws.recv(), 10))


def origine_refusee(e):
    """vrai si le serveur a refusé l'origine : réponse HTTP 403 à l'ouverture, ou fermeture 4003 (refus d'un créateur). Jamais d'après les chiffres du texte :
    un numéro de port comme 54003 contient « 403 »."""
    rep = getattr(e, "response", None)                                   # InvalidStatus (websockets récent)
    statut = getattr(rep, "status_code", None) or getattr(e, "status_code", None)   # InvalidStatusCode (ancien)
    fermeture = getattr(getattr(e, "rcvd", None), "code", None) or getattr(e, "code", None)   # ConnectionClosed
    return statut == 403 or fermeture == 4003 or "origin" in str(e).lower()


async def diagnostiquer(url, cle, origine):
    print(_tr("py.diag.server_origin", url, origine) if origine else _tr("py.diag.server_noorigin", url))
    try:
        sans = await demander(url, None, origine)
        avec = await demander(url, cle, origine)
    except Exception as e:
        print(_tr("py.diag.err_ask", type(e).__name__, e))
        if origine_refusee(e):
            print(_tr("py.diag.err_origin", url))
            return 4
        print(_tr("py.diag.err_other"))
        return 1
    print(_tr("py.diag.no_key", sans.get("rooms"), sans.get("visitors"), sans.get("names", _tr("py.diag.no_names_field"))))
    print(_tr("py.diag.with_key", avec.get("rooms"), avec.get("visitors"), avec.get("names", _tr("py.diag.no_names_field")),
              avec.get("viewers", _tr("py.diag.no_viewers_field"))))
    print()
    if "names" in sans:
        print(_tr("py.diag.res_old"))
        return 2
    if "names" not in avec:
        print(_tr("py.diag.res_nokey"))
        return 3
    if not (avec.get("names") or avec.get("viewers")):
        print(_tr("py.diag.res_nobody"))
        return 0
    print(_tr("py.diag.res_ok"))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=_tr("py.diag.desc", version_tag()), epilog=_tr("py.diag.epilog"),
                                 formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False)
    i18n_add_common(ap)
    ap.add_argument("--version", action="version", version=f"diag_carte {version_tag()}", help=_tr("py.common.version"))
    ap.add_argument("url", metavar="ws://HOST:PORT", help=_tr("py.diag.help.url"))
    ap.add_argument("key", metavar="KEY", help=_tr("py.diag.help.key"))
    ap.add_argument("origin", nargs="?", metavar="ORIGIN", help=_tr("py.diag.help.origin"))
    a = ap.parse_args(argv)
    try:
        return asyncio.run(diagnostiquer(a.url, a.key, a.origin))
    except KeyboardInterrupt:
        return 1


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # sortie dans un tube ou un fichier (Windows, cp1252) : un caractere hors de la page de code est remplace, il n'arrete pas l'outil
        try:
            _s.reconfigure(errors="replace")
        except Exception:
            pass
    sys.exit(main())
