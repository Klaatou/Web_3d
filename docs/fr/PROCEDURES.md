# Que faire pour… (procédures pas à pas)

*Écrit le 23/10/2026, revu le 29/10/2026 pour la version 1.0.0 (les « vNN » du texte sont les versions d'avant la 1.0.0 : la v52 est devenue la 1.0.0). Les commandes sont en PowerShell, sur une seule ligne, avec les chemins de ta machine. La liste complète des options est dans `REFERENCE_OPTIONS.md` ; le détail des zones, touches et réglages est dans `MANUEL.md`.*

**Ce qui a été essayé ici :** les commandes de `glb2html`, `glb2tiles` (y compris `--update`, `--register`, `--map-page`) sur des régions de test, un seul GLB et en tuiles. **Ce qui ne l'a pas été :** la conversion d'un OAR par convoar (convoar n'est pas disponible dans le bac à sable), et les commandes PowerShell elles-mêmes (essayées sous Linux avec des chemins équivalents).

**Les trois dossiers de référence**

| Rôle | Chemin |
|---|---|
| Outils (fabriqués par `python build.py`) | `P:\_OpenSim\SL&OS\Web_3d\web_3d\dist` |
| OAR et GLB source | `J:\Download\Com\Chat\_Monde virtuel en ligne_\_OpenSim_\_Contenu_\OAR` |
| Régions publiées en tuiles | `P:\_OpenSim\SL&OS\Web_3d\tuiles` |

**Règle d'or :** lance toujours les outils depuis le dossier des outils (`cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"`). Donne des **chemins complets** pour tout fichier écrit, sauf avec `--update` (les chemins relatifs y sont relatifs au dossier de la page).

---

## 1. D'un OAR à une page web, région légère (un seul GLB)

À choisir quand `glb2tiles --analyse` ne recommande pas de découpage (en gros : GLB sous 150 Mo et sous 3 millions de triangles).

1. **Convertir l'OAR.** Le GLB est écrit à côté de l'OAR (`MaRegion.oar` donne `MaRegion.glb`). Le terrain complet est ajouté automatiquement si celui de convoar est incomplet.
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python oar2glb.py "J:\Download\Com\Chat\_Monde virtuel en ligne_\_OpenSim_\_Contenu_\OAR\MaRegion.oar"`
2. **Vérifier si un découpage serait nécessaire** (lecture seule, n'écrit rien) :
   `python glb2tiles.py "J:\Download\Com\Chat\_Monde virtuel en ligne_\_OpenSim_\_Contenu_\OAR\MaRegion.glb" --analyse`
3. **Fabriquer la page** dans un dossier de publication (par exemple `P:\_OpenSim\SL&OS\Web_3d\sites\MaRegion`, à créer) :
   `python glb2html.py "J:\Download\Com\Chat\_Monde virtuel en ligne_\_OpenSim_\_Contenu_\OAR\MaRegion.glb" --shared-shell -o "P:\_OpenSim\SL&OS\Web_3d\sites\MaRegion\MaRegion.html" --sea-y 18.5 --presence-url "ws://ADRESSE:8765" --chat`
   Sont écrits : `MaRegion.glb`, `MaRegion.config.json`, `MaRegion.zones.json`, `index.html` et `lib\`.
4. **Servir et ouvrir.** La page doit passer par un serveur web, pas par un double-clic.
   `cd "P:\_OpenSim\SL&OS\Web_3d\sites\MaRegion"; python -m http.server 8000`
   Puis `http://localhost:8000/index.html?region=MaRegion`.
5. **Poser les zones** (portails, arrivées, panneaux) dans `glb-viewer.html` : voir `MANUEL.md` §§ 3 à 12. En fin de travail, le viewer exporte `MaRegion.zones.json` : copie-le dans le dossier de la page, puis F5.

## 2. D'un OAR à une page web, région lourde (tuiles)

Cas de la 4X4 : un GLB de 1,2 Go ne tient pas d'un bloc dans le navigateur. Les tuiles chargent autour de l'avatar et déchargent le reste ; la vue d'ensemble montre toute la région de loin.

1. **Convertir l'OAR** comme au 1.1. Ça peut durer plusieurs heures et plusieurs dizaines de Go de mémoire (4 h 20 et 45 Go pour la 4X4). Si convoar plante dans la lecture des textures JPEG 2000, relance avec `--reencode` (voir `MANUEL.md` § 15 : à n'utiliser qu'en dernier recours).
2. **Analyser** (lecture seule) :
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python glb2tiles.py "J:\...\OAR\X.glb" --analyse`
3. **Découper.** `--output` désigne le dossier où sont écrits `X.tiles\`, `X.tiles.json` et `X.overview.glb`. `--exclude` retire du découpage les objets dont le nom correspond (garde-fous : 24 triangles et 1 mesh au plus), par exemple les boîtes de livraison des catalogues.
   `python glb2tiles.py "J:\...\OAR\X.glb" --output "P:\_OpenSim\SL&OS\Web_3d\tuiles" --exclude "RAKis Freebies"`
4. **Fabriquer la page.** Remplace `ADRESSE` par ton adresse publique et `--target` par un endroit dégagé (coordonnées relevées dans le viewer), ou pose une arrivée nommée `default` et retire `--target`.
   `python glb2html.py --shared-shell -o "P:\_OpenSim\SL&OS\Web_3d\tuiles\X.html" --tiles "P:\_OpenSim\SL&OS\Web_3d\tuiles\X.tiles.json" --sea-y 18.5 --presence-url "ws://ADRESSE:8765" --chat --target 392,68,-373`
5. **Servir et ouvrir** :
   `cd "P:\_OpenSim\SL&OS\Web_3d\tuiles"; python -m http.server 8000`
   Puis `http://localhost:8000/index.html?region=X`.
6. **Poser les zones.** Ouvre `glb-viewer.html`, bouton « Ouvrir une région en tuiles (dossier) », choisis le dossier `tuiles`. Pose tes zones, puis « Enregistrer les zones dans le dossier de la région » (Edge ou Chrome ; sinon l'export est un téléchargement à copier dans le dossier sous le nom `X.zones.json`). F5 sur la page : les zones sont prises en compte, sans régénération.

Pour lier une zone à un objet de la région en tuiles, les tuiles doivent avoir été découpées avec `glb2tiles` v32 ou plus (sinon, redécouper).

## 3. Changer un réglage d'une région déjà publiée (mer, point de départ, présence…)

**Une valeur : modifier le fichier de config et recharger.** La page relit `X.config.json` à chaque ouverture, sans cache.
`notepad "P:\_OpenSim\SL&OS\Web_3d\tuiles\X.config.json"`
Clés utiles : `seaY` (hauteur de la mer, en m), `target` (`[x, y, z]`), `presenceUrl`, `chat` (`true` ou `false`), `zoneInfoDist`, `tileRadius`, `tileMaxMB`, `tileMaxTriangles`. Le JSON est strict : garde les virgules et les guillemets. **Les couleurs y sont des nombres décimaux** (`seaColor` 3840729 vaut `3a9ad9`) : pour les changer, passe plutôt par `--update`.

**Plusieurs valeurs, ou une couleur : `--update`.** Il applique seulement les options que tu écris, garde tout le reste de la config et le fichier de zones.
`cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python glb2html.py --update --shared-shell -o "P:\_OpenSim\SL&OS\Web_3d\tuiles\X.html" --sea-y 10`

**Ne relance jamais la commande complète de fabrication (procédure 2.4) pour changer un détail** : elle réécrit toute la config à partir des seules options de la ligne, et efface ce que tu avais réglé à la main.

## 4. Après une nouvelle version des outils

1. **Appliquer le patch et fabriquer** (la conversation donne les lignes exactes, chacune sur une ligne) :
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d"; git pull; python .\patch_NOM.py; if ($LASTEXITCODE -eq 0) { python build.py }`
   puis la ligne `git add …; git commit …; git push` livrée avec le patch, et, seulement quand tu décides une publication, `git tag v1.0.0; git push origin v1.0.0` (le numéro est celui de `VERSION`).
2. **Copier la coquille et la carte** à la racine du site (organisation `Sites\`, `MANUEL.md` § 29.8) ; la ligne `const LIB` de la coquille reste `./lib` :
   `Copy-Item "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\index.html" "P:\_OpenSim\SL&OS\Web_3d\Sites\index.html"; Copy-Item "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\carte.html" "P:\_OpenSim\SL&OS\Web_3d\Sites\carte.html"`
3. **Mettre à jour chaque région** avec `--update` (la config et les zones sont gardées). Donner le chemin de la coquille de la racine, sinon une coquille et un `lib` inutiles sont écrits dans le dossier de la région :
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --update -o "P:\_OpenSim\SL&OS\Web_3d\Sites\houses\NOM.html" --shared-shell "P:\_OpenSim\SL&OS\Web_3d\Sites\index.html"`
   Région seule dans son dossier (coquille à côté d'elle) : `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --update --shared-shell -o "P:\dossier\X.html"`. La coquille `index.html` est renouvelée si elle est plus ancienne (l'ancienne est gardée sous un nom daté).
4. Recharger la page avec Ctrl+F5. La ligne du bas du panneau d'aide donne la version affichée (par exemple « glb2html 1.0.0 (29/10/2026) ») : si elle est ancienne, la mise à jour n'a pas eu lieu.
5. **Relancer le serveur de présence** depuis `dist\` (procédure 6) après chaque nouvelle version : un ancien exemplaire continue de marcher mais n'a pas les nouveautés (v47 : compteurs de la carte ; v48 : journal des visites).
6. Le découpage en tuiles n'est à refaire que si la conversation le dit, par exemple pour de nouvelles informations dans les tuiles.

## 5. Poser et modifier des zones

| Besoin | Où |
|---|---|
| Poser portail, arrivée, panneau, lien | viewer, `MANUEL.md` §§ 3 à 8 |
| Arrivée utilisée à l'ouverture sans lien | une arrivée nommée `default` (§ 4) ; `--target` explicite garde le cadrage |
| Portail vers une autre région | `MANUEL.md` § 6 |
| Zone liée à un objet du modèle | `MANUEL.md` § 9 (en tuiles : § 17 ter) |
| Zone privée (visible seulement avec le profil « private ») | `MANUEL.md` § 10 |

Les zones d'une région en tuiles s'écrivent dans le repère d'origine du modèle (aucun recentrage). Le viewer en mode tuiles produit ces coordonnées directement ; ne reporte pas à la main des coordonnées d'un autre GLB.

## 6. Serveur de présence (positions, chat, modération)

1. **Installer** une fois : `pip install websockets`
2. **Lancer** (le journal relatif est écrit dans le dossier du script ; `--log-ip raw` écrit les adresses IP en clair, `--log-days` limite la conservation, **`--log-days 0` conserve les journaux sans limite**) :
   `python ".\presence_server.py" --log presence.log --log-ip raw --log-days 0`
   Historique du chat (v37) : 200 derniers messages rejoués aux nouveaux arrivants (`--history`) ; `--history-file chat.jsonl` le garde entre deux relances (messages = données personnelles, jamais d'adresse IP dans ce fichier), `--history-days N` (30 ; 0 = tout conserver) limite la relecture au démarrage.
3. **Ouvrir le port** (8765 par défaut, `--port` pour en changer) dans la box, vers la machine qui fait tourner le serveur.
4. **Brancher la page** : `--presence-url "ws://ADRESSE:8765"` à la fabrication, ou la clé `presenceUrl` de `X.config.json`. Si la page est en https, l'adresse doit être en `wss://` (voir `--cert` et `--key`, ou un reverse proxy avec `--proxy-header`). Si tes pages sont ouvertes par plusieurs adresses (`localhost`, réseau, nom public), mets `ws://*:8765` : l'étoile prend le nom par lequel la page a été ouverte (manuel § 34.10).
5. **Modérer** dans la console du serveur : `liste` (visiteurs), `ejecter <n°|nom> [raison]`, `bannir <n°|nom> [minutes] [raison]` (0 = définitif), `bans`, `debannir <n° de bans>`, `pseudos` (liste les pseudos réservés), `oublier <pseudo>` (libère un pseudo réservé), `aide`. Un bannissement vise la clé du visiteur (si elle n'est pas anonyme) et son adresse IP : l'IPv4 exacte, l'IPv6 par préfixe `/64` (jamais une plage plus large).
6. **Journal des visites** (v48) : ajoute `--visits visits.jsonl` à la ligne de lancement ; dans la console, `rooms` liste les salons connus (casse exacte) et `visits-key ROOM` donne la clé d'un salon (affichée une seule fois). Envoie au créateur l'adresse de sa page suivie de `#visits` et la clé (manuel § 31).
7. **Accueillir un créateur** (v51, manuel § 34) : ajoute `--creators presence_creators.json` à la ligne de lancement ; dans ce fichier (copie de `docs\samples\presence_creators.sample.json`), garde une entrée pour toi (`"prefix": ""`, tes origines et `null`) et ajoute la sienne (`id`, origines de ses pages). Le créateur met `room` à `ID.NAME` (par exemple `alice.galerie`) et ton adresse `wss://` dans `presenceUrl` de sa config. Vérifie avec `creators` dans la console ; clé de ses visites : `visits-key alice.galerie` ; fiche sur ta carte : `--register` sans glb (manuel § 27.6).
8. **Mettre à jour** : arrête le serveur (Ctrl+C) et relance-le depuis le `presence_server.py` du dossier `dist` après `python build.py`. Un ancien exemplaire ignore les nouveautés (par exemple la couleur choisie).
9. **Serveur permanent sur une VM** : un service systemd seul ne donne pas de clavier à la console de modération ; la façon qui a marché (une session `tmux` lancée par systemd) est décrite au § 11, « VM Debian 13 : service permanent avec console de modération ».

Les adresses IP et les messages du chat sont des données personnelles : informe tes visiteurs et limite la durée de conservation. Le journal des visites ne contient jamais d'adresse IP.

## 7. Carte des mondes

Avec l'organisation `Sites\` (une coquille à la racine, un dossier par région, `MANUEL.md` § 29.8) :

1. **Mettre à jour `regions.json` depuis le dossier** (v49) :
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --scan-sites "P:\_OpenSim\SL&OS\Web_3d\Sites" --dry-run`
   puis la même ligne sans `--dry-run`. Une fiche par région trouvée, avec sa vignette `NOM.jpg` à côté de `NOM.config.json` (carré de 320 pixels conseillé) ; les noms, places et arrivées déjà notés sont gardés ; rien n'est supprimé (`MANUEL.md` § 32).
2. **Nommer et placer les régions** une fois : `name`, `x`, `y` et `spawn` dans `Sites\regions.json`, à la main ou avec le viewer (« Importer regions.json », modifier, « Exporter regions.json » : l'en-tête et tous les champs sont gardés depuis la v50). Les parcours suivants les gardent.
3. **Afficher la carte** : `carte.html` (copiée à la racine, procédure 4) relit `regions.json` à chaque ouverture, rien à régénérer (`MANUEL.md` § 30.4). L'ouvrir par le serveur web, par exemple `http://localhost:8000/carte.html` après `cd "P:\_OpenSim\SL&OS\Web_3d\Sites"; python -m http.server 8000`. Un champ « Mon pseudo » en haut ajoute `name=` aux liens des régions.

Sans dossier de site : `--register regions.json` ajoute la région à chaque génération (`--region-name`, `--region-xy x,y`), et `--map-page carte.html` écrit une page autonome qui contient la liste (`MANUEL.md` § 30.4).

Avec une seule région, la carte n'apporte rien : elle sert à relier plusieurs régions entre elles.

## 8. Quand relancer quoi

| Ce qui a changé | À faire | Page à recharger |
|---|---|---|
| Une valeur de réglage (mer, cible, présence) | modifier `X.config.json`, ou `--update` avec l'option | F5 |
| Les zones | enregistrer `X.zones.json` dans le dossier de la région | F5 |
| Nouvelle version des outils | procédure 4 (`--update`) | Ctrl+F5 |
| Nouvelle version du serveur de présence (v48 : journal des visites ; v47 : compteurs de la carte ; v37 : historique du chat) | arrêter et relancer `presence_server.py` | F5 |
| L'OAR a changé | reconvertir (1.1 ou 2.1), redécouper (2.3), puis `--update` | Ctrl+F5 |
| Les objets exclus du découpage | redécouper (2.3) avec un autre `--exclude` | Ctrl+F5 |
| Rotation de la région (`--rotate`) | `--update --rotate 180`, puis refaire la vignette de la carte | Ctrl+F5 |
| Première mise en ligne d'une région | procédure 1 ou 2 (commande complète) | — |

## 9. Quand ça ne marche pas

| Symptôme | Cause probable | À faire |
|---|---|---|
| Page noire avec `#spawn=…` | la tuile de l'arrivée se charge | depuis la v33, un texte « Chargement du sol… » doit s'afficher ; sinon, console (F12) et lignes `[tuile] …` |
| « Chargement du sol… » qui dure | grosse tuile | patienter ; relever les lignes `[tuile] …` de la console |
| Les zones n'apparaissent pas | fichier de zones ailleurs que dans le dossier de la page, zone privée, marqueur discret | vérifier `X.zones.json` dans le dossier servi, F5 en fenêtre privée, `--zone-marker range` |
| Les réglages ne changent pas | coquille ancienne, cache | `--update`, puis Ctrl+F5 |
| Erreurs « Couldn't load texture » | images de 0 octet dans des tuiles d'avant la v31 | redécouper avec glb2tiles v31 ou plus |
| Pas de chat | page fabriquée sans `--presence-url` ou sans `--chat` | ajouter les options avec `--update`, relancer le serveur |
| La couleur d'avatar ne change pas | serveur de présence ancien | relancer le `presence_server.py` du dossier `dist` |
| Copier le texte de l'aide | — | sélectionner à la souris, Ctrl+C ; sinon, dans la console : `copy(document.body.innerText)` |

Pour tout rapport de bug, colle le texte du panneau d'état et d'aide, et les messages de la console (en ignorant ceux de LastPass).

## 10. Touches utiles et langue

| Besoin | Geste |
|---|---|
| Entrer en promenade / en sortir | **F** ou **P** (dans le viewer, P pose une zone : sortir par **F** ou **Maj+P**) |
| Déclencher une zone proche | clic sur elle, ou **E** (portail « en marchant dedans » : à l'entrée de son rayon) |
| Voler | **Début**, le bouton de vol, ou **Page Haut** maintenu plus de 0,4 s ; monter : **Page Haut** ou **Espace** maintenu ; descendre : **Page Bas** ou **C** ; sauter : **Espace** ou appui bref sur **Page Haut** |
| Afficher les repères de portail | **T** (retirés de la fabrication avec `--no-zone-cone`) |
| Clavier AZERTY ou QWERTY | réglage « Clavier » de la page (Auto par défaut) : les touches physiques ne changent pas, l'aide affiche les lettres de ta disposition |
| Langue de la page | réglage « Langue / Language » (Auto, français, English), ou `#lang=en` dans l'adresse |
| Langue des outils | `--lang fr` ou `--lang en` sur chaque outil, ou la variable d'environnement `WEB3D_LANG` ; sans rien, la langue du système. PowerShell, une session : `$env:WEB3D_LANG = "fr"` |
| Copier ma position | bouton « Copier ma position » (liste URL / xyz) ; « Aller à » accepte l'URL `#pos=…` et `x, y, z` |
| Ouvrir / fermer les Réglages | touche **O** (bascule, comme **H** et **I**) |
| Souris en promenade | **G** bascule la capture (capture si elle est libre, la libère si elle est capturée) ; le bouton « Capturer la souris » ne fait que capturer ; **Échap** la libère ; un clic ne la capture jamais |
| Changer de vue | **V** : subjective, troisième personne, caméra libre ; **M** : subjective / troisième personne en promenade, carte des mondes hors promenade (**Ctrl+M** : carte partout) |
| Revenir au point d'arrivée | **R** |
| Boussole (cap en haut de la page) | case « Boussole » des Réglages ; `--no-compass` pour la retirer de la fabrication, `--north DEGRES` pour un GLB qui ne vient pas d'OpenSim |
| Régler la largeur de l'aide et des informations | tirer leur bord droit (260 px à 70 % de la fenêtre), mémorisé |
| Chat : messages plus anciens, non lus, citations | bouton « Messages plus anciens » (chat ouvert), titre de l'onglet « (3) Région », « N messages vous citent » ; réglage « Messages d'historique affichés » |
| Région par défaut (adresse sans `?region=`) | `default.json` écrit à la première région d'un dossier, `--default` pour en changer ; sinon la première entrée relative de `regions.json` |
| Mettre `lib/` ailleurs | `--lib-url ../lib` (ou une adresse `https://…/lib`) à la fabrication de la coquille, ou modifier à la main la ligne `const LIB = './lib';` au début de `index.html` ; `--update` la garde |
| Région dans un sous-dossier | `glb2html.py X.glb --shared-shell "P:\site\index.html" -o "P:\site\sous\dossier\X.html"` ; adresse `index.html?region=sous/dossier/X` |
| Flèches à l'écran (v46) | **K**, bouton « Flèches (K) » ou case « Flèches à l'écran (K) » des Réglages ; appui maintenu = touche tenue |
| Téléphone, tablette (v46) | mode tactile automatique (réglage « Commandes tactiles ») : colonne de boutons, « Menu », glisser du doigt pour regarder, appui long = bulle |
| Paramètres de l'adresse | séparés par `&` ; `#` est aussi accepté (`#name=Klaatou&lang=en` = `#name=Klaatou#lang=en`) |

Détail : `MANUEL.md` §§ 2, 21 et 22.

---

## 11. Rendre le serveur de présence public sans montrer son adresse IP

*Rédigé le 24/10/2026, complété le 29/10/2026. **Essayé le 24/10/2026** : Tailscale Funnel (voie A), avec une page servie en `http` et un visiteur extérieur au réseau. **Essayé le 29/10/2026** : la voie A sur une VM Debian 13, avec une page publiée sur GitHub Pages (https), un visiteur extérieur, le redémarrage de la VM et celui du service (voir « VM Debian 13 : service permanent avec console de modération »). **Non essayé** : Caddy (voie B), Cloudflare Tunnel (voie C), la voie D avec Apache sous Tailscale (Apache, service et lignes de configuration essayés dans le bac à sable de conception, mais pas Tailscale) et les commandes du cas « un autre service est déjà publié ». Vérifie toujours le résultat avec le contrôle de l'étape finale (« Contrôler l'adresse vue par le serveur »).*

**Principe.** Un navigateur refuse une connexion `ws://` depuis une page en https : une page https demande donc une adresse de présence en `wss://NOM`. Le visiteur ne se connecte qu'à ce `NOM`, jamais à ton IP. Un relais reçoit le `wss://` et le transmet en `ws://` à `presence_server.py`, qui n'écoute alors que sur `127.0.0.1` (donc sans `--cert` ni `--key`). Choisis **une** des quatre voies.

**Règle apprise le 24/10/2026 : la présence doit être au même endroit que la page** : même nom, ou page en https publiée elle aussi par Funnel. Sur un appareil où Tailscale est actif, le navigateur bloque la connexion de présence quand la page vient d'une autre adresse (le nom `.ts.net` y donne une adresse privée en 100.x) ; avec Tailscale coupé sur le téléphone, la même page se connecte.

### Voie A : chez toi, Tailscale Funnel (aucun port à ouvrir dans la box)
1. Installe Tailscale sur la machine qui fait tourner le serveur et connecte-la à ton compte. Dans la console d'administration Tailscale, active **HTTPS** (DNS) et autorise **Funnel** pour cette machine (voir la documentation « Tailscale Funnel »).
2. Avant de publier, regarde ce qui l'est déjà : `tailscale serve status` et `tailscale funnel status`. **`tailscale funnel` prend la racine du port et remplace ce que `tailscale serve` y publiait** (constaté : le service qui y était a été écrasé). Si un service est déjà publié, passe au cas « un autre service est déjà publié » plus bas. N'utilise `tailscale funnel reset` que pour tout effacer.
3. Lance le serveur sur l'adresse locale seulement (PowerShell, une ligne) : `python ".\presence_server.py" --host 127.0.0.1 --port 8765 --proxy-header X-Forwarded-For --origins "https://TONSITE" --log presence.log --log-ip raw --log-days 0 --history-file chat.jsonl --history-days 0`
4. Expose-le : `tailscale funnel --bg 8765`. L'adresse publique est `https://MACHINE.TAILNET.ts.net` ; l'adresse de présence est donc `wss://MACHINE.TAILNET.ts.net`.
5. Ton IP n'apparaît pas ; en revanche le nom de ta machine et celui de ton réseau Tailscale sont publics.

Résultats de l'essai du 24/10/2026 :
- le WebSocket traverse Funnel (réponse 101) ;
- avec `--proxy-header X-Forwarded-For`, le journal montre la vraie IP du visiteur ;
- un visiteur extérieur au réseau s'est promené par Funnel ;
- sur les appareils où Tailscale est actif, la connexion est bloquée si la page vient d'une autre adresse (voir la règle plus haut) ;
- un détour par le fichier `hosts` de la machine n'a pas marché.

### Voie B : petit VPS, Caddy (certificat https automatique)
Il faut un nom de domaine dont un enregistrement `A` pointe vers le VPS, et l'accès root **une seule fois**, pour l'installation (ouvrir les ports 80 et 443 uniquement).
1. Installe Python, `pip install websockets` et Caddy.
2. Fichier `Caddyfile` : un bloc `presence.TONDOMAINE.tld { reverse_proxy 127.0.0.1:8765 }`. Caddy gère les WebSocket et envoie l'adresse du visiteur dans `X-Forwarded-For`.
3. Lance le serveur : `python3 presence_server.py --host 127.0.0.1 --port 8765 --proxy-header X-Forwarded-For --origins "https://TONSITE" --log presence.log --history-file chat.jsonl`
4. Adresse de présence : `wss://presence.TONDOMAINE.tld`. Ici l'IP du VPS est publique dans le DNS ; c'est la voie C qui la cache.

### Voie C : Cloudflare Tunnel (IP cachée, aucun port ouvert, chez toi ou sur un VPS)
Il faut un nom de domaine géré par Cloudflare (compte gratuit).
1. Installe `cloudflared`, puis `cloudflared tunnel login` et `cloudflared tunnel create presence`.
2. Dans le fichier de configuration du tunnel, route `presence.TONDOMAINE.tld` vers `http://127.0.0.1:8765` (`cloudflared tunnel route dns presence presence.TONDOMAINE.tld`, puis `cloudflared tunnel run presence`).
3. Lance le serveur : `python3 presence_server.py --host 127.0.0.1 --port 8765 --proxy-header CF-Connecting-IP --origins "https://TONSITE"`
4. Adresse de présence : `wss://presence.TONDOMAINE.tld`.

### Voie D : VM Linux, Tailscale Funnel et Apache (page et présence sous le même nom)
Pour une page servie par Apache sur une VM Linux. Un seul nom public (`https://MACHINE.TAILNET.ts.net`) sert la page à la racine et la présence sous `/presence` : la page et la présence sont au même endroit. Apache et la présence n'écoutent que sur `127.0.0.1` ; aucun port n'est ouvert dans la box.
1. **Tailscale dans la VM** : installe-le, connecte la VM, active **HTTPS** et autorise **Funnel** (comme à l'étape 1 de la voie A).
2. **Apache sur `127.0.0.1` seulement** (Debian ou Ubuntu ; essayé avec Apache 2.4.58 sous Ubuntu 24.04). Dans `/etc/apache2/ports.conf`, remplace `Listen 80` par `Listen 127.0.0.1:80`. Fichier `/etc/apache2/sites-available/web3d.conf` :

```
<VirtualHost 127.0.0.1:80>
    DocumentRoot /var/www/web3d
    <Directory /var/www/web3d>
        Require all granted
    </Directory>
    RemoteIPHeader X-Forwarded-For
    RemoteIPInternalProxy 127.0.0.1
    ErrorLog ${APACHE_LOG_DIR}/web3d-error.log
    CustomLog ${APACHE_LOG_DIR}/web3d-access.log combined
</VirtualHost>
```

   Puis `a2enmod remoteip`, `a2dissite 000-default`, `a2ensite web3d`, `apache2ctl configtest` (message attendu : `Syntax OK`), et recharge Apache. Les deux lignes `RemoteIP` font écrire dans le journal d'Apache l'IP du visiteur au lieu de `127.0.0.1` (essayé ici avec un en-tête simulé ; derrière Funnel : à contrôler). Les fichiers de la page vont dans `/var/www/web3d`.
3. **Présence en service système.** Compte et environnement Python (essayés) : `useradd --system --home /opt/web3d --shell /usr/sbin/nologin web3d`, puis `mkdir -p /opt/web3d`, `python3 -m venv /opt/web3d/venv` et `/opt/web3d/venv/bin/pip install websockets`. Copie `presence_server.py` (le fichier de `dist\`) dans `/opt/web3d/`. Fichier `/etc/systemd/system/web3d-presence.service` :

```
[Unit]
Description=Web 3d presence server
After=network-online.target
Wants=network-online.target

[Service]
User=web3d
StateDirectory=web3d
ExecStart=/opt/web3d/venv/bin/python /opt/web3d/presence_server.py --host 127.0.0.1 --port 8765 --proxy-header X-Forwarded-For --origins https://MACHINE.TAILNET.ts.net --log /var/lib/web3d/presence.log --log-ip raw --identities /var/lib/web3d/presence_identities.json --bans /var/lib/web3d/presence_bans.json --log-days 0 --history-file /var/lib/web3d/chat.jsonl --history-days 0
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

   Puis `systemctl daemon-reload` et `systemctl enable --now web3d-presence`. **Essayé ici** : le fichier passe `systemd-analyze verify` ; la ligne `ExecStart` lancée à la main par le compte `web3d` démarre, accepte l'origine donnée à `--origins`, refuse une autre origine (HTTP 403) et écrit dans le journal l'IP envoyée dans `X-Forwarded-For`. **Non essayé ici** : le démarrage par systemd lui-même (pas de systemd actif dans le bac à sable). Les fichiers du serveur sont dans `/var/lib/web3d/` : sans les options `--identities` et `--bans`, le serveur écrit à côté du script, dossier que le compte du service ne peut pas modifier (erreur de démarrage constatée).
4. **Funnel** (syntaxe de la documentation Tailscale ; non essayé ici, en root si nécessaire) : `tailscale funnel --bg --set-path=/presence http://127.0.0.1:8765` puis `tailscale funnel --bg http://127.0.0.1:80`. Le serveur de présence accepte n'importe quel chemin (essayé avec `/`, `/presence` et `/x/y`).
5. **Brancher la page** : `--presence-url "wss://MACHINE.TAILNET.ts.net/presence"` (section « Brancher les pages »). La page est à `https://MACHINE.TAILNET.ts.net/`.
6. **Vérifier** : `tailscale funnel status` liste les deux chemins ; ouvre la page depuis un téléphone où Tailscale est coupé ; lis `presence.log` (contrôle de l'étape finale) et le journal d'Apache.

### VM Debian 13 : service permanent avec console de modération (essayé le 29/10/2026)
Voie A sur une VM Debian 13 (VMware, réseau NAT), publication par Tailscale Funnel, page publiée sur GitHub Pages. Le service doit démarrer seul **et** garder la console de modération (commandes tapées), qu'un service systemd seul ne peut pas offrir faute de clavier.
1. **Installer** : `python3`, `python3-websockets` et `tmux` viennent d'`apt` (pas d'environnement virtuel) ; Tailscale (`tailscale up`) ; publication par `tailscale funnel --bg 8765`. L'origine de la page (`https://NOMDUSITE.github.io`) est déclarée dans le `presence_creators.json` de la VM (option `--creators`, sans `--origins`).
2. **Options du serveur** : `--host 127.0.0.1 --port 8765 --proxy-header X-Forwarded-For --log presence.log --log-ip raw --log-days 0 --history-file chat.jsonl --history-days 0 --visits visits.jsonl --creators presence_creators.json`. Choix de l'auteur : `--log-ip raw` et conservation sans limite (adresses IP et messages d'inconnus sont des données personnelles, voir « À garder en tête » ; défauts du serveur : `--log-ip hash` et 30 jours).
3. **Démarrage** : une unité systemd (`web3d-presence.service`, `Type=forking`, `Restart=always`, `RestartSec=5`) lance une session `tmux` nommée `presence` qui exécute un script `lance_presence.sh`. Ce script est une boucle qui relance `presence_server.py` 5 secondes après son arrêt. Le serveur garde ainsi sa console dans la session `tmux`.

`lance_presence.sh`, dans le dossier du serveur (ici `/home/UTILISATEUR/presence`, à côté de `presence_server.py`), rendu exécutable par `chmod +x lance_presence.sh` :

```bash
#!/bin/bash
# Lance le serveur de presence dans une boucle : s'il s'arrete, il repart apres 5 secondes.
# A ranger dans le dossier du serveur (a cote de presence_server.py), rendre executable : chmod +x lance_presence.sh
cd "$(dirname "$0")" || exit 1
while true; do
  python3 presence_server.py --host 127.0.0.1 --port 8765 --proxy-header X-Forwarded-For --log presence.log --log-ip raw --log-days 0 --history-file chat.jsonl --history-days 0 --visits visits.jsonl --creators presence_creators.json
  echo "Serveur arrete (code $?). Relance dans 5 secondes (pour l'arreter pour de bon : systemctl stop web3d-presence)."
  sleep 5
done
```

`/etc/systemd/system/web3d-presence.service` (remplace `UTILISATEUR` par l'utilisateur de la VM) :

```
[Unit]
Description=Web 3d presence server (console dans tmux)
After=network-online.target
Wants=network-online.target

[Service]
Type=forking
Restart=always
RestartSec=5
User=UTILISATEUR
WorkingDirectory=/home/UTILISATEUR/presence
ExecStart=/usr/bin/tmux new-session -d -s presence /home/UTILISATEUR/presence/lance_presence.sh
ExecStop=/usr/bin/tmux kill-session -t presence

[Install]
WantedBy=multi-user.target
```

Puis `systemctl daemon-reload` et `systemctl enable --now web3d-presence`. Ce sont les copies des deux fichiers de la VM de l'auteur.

4. **Console** : sous l'utilisateur de la VM (pas `root`), `tmux attach -t presence` ; depuis le PC, `ssh -t UTILISATEUR@ADRESSE_VM "tmux attach -t presence"` (le copier-coller marche) ; pour sortir sans arrêter le serveur : **Ctrl+B** puis **D** ; pour l'arrêter pour de bon : `systemctl stop web3d-presence` (`root`).
5. **Mettre à jour le serveur** après un `python build.py` qui change `presence_server.py` : envoyer le fichier de `dist\` par `scp`, puis `systemctl restart web3d-presence`. La VM a **sa propre copie** de `presence_creators.json` et de `presence_identities.json` (pseudos réservés).
6. **Essayé le 29/10/2026** : `reboot` (la session `presence` et la publication Funnel reviennent seules) ; `tmux kill-server` (le service revient en quelques secondes) ; un visiteur extérieur, depuis une page de GitHub Pages.
7. **Pièges de Debian 13** :
   - le paquet `python` n'existe plus : `python3` ;
   - la ligne `cdrom` de `/etc/apt/sources.list` fait échouer `apt-get update` (la retirer avec `sed`) et **bloque** `apt-get update && apt-get install` : ne pas les enchaîner ;
   - `su` sans le tiret ne met pas `/usr/sbin` dans le chemin (`usermod` introuvable) : utiliser `su -` ;
   - `sudo` n'est pas installé par défaut ;
   - un fichier de service **collé** dans la console de la VM a été mal recopié (pas de presse-papiers sans les extensions VMware) : l'envoyer par `scp` est fiable.
8. **Constaté deux fois (29/10/2026 et 30/10/2026), cause non établie** : l'écran de la console de la VM (VMware Workstation) devient noir ; le `ssh` répond et le serveur de présence tourne, donc seul l'affichage est en cause. Le 30/10/2026, Ctrl+Alt+Suppr envoyé depuis VMware a ramené l'écran de connexion. Écarté le 30/10/2026 : l'extinction de l'écran du bureau (`idle-delay` déjà à 0) et celle de la console texte (`consoleblank` à 0). La session du bureau est en Wayland et `open-vm-tools` est actif ; le seul avertissement vu (`gsd-xsettings`) n'a pas de lien établi. Si cela revient : essaie d'abord une connexion `ssh` avant de redémarrer, puis, **avant** Ctrl+Alt+Suppr, lance `loginctl show-session 2 -p Active -p LockedHint -p IdleHint; journalctl -b --no-pager -p warning -n 40`. Pour lire tout le journal, l'utilisateur doit être dans le groupe `systemd-journal` (`usermod -aG systemd-journal UTILISATEUR`, en `root` avec `su -`).

### Cas : un autre service est déjà publié (exemple : un LLM publié par `tailscale serve` sur le port 443)
Ne lance pas `tailscale funnel` sur le port 443 : il remplacerait ce service. Funnel accepte aussi les ports 8443 et 10000 (documentation Tailscale) : publie la page et la présence sous le même nom sur le port 8443, le service existant garde le 443. **Commandes proposées, non essayées** (`PORT_PAGE` est le port local du serveur qui sert la page) :
- `tailscale funnel --bg --https=8443 --set-path=/presence http://127.0.0.1:8765`
- `tailscale funnel --bg --https=8443 http://127.0.0.1:PORT_PAGE`
- présence lancée avec `--host 127.0.0.1 --proxy-header X-Forwarded-For --origins "https://MACHINE.TAILNET.ts.net:8443"`
- adresse de présence : `wss://MACHINE.TAILNET.ts.net:8443/presence` ; adresse de la page : `https://MACHINE.TAILNET.ts.net:8443/`.

Avant de lancer quoi que ce soit : `tailscale serve status` et `tailscale funnel status`, puis la même vérification après.

### Brancher les pages (les quatre voies)
Une région à la fois : `glb2html.py --update -o "CHEMIN\X.html" --shared-shell --presence-url "wss://ADRESSE"` (la ligne `--update` de la section 4 plus `--presence-url`). Ou la clé `presenceUrl` de `X.config.json`. La coquille de la page n'est pas mise à jour par `build.py` : refais `--update` pour chaque région après une nouvelle version.

### Contrôler l'adresse vue par le serveur (à faire une fois, avec `--log-ip raw`)
Ouvre une page depuis un téléphone en 4G (pas depuis ton réseau, et avec Tailscale coupé), puis lis `presence.log` : l'adresse écrite doit être celle du téléphone. Si tu vois `127.0.0.1` ou l'adresse du relais, l'en-tête donné à `--proxy-header` est mauvais ou absent : **les bannissements par IP ne marcheraient pas**. Les en-têtes attendus : `X-Forwarded-For` (Caddy, nginx, Tailscale Funnel : vérifié le 24/10/2026), `CF-Connecting-IP` (Cloudflare).

### À garder en tête
- `--origins` limite les connexions aux pages de ton site ; sans lui, n'importe quelle page peut se brancher sur ton serveur. Plusieurs sites : une liste séparée par des virgules.
- Les limites existantes restent actives : `--max-per-ip` (10), `--max-per-room` (50), `--chat-burst`, message de 4 096 octets au plus.
- Cacher l'IP protège la machine, pas le service : un abus (messages, pseudos) se traite par la modération (section 6, étape 5). Lancé comme simple service système, le serveur n'a pas de clavier : la solution essayée (une session `tmux` lancée par systemd) est décrite plus haut.
- Le relais (Tailscale, Cloudflare) voit le trafic déchiffré. Les messages et les adresses restent des données personnelles : informe les visiteurs.
- Relance toujours le serveur après `python build.py` (section 6, étape 6).
