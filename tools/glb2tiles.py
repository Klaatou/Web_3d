#!/usr/bin/env python3
"""glb2tiles.py : découpe un GLB énorme en tuiles autonomes (un GLB valide par tuile).

Usage :  python glb2tiles.py --version
         python glb2tiles.py "Region.glb" --analyse
         python glb2tiles.py "Region.glb" [--budget 32] [--budget-tri 1500000] [--min 16] [--sortie DOSSIER]

Python standard seulement. Le GLB d'entrée n'est jamais chargé en entier : l'en-tête JSON est lu, puis les accessors
et les images sont lus par seek/read, par morceaux, à la demande. Chaque tuile (quelques dizaines de Mo) est
assemblée en mémoire puis écrite.

Sorties (à côté du GLB, ou dans --sortie) : X.tiles/T_<niveau>_<i>_<j>.glb et X.tiles.json.
Le journal est glb2tiles.log, écrit à côté du script (sa première ligne donne la version).

Principe : quadtree adaptatif sur le plan X,Z (glTF : Y vers le haut), uniquement sur les cellules non vides. Une cellule
est subdivisée tant que son poids autonome dépasse --budget (Mo) ou ses triangles --budget-tri, et que son côté dépasse
--min (m). Un objet racine (nœud de premier niveau) reste entier si son poids autonome ne dépasse pas --entier-poids (Mo)
ET si son étendue ne dépasse pas --entier-etendue (m) ; sinon il est réparti instance par instance. Un objet portant un
skin n'est jamais réparti. Les meshes partagés entre tuiles sont dupliqués dans chaque tuile qui les utilise.
Les sommets de chaque primitive sont compactés (seuls les sommets indexés sont gardés). Coordonnées inchangées.

Hors lot : découpage par triangles d'un mesh unique plus grand qu'une cellule (terrain, mer), vue d'ensemble,
compression des tuiles, chargement des tuiles dans la coquille. Les GLB compressés (Draco, meshopt) sont refusés.

Les fonctions communes de mesure (lecture de l'en-tête, matrices, instances) viennent de glb-stats.py, qui doit se
trouver à côté de ce script (build.py le recopie dans dist/).
"""
import argparse
import array
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
from pathlib import Path

