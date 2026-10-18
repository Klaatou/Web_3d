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
- `src/gen_tpl.py` : script de génération (devient `dist/glb2html.py`). Points d'entrée : `build_html` (cfg + page), `generate`, `main` (arguments ; `--settings` relit le fichier en deux passes d'argparse), `clean_map` / `clean_zones` (assainissement), `register_region`, `write_map_page` (+ `MAP_PAGE_TEMPLATE`), `settings_defaults`.
- `src/presence_server.py` : serveur WebSocket (bibliothèque `websockets`).
- `build.py` : assemble le tout dans `dist/`. **Ne jamais éditer `dist/`** : modifier `src/` puis `python build.py`.
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

## Feuille de route (priorité décroissante)
1. **Mode modulaire** (`--modular`, `--config-only`). Conception retenue :
   - Sorties : `<page>.html` (coquille, ~100 Ko), `<page>.glb` (octets bruts, non encodés), `<page>.config.json` (= le dict `cfg`, zones et carte comprises), et `lib/three-0.160.0/` partagé par toutes les pages du dossier (modules transformés comme dans `jsurl` de build.py, + `draco/draco_wasm_wrapper.js` et `draco_decoder.wasm` si besoin).
   - Coquille obtenue à partir de `template.html` par remplacements exacts (vérifier que chacun trouve sa cible) : (1) supprimer `<script type="application/octet-stream" id="glb">__GLB_B64__</script>` ; (2) remplacer `const C = JSON.parse(document.getElementById('cfg').textContent);` par un chargement `fetch(BOOT.config, {cache:'no-store'})` (`BOOT` = JSON inline `{"config":"x.config.json","glb":"x.glb"}`), avec un message clair si la page est ouverte depuis le disque ; (3) remplacer `await viewer.loadBuffer(await b64ToBuffer(...))` par un `fetch(BOOT.glb)` en ArrayBuffer ; (4) importmap vers `./lib/three-0.160.0/<fichier>` ; (5) extrait Draco : `setDecoderPath('./lib/three-0.160.0/draco/')`.
   - `--config-only -o page.html` : réécrit seulement `x.config.json` (et la carte si `--register`), sans toucher au GLB ni à la coquille. Changer un paramètre = relancer cette commande, les visiteurs rechargent.
   - Nécessite http(s) (le mode autonome reste le défaut). `build_html` doit accepter `glb=None` pour la config seule.
   - Tests : servir le dossier avec `python -m http.server`, vérifier le chargement (`#msg` supprimé), modifier `config.json` puis recharger, comparer `cfg` avec celui du mode autonome.
   - Viewer : la commande générée doit pouvoir ajouter `--modular` ; étudier un export modulaire depuis le viewer.
2. **`presence_server.py` comme hébergeur de la carte et des pages.** Avec `websockets` ≥ 13 (`websockets.asyncio.server.serve(..., process_request=...)`), répondre en HTTP aux requêtes non WebSocket :
   - `--serve-dir DOSSIER` : fichiers statiques (pages, glb, config, lib, vignettes), protection contre `..`, types MIME, `Cache-Control: no-store` pour les `.json`, `Access-Control-Allow-Origin: *` pour `GET /regions.json`. TLS déjà géré (`--cert/--key`) : tout sur un seul port.
   - Registre de carte : `GET /regions.json` ; fichier `presence_regions.json` (relatif au script) ; enregistrement authentifié par une clé propre à chaque propriétaire (`--keys`, valeurs hachées) ; `glb2html.py --publish ws://… --key …` pousse la fiche après génération.
   - Pairs : `--peer https://autre/regions.json` relus périodiquement et fusionnés en lecture seule.
   - Bornes : vignette ≤ 140 Ko, nombre de régions limité, journal des enregistrements.
3. Autres idées citées : état réel des objets Home Assistant visible en 3D ; couche de décor (objets GLB ajoutés sans régénérer) ; avatars VRM (three-vrm, distribués par le serveur de présence) ; chat : filtre de mots et commande `/mute`.

## Tests
- `python build.py` puis `python tests/smoke.py` : génère des pages (GLB brut, Draco, Meshopt) avec `--register` et `--map-page`, les ouvre dans Chromium sans tête, vérifie l'absence d'erreur JavaScript et la disparition du message « Chargement… ». Variables : `THREE_DIR` (paquet npm three, hors ligne), `CHROMIUM` (exécutable).
- Chromium sans tête : options `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`. Le viewer expose `window.__viewer` (réglages, caméra) pour les tests.
- Pour tester les compteurs de visiteurs : lancer `presence_server.py --host 127.0.0.1 --port N` et ouvrir des connexions WebSocket `{"t":"hello","room":...,"name":...,"uid":...}`.
- Le chemin de téléchargement de `build.py` (jsDelivr) reprend celui de `glb2html.py` ; il n'a pas pu être exercé dans l'environnement de conception (réseau limité) : utiliser `--vendor` en cas de doute.
