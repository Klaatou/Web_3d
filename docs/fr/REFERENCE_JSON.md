# Référence des fichiers JSON (v43)

Ce document décrit **chaque fichier JSON du projet, champ par champ**, comme le font `opensim.sample.ini` et `robust.sample.ini` pour OpenSim. Il était le chapitre 11 du manuel (`MANUEL.md`) ; **la numérotation 11.1 à 11.12 est conservée**, pour que les renvois « § 11.x » écrits ailleurs restent valables. Les renvois « § N » dont N n'est pas 11 visent `MANUEL.md`.

Un fichier JSON n'accepte pas de commentaires. Les explications sont donc ici, et les exemples sont à part, dans le dossier `docs/samples/` : ce sont de **vrais fichiers, complets et valides**. Pour s'en servir, on copie l'exemple, on le renomme et on change les valeurs. Le test `tests/samples.py` vérifie que chaque exemple est accepté par le vrai code qui lit ce fichier : la page, le viewer, les outils et le serveur de présence. Les exemples restent donc justes quand le code change.

## 11.1 Les fichiers et leurs exemples

| Fichier réel                                           | Exemple dans `docs/samples/`       | Écrit par                                    | Lu par                                               |
| ------------------------------------------------------ | ---------------------------------- | -------------------------------------------- | ---------------------------------------------------- |
| `NOM.config.json`                                      | `region.config.sample.json`        | `glb2html.py`                                | la page                                              |
| `NOM.zones.json`                                       | `region.zones.sample.json`         | le viewer, `glb2html.py --zones`, à la main  | la page, le viewer, `glb2html.py --zones`            |
| `default.json`                                         | `default.sample.json`              | `glb2html.py --default`                      | la coquille                                          |
| `regions.json`                                         | `regions.sample.json`              | `glb2html.py --register`, le viewer          | la page (`mapUrl`), la coquille, `glb2html.py --map` |
| `NOM.tiles.json`                                       | `region.tiles.sample.json`         | `glb2tiles.py`                               | la page, le viewer, `glb2html.py --tiles`            |
| `NOM.reglages.json`                                    | `region.reglages.sample.json`      | le viewer (« Enregistrer dans un fichier »)  | le viewer, `glb2html.py --settings`                  |
| `disposition.json`                                     | `disposition.sample.json`          | la page (Réglages, « Enregistrer »)          | la page (Réglages, « Charger »)                      |
| `presence_identities.json`                             | `presence_identities.sample.json`  | `presence_server.py`                         | `presence_server.py`                                 |
| `presence_bans.json`                                   | `presence_bans.sample.json`        | `presence_server.py` (commande `bannir`)     | `presence_server.py`                                 |
| fichier de `--history-file` (par exemple `chat.jsonl`) | `chat_history.sample.jsonl`        | `presence_server.py`                         | `presence_server.py`                                 |
| fichier de `--visits` (par exemple `visits.jsonl`)     | `visits.sample.jsonl`              | `presence_server.py`                         | `presence_server.py`                                 |
| `presence_visits_keys.json`                            | `presence_visits_keys.sample.json` | `presence_server.py` (commande `visits-key`) | `presence_server.py`                                 |
| `presence_creators.json`                               | `presence_creators.sample.json`    | à la main (§ 10.10)                             | `presence_server.py` (`--creators`)                  |

Deux autres fichiers ont **exactement le format** de `NOM.zones.json` :

- `zones.json`, les zones communes aux régions d'un dossier, lu quand une région n'a pas son propre `NOM.zones.json` (§ 11.12) ;
- `NOM.zones.bak.json`, la copie de sécurité que le viewer laisse quand il enregistre les zones dans le dossier de la région.

Dans les exemples, la région s'appelle `Region`. Pour une région « Atoll », on renomme `region.config.sample.json` en `Atoll.config.json` et on remplace `Region` par `Atoll` dans les valeurs qui le contiennent (`room`, `tiles`, les adresses). Les adresses des exemples sont écrites `ADRESSE` : il faut y mettre la sienne.

## 11.2 Comment lire les tableaux

- **Texte** : une valeur entre guillemets, par exemple `"door, porte"`.
- **Nombre** : sans guillemets, avec un point pour les décimales, par exemple `18.5`.
- **Oui / non** : `true` (oui) ou `false` (non), sans guillemets.
- **Liste** : des valeurs entre crochets, par exemple `[392, 68, -373]` pour une position x, y, z.
- **Objet** : des champs entre accolades, comme une fiche dans la fiche.
- **Couleur** : un nombre entier, qui est le code couleur habituel écrit en base 10. Le bleu de la mer `#3A9AD9` s'écrit `3840729`. Pour convertir dans PowerShell, taper `0x3A9AD9` donne `3840729`, et `'{0:X6}' -f 3840729` redonne `3A9AD9`. Les options `--sea-color` et `--sky-color` acceptent directement le code `3a9ad9`.
- **Option** : l'option de `glb2html.py` qui écrit ce champ. Un tiret « — » veut dire qu'aucune option ne le règle.

Les positions sont en mètres, dans le repère de la page : x vers l'est, y vers le haut, z vers le sud (le nord est la direction -z). Les angles (`yaw`) sont en radians : 1.57 fait un quart de tour, 3.14 un demi-tour.

## 11.3 `NOM.config.json` : les réglages de la page

`glb2html.py` l'écrit ; la page le relit à chaque ouverture, donc **F5 suffit** après une modification. On le change de préférence avec `glb2html.py --update -o NOM.html --shared-shell` suivi des options voulues : seuls les champs des options données changent, le reste est gardé, y compris un champ ajouté à la main. On peut aussi le modifier à la main ; une erreur de syntaxe (virgule oubliée, guillemet manquant) empêche alors la page de s'ouvrir.

**Mer et ciel**

