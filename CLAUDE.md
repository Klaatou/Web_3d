# web_3d (outil glb2html) — contexte pour Claude Code

## Façon de travailler avec le propriétaire (JJ)
- Réponses en français, directes et techniques. Une seule solution recommandée, pas de liste d'options.
- Patchs chirurgicaux plutôt que réécritures ; livrer des fichiers complets qui fonctionnent.
- Commandes PowerShell (Windows, chemins du type `P:\...`) **sur une seule ligne**.
- Ne jamais s'appuyer sur la couleur seule dans un diagnostic ou une consigne (accessibilité).
- Dates en chiffres, jj/mm/aaaa.
- Il corrige sèchement : reconnaître l'erreur sans se défendre, corriger.
- Tester avant de livrer (voir Tests). Ne rien annoncer qui n'ait été exécuté.

## Architecture
- `src/core.js` : noyau JS partagé (collisions, promenade, avatars, zones, carte, chat). Inséré dans `template.html` ET dans `viewer_tpl.html`.
- `src/template.html` : page exportée (placeholders `__IMPORTMAP__`, `__CONFIG__`, `__GLB_B64__`, `__DECODERS__`, `__TITLE__`, `__SKY_HEX__`, `__CORE__`).
- `src/viewer_tpl.html` : page de réglages/export ; embarque le template et le script Python pour pouvoir exporter et fournir la ligne de commande.
- `src/gen_tpl.py` : script de génération (devient `dist/glb2html.py`). Points d'entrée : `build_html` (cfg + page), `generate`, `build_shell` (coquille modulaire universelle), `main` (arguments ; `--settings` relit le fichier en deux passes d'argparse), `clean_map` / `clean_zones` (assainissement), `register_region`, `write_map_page` (+ `MAP_PAGE_TEMPLATE`), `settings_defaults`.
- `src/presence_server.py` : serveur WebSocket (bibliothèque `websockets`).
- `build.py` : assemble le tout dans `dist/`. **Ne jamais éditer `dist/`** : modifier `src/` puis `python build.py`. Le texte de la coquille modulaire n'est écrit qu'une fois, dans `gen_tpl.py` (`build_shell`) : `build.py` charge le script fabriqué et en tire la coquille pour le viewer (export `.zip`), sans la recopier.
- Contraintes de fabrication : les textes insérés dans des chaînes Python `r"""..."""` ne doivent contenir ni `"""` ni finir par `\` (build.py le vérifie). `__VERSION__` est remplacé partout, y compris dans `MAP_PAGE_TEMPLATE`.
- Les clés de `cfg` doivent rester identiques entre l'export du viewer (JS) et celui du script (Python).
- Version : fichier `VERSION` + `CHANGELOG.md` à chaque livraison.

## Décisions techniques acquises
- Page exportée 100 % autonome par défaut : three.js r160, GLTFLoader, OrbitControls, Draco et Meshopt en `data:` dans l'importmap ; GLB en base64. Aucun réseau à l'ouverture, ouverture possible depuis le disque.
- `0.0.0.0` n'est pas une adresse de connexion : `ws://0.0.0.0:p` devient `ws://127.0.0.1:p` (script et viewer).
- Pas de collisions entre visiteurs (positions côté client).
- Zones en JSON séparé (pas dans le GLB). `zones.json` cherché dans le dossier de lancement puis dans celui du script (idem `regions.json`). `--zones-live` recharge les zones à chaque ouverture (http seulement).
- Haute résolution = supersampling ×2 minimum. Mer : 400 segments par défaut (maille 10 m) pour que le trou soit net.
- Collision : `door` = début de mot ; `=mesh_346_5` = nom exact.
- Carte : X est / Y nord (style OpenSim), pas de borne ; placement compact (un vide de plus de 2 cases compte pour 2 ; liste simple si coordonnées en double ou plus de 14 colonnes/lignes).
- Réglages mémorisés par fichier (clé nom+taille du `.glb`) dans le navigateur ; export/import `.reglages.json`, relu par `glb2html.py --settings`.
- Sécurité : les adresses de carte/zones sont filtrées (http/https), vignettes = data:image ou lien, tailles bornées. Le profil `public` retire les zones privées (Home Assistant).

