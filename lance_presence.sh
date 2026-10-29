#!/bin/bash
# Lance le serveur de presence dans une boucle : s'il s'arrete, il repart apres 5 secondes.
# A ranger dans le dossier du serveur (a cote de presence_server.py), rendre executable : chmod +x lance_presence.sh
cd "$(dirname "$0")" || exit 1
while true; do
  python3 presence_server.py --host 127.0.0.1 --port 8765 --proxy-header X-Forwarded-For --log presence.log --log-ip raw --log-days 0 --history-file chat.jsonl --history-days 0 --visits visits.jsonl --creators presence_creators.json
  echo "Serveur arrete (code $?). Relance dans 5 secondes (pour l'arreter pour de bon : systemctl stop web3d-presence)."
  sleep 5
done
