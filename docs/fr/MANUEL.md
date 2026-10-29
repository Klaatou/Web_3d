# Mode d'emploi : zones, portails et points d'arrivée (v52)

> **Résumé (v52).** Ce fichier est le mode d'emploi détaillé ; il ne se lit pas d'un bout à l'autre. Pour **toutes les options** des outils, avec leur effet et leur défaut en français et en anglais : `REFERENCE_OPTIONS.md` (générée depuis les outils par `gen_reference.py`). Pour **faire une tâche pas à pas** (OAR vers page, région en tuiles, mise à jour, zones, serveur de présence, carte) : `PROCEDURES.md`. Ici : les zones et les portails (§§ 1 à 10), les touches (§ 2), les réglages et leurs fichiers (§§ 11 à 19) et les nouveautés version par version (§§ 18 à 34 ; le § 27 est la référence des fichiers JSON). Langue de la page et des outils : § 21.8 à 21.11.

## 1. La règle qui explique 90 % des pannes

Chaque zone a deux noms :

| Champ           | À quoi il sert                                 | Qui le lit                                             |
| --------------- | ---------------------------------------------- | ------------------------------------------------------ |
| **Identifiant** | le nom technique de la zone                    | les portails, la carte des mondes, les liens `#spawn=` |
| **Nom affiché** | le texte vu par le visiteur (« E : Empereur ») | uniquement l'écran                                     |

**Un portail désigne toujours une arrivée par son Identifiant, jamais par son Nom affiché.**
L'identifiant est automatiquement mis en minuscules, et tout caractère autre que lettre non accentuée, chiffre, `-` ou `_` y devient un tiret (`Salle du Trône` devient `salle-du-tr-ne`). Écris-le directement en minuscules, sans accent ni espace, pour éviter les surprises.

Exemple juste :

- Arrivée : Identifiant `empereur`, Nom affiché `Salle de l'Empereur`
- Portail : Point d'arrivée `empereur`

## 2. Les touches

| Touche                                  | Effet                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **F** (v36)                             | **entre en promenade et en sort**, en vue globale comme en promenade (comme **P**) ; le vol se bascule avec **Début** (en v35, F basculait le vol). **À la sortie (v31)**, le petit cercle d'atterrissage et la cible de la vue globale se posent **au sol, sous le dernier endroit où se trouvait l'avatar** ; la caméra revient à la **même distance et dans la même direction** de cette cible qu'avant l'entrée en promenade (elle ne revient plus à l'endroit exact d'où tu étais parti). En mode tuiles, les tuiles autour de l'avatar restent donc chargées. |
| **P** (v35)                             | **entrer dans la promenade / en sortir** (le bouton « Promenade (P) » reste en vue globale ; il n'y a plus de bouton « Quitter la promenade »). Dans le **viewer**, P pose une zone en promenade : on en sort avec **F**, **Maj+P** ou le bouton                                                                                                                                                                                                                                                                                                                    |
| **E** (v36)                             | **déclenche la zone proche** (déclenchement « au clic » ou « les deux », comme avant la v35 ; un portail « en marchant dedans » part à l'entrée de son rayon, § 8). Le nom de la zone proche s'affiche en bas : « clic ou E : … ». **E ne fait rien d'autre** (il ne saute plus et ne monte plus)                                                                                                                                                                                                                                                                   |
| **Page Haut** (v35)                     | **appui bref au sol = saut** (comme Espace) ; **maintenu plus de 0,4 s au sol = décoller** ; en vol, maintenu = monter                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **Espace** (v36)                        | au sol : saut ; **en vol, maintenu : monter**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **T** (v36)                             | affiche ou masque les **repères de portail** (petits cônes, § 21.4) ; le choix est mémorisé                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **Début** (v33)                         | décoller ou atterrir (bascule ; v36 : F ne bascule plus le vol). En vol : **Page Haut** ou **Espace** maintenu monte, **C** / **Page Bas** descend, pas de gravité, les murs restent solides, jamais sous le sol. Retirable avec `--no-fly` (§ 18.4)                                                                                                                                                                                                                                                                                                                |
| **M** (v35)                             | **en promenade : bascule vue subjective / troisième personne** ; hors promenade : ouvre la carte des mondes (comme avant). **Ctrl+M ouvre la carte des mondes partout**. **v36 : la touche est reconnue par la lettre imprimée « m »**, pas par sa place : sur un clavier AZERTY c'est la vraie touche M (avant, c'était la touche « , »)                                                                                                                                                                                                                           |
| **Fin**, **Alt + clic** (v35)           | remettre la caméra **derrière l'avatar** (troisième personne). **Alt + glisser** orbite la caméra (à la troisième personne la souris orbite déjà ; en vue subjective, Alt + glisser regarde autour comme la souris)                                                                                                                                                                                                                                                                                                                                                 |
| **molette** (v35)                       | en promenade, la page ne défile pas. **Troisième personne** : règle la distance de la caméra (1 à 30 m, 4 m par défaut, mémorisée) ; **caméra libre** : avance / recule la caméra le long du regard ; vue subjective : rien (§ 20.9)                                                                                                                                                                                                                                                                                                                                |
| **double appui** sur W, S, ↑ ou ↓ (v35) | **course** tant que la touche reste enfoncée (deux appuis à moins de 300 ms) ; **Maj** reste une course. Pas de course permanente (Ctrl+R recharge la page)                                                                                                                                                                                                                                                                                                                                                                                                         |
| **V** (v33)                             | changer de vue : subjective → troisième personne → caméra libre → subjective. La vue courante est écrite en texte dans le bloc d'état (« Vue : … », v34)                                                                                                                                                                                                                                                                                                                                                                                                            |
| **R** (v33)                             | **retour à l'arrivée** : en promenade, téléporte à l'arrivée `default` (à défaut, à la cible de départ) en attendant la tuile ; en vue globale, recadre la cible et la caméra sur ce point. Le bouton « Retour à l'arrivée (R) » fait la même chose                                                                                                                                                                                                                                                                                                                 |
| **Entrée** (v33)                        | ouvrir la saisie du chat ; **Entrée envoie et garde la saisie ouverte**, **Échap** la ferme. Les flèches continuent à déplacer l'avatar (§ 18.5)                                                                                                                                                                                                                                                                                                                                                                                                                    |
| **Page Haut** / **Page Bas** (v34)      | en vol, monter / descendre (en plus de **Espace** maintenu / **C**, v36) ; la page ne défile pas. **Descendre jusqu'au sol pose l'avatar** : le vol s'arrête tout seul. Bouton « Voler / Atterrir » dans la barre du bas pour qui n'a pas de touche Début (§ 19.3)                                                                                                                                                                                                                                                                                                  |
| **Échap** (v34)                         | libère la souris en promenade. La souris reste alors **libre** jusqu'à **G** ou au bouton « Capturer la souris » (§ 19.4) ; **un clic ne la capture jamais** (après la v52)                                                                                                                                                                                                                                                                                                                                                                                     |
| **G** (v34) | **bascule la capture de la souris** (après la v52) : capture si elle est libre, la libère si elle est capturée. Le bouton « Capturer la souris » ne fait que capturer (un pointeur capturé ne peut rien cliquer) ; **un clic ne la capture jamais** |
| **O** (v37)                             | ouvre / ferme la fenêtre **Réglages** (bascule, comme **H** et **I**) ; **R** est déjà pris par le retour à l'arrivée                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **I** (v34)                             | la fenêtre **Informations / État** (v36 : ancien « bloc d'état » : vue, mode, souris, clavier, position, tuiles) : masquée → déployée ; réduite → déployée ; déployée → masquée. **H** fait de même pour l'aide seule (§ 19.1, § 21.3)                                                                                                                                                                                                                                                                                                                              |
| **K** (v46)                             | affiche ou masque les **flèches à l'écran** (comme le bouton « Flèches (K) » et la case des Réglages ; choix retenu par le navigateur ; même place en AZERTY et en QWERTY, § 29.3)                                                                                                                                                                                                                                                                                                                                                                                  |
| **L** (v40)                             | la fenêtre **Arrivées** : liste des points de téléportation de la région ; un clic sur un nom y téléporte (en promenade) ou y fait entrer en promenade (en vue globale). Même cycle que **H** et **I** ; absente si la région n'a aucune arrivée                                                                                                                                                                                                                                                                                                                    |

Les portails ne fonctionnent qu'en promenade.

### Clic et double-clic (vue globale du viewer)

| Geste                         | Effet                                                                                                                                                                                                                                                   |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **clic simple** sur le modèle | affiche, dans le bloc « picked » et la barre d'état, le **nom de l'élément** et les **coordonnées du point touché** (x, y, z, 2 décimales). Rien ne bouge : ni la cible, ni le cercle d'atterrissage.                                                   |
| **double-clic** sur le modèle | choisit la **cible** de la vue et le **point d'atterrissage** (comme dans la page exportée). En mode tuiles (§ 17 bis), le double-clic fonctionne aussi sur la **vue d'ensemble** : la cible se place sur le point lointain et les tuiles s'y chargent. |

Deux cercles à ne pas confondre :

- le **petit cercle** (noir et blanc, posé sur le sol) est le **repère d'atterrissage** : il montre où l'avatar apparaîtra en appuyant sur F. Il suit la cible, donc il ne change qu'au double-clic ;
- le **grand cercle** (cylindre translucide avec son nom) est une **zone** : son rayon est celui de la fiche de la zone. **Il n'existe que dans le viewer** (voir § 2 bis).

## 2 bis. Ce que voit le visiteur : les liens se comportent comme sur le web

Dans le **viewer** (édition), chaque zone non liée garde son **cylindre translucide**, toujours visible, pour la repérer et la positionner (les panneaux aussi) ; une zone liée à un élément y est entourée d'un contour. Rien de tout cela n'est exporté.

Dans la **page exportée** (autonome ou modulaire), il n'y a **aucun cylindre** pour les zones lien web, commande Home Assistant et portail :

| Zone                  | Ce qui est ajouté dans la scène                                                                   | Au survol                                                                                                                  |
| --------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **liée à un élément** | **rien**                                                                                          | le curseur devient une **main**, l'élément reçoit un léger **contour**, une **infobulle** affiche le nom et la destination |
| **non liée**          | un **marqueur discret au sol** (petit disque plat de 0,4 m, semi-transparent, avec un anneau fin) | même chose : main, infobulle, le marqueur s'éclaircit                                                                      |

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

| Champ                | Réglage                                                                |
| -------------------- | ---------------------------------------------------------------------- |
| Identifiant          | le nom que les portails utiliseront (`empereur`, `temple`, `default`…) |
| Nom affiché          | libre                                                                  |
| Position X / Y / Z   | Y est la hauteur                                                       |
| Orientation (degrés) | la direction dans laquelle le visiteur regarde en arrivant             |

Pose-le en promenade avec **P**, en regardant dans la direction voulue : position et orientation sont prises d'un coup.

L'arrivée d'identifiant **`default`** est spéciale : c'est là qu'arrive un visiteur quand rien d'autre n'est précisé (portail sans point d'arrivée, arrivée demandée introuvable, venue depuis la carte sans réglage). Mets-en une dans chaque région.

**Arrivée `default` et ouverture sans lien (v33)** : si la région a une arrivée `default`, la page s'ouvre **cadrée sur elle** (la cible de la caméra devient sa position) et **F démarre à son point, avec son orientation** (tant que la cible n'a pas été déplacée, par exemple au double-clic). Une cible donnée explicitement sur la ligne de commande (`--target`) garde la priorité pour le cadrage : voir la règle exacte au § 18.2.

## 5. Portail vers un autre endroit de la même région

| Champ                           | Réglage                                             |
| ------------------------------- | --------------------------------------------------- |
| Page de destination             | **vide** (le nom de la page elle-même marche aussi) |
| Point d'arrivée dans cette page | l'**Identifiant** de l'arrivée visée                |
| Déclenchement                   | voir § 8                                            |

Effet : fondu au noir, puis le visiteur est posé sur l'arrivée, orienté comme elle. La page n'est pas rechargée : il reste connecté à la présence et au chat.

Si l'arrivée n'existe pas, un message « Point d'arrivée … introuvable dans cette région » s'affiche.

## 6. Portail vers une autre région

| Champ                           | Réglage                                                                                                                                                                                                                         |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Page de destination             | l'autre page : `autre-region.html` si elle est dans le même dossier, sinon son adresse complète `https://…/autre-region.html`. Avec une coquille commune (§ 16) : `index.html?region=AutreRegion` (le `#spawn=` s'ajoute après) |
| Point d'arrivée dans cette page | l'**Identifiant** d'une arrivée **de l'autre page** (vide = `default`)                                                                                                                                                          |

Effet : fondu, chargement de l'autre page, le visiteur y arrive directement en promenade, avec son pseudo.

À vérifier :

- l'autre page doit exister à cette adresse et avoir la promenade activée ;
- l'arrivée visée doit exister **dans l'autre page**, pas dans celle-ci ;
- seules les adresses `http`, `https` et les fichiers locaux sont acceptés.

## 7. Panneaux

### Lien web

| Champ       | Réglage     |
| ----------- | ----------- |
| Adresse web | `https://…` |

Approche-toi et appuie sur **E** (ou clique) : la page s'ouvre dans un nouvel onglet.

Formats acceptés pour l'adresse (aussi pour la page de destination d'un portail) :

| Format                  | Exemple                         | Remarque                                                                              |
| ----------------------- | ------------------------------- | ------------------------------------------------------------------------------------- |
| adresse web             | `https://monsite.fr/ile.html`   | marche partout                                                                        |
| fichier `.html` relatif | `autre-ile.html`                | relatif à la page qui contient la zone                                                |
| fichier local           | `file:///P:/web/autre-ile.html` | **sans guillemets** ; ne marche que si la page elle-même est ouverte depuis le disque |

Les espaces s'écrivent `%20` (`file:///P:/mes%20pages/ile.html`). Toute autre forme (`javascript:`, `ftp:`…) est refusée.

### Commande Home Assistant

| Champ                             | Réglage                                        |
| --------------------------------- | ---------------------------------------------- |
| Adresse du webhook Home Assistant | l'adresse du webhook de ton automatisation     |
| Demander confirmation             | coché : le visiteur doit valider avant l'envoi |

Effet : envoi d'une requête POST au webhook avec deux valeurs, `zone` (le nom affiché) et `visitor` (le pseudo). Une même commande ne peut pas repartir avant 3 s. La page ne reçoit pas la réponse de Home Assistant : « Commande envoyée » veut dire envoyée, pas exécutée.

## 8. Déclenchement, forme et taille

**Déclenchement** (portails) :

| Choix              | Effet                                                                  |
| ------------------ | ---------------------------------------------------------------------- |
| en marchant dedans | le portail part dès qu'on entre dans le cercle                         |
| au clic            | il faut cliquer dessus (v35 : la touche E ne déclenche plus les zones) |
| les deux           | l'un ou l'autre                                                        |

Un portail « en marchant dedans » sur lequel on arrive ne se déclenche pas tout de suite : il faut en sortir puis y rentrer. Deux portails qui se renvoient l'un vers l'autre ne font donc pas de ping-pong.

**Forme** :

| Choix         | Réglage de taille                                                 |
| ------------- | ----------------------------------------------------------------- |
| cercle au sol | Rayon (m)                                                         |
| panneau       | Largeur, Hauteur, et Portée d'approche pour l'invite « clic » (m) |

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

