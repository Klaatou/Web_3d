#!/usr/bin/env python3
"""Tests 1.13.21 : micro coupe pendant un DJ en direct, cote page (vrai presence_server.py, vraie page, Chromium avec micro simule, faux Icecast).

Une region avec une zone radio (cast) a deux flux : la base et le montage direct (celui de --live). Le faux Icecast annonce ou non une source sur le
montage direct. Verifie :
1.  sans DJ : le micro s'ouvre (touche X), meme dans la zone radio ;
2.  le DJ arrive : le visiteur DANS la zone radio (a portee, sans ecouter la radio) a le micro coupe (voiceInfo().muted et dj vrais, X sans effet,
    message « DJ en direct ») ; le visiteur hors de la zone garde son micro ;
3.  sortir de la zone rend le micro, y rentrer le recoupe ; le DJ part : micro rendu ;
4.  aucune erreur de page.
Non teste ici : Windows, Edge, vrai Icecast, tactile. Lancer : python tests/live_page.py (apres python build.py)
"""
import asyncio, http.server, json, os, sys, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

V = "window.__viewer."
ETAT = {"direct": False}


class Faux(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        src = [{"listenurl": "http://interne:8000/autodj"}] + ([{"listenurl": "http://interne:8000/live"}] if ETAT["direct"] else [])
        corps = json.dumps({"icestats": {"source": src}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)


async def main():
    from playwright.async_api import async_playwright
    ice = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Faux)
    threading.Thread(target=ice.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{ice.server_address[1]}"
    live = tmp / "live.json"
    live.write_text(json.dumps([base + "/live"]), encoding="utf-8")
    site = tmp / "site"; site.mkdir()
    sol_glb(site / "sol.glb", demi=150.0)
    (tmp / "z.json").write_text(json.dumps([
        {"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0.0},
        {"id": "radio", "type": "cast", "label": "Radio", "x": 0, "y": 15, "z": 0, "radius": 30, "streams": [["Base", base + "/autodj"], ["Direct", base + "/live"]]}]), encoding="utf-8")
    ps, port_v = lancer_presence("--live", str(live), "--live-every", "5")
    html(site / "sol.glb", "-o", site / "Live.html", "--shared-shell", "--zones", tmp / "z.json", "--no-sea", "--target", "0,0,0", "--presence-url", f"ws://127.0.0.1:{port_v}", "--room", "dj", "--title", "Ile Test")
    srv, port = serveur(site)
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream", "--autoplay-policy=no-user-gesture-required"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        try:
            ctxa = await br.new_context(viewport={"width": 1000, "height": 700}, permissions=["microphone"])
            ctxb = await br.new_context(viewport={"width": 1000, "height": 700}, permissions=["microphone"])
            url = f"http://127.0.0.1:{port}/index.html?region=Live#spawn=default"
            a = await Onglet(br).ouvrir(url, init=STUB + "try { localStorage.setItem('glb2html_name', 'Ana'); } catch (e) {}", ctx=ctxa)
            b = await Onglet(br).ouvrir(url, init=STUB + "try { localStorage.setItem('glb2html_name', 'Ben'); } catch (e) {}", ctx=ctxb)
            for o in (a, b):
                await o.attendre(V + "walking && " + V + "getPresence().state === 'online'", 40)
            await b.ev("window.__viewer.teleportTo([100, 15, 0], 0)")      # Ben : loin de la zone radio (rayon 30 m)
            await a.pg.wait_for_timeout(2500)
            await a.ev("document.getElementById('voiceBtn').click()")
            ra = await a.ev(V + "voiceStart(true)"); rb = await b.ev(V + "voiceStart(true)")
            rapport(ra["ok"] and rb["ok"] and ra["mic"] and rb["mic"], "micro + ecoute demarrent (micro simule)", (ra, rb))
            info = lambda o: o.ev(V + "voiceInfo()")
            tip = lambda: a.ev("(document.querySelector('.vcTip') || {}).textContent || ''")

            print("--- sans DJ")
            await a.key("keydown", "KeyX"); await a.pg.wait_for_timeout(300)
            ia = await info(a)
            rapport(ia["dj"] is False and ia["muted"] is False and ia["talk"] is True, "sans DJ, dans la zone radio : touche X, micro ouvert", ia)
            await a.key("keyup", "KeyX"); await a.pg.wait_for_timeout(200)

            print("--- le DJ arrive")
            ETAT["direct"] = True
            await a.attendre(V + "voiceInfo().dj === true", 25)
            await a.key("keydown", "KeyX"); await a.pg.wait_for_timeout(300)
            ia, ib = await info(a), await info(b)
            rapport(ia["dj"] is True and ia["muted"] is True and not ia["speaking"], "DJ en direct : micro coupe chez A (dans la zone, sans ecouter la radio) ; X demande le micro mais il reste ferme", ia)
            rapport(await tip() in ("Micro coupé : DJ en direct.", "Microphone muted: live DJ."), "la fenetre Voix dit « DJ en direct » (et non « coupe par l'orateur »)", await tip())
            rapport(ib["dj"] is False and ib["muted"] is False, "B hors de la zone : micro libre", ib)
            await a.key("keyup", "KeyX")
            await b.key("keydown", "KeyX"); await b.pg.wait_for_timeout(300)
            rapport((await info(b))["talk"] is True, "B hors de la zone : touche X, micro ouvert", await info(b))
            await b.key("keyup", "KeyX")

            print("--- sortie, rentree, fin du direct")
            await a.ev("window.__viewer.teleportTo([100, 15, 0], 0)")
            await a.attendre(V + "voiceInfo().dj === false", 12)
            ia = await info(a)
            rapport(ia["muted"] is False, "A quitte la zone : micro rendu (le direct continue)", ia)
            await a.pg.wait_for_timeout(1700)
            await a.ev("window.__viewer.teleportTo([0, 15, 0], 0)")
            await a.attendre(V + "voiceInfo().dj === true", 12)
            ia = await info(a)
            rapport(ia["muted"] is True, "A rentre dans la zone pendant le direct : micro recoupe", ia)
            ETAT["direct"] = False
            await a.attendre(V + "voiceInfo().dj === false", 25)
            ia = await info(a)
            rapport(ia["muted"] is False, "le DJ part : micro rendu", ia)
            rapport(not (a.errs + b.errs), "aucune erreur de page", (a.errs + b.errs)[:5])
        finally:
            await br.close()
            srv.kill(); ps.kill(); ice.shutdown()


asyncio.run(main())
sys.exit(1 if h37.resultat() else 0)