## Décisions de la session du 18/10/2026 (à respecter)
- La carte vit dans `regions.json` (un fichier), alimenté par `--register` à chaque génération ; page web de la carte par `--map-page`.
- Fédération : `--map-url` accepte plusieurs adresses (fusion) ; chaque région peut avoir son serveur de présence (champ `presence`).
- **JJ veut un mode modulaire** : la page région est déjà énorme (GLB en base64, plus de 17 Mo) et grossira ; carte, zones et paramètres ne doivent pas y être figés. Le mode autonome actuel reste disponible (ouverture depuis le disque).
- **La fédération de la carte doit pouvoir tourner sur l'hébergement du `presence_server.py`.** JJ a 3 régions, un collègue 2, un autre 2 : le souci n'est pas le poids mais la logistique (qui envoie quoi à qui, regénération des pages).

## Décisions de la v23 (19/10/2026)
- Clic simple = information seule (nom + point) ; seul le double-clic déplace cible et atterrissage.
- Rotation de la région (`rotate` : 0/90/180/270) appliquée au chargement à la racine du modèle, avant recentrage. Les positions stockées (zones, arrivées, cible, trou) sont dans le repère déjà tourné : le viewer les fait tourner quand on change la valeur, glb2html.py ne les touche jamais.

## Décisions de la v25 (20/10/2026) : `tools/oar2glb.py`
- La géométrie que convoar écrit pour les meshes riggés (animesh) est inutilisable (mêmes étendues de sommets pour des animaux différents, échelle cuite inconnue de l'OAR) : le script les reconstruit depuis `assets/*_mesh.llmesh` (zlib + LLSD binaire : `high_lod`, `skin`) et applique `bind_shape_matrix` ; l'échelle du prim est ignorée. Aucune règle propre à un animal ou à un OAR.
- convoar ne conserve aucun UUID dans le GLB : la correspondance nœud ↔ partie de l'OAR se fait par nom + position (ordre de l'OAR à distance égale).
- Ne pas utiliser `--reencode` par défaut : sur Jungle_Isle il faisait manquer environ 150 textures sur 353.
- `e97cf410-…` est le dégradé alpha (visible) ; les textures invisibles sont `8dcd4a48-…` et `3a367d1c-…`.
- Le terrain de l'OAR peut être plat (21 m) : les animaux sont posés sous leur boîte racine, jamais sur le terrain.
- Tester avec `python tests/oar2glb.py` ; sur un vrai OAR : `--keep --reperes` puis `--diag`. Le journal de conversion est `oar2glb.log`, celui du diagnostic `oar2glb.diag.log`.

## Décisions de la v26 (21/10/2026) : coquille unique
- Une seule coquille (par défaut `index.html`) et un seul `lib/` pour plusieurs régions d'un dossier ; par région : `X.glb`, `X.config.json`, `X.zones.json`. Adresse `COQUILLE.html?region=NOM`. La coquille reste identique octet pour octet et lit `?region=` à l'exécution (aucun nom écrit dedans) ; sans `region`, comportement d'avant (fichiers déduits du nom de la page).
- **Sécurité, non négociable** : NOM = un seul nom de fichier ; refusé (message dans la page, aucune requête réseau) s'il est vide, contient `/` `\` `:` `?` `#` `..` ou un caractère de contrôle, ou commence par un point (après retrait de `.html`). La règle existe deux fois, à garder identique : JS dans `SHELL_BOOT_NEW` et `valid_region_name` (gen_tpl.py) ; le viewer la reprend pour son `.zip`. Ne jamais accepter une adresse dans `region` (portails piégés, webhooks Home Assistant envoyés ailleurs).
- `glb2html.py --shared-shell [COQUILLE.html]` (implique `--modular`) : `-o` désigne la région, `X.html` n'est pas écrit ; coquille et `lib/` écrits seulement s'ils sont absents, une coquille existante et différente n'est jamais écrasée (avertissement). `--register` écrit `COQUILLE.html?region=NOM` (`page_name_of`, `shell_page_address`).
- Le `.zip` du viewer contient `index.html` (et non plus `NOM.html`).
- `tools/oar2glb.py` porte `__VERSION__` ; `build.py` en fabrique `dist/oar2glb.py`. `--version` sort avant l'ouverture du journal et avant la pause « Entrée ».

