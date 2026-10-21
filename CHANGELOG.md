# Journal des versions

Les dates sont au format jj/mm/aaaa.

## v26 (21/10/2026)
- **Coquille unique en mode modulaire.** Une seule coquille (par défaut `index.html`) et un seul `lib/three-0.160.0/` servent plusieurs régions d'un même dossier ; chaque région n'ajoute que `NOM.glb`, `NOM.config.json` et `NOM.zones.json`. Adresse : `index.html?region=NOM` (`NOM.html` accepté : l'extension est retirée).
- La coquille reste identique, octet pour octet, pour toutes les régions (elle lit `?region=` à l'exécution). **Sans paramètre `region`, comportement inchangé** (fichiers déduits du nom de la page) : les pages déjà publiées et leurs coquilles continuent de marcher. Sans paramètre ni fichier correspondant : « Erreur : … introuvable (HTTP …) ».
- **Sécurité.** NOM doit être un seul nom de fichier : un nom vide, contenant `/` `\` `:` `?` `#` ou `..`, des caractères de contrôle, ou commençant par un point est refusé avec un message dans la page et **aucune requête réseau** (sinon `?region=https://autre-site/x` ferait charger config, zones et modèle depuis un site étranger). Contrôle fait avant toute requête ; le script `glb2html.py` applique la même règle à `-o`.
- `glb2html.py --shared-shell [COQUILLE.html]` (implique `--modular`) : `-o` désigne la région ; n'écrit que `X.glb`, `X.config.json`, `X.zones.json`, plus la coquille et `lib/` **s'ils sont absents** (une coquille existante et différente est conservée, avec avertissement). `--register` écrit l'adresse `COQUILLE.html?region=NOM` dans `regions.json` ; `--config-only` et `--zones-only` marchent avec cette structure. Vérifiés : `#spawn=` ajouté après la query string (carte, portails), « vous êtes ici » (reconnu par le salon puis par l'adresse complète), portail vers la même région (aucune navigation) ou vers une autre région de la même coquille.
- Viewer : « Exporter la structure modulaire (.zip) » donne `index.html`, `NOM.glb`, `NOM.config.json`, `NOM.zones.json`, `lib/` (la région s'ouvre à `index.html?region=NOM`) ; le récapitulatif pour le script a une case « Coquille commune » (`--shared-shell` à la place de `--modular`). **Changement** : le `.zip` ne contient plus `NOM.html` mais `index.html`.
- `tools/oar2glb.py` : `--version` (affiche `oar2glb vNN (jj/mm/aaaa)` sans journal ni pause), version en première ligne du journal (`[oar2glb] …`), fabriqué dans `dist/oar2glb.py` par `build.py` (marqueur `__VERSION__`, comme `presence_server.py`).
- `tools/oar2glb.py --reencode` : les textures que Pillow ne sait pas lire sont remplacées par un gris neutre 4x4 au lieu d'être laissées à convoar (constat : convoar plante dans `OpenJPEG.DotNetDecode64` après environ 30 minutes sur une région 4x4 de 17 173 textures dont 762 illisibles) ; liste écrite dans `X-reenc-illisibles.txt` ; 8 cœurs au plus et lots de 512 pour borner la mémoire ; test ajouté dans `tests/oar2glb.py`.
- Tests : `tests/modulaire.py` étendu (deux régions avec la même coquille, région simple inchangée, absence de fichier, paramètres refusés `../x`, `https://…`, `a/b`, vide, point initial, encodés en pourcentage, sans aucune requête réseau ; carte, `#spawn=`, portails) ; `tests/oar2glb.py` (version source et `dist/`, première ligne du journal).
- Docs : `MODE_EMPLOI.md` § 16 (coquille unique), § 6 et § 15 ; `README.md` ; `CLAUDE.md` (décisions v26 ; feuille de route : régions énormes, notes seulement, rien d'implémenté).

## v25 (20/10/2026)
`tools/oar2glb.py` : correction des animaux riggés (animesh) et des prims invisibles, validée sur un vrai OAR (Jungle_Isle : 771 parties, 34 meshes riggés). Cette version regroupe les itérations de mise au point du 20/10/2026.
- **Meshes riggés reconstruits depuis l'OAR.** Pour tout mesh riggé, le `.llmesh` de l'OAR (`assets/*_mesh.llmesh`) est décodé (positions, normales, UV, triangles, domaine de position, bloc skin zlib + LLSD binaire) et `bind_shape_matrix` est appliquée ; l'échelle du prim est ignorée. Raison : la géométrie que convoar écrit pour ces meshes est inutilisable (étendues de sommets identiques pour des animaux différents, échelle cuite inconnue de l'OAR). Aucune règle propre à un animal. Matériaux et textures repris du nœud GLB (face i = primitive i), sens des UV détecté. Si le `.llmesh` est illisible, le mesh reste tel que convoar l'a produit.
- **Placement.** Les morceaux d'un même animal (un cheval = 6 meshes de même nom, chacun avec sa `bind_shape_matrix`) sont déplacés ensemble : centrés à l'horizontale sur la racine, rotation = racine x rotation du premier morceau, pieds sous la boîte racine (z moins la moitié de son échelle) ou à l'altitude de la racine si elle est elle-même riggée. Le terrain de l'OAR n'est pas utilisé. Garde-fou : une taille hors de 0,1 à 12 m laisse le mesh tel quel.
- **Prims invisibles retirés** (`--keep-invisible` pour les garder) : toutes les faces à alpha 0, ou texture invisible standard (`8dcd4a48-…`, `3a367d1c-…` ; `e97cf410-…` est le dégradé alpha, visible), nœuds dont tous les matériaux sont à alpha 0, et boîte racine d'animesh (prim simple, racine d'un objet dont toutes les autres parties sont des meshes riggés). Les enfants d'une racine retirée restent.
- **Correspondance nœud GLB ↔ partie de l'OAR** : UUID du prim, sinon UUID du mesh, sinon nom + position (2 m), ordre de l'OAR à distance égale. convoar ne conserve aucun UUID : sur Jungle_Isle tout passe par nom + position.
- **`--diag`** : ne modifie rien, ne lance pas convoar ; une ligne par partie de l'OAR (nom, UUID, riggé, échelle du prim, `bind_shape_matrix`, domaine de position, transparent, boîte racine d'animesh, nœud GLB trouvé et méthode, matériau GLB). Lit le `.gltf` de `<oar>-GLTF` (conservé par `--keep`), sinon le `.glb` voisin, ou `--glb`. Journal dans `oar2glb.diag.log` (la conversion écrit `oar2glb.log`).
- **`--reperes`** : un mât rouge de 15 m à chaque animal riggé posé, pour les retrouver dans le viewer.
- **Textures** : constat sur Jungle_Isle : `--reencode` faisait manquer environ 150 images sur 353 (textures grises) ; sans lui, aucune absente. Le script compare les images annoncées par le `.gltf` aux fichiers présents, relance convoar (2 essais de plus au maximum) en gardant les images déjà écrites, et résume les absentes en une ligne.
- Journal : « N mesh(es) riggé(s) remis à l'échelle, M prim(s) invisible(s) retiré(s) » et une ligne `[contrôle]` par animal (objets dont la boîte englobante contient son centre).
- Tests : `tests/oar2glb.py` (OAR synthétique, faux convoar, deux variantes de GLB : UUID dans les extras ou noms seuls ; cheval en 2 morceaux, mesh non normalisé, racine tournée, taille implausible, image manquante).
- `MODE_EMPLOI.md` : section 15 complète (commandes de `oar2glb.py`).

