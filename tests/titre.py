#!/usr/bin/env python3
"""Tests 1.4.7 : titre affiche distinct du salon (cle title de la config) et glb2html.py --scan-sites --prune-missing.

Verifie : --title ecrit « title » dans NOM.config.json en mode coquille et en mode tuiles (plus d'avertissement « ignore ») ; sans --title aucune cle
« title » ; --update garde le titre s'il n'est pas redonne et le remplace s'il l'est ; l'onglet du navigateur affiche le titre (le salon « room » ne change
pas), ou le salon quand il n'y a pas de titre ; --scan-sites donne a une NOUVELLE fiche le titre comme nom ; --prune-missing retire les fiches locales
introuvables (les externes restent), --dry-run n'ecrit rien, sans l'option rien n'est supprime, seul il est refuse, anglais.

Prerequis : python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/titre.py
"""
import asyncio, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37
import glbfab

DATA = ROOT / "tests" / "data"
site = tmp / "site"
site.mkdir()


def cfg(nom):
    return json.loads((site / f"{nom}.config.json").read_text(encoding="utf-8"))


print("--- 1. generation : --title ecrit « title » (coquille)")
r = html(DATA / "walk3.glb", "-o", site / "houses.html", "--shared-shell", "--room", "houses", "--title", "Houses")
rapport(cfg("houses").get("title") == "Houses" and cfg("houses").get("room") == "houses", "coquille : title = Houses, room = houses (le salon ne change pas)", cfg("houses"))
rapport("ignor" not in r.stdout + r.stderr, "plus d'avertissement « title est ignore »", r.stdout + r.stderr)
html(DATA / "walk3.glb", "-o", site / "plain.html", "--shared-shell", "--room", "plain")
rapport("title" not in cfg("plain"), "sans --title : aucune cle title (les configs existantes ne changent pas)", sorted(cfg("plain"))[:5])
html(DATA / "walk3.glb", "-o", site / "long.html", "--shared-shell", "--title", "x" * 80)
rapport(len(cfg("long").get("title", "")) == 60, "titre tronque a 60 caracteres", len(cfg("long").get("title", "")))

print("--- 2. --update : le titre est garde, ou remplace s'il est redonne")
html("--update", "-o", site / "houses.html", "--shared-shell", site / "index.html")
rapport(cfg("houses").get("title") == "Houses", "--update sans --title : titre garde", cfg("houses").get("title"))
html("--update", "-o", site / "houses.html", "--shared-shell", site / "index.html", "--title", "Maisons")
rapport(cfg("houses").get("title") == "Maisons", "--update --title Maisons : titre remplace", cfg("houses").get("title"))
html("--update", "-o", site / "houses.html", "--shared-shell", site / "index.html", "--title", "Houses")
rapport(cfg("houses").get("title") == "Houses" and cfg("houses").get("room") == "houses", "retour a Houses, salon inchange", cfg("houses"))

print("--- 3. generation : --title en mode tuiles")
src = tmp / "src"
src.mkdir()
glbfab.region(src / "Syn.glb")
run(DIST / "glb2tiles.py", src / "Syn.glb", "--nopause", "--forcer", "--budget-tri", "900", "--min", "64")
r = html("--tiles", src / "Syn.tiles.json", "-o", site / "tuilee.html", "--shared-shell", "--title", "Region en tuiles", "--no-sea")
rapport(cfg("tuilee").get("title") == "Region en tuiles" and "ignor" not in r.stdout + r.stderr, "tuiles : title ecrit, pas d'avertissement", (cfg("tuilee").get("title"), r.stderr[-120:]))

http, port = serveur(site)
BASE = f"http://127.0.0.1:{port}/"


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        print("--- 4. l'onglet du navigateur")
        o = await Onglet(br).ouvrir(BASE + "index.html?region=houses")
        t, room = await o.ev("[document.title, window.__viewer ? 'ok' : '']"), None
        rapport(t[0] == "Houses", "region avec title : l'onglet affiche « Houses »", t)
        rapport(not o.errs, "aucune erreur de page", o.errs)
        await o.ctx.close()
        o = await Onglet(br).ouvrir(BASE + "index.html?region=plain")
        rapport(await o.ev("document.title") == "plain", "region sans title : l'onglet affiche le salon (comme avant)", await o.ev("document.title"))
        await o.ctx.close()
        await br.close()


