#!/usr/bin/env python3
"""Test 1.4.6 : glb2tiles.py --compress (compression des tuiles et de la vue d'ensemble par gltfpack).

Toujours : sans gltfpack (ni PATH, ni npx) l'option echoue proprement avant toute ecriture (code non nul, message clair, dossier de sortie vide).
Si gltfpack est disponible (PATH ou npx) : region synthetique (glbfab.region) decoupee en plusieurs tuiles, une fois sans compression (reference),
une fois avec --compress : extensionsUsed contient EXT_meshopt_compression, memes noms de noeuds, memes extras, memes materiaux, nombre de triangles
proche ; X.tiles.json identique octet pour octet (les « bytes » de l'index ne changent pas) ; fichiers plus petits ; relance (--overview-only --compress)
sans effet sur les tuiles (sautees, contenu identique) ; un fichier en erreur n'arrete pas les autres et reste intact ; la page charge la region compressee,
toutes les tuiles pretes, et la ligne « Tuile(s) sous l'avatar » est exacte. Sans gltfpack : « ignore (gltfpack absent) », sortie sans echec.

Prerequis : pip install playwright ; python build.py avant. Variables facultatives : THREE_DIR, CHROMIUM.
Lancer : python tests/compress.py
"""
import asyncio, hashlib, json, os, re, shutil, struct, subprocess, sys

from h37 import DIST, html, rapport, resultat, serveur, tmp
import glbfab


def lire_glb(chemin):
    d = open(chemin, "rb").read()
    n = struct.unpack("<I", d[12:16])[0]
    return json.loads(d[20:20 + n].decode("utf-8"))


def tri(g):
    """triangles des primitives de chaque mesh, comptes une fois par mesh (indices / 3), sans tenir compte des instances"""
    t = 0
    for m in g.get("meshes", []):
        for p in m.get("primitives", []):
            if "indices" in p:
                t += g["accessors"][p["indices"]]["count"] // 3
            else:
                t += g["accessors"][p["attributes"]["POSITION"]]["count"] // 3
    return t


def sha(chemin):
    return hashlib.sha256(open(chemin, "rb").read()).hexdigest()


def tuiler(src_glb, sortie, *extra, env=None, ok_code=0):
    sortie.mkdir(exist_ok=True)
    r = subprocess.run([sys.executable, str(DIST / "glb2tiles.py"), str(src_glb), "--force", "--nopause", "--budget-triangles", "3000", "--min", "64", "--output", str(sortie), *extra],
                       capture_output=True, text=True, env=env, cwd=tmp, encoding="utf-8")
    return r


def gltfpack_dispo():
    g = shutil.which("gltfpack")
    cmd = [g] if g else ([shutil.which("npx"), "-y", "gltfpack"] if shutil.which("npx") else None)
    if not cmd:
        return False
    try:
        r = subprocess.run(cmd + ["-h"], capture_output=True, text=True, timeout=180)
        return "gltfpack" in (r.stdout + r.stderr).lower()
    except Exception:
        return False


src = tmp / "src"
src.mkdir()
glbfab.region(src / "Reg.glb", maisons=24, instances=40, petits=12)
env_fr = dict(os.environ, WEB3D_LANG="fr")

# ---- 1. gltfpack absent : echec propre, rien d'ecrit
vide = tmp / "pasdetool"
vide.mkdir()
sortie_a = tmp / "sortie_absent"
r = tuiler(src / "Reg.glb", sortie_a, "--compress", env=dict(env_fr, PATH=str(vide)))
rapport(r.returncode != 0, "gltfpack absent : code de sortie non nul", r.returncode)
rapport("gltfpack est introuvable" in (r.stdout + r.stderr) and "rien n'a été modifié" in (r.stdout + r.stderr), "gltfpack absent : message clair", (r.stdout + r.stderr)[-300:])
rapport(not any(sortie_a.iterdir()), "gltfpack absent : aucun fichier ecrit", [p.name for p in sortie_a.iterdir()])

if not gltfpack_dispo():
    print("ignore (gltfpack absent) : la partie compression n'a pas ete essayee")
    bad = resultat()
    print()
    print("RESULTAT : " + ("tout est passe (partie compression ignoree)" if not bad else f"ECHEC ({bad})"))
    sys.exit(1 if bad else 0)