| Champ            | Type          | Défaut    | Ce qu'il fait                                                                                | Option                 |
| ---------------- | ------------- | --------- | -------------------------------------------------------------------------------------------- | ---------------------- |
| `sea`            | oui / non     | `true`    | affiche la mer                                                                               | `--sea`, `--no-sea`    |
| `seaY`           | nombre        | `-50`     | hauteur de la mer en mètres (de -150 à 60)                                                   | `--sea-y`              |
| `seaColor`       | couleur       | `3840729` | couleur de la mer (`#3A9AD9`)                                                                | `--sea-color`          |
| `skyColor`       | couleur       | `8900331` | couleur du ciel et du brouillard (`#87CEEB`)                                                 | `--sky-color`          |
| `anim`           | oui / non     | `false`   | vagues animées ; sinon la mer est fixe                                                       | `--anim`, `--no-anim`  |
| `wave`           | nombre        | `0.5`     | hauteur des vagues (de 0 à 10)                                                               | `--wave`               |
| `seaSegments`    | nombre entier | `400`     | finesse de la surface de la mer (de 8 à 1000) ; ne compte qu'avec les vagues animées         | `--sea-segments`       |
| `seaSize`        | nombre        | `4000`    | largeur de la mer en mètres                                                                  | —                      |
| `hole`           | nombre        | `180`     | rayon en mètres de la **zone calme** autour de l'île, où les vagues s'effacent (de 30 à 600) | `--hole`               |
| `holeFade`       | nombre        | `60`      | largeur de la transition entre la zone calme et les vagues                                   | `--hole-fade`          |
| `holeX`, `holeZ` | nombre        | `0`       | centre de la zone calme                                                                      | `--hole-x`, `--hole-z` |

**Région et caméra de départ**

| Champ            | Type               | Défaut         | Ce qu'il fait                                                                                           | Option                      |
| ---------------- | ------------------ | -------------- | ------------------------------------------------------------------------------------------------------- | --------------------------- |
| `rotate`         | nombre entier      | `0`            | rotation de la région : 0, 90, 180 ou 270 degrés                                                        | `--rotate`                  |
| `target`         | liste de 3 nombres | `[0, 15, 0]`   | point regardé par la caméra à l'ouverture                                                               | `--target`                  |
| `targetExplicit` | oui / non          | `false`        | `true` quand `--target` a été donné : la page garde ce cadrage au lieu de partir de l'arrivée `default` | `--target`                  |
| `camDir`         | liste de 3 nombres | `[0, 0.25, 1]` | direction d'où regarde la caméra                                                                        | `--cam-dir`                 |
| `zoom`           | nombre             | `1`            | recul de la caméra (1 = cadrage automatique, 2 = deux fois plus loin)                                   | `--zoom`                    |
| `compass`        | oui / non          | `true`         | boussole en haut de la page                                                                             | `--compass`, `--no-compass` |
| `northDeg`       | nombre             | `0`            | décalage en degrés de la boussole, pour un modèle qui ne vient pas d'OpenSim                            | `--north`                   |

**Affichage**

| Champ           | Type      | Défaut             | Ce qu'il fait                                                                                                                                      | Option                    |
| --------------- | --------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| `retina`        | oui / non | `false`            | haute résolution (plus net, environ quatre fois plus lourd)                                                                                        | `--retina`, `--no-retina` |
| `light`         | oui / non | `false`            | la page s'ouvre en rendu léger tant que le visiteur n'a rien choisi (§ 7.45)                                                                         | `--light`, `--no-light`   |
| `foliageCutout` | nombre    | `0.12`             | seuil de transparence des feuillages (de 0 à 0.5) : plus haut, les bords des feuilles sont plus découpés                                           | `--foliage-cutout`        |
| `solidMaterials` | texte     | `""`               | matériaux rendus pleins (§ 6.13) : noms ou morceaux de noms séparés par des virgules, `=nom` pour un nom exact ; vide = rien ne change             | `--solid-materials`       |
| `names`         | oui / non | `false`            | affiche le nom du bâtiment (objet racine) et de l'élément visé (§ 7.61)                                                                                                                 | `--names`, `--no-names`   |
| `panel`         | oui / non | `true`             | bouton Réglages pour les visiteurs                                                                                                                 | `--panel`, `--no-panel`   |
| `libUrl`        | texte     | `""`               | dossier ou adresse de `lib` (three.js) quand il n'est pas à côté de la page ; `--update` l'aligne sur la ligne `const LIB` de la coquille (§ 6.4) | `--lib-url`               |
| `version`       | texte     | version de l'outil | version de `glb2html.py` qui a écrit le fichier ; `--update` la remplace ; `fabriquer_paquets.py` y écrit la version de la release dans les paquets                    | —                         |

**Promenade**

| Champ        | Type      | Défaut          | Ce qu'il fait                                                                                                                              | Option                |
| ------------ | --------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------- |
| `walk`       | oui / non | `true`          | mode promenade (touche F)                                                                                                                  | `--walk`, `--no-walk` |
| `fly`        | oui / non | `true`          | vol en promenade                                                                                                                           | `--fly`, `--no-fly`   |
| `eyeHeight`  | nombre    | `1.7`           | hauteur des yeux en mètres                                                                                                                 | `--eye-height`        |
| `walkSpeed`  | nombre    | `3.5`           | vitesse de marche en mètres par seconde (en courant : 2,2 fois plus)                                                                       | `--walk-speed`        |
| `walkIgnore` | texte     | `"door, porte"` | objets que l'on traverse, séparés par des virgules : `door` = tout nom qui commence par ce mot, `=mesh_346_5` = ce nom exact, `""` = aucun | `--walk-ignore`       |

**Visiteurs et chat**

