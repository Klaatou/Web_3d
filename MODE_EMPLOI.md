# Mode d'emploi : zones, portails et points d'arrivée (v30)

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

`python oar2glb.py "J:\...\X.oar"` lance convoar, répare le résultat et écrit `X.glb` à côté de l'OAR.

**Animesh (meshes riggés).** Dans l'OAR, un animal riggé a souvent une échelle de prim sans rapport avec sa vraie taille (hippopotame géant, éléphant minuscule). Le script lit le bloc skin du mesh (`assets/*_mesh.llmesh`), ignore l'échelle du prim (convoar en applique une que l'OAR ne donne pas : le script mesure l'étendue des sommets et les remet dans le domaine du mesh), applique `bind_shape_matrix`, centre l'animal à l'horizontale sur la position de la racine de l'objet et pose ses pieds sous la boîte racine (le terrain de l'OAR n'est pas utilisé : les animaux sont souvent sur des rochers). Les morceaux d'un même animal (chacun avec sa `bind_shape_matrix`) sont déplacés ensemble. Le journal indique la taille obtenue de chaque animal. Si cette taille sort de 0,1 à 12 m, l'animal est laissé tel que convoar l'a produit (garde-fou) et le journal le dit.

**Prims invisibles.** Un prim dont toutes les faces sont à alpha 0, ou qui porte la texture invisible standard, n'est plus exporté (boîtes translucides autour des animaux). Si c'est la racine d'un linkset, les enfants restent. La boîte racine d'un animesh (prim simple, racine d'un objet dont toutes les autres parties sont des meshes riggés) est retirée aussi, même si l'OAR ne la donne pas transparente. `--keep-invisible` les garde. Le journal se termine par : « N mesh(es) riggé(s) remis à l'échelle, M prim(s) invisible(s) retiré(s) ».

**Valider avant de croire : `--diag`.** `python oar2glb.py "J:\...\X.oar" --diag` ne modifie rien et ne lance pas convoar. Il lit le `.gltf` du dossier `X-GLTF` (conservé avec `--keep`), sinon le `X.glb` voisin, ou celui donné par `--glb` et affiche une ligne par partie de l'OAR : nom, UUID, riggé oui/non, échelle du prim, échelle de `bind_shape_matrix`, transparent oui/non, nœud GLB trouvé ou non et par quelle méthode (UUID du prim, UUID du mesh, nom + position). Les lignes « nœud introuvable » sur un animal ou un prim transparent signifient que le correctif ne s'appliquera pas à lui : envoyer le journal (`oar2glb.diag.log`, la conversion écrit `oar2glb.log`) pour ajuster la correspondance. Le GLB final contient les nœuds déjà corrigés : pour diagnostiquer, garder le `-GLTF` produit avec `--keep` et passer son `.gltf` à `--glb`.

Si des textures deviennent grises, relancer la conversion SANS `--reencode` (sur Jungle_Isle, avec `--reencode`, environ 150 images sur 353 manquaient) et comparer le nombre de textures absentes et chercher la ligne `[GLB] N texture(s) absente(s)`. Si convoar n'écrit pas toutes les images qu'il annonce, le script le relance (2 essais de plus au maximum) et garde les images déjà écrites.

**Retrouver les animaux : `--reperes`.** Ajoute un mât rouge de 15 m à chaque animal riggé posé ; le nom du nœud donne l'animal et sa taille. À retirer une fois les animaux vérifiés (relancer sans l'option).

Test : `python tests/oar2glb.py` (OAR synthétique et faux convoar, sans réseau).
