#!/usr/bin/env python3
"""Tests : icone « 3D » des pages (coquille index.html, page autonome, carte.html, glb-viewer.html), remplacable par un fichier favicon.ico.

Verifie : dist/favicon.ico est un vrai fichier ICO (16, 32, 48, 64 px) ; chaque page porte une icone SVG incorporee par defaut (elle se decode) ;
quand un favicon.ico est place a cote de la page, la page l'adopte (l'icone devient ce fichier, il est servi et se decode), sans rien refaire.
Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/icone.py
"""
import asyncio, functools, http.server, os, shutil, struct, sys, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

print("--- 0. le fichier favicon.ico fabrique par build.py")
ico = (DIST / "favicon.ico").read_bytes()
res, typ, n = struct.unpack("<HHH", ico[:6])
tailles = sorted((ico[6 + 16 * i] or 256) for i in range(n))
rapport(res == 0 and typ == 1 and tailles == [16, 32, 48, 64], f"dist/favicon.ico : vrai fichier ICO, tailles {tailles}", (res, typ, n))

print("--- 1. fabrication des pages")
site = tmp / "site"; site.mkdir()
sol_glb(site / "sol.glb")
html(site / "sol.glb", "-o", site / "Seule.html", "--no-sea", "--target", "0,0,0")
html(site / "sol.glb", "-o", site / "Region.html", "--shared-shell", "--no-sea", "--target", "0,0,0")
shutil.copy(DIST / "carte.html", site / "carte.html")
shutil.copy(DIST / "glb-viewer.html", site / "glb-viewer.html")
(site / "regions.json").write_text("[]", encoding="utf-8")
for nom in ("index.html", "Seule.html", "carte.html", "glb-viewer.html"):
    t = (site / nom).read_text(encoding="utf-8")
    rapport('<link rel="icon" id="siteIcon" type="image/svg+xml" href="data:image/svg+xml,' in t and "%3E3D%3C" in t and 'i.src = "favicon.ico"' in t, f"{nom} : icone incorporee et recherche d'un favicon.ico a cote")
site2 = tmp / "site2"
shutil.copytree(site, site2)
shutil.copy(DIST / "favicon.ico", site2 / "favicon.ico")      # le seul geste : poser le fichier a cote des pages

journal = []
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *a):
        journal.append((self.path, fmt % a if a else fmt))
def serveur_web(dossier):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(H, directory=str(dossier)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"
LIEN = """() => new Promise(r => { const l = document.querySelector('link[rel~=icon]'); if (!l) return r({ href: '', type: '', w: 0 });
  const i = new Image(); i.onload = () => r({ href: l.href, type: l.type, w: i.naturalWidth }); i.onerror = () => r({ href: l.href, type: l.type, w: 0 }); i.src = l.href; })"""
PAGES = (("index.html?region=Region", True), ("Seule.html", True), ("carte.html", False), ("glb-viewer.html", False))


async def main():
    from playwright.async_api import async_playwright
    srv1, base1 = serveur_web(site)
    srv2, base2 = serveur_web(site2)
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        print("--- 2. sans favicon.ico a cote : l'icone incorporee")
        for url, viewer in PAGES:
            o = await Onglet(br).ouvrir(base1 + url, locale="fr-FR", viewer=viewer)
            await asyncio.sleep(1.5)
            r = await o.ev(LIEN)
            rapport(r["href"].startswith("data:image/svg+xml") and r["w"] > 0, f"{url} : icone incorporee, elle se decode (largeur {r['w']})")
            rapport(not o.errs, f"{url} : aucune erreur de page", o.errs)
            await o.ctx.close()
        print("--- 3. avec un favicon.ico a cote : la page l'adopte")
        for url, viewer in PAGES:
            journal.clear()
            o = await Onglet(br).ouvrir(base2 + url, locale="fr-FR", viewer=viewer)
            await asyncio.sleep(1.5)
            r = await o.ev(LIEN)
            rapport(r["href"].endswith("/favicon.ico") and r["type"] == "image/x-icon" and r["w"] > 0, f"{url} : l'icone est le fichier favicon.ico (largeur {r['w']})", r)
            rapport(any(c[0] == "/favicon.ico" and " 200 " in c[1] for c in journal), f"{url} : favicon.ico servi (200)", journal[:4])
            rapport(not o.errs, f"{url} : aucune erreur de page", o.errs)
            await o.ctx.close()
        await br.close()
    srv1.shutdown(); srv2.shutdown()


asyncio.run(main())
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
