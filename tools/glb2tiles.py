#!/usr/bin/env python3
"""glb2tiles.py : découpe un GLB énorme en tuiles autonomes (un GLB valide par tuile).

Usage :  python glb2tiles.py --version
         python glb2tiles.py "Region.glb" --analyse
         python glb2tiles.py "Region.glb" [--budget 32] [--budget-triangles 1500000] [--min 16] [--output DOSSIER] [--no-overview]
         python glb2tiles.py "Region.glb" --overview-only [mêmes options de découpage] [--ov-budget 25] [--ov-threshold 3]

Python standard seulement. Le GLB d'entrée n'est jamais chargé en entier : l'en-tête JSON est lu, puis les accessors
et les images sont lus par seek/read, par morceaux, à la demande. Chaque tuile (quelques dizaines de Mo) est
assemblée en mémoire puis écrite.

Sorties (à côté du GLB, ou dans --output) : X.tiles/T_<niveau>_<i>_<j>.glb, X.tiles.json et (v31) X.overview.glb.
Le journal est glb2tiles.log, écrit à côté du script (sa première ligne donne la version).

Principe : quadtree adaptatif sur le plan X,Z (glTF : Y vers le haut), uniquement sur les cellules non vides. Une cellule
est subdivisée tant que son poids autonome dépasse --budget (Mo) ou ses triangles --budget-triangles, et que son côté dépasse
--min (m). Un objet racine (nœud de premier niveau) reste entier si son poids autonome ne dépasse pas --whole-weight (Mo)
ET si son étendue ne dépasse pas --whole-extent (m) ; sinon il est réparti instance par instance. Un objet portant un
skin n'est jamais réparti. Les meshes partagés entre tuiles sont dupliqués dans chaque tuile qui les utilise.
Les sommets de chaque primitive sont compactés (seuls les sommets indexés sont gardés). Coordonnées inchangées.

Images (v31) : une image embarquée de 0 octet, d'un autre format que PNG/JPEG/WebP ou tronquée fait échouer le chargement de la tuile
dans le navigateur ; elle est remplacée par un petit PNG gris (un seul par tuile). --analyse et le rapport en donnent le nombre.

Vue d'ensemble (v31, X.overview.glb) : toute la région en géométrie légère, sans image, un nœud par fichier de tuile ; chaque primitive
unique est simplifiée une seule fois (regroupement de sommets), le terrain est rééchantillonné sur un réseau commun. Écrite avec les
tuiles (--no-overview pour s'en passer) ou seule (--overview-only, mêmes options de découpage). Options --ov-*.

Hors lot : découpage par triangles d'un mesh unique plus grand qu'une cellule (terrain, mer), compression des tuiles.
Les GLB compressés (Draco, meshopt) sont refusés.

Les fonctions communes de mesure (lecture de l'en-tête, matrices, instances) viennent de glb-stats.py, qui doit se
trouver à côté de ce script (build.py le recopie dans dist/).
"""
import argparse
import array
import base64
import collections
import importlib.util
import itertools
import json
import math
import os
import re
import statistics
import struct
import sys
import time
import traceback
import zlib
from pathlib import Path

# <<I18N_PY>>
def _i18n_boot():   # depuis les sources : charge src/i18n_py.py ; fabriqué par build.py (dist\) : ce bloc est remplacé par le texte de i18n_py.py avec les langues intégrées
    import importlib.util, pathlib
    here = pathlib.Path(__file__).resolve().parent
    for p in (here / "i18n_py.py", here.parent / "src" / "i18n_py.py"):
        if p.is_file():
            spec = importlib.util.spec_from_file_location("i18n_py", p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            return m
    raise SystemExit("i18n_py.py not found / introuvable")


_I18N = _i18n_boot()
_tr, i18n_add_common = _I18N._tr, _I18N.i18n_add_common
# <</I18N_PY>>

VERSION = "__VERSION__"      # remplacé par build.py (fichier VERSION) dans dist/glb2tiles.py
MARK = "__MARK__"      # empreinte du fichier fabriqué, inscrite par build.py ; reste telle quelle depuis tools/


def version_tag():
    """version, suivie de l'empreinte du fichier quand build.py l'a inscrite"""
    return VERSION if MARK.startswith("__") else _tr("py.common.version_mark", VERSION, MARK)
FORMAT_TUILES = 1            # version du format de X.tiles.json
BLOC_LECTURE = 4 << 20       # octets lus d'un coup dans le GLB d'entrée (lectures toujours par morceaux)
MO = 1048576
LIMITE_GLB = 0xFFFFFFFF      # un GLB ne dépasse jamais 4 Go (longueurs sur 32 bits)
COMPRESSIONS = ("KHR_draco_mesh_compression", "EXT_meshopt_compression", "KHR_meshopt_compression")
CODE = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
U32 = next(c for c in "IL" if array.array(c).itemsize == 4)
CODE[5125] = U32
TAILLE = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}
LOG_PATH = None              # fixé par main() : fichier du journal (None = écran seulement)


class ErreurGlb(Exception):
    """Cas non géré ou fichier invalide : message clair pour l'utilisateur, arrêt propre."""


# ---------------------------------------------------------------- journal et avancement
def log(msg=""):
    print(msg, flush=True)
    if LOG_PATH:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")


class Progres:
    """Écrit l'avancement dans le journal toutes les 5 % ou 10 s."""

    def __init__(self, titre, total):
        self.titre, self.total = titre, max(1, total)
        self.t0 = self.t = time.time()
        self.pct = -5.0

    def avance(self, fait):
        pct = 100.0 * fait / self.total
        now = time.time()
        if pct - self.pct >= 5 or now - self.t >= 10:
            log(f"[{self.titre}] {pct:.0f} % ({fait}/{self.total}, {now - self.t0:.0f} s)")
            self.pct, self.t = pct, now


# ---------------------------------------------------------------- mesures communes (glb-stats.py)
_stats = None