## v24 (19/10/2026)
- Page exportée (autonome et modulaire) : plus aucun cylindre pour les zones lien web, commande HA et portail. Zone liée à un élément : aucun objet ajouté ; au survol, curseur main, léger contour de l'élément et infobulle (nom + destination : adresse web, « Région : … », « Commande : … » ; jamais le webhook). Zone non liée : marqueur discret au sol (disque plat de 0,4 m + anneau fin, semi-transparent) avec le même survol ; la surface de visée est plus large que le marqueur et masquée par le relief. Clic = suivre le lien. Plus de panneau de texte permanent : le nom ne s'affiche qu'au survol ou à portée (« E : … »).
- Nouvelle option par zone « Toujours afficher le nom » (champ `showName`, décochée par défaut ; viewer, `clean_zones`, `.zones.json`, `.reglages.json`) : nom permanent au-dessus de l'élément ou du marqueur ; panneau complet pour une zone non liée de forme « panneau ».
- Viewer (édition) : cylindres conservés et toujours visibles pour toutes les zones non liées, panneaux compris (portée), contour pour les zones liées. Pas d'infobulle en édition.
- Changement de comportement : les zones non liées de forme « panneau » ne sont plus dessinées dans la page exportée sauf avec « Toujours afficher le nom ».
- La page exportée expose `window.__viewer` (comme le viewer) pour les tests.
- Tests : nouveau `tests/v24.py` (aucun mesh de cylindre, zone liée sans objet ajouté, marqueurs, infobulle avec destination exacte, webhook non affiché, marqueur masqué par le relief, clic, nom permanent, cylindres du viewer, case à cocher), en modulaire et en autonome.
- `MODE_EMPLOI.md` : nouvelle section 2 bis.

