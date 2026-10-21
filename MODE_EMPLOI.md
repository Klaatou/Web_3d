# Mode d'emploi : zones, portails et points d'arrivée (v25)

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
| Page de destination | l'autre page : `autre-region.html` si elle est dans le même dossier, sinon son adresse complète `https://…/autre-region.html` |
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
| `--reencode` | **à éviter** : réencode les textures avant convoar ; sur Jungle_Isle il faisait manquer environ 150 textures sur 353 (textures grises). À n'utiliser que si convoar affiche beaucoup d'erreurs « unhandled number of components » et que les textures restent bonnes |
| `--nopause` | ne pas attendre « Entrée » à la fin |

### Ce que le script corrige

- **Animaux riggés (animesh).** La géométrie que convoar écrit pour ces meshes est inutilisable (hippopotames géants, éléphants minuscules ou envolés, formes partagées entre animaux). Le script la reconstruit depuis le fichier `.llmesh` de l'OAR : positions, normales, UV, triangles, puis `bind_shape_matrix` ; l'échelle du prim est ignorée. Les morceaux d'un même animal restent ensemble. L'animal est centré sur la position de la racine de l'objet et ses pieds sont posés sous la boîte racine (à l'altitude de la racine si elle est elle-même riggée). Les textures viennent de convoar (face n du mesh = matériau n). Aucune règle ne dépend du nom d'un animal. Un animal dont la taille calculée sort de 0,1 à 12 m reste tel que convoar l'a produit (le journal le dit).
- **Prims invisibles.** Sont retirés : les prims dont toutes les faces sont à alpha 0 ou portent une texture invisible standard, les nœuds dont tous les matériaux sont transparents, et la boîte racine d'un animesh (prim simple, racine d'un objet dont tous les autres morceaux sont des meshes riggés). Les enfants d'une racine retirée restent.
- **Textures.** Le script compare les images annoncées par le `.gltf` aux fichiers présents ; s'il en manque, il relance convoar (2 essais de plus au maximum) en gardant les images déjà écrites.
- **Positions des régions plus grandes que 256 m** et objets hors région : traitement inchangé.

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

Test du script : `python tests/oar2glb.py` (OAR synthétique et faux convoar, sans réseau).

## 16. Fichiers JSON d'une région modulaire

Pour une page `Region.html` produite par `--modular` (ou par « Exporter la structure modulaire (.zip) » du viewer), le dossier contient :

| Fichier              | Rôle                                                                                   | Relu à chaque F5 |
|----------------------|----------------------------------------------------------------------------------------|------------------|
| `Region.html`        | coquille identique pour toutes les régions, elle déduit ses fichiers de son nom        | non              |
| `Region.glb`         | le modèle                                                                              | non              |
| `Region.config.json` | réglages de **rendu de la page** (voir plus bas)                                       | oui              |
| `Region.zones.json`  | zones, portails, arrivées                                                              | oui              |
| `zones.json`         | zones de secours, communes aux pages du dossier qui n'ont pas leur propre `.zones.json` | oui              |
| `lib/three-0.160.0/` | three.js, Draco, Meshopt, partagés par toutes les pages du dossier                     | non              |

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
