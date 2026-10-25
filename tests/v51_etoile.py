#!/usr/bin/env python3
"""Tests v51 (suite) : adresse de présence « même nom que la page » (ws://*:PORT).

Vrai presence_server.py et Chromium. Une région dont presenceUrl vaut ws://*:PORT : connectée en l'ouvrant par 127.0.0.1 puis par
localhost (la page vise chaque fois le nom par lequel elle a été ouverte) ; la fenêtre Carte et carte.html reçoivent leurs compteurs
pour une fiche en ws://*:PORT ; le journal des visites joint le serveur (clé refusée) ;
le message d'erreur montre l'adresse résolue ; le viewer ouvert depuis le disque vise 127.0.0.1 ; ws://0.0.0.0 toujours corrigé.

Non reproduit ici : le blocage par Edge d'une page à adresse publique qui vise une adresse du réseau local (cause des connexions vides
constatées par JJ) ; Chromium 141, même avec les contrôles de réseau local activés, ne le montre pas.

Prérequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v51_etoile.py
"""
import asyncio, json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

port = port_libre()
d = tmp / "srv"; d.mkdir()
srv = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--lang", "fr", "--host", "127.0.0.1", "--port", str(port), "--identities", "",
                        "--visits", str(d / "visits.jsonl"), "--visits-keys", str(d / "keys.json"), "--log", str(d / "presence.log")],
                       stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
attendre_port(port, srv, "presence_server")
site = tmp / "site"; site.mkdir()
sol_glb(site / "sol.glb")
STAR = f"ws://*:{port}"
html(site / "sol.glb", "-o", site / "E.html", "--shared-shell", "--no-sea", "--target", "0,0,0", "--presence-url", STAR, "--room", "etoile")
cfg = json.loads((site / "E.config.json").read_text(encoding="utf-8"))
rapport(cfg.get("presenceUrl") == STAR, "glb2html garde ws://*:PORT tel quel dans la config", cfg.get("presenceUrl"))
cfg["map"] = [{"name": "Etoile", "url": "index.html?region=E", "x": 0, "y": 0, "room": "etoile", "presence": STAR}]
(site / "E.config.json").write_text(json.dumps(cfg), encoding="utf-8")
html(site / "sol.glb", "-o", site / "Z.html", "--shared-shell", "--no-sea", "--target", "0,0,0", "--presence-url", f"ws://0.0.0.0:{port}", "--room", "zero")
shutil.copy(DIST / "carte.html", site / "carte.html")
(site / "regions.json").write_text(json.dumps([{"name": "Etoile", "url": "index.html?region=E", "x": 0, "y": 0, "room": "etoile", "presence": STAR}]), encoding="utf-8")
http, hp = serveur(site)


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        for hote in ("127.0.0.1", "localhost"):
            print(f"--- page ouverte par {hote}")
            o = await Onglet(br).ouvrir(f"http://{hote}:{hp}/index.html?region=E#name=Zoe")
            await o.attendre("window.__viewer.getPresence().state === 'online'", 20)
            rapport(True, f"{hote} : présence connectée avec ws://*:PORT")
            await o.ev("document.getElementById('mapBtn').click()")
            await o.attendre("document.getElementById('mapGrid').textContent.includes('visiteur')", 15)
            rapport(True, f"{hote} : fenêtre Carte, compteur reçu", await o.txt("mapGrid"))
            await o.ctx.close()
        print("--- journal des visites")
        o = await Onglet(br).ouvrir(f"http://localhost:{hp}/index.html?region=E#visits")
        await o.ev("document.getElementById('visitsKey').value = 'FAUX'; document.getElementById('visitsGo').click()")
        await o.attendre("document.getElementById('visitsStatus').textContent.includes('refusée')", 15)
        rapport(True, "journal des visites : serveur joint (clé refusée)")
        await o.ctx.close()
        print("--- carte.html")
        o = await Onglet(br).ouvrir(f"http://localhost:{hp}/carte.html", viewer=False)
        await o.attendre("document.getElementById('grid').textContent.includes('visiteur')", 20)
        rapport(True, "carte.html : compteur reçu pour une fiche en ws://*:PORT", await o.txt("grid"))
        await o.ctx.close()
        print("--- 0.0.0.0 et message d'erreur")
        o = await Onglet(br).ouvrir(f"http://127.0.0.1:{hp}/index.html?region=Z#name=Zoe")
        await o.attendre("window.__viewer.getPresence().state === 'online'", 20)
        rapport(True, "ws://0.0.0.0:PORT toujours corrigé en 127.0.0.1")
        await o.ctx.close()
        mort = port_libre()
        cfg2 = json.loads((site / "E.config.json").read_text(encoding="utf-8")); cfg2["presenceUrl"] = f"ws://*:{mort}"; cfg2["map"] = []
        (site / "M.config.json").write_text(json.dumps(cfg2), encoding="utf-8")
        shutil.copy(site / "E.glb", site / "M.glb") if (site / "E.glb").exists() else None
        o = await Onglet(br).ouvrir(f"http://localhost:{hp}/index.html?region=M#name=Zoe")
        await o.attendre("document.getElementById('presenceStatus').textContent.includes('jamais établie')", 25)
        s = await o.txt("presenceStatus")
        rapport(f"ws://localhost:{mort}" in s and "*" not in s, "message d'erreur : adresse résolue (ws://localhost:PORT), pas l'étoile", s)
        await o.ctx.close()
        print("--- viewer ouvert depuis le disque")
        o = await Onglet(br).ouvrir((DIST / "glb-viewer.html").as_uri(), init=None, viewer=False)
        await o.attendre("!!document.getElementById('presInfo')", 20)
        await o.ev(f"""(() => {{ const i = [...document.querySelectorAll('input[type=text]')].find(x => x.placeholder === 'ws://127.0.0.1:8765'); i.value = '{STAR}'; i.onchange(); }})()""")
        await o.attendre("window.__viewer.getPresence().state === 'online'", 20)
        rapport(True, "viewer (file://) : ws://*:PORT vise 127.0.0.1")
        await o.ctx.close()
        await br.close()


try:
    asyncio.run(main())
finally:
    http.kill()
    srv.kill()
out = srv.communicate()[0]
log = (d / "presence.log").read_text(encoding="utf-8")
rapport("salon=etoile" in log and "salon=zero" in log, "journal : connexions des salons etoile et zero", log[-600:])
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
