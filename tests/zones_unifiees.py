#!/usr/bin/env python3
"""Format unifie des zones (1.12.35) : plus de type ni de target ; ce qu'on voit (image, video, mesh, sinon anneau ou panneau) + ce qui se passe
(link, portal, ha, radio, music) ; arrival pour un point d'arrivee.

Verifie :
 - Python (zone_in, zone_out, clean_zones) et JavaScript (zoneIn, zoneOut, setZones) donnent les memes zones et les memes messages ;
 - aller-retour : chaque zone de l'ancien format, ecrite au nouveau format puis relue, redonne la meme zone ;
 - messages : cle inconnue, cle ignoree, deux visuels, deux actions, combinaison pas encore possible, zone vide ;
 - glb2html.py : lit le nouveau format, affiche les messages, ecrit X.zones.json au nouveau format (mode modulaire) ;
 - glb2html.py --convert-zones : reecrit un fichier de l'ancien format (liste ou reglages), garde FICHIER.bak, puis « rien a convertir » ;
 - un tableau accroche haut (bas du tableau a 3,7 m du sol) se touche en promenade ; un tableau a 8 m ne se touche pas.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/zones_unifiees.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import asyncio, importlib.util, json, os, pathlib, shutil, socket, struct, subprocess, sys, tempfile, time, zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_zu_"))
vend = ["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else []
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {detail}"))
    echecs += not ok


def png(w, h, rgb=(200, 20, 20)):
    brut = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    def ch(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(brut)) + ch(b"IEND", b"")


def mur_glb(path):
    """sol de 40 x 40 m et un mur de 20 x 12 m en z = -5 (normale vers +z) ; la page releve le modele de 15 m (sol a y = 15)"""
    v = [(-20, 0, -20), (20, 0, -20), (20, 0, 20), (-20, 0, 20), (-10, 0, -5), (10, 0, -5), (10, 12, -5), (-10, 12, -5)]
    pos = b"".join(struct.pack("<3f", *p) for p in v)
    blob = pos + struct.pack("<12H", 0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7)
    g = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
         "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 96}, {"buffer": 0, "byteOffset": 96, "byteLength": 24}],
         "accessors": [{"bufferView": 0, "componentType": 5126, "count": 8, "type": "VEC3", "min": [-20, 0, -20], "max": [20, 12, 20]},
                       {"bufferView": 1, "componentType": 5123, "count": 12, "type": "SCALAR"}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
         "nodes": [{"mesh": 0, "name": "salle"}], "scenes": [{"nodes": [0]}], "scene": 0}
    js = json.dumps(g).encode(); js += b" " * ((4 - len(js) % 4) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob))
                     + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + blob)


def serveur(dossier):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=dossier, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close(); return proc, port
        except OSError:
            time.sleep(0.1)
    sys.exit("[ECHEC] serveur http")


P = dict(x=1, y=2, z=3)
# zones au nouveau format : une par sorte, plus les cas qui produisent des messages
CAS = [
    dict(id="arr", label="Entree", yaw=1.5, arrival=True, **P),
    dict(id="arr2", arrival=True, link="x.html", radius=4, **P),                                          # cles ignorees
    dict(id="lien", label="Lien", link="https://exemple.invalid/p", frame=True, trigger="both", radius=3, **P),
    dict(id="lien2", link="https://exemple.invalid/q", shape="board", w=3, h=1.5, showName=True, cone=False, **P),
    dict(id="port", portal="", spawn="arr", trigger="enter", **P),
    dict(id="port2", portal="https://exemple.invalid/r.html", mesh="porte", **P),
    dict(id="ha1", ha="http://exemple.invalid/api", confirm=True, **P),
    dict(id="rad", radio=[["Jazz", "https://exemple.invalid/jazz"], "https://exemple.invalid/b"], poster="p.jpg", posterLink="https://exemple.invalid/s", radius=30, **P),
    dict(id="mus", music="audio", tracks=["a.mp3", "b.mp3"], cone=True, **P),
    dict(id="img", label="Tableau", image="t.png", w=1.5, **P),
    dict(id="img2", image="t.png", link="https://www.youtube.com/watch?v=Qp7TR1RAjXc", frame=True, trigger="both", radius=3, showName=True, **P),
    dict(id="vid", video="clip.mp4", sound=True, w=3, radius=25, **P),
    dict(id="vid2", video="", videoFolder="videos", tracks=["a.mp4"], **P),
    dict(id="inconnu", link="a.html", couleur="rouge", **P),                                              # cle inconnue
    dict(id="ign", portal="b.html", frame=True, poster="p.jpg", sound=True, **P),                       # cles ignorees
    dict(id="deuxv", image="t.png", video="v.mp4", **P),                                                # deux visuels
    dict(id="deuxa", link="a.html", portal="b.html", **P),                                              # deux actions
    dict(id="bport", image="t.png", portal="", spawn="arr", trigger="both", radius=3, **P),                # tableau + portail
    dict(id="bha", image="t.png", ha="http://exemple.invalid/api", confirm=True, **P),                   # tableau + Home Assistant
    dict(id="brad", image="t.png", radio=["https://exemple.invalid/r"], **P),                            # tableau + radio (pochette = tableau)
    dict(id="bmus", image="t.png", music="audio", tracks=["a.mp3"], poster="p.jpg", **P),                # tableau + musique, pochette choisie
    dict(id="mdec", model="m.glb", scale=2, pitch=0.2, roll=-0.1, solid=True, **P),                      # modele seul : decor
    dict(id="mdec2", model="m.glb", radius=5, showName=True, cone=True, **P),                            # decor : rayon, nom et repere ignores
    dict(id="mlink", model="m.glb", link="https://exemple.invalid/m", trigger="both", radius=3, solid=True, **P),   # modele + lien
    dict(id="mrad", model="m.glb", radio=["https://exemple.invalid/r"], poster="p.jpg", scale=0.5, **P),  # modele + radio
    dict(id="mscale", link="a.html", scale=2, pitch=0.1, **P),                                           # taille et inclinaison sans modele : ignorees
    dict(id="mcombo", model="m.glb", image="t.png", **P),                                                # deux visuels
    dict(id="combo2", video="v.mp4", link="a.html", **P),
    dict(id="combo3", mesh="porte", radio=["https://exemple.invalid/r"], **P),
    dict(id="posa", link="a.html", pos=[120, 25.5, -80]),                                               # pos remplace x, y, z
    dict(id="posb", link="a.html", pos=[1, 2, 3], x=9, y=9, z=9),                                       # pos et x, y, z : pos gagne, message
    dict(id="posc", link="a.html", pos=[1, 2], x=4, y=5, z=6),                                          # pos invalide : ignoree, x, y, z gardes
    dict(id="posd", arrival=True, pos=[7, 8, 9]),                                                       # arrivee avec pos
    dict(id="pose", link="a.html", pos=[1, "2", 3], x=4, y=5, z=6),                                     # un texte dans pos : invalide
    dict(id="vide", label="Rien", **P),                                                                 # rien a montrer ni a faire
    dict(id="vide2", mesh="porte", **P),
]
# zones a l'ancien format (une par type) : aller-retour
ANCIEN = [
    {"id": "default", "type": "spawn", "x": 10, "y": 22, "z": -5, "yaw": 0.5},
    {"id": "p", "type": "portal", "target": "", "spawn": "default", "trigger": "enter", "radius": 1.5, "x": 1, "y": 2, "z": 3},
    {"id": "p2", "type": "portal", "target": "https://exemple.invalid/a.html", "shape": "board", "w": 3, "h": 1, "trigger": "both", "x": 1, "y": 2, "z": 3},
    {"id": "u", "type": "url", "target": "https://exemple.invalid/u", "frame": True, "mesh": "porte", "showName": True, "x": 1, "y": 2, "z": 3},
    {"id": "h", "type": "ha", "target": "http://exemple.invalid/api", "confirm": True, "private": True, "x": 1, "y": 2, "z": 3},
    {"id": "c", "type": "cast", "streams": [["Jazz", "https://exemple.invalid/j"]], "poster": "p.jpg", "link": "https://exemple.invalid/s", "radius": 40, "cone": False, "x": 1, "y": 2, "z": 3},
    {"id": "a", "type": "audio", "folder": "audio", "tracks": ["a.mp3"], "x": 1, "y": 2, "z": 3},
    {"id": "i", "type": "image", "target": "t.png", "link": "https://exemple.invalid/l", "frame": True, "trigger": "both", "w": 2, "h": 1, "x": 1, "y": 2, "z": 3},
    {"id": "i2", "type": "image", "target": "t.png", "x": 1, "y": 2, "z": 3, "yaw": 3.14},
    {"id": "v", "type": "video", "target": "", "folder": "videos", "tracks": ["a.mp4"], "sound": True, "w": 4, "radius": 30, "x": 1, "y": 2, "z": 3},
]


def resolu(c, g):
    """Zone interne de l'ancien format avec le cone d'avant (absent = selon le type et le declenchement) rendu explicite : le nouveau format l'ecrit toujours en clair (1.12.41)."""
    c = dict(c)
    if c.get("type") not in ("spawn", "image", "video") and not isinstance(c.get("cone"), bool):
        c["cone"] = g.cone_auto(c)
    return c