| Champ         | Type      | Défaut                             | Ce qu'il fait                                                                                  | Option                        |
| ------------- | --------- | ---------------------------------- | ---------------------------------------------------------------------------------------------- | ----------------------------- |
| `presenceUrl` | texte     | `""`                               | adresse du serveur de présence (`ws://...` ou `wss://...`) ; vide = seul, sans avatars ni chat | `--presence-url`              |
| `room`        | texte     | nom de la page                     | salon de présence : les visiteurs d'un même salon se voient                                    | `--room`                      |
| `title`       | texte     | absent (le titre est le salon)     | titre de l'onglet du navigateur (60 caractères au plus), facultatif, coquille seulement         | `--title`                     |
| `spectate`    | oui / non | `true` si `presenceUrl` est rempli | voir les promeneurs depuis la vue globale                                                      | `--spectate`, `--no-spectate` |
| `chat`        | oui / non | `true`                             | chat entre visiteurs (il faut un serveur de présence)                                          | `--chat`, `--no-chat`         |
| `chatFade`    | nombre    | `0`                                | secondes avant que les messages et bulles disparaissent ; 0 = ils restent                      | `--chat-fade`                 |

**Zones**

| Champ          | Type      | Défaut     | Ce qu'il fait                                                                                                        | Option                              |
| -------------- | --------- | ---------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| `profile`      | texte     | `"public"` | `"public"` : les zones privées ne sont pas affichées ; `"private"` : toutes les zones le sont                        | `--profile`                         |
| `zones`        | liste     | `[]`       | toujours vide dans ce fichier : les zones sont dans `NOM.zones.json`                                                 | —                                   |
| `zonesLive`    | texte     | `""`       | toujours vide dans ce fichier (sert aux pages autonomes, `--zones-live`)                                             | `--zones-live`                      |
| `imageExts`    | texte     | `"jpg,jpeg,png,webp,gif,avif"` | extensions essayées, dans l'ordre, pour un nom d'image sans extension (§ 5.11) ; clé facultative, absente du fichier écrit par le générateur | —                                   |
| `mediaDir`     | texte     | `"medias"` | sous-dossier des images et des fichiers texte des zones `image` (§ 5.11) ; `""` = aucun ; clé facultative, absente du fichier écrit par le générateur | —                                   |
| `zoneMarker`   | texte     | `"dot"`    | repère des portails et zones libres : `"dot"` petit disque, `"range"` anneau au rayon réel de la zone, `"none"` rien | `--zone-marker`                     |
| `zoneCone`     | oui / non | `true`     | petit cône au-dessus des portails (touche T)                                                                         | `--zone-cone`, `--no-zone-cone`     |
| `showSpawns`   | oui / non | `false`    | dessine aussi les arrivées                                                                                           | `--show-spawns`, `--no-show-spawns` |
| `zoneInfoDist` | nombre    | `150`      | distance en mètres (de 5 à 500) jusqu'où les zones répondent au survol et au clic en promenade                       | `--zone-info-dist`                  |

**Carte des mondes**

| Champ    | Type  | Défaut | Ce qu'il fait                                                                     | Option                |
| -------- | ----- | ------ | --------------------------------------------------------------------------------- | --------------------- |
| `map`    | liste | `[]`   | carte intégrée à la page : mêmes fiches que `regions.json` (§ 11.6)               | `--map`, `--register` |
| `mapUrl` | texte | `""`   | adresse(s) de `regions.json` relues à chaque ouverture, séparées par des virgules | `--map-url`           |

**Région en tuiles** : ces six champs n'existent que pour une région découpée par `glb2tiles.py`. Pour une région faite d'un seul fichier `.glb`, il faut les **retirer** de l'exemple, sinon la page cherche des tuiles.

| Champ              | Type          | Défaut    | Ce qu'il fait                                                           | Option                 |
| ------------------ | ------------- | --------- | ----------------------------------------------------------------------- | ---------------------- |
| `tiles`            | texte         | —         | nom de l'index des tuiles, par exemple `"Region.tiles.json"`            | `--tiles`              |
| `tileRadius`       | nombre        | `150`     | rayon en mètres autour de l'avatar dans lequel les tuiles sont chargées | `--tile-radius`        |
| `tileMargin`       | nombre        | `60`      | marge en mètres au-delà de ce rayon avant qu'une tuile soit retirée     | `--tile-margin`        |
| `tileMaxMB`        | nombre        | `200`     | mégaoctets de tuiles chargées en même temps, au plus                    | `--tile-max-mb`        |
| `tileMaxTriangles` | nombre entier | `8000000` | triangles de tuiles chargées en même temps, au plus                     | `--tile-max-triangles` |
| `tileConcurrency`  | nombre entier | `4`       | téléchargements de tuiles en même temps                                 | `--tile-concurrency`   |

