# Étude : tuiles hébergées ailleurs et « méga-région »

*Rédigée le 03/11/2026 à la demande de Klaatou, **sans aucun code**. Aucune décision n'est prise : tout ce qui suit est une proposition à valider (règle 21 : ne pas rouvrir les décisions arrêtées sans demande de Klaatou ; ici, c'est lui qui la demande). Ce document est interne, en français ; il ne remplace ni le manuel ni `REPRISE.md`.*

## 1. Objectif

Une **méga-région** : une page unique où le visiteur marche d'une région à l'autre, chaque région restant **hébergée par son créateur** (sur son propre site). La page de la méga-région ne contient pas les modèles : elle sait où les trouver, combien ils pèsent, à quelle position les poser, et prévient le visiteur quand il passe chez un autre hébergeur.

## 2. Ce que le code fait aujourd'hui (vérifié)

- Les tuiles (`glb2tiles.py`) sont décrites par un index `X.tiles.json` (liste de `file`, `min`, `max`) ; le champ `tiles` de la configuration désigne cet index.
- **Tout est relatif à la page** : `safeRel` (`src/core.js:537`) refuse un chemin qui commence par `/` ou `\`, contient `:`, `?`, `#`, un caractère de contrôle, un segment vide ou `..`. Il s'applique à l'index (`core.js:840`), à chaque tuile (`core.js:859`) et à la vue d'ensemble (`core.js:886`). Message : « adresse de tuiles refusée » (manuel : le champ `tiles` doit être un chemin relatif simple).
- La source des fichiers est `urlSource()` : adresses http relatives à la page.
- **Précédent** : le dossier de la bibliothèque 3D peut déjà être une adresse complète (`lib_url`, `gen_tpl.py:926`). L'idée d'adresse externe n'est donc pas étrangère au projet.
- Plafonds existants : `--tile-radius` (150 m), `--tile-margin`, `--tile-max-mb` (200 Mo chargés en même temps), `--tile-max-triangles` (8 millions). Ils limitent le total chargé en même temps, pas la taille d'un fichier isolé.
- **Aucune politique CSP** dans la page (vérifié).
- Décodeurs Draco et meshopt toujours présents dans la coquille (`gen_tpl.py:903-904`).
- La carte des mondes connaît déjà les régions par leurs coordonnées de grille OpenSim (`x`, `y`, manuel § 27.6) et accepte une adresse complète par région.

## 3. Risques, et leurs parades

Réponse à la question de Klaatou (« ces risques ne sont-ils pas ceux d'un site normal, avec des iframes par exemple ? ») : **oui pour l'essentiel, c'est la même famille de risques que le web ordinaire** (contenu tiers, vie privée, images distantes) et on la traite avec les mêmes outils (liste d'hôtes autorisés, politique CSP, empreintes). Deux différences : (a) une `iframe` est **isolée** par le navigateur, alors que des tuiles chargées dans la scène sont des données dans le contexte de la page, présentées comme faisant partie de **sa** méga-région ; (b) un GLB n'exécute pas de script, mais il peut figer l'affichage (trop de triangles, fichier énorme).

| Risque                                                                                      | Parade proposée                                                                                                                                                         |
| ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Le créateur change ses tuiles après coup (contenu, poids)                                   | **Manifeste** avec `bytes` et `sha256` par tuile (voir § 4.1) ; la page vérifie la taille avant, l'empreinte après le téléchargement ; une tuile différente est refusée |
| Fichier énorme                                                                              | plafond par fichier (en plus des plafonds existants), vérifié sur `bytes` puis sur `Content-Length`                                                                     |
| Vie privée du visiteur (IP, navigateur, adresse de la page vue par l'hébergeur)             | bandeau d'information + **accord par hébergeur** mémorisé (§ 4.5) ; `credentials: 'omit'`, `referrerPolicy: 'no-referrer'`                                              |
| Adresses cachées **dans** un GLB (image distante, requête vers le réseau local du visiteur) | gestionnaire d'URL du chargeur qui refuse toute adresse hors liste ; CSP (`connect-src`, `img-src`) écrite par `glb2html` à partir de la liste d'hôtes                  |
| Lien fabriqué qui impose des tuiles étrangères à ta page                                    | adresses externes acceptées **uniquement** depuis le fichier de configuration de la méga-région (même origine), avec liste d'hôtes ; **jamais** depuis `?` ni `#`       |
| Décodeurs WASM lisant un fichier malformé                                                   | bac à sable du navigateur ; risque déjà présent aujourd'hui ; limité par l'allowlist                                                                                    |
| Noms ou `extras` affichés comme du HTML                                                     | à auditer : tout doit passer par `textContent` (déjà le cas pour les pseudos, testé)                                                                                    |
| Hébergeur indisponible ou lent                                                              | la tuile manquante est ignorée avec un message ; la région voisine continue                                                                                             |
| Droits et bande passante des créateurs                                                      | accord explicite de chaque créateur ; champ « licence » et « contact » dans le manifeste                                                                                |

**Signature.** Klaatou propose un élément produit par un script chez le créateur : c'est le manifeste. Version minimale proposée : **empreintes SHA-256** (la fonction `crypto.subtle.digest('SHA-256')` existe dans tous les navigateurs courants) ; la méga-région **épingle** l'empreinte du manifeste de chaque source. Une vraie **signature** (clé publique du créateur) est une option ultérieure ; je ne l'affirme pas disponible partout (Ed25519 dans WebCrypto : à vérifier avant de s'y fier).