VERSION = "__VERSION__"      # remplacé par build.py (fichier VERSION) dans dist/glb2tiles.py
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
            raise ErreurGlb(f"glb-stats.py introuvable à côté de glb2tiles.py ({p.parent}) : le copier au même endroit.")
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
            raise ErreurGlb("Machine big-endian non gérée.")
        self.chemin = str(chemin)
        self.taille = os.path.getsize(chemin)
        self.g, njson = stats().lire_json(self.chemin)
        self.njson = njson
        self.octets_lus = 20 + njson        # en-tête + JSON (lus par lire_json)
        self.plus_grande_lecture = 0
        self.nb_lectures = 0
        comp = [e for e in self.g.get("extensionsUsed", []) if e in COMPRESSIONS]
        if comp:
            raise ErreurGlb("Ce GLB est compressé (" + ", ".join(comp) + ") : glb2tiles ne lit pas les GLB compressés "
                            "(hors de son périmètre). Décompresser le GLB d'abord, puis relancer.")
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
            raise ErreurGlb("Le tampon 0 a une adresse (uri) : seuls les GLB à tampon intégré sont gérés.")
        self._acc = {}

    def fermer(self):
        self.f.close()

    def lire(self, off, n):
        """Lit n octets à partir de off (relatif au tampon BIN), par morceaux de BLOC_LECTURE."""
        if off < 0 or n < 0 or off + n > self.bin_len:
            raise ErreurGlb(f"Lecture hors du tampon du GLB (décalage {off}, {n} octets) : fichier invalide ou tronqué.")
        out = bytearray()
        self.f.seek(self.bin_off + off)
        reste = n
        while reste > 0:
            k = min(reste, BLOC_LECTURE)
            b = self.f.read(k)
            if len(b) != k:
                raise ErreurGlb("Fichier GLB tronqué.")
            self.octets_lus += k
            self.nb_lectures += 1
            self.plus_grande_lecture = max(self.plus_grande_lecture, k)
            out += b
            reste -= k
        return out

    def vue(self, i):
        bvs = self.g.get("bufferViews", [])
        if i is None or not (0 <= i < len(bvs)):
            raise ErreurGlb(f"bufferView {i} inexistant.")
        bv = bvs[i]
        if bv.get("buffer", 0) != 0:
            raise ErreurGlb(f"bufferView {i} : seul le tampon 0 est géré.")
        return bv

    def acc(self, i):
        a = self._acc.get(i)
        if a is not None:
            return a
        accs = self.g.get("accessors", [])
        if i is None or not (0 <= i < len(accs)):
            raise ErreurGlb(f"Accessor {i} inexistant.")
        x = accs[i]
        if "sparse" in x:
            raise ErreurGlb(f"Accessor {i} : accessor « sparse » non géré par glb2tiles.")
        if "bufferView" not in x:
            raise ErreurGlb(f"Accessor {i} : sans bufferView (valeurs à zéro) non géré par glb2tiles.")
        bv = self.vue(x["bufferView"])
        comp, typ = x.get("componentType"), x.get("type")
        if comp not in TAILLE or typ not in NCOMP:
            raise ErreurGlb(f"Accessor {i} : type {typ}/{comp} inconnu.")
        nc = NCOMP[typ]
        es = nc * TAILLE[comp]
        stride = bv.get("byteStride") or es
        off = bv.get("byteOffset", 0) + x.get("byteOffset", 0)
        count = x.get("count", 0)
        if stride < es:
            raise ErreurGlb(f"Accessor {i} : byteStride ({stride}) plus petit qu'un élément ({es}).")
        if count and off + (count - 1) * stride + es > bv.get("byteOffset", 0) + bv.get("byteLength", 0):
            raise ErreurGlb(f"Accessor {i} : dépasse son bufferView (fichier invalide).")
        a = Acc(i, comp, nc, count, es, stride, off, bool(x.get("normalized")), typ, x.get("min"), x.get("max"))
        self._acc[i] = a
        return a

    def blocs_indices(self, ai):
        """Indices d'un accessor, par morceaux (array non signé)."""
        a = self.acc(ai)
        if a.comp not in (5121, 5123, 5125) or a.ncomp != 1:
            raise ErreurGlb(f"Accessor {ai} : type d'indices non géré.")
        if a.stride != a.es:
            raise ErreurGlb(f"Accessor {ai} : indices avec byteStride non gérés.")
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
    __slots__ = ("id", "nodes", "insts", "cles", "imgs", "tri", "lo", "hi", "centre", "etendue", "poids", "skin", "entier")


class Unite:
    __slots__ = ("racine", "node", "entier", "cles", "imgs", "tri", "cx", "cz", "ninst", "nom", "etendue")


class Tuile:
    def __init__(self, niveau, i, j, units):
        self.niveau, self.i, self.j, self.units = niveau, i, j, units
        self.nom = f"T_{niveau}_{i}_{j}"


def compiler_exclusions(motifs):
    """Expressions de --exclure compilées (insensibles à la casse) ; message clair si l'une est invalide."""
    res = []
    for m in motifs:
        try:
            res.append(re.compile(m, re.IGNORECASE))
        except re.error as e:
            raise ErreurGlb(f"Expression régulière invalide pour --exclure : {m!r} ({e}).")
    return res


