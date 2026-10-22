# Mode d'emploi : zones, portails et points d'arrivée (v29)

## 1. La règle qui explique 90 % des pannes

Chaque zone a deux noms :

| Champ | À quoi il sert | Qui le lit |
|---|---|---|
| **Identifiant** | le nom technique de la zone | les portails, la carte des mondes, les liens `#spawn=` |
| **Nom affiché** | le texte vu par le visiteur (« E : Empereur ») | uniquement l'écran |

**Un portail désigne toujours une arrivée par son Identifiant, jamais par son Nom affiché.**
L'identifiant est automatiquement mis en minuscules, et tout caractère autre que lettre non accentuée, chiffre, `-` ou `_` y devient un tiret (`Salle du Trône` devient `salle-du-tr-ne`). Écris-le directement en minuscules, sans accent ni espace, pour éviter les surprises.

Exemple juste :

- Arrivée : Identifiant `empereur`, Nom affiché `Salle de l'Empereur`
- Portail : Point d'arrivée `empereur`

## 2. Les touches

| Touche | Effet |
|---|---|
| **F** | entrer ou sortir de la promenade |
| **E** | utiliser la zone proche (son nom s'affiche en bas : « E : … ») |
| **P** | dans le viewer, en promenade : poser la zone à tes pieds |
| **M** | ouvrir la carte des mondes |

Les portails ne fonctionnent qu'en promenade.

### Clic et double-clic (vue globale du viewer)

| Geste | Effet |
|---|---|
| **clic simple** sur le modèle | affiche, dans le bloc « picked » et la barre d'état, le **nom de l'élément** et les **coordonnées du point touché** (x, y, z, 2 décimales). Rien ne bouge : ni la cible, ni le cercle d'atterrissage. |
| **double-clic** sur le modèle | choisit la **cible** de la vue et le **point d'atterrissage** (comme dans la page exportée) |

Deux cercles à ne pas confondre :

- le **petit cercle** (noir et blanc, posé sur le sol) est le **repère d'atterrissage** : il montre où l'avatar apparaîtra en appuyant sur F. Il suit la cible, donc il ne change qu'au double-clic ;
- le **grand cercle** (cylindre translucide avec son nom) est une **zone** : son rayon est celui de la fiche de la zone. **Il n'existe que dans le viewer** (voir § 2 bis).

## 2 bis. Ce que voit le visiteur : les liens se comportent comme sur le web

Dans le **viewer** (édition), chaque zone non liée garde son **cylindre translucide**, toujours visible, pour la repérer et la positionner (les panneaux aussi) ; une zone liée à un élément y est entourée d'un contour. Rien de tout cela n'est exporté.

Dans la **page exportée** (autonome ou modulaire), il n'y a **aucun cylindre** pour les zones lien web, commande Home Assistant et portail :

| Zone | Ce qui est ajouté dans la scène | Au survol |
|---|---|---|
| **liée à un élément** | **rien** | le curseur devient une **main**, l'élément reçoit un léger **contour**, une **infobulle** affiche le nom et la destination |
| **non liée** | un **marqueur discret au sol** (petit disque plat de 0,4 m, semi-transparent, avec un anneau fin) | même chose : main, infobulle, le marqueur s'éclaircit |

L'infobulle donne le **nom** puis la **destination** : l'adresse web pour un lien, « Région : adresse (#arrivée) » pour un portail (« cette région » si la destination est vide), « Commande : nom » pour une commande Home Assistant (l'adresse du webhook n'est **jamais** affichée). Un **clic** suit le lien. Un portail réglé « en marchant dedans » reste sans survol (il se déclenche seul).

Aucun panneau de texte permanent : le nom ne s'affiche qu'au survol, ou quand on est à portée (« E : … » en bas de l'écran).

**Toujours afficher le nom** (fiche de la zone, **décochée par défaut**) : garde un nom visible en permanence, au-dessus de l'élément ou du marqueur ; pour une zone non liée de forme « panneau », c'est le panneau complet qui est affiché.

*Changement depuis la v23* : les zones non liées de forme « panneau » ne sont plus dessinées dans la page exportée, sauf si **Toujours afficher le nom** est coché.

## 3. Poser une zone

Dans le viewer, section **Zones : panneaux, portails, liens, commandes** :

1. **Type à poser** : choisis le type.
2. Pose-la, au choix :
   - clique sur **Poser une zone par un clic sur la scène**, puis clique dans la scène ;
   - ou, en promenade, place-toi au bon endroit et appuie sur **P** (un cercle sous tes pieds, ou un panneau 2 m devant toi, tourné vers toi).
3. La zone apparaît dans la liste : ouvre sa fiche pour la régler.
4. **Voir cette zone** recadre la vue dessus ; **Supprimer** l'efface.
5. **Placer ici (dernier point cliqué)** copie x, y, z du dernier clic simple sur le modèle dans la position de la zone : clique sur le modèle (les coordonnées s'affichent dans « picked »), ouvre la fiche, puis clique sur ce bouton.

## 4. Point d'arrivée

C'est l'endroit où un visiteur apparaît.

| Champ | Réglage |
|---|---|
| Identifiant | le nom que les portails utiliseront (`empereur`, `temple`, `default`…) |
| Nom affiché | libre |
| Position X / Y / Z | Y est la hauteur |
| Orientation (degrés) | la direction dans laquelle le visiteur regarde en arrivant |

Pose-le en promenade avec **P**, en regardant dans la direction voulue : position et orientation sont prises d'un coup.

L'arrivée d'identifiant **`default`** est spéciale : c'est là qu'arrive un visiteur quand rien d'autre n'est précisé (portail sans point d'arrivée, arrivée demandée introuvable, venue depuis la carte sans réglage). Mets-en une dans chaque région.

## 5. Portail vers un autre endroit de la même région

| Champ | Réglage |
|---|---|
| Page de destination | **vide** (le nom de la page elle-même marche aussi) |
| Point d'arrivée dans cette page | l'**Identifiant** de l'arrivée visée |
| Déclenchement | voir § 8 |

Effet : fondu au noir, puis le visiteur est posé sur l'arrivée, orienté comme elle. La page n'est pas rechargée : il reste connecté à la présence et au chat.

Si l'arrivée n'existe pas, un message « Point d'arrivée … introuvable dans cette région » s'affiche.

## 6. Portail vers une autre région

| Champ | Réglage |
|---|---|
| Page de destination | l'autre page : `autre-region.html` si elle est dans le même dossier, sinon son adresse complète `https://…/autre-region.html`. Avec une coquille commune (§ 16) : `index.html?region=AutreRegion` (le `#spawn=` s'ajoute après) |
| Point d'arrivée dans cette page | l'**Identifiant** d'une arrivée **de l'autre page** (vide = `default`) |

Effet : fondu, chargement de l'autre page, le visiteur y arrive directement en promenade, avec son pseudo.

À vérifier :

- l'autre page doit exister à cette adresse et avoir la promenade activée ;
- l'arrivée visée doit exister **dans l'autre page**, pas dans celle-ci ;
- seules les adresses `http`, `https` et les fichiers locaux sont acceptés.

## 7. Panneaux

### Lien web

| Champ | Réglage |
|---|---|
| Adresse web | `https://…` |

Approche-toi et appuie sur **E** (ou clique) : la page s'ouvre dans un nouvel onglet.

Formats acceptés pour l'adresse (aussi pour la page de destination d'un portail) :

| Format | Exemple | Remarque |
|---|---|---|
| adresse web | `https://monsite.fr/ile.html` | marche partout |
| fichier `.html` relatif | `autre-ile.html` | relatif à la page qui contient la zone |
| fichier local | `file:///P:/web/autre-ile.html` | **sans guillemets** ; ne marche que si la page elle-même est ouverte depuis le disque |

Les espaces s'écrivent `%20` (`file:///P:/mes%20pages/ile.html`). Toute autre forme (`javascript:`, `ftp:`…) est refusée.

### Commande Home Assistant

| Champ | Réglage |
|---|---|
| Adresse du webhook Home Assistant | l'adresse du webhook de ton automatisation |
| Demander confirmation | coché : le visiteur doit valider avant l'envoi |

Effet : envoi d'une requête POST au webhook avec deux valeurs, `zone` (le nom affiché) et `visitor` (le pseudo). Une même commande ne peut pas repartir avant 3 s. La page ne reçoit pas la réponse de Home Assistant : « Commande envoyée » veut dire envoyée, pas exécutée.

## 8. Déclenchement, forme et taille

**Déclenchement** (portails) :

| Choix | Effet |
|---|---|
| en marchant dedans | le portail part dès qu'on entre dans le cercle |
| au clic ou touche E | il faut cliquer dessus ou appuyer sur E à proximité |
| les deux | l'un ou l'autre |

Un portail « en marchant dedans » sur lequel on arrive ne se déclenche pas tout de suite : il faut en sortir puis y rentrer. Deux portails qui se renvoient l'un vers l'autre ne font donc pas de ping-pong.

**Forme** :

| Choix | Réglage de taille |
|---|---|
| cercle au sol | Rayon (m) |
| panneau | Largeur, Hauteur, et Portée de la touche E (m) |

## 9. Lier une zone à un élément du modèle

Pour qu'un objet de la scène serve lui-même de déclencheur (une porte, une boîte…) :

1. Dans la fiche de la zone, clique sur **Lier à un élément**.
2. Clique sur l'objet dans la scène.
3. La fiche indique l'élément lié. Le champ de taille devient « Distance de déclenchement… (m, depuis l'élément) ».

Le visiteur déclenche alors la zone en cliquant sur l'objet, ou avec E quand il en est assez près. **Délier** remet la zone à sa position propre.

**Un seul morceau est lié** : celui sur lequel tu as cliqué. Si plusieurs objets du modèle portent le même nom (fréquent dans un OAR), la zone mémorise `nom#index` (le rang de l'objet parmi ceux de ce nom) au lieu du nom seul : les autres objets de même nom ne sont pas touchés.

**Limite : 10 m.** Un élément dont une dimension dépasse 10 m est refusé avec le message « Élément trop grand (L × l × h m) : probablement fusionné avec un bâtiment dans l'OAR… ». Cause : un objet appartenant à un **linkset** OpenSim est fusionné avec lui dans le GLB ; il n'existe plus seul, et on ne peut pas le lier. Deux remèdes :

- le **délier dans OpenSim** (Unlink) avant d'exporter l'OAR, puis régénérer le GLB ;
- ou garder le bâtiment tel quel et poser dessus une **zone cercle** (Forme : cercle au sol), avec le bouton **Placer ici** pour la positionner.

## 10. Zones privées

**Privé (absent de l'export public)** coché : la zone reste dans tes exports « perso », mais disparaît des exports « public ». Le choix se fait dans **Profil d'export** :

- **perso : toutes les zones**
- **public : sans les zones privées**

Une arrivée privée disparaît aussi de l'export public : un portail public qui la vise tombera sur `default`.

## 11. Carte des mondes

Dans la section **Carte des mondes**, le champ **Point d'arrivée des visiteurs (identifiant)** dit où arrive quelqu'un qui vient de la carte. Le viewer indique sous ce champ :

- ✔ si cette arrivée existe dans la région ;
- ⚠ sinon (le visiteur apparaît alors au point de départ habituel de la touche F).

### Rotation de la région

Quand l'OAR arrive tourné (ou l'île inversée nord-sud sur la carte), la section **Région** du viewer propose **Rotation de la région** : 0, 90, 180 ou 270° autour de l'axe vertical. Le modèle tourne, et du même angle, autour du centre de la région : les zones (position et orientation), les points d'arrivée, la cible et le cercle d'atterrissage, le trou de la mer. Les zones liées suivent leur élément. La barre d'état annonce « Région tournée de N° : M zone(s) déplacée(s). Recapture la vignette. »

La rotation est mémorisée comme les autres réglages, et reprise dans la commande (`--rotate 180`), dans `.reglages.json` et dans `<page>.config.json`. La page générée applique la rotation au chargement ; les zones du fichier sont déjà dans le repère tourné : ne tourne pas deux fois.

**Après une rotation**, la vignette de la carte ne correspond plus au modèle :

1. section **Carte des mondes** : **Capturer la vignette (vue du dessus)** ;
2. **Ajouter / mettre à jour cette région dans la carte** ;
3. **Exporter regions.json** (puis régénérer ou republier les pages qui l'embarquent).

## 12. Publier les changements

Les zones se règlent dans le viewer, mais une page déjà publiée ne les voit qu'après publication :

| Ta page est… | Que faire après avoir modifié les zones |
|---|---|
| **autonome** (un seul .html) | **Exporter HTML autonome**, puis remplacer l'ancienne page |
| **modulaire** (coquille + .glb + .json) | **Exporter zones (.json)**, renommer en `<nom de la page>.zones.json`, remplacer l'ancien, puis F5 dans la page |

Les zones peuvent aussi être sauvées et rechargées avec **Exporter zones (.json)** / **Importer zones (.json)**, par exemple pour les copier d'une région à l'autre.

**Après un changement de version** de glb2html (comme v21 → v22), les pages existantes gardent l'ancien comportement : il faut les régénérer. En modulaire, c'est la coquille `.html` qui change : régénère-la, un simple remplacement des `.json` ne suffit pas.

## 13. Dépannage

| Symptôme | Cause probable | Remède |
|---|---|---|
| Rien ne se passe en entrant dans un portail | pas en promenade | appuie sur F |
| | déclenchement réglé « au clic ou touche E » | appuie sur E, ou passe en « en marchant dedans » |
| | tu étais déjà dans le cercle en arrivant | sors du cercle puis rentre |
| « Point d'arrivée … introuvable » | le portail contient le **Nom affiché** au lieu de l'**Identifiant** | recopie l'Identifiant exact de l'arrivée (§ 1) |
| Arrivée au mauvais endroit dans une autre région | l'arrivée visée n'existe pas dans l'**autre** page, ou elle est privée et la page est publique | crée-la dans l'autre page, ou décoche Privé |
| Écran noir après un portail interne | page générée avant la v22 | régénère la page |
| « Portail sans destination valide » | adresse mal écrite, ou protocole non accepté | `https://…` ou nom de fichier `.html` |
| La zone marche dans le viewer, pas dans la page | page pas republiée | voir § 12 |
| Commande HA « envoyée » mais rien ne bouge | webhook faux, ou automatisation désactivée | teste le webhook directement depuis Home Assistant |
| Une zone supprimée revient après rechargement | le viewer restaure les réglages mémorisés pour ce fichier, ou l'ancien `.reglages.json` / `zones.json` a été rechargé | supprime-la (**Supprimer**), attends 2 s (mémorisation automatique), ou **Oublier les réglages de ce fichier** (§ 14) ; vérifie aussi `zones.json` / `<page>.zones.json` |
| La liaison prend un objet de 30 m | (avant v23) l'objet est fusionné avec un bâtiment dans l'OAR ; la limite était de 30 m | v23 : limite de 10 m et message explicite ; délie l'objet dans OpenSim (Unlink) ou pose une zone cercle (§ 9) |
| Le cercle d'atterrissage « saute » | (avant v23) chaque clic simple déplaçait la cible | v23 : seul le **double-clic** le déplace ; le clic simple affiche nom et coordonnées |
| L'île est inversée nord-sud sur la carte | l'OAR est exporté dans l'autre orientation | **Rotation de la région** : 180° (§ 11), puis recapturer la vignette, mettre à jour la région dans la carte et réexporter `regions.json` |

## 14. Réglages mémorisés

Le viewer mémorise **tout** (zones comprises, mais aussi trou, vagues, caméra, rotation, carte, fiche de région…) **par fichier `.glb`** dans le navigateur (clé : nom + taille du fichier). Il enregistre seul, environ toutes les 1,5 s après une modification. Au rechargement du même `.glb`, tout est restauré, et la barre d'état indique « Réglages restaurés depuis la mémoire du navigateur (N zone(s)) ».

Conséquences :

- une zone ajoutée ou supprimée est retrouvée telle quelle au rechargement ; pour **supprimer une zone**, ouvre sa fiche et clique sur **Supprimer** (attends 2 s avant de fermer l'onglet) ;
- la mémoire est propre au navigateur et à l'adresse de la page du viewer : un autre navigateur ou un autre ordinateur ne voit rien. Pour transporter les réglages : **Enregistrer dans un fichier** (`.reglages.json`) puis **Charger depuis un fichier**, ou `glb2html.py --settings` ;
- **Oublier les réglages de ce fichier** (section Réglages mémorisés) efface la mémoire de ce `.glb` : les valeurs actuelles restent à l'écran, mais ne sont plus protégées, et elles seront mémorisées de nouveau à la prochaine modification. Pour repartir de zéro : cliquer ce bouton puis recharger la page du viewer et rouvrir le `.glb`.

## 15. Convertir un OAR en GLB (`tools/oar2glb.py`)

`oar2glb.py` transforme une sauvegarde de région OpenSim (`.oar`) en un seul fichier `.glb` prêt pour le viewer et pour `glb2html.py`. Il lance convoar, répare sa sortie et assemble le tout. La sortie est écrite à côté de l'OAR : `X.oar` donne `X.glb`.

### Les commandes (PowerShell, une seule ligne)

Se placer d'abord dans le dossier du script : `cd "P:\_OpenSim\SL&OS\Web_3d"`.

| Besoin | Commande |
|---|---|
| Conversion normale | `python oar2glb.py "J:\...\X.oar"` |
| Conversion qui garde les dossiers intermédiaires (nécessaire pour `--diag`) | `python oar2glb.py "J:\...\X.oar" --keep` |
| Retrouver les animaux dans le viewer (mât rouge de 15 m à chacun) | `python oar2glb.py "J:\...\X.oar" --keep --reperes` |
| Garder les prims invisibles | `python oar2glb.py "J:\...\X.oar" --keep-invisible` |
| Vérifier ce que le script voit, sans rien modifier | `python oar2glb.py "J:\...\X.oar" --diag` |
| Idem, en désignant le GLB ou le `.gltf` à comparer | `python oar2glb.py "J:\...\X.oar" --diag --glb "J:\...\X-GLTF\fichier.gltf"` |
| Ne pas attendre « Entrée » à la fin | ajouter `--nopause` |
| Ajouter le terrain complet à un GLB existant, sans relancer convoar | `python oar2glb.py "J:\...\X.oar" --terrain-seul "J:\...\X.glb"` (écrit `X-terrain.glb`) |

Avant de refaire une conversion, supprimer l'ancien dossier intermédiaire : `Remove-Item -Recurse -Force "J:\...\X-GLTF*"`.

### Les options

| Option | Effet |
|---|---|
| `--keep` | garde le dossier `X-GLTF` (images, tampons, `.gltf`) ; indispensable pour lancer ensuite `--diag` |
| `--keep-invisible` | garde les prims entièrement transparents (retirés par défaut) |
| `--reperes` | ajoute un mât rouge de 15 m à chaque animal riggé posé ; le nom du nœud donne l'animal et sa taille ; à retirer en relançant sans l'option |
| `--diag` | ne modifie rien et ne lance pas convoar : liste chaque partie de l'OAR (voir plus bas) |
| `--glb CHEMIN` | avec `--diag` : GLB ou `.gltf` à comparer ; par défaut le `.gltf` du dossier `X-GLTF`, sinon le `X.glb` voisin |
| `--max N` | hauteur maximale (m) d'un objet racine ; au-delà (skybox) il est retiré ; défaut 600 |
| `--convoar CHEMIN` | chemin de `convoar.exe` si ce n'est pas celui par défaut |
| `--reencode` | **à éviter** : réencode les textures avant convoar ; sur Jungle_Isle il faisait manquer environ 150 textures sur 353 (textures grises). À n'utiliser que si convoar affiche beaucoup d'erreurs « unhandled number of components » ou plante dans `OpenJPEG.DotNetDecode64` (code retour 3221225477). Les textures que Pillow ne sait pas lire sont remplacées par un gris 4x4 (liste dans `X-reenc-illisibles.txt`, à côté de l'OAR) pour ne pas les laisser au décodeur de convoar ; les sculpt maps restent intactes ; 8 cœurs au plus et envoi par lots de 512 pour limiter la mémoire |
| `--nopause` | ne pas attendre « Entrée » à la fin (la pause est aussi supprimée quand il n'y a pas de console, et avec `--terrain-seul`) |
| `--terrain auto\|oui\|non` | terrain complet depuis la carte de hauteurs (voir plus bas) ; `auto` par défaut |
| `--terrain-patch N` | côté d'un patch de terrain en mètres, de 2 à 255 ; défaut 64 |
| `--terrain-seul GLB` | ne lance pas convoar : ajoute le terrain complet à ce GLB et écrit `X-terrain.glb` à côté (l'original n'est jamais modifié) |
| `--sortie FICHIER` | avec `--terrain-seul` : fichier de sortie à la place de `X-terrain.glb` (jamais l'original) |

### Terrain complet des régions de plus de 256 m (v29)

convoar ne produit qu'**un** nœud « Terrain » dont l'étendue plafonne (par exemple 257 x 267 m sur une région de 1 024 m : un seizième de la région n'a pas de sol). La carte de hauteurs complète est dans l'OAR (`terrains/*.r32`, un échantillon par mètre). `oar2glb.py` s'en sert pour construire le sol :

- **Patches.** Des carrés de P x P mètres (`--terrain-patch`, 64 par défaut), chacun un mesh de (P+1)² sommets. Les bords sont partagés entre voisins (mêmes hauteurs, mêmes normales, mêmes couleurs : pas de fissure, éclairage continu). Le dernier patch d'une rangée est plus petit quand n-1 n'est pas un multiple de P. Chaque patch est un objet racine nommé `Terrain i,j` (i : colonne vers l'est, j : rangée vers le nord). Repère monde : X = x, hauteur = h, Z = -y. Un seul matériau « terrain » (blanc, métal 0, rugosité 1, simple face), indices 16 bits, **pas de coordonnées de texture** : l'aspect vient de la couleur par sommet (`COLOR_0`).
- **Normales** par différences centrées sur toute la carte (une seule différence aux bords de la carte).
- **Couleur par sommet** d'après l'altitude `a` au-dessus du niveau d'eau et la pente :

| Situation | Couleur (rouge, vert, bleu) |
|---|---|
| `a` ≤ 0 (sous l'eau) | sable humide (166, 150, 104) |
| 0 < `a` ≤ 1 m | sable sec (214, 196, 142) |
| 1 à 4 m | passage progressif du sable sec à l'herbe |
| `a` ≥ 4 m | herbe, dégradé léger de (98, 146, 66) à `a` = 4 m vers (132, 140, 78) à `a` = 80 m |
| pente de 32 à 38 degrés | passage progressif vers la roche grise (122, 120, 116) ; au-delà de 38 degrés : roche |

- **Niveau d'eau.** `WaterHeight` lu dans `settings/*.xml` de l'OAR, sinon 20 m (défaut d'OpenSim). Le journal dit quelle valeur est utilisée et d'où elle vient.
- **Quand remplacer.** `--terrain auto` (défaut) : si le nœud « Terrain » de convoar existe et couvre moins de 95 % de la carte (boîtes comparées en repère monde), il est retiré de la scène et les patches sont ajoutés. Sinon (région de 256 m, terrain déjà complet, pas de nœud « Terrain ») le GLB n'est **pas modifié** : il est identique à celui de `--terrain non`. `--terrain oui` ajoute toujours les patches (et retire le « Terrain » de convoar s'il existe) ; `--terrain non` ne fait rien. Un GLB qui contient déjà des patches n'en reçoit pas d'autres. Le filtre des objets hors région ne retire jamais les patches.
- **`--terrain-seul GLB`** (sans relancer convoar, pour un GLB de plusieurs Go) : le GLB n'est **pas chargé en entier**. L'en-tête JSON est réécrit, le chunk binaire est recopié par morceaux de 8 Mo, les nouveaux tampons sont ajoutés à la fin. Sortie `X-terrain.glb` à côté de l'original (ou `--sortie`) ; l'original n'est jamais écrasé, et rien n'est écrit si le terrain de convoar est déjà complet. Les données de l'ancien « Terrain » restent dans le fichier, inutilisées (quelques Mo). Aucune pause « Entrée » à la fin.
- **Journal.** Ligne `[terrain] carte N x N échantillons (1 m) ; niveau d'eau E m (origine) ; K patch(es) de P m ; V sommets ; B Mo ajoutés ; durée`. Un OAR sans carte de hauteurs donne `cet OAR n'a pas de carte de hauteurs ... rien n'est modifié` (code de retour 0, aucune erreur).
- **Hors lot** : textures de terrain d'OpenSim (les quatre textures mélangées selon l'altitude), niveau de détail du terrain pour la vue d'ensemble.

Test : `python tests/terrain.py` (OAR et GLB synthétiques).

### Ce que le script corrige

- **Animaux riggés (animesh).** La géométrie que convoar écrit pour ces meshes est inutilisable (hippopotames géants, éléphants minuscules ou envolés, formes partagées entre animaux). Le script la reconstruit depuis le fichier `.llmesh` de l'OAR : positions, normales, UV, triangles, puis `bind_shape_matrix` ; l'échelle du prim est ignorée. Les morceaux d'un même animal restent ensemble. L'animal est centré sur la position de la racine de l'objet et ses pieds sont posés sous la boîte racine (à l'altitude de la racine si elle est elle-même riggée). Les textures viennent de convoar (face n du mesh = matériau n). Aucune règle ne dépend du nom d'un animal. Un animal dont la taille calculée sort de 0,1 à 12 m reste tel que convoar l'a produit (le journal le dit).
- **Prims invisibles.** Sont retirés : les prims dont toutes les faces sont à alpha 0 ou portent une texture invisible standard, les nœuds dont tous les matériaux sont transparents, et la boîte racine d'un animesh (prim simple, racine d'un objet dont tous les autres morceaux sont des meshes riggés). Les enfants d'une racine retirée restent.
- **Textures.** Le script compare les images annoncées par le `.gltf` aux fichiers présents ; s'il en manque, il relance convoar (2 essais de plus au maximum) en gardant les images déjà écrites.
- **Positions des régions plus grandes que 256 m** et objets hors région : traitement inchangé. Le terrain de ces régions est complété par les patches (voir « Terrain complet »).

### Lire le journal (`oar2glb.log`, à côté du script)

| Ligne | Sens |
|---|---|
| `[riggé] 'Nom' reconstruit depuis l'OAR : N face(s), M sommets...` | un morceau d'animal a été reconstruit ; les chiffres « convoar » à côté montrent ce que convoar avait écrit |
| `[riggé] 'Nom' : 5 morceau(x)... pieds à 27.11 m (dessous de la boîte racine)` | animal posé ; taille L x l x h et altitude des pieds |
| `[riggé] ... nœud GLB introuvable` | le morceau n'a pas été retrouvé dans le GLB ; lancer `--diag` |
| `[riggé] ... taille obtenue ... implausible` | garde-fou : l'animal est laissé tel que convoar l'a produit |
| `[invisible] node N 'Nom' retiré : ...` | prim retiré, avec la raison |
| `[correctif] N mesh(es) riggé(s) remis à l'échelle, M prim(s) invisible(s) retiré(s)` | récapitulatif |
| `[contrôle] 'Nom' pieds à ... : dans la boîte de N objet(s)` | objets dont la boîte englobante contient le centre de l'animal (indice si un animal est dans un rocher) |
| `[GLB] N texture(s) absente(s) sur M` | images manquantes, remplacées par du gris |
| `[terrain] ...` | décision (couverture du terrain de convoar) puis résumé des patches ajoutés |
| `[OK] ...glb (taille, meshes, textures)` | fin normale |

### Diagnostic : `--diag`

À lancer après une conversion faite avec `--keep`. Le journal est `oar2glb.diag.log`. Chaque partie de l'OAR donne une ligne : nom, UUID, racine ou enfant, riggé oui/non, échelle du prim, échelle de `bind_shape_matrix`, transparent oui/non, boîte racine d'animesh oui/non, et le nœud GLB trouvé avec la méthode (UUID du prim, UUID du mesh, nom + position). Les animaux et prims invisibles affichent en plus le résumé du `TextureEntry`, la matrice complète, le domaine de position et le matériau GLB. Une ligne « nœud introuvable » sur un animal ou un prim transparent signifie que le correctif ne s'appliquera pas à lui.

### Si quelque chose ne va pas

| Symptôme | Cause probable | Remède |
|---|---|---|
| Beaucoup de textures grises | `--reencode`, ou images non écrites par convoar | relancer sans `--reencode` ; lire `[GLB] N texture(s) absente(s)` |
| Un animal invisible ou à la mauvaise place | nœud non retrouvé, ou animal caché | `--keep --reperes`, puis `--diag` ; envoyer `oar2glb.log` et `oar2glb.diag.log` |
| Un animal avec la mauvaise texture | l'ordre des faces du mesh ne suit pas celui des matériaux de convoar | signaler l'animal avec son journal |
| Des prims transparents qu'on voulait garder | retirés par défaut | `--keep-invisible` |
| « convoar introuvable » | chemin différent | `--convoar "P:\...\convoar.exe"` |

`python oar2glb.py --version` affiche la version (`oar2glb v29 (22/10/2026)`) sans rien lancer ; la première ligne du journal (`oar2glb.log`, `oar2glb.diag.log`) la rappelle : `[oar2glb] v29 (22/10/2026)`. Joindre ce journal à tout signalement donne donc la version utilisée. Le fichier est fabriqué dans `dist/` par `python build.py`.

Test du script : `python tests/oar2glb.py` (OAR synthétique et faux convoar, sans réseau).

## 16. Fichiers JSON d'une région modulaire

Pour une page `Region.html` produite par `--modular` (ou par « Exporter la structure modulaire (.zip) » du viewer), le dossier contient :

Ces fichiers sont ceux d'une région à coquille propre (`--modular`). Pour plusieurs régions dans un même dossier avec **une seule** coquille, voir « Coquille unique pour plusieurs régions » plus bas.

| Fichier              | Rôle                                                                                   | Relu à chaque F5 |
|----------------------|----------------------------------------------------------------------------------------|------------------|
| `Region.html`        | coquille identique pour toutes les régions, elle déduit ses fichiers de son nom        | non              |
| `Region.glb`         | le modèle                                                                              | non              |
| `Region.config.json` | réglages de **rendu de la page** (voir plus bas)                                       | oui              |
| `Region.zones.json`  | zones, portails, arrivées                                                              | oui              |
| `zones.json`         | zones de secours, communes aux pages du dossier qui n'ont pas leur propre `.zones.json` | oui              |
| `lib/three-0.160.0/` | three.js, Draco, Meshopt, partagés par toutes les pages du dossier                     | non              |

### Coquille unique pour plusieurs régions (`--shared-shell`, v26)

Une seule coquille (par défaut `index.html`) sert toutes les régions d'un même dossier, avec un seul `lib/`. Chaque région n'ajoute que trois fichiers. La région s'ouvre à **`index.html?region=NOM`**, où NOM est le nom des fichiers sans extension (`?region=NOM.html` est accepté : l'extension est retirée).

```
dossier/
  index.html            la coquille, identique pour toutes les régions
  lib/three-0.160.0/    partagé
  Ankh.glb   Ankh.config.json   Ankh.zones.json
  Jungle.glb Jungle.config.json Jungle.zones.json
```

| Besoin | Commande (PowerShell, une seule ligne) |
|---|---|
| Générer une région | `python glb2html.py "Ankh.glb" --settings --shared-shell --register regions.json -o "Ankh.html"` |
| Autre nom de coquille | `--shared-shell monde.html` (adresse `monde.html?region=Ankh`) |
| Changer un réglage | `python glb2html.py --settings "Ankh.glb" --config-only --shared-shell --wave 2 -o "Ankh.html"` |
| Changer les zones seules | `python glb2html.py -o "Ankh.html" --zones-only --zones zones.json` |

Règles :

- `-o` désigne la **région** : son nom sans extension donne NOM. `Ankh.html` n'est pas écrit ; sont écrits `Ankh.glb`, `Ankh.config.json`, `Ankh.zones.json`, plus `index.html` et `lib/three-0.160.0/` **s'ils sont absents**. Une coquille existante n'est jamais écrasée (les autres régions la partagent) : si elle diffère de celle de la version courante, le script avertit ; la supprimer pour la renouveler.
- `--register` écrit l'adresse `index.html?region=NOM` dans `regions.json` (sauf `--region-url` ou fiche du `.reglages.json`). Les portails et la carte ajoutent `#spawn=…` après la query string : `index.html?region=NOM#spawn=default&name=…`. « ● vous êtes ici » reconnaît la région par son salon, puis par l'adresse complète (query string comprise).
- **Sans paramètre `region`**, la coquille se comporte comme avant : elle déduit ses fichiers du nom de la page (`index.html` charge `index.config.json`, `index.glb`, `index.zones.json`). Les pages déjà publiées et leurs coquilles continuent donc de marcher, sans rien changer. Sans paramètre ni fichier correspondant, la page affiche « Erreur : … introuvable (HTTP 404) » avec le nom du fichier cherché.
- **Sécurité.** NOM doit être un seul nom de fichier. Sont refusés, avec un message d'erreur dans la page et **aucune requête réseau** : un nom vide, contenant `/` `\` `:` `?` `#` ou `..` (même encodés dans l'adresse), ou commençant par un point. Sans cela, `?region=https://autre-site/x` ferait charger config, zones et modèle depuis un site étranger (portails piégés, webhooks Home Assistant envoyés ailleurs). Le script refuse de la même façon un `-o` dont le nom serait refusé.
- Viewer : « Exporter la structure modulaire (.zip) » donne la même structure (`index.html`, `NOM.glb`, `NOM.config.json`, `NOM.zones.json`, `lib/`) ; la case « Coquille commune » du récapitulatif pour le script ajoute `--shared-shell` à la place de `--modular`. Le `.zip` écrase `index.html` à la décompression : pour un dossier qui a déjà plusieurs régions, ne copier que les fichiers de NOM si la coquille n'a pas changé.
- Comme tout mode modulaire, la page demande http/https (pas d'ouverture depuis le disque).

### Quel fichier de zones est lu

Dans l'ordre, et on s'arrête au premier qui donne une liste JSON valide :

1. `Region.zones.json`
2. `zones.json` du même dossier, **seulement si** le premier est absent, inaccessible (erreur HTTP) ou n'est pas une liste
3. sinon : aucune zone

Il n'y a **pas de fusion** : dès que `Region.zones.json` est lu, `zones.json` est ignoré. Un `zones.json` posé à côté d'une région qui a déjà son `.zones.json` n'a donc aucun effet.

Les zones marquées **privées** sont retirées à la lecture, dans l'un comme dans l'autre fichier, sauf si `profile` vaut `perso` dans `Region.config.json`.

### Region.config.json : le rendu de la page, pas le viewer

C'est le dictionnaire de réglages que la page lit au démarrage (le même que celui intégré dans une page autonome). Il est **à plat** :

- mer, trou, vagues, ciel, rotation de la région ;
- caméra de départ : `camDir`, `target`, `zoom` ;
- promenade : `walk`, `eyeHeight`, `walkSpeed`, `walkIgnore` ;
- `names`, `panel`, `retina`, `anim`, `foliageCutout` ;
- présence : `presenceUrl`, `room`, `chat`, `chatFade`, `spectate` ;
- carte des mondes : `map` (carte résolue) et `mapUrl` ;
- `profile` (`public` ou `perso`), `version`, `seaSize`.

`zones` y est **toujours vide** (`[]`) et `zonesLive` toujours vide : en modulaire, les zones sont uniquement dans `Region.zones.json`.

Le viewer ne lit jamais ce fichier : il travaille avec son propre fichier de réglages (ci-dessous).

### `.reglages.json` et `.config.json` n'ont pas la même structure

`<nom>.reglages.json` est l'état de travail du viewer (« Enregistrer dans un fichier »). Il est **imbriqué** :

```
{ v, file, saved,
  cfg:     { rotate, hole, holeFade, ..., mapUrl, guide, ignoreViz },
  camera:  { camDir, target, zoom },
  zones:   [ ...toutes les zones, privées comprises ],
  profile, thisReg: { fiche de cette région pour la carte },
  cmd:     { script, glb, dest, mapPage } }
```

| | `<nom>.reglages.json` (viewer) | `<page>.config.json` (page) |
|---|---|---|
| Structure | imbriquée (`cfg`, `camera`, ...) | à plat |
| Caméra | sous-objet `camera` | à la racine (`camDir`, `target`, `zoom`) |
| Zones | toutes, privées comprises | toujours vide |
| Carte | seulement la fiche de cette région (`thisReg`) | carte complète résolue (`map`) |
| Propre à lui | `guide`, `ignoreViz`, `cmd`, `thisReg` | `seaSize`, `version` |
| Écrit par | le viewer | `glb2html.py` |
| Lu par | le viewer, `glb2html.py --settings` | la page exportée |

La conversion ne va que dans un sens :

```
<nom>.reglages.json  ->  glb2html.py --settings  ->  <page>.config.json + <page>.zones.json
```

Un `.config.json` ne peut pas être donné à `--settings` (le script cherche la clé `cfg` et refuse le fichier), ni rechargé dans le viewer (« fichier de réglages non reconnu »). Pour garder ses réglages, il faut donc conserver le `.reglages.json` : le `.config.json` n'en est qu'un produit dérivé.

### Quel fichier modifier, et ce qui l'écrase

| Je veux changer...                    | Je modifie / je lance                                                    | Ce qui peut l'écraser ensuite                                              |
|---------------------------------------|--------------------------------------------------------------------------|----------------------------------------------------------------------------|
| un réglage de rendu (vagues, ciel...) | `--config-only` (voir ci-dessous), ou `Region.config.json` à la main     | tout nouveau `--modular` ou `--config-only` réécrit `Region.config.json`   |
| une zone                              | `Region.zones.json` à la main, ou **Exporter zones (.json)** (§ 12)      | `--modular` avec `--zones` ou `--settings` ; `--config-only` avec `--zones` |
| l'état de travail du viewer           | **Enregistrer dans un fichier**                                          | rien (c'est la source)                                                     |

Sans `--zones` ni `--settings`, un `Region.zones.json` déjà présent (modifié à la main, par exemple) n'est pas écrasé. Dès qu'une source de zones est donnée, il est réécrit.

Changer un réglage sans toucher au `.glb`, à la coquille ni aux zones :

```
python glb2html.py --settings "Region-final.glb" --config-only --wave 2 -o "Region.html"
```

Les options de la ligne de commande l'emportent sur le `.reglages.json`. Les visiteurs voient le changement à leur prochain rechargement.

## 17. Découper un GLB énorme en tuiles (`tools/glb2tiles.py`, v28 ; `--exclure` et pause en v29)

`glb2tiles.py` découpe un GLB trop lourd en **tuiles autonomes** : chacune est un GLB valide (ouvrable seul dans `glb-viewer.html`), avec ses propres nœuds, meshes, matériaux et images, aux coordonnées d'origine (aucun recentrage). Cette version **écrit seulement les tuiles et leur liste** ; le chargement des tuiles par la page n'existe pas encore (lot suivant). Python standard seulement. Le GLB d'entrée n'est jamais chargé en entier : l'en-tête JSON est lu, puis les indices, positions et images par morceaux.

`glb-stats.py` doit rester **à côté** de `glb2tiles.py` (fonctions de mesure communes) ; `python build.py` met les deux dans `dist/`.

### Les commandes (PowerShell, une seule ligne)

| Pour | Commande |
|---|---|
| Voir la version | `python glb2tiles.py --version` |
| Mesurer et obtenir une recommandation, sans rien écrire | `python glb2tiles.py "P:\...\Region.glb" --analyse` |
| Découper (recommandation « découper ») | `python glb2tiles.py "P:\...\Region.glb"` |
| Découper même si la recommandation est « pas de découpage » | `python glb2tiles.py "P:\...\Region.glb" --forcer` |
| Écrire ailleurs qu'à côté du GLB | `python glb2tiles.py "P:\...\Region.glb" --sortie "P:\...\tuiles"` |
| Écarter les « boîtes de livraison » d'un fournisseur | `python glb2tiles.py "P:\...\Region.glb" --analyse --exclure "Freebies 20"` puis la même commande sans `--analyse` |

Commencer par `--analyse` : elle donne les mesures de `glb-stats.py`, les 10 meshes les plus lourds (octets compactés, étendue en mètres), les 10 instances les plus éloignées du centre médian (valeurs aberrantes), le nombre de tuiles prévu avec les paramètres choisis, le facteur de duplication prévu, le nombre d'objets racine gardés entiers ou répartis, et une phrase de recommandation : « pas de découpage nécessaire » ou « découper : budget N Mo, T tuiles, duplication F ». Un GLB léger répond « pas de découpage nécessaire » et rien n'est écrit (même sans `--analyse`, sauf avec `--forcer`).

### Les paramètres

| Option | Défaut | Sens |
|---|---|---|
| `--budget` | 32 | Mo par tuile (poids autonome : primitives distinctes compactées + images distinctes) |
| `--budget-tri` | 1500000 | triangles par tuile (le poids en Mo ne suffit pas : un bloc peut avoir 5 M de triangles pour 70 Mo) |
| `--min` | 16 | côté minimal d'une cellule, en m : on ne subdivise plus en dessous |
| `--entier-poids` | 16 | Mo : un objet racine plus léger que cela peut rester entier |
| `--entier-etendue` | 256 | m : …et plus petit que cela (les deux conditions ensemble ; l'étendue seule ne décide pas) |
| `--seuil`, `--seuil-tri` | 150, 3000000 | sous ces deux valeurs : « pas de découpage nécessaire » |
| `--aberrant` | 1000 | m : une instance plus loin que cela du centre médian, ou plus grande, est signalée |
| `--bloc` | 256 | côté des blocs de la partie `glb-stats` de `--analyse` |
| `--sortie` | à côté du GLB | dossier de sortie |
| `--forcer` | | découper même sous les seuils |
| `--exclure REGEX` | | retire du découpage les objets racine dont le nom correspond (insensible à la casse, répétable ; voir ci-dessous) |
| `--exclure-max-tri` | 24 | triangles au plus dans l'objet racine, tous meshes compris, pour être exclu |
| `--exclure-max-meshes` | 1 | meshes au plus dans l'objet racine pour être exclu |
| `--nopause` | | ne pas attendre Entrée à la fin (la pause est aussi supprimée quand il n'y a pas de console : script, tâche planifiée) |

### Exclure des objets (`--exclure`, v29)

Certains catalogues posent à côté de chaque bâtiment une « boîte de livraison » (cube texturé de 12 triangles, un seul mesh) dont le nom se termine par celui du fournisseur, par exemple « City Stores - Box - RAKis Freebies 2019 ». `--exclure "Freebies"` les retire, **à condition** que l'objet racine ait aussi au plus `--exclure-max-tri` triangles (tous meshes compris) **et** au plus `--exclure-max-meshes` meshes. Sans ces garde-fous le nom du fournisseur retirerait aussi de vrais bâtiments (« Jewel Box House V17 with Stairs - RAKis Freebies 2 » : 143 meshes, conservé). La décision ne dépend **jamais de l'étendue** : la boîte englobante d'un petit mesh qui partage un tampon de sommets avec d'autres est gonflée, jusqu'à plusieurs dizaines de mètres pour un cube de 12 triangles.

- Plusieurs `--exclure` s'additionnent. Une expression invalide donne un message clair (`Expression régulière invalide pour --exclure`) et rien n'est lu.
- Les nœuds retirés sont l'objet racine et tous ses descendants ; aucun autre objet ne change. Les exclus n'entrent ni dans les tuiles ni dans les calculs de poids, de triangles et de budget (la recommandation « pas de découpage » retire aussi leurs octets de la taille du GLB). Le GLB d'origine n'est pas modifié ; la partie `glb-stats` de `--analyse` décrit le fichier d'origine.
- `--analyse` et le rapport final donnent : le nombre d'objets exclus, les triangles retirés, les octets gagnés (géométrie et images qu'aucun objet conservé n'utilise), le nombre d'objets au nom correspondant mais conservés par les garde-fous, et les 20 noms les plus fréquents avec leur nombre. `X.tiles.json` reçoit une clé `excluded` (motifs, garde-fous, `count`, `triangles`, `bytesSaved`, `names`) seulement quand `--exclure` est utilisé.

### Comment le découpage se décide

- Quadtree adaptatif sur le plan X,Z (Y est la hauteur), uniquement sur les cellules non vides. Une cellule est subdivisée tant que son poids autonome dépasse `--budget` **ou** ses triangles dépassent `--budget-tri`, et que son côté dépasse `--min`.
- Un **objet racine** (nœud de premier niveau de la scène) reste **entier**, dans la cellule du centre de sa boîte, si son poids autonome ≤ `--entier-poids` **et** son étendue ≤ `--entier-etendue`. Sinon il est **réparti instance par instance** : chaque instance va dans la cellule de son propre centre, et les nœuds parents sont recopiés (sans mesh) avec leurs transformations d'origine.
- Un objet qui porte un **skin** n'est jamais réparti : son objet racine entier va dans la tuile du centre de sa boîte, avec le skin, les nœuds de joints (même s'ils sont hors de l'objet) et les `inverseBindMatrices`.
- Les meshes partagés entre tuiles sont **dupliqués** dans chaque tuile qui les utilise (tuiles autonomes). La duplication réelle est écrite dans le rapport.
- Les sommets de chaque primitive sont **compactés** : seuls les sommets indexés sont gardés et renumérotés, avec le plus petit type d'indices (16 bits si possible). Les triangles sont identiques.
- Un mesh **unique** plus lourd que le budget (terrain, mer) ne peut pas être réparti à ce stade : sa cellule reste telle quelle, hors budget, avec un avertissement (nom, étendue, Mo).
- Un GLB compressé (Draco, meshopt) est refusé avec un message clair. Accessors `sparse` : refusés avec un message.

### Fichiers produits

`X.tiles/T_<niveau>_<i>_<j>.glb` (niveau et position de la cellule dans le quadtree) et `X.tiles.json` (UTF-8 sans BOM), à côté du GLB `X.glb` :

```
{
 "version": 1,                      version du format
 "generator": "glb2tiles v28 (21/10/2026)",
 "source": "X.glb",
 "extent": {"min": [x,y,z], "max": [x,y,z]},     étendue globale du contenu
 "params": {"budgetMo": 32, "budgetTriangles": 1500000, "minCell": 16, "wholeWeightMo": 16, "wholeExtent": 256,
            "thresholdMo": 150, "thresholdTriangles": 3000000, "outlier": 1000},
 "warnings": ["..."],               tuiles hors budget, valeurs aberrantes, extensions non recopiées
 "roots": {"whole": 1700, "split": 125},         objets racine gardés entiers / répartis
 "duplication": 1.8,                somme des octets de géométrie des tuiles / géométrie unique du GLB
 "tiles": [{"file": "X.tiles/T_3_2_5.glb", "level": 3, "i": 2, "j": 5,
            "min": [x,y,z], "max": [x,y,z],   boîte du contenu réel de la tuile (un objet qui déborde de sa cellule reste couvert)
            "instances": 812, "triangles": 410233,
            "bytes": 21345678, "geometryBytes": 9001234, "imageBytes": 12000000}]
}
```

Relancer écrase les `T_*_*_*.glb` du dossier `X.tiles/` (les autres fichiers ne sont pas touchés).

### Lire le journal (`glb2tiles.log`, à côté du script)

Première ligne : `[glb2tiles] v29 (22/10/2026)`. L'avancement est écrit toutes les 5 % ou 10 s. Le rapport final donne : nombre de tuiles, médiane / 90 % / maximum du poids et des triangles, duplication réelle, nombre de racines entières et réparties, avertissements, temps total. `python glb2tiles.py --version` affiche la version sans journal ni pause.

Dans `--analyse`, la ligne « Lecture » indique les octets lus. Les positions ne sont lues que pour les primitives qui n'utilisent qu'une partie d'un tampon de sommets partagé (la boîte de l'accessor serait trop grande) ; les autres boîtes viennent de l'en-tête.

### Si quelque chose ne va pas

| Symptôme | Cause probable | Que faire |
|---|---|---|
| « GLB compressé » | le GLB utilise Draco ou meshopt | décompresser le GLB d'abord (hors de ce lot) |
| « glb-stats.py introuvable » | le script est seul dans son dossier | copier `glb-stats.py` à côté |
| « Tuile … hors budget » | un mesh unique (terrain, mer) dépasse le budget, ou la cellule minimale est atteinte | normal à ce stade : voir la feuille de route (découpage par triangles) |
| Beaucoup de tuiles pour un petit GLB | `--budget` trop petit ou duplication forte | relancer `--analyse` avec d'autres valeurs |
| Instance à 3 000 m signalée | un prim géant ou un objet égaré | l'outil la garde ; la corriger dans le modèle si c'est une erreur |

Test : `python tests/glb2tiles.py` (GLB synthétiques, sans navigateur ni réseau).

