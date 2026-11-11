# Créer et gérer sa région

*03/11/2026. Pour qui veut mettre une région OpenSim dans une page web : le chemin dans l'ordre, du plus simple au plus complet. Les numéros de § renvoient à `MANUEL.md`. Dans les commandes, `CHEMIN` est un chemin et `NOM` le nom de la région.*

## 1. Obtenir sa région en 3D

### 1.1 Le plus simple : un paquet prêt à l'emploi

Deux paquets sont sur la page des versions du dépôt GitHub. Rien à installer pour visiter ; le petit serveur local demande Python 3.7 ou plus.

- `galerie-photos.zip` : une galerie de photos en 3D, prête à remplir.
- `region-simple.zip` : une région d'exemple ; on y met son propre `.glb` sous le nom `site\region.glb` pour le voir dans le navigateur. C'est aussi le moyen le plus simple d'essayer un GLB qu'on vient de fabriquer (§ 1.2).

Dans chaque paquet, `lancer-…` ouvre la région (`.bat` sous Windows, `.sh` sous Linux, `.command` sous macOS) et `renommer-…` change son nom. Chaque paquet a aussi sa propre carte (`carte.html`, avec la vignette `site/vignette.jpg` et la fiche `site/regions.json`) : une page de présentation de la région, que le créateur complète de ses autres régions. Le `README.txt` et le `readme.html` du paquet détaillent tout.

### 1.2 Depuis son OAR : `oar2glb.py` (Windows seulement)

Une sauvegarde de région OpenSim (`.oar`) devient un `.glb`, écrit à côté de l'OAR.

- Il faut Python 3.8 ou plus et **convoar**, déjà fourni dans `dist/convoar/` de ce dépôt (copie du dossier `dist` de `github.com/Misterblue/convoar`, sans les fichiers de débogage ; `convoar.exe` seul ne marche pas, il a besoin des DLL de ce dossier : si vous déplacez `oar2glb.py`, emportez ce dossier avec lui), avec .NET Framework 4.8, déjà présent sous Windows 10 et 11.
- Linux : `oar2glb.py` lance convoar avec Mono (essayé sur Debian 13, petites régions ; paquets à installer : manuel, § 3.11). macOS : non essayé.

```powershell
python oar2glb.py "CHEMIN\NOM.oar" --convoar "CHEMIN\convoar\dist\convoar.exe"
```

Pour l'essayer : copier le GLB dans `site\region.glb` du paquet `region-simple` (§ 1.1). Options et dépannage : § 15.

### 1.3 Région lourde : la découper en tuiles

Au-delà d'environ 150 Mo ou 3 millions de triangles, la page doit charger la région par morceaux. `--analyse` dit s'il faut découper, sans rien écrire :

```powershell
python glb2tiles.py "CHEMIN\NOM.glb" --analyse
```

Le découpage, avec la compression qui réduit les fichiers d'environ moitié (Node requis) :

```powershell
python glb2tiles.py "CHEMIN\NOM.glb" --compress
```

Détails : § 4.1 et § 4.2.

## 2. Poser les zones : le viewer `glb-viewer.html`

Le viewer s'ouvre dans le navigateur ; on y ouvre son `.glb` et on y pose les zones : point d'arrivée, portails, panneaux, liens, images (chapitre 5). Il enregistre `NOM.zones.json`, à mettre à côté de la page. Une image peut être un GIF animé (manuel § 5.11).

## 3. Fabriquer la page : `glb2html.py`

Deux formes de page :

- **Autonome** : un seul fichier `NOM.html` qui contient tout, modèle compris. Simple à envoyer, mais tout est à refaire à chaque changement.
- **Avec coquille** (`--shared-shell`) : une `index.html` commune à toutes les régions du dossier, plus `NOM.glb`, `NOM.config.json` et `NOM.zones.json` ; adresse `index.html?region=NOM`. À préférer : plusieurs régions, réglages modifiables sans tout refaire, mises à jour des outils, « À propos », carte des mondes.

```powershell
python glb2html.py "CHEMIN\NOM.glb" --shared-shell -o "CHEMIN\site\NOM.html" --title "Ma région"
```

| Option | Rôle |
|---|---|
| `-o` | fichier de la page (son nom donne le nom de la région) |
| `--shared-shell` | page avec coquille commune |
| `--title` | titre affiché dans l'onglet (§ 6.11) |
| `--sea-y` | hauteur de la mer |
| `--presence-url`, `--room`, `--chat` | serveur de présence, salon, chat (§ 5) |
| `--tiles` | région découpée en tuiles (§ 8) |
| `--update` | remettre une page au niveau d'une nouvelle version des outils sans rien ressaisir |

Toutes les options : `docs/REFERENCE_OPTIONS.md`.

## 4. Publier

- Copier le dossier de la page sur un hébergement web (GitHub Pages ou tout serveur web). Une page ouverte par double-clic ne marche pas ; pour essayer chez soi :

```powershell
python -m http.server 8000
```

  puis ouvrir `http://localhost:8000/index.html?region=NOM`.
- Noms de fichiers en minuscules : un hébergeur distingue les majuscules. Le nom lisible va dans `title`.
- Facultatif : une présentation de la région dans `NOM.about.fr.txt` (§ 6.10) et une carte des mondes (`--scan-sites`, § 9.9).

## 5. Les autres visiteurs : la présence

Voir les autres promeneurs et discuter demande un serveur de présence : celui d'un hôte qui t'accueille (note `CREATEURS.md`, en anglais `CREATORS.md`), ou le tien (`presence_server.py`, `PROCEDURES.md` § 6 et § 11).

## 6. Les outils et leur rôle

Tous sont dans le dossier `dist` du dépôt.

| Outil | Rôle |
|---|---|
| `oar2glb.py` | OAR vers GLB (Windows, avec convoar) |
| `glb-stats.py` | analyse rapide d'un GLB (poids, étendue, répartition), sans le charger en entier |
| `glb2tiles.py` | découpe un gros GLB en tuiles, compression avec `--compress` |
| `glb-viewer.html` | voir un GLB, poser les zones |
| `glb2html.py` | fabrique la page, la met à jour (`--update`), met à jour la carte (`--scan-sites`) |
| `index.html` | la coquille commune des régions |
| `carte.html` | la carte des mondes en page seule |
| `presence_server.py` | serveur de présence : positions, chat, modération |
