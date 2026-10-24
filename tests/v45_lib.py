#!/usr/bin/env python3
"""Tests v45 (coquille, dossier lib) : la coquille se règle par UNE ligne (const LIB), construite par un script classique avant tout module.

Vérifie : ligne const LIB unique et pas de balise importmap dans la coquille, dist/index.html = build_shell() = coquille écrite, page autonome inchangée,
démarrage dans Chromium avec ./lib puis avec ../lib (une seule ligne changée à la main, lib déplacé), --update qui garde la ligne modifiée à la main
(message, config alignée, aucune copie datée, rien créé à côté), fins de ligne CRLF acceptées, valeur refusée, --lib-url explicite prioritaire,
nouvelle région créée dans un dossier dont la coquille a été modifiée à la main, page d'essai tests/essai_importmap.html (à ouvrir aussi dans Firefox et Safari).

Prérequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v45_lib.py
"""
import asyncio, importlib.util, json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

spec = importlib.util.spec_from_file_location("g2h", str(DIST / "glb2html.py"))
g2h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g2h)
BASE = ["--no-sea", "--target", "0,0,0", *vend]


def lire(p):
    return json.loads(p.read_text(encoding="utf-8"))


def gen(dossier, nom, room, *extra):
    dossier.mkdir(parents=True, exist_ok=True)
    return html(site / "sol.glb", "-o", dossier / (nom + ".html"), "--room", room, *BASE, *extra)


def maj(dossier, *extra):
    return html("-o", dossier / "Reg.html", "--shared-shell", "--update", *extra)


def avant(dossier):
    return sorted(p.name for p in dossier.glob("index.avant-*.html"))


site = tmp / "site"; site.mkdir()
sol_glb(site / "sol.glb")

print("--- 1. coquille par défaut")
app = site / "app"
gen(app, "Reg", "r46", "--shared-shell")
shell = (app / "index.html").read_text(encoding="utf-8")
rapport(shell.count("\nconst LIB = './lib';\n") == 1, "une seule ligne const LIB = './lib';", shell.count("const LIB"))
rapport('<script type="importmap">' not in shell and "s.type = 'importmap'" in shell, "plus de balise importmap : la table est construite par un script")
rapport(shell.count("./lib") == 1, "./lib n'apparaît qu'une fois dans la coquille", shell.count("./lib"))
rapport("setDecoderPath(LIB + '/three-0.160.0/draco/')" in shell, "chemin Draco construit avec LIB")
rapport((app / "index.html").read_bytes() == g2h.build_shell().encode("utf-8"), "coquille écrite = build_shell()")
rapport((DIST / "index.html").is_file() and (DIST / "index.html").read_bytes() == (app / "index.html").read_bytes(), "dist/index.html identique, octet pour octet, à la coquille de glb2html.py")
html(site / "sol.glb", "-o", site / "auto.html", "--no-sea", "--target", "0,0,0")
auto = (site / "auto.html").read_text(encoding="utf-8")
rapport('<script type="importmap">' in auto and "const LIB" not in auto and "lib/three" not in auto, "page autonome inchangée (importmap en data:, pas de const LIB)")
a = tmp / "a2"; a.mkdir()
gen(a, "Reg", "r46", "--shared-shell", "--lib-url", "../lib")
rapport("\nconst LIB = '../lib';\n" in (a / "index.html").read_text(encoding="utf-8"), "--lib-url écrit la valeur dans la ligne const LIB")

print("--- 2. préparation : lib déplacé dans le dossier parent, une seule ligne changée")
B = site / "b"; (B / "app").mkdir(parents=True)
for f in app.glob("Reg.*"):
    shutil.copy(f, B / "app" / f.name)
shutil.copy(app / "default.json", B / "app" / "default.json")
shutil.copytree(app / "lib", B / "lib")
(B / "app" / "index.html").write_text(shell.replace("const LIB = './lib';", "const LIB = '../lib';"), encoding="utf-8", newline="\n")
rapport(not (B / "app" / "lib").exists() and (B / "lib" / "three-0.160.0").is_dir(), "lib à ../lib, rien à côté de la page")
C = site / "c"; shutil.copytree(B, C)

http, hport = serveur(site)


