#!/usr/bin/env python3
"""Test 1.9.12 : matériaux PBR d'OpenSim 0.9.3 dans oar2glb.py (hors navigateur, sans convoar).

Vérifie : lecture du paramètre supplémentaire 0x80 (face + UUID), du <MatOvrd> (LLSD notation, base64), d'un matériau *_prmat.dat
(en-tête LLSD binaire autour d'un glTF), puis l'application à un GLB fabriqué à la main : matériau par face, surcharges (facteurs,
transformation de texture), maillage partagé copié seulement quand les matériaux diffèrent, images ajoutées au GLB final.
Les parties qui demandent Pillow (textures JPEG 2000) sont ignorées si Pillow ou son module JPEG 2000 manque.

Lancer : python tests/pbr_oar.py
"""
import os as _os_lang; _os_lang.environ["WEB3D_LANG"] = "fr"
import base64, io, json, pathlib, struct, sys, tempfile, shutil, uuid
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import oar2glb as T  # noqa: E402

bad = 0


def rapport(ok, nom, detail=""):
    global bad
    bad += not ok
    print(("[OK]    " if ok else "[ECHEC] ") + nom + ("" if ok else "  " + str(detail)), flush=True)


def u():
    return str(uuid.uuid4())


# --- 1. paramètre supplémentaire 0x80
A, B, C = u(), u(), u()
entrees = [(0, A), (2, B), (5, C)]
pay = bytes([len(entrees)]) + b"".join(bytes([f]) + uuid.UUID(x).bytes for f, x in entrees)
lumiere = struct.pack("<Hi", 0x20, 16) + b"\x00" * 16            # un autre paramètre avant : doit être sauté
d = bytes([2]) + lumiere + struct.pack("<Hi", 0x80, len(pay)) + pay
rapport(T.pbr_extra_params(d) == entrees, "ExtraParams : (face, UUID) du paramètre 0x80, un autre paramètre sauté", T.pbr_extra_params(d))
rapport(T.pbr_extra_params(b"\x00") == [] and T.pbr_extra_params(b"") == [] and T.pbr_extra_params(d[:20]) == [], "ExtraParams vide ou tronqué : liste vide, sans exception")

# --- 2. LLSD notation
s = "{'rf':r0.2,'mf':i1,'ds':t,'tex':[!,u%s,u%s],'ti':[{'o':[r0,r-0.5],'r':r1.570796,'s':[r2,r2]}],'am':i1,'nom':'a\\'b'}" % (A.upper(), T.PBR_NUL)
v = T.llsd_notation(s)
ok = (v["rf"] == 0.2 and v["mf"] == 1 and v["ds"] is True and v["tex"] == [None, A, T.PBR_NUL] and v["ti"][0]["o"] == [0.0, -0.5]
      and abs(v["ti"][0]["r"] - 1.570796) < 1e-9 and v["ti"][0]["s"] == [2.0, 2.0] and v["am"] == 1 and v["nom"] == "a'b")
rapport(ok, "LLSD notation : réels, entiers, booléen, UUID, !, tableaux, tables imbriquées, texte avec apostrophe échappée", v)
rapport(T.llsd_notation("{}") == {} and T.llsd_notation("[]") == [], "LLSD notation : table et tableau vides")


# --- 3. <MatOvrd>
def matovrd(par_face):
    out = bytes([len(par_face)])
    for f, txt in par_face:
        t = txt.encode("utf-8")
        out += bytes([f, len(t) & 255, len(t) >> 8]) + t
    return base64.b64encode(out).decode()


mo = T.pbr_matovrd(matovrd([(0, "{'rf':r0.2}"), (3, "{'bc':[r1,r0.5,r0.25,r0.6],'am':i1}")]))
rapport(mo == {0: {"rf": 0.2}, 3: {"bc": [1.0, 0.5, 0.25, 0.6], "am": 1}}, "MatOvrd : surcharges par face", mo)
rapport(T.pbr_matovrd("") == {} and T.pbr_matovrd("AA==") == {} and T.pbr_matovrd("!!!") == {}, "MatOvrd : vide, « aucune », illisible -> {}")

# --- 4. matériau *_prmat.dat
MAT = {"asset": {"version": "2.0"}, "images": [{"uri": A}, {"uri": B}, {"uri": A}],
       "materials": [{"normalTexture": {"index": 1, "scale": 0.5}, "occlusionTexture": {"index": 2},
                      "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicRoughnessTexture": {"index": 2}, "roughnessFactor": 0.9}}],
       "textures": [{"source": 0}, {"source": 1}, {"source": 2}]}


def prmat(g):
    js = json.dumps(g).encode()
    return b"<? LLSD/Binary ?>\n{" + struct.pack(">I", 1) + b"k" + struct.pack(">I", 4) + b"data" + b"s" + struct.pack(">I", len(js)) + js + b"}"


