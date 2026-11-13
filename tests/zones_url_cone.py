#!/usr/bin/env python3
"""Test des zones url (1.10.16) : declenchement en marchant dedans (enter, both), ouverture d'un lien hop:// dans le meme onglet,
cle facultative `cone` par zone (vrai : cone meme pour une zone « au clic » ; faux : pas de cone pour un portail ; absente : comme avant).

Prerequis : pip install playwright && playwright install chromium ; python build.py avant.
Variable facultative : THREE_DIR (paquet npm three, hors ligne), CHROMIUM.
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, json, os, pathlib, struct, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_zonecone_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0
HOP = "hop://exemple.invalid:9000/Atoll/128/128/25"


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def sol_glb(path):
    pos = struct.pack("<12f", -20, 0, -20, 20, 0, -20, 20, 0, 20, -20, 0, 20)
    blob = pos + struct.pack("<6H", 0, 2, 1, 0, 3, 2) + b"\0\0"
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 48}, {"buffer": 0, "byteOffset": 48, "byteLength": 12}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [-20, 0, -20], "max": [20, 0, 20]},
                       {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "sol"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * ((4 - len(js) % 4) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob))
                     + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def page():
    # le centre du sol est releve a 15 m par le cadrage : zones posees a cette hauteur
    Z = lambda i, t, x, z, **k: dict({"id": i, "type": t, "label": "Zone " + i, "x": x, "y": 15, "z": z, "radius": 2}, **k)
    zones = [Z("hop", "url", 0, 0, target=HOP, trigger="both", shape="ring"),
             Z("lien", "url", 10, 10, target="https://exemple.invalid/", trigger="click"),
             Z("lienc", "url", -10, 10, target="https://exemple.invalid/", trigger="click", cone=True),
             Z("portnc", "portal", 10, -10, trigger="enter", cone=False),
             Z("portail", "portal", -10, -10, trigger="enter"),
             Z("cmd", "ha", 15, 0, target="http://exemple.invalid/x", trigger="enter")]
    (tmp / "z.json").write_text(json.dumps(zones), encoding="utf-8")
    out = tmp / "p.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out), "--zones", str(tmp / "z.json"), "--no-sea", *vend],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    out.write_text(out.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    return out


async def main():
    from playwright.async_api import async_playwright
    sol_glb(tmp / "sol.glb")
    out = page()
    async with async_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
        br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
        pg = await br.new_page(locale="fr-FR"); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(out.as_uri())
        await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
        await pg.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
        await pg.evaluate("(window.open = (...a) => { (window.__op = window.__op || []).push(a); return null; }, 0)")   # le « , 0 » : sinon Playwright appelle la fonction obtenue
        zs = {z["id"]: z for z in await pg.evaluate("window.__v.getZones()")}
        rapport(zs["hop"]["trigger"] == "both" and zs["lien"]["trigger"] == "click", "zone url : le declenchement both est conserve", (zs["hop"]["trigger"], zs["lien"]["trigger"]))
        rapport(zs["cmd"]["trigger"] == "click", "zone ha : toujours au clic", zs["cmd"]["trigger"])
        rapport(zs["lienc"].get("cone") is True and zs["portnc"].get("cone") is False and "cone" not in zs["hop"] and "cone" not in zs["portail"],
                "cle cone : conservee quand vraie ou fausse, absente sinon", {k: v.get("cone", "-") for k, v in zs.items()})
        ids = sorted(c["id"] for c in await pg.evaluate("window.__v.getCones()"))
        rapport(ids == ["hop", "lienc", "portail"], "cones : url both, url au clic avec cone vrai, portail ; pas pour url au clic, ni portail avec cone faux, ni ha",
                ids)
        # marcher dans la zone hop (both) : le lien s'ouvre dans le meme onglet
        await pg.evaluate("window.__v.walkStart({ pos: [0, 15, 5], yaw: 0 })"); await pg.wait_for_timeout(400)
        if await pg.evaluate("document.body.classList.contains('padOn')"):
            await pg.keyboard.press("KeyK"); await pg.wait_for_timeout(200)
        await pg.keyboard.down("ArrowUp")
        try:
            await pg.wait_for_function("(window.__op || []).length > 0", timeout=15000)
        except Exception:
            pass
        await pg.keyboard.up("ArrowUp")
        op = json.loads(await pg.evaluate("JSON.stringify(window.__op || [])"))
        rapport(len(op) == 1 and op[0][0] == HOP and op[0][1] == "_self", "marcher dans une zone url both : le hop:// s'ouvre dans le meme onglet", op)
        # zone url au clic : E l'ouvre, mais la traverser ne l'ouvre pas
        await pg.evaluate("window.__op = []; window.__v.teleportTo([10, 15, 12], 0)"); await pg.wait_for_timeout(500)
        await pg.keyboard.press("KeyE"); await pg.wait_for_timeout(300)
        op = json.loads(await pg.evaluate("JSON.stringify(window.__op)"))
        rapport(len(op) == 1 and op[0][0].startswith("https://exemple.invalid/"), "zone url au clic : E l'ouvre (nouvel onglet)", op)
        await pg.evaluate("window.__op = []; window.__v.teleportTo([10, 15, 14], 0)"); await pg.wait_for_timeout(300)
        await pg.keyboard.down("ArrowUp"); await pg.wait_for_timeout(3500); await pg.keyboard.up("ArrowUp")
        w = await pg.evaluate("window.__v.getWalk().pos")
        rapport(w[2] < 8 and not await pg.evaluate("window.__op.length"), "zone url au clic : la traverser ne l'ouvre pas", (w, await pg.evaluate("window.__op")))
        rapport(not errs, "aucune erreur JavaScript", errs)
        await br.close()
    print("\nRESULTAT : " + ("tout est passe" if not echecs else f"ECHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
