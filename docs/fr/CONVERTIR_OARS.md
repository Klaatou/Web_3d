# Convertir un dossier d'OAR en site web (`oars2site.py`)

`oars2site.py` transforme un dossier de sauvegardes de région OpenSim (`.oar`, `.tgz`) en un site web complet, une région après l'autre. Il ne fait que lancer les outils existants, dans l'ordre : `oar2glb.py`, `glb2tiles.py`, `glb2html.py` (mode coquille commune), puis la mise à jour de la carte des mondes. Il ne modifie ni les OAR ni les outils.

## 1. Ce qu'il faut

- Python 3 et Pillow (`pip install pillow`).
- Les outils `oar2glb.py`, `glb2tiles.py` et `glb2html.py` : ils sont dans `dist/`, à côté de `oars2site.py`. Sous Linux, voir `MANUEL.md` § 3.11 (convoar avec Mono).
- De la place sur le disque et du temps : convertir un OAR est lourd (§ 8).

## 2. Lancer

Une seule ligne PowerShell, le premier dossier contient les OAR, le second sera le site :

```powershell
python .\oars2site.py "P:\chemin\OAR" "P:\chemin\site"
```

Pour voir ce qui serait fait, sans rien écrire :

```powershell
python .\oars2site.py "P:\chemin\OAR" "P:\chemin\site" --dry-run
```

Les OAR sont traités un par un, jamais en parallèle. Un OAR déjà converti (son `NOM.config.json` est plus récent que l'OAR) est sauté ; un OAR qui échoue est noté dans son journal, ne laisse pas de dossier à moitié fait si la région est nouvelle, et le suivant continue. Le code de sortie est 1 si au moins un OAR a échoué.

## 3. Ce qui est produit

Dans le dossier du site :

- `index.html`, `lib/`, `default.json` et `regions.json` à la racine : la coquille commune, créée une fois puis tenue à jour ; `regions.json` alimente la carte des mondes ;
- `carte.html` à la racine : la page de la carte des mondes, copiée au début si elle n'existe pas (une carte déjà là n'est jamais écrasée) ;
- un dossier par région, `NOM/`, avec `NOM.config.json`, `NOM.zones.json` et le GLB : `NOM.glb`, ou `NOM.tiles.json`, `NOM.tiles/` et `NOM.overview.glb` quand `glb2tiles.py` décide qu'il faut des tuiles (régions lourdes) ;
- une région est ensuite à l'adresse `index.html?region=NOM/NOM`, servie par n'importe quel serveur web statique.

Le nom de la région vient du nom du fichier, réduit aux lettres, chiffres, `_` et `-` : `Plage Sud.oar` donne `Plage_Sud`. Deux OAR qui donnent le même nom arrêtent l'outil avant tout travail.

## 4. Les options principales

| Option | Effet |
| --- | --- |
| `--only` | expression régulière : seulement les OAR dont le nom correspond |
| `--tex-size` | réduit les textures ordinaires à N pixels de côté au plus (§ 5) |
| `--tex-quality` | compresse les textures ordinaires en JPEG de qualité Q (§ 5) |
| `--pbr-size` | côté maximal des textures PBR (défaut 512) |
| `--split` | `auto` (défaut : `glb2tiles.py` décide), `never` (un seul GLB) ou `always` (des tuiles) |
| `--thumbs` | dossier de vignettes `NOM.jpg`, `NOM.png` ou `NOM.webp` pour la carte des mondes |
| `--force` | refait les régions déjà converties (écrase leur config et leurs zones) |
| `--reuse-glb` | utilise un `NOM.glb` déjà présent à côté de l'OAR au lieu de lancer `oar2glb.py` |
| `--keep-work` | garde les fichiers de travail de chaque région |
| `--work` | dossier de travail et de journaux (défaut : à côté du site) |
| `--timeout-min` | arrête une étape après ce nombre de minutes |
| `--vendor` | dossier local de three.js, pour travailler hors ligne |
| `--tools` | dossier des trois outils (défaut : à côté du script, puis `dist`) |
| `--oar2glb-arg`, `--html-arg` | argument supplémentaire transmis à `oar2glb.py` ou à `glb2html.py` (répétable) |
| `--lang` | langue des messages : `fr`, `en` ou `auto` |

