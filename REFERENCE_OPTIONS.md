# Référence complète des options

*Générée le 23/10/2026 par `gen_reference.py`, à partir des outils eux-mêmes : toute option qui existe dans un outil figure ici. Ne la modifie pas à la main : relance le script. Un * en fin de description signale un texte de secours du script, l'outil n'en ayant pas.*

## glb2html.py

Fabrique la page web d'une région (GLB unique ou tuiles), met une région à jour, enregistre une région dans la carte des mondes et génère la page carte.

| Option | Valeur | Défaut | Effet |
|---|---|---|---|
| `--version` |  |  | show program's version number and exit |
| `input` (facultatif) |  |  | fichier .glb ou dossier de .glb |
| `--zones-live` | NOM |  | la page recharge ses zones à chaque ouverture depuis un fichier .zones.json placé à côté d'elle (servie en http/https ; sinon les zones intégrées servent). Sans NOM : <page>.zones.json. Le fichier est écrit par le script, filtré selon --profile |
| `--zones-only` | (aucune) |  | réécrit seulement les zones, sans régénérer le HTML : <page>.zones.json d'une page modulaire déjà générée (avec --zones FICHIER), ou, avec --zones-live, le fichier de zones d'une page autonome |
| `-o` / `--output` | OUTPUT |  | sortie : fichier .html, ou dossier (créé si besoin). Entrée dossier : dossier de sortie. Défaut : "<nom> - Offline.html" à côté du .glb |
| `--rotate` | 0 ou 90 ou 180 ou 270 | `0` | rotation de la région autour de l'axe vertical (0, 90, 180 ou 270 degrés), appliquée au chargement avant le recentrage. Les zones, arrivées, cible et trou du fichier de zones / de réglages sont DÉJÀ dans le repère tourné (le viewer les fait tourner avec la région) |
| `--hole` | HOLE | `180.0` | rayon du trou 30..600 (zone plate = rayon - fondu) |
| `--hole-fade` | HOLE_FADE | `60.0` | demi-largeur du fondu du trou |
| `--hole-x` | HOLE_X | `0.0` | position X du centre du trou (monde) |
| `--hole-z` | HOLE_Z | `0.0` | position Z du centre du trou (monde) |
| `--wave` | WAVE | `0.5` | amplitude vagues 0..10 |
| `--sea-y` | SEA_Y | `-50.0` | hauteur mer -150..60 |
| `--zoom` | ZOOM | `1.0` | ratio de cadrage (1 = cadrage auto) |
| `--cam-dir` | CAM_DIR | `(0.0, 0.25, 1.0)` | direction caméra x,y,z |
| `--target` | TARGET | `(0.0, 15.0, 0.0)` | cible caméra x,y,z |
| `--foliage-cutout` | FOLIAGE_CUTOUT | `0.12` | seuil alpha feuillage 0..0.5 |
| `--sea-color` | SEA_COLOR | `3a9ad9` | couleur mer, ex 3a9ad9 |
| `--sky-color` | SKY_COLOR | `87ceeb` | couleur ciel, ex 87ceeb |
| `--sea-segments` | SEA_SEGMENTS | `400` | finesse du maillage de la mer 8..1000 (maille = 4000/segments ; seulement avec --anim) |
| `--walk` / `--no-walk` | (aucune) |  | inclure le mode promenade (touche F) dans la page |
| `--eye-height` | EYE_HEIGHT | `1.7` | hauteur des yeux en m (promenade) |
| `--walk-speed` | WALK_SPEED | `3.5` | vitesse de marche en m/s (Maj = x2.2) |
| `--walk-ignore` | WALK_IGNORE | `door, porte` | noms à ignorer en collision, séparés par des virgules : "door" = début de mot, "=mesh_346_5" = nom exact ; "" = rien |
| `--names` / `--no-names` | (aucune) |  | afficher le nom de l'élément cliqué |
| `--presence-url` | PRESENCE_URL | (vide) | serveur de présence ws:// ou wss:// (voir presence_server.py) ; vide = désactivé |
| `--chat` / `--no-chat` | (aucune) |  | chat entre visiteurs (nécessite --presence-url ; touche Entrée en promenade) |
| `--chat-fade` | CHAT_FADE | `0.0` | secondes avant disparition des messages et bulles ; 0 = restent jusqu'à ce que de nouveaux messages les remplacent |
| `--zones` | ZONES |  | fichier .json de zones exporté par le viewer ; chemin relatif : cherché dans le dossier de lancement, puis dans le dossier du script. Une zone peut porter un champ mesh (nom exact d'un élément du modèle) : l'élément devient cliquable |
| `--profile` | public ou perso | `public` | public : retire les zones privées (ex. Home Assistant) ; perso : les garde |
| `--spectate` / `--no-spectate` | (aucune) |  | voir les visiteurs en promenade depuis la vue globale (se connecte dès l'ouverture de la page ; actif par défaut dès qu'une --presence-url est donnée ; --no-spectate pour l'éviter) |
| `--panel` / `--no-panel` | (aucune) |  | panneau de réglages pour les visiteurs (haute résolution, mer animée, force des vagues), bouton en haut à droite |
| `--map` | MAP |  | fichier regions.json (carte des mondes : nom, adresse, position, vignette) exporté par le viewer ; chemin relatif : dossier de lancement, puis dossier du script |
| `--map-url` | MAP_URL | (vide) | adresse(s) de regions.json partagé(s), séparées par des virgules : la page les relit à chaque ouverture (http/https), les fusionne et complète avec la carte intégrée. Un autre site doit autoriser l'accès (CORS) |
| `--register` | REGISTER |  | fichier regions.json à mettre à jour avec CETTE région (ajoutée ou mise à jour par salon) ; relatif : dossier de lancement s'il y existe, sinon dossier du script. La page générée embarque la carte à jour |
| `--region-name` | REGION_NAME |  | nom affiché dans la carte (défaut : nom du .glb) |
| `--region-url` | REGION_URL |  | adresse de la page de cette région (défaut : le nom du fichier .html, relatif) |
| `--region-xy` | X,Y |  | position sur la grille, comme OpenSim (X vers l'est, Y vers le nord), ex. 1000,1001 |
| `--region-spawn` | REGION_SPAWN |  | identifiant du point d'arrivée des visiteurs dans cette région (défaut : default) |
| `--thumb` | THUMB |  | vignette de la région : fichier jpg/png/webp de 140 Ko maximum (intégré), ou adresse http(s) (gardée telle quelle, carte plus légère) |
| `--map-page` | FICHIER.html |  | génère aussi une page web « carte des mondes » (liens cliquables vers chaque région) ; sans .glb : génère seulement cette page depuis --map. Relatif : à côté de la page de la région |
| `--settings` | FICHIER |  | reprend TOUS les réglages enregistrés par le viewer (bouton « Enregistrer dans un fichier » : trou, vagues, caméra, zones, fiche de région, vignette…). Sans nom : <nom du .glb>.reglages.json. Les options de la ligne de commande l'emportent. Relatif : dossier de lancement, puis dossier du script |
| `--modular` | (aucune) |  | mode modulaire : écrit une coquille <page>.html identique pour toutes les régions (elle déduit ses fichiers de son nom) + <page>.glb (octets bruts) + <page>.config.json (réglages) + <page>.zones.json (zones, relues à chaque ouverture ; à défaut zones.json du dossier) + lib/three-X/ partagé (Draco et Meshopt compris). Demande http(s) pour l'ouverture (pas depuis le disque) |
| `--shared-shell` | COQUILLE.html |  | mode modulaire à coquille commune : une seule coquille (défaut index.html) sert plusieurs régions du même dossier, à l'adresse COQUILLE.html?region=NOM. -o désigne la région (NOM = son nom sans extension, ex. -o Ankh.html) : seuls NOM.glb, NOM.config.json et NOM.zones.json sont écrits, plus la coquille et lib/three-X/ s'ils sont absents (une coquille existante n'est jamais écrasée). --register écrit cette adresse dans regions.json. Implique --modular |
| `--tiles` | X.tiles.json |  | région découpée en tuiles par glb2tiles.py : pas de .glb en entrée ; -o désigne la région. Écrit X.config.json (champ « tiles »), X.zones.json, la coquille et lib/ ; X.tiles.json et ses tuiles ne sont copiés que s'ils ne sont pas déjà à côté de la page. Implique --modular. Repère = celui du modèle d'origine (aucun recentrage) ; zones liées à un objet : possibles si les tuiles viennent de glb2tiles v32, ignorées sinon |
| `--tile-radius` | TILE_RADIUS | `150.0` | m : charger les tuiles dont la boîte est à moins de ce rayon de l'avatar, en plan X,Z (défaut %(default)g ; ?rayon=NNN dans l'adresse pour essayer) |
| `--tile-margin` | TILE_MARGIN | `60.0` | m : décharger les tuiles au-delà de rayon + marge (défaut %(default)g) |
| `--tile-max-mo` | TILE_MAX_MO | `200.0` | Mo de tuiles chargées en même temps (poids des fichiers ; défaut %(default)g) ; au-delà, les plus lointaines partent d'abord |
| `--tile-max-tri` | TILE_MAX_TRI | `8000000` | triangles de tuiles chargées en même temps (défaut %(default)d) |
| `--tile-concurrency` | TILE_CONCURRENCY | `4` | téléchargements simultanés (défaut %(default)d) |
| `--config-only` | (aucune) |  | réécrit seulement <page>.config.json d'une page modulaire déjà générée (indiquée par -o), sans toucher au .glb ni à la coquille ; les visiteurs rechargent. <page>.zones.json n'est réécrit que si --zones est donné. Avec --register, met aussi la carte à jour |
| `--zone-marker` | discret ou portee ou aucun | `discret` | marqueur des portails et zones libres dans la page : discret (défaut : disque de 0,4 m et anneau fin), portee (anneau fin et net au rayon réel de la zone, visible de loin) ou aucun. Les arrivées ne sont jamais dessinées (voir --show-spawns) |
| `--show-spawns` / `--no-show-spawns` | (aucune) |  | dessine aussi les arrivées dans la page (petit marqueur discret au sol ; défaut : jamais) |
| `--zone-info-dist` | M | `40.0` | distance (5 à 200 m, défaut 40) jusqu'à laquelle l'infobulle, le clic et le nom affiché (showName) des zones marchent en promenade |
| `--fly` / `--no-fly` | (aucune) |  | vol en promenade (touche F ou Début ; Page Haut / E monte, Page Bas / C descend) : activé par défaut, --no-fly le retire |
| `--maj` | (aucune) |  | met à jour une région déjà générée (-o REGION.html [--shared-shell [COQUILLE.html]] [--tiles X.tiles.json \| X.glb]) : lit X.config.json, n'applique QUE les options données sur la ligne, garde tout le reste et X.zones.json (réécrit seulement avec --zones), écrit la version courante et renouvelle la coquille si elle est plus ancienne (ancienne copie gardée sous un nom daté). Échoue si X.config.json n'existe pas |
| `--room` | ROOM | (vide) | salon de présence (défaut : nom du fichier) |
| `--sea` / `--no-sea` | (aucune) |  | affiche la mer (--no-sea : sans mer) * |
| `--anim` / `--no-anim` | (aucune) |  | anime la mer (vagues) ; --no-anim : mer fixe * |
| `--retina` / `--no-retina` | (aucune) |  | haute résolution : rendu x2 minimum (supersampling, plus net mais ~4x plus lourd) |
| `--title` | TITLE |  | titre de la page |
| `--vendor` | VENDOR |  | racine d'un paquet npm three local (sinon cache + téléchargement) |

## glb2tiles.py

Découpe un GLB énorme en tuiles autonomes et fabrique la vue d'ensemble légère.

| Option | Valeur | Défaut | Effet |
|---|---|---|---|
| `glb` (obligatoire) |  |  | GLB d'entrée |
| `--version` |  |  | show program's version number and exit |
| `--analyse` | (aucune) |  | lecture seule : mesures, découpage prévu, recommandation ; n'écrit rien |
| `--budget` | BUDGET | `32.0` | Mo par tuile (défaut 32) |
| `--budget-tri` | BUDGET_TRI | `1500000` | triangles par tuile (défaut 1500000) |
| `--min` | COTE_MIN | `16.0` | côté minimal d'une cellule en m (défaut 16) |
| `--entier-poids` | ENTIER_POIDS | `16.0` | Mo : un objet racine plus léger et plus petit que --entier-etendue reste entier (défaut 16) |
| `--entier-etendue` | ENTIER_ETENDUE | `256.0` | m : étendue maximale d'un objet racine gardé entier (défaut 256) |
| `--seuil` | SEUIL | `150.0` | Mo : sous ce poids (et sous --seuil-tri) « pas de découpage » (défaut 150) |
| `--seuil-tri` | SEUIL_TRI | `3000000` | triangles pour la recommandation « pas de découpage » (défaut 3000000) |
| `--aberrant` | ABERRANT | `1000.0` | m : distance ou étendue au-delà de laquelle une instance est signalée (défaut 1000) |
| `--bloc` | BLOC | `256.0` | côté des blocs de la section glb-stats de --analyse (défaut 256) |
| `--exclure` | REGEX | `[]` | retire du découpage les objets racine dont le nom correspond (insensible à la casse, répétable), à condition de respecter --exclure-max-tri et --exclure-max-meshes |
| `--exclure-max-tri` | EXCLURE_MAX_TRI | `24` | avec --exclure : triangles au plus dans l'objet racine, tous meshes compris (défaut 24) |
| `--exclure-max-meshes` | EXCLURE_MAX_MESHES | `1` | avec --exclure : meshes au plus dans l'objet racine (défaut 1) |
| `--sans-references` | (aucune) |  | ne pas écrire extras.ref / extras.box dans les nœuds des tuiles (format de la v31 : les zones liées à un objet sont alors ignorées en mode tuiles) |
| `--sans-vue-ensemble` | (aucune) |  | ne pas écrire X.overview.glb (vue d'ensemble légère de toute la région) |
| `--vue-ensemble-seule` | (aucune) |  | n'écrire que X.overview.glb (et sa mention dans X.tiles.json) : les tuiles existantes ne sont pas réécrites ; les paramètres de découpage doivent être ceux du découpage d'origine |
| `--ov-budget` | OV_BUDGET | `25.0` | Mo : poids maximal de la vue d'ensemble (défaut %(default)g) |
| `--ov-budget-tri` | OV_BUDGET_TRI | `1500000` | triangles de la vue d'ensemble (défaut %(default)d) |
| `--ov-seuil` | OV_SEUIL | `3.0` | m : les objets dont la plus grande dimension est plus petite sont omis (défaut %(default)g) ; le budget peut le relever |
| `--ov-seuil-max` | OV_SEUIL_MAX | `24.0` | m : si le budget oblige à omettre des objets plus grands, la résolution baisse (défaut %(default)g) |
| `--ov-resolution` | OV_RESOLUTION | `10` | cellules sur la plus grande dimension d'une primitive pour le regroupement de sommets (défaut %(default)d) |
| `--ov-terrain-pas` | OV_TERRAIN_PAS | `4.0` | m : pas du réseau du terrain dans la vue d'ensemble (défaut %(default)g) |
| `--forcer` | (aucune) |  | découper même si la recommandation est « pas de découpage » |
| `--sortie` | SORTIE |  | dossier de sortie (défaut : à côté du GLB) |
| `--nopause` | (aucune) |  | ne pas attendre Entrée à la fin |

## oar2glb.py

Convertit une sauvegarde de région OpenSim (.oar) en GLB, refait le terrain complet.

| Option | Valeur | Défaut | Effet |
|---|---|---|---|
| `--version` |  |  | show program's version number and exit |
| `oar` (obligatoire) |  |  | fichier .oar (ou .tgz) de la région à convertir * |
| `--reencode` | (aucune) |  | réencoder les textures J2K avant convoar |
| `--max` | MAX | `600.0` | hauteur max (m) d'un objet racine (skybox au-delà), défaut 600 |
| `--convoar` | CONVOAR | `P:\_OpenSim\SL&OS\MOSES\convoar-master\dist\convoar.exe` | chemin de convoar.exe si ce n'est pas celui par défaut * |
| `--keep` | (aucune) |  | garder les fichiers intermédiaires |
| `--keep-invisible` | (aucune) |  | garder les prims entièrement transparents (retirés par défaut) |
| `--reperes` | (aucune) |  | ajouter un mât rouge de 15 m à chaque animal riggé posé (pour le retrouver dans le viewer) |
| `--diag` | (aucune) |  | ne rien modifier : lister les objets de l'OAR, leur skin et le nœud GLB correspondant |
| `--glb` | GLB |  | avec --diag : GLB ou .gltf à comparer ; défaut : le .gltf du dossier <oar>-GLTF (conservé par --keep), sinon le .glb voisin |
| `--nopause` | (aucune) |  | ne pas attendre Entrée à la fin |
| `--terrain` | auto ou oui ou non | `auto` | terrain complet depuis la carte de hauteurs : auto = remplace le terrain de convoar s'il couvre moins que la carte (défaut), oui = toujours, non = jamais |
| `--terrain-patch` | TERRAIN_PATCH | `64` | côté d'un patch de terrain en mètres, 2 à 255 (défaut 64) |
| `--terrain-seul` | GLB |  | ne pas lancer convoar : ajouter le terrain complet à ce GLB (écrit X-terrain.glb, l'original n'est jamais modifié) |
| `--sortie` | SORTIE |  | avec --terrain-seul : fichier GLB de sortie (défaut : X-terrain.glb à côté de l'original) |

## presence_server.py

Serveur de présence : positions des visiteurs, chat, modération.

| Option | Valeur | Défaut | Effet |
|---|---|---|---|
| `--version` |  |  | show program's version number and exit |
| `--host` | HOST | `0.0.0.0` | adresse d'écoute (0.0.0.0 = toutes les interfaces) * |
| `--port` | PORT | `8765` | port d'écoute des visiteurs * |
| `--max-per-room` | MAX_PER_ROOM | `50` | promeneurs max par salon |
| `--max-spectators` | MAX_SPECTATORS | `100` | spectateurs (vue globale) max, tous salons |
| `--max-total` | MAX_TOTAL | `500` | connexions simultanées au total, tous salons * |
| `--max-per-ip` | MAX_PER_IP | `10` | connexions simultanées par adresse IP |
| `--max-chat` | MAX_CHAT | `200` | longueur max d'un message de chat |
| `--chat-gap` | CHAT_GAP | `0.7` | délai mini entre deux messages d'un visiteur (s) |
| `--chat-burst` | CHAT_BURST | `5` | messages max par fenêtre de 10 s et par visiteur |
| `--history` | HISTORY | `20` | derniers messages rejoués aux nouveaux arrivants (mémoire seulement, 0 = aucun) |
| `--identities` | IDENTITIES | `presence_identities.json` | registre des noms réservés (vide = en mémoire seulement) ; chemin relatif = dossier du script |
| `--name-ttl-days` | NAME_TTL_DAYS | `365` | un nom non utilisé depuis ce nombre de jours est libéré |
| `--reserved` | RESERVED | (vide) | noms interdits à la réservation, séparés par des virgules (ex. admin,moderateur) |
| `--log` | LOG |  | fichier de journal (tourné chaque nuit) ; chemin relatif = dossier du script |
| `--log-days` | LOG_DAYS | `30` | jours de journal conservés |
| `--log-ip` | hash ou raw ou none | `hash` | adresses IP dans le journal : masquées (défaut), en clair, ou absentes |
| `--proxy-header` | PROXY_HEADER |  | derrière un reverse proxy : en-tête portant l'IP réelle du visiteur (ex. X-Forwarded-For, CF-Connecting-IP) ; à n'activer que si le serveur n'est joignable que par ce proxy |
| `--bans` | BANS | `presence_bans.json` | fichier des bannissements ; chemin relatif = dossier du script |
| `--origins` | ORIGINS |  | origines autorisées, séparées par des virgules (défaut : toutes) |
| `--cert` | CERT |  | certificat TLS (wss://) |
| `--key` | KEY |  | clé privée TLS |

