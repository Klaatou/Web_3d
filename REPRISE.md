# Reprise du projet Web 3d

*État au 24/10/2026, version v41. À lire après `REGLES.md` (qui est dans les fichiers du Projet, pas dans le dépôt). Ce fichier est mis à jour et commité à la fin de chaque lot. Il ne contient ni adresse IP ni nom d'hôte.*

## 1. Ce qu'est ce projet

Une région OpenSim (sauvegarde `.oar`) devient une **page web 3D** où l'on se promène : conversion en glTF (`.glb`), chargement par tuiles pour les régions énormes, avatars des autres visiteurs, chat, portails et zones. Rien à installer pour les visiteurs. Dépôt public : `github.com/Klaatou/Web_3d` (licence MIT). Le propriétaire est JJ ; il travaille sous Windows (PowerShell, clavier AZERTY) et son public visé est la communauté OpenSim, majoritairement anglophone.

## 2. État du dépôt

- **`main` = v41** (étiquette `v41`, fichier `VERSION` : `v41 (24/10/2026)`). Étiquettes `v14` à `v41`.
- **v41** : bulles des fenêtres H, I, L et de Réglages ; fenêtres déplaçables par le titre (pile de gauche, pile de droite sous Réglages poussée par Réglages, ou libres), double-clic = retour à la dernière pile, clic de souris sur un titre retardé de 250 ms ; disposition retenue (`glb2html_layout`) et fichier `disposition.json` (Réglages : enregistrer, charger, disposition d'origine). Manuel § 25, `tests/v41.py`.
- **v40** : fenêtre « Arrivées » (touche L, clic = téléportation ou entrée en promenade), bouton « Recentrer la vue » (hors promenade, cadrage d'ouverture), lien « Manuel complet » (aide de la page, viewer), bulle du bouton « Copier le diagnostic ». Manuel § 24, `tests/v40.py`.
- **v39** : bouton « Copier le diagnostic » (fenêtre Informations / État de la page, panneau du viewer) : version, carte graphique, rendu, tuiles et durées, état, présence, 10 dernières erreurs ; adresses remplacées par `ADRESSE`, partie `#` jamais copiée. Code commun `DIAG` / `diagText` dans `src/core.js`, manuel § 23, `tests/v39.py`. Pas de bouton sur une page `--no-walk` (pas de fenêtre d'état).
- Les sessions cloud sont **terminées** (crédit épuisé). Tout se fait désormais dans le chat, par patchs (voir `REGLES.md`).
- **v38 (documentation, aucun changement de comportement)** : manuel, procédures et historique traduits en anglais (`docs/en/`), documents français déplacés dans `docs/fr/` (`MODE_EMPLOI.md` devenu `MANUEL.md`), `README.md` en anglais (page d'accueil GitHub) et `README.fr.md` en français, `verif_trad.py` (contrôle des traductions). Seule la chaîne de version change dans les outils fabriqués : après `python build.py`, `--maj` renouvelle la coquille des régions (ancienne copie gardée).
- Région de référence de JJ : la « 4X4 » (`OAR-Free_House_Gallery_I(4X4)-terrain`), 1 024 x 1 024 m, 106 tuiles et une vue d'ensemble, publiée avec présence et chat. Options de sa page : mer à 18,5 m (`--sea-y 18.5`), cible de départ `--target 392,68,-373`, `default.json` posé avec `--maj --default`.
- Fichiers locaux de JJ **hors dépôt** : `tools\glb-images-check.py`, `tools\glb-terrain-alt.py` (non suivis) : committer avec `git add -u` ou en nommant les fichiers, jamais `git add -A` sans vérifier.

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
| `verif_trad.py` | compare un document français et sa traduction (titres, tableaux, listes, code, liens, glossaire de l'interface) ; `python verif_trad.py docs\fr\MANUEL.md docs\en\MANUAL.md` |
| `tests/` | une vingtaine de suites (Chromium sans tête, vrai `presence_server.py`) |
| Documents | `docs/fr/` : `MANUEL.md`, `PROCEDURES.md`, `HISTORIQUE.md` ; `docs/en/` : `MANUAL.md`, `PROCEDURES.md`, `HISTORY.md` (tenus à jour ensemble, contrôlés par `verif_trad.py`) ; à la racine : `README.md` (anglais), `README.fr.md`, `CHANGELOG.md`, `CLAUDE.md`, `REFERENCE_OPTIONS.md`, `REPRISE.md` |

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
- **Options de fabrication** : `--maj` ne ressaisit rien et garde config et zones ; `--default` écrit `default.json` ; `--lib-url` place `lib` ailleurs ; `--zone-info-dist` (150 m par défaut) règle la distance des infobulles et des cônes.
- **Interface** : jamais d'information portée par la seule couleur.

## 6. À faire (dans l'ordre)

1. **Démo publique** (JJ n'est pas prêt : ne pas la lancer sans sa demande) : page statique sans chat d'une petite région (par exemple Ankh Island, 12 Mo) sur GitHub Pages, dans un dépôt séparé ; plus tard, serveur de présence sur un petit VPS avec `wss://` (Caddy et un nom de domaine) : procédure écrite le 24/10/2026 dans `docs/fr/PROCEDURES.md` § 11 et `docs/en/PROCEDURES.md` § 11 (Tailscale Funnel, Caddy, Cloudflare Tunnel), **non testée** : vérifier l'adresse IP vue derrière Funnel, Caddy ou Cloudflare Tunnel (contrôle en 4G décrit au § 11) avant de la tenir pour acquise ; pour Funnel, l'en-tête à donner à `--proxy-header` est inconnu (essayer `X-Forwarded-For`). Idée plus lointaine : présence réécrite en Worker Cloudflare avec Durable Object (aucun serveur à gérer).
2. **Règles de documentation désormais** : toute modification du manuel, des procédures ou de l'historique se fait dans les deux langues, puis `verif_trad.py` sur le couple modifié (0 erreur exigée) ; chaque entrée de `CHANGELOG.md` en français puis en anglais.

## 7. Limites connues et pièges

- **Non testé ici** : Windows, Edge, carte graphique réelle, la vraie capture de souris d'Échap, une région en tuiles dans un sous-dossier, la conversion par convoar, les lignes PowerShell elles-mêmes (essayées sous Linux avec des chemins équivalents).
- Les tests de navigateur durent de 1 à 2,5 min chacun (rendu logiciel) et un processus lancé en arrière-plan ne survit pas d'une réponse à l'autre : les lancer au premier plan, un ou deux par commande.
- **Edge de JJ en rendu logiciel, volontairement** (« Microsoft Basic Render Driver » dans le diagnostic) : sa carte graphique est réservée à son LLM. La lenteur des tuiles chez lui est donc attendue : ce n'est pas un bug à chercher.
- Le test `tests/v33.py` sur le clignotement de bulle dépend du rendu logiciel de Chromium : il a déjà échoué une fois sans lien avec le code.
- Un ancien `presence_server.py` ignore les nouveautés (couleur, historique) : toujours relancer celui de `dist\` après `python build.py`.
- `--maj` ignore les options de la carte si on n'ajoute pas `--register` ; les chemins relatifs de `--register` et `--map-page` y sont relatifs à la page.
- Copier-coller depuis une réponse mise en forme peut ajouter des accents graves (backticks) devant les options : en PowerShell, ils cassent la commande.
- Les chemins contiennent `&` (`SL&OS`) : toujours des guillemets.
- **Lignes PowerShell d'un patch** : ne jamais enchaîner `build` ou `Remove-Item` après un patch sans `if ($LASTEXITCODE -eq 0) { … }` (un patch arrêté a été effacé en v38). Un déplacement se fait avec `git mv` **avant** le patch ; un fichier effacé hors de git (` D` dans `git status`) se récupère avec `git restore`.
- `verif_trad.py` reconnaît le français dans le code par des indices (accents, mots propres au français, espace avant le deux-points) : un faux négatif reste possible ; les valeurs réelles (options, identifiants, chemins d'exemple) doivent rester identiques dans la traduction.
- Après un commit, vérifier que `git push` a abouti (`git log --oneline -2` montre `origin/main` sur le même commit).
