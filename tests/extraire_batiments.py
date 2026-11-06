#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extraire_batiments.py (hors navigateur) : OAR et GLB synthetiques, outil lance depuis tools/ (sources) et depuis dist/ (fabrique).

Verifie : aide fr/en ; --list (boite reperee, voisin apparie par nom) ; cache cree dans le dossier COURANT (jamais a cote du script) et relu ;
extraction d'un groupe (fichiers .glb et .json, recentrage, sol d'essai) ; --fusionner ; --tools et WEB3D_TOOLS ; message clair sans les outils voisins.
Lancer : python build.py puis python tests/extraire_batiments.py
"""
import io, json, os, pathlib, re, shutil, struct, subprocess, sys, tarfile, tempfile, uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST, TOOLS = ROOT / "dist", ROOT / "tools"
ACC = re.compile(r"[éèêëàâùûôîïçœÉÈÀÙÎÔ]")
bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)[:500]), flush=True)


def U():
    return str(uuid.uuid4())


def vec(t, a, k="XYZ"):
    return f"<{t}>" + "".join(f"<{c}>{x}</{c}>" for c, x in zip(k, a)) + f"</{t}>"


def part_xml(pid, name, gpos, off, scale):
    return (f"<SceneObjectPart><UUID><Guid>{pid}</Guid></UUID><Name>{name}</Name>{vec('GroupPosition', gpos)}{vec('OffsetPosition', off)}"
            f"{vec('RotationOffset', [0, 0, 0, 1], 'XYZW')}{vec('Scale', scale)}<Shape><SculptType>0</SculptType></Shape></SceneObjectPart>")


def group_xml(parts):
    return "<SceneObjectGroup><RootPart>" + parts[0] + "</RootPart><OtherParts>" + "".join(parts[1:]) + "</OtherParts></SceneObjectGroup>"


# groupes (OpenSim : x, y, z haut) : maison de 3 parties, sa boite de livraison (cube 1,2 m), un panneau seul
GROUPES = [
    ("Maison Test", [(U(), (100.0, 100.0, 25.0), (0, 0, 0), (10, 8, 4)), (U(), (100.0, 100.0, 25.0), (3, 0, 2), (2, 2, 2)), (U(), (100.0, 100.0, 25.0), (-3, 0, 2), (2, 2, 2))]),
    ("Maison Test - RAKis Freebies", [(U(), (110.0, 100.0, 25.0), (0, 0, 0), (1.2, 1.2, 1.2))]),
    ("Panneau", [(U(), (50.0, 50.0, 25.0), (0, 0, 0), (1, 1, 1))]),
]


def faire_oar(chemin):
    with tarfile.open(chemin, "w:gz") as t:
        def add(nom, data):
            ti = tarfile.TarInfo(nom)
            ti.size = len(data)
            t.addfile(ti, io.BytesIO(data))
        add("archive.xml", b"<archive><region_info><size_in_meters>256,256</size_in_meters></region_info></archive>")
        for i, (nom, parts) in enumerate(GROUPES):
            add(f"objects/g{i}.xml", ("<?xml version=\"1.0\" encoding=\"utf-8\"?>" + group_xml([part_xml(p[0], nom if k == 0 else f"{nom} {k}", p[1], p[2], p[3])
                                                                                                for k, p in enumerate(parts)])).encode())
        add("terrains/heightmap.r32", struct.pack("<%df" % (256 * 256), *([20.0] * (256 * 256))))


def faire_glb(chemin):
    blob, views, accs, meshes, nodes = bytearray(), [], [], [], []
    idx = [0, 1, 3, 0, 3, 2, 4, 6, 7, 4, 7, 5, 0, 4, 5, 0, 5, 1, 2, 3, 7, 2, 7, 6, 0, 2, 6, 0, 6, 4, 1, 5, 7, 1, 7, 3]

    def add(data, target, kind, count, mm=None, comp=5126):
        views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data), "target": target})
        blob.extend(data + b"\0" * (-len(data) % 4))
        a = {"bufferView": len(views) - 1, "componentType": comp, "count": count, "type": kind}
        if mm:
            a["min"], a["max"] = mm
        accs.append(a)
        return len(accs) - 1

    def mesh(nom, s):
        h = [x / 2 for x in s]
        v = [(x, y, z) for x in (-h[0], h[0]) for y in (-h[1], h[1]) for z in (-h[2], h[2])]
        g = [(p[0], p[2], -p[1]) for p in v]                       # OpenSim -> glTF
        n = [(0.0, 1.0, 0.0)] * 8
        pa = add(b"".join(struct.pack("<3f", *p) for p in g), 34962, "VEC3", 8, ([min(p[k] for p in g) for k in range(3)], [max(p[k] for p in g) for k in range(3)]))
        na = add(b"".join(struct.pack("<3f", *p) for p in n), 34962, "VEC3", 8)
        ia = add(struct.pack("<36H", *idx), 34963, "SCALAR", 36, comp=5123)
        meshes.append({"name": nom, "primitives": [{"attributes": {"POSITION": pa, "NORMAL": na}, "indices": ia, "material": 0}]})
        return len(meshes) - 1

    def noeud(nom, pos, m, pid, enfants=None):
        n = {"name": nom, "translation": [pos[0], pos[2], -pos[1]], "mesh": m, "extras": {"uuid": pid}}
        if enfants:
            n["children"] = enfants
        nodes.append(n)
        return len(nodes) - 1
    racines = []
    for nom, parts in GROUPES:
        kids = []
        for k, p in enumerate(parts[1:], 1):
            kids.append(noeud(f"{nom} {k}", p[2], mesh(f"{nom} {k}", p[3]), p[0]))
        r = parts[0]
        racines.append(noeud(nom, r[1], mesh(nom, r[3]), r[0], kids))
    js = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": racines}], "nodes": nodes, "meshes": meshes,
          "materials": [{"name": "m", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1]}}], "accessors": accs, "bufferViews": views, "buffers": [{"byteLength": len(blob)}]}
    jb = json.dumps(js, separators=(",", ":")).encode()
    jb += b" " * (-len(jb) % 4)
    total = 12 + 8 + len(jb) + 8 + len(blob)
    chemin.write_bytes(struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<II", len(jb), 0x4E4F534A) + jb + struct.pack("<II", len(blob), 0x004E4942) + bytes(blob))


def lire_glb(chemin):
    d = pathlib.Path(chemin).read_bytes()
    ln = struct.unpack_from("<I", d, 12)[0]
    return json.loads(d[20:20 + ln])


def lance(script, *args, cwd, env=None):
    e = dict(os.environ)
    for v in ("WEB3D_LANG", "WEB3D_TOOLS", "LC_ALL", "LC_MESSAGES", "LANGUAGE"):
        e.pop(v, None)
    e["LANG"], e["PYTHONIOENCODING"] = "C", "utf-8"
    e.update(env or {})
    r = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, encoding="utf-8", cwd=str(cwd), env=e, stdin=subprocess.DEVNULL, timeout=250)
    return r.returncode, r.stdout + r.stderr


tmp = pathlib.Path(tempfile.mkdtemp(prefix="extraire_"))
oar, glb = tmp / "Essai.oar", tmp / "Essai.glb"
faire_oar(oar)
faire_glb(glb)
def contenu(d):
    return sorted(p.name for p in d.iterdir() if p.name != "__pycache__") if d.is_dir() else []   # __pycache__ : ignore par git, ecrit par les import


avant_dist = contenu(DIST)

for nom_env, script in (("sources tools/", TOOLS / "extraire_batiments.py"), ("dist/", DIST / "extraire_batiments.py")):
    if not script.is_file():
        rapport(False, f"{nom_env} : {script.name} introuvable (python build.py d'abord)")
        continue
    w = tmp / ("w_" + nom_env.strip("/").replace("/", "_"))
    w.mkdir()
    # aide
    c, en = lance(script, "--lang", "en", "--help", cwd=w)
    c2, fr = lance(script, "--lang", "fr", "--help", cwd=w)
    rapport(c == 0 and "--tools" in en and "--lang" in en and "--group" in en and not ACC.search(en), f"{nom_env} aide anglaise, sans lettre accentuee francaise", [l for l in en.splitlines() if ACC.search(l)][:3])
    rapport(c2 == 0 and ACC.search(fr) and "py." not in fr and "py." not in en, f"{nom_env} aide francaise, aucune cle brute")
    # liste
    c, sortie = lance(script, str(oar), str(glb), "--lang", "fr", "--list", "--box", "RAKis", "--neighbor", cwd=w)
    rapport(c == 0 and "Maison Test" in sortie and "3 parties" in sortie and "BOÎTE" in sortie and "par NOM" in sortie and "voisin 1 " in sortie and "3 groupe(s) affiché(s) sur 3" in sortie,
            f"{nom_env} --list : 3 groupes, boite reperee, voisin apparie par nom", sortie[-600:])
    rapport((w / "extraire_batiments.cache").is_dir() and not (script.parent / "extraire_batiments.cache").exists(), f"{nom_env} cache cree dans le dossier courant, pas a cote du script")
    c, sortie = lance(script, str(oar), str(glb), "--lang", "fr", "--list", cwd=w)
    rapport(c == 0 and "lus dans le cache" in sortie, f"{nom_env} deuxieme lancement : groupes lus dans le cache", sortie[-300:])
    c, sortie = lance(script, str(oar), str(glb), "--lang", "en", "--list", "--no-cache", cwd=w)
    rapport(c == 0 and "3 parts" in sortie and "group(s) shown out of 3" in sortie and not ACC.search(sortie), f"{nom_env} --list en anglais", sortie[-300:])
    # extraction
    c, sortie = lance(script, str(oar), str(glb), "--lang", "fr", "--group", "1", "-o", "sortie", "--ground", "2", cwd=w)
    f = w / "sortie" / "0001_Maison_Test.glb"
    rapport(c == 0 and f.is_file() and f.with_suffix(".json").is_file(), f"{nom_env} --groupe 1 : .glb et .json ecrits", sortie[-500:])
    if f.is_file() and f.with_suffix(".json").is_file():
        info = json.loads(f.with_suffix(".json").read_text(encoding="utf-8"))
        js = lire_glb(f)
        racine = js["nodes"][js["scenes"][0]["nodes"][0]]
        rapport(abs(info["origine_opensim"]["x"] - 100.0) < 0.6 and abs(info["origine_opensim"]["y"] - 100.0) < 0.6 and abs(info["origine_opensim"]["sol"] - 20.0) < 0.05,
                f"{nom_env} json : origine OpenSim (100, 100) et sol 20", info.get("origine_opensim"))
        rapport(info["sol_source"].startswith("terrain de l'OAR") and info["groupes"] == [1] and info["noeuds"] == 3, f"{nom_env} json : source du sol, groupe 1, 3 noeuds", info)
        t = racine["translation"]
        rapport(abs(t[1] + 20.0) < 0.05 and abs(t[0] + 100.0) < 0.6 and abs(t[2] - 100.0) < 0.6, f"{nom_env} glb : noeud parent de recentrage", t)
        rapport(any(n.get("extras", {}).get("essai") for n in js["nodes"]) and len(js["scenes"][0]["nodes"]) == 2, f"{nom_env} glb : sol d'essai ajoute (extras.essai)")
    # anciens noms francais des options : memes resultats
    c, ancien = lance(script, str(oar), str(glb), "--lang", "fr", "--list", "--boite", "RAKis", "--voisin", "--rayon", "30", cwd=w)
    c2, nouveau = lance(script, str(oar), str(glb), "--lang", "fr", "--list", "--box", "RAKis", "--neighbor", "--radius", "30", cwd=w)
    rapport(c == 0 and c2 == 0 and "voisin 1 " in ancien and "rayon position 30 m" in ancien and re.sub(r"cache.*", "", ancien) == re.sub(r"cache.*", "", nouveau),
            f"{nom_env} anciens noms (--boite --voisin --rayon) : meme resultat que les nouveaux", ancien[-300:])
    c, sortie = lance(script, str(oar), str(glb), "--lang", "fr", "--groupe=3", "--sortie", "ancien", "--fusionner", "Pan", cwd=w)
    rapport(c == 0 and (w / "ancien" / "Pan.glb").is_file(), f"{nom_env} anciens noms (--groupe=3 --sortie --fusionner) acceptes", sortie[-300:])
    # fusion
    c, sortie = lance(script, str(oar), str(glb), "--lang", "fr", "--group", "1", "--group", "3", "--merge", "Maison et panneau", "-o", "sortie", cwd=w)
    rapport(c == 0 and (w / "sortie" / "Maison_et_panneau.glb").is_file(), f"{nom_env} --fusionner : un seul fichier", sortie[-400:])
    # erreurs
    c, sortie = lance(script, str(oar), str(glb), "--lang", "en", "--group", "99", cwd=w)
    rapport(c != 0 and "unknown group number" in sortie and not ACC.search(sortie), f"{nom_env} numero inconnu : message anglais", sortie[-300:])
    c, sortie = lance(script, str(oar), str(glb), "--lang", "fr", "--all", cwd=w)
    rapport(c != 0 and "--min-parts" in sortie, f"{nom_env} --tous sans --min-parties refuse", sortie[-300:])
    c, sortie = lance(script, "--lang", "fr", "--clear-cache", cwd=w)
    rapport(c == 0 and "cache supprimé" in sortie and not (w / "extraire_batiments.cache").exists(), f"{nom_env} --vider-cache", sortie[-300:])

# outils voisins : --tools, WEB3D_TOOLS, absence
seul = tmp / "seul"
seul.mkdir()
if (DIST / "extraire_batiments.py").is_file():
    shutil.copy(DIST / "extraire_batiments.py", seul / "extraire_batiments.py")
    w = tmp / "w_tools"
    w.mkdir()
    c, s = lance(seul / "extraire_batiments.py", "--lang", "en", "--help", cwd=w)
    rapport(c == 0 and "usage:" in s, "script seul : l'aide marche sans les outils voisins", s[-200:])
    c, s = lance(seul / "extraire_batiments.py", str(oar), str(glb), "--lang", "en", "--list", cwd=w)
    rapport(c != 0 and "not found" in s and "--tools" in s and not ACC.search(s) and "py." not in s, "script seul : message clair (--tools), en anglais", s[-300:])
    c, s = lance(seul / "extraire_batiments.py", str(oar), str(glb), "--lang", "fr", "--list", cwd=w)
    rapport(c != 0 and "introuvables" in s, "script seul : message clair en francais", s[-300:])
    c, s = lance(seul / "extraire_batiments.py", str(oar), str(glb), "--lang", "fr", "--list", "--tools", str(DIST), cwd=w)
    rapport(c == 0 and "3 groupe(s) affiché(s) sur 3" in s, "script seul + --tools DOSSIER : marche", s[-300:])
    c, s = lance(seul / "extraire_batiments.py", str(oar), str(glb), "--lang", "fr", "--list", cwd=w, env={"WEB3D_TOOLS": str(DIST)})
    rapport(c == 0 and "3 groupe(s) affiché(s) sur 3" in s, "script seul + variable WEB3D_TOOLS : marche", s[-300:])
    c, s = lance(seul / "extraire_batiments.py", str(oar), str(glb), "--lang", "fr", "--list", "--tools", str(tmp), cwd=w)
    rapport(c != 0 and "introuvables" in s, "--tools vers un mauvais dossier : message clair", s[-300:])

apres_dist = contenu(DIST)
rapport(avant_dist == apres_dist, "dist/ : aucun fichier ajoute par les essais (cache, sortie)", set(apres_dist) ^ set(avant_dist))
shutil.rmtree(tmp, ignore_errors=True)
print("\nRESULTAT : " + ("tout est passe" if not bad else f"{bad} echec(s)"))
sys.exit(1 if bad else 0)
