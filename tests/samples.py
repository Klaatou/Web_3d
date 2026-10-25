#!/usr/bin/env python3
"""Tests v43 : les fichiers d'exemple de docs/samples/ sont acceptés par le vrai code qui lit chaque fichier
(glb2html.py, glb2tiles.py, presence_server.py, la page exportée, le viewer), pour qu'ils restent justes quand le code change.
Vérifie aussi les anciens noms (avant la v43) : options, profil « perso », repère « portee ».

Prérequis : pip install playwright websockets ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM. Lancer : python tests/samples.py
"""
import asyncio, json, os, runpy, shutil, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37

SAMPLES = ROOT / "docs" / "samples"
FR = json.loads((ROOT / "src" / "i18n" / "fr.json").read_text(encoding="utf-8"))
avant = lambda cle: FR[cle].split("{")[0]
lire = lambda nom: json.loads((SAMPLES / nom).read_text(encoding="utf-8"))

print("--- 0. aucun ancien nom (avant v43 / v44) dans l'aide, les messages et les documents")
import re
ANCIENS = re.compile(r"(?<![\w-])--(maj|tile-max-mo|tile-max-tri|budget-tri|entier-poids|entier-etendue|seuil|seuil-tri|aberrant|bloc|exclure|exclure-max-tri|"
                     r"exclure-max-meshes|sans-references|sans-vue-ensemble|vue-ensemble-seule|ov-budget-tri|ov-seuil|ov-seuil-max|ov-terrain-pas|forcer|sortie|reperes|"
                     r"terrain-seul|outils|verifier|glossaire)(?![\w-])|\btileMaxMo\b|\btileMaxTri\b|\bbudgetMo\b|\bwholeWeightMo\b|\bthresholdMo\b|\?tuiles=|\?rayon=|"
                     r"--terrain (oui|non)\b|--zone-marker (discret|portee|aucun)\b|--profile perso\b|\[maj\]")
EXCEPTION = re.compile(r"avant la v4[34]|before v4[34]|ancien|old value|old name|accept")
trouves = []
for nom in ("src/i18n/fr.json", "src/i18n/en.json"):
    for k, v in json.loads((ROOT / nom).read_text(encoding="utf-8")).items():
        if isinstance(v, str) and ANCIENS.search(v) and not EXCEPTION.search(v):
            trouves.append(nom + " " + k)
for nom in ("REFERENCE_OPTIONS.md", "README.md", "README.fr.md", "CLAUDE.md", "docs/fr/MANUEL.md", "docs/en/MANUAL.md", "docs/fr/PROCEDURES.md", "docs/en/PROCEDURES.md"):
    texte = re.sub(r"### 27\.11.*?(?=\n## |\Z)", "", (ROOT / nom).read_text(encoding="utf-8"), flags=re.S)   # tableau des anciens noms
    for i, ligne in enumerate(texte.splitlines(), 1):
        if ANCIENS.search(ligne) and not EXCEPTION.search(ligne):
            trouves.append(f"{nom} : {ligne[:90]}")
rapport(not trouves, "aide, messages et documents : seulement les nouveaux noms (anciens cités uniquement comme anciens)", trouves[:10])

print("--- 1. les fichiers se lisent")
noms = sorted(p.name for p in SAMPLES.iterdir())
attendus = ["chat_history.sample.jsonl", "default.sample.json", "disposition.sample.json", "presence_bans.sample.json", "presence_creators.sample.json",
            "presence_identities.sample.json", "presence_visits_keys.sample.json", "region.config.sample.json", "region.reglages.sample.json", "region.tiles.sample.json", "region.zones.sample.json",
            "regions.sample.json", "visits.sample.jsonl"]
rapport(noms == attendus, "docs/samples/ contient les 13 exemples", noms)
for n in noms:
    try:
        if n.endswith(".jsonl"):
            [json.loads(l) for l in (SAMPLES / n).read_text(encoding="utf-8").splitlines() if l.strip()]
        else:
            lire(n)
        rapport(True, n + " : JSON valide")
    except ValueError as e:
        rapport(False, n + " : JSON valide", e)

