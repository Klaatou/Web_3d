#!/usr/bin/env python3
"""Test du titre du morceau des zones radio (1.10.34) : le serveur de presence lit le titre DANS le flux (en-tete Icy-MetaData: 1, bloc apres
icy-metaint octets) pour les seules adresses de --radios ; la page demande le titre en entrant dans la zone, l'affiche apres le nom de la zone,
le met a jour quand il change, et une adresse hors liste ne donne rien.

Un faux serveur Icecast local sert un WAV : avec Icy-MetaData: 1, des blocs de metadonnees sont intercales (titre modifiable pendant le test) ;
sans l'en-tete (la balise <audio> de la page), le WAV est servi tel quel.
Prerequis : pip install playwright websockets && playwright install chromium ; python build.py avant.
Variable facultative : THREE_DIR (paquet npm three, hors ligne), CHROMIUM.
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, math, os, pathlib, socket, struct, subprocess, sys, tempfile, threading, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_radiotitre_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0
TITRE = ["Artiste Un - Premier morceau"]
DEMANDES_META = []


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def port_libre():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def sol_glb(path):
    pos = struct.pack("<12f", -40, 0, -40, 40, 0, -40, 40, 0, 40, -40, 0, 40)
    blob = pos + struct.pack("<6H", 0, 2, 1, 0, 3, 2) + b"\0\0"
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-40, 0, -40], "max": [40, 0, 40]},
                       {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * ((4 - len(js) % 4) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob))
                     + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def wav(secondes=40):
    n = 8000 * secondes
    data = bytes(int(128 + 100 * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(n))
    return b"RIFF" + struct.pack("<I", 36 + n) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 8000, 8000, 1, 8) + b"data" + struct.pack("<I", n) + data


def faux_icecast(port, corps):
    """serveur HTTP minimal : /flux.wav ; avec Icy-MetaData: 1, icy-metaint 4000 et un bloc de metadonnees tous les 4000 octets"""
    srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); srv.bind(("127.0.0.1", port)); srv.listen(8)

    def client(c):
        try:
            c.settimeout(5)
            req = b""
            while b"\r\n\r\n" not in req:
                d = c.recv(4096)
                if not d:
                    return
                req += d
            head = req.decode("latin-1").lower()
            meta = "icy-metadata: 1" in head
            if meta:
                DEMANDES_META.append(time.time())
            if "/absent" in head.split("\r\n")[0]:
                c.sendall(b"HTTP/1.0 404 Not Found\r\nContent-Length: 0\r\n\r\n"); return
            h = b"HTTP/1.0 200 OK\r\nContent-Type: audio/wav\r\nicy-name: Test\r\n" + (b"icy-metaint: 4000\r\n" if meta else b"") + b"\r\n"
            c.sendall(h)
            if not meta:
                c.sendall(corps); return
            for i in range(0, len(corps), 4000):
                t = ("StreamTitle='%s';" % TITRE[0]).encode("utf-8")
                t += b"\0" * (-len(t) % 16)
                c.sendall(corps[i:i + 4000] + bytes([len(t) // 16]) + t)
        except OSError:
            pass
        finally:
            c.close()

    def boucle():
        while True:
            try:
                c, _ = srv.accept()
            except OSError:
                return
            threading.Thread(target=client, args=(c,), daemon=True).start()
    threading.Thread(target=boucle, daemon=True).start()
    return srv


async def main():
    from playwright.async_api import async_playwright
    if subprocess.run([sys.executable, "-c", "import websockets"], capture_output=True).returncode:
        sys.exit("[ECHEC] la bibliotheque « websockets » n'est pas installee (pip install websockets).")
    site = tmp / "site"; site.mkdir()
    sol_glb(tmp / "sol.glb")
    pport, wport, iport = port_libre(), port_libre(), port_libre()
    flux = f"http://127.0.0.1:{iport}/flux.wav"
    ice = faux_icecast(iport, wav())
    (tmp / "radios.json").write_text(json.dumps([flux]), encoding="utf-8")
    pres = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--host", "127.0.0.1", "--port", str(pport),
                             "--identities", str(tmp / "id.json"), "--bans", str(tmp / "bans.json"), "--radios", str(tmp / "radios.json"), "--radios-every", "5"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env={**os.environ, "PYTHONIOENCODING": "utf-8"})   # Windows : sinon la console du serveur sort en page de code locale et « demandé » ne se retrouve pas
    JOURNAL = []
    threading.Thread(target=lambda: [JOURNAL.append(l.decode("utf-8", "replace")) for l in pres.stdout], daemon=True).start()   # vide le tube (Windows : 4 Ko) et garde le journal
    Z = lambda i, x, z, **k: dict({"id": i, "type": "cast", "label": "Zone " + i, "x": x, "y": 15, "z": z, "radius": 6}, **k)
    zones = [Z("salle", 0, 0, target=flux), Z("inconnue", 20, 0, target=f"http://127.0.0.1:{iport}/autre.wav")]
    (tmp / "z.json").write_text(json.dumps(zones), encoding="utf-8")
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(site / "page.html"), "--no-sea", "--zones", str(tmp / "z.json"),
                        "--presence-url", f"ws://127.0.0.1:{pport}", "--room", "t", *vend], capture_output=True, text=True)
    if r.returncode:
        pres.kill(); sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    p = site / "page.html"
    p.write_text(p.read_text(encoding="utf-8").replace("const RADIO = (() => {", "const RADIO = window.__r = (() => {", 1).replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    for _ in range(60):
        try:
            socket.create_connection(("127.0.0.1", pport), timeout=0.3).close(); break
        except OSError:
            time.sleep(0.2)
    web = subprocess.Popen([sys.executable, "-m", "http.server", str(wport), "--bind", "127.0.0.1"], cwd=site, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    try:
        async with async_playwright() as pw:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await pw.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            pg = await br.new_page(locale="fr-FR"); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{wport}/page.html")
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
            await pg.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
            info = lambda: pg.evaluate("(() => { const e = document.getElementById('radioInfo'); return e.hidden ? '' : e.textContent; })()")
            await pg.evaluate("window.__v.walkStart({ pos: [0, 15, 20], yaw: 0 })"); await pg.wait_for_timeout(500)
            await pg.keyboard.press("ControlLeft")
            rapport(not DEMANDES_META, "avant l'entree dans la zone : le serveur n'a pas lu le flux", len(DEMANDES_META))
            await pg.evaluate("window.__v.teleportTo([0, 15, 1], 0)")
            try:
                await pg.wait_for_function("/Premier morceau/.test(document.getElementById('radioInfo').textContent)", timeout=20000)
            except Exception:
                pass
            t = await info()
            rapport("Zone salle" in t and "Artiste Un - Premier morceau" in t and "—" in t, "dans la zone : la ligne donne le nom de la zone puis le titre lu dans le flux", t)
            rapport(len(DEMANDES_META) >= 1, "le serveur a lu le flux avec Icy-MetaData: 1", len(DEMANDES_META))
            TITRE[0] = "Artiste Deux - Second morceau"
            try:
                await pg.wait_for_function("/Second morceau/.test(document.getElementById('radioInfo').textContent)", timeout=20000)
            except Exception:
                pass
            rapport("Second morceau" in await info(), "changement de titre : la ligne suit (relevé toutes les 5 s)", await info())
            # sortie : plus de lecture ; retour : titre de nouveau
            await pg.evaluate("window.__v.teleportTo([0, 15, 15], 0)"); await pg.wait_for_timeout(800)
            n = len(DEMANDES_META); await pg.wait_for_timeout(6500)
            rapport(len(DEMANDES_META) == n and await info() == "", "hors de la zone : le serveur cesse de lire le flux, ligne cachee", (n, len(DEMANDES_META), await info()))
            # adresse hors liste : le flux joue (c'est un vrai WAV), mais aucun titre
            await pg.evaluate("window.__v.teleportTo([20, 15, 1], 0)")
            try:
                await pg.wait_for_function("window.__r.playing()", timeout=15000)
            except Exception:
                pass
            await pg.wait_for_timeout(1500)
            t = await info()
            rapport("Zone inconnue" in t and "—" not in t and "morceau" not in t, "adresse hors de --radios : le flux joue, pas de titre", t)
            await pg.wait_for_timeout(500)
            j = "".join(JOURNAL)
            rapport("titre demandé pour http://127.0.0.1" in j and "Premier morceau" in j and "Second morceau" in j and "hors de --radios" in j,
                    "journal du serveur (1.10.35) : demande, titres lus, adresse hors liste", [l.strip()[:110] for l in JOURNAL if "radio" in l][:6])
            rapport(not errs, "aucune erreur JavaScript", errs)
            # 1.11.1 : le titre n'est demande que si le flux est reellement ecoute : radio decochee = aucune demande, donc aucune lecture du flux par le serveur
            await pg.evaluate("window.__v.teleportTo([0, 15, 15], 0)"); await pg.wait_for_timeout(1500)
            n = len(DEMANDES_META)
            pg2 = await br.new_page(locale="fr-FR"); errs2 = []
            pg2.on("pageerror", lambda e: errs2.append(str(e)))
            await pg2.add_init_script("try { localStorage.setItem('glb2html_visitor', JSON.stringify({ radio: false })); } catch (e) {}")
            await pg2.goto(f"http://127.0.0.1:{wport}/page.html")
            await pg2.wait_for_function("document.getElementById('msg') === null", timeout=60000)
            await pg2.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
            await pg2.evaluate("window.__v.walkStart({ pos: [0, 15, 20], yaw: 0 })"); await pg2.wait_for_timeout(500)
            await pg2.keyboard.press("ControlLeft")   # premiere action du visiteur : le navigateur autorise le son
            await pg2.evaluate("window.__v.teleportTo([0, 15, 1], 0)")
            await pg2.wait_for_timeout(7500)
            rapport(len(DEMANDES_META) == n, "radio decochee, dans la zone : aucune demande de titre, le serveur ne lit pas le flux", (n, len(DEMANDES_META)))
            await pg2.evaluate("document.getElementById('visRadio').click()")
            try:
                await pg2.wait_for_function("/Second morceau/.test(document.getElementById('radioInfo').textContent)", timeout=20000)
            except Exception:
                pass
            rapport(len(DEMANDES_META) > n and "Second morceau" in await pg2.evaluate("document.getElementById('radioInfo').textContent"), "radio recochee : la demande part, le serveur lit le flux, le titre s'affiche", (n, len(DEMANDES_META)))
            await pg2.evaluate("document.getElementById('visRadio').click()"); await pg2.wait_for_timeout(2500)   # la page espace ses demandes de 1,5 s : le retrait part a l'echeance
            n2 = len(DEMANDES_META); await pg2.wait_for_timeout(6500)
            rapport(len(DEMANDES_META) == n2, "radio decochee de nouveau : la demande est retiree, le serveur cesse de lire le flux", (n2, len(DEMANDES_META)))
            rapport(not errs2, "aucune erreur JavaScript (page radio decochee)", errs2)
            await br.close()
        # 1.10.35 : deconnexions simultanees de tout un salon (arret du serveur, coupure) : plus de KeyError dans le finally du handler
        import websockets.asyncio.client
        cls = []
        for i in range(6):
            c = await websockets.asyncio.client.connect(f"ws://127.0.0.1:{pport}"); cls.append(c)
            await c.send(json.dumps({"t": "hello", "room": "r2", "uid": os.urandom(12).hex(), "spectator": False, "name": f"V{i}"})); await c.recv()
        await asyncio.gather(*(c.close() for c in cls))
        await asyncio.sleep(1.5)
        j = "".join(JOURNAL)
        rapport("Traceback" not in j and "KeyError" not in j and pres.poll() is None, "six deconnexions en meme temps : pas de KeyError, serveur toujours la", [l.strip()[:100] for l in JOURNAL if "Error" in l][:3])
    finally:
        pres.terminate(); web.terminate(); ice.close()
    print("\nRESULTAT : " + ("tout est passe" if not echecs else f"ECHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