class Params:
    """Paramètres du découpage (les poids sont convertis en octets)."""

    def __init__(self, budget=32.0, budget_tri=1500000, cote_min=16.0, entier_poids=16.0, entier_etendue=256.0,
                 seuil=150.0, seuil_tri=3000000, aberrant=1000.0, bloc=256.0, exclure=(), exclure_max_tri=24, exclure_max_meshes=1):
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

    def dict(self):
        return {"budgetMo": self.budget_mo, "budgetTriangles": self.budget_tri, "minCell": self.cote_min,
                "wholeWeightMo": self.entier_poids_mo, "wholeExtent": self.entier_etendue,
                "thresholdMo": self.seuil_mo, "thresholdTriangles": self.seuil_tri, "outlier": self.aberrant}


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
            self.avertissements.append(f"{len(scs)} scènes : seule la scène {g.get('scene', 0)} est découpée.")
        sc = scs[g.get("scene", 0)] if scs else {}
        self.racines_ids = sc.get("nodes") if scs else [i for i in range(len(self.nodes)) if i not in self.parent]
        self.cb = {}            # clé (primitive, skin) -> octets compactés
        self.prims = {}         # clé de primitive -> Prim
        self.img_oct = [self.glb.vue(i["bufferView"]).get("byteLength", 0) + 3 & ~3 if "bufferView" in i else 0
                        for i in g.get("images", [])]
        for i in g.get("images", []):
            if "bufferView" not in i and not str(i.get("uri", "")).startswith("data:"):
                raise ErreurGlb("Image externe (uri) non gérée : seuls les GLB à images intégrées le sont.")
        self._imgs_mat = {}
        self.parcourir()
        self.analyser_prims()
        self.construire_racines()
        self.construire_unites()

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
            self.avertissements.append(f"{len(ignores)} nœud(s) avec caméra ou extensions de nœud : ces champs ne sont pas recopiés dans les tuiles.")

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
                raise ErreurGlb(f"Nœud {ni} : mesh {m} inexistant.")
            lst = []
            for pr in self.meshes[m].get("primitives", []):
                if "extensions" in pr:
                    ext_prim = True
                if "POSITION" not in pr.get("attributes", {}):
                    raise ErreurGlb(f"Mesh {m} : primitive sans POSITION non gérée.")
                lst.append((cle_prim(pr), pr))
            self.mesh_prims[m] = lst
        if ext_prim:
            self.avertissements.append("Des primitives portent des extensions : elles ne sont pas recopiées dans les tuiles.")
        cles = []
        vu = set()
        for lst in self.mesh_prims.values():
            for k, _ in lst:
                if k not in vu:
                    vu.add(k)
                    cles.append(k)
        log(f"[analyse] {len(cles)} primitives distinctes à mesurer (lecture des indices par morceaux)")
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
                raise ErreurGlb(f"Primitive : les attributs n'ont pas tous {pa.count} sommets (accessor {ac}).")
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
                raise ErreurGlb(f"Accessor {ai} : un indice dépasse le nombre de sommets ({pa.count}) : fichier invalide.")
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
            raise ErreurGlb(f"Accessor {pa.i} : positions non gérées.")
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
        self.exclus = []        # objets racine retirés par --exclure : {"nom", "tri", "meshes", "cles", "imgs"}
        self.gardes = 0         # noms qui correspondent à --exclure mais conservés par les garde-fous
        for r in self.racines_ids:
            rac = Racine()
            rac.id, rac.nodes = r, self.noeuds_racine[r]
            rac.insts = []
            rac.skin = False
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
                        self.exclus.append({"nom": nom or f"nœud {r}", "tri": rac.tri, "meshes": len(rac.insts), "cles": rac.cles, "imgs": rac.imgs})
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

    def cle_skin(self, si, cles):
        skins = self.glb.g.get("skins", [])
        if not (0 <= si < len(skins)):
            raise ErreurGlb(f"Skin {si} inexistant.")
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
                u.nom = self.nodes[rac.id].get("name") or f"nœud {rac.id}"
                self.unites.append(u)
            else:
                for it in rac.insts:
                    mi = self.mesh_info[it.mesh]
                    u = Unite()
                    u.racine, u.node, u.entier, u.cles, u.imgs, u.tri = rac, it.node, False, mi.cles, mi.imgs, it.tri
                    u.cx, u.cz, u.ninst = it.centre[0], it.centre[2], 1
                    u.etendue = max(it.hi[0] - it.lo[0], it.hi[2] - it.lo[2])
                    u.nom = self.nodes[it.node].get("name") or self.meshes[it.mesh].get("name") or f"nœud {it.node}"
                    self.unites.append(u)

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
            res.append(f"Tuile {t.nom} hors budget ({mo(geo + img):.1f} Mo, {fmt(tri)} triangles) : {noms}. "
                       "Un mesh unique plus grand qu'une cellule ne peut pas être réparti à ce stade.")
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
            raise ErreurGlb(f"Texture {ti} inexistante.")
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
        raise ErreurGlb(f"Tuile {tuile.nom} : {total / 1024 ** 3:.2f} Go, au-delà de la limite de 4 Go d'un GLB.")
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
            "geometryBytes": asm.o_geo, "imageBytes": asm.o_img}


