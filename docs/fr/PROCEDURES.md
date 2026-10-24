# Que faire pour… (procédures pas à pas)

*Écrit le 23/10/2026 pour la version v36. Les commandes sont en PowerShell, sur une seule ligne, avec les chemins de ta machine. La liste complète des options est dans `REFERENCE_OPTIONS.md` ; le détail des zones, touches et réglages est dans `MANUEL.md`.*

**Ce qui a été essayé ici :** les commandes de `glb2html`, `glb2tiles` (y compris `--maj`, `--register`, `--map-page`) sur des régions de test, un seul GLB et en tuiles. **Ce qui ne l'a pas été :** la conversion d'un OAR par convoar (convoar n'est pas disponible dans le bac à sable), et les commandes PowerShell elles-mêmes (essayées sous Linux avec des chemins équivalents).

**Les trois dossiers de référence**

| Rôle | Chemin |
|---|---|
| Outils (fabriqués par `python build.py`) | `P:\_OpenSim\SL&OS\Web_3d\web_3d\dist` |
| OAR et GLB source | `J:\Download\Com\Chat\_Monde virtuel en ligne_\_OpenSim_\_Contenu_\OAR` |
| Régions publiées en tuiles | `P:\_OpenSim\SL&OS\Web_3d\tuiles` |

**Règle d'or :** lance toujours les outils depuis le dossier des outils (`cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"`). Donne des **chemins complets** pour tout fichier écrit, sauf avec `--maj` (les chemins relatifs y sont relatifs au dossier de la page).

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
3. **Découper.** `--sortie` désigne le dossier où sont écrits `X.tiles\`, `X.tiles.json` et `X.overview.glb`. `--exclure` retire du découpage les objets dont le nom correspond (garde-fous : 24 triangles et 1 mesh au plus), par exemple les boîtes de livraison des catalogues.
   `python glb2tiles.py "J:\...\OAR\X.glb" --sortie "P:\_OpenSim\SL&OS\Web_3d\tuiles" --exclure "RAKis Freebies"`
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
Clés utiles : `seaY` (hauteur de la mer, en m), `target` (`[x, y, z]`), `presenceUrl`, `chat` (`true` ou `false`), `zoneInfoDist`, `tileRadius`, `tileMaxMo`, `tileMaxTri`. Le JSON est strict : garde les virgules et les guillemets. **Les couleurs y sont des nombres décimaux** (`seaColor` 3840729 vaut `3a9ad9`) : pour les changer, passe plutôt par `--maj`.

**Plusieurs valeurs, ou une couleur : `--maj`.** Il applique seulement les options que tu écris, garde tout le reste de la config et le fichier de zones.
`cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python glb2html.py --maj --shared-shell -o "P:\_OpenSim\SL&OS\Web_3d\tuiles\X.html" --sea-y 10`

**Ne relance jamais la commande complète de fabrication (procédure 2.4) pour changer un détail** : elle réécrit toute la config à partir des seules options de la ligne, et efface ce que tu avais réglé à la main.

## 4. Après une nouvelle version des outils

1. Fusionner la branche de la session, fabriquer, pousser, étiqueter (la session donne la ligne exacte) :
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d"; git checkout main; git pull; git fetch; git merge origin/NOM -m "Fusion vNN"; python build.py; git push; git tag vNN HASH; git push origin vNN`
2. Mettre à jour chaque région avec `--maj`. La coquille `index.html` est renouvelée si elle est plus ancienne (l'ancienne est gardée sous un nom daté), la config et les zones sont gardées.
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python glb2html.py --maj --shared-shell -o "P:\_OpenSim\SL&OS\Web_3d\tuiles\X.html"`
3. Recharger la page avec Ctrl+F5. La ligne du bas du panneau d'aide donne la version affichée (par exemple « glb2html v36 ») : si elle est ancienne, la mise à jour n'a pas eu lieu.
4. Relancer le serveur de présence : **oui pour la v36** (ses messages et son aide sont traduits ; un ancien exemplaire continue de marcher mais reste en français). Procédure 6.
5. Le découpage en tuiles n'est à refaire que si la session le dit, par exemple pour de nouvelles informations dans les tuiles.

## 5. Poser et modifier des zones

| Besoin | Où |
|---|---|
| Poser portail, arrivée, panneau, lien | viewer, `MANUEL.md` §§ 3 à 8 |
| Arrivée utilisée à l'ouverture sans lien | une arrivée nommée `default` (§ 4) ; `--target` explicite garde le cadrage |
| Portail vers une autre région | `MANUEL.md` § 6 |
| Zone liée à un objet du modèle | `MANUEL.md` § 9 (en tuiles : § 17 ter) |
| Zone privée (visible seulement avec le profil « perso ») | `MANUEL.md` § 10 |

Les zones d'une région en tuiles s'écrivent dans le repère d'origine du modèle (aucun recentrage). Le viewer en mode tuiles produit ces coordonnées directement ; ne reporte pas à la main des coordonnées d'un autre GLB.

## 6. Serveur de présence (positions, chat, modération)

1. **Installer** une fois : `pip install websockets`
2. **Lancer** (le journal relatif est écrit dans le dossier du script ; `--log-ip raw` écrit les adresses IP en clair, `--log-days` limite la conservation, **`--log-days 0` conserve les journaux sans limite**) :
   `python ".\presence_server.py" --log presence.log --log-ip raw --log-days 0`
   Historique du chat (v37) : 200 derniers messages rejoués aux nouveaux arrivants (`--history`) ; `--history-file chat.jsonl` le garde entre deux relances (messages = données personnelles, jamais d'adresse IP dans ce fichier), `--history-days N` (30 ; 0 = tout conserver) limite la relecture au démarrage.
3. **Ouvrir le port** (8765 par défaut, `--port` pour en changer) dans la box, vers la machine qui fait tourner le serveur.
4. **Brancher la page** : `--presence-url "ws://ADRESSE:8765"` à la fabrication, ou la clé `presenceUrl` de `X.config.json`. Si la page est en https, l'adresse doit être en `wss://` (voir `--cert` et `--key`, ou un reverse proxy avec `--proxy-header`).
5. **Modérer** dans la console du serveur : `liste` (visiteurs), `ejecter <n°|nom> [raison]`, `bannir <n°|nom> [minutes] [raison]` (0 = définitif), `bans`, `debannir <n° de bans>`, `aide`.
6. **Mettre à jour** : arrête le serveur (Ctrl+C) et relance-le depuis le `presence_server.py` du dossier `dist` après `python build.py`. Un ancien exemplaire ignore les nouveautés (par exemple la couleur choisie).

Les adresses IP et les messages du chat sont des données personnelles : informe tes visiteurs et limite la durée de conservation.

## 7. Carte des mondes

Deux étapes, avec `--maj` (les chemins relatifs y sont relatifs au dossier de la page).

1. **Enregistrer chaque région** dans `regions.json` :
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python glb2html.py --maj -o "P:\_OpenSim\SL&OS\Web_3d\tuiles\X.html" --shared-shell --register "P:\_OpenSim\SL&OS\Web_3d\tuiles\regions.json" --region-name "Nom affiché"`
   Pour une autre région, même commande avec sa page et son nom (`--region-xy x,y` donne sa place sur la carte).
2. **Générer la page carte** (après chaque enregistrement) :
   `python glb2html.py --maj -o "P:\_OpenSim\SL&OS\Web_3d\tuiles\X.html" --shared-shell --map-page "P:\_OpenSim\SL&OS\Web_3d\tuiles\carte.html"`
3. Ouvre `carte.html` par le serveur web. Un champ « Mon pseudo » en haut ajoute `name=` aux liens des régions.

Avec une seule région, la carte n'apporte rien : elle sert à relier plusieurs régions entre elles.

## 8. Quand relancer quoi

| Ce qui a changé | À faire | Page à recharger |
|---|---|---|
| Une valeur de réglage (mer, cible, présence) | modifier `X.config.json`, ou `--maj` avec l'option | F5 |
| Les zones | enregistrer `X.zones.json` dans le dossier de la région | F5 |
| Nouvelle version des outils | procédure 4 (`--maj`) | Ctrl+F5 |
| Nouvelle version du serveur de présence (v37 : historique du chat ; v36 : messages traduits) | arrêter et relancer `presence_server.py` | F5 |
| L'OAR a changé | reconvertir (1.1 ou 2.1), redécouper (2.3), puis `--maj` | Ctrl+F5 |
| Les objets exclus du découpage | redécouper (2.3) avec un autre `--exclure` | Ctrl+F5 |
| Rotation de la région (`--rotate`) | `--maj --rotate 180`, puis refaire la vignette de la carte | Ctrl+F5 |
| Première mise en ligne d'une région | procédure 1 ou 2 (commande complète) | — |

## 9. Quand ça ne marche pas

| Symptôme | Cause probable | À faire |
|---|---|---|
| Page noire avec `#spawn=…` | la tuile de l'arrivée se charge | depuis la v33, un texte « Chargement du sol… » doit s'afficher ; sinon, console (F12) et lignes `[tuile] …` |
| « Chargement du sol… » qui dure | grosse tuile | patienter ; relever les lignes `[tuile] …` de la console |
| Les zones n'apparaissent pas | fichier de zones ailleurs que dans le dossier de la page, zone privée, marqueur discret | vérifier `X.zones.json` dans le dossier servi, F5 en fenêtre privée, `--zone-marker portee` |
| Les réglages ne changent pas | coquille ancienne, cache | `--maj`, puis Ctrl+F5 |
| Erreurs « Couldn't load texture » | images de 0 octet dans des tuiles d'avant la v31 | redécouper avec glb2tiles v31 ou plus |
| Pas de chat | page fabriquée sans `--presence-url` ou sans `--chat` | ajouter les options avec `--maj`, relancer le serveur |
| La couleur d'avatar ne change pas | serveur de présence ancien | relancer le `presence_server.py` du dossier `dist` |
| Copier le texte de l'aide | — | sélectionner à la souris, Ctrl+C ; sinon, dans la console : `copy(document.body.innerText)` |

Pour tout rapport de bug, colle le texte du panneau d'état et d'aide, et les messages de la console (en ignorant ceux de LastPass).

## 10. Touches utiles et langue (v36)

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
| Boussole (cap en haut de la page) | case « Boussole » des Réglages ; `--no-compass` pour la retirer de la fabrication, `--north DEGRES` pour un GLB qui ne vient pas d'OpenSim |
| Régler la largeur de l'aide et des informations | tirer leur bord droit (260 px à 70 % de la fenêtre), mémorisé |
| Chat : messages plus anciens, non lus, citations | bouton « Messages plus anciens » (chat ouvert), titre de l'onglet « (3) Région », « N messages vous citent » ; réglage « Messages d'historique affichés » |
| Région par défaut (adresse sans `?region=`) | `default.json` écrit à la première région d'un dossier, `--default` pour en changer ; sinon la première entrée relative de `regions.json` |
| Mettre `lib/` ailleurs | `--lib-url ../lib` (ou une adresse `https://…/lib`) à la fabrication de la coquille ; retenu pour `--maj` |
| Région dans un sous-dossier | `glb2html.py X.glb --shared-shell "P:\site\index.html" -o "P:\site\sous\dossier\X.html"` ; adresse `index.html?region=sous/dossier/X` |
| Paramètres de l'adresse | séparés par `&` ; `#` est aussi accepté (`#name=Klaatou&lang=en` = `#name=Klaatou#lang=en`) |

Détail : `MANUEL.md` §§ 2, 21 et 22.

---

## 11. Rendre le serveur de présence public sans montrer son adresse IP

*Rédigé le 24/10/2026. **Non testé** : ni Tailscale Funnel, ni Caddy, ni Cloudflare Tunnel n'ont été essayés dans le bac à sable de conception. Les lignes ci-dessous suivent la documentation de ces outils ; vérifie le résultat avec le contrôle de l'étape finale (« Contrôler l'adresse vue par le serveur »).*

**Principe.** Les pages sont en https, donc l'adresse de présence doit être en `wss://NOM`. Le visiteur ne se connecte qu'à ce `NOM`, jamais à ton IP. Un relais reçoit le `wss://` et le transmet en `ws://` à `presence_server.py`, qui n'écoute alors que sur `127.0.0.1` (donc sans `--cert` ni `--key`). Choisis **une** des trois voies.

### Voie A : chez toi, Tailscale Funnel (aucun port à ouvrir dans la box)
1. Installe Tailscale sur la machine qui fait tourner le serveur et connecte-la à ton compte. Dans la console d'administration Tailscale, active **HTTPS** (DNS) et autorise **Funnel** pour cette machine (voir la documentation « Tailscale Funnel »).
2. Lance le serveur sur l'adresse locale seulement (PowerShell, une ligne) : `python ".\presence_server.py" --host 127.0.0.1 --port 8765 --origins "https://TONSITE" --log presence.log --log-ip raw --log-days 0 --history-file chat.jsonl --history-days 0`
3. Expose-le : `tailscale funnel --bg 8765`. L'adresse publique est `https://MACHINE.TAILNET.ts.net` ; l'adresse de présence est donc `wss://MACHINE.TAILNET.ts.net`.
4. Ton IP n'apparaît pas ; en revanche le nom de ta machine et celui de ton réseau Tailscale sont publics.

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

### Brancher les pages (les trois voies)
Une région à la fois : `glb2html.py --maj -o "CHEMIN\X.html" --shared-shell --presence-url "wss://ADRESSE"` (la ligne `--maj` de la section 4 plus `--presence-url`). Ou la clé `presenceUrl` de `X.config.json`.

### Contrôler l'adresse vue par le serveur (à faire une fois, avec `--log-ip raw`)
Ouvre une page depuis un téléphone en 4G (pas depuis ton réseau), puis lis `presence.log` : l'adresse écrite doit être celle du téléphone. Si tu vois `127.0.0.1` ou l'adresse du relais, l'en-tête donné à `--proxy-header` est mauvais ou absent : **les bannissements par IP ne marcheraient pas**. Les en-têtes attendus : `X-Forwarded-For` (Caddy, nginx), `CF-Connecting-IP` (Cloudflare) ; pour Funnel, essaie `X-Forwarded-For` et dis-moi ce que montre le journal.

### À garder en tête
- `--origins` limite les connexions aux pages de ton site ; sans lui, n'importe quelle page peut se brancher sur ton serveur. Plusieurs sites : une liste séparée par des virgules.
- Les limites existantes restent actives : `--max-per-ip` (10), `--max-per-room` (50), `--chat-burst`, message de 4 096 octets au plus.
- Cacher l'IP protège la machine, pas le service : un abus (messages, pseudos) se traite par la modération (section 6, étape 5).
- Le relais (Tailscale, Cloudflare) voit le trafic déchiffré. Les messages et les adresses restent des données personnelles : informe les visiteurs.
- Relance toujours le serveur après `python build.py` (section 6, étape 6).