rapport(T.pbr_materiau(prmat(MAT)) == MAT, "prmat.dat : en-tête LLSD binaire + glTF décodés")
rapport(T.pbr_materiau(b"n'importe quoi") is None and T.pbr_materiau(prmat({"asset": {}})) is None, "prmat.dat illisible ou sans matériau : None")

# --- 5. partie complète depuis l'XML
extra = base64.b64encode(d).decode()
xml = "<Shape><ExtraParams>%s</ExtraParams><MatOvrd>%s</MatOvrd></Shape>" % (extra, matovrd([(0, "{'rf':r0.2}")]))
pp = T.pbr_partie(ET.fromstring(xml))
rapport(pp == {"faces": dict(entrees), "ovr": {0: {"rf": 0.2}}, "nfaces": None}, "partie : faces + surcharges depuis <Shape>", pp)
SPHERE = "<Shape><ProfileCurve>5</ProfileCurve><PathCurve>32</PathCurve><SculptEntry>false</SculptEntry><ExtraParams>%s</ExtraParams>%s</Shape>"
rapport(T.pbr_partie(ET.fromstring(SPHERE % (extra, "")))["nfaces"] == 1, "sphère entière : 1 face (règle d'OpenSim)")
for nom, champ in (("creuse", "<ProfileHollow>49500</ProfileHollow>"), ("coupée", "<PathEnd>5000</PathEnd>"), ("tordue", "<PathTwist>10</PathTwist>")):
    rapport(T.pbr_partie(ET.fromstring(SPHERE.replace("<ExtraParams>", champ + "<ExtraParams>") % (extra, "")))["nfaces"] is None, "sphère " + nom + " : pas de règle")
rapport(T.pbr_partie(ET.fromstring(SPHERE.replace("<PathCurve>32", "<PathCurve>16") % (extra, "")))["nfaces"] is None, "cube/cylindre : pas de règle")
rapport(T.pbr_partie(ET.fromstring("<Shape><ExtraParams>AA==</ExtraParams></Shape>")) is None and T.pbr_partie(ET.fromstring("<Shape/>")) is None,
        "partie sans PBR : None")

# --- 6. application à un GLB fabriqué à la main
MAT2 = {"asset": {"version": "2.0"}, "materials": [{"pbrMetallicRoughness": {"metallicFactor": 0.2}}]}
U1, U2, U3 = u(), u(), u()


def fabrique():
    g = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0, 1, 2]}],
         "nodes": [{"name": U1, "mesh": 0}, {"name": U2, "mesh": 0}, {"name": U3, "mesh": 0}],
         "meshes": [{"primitives": [{"attributes": {}, "material": 0}, {"attributes": {}, "material": 0}], "extras": {"uniqueHash": "H"}}],
         "materials": [{"name": "convoar"}], "buffers": []}
    part = lambda uid, faces, ovr: {"uuid": uid, "name": "p", "mesh": None, "wpos": [0, 0, 0], "gpos": [0, 0, 0], "pbr": {"faces": faces, "ovr": ovr}}
    ov = {0: {"rf": 0.2, "mf": 0, "am": 1, "ti": [{"o": [0.5, 0.0], "r": 0.0, "s": [2.0, 2.0]}, None, None, None]}}
    scan = {"groups": [{"file": "x", "parts": [part(U1, {0: A, 1: B}, ov), part(U2, {0: A, 1: B}, {}), part(U3, {0: A, 1: B}, {})]}],
            "pbr_mats": {A: MAT, B: MAT2}}
    return g, scan


g, scan = fabrique()
n = T.pbr_appliquer(g, scan, None, 0, textures={})
rapport(n == 3, "3 prims PBR traitées", n)
rapport(g["meshes"][0]["primitives"][0]["material"] == 0, "maillage d'origine inchangé")
m1, m2, m3 = (g["nodes"][i]["mesh"] for i in range(3))
rapport(m1 != 0 and m2 != 0 and m1 != m2 and m2 == m3 and len(g["meshes"]) == 3,
        "maillage copié par jeu de matériaux : la prim à surcharges a le sien, les deux autres partagent une copie", (m1, m2, m3))
mat = g["materials"][g["meshes"][m1]["primitives"][0]["material"]]
p = mat["pbrMetallicRoughness"]
rapport(p["roughnessFactor"] == 0.2 and p["metallicFactor"] == 0.0 and mat["alphaMode"] == "BLEND", "surcharges rf, mf, am appliquées", mat)
sans = g["materials"][g["meshes"][m2]["primitives"][0]["material"]]
rapport(sans["pbrMetallicRoughness"]["roughnessFactor"] == 0.9 and "alphaMode" not in sans, "sans surcharge : valeurs du matériau d'origine", sans)
rapport(g["materials"][g["meshes"][m2]["primitives"][1]["material"]]["pbrMetallicRoughness"]["metallicFactor"] == 0.2, "face 1 : matériau B (facteur seul, sans texture)")
rapport("baseColorTexture" not in sans["pbrMetallicRoughness"] and "images" not in g, "sans textures fournies : facteurs seulement, aucune image ajoutée")