asyncio.run(main())
http.kill()

print("--- 5. --scan-sites : nom d'une nouvelle fiche, --prune-missing")


def scan(*a, ok=True, lang="fr"):
    env = dict(os.environ, WEB3D_LANG=lang)
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), *map(str, a)], capture_output=True, text=True, env=env)
    if ok and r.returncode:
        sys.exit(f"[ECHEC] {a}\n{r.stdout}{r.stderr}")
    return r


S = tmp / "Sites"
for d in ("houses", "plain"):
    (S / d).mkdir(parents=True)
(S / "index.html").write_text("x", encoding="utf-8")
(S / "houses" / "houses.config.json").write_text(json.dumps({"room": "houses", "title": "Houses", "presenceUrl": ""}), encoding="utf-8")
(S / "plain" / "plain.config.json").write_text(json.dumps({"room": "plain", "presenceUrl": ""}), encoding="utf-8")
DEPART = {"showUrl": False, "regions": [
    {"id": "gone", "name": "Region disparue", "url": "index.html?region=gone/gone", "x": 5, "y": 0, "spawn": "", "room": "gone", "thumb": "", "presence": ""},
    {"id": "ext", "name": "Externe", "url": "https://autre.example/index.html?region=x", "x": 6, "y": 0, "spawn": "", "room": "ext", "thumb": "", "presence": ""}]}
REG = S / "regions.json"
REG.write_text(json.dumps(DEPART, indent=1), encoding="utf-8")


def noms():
    return {r["id"]: r["name"] for r in json.loads(REG.read_text(encoding="utf-8"))["regions"]}


avant = REG.read_bytes()
r = scan("--scan-sites", S, "--prune-missing", "--dry-run")
rapport(REG.read_bytes() == avant and "Region disparue" in r.stdout and "retirée" in r.stdout and "rien n'a été écrit" in r.stdout, "--prune-missing --dry-run : liste la fiche, n'ecrit rien", r.stdout)
r = scan("--scan-sites", S)
n = noms()
rapport("gone" in n and "ext" in n and n.get("houses") == "Houses" and n.get("plain") == "plain", "sans --prune-missing : rien n'est supprime ; nouvelle fiche nommee par le title (Houses), sinon par le fichier (plain)", n)
rapport("fiche gardée" in r.stdout or "gardée" in r.stdout, "la fiche introuvable est signalee et gardee", r.stdout)
r = scan("--scan-sites", S, "--prune-missing")
n = noms()
rapport("gone" not in n and "ext" in n and "houses" in n and "plain" in n, "--prune-missing : fiche locale introuvable retiree, externe et trouvees gardees", n)
rapport("1 fiche(s) orpheline(s) retirée(s)" in r.stdout, "compte rendu : 1 fiche retiree", r.stdout)
r = scan("--scan-sites", S, "--prune-missing")
rapport("0 fiche(s) orpheline(s)" in r.stdout and noms() == n, "deuxieme passage : plus rien a retirer, rien ne change", r.stdout)
(S / "houses" / "houses.config.json").write_text(json.dumps({"room": "houses", "title": "Autre nom", "presenceUrl": ""}), encoding="utf-8")
scan("--scan-sites", S)
rapport(noms().get("houses") == "Houses", "une fiche existante garde son nom meme si le title change", noms())
r = scan("--prune-missing", ok=False)
rapport(r.returncode != 0 and "--scan-sites" in r.stderr, "--prune-missing seul : refuse avec un message", (r.returncode, r.stderr[-150:]))
REG.write_text(json.dumps(DEPART, indent=1), encoding="utf-8")
r = scan("--scan-sites", S, "--prune-missing", lang="en")
rapport("removed" in r.stdout and "gone" not in noms(), "anglais : message « removed »", r.stdout)

sys.exit(1 if resultat() else 0)
