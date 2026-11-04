#!/usr/bin/env python3
"""Chat : une sélection de texte dans le journal survit (Chromium sans tête + vrai serveur de présence).

Avant la 1.5.2, la page reconstruisait tout le journal du chat chaque seconde (setInterval(render, 1000)) : une sélection de texte
(triple clic, glisser) disparaissait avant qu'on puisse la copier. Vérifie : un message sélectionné reste sélectionné après 3,5 s ;
il le reste quand un nouveau message arrive ; le journal contient les messages dans l'ordre, sans doublon ; aucune erreur JavaScript.
Contre-épreuve : sur le code de la 1.5.1, les deux premiers contrôles échouent.

Prérequis : python build.py ; pip install playwright websockets. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/chat_selection.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, socket, struct, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_sel_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0
print("chat_selection.py version 1 (04/11/2026)")


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
    import websockets.asyncio.client
    from playwright.async_api import async_playwright
    site = tmp / "site"; site.mkdir()
    sol_glb(tmp / "sol.glb")
    pport, wport = port_libre(), port_libre()
    pres = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--host", "127.0.0.1", "--port", str(pport),
                             "--identities", str(tmp / "id.json"), "--bans", str(tmp / "bans.json"),
                             "--chat-gap", "0.05", "--chat-burst", "100"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(site / "page.html"), "--no-sea",
                        "--presence-url", f"ws://127.0.0.1:{pport}", "--room", "t", "--chat", *vend], capture_output=True, text=True)
    if r.returncode:
        pres.kill(); sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    for _ in range(60):
        try:
            socket.create_connection(("127.0.0.1", pport), timeout=0.3).close(); break
        except OSError:
            time.sleep(0.2)
    web = subprocess.Popen([sys.executable, "-m", "http.server", str(wport), "--bind", "127.0.0.1"], cwd=site, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    bob = None
    try:
        bob = await websockets.asyncio.client.connect(f"ws://127.0.0.1:{pport}")
        await bob.send(json.dumps({"t": "hello", "room": "t", "uid": os.urandom(12).hex(), "spectator": False, "name": "Bob"})); await bob.recv()

        async def dire(texte):
            await asyncio.sleep(0.4)      # comme chat_bip.py : jamais deux messages a moins de 0,1 s
            await bob.send(json.dumps({"t": "chat", "text": texte}))
            fin = time.time() + 5
            while time.time() < fin:
                try:
                    m = json.loads(await asyncio.wait_for(bob.recv(), 1))
                except asyncio.TimeoutError:
                    continue
                if m.get("t") == "chat" and m.get("text") == texte:
                    return True
            rapport(False, f"le serveur a accepte « {texte} »", "message jete")
            return False

        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            ctx = await br.new_context(locale="fr-FR", viewport={"width": 1100, "height": 650})
            pg = await ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{wport}/page.html#name=Zoe")
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=90000); await pg.wait_for_timeout(2000)
            await pg.keyboard.press("f"); await pg.wait_for_timeout(1500)
            await pg.wait_for_function("document.getElementById('chatHelp') && document.getElementById('chatHelp').textContent.length > 0", timeout=20000)
            await dire("premier message de Bob"); await dire("deuxieme message de Bob")
            await pg.wait_for_function("document.querySelectorAll('#chatLog div').length >= 2", timeout=10000)
            lignes = await pg.evaluate("[...document.querySelectorAll('#chatLog div')].map(d => d.textContent)")
            rapport(lignes == ["Bob : premier message de Bob", "Bob : deuxieme message de Bob"], "le journal contient les deux messages, dans l'ordre", lignes)
            # sélection à la souris : triple clic sur le premier message
            sel0 = ""
            for _ in range(6):      # sur l'ancien code la reconstruction du journal peut effacer la sélection avant la lecture : on recommence le clic
                await pg.locator("#chatLog div").nth(0).click(click_count=3)
                sel0 = (await pg.evaluate("String(getSelection())")).strip()
                if "premier message de Bob" in sel0:
                    break
            rapport("premier message de Bob" in sel0, "triple clic : le premier message est sélectionné", sel0)
            await pg.wait_for_timeout(3500)
            sel1 = (await pg.evaluate("String(getSelection())")).strip()
            rapport(sel1 == sel0, "3,5 s plus tard : la sélection est intacte", f"avant={sel0!r} apres={sel1!r}")
            await dire("troisieme message de Bob"); await pg.wait_for_function("document.querySelectorAll('#chatLog div').length >= 3", timeout=10000)
            await pg.wait_for_timeout(1500)
            sel2 = (await pg.evaluate("String(getSelection())")).strip()
            rapport(sel2 == sel0, "un nouveau message arrive : la sélection est intacte", f"apres={sel2!r}")
            lignes = await pg.evaluate("[...document.querySelectorAll('#chatLog div')].map(d => d.textContent)")
            rapport(lignes == ["Bob : premier message de Bob", "Bob : deuxieme message de Bob", "Bob : troisieme message de Bob"], "trois messages, dans l'ordre, sans doublon", lignes)
            # sens opposé : la liste affichée change autrement qu'en ajoutant au bout (le journal ferme n'affiche que les 6 derniers) -> reconstruction
            for k in range(4, 9):
                await dire(f"message {k} de Bob")
            await pg.wait_for_timeout(2500)
            lignes = await pg.evaluate("[...document.querySelectorAll('#chatLog div')].map(d => d.textContent)")
            attendu = ["Bob : troisieme message de Bob"] + [f"Bob : message {k} de Bob" for k in range(4, 9)]
            rapport(lignes == attendu, "plus de 6 messages : les 6 derniers, dans l'ordre, sans doublon (reconstruction)", lignes)
            rapport(not errs, "aucune erreur JavaScript", errs)
            await ctx.close(); await br.close()
    finally:
        if bob:
            try:
                await bob.close()
            except Exception:
                pass
        pres.kill(); web.kill()
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
