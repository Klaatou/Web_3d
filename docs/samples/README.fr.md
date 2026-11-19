# Exemples de fichiers (`docs/samples/`)

Ce dossier contient **un exemple de chaque fichier JSON** que la page, le viewer, les outils et le serveur de présence lisent ou écrivent. Un fichier JSON n'accepte pas de commentaires : le sens de chaque champ est expliqué dans `REFERENCE_JSON.md` (colonne « Référence » des tableaux ci-dessous). Ici, ce sont de **vrais fichiers, complets et valides**.

**S'en servir** : copier l'exemple, le renommer, changer les valeurs. Dans les exemples la région s'appelle `Region` : pour une région « Atoll », `region.config.sample.json` devient `Atoll.config.json` et `Atoll` remplace `Region` dans les valeurs qui le contiennent (`room`, `tiles`, les adresses). Les adresses sont écrites `ADRESSE` : mets la tienne. Le test `tests/samples.py` vérifie que chaque exemple est accepté par le vrai code qui le lit : ils restent donc justes quand le code change.

## Fichiers d'une région et du site

| Exemple | Fichier réel | À quoi il sert | Référence |
| --- | --- | --- | --- |
| `region.config.sample.json` | `NOM.config.json` | les réglages que la page lit au démarrage (mer, marche, chat, présence, carte, tuiles) ; écrit par `glb2html.py` ; à plat | § 11.3 |
| `region.zones.sample.json` | `NOM.zones.json` | les zones d'une région : arrivées, portails, liens, commande, images, radio, musique, écrans vidéo (la liste est plus bas) | § 11.4 |
| `region.tiles.sample.json` | `NOM.tiles.json` | l'index des tuiles d'une grosse région, écrit par `glb2tiles.py` ; ne se modifie pas à la main | § 11.7 |
| `region.reglages.sample.json` | `NOM.reglages.json` | l'état de travail du viewer, écrit par le bouton « Enregistrer dans un fichier » : les réglages, **toutes** les zones (privées comprises), le cadrage de la caméra, la fiche de la région pour la carte et le récapitulatif de commande ; imbriqué ; relu par le viewer et par `glb2html.py --settings` | § 11.8 |
| `default.sample.json` | `default.json` | la région ouverte quand l'adresse n'a pas de `?region=` | § 11.5 |
| `regions.sample.json` | `regions.json` | la carte des mondes : une fiche par région (nom, place, adresse, présence, vignette) | § 11.6 |
| `disposition.sample.json` | `disposition.json` | la place des fenêtres d'aide, d'informations et d'arrivées, enregistrée par les Réglages de la page | § 11.9 |

## Les zones de l'exemple

`region.zones.sample.json` contient 14 zones (`REFERENCE_JSON.md` § 11.4) :

- arrivées : `default`, `gallery`
- portails : `to-gallery` (même région, en marchant dedans), `to-other-region` (autre région, avec confirmation), `back-home` (nom affiché)
- liens web : `website`, `door-info` (liée à l'objet `Door#2`)
- commande Home Assistant : `light-on` (privée, avec confirmation)
- image : `painting-1` (clé facultative `link` : page ouverte au clic)
- radio (`cast`) : `dance-floor` (flux de la liste `streams`, joués à portée en promenade ; `poster` (pochette) et `link` (page) facultatifs, montrés dans la fenêtre Son)
- musique (`audio`) : `ambiance` (fichiers du dossier `audio`, avec une pochette `poster` et un `link`)
- écrans vidéo (`video`) : `screen-clip` (un fichier, avec du son), `screen-list` (un dossier de vidéos)
- lien en fenêtre flottante : `video-page` (zone `url` avec la clé `frame`)

## Fichiers du serveur de présence

| Exemple | Fichier réel | À quoi il sert | Référence |
| --- | --- | --- | --- |
| `presence_identities.sample.json` | `presence_identities.json` | les pseudos réservés, gardés sous forme d'empreintes | § 11.10 |
| `presence_bans.sample.json` | `presence_bans.json` | les bannissements posés par la commande `bannir` (clé et adresse en empreintes, fin éventuelle) | § 11.10 |
| `chat_history.sample.jsonl` | fichier de `--history-file` | l'historique du chat, une ligne par message | § 11.10 |
| `visits.sample.jsonl` | fichier de `--visits` | le journal des visites, une ligne par visite, sans adresse IP | § 11.10 |
| `presence_visits_keys.sample.json` | `presence_visits_keys.json` | les clés (en empreintes) qui donnent accès au journal des visites d'un salon, commande `visits-key` | § 11.10 |
| `presence_creators.sample.json` | `presence_creators.json` | les créateurs accueillis (`--creators`) ; écrit à la main | § 10.10 |
| `presence_radios.sample.json` | `presence_radios.json` | les adresses de flux radio dont le serveur lit le titre du morceau pour les zones radio (`--radios`) ; écrit à la main | § 10 |

## Ce qui ne va jamais dans le dépôt des outils

Les vrais fichiers (pas ces exemples) `*.zones.json` et `zones*.json` (adresses Home Assistant), `*.reglages.json` (zones privées comprises), `regions.json`, `presence_identities.json`, `presence_bans.json`, `presence_visits_keys.json`, `presence_creators.json`, les journaux et les fichiers `*.jsonl` (historique du chat, journal des visites). Le `.gitignore` exclut les plus courants.
