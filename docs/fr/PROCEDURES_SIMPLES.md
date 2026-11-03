# Mes procédures : sites et serveur de présence

*03/11/2026. Pour l'hôte (Klaatou) : ses sites publiés et son serveur de présence. Créer une région : `GUIDE.md`. Livraisons et versions : `DEVELOPPEMENT.md` (en anglais : `DEVELOPMENT.md`). Dans les commandes, `NOM` est le nom de la région, `ANCIEN` et `NOUVEAU` l'ancien et le nouveau nom, `CHEMIN` un chemin, `UTILISATEUR` et `ADRESSE_VM` le compte et l'adresse de la VM.*

## 1. Mettre une région publiée au niveau d'une nouvelle version

À faire après une nouvelle version des outils : la page reçoit la nouvelle coquille `index.html` (l'ancienne est gardée sous un nom daté) et sa configuration est mise à jour, sans rien ressaisir ; les zones ne bougent pas. Ensuite Ctrl+F5 dans la page.

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --update -o "P:\_OpenSim\SL&OS\Web_3d\Sites\houses\houses.html" --shared-shell "P:\_OpenSim\SL&OS\Web_3d\Sites\index.html"
```

## 2. Fixer le titre affiché dans l'onglet

La même commande avec `--title "Houses"`, ou à la main la ligne `"title": "Houses",` dans `NOM.config.json`. Les fichiers et le salon restent en minuscules.

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

## 5. Compresser une grosse région déjà découpée

Pour une région neuve, `--compress` de `glb2tiles.py` suffit (`GUIDE.md` § 1.3). Pour des tuiles déjà découpées et non compressées : à la main, depuis le dossier qui contient `NOM.tiles`, vers un dossier `sortie` (Node requis ; jamais recompresser un fichier déjà compressé) :

```powershell
New-Item -ItemType Directory -Force ".\sortie" | Out-Null; Get-ChildItem ".\NOM.tiles" -Filter *.glb | ForEach-Object { npx -y gltfpack -i $_.FullName -o ".\sortie\$($_.Name)" -cc -kn -ke -km -vpf -vtf }
```

```powershell
npx -y gltfpack -i ".\NOM.overview.glb" -o ".\sortie\NOM.overview.glb" -cc -kn -ke -km -vpf -vtf
```

Remplacer ensuite les fichiers par ceux de `sortie`. Garder une sauvegarde avant.

## 6. Extraire des bâtiments d'une région

Le script `extraire_batiments.py` (hors dépôt, dans `P:\_OpenSim\SL&OS\Web_3d`) sort un GLB par bâtiment, recentré, avec un `.json` qui garde sa position d'origine. Il lit l'OAR et le GLB fabriqué par `oar2glb.py` ; la première lecture est longue, la suite vient d'un cache. Lister les groupes d'au moins 5 parties :

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d"; python .\extraire_batiments.py "CHEMIN\NOM.oar" "CHEMIN\NOM.glb" --list --min-parties 5
```

Extraire par nom (ou `--groupe 12`, `--groupe 15,18,100-150`) ; `--sol 5` ajoute un sol d'essai de 5 m autour :

```powershell
python .\extraire_batiments.py "CHEMIN\NOM.oar" "CHEMIN\NOM.glb" --nom "Jewel Box House" -o "CHEMIN\batiments"
```

Les autres options (boîtes de livraison, voisins, fusion, tout extraire) sont décrites en tête du script.

## 7. Mettre à jour la démo en ligne

À faire quand `index.html`, `carte.html` ou l'icône changent. `ajout_og.py` (hors dépôt) remet dans `index.html` les balises d'aperçu de partage (image et titre affichés quand on partage le lien) ; le chemin indiqué est à confirmer :

```powershell
Copy-Item "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\index.html", "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\carte.html", "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\favicon.ico" "P:\_OpenSim\SL&OS\Web_3d\Web_3d_demo"; cd "P:\_OpenSim\SL&OS\Web_3d\Web_3d_demo"; python "P:\_OpenSim\SL&OS\Web_3d\ajout_og.py"; git add index.html carte.html favicon.ico; git commit -m "mise a jour"; git push
```

## 8. Le serveur de présence sur la VM

Ouvrir la console de modération depuis le PC ; pour en sortir sans arrêter le serveur : Ctrl+B puis D.

```powershell
ssh -t UTILISATEUR@ADRESSE_VM "tmux attach -t presence"
```

Dans la console : `version` donne la version et l'empreinte du serveur ; `liste`, `ejecter`, `bannir`, `creators`, `aide`. Mettre le serveur à jour **seulement** si l'empreinte affichée par `version` diffère de celle que `python build.py` liste pour `presence_server.py` : envoyer le fichier, puis, sur la VM en root, `systemctl restart web3d-presence`.

```powershell
scp "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\presence_server.py" UTILISATEUR@ADRESSE_VM:/home/UTILISATEUR/presence/
```

Installation complète de la VM : `PROCEDURES.md` § 11.

## 9. Accueillir un créateur sur mon serveur de présence

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
- Dans la console (§ 8), taper `creators` : il liste le créateur, ses origines et son état.
- Lui envoyer l'adresse `wss://` de mon serveur, son préfixe (`alice.`) et la note aux créateurs (`CREATEURS.md`, en anglais `CREATORS.md`).
- Facultatif : `visits-key alice.NOM` donne la clé de son journal des visites, à lui envoyer avec l'adresse de sa page suivie de `#visits`.

S'il n'a pas encore sa région en page web : lui envoyer `GUIDE.md`.
