# Reprise du projet Web 3d

*État au 24/10/2026, version v45. À lire après `REGLES.md` (qui est dans les fichiers du Projet, pas dans le dépôt). Ce fichier est mis à jour et commité à la fin de chaque lot. Il ne contient ni adresse IP ni nom d'hôte.*

## 1. Ce qu'est ce projet

Une région OpenSim (sauvegarde `.oar`) devient une **page web 3D** où l'on se promène : conversion en glTF (`.glb`), chargement par tuiles pour les régions énormes, avatars des autres visiteurs, chat, portails et zones. Rien à installer pour les visiteurs. Dépôt public : `github.com/Klaatou/Web_3d` (licence MIT). Le propriétaire est JJ ; il travaille sous Windows (PowerShell, clavier AZERTY) et son public visé est la communauté OpenSim, majoritairement anglophone.

## 2. État du dépôt

- **`main` = v45** (fichier `VERSION` : `v45 (24/10/2026)`). Étiquettes `v14` à `v45` : la `v45` doit pointer sur le commit de clôture du point 1 (déplacée avec `git tag -f v45` puis `git push --force origin v45`, après le commit de `patch_v45d.py`).
- **v45** (point 1 des demandes de JJ : **une seule version**) : **(1b)** la page dit pourquoi la connexion de présence s'est fermée : `src/core.js` (`presenceConnect`, `onclose` lit `ev.code` et `ev.reason`, indicateur `P.opened`, `getPresence()` expose `opened`, `closeCode`, `closeReason`), textes `core.pres.never`, `core.pres.closed`, `core.pres.secerr`, `page.pres.error.why`, `viewer.pres.error.why`, ligne « Connexion de présence » du diagnostic ; `tests/v45.py`, manuel § 28. Le navigateur ne donne jamais la cause d'une connexion qui ne s'ouvre pas (code 1006, sans raison). **(1c)** `docs/*/PROCEDURES.md` § 11 : Funnel essayé, règle « la présence au même endroit que la page », voie D (VM Linux + Funnel + Apache), cas d'un autre service déjà publié. Le serveur de présence n'a pas changé. **(1a)** la coquille commence par `const LIB = './lib';` (seule ligne à modifier pour le dossier `lib`) ; la table d'import et le chemin Draco sont construits par un script classique avant tout module (`SHELL_IMPORTMAP_NEW`, `LIB_LINE_RE` dans `src/gen_tpl.py`) ; `--update` et la création gardent la ligne modifiée à la main (`lib_from_shell`, `effective_lib_url` : `--lib-url`, puis ligne de la coquille si elle n'est pas `./lib`, puis `libUrl`, puis `./lib`) ; `same_shell` ignore CRLF ; `build.py` écrit `dist/index.html`. Manuel § 28, `tests/v45_lib.py`, `tests/essai_importmap.html`. **Firefox et Safari : non essayés** (JJ doit ouvrir `tests/essai_importmap.html` dedans).
- **v44** : fin du passage à l'anglais : `gen_reference.py` (`--tools`, `--output`, `--check`), `verif_trad.py` (`--glossary`), anciens noms acceptés ; messages `[update]` ; noms d'exemple de l'aide (`FILE`, `FOLDER`, `SHELL.html`, `NAME`) ; menu Marqueur du viewer « Point (dot) » / « Dot ». `tests/samples.py` (partie 0) cherche les anciens noms dans l'aide, les messages et les documents : un oubli fait échouer le test. Historique complété de la v38 à la v44.
- **v43** : manuel § 27 « Référence des fichiers JSON » (FR et EN) : chaque fichier JSON, champ par champ (type, défaut, rôle, option) ; le § 16 y renvoie. `docs/samples/` : un exemple valide de chaque fichier (`region.config`, `region.zones` avec 8 zones, `default`, `regions`, `region.tiles`, `region.reglages`, `disposition`, `presence_identities`, `presence_bans`, `chat_history.sample.jsonl`), vérifiés par `tests/samples.py` contre le vrai code. **Tous les noms en anglais** (options, valeurs, clés, adresses), anciens noms toujours acceptés et convertis (fonction `old_options` dans chaque outil, `ZONE_MARKER_OLD`, `PROFILE_OLD` dans `src/gen_tpl.py`, `zmNorm` dans `src/core.js`) ; tableau complet au § 27.11. Correction : `--zone-marker none` (outils en anglais) n'était pas compris par la page. `gen_reference.py` passe `--nopause`.
- **v42** : rendu léger. Case « Rendu léger » dans Réglages (sous « Haute résolution ») et sous-fenêtre « Réglages fins… » (à gauche de Réglages, cachée quand Réglages se ferme), réglages en direct retenus par le navigateur (clé `glb2html_light_SALON`) : résolution (50 % préconisé), images/s au plus (15), vue d'ensemble seule en vue globale (aucune tuile détaillée hors promenade), rayon des tuiles (80 m), anticrénelage (non, au rechargement) ; bouton « Valeurs préconisées » ; « Valeurs d'origine » remet aussi le rendu léger. Proposition unique quand le rendu est logiciel (`softGpu` dans `src/core.js`). Option `--light` (reprise par `--maj`), lignes dans le viewer. Diagnostic : réglages du rendu léger, images rendues/s sur 5 s et causes du rendu continu. Réglages : 420 px de large au plus, défilement, note de couleur sur deux lignes, section « Disposition des fenêtres » mise en forme (titre en gras, filet), note « En promenade, Échap… » tout en bas (`#optsNote`). Proposition affichée en bas de l'écran, au-dessus des boutons. Manuel § 26, `tests/v42.py`.
- **v41** : bulles des fenêtres H, I, L et de Réglages ; fenêtres déplaçables par le titre (pile de gauche, pile de droite sous Réglages poussée par Réglages, ou libres), double-clic = retour à la dernière pile, clic de souris sur un titre retardé de 250 ms ; disposition retenue (`glb2html_layout`) et fichier `disposition.json` (Réglages : enregistrer, charger, disposition d'origine). Manuel § 25, `tests/v41.py`.
- **v40** : fenêtre « Arrivées » (touche L, clic = téléportation ou entrée en promenade), bouton « Recentrer la vue » (hors promenade, cadrage d'ouverture), lien « Manuel complet » (aide de la page, viewer), bulle du bouton « Copier le diagnostic ». Manuel § 24, `tests/v40.py`.
- **v39** : bouton « Copier le diagnostic » (fenêtre Informations / État de la page, panneau du viewer) : version, carte graphique, rendu, tuiles et durées, état, présence, 10 dernières erreurs ; adresses remplacées par `ADRESSE`, partie `#` jamais copiée. Code commun `DIAG` / `diagText` dans `src/core.js`, manuel § 23, `tests/v39.py`. Pas de bouton sur une page `--no-walk` (pas de fenêtre d'état).
- Les sessions cloud sont **terminées** (crédit épuisé). Tout se fait désormais dans le chat, par patchs (voir `REGLES.md`).
- **v38 (documentation, aucun changement de comportement)** : manuel, procédures et historique traduits en anglais (`docs/en/`), documents français déplacés dans `docs/fr/` (`MODE_EMPLOI.md` devenu `MANUEL.md`), `README.md` en anglais (page d'accueil GitHub) et `README.fr.md` en français, `verif_trad.py` (contrôle des traductions). Seule la chaîne de version change dans les outils fabriqués : après `python build.py`, `--maj` renouvelle la coquille des régions (ancienne copie gardée).
- Région de référence de JJ : la « 4X4 » (`OAR-Free_House_Gallery_I(4X4)-terrain`), 1 024 x 1 024 m, 106 tuiles et une vue d'ensemble, publiée avec présence et chat. Options de sa page : mer à 18,5 m (`--sea-y 18.5`), cible de départ `--target 392,68,-373`, `default.json` posé avec `--update --default`.
- Fichiers locaux de JJ **hors dépôt** : `tools\glb-images-check.py`, `tools\glb-terrain-alt.py` (non suivis) : committer avec `git add -u` ou en nommant les fichiers, jamais `git add -A` sans vérifier.

## 3. Architecture (détail dans `CLAUDE.md`)

| Élément | Rôle |
|---|---|
| `src/core.js` | noyau JavaScript commun : collisions, promenade, avatars, zones, carte, chat |
| `src/template.html` | page exportée (aide, état, réglages, chat) |
| `src/viewer_tpl.html` | viewer / éditeur de zones (`glb-viewer.html`) |
| `src/gen_tpl.py` | devient `dist/glb2html.py` : fabrique la page, `--update`, `--register`, `--map-page` |
| `src/presence_server.py` | serveur WebSocket de présence et de chat (dépendance `websockets`) |
| `tools/glb2tiles.py` | découpe un GLB énorme en tuiles + `X.overview.glb` |
| `tools/oar2glb.py` | convertit un OAR en GLB, refait le terrain complet |
| `src/i18n/fr.json`, `en.json`, `src/i18n.js`, `src/i18n_py.py` | tous les textes (page, viewer, outils) en français et en anglais |
| `build.py` | assemble tout dans `dist/` (**jamais éditer `dist/`**) |
| `gen_reference.py` | écrit `REFERENCE_OPTIONS.md` (bilingue) depuis les outils |
| `verif_trad.py` | compare un document français et sa traduction (titres, tableaux, listes, code, liens, glossaire de l'interface) ; `python verif_trad.py docs\fr\MANUEL.md docs\en\MANUAL.md` |
| `tests/` | une vingtaine de suites (Chromium sans tête, vrai `presence_server.py`) |
| Documents | `docs/fr/` : `MANUEL.md`, `PROCEDURES.md`, `HISTORIQUE.md` ; `docs/en/` : `MANUAL.md`, `PROCEDURES.md`, `HISTORY.md` (tenus à jour ensemble, contrôlés par `verif_trad.py`) ; à la racine : `README.md` (anglais), `README.fr.md`, `CHANGELOG.md`, `CLAUDE.md`, `REFERENCE_OPTIONS.md`, `REPRISE.md` |

Le dossier des outils fabriqués est `dist\` ; le dépôt local est `P:\_OpenSim\SL&OS\Web_3d\web_3d` ; les régions en tuiles sont dans `P:\_OpenSim\SL&OS\Web_3d\tuiles`.

## 4. Commandes de tous les jours (PowerShell, une ligne)

- Fabriquer : `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d"; python build.py` (écrit aussi `dist\index.html`, la coquille prête : à copier à la place de `--update` ; reporter la ligne `const LIB` si le dossier `lib` est ailleurs)
- Mettre à jour une région après une nouvelle version (garde config et zones ; `--update`, anciennement `--maj`, toujours accepté) : `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --update -o "P:\_OpenSim\SL&OS\Web_3d\tuiles\OAR-Free_House_Gallery_I(4X4)-terrain.html" --shared-shell`
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
| Fenêtres et repères | H aide, I informations / état, L arrivées (téléportation), O réglages, T cônes de portail |
| Recentrer la vue globale | bouton « Recentrer la vue » (pas de touche) |

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
- **Options de fabrication** : `--update` ne ressaisit rien et garde config et zones ; `--default` écrit `default.json` ; `--lib-url` place `lib` ailleurs ; `--zone-info-dist` (150 m par défaut) règle la distance des infobulles et des cônes.
- **Interface** : jamais d'information portée par la seule couleur.
- **Versions** : un point numéroté des demandes de JJ = **une seule version** (`VERSION` change une fois, `CHANGELOG.md`, manuel et historique n'ont qu'une entrée, étiquette posée à la fin du point) ; ne jamais en faire une par morceau.
- **Noms (v43)** : options, valeurs et clés JSON, paramètres d'adresse et noms d'exemple de l'aide sont **en anglais** ; un nom renommé garde l'ancien en alias (jamais de rupture pour JJ). Les textes visibles restent traduits par `src/i18n`. L'historique (`CHANGELOG.md`, `HISTORIQUE.md`) garde les noms de l'époque.
- **Contrôle des noms (v44)** : tout nouveau renommage ajoute l'ancien nom à l'expression `ANCIENS` de `tests/samples.py` et au tableau du manuel § 27.11.
- **Historique** : chaque lot ajoute sa ligne à `docs/fr/HISTORIQUE.md` et `docs/en/HISTORY.md`.
- **Fichiers JSON (v43)** : tout champ ajouté ou changé dans un fichier JSON se reporte dans le manuel § 27 (FR et EN) et dans l'exemple de `docs/samples/` ; `tests/samples.py` échoue si la config d'exemple n'a pas exactement les clés écrites par `build_cfg`.

## 6. À faire (dans l'ordre)

*Demandes de JJ du 24/10/2026. **Point 1 terminé en une seule version, v45 : 1a, 1b et 1c faits (reste l'essai Firefox et Safari chez JJ pour 1a), 1d étudié et non retenu.** Les points 2 à 7 et 9 attendent (le 8 est fermé) ; chacun sera de nouveau une seule version, après un rapport dans le chat avant tout code.*

### État vérifié chez JJ le 24/10/2026
- Région Hobbit (simple, sans zones, coquille commune et `default.json`) : la présence marche en `ws://` avec l'IP ou le nom et le port 8765 ; serveur lancé depuis `dist\`, sans `--host` ni `--proxy-header`.
- Tailscale Funnel : transmet bien le WebSocket (réponse 101) et la vraie IP du visiteur (`--proxy-header X-Forwarded-For`) ; un visiteur extérieur s'est promené par Funnel. Mais le navigateur bloque la connexion sur les appareils où Tailscale est actif quand la page vient d'une autre adresse (le nom `.ts.net` y donne une adresse privée en 100.x) ; téléphone avec Tailscale coupé : connecté. Un détour par le fichier `hosts` n'a pas marché.
- Sur la machine du LLM, `tailscale funnel --bg 8765` a écrasé la publication du LLM (rétablie par `tailscale serve --bg 3080`). Vérifié le 24/10/2026 : `tailscale serve status` montre le LLM sur `127.0.0.1:3080` (tailnet seulement), Funnel inactif ; le fichier `hosts` de cette machine ne contient plus de ligne pour le nom `.ts.net` (seule reste celle du téléphone de JJ : ne pas y toucher).
- **Règle apprise : la présence doit être au même endroit que la page** (même nom, ou page en https publiée aussi par Funnel).
- La page de JJ tournait encore en v42 : la coquille n'est pas mise à jour par `build.py` (`--update` nécessaire).
- Commit v44 (`6e5a603`) et étiquette `v44` sur `origin/main` ; v45 : commit `5301e77` (1b), puis les documents de ce fichier.

### Consignes réseau (machine du LLM de JJ)
Avant de proposer une configuration réseau, **demander où la page est hébergée et ce qui tourne déjà sur la machine**. Sur la machine du LLM (publié par `tailscale serve` vers `127.0.0.1:3080`) : ne jamais lancer `tailscale funnel` sans `--https=8443`, ne jamais lancer `tailscale funnel reset`. JJ laisse volontairement Edge en rendu logiciel pour garder sa carte graphique à son LLM : ne pas lui suggérer l'accélération matérielle.

### Demandes
1. **Point 1 : une seule version, v45**
   - **a) FAIT (v45)** : `build.py` dépose la coquille prête dans `dist\index.html` ; une seule ligne à éditer pour le dossier `lib` (`const LIB` en tête de coquille, table d'import et chemin Draco construits par un script classique avant tout module) ; `--update` et la création gardent la ligne modifiée à la main. Essai Chromium (Playwright) : démarre avec `./lib` et avec `../lib` (une ligne changée) ; un importmap écrit après un module est refusé (essai de JJ, Chromium 141). **Essai Edge 155 (Chromium) : OK**, fait par JJ le 24/10/2026 avec `tests/essai_importmap.html`. **Non essayés : Firefox et Safari** : JJ ouvre `tests/essai_importmap.html` dans ces navigateurs (résultat écrit en toutes lettres) ; si l'essai échoue quelque part, la coquille ne démarre pas dedans et il faut revoir ce choix. `--lib-url` reste accepté.
   - **b) FAIT (v45)** : la page dit pourquoi la connexion de présence s'est fermée (code et raison du serveur) ; le diagnostic dit si la connexion s'était ouverte.
   - **c) FAIT (v45)** : `PROCEDURES.md` § 11 (FR et EN) : résultats Funnel, règle « la présence au même endroit que la page », avertissement sur la racine du port, voie D (VM Linux + Tailscale Funnel + Apache), cas « un autre service est déjà publié » (commandes `--https=8443`, **non essayées** ; `PORT_PAGE` reste à choisir : le port 8096 de la machine du LLM est celui de Jellyfin, **à ne pas utiliser** ; JJ n'a pas accès à la configuration de son routeur (NAT), il avait pris ce port seulement parce qu'il était déjà ouvert). JJ essaiera la voie D sur sa VM Linux : ses retours (Apache derrière Funnel, journal d'Apache, démarrage par systemd, modération en service) sont à reporter dans `PROCEDURES.md` § 11.
   - **d) ÉTUDIÉ, NON RETENU (v45)** : `presenceUrl` avec deux adresses (la page essaie la seconde si la première échoue), par exemple « `wss://nom.ts.net, ws://127.0.0.1:8765` ». Raisons : utile surtout aux essais personnels de JJ sur la machine du serveur ; inutile aux visiteurs publics (une seule adresse `wss://`, au même endroit que la page : procédures § 11) ; coût : code à quatre endroits (page, carte des mondes, générateur, viewer), délai d'environ 6 s (estimation) avant de passer à la suivante, risque de deux serveurs différents derrière les deux adresses sans moyen de le détecter. Constats si l'idée revient : aujourd'hui une liste donne une `SyntaxError` immédiate à `core.js` (`presenceConnect`, `new WebSocket`), attrapée sans nouvelle tentative ; la carte (`template.html` `srvOf` et `queryServer`) utilise la même chaîne ; `gen_tpl.py` `fix_presence_url` et `clean_map` ; dans PowerShell, la virgule sans guillemets fait un tableau. À reprendre seulement si une région a un public mixte (réseau local et extérieur).
2. **Commandes à l'écran (gros lot, Opus, MAQUETTE À VALIDER AVANT LE CODE)**
   - Ligne d'état en bas, toujours visible, comme la boussole : position, mode (promenade, vol, vue globale), vue (subjective, 3e personne, caméra libre), sans ouvrir Infos.
   - Flèches cliquables à la souris : en promenade avancer, reculer, tourner ; en vue globale déplacer et tourner la vue.
   - Mode téléphone et tablette : aujourd'hui la page n'est pas utilisable au doigt (aucun geste tactile dans `core.js` et `template.html` ; seule la vue globale tourne et zoome, grâce à OrbitControls). Détecter l'écran tactile ; fenêtres Aide, Informations, Arrivées repliées à l'ouverture avec fermeture bien visible ; flèches en grand ; glissé du doigt pour regarder ; boutons Promenade / Voler / Chat ; vrai champ de saisie du chat pour ouvrir le clavier du téléphone.
   - Tests dans Chromium avec écran tactile simulé ; vrai téléphone non testable ici.
   - Le bas de l'écran est déjà occupé (proposition de rendu léger, boutons) : la place de chaque élément est une décision à valider sur maquette.
3. **Journal des visites** pour le créateur d'une page (artiste qui présente sa galerie) : visites horodatées avec durée, consultables même s'il n'était pas là. Décidé : lu depuis les journaux du serveur de présence (`presence.log` note déjà connexion, déconnexion et durée, spectateurs compris quand `spectate` est actif). Limites à dire : ne compte que ceux qui s'y connectent (un minimum) ; le nombre de pages ouvertes se lit mieux dans le journal d'Apache. Téléchargement par l'artiste : un RÉSUMÉ (date, durée, nombre de visites), pas le journal brut (avec `--log-ip raw` il contient des IP en clair) ; système de connexion pour y accéder à concevoir. Proposer la conception avant de coder.
4. **Livre d'or** : un lien posé dans le monde 3D (zone `url`) vers une page PHP sur Apache (VM Linux). Texte affiché en brut (jamais en HTML), limites de taille et de rythme, fichier hors du dossier public, pas d'IP en clair, RGPD (JJ est en France). Absent de la démo GitHub Pages (pas de PHP). Conception avec le point 3.
5. **Démo publique** (JJ n'est pas prêt : ne pas lancer sans sa demande) : candidate la région Hobbit (petite, s'ouvre seule avec `default.json`, aucune zone nécessaire). Config sans IP : vider `presenceUrl` et le `presence` de la fiche map, sinon l'IP est publiée sur GitHub Pages ; ou présence via Funnel ou VM avec la page en https.
6. **Release GitHub v45** (anciennement prévue pour la v44) : à publier après le commit, **seulement si JJ le décide** ; notes en anglais à refaire depuis `CHANGELOG.md` (v38 à v45), avec une section « Upgrading from v37 » (les anciens noms marchent toujours ; `python build.py`, relancer le serveur de présence depuis `dist\`, puis `--update` pour chaque région). Releases existantes : v35, v36, v37 (« Latest »), sans fichier joint. JJ hésite : personne n'utilise encore le dépôt.
7. **Vérifications restantes chez JJ** : rendu léger sous Edge sur la 4X4 (si le délai des fenêtres reste, lire les lignes « Rendu léger » et « Images rendues par seconde » de « Copier le diagnostic ») ; ses commandes avec les anciens noms (`--maj`, options de `glb2tiles.py` et `oar2glb.py`) marchent toujours ; `gen_reference.py` sans pause.
8. **Nom de domaine et présence : FERMÉ (24/10/2026)**. JJ a retesté : `ws://NOM:8765` (le nom de domaine de JJ) se connecte bien au serveur de présence ; l'échec noté d'abord était sans doute une erreur. Rien à diagnostiquer ; à rouvrir seulement si le problème revient.
9. **Idées anciennes (pas prioritaires)** : relayer seulement les visiteurs proches (rayon d'environ 100 m) si une région attire des foules ; but final de JJ : sa maison numérisée depuis ses plans et reliée à Home Assistant. Idée plus lointaine : présence réécrite en Worker Cloudflare avec Durable Object (aucun serveur à gérer).

### Règles permanentes de documentation
Toute modification du manuel, des procédures ou de l'historique se fait dans les deux langues, puis `verif_trad.py` sur le couple modifié (0 erreur exigée) ; chaque entrée de `CHANGELOG.md` en français puis en anglais ; tout renommage ajoute l'ancien nom à `ANCIENS` dans `tests/samples.py` et au manuel § 27.11 ; tout champ JSON ajouté ou modifié va au manuel § 27 et dans `docs/samples/`. Commit : jamais `git add -A` (fichiers locaux non suivis, par exemple `patch_v42.py`) ; `git add -u` plus les nouveaux fichiers nommés.

## 7. Limites connues et pièges

- **Non testé ici** : Windows, Edge, carte graphique réelle, la vraie capture de souris d'Échap, une région en tuiles dans un sous-dossier, la conversion par convoar, les lignes PowerShell elles-mêmes (essayées sous Linux avec des chemins équivalents).
- Les tests de navigateur durent de 1 à 2,5 min chacun (rendu logiciel) et un processus lancé en arrière-plan ne survit pas d'une réponse à l'autre : les lancer au premier plan, un ou deux par commande.
- **Edge de JJ en rendu logiciel, volontairement** (« Microsoft Basic Render Driver » dans le diagnostic) : sa carte graphique est réservée à son LLM. La lenteur des tuiles chez lui est donc attendue : ce n'est pas un bug à chercher. Le rendu léger (v42) vise ce cas ; ses valeurs préconisées n'ont pas été mesurées sur Edge. Constat de JJ avant la v42 : 2 s de délai à l'ouverture des fenêtres en vue globale, moins en promenade. Mesuré dans Chromium (SwiftShader) : au repos en vue globale, 0 rendu par seconde, et l'ouverture d'une fenêtre ne déclenche aucun rendu ; seuls la mer animée (`core.js`, boucle de rendu) et la présence d'autres visiteurs (`presenceTick`) forcent un rendu continu. La cause exacte chez JJ reste à lire dans la ligne « Images rendues par seconde » du diagnostic.
- **Tests de navigateur : un seul à la fois.** Le 24/10/2026, `tests/v32.py` lancé en même temps qu'un autre a échoué 4 fois (2 fois en v42 aussi), puis est passé entier seul : les échecs venaient de la charge. Les « 2 échecs anciens » de `tests/v32.py` notés plus tôt étaient de cette nature.
- **Patch de plusieurs fichiers** : fabriqué à partir des différences avec le commit de départ, appliqué à un clone frais en LF puis en CRLF (résultat identique), puis build et tests ; un nouveau fichier prend les fins de ligne du dépôt. Dire ce qui n'a pas pu être essayé (Windows, Edge, PowerShell, Firefox, Safari, vrai téléphone).
- **`tests/v45.py`** (présence : serveur absent, serveur qui ferme avec un code, constructeur refusé, anglais, viewer) passe seul en 1 min environ.
- `tests/v33.py` s'arrête à l'étape 1 (attente de 60 s, processeur ralenti x6) en v42 comme en v43 : la suite du test (repères des zones, récapitulatif du viewer) **ne tourne donc jamais ici** ; ses attentes ont été mises aux nouveaux noms (`dot`, `range`) sans pouvoir les essayer.
- Le test `tests/v33.py` sur le clignotement de bulle dépend du rendu logiciel de Chromium : il a déjà échoué une fois sans lien avec le code. Le 24/10/2026, dans le bac à sable, `tests/v33.py` (attente de 60 s à l'étape 1, processeur ralenti x6) et `tests/v24.py` (2 échecs « survol du marqueur por ») échouent de la même façon en v41 et en v42 : antérieurs, cause non cherchée.
- Un ancien `presence_server.py` ignore les nouveautés (couleur, historique) : toujours relancer celui de `dist\` après `python build.py`.
- `--update` ignore les options de la carte si on n'ajoute pas `--register` ; les chemins relatifs de `--register` et `--map-page` y sont relatifs à la page.
- Copier-coller depuis une réponse mise en forme peut ajouter des accents graves (backticks) devant les options : en PowerShell, ils cassent la commande.
- Les chemins contiennent `&` (`SL&OS`) : toujours des guillemets.
- **Lignes PowerShell d'un patch** : ne jamais enchaîner `build` ou `Remove-Item` après un patch sans `if ($LASTEXITCODE -eq 0) { … }` (un patch arrêté a été effacé en v38). Un déplacement se fait avec `git mv` **avant** le patch ; un fichier effacé hors de git (` D` dans `git status`) se récupère avec `git restore`.
- `verif_trad.py` reconnaît le français dans le code par des indices (accents, mots propres au français, espace avant le deux-points) : un faux négatif reste possible ; les valeurs réelles (options, identifiants, chemins d'exemple) doivent rester identiques dans la traduction.
- Après un commit, vérifier que `git push` a abouti (`git log --oneline -2` montre `origin/main` sur le même commit).
