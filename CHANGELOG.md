# Journal des versions

Les dates sont au format jj/mm/aaaa.

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
