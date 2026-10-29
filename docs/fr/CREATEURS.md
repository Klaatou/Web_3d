# Accueil sur un serveur de présence : note pour les créateurs

*29/10/2026. Pour le créateur d'une région qui veut la brancher sur le serveur de présence d'un hôte. Le côté hôte est au manuel § 34 et aux procédures § 6, point 7.*

## 1. De quoi il s'agit

Un serveur de présence relaie les positions, le chat et les compteurs de visiteurs d'une région. Un hôte peut accueillir ta page : ta région reste hébergée où tu veux (chez toi, GitHub Pages...), seul le serveur de présence est chez lui. L'hôte décide qui se branche : chaque page déclarée n'a accès qu'à ses propres salons.

## 2. Ce que tu donnes à l'hôte

- **L'origine de ta page** : le début de son adresse, sans chemin, par exemple `https://alice.example` (avec le port s'il n'est pas le port habituel). Si ta page est joignable avec et sans `www`, donne les deux.
- **Un identifiant court**, par exemple `alice` : il devient ton préfixe de salon.
- Une page ouverte depuis le disque, et le viewer, ont l'origine `null` : l'hôte décide de l'accepter ou non.

## 3. Ce que l'hôte te donne

- **L'adresse du serveur**, en `wss://` (par exemple `wss://MACHINE.TAILNET.ts.net`). Une page en https ne peut joindre qu'un serveur en `wss://`.
- **Ton préfixe** : tes salons s'appellent `alice.NAME` (la casse du préfixe est ignorée).
- **Tes limites**, s'il en fixe : `maxWalkers` (promeneurs en même temps, tous salons confondus) et `maxRooms` (salons ouverts en même temps). Les limites générales du serveur s'appliquent aussi.

## 4. Régler ta page

Deux façons, au choix :

- à la fabrication : `--presence-url wss://MACHINE.TAILNET.ts.net --room alice.galerie` ;
- ou dans `NOM.config.json` : les clés `presenceUrl` et `room`.

`room` n'est pas facultatif : sans lui, le salon prend le nom de la page, qui ne commence pas par ton préfixe, et le serveur refuse. Recharge ensuite la page.

## 5. Si la présence est refusée

La page affiche « présence refusée : » suivi de la raison, et ne réessaie pas : recharge-la une fois corrigé. « Copier le diagnostic » (touche I) montre le code 4003.

| Message affiché | Cause | Qui corrige |
|---|---|---|
| cette page n'est pas déclarée sur ce serveur de présence | l'origine de ta page n'est pas dans le fichier de l'hôte (faute de frappe, `www`, port) | l'hôte, ou toi si l'origine donnée était fausse |
| le créateur de cette page est suspendu sur ce serveur de présence | ton accès est suspendu | l'hôte |
| le salon de cette page n'appartient pas à son créateur sur ce serveur | `room` ne commence pas par ton préfixe | toi |
| son créateur a déjà tous les salons permis ouverts | `maxRooms` atteint | toi ou l'hôte |
| salon complet | plus de place pour les promeneurs (`maxWalkers` ou limite du serveur) | personne : attendre |

## 6. Journal des visites

L'hôte peut te donner une clé pour ton salon (`visits-key alice.galerie` dans sa console). Tu ouvres alors l'adresse de ta page suivie de `#visits`, depuis n'importe quel appareil, et tu tapes la clé : visites par jour, durées, export CSV. Le journal ne contient jamais d'adresse IP. Détail : manuel § 31.

## 7. Ce que le serveur enregistre

- **Le journal du serveur** (`--log`) : une ligne par évènement, avec le salon, le pseudo et **le texte de chaque message du chat**. L'adresse IP y est masquée par défaut (`--log-ip hash`), en clair avec `--log-ip raw`, absente avec `--log-ip none`. Conservation : `--log-days` (30 jours par défaut, `0` = sans limite).
- **L'historique du chat** (`--history-file`) : pseudo, texte, salon et heure, jamais d'adresse IP. Les 200 derniers messages d'un salon sont rejoués aux nouveaux arrivants (`--history`). Conservation : `--history-days` (30 jours par défaut, `0` = sans limite).
- **Le journal des visites** (`--visits`) : salon, arrivée, durée, temps de promenade, empreinte du navigateur ; jamais d'adresse IP ; le pseudo seulement avec `--visits-names`. Conservation : `--visits-days` (365 jours par défaut).
- **Le registre des pseudos** : chaque navigateur a une clé aléatoire ; le premier qui prend un pseudo le garde, les suivants reçoivent `NAME#CODE`.

Adresses IP, pseudos et messages sont des données personnelles : prévois d'informer tes visiteurs. La règle exacte dépend du pays, à vérifier de ton côté.

**Serveur de démonstration de Klaatou (état au 29/10/2026)** : adresses IP en clair (`--log-ip raw`), journal et historique du chat conservés sans limite de durée (`--log-days 0`, `--history-days 0`). Ce choix peut changer : demande à l'hôte.

## 8. Ce que tu ne contrôles pas

- La modération : l'hôte lit le journal et peut éjecter ou bannir un visiteur (`ejecter`, `bannir`).
- La suspension de ton accès, tes limites, la durée de conservation.
- La disponibilité du serveur : s'il s'arrête, ta page cesse ses essais de connexion après quelques tentatives et demande de la recharger (manuel § 36.4).

## 9. Essayé, non essayé

- **Essayé** (29/10/2026) : une page hébergée sur `https://NOMDUSITE.github.io`, son origine déclarée dans le fichier des créateurs du serveur de Klaatou, `wss://` fourni par Tailscale Funnel (procédures § 11) ; un visiteur extérieur s'y est promené.
- **Non essayé** : la page d'un créateur extérieur sur son propre domaine, Windows, Edge.
