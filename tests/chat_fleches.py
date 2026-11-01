#!/usr/bin/env python3
"""Chat : les fleches restent dans le texte tant que la saisie est ouverte (Chromium sans tete + vrai serveur de presence).

Avant la 1.1.9, les fleches deplacaient l'avatar meme pendant la saisie, ce qui empechait de corriger son texte. Maintenant : saisie ouverte (Entree),
les fleches deplacent le curseur dans le texte et l'avatar reste immobile ; Echap ferme la saisie et rend les fleches a la promenade ; l'aide le dit.

Prerequis : python build.py ; pip install playwright websockets. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/chat_fleches.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_chatf_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def sol_glb(path):
    v = [(-20, 0, -20), (20, 0, -20), (20, 0, 20), (-20, 0, 20)]
    pos = b"".join(struct.pack("<3f", *p) for p in v); idx = struct.pack("<6H", 0, 2, 1, 0, 3, 2); blob = pos + idx
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pos)}, {"buffer": 0, "byteOffset": len(pos), "byteLength": len(idx)}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-20, 0, -20], "max": [20, 0, 20]}, {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}], "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * (-len(js) % 4); blob += bytes(-len(blob) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def port_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); return s.getsockname()[1]


async def main():
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    sol_glb(tmp / "sol.glb")
    pport, wport = port_libre(), port_libre()
    if subprocess.run([sys.executable, "-c", "import websockets"], capture_output=True).returncode:
        sys.exit("[ECHEC] la bibliotheque « websockets » n'est pas installee : le serveur de presence ne peut pas demarrer (pip install websockets), donc le chat n'existe pas.")
    pres = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--host", "127.0.0.1", "--port", str(pport),
                             "--identities", str(tmp / "id.json"), "--bans", str(tmp / "bans.json")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(site / "page.html"), "--no-sea", "--presence-url", f"ws://127.0.0.1:{pport}", "--room", "t", "--chat", *vend], capture_output=True, text=True)
    if r.returncode:
        pres.kill(); sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    for _ in range(60):   # le serveur de presence doit repondre avant d'ouvrir la page
        try:
            socket.create_connection(("127.0.0.1", pport), timeout=0.3).close(); break
        except OSError:
            time.sleep(0.2)
    else:
        pres.kill(); sys.exit("[ECHEC] le serveur de presence ne repond pas sur le port " + str(pport))
    page = site / "page.html"
    page.write_text(page.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    web = subprocess.Popen([sys.executable, "-m", "http.server", str(wport), "--bind", "127.0.0.1"], cwd=site, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            pg = await br.new_page(locale="fr-FR", viewport={"width": 1200, "height": 700}); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{wport}/page.html")
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=90000); await pg.wait_for_timeout(2500)
            await pg.keyboard.press("f"); await pg.wait_for_function("window.__v.walking", timeout=10000)
            try:
                await pg.wait_for_function("document.getElementById('chatHelp') && /Entr/.test(document.getElementById('chatHelp').textContent)", timeout=20000)
            except Exception:
                pass
            ev = lambda s: pg.evaluate(s)
            await pg.keyboard.press("Enter"); await pg.wait_for_timeout(500)
            rapport(await ev("document.activeElement && document.activeElement.id") == "chatInput", "Entree ouvre la saisie du chat (le champ a le focus)")
            await pg.keyboard.type("abc")
            w0 = await ev("(() => { const w = window.__v.getWalk(); return [w.yaw, w.pos.slice()]; })()")
            await pg.keyboard.down("ArrowLeft")
            m = await ev("(() => { const v = window.__v; v.walkTick(0.5); const w = v.getWalk(); return [w.yaw, w.pos.slice()]; })()")
            await pg.keyboard.up("ArrowLeft")
            caret = await ev("document.activeElement.selectionStart")
            rapport(abs(m[0] - w0[0]) < 1e-6 and caret == 2, "saisie ouverte : la fleche gauche deplace le curseur dans le texte, l'avatar ne tourne pas", (w0[0], m[0], caret))
            await pg.keyboard.down("ArrowUp")
            m = await ev("(() => { const v = window.__v; v.walkTick(0.5); const w = v.getWalk(); return w.pos.slice(); })()")
            await pg.keyboard.up("ArrowUp")
            rapport(max(abs(a - b) for a, b in zip(m, w0[1])) < 1e-9, "saisie ouverte : la fleche haut n'avance pas l'avatar", (w0[1], m))
            await pg.keyboard.press("Escape"); await pg.wait_for_timeout(400)
            rapport(await ev("document.getElementById('chatInput').hidden"), "Echap ferme la saisie")
            await pg.keyboard.down("ArrowUp")
            m = await ev("(() => { const v = window.__v; const a = v.getWalk().pos.slice(); v.walkTick(0.5); return [a, v.getWalk().pos.slice()]; })()")
            await pg.keyboard.up("ArrowUp")
            rapport(max(abs(a - b) for a, b in zip(m[0], m[1])) > 0.5, "apres Echap : la fleche haut avance de nouveau l'avatar", m)
            aide = await ev("document.getElementById('walkHint').textContent")
            rapport("flèches : dans le texte" in aide, "l'aide du chat dit que les fleches restent dans le texte", aide[-160:])
            rapport(not errs, "aucune erreur JavaScript", errs)
            await br.close()
    finally:
        pres.kill(); web.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
