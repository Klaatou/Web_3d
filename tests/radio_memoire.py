#!/usr/bin/env python3
"""Test de la memoire du flux choisi d'une radio (1.13.3) : le flux choisi dans la liste est retenu par zone (cle glb2html_radio_<region>), retrouve au retour dans la zone et
apres un rechargement de la page, repris au premier flux si l'adresse retenue n'existe plus, sans erreur si la valeur retenue est abimee ; une radio a un seul flux n'est pas retenue ;
la bulle de la radio donne le flux retenu. Meme famille que zone_cast et bulle_radio.

Prerequis : pip install playwright && playwright install chromium ; python build.py avant.
Variable facultative : THREE_DIR (paquet npm three, hors ligne), CHROMIUM.
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, functools, http.server, json, math, os, pathlib, struct, subprocess, sys, tempfile, threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_cast_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def sol_glb(path):
    pos = struct.pack("<12f", -60, 0, -60, 60, 0, -60, 60, 0, 60, -60, 0, 60)
    blob = pos + struct.pack("<6H", 0, 2, 1, 0, 3, 2) + b"\0\0"
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-60, 0, -60], "max": [60, 0, 60]},
                       {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * ((4 - len(js) % 4) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob))
                     + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def wav(path, secondes=40):
    n = 8000 * secondes
    data = bytes(int(128 + 100 * math.sin(2 * math.pi * 440 * i / 8000)) for i in range(n))
    path.write_bytes(b"RIFF" + struct.pack("<I", 36 + n) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 8000, 8000, 1, 8) + b"data" + struct.pack("<I", n) + data)


PORT = [0]


def page():
    u = lambda n: f"http://127.0.0.1:{PORT[0]}/{n}.wav"
    # le centre du sol est releve a 15 m par le cadrage : zones posees a cette hauteur
    Z = lambda i, x, z, st: {"id": i, "type": "cast", "label": "Zone " + i, "x": x, "y": 15, "z": z, "radius": 10, "cone": True, "streams": st}
    zones = [Z("salle", 0, 0, [["Jazz", u("a")], ["Rock", u("b")], ["", u("c")]]),
             Z("bar", 30, 0, [["Classique", u("d")]]),
             Z("nu", 30, 25, [["", u("e")]])]
    (tmp / "z.json").write_text(json.dumps(zones), encoding="utf-8")
    out = tmp / "p.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--zones", str(tmp / "z.json"), "--no-sea", *vend],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    t = out.read_text(encoding="utf-8")
    for a, b in (("const viewer = createViewer(", "const viewer = window.__v = createViewer("), ("const RADIO = (() => {", "const RADIO = window.__r = (() => {")):
        if a not in t:
            sys.exit(f"[ECHEC] marqueur absent de la page : {a}")
        t = t.replace(a, b, 1)
    out.write_text(t, encoding="utf-8")
    return out


async def bulle(pg, zid):
    """texte de la bulle quand la souris est sur le cone de la zone (None si pas de bulle)"""
    c = [c for c in await pg.evaluate("window.__v.getCones()") if c["id"] == zid][0]
    await pg.mouse.move(c["sx"], c["sy"]); await pg.wait_for_timeout(150)
    await pg.mouse.move(c["sx"] + 1, c["sy"]); await pg.wait_for_timeout(150)
    return await pg.evaluate("(() => { const e = document.getElementById('zoneTip'); return e && !e.hidden ? e.innerText : null; })()")


async def entrer(pg, pos=(0, 15, 8)):
    await pg.evaluate("window.__v.walkStart({ pos: [%s], yaw: 0 })" % ", ".join(map(str, pos)))
    await pg.wait_for_timeout(500)


async def choix(pg):
    return await pg.evaluate("document.getElementById('radioSel').value")


async def memoire(pg):
    return await pg.evaluate("(() => { const k = Object.keys(localStorage).filter(k => k.startsWith('glb2html_radio_')); return k.length ? [k[0], localStorage.getItem(k[0])] : null; })()")


async def recharger(pg, out):
    await pg.goto(out.as_uri())
    await pg.reload()
    await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
    await pg.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")


async def main():
    from playwright.async_api import async_playwright
    sol_glb(tmp / "sol.glb")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    PORT[0] = srv.server_address[1]
    out = page()
    ub = f"http://127.0.0.1:{PORT[0]}/b.wav"
    async with async_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
        br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
        pg = await br.new_page(locale="fr-FR", viewport={"width": 1000, "height": 700}); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(out.as_uri())
        await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
        await pg.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
        await entrer(pg)
        rapport(await choix(pg) == "0" and await memoire(pg) is None, "premiere visite : premier flux, rien de retenu", (await choix(pg), await memoire(pg)))
        await pg.evaluate("(() => { const s = document.getElementById('radioSel'); s.value = '1'; s.dispatchEvent(new Event('change')); })()"); await pg.wait_for_timeout(300)
        m = await memoire(pg)
        rapport(m is not None and json.loads(m[1]) == {"salle": ub}, "choisir le 2e flux le retient (zone -> adresse du flux)", m)
        # sortie de la zone puis retour
        await pg.evaluate("window.__v.teleportTo([0, 15, 40], 0)"); await pg.wait_for_timeout(600)
        await pg.evaluate("window.__v.teleportTo([0, 15, 8], 0)"); await pg.wait_for_timeout(600)
        rapport(await choix(pg) == "1", "sortie de la zone puis retour : le 2e flux est retrouve (avant 1.13.3 : retour au premier)", await choix(pg))
        # une radio a un seul flux n'est pas retenue
        await pg.evaluate("window.__v.teleportTo([30, 15, 1], 0)"); await pg.wait_for_timeout(600)
        await pg.evaluate("window.__r.setIdx(0)"); await pg.wait_for_timeout(200)
        m = await memoire(pg)
        rapport(m is not None and list(json.loads(m[1])) == ["salle"], "radio a un seul flux : rien de retenu", m)
        # rechargement de la page
        await recharger(pg, out)
        await entrer(pg)
        rapport(await choix(pg) == "1", "apres un rechargement de la page : le 2e flux est retrouve", await choix(pg))
        await pg.evaluate("window.__v.toggleWalk()"); await pg.wait_for_timeout(400)
        c = [c for c in await pg.evaluate("window.__v.getCones()") if c["id"] == "salle"][0]
        await pg.mouse.move(c["sx"], c["sy"]); await pg.wait_for_timeout(150); await pg.mouse.move(c["sx"] + 1, c["sy"]); await pg.wait_for_timeout(150)
        t = await pg.evaluate("(() => { const e = document.getElementById('zoneTip'); return e && !e.hidden ? e.innerText : null; })()")
        rapport(t is not None and "Rock" in t and "Jazz" not in t, "bulle de la radio (vue globale) : le flux retenu, « Rock »", t)
        # adresse retenue disparue : premier flux
        k = (await memoire(pg))[0]
        await pg.evaluate("([k]) => localStorage.setItem(k, JSON.stringify({ salle: 'http://exemple.invalid/disparu.wav' }))", [k])
        await recharger(pg, out); await entrer(pg)
        rapport(await choix(pg) == "0", "adresse retenue qui n'existe plus : retour au premier flux", await choix(pg))
        # valeur abimee
        for brut in ("pas du json", "[1, 2]", '{"salle": 5}', "null"):
            await pg.evaluate("([k, v]) => localStorage.setItem(k, v)", [k, brut])
            await recharger(pg, out); await entrer(pg)
            rapport(await choix(pg) == "0", "valeur retenue abimee (" + brut + ") : premier flux, la page marche", await choix(pg))
        rapport(not errs, "aucune erreur JavaScript", errs)
        await br.close()
    print()
    print("RESULTAT : " + ("tout est passe" if not echecs else f"{echecs} echec(s)"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
