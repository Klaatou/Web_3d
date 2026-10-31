#!/usr/bin/env python3
"""Tests v37 (lot 1) : indicateur de course, repère de portail à taille constante (cône) et distance dans l'infobulle, arrivée occupée (plus proche de l'occupant, tourné vers lui),
pseudo cité (clignotement continu jusqu'à la première action), paramètres du hash séparés par & ou #, boussole, aide des outils, fenêtres Aide et Informations redimensionnables.

Prérequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/v37.py
"""
import asyncio, json, math, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

FLOOR = 15
print("--- 0. fabrication des pages")
presence, pport = lancer_presence("--chat-burst", "100", "--chat-gap", "0.1")
PURL = f"ws://127.0.0.1:{pport}"
site = tmp / "site"
site.mkdir()
sol_glb(site / "sol.glb")
sol_glb(site / "grand.glb", 200.0)
ZL = [
    {"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0.0},
    {"id": "autre", "type": "spawn", "x": 6, "y": 15, "z": 6, "yaw": 0.0},
    {"id": "loin", "type": "portal", "label": "château", "target": "", "spawn": "autre", "x": 150, "y": 15, "z": 0, "radius": 2, "trigger": "enter"},
]
(tmp / "z.json").write_text(json.dumps(ZL), encoding="utf-8")
base = ["--shared-shell", "--zones", tmp / "z.json", "--no-sea", "--target", "0,0,0", "--presence-url", PURL, "--room", "t37", "--chat", *vend]
html(site / "grand.glb", "-o", site / "Grand.html", *base)
html(site / "sol.glb", "-o", site / "Sol.html", *base)
html(site / "sol.glb", "-o", site / "Rot.html", *base, "--rotate", "90", "--north", "180")
html(site / "sol.glb", "-o", site / "NoComp.html", *base, "--no-compass")
cfg = json.loads((site / "Sol.config.json").read_text(encoding="utf-8"))
cfg_r = json.loads((site / "Rot.config.json").read_text(encoding="utf-8"))
cfg_n = json.loads((site / "NoComp.config.json").read_text(encoding="utf-8"))
rapport(cfg["compass"] is True and cfg["northDeg"] == 0 and cfg["zoneInfoDist"] == 150, "config : compass vrai, northDeg 0, zoneInfoDist 150 par défaut", (cfg["compass"], cfg["northDeg"], cfg["zoneInfoDist"]))
rapport(cfg_r["northDeg"] == 180 and cfg_r["rotate"] == 90 and cfg_n["compass"] is False, "config : --north 180, --rotate 90, --no-compass")
r = html(site / "sol.glb", "-o", site / "Large.html", *base, "--zone-info-dist", "500")
rapport(json.loads((site / "Large.config.json").read_text(encoding="utf-8"))["zoneInfoDist"] == 500, "--zone-info-dist accepte jusqu'à 500")
html(site / "sol.glb", "-o", site / "Large.html", *base, "--zone-info-dist", "900")
rapport(json.loads((site / "Large.config.json").read_text(encoding="utf-8"))["zoneInfoDist"] == 500, "--zone-info-dist 900 est borné à 500")

# --- aide des outils
for outil, nom in (("glb2html.py", "glb2html.py"), ("glb2tiles.py", "glb2tiles.py"), ("oar2glb.py", "oar2glb.py"), ("presence_server.py", "presence_server.py")):
    for lg in ("fr", "en"):
        e = dict(os.environ, WEB3D_LANG=lg)
        t = subprocess.run([sys.executable, str(DIST / outil), "--help"], capture_output=True, text=True, env=e, input="").stdout
        prem = [l for l in t.splitlines() if l.strip()]
        ligne = next((l for l in prem if l.startswith(nom)), "")
        ver = __import__("json").loads((ROOT / "VERSIONS.json").read_text(encoding="utf-8"))[outil]["version"]
        rapport(bool(re.match(re.escape(nom) + " " + re.escape(ver) + r" ?: \S", ligne)), f"{outil} --help ({lg}) : ligne « {nom} {ver} : … »", ligne[:90])

STUB2 = STUB + "try { localStorage.setItem('glb2html_name', 'Alice'); } catch (e) {}"


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        proc, port = serveur(site)
        base_url = f"http://127.0.0.1:{port}/index.html?region="
        try:
            # ================= 1.5 hash =================
            print("--- 1.5 paramètres du hash : & ou #")
            o = await Onglet(br).ouvrir(base_url + "Sol", init=STUB)
            rapport(await o.ev("hashParams('#name=Klaatou&lang=en').get('lang') === 'en' && hashParams('#name=Klaatou#lang=en').get('name') === 'Klaatou' && hashParams('#name=Klaatou#lang=en').get('lang') === 'en'"), "hashParams : les deux séparateurs sont équivalents")
            await o.ctx.close()
            for h in ("#name=Klaatou&lang=en", "#name=Klaatou#lang=en"):
                o = await Onglet(br).ouvrir(base_url + "Sol" + h, init=STUB)
                nom = await o.ev("window.__viewer.getName()")
                lang = await o.ev("document.documentElement.lang")
                rapport(nom == "Klaatou" and lang == "en", f"{h} : pseudo « Klaatou », langue en", (nom, lang))
                await o.ctx.close()
            for h in ("#spawn=autre&name=Zed1", "#spawn=autre#name=Zed2"):
                o = await Onglet(br).ouvrir(base_url + "Sol" + h, init=STUB)
                await o.attendre("window.__viewer.walking", 30)
                w = await o.gw()
                rapport(dist_h(w["pos"], (6, 0, 6)) < 1.0 and await o.ev("window.__viewer.getName()") == h[-4:], f"{h} : arrivée « autre » et pseudo {h[-4:]}", w["pos"])
                await o.ctx.close()
            for h in ("#pos=3,15,4,0&name=Zed3", "#pos=3,15,4,0#name=Zed4"):
                o = await Onglet(br).ouvrir(base_url + "Sol" + h, init=STUB)
                await o.attendre("window.__viewer.walking", 30)
                w = await o.gw()
                rapport(dist_h(w["pos"], (3, 0, 4)) < 0.5 and await o.ev("window.__viewer.getName()") == h[-4:], f"{h} : arrivée à la position demandée et pseudo {h[-4:]}", w["pos"])
                await o.ctx.close()
            clef = "0123456789abcdef0123456789abcdef"
            for h in (f"#key={clef}&name=Zed5", f"#key={clef}#name=Zed6"):
                o = await Onglet(br).ouvrir(base_url + "Sol" + h, init=STUB)
                k = await o.ev("localStorage.getItem('glb2html_uid')")
                rapport(k == clef and await o.ev("window.__viewer.getName()") == h[-4:] and "key" not in await o.ev("location.hash"), f"{h[:12]}… : clé adoptée, retirée de l'adresse, pseudo {h[-4:]}", (k, await o.ev("location.hash")))
                await o.ctx.close()

            # ================= 1.1 course =================
            print("--- 1.1 indicateur de course")
            o = await Onglet(br).ouvrir(base_url + "Sol", init=STUB)
            await o.walk((0, 15, 0), 0)
            await o.ticks(5)
            rapport("course" not in await o.txt("modeInfo") and "à pied" in await o.txt("modeInfo"), "à pied sans course : « à pied »", await o.txt("modeInfo"))
            await o.key("keydown", "ShiftLeft"); await o.ticks(3)
            rapport(await o.txt("modeInfo") == "Mode : à pied · course", "Maj tenu : « à pied · course »", await o.txt("modeInfo"))
            await o.key("keyup", "ShiftLeft"); await o.ticks(3)
            rapport(await o.txt("modeInfo") == "Mode : à pied", "Maj relâché : « à pied »", await o.txt("modeInfo"))
            await o.key("keydown", "KeyW"); await o.key("keyup", "KeyW"); await o.key("keydown", "KeyW"); await o.ticks(3)
            rapport("course" in await o.txt("modeInfo"), "double appui rapide sur W : course", await o.txt("modeInfo"))
            await o.key("keyup", "KeyW"); await o.ticks(3)
            rapport("course" not in await o.txt("modeInfo"), "W relâché : fin de la course", await o.txt("modeInfo"))
            await o.touche("Home"); await o.ticks(3)
            await o.key("keydown", "ShiftLeft"); await o.ticks(3)
            rapport(await o.txt("modeInfo") == "Mode : en vol · course", "en vol, Maj tenu : « en vol · course »", await o.txt("modeInfo"))
            await o.key("keyup", "ShiftLeft"); await o.ticks(3)
            rapport(await o.txt("modeInfo") == "Mode : en vol", "en vol, Maj relâché : « en vol »", await o.txt("modeInfo"))
            await o.ctx.close()

            # ================= 1.6 boussole =================
            print("--- 1.6 boussole")
            motif = re.compile(r"^(N|NE|E|SE|S|SO|O|NO) \d+°$")
            o = await Onglet(br).ouvrir(base_url + "Sol", init=STUB)
            await o.pg.wait_for_timeout(300)
            t = await o.txt("compass")
            rapport(bool(motif.match(t)) and not await o.ev("document.getElementById('compass').hidden"), "vue globale : cap de la caméra affiché", t)
            await o.walk((0, 15, 0), 0)
            await o.pg.wait_for_timeout(300)
            rapport(await o.txt("compass") == "N 0°", "avatar orienté vers -Z : « N 0° »", await o.txt("compass"))
            for yaw, att in ((-math.pi / 4, "NE 45°"), (-math.pi / 2, "E 90°"), (-math.pi, "S 180°"), (math.pi / 2, "O 270°"), (math.pi / 4, "NO 315°")):
                await o.ev("(y) => window.__viewer.walkStart && 0", yaw)
                await o.ev("([p, y]) => window.__viewer.teleportTo(p, y)", [[0, 15, 0], yaw])
                await o.ticks(5)
                await o.pg.wait_for_timeout(250)
                rapport(await o.txt("compass") == att, f"yaw {yaw:.2f} : « {att} »", await o.txt("compass"))
            await o.ev("document.getElementById('optsBtn').click()")
            rapport(await o.ev("document.getElementById('visCompass').checked"), "Réglages visiteur : case « Boussole » cochée par défaut")
            await o.ev("document.getElementById('visCompass').click()")
            await o.pg.wait_for_timeout(300)
            rapport(await o.ev("document.getElementById('compass').hidden"), "case décochée : boussole masquée")
            await o.pg.reload(); await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            await o.pg.wait_for_timeout(400)
            rapport(await o.ev("document.getElementById('compass').hidden"), "le choix est mémorisé après rechargement")
            await o.ctx.close()
            o = await Onglet(br).ouvrir(base_url + "Rot", init=STUB)
            await o.walk((0, 15, 0), 0)
            await o.pg.wait_for_timeout(300)
            rapport(await o.txt("compass") == "O 270°", "rotate 90 et --north 180, avatar vers -Z : 90 + 180 = « O 270° »", await o.txt("compass"))
            await o.ctx.close()
            o = await Onglet(br).ouvrir(base_url + "Sol#lang=en", init=STUB)
            await o.walk((0, 15, 0), math.pi / 2)
            await o.pg.wait_for_timeout(300)
            rapport(await o.txt("compass") == "W 270°", "anglais : « W 270° »", await o.txt("compass"))
            await o.ctx.close()
            o = await Onglet(br).ouvrir(base_url + "NoComp", init=STUB)
            await o.walk((0, 15, 0), 0)
            await o.pg.wait_for_timeout(300)
            rapport(await o.ev("document.getElementById('compass').hidden") and not await o.ev("!!document.getElementById('visCompass')"), "--no-compass : boussole absente, pas de case") if False else rapport(await o.ev("document.getElementById('compass').hidden") and await o.ev("!document.getElementById('visCompass')"), "--no-compass : boussole masquée, pas de case")
            await o.ctx.close()

            # ================= 1.2 cône =================
            print("--- 1.2 cône : taille constante à l'écran, distance dans l'infobulle")
            o = await Onglet(br).ouvrir(base_url + "Grand", init=STUB)
            await o.walk((50, 15, 0), -math.pi / 2)
            await o.ticks(5)
            await o.pg.wait_for_timeout(500)
            cs = await o.ev("window.__viewer.getCones()")
            c = next((x for x in cs if x["id"] == "loin"), None)
            rapport(c is not None and c["visible"] and 90 < c["dist"] < 110, "à 100 m (zoneInfoDist 150) le cône est visible", c)
            rapport(c is not None and c["px"] >= 8 and 7 < c["scale"] <= 12, f"taille projetée {c['px']:.1f} px (≥ 8), échelle {c['scale']:.1f}" if c else "", c)
            await o.pg.mouse.move(c["sx"], c["sy"] + 2)
            await o.pg.mouse.move(c["sx"], c["sy"])
            await o.pg.wait_for_timeout(300)
            tip = await o.ev("(document.getElementById('zoneTip') || {}).textContent || ''")
            m = re.search(r"· (\d+) m$", tip)
            rapport(bool(m) and abs(int(m.group(1)) - round(c["dist"] if False else math.dist(c["pos"], [50, 15, 0]))) <= 3 and "château" in tip, "infobulle : nom et distance (« … · 100 m »)", tip)
            await o.ev("window.__viewer.teleportTo([120, 15, 0], -Math.PI / 2)")
            await o.ticks(5)
            await o.pg.wait_for_timeout(400)
            c2 = next(x for x in await o.ev("window.__viewer.getCones()") if x["id"] == "loin")
            await o.pg.mouse.move(c2["sx"], c2["sy"] + 3); await o.pg.mouse.move(c2["sx"], c2["sy"])
            await o.pg.wait_for_timeout(300)
            tip2 = await o.ev("(document.getElementById('zoneTip') || {}).textContent || ''")
            m2 = re.search(r"· (\d+) m$", tip2)
            rapport(bool(m2) and int(m2.group(1)) < int(m.group(1)) - 50, f"la distance est mise à jour quand on s'approche ({m.group(1)} m puis {m2.group(1) if m2 else '?'} m)", tip2)
            rapport(c2["scale"] < c["scale"] and c2["px"] >= 8, f"plus près, l'échelle diminue ({c2['scale']:.1f}) et la taille à l'écran reste ≥ 8 px ({c2['px']:.1f})")
            await o.ev("window.__viewer.walkStop && window.__viewer.walkStop()")
            await o.ctx.close()

            # ================= 1.3 arrivée occupée =================
            print("--- 1.3 arrivée occupée (deux navigateurs, vrai presence_server.py)")
            A = await Onglet(br).ouvrir(base_url + "Sol#spawn=default", init=STUB2)
            await A.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await A.pg.wait_for_timeout(1300)
            pa = (await A.gw())["pos"]
            B = await Onglet(br).ouvrir(base_url + "Sol#spawn=default", init=STUB + "try { localStorage.setItem('glb2html_name', 'Bea'); } catch (e) {}")
            await B.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await B.pg.wait_for_timeout(1500)
            gb = await B.gw()
            pb = gb["pos"]
            d = dist_h(pb, pa)
            rapport(1.0 <= d <= 2.5, f"le second arrive entre 1 et 2,5 m du premier ({d:.2f} m)", (pa, pb))
            att = math.atan2(-(pa[0] - pb[0]), -(pa[2] - pb[2]))
            ecart = abs(math.degrees(math.atan2(math.sin(gb["yaw"] - att), math.cos(gb["yaw"] - att))))
            rapport(ecart < 20, f"le second regarde vers le premier (écart {ecart:.1f}°)", (gb["yaw"], att))
            rapport(any(re.search(r"arrivée occupée : décalé de [\d.]+ m \(anneau [\d.]+ m\)", l) for l in B.logs), "ligne console « arrivée occupée : décalé de X m (anneau R m) »", [l for l in B.logs if "occup" in l])
            await A.ctx.close(); await B.ctx.close()

            # ================= 1.4 pseudo cité =================
            print("--- 1.4 pseudo cité : clignotement continu jusqu'à la première action")
            A = await Onglet(br).ouvrir(base_url + "Sol#spawn=default", init=STUB + "try { localStorage.setItem('glb2html_name', 'Dana'); } catch (e) {}")
            await A.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            B = await Onglet(br).ouvrir(base_url + "Sol#spawn=default", init=STUB + "try { localStorage.setItem('glb2html_name', 'Cleo'); } catch (e) {}")
            await B.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await asyncio.sleep(2.0)
            await A.attendre("window.__viewer.getPresence().peers.some(p => p.name === 'Cleo')", 30)
            await asyncio.sleep(1.0)
            await A.ev("""() => { window.__samples = []; window.__lines = []; setInterval(() => { const p = window.__viewer.getPresence().peers.find(q => q.name === 'Cleo');
                window.__samples.push(p ? p.labelVisible : null);
                const ls = [...document.querySelectorAll('#chatLog div')].filter(d => d.textContent.includes('cite'));
                window.__lines.push(ls.map(d => d.style.visibility !== 'hidden')); }, 50); }""")
            await B.ev("window.__viewer.sendChat('salut @dana, premier cite')")
            await asyncio.sleep(0.4)
            await B.ev("window.__viewer.sendChat('encore dana, second cite')")
            await asyncio.sleep(4.0)
            s = await A.ev("window.__samples.slice(-80)")
            flips = sum(1 for a, b in zip(s, s[1:]) if a != b)
            rapport(flips >= 5 and s.count(False) >= 10 and s.count(True) >= 10, f"l'étiquette du nom bascule visible / cachée {flips} fois en 4 s sans action", s[:40])
            rapport(await A.ev("window.__viewer.getPresence().peers.find(q => q.name === 'Cleo').blinking"), "toujours en train de clignoter après plus de 3 s")
            lignes = await A.ev("window.__lines.slice(-80)")
            deux = [l for l in lignes if len(l) == 2]
            rapport(len(deux) > 20 and any(not l[0] for l in deux) and any(not l[1] for l in deux) and any(l[0] for l in deux), "les deux lignes de messages cités clignotent", deux[:6])
            await A.pg.keyboard.press("Shift")
            await asyncio.sleep(1.4)
            s = await A.ev("window.__samples.slice(-20)")
            rapport(all(s) and not await A.ev("window.__viewer.getPresence().peers.find(q => q.name === 'Cleo').blinking"), "après une touche : tout reste visible, plus de clignotement", s)
            rapport(await A.ev("[...document.querySelectorAll('#chatLog div')].every(d => d.style.visibility !== 'hidden')"), "les lignes du chat sont visibles")
            # mouvement de l'avatar
            await B.ev("window.__viewer.sendChat('encore une fois dana')")
            await asyncio.sleep(1.0)
            rapport(await A.ev("window.__viewer.getPresence().peers.find(q => q.name === 'Cleo').blinking"), "nouvelle citation : le clignotement reprend")
            await A.ev("window.__viewer.teleportTo([3, 15, 3], 0)")
            await A.ticks(3)
            await asyncio.sleep(0.5)
            rapport(not await A.ev("window.__viewer.getPresence().peers.find(q => q.name === 'Cleo').blinking"), "mouvement de l'avatar : le clignotement s'arrête")
            await B.ev("window.__viewer.sendChat('et dana encore')")
            await asyncio.sleep(0.8)
            await A.pg.mouse.click(500, 300)
            await asyncio.sleep(0.3)
            rapport(not await A.ev("window.__viewer.getPresence().peers.find(q => q.name === 'Cleo').blinking"), "un clic arrête le clignotement")
            await A.ctx.close(); await B.ctx.close()

            # touche O : fenêtre Réglages
            o = await Onglet(br).ouvrir(base_url + "Sol", init=STUB)
            h0 = await o.ev("document.getElementById('optsPanel').hidden")
            await o.touche("KeyO"); h1 = await o.ev("document.getElementById('optsPanel').hidden")
            await o.touche("KeyO"); h2 = await o.ev("document.getElementById('optsPanel').hidden")
            rapport(h0 and not h1 and h2, "touche O : ouvre puis ferme la fenêtre Réglages", (h0, h1, h2))
            await o.walk((0, 15, 0), 0)
            rapport("O : réglages" in await o.txt("helpBody"), "l'aide cite « O : réglages »")
            await o.ctx.close()
            # ================= 1.8 fenêtres redimensionnables =================
            print("--- 1.8 Aide et Informations redimensionnables")
            o = await Onglet(br).ouvrir(base_url + "Sol", init=STUB, viewport={"width": 1000, "height": 1300})
            await o.walk((0, 15, 0), 0)
            await o.pg.wait_for_timeout(500)
            geo = """() => { const g = id => { const r = document.getElementById(id).getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom, w: r.width, h: r.height, sc: document.getElementById(id).scrollHeight > document.getElementById(id).clientHeight + 1 }; };
                return { help: g('walkHint'), info: g('stateInfo') }; }"""
            g0 = await o.ev(geo)
            rapport(g0["help"]["w"] <= 441 and g0["info"]["w"] <= 441 and abs(g0["info"]["t"] - g0["help"]["b"]) < 12, "largeurs par défaut ≤ 440 px, fenêtres empilées et collées", g0)
            x = g0["help"]["r"] - 3; y = g0["help"]["t"] + 30
            await o.pg.mouse.move(x, y); await o.pg.mouse.down(); await o.pg.mouse.move(x + 150, y, steps=5); await o.pg.mouse.up()
            g1 = await o.ev(geo)
            rapport(g1["help"]["w"] > g0["help"]["w"] + 100 and g1["help"]["h"] <= g0["help"]["h"] + 1, f"tirer le bord droit de l'aide l'élargit ({g0['help']['w']:.0f} → {g1['help']['w']:.0f} px) et la hauteur suit ({g0['help']['h']:.0f} → {g1['help']['h']:.0f} px)", g1)
            rapport(abs(g1["info"]["t"] - g1["help"]["b"]) < 12 and g1["info"]["b"] > 1000, "l'aide reste collée aux informations, en bas à gauche", g1)
            x = g1["help"]["r"] - 3; y = g1["help"]["t"] + 30
            await o.pg.mouse.move(x, y); await o.pg.mouse.down(); await o.pg.mouse.move(x - 600, y, steps=5); await o.pg.mouse.up()
            g2 = await o.ev(geo)
            rapport(abs(g2["help"]["w"] - 260) < 2 and g2["help"]["h"] > g1["help"]["h"] + 20 and not g2["help"]["sc"], f"largeur minimale 260 px : hauteur {g2['help']['h']:.0f} px, sans barre de défilement", g2)
            rapport(abs(g2["info"]["t"] - g2["help"]["b"]) < 12, "toujours collées après le rétrécissement", g2)
            x = g2["help"]["r"] - 3; y = g2["help"]["t"] + 30
            await o.pg.mouse.move(x, y); await o.pg.mouse.down(); await o.pg.mouse.move(x + 900, y, steps=5); await o.pg.mouse.up()
            g3 = await o.ev(geo)
            rapport(abs(g3["help"]["w"] - 700) < 3, f"largeur maximale 70 % de la fenêtre (700 px sur 1000) : {g3['help']['w']:.0f} px", g3)
            ys = g3["info"]["t"] + 12
            await o.pg.mouse.move(g3["info"]["r"] - 3, ys); await o.pg.mouse.down(); await o.pg.mouse.move(g3["info"]["r"] + 117, ys, steps=5); await o.pg.mouse.up()
            g4 = await o.ev(geo)
            rapport(g4["info"]["w"] > g3["info"]["w"] + 60, "la fenêtre Informations se règle aussi", g4)
            await o.pg.reload(); await o.pg.wait_for_function("document.getElementById('msg') === null && window.__viewer", timeout=40000)
            await o.walk((0, 15, 0), 0)
            await o.pg.wait_for_timeout(400)
            g5 = await o.ev(geo)
            rapport(abs(g5["help"]["w"] - g3["help"]["w"]) < 2 and abs(g5["info"]["w"] - g4["info"]["w"]) < 2, "les deux largeurs sont mémorisées après rechargement", (g3["help"]["w"], g5["help"]["w"], g4["info"]["w"], g5["info"]["w"]))
            await o.ctx.close()
        finally:
            proc.terminate()
            await br.close()
    print("\nRÉSULTAT : " + ("tout est passé" if not h37.bad else f"{h37.bad} échec(s)"))
    presence.terminate()
    sys.exit(1 if h37.bad else 0)


asyncio.run(main())