print("--- 2. glb2html.py")
G = runpy.run_path(str(DIST / "glb2html.py"), run_name="samples")
cfg = lire("region.config.sample.json")
ref = G["build_cfg"]("Region.html", tiles="Region.tiles.json", modular=True)
rapport(set(cfg) == set(ref), "config : exactement les clés que glb2html.py écrit (région en tuiles)", (set(cfg) ^ set(ref)))
rapport(all(type(cfg[k]) is type(ref[k]) for k in ref if k in cfg), "config : chaque valeur a le type écrit par glb2html.py",
        [k for k in ref if k in cfg and type(cfg[k]) is not type(ref[k])])
rapport(cfg["zoneMarker"] in G["ZONE_MARKERS"] and cfg["profile"] in ("public", "private"), "config : repère et profil sont des valeurs connues")
zones = lire("region.zones.sample.json")
rapport(G["clean_zones"](zones, "private") == zones, "zones : déjà propres (rien à corriger) avec le profil private")
pub = G["clean_zones"](zones, "public")
rapport(len(pub) == 7 and all(not z["private"] for z in pub), "zones : profil public, la zone privée est retirée", len(pub))
rapport(sorted({z["type"] for z in zones}) == sorted(G["ZONE_TYPES"]), "zones : une zone de chaque sorte", sorted({z["type"] for z in zones}))
rapport(any(z["mesh"] for z in zones) and any(z["showName"] for z in zones) and any(z["confirm"] for z in zones), "zones : liée à un objet, nom affiché, confirmation")
rapport(G["clean_zones"](zones, "perso") == zones, "ancien profil « perso » : compris comme private")
regions = lire("regions.sample.json")
rapport(isinstance(regions, dict) and regions.get("showUrl") is False and G["clean_map"](regions) == regions["regions"], "regions : en-tête showUrl et fiches déjà propres (rien à corriger)")
S = lire("region.reglages.sample.json")
d = G["settings_defaults"](S)
rapport(d.get("sea_y") == 18.5 and d.get("profile") == "private" and d.get("target") == (392.0, 68.0, -373.0) and d.get("zone_marker") == "dot"
        and d.get("target_explicit") is True and d.get("presence_url") == "ws://ADRESSE:8765", "réglages du viewer : relus par --settings", d)
S2 = json.loads(json.dumps(S)); S2["profile"] = "perso"; S2["cfg"]["zoneMarker"] = "portee"
d2 = G["settings_defaults"](S2)
c2 = G["build_cfg"]("R.html", zone_marker=d2["zone_marker"], profile=d2["profile"])
rapport(c2["profile"] == "private" and c2["zoneMarker"] == "range", "anciennes valeurs perso / portee : converties en private / range", (c2["profile"], c2["zoneMarker"]))

print("--- 3. glb2tiles.py : mêmes champs que l'index réel")
gt = tmp / "gt"; gt.mkdir()
shutil.copy(ROOT / "tests" / "data" / "walk3.glb", gt / "Region.glb")
r = run(DIST / "glb2tiles.py", gt / "Region.glb", "--nopause", "--force")
vrai = json.loads((gt / "Region.tiles.json").read_text(encoding="utf-8"))
ti = lire("region.tiles.sample.json")
rapport(set(vrai) <= set(ti) <= set(vrai) | {"excluded"}, "index des tuiles : mêmes champs (plus « excluded »)", set(vrai) ^ set(ti))
rapport(all(set(t) == set(vrai["tiles"][0]) for t in ti["tiles"]), "index des tuiles : chaque tuile a les champs réels")
rapport(set(ti["params"]) == set(vrai["params"]) and set(ti["overview"]) == set(vrai["overview"]) and set(ti["overview"]["params"]) == set(vrai["overview"]["params"]),
        "index des tuiles : réglages et vue d'ensemble ont les champs réels")
