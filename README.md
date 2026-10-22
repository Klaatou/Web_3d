# web_3d

Outils pour mettre une région 3D sur le web : `glb2html` (générateur de pages), le viewer de réglages et le serveur de présence.

Transforme une région 3D exportée en `.glb` (OpenSim, par exemple) en **page web autonome** : vue 3D, promenade avec avatar, visiteurs en temps réel, chat, zones et portails, carte des mondes.

Outils :

| Fichier fabriqué | Rôle |
|---|---|
| `glb-viewer.html` | Page de réglages et d'export : on charge un `.glb` (ou, depuis la v32, le dossier d'une région en tuiles), on règle la mer, le trou, la caméra, la promenade, les zones, la fiche de région, puis on exporte (zones et ligne de commande seulement pour une région en tuiles). |
| `glb2html.py` | Script qui fait la même chose en ligne de commande (hors ligne, sans navigateur). |
| `presence_server.py` | Serveur WebSocket de présence, chat, modération et compteurs de visiteurs. |
| `oar2glb.py` | Convertit une sauvegarde OpenSim (`.oar`) en `.glb` (convoar + réparation) ; `--version` affiche sa version. `--terrain-seul` ajoute le terrain complet des régions de plus de 256 m à un GLB existant. Détail : `MODE_EMPLOI.md` § 15. |
| `glb2tiles.py` (+ `glb-stats.py` à côté) | Découpe un GLB énorme en tuiles autonomes (`X.tiles/*.glb` + `X.tiles.json`) ; `--analyse` mesure et recommande sans rien écrire. `--exclure` écarte les « boîtes de livraison » d'un catalogue. La page charge ces tuiles autour de l'avatar (`glb2html.py --tiles`, v30). v31 : images vides ou tronquées remplacées par un gris, et vue d'ensemble légère `X.overview.glb` (toute la région, sans image) affichée au loin. v32 : références d'objets dans les tuiles (zones liées à un objet en mode tuiles). Détail : `MODE_EMPLOI.md` § 17 et § 17 bis. Poser des zones dans une région en tuiles avec le viewer : § 17 ter. |

## Fabriquer les fichiers

```
python build.py
```

Le résultat est dans `dist/`. Au premier lancement, three.js r160 est téléchargé dans `.cache/` (ou `python build.py --vendor DOSSIER` avec un paquet npm `three` déjà présent). Les fichiers de `dist/` ne sont pas versionnés : on les publie dans les « Releases » du dépôt.

## Utiliser

1. Ouvrir `dist/glb-viewer.html`, charger le `.glb`, régler, puis « Enregistrer dans un fichier » (section Réglages mémorisés) : on obtient `<nom>.reglages.json`.
2. Générer la page avec les mêmes réglages (une seule ligne) :

```
python glb2html.py "Region-final.glb" --settings --register regions.json --map-page carte.html -o "Region.html"
```

3. Lancer le serveur de présence : `python presence_server.py --log presence.log`.

`python glb2html.py --help` et `python presence_server.py --help` listent toutes les options.

## Mode modulaire

`--modular` produit, pour la page `Region.html` :

| Fichier | Rôle |
|---|---|
| `Region.html` | Coquille (~85 Ko), **identique pour toutes les régions** : elle déduit ses fichiers de son propre nom. Titre de l'onglet = `room`, fond = `skyColor`. |
| `Region.glb` | Le modèle, octets bruts. |
| `Region.config.json` | Réglages de rendu de la page (mer, caméra, promenade, présence, carte), sans les zones. Relu à chaque rechargement (F5). Détail et comparaison avec `.reglages.json` : `MODE_EMPLOI.md` § 16. |
| `Region.zones.json` | Les zones. Relu à chaque rechargement ; s'il est absent, `zones.json` du même dossier ; sinon aucune zone. |
| `lib/three-0.160.0/` | three.js, Draco et Meshopt, partagés par toutes les pages du dossier. |