async def navigateur():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        shutil.copy(h37.ROOT / "tests" / "essai_importmap.html", site / "essai_importmap.html")
        o = Onglet(br)
        o.ctx = await br.new_context(locale=LOC)
        o.pg = await o.ctx.new_page()
        await o.pg.goto(f"http://127.0.0.1:{hport}/essai_importmap.html")
        await o.pg.wait_for_function("!document.getElementById('r').textContent.startsWith('Essai en cours')", timeout=15000)
        t = await o.txt("r")
        rapport(t.startswith("RÉSULTAT : OK / RESULT: OK"), "tests/essai_importmap.html : table d'import construite par script acceptée", t[:200])
        await o.ctx.close()
        for nom, chemin, attendu in (("./lib (à côté de la page)", "app/index.html", "/app/lib/three-0.160.0/three.module.js"),
                                     ("../lib (une ligne changée à la main)", "b/app/index.html", "/b/lib/three-0.160.0/three.module.js")):
            reqs = []
            o = Onglet(br)
            o.ctx = await br.new_context(locale=LOC, viewport={"width": 1000, "height": 700})
            await o.ctx.add_init_script(STUB)
            o.pg = await o.ctx.new_page()
            o.pg.on("pageerror", lambda e: o.errs.append(str(e)))
            o.pg.on("request", lambda rq: reqs.append(rq.url))
            await o.pg.goto(f"http://127.0.0.1:{hport}/{chemin}?region=Reg")
            await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            rapport(not o.errs, nom + " : la coquille démarre sans erreur", o.errs[:2])
            rapport(any(u.endswith(attendu) for u in reqs), nom + " : three.js vient bien de ce dossier", [u for u in reqs if "three.module" in u])
            ims = await o.ev("document.querySelectorAll('script[type=importmap]').length")
            rapport(ims == 1, nom + " : une seule table d'import", ims)
            await o.ctx.close()
        await br.close()


try:
    print("--- 3. démarrage dans Chromium")
    asyncio.run(navigateur())
finally:
    http.kill()

print("--- 4. --update garde la ligne modifiée à la main")
sh0 = (C / "app" / "index.html").read_bytes()
r = maj(C / "app")
rapport("const LIB" in r.stdout and "../lib" in r.stdout, "message : dossier lib repris de la coquille", r.stdout[-400:])
rapport((C / "app" / "index.html").read_bytes() == sh0 and not avant(C / "app"), "coquille inchangée, aucune copie datée")
rapport(not (C / "app" / "lib").exists(), "rien créé à côté de la page")
rapport(lire(C / "app" / "Reg.config.json")["libUrl"] == "../lib", "libUrl de la config aligné sur la coquille")
r = maj(C / "app")
rapport("const LIB" not in r.stdout and (C / "app" / "index.html").read_bytes() == sh0, "deuxième --update : plus rien à reprendre")

print("--- 5. fins de ligne CRLF (éditeur Windows)")
crlf = sh0.replace(b"\n", b"\r\n")
(C / "app" / "index.html").write_bytes(crlf)
maj(C / "app")
rapport((C / "app" / "index.html").read_bytes() == crlf and not avant(C / "app"), "coquille en CRLF reconnue identique : ni réécrite ni copie datée")
(C / "app" / "index.html").write_bytes(sh0)

print("--- 6. valeur refusée dans la ligne")
(C / "app" / "index.html").write_bytes(sh0.replace(b"const LIB = '../lib';", b"const LIB = '/abs';"))
r = maj(C / "app")
nouveau = (C / "app" / "index.html").read_text(encoding="utf-8")
rapport("\nconst LIB = '../lib';\n" in nouveau and len(avant(C / "app")) == 1, "valeur refusée : coquille renouvelée avec le dossier de la config, ancienne copie gardée", (avant(C / "app"), r.stdout[-300:]))

print("--- 7. --lib-url explicite prioritaire")
r = maj(C / "app", "--lib-url", "../lib2")
rapport("\nconst LIB = '../lib2';\n" in (C / "app" / "index.html").read_text(encoding="utf-8") and (C / "lib2" / "three-0.160.0").is_dir() and lire(C / "app" / "Reg.config.json")["libUrl"] == "../lib2", "--lib-url ../lib2 l'emporte, lib2 créé, config alignée", r.stdout[-300:])

print("--- 8. nouvelle région dans un dossier dont la coquille a été modifiée")
r = gen(C / "app", "Autre", "r46b", "--shared-shell")
rapport(lire(C / "app" / "Autre.config.json")["libUrl"] == "../lib2" and not (C / "app" / "lib").exists(), "la config de la nouvelle région suit la coquille (../lib2), rien créé à côté", lire(C / "app" / "Autre.config.json").get("libUrl"))
rapport("index.html" not in r.stderr, "aucun avertissement « la coquille existe et diffère »", r.stderr[-300:])

print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
