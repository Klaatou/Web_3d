# Web 3d : vue d'ensemble en une page

*État au 08/11/2026, version 1.8.0 (dernière publication : 1.8.0, le 08/11/2026).*

Une région OpenSim (sauvegarde `.oar`) devient une **page web 3D** où l'on se promène, sans rien installer. Dépôt : `github.com/Klaatou/Web_3d` (licence MIT). Cette page dit où on en est ; le détail est dans le manuel, l'état technique dans `REPRISE.md`.

**Questions, aide, nouvelles** : [serveur Discord](https://discord.gg/BDG9r5gXwr).

## 1. Ce qui marche aujourd'hui

- **Fabriquer** : `tools/oar2glb.py` (OAR vers GLB), `tools/glb2tiles.py` (découpe les régions énormes en tuiles et vue d'ensemble), `glb2html.py` (la page) ; `extraire_batiments.py` et `iar2oar.py` (sortent d'un OAR ou d'un IAR un GLB par groupe d'objets) ; `web3d_gui.py` (ouvre tous ces outils dans une fenêtre, avec l'aide des options et des raccourcis Windows) ; `python build.py` assemble tout dans `dist\`.
- **Se promener** : marche, course, saut, vol ; vue subjective, troisième personne, caméra libre ; collisions ; arrivées nommées, zones, portails vers une autre région ; commandes à l'écran et mode tactile.
- **Être plusieurs** : le serveur de présence (`presence_server.py`) : avatars, chat, journal des visites, créateurs accueillis (`--creators`), modération en console.
- **Relier les mondes** : la carte des mondes (`regions.json`), la page `carte.html` avec les visiteurs en direct et la surveillance des arrivées (son et repère), `--scan-sites` pour construire la liste depuis le dossier des sites ; `diag_carte.py` dit pourquoi la carte n'affiche pas les pseudos.
- **Régler** : la fenêtre Réglages (haute résolution, rendu léger, mer, sons, disposition des fenêtres) ; français et anglais.
- **Images d'exposition** : une zone `image` plaque une image sur un mur ; on dépose les fichiers dans le sous-dossier `medias` de la région, sans refaire la conversion ni passer par OpenSim ; légende dans le nom du fichier ou dans un fichier `.txt` ; une zone image peut ouvrir une page au clic (`link`), et une case des Réglages affiche les numéros des zones pour repérer les emplacements.
- **Animations, liens, à propos** : un GIF animé s'anime dans la page ; les zones `url` et `image` ouvrent aussi un lien `hop://` (monde virtuel) ; un panneau « À propos de la région » s'ouvre à l'entrée (touche `?`).
- **Paquets prêts à l'emploi** : `galerie-photos.zip` (galerie de 30 photos en 3D) et `region-simple.zip` (une région à partir d'un GLB), à télécharger sur la page des versions ; chacun s'ouvre d'un double-clic (Windows, macOS) ou d'une commande (Linux), avec un serveur de présence facultatif ; sources dans `paquets/`.
- **Démo en ligne** : `https://klaatou.github.io/Web_3d_demo/` (plusieurs régions reliées par des portails, carte des mondes, présence).

## 2. Ce qui a été essayé, et ce qui ne l'a pas été

- **Essayé** : Chromium (tests automatiques), Edge et le téléphone de Klaatou (« un peu encombré sur un petit écran, mais ça marche »), la région de référence de 1 024 x 1 024 m en 106 tuiles, les derniers lots (icône, souris, touche G, carte, présence) sur la démo en ligne, le serveur de présence public sur une VM Debian 13 (Tailscale Funnel, page sur GitHub Pages, visiteur extérieur, redémarrages de la VM et du service), la zone `image` (tests automatiques ; par Klaatou sur une vraie région : les images s'affichent, le choix du dossier de la région marche) ; par Klaatou, `extraire_batiments.py` sur une vraie région, `iar2oar.py` sur un vrai IAR (puis convoar et Blender), `diag_carte.py` contre un vrai serveur de présence, les GIF animés sous Windows et sous Firefox, et `web3d_gui.py` sous Windows (la fenêtre, la liste des outils, les raccourcis avec l'icône du projet).
- **Essayé par un tiers (NightshadeCeres)** : Firefox 159.0.1 sous macOS Ventura 13.7.8, avec le lanceur `.command` du paquet `region-simple` : la région s'affiche (seul résultat rapporté). Le paquet `galerie-photos`, même lanceur, n'a pas été essayé séparément.
- **Non essayé** : Safari, Firefox sous Windows et Linux ; Caddy et Cloudflare Tunnel (voies B et C) ; la voie D avec Apache ; `wss://` hors de Funnel ; un domaine à soi ; le son réel (les tests le simulent) ; un onglet de `carte.html` gardé longtemps en arrière-plan ; la zone `image` dans une région en tuiles ; le vrai sélecteur de dossier de l'éditeur sous Windows et Edge ; l'animation des GIF sous Safari (essayée sous Chromium, Windows et Firefox) ; l'icône « Réalisé avec Web_3d » sous Windows, Firefox, Safari et sur un vrai écran tactile.

## 3. Ce qui reste à faire

1. **Nom de domaine** : pour le site de présentation et pour un nom stable du serveur de présence.
2. **Page de présentation** : GIF cliquable vers la démo, bouton pour l'essayer, contact, procédure de retrait, mentions légales.
3. **Option pour retirer l'icône « Réalisé avec Web_3d »** (clé `credit`) : à décider dans quelques semaines.
4. **Idées** : zones média restantes (musique, page), images en région en tuiles, insertion de GLB, livre d'or (facultatif, peut être externe) ; extraire chaque bâtiment d'un grand OAR en GLB séparé pour recomposer des régions (fait : `extraire_batiments.py`, la composition se fait dans Blender) ; méga-région (étude dans `docs/fr/ETUDE_MEGAREGION.md`, rien n'est codé) ; PNG et WebP animés.

## 4. Où lire quoi

- `README.md` : présentation et démarrage.
- `INDEX.md` : quel document lire pour quoi.
- Le manuel : tout le détail (zones, options, serveur, nouveautés par version).
- `REFERENCE_JSON.md` : le sens de chaque champ des fichiers JSON.
- Les procédures : pas à pas (publier, serveur, réseau).
- `REFERENCE_OPTIONS.md` : toutes les options des outils.
- `CHANGELOG.md` et l'historique : ce qui a changé et quand.
- `REPRISE.md` : l'état technique pour reprendre le travail.
