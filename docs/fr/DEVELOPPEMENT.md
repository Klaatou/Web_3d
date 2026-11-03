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

## 5. Publier une version

Décision de Klaatou. Une livraison passe `VERSION` au numéro de la version (mineur + 1 si des fonctions ont été ajoutées depuis la précédente). Quand tout est poussé :

```powershell
python .\fabriquer_paquets.py; git tag vX.Y.Z; git push origin vX.Y.Z
```

Puis, sur GitHub, créer la release de l'étiquette `vX.Y.Z` en y joignant les deux zips du dossier `paquets-zip\`.
