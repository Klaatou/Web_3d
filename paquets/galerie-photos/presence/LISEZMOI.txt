SERVEUR DE PRESENCE / PRESENCE SERVER
=====================================

FRANCAIS
--------
presence_server.py est une COPIE du serveur de presence de Web_3d :
  https://github.com/Klaatou/Web_3d  (dossier dist, version __VERSION_PRESENCE__, licence MIT).
Il relaie les positions des visiteurs et leurs messages de chat. Il est facultatif : sans lui, la galerie
marche, chaque visiteur est seul.

  1. Installez Python (python.org), puis : pip install websockets
  2. Dans CE dossier : python presence_server.py     (port 8765 par defaut)
  3. Dans site/galerie.config.json : "presenceUrl": "ws://*:8765"  et  "chat": true
  4. Servez la galerie avec "python -m http.server" lance dans le dossier site.
  Details : site/galerie.html, section 6.

Le serveur ECRIT SES FICHIERS ICI (pseudos reserves, bannissements ; journaux si vous les demandez).
Ne les copiez jamais dans le dossier site ni sur un hebergement.
Options (journal, conservation) : python presence_server.py --help ; documentation du depot Web_3d :
docs/fr/MANUEL.md (18.6, 18.7, 22.6) et docs/fr/PROCEDURES.md (6).
Pseudos, messages et adresses IP sont des donnees personnelles : prevenez vos visiteurs.

ENGLISH
-------
presence_server.py is a COPY of Web_3d's presence server:
  https://github.com/Klaatou/Web_3d  (dist folder, version __VERSION_PRESENCE__, MIT licence).
It relays visitors' positions and chat messages. It is optional: without it the gallery works, every
visitor is alone.

  1. Install Python (python.org), then: pip install websockets
  2. In THIS folder: python presence_server.py     (port 8765 by default)
  3. In site/galerie.config.json: "presenceUrl": "ws://*:8765"  and  "chat": true
  4. Serve the gallery with "python -m http.server" run in the site folder.
  Details: site/galerie.html, section 6.

The server WRITES ITS FILES HERE (reserved nicknames, bans; logs if you ask for them).
Never copy them into the site folder or onto a web host.
Options (log, retention): python presence_server.py --help ; documentation in the Web_3d repository:
docs/en/MANUAL.md (18.6, 18.7, 22.6) and docs/en/PROCEDURES.md (6).
Nicknames, messages and IP addresses are personal data: tell your visitors.
