# Web 3d : vue d'ensemble en une page

*État au 25/10/2026, version v52.*

Une région OpenSim (sauvegarde `.oar`) devient une **page web 3D** où l'on se promène, sans rien installer. Dépôt : `github.com/Klaatou/Web_3d` (licence MIT). Cette page dit où on en est ; le détail est dans le manuel, l'état technique dans `REPRISE.md`.

## 1. Ce qui marche aujourd'hui

- **Fabriquer** : `tools/oar2glb.py` (OAR vers GLB), `tools/glb2tiles.py` (découpe les régions énormes en tuiles et vue d'ensemble), `glb2html.py` (la page) ; `python build.py` assemble tout dans `dist\`.
- **Se promener** : marche, course, saut, vol ; vue subjective, troisième personne, caméra libre ; collisions ; arrivées nommées, zones, portails vers une autre région ; commandes à l'écran et mode tactile.
- **Être plusieurs** : le serveur de présence (`presence_server.py`) : avatars, chat, journal des visites, créateurs accueillis (`--creators`), modération en console.
- **Relier les mondes** : la carte des mondes (`regions.json`), la page `carte.html` avec les visiteurs en direct et la surveillance des arrivées (son et repère), `--scan-sites` pour construire la liste depuis le dossier des sites.
- **Régler** : la fenêtre Réglages (haute résolution, rendu léger, mer, sons, disposition des fenêtres) ; français et anglais.

## 2. Ce qui a été essayé, et ce qui ne l'a pas été

- **Essayé** : Chromium (tests automatiques), Edge et le téléphone de JJ (« un peu encombré sur un petit écran, mais ça marche »), la région de référence de 1 024 x 1 024 m en 106 tuiles.
- **Non essayé** : Firefox et Safari ; la voie D (VM Linux, Tailscale Funnel, Apache) ; `wss://` derrière Funnel ; un créateur depuis une autre origine ; le son réel (les tests le simulent) ; un onglet de `carte.html` gardé longtemps en arrière-plan.

## 3. Ce qui reste à faire

1. **Essai depuis la VM** : accès par Tailscale, et un créateur d'une autre origine (`--creators`).
2. **Note pour les créateurs** accueillis sur le serveur de présence, écrite après cet essai.
3. **Souris** : ne la capturer que volontairement (bouton ou G), en retirant la capture au clic.
4. **Démo publique** : région candidate Hobbit (petite, elle s'ouvre seule) ; configuration sans adresse IP ; GitHub Pages n'exécute pas de PHP.
5. **Numérotation** : passer à `1.0.0` après les essais ci-dessus (proposé, pas décidé).
6. **Release GitHub** avec notes en anglais (à décider).
7. **Idées** : afficher une image ou une page sur un objet, jouer une musique en entrant dans une zone (étudié, pas commencé) ; livre d'or (facultatif, peut être externe).

## 4. Où lire quoi

- `README.md` : présentation et démarrage.
- Le manuel : tout le détail (zones, options, serveur, nouveautés par version).
- Les procédures : pas à pas (publier, serveur, réseau).
- `REFERENCE_OPTIONS.md` : toutes les options des outils.
- `CHANGELOG.md` et l'historique : ce qui a changé et quand.
- `REPRISE.md` : l'état technique pour reprendre le travail.