Les réglages du rendu léger choisis par un visiteur (résolution, images par seconde, vue d'ensemble seule, anticrénelage) sont gardés **par son navigateur**, pas dans ce fichier : la page ignore `pixelScale`, `fpsMax`, `ovOnly` ou `antialias` écrits ici.

## 11.4 `NOM.zones.json` : les zones

Une **liste** de zones, relue à chaque ouverture de la page. Chaque zone a les champs ci-dessous ; un champ absent prend sa valeur par défaut, et une valeur hors des limites est ramenée dans les limites.

Il existe **cinq sortes** de zones (champ `type`) : `"spawn"` (arrivée), `"portal"` (portail), `"url"` (lien web), `"ha"` (commande) et `"image"` (tableau sur un mur, § 5.11). « Privée », « liée à un objet » et « nom affiché » ne sont pas des sortes : ce sont des cases (`private`, `mesh`, `showName`) valables pour toutes les sortes.

| Champ         | Type      | Défaut        | Ce qu'il fait                                                                                                                                            |
| ------------- | --------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`          | texte     | `z1`, `z2`... | nom court et unique : lettres minuscules, chiffres, `-` et `_`, 40 caractères au plus. L'arrivée `default` est le point d'entrée de la région            |
| `type`        | texte     | `"portal"`    | `"spawn"`, `"portal"`, `"url"`, `"ha"` ou `"image"`                                                                                                                 |
| `label`       | texte     | `""`          | nom affiché (infobulle, panneau), 60 caractères au plus                                                                                                  |
| `x`, `y`, `z` | nombre    | `0`           | position en mètres                                                                                                                                       |
| `yaw`         | nombre    | `0`           | orientation en radians : sens du regard à l'arrivée, ou face du panneau                                                                                  |
| `shape`       | texte     | `"ring"`      | `"ring"` (anneau au sol) ou `"board"` (panneau sur un poteau)                                                                                            |
| `trigger`     | texte     | `"click"`     | portails seulement : `"click"` (clic ou E), `"enter"` (en marchant dedans) ou `"both"` (les deux). Les autres sortes sont toujours `"click"`             |
| `radius`      | nombre    | `2`           | rayon de la zone en mètres (de 0.5 à 50)                                                                                                                 |
| `w`, `h`      | nombre    | `2.4`, `1.2`  | largeur et hauteur du panneau en mètres ; pour `image` : 1,2 de large par défaut, hauteur 0 = d'après l'image                                                                                                                  |
| `target`      | texte     | `""`          | portail : adresse de la région d'arrivée, ou vide pour un point de la même région ; lien : adresse de la page web ; commande : adresse appelée ; image : nom du fichier ou adresse de l'image           |
| `link`        | texte     | `""`          | image seulement, facultatif : page ouverte au clic ou à E devant le tableau (adresse `http(s)` ou `hop://`, ou chemin relatif à la page ouverte, par exemple `galerie.html`) ; 600 caractères au plus ; la clé n'est écrite que si elle est remplie (§ 5.11) |
| `spawn`       | texte     | `""`          | portail : `id` de l'arrivée visée (vide = `default`)                                                                                                     |
| `confirm`     | oui / non | `false`       | demande une confirmation avant d'agir                                                                                                                    |
| `private`     | oui / non | `false`       | zone privée : absente des pages publiques (profil `public`)                                                                                              |
| `showName`    | oui / non | `false`       | écrit le `label` au-dessus de la zone en promenade                                                                                                       |
| `mesh`        | texte     | `""`          | zone **liée à un objet** du modèle : son nom, ou `nom#numéro` quand plusieurs objets portent ce nom ; l'objet devient cliquable. Jamais pour une arrivée |

L'exemple contient neuf zones, une de chaque cas :

| `id`              | Sorte    | Ce qu'elle montre                                                                              |
| ----------------- | -------- | ---------------------------------------------------------------------------------------------- |
| `default`         | arrivée  | point d'entrée de la région                                                                    |
| `gallery`         | arrivée  | seconde arrivée, visée par un portail                                                          |
| `to-gallery`      | portail  | vers un autre point de la même région (`target` vide, `spawn` = `gallery`), en marchant dedans |
| `to-other-region` | portail  | vers une autre région, panneau, clic ou marche, avec confirmation                              |
| `website`         | lien     | ouvre une page web, panneau                                                                    |
| `light-on`        | commande | appel d'une adresse (par exemple un webhook Home Assistant), privée, avec confirmation         |
| `door-info`       | lien     | liée à l'objet `Door#2` du modèle                                                              |
| `back-home`       | portail  | nom affiché au-dessus de la zone (`showName`)                                                  |
| `painting-1`      | image    | tableau sur un mur : fichier `paintings/painting-1.jpg`, hauteur d'après l'image               |

Dans une région en tuiles, une zone liée retrouve son objet grâce à l'étiquette `extras.ref` que `glb2tiles.py` écrit dans les objets des tuiles. Cette étiquette est dans les fichiers `.glb` des tuiles, **pas** dans `NOM.zones.json`.

## 11.5 `default.json` : la région par défaut

| Champ    | Type  | Défaut | Ce qu'il fait                                               | Option      |
| -------- | ----- | ------ | ----------------------------------------------------------- | ----------- |
| `region` | texte | —      | région ouverte quand l'adresse n'a pas de `?region=` (§ 11.12) | `--default` |

## 11.6 `regions.json` : la carte des mondes

Une **liste** de régions (forme simple), ou, depuis la v47, un **objet** avec un en-tête : `{"showUrl": false, "regions": [ ... ]}`. Les deux formes sont lues partout (carte `carte.html`, carte autonome, carte ouverte par M, coquille). Une fiche sans `name` ou sans `url` est ignorée.

| Champ de l'en-tête | Type    | Défaut  | Ce qu'il fait                                                                                                                                                             | Option |
| ------------------ | ------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| `showUrl`          | booléen | `false` | affiche l'adresse sous chaque tuile de la page carte ; la case de la page carte, une fois cochée ou décochée par le visiteur, l'emporte (choix retenu par son navigateur) | —      |
| `regions`          | liste   | —       | les fiches de régions (tableau suivant)                                                                                                                                   | —      |

`--register` et `--scan-sites` gardent l'en-tête et la forme du fichier (liste ou objet). Le viewer aussi depuis la v50 : « Importer regions.json » accepte les deux formes, « Exporter regions.json » rend la forme importée avec son en-tête, et chaque fiche garde tous ses champs (§ 9.13).

| Champ      | Type          | Défaut      | Ce qu'il fait                                                                                     | Option           |
| ---------- | ------------- | ----------- | ------------------------------------------------------------------------------------------------- | ---------------- |
| `id`       | texte         | tiré du nom | identifiant court, unique dans la carte                                                           | —                |
| `name`     | texte         | —           | nom affiché, 60 caractères au plus                                                                | `--region-name`  |
| `url`      | texte         | —           | adresse de la page : complète (`https://...`) ou relative (`index.html?region=Region`)            | `--region-url`   |
| `x`, `y`   | nombre entier | `0`         | place sur la grille, comme dans OpenSim (x vers l'est, y vers le nord)                            | `--region-xy`    |
| `spawn`    | texte         | `""`        | arrivée utilisée en venant de la carte (vide = `default`)                                         | `--region-spawn` |
| `presence` | texte         | `""`        | serveur de présence de cette région, s'il n'est pas celui de la page (pour compter les visiteurs) | —                |
| `room`     | texte         | `""`        | salon de présence de cette région                                                                 | `--room`         |
| `thumb`    | texte         | `""`        | vignette : image intégrée (`data:image/...`) ou adresse d'une image                               | `--thumb`        |

## 11.7 `NOM.tiles.json` : l'index des tuiles

`glb2tiles.py` l'écrit ; il ne se modifie **pas à la main**. La page n'en lit que quelques champs : `tiles` (pour chaque tuile `file`, `min`, `max`, `bytes`, `triangles`), `nodeRefs` et `overview.file`. Les autres servent au compte rendu.

| Champ            | Type            | Ce qu'il contient                                                                                                                                                                                                                                                                             |
| ---------------- | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `version`        | nombre entier   | version du format (1)                                                                                                                                                                                                                                                                         |
| `generator`      | texte           | outil et version qui ont écrit le fichier                                                                                                                                                                                                                                                     |
| `source`         | texte           | nom du `.glb` découpé                                                                                                                                                                                                                                                                         |
| `extent`         | objet           | boîte de toute la région : `min` et `max`, chacun x, y, z                                                                                                                                                                                                                                     |
| `params`         | objet           | réglages du découpage : `budgetMB`, `budgetTriangles`, `minCell`, `wholeWeightMB`, `wholeExtent`, `thresholdMB`, `thresholdTriangles`, `outlier` (options `--budget`, `--budget-triangles`, `--min`, `--whole-weight`, `--whole-extent`, `--threshold`, `--threshold-triangles`, `--outlier`) |
| `warnings`       | liste de textes | avertissements du découpage                                                                                                                                                                                                                                                                   |
| `roots`          | objet           | objets gardés entiers (`whole`) et répartis (`split`)                                                                                                                                                                                                                                         |
| `duplication`    | nombre          | géométrie de toutes les tuiles divisée par celle du modèle (1 = rien en double)                                                                                                                                                                                                               |
| `nodeRefs`       | nombre          | 1 si les objets portent `extras.ref` (zones liées possibles), 0 avec `--no-refs`                                                                                                                                                                                                              |
| `replacedImages` | objet           | images illisibles remplacées par du gris : `distinct`, `occurrences`, `grey`                                                                                                                                                                                                                  |
| `tiles`          | liste           | une fiche par tuile (ci-dessous)                                                                                                                                                                                                                                                              |
| `excluded`       | objet           | seulement avec `--exclude` : motifs, limites, nombre d'objets retirés, triangles et octets gagnés, noms les plus fréquents                                                                                                                                                                    |
| `overview`       | objet           | seulement avec la vue d'ensemble : `file` (le `.glb`), poids, triangles, objets gardés et omis, durée, `params` (`budgetMB`, `budgetTriangles`, `minExtent`, `maxExtent`, `resolution`, `terrainStep`)                                                                                        |

Chaque fiche de `tiles` :

| Champ                         | Type               | Ce qu'il contient                               |
| ----------------------------- | ------------------ | ----------------------------------------------- |
| `file`                        | texte              | chemin du `.glb` de la tuile, relatif à l'index |
| `level`, `i`, `j`             | nombre entier      | niveau et place de la tuile dans la grille      |
| `min`, `max`                  | liste de 3 nombres | boîte de la tuile                               |
| `instances`                   | nombre entier      | nombre d'objets dans la tuile                   |
| `triangles`                   | nombre entier      | triangles de la tuile                           |
| `bytes`                       | nombre entier      | poids du fichier                                |
| `geometryBytes`, `imageBytes` | nombre entier      | dont géométrie, dont images                     |
| `replacedImages`              | nombre entier      | images remplacées par du gris dans cette tuile  |

## 11.8 `NOM.reglages.json` : l'état de travail du viewer

Écrit par le bouton « Enregistrer dans un fichier » du viewer, relu par « Charger un fichier » et par `glb2html.py --settings`. Contrairement à `NOM.config.json`, il est **imbriqué** (§ 11.12).

| Champ            | Type          | Ce qu'il contient                                                                                                             |
| ---------------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `v`              | nombre entier | version du format : toujours `1`                                                                                              |
| `file`           | texte         | nom du `.glb` ouvert dans le viewer                                                                                           |
| `saved`          | texte         | date et heure de l'enregistrement                                                                                             |
| `cfg`            | objet         | les réglages : mêmes noms et même sens que dans `NOM.config.json` (§ 11.3), plus cinq réglages propres au viewer (ci-dessous) |
| `zones`          | liste         | toutes les zones, privées comprises (format du § 11.4)                                                                        |
| `camera`         | objet         | `camDir`, `target`, `zoom` : le cadrage choisi dans le viewer                                                                 |
| `profile`        | texte         | `"public"` ou `"private"` (menu « Profil d'export »)                                                                          |
| `thisReg`        | objet         | fiche de cette région pour la carte : `name`, `url`, `x`, `y`, `spawn`, `thumb` (§ 11.6)                                      |
| `cmd`            | objet         | champs du récapitulatif de commande : `script`, `glb`, `dest`, `mapPage`                                                      |
| `targetExplicit` | oui / non     | la cible de la caméra a été déplacée à la main                                                                                |

Les cinq réglages de `cfg` propres au viewer : `pixelScale`, `fpsMax` et `ovOnly` (rendu léger, essais dans le viewer), `guide` (guide de la zone calme affiché dans le viewer) et `ignoreViz` (objets traversés montrés en fil de fer). `--settings` ne les reprend pas.

## 11.9 `disposition.json` : la place des fenêtres

Écrit par Réglages, « Enregistrer » (section « Disposition des fenêtres »), relu par « Charger » (§ 7.44).

| Champ    | Type          | Ce qu'il contient                                                                                                                                                                                                                                                                                                     |
| -------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app`    | texte         | toujours `"web3d-layout"` : un autre fichier est refusé                                                                                                                                                                                                                                                               |
| `v`      | nombre entier | version du format : `1`                                                                                                                                                                                                                                                                                               |
| `layout` | objet         | `wins` : pour chaque fenêtre (`H` aide, `I` informations / état, `L` arrivées), `pile` (`"L"` pile de gauche, `"R"` pile de droite, `"F"` libre), `home` (`"L"` ou `"R"`, la pile où la fenêtre revient au double-clic), et pour une fenêtre libre `x`, `y` en pixels ; `order` : ordre des fenêtres dans chaque pile |
| `ls`     | objet         | état des fenêtres : `glb2html_help`, `glb2html_state`, `glb2html_spawn` (`"1"` affichée, `"0"` masquée), `glb2html_helpFold`, `glb2html_stateFold`, `glb2html_spawnFold` (`"1"` repliée), `glb2html_helpW`, `glb2html_stateW`, `glb2html_spawnW` (largeur en pixels)                                                  |

## 11.10 Fichiers du serveur de présence

Le serveur les écrit lui-même ; on ne les modifie à la main que serveur arrêté. Les valeurs « hachées » sont des empreintes : on ne peut pas retrouver la clé ou l'adresse IP d'origine, ce qui protège les visiteurs. Les empreintes des exemples sont fabriquées et ne correspondent à personne.

**`presence_identities.json`** (option `--identities`) : les pseudos réservés (la commande de console `oublier <pseudo>` en libère un sans toucher au fichier, § 10.19).

| Champ   | Type  | Ce qu'il contient                                                                                                                                                                                                            |
| ------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `salt`  | texte | « sel » secret tiré au hasard au premier démarrage, mélangé aux clés avant de les hacher. Le changer libère tous les pseudos                                                                                                 |
| `names` | objet | pour chaque pseudo simplifié (minuscules, sans accents ni espaces), l'empreinte de la clé du navigateur qui le possède                                                                                                       |
| `users` | objet | pour chaque empreinte : `name` (pseudo tel qu'écrit), `key` (pseudo simplifié), `first` et `last` (première et dernière venue, en secondes depuis 1970). Un pseudo inutilisé depuis `--name-ttl-days` jours (365) est libéré |

**`presence_bans.json`** (option `--bans`) : une liste de bannissements.

| Champ    | Type   | Ce qu'il contient                                                                                                                       |
| -------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| `key`    | texte  | empreinte de la clé du navigateur banni (vide pour un visiteur sans clé)                                                                |
| `ip`     | texte  | empreinte de son adresse IP                                                                                                             |
| `until`  | nombre | fin du bannissement en secondes depuis 1970 ; `0` = définitif. Un bannissement terminé est retiré du fichier à la vérification suivante |
| `name`   | texte  | pseudo au moment du bannissement                                                                                                        |
| `reason` | texte  | raison donnée                                                                                                                           |
| `added`  | nombre | date du bannissement en secondes depuis 1970                                                                                            |

**Historique du chat** (option `--history-file`) : ce n'est pas un fichier JSON d'un seul bloc, mais **un message par ligne**, chaque ligne étant un petit JSON. Jamais d'adresse IP.

| Champ  | Type          | Ce qu'il contient                                                           |
| ------ | ------------- | --------------------------------------------------------------------------- |
| `n`    | nombre entier | numéro du message                                                           |
| `t`    | nombre entier | heure en secondes depuis 1970 (c'est elle qui compte pour `--history-days`) |
| `d`    | texte         | la même heure lisible (jj/mm/aaaa hh:mm:ss)                                 |
| `room` | texte         | salon                                                                       |
| `name` | texte         | pseudo                                                                      |
| `text` | texte         | message                                                                     |

Les messages plus vieux que `--history-days` jours (30 par défaut) sont retirés au démarrage ; avec `--history-days 0`, rien n'est retiré.

**Journal des visites** (option `--visits`, v48) : comme l'historique, **une visite par ligne**, chaque ligne étant un petit JSON. Jamais d'adresse IP.

| Champ   | Type          | Ce qu'il contient                                                                                                                                                |
| ------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `room`  | texte         | salon                                                                                                                                                            |
| `start` | nombre entier | arrivée en secondes depuis 1970 (c'est elle qui compte pour `--visits-days`)                                                                                     |
| `dur`   | nombre entier | durée de la connexion en secondes                                                                                                                                |
| `walk`  | nombre entier | secondes passées en promenade                                                                                                                                    |
| `v`     | texte         | empreinte du navigateur (10 caractères), différente de la clé du journal `presence.log` : sert à compter les visiteurs distincts et à fusionner les reconnexions |
| `name`  | texte         | pseudo du promeneur, seulement avec `--visits-names`                                                                                                             |

Les visites plus vieilles que `--visits-days` jours (365 par défaut) sont retirées au démarrage puis toutes les 6 heures, avec les lignes illisibles ; avec `--visits-days 0`, rien n'est retiré.

**`presence_visits_keys.json`** (option `--visits-keys`, v48) : les clés du journal des visites, écrites par la commande `visits-key`.

| Champ   | Type  | Ce qu'il contient                                                                                                                                                                                                           |
| ------- | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `rooms` | objet | pour chaque salon : `salt` (sel tiré au hasard), `hash` (empreinte SHA-256 du sel suivi de la clé en majuscules, sans tirets ni espaces), `added` (création, en secondes depuis 1970). La clé elle-même n'est jamais écrite |

**`presence_creators.json`** (option `--creators`, v51) : les créateurs accueillis, écrit à la main et relu sans relancer le serveur (§ 10.10). Un objet `{"creators": [...]}` ; pour chaque créateur :

| Champ        | Type            | Ce qu'il contient                                                                                                                                            |
| ------------ | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `id`         | texte           | identifiant unique : lettres, chiffres, `-` et `_`, 32 au plus                                                                                               |
| `prefix`     | texte           | préfixe de ses salons, sans point ; absent = `id` ; `""` = l'hôte, qui garde tous les salons n'appartenant à aucun créateur (une seule entrée)               |
| `origins`    | liste de textes | origines de ses pages (`https://alice.example`, `null` pour une page ouverte depuis le disque et pour le viewer, écrit entre guillemets ; sans guillemets, il est ignoré avec un avertissement) ; une origine n'appartient qu'à un créateur |
| `maxWalkers` | nombre entier   | promeneurs au plus sur tous ses salons ; `0` ou absent = seulement les limites générales                                                                     |
| `maxRooms`   | nombre entier   | salons ouverts en même temps au plus ; `0` ou absent = sans limite propre                                                                                    |
| `off`        | booléen         | `true` : suspendu, ses nouvelles connexions sont refusées                                                                                                    |
| `note`       | texte           | note libre de l'hôte, ignorée par le serveur                                                                                                                 |

## 11.11 Noms en anglais depuis la v43

Pour que tous les noms soient dans la même langue, la v43 a mis en anglais les derniers noms français : options des outils, valeurs dans les fichiers JSON et paramètres d'adresse. **Les anciens noms restent acceptés** : les commandes, les fichiers et les liens déjà écrits continuent de marcher. Un ancien nom est remplacé par le nouveau à la lecture ; quand un outil réécrit un fichier, il écrit le nouveau. `--update` garde tel quel un champ que l'on ne change pas : un ancien `tileMaxMo` reste donc dans `NOM.config.json`, et la page le lit toujours.

| Où                                     | Ancien nom                                                         | Nouveau nom                                                    |
| -------------------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------- |
| `glb2html.py`                          | `--maj`                                                            | `--update`                                                     |
| `glb2html.py`                          | `--tile-max-mo`, `--tile-max-tri`                                  | `--tile-max-mb`, `--tile-max-triangles`                        |
| `glb2html.py`                          | `--zone-marker discret`, `portee`, `aucun`                         | `--zone-marker dot`, `range`, `none`                           |
| `glb2html.py`                          | `--profile perso`                                                  | `--profile private`                                            |
| `glb2tiles.py`                         | `--budget-tri`, `--ov-budget-tri`                                  | `--budget-triangles`, `--ov-budget-triangles`                  |
| `glb2tiles.py`                         | `--entier-poids`, `--entier-etendue`                               | `--whole-weight`, `--whole-extent`                             |
| `glb2tiles.py`                         | `--seuil`, `--seuil-tri`, `--aberrant`                             | `--threshold`, `--threshold-triangles`, `--outlier`            |
| `glb2tiles.py`                         | `--exclure`, `--exclure-max-tri`, `--exclure-max-meshes`           | `--exclude`, `--exclude-max-triangles`, `--exclude-max-meshes` |
| `glb2tiles.py`                         | `--sans-references`, `--sans-vue-ensemble`, `--vue-ensemble-seule` | `--no-refs`, `--no-overview`, `--overview-only`                |
| `glb2tiles.py`                         | `--ov-seuil`, `--ov-seuil-max`, `--ov-terrain-pas`                 | `--ov-threshold`, `--ov-threshold-max`, `--ov-terrain-step`    |
| `glb2tiles.py`                         | `--bloc`, `--forcer`, `--sortie`                                   | `--block`, `--force`, `--output`                               |
| `oar2glb.py`                           | `--reperes`, `--terrain-seul`, `--sortie`                          | `--markers`, `--terrain-only`, `--output`                      |
| `oar2glb.py`                           | `--terrain oui`, `--terrain non`                                   | `--terrain yes`, `--terrain no`                                |
| `glb-stats.py`                         | `--bloc`, `--sortie`                                               | `--block`, `--output`                                          |
| `extraire_batiments.py` (1.6.3)        | `--filtre`, `--min-parties`, `--boite`                             | `--filter`, `--min-parts`, `--box`                             |
| `extraire_batiments.py` (1.6.3)        | `--voisin`, `--rayon`, `--rayon-nom`, `--parties-voisin`           | `--neighbor`, `--radius`, `--name-radius`, `--neighbor-parts`  |
| `extraire_batiments.py` (1.6.3)        | `--groupe`, `--nom`, `--tous`, `--exclure`, `--limite`             | `--group`, `--name`, `--all`, `--exclude`, `--limit`           |
| `extraire_batiments.py` (1.6.3)        | `--simuler`, `--oui`, `--fusionner`, `--sol`                       | `--dry-run`, `--yes`, `--merge`, `--ground`                    |
| `extraire_batiments.py` (1.6.3)        | `--sortie`, `--sans-cache`, `--vider-cache`                        | `--output`, `--no-cache`, `--clear-cache`                      |
| `iar2oar.py` (1.6.4)                   | `--liste`, `--filtre`, `--sans-imbriques`, `--marge`, `--sortie`   | `--list`, `--filter`, `--no-nested`, `--margin`, `--output`    |
| `gen_reference.py` (v44)               | `--outils`, `--sortie`, `--verifier`                               | `--tools`, `--output`, `--check`                               |
| `verif_trad.py` (v44)                  | `--glossaire`                                                      | `--glossary`                                                   |
| `NOM.config.json`                      | `tileMaxMo`, `tileMaxTri`                                          | `tileMaxMB`, `tileMaxTriangles`                                |
| `NOM.config.json`, `NOM.reglages.json` | `zoneMarker` : `discret`, `portee`, `aucun`                        | `dot`, `range`, `none`                                         |
| `NOM.config.json`, `NOM.reglages.json` | `profile` : `perso`                                                | `private`                                                      |
| `NOM.tiles.json`                       | `budgetMo`, `wholeWeightMo`, `thresholdMo`                         | `budgetMB`, `wholeWeightMB`, `thresholdMB`                     |
| adresse de la page                     | `?rayon=`                                                          | `?radius=`                                                     |
| adresse du viewer                      | `?tuiles=`                                                         | `?tiles=`                                                      |

Les deux outils de développement (`gen_reference.py`, `verif_trad.py`) ont suivi en v44, et les messages de `--update` commencent par `[update]`. Restent tels quels : `--analyse` (aussi de l'anglais britannique) et les valeurs qui sont des noms d'objets, comme `door, porte`. Dans l'aide des outils, les noms d'exemple des valeurs sont aussi en anglais (`FILE`, `PATH`, `NAME`, `DEGREES`, `SHELL.html`). L'historique (`CHANGELOG.fr.md`, `HISTORIQUE.md`) garde les noms de l'époque.

## 11.12 Fichiers JSON d'une région modulaire

Pour une page `Region.html` produite par `--modular` (ou par « Exporter la structure modulaire (.zip) » du viewer), le dossier contient :

Ces fichiers sont ceux d'une région à coquille propre (`--modular`). Pour plusieurs régions dans un même dossier avec **une seule** coquille, voir « Coquille unique pour plusieurs régions » plus bas.

| Fichier              | Rôle                                                                                    | Relu à chaque F5 |
| -------------------- | --------------------------------------------------------------------------------------- | ---------------- |
| `Region.html`        | coquille identique pour toutes les régions, elle déduit ses fichiers de son nom         | non              |
| `Region.glb`         | le modèle                                                                               | non              |
| `Region.config.json` | réglages de **rendu de la page** (voir plus bas)                                        | oui              |
| `Region.zones.json`  | zones, portails, arrivées                                                               | oui              |
| `zones.json`         | zones de secours, communes aux pages du dossier qui n'ont pas leur propre `.zones.json` | oui              |
| `lib/three-0.160.0/` | three.js, Draco, Meshopt, partagés par toutes les pages du dossier                      | non              |

### 11.12.1 Quel fichier de zones est lu

Dans l'ordre, et on s'arrête au premier qui donne une liste JSON valide :

1. `Region.zones.json`
2. `zones.json` du même dossier, **seulement si** le premier est absent, inaccessible (erreur HTTP) ou n'est pas une liste
3. sinon : aucune zone

Il n'y a **pas de fusion** : dès que `Region.zones.json` est lu, `zones.json` est ignoré. Un `zones.json` posé à côté d'une région qui a déjà son `.zones.json` n'a donc aucun effet.

Les zones marquées **privées** sont retirées à la lecture, dans l'un comme dans l'autre fichier, sauf si `profile` vaut `private` dans `Region.config.json`.

### 11.12.2 Region.config.json : le rendu de la page, pas le viewer

C'est le dictionnaire de réglages que la page lit au démarrage (le même que celui intégré dans une page autonome). Il est **à plat**. La liste complète de ses champs, avec leur type, leur valeur par défaut, leur rôle et l'option qui les règle, est au **§ 11.3** ; un exemple complet est dans `docs/samples/region.config.sample.json`.

`zones` y est **toujours vide** (`[]`) et `zonesLive` toujours vide : en modulaire, les zones sont uniquement dans `Region.zones.json`.

Le viewer ne lit jamais ce fichier : il travaille avec son propre fichier de réglages (ci-dessous).

### 11.12.3 `.reglages.json` et `.config.json` n'ont pas la même structure

`<nom>.reglages.json` est l'état de travail du viewer (« Enregistrer dans un fichier »). Il est **imbriqué** :

```
{ v, file, saved,
  cfg:     { rotate, hole, holeFade, ..., mapUrl, guide, ignoreViz },
  camera:  { camDir, target, zoom },
  zones:   [ ...toutes les zones, privées comprises ],
  profile, thisReg: { fiche de cette région pour la carte },
  cmd:     { script, glb, dest, mapPage } }
```

|              | `<nom>.reglages.json` (viewer)                 | `<page>.config.json` (page)              |
| ------------ | ---------------------------------------------- | ---------------------------------------- |
| Structure    | imbriquée (`cfg`, `camera`, ...)               | à plat                                   |
| Caméra       | sous-objet `camera`                            | à la racine (`camDir`, `target`, `zoom`) |
| Zones        | toutes, privées comprises                      | toujours vide                            |
| Carte        | seulement la fiche de cette région (`thisReg`) | carte complète résolue (`map`)           |
| Propre à lui | `guide`, `ignoreViz`, `cmd`, `thisReg`         | `seaSize`, `version`                     |
| Écrit par    | le viewer                                      | `glb2html.py`                            |
| Lu par       | le viewer, `glb2html.py --settings`            | la page exportée                         |

La conversion ne va que dans un sens :

```
<nom>.reglages.json  ->  glb2html.py --settings  ->  <page>.config.json + <page>.zones.json
```

Un `.config.json` ne peut pas être donné à `--settings` (le script cherche la clé `cfg` et refuse le fichier), ni rechargé dans le viewer (« fichier de réglages non reconnu »). Pour garder ses réglages, il faut donc conserver le `.reglages.json` : le `.config.json` n'en est qu'un produit dérivé.

### 11.12.4 Quel fichier modifier, et ce qui l'écrase

| Je veux changer...                    | Je modifie / je lance                                                | Ce qui peut l'écraser ensuite                                               |
| ------------------------------------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| un réglage de rendu (vagues, ciel...) | `--config-only` (voir ci-dessous), ou `Region.config.json` à la main | tout nouveau `--modular` ou `--config-only` réécrit `Region.config.json`    |
| une zone                              | `Region.zones.json` à la main, ou **Exporter zones (.json)** (§ 6.16)  | `--modular` avec `--zones` ou `--settings` ; `--config-only` avec `--zones` |
| l'état de travail du viewer           | **Enregistrer dans un fichier**                                      | rien (c'est la source)                                                      |

Sans `--zones` ni `--settings`, un `Region.zones.json` déjà présent (modifié à la main, par exemple) n'est pas écrasé. Dès qu'une source de zones est donnée, il est réécrit.

Changer un réglage sans toucher au `.glb`, à la coquille ni aux zones :

```
python glb2html.py --settings "Region-final.glb" --config-only --wave 2 -o "Region.html"
```

Les options de la ligne de commande l'emportent sur le `.reglages.json`. Les visiteurs voient le changement à leur prochain rechargement.
