# Web 3d : vue d'ensemble en une page

*État au 31/10/2026, version 1.1.0.*

Une région OpenSim (sauvegarde `.oar`) devient une **page web 3D** où l'on se promène, sans rien installer. Dépôt : `github.com/Klaatou/Web_3d` (licence MIT). Cette page dit où on en est ; le détail est dans le manuel, l'état technique dans `REPRISE.md`.

## 1. Ce qui marche aujourd'hui

- **Fabriquer** : `tools/oar2glb.py` (OAR vers GLB), `tools/glb2tiles.py` (découpe les régions énormes en tuiles et vue d'ensemble), `glb2html.py` (la page) ; `python build.py` assemble tout dans `dist\`.
- **Se promener** : marche, course, saut, vol ; vue subjective, troisième personne, caméra libre ; collisions ; arrivées nommées, zones, portails vers une autre région ; commandes à l'écran et mode tactile.
- **Être plusieurs** : le serveur de présence (`presence_server.py`) : avatars, chat, journal des visites, créateurs accueillis (`--creators`), modération en console.
- **Relier les mondes** : la carte des mondes (`regions.json`), la page `carte.html` avec les visiteurs en direct et la surveillance des arrivées (son et repère), `--scan-sites` pour construire la liste depuis le dossier des sites.
- **Régler** : la fenêtre Réglages (haute résolution, rendu léger, mer, sons, disposition des fenêtres) ; français et anglais.
- **Images d'exposition** : une zone `image` plaque une image sur un mur ; on dépose les fichiers dans le sous-dossier `medias` de la région, sans refaire la conversion ni passer par OpenSim ; légende dans le nom du fichier ou dans un fichier `.txt`.
- **Démo en ligne** : `https://klaatou.github.io/Web_3d_demo/` (deux régions reliées par des portails, carte des mondes, présence).

## 2. Ce qui a été essayé, et ce qui ne l'a pas été

- **Essayé** : Chromium (tests automatiques), Edge et le téléphone de Klaatou (« un peu encombré sur un petit écran, mais ça marche »), la région de référence de 1 024 x 1 024 m en 106 tuiles, les derniers lots (icône, souris, touche G, carte, présence) sur la démo en ligne, le serveur de présence public sur une VM Debian 13 (Tailscale Funnel, page sur GitHub Pages, visiteur extérieur, redémarrages de la VM et du service), la zone `image` (tests automatiques ; par Klaatou sur une vraie région : les images s'affichent, le choix du dossier de la région marche).
- **Non essayé** : Firefox et Safari ; Caddy et Cloudflare Tunnel (voies B et C) ; la voie D avec Apache ; `wss://` hors de Funnel ; un domaine à soi ; le son réel (les tests le simulent) ; un onglet de `carte.html` gardé longtemps en arrière-plan ; la zone `image` dans une région en tuiles ; le vrai sélecteur de dossier de l'éditeur sous Windows et Edge.

## 3. Ce qui reste à faire

1. **Nom de domaine** : pour le site de présentation et pour un nom stable du serveur de présence.
2. **Page de présentation** : GIF cliquable vers la démo, bouton pour l'essayer, contact, procédure de retrait, mentions légales.
3. **Release GitHub** de la 1.1.0 : étiquette `v1.1.0` et notes en anglais (entrée « 1.1.0 » de `CHANGELOG.md`), à poser par Klaatou.
4. **Idées** : zones média restantes (musique, page), images en région en tuiles, insertion de GLB, livre d'or (facultatif, peut être externe) ; extraire chaque bâtiment d'un grand OAR en GLB séparé pour recomposer des régions (un script existe, hors dépôt).

## 4. Où lire quoi

- `README.md` : présentation et démarrage.
- Le manuel : tout le détail (zones, options, serveur, nouveautés par version).
- Les procédures : pas à pas (publier, serveur, réseau).
- `REFERENCE_OPTIONS.md` : toutes les options des outils.
- `CHANGELOG.md` et l'historique : ce qui a changé et quand.
- `REPRISE.md` : l'état technique pour reprendre le travail.
