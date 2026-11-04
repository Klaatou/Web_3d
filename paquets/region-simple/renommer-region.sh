#!/bin/sh
# Renomme la region : fichiers de site/ (NOM.glb, NOM.config.json, NOM.zones.json), default.json, le salon de presence (cle "room") et la fiche de la carte (regions.json).
# Usage : sh renommer-region.sh NOUVEAU_NOM      (sans nom : il est demande)
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python)
if [ -z "$PY" ] || ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)' 2>/dev/null; then
  echo "Python 3.7 ou plus est introuvable (commande python3)."
  echo "Linux : installez le paquet python3. macOS : tapez python3 dans le Terminal, le systeme propose de l'installer."
  printf "Entree pour fermer "; read -r _; exit 1
fi
NOUVEAU="$1"
if [ -z "$NOUVEAU" ]; then printf "Nouveau nom (lettres, chiffres, tiret, souligne) : "; read -r NOUVEAU; fi
"$PY" - site "$NOUVEAU" <<'PYEOF'
import io, os, re, sys
site, nouveau = sys.argv[1], sys.argv[2]
defaut = os.path.join(site, 'default.json')
if not os.path.isfile(defaut):
    print("default.json introuvable dans le dossier site."); sys.exit(1)
def lire(c):
    with io.open(c, encoding='utf-8', newline='') as f:
        return f.read()
def ecrire(c, t):
    with io.open(c, 'w', encoding='utf-8', newline='') as f:
        f.write(t)
texte = lire(defaut)
m = re.search(r'"region"\s*:\s*"([^"]+)"', texte)
if not m:
    print('default.json illisible : il doit contenir {"region": "NOM"}.'); sys.exit(1)
ancien = m.group(1)
print("Nom actuel de la region : " + ancien)
if not re.fullmatch(r'[\w-]+', nouveau):
    print("Nom refuse : seulement des lettres, des chiffres, - et _ (ni espace, ni point)."); sys.exit(1)
if nouveau == ancien:
    print("C'est deja le nom actuel : rien a faire."); sys.exit(0)
for ext in ('.glb', '.config.json', '.zones.json'):
    if os.path.exists(os.path.join(site, nouveau + ext)):
        print("Un fichier " + nouveau + ext + " existe deja dans site : abandon, rien n'a ete modifie."); sys.exit(1)
for ext in ('.glb', '.config.json', '.zones.json'):
    src = os.path.join(site, ancien + ext)
    if os.path.exists(src):
        os.rename(src, os.path.join(site, nouveau + ext)); print("  renomme : " + ancien + ext + " -> " + nouveau + ext)
    elif ext == '.glb':
        print("  ATTENTION : " + ancien + ".glb est introuvable dans site : mettez votre GLB sous le nom " + nouveau + ".glb")
ecrire(defaut, re.sub(r'"region"\s*:\s*"' + re.escape(ancien) + '"', lambda _: '"region": "' + nouveau + '"', texte))
print("  default.json mis a jour")
config = os.path.join(site, nouveau + '.config.json')
if os.path.exists(config):
    c = lire(config)
    c2 = re.sub(r'"room"\s*:\s*"' + re.escape(ancien) + '"', lambda _: '"room": "' + nouveau + '"', c)
    if c2 != c:
        ecrire(config, c2); print("  salon de presence (room) mis a jour")
regions = os.path.join(site, 'regions.json')
if os.path.exists(regions):
    r = lire(regions)
    r2 = re.sub(r'("(?:id|room)"\s*:\s*")' + re.escape(ancien) + '"', lambda m: m.group(1) + nouveau + '"', r)
    r2 = re.sub(r'(region=)' + re.escape(ancien) + r'(?![\w-])', lambda m: m.group(1) + nouveau, r2)
    if r2 != r:
        ecrire(regions, r2); print("  carte (regions.json) mise a jour")
print("Termine. Rechargez la page (F5) ; le salon de presence s'appelle maintenant " + nouveau + ".")
PYEOF
exit $?
