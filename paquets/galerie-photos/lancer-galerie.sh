#!/bin/sh
# Sert le dossier site sur http://localhost (cette machine seulement) et ouvre la galerie.
# Linux ou macOS : sh lancer-galerie.sh   (macOS : double-clic sur lancer-galerie.command)
# Il faut Python 3.7 ou plus (commande python3). Arret : Ctrl+C dans ce terminal.
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python)
if [ -z "$PY" ] || ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)' 2>/dev/null; then
  echo "Python 3.7 ou plus est introuvable (commande python3)."
  echo "Linux : installez le paquet python3. macOS : tapez python3 dans le Terminal, le systeme propose de l'installer."
  printf "Entree pour fermer "; read -r _; exit 1
fi
exec "$PY" - site Galerie <<'PYEOF'
import http.server, os, sys, webbrowser
racine = os.path.abspath(sys.argv[1]); libelle = sys.argv[2]
if not (os.path.isfile(os.path.join(racine, 'index.html')) and os.path.isdir(os.path.join(racine, 'lib'))):
    print("Ce dossier est le CODE SOURCE du depot Web_3d : il manque site/index.html et site/lib.")
    print("Telechargez le paquet pret a l'emploi (region-simple.zip ou galerie-photos.zip) sur :")
    print("https://github.com/Klaatou/Web_3d/releases/latest")
    sys.exit(3)
types = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
         '.json': 'application/json; charset=utf-8', '.txt': 'text/plain; charset=utf-8', '.glb': 'model/gltf-binary', '.wasm': 'application/wasm',
         '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.gif': 'image/gif', '.ico': 'image/x-icon'}
class Gestionnaire(http.server.SimpleHTTPRequestHandler):
    extensions_map = dict(http.server.SimpleHTTPRequestHandler.extensions_map, **types)
    def __init__(self, *a, **k):
        super().__init__(*a, directory=racine, **k)
    def log_message(self, *a):
        pass
srv = None
for p in range(8000, 8021):
    try:
        srv = http.server.ThreadingHTTPServer(('localhost', p), Gestionnaire)
        break
    except OSError:
        pass
if srv is None:
    print("Impossible de demarrer le serveur local (ports 8000 a 8020 occupes).")
    sys.exit(1)
url = 'http://localhost:%d/' % srv.server_address[1]
print("%s sur %s - Ctrl+C (ou fermez ce terminal) pour arreter." % (libelle, url))
sys.stdout.flush()
try:
    webbrowser.open(url)
except Exception:
    pass
try:
    srv.serve_forever()
except KeyboardInterrupt:
    pass
PYEOF
