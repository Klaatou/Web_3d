#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iar2oar.py (hors navigateur) : IAR synthetique, outil lance depuis tools/ (sources) et depuis dist/ (fabrique).

Verifie : aide fr/en ; --list ; OAR ecrit (groupes, noms, positions en grille, objet combine separe, objet imbrique, --no-nested, --filter) ;
OAR relu par oar_scan d'oar2glb.py ; assets utiles seulement ; octet nul retire ; anciens noms francais des options ; messages d'erreur fr/en.
Lancer : python build.py puis python tests/iar2oar.py
"""
import io, os, pathlib, re, subprocess, sys, tarfile, tempfile, uuid

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


def partie(nom, off=(0, 0, 0), ech=(10, 8, 4), extra=""):
    return (f"<SceneObjectPart><UUID><Guid>{U()}</Guid></UUID><Name>{nom}</Name><GroupPosition><X>1</X><Y>1</Y><Z>1</Z></GroupPosition>"
            f"<OffsetPosition><X>{off[0]}</X><Y>{off[1]}</Y><Z>{off[2]}</Z></OffsetPosition><RotationOffset><X>0</X><Y>0</Y><Z>0</Z><W>1</W></RotationOffset>"
            f"<Scale><X>{ech[0]}</X><Y>{ech[1]}</Y><Z>{ech[2]}</Z></Scale><Shape><SculptType>0</SculptType></Shape>{extra}</SceneObjectPart>")


def groupe(parties_):
    return "<SceneObjectGroup><RootPart>" + parties_[0] + "</RootPart><OtherParts>" + "".join(parties_[1:]) + "</OtherParts></SceneObjectGroup>"


A_MAISON, A_BOITE, A_DEDANS, A_COMBI, A_VIDE = U(), U(), U(), U(), U()
TEXTURE, MESH, MATERIAU, SON = U(), U(), U(), U()
dedans_xml = ("<TaskInventory><TaskInventoryItem><Name>Dedans</Name><AssetID><UUID>" + A_DEDANS + "</UUID></AssetID></TaskInventoryItem></TaskInventory>")
ASSETS = {
    f"assets/{A_MAISON}_object.xml": (groupe([partie("racine"), partie("toit", (0, 0, 3), (12, 10, 1))]).encode() + b"\x00"),
    f"assets/{A_BOITE}_object.xml": (groupe([partie("boite", ech=(1.2, 1.2, 1.2), extra=dedans_xml)]).encode() + b"\x00"),
    f"assets/{A_DEDANS}_object.xml": (groupe([partie("contenu", ech=(3, 3, 3))]).encode() + b"\x00"),
    f"assets/{A_COMBI}_object.xml": ('<CoalescedObject x="20" y="10" z="5"><SceneObjectGroup offsetx="0" offsety="0" offsetz="0"><RootPart>' + partie("a", ech=(5, 5, 5))
                                    + '</RootPart></SceneObjectGroup><SceneObjectGroup offsetx="10" offsety="0" offsetz="0"><RootPart>' + partie("b", ech=(5, 5, 5))
                                    + "</RootPart></SceneObjectGroup></CoalescedObject>").encode() + b"\x00",
    f"assets/{MESH}_mesh.llmesh": b"mesh", f"assets/{TEXTURE}_texture.jp2": b"tex", f"assets/{MATERIAU}_material.xml": b"<m/>", f"assets/{SON}_sound.ogg": b"son",
}


def item(nom, asset, type_="6"):
    return f"<InventoryItem><Name>{nom}</Name><AssetID>{asset}</AssetID><AssetType>{type_}</AssetType></InventoryItem>".encode()


def faire_iar(chemin, avec_inventaire=True):
    with tarfile.open(chemin, "w:gz") as t:
        def add(nom, data):
            ti = tarfile.TarInfo(nom)
            ti.size = len(data)
            t.addfile(ti, io.BytesIO(data))
        if avec_inventaire:
            add("inventory/Objects/Maison.xml", item("Maison", A_MAISON))
            add("inventory/Objects/Boite.xml", item("Boite", A_BOITE))
            add("inventory/Objects/Combine.xml", item("Combine", A_COMBI))
            add("inventory/Objects/Sans asset.xml", item("Sans asset", A_VIDE))
            add("inventory/Textures/Tex.xml", item("Tex", TEXTURE, "0"))
        for nom, data in ASSETS.items():
            add(nom, data)


def lance(script, *args, cwd, env=None):
    e = dict(os.environ)
    for v in ("WEB3D_LANG", "LC_ALL", "LC_MESSAGES", "LANGUAGE"):
        e.pop(v, None)
    e["LANG"], e["PYTHONIOENCODING"] = "C", "utf-8"
    e.update(env or {})
    r = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, encoding="utf-8", cwd=str(cwd), env=e, stdin=subprocess.DEVNULL, timeout=120)
    return r.returncode, r.stdout + r.stderr


sys.path.insert(0, str(TOOLS))
import oar2glb  # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="iar2oar_"))
iar, iar_vide = tmp / "Essai.iar", tmp / "Vide.iar"
faire_iar(iar)
faire_iar(iar_vide, avec_inventaire=False)


def contenu(d):
    return sorted(p.name for p in d.iterdir() if p.name != "__pycache__") if d.is_dir() else []


avant_dist = contenu(DIST)
for nom_env, script in (("sources tools/", TOOLS / "iar2oar.py"), ("dist/", DIST / "iar2oar.py")):
    if not script.is_file():
        rapport(False, f"{nom_env} : {script.name} introuvable (python build.py d'abord)")
        continue
    w = tmp / ("w_" + nom_env.strip("/").replace("/", "_"))
    w.mkdir()
    c, en = lance(script, "--lang", "en", "--help", cwd=w)
    c2, fr = lance(script, "--lang", "fr", "--help", cwd=w)
    rapport(c == 0 and "--margin" in en and "--lang" in en and not ACC.search(en), f"{nom_env} aide anglaise, sans lettre accentuee francaise", [l for l in en.splitlines() if ACC.search(l)][:3])
    rapport(c2 == 0 and ACC.search(fr) and "py." not in fr and "py." not in en, f"{nom_env} aide francaise, aucune cle brute")
    c, s = lance(script, str(iar), "--lang", "fr", "--list", cwd=w)
    rapport(c == 0 and "4 objet(s)" in s and "5 groupe(s)" in s and "6 partie(s)" in s and "combiné" in s and "imbriqué niveau 1" in s and "Boite / Dedans" in s
            and "1 élément(s) sans asset objet" in s and "Sans asset" in s and "Tex" not in s.replace("Texture", ""), f"{nom_env} --list : objets, groupes, parties, combine, imbrique, manquant", s[-700:])
    rapport(not (w / "inventaire.oar").exists(), f"{nom_env} --list n'ecrit rien")
    c, s = lance(script, str(iar), "--lang", "en", "--list", cwd=w)
    rapport(c == 0 and "4 object(s)" in s and "coalesced" in s and "nested level 1" in s and not ACC.search(s), f"{nom_env} --list en anglais", s[-400:])
    # ecriture
    sortie = w / "inv.oar"
    c, s = lance(script, str(iar), "--lang", "fr", "-o", str(sortie), cwd=w)
    rapport(c == 0 and sortie.is_file() and "OAR écrit" in s and "5 groupes" in s and "3 assets copiés" in s, f"{nom_env} OAR ecrit (5 groupes, 3 assets copies)", s[-400:])
    if sortie.is_file():
        with tarfile.open(sortie) as t:
            noms = [m.name for m in t if m.isfile()]
            objets = [n for n in noms if n.startswith("objects/")]
            assets = sorted(n for n in noms if n.startswith("assets/"))
            xml = {n: t.extractfile(n).read() for n in objets}
            arch = t.extractfile("archive.xml").read().decode()
        rapport(len(objets) == 5 and len(assets) == 3 and not any(n.endswith("_sound.ogg") or n.endswith("_object.xml") for n in assets), f"{nom_env} OAR : 5 objets, seuls mesh, texture, materiau copies", (len(objets), assets))
        rapport(all(b"\x00" not in d for d in xml.values()) and "<size_in_meters>256,256</size_in_meters>" in arch, f"{nom_env} OAR : aucun octet nul, region de 256 m")
        scan = oar2glb.oar_scan(sortie)
        gs = {g["parts"][0]["name"]: g for g in scan["groups"]}
        rapport(sorted(gs) == ["Boite", "Boite / Dedans", "Combine [1]", "Combine [2]", "Maison"], f"{nom_env} OAR relu par oar_scan : noms des groupes", sorted(gs))
        pos = {n: g["parts"][0]["gpos"] for n, g in gs.items()}
        rapport(all(abs(p[2] - 20.0) < 0.01 for p in pos.values()) and len({(round(p[0], 1), round(p[1], 1)) for p in pos.values()}) == 5, f"{nom_env} OAR : cinq cases distinctes, z = 20", pos)
        rapport(abs((pos["Combine [2]"][0] - pos["Combine [1]"][0]) - 10.0) < 0.01 and abs(pos["Combine [2]"][1] - pos["Combine [1]"][1]) < 0.01, f"{nom_env} OAR : l'objet combine garde son decalage de 10 m")
        rapport(len(gs["Maison"]["parts"]) == 2, f"{nom_env} OAR : la maison garde ses 2 parties")
    # options
    c, s = lance(script, str(iar), "--lang", "fr", "--list", "--no-nested", cwd=w)
    rapport(c == 0 and "3 objet(s)" in s and "4 groupe(s)" in s and "Dedans" not in s, f"{nom_env} --no-nested", s[-300:])
    c, s = lance(script, str(iar), "--lang", "fr", "--list", "--filter", "^maison", cwd=w)
    rapport(c == 0 and "1 objet(s)" in s and "Maison" in s, f"{nom_env} --filter (casse ignoree)", s[-300:])
    c, ancien = lance(script, str(iar), "--lang", "fr", "--liste", "--filtre", "^maison", "--sans-imbriques", cwd=w)
    c2, nouveau = lance(script, str(iar), "--lang", "fr", "--list", "--filter", "^maison", "--no-nested", cwd=w)
    rapport(c == 0 and c2 == 0 and ancien == nouveau and "1 objet(s)" in ancien, f"{nom_env} anciens noms (--liste --filtre --sans-imbriques) : meme resultat", ancien[-300:])
    c, s = lance(script, str(iar), "--lang", "fr", "--sortie", "ancien.oar", "--marge=8", cwd=w)
    rapport(c == 0 and (w / "ancien.oar").is_file(), f"{nom_env} anciens noms (--sortie --marge=8) acceptes", s[-300:])
    # erreurs
    c, s = lance(script, str(tmp / "absent.iar"), "--lang", "en", cwd=w)
    rapport(c != 0 and "unreadable IAR" in s and not ACC.search(s), f"{nom_env} IAR absent : message anglais", s[-300:])
    c, s = lance(script, str(iar_vide), "--lang", "fr", cwd=w)
    rapport(c != 0 and "aucun objet dans l'inventaire" in s, f"{nom_env} IAR sans inventaire : message francais", s[-300:])
    c, s = lance(script, str(iar), "--lang", "en", "--filter", "zzz", cwd=w)
    rapport(c != 0 and "nothing to convert" in s, f"{nom_env} filtre sans resultat : message anglais", s[-300:])

rapport(avant_dist == contenu(DIST), "dist/ : aucun fichier ajoute par les essais", set(contenu(DIST)) ^ set(avant_dist))
print("\nRESULTAT : " + ("tout est passe" if not bad else f"{bad} echec(s)"))
sys.exit(1 if bad else 0)
