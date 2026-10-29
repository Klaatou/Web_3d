# Reprise du projet Web 3d

*État au 29/10/2026 (fin de journée) : `main` = v52 plus des lots « Non publié » (§ 2.1) ; démo en ligne avec présence (§ 2.2). À lire après `REGLES.md` (dans les fichiers du Projet, pas dans le dépôt). Ce fichier est **remplacé en entier** et commité à la fin de chaque lot (règles 12 et 23) ; les anciens patchs de `REPRISE.md` (`patch_reprise_*.py`) sont **remplacés par cette version : ne pas les appliquer**. Il ne contient ni adresse IP ni nom d'hôte réels (règle 18) : le nom public du serveur de présence s'écrit `MACHINE.TAILNET.ts.net`, l'adresse de la VM `ADRESSE_VM`, son utilisateur `UTILISATEUR`.*

## 1. Ce qu'est ce projet

Une région OpenSim (sauvegarde `.oar`) devient une **page web 3D** où l'on se promène : conversion en glTF (`.glb`), chargement par tuiles pour les régions énormes, avatars des autres visiteurs, chat, portails et zones. Rien à installer pour les visiteurs. Dépôt public : `github.com/Klaatou/Web_3d` (licence MIT). Le propriétaire est Klaatou ; il travaille sous Windows (PowerShell, clavier AZERTY) et son public visé est la communauté OpenSim, majoritairement anglophone. **Démo en ligne** : `https://klaatou.github.io/Web_3d_demo/` (deux régions reliées par des portails, carte des mondes, présence). Contenus de démonstration tirés du site Outworldz (retrait sur demande).

## 2. État au 29/10/2026

### 2.1 Dépôt

- **`main` = v52** (`VERSION` : `v52 (25/10/2026)`, étiquette `v52` posée sur `72d8b22`) **plus des lots non publiés** (`VERSION` inchangée, détail dans `CHANGELOG.md` « Non publié (après la v52) », `docs/fr/HISTORIQUE.md` et le manuel § 36), dans l'ordre : 25/10 vue d'ensemble (`VUE_ENSEMBLE.md`, `OVERVIEW.md`) et crédits des README ; 25 au 27/10 audit complet et lot correctif ; 27/10 `oar2glb` sans chemin personnel (variable `CONVOAR`), GIF du README, lien Outworldz ; 28/10 démo en ligne (README, aperçu de partage), `carte.html` sans présence, **souris volontaire**, **G en bascule** ; 29/10 **icône « 3D »** (`favicon.ico` remplaçable), **adresses de `carte.html` sélectionnables**, serveur : **requêtes illisibles**, **IPv6 par `/64`**, **`oublier`**, **`pseudos`**, page : **arrêt des essais de connexion**.
- Les versions v14 à v52 (étiquettes `v14` à `v52`, la `v45` a été déplacée) sont décrites dans `CHANGELOG.md` et `docs/fr/HISTORIQUE.md` : ne pas les recopier ici. Le dépôt compte environ 35 000 lignes de code et une cinquantaine de fichiers de test.
- **Numérotation** : Klaatou est d'accord (27/10/2026) pour « une version = une publication décidée par lui » ; les petites modifications restent des commits sous « Non publié ». La v52 deviendrait `1.0.0` (lot séparé : `VERSION`, `build.py`, `--update`, tests qui lisent la version, étiquettes, documents). La règle 15 de `REGLES.md` est à réécrire par lui.
- Fichiers de Klaatou **hors dépôt** : `tools\glb-images-check.py` et `tools\glb-terrain-alt.py` (non suivis).

### 2.2 En ligne

