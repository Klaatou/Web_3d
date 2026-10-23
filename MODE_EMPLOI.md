# Mode d'emploi : zones, portails et points d'arrivée (v36)

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
| **F** (v36) | **entre en promenade et en sort**, en vue globale comme en promenade (comme **P**) ; le vol se bascule avec **Début** (en v35, F basculait le vol). **À la sortie (v31)**, le petit cercle d'atterrissage et la cible de la vue globale se posent **au sol, sous le dernier endroit où se trouvait l'avatar** ; la caméra revient à la **même distance et dans la même direction** de cette cible qu'avant l'entrée en promenade (elle ne revient plus à l'endroit exact d'où tu étais parti). En mode tuiles, les tuiles autour de l'avatar restent donc chargées. |
| **P** (v35) | **entrer dans la promenade / en sortir** (le bouton « Promenade (P) » reste en vue globale ; il n'y a plus de bouton « Quitter la promenade »). Dans le **viewer**, P pose une zone en promenade : on en sort avec **F**, **Maj+P** ou le bouton |
| **E** (v36) | **déclenche la zone proche** (déclenchement « au clic » ou « les deux », comme avant la v35 ; un portail « en marchant dedans » part à l'entrée de son rayon, § 8). Le nom de la zone proche s'affiche en bas : « clic ou E : … ». **E ne fait rien d'autre** (il ne saute plus et ne monte plus) |
| **Page Haut** (v35) | **appui bref au sol = saut** (comme Espace) ; **maintenu plus de 0,4 s au sol = décoller** ; en vol, maintenu = monter |
| **Espace** (v36) | au sol : saut ; **en vol, maintenu : monter** |
| **T** (v36) | affiche ou masque les **repères de portail** (petits cônes, § 21.4) ; le choix est mémorisé |
| **Début** (v33) | décoller ou atterrir (bascule ; v36 : F ne bascule plus le vol). En vol : **Page Haut** ou **Espace** maintenu monte, **C** / **Page Bas** descend, pas de gravité, les murs restent solides, jamais sous le sol. Retirable avec `--no-fly` (§ 18.4) |
| **M** (v35) | **en promenade : bascule vue subjective / troisième personne** ; hors promenade : ouvre la carte des mondes (comme avant). **Ctrl+M ouvre la carte des mondes partout**. **v36 : la touche est reconnue par la lettre imprimée « m »**, pas par sa place : sur un clavier AZERTY c'est la vraie touche M (avant, c'était la touche « , ») |
| **Fin**, **Alt + clic** (v35) | remettre la caméra **derrière l'avatar** (troisième personne). **Alt + glisser** orbite la caméra (à la troisième personne la souris orbite déjà ; en vue subjective, Alt + glisser regarde autour comme la souris) |
| **molette** (v35) | en promenade, la page ne défile pas. **Troisième personne** : règle la distance de la caméra (1 à 30 m, 4 m par défaut, mémorisée) ; **caméra libre** : avance / recule la caméra le long du regard ; vue subjective : rien (§ 20.9) |
| **double appui** sur W, S, ↑ ou ↓ (v35) | **course** tant que la touche reste enfoncée (deux appuis à moins de 300 ms) ; **Maj** reste une course. Pas de course permanente (Ctrl+R recharge la page) |
| **V** (v33) | changer de vue : subjective → troisième personne → caméra libre → subjective. La vue courante est écrite en texte dans le bloc d'état (« Vue : … », v34) |
| **R** (v33) | **retour à l'arrivée** : en promenade, téléporte à l'arrivée `default` (à défaut, à la cible de départ) en attendant la tuile ; en vue globale, recadre la cible et la caméra sur ce point. Le bouton « Retour à l'arrivée (R) » fait la même chose |
| **Entrée** (v33) | ouvrir la saisie du chat ; **Entrée envoie et garde la saisie ouverte**, **Échap** la ferme. Les flèches continuent à déplacer l'avatar (§ 18.5) |
| **Page Haut** / **Page Bas** (v34) | en vol, monter / descendre (en plus de **Espace** maintenu / **C**, v36) ; la page ne défile pas. **Descendre jusqu'au sol pose l'avatar** : le vol s'arrête tout seul. Bouton « Voler / Atterrir » dans la barre du bas pour qui n'a pas de touche Début (§ 19.3) |
| **Échap** (v34) | libère la souris en promenade. La souris reste alors **libre** (un clic ou un double-clic n'aspire plus le pointeur) jusqu'à **G** ou au bouton « Capturer la souris » (§ 19.4) |
| **G** (v34) | recapturer la souris après Échap |
| **I** (v34) | la fenêtre **Informations / État** (v36 : ancien « bloc d'état » : vue, mode, souris, clavier, position, tuiles) : masquée → déployée ; réduite → déployée ; déployée → masquée. **H** fait de même pour l'aide seule (§ 19.1, § 21.3) |

Les portails ne fonctionnent qu'en promenade.

### Clic et double-clic (vue globale du viewer)

| Geste | Effet |
|---|---|
| **clic simple** sur le modèle | affiche, dans le bloc « picked » et la barre d'état, le **nom de l'élément** et les **coordonnées du point touché** (x, y, z, 2 décimales). Rien ne bouge : ni la cible, ni le cercle d'atterrissage. |
| **double-clic** sur le modèle | choisit la **cible** de la vue et le **point d'atterrissage** (comme dans la page exportée). En mode tuiles (§ 17 bis), le double-clic fonctionne aussi sur la **vue d'ensemble** : la cible se place sur le point lointain et les tuiles s'y chargent. |

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

Aucun panneau de texte permanent : le nom ne s'affiche qu'au survol, ou quand on est à portée (« clic : … » en bas de l'écran).

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

**Arrivée `default` et ouverture sans lien (v33)** : si la région a une arrivée `default`, la page s'ouvre **cadrée sur elle** (la cible de la caméra devient sa position) et **F démarre à son point, avec son orientation** (tant que la cible n'a pas été déplacée, par exemple au double-clic). Une cible donnée explicitement sur la ligne de commande (`--target`) garde la priorité pour le cadrage : voir la règle exacte au § 18.2.

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
| au clic | il faut cliquer dessus (v35 : la touche E ne déclenche plus les zones) |
| les deux | l'un ou l'autre |

Un portail « en marchant dedans » sur lequel on arrive ne se déclenche pas tout de suite : il faut en sortir puis y rentrer. Deux portails qui se renvoient l'un vers l'autre ne font donc pas de ping-pong.

**Forme** :

| Choix | Réglage de taille |
|---|---|
| cercle au sol | Rayon (m) |
| panneau | Largeur, Hauteur, et Portée d'approche pour l'invite « clic » (m) |

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
| Rien ne se passe en entrant dans un portail | pas en promenade | appuie sur P (ou F en vue globale) |
| | déclenchement réglé « au clic » | clique sur le portail (v35 : E ne le déclenche plus), ou passe en « en marchant dedans » |
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
| Mettre à jour une région (v34) | `python glb2html.py --maj -o "Ankh.html" --shared-shell --sea-y 12` : applique **seulement** les options données, garde le reste de la config et les zones (§ 19.6) |

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

## 17. Découper un GLB énorme en tuiles (`tools/glb2tiles.py`, v28 ; `--exclure` et pause en v29 ; images invalides et vue d'ensemble en v31)

`glb2tiles.py` découpe un GLB trop lourd en **tuiles autonomes** : chacune est un GLB valide (ouvrable seul dans `glb-viewer.html`), avec ses propres nœuds, meshes, matériaux et images, aux coordonnées d'origine (aucun recentrage). Cet outil **écrit les tuiles, leur liste et (v31) une vue d'ensemble légère de toute la région** ; c'est la coquille qui les charge autour de l'avatar (v30, voir § 17 bis). Python standard seulement. Le GLB d'entrée n'est jamais chargé en entier : l'en-tête JSON est lu, puis les indices, positions et images par morceaux.

`glb-stats.py` doit rester **à côté** de `glb2tiles.py` (fonctions de mesure communes) ; `python build.py` met les deux dans `dist/`.

### Les commandes (PowerShell, une seule ligne)

| Pour | Commande |
|---|---|
| Voir la version | `python glb2tiles.py --version` |
| Mesurer et obtenir une recommandation, sans rien écrire | `python glb2tiles.py "P:\...\Region.glb" --analyse` |
| Découper (recommandation « découper ») | `python glb2tiles.py "P:\...\Region.glb"` |
| Découper même si la recommandation est « pas de découpage » | `python glb2tiles.py "P:\...\Region.glb" --forcer` |
| Écrire ailleurs qu'à côté du GLB | `python glb2tiles.py "P:\...\Region.glb" --sortie "P:\...\tuiles"` |
| Découper sans la vue d'ensemble | `python glb2tiles.py "P:\...\Region.glb" --sans-vue-ensemble` |
| Refaire **seulement** la vue d'ensemble (tuiles intactes) | `python glb2tiles.py "P:\...\Region.glb" --vue-ensemble-seule` avec **les mêmes options de découpage** (`--sortie`, `--budget`, `--exclure`…) que la première fois |
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
| `--sans-references` | | ne pas écrire `extras.ref` / `extras.box` dans les nœuds des tuiles (format de la v31 : zones liées à un objet impossibles en mode tuiles) |
| `--sans-vue-ensemble` | | ne pas écrire `X.overview.glb` |
| `--vue-ensemble-seule` | | n'écrire que `X.overview.glb` et sa mention dans `X.tiles.json` ; le découpage recalculé doit retrouver exactement les tuiles de `X.tiles.json` (sinon : erreur « ne correspond pas », utiliser les mêmes options) |
| `--ov-budget`, `--ov-budget-tri` | 25, 1500000 | Mo et triangles de toute la vue d'ensemble |
| `--ov-seuil` | 3 | m : les objets dont la plus grande dimension est plus petite sont omis (le budget peut relever ce seuil) |
| `--ov-seuil-max` | 24 | m : si le budget oblige à omettre des objets plus grands que cela, la résolution baisse |
| `--ov-resolution` | 10 | cellules sur la plus grande dimension d'une primitive pour le regroupement de sommets (plus grand = plus fin et plus lourd) |
| `--ov-terrain-pas` | 4 | m : pas du réseau du terrain dans la vue d'ensemble |
| `--nopause` | | ne pas attendre Entrée à la fin (la pause est aussi supprimée quand il n'y a pas de console : script, tâche planifiée) |

### Exclure des objets (`--exclure`, v29)

Certains catalogues posent à côté de chaque bâtiment une « boîte de livraison » (cube texturé de 12 triangles, un seul mesh) dont le nom se termine par celui du fournisseur, par exemple « City Stores - Box - RAKis Freebies 2019 ». `--exclure "Freebies"` les retire, **à condition** que l'objet racine ait aussi au plus `--exclure-max-tri` triangles (tous meshes compris) **et** au plus `--exclure-max-meshes` meshes. Sans ces garde-fous le nom du fournisseur retirerait aussi de vrais bâtiments (« Jewel Box House V17 with Stairs - RAKis Freebies 2 » : 143 meshes, conservé). La décision ne dépend **jamais de l'étendue** : la boîte englobante d'un petit mesh qui partage un tampon de sommets avec d'autres est gonflée, jusqu'à plusieurs dizaines de mètres pour un cube de 12 triangles.

- Plusieurs `--exclure` s'additionnent. Une expression invalide donne un message clair (`Expression régulière invalide pour --exclure`) et rien n'est lu.
- Les nœuds retirés sont l'objet racine et tous ses descendants ; aucun autre objet ne change. Les exclus n'entrent ni dans les tuiles ni dans les calculs de poids, de triangles et de budget (la recommandation « pas de découpage » retire aussi leurs octets de la taille du GLB). Le GLB d'origine n'est pas modifié ; la partie `glb-stats` de `--analyse` décrit le fichier d'origine.
- `--analyse` et le rapport final donnent : le nombre d'objets exclus, les triangles retirés, les octets gagnés (géométrie et images qu'aucun objet conservé n'utilise ; **0** quand tous les exclus partagent leurs primitives ou leurs images avec des objets conservés, par exemple un cube commun : le rapport le dit alors, et chiffre les octets partagés non gagnés), le nombre d'objets au nom correspondant mais conservés par les garde-fous, et les 20 noms les plus fréquents avec leur nombre. `X.tiles.json` reçoit une clé `excluded` (motifs, garde-fous, `count`, `triangles`, `bytesSaved`, `bytesShared`, `names`) seulement quand `--exclure` est utilisé.

### Références d'objets (v32) : lier une zone à un objet en mode tuiles

Chaque nœud copié dans une tuile reçoit dans ses `extras` : **`ref`**, sa référence stable dans le modèle d'origine, et **`box`**, la boîte (monde, 6 nombres en m) de **l'objet entier**, même quand il est réparti sur plusieurs tuiles (chaque morceau porte la même boîte). `X.tiles.json` porte `"nodeRefs": 1`.

- **Règle de la référence** (celle de `nom#index` du mode GLB unique, calculée sur le GLB entier) : le **nom** du nœud (à défaut le nom de son mesh) s'il est unique dans tout le modèle ; sinon **`nom#index`**, index = rang du nœud parmi les nœuds de ce nom, dans l'ordre de parcours (pré-ordre, enfants dans l'ordre du fichier). Les objets retirés par `--exclure` comptent dans les rangs (une référence ne change pas quand on exclut autre chose). Un nœud sans nom n'a pas de référence ; une référence de plus de 200 caractères n'est pas écrite.
- Ces références sont celles des **noms du GLB**, pas celles que verrait le viewer en ouvrant le même GLB entier (le chargeur de three.js renomme les doublons) : une zone liée écrite en mode tuiles s'utilise en mode tuiles.
- **Coût mesuré** (GLB synthétique de 40 000 nœuds) : +0,5 s sur 8 s, +3 Mo sur 230 Mo de tuiles.
- Des tuiles écrites **avant la v32** n'ont pas ces extras : les zones liées y restent ignorées. `glb2tiles.py --analyse` (et `--vue-ensemble-seule`) le signalent quand `X.tiles.json` existe déjà sans `nodeRefs` ; `glb2html.py --tiles` aussi, s'il y a des zones liées. Il faut **refaire le découpage** (sans `--vue-ensemble-seule`).

### Images vides ou invalides (v31)

Une image embarquée **de 0 octet**, d'un **autre format** que PNG, JPEG ou WebP, ou **tronquée** fait échouer le chargement de la tuile dans le navigateur (« THREE.GLTFLoader: Couldn't load texture ») : mesuré dans Chromium, `createImageBitmap` échoue aussi sur un PNG, un JPEG ou un WebP coupé, pas seulement sur une image vide. Sur la région « Free House Gallery 4X4 », 778 images sur 19 799 étaient dans ce cas (toutes avec un `bufferView` de `byteLength` 0).

- À l'écriture, chaque image de ce genre est remplacée par **un PNG gris de 4 x 4 pixels** (gris 128, celui des textures remplacées par `oar2glb.py`), **écrit une seule fois par tuile** et partagé par toutes les références de cette tuile (nom `image-remplacee`). Les matériaux, les textures et les coordonnées de texture ne changent pas.
- Vérification sans décoder : PNG = blocs chaînés jusqu'à `IEND` ; JPEG = marqueur de fin `FFD9` en dernier (aux zéros et espaces de bourrage près) ; WebP = taille RIFF contenue dans le fichier. Seuls l'en-tête, la fin et les en-têtes de blocs sont lus (jamais l'image entière). Un fichier qui serait décodé par Chromium malgré une fin inhabituelle serait remplacé à tort : le nombre rapporté permet de s'en apercevoir.
- `--analyse` et le rapport final donnent « Images vides ou invalides remplacées… : N distincte(s), M occurrence(s) » (une occurrence = une image écrite dans une tuile). `X.tiles.json` reçoit `"replacedImages": {"distinct": N, "occurrences": M, "grey": 128}` et chaque tuile son propre nombre.

### Vue d'ensemble (`X.overview.glb`, v31)

But : en vue globale, voir **toute** la région ; en promenade, voir **au loin** au-delà des tuiles chargées. Les tuiles détaillées restent la seule source des collisions et du sol.

- **Écrite avec les tuiles** (ou seule avec `--vue-ensemble-seule`), à côté de `X.tiles.json`, et référencée dans `X.tiles.json` (clé `overview` : `file`, `bytes`, `triangles`, `terrainTriangles`, `objects`, `candidates`, `omitted`, `effectiveMinExtent`, `effectiveTerrainStep`, `resolution`, `seconds`, `colors`, `params`).
- **Un nœud par fichier de tuile**, nommé comme la tuile (`X.tiles/T_3_2_5.glb`, et `extras.tile`) : la page masque la cellule dès que la tuile détaillée est **affichée** et la réaffiche quand la tuile est déchargée ou en échec. Les objets d'une cellule sont exactement ceux de la tuile : pas de double affichage, pas de trou pendant le chargement.
- **Aucune image.** Un seul matériau ; les couleurs sont des **couleurs de sommets**. Chaque matériau devient une couleur unie : la **couleur moyenne de sa texture** si Pillow est installé (moyenne en espace linéaire, pondérée par l'opacité), sinon sa **couleur de base**. Les couleurs de sommets du terrain sont conservées. Sans normales : la page affiche la vue d'ensemble en ombrage plat. Les primitives translucides (`alphaMode` BLEND : verre, effets) et les objets à squelette sont omis.
- **Chaque primitive UNIQUE est simplifiée une seule fois**, puis recopiée avec la matrice de chacune de ses instances (jamais simplifiée par instance). Méthode : regroupement de sommets sur une grille de côté (plus grande dimension de la primitive) / `--ov-resolution` ; un sommet par cellule (moyenne), triangles dégénérés et doublons retirés. Python standard seulement ; Pillow est facultatif (couleurs moyennes).
- **Terrain simplifié à part.** Les pièces marquées `extras.terrain` (patches d'`oar2glb.py`) sont rééchantillonnées sur un **réseau régulier commun** de pas `--ov-terrain-pas` : hauteur et couleur interpolées dans les triangles d'origine, une case appartient à une seule pièce (donc à une seule tuile). Un point du réseau sur un bord commun reçoit la même hauteur des deux côtés : **aucune fente entre les patches** (testé). Le terrain prend au plus la moitié des budgets ; sinon son pas grossit (× 1,5) jusqu'à ce qu'il tienne (dit dans le journal).
- **Objets omis.** Ceux dont la plus grande dimension est sous `--ov-seuil` (3 m par défaut : à 600 m, distance à laquelle la vue d'ensemble fait l'essentiel de l'image, 3 m couvrent environ 8 pixels sur un écran de 1 080 pixels de haut avec le champ de vision de 38 degrés ; à 210 m, limite du rayon de chargement, 22 pixels). Ce choix vient d'un calcul de taille à l'écran, **pas d'une mesure sur ta région** : `--analyse` imprime le nombre d'instances et de triangles au-dessus de 1, 2, 3, 4, 8, 16, 32 et 64 m pour décider sur tes données. Si le budget est atteint, les **plus grands objets sont gardés d'abord** et le seuil effectif monte (`effectiveMinExtent`) ; au-delà de `--ov-seuil-max` la résolution baisse et le calcul est refait.
- **Budgets** : 25 Mo et 1 500 000 triangles pour toute la région (`--ov-budget`, `--ov-budget-tri`). Le rapport donne le poids, les triangles (dont le terrain), les objets gardés sur candidats, les objets omis (trop petits / par le budget / à squelette), les primitives translucides omises, les couleurs (moyennes de texture, illisibles, Pillow absent) et le temps.
- **Le GLB n'est jamais chargé en entier** (même lecture par morceaux de 4 Mo au plus que pour les tuiles), avec une progression (« [vue d'ensemble : primitives] … ») ; les pièces de terrain sont lues une à une.
- **Durée.** Débit mesuré sur des GLB synthétiques de taille croissante (0,5 ; 2 ; 8 ; 24 millions de triangles uniques) : environ 1,8 million de triangles uniques par seconde, linéaire (0,3 ; 1,2 ; 4,5 ; 13 s), soit 14 à 680 Mo de GLB pour 25 à 164 Mo de mémoire ; 20 000 petits meshes (4 millions de triangles, 40 000 instances) : 15 s, 377 Mo ; terrain de 1 024 m en 256 patches de 4 225 sommets : 3,6 s, 57 Mo. L'estimation pour la région de 1,3 Go est donnée dans `CHANGELOG.md` (v31).

### Comment le découpage se décide

- Quadtree adaptatif sur le plan X,Z (Y est la hauteur), uniquement sur les cellules non vides. Une cellule est subdivisée tant que son poids autonome dépasse `--budget` **ou** ses triangles dépassent `--budget-tri`, et que son côté dépasse `--min`.
- Un **objet racine** (nœud de premier niveau de la scène) reste **entier**, dans la cellule du centre de sa boîte, si son poids autonome ≤ `--entier-poids` **et** son étendue ≤ `--entier-etendue`. Sinon il est **réparti instance par instance** : chaque instance va dans la cellule de son propre centre, et les nœuds parents sont recopiés (sans mesh) avec leurs transformations d'origine.
- Un objet qui porte un **skin** n'est jamais réparti : son objet racine entier va dans la tuile du centre de sa boîte, avec le skin, les nœuds de joints (même s'ils sont hors de l'objet) et les `inverseBindMatrices`.
- Les meshes partagés entre tuiles sont **dupliqués** dans chaque tuile qui les utilise (tuiles autonomes). La duplication réelle est écrite dans le rapport.
- Les sommets de chaque primitive sont **compactés** : seuls les sommets indexés sont gardés et renumérotés, avec le plus petit type d'indices (16 bits si possible). Les triangles sont identiques.
- Un mesh **unique** plus lourd que le budget (terrain, mer) ne peut pas être réparti à ce stade : sa cellule reste telle quelle, hors budget, avec un avertissement (nom, étendue, Mo).
- Un GLB compressé (Draco, meshopt) est refusé avec un message clair. Accessors `sparse` : refusés avec un message.

### Fichiers produits

`X.tiles/T_<niveau>_<i>_<j>.glb` (niveau et position de la cellule dans le quadtree), `X.tiles.json` (UTF-8 sans BOM) et `X.overview.glb` (v31), à côté du GLB `X.glb` :

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
 "nodeRefs": 1,                     extras.ref / extras.box dans les nœuds des tuiles (v32 ; 0 avec --sans-references)
 "replacedImages": {"distinct": 778, "occurrences": 1200, "grey": 128},    images vides ou invalides remplacées (v31)
 "overview": {"file": "X.overview.glb", "bytes": 23000000, "triangles": 1400000, "terrainTriangles": 131072,
              "objects": 21000, "candidates": 30000, "omitted": {"small": 9000, "skinned": 12, "translucentPrimitives": 800, "budget": 0},
              "effectiveMinExtent": 3, "effectiveTerrainStep": 4, "resolution": 10, "seconds": 95.0, "colors": {...}, "params": {...}},   (v31)
 "tiles": [{"file": "X.tiles/T_3_2_5.glb", "level": 3, "i": 2, "j": 5,
            "min": [x,y,z], "max": [x,y,z],   boîte du contenu réel de la tuile (un objet qui déborde de sa cellule reste couvert)
            "instances": 812, "triangles": 410233,
            "bytes": 21345678, "geometryBytes": 9001234, "imageBytes": 12000000, "replacedImages": 2}]
}
```

Relancer réécrit les `T_*_*_*.glb` du dossier `X.tiles/` ; **ensuite** (v31), les `T_*_*_*.glb` d'une exécution précédente qui ne figurent plus dans le nouvel index sont **supprimés** et le rapport en donne le nombre (les autres fichiers du dossier ne sont pas touchés). `--vue-ensemble-seule` ne touche à aucune tuile.

### Lire le journal (`glb2tiles.log`, à côté du script)

Première ligne : `[glb2tiles] v31 (22/10/2026)`. L'avancement est écrit toutes les 5 % ou 10 s. Le rapport final donne : nombre de tuiles, médiane / 90 % / maximum du poids et des triangles, duplication réelle, nombre de racines entières et réparties, avertissements, temps total. `python glb2tiles.py --version` affiche la version sans journal ni pause.

Dans `--analyse`, la ligne « Lecture » indique les octets lus. Les positions ne sont lues que pour les primitives qui n'utilisent qu'une partie d'un tampon de sommets partagé (la boîte de l'accessor serait trop grande) ; les autres boîtes viennent de l'en-tête.

### Si quelque chose ne va pas

| Symptôme | Cause probable | Que faire |
|---|---|---|
| « GLB compressé » | le GLB utilise Draco ou meshopt | décompresser le GLB d'abord (hors de ce lot) |
| « glb-stats.py introuvable » | le script est seul dans son dossier | copier `glb-stats.py` à côté |
| « Tuile … hors budget » | un mesh unique (terrain, mer) dépasse le budget, ou la cellule minimale est atteinte | normal à ce stade : voir la feuille de route (découpage par triangles) |
| Beaucoup de tuiles pour un petit GLB | `--budget` trop petit ou duplication forte | relancer `--analyse` avec d'autres valeurs |
| « THREE.GLTFLoader: Couldn't load texture » sur une tuile faite avant la v31 | image de 0 octet ou tronquée dans le GLB | refaire le découpage avec la v31 (images remplacées par un gris) |
| « Le découpage recalculé … ne correspond pas à X.tiles.json » | `--vue-ensemble-seule` lancé avec d'autres options de découpage | reprendre exactement les options du découpage d'origine |
| « Pillow absent » dans le rapport | la vue d'ensemble utilise la couleur de base des matériaux (souvent blanche pour un matériau texturé) | `pip install pillow` puis `--vue-ensemble-seule` |
| Vue d'ensemble trop lourde ou objets manquants | budget atteint, `effectiveMinExtent` monté | `--ov-budget` / `--ov-budget-tri` plus grands, ou `--ov-seuil` plus haut ; lire les lignes « objets omis » |
| Instance à 3 000 m signalée | un prim géant ou un objet égaré | l'outil la garde ; la corriger dans le modèle si c'est une erreur |

Test : `python tests/glb2tiles.py` (GLB synthétiques, sans navigateur ni réseau) ; `python tests/v31.py` (images invalides, vue d'ensemble, sortie de promenade).

## 17 bis. Charger une région en tuiles dans la page (`glb2html.py --tiles`, v30)

Une région de plusieurs centaines de Mo ou de plusieurs Go ne tient pas dans un navigateur : après `glb2tiles.py` (§ 17), la **coquille** charge seulement les tuiles proches de l'avatar et décharge les lointaines, et (v31) affiche au loin la **vue d'ensemble légère** `X.overview.glb` quand elle existe. Sans le champ `tiles` dans `X.config.json`, la page se comporte exactement comme avant (un seul `X.glb`).

### Les commandes (PowerShell, une seule ligne)

| Pour | Commande |
|---|---|
| Découper | `python glb2tiles.py "P:\regions\4X4.glb" --exclure "Freebies"` (écrit `4X4.tiles.json` et `4X4.tiles\` à côté du GLB) |
| Mettre la région dans le site | `python glb2html.py --shared-shell -o "P:\site\4X4.html" --tiles "P:\regions\4X4.tiles.json"` |
| Ouvrir | `http://…/index.html?region=4X4` (la coquille commune, comme § 16) |
| Essayer un autre rayon | `index.html?region=4X4&rayon=300` |
| Changer un réglage | relancer la même commande avec l'option : rien de lourd n'est recopié |

`-o` désigne la région (son nom sans extension). Pas de `.glb` en entrée. `--tiles` seul (sans `--shared-shell`) donne une coquille propre `4X4.html`. Sont écrits : `4X4.config.json` (champ `tiles`), `4X4.zones.json` (si absent ou si une source de zones est donnée), la coquille et `lib/` s'ils manquent. **`4X4.tiles.json` et le dossier des tuiles ne sont copiés que s'ils ne sont pas déjà à côté de la page** : mettre `-o` dans le dossier des tuiles évite toute copie (« tuiles déjà à côté de la page : rien n'est copié ») ; sinon le script copie ce qui manque ou a une autre taille, fichier par fichier, et dit combien. Il n'y a pas de `4X4.glb`. Comme tout mode modulaire, la page demande http/https.

### Les paramètres (dans `X.config.json`, avec leurs options)

| Clé / option | Défaut | Sens |
|---|---|---|
| `tileRadius` / `--tile-radius` | 150 | m : charger les tuiles dont la **boîte** (min / max de `X.tiles.json`) est à moins de ce rayon de l'avatar, en plan X,Z (distance 0 = l'avatar est dans la boîte) |
| `tileMargin` / `--tile-margin` | 60 | m : décharger au-delà de rayon + marge (hystérésis : pas de va-et-vient à la limite) |
| `tileMaxMo` / `--tile-max-mo` | 200 | Mo de tuiles chargées en même temps (poids des fichiers `.glb`) |
| `tileMaxTri` / `--tile-max-tri` | 8 000 000 | triangles de tuiles chargées en même temps |
| `tileConcurrency` / `--tile-concurrency` | 4 | téléchargements simultanés |

`?rayon=NNN` dans l'adresse remplace `tileRadius` pour cette ouverture (10 à 5 000). Ces clés n'existent dans la config que pour une région en tuiles.

### Ce que fait la page

- **Départ.** Les tuiles autour du point de départ se chargent d'abord, les plus proches en premier : l'arrivée du lien (`#spawn=…`, sinon l'arrivée `default`) si la page est ouverte par un portail, sinon la cible de la caméra. « Chargement… » reste affiché jusqu'à ce que les tuiles qui contiennent ce point soient prêtes (ou en échec) ; les autres arrivent ensuite. Un sol partiel est normal tant que tout n'est pas là : une tuile ne contient que ses patches de terrain et ses objets.
- **Pendant la visite.** Le point de référence est l'avatar en promenade, ou la cible (le cercle d'atterrissage) en vue globale. Toutes les 250 ms : déchargement des tuiles au-delà de rayon + marge, chargement de celles du rayon. Si `tileMaxMo` ou `tileMaxTri` serait dépassé, les tuiles **chargées les plus lointaines** (plus lointaines que celle à charger) partent d'abord ; une tuile qui contient l'avatar est chargée même si elle dépasse seule le budget (avertissement en console).
- **Mémoire.** Une tuile déchargée libère ses géométries, matériaux, textures et images décodées. Le budget compte le **poids des fichiers** : des textures décodées pèsent bien plus en mémoire graphique que leur fichier compressé ; en cas de page lourde, baisser `tileMaxMo` ou `tileRadius`. La grille de collision de chaque tuile coûte environ 36 octets par triangle de sol et de mur, plus l'index : à 8 millions de triangles, compter plusieurs centaines de Mo.
- **Promenade et collisions.** Une grille de collision est construite par tuile, par tranches pour ne pas figer l'image, et supprimée avec la tuile. Sol et murs ne viennent que des tuiles prêtes. L'avatar **n'avance jamais vers un point dont une tuile n'est pas prête** : il reste sur place, le texte « Chargement du sol… » s'affiche, et il repart dès que la tuile est prête (jamais de chute). **F** attend la tuile sous l'avatar avant de démarrer la promenade (F de nouveau : annuler) ; un portail interne ou un double-clic vers une zone non chargée attend de même. Les patches de terrain ont des bords communs : le sol se prolonge d'une tuile à l'autre sans marche.
- **Tuile en échec** (fichier absent, HTTP 404, GLB illisible) : message en haut de la page et dans la ligne d'information, avertissement en console, nouvelle tentative 3 s, 6 s, 12 s… jusqu'à 30 s après. Les autres tuiles ne sont pas retardées. Un avatar ne traverse pas la boîte d'une tuile en échec (même règle que « pas prête »).
- **Ligne d'information** (texte seul), dans le panneau d'aide en bas à gauche (masquable avec H), sinon dans un petit cadre : « Tuiles : 7 chargées / 106 · 74 Mo · 2,10 M triangles », avec « · 2 en cours » et « · 1 en échec (nouvelle tentative) » quand il y en a, puis (v31) « · Vue d'ensemble (à part) : 23,1 Mo · 1,40 M triangles » : la vue d'ensemble est comptée à part, hors des 200 Mo / 8 M triangles du budget.
- **Vue d'ensemble (v31).** Si `X.tiles.json` mentionne `overview`, la page la charge **en premier** (avant toute tuile), avec les mêmes règles de sécurité de chemin que les tuiles. Elle montre toute la région en géométrie légère, sans image. Chaque cellule (un nœud par fichier de tuile) est **masquée dès que la tuile détaillée correspondante est affichée** et réaffichée quand la tuile est déchargée ou en échec : jamais les deux, jamais de trou pendant un chargement. Elle ne sert **ni aux collisions, ni au sol, ni à « Chargement du sol… »** (la promenade attend toujours la tuile), et n'entre pas dans le budget `tileMaxMo` / `tileMaxTri`. Un **double-clic** dessus en vue globale place la cible sur le point lointain ; le sol réel est repris quand sa tuile est prête. Si elle est introuvable ou illisible : avertissement en console, « Vue d'ensemble indisponible » dans la ligne d'information, la région fonctionne comme en v30.
- **Vue globale.** Avec la vue d'ensemble, la caméra se cadre sur **toute la région** (distance maximale, brouillard et plan lointain suivent l'étendue). Sans elle (ancien `X.tiles.json` ou `--sans-vue-ensemble`), comme en v30 : seules les tuiles chargées autour de la cible, et la caméra se cadre sur le rayon de chargement.
- **Sortie de promenade (v31).** F pour sortir place la cible de la vue globale au sol sous l'avatar et garde le décalage de caméra d'avant l'entrée en promenade ; le chargeur suit cette cible, donc les tuiles autour de l'avatar ne sont pas déchargées.

### Repère, rotation, mer, zones

- **Repère.** Celui du modèle d'origine : **aucun recentrage** (les tuiles gardent leurs coordonnées). Les coordonnées des zones, arrivées, cible de caméra et trou de la mer sont donc dans ce repère, pas dans celui du viewer (qui recentre le modèle entier, ce qu'on ne peut pas faire avec des tuiles). `--rotate` (0, 90, 180, 270) tourne la racine des tuiles autour de l'axe vertical passant par l'origine ; comme au § 11, les valeurs stockées sont dans le repère déjà tourné, et la cible par défaut écrite par `--tiles` l'est aussi.
- **Cible et mer par défaut.** Sans `--target`, la cible de caméra est le centre de l'étendue des tuiles, à 20 m de hauteur ; sans `--sea-y`, la mer est à 20 m (l'eau d'OpenSim). La mer est centrée sur le centre de l'étendue ; le trou (`--hole`, `--hole-x`, `--hole-z`) est relatif à ce centre. Pour retirer la mer : `--no-sea`.
- **Zones libres** (cylindres à coordonnées, arrivées, portails, panneaux) : comme avant. **Zones liées à un objet** (champ `mesh`, v32) : si les tuiles portent les références d'objets (`glb2tiles.py` v32, § 17), la zone **apparaît quand la tuile qui contient l'objet est chargée** et disparaît quand elle est déchargée : cliquable, touche E à moins de `radius` m de l'objet, comme en mode GLB unique. Un objet réparti sur plusieurs tuiles : la zone suit la **boîte de l'objet entier** (stockée dans les tuiles), dès qu'**un** morceau est chargé. Tuiles d'avant la v32 : zone **ignorée**, avec « zone « id » ignorée : liée à l'élément « … » … (tuiles écrites sans références d'objets : redécouper avec glb2tiles v32) » en console, et un avertissement de `glb2html.py` à la génération. Présence, chat, carte des mondes, portails : inchangés. Le viewer ouvre maintenant une région en tuiles (§ 17 ter).
- **Position affichée (v32).** Le panneau d'aide (touche H, en bas à gauche) donne en texte la **position de la cible** en vue globale, ou de l'**avatar** en promenade : « Position cible (vue globale) : x 123.5 · y 15.0 · z -77.7 m », en mètres, une décimale, dans le repère du modèle d'origine : celui des zones. Pratique pour noter un endroit.

### Limites de cette version

- La vue d'ensemble est grossière : les petits objets (sous `--ov-seuil`), le verre et les objets à squelette n'y figurent pas, les couleurs sont unies, le terrain est au pas de 4 m ; à la limite d'une tuile chargée, la hauteur du sol peut différer de quelques décimètres entre la tuile (1 m) et la vue d'ensemble (4 m).
- Les meshes partagés entre tuiles sont dupliqués dans chaque tuile qui les utilise (tuiles autonomes) : plus de Mo téléchargés.
- Un mesh unique plus lourd que le budget de `glb2tiles.py` reste dans une seule tuile (pas de découpage par triangles).
- Une tuile très lourde en triangles reste coûteuse à analyser : la construction de sa grille de collision est découpée, pas supprimée.
- Pas de compression meshopt des tuiles, pas encore de textures de terrain d'OpenSim (couleurs par sommet de `oar2glb.py`).

### Si quelque chose ne va pas

| Symptôme | Cause probable | Que faire |
|---|---|---|
| « Erreur de chargement : … X.tiles.json : HTTP 404 » | `X.tiles.json` n'est pas à côté de la page, ou le champ `tiles` de la config est faux | relancer `glb2html.py --tiles` ; vérifier le dossier |
| « adresse de tuiles refusée » | le champ `tiles` contient `..`, `:`, `?`, `#` ou commence par `/` | un chemin relatif simple (`X.tiles.json`) |
| Sol partiel, trous | tuiles hors du rayon, ou en échec | monter `tileRadius` (ou `?rayon=`), voir la ligne d'information et la console |
| « Chargement du sol… » qui reste | une tuile en échec devant l'avatar | corriger le fichier ; la page réessaie seule |
| Au loin, rien ou un trou | pas de vue d'ensemble (région découpée avant la v31, ou `--sans-vue-ensemble`) | `glb2tiles.py … --vue-ensemble-seule` avec les options d'origine, puis relancer `glb2html.py --tiles` (copie le fichier avec les tuiles) |
| « Vue d'ensemble indisponible » | `X.overview.glb` absent à côté de la page, ou illisible | le copier à côté de `X.tiles.json` ; relancer `glb2html.py --tiles` |
| Page lourde, ralentie | trop de textures chargées | baisser `tileMaxMo`, `tileMaxTri` ou `tileRadius` |
| Les zones liées n'apparaissent pas | la tuile de l'objet n'est pas chargée (elles n'existent que tuile chargée), ou les tuiles datent d'avant la v32 (ignorées, avertissement en console) | s'approcher / `?rayon=` ; sinon refaire le découpage avec `glb2tiles.py` v32 (§ 17), ou utiliser des zones libres à coordonnées |
| Les zones sont décalées | elles viennent du viewer (repère recentré) | les écrire dans le repère du modèle d'origine |

Test : `python tests/tuiles.py` (région synthétique de 16 tuiles, Chromium sans tête) et `python tests/v31.py` (vue d'ensemble dans la coquille, sortie de promenade).

## 17 ter. Poser des zones dans une région en tuiles (viewer, v32)

Le viewer (`glb-viewer.html`) ouvre une région découpée en tuiles et la montre **dans le repère du modèle d'origine** (aucun recentrage) : les coordonnées de zones, d'arrivées, de caméra et du trou de la mer qu'il produit sont directement celles que `glb2html.py --tiles` attend. Il affiche la vue d'ensemble partout et charge les tuiles détaillées **autour de la cible** (avec le même chargeur et les mêmes limites que la page : rayon 150 m, 200 Mo, 8 millions de triangles).

**Pas à pas** (Edge ou Chrome récents) :

1. Ouvre `glb-viewer.html` (double-clic sur le fichier, ou dans un navigateur).
2. Clique sur **« Ouvrir une région en tuiles (dossier) »** et choisis le **dossier qui contient `X.tiles.json`** (celui où `glb2tiles.py` a écrit `X.tiles.json`, `X.overview.glb` et le dossier `X.tiles`). Ou **glisse ce dossier** dans la fenêtre. Le navigateur peut demander de confirmer l'envoi des fichiers : rien n'est envoyé nulle part, il les lit sur place, un par un, quand une tuile est nécessaire. S'il y a plusieurs régions dans le dossier, une liste « Région du dossier » apparaît.
3. Le texte sous les boutons dit ce qui est ouvert (tuiles, vue d'ensemble, références d'objets). La région apparaît en entier ; les tuiles autour de la cible (le petit cercle noir et blanc au sol) se chargent.
4. **Déplace la cible** : double-clic sur le terrain (même sur la vue d'ensemble : les tuiles de cet endroit se chargent). Molette pour zoomer, glisser pour tourner, clic droit + glisser pour déplacer.
5. Dans la section **« Zones »**, choisis le type, clique **« Poser une zone par un clic sur la scène »**, puis clique sur le sol ou un objet **une fois la tuile affichée**. Si tu cliques hors d'une tuile chargée (sur la vue d'ensemble), le viewer te le dit en texte (« Pas de tuile détaillée chargée à cet endroit… »), charge la tuile, et tu cliques de nouveau quelques secondes plus tard. Tout le reste est comme en mode GLB unique : rayon et hauteur, portails (§ 5, 6), arrivées (§ 4), panneaux, Home Assistant (§ 7, 8), touche P en promenade.
6. **Lier une zone à un objet** (§ 9) : dans la fiche de la zone, **« Lier à un élément »**, puis clic sur l'objet. La zone prend la position de l'objet. Une zone liée n'est visible que lorsque la tuile de l'objet est chargée (le texte de la fiche le dit : « tuile non chargée » ; **« Voir cette zone »** la charge). Si le viewer répond que l'élément n'a pas de référence, les tuiles datent d'avant la v32 : refaire le découpage (§ 17).
7. Section **« Coordonnées (m) »** : le point visé (clic simple sur le modèle) et la cible, en texte (x, y, z, une décimale), avec **« Copier le point visé »** et **« Copier la cible »**.
8. **Exporter les zones** : « Exporter zones (.json) » écrit **`X.zones.json`** (X = nom de la région) dans ton dossier de téléchargements. Pour **compléter** une région déjà faite : ouvre la région, « Importer zones (.json) » avec le `X.zones.json` existant, ajoute les nouvelles zones, exporte de nouveau.
9. **Régénérer la page** : renseigne « Chemin de glb2html.py » et clique sur **« Générer la ligne de commande PowerShell »** : le viewer écrit la commande complète (`--tiles`, `--zones`, `-o`, coquille commune, hauteur de la mer, présence, chat…). Lance-la depuis le dossier de `glb2html.py`, en corrigeant le chemin de `X.zones.json` s'il n'est pas à côté. Si la page existe déjà et que la coquille `index.html` a changé de version, supprime-la d'abord (une coquille existante différente n'est jamais écrasée : l'avertissement le dit).

Autre façon d'ouvrir : par adresse, si le viewer est servi en http (par exemple `python -m http.server` lancé dans un dossier qui contient `glb-viewer.html` et, en dessous, la région) : `http://localhost:8000/glb-viewer.html?tuiles=region/X.tiles.json`. Le chemin est relatif à la page, sans `..`, sans `:`, `?` ni `#`.

**Ce qui est différent du mode GLB unique** : pas d'export HTML autonome ni de `.zip` (il n'y a pas de GLB unique ; les boutons sont désactivés) ; pas de rotation de la région (repère d'origine ; avec `glb2html.py --tiles --rotate`, les zones doivent déjà être dans le repère tourné) ; le trou de la mer est relatif au **centre de la région** (comme dans la page) ; la mer est à 20 m par défaut (`--sea-y` pour la changer, la commande l'écrit) ; le filaire des éléments traversables ne montre que les tuiles déjà chargées ; le texte d'une fiche de zone liée (« tuile non chargée ») ne se met à jour qu'au prochain changement de la liste (modifier ou ajouter une zone, cliquer une zone dans la scène), pas au moment où la tuile arrive ; la zone, elle, apparaît aussitôt dans la scène.

Test : `python tests/v32.py` (région synthétique de 16 tuiles : zones libre, portail, arrivée et liées posées dans le viewer, export, puis page générée).


## 18. Nouveautés de la v33 (22/10/2026)

### 18.1 Démarrage avec une arrivée (`#spawn=`, `#pos=`) dans une région en tuiles

**Ce qui se passait (mesuré, 22/10/2026).** Avec un lien `#spawn=chateau`, le chargeur prenait l'arrivée pour référence pendant **4 secondes seulement**, puis revenait à la cible de caméra par défaut. Si la tuile de l'arrivée n'était pas prête à ce moment-là (tuile lourde, processeur ou réseau lents), elle était **déchargée et son téléchargement abandonné**, les tuiles autour de la cible se chargeaient à sa place, et la page attendait 120 secondes avant de continuer, **derrière un écran noir sans aucun texte**. Reproduit sur une région synthétique de 16 tuiles dont deux de plus d'un million de triangles (23 Mo, `tests/glbfab.py`), processeur ralenti 10 fois (outils de développement de Chromium) : écran noir **121,6 s**, avatar en promenade à **125,7 s** ; avec la v33 : promenade à **7,1 s**. Sans ralentissement : 2,6 s avant, 1,6 s après. La cause mesurée est la fenêtre de 4 s (la tuile de l'arrivée, déchargée, était redemandée plus tard) ; la construction de la grille de collision n'en était pas la cause sur cette région synthétique (142 ms de calcul pour 1 million de triangles sans ralentissement, 2 s à x10).

**Ce que fait la v33.**

- Le point d'arrivée demandé (`#spawn=ID`, ou `#pos=x,y,z,yaw`, ou l'arrivée `default` à l'ouverture sans lien) est la **référence du chargeur jusqu'à ce que la promenade démarre** (ou que la cible de la vue globale soit déplacée), jamais la cible de caméra.
- La ou les tuiles qui contiennent ce point démarrent **avant la vue d'ensemble et avant toute autre tuile** ; **aucune autre tuile ne démarre** tant que celles-là ne sont pas prêtes (ou en échec).
- Leur grille de collision passe en premier dans la file, avec un **budget de temps par image de 40 ms** (6 ms pour les autres tuiles). Pendant une promenade, la grille de la tuile qui contient l'avatar passe **toujours** avant les autres.
- **Jamais d'écran noir sans texte** : dès le début, « Chargement du sol… 0/1 tuile prête · 3 s » (tuiles prêtes sur tuiles attendues, temps écoulé), sur fond noir et texte blanc encadré. **Après 15 s**, l'écran noir est retiré : on voit la scène (vue d'ensemble comprise) avec le texte, et la promenade démarre dès que la tuile est prête. Après 60 s, le texte ajoute « attente longue (tuile lourde ou réseau lent) » ; le délai de 120 s n'existe plus.
- Si le chargement échoue, le message d'erreur n'est plus caché derrière l'écran noir.

**`#pos=x,y,z[,yaw]`** (nombres seulement, point décimal, valeurs bornées à ±100 000 ; autre chose est ignoré) : arrivée anonyme à ce point, avec les mêmes règles de chargement. Le repère est celui du modèle d'origine en mode tuiles, celui de la page (modèle recentré) en mode GLB unique. Le panneau d'aide propose **« Copier le lien de ma position »** : adresse de la page (avec `?region=`) suivie de `#pos=x,y,z,yaw` (2 décimales), lisible à l'ouverture ; sans clipboard, le lien est écrit dans un champ du panneau.

**Une ligne par tuile dans la console** (touche F12 du navigateur) quand elle devient prête ou échoue, à coller dans le chat de diagnostic :

```
[tuile] X.tiles/T_3_0_1.glb prête : 14.0 Mo · 1002668 triangles · attente avant téléchargement 0 ms · téléchargement 278 ms · analyse du GLB 28 ms · attente en file de grille 53 ms · construction de la grille 142 ms de travail (1004 ms écoulées) · total 1310 ms
[tuile] X.tiles/T_3_2_4.glb : échec après 2100 ms (HTTP 404)
```

« Construction de la grille » = temps de calcul réellement consommé ; « écoulées » = temps d'horloge entre l'entrée dans la file et la fin (comprend le rendu des images). `viewer.tilesState().log` (console du navigateur : `__viewer.tilesState().log`) donne les mêmes valeurs en nombres.

### 18.2 Arrivée par défaut et retour à l'arrivée

Règle exacte, **sans lien** (ni `#spawn=` ni `#pos=`) :

| Situation | Cadrage de départ (cible de la caméra) | Touche F (sans avoir déplacé la cible) |
|---|---|---|
| la région a une arrivée `default`, pas de `--target` | **la position de cette arrivée** | **son point et son orientation** |
| la région a une arrivée `default`, `--target` donné | la cible donnée | la cible (comme avant) |
| pas d'arrivée `default` | la cible (celle de la configuration, ou le centre de l'étendue en mode tuiles) | la cible (comme avant) |
| configuration écrite avant la v33 (sans la clé `targetExplicit`) | la cible (comme avant) | la cible (comme avant) |

Avec un lien (`#spawn=`, `#pos=`), le cadrage et la promenade se font à l'arrivée demandée. En mode tuiles, c'est ce point qui sert de référence de chargement au départ.

Le viewer écrit `targetExplicit` à vrai quand la cible de sa caméra n'est pas la cible par défaut (même test que la ligne de commande `--target`). Une arrivée `default` placée dans le viewer ne change donc rien à une page dont tu as cadré la caméra à la main.

**Retour à l'arrivée** : bouton « Retour à l'arrivée (R) » ou touche **R**. En promenade : téléportation à l'arrivée `default` (à défaut : à la cible de départ), avec « Chargement du sol… » si la tuile n'est pas prête, comme un portail interne. En vue globale : la cible et la caméra se déplacent sur ce point (même décalage de caméra).

### 18.3 Marqueurs de zones dans la page exportée

| Option | Valeur | Effet |
|---|---|---|
| `--zone-marker` | `discret` (défaut) | comportement d'avant : disque plat de 0,4 m semi-transparent et anneau fin |
| | `portee` | **anneau fin et net au rayon réel de la zone**, sans cylindre ; un trait d'un pixel est ajouté à l'anneau plat pour qu'il reste tracé de loin |
| | `aucun` | aucun marqueur ; la zone reste cliquable et se déclenche comme avant |
| `--show-spawns` | (aucune) | dessine aussi les **arrivées** : petit disque de 0,3 m et anneau fin au sol. Sans cette option, les arrivées ne sont **jamais** dessinées dans la page exportée (seulement dans l'éditeur) |

Ils concernent les portails et les zones libres (lien web, commande). Réglage dans le viewer : section « Zones » (menu « Marqueur des portails et zones libres », case « Dessiner les arrivées ») ; il figure dans le récapitulatif de la ligne de commande. Config : `zoneMarker`, `showSpawns`.

### 18.4 Vol, trois vues, « Aller à »

- **Vol** (`--fly`, défaut ; `--no-fly` le retire de la page et de l'aide) : **Début** décolle ou atterrit. En vol, **Page Haut** (ou **Espace** maintenu, v36) monte et **C** descend (même vitesse que la marche, **Maj** accélère), pas de gravité, les murs bloquent comme au sol, l'avatar ne descend jamais sous le sol des tuiles chargées. Vers une tuile pas encore prête, l'avatar s'arrête au bord (« Chargement du sol… »), comme à pied. À l'atterrissage la gravité le ramène sur le sol (ou sur un toit). La présence transmet la hauteur normalement. En vol, E déclenche la zone proche comme au sol (v36).
- **Vues** (**V**) : subjective (la vue d'avant) ; **troisième personne** (la caméra tourne autour de l'avatar, à 4 m, se rapproche si un mur est derrière lui, ne passe jamais sous le sol, la souris règle la hauteur) ; **caméra libre** (l'avatar reste sur place, les touches de déplacement et les flèches déplacent et tournent la caméra, **Page Haut** et **C** la montent et la descendent, elle ne traverse pas le sol). En caméra libre, **V** de nouveau rend la main à l'avatar (v36 : **F** quitte la promenade, comme **P**). L'avatar est dessiné avec le même modèle que les autres visiteurs, avec le nom et la couleur du visiteur. La vue est écrite en texte dans le panneau d'aide (v34 : « Vue : troisième personne » et « Mode : à pied » dans le bloc d'état, § 19.1).
- **« Aller à x, y, z »** (panneau d'aide) : mètres, **repère du modèle d'origine en mode tuiles, repère de la page (modèle recentré) en mode GLB unique** (le panneau le dit). Formats : `68.2, 39, -823.3` ; `68.2 39 -823.3` ; `68,2 ; 39,0 ; -823,3` (virgule décimale avec points-virgules). En promenade : téléportation, avec l'attente de la tuile ; en vue globale : la cible se déplace.

### 18.5 Chat

- **Saisie persistante** : **Entrée** ouvre la saisie, **Entrée envoie et la garde ouverte** (champ vidé), **Échap** la ferme et rend les touches à la promenade. Tant qu'elle est ouverte, les lettres vont dans le texte, mais les **flèches** déplacent et font tourner l'avatar. L'état est écrit dans l'aide. Rien ne change pour qui n'utilise pas le chat.
- **Enregistrer le chat** : bouton sous le chat. Télécharge un fichier texte UTF-8 (avec marque d'ordre des octets, lisible dans le Bloc-notes, fins de ligne Windows) : une ligne `jj/mm/aaaa hh:mm:ss | Nom | texte` par message reçu ou envoyé **depuis ton arrivée**. Tout se passe dans le navigateur : **rien n'est stocké côté serveur pour toi**. Précision : le serveur de présence garde en mémoire les derniers messages d'un salon (`--history`, 20 par défaut) et les rejoue à l'arrivée d'un visiteur ; ils s'affichent mais **ne sont pas dans le fichier** (ils précèdent l'arrivée).
- **Pseudo cité** : quand ton pseudo figure dans un message reçu **en mot entier**, sans tenir compte des majuscules, avec ou sans `@` devant (`@alice`, `ALICE,`, `l'alice` oui ; `Alicex`, `Alicia` non), le message est affiché **en gras et précédé de « @ »**, la **bulle de l'auteur clignote** 6 fois (visible 150 ms, cachée 150 ms) et un **bip court** est joué (Web Audio, volume modéré, sans fichier ; seulement après une première interaction avec la page, règle des navigateurs). Trois cases dans « Réglages » : gras, clignotement (cochées par défaut), son (décochée par défaut), mémorisées dans le navigateur. Aucun changement côté serveur. Tout est redondant avec le texte : rien ne dépend de la couleur.
- **Complétion `@`** : quand le texte se termine par `@` suivi de lettres, une liste de **5 pseudos au plus** (visiteurs en ligne dont le pseudo commence par ces lettres) s'affiche au-dessus de la saisie ; **flèches haut et bas** pour choisir (le choix est marqué par `▶`, en gras et en inversé), **Tab ou Entrée** insèrent `@Pseudo ` (Entrée n'envoie pas tant que la liste est ouverte), **Échap** ferme la liste sans fermer la saisie. Liste vide : rien n'est affiché.

### 18.6 Couleur de l'avatar (client et serveur)

Réglages → « Choisir la couleur de mon avatar » : la valeur est mémorisée dans le navigateur et **envoyée dans le message `hello`** (entier de 0 à 0xFFFFFF). `presence_server.py` l'accepte si c'est **un entier entre 0 et 0xFFFFFF** ; sinon (hors bornes, flottant, texte, booléen, null, liste) il la **rejette sans rien dire** et tire une couleur au hasard, comme avant, puis la diffuse comme couleur actuelle. Un ancien client (sans couleur) fonctionne ; un ancien serveur ignore simplement le champ. Depuis la v34, le changement est **envoyé aussitôt** (§ 19.5). **Le nom affiché reste le repère principal** (étiquette au-dessus de l'avatar) ; rien n'est basé sur la couleur seule.

**À faire côté serveur : relancer `presence_server.py` avec la nouvelle version** (la couleur choisie n'est prise en compte que par la v33 du serveur). Commande type (une seule ligne, à adapter à tes options) :

```
python .\presence_server.py --host 0.0.0.0 --port 8765 --log presence.log --log-days 30 --log-ip raw
```

### 18.7 Adresses IP dans le journal : `--log-ip raw`

L'option existante `--log-ip` accepte `hash` (défaut : empreinte de 8 caractères), `raw` (**adresse en clair**) ou `none`. Avec `raw`, l'adresse figure **dès la connexion**, dans la console et dans le journal (`--log`) : `connexion | salon=… | Nom [id 3, clé a1b2c3, ip ADRESSE]`. Vérifié par `tests/v33.py` (défaut : empreinte ; `raw` : adresse en clair, dans la console et dans le fichier).

**Rappel : une adresse IP est une donnée personnelle.** Informe tes visiteurs que le journal les enregistre (et à quelle fin), limite la durée de conservation avec `--log-days` (30 jours par défaut ; le journal tourne chaque nuit), et ne publie jamais le journal.

### 18.8 Enregistrer les zones directement dans le dossier de la région (viewer)

En mode tuiles, section « Zones » du viewer : bouton **« Enregistrer les zones dans le dossier de la région »**.

1. **Edge ou Chrome** (API File System Access) : le bouton demande **une seule fois** le dossier de la région (celui qui contient `X.tiles.json`, accès en lecture-écriture). Il est mémorisé pour la session (et dans IndexedDB quand le navigateur l'accepte, pour ne pas le redemander ; une confirmation d'accès peut être redemandée par le navigateur).
2. `X.zones.json` y est écrit (X = nom de `X.tiles.json` sans extension), **après avoir gardé l'ancien sous `X.zones.bak.json`** (une seule copie, écrasée à chaque enregistrement).
3. Le viewer affiche en texte le dossier, le fichier, la date jj/mm/aaaa et l'heure. (Le navigateur ne donne pas le chemin complet, seulement le nom du dossier.) Si le dossier choisi ne contient pas `X.tiles.json`, rien n'est écrit.
4. **Sans l'API (Firefox, Safari), ou si l'accès est refusé** : le fichier est téléchargé et le viewer dit « enregistre ce fichier dans le dossier de la région, sous le nom X.zones.json, en remplaçant l'ancien ». Choix du dossier annulé : rien n'est écrit.

**La coquille relit `X.zones.json` à chaque ouverture** : après cet enregistrement, **F5 suffit** dans le navigateur, **sans régénérer la page** — sauf si tu changes les options de la page (`--zone-marker`, `--target`, `--presence-url`…), qui sont dans `X.config.json`.

### 18.9 `glb2html.py --tiles --zones` avec le fichier déjà en place

Si `--zones FICHIER` désigne **le `X.zones.json` de destination** (même chemin une fois résolu, absolu ou relatif), rien n'est copié, rien n'est réécrit, rien n'échoue : le script dit « zones déjà en place ». Le fichier n'est donc pas filtré par le profil `public` ni reformaté. Sans `--zones`, un `X.zones.json` existant est de toute façon conservé.

### 18.10 Mettre à jour une région déjà publiée

La coquille (`index.html`), `core.js` et `X.config.json` changent ; **les tuiles et `X.tiles.json` ne changent pas** (aucun redécoupage). Supprimer la coquille `index.html` de la région (une coquille existante et différente n'est jamais écrasée), régénérer la page **sans `--zones`** (le `X.zones.json` existant est conservé), relancer `presence_server.py` (§ 18.6).

## 19. Nouveautés de la v34 (22/10/2026)

### 19.1 Panneau d'aide sélectionnable et bloc d'état

- Le **texte de l'aide** (touche **H**) se sélectionne à la souris et se copie avec **Ctrl+C**, sans bouton « copier » ; **Ctrl+C n'est plus intercepté** par la promenade (la touche **C** seule continue de descendre en vol). L'aide reçoit la souris : le survol des marqueurs de zones ne marche plus **sous** l'aide, il marche partout ailleurs. Son encombrement est borné (largeur de 440 px au plus et 45 % de la fenêtre, hauteur de 42 % de la fenêtre avec défilement).
- Nouveau **bloc d'état**, séparé de l'aide, en dessous d'elle, avec le texte sélectionnable aussi : `Vue : …` (subjective, troisième personne, caméra libre, ou globale en orbite), `Mode : à pied` / `Mode : en vol`, `Souris : …` (§ 19.4), `Position avatar : x … y … z …` (ou cible de la vue globale), puis les lignes des tuiles et de la vue d'ensemble. L'aide ne garde que les touches et les réglages.
- **H** masque l'aide seule (l'état reste). **I** masque ou affiche le bloc d'état (choix mémorisé dans le navigateur, clé `glb2html_state`).
- L'étiquette « Vue : troisième personne · au sol » est remplacée par deux lignes : « Vue : troisième personne » et « Mode : à pied ».

### 19.2 Zone de survol et de clic des marqueurs

| Option | Rayon de la zone de survol / de clic (disque invisible au sol) |
|---|---|
| `--zone-marker portee` | **le rayon de l'anneau visible** (rayon réel de la zone ; 2 m au moins pour un panneau) : l'infobulle apparaît en survolant l'anneau ou son intérieur |
| `--zone-marker discret` (défaut) | le rayon de la zone borné entre **0,6 m** (comme avant) et **1 m** |
| `--zone-marker aucun` | 0,6 m, comme avant |

### 19.3 Vol

**Page Haut** monte, **Page Bas** descend (en plus de **Espace** maintenu et **C**, v36), sans défilement de la page. **Début** garde la bascule. Quand on descend jusqu'au sol, **l'avatar atterrit tout seul** (le vol s'arrête, la gravité reprend) ; il ne passe jamais sous le sol. Le bouton **« Voler / Atterrir »** de la barre du bas (visible en promenade, absent avec `--no-fly`) bascule le vol ; son état (`aria-pressed`) et la ligne « Mode : … » le disent en texte.

### 19.4 Souris libre après Échap

En promenade, quand le pointeur est libéré (Échap, ou perte du focus), la page mémorise **« souris libre »**, écrit « Souris : libre (G ou bouton « Capturer la souris » pour la reprendre) » dans le bloc d'état et **ne redemande plus le verrouillage** : un clic simple, un double-clic (téléportation à l'endroit du curseur) et un clic sur une zone fonctionnent à l'endroit du curseur ; glisser avec le bouton enfoncé tourne toujours la vue. **Recapturer** : touche **G** ou bouton **« Capturer la souris »** (barre du bas). L'état est remis à zéro à chaque entrée en promenade (le premier clic capture comme avant).

### 19.5 Couleur en direct

Changer la couleur dans les Réglages pendant la connexion envoie `{"t":"color","color":N}` (au plus toutes les 300 ms, la dernière valeur part toujours). `presence_server.py` accepte un **entier de 0 à 0xFFFFFF** (sinon ignoré sans rien dire), ignore deux changements à moins de 0,2 s, met le visiteur à jour et diffuse `{"t":"color","id":…,"color":N}` aux autres ; un visiteur qui arrive ensuite reçoit la couleur à jour. L'avatar du visiteur lui-même (vue à la troisième personne) la prend aussi. Compatible : un ancien serveur ignore le message, un ancien client n'en envoie pas. **Relancer `presence_server.py`** pour en profiter.

### 19.6 `glb2html.py --maj` : mettre à jour une région sans rien ressaisir

| Option | Effet |
|---|---|
| `--maj` | lit `X.config.json` existant, **n'applique que les options explicitement données** (une valeur égale à la valeur par défaut, mais donnée, est appliquée), garde tout le reste (clés inconnues comprises) et `X.zones.json` (réécrit seulement avec `--zones`), écrit la version courante, **renouvelle la coquille** si elle diffère de celle de cette version (ancienne copie gardée sous `index.avant-AAAAMMJJ-HHMMSS.html`) et écrit `lib/` s'il manque. Sans `X.config.json`, échoue en proposant la commande sans `--maj`. Exclut `--settings` |

Forme : `python glb2html.py --maj -o "X.html" [--shared-shell [COQUILLE.html]] [--tiles "X.tiles.json" | "X.glb"] [options]`. Sans `--shared-shell`, la page `X.html` doit exister. La coquille est **partagée par les autres régions du dossier** : elles gardent leur comportement (les anciennes configurations restent comprises ; aucune clé de config n'est nouvelle en v34). Le compte rendu liste les clés changées. Le profil (`--profile`) ne filtre les zones qu'à l'écriture de la liste : ajouter `--zones` pour la réécrire.

### 19.7 Pseudo, lien personnel, page de lancement

- **`#name=PSEUDO`** dans l'adresse règle le pseudo (mémorisé dans le navigateur) ; les portails et la carte l'ajoutent déjà.
- Réglages → **« Copier mon lien personnel »** : copie l'adresse de la page avec `#name=PSEUDO&key=CLE`, où CLE est la **clé d'identité du navigateur** (32 caractères hexadécimaux, `glb2html_uid`, celle que le serveur associe au nom réservé). **Ce lien est un secret : quiconque l'ouvre prend l'identité** (le nom réservé). À l'ouverture, une clé au bon format devient celle du navigateur ; si ce navigateur en a déjà une **différente**, un message à l'écran demande confirmation avant de la remplacer. La clé est ensuite **retirée de l'adresse visible**. Une clé au mauvais format est ignorée (et retirée). Aucune modification du serveur.
- **Page carte** (`--map-page`) : champ **« Mon pseudo »** en haut, mémorisé dans le navigateur ; les liens vers les régions reçoivent `#spawn=…&name=PSEUDO`.

## 20. Nouveautés de la v35 (22/10/2026)

### 20.1 Aide en groupes, panneaux repliables

- L'aide est écrite en **groupes courts**, une ligne par groupe, sans phrases : **Déplacement**, **Vol**, **Vue**, **Souris**, **Chat**, **Zones**, **Page** (en vue globale : **Vue globale**, **Promenade**, **Zones**, **Page**). La mention « Ctrl+C copie » et l'explication de la sélection ont disparu ; le texte reste sélectionnable.
- L'aide et le bloc d'état ont chacun une **barre de titre** (« ▾ Aide », « ▾ État ») : un clic la **replie** (« ▸ Aide », seule la barre reste) ou la déplie. Le titre dit l'état en texte (flèche et `aria-expanded`), jamais par la couleur. L'état replié ou déplié est **mémorisé dans le navigateur** (clés `glb2html_helpFold` et `glb2html_stateFold`). **H** et **I** continuent de masquer entièrement l'aide et l'état.
- Le bouton « Quitter la promenade (F) » est supprimé (la touche **P** suffit). En vue globale, le bouton s'appelle « Promenade (P) ».

### 20.2 Touches Firestorm / touches de cette page

Colonne de gauche : les défauts du visualiseur officiel d'après le wiki de Second Life (Quick Start Guide, « Keyboard Shortcuts »), que Firestorm reprend à ma connaissance ; ils n'ont pas été comparés ici à une installation de Firestorm.

| Commande | Firestorm | Cette page |
|---|---|---|
| Marcher avant / arrière | W ou ↑ / S ou ↓ | W ou ↑ / S ou ↓ (ZQSD en AZERTY ; v36 : l'aide affiche les lettres réelles) |
| Pas de côté | A / D (ou Maj + flèches) | A / D (Q / D en AZERTY) |
| Tourner | ← / → | ← / → (à la troisième personne : tourne la caméra) |
| Courir | double appui sur W / S / ↑ / ↓ ; Ctrl+R bascule la course | **Maj**, ou **double appui** (moins de 300 ms) sur W, S, ↑ ou ↓, tant que la touche est maintenue. **Pas de course permanente** (Ctrl+R recharge la page du navigateur) |
| Sauter | E ou Page Haut (appui bref) | **Page Haut** (appui bref) ou **Espace** (v36 : E ne saute plus) |
| Voler / atterrir | Début | **Début** ou le bouton « Voler / Atterrir » (v36 : F ne bascule plus le vol) |
| Décoller | E ou Page Haut maintenu | **Page Haut** maintenu **plus de 0,4 s** au sol : vol + montée |
| Monter en vol | E ou Page Haut | **Page Haut** ou **Espace** maintenu |
| Descendre en vol | C ou Page Bas | **C** ou **Page Bas** maintenu ; **atterrissage automatique** au sol |
| Vue subjective | M | **M** bascule vue subjective / troisième personne ; **V** fait tourner les trois vues (dont la caméra libre) |
| Orbiter la caméra | Alt + glisser | **Alt + glisser** (à la troisième personne, la souris orbite déjà autour de l'avatar sans le tourner) |
| Caméra derrière l'avatar | Échap | **Fin** ou **Alt + clic** (Échap est réservé au navigateur : il libère la souris) |
| Zoom caméra | molette | **molette** (3e personne : distance de la caméra ; caméra libre : avance / recule) |
| Carte du monde | Ctrl+M | **Ctrl+M** partout ; **M** seul l'ouvre aussi hors promenade |
| Chat | Entrée | **Entrée** |
| Entrer / sortir de la promenade | (n'existe pas) | **P** ou **F** (v36) |
| Toucher un objet, une zone | clic | **clic** ou **E** (v36) ; un portail « en marchant dedans » part à l'entrée de son rayon |
| Se téléporter | (carte, double-clic selon le réglage) | **double-clic** |

Gardées telles quelles : ZQSD / WASD / flèches, Espace, Entrée, G, R, V, H, I, Maj.

### 20.3 Vol et saut

- Au sol, **Page Haut** : un appui bref fait **sauter** (comme Espace) ; **maintenu plus de 0,4 s**, l'avatar **décolle** et monte tant que la touche est tenue. Relâchée, il reste en vol, immobile en hauteur.
- **Début** bascule le vol (v36 : F ne le fait plus) ; le bouton « Voler / Atterrir » reste. Descendre jusqu'au sol (C ou Page Bas) pose l'avatar : le vol s'arrête tout seul (v34). Avec `--no-fly`, rien de tout cela ne fait voler : Page Haut saute seulement.

### 20.4 Troisième personne

- La **souris orbite la caméra** autour de l'avatar (lacet et tangage propres à la caméra) **sans le tourner** ; à l'arrêt l'avatar garde son orientation : on peut tourner autour de lui et voir son devant.
- Quand une touche de marche est pressée, **l'avatar se tourne vers sa direction de déplacement** (rotation lissée, quelques dixièmes de seconde) ; la marche avant va **dans la direction de la caméra**. La caméra ne traverse ni sol ni mur, comme avant.
- **La présence transmet l'orientation de l'avatar**, pas celle de la caméra : tourner la caméra de 180° sans marcher ne change rien pour les autres visiteurs. Vue subjective et caméra libre sont inchangées. **M** (ou V) change de vue ; en passant à la vue subjective le regard garde la direction de la caméra.

### 20.5 Infobulle et clic des zones : `--zone-info-dist`

| Option | Config | Effet |
|---|---|---|
| `--zone-info-dist M` | `zoneInfoDist` | distance, **en promenade**, jusqu'à laquelle l'infobulle, le clic et le **nom affiché** (« Toujours afficher le nom ») des zones fonctionnent. **40 m par défaut** (14 m avant), de **5 à 200** (hors bornes : ramené à la borne). Réglable dans le viewer (section « Promenade »), repris dans la ligne de commande. Un nom plus loin que cette distance est masqué en promenade et réapparaît en vue globale |

`glb2html.py --maj --zone-info-dist 60` suffit à l'appliquer à une région déjà publiée (§ 20.7).

### 20.6 Copier dans le presse-papiers

Tous les boutons « copier » (lien personnel, lien de ma position, point visé, cible, commande) utilisent `navigator.clipboard.writeText` dans un **contexte sécurisé** (https, localhost), et sinon, **en http sur une adresse publique**, un repli : champ temporaire hors écran, sélection, `document.execCommand('copy')`, suppression. La page affiche **« Copié »** quelques secondes. Si tout échoue, le champ du lien reste **affiché et sélectionné**, avec « Copie impossible : le texte est sélectionné, fais Ctrl+C ».

### 20.7 `--maj` et la carte des mondes

`glb2html.py --maj` accepte maintenant aussi `--register FICHIER`, `--region-name`, `--region-xy`, `--region-url`, `--region-spawn`, `--thumb`, `--map`, `--map-url` et `--map-page FICHIER.html` : il applique ce qui est donné et garde tout le reste (config et zones, comme avant). Le salon et la présence de la fiche viennent de la config existante quand tu ne les redonnes pas.

**Avec `--maj`, les chemins relatifs de `--register`, `--map`, `--map-page` et `--thumb` sont relatifs au dossier de la page (celui de `-o`)**, et non au dossier des outils ni au dossier de lancement ; le message de fin le rappelle avec le dossier. Un chemin absolu est respecté. `--region-name`, `--region-url`, `--region-xy`, `--region-spawn` et `--thumb` sans `--register` sont ignorés avec un avertissement.

**Sans `--maj`**, l'ancien comportement est conservé (un chemin relatif de `--register` est cherché dans le dossier de lancement, sinon dans le dossier des outils, où il est créé) ; quand le fichier n'est pas à côté de la page `-o`, une ligne dit où `regions.json` est écrit et propose `--maj` ou un chemin complet.

### 20.8 Créer la carte des mondes

1. **Chaque région est enregistrée dans un même `regions.json`**, à côté des pages (un seul dossier de pages, une coquille commune). Pour chaque région déjà générée, une commande `--maj --register`, **une seule ligne PowerShell** (nom, position sur la grille OpenSim, vignette facultative de 140 Ko au plus à côté de la page) :

   `python glb2html.py --maj -o "X.html" --shared-shell --register regions.json --region-name "Nom affiché" --region-xy 1000,1001 --thumb vignette.png`

   La fiche reçoit l'adresse `index.html?region=X`, le salon et le serveur de présence de la config de la région. Redonner la commande met la fiche à jour (identifiée par le salon), sans doublon.
2. **Générer la page web de la carte** : `python glb2html.py --maj -o "X.html" --shared-shell --map-page carte.html` (elle lit les régions de `regions.json` enregistrées dans la config de la région `X`). Pour qu'elle contienne toutes les régions, exécute-la **après** les enregistrements, ou donne `--map regions.json --map-page carte.html`.
3. **L'ouvrir par le serveur web**, pas depuis le disque : le dossier contenant `carte.html`, `index.html`, `lib/` et les régions est servi en http(s) (`python -m http.server` pour un essai, ou `presence_server.py --serve-dir` quand il hébergera les pages), puis ouvre `http://ADRESSE/carte.html`. Chaque lien de la carte ouvre la région à son point d'arrivée, avec le pseudo saisi en haut de la page.
4. **Les pages des régions** affichent la carte avec la touche **M** (**Ctrl+M** en promenade) : `--map-url http://ADRESSE/regions.json` (plusieurs adresses séparées par des virgules, fusionnées) les fait relire `regions.json` à chaque ouverture, sans régénérer les pages.

### 20.9 Caméra libre et molette

- **Troisième personne** : la **molette** règle la distance de la caméra (de **1 à 30 m**, **4 m par défaut**, mémorisée dans le navigateur, clé `glb2html_tpsDist`), avec le recul devant un mur et la protection du sol déjà en place. **Fin** remet la caméra derrière l'avatar à la distance par défaut.
- **Caméra libre** : la molette **avance ou recule la caméra le long du regard**, d'un pas proportionnel à la distance caméra-avatar (15 %, au moins 0,5 m et au plus 20 m par cran), jamais sous le sol. La **vitesse des touches** est `max(vitesse de marche, 0,5 x distance caméra-avatar)` m/s, plafonnée à **60 m/s** ; **Maj la multiplie par 3**. **Alt + glisser** fait orbiter la caméra autour de l'avatar en gardant sa distance (lacet et tangage), le regard restant sur lui. **Fin** la remet derrière l'avatar, à 4 m.
- **Vue subjective** : la molette ne fait rien. Dans tous les cas la page ne défile pas en promenade (sur la vue ; l'aide et l'état gardent leur défilement).