# ---- 2. reference et compression
ref, cmp_ = tmp / "ref", tmp / "cmp"
r0 = tuiler(src / "Reg.glb", ref)
r1 = tuiler(src / "Reg.glb", cmp_, "--compress", env=env_fr)
rapport(r0.returncode == 0 and r1.returncode == 0, "reference et --compress : code 0", (r0.returncode, r1.returncode, (r1.stdout + r1.stderr)[-400:]))
idx_ref, idx_cmp = json.loads((ref / "Reg.tiles.json").read_text(encoding="utf-8")), json.loads((cmp_ / "Reg.tiles.json").read_text(encoding="utf-8"))
fichiers = [f["file"] for f in idx_cmp["tiles"]] + ["Reg.overview.glb"]
rapport(len(idx_cmp["tiles"]) >= 3, "la region est decoupee en plusieurs tuiles", len(idx_cmp["tiles"]))
rapport((ref / "Reg.tiles.json").read_text(encoding="utf-8").replace(str(ref), "") == (cmp_ / "Reg.tiles.json").read_text(encoding="utf-8").replace(str(cmp_), ""),
        "X.tiles.json identique (les « bytes » de l'index ne changent pas, aucun champ ajoute)")
ok_ext, ok_noms, ok_extras, ok_mat, ok_tri, plus_petits, details = True, True, True, True, True, True, []
for f in fichiers:
    a, b = lire_glb(ref / f), lire_glb(cmp_ / f)
    if "EXT_meshopt_compression" not in b.get("extensionsUsed", []):
        ok_ext = False
        details.append(("ext", f))
    na = {n.get("name") for n in a["nodes"] if n.get("name")}
    nb = {n.get("name") for n in b["nodes"] if n.get("name")}
    if not na <= nb:
        ok_noms = False
        details.append(("noms", f, sorted(na - nb)[:3]))
    ea = {n["name"]: n["extras"] for n in a["nodes"] if n.get("name") and n.get("extras")}
    eb = {n["name"]: n["extras"] for n in b["nodes"] if n.get("name") and n.get("extras")}
    if ea != eb:
        ok_extras = False
        details.append(("extras", f, len(ea), len(eb)))
    if len(a.get("materials", [])) != len(b.get("materials", [])):
        ok_mat = False
        details.append(("materiaux", f, len(a.get("materials", [])), len(b.get("materials", []))))
    ta, tb = tri(a), tri(b)
    if not (ta * 0.9 <= tb <= ta * 1.05):
        ok_tri = False
        details.append(("triangles", f, ta, tb))
    if (cmp_ / f).stat().st_size >= (ref / f).stat().st_size:
        plus_petits = False
        details.append(("taille", f, (ref / f).stat().st_size, (cmp_ / f).stat().st_size))
rapport(ok_ext, "chaque tuile et la vue d'ensemble declarent EXT_meshopt_compression", details)
rapport(ok_noms, "memes noms de noeuds (gltfpack peut en ajouter des sans nom)", details)
rapport(ok_extras, "memes extras (-ke)", details)
rapport(ok_mat, "memes materiaux (-km)", details)
rapport(ok_tri, "nombre de triangles proche (les degeneres sont retires)", details)
rapport(plus_petits, "chaque fichier est plus petit", details)
rapport(not list(cmp_.rglob("*gltfpack-tmp*")), "aucun fichier temporaire laisse")
n_ext_ref = sum("EXT_meshopt_compression" in lire_glb(ref / f).get("extensionsUsed", []) for f in fichiers)
rapport(n_ext_ref == 0, "temoin : la reference (sans --compress) n'est pas compressee", n_ext_ref)

# ---- 3. relance : tuiles sautees, contenu inchange
avant = {f: sha(cmp_ / f) for f in [t["file"] for t in idx_cmp["tiles"]]}
r2 = tuiler(src / "Reg.glb", cmp_, "--overview-only", "--compress", env=env_fr)
apres = {f: sha(cmp_ / f) for f in avant}
rapport(r2.returncode == 0 and avant == apres, "relance (--overview-only --compress) : les tuiles ne changent pas", (r2.returncode, (r2.stdout + r2.stderr)[-300:]))
rapport(r2.stdout.count("déjà compressé") == len(avant), "relance : chaque tuile est sautee avec un message", (r2.stdout.count("déjà compressé"), len(avant)))
rapport("EXT_meshopt_compression" in lire_glb(cmp_ / "Reg.overview.glb").get("extensionsUsed", []), "relance : la vue d'ensemble regeneree est recompressee")

