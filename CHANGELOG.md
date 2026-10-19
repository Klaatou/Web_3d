# Journal des versions

Les dates sont au format jj/mm/aaaa.

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
