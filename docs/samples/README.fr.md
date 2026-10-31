# Exemples de fichiers (`docs/samples/`)

Ce dossier contient **un exemple de chaque fichier JSON** que la page, le viewer, les outils et le serveur de présence lisent ou écrivent. Un fichier JSON n'accepte pas de commentaires : le sens de chaque champ est expliqué dans `MANUEL.md` § 27. Ici, ce sont de **vrais fichiers, complets et valides**.

**S'en servir** : copier l'exemple, le renommer, changer les valeurs. Dans les exemples la région s'appelle `Region` : pour une région « Ankh », `region.config.sample.json` devient `Ankh.config.json` et `Ankh` remplace `Region` dans les valeurs qui le contiennent (`room`, `tiles`, les adresses). Les adresses sont écrites `ADRESSE` : mets la tienne. Le test `tests/samples.py` vérifie que chaque exemple est accepté par le vrai code qui le lit : ils restent donc justes quand le code change.

## Fichiers d'une région et du site

| Exemple | Fichier réel | À quoi il sert | Manuel |
| --- | --- | --- | --- |
| `region.config.sample.json` | `NOM.config.json` | les réglages que la page lit au démarrage (mer, marche, chat, présence, carte, tuiles) ; écrit par `glb2html.py` ; à plat | § 27.3 |
| `region.zones.sample.json` | `NOM.zones.json` | les zones : arrivées, portails, liens web, Home Assistant et images sur un mur (la zone `painting-1`, type `image`) | § 27.4 |
| `region.tiles.sample.json` | `NOM.tiles.json` | l'index des tuiles d'une grosse région, écrit par `glb2tiles.py` ; ne se modifie pas à la main | § 27.7 |
| `region.reglages.sample.json` | `NOM.reglages.json` | l'état de travail du viewer, écrit par le bouton « Enregistrer dans un fichier » : les réglages, **toutes** les zones (privées comprises), le cadrage de la caméra, la fiche de la région pour la carte et le récapitulatif de commande ; imbriqué ; relu par le viewer et par `glb2html.py --settings` | § 27.8 |
| `default.sample.json` | `default.json` | la région ouverte quand l'adresse n'a pas de `?region=` | § 27.5 |
| `regions.sample.json` | `regions.json` | la carte des mondes : une fiche par région (nom, place, adresse, présence, vignette) | § 27.6 |
| `disposition.sample.json` | `disposition.json` | la place des fenêtres d'aide, d'informations et d'arrivées, enregistrée par les Réglages de la page | § 27.9 |

## Fichiers du serveur de présence

| Exemple | Fichier réel | À quoi il sert | Manuel |
| --- | --- | --- | --- |
| `presence_identities.sample.json` | `presence_identities.json` | les pseudos réservés, gardés sous forme d'empreintes | § 27.10 |
| `presence_bans.sample.json` | `presence_bans.json` | les bannissements posés par la commande `bannir` (clé et adresse en empreintes, fin éventuelle) | § 27.10 |
| `chat_history.sample.jsonl` | fichier de `--history-file` | l'historique du chat, une ligne par message | § 27.10 |
| `visits.sample.jsonl` | fichier de `--visits` | le journal des visites, une ligne par visite, sans adresse IP | § 27.10 |
| `presence_visits_keys.sample.json` | `presence_visits_keys.json` | les clés (en empreintes) qui donnent accès au journal des visites d'un salon, commande `visits-key` | § 27.10 |
| `presence_creators.sample.json` | `presence_creators.json` | les créateurs accueillis (`--creators`) ; écrit à la main | § 34 |

## Ce qui ne va jamais dans le dépôt des outils

Les vrais fichiers (pas ces exemples) `*.zones.json` et `zones*.json` (adresses Home Assistant), `*.reglages.json` (zones privées comprises), `regions.json`, `presence_identities.json`, `presence_bans.json`, `presence_visits_keys.json`, `presence_creators.json`, les journaux et les fichiers `*.jsonl` (historique du chat, journal des visites). Le `.gitignore` exclut les plus courants.
