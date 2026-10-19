# Mode d'emploi : zones, portails et points d'arrivée (v22)

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

## 3. Poser une zone

Dans le viewer, section **Zones : panneaux, portails, liens, commandes** :

1. **Type à poser** : choisis le type.
2. Pose-la, au choix :
   - clique sur **Poser une zone par un clic sur la scène**, puis clique dans la scène ;
   - ou, en promenade, place-toi au bon endroit et appuie sur **P** (un cercle sous tes pieds, ou un panneau 2 m devant toi, tourné vers toi).
3. La zone apparaît dans la liste : ouvre sa fiche pour la régler.
4. **Voir cette zone** recadre la vue dessus ; **Supprimer** l'efface.

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

## 10. Zones privées

**Privé (absent de l'export public)** coché : la zone reste dans tes exports « perso », mais disparaît des exports « public ». Le choix se fait dans **Profil d'export** :

- **perso : toutes les zones**
- **public : sans les zones privées**

Une arrivée privée disparaît aussi de l'export public : un portail public qui la vise tombera sur `default`.

## 11. Carte des mondes

Dans la section **Carte des mondes**, le champ **Point d'arrivée des visiteurs (identifiant)** dit où arrive quelqu'un qui vient de la carte. Le viewer indique sous ce champ :

- ✔ si cette arrivée existe dans la région ;
- ⚠ sinon (le visiteur apparaît alors au point de départ habituel de la touche F).

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