## v23 (19/10/2026)
- Viewer, clic : un clic simple sur le modèle n'a plus d'effet sur la cible caméra ni sur le cercle d'atterrissage, dans aucun mode. Il affiche le nom de l'élément ET les coordonnées du point touché (x, y, z, 2 décimales) dans « picked » et la barre d'état. Seul le double-clic choisit la cible / l'atterrissage, comme la page exportée.
- Viewer, zone : bouton « Placer ici (dernier point cliqué) » (copie x, y, z du dernier clic simple).
- Liaison à un élément : on lie le morceau réellement cliqué. Si son nom est partagé par plusieurs objets (OAR : prims répétés), la zone stocke `nom#index` (rang de l'objet parmi ceux de ce nom, ordre de parcours three.js). Nom unique : le nom seul, comme avant (zones existantes inchangées). Règle commune : `resolveMeshRef` (core.js) et `resolve_mesh_ref` (glb2html.py). glb2html.py n'ouvre pas le GLB : il ne fait que transporter la référence.
- `LINK_MAX` passe de 30 à 10 m. Refus : « Élément trop grand (L × l × h m) : probablement fusionné avec un bâtiment dans l'OAR. Délie-le dans OpenSim ou utilise une zone cercle. »
- Viewer : au chargement d'un GLB dont les réglages sont restaurés depuis le navigateur, la barre d'état dit « Réglages restaurés depuis la mémoire du navigateur (N zone(s)) ».
- Correctif : « Oublier les réglages de ce fichier » était annulé en 1,5 s par l'enregistrement automatique ; la mémoire reste maintenant vide jusqu'à la prochaine modification.
- Rotation de la région (0, 90, 180, 270°, axe vertical) : réglage `rotate` (liste dans le viewer, `--rotate` dans glb2html.py, `rotate` dans la config, `.reglages.json` et la commande générée ; relu par `--settings`). Appliquée à la racine du modèle au chargement, avant recentrage, boîte englobante, sol de promenade, trou et vignette. Changer la valeur dans le viewer fait tourner du même angle, autour du centre de la région : zones (position + orientation), arrivées, caméra, cible (donc atterrissage), dernier point cliqué, et le trou de la mer (non demandé, mais il resterait hors de l'île sinon). Zones liées : elles suivent leur élément. Les zones d'un fichier donné à `--rotate` sont déjà dans le repère tourné.
- `MODE_EMPLOI.md` mis à jour pour la v23 : clic et double-clic, « Placer ici », formats de lien web, limite de 10 m et linksets OpenSim, rotation et vignette, dépannage, nouvelle section 14 « Réglages mémorisés ».
- Tests : nouveau `tests/v23.py` (clic simple sans effet, double-clic, « Placer ici », deux meshes de même nom à 100 m, mesh de 30 m refusé, rotation 180 avec zone sur le mesh nord, mémorisation, page générée `--rotate 180` aux mêmes positions que le viewer, « Oublier »). Pour obtenir de vrais doublons de nom, le modèle de test instancie un mesh à deux primitives : three.js rend uniques les noms de nœuds (`_instance_N`), mais les enfants des clones gardent leur nom.

## v22 (19/10/2026)
- Portail interne : un portail dont la « Page de destination » est vide, ou désigne la page elle-même, pose le visiteur sur le point d'arrivée indiqué de la même région (fondu, sans rechargement : présence et chat conservés). Avant, la page restait sur un écran noir. Arrivée absente : message « Point d'arrivée … introuvable dans cette région ».
- Noyau : `teleportTo(pos, yaw)` (hors promenade : `walkStart`). Les portails « en marchant dedans » sous les pieds à l'arrivée ne se déclenchent pas tout de suite (pas de ping-pong).
- Viewer : libellé « Page de destination (adresse ou fichier .html ; vide = cette région) » ; l'aperçu applique le portail interne en promenade.
- `MODE_EMPLOI.md` : zones, arrivées, portails (même région et autre région), panneaux, liaison, zones privées, publication, dépannage.
- Tests : nouveau `tests/portail_interne.py` ; `tests/modulaire.py` attend le chargement réel des pages exportées au lieu d'un délai fixe (échouait sur une machine lente).

## v21 (19/10/2026)
- Correctif viewer, « Lier à un élément » sur un gros modèle (Ankh) : le contour affiché était un énorme cube noir ou un petit cube sous la région, et le cercle d'atterrissage pouvait se déplacer.
- Mode liaison exclusif : le noyau ignore clics, double-clics et survol pendant la liaison (le double-clic déclenchait l'atterrissage) ; il reste verrouillé 600 ms après une liaison réussie. Le mode se quitte en cliquant sur le bouton, en posant une zone ou en plaçant le trou.
- On lie le mesh nommé touché (éléments traversables ignorés), non un parent. Boîte englobante calculée en coordonnées monde après mise à jour des matrices depuis la racine (`boxOfMeshes`). Boîte vide ou non finie : élément refusé.
- Un élément de plus de 30 m est refusé avec un message ; le refus laisse le mode actif.
- Le viewer affiche le nom choisi, sa taille en mètres et un contour fil de fer. La sélection d'une zone liée contourne l'élément lui-même (la boîte du groupe de repère, non rendue, produisait le cube parasite).
- Test : modèle à racine décalée et mise à l'échelle ×2 avec voile traversable et sol géant (`tests/modulaire.py`, `test_liaison`).

## v20 (18/10/2026)
- Mode modulaire universel : la coquille `<page>.html` est la même, octet pour octet, pour toutes les régions (~85 Ko). Elle déduit ses fichiers de son propre nom (`X.html` charge `X.config.json`, `X.glb` et `X.zones.json` du même dossier) : aucun nom écrit en dur, elle se copie sous un autre nom avec ses trois fichiers frères renommés. Titre de l'onglet = champ `room` de la config, fond = `skyColor`. `lib/three-0.160.0/` contient toujours Draco et Meshopt (la coquille ne dépend plus du contenu du `.glb`).
- Zones relues à chaque rechargement : `X.zones.json`, sinon `zones.json` du même dossier, sinon aucune zone, sans erreur. Corrige la v19, où modifier `zones.json` dans le dossier du site n'avait aucun effet (les zones étaient figées dans la config). Le mode modulaire écrit les zones dans `X.zones.json`, jamais dans `config.json` (`zones: []`).
- `--config-only` ne touche pas `X.zones.json`, sauf si `--zones` est donné. `--zones-only` marche sur une page modulaire (`-o X.html --zones z.json`). Régénérer avec `--modular` sans source de zones n'écrase pas un `X.zones.json` existant.
- Viewer : bouton « Exporter la structure modulaire (.zip) » à côté de « Exporter HTML autonome » (inchangé) : `X.html`, `X.glb`, `X.config.json`, `X.zones.json`, `lib/three-0.160.0/` (`draco/` compris). Le `X.html` du zip est identique octet pour octet à celui de `glb2html.py --modular` : `build.py` prend le texte de la coquille dans `gen_tpl.py` (`build_shell`), sans le recopier.
- Zones liées à un élément du modèle (champ `mesh`, nom exact) : l'élément devient cliquable (curseur main, contour au survol), touche E à moins de `radius` mètres de l'élément, portail déclenché en s'approchant. Un élément traversable (`walkIgnore`) ne bloque pas le clic (valable pour toutes les zones). Si l'élément est introuvable dans le modèle, la zone reste à sa position.
- Viewer : boutons « Lier à un élément » (le clic ignore les éléments traversables : il lie la boîte, pas le voile transparent devant) et « Délier » dans chaque zone. `mesh` est validé dans `clean_zones`.
- `--title` et `--zones-live` sont ignorés (avec avertissement) en mode modulaire.
- Tests : nouveau `tests/modulaire.py` (coquille identique, copie renommée, rechargement des zones, secours `zones.json`, `--config-only` / `--zones-only`, zones liées, voile traversable, touche E, portail à l'approche, deux exports du viewer, zip) ; `tests/smoke.py` inchangé.

## v19 (18/10/2026)
- Mode modulaire : `--modular` écrit une coquille légère `<page>.html` (~80 Ko), `<page>.glb` (octets bruts, non encodés), `<page>.config.json` (le même `cfg` que la page autonome, zones et carte comprises) et `lib/three-0.160.0/` partagé par toutes les pages du dossier (modules à plat, décodeurs Draco/Meshopt ajoutés au besoin). La page se charge par `fetch` : elle exige http(s) (message explicatif si ouverte depuis le disque). Le mode autonome reste le défaut.
- `--config-only -o page.html` : réécrit seulement `<page>.config.json` (et `regions.json` / la page carte avec `--register` / `--map-page`), sans toucher au `.glb` ni à la coquille. Le salon (`room`) existant est conservé si `--room` n'est pas donné. Les visiteurs rechargent la page pour voir le changement.
- `build_html` est scindé : `build_cfg` fabrique le dictionnaire de réglages (commun aux deux modes) ; `build_html` accepte `modular=True`.
- Viewer : case « Mode modulaire » (ajoute `--modular` à la commande, courte ou non). L'export de page depuis le viewer reste autonome.
- `tests/smoke.py` : teste le mode modulaire sous `python -m http.server` (chargement des 3 GLB, cfg identique au mode autonome, modification de `config.json` puis rechargement, `--config-only`, config absente, ouverture depuis le disque).

## v18 (18/10/2026)
- `--settings [FICHIER]` : le script relit tous les réglages enregistrés par le viewer (trou, vagues, caméra, zones, fiche de région, vignette). La ligne de commande l'emporte sur le fichier.
- Viewer : case « Commande courte » (utilise `--settings`).
- `--register` sans `.glb` : ajoute ou met à jour une région dans `regions.json` sans rien régénérer (région d'un collègue, par exemple).
- Chaque région peut porter son propre serveur de présence (`presence`) ; la carte interroge chaque serveur.
- `--map-url` accepte plusieurs adresses séparées par des virgules (cartes de plusieurs propriétaires, fusionnées).
- `--thumb` accepte une adresse http(s) (vignette en lien).
- `--map-page` n'écrase plus la page carte par une page vide.

## v17 (18/10/2026)
- Carte : `--register`, `--region-name`, `--region-url`, `--region-xy`, `--region-spawn`, `--thumb`.
- Page web « carte des mondes » : `--map-page` (liens réels vers chaque région, compteurs de visiteurs).
- Viewer : bouton « Enregistrer la vignette (.jpg) », champ « page carte », ligne de commande avec `--register`.
- Placement compact de la carte : les grands vides entre régions sont compressés.

## v16 (18/10/2026)
- Mémorisation des réglages par fichier, carte des mondes (touche M), zones/portails, présence, chat, modération.

## v1 à v15
- Développement initial (viewer, export HTML autonome, promenade, présence). Les décisions sont dans CLAUDE.md.