**Privé (absent de l'export public)** coché : la zone reste dans tes exports « private », mais disparaît des exports « public ». Le choix se fait dans **Profil d'export** :

- **private : toutes les zones** (appelé « perso » avant la v43)
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

| Ta page est…                            | Que faire après avoir modifié les zones                                                                         |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **autonome** (un seul .html)            | **Exporter HTML autonome**, puis remplacer l'ancienne page                                                      |
| **modulaire** (coquille + .glb + .json) | **Exporter zones (.json)**, renommer en `<nom de la page>.zones.json`, remplacer l'ancien, puis F5 dans la page |

Les zones peuvent aussi être sauvées et rechargées avec **Exporter zones (.json)** / **Importer zones (.json)**, par exemple pour les copier d'une région à l'autre.

**Après un changement de version** de glb2html (comme v21 → v22), les pages existantes gardent l'ancien comportement : il faut les régénérer. En modulaire, c'est la coquille `.html` qui change : régénère-la, un simple remplacement des `.json` ne suffit pas.

## 13. Dépannage

| Symptôme                                         | Cause probable                                                                                                        | Remède                                                                                                                                                                   |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Rien ne se passe en entrant dans un portail      | pas en promenade                                                                                                      | appuie sur P (ou F en vue globale)                                                                                                                                       |
|                                                  | déclenchement réglé « au clic »                                                                                       | clique sur le portail (v35 : E ne le déclenche plus), ou passe en « en marchant dedans »                                                                                 |
|                                                  | tu étais déjà dans le cercle en arrivant                                                                              | sors du cercle puis rentre                                                                                                                                               |
| « Point d'arrivée … introuvable »                | le portail contient le **Nom affiché** au lieu de l'**Identifiant**                                                   | recopie l'Identifiant exact de l'arrivée (§ 1)                                                                                                                           |
| Arrivée au mauvais endroit dans une autre région | l'arrivée visée n'existe pas dans l'**autre** page, ou elle est privée et la page est publique                        | crée-la dans l'autre page, ou décoche Privé                                                                                                                              |
| Écran noir après un portail interne              | page générée avant la v22                                                                                             | régénère la page                                                                                                                                                         |
| « Portail sans destination valide »              | adresse mal écrite, ou protocole non accepté                                                                          | `https://…` ou nom de fichier `.html`                                                                                                                                    |
| La zone marche dans le viewer, pas dans la page  | page pas republiée                                                                                                    | voir § 12                                                                                                                                                                |
| Commande HA « envoyée » mais rien ne bouge       | webhook faux, ou automatisation désactivée                                                                            | teste le webhook directement depuis Home Assistant                                                                                                                       |
| Une zone supprimée revient après rechargement    | le viewer restaure les réglages mémorisés pour ce fichier, ou l'ancien `.reglages.json` / `zones.json` a été rechargé | supprime-la (**Supprimer**), attends 2 s (mémorisation automatique), ou **Oublier les réglages de ce fichier** (§ 14) ; vérifie aussi `zones.json` / `<page>.zones.json` |
| La liaison prend un objet de 30 m                | (avant v23) l'objet est fusionné avec un bâtiment dans l'OAR ; la limite était de 30 m                                | v23 : limite de 10 m et message explicite ; délie l'objet dans OpenSim (Unlink) ou pose une zone cercle (§ 9)                                                            |
| Le cercle d'atterrissage « saute »               | (avant v23) chaque clic simple déplaçait la cible                                                                     | v23 : seul le **double-clic** le déplace ; le clic simple affiche nom et coordonnées                                                                                     |
| L'île est inversée nord-sud sur la carte         | l'OAR est exporté dans l'autre orientation                                                                            | **Rotation de la région** : 180° (§ 11), puis recapturer la vignette, mettre à jour la région dans la carte et réexporter `regions.json`                                 |

## 14. Réglages mémorisés

Le viewer mémorise **tout** (zones comprises, mais aussi trou, vagues, caméra, rotation, carte, fiche de région…) **par fichier `.glb`** dans le navigateur (clé : nom + taille du fichier). Il enregistre seul, environ toutes les 1,5 s après une modification. Au rechargement du même `.glb`, tout est restauré, et la barre d'état indique « Réglages restaurés depuis la mémoire du navigateur (N zone(s)) ».

Conséquences :

- une zone ajoutée ou supprimée est retrouvée telle quelle au rechargement ; pour **supprimer une zone**, ouvre sa fiche et clique sur **Supprimer** (attends 2 s avant de fermer l'onglet) ;
- la mémoire est propre au navigateur et à l'adresse de la page du viewer : un autre navigateur ou un autre ordinateur ne voit rien. Pour transporter les réglages : **Enregistrer dans un fichier** (`.reglages.json`) puis **Charger depuis un fichier**, ou `glb2html.py --settings` ;
- **Oublier les réglages de ce fichier** (section Réglages mémorisés) efface la mémoire de ce `.glb` : les valeurs actuelles restent à l'écran, mais ne sont plus protégées, et elles seront mémorisées de nouveau à la prochaine modification. Pour repartir de zéro : cliquer ce bouton puis recharger la page du viewer et rouvrir le `.glb`.

## 15. Convertir un OAR en GLB (`tools/oar2glb.py`)

`oar2glb.py` transforme une sauvegarde de région OpenSim (`.oar`) en un seul fichier `.glb` prêt pour le viewer et pour `glb2html.py`. Il lance convoar¹, répare sa sortie et assemble le tout. La sortie est écrite à côté de l'OAR : `X.oar` donne `X.glb`.

¹ **Prérequis** :  **oar2glb.py** s'appuie sur le convertisseur externe **convoar.exe**
  Téléchargement : https://github.com/Misterblue/convoar/tree/master/bin
  Sans convoar.exe, oar2glb.py ne peut pas effectuer la conversion OAR → GLB.

### Les commandes (PowerShell, une seule ligne)

Se placer d'abord dans le dossier du script : `cd "P:\_OpenSim\SL&OS\Web_3d"`.

| Besoin                                                                      | Commande                                                                                 |
| --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Conversion normale                                                          | `python oar2glb.py "J:\...\X.oar"`                                                       |
| Conversion qui garde les dossiers intermédiaires (nécessaire pour `--diag`) | `python oar2glb.py "J:\...\X.oar" --keep`                                                |
| Retrouver les animaux dans le viewer (mât rouge de 15 m à chacun)           | `python oar2glb.py "J:\...\X.oar" --keep --markers`                                      |
| Garder les prims invisibles                                                 | `python oar2glb.py "J:\...\X.oar" --keep-invisible`                                      |
| Vérifier ce que le script voit, sans rien modifier                          | `python oar2glb.py "J:\...\X.oar" --diag`                                                |
| Idem, en désignant le GLB ou le `.gltf` à comparer                          | `python oar2glb.py "J:\...\X.oar" --diag --glb "J:\...\X-GLTF\fichier.gltf"`             |
| Ne pas attendre « Entrée » à la fin                                         | ajouter `--nopause`                                                                      |
| Ajouter le terrain complet à un GLB existant, sans relancer convoar         | `python oar2glb.py "J:\...\X.oar" --terrain-only "J:\...\X.glb"` (écrit `X-terrain.glb`) |

Avant de refaire une conversion, supprimer l'ancien dossier intermédiaire : `Remove-Item -Recurse -Force "J:\...\X-GLTF*"`.

### Les options

| Option                    | Effet                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--keep`                  | garde le dossier `X-GLTF` (images, tampons, `.gltf`) ; indispensable pour lancer ensuite `--diag`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `--keep-invisible`        | garde les prims entièrement transparents (retirés par défaut)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `--markers`               | ajoute un mât rouge de 15 m à chaque animal riggé posé ; le nom du nœud donne l'animal et sa taille ; à retirer en relançant sans l'option                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `--diag`                  | ne modifie rien et ne lance pas convoar : liste chaque partie de l'OAR (voir plus bas)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `--glb CHEMIN`            | avec `--diag` : GLB ou `.gltf` à comparer ; par défaut le `.gltf` du dossier `X-GLTF`, sinon le `X.glb` voisin                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `--max N`                 | hauteur maximale (m) d'un objet racine ; au-delà (skybox) il est retiré ; défaut 600                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `--convoar CHEMIN`        | chemin de `convoar.exe` (défaut : variable `CONVOAR`, sinon `convoar` du PATH, sinon `convoar.exe` à côté de `oar2glb.py`) ; s'il est introuvable, le message donne l'adresse de téléchargement                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `--reencode`              | **à éviter** : réencode les textures avant convoar ; sur Jungle_Isle il faisait manquer environ 150 textures sur 353 (textures grises). À n'utiliser que si convoar affiche beaucoup d'erreurs « unhandled number of components » ou plante dans `OpenJPEG.DotNetDecode64` (code retour 3221225477). Les textures que Pillow ne sait pas lire sont remplacées par un gris 4x4 (liste dans `X-reenc-illisibles.txt`, à côté de l'OAR) pour ne pas les laisser au décodeur de convoar ; les sculpt maps restent intactes ; 8 cœurs au plus et envoi par lots de 512 pour limiter la mémoire |
| `--nopause`               | ne pas attendre « Entrée » à la fin (la pause est aussi supprimée quand il n'y a pas de console, et avec `--terrain-only`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `--terrain auto\|yes\|no` | terrain complet depuis la carte de hauteurs (voir plus bas) ; `auto` par défaut                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `--terrain-patch N`       | côté d'un patch de terrain en mètres, de 2 à 255 ; défaut 64                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `--terrain-only GLB`      | ne lance pas convoar : ajoute le terrain complet à ce GLB et écrit `X-terrain.glb` à côté (l'original n'est jamais modifié)                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `--output FICHIER`        | avec `--terrain-only` : fichier de sortie à la place de `X-terrain.glb` (jamais l'original)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |

### Terrain complet des régions de plus de 256 m (v29)

convoar ne produit qu'**un** nœud « Terrain » dont l'étendue plafonne (par exemple 257 x 267 m sur une région de 1 024 m : un seizième de la région n'a pas de sol). La carte de hauteurs complète est dans l'OAR (`terrains/*.r32`, un échantillon par mètre). `oar2glb.py` s'en sert pour construire le sol :

- **Patches.** Des carrés de P x P mètres (`--terrain-patch`, 64 par défaut), chacun un mesh de (P+1)² sommets. Les bords sont partagés entre voisins (mêmes hauteurs, mêmes normales, mêmes couleurs : pas de fissure, éclairage continu). Le dernier patch d'une rangée est plus petit quand n-1 n'est pas un multiple de P. Chaque patch est un objet racine nommé `Terrain i,j` (i : colonne vers l'est, j : rangée vers le nord). Repère monde : X = x, hauteur = h, Z = -y. Un seul matériau « terrain » (blanc, métal 0, rugosité 1, simple face), indices 16 bits, **pas de coordonnées de texture** : l'aspect vient de la couleur par sommet (`COLOR_0`).
- **Normales** par différences centrées sur toute la carte (une seule différence aux bords de la carte).
- **Couleur par sommet** d'après l'altitude `a` au-dessus du niveau d'eau et la pente :

| Situation               | Couleur (rouge, vert, bleu)                                                           |
| ----------------------- | ------------------------------------------------------------------------------------- |
| `a` ≤ 0 (sous l'eau)    | sable humide (166, 150, 104)                                                          |
| 0 < `a` ≤ 1 m           | sable sec (214, 196, 142)                                                             |
| 1 à 4 m                 | passage progressif du sable sec à l'herbe                                             |
| `a` ≥ 4 m               | herbe, dégradé léger de (98, 146, 66) à `a` = 4 m vers (132, 140, 78) à `a` = 80 m    |
| pente de 32 à 38 degrés | passage progressif vers la roche grise (122, 120, 116) ; au-delà de 38 degrés : roche |

- **Niveau d'eau.** `WaterHeight` lu dans `settings/*.xml` de l'OAR, sinon 20 m (défaut d'OpenSim). Le journal dit quelle valeur est utilisée et d'où elle vient.
- **Quand remplacer.** `--terrain auto` (défaut) : si le nœud « Terrain » de convoar existe et couvre moins de 95 % de la carte (boîtes comparées en repère monde), il est retiré de la scène et les patches sont ajoutés. Sinon (région de 256 m, terrain déjà complet, pas de nœud « Terrain ») le GLB n'est **pas modifié** : il est identique à celui de `--terrain no`. `--terrain yes` ajoute toujours les patches (et retire le « Terrain » de convoar s'il existe) ; `--terrain no` ne fait rien. Un GLB qui contient déjà des patches n'en reçoit pas d'autres. Le filtre des objets hors région ne retire jamais les patches.
- **`--terrain-only GLB`** (sans relancer convoar, pour un GLB de plusieurs Go) : le GLB n'est **pas chargé en entier**. L'en-tête JSON est réécrit, le chunk binaire est recopié par morceaux de 8 Mo, les nouveaux tampons sont ajoutés à la fin. Sortie `X-terrain.glb` à côté de l'original (ou `--output`) ; l'original n'est jamais écrasé, et rien n'est écrit si le terrain de convoar est déjà complet. Les données de l'ancien « Terrain » restent dans le fichier, inutilisées (quelques Mo). Aucune pause « Entrée » à la fin.
- **Journal.** Ligne `[terrain] carte N x N échantillons (1 m) ; niveau d'eau E m (origine) ; K patch(es) de P m ; V sommets ; B Mo ajoutés ; durée`. Un OAR sans carte de hauteurs donne `cet OAR n'a pas de carte de hauteurs ... rien n'est modifié` (code de retour 0, aucune erreur).
- **Hors lot** : textures de terrain d'OpenSim (les quatre textures mélangées selon l'altitude), niveau de détail du terrain pour la vue d'ensemble.

Test : `python tests/terrain.py` (OAR et GLB synthétiques).

### Ce que le script corrige

- **Animaux riggés (animesh).** La géométrie que convoar écrit pour ces meshes est inutilisable (hippopotames géants, éléphants minuscules ou envolés, formes partagées entre animaux). Le script la reconstruit depuis le fichier `.llmesh` de l'OAR : positions, normales, UV, triangles, puis `bind_shape_matrix` ; l'échelle du prim est ignorée. Les morceaux d'un même animal restent ensemble. L'animal est centré sur la position de la racine de l'objet et ses pieds sont posés sous la boîte racine (à l'altitude de la racine si elle est elle-même riggée). Les textures viennent de convoar (face n du mesh = matériau n). Aucune règle ne dépend du nom d'un animal. Un animal dont la taille calculée sort de 0,1 à 12 m reste tel que convoar l'a produit (le journal le dit).
- **Prims invisibles.** Sont retirés : les prims dont toutes les faces sont à alpha 0 ou portent une texture invisible standard, les nœuds dont tous les matériaux sont transparents, et la boîte racine d'un animesh (prim simple, racine d'un objet dont tous les autres morceaux sont des meshes riggés). Les enfants d'une racine retirée restent.
- **Textures.** Le script compare les images annoncées par le `.gltf` aux fichiers présents ; s'il en manque, il relance convoar (2 essais de plus au maximum) en gardant les images déjà écrites.
- **Positions des régions plus grandes que 256 m** et objets hors région : traitement inchangé. Le terrain de ces régions est complété par les patches (voir « Terrain complet »).

### Lire le journal (`oar2glb.log`, à côté du script)

| Ligne                                                                                 | Sens                                                                                                        |
| ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `[riggé] 'Nom' reconstruit depuis l'OAR : N face(s), M sommets...`                    | un morceau d'animal a été reconstruit ; les chiffres « convoar » à côté montrent ce que convoar avait écrit |
| `[riggé] 'Nom' : 5 morceau(x)... pieds à 27.11 m (dessous de la boîte racine)`        | animal posé ; taille L x l x h et altitude des pieds                                                        |
| `[riggé] ... nœud GLB introuvable`                                                    | le morceau n'a pas été retrouvé dans le GLB ; lancer `--diag`                                               |
| `[riggé] ... taille obtenue ... implausible`                                          | garde-fou : l'animal est laissé tel que convoar l'a produit                                                 |
| `[invisible] node N 'Nom' retiré : ...`                                               | prim retiré, avec la raison                                                                                 |
| `[correctif] N mesh(es) riggé(s) remis à l'échelle, M prim(s) invisible(s) retiré(s)` | récapitulatif                                                                                               |
| `[contrôle] 'Nom' pieds à ... : dans la boîte de N objet(s)`                          | objets dont la boîte englobante contient le centre de l'animal (indice si un animal est dans un rocher)     |
| `[GLB] N texture(s) absente(s) sur M`                                                 | images manquantes, remplacées par du gris                                                                   |
| `[terrain] ...`                                                                       | décision (couverture du terrain de convoar) puis résumé des patches ajoutés                                 |
| `[OK] ...glb (taille, meshes, textures)`                                              | fin normale                                                                                                 |

### Diagnostic : `--diag`

À lancer après une conversion faite avec `--keep`. Le journal est `oar2glb.diag.log`. Chaque partie de l'OAR donne une ligne : nom, UUID, racine ou enfant, riggé oui/non, échelle du prim, échelle de `bind_shape_matrix`, transparent oui/non, boîte racine d'animesh oui/non, et le nœud GLB trouvé avec la méthode (UUID du prim, UUID du mesh, nom + position). Les animaux et prims invisibles affichent en plus le résumé du `TextureEntry`, la matrice complète, le domaine de position et le matériau GLB. Une ligne « nœud introuvable » sur un animal ou un prim transparent signifie que le correctif ne s'appliquera pas à lui.

### Si quelque chose ne va pas

| Symptôme                                    | Cause probable                                                       | Remède                                                                          |
| ------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Beaucoup de textures grises                 | `--reencode`, ou images non écrites par convoar                      | relancer sans `--reencode` ; lire `[GLB] N texture(s) absente(s)`               |
| Un animal invisible ou à la mauvaise place  | nœud non retrouvé, ou animal caché                                   | `--keep --markers`, puis `--diag` ; envoyer `oar2glb.log` et `oar2glb.diag.log` |
| Un animal avec la mauvaise texture          | l'ordre des faces du mesh ne suit pas celui des matériaux de convoar | signaler l'animal avec son journal                                              |
| Des prims transparents qu'on voulait garder | retirés par défaut                                                   | `--keep-invisible`                                                              |
| « convoar introuvable »                     | chemin différent                                                     | `--convoar "P:\...\convoar.exe"`                                                |

`python oar2glb.py --version` affiche la version (`oar2glb v29 (22/10/2026)`) sans rien lancer ; la première ligne du journal (`oar2glb.log`, `oar2glb.diag.log`) la rappelle : `[oar2glb] v29 (22/10/2026)`. Joindre ce journal à tout signalement donne donc la version utilisée. Le fichier est fabriqué dans `dist/` par `python build.py`.

Test du script : `python tests/oar2glb.py` (OAR synthétique et faux convoar, sans réseau).

## 16. Fichiers JSON d'une région modulaire

Pour une page `Region.html` produite par `--modular` (ou par « Exporter la structure modulaire (.zip) » du viewer), le dossier contient :

Ces fichiers sont ceux d'une région à coquille propre (`--modular`). Pour plusieurs régions dans un même dossier avec **une seule** coquille, voir « Coquille unique pour plusieurs régions » plus bas.

| Fichier              | Rôle                                                                                    | Relu à chaque F5 |
| -------------------- | --------------------------------------------------------------------------------------- | ---------------- |
| `Region.html`        | coquille identique pour toutes les régions, elle déduit ses fichiers de son nom         | non              |
| `Region.glb`         | le modèle                                                                               | non              |
| `Region.config.json` | réglages de **rendu de la page** (voir plus bas)                                        | oui              |
| `Region.zones.json`  | zones, portails, arrivées                                                               | oui              |
| `zones.json`         | zones de secours, communes aux pages du dossier qui n'ont pas leur propre `.zones.json` | oui              |
| `lib/three-0.160.0/` | three.js, Draco, Meshopt, partagés par toutes les pages du dossier                      | non              |

### Coquille unique pour plusieurs régions (`--shared-shell`, v26)

Une seule coquille (par défaut `index.html`) sert toutes les régions d'un même dossier, avec un seul `lib/`. Chaque région n'ajoute que trois fichiers. La région s'ouvre à **`index.html?region=NOM`**, où NOM est le nom des fichiers sans extension (`?region=NOM.html` est accepté : l'extension est retirée).

```
dossier/
  index.html            la coquille, identique pour toutes les régions
  lib/three-0.160.0/    partagé
  Ankh.glb   Ankh.config.json   Ankh.zones.json
  Jungle.glb Jungle.config.json Jungle.zones.json
```

| Besoin                         | Commande (PowerShell, une seule ligne)                                                                                                                                 |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Générer une région             | `python glb2html.py "Ankh.glb" --settings --shared-shell --register regions.json -o "Ankh.html"`                                                                       |
| Autre nom de coquille          | `--shared-shell monde.html` (adresse `monde.html?region=Ankh`)                                                                                                         |
| Changer un réglage             | `python glb2html.py --settings "Ankh.glb" --config-only --shared-shell --wave 2 -o "Ankh.html"`                                                                        |
| Changer les zones seules       | `python glb2html.py -o "Ankh.html" --zones-only --zones zones.json`                                                                                                    |
| Mettre à jour une région (v34) | `python glb2html.py --update -o "Ankh.html" --shared-shell --sea-y 12` : applique **seulement** les options données, garde le reste de la config et les zones (§ 19.6) |

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

Les zones marquées **privées** sont retirées à la lecture, dans l'un comme dans l'autre fichier, sauf si `profile` vaut `private` dans `Region.config.json`.

### Region.config.json : le rendu de la page, pas le viewer

C'est le dictionnaire de réglages que la page lit au démarrage (le même que celui intégré dans une page autonome). Il est **à plat**. La liste complète de ses champs, avec leur type, leur valeur par défaut, leur rôle et l'option qui les règle, est au **§ 27.3** ; un exemple complet est dans `docs/samples/region.config.sample.json`.

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

|              | `<nom>.reglages.json` (viewer)                 | `<page>.config.json` (page)              |
| ------------ | ---------------------------------------------- | ---------------------------------------- |
| Structure    | imbriquée (`cfg`, `camera`, ...)               | à plat                                   |
| Caméra       | sous-objet `camera`                            | à la racine (`camDir`, `target`, `zoom`) |
| Zones        | toutes, privées comprises                      | toujours vide                            |
| Carte        | seulement la fiche de cette région (`thisReg`) | carte complète résolue (`map`)           |
| Propre à lui | `guide`, `ignoreViz`, `cmd`, `thisReg`         | `seaSize`, `version`                     |
| Écrit par    | le viewer                                      | `glb2html.py`                            |
| Lu par       | le viewer, `glb2html.py --settings`            | la page exportée                         |

La conversion ne va que dans un sens :

```
<nom>.reglages.json  ->  glb2html.py --settings  ->  <page>.config.json + <page>.zones.json
```

Un `.config.json` ne peut pas être donné à `--settings` (le script cherche la clé `cfg` et refuse le fichier), ni rechargé dans le viewer (« fichier de réglages non reconnu »). Pour garder ses réglages, il faut donc conserver le `.reglages.json` : le `.config.json` n'en est qu'un produit dérivé.

### Quel fichier modifier, et ce qui l'écrase

| Je veux changer...                    | Je modifie / je lance                                                | Ce qui peut l'écraser ensuite                                               |
| ------------------------------------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| un réglage de rendu (vagues, ciel...) | `--config-only` (voir ci-dessous), ou `Region.config.json` à la main | tout nouveau `--modular` ou `--config-only` réécrit `Region.config.json`    |
| une zone                              | `Region.zones.json` à la main, ou **Exporter zones (.json)** (§ 12)  | `--modular` avec `--zones` ou `--settings` ; `--config-only` avec `--zones` |
| l'état de travail du viewer           | **Enregistrer dans un fichier**                                      | rien (c'est la source)                                                      |

Sans `--zones` ni `--settings`, un `Region.zones.json` déjà présent (modifié à la main, par exemple) n'est pas écrasé. Dès qu'une source de zones est donnée, il est réécrit.

Changer un réglage sans toucher au `.glb`, à la coquille ni aux zones :

```
python glb2html.py --settings "Region-final.glb" --config-only --wave 2 -o "Region.html"
```

Les options de la ligne de commande l'emportent sur le `.reglages.json`. Les visiteurs voient le changement à leur prochain rechargement.

## 17. Découper un GLB énorme en tuiles (`tools/glb2tiles.py`, v28 ; `--exclude` et pause en v29 ; images invalides et vue d'ensemble en v31)

`glb2tiles.py` découpe un GLB trop lourd en **tuiles autonomes** : chacune est un GLB valide (ouvrable seul dans `glb-viewer.html`), avec ses propres nœuds, meshes, matériaux et images, aux coordonnées d'origine (aucun recentrage). Cet outil **écrit les tuiles, leur liste et (v31) une vue d'ensemble légère de toute la région** ; c'est la coquille qui les charge autour de l'avatar (v30, voir § 17 bis). Python standard seulement. Le GLB d'entrée n'est jamais chargé en entier : l'en-tête JSON est lu, puis les indices, positions et images par morceaux.

`glb-stats.py` doit rester **à côté** de `glb2tiles.py` (fonctions de mesure communes) ; `python build.py` met les deux dans `dist/`.

### Les commandes (PowerShell, une seule ligne)

| Pour                                                        | Commande                                                                                                                                                      |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Voir la version                                             | `python glb2tiles.py --version`                                                                                                                               |
| Mesurer et obtenir une recommandation, sans rien écrire     | `python glb2tiles.py "P:\...\Region.glb" --analyse`                                                                                                           |
| Découper (recommandation « découper »)                      | `python glb2tiles.py "P:\...\Region.glb"`                                                                                                                     |
| Découper même si la recommandation est « pas de découpage » | `python glb2tiles.py "P:\...\Region.glb" --force`                                                                                                             |
| Écrire ailleurs qu'à côté du GLB                            | `python glb2tiles.py "P:\...\Region.glb" --output "P:\...\tuiles"`                                                                                            |
| Découper sans la vue d'ensemble                             | `python glb2tiles.py "P:\...\Region.glb" --no-overview`                                                                                                       |
| Refaire **seulement** la vue d'ensemble (tuiles intactes)   | `python glb2tiles.py "P:\...\Region.glb" --overview-only` avec **les mêmes options de découpage** (`--output`, `--budget`, `--exclude`…) que la première fois |
| Écarter les « boîtes de livraison » d'un fournisseur        | `python glb2tiles.py "P:\...\Region.glb" --analyse --exclude "Freebies 20"` puis la même commande sans `--analyse`                                            |

Commencer par `--analyse` : elle donne les mesures de `glb-stats.py`, les 10 meshes les plus lourds (octets compactés, étendue en mètres), les 10 instances les plus éloignées du centre médian (valeurs aberrantes), le nombre de tuiles prévu avec les paramètres choisis, le facteur de duplication prévu, le nombre d'objets racine gardés entiers ou répartis, et une phrase de recommandation : « pas de découpage nécessaire » ou « découper : budget N Mo, T tuiles, duplication F ». Un GLB léger répond « pas de découpage nécessaire » et rien n'est écrit (même sans `--analyse`, sauf avec `--force`).

### Les paramètres

| Option                                 | Défaut        | Sens                                                                                                                                                                                                               |
| -------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `--budget`                             | 32            | Mo par tuile (poids autonome : primitives distinctes compactées + images distinctes)                                                                                                                               |
| `--budget-triangles`                   | 1500000       | triangles par tuile (le poids en Mo ne suffit pas : un bloc peut avoir 5 M de triangles pour 70 Mo)                                                                                                                |
| `--min`                                | 16            | côté minimal d'une cellule, en m : on ne subdivise plus en dessous                                                                                                                                                 |
| `--whole-weight`                       | 16            | Mo : un objet racine plus léger que cela peut rester entier                                                                                                                                                        |
| `--whole-extent`                       | 256           | m : …et plus petit que cela (les deux conditions ensemble ; l'étendue seule ne décide pas)                                                                                                                         |
| `--threshold`, `--threshold-triangles` | 150, 3000000  | sous ces deux valeurs : « pas de découpage nécessaire »                                                                                                                                                            |
| `--outlier`                            | 1000          | m : une instance plus loin que cela du centre médian, ou plus grande, est signalée                                                                                                                                 |
| `--block`                              | 256           | côté des blocs de la partie `glb-stats` de `--analyse`                                                                                                                                                             |
| `--output`                             | à côté du GLB | dossier de sortie                                                                                                                                                                                                  |
| `--force`                              |               | découper même sous les seuils                                                                                                                                                                                      |
| `--exclude REGEX`                      |               | retire du découpage les objets racine dont le nom correspond (insensible à la casse, répétable ; voir ci-dessous)                                                                                                  |
| `--exclude-max-triangles`              | 24            | triangles au plus dans l'objet racine, tous meshes compris, pour être exclu                                                                                                                                        |
| `--exclude-max-meshes`                 | 1             | meshes au plus dans l'objet racine pour être exclu                                                                                                                                                                 |
| `--no-refs`                            |               | ne pas écrire `extras.ref` / `extras.box` dans les nœuds des tuiles (format de la v31 : zones liées à un objet impossibles en mode tuiles)                                                                         |
| `--no-overview`                        |               | ne pas écrire `X.overview.glb`                                                                                                                                                                                     |
| `--overview-only`                      |               | n'écrire que `X.overview.glb` et sa mention dans `X.tiles.json` ; le découpage recalculé doit retrouver exactement les tuiles de `X.tiles.json` (sinon : erreur « ne correspond pas », utiliser les mêmes options) |
| `--ov-budget`, `--ov-budget-triangles` | 25, 1500000   | Mo et triangles de toute la vue d'ensemble                                                                                                                                                                         |
| `--ov-threshold`                       | 3             | m : les objets dont la plus grande dimension est plus petite sont omis (le budget peut relever ce seuil)                                                                                                           |
| `--ov-threshold-max`                   | 24            | m : si le budget oblige à omettre des objets plus grands que cela, la résolution baisse                                                                                                                            |
| `--ov-resolution`                      | 10            | cellules sur la plus grande dimension d'une primitive pour le regroupement de sommets (plus grand = plus fin et plus lourd)                                                                                        |
| `--ov-terrain-step`                    | 4             | m : pas du réseau du terrain dans la vue d'ensemble                                                                                                                                                                |
| `--nopause`                            |               | ne pas attendre Entrée à la fin (la pause est aussi supprimée quand il n'y a pas de console : script, tâche planifiée)                                                                                             |

### Exclure des objets (`--exclude`, v29)

Certains catalogues posent à côté de chaque bâtiment une « boîte de livraison » (cube texturé de 12 triangles, un seul mesh) dont le nom se termine par celui du fournisseur, par exemple « City Stores - Box - RAKis Freebies 2019 ». `--exclude "Freebies"` les retire, **à condition** que l'objet racine ait aussi au plus `--exclude-max-triangles` triangles (tous meshes compris) **et** au plus `--exclude-max-meshes` meshes. Sans ces garde-fous le nom du fournisseur retirerait aussi de vrais bâtiments (« Jewel Box House V17 with Stairs - RAKis Freebies 2 » : 143 meshes, conservé). La décision ne dépend **jamais de l'étendue** : la boîte englobante d'un petit mesh qui partage un tampon de sommets avec d'autres est gonflée, jusqu'à plusieurs dizaines de mètres pour un cube de 12 triangles.

- Plusieurs `--exclude` s'additionnent. Une expression invalide donne un message clair (`Expression régulière invalide pour --exclude`) et rien n'est lu.
- Les nœuds retirés sont l'objet racine et tous ses descendants ; aucun autre objet ne change. Les exclus n'entrent ni dans les tuiles ni dans les calculs de poids, de triangles et de budget (la recommandation « pas de découpage » retire aussi leurs octets de la taille du GLB). Le GLB d'origine n'est pas modifié ; la partie `glb-stats` de `--analyse` décrit le fichier d'origine.
- `--analyse` et le rapport final donnent : le nombre d'objets exclus, les triangles retirés, les octets gagnés (géométrie et images qu'aucun objet conservé n'utilise ; **0** quand tous les exclus partagent leurs primitives ou leurs images avec des objets conservés, par exemple un cube commun : le rapport le dit alors, et chiffre les octets partagés non gagnés), le nombre d'objets au nom correspondant mais conservés par les garde-fous, et les 20 noms les plus fréquents avec leur nombre. `X.tiles.json` reçoit une clé `excluded` (motifs, garde-fous, `count`, `triangles`, `bytesSaved`, `bytesShared`, `names`) seulement quand `--exclude` est utilisé.

### Références d'objets (v32) : lier une zone à un objet en mode tuiles

Chaque nœud copié dans une tuile reçoit dans ses `extras` : **`ref`**, sa référence stable dans le modèle d'origine, et **`box`**, la boîte (monde, 6 nombres en m) de **l'objet entier**, même quand il est réparti sur plusieurs tuiles (chaque morceau porte la même boîte). `X.tiles.json` porte `"nodeRefs": 1`.

- **Règle de la référence** (celle de `nom#index` du mode GLB unique, calculée sur le GLB entier) : le **nom** du nœud (à défaut le nom de son mesh) s'il est unique dans tout le modèle ; sinon **`nom#index`**, index = rang du nœud parmi les nœuds de ce nom, dans l'ordre de parcours (pré-ordre, enfants dans l'ordre du fichier). Les objets retirés par `--exclude` comptent dans les rangs (une référence ne change pas quand on exclut autre chose). Un nœud sans nom n'a pas de référence ; une référence de plus de 200 caractères n'est pas écrite.
- Ces références sont celles des **noms du GLB**, pas celles que verrait le viewer en ouvrant le même GLB entier (le chargeur de three.js renomme les doublons) : une zone liée écrite en mode tuiles s'utilise en mode tuiles.
- **Coût mesuré** (GLB synthétique de 40 000 nœuds) : +0,5 s sur 8 s, +3 Mo sur 230 Mo de tuiles.
- Des tuiles écrites **avant la v32** n'ont pas ces extras : les zones liées y restent ignorées. `glb2tiles.py --analyse` (et `--overview-only`) le signalent quand `X.tiles.json` existe déjà sans `nodeRefs` ; `glb2html.py --tiles` aussi, s'il y a des zones liées. Il faut **refaire le découpage** (sans `--overview-only`).

### Images vides ou invalides (v31)

Une image embarquée **de 0 octet**, d'un **autre format** que PNG, JPEG ou WebP, ou **tronquée** fait échouer le chargement de la tuile dans le navigateur (« THREE.GLTFLoader: Couldn't load texture ») : mesuré dans Chromium, `createImageBitmap` échoue aussi sur un PNG, un JPEG ou un WebP coupé, pas seulement sur une image vide. Sur la région « Free House Gallery 4X4 », 778 images sur 19 799 étaient dans ce cas (toutes avec un `bufferView` de `byteLength` 0).

- À l'écriture, chaque image de ce genre est remplacée par **un PNG gris de 4 x 4 pixels** (gris 128, celui des textures remplacées par `oar2glb.py`), **écrit une seule fois par tuile** et partagé par toutes les références de cette tuile (nom `image-remplacee`). Les matériaux, les textures et les coordonnées de texture ne changent pas.
- Vérification sans décoder : PNG = blocs chaînés jusqu'à `IEND` ; JPEG = marqueur de fin `FFD9` en dernier (aux zéros et espaces de bourrage près) ; WebP = taille RIFF contenue dans le fichier. Seuls l'en-tête, la fin et les en-têtes de blocs sont lus (jamais l'image entière). Un fichier qui serait décodé par Chromium malgré une fin inhabituelle serait remplacé à tort : le nombre rapporté permet de s'en apercevoir.
- `--analyse` et le rapport final donnent « Images vides ou invalides remplacées… : N distincte(s), M occurrence(s) » (une occurrence = une image écrite dans une tuile). `X.tiles.json` reçoit `"replacedImages": {"distinct": N, "occurrences": M, "grey": 128}` et chaque tuile son propre nombre.

### Vue d'ensemble (`X.overview.glb`, v31)

But : en vue globale, voir **toute** la région ; en promenade, voir **au loin** au-delà des tuiles chargées. Les tuiles détaillées restent la seule source des collisions et du sol.

- **Écrite avec les tuiles** (ou seule avec `--overview-only`), à côté de `X.tiles.json`, et référencée dans `X.tiles.json` (clé `overview` : `file`, `bytes`, `triangles`, `terrainTriangles`, `objects`, `candidates`, `omitted`, `effectiveMinExtent`, `effectiveTerrainStep`, `resolution`, `seconds`, `colors`, `params`).
- **Un nœud par fichier de tuile**, nommé comme la tuile (`X.tiles/T_3_2_5.glb`, et `extras.tile`) : la page masque la cellule dès que la tuile détaillée est **affichée** et la réaffiche quand la tuile est déchargée ou en échec. Les objets d'une cellule sont exactement ceux de la tuile : pas de double affichage, pas de trou pendant le chargement.
- **Aucune image.** Un seul matériau ; les couleurs sont des **couleurs de sommets**. Chaque matériau devient une couleur unie : la **couleur moyenne de sa texture** si Pillow est installé (moyenne en espace linéaire, pondérée par l'opacité), sinon sa **couleur de base**. Les couleurs de sommets du terrain sont conservées. Sans normales : la page affiche la vue d'ensemble en ombrage plat. Les primitives translucides (`alphaMode` BLEND : verre, effets) et les objets à squelette sont omis.
- **Chaque primitive UNIQUE est simplifiée une seule fois**, puis recopiée avec la matrice de chacune de ses instances (jamais simplifiée par instance). Méthode : regroupement de sommets sur une grille de côté (plus grande dimension de la primitive) / `--ov-resolution` ; un sommet par cellule (moyenne), triangles dégénérés et doublons retirés. Python standard seulement ; Pillow est facultatif (couleurs moyennes).
- **Terrain simplifié à part.** Les pièces marquées `extras.terrain` (patches d'`oar2glb.py`) sont rééchantillonnées sur un **réseau régulier commun** de pas `--ov-terrain-step` : hauteur et couleur interpolées dans les triangles d'origine, une case appartient à une seule pièce (donc à une seule tuile). Un point du réseau sur un bord commun reçoit la même hauteur des deux côtés : **aucune fente entre les patches** (testé). Le terrain prend au plus la moitié des budgets ; sinon son pas grossit (× 1,5) jusqu'à ce qu'il tienne (dit dans le journal).
- **Objets omis.** Ceux dont la plus grande dimension est sous `--ov-threshold` (3 m par défaut : à 600 m, distance à laquelle la vue d'ensemble fait l'essentiel de l'image, 3 m couvrent environ 8 pixels sur un écran de 1 080 pixels de haut avec le champ de vision de 38 degrés ; à 210 m, limite du rayon de chargement, 22 pixels). Ce choix vient d'un calcul de taille à l'écran, **pas d'une mesure sur ta région** : `--analyse` imprime le nombre d'instances et de triangles au-dessus de 1, 2, 3, 4, 8, 16, 32 et 64 m pour décider sur tes données. Si le budget est atteint, les **plus grands objets sont gardés d'abord** et le seuil effectif monte (`effectiveMinExtent`) ; au-delà de `--ov-threshold-max` la résolution baisse et le calcul est refait.
- **Budgets** : 25 Mo et 1 500 000 triangles pour toute la région (`--ov-budget`, `--ov-budget-triangles`). Le rapport donne le poids, les triangles (dont le terrain), les objets gardés sur candidats, les objets omis (trop petits / par le budget / à squelette), les primitives translucides omises, les couleurs (moyennes de texture, illisibles, Pillow absent) et le temps.
- **Le GLB n'est jamais chargé en entier** (même lecture par morceaux de 4 Mo au plus que pour les tuiles), avec une progression (« [vue d'ensemble : primitives] … ») ; les pièces de terrain sont lues une à une.
- **Durée.** Débit mesuré sur des GLB synthétiques de taille croissante (0,5 ; 2 ; 8 ; 24 millions de triangles uniques) : environ 1,8 million de triangles uniques par seconde, linéaire (0,3 ; 1,2 ; 4,5 ; 13 s), soit 14 à 680 Mo de GLB pour 25 à 164 Mo de mémoire ; 20 000 petits meshes (4 millions de triangles, 40 000 instances) : 15 s, 377 Mo ; terrain de 1 024 m en 256 patches de 4 225 sommets : 3,6 s, 57 Mo. L'estimation pour la région de 1,3 Go est donnée dans `CHANGELOG.md` (v31).

### Comment le découpage se décide

- Quadtree adaptatif sur le plan X,Z (Y est la hauteur), uniquement sur les cellules non vides. Une cellule est subdivisée tant que son poids autonome dépasse `--budget` **ou** ses triangles dépassent `--budget-triangles`, et que son côté dépasse `--min`.
- Un **objet racine** (nœud de premier niveau de la scène) reste **entier**, dans la cellule du centre de sa boîte, si son poids autonome ≤ `--whole-weight` **et** son étendue ≤ `--whole-extent`. Sinon il est **réparti instance par instance** : chaque instance va dans la cellule de son propre centre, et les nœuds parents sont recopiés (sans mesh) avec leurs transformations d'origine.
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
 "params": {"budgetMB": 32, "budgetTriangles": 1500000, "minCell": 16, "wholeWeightMB": 16, "wholeExtent": 256,
            "thresholdMB": 150, "thresholdTriangles": 3000000, "outlier": 1000},
 "warnings": ["..."],               tuiles hors budget, valeurs aberrantes, extensions non recopiées
 "roots": {"whole": 1700, "split": 125},         objets racine gardés entiers / répartis
 "duplication": 1.8,                somme des octets de géométrie des tuiles / géométrie unique du GLB
 "nodeRefs": 1,                     extras.ref / extras.box dans les nœuds des tuiles (v32 ; 0 avec --no-refs)
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

Relancer réécrit les `T_*_*_*.glb` du dossier `X.tiles/` ; **ensuite** (v31), les `T_*_*_*.glb` d'une exécution précédente qui ne figurent plus dans le nouvel index sont **supprimés** et le rapport en donne le nombre (les autres fichiers du dossier ne sont pas touchés). `--overview-only` ne touche à aucune tuile.

### Lire le journal (`glb2tiles.log`, à côté du script)

Première ligne : `[glb2tiles] v31 (22/10/2026)`. L'avancement est écrit toutes les 5 % ou 10 s. Le rapport final donne : nombre de tuiles, médiane / 90 % / maximum du poids et des triangles, duplication réelle, nombre de racines entières et réparties, avertissements, temps total. `python glb2tiles.py --version` affiche la version sans journal ni pause.

Dans `--analyse`, la ligne « Lecture » indique les octets lus. Les positions ne sont lues que pour les primitives qui n'utilisent qu'une partie d'un tampon de sommets partagé (la boîte de l'accessor serait trop grande) ; les autres boîtes viennent de l'en-tête.

### Si quelque chose ne va pas

| Symptôme                                                                     | Cause probable                                                                                        | Que faire                                                                                                            |
| ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| « GLB compressé »                                                            | le GLB utilise Draco ou meshopt                                                                       | décompresser le GLB d'abord (hors de ce lot)                                                                         |
| « glb-stats.py introuvable »                                                 | le script est seul dans son dossier                                                                   | copier `glb-stats.py` à côté                                                                                         |
| « Tuile … hors budget »                                                      | un mesh unique (terrain, mer) dépasse le budget, ou la cellule minimale est atteinte                  | normal à ce stade : voir la feuille de route (découpage par triangles)                                               |
| Beaucoup de tuiles pour un petit GLB                                         | `--budget` trop petit ou duplication forte                                                            | relancer `--analyse` avec d'autres valeurs                                                                           |
| « THREE.GLTFLoader: Couldn't load texture » sur une tuile faite avant la v31 | image de 0 octet ou tronquée dans le GLB                                                              | refaire le découpage avec la v31 (images remplacées par un gris)                                                     |
| « Le découpage recalculé … ne correspond pas à X.tiles.json »                | `--overview-only` lancé avec d'autres options de découpage                                            | reprendre exactement les options du découpage d'origine                                                              |
| « Pillow absent » dans le rapport                                            | la vue d'ensemble utilise la couleur de base des matériaux (souvent blanche pour un matériau texturé) | `pip install pillow` puis `--overview-only`                                                                          |
| Vue d'ensemble trop lourde ou objets manquants                               | budget atteint, `effectiveMinExtent` monté                                                            | `--ov-budget` / `--ov-budget-triangles` plus grands, ou `--ov-threshold` plus haut ; lire les lignes « objets omis » |
| Instance à 3 000 m signalée                                                  | un prim géant ou un objet égaré                                                                       | l'outil la garde ; la corriger dans le modèle si c'est une erreur                                                    |

Test : `python tests/glb2tiles.py` (GLB synthétiques, sans navigateur ni réseau) ; `python tests/v31.py` (images invalides, vue d'ensemble, sortie de promenade).

## 17 bis. Charger une région en tuiles dans la page (`glb2html.py --tiles`, v30)

Une région de plusieurs centaines de Mo ou de plusieurs Go ne tient pas dans un navigateur : après `glb2tiles.py` (§ 17), la **coquille** charge seulement les tuiles proches de l'avatar et décharge les lointaines, et (v31) affiche au loin la **vue d'ensemble légère** `X.overview.glb` quand elle existe. Sans le champ `tiles` dans `X.config.json`, la page se comporte exactement comme avant (un seul `X.glb`).

### Les commandes (PowerShell, une seule ligne)

| Pour                          | Commande                                                                                                               |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Découper                      | `python glb2tiles.py "P:\regions\4X4.glb" --exclude "Freebies"` (écrit `4X4.tiles.json` et `4X4.tiles\` à côté du GLB) |
| Mettre la région dans le site | `python glb2html.py --shared-shell -o "P:\site\4X4.html" --tiles "P:\regions\4X4.tiles.json"`                          |
| Ouvrir                        | `http://…/index.html?region=4X4` (la coquille commune, comme § 16)                                                     |
| Essayer un autre rayon        | `index.html?region=4X4&radius=300`                                                                                     |
| Changer un réglage            | relancer la même commande avec l'option : rien de lourd n'est recopié                                                  |

`-o` désigne la région (son nom sans extension). Pas de `.glb` en entrée. `--tiles` seul (sans `--shared-shell`) donne une coquille propre `4X4.html`. Sont écrits : `4X4.config.json` (champ `tiles`), `4X4.zones.json` (si absent ou si une source de zones est donnée), la coquille et `lib/` s'ils manquent. **`4X4.tiles.json` et le dossier des tuiles ne sont copiés que s'ils ne sont pas déjà à côté de la page** : mettre `-o` dans le dossier des tuiles évite toute copie (« tuiles déjà à côté de la page : rien n'est copié ») ; sinon le script copie ce qui manque ou a une autre taille, fichier par fichier, et dit combien. Il n'y a pas de `4X4.glb`. Comme tout mode modulaire, la page demande http/https.

### Les paramètres (dans `X.config.json`, avec leurs options)

| Clé / option                                | Défaut    | Sens                                                                                                                                                              |
| ------------------------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tileRadius` / `--tile-radius`              | 150       | m : charger les tuiles dont la **boîte** (min / max de `X.tiles.json`) est à moins de ce rayon de l'avatar, en plan X,Z (distance 0 = l'avatar est dans la boîte) |
| `tileMargin` / `--tile-margin`              | 60        | m : décharger au-delà de rayon + marge (hystérésis : pas de va-et-vient à la limite)                                                                              |
| `tileMaxMB` / `--tile-max-mb`               | 200       | Mo de tuiles chargées en même temps (poids des fichiers `.glb`)                                                                                                   |
| `tileMaxTriangles` / `--tile-max-triangles` | 8 000 000 | triangles de tuiles chargées en même temps                                                                                                                        |
| `tileConcurrency` / `--tile-concurrency`    | 4         | téléchargements simultanés                                                                                                                                        |

`?radius=NNN` dans l'adresse remplace `tileRadius` pour cette ouverture (10 à 5 000). Ces clés n'existent dans la config que pour une région en tuiles.

### Ce que fait la page

- **Départ.** Les tuiles autour du point de départ se chargent d'abord, les plus proches en premier : l'arrivée du lien (`#spawn=…`, sinon l'arrivée `default`) si la page est ouverte par un portail, sinon la cible de la caméra. « Chargement… » reste affiché jusqu'à ce que les tuiles qui contiennent ce point soient prêtes (ou en échec) ; les autres arrivent ensuite. Un sol partiel est normal tant que tout n'est pas là : une tuile ne contient que ses patches de terrain et ses objets.
- **Pendant la visite.** Le point de référence est l'avatar en promenade, ou la cible (le cercle d'atterrissage) en vue globale. Toutes les 250 ms : déchargement des tuiles au-delà de rayon + marge, chargement de celles du rayon. Si `tileMaxMB` ou `tileMaxTriangles` serait dépassé, les tuiles **chargées les plus lointaines** (plus lointaines que celle à charger) partent d'abord ; une tuile qui contient l'avatar est chargée même si elle dépasse seule le budget (avertissement en console).
- **Mémoire.** Une tuile déchargée libère ses géométries, matériaux, textures et images décodées. Le budget compte le **poids des fichiers** : des textures décodées pèsent bien plus en mémoire graphique que leur fichier compressé ; en cas de page lourde, baisser `tileMaxMB` ou `tileRadius`. La grille de collision de chaque tuile coûte environ 36 octets par triangle de sol et de mur, plus l'index : à 8 millions de triangles, compter plusieurs centaines de Mo.
- **Promenade et collisions.** Une grille de collision est construite par tuile, par tranches pour ne pas figer l'image, et supprimée avec la tuile. Sol et murs ne viennent que des tuiles prêtes. L'avatar **n'avance jamais vers un point dont une tuile n'est pas prête** : il reste sur place, le texte « Chargement du sol… » s'affiche, et il repart dès que la tuile est prête (jamais de chute). **F** attend la tuile sous l'avatar avant de démarrer la promenade (F de nouveau : annuler) ; un portail interne ou un double-clic vers une zone non chargée attend de même. Les patches de terrain ont des bords communs : le sol se prolonge d'une tuile à l'autre sans marche.
- **Tuile en échec** (fichier absent, HTTP 404, GLB illisible) : message en haut de la page et dans la ligne d'information, avertissement en console, nouvelle tentative 3 s, 6 s, 12 s… jusqu'à 30 s après. Les autres tuiles ne sont pas retardées. Un avatar ne traverse pas la boîte d'une tuile en échec (même règle que « pas prête »).
- **Ligne d'information** (texte seul), dans le panneau d'aide en bas à gauche (masquable avec H), sinon dans un petit cadre : « Tuiles : 7 chargées / 106 · 74 Mo · 2,10 M triangles », avec « · 2 en cours » et « · 1 en échec (nouvelle tentative) » quand il y en a, puis (v31) « · Vue d'ensemble (à part) : 23,1 Mo · 1,40 M triangles » : la vue d'ensemble est comptée à part, hors des 200 Mo / 8 M triangles du budget.
- **Vue d'ensemble (v31).** Si `X.tiles.json` mentionne `overview`, la page la charge **en premier** (avant toute tuile), avec les mêmes règles de sécurité de chemin que les tuiles. Elle montre toute la région en géométrie légère, sans image. Chaque cellule (un nœud par fichier de tuile) est **masquée dès que la tuile détaillée correspondante est affichée** et réaffichée quand la tuile est déchargée ou en échec : jamais les deux, jamais de trou pendant un chargement. Elle ne sert **ni aux collisions, ni au sol, ni à « Chargement du sol… »** (la promenade attend toujours la tuile), et n'entre pas dans le budget `tileMaxMB` / `tileMaxTriangles`. Un **double-clic** dessus en vue globale place la cible sur le point lointain ; le sol réel est repris quand sa tuile est prête. Si elle est introuvable ou illisible : avertissement en console, « Vue d'ensemble indisponible » dans la ligne d'information, la région fonctionne comme en v30.
- **Vue globale.** Avec la vue d'ensemble, la caméra se cadre sur **toute la région** (distance maximale, brouillard et plan lointain suivent l'étendue). Sans elle (ancien `X.tiles.json` ou `--no-overview`), comme en v30 : seules les tuiles chargées autour de la cible, et la caméra se cadre sur le rayon de chargement.
- **Sortie de promenade (v31).** F pour sortir place la cible de la vue globale au sol sous l'avatar et garde le décalage de caméra d'avant l'entrée en promenade ; le chargeur suit cette cible, donc les tuiles autour de l'avatar ne sont pas déchargées.

### Repère, rotation, mer, zones

- **Repère.** Celui du modèle d'origine : **aucun recentrage** (les tuiles gardent leurs coordonnées). Les coordonnées des zones, arrivées, cible de caméra et trou de la mer sont donc dans ce repère, pas dans celui du viewer (qui recentre le modèle entier, ce qu'on ne peut pas faire avec des tuiles). `--rotate` (0, 90, 180, 270) tourne la racine des tuiles autour de l'axe vertical passant par l'origine ; comme au § 11, les valeurs stockées sont dans le repère déjà tourné, et la cible par défaut écrite par `--tiles` l'est aussi.
- **Cible et mer par défaut.** Sans `--target`, la cible de caméra est le centre de l'étendue des tuiles, à 20 m de hauteur ; sans `--sea-y`, la mer est à 20 m (l'eau d'OpenSim). La mer est centrée sur le centre de l'étendue ; le trou (`--hole`, `--hole-x`, `--hole-z`) est relatif à ce centre. Pour retirer la mer : `--no-sea`.
- **Zones libres** (cylindres à coordonnées, arrivées, portails, panneaux) : comme avant. **Zones liées à un objet** (champ `mesh`, v32) : si les tuiles portent les références d'objets (`glb2tiles.py` v32, § 17), la zone **apparaît quand la tuile qui contient l'objet est chargée** et disparaît quand elle est déchargée : cliquable, touche E à moins de `radius` m de l'objet, comme en mode GLB unique. Un objet réparti sur plusieurs tuiles : la zone suit la **boîte de l'objet entier** (stockée dans les tuiles), dès qu'**un** morceau est chargé. Tuiles d'avant la v32 : zone **ignorée**, avec « zone « id » ignorée : liée à l'élément « … » … (tuiles écrites sans références d'objets : redécouper avec glb2tiles v32) » en console, et un avertissement de `glb2html.py` à la génération. Présence, chat, carte des mondes, portails : inchangés. Le viewer ouvre maintenant une région en tuiles (§ 17 ter).
- **Position affichée (v32).** Le panneau d'aide (touche H, en bas à gauche) donne en texte la **position de la cible** en vue globale, ou de l'**avatar** en promenade : « Position cible (vue globale) : x 123.5 · y 15.0 · z -77.7 m », en mètres, une décimale, dans le repère du modèle d'origine : celui des zones. Pratique pour noter un endroit.

### Limites de cette version

- La vue d'ensemble est grossière : les petits objets (sous `--ov-threshold`), le verre et les objets à squelette n'y figurent pas, les couleurs sont unies, le terrain est au pas de 4 m ; à la limite d'une tuile chargée, la hauteur du sol peut différer de quelques décimètres entre la tuile (1 m) et la vue d'ensemble (4 m).
- Les meshes partagés entre tuiles sont dupliqués dans chaque tuile qui les utilise (tuiles autonomes) : plus de Mo téléchargés.
- Un mesh unique plus lourd que le budget de `glb2tiles.py` reste dans une seule tuile (pas de découpage par triangles).
- Une tuile très lourde en triangles reste coûteuse à analyser : la construction de sa grille de collision est découpée, pas supprimée.
- Pas de compression meshopt des tuiles, pas encore de textures de terrain d'OpenSim (couleurs par sommet de `oar2glb.py`).

### Si quelque chose ne va pas

| Symptôme                                             | Cause probable                                                                                                                                       | Que faire                                                                                                                           |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| « Erreur de chargement : … X.tiles.json : HTTP 404 » | `X.tiles.json` n'est pas à côté de la page, ou le champ `tiles` de la config est faux                                                                | relancer `glb2html.py --tiles` ; vérifier le dossier                                                                                |
| « adresse de tuiles refusée »                        | le champ `tiles` contient `..`, `:`, `?`, `#` ou commence par `/`                                                                                    | un chemin relatif simple (`X.tiles.json`)                                                                                           |
| Sol partiel, trous                                   | tuiles hors du rayon, ou en échec                                                                                                                    | monter `tileRadius` (ou `?radius=`), voir la ligne d'information et la console                                                      |
| « Chargement du sol… » qui reste                     | une tuile en échec devant l'avatar                                                                                                                   | corriger le fichier ; la page réessaie seule                                                                                        |
| Au loin, rien ou un trou                             | pas de vue d'ensemble (région découpée avant la v31, ou `--no-overview`)                                                                             | `glb2tiles.py … --overview-only` avec les options d'origine, puis relancer `glb2html.py --tiles` (copie le fichier avec les tuiles) |
| « Vue d'ensemble indisponible »                      | `X.overview.glb` absent à côté de la page, ou illisible                                                                                              | le copier à côté de `X.tiles.json` ; relancer `glb2html.py --tiles`                                                                 |
| Page lourde, ralentie                                | trop de textures chargées                                                                                                                            | baisser `tileMaxMB`, `tileMaxTriangles` ou `tileRadius`                                                                             |
| Les zones liées n'apparaissent pas                   | la tuile de l'objet n'est pas chargée (elles n'existent que tuile chargée), ou les tuiles datent d'avant la v32 (ignorées, avertissement en console) | s'approcher / `?radius=` ; sinon refaire le découpage avec `glb2tiles.py` v32 (§ 17), ou utiliser des zones libres à coordonnées    |
| Les zones sont décalées                              | elles viennent du viewer (repère recentré)                                                                                                           | les écrire dans le repère du modèle d'origine                                                                                       |

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

Autre façon d'ouvrir : par adresse, si le viewer est servi en http (par exemple `python -m http.server` lancé dans un dossier qui contient `glb-viewer.html` et, en dessous, la région) : `http://localhost:8000/glb-viewer.html?tiles=region/X.tiles.json`. Le chemin est relatif à la page, sans `..`, sans `:`, `?` ni `#`.

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

| Situation                                                        | Cadrage de départ (cible de la caméra)                                         | Touche F (sans avoir déplacé la cible) |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------ | -------------------------------------- |
| la région a une arrivée `default`, pas de `--target`             | **la position de cette arrivée**                                               | **son point et son orientation**       |
| la région a une arrivée `default`, `--target` donné              | la cible donnée                                                                | la cible (comme avant)                 |
| pas d'arrivée `default`                                          | la cible (celle de la configuration, ou le centre de l'étendue en mode tuiles) | la cible (comme avant)                 |
| configuration écrite avant la v33 (sans la clé `targetExplicit`) | la cible (comme avant)                                                         | la cible (comme avant)                 |

Avec un lien (`#spawn=`, `#pos=`), le cadrage et la promenade se font à l'arrivée demandée. En mode tuiles, c'est ce point qui sert de référence de chargement au départ.

Le viewer écrit `targetExplicit` à vrai quand la cible de sa caméra n'est pas la cible par défaut (même test que la ligne de commande `--target`). Une arrivée `default` placée dans le viewer ne change donc rien à une page dont tu as cadré la caméra à la main.

**Retour à l'arrivée** : bouton « Retour à l'arrivée (R) » ou touche **R**. En promenade : téléportation à l'arrivée `default` (à défaut : à la cible de départ), avec « Chargement du sol… » si la tuile n'est pas prête, comme un portail interne. En vue globale : la cible et la caméra se déplacent sur ce point (même décalage de caméra).

### 18.3 Marqueurs de zones dans la page exportée

| Option          | Valeur                                  | Effet                                                                                                                                                                                      |
| --------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `--zone-marker` | `dot` (défaut ; `discret` avant la v43) | comportement d'avant : disque plat de 0,4 m semi-transparent et anneau fin                                                                                                                 |
|                 | `range` (`portee` avant la v43)         | **anneau fin et net au rayon réel de la zone**, sans cylindre ; un trait d'un pixel est ajouté à l'anneau plat pour qu'il reste tracé de loin                                              |
|                 | `none` (`aucun` avant la v43)           | aucun marqueur ; la zone reste cliquable et se déclenche comme avant                                                                                                                       |
| `--show-spawns` | (aucune)                                | dessine aussi les **arrivées** : petit disque de 0,3 m et anneau fin au sol. Sans cette option, les arrivées ne sont **jamais** dessinées dans la page exportée (seulement dans l'éditeur) |

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

(Depuis la v37 l'exemple de lancement recommandé est `python .\presence_server.py --log presence.log --log-ip raw --log-days 0` ; voir § 22.6 pour `--log-days 0`, l'historique du chat et les données personnelles.)

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

| Option                       | Rayon de la zone de survol / de clic (disque invisible au sol)                                                                                        |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--zone-marker range`        | **le rayon de l'anneau visible** (rayon réel de la zone ; 2 m au moins pour un panneau) : l'infobulle apparaît en survolant l'anneau ou son intérieur |
| `--zone-marker dot` (défaut) | le rayon de la zone borné entre **0,6 m** (comme avant) et **1 m**                                                                                    |
| `--zone-marker none`         | 0,6 m, comme avant                                                                                                                                    |

### 19.3 Vol

**Page Haut** monte, **Page Bas** descend (en plus de **Espace** maintenu et **C**, v36), sans défilement de la page. **Début** garde la bascule. Quand on descend jusqu'au sol, **l'avatar atterrit tout seul** (le vol s'arrête, la gravité reprend) ; il ne passe jamais sous le sol. Le bouton **« Voler / Atterrir »** de la barre du bas (visible en promenade, absent avec `--no-fly`) bascule le vol ; son état (`aria-pressed`) et la ligne « Mode : … » le disent en texte.

### 19.4 Souris libre après Échap

En promenade, quand le pointeur est libéré (Échap, ou perte du focus), la page mémorise **« souris libre »**, écrit « Souris : libre (G ou bouton « Capturer la souris » pour la reprendre) » dans le bloc d'état et **ne redemande plus le verrouillage** : un clic simple, un double-clic (téléportation à l'endroit du curseur) et un clic sur une zone fonctionnent à l'endroit du curseur ; glisser avec le bouton enfoncé tourne toujours la vue. **Capturer** : touche **G** (elle bascule : si la souris est déjà capturée, elle la libère) ou bouton **« Capturer la souris »** (barre du bas ; il ne fait que capturer, un pointeur capturé ne peut pas le cliquer). L'état est remis à zéro à chaque entrée en promenade, mais **un clic ne capture jamais la souris** (après la v52 ; avant, le premier clic la capturait) : la capture est toujours volontaire, par **G** ou par le bouton. Sans capture, glisser avec le bouton enfoncé tourne la vue.

### 19.5 Couleur en direct

Changer la couleur dans les Réglages pendant la connexion envoie `{"t":"color","color":N}` (au plus toutes les 300 ms, la dernière valeur part toujours). `presence_server.py` accepte un **entier de 0 à 0xFFFFFF** (sinon ignoré sans rien dire), ignore deux changements à moins de 0,2 s, met le visiteur à jour et diffuse `{"t":"color","id":…,"color":N}` aux autres ; un visiteur qui arrive ensuite reçoit la couleur à jour. L'avatar du visiteur lui-même (vue à la troisième personne) la prend aussi. Compatible : un ancien serveur ignore le message, un ancien client n'en envoie pas. **Relancer `presence_server.py`** pour en profiter.

### 19.6 `glb2html.py --update` : mettre à jour une région sans rien ressaisir

| Option     | Effet                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `--update` | lit `X.config.json` existant, **n'applique que les options explicitement données** (une valeur égale à la valeur par défaut, mais donnée, est appliquée), garde tout le reste (clés inconnues comprises) et `X.zones.json` (réécrit seulement avec `--zones`), écrit la version courante, **renouvelle la coquille** si elle diffère de celle de cette version (ancienne copie gardée sous `index.avant-AAAAMMJJ-HHMMSS.html`) et écrit `lib/` s'il manque. Sans `X.config.json`, échoue en proposant la commande sans `--update`. Exclut `--settings` |

Forme : `python glb2html.py --update -o "X.html" [--shared-shell [COQUILLE.html]] [--tiles "X.tiles.json" | "X.glb"] [options]`. Sans `--shared-shell`, la page `X.html` doit exister. La coquille est **partagée par les autres régions du dossier** : elles gardent leur comportement (les anciennes configurations restent comprises ; aucune clé de config n'est nouvelle en v34). Le compte rendu liste les clés changées. Le profil (`--profile`) ne filtre les zones qu'à l'écriture de la liste : ajouter `--zones` pour la réécrire.

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

| Commande                        | Firestorm                                                 | Cette page                                                                                                                                                              |
| ------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Marcher avant / arrière         | W ou ↑ / S ou ↓                                           | W ou ↑ / S ou ↓ (ZQSD en AZERTY ; v36 : l'aide affiche les lettres réelles)                                                                                             |
| Pas de côté                     | A / D (ou Maj + flèches)                                  | A / D (Q / D en AZERTY)                                                                                                                                                 |
| Tourner                         | ← / →                                                     | ← / → (à la troisième personne : tourne la caméra)                                                                                                                      |
| Courir                          | double appui sur W / S / ↑ / ↓ ; Ctrl+R bascule la course | **Maj**, ou **double appui** (moins de 300 ms) sur W, S, ↑ ou ↓, tant que la touche est maintenue. **Pas de course permanente** (Ctrl+R recharge la page du navigateur) |
| Sauter                          | E ou Page Haut (appui bref)                               | **Page Haut** (appui bref) ou **Espace** (v36 : E ne saute plus)                                                                                                        |
| Voler / atterrir                | Début                                                     | **Début** ou le bouton « Voler / Atterrir » (v36 : F ne bascule plus le vol)                                                                                            |
| Décoller                        | E ou Page Haut maintenu                                   | **Page Haut** maintenu **plus de 0,4 s** au sol : vol + montée                                                                                                          |
| Monter en vol                   | E ou Page Haut                                            | **Page Haut** ou **Espace** maintenu                                                                                                                                    |
| Descendre en vol                | C ou Page Bas                                             | **C** ou **Page Bas** maintenu ; **atterrissage automatique** au sol                                                                                                    |
| Vue subjective                  | M                                                         | **M** bascule vue subjective / troisième personne ; **V** fait tourner les trois vues (dont la caméra libre)                                                            |
| Orbiter la caméra               | Alt + glisser                                             | **Alt + glisser** (à la troisième personne, la souris orbite déjà autour de l'avatar sans le tourner)                                                                   |
| Caméra derrière l'avatar        | Échap                                                     | **Fin** ou **Alt + clic** (Échap est réservé au navigateur : il libère la souris)                                                                                       |
| Zoom caméra                     | molette                                                   | **molette** (3e personne : distance de la caméra ; caméra libre : avance / recule)                                                                                      |
| Carte du monde                  | Ctrl+M                                                    | **Ctrl+M** partout ; **M** seul l'ouvre aussi hors promenade                                                                                                            |
| Chat                            | Entrée                                                    | **Entrée**                                                                                                                                                              |
| Entrer / sortir de la promenade | (n'existe pas)                                            | **P** ou **F** (v36)                                                                                                                                                    |
| Toucher un objet, une zone      | clic                                                      | **clic** ou **E** (v36) ; un portail « en marchant dedans » part à l'entrée de son rayon                                                                                |
| Se téléporter                   | (carte, double-clic selon le réglage)                     | **double-clic**                                                                                                                                                         |
| Flèches à l'écran               | (n'existe pas)                                            | **K** ou le bouton « Flèches (K) » les cache ou les montre (v46, § 29)                                                                                                  |

Gardées telles quelles : ZQSD / WASD / flèches, Espace, Entrée, G, R, V, H, I, Maj.

### 20.3 Vol et saut

- Au sol, **Page Haut** : un appui bref fait **sauter** (comme Espace) ; **maintenu plus de 0,4 s**, l'avatar **décolle** et monte tant que la touche est tenue. Relâchée, il reste en vol, immobile en hauteur.
- **Début** bascule le vol (v36 : F ne le fait plus) ; le bouton « Voler / Atterrir » reste. Descendre jusqu'au sol (C ou Page Bas) pose l'avatar : le vol s'arrête tout seul (v34). Avec `--no-fly`, rien de tout cela ne fait voler : Page Haut saute seulement.

### 20.4 Troisième personne

- La **souris orbite la caméra** autour de l'avatar (lacet et tangage propres à la caméra) **sans le tourner** ; à l'arrêt l'avatar garde son orientation : on peut tourner autour de lui et voir son devant.
- Quand une touche de marche est pressée, **l'avatar se tourne vers sa direction de déplacement** (rotation lissée, quelques dixièmes de seconde) ; la marche avant va **dans la direction de la caméra**. La caméra ne traverse ni sol ni mur, comme avant.
- **La présence transmet l'orientation de l'avatar**, pas celle de la caméra : tourner la caméra de 180° sans marcher ne change rien pour les autres visiteurs. Vue subjective et caméra libre sont inchangées. **M** (ou V) change de vue ; en passant à la vue subjective le regard garde la direction de la caméra.

### 20.5 Infobulle et clic des zones : `--zone-info-dist`

| Option               | Config         | Effet                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| -------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--zone-info-dist M` | `zoneInfoDist` | distance, **en promenade**, jusqu'à laquelle l'infobulle, le clic et le **nom affiché** (« Toujours afficher le nom ») des zones fonctionnent. **150 m par défaut depuis la v37** (40 m en v35 et v36), de **5 à 500** (hors bornes : ramené à la borne). Réglable dans le viewer (section « Promenade »), repris dans la ligne de commande. Un nom plus loin que cette distance est masqué en promenade et réapparaît en vue globale |

`glb2html.py --update --zone-info-dist 60` suffit à l'appliquer à une région déjà publiée (§ 20.7).

### 20.6 Copier dans le presse-papiers

Tous les boutons « copier » (lien personnel, lien de ma position, point visé, cible, commande) utilisent `navigator.clipboard.writeText` dans un **contexte sécurisé** (https, localhost), et sinon, **en http sur une adresse publique**, un repli : champ temporaire hors écran, sélection, `document.execCommand('copy')`, suppression. La page affiche **« Copié »** quelques secondes. Si tout échoue, le champ du lien reste **affiché et sélectionné**, avec « Copie impossible : le texte est sélectionné, fais Ctrl+C ».

### 20.7 `--update` et la carte des mondes

`glb2html.py --update` accepte maintenant aussi `--register FICHIER`, `--region-name`, `--region-xy`, `--region-url`, `--region-spawn`, `--thumb`, `--map`, `--map-url` et `--map-page FICHIER.html` : il applique ce qui est donné et garde tout le reste (config et zones, comme avant). Le salon et la présence de la fiche viennent de la config existante quand tu ne les redonnes pas.

**Avec `--update`, les chemins relatifs de `--register`, `--map`, `--map-page` et `--thumb` sont relatifs au dossier de la page (celui de `-o`)**, et non au dossier des outils ni au dossier de lancement ; le message de fin le rappelle avec le dossier. Un chemin absolu est respecté. `--region-name`, `--region-url`, `--region-xy`, `--region-spawn` et `--thumb` sans `--register` sont ignorés avec un avertissement.

**Sans `--update`**, l'ancien comportement est conservé (un chemin relatif de `--register` est cherché dans le dossier de lancement, sinon dans le dossier des outils, où il est créé) ; quand le fichier n'est pas à côté de la page `-o`, une ligne dit où `regions.json` est écrit et propose `--update` ou un chemin complet.

### 20.8 Créer la carte des mondes

1. **Chaque région est enregistrée dans un même `regions.json`**, à côté des pages (un seul dossier de pages, une coquille commune). Pour chaque région déjà générée, une commande `--update --register`, **une seule ligne PowerShell** (nom, position sur la grille OpenSim, vignette facultative de 140 Ko au plus à côté de la page) :
   
   `python glb2html.py --update -o "X.html" --shared-shell --register regions.json --region-name "Nom affiché" --region-xy 1000,1001 --thumb vignette.png`
   
   La fiche reçoit l'adresse `index.html?region=X`, le salon et le serveur de présence de la config de la région. Redonner la commande met la fiche à jour (identifiée par le salon), sans doublon.

2. **Générer la page web de la carte** : `python glb2html.py --update -o "X.html" --shared-shell --map-page carte.html` (elle lit les régions de `regions.json` enregistrées dans la config de la région `X`). Pour qu'elle contienne toutes les régions, exécute-la **après** les enregistrements, ou donne `--map regions.json --map-page carte.html`.

3. **L'ouvrir par le serveur web**, pas depuis le disque : le dossier contenant `carte.html`, `index.html`, `lib/` et les régions est servi en http(s) (`python -m http.server` pour un essai, ou n'importe quel serveur web), puis ouvre `http://ADRESSE/carte.html`. Chaque lien de la carte ouvre la région à son point d'arrivée, avec le pseudo saisi en haut de la page.

4. **Les pages des régions** affichent la carte avec la touche **M** (**Ctrl+M** en promenade) : `--map-url http://ADRESSE/regions.json` (plusieurs adresses séparées par des virgules, fusionnées) les fait relire `regions.json` à chaque ouverture, sans régénérer les pages.

**Depuis la v47** : la page carte peut aussi être une `carte.html` universelle, sans région dedans, qui relit `regions.json` à chaque ouverture (§ 30.4).

### 20.9 Caméra libre et molette

- **Troisième personne** : la **molette** règle la distance de la caméra (de **1 à 30 m**, **4 m par défaut**, mémorisée dans le navigateur, clé `glb2html_tpsDist`), avec le recul devant un mur et la protection du sol déjà en place. **Fin** remet la caméra derrière l'avatar à la distance par défaut.
- **Caméra libre** : la molette **avance ou recule la caméra le long du regard**, d'un pas proportionnel à la distance caméra-avatar (15 %, au moins 0,5 m et au plus 20 m par cran), jamais sous le sol. La **vitesse des touches** est `max(vitesse de marche, 0,5 x distance caméra-avatar)` m/s, plafonnée à **60 m/s** ; **Maj la multiplie par 3**. **Alt + glisser** fait orbiter la caméra autour de l'avatar en gardant sa distance (lacet et tangage), le regard restant sur lui. **Fin** la remet derrière l'avatar, à 4 m.
- **Vue subjective** : la molette ne fait rien. Dans tous les cas la page ne défile pas en promenade (sur la vue ; l'aide et l'état gardent leur défilement).

## 21. Nouveautés de la v36 (23/10/2026)

### 21.1 Touches : F et P, E, vol

- **F** et **P** entrent en promenade et en sortent (vue globale comme promenade). Dans le **viewer**, P pose une zone en promenade ; on en sort avec **F**, **Maj+P** ou le bouton.
- **F ne fait plus basculer le vol.** Voler / atterrir : **Début**, le bouton « Voler / Atterrir », ou **Page Haut** maintenu plus de 0,4 s au sol. Monter en vol : **Page Haut** ou **Espace** maintenu. Descendre : **Page Bas** ou **C** (atterrissage automatique au sol). Sauter au sol : **Espace**, ou **Page Haut** en appui bref.
- **E** redevient la touche d'action des zones (déclenchement « au clic » ou « les deux ») : l'invite dit « clic ou E : … ». E ne fait rien d'autre (il ne saute plus, ne monte plus).

### 21.2 Disposition du clavier : AZERTY ou QWERTY

La marche garde les touches **physiques** (celles qui sont Z, Q, S, D sur un clavier AZERTY sont W, A, S, D sur un QWERTY) : rien ne change pour jouer. L'**aide** et la fenêtre **Informations / État** affichent les lettres **réelles** de ta disposition (« Z Q S D » ou « W A S D », jamais les deux à la fois). La disposition est détectée avec `navigator.keyboard.getLayoutMap()` quand le navigateur l'a (Chrome, Edge ; seulement en https ou sur localhost), sinon avec la langue du navigateur (fr, fr-FR et fr-BE : AZERTY ; le reste : QWERTY). Réglage visiteur **« Disposition du clavier : Auto / AZERTY / QWERTY »** (Réglages, mémorisé) ; même réglage dans le viewer. **M** (vue subjective / troisième personne en promenade, carte des mondes sinon ; Ctrl+M : carte partout) se reconnaît à la **lettre imprimée « m »**, pas à la place de la touche : sur un clavier AZERTY c'est la vraie touche M (avant la v36, c'était la touche « , »).

### 21.3 Aide et informations : trois temps

La fenêtre « État » s'appelle **Informations / État**. **H** (aide) et **I** (informations) font tourner la fenêtre : **masquée → affichée déployée** ; **réduite → déployée** ; **déployée → masquée**. Le clic sur la barre de titre réduit / déploie ; l'état (masqué, réduit, déployé) est mémorisé dans le navigateur.

### 21.4 Repères de portail (cônes) : `--zone-cone`, touche T

Au-dessus de chaque portail et de chaque zone « en marchant dedans » ou « les deux », la page dessine un petit **cône pointé vers le bas** (environ 0,35 m de large, 0,5 m de haut, sommet à 2 m au-dessus du centre de la zone ; teinte claire neutre, contour sombre : il se lit sans dépendre de la couleur). Il s'ajoute à `--zone-marker` (il ne le remplace pas). Visible jusqu'à `--zone-info-dist` (150 m par défaut depuis la v37) ; survoler le cône affiche la même infobulle que la zone, avec la **distance** au visiteur (§ 22.2). Depuis la v37 sa **taille apparente est constante** (§ 22.2). **T** affiche ou masque tous les cônes (choix mémorisé). `--no-zone-cone` les masque au départ (config `zoneCone`) ; les arrivées n'ont de cône qu'avec `--show-spawns`.

### 21.5 Arrivée occupée

Quand l'avatar est posé sur un point (ouverture, `#spawn=`, `#pos=`, arrivée par défaut, **R**, portail interne ou vers une autre région, « Aller à »), si un autre visiteur en promenade se trouve à moins de **1 m** (2 m en hauteur), le **nouvel arrivant** est décalé sur le point libre le plus proche : anneaux de 1,2, 2,4 puis 3,6 m, sol à moins de 1 m d'écart de hauteur, aucun mur entre les deux points, aucun visiteur à moins de 1 m. **(Règle remplacée en v37 : voir § 22.3 ; les anneaux sont maintenant autour de l'occupant.)** Si la présence n'est pas encore connectée, le contrôle est refait à la réception de la liste des visiteurs, seulement si l'avatar n'a pas bougé de plus de 0,3 m (on ne déplace jamais quelqu'un qui marche). Sans place libre à moins de 3,6 m, l'avatar est posé à l'endroit demandé. Les visiteurs en vue globale sont invisibles : ignorés.

### 21.6 Sons

Réglages visiteur : case générale **« Sons »** (cochée) avec un **volume** de 0 à 100 (50), puis trois cases cochées : « Bip quand un message cite mon pseudo », « Son à l'arrivée d'un visiteur » (deux notes montantes), « Son au départ d'un visiteur » (deux notes descendantes). Les sons sont synthétisés (Web Audio), sans fichier ; ils ne concernent que les visiteurs **en promenade** de ton salon (jamais les spectateurs, jamais toi, jamais ceux déjà présents quand tu arrives), au plus un son d'arrivée et un de départ toutes les 2 s. Le navigateur n'autorise le son qu'après une première action de ta part sur la page. Les anciens réglages du bip (clé `sound`) sont ignorés.

### 21.7 Copier ma position, « Aller à »

« **Copier ma position** » (panneau d'aide) copie, selon la liste à côté (mémorisée) : **URL** = l'adresse de la page avec `#pos=x,y,z,cap` ; **xyz** = `68.2, 39.0, -823.3` (mètres, point décimal, une décimale). Le champ « **Aller à** » accepte les deux, ainsi que les formats d'avant ; avec une adresse complète contenant `#pos=x,y,z,cap`, il reprend aussi l'orientation.

### 21.8 Langue de la page

Toute l'interface (aide, réglages, informations, invites, messages de chargement et d'erreur, chat, carte, page « carte des mondes », viewer) existe en **français** et en **anglais**. Réglage visiteur **« Langue / Language »** : **Auto** (la première langue de `navigator.languages` qui est disponible, sinon l'anglais), puis chaque langue disponible. Changer la langue recharge la page. Le paramètre **`#lang=en`** (ou `#lang=fr`, `#lang=auto`) dans l'adresse est prioritaire et mémorisé ; il se combine avec `#spawn=`, `#pos=`, `#name=`. Les textes que **tu** saisis (noms de zones, panneaux, pseudos) ne sont jamais traduits.

### 21.9 Ajouter une langue (sans toucher au code)

1. Copie `src/i18n/en.json` en `src/i18n/<code>.json` (le code est celui de `navigator.language` : `de`, `es`, `pt`…).
2. Traduis les **valeurs** (jamais les clés). `_name` = le nom de la langue dans cette langue (« Deutsch »). `{0}`, `{1}`… sont des marqueurs à garder tels quels (ils peuvent changer de place) ; les clés qui finissent par `.one` / `.other` (pluriel) peuvent aussi avoir `.zero`, `.two`, `.few`, `.many` si ta langue le demande. Une clé absente est remplacée par l'anglais, puis le français, puis la clé elle-même : une traduction partielle fonctionne.
3. Les clés commençant par `page.`, `core.`, `viewer.`, `map.` et `common.` sont celles des pages et du viewer ; celles qui commencent par `py.` sont celles des outils Python (`--lang`, § 21.11).
4. Fabrique avec `python build.py` (le dossier de langue se choisit avec `--i18n DOSSIER`) : la liste « Langue / Language » propose la nouvelle langue, les pages et les outils de `dist\` l'embarquent. Aucun code à modifier. `python tests/i18n.py` vérifie les fichiers de langue (mêmes clés, mêmes marqueurs, aucune clé inutilisée).

### 21.10 Langue du viewer

Le viewer (`glb-viewer.html`) a la même liste « **Langue / Language** » que les pages exportées (Auto, puis chaque langue disponible), le même repli (anglais, puis français, puis la clé) et le même paramètre `#lang=`. Tous ses textes sont traduits (réglages, boutons, messages, aide), y compris la section « Clavier » (Auto / AZERTY / QWERTY) et les commandes qu'il fabrique ; les noms de zones que tu saisis ne le sont jamais. Les pages que le viewer exporte (HTML autonome, `.zip` modulaire) contiennent la même coquille que `glb2html.py` : leur langue se règle sur la page exportée, pas dans le viewer.

### 21.11 Langue des outils Python : `--lang`, `WEB3D_LANG`

`glb2html.py`, `glb2tiles.py`, `oar2glb.py` et `presence_server.py` (et `glb-stats.py`, utilisé par `glb2tiles.py`) affichent leurs messages, leurs avertissements, leurs erreurs et leur aide (`--help`) en français ou en anglais. **Choix de la langue** : `--lang fr`, `--lang en` ou `--lang auto` (par défaut) ; sinon la variable d'environnement `WEB3D_LANG` ; sinon la langue du système ; sinon l'anglais. `--lang` l'emporte sur `WEB3D_LANG`. Les options elles-mêmes (`--budget`, `--exclude`…) et les commandes de modération du serveur (`liste`, `ejecter`, `bannir`, `bans`, `debannir`, `aide`) ne changent pas de langue. Les fichiers de sortie (JSON, journaux des outils) gardent leurs clés ; les journaux sont écrits dans la langue choisie.

**Fichiers autonomes** : `build.py` intègre les textes de `src/i18n/*.json` (clés `py.*`) dans chaque outil de `dist\` : un outil copié seul sur une autre machine garde ses deux langues (c'est un choix de fabrication, documenté dans `CLAUDE.md`). Depuis les sources (`tools\`, `src\`), les outils lisent `i18n_py.py` et `i18n\` à côté d'eux ou dans `src\`. Ajouter une langue : § 21.9, aucun code à modifier. Une nouvelle option d'un outil doit avoir sa clé `py.*` dans **les deux** fichiers (`python tests/i18n.py` le vérifie) ; `python gen_reference.py` refait `REFERENCE_OPTIONS.md` (français puis anglais dans chaque case « Effet »), `python tests/doc_options.py` vérifie qu'aucune option n'y manque et qu'aucune description n'est vide.

## 22. Nouveautés de la v37 (23/10/2026)

### 22.1 Indicateur de course, boussole, fenêtres redimensionnables, touche O

- La ligne **Mode** de la fenêtre Informations / État affiche **« à pied · course »** ou **« en vol · course »** tant que la course est active (touche **Maj** tenue, ou double appui rapide en cours), puis revient à « à pied » ou « en vol ».
- **Boussole** : en haut de la page, au centre, le cap en texte, point cardinal puis degrés (« NE 45° »). C'est l'orientation de l'**avatar** en promenade, de la **caméra** en vue globale. Convention OpenSim : le nord est la direction **-Z** du modèle (z = -y d'OpenSim) ; la rotation de la région (`rotate`) est prise en compte. Lettres : français N, NE, E, SE, S, SO, O, NO ; anglais N, NE, E, SE, S, SW, W, NW. Case **« Boussole »** dans les Réglages visiteur (cochée par défaut, mémorisée). Options de `glb2html.py` : `--compass` / `--no-compass` (config `compass`, défaut activée) et `--north DEGRES` (config `northDeg`, défaut 0) pour un GLB qui ne vient pas d'OpenSim : le décalage est **ajouté** au cap affiché (180 : face à -Z, la boussole indique S). `--update` les applique.
- **Fenêtres Aide et Informations** : un **bord droit à tirer** (curseur de redimensionnement, double trait sur le bord) règle la largeur de chacune, de **260 px** à **70 %** de la fenêtre du navigateur ; la largeur est **mémorisée** dans le navigateur. Le texte se reflue et la **hauteur suit le contenu** (la barre de défilement de l'aide n'apparaît que si la fenêtre du navigateur est trop basse : à 260 px de large l'aide demande environ 730 px de hauteur). Les deux fenêtres restent empilées en bas à gauche : quand l'aide perd de la hauteur, elle descend pour rester collée aux informations. Les 440 px / 45 % de la v34 sont les valeurs par défaut.
- Touche **O** : ouvre / ferme la fenêtre **Réglages** (R est déjà pris).

### 22.2 Repère de portail (cône) : taille constante, distance

Le cône garde la **même taille apparente** : son échelle suit la distance à la caméra (distance / 12, entre 1 et 12), sa pointe reste au même point et sa forme ne change pas. Il reste visible jusqu'à `zoneInfoDist`, **150 m par défaut** (plage de 5 à 500). Son infobulle ajoute la **distance au visiteur**, arrondie au mètre et mise à jour quand on bouge : « Portail → château · 120 m » (en vue globale : distance à la caméra).

### 22.3 Arrivée occupée, améliorée

Le point libre choisi est le plus proche de l'**occupant** (et non du point demandé) : anneaux de **1,5, 2,0 puis 3,0 m** autour de lui (16 candidats par anneau), mêmes conditions de sol, de mur et de distance aux autres visiteurs qu'en v36 ; dans l'anneau, le candidat le plus proche du point demandé. L'arrivant est ensuite **tourné vers l'occupant** (le plus proche s'il y en a plusieurs). Une ligne est écrite dans la console du navigateur : « arrivée occupée : décalé de X m (anneau R m) ».

### 22.4 Pseudo cité : clignotement continu

Quand un message cite mon pseudo, l'alerte clignote sur **ma page seulement** : une demi-seconde visible, une demi-seconde cachée, sur l'**étiquette du nom de l'auteur** (qui reste même quand sa bulle a disparu), sa **bulle** si elle existe encore, et la **ligne du message** dans le chat. **Sans limite de durée** : le clignotement continue jusqu'à ma première action (touche, clic, mouvement de l'avatar, envoi d'un message), puis tout reste visible. Plusieurs citations avant mon action clignotent toutes. Le texte n'est pas seulement une couleur : l'élément disparaît et réapparaît. (Remplace les 6 clignotements de 300 ms de la v33.)

### 22.5 Paramètres du lien après `#`

Le séparateur est **`&`** ; **`#` est aussi accepté** : `#name=Klaatou&lang=en` et `#name=Klaatou#lang=en` sont équivalents (`name`, `lang`, `spawn`, `pos`, `key`). Une seule fonction (`hashParams`) lit le lien dans la page, la coquille et la page carte.

### 22.6 Historique du chat

- `presence_server.py --history N` : derniers messages rejoués aux nouveaux arrivants, **200 par défaut** (20 avant), 0 = aucun.
- `--history-file FICHIER` (désactivé par défaut) : chaque message est ajouté au fichier, une ligne JSON par message : `{"n":numéro,"t":secondes Unix,"d":"jj/mm/aaaa hh:mm:ss","room":salon,"name":pseudo,"text":texte}`. **Jamais l'adresse IP.** Le fichier est relu au démarrage : l'historique survit aux relances (jusqu'à 20 000 messages par salon en mémoire).
- `--history-days N` (défaut 30 ; **0 = tout conserver**) : au démarrage, les messages plus anciens ne sont ni relus ni conservés (le fichier est réécrit sans eux).
- **Protocole** : le client envoie `{t:'history', before:N, n:50}` (N = numéro du plus ancien message affiché) ; le serveur répond `{t:'history', msgs:[…], more:true|false}` pour son salon (au plus 100 messages, une demande toutes les 0,2 s). Chaque message (accueil, diffusion, page d'historique) porte en plus `n` et `t`/`ts` ; les anciens clients les ignorent. Un ancien serveur ne répond pas : le bouton « Messages plus anciens » se masque après 4 s.
- **Page** : le panneau de chat ouvert est **défilable**. Réglage visiteur **« Messages d'historique affichés »** (200 par défaut, de 20 à 2000, mémorisé). Bouton **« Messages plus anciens »** (par paquets de 50, insérés en haut ; masqué si `more` vaut false ou si le serveur ne répond pas). **Titre de l'onglet** : « (3) NomDeLaRégion » = messages non lus quand la page est cachée ou le chat réduit, remis à zéro à l'ouverture du chat (comportement voulu : ouvrir le chat vaut lecture de tous les messages, même sans les avoir fait défiler). **« N messages vous citent »** avec un bouton « Aller au premier » (ces messages gardent le clignotement du § 22.4 jusqu'à ma première action).
- **Données personnelles.** Les messages (pseudo, texte, heure) sont des données personnelles : informe tes visiteurs, limite la durée avec `--history-days`, protège le fichier. De même **`--log-days 0` conserve les journaux sans limite** (la rotation nocturne continue mais plus aucun fichier n'est supprimé) : à n'utiliser que si tu l'assumes.
- Commande de lancement du serveur (une seule ligne ; **relancer le serveur** pour profiter de l'historique) : `python .\presence_server.py --log presence.log --log-ip raw --log-days 0` ; ajoute `--history-file chat.jsonl` pour garder l'historique entre deux relances.

### 22.7 Région par défaut (`default.json`)

Quand l'adresse de la coquille n'a pas de paramètre `region`, elle essaie dans l'ordre : (a) `X.config.json` du nom de la page (comportement d'avant) ; (b) **`default.json`** du dossier, de la forme `{"region": "NOM"}` ; (c) la **première entrée de `regions.json`** dont l'adresse est relative et dont le paramètre `?region=NOM` est valide ; (d) sinon un message d'une phrase qui dit quoi faire. Le nom suit les mêmes contrôles de sécurité que `?region=`. `glb2html.py --shared-shell` écrit `default.json` la **première fois** qu'il fabrique une région dans un dossier où il n'existe pas ; **`--default`** fait de la région fabriquée la région par défaut même si `default.json` existe. `--update` ne l'écrase jamais, sauf avec `--default`.

### 22.8 Dossier lib : `--lib-url`

`--lib-url CHEMIN` : chemin relatif (par exemple `../lib`) ou adresse `http(s)` complète où trouver three.js et ses modules. Il est écrit dans la ligne `const LIB = './lib';` au début de la coquille (§ 28.4) quand la coquille est écrite, et retenu dans la config (`libUrl`) pour que `--update` le retrouve. Chemin relatif : `lib/three-X/` est créé à cet endroit s'il est absent ; adresse complète : rien n'est copié. Une coquille existante n'est jamais écrasée : pour changer le dossier d'une coquille déjà en place, modifie à la main la ligne `const LIB` (§ 28.4) ou utilise `--update --lib-url CHEMIN` (copie datée de l'ancienne). Valeurs refusées : `?`, `#`, `\`, guillemets, autres schémas (`javascript:`), chemins commençant par `/`.

### 22.9 Régions dans des sous-dossiers

`?region=` accepte `dossier/nom` ou `a/b/nom` : segments faits de lettres, chiffres, point (pas au début), tiret, souligné, espace et parenthèses ; jamais `..`, `:`, `\`, `?`, `#`, ni chemin commençant par `/`. La config, le GLB ou les tuiles, les zones (et `zones.json` de ce dossier) et la vue d'ensemble se résolvent à partir du **dossier de la région** (les chemins de la config sont relatifs à ce dossier). Fabriquer : `glb2html.py X.glb --shared-shell P:\site\index.html -o P:\site\sous\dossier\Ile.html` (le chemin de la coquille désigne le dossier parent ; la région doit être dessous ; coquille, `lib/` et `default.json` sont écrits dans ce dossier parent ; combine avec `--lib-url`). L'adresse devient `index.html?region=sous/dossier/Ile`.

### 22.10 Tests de la v37

`tests/v37.py` (lot 1), `tests/v37_chat.py` (lot 2), `tests/v37_region.py` (lot 3), aide commune `tests/h37.py`. Attentes adaptées parce qu'une règle de la v37 l'impose : `v33.py` (le clignotement ne s'arrête plus seul : il s'arrête à une touche), `v35.py` (zoneInfoDist 150 par défaut, bornes 5 et 500 ; les tests de 40 m demandent `--zone-info-dist 40`), `v36.py` (la pointe du cône reste en place quand l'échelle change).

## 23. Nouveautés de la v39 (23/10/2026)

### 23.1 Bouton « Copier le diagnostic »

En bas de la fenêtre **Informations / État** (touche **I**), le bouton **« Copier le diagnostic »** copie dans le presse-papiers un texte à coller tel quel dans une conversation d'aide : il remplace les relevés de la console F12. Le bouton reste visible quand la fenêtre est réduite ; il ne garde pas le focus (Espace et Entrée restent à la promenade et au chat). Le même bouton est en haut du panneau du viewer (`glb-viewer.html`).

Le texte contient : la version du code (et celle de la configuration de la région si elle diffère), la date, la durée depuis l'ouverture, l'adresse de la page, la langue, le clavier, le navigateur, la taille de la fenêtre, la carte graphique vue par WebGL, le rendu de la dernière image (triangles, appels de dessin, géométries, textures), la mémoire JavaScript (Chrome et Edge seulement), les tuiles (prêtes, en cours, en échec) et leurs durées (première et dernière prêtes, médiane et maximum par tuile), les lignes affichées dans la fenêtre Informations / État, l'état de la présence, puis **les 10 dernières erreurs et avertissements** de la page (erreurs non attrapées, promesses rejetées, `console.error`, `console.warn`, fichiers qui ne se chargent pas).

**Rien de privé** : l'hôte de la page et de tout serveur est remplacé par `ADRESSE`, les adresses IP aussi ; la partie `#` de l'adresse (pseudo, clé) n'est jamais copiée.

Si le navigateur refuse la copie (page en `http://` hors `localhost`), le texte s'affiche **déjà sélectionné** sous le bouton : **Ctrl+C**. Une page fabriquée avec `--no-walk` n'a pas de fenêtre Informations / État, donc pas de bouton.

### 23.2 Tests de la v39

`tests/v39.py` : bouton présent dans la page et dans le viewer, en français et en anglais, adresses masquées, erreurs capturées, durées d'une région en tuiles.

## 24. Nouveautés de la v40 (24/10/2026)

### 24.1 Fenêtre « Arrivées » (touche L)

Sous la fenêtre **Informations / État**, la fenêtre **Arrivées** liste les points d'arrivée de la région (`default` d'abord, puis par nom ; l'étiquette remplace l'identifiant quand elle existe). Au survol, une bulle rappelle son rôle : liste des points de téléportation disponibles (TP).

- **En promenade**, un clic sur un nom téléporte à cette arrivée.
- **En vue globale**, un clic sur un nom fait entrer en promenade à cette arrivée.
- **L** fait tourner la fenêtre comme **H** et **I** : masquée → déployée ; réduite → déployée ; déployée → masquée. Le titre « ▾ Arrivées » la réduit ou la déplie. Les états sont mémorisés dans le navigateur (clés `glb2html_spawn` et `glb2html_spawnFold`).
- Une région sans arrivée n'a pas cette fenêtre ; **L** le dit par un message, et l'aide ne cite pas **L**.

### 24.2 Bouton « Recentrer la vue »

Dans la barre du bas, hors promenade seulement : le bouton **« Recentrer la vue »** remet le cadrage d'ouverture de la région (même centre, même angle, même distance qu'à la fin du chargement). **R** reste le retour à l'arrivée : en vue globale, il centre la vue sur l'arrivée en gardant l'angle et la distance.

### 24.3 Lien « Manuel complet » et bulle du diagnostic

La fenêtre d'aide (**H**) se termine par un lien **« Manuel complet (en ligne) »** vers ce manuel sur GitHub, en français si la page est en français, en anglais sinon (il faut une connexion Internet). Le viewer a le même lien sous le bouton « Copier le diagnostic ». Ce bouton a maintenant une bulle qui explique ce qu'il copie et ce qu'il ne copie jamais.

### 24.4 Tests de la v40

`tests/v40.py` : liste et ordre des arrivées, touche L, téléportation au clic (vue globale et promenade), bouton « Recentrer la vue » (cadrage d'ouverture exact), région sans arrivée, aide, lien du manuel et bulle du diagnostic en français et en anglais, viewer.

## 25. Nouveautés de la v41 (24/10/2026)

### 25.1 Bulles des fenêtres

Au survol du titre, chaque fenêtre dit son rôle et sa touche : **Aide** (H), **Informations / État** (I), **Arrivées** (L), puis comment la réduire, la déplacer et la remettre dans sa pile. Le bouton **Réglages** a aussi sa bulle (O).

### 25.2 Fenêtres déplaçables

Les fenêtres **Aide**, **Informations / État** et **Arrivées** se déplacent en **glissant leur titre**. Il y a deux piles :

- **la pile de gauche**, en bas de l'écran : la place d'origine des trois fenêtres ;
- **la pile de droite**, sous le bouton **Réglages** : quand Réglages s'ouvre, elle descend d'autant ; quand il se ferme, elle remonte.

Une fenêtre lâchée sur une pile s'y accroche, à la hauteur où on la lâche. Lâchée ailleurs, elle reste **libre**, exactement où on l'a posée, au-dessus de la vue. Un **double-clic sur le titre** la renvoie à la dernière pile où elle était accrochée (la gauche si elle n'en a jamais connu d'autre). Si la fenêtre du navigateur rétrécit, une fenêtre libre est ramenée dans l'écran ; sa position retenue ne change pas.

Un **clic** sur le titre réduit ou déplie toujours la fenêtre, mais **250 ms après le clic** quand il est fait à la souris : un double-clic ne la replie donc pas. Le bord droit garde son rôle de la v37 (tirer pour changer la largeur) ; la largeur de la fenêtre Arrivées se règle aussi.

### 25.3 Disposition retenue et fichier de disposition

La disposition (pile ou position de chaque fenêtre, ordre dans les piles) est retenue par le navigateur (clé `glb2html_layout`), avec les états ouvert / réduit et les largeurs. Elle dépend du navigateur et de l'adresse de la page.

Dans **Réglages**, rubrique **Disposition des fenêtres** :

- **« Enregistrer la disposition »** télécharge un fichier `disposition.json` (dossier Téléchargements, ou l'emplacement que le navigateur demande) ;
- **« Charger une disposition »** ouvre le choix de fichier et applique le `.json` choisi aussitôt, sans recharger la page. Un fichier qui n'est pas une disposition est refusé et rien ne change ;
- **« Disposition d'origine »** remet les trois fenêtres dans la pile de gauche et efface les largeurs.

Une page web ne peut pas écrire d'elle-même dans un fichier choisi à l'avance : l'enregistrement passe donc par un téléchargement.

### 25.4 Tests de la v41

`tests/v41.py` : bulles, glisser vers la vue (libre), vers Réglages (pile de droite poussée par Réglages), rechargement, double-clic de retour sans replier, clic retardé, enregistrer, disposition d'origine, charger, fichier refusé, fenêtre libre gardée dans l'écran. `tests/v35.py` et `tests/v36.py` attendent maintenant 300 ms après un clic de souris sur un titre.

## 26. Nouveautés de la v42 (24/10/2026)

### 26.1 Rendu léger

Sans carte graphique (rendu logiciel, par exemple « Microsoft Basic Render Driver » dans Edge), ou sur une très grosse région, chaque image coûte cher et la page répond lentement. Le **rendu léger** allège l'image : moins de pixels calculés, moins d'images par seconde et, en vue globale, la vue d'ensemble seule.

Dans **Réglages**, la case **« Rendu léger »** se trouve sous **« Haute résolution »**. La cocher applique les valeurs préconisées ; la décocher rend les valeurs normales de la page. Le choix est retenu par ce navigateur, pour cette région.

### 26.2 Réglages fins

Le bouton **« Réglages fins… »**, à côté de la case, ouvre une petite fenêtre à gauche de Réglages ; elle se cache quand Réglages se ferme. Chaque réglage s'applique aussitôt, que la case soit cochée ou non :

| Réglage                            | Normal                                    | Préconisé | Effet                                                                 |
| ---------------------------------- | ----------------------------------------- | --------- | --------------------------------------------------------------------- |
| Résolution du rendu                | 100 %                                     | 50 %      | moins de pixels calculés ; le navigateur agrandit l'image, plus floue |
| Images par seconde (au plus)       | sans limite                               | 15        | laisse du temps au navigateur entre deux images (fenêtres, clavier)   |
| Vue globale : vue d'ensemble seule | non                                       | oui       | hors de la promenade, aucune tuile détaillée n'est chargée            |
| Rayon des tuiles détaillées        | celui de la page (`--tile-radius`, 150 m) | 80 m      | moins de tuiles autour de l'avatar                                    |
| Anticrénelage                      | oui                                       | non       | bords lissés ; pris au prochain chargement de la page                 |

Les deux réglages de tuiles n'apparaissent que sur une région en tuiles. **« Valeurs préconisées »** remet les cinq valeurs de la colonne « Préconisé ». **« Valeurs d'origine »**, en bas de Réglages, remet aussi le rendu léger aux valeurs de la page. Les valeurs préconisées sont une estimation : elles n'ont pas été mesurées sur Edge en rendu logiciel.

Avec la vue d'ensemble seule, les tuiles détaillées se chargent quand on entre en promenade et repartent quand on en sort. Les zones liées à un objet d'une tuile ne sont donc visibles qu'en promenade.

### 26.3 Proposition automatique

Quand la page voit un rendu sans carte graphique (« Basic Render Driver », « SwiftShader », « llvmpipe »), un message en bas de l'écran, au-dessus des boutons, propose d'activer le rendu léger : **Oui** applique les valeurs préconisées, **Non** garde le rendu normal. La question n'est posée qu'une fois ; on change d'avis dans Réglages.

### 26.4 Option `--light`

`glb2html.py --light` : la page s'ouvre en rendu léger tant que le visiteur n'a rien choisi ; `--no-light` revient au rendu normal (par défaut). L'option est reprise par `--update`. Dans le viewer, la case « Page exportée ouverte en rendu léger (--light) » fait de même pour les pages exportées ; trois lignes de la rubrique du rendu (résolution, images par seconde, vue d'ensemble seule) règlent le viewer lui-même.

### 26.5 Fenêtre Réglages plus étroite

Réglages fait au plus 420 px de large : les longs libellés passent à la ligne, et la fenêtre défile si elle dépasse la hauteur de l'écran. La note sur la couleur de l'avatar tient sur deux lignes. **Disposition des fenêtres** devient une vraie section (titre en gras, filet au-dessus, trois boutons alignés), et la note « En promenade, Échap libère la souris… » est désormais tout en bas de la fenêtre.

### 26.6 Diagnostic

« Copier le diagnostic » ajoute deux lignes : les réglages du rendu léger en cours, et le nombre d'images rendues par seconde sur les 5 dernières secondes, avec ce qui force le rendu continu (mer animée, autres visiteurs, promenade, tuiles en chargement ; « rien » quand la page ne redessine qu'à la demande).

### 26.7 Tests de la v42

`tests/v42.py` : proposition en rendu logiciel, Oui, choix retenu, anticrénelage coupé au chargement, case et sous-fenêtre, réglages en direct, valeurs préconisées, plafond d'images par seconde, diagnostic, valeurs d'origine, page `--light`, `--update`, vue d'ensemble seule sur une région en tuiles (déchargement, promenade, retour), rayon en direct, lignes du viewer, note de couleur sur deux lignes, largeur de Réglages, section Disposition, note en bas.

## 27. Référence des fichiers JSON (v43)

Cette section décrit **chaque fichier JSON du projet, champ par champ**, comme le font `opensim.sample.ini` et `robust.sample.ini` pour OpenSim.

Un fichier JSON n'accepte pas de commentaires. Les explications sont donc ici, et les exemples sont à part, dans le dossier `docs/samples/` : ce sont de **vrais fichiers, complets et valides**. Pour s'en servir, on copie l'exemple, on le renomme et on change les valeurs. Le test `tests/samples.py` vérifie que chaque exemple est accepté par le vrai code qui lit ce fichier : la page, le viewer, les outils et le serveur de présence. Les exemples restent donc justes quand le code change.

### 27.1 Les fichiers et leurs exemples

| Fichier réel                                           | Exemple dans `docs/samples/`       | Écrit par                                    | Lu par                                               |
| ------------------------------------------------------ | ---------------------------------- | -------------------------------------------- | ---------------------------------------------------- |
| `NOM.config.json`                                      | `region.config.sample.json`        | `glb2html.py`                                | la page                                              |
| `NOM.zones.json`                                       | `region.zones.sample.json`         | le viewer, `glb2html.py --zones`, à la main  | la page, le viewer, `glb2html.py --zones`            |
| `default.json`                                         | `default.sample.json`              | `glb2html.py --default`                      | la coquille                                          |
| `regions.json`                                         | `regions.sample.json`              | `glb2html.py --register`, le viewer          | la page (`mapUrl`), la coquille, `glb2html.py --map` |
| `NOM.tiles.json`                                       | `region.tiles.sample.json`         | `glb2tiles.py`                               | la page, le viewer, `glb2html.py --tiles`            |
| `NOM.reglages.json`                                    | `region.reglages.sample.json`      | le viewer (« Enregistrer dans un fichier »)  | le viewer, `glb2html.py --settings`                  |
| `disposition.json`                                     | `disposition.sample.json`          | la page (Réglages, « Enregistrer »)          | la page (Réglages, « Charger »)                      |
| `presence_identities.json`                             | `presence_identities.sample.json`  | `presence_server.py`                         | `presence_server.py`                                 |
| `presence_bans.json`                                   | `presence_bans.sample.json`        | `presence_server.py` (commande `bannir`)     | `presence_server.py`                                 |
| fichier de `--history-file` (par exemple `chat.jsonl`) | `chat_history.sample.jsonl`        | `presence_server.py`                         | `presence_server.py`                                 |
| fichier de `--visits` (par exemple `visits.jsonl`)     | `visits.sample.jsonl`              | `presence_server.py`                         | `presence_server.py`                                 |
| `presence_visits_keys.json`                            | `presence_visits_keys.sample.json` | `presence_server.py` (commande `visits-key`) | `presence_server.py`                                 |
| `presence_creators.json`                               | `presence_creators.sample.json`    | à la main (§ 34)                             | `presence_server.py` (`--creators`)                  |

Deux autres fichiers ont **exactement le format** de `NOM.zones.json` :

- `zones.json`, les zones communes aux régions d'un dossier, lu quand une région n'a pas son propre `NOM.zones.json` (§ 16) ;
- `NOM.zones.bak.json`, la copie de sécurité que le viewer laisse quand il enregistre les zones dans le dossier de la région.

Dans les exemples, la région s'appelle `Region`. Pour une région « Ankh », on renomme `region.config.sample.json` en `Ankh.config.json` et on remplace `Region` par `Ankh` dans les valeurs qui le contiennent (`room`, `tiles`, les adresses). Les adresses des exemples sont écrites `ADRESSE` : il faut y mettre la sienne.

### 27.2 Comment lire les tableaux

- **Texte** : une valeur entre guillemets, par exemple `"door, porte"`.
- **Nombre** : sans guillemets, avec un point pour les décimales, par exemple `18.5`.
- **Oui / non** : `true` (oui) ou `false` (non), sans guillemets.
- **Liste** : des valeurs entre crochets, par exemple `[392, 68, -373]` pour une position x, y, z.
- **Objet** : des champs entre accolades, comme une fiche dans la fiche.
- **Couleur** : un nombre entier, qui est le code couleur habituel écrit en base 10. Le bleu de la mer `#3A9AD9` s'écrit `3840729`. Pour convertir dans PowerShell, taper `0x3A9AD9` donne `3840729`, et `'{0:X6}' -f 3840729` redonne `3A9AD9`. Les options `--sea-color` et `--sky-color` acceptent directement le code `3a9ad9`.
- **Option** : l'option de `glb2html.py` qui écrit ce champ. Un tiret « — » veut dire qu'aucune option ne le règle.

Les positions sont en mètres, dans le repère de la page : x vers l'est, y vers le haut, z vers le sud (le nord est la direction -z). Les angles (`yaw`) sont en radians : 1.57 fait un quart de tour, 3.14 un demi-tour.

### 27.3 `NOM.config.json` : les réglages de la page

`glb2html.py` l'écrit ; la page le relit à chaque ouverture, donc **F5 suffit** après une modification. On le change de préférence avec `glb2html.py --update -o NOM.html --shared-shell` suivi des options voulues : seuls les champs des options données changent, le reste est gardé, y compris un champ ajouté à la main. On peut aussi le modifier à la main ; une erreur de syntaxe (virgule oubliée, guillemet manquant) empêche alors la page de s'ouvrir.

**Mer et ciel**

| Champ            | Type          | Défaut    | Ce qu'il fait                                                                                | Option                 |
| ---------------- | ------------- | --------- | -------------------------------------------------------------------------------------------- | ---------------------- |
| `sea`            | oui / non     | `true`    | affiche la mer                                                                               | `--sea`, `--no-sea`    |
| `seaY`           | nombre        | `-50`     | hauteur de la mer en mètres (de -150 à 60)                                                   | `--sea-y`              |
| `seaColor`       | couleur       | `3840729` | couleur de la mer (`#3A9AD9`)                                                                | `--sea-color`          |
| `skyColor`       | couleur       | `8900331` | couleur du ciel et du brouillard (`#87CEEB`)                                                 | `--sky-color`          |
| `anim`           | oui / non     | `false`   | vagues animées ; sinon la mer est fixe                                                       | `--anim`, `--no-anim`  |
| `wave`           | nombre        | `0.5`     | hauteur des vagues (de 0 à 10)                                                               | `--wave`               |
| `seaSegments`    | nombre entier | `400`     | finesse de la surface de la mer (de 8 à 1000) ; ne compte qu'avec les vagues animées         | `--sea-segments`       |
| `seaSize`        | nombre        | `4000`    | largeur de la mer en mètres                                                                  | —                      |
| `hole`           | nombre        | `180`     | rayon en mètres de la **zone calme** autour de l'île, où les vagues s'effacent (de 30 à 600) | `--hole`               |
| `holeFade`       | nombre        | `60`      | largeur de la transition entre la zone calme et les vagues                                   | `--hole-fade`          |
| `holeX`, `holeZ` | nombre        | `0`       | centre de la zone calme                                                                      | `--hole-x`, `--hole-z` |

**Région et caméra de départ**

| Champ            | Type               | Défaut         | Ce qu'il fait                                                                                           | Option                      |
| ---------------- | ------------------ | -------------- | ------------------------------------------------------------------------------------------------------- | --------------------------- |
| `rotate`         | nombre entier      | `0`            | rotation de la région : 0, 90, 180 ou 270 degrés                                                        | `--rotate`                  |
| `target`         | liste de 3 nombres | `[0, 15, 0]`   | point regardé par la caméra à l'ouverture                                                               | `--target`                  |
| `targetExplicit` | oui / non          | `false`        | `true` quand `--target` a été donné : la page garde ce cadrage au lieu de partir de l'arrivée `default` | `--target`                  |
| `camDir`         | liste de 3 nombres | `[0, 0.25, 1]` | direction d'où regarde la caméra                                                                        | `--cam-dir`                 |
| `zoom`           | nombre             | `1`            | recul de la caméra (1 = cadrage automatique, 2 = deux fois plus loin)                                   | `--zoom`                    |
| `compass`        | oui / non          | `true`         | boussole en haut de la page                                                                             | `--compass`, `--no-compass` |
| `northDeg`       | nombre             | `0`            | décalage en degrés de la boussole, pour un modèle qui ne vient pas d'OpenSim                            | `--north`                   |

**Affichage**

| Champ           | Type      | Défaut             | Ce qu'il fait                                                                                                                                      | Option                    |
| --------------- | --------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| `retina`        | oui / non | `false`            | haute résolution (plus net, environ quatre fois plus lourd)                                                                                        | `--retina`, `--no-retina` |
| `light`         | oui / non | `false`            | la page s'ouvre en rendu léger tant que le visiteur n'a rien choisi (§ 26)                                                                         | `--light`, `--no-light`   |
| `foliageCutout` | nombre    | `0.12`             | seuil de transparence des feuillages (de 0 à 0.5) : plus haut, les bords des feuilles sont plus découpés                                           | `--foliage-cutout`        |
| `names`         | oui / non | `false`            | affiche le nom de l'élément cliqué                                                                                                                 | `--names`, `--no-names`   |
| `panel`         | oui / non | `true`             | bouton Réglages pour les visiteurs                                                                                                                 | `--panel`, `--no-panel`   |
| `libUrl`        | texte     | `""`               | dossier ou adresse de `lib` (three.js) quand il n'est pas à côté de la page ; `--update` l'aligne sur la ligne `const LIB` de la coquille (§ 28.5) | `--lib-url`               |
| `version`       | texte     | version de l'outil | version de `glb2html.py` qui a écrit le fichier ; `--update` la remplace                                                                           | —                         |

**Promenade**

| Champ        | Type      | Défaut          | Ce qu'il fait                                                                                                                              | Option                |
| ------------ | --------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------- |
| `walk`       | oui / non | `true`          | mode promenade (touche F)                                                                                                                  | `--walk`, `--no-walk` |
| `fly`        | oui / non | `true`          | vol en promenade                                                                                                                           | `--fly`, `--no-fly`   |
| `eyeHeight`  | nombre    | `1.7`           | hauteur des yeux en mètres                                                                                                                 | `--eye-height`        |
| `walkSpeed`  | nombre    | `3.5`           | vitesse de marche en mètres par seconde (en courant : 2,2 fois plus)                                                                       | `--walk-speed`        |
| `walkIgnore` | texte     | `"door, porte"` | objets que l'on traverse, séparés par des virgules : `door` = tout nom qui commence par ce mot, `=mesh_346_5` = ce nom exact, `""` = aucun | `--walk-ignore`       |

**Visiteurs et chat**

| Champ         | Type      | Défaut                             | Ce qu'il fait                                                                                  | Option                        |
| ------------- | --------- | ---------------------------------- | ---------------------------------------------------------------------------------------------- | ----------------------------- |
| `presenceUrl` | texte     | `""`                               | adresse du serveur de présence (`ws://...` ou `wss://...`) ; vide = seul, sans avatars ni chat | `--presence-url`              |
| `room`        | texte     | nom de la page                     | salon de présence : les visiteurs d'un même salon se voient                                    | `--room`                      |
| `spectate`    | oui / non | `true` si `presenceUrl` est rempli | voir les promeneurs depuis la vue globale                                                      | `--spectate`, `--no-spectate` |
| `chat`        | oui / non | `true`                             | chat entre visiteurs (il faut un serveur de présence)                                          | `--chat`, `--no-chat`         |
| `chatFade`    | nombre    | `0`                                | secondes avant que les messages et bulles disparaissent ; 0 = ils restent                      | `--chat-fade`                 |

**Zones**

| Champ          | Type      | Défaut     | Ce qu'il fait                                                                                                        | Option                              |
| -------------- | --------- | ---------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| `profile`      | texte     | `"public"` | `"public"` : les zones privées ne sont pas affichées ; `"private"` : toutes les zones le sont                        | `--profile`                         |
| `zones`        | liste     | `[]`       | toujours vide dans ce fichier : les zones sont dans `NOM.zones.json`                                                 | —                                   |
| `zonesLive`    | texte     | `""`       | toujours vide dans ce fichier (sert aux pages autonomes, `--zones-live`)                                             | `--zones-live`                      |
| `zoneMarker`   | texte     | `"dot"`    | repère des portails et zones libres : `"dot"` petit disque, `"range"` anneau au rayon réel de la zone, `"none"` rien | `--zone-marker`                     |
| `zoneCone`     | oui / non | `true`     | petit cône au-dessus des portails (touche T)                                                                         | `--zone-cone`, `--no-zone-cone`     |
| `showSpawns`   | oui / non | `false`    | dessine aussi les arrivées                                                                                           | `--show-spawns`, `--no-show-spawns` |
| `zoneInfoDist` | nombre    | `150`      | distance en mètres (de 5 à 500) jusqu'où les zones répondent au survol et au clic en promenade                       | `--zone-info-dist`                  |

**Carte des mondes**

| Champ    | Type  | Défaut | Ce qu'il fait                                                                     | Option                |
| -------- | ----- | ------ | --------------------------------------------------------------------------------- | --------------------- |
| `map`    | liste | `[]`   | carte intégrée à la page : mêmes fiches que `regions.json` (§ 27.6)               | `--map`, `--register` |
| `mapUrl` | texte | `""`   | adresse(s) de `regions.json` relues à chaque ouverture, séparées par des virgules | `--map-url`           |

**Région en tuiles** : ces six champs n'existent que pour une région découpée par `glb2tiles.py`. Pour une région faite d'un seul fichier `.glb`, il faut les **retirer** de l'exemple, sinon la page cherche des tuiles.

| Champ              | Type          | Défaut    | Ce qu'il fait                                                           | Option                 |
| ------------------ | ------------- | --------- | ----------------------------------------------------------------------- | ---------------------- |
| `tiles`            | texte         | —         | nom de l'index des tuiles, par exemple `"Region.tiles.json"`            | `--tiles`              |
| `tileRadius`       | nombre        | `150`     | rayon en mètres autour de l'avatar dans lequel les tuiles sont chargées | `--tile-radius`        |
| `tileMargin`       | nombre        | `60`      | marge en mètres au-delà de ce rayon avant qu'une tuile soit retirée     | `--tile-margin`        |
| `tileMaxMB`        | nombre        | `200`     | mégaoctets de tuiles chargées en même temps, au plus                    | `--tile-max-mb`        |
| `tileMaxTriangles` | nombre entier | `8000000` | triangles de tuiles chargées en même temps, au plus                     | `--tile-max-triangles` |
| `tileConcurrency`  | nombre entier | `4`       | téléchargements de tuiles en même temps                                 | `--tile-concurrency`   |

Les réglages du rendu léger choisis par un visiteur (résolution, images par seconde, vue d'ensemble seule, anticrénelage) sont gardés **par son navigateur**, pas dans ce fichier : la page ignore `pixelScale`, `fpsMax`, `ovOnly` ou `antialias` écrits ici.

### 27.4 `NOM.zones.json` : les zones

Une **liste** de zones, relue à chaque ouverture de la page. Chaque zone a les champs ci-dessous ; un champ absent prend sa valeur par défaut, et une valeur hors des limites est ramenée dans les limites.

Il existe **quatre sortes** de zones (champ `type`) : `"spawn"` (arrivée), `"portal"` (portail), `"url"` (lien web) et `"ha"` (commande). « Privée », « liée à un objet » et « nom affiché » ne sont pas des sortes : ce sont des cases (`private`, `mesh`, `showName`) valables pour toutes les sortes.

| Champ         | Type      | Défaut        | Ce qu'il fait                                                                                                                                            |
| ------------- | --------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`          | texte     | `z1`, `z2`... | nom court et unique : lettres minuscules, chiffres, `-` et `_`, 40 caractères au plus. L'arrivée `default` est le point d'entrée de la région            |
| `type`        | texte     | `"portal"`    | `"spawn"`, `"portal"`, `"url"` ou `"ha"`                                                                                                                 |
| `label`       | texte     | `""`          | nom affiché (infobulle, panneau), 60 caractères au plus                                                                                                  |
| `x`, `y`, `z` | nombre    | `0`           | position en mètres                                                                                                                                       |
| `yaw`         | nombre    | `0`           | orientation en radians : sens du regard à l'arrivée, ou face du panneau                                                                                  |
| `shape`       | texte     | `"ring"`      | `"ring"` (anneau au sol) ou `"board"` (panneau sur un poteau)                                                                                            |
| `trigger`     | texte     | `"click"`     | portails seulement : `"click"` (clic ou E), `"enter"` (en marchant dedans) ou `"both"` (les deux). Les autres sortes sont toujours `"click"`             |
| `radius`      | nombre    | `2`           | rayon de la zone en mètres (de 0.5 à 50)                                                                                                                 |
| `w`, `h`      | nombre    | `2.4`, `1.2`  | largeur et hauteur du panneau en mètres                                                                                                                  |
| `target`      | texte     | `""`          | portail : adresse de la région d'arrivée, ou vide pour un point de la même région ; lien : adresse de la page web ; commande : adresse appelée           |
| `spawn`       | texte     | `""`          | portail : `id` de l'arrivée visée (vide = `default`)                                                                                                     |
| `confirm`     | oui / non | `false`       | demande une confirmation avant d'agir                                                                                                                    |
| `private`     | oui / non | `false`       | zone privée : absente des pages publiques (profil `public`)                                                                                              |
| `showName`    | oui / non | `false`       | écrit le `label` au-dessus de la zone en promenade                                                                                                       |
| `mesh`        | texte     | `""`          | zone **liée à un objet** du modèle : son nom, ou `nom#numéro` quand plusieurs objets portent ce nom ; l'objet devient cliquable. Jamais pour une arrivée |

L'exemple contient huit zones, une de chaque cas :

| `id`              | Sorte    | Ce qu'elle montre                                                                              |
| ----------------- | -------- | ---------------------------------------------------------------------------------------------- |
| `default`         | arrivée  | point d'entrée de la région                                                                    |
| `gallery`         | arrivée  | seconde arrivée, visée par un portail                                                          |
| `to-gallery`      | portail  | vers un autre point de la même région (`target` vide, `spawn` = `gallery`), en marchant dedans |
| `to-other-region` | portail  | vers une autre région, panneau, clic ou marche, avec confirmation                              |
| `website`         | lien     | ouvre une page web, panneau                                                                    |
| `light-on`        | commande | appel d'une adresse (par exemple un webhook Home Assistant), privée, avec confirmation         |
| `door-info`       | lien     | liée à l'objet `Door#2` du modèle                                                              |
| `back-home`       | portail  | nom affiché au-dessus de la zone (`showName`)                                                  |

Dans une région en tuiles, une zone liée retrouve son objet grâce à l'étiquette `extras.ref` que `glb2tiles.py` écrit dans les objets des tuiles. Cette étiquette est dans les fichiers `.glb` des tuiles, **pas** dans `NOM.zones.json`.

### 27.5 `default.json` : la région par défaut

| Champ    | Type  | Défaut | Ce qu'il fait                                               | Option      |
| -------- | ----- | ------ | ----------------------------------------------------------- | ----------- |
| `region` | texte | —      | région ouverte quand l'adresse n'a pas de `?region=` (§ 16) | `--default` |

### 27.6 `regions.json` : la carte des mondes

Une **liste** de régions (forme simple), ou, depuis la v47, un **objet** avec un en-tête : `{"showUrl": false, "regions": [ ... ]}`. Les deux formes sont lues partout (carte `carte.html`, carte autonome, carte ouverte par M, coquille). Une fiche sans `name` ou sans `url` est ignorée.

| Champ de l'en-tête | Type    | Défaut  | Ce qu'il fait                                                                                                                                                             | Option |
| ------------------ | ------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| `showUrl`          | booléen | `false` | affiche l'adresse sous chaque tuile de la page carte ; la case de la page carte, une fois cochée ou décochée par le visiteur, l'emporte (choix retenu par son navigateur) | —      |
| `regions`          | liste   | —       | les fiches de régions (tableau suivant)                                                                                                                                   | —      |

`--register` et `--scan-sites` gardent l'en-tête et la forme du fichier (liste ou objet). Le viewer aussi depuis la v50 : « Importer regions.json » accepte les deux formes, « Exporter regions.json » rend la forme importée avec son en-tête, et chaque fiche garde tous ses champs (§ 33).

| Champ      | Type          | Défaut      | Ce qu'il fait                                                                                     | Option           |
| ---------- | ------------- | ----------- | ------------------------------------------------------------------------------------------------- | ---------------- |
| `id`       | texte         | tiré du nom | identifiant court, unique dans la carte                                                           | —                |
| `name`     | texte         | —           | nom affiché, 60 caractères au plus                                                                | `--region-name`  |
| `url`      | texte         | —           | adresse de la page : complète (`https://...`) ou relative (`index.html?region=Region`)            | `--region-url`   |
| `x`, `y`   | nombre entier | `0`         | place sur la grille, comme dans OpenSim (x vers l'est, y vers le nord)                            | `--region-xy`    |
| `spawn`    | texte         | `""`        | arrivée utilisée en venant de la carte (vide = `default`)                                         | `--region-spawn` |
| `presence` | texte         | `""`        | serveur de présence de cette région, s'il n'est pas celui de la page (pour compter les visiteurs) | —                |
| `room`     | texte         | `""`        | salon de présence de cette région                                                                 | `--room`         |
| `thumb`    | texte         | `""`        | vignette : image intégrée (`data:image/...`) ou adresse d'une image                               | `--thumb`        |

### 27.7 `NOM.tiles.json` : l'index des tuiles

`glb2tiles.py` l'écrit ; il ne se modifie **pas à la main**. La page n'en lit que quelques champs : `tiles` (pour chaque tuile `file`, `min`, `max`, `bytes`, `triangles`), `nodeRefs` et `overview.file`. Les autres servent au compte rendu.

| Champ            | Type            | Ce qu'il contient                                                                                                                                                                                                                                                                             |
| ---------------- | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `version`        | nombre entier   | version du format (1)                                                                                                                                                                                                                                                                         |
| `generator`      | texte           | outil et version qui ont écrit le fichier                                                                                                                                                                                                                                                     |
| `source`         | texte           | nom du `.glb` découpé                                                                                                                                                                                                                                                                         |
| `extent`         | objet           | boîte de toute la région : `min` et `max`, chacun x, y, z                                                                                                                                                                                                                                     |
| `params`         | objet           | réglages du découpage : `budgetMB`, `budgetTriangles`, `minCell`, `wholeWeightMB`, `wholeExtent`, `thresholdMB`, `thresholdTriangles`, `outlier` (options `--budget`, `--budget-triangles`, `--min`, `--whole-weight`, `--whole-extent`, `--threshold`, `--threshold-triangles`, `--outlier`) |
| `warnings`       | liste de textes | avertissements du découpage                                                                                                                                                                                                                                                                   |
| `roots`          | objet           | objets gardés entiers (`whole`) et répartis (`split`)                                                                                                                                                                                                                                         |
| `duplication`    | nombre          | géométrie de toutes les tuiles divisée par celle du modèle (1 = rien en double)                                                                                                                                                                                                               |
| `nodeRefs`       | nombre          | 1 si les objets portent `extras.ref` (zones liées possibles), 0 avec `--no-refs`                                                                                                                                                                                                              |
| `replacedImages` | objet           | images illisibles remplacées par du gris : `distinct`, `occurrences`, `grey`                                                                                                                                                                                                                  |
| `tiles`          | liste           | une fiche par tuile (ci-dessous)                                                                                                                                                                                                                                                              |
| `excluded`       | objet           | seulement avec `--exclude` : motifs, limites, nombre d'objets retirés, triangles et octets gagnés, noms les plus fréquents                                                                                                                                                                    |
| `overview`       | objet           | seulement avec la vue d'ensemble : `file` (le `.glb`), poids, triangles, objets gardés et omis, durée, `params` (`budgetMB`, `budgetTriangles`, `minExtent`, `maxExtent`, `resolution`, `terrainStep`)                                                                                        |

Chaque fiche de `tiles` :

| Champ                         | Type               | Ce qu'il contient                               |
| ----------------------------- | ------------------ | ----------------------------------------------- |
| `file`                        | texte              | chemin du `.glb` de la tuile, relatif à l'index |
| `level`, `i`, `j`             | nombre entier      | niveau et place de la tuile dans la grille      |
| `min`, `max`                  | liste de 3 nombres | boîte de la tuile                               |
| `instances`                   | nombre entier      | nombre d'objets dans la tuile                   |
| `triangles`                   | nombre entier      | triangles de la tuile                           |
| `bytes`                       | nombre entier      | poids du fichier                                |
| `geometryBytes`, `imageBytes` | nombre entier      | dont géométrie, dont images                     |
| `replacedImages`              | nombre entier      | images remplacées par du gris dans cette tuile  |

### 27.8 `NOM.reglages.json` : l'état de travail du viewer

Écrit par le bouton « Enregistrer dans un fichier » du viewer, relu par « Charger un fichier » et par `glb2html.py --settings`. Contrairement à `NOM.config.json`, il est **imbriqué** (§ 16).

| Champ            | Type          | Ce qu'il contient                                                                                                             |
| ---------------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `v`              | nombre entier | version du format : toujours `1`                                                                                              |
| `file`           | texte         | nom du `.glb` ouvert dans le viewer                                                                                           |
| `saved`          | texte         | date et heure de l'enregistrement                                                                                             |
| `cfg`            | objet         | les réglages : mêmes noms et même sens que dans `NOM.config.json` (§ 27.3), plus cinq réglages propres au viewer (ci-dessous) |
| `zones`          | liste         | toutes les zones, privées comprises (format du § 27.4)                                                                        |
| `camera`         | objet         | `camDir`, `target`, `zoom` : le cadrage choisi dans le viewer                                                                 |
| `profile`        | texte         | `"public"` ou `"private"` (menu « Profil d'export »)                                                                          |
| `thisReg`        | objet         | fiche de cette région pour la carte : `name`, `url`, `x`, `y`, `spawn`, `thumb` (§ 27.6)                                      |
| `cmd`            | objet         | champs du récapitulatif de commande : `script`, `glb`, `dest`, `mapPage`                                                      |
| `targetExplicit` | oui / non     | la cible de la caméra a été déplacée à la main                                                                                |

Les cinq réglages de `cfg` propres au viewer : `pixelScale`, `fpsMax` et `ovOnly` (rendu léger, essais dans le viewer), `guide` (guide de la zone calme affiché dans le viewer) et `ignoreViz` (objets traversés montrés en fil de fer). `--settings` ne les reprend pas.

### 27.9 `disposition.json` : la place des fenêtres

Écrit par Réglages, « Enregistrer » (section « Disposition des fenêtres »), relu par « Charger » (§ 25).

| Champ    | Type          | Ce qu'il contient                                                                                                                                                                                                                                                                                                     |
| -------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app`    | texte         | toujours `"web3d-layout"` : un autre fichier est refusé                                                                                                                                                                                                                                                               |
| `v`      | nombre entier | version du format : `1`                                                                                                                                                                                                                                                                                               |
| `layout` | objet         | `wins` : pour chaque fenêtre (`H` aide, `I` informations / état, `L` arrivées), `pile` (`"L"` pile de gauche, `"R"` pile de droite, `"F"` libre), `home` (`"L"` ou `"R"`, la pile où la fenêtre revient au double-clic), et pour une fenêtre libre `x`, `y` en pixels ; `order` : ordre des fenêtres dans chaque pile |
| `ls`     | objet         | état des fenêtres : `glb2html_help`, `glb2html_state`, `glb2html_spawn` (`"1"` affichée, `"0"` masquée), `glb2html_helpFold`, `glb2html_stateFold`, `glb2html_spawnFold` (`"1"` repliée), `glb2html_helpW`, `glb2html_stateW`, `glb2html_spawnW` (largeur en pixels)                                                  |

### 27.10 Fichiers du serveur de présence

Le serveur les écrit lui-même ; on ne les modifie à la main que serveur arrêté. Les valeurs « hachées » sont des empreintes : on ne peut pas retrouver la clé ou l'adresse IP d'origine, ce qui protège les visiteurs. Les empreintes des exemples sont fabriquées et ne correspondent à personne.

**`presence_identities.json`** (option `--identities`) : les pseudos réservés.

| Champ   | Type  | Ce qu'il contient                                                                                                                                                                                                            |
| ------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `salt`  | texte | « sel » secret tiré au hasard au premier démarrage, mélangé aux clés avant de les hacher. Le changer libère tous les pseudos                                                                                                 |
| `names` | objet | pour chaque pseudo simplifié (minuscules, sans accents ni espaces), l'empreinte de la clé du navigateur qui le possède                                                                                                       |
| `users` | objet | pour chaque empreinte : `name` (pseudo tel qu'écrit), `key` (pseudo simplifié), `first` et `last` (première et dernière venue, en secondes depuis 1970). Un pseudo inutilisé depuis `--name-ttl-days` jours (365) est libéré |

**`presence_bans.json`** (option `--bans`) : une liste de bannissements.

| Champ    | Type   | Ce qu'il contient                                                                                                                       |
| -------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| `key`    | texte  | empreinte de la clé du navigateur banni (vide pour un visiteur sans clé)                                                                |
| `ip`     | texte  | empreinte de son adresse IP                                                                                                             |
| `until`  | nombre | fin du bannissement en secondes depuis 1970 ; `0` = définitif. Un bannissement terminé est retiré du fichier à la vérification suivante |
| `name`   | texte  | pseudo au moment du bannissement                                                                                                        |
| `reason` | texte  | raison donnée                                                                                                                           |
| `added`  | nombre | date du bannissement en secondes depuis 1970                                                                                            |

**Historique du chat** (option `--history-file`) : ce n'est pas un fichier JSON d'un seul bloc, mais **un message par ligne**, chaque ligne étant un petit JSON. Jamais d'adresse IP.

| Champ  | Type          | Ce qu'il contient                                                           |
| ------ | ------------- | --------------------------------------------------------------------------- |
| `n`    | nombre entier | numéro du message                                                           |
| `t`    | nombre entier | heure en secondes depuis 1970 (c'est elle qui compte pour `--history-days`) |
| `d`    | texte         | la même heure lisible (jj/mm/aaaa hh:mm:ss)                                 |
| `room` | texte         | salon                                                                       |
| `name` | texte         | pseudo                                                                      |
| `text` | texte         | message                                                                     |

Les messages plus vieux que `--history-days` jours (30 par défaut) sont retirés au démarrage ; avec `--history-days 0`, rien n'est retiré.

**Journal des visites** (option `--visits`, v48) : comme l'historique, **une visite par ligne**, chaque ligne étant un petit JSON. Jamais d'adresse IP.

| Champ   | Type          | Ce qu'il contient                                                                                                                                                |
| ------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `room`  | texte         | salon                                                                                                                                                            |
| `start` | nombre entier | arrivée en secondes depuis 1970 (c'est elle qui compte pour `--visits-days`)                                                                                     |
| `dur`   | nombre entier | durée de la connexion en secondes                                                                                                                                |
| `walk`  | nombre entier | secondes passées en promenade                                                                                                                                    |
| `v`     | texte         | empreinte du navigateur (10 caractères), différente de la clé du journal `presence.log` : sert à compter les visiteurs distincts et à fusionner les reconnexions |
| `name`  | texte         | pseudo du promeneur, seulement avec `--visits-names`                                                                                                             |

Les visites plus vieilles que `--visits-days` jours (365 par défaut) sont retirées au démarrage puis toutes les 6 heures, avec les lignes illisibles ; avec `--visits-days 0`, rien n'est retiré.

**`presence_visits_keys.json`** (option `--visits-keys`, v48) : les clés du journal des visites, écrites par la commande `visits-key`.

| Champ   | Type  | Ce qu'il contient                                                                                                                                                                                                           |
| ------- | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `rooms` | objet | pour chaque salon : `salt` (sel tiré au hasard), `hash` (empreinte SHA-256 du sel suivi de la clé en majuscules, sans tirets ni espaces), `added` (création, en secondes depuis 1970). La clé elle-même n'est jamais écrite |

**`presence_creators.json`** (option `--creators`, v51) : les créateurs accueillis, écrit à la main et relu sans relancer le serveur (§ 34). Un objet `{"creators": [...]}` ; pour chaque créateur :

| Champ        | Type            | Ce qu'il contient                                                                                                                                            |
| ------------ | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `id`         | texte           | identifiant unique : lettres, chiffres, `-` et `_`, 32 au plus                                                                                               |
| `prefix`     | texte           | préfixe de ses salons, sans point ; absent = `id` ; `""` = l'hôte, qui garde tous les salons n'appartenant à aucun créateur (une seule entrée)               |
| `origins`    | liste de textes | origines de ses pages (`https://alice.example`, `null` pour une page ouverte depuis le disque et pour le viewer, écrit entre guillemets ; sans guillemets, il est ignoré avec un avertissement) ; une origine n'appartient qu'à un créateur |
| `maxWalkers` | nombre entier   | promeneurs au plus sur tous ses salons ; `0` ou absent = seulement les limites générales                                                                     |
| `maxRooms`   | nombre entier   | salons ouverts en même temps au plus ; `0` ou absent = sans limite propre                                                                                    |
| `off`        | booléen         | `true` : suspendu, ses nouvelles connexions sont refusées                                                                                                    |
| `note`       | texte           | note libre de l'hôte, ignorée par le serveur                                                                                                                 |

### 27.11 Noms en anglais depuis la v43

Pour que tous les noms soient dans la même langue, la v43 a mis en anglais les derniers noms français : options des outils, valeurs dans les fichiers JSON et paramètres d'adresse. **Les anciens noms restent acceptés** : les commandes, les fichiers et les liens déjà écrits continuent de marcher. Un ancien nom est remplacé par le nouveau à la lecture ; quand un outil réécrit un fichier, il écrit le nouveau. `--update` garde tel quel un champ que l'on ne change pas : un ancien `tileMaxMo` reste donc dans `NOM.config.json`, et la page le lit toujours.

| Où                                     | Ancien nom                                                         | Nouveau nom                                                    |
| -------------------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------- |
| `glb2html.py`                          | `--maj`                                                            | `--update`                                                     |
| `glb2html.py`                          | `--tile-max-mo`, `--tile-max-tri`                                  | `--tile-max-mb`, `--tile-max-triangles`                        |
| `glb2html.py`                          | `--zone-marker discret`, `portee`, `aucun`                         | `--zone-marker dot`, `range`, `none`                           |
| `glb2html.py`                          | `--profile perso`                                                  | `--profile private`                                            |
| `glb2tiles.py`                         | `--budget-tri`, `--ov-budget-tri`                                  | `--budget-triangles`, `--ov-budget-triangles`                  |
| `glb2tiles.py`                         | `--entier-poids`, `--entier-etendue`                               | `--whole-weight`, `--whole-extent`                             |
| `glb2tiles.py`                         | `--seuil`, `--seuil-tri`, `--aberrant`                             | `--threshold`, `--threshold-triangles`, `--outlier`            |
| `glb2tiles.py`                         | `--exclure`, `--exclure-max-tri`, `--exclure-max-meshes`           | `--exclude`, `--exclude-max-triangles`, `--exclude-max-meshes` |
| `glb2tiles.py`                         | `--sans-references`, `--sans-vue-ensemble`, `--vue-ensemble-seule` | `--no-refs`, `--no-overview`, `--overview-only`                |
| `glb2tiles.py`                         | `--ov-seuil`, `--ov-seuil-max`, `--ov-terrain-pas`                 | `--ov-threshold`, `--ov-threshold-max`, `--ov-terrain-step`    |
| `glb2tiles.py`                         | `--bloc`, `--forcer`, `--sortie`                                   | `--block`, `--force`, `--output`                               |
| `oar2glb.py`                           | `--reperes`, `--terrain-seul`, `--sortie`                          | `--markers`, `--terrain-only`, `--output`                      |
| `oar2glb.py`                           | `--terrain oui`, `--terrain non`                                   | `--terrain yes`, `--terrain no`                                |
| `glb-stats.py`                         | `--bloc`, `--sortie`                                               | `--block`, `--output`                                          |
| `gen_reference.py` (v44)               | `--outils`, `--sortie`, `--verifier`                               | `--tools`, `--output`, `--check`                               |
| `verif_trad.py` (v44)                  | `--glossaire`                                                      | `--glossary`                                                   |
| `NOM.config.json`                      | `tileMaxMo`, `tileMaxTri`                                          | `tileMaxMB`, `tileMaxTriangles`                                |
| `NOM.config.json`, `NOM.reglages.json` | `zoneMarker` : `discret`, `portee`, `aucun`                        | `dot`, `range`, `none`                                         |
| `NOM.config.json`, `NOM.reglages.json` | `profile` : `perso`                                                | `private`                                                      |
| `NOM.tiles.json`                       | `budgetMo`, `wholeWeightMo`, `thresholdMo`                         | `budgetMB`, `wholeWeightMB`, `thresholdMB`                     |
| adresse de la page                     | `?rayon=`                                                          | `?radius=`                                                     |
| adresse du viewer                      | `?tuiles=`                                                         | `?tiles=`                                                      |

Les deux outils de développement (`gen_reference.py`, `verif_trad.py`) ont suivi en v44, et les messages de `--update` commencent par `[update]`. Restent tels quels : `--analyse` (aussi de l'anglais britannique) et les valeurs qui sont des noms d'objets, comme `door, porte`. Dans l'aide des outils, les noms d'exemple des valeurs sont aussi en anglais (`FILE`, `PATH`, `NAME`, `DEGREES`, `SHELL.html`). L'historique (`CHANGELOG.md`, `HISTORIQUE.md`) garde les noms de l'époque.

## 28. Nouveautés de la v45 (24/10/2026)

### 28.1 La page dit pourquoi la présence s'est coupée

Quand la connexion au serveur de présence se ferme, la ligne de présence (fenêtre Informations / État, panneau du viewer) ne dit plus toujours « serveur injoignable » : elle donne ce que le navigateur sait.

- **la connexion ne s'est jamais ouverte** : « connexion jamais établie (adresse, port ou pare-feu à vérifier) » ;
- **la connexion s'était ouverte, puis le serveur ou le réseau l'a coupée** : « connexion ouverte puis fermée (code N) », suivi de la raison envoyée par le serveur quand il en donne une ;
- **le navigateur a refusé de créer la connexion** (page en https avec une adresse `ws://`, ou port interdit) : « refusé par le navigateur ».

Limite : le navigateur ne donne jamais la cause d'une connexion qui ne s'ouvre pas (code 1006, sans raison). La page ne peut donc pas distinguer un nom introuvable, un port fermé, un pare-feu ou un blocage du navigateur ; seul un serveur qui coupe une connexion déjà ouverte fournit un code et une raison.

### 28.2 Diagnostic

« Copier le diagnostic » ajoute la ligne « Connexion de présence » : la connexion s'est-elle ouverte (oui ou non), dernier code de fermeture et dernière raison. Les adresses restent remplacées par `ADRESSE`.

### 28.3 Test de la présence

`tests/v45.py` : serveur absent, serveur qui ferme avec un code et une raison, constructeur refusé par le navigateur, anglais, viewer.

### 28.4 Une seule ligne pour le dossier `lib`

La coquille (le fichier `index.html` commun à toutes les régions d'un dossier) commence par une ligne `const LIB = './lib';` : c'est **la seule ligne à modifier** pour mettre le dossier `lib` ailleurs (par exemple `'../lib'`, ou une adresse `https://…/lib`). La table d'import de three.js et le chemin des décodeurs Draco sont construits à partir de cette ligne par un petit script exécuté avant tout module. Valeurs acceptées : les mêmes que `--lib-url` (§ 22.8) ; une valeur refusée est ignorée.

### 28.5 `--update` garde la ligne

Ordre de priorité du dossier `lib` : l'option `--lib-url` si elle est donnée ; la ligne `const LIB` d'une coquille existante si elle n'est pas `./lib` ; la clé `libUrl` de `NOM.config.json` ; sinon `./lib`. Quand la ligne de la coquille l'emporte, `--update` l'écrit dans son compte rendu et aligne `libUrl`. Une coquille enregistrée avec des fins de ligne Windows (CRLF) est reconnue identique. Une nouvelle région créée dans un dossier dont la coquille a été modifiée à la main garde le même dossier `lib`, sans avertissement.

### 28.6 `dist\index.html`

`python build.py` dépose maintenant la coquille prête dans `dist\index.html` (dossier `lib` : `./lib`), identique octet pour octet à celle que `glb2html.py` écrit. Elle peut être copiée dans un dossier de régions à la place de `--update` ; si le dossier `lib` est ailleurs, il faut reporter la ligne `const LIB`. `--update` reste nécessaire pour mettre à jour la configuration d'une région.

### 28.7 Navigateurs

Essayé dans Chromium (`tests/v45_lib.py`). **Non essayé : Firefox et Safari.** Le fichier `tests/essai_importmap.html` (à ouvrir dans le navigateur ; résultat écrit en toutes lettres) vérifie qu'un navigateur accepte une table d'import construite par un script ; si l'essai échoue dans un navigateur, la coquille ne démarre pas dedans.

### 28.8 Test de la coquille

`tests/v45_lib.py` : ligne unique, plus de balise d'import dans la coquille, `dist\index.html` identique, page autonome inchangée, démarrage dans Chromium avec `./lib` puis avec `../lib` (une ligne changée), `--update` qui garde la ligne (message, config alignée, aucune copie datée), CRLF, valeur refusée, `--lib-url` prioritaire, nouvelle région, page d'essai.

## 29. Nouveautés de la v46 (25/10/2026)

### 29.1 Ligne d'état

Une ligne toujours visible donne, sans ouvrir la fenêtre Informations : le **mode** écrit en gras (« Promenade » ou « Vue globale »), puis en promenade l'allure (à pied, en vol, course), la vue (subjective, troisième personne, caméra libre) et la position `x y z` ; en vue globale, la cible. Elle est en bas au centre ; sur un écran de moins de 1361 px de large, et sur un écran tactile, elle passe en haut, sous la boussole (et sous le bloc du pseudo). Aucune information n'y est portée par une couleur.

### 29.2 Flèches à l'écran

Un pavé de 3 x 3 boutons, au-dessus de la ligne d'état, se clique à la souris ou se touche du doigt. **Appui maintenu = touche tenue** : le mouvement dure tant que le bouton est enfoncé.

En promenade (les flèches reprennent les touches du clavier : la marche ne change pas) :

| Rangée | Gauche                               | Milieu                                                | Droite                                      |
| ------ | ------------------------------------ | ----------------------------------------------------- | ------------------------------------------- |
| haut   | tourner à gauche (←)                 | avancer (Z ou W, ↑)                                   | tourner à droite (→)                        |
| milieu | pas de côté à gauche (Q ou A)        | **Courir** : un clic l'allume, un clic l'éteint (Maj) | pas de côté à droite (D)                    |
| bas    | monter, en vol seulement (Page Haut) | reculer (S, ↓)                                        | descendre, en vol seulement (Page Bas ou C) |

En vue globale :

| Rangée | Gauche                   | Milieu                                     | Droite                   |
| ------ | ------------------------ | ------------------------------------------ | ------------------------ |
| haut   | tourner la vue à gauche  | déplacer la vue en avant                   | tourner la vue à droite  |
| milieu | déplacer la vue à gauche | **recentrer la vue** (cadrage d'ouverture) | déplacer la vue à droite |
| bas    | éloigner (−)             | déplacer la vue en arrière                 | rapprocher (+)           |

Déplacer et rapprocher ne font pas la même chose : **déplacer** fait glisser la caméra et le point visé ensemble, à hauteur et distance constantes (le paysage défile, les tuiles se chargent autour du nouveau point) ; **rapprocher / éloigner** garde le point visé et change seulement la distance de la caméra, comme la molette.

Le centre du pavé remplace le bouton « Recentrer la vue » : ce bouton ne revient dans la barre que si les flèches sont cachées. En promenade, la souris capturée (par **G** ou le bouton) ne peut pas cliquer les flèches : **Échap** ou **G** la libère, **G** ou le bouton « Capturer la souris » la reprend.

L'invite de zone et la proposition de rendu léger remontent au-dessus du pavé.

### 29.3 Cacher ou montrer les flèches

Trois moyens, qui font la même chose et sont retenus par le navigateur : la touche **K** (même place en AZERTY et en QWERTY), le bouton « Flèches (K) » de la barre (« Flèches (K) : cachées » quand elles le sont ; sur écran tactile, le bouton « Flèches » de la colonne), et la case « Flèches à l'écran (K) » des Réglages. Les flèches sont affichées par défaut.

### 29.4 Écran tactile (téléphone, tablette)

La page passe en mode tactile quand le navigateur annonce un écran tactile comme pointeur principal (réglage « Commandes tactiles » : Auto ; Oui force le mode tactile, Non le refuse, par exemple sur un ordinateur à écran tactile). En mode tactile :

- la barre de boutons est remplacée par une **colonne de boutons** en bas à droite : « Promenade » (« Sortir » en promenade), « Sauter », « Voler » (« Atterrir » en vol), « Vue », « Chat » (avec le nombre de messages non lus), « Flèches », « Menu » ; le bouton actif a un bord épais ;
- le **menu** donne : Aide, Informations, Arrivées, Carte des mondes, Retour à l'arrivée (en promenade), Recentrer la vue (quand les flèches sont cachées) et **Plein écran** quand le navigateur le permet (pas sur iPhone, où Safari ne l'accorde qu'aux vidéos) ;
- les fenêtres Aide, Informations et Arrivées sont **réduites à l'ouverture** (sans changer le réglage retenu) et ont un bouton **✕** pour les fermer ;
- les flèches sont grandes (56 px), en bas à gauche ;
- en promenade, **glisser le doigt** sur la scène fait regarder autour de soi : on tire le décor (doigt vers la droite, regard vers la gauche) ; une bulle l'explique à la première promenade. En vue globale, les gestes restent ceux d'avant (un doigt : tourner ; deux doigts : déplacer et zoomer) ;
- « Chat » ouvre un vrai champ de saisie (le clavier du téléphone s'ouvre) avec « Envoyer » et « ✕ Fermer » ; flèches et colonne se cachent pendant la saisie ;
- l'écran tourné à l'horizontale est pris en charge : la colonne passe sur deux ou trois colonnes ;
- « Capturer la souris » n'existe pas (rien à capturer au doigt).

Sur un petit écran de téléphone, la page reste chargée : fenêtres et chat peuvent se refermer pour dégager la vue.

### 29.5 Bulles

Chaque bouton de la barre et chaque flèche a une bulle : son rôle et sa touche (la lettre suit la disposition du clavier). Sur écran tactile, **un appui long** (une demi-seconde) montre la bulle ; sur un bouton à action unique, l'appui long ne déclenche pas l'action.

### 29.6 Compteur du chat

Le nombre entre parenthèses du titre de l'onglet (« (3) Région ») et du bouton « Chat » compte les messages des autres visiteurs reçus pendant que le chat est fermé ou l'onglet caché (l'historique rejoué à l'arrivée n'est pas compté) ; il revient à zéro **à l'ouverture du chat**, même sans lire les messages (comportement voulu).

### 29.7 Diagnostic

« Copier le diagnostic » ajoute la ligne « Commandes tactiles » : mode tactile oui ou non, réglage, écran tactile détecté, nombre de points de contact.

### 29.8 Une coquille pour tout un site

Organisation conseillée : à la racine du site, une seule coquille `index.html`, le dossier `lib`, `regions.json` et `default.json` ; un dossier par région. Adresse d'une région : `index.html?region=dossier/NOM`. Pour mettre une région à jour **et** la coquille de la racine, donner le chemin de la coquille à `--shared-shell` :

`python glb2html.py --update -o "P:\site\dossier\NOM.html" --shared-shell "P:\site\index.html"`

Avec `--shared-shell` sans chemin, la coquille et un dossier `lib` sont écrits **dans le dossier de la région**, où ils ne servent pas avec cette organisation. Autre moyen après `python build.py` : copier `dist\index.html` à la place de `index.html` (la ligne `const LIB` reste `./lib`). `--update` compare la coquille au contenu de celle qu'il contient lui-même : il faut lancer le `glb2html.py` de `dist`, fabriqué en dernier (une copie plus ancienne ailleurs écrit son ancienne coquille). Une coquille modifiée à la main est renouvelée, l'ancienne gardée sous un nom daté (`index.avant-AAAAMMJJ-HHMMSS.html`).

### 29.9 Tests de la v46

`tests/v46.py` (Chromium, écran tactile simulé par de vrais évènements tactiles) : ligne d'état, place des éléments (rien ne se chevauche, à 1440 x 900, 390 x 844, 844 x 390 et 1180 x 820), flèches tenues à la souris et au doigt (avancer, pas de côté, tourner, monter, vue globale), Courir, K et bouton « Flèches (K) », Recentrer, bulles, appui long, menu, chat tactile, ✕, réglages, diagnostic, anglais.

### 29.10 Non testé

Un vrai téléphone, une vraie tablette, iPhone et iPad, Edge, Windows, le plein écran réel.

## 30. Nouveautés de la v47 (25/10/2026)

### 30.1 La tuile de la carte

Sous le nom, une ligne de texte (jamais de couleur seule) : « 3 visiteurs » puis « 1 promeneur » sur deux lignes (v52 ; en anglais « 3 visitors · 1 walker » sur une ligne), ou « aucun visiteur ». Les visiteurs comptent les promeneurs **et** les spectateurs (pages ouvertes en vue globale) ; les promeneurs ne sont indiqués que s'il y en a. La ligne n'apparaît que si la fiche a un salon (`room`) et un serveur de présence (`presence`, ou celui de la page). Le mot « visiter → » a disparu : une **bulle** au survol dit ce que fait le clic (« Cliquer pour entrer dans la région (arrivée : default) »). La région où l'on se trouve garde « ● vous êtes ici ». Au doigt, il n'y a pas de survol, donc pas de bulle. Même affichage sur la page carte et dans la carte ouverte par M.

### 30.2 Adresse facultative

L'adresse sous chaque tuile est **masquée par défaut**. Elle s'affiche si `showUrl` vaut `true` dans l'en-tête de `regions.json` (§ 27.6), ou si le visiteur coche la case « Afficher les adresses » en haut de la page carte (à côté du pseudo). Le choix du visiteur est retenu par son navigateur et l'emporte sur le fichier. Une adresse invalide garde son message « (adresse invalide) ». L'adresse s'affiche sous la vignette, **hors du lien** : on peut la sélectionner à la souris et la copier (après la v52 ; dans un lien, un clic-glissé ne sélectionne pas le texte), et le zoom au survol reste sur la vignette. La grille n'est redessinée que si les données ont changé, et jamais tant qu'un texte de la grille est sélectionné (les compteurs attendent la fin de la sélection).

### 30.3 `regions.json` avec en-tête

Deux formes, la liste simple et l'objet `{"showUrl": ..., "regions": [...]}` (§ 27.6). `--register` lit et réécrit le fichier en gardant l'en-tête et la forme. Un ancien `glb2html.py` efface une liste qui n'en est pas une : ne pas l'utiliser sur un fichier avec en-tête.

### 30.4 Deux façons de faire la carte

- **Mode autonome** : `--map-page` écrit une page avec la liste des régions dedans. Elle s'ouvre depuis le disque et se régénère quand la liste change (sauf avec `--map-url`, qui la fait relire `regions.json`). Le `showUrl` de l'en-tête y est repris.
- **Mode hébergé** : `python build.py` écrit `dist\carte.html`, une page identique pour tous les sites, **sans région dedans**. Elle lit `regions.json` à côté d'elle à chaque ouverture, comme `index.html` lit les `NOM.config.json`. On la copie une seule fois à côté de `index.html` : `Copy-Item "P:\site\web_3d\dist\carte.html" "P:\site\carte.html"`. Plus rien à régénérer quand `regions.json` change. Elle demande un serveur web : ouverte depuis le disque, elle le dit ; sans `regions.json`, elle dit « Impossible de lire regions.json ».

Les deux modes cohabitent.

### 30.5 Serveur de présence

La réponse à une demande `rooms` ajoute `visitors` (promeneurs et spectateurs, par salon) à `rooms` (promeneurs) et `spectators` (total). Avec un ancien serveur, la carte n'affiche que les promeneurs : relancer le `presence_server.py` de `dist\` après `python build.py`.

### 30.6 Tests de la v47

`tests/v47.py` (Chromium, vrai serveur de présence) : `visitors` par salon, `carte.html` universelle, liste simple et en-tête, case à cocher (départ, choix retenu, priorité), anglais, `--register` qui garde l'en-tête, ancien serveur, `regions.json` absent, ouverture depuis le disque, carte ouverte par M.

### 30.7 Non testé

Un vrai téléphone (pas de bulle au doigt), Edge, Windows, les lignes PowerShell elles-mêmes.

## 31. Nouveautés de la v48 (25/10/2026) : journal des visites

### 31.1 À quoi il sert

Le créateur d'une région (par exemple un artiste qui présente sa galerie) voit combien de personnes l'ont visitée, quand et combien de temps, même s'il n'était pas là. Les visites sont notées par le serveur de présence dans un fichier à part ; le créateur les consulte depuis la page de sa région, avec une clé. Il ne reçoit qu'un résumé, jamais le fichier.

### 31.2 Côté hôte : le serveur de présence

1. Lancer le serveur avec `--visits visits.jsonl` (un chemin relatif désigne le dossier du script, comme `--log`). `--visits-days N` règle la conservation (365 jours par défaut ; `0` = tout garder). `--visits-names` note aussi le pseudo des promeneurs (désactivé par défaut) :
   `python ".\presence_server.py" --log presence.log --log-ip raw --log-days 0 --history-file chat.jsonl --history-days 0 --visits visits.jsonl`
2. Dans la console du serveur, taper `visits-key ROOM`, où ROOM est le salon : la valeur `room` de la config de la page (par défaut, le nom de la page). La clé s'affiche **une seule fois**, par exemple `K7QF-29MD-XR4P` ; seule son empreinte est gardée, dans `presence_visits_keys.json` (option `--visits-keys`). Refaire la commande donne une nouvelle clé : l'ancienne ne marche plus. `visits-key ROOM off` retire la clé ; `visits-key` seul liste les salons qui ont une clé. `cle-visites` est accepté à la place de `visits-key`. **La casse compte** dans le nom du salon, comme partout dans le serveur (`Houses` et `houses` sont deux salons) : si le nom tapé n'existe qu'avec une autre casse, la console le signale. La commande `rooms` (alias `salons`) liste les salons connus, avec leur casse exacte : visiteurs connectés (dont promeneurs), nombre de visites et date de la dernière, clé ou non. Un salon jamais visité et sans clé n'y figure pas : son nom est la valeur `room` de `NOM.config.json`, par défaut le nom de la page.
3. Envoyer au créateur l'adresse de sa page suivie de `#visits`, et la clé : `https://ADRESSE/index.html?region=galerie#visits`.

### 31.3 Côté créateur : la fenêtre « Journal des visites »

Il ouvre ce lien, depuis n'importe quel appareil, sans rien installer. La région s'ouvre avec la fenêtre « Journal des visites ». Sans `#visits`, le bouton « Journal des visites… » de la fenêtre Informations (I), à côté de « Copier le diagnostic », ouvre la même fenêtre ; il n'existe que sur une page qui a un serveur de présence. Il tape la clé (majuscules ou minuscules, tirets ou espaces : peu importe), puis « Afficher » ou Entrée :

- tableau « Par jour » : Date, Visites, Visiteurs distincts, Durée totale, Durée médiane, Avec promenade ;
- tableau « Visites des 30 derniers jours » : Arrivée, Durée, Promenade (oui ou non), et Pseudo si le serveur a `--visits-names` (1000 visites au plus) ;
- bouton « Télécharger (CSV) » : les deux tableaux pour un tableur, durées en secondes, séparateur `;` en français et `,` en anglais.

La clé acceptée est retenue par le navigateur : la fois suivante, le résumé s'affiche directement. « Oublier la clé » l'efface (à faire sur un ordinateur partagé). Échap ou « Fermer (Échap) » ferme la fenêtre ; la région reste utilisable derrière.

Messages possibles : clé refusée ; trop d'essais (5 clés refusées par minute et par adresse IP, puis une minute d'attente) ; serveur lancé sans `--visits` ; serveur trop ancien (avant la v48) ; serveur qui ne répond pas ; page sans serveur de présence.

### 31.4 Ce qui est compté

- **Une visite** est une connexion au serveur de présence : une page ouverte (spectateur, quand `spectate` est actif, ce qui est le cas par défaut avec une adresse de présence) ou une promenade. Le temps passé en promenade est noté à part (colonne « Avec promenade »).
- **Reconnexions** : un rechargement de page, une coupure du réseau ou un passage entre promenade et vue globale moins de 2 minutes après la fin compte comme la même visite (même navigateur, même salon).
- **Visiteurs distincts** : comptés par l'empreinte du navigateur. Un même visiteur sur deux appareils compte deux fois ; un navigateur qui efface ses données compte comme un nouveau visiteur.
- **Ne sont pas comptés** : les pages sans serveur de présence, les visiteurs dont la connexion échoue (pare-feu, page https avec une adresse `ws://`), les pages fabriquées avec `--no-spectate` tant qu'on ne se promène pas. La consultation du journal compte elle-même comme une visite (la page est ouverte). Le nombre de pages servies se lit dans le journal du serveur web (Apache).
- Les jours suivent l'horloge de la machine du serveur.
- Une visite est écrite quand elle se termine. Arrêt propre du serveur (Ctrl+C) : les visites en cours sont écrites. Arrêt brutal du serveur ou de la machine : elles sont perdues.

### 31.5 Données personnelles

Le fichier des visites ne contient **jamais d'adresse IP**. L'empreinte du navigateur est une donnée pseudonyme, le pseudo (avec `--visits-names`) une donnée personnelle : informer les visiteurs et garder une durée raisonnable (`--visits-days`). Le journal `presence.log` ne change pas. Sur une adresse `ws://`, la clé circule en clair : pour un accès depuis l'extérieur, page et présence en https et `wss://` (procédures § 11).

### 31.6 Fichiers

Format du fichier des visites et de `presence_visits_keys.json` : § 27.10. Exemples : `docs/samples/visits.sample.jsonl` et `docs/samples/presence_visits_keys.sample.json` (clé d'exemple `ABCD-EFGH-JKMN`, à ne jamais utiliser).

### 31.7 Tests de la v48

`tests/v48.py` (vrai serveur de présence, Chromium) : écriture des visites sans IP ni pseudo, fusion des reconnexions, temps de promenade, empreinte de la clé seulement, clé en minuscules acceptée, mauvaise clé, limite de 5 essais, `visits-key ROOM off`, purge, pseudos avec `--visits-names`, arrêt propre, fenêtre de la page (clé refusée, résumé, CSV, clé retenue puis oubliée, Échap), page sans présence, serveur sans `--visits`, ancien serveur, serveur absent, anglais. `tests/samples.py` lit les deux nouveaux exemples.

### 31.8 Non testé

Windows (Ctrl+C dans la console Windows), Edge, un vrai téléphone, Tailscale Funnel, les lignes PowerShell elles-mêmes.

## 32. Nouveautés de la v49 (25/10/2026) : mise à jour de `regions.json` depuis le dossier des sites

### 32.1 La commande

`cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --scan-sites "P:\_OpenSim\SL&OS\Web_3d\Sites" --dry-run`

`--dry-run` affiche ce qui changerait sans rien écrire ; la même ligne sans `--dry-run` écrit `Sites\regions.json`. Le dossier donné est celui de la coquille commune (`index.html` à la racine) ; sans `index.html`, un avertissement le signale.

### 32.2 Ce que fait le parcours

- Une fiche par fichier `NOM.config.json` trouvé dans le dossier et ses sous-dossiers (les dossiers `lib`, `_bak` et ceux qui commencent par un point sont ignorés, ainsi qu'un fichier sans champ `room`).
- Adresse de la fiche : `index.html?region=dossier/NOM` ; salon et serveur de présence : ceux de la config (`room`, `presenceUrl`).
- Une fiche existante est reconnue par son salon, sinon par son adresse. Son nom, sa place (`x`, `y`), son arrivée (`spawn`) et son `id` sont gardés : seuls l'adresse, le salon, le serveur et la vignette sont mis à jour. Le nom d'une nouvelle fiche est celui du fichier : à changer une fois dans `regions.json`, il est gardé ensuite.
- Une nouvelle région reçoit la première case libre de la ligne `y = 0` (jamais une place déjà prise : deux fiches à la même place font passer la carte en simple liste).
- Les fiches des créateurs (adresse complète en `http` ou `https`) ne sont jamais touchées. L'en-tête (`showUrl`) et la forme du fichier (objet ou liste) sont gardés. Sans `regions.json`, le fichier est créé avec l'en-tête.
- Rien n'est supprimé : une fiche locale dont la région n'est plus dans le dossier est signalée « orpheline » et gardée.

### 32.3 Les vignettes

Une image `NOM.jpg` (ou `.jpeg`, `.png`, `.webp`) à côté de `NOM.config.json` devient la vignette de la fiche, par un chemin relatif (`houses/NOM.jpg`) : `regions.json` reste léger, et le chemin marche depuis `carte.html` comme depuis la carte ouverte par M, toutes deux à la racine. Sans image, la vignette déjà notée est gardée.

Caractéristiques conseillées : **image carrée de 320 x 320 pixels**, JPEG de qualité moyenne (quelques dizaines de Ko, estimation). La tuile l'affiche en carré d'environ 155 pixels de côté (`aspect-ratio: 1`) ; 320 pixels restent nets sur les écrans à haute densité. Une image qui n'est pas carrée est recadrée au centre (`object-fit: cover`).

### 32.4 Tests de la v49

`tests/v49.py` (hors navigateur) : fiches créées et mises à jour, vignettes (chemin encodé), nom, place et arrivée gardés, en-tête gardé, fiche externe intacte, orpheline gardée, places sans doublon, dossiers ignorés, `--dry-run`, deuxième passage sans changement, liste simple, dossier absent, absence de `index.html`, anglais.

### 32.5 Non testé

Windows, les chemins de Klaatou, les lignes PowerShell elles-mêmes.

## 33. Nouveautés de la v50 (25/10/2026) : la carte des mondes dans le viewer

### 33.1 Importer et exporter `regions.json`

Section « Carte des mondes » du viewer :

- **Importer regions.json** accepte la liste simple comme l'objet avec en-tête (`{"showUrl": ..., "regions": [...]}`, § 27.6). Avant la v50, la forme objet était refusée (« tableau attendu ») : c'est celle qu'écrit `--scan-sites` quand il crée le fichier.
- **Exporter regions.json** rend la forme importée : objet avec le même en-tête, ou liste. L'en-tête est retenu par le navigateur, comme la liste des régions. Sans import, l'export est une liste simple.
- Chaque fiche garde tous ses champs, dont `presence` (serveur de présence d'une région externe), qui était perdu à l'import.
- Un fichier sans régions est refusé avec le message « fichier de carte attendu : liste de régions, ou objet {"regions": [...]} ».

### 33.2 Ajouter ou mettre à jour cette région

Le bouton **Ajouter / mettre à jour cette région dans la carte** met à jour sur place la fiche du même salon, comme `--register` : sa place dans la liste ne change plus, un champ vide (la vignette non capturée, par exemple) n'efface pas l'ancien, et les champs que le viewer n'affiche pas (`presence`...) restent. Le nom, l'adresse, la place et l'arrivée viennent des champs du viewer.

### 33.3 Tests de la v50

`tests/v50.py` (Chromium) : import de la forme objet, export identique (en-tête et champs inconnus gardés), rechargement du viewer, « Ajouter » sur place, liste simple exportée en liste, fichier refusé (français et anglais).

### 33.4 Non testé

Edge, Windows.

## 34. Nouveautés de la v51 (25/10/2026) : créateurs sur le serveur de présence

### 34.1 À quoi ça sert

L'hôte d'un serveur de présence accueille les régions d'autres créateurs, hébergées où ils veulent. Sans précaution, toute page qui connaît l'adresse du serveur peut s'y brancher et prendre le salon d'un autre, et ajouter une origine (`--origins`) demande de relancer le serveur. Avec `--creators`, le serveur n'accepte que les pages déclarées, chacune dans ses propres salons. Sans `--creators`, rien ne change.

### 34.2 Le fichier des créateurs

Lancement : ajouter `--creators presence_creators.json` à la ligne du serveur (chemin relatif au dossier du script). Le fichier s'écrit à la main, à partir de `docs/samples/presence_creators.sample.json` (champs au § 27.10). Il est relu sans relancer le serveur : une modification compte pour les connexions suivantes (vérification au plus toutes les 2 s) ; les connexions déjà ouvertes restent (pour en couper une : `ejecter`).

- **Origine** : le début de l'adresse de la page, sans chemin : `https://alice.example`, avec le port s'il n'est pas le port habituel (`http://localhost:8000`). Une page ouverte depuis le disque et le viewer ont l'origine `null`.
- **Préfixe** : le créateur `alice` n'ouvre que des salons `alice.NAME` (casse du préfixe ignorée) ; la valeur `room` de sa config doit donc commencer par `alice.`. Une seule entrée peut avoir `"prefix": ""` : l'hôte, qui garde tous les salons n'appartenant à aucun créateur (ses salons actuels ne changent pas de nom).
- **Limites** : `maxWalkers` (promeneurs au plus sur tous ses salons ; au-delà, « salon complet », aussi au passage en promenade), `maxRooms` (salons ouverts en même temps). Les limites générales (`--max-per-room`, `--max-total`, `--max-per-ip`) s'appliquent toujours.
- **`"off": true`** suspend le créateur.
- Fichier absent : toute connexion est refusée. Fichier illisible (par exemple pendant qu'on l'écrit) : la liste précédente est gardée. Entrée invalide : signalée dans la console et ignorée.

### 34.3 Ce que voit le visiteur

La page affiche « présence refusée : » suivi de la raison, et ne réessaie pas (recharger la page une fois corrigé) : page non déclarée sur ce serveur, créateur suspendu, salon qui n'appartient pas au créateur, trop de salons ouverts. Le viewer affiche la même raison. Le serveur ferme la connexion avec le code 4003, que montre « Copier le diagnostic ».

### 34.4 Console et journal

- `creators` (alias `createurs`) relit le fichier et liste chaque créateur : préfixe, actif ou suspendu, salons ouverts, promeneurs, origines.
- Chaque refus est noté « refus » dans `presence.log` avec sa raison ; une connexion acceptée se reconnaît au préfixe de son salon.
- Les clés du journal des visites restent par salon : `visits-key alice.galerie`.

### 34.5 Accueillir un créateur

Procédures § 6, point 7.

### 34.6 Limites

- L'origine est annoncée par le navigateur : elle empêche une autre page web de prendre un salon, pas un programme écrit exprès qui annoncerait une fausse origine. Contre lui restent `--max-per-ip`, `ejecter` et `bannir`.
- Une page en https ne peut joindre qu'un serveur en `wss://` (procédures § 11).
- Les compteurs de la carte des mondes (requête des salons) suivent la même règle d'origine.

### 34.7 Tests de la v51

`tests/v51.py` (vrai serveur, puis Chromium) : sans fichier, tout est accepté ; refus par origine, suspension, préfixe, nombre de salons ; promeneurs au plus à l'arrivée et au passage en promenade ; hôte sans préfixe ; relecture à chaud ; console ; journal ; refus affiché par la page (français, anglais) et par le viewer. `tests/samples.py` lit l'exemple.

### 34.8 Non testé

Windows, Edge, `wss://` derrière Funnel, page d'un créateur sur un autre domaine.

### 34.9 Connexions vides

Une connexion ouverte sur le port du serveur de présence puis refermée sans rien envoyer (préconnexion d'un navigateur, test de port, robot) remplissait la console d'une longue trace « opening handshake failed » avec les versions 14 et 15 de `websockets`. Depuis la v51, elle donne une ligne courte « vide » dans la console et dans `presence.log`, avec l'adresse de l'appelant (masquée selon `--log-ip`) et le nombre de connexions vides, au plus une ligne par minute et par adresse. C'est sans danger ; les autres erreurs de `websockets` restent affichées en entier.

`tests/v51_vides.py` : avec la version installée, puis avec une ancienne version donnée par la variable `WS_OLD` (essayé ici avec 13.1, 14.2 et 15.0.1). Non testé : Windows, Edge.

### 34.10 Adresse de présence « même nom que la page »

Une adresse de présence peut s'écrire avec une étoile à la place du nom : `ws://*:8765`. La page remplace l'étoile par le nom avec lequel elle a été ouverte : ouverte par `http://localhost:8096`, elle vise `ws://localhost:8765` ; ouverte par l'adresse réseau ou le nom public de la machine, elle vise cette même adresse. Une page ouverte depuis le disque, et le viewer, visent `127.0.0.1`. La règle « la présence au même endroit que la page » (procédures § 11) est ainsi tenue d'office.

Pourquoi : chaque config ou fiche portait une seule adresse (adresse réseau, adresse IP publique ou nom public), juste pour un seul des chemins d'accès. Une page ouverte par le nom public qui vise une adresse du réseau local est coupée par Edge avant l'envoi de la requête : la carte reste sans compteur et le serveur note une connexion « vide » à chaque interrogation (toutes les 10 s pour `carte.html`, toutes les 8 s pour la fenêtre Carte). Ce blocage est déduit des constats de Klaatou ; il n'est pas reproduit ici et n'a pas été essayé sous Edge.

L'étoile vaut partout : `--presence-url`, `presenceUrl` de `NOM.config.json`, champ `presence` de `regions.json`, champ de présence du viewer. Le serveur rappelle cette forme au démarrage. Limite : pour un visiteur venu d'Internet, le port du serveur de présence doit être joignable sous le même nom que la page (redirection de la box, ou Funnel, procédures § 11).

`tests/v51_etoile.py` (Chromium) : page ouverte par `127.0.0.1` puis par `localhost`, fenêtre Carte, `carte.html`, journal des visites, viewer ouvert depuis le disque, `ws://0.0.0.0` toujours corrigé, message d'erreur avec l'adresse résolue. Non testé : Windows, Edge.

## 35. Nouveautés de la v52 (25/10/2026)

### 35.1 `carte.html` : décompte, total, deux lignes

Au-dessus de la grille : « 12 régions · Total : 3 visiteurs · 2 promeneurs ». Chaque salon est compté une fois ; avec un ancien serveur qui ne répond pas `visitors`, seuls les promeneurs sont comptés (pas de visiteurs inventés). Dans les tuiles, les visiteurs et les promeneurs passent sur deux lignes en français (« 2 visiteurs », puis « 1 promeneur ») et restent sur une ligne en anglais (« 2 visitors · 1 walker ») : c'est la clé de langue `map.sep` (`page.map.sep` pour la carte ouverte par M), un saut de ligne en français et « · » en anglais ; une nouvelle langue choisit la sienne. Le total reste sur une ligne.

### 35.2 Surveillance des arrivées (son et repère)

Une case en haut de `carte.html`, « Surveillance des arrivées (son et repère) », mémorisée dans ce navigateur (clé `glb2html_map_alert`). Elle n'apparaît que si au moins une région a un serveur de présence (sinon il n'y a rien à surveiller, comme dans la démo en ligne). Cochée :

- Une **hausse du nombre de visiteurs** d'un salon de la carte entre deux relevés est une arrivée : deux notes montantes (660 puis 880 Hz, comme l'arrivée d'un promeneur dans la page), au plus un bip toutes les 2 s, et la **tuile de la région est marquée** : contour en pointillés qui clignote, fond jaune et texte « ● arrivée hh:mm » (jamais la couleur seule ; pas de clignotement si le système demande de réduire les animations). Le repère reste jusqu'au survol de la tuile ; décocher la case l'efface. La ligne d'état dit « dernière arrivée : région, hh:mm ».
- Le **premier relevé** d'un serveur ne sonne jamais (il sert de base). Une arrivée et un départ dans le même intervalle de relevé s'annulent : pas de bip.
- Le navigateur interdit tout son avant un clic ou une touche dans la page : après un rechargement, la case cochée affiche « le son démarre au premier clic dans la page ». Cocher la case est déjà un clic.
- **Délais** : en tête du script de `carte.html` (dans le dépôt, `MAP_PAGE_TEMPLATE` de `src/gen_tpl.py`), `const POLL_MS = 10000;` (relevé normal) et `const POLL_ALERT_MS = 5000;` (case cochée), en millisecondes. Le délai est relu à chaque tour et dès que la case change. Chaque relevé ouvre une connexion brève par serveur de présence : augmenter ces valeurs allège le serveur (charge non mesurée).

La surveillance ne concerne que `carte.html` (et la carte autonome `--map-page`) ; la carte ouverte par M garde les sons de la page (§ 21.6).

### 35.3 Vignette agrandie au survol

Au survol d'une tuile qui a une vignette, **à la souris seulement** (pas au doigt), la vignette s'affiche en grand, 400 px au plus, replacée pour rester dans la fenêtre. C'est le même code dans `carte.html` et dans la carte ouverte par M. Les vignettes conseillées font 320 x 320 px (§ 32.3) : l'image est agrandie, pas améliorée. Une tuile sans vignette n'a rien à agrandir.

### 35.4 Case « Afficher la mer »

Dans Réglages, avant « Mer animée », seulement si la page a une mer (pas faite avec `--no-sea`). Décochée : la mer disparaît de la scène, « Mer animée » et « Vagues » sont grisés. Le choix est retenu avec les autres réglages (clé `glb2html_opts_SALON`) ; « Valeurs d'origine » remet celui de la page. Utile pour une région sans eau faite sans `--no-sea` (la mer est active par défaut). La hauteur de la mer ne sert qu'à poser le plan d'eau : masquer la mer ne change aucune collision. Une page faite avec `--no-sea` ignore un ancien choix retenu.

### 35.5 Serveur de présence : requêtes HTTP ordinaires

Avec `websockets` 14 et 15, une requête HTTP ordinaire sur le port du serveur (navigateur qui ouvre son adresse, robot, test) écrivait une trace complète (« opening handshake failed », `InvalidUpgrade`, « invalid Connection header: keep-alive »), alors que le client reçoit bien « 426 Upgrade Required ». Le journal écrit à la place une ligne `requête http` : adresse, chemin, hôte, agent et raison, au plus une par minute et par adresse. Elle dit qui est venu. Tout caractère de contrôle (échappement de terminal, sonnerie) est remplacé par une espace, dans cette ligne comme dans tout le journal. Une requête illisible (sondage du Bureau à distance Windows, connexion chiffrée sur ce port, octets quelconques) donne aussi une seule ligne « requête illisible » avec la sorte reconnue et le début de la requête, au plus une par minute, par adresse et par sorte. Les autres erreurs restent affichées en entier. **Relancer le serveur de présence** depuis `dist\`. Les versions récentes de `websockets` (17.3 essayée) n'écrivent pas cette trace : rien à filtrer.

### 35.6 Région en tuiles renommée

`NOM.overview.glb` garde dans chaque nœud le chemin de sa tuile tel qu'il était au découpage (`NOM.tiles/T_3_0_0.glb`). Jusqu'à la v51, renommer à la main les dossiers et les chemins de l'index laissait la vue d'ensemble **visible sous les tuiles détaillées** : surfaces superposées, moirures et plaques sombres sur le terrain et les rochers (cas de Klaatou, région Houses, 25/10/2026). Depuis la v52, la page retrouve la cellule par le **nom du fichier de la tuile** quand le chemin complet ne correspond pas (nom unique dans une région ; sinon la cellule reste visible, jamais de trou). Pour renommer une région en tuiles : renommer `NOM.tiles`, `NOM.overview.glb`, `NOM.tiles.json`, `NOM.config.json` et `NOM.zones.json`, corriger dans l'index les chemins `file` des tuiles et `overview.file`, corriger le champ `tiles` de la config, puis copier la coquille `index.html` de la v52. Il n'y a pas à régénérer la vue d'ensemble.

### 35.7 Tests de la v52

`tests/v52.py` (Chromium, vrai serveur de présence, faux `AudioContext`) : `carte.html` (« promeneur », total et décompte, aucun son au premier relevé ni case décochée, deux notes 660 et 880 Hz sur une arrivée, repère visuel et sa disparition au survol, délai relu à la case cochée, constantes `POLL_MS` et `POLL_ALERT_MS`), vignette agrandie (carte et carte M), ancien serveur, anglais, case « Afficher la mer » ; `tests/v52_http.py` (vrai serveur, `websockets` installé puis `WS_OLD` et `WS_OLD2`) ; `tests/v52_renom.py` (région découpée, copiée sous deux autres noms) ; `tests/i18n.py` accepte une valeur blanche pour les clés en `.sep` ; `tests/v47.py` adapté au texte « promeneur ».

### 35.8 Non testé

Le son réel (le test remplace `AudioContext`), Edge, Windows, un vrai téléphone, un onglet gardé longtemps en arrière-plan (le navigateur peut ralentir ses minuteries : non mesuré), la charge du serveur à 5 s. Le renommage de § 35.6 a été confirmé par Klaatou sur sa région Houses (25/10/2026).

## 36. Ajouts depuis la v52 (non publié)

### 36.1 Icône des pages (`favicon.ico`)

Les pages (coquille `index.html`, page autonome, `carte.html`, `glb-viewer.html`) portent une icône « 3D » (texte blanc sur fond bleu foncé) incorporée par défaut. **Pour la changer, place un fichier `favicon.ico` à côté de la page** : s'il existe, la page l'adopte, sans refaire aucune page. `python build.py` écrit un `favicon.ico` d'exemple dans `dist\` (quatre tailles : 16, 32, 48 et 64 px) ; copie-le avec `index.html`, puis remplace-le par le tien (un fichier ICO à plusieurs tailles donne le meilleur rendu). Sans ce fichier, la page garde l'icône incorporée, et le serveur web voit une demande `favicon.ico` sans réponse. Pour un site à coquille partagée (§ 29.8), un seul `favicon.ico` à côté de `index.html` suffit ; une page autonome rangée dans un autre dossier a besoin du sien à côté d'elle. Safari n'a pas été essayé.
