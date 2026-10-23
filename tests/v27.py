#!/usr/bin/env python3
"""Tests v27 : pile des repères d'un avatar visiteur (nom, bulle de chat, losange).

Le serveur de présence est remplacé par un faux WebSocket injecté dans la page (aucun réseau, aucun serveur) :
il envoie « welcome » avec deux visiteurs (A écrit, B se tait), puis les messages « chat » demandés par le test.
Vérifie, de près et de loin, avec une bulle de 1 ligne et de 4 lignes :
  - le bas de la bulle est au-dessus du haut du nom ;
  - le bas du losange est au-dessus du haut de la bulle ;
  - sans bulle (visiteur B, ou A avant d'écrire), le losange est exactement à sa hauteur d'avant (ly + 0,2 k + 0,5 ks) ;
  - A retrouve cette hauteur quand sa bulle disparaît.

Prérequis : pip install playwright ; python build.py avant.
Variables facultatives : THREE_DIR (paquet npm three, hors ligne), CHROMIUM (chemin de l'exécutable).
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"   # outils Python en français (v36)
import asyncio, os, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST, DATA = ROOT / "dist", ROOT / "tests" / "data"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_v27_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)))


page = tmp / "p.html"
r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(DATA / "walk3.glb"), "-o", str(page), "--presence-url", "ws://127.0.0.1:9", "--chat", "--chat-fade", "0", "--room", "t", *vend], capture_output=True, text=True, cwd=tmp)
if r.returncode:
    sys.exit(f"[ECHEC] génération\n{r.stdout}{r.stderr}")

FAKE = """
window.__fakeWS = null;
window.WebSocket = class {
  constructor() { this.readyState = 0; window.__fakeWS = this; setTimeout(() => { this.readyState = 1; this.onopen && this.onopen(); this.push({ t: 'welcome', id: 'me', role: 'spectator', peers: [
    { id: 'A', name: 'Alice', color: 255, p: [0, 0, 0], yaw: 0 }, { id: 'B', name: 'Bob', color: 65280, p: [3, 0, 0], yaw: 0 }], history: [] }); }, 50); }
  push(m) { this.onmessage && this.onmessage({ data: JSON.stringify(m) }); }
  send() {} close() { this.readyState = 3; }
};
"""
LONG = " ".join(["bonjour"] * 80)


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        ctx = await br.new_context(locale="fr-FR", viewport={"width": 900, "height": 600})
        await ctx.add_init_script(FAKE)
        pg = await ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(page.as_uri())
        await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)

        async def peers(dist):
            # caméra à `dist` mètres de A (A est à l'origine, B à 3 m de lui)
            await pg.evaluate("d => { const v = window.__viewer; v.camera.position.set(d, 1.5, 0); }", dist)
            await pg.wait_for_timeout(1200)
            d = await pg.evaluate("window.__viewer.getPresence().peers")
            return {q["name"]: q for q in d}

        def attendu(dist):
            k, ks = max(1, dist / 28), max(1, dist / 45)
            return k, ks, 2.1 + 0.55 * (k - 1)

        async def sans_bulle(dist, qui, nom):
            q = (await peers(dist))[qui]
            k, ks, ly = attendu(q["stack"]["dist"])
            b = q["stack"]["beacon"]["y"]
            rapport(not q["bubble"] and abs(b - (ly + 0.2 * k + 0.5 * ks)) < 0.02, f"{nom} : sans bulle, losange à sa hauteur d'avant (ly + 0,2 k + 0,5 ks)", (b, ly + 0.2 * k + 0.5 * ks))

        await peers(8)
        for dist in (8, 120):
            await sans_bulle(dist, "Alice", f"distance {dist} m, Alice")
        for lignes, texte in ((1, "Bonjour"), (4, LONG)):
            await pg.evaluate("t => window.__fakeWS.push({ t: 'chat', id: 'A', name: 'Alice', text: t })", texte)
            for dist in (8, 120):
                st = (await peers(dist))["Alice"]["stack"]
                s = st["label"], st["bubble"], st["beacon"]
                ok = bool(s[1]) and s[1]["bottom"] >= s[0]["top"] - 1e-6 and s[2]["bottom"] >= s[1]["top"] + 1e-6
                rapport(ok, f"{lignes} ligne(s), distance {dist} m : nom < bulle < losange (bas du losange au-dessus du haut de la bulle)", st)
                rapport(ok and s[1]["top"] - s[1]["bottom"] > (0.25 if lignes == 1 else 0.8), f"{lignes} ligne(s), distance {dist} m : la hauteur de la bulle suit le nombre de lignes", s[1])
                await sans_bulle(dist, "Bob", f"distance {dist} m, Bob (autre visiteur sans bulle)")
        # la bulle disparaît : le losange retrouve sa hauteur d'avant
        await pg.evaluate("window.__viewer.getPresence(); window.__fakeWS.push({ t: 'leave', id: 'B' })")
        await pg.evaluate("""() => { const v = window.__viewer; v.setCfg && v.setCfg({ chatFade: 0.3 }); }""")
        await pg.evaluate("window.__fakeWS.push({ t: 'chat', id: 'A', name: 'Alice', text: 'court' })")
        await pg.wait_for_timeout(1800)
        await sans_bulle(8, "Alice", "bulle expirée, Alice")
        rapport(not errs, "aucune erreur JavaScript", errs)
        await br.close()


asyncio.run(main())
print("\nRÉSULTAT :", "ÉCHEC (%d)" % bad if bad else "tout est passé")
sys.exit(1 if bad else 0)