## 4. Conception proposée

### 4.1 Manifeste d'hébergement (produit chez le créateur)

`X.tiles.json` étendu, ou `X.host.json` à côté : `source` (nom de la région, créateur, adresse de sa page, licence, contact, texte de présentation court), et pour chaque tuile `file`, `min`, `max`, **`bytes`**, **`sha256`**. Un script (par exemple `glb2tiles.py --manifest`, ou un petit outil à part) le calcule ; il peut aussi compresser les tuiles (voir `REPRISE.md` § 6, essai `gltfpack`).

### 4.2 Index de méga-région (chez celui qui l'assemble)

`X.mega.json` : liste de **sources**, chacune avec `id`, `base` (adresse https de la région du créateur), **position** (coordonnées de grille OpenSim `x`, `y`, multipliées par 256 m, ou décalage `x`, `z` en mètres), vue d'ensemble (adresse du `.overview.glb` du créateur), **épingle** (`sha256` de son manifeste), plafond propre (`maxMb`). La configuration porte la liste d'hôtes autorisés (`megaHosts`).

### 4.3 Chargeur

`urlSource(base)` accepte une adresse https complète **seulement** si son hôte est dans `megaHosts` ; vérifie la taille (manifeste puis `Content-Length`) ; vérifie le `sha256` avant d'analyser ; refuse toute autre adresse rencontrée **dans** le GLB (gestionnaire d'URL du chargeur). Les plafonds existants restent valables et s'appliquent au total, toutes sources confondues.

### 4.4 Vue d'ensemble

Pas de GLB géant à fabriquer : la page charge la vue d'ensemble légère de chaque source (`glb2tiles` l'écrit déjà) et la pose à sa position. Il suffit donc de **coordonnées précises par source**. Reste à s'entendre sur des **conventions de raccord** (non codables, à discuter avec les créateurs) : même niveau d'eau (20 m par défaut), hauteur de terrain au bord (ou bande de transition d'une quinzaine de mètres avec fondu), côté de région de 256 m, repère commun. Option du visionneur envisagée : un fondu de bord par source (`edgeFade`).

### 4.5 Information du visiteur

Proposition de Klaatou, retenue : **un panneau** quand le visiteur entre dans le rayon de tuiles d'un autre hébergeur : nom de la région, créateur, hébergeur (nom de domaine), licence, texte de présentation, lien vers la page du créateur, poids chargé depuis cet hébergeur. C'est une **amélioration sur le web ordinaire**, où seule la barre d'adresse renseigne. Première entrée chez un hébergeur : demande d'accord (mémorisé sur l'appareil, révocable).

## 5. Lots proposés (dans cet ordre)

1. **Outil de manifeste** (`bytes`, `sha256`, option de compression) ; sans changement du visionneur.
2. **Chargeur inter-sites** : liste d'hôtes, plafond par fichier, empreintes, gestionnaire d'URL, CSP écrite par `glb2html` ; désactivé par défaut.
3. **Index de méga-région** et vue d'ensemble assemblée à l'exécution, avec positions.
4. **Panneau d'information et accord** par hébergeur.
5. **Documents** FR et EN (règle 16), après validation par Klaatou.

## 6. Plan de test (sans réseau extérieur)

Deux serveurs http locaux sur deux ports différents (deux **origines** distinctes) : la méga-région sur l'un, une « région de créateur » sur l'autre. Cas : tuile servie normalement ; en-têtes CORS absents (refus propre) ; tuile dont l'empreinte ne correspond plus (refusée) ; tuile plus grosse que son `bytes` (refusée) ; GLB contenant une image distante (adresse bloquée, aucune requête partie) ; hôte absent de la liste (refusé) ; adresse externe dans `?` (ignorée) ; panneau affiché à l'entrée, accord mémorisé ; plafonds respectés ; noms hostiles affichés en texte.

## 7. Questions ouvertes pour Klaatou

- Empreinte épinglée seule (simple), ou signature par clé publique du créateur (plus lourd) ?
  Réponse : empreinte simple dans un premier temps, je me demande meme si ça n'est pas trop contraignant en cas de petite modifs du GLB...
- Accord du visiteur obligatoire à chaque nouvel hébergeur, ou simple bandeau ?
  Non, on verra a l'avenir si integre ça dans le "manifest" ou pas
- Qui tient la liste des hôtes autorisés et comment un créateur y entre-t-il ?
  Il me semblait avoir compris que c'est l'hébergeur de la Méga Région et pour y entrer, c'est avec la fourniture tu manifeste de la tuile/région proposée par le créateur avec l'outils diffusé.
- Mention des droits d'auteur et accord écrit de chaque créateur : sous quelle forme ?
  à voir ...
- Où héberger **la** page de la méga-région (même question d'adresse IP que pour la région « Houses » : voir `REPRISE.md` § 6) ?
  A voir ... chez moi on un vps pour le coup ! comme la carte générale ...

## 8. Ce que cette étude ne règle pas

La **taille** des régions (voir l'essai de compression dans `REPRISE.md` § 6) et leur **hébergement** (GitHub Pages, Cloudflare Pages, etc.) sont des questions voisines mais indépendantes : chaque créateur choisit le sien.

## 7. Questions ouvertes de Klaatou à Claude

- La compression est elle appliqué à la conversion des OAR au GLB uniques produit (sans les tuiles) ?