# ---- 4. une erreur n'abandonne pas les autres et laisse l'original intact
cas = tmp / "cas_erreur"
tuiler(src / "Reg.glb", cas)
idx = json.loads((cas / "Reg.tiles.json").read_text(encoding="utf-8"))
casse = cas / idx["tiles"][0]["file"]
casse.write_bytes(b"glTF" + b"\x02\x00\x00\x00" + b"\x10\x00\x00\x00" + b"\x00" * 8)   # en-tete GLB tronque
octets_casse = casse.read_bytes()
r3 = tuiler(src / "Reg.glb", cas, "--overview-only", "--compress", env=env_fr)
rapport(r3.returncode != 0, "fichier en erreur : code de sortie non nul", r3.returncode)
rapport(casse.read_bytes() == octets_casse, "fichier en erreur : original intact")
suite = [lire_glb(cas / t["file"]) for t in idx["tiles"][1:]]
rapport(all("EXT_meshopt_compression" in g.get("extensionsUsed", []) for g in suite), "les autres tuiles sont quand meme compressees", [g.get("extensionsUsed") for g in suite][:2])

# ---- 5. la page charge la region compressee
site = tmp / "site"
site.mkdir()
shutil.copy(cmp_ / "Reg.tiles.json", site / "Reg.tiles.json")
shutil.copy(cmp_ / "Reg.overview.glb", site / "Reg.overview.glb")
shutil.copytree(cmp_ / "Reg.tiles", site / "Reg.tiles")
html("-o", site / "Reg.html", "--shared-shell", "--tiles", site / "Reg.tiles.json", "--rotate", "0", "--tile-radius", "5000")
ext = idx_cmp["extent"]
cx, cz = (ext["min"][0] + ext["max"][0]) / 2, (ext["min"][2] + ext["max"][2]) / 2


def attendu(x, z):
    m = 0.5
    return sorted(t["file"].split("/")[-1] for t in idx_cmp["tiles"] if t["min"][0] - m <= x <= t["max"][0] + m and t["min"][2] - m <= z <= t["max"][2] + m)


async def page():
    from playwright.async_api import async_playwright
    errs = []
    async with async_playwright() as p:
        kw = dict(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        if os.environ.get("CHROMIUM"):
            kw["executable_path"] = os.environ["CHROMIUM"]
        br = await p.chromium.launch(**kw)
        proc, port = serveur(site)
        try:
            ctx = await br.new_context(locale="fr-FR", viewport={"width": 700, "height": 500})
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append(m.text + " " + (m.location or {}).get("url", "")) if m.type == "error" else None)
            await pg.goto(f"http://127.0.0.1:{port}/index.html?region=Reg#pos={cx},60,{cz},0&name=Test")
            await pg.wait_for_function("document.getElementById('msg') === null", timeout=90000)
            await pg.wait_for_function("window.__viewer.tilesState().loaded === window.__viewer.tilesState().total && window.__viewer.tilesState().total > 0", timeout=120000)
            st = await pg.evaluate("(() => { const s = window.__viewer.tilesState(); return { loaded: s.loaded, total: s.total, failed: s.failed, ov: s.overview && s.overview.state }; })()")
            rapport(st["loaded"] == st["total"] and st["failed"] == 0, "la page charge la region compressee : toutes les tuiles pretes, aucune en echec", st)
            await pg.wait_for_function("window.__viewer.walking", timeout=30000)
            await pg.wait_for_timeout(600)
            r = await pg.evaluate("() => { const v = window.__viewer; return { pos: v.getWalk().pos, here: v.tilesState().here || [], ligne: document.getElementById('tilesInfo').textContent }; }")
            exp = attendu(r["pos"][0], r["pos"][2])
            rapport(bool(r["here"]) and r["here"] == exp and ("sous l'avatar : " + ", ".join(r["here"])) in r["ligne"], "la ligne « Tuile(s) sous l'avatar » est exacte", (r, exp))
            rapport("Mo" in r["ligne"], "la ligne donne un poids", r["ligne"])
            # les 404 de fichiers facultatifs absents (favicon.ico, NOM.about.*.txt, aide.html) sont journalises par le navigateur : voulus
            errs = [e for e in errs if not re.search(r"404.*(favicon\.ico|aide\.html|\.about(\.[a-z]{2,3})?\.txt)$", e)]
            rapport(not errs, "aucune erreur JavaScript ni de console", errs[:3])
        finally:
            proc.kill()
            await br.close()


asyncio.run(page())
bad = resultat()
print()
print("RESULTAT : " + ("tout est passe" if not bad else f"ECHEC ({bad})"))
sys.exit(1 if bad else 0)