Il faut servir le dossier en http/https (test local : `python -m http.server`). Copier une page sous un autre nom marche : renommer ses trois fichiers frères de la même façon.

```
python glb2html.py "Region-final.glb" --settings --modular -o "Region.html"
python glb2html.py --settings "Region-final.glb" --config-only --wave 2 -o "Region.html"
python glb2html.py -o "Region.html" --zones-only --zones zones.json
```

`--config-only` ne réécrit que la config (les zones ne bougent que si `--zones` est donné) ; `--zones-only` ne réécrit que les zones. Les visiteurs rechargent la page.

Le viewer exporte la même structure : bouton « Exporter la structure modulaire (.zip) », à côté de « Exporter HTML autonome » (page unique qui s'ouvre depuis le disque, sans serveur). Le `.html` du zip est identique à celui de `glb2html.py --modular`.

### Coquille unique pour plusieurs régions

Avec `--shared-shell`, une seule coquille (`index.html` par défaut) et un seul `lib/` servent plusieurs régions du même dossier ; chaque région n'ajoute que `NOM.glb`, `NOM.config.json` et `NOM.zones.json`, et s'ouvre à `index.html?region=NOM`. Sans paramètre `region`, la coquille se comporte comme avant (pages déjà publiées inchangées). NOM doit être un seul nom de fichier : `../x`, `https://…`, `a/b`, un nom vide ou commençant par un point sont refusés sans aucune requête réseau.

```
python glb2html.py "Ankh.glb" --settings --shared-shell --register regions.json -o "Ankh.html"
```

`-o` désigne la région (`Ankh.html` n'est pas écrit) ; la coquille et `lib/` ne sont écrits que s'ils sont absents. `--register` enregistre l'adresse `index.html?region=Ankh`. Détail : `MODE_EMPLOI.md` § 16.

### Zones liées à un élément du modèle

Une zone peut porter un champ `mesh` : le nom exact d'un élément du modèle. L'élément devient cliquable (curseur main, contour au survol), la touche E agit à moins de `radius` mètres de l'élément, et un portail se déclenche en s'approchant. Un élément traversable (`walkIgnore`) ne bloque pas le clic. Dans le viewer, section Zones : « Lier à un élément » (le clic ignore les éléments traversables) et « Délier ».

## Carte des mondes

`regions.json` est la carte : une liste de régions (nom, adresse, X, Y, point d'arrivée, salon, serveur de présence, vignette). `--register` y ajoute ou met à jour la région en cours de génération ; `--map-page` génère une page web de la carte avec un lien cliquable par région ; `--map-url a.json,b.json` fusionne les cartes de plusieurs propriétaires à chaque ouverture de la page.

## Développer

Voir `CLAUDE.md` (architecture, décisions, feuille de route) et `HISTORIQUE.md` (comment retrouver chaque version) `tests/smoke.py` (test de fumée dans Chromium sans tête) `tests/modulaire.py` (mode modulaire universel, zones liées, exports du viewer) et `tests/portail_interne.py` (portail dans la même région), `tests/tuiles.py` (région en tuiles chargée par la coquille : rayon, budget, sol continu, blocage, échecs), `tests/v31.py` (images invalides, vue d'ensemble, sortie de promenade), `tests/v32.py` (zones dans une région en tuiles : viewer, zones liées à un objet, position affichée) et `tests/v23.py` (clic, liaison, rotation). Mode d'emploi des zones et portails : `MODE_EMPLOI.md`.

## Sécurité

Ne jamais committer : adresses Home Assistant (`zones*.json`), `*.reglages.json`, `presence_identities.json`, `presence_bans.json`, journaux. Le `.gitignore` les exclut. Le profil `--profile public` retire les zones privées des pages publiées.

## Licence

À choisir par le propriétaire du dépôt. three.js (MIT) et les décodeurs embarqués : voir `THIRD-PARTY.md`.