## Décisions de la v28 (21/10/2026) : `tools/glb2tiles.py`
- **Tuiles autonomes** : une tuile = un GLB valide qui s'ouvre seul ; les meshes partagés entre tuiles sont dupliqués dans chaque tuile qui les utilise (une bibliothèque commune serait trop lourde : 525 à 560 Mo pour la 4X4). Ce lot n'écrit que les tuiles et `X.tiles.json` ; ni `src/core.js`, ni `template.html`, ni `viewer_tpl.html` ne sont touchés.
- **Budget en Mo ET en triangles** (`--budget 32`, `--budget-tri 1500000`) : le poids seul ne suffit pas (Aestia : jusqu'à 5,1 M de triangles dans un seul bloc de 64 m). Poids autonome = octets compactés des primitives distinctes + images distinctes.
- **Règle des objets entiers par le poids, pas par l'étendue seule** : un objet racine reste entier si poids autonome ≤ `--entier-poids` (16 Mo) ET étendue ≤ `--entier-etendue` (256 m). L'étendue d'un objet racine ne dit rien de sa taille réelle (« Federalist House » 67 m, 447 meshes ; « Gandalf Statue » 168 m, 27 meshes ; des maisons de 167 m n'ont qu'un mesh) : une règle d'étendue seule couperait des centaines de maisons. Objet avec skin : jamais réparti. Mesh unique plus lourd que le budget (terrain, mer) : avertissement, pas de découpage par triangles à ce stade.
- **Accessors partagés** : des meshes différents partagent souvent un tampon de sommets dont chacun n'utilise qu'une partie ; la somme brute des accessors surestime le poids réel et le champ « sommets rendus » de `glb-stats` est trompeur. glb2tiles compte les sommets réellement indexés (lecture des indices par morceaux) et, quand un mesh n'utilise qu'une partie d'un tampon, lit ses positions pour avoir sa vraie boîte (celle de l'accessor ne convient pas).
- Aucune valeur propre à une région dans le code ; tous les seuils sont des paramètres. Valeurs aberrantes (tatooine2 : prim de 3 097 m) : acceptées, signalées (`--aberrant`).
- `glb-stats.py` : fonctions communes `modele(g)` et `rapport(...)` réutilisées par `glb2tiles.py` (qui l'exige à côté de lui, `build.py` copie les deux dans `dist/`).
- **Mesures des six régions** (avec `glb-stats.py`) : 4X4 « Free House Gallery » 1,2 Go (889 Mo de géométrie, 300 Mo de textures, 30 239 meshes, 60 641 instances, 44,8 M triangles, 1 825 objets racine dont 521 > 64 m et 175 > 128 m, 1 392 x 1 251 m ; blocs de 64 m : 253 non vides, médiane 12 Mo, maximum 78 Mo, 2,1 M triangles au plus ; blocs de 128 m trop lourds : 140 Mo, 3,4 M) ; Aestia 253 Mo (15,8 M triangles, 4,4 M sommets uniques ; blocs de 64 m : médiane 18 Mo, maximum 73 Mo, 5,1 M triangles dans un bloc) ; tatooine2 131 Mo (5,8 M triangles, 944 x 4 005 m, hauteur -3 176 à 3 137 m à cause d'un prim de 3 097 m ; 38 blocs, maximum 50 Mo) ; Club House 50 Mo (2,7 M triangles), Hobbit 28 Mo (0,8 M), Ankh Island 12 Mo (1,5 M) : légères. De 52 à 77 % de la géométrie est utilisée par plusieurs blocs de 64 m (3 % pour Club House).
- Mesuré sur un GLB synthétique de 146 Mo (4 000 instances, 400 meshes) : analyse en 1,7 s pour 40 Mo de mémoire ; découpage en 70 tuiles en 22 s.

## Feuille de route (priorité décroissante)
1. ~~Mode modulaire~~ **fait (v19), rendu universel en v20.** Sorties : `<page>.html` (coquille, identique pour toutes les régions, octet pour octet), `<page>.glb`, `<page>.config.json` (= le dict `cfg`, sans zones : `zones: []`), `<page>.zones.json` et `lib/three-0.160.0/` (Draco et Meshopt toujours présents). Décisions :
   - La coquille ne contient aucun nom : elle déduit `X.config.json`, `X.glb`, `X.zones.json` du nom de sa propre page (`location.pathname`), titre = `room`, fond = `skyColor`. Copier la page sous un autre nom avec ses fichiers frères renommés doit marcher.
   - Zones : relues à chaque F5 depuis `X.zones.json`, sinon `zones.json` du même dossier, sinon aucune (sans erreur). Jamais dans `config.json`. `--config-only` ne touche pas `X.zones.json` sauf avec `--zones` ; `--zones-only` marche sur une page modulaire ; régénérer sans source de zones n'écrase pas un `X.zones.json` existant.
   - Le viewer exporte la structure en `.zip` (bouton à côté de « Exporter HTML autonome », qui ne change pas). Son `index.html` (v26 ; avant : `X.html`) doit être identique octet pour octet à celui de `glb2html.py --modular`.
   - Zones liées à un élément : champ `mesh` (nom exact, ou `nom#index` si plusieurs objets portent ce nom : v23, `resolveMeshRef` / `resolve_mesh_ref`; limite 10 m) ; élément cliquable, E à moins de `radius` m de l'élément (boîte englobante), portail à l'approche ; un élément `walkIgnore` ne bloque pas le clic. Introuvable : la zone reste à sa position.
2. **`presence_server.py` comme hébergeur de la carte et des pages.** Avec `websockets` ≥ 13 (`websockets.asyncio.server.serve(..., process_request=...)`), répondre en HTTP aux requêtes non WebSocket :
   - `--serve-dir DOSSIER` : fichiers statiques (pages, glb, config, lib, vignettes), protection contre `..`, types MIME, `Cache-Control: no-store` pour les `.json`, `Access-Control-Allow-Origin: *` pour `GET /regions.json`. TLS déjà géré (`--cert/--key`) : tout sur un seul port.
   - Registre de carte : `GET /regions.json` ; fichier `presence_regions.json` (relatif au script) ; enregistrement authentifié par une clé propre à chaque propriétaire (`--keys`, valeurs hachées) ; `glb2html.py --publish ws://… --key …` pousse la fiche après génération.
   - Pairs : `--peer https://autre/regions.json` relus périodiquement et fusionnés en lecture seule.
   - Bornes : vignette ≤ 140 Ko, nombre de régions limité, journal des enregistrements.
3. Autres idées citées : état réel des objets Home Assistant visible en 3D ; couche de décor (objets GLB ajoutés sans régénérer) ; avatars VRM (three-vrm, distribués par le serveur de présence) ; chat : filtre de mots et commande `/mute`.
4. **Régions énormes : tuiles à deux niveaux de détail** (notes seulement, rien n'est implémenté). Constat : la page région devient trop lourde quand le GLB atteint plusieurs Go ; Ankh Island (12 Mo) est léger, ses textures ne pèsent que 3,7 Mo, donc le besoin ne vient pas d'elle. Idée retenue :
   - Une **vue d'ensemble légère** (`X.overview.glb`), toujours affichée ; des **tuiles détaillées** chargées autour de l'avatar en promenade et déchargées au-delà.
   - Liste des tuiles dans `X.tiles.json`, relue à chaque F5 (comme les zones). Activé par un champ `tiles` dans `X.config.json` ; absent = mode actuel (un seul `X.glb`), aucune région existante ne change.
   - Découpage **par objet racine** : chaque objet entier dans une seule tuile. Le terrain et la mer sont répartis **par triangle**, sans en couper. Chargement selon la distance à la **boîte réelle du contenu de la tuile** (pas à sa case de grille).
   - Points ouverts : (a) bibliothèque commune pour les meshes réutilisés entre tuiles (un GLB ne peut pas en référencer un autre : sans elle, un mesh répété est dupliqué dans chaque tuile) ; (b) grille de collision par tuile (chargée et libérée avec elle) ; (c) format de référence des zones liées (aujourd'hui `nom#index` calculé sur tout le modèle : à redéfinir quand le modèle est réparti).
   - Outil : `tools/glb2tiles.py` **fait en v28** (`--analyse` et découpage en tuiles autonomes, voir « Décisions de la v28 »). Le format de `X.tiles.json` est celui du `MODE_EMPLOI.md` § 17 (clés en anglais comme les autres JSON du projet). Les points ouverts (a) bibliothèque commune : écartée, tuiles autonomes ; (b) et (c) restent ouverts.
   - **Hors lot, à faire ensuite** : découpage **par triangles** d'un mesh unique plus grand qu'une cellule (terrain, mer) ; vue d'ensemble `X.overview.glb` obtenue en simplifiant chaque mesh **unique** une seule fois (pas par instance) ; compression meshopt des tuiles ; **chargement des tuiles dans la coquille** (rayon autour de l'avatar, déchargement, grille de collision par tuile, format de référence des zones liées, dont l'identifiant `nom#index` calculé aujourd'hui sur tout le modèle).

## Tests
- `python build.py` puis `python tests/portail_interne.py` (portail vers une arrivée de la même région), `python tests/v23.py` (clic simple, liaison nom#index, rotation de la région, page générée = viewer), `python tests/modulaire.py` (mode modulaire universel : coquille identique, copie renommée, rechargement des zones, zones liées à un élément, coquille unique `?region=` avec paramètres refusés, exports du viewer), `python tests/v27.py` (pile nom / bulle / losange des avatars, faux WebSocket), `python tests/oar2glb.py` (hors navigateur ; vérifie aussi `dist/oar2glb.py` et la version), `python tests/glb2tiles.py` (hors navigateur ; GLB synthétiques, vérifie aussi `dist/glb2tiles.py`) et `python tests/smoke.py` : génère des pages (GLB brut, Draco, Meshopt) avec `--register` et `--map-page`, les ouvre dans Chromium sans tête, vérifie l'absence d'erreur JavaScript et la disparition du message « Chargement… ». Variables : `THREE_DIR` (paquet npm three, hors ligne), `CHROMIUM` (exécutable).
- Chromium sans tête : options `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`. Le viewer expose `window.__viewer` (réglages, caméra) pour les tests.
- Pour tester les compteurs de visiteurs : lancer `presence_server.py --host 127.0.0.1 --port N` et ouvrir des connexions WebSocket `{"t":"hello","room":...,"name":...,"uid":...}`.
- Le chemin de téléchargement de `build.py` (jsDelivr) reprend celui de `glb2html.py` ; il n'a pas pu être exercé dans l'environnement de conception (réseau limité) : utiliser `--vendor` en cas de doute.

## Livraison d'une version
À chaque nouvelle version :
1. Mettre à jour `VERSION` (format `vNN (jj/mm/aaaa)`).
2. Mettre à jour `CHANGELOG.md` (nouvelle section en tête, date jj/mm/aaaa).
3. Mettre à jour `HISTORIQUE.md` : une ligne de plus dans le tableau, avec la date jj/mm/aaaa, l'étiquette (`vNN`) et le contenu.
4. Fabriquer (`python build.py`) et lancer les tests avant de livrer.
5. Indiquer à JJ la commande pour poser l'étiquette Git, en PowerShell sur une seule ligne, par exemple : `git tag v20 <commit>; git push origin v20`.
