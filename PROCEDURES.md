# Que faire pour… (procédures pas à pas)

*Écrit le 23/10/2026 pour la version v35. Les commandes sont en PowerShell, sur une seule ligne, avec les chemins de ta machine. La liste complète des options est dans `REFERENCE_OPTIONS.md` ; le détail des zones, touches et réglages est dans `MODE_EMPLOI.md`.*

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
5. **Poser les zones** (portails, arrivées, panneaux) dans `glb-viewer.html` : voir `MODE_EMPLOI.md` §§ 3 à 12. En fin de travail, le viewer exporte `MaRegion.zones.json` : copie-le dans le dossier de la page, puis F5.

## 2. D'un OAR à une page web, région lourde (tuiles)

Cas de la 4X4 : un GLB de 1,2 Go ne tient pas d'un bloc dans le navigateur. Les tuiles chargent autour de l'avatar et déchargent le reste ; la vue d'ensemble montre toute la région de loin.

1. **Convertir l'OAR** comme au 1.1. Ça peut durer plusieurs heures et plusieurs dizaines de Go de mémoire (4 h 20 et 45 Go pour la 4X4). Si convoar plante dans la lecture des textures JPEG 2000, relance avec `--reencode` (voir `MODE_EMPLOI.md` § 15 : à n'utiliser qu'en dernier recours).
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
3. Recharger la page avec Ctrl+F5. La ligne du bas du panneau d'aide donne la version affichée (par exemple « glb2html v35 ») : si elle est ancienne, la mise à jour n'a pas eu lieu.
4. Relancer le serveur de présence **seulement** si la session le demande (procédure 6).
5. Le découpage en tuiles n'est à refaire que si la session le dit, par exemple pour de nouvelles informations dans les tuiles.

## 5. Poser et modifier des zones

| Besoin | Où |
|---|---|
| Poser portail, arrivée, panneau, lien | viewer, `MODE_EMPLOI.md` §§ 3 à 8 |
| Arrivée utilisée à l'ouverture sans lien | une arrivée nommée `default` (§ 4) ; `--target` explicite garde le cadrage |
| Portail vers une autre région | `MODE_EMPLOI.md` § 6 |
| Zone liée à un objet du modèle | `MODE_EMPLOI.md` § 9 (en tuiles : § 17 ter) |
| Zone privée (visible seulement avec le profil « perso ») | `MODE_EMPLOI.md` § 10 |

Les zones d'une région en tuiles s'écrivent dans le repère d'origine du modèle (aucun recentrage). Le viewer en mode tuiles produit ces coordonnées directement ; ne reporte pas à la main des coordonnées d'un autre GLB.

## 6. Serveur de présence (positions, chat, modération)

1. **Installer** une fois : `pip install websockets`
2. **Lancer** (le journal relatif est écrit dans le dossier du script ; `--log-ip raw` écrit les adresses IP en clair, `--log-days` limite la conservation) :
   `python "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\presence_server.py" --log presence.log --log-days 30 --log-ip raw`
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
| Nouvelle version du serveur de présence | arrêter et relancer `presence_server.py` | F5 |
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
