#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diag_carte.py : diagnostic des pseudos de la carte. Interroge le serveur de présence comme le fait la carte, avec et sans la clé, et dit ce qui manque.

Ne modifie rien. Nécessite : pip install websockets. Tous les messages et l'aide : --lang fr|en|auto (python diag_carte.py --help).
Codes de sortie : 0 serveur bon, 1 serveur injoignable, 2 ancien serveur (pseudos sans clé), 3 aucun pseudo avec la clé, 4 origine refusée.
"""
import argparse, asyncio, json, sys

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
_tr, i18n_add_common = _I18N._tr, _I18N.i18n_add_common
# <</I18N_PY>>

VERSION = "__VERSION__"      # remplacé par build.py (fichier VERSION) dans dist/diag_carte.py
MARK = "__MARK__"      # empreinte du fichier fabriqué, inscrite par build.py ; reste telle quelle depuis tools/


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