# ---------------------------------------------------------------- rapports
def quantile(v, q):
    v = sorted(v)
    return v[min(len(v) - 1, max(0, math.ceil(q * len(v)) - 1))] if v else 0


def recommandation(glb, plan, tuiles):
    P = plan.P
    tri = sum(i.tri for i in plan.insts)
    taille = glb.taille - getattr(plan, "octets_exclus", 0)        # sans les objets exclus
    if mo(taille) <= P.seuil_mo and tri <= P.seuil_tri:
        return False, (f"Recommandation : pas de découpage nécessaire ({mo(taille):.1f} Mo sous {P.seuil_mo:g} Mo "
                       f"et {fmt(tri)} triangles sous {fmt(P.seuil_tri)}).")
    geo_u = sum(plan.cb[k] for k in {k for u in plan.unites for k in u.cles})
    st = plan.stats_tuiles(tuiles)
    dup = sum(s[0] for s in st) / geo_u if geo_u else 1.0
    return True, f"Recommandation : découper : budget {P.budget_mo:g} Mo, {len(tuiles)} tuiles, duplication {virg(dup)}."


def lignes_exclusions(plan):
    """Récapitulatif de --exclure : nombre, 20 noms les plus fréquents, octets gagnés ; liste vide sans option."""
    P = plan.P
    if not P.exclure:
        return []
    out = [f"Objets exclus (--exclure, au plus {P.exclure_max_tri} triangles et {P.exclure_max_meshes} mesh(es) par objet racine) : "
           f"{len(plan.exclus)} | triangles retirés : {fmt(sum(x['tri'] for x in plan.exclus))} | octets gagnés : {fmt(plan.octets_exclus)} ({mo(plan.octets_exclus):.1f} Mo)"]
    if plan.gardes:
        out.append(f"  {plan.gardes} objet(s) au nom correspondant conservé(s) par les garde-fous (trop de triangles ou de meshes)")
    for nom, n in collections.Counter(x["nom"] for x in plan.exclus).most_common(20):
        out.append(f"  - {n} x « {nom[:70]} »")
    return out


