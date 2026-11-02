#!/bin/sh
# macOS : double-clic dans le Finder (premier lancement : clic droit, Ouvrir)
cd "$(dirname "$0")" || exit 1
sh ./renommer-galerie.sh "$@"
printf "Entree pour fermer "; read -r _
