# Retrouver chaque version

Les premières versions ont toutes été faites le 18/10/2026. Cet historique a été **reconstitué après coup** à partir des sauvegardes de sources faites pendant la journée ; il est fidèle sur ce qui existe, mais incomplet.

## Ce qu'il faut savoir

- Chaque ligne ci-dessous est un état des sources (dossier `src/`) à la fin d'une série de modifications. La date est au format jj/mm/aaaa. L'heure (heure de Paris) n'est renseignée que pour les entrées reconstituées ; à partir de v19, une ligne est ajoutée à chaque livraison (voir « Livraison d'une version » dans `CLAUDE.md`).
- **Avant 12:05, rien n'a été conservé** : le travail avait commencé vers 09:28 (première demande), avec l'export de base, le trou de mer et la haute résolution.
- Les numéros de version ne s'affichent dans les pages qu'à partir de v5 (vers 16:13). Les étiquettes **v14 à v18** sont posées ; v19 (commit `5632bd5`) et les suivantes sont à poser avec la commande donnée à chaque livraison. v14 a été vérifié octet pour octet contre les fichiers v14 fournis au projet ; v15 à v17 sont les états relevés au début de chaque version suivante ; v18 est le dernier état.
- Les messages de chaque entrée ont été écrits après coup, d'après les différences entre états et l'ordre des demandes.
- Les fichiers fabriqués (`dist/`) ne sont pas dans le dépôt. Seul le dernier état contient `build.py` : pour refabriquer une ancienne version, récupérer ses `src/` et les fabriquer avec le `build.py` du dernier état.
- L'auteur des entrées est `Klaatou` par commodité ; les prochaines entrées prendront l'identité configurée sur ton poste.

## Historique

