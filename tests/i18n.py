#!/usr/bin/env python3
"""Tests des fichiers de langue (hors navigateur) : src/i18n/*.json

- les langues ont exactement les mêmes clés, aucune valeur vide, un nom (_name), les mêmes marqueurs {0} {1}… dans chaque langue ;
- chaque clé utilisée dans le code (tr('…'), trn('…'), data-i18n="…", py : tr("…")) existe, et chaque clé du fichier est utilisée quelque part (pas de texte mort) ;
- le français contient bien des accents, l'anglais n'en contient aucun (hors noms propres listés) ;
- les clés de pluriel vont par paire (.one / .other).

Lancer : python tests/i18n.py
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIR = ROOT / "src" / "i18n"
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)), flush=True)


langs = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(DIR.glob("*.json"))}
rapport(len(langs) >= 2 and "fr" in langs and "en" in langs, f"langues présentes : {', '.join(langs)}")
ref = set(langs["fr"])
for code, d in langs.items():
    manque = sorted(ref - set(d)); en_plus = sorted(set(d) - ref)
    rapport(not manque and not en_plus, f"{code} : mêmes clés que fr ({len(d)})", {"manquantes": manque[:10], "en plus": en_plus[:10]})
    rapport(isinstance(d.get("_name"), str) and d["_name"].strip(), f"{code} : _name (nom de la langue dans sa langue)")
    vides = [k for k, v in d.items() if not isinstance(v, str) or not (v if k.endswith('.sep') else v.strip())]   # v52 : un separateur (cle en .sep) peut etre un saut de ligne
    rapport(not vides, f"{code} : aucune valeur vide ou non textuelle", vides[:10])
fr, en = langs["fr"], langs["en"]
ph = lambda s: sorted(set(re.findall(r"\{(\d+)(?::[^}]*)?\}", s)))
diff = [k for k in fr if k != "_name" and ph(fr[k]) != ph(en.get(k, ""))]
rapport(not diff, "mêmes marqueurs {0} {1}… en français et en anglais", [(k, ph(fr[k]), ph(en.get(k, ""))) for k in diff[:8]])
paires = [k for k in fr if k.endswith(".one") and k[:-4] + ".other" not in fr] + [k for k in fr if k.endswith(".other") and k[:-6] + ".one" not in fr and (k[:-6] + ".few") not in fr]
rapport(not paires, "pluriels : .one et .other vont par paire", paires[:8])
ACC = re.compile(r"[éèêëàâùûôîïçœÉÈÀÙÎÔ]")
accents_en = [k for k, v in en.items() if k != "_name" and ACC.search(v)]
rapport(not accents_en, "l'anglais ne contient aucune lettre accentuée française", accents_en[:8])
rapport(sum(1 for v in fr.values() if ACC.search(v)) > 50, "le français contient bien ses accents")

# ---- clés utilisées dans le code
src = {}
for pat in ("src/core.js", "src/template.html", "src/viewer_tpl.html", "src/i18n.js", "src/gen_tpl.py", "src/presence_server.py", "src/i18n_py.py", "tools/*.py", "gen_reference.py", "build.py"):
    for p in ROOT.glob(pat):
        src[str(p.relative_to(ROOT))] = p.read_text(encoding="utf-8")
txt = "\n".join(src.values())
used = set()
for m in re.finditer(r"""\b(?:tr|trn|tr_|_tr)\(\s*(['"])([A-Za-z0-9_.]+)\1""", txt):
    used.add(m.group(2))
for m in re.finditer(r"""data-i18n(?:-title|-ph|-aria)?=["']([A-Za-z0-9_.]+)["']""", txt):
    used.add(m.group(1))
for m in re.finditer(r"""['"]((?:page|viewer|common|py|map)\.[A-Za-z0-9_.]+)['"]""", txt):
    used.add(m.group(1))   # clés citées en toutes lettres (tables de clés)
def existe(k):
    return k in fr or (k + ".other") in fr
inconnues = sorted(k for k in used if not existe(k) and not k.endswith(".") and "*" not in k)
rapport(not inconnues, f"toutes les clés citées dans le code existent ({len(used)} citées)", inconnues[:15])
mortes = sorted(k for k in fr if k != "_name" and k not in used and not any(k == u + s for u in used for s in (".one", ".other", ".zero", ".two", ".few", ".many")) and not any(k.startswith(u) for u in used if u.endswith(".")))
rapport(not mortes, "aucune clé inutilisée dans le code", mortes[:15])
print("\nRÉSULTAT : " + ("tout est passé" if not bad else f"{bad} échec(s)"))
sys.exit(1 if bad else 0)
