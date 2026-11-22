#!/usr/bin/env python3
"""Nom de zone par langue et bulle d'un lien YouTube (1.13.5).

Verifie :
 - labels { fr, en } : la page affiche le nom dans sa langue (bulle, liste), sinon label, sinon id ; labels d'une radio de l'ancien format (liste de noms de flux) n'est pas pris pour un nom ;
 - linkTitle : la bulle d'un lien montre le titre de la page (ex. video YouTube) a la place de l'adresse ; sans titre, un lien YouTube montre « youtube.com », un autre lien son adresse ;
 - Python (zone_in, zone_out, clean_zones, clean_labs) et JavaScript (zoneIn, zoneOut, setZones) donnent les memes zones, aller-retour compris ;
 - glb2html.py --link-titles : ajoute linkTitle aux zones au lien YouTube (service oEmbed simule par WEB3D_OEMBED), garde FICHIER.bak, ne touche ni un titre deja ecrit ni un autre lien,
   laisse en l'etat une zone dont le titre est introuvable, puis dit « aucun titre a ajouter ».
Le vrai service oEmbed de YouTube n'est pas joint (pas de reseau d'essai).

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/zone_labels.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, functools, http.server, importlib.util, json, os, pathlib, struct, subprocess, sys, tempfile, threading, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_lab_"))
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


YT = "https://www.youtube.com/watch?v=abc123"
LAB = {"fr": "Vidéo YouTube", "en": "YouTube video"}
# unified format ; cone vrai : la bulle se montre quand la souris est sur le cone
ZONES = [
    {"id": "yt", "label": "Video", "labels": LAB, "x": 0, "y": 15, "z": 0, "link": YT, "linkTitle": "Mon titre de video", "cone": True},
    {"id": "ytnu", "label": "Video sans titre", "x": 30, "y": 15, "z": 0, "link": "https://youtu.be/xyz", "cone": True},
    {"id": "web", "x": 30, "y": 15, "z": 25, "link": "https://exemple.invalid/page", "labels": {"en": "Web page"}, "cone": True},
    {"id": "objet", "label": {"fr": "Nom objet", "en": "Object name"}, "x": 0, "y": 15, "z": -25, "link": "https://exemple.invalid/o", "cone": True},   # forme ecrite a la main : label = { fr, en }
    {"id": "sans", "label": "Sans langue", "x": 0, "y": 15, "z": 25, "link": "https://exemple.invalid/b", "labels": {"fr": "Seulement fr"}, "cone": True},
]


async def bulle(pg, zid):
    c = [c for c in await pg.evaluate("window.__v.getCones()") if c["id"] == zid]
    if not c:
        return None
    c = c[0]
    await pg.mouse.move(c["sx"], c["sy"]); await pg.wait_for_timeout(150)
    await pg.mouse.move(c["sx"] + 1, c["sy"]); await pg.wait_for_timeout(150)
    return await pg.evaluate("(() => { const e = document.getElementById('zoneTip'); return e && !e.hidden ? e.innerText : null; })()")


def charger_gen():
    sp = importlib.util.spec_from_file_location("g", DIST / "glb2html.py")
    g = importlib.util.module_from_spec(sp); sp.loader.exec_module(g)
    return g


class Oembed(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        u = (q.get("url") or [""])[0]
        if "abc123" in u:
            body = json.dumps({"title": "Titre réel\u0001 de la vidéo", "type": "video"}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        else:
            self.send_response(404); self.end_headers()

    def log_message(self, *a):
        pass


async def main():
    from playwright.async_api import async_playwright
    g = charger_gen()
    # ---- Python : clean_labs, zone_in / zone_out / clean_zones
    rapport(g.clean_labs({"fr": " A\x01B ", "en": "x" * 80, "de": "nein"}) == {"fr": "AB", "en": "x" * 60}, "clean_labs : espaces et controles retires, 60 caracteres, langues autres que fr / en ignorees")
    rapport(g.clean_labs({}) is None and g.clean_labs(["a"]) is None and g.clean_labs("x") is None and g.clean_labs({"fr": ""}) is None, "clean_labs : rien de valide = None")
    ob = g.clean_zones([{"id": "o", "link": "http://x", "label": {"fr": "A", "en": "B"}, "x": 0, "y": 0, "z": 0}], "private")[0]
    rapport(ob.get("label") == "" and ob.get("labs") == {"fr": "A", "en": "B"}, "Python : label ecrit { fr, en } = labels (label vide, pas de repr d'objet)", ob)
    msgs = []
    pz = g.clean_zones([dict(z) for z in ZONES], "private", msgs)
    rapport(pz[0].get("labs") == LAB and pz[0].get("ltitle") == "Mon titre de video", "Python : labels et linkTitle lus (cles internes labs et ltitle)", pz[0])
    rapport("ltitle" not in pz[1] and pz[2].get("labs") == {"en": "Web page"}, "Python : sans linkTitle, pas de ltitle ; labels partiel garde", (pz[1], pz[2]))
    rapport(not [m for m in msgs if m[0] in ("unknown", "ignored")], "Python : labels et linkTitle sont des cles connues, aucun message", msgs)
    out = [g.zone_out(z) for z in pz]
    rapport(out[0].get("labels") == LAB and out[0].get("linkTitle") == "Mon titre de video" and "labs" not in out[0] and "ltitle" not in out[0], "Python : zone_out reecrit labels et linkTitle", out[0])
    rapport(json.dumps(g.clean_zones(out, "private"), sort_keys=True) == json.dumps(pz, sort_keys=True), "Python : aller-retour zone_out puis clean_zones identique")
    cast = g.clean_zones([{"id": "r", "type": "cast", "x": 0, "y": 0, "z": 0, "urls": ["http://a/1", "http://a/2"], "labels": ["Jazz", "Rock"]}], "private")[0]
    rapport(cast.get("streams") == [["Jazz", "http://a/1"], ["Rock", "http://a/2"]] and "labs" not in cast, "Python : labels (liste) d'une radio de l'ancien format = noms de flux, pas un nom de zone", cast)
    arr = g.clean_zones([{"id": "a", "arrival": True, "x": 1, "y": 2, "z": 3, "labels": {"fr": "Arrivee"}}], "private", msgs := [])
    rapport(arr and arr[0].get("labs") == {"fr": "Arrivee"} and not [m for m in msgs if m[0] == "ignored"], "Python : labels permis sur un point d'arrivee", (arr, msgs))
    lt = g.clean_zones([{"id": "p", "portal": "http://x", "x": 0, "y": 0, "z": 0, "linkTitle": "pas ici"}], "private", msgs := [])
    rapport(not (lt and lt[0].get("ltitle")) and any(m[0] == "ignored" and m[2] == "linkTitle" for m in msgs), "Python : linkTitle sur une zone qui n'est pas un lien : ignore, avec message", (lt, msgs))

    # ---- page : langue
    sol_glb(tmp / "sol.glb")
    (tmp / "z.json").write_text(json.dumps(ZONES), encoding="utf-8")
    out_html = tmp / "p.html"
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "sol.glb"), "-o", str(out_html), "--zones", str(tmp / "z.json"), "--no-sea", *vend], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    t = out_html.read_text(encoding="utf-8")
    if "const viewer = createViewer(" not in t:
        sys.exit("[ECHEC] marqueur absent de la page")
    out_html.write_text(t.replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    async with async_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
        br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
        for loc, lab, sous in (("fr-FR", "Vidéo YouTube", "Mon titre de video"), ("en-GB", "YouTube video", "Mon titre de video")):
            pg = await br.new_page(locale=loc, viewport={"width": 1000, "height": 700}); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(out_html.as_uri())
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
            await pg.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
            L = await pg.evaluate("window.__v.getLang ? window.__v.getLang() : document.documentElement.lang")
            b = await bulle(pg, "yt")
            rapport(b is not None and lab in b and "Video" not in b.replace("Vidéo", "") and sous in b and "youtube.com" not in b and "abc123" not in b, f"{loc} : bulle du lien YouTube = nom dans la langue + titre de la video (pas l'adresse)", (L, b))
            b = await bulle(pg, "ytnu")
            rapport(b is not None and "Video sans titre" in b and "youtube.com" in b and "youtu.be/xyz" not in b, f"{loc} : sans linkTitle, un lien YouTube montre « youtube.com » (pas l'adresse entiere)", b)
            b = await bulle(pg, "web")
            want = "Web page" if loc == "en-GB" else "web"
            rapport(b is not None and want in b and "exemple.invalid/page" in b, f"{loc} : un autre lien montre toujours son adresse ; nom {'en' if loc == 'en-GB' else 'absent en fr : id'}", b)
            b = await bulle(pg, "sans")
            want = "Sans langue" if loc == "en-GB" else "Seulement fr"
            rapport(b is not None and want in b and ("Seulement fr" not in b if loc == "en-GB" else True), f"{loc} : langue absente de labels : retombe sur label", b)
            b = await bulle(pg, "objet")
            want = "Object name" if loc == "en-GB" else "Nom objet"
            rapport(b is not None and want in b and "object" not in b.lower().replace("object name", ""), f"{loc} : label ecrit { '{' }fr, en{ '}' } (au lieu de labels) : le nom dans la langue, jamais « [object Object] »", b)
            zl = await pg.evaluate("window.__v.getZones().map(z => window.__v.zoneLabel(z))")
            rapport(zl[0] == lab, f"{loc} : viewer.zoneLabel donne le nom dans la langue", zl)
            rapport(not errs, f"{loc} : aucune erreur JavaScript", errs)
            if loc == "fr-FR":
                # parite JS / Python
                js = await pg.evaluate("""(cas) => { const v = window.__v; const z = v.setZones(cas, { editor: false }); return { z, out: z.map(v.zoneOut), m: v.zoneMessages() }; }""", ZONES)
                norm = lambda o: json.loads(json.dumps(o, sort_keys=True))
                rapport(norm(js["z"]) == norm(pz), "JavaScript : memes zones que Python (labs, ltitle)", [(a["id"], {k: (a.get(k), b2.get(k)) for k in set(a) | set(b2) if a.get(k) != b2.get(k)}) for a, b2 in zip(js["z"], pz) if a != b2][:2])
                rapport(norm(js["out"]) == norm(out), "JavaScript : zoneOut ecrit la meme chose que zone_out", (js["out"][0], out[0]))
                js2 = await pg.evaluate("""(cas) => { const v = window.__v; const a = v.setZones(cas, { editor: false }); const b = v.setZones(a.map(v.zoneOut), { editor: false });
                    const ser = l => JSON.stringify(l.map(z => Object.keys(z).sort().reduce((r, k) => (r[k] = z[k], r), {}))); return ser(a) === ser(b); }""", ZONES)
                rapport(js2, "JavaScript : aller-retour zoneOut puis setZones identique")
                js3 = await pg.evaluate("""() => { const v = window.__v; const z = v.setZones([{ id: 'r', type: 'cast', x: 0, y: 0, z: 0, urls: ['http://a/1'], labels: ['Jazz'] }], { editor: false })[0]; return { s: z.streams, labs: z.labs || null }; }""")
                rapport(js3["labs"] is None and js3["s"] == [["Jazz", "http://a/1"]], "JavaScript : labels (liste) d'une radio de l'ancien format = noms de flux, pas un nom de zone", js3)
            await pg.close()
        await br.close()

    # ---- --link-titles
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Oembed)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    env = dict(os.environ, WEB3D_OEMBED=f"http://127.0.0.1:{srv.server_address[1]}/oembed", WEB3D_LANG="fr")
    lst = [{"id": "a", "x": 0, "y": 0, "z": 0, "link": YT},
           {"id": "b", "x": 1, "y": 0, "z": 0, "link": YT, "linkTitle": "Deja la"},
           {"id": "c", "x": 2, "y": 0, "z": 0, "link": "https://exemple.invalid/x"},
           {"id": "d", "x": 3, "y": 0, "z": 0, "link": "https://youtu.be/introuvable"},
           {"id": "e", "x": 4, "y": 0, "z": 0, "portal": "http://x"}]
    f = tmp / "liens.json"; f.write_text(json.dumps(lst), encoding="utf-8")
    run = lambda: subprocess.run([sys.executable, str(DIST / "glb2html.py"), "--link-titles", str(f)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    r = run(); res = json.loads(f.read_text(encoding="utf-8"))
    rapport(r.returncode == 0 and res[0].get("linkTitle") == "Titre réel de la vidéo", "--link-titles : le titre de la video est ajouté (controles retires)", (r.stdout, r.stderr, res[0]))
    rapport(res[1]["linkTitle"] == "Deja la" and "linkTitle" not in res[2] and "linkTitle" not in res[3] and "linkTitle" not in res[4], "--link-titles : titre deja ecrit, autre lien, titre introuvable et zone sans lien : inchanges", res)
    rapport((tmp / "liens.json.bak").exists() and json.loads((tmp / "liens.json.bak").read_text(encoding="utf-8")) == lst, "--link-titles : l'original est gardé dans .bak")
    rapport("introuvable" in r.stdout and "1 titre" in r.stdout, "--link-titles : dit quel lien n'a pas de titre et combien ont ete ajoutes", r.stdout)
    avant = f.read_text(encoding="utf-8")
    r = run()
    rapport(r.returncode == 0 and "aucun titre" in r.stdout and f.read_text(encoding="utf-8") == avant, "--link-titles : 2e passage : rien a ajouter, fichier intact", r.stdout)
    f2 = tmp / "reglages.json"; f2.write_text(json.dumps({"title": "T", "zones": [lst[0]]}), encoding="utf-8")
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), "--link-titles", str(f2)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    d = json.loads(f2.read_text(encoding="utf-8"))
    rapport(r.returncode == 0 and d.get("title") == "T" and d["zones"][0].get("linkTitle") == "Titre réel de la vidéo", "--link-titles : fichier de reglages (cle zones) : le reste du fichier est conserve", (r.stdout, d))
    env2 = dict(env, WEB3D_OEMBED="http://127.0.0.1:9/oembed")
    f3 = tmp / "mort.json"; f3.write_text(json.dumps([lst[0]]), encoding="utf-8")
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), "--link-titles", str(f3)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env2)
    rapport(r.returncode == 0 and "linkTitle" not in json.loads(f3.read_text(encoding="utf-8"))[0] and not (tmp / "mort.json.bak").exists(), "--link-titles : service injoignable : pas d'erreur, fichier et .bak non touches", (r.returncode, r.stdout, r.stderr))
    print()
    print("RESULTAT : " + ("tout est passe" if not echecs else f"{echecs} echec(s)"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
