# Développement : livraisons et versions

*03/11/2026. Pour qui entretient le dépôt (Klaatou). L'état du travail est dans `REPRISE.md`. Dans les commandes, `NOM` est le nom du patch ou du test, `MESSAGE` le message de commit, `X.Y.Z` le numéro de version.*

## 1. Appliquer une livraison

Les fichiers livrés se posent à la racine du dépôt ; un fichier nouveau (test, document) est rangé par la ligne donnée avec la livraison (`Move-Item`). Essai à blanc d'abord :

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d\web_3d"; git pull; python .\patch_NOM.py --dry-run; if ($LASTEXITCODE -eq 0) { python .\patch_NOM.py }
```

Chaque patch garde une copie des fichiers qu'il modifie dans `_bak\` et refuse de s'appliquer deux fois.

## 2. Fabriquer et contrôler

Sans cette étape, `dist\` reste à l'ancienne version. `python build.py` affiche le numéro de chaque fichier : seul un fichier dont le contenu a changé prend le numéro du lot.

```powershell
python build.py; python .\tests\dist_a_jour.py
```

`python build.py` refait aussi `docs/REFERENCE_OPTIONS.md` (seulement quand la sortie est `dist/`, et seulement si son contenu change hors la date) : `git add -A` le prend avec le lot.

`dist/convoar/` (convoar, fourni, copie sans fichiers de débogage) n'est pas fabriqué par `build.py` : `tests/dist_a_jour.py` l'ignore, `.gitattributes` y met `-text` (git ne touche pas aux fins de ligne, sinon les empreintes de `SHA256SUMS.txt` ne correspondent plus), `.gitignore` écarte `convoar_inv.*` (le lanceur que `oar2glb.py` fabrique à la première conversion) et `tests/convoar_dist.py` contrôle les empreintes.

## 3. Publier sur GitHub

La liste des fichiers s'affiche, puis tout part :

```powershell
git status --short; git add -A; git commit -m "MESSAGE"; git push
```

## 4. Lancer un test

Un test à la fois, jamais plusieurs en même temps :

```powershell
python .\tests\NOM.py
```

La suite complète compte plus de 70 fichiers et dure longtemps. Échouent déjà dans le bac à sable et en session cloud : `doc_options`, `image_dossier`, `marque`.

Pour la lancer d'un coup : `python .\tests\tout.py`. Elle lance chaque test l'un après l'autre, signale ceux qui échouent (code de retour, ligne `[ECHEC]`, délai dépassé, trace d'erreur suspecte) et résume le tout ; les sorties complètes sont dans `tests_logs\` (dossier ignoré par git). Options : `--liste`, `--seulement REGEX`, `--sauf REGEX`, `--reprendre` (saute les tests réussis au dernier passage), `--arreter`, `--delai N`.

Tests ajoutés avec la 1.8.x : `bouton_promenade.py`, `demarrage_lien.py`, `build_reference.py` et `convoar_dist.py`.

Sous Windows, un test qui lit la sortie d'un programme fils doit lancer ce programme avec `PYTHONIOENCODING=utf-8` (sinon sa sortie est en cp1252), fermer son entrée (`stdin=subprocess.DEVNULL`, sinon un outil attend Entrée) et, si ce programme écrit beaucoup dans sa console, la lire pendant le test (un tube Windows ne garde que 4 Ko) : `tests/build_reference.py`, `tests/console.py` et `tests/correctifs_v52.py` en sont des exemples.

## 5. Publier une version

Décision de Klaatou. Une livraison passe `VERSION` au numéro de la version (mineur + 1 si des fonctions ont été ajoutées depuis la précédente). Quand tout est poussé :

```powershell
python .\fabriquer_paquets.py; git tag vX.Y.Z; git push origin vX.Y.Z
```

Puis, sur GitHub, créer la release de l'étiquette `vX.Y.Z` en y joignant les deux zips du dossier `paquets-zip\`.

## 6. Images du README

Les schémas des `README.md` et `README.fr.md` sont des **SVG dessinés à la main**, rangés dans `docs/images/` : `fonctionnement.fr.svg` et `fonctionnement.en.svg` (la chaîne d'outils, section « Comment ça marche »), `site.fr.svg` et `site.en.svg` (l'arbre d'un site, en fenêtre d'explorateur). Aucun script du dépôt ne les produit : un SVG est du texte, on le modifie à la main (textes, positions, légende), puis on le regarde dans un navigateur. Les deux langues se tiennent à jour ensemble. Rien n'y est porté par la couleur seule (contours, pointillés, numéros, légende). Le dossier contient aussi le GIF de démonstration (`PalmIsland_demo.gif`) et `carte.jpg`.

Contrôle : `python .\tests\readme_liens.py` vérifie que chaque image et chaque lien relatif des deux README et des documents de `docs/` désignent un fichier qui existe (il a été écrit après la disparition du GIF de démonstration, balayé par un `git add -A`). Il ne juge pas le dessin : le rendu a été regardé sous Chromium seulement, pas sur GitHub.