Toutes les options, avec leurs valeurs par défaut : `docs/REFERENCE_OPTIONS.md`.

## 5. Régler les textures

`--tex-size` change le nombre de pixels ; `--tex-quality` règle la compression JPEG sans changer les pixels ; les deux peuvent se combiner. Le GLB est plus léger et les textures moins utiles à qui l'enregistre ; la géométrie n'est pas touchée et la région est plus floue de près. Les textures transparentes restent en PNG (réduites si elles sont trop grandes, jamais recompressées) et les images des matériaux PBR ne sont pas concernées.

Pour choisir N sans deviner :

1. À la fin de chaque conversion, `oar2glb.py` affiche le nombre et le poids des textures ordinaires par tranche de plus grand côté, avant toute réduction. Il est dans le journal de la région, `NOM_work/logs/NOM.log`. Exemple (images d'essai) :

```
[textures] 3 textures ordinaires, 0.9 Mo (plus grand côté : 512 px), tailles d'origine :
    jusqu'à 256 px : 1 textures, 0.0 Mo
    257 à 512 px : 2 textures, 0.9 Mo
```

2. Pour un GLB déjà fait, `glb-stats.py NOM.glb` donne le même tableau.
3. Pour essayer des valeurs sans refaire la conversion, `oar2glb.py --tex-only NOM.glb --tex-size 1024` écrit `NOM-tex1024.glb` à côté de l'original, qui n'est jamais modifié, et affiche le poids avant et après et la durée. Copie ensuite le fichier choisi à la place du GLB de la région dans le site.

## 6. Journaux et rapport

Les fichiers de travail et les journaux sont écrits hors du dossier du site (par défaut `NOM_DU_SITE_work`, à côté de lui), pour qu'ils ne soient jamais servis par le serveur web :

- `logs/NOM.log` : tout ce que les outils ont affiché pour la région, dans la langue du script ;
- `logs/_scan-sites.log` : la mise à jour de `regions.json` ;
- `conversion_report.json` : pour chaque OAR, son état (`ok`, `skipped` ou `failed`), son adresse, son mode (`glb` ou `tiles`) et sa durée, pour que les scripts d'un site s'en servent.

Le dossier de travail d'une région est supprimé à la fin, y compris après un échec : le journal suffit à comprendre.

## 7. Le GLB publié peut être téléchargé

La page charge la région en téléchargeant son GLB (ou ses tuiles) et ses fichiers JSON par HTTP ordinaire. Web_3d ne les chiffre pas et ne les cache pas : toute personne qui peut ouvrir la page peut enregistrer le GLB, avec la géométrie et les textures de l'OAR, et un nom de région illisible n'y change rien, car `default.json` le donne.

Pour des OAR payants, c'est donc à toi de décider ce que tu acceptes de montrer :

- dégrader les textures (§ 5) ;
- ne montrer que des OAR gratuits ou une région d'aperçu ;
- côté serveur web, hors de Web_3d : exiger une connexion pour le dossier du site, ou refuser les requêtes qui ne viennent pas de tes propres pages (cela arrête les liens depuis d'autres sites, pas un visiteur décidé).

## 8. Limites et ce qui n'est pas essayé

- Une seule mesure de charge : un OAR de 1,45 Go a pris environ 2 min 12 s avec `--pbr-size 256`, sous Windows, et la mémoire est montée à 61 Go (cause non établie). Lance les plus gros OAR d'abord en essai, un à la fois.
- Essayé avec un faux convoar seulement : dossier d'OAR converti en site, OAR sauté, échec qui ne bloque pas les autres, tuiles puis retour à un GLB seul, vignettes, `carte.html` copiée, échec de `glb2html.py` sans dossier à moitié fait, options de textures, langues, délai dépassé.
- Non essayé : un vrai OAR avec le vrai convoar, Windows, macOS, et une grande région par le chemin des tuiles.
