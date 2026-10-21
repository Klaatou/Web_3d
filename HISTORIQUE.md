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

## Commandes utiles

- Voir l'historique : `git log --oneline --decorate`
- Voir ce qui a changé dans une version : `git show v16 --stat`
- Retrouver les sources d'une version : `git switch --detach v14` (puis `git switch main` pour revenir)
- Comparer deux versions : `git diff v16 v17 --stat`
