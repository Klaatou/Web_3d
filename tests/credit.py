#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Icone « Realise avec Web_3d » (lot 1.6.13) : bas a droite de la page et de la carte, avec sa bulle et son lien vers le depot.

Verifie, sur le paquet region-simple fabrique : le lien (adresse, nouvel onglet, noopener), la forme (carree, pas plus haute que les boutons de la page),
la place (coin bas droit), la bulle (cachee, puis au survol, en francais et en anglais), le chat qui passe au-dessus, les deux modes (vue globale et
promenade), la carte, et l'ecran tactile (colonne de boutons au-dessus, icone cachee quand la saisie du chat occupe le bas).
Prerequis : python build.py. Variables facultatives : THREE_DIR (racine d'un paquet npm three, hors ligne), CHROMIUM. Lancer : python tests/credit.py
"""
import asyncio, json, os, pathlib, shutil, socket, subprocess, sys, tempfile, time, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEPOT = "https://github.com/Klaatou/Web_3d"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="glb2html_credit_"))
echecs = 0


def rapport(ok, titre, detail=""):
    global echecs
    print(("[OK]    " if ok else "[ECHEC] ") + titre + ("" if ok else f"  {str(detail)[:400]}"), flush=True)
    echecs += not ok


cmd = [sys.executable, str(ROOT / "fabriquer_paquets.py"), "--out", str(tmp / "zips")] + (["--vendor", os.environ["THREE_DIR"]] if os.environ.get("THREE_DIR") else [])
r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
rapport(r.returncode == 0, "fabrication des zips", (r.stdout + r.stderr)[-300:])
if r.returncode:
    sys.exit(1)
zipfile.ZipFile(tmp / "zips" / "region-simple.zip").extractall(tmp / "x")
site = tmp / "x" / "region-simple" / "site"

INFO = """() => { const c = document.getElementById('credit'); if (!c) return null; const r = c.getBoundingClientRect(), s = getComputedStyle(c), t = document.getElementById('creditTip'), tr = t.getBoundingClientRect();
  return { href: c.getAttribute('href'), target: c.getAttribute('target'), rel: c.getAttribute('rel'), w: r.width, h: r.height, right: innerWidth - r.right, bottom: innerHeight - r.bottom, top: r.top, left: r.left,
           display: s.display, tipShown: getComputedStyle(t).display !== 'none', tip: t.textContent, tipRect: [tr.left, tr.top, tr.right, tr.bottom], aria: c.getAttribute('aria-label') || '' } }"""


def serveur(d):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    return subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL), port


async def main():
    from playwright.async_api import async_playwright
    proc, port = serveur(site)
    time.sleep(1.5)
    base = f"http://127.0.0.1:{port}/"
    try:
        async with async_playwright() as p:
            kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
            br = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"], **kw)
            # ---- la page, en francais
            pg = await br.new_page(locale="fr-FR", viewport={"width": 1200, "height": 700}); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(base + "index.html")
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=90000)
            await pg.wait_for_timeout(1500)
            c = await pg.evaluate(INFO)
            bh = await pg.evaluate("Math.max(...[...document.querySelectorAll('#bar button')].filter(b => !b.hidden).map(b => b.getBoundingClientRect().height))")
            im = await pg.evaluate("(() => { const i = document.querySelector('#credit img'); return i ? { ok: i.complete && i.naturalWidth > 0, src: i.getAttribute('src').slice(0, 22), nat: [i.naturalWidth, i.naturalHeight] } : null; })()")
            rapport(bool(im) and im["ok"] and im["src"].startswith("data:image/png") and im["nat"][0] >= 64, "page : l'image du logo est chargee (PNG integre a la page)", im)
            bruts = [n for n in ("index.html", "carte.html", "glb2html.py", "glb-viewer.html") if "__CREDIT_ICON__" in (ROOT / "dist" / n).read_text(encoding="utf-8")]
            rapport(not bruts, "dist : aucun jeton __CREDIT_ICON__ n'est reste dans les fichiers fabriques", bruts)
            rapport(bool(c) and c["href"] == DEPOT and c["target"] == "_blank" and "noopener" in (c["rel"] or ""), "page : l'icone mene au depot, dans un nouvel onglet, avec noopener", c)
            rapport(bool(c) and abs(c["w"] - c["h"]) < 0.6 and c["h"] <= bh + 0.5, "page : l'icone est carree et pas plus haute que les boutons de la page", (c and [c["w"], c["h"]], bh))
            rapport(bool(c) and abs(c["right"] - 12) <= 1 and abs(c["bottom"] - 12) <= 1, "page : l'icone est tout en bas a droite (12 px des bords)", c and [c["right"], c["bottom"]])
            rapport(bool(c) and not c["tipShown"] and "Web_3d" in c["tip"] and c["aria"] != "", "page : la bulle est cachee au repos, le nom accessible existe", c and [c["tipShown"], c["tip"], c["aria"]])
            await pg.mouse.move(c["left"] + c["w"] / 2, c["top"] + c["h"] / 2); await pg.wait_for_timeout(300)
            c2 = await pg.evaluate(INFO)
            tr_ = c2["tipRect"]
            rapport(c2["tipShown"] and 0 <= tr_[0] and tr_[2] <= 1200 and 0 <= tr_[1] and tr_[3] <= c2["top"] + 1, "page : au survol, la bulle apparait, entiere dans la fenetre et au-dessus de l'icone", c2["tipRect"])
            await pg.mouse.move(300, 300); await pg.wait_for_timeout(300)
            rapport(not (await pg.evaluate(INFO))["tipShown"], "page : la bulle disparait quand la souris part")
            # promenade : le chat passe au-dessus de l'icone
            await pg.keyboard.press("f"); await pg.wait_for_function("window.__viewer && window.__viewer.walking", timeout=20000); await pg.wait_for_timeout(500)
            await pg.evaluate("document.getElementById('chat').hidden = false")
            ch = await pg.evaluate("(() => { const r = document.getElementById('chat').getBoundingClientRect(); return [r.top, r.bottom, innerHeight - r.bottom, innerWidth - r.right]; })()")
            c3 = await pg.evaluate(INFO)
            rapport(c3["display"] != "none" and abs(c3["right"] - 12) <= 1, "promenade : l'icone est toujours la, au meme endroit", c3 and [c3["display"], c3["right"], c3["bottom"]])
            rapport(ch[1] <= c3["top"] - 3 and abs(ch[3] - 12) <= 1, "promenade : le chat est au-dessus de l'icone, sans la toucher, toujours a droite", [ch, c3["top"]])
            rapport(not errs, "page : aucune erreur JavaScript", errs[:2])
            await pg.close()
            # ---- la page, en anglais
            pe = await br.new_page(locale="en-US", viewport={"width": 1200, "height": 700})
            await pe.goto(base + "index.html")
            await pe.wait_for_function("document.getElementById('msg') === null", timeout=90000)
            await pe.wait_for_timeout(1000)
            ce = await pe.evaluate(INFO)
            rapport(bool(ce) and ce["tip"].startswith("Made with") and ce["aria"].startswith("Made with"), "page en anglais : la bulle et le nom accessible sont en anglais", ce and [ce["tip"], ce["aria"]])
            await pe.close()
            # ---- ecran tactile : paysage court (colonne de boutons sur trois colonnes) et portrait
            for nom_t, vp in (("paysage", {"width": 800, "height": 420}), ("portrait", {"width": 420, "height": 800})):
                pt = await br.new_page(locale="fr-FR", viewport=vp)
                await pt.goto(base + "index.html")
                await pt.wait_for_function("document.getElementById('msg') === null", timeout=90000)
                await pt.wait_for_timeout(1000)
                # tout dans le meme appel : la page peut retirer elle-meme la classe « touch » (detection de l'ecran) entre deux appels
                res = await pt.evaluate("""() => {
                  document.body.classList.add('touch'); const t = document.getElementById('tcol'); t.hidden = false;
                  if (!t.children.length) { for (let i = 0; i < 7; i++) { const b = document.createElement('button'); b.textContent = 'B' + i; t.appendChild(b); } }
                  const r = t.getBoundingClientRect(), c = document.getElementById('credit').getBoundingClientRect();
                  const tc = [r.bottom, c.top, innerWidth - c.right, innerHeight - c.bottom];
                  document.body.classList.add('chatOpen');
                  return { tc, cache: getComputedStyle(document.getElementById('credit')).display === 'none' }; }""")
                tc = res["tc"]
                rapport(tc[0] <= tc[1] - 3 and abs(tc[2] - 12) <= 1 and abs(tc[3] - 12) <= 1, f"ecran tactile ({nom_t}) : la colonne de boutons est au-dessus de l'icone, qui reste en bas a droite", tc)
                rapport(res["cache"], f"ecran tactile ({nom_t}) : l'icone se cache quand la saisie du chat occupe le bas")
                await pt.close()
            # ---- la carte
            cp = await br.new_page(locale="fr-FR", viewport={"width": 900, "height": 600}); cerrs = []
            cp.on("pageerror", lambda e: cerrs.append(str(e)))
            await cp.goto(base + "carte.html")
            await cp.wait_for_function("document.querySelectorAll('a.tile').length > 0", timeout=20000)
            await cp.wait_for_timeout(500)
            m = await cp.evaluate(INFO.replace("innerWidth", "innerWidth").replace("innerHeight", "innerHeight"))
            rapport(bool(m) and m["href"] == DEPOT and m["target"] == "_blank" and abs(m["w"] - m["h"]) < 0.6 and m["h"] <= 33.5, "carte : l'icone carree mene au depot, dans un nouvel onglet", m and [m["href"], m["target"], m["w"], m["h"]])
            rapport(bool(m) and abs(m["right"] - 12) <= 1 and abs(m["bottom"] - 12) <= 1, "carte : l'icone est tout en bas a droite", m and [m["right"], m["bottom"]])
            await cp.mouse.move(m["left"] + m["w"] / 2, m["top"] + m["h"] / 2); await cp.wait_for_timeout(300)
            m2 = await cp.evaluate(INFO)
            rapport(m2["tipShown"] and "Web_3d" in m2["tip"], "carte : la bulle apparait au survol", m2["tip"])
            rapport(not cerrs, "carte : aucune erreur JavaScript", cerrs[:2])
            await cp.close()
            # carte etroite : le texte du pied de page ne passe pas sous l'icone
            cn = await br.new_page(locale="fr-FR", viewport={"width": 760, "height": 420})
            await cn.goto(base + "carte.html")
            await cn.wait_for_function("document.querySelectorAll('a.tile').length > 0", timeout=20000)
            await cn.wait_for_timeout(500)
            sous = await cn.evaluate("""() => { const c = document.getElementById('credit').getBoundingClientRect(), rg = document.createRange(); rg.selectNodeContents(document.getElementById('foot'));
              return [...rg.getClientRects()].filter(r => r.width > 0 && r.right > c.left - 2 && r.bottom > c.top && r.top < c.bottom).map(r => [Math.round(r.left), Math.round(r.right), Math.round(r.top)]); }""")
            rapport(sous == [], "carte etroite : le texte du pied de page ne passe pas sous l'icone", sous)
            await cn.close()
            # ---- 1.10.13 : sans icone (credit: false dans la config de la page, dans l'en-tete de regions.json pour la carte)
            s2 = tmp / "site2"
            shutil.copytree(site, s2)
            for nom_j in ("region.config.json", "regions.json"):
                dj = json.loads((s2 / nom_j).read_text(encoding="utf-8"))
                dj["credit"] = False
                (s2 / nom_j).write_text(json.dumps(dj), encoding="utf-8")
            proc2, port2 = serveur(s2)
            time.sleep(1.5)
            try:
                b2 = f"http://127.0.0.1:{port2}/"
                pn = await br.new_page(locale="fr-FR", viewport={"width": 1200, "height": 700}); nerrs = []
                pn.on("pageerror", lambda e: nerrs.append(str(e)))
                await pn.goto(b2 + "index.html")
                await pn.wait_for_function("document.getElementById('msg') === null", timeout=90000)
                await pn.wait_for_timeout(1500)
                rapport(await pn.evaluate("!document.getElementById('credit')"), "sans icone : la page n'a pas l'icone (credit: false dans la config)")
                rapport(await pn.evaluate("!!document.getElementById('bar')") and not nerrs, "sans icone : la page s'ouvre sans erreur JavaScript", nerrs[:2])
                await pn.close()
                cs = await br.new_page(locale="fr-FR", viewport={"width": 900, "height": 600}); serrs = []
                cs.on("pageerror", lambda e: serrs.append(str(e)))
                await cs.goto(b2 + "carte.html")
                await cs.wait_for_function("document.querySelectorAll('a.tile').length > 0", timeout=20000)
                await cs.wait_for_timeout(800)
                rapport(await cs.evaluate("!document.getElementById('credit')"), "sans icone : la carte n'a pas l'icone (credit: false dans l'en-tete de regions.json)")
                rapport(await cs.evaluate("!!document.querySelector('#foot a')") and not serrs, "sans icone : le lien du pied de page de la carte reste, sans erreur", serrs[:2])
                await cs.close()
            finally:
                proc2.terminate()
            # options de fabrication : --update, puis --map-page
            s3 = tmp / "site3"
            shutil.copytree(site, s3)
            env_u = dict(os.environ, PYTHONUTF8="1")
            def maj(*opt):
                subprocess.run([sys.executable, str(ROOT / "dist" / "glb2html.py"), "--update", "-o", str(s3 / "region.html"), "--shared-shell", str(s3 / "index.html"), *opt],
                               capture_output=True, text=True, cwd=ROOT, env=env_u)
                return json.loads((s3 / "region.config.json").read_text(encoding="utf-8")).get("credit", "absent")
            rapport(maj() == "absent", "glb2html --update sans option : pas de cle credit")
            rapport(maj("--no-credit") is False, "glb2html --update --no-credit : credit: false dans la config")
            rapport(maj() is False, "glb2html --update sans option : credit: false est garde")
            rapport(maj("--credit") == "absent", "glb2html --update --credit : la cle disparait")
            for opt_c, attendu in (("--no-credit", True), ("--credit", False)):
                mp = tmp / ("map" + opt_c.replace("-", "") + ".html")
                subprocess.run([sys.executable, str(ROOT / "dist" / "glb2html.py"), "--map-page", str(mp), "--map", str(site / "regions.json"), opt_c], capture_output=True, text=True, cwd=ROOT, env=env_u)
                cfg_c = mp.read_text(encoding="utf-8") if mp.exists() else ""
                rapport(mp.exists() and (('"credit":false' in cfg_c.replace(" ", "")) == attendu), f"glb2html --map-page {opt_c} : credit: false " + ("ecrit" if attendu else "absent"))
            await br.close()
    finally:
        proc.terminate()


asyncio.run(main())
print("\nRESULTAT : " + ("tout est passe" if not echecs else f"{echecs} echec(s)"))
sys.exit(1 if echecs else 0)
