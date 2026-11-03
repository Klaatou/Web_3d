# Procédures simplifiées

*03/11/2026. Les tâches de tous les jours, une commande par bloc, à copier telle quelle (PowerShell). Le détail est dans `PROCEDURES.md` et `MANUEL.md`. Dans les commandes, `NOM` est le nom de la région, `ANCIEN` son ancien nom, `NOUVEAU` son nouveau nom, `CHEMIN` un chemin, `MESSAGE` un message de commit.*

## 1. Appliquer une livraison

Récupérer et appliquer le patch (essai à blanc d'abord) :

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d\web_3d"; git pull; python .\patch_NOM.py --dry-run; if ($LASTEXITCODE -eq 0) { python .\patch_NOM.py }
```

Fabriquer et contrôler. Sans cette étape, `dist\` reste à l'ancienne version :

```powershell
python build.py; python .\tests\dist_a_jour.py
```

Publier : d'abord le statut, puis tout :

```powershell
git status --short
```

```powershell
git add -A; git commit -m "MESSAGE"; git push
```

## 2. Mettre à jour la page d'une région publiée

Garde la configuration et les zones, renouvelle la coquille `index.html` si elle est plus ancienne. Ajouter `--title "Houses"` pour fixer le titre affiché dans l'onglet (les fichiers et le salon restent en minuscules). Ensuite Ctrl+F5 dans la page.

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --update -o "P:\_OpenSim\SL&OS\Web_3d\Sites\houses\houses.html" --shared-shell "P:\_OpenSim\SL&OS\Web_3d\Sites\index.html"
```

## 3. Renommer une région en tuiles

Le script `renommer_region.py` (hors dépôt, dans `P:\_OpenSim\SL&OS\Web_3d`) renomme les fichiers et le dossier des tuiles, corrige l'index, la configuration, `default.json`, les liens des zones et la fiche de `regions.json`. Chaque ancien fichier modifié est copié dans `_avant_renommage\` (un dossier daté par lancement). D'abord la simulation :

```powershell
python "P:\_OpenSim\SL&OS\Web_3d\renommer_region.py" "P:\_OpenSim\SL&OS\Web_3d\Sites\houses" ANCIEN NOUVEAU --dry-run
```

Puis le renommage (ajouter `--remplacer` si le nouveau nom existe déjà : l'ancien fichier est mis de côté, jamais supprimé) :

```powershell
python "P:\_OpenSim\SL&OS\Web_3d\renommer_region.py" "P:\_OpenSim\SL&OS\Web_3d\Sites\houses" ANCIEN NOUVEAU
```

Finir par la mise à jour de la carte (§ 4). Le script peut être relancé : si la région est déjà renommée, il ne fait que les corrections.

## 4. Mettre à jour la carte des mondes

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --scan-sites "P:\_OpenSim\SL&OS\Web_3d\Sites"
```

Pour retirer aussi les fiches dont la région n'existe plus (les fiches externes sont gardées), ajouter `--prune-missing`, de préférence avec `--dry-run` la première fois :

```powershell
python .\glb2html.py --scan-sites "P:\_OpenSim\SL&OS\Web_3d\Sites" --prune-missing --dry-run
```

## 5. Découper et compresser une grosse région

Région neuve : découper avec la compression (Node requis, `gltfpack` est lancé par `npx`) :

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2tiles.py "CHEMIN\Region.glb" --compress
```

Tuiles déjà découpées et non compressées : à la main, depuis le dossier qui contient `NOM.tiles`, vers un dossier `sortie` (jamais recompresser un fichier déjà compressé) :

```powershell
New-Item -ItemType Directory -Force ".\sortie" | Out-Null; Get-ChildItem ".\NOM.tiles" -Filter *.glb | ForEach-Object { npx -y gltfpack -i $_.FullName -o ".\sortie\$($_.Name)" -cc -kn -ke -km -vpf -vtf }
```

```powershell
npx -y gltfpack -i ".\NOM.overview.glb" -o ".\sortie\NOM.overview.glb" -cc -kn -ke -km -vpf -vtf
```

Remplacer ensuite les fichiers par ceux de `sortie`. Garder une sauvegarde avant.

## 6. Mettre à jour la démo en ligne

À faire quand `index.html`, `carte.html` ou l'icône changent (le chemin d'`ajout_og.py` est à confirmer) :

```powershell
Copy-Item "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\index.html" "P:\_OpenSim\SL&OS\Web_3d\Web_3d_demo"; cd "P:\_OpenSim\SL&OS\Web_3d\Web_3d_demo"; python "P:\_OpenSim\SL&OS\Web_3d\ajout_og.py"; git add index.html; git commit -m "mise a jour"; git push
```

## 7. Accueillir un créateur sur mon serveur de présence

Ce que je lui envoie (message à copier) :

```text
Pour brancher ta région sur mon serveur de présence (positions, chat), envoie-moi :
1. l'origine de ta page : le début de son adresse, sans chemin (par exemple https://alice.example ; donne aussi la version avec www si elle marche) ;
2. un identifiant court (par exemple alice).
Je te réponds avec l'adresse du serveur (wss://...) et ton préfixe de salon (alice.NOM).
Chez toi, dans NOM.config.json, mets presenceUrl = l'adresse reçue et room = alice.NOM, puis recharge la page.
Si la présence est refusée, la page dit pourquoi (note aux créateurs, § 5).
```

Ce que je fais ensuite :

- Sur la VM, ouvrir ma copie de `presence_creators.json` et ajouter l'entrée du créateur (modèle : `docs/samples/presence_creators.sample.json`), par exemple `{"id": "alice", "origins": ["https://alice.example"]}`. Pas de redémarrage : le fichier est relu en 2 secondes au plus.
- Dans la console du serveur (`tmux attach -t presence`), taper `creators` : il liste le créateur, ses origines et son état.
- Lui envoyer l'adresse `wss://` de mon serveur et son préfixe (`alice.`).
- Facultatif : `visits-key alice.NOM` donne la clé de son journal des visites, à lui envoyer avec l'adresse de sa page suivie de `#visits`.

S'il n'a pas encore de GLB :

- Il a déjà un `.glb` : le paquet `region-simple.zip` (page des versions du dépôt GitHub) l'affiche sans rien installer.
- Il n'a qu'un OAR : la conversion demande `convoar.exe` (Windows) et `oar2glb.py`. Le plus simple est qu'il m'envoie l'OAR, que je le convertisse (§ 5) et que je lui renvoie les fichiers de la région. La conversion OAR vers GLB n'a été essayée jusqu'ici que par Klaatou.
