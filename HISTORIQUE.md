# Retrouver chaque version

Tout le travail a eu lieu le 18/10/2026. Cet historique a été **reconstitué après coup** à partir des sauvegardes de sources faites pendant la journée ; il est fidèle sur ce qui existe, mais incomplet.

## Ce qu'il faut savoir

- Chaque ligne ci-dessous est un état des sources (dossier `src/`) à la fin d'une série de modifications. L'heure est celle de Paris.
- **Avant 12:05, rien n'a été conservé** : le travail avait commencé vers 09:28 (première demande), avec l'export de base, le trou de mer et la haute résolution.
- Les numéros de version ne s'affichent dans les pages qu'à partir de v5 (vers 16:13). Seules les étiquettes **v14 à v18** sont posées. v14 a été vérifié octet pour octet contre les fichiers v14 fournis au projet ; v15 à v17 sont les états relevés au début de chaque version suivante ; v18 est le dernier état.
- Les messages de chaque entrée ont été écrits après coup, d'après les différences entre états et l'ordre des demandes.
- Les fichiers fabriqués (`dist/`) ne sont pas dans le dépôt. Seul le dernier état contient `build.py` : pour refabriquer une ancienne version, récupérer ses `src/` et les fabriquer avec le `build.py` du dernier état.
- L'auteur des entrées est `Klaatou` par commodité ; les prochaines entrées prendront l'identité configurée sur ton poste.

## Historique (heure de Paris, 18/10/2026)

| Heure | Étiquette | Contenu |
|---|---|---|
| 12:05 |  | Promenade à la première personne (touche F) : première ébauche du noyau |
| 12:44 |  | Collisions par grille et éléments traversables |
| 13:23 |  | Nom de l'élément au clic ; visiteurs en temps réel |
| 13:50 |  | Viewer : premier état conservé |
| 14:28 |  | Chat : bulles et durée réglable ; premiers états du script et du gabarit de page |
| 14:54 |  | Serveur : limites de débit du chat, historique, proxy |
| 14:55 |  | Zones : portails, panneaux lien web et Home Assistant, points d'arrivée |
| 15:42 |  | Viewer : éditeur de zones et profils public/perso |
| 16:32 |  | Vue globale : visiteurs en promenade visibles (spectateur) |
| 16:39 |  | Repère d'atterrissage au sol et choix du point d'arrivée |
| 16:55 |  | Export : zones, profils et ligne de commande PowerShell |
| 17:17 |  | Téléportation au double-clic fiable malgré le lag |
| 17:55 |  | Losange des visiteurs masqué derrière les murs ; noms mémorisés |
| 18:02 |  | Panneau de réglages pour les visiteurs |
| 19:25 | v14 | v14 : zones rechargeables, éjection et bannissement |
| 20:14 | v15 | v15 : carte des mondes (touche M) |
| 20:52 | v16 | v16 : réglages mémorisés par fichier ; carte orientée X est / Y nord |
| 21:04 | v17 | v17 : --register, page carte, vignette enregistrable, placement compact |
| 21:20 |  | v18 : --settings, enregistrement sans .glb, cartes multi-sources |

## Commandes utiles

- Voir l'historique : `git log --oneline --decorate`
- Voir ce qui a changé dans une version : `git show v16 --stat`
- Retrouver les sources d'une version : `git switch --detach v14` (puis `git switch main` pour revenir)
- Comparer deux versions : `git diff v16 v17 --stat`