r = run(DIST / "glb2tiles.py", gt / "Region.glb", "--nopause", "--forcer", "--sortie", gt / "ancien", "--sans-vue-ensemble")
rapport((gt / "ancien" / "Region.tiles.json").is_file() and not (gt / "ancien" / "Region.overview.glb").exists(), "anciens noms --sortie, --sans-vue-ensemble : acceptés")

print("--- 4. le dossier d'une région fait des exemples")
site = tmp / "site"; site.mkdir()
html("--tiles", gt / "Region.tiles.json", "-o", site / "Region.html", "--shared-shell")
for src_, dst in (("region.config.sample.json", "Region.config.json"), ("region.tiles.sample.json", "Region.tiles.json"), ("region.zones.sample.json", "Region.zones.json"),
                  ("regions.sample.json", "regions.json"), ("default.sample.json", "default.json")):
    shutil.copy(SAMPLES / src_, site / dst)
(site / "Region.tiles").mkdir(exist_ok=True)
for t in ti["tiles"] + [ti["overview"]]:
    shutil.copy(ROOT / "tests" / "data" / "walk3.glb", site / t["file"])
shutil.copy(DIST / "glb-viewer.html", site / "glb-viewer.html")
avant_maj = json.loads((site / "Region.config.json").read_text(encoding="utf-8"))
r = html("--update", "-o", site / "Region.html", "--shared-shell", "--sea-y", "12")
apres = json.loads((site / "Region.config.json").read_text(encoding="utf-8"))
diff = {k for k in set(avant_maj) | set(apres) if avant_maj.get(k) != apres.get(k)}
rapport(diff <= {"seaY", "version"} and apres["seaY"] == 12.0, "--update sur la config d'exemple : seule seaY change", diff)
r = html("--maj", "-o", site / "Region.html", "--shared-shell", "--sea-y", "18.5")
rapport(json.loads((site / "Region.config.json").read_text(encoding="utf-8"))["seaY"] == 18.5, "ancien nom --maj : accepté")

print("--- 5. serveur de présence")
ids, bans, hist = tmp / "ids.json", tmp / "bans.json", tmp / "chat.jsonl"
shutil.copy(SAMPLES / "presence_identities.sample.json", ids)
shutil.copy(SAMPLES / "presence_bans.sample.json", bans)
shutil.copy(SAMPLES / "chat_history.sample.jsonl", hist)
pp, pport = lancer_presence("--identities", ids, "--bans", bans, "--history-file", hist, "--history-days", "0")   # 0 : les messages d'exemple ne deviennent jamais trop anciens
time.sleep(1.0)
pp.kill()
sortie = pp.communicate()[0]
rapport(avant("py.presence.registre_illisible_0_demarrage_a_vide") not in sortie and avant("py.presence.fichier_de_bannissements_illisible_0_ignore") not in sortie,
        "identités et bannissements d'exemple : lus sans erreur", sortie[-600:])
rapport(FR["py.presence.history_loaded"].replace("{0}", "3").replace("{1}", "0").split("(")[0].strip() in sortie, "historique d'exemple : 3 messages relus", sortie[-600:])
idoc = json.loads(ids.read_text(encoding="utf-8"))
rapport(idoc["salt"] == lire("presence_identities.sample.json")["salt"] and set(idoc["names"]) == {"jj", "alice"}, "identités : gardées telles quelles")
rapport(len(json.loads(bans.read_text(encoding="utf-8"))) == 2, "bannissements : gardés (aucun n'est expiré)")
# v48 : journal des visites et clé d'exemple (clé ABCD-EFGH-JKMN, documentée au manuel § 27) ; --visits-days 0 : rien n'est purgé
vis, vkeys = tmp / "visits.jsonl", tmp / "vkeys.json"
shutil.copy(SAMPLES / "visits.sample.jsonl", vis)
shutil.copy(SAMPLES / "presence_visits_keys.sample.json", vkeys)
pp, pport = lancer_presence("--identities", ids, "--bans", bans, "--visits", vis, "--visits-keys", vkeys, "--visits-days", "0", "--visits-names")


