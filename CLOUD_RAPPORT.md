# Rapport de la session cloud : refonte du manuel

*Branche `claude/manuel` (point de départ : `main` 1.4.10, commit d92045b). L'ancien rapport (lots 1.4.4 à 1.4.6) reste dans l'historique git. Aucun fichier de code, `VERSION`, `CHANGELOG.md` ou `VERSIONS.json` modifié.*

## État des étapes

| Étape | État | Contrôles | Reste |
| --- | --- | --- | --- |
| 1. Table de correspondance | faite | 228 titres, chacun placé une fois (script) | |
| 2. Manuel français | faite | script d'assemblage : 228 titres placés une fois ; codes en ligne comparés (ci-dessous) ; blocs de code : 7 sur 7 ; renvois `§` renumérotés automatiquement (aucun non résolu) | relecture humaine des chapitres 1 et 2 (textes neufs) |
| 3. Manuel anglais | faite | `python verif_trad.py docs/fr/MANUEL.md docs/en/MANUAL.md` : OK, 0 erreur, 9 avertissements (glossaire, comme avant) ; 205 titres, 67 tableaux, 7 blocs de code, 2 331 codes en ligne identiques | relecture humaine des chapitres 1 et 2 anglais |
| 4. Renvois des autres documents | faite | `verif_trad.py` OK (0 erreur) sur les 6 paires ; `tests/samples.py` : voir ci-dessous | décisions de Klaatou sur les points « À signaler » |

## Plan retenu

Les 12 chapitres du brief, plus un 13e : l'annexe (tableau « version → contenu », renvois à `HISTORIQUE.md` et `CHANGELOG.md`). Écarts au brief, justifiés :

- Chapitre 12 « Dépannage » : le tableau de l'ancien § 13 et les trois parties « Si quelque chose ne va pas » (OAR, découpage, tuiles dans la page).
- L'ancien § 16 (fichiers JSON d'une région modulaire) va au chapitre 11 avec le § 27 ; sa partie « Coquille unique » va au chapitre 6.
- Les titres « Nouveautés de la vNN » disparaissent ; leurs sous-sections vont dans leur thème. Les textes d'introduction des conteneurs 37 et 38 et les § 36.5, 37.6, 37.8 vont en annexe.
- Les notes « Non testé » / « Essayé » gardent leur thème et reçoivent la version entre parenthèses.
- Seules suppressions : les 13 listes « Tests de la vNN » (y compris « Test de la coquille », ancien § 28.8, qui est une liste de tests) et les titres-conteneurs.

## Étape 2 : manuel français

