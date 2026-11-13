# Index de la documentation

Cette page dit **quel document lire pour quoi**. Les documents anglais portent le même contenu sous d'autres noms : `OVERVIEW.md`, `MANUAL.md`, `SIMPLE_PROCEDURES.md`, `CREATORS.md`, `DEVELOPMENT.md`, `CONVERT_OARS.md` et `HISTORY.md` ; `GUIDE.md`, `PROCEDURES.md`, `REFERENCE_JSON.md` et `INDEX.md` gardent le même nom. Les numéros « § » sont ceux des titres du document cité.

## 1. Par où commencer

1. `README.md` (à la racine) : ce qu'est le projet et le démarrage rapide.
2. `VUE_ENSEMBLE.md` : ce qui marche, ce qui a été essayé ou non, ce qui reste à faire.
3. `GUIDE.md` : la prise en main, de la région à la page publiée.

## 2. Par tâche

| Je veux… | Où lire |
| --- | --- |
| obtenir une région en 3D sans rien installer | `GUIDE.md` § 1.1 ; `PROCEDURES.md` § 12 |
| convertir mon OAR en GLB | `GUIDE.md` § 1.2 ; `MANUEL.md` § 3 ; `PROCEDURES.md` § 1 |
| traiter une région lourde (tuiles) | `GUIDE.md` § 1.3 ; `MANUEL.md` § 4 et § 8 ; `PROCEDURES.md` § 2 |
| compresser une région déjà découpée | `MANUEL.md` § 4.2 ; `PROCEDURES_SIMPLES.md` § 5 |
| extraire des objets (bâtiments, meubles...) d'une région | `MANUEL.md` § 3.7 ; `PROCEDURES_SIMPLES.md` § 6 |
| extraire des objets d'un inventaire (IAR) | `MANUEL.md` § 3.8 ; `PROCEDURES_SIMPLES.md` § 6 |
| convertir un dossier d'OAR en site web, une région après l'autre | `CONVERTIR_OARS.md` |
| poser des zones (arrivées, portails, panneaux, images) | `GUIDE.md` § 2 ; `MANUEL.md` § 5 ; `PROCEDURES.md` § 5 |
| fabriquer ou mettre à jour la page | `GUIDE.md` § 3 ; `MANUEL.md` § 6 ; `PROCEDURES.md` § 3, § 4 et § 8 ; `PROCEDURES_SIMPLES.md` § 1 |
| fixer le titre de l'onglet, renommer une région en tuiles | `PROCEDURES_SIMPLES.md` § 2 et § 3 |
| publier, mettre à jour la démo en ligne | `GUIDE.md` § 4 ; `PROCEDURES_SIMPLES.md` § 7 |
| savoir ce que le visiteur peut faire (touches, vol, chat) | `MANUEL.md` § 7 ; `PROCEDURES.md` § 10 |
| relier plusieurs régions par une carte des mondes | `MANUEL.md` § 9 ; `PROCEDURES.md` § 7 ; `PROCEDURES_SIMPLES.md` § 4 |
| comprendre pourquoi la carte n'affiche pas les pseudos | `MANUEL.md` § 9.22 ; `PROCEDURES.md` § 7 ; `PROCEDURES_SIMPLES.md` § 4 |
| ouvrir les outils dans une fenêtre, créer des raccourcis sur le bureau | `MANUEL.md` § 3.9 ; `PROCEDURES_SIMPLES.md` § 11 |
| convertir un OAR qui contient du PBR (OpenSim 0.9.3) | `MANUEL.md` § 3.10 |
| convertir un OAR sous Linux (Mono) | `MANUEL.md` § 3.11 |
| régler les reflets des métaux (PBR) dans la page | `MANUEL.md` § 7.65 |
| retirer l'icône « Réalisé avec Web_3d » | `MANUEL.md` § 7.62 |
| saisir la clé des pseudos de la carte | `MANUEL.md` § 9.16 |
| régler la hauteur de la mer dans la page | `MANUEL.md` § 9.19 |
| poser une question, demander de l'aide | le serveur Discord : https://discord.gg/BDG9r5gXwr |
| voir les autres visiteurs, chatter, modérer | `GUIDE.md` § 5 ; `MANUEL.md` § 10 ; `PROCEDURES.md` § 6 |
| installer le serveur de présence sur une VM | `PROCEDURES_SIMPLES.md` § 8 ; `PROCEDURES.md` § 11 |
| rendre le serveur de présence public sans montrer mon adresse IP | `PROCEDURES.md` § 11 |
| accueillir un créateur sur mon serveur | `PROCEDURES_SIMPLES.md` § 9 ; `MANUEL.md` § 10.10 |
| utiliser le serveur de présence de quelqu'un d'autre | `CREATEURS.md` |
| ouvrir un lien `hop://` | `PROCEDURES.md` § 13 |
| fabriquer les paquets prêts à l'emploi (zips) | `PROCEDURES.md` § 12 |
| mettre à jour un paquet déjà publié | `PROCEDURES_SIMPLES.md` § 10 |
| comprendre une panne | `PROCEDURES.md` § 9 ; `MANUEL.md` § 12 |

## 3. Références

| Je cherche… | Où |
| --- | --- |
| toutes les options de chaque outil, en français et en anglais | `docs/REFERENCE_OPTIONS.md` ; `--help` de l'outil |
| le sens de chaque champ d'un fichier JSON | `REFERENCE_JSON.md` |
| un exemple complet de chaque fichier JSON | dossier `docs/samples/` |
| les noms d'options français d'avant la v43 | `REFERENCE_JSON.md` § 11.11 |

## 4. L'état du projet et le travail sur le code

| Je veux savoir… | Où |
| --- | --- |
| ce qui a été essayé, et ce qui ne l'a pas été | `VUE_ENSEMBLE.md` § 2 |
| ce qui a changé, et quand | `CHANGELOG.fr.md` (à la racine) ; `HISTORIQUE.md` ; `MANUEL.md` § 13 |
| comment appliquer une livraison, fabriquer, tester, publier une version | `DEVELOPPEMENT.md` § 1 à § 5 |
| comment modifier les schémas du README | `DEVELOPPEMENT.md` § 6 |
| l'état technique pour reprendre le travail | `REPRISE.md` (à la racine) |