def rapport_analyse(glb, plan, tuiles):
    P = plan.P
    out = []
    out.append("== Mesures de glb-stats ==")
    out.extend(stats().rapport(glb.chemin, P.bloc, glb.g, glb.njson))
    out.append("")
    # meshes les plus lourds
    insts_mesh = collections.defaultdict(list)
    for it in plan.insts:
        insts_mesh[it.mesh].append(it)
    lourds = sorted(plan.mesh_info.items(), key=lambda kv: -sum(plan.cb[k] for k in set(kv[1].prims)))[:10]
    out.append("== Les 10 meshes les plus lourds (octets compactés, sommets réellement utilisés) ==")
    for m, mi in lourds:
        o = sum(plan.cb[k] for k in set(mi.prims))
        its = insts_mesh.get(m, [])
        if its:
            e = its[0]
            dim = f"{e.hi[0] - e.lo[0]:.1f} x {e.hi[1] - e.lo[1]:.1f} x {e.hi[2] - e.lo[2]:.1f} m"
        else:
            dim = "sans instance"
        nom = plan.meshes[m].get("name") or f"mesh {m}"
        out.append(f"  - « {nom[:40]} » : {mo(o):.2f} Mo, {fmt(mi.tri)} triangles, étendue (X x Y x Z) {dim}, {len(its)} instance(s)")
    # instances aberrantes
    lst, (mx, mz) = plan.aberrantes()
    out.append("")
    out.append(f"== Les 10 instances les plus éloignées du centre médian (X {mx:.0f} m, Z {mz:.0f} m) ==")
    for d, ext, it in sorted(lst, key=lambda t: -t[0])[:10]:
        nom = plan.nodes[it.node].get("name") or f"nœud {it.node}"
        out.append(f"  - « {nom[:40]} » : distance {d:.0f} m, étendue {ext:.0f} m")
    # découpage prévu
    st = plan.stats_tuiles(tuiles)
    geo_u = sum(plan.cb[k] for k in {k for u in plan.unites for k in u.cles})
    img_u = sum(plan.img_oct[i] for i in {i for u in plan.unites for i in u.imgs})
    dup_g = sum(s[0] for s in st) / geo_u if geo_u else 1.0
    dup_i = sum(s[1] for s in st) / img_u if img_u else 1.0
    out.append("")
    out.append(f"== Découpage prévu (budget {P.budget_mo:g} Mo, {fmt(P.budget_tri)} triangles, cellule minimale {P.cote_min:g} m) ==")
    out.append(f"Tuiles : {len(tuiles)} | duplication prévue : géométrie {virg(dup_g)}, images {virg(dup_i)}")
    if st:
        poids = [(s[0] + s[1]) / MO for s in st]
        tris = [s[2] for s in st]
        out.append(f"Poids par tuile (Mo) : médiane {quantile(poids, 0.5):.1f} | 90 % sous {quantile(poids, 0.9):.1f} | maximum {max(poids):.1f}")
        out.append(f"Triangles par tuile : médiane {fmt(quantile(tris, 0.5))} | 90 % sous {fmt(quantile(tris, 0.9))} | maximum {fmt(max(tris))}")
    ent = sum(1 for r in plan.racines if r.entier)
    skin = sum(1 for r in plan.racines if r.skin)
    out.extend(lignes_exclusions(plan))
    out.append(f"Objets racine : {len(plan.racines)} | gardés entiers : {ent} (dont {skin} avec skin) | répartis instance par instance : {len(plan.racines) - ent}")
    avert = plan.avertissements + signalements(plan) + plan.hors_budget(tuiles)
    if avert:
        out.append("Avertissements :")
        out.extend("  - " + a for a in avert)
    out.append(f"Lecture : {fmt(glb.octets_lus)} octets lus sur {fmt(glb.taille)} (plus grande lecture {fmt(glb.plus_grande_lecture)} octets"
               f"; positions relues pour {fmt(plan.positions_lues)} octets, primitives qui partagent un tampon de sommets).")
    out.append("")
    out.append(recommandation(glb, plan, tuiles)[1])
    return out


def signalements(plan):
    """Valeurs aberrantes (distance au centre médian ou étendue au-delà de --aberrant)."""
    lst, _ = plan.aberrantes()
    seuil = plan.P.aberrant
    mauvais = sorted([t for t in lst if t[0] > seuil or t[1] > seuil], key=lambda t: -max(t[0], t[1]))
    if not mauvais:
        return []
    ex = ", ".join(f"« {(plan.nodes[t[2].node].get('name') or 'nœud ' + str(t[2].node))[:30]} » ({t[0]:.0f} m du centre, étendue {t[1]:.0f} m)" for t in mauvais[:3])
    return [f"{len(mauvais)} instance(s) aberrante(s) (à plus de {seuil:g} m du centre médian ou d'étendue supérieure) : {ex}."]


