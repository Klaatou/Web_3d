# Rapport de la session cloud (lots 1.4.4 à 1.4.6)

Branche : `claude/lots-1-4-4` (point de départ : `main` 1.4.3, commit 3336bbb). Environnement : Chromium 1243 sans tête, Linux, three 0.160.0, Playwright 1.64.1 (variable `CHROMIUM` nécessaire : l'installation de Playwright a changé sa version).

## Étape 1 : suite complète (aucun code modifié)

72 fichiers lancés un par un. **69 passent, 3 échouent** (voir plus bas).

| Fichier | Résultat | Durée |
|---|---|---|
| carte_pseudos | ok | 8s |
| chat_bip | ok | 34s |
| chat_fleches | ok | 10s |
| console | ok | 4s |
| correctifs_v52 | ok | 2s |
| dist_a_jour | ok | 0s |
| doc_options | ÉCHEC | 1s |
| essais_presence | ok | 67s |
| glb2tiles | ok | 1s |
| glbfab | ok | 0s |
| http_proxy | ok | 0s |
| i18n | ok | 1s |
| icone | ok | 17s |
| image_cache | ok | 10s |
| image_cache_vieux | ok | 31s |
| image_diag | ok | 6s |
| image_dossier | ÉCHEC | 6s |
| image_legende | ok | 8s |
| image_medias | ok | 10s |
| image_noms_gen | ok | 1s |
| image_numero | ok | 10s |
| image_zone | ok | 11s |
| ipv6 | ok | 3s |
| lien_image | ok | 21s |
| marque | ÉCHEC | 2s |
| modulaire | ok | 142s |
| oar2glb | ok | 29s |
| oublier | ok | 7s |
| paquets | ok | 21s |
| pointeur_objet | ok | 4s |
| portail_interne | ok | 6s |
| pose_promenade | ok | 11s |
| samples | ok | 10s |
| smoke | ok | 35s |
| solid_materiaux | ok | 4s |
| terrain | ok | 38s |
| tools_lang | ok | 1s |
| tuile_ici | ok | 9s |
| tuiles | ok | 43s |
| v23 | ok | 17s |
| v24 | ok | 15s |
| v27 | ok | 20s |
| v31 | ok | 21s |
| v32 | ok | 42s |
| v33 | ok | 355s |
| v34 | ok | 60s |
| v35 | ok | 35s |
| v36 | ok | 64s |
| v36_lang | ok | 22s |
| v36_viewer_lang | ok | 10s |
| v37 | ok | 41s |
| v37_chat | ok | 63s |
| v37_region | ok | 35s |
| v39 | ok | 6s |
| v40 | ok | 7s |
| v41 | ok | 6s |
| v42 | ok | 19s |
| v45 | ok | 6s |
| v45_lib | ok | 4s |
| v46 | ok | 18s |
| v47 | ok | 6s |
| v48 | ok | 21s |
| v49 | ok | 1s |
| v50 | ok | 7s |
| v51 | ok | 25s |
| v51_etoile | ok | 6s |
| v51_vides | ok | 2s |
| v52 | ok | 28s |
| v52_http | ok | 4s |
| v52_renom | ok | 18s |
| webgl_absent | ok | 10s |
| zones_numeros | ok | 10s |

### Échecs, relancés seuls puis comparés à la publication 1.4.0

L'étiquette `v1.4.0` n'existe pas dans le dépôt cloné (aucune étiquette) : comparaison faite sur le commit `b9337a5` « Publication 1.4.0 » (`git worktree`, build neuf).

- **doc_options** : échoue seul, et sur 1.4.0 (même nombre d'échecs). Messages : « presence_server `--map-names` : description absente (fr) » et « REFERENCE_OPTIONS.md est à jour ». C'est la dérive connue du brief, non corrigée.
- **marque** : échoue seul, et sur 1.4.0. Le test attend une empreinte dans la sortie de `--version` de `presence_server.py`, `oar2glb.py`, `glb2tiles.py`, qui affichent par exemple « glb2tiles 1.3.3 (02/11/2026), fingerprint 0166707d ». Cause du format non analysée (rien corrigé).
- **image_dossier** : échoue seul. Sur 1.4.x : « bon dossier : images relatives lues dans le dossier … {'tab': 0, 'dos': 16, 'sous': 6, 'hors': 512} » puis `TargetClosedError` dans `Page.set_input_files`. Sur 1.4.0 : échec différent (attente de `#fZones`, délai dépassé). Cause non élucidée ; probablement lié au sélecteur de dossier en Chromium sans tête. Non corrigé.

Aucun échec « sensible à la charge » : tous les tests ont été lancés séparément. `v31` et `v33` (355 s) passent.

**Non testé ici** : Windows, Edge, carte graphique réelle, Firefox, Safari, téléphone.

## Étape 2 : lot 1.4.4 (faite)

- (a) `core.js` : champ `got` ajouté à `tilesStatus()` et à la clé de `tilesInfo()` ; `bytes` inchangé (budget). Affichage : `template.html` (`page.tiles.main`) et `viewer_tpl.html` (`viewer.tiles.line`). (b) setter `onTiles` : rejoue l'état.
- Tests lancés (tous OK) : `tuile_ici` (étendu : index gonflé de 2 Mo par tuile, `bytes` suit l'index, `got` et la ligne suivent les fichiers servis ; viewer : ligne présente dès le branchement, sans attendre), `tuiles`, `v31`, `v32`, `i18n`, `smoke`, `dist_a_jour`.
- Contre-épreuve : avec `src/` d'avant le correctif, `tuile_ici` échoue (ligne vide au branchement du viewer, puis plantage faute de `got`).
- Build : seuls `glb-viewer.html`, `glb2html.py` et `index.html` ont changé de numéro (1.4.3 → 1.4.4) ; les autres fichiers de `dist/` gardent le leur.
- Non testé : poids affiché avec de vraies tuiles `gltfpack` (seulement un index gonflé sur une région synthétique), Windows, Edge, carte graphique.
