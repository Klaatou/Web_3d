#!/usr/bin/env python3
"""Tests v37 (lot 3) : région par défaut (default.json, regions.json, message), --lib-url (relatif, adresse complète, retenu pour --maj), sous-dossiers
(?region=a/b/nom, cas refusés, règle JS = règle Python). Lancer : python tests/v37_region.py (après python build.py)
"""
import asyncio, importlib.util, json, os, shutil, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

spec = importlib.util.spec_from_file_location("g2h", str(DIST / "glb2html.py"))
g2h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g2h)

site = tmp / "site"
site.mkdir()
sol_glb(site / "sol.glb")
Z = tmp / "z.json"
Z.write_text(json.dumps([{"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0.0}]), encoding="utf-8")
BASE = ["--zones", Z, "--no-sea", "--target", "0,0,0", *vend]


def gen(dossier, nom, room, *extra, glb=None):
    dossier.mkdir(parents=True, exist_ok=True)
    return html(glb or site / "sol.glb", "-o", dossier / (nom + ".html"), "--room", room, *BASE, *extra)


def lire(p):
    return json.loads(p.read_text(encoding="utf-8"))


print("--- 3.1 région par défaut : fabrication")
d1 = site / "un"
r = gen(d1, "Ile", "ile", "--shared-shell")
rapport(lire(d1 / "default.json") == {"region": "Ile"}, "première région d'un dossier : default.json = {\"region\": \"Ile\"}", (d1 / "default.json").read_text())
gen(d1, "Ankh", "ankh", "--shared-shell")
rapport(lire(d1 / "default.json") == {"region": "Ile"}, "une deuxième région ne change pas default.json")
d2 = site / "deux"
gen(d2, "Ile", "ile", "--shared-shell")
gen(d2, "Ankh", "ankh", "--shared-shell", "--default")
rapport(lire(d2 / "default.json") == {"region": "Ankh"}, "--default : la région devient la région par défaut même si default.json existe")
html("-o", d2 / "Ile.html", "--shared-shell", "--maj", "--room", "ile")
rapport(lire(d2 / "default.json") == {"region": "Ankh"}, "--maj ne touche pas default.json")
html("-o", d2 / "Ile.html", "--shared-shell", "--maj", "--default")
rapport(lire(d2 / "default.json") == {"region": "Ile"}, "--maj --default l'écrase")
# repli regions.json
d3 = site / "trois"
gen(d3, "Ile", "ile", "--shared-shell")
gen(d3, "Ankh", "ankh", "--shared-shell", "--register", d3 / "regions.json", "--region-name", "Ankh")
(d3 / "default.json").unlink()
reg = lire(d3 / "regions.json")
reg.insert(0, {"id": "loin", "name": "Loin", "url": "https://autre.example/index.html?region=Zzz", "x": 0, "y": 0})
reg.insert(1, {"id": "mauvais", "name": "Mauvais", "url": "index.html?region=..%2Fx", "x": 1, "y": 0})
(d3 / "regions.json").write_text(json.dumps(reg), encoding="utf-8")
rapport(any(e["url"] == "index.html?region=Ankh" for e in reg), "--register écrit index.html?region=Ankh", [e["url"] for e in reg])
# message d'erreur
d4 = site / "quatre"
gen(d4, "Ile", "ile", "--shared-shell")
(d4 / "default.json").unlink()
# un dossier avec la seule coquille (copiée) : rien à ouvrir
d5 = site / "cinq"
d5.mkdir()
shutil.copy(d4 / "index.html", d5 / "index.html")
shutil.copytree(d4 / "lib", d5 / "lib")

print("--- 3.2 --lib-url")
app = site / "app"
gen(app, "Ile", "ile", "--shared-shell", "--lib-url", "../lib")
rapport((site / "lib" / "three-0.160.0").is_dir() and not (app / "lib").exists(), "lib/ créé à ../lib, pas à côté de la coquille")
shell = (app / "index.html").read_text(encoding="utf-8")
rapport('"three": "../lib/three-0.160.0/' in shell.replace("\n", " ").replace('  ', ' ') or "../lib/three-0.160.0/three.module.js" in shell, "table d'import de la coquille : ../lib/three-0.160.0/…")
rapport("setDecoderPath('../lib/three-0.160.0/draco/')" in shell, "chemin Draco suivi aussi")
rapport(lire(app / "Ile.config.json")["libUrl"] == "../lib", "libUrl retenu dans la config")
avant = (app / "index.html").read_bytes()
html("-o", app / "Ile.html", "--shared-shell", "--maj", "--wave", "1.5")
rapport((app / "index.html").read_bytes() == avant and not (app / "lib").exists() and lire(app / "Ile.config.json")["libUrl"] == "../lib" and lire(app / "Ile.config.json")["wave"] == 1.5, "--maj retrouve le dossier lib : coquille identique, pas de lib/ à côté, libUrl gardé")
r = html("-o", app / "Autre.html", "--shared-shell", "--lib-url", "http://ADRESSE/lib", ok=True, cwd=tmp) if False else None
ab = site / "abs"
gen(ab, "Ile", "ile", "--shared-shell", "--lib-url", "http://ADRESSE/lib")
sh = (ab / "index.html").read_text(encoding="utf-8")
rapport(not (ab / "lib").exists(), "adresse complète : rien n'est copié")
r = run(DIST / "glb2html.py", site / "sol.glb", "-o", site / "mauvais" / "X.html", "--shared-shell", "--lib-url", "javascript:alert(1)", *BASE, ok=False)
rapport(r.returncode != 0, "--lib-url refusé s'il n'est ni un chemin relatif ni une adresse http(s)", r.stderr[-200:])
r = run(DIST / "glb2html.py", site / "sol.glb", "-o", site / "mauvais" / "X.html", "--shared-shell", "--lib-url", "../l?x=1", *BASE, ok=False)
rapport(r.returncode != 0, "--lib-url avec ? refusé")

print("--- 3.3 sous-dossiers")
d6 = site / "six"
d6.mkdir()
gen(d6 / "sous" / "dossier", "Ile", "ile6", "--shared-shell", d6 / "index.html")
rapport(not (d6 / "sous" / "dossier" / "Ile.html").exists() and (d6 / "sous" / "dossier" / "Ile.glb").is_file() and (d6 / "sous" / "dossier" / "Ile.config.json").is_file() and (d6 / "sous" / "dossier" / "Ile.zones.json").is_file(), "région dans un sous-dossier : .glb, .config.json, .zones.json là, aucune page")
rapport((d6 / "index.html").is_file() and (d6 / "lib" / "three-0.160.0").is_dir() and lire(d6 / "default.json") == {"region": "sous/dossier/Ile"}, "coquille, lib/ et default.json dans le dossier parent donné par l'option", (d6 / "default.json").read_text() if (d6 / "default.json").exists() else None)
for mauvais in (["--shared-shell", d6 / "index.html", "-o", site / "ailleurs" / "X.html"],):
    r = run(DIST / "glb2html.py", site / "sol.glb", *BASE, *mauvais, ok=False)
    rapport(r.returncode != 0, "région hors du dossier de la coquille : refusée", r.stderr[-160:])
r = run(DIST / "glb2html.py", site / "sol.glb", "-o", d6 / "a:b" / "X.html", "--shared-shell", d6 / "index.html", *BASE, ok=False)
rapport(r.returncode != 0, "segment contenant « : » refusé à la fabrication", r.stderr[-160:])

NOMS = ["Ile", "a/b/Ile", "Île d'Ankh", "sous/dossier/Ile", "a b/c(1)/x-y_z.v2", "é/ü", "a/.cache/x", "a/../b", "../x", "/abs", "a//b", "a:b/c", "a\\b", "a/b?", "a/b#", "x/y.", ".caché", "a/..b/c", "a/ /c", "ab/c d", "a%2Fb"]
attendu = {n: g2h.valid_region_name(n) for n in NOMS}
rapport(attendu["a/b/Ile"] and attendu["é/ü"] and attendu["a b/c(1)/x-y_z.v2"] and not attendu["a/../b"] and not attendu["a:b/c"] and not attendu["/abs"] and not attendu["a\\b"] and not attendu["a/.cache/x"] and not attendu["a//b"], "règle Python : cas valides et refusés", attendu)


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        proc, port = serveur(site)
        B = f"http://127.0.0.1:{port}/"
        try:
            print("--- 3.1 région par défaut dans le navigateur")
            for rel, room, nom in (("un/index.html", "ile", "une seule région : adresse sans paramètre"), ("deux/index.html", "ile", "--default puis --maj --default : Ile"), ("trois/index.html", "ankh", "repli regions.json (adresses absolue et invalide ignorées) : Ankh")):
                o = await Onglet(br).ouvrir(B + rel, init=STUB)
                t = await o.ev("document.title")
                rapport(t == room, f"{nom} → salon « {room} »", t)
                await o.ctx.close()
            o = await Onglet(br).ouvrir(B + "un/index.html?region=Ankh", init=STUB)
            rapport(await o.ev("document.title") == "ankh", "?region=Ankh l'emporte sur default.json")
            await o.ctx.close()
            # message d'erreur
            for rel in ("quatre/index.html", "cinq/index.html"):
                o = await Onglet(br).ouvrir(B + rel, init=STUB, viewer=False)
                await o.pg.wait_for_timeout(1500)
                m = await o.ev("document.getElementById('msg') ? document.getElementById('msg').textContent : ''")
                rapport("default.json" in m and "?region=" in m and m.count(".") <= 4, f"{rel} : message d'erreur d'une phrase qui dit quoi faire", m)
                await o.ctx.close()
            # default.json piégé
            (site / "cinq" / "default.json").write_text(json.dumps({"region": "../un/Ile"}), encoding="utf-8")
            reqs = []
            o = Onglet(br)
            o.ctx = await br.new_context(locale=LOC)
            pg = await o.ctx.new_page()
            pg.on("request", lambda rq: reqs.append(rq.url))
            await pg.goto(B + "cinq/index.html")
            await pg.wait_for_timeout(1500)
            rapport(not any("Ile.config" in u for u in reqs), "default.json qui contient « ../un/Ile » : refusé, aucune requête vers cette région", [u for u in reqs if "config" in u])
            await o.ctx.close()

            print("--- 3.2 lib hors du dossier")
            o = await Onglet(br).ouvrir(B + "app/index.html", init=STUB)
            rapport(await o.ev("document.title") == "ile" and not o.errs, "coquille dans app/, lib/ à côté du dossier : la région s'ouvre", o.errs[:2])
            await o.ctx.close()
            # adresse complète (même origine : pas de CORS à gérer) : on regénère la coquille avec l'adresse du lib de ../lib
            (ab / "index.html").unlink()   # une coquille existante différente n'est jamais écrasée : on la retire pour la refaire avec l'adresse du serveur de test
            html(site / "sol.glb", "-o", ab / "Ile.html", "--room", "ile", *BASE, "--shared-shell", "--lib-url", f"http://127.0.0.1:{port}/lib")
            rapport(not (ab / "lib").exists() and f"http://127.0.0.1:{port}/lib/three-0.160.0/three.module.js" in (ab / "index.html").read_text(encoding="utf-8").replace("\\/", "/"), "adresse complète : table d'import sur cette adresse, rien de copié")
            reqs = []
            o = Onglet(br)
            o.ctx = await br.new_context(locale=LOC)
            pg = await o.ctx.new_page()
            pg.on("request", lambda rq: reqs.append(rq.url))
            await pg.goto(B + "abs/index.html")
            await pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            rapport(any("/lib/three-0.160.0/three.module.js" in u and "/abs/" not in u for u in reqs), "les modules viennent bien de l'adresse complète")
            await o.ctx.close()

            print("--- 3.3 sous-dossiers dans le navigateur")
            o = await Onglet(br).ouvrir(B + "six/index.html?region=sous/dossier/Ile", init=STUB)
            rapport(await o.ev("document.title") == "ile6", "?region=sous/dossier/Ile : la région d'un sous-dossier s'ouvre")
            await o.ctx.close()
            o = await Onglet(br).ouvrir(B + "six/index.html", init=STUB)
            rapport(await o.ev("document.title") == "ile6", "sans paramètre, default.json = sous/dossier/Ile")
            await o.ctx.close()
            # règle JS = règle Python, et aucune requête pour les noms refusés
            ecarts, vus = [], {}
            for n in NOMS:
                reqs = []
                ctx = await br.new_context(locale=LOC)
                pg = await ctx.new_page()
                pg.on("request", lambda rq, reqs=reqs: reqs.append(rq.url))
                await pg.goto(B + "six/index.html?region=" + urllib.parse.quote(n, safe=""))
                await pg.wait_for_timeout(700)
                demande = any(u.endswith(".config.json") for u in reqs)
                vus[n] = demande
                if demande != attendu[n]:
                    ecarts.append((n, "JS accepte" if demande else "JS refuse", "Python accepte" if attendu[n] else "Python refuse"))
                await ctx.close()
            rapport(not ecarts, f"la règle JS (coquille) et la règle Python donnent le même verdict sur {len(NOMS)} noms", ecarts)
            rapport(not any(vus[n] for n in ("a/../b", "../x", "/abs", "a:b/c", "a\\b", "a/b?", "a/b#")), "les cas refusés (.., :, \\, ?, #, chemin absolu) ne déclenchent aucune requête", {n: vus[n] for n in vus})
        finally:
            proc.terminate()
            await br.close()
    print("\nRÉSULTAT : " + ("tout est passé" if not h37.bad else f"{h37.bad} échec(s)"))
    sys.exit(1 if h37.bad else 0)


asyncio.run(main())