def ecrire_tout(glb, plan, tuiles, sortie, nom):
    t0 = time.time()
    dossier = Path(sortie) / f"{nom}.tiles"
    dossier.mkdir(parents=True, exist_ok=True)
    for ancien in dossier.glob("T_*_*_*.glb"):
        ancien.unlink()
    fiches = []
    pg = Progres("tuiles", len(tuiles))
    for n, t in enumerate(tuiles):
        f = ecrire_tuile(plan, t, dossier / f"{t.nom}.glb")
        f["file"] = f"{nom}.tiles/{t.nom}.glb"
        fiches.append(f)
        pg.avance(n + 1)
    return fiches, dossier


def main(argv=None, log_path=None):
    global LOG_PATH
    LOG_PATH = log_path
    ap = argparse.ArgumentParser(description="Découpe un GLB énorme en tuiles autonomes.")
    ap.add_argument("glb", help="GLB d'entrée")
    ap.add_argument("--version", action="version", version=f"glb2tiles {VERSION}")
    ap.add_argument("--analyse", action="store_true", help="lecture seule : mesures, découpage prévu, recommandation ; n'écrit rien")
    ap.add_argument("--budget", type=float, default=32.0, help="Mo par tuile (défaut 32)")
    ap.add_argument("--budget-tri", type=int, default=1500000, help="triangles par tuile (défaut 1500000)")
    ap.add_argument("--min", type=float, default=16.0, dest="cote_min", help="côté minimal d'une cellule en m (défaut 16)")
    ap.add_argument("--entier-poids", type=float, default=16.0, help="Mo : un objet racine plus léger et plus petit que --entier-etendue reste entier (défaut 16)")
    ap.add_argument("--entier-etendue", type=float, default=256.0, help="m : étendue maximale d'un objet racine gardé entier (défaut 256)")
    ap.add_argument("--seuil", type=float, default=150.0, help="Mo : sous ce poids (et sous --seuil-tri) « pas de découpage » (défaut 150)")
    ap.add_argument("--seuil-tri", type=int, default=3000000, help="triangles pour la recommandation « pas de découpage » (défaut 3000000)")
    ap.add_argument("--aberrant", type=float, default=1000.0, help="m : distance ou étendue au-delà de laquelle une instance est signalée (défaut 1000)")
    ap.add_argument("--bloc", type=float, default=256.0, help="côté des blocs de la section glb-stats de --analyse (défaut 256)")
    ap.add_argument("--exclure", action="append", default=[], metavar="REGEX",
                    help="retire du découpage les objets racine dont le nom correspond (insensible à la casse, répétable), à condition de respecter --exclure-max-tri et --exclure-max-meshes")
    ap.add_argument("--exclure-max-tri", type=int, default=24, help="avec --exclure : triangles au plus dans l'objet racine, tous meshes compris (défaut 24)")
    ap.add_argument("--exclure-max-meshes", type=int, default=1, help="avec --exclure : meshes au plus dans l'objet racine (défaut 1)")
    ap.add_argument("--forcer", action="store_true", help="découper même si la recommandation est « pas de découpage »")
    ap.add_argument("--sortie", help="dossier de sortie (défaut : à côté du GLB)")
    ap.add_argument("--nopause", action="store_true", help="ne pas attendre Entrée à la fin")
    a = ap.parse_args(argv)
    P = Params(a.budget, a.budget_tri, a.cote_min, a.entier_poids, a.entier_etendue, a.seuil, a.seuil_tri, a.aberrant, a.bloc,
               a.exclure, a.exclure_max_tri, a.exclure_max_meshes)
    t0 = time.time()
    chemin = Path(a.glb)
    if not chemin.is_file():
        raise ErreurGlb(f"GLB introuvable : {chemin}")
    glb = Glb(chemin)
    try:
        log(f"[glb2tiles] {chemin.name} : {mo(glb.taille):.1f} Mo")
        plan = Plan(glb, P)
        if not plan.insts:
            raise ErreurGlb("Aucun mesh positionnable dans la scène : rien à découper.")
        tuiles = plan.decouper()
        decoupe, phrase = recommandation(glb, plan, tuiles)
        if a.analyse:
            for ligne in rapport_analyse(glb, plan, tuiles):
                log(ligne)
            log(f"[temps] {time.time() - t0:.1f} s")
            return 0
        log(phrase)
        if not decoupe and not a.forcer:
            log("Rien n'est écrit (--forcer pour découper quand même).")
            return 0
        sortie = Path(a.sortie) if a.sortie else chemin.resolve().parent
        nom = chemin.stem
        fiches, dossier = ecrire_tout(glb, plan, tuiles, sortie, nom)
        geo_u = sum(plan.cb[k] for k in {k for u in plan.unites for k in u.cles})
        dup = sum(f["geometryBytes"] for f in fiches) / geo_u if geo_u else 1.0
        ent = sum(1 for r in plan.racines if r.entier)
        avert = plan.avertissements + signalements(plan) + plan.hors_budget(tuiles)
        lo = [min(i.lo[k] for i in plan.insts) for k in range(3)]
        hi = [max(i.hi[k] for i in plan.insts) for k in range(3)]
        doc = {"version": FORMAT_TUILES, "generator": f"glb2tiles {VERSION}", "source": chemin.name,
               "extent": {"min": lo, "max": hi}, "params": P.dict(), "warnings": avert,
               "roots": {"whole": ent, "split": len(plan.racines) - ent},
               "duplication": round(dup, 3), "tiles": fiches}
        if P.exclure:
            doc["excluded"] = {"patterns": P.exclure_motifs, "maxTriangles": P.exclure_max_tri, "maxMeshes": P.exclure_max_meshes,
                               "count": len(plan.exclus), "triangles": sum(x["tri"] for x in plan.exclus), "bytesSaved": plan.octets_exclus,
                               "names": dict(collections.Counter(x["nom"] for x in plan.exclus).most_common(20))}
        with open(Path(sortie) / f"{nom}.tiles.json", "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
            f.write("\n")
        poids = [x["bytes"] / MO for x in fiches]
        tris = [x["triangles"] for x in fiches]
        log("")
        log("== Rapport ==")
        log(f"Tuiles : {len(fiches)} dans {dossier}")
        log(f"Poids (Mo) : médiane {quantile(poids, 0.5):.1f} | 90 % sous {quantile(poids, 0.9):.1f} | maximum {max(poids):.1f}")
        log(f"Triangles : médiane {fmt(quantile(tris, 0.5))} | 90 % sous {fmt(quantile(tris, 0.9))} | maximum {fmt(max(tris))}")
        log(f"Duplication réelle de la géométrie (somme des tuiles / géométrie unique) : {virg(dup)}")
        log(f"Objets racine gardés entiers : {ent} | répartis : {len(plan.racines) - ent}")
        for ligne in lignes_exclusions(plan):
            log(ligne)
        for w in avert:
            log("Avertissement : " + w)
        log(f"[temps] {time.time() - t0:.1f} s ; {fmt(glb.octets_lus)} octets lus sur {fmt(glb.taille)}")
        return 0
    finally:
        glb.fermer()


if __name__ == "__main__":
    if "--version" in sys.argv[1:]:      # ni journal ni pause « Entrée »
        print(f"glb2tiles {VERSION}")
        sys.exit(0)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    journal = Path(__file__).resolve().with_name("glb2tiles.log")
    with open(journal, "w", encoding="utf-8") as lf:
        lf.write(f"[glb2tiles] {VERSION}\n")
    print(f"[glb2tiles] {VERSION}")
    code = 0
    try:
        code = main(log_path=journal)
    except SystemExit as e:
        if isinstance(e.code, str):
            log(e.code)
        code = e.code if isinstance(e.code, int) else 1
    except ErreurGlb as e:
        log(f"[ERREUR] {e}")
        code = 2
    except Exception:
        log(traceback.format_exc())
        code = 1
    print(f"[log] {journal}")
    if "--nopause" not in sys.argv and sys.stdin and sys.stdin.isatty():      # ni console (script, tâche planifiée) : pas de pause
        try:
            input("Entrée pour fermer...")
        except EOFError:
            pass
    sys.exit(code)
