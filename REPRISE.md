# Reprise du projet Web 3d

*État au 23/10/2026, version v37. À lire après `REGLES.md` (qui est dans les fichiers du Projet, pas dans le dépôt). Ce fichier est mis à jour et commité à la fin de chaque lot. Il ne contient ni adresse IP ni nom d'hôte.*

## 1. Ce qu'est ce projet

Une région OpenSim (sauvegarde `.oar`) devient une **page web 3D** où l'on se promène : conversion en glTF (`.glb`), chargement par tuiles pour les régions énormes, avatars des autres visiteurs, chat, portails et zones. Rien à installer pour les visiteurs. Dépôt public : `github.com/Klaatou/Web_3d` (licence MIT). Le propriétaire est JJ ; il travaille sous Windows (PowerShell, clavier AZERTY) et son public visé est la communauté OpenSim, majoritairement anglophone.

## 2. État du dépôt

- **`main` = v37** (commit `cd01be1`, étiquette `v37`, fichier `VERSION` : `v37 (23/10/2026)`). Étiquettes `v14` à `v37`.
- Les sessions cloud sont **terminées** (crédit épuisé). Tout se fait désormais dans le chat, par patchs (voir `REGLES.md`).
- Région de référence de JJ : la « 4X4 » (`OAR-Free_House_Gallery_I(4X4)-terrain`), 1 024 x 1 024 m, 106 tuiles et une vue d'ensemble, publiée avec présence et chat. Options de sa page : mer à 18,5 m (`--sea-y 18.5`), cible de départ `--target 392,68,-373`, `default.json` posé avec `--maj --default`.
- **Pas encore fait** : voir la section 6.

## 3. Architecture (détail dans `CLAUDE.md`)

| Élément | Rôle |
|---|---|
| `src/core.js` | noyau JavaScript commun : collisions, promenade, avatars, zones, carte, chat |
| `src/template.html` | page exportée (aide, état, réglages, chat) |
| `src/viewer_tpl.html` | viewer / éditeur de zones (`glb-viewer.html`) |
| `src/gen_tpl.py` | devient `dist/glb2html.py` : fabrique la page, `--maj`, `--register`, `--map-page` |
| `src/presence_server.py` | serveur WebSocket de présence et de chat (dépendance `websockets`) |
| `tools/glb2tiles.py` | découpe un GLB énorme en tuiles + `X.overview.glb` |
| `tools/oar2glb.py` | convertit un OAR en GLB, refait le terrain complet |
| `src/i18n/fr.json`, `en.json`, `src/i18n.js`, `src/i18n_py.py` | tous les textes (page, viewer, outils) en français et en anglais |
| `build.py` | assemble tout dans `dist/` (**jamais éditer `dist/`**) |
| `gen_reference.py` | écrit `REFERENCE_OPTIONS.md` (bilingue) depuis les outils |
| `tests/` | une vingtaine de suites (Chromium sans tête, vrai `presence_server.py`) |
| Documents | `MODE_EMPLOI.md`, `PROCEDURES.md`, `HISTORIQUE.md`, `CHANGELOG.md`, `CLAUDE.md`, `README.md`, `README.en.md`, `REFERENCE_OPTIONS.md` |

Le dossier des outils fabriqués est `dist\` ; le dépôt local est `P:\_OpenSim\SL&OS\Web_3d\web_3d` ; les régions en tuiles sont dans `P:\_OpenSim\SL&OS\Web_3d\tuiles`.

## 4. Commandes de tous les jours (PowerShell, une ligne)

- Fabriquer : `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d"; python build.py`
- Mettre à jour une région après une nouvelle version (garde config et zones) : `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --maj -o "P:\_OpenSim\SL&OS\Web_3d\tuiles\OAR-Free_House_Gallery_I(4X4)-terrain.html" --shared-shell`
- Serveur de présence de JJ (journaux jamais effacés) : `python ".\presence_server.py" --log presence.log --log-ip raw --log-days 0 --history-file chat.jsonl --history-days 0`
- Servir une région pour l'essayer : `cd "P:\_OpenSim\SL&OS\Web_3d\tuiles"; python -m http.server 8000`, puis `http://localhost:8000/index.html?region=NOM`.
- Fusion d'une branche et étiquette : `git checkout main; git pull; git fetch; git merge origin/BRANCHE -m "Fusion vNN"; python build.py; git push; git tag vNN HASH; git push origin vNN`
- Tests dans le bac à sable : `npm pack three@0.160.0` (jsDelivr est refusé), extraire, `python build.py --vendor DOSSIER_package`, puis `THREE_DIR=DOSSIER_package`, `CHROMIUM=` l'exécutable si besoin, `WEB3D_LANG=fr` et locale `fr-FR` pour les tests de navigateur ; `pip install playwright websockets`. Les procédures complètes sont dans `PROCEDURES.md`, la liste de toutes les options dans `REFERENCE_OPTIONS.md`.