# --- 6 bis. sphère entière : la primitive en plus (calotte de libomv) prend la face 0, pas la face 1
g, scan = fabrique()
for p in scan["groups"][0]["parts"]:
    p["pbr"]["nfaces"] = 1
T.pbr_appliquer(g, scan, None, 0, textures={})
mats_prims = [g["materials"][pr["material"]]["pbrMetallicRoughness"] for pr in g["meshes"][g["nodes"][1]["mesh"]]["primitives"]]
rapport(mats_prims[0] == mats_prims[1] and mats_prims[0]["roughnessFactor"] == 0.9, "sphère entière : les 2 primitives ont le matériau de la face 0 (pas de disque à part)", mats_prims)

# --- 7. avec de vraies textures (Pillow + JPEG 2000)
try:
    from PIL import Image, features
    jp2 = features.check_codec("jpg_2000")
except ImportError:
    jp2 = False
if not jp2:
    print("[IGNORE] Pillow ou son module JPEG 2000 absent : parties « textures » non essayées")
else:
    def j2k(couleur, taille=(64, 48)):
        out = io.BytesIO()
        Image.new("RGB", taille, couleur).save(out, "JPEG2000")
        return out.getvalue()
    g, scan = fabrique()
    textures = {A: j2k((200, 30, 30), (64, 48)), B: j2k((128, 128, 255), (32, 32))}
    n = T.pbr_appliquer(g, scan, None, 0, textures=textures)
    rapport(len(g["images"]) == 2 and len(g["textures"]) == 2 and all(i["mimeType"] == "image/jpeg" for i in g["images"]),
            "2 images (A partagée entre couleur de base et métal/rugosité, B normale), JPEG", g.get("images"))
    m1 = g["nodes"][0]["mesh"]
    mat = g["materials"][g["meshes"][m1]["primitives"][0]["material"]]
    p = mat["pbrMetallicRoughness"]
    rapport(p["baseColorTexture"]["index"] == p["metallicRoughnessTexture"]["index"] == mat["occlusionTexture"]["index"],
            "occlusion = texture métal/rugosité (même image)", mat)
    rapport(mat["normalTexture"]["scale"] == 0.5 and mat["normalTexture"]["index"] != p["baseColorTexture"]["index"], "normale : texture B, échelle d'origine gardée")
    tr = p["baseColorTexture"].get("extensions", {}).get("KHR_texture_transform")
    rapport(tr == {"offset": [0.5, 0.0], "rotation": 0.0, "scale": [2.0, 2.0]} and "KHR_texture_transform" in g["extensionsUsed"],
            "surcharge « ti » : KHR_texture_transform + extensionsUsed", tr)
    ms = g["materials"][g["meshes"][g["nodes"][1]["mesh"]]["primitives"][0]["material"]]
    rapport("extensions" not in ms["pbrMetallicRoughness"]["baseColorTexture"], "sans surcharge : pas de transformation")
    # réduction de taille
    g2, scan2 = fabrique()
    T.pbr_appliquer(g2, scan2, None, 16, textures={A: j2k((10, 20, 30), (64, 48)), B: j2k((1, 2, 3), (32, 32))})
    rapport(len(g2["images"]) == 2, "taille maximale 16 px : textures encore lisibles")
    # GLB final : les images (bufferView) survivent à pack_glb
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="pbr_oar_"))
    try:
        out = tmp / "t.glb"
        T.pack_glb(g, tmp, out)
        data = out.read_bytes()
        ln = struct.unpack_from("<I", data, 12)[0]
        js = json.loads(data[20:20 + ln])
        binlen = struct.unpack_from("<I", data, 20 + ln)[0]
        ok = len(js["images"]) == 2 and all("bufferView" in i and "uri" not in i for i in js["images"])
        for i in js["images"]:
            bv = js["bufferViews"][i["bufferView"]]
            ok = ok and bv["byteOffset"] + bv["byteLength"] <= binlen and data[28 + ln + bv["byteOffset"]:28 + ln + bv["byteOffset"] + 2] == b"\xff\xd8"
        rapport(ok, "GLB final : images dans le bloc binaire (début JPEG vérifié)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

# --- 8. Pillow absent : facteurs seulement, message, pas d'exception
g, scan = fabrique()
vrai = T.pbr_pillow
T.pbr_pillow = lambda: None
try:
    n = T.pbr_appliquer(g, scan, None, 0)
finally:
    T.pbr_pillow = vrai
rapport(n == 3 and "images" not in g, "Pillow absent : matériaux appliqués sans textures")

print("\n%s" % ("TOUT PASSE" if not bad else "%d ECHEC(S)" % bad))
sys.exit(1 if bad else 0)
