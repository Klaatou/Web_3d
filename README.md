# web_3d

Outils pour mettre une région 3D sur le web : `glb2html` (générateur de pages), le viewer de réglages et le serveur de présence.

Transforme une région 3D exportée en `.glb` (OpenSim, par exemple) en **page web autonome** : vue 3D, promenade avec avatar, visiteurs en temps réel, chat, zones et portails, carte des mondes.

Trois outils :

| Fichier fabriqué | Rôle |
|---|---|
| `glb-viewer.html` | Page de réglages et d'export : on charge un `.glb`, on règle la mer, le trou, la caméra, la promenade, les zones, la fiche de région, puis on exporte. |
| `glb2html.py` | Script qui fait la même chose en ligne de commande (hors ligne, sans navigateur). |
| `presence_server.py` | Serveur WebSocket de présence, chat, modération et compteurs de visiteurs. |

## Fabriquer les trois fichiers

```
python build.py
```

Le résultat est dans `dist/`. Au premier lancement, three.js r160 est téléchargé dans `.cache/` (ou `python build.py --vendor DOSSIER` avec un paquet npm `three` déjà présent). Les fichiers de `dist/` ne sont pas versionnés : on les publie dans les « Releases » du dépôt.

## Utiliser

1. Ouvrir `dist/glb-viewer.html`, charger le `.glb`, régler, puis « Enregistrer dans un fichier » (section Réglages mémorisés) : on obtient `<nom>.reglages.json`.
2. Générer la page avec les mêmes réglages (une seule ligne) :

```
python glb2html.py "Ankh-final.glb" --settings --register regions.json --map-page carte.html -o "Ankh Island.html"
```

3. Lancer le serveur de présence : `python presence_server.py --log presence.log`.

`python glb2html.py --help` et `python presence_server.py --help` listent toutes les options.

## Carte des mondes

`regions.json` est la carte : une liste de régions (nom, adresse, X, Y, point d'arrivée, salon, serveur de présence, vignette). `--register` y ajoute ou met à jour la région en cours de génération ; `--map-page` génère une page web de la carte avec un lien cliquable par région ; `--map-url a.json,b.json` fusionne les cartes de plusieurs propriétaires à chaque ouverture de la page.

## Développer

Voir `CLAUDE.md` (architecture, décisions, feuille de route) et `HISTORIQUE.md` (comment retrouver chaque version) et `tests/smoke.py` (test de fumée dans Chromium sans tête).

## Sécurité

Ne jamais committer : adresses Home Assistant (`zones*.json`), `*.reglages.json`, `presence_identities.json`, `presence_bans.json`, journaux. Le `.gitignore` les exclut. Le profil `--profile public` retire les zones privées des pages publiées.

## Licence

À choisir par le propriétaire du dépôt. three.js (MIT) et les décodeurs embarqués : voir `THIRD-PARTY.md`.
