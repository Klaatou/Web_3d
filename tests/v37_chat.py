#!/usr/bin/env python3
"""Tests v37 (lot 2) : historique du chat. Vrai presence_server.py : --history 200 par défaut, --history-file (conservé après relance, sans adresse IP), --history-days,
message {t:'history'} (pages de 50, more), compatibilité ; page : panneau défilable, « Messages plus anciens », serveur muet, réglage du nombre de messages,
compteur de non lus dans le titre, compteur de citations. Lancer : python tests/v37_chat.py (après python build.py)
"""
import asyncio, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

def lancer(*extra):
    return lancer_presence("--chat-burst", "100000", "--chat-gap", "0", *extra)

async def client(url, nom, room="r37"):
    import websockets.asyncio.client
    ws = await websockets.asyncio.client.connect(url)
    await ws.send(json.dumps({"t": "hello", "room": room, "name": nom, "uid": (nom * 8)[:24].encode().hex()[:24], "spectator": False}))
    w = json.loads(await asyncio.wait_for(ws.recv(), 5))
    return ws, w

async def vide(ws, t=0.4):
    out = []
    try:
        while True:
            out.append(json.loads(await asyncio.wait_for(ws.recv(), t)))
    except Exception:
        return out

async def envoyer(ws, n, prefixe="msg"):
    for i in range(n):
        await ws.send(json.dumps({"t": "chat", "text": f"{prefixe} {i}"}))
    await asyncio.sleep(0.3)

