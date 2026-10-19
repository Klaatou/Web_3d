# Journal des versions

Les dates sont au format jj/mm/aaaa.

## v24 (19/10/2026)
- Page exportée (autonome et modulaire) : plus aucun cylindre pour les zones lien web, commande HA et portail. Zone liée à un élément : aucun objet ajouté ; au survol, curseur main, léger contour de l'élément et infobulle (nom + destination : adresse web, « Région : … », « Commande : … » ; jamais le webhook). Zone non liée : marqueur discret au sol (anneau fin noir et blanc d'environ 1 m + disque translucide, relevé de 10 cm et décalé vers la caméra pour ne pas être masqué par un sol irrégulier) avec le même survol ; la surface de visée est plus large que le marqueur et masquée par le relief. Clic = suivre le lien. Plus de panneau de texte permanent : le nom ne s'affiche qu'au survol ou à portée (« E : … »).
- Le marqueur se recolle au sol réel (rayon vers le bas depuis 1,5 m au-dessus de la zone) seulement si aucune surface n'existe à moins de 15 cm de la zone (une zone calée au sol sous une box reste au sol), donc il reste visible même si la zone a été posée un peu sous le relief ; sans sol trouvé, il est tracé sans test de profondeur. À l'approche, le message du bas indique aussi la destination (« E : nom → destination »).
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