| Date | Heure | Étiquette | Contenu |
|---|---|---|---|
| 18/10/2026 | 12:05 |  | Promenade à la première personne (touche F) : première ébauche du noyau |
| 18/10/2026 | 12:44 |  | Collisions par grille et éléments traversables |
| 18/10/2026 | 13:23 |  | Nom de l'élément au clic ; visiteurs en temps réel |
| 18/10/2026 | 13:50 |  | Viewer : premier état conservé |
| 18/10/2026 | 14:28 |  | Chat : bulles et durée réglable ; premiers états du script et du gabarit de page |
| 18/10/2026 | 14:54 |  | Serveur : limites de débit du chat, historique, proxy |
| 18/10/2026 | 14:55 |  | Zones : portails, panneaux lien web et Home Assistant, points d'arrivée |
| 18/10/2026 | 15:42 |  | Viewer : éditeur de zones et profils public/perso |
| 18/10/2026 | 16:32 |  | Vue globale : visiteurs en promenade visibles (spectateur) |
| 18/10/2026 | 16:39 |  | Repère d'atterrissage au sol et choix du point d'arrivée |
| 18/10/2026 | 16:55 |  | Export : zones, profils et ligne de commande PowerShell |
| 18/10/2026 | 17:17 |  | Téléportation au double-clic fiable malgré le lag |
| 18/10/2026 | 17:55 |  | Losange des visiteurs masqué derrière les murs ; noms mémorisés |
| 18/10/2026 | 18:02 |  | Panneau de réglages pour les visiteurs |
| 18/10/2026 | 19:25 | v14 | v14 : zones rechargeables, éjection et bannissement |
| 18/10/2026 | 20:14 | v15 | v15 : carte des mondes (touche M) |
| 18/10/2026 | 20:52 | v16 | v16 : réglages mémorisés par fichier ; carte orientée X est / Y nord |
| 18/10/2026 | 21:04 | v17 | v17 : --register, page carte, vignette enregistrable, placement compact |
| 18/10/2026 | 21:20 |  | v18 : --settings, enregistrement sans .glb, cartes multi-sources |
| 18/10/2026 |  | v19 | v19 : mode modulaire (`--modular`, `--config-only`, case « Mode modulaire » du viewer), commit `5632bd5` |
| 18/10/2026 |  | v20 | v20 : mode modulaire universel (coquille identique pour toutes les régions, zones relues dans `<page>.zones.json` ou `zones.json`, export `.zip` du viewer, zones liées à un élément du modèle) |
| 19/10/2026 |  | v21 | v21 : correctif « Lier à un élément » (mode exclusif, boîte en coordonnées monde, mesh nommé touché, refus au-delà de 30 m, contour fil de fer) |
| 19/10/2026 |  | v22 | v22 : portail vers un point d'arrivée de la même région, mode d'emploi |
| 19/10/2026 |  | v23 | v23 : clic simple sans effet sur la cible, liaison au morceau cliqué (nom#index, limite 10 m), rotation de la région, mode d'emploi |
| 19/10/2026 |  | v24 | v24 : les liens se comportent comme sur le web (plus de cylindres dans la page exportée, marqueur au sol, infobulle au survol, option « Toujours afficher le nom »), mode d'emploi |
| 20/10/2026 |  | v25 | v25 : oar2glb.py, meshes riggés reconstruits depuis le .llmesh de l'OAR, prims invisibles et boîtes d'animesh retirés, --diag, --reperes, --keep-invisible, relance de convoar si des images manquent, mode d'emploi |
| 21/10/2026 |  | v26 | v26 : coquille unique en mode modulaire (`--shared-shell`, `index.html?region=NOM`, nom refusé sans requête réseau), export `.zip` du viewer en `index.html`, `oar2glb.py --version` fabriqué dans `dist/`, notes « régions énormes » |
| 21/10/2026 |  | v27 | v27 : repères des avatars empilés (nom, bulle de chat, losange) : la bulle n'est plus recouverte, `tests/v27.py` |
| 21/10/2026 |  | v28 | v28 : `tools/glb2tiles.py` (découpage d'un GLB énorme en tuiles autonomes, `--analyse`), `glb-stats.py` en fonctions communes, `tests/glb2tiles.py` |
| 22/10/2026 |  | v29 | v29 : oar2glb.py terrain complet des régions de plus de 256 m (patches depuis la carte de hauteurs, `--terrain`, `--terrain-patch`, `--terrain-seul`), glb2tiles.py `--exclure` et pause sans console, `tests/terrain.py` |
| 22/10/2026 |  | v30 | v30 : la coquille charge une région en tuiles (`tiles` dans `X.config.json`, rayon, hystérésis, budget Mo / triangles, grille de collision par tuile, sol bloqué tant que la tuile n'est pas prête, `?rayon=`), `glb2html.py --tiles`, `glb2tiles.py` explique les « octets gagnés » à 0, `tests/tuiles.py` |
| 22/10/2026 |  | v31 | v31 : `glb2tiles.py` remplace les images vides, invalides ou tronquées par un PNG gris (une par tuile) et écrit une vue d'ensemble légère `X.overview.glb` (`--vue-ensemble-seule`, `--ov-*`) ; la coquille la charge avant les tuiles, masque chaque cellule quand sa tuile est affichée, cadre toute la région ; sortie de promenade : cible sous l'avatar, même décalage de caméra ; anciennes tuiles supprimées ; `tests/v31.py`, `tests/glbfab.py` |
| 22/10/2026 |  | v32 | v32 : le viewer ouvre une région en tuiles (dossier choisi ou glissé, `?tuiles=`, repère d'origine, vue d'ensemble, placement de zones sur les tuiles chargées, export `X.zones.json` et commande `--tiles`), coordonnées du point visé et de la cible avec copie, position affichée dans le panneau d'aide de la coquille, zones liées à un objet en mode tuiles (`extras.ref` / `extras.box` écrits par `glb2tiles.py`, `--sans-references`), `tests/v32.py` |
| 22/10/2026 |  | v33 | v33 : démarrage avec une arrivée corrigé (référence du chargeur = arrivée, tuiles de l'arrivée d'abord, texte « Chargement du sol… » et plus d'écran noir muet, journal par tuile), arrivée `default` et retour (R), `#pos=` et « Aller à », vol et trois vues, chat persistant / enregistré / pseudo cité / complétion, couleur d'avatar, `--zone-marker`, `--show-spawns`, `--fly`, zones enregistrées dans le dossier de la région, `tests/v33.py` |
| 22/10/2026 |  | v34 | v34 : aide sélectionnable et bloc d'état séparé (vue, mode, souris, position), zone de survol des marqueurs au rayon de l'anneau, vol (Page Haut / Page Bas, atterrissage automatique, bouton), souris libre après Échap (G, bouton), couleur en direct, `glb2html.py --maj`, lien personnel `#name=…&key=…`, pseudo de la page carte, `tests/v34.py` |
| 22/10/2026 |  | v35 | v35 : aide en groupes et panneaux repliables, commandes à la Firestorm (F / P / E / Page Haut / course / M / Ctrl+M / Fin / Alt), vol par appui long, troisième personne (caméra qui orbite, avatar qui se tourne vers sa marche), infobulles de zones à 40 m (`--zone-info-dist`), copie sans contexte sécurisé, molette et orbite de la caméra libre, `--maj` avec la carte des mondes |
| 23/10/2026 |  | v36 | v36 (lot A) : F et P entrent et sortent de la promenade, E redevient la touche des zones, vol par Début / Page Haut maintenu / Espace, disposition AZERTY / QWERTY (lettres réelles dans l'aide, M par la lettre imprimée), aide et informations en trois temps, arrivée occupée (décalage du nouvel arrivant), repères de portail en cône (`--zone-cone`, T), sons d'arrivée / départ / citation avec volume, « Copier ma position » (URL / xyz) et « Aller à » avec `#pos=`, `tests/v36.py` ; lots B à D : interface de la page, du viewer et des outils Python en français et en anglais (`src/i18n/*.json`, réglage « Langue / Language », `--lang`, `WEB3D_LANG`), `REFERENCE_OPTIONS.md` bilingue, `README.en.md`, `tests/i18n.py`, `v36_lang.py`, `v36_viewer_lang.py`, `tools_lang.py`, `doc_options.py` |
| 23/10/2026 |  | v37 | v37 : indicateur de course, boussole (`--compass`, `--north`), cône de taille constante avec distance (`--zone-info-dist` 150 m, jusqu'à 500), arrivée occupée autour de l'occupant et tournée vers lui, pseudo cité clignotant jusqu'à la première action, hash séparé par & ou #, fenêtres Aide / Informations redimensionnables, touche O (Réglages) ; historique du chat (`--history` 200, `--history-file`, `--history-days`, message `history`, bouton « Messages plus anciens », non lus, citations) ; région par défaut (`default.json`, `--default`), `--lib-url`, sous-dossiers (`?region=a/b/nom`) ; `--help` des outils avec nom et version |
| 23/10/2026 |  | v38 | v38 : manuel, procédures et historique traduits en anglais (`docs/en/`), documents français dans `docs/fr/` (`MODE_EMPLOI.md` devient `MANUEL.md`), `README.md` en anglais et `README.fr.md`, `verif_trad.py` |
| 23/10/2026 |  | v39 | v39 : bouton « Copier le diagnostic » (page et viewer : version, carte graphique, rendu, tuiles, état, présence, dernières erreurs ; adresses masquées), `tests/v39.py` |
| 24/10/2026 |  | v40 | v40 : fenêtre Arrivées (touche L, téléportation), bouton « Recentrer la vue », lien « Manuel complet », bulle du diagnostic, `tests/v40.py` |
| 24/10/2026 |  | v41 | v41 : bulles des fenêtres H, I, L et Réglages, fenêtres déplaçables par le titre (piles de gauche et de droite, libres), disposition retenue et fichier `disposition.json`, `tests/v41.py` |
| 24/10/2026 |  | v42 | v42 : rendu léger (case et « Réglages fins… » : résolution, images par seconde, vue d'ensemble seule, rayon des tuiles, anticrénelage ; `--light`), Réglages plus étroite, `tests/v42.py` |
| 24/10/2026 |  | v43 | v43 : manuel § 27 « Référence des fichiers JSON », exemples dans `docs/samples/`, `tests/samples.py`, noms en anglais (options, valeurs, clés, adresses ; anciens noms acceptés), `gen_reference.py` sans pause |
| 24/10/2026 |  | v44 | v44 : derniers noms en anglais (`gen_reference.py`, `verif_trad.py`, messages `[update]`, noms d'exemple de l'aide, menu « Marqueur des portails et zones libres » du viewer), contrôle automatique des anciens noms dans `tests/samples.py`, historique complété (v38 à v44) |
| 24/10/2026 |  | v45 | v45 : la page dit pourquoi la connexion de présence s'est fermée (`tests/v45.py`, manuel § 28), diagnostic « Connexion de présence » ; procédures § 11 complétées (Tailscale Funnel essayé, voie D VM Linux + Funnel + Apache, cas d'un autre service déjà publié) ; dossier `lib` de la coquille réglé par une seule ligne (`const LIB`), `--update` la garde, `dist/index.html` fabriqué par `build.py`, page d'essai `tests/essai_importmap.html` (`tests/v45_lib.py`) |
| 25/10/2026 |  | v46 | v46 : commandes à l'écran (manuel § 29) : ligne d'état toujours visible, flèches 3 x 3 en promenade (avancer, reculer, tourner, pas de côté, Courir, monter et descendre en vol) et en vue globale (déplacer, tourner, rapprocher, recentrer), touche K et bouton « Flèches (K) » ; mode tactile (colonne de boutons, menu, plein écran, fenêtres réduites avec ✕, glisser du doigt pour regarder, chat tactile, écran à l'horizontale, bulle par appui long) ; bulles sur tous les boutons ; une coquille pour tout un site (§ 29.8) ; `tests/v46.py` |
| 25/10/2026 |  | v47 | v47 : carte des mondes (manuel § 30) : tuile « N visiteurs · N en promenade » et bulle au survol, adresse facultative (`showUrl`, case « Afficher les adresses »), `regions.json` avec en-tête conservé par `--register`, `visitors` dans la réponse du serveur de présence, `dist/carte.html` universelle ; `tests/v47.py` |
| 25/10/2026 |  | v48 | v48 : journal des visites (manuel § 31) : le serveur de présence note chaque visite dans un fichier à part (`--visits`, sans IP ; `--visits-days`, `--visits-names`), commande `visits-key ROOM` ; le créateur ouvre sa page avec `#visits` et la clé : résumé par jour, visites des 30 derniers jours, CSV ; `tests/v48.py` |

## Commandes utiles
| 25/10/2026 |  | v49 | v49 : `glb2html.py --scan-sites` met à jour `regions.json` depuis le dossier des sites (fiches, vignettes `NOM.jpg`, rien supprimé), manuel § 32 ; `tests/v49.py` |
| 25/10/2026 |  | v50 | v50 : viewer, carte des mondes : import et export de `regions.json` avec en-tête, champs des fiches gardés, « Ajouter » sur place (manuel § 33) ; `tests/v50.py` ; README, procédures § 4 et § 7, `CLAUDE.md` mis à jour |

- Voir l'historique : `git log --oneline --decorate`
- Voir ce qui a changé dans une version : `git show v16 --stat`
- Retrouver les sources d'une version : `git switch --detach v14` (puis `git switch main` pour revenir)
- Comparer deux versions : `git diff v16 v17 --stat`