def stats():
    global _stats
    if _stats is None:
        p = Path(__file__).resolve().with_name("glb-stats.py")
        if not p.is_file():
            raise ErreurGlb(_tr("py.glb2tiles.glb_stats_py_introuvable_a_cote", p.parent))
        spec = importlib.util.spec_from_file_location("glb_stats", p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _stats = m
    return _stats


def fmt(n):
    return stats().fmt(int(n))


def mo(o):
    return o / MO


def virg(x, nd=2):
    return f"{x:.{nd}f}".replace(".", ",")


# ---------------------------------------------------------------- lecture du GLB par morceaux
Acc = collections.namedtuple("Acc", "i comp ncomp count es stride off norm type mn mx")


class Glb:
    """Accès au GLB d'entrée : JSON en mémoire, données lues à la demande (compteurs pour les tests)."""

    def __init__(self, chemin):
        if sys.byteorder != "little":
            raise ErreurGlb(_tr("py.glb2tiles.machine_big_endian_non_geree"))
        self.chemin = str(chemin)
        self.taille = os.path.getsize(chemin)
        self.g, njson = stats().lire_json(self.chemin)
        self.njson = njson
        self.octets_lus = 20 + njson        # en-tête + JSON (lus par lire_json)
        self.plus_grande_lecture = 0
        self.nb_lectures = 0
        comp = [e for e in self.g.get("extensionsUsed", []) if e in COMPRESSIONS]
        if comp:
            raise ErreurGlb(_tr("py.glb2tiles.ce_glb_est_compresse") + ", ".join(comp) + _tr("py.glb2tiles.glb2tiles_ne_lit_pas_les_glb"))
        self.f = open(self.chemin, "rb")
        self.f.seek(20 + njson)
        ent = self.f.read(8)
        self.bin_off, self.bin_len = 0, 0
        if len(ent) == 8:
            ln, typ = struct.unpack("<II", ent)
            if typ == 0x004E4942:
                self.bin_off, self.bin_len = 28 + njson, ln
        self.octets_lus += len(ent)
        bufs = self.g.get("buffers", [])
        if bufs and "uri" in bufs[0]:
            raise ErreurGlb(_tr("py.glb2tiles.le_tampon_0_a_une_adresse"))
        self._acc = {}

    def fermer(self):
        self.f.close()

    def lire(self, off, n):
        """Lit n octets à partir de off (relatif au tampon BIN), par morceaux de BLOC_LECTURE."""
        if off < 0 or n < 0 or off + n > self.bin_len:
            raise ErreurGlb(_tr("py.glb2tiles.lecture_hors_du_tampon_du_glb", off, n))
        out = bytearray()
        self.f.seek(self.bin_off + off)
        reste = n
        while reste > 0:
            k = min(reste, BLOC_LECTURE)
            b = self.f.read(k)
            if len(b) != k:
                raise ErreurGlb(_tr("py.glb2tiles.fichier_glb_tronque"))
            self.octets_lus += k
            self.nb_lectures += 1
            self.plus_grande_lecture = max(self.plus_grande_lecture, k)
            out += b
            reste -= k
        return out

    def vue(self, i):
        bvs = self.g.get("bufferViews", [])
        if i is None or not (0 <= i < len(bvs)):
            raise ErreurGlb(_tr("py.glb2tiles.bufferview_0_inexistant", i))
        bv = bvs[i]
        if bv.get("buffer", 0) != 0:
            raise ErreurGlb(_tr("py.glb2tiles.bufferview_0_seul_le_tampon_0", i))
        return bv

    def acc(self, i):
        a = self._acc.get(i)
        if a is not None:
            return a
        accs = self.g.get("accessors", [])
        if i is None or not (0 <= i < len(accs)):
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_inexistant", i))
        x = accs[i]
        if "sparse" in x:
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_accessor_sparse_non_gere", i))
        if "bufferView" not in x:
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_sans_bufferview_valeurs_a", i))
        bv = self.vue(x["bufferView"])
        comp, typ = x.get("componentType"), x.get("type")
        if comp not in TAILLE or typ not in NCOMP:
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_type_1_2_inconnu", i, typ, comp))
        nc = NCOMP[typ]
        es = nc * TAILLE[comp]
        stride = bv.get("byteStride") or es
        off = bv.get("byteOffset", 0) + x.get("byteOffset", 0)
        count = x.get("count", 0)
        if stride < es:
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_bytestride_1_plus_petit", i, stride, es))
        if count and off + (count - 1) * stride + es > bv.get("byteOffset", 0) + bv.get("byteLength", 0):
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_depasse_son_bufferview_fichier", i))
        a = Acc(i, comp, nc, count, es, stride, off, bool(x.get("normalized")), typ, x.get("min"), x.get("max"))
        self._acc[i] = a
        return a

    def blocs_indices(self, ai):
        """Indices d'un accessor, par morceaux (array non signé)."""
        a = self.acc(ai)
        if a.comp not in (5121, 5123, 5125) or a.ncomp != 1:
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_type_d_indices_non", ai))
        if a.stride != a.es:
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_indices_avec_bytestride_non", ai))
        n_par = max(1, BLOC_LECTURE // a.es)
        for debut in range(0, a.count, n_par):
            n = min(n_par, a.count - debut)
            arr = array.array(CODE[a.comp])
            arr.frombytes(self.lire(a.off + debut * a.es, n * a.es))
            yield arr

    def rangee(self, a, r0, n):
        """Octets bruts de n lignes de l'accessor a à partir de la ligne r0 (longueur (n-1)*stride + es)."""
        if n <= 0:
            return bytearray()
        return self.lire(a.off + r0 * a.stride, (n - 1) * a.stride + a.es)


# ---------------------------------------------------------------- sommets utilisés
class Marques:
    """Ensemble des sommets indexés, sous forme de drapeaux sur la plage [base, base+len(flags))."""

    def __init__(self):
        self.base = 0
        self.flags = bytearray()

    def ajouter(self, arr):
        if not len(arr):
            return
        mn, mx = min(arr), max(arr)
        if not self.flags:
            self.base = mn
            self.flags = bytearray(mx - mn + 1)
        else:
            if mn < self.base:
                self.flags = bytearray(self.base - mn) + self.flags
                self.base = mn
            fin = self.base + len(self.flags)
            if mx >= fin:
                self.flags.extend(bytes(mx - fin + 1))
        src = map(self.base.__rsub__, arr) if self.base else arr
        collections.deque(map(self.flags.__setitem__, src, itertools.repeat(1)), maxlen=0)

    def compter(self):
        return self.flags.count(1)

    @property
    def imin(self):
        return self.base

    @property
    def imax(self):
        return self.base + len(self.flags) - 1


def tri_mode(mode, n):
    if mode == 4:
        return n // 3
    if mode in (5, 6):
        return max(0, n - 2)
    return 0


def taille_indices(used):
    return 2 if used <= 65535 else 4


def es_sortie(es):
    return (es + 3) // 4 * 4


def decode_norm(v, comp, norm):
    if not norm or comp == 5126:
        return v
    if comp in (5120, 5122):
        return max(v / (2 ** (8 * TAILLE[comp] - 1) - 1), -1.0)
    return v / (2 ** (8 * TAILLE[comp]) - 1)


def minmax_donnees(data, a, stride_out):
    """min/max par composante d'un tampon compact (lignes de stride_out octets) ; None si non fini."""
    arr = array.array(CODE[a.comp])
    arr.frombytes(bytes(data) if not isinstance(data, (bytes, bytearray)) else data)
    se = stride_out // TAILLE[a.comp]
    mins, maxs = [], []
    for k in range(a.ncomp):
        col = arr[k::se]
        if not len(col):
            return None
        mins.append(decode_norm(min(col), a.comp, a.norm))
        maxs.append(decode_norm(max(col), a.comp, a.norm))
    if a.comp == 5126 and not all(math.isfinite(v) for v in mins + maxs):
        return None
    return mins, maxs


class Prim:
    """Géométrie distincte (clé : mode, indices, attributs, cibles) ; les matériaux n'en font pas partie."""
    __slots__ = ("key", "mode", "indices", "attrs", "targets", "tri", "used", "n_idx", "imin", "imax", "lo", "hi", "cbytes", "vide")


def cle_prim(pr):
    attrs = tuple(sorted(pr.get("attributes", {}).items()))
    tg = tuple(tuple(sorted(t.items())) for t in pr.get("targets", ()))
    return (pr.get("mode", 4), pr.get("indices"), attrs, tg)


def parcourir_textures(obj, f):
    """Appelle f(dict) pour chaque référence de texture (clé finissant par « Texture », avec « index »)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.endswith("Texture") and isinstance(v, dict) and isinstance(v.get("index"), int):
                f(v)
            parcourir_textures(v, f)
    elif isinstance(obj, list):
        for v in obj:
            parcourir_textures(v, f)


def images_de_texture(t):
    src = [t.get("source")]
    src += [e.get("source") for e in t.get("extensions", {}).values() if isinstance(e, dict)]
    return [s for s in src if isinstance(s, int)]


GRIS_IMAGE = 128             # niveau du gris des images remplacées (celui de oar2glb.py, GREY_PNG)
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def png_gris(niveau=GRIS_IMAGE, cote=4):
    """PNG RVB uni de cote x cote pixels (zlib et struct seulement)."""
    def chunk(typ, data):
        c = typ + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    ligne = b"\x00" + bytes([niveau]) * (3 * cote)
    return PNG_SIG + chunk(b"IHDR", struct.pack(">IIBBBBB", cote, cote, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(ligne * cote, 9)) + chunk(b"IEND", b"")


def image_valide(lecteur, n):
    """PNG, JPEG ou WebP complet (structure seulement, sans décoder) ; faux pour 0 octet, autre format ou image tronquée.
    lecteur(décalage, longueur) rend des octets, n est la taille de l'image : seuls l'en-tête, la fin et les en-têtes de blocs sont lus.
    Mesuré dans Chromium (createImageBitmap) : une image tronquée échoue comme une image vide, d'où la vérification de la fin du fichier :
    PNG = chaînage des blocs jusqu'à IEND ; JPEG = marqueur EOI (FFD9) en dernier, aux zéros et espaces de bourrage près, ou dans les 64
    derniers octets ; WebP = taille RIFF contenue dans le fichier."""
    tete = bytes(lecteur(0, min(n, 12)))
    if tete[:8] == PNG_SIG:
        p = 8
        for _ in range(100000):
            if p + 12 > n:
                return False
            ln, typ = struct.unpack(">I4s", bytes(lecteur(p, 8)))
            p += 12 + ln
            if typ == b"IEND":
                return p <= n
        return False
    if tete[:3] == b"\xff\xd8\xff":
        fin = bytes(lecteur(max(0, n - 64), min(n, 64)))
        return fin.rstrip(b"\x00 \r\n").endswith(b"\xff\xd9") or b"\xff\xd9" in fin
    if tete[:4] == b"RIFF" and tete[8:12] == b"WEBP":
        return struct.unpack("<I", tete[4:8])[0] + 8 <= n
    return False


def extensions_presentes(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "extensions" and isinstance(v, dict):
                out.update(v.keys())
            extensions_presentes(v, out)
    elif isinstance(obj, list):
        for v in obj:
            extensions_presentes(v, out)


# ---------------------------------------------------------------- plan : mesures, objets racine, unités, quadtree
Mi = collections.namedtuple("Mi", "prims cles imgs tri lo hi poids")


class Inst:
    __slots__ = ("node", "mesh", "lo", "hi", "centre", "tri", "racine")


class Racine:
    __slots__ = ("id", "nodes", "insts", "cles", "imgs", "tri", "lo", "hi", "centre", "etendue", "poids", "skin", "entier", "terrain")


class Unite:
    __slots__ = ("racine", "node", "entier", "cles", "imgs", "tri", "cx", "cz", "ninst", "nom", "etendue")


class Tuile:
    def __init__(self, niveau, i, j, units):
        self.niveau, self.i, self.j, self.units = niveau, i, j, units
        self.nom = f"T_{niveau}_{i}_{j}"


def compiler_exclusions(motifs):
    """Expressions de --exclude compilées (insensibles à la casse) ; message clair si l'une est invalide."""
    res = []
    for m in motifs:
        try:
            res.append(re.compile(m, re.IGNORECASE))
        except re.error as e:
            raise ErreurGlb(_tr("py.glb2tiles.expression_reguliere_invalide_pour_exclure_0", m, e))
    return res


class Params:
    """Paramètres du découpage (les poids sont convertis en octets)."""

    def __init__(self, budget=32.0, budget_tri=1500000, cote_min=16.0, entier_poids=16.0, entier_etendue=256.0,
                 seuil=150.0, seuil_tri=3000000, aberrant=1000.0, bloc=256.0, exclure=(), exclure_max_tri=24, exclure_max_meshes=1, references=True):
        self.budget_mo, self.budget = budget, budget * MO
        self.budget_tri = budget_tri
        self.cote_min = max(cote_min, 1e-3)
        self.entier_poids_mo, self.entier_poids = entier_poids, entier_poids * MO
        self.entier_etendue = entier_etendue
        self.seuil_mo, self.seuil_tri = seuil, seuil_tri
        self.aberrant = aberrant
        self.bloc = bloc
        self.exclure_motifs = list(exclure)             # expressions régulières (texte) ; vérifiées par compiler_exclusions
        self.exclure = compiler_exclusions(self.exclure_motifs)
        self.exclure_max_tri, self.exclure_max_meshes = exclure_max_tri, exclure_max_meshes
        self.references = references                    # v32 : extras.ref / extras.box sur chaque nœud copié (zones liées en mode tuiles)

    def dict(self):
        return {"budgetMB": self.budget_mo, "budgetTriangles": self.budget_tri, "minCell": self.cote_min,
                "wholeWeightMB": self.entier_poids_mo, "wholeExtent": self.entier_etendue,
                "thresholdMB": self.seuil_mo, "thresholdTriangles": self.seuil_tri, "outlier": self.aberrant}


class Plan:
    def __init__(self, glb, P):
        self.glb, self.P = glb, P
        g = glb.g
        self.nodes, self.meshes = g.get("nodes", []), g.get("meshes", [])
        self.mats, self.texs = g.get("materials", []), g.get("textures", [])
        self.avertissements = []
        self.parent = {}
        for i, n in enumerate(self.nodes):
            for c in n.get("children", []):
                self.parent.setdefault(c, i)
        scs = g.get("scenes", [])
        if len(scs) > 1:
            self.avertissements.append(_tr("py.glb2tiles.0_scenes_seule_la_scene_1", len(scs), g.get('scene', 0)))
        sc = scs[g.get("scene", 0)] if scs else {}
        self.racines_ids = sc.get("nodes") if scs else [i for i in range(len(self.nodes)) if i not in self.parent]
        self.cb = {}            # clé (primitive, skin) -> octets compactés
        self.prims = {}         # clé de primitive -> Prim
        self.img_oct = [self.glb.vue(i["bufferView"]).get("byteLength", 0) + 3 & ~3 if "bufferView" in i else 0
                        for i in g.get("images", [])]
        for i in g.get("images", []):
            if "bufferView" not in i and not str(i.get("uri", "")).startswith("data:"):
                raise ErreurGlb(_tr("py.glb2tiles.image_externe_uri_non_geree_seuls"))
        self._imgs_mat = {}
        self.parcourir()
        self.analyser_prims()
        self.construire_racines()
        self.construire_unites()
        self.verifier_images()
        self.calculer_references()

    # -- parcours de la scène
    def parcourir(self):
        S = stats()
        self.noeuds_racine = {}
        self.monde = {}
        ignores = set()
        vus = set()
        ident = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        for r in self.racines_ids:
            lst = []
            pile = [(r, ident)]
            while pile:
                ni, pm = pile.pop()
                if ni in vus:
                    continue
                vus.add(ni)
                n = self.nodes[ni]
                m = S.mat_mul(pm, S.mat_noeud(n))
                lst.append(ni)
                if "mesh" in n:
                    self.monde[ni] = m
                if "camera" in n or "extensions" in n:
                    ignores.add(ni)
                for c in reversed(n.get("children", [])):
                    pile.append((c, m))
            self.noeuds_racine[r] = lst
        if ignores:
            self.avertissements.append(_tr("py.glb2tiles.0_nud_s_avec_camera_ou", len(ignores)))

    def textures_materiau(self, mi):
        res = self._imgs_mat.get(mi)
        if res is None:
            ts = set()
            parcourir_textures(self.mats[mi], lambda d: ts.add(d["index"]))
            res = set()
            for t in ts:
                if 0 <= t < len(self.texs):
                    res.update(images_de_texture(self.texs[t]))
            self._imgs_mat[mi] = res
        return res

    # -- primitives
    def analyser_prims(self):
        ext_prim = False
        self.mesh_prims = {}
        for ni in self.monde:
            m = self.nodes[ni]["mesh"]
            if m in self.mesh_prims:
                continue
            if not (0 <= m < len(self.meshes)):
                raise ErreurGlb(_tr("py.glb2tiles.nud_0_mesh_1_inexistant", ni, m))
            lst = []
            for pr in self.meshes[m].get("primitives", []):
                if "extensions" in pr:
                    ext_prim = True
                if "POSITION" not in pr.get("attributes", {}):
                    raise ErreurGlb(_tr("py.glb2tiles.mesh_0_primitive_sans_position_non", m))
                lst.append((cle_prim(pr), pr))
            self.mesh_prims[m] = lst
        if ext_prim:
            self.avertissements.append(_tr("py.glb2tiles.des_primitives_portent_des_extensions_elles"))
        cles = []
        vu = set()
        for lst in self.mesh_prims.values():
            for k, _ in lst:
                if k not in vu:
                    vu.add(k)
                    cles.append(k)
        log(_tr("py.glb2tiles.analyse_0_primitives_distinctes_a_mesurer", len(cles)))
        pg = Progres("primitives", len(cles))
        self.positions_lues = 0
        for n, k in enumerate(cles):
            self.prims[k] = self.analyser_prim(k)
            self.cb[k] = self.prims[k].cbytes
            pg.avance(n + 1)
        # meshes
        self.mesh_info = {}
        for m, lst in self.mesh_prims.items():
            cl, im, tri = [], set(), 0
            lo, hi = [1e30] * 3, [-1e30] * 3
            for k, pr in lst:
                p = self.prims[k]
                if p.vide:
                    continue
                cl.append(k)
                tri += p.tri
                for q in range(3):
                    lo[q], hi[q] = min(lo[q], p.lo[q]), max(hi[q], p.hi[q])
                if isinstance(pr.get("material"), int) and 0 <= pr["material"] < len(self.mats):
                    im |= self.textures_materiau(pr["material"])
            if cl:
                poids = sum(self.cb[k] for k in set(cl)) + sum(self.img_oct[i] for i in im)
                self.mesh_info[m] = Mi(cl, frozenset(cl), frozenset(im), tri, lo, hi, poids)

    def analyser_prim(self, key):
        glb = self.glb
        mode, ai, attrs, tg = key
        d = dict(attrs)
        pa = glb.acc(d["POSITION"])
        p = Prim()
        p.key, p.mode, p.indices, p.attrs, p.targets = key, mode, ai, d, [dict(t) for t in tg]
        for ac in list(d.values()) + [v for t in p.targets for v in t.values()]:
            if glb.acc(ac).count != pa.count:
                raise ErreurGlb(_tr("py.glb2tiles.primitive_les_attributs_n_ont_pas", pa.count, ac))
        mq = None
        if ai is None:
            p.n_idx = p.used = pa.count
            p.imin, p.imax = 0, pa.count - 1
        else:
            ia = glb.acc(ai)
            p.n_idx = ia.count
            mq = Marques()
            for bloc in glb.blocs_indices(ai):
                mq.ajouter(bloc)
            p.used = mq.compter()
            p.imin, p.imax = (mq.imin, mq.imax) if p.used else (0, -1)
            if p.used and p.imax >= pa.count:
                raise ErreurGlb(_tr("py.glb2tiles.accessor_0_un_indice_depasse_le", ai, pa.count))
        p.tri = tri_mode(mode, p.n_idx)
        p.vide = p.used == 0
        p.lo = p.hi = None
        p.cbytes = 0
        if p.vide:
            return p
        p.lo, p.hi = self.boite_prim(p, pa, mq)
        o = 0
        for ac in list(d.values()) + [v for t in p.targets for v in t.values()]:
            o += p.used * es_sortie(glb.acc(ac).es)
        if ai is not None:
            o += (p.n_idx * taille_indices(p.used) + 3) & ~3
        p.cbytes = o
        return p

    def boite_prim(self, p, pa, mq):
        """Boîte locale exacte des sommets utilisés (accessor min/max seulement s'il est exact)."""
        glb = self.glb
        if pa.mn and pa.mx and len(pa.mn) >= 3 and len(pa.mx) >= 3 and p.used == pa.count:
            return [float(v) for v in pa.mn[:3]], [float(v) for v in pa.mx[:3]]
        if pa.ncomp < 3 or pa.stride % TAILLE[pa.comp]:
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_positions_non_gerees", pa.i))
        lo, hi = [math.inf] * 3, [-math.inf] * 3
        se = pa.stride // TAILLE[pa.comp]
        lignes = max(1, BLOC_LECTURE // max(pa.stride, 1))
        r = p.imin
        while r <= p.imax:
            n = min(lignes, p.imax - r + 1)
            raw = bytes(glb.rangee(pa, r, n)) + bytes(pa.stride - pa.es)
            self.positions_lues += len(raw)
            arr = array.array(CODE[pa.comp])
            arr.frombytes(raw)
            fl = mq.flags[r - mq.base:r - mq.base + n] if mq is not None else None
            for k in range(3):
                col = arr[k::se]
                if fl is not None:
                    col = list(itertools.compress(col, fl))
                if len(col):
                    lo[k] = min(lo[k], min(col))
                    hi[k] = max(hi[k], max(col))
            r += n
        return ([decode_norm(v, pa.comp, pa.norm) for v in lo], [decode_norm(v, pa.comp, pa.norm) for v in hi])

    # -- objets racine
    def construire_racines(self):
        S = stats()
        self.racines = []
        self.insts = []
        self.exclus = []        # objets racine retirés par --exclude : {"nom", "tri", "meshes", "cles", "imgs"}
        self.gardes = 0         # noms qui correspondent à --exclude mais conservés par les garde-fous
        for r in self.racines_ids:
            rac = Racine()
            rac.id, rac.nodes = r, self.noeuds_racine[r]
            rac.insts = []
            rac.skin = False
            ex = self.nodes[r].get("extras")
            rac.terrain = isinstance(ex, dict) and bool(ex.get("terrain"))      # pièce de terrain d'oar2glb.py (extras.terrain)
            cles, imgs = set(), set()
            for ni in rac.nodes:
                n = self.nodes[ni]
                if "mesh" not in n:
                    continue
                mi = self.mesh_info.get(n["mesh"])
                if mi is None:
                    continue
                it = Inst()
                it.node, it.mesh, it.tri, it.racine = ni, n["mesh"], mi.tri, rac
                pts = S.coins_monde(self.monde[ni], mi.lo, mi.hi)
                it.lo = [min(c[k] for c in pts) for k in range(3)]
                it.hi = [max(c[k] for c in pts) for k in range(3)]
                it.centre = [sum(c[k] for c in pts) / 8 for k in range(3)]
                rac.insts.append(it)
                cles |= mi.cles
                imgs |= mi.imgs
                if isinstance(n.get("skin"), int):
                    rac.skin = True
                    self.cle_skin(n["skin"], cles)
            if not rac.insts:
                continue
            rac.cles, rac.imgs = frozenset(cles), frozenset(imgs)
            rac.tri = sum(i.tri for i in rac.insts)
            if self.P.exclure:
                # décision sur le nom, le nombre de triangles et le nombre de meshes de l'objet racine ; JAMAIS sur l'étendue
                # (la boîte d'un petit mesh qui partage un tampon de sommets est gonflée)
                nd = self.nodes[r]
                nom = nd.get("name") or (self.meshes[nd["mesh"]].get("name") if "mesh" in nd else "") or ""
                if any(rx.search(nom) for rx in self.P.exclure):
                    if rac.tri <= self.P.exclure_max_tri and len(rac.insts) <= self.P.exclure_max_meshes:
                        self.exclus.append({"nom": nom or _tr("py.glb2tiles.nud_0", r), "tri": rac.tri, "meshes": len(rac.insts), "cles": rac.cles, "imgs": rac.imgs})
                        continue
                    self.gardes += 1
            rac.lo = [min(i.lo[k] for i in rac.insts) for k in range(3)]
            rac.hi = [max(i.hi[k] for i in rac.insts) for k in range(3)]
            rac.centre = [(rac.lo[k] + rac.hi[k]) / 2 for k in range(3)]
            rac.etendue = max(rac.hi[0] - rac.lo[0], rac.hi[2] - rac.lo[2])
            rac.poids = sum(self.cb[k] for k in rac.cles) + sum(self.img_oct[i] for i in rac.imgs)
            rac.entier = rac.skin or (rac.poids <= self.P.entier_poids and rac.etendue <= self.P.entier_etendue)
            self.racines.append(rac)
            self.insts.extend(rac.insts)
        # octets gagnés : géométrie et images qu'aucun objet conservé n'utilise
        ks, im = set(), set()
        for rac in self.racines:
            ks |= rac.cles
            im |= rac.imgs
        ek, ei = set(), set()
        for x in self.exclus:
            ek |= x["cles"]
            ei |= x["imgs"]
        self.octets_exclus = sum(self.cb[k] for k in ek - ks) + sum(self.img_oct[i] for i in ei - im)
        # géométrie et images des exclus que des objets conservés utilisent aussi (même primitive, même texture) : retirer l'objet ne les économise pas
        self.octets_partages = sum(self.cb[k] for k in ek & ks) + sum(self.img_oct[i] for i in ei & im)

    def nom_noeud(self, ni):
        """Nom d'un nœud pour les références : son nom, sinon celui de son mesh (comme les objets nommés que voit le chargeur)."""
        n = self.nodes[ni]
        nm = n.get("name") or ""
        if not nm and isinstance(n.get("mesh"), int) and 0 <= n["mesh"] < len(self.meshes):
            nm = self.meshes[n["mesh"]].get("name") or ""
        return re.sub(r"[\x00-\x1f]", "", str(nm))

    def calculer_references(self):
        """Référence stable de chaque nœud dans le GLB ENTIER (v32), même règle que resolveMeshRef de core.js : le nom s'il est unique, sinon
        « nom#index », index = rang du nœud parmi les nœuds de ce nom dans l'ordre de parcours (pré-ordre, enfants dans l'ordre du fichier).
        Les nœuds exclus par --exclude comptent (la référence ne dépend pas de ce qu'on retire). Boîte (monde) de l'objet entier : union des
        boîtes de toutes les instances de ses descendants, y compris celles qui sont dans d'autres tuiles."""
        self.ref_de, self.box_de = {}, {}
        if not self.P.references:
            return
        ordre = [ni for r in self.racines_ids for ni in self.noeuds_racine.get(r, ())]
        noms = {ni: self.nom_noeud(ni) for ni in ordre}
        total = collections.Counter(nm for nm in noms.values() if nm)
        vu = collections.Counter()
        for ni in ordre:
            nm = noms[ni]
            if not nm:
                continue
            ref = nm if total[nm] == 1 else f"{nm}#{vu[nm]}"
            vu[nm] += 1
            if len(ref) <= 200:
                self.ref_de[ni] = ref
        for it in self.insts:
            n = it.node
            while n is not None:
                b = self.box_de.get(n)
                if b is None:
                    self.box_de[n] = [list(it.lo), list(it.hi)]
                else:
                    for k in range(3):
                        b[0][k] = min(b[0][k], it.lo[k])
                        b[1][k] = max(b[1][k], it.hi[k])
                n = self.parent.get(n)
        self.nb_refs, self.nb_partages = len(self.ref_de), sum(1 for nm, c in total.items() if c > 1)

    def est_terrain(self, rac):
        return rac.terrain

    def cle_skin(self, si, cles):
        skins = self.glb.g.get("skins", [])
        if not (0 <= si < len(skins)):
            raise ErreurGlb(_tr("py.glb2tiles.skin_0_inexistant", si))
        k = ("skin", si)
        if k not in self.cb:
            ib = skins[si].get("inverseBindMatrices")
            self.cb[k] = self.glb.acc(ib).count * 64 if ib is not None else 0
        cles.add(k)

    def construire_unites(self):
        self.unites = []
        for rac in self.racines:
            if rac.entier:
                u = Unite()
                u.racine, u.node, u.entier, u.cles, u.imgs, u.tri = rac, None, True, rac.cles, rac.imgs, rac.tri
                u.cx, u.cz, u.ninst, u.etendue = rac.centre[0], rac.centre[2], len(rac.insts), rac.etendue
                u.nom = self.nodes[rac.id].get("name") or _tr("py.glb2tiles.nud_0", rac.id)
                self.unites.append(u)
            else:
                for it in rac.insts:
                    mi = self.mesh_info[it.mesh]
                    u = Unite()
                    u.racine, u.node, u.entier, u.cles, u.imgs, u.tri = rac, it.node, False, mi.cles, mi.imgs, it.tri
                    u.cx, u.cz, u.ninst = it.centre[0], it.centre[2], 1
                    u.etendue = max(it.hi[0] - it.lo[0], it.hi[2] - it.lo[2])
                    u.nom = self.nodes[it.node].get("name") or self.meshes[it.mesh].get("name") or _tr("py.glb2tiles.nud_0", it.node)
                    self.unites.append(u)

    def donnees_image(self, ii):
        """Octets d'une image (bufferView lu dans le GLB, ou adresse data:) ; None si l'adresse data: est illisible."""
        src = self.glb.g["images"][ii]
        if "bufferView" in src:
            bv = self.glb.vue(src["bufferView"])
            return self.glb.lire(bv.get("byteOffset", 0), bv.get("byteLength", 0))
        try:
            return base64.b64decode(src["uri"].split(",", 1)[1], validate=False) if ";base64," in src["uri"][:80] else None
        except (ValueError, IndexError):
            return b""

    def verifier_images(self):
        """Images embarquées vides ou invalides (0 octet, autre format que PNG/JPEG/WebP, tronquées) parmi celles que les unités utilisent.
        img_ko = leurs numéros ; elles seront remplacées par un petit PNG gris dans chaque tuile qui les utilise."""
        utilisees = sorted({i for u in self.unites for i in u.imgs})
        self.img_ko = set()
        if not utilisees:
            return
        pg = Progres("images", len(utilisees))
        for n, ii in enumerate(utilisees):
            src = self.glb.g["images"][ii]
            if "bufferView" in src:
                bv = self.glb.vue(src["bufferView"])
                off, ln = bv.get("byteOffset", 0), bv.get("byteLength", 0)
                ok = image_valide(lambda o, k: self.glb.lire(off + o, k), ln)
            else:
                d = self.donnees_image(ii)
                ok = d is None or image_valide(lambda o, k: d[o:o + k], len(d))
            if not ok:
                self.img_ko.add(ii)
            pg.avance(n + 1)

    def images_remplacees(self, tuiles):
        """(images distinctes remplacées, occurrences) : une occurrence = une image invalide dans une tuile (elle y serait écrite une fois)."""
        tous = set()
        occ = 0
        for t in tuiles:
            im = {i for u in t.units for i in u.imgs} & self.img_ko
            tous |= im
            occ += len(im)
        return len(tous), occ

    # -- poids d'un groupe d'unités
    def poids(self, units):
        ks, im, tri = set(), set(), 0
        for u in units:
            ks |= u.cles
            im |= u.imgs
            tri += u.tri
        geo = sum(map(self.cb.__getitem__, ks))
        img = sum(self.img_oct[i] for i in im)
        return geo, img, tri

    # -- quadtree adaptatif sur X,Z
    def decouper(self):
        P = self.P
        units = self.unites
        if not units:
            return []
        x0, z0 = min(u.cx for u in units), min(u.cz for u in units)
        cote = max(max(u.cx for u in units) - x0, max(u.cz for u in units) - z0, 1e-6)
        res = []

        def rec(niveau, i, j, ox, oz, c, liste):
            geo, img, tri = self.poids(liste)
            if (geo + img > P.budget or tri > P.budget_tri) and c > P.cote_min and len(liste) > 1 and niveau < 40:
                demi = c / 2
                enf = {}
                for u in liste:
                    a = 1 if u.cx >= ox + demi else 0
                    b = 1 if u.cz >= oz + demi else 0
                    enf.setdefault((a, b), []).append(u)
                for (a, b), sous in sorted(enf.items()):
                    rec(niveau + 1, 2 * i + a, 2 * j + b, ox + a * demi, oz + b * demi, demi, sous)
            else:
                res.append(Tuile(niveau, i, j, liste))

        rec(0, 0, 0, x0, z0, cote, list(units))
        res.sort(key=lambda t: (t.niveau, t.i, t.j))
        return res

    def stats_tuiles(self, tuiles):
        out = []
        for t in tuiles:
            geo, img, tri = self.poids(t.units)
            out.append((geo, img, tri))
        return out

    def hors_budget(self, tuiles):
        """Avertissements pour les tuiles qui dépassent le budget (mesh unique trop lourd, cellule minimale atteinte)."""
        P = self.P
        res = []
        for t in tuiles:
            geo, img, tri = self.poids([*t.units])
            if geo + img <= P.budget and tri <= P.budget_tri:
                continue
            lourds = sorted(t.units, key=lambda u: -(sum(self.cb[k] for k in u.cles) + sum(self.img_oct[i] for i in u.imgs)))[:3]
            noms = "; ".join(f"« {u.nom} » {u.etendue:.0f} m, "
                             f"{mo(sum(self.cb[k] for k in u.cles) + sum(self.img_oct[i] for i in u.imgs)):.1f} Mo" for u in lourds)
            res.append(_tr("py.glb2tiles.tuile_0_hors_budget_1_1f", t.nom, mo(geo + img), fmt(tri), noms))
        return res

    def aberrantes(self):
        """Instances très éloignées du centre médian ou d'étendue démesurée."""
        if not self.insts:
            return [], (0, 0)
        mx = statistics.median(i.centre[0] for i in self.insts)
        mz = statistics.median(i.centre[2] for i in self.insts)
        lst = []
        for it in self.insts:
            d = math.hypot(it.centre[0] - mx, it.centre[2] - mz)
            ext = max(it.hi[k] - it.lo[k] for k in range(3))
            lst.append((d, ext, it))
        return lst, (mx, mz)


# ---------------------------------------------------------------- écriture d'une tuile
class Assemblage:
    """Construit un GLB de tuile en mémoire : nœuds, meshes, matériaux, textures, images, accessors."""

    def __init__(self, plan):
        self.plan, self.glb = plan, plan.glb
        self.g = plan.glb.g
        self.parts = []
        self.bin_len = 0
        self.views, self.accessors = [], []
        self.o_geo = self.o_img = 0
        self.gris, self.nb_remplacees = None, 0
        self.prim_out = {}
        self.mesh_idx, self.mat_idx, self.tex_idx, self.img_idx, self.samp_idx, self.skin_idx = {}, {}, {}, {}, {}, {}
        self.meshes_o, self.mats_o, self.texs_o, self.imgs_o, self.samps_o, self.skins_o = [], [], [], [], [], []

    def vue(self, data, cible=None, stride=None, geo=True):
        if self.bin_len % 4:
            pad = 4 - self.bin_len % 4
            self.parts.append(bytes(pad))
            self.bin_len += pad
        v = {"buffer": 0, "byteOffset": self.bin_len, "byteLength": len(data)}
        if stride:
            v["byteStride"] = stride
        if cible:
            v["target"] = cible
        self.parts.append(data)
        self.bin_len += len(data)
        reel = (len(data) + 3) & ~3
        if geo:
            self.o_geo += reel
        else:
            self.o_img += reel
        self.views.append(v)
        return len(self.views) - 1

    def accessor(self, vue, comp, count, typ, norm=False, mn=None, mx=None):
        d = {"bufferView": vue, "componentType": comp, "count": count, "type": typ}
        if norm:
            d["normalized"] = True
        if mn is not None:
            d["min"], d["max"] = mn, mx
        self.accessors.append(d)
        return len(self.accessors) - 1

    # -- compactage d'une primitive
    def prim(self, key):
        r = self.prim_out.get(key)
        if r is not None:
            return r
        glb = self.glb
        p = self.plan.prims[key]
        idx = None
        rel = None
        if p.indices is None:
            used, contiguo, imin = p.used, True, 0
            nouveau = None
        else:
            ia = glb.acc(p.indices)
            code = CODE[ia.comp]
            idx = array.array(code)
            mq = Marques()
            for bloc in glb.blocs_indices(p.indices):
                mq.ajouter(bloc)
                idx.extend(bloc)
            used, imin = mq.compter(), mq.imin
            contiguo = used == len(mq.flags)
            sortie = "H" if taille_indices(used) == 2 else U32
            if contiguo:
                if imin:
                    nouveau = array.array(sortie, map(imin.__rsub__, idx))
                elif sortie != code:
                    nouveau = array.array(sortie, idx)
                else:
                    nouveau = idx
            else:
                rel = list(itertools.compress(range(len(mq.flags)), mq.flags))
                remap = array.array(U32, bytes(4 * len(mq.flags)))
                collections.deque(map(remap.__setitem__, rel, range(len(rel))), maxlen=0)
                src = map(imin.__rsub__, idx) if imin else idx
                nouveau = array.array(sortie, map(remap.__getitem__, src))
            del idx
        res = {"targets": [], "indices": None}
        res["attrs"] = {nom: self.attribut(ai, nom == "POSITION", imin, used, contiguo, rel) for nom, ai in p.attrs.items()}
        for t in p.targets:
            res["targets"].append({nom: self.attribut(ai, False, imin, used, contiguo, rel) for nom, ai in t.items()})
        if nouveau is not None:
            v = self.vue(nouveau.tobytes(), 34963)
            res["indices"] = self.accessor(v, 5123 if nouveau.typecode == "H" else 5125, len(nouveau), "SCALAR")
        self.prim_out[key] = res
        return res

    def attribut(self, ai, avec_minmax, imin, used, contiguo, rel):
        glb = self.glb
        a = glb.acc(ai)
        es, so = a.es, es_sortie(a.es)
        n = used if rel is None else (rel[-1] + 1 if rel else 0)     # lignes de la plage lue
        raw = glb.rangee(a, imin, n)
        if contiguo and a.stride == so == es:
            data = bytes(raw[:used * es])
        else:
            mv = memoryview(raw)
            offs = range(0, used * a.stride, a.stride) if rel is None else [r * a.stride for r in rel]
            if so == es:
                data = b"".join([mv[o:o + es] for o in offs])
            else:
                pad = bytes(so - es)
                data = b"".join([bytes(mv[o:o + es]) + pad for o in offs])
        mm = minmax_donnees(data, a, so) if avec_minmax else None
        v = self.vue(data, 34962, stride=so if so != es else None)
        return self.accessor(v, a.comp, used, a.type, a.norm, mm[0] if mm else None, mm[1] if mm else None)

    # -- mesh, matériau, texture, image, skin
    def mesh(self, m):
        if m in self.mesh_idx:
            return self.mesh_idx[m]
        src = self.plan.meshes[m]
        prims = []
        for pr in src.get("primitives", []):
            key = cle_prim(pr)
            if self.plan.prims[key].vide:
                continue
            o = self.prim(key)
            d = {"attributes": dict(o["attrs"])}
            if o["indices"] is not None:
                d["indices"] = o["indices"]
            if pr.get("mode", 4) != 4:
                d["mode"] = pr["mode"]
            if isinstance(pr.get("material"), int) and 0 <= pr["material"] < len(self.plan.mats):
                d["material"] = self.materiau(pr["material"])
            if o["targets"]:
                d["targets"] = [dict(t) for t in o["targets"]]
            if "extras" in pr:
                d["extras"] = pr["extras"]
            prims.append(d)
        if not prims:
            self.mesh_idx[m] = None
            return None
        d = {"primitives": prims}
        for k in ("name", "weights", "extras"):
            if k in src:
                d[k] = src[k]
        self.meshes_o.append(d)
        self.mesh_idx[m] = len(self.meshes_o) - 1
        return self.mesh_idx[m]

    def materiau(self, mi):
        if mi in self.mat_idx:
            return self.mat_idx[mi]
        d = json.loads(json.dumps(self.plan.mats[mi]))

        def remap(t):
            t["index"] = self.texture(t["index"])
        parcourir_textures(d, remap)
        self.mats_o.append(d)
        self.mat_idx[mi] = len(self.mats_o) - 1
        return self.mat_idx[mi]

    def texture(self, ti):
        if ti in self.tex_idx:
            return self.tex_idx[ti]
        if not (0 <= ti < len(self.plan.texs)):
            raise ErreurGlb(_tr("py.glb2tiles.texture_0_inexistante", ti))
        d = json.loads(json.dumps(self.plan.texs[ti]))
        if isinstance(d.get("source"), int):
            d["source"] = self.image(d["source"])
        for e in d.get("extensions", {}).values():
            if isinstance(e, dict) and isinstance(e.get("source"), int):
                e["source"] = self.image(e["source"])
        if isinstance(d.get("sampler"), int):
            si = d["sampler"]
            if si not in self.samp_idx:
                self.samps_o.append(self.g["samplers"][si])
                self.samp_idx[si] = len(self.samps_o) - 1
            d["sampler"] = self.samp_idx[si]
        self.texs_o.append(d)
        self.tex_idx[ti] = len(self.texs_o) - 1
        return self.tex_idx[ti]

    def image(self, ii):
        if ii in self.img_idx:
            return self.img_idx[ii]
        if ii in self.plan.img_ko:
            # image vide, d'un autre format ou tronquée : un seul PNG gris par tuile, partagé par toutes ses références
            if self.gris is None:
                self.imgs_o.append({"name": "image-remplacee", "mimeType": "image/png", "bufferView": self.vue(png_gris(), geo=False)})
                self.gris = len(self.imgs_o) - 1
            self.img_idx[ii] = self.gris
            self.nb_remplacees += 1
            return self.gris
        src = self.g["images"][ii]
        d = {k: v for k, v in src.items() if k in ("name", "mimeType", "extras")}
        if "bufferView" in src:
            bv = self.glb.vue(src["bufferView"])
            data = self.glb.lire(bv.get("byteOffset", 0), bv.get("byteLength", 0))
            d["bufferView"] = self.vue(data, geo=False)
        else:
            d["uri"] = src["uri"]
        self.imgs_o.append(d)
        self.img_idx[ii] = len(self.imgs_o) - 1
        return self.img_idx[ii]

    def skin(self, si, new_id):
        if si in self.skin_idx:
            return self.skin_idx[si]
        src = self.g["skins"][si]
        d = {"joints": [new_id[j] for j in src["joints"]]}
        if isinstance(src.get("skeleton"), int) and src["skeleton"] in new_id:
            d["skeleton"] = new_id[src["skeleton"]]
        ib = src.get("inverseBindMatrices")
        if ib is not None:
            a = self.glb.acc(ib)
            raw = self.glb.rangee(a, 0, a.count)
            mv = memoryview(raw)
            data = b"".join([mv[o:o + a.es] for o in range(0, a.count * a.stride, a.stride)]) if a.stride != a.es else bytes(raw)
            d["inverseBindMatrices"] = self.accessor(self.vue(data), a.comp, a.count, a.type)
        if "name" in src:
            d["name"] = src["name"]
        self.skins_o.append(d)
        self.skin_idx[si] = len(self.skins_o) - 1
        return self.skin_idx[si]


def ecrire_tuile(plan, tuile, chemin):
    """Écrit le GLB d'une tuile ; renvoie sa fiche pour X.tiles.json."""
    nodes = plan.nodes
    asm = Assemblage(plan)
    affectes, avec_mesh, insts = set(), [], []
    for u in tuile.units:
        if u.entier:
            affectes.update(u.racine.nodes)
            insts.extend(u.racine.insts)
        else:
            affectes.add(u.node)
            insts.extend(i for i in u.racine.insts if i.node == u.node)
    avec_mesh = {i.node for i in insts}
    ens = set(affectes)
    for n in affectes:                         # joints d'un skin : dans la tuile, même hors de l'objet
        si = nodes[n].get("skin")
        if isinstance(si, int):
            sk = plan.glb.g["skins"][si]
            ens.update(j for j in sk["joints"])
            if isinstance(sk.get("skeleton"), int):
                ens.add(sk["skeleton"])
    for n in list(ens):                        # ancêtres : transformations d'origine conservées
        p = plan.parent.get(n)
        while p is not None and p not in ens:
            ens.add(p)
            p = plan.parent.get(p)
    racines = sorted(n for n in ens if plan.parent.get(n) not in ens)
    ordre = []
    pile = list(reversed(racines))
    while pile:
        n = pile.pop()
        ordre.append(n)
        pile.extend(reversed([c for c in nodes[n].get("children", []) if c in ens]))
    new_id = {n: k for k, n in enumerate(ordre)}
    nodes_o = []
    for n in ordre:
        src = nodes[n]
        d = {}
        if "name" in src:
            d["name"] = src["name"]
        for k in ("matrix", "translation", "rotation", "scale", "weights", "extras"):
            if k in src:
                d[k] = src[k]
        ref = plan.ref_de.get(n)
        if ref is not None and isinstance(d.get("extras", {}), dict):
            # v32 : référence stable dans le modèle d'origine et boîte monde de l'objet ENTIER (même quand il est réparti sur plusieurs tuiles)
            d["extras"] = dict(d.get("extras", {}), ref=ref)
            b = plan.box_de.get(n)
            if b is not None:
                d["extras"]["box"] = [round(v, 3) for v in b[0] + b[1]]
        if n in avec_mesh:
            mi = asm.mesh(src["mesh"])
            if mi is not None:
                d["mesh"] = mi
        if n in affectes and isinstance(src.get("skin"), int) and "mesh" in d:
            d["skin"] = asm.skin(src["skin"], new_id)
        ch = [new_id[c] for c in src.get("children", []) if c in ens]
        if ch:
            d["children"] = ch
        nodes_o.append(d)
    js = {"asset": {"version": "2.0", "generator": f"glb2tiles {VERSION}"}, "scene": 0,
          "scenes": [{"nodes": [new_id[n] for n in racines]}], "nodes": nodes_o}
    for nom, lst in (("meshes", asm.meshes_o), ("materials", asm.mats_o), ("textures", asm.texs_o), ("samplers", asm.samps_o),
                     ("images", asm.imgs_o), ("skins", asm.skins_o), ("accessors", asm.accessors), ("bufferViews", asm.views)):
        if lst:
            js[nom] = lst
    present = set()
    extensions_presentes(js, present)
    for cle in ("extensionsUsed", "extensionsRequired"):
        liste = [e for e in plan.glb.g.get(cle, []) if e in present]
        if liste:
            js[cle] = liste
    total_bin = (asm.bin_len + 3) & ~3
    js["buffers"] = [{"byteLength": total_bin}]
    jb = json.dumps(js, separators=(",", ":")).encode("utf-8")
    jb += b" " * (-len(jb) % 4)
    total = 12 + 8 + len(jb) + 8 + total_bin
    if total > LIMITE_GLB:
        raise ErreurGlb(_tr("py.glb2tiles.tuile_0_1_2f_go_au", tuile.nom, total / 1024 ** 3))
    tmp = str(chemin) + ".tmp"
    with open(tmp, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total))
        f.write(struct.pack("<II", len(jb), 0x4E4F534A))
        f.write(jb)
        f.write(struct.pack("<II", total_bin, 0x004E4942))
        for part in asm.parts:
            f.write(part)
        f.write(bytes(total_bin - asm.bin_len))
    os.replace(tmp, chemin)
    lo = [min(i.lo[k] for i in insts) for k in range(3)]
    hi = [max(i.hi[k] for i in insts) for k in range(3)]
    return {"file": None, "level": tuile.niveau, "i": tuile.i, "j": tuile.j, "min": lo, "max": hi,
            "instances": len(insts), "triangles": sum(i.tri for i in insts), "bytes": total,
            "geometryBytes": asm.o_geo, "imageBytes": asm.o_img, "replacedImages": asm.nb_remplacees}


# ---------------------------------------------------------------- rapports
def quantile(v, q):
    v = sorted(v)
    return v[min(len(v) - 1, max(0, math.ceil(q * len(v)) - 1))] if v else 0


def recommandation(glb, plan, tuiles):
    P = plan.P
    tri = sum(i.tri for i in plan.insts)
    taille = glb.taille - getattr(plan, "octets_exclus", 0)        # sans les objets exclus
    if mo(taille) <= P.seuil_mo and tri <= P.seuil_tri:
        return False, (_tr("py.glb2tiles.recommandation_pas_de_decoupage_necessaire_0", mo(taille), P.seuil_mo, fmt(tri), fmt(P.seuil_tri)))
    geo_u = sum(plan.cb[k] for k in {k for u in plan.unites for k in u.cles})
    st = plan.stats_tuiles(tuiles)
    dup = sum(s[0] for s in st) / geo_u if geo_u else 1.0
    return True, _tr("py.glb2tiles.recommandation_decouper_budget_0_g_mo", P.budget_mo, len(tuiles), virg(dup))


def lignes_exclusions(plan):
    """Récapitulatif de --exclude : nombre, 20 noms les plus fréquents, octets gagnés ; liste vide sans option."""
    P = plan.P
    if not P.exclure:
        return []
    out = [_tr("py.glb2tiles.objets_exclus_exclure_au_plus_0", P.exclure_max_tri, P.exclure_max_meshes, len(plan.exclus), fmt(sum(x['tri'] for x in plan.exclus)), fmt(plan.octets_exclus), mo(plan.octets_exclus))]
    if plan.exclus:
        out.append(_tr("py.glb2tiles.octets_des_exclus_qu_un_objet", fmt(plan.octets_partages), mo(plan.octets_partages)))
        if plan.octets_exclus == 0:
            out.append(_tr("py.glb2tiles.0_octet_gagne_toute_la_geometrie"))
    if plan.gardes:
        out.append(_tr("py.glb2tiles.0_objet_s_au_nom_correspondant", plan.gardes))
    for nom, n in collections.Counter(x["nom"] for x in plan.exclus).most_common(20):
        out.append(f"  - {n} x « {nom[:70]} »")
    return out


def ligne_images(plan, tuiles):
    """Images vides ou invalides remplacées par un PNG gris (une phrase)."""
    dist, occ = plan.images_remplacees(tuiles)
    return (_tr("py.glb2tiles.images_vides_ou_invalides_remplacees_par", GRIS_IMAGE, fmt(dist), fmt(occ)))


def rapport_analyse(glb, plan, tuiles):
    P = plan.P
    out = []
    out.append(_tr("py.glb2tiles.mesures_de_glb_stats"))
    out.extend(stats().rapport(glb.chemin, P.bloc, glb.g, glb.njson))
    out.append("")
    # meshes les plus lourds
    insts_mesh = collections.defaultdict(list)
    for it in plan.insts:
        insts_mesh[it.mesh].append(it)
    lourds = sorted(plan.mesh_info.items(), key=lambda kv: -sum(plan.cb[k] for k in set(kv[1].prims)))[:10]
    out.append(_tr("py.glb2tiles.les_10_meshes_les_plus_lourds"))
    for m, mi in lourds:
        o = sum(plan.cb[k] for k in set(mi.prims))
        its = insts_mesh.get(m, [])
        if its:
            e = its[0]
            dim = f"{e.hi[0] - e.lo[0]:.1f} x {e.hi[1] - e.lo[1]:.1f} x {e.hi[2] - e.lo[2]:.1f} m"
        else:
            dim = _tr("py.glb2tiles.sans_instance")
        nom = plan.meshes[m].get("name") or f"mesh {m}"
        out.append(_tr("py.glb2tiles.0_1_2f_mo_2_triangles", nom[:40], mo(o), fmt(mi.tri), dim, len(its)))
    # instances aberrantes
    lst, (mx, mz) = plan.aberrantes()
    out.append("")
    out.append(_tr("py.glb2tiles.les_10_instances_les_plus_eloignees", mx, mz))
    for d, ext, it in sorted(lst, key=lambda t: -t[0])[:10]:
        nom = plan.nodes[it.node].get("name") or _tr("py.glb2tiles.nud_0", it.node)
        out.append(_tr("py.glb2tiles.0_distance_1_0f_m_etendue", nom[:40], d, ext))
    # découpage prévu
    st = plan.stats_tuiles(tuiles)
    geo_u = sum(plan.cb[k] for k in {k for u in plan.unites for k in u.cles})
    img_u = sum(plan.img_oct[i] for i in {i for u in plan.unites for i in u.imgs})
    dup_g = sum(s[0] for s in st) / geo_u if geo_u else 1.0
    dup_i = sum(s[1] for s in st) / img_u if img_u else 1.0
    out.append("")
    out.append(_tr("py.glb2tiles.decoupage_prevu_budget_0_g_mo", P.budget_mo, fmt(P.budget_tri), P.cote_min))
    out.append(_tr("py.glb2tiles.tuiles_0_duplication_prevue_geometrie_1", len(tuiles), virg(dup_g), virg(dup_i)))
    if st:
        poids = [(s[0] + s[1]) / MO for s in st]
        tris = [s[2] for s in st]
        out.append(_tr("py.glb2tiles.poids_par_tuile_mo_mediane_0", quantile(poids, 0.5), quantile(poids, 0.9), max(poids)))
        out.append(_tr("py.glb2tiles.triangles_par_tuile_mediane_0_90", fmt(quantile(tris, 0.5)), fmt(quantile(tris, 0.9)), fmt(max(tris))))
    ent = sum(1 for r in plan.racines if r.entier)
    skin = sum(1 for r in plan.racines if r.skin)
    out.extend(lignes_exclusions(plan))
    out.append(ligne_images(plan, tuiles))
    out.append(_tr("py.glb2tiles.objets_racine_0_gardes_entiers_1", len(plan.racines), ent, skin, len(plan.racines) - ent))
    avert = plan.avertissements + signalements(plan) + plan.hors_budget(tuiles)
    if avert:
        out.append("Avertissements :")
        out.extend("  - " + a for a in avert)
    out.append(_tr("py.glb2tiles.lecture_0_octets_lus_sur_1", fmt(glb.octets_lus), fmt(glb.taille), fmt(glb.plus_grande_lecture), fmt(plan.positions_lues)))
    out.append("")
    out.append(recommandation(glb, plan, tuiles)[1])
    return out


def signalements(plan):
    """Valeurs aberrantes (distance au centre médian ou étendue au-delà de --outlier)."""
    lst, _ = plan.aberrantes()
    seuil = plan.P.aberrant
    mauvais = sorted([t for t in lst if t[0] > seuil or t[1] > seuil], key=lambda t: -max(t[0], t[1]))
    if not mauvais:
        return []
    ex = ", ".join(_tr("py.glb2tiles.0_1_0f_m_du_centre", (plan.nodes[t[2].node].get('name') or 'nœud ' + str(t[2].node))[:30], t[0], t[1]) for t in mauvais[:3])
    return [_tr("py.glb2tiles.0_instance_s_aberrante_s_a", len(mauvais), seuil, ex)]


# ---------------------------------------------------------------- vue d'ensemble (X.overview.glb)
# Une seule géométrie légère pour toute la région, sans image : un nœud par fichier de tuile (mêmes clés que X.tiles.json), pour que la
# coquille masque la partie d'une cellule dès que la tuile détaillée correspondante est affichée. Les couleurs sont des couleurs de sommets
# (COLOR_0) : un seul matériau, donc au plus un appel de dessin par tuile. Sans normales : la coquille (GLTFLoader) rend alors en ombrage plat.
# Chaque primitive UNIQUE est simplifiée une seule fois (regroupement de sommets sur une grille proportionnelle à sa boîte), puis recopiée
# avec la matrice de chaque instance. Le terrain est rééchantillonné à part sur un réseau régulier commun à toutes ses pièces.
OV_PAS_TERRAIN = 4.0
OV_SEUIL = 3.0
OV_SEUIL_MAX = 24.0
OV_RESOLUTION = 10
OV_BUDGET_MO = 25.0
OV_BUDGET_TRI = 1500000
OV_GRIS_DEFAUT = (0.8, 0.8, 0.8)
LUT_LIN = [(c / 255 / 12.92 if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4) for c in range(256)]


class ParamsOv:
    def __init__(self, budget_mo=OV_BUDGET_MO, budget_tri=OV_BUDGET_TRI, seuil=OV_SEUIL, seuil_max=OV_SEUIL_MAX, resolution=OV_RESOLUTION,
                 pas_terrain=OV_PAS_TERRAIN):
        self.budget_mo, self.budget = budget_mo, budget_mo * MO
        self.budget_tri = budget_tri
        self.seuil, self.seuil_max = seuil, max(seuil, seuil_max)
        self.resolution = max(2, int(resolution))
        self.pas_terrain = max(0.25, float(pas_terrain))

    def dict(self):
        return {"budgetMB": self.budget_mo, "budgetTriangles": self.budget_tri, "minExtent": self.seuil, "maxExtent": self.seuil_max,
                "resolution": self.resolution, "terrainStep": self.pas_terrain}


class Couleurs:
    """Couleur unie (linéaire, octets RGBA) de chaque matériau : couleur moyenne de sa texture si Pillow est disponible, sinon couleur de base."""

    def __init__(self, plan):
        self.plan = plan
        self.cache, self.moy = {}, {}
        self.pil = None
        try:
            from PIL import Image
            self.pil = Image
        except ImportError:
            pass
        self.sans_pillow = self.illisibles = self.moyennes = 0

    def moyenne_image(self, ii):
        """Couleur moyenne linéaire (r, v, b) d'une image, pondérée par l'opacité ; None si illisible."""
        if ii in self.moy:
            return self.moy[ii]
        res = None
        if self.pil is not None and ii not in self.plan.img_ko:
            try:
                import io
                import warnings
                d = self.plan.donnees_image(ii)
                if d:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        im = self.pil.open(io.BytesIO(bytes(d)))
                        try:
                            im.draft("RGB", (32, 32))
                        except Exception:
                            pass
                        box = getattr(getattr(self.pil, "Resampling", self.pil), "BOX")
                        px = list(im.convert("RGBA").resize((8, 8), box).getdata())
                    sa = sum(p[3] for p in px)
                    if sa > 0:
                        res = tuple(sum(LUT_LIN[p[k]] * p[3] for p in px) / sa for k in range(3))
                        self.moyennes += 1
            except Exception:
                res = None
            if res is None:
                self.illisibles += 1
        self.moy[ii] = res
        return res

    def materiau(self, mi):
        """(r, v, b, a) en octets, ou None si le matériau est translucide (alphaMode BLEND : verre, effets), omis de la vue d'ensemble."""
        if mi is None or not (0 <= mi < len(self.plan.mats)):
            c = tuple(int(v * 255 + 0.5) for v in OV_GRIS_DEFAUT)
            return c + (255,)
        if mi in self.cache:
            return self.cache[mi]
        m = self.plan.mats[mi]
        res = None
        if m.get("alphaMode") != "BLEND":
            pbr = m.get("pbrMetallicRoughness", {})
            fac, tex = pbr.get("baseColorFactor", [1, 1, 1, 1]), pbr.get("baseColorTexture")
            sg = m.get("extensions", {}).get("KHR_materials_pbrSpecularGlossiness")
            if isinstance(sg, dict):
                fac, tex = sg.get("diffuseFactor", [1, 1, 1, 1]), sg.get("diffuseTexture")
            fac = [float(v) for v in fac[:3]] if isinstance(fac, list) and len(fac) >= 3 and all(isinstance(v, (int, float)) for v in fac[:3]) else [1.0, 1.0, 1.0]
            moy = None
            if isinstance(tex, dict) and isinstance(tex.get("index"), int) and 0 <= tex["index"] < len(self.plan.texs):
                if self.pil is None:
                    self.sans_pillow += 1
                else:
                    for ii in images_de_texture(self.plan.texs[tex["index"]]):
                        if 0 <= ii < len(self.plan.glb.g.get("images", [])):
                            moy = self.moyenne_image(ii)
                            break
            if moy is None:
                moy = (1.0, 1.0, 1.0)
            res = tuple(int(min(1.0, max(0.0, moy[k] * fac[k])) * 255 + 0.5) for k in range(3)) + (255,)
        self.cache[mi] = res
        return res


def lire_geometrie(plan, key):
    """Indices d'origine, plage de lignes et colonnes X, Y, Z des positions d'une primitive : (idx, imin, drapeaux, (xs, ys, zs))."""
    glb = plan.glb
    p = plan.prims[key]
    pa = glb.acc(p.attrs["POSITION"])
    if p.indices is None:
        idx, flags = array.array(U32, range(pa.count)), None
    else:
        idx, mq = array.array(CODE[glb.acc(p.indices).comp]), Marques()
        for bloc in glb.blocs_indices(p.indices):
            mq.ajouter(bloc)
            idx.extend(bloc)
        flags = mq.flags
    n = p.imax - p.imin + 1
    if pa.ncomp < 3 or pa.stride % TAILLE[pa.comp]:
        raise ErreurGlb(_tr("py.glb2tiles.accessor_0_positions_non_gerees", pa.i))
    raw = bytes(glb.rangee(pa, p.imin, n)) + bytes(pa.stride - pa.es)
    arr = array.array(CODE[pa.comp])
    arr.frombytes(raw)
    se = pa.stride // TAILLE[pa.comp]
    cols = [arr[k::se] for k in range(3)]
    if pa.comp != 5126 and pa.norm:
        cols = [[decode_norm(v, pa.comp, True) for v in c] for c in cols]
    return idx, p.imin, flags, cols


def regrouper(idx, imin, flags, cols, origine, cell):
    """Regroupement de sommets : un sommet par cellule de côté `cell` (moyenne des sommets de la cellule), triangles dégénérés et doublons
    retirés. cell=None : pas de regroupement (sommets utilisés seulement). Rend (sommets à plat array('f'), triangles à plat list d'indices)."""
    xs, ys, zs = cols
    n = len(xs)
    rows = list(itertools.compress(range(n), flags)) if flags is not None else range(n)
    ux, uy, uz = [xs[r] for r in rows], [ys[r] for r in rows], [zs[r] for r in rows]
    if cell is None:
        cid = list(range(len(ux)))
        nc = len(ux)
        px, py, pz = ux, uy, uz
    else:
        ox, oy, oz = origine
        inv = 1.0 / cell
        M = 4096
        keys = [(int((x - ox) * inv) * M + int((y - oy) * inv)) * M + int((z - oz) * inv) for x, y, z in zip(ux, uy, uz)]
        ids = {}
        cid = [ids.setdefault(k, len(ids)) for k in keys]
        nc = len(ids)
        sx, sy, sz, cnt = [0.0] * nc, [0.0] * nc, [0.0] * nc, [0] * nc
        for c, x, y, z in zip(cid, ux, uy, uz):
            sx[c] += x
            sy[c] += y
            sz[c] += z
            cnt[c] += 1
        px, py, pz = [a / b for a, b in zip(sx, cnt)], [a / b for a, b in zip(sy, cnt)], [a / b for a, b in zip(sz, cnt)]
    rowcid = array.array("i", bytes(4 * n))
    collections.deque(map(rowcid.__setitem__, rows, cid), maxlen=0)
    it = iter([rowcid[i - imin] for i in idx[:len(idx) // 3 * 3]])
    vus, tris = set(), []
    for a, b, c in zip(it, it, it):
        if a == b or b == c or a == c:
            continue
        k = (a, b, c) if a < b and a < c else ((b, c, a) if b < c else (c, a, b))
        if k in vus:
            continue
        vus.add(k)
        tris.append(a)
        tris.append(b)
        tris.append(c)
    # sommets réellement utilisés
    new = {}
    for c in tris:
        if c not in new:
            new[c] = len(new)
    verts = array.array("f")
    for c in new:
        verts.append(px[c])
        verts.append(py[c])
        verts.append(pz[c])
    return verts, [new[c] for c in tris]


class Simplif:
    """Primitives simplifiées, une fois chacune (clé : primitive, résolution), puis réutilisées par toutes les instances."""

    def __init__(self, plan, resolution):
        self.plan, self.res = plan, resolution
        self.cache = {}
        self.lus = 0

    def prim(self, key):
        r = self.cache.get(key)
        if r is not None:
            return r
        p = self.plan.prims[key]
        idx, imin, flags, cols = lire_geometrie(self.plan, key)
        etendue = max(p.hi[k] - p.lo[k] for k in range(3))
        cell = None if p.tri <= 24 or etendue <= 0 else etendue / self.res
        verts, tris = regrouper(idx, imin, flags, cols, p.lo, cell)
        self.lus += p.used
        r = (verts, array.array(U32, tris))
        self.cache[key] = r
        return r


def matrice_pos(m, verts):
    """Positions à plat transformées par la matrice monde m (16 nombres, colonnes)."""
    it = iter(verts)
    out = array.array("f")
    m0, m1, m2, m4, m5, m6, m8, m9, m10, m12, m13, m14 = m[0], m[1], m[2], m[4], m[5], m[6], m[8], m[9], m[10], m[12], m[13], m[14]
    for x, y, z in zip(it, it, it):
        out.append(m0 * x + m4 * y + m8 * z + m12)
        out.append(m1 * x + m5 * y + m9 * z + m13)
        out.append(m2 * x + m6 * y + m10 * z + m14)
    return out


class AccTuile:
    """Géométrie de la vue d'ensemble pour une tuile : primitives de 65 535 sommets au plus (indices 16 bits)."""

    def __init__(self):
        self.morceaux = []        # chacun : [positions array('f'), couleurs bytearray, indices list]
        self.tri = 0

    def ajouter(self, pos, col, tris):
        nv = len(pos) // 3
        if not self.morceaux or (self.morceaux[-1][0] and len(self.morceaux[-1][0]) // 3 + nv > 65535):
            self.morceaux.append([array.array("f"), bytearray(), array.array(U32)])
        m = self.morceaux[-1]
        base = len(m[0]) // 3
        m[0].extend(pos)
        m[1].extend(col)
        m[2].extend(base + i for i in tris)
        self.tri += len(tris) // 3


def terrain_vue(plan, tuiles_de, couleurs, pas, acc):
    """Réseau régulier de pas `pas` commun à toutes les pièces du terrain : hauteur et couleur interpolées dans les triangles d'origine, donc
    aucune fente entre pièces (un point du réseau sur un bord commun reçoit la même hauteur des deux côtés). tuiles_de : liste (instance, tuile).
    Les pièces sont lues l'une après l'autre (jamais toutes en mémoire)."""
    if not tuiles_de:
        return 0
    ox = min(it.lo[0] for it, _ in tuiles_de)
    oz = min(it.lo[2] for it, _ in tuiles_de)
    ech = {}                      # (i, j) -> (y, couleur RGBA)
    e = 1e-6
    for it, nom in tuiles_de:
        for key, pr in plan.mesh_prims[it.mesh]:
            p = plan.prims[key]
            if p.vide or p.mode != 4:
                continue
            idx, imin, flags, cols = lire_geometrie(plan, key)
            n = len(cols[0])
            rows = list(itertools.compress(range(n), flags)) if flags is not None else range(n)
            m = plan.monde[it.node]
            xs, ys, zs = cols
            wx = [m[0] * xs[r] + m[4] * ys[r] + m[8] * zs[r] + m[12] for r in rows]
            wy = [m[1] * xs[r] + m[5] * ys[r] + m[9] * zs[r] + m[13] for r in rows]
            wz = [m[2] * xs[r] + m[6] * ys[r] + m[10] * zs[r] + m[14] for r in rows]
            col = couleur_sommets(plan, pr, rows, couleurs)
            ou = array.array("i", [-1]) * n
            collections.deque(map(ou.__setitem__, rows, itertools.count()), maxlen=0)
            t3 = [ou[i - imin] for i in idx[:len(idx) // 3 * 3]]
            for a, b, c in zip(t3[0::3], t3[1::3], t3[2::3]):
                x1, x2, x3, z1, z2, z3 = wx[a], wx[b], wx[c], wz[a], wz[b], wz[c]
                ia, ib = math.ceil((min(x1, x2, x3) - ox) / pas - e), math.floor((max(x1, x2, x3) - ox) / pas + e)
                ja, jb = math.ceil((min(z1, z2, z3) - oz) / pas - e), math.floor((max(z1, z2, z3) - oz) / pas + e)
                if ia > ib or ja > jb:
                    continue
                den = (z2 - z3) * (x1 - x3) + (x3 - x2) * (z1 - z3)
                if abs(den) < 1e-12:
                    continue
                for i in range(ia, ib + 1):
                    px = ox + i * pas
                    for j in range(ja, jb + 1):
                        if (i, j) in ech:
                            continue
                        pz = oz + j * pas
                        l1 = ((z2 - z3) * (px - x3) + (x3 - x2) * (pz - z3)) / den
                        l2 = ((z3 - z1) * (px - x3) + (x1 - x3) * (pz - z3)) / den
                        l3 = 1.0 - l1 - l2
                        if l1 < -e or l2 < -e or l3 < -e:
                            continue
                        ca, cb, cc = col[a], col[b], col[c]
                        ech[(i, j)] = (l1 * wy[a] + l2 * wy[b] + l3 * wy[c],
                                       bytes(int(l1 * ca[k] + l2 * cb[k] + l3 * cc[k] + 0.5) for k in range(4)))
    total = 0
    for it, nom in tuiles_de:
        # cases possédées par la pièce : coin bas dans [min, max[ (intervalle semi-ouvert : jamais deux pièces pour une case, jamais de case sans pièce)
        i0, i1 = math.ceil((it.lo[0] - ox) / pas - e), math.ceil((it.hi[0] - ox) / pas - e)
        j0, j1 = math.ceil((it.lo[2] - oz) / pas - e), math.ceil((it.hi[2] - oz) / pas - e)
        pos, cols, tris, local = array.array("f"), bytearray(), [], {}

        def sommet(i, j):
            v = local.get((i, j))
            if v is None:
                s = ech[(i, j)]
                v = local[(i, j)] = len(local)
                pos.extend((ox + i * pas, s[0], oz + j * pas))
                cols.extend(s[1])
            return v
        for i in range(i0, i1):
            for j in range(j0, j1):
                if (i, j) in ech and (i + 1, j) in ech and (i, j + 1) in ech and (i + 1, j + 1) in ech:
                    v00, v10, v01, v11 = sommet(i, j), sommet(i + 1, j), sommet(i, j + 1), sommet(i + 1, j + 1)
                    tris.extend((v00, v01, v10, v10, v01, v11))
        if tris:
            acc.setdefault(nom, AccTuile()).ajouter(pos, cols, tris)
            total += len(tris) // 3
    return total


def couleur_sommets(plan, pr, rows, couleurs):
    """Couleurs RGBA (octets) des sommets utilisés : COLOR_0 s'il existe (terrain d'oar2glb), sinon la couleur du matériau."""
    ai = pr.get("attributes", {}).get("COLOR_0")
    fond = couleurs.materiau(pr.get("material")) or (200, 200, 200, 255)
    if ai is None:
        return [fond] * len(rows)
    glb = plan.glb
    a = glb.acc(ai)
    if a.ncomp not in (3, 4) or a.stride % TAILLE[a.comp]:
        return [fond] * len(rows)
    p = plan.prims[cle_prim(pr)]
    n = p.imax - p.imin + 1
    arr = array.array(CODE[a.comp])
    arr.frombytes(bytes(glb.rangee(a, p.imin, n)) + bytes(a.stride - a.es))
    se = a.stride // TAILLE[a.comp]
    out = []
    for r in rows:
        v = [decode_norm(arr[r * se + k], a.comp, a.norm) for k in range(3)]
        out.append(tuple(int(min(1.0, max(0.0, c)) * 255 + 0.5) for c in v) + (255,))
    return out


def fusionner(morceaux):
    """Regroupe les morceaux consécutifs tant que le total reste à 65 535 sommets au plus : une primitive (un appel de dessin) par tuile en général."""
    out = []
    for pos, col, idx in morceaux:
        nv = len(pos) // 3
        if out and len(out[-1][0]) // 3 + nv <= 65535:
            base = len(out[-1][0]) // 3
            out[-1][0].extend(pos)
            out[-1][1].extend(col)
            out[-1][2].extend(base + i for i in idx)
        else:
            out.append([array.array("f", pos), bytearray(col), array.array(U32, idx)])
    return out


def ecrire_vue_ensemble(plan, groupes, chemin, tuiles_fichiers):
    """Écrit X.overview.glb : un nœud par tuile (nom = fichier de la tuile), un seul matériau (couleurs de sommets). Rend (octets, triangles, nœuds)."""
    parts, bin_len = [], 0
    views, accessors, meshes, nodes = [], [], [], []

    def vue(data, cible):
        nonlocal bin_len
        if bin_len % 4:
            parts.append(bytes(4 - bin_len % 4))
            bin_len += 4 - bin_len % 4
        views.append({"buffer": 0, "byteOffset": bin_len, "byteLength": len(data), "target": cible})
        parts.append(bytes(data))
        bin_len += len(data)
        return len(views) - 1
    tri = 0
    for nom in tuiles_fichiers:
        morceaux = fusionner([m for acc in groupes for m in (acc[nom].morceaux if nom in acc else ())])
        if not morceaux:
            continue
        prims = []
        for pos, col, idx in morceaux:
            nv = len(pos) // 3
            if not idx:
                continue
            mn = [min(pos[k::3]) for k in range(3)]
            mx = [max(pos[k::3]) for k in range(3)]
            ap = len(accessors)
            accessors.append({"bufferView": vue(pos.tobytes(), 34962), "componentType": 5126, "count": nv, "type": "VEC3", "min": mn, "max": mx})
            accessors.append({"bufferView": vue(col, 34962), "componentType": 5121, "normalized": True, "count": nv, "type": "VEC4"})
            if nv <= 65535:
                ib, comp = array.array("H", idx).tobytes(), 5123
            else:
                ib, comp = array.array(U32, idx).tobytes(), 5125
            accessors.append({"bufferView": vue(ib, 34963), "componentType": comp, "count": len(idx), "type": "SCALAR"})
            prims.append({"attributes": {"POSITION": ap, "COLOR_0": ap + 1}, "indices": ap + 2, "material": 0, "mode": 4})
            tri += len(idx) // 3
        if not prims:
            continue
        meshes.append({"name": "vue:" + nom, "primitives": prims})
        nodes.append({"name": nom, "mesh": len(meshes) - 1, "extras": {"tile": nom}})
    js = {"asset": {"version": "2.0", "generator": f"glb2tiles {VERSION} (vue d'ensemble)"}, "scene": 0,
          "scenes": [{"nodes": list(range(len(nodes)))}], "nodes": nodes, "meshes": meshes, "accessors": accessors, "bufferViews": views,
          "materials": [{"name": "vue-ensemble", "doubleSided": True,
                         "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 1}}]}
    total_bin = (bin_len + 3) & ~3
    js["buffers"] = [{"byteLength": total_bin}]
    if not nodes:
        for k in ("meshes", "accessors", "bufferViews", "buffers"):
            js.pop(k)
    jb = json.dumps(js, separators=(",", ":")).encode("utf-8")
    jb += b" " * (-len(jb) % 4)
    total = 12 + 8 + len(jb) + (8 + total_bin if nodes else 0)
    if total > LIMITE_GLB:
        raise ErreurGlb(_tr("py.glb2tiles.la_vue_d_ensemble_depasse_la"))
    tmp = str(chemin) + ".tmp"
    with open(tmp, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total))
        f.write(struct.pack("<II", len(jb), 0x4E4F534A))
        f.write(jb)
        if nodes:
            f.write(struct.pack("<II", total_bin, 0x004E4942))
            for part in parts:
                f.write(part)
            f.write(bytes(total_bin - bin_len))
    os.replace(tmp, chemin)
    return total, tri, len(nodes)


def instances_de(plan, tuile):
    """(instances, terrain) d'une tuile : toutes les instances de ses unités, séparées selon que la racine est du terrain (extras.terrain)."""
    objets, terrain, vus = [], [], set()
    for u in tuile.units:
        lst = u.racine.insts if u.entier else [i for i in u.racine.insts if i.node == u.node]
        for it in lst:
            if it.node in vus:
                continue
            vus.add(it.node)
            (terrain if plan.est_terrain(u.racine) else objets).append(it)
    return objets, terrain


def vue_ensemble(plan, tuiles, noms, OP, chemin):
    """Construit et écrit la vue d'ensemble. noms : fichier de chaque tuile (même ordre que `tuiles`). Rend le dictionnaire du rapport."""
    t0 = time.time()
    log(_tr("py.glb2tiles.vue_d_ensemble_budget_0_g", OP.budget_mo, fmt(OP.budget_tri), OP.seuil, OP.resolution, OP.pas_terrain))
    couleurs = Couleurs(plan)
    omis = {"petits": 0, "squelette": 0, "translucides": 0, "budget": 0}
    tp, cand = [], []             # pièces de terrain (instance, tuile) ; objets candidats (étendue, instance, tuile)
    for t, nom in zip(tuiles, noms):
        objets, terrain = instances_de(plan, t)
        tp += [(it, nom) for it in terrain]
        for it in objets:
            if isinstance(plan.nodes[it.node].get("skin"), int):
                omis["squelette"] += 1
                continue
            cand.append((max(it.hi[k] - it.lo[k] for k in range(3)), it, nom))
    # terrain : au plus la moitié des budgets ; sinon le pas du réseau grossit (x 1,5) jusqu'à ce qu'il tienne
    pas = OP.pas_terrain
    while True:
        acc_t = {}
        tri_terrain = terrain_vue(plan, tp, couleurs, pas, acc_t) if tp else 0
        oct_terrain = sum(len(p) * 4 + len(c) + len(ix) * 2 for a in acc_t.values() for p, c, ix in a.morceaux)
        if not tp or (tri_terrain <= OP.budget_tri / 2 and oct_terrain <= OP.budget / 2) or pas > 4096:
            break
        pas *= 1.5
        log(_tr("py.glb2tiles.vue_d_ensemble_terrain_trop_lourd", pas))
    log(_tr("py.glb2tiles.vue_d_ensemble_terrain_0_piece", len(tp), fmt(tri_terrain), pas))
    res = OP.resolution
    while True:
        base = sorted((c for c in cand if c[0] >= OP.seuil), key=lambda c: -c[0])
        omis["petits"] = len(cand) - len(base)
        simp = Simplif(plan, res)
        meshes = sorted({c[1].mesh for c in base})
        pg = Progres("vue d'ensemble : primitives", len(meshes))
        info, transl = {}, 0       # mesh -> (parties (sommets, triangles, couleur), triangles, sommets)
        for n, m in enumerate(meshes):
            parts, tri, nv = [], 0, 0
            for key, pr in plan.mesh_prims[m]:
                p = plan.prims[key]
                if p.vide or p.mode != 4:
                    continue
                col = couleurs.materiau(pr.get("material"))
                if col is None:
                    transl += 1
                    continue
                v, tr = simp.prim(key)
                if len(tr):
                    parts.append((v, tr, col))
                    tri += len(tr) // 3
                    nv += len(v) // 3
            info[m] = (parts, tri, nv)
            pg.avance(n + 1)
        omis["translucides"] = transl
        # les plus grands d'abord, tant que le budget le permet : le seuil effectif est l'étendue du dernier objet gardé
        reste_tri, reste_oct = OP.budget_tri - tri_terrain, OP.budget - oct_terrain
        gardes, tri_tot, oct_tot = [], 0, 0
        for c in base:
            parts, tri, nv = info[c[1].mesh]
            if not parts:
                continue
            ob = tri * 6 + nv * 16
            if tri_tot + tri > reste_tri or oct_tot + ob > reste_oct:
                break
            gardes.append(c)
            tri_tot += tri
            oct_tot += ob
        coupes = [c for c in base[len(gardes):] if info[c[1].mesh][0]]
        limite = max((c[0] for c in coupes), default=0.0)
        if limite > OP.seuil_max and res > 3:
            res = max(3, int(res * 0.7))
            log(_tr("py.glb2tiles.vue_d_ensemble_budget_atteint_avant", limite, res))
            continue
        break

    def assembler(liste):
        acc = {}
        for e, it, nom in liste:
            a = acc.setdefault(nom, AccTuile())
            m = plan.monde[it.node]
            for v, tr, col in info[it.mesh][0]:
                a.ajouter(matrice_pos(m, v), bytes(col) * (len(v) // 3), list(tr))
        return acc
    acc_o = assembler(gardes)
    total, tri, nn = ecrire_vue_ensemble(plan, [acc_t, acc_o], chemin, noms)
    while total > OP.budget and gardes:            # poids réel au-dessus du budget (estimation trop optimiste) : on retire les plus petits
        gardes = gardes[:len(gardes) - max(1, len(gardes) // 10)]
        acc_o = assembler(gardes)
        total, tri, nn = ecrire_vue_ensemble(plan, [acc_t, acc_o], chemin, noms)
    omis["budget"] = len(base) - len(gardes) - sum(1 for c in base if not info[c[1].mesh][0])
    seuil_eff = min((c[0] for c in gardes), default=OP.seuil)
    log(_tr("py.glb2tiles.vue_d_ensemble_0_1f_mo", total / MO, fmt(tri), len(gardes), len(cand), nn, time.time() - t0))
    return {"file": chemin.name, "bytes": total, "triangles": tri, "terrainTriangles": tri_terrain, "objects": len(gardes), "candidates": len(cand),
            "omitted": {"small": omis["petits"], "skinned": omis["squelette"], "translucentPrimitives": omis["translucides"], "budget": omis["budget"]},
            "effectiveMinExtent": round(seuil_eff, 2), "resolution": res, "effectiveTerrainStep": round(pas, 3), "seconds": round(time.time() - t0, 1),
            "colors": {"textureAverages": couleurs.moyennes, "unreadable": couleurs.illisibles, "withoutPillow": couleurs.sans_pillow,
                       "pillow": couleurs.pil is not None},
            "params": OP.dict()}


def ecrire_tout(glb, plan, tuiles, sortie, nom):
    """Écrit les tuiles ; ensuite seulement, supprime les T_*.glb d'une exécution précédente qui ne figurent plus dans le nouvel index.
    Rend (fiches, dossier, nombre de fichiers supprimés)."""
    dossier = Path(sortie) / f"{nom}.tiles"
    dossier.mkdir(parents=True, exist_ok=True)
    fiches = []
    pg = Progres("tuiles", len(tuiles))
    for n, t in enumerate(tuiles):
        f = ecrire_tuile(plan, t, dossier / f"{t.nom}.glb")
        f["file"] = f"{nom}.tiles/{t.nom}.glb"
        fiches.append(f)
        pg.avance(n + 1)
    nouveaux = {Path(f["file"]).name for f in fiches}
    supprimes = 0
    for ancien in dossier.glob("T_*_*_*.glb"):
        if ancien.name not in nouveaux:
            ancien.unlink()
            supprimes += 1
    return fiches, dossier, supprimes


def lignes_taille_instances(plan):
    """Répartition des instances par étendue (plus grande dimension) : aide à choisir --ov-threshold de la vue d'ensemble."""
    out = [_tr("py.glb2tiles.etendue_des_instances_plus_grande_dimension")]
    tot_i, tot_t = len(plan.insts), sum(i.tri for i in plan.insts)
    for sv in (1, 2, 3, 4, 8, 16, 32, 64):
        n = t = 0
        for i in plan.insts:
            if max(i.hi[k] - i.lo[k] for k in range(3)) >= sv:
                n += 1
                t += i.tri
        out.append(f"  - au moins {sv} m : {fmt(n)} instances ({100 * n / max(1, tot_i):.0f} %), {fmt(t)} triangles ({100 * t / max(1, tot_t):.0f} %)")
    return out


# v43 : anciens noms d'options (avant la v43), toujours acceptés : remplacés avant la lecture de la ligne de commande
OLD_OPTIONS = {"--budget-tri": "--budget-triangles", "--entier-poids": "--whole-weight", "--entier-etendue": "--whole-extent", "--seuil": "--threshold",
               "--seuil-tri": "--threshold-triangles", "--aberrant": "--outlier", "--bloc": "--block", "--exclure": "--exclude",
               "--exclure-max-tri": "--exclude-max-triangles", "--exclure-max-meshes": "--exclude-max-meshes", "--sans-references": "--no-refs",
               "--sans-vue-ensemble": "--no-overview", "--vue-ensemble-seule": "--overview-only", "--ov-budget-tri": "--ov-budget-triangles",
               "--ov-seuil": "--ov-threshold", "--ov-seuil-max": "--ov-threshold-max", "--ov-terrain-pas": "--ov-terrain-step", "--forcer": "--force",
               "--sortie": "--output"}


def old_options(argv):
    """Remplace les anciens noms d'options par les nouveaux (« --nom=valeur » compris)."""
    out = []
    for x in argv:
        k, eq, v = str(x).partition("=")
        out.append(OLD_OPTIONS.get(k, k) + eq + v if k.startswith("--") else x)
    return out


def main(argv=None, log_path=None):
    global LOG_PATH
    LOG_PATH = log_path
    ap = argparse.ArgumentParser(description=_tr("py.glb2tiles.desc", VERSION), epilog=_tr("py.glb2tiles.epilog"), formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False)
    i18n_add_common(ap)
    ap.add_argument("glb", help=_tr("py.glb2tiles.glb_d_entree"))
    ap.add_argument("--version", action="version", version=f"glb2tiles {version_tag()}", help=_tr("py.common.version"))
    ap.add_argument("--analyse", action="store_true", help=_tr("py.glb2tiles.lecture_seule_mesures_decoupage_prevu_recomm"))
    ap.add_argument("--budget", type=float, default=32.0, help=_tr("py.glb2tiles.mo_par_tuile_defaut_32"))
    ap.add_argument("--budget-triangles", metavar="BUDGET_TRIANGLES", dest="budget_tri", type=int, default=1500000, help=_tr("py.glb2tiles.triangles_par_tuile_defaut_1500000"))
    ap.add_argument("--min", metavar="MIN", type=float, default=16.0, dest="cote_min", help=_tr("py.glb2tiles.cote_minimal_d_une_cellule_en"))
    ap.add_argument("--whole-weight", metavar="WHOLE_WEIGHT", dest="entier_poids", type=float, default=16.0, help=_tr("py.glb2tiles.mo_un_objet_racine_plus_leger"))
    ap.add_argument("--whole-extent", metavar="WHOLE_EXTENT", dest="entier_etendue", type=float, default=256.0, help=_tr("py.glb2tiles.m_etendue_maximale_d_un_objet"))
    ap.add_argument("--threshold", metavar="THRESHOLD", dest="seuil", type=float, default=150.0, help=_tr("py.glb2tiles.mo_sous_ce_poids_et_sous"))
    ap.add_argument("--threshold-triangles", metavar="THRESHOLD_TRIANGLES", dest="seuil_tri", type=int, default=3000000, help=_tr("py.glb2tiles.triangles_pour_la_recommandation_pas_de"))
    ap.add_argument("--outlier", metavar="OUTLIER", dest="aberrant", type=float, default=1000.0, help=_tr("py.glb2tiles.m_distance_ou_etendue_au_dela"))
    ap.add_argument("--block", metavar="BLOCK", dest="bloc", type=float, default=256.0, help=_tr("py.glb2tiles.cote_des_blocs_de_la_section"))
    ap.add_argument("--exclude", dest="exclure", action="append", default=[], metavar="REGEX",
                    help=_tr("py.glb2tiles.retire_du_decoupage_les_objets_racine"))
    ap.add_argument("--exclude-max-triangles", metavar="EXCLUDE_MAX_TRIANGLES", dest="exclure_max_tri", type=int, default=24, help=_tr("py.glb2tiles.avec_exclure_triangles_au_plus_dans"))
    ap.add_argument("--exclude-max-meshes", metavar="EXCLUDE_MAX_MESHES", dest="exclure_max_meshes", type=int, default=1, help=_tr("py.glb2tiles.avec_exclure_meshes_au_plus_dans"))
    ap.add_argument("--no-refs", dest="sans_references", action="store_true", help=_tr("py.glb2tiles.ne_pas_ecrire_extras_ref_extras"))
    ap.add_argument("--no-overview", dest="sans_vue_ensemble", action="store_true", help=_tr("py.glb2tiles.ne_pas_ecrire_x_overview_glb"))
    ap.add_argument("--overview-only", dest="vue_ensemble_seule", action="store_true", help=_tr("py.glb2tiles.n_ecrire_que_x_overview_glb"))
    ap.add_argument("--ov-budget", type=float, default=OV_BUDGET_MO, help=_tr("py.glb2tiles.mo_poids_maximal_de_la_vue"))
    ap.add_argument("--ov-budget-triangles", metavar="OV_BUDGET_TRIANGLES", dest="ov_budget_tri", type=int, default=OV_BUDGET_TRI, help=_tr("py.glb2tiles.triangles_de_la_vue_d_ensemble"))
    ap.add_argument("--ov-threshold", metavar="OV_THRESHOLD", dest="ov_seuil", type=float, default=OV_SEUIL, help=_tr("py.glb2tiles.m_les_objets_dont_la_plus"))
    ap.add_argument("--ov-threshold-max", metavar="OV_THRESHOLD_MAX", dest="ov_seuil_max", type=float, default=OV_SEUIL_MAX, help=_tr("py.glb2tiles.m_si_le_budget_oblige_a"))
    ap.add_argument("--ov-resolution", type=int, default=OV_RESOLUTION, help=_tr("py.glb2tiles.cellules_sur_la_plus_grande_dimension"))
    ap.add_argument("--ov-terrain-step", metavar="OV_TERRAIN_STEP", dest="ov_terrain_pas", type=float, default=OV_PAS_TERRAIN, help=_tr("py.glb2tiles.m_pas_du_reseau_du_terrain"))
    ap.add_argument("--force", dest="forcer", action="store_true", help=_tr("py.glb2tiles.decouper_meme_si_la_recommandation_est"))
    ap.add_argument("--output", metavar="OUTPUT", dest="sortie", help=_tr("py.glb2tiles.dossier_de_sortie_defaut_a_cote"))
    ap.add_argument("--nopause", action="store_true", help=_tr("py.glb2tiles.ne_pas_attendre_entree_a_la"))
    a = ap.parse_args(old_options(sys.argv[1:] if argv is None else list(argv)))
    P = Params(a.budget, a.budget_tri, a.cote_min, a.entier_poids, a.entier_etendue, a.seuil, a.seuil_tri, a.aberrant, a.bloc,
               a.exclure, a.exclure_max_tri, a.exclure_max_meshes, not a.sans_references)
    OP = ParamsOv(a.ov_budget, a.ov_budget_tri, a.ov_seuil, a.ov_seuil_max, a.ov_resolution, a.ov_terrain_pas)
    if a.sans_vue_ensemble and a.vue_ensemble_seule:
        raise ErreurGlb(_tr("py.glb2tiles.sans_vue_ensemble_et_vue_ensemble"))
    t0 = time.time()
    chemin = Path(a.glb)
    if not chemin.is_file():
        raise ErreurGlb(_tr("py.glb2tiles.glb_introuvable_0", chemin))
    glb = Glb(chemin)
    try:
        log(_tr("py.glb2tiles.glb2tiles_0_1_1f_mo", chemin.name, mo(glb.taille)))
        plan = Plan(glb, P)
        if not plan.insts:
            raise ErreurGlb(_tr("py.glb2tiles.aucun_mesh_positionnable_dans_la_scene"))
        tuiles = plan.decouper()
        sortie = Path(a.sortie) if a.sortie else chemin.resolve().parent
        nom = chemin.stem
        if a.vue_ensemble_seule and not a.analyse:
            return vue_ensemble_seule(glb, plan, tuiles, sortie, nom, OP, t0)
        decoupe, phrase = recommandation(glb, plan, tuiles)
        if a.analyse:
            for ligne in rapport_analyse(glb, plan, tuiles):
                log(ligne)
            for ligne in lignes_taille_instances(plan):
                log(ligne)
            ancien = sortie / f"{nom}.tiles.json"       # v32 : tuiles déjà écrites sans les références d'objets
            if ancien.is_file():
                try:
                    d_anc = json.loads(ancien.read_text(encoding="utf-8-sig"))
                except ValueError:
                    d_anc = {}
                if isinstance(d_anc, dict) and d_anc.get("tiles") and not d_anc.get("nodeRefs"):
                    log(_tr("py.glb2tiles.avertissement_0_existe_deja_mais_ses", ancien.name))
            log(_tr("py.glb2tiles.temps_0_1f_s", time.time() - t0))
            return 0
        log(phrase)
        if not decoupe and not a.forcer:
            log(_tr("py.glb2tiles.rien_n_est_ecrit_forcer_pour"))
            return 0
        fiches, dossier, supprimes = ecrire_tout(glb, plan, tuiles, sortie, nom)
        geo_u = sum(plan.cb[k] for k in {k for u in plan.unites for k in u.cles})
        dup = sum(f["geometryBytes"] for f in fiches) / geo_u if geo_u else 1.0
        ent = sum(1 for r in plan.racines if r.entier)
        avert = plan.avertissements + signalements(plan) + plan.hors_budget(tuiles)
        img_dist, img_occ = plan.images_remplacees(tuiles)
        lo = [min(i.lo[k] for i in plan.insts) for k in range(3)]
        hi = [max(i.hi[k] for i in plan.insts) for k in range(3)]
        doc = {"version": FORMAT_TUILES, "generator": f"glb2tiles {VERSION}", "source": chemin.name,
               "extent": {"min": lo, "max": hi}, "params": P.dict(), "warnings": avert,
               "roots": {"whole": ent, "split": len(plan.racines) - ent},
               "duplication": round(dup, 3), "nodeRefs": 1 if P.references else 0, "replacedImages": {"distinct": img_dist, "occurrences": img_occ, "grey": GRIS_IMAGE}, "tiles": fiches}
        if P.exclure:
            doc["excluded"] = {"patterns": P.exclure_motifs, "maxTriangles": P.exclure_max_tri, "maxMeshes": P.exclure_max_meshes,
                               "count": len(plan.exclus), "triangles": sum(x["tri"] for x in plan.exclus), "bytesSaved": plan.octets_exclus, "bytesShared": plan.octets_partages,
                               "names": dict(collections.Counter(x["nom"] for x in plan.exclus).most_common(20))}
        ov = None
        if not a.sans_vue_ensemble:
            ov = vue_ensemble(plan, tuiles, [f["file"] for f in fiches], OP, Path(sortie) / f"{nom}.overview.glb")
            doc["overview"] = ov
        else:
            ancien = Path(sortie) / f"{nom}.overview.glb"
            if ancien.is_file():
                log(_tr("py.glb2tiles.avertissement_0_d_une_execution_precedente", ancien.name))
        ecrire_index(Path(sortie) / f"{nom}.tiles.json", doc)
        poids = [x["bytes"] / MO for x in fiches]
        tris = [x["triangles"] for x in fiches]
        log("")
        log(_tr("py.glb2tiles.rapport"))
        log(_tr("py.glb2tiles.tuiles_0_dans_1", len(fiches), dossier))
        if supprimes:
            log(_tr("py.glb2tiles.tuiles_d_une_execution_precedente_absentes", supprimes))
        log(_tr("py.glb2tiles.poids_mo_mediane_0_1f_90", quantile(poids, 0.5), quantile(poids, 0.9), max(poids)))
        log(_tr("py.glb2tiles.triangles_mediane_0_90_sous_1", fmt(quantile(tris, 0.5)), fmt(quantile(tris, 0.9)), fmt(max(tris))))
        log(_tr("py.glb2tiles.duplication_reelle_de_la_geometrie_somme", virg(dup)))
        log(_tr("py.glb2tiles.objets_racine_gardes_entiers_0_repartis", ent, len(plan.racines) - ent))
        for ligne in lignes_exclusions(plan):
            log(ligne)
        log(ligne_images(plan, tuiles))
        if P.references:
            log(_tr("py.glb2tiles.references_d_objets_extras_ref_extras", fmt(plan.nb_refs), fmt(plan.nb_partages)))
        else:
            log(_tr("py.glb2tiles.references_d_objets_non_ecrites_sans"))
        if ov:
            for ligne in lignes_vue_ensemble(ov):
                log(ligne)
        for w in avert:
            log(_tr("py.glb2tiles.warning_prefix") + w)
        log(_tr("py.glb2tiles.temps_0_1f_s_1_octets", time.time() - t0, fmt(glb.octets_lus), fmt(glb.taille)))
        return 0
    finally:
        glb.fermer()


def ecrire_index(chemin, doc):
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")


def lignes_vue_ensemble(ov):
    om = ov["omitted"]
    out = [_tr("py.glb2tiles.vue_d_ensemble_0_1_1f", ov['file'], ov['bytes'] / MO, fmt(ov['triangles']), fmt(ov['terrainTriangles']), fmt(ov['objects']), fmt(ov['candidates']), ov['seconds']),
           _tr("py.glb2tiles.objets_omis_0_trop_petits_etendue", fmt(om['small']), fmt(om['budget']), fmt(om['skinned']), fmt(om['translucentPrimitives'])),
           _tr("py.glb2tiles.etendue_minimale_effective_0_g_m", ov['effectiveMinExtent'], ov['params']['minExtent'], ov['resolution'], ov['effectiveTerrainStep'], ov['params']['terrainStep'])]
    c = ov["colors"]
    if c["pillow"]:
        out.append(_tr("py.glb2tiles.couleurs_moyenne_de_texture_pour_0", fmt(c['textureAverages']), fmt(c['unreadable'])))
    else:
        out.append(_tr("py.glb2tiles.couleurs_pillow_absent_couleur_de_base", fmt(c['withoutPillow'])))
    return out


def vue_ensemble_seule(glb, plan, tuiles, sortie, nom, OP, t0):
    """--overview-only : les tuiles et X.tiles.json existent ; le découpage recalculé doit correspondre à l'index (mêmes fichiers)."""
    idx = Path(sortie) / f"{nom}.tiles.json"
    if not idx.is_file():
        raise ErreurGlb(_tr("py.glb2tiles.0_introuvable_vue_ensemble_seule_suppose", idx, sortie))
    try:
        doc = json.loads(idx.read_text(encoding="utf-8-sig"))
    except ValueError as e:
        raise ErreurGlb(_tr("py.glb2tiles.0_illisible_1", idx, e))
    noms = [f"{nom}.tiles/{t.nom}.glb" for t in tuiles]
    index = {f.get("file"): f for f in doc.get("tiles", []) if isinstance(f, dict)}
    if set(noms) != set(index):
        raise ErreurGlb(_tr("py.glb2tiles.le_decoupage_recalcule_0_tuiles_ne", len(noms), idx.name, len(index)))
    for t, f in zip(tuiles, noms):
        if index[f].get("triangles") != sum(u.tri for u in t.units) or index[f].get("instances") != sum(u.ninst for u in t.units):
            raise ErreurGlb(_tr("py.glb2tiles.la_tuile_0_n_a_plus", f, idx.name))
    if not doc.get("nodeRefs"):
        log(_tr("py.glb2tiles.avertissement_ces_tuiles_ont_ete_ecrites"))
    ov = vue_ensemble(plan, tuiles, noms, OP, Path(sortie) / f"{nom}.overview.glb")
    doc["overview"] = ov
    ecrire_index(idx, doc)
    log("")
    log(_tr("py.glb2tiles.rapport"))
    for ligne in lignes_vue_ensemble(ov):
        log(ligne)
    log(_tr("py.glb2tiles.temps_0_1f_s_1_octets", time.time() - t0, fmt(glb.octets_lus), fmt(glb.taille)))
    return 0


if __name__ == "__main__":
    sys.argv = old_options(sys.argv)
    if "--version" in sys.argv[1:]:      # ni journal ni pause « Entrée »
        print(_tr("py.glb2tiles.glb2tiles_0_2", version_tag()))
        sys.exit(0)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    journal = Path(__file__).resolve().with_name("glb2tiles.log")
    with open(journal, "w", encoding="utf-8") as lf:
        lf.write(f"[glb2tiles] {version_tag()}\n")
    print(_tr("py.glb2tiles.glb2tiles_0", version_tag()))
    code = 0
    try:
        code = main(log_path=journal)
    except SystemExit as e:
        if isinstance(e.code, str):
            log(e.code)
        code = e.code if isinstance(e.code, int) else 1
    except ErreurGlb as e:
        log(_tr("py.glb2tiles.erreur_0", e))
        code = 2
    except Exception:
        log(traceback.format_exc())
        code = 1
    print(_tr("py.glb2tiles.log_0", journal))
    if "--nopause" not in sys.argv and sys.stdin and sys.stdin.isatty():      # ni console (script, tâche planifiée) : pas de pause
        try:
            input(_tr("py.glb2tiles.entree_pour_fermer"))
        except EOFError:
            pass
    sys.exit(code)