async def visites_exemple():
    import websockets
    async with websockets.connect(f"ws://127.0.0.1:{pport}") as ws:
        await ws.send(json.dumps({"t": "visits", "room": "Region", "key": "abcd efgh jkmn"}))
        return json.loads(await ws.recv())
vr = asyncio.run(visites_exemple())
pp.kill()
rapport(vr.get("ok") is True and vr.get("visits") == 3 and vr.get("visitors") == 3 and vr.get("keep") == 0 and vr.get("names") is True,
        "visites d'exemple : clé acceptée, 3 visites (deux lignes de JJ fusionnées), 3 visiteurs", vr)
rapport(sum(d["visits"] for d in vr.get("days", [])) == 3 and sum(d["walked"] for d in vr.get("days", [])) == 1, "visites d'exemple : total par jour, une avec promenade", vr.get("days"))
rapport(len(vis.read_text(encoding="utf-8").splitlines()) == 5, "visites d'exemple : fichier gardé tel quel (5 lignes)")
# v51 : créateurs d'exemple (manuel § 27.12 et § 34) : 3 lus, alice accueillie dans alice.gallery, bob suspendu, hôte sans préfixe
crf = tmp / "creators.json"
shutil.copy(SAMPLES / "presence_creators.sample.json", crf)
pp, pport = lancer_presence("--creators", crf)


async def createurs_exemple():
    import websockets
    out = []
    for origine, salon in (("https://alice.example", "alice.gallery"), ("https://bob.example", "bob.gallery"), ("http://localhost:8000", "Region"), ("https://alice.example", "Region")):
        async with websockets.connect(f"ws://127.0.0.1:{pport}", origin=origine) as ws:
            try:
                await ws.send(json.dumps({"t": "hello", "room": salon, "name": "T", "uid": "0123456789abcdef0123", "spectator": True}))
            except websockets.ConnectionClosed:      # refus : le serveur a déjà répondu et fermé
                pass
            out.append(json.loads(await ws.recv()).get("t"))
    return out
cr = asyncio.run(createurs_exemple())
pp.kill()
sortie = pp.communicate()[0]
rapport(FR["py.presence.cr.loaded"].replace("{0}", "3").split("{")[0] in sortie and "ignor" not in sortie, "créateurs d'exemple : 3 lus, aucune entrée ignorée", sortie[-600:])
rapport(cr == ["welcome", "refused", "welcome", "refused"], "créateurs d'exemple : alice accueillie, bob suspendu, hôte accueilli, alice hors de ses salons refusée", cr)