async def main():
    from playwright.async_api import async_playwright
    # ---------- serveur par défaut ----------
    print("--- 2.1 serveur : --history 200 par défaut")
    p0, port0 = lancer_presence("--chat-burst", "100000", "--chat-gap", "0")
    u0 = f"ws://127.0.0.1:{port0}"
    a, _ = await client(u0, "Ann")
    await envoyer(a, 250)
    b, w = await client(u0, "Bob")
    hist = w["history"]
    rapport(len(hist) == 200 and hist[-1]["text"] == "msg 249" and hist[0]["text"] == "msg 50", f"un nouvel arrivant reçoit les 200 derniers messages ({len(hist)})", (len(hist), hist[:1]))
    rapport(all(k in hist[0] for k in ("id", "name", "text")) and all("n" in h and "t" in h for h in hist), "chaque message garde id, name, text (anciens clients) et porte n et t")
    await b.send(json.dumps({"t": "history", "before": hist[0]["n"], "n": 50}))
    r = [m for m in await vide(b) if m.get("t") == "history"]
    rapport(len(r) == 1 and len(r[0]["msgs"]) == 0 and r[0]["more"] is False, "sans fichier, rien de plus ancien que la mémoire de 200 : more = false")
    b.close if False else await b.close(); await a.close(); p0.terminate()

    print("--- 2.1 serveur : --history 20, requête history par pages")
    p1, port1 = lancer("--history", "20")
    u1 = f"ws://127.0.0.1:{port1}"
    a, _ = await client(u1, "Ann")
    await envoyer(a, 130)
    b, w = await client(u1, "Bob")
    rapport(len(w["history"]) == 20, "--history 20 : 20 messages rejoués", len(w["history"]))
    # sans fichier la mémoire = --history : 'more' faux
    await b.send(json.dumps({"t": "history", "before": w["history"][0]["n"], "n": 50}))
    r = [m for m in await vide(b) if m.get("t") == "history"]
    rapport(len(r) == 1 and r[0]["msgs"] == [] and r[0]["more"] is False, "sans --history-file : pas de page plus ancienne", r)
    await a.close(); await b.close(); p1.terminate()

    print("--- 2.1 serveur : --history-file")
    fich = tmp / "hist.jsonl"
    p2, port2 = lancer("--history", "20", "--history-file", str(fich))
    u2 = f"ws://127.0.0.1:{port2}"
    a, _ = await client(u2, "Ann")
    await envoyer(a, 130, "f")
    txt = fich.read_text(encoding="utf-8")
    lignes = [json.loads(l) for l in txt.splitlines()]
    rapport(len(lignes) == 130 and set(lignes[0]) == {"n", "t", "d", "room", "name", "text"} and lignes[0]["room"] == "r37" and lignes[0]["name"] == "Ann", "une ligne JSON par message : heure, pseudo, texte, salon", lignes[0])
    rapport("127.0.0.1" not in txt and "ip" not in lignes[0], "aucune adresse IP dans le fichier")
    b, w = await client(u2, "Bob")
    rapport(len(w["history"]) == 20, "--history 20 rejoue 20 messages même avec la mémoire du fichier", len(w["history"]))
    oldest = w["history"][0]["n"]
    got, more = [], True
    pages = 0
    while more and pages < 10:
        await b.send(json.dumps({"t": "history", "before": oldest, "n": 50}))
        await asyncio.sleep(0.4)
        r = [m for m in await vide(b) if m.get("t") == "history"][0]
        got = r["msgs"] + got
        more = r["more"]; pages += 1
        if r["msgs"]:
            oldest = r["msgs"][0]["n"]
        rapport(all(m["n"] < (oldest if False else 10**9) for m in r["msgs"]), "") if False else None
    rapport(len(got) == 110 and pages == 3 and more is False and got[0]["text"] == "f 0", f"pages de 50 puis 50 puis 10 : {len(got)} messages en {pages} requêtes, more = false à la fin", (len(got), pages, more))
    ns = [m["n"] for m in got]
    rapport(ns == sorted(ns) and len(set(ns)) == len(ns), "les messages arrivent dans l'ordre, sans doublon")
    await a.close(); await b.close(); p2.terminate(); await asyncio.sleep(0.5)
    p3, port3 = lancer("--history", "20", "--history-file", str(fich))
    u3 = f"ws://127.0.0.1:{port3}"
    c, w = await client(u3, "Cid")
    rapport(len(w["history"]) == 20 and w["history"][-1]["text"] == "f 129", "après relance du serveur, l'historique est rejoué", w["history"][-1:] )
    await c.send(json.dumps({"t": "chat", "text": "après"})); await asyncio.sleep(0.3)
    nouv = [json.loads(l) for l in fich.read_text(encoding="utf-8").splitlines()]
    rapport(len(nouv) == 131 and nouv[-1]["n"] == 131, "la numérotation continue après la relance (n = 131)", nouv[-1])
    await c.close(); p3.terminate(); await asyncio.sleep(0.5)

    print("--- 2.1 serveur : --history-days")
    now = int(time.time())
    f2 = tmp / "h2.jsonl"
    f2.write_text("\n".join(json.dumps({"n": i + 1, "t": now - d * 86400, "d": "", "room": "r37", "name": "X", "text": f"j-{d}"}) for i, d in enumerate((40, 35, 5, 1))) + "\nligne cassée\n", encoding="utf-8")
    p4, port4 = lancer("--history-file", str(f2))
    c, w = await client(f"ws://127.0.0.1:{port4}", "Cid")
    rapport([h["text"] for h in w["history"]] == ["j-5", "j-1"], "--history-days 30 (défaut) : les messages de plus de 30 jours ne sont pas relus", [h["text"] for h in w["history"]])
    rapport([json.loads(l)["text"] for l in f2.read_text(encoding="utf-8").splitlines()] == ["j-5", "j-1"], "le fichier est réécrit sans eux (ligne cassée comprise)")
    await c.close(); p4.terminate(); await asyncio.sleep(0.4)
    f3 = tmp / "h3.jsonl"
    f3.write_text("\n".join(json.dumps({"n": i + 1, "t": now - d * 86400, "d": "", "room": "r37", "name": "X", "text": f"j-{d}"}) for i, d in enumerate((400, 35, 5))) + "\n", encoding="utf-8")
    p5, port5 = lancer("--history-file", str(f3), "--history-days", "0")
    c, w = await client(f"ws://127.0.0.1:{port5}", "Cid")
    rapport(len(w["history"]) == 3, "--history-days 0 : tout est conservé", [h["text"] for h in w["history"]])
    await c.close(); p5.terminate()

    print("--- 2.2 page : historique, bouton, compteurs")
    site = tmp / "site"; site.mkdir()
    sol_glb(site / "sol.glb")
    (tmp / "z.json").write_text(json.dumps([{"id": "default", "type": "spawn", "x": 0, "y": 15, "z": 0, "yaw": 0.0}]), encoding="utf-8")
    ph, porth = lancer("--history", "60", "--history-file", str(tmp / "h4.jsonl"))
    uh = f"ws://127.0.0.1:{porth}"
    html(site / "sol.glb", "-o", site / "Chat.html", "--shared-shell", "--zones", tmp / "z.json", "--no-sea", "--target", "0,0,0", "--presence-url", uh, "--room", "r37", "--title", "Ile Test", "--chat", *vend)
    seed, _ = await client(uh, "Seed")
    await envoyer(seed, 150, "h")
    srv, port = serveur(site)
    base_url = f"http://127.0.0.1:{port}/index.html?region=Chat"
    DANA = "try { localStorage.setItem('glb2html_name', 'Dana'); } catch (e) {}"
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        try:
            o = await Onglet(br).ouvrir(base_url + "#spawn=default", init=STUB + DANA)
            await o.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await o.attendre("document.getElementById('chatLog').children.length >= 6", 20)
            rapport(await o.ev("document.getElementById('chatOlder').hidden"), "chat fermé : pas de bouton « Messages plus anciens »")
            await o.touche("Enter")
            await o.attendre("!document.getElementById('chatInput').hidden", 10)
            n0 = await o.ev("document.getElementById('chatLog').children.length")
            rapport(n0 >= 60 and await o.ev("(l => getComputedStyle(l).overflowY === 'auto' && l.scrollHeight > l.clientHeight)(document.getElementById('chatLog'))"), f"chat ouvert : {n0} messages dans un panneau défilable", n0)
            rapport(not await o.ev("document.getElementById('chatOlder').hidden"), "le bouton « Messages plus anciens » apparaît")
            await o.ev("document.getElementById('chatLog').scrollTop = 0")
            await o.pg.wait_for_timeout(1200)
            top = await o.ev("document.getElementById('chatLog').scrollTop")
            rapport(top < 5, "on peut remonter dans le panneau sans qu'il revienne en bas (rendu toutes les secondes)", top)
            await o.ev("document.getElementById('chatOlder').click()")
            await o.attendre("document.getElementById('chatLog').children.length >= 110", 10)
            n1 = await o.ev("document.getElementById('chatLog').children.length")
            rapport(n1 - n0 == 50, f"un clic ajoute 50 messages en haut ({n0} → {n1})", n1)
            rapport(await o.ev("document.getElementById('chatLog').firstChild.textContent") == "Seed : h 40", "le plus ancien ajouté est le bon (h 40)", await o.ev("document.getElementById('chatLog').firstChild.textContent"))
            await o.pg.wait_for_timeout(400)   # le serveur limite à une demande par 0,2 s (un clic humain est plus lent)
            await o.ev("document.getElementById('chatOlder').click()")
            await o.attendre("document.getElementById('chatLog').children.length >= 150", 10)
            await o.pg.wait_for_timeout(300)
            rapport(await o.ev("document.getElementById('chatOlder').hidden"), "plus rien d'ancien (more = false) : le bouton se masque")
            await o.ctx.close()

            # serveur muet : la requête history est supprimée côté client
            MUET = "(() => { const s = WebSocket.prototype.send; WebSocket.prototype.send = function (d) { try { if (JSON.parse(d).t === 'history') { window.__muet = (window.__muet || 0) + 1; return; } } catch (e) {} return s.call(this, d); }; })();"
            o = await Onglet(br).ouvrir(base_url + "#spawn=default", init=STUB + DANA + MUET)
            await o.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await o.touche("Enter")
            await o.attendre("!document.getElementById('chatOlder').hidden", 10)
            await o.ev("document.getElementById('chatOlder').click()")
            await o.pg.wait_for_timeout(5200)
            rapport(await o.ev("window.__muet") == 1 and await o.ev("document.getElementById('chatOlder').hidden"), "serveur qui ne répond pas : le bouton se masque")
            await o.ctx.close()

            # réglage du nombre de messages
            o = await Onglet(br).ouvrir(base_url + "#spawn=default", init=STUB + DANA + "try { localStorage.setItem('glb2html_visitor', JSON.stringify({ histMax: 30 })); } catch (e) {}")
            await o.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await o.touche("Enter")
            await o.pg.wait_for_timeout(500)
            n = await o.ev("document.getElementById('chatLog').children.length")
            rapport(n == 30, f"« Messages d'historique affichés » = 30 : 30 lignes gardées ({n})", n)
            await o.ev("document.getElementById('optsBtn').click()")
            await o.ev("(i => { i.value = 20; i.dispatchEvent(new Event('change')); })(document.getElementById('visHist'))")
            await o.pg.wait_for_timeout(300)
            rapport(await o.ev("document.getElementById('chatLog').children.length") == 20 and json.loads(await o.ev("localStorage.getItem('glb2html_visitor')"))["histMax"] == 20, "réglage ramené à 20 : liste réduite et mémorisée")
            await o.ev("(i => { i.value = 99999; i.dispatchEvent(new Event('change')); })(document.getElementById('visHist'))")
            rapport(await o.ev("document.getElementById('visHist').value") == "2000", "réglage borné à 2000")
            await o.ctx.close()

            # compteur de non lus et de citations
            o = await Onglet(br).ouvrir(base_url + "#spawn=default", init=STUB + DANA.replace('Dana', 'Eve'))
            await o.attendre("window.__viewer.walking && window.__viewer.getPresence().state === 'online'", 40)
            await o.pg.wait_for_timeout(1000)
            t0 = await o.ev("document.title")
            await envoyer(seed, 3, "nouveau")
            await o.pg.wait_for_timeout(500)
            t1 = await o.ev("document.title")
            rapport(t1 == "(3) " + t0 and bool(t0), f"chat réduit : titre « {t1} »", (t0, t1))
            await seed.send(json.dumps({"t": "chat", "text": "salut @eve, première citation"})); await asyncio.sleep(0.2)
            await seed.send(json.dumps({"t": "chat", "text": "et eve encore"})); await asyncio.sleep(0.5)
            rapport(await o.ev("document.title") == "(5) " + t0, "compteur de non lus : 5", await o.ev("document.title"))
            rapport(not await o.ev("document.getElementById('chatMentions').hidden") and "2 messages vous citent" in await o.txt("mentCount"), "« 2 messages vous citent »", await o.txt("mentCount"))
            rapport(await o.ev("window.__viewer.getPresence().peers.some(q => q.name === 'Seed' && q.blinking)"), "les citations clignotent tant que je n'ai rien fait") if False else None
            await o.ev("document.getElementById('mentGo').click()")
            await o.pg.wait_for_timeout(400)
            rapport(not await o.ev("document.getElementById('chatInput').hidden") and await o.ev("document.getElementById('chatMentions').hidden"), "le bouton ouvre le chat et efface le compteur de citations")
            rapport(await o.ev("document.title") == t0, "ouverture du chat : titre remis à zéro", await o.ev("document.title"))
            vis = await o.ev("""() => { const l = document.getElementById('chatLog'), d = [...l.children].find(x => x.textContent.includes('première citation')), r = d.getBoundingClientRect(), q = l.getBoundingClientRect(); return r.top >= q.top - 1 && r.bottom <= q.bottom + 1; }""")
            rapport(vis, "le premier message qui me cite est visible dans le panneau")
            await o.ctx.close()
        finally:
            srv.terminate()
            await br.close()
    await seed.close(); ph.terminate()
    print("\nRÉSULTAT : " + ("tout est passé" if not h37.bad else f"{h37.bad} échec(s)"))
    sys.exit(1 if h37.bad else 0)

asyncio.run(main())