- **Démo** : dépôt `Klaatou/Web_3d_demo` (public, description, mots-clés et image de partage réglés ; README bilingue avec le GIF du dépôt principal), GitHub Pages sur la branche `main`. Contenu : `index.html` et `carte.html` de `dist\`, `favicon.ico`, `lib\three-0.160.0\` (avec `draco\`), `regions.json` (par `--scan-sites`), `default.json`, `.nojekyll`, `.gitattributes` (`* -text`), un dossier par région (PalmIsland, hobbit : `.glb`, `.config.json`, `.zones.json`, vignette 320 px du même nom), `preview.jpg` et les balises d'aperçu de partage ajoutées à `index.html` par `ajout_og.py`. La présence de la démo est active : `presenceUrl` des deux `.config.json` = `wss://MACHINE.TAILNET.ts.net` ; `regions.json` reprend ce `presence`. **Un visiteur extérieur (adresse étrangère) s'y est promené le 29/10/2026.**
- **Serveur de présence public** : une **VM Debian 13** dans VMware sur le PC de Klaatou (réseau NAT : invisible du réseau local, voulu ; installée sans les extensions VMware, donc ni copier-coller ni dossier partagé). Python 3.13 et `python3-websockets` d'`apt` ; **Tailscale** (`tailscale up`), publication par **`tailscale funnel --bg 8765`** (aucun port ouvert dans la box) ; origine `https://klaatou.github.io` déclarée dans `presence_creators.json` de la VM.
  - **Démarrage** : l'unité systemd `web3d-presence.service` (`Type=forking`, `Restart=always`, `RestartSec=5`) lance une session **`tmux` nommée `presence`** qui exécute `lance_presence.sh`, une boucle qui relance `presence_server.py` 5 s après un arrêt. Raison : la **console de modération** du serveur (commandes tapées) a besoin d'un clavier, que `systemctl` seul ne donne pas.
  - **Console** : `tmux attach -t presence` (sous l'utilisateur de la VM, pas `root`) ; depuis le PC : `ssh -t UTILISATEUR@ADRESSE_VM "tmux attach -t presence"` (avec copier-coller) ; sortir sans arrêter : `Ctrl+B` puis `D` ; arrêter pour de bon : `systemctl stop web3d-presence` (`root`).
  - **Options** : `--host 127.0.0.1 --port 8765 --proxy-header X-Forwarded-For --log presence.log --log-ip raw --log-days 0 --history-file chat.jsonl --history-days 0 --visits visits.jsonl --creators presence_creators.json`. **Klaatou a choisi** `--log-ip raw` et la conservation sans limite (il veut voir les IP) ; risque noté (adresses IP et chat d'inconnus, RGPD en France ; défauts du serveur : `--log-ip hash` et 30 jours) : à rappeler avant de promouvoir la démo.
  - **Mise à jour du serveur** : après un `python build.py` qui change `presence_server.py`, l'envoyer (`scp` depuis `dist\`) puis `systemctl restart web3d-presence`. La VM a **sa propre copie** de `presence_creators.json` et du registre `presence_identities.json` (pseudos réservés).
  - **Debian 13 : pièges rencontrés** : le paquet `python` n'existe plus (`python3`) ; la ligne `cdrom` de `/etc/apt/sources.list` fait échouer `apt-get update` (la retirer avec `sed`) et **bloque** `apt-get update && apt-get install` (ne pas chaîner) ; `su` sans le tiret ne met pas `/usr/sbin` dans le chemin (`usermod` introuvable) : utiliser `su -` ; `sudo` n'est pas installé par défaut ; un fichier de service **collé** dans la console a été mal recopié (fichier envoyé par `scp` : fiable).
- **Pas de nom de domaine** pour l'instant (§ 6).
- **Plan « page de présentation et services »** : document de Klaatou hors dépôt (objectif, six étapes à critères de passage, liste de contrôle technique, juridique et coût, risques).

### 2.3 Hors dépôt, à garder chez Klaatou
`ajout_og.py` (ajoute les balises d'aperçu à l'`index.html` de la démo, à relancer après chaque recopie de `dist\index.html`), `preview.jpg` (1200 x 630), `lance_presence.sh` et `web3d-presence.service` (copies dans la VM), `presence_creators.json` (copie sur le PC : `P:\_OpenSim\SL&OS\Web_3d\`, **jamais** dans `Sites\` : servi publiquement), ses sites (`P:\_OpenSim\SL&OS\Web_3d\Sites\` : **une** coquille `index.html`, `lib\`, `regions.json`, `carte.html`, un dossier par région avec config, `.glb` ou tuiles, zones et `default.json` ; lien `index.html?region=houses/NOM#spawn=default&name=…` ; la bonne commande de mise à jour est celle du § 4). Région de référence : la « 4X4 » (`OAR-Free_House_Gallery_I(4X4)-terrain`, 1 024 x 1 024 m, 106 tuiles et une vue d'ensemble, mer à 18,5 m, cible de départ `392,68,-373`).

## 3. Architecture (détail jusqu'à la v37 dans `CLAUDE.md`)

| Élément | Rôle |
|---|---|
| `src/core.js` | noyau JavaScript commun : collisions, promenade, avatars, zones, carte, chat |
| `src/template.html` | page exportée (aide, état, réglages, chat) |
| `src/viewer_tpl.html` | viewer / éditeur de zones (`glb-viewer.html`) |
| `src/gen_tpl.py` | devient `dist/glb2html.py` : fabrique la page, `--update`, `--register`, `--map-page`, `--scan-sites` ; contient aussi la page de carte (`MAP_PAGE_TEMPLATE`) |
| `src/presence_server.py` | serveur WebSocket de présence et de chat (dépendance `websockets`) |
| `tools/glb2tiles.py` | découpe un GLB énorme en tuiles + `X.overview.glb` |
| `tools/oar2glb.py` | convertit un OAR en GLB, refait le terrain complet |
| `src/i18n/fr.json`, `en.json`, `src/i18n.js`, `src/i18n_py.py` | tous les textes (page, viewer, outils) en français et en anglais |
| `build.py` | assemble tout dans `dist/` (**jamais éditer `dist/`**) |
| `gen_reference.py` | écrit `REFERENCE_OPTIONS.md` (bilingue) depuis les outils |
| `verif_trad.py` | compare un document français et sa traduction (titres, tableaux, listes, code, liens, glossaire de l'interface) ; `python verif_trad.py docs\fr\MANUEL.md docs\en\MANUAL.md` |
| `tests/` | une cinquantaine de fichiers de test (Chromium sans tête, vrai `presence_server.py`) ; `h37.py` : outils communs (`Onglet`, `serveur`, `port_libre`) |
| `src/favicon.ico` | icône par défaut, copiée dans `dist\` par `build.py` |
| Documents | `docs/fr/` : `MANUEL.md`, `PROCEDURES.md`, `HISTORIQUE.md` ; `docs/en/` : `MANUAL.md`, `PROCEDURES.md`, `HISTORY.md` (tenus à jour ensemble, contrôlés par `verif_trad.py`) ; à la racine : `README.md` (anglais), `README.fr.md`, `CHANGELOG.md`, `CLAUDE.md`, `REFERENCE_OPTIONS.md`, `REPRISE.md` |

Le dossier des outils fabriqués est `dist\` ; le dépôt local est `P:\_OpenSim\SL&OS\Web_3d\web_3d` ; les sites publiés sont dans `P:\_OpenSim\SL&OS\Web_3d\Sites` (une coquille à la racine, un dossier par région, voir § 2) ; l'ancien dossier `P:\_OpenSim\SL&OS\Web_3d\tuiles` n'est plus celui que Klaatou publie.

## 4. Commandes de tous les jours (PowerShell, **une ligne chacune, chemins complets entre guillemets**)

- **Appliquer un patch** : `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d"; git pull; python .\patch_NOM.py; if ($LASTEXITCODE -eq 0) { python build.py }` ; commit : `git status --short` puis `git add -A; git commit -m "..."; git push` (messages neutres : « docs : mise en forme »).
- **Fabriquer** : `python build.py` (écrit `dist\index.html`, la coquille prête, `dist\carte.html`, `dist\favicon.ico`) ; **ne jamais éditer `dist\`**.
- **Mettre à jour une région** (garde config et zones) : `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --update -o "P:\_OpenSim\SL&OS\Web_3d\Sites\houses\NOM.html" --shared-shell "P:\_OpenSim\SL&OS\Web_3d\Sites\index.html"` (le chemin de la coquille de la racine évite d'en écrire une inutile dans le dossier de la région).
- **Sites de Klaatou** après `python build.py` : copier `dist\index.html`, `dist\carte.html` et `dist\favicon.ico` dans `Sites\` ; `regions.json` : `python .\glb2html.py --scan-sites "P:\_OpenSim\SL&OS\Web_3d\Sites"` (d'abord avec `--dry-run`).
- **Mettre à jour la démo en ligne** (à chaque lot qui change la page, la carte ou l'icône) : `Copy-Item "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\index.html", "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\carte.html", "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\favicon.ico" "P:\_OpenSim\SL&OS\Web_3d\Web_3d_demo"; cd "P:\_OpenSim\SL&OS\Web_3d\Web_3d_demo"; python "P:\_OpenSim\SL&OS\Web_3d\ajout_og.py"; git add index.html carte.html favicon.ico; git commit -m "mise a jour"; git push`. (Le chemin de `ajout_og.py` est celui proposé : à confirmer avec Klaatou.) **Rappeler cette séquence à Klaatou à chaque lot qui touche `src/template.html`, `src/core.js`, `src/gen_tpl.py` ou l'icône.** Vérifier : `curl.exe -s "https://klaatou.github.io/Web_3d_demo/?v=N" | Select-String "og:image"` (`?v=N` évite les caches). **GitHub Pages met jusqu'à une dizaine de minutes à refléter un changement** (constaté le 29/10/2026).
- **Servir les sites pour les essayer** : `cd "P:\_OpenSim\SL&OS\Web_3d\Sites"; python -m http.server 8000`.
- **Serveur de présence sur le PC** (essais locaux) : `python ".\presence_server.py" --log presence.log --log-ip raw --log-days 0 --history-file chat.jsonl --history-days 0 --visits visits.jsonl --creators presence_creators.json` depuis `dist\` (toujours relancer celui de `dist\` après `python build.py`).
- **Serveur de présence public (VM)** : voir § 2.2 (envoi par `scp`, `systemctl restart web3d-presence`, console `tmux`).
- **Bac à sable** : `npm pack three@0.160.0` (jsDelivr est refusé), `python build.py --vendor DOSSIER_package` ; voir § 7.
- Règles de Klaatou : écrire « Klaatou », jamais ses initiales ; README FR et EN, section « Crédits » faite (texte choisi par lui le 25/10/2026) : ne pas la reformuler sans sa demande ; commits neutres.

## 5. Décisions de conception arrêtées (ne pas rediscuter sans demande de Klaatou)

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
| Souris | **G bascule** (capture si la souris est libre, la libère si elle est capturée) ; le bouton « Capturer la souris » ne fait que capturer (un pointeur capturé ne clique rien) ; **un clic ne capture jamais** ; Échap libère (réservé au navigateur) ; sans capture, glisser bouton enfoncé tourne la vue |
| Retour à l'arrivée | R |
| Fenêtres et repères | H aide, I informations / état, L arrivées (téléportation), O réglages, T cônes de portail |
| Recentrer la vue globale | bouton « Recentrer la vue » (pas de touche) |

**Comportements**
- Une arrivée nommée `default` sert de point d'entrée à l'ouverture sans lien ; `--target` explicite garde le cadrage. `#spawn=NOM` ou `#pos=x,y,z,yaw` : arrivée demandée.
- **Arrivée occupée** : le nouvel arrivant est décalé (1,5 m environ de l'occupant) et tourné vers lui ; jamais quelqu'un qui marche.
- **Région par défaut** (adresse sans `?region=`) : `X.config.json` du nom de la page, puis `default.json`, puis la première entrée relative de `regions.json`, sinon message d'erreur. `?region=` accepte `nom` ou `dossier/nom`, jamais `..`, `:`, `\`, `?`, `#`.
- **Paramètres de l'adresse** : séparés par `&` ou `#` (fonction `hashParams`), langue `#lang=en`, pseudo `#name=`.
- **Zones d'une région en tuiles** : repère du modèle d'origine, sans recentrage ; zones liées à un objet par `extras.ref`. Fichiers `X.zones.json`, `regions.json`, `*.html`, journaux : jamais dans le dépôt (`.gitignore`).
- **Clignotement du pseudo cité** : sans limite de durée, jusqu'à la première action (touche, clic, mouvement), uniquement sur la page du visiteur cité. Le compteur « (N) » du titre se remet à zéro à l'ouverture du chat (comportement voulu par Klaatou, documenté au manuel § 29.6).
- **Langue** : tout texte visible passe par `tr()` ou `data-i18n*`, jamais de français en dur ; ajouter une langue = ajouter un fichier `src/i18n/xx.json`. Réglage « Langue / Language » (Auto, Français, English).
- **Sons** : réglage général (volume), citation, arrivée, départ ; les promeneurs seulement, jamais la liste initiale.
- **Boussole** : le nord est la direction -Z du modèle (z = -y d'OpenSim), décalée par `rotate` et `--north` ; case dans les réglages.
- **Chat et serveur** : historique de 200 messages par défaut, `--history-file` conserve entre deux relances (jamais d'adresse IP), `--log-days 0` ne supprime aucun journal.
- **Options de fabrication** : `--update` ne ressaisit rien et garde config et zones ; `--default` écrit `default.json` ; `--lib-url` place `lib` ailleurs ; `--zone-info-dist` (150 m par défaut) règle la distance des infobulles et des cônes.
- **Interface** : jamais d'information portée par la seule couleur.
- **Deux philosophies du projet (Klaatou, 25/10/2026)** : (1) **autonome** : des `.html` fabriqués par `glb2html.py` avec tout dedans (région, liste des régions de `--map-page`), qui s'ouvrent depuis le disque ; (2) **hébergée** : les deux coquilles communes `index.html` et `carte.html` (déposées par `build.py` dans `dist\`) lisent leurs JSON (`NOM.config.json`, `regions.json`) et demandent un serveur web ; elles peuvent aussi être fabriquées par le générateur. Les deux modes cohabitent.
- **Versions** : un point numéroté des demandes de Klaatou = **une seule version** (`VERSION` change une fois, `CHANGELOG.md`, manuel et historique n'ont qu'une entrée, étiquette posée à la fin du point) ; ne jamais en faire une par morceau.
- **Noms (v43)** : options, valeurs et clés JSON, paramètres d'adresse et noms d'exemple de l'aide sont **en anglais** ; un nom renommé garde l'ancien en alias (jamais de rupture pour Klaatou). Les textes visibles restent traduits par `src/i18n`. L'historique (`CHANGELOG.md`, `HISTORIQUE.md`) garde les noms de l'époque.
- **Contrôle des noms (v44)** : tout nouveau renommage ajoute l'ancien nom à l'expression `ANCIENS` de `tests/samples.py` et au tableau du manuel § 27.11.
- **Historique** : chaque lot ajoute sa ligne à `docs/fr/HISTORIQUE.md` et `docs/en/HISTORY.md`.
- **Fichiers JSON (v43)** : tout champ ajouté ou changé dans un fichier JSON se reporte dans le manuel § 27 (FR et EN) et dans l'exemple de `docs/samples/` ; `tests/samples.py` échoue si la config d'exemple n'a pas exactement les clés écrites par `build_cfg`.

- **Séparateurs de langue (v52)** : une clé en `.sep` (`map.sep`, `page.map.sep`) est un séparateur : saut de ligne en français, « · » en anglais ; une nouvelle langue choisit le sien. `tests/i18n.py` accepte les valeurs blanches pour ces clés seulement.
- **Délais de `carte.html` (v52)** : `POLL_MS` et `POLL_ALERT_MS` en tête du script de la page, modifiables à la main ; Klaatou veut pouvoir les changer sans chercher.
- **Surveillance des arrivées (v52)** : seulement `carte.html` ; repère visuel en texte et forme (jamais la couleur seule) ; le repère reste jusqu'au survol de la tuile.

- **Images d'exposition (idée de Klaatou, 25/10/2026, pas commencée)** : pour des expositions ou des portfolios. Exigence de Klaatou : **mettre à jour le contenu sans repasser par un serveur OpenSim, sans modifier l'OAR ni refaire la conversion** : déposer des images dans un dossier, avec un nommage qui les affiche à l'endroit voulu. Pistes à étudier (aucune décidée) : lien par zone liée à un objet (manuel § 9, `extras.ref`) ou par nom d'objet ; un site statique ne peut pas lister un dossier, donc soit un index écrit par une commande (comme `--scan-sites`), soit la page essaie des noms connus ; remplacer la texture de l'objet (un objet plat dédié est préférable : étirement et orientation dépendent des UV, à essayer sur un vrai objet) ; images d'un autre site : CORS requis pour WebGL, `http` bloqué dans une page `https`.
- **Zones média (réponse à Klaatou, 25/10/2026, estimations non essayées)** : aujourd'hui les zones sont `url` (nouvel onglet), `ha`, `portal`, `spawn` (`core.js:1790`). Musique (la plus simple : clic ou E, ou entrée dans la zone ; boucle, fondu à la sortie, volume du réglage « Sons », une seule à la fois ; mp3 ou ogg à côté de la région ; un geste de l'utilisateur suffit, la promenade en fournit un), image sur un objet, page HTML dans une fenêtre superposée (iframe `sandbox`, `http` et `https` seulement ; beaucoup de sites interdisent l'affichage dans un cadre ; ton propre fichier à côté de la région marche). Ordre proposé : musique, image, page, en une seule version. **Klaatou : « on verra quand le faire ».**

**Décisions du 28 et 29/10/2026**
- **Souris** (demandes de Klaatou) : capture volontaire seulement (G ou bouton) ; G en bascule ; le bouton ne change pas d'étiquette (souris capturée, on ne peut plus cliquer dessus).
- **Icône des pages** : petit SVG « 3D » incorporé dans `<link rel="icon">` (`template.html`, `viewer_tpl.html`, page carte de `gen_tpl.py`) **et** adoption d'un `favicon.ico` placé à côté de la page (sonde par `Image`) : on change l'icône d'un site en remplaçant ce fichier. `build.py` écrit `dist\favicon.ico` depuis `src/favicon.ico` (16, 32, 48, 64 px).
- **`carte.html`** : la case de surveillance disparaît sans serveur de présence ; l'adresse affichée est **hors du lien** de la vignette (`.cell`), donc sélectionnable (le zoom n'était pas en cause : un clic-glissé dans un lien ne sélectionne pas) ; `draw()` ne redessine que si les données changent (`lastSig`, qui doit inclure tout ce qui change le contenu, y compris `emptyText()`) et jamais pendant une sélection (`drawLater`).
- **Serveur de présence** : requêtes illisibles (sondage RDP `mstshash`, début de TLS, autre) en une ligne « requête illisible » au lieu d'une trace ; IPv6 groupée par préfixe `/64` pour `--max-per-ip`, `bannir` et la limite des clés de visites (`ip_group`) ; les anciens bannissements gardent l'adresse exacte ; journal et console gardent l'adresse complète. Console : `liste`, `ejecter`, `bannir`, `bans`, `debannir`, `oublier <pseudo>` (libère un pseudo réservé), `pseudos [filtre]` (liste les pseudos réservés), `rooms`, `visits-key`, `creators`, `aide`.
- **Page, présence** : après 5 essais de connexion sans jamais s'être ouverte (12 si ouverte puis perdue), la page s'arrête et dit « essais arrêtés : recharge la page pour réessayer » (`PRES_TRIES_NEVER`, `PRES_TRIES_LOST` dans `core.js`) ; un nouveau passage en promenade refait un essai.
- **Portails de la démo** : cible relative (`index.html?region=DOSSIER/NOM`), `spawn` = zone d'arrivée de la région d'arrivée, jamais de `#` dans la cible, la casse des noms compte sur GitHub Pages.
- **Présence publique** : voie A de `PROCEDURES` § 11 (Tailscale Funnel depuis la machine du serveur), **`wss://` jamais `ws://`**, origine de la page déclarée dans `presence_creators.json` (copie de la machine du serveur), pas de `--origins` quand `--creators` est utilisé.
- **Console du serveur en service** : jamais `systemctl` seul (plus de clavier, donc plus de console de modération) : `tmux` démarré par systemd, voir § 2.2.

## 6. À faire

Klaatou choisit l'ordre ; chaque lot commence par un rapport dans le chat (règle 8 : aucune livraison sans son accord).

**D'abord (essais à faire chez Klaatou)**
1. **Durabilité de la VM** : `reboot` (la session `presence` et la publication Funnel doivent revenir seules : `su - UTILISATEUR -c "tmux ls"`, `tailscale funnel status`) ; `su - UTILISATEUR -c "tmux kill-server"` (le service doit revenir en quelques secondes grâce à `Restart=always`) ; `systemctl status web3d-presence`. Corriger si besoin, puis **documenter dans `PROCEDURES` § 11** (FR et EN) la séquence qui marche (tmux et systemd, pièges de Debian 13), **seulement après ces essais**.
2. **Edge** (et un téléphone) sur la démo en ligne : icône, souris, G, carte, présence.

**Ensuite**
3. **Note pour les créateurs** accueillis sur le serveur de présence (FR et EN, aucune adresse réelle) : l'essai d'une origine déclarée depuis `github.io` a réussi ; à écrire en ne documentant que ce qui a marché : l'origine à donner à l'hôte, le préfixe de salon (`alice.NOM`, valeur `room` de la config), l'option `--presence-url` de leur page, les limites (`maxWalkers`, `maxRooms`), `wss://` obligatoire en https, ce que le serveur enregistre (IP selon `--log-ip`, historique du chat, journal des visites) et ce qu'ils ne contrôlent pas (modération, suspension).
4. **Renumérotation `1.0.0`** (lot séparé, § 2.1).
5. **Nom de domaine** : Klaatou en veut un, pour le site de présentation **et** pour servir le serveur de présence (nom stable pour `wss://`, IP absente des pages). **Ne plus lui répondre qu'il n'en a pas besoin.** Écartés : `web-3d.com` (495 € de frais « premium » en plus de 9 € par an) et `sites-3d.com` (éloigné du nom du projet, tiret, proche de Site3D, service d'intégration de GLB avec three.js, et de deux logiciels du même nom ; `sites3d.com` est pris). Critères : court, sans tiret, dit « régions » ou « mondes », aucun frais premium, **recherche** d'abord pour voir s'il ressemble à un produit connu ; éviter « opensim » dans le nom (marque du projet OpenSimulator : à vérifier). Piste technique, non essayée : domaine plus serveur avec Caddy en proxy inverse (certificat automatique, WebSocket sans réglage à ma connaissance) à la place d'Apache de la voie D.
6. **Page de présentation** (étape 3 du plan hors dépôt) : GIF cliquable vers la démo, deux phrases, bouton « Essayer la démo », contact et procédure de retrait, mentions légales (à vérifier pour la France).
7. **Release GitHub** (à décider par Klaatou ; releases existantes : v35, v36, v37 sans fichier joint) ; **livre d'or** (facultatif, peut être externe : zone `url` vers une page PHP, texte brut, RGPD) ; **zones média** (musique, image sur un objet, page HTML en fenêtre ; ordre proposé : musique, image, page ; « on verra quand ») ; **images d'exposition** (mettre à jour sans refaire l'OAR : déposer des images dans un dossier avec un nommage, pistes dans le § 5).
8. **Intégrer les balises d'aperçu de partage à `glb2html.py`** (options `--og-title`, `--og-description`, `--og-image`, `--site-url`) : reporté ; il faudrait mémoriser les valeurs dans `default.json`, sinon `--update` renouvelle la coquille « modifiée à la main » et efface les balises (manuel § 29.8).
9. **Mis de côté par Klaatou** : carte en damier adaptée à l'écran (`regions.json` avec deux fiches à la même place `x,y` passe en liste ; Ctrl+M en liste fait une colonne ; piste : colonnes d'après la largeur de l'écran, champ `layout`) ; **idées anciennes** : relayer seulement les visiteurs proches, présence en Worker Cloudflare, but final : sa maison numérisée reliée à Home Assistant.

**Rappels**
- Avant de promouvoir la démo : revoir `--log-ip raw` et `--history-days 0` (§ 2.2) ; limites du serveur (`--max-per-ip` 10 par défaut), modération par la console.
- Klaatou n'a pas accès à la configuration NAT de sa box : tout passe par Tailscale ; le fichier `hosts` de son PC sert à joindre la box par son nom.
- Un serveur lancé sans `--creators` accepte toutes les origines ; avec le fichier, une page d'une origine non déclarée est refusée (« refus | origine non déclarée : » avec l'origine exacte).
- Origine des lignes « requête http » et « requête illisible » : **élucidée** (29/10/2026) : sondages automatiques d'Internet (adresse d'hébergeur, hôte = IP publique, RDP `mstshash`) ; sans danger.
- Les « cloneurs » du tableau de fréquentation GitHub (plus de 1 000 clones en 14 jours pour quelques visiteurs) sont presque sûrement des robots (scanneurs de secrets, miroirs, indexeurs) ; l'outil de lecture web de l'assistant et ses clones comptent un peu aussi.

### Règles permanentes de documentation
Toute modification du manuel, des procédures ou de l'historique se fait dans les deux langues, puis `verif_trad.py` sur le couple modifié (0 erreur exigée) ; chaque entrée de `CHANGELOG.md` en français puis en anglais ; chaque lot ajoute sa ligne à `docs/fr/HISTORIQUE.md` et `docs/en/HISTORY.md` ; tout renommage ajoute l'ancien nom à `ANCIENS` dans `tests/samples.py` et au manuel § 27.11 ; tout champ JSON ajouté ou modifié va au manuel § 27 et dans `docs/samples/` ; `REFERENCE_OPTIONS.md` est régénéré par `gen_reference.py` après `python build.py`.

## 7. Limites connues et pièges

- **Non testé ici** : Windows, Edge, carte graphique réelle, la vraie capture de souris (les tests simulent `requestPointerLock`), une région en tuiles dans un sous-dossier, la conversion par convoar, les lignes PowerShell elles-mêmes (essayées sous Linux avec des chemins équivalents).
- **Edge de Klaatou en rendu logiciel, volontairement** (« Microsoft Basic Render Driver » dans le diagnostic) : sa carte graphique est réservée à son LLM. La lenteur des tuiles chez lui est donc attendue : ce n'est pas un bug à chercher. Le rendu léger (v42) vise ce cas ; ses valeurs préconisées n'ont pas été mesurées sur Edge. Constat de Klaatou avant la v42 : 2 s de délai à l'ouverture des fenêtres en vue globale, moins en promenade. Mesuré dans Chromium (SwiftShader) : au repos en vue globale, 0 rendu par seconde, et l'ouverture d'une fenêtre ne déclenche aucun rendu ; seuls la mer animée (`core.js`, boucle de rendu) et la présence d'autres visiteurs (`presenceTick`) forcent un rendu continu. La cause exacte chez Klaatou reste à lire dans la ligne « Images rendues par seconde » du diagnostic.
- **Non essayé du tout** : Firefox et Safari (ne plus les redemander à Klaatou), Edge pour les derniers lots (icône, souris, G, carte), le redémarrage de la VM (`reboot`) et le test `tmux kill-server` du service, un vrai téléphone, `wss://` hors de Funnel, un domaine à soi.

**Bac à sable et tests**
- Tests de navigateur : **un seul à la fois**. Durées mesurées (rendu logiciel) : `v34` 2 min, `v33` 9 min, `modulaire` 4,3 min, `essais_presence` 1 min, `v36` 1,5 min, `v37` 1 min ; les autres de 5 à 70 s. Les longues séries : un script lancé par `setsid nohup bash script.sh &`, qui écrit un résumé lu ensuite. **Ne jamais reconstruire ni recloner le dossier pendant qu'une série tourne** (résultats faux, constaté le 29/10/2026).
- Variables : `THREE_DIR` (dossier `package` de `npm pack three@0.160.0`, `python build.py --vendor`), `WEB3D_LANG=fr`, `CHROMIUM` si besoin ; `WS_OLD` et `WS_OLD2` (anciennes versions de `websockets`, 14.2 et 15.0.1) : **sans elles, les sections « anciennes versions » de `v51_vides`, `v52_http` et `correctifs_v52` ne tournent pas** (compteurs plus bas : ce n'est pas une régression).
- **Fabriquer un patch** : lire les ancres dans un clone **intact** de `main` (jamais celui où le patch a déjà été appliqué), appliquer sur un clone frais, build, tests. Un patch qui remplace du texte doit retrouver **chaque** passage **exactement une fois**.
- `gen_reference.py` lit `dist\` : sans `python build.py` avant, il écrit un `REFERENCE_OPTIONS.md` vide ; il change aussi la date de génération.
- `verif_trad.py` : les extraits de code en ligne doivent être **identiques** en français et en anglais (par exemple `oublier <pseudo>` partout, pas `oublier <name>`).
- Un nom de clé i18n qui finit par `.other` est pris pour une forme de pluriel (`tests/i18n.py`).
- `pkill -f presence_server.py` dans le bac à sable tue aussi le shell qui l'exécute (la ligne de commande contient le motif).
- Outil de lecture web : il renvoie des copies en cache et ne lit que les adresses données par Klaatou ; pour l'état d'un dépôt, `git clone` ; pour un site, un `curl.exe -s "URL?v=N" | Select-String "…"` chez Klaatou. GitHub interdit la lecture automatique de `/stargazers` et `/forks`.
- Tests fragiles connus : `v31` (échoue depuis la v46, défaut du test), `v27`, `v46` et `v35` parfois (passent à la relance), `v33` dure 9 minutes (rendu logiciel, processeur ralenti).

**Klaatou et PowerShell**
- Commandes dans un **bloc de code isolé**, une par ligne, **jamais dans une phrase** (un point final copié casse la ligne), **chemins complets entre guillemets** (le chemin contient `&`), **sans variables** `$b`, `$d` ; une ligne de procédure doit marcher **relancée** et être suivie d'une ligne de contrôle ; après un patch : `if ($LASTEXITCODE -eq 0) { python build.py }` ; ne pas enchaîner deux commandes dont la deuxième ne doit pas partir si la première échoue.
- Klaatou n'a pas de presse-papiers dans la console de sa VM (pas d'extensions VMware) : pour coller du texte, il passe par SSH depuis PowerShell, ou on lui donne un **fichier** à envoyer par `scp` (c'est plus sûr qu'un long bloc collé).
- Les commandes PowerShell et Windows ne sont pas testables ici : le dire chaque fois (règle 20).
- Après un commit, vérifier que `git push` a abouti (GitHub Desktop montre sinon « Push origin »).
- Un commit de plusieurs fichiers : `git status --short` d'abord ; ses fichiers locaux `tools\glb-images-check.py` et `tools\glb-terrain-alt.py` ne sont pas suivis : ne pas les ajouter par mégarde.

**Réseau (machine du LLM de Klaatou)** : avant de proposer une configuration réseau, **demander où la page est hébergée et ce qui tourne déjà sur la machine**. Sur la machine du LLM (publié par `tailscale serve` vers `127.0.0.1:3080`) : ne jamais lancer `tailscale funnel` sans `--https=8443`, ne jamais lancer `tailscale funnel reset`. Le serveur public de présence est sur la **VM**, une machine Tailscale distincte : il n'y a pas de conflit. Klaatou laisse volontairement Edge en rendu logiciel pour garder sa carte graphique à son LLM : ne pas lui suggérer l'accélération matérielle. Sur un appareil où Tailscale est actif, le navigateur peut bloquer la présence quand la page vient d'une autre adresse : tester depuis un téléphone où Tailscale est coupé, ou `tailscale down` sur le PC le temps de l'essai, puis `tailscale up`.

**Observations non élucidées** : un client de test sans `uid` ni `spectator` dans son `hello` sort aussitôt de la salle (la vraie page envoie les deux) ; bips de `carte.html` sans le focus (non mesuré : le script ne teste ni focus ni visibilité ; remède possible, non fait : cadencer les relevés depuis un Web Worker, à essayer ici avant tout code).