http, hport = serveur(site)
BASE = f"http://127.0.0.1:{hport}/"


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)

        print("--- 6. la page ouvre la région des exemples")
        ctx = await br.new_context(locale=LOC, viewport={"width": 1000, "height": 700}, accept_downloads=True)
        o = await Onglet(br).ouvrir(BASE + "index.html?region=Region", ctx=ctx)
        await o.attendre("window.__viewer.tilesState().total > 0", 30)
        tot = await o.ev("window.__viewer.tilesState().total")
        ign = [l for l in o.logs if avant("core.tile.ignored") in l]
        rapport(tot == 4 and not ign, "index des tuiles d'exemple : 4 tuiles, aucune ignorée", (tot, ign))
        zs = await o.ev("window.__viewer.getZones().map(z => z.id)")
        rapport(len(zs) == 7 and "light-on" not in zs, "zones d'exemple : 7 affichées, la zone privée retirée (profil public)", zs)
        await o.attendre("!document.getElementById('mapBtn').hidden", 10)
        await o.ev("document.getElementById('mapBtn').click()")
        await o.attendre("document.getElementById('mapGrid').textContent.includes('Other region')", 15)
        rapport(True, "carte des mondes : regions.json d'exemple chargé (mapUrl)")
        await o.ev("document.getElementById('mapClose').click()")
        await o.pg.set_input_files("#layFile", str(SAMPLES / "disposition.sample.json"))
        await o.pg.wait_for_timeout(400)
        par = await o.ev("(() => { const p = document.getElementById('spawnInfo').parentElement; return p === document.body ? 'body' : p.id; })()")
        rapport(await o.txt("toast") == FR["page.layout.loaded"] and par == "body", "disposition d'exemple : chargée (fenêtre Arrivées libre)", (await o.txt("toast"), par))
        rapport(not o.errs, "aucune erreur JavaScript", o.errs)
        await ctx.close()

        print("--- 6 bis. nouveaux noms d'adresse : ?radius= (page), ?tiles= (viewer)")
        o = await Onglet(br).ouvrir(BASE + "index.html?region=Region&radius=33")
        await o.attendre("window.__viewer.tilesState().total > 0", 30)
        rapport(await o.ev("window.__viewer.tilesState().radius") == 33, "?radius=33 : rayon des tuiles pris en compte", await o.ev("window.__viewer.tilesState().radius"))
        await o.ctx.close()
        ctx = await br.new_context(locale=LOC, viewport={"width": 1300, "height": 800})
        pg = await ctx.new_page()
        await pg.goto(BASE + "glb-viewer.html?tiles=Region.tiles.json")
        await pg.wait_for_function("window.__viewer && window.__viewer.tiled && window.__viewer.tilesState().total === 4", timeout=40000)
        rapport(True, "viewer : glb-viewer.html?tiles=… ouvre la région en tuiles")
        await ctx.close()

        print("--- 7. adresse sans ?region= : default.json")
        o = await Onglet(br).ouvrir(BASE)
        rapport(await o.ev("document.title") == "Region", "default.json d'exemple : la région Region s'ouvre", await o.ev("document.title"))
        await o.ctx.close()

        print("--- 8. viewer : réglages d'exemple")
        ctx = await br.new_context(locale=LOC, viewport={"width": 1300, "height": 800})
        pg = await ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto((DIST / "glb-viewer.html").as_uri())
        await pg.wait_for_function("window.__viewer", timeout=20000)
        await pg.set_input_files("#fSettings", str(SAMPLES / "region.reglages.sample.json"))
        await pg.wait_for_timeout(500)
        st = await pg.inner_text("#stat")
        v = await pg.evaluate("[window.__viewer.cfg.seaY, window.__viewer.cfg.zoneMarker, document.getElementById('profileSel').value, window.__viewer.cfg.zones.length]")
        rapport(st.startswith(FR["viewer.set.loadedfrom"].split("{")[0]) and v == [18.5, "dot", "private", 3], "viewer : réglages d'exemple chargés", (st, v))
        S3 = json.loads((SAMPLES / "region.reglages.sample.json").read_text(encoding="utf-8")); S3["profile"] = "perso"; S3["cfg"]["zoneMarker"] = "aucun"
        (tmp / "ancien.reglages.json").write_text(json.dumps(S3), encoding="utf-8")
        await pg.set_input_files("#fSettings", str(tmp / "ancien.reglages.json"))
        await pg.wait_for_timeout(500)
        v = await pg.evaluate("[window.__viewer.cfg.zoneMarker, document.getElementById('profileSel').value, document.getElementById('selZMark') ? document.getElementById('selZMark').value : 'none']")
        rapport(v == ["none", "private", "none"], "viewer : anciennes valeurs aucun / perso converties", v)
        rapport(not errs, "viewer : aucune erreur JavaScript", errs)
        await ctx.close()
        await br.close()


try:
    asyncio.run(main())
finally:
    http.kill()
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