def norm(o):
    """nombres : 2 et 2.0 sont la meme valeur (Python ecrit des float)"""
    if isinstance(o, dict):
        return {k: norm(v) for k, v in o.items()}
    if isinstance(o, list):
        return [norm(v) for v in o]
    if isinstance(o, bool) or not isinstance(o, (int, float)):
        return o
    return float(o)


async def main():
    from playwright.async_api import async_playwright
    spec = importlib.util.spec_from_file_location("g2h", DIST / "glb2html.py"); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

    # ---- Python seul
    msgs = []
    pyz = g.clean_zones(CAS, "private", msgs)
    codes = {(m[0], m[1]) for m in msgs}
    attendu = {("ignored", "arr2"), ("unknown", "inconnu"), ("ignored", "ign"), ("visuals", "deuxv"), ("actions", "deuxa"),
               ("posboth", "posb"), ("posbad", "posc"), ("posbad", "pose"), ("combo", "combo2"), ("combo", "combo3"), ("empty", "vide"), ("empty", "vide2"),
               ("ignored", "mdec2"), ("ignored", "mscale"), ("visuals", "mcombo")}
    rapport(codes == attendu, "Python : messages attendus (inconnue, ignoree, deux visuels, deux actions, pas encore possible, vide)", sorted(codes ^ attendu))
    ign = sorted(m[2] for m in msgs if m[:2] == ["ignored", "ign"])
    rapport(ign == ["frame", "poster", "sound"], "Python : portail avec frame, poster et sound : les trois cles signalees", ign)
    rapport(sorted(z["id"] for z in pyz) == sorted(c["id"] for c in CAS if c["id"] not in ("combo2", "combo3", "vide", "vide2")),
            "Python : zones refusees absentes, les autres gardees", [z["id"] for z in pyz])
    t = {z["id"]: z for z in pyz}
    rapport(t["img2"]["type"] == "image" and t["img2"]["link"].startswith("https://www.youtube") and t["img2"]["frame"] is True and t["img2"]["trigger"] == "both"
            and t["port2"]["type"] == "portal" and t["port2"]["mesh"] == "porte" and t["rad"]["type"] == "cast" and t["rad"]["link"] == "https://exemple.invalid/s"
            and t["vid2"]["folder"] == "videos" and t["arr"]["type"] == "spawn" and t["deuxa"]["type"] == "url",
            "Python : chaque cle donne la bonne zone (tableau avec lien, portail lie, radio et lien de pochette, video en dossier, arrivee)", t.get("img2"))

    rapport([(t[k]["x"], t[k]["y"], t[k]["z"]) for k in ("posa", "posb", "posc", "posd", "pose")] == [(120, 25.5, -80), (1, 2, 3), (4, 5, 6), (7, 8, 9), (4, 5, 6)] and "pos" not in g.zone_out(t["posa"]),
            "Python : pos [x, y, z] remplace x, y, z (pos gagne si les deux, invalide ignoree), ecrit en x, y, z", [(t[k]["x"], t[k]["y"], t[k]["z"]) for k in ("posa", "posb", "posc", "posd", "pose")])
    rapport(t["bport"]["type"] == "portal" and t["bport"]["pic"] == "t.png" and t["bha"]["type"] == "ha" and t["bha"]["pic"] == "t.png"
            and t["brad"]["type"] == "cast" and t["brad"]["pic"] == "t.png" and t["bmus"]["type"] == "audio" and t["bmus"]["pic"] == "t.png"
            and t["bmus"].get("poster") == "p.jpg" and "pic" not in t["img2"] and "pic" not in t["mus"],
            "Python : tableau + portail / ha / radio / musique : image gardee, pochette choisie respectee", {k: t[k].get("pic") for k in ("bport", "bha", "brad", "bmus")})
    ok = all(g.zone_out(t[k]).get("image") == "t.png" and "pic" not in g.zone_out(t[k]) for k in ("bport", "bha", "brad", "bmus"))
    rapport(ok, "Python : ecriture : l'image du tableau revient sous la cle image")
    ig2 = sorted(m[2] for m in msgs if m[:2] == ["ignored", "mdec2"]); ig3 = sorted(m[2] for m in msgs if m[:2] == ["ignored", "mscale"])
    rapport(ig2 == ["cone", "radius", "showName"] and ig3 == ["pitch", "scale"], "Python : modele seul : rayon, nom et repere signales ; taille et inclinaison sans modele signalees", (ig2, ig3))
    rapport(t["mdec"]["type"] == "model" and t["mdec"]["mdl"] == "m.glb" and t["mdec"]["mscale"] == 2 and t["mdec"]["pitch"] == 0.2 and t["mdec"]["roll"] == -0.1 and t["mdec"]["solid"] is True
            and t["mlink"]["type"] == "url" and t["mlink"]["mdl"] == "m.glb" and t["mlink"]["target"] == "https://exemple.invalid/m" and t["mlink"]["trigger"] == "both" and t["mlink"]["solid"] is True
            and t["mrad"]["type"] == "cast" and t["mrad"]["mdl"] == "m.glb" and t["mrad"]["mscale"] == 0.5 and t["mrad"]["poster"] == "p.jpg"
            and t["mcombo"]["type"] == "image" and "mdl" not in t["mcombo"] and "mdl" not in t["mscale"] and "mscale" not in t["mscale"],
            "Python : modele seul (decor), modele + lien, modele + radio ; deux visuels : image gagne ; taille sans modele : rien", {k: t[k] for k in ("mdec", "mlink")})
    o1, o2 = g.zone_out(t["mdec"]), g.zone_out(t["mlink"])
    rapport(o1.get("model") == "m.glb" and o1.get("scale") == 2 and o1.get("pitch") == 0.2 and o1.get("roll") == -0.1 and o1.get("solid") is True and "radius" not in o1 and "type" not in o1
            and o2.get("model") == "m.glb" and o2.get("link") == "https://exemple.invalid/m" and o2.get("trigger") == "both" and o2.get("radius") == 3 and "target" not in o2,
            "Python : ecriture : model, scale, pitch, roll, solid (decor sans rayon) ; modele + lien garde rayon et declenchement", (o1, o2))
    # aller-retour
    ok = True
    for z in ANCIEN:
        c = g.clean_zones([z], "private")[0]; u = g.zone_out(c); m = []; c2 = g.clean_zones([u], "private", m)
        if m or not c2 or c2[0] != resolu(c, g) or "type" in u or "target" in u:
            ok = False; print("   ", z["id"], m, u)
    rapport(ok, "Python : aller-retour ancien format -> nouveau -> zone identique, sans type ni target")
    # 1.12.41 : cone faux par defaut dans le format unifie ; l'ancien format garde son comportement et l'ecrit en clair
    cu = g.clean_zones([dict(id="r1", radio=["https://exemple.invalid/r"], **P), dict(id="p1", portal="", **P), dict(id="m1", music="audio", **P),
                        dict(id="r2", radio=["https://exemple.invalid/r"], cone=True, **P)], "private")
    rapport([c.get("cone") for c in cu] == [False, False, False, True] and [g.zone_out(c).get("cone") for c in cu] == [None, None, None, True],
            "Python : format unifie : sans la cle cone, pas de cone (radio, portail, musique) ; cone: true l'allume ; seul le vrai est ecrit", [(c["id"], c.get("cone")) for c in cu])
    lg = g.clean_zones([{"id": "lr", "type": "cast", "streams": [["a", "https://exemple.invalid/r"]], "x": 1, "y": 2, "z": 3}, {"id": "lu", "type": "url", "target": "https://exemple.invalid/u", "x": 1, "y": 2, "z": 3}], "private")
    rapport([g.zone_out(c).get("cone") for c in lg] == [True, None], "Python : ancien format sans cone : la radio garde son cone (ecrit true), l'url en clic n'en a pas", [g.zone_out(c).get("cone") for c in lg])

    # ---- glb2html : lecture, messages, ecriture au nouveau format, conversion
    mur_glb(tmp / "salle.glb")
    site = tmp / "site"; site.mkdir()
    (tmp / "z.json").write_text(json.dumps(CAS), encoding="utf-8")
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "salle.glb"), "-o", str(site / "Salle.html"), "--zones", str(tmp / "z.json"),
                        "--shared-shell", "--no-sea", *vend], capture_output=True, text=True, encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    rapport(r.returncode == 0, "glb2html : un fichier au nouveau format est accepte", r.stdout[-400:] + r.stderr[-400:])
    out = r.stdout
    rapport("clé inconnue « couleur »" in out and "« video » avec « link » n'est pas encore possible" in out and "zone « vide » non affichée" in out,
            "glb2html : les messages sont affiches a la lecture", out[-900:])
    ecrit = json.loads((site / "Salle.zones.json").read_text(encoding="utf-8"))
    rapport(all("type" not in z and "target" not in z for z in ecrit) and len(ecrit) == len(pyz), "glb2html : Salle.zones.json ecrit au nouveau format",
            [z for z in ecrit if "type" in z][:2])
    rapport(norm(g.clean_zones(ecrit, "private")) == norm(pyz), "glb2html : le fichier ecrit redonne les memes zones")

    (tmp / "ancien.json").write_text(json.dumps(ANCIEN), encoding="utf-8")
    reg = {"v": 1, "cfg": {}, "zones": ANCIEN}
    (tmp / "r.reglages.json").write_text(json.dumps(reg), encoding="utf-8")
    sorties = []
    for f in ("ancien.json", "r.reglages.json"):
        r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), "--convert-zones", str(tmp / f)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        sorties.append(r.stdout + r.stderr)
    conv = json.loads((tmp / "ancien.json").read_text(encoding="utf-8"))
    convr = json.loads((tmp / "r.reglages.json").read_text(encoding="utf-8"))
    rapport(all("type" not in z for z in conv) and norm(g.clean_zones(conv, "private")) == norm([resolu(z, g) for z in g.clean_zones(ANCIEN, "private")]),
            "--convert-zones : liste reecrite au nouveau format, memes zones", sorties[0])
    rapport(all("type" not in z for z in convr["zones"]) and convr["v"] == 1 and (tmp / "r.reglages.json.bak").is_file() and (tmp / "ancien.json.bak").is_file(),
            "--convert-zones : fichier de reglages converti (le reste garde), originaux dans .bak", sorties[1])
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), "--convert-zones", str(tmp / "ancien.json")], capture_output=True, text=True, encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    rapport("rien à convertir" in r.stdout and r.returncode == 0, "--convert-zones une seconde fois : rien a convertir", r.stdout)

    # ---- JavaScript : memes zones, memes messages, zoneOut identique
    (site / "t.png").write_bytes(png(8, 8))
    hauts = [dict(id="haut", image="t.png", link="https://exemple.invalid/h", w=1, h=1, x=-4, y=19.2, z=-4.98),      # bas a 3,7 m du sol
             dict(id="trop", image="t.png", link="https://exemple.invalid/t", w=1, h=1, x=4, y=23.5, z=-4.98),
             dict(id="arrx", arrival=True, x=30, y=15, z=30),                                               # arrivee du portail du tableau
             dict(id="tport", image="t.png", portal="", spawn="arrx", trigger="enter", radius=3, w=1.5, h=1, x=-20, y=15.5, z=-20)]        # bas a 8 m
    (tmp / "h.json").write_text(json.dumps(hauts), encoding="utf-8")
    r = subprocess.run([sys.executable, str(DIST / "glb2html.py"), str(tmp / "salle.glb"), "-o", str(site / "page.html"), "--zones", str(tmp / "h.json"), "--no-sea", *vend],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        sys.exit(f"[ECHEC] generation\n{r.stdout}{r.stderr}")
    pg_html = site / "page.html"
    pg_html.write_text(pg_html.read_text(encoding="utf-8").replace("const viewer = createViewer(", "const viewer = window.__v = createViewer(", 1), encoding="utf-8")
    proc, port = serveur(site)
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            pg = await br.new_page(locale="fr-FR"); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://127.0.0.1:{port}/page.html")
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=60000)
            await pg.evaluate("document.getElementById('lightAskNo') && document.getElementById('lightAskNo').click()")
            # promenade : tableau accroche haut
            await pg.evaluate("window.__v.walkStart({ pos: [0, 15, 5], yaw: 0 })"); await pg.wait_for_timeout(1500)
            async def invite(x):
                await pg.evaluate(f"window.__v.teleportTo([{x}, 15, -3.5], 0)"); await pg.wait_for_timeout(700)
                return await pg.evaluate("document.getElementById('zonePrompt').hidden ? '' : document.getElementById('zonePrompt').textContent")
            rapport("haut" in await invite(-4), "promenade : tableau dont le bas est a 3,7 m du sol : invite « clic ou E » (avant : intouchable)")
            rapport(await invite(4) == "", "promenade : tableau dont le bas est a 8 m du sol : pas d'invite")
            # tableau + portail : marcher dans le cercle du tableau teleporte (declenchement a l'approche)
            await pg.evaluate("window.__v.teleportTo([-20, 15, -16], 0)"); await pg.wait_for_timeout(500)
            await pg.keyboard.down("ArrowUp")
            try:
                await pg.wait_for_function("(() => { const w = window.__v.getWalk().pos; return Math.abs(w[0] - 30) < 4 && Math.abs(w[2] - 30) < 4; })()", timeout=15000)
            except Exception:
                pass
            await pg.keyboard.up("ArrowUp")
            w = await pg.evaluate("window.__v.getWalk().pos")
            rapport(abs(w[0] - 30) < 4 and abs(w[2] - 30) < 4, "promenade : tableau + portail (enter) : marcher dans le cercle teleporte a l'arrivee", w)
            # parite JS / Python
            js = await pg.evaluate("""(cas) => { const v = window.__v; const z = v.setZones(cas, { editor: false }); return { z, m: v.zoneMessages(), out: z.map(v.zoneOut) }; }""", CAS)
            rapport(sorted(map(tuple, js["m"])) == sorted(map(tuple, msgs)), "JavaScript : memes messages que Python", (js["m"], msgs))
            rapport(norm(js["z"]) == norm(pyz), "JavaScript : memes zones que Python",
                    [(a["id"], {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if norm(a.get(k)) != norm(b.get(k))}) for a, b in zip(js["z"], pyz) if norm(a) != norm(b)][:3])
            rapport(norm(js["out"]) == norm([g.zone_out(z) for z in pyz]), "JavaScript : zoneOut ecrit la meme chose que zone_out")
            jsa = await pg.evaluate("""(an) => { const v = window.__v; const a0 = v.setZones(an, { editor: false }); const o = a0.map(v.zoneOut); const b = v.setZones(o, { editor: false });
                const a = a0.map(z => (['spawn', 'image', 'video'].includes(z.type) || typeof z.cone === 'boolean') ? z : Object.assign({}, z, { cone: z.type === 'portal' || z.type === 'cast' || z.type === 'audio' || (z.trigger !== 'click' && z.type !== 'image') }));   // 1.12.41 : le cone d'avant, rendu explicite
                const ser = l => JSON.stringify(l.map(z => Object.keys(z).sort().reduce((r, k) => (r[k] = z[k], r), {})));   // l'ordre des cles ne compte pas
                return { same: ser(a) === ser(b), m: v.zoneMessages(), legacy: o.some(z => 'type' in z || 'target' in z) }; }""", ANCIEN)
            rapport(jsa["same"] and not jsa["m"] and not jsa["legacy"], "JavaScript : aller-retour ancien format -> nouveau -> zone identique", jsa)
            jc = await pg.evaluate("""() => { const v = window.__v, P = { x: 1, y: 2, z: 3 };
                const u = v.setZones([Object.assign({ id: 'r1', radio: ['https://exemple.invalid/r'] }, P), Object.assign({ id: 'r2', radio: ['https://exemple.invalid/r'], cone: true }, P)], { editor: false });
                const l = v.setZones([{ id: 'lr', type: 'cast', streams: [['a', 'https://exemple.invalid/r']], x: 1, y: 2, z: 3 }, { id: 'lu', type: 'url', target: 'https://exemple.invalid/u', x: 1, y: 2, z: 3 }], { editor: false });
                return { u: u.map(z => z.cone), uo: u.map(z => v.zoneOut(z).cone), lo: l.map(z => v.zoneOut(z).cone) }; }""")
            rapport(jc["u"] == [False, True] and jc["uo"] == [None, True] and jc["lo"] == [True, None],
                    "JavaScript : format unifie : sans cone pas de cone, cone: true l'allume ; ancien format sans cone : la radio garde le sien (ecrit true), l'url en clic non", jc)
            rapport(not errs, "aucune erreur JavaScript", errs)
            await br.close()
    finally:
        proc.kill()
    shutil.rmtree(tmp, ignore_errors=True)
    print("\nRÉSULTAT : " + ("tout est passé" if not echecs else f"ÉCHEC ({echecs})"))
    sys.exit(1 if echecs else 0)


asyncio.run(main())