Méthode : le nouveau `docs/fr/MANUEL.md` est assemblé par script à partir des blocs de l'ancien (aucune réécriture des faits), dans l'ordre du plan, avec renumérotation des titres et des renvois `§`. Textes neufs : titre, résumé, chapitres 1 et 2 (tirés de `GUIDE.md`, `README.fr.md` et de l'ancien manuel), une phrase d'introduction par chapitre (pointeurs seulement), l'annexe (tableau généré à partir des titres). Cinq renvois qui visaient des chapitres « Nouveautés » supprimés (`§ 25`, `§ 26`, `§ 29`, `§ 33`, `§ 34`) pointent désormais vers la sous-section précise (ancien 25.3, 26.1, 29.3, 33.1, 34.2).

Contrôle « rien ne se perd » : 1 108 codes en ligne dans l'ancien, 1 086 dans le nouveau ; **28 absents, tous dans des listes « Tests de la vNN » supprimées** : `--zone-info-dist 40`, `tests/h37.py`, `tests/v37.py`, `v33.py`, `v35.py`, `v36.py` (ancien § 22.10) ; `tests/v39.py` (23.2) ; `tests/v40.py` (24.4) ; `tests/v35.py`, `tests/v36.py`, `tests/v41.py` (25.4) ; `tests/v42.py` (26.7) ; `tests/v46.py` (29.9) ; `tests/v47.py` à `tests/v51.py` (30.6 à 34.7) ; `.sep`, `POLL_ALERT_MS`, `POLL_MS`, `WS_OLD2`, `tests/i18n.py`, `tests/v52.py`, `tests/v52_http.py`, `tests/v52_renom.py` (35.7). Blocs de code : 7 dans l'ancien, 7 dans le nouveau, identiques.

## Étape 3 : manuel anglais

Même assemblage, mêmes positions de titres, à partir de l'ancien `docs/en/MANUAL.md` (les textes anglais existants sont repris tels quels) ; textes neufs traduits à la main (titre, résumé, chapitres 1 et 2, introductions, annexe). Le tableau de l'annexe renvoie à `HISTORIQUE.md` côté français et à `HISTORY.md` côté anglais, comme dans les deux anciens manuels.

## Étape 4 : renvois

Fichiers modifiés (français et anglais, mêmes lignes) : `GUIDE.md`, `PROCEDURES.md`, `CREATEURS.md` / `CREATORS.md`, `README.fr.md` / `README.md`, et, en plus de la liste du brief, `docs/samples/README.fr.md` et `docs/samples/README.md` (renvois `§ 27.x` et `§ 34`). Méthode : un script ne change que les `§` qui visent le manuel (mot « manuel », `MANUEL.md`, `MANUAL.md` juste avant, ou ligne reconnue à la main) ; les renvois à `GUIDE.md`, `PROCEDURES.md`, aux procédures simples et à la note créateurs ne sont pas touchés. Relu à l'œil sur le diff. Les plages (`§§ 3 à 12`, `§§ 3 à 8`, `§§ 2, 21 et 22`) deviennent « chapitre 5 » ou « chapitre 7 (touches) et §§ 7.49, 2.1 et 2.2 (langue) ». Les renvois à un ancien chapitre « Nouveautés » supprimé pointent vers un chapitre ou une sous-section (ancien 30 vers chapitre 9, 31 vers chapitre 10, 32 vers § 9.9). `PROCEDURES_SIMPLES.md` / `SIMPLE_PROCEDURES.md` : aucun renvoi au manuel, rien changé.

Contrôles : `python verif_trad.py` sans erreur sur chaque paire (`MANUEL`/`MANUAL`, `GUIDE`, `PROCEDURES`, `PROCEDURES_SIMPLES`/`SIMPLE_PROCEDURES`, `CREATEURS`/`CREATORS`, `README.fr`/`README`, `docs/samples/README*`).

### À signaler (rien n'a été modifié pour ces points)

1. **`tests/samples.py` : un échec de plus qu'avant, dû au nouveau plan.** Sur `main`, un seul échec (le téléchargement de three.js, bloqué ici par le proxy). Maintenant un second : la ligne 31 retire du manuel le tableau des anciens noms par l'expression `### 27\.11.*?(?=\n## |\Z)`, et ce tableau est désormais au § 11.11. Correction d'une ligne dans le test : remplacer `27\.11` par `11\.11` (le brief interdit de toucher au code ; je n'ai pas modifié `tests/`).
2. **Deux commentaires du code citent le manuel** (non modifiés) : `src/gen_tpl.py:881` « `docs/fr/MANUEL.md § 17 bis` » devient « chapitre 8 » ; `tools/oar2glb.py:1411` « palette ... `docs/fr/MANUEL.md § 15` » devient « chapitre 3 » (aucune mention de « palette » dans le manuel actuel : à vérifier).
3. **Documents qui citent encore les anciens numéros** (hors liste du brief, non modifiés) : `docs/fr/HISTORIQUE.md` et `docs/en/HISTORY.md` (20 renvois chacun, historiques par nature), `REPRISE.md` (12 renvois). La correspondance ancien → nouveau est dans la table de l'étape 1.
4. Le numéro du manuel dans le titre est « 1.4.10 » (le titre d'avant disait « 1.1.0 »).
5. `tests/doc_options.py` : non lancé (échoue déjà sur `main`, consigne du brief).

## Révision après relecture de Klaatou (03/11/2026)

- « leur défaut » devient « les valeurs par défaut de leurs paramètres » (résumé et chapitre 2, FR et EN).
- Chapitre 1 : nouveau § 1.1 « vocabulaire » (région, OAR, GLB, tuiles, viewer, zone, page autonome, page avec coquille, présence, carte des mondes), puis § 1.2 (trois chemins) et § 1.3 (où chercher).
- Chapitre 2 : tableau des fichiers de `dist` en mots simples, sans les deux sections sur les langues, déplacées au chapitre 7 (§ 7.49 à 7.51), après « Langue de la page ».
- Chapitre 5 : l'introduction dit tout ce que fait le viewer (regarder, régler, poser les zones, capturer la vignette, exporter), pas seulement les zones.
- `X.glb`, `X.oar`, `X.tiles.json`, `X.config.json`… deviennent `NOM.glb`, `NOM.oar`… dans tout le manuel (FR et EN) ; `NOM` est défini au § 1.1. `X.Y.Z` (schéma de version) et `three-X` sont inchangés.
- Renvois des autres documents recalculés avec la nouvelle numérotation du chapitre 7. Contrôles refaits : `verif_trad.py` 0 erreur sur toutes les paires ; codes en ligne absents : toujours les 28 des listes « Tests » (après le remplacement `X` vers `NOM` des deux côtés).

## Étape 1 : table de correspondance

| Titre de l'ancien manuel | Où il va |
| --- | --- |
| 1. La règle qui explique 90 % des pannes | chapitre 5 « Poser les zones (le viewer) », § 5.1 |
| 2. Les touches | chapitre 7 « La page côté visiteur », § 7.1 |
| &nbsp;&nbsp;Clic et double-clic (vue globale du viewer) | chapitre 5 « Poser les zones (le viewer) », § 5.3 |
| 2 bis. Ce que voit le visiteur : les liens se comportent comme sur le web | chapitre 7 « La page côté visiteur », § 7.13 |
| 3. Poser une zone | chapitre 5 « Poser les zones (le viewer) », § 5.2 |
| 4. Point d'arrivée | chapitre 5 « Poser les zones (le viewer) », § 5.4 |
| 5. Portail vers un autre endroit de la même région | chapitre 5 « Poser les zones (le viewer) », § 5.5 |
| 6. Portail vers une autre région | chapitre 5 « Poser les zones (le viewer) », § 5.6 |
| 7. Panneaux | chapitre 5 « Poser les zones (le viewer) », § 5.7 |
| &nbsp;&nbsp;Lien web | chapitre 5 « Poser les zones (le viewer) », § 5.7.1 |
| &nbsp;&nbsp;Commande Home Assistant | chapitre 5 « Poser les zones (le viewer) », § 5.7.2 |
| 8. Déclenchement, forme et taille | chapitre 5 « Poser les zones (le viewer) », § 5.8 |
| 9. Lier une zone à un élément du modèle | chapitre 5 « Poser les zones (le viewer) », § 5.9 |
| 10. Zones privées | chapitre 5 « Poser les zones (le viewer) », § 5.10 |
| 11. Carte des mondes | chapitre 9 « Carte des mondes », § 9.1 |
| &nbsp;&nbsp;Rotation de la région | chapitre 5 « Poser les zones (le viewer) », § 5.13 |
| 12. Publier les changements | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.16 |
| 13. Dépannage | chapitre 12 « Dépannage » |
| 14. Réglages mémorisés | chapitre 5 « Poser les zones (le viewer) », § 5.16 |
| 15. Convertir un OAR en GLB (`tools/oar2glb.py`) | chapitre 3 « Convertir un OAR en GLB (`tools/oar2glb.py`) » |
| &nbsp;&nbsp;Les commandes (PowerShell, une seule ligne) | chapitre 3 « Convertir un OAR en GLB (`tools/oar2glb.py`) », § 3.1 |
| &nbsp;&nbsp;Les options | chapitre 3 « Convertir un OAR en GLB (`tools/oar2glb.py`) », § 3.2 |
| &nbsp;&nbsp;Terrain complet des régions de plus de 256 m (v29) | chapitre 3 « Convertir un OAR en GLB (`tools/oar2glb.py`) », § 3.3 |
| &nbsp;&nbsp;Ce que le script corrige | chapitre 3 « Convertir un OAR en GLB (`tools/oar2glb.py`) », § 3.4 |
| &nbsp;&nbsp;Lire le journal (`oar2glb.log`, à côté du script) | chapitre 3 « Convertir un OAR en GLB (`tools/oar2glb.py`) », § 3.5 |
| &nbsp;&nbsp;Diagnostic : `--diag` | chapitre 3 « Convertir un OAR en GLB (`tools/oar2glb.py`) », § 3.6 |
| &nbsp;&nbsp;Si quelque chose ne va pas | chapitre 12 « Dépannage », § 12.1 |
| 16. Fichiers JSON d'une région modulaire | chapitre 11 « Référence des fichiers JSON (v43) », § 11.12 |
| &nbsp;&nbsp;Coquille unique pour plusieurs régions (`--shared-shell`, v26) | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.1 |
| &nbsp;&nbsp;Quel fichier de zones est lu | chapitre 11 « Référence des fichiers JSON (v43) », § 11.12.1 |
| &nbsp;&nbsp;Region.config.json : le rendu de la page, pas le viewer | chapitre 11 « Référence des fichiers JSON (v43) », § 11.12.2 |
| &nbsp;&nbsp;`.reglages.json` et `.config.json` n'ont pas la même structure | chapitre 11 « Référence des fichiers JSON (v43) », § 11.12.3 |
| &nbsp;&nbsp;Quel fichier modifier, et ce qui l'écrase | chapitre 11 « Référence des fichiers JSON (v43) », § 11.12.4 |
| 17. Découper un GLB énorme en tuiles (`tools/glb2tiles.py`, v28 ; `--exclude` et pause en v29 ; images invalides et vue d'ensemble en v31) | chapitre 4 « Mesurer et découper une grosse région », § 4.1 |
| &nbsp;&nbsp;Les commandes (PowerShell, une seule ligne) | chapitre 4 « Mesurer et découper une grosse région », § 4.1.1 |
| &nbsp;&nbsp;Les paramètres | chapitre 4 « Mesurer et découper une grosse région », § 4.1.2 |
| &nbsp;&nbsp;Exclure des objets (`--exclude`, v29) | chapitre 4 « Mesurer et découper une grosse région », § 4.1.3 |
| &nbsp;&nbsp;Références d'objets (v32) : lier une zone à un objet en mode tuiles | chapitre 4 « Mesurer et découper une grosse région », § 4.1.4 |
| &nbsp;&nbsp;Images vides ou invalides (v31) | chapitre 4 « Mesurer et découper une grosse région », § 4.1.5 |
| &nbsp;&nbsp;Vue d'ensemble (`X.overview.glb`, v31) | chapitre 4 « Mesurer et découper une grosse région », § 4.1.6 |
| &nbsp;&nbsp;Comment le découpage se décide | chapitre 4 « Mesurer et découper une grosse région », § 4.1.7 |
| &nbsp;&nbsp;Fichiers produits | chapitre 4 « Mesurer et découper une grosse région », § 4.1.8 |
| &nbsp;&nbsp;Lire le journal (`glb2tiles.log`, à côté du script) | chapitre 4 « Mesurer et découper une grosse région », § 4.1.9 |
| &nbsp;&nbsp;Si quelque chose ne va pas | chapitre 12 « Dépannage », § 12.2 |
| 17 bis. Charger une région en tuiles dans la page (`glb2html.py --tiles`, v30) | chapitre 8 « Charger une région en tuiles dans la page (`glb2html.py --tiles`, v30) » |
| &nbsp;&nbsp;Les commandes (PowerShell, une seule ligne) | chapitre 8 « Charger une région en tuiles dans la page (`glb2html.py --tiles`, v30) », § 8.1 |
| &nbsp;&nbsp;Les paramètres (dans `X.config.json`, avec leurs options) | chapitre 8 « Charger une région en tuiles dans la page (`glb2html.py --tiles`, v30) », § 8.2 |
| &nbsp;&nbsp;Ce que fait la page | chapitre 8 « Charger une région en tuiles dans la page (`glb2html.py --tiles`, v30) », § 8.3 |
| &nbsp;&nbsp;Repère, rotation, mer, zones | chapitre 8 « Charger une région en tuiles dans la page (`glb2html.py --tiles`, v30) », § 8.4 |
| &nbsp;&nbsp;Limites de cette version | chapitre 8 « Charger une région en tuiles dans la page (`glb2html.py --tiles`, v30) », § 8.5 |
| &nbsp;&nbsp;Si quelque chose ne va pas | chapitre 12 « Dépannage », § 12.3 |
| 17 ter. Poser des zones dans une région en tuiles (viewer, v32) | chapitre 5 « Poser les zones (le viewer) », § 5.14 |
| 18. Nouveautés de la v33 (22/10/2026) | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;18.1 Démarrage avec une arrivée (`#spawn=`, `#pos=`) dans une région en tuiles | chapitre 8 « Charger une région en tuiles dans la page (`glb2html.py --tiles`, v30) », § 8.6 |
| &nbsp;&nbsp;18.2 Arrivée par défaut et retour à l'arrivée | chapitre 7 « La page côté visiteur », § 7.21 |
| &nbsp;&nbsp;18.3 Marqueurs de zones dans la page exportée | chapitre 7 « La page côté visiteur », § 7.14 |
| &nbsp;&nbsp;18.4 Vol, trois vues, « Aller à » | chapitre 7 « La page côté visiteur », § 7.7 |
| &nbsp;&nbsp;18.5 Chat | chapitre 7 « La page côté visiteur », § 7.25 |
| &nbsp;&nbsp;18.6 Couleur de l'avatar (client et serveur) | chapitre 7 « La page côté visiteur », § 7.29 |
| &nbsp;&nbsp;18.7 Adresses IP dans le journal : `--log-ip raw` | chapitre 10 « Serveur de présence », § 10.22 |
| &nbsp;&nbsp;18.8 Enregistrer les zones directement dans le dossier de la région (viewer) | chapitre 5 « Poser les zones (le viewer) », § 5.15 |
| &nbsp;&nbsp;18.9 `glb2html.py --tiles --zones` avec le fichier déjà en place | chapitre 8 « Charger une région en tuiles dans la page (`glb2html.py --tiles`, v30) », § 8.7 |
| &nbsp;&nbsp;18.10 Mettre à jour une région déjà publiée | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.14 |
| 19. Nouveautés de la v34 (22/10/2026) | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;19.1 Panneau d'aide sélectionnable et bloc d'état | chapitre 7 « La page côté visiteur », § 7.38 |
| &nbsp;&nbsp;19.2 Zone de survol et de clic des marqueurs | chapitre 7 « La page côté visiteur », § 7.15 |
| &nbsp;&nbsp;19.3 Vol | chapitre 7 « La page côté visiteur », § 7.8 |
| &nbsp;&nbsp;19.4 Souris libre après Échap | chapitre 7 « La page côté visiteur », § 7.10 |
| &nbsp;&nbsp;19.5 Couleur en direct | chapitre 7 « La page côté visiteur », § 7.30 |
| &nbsp;&nbsp;19.6 `glb2html.py --update` : mettre à jour une région sans rien ressaisir | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.15 |
| &nbsp;&nbsp;19.7 Pseudo, lien personnel, page de lancement | chapitre 7 « La page côté visiteur », § 7.28 |
| 20. Nouveautés de la v35 (22/10/2026) | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;20.1 Aide en groupes, panneaux repliables | chapitre 7 « La page côté visiteur », § 7.39 |
| &nbsp;&nbsp;20.2 Touches Firestorm / touches de cette page | chapitre 7 « La page côté visiteur », § 7.2 |
| &nbsp;&nbsp;20.3 Vol et saut | chapitre 7 « La page côté visiteur », § 7.5 |
| &nbsp;&nbsp;20.4 Troisième personne | chapitre 7 « La page côté visiteur », § 7.6 |
| &nbsp;&nbsp;20.5 Infobulle et clic des zones : `--zone-info-dist` | chapitre 7 « La page côté visiteur », § 7.16 |
| &nbsp;&nbsp;20.6 Copier dans le presse-papiers | chapitre 7 « La page côté visiteur », § 7.23 |
| &nbsp;&nbsp;20.7 `--update` et la carte des mondes | chapitre 9 « Carte des mondes », § 9.3 |
| &nbsp;&nbsp;20.8 Créer la carte des mondes | chapitre 9 « Carte des mondes », § 9.2 |
| &nbsp;&nbsp;20.9 Caméra libre et molette | chapitre 7 « La page côté visiteur », § 7.9 |
| 21. Nouveautés de la v36 (23/10/2026) | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;21.1 Touches : F et P, E, vol | chapitre 7 « La page côté visiteur », § 7.3 |
| &nbsp;&nbsp;21.2 Disposition du clavier : AZERTY ou QWERTY | chapitre 7 « La page côté visiteur », § 7.4 |
| &nbsp;&nbsp;21.3 Aide et informations : trois temps | chapitre 7 « La page côté visiteur », § 7.40 |
| &nbsp;&nbsp;21.4 Repères de portail (cônes) : `--zone-cone`, touche T | chapitre 7 « La page côté visiteur », § 7.17 |
| &nbsp;&nbsp;21.5 Arrivée occupée | chapitre 7 « La page côté visiteur », § 7.19 |
| &nbsp;&nbsp;21.6 Sons | chapitre 7 « La page côté visiteur », § 7.31 |
| &nbsp;&nbsp;21.7 Copier ma position, « Aller à » | chapitre 7 « La page côté visiteur », § 7.22 |
| &nbsp;&nbsp;21.8 Langue de la page | chapitre 7 « La page côté visiteur », § 7.49 |
| &nbsp;&nbsp;21.9 Ajouter une langue (sans toucher au code) | chapitre 2 « Les outils et leurs fichiers », § 2.2 |
| &nbsp;&nbsp;21.10 Langue du viewer | chapitre 5 « Poser les zones (le viewer) », § 5.17 |
| &nbsp;&nbsp;21.11 Langue des outils Python : `--lang`, `WEB3D_LANG` | chapitre 2 « Les outils et leurs fichiers », § 2.1 |
| 22. Nouveautés de la v37 (23/10/2026) | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;22.1 Indicateur de course, boussole, fenêtres redimensionnables, touche O | chapitre 7 « La page côté visiteur », § 7.12 |
| &nbsp;&nbsp;22.2 Repère de portail (cône) : taille constante, distance | chapitre 7 « La page côté visiteur », § 7.18 |
| &nbsp;&nbsp;22.3 Arrivée occupée, améliorée | chapitre 7 « La page côté visiteur », § 7.20 |
| &nbsp;&nbsp;22.4 Pseudo cité : clignotement continu | chapitre 7 « La page côté visiteur », § 7.27 |
| &nbsp;&nbsp;22.5 Paramètres du lien après `#` | chapitre 7 « La page côté visiteur », § 7.50 |
| &nbsp;&nbsp;22.6 Historique du chat | chapitre 10 « Serveur de présence », § 10.21 |
| &nbsp;&nbsp;22.7 Région par défaut (`default.json`) | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.7 |
| &nbsp;&nbsp;22.8 Dossier lib : `--lib-url` | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.5 |
| &nbsp;&nbsp;22.9 Régions dans des sous-dossiers | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.6 |
| &nbsp;&nbsp;22.10 Tests de la v37 | supprimé (liste « Tests de la vNN » : voir `CHANGELOG.md`) |
| 23. Nouveautés de la v39 (23/10/2026) | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;23.1 Bouton « Copier le diagnostic » | chapitre 7 « La page côté visiteur », § 7.51 |
| &nbsp;&nbsp;23.2 Tests de la v39 | supprimé (liste « Tests de la vNN » : voir `CHANGELOG.md`) |
| 24. Nouveautés de la v40 (24/10/2026) | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;24.1 Fenêtre « Arrivées » (touche L) | chapitre 7 « La page côté visiteur », § 7.24 |
| &nbsp;&nbsp;24.2 Bouton « Recentrer la vue » | chapitre 7 « La page côté visiteur », § 7.11 |
| &nbsp;&nbsp;24.3 Lien « Manuel complet » et bulle du diagnostic | chapitre 7 « La page côté visiteur », § 7.41 |
| &nbsp;&nbsp;24.4 Tests de la v40 | supprimé (liste « Tests de la vNN » : voir `CHANGELOG.md`) |
| 25. Nouveautés de la v41 (24/10/2026) | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;25.1 Bulles des fenêtres | chapitre 7 « La page côté visiteur », § 7.42 |
| &nbsp;&nbsp;25.2 Fenêtres déplaçables | chapitre 7 « La page côté visiteur », § 7.43 |
| &nbsp;&nbsp;25.3 Disposition retenue et fichier de disposition | chapitre 7 « La page côté visiteur », § 7.44 |
| &nbsp;&nbsp;25.4 Tests de la v41 | supprimé (liste « Tests de la vNN » : voir `CHANGELOG.md`) |
| 26. Nouveautés de la v42 (24/10/2026) | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;26.1 Rendu léger | chapitre 7 « La page côté visiteur », § 7.45 |
| &nbsp;&nbsp;26.2 Réglages fins | chapitre 7 « La page côté visiteur », § 7.46 |
| &nbsp;&nbsp;26.3 Proposition automatique | chapitre 7 « La page côté visiteur », § 7.47 |
| &nbsp;&nbsp;26.4 Option `--light` | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.12 |
| &nbsp;&nbsp;26.5 Fenêtre Réglages plus étroite | chapitre 7 « La page côté visiteur », § 7.48 |
| &nbsp;&nbsp;26.6 Diagnostic | chapitre 7 « La page côté visiteur », § 7.52 |
| &nbsp;&nbsp;26.7 Tests de la v42 | supprimé (liste « Tests de la vNN » : voir `CHANGELOG.md`) |
| 27. Référence des fichiers JSON (v43) | chapitre 11 « Référence des fichiers JSON (v43) » |
| &nbsp;&nbsp;27.1 Les fichiers et leurs exemples | chapitre 11 « Référence des fichiers JSON (v43) », § 11.1 |
| &nbsp;&nbsp;27.2 Comment lire les tableaux | chapitre 11 « Référence des fichiers JSON (v43) », § 11.2 |
| &nbsp;&nbsp;27.3 `NOM.config.json` : les réglages de la page | chapitre 11 « Référence des fichiers JSON (v43) », § 11.3 |
| &nbsp;&nbsp;27.4 `NOM.zones.json` : les zones | chapitre 11 « Référence des fichiers JSON (v43) », § 11.4 |
| &nbsp;&nbsp;27.5 `default.json` : la région par défaut | chapitre 11 « Référence des fichiers JSON (v43) », § 11.5 |
| &nbsp;&nbsp;27.6 `regions.json` : la carte des mondes | chapitre 11 « Référence des fichiers JSON (v43) », § 11.6 |
| &nbsp;&nbsp;27.7 `NOM.tiles.json` : l'index des tuiles | chapitre 11 « Référence des fichiers JSON (v43) », § 11.7 |
| &nbsp;&nbsp;27.8 `NOM.reglages.json` : l'état de travail du viewer | chapitre 11 « Référence des fichiers JSON (v43) », § 11.8 |
| &nbsp;&nbsp;27.9 `disposition.json` : la place des fenêtres | chapitre 11 « Référence des fichiers JSON (v43) », § 11.9 |
| &nbsp;&nbsp;27.10 Fichiers du serveur de présence | chapitre 11 « Référence des fichiers JSON (v43) », § 11.10 |
| &nbsp;&nbsp;27.11 Noms en anglais depuis la v43 | chapitre 11 « Référence des fichiers JSON (v43) », § 11.11 |
| 28. Nouveautés de la v45 (24/10/2026) | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;28.1 La page dit pourquoi la présence s'est coupée | chapitre 7 « La page côté visiteur », § 7.55 |
| &nbsp;&nbsp;28.2 Diagnostic | chapitre 7 « La page côté visiteur », § 7.53 |
| &nbsp;&nbsp;28.3 Test de la présence | chapitre 10 « Serveur de présence », § 10.23 |
| &nbsp;&nbsp;28.4 Une seule ligne pour le dossier `lib` | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.3 |
| &nbsp;&nbsp;28.5 `--update` garde la ligne | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.4 |
| &nbsp;&nbsp;28.6 `dist\index.html` | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.8 |
| &nbsp;&nbsp;28.7 Navigateurs | chapitre 7 « La page côté visiteur », § 7.57 |
| &nbsp;&nbsp;28.8 Test de la coquille | supprimé (liste « Tests de la vNN » : voir `CHANGELOG.md`) |
| 29. Nouveautés de la v46 (25/10/2026) | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;29.1 Ligne d'état | chapitre 7 « La page côté visiteur », § 7.32 |
| &nbsp;&nbsp;29.2 Flèches à l'écran | chapitre 7 « La page côté visiteur », § 7.33 |
| &nbsp;&nbsp;29.3 Cacher ou montrer les flèches | chapitre 7 « La page côté visiteur », § 7.34 |
| &nbsp;&nbsp;29.4 Écran tactile (téléphone, tablette) | chapitre 7 « La page côté visiteur », § 7.35 |
| &nbsp;&nbsp;29.5 Bulles | chapitre 7 « La page côté visiteur », § 7.36 |
| &nbsp;&nbsp;29.6 Compteur du chat | chapitre 7 « La page côté visiteur », § 7.26 |
| &nbsp;&nbsp;29.7 Diagnostic | chapitre 7 « La page côté visiteur », § 7.54 |
| &nbsp;&nbsp;29.8 Une coquille pour tout un site | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.2 |
| &nbsp;&nbsp;29.9 Tests de la v46 | supprimé (liste « Tests de la vNN » : voir `CHANGELOG.md`) |
| &nbsp;&nbsp;29.10 Non testé | chapitre 7 « La page côté visiteur », § 7.37 |
| 30. Nouveautés de la v47 (25/10/2026) | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;30.1 La tuile de la carte | chapitre 9 « Carte des mondes », § 9.4 |
| &nbsp;&nbsp;30.2 Adresse facultative | chapitre 9 « Carte des mondes », § 9.5 |
| &nbsp;&nbsp;30.3 `regions.json` avec en-tête | chapitre 9 « Carte des mondes », § 9.6 |
| &nbsp;&nbsp;30.4 Deux façons de faire la carte | chapitre 9 « Carte des mondes », § 9.7 |
| &nbsp;&nbsp;30.5 Serveur de présence | chapitre 10 « Serveur de présence », § 10.1 |
| &nbsp;&nbsp;30.6 Tests de la v47 | supprimé (liste « Tests de la vNN » : voir `CHANGELOG.md`) |
| &nbsp;&nbsp;30.7 Non testé | chapitre 9 « Carte des mondes », § 9.8 |
| 31. Nouveautés de la v48 (25/10/2026) : journal des visites | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;31.1 À quoi il sert | chapitre 10 « Serveur de présence », § 10.2 |
| &nbsp;&nbsp;31.2 Côté hôte : le serveur de présence | chapitre 10 « Serveur de présence », § 10.3 |
| &nbsp;&nbsp;31.3 Côté créateur : la fenêtre « Journal des visites » | chapitre 10 « Serveur de présence », § 10.4 |
| &nbsp;&nbsp;31.4 Ce qui est compté | chapitre 10 « Serveur de présence », § 10.5 |
| &nbsp;&nbsp;31.5 Données personnelles | chapitre 10 « Serveur de présence », § 10.6 |
| &nbsp;&nbsp;31.6 Fichiers | chapitre 10 « Serveur de présence », § 10.7 |
| &nbsp;&nbsp;31.7 Tests de la v48 | supprimé (liste « Tests de la vNN » : voir `CHANGELOG.md`) |
| &nbsp;&nbsp;31.8 Non testé | chapitre 10 « Serveur de présence », § 10.8 |
| 32. Nouveautés de la v49 (25/10/2026) : mise à jour de `regions.json` depuis le dossier des sites | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;32.1 La commande | chapitre 9 « Carte des mondes », § 9.9 |
| &nbsp;&nbsp;32.2 Ce que fait le parcours | chapitre 9 « Carte des mondes », § 9.10 |
| &nbsp;&nbsp;32.3 Les vignettes | chapitre 9 « Carte des mondes », § 9.11 |
| &nbsp;&nbsp;32.4 Tests de la v49 | supprimé (liste « Tests de la vNN » : voir `CHANGELOG.md`) |
| &nbsp;&nbsp;32.5 Non testé | chapitre 9 « Carte des mondes », § 9.12 |
| 33. Nouveautés de la v50 (25/10/2026) : la carte des mondes dans le viewer | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;33.1 Importer et exporter `regions.json` | chapitre 9 « Carte des mondes », § 9.13 |
| &nbsp;&nbsp;33.2 Ajouter ou mettre à jour cette région | chapitre 9 « Carte des mondes », § 9.14 |
| &nbsp;&nbsp;33.3 Tests de la v50 | supprimé (liste « Tests de la vNN » : voir `CHANGELOG.md`) |
| &nbsp;&nbsp;33.4 Non testé | chapitre 9 « Carte des mondes », § 9.15 |
| 34. Nouveautés de la v51 (25/10/2026) : créateurs sur le serveur de présence | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;34.1 À quoi ça sert | chapitre 10 « Serveur de présence », § 10.9 |
| &nbsp;&nbsp;34.2 Le fichier des créateurs | chapitre 10 « Serveur de présence », § 10.10 |
| &nbsp;&nbsp;34.3 Ce que voit le visiteur | chapitre 10 « Serveur de présence », § 10.11 |
| &nbsp;&nbsp;34.4 Console et journal | chapitre 10 « Serveur de présence », § 10.12 |
| &nbsp;&nbsp;34.5 Accueillir un créateur | chapitre 10 « Serveur de présence », § 10.13 |
| &nbsp;&nbsp;34.6 Limites | chapitre 10 « Serveur de présence », § 10.14 |
| &nbsp;&nbsp;34.7 Tests de la v51 | supprimé (liste « Tests de la vNN » : voir `CHANGELOG.md`) |
| &nbsp;&nbsp;34.8 Non testé | chapitre 10 « Serveur de présence », § 10.15 |
| &nbsp;&nbsp;34.9 Connexions vides | chapitre 10 « Serveur de présence », § 10.16 |
| &nbsp;&nbsp;34.10 Adresse de présence « même nom que la page » | chapitre 10 « Serveur de présence », § 10.17 |
| 35. Nouveautés de la v52 (25/10/2026) | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;35.1 `carte.html` : décompte, total, deux lignes | chapitre 9 « Carte des mondes », § 9.16 |
| &nbsp;&nbsp;35.2 Surveillance des arrivées (son et repère) | chapitre 9 « Carte des mondes », § 9.17 |
| &nbsp;&nbsp;35.3 Vignette agrandie au survol | chapitre 9 « Carte des mondes », § 9.18 |
| &nbsp;&nbsp;35.4 Case « Afficher la mer » | chapitre 9 « Carte des mondes », § 9.19 |
| &nbsp;&nbsp;35.5 Serveur de présence : requêtes HTTP ordinaires | chapitre 10 « Serveur de présence », § 10.18 |
| &nbsp;&nbsp;35.6 Région en tuiles renommée | chapitre 8 « Charger une région en tuiles dans la page (`glb2html.py --tiles`, v30) », § 8.9 |
| &nbsp;&nbsp;35.7 Tests de la v52 | supprimé (liste « Tests de la vNN » : voir `CHANGELOG.md`) |
| &nbsp;&nbsp;35.8 Non testé | chapitre 9 « Carte des mondes », § 9.20 |
| 36. Ajouts de la 1.0.0 (après la v52) | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;36.1 Icône des pages (`favicon.ico`) | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.9 |
| &nbsp;&nbsp;36.2 Pseudos : la commande `oublier` | chapitre 10 « Serveur de présence », § 10.19 |
| &nbsp;&nbsp;36.3 Adresses IPv6 : limite et bannissements par préfixe `/64` | chapitre 10 « Serveur de présence », § 10.20 |
| &nbsp;&nbsp;36.4 Essais de connexion à la présence | chapitre 7 « La page côté visiteur », § 7.56 |
| &nbsp;&nbsp;36.5 Numérotation des versions | chapitre 13 « Annexe : ce que chaque version a apporté », § 13.1 |
| 37. Ajouts de la 1.1.0 (après la 1.0.0) | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;37.1 Zone `image` : un tableau sur un mur | chapitre 5 « Poser les zones (le viewer) », § 5.11 |
| &nbsp;&nbsp;37.2 Éditeur : dossier de la région et aperçu des images | chapitre 5 « Poser les zones (le viewer) », § 5.12 |
| &nbsp;&nbsp;37.3 Matériaux rendus pleins : `--solid-materials` | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.13 |
| &nbsp;&nbsp;37.4 Pointeur : le nom du bâtiment | chapitre 7 « La page côté visiteur », § 7.59 |
| &nbsp;&nbsp;37.5 Quand WebGL est indisponible | chapitre 7 « La page côté visiteur », § 7.58 |
| &nbsp;&nbsp;37.6 Versions : un numéro par fichier, marque, commande `version` | chapitre 13 « Annexe : ce que chaque version a apporté », § 13.2 |
| &nbsp;&nbsp;37.7 Serveur de présence : console et lignes « requête http » | chapitre 10 « Serveur de présence », § 10.24 |
| &nbsp;&nbsp;37.8 Documents ajoutés ou revus depuis la 1.0.0 | chapitre 13 « Annexe : ce que chaque version a apporté », § 13.3 |
| &nbsp;&nbsp;37.9 Essayé et non essayé | chapitre 5 « Poser les zones (le viewer) », § 5.18 |
| 38. Ajouts de la 1.4 (lots 1.4.2 à 1.4.7) | titre supprimé (conteneur « Nouveautés/Ajouts » : sous-sections réparties ; une ligne dans le tableau de l'annexe, chapitre 13) |
| &nbsp;&nbsp;38.1 La ligne des tuiles | chapitre 8 « Charger une région en tuiles dans la page (`glb2html.py --tiles`, v30) », § 8.8 |
| &nbsp;&nbsp;38.2 « À propos de la région » | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.10 |
| &nbsp;&nbsp;38.3 Compresser les tuiles : `glb2tiles.py --compress` | chapitre 4 « Mesurer et découper une grosse région », § 4.2 |
| &nbsp;&nbsp;38.4 Titre affiché : la clé `title` | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.11 |
| &nbsp;&nbsp;38.5 `--scan-sites --prune-missing` | chapitre 9 « Carte des mondes », § 9.21 |
| &nbsp;&nbsp;38.6 Essayé et non essayé | chapitre 6 « Fabriquer la page (`glb2html.py`) », § 6.17 |