## 5. Décisions de conception arrêtées (ne pas rediscuter sans demande de JJ)

**Touches** (même lettre sur AZERTY et QWERTY sauf la marche ; **M se reconnaît par le caractère imprimé**, pas par la position) :

| Action | Touche |
|---|---|
| Entrer et sortir de la promenade | F, P (dans le viewer, P pose une zone ; on en sort avec F ou Maj+P) |
| Marcher | codes physiques W A S D (donc Z Q S D sur AZERTY), flèches |
| Courir | Maj, ou double appui rapide (moins de 300 ms) sur avancer ou reculer |
| Sauter | Espace |
| Voler / atterrir | Début, bouton « Voler / Atterrir », ou Page Haut maintenu plus de 0,4 s au sol |
| Monter, descendre en vol | Page Haut ou Espace maintenu, Page Bas ou C ; atterrissage en descendant jusqu'au sol |
| Action d'une zone proche | E (et clic) |
| Vue : subjective, 3e personne, caméra libre | V ; M bascule subjective et 3e personne en promenade (hors promenade, M ouvre la carte) ; Ctrl+M carte partout |
| Caméra | molette (distance), Alt+glisser (orbite), Fin (derrière l'avatar) |
| Chat | Entrée ouvre et envoie, Échap ferme ; les flèches marchent pendant la saisie |
| Souris | Échap libère, G ou bouton « Capturer la souris » reprend |
| Retour à l'arrivée | R |
| Fenêtres et repères | H aide, I informations / état, O réglages, T cônes de portail |

**Comportements**
- Une arrivée nommée `default` sert de point d'entrée à l'ouverture sans lien ; `--target` explicite garde le cadrage. `#spawn=NOM` ou `#pos=x,y,z,yaw` : arrivée demandée.
- **Arrivée occupée** : le nouvel arrivant est décalé (1,5 m environ de l'occupant) et tourné vers lui ; jamais quelqu'un qui marche.
- **Région par défaut** (adresse sans `?region=`) : `X.config.json` du nom de la page, puis `default.json`, puis la première entrée relative de `regions.json`, sinon message d'erreur. `?region=` accepte `nom` ou `dossier/nom`, jamais `..`, `:`, `\`, `?`, `#`.
- **Paramètres de l'adresse** : séparés par `&` ou `#` (fonction `hashParams`), langue `#lang=en`, pseudo `#name=`.
- **Zones d'une région en tuiles** : repère du modèle d'origine, sans recentrage ; zones liées à un objet par `extras.ref`. Fichiers `X.zones.json`, `regions.json`, `*.html`, journaux : jamais dans le dépôt (`.gitignore`).
- **Clignotement du pseudo cité** : sans limite de durée, jusqu'à la première action (touche, clic, mouvement), uniquement sur la page du visiteur cité. Le compteur « (N) » du titre se remet à zéro à l'ouverture du chat (comportement voulu par JJ, **à documenter dans le manuel**).
- **Langue** : tout texte visible passe par `tr()` ou `data-i18n*`, jamais de français en dur ; ajouter une langue = ajouter un fichier `src/i18n/xx.json`. Réglage « Langue / Language » (Auto, Français, English).
- **Sons** : réglage général (volume), citation, arrivée, départ ; les promeneurs seulement, jamais la liste initiale.
- **Boussole** : le nord est la direction -Z du modèle (z = -y d'OpenSim), décalée par `rotate` et `--north` ; case dans les réglages.
- **Chat et serveur** : historique de 200 messages par défaut, `--history-file` conserve entre deux relances (jamais d'adresse IP), `--log-days 0` ne supprime aucun journal.
- **Options de fabrication** : `--maj` ne ressaisit rien et garde config et zones ; `--default` écrit `default.json` ; `--lib-url` place `lib` ailleurs ; `--zone-info-dist` (150 m par défaut) règle la distance des infobulles et des cônes.
- **Interface** : jamais d'information portée par la seule couleur.

## 6. À faire (dans l'ordre)

1. **`.gitignore`** : JJ ajoute à la main `REGLES.md` et `_bak/` (le fichier existe, il se termine par un saut de ligne). **Ne pas** ajouter `REPRISE.md`.
2. **Réorganisation des documents** (un patch testé, avec `git mv`, qui met à jour les références, une dizaine de fichiers : `gen_reference.py`, `src/i18n.js`, `src/core.js`, `src/gen_tpl.py`, `tools/oar2glb.py`, `README`, `PROCEDURES`, `CLAUDE`, `CHANGELOG`, `fr.json`, `en.json`) :
   - `README.md` devient la version anglaise (page d'accueil GitHub), `README.fr.md` la française, avec une ligne `English | Français` en tête de chacun ;
   - `docs/fr/MANUEL.md` (ex `MODE_EMPLOI.md`), `docs/fr/PROCEDURES.md`, `docs/fr/HISTORIQUE.md` ; `docs/en/MANUAL.md`, `docs/en/PROCEDURES.md`, `docs/en/HISTORY.md` ;
   - les messages de la page et des outils renvoient, selon la langue, au manuel français ou anglais ; `CHANGELOG.md`, `CLAUDE.md`, `REFERENCE_OPTIONS.md` (déjà bilingue), `REPRISE.md`, `LICENSE`, `THIRD-PARTY.md` restent à la racine.
3. **Traductions anglaises** de `MODE_EMPLOI.md` (1 012 lignes, 120 000 caractères), `PROCEDURES.md` (152 lignes), `HISTORIQUE.md` (61 lignes) :
   - dans une conversation neuve, par tranches de 150 à 200 lignes, assemblées par un script ; livrer un seul fichier final ;
   - glossaire tiré de `src/i18n/en.json` (Arrival, Portal, Spawn, zone, Tiles…) pour que le manuel emploie les termes de l'interface ;
   - **à écrire d'abord** : un script de contrôle qui compare original et traduction (même nombre de titres, de lignes de tableau, de blocs de code ; blocs de code identiques ; termes du glossaire respectés) ;
   - essai prévu avec un petit modèle (Haiku) sur `PROCEDURES.md` : s'il passe le contrôle sans retouche, continuer avec lui, sinon Sonnet.
4. **Contenu à ajouter au manuel** : le compteur du titre se remet à zéro quand on ouvre le chat ; les nouveautés v35 à v37 non encore listées.
5. **`CHANGELOG.md`** : chaque entrée à partir de la v38 en français puis en anglais ; rédiger en anglais les notes des « Releases » GitHub pour `v35`, `v36`, `v37`.
6. **README** : vérifier que la section « Licence » annonce la MIT (elle disait « à choisir »), et qu'il n'y a ni IP ni nom d'hôte.
7. **Bouton « Copier le diagnostic »** dans la page (versions, état, tuiles chargées, durées) pour supprimer les demandes de F12.
8. **Démo publique** : page statique sans chat d'une petite région (par exemple Ankh Island, 12 Mo) sur GitHub Pages, dans un dépôt séparé ; plus tard, serveur de présence sur un petit VPS avec `wss://` (Caddy et un nom de domaine) : écrire la procédure d'installation. Une idée plus lointaine : présence réécrite en Worker Cloudflare avec Durable Object (aucun serveur à gérer).

## 7. Limites connues et pièges

- **Non testé ici** : Windows, Edge, carte graphique réelle, la vraie capture de souris d'Échap, une région en tuiles dans un sous-dossier, la conversion par convoar, les lignes PowerShell elles-mêmes (essayées sous Linux avec des chemins équivalents).
- Le test `tests/v33.py` sur le clignotement de bulle dépend du rendu logiciel de Chromium : il a déjà échoué une fois sans lien avec le code.
- Un ancien `presence_server.py` ignore les nouveautés (couleur, historique) : toujours relancer celui de `dist\` après `python build.py`.
- `--maj` ignore les options de la carte si on n'ajoute pas `--register` ; les chemins relatifs de `--register` et `--map-page` y sont relatifs à la page.
- Copier-coller depuis une réponse mise en forme peut ajouter des accents graves (backticks) devant les options : en PowerShell, ils cassent la commande.
- Les chemins contiennent `&` (`SL&OS`) : toujours des guillemets.
