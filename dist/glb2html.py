#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
glb2html - Génère une page HTML 100 % hors ligne à partir d'un .glb
(three.js + loaders + GLB intégrés dans le fichier, aucun accès réseau à l'ouverture).

Usage :
  python glb2html.py ile.glb
  python glb2html.py ile.glb -o ile.html --hole 90 --wave 1.2 --sea-y -30 --zoom 1.3
  python glb2html.py dossier_glb/ --no-sea
  python glb2html.py ile.glb --vendor C:\\chemin\\node_modules\\three   (aucun téléchargement)

Au premier lancement, les fichiers three.js nécessaires sont téléchargés une fois
dans ~/.cache/glb2html/three@VERSION, ensuite tout est local.
Draco et Meshopt gérés automatiquement (décodeurs intégrés seulement si le GLB en a besoin).
"""
from __future__ import annotations

VERSION = "1.4.5 (03/11/2026)"
SHELL_VERSION = "1.4.5 (03/11/2026)"   # numéro de version de la coquille (index.html) : écrit par build.py, ne change que si la coquille change
MAP_VERSION = "1.4.5 (03/11/2026)"       # numéro de version de la page de carte (carte.html) : idem

import argparse
import base64
import html
import json
import math
import pathlib
import re
import shutil
import struct
import time
import sys
import urllib.parse
import urllib.request

# ---- langue des messages (v36) : textes intégrés par build.py (src/i18n/*.json, clés py.*) ; --lang fr|en|auto ou WEB3D_LANG ----
import json as _json, locale as _locale, os as _os, pathlib as _pl, sys as _sys

# fabrication (build.py) : la ligne suivante devient I18N_DATA = { "fr": {...}, "en": {...} }
I18N_DATA = _json.loads(r'''{"en":{"_name":"English","py.common.help":"show this help message and exit","py.common.lang_help":"language of the messages and of this help: fr, en or auto (default: the system's language; environment variable WEB3D_LANG is equivalent). Available: {0}","py.common.optionals":"options","py.common.positionals":"arguments","py.common.version_mark":"{0}, fingerprint {1}","py.common.version":"show the version and exit","py.glb2html.0_1_fichiers_generes":"{0}/{1} files generated","py.glb2html.0_cle_s_changee_s":"{0} key(s) changed","py.glb2html.0_gardee_s_telle_s_quelle":", {0} kept as they are","py.glb2html.0_gltf_version_1_non_supportee":"{0}: glTF version {1} not supported","py.glb2html.0_introuvable":"{0} not found","py.glb2html.0_pas_un_glb_magic_absent":"{0}: not a GLB (magic number missing)","py.glb2html.0_premier_chunk_non_json":"{0}: first chunk is not JSON","py.glb2html.0_reference_des_fichiers_externes_1":"{0}: references external files {1} -> repack as a standalone GLB (npx @gltf-transform/cli copy in.gltf out.glb)","py.glb2html.0_taille_annoncee_1_taille_fichier":"{0}: announced size {1} != file size {2} (truncated?)","py.glb2html.0_textures_ktx2_basis_non_gerees":"{0}: KTX2/Basis textures not handled offline -> npx @gltf-transform/cli png in.glb out.glb","py.glb2html.absent_paren":" (missing)","py.glb2html.adresse_de_la_page_de_cette":"address of the page of this region (default: the name of the .html file, relative)","py.glb2html.adresse_s_de_regions_json_partage":"address(es) of shared regions.json, comma-separated: the page reads them again at each opening (http/https), merges them and completes them with the embedded map. Another site must allow access (CORS)","py.glb2html.afficher_le_nom_de_l_element":"show the name of the clicked element","py.glb2html.amplitude_vagues_0_10":"wave amplitude 0..10","py.glb2html.aucun_glb_dans_0":"No .glb in {0}","py.glb2html.aucune_cle_changee":"no key changed","py.glb2html.avertissement_0_0_0_0_est":"[WARNING] 0.0.0.0 is a listening address of the server, not a destination: replaced by 127.0.0.1 -> {0}","py.glb2html.avertissement_0_existe_et_differe_de":"[WARNING] {0} exists and differs from this version's shell: kept (the other regions share it). Delete it to renew it","py.glb2html.avertissement_0_introuvable_a_cote_de":"[WARNING] {0} not found beside the page (the region has neither .glb nor tiles here)","py.glb2html.avertissement_0_tuile_s_listee_s":"[WARNING] {0} tile(s) listed in {1} not found beside it (first: {2}); the page will report them and retry","py.glb2html.avertissement_default_ignore_sans_shared_shell":"Warning: --default is ignored without --shared-shell.","py.glb2html.avertissement_des_zones_sont_liees_a":"[WARNING] some zones are linked to a model element (mesh field), but {0} was written without object references (glb2tiles before v32): the page will ignore these zones (console warning). Split again with glb2tiles v32 to benefit from them.","py.glb2html.avertissement_map_page_ignore_aucune_region":"[WARNING] --map-page ignored: no region to show (give --register to register this region, or --map)","py.glb2html.avertissement_map_page_ignore_aucune_region_2":"[WARNING] --map-page ignored: no region to show (give --register or --map)","py.glb2html.avertissement_presence_url_doit_commencer_pa":"[WARNING] --presence-url must start with ws:// or wss:// (received: {0})","py.glb2html.avertissement_region_name_region_url_region":"[WARNING] --region-name, --region-url, --region-xy, --region-spawn and --thumb are only used with --register: ignored","py.glb2html.avertissement_register_et_map_page_ne":"[WARNING] --register and --map-page only apply to a .glb file, not to a folder","py.glb2html.avertissement_title_est_ignore_en_mode":"[WARNING] --title is ignored in modular mode: the page title is the room (--room) of the config","py.glb2html.avertissement_vignette_ignoree_jpg_png_webp":"[WARNING] thumbnail ignored (jpg/png/webp of 140 KB at most expected): {0}","py.glb2html.avertissement_vignette_introuvable_0":"[WARNING] thumbnail not found: {0}","py.glb2html.avertissement_vue_d_ensemble_0_introuvable":"[WARNING] overview {0} not found beside {1}; the page will work without it","py.glb2html.avertissement_zones_live_est_ignore_en":"[WARNING] --zones-live is ignored in modular mode: the zones are always read again from <page>.zones.json","py.glb2html.cache_telechargement_0":"[cache] downloading {0}","py.glb2html.image_nombre":"[image] \"{0}\": {1} exists, the name stays \"{0}\" (the page looks for the file by itself)","py.glb2html.image_completee":"[image] \"{0}\" -> {1}","py.glb2html.image_plusieurs":"[image] \"{0}\" -> {1} ({2} files match: the first in alphabetical order is used)","py.glb2html.image_sans_fichier":"[image] \"{0}\": no file \"{0}.jpg\", \"{0}-...\" in {1} (name left as is)","py.glb2html.carte_0_ajoutee_ou_mise_a":"[map] “{0}” added or updated in {1} ({2} region(s))","py.glb2html.carte_0_n_est_pas_a":"[map] {0} is not beside the page {1} (a relative path of --register is searched in the launch folder, otherwise in the tools folder). To write it beside the page: give a full path, or update the region with --update (paths relative to the page)","py.glb2html.carte_0_region_s_lue_s":"[map] {0} region(s) read from {1}","py.glb2html.carte_avec_maj_les_chemins_relatifs":"[map] with --update, the relative paths of --register, --map, --map-page and --thumb are relative to the page folder: {0}","py.glb2html.carte_des_mondes":"World map","py.glb2html.carte_page_carte_0_region_s":"[map] map page ({0} region(s)) -> {1}","py.glb2html.ce_n_est_pas_un_fichier":"this is not a viewer settings file","py.glb2html.ce_n_est_pas_un_objet":"this is not a JSON object","py.glb2html.chat_entre_visiteurs_necessite_presence_url":"chat between visitors (needs --presence-url; Enter key while walking)","py.glb2html.cible_camera_x_y_z":"camera target x,y,z","py.glb2html.compass":"compass at the top of the page: heading of the avatar (of the camera in global view) with the cardinal point and degrees (default: on)","py.glb2html.coquille_0_absente_ecrite":"shell {0} missing: written","py.glb2html.coquille_0_deja_a_jour_identique":"shell {0} already up to date (identical to the one from {1})","py.glb2html.coquille_0_deja_presente_et_identique":"[shell] {0} already present and identical","py.glb2html.coquille_0_ecrite":"[shell] {0} written","py.glb2html.coquille_0_plus_ancienne_que_1":"shell {0} older than {1}: renewed, old copy kept as {2}. This shell is shared by the other regions of the folder: they keep their behavior (old configurations are still understood)","py.glb2html.coquille_commune_0_adresse_1":"shared shell {0}; address: {1}","py.glb2html.coquille_modulaire_marqueur_s_non_remplace":"modular shell: marker(s) not replaced {0}","py.glb2html.couleur_ciel_ex_87ceeb":"sky color, e.g. 87ceeb","py.glb2html.couleur_mer_ex_3a9ad9":"sea color, e.g. 3a9ad9","py.glb2html.default_json_ecrit":"default.json written: {0} (default region: {1})","py.glb2html.default_region":"with --shared-shell: this region becomes the default region (default.json), opened when the address has no ?region=; without this option default.json is only written if it does not exist yet","py.glb2html.demi_largeur_du_fondu_du_trou":"half-width of the hole fade","py.glb2html.desc":"glb2html.py {0}: builds the web page of a region from a .glb (or from tiles), updates a region, registers it in the world map.","py.glb2html.dessine_aussi_les_arrivees_dans_la":"also draws the arrivals in the page (small discreet marker on the ground; default: never)","py.glb2html.direction_camera_x_y_z":"camera direction x,y,z","py.glb2html.distance_5_a_200_m_defaut":"distance (5 to 500 m, default 150) up to which the tooltip, the click, the portal marker (cone) and the displayed name (showName) of the zones work while walking","py.glb2html.entree_gltf_repacker_d_abord_en":".gltf input: repack as a .glb first (npx @gltf-transform/cli copy in.gltf out.glb)","py.glb2html.epilog":"Examples:\n  python glb2html.py island.glb\n  python glb2html.py island.glb -o island.html --hole 90 --wave 1.2 --sea-y -30 --zoom 1.3\n  python glb2html.py island.glb --shared-shell -o Island.html --presence-url ws://ADDRESS:8765\n  python glb2html.py -o Island.html --shared-shell --update --zone-info-dist 60\n  python glb2html.py glb_folder/ --no-sea\nThe first time, three.js is downloaded once into ~/.cache/glb2html (or --vendor FOLDER: no download).","py.glb2html.erreur_0":"[ERROR] {0}","py.glb2html.erreur_0_entree_de_tuile_invalide":"[ERROR] {0}: invalid tile entry ({1}): \"file\" must be a relative .glb path (without .. or :), \"min\" and \"max\" three numbers","py.glb2html.erreur_0_illisible_1":"[ERROR] {0} unreadable ({1})","py.glb2html.erreur_0_introuvable":"[ERROR] {0} not found","py.glb2html.erreur_0_introuvable_cherche_dans_1":"[ERROR] {0} not found (searched in {1} then in {2})","py.glb2html.erreur_0_introuvable_vendor_doit_pointer":"[ERROR] {0} not found (--vendor must point to the root of the npm three package)","py.glb2html.erreur_0_liste_tiles_absente_ou":"[ERROR] {0}: “tiles” list missing or empty (a file written by glb2tiles.py is expected)","py.glb2html.erreur_0_ou_1_introuvable_genere":"[ERROR] {0} or {1} not found: first generate the region with --shared-shell","py.glb2html.erreur_0_ou_1_introuvable_genere_2":"[ERROR] {0} or {1} not found: first generate the page with --modular","py.glb2html.erreur_0_overview_invalide_1_file":"[ERROR] {0}: invalid “overview” ({1}): “file” must be a relative .glb path (without .. or :)","py.glb2html.erreur_aucune_region_a_afficher_donne":"[ERROR] no region to show: give --map regions.json","py.glb2html.erreur_avec_maj_o_designe_la":"[ERROR] with --update, -o designates the region (e.g. -o Region.html), not a folder","py.glb2html.erreur_avec_tiles_o_designe_la":"[ERROR] with --tiles, -o designates the region (e.g. -o Region.html), not a folder","py.glb2html.erreur_config_only_demande_o_page":"[ERROR] --config-only needs -o <page.html> (the already generated modular page)","py.glb2html.erreur_enregistrer_une_region_sans_glb":"[ERROR] registering a region without .glb needs --region-name, --region-url and --room","py.glb2html.erreur_fichier_de_reglages_0_introuvable":"[ERROR] settings file {0} not found (searched in {1} then in {2})","py.glb2html.erreur_lib_url_refuse":"Error: --lib-url \"{0}\" refused (expected: relative path such as ../lib, or a full http(s) address, without ? # \\ or quotes).","py.glb2html.erreur_maj_0_introuvable_la_region":"[ERROR] --update: {0} not found, the region has not been generated yet. Generate it first, without --update: {1}","py.glb2html.erreur_maj_0_introuvable_si_la":"[ERROR] --update: {0} not found. If the region uses a shared shell, give --shared-shell NAME.html (default {1})","py.glb2html.erreur_maj_demande_o_region_html":"[ERROR] --update needs -o <Region.html> (the already generated region)","py.glb2html.erreur_maj_et_settings_s_excluent":"[ERROR] --update and --settings exclude each other: --update only takes the options given and the existing config","py.glb2html.erreur_nom_de_region_0_refuse":"[ERROR] region name “{0}” refused by the shared shell (a single file name, without / \\ : ? # or .., without a leading dot)","py.glb2html.erreur_nom_de_region_0_refuse_2":"[ERROR] region name “{0}” refused by the shared shell","py.glb2html.erreur_nom_de_region_0_refuse_3":"[ERROR] region name \"{0}\" refused by the shared shell (a single file name, without / \\ : ? # or .., no leading dot): choose another -o","py.glb2html.erreur_region_xy_attend_deux_nombres":"[ERROR] --region-xy expects two numbers: X,Y","py.glb2html.erreur_settings_sans_nom_demande_le":"[ERROR] --settings without a name needs the .glb (the file searched is <name of the .glb>.reglages.json)","py.glb2html.erreur_shared_shell_attend_un_nom":"[ERROR] --shared-shell expects an .html file (a name, or a path FOLDER/index.html for regions in sub-folders) (received \"{0}\")","py.glb2html.erreur_telechargement_impossible_0_utilise_v":"[ERROR] download impossible ({0}). Use --vendor <three folder>.","py.glb2html.erreur_tiles_demande_o_region_html":"[ERROR] --tiles needs -o <Region.html> (its name without extension is the region's)","py.glb2html.erreur_tiles_remplace_le_glb_ne":"[ERROR] --tiles replaces the .glb: do not give a .glb file with --tiles","py.glb2html.erreur_zones_only_demande_o_page":"[ERROR] --zones-only needs -o <page.html>","py.glb2html.erreur_zones_only_demande_zones_fichier":"[ERROR] --zones-only needs --zones FILE (or --settings): no zone to write","py.glb2html.erreur_zones_only_demande_zones_live":"[ERROR] --zones-only needs --zones-live (standalone page) or an already generated modular page ({0} not found beside the page)","py.glb2html.fichier_glb_ou_dossier_de_glb":".glb file or folder of .glb files","py.glb2html.fichier_json_de_zones_exporte_par":"zones .json file exported by the viewer; relative path: searched in the launch folder, then in the script folder. A zone can carry a mesh field (exact name of an element of the model): the element becomes clickable","py.glb2html.scan.help":"sites folder (shared shell at the root): updates its regions.json with the regions found (NAME.config.json) and their thumbnails (NAME.jpg, .png or .webp next to it); keeps names, places, arrivals, the header and external cards; deletes nothing","py.glb2html.scan.dryhelp":"with --scan-sites: shows the changes without writing anything","py.glb2html.scan.nofolder":"[ERROR] folder not found: {0}","py.glb2html.scan.noshell":"[WARNING] no index.html in {0}: the index.html?region=... addresses of the cards need the shell at the root","py.glb2html.scan.badcfg":"[WARNING] {0} unreadable, skipped: {1}","py.glb2html.scan.add":"  + {0} ({1}), place {2},{3}","py.glb2html.scan.upd":"  ~ {0}: {1}","py.glb2html.scan.orphan":"  ? {0}: {1} not found in the folder, card kept","py.glb2html.scan.summary":"regions.json: {0} added, {1} updated, {2} unchanged, {3} external kept, {4} orphan(s) -> {5}","py.glb2html.scan.dry":"--dry-run: nothing was written","py.glb2html.fichier_regions_json_a_mettre_a":"regions.json file to update with THIS region (added or updated per room); relative: launch folder if it exists there, otherwise script folder. The generated page embeds the up-to-date map","py.glb2html.fichier_regions_json_carte_des_mondes":"regions.json file (world map: name, address, position, thumbnail) exported by the viewer; relative path: launch folder, then script folder","py.glb2html.finesse_du_maillage_de_la_mer":"fineness of the sea mesh 8..1000 (cell = 4000/segments; only with --anim)","py.glb2html.format_attendu_x_y_z":"expected format: x,y,z","py.glb2html.gabarit_modulaire_cible_introuvable_ou_multi":"modular template: target not found or multiple ({0}...)","py.glb2html.genere_aussi_une_page_web_carte":"also generates a “world map” web page (clickable links to each region); without .glb: generates only this page from --map. Relative: beside the page of the region","py.glb2html.haute_resolution_rendu_x2_minimum_supersampl":"high resolution: x2 rendering at least (supersampling, sharper but ~4x heavier)","py.glb2html.hauteur_des_yeux_en_m_promenade":"eye height in m (walk)","py.glb2html.hauteur_mer_150_60":"sea height -150..60","py.glb2html.help.anim":"animate the sea (waves); --no-anim: still sea","py.glb2html.help.light":"the page opens in light rendering (half resolution, at most 15 frames/s, overview only in global view, no antialiasing) until the visitor chooses otherwise in Settings; --no-light: normal rendering","py.glb2html.help.sea":"show the sea (--no-sea: without the sea)","py.glb2html.identifiant_du_point_d_arrivee_des":"identifier of the arrival point of the visitors in this region (default: default)","py.glb2html.inclure_le_mode_promenade_touche_f":"include the walk mode (P and F keys) in the page","py.glb2html.la_page_recharge_ses_zones_a":"the page reloads its zones at each opening from a .zones.json file placed beside it (served over http/https; otherwise the embedded zones are used). Without NAME: <page>.zones.json. The file is written by the script, filtered according to --profile","py.glb2html.le_fichier_glb_ou_le_dossier":"the .glb file (or the folder) is required","py.glb2html.lib_url":"relative path (../lib) or full http(s) address where to find three.js and its modules; written in the \"const LIB\" line of the shell (editable by hand; --update keeps it) when it is written and kept in the config for --update. Relative path: lib/ is created there if missing; full address: nothing is copied","py.glb2html.m_charger_les_tuiles_dont_la":"m: load the tiles whose box is within this radius of the avatar, in the X,Z plane (default %(default)g; ?radius=NNN in the address to try)","py.glb2html.m_decharger_les_tuiles_au_dela":"m: unload the tiles beyond radius + margin (default %(default)g)","py.glb2html.maj_0_absent_ou_incomplet_ecrit":"[update] {0}/ missing or incomplete: written","py.glb2html.maj_0_conserve_tel_quel":"[update] {0} kept as is","py.glb2html.maj_0_mis_a_jour_glb2html":"[update] {0} updated (glb2html {1}): ","py.glb2html.maj_0_present_conserve":"[update] {0}/ present: kept","py.glb2html.maj_0_remplace_par_1":"[update] {0} replaced by {1}","py.glb2html.maj_le_profil_ne_filtre_les":"[update] the profile only filters the zones when the zone list is written: add --zones FILE to write it again","py.glb2html.maj_lib_repris":"[update] lib folder taken from the \"const LIB\" line of the shell: {0}","py.glb2html.marqueur_des_portails_et_zones_libres":"marker of the portals and free zones in the page: dot (default: 0.4 m disc and thin ring), range (thin sharp ring at the real radius of the zone, visible from afar) or none; the old values discret, portee and aucun are still accepted. The arrivals are never drawn (see --show-spawns)","py.glb2html.met_a_jour_une_region_deja":"updates an already generated region (-o REGION.html [--shared-shell [SHELL.html]] [--tiles X.tiles.json | X.glb]): reads X.config.json, applies ONLY the options given on the line, keeps everything else and X.zones.json (rewritten only with --zones), writes the current version and renews the shell if it is older (old copy kept under a dated name). Fails if X.config.json does not exist","py.glb2html.mo_de_tuiles_chargees_en_meme":"MB of tiles loaded at the same time (file weight; default %(default)g); beyond that, the farthest ones go first","py.glb2html.mode_modulaire_a_coquille_commune_une":"modular mode with a shared shell: a single shell (default {0}) serves several regions, at the address SHELL.html?region=NAME. -o designates the region (NAME = its name without extension, e.g. -o Ankh.html): only NAME.glb, NAME.config.json and NAME.zones.json are written, plus the shell, lib/three-X/ and (the first time) default.json if they are missing (an existing shell is never overwritten). With a path (--shared-shell FOLDER/index.html), -o may be in a sub-folder of FOLDER: address SHELL.html?region=sub/folder/NAME. --register writes this address in regions.json. Implies --modular","py.glb2html.mode_modulaire_ecrit_une_coquille_page":"modular mode: writes a shell <page>.html identical for all regions (it deduces its files from its name) + <page>.glb (raw bytes) + <page>.config.json (settings) + <page>.zones.json (zones, read again at each opening; otherwise zones.json of the folder) + shared lib/three-X/ (Draco and Meshopt included). Needs http(s) to open (not from the disk)","py.glb2html.nom_affiche_dans_la_carte_defaut":"name shown in the map (default: name of the .glb)","py.glb2html.materiaux_rendus_opaques":"names of materials drawn opaque (they then hide what is behind), comma-separated: \"1471516\" = any name containing this text, \"=pbrmat-123\" = exact name; \"\" = none","py.glb2html.noms_a_ignorer_en_collision_separes":"names to ignore in collisions, comma-separated: \"door\" = start of word, \"=mesh_346_5\" = exact name; \"\" = nothing","py.glb2html.north":"offset in degrees added to the displayed heading; 0 = north is the -Z direction of the model (OpenSim); for a GLB that does not come from OpenSim (default 0)","py.glb2html.ok_0_1_2_2f_mo":"[OK] {0} -> {1} ({2:.2f} MB glb, {3:.2f} MB html) [glb2html {4}]","py.glb2html.ok_0_1_2_3_coquille":"[OK] {0} -> {1} + {2} + {3}, shared shell {4}; address: {5} [glb2html {6}]","py.glb2html.ok_0_1_modulaire_coquille_2":"[OK] {0} -> {1} (modular: shell {2:.0f} KB + {3} {4:.2f} MB + {5} + {6} + {7}/) [glb2html {8}]","py.glb2html.ok_0_tuile_s_1_2":"[OK] {0} tile(s) -> {1} + {2}, ","py.glb2html.ok_region_mise_a_jour_adresse":"[OK] region updated ; address: {0} [glb2html {1}]","py.glb2html.ok_reglages_0_coquille_et_glb":"[OK] settings -> {0} (shell and .glb unchanged) [glb2html {1}]","py.glb2html.panneau_de_reglages_pour_les_visiteurs":"settings panel for the visitors (high resolution, animated sea, wave strength), button at the top right","py.glb2html.petit_cone_pointe_vers_le_bas":"small cone pointing down above each portal and each “enter” or “both” zone (marker visible up to --zone-info-dist; T key to show or hide it; default: shown; the arrivals only have one with --show-spawns)","py.glb2html.position_sur_la_grille_comme_opensim":"position on the grid, as in OpenSim (X to the east, Y to the north), e.g. 1000,1001","py.glb2html.position_x_du_centre_du_trou":"X position of the hole center (world)","py.glb2html.position_z_du_centre_du_trou":"Z position of the hole center (world)","py.glb2html.public_retire_les_zones_privees_ex":"public: removes the private zones (e.g. Home Assistant); private: keeps them (old value perso accepted)","py.glb2html.racine_d_un_paquet_npm_three":"root of a local npm three package (otherwise cache + download)","py.glb2html.ratio_de_cadrage_1_cadrage_auto":"framing ratio (1 = automatic framing)","py.glb2html.rayon_du_trou_30_600_zone":"hole radius 30..600 (flat zone = radius - fade)","py.glb2html.reecrit_seulement_les_zones_sans_regenerer":"rewrites only the zones, without regenerating the HTML: <page>.zones.json of an already generated modular page (with --zones FILE), or, with --zones-live, the zones file of a standalone page","py.glb2html.reecrit_seulement_page_config_json_d":"rewrites only <page>.config.json of an already generated modular page (given by -o), without touching the .glb or the shell; visitors reload. <page>.zones.json is only rewritten if --zones is given. With --register, also updates the map","py.glb2html.region_decoupee_en_tuiles_par_glb2tiles":"region split into tiles by glb2tiles.py: no .glb as input; -o designates the region. Writes X.config.json (“tiles” field), X.zones.json, the shell and lib/; X.tiles.json and its tiles are only copied if they are not already beside the page. Implies --modular. Frame = that of the original model (no recentering); zones linked to an object: possible if the tiles come from glb2tiles v32, ignored otherwise","py.glb2html.reglages_0_parametre_s_repris_de":"[settings] {0} parameter(s) taken from {1}","py.glb2html.reprend_tous_les_reglages_enregistres_par":"takes ALL the settings saved by the viewer (“Save to a file” button: hole, waves, camera, zones, region card, thumbnail…). Without a name: <name of the .glb>.reglages.json. The command-line options take precedence. Relative: launch folder, then script folder","py.glb2html.rotation_de_la_region_autour_de":"rotation of the region around the vertical axis (0, 90, 180 or 270 degrees), applied at loading before recentering. The zones, arrivals, target and hole of the zones / settings file are ALREADY in the rotated frame (the viewer rotates them with the region)","py.glb2html.salon_de_presence_defaut_nom_du":"presence room (default: file name)","py.glb2html.secondes_avant_disparition_des_messages_et":"seconds before messages and bubbles disappear; 0 = they stay until new messages replace them","py.glb2html.serveur_de_presence_ws_ou_wss":"presence server ws:// or wss:// (see presence_server.py); \"*\" instead of the name = the same name as the page (ws://*:8765, advised for a page opened through several addresses); empty = disabled","py.glb2html.seuil_alpha_feuillage_0_0_5":"foliage alpha threshold 0..0.5","py.glb2html.shell_name":"shell {0}","py.glb2html.sortie_fichier_html_ou_dossier_cree":"output: .html file, or folder (created if needed). Folder input: output folder. Default: \"<name> - Offline.html\" beside the .glb","py.glb2html.telechargements_simultanes_defaut_default_d":"simultaneous downloads (default %(default)d)","py.glb2html.titre_de_la_page":"page title","py.glb2html.triangles_de_tuiles_chargees_en_meme":"triangles of tiles loaded at the same time (default %(default)d)","py.glb2html.tuiles_0_copie_dans_1_tuiles":"[tiles] {0} copied into {1} ; tiles: {2} copied ({3:.1f} MB), {4} already present with the same size (neither checked nor copied again){5}","py.glb2html.tuiles_0_tuile_s_et_1":"[tiles] {0} tile(s) and {1} already beside the page: nothing is copied{2}","py.glb2html.tuiles_cible_de_camera_par_defaut":"[tiles] default camera target: {0} (center of the extent, original model frame; --target to change it)","py.glb2html.tuiles_des_zones_sont_liees_a":"[tiles] some zones are linked to an object (mesh field): the page places them with the object as soon as the tile that contains it is loaded","py.glb2html.tuiles_hauteur_de_la_mer_par":"[tiles] default sea height: 20 m (original model frame, like OpenSim water; --sea-y to change it, --no-sea to remove it)","py.glb2html.vignette_de_la_region_fichier_jpg":"thumbnail of the region: jpg/png/webp file of 140 KB at most (embedded), or http(s) address (kept as is, lighter map)","py.glb2html.vitesse_de_marche_en_m_s":"walking speed in m/s (Shift = x2.2)","py.glb2html.voir_les_visiteurs_en_promenade_depuis":"see the walking visitors from the global view (connects as soon as the page opens; on by default as soon as a --presence-url is given; --no-spectate to avoid it)","py.glb2html.vol_en_promenade_touche_f_ou":"flight while walking (Home key or button; Page Up / Space held goes up, Page Down / C goes down): on by default, --no-fly removes it","py.glb2html.vue_d_ensemble_0_placee_avec":" ; overview {0} placed with the tiles","py.glb2html.zones_0_non_modifie_donne_zones":"[zones] {0} unchanged (give --zones FILE to rewrite it)","py.glb2html.zones_0_zone_s_lue_s":"[zones] {0} zone(s) read from {1}","py.glb2html.zones_0_zone_s_profil_1":"[zones] {0} zone(s), profile {1} -> {2}","py.glb2html.zones_zones_deja_en_place_0":"[zones] zones already in place: {0} (not rewritten)","py.glb2html.zones_zones_deja_en_place_0_2":"[zones] zones already in place: {0} (read for checking, neither rewritten nor copied)","py.glb2tiles.0_1_0f_m_du_centre":"\"{0}\" ({1:.0f} m from the center, extent {2:.0f} m)","py.glb2tiles.0_1_2f_mo_2_triangles":"  - \"{0}\": {1:.2f} MB, {2} triangles, extent (X x Y x Z) {3}, {4} instance(s)","py.glb2tiles.0_distance_1_0f_m_etendue":"  - \"{0}\": distance {1:.0f} m, extent {2:.0f} m","py.glb2tiles.0_illisible_1":"{0} unreadable ({1}).","py.glb2tiles.0_instance_s_aberrante_s_a":"{0} outlying instance(s) (farther than {1:g} m from the median center or with a larger extent): {2}.","py.glb2tiles.0_introuvable_vue_ensemble_seule_suppose":"{0} not found: --overview-only assumes the split has already been done (in {1}).","py.glb2tiles.0_nud_s_avec_camera_ou":"{0} node(s) with a camera or node extensions: these fields are not copied into the tiles.","py.glb2tiles.0_objet_s_au_nom_correspondant":"  {0} object(s) with a matching name kept by the safeguards (too many triangles or meshes)","py.glb2tiles.0_octet_gagne_toute_la_geometrie":"  0 bytes gained: all the geometry and images of the excluded objects are shared with kept objects (same primitive or same texture, typically a common cube); removing these objects removes nodes and triangles, not bytes.","py.glb2tiles.0_scenes_seule_la_scene_1":"{0} scenes: only scene {1} is split.","py.glb2tiles.accessor_0_accessor_sparse_non_gere":"Accessor {0}: \"sparse\" accessor not supported by glb2tiles.","py.glb2tiles.accessor_0_bytestride_1_plus_petit":"Accessor {0}: byteStride ({1}) smaller than an element ({2}).","py.glb2tiles.accessor_0_depasse_son_bufferview_fichier":"Accessor {0}: exceeds its bufferView (invalid file).","py.glb2tiles.accessor_0_indices_avec_bytestride_non":"Accessor {0}: indices with byteStride not supported.","py.glb2tiles.accessor_0_inexistant":"Accessor {0} does not exist.","py.glb2tiles.accessor_0_positions_non_gerees":"Accessor {0}: positions not handled.","py.glb2tiles.accessor_0_sans_bufferview_valeurs_a":"Accessor {0}: without bufferView (zero values) not supported by glb2tiles.","py.glb2tiles.accessor_0_type_1_2_inconnu":"Accessor {0}: unknown type {1}/{2}.","py.glb2tiles.accessor_0_type_d_indices_non":"Accessor {0}: unsupported index type.","py.glb2tiles.accessor_0_un_indice_depasse_le":"Accessor {0}: an index exceeds the number of vertices ({1}): invalid file.","py.glb2tiles.analyse_0_primitives_distinctes_a_mesurer":"[analysis] {0} distinct primitives to measure (indices read in chunks)","py.glb2tiles.aucun_mesh_positionnable_dans_la_scene":"No placeable mesh in the scene: nothing to split.","py.glb2tiles.avec_exclure_meshes_au_plus_dans":"with --exclude: at most this many meshes in the root object (default 1)","py.glb2tiles.avec_exclure_triangles_au_plus_dans":"with --exclude: at most this many triangles in the root object, all meshes included (default 24)","py.glb2tiles.avertissement_0_d_une_execution_precedente":"Warning: {0} from a previous run is not removed, but the index no longer mentions it (--no-overview).","py.glb2tiles.avertissement_0_existe_deja_mais_ses":"Warning: {0} already exists but its tiles do not carry object references (glb2tiles before v32): to link zones to objects in tile mode, redo the split.","py.glb2tiles.avertissement_ces_tuiles_ont_ete_ecrites":"Warning: these tiles were written without object references (glb2tiles before v32): zones linked to an object remain ignored in tile mode. Redo the split (without --overview-only) to benefit from them.","py.glb2tiles.bufferview_0_inexistant":"bufferView {0} does not exist.","py.glb2tiles.bufferview_0_seul_le_tampon_0":"bufferView {0}: only buffer 0 is supported.","py.glb2tiles.ce_glb_est_compresse":"This GLB is compressed (","py.glb2tiles.cellules_sur_la_plus_grande_dimension":"cells along the largest dimension of a primitive for vertex clustering (default %(default)d)","py.glb2tiles.cote_des_blocs_de_la_section":"side of the blocks of the glb-stats section of --analyse (default 256)","py.glb2tiles.cote_minimal_d_une_cellule_en":"minimum side of a cell in m (default 16)","py.glb2tiles.couleurs_moyenne_de_texture_pour_0":"  colors: texture average for {0} image(s), {1} unreadable (base color)","py.glb2tiles.couleurs_pillow_absent_couleur_de_base":"  colors: Pillow missing, material base color ({0} textured material(s) concerned); install Pillow for average colors","py.glb2tiles.decoupage_prevu_budget_0_g_mo":"== Planned split (budget {0:g} MB, {1} triangles, minimum cell {2:g} m) ==","py.glb2tiles.decouper_meme_si_la_recommandation_est":"split even if the recommendation is \"no split\"","py.glb2tiles.des_primitives_portent_des_extensions_elles":"Some primitives carry extensions: they are not copied into the tiles.","py.glb2tiles.desc":"glb2tiles.py {0}: splits a huge GLB into standalone tiles and writes X.tiles.json and the overview X.overview.glb (standard Python only).","py.glb2tiles.dossier_de_sortie_defaut_a_cote":"output folder (default: beside the GLB)","py.glb2tiles.duplication_reelle_de_la_geometrie_somme":"Actual geometry duplication (sum of the tiles / unique geometry): {0}","py.glb2tiles.entree_pour_fermer":"Press Enter to close...","py.glb2tiles.epilog":"Examples:\n  python glb2tiles.py Region.glb --analyse\n  python glb2tiles.py Region.glb --budget 32 --budget-triangles 1500000\n  python glb2tiles.py Region.glb --overview-only\nThe log is glb2tiles.log, written beside the script. glb-stats.py must be beside this script.","py.glb2tiles.erreur_0":"[ERROR] {0}","py.glb2tiles.etendue_des_instances_plus_grande_dimension":"Extent of the instances (largest dimension): instances and triangles above each threshold","py.glb2tiles.etendue_minimale_effective_0_g_m":"  effective minimum extent {0:g} m (requested threshold {1:g} m), resolution {2}, terrain step {3:g} m (requested {4:g} m)","py.glb2tiles.expression_reguliere_invalide_pour_exclure_0":"Invalid regular expression for --exclude: {0!r} ({1}).","py.glb2tiles.fichier_glb_tronque":"Truncated GLB file.","py.glb2tiles.glb2tiles_0":"[glb2tiles] {0}","py.glb2tiles.glb2tiles_0_1_1f_mo":"[glb2tiles] {0}: {1:.1f} MB","py.glb2tiles.glb2tiles_0_2":"glb2tiles {0}","py.glb2tiles.glb2tiles_ne_lit_pas_les_glb":"): glb2tiles does not read compressed GLBs (out of scope). Decompress the GLB first, then run again.","py.glb2tiles.glb_d_entree":"input GLB","py.glb2tiles.glb_introuvable_0":"GLB not found: {0}","py.glb2tiles.glb_stats_py_introuvable_a_cote":"glb-stats.py not found beside glb2tiles.py ({0}): copy it to the same place.","py.glb2tiles.image_externe_uri_non_geree_seuls":"External image (uri) not supported: only GLBs with embedded images are.","py.glb2tiles.images_vides_ou_invalides_remplacees_par":"Empty or invalid images replaced by a gray {0} PNG: {1} distinct, {2} occurrence(s) (one occurrence = one image written in a tile); materials and texture coordinates unchanged.","py.glb2tiles.la_tuile_0_n_a_plus":"Tile {0} no longer has the content of {1}: use the same options as for the original split.","py.glb2tiles.la_vue_d_ensemble_depasse_la":"The overview exceeds the 4 GB limit of a GLB.","py.glb2tiles.le_decoupage_recalcule_0_tuiles_ne":"The recomputed split ({0} tiles) does not match {1} ({2} tiles): use the same options (--budget, --budget-triangles, --min, --entier-*, --exclude...) as for the original split.","py.glb2tiles.le_tampon_0_a_une_adresse":"Buffer 0 has an address (uri): only GLBs with an embedded buffer are supported.","py.glb2tiles.lecture_0_octets_lus_sur_1":"Reading: {0} bytes read out of {1} (largest read {2} bytes; positions read again for {3} bytes, primitives sharing a vertex buffer).","py.glb2tiles.lecture_hors_du_tampon_du_glb":"Read outside the GLB buffer (offset {0}, {1} bytes): invalid or truncated file.","py.glb2tiles.lecture_seule_mesures_decoupage_prevu_recomm":"read-only: measurements, planned split, recommendation; writes nothing","py.glb2tiles.les_10_instances_les_plus_eloignees":"== The 10 instances farthest from the median center (X {0:.0f} m, Z {1:.0f} m) ==","py.glb2tiles.les_10_meshes_les_plus_lourds":"== The 10 heaviest meshes (compacted bytes, vertices really used) ==","py.glb2tiles.log_0":"[log] {0}","py.glb2tiles.m_distance_ou_etendue_au_dela":"m: distance or extent beyond which an instance is reported (default 1000)","py.glb2tiles.m_etendue_maximale_d_un_objet":"m: maximum extent of a root object kept whole (default 256)","py.glb2tiles.m_les_objets_dont_la_plus":"m: objects whose largest dimension is smaller are omitted (default %(default)g); the budget may raise it","py.glb2tiles.m_pas_du_reseau_du_terrain":"m: step of the terrain grid in the overview (default %(default)g)","py.glb2tiles.m_si_le_budget_oblige_a":"m: if the budget forces larger objects to be omitted, the resolution drops (default %(default)g)","py.glb2tiles.machine_big_endian_non_geree":"Big-endian machine not supported.","py.glb2tiles.mesh_0_primitive_sans_position_non":"Mesh {0}: primitive without POSITION not supported.","py.glb2tiles.mesures_de_glb_stats":"== glb-stats measurements ==","py.glb2tiles.mo_par_tuile_defaut_32":"MB per tile (default 32)","py.glb2tiles.mo_poids_maximal_de_la_vue":"MB: maximum weight of the overview (default %(default)g)","py.glb2tiles.mo_sous_ce_poids_et_sous":"MB: under this weight (and under --threshold-triangles) \"no split\" (default 150)","py.glb2tiles.mo_un_objet_racine_plus_leger":"MB: a root object lighter than this and smaller than --whole-extent stays whole (default 16)","py.glb2tiles.n_ecrire_que_x_overview_glb":"write only X.overview.glb (and its mention in X.tiles.json): existing tiles are not rewritten; the split parameters must be those of the original split","py.glb2tiles.ne_pas_attendre_entree_a_la":"do not wait for Enter at the end","py.glb2tiles.ne_pas_ecrire_extras_ref_extras":"do not write extras.ref / extras.box in the tile nodes (v31 format: zones linked to an object are then ignored in tile mode)","py.glb2tiles.ne_pas_ecrire_x_overview_glb":"do not write X.overview.glb (light overview of the whole region)","py.glb2tiles.nud_0":"node {0}","py.glb2tiles.nud_0_mesh_1_inexistant":"Node {0}: mesh {1} does not exist.","py.glb2tiles.objets_exclus_exclure_au_plus_0":"Excluded objects (--exclude, at most {0} triangles and {1} mesh(es) per root object): {2} | triangles removed: {3} | bytes gained: {4} ({5:.1f} MB)","py.glb2tiles.objets_omis_0_trop_petits_etendue":"  objects omitted: {0} too small (extent under the threshold), {1} by the budget, {2} with a skeleton; translucent primitives omitted: {3}","py.glb2tiles.objets_racine_0_gardes_entiers_1":"Root objects: {0} | kept whole: {1} (of which {2} with a skin) | spread instance by instance: {3}","py.glb2tiles.objets_racine_gardes_entiers_0_repartis":"Root objects kept whole: {0} | spread: {1}","py.glb2tiles.octets_des_exclus_qu_un_objet":"  bytes of excluded objects that a kept object also uses (not gained): {0} ({1:.1f} MB)","py.glb2tiles.poids_mo_mediane_0_1f_90":"Weight (MB): median {0:.1f} | 90 % under {1:.1f} | maximum {2:.1f}","py.glb2tiles.poids_par_tuile_mo_mediane_0":"Weight per tile (MB): median {0:.1f} | 90 % under {1:.1f} | maximum {2:.1f}","py.glb2tiles.primitive_les_attributs_n_ont_pas":"Primitive: the attributes do not all have {0} vertices (accessor {1}).","py.glb2tiles.rapport":"== Report ==","py.glb2tiles.recommandation_decouper_budget_0_g_mo":"Recommendation: split: budget {0:g} MB, {1} tiles, duplication {2}.","py.glb2tiles.recommandation_pas_de_decoupage_necessaire_0":"Recommendation: no split needed ({0:.1f} MB under {1:g} MB and {2} triangles under {3}).","py.glb2tiles.references_d_objets_extras_ref_extras":"Object references (extras.ref, extras.box): {0} named node(s), {1} name(s) shared by several nodes (name#index reference): zones linked to an object possible in tile mode.","py.glb2tiles.references_d_objets_non_ecrites_sans":"Object references not written (--no-refs): zones linked to an object will be ignored in tile mode.","py.glb2tiles.retire_du_decoupage_les_objets_racine":"removes from the split the root objects whose name matches (case-insensitive, repeatable), provided --exclude-max-triangles and --exclude-max-meshes are respected","py.glb2tiles.rien_n_est_ecrit_forcer_pour":"Nothing is written (--force to split anyway).","py.glb2tiles.sans_instance":"no instance","py.glb2tiles.sans_vue_ensemble_et_vue_ensemble":"--no-overview and --overview-only are mutually exclusive.","py.glb2tiles.skin_0_inexistant":"Skin {0} does not exist.","py.glb2tiles.temps_0_1f_s":"[time] {0:.1f} s","py.glb2tiles.temps_0_1f_s_1_octets":"[time] {0:.1f} s; {1} bytes read out of {2}","py.glb2tiles.texture_0_inexistante":"Texture {0} does not exist.","py.glb2tiles.triangles_de_la_vue_d_ensemble":"triangles of the overview (default %(default)d)","py.glb2tiles.triangles_mediane_0_90_sous_1":"Triangles: median {0} | 90 % under {1} | maximum {2}","py.glb2tiles.triangles_par_tuile_defaut_1500000":"triangles per tile (default 1500000)","py.glb2tiles.triangles_par_tuile_mediane_0_90":"Triangles per tile: median {0} | 90 % under {1} | maximum {2}","py.glb2tiles.triangles_pour_la_recommandation_pas_de":"triangles for the \"no split\" recommendation (default 3000000)","py.glb2tiles.tuile_0_1_2f_go_au":"Tile {0}: {1:.2f} GB, beyond the 4 GB limit of a GLB.","py.glb2tiles.tuile_0_hors_budget_1_1f":"Tile {0} over budget ({1:.1f} MB, {2} triangles): {3}. A single mesh larger than a cell cannot be spread at this stage.","py.glb2tiles.tuiles_0_dans_1":"Tiles: {0} in {1}","py.glb2tiles.tuiles_0_duplication_prevue_geometrie_1":"Tiles: {0} | planned duplication: geometry {1}, images {2}","py.glb2tiles.tuiles_d_une_execution_precedente_absentes":"Tiles from a previous run absent from the new index: {0} T_*.glb file(s) deleted","py.glb2tiles.vue_d_ensemble_0_1_1f":"Overview {0}: {1:.1f} MB, {2} triangles (of which terrain {3}), {4} object(s) kept out of {5}, in {6:g} s","py.glb2tiles.vue_d_ensemble_0_1f_mo":"[overview] {0:.1f} MB, {1} triangles, {2} object(s) out of {3}, {4} tile(s) in {5:.1f} s","py.glb2tiles.vue_d_ensemble_budget_0_g":"[overview] budget {0:g} MB and {1} triangles, extent threshold {2:g} m, resolution {3}, terrain step {4:g} m","py.glb2tiles.vue_d_ensemble_budget_atteint_avant":"[overview] budget reached before objects of {0:.0f} m: resolution reduced to {1}","py.glb2tiles.vue_d_ensemble_terrain_0_piece":"[overview] terrain: {0} piece(s), {1} triangles, grid of {2:g} m","py.glb2tiles.vue_d_ensemble_terrain_trop_lourd":"[overview] terrain too heavy for half the budget: step raised to {0:g} m","py.glb2tiles.warning_prefix":"Warning: ","py.oar2glb.0_5d_1_2_3_rigge":"{0:5d} | {1} | {2} | {3} | rigged: {4} | prim scale {5} | bind_shape scale {6} | transparent: {7} | animesh root box: {8} | GLB: {9}","py.oar2glb.0_face_s_a_part":" (+{0} separate face(s))","py.oar2glb.accesseur_0_non_gere":"accessor {0} not supported","py.oar2glb.accesseur_0_non_gere_float_vec3":"accessor {0} not supported (plain float VEC3 expected)","py.oar2glb.accesseur_position_0_bufferview_1_buffer":"      POSITION accessor {0}; bufferView {1}; buffer {2} {3} B; first 3 vertices {4}","py.oar2glb.ajouter_un_mat_rouge_de_15":"add a red 15 m pole to each placed rigged animal (to find it in the viewer)","py.oar2glb.altitude_de_la_racine":"altitude of the root","py.oar2glb.args":"[args]","py.oar2glb.aucune":"none","py.oar2glb.aucune_geometrie":"no geometry","py.oar2glb.avec_diag_glb_ou_gltf_a":"with --diag: GLB or .gltf to compare; default: the .gltf of the <oar>-GLTF folder (kept by --keep), otherwise the neighbouring .glb","py.oar2glb.avec_terrain_seul_fichier_glb_de":"with --terrain-only: output GLB file (default: X-terrain.glb beside the original)","py.oar2glb.bind_shape_matrix_0":"      bind_shape_matrix: {0}","py.oar2glb.bind_shape_matrix_non_inversible":"non-invertible bind_shape_matrix","py.oar2glb.bloc_skin_present_mais_illisible":"skin block present but unreadable","py.oar2glb.boite_racine_d_animesh":"animesh root box","py.oar2glb.cle_llsd_attendue":"LLSD key expected","py.oar2glb.controle_0_pieds_a_1_2f":"[check] '{0}' feet at {1:.2f} m, center {2:.2f} m: ","py.oar2glb.convoar":"[convoar]","py.oar2glb.convoar_0_image_s_annoncee_s":"[convoar] {0} image(s) announced by the .gltf but missing from the folder (examples: {1}): new attempt {2}/{3}, images already written are kept","py.oar2glb.convoar_0_image_s_recuperee_s":"[convoar] {0} image(s) recovered from the previous attempt","py.oar2glb.convoar_code_retour_0":"[convoar] return code {0}","py.oar2glb.correctif_0_mesh_es_rigge_s":"[fix] {0} rigged mesh(es) rescaled, {1} invisible prim(s) removed","py.oar2glb.cote_d_un_patch_de_terrain":"side of a terrain patch in meters, 2 to 255 (default {0})","py.oar2glb.dans_la_boite_de_0_objet":"inside the box of {0} object(s): {1}","py.oar2glb.defaut_d_opensim_aucun_waterheight_dans":"OpenSim default, no WaterHeight in settings/","py.oar2glb.desc":"oar2glb.py {0}: converts an OpenSim region backup (.oar) into a single GLB (convoar, repair, full terrain, packing).","py.oar2glb.dessous_de_la_boite_racine":"underside of the root box","py.oar2glb.diag_0_objet_s_1_partie":"[diag] {0} object(s), {1} part(s); terrain {2}; {3}","py.oar2glb.diag_nuds_glb_dont_tous_les":"[diag] GLB nodes whose materials are all transparent: {0}","py.oar2glb.diag_pos":"      position {0} ; terrain {1} ; {2}","py.oar2glb.diag_rigges_0_transparents_1_boites":"[diag] rigged: {0}; transparent: {1}; animesh root boxes: {2}; GLB nodes found: {3}/{4}","py.oar2glb.diag_uuid_lisibles_dans_les_nuds":"[diag] readable UUIDs in GLB nodes: {0}; example nodes:","py.oar2glb.domaine_de_position_du_mesh_0":"      mesh position domain ({0} submesh(es)): ","py.oar2glb.echelle_du_prim_appliquee_0":" ; prim scale applied: {0}","py.oar2glb.en_tete_du_mesh_illisible_0":"unreadable mesh header ({0})","py.oar2glb.entree_pour_fermer":"Press Enter to close...","py.oar2glb.epilog":"Examples:\n  python oar2glb.py \"P:\\path\\MyRegion.oar\"\n  python oar2glb.py \"P:\\path\\MyRegion.oar\" --keep --markers\n  python oar2glb.py \"P:\\path\\MyRegion.oar\" --diag        (changes nothing, does not run convoar)\n  python oar2glb.py --terrain-only MyRegion.glb \"P:\\path\\MyRegion.oar\"","py.oar2glb.erreur_0_introuvable":"[ERROR] {0} not found","py.oar2glb.erreur_0_introuvable_annonce_par_le":"[ERROR] {0} not found (announced by the .gltf).\n  {1} contains {2} file(s), of which {3} .buf: ","py.oar2glb.erreur_0_le_premier_chunk_n":"[ERROR] {0}: the first chunk is not JSON","py.oar2glb.erreur_0_le_tampon_0_n":"[ERROR] {0}: buffer 0 is not the BIN chunk's","py.oar2glb.erreur_0_n_est_pas_un":"[ERROR] {0} is not a GLB","py.oar2glb.erreur_0_n_est_pas_un_2":"[ERROR] {0} is not a version 2 GLB","py.oar2glb.erreur_0_tronque":"[ERROR] {0} truncated","py.oar2glb.erreur_0_vecteurs_de_mauvaise_taille":"[ERROR] {0} vectors of the wrong size: numbers written with a decimal comma.\n  ","py.oar2glb.erreur_aucun_gltf_produit_dans_0":"[ERROR] no .gltf produced in {0}","py.oar2glb.erreur_compilation_du_lanceur_0_1":"[ERROR] launcher compilation:\n{0}{1}","py.oar2glb.erreur_convoar_introuvable_0_utilise_convoar":"[ERROR] convoar not found: {0}\n  convoar.exe is the external converter oar2glb.py needs. Download: {1}\n  Give its location with --convoar PATH (or the CONVOAR variable, or put it in the PATH).","py.oar2glb.erreur_csc_exe_net_framework_4":"[ERROR] csc.exe (.NET Framework 4) not found","py.oar2glb.erreur_gltf_invalide_0_ligne_1":"[ERROR] invalid .gltf: {0}\n  line {1}: {2}","py.oar2glb.erreur_la_sortie_ne_peut_pas":"[ERROR] the output cannot be the original GLB (never overwritten)","py.oar2glb.erreur_reencode_demande_pillow_absent_de":"[ERROR] --reencode needs Pillow, missing from this Python ({0}).\n  Install it in this exact Python: & \"{1}\" -m pip install pillow","py.oar2glb.erreur_terrain_patch_doit_etre_compris":"[ERROR] --terrain-patch must be between 2 and 255 (16-bit indices: (side + 1)² vertices at most 65,536)","py.oar2glb.espace_libre_sur_0_1_1f":"\n  Free space on {0}: {1:.1f} GB","py.oar2glb.etendue_0_objets_de_1_a":"[extent] {0} objects from {1} to {2}  (glTF: X, height, -Y)","py.oar2glb.fin_de_table_llsd_attendue":"end of LLSD map expected","py.oar2glb.fin_de_tableau_llsd_attendue":"end of LLSD array expected","py.oar2glb.force_terrain_oui":"forced (--terrain yes)","py.oar2glb.garder_les_fichiers_intermediaires":"keep the intermediate files","py.oar2glb.garder_les_prims_entierement_transparents_re":"keep fully transparent prims (removed by default)","py.oar2glb.geometrie_du_llmesh_illisible":"unreadable .llmesh geometry","py.oar2glb.glb_0_1":"[GLB] {0} -> {1}","py.oar2glb.glb_0_contient_1_fichier_s":"[GLB] {0} contains {1} file(s): ","py.oar2glb.glb_0_texture_s_absente_s":"[GLB] {0} texture(s) missing out of {1}, replaced by gray. Examples: ","py.oar2glb.glb_fichiers_images_presents_exemples":"[GLB] image files present, examples: ","py.oar2glb.hauteur_max_m_d_un_objet":"maximum height (m) of a root object (skybox beyond), default 600","py.oar2glb.help.convoar":"path of convoar.exe (default: the CONVOAR variable, otherwise convoar from the PATH, otherwise convoar.exe next to oar2glb.py; download: https://github.com/Misterblue/convoar/tree/master/bin)","py.oar2glb.help.oar":"the .oar (or .tgz) file of the region to convert","py.oar2glb.hors_region_node_0_1_a":"[outside region] node {0} '{1}' at {2} removed","py.oar2glb.invisible_node_0_1_retire_2":"[invisible] node {0} '{1}' removed: {2}","py.oar2glb.lanceur_0_compile_1":"[launcher] {0} compiled ({1})","py.oar2glb.lanceur_0_mis_a_jour_loadfromremotesources":"[launcher] {0} updated (loadFromRemoteSources)","py.oar2glb.le_nud_n_a_pas_de":"the node has no mesh","py.oar2glb.les_patches_de_terrain_sont_deja":"the terrain patches are already in this GLB: unchanged","py.oar2glb.libre_aucune_boite_d_objet_ne":"free (no object box contains it)","py.oar2glb.list_paren":" (list: {0})","py.oar2glb.log_0":"[log] {0}","py.oar2glb.lu_dans":"read in ","py.oar2glb.materiau_glb_0_r_couleur_1":"      GLB material: {0!r} color {1} mode {2} image {3}","py.oar2glb.materiaux_transparents_glb":"transparent materials (GLB)","py.oar2glb.ne_pas_attendre_entree_a_la":"do not wait for Enter at the end","py.oar2glb.ne_pas_lancer_convoar_ajouter_le":"do not run convoar: add the full terrain to this GLB (writes X-terrain.glb, the original is never modified)","py.oar2glb.ne_rien_modifier_lister_les_objets":"modify nothing: list the objects of the OAR, their skin and the matching GLB node","py.oar2glb.node_0_nom_1_r_extras":"       node {0}: name={1!r} extras={2} keys={3}","py.oar2glb.non_pas_un_mesh":"no (not a mesh)","py.oar2glb.nud":"node","py.oar2glb.nud_0_1_2_echelle_du":"node {0} '{1}' [{2}]; node scale {3}","py.oar2glb.nud_introuvable":"node not found","py.oar2glb.nud_terrain_sans_min_max_d":"\"Terrain\" node without accessor min/max: coverage unknown, unchanged (--terrain yes to force)","py.oar2glb.oar2glb_0":"[oar2glb] {0}","py.oar2glb.oar2glb_0_2":"oar2glb {0}","py.oar2glb.oar_0_illisible_1":"[OAR] {0} unreadable ({1})","py.oar2glb.oar_0_objets_de_1_a":"[OAR] {0} objects from {1} to {2}  (OpenSim X, Y, Z, Z = height)","py.oar2glb.oar_region_0_g_x_1":"[OAR] region {0:g} x {1:g} m","py.oar2glb.ok_0_1_1f_mo_2":"[OK] {0}  ({1:.1f} MB, {2} meshes, {3} textures, {4} object(s) outside the region removed)","py.oar2glb.pas_de_glb_correspondance_non_evaluee":"no GLB: match not evaluated (--glb)","py.oar2glb.pas_de_nud_terrain_de_convoar":"no convoar \"Terrain\" node: unchanged (--terrain yes to add the patches anyway)","py.oar2glb.reencoder_les_textures_j2k_avant_convoar":"re-encode J2K textures before convoar","py.oar2glb.reperes_0_mat_s_rouge_s":"[markers] {0} red 15 m pole(s) added, one per placed animal","py.oar2glb.rien":"nothing","py.oar2glb.rigge_0_1_ignore":"[rigged] '{0}': {1}, ignored","py.oar2glb.rigge_0_1_morceau_x_echelle":"[rigged] '{0}': {1} piece(s), prim scale {2}, {3:.2f} x {4:.2f} x {5:.2f} m (L x W x H), centered at ({6:.1f}, {7:.1f}), feet at {8:.2f} m ({9})","py.oar2glb.rigge_0_1_non_corrige":"[rigged] '{0}': {1}, not corrected","py.oar2glb.rigge_0_1_nud_glb_introuvable":"[rigged] '{0}' ({1}): GLB node not found, not corrected (see --diag)","py.oar2glb.rigge_0_reconstruit_depuis_l_oar":"[rigged] '{0}' rebuilt from the OAR: {1} face(s), {2} vertices, {3} triangles (convoar: {4} primitive(s), {5} vertices), prim scale ignored {6}, bind_shape scale {7}","py.oar2glb.rigge_0_taille_obtenue_1_2f":"[rigged] '{0}': obtained size {1:.2f} x {2:.2f} x {3:.2f} m implausible (outside {4:g} to {5:g} m), left as convoar produced it","py.oar2glb.sans_bind_shape_matrix":"without bind_shape_matrix","py.oar2glb.sans_extension":"(no extension)","py.oar2glb.sans_textureentry":"without TextureEntry","py.oar2glb.sommets_du_glb_axes_opensim_x":"      GLB vertices (OpenSim axes x, y, z): from {0} to {1}, i.e. {2} m, {3} vertices","py.oar2glb.sommets_du_glb_illisibles_0":"      unreadable GLB vertices ({0})","py.oar2glb.terrain_0":"[terrain] {0}","py.oar2glb.terrain_0_nud_s_terrain_de":"[terrain] {0} convoar \"Terrain\" node(s) removed from the scene","py.oar2glb.terrain_0_nud_s_terrain_retire":"[terrain] {0} \"Terrain\" node(s) removed from the scene (their data stay in the GLB, unused); {1:.1f} MB read, in chunks of at most {2} KB","py.oar2glb.terrain_attention_carte_de_0_x":"[terrain] warning: map of {0} x {1} samples for a region of {2:g} x {3:g} m","py.oar2glb.terrain_aucun_fichier_ecrit":"[terrain] no file written","py.oar2glb.terrain_carte_0_x_1_echantillons":"[terrain] map {0} x {1} samples (1 m); water level {2:g} m ({3}); {4} patch(es) of {5} m; {6} vertices; {7:.1f} MB added; {8:.1f} s","py.oar2glb.terrain_cet_oar_n_a_pas":"[terrain] this OAR has no height map (terrains/*.r32): terrain not generated, nothing is modified","py.oar2glb.terrain_complet_depuis_la_carte_de":"full terrain from the height map: auto = replaces the convoar terrain if it covers less than the map (default), oui = always, non = never","py.oar2glb.terrain_de_convoar_complet_couvre_0":"complete convoar terrain (covers {0:.1f} % of the map): unchanged","py.oar2glb.terrain_de_convoar_incomplet_couvre_0":"incomplete convoar terrain (covers {0:.1f} % of the map)","py.oar2glb.terrain_desactive_terrain_non":"[terrain] disabled (--terrain no)","py.oar2glb.texture_0_alpha_1_2f":"texture {0} alpha {1:.2f}","py.oar2glb.textures_0_1_2_3_0f":"[textures] {0}/{1} ({2} %) - {3:.0f} s","py.oar2glb.textures_0_reencodees_1_illisibles_remplacee":"[textures] {0} re-encoded, {1} unreadable ones replaced by a neutral gray","py.oar2glb.textures_0_sculpt_maps_laissees_intactes":"[textures] {0} sculpt maps left untouched","py.oar2glb.textures_0_textures_a_reencoder_sur":"[textures] {0} textures to re-encode on {1} cores ({2:.0f} s)","py.oar2glb.textures_ecriture_de_0":"[textures] writing {0}...","py.oar2glb.textures_lecture_de_0":"[textures] reading {0}...","py.oar2glb.translation_bind_shape_0":" ; bind_shape translation {0}","py.oar2glb.type_llsd_inconnu_0_r":"unknown LLSD type {0!r}","py.oar2glb.unknown":"unknown","py.oar2glb.unreadable":"unreadable","py.oar2glb.uuid_du_mesh":"mesh UUID","py.oar2glb.uuid_du_prim":"prim UUID","py.oar2glb.var_region_0_objet_s_replace":"[var-region] {0} object(s) moved back to their real position, {1} recognized, {2} not recognized","py.presence.0_1_20_jusqu_au_2":"  {0}. {1:<20} until {2:<17} {3}","py.presence.0_1_2_autres_appareils_du":" · {0}://{1}:{2} (other devices on the network)","py.presence.0_ejecte":"{0} ejected","py.presence.0_id_1_cle_2_ip":"{0} [id {1}, key {2}, ip {3}]","py.presence.adresses_ip_dans_le_journal_masquees":"IP addresses in the log: masked (default), in clear, or absent","py.presence.aucun_bannissement":"(no ban)","py.presence.ban_ip":"banned (IP)","py.presence.banned":"banned","py.presence.banned_line":"{0} banned ({1})","py.presence.bannissement_de_0_leve":"ban on {0} lifted","py.presence.certificat_tls_wss":"TLS certificate (wss://)","py.presence.chat":"chat","py.presence.cle_0_ip_1":"key {0} ip {1}","py.presence.cle_privee_tls":"TLS private key","py.presence.commande_inconnue_0_tape_aide":"unknown command: {0} (type \"aide\")","py.presence.commandes_tape_les_ici_puis_entree":"commands (type them here, then Enter):\n  liste                           connected visitors (no., name, role, room, duration, IP)\n  ejecter <no.|name> [reason]       disconnects the visitor (they can come back)\n  bannir <no.|name> [minutes] [reason]   ejects and bans their key and IP (IPv6: its /64 prefix; default 60 min; 0 = permanent)\n  bans                            current bans\n  debannir <ban no.>           lifts a ban\n  rooms                           known rooms: connected, visits, key (exact case)\n  visits-key <room> [off]         visit log key of a room (new key, or off to remove it; alone: list)\n  creators                        creators (--creators file re-read): prefix, state, open rooms, walkers, origins\n  oublier <name>                  releases a reserved name (its owner loses it; the first to ask for it gets it)\n  pseudos [filtre]                lists the reserved names (owner's #XXXX code, last seen, expiry)\n  version                         version number and revision of this file\n  aide                            this message\n  (a name containing spaces: use the no. from \"liste\")","py.presence.comportement_inapproprie":"inappropriate behavior","py.presence.connexions_simultanees_par_adresse_ip":"simultaneous connections per IP address (IPv6: per /64 prefix)","py.presence.debut":"start","py.presence.deconnexion":"disconnection","py.presence.definitif":"permanent","py.presence.delai_mini_entre_deux_messages_d":"minimum delay between two messages from a visitor (s)","py.presence.derniers_messages_rejoues_aux_nouveaux_arriv":"last messages replayed to newcomers (default 200; 0 = none); older ones are requested in batches of 50 (history message)","py.presence.derriere_un_reverse_proxy_en_tete":"behind a reverse proxy: header carrying the visitor's real IP (e.g. X-Forwarded-For, CF-Connecting-IP); enable only if the server is reachable only through that proxy","py.presence.duree_0_min_1_02d_s":"duration {0} min {1:02d} s","py.presence.ejecte_par_l_hote":"ejected by the host","py.presence.erreur_de_commande_0":"[command error] {0}","py.presence.ev.ban":"ban","py.presence.ev.connect":"connection","py.presence.ev.end":"end","py.presence.ev.kick":"kick","py.presence.ev.name":"name","py.presence.ev.refuse":"refusal","py.presence.ev.empty":"empty","py.presence.ev.http":"http request","py.presence.empty":"connection opened then closed without a request ({0} since the last line for this address; browser preconnection, port test or robot: harmless)","py.presence.http":"GET {1}, host {2}, agent {3}: not a WebSocket opening ({4}) ({0} since the last line for this address; a browser opening the server address, a robot or a test: harmless)","py.presence.ev.raw":"unreadable request","py.presence.raw":"{1}, start '{2}' ({0} since the last line for this address; a robot probing the port: harmless)","py.presence.rawkind.misc":"not an HTTP request","py.presence.rawkind.rdp":"probe of Windows Remote Desktop (RDP)","py.presence.rawkind.tls":"encrypted (https) connection on a port without encryption","py.presence.ev.walk":"walk","py.presence.fichier_de_bannissements_illisible_0_ignore":"[!] ban file unreadable ({0}): ignored","py.presence.fichier_de_journal_tourne_chaque_nuit":"log file (rotated every night); relative path = script folder","py.presence.fichier_des_bannissements_chemin_relatif_dos":"ban file; relative path = script folder","py.presence.help.host":"listening address (0.0.0.0 = all interfaces; 127.0.0.1 = this machine only)","py.presence.help.maxtotal":"simultaneous connections in total, all rooms together","py.presence.help.port":"port the visitors connect to","py.presence.history_days":"days of messages read back and kept in --history-file at startup (default 30; 0 = keep everything)","py.presence.history_file":"chat history file (one JSON line per message: time, name, text, room; never the IP address): read back at startup to keep the history across restarts; off by default. These are personal data","py.presence.history_loaded":"history: {0} message(s) read back, {1} ignored or too old ({2})","py.presence.history_write_error":"history: cannot write ({0})","py.presence.jours_de_journal_conserves":"days of log kept","py.presence.leve":"lifted","py.presence.limite_de_connexions_par_ip":"connection limit per IP","py.presence.list_line":"  #{0:<4} {1:<26} {2:<10} room={3:<16} {4} min {5:02d} s   ip {6}","py.presence.log_line":"{0:<11} | room={1} | {2}","py.presence.longueur_max_d_un_message_de":"maximum length of a chat message","py.presence.messages_max_par_fenetre_de_10":"maximum messages per 10 s window and per visitor","py.presence.moderation_tape_aide_pour_la_liste":"moderation: type \"aide\" for the list of commands (liste, ejecter, bannir, bans, debannir, oublier, pseudos, rooms, visits-key, creators, version)","py.presence.nobody":"(nobody)","py.presence.noms_interdits_a_la_reservation_separes":"names forbidden for reservation, comma-separated (e.g. admin,moderator)","py.presence.old_name":"previous: {0}","py.presence.origines_autorisees_separees_par_des_virgule":"allowed origins, comma-separated (default: all)","py.presence.personne_ne_correspond_a_0_tape":"nobody matches \"{0}\" (type \"liste\")","py.presence.plusieurs_visiteurs_correspondent_utilise_le":"several visitors match, use the number:","py.presence.promeneur_0_dans_le_salon":"walker ({0} in the room)","py.presence.promeneurs_max_par_salon":"maximum walkers per room","py.presence.registre_des_noms_reserves_vide_en":"registry of reserved names (empty = in memory only); relative path = script folder","py.presence.registre_illisible_0_demarrage_a_vide":"[!] registry unreadable ({0}): starting empty","py.presence.role.spectator":"spectator","py.presence.role.walker":"walker","py.presence.salon_plein":"room full","py.presence.serveur_adresse_a_donner_a_presence":"server | address to give to --presence-url: {0}://{1}:{2}","py.presence.serveur_adresses_a_donner_a_presence":"server | addresses to give to --presence-url: {0}://127.0.0.1:{1} (this machine)","py.presence.serveur_de_presence_glb2html_websocket":"presence_server.py {0}: glb2html presence server (WebSocket): visitors, chat, moderation.","py.presence.serveur_journal_0_registre_des_noms":"server | log: {0} | name registry: {1}","py.presence.serveur_n_utilise_jamais_0_0":"server | never use 0.0.0.0 in --presence-url: it is a listening address, not a destination","py.presence.star_hint":"server | or {0}://*:{1}: the same name as the page that connects (advised if your pages are opened through several addresses: localhost, network, public name)","py.presence.serveur_presence_server_0_ecoute_sur":"server | presence_server {0} | listening on {1}:{2}  (Ctrl+C to stop)","py.presence.spectateurs_vue_globale_max_tous_salons":"maximum spectators (global view), all rooms","py.presence.spectator_paren":"(spectator)","py.presence.trop_de_messages_patiente_quelques_secondes":"Too many messages, please wait a few seconds.","py.presence.trop_de_spectateurs":"too many spectators","py.presence.un_nom_non_utilise_depuis_ce":"a name unused for this many days is released","py.presence.until_date":"until {0}","py.presence.usage_ban":"usage: ban <#|name> [minutes] [reason]","py.presence.usage_kick":"usage: kick <#|name> [reason]","py.presence.usage_unban":"usage: unban <number from “bans”>","py.presence.ev.forget":"name released","py.presence.forget_done":"name “{0}” released: the first browser to ask for it will get it","py.presence.forget_logged":"former owner #{0}","py.presence.forget_none":"no reserved name matches “{0}”","py.presence.forget_online":"(its former owner is connected: the displayed name does not change before their next connection)","py.presence.usage_forget":"usage: oublier <name>   (the name as you like: case, accents and spaces do not matter)","py.presence.names_head":"reserved names ({0}):","py.presence.names_line":"  {0} #{1}  last seen {2}, released on {3} if unused{4}","py.presence.names_none":"(no reserved name)","py.presence.names_online":"(connected)","py.presence.zone":"zone","py.stats.0_16_mediane_1_1f_90":"{0:>16}: median {1:,.1f} | 90 % of blocks under {2:,.1f} | maximum {3:,.1f}","py.stats.attention_geometrie_compressee_0_les_mo":"Warning: compressed geometry ({0}): the MB of geometry above are the decoded size, not the file's.","py.stats.aucun_mesh_positionnable_accessors_sans_min":"No placeable mesh (accessors without min/max?).","py.stats.bloc_0_1_2_1f_mo":"  block {0},{1}: {2:.1f} MB of geometry, {3} triangles, {4} instances, {5:.1f} MB of textures","py.stats.blocs_de_0_0f_m_1":"== Blocks of {0:.0f} m: {1} non-empty (instance center; geometry and textures without duplicates within the block) ==","py.stats.ce_fichier_n_est_pas_un":"This file is not a GLB.","py.stats.cote_des_blocs_en_metres_defaut":"block side in meters (default 256)","py.stats.cout_de_la_reutilisation_entre_blocs":"== Cost of reuse between blocks ==","py.stats.desc":"glb-stats.py: quick analysis of a GLB, whatever its size. Reads only the JSON header (never the binary data or the textures): a few seconds and very little memory.","py.stats.ecrit_aussi_le_rapport_dans_ce":"also writes the report to this file (UTF-8)","py.stats.etendue":"== Extent ==","py.stats.fichier_0_1_1f_mo_en":"File: {0} ({1:,.1f} MB; JSON header read: {2:,.1f} MB)","py.stats.geometrie_accessors_uniques_0_1f_mo":"Geometry (unique accessors): {0:,.1f} MB | Embedded textures: {1:,.1f} MB | Rest: {2:,.1f} MB","py.stats.geometrie_mo":"geometry (MB)","py.stats.geometrie_utilisee_par_plusieurs_blocs_0":"Geometry used by several blocks: {0:,.1f} MB ({1:.0f} % of the total) | textures used by several blocks: {2:,.1f} MB ({3:.0f} % of the total): size of a shared library loaded once.","py.stats.help.glb":"the .glb file to analyze","py.stats.le_premier_bloc_du_glb_n":"The first GLB chunk is not JSON.","py.stats.les_5_blocs_les_plus_lourds":"The 5 blocks heaviest in geometry:","py.stats.meshes_reutilises_plusieurs_fois_0_materiaux":"Meshes reused several times: {0} | materials: {1} | textures (images): {2} (used: {3})","py.stats.nud_0_1_2_0f_m":"  - node {0} \"{1}\": {2:.0f} m, {3} mesh(es)","py.stats.nuds_parcourus_0_meshes_1_utilises":"Nodes visited: {0} | meshes: {1} (used: {2}) | mesh instances: {3}","py.stats.objets_racine_0_plus_grands_qu":"Root objects: {0} | larger than a {1:.0f} m block: {2}","py.stats.poids_estime_octets_lus_dans_l":"== Estimated weight (bytes read from the header, without decoding) ==","py.stats.somme_des_blocs_geometrie_0_1f":"Sum of blocks: geometry {0:,.1f} MB (against {1:,.1f} MB without duplicates across the whole file): difference = extra cost if shared meshes are duplicated in each block.","py.stats.sommets_uniques_0_sommets_rendus_instances":"Unique vertices: {0:,} | rendered vertices (instances included): {1:,} | rendered triangles: {2:,}","py.stats.taux_de_reutilisation_sommets_rendus_uniques":"Reuse ratio (rendered / unique vertices): {0:.1f}","py.stats.x_0_1f_a_1_1f":"X: {0:.1f} to {1:.1f} ({2:.0f} m) | Z: {3:.1f} to {4:.1f} ({5:.0f} m) | height Y: {6:.1f} to {7:.1f}","py.presence.help.visits":"visit log file (one JSON line per visit, no IP; empty = no log; path relative to the script's folder)","py.presence.help.visits_days":"days of visits kept in this log (0 = all)","py.presence.help.visits_names":"also record walkers' nicknames in the visit log","py.presence.help.visits_keys":"file of the visit log access keys (fingerprints only, path relative to the script's folder)","py.presence.ev.visits":"visits","py.presence.visits.rate":"too many key attempts","py.presence.visits.badkey":"key refused","py.presence.visits.granted":"summary sent","py.presence.visits.yes":"yes","py.presence.visits.no":"no","py.presence.visits_on":"server: visit log {0} (kept {1} days, 0 = all; nicknames: {2})","py.presence.map_names_on":"server: nicknames are given to maps that present the --map-names-key key (5 refused keys per minute and per address at most)","py.presence.help.map_names_key":"gives the nicknames of walkers and of visitors in the global view to maps opened with this key (carte.html#pseudos=KEY; at least 8 characters)","py.presence.map_key_short":"--map-names-key: the key must be at least {0} characters long","py.presence.map_names_old":"--map-names no longer exists: the map's nicknames are protected by a key (--map-names-key SECRET); no nickname is given","py.presence.ev.mapnames":"map nicknames","py.presence.visits_write_err":"visit log {0}: cannot write ({1})","py.presence.vkey.unreadable":"unreadable visit keys file: {0} (starting without keys)","py.presence.help.creators":"file of allowed creators (origins of their pages, room prefix, limits; re-read on change, path relative to the script's folder); absent: everyone is accepted","py.presence.cr.bad":"creators: entry {0} ignored (missing or invalid id: letters, digits, - and _, 32 at most)","py.presence.cr.badprefix":"creators: entry {0} ignored (invalid prefix {1}: letters, digits, space, - and _, no dot)","py.presence.cr.dup":"creators: entry {0} ignored ({1} already used by a previous entry)","py.presence.cr.nulljson":"creators: {0}: origin null written without quotes, ignored (write \"null\" in quotes for a page opened from the disk)","py.presence.cr.origindup":"creators: origin {0} already belongs to {1}, ignored for {2}","py.presence.cr.missing":"creators file missing: {0}; every connection is refused until it exists","py.presence.cr.unreadable":"unreadable creators file: {0} ({1}); previous list kept","py.presence.cr.loaded":"creators: {0} read from {1}","py.presence.cr.on":"server: creators {0} ({1}); a page from another origin is refused","py.presence.cr.off":"no creators file (start the server with --creators FILE): every page is accepted","py.presence.cr.none":"no valid creator in {0}: every connection is refused","py.presence.cr.line":"  {0:<16} prefix: {1}   {2}   open rooms: {3}{4}   walkers: {5}{6}","py.presence.cr.noprefix":"(none: all other rooms)","py.presence.cr.active":"active","py.presence.cr.suspended":"suspended","py.presence.cr.max":" / {0} at most","py.presence.cr.origins":"      origins: {0}","py.presence.cr.noorigin":"(none)","py.presence.cr.refuse.origin":"undeclared origin: {0}","py.presence.cr.refuse.off":"creator {0} suspended","py.presence.cr.refuse.room":"room {0} outside the rooms of {1}","py.presence.cr.refuse.rooms":"{0}: already {1} open rooms","py.presence.vkey.none":"no visit log key","py.presence.vkey.line":"  room \"{0}\": key created on {1}","py.presence.vkey.unknown":"no key for room \"{0}\"","py.presence.vkey.off":"key of room \"{0}\" removed","py.presence.vkey.new":"visit log key of room \"{0}\": {1}\n  (shown only once; give it to the creator with their page address followed by #visits; the old key no longer works)","py.presence.vkey.inactive":"warning: the visit log is off (start the server with --visits FILE)","py.presence.vkey.case":"warning: no visit and no visitor for room \"{0}\"; room known with a different case: {1}. Case matters: run visits-key again with the exact name (this key stays valid for \"{0}\").","py.presence.rooms.none":"no known room (no connected visitor, no recorded visit, no key)","py.presence.rooms.line":"  {0:<24} connected: {1} ({2} walking)   visits: {3}{4}   key: {5}","py.presence.rooms.last":", last on {0}","py.presence.rooms.novisits":"  (visit log off: start the server with --visits FILE to count visits)","py.presence.rooms.note":"  (exact case; a room never visited and without a key is not shown: its name is the room value of NAME.config.json, the page name by default)"},"fr":{"_name":"Français","py.common.help":"afficher ce message d'aide et quitter","py.common.lang_help":"langue des messages et de l'aide : fr, en ou auto (défaut : langue du système ; variable d'environnement WEB3D_LANG équivalente). Disponibles : {0}","py.common.optionals":"options","py.common.positionals":"arguments","py.common.version_mark":"{0}, empreinte {1}","py.common.version":"afficher la version et quitter","py.glb2html.0_1_fichiers_generes":"{0}/{1} fichiers générés","py.glb2html.0_cle_s_changee_s":"{0} clé(s) changée(s)","py.glb2html.0_gardee_s_telle_s_quelle":", {0} gardée(s) telle(s) quelle(s)","py.glb2html.0_gltf_version_1_non_supportee":"{0} : glTF version {1} non supportée","py.glb2html.0_introuvable":"{0} introuvable","py.glb2html.0_pas_un_glb_magic_absent":"{0} : pas un GLB (magic absent)","py.glb2html.0_premier_chunk_non_json":"{0} : premier chunk non JSON","py.glb2html.0_reference_des_fichiers_externes_1":"{0} : référence des fichiers externes {1} -> repacker en GLB autonome (npx @gltf-transform/cli copy in.gltf out.glb)","py.glb2html.0_taille_annoncee_1_taille_fichier":"{0} : taille annoncée {1} != taille fichier {2} (tronqué ?)","py.glb2html.0_textures_ktx2_basis_non_gerees":"{0} : textures KTX2/Basis non gérées hors ligne -> npx @gltf-transform/cli png in.glb out.glb","py.glb2html.absent_paren":" (absent)","py.glb2html.adresse_de_la_page_de_cette":"adresse de la page de cette région (défaut : le nom du fichier .html, relatif)","py.glb2html.adresse_s_de_regions_json_partage":"adresse(s) de regions.json partagé(s), séparées par des virgules : la page les relit à chaque ouverture (http/https), les fusionne et complète avec la carte intégrée. Un autre site doit autoriser l'accès (CORS)","py.glb2html.afficher_le_nom_de_l_element":"afficher le nom de l'élément cliqué","py.glb2html.amplitude_vagues_0_10":"amplitude vagues 0..10","py.glb2html.aucun_glb_dans_0":"Aucun .glb dans {0}","py.glb2html.aucune_cle_changee":"aucune clé changée","py.glb2html.avertissement_0_0_0_0_est":"[AVERTISSEMENT] 0.0.0.0 est une adresse d'écoute du serveur, pas une destination : remplacée par 127.0.0.1 -> {0}","py.glb2html.avertissement_0_existe_et_differe_de":"[AVERTISSEMENT] {0} existe et diffère de la coquille de cette version : conservée (les autres régions la partagent). Supprime-la pour la renouveler","py.glb2html.avertissement_0_introuvable_a_cote_de":"[AVERTISSEMENT] {0} introuvable à côté de la page (la région n'a ni .glb ni tuiles ici)","py.glb2html.avertissement_0_tuile_s_listee_s":"[AVERTISSEMENT] {0} tuile(s) listée(s) dans {1} introuvable(s) à côté de lui (première : {2}) ; la page les signalera et réessaiera","py.glb2html.avertissement_default_ignore_sans_shared_shell":"Avertissement : --default est ignoré sans --shared-shell.","py.glb2html.avertissement_des_zones_sont_liees_a":"[AVERTISSEMENT] des zones sont liées à un élément du modèle (champ mesh), mais {0} a été écrit sans références d'objets (glb2tiles avant la v32) : ces zones seront ignorées par la page (avertissement en console). Refaire le découpage avec glb2tiles v32 pour en profiter.","py.glb2html.avertissement_map_page_ignore_aucune_region":"[AVERTISSEMENT] --map-page ignoré : aucune région à afficher (donne --register pour enregistrer cette région, ou --map)","py.glb2html.avertissement_map_page_ignore_aucune_region_2":"[AVERTISSEMENT] --map-page ignoré : aucune région à afficher (donne --register ou --map)","py.glb2html.avertissement_presence_url_doit_commencer_pa":"[AVERTISSEMENT] --presence-url doit commencer par ws:// ou wss:// (reçu : {0})","py.glb2html.avertissement_region_name_region_url_region":"[AVERTISSEMENT] --region-name, --region-url, --region-xy, --region-spawn et --thumb ne servent qu'avec --register : ignorés","py.glb2html.avertissement_register_et_map_page_ne":"[AVERTISSEMENT] --register et --map-page ne s'appliquent qu'à un fichier .glb, pas à un dossier","py.glb2html.avertissement_title_est_ignore_en_mode":"[AVERTISSEMENT] --title est ignoré en mode modulaire : le titre de la page est le salon (--room) de la config","py.glb2html.avertissement_vignette_ignoree_jpg_png_webp":"[AVERTISSEMENT] vignette ignorée (jpg/png/webp de 140 Ko maximum attendus) : {0}","py.glb2html.avertissement_vignette_introuvable_0":"[AVERTISSEMENT] vignette introuvable : {0}","py.glb2html.avertissement_vue_d_ensemble_0_introuvable":"[AVERTISSEMENT] vue d'ensemble {0} introuvable à côté de {1} ; la page fonctionnera sans elle","py.glb2html.avertissement_zones_live_est_ignore_en":"[AVERTISSEMENT] --zones-live est ignoré en mode modulaire : les zones sont toujours relues dans <page>.zones.json","py.glb2html.cache_telechargement_0":"[cache] téléchargement {0}","py.glb2html.image_nombre":"[image] « {0} » : {1} existe, le nom reste « {0} » (la page cherche le fichier toute seule)","py.glb2html.image_completee":"[image] « {0} » → {1}","py.glb2html.image_plusieurs":"[image] « {0} » → {1} ({2} fichiers correspondent : le premier par ordre alphabétique est pris)","py.glb2html.image_sans_fichier":"[image] « {0} » : aucun fichier « {0}.jpg », « {0}-… » dans {1} (nom laissé tel quel)","py.glb2html.carte_0_ajoutee_ou_mise_a":"[carte] « {0} » ajoutée ou mise à jour dans {1} ({2} région(s))","py.glb2html.carte_0_n_est_pas_a":"[carte] {0} n'est pas à côté de la page {1} (un chemin relatif de --register est cherché dans le dossier de lancement, sinon dans celui des outils). Pour l'écrire à côté de la page : donne un chemin complet, ou mets la région à jour avec --update (chemins relatifs à la page)","py.glb2html.carte_0_region_s_lue_s":"[carte] {0} région(s) lue(s) dans {1}","py.glb2html.carte_avec_maj_les_chemins_relatifs":"[carte] avec --update, les chemins relatifs de --register, --map, --map-page et --thumb sont relatifs au dossier de la page : {0}","py.glb2html.carte_des_mondes":"Carte des mondes","py.glb2html.carte_page_carte_0_region_s":"[carte] page carte ({0} région(s)) -> {1}","py.glb2html.ce_n_est_pas_un_fichier":"ce n'est pas un fichier de réglages du viewer","py.glb2html.ce_n_est_pas_un_objet":"ce n'est pas un objet JSON","py.glb2html.chat_entre_visiteurs_necessite_presence_url":"chat entre visiteurs (nécessite --presence-url ; touche Entrée en promenade)","py.glb2html.cible_camera_x_y_z":"cible caméra x,y,z","py.glb2html.compass":"boussole en haut de la page : cap de l'avatar (de la caméra en vue globale) avec le point cardinal et les degrés (défaut : activée)","py.glb2html.coquille_0_absente_ecrite":"coquille {0} absente : écrite","py.glb2html.coquille_0_deja_a_jour_identique":"coquille {0} déjà à jour (identique à celle de {1})","py.glb2html.coquille_0_deja_presente_et_identique":"[coquille] {0} déjà présente et identique","py.glb2html.coquille_0_ecrite":"[coquille] {0} écrite","py.glb2html.coquille_0_plus_ancienne_que_1":"coquille {0} plus ancienne que {1} : renouvelée, ancienne copie gardée sous {2}. Cette coquille est partagée par les autres régions du dossier : elles gardent leur comportement (les anciennes configurations restent comprises)","py.glb2html.coquille_commune_0_adresse_1":"coquille commune {0} ; adresse : {1}","py.glb2html.coquille_modulaire_marqueur_s_non_remplace":"coquille modulaire : marqueur(s) non remplacé(s) {0}","py.glb2html.couleur_ciel_ex_87ceeb":"couleur ciel, ex 87ceeb","py.glb2html.couleur_mer_ex_3a9ad9":"couleur mer, ex 3a9ad9","py.glb2html.default_json_ecrit":"default.json écrit : {0} (région par défaut : {1})","py.glb2html.default_region":"avec --shared-shell : cette région devient la région par défaut (default.json), ouverte quand l'adresse n'a pas de ?region= ; sans cette option default.json n'est écrit que s'il n'existe pas encore","py.glb2html.demi_largeur_du_fondu_du_trou":"demi-largeur du fondu du trou","py.glb2html.desc":"glb2html.py {0} : fabrique la page web d'une région à partir d'un .glb (ou de tuiles), met une région à jour, l'enregistre dans la carte des mondes.","py.glb2html.dessine_aussi_les_arrivees_dans_la":"dessine aussi les arrivées dans la page (petit marqueur discret au sol ; défaut : jamais)","py.glb2html.direction_camera_x_y_z":"direction caméra x,y,z","py.glb2html.distance_5_a_200_m_defaut":"distance (5 à 500 m, défaut 150) jusqu'à laquelle l'infobulle, le clic, le repère de portail (cône) et le nom affiché (showName) des zones marchent en promenade","py.glb2html.entree_gltf_repacker_d_abord_en":"Entrée .gltf : repacker d'abord en .glb (npx @gltf-transform/cli copy in.gltf out.glb)","py.glb2html.epilog":"Exemples :\n  python glb2html.py ile.glb\n  python glb2html.py ile.glb -o ile.html --hole 90 --wave 1.2 --sea-y -30 --zoom 1.3\n  python glb2html.py ile.glb --shared-shell -o Ile.html --presence-url ws://ADRESSE:8765\n  python glb2html.py -o Ile.html --shared-shell --update --zone-info-dist 60\n  python glb2html.py dossier_glb/ --no-sea\nAu premier lancement, three.js est téléchargé une fois dans ~/.cache/glb2html (ou --vendor FOLDER : aucun téléchargement).","py.glb2html.erreur_0":"[ERREUR] {0}","py.glb2html.erreur_0_entree_de_tuile_invalide":"[ERREUR] {0} : entrée de tuile invalide ({1}) : « file » doit être un chemin relatif .glb (sans .. ni :), « min » et « max » trois nombres","py.glb2html.erreur_0_illisible_1":"[ERREUR] {0} illisible ({1})","py.glb2html.erreur_0_introuvable":"[ERREUR] {0} introuvable","py.glb2html.erreur_0_introuvable_cherche_dans_1":"[ERREUR] {0} introuvable (cherché dans {1} puis dans {2})","py.glb2html.erreur_0_introuvable_vendor_doit_pointer":"[ERREUR] {0} introuvable (--vendor doit pointer sur la racine du paquet npm three)","py.glb2html.erreur_0_liste_tiles_absente_ou":"[ERREUR] {0} : liste « tiles » absente ou vide (fichier écrit par glb2tiles.py attendu)","py.glb2html.erreur_0_ou_1_introuvable_genere":"[ERREUR] {0} ou {1} introuvable : génère d'abord la région avec --shared-shell","py.glb2html.erreur_0_ou_1_introuvable_genere_2":"[ERREUR] {0} ou {1} introuvable : génère d'abord la page avec --modular","py.glb2html.erreur_0_overview_invalide_1_file":"[ERREUR] {0} : « overview » invalide ({1}) : « file » doit être un chemin relatif .glb (sans .. ni :)","py.glb2html.erreur_aucune_region_a_afficher_donne":"[ERREUR] aucune région à afficher : donne --map regions.json","py.glb2html.erreur_avec_maj_o_designe_la":"[ERREUR] avec --update, -o désigne la région (ex. -o Region.html), pas un dossier","py.glb2html.erreur_avec_tiles_o_designe_la":"[ERREUR] avec --tiles, -o désigne la région (ex. -o Region.html), pas un dossier","py.glb2html.erreur_config_only_demande_o_page":"[ERREUR] --config-only demande -o <page.html> (la page modulaire déjà générée)","py.glb2html.erreur_enregistrer_une_region_sans_glb":"[ERREUR] enregistrer une région sans .glb demande --region-name, --region-url et --room","py.glb2html.erreur_fichier_de_reglages_0_introuvable":"[ERREUR] fichier de réglages {0} introuvable (cherché dans {1} puis dans {2})","py.glb2html.erreur_lib_url_refuse":"Erreur : --lib-url « {0} » refusé (attendu : chemin relatif comme ../lib, ou adresse http(s) complète, sans ? # \\ ni guillemet).","py.glb2html.erreur_maj_0_introuvable_la_region":"[ERREUR] --update : {0} introuvable, la région n'a pas encore été générée. Génère-la d'abord, sans --update : {1}","py.glb2html.erreur_maj_0_introuvable_si_la":"[ERREUR] --update : {0} introuvable. Si la région utilise une coquille commune, donne --shared-shell NAME.html (par défaut {1})","py.glb2html.erreur_maj_demande_o_region_html":"[ERREUR] --update demande -o <Region.html> (la région déjà générée)","py.glb2html.erreur_maj_et_settings_s_excluent":"[ERREUR] --update et --settings s'excluent : --update ne reprend que les options données et la config existante","py.glb2html.erreur_nom_de_region_0_refuse":"[ERREUR] nom de région « {0} » refusé par la coquille commune (un seul nom de fichier, sans / \\ : ? # ni .., sans point au début)","py.glb2html.erreur_nom_de_region_0_refuse_2":"[ERREUR] nom de région « {0} » refusé par la coquille commune","py.glb2html.erreur_nom_de_region_0_refuse_3":"[ERREUR] nom de région « {0} » refusé par la coquille commune (un seul nom de fichier, sans / \\ : ? # ni .., sans point au début) : choisis un autre -o","py.glb2html.erreur_region_xy_attend_deux_nombres":"[ERREUR] --region-xy attend deux nombres : X,Y","py.glb2html.erreur_settings_sans_nom_demande_le":"[ERREUR] --settings sans nom demande le .glb (le fichier cherché est <nom du .glb>.reglages.json)","py.glb2html.erreur_shared_shell_attend_un_nom":"[ERREUR] --shared-shell attend un fichier .html (nom, ou chemin FOLDER/index.html pour des régions en sous-dossiers) (reçu « {0} »)","py.glb2html.erreur_telechargement_impossible_0_utilise_v":"[ERREUR] téléchargement impossible ({0}). Utilise --vendor <dossier three>.","py.glb2html.erreur_tiles_demande_o_region_html":"[ERREUR] --tiles demande -o <Region.html> (son nom sans extension est celui de la région)","py.glb2html.erreur_tiles_remplace_le_glb_ne":"[ERREUR] --tiles remplace le .glb : ne donne pas de fichier .glb avec --tiles","py.glb2html.erreur_zones_only_demande_o_page":"[ERREUR] --zones-only demande -o <page.html>","py.glb2html.erreur_zones_only_demande_zones_fichier":"[ERREUR] --zones-only demande --zones FILE (ou --settings) : aucune zone à écrire","py.glb2html.erreur_zones_only_demande_zones_live":"[ERREUR] --zones-only demande --zones-live (page autonome) ou une page modulaire déjà générée ({0} introuvable à côté de la page)","py.glb2html.fichier_glb_ou_dossier_de_glb":"fichier .glb ou dossier de .glb","py.glb2html.fichier_json_de_zones_exporte_par":"fichier .json de zones exporté par le viewer ; chemin relatif : cherché dans le dossier de lancement, puis dans le dossier du script. Une zone peut porter un champ mesh (nom exact d'un élément du modèle) : l'élément devient cliquable","py.glb2html.scan.help":"dossier des sites (coquille commune à la racine) : met à jour son regions.json avec les régions trouvées (NOM.config.json) et leurs vignettes (NOM.jpg, .png ou .webp à côté) ; garde les noms, places, arrivées, l'en-tête et les fiches externes ; ne supprime rien","py.glb2html.scan.dryhelp":"avec --scan-sites : affiche les changements sans rien écrire","py.glb2html.scan.nofolder":"[ERREUR] dossier introuvable : {0}","py.glb2html.scan.noshell":"[AVERTISSEMENT] pas de index.html dans {0} : les adresses index.html?region=… des fiches demandent la coquille à la racine","py.glb2html.scan.badcfg":"[AVERTISSEMENT] {0} illisible, ignoré : {1}","py.glb2html.scan.add":"  + {0} ({1}), place {2},{3}","py.glb2html.scan.upd":"  ~ {0} : {1}","py.glb2html.scan.orphan":"  ? {0} : {1} introuvable dans le dossier, fiche gardée","py.glb2html.scan.summary":"regions.json : {0} ajoutée(s), {1} mise(s) à jour, {2} inchangée(s), {3} externe(s) gardée(s), {4} orpheline(s) -> {5}","py.glb2html.scan.dry":"--dry-run : rien n'a été écrit","py.glb2html.fichier_regions_json_a_mettre_a":"fichier regions.json à mettre à jour avec CETTE région (ajoutée ou mise à jour par salon) ; relatif : dossier de lancement s'il y existe, sinon dossier du script. La page générée embarque la carte à jour","py.glb2html.fichier_regions_json_carte_des_mondes":"fichier regions.json (carte des mondes : nom, adresse, position, vignette) exporté par le viewer ; chemin relatif : dossier de lancement, puis dossier du script","py.glb2html.finesse_du_maillage_de_la_mer":"finesse du maillage de la mer 8..1000 (maille = 4000/segments ; seulement avec --anim)","py.glb2html.format_attendu_x_y_z":"format attendu : x,y,z","py.glb2html.gabarit_modulaire_cible_introuvable_ou_multi":"gabarit modulaire : cible introuvable ou multiple ({0}…)","py.glb2html.genere_aussi_une_page_web_carte":"génère aussi une page web « carte des mondes » (liens cliquables vers chaque région) ; sans .glb : génère seulement cette page depuis --map. Relatif : à côté de la page de la région","py.glb2html.haute_resolution_rendu_x2_minimum_supersampl":"haute résolution : rendu x2 minimum (supersampling, plus net mais ~4x plus lourd)","py.glb2html.hauteur_des_yeux_en_m_promenade":"hauteur des yeux en m (promenade)","py.glb2html.hauteur_mer_150_60":"hauteur mer -150..60","py.glb2html.help.anim":"animer la mer (vagues) ; --no-anim : mer fixe","py.glb2html.help.light":"la page s'ouvre en rendu léger (résolution divisée par deux, 15 images/s au plus, vue d'ensemble seule en vue globale, sans anticrénelage) tant que le visiteur n'a rien choisi dans Réglages ; --no-light : rendu normal","py.glb2html.help.sea":"afficher la mer (--no-sea : sans mer)","py.glb2html.identifiant_du_point_d_arrivee_des":"identifiant du point d'arrivée des visiteurs dans cette région (défaut : default)","py.glb2html.inclure_le_mode_promenade_touche_f":"inclure le mode promenade (touche F) dans la page","py.glb2html.la_page_recharge_ses_zones_a":"la page recharge ses zones à chaque ouverture depuis un fichier .zones.json placé à côté d'elle (servie en http/https ; sinon les zones intégrées servent). Sans NAME : <page>.zones.json. Le fichier est écrit par le script, filtré selon --profile","py.glb2html.le_fichier_glb_ou_le_dossier":"le fichier .glb (ou le dossier) est obligatoire","py.glb2html.lib_url":"chemin relatif (../lib) ou adresse http(s) complète où trouver three.js et ses modules ; écrit dans la ligne « const LIB » de la coquille (modifiable à la main ; --update la garde) quand elle est écrite et retenu dans la config pour --update. Chemin relatif : lib/ y est créé s'il manque ; adresse complète : rien n'est copié","py.glb2html.m_charger_les_tuiles_dont_la":"m : charger les tuiles dont la boîte est à moins de ce rayon de l'avatar, en plan X,Z (défaut %(default)g ; ?radius=NNN dans l'adresse pour essayer)","py.glb2html.m_decharger_les_tuiles_au_dela":"m : décharger les tuiles au-delà de rayon + marge (défaut %(default)g)","py.glb2html.maj_0_absent_ou_incomplet_ecrit":"[update] {0}/ absent ou incomplet : écrit","py.glb2html.maj_0_conserve_tel_quel":"[update] {0} conservé tel quel","py.glb2html.maj_0_mis_a_jour_glb2html":"[update] {0} mis à jour (glb2html {1}) : ","py.glb2html.maj_0_present_conserve":"[update] {0}/ présent : conservé","py.glb2html.maj_0_remplace_par_1":"[update] {0} remplacé par {1}","py.glb2html.maj_le_profil_ne_filtre_les":"[update] le profil ne filtre les zones qu'à l'écriture de la liste de zones : ajoute --zones FILE pour la réécrire","py.glb2html.maj_lib_repris":"[update] dossier lib repris de la ligne « const LIB » de la coquille : {0}","py.glb2html.marqueur_des_portails_et_zones_libres":"marqueur des portails et zones libres dans la page : dot (défaut : disque de 0,4 m et anneau fin), range (anneau fin et net au rayon réel de la zone, visible de loin) ou none ; les anciennes valeurs discret, portee et aucun restent acceptées. Les arrivées ne sont jamais dessinées (voir --show-spawns)","py.glb2html.met_a_jour_une_region_deja":"met à jour une région déjà générée (-o REGION.html [--shared-shell [SHELL.html]] [--tiles X.tiles.json | X.glb]) : lit X.config.json, n'applique QUE les options données sur la ligne, garde tout le reste et X.zones.json (réécrit seulement avec --zones), écrit la version courante et renouvelle la coquille si elle est plus ancienne (ancienne copie gardée sous un nom daté). Échoue si X.config.json n'existe pas","py.glb2html.mo_de_tuiles_chargees_en_meme":"Mo de tuiles chargées en même temps (poids des fichiers ; défaut %(default)g) ; au-delà, les plus lointaines partent d'abord","py.glb2html.mode_modulaire_a_coquille_commune_une":"mode modulaire à coquille commune : une seule coquille (défaut {0}) sert plusieurs régions, à l'adresse SHELL.html?region=NAME. -o désigne la région (NAME = son nom sans extension, ex. -o Ankh.html) : seuls NAME.glb, NAME.config.json et NAME.zones.json sont écrits, plus la coquille, lib/three-X/ et (la première fois) default.json s'ils sont absents (une coquille existante n'est jamais écrasée). Avec un chemin (--shared-shell FOLDER/index.html), -o peut être dans un sous-dossier de FOLDER : adresse SHELL.html?region=sous/dossier/NAME. --register écrit cette adresse dans regions.json. Implique --modular","py.glb2html.mode_modulaire_ecrit_une_coquille_page":"mode modulaire : écrit une coquille <page>.html identique pour toutes les régions (elle déduit ses fichiers de son nom) + <page>.glb (octets bruts) + <page>.config.json (réglages) + <page>.zones.json (zones, relues à chaque ouverture ; à défaut zones.json du dossier) + lib/three-X/ partagé (Draco et Meshopt compris). Demande http(s) pour l'ouverture (pas depuis le disque)","py.glb2html.nom_affiche_dans_la_carte_defaut":"nom affiché dans la carte (défaut : nom du .glb)","py.glb2html.materiaux_rendus_opaques":"noms de matériaux rendus opaques (ils masquent alors ce qui est derrière), séparés par des virgules : \"1471516\" = tout nom qui contient ce texte, \"=pbrmat-123\" = nom exact ; \"\" = aucun","py.glb2html.noms_a_ignorer_en_collision_separes":"noms à ignorer en collision, séparés par des virgules : \"door\" = début de mot, \"=mesh_346_5\" = nom exact ; \"\" = rien","py.glb2html.north":"décalage en degrés ajouté au cap affiché ; 0 = le nord est la direction -Z du modèle (OpenSim) ; pour un GLB qui ne vient pas d'OpenSim (défaut 0)","py.glb2html.ok_0_1_2_2f_mo":"[OK] {0} -> {1} ({2:.2f} Mo glb, {3:.2f} Mo html) [glb2html {4}]","py.glb2html.ok_0_1_2_3_coquille":"[OK] {0} -> {1} + {2} + {3}, coquille commune {4} ; adresse : {5} [glb2html {6}]","py.glb2html.ok_0_1_modulaire_coquille_2":"[OK] {0} -> {1} (modulaire : coquille {2:.0f} Ko + {3} {4:.2f} Mo + {5} + {6} + {7}/) [glb2html {8}]","py.glb2html.ok_0_tuile_s_1_2":"[OK] {0} tuile(s) -> {1} + {2}, ","py.glb2html.ok_region_mise_a_jour_adresse":"[OK] région mise à jour ; adresse : {0} [glb2html {1}]","py.glb2html.ok_reglages_0_coquille_et_glb":"[OK] réglages -> {0} (coquille et .glb inchangés) [glb2html {1}]","py.glb2html.panneau_de_reglages_pour_les_visiteurs":"panneau de réglages pour les visiteurs (haute résolution, mer animée, force des vagues), bouton en haut à droite","py.glb2html.petit_cone_pointe_vers_le_bas":"petit cône pointé vers le bas au-dessus de chaque portail et de chaque zone « enter » ou « both » (repère visible jusqu'à --zone-info-dist ; touche T pour l'afficher ou le masquer ; défaut : affiché ; les arrivées n'en ont qu'avec --show-spawns)","py.glb2html.position_sur_la_grille_comme_opensim":"position sur la grille, comme OpenSim (X vers l'est, Y vers le nord), ex. 1000,1001","py.glb2html.position_x_du_centre_du_trou":"position X du centre du trou (monde)","py.glb2html.position_z_du_centre_du_trou":"position Z du centre du trou (monde)","py.glb2html.public_retire_les_zones_privees_ex":"public : retire les zones privées (ex. Home Assistant) ; private : les garde (ancienne valeur perso acceptée)","py.glb2html.racine_d_un_paquet_npm_three":"racine d'un paquet npm three local (sinon cache + téléchargement)","py.glb2html.ratio_de_cadrage_1_cadrage_auto":"ratio de cadrage (1 = cadrage auto)","py.glb2html.rayon_du_trou_30_600_zone":"rayon du trou 30..600 (zone plate = rayon - fondu)","py.glb2html.reecrit_seulement_les_zones_sans_regenerer":"réécrit seulement les zones, sans régénérer le HTML : <page>.zones.json d'une page modulaire déjà générée (avec --zones FILE), ou, avec --zones-live, le fichier de zones d'une page autonome","py.glb2html.reecrit_seulement_page_config_json_d":"réécrit seulement <page>.config.json d'une page modulaire déjà générée (indiquée par -o), sans toucher au .glb ni à la coquille ; les visiteurs rechargent. <page>.zones.json n'est réécrit que si --zones est donné. Avec --register, met aussi la carte à jour","py.glb2html.region_decoupee_en_tuiles_par_glb2tiles":"région découpée en tuiles par glb2tiles.py : pas de .glb en entrée ; -o désigne la région. Écrit X.config.json (champ « tiles »), X.zones.json, la coquille et lib/ ; X.tiles.json et ses tuiles ne sont copiés que s'ils ne sont pas déjà à côté de la page. Implique --modular. Repère = celui du modèle d'origine (aucun recentrage) ; zones liées à un objet : possibles si les tuiles viennent de glb2tiles v32, ignorées sinon","py.glb2html.reglages_0_parametre_s_repris_de":"[réglages] {0} paramètre(s) repris de {1}","py.glb2html.reprend_tous_les_reglages_enregistres_par":"reprend TOUS les réglages enregistrés par le viewer (bouton « Enregistrer dans un fichier » : trou, vagues, caméra, zones, fiche de région, vignette…). Sans nom : <nom du .glb>.reglages.json. Les options de la ligne de commande l'emportent. Relatif : dossier de lancement, puis dossier du script","py.glb2html.rotation_de_la_region_autour_de":"rotation de la région autour de l'axe vertical (0, 90, 180 ou 270 degrés), appliquée au chargement avant le recentrage. Les zones, arrivées, cible et trou du fichier de zones / de réglages sont DÉJÀ dans le repère tourné (le viewer les fait tourner avec la région)","py.glb2html.salon_de_presence_defaut_nom_du":"salon de présence (défaut : nom du fichier)","py.glb2html.secondes_avant_disparition_des_messages_et":"secondes avant disparition des messages et bulles ; 0 = restent jusqu'à ce que de nouveaux messages les remplacent","py.glb2html.serveur_de_presence_ws_ou_wss":"serveur de présence ws:// ou wss:// (voir presence_server.py) ; « * » à la place du nom = le même nom que la page (ws://*:8765, conseillé pour une page ouverte par plusieurs adresses) ; vide = désactivé","py.glb2html.seuil_alpha_feuillage_0_0_5":"seuil alpha feuillage 0..0.5","py.glb2html.shell_name":"coquille {0}","py.glb2html.sortie_fichier_html_ou_dossier_cree":"sortie : fichier .html, ou dossier (créé si besoin). Entrée dossier : dossier de sortie. Défaut : \"<nom> - Offline.html\" à côté du .glb","py.glb2html.telechargements_simultanes_defaut_default_d":"téléchargements simultanés (défaut %(default)d)","py.glb2html.titre_de_la_page":"titre de la page","py.glb2html.triangles_de_tuiles_chargees_en_meme":"triangles de tuiles chargées en même temps (défaut %(default)d)","py.glb2html.tuiles_0_copie_dans_1_tuiles":"[tuiles] {0} copié dans {1} ; tuiles : {2} copiée(s) ({3:.1f} Mo), {4} déjà présente(s) de même taille (ni vérifiées ni recopiées){5}","py.glb2html.tuiles_0_tuile_s_et_1":"[tuiles] {0} tuile(s) et {1} déjà à côté de la page : rien n'est copié{2}","py.glb2html.tuiles_cible_de_camera_par_defaut":"[tuiles] cible de caméra par défaut : {0} (centre de l'étendue, repère du modèle d'origine ; --target pour la changer)","py.glb2html.tuiles_des_zones_sont_liees_a":"[tuiles] des zones sont liées à un objet (champ mesh) : la page les place avec l'objet dès que la tuile qui le contient est chargée","py.glb2html.tuiles_hauteur_de_la_mer_par":"[tuiles] hauteur de la mer par défaut : 20 m (repère du modèle d'origine, comme l'eau d'OpenSim ; --sea-y pour la changer, --no-sea pour la retirer)","py.glb2html.vignette_de_la_region_fichier_jpg":"vignette de la région : fichier jpg/png/webp de 140 Ko maximum (intégré), ou adresse http(s) (gardée telle quelle, carte plus légère)","py.glb2html.vitesse_de_marche_en_m_s":"vitesse de marche en m/s (Maj = x2.2)","py.glb2html.voir_les_visiteurs_en_promenade_depuis":"voir les visiteurs en promenade depuis la vue globale (se connecte dès l'ouverture de la page ; actif par défaut dès qu'une --presence-url est donnée ; --no-spectate pour l'éviter)","py.glb2html.vol_en_promenade_touche_f_ou":"vol en promenade (touche F ou Début ; Page Haut / E monte, Page Bas / C descend) : activé par défaut, --no-fly le retire","py.glb2html.vue_d_ensemble_0_placee_avec":" ; vue d'ensemble {0} placée avec les tuiles","py.glb2html.zones_0_non_modifie_donne_zones":"[zones] {0} non modifié (donne --zones FILE pour le réécrire)","py.glb2html.zones_0_zone_s_lue_s":"[zones] {0} zone(s) lue(s) dans {1}","py.glb2html.zones_0_zone_s_profil_1":"[zones] {0} zone(s), profil {1} -> {2}","py.glb2html.zones_zones_deja_en_place_0":"[zones] zones déjà en place : {0} (non réécrit)","py.glb2html.zones_zones_deja_en_place_0_2":"[zones] zones déjà en place : {0} (lu pour vérification, non réécrit ni copié)","py.glb2tiles.0_1_0f_m_du_centre":"« {0} » ({1:.0f} m du centre, étendue {2:.0f} m)","py.glb2tiles.0_1_2f_mo_2_triangles":"  - « {0} » : {1:.2f} Mo, {2} triangles, étendue (X x Y x Z) {3}, {4} instance(s)","py.glb2tiles.0_distance_1_0f_m_etendue":"  - « {0} » : distance {1:.0f} m, étendue {2:.0f} m","py.glb2tiles.0_illisible_1":"{0} illisible ({1}).","py.glb2tiles.0_instance_s_aberrante_s_a":"{0} instance(s) aberrante(s) (à plus de {1:g} m du centre médian ou d'étendue supérieure) : {2}.","py.glb2tiles.0_introuvable_vue_ensemble_seule_suppose":"{0} introuvable : --overview-only suppose que le découpage a déjà été fait (dans {1}).","py.glb2tiles.0_nud_s_avec_camera_ou":"{0} nœud(s) avec caméra ou extensions de nœud : ces champs ne sont pas recopiés dans les tuiles.","py.glb2tiles.0_objet_s_au_nom_correspondant":"  {0} objet(s) au nom correspondant conservé(s) par les garde-fous (trop de triangles ou de meshes)","py.glb2tiles.0_octet_gagne_toute_la_geometrie":"  0 octet gagné : toute la géométrie et toutes les images des objets exclus sont partagées avec des objets conservés (même primitive ou même texture, typiquement un cube commun) ; retirer ces objets enlève des nœuds et des triangles, pas des octets.","py.glb2tiles.0_scenes_seule_la_scene_1":"{0} scènes : seule la scène {1} est découpée.","py.glb2tiles.accessor_0_accessor_sparse_non_gere":"Accessor {0} : accessor « sparse » non géré par glb2tiles.","py.glb2tiles.accessor_0_bytestride_1_plus_petit":"Accessor {0} : byteStride ({1}) plus petit qu'un élément ({2}).","py.glb2tiles.accessor_0_depasse_son_bufferview_fichier":"Accessor {0} : dépasse son bufferView (fichier invalide).","py.glb2tiles.accessor_0_indices_avec_bytestride_non":"Accessor {0} : indices avec byteStride non gérés.","py.glb2tiles.accessor_0_inexistant":"Accessor {0} inexistant.","py.glb2tiles.accessor_0_positions_non_gerees":"Accessor {0} : positions non gérées.","py.glb2tiles.accessor_0_sans_bufferview_valeurs_a":"Accessor {0} : sans bufferView (valeurs à zéro) non géré par glb2tiles.","py.glb2tiles.accessor_0_type_1_2_inconnu":"Accessor {0} : type {1}/{2} inconnu.","py.glb2tiles.accessor_0_type_d_indices_non":"Accessor {0} : type d'indices non géré.","py.glb2tiles.accessor_0_un_indice_depasse_le":"Accessor {0} : un indice dépasse le nombre de sommets ({1}) : fichier invalide.","py.glb2tiles.analyse_0_primitives_distinctes_a_mesurer":"[analyse] {0} primitives distinctes à mesurer (lecture des indices par morceaux)","py.glb2tiles.aucun_mesh_positionnable_dans_la_scene":"Aucun mesh positionnable dans la scène : rien à découper.","py.glb2tiles.avec_exclure_meshes_au_plus_dans":"avec --exclude : meshes au plus dans l'objet racine (défaut 1)","py.glb2tiles.avec_exclure_triangles_au_plus_dans":"avec --exclude : triangles au plus dans l'objet racine, tous meshes compris (défaut 24)","py.glb2tiles.avertissement_0_d_une_execution_precedente":"Avertissement : {0} d'une exécution précédente n'est pas retiré, mais l'index ne le mentionne plus (--no-overview).","py.glb2tiles.avertissement_0_existe_deja_mais_ses":"Avertissement : {0} existe déjà mais ses tuiles ne portent pas les références d'objets (glb2tiles avant la v32) : pour lier des zones à des objets en mode tuiles, refaire le découpage.","py.glb2tiles.avertissement_ces_tuiles_ont_ete_ecrites":"Avertissement : ces tuiles ont été écrites sans les références d'objets (glb2tiles avant la v32) : les zones liées à un objet restent ignorées en mode tuiles. Refaire le découpage (sans --overview-only) pour en profiter.","py.glb2tiles.bufferview_0_inexistant":"bufferView {0} inexistant.","py.glb2tiles.bufferview_0_seul_le_tampon_0":"bufferView {0} : seul le tampon 0 est géré.","py.glb2tiles.ce_glb_est_compresse":"Ce GLB est compressé (","py.glb2tiles.cellules_sur_la_plus_grande_dimension":"cellules sur la plus grande dimension d'une primitive pour le regroupement de sommets (défaut %(default)d)","py.glb2tiles.cote_des_blocs_de_la_section":"côté des blocs de la section glb-stats de --analyse (défaut 256)","py.glb2tiles.cote_minimal_d_une_cellule_en":"côté minimal d'une cellule en m (défaut 16)","py.glb2tiles.couleurs_moyenne_de_texture_pour_0":"  couleurs : moyenne de texture pour {0} image(s), {1} illisible(s) (couleur de base)","py.glb2tiles.couleurs_pillow_absent_couleur_de_base":"  couleurs : Pillow absent, couleur de base du matériau ({0} matériau(x) texturé(s) concerné(s)) ; installer Pillow pour les couleurs moyennes","py.glb2tiles.decoupage_prevu_budget_0_g_mo":"== Découpage prévu (budget {0:g} Mo, {1} triangles, cellule minimale {2:g} m) ==","py.glb2tiles.decouper_meme_si_la_recommandation_est":"découper même si la recommandation est « pas de découpage »","py.glb2tiles.des_primitives_portent_des_extensions_elles":"Des primitives portent des extensions : elles ne sont pas recopiées dans les tuiles.","py.glb2tiles.desc":"glb2tiles.py {0} : découpe un GLB énorme en tuiles autonomes et écrit X.tiles.json et la vue d'ensemble X.overview.glb (Python standard seulement).","py.glb2tiles.dossier_de_sortie_defaut_a_cote":"dossier de sortie (défaut : à côté du GLB)","py.glb2tiles.duplication_reelle_de_la_geometrie_somme":"Duplication réelle de la géométrie (somme des tuiles / géométrie unique) : {0}","py.glb2tiles.entree_pour_fermer":"Entrée pour fermer...","py.glb2tiles.epilog":"Exemples :\n  python glb2tiles.py Region.glb --analyse\n  python glb2tiles.py Region.glb --budget 32 --budget-triangles 1500000\n  python glb2tiles.py Region.glb --overview-only\nLe journal est glb2tiles.log, écrit à côté du script. glb-stats.py doit se trouver à côté de ce script.","py.glb2tiles.erreur_0":"[ERREUR] {0}","py.glb2tiles.etendue_des_instances_plus_grande_dimension":"Étendue des instances (plus grande dimension) : instances et triangles au-dessus de chaque seuil","py.glb2tiles.etendue_minimale_effective_0_g_m":"  étendue minimale effective {0:g} m (seuil demandé {1:g} m), résolution {2}, pas du terrain {3:g} m (demandé {4:g} m)","py.glb2tiles.expression_reguliere_invalide_pour_exclure_0":"Expression régulière invalide pour --exclude : {0!r} ({1}).","py.glb2tiles.fichier_glb_tronque":"Fichier GLB tronqué.","py.glb2tiles.glb2tiles_0":"[glb2tiles] {0}","py.glb2tiles.glb2tiles_0_1_1f_mo":"[glb2tiles] {0} : {1:.1f} Mo","py.glb2tiles.glb2tiles_0_2":"glb2tiles {0}","py.glb2tiles.glb2tiles_ne_lit_pas_les_glb":") : glb2tiles ne lit pas les GLB compressés (hors de son périmètre). Décompresser le GLB d'abord, puis relancer.","py.glb2tiles.glb_d_entree":"GLB d'entrée","py.glb2tiles.glb_introuvable_0":"GLB introuvable : {0}","py.glb2tiles.glb_stats_py_introuvable_a_cote":"glb-stats.py introuvable à côté de glb2tiles.py ({0}) : le copier au même endroit.","py.glb2tiles.image_externe_uri_non_geree_seuls":"Image externe (uri) non gérée : seuls les GLB à images intégrées le sont.","py.glb2tiles.images_vides_ou_invalides_remplacees_par":"Images vides ou invalides remplacées par un PNG gris de {0} : {1} distincte(s), {2} occurrence(s) (une occurrence = une image écrite dans une tuile) ; matériaux et coordonnées de texture inchangés.","py.glb2tiles.la_tuile_0_n_a_plus":"La tuile {0} n'a plus le contenu de {1} : utiliser les mêmes options que pour le découpage d'origine.","py.glb2tiles.la_vue_d_ensemble_depasse_la":"La vue d'ensemble dépasse la limite de 4 Go d'un GLB.","py.glb2tiles.le_decoupage_recalcule_0_tuiles_ne":"Le découpage recalculé ({0} tuiles) ne correspond pas à {1} ({2} tuiles) : utiliser les mêmes options (--budget, --budget-triangles, --min, --entier-*, --exclude…) que pour le découpage d'origine.","py.glb2tiles.le_tampon_0_a_une_adresse":"Le tampon 0 a une adresse (uri) : seuls les GLB à tampon intégré sont gérés.","py.glb2tiles.lecture_0_octets_lus_sur_1":"Lecture : {0} octets lus sur {1} (plus grande lecture {2} octets; positions relues pour {3} octets, primitives qui partagent un tampon de sommets).","py.glb2tiles.lecture_hors_du_tampon_du_glb":"Lecture hors du tampon du GLB (décalage {0}, {1} octets) : fichier invalide ou tronqué.","py.glb2tiles.lecture_seule_mesures_decoupage_prevu_recomm":"lecture seule : mesures, découpage prévu, recommandation ; n'écrit rien","py.glb2tiles.les_10_instances_les_plus_eloignees":"== Les 10 instances les plus éloignées du centre médian (X {0:.0f} m, Z {1:.0f} m) ==","py.glb2tiles.les_10_meshes_les_plus_lourds":"== Les 10 meshes les plus lourds (octets compactés, sommets réellement utilisés) ==","py.glb2tiles.log_0":"[log] {0}","py.glb2tiles.m_distance_ou_etendue_au_dela":"m : distance ou étendue au-delà de laquelle une instance est signalée (défaut 1000)","py.glb2tiles.m_etendue_maximale_d_un_objet":"m : étendue maximale d'un objet racine gardé entier (défaut 256)","py.glb2tiles.m_les_objets_dont_la_plus":"m : les objets dont la plus grande dimension est plus petite sont omis (défaut %(default)g) ; le budget peut le relever","py.glb2tiles.m_pas_du_reseau_du_terrain":"m : pas du réseau du terrain dans la vue d'ensemble (défaut %(default)g)","py.glb2tiles.m_si_le_budget_oblige_a":"m : si le budget oblige à omettre des objets plus grands, la résolution baisse (défaut %(default)g)","py.glb2tiles.machine_big_endian_non_geree":"Machine big-endian non gérée.","py.glb2tiles.mesh_0_primitive_sans_position_non":"Mesh {0} : primitive sans POSITION non gérée.","py.glb2tiles.mesures_de_glb_stats":"== Mesures de glb-stats ==","py.glb2tiles.mo_par_tuile_defaut_32":"Mo par tuile (défaut 32)","py.glb2tiles.mo_poids_maximal_de_la_vue":"Mo : poids maximal de la vue d'ensemble (défaut %(default)g)","py.glb2tiles.mo_sous_ce_poids_et_sous":"Mo : sous ce poids (et sous --threshold-triangles) « pas de découpage » (défaut 150)","py.glb2tiles.mo_un_objet_racine_plus_leger":"Mo : un objet racine plus léger et plus petit que --whole-extent reste entier (défaut 16)","py.glb2tiles.n_ecrire_que_x_overview_glb":"n'écrire que X.overview.glb (et sa mention dans X.tiles.json) : les tuiles existantes ne sont pas réécrites ; les paramètres de découpage doivent être ceux du découpage d'origine","py.glb2tiles.ne_pas_attendre_entree_a_la":"ne pas attendre Entrée à la fin","py.glb2tiles.ne_pas_ecrire_extras_ref_extras":"ne pas écrire extras.ref / extras.box dans les nœuds des tuiles (format de la v31 : les zones liées à un objet sont alors ignorées en mode tuiles)","py.glb2tiles.ne_pas_ecrire_x_overview_glb":"ne pas écrire X.overview.glb (vue d'ensemble légère de toute la région)","py.glb2tiles.nud_0":"nœud {0}","py.glb2tiles.nud_0_mesh_1_inexistant":"Nœud {0} : mesh {1} inexistant.","py.glb2tiles.objets_exclus_exclure_au_plus_0":"Objets exclus (--exclude, au plus {0} triangles et {1} mesh(es) par objet racine) : {2} | triangles retirés : {3} | octets gagnés : {4} ({5:.1f} Mo)","py.glb2tiles.objets_omis_0_trop_petits_etendue":"  objets omis : {0} trop petits (étendue sous le seuil), {1} par le budget, {2} avec squelette ; primitives translucides omises : {3}","py.glb2tiles.objets_racine_0_gardes_entiers_1":"Objets racine : {0} | gardés entiers : {1} (dont {2} avec skin) | répartis instance par instance : {3}","py.glb2tiles.objets_racine_gardes_entiers_0_repartis":"Objets racine gardés entiers : {0} | répartis : {1}","py.glb2tiles.octets_des_exclus_qu_un_objet":"  octets des exclus qu'un objet conservé utilise aussi (non gagnés) : {0} ({1:.1f} Mo)","py.glb2tiles.poids_mo_mediane_0_1f_90":"Poids (Mo) : médiane {0:.1f} | 90 % sous {1:.1f} | maximum {2:.1f}","py.glb2tiles.poids_par_tuile_mo_mediane_0":"Poids par tuile (Mo) : médiane {0:.1f} | 90 % sous {1:.1f} | maximum {2:.1f}","py.glb2tiles.primitive_les_attributs_n_ont_pas":"Primitive : les attributs n'ont pas tous {0} sommets (accessor {1}).","py.glb2tiles.rapport":"== Rapport ==","py.glb2tiles.recommandation_decouper_budget_0_g_mo":"Recommandation : découper : budget {0:g} Mo, {1} tuiles, duplication {2}.","py.glb2tiles.recommandation_pas_de_decoupage_necessaire_0":"Recommandation : pas de découpage nécessaire ({0:.1f} Mo sous {1:g} Mo et {2} triangles sous {3}).","py.glb2tiles.references_d_objets_extras_ref_extras":"Références d'objets (extras.ref, extras.box) : {0} nœud(s) nommé(s), {1} nom(s) partagé(s) par plusieurs nœuds (référence nom#index) : zones liées à un objet possibles en mode tuiles.","py.glb2tiles.references_d_objets_non_ecrites_sans":"Références d'objets non écrites (--no-refs) : les zones liées à un objet seront ignorées en mode tuiles.","py.glb2tiles.retire_du_decoupage_les_objets_racine":"retire du découpage les objets racine dont le nom correspond (insensible à la casse, répétable), à condition de respecter --exclude-max-triangles et --exclude-max-meshes","py.glb2tiles.rien_n_est_ecrit_forcer_pour":"Rien n'est écrit (--force pour découper quand même).","py.glb2tiles.sans_instance":"sans instance","py.glb2tiles.sans_vue_ensemble_et_vue_ensemble":"--no-overview et --overview-only s'excluent.","py.glb2tiles.skin_0_inexistant":"Skin {0} inexistant.","py.glb2tiles.temps_0_1f_s":"[temps] {0:.1f} s","py.glb2tiles.temps_0_1f_s_1_octets":"[temps] {0:.1f} s ; {1} octets lus sur {2}","py.glb2tiles.texture_0_inexistante":"Texture {0} inexistante.","py.glb2tiles.triangles_de_la_vue_d_ensemble":"triangles de la vue d'ensemble (défaut %(default)d)","py.glb2tiles.triangles_mediane_0_90_sous_1":"Triangles : médiane {0} | 90 % sous {1} | maximum {2}","py.glb2tiles.triangles_par_tuile_defaut_1500000":"triangles par tuile (défaut 1500000)","py.glb2tiles.triangles_par_tuile_mediane_0_90":"Triangles par tuile : médiane {0} | 90 % sous {1} | maximum {2}","py.glb2tiles.triangles_pour_la_recommandation_pas_de":"triangles pour la recommandation « pas de découpage » (défaut 3000000)","py.glb2tiles.tuile_0_1_2f_go_au":"Tuile {0} : {1:.2f} Go, au-delà de la limite de 4 Go d'un GLB.","py.glb2tiles.tuile_0_hors_budget_1_1f":"Tuile {0} hors budget ({1:.1f} Mo, {2} triangles) : {3}. Un mesh unique plus grand qu'une cellule ne peut pas être réparti à ce stade.","py.glb2tiles.tuiles_0_dans_1":"Tuiles : {0} dans {1}","py.glb2tiles.tuiles_0_duplication_prevue_geometrie_1":"Tuiles : {0} | duplication prévue : géométrie {1}, images {2}","py.glb2tiles.tuiles_d_une_execution_precedente_absentes":"Tuiles d'une exécution précédente absentes du nouvel index : {0} fichier(s) T_*.glb supprimé(s)","py.glb2tiles.vue_d_ensemble_0_1_1f":"Vue d'ensemble {0} : {1:.1f} Mo, {2} triangles (dont terrain {3}), {4} objet(s) gardés sur {5}, en {6:g} s","py.glb2tiles.vue_d_ensemble_0_1f_mo":"[vue d'ensemble] {0:.1f} Mo, {1} triangles, {2} objet(s) sur {3}, {4} tuile(s) en {5:.1f} s","py.glb2tiles.vue_d_ensemble_budget_0_g":"[vue d'ensemble] budget {0:g} Mo et {1} triangles, seuil d'étendue {2:g} m, résolution {3}, pas du terrain {4:g} m","py.glb2tiles.vue_d_ensemble_budget_atteint_avant":"[vue d'ensemble] budget atteint avant des objets de {0:.0f} m : résolution réduite à {1}","py.glb2tiles.vue_d_ensemble_terrain_0_piece":"[vue d'ensemble] terrain : {0} pièce(s), {1} triangles, réseau de {2:g} m","py.glb2tiles.vue_d_ensemble_terrain_trop_lourd":"[vue d'ensemble] terrain trop lourd pour la moitié du budget : pas porté à {0:g} m","py.glb2tiles.warning_prefix":"Avertissement : ","py.oar2glb.0_5d_1_2_3_rigge":"{0:5d} | {1} | {2} | {3} | riggé : {4} | échelle du prim {5} | échelle bind_shape {6} | transparent : {7} | boîte racine d'animesh : {8} | GLB : {9}","py.oar2glb.0_face_s_a_part":" (+{0} face(s) à part)","py.oar2glb.accesseur_0_non_gere":"accesseur {0} non géré","py.oar2glb.accesseur_0_non_gere_float_vec3":"accesseur {0} non géré (float VEC3 simple attendu)","py.oar2glb.accesseur_position_0_bufferview_1_buffer":"      accesseur POSITION {0} ; bufferView {1} ; buffer {2} {3} o ; 3 premiers sommets {4}","py.oar2glb.ajouter_un_mat_rouge_de_15":"ajouter un mât rouge de 15 m à chaque animal riggé posé (pour le retrouver dans le viewer)","py.oar2glb.altitude_de_la_racine":"altitude de la racine","py.oar2glb.args":"[args]","py.oar2glb.aucune":"aucune","py.oar2glb.aucune_geometrie":"aucune géométrie","py.oar2glb.avec_diag_glb_ou_gltf_a":"avec --diag : GLB ou .gltf à comparer ; défaut : le .gltf du dossier <oar>-GLTF (conservé par --keep), sinon le .glb voisin","py.oar2glb.avec_terrain_seul_fichier_glb_de":"avec --terrain-only : fichier GLB de sortie (défaut : X-terrain.glb à côté de l'original)","py.oar2glb.bind_shape_matrix_0":"      bind_shape_matrix : {0}","py.oar2glb.bind_shape_matrix_non_inversible":"bind_shape_matrix non inversible","py.oar2glb.bloc_skin_present_mais_illisible":"bloc skin présent mais illisible","py.oar2glb.boite_racine_d_animesh":"boîte racine d'animesh","py.oar2glb.cle_llsd_attendue":"clé LLSD attendue","py.oar2glb.controle_0_pieds_a_1_2f":"[contrôle] '{0}' pieds à {1:.2f} m, centre {2:.2f} m : ","py.oar2glb.convoar":"[convoar]","py.oar2glb.convoar_0_image_s_annoncee_s":"[convoar] {0} image(s) annoncée(s) par le .gltf mais absente(s) du dossier (exemples : {1}) : nouvel essai {2}/{3}, les images déjà écrites sont conservées","py.oar2glb.convoar_0_image_s_recuperee_s":"[convoar] {0} image(s) récupérée(s) de l'essai précédent","py.oar2glb.convoar_code_retour_0":"[convoar] code retour {0}","py.oar2glb.correctif_0_mesh_es_rigge_s":"[correctif] {0} mesh(es) riggé(s) remis à l'échelle, {1} prim(s) invisible(s) retiré(s)","py.oar2glb.cote_d_un_patch_de_terrain":"côté d'un patch de terrain en mètres, 2 à 255 (défaut {0})","py.oar2glb.dans_la_boite_de_0_objet":"dans la boîte de {0} objet(s) : {1}","py.oar2glb.defaut_d_opensim_aucun_waterheight_dans":"défaut d'OpenSim, aucun WaterHeight dans settings/","py.oar2glb.desc":"oar2glb.py {0} : convertit une sauvegarde de région OpenSim (.oar) en un seul GLB (convoar, réparation, terrain complet, empaquetage).","py.oar2glb.dessous_de_la_boite_racine":"dessous de la boîte racine","py.oar2glb.diag_0_objet_s_1_partie":"[diag] {0} objet(s), {1} partie(s) ; terrain {2} ; {3}","py.oar2glb.diag_nuds_glb_dont_tous_les":"[diag] nœuds GLB dont tous les matériaux sont transparents : {0}","py.oar2glb.diag_pos":"      position {0} ; terrain {1} ; {2}","py.oar2glb.diag_rigges_0_transparents_1_boites":"[diag] riggés : {0} ; transparents : {1} ; boîtes racines d'animesh : {2} ; nœuds GLB trouvés : {3}/{4}","py.oar2glb.diag_uuid_lisibles_dans_les_nuds":"[diag] UUID lisibles dans les nœuds GLB : {0} ; exemples de nœuds :","py.oar2glb.domaine_de_position_du_mesh_0":"      domaine de position du mesh ({0} sous-maillage(s)) : ","py.oar2glb.echelle_du_prim_appliquee_0":" ; échelle du prim appliquée : {0}","py.oar2glb.en_tete_du_mesh_illisible_0":"en-tête du mesh illisible ({0})","py.oar2glb.entree_pour_fermer":"Entrée pour fermer...","py.oar2glb.epilog":"Exemples :\n  python oar2glb.py \"P:\\chemin\\MaRegion.oar\"\n  python oar2glb.py \"P:\\chemin\\MaRegion.oar\" --keep --markers\n  python oar2glb.py \"P:\\chemin\\MaRegion.oar\" --diag        (ne modifie rien, ne lance pas convoar)\n  python oar2glb.py --terrain-only MaRegion.glb \"P:\\chemin\\MaRegion.oar\"","py.oar2glb.erreur_0_introuvable":"[ERREUR] {0} introuvable","py.oar2glb.erreur_0_introuvable_annonce_par_le":"[ERREUR] {0} introuvable (annoncé par le .gltf).\n  {1} contient {2} fichier(s), dont {3} .buf : ","py.oar2glb.erreur_0_le_premier_chunk_n":"[ERREUR] {0} : le premier chunk n'est pas JSON","py.oar2glb.erreur_0_le_tampon_0_n":"[ERREUR] {0} : le tampon 0 n'est pas celui du chunk BIN","py.oar2glb.erreur_0_n_est_pas_un":"[ERREUR] {0} n'est pas un GLB","py.oar2glb.erreur_0_n_est_pas_un_2":"[ERREUR] {0} n'est pas un GLB version 2","py.oar2glb.erreur_0_tronque":"[ERREUR] {0} tronqué","py.oar2glb.erreur_0_vecteurs_de_mauvaise_taille":"[ERREUR] {0} vecteurs de mauvaise taille : nombres écrits avec virgule décimale.\n  ","py.oar2glb.erreur_aucun_gltf_produit_dans_0":"[ERREUR] aucun .gltf produit dans {0}","py.oar2glb.erreur_compilation_du_lanceur_0_1":"[ERREUR] compilation du lanceur :\n{0}{1}","py.oar2glb.erreur_convoar_introuvable_0_utilise_convoar":"[ERREUR] convoar introuvable : {0}\n  convoar.exe est le convertisseur externe dont oar2glb.py a besoin. Téléchargement : {1}\n  Indiquer son emplacement avec --convoar CHEMIN (ou la variable CONVOAR, ou le mettre dans le PATH).","py.oar2glb.erreur_csc_exe_net_framework_4":"[ERREUR] csc.exe (.NET Framework 4) introuvable","py.oar2glb.erreur_gltf_invalide_0_ligne_1":"[ERREUR] .gltf invalide : {0}\n  ligne {1} : {2}","py.oar2glb.erreur_la_sortie_ne_peut_pas":"[ERREUR] la sortie ne peut pas être le GLB d'origine (jamais écrasé)","py.oar2glb.erreur_reencode_demande_pillow_absent_de":"[ERREUR] --reencode demande Pillow, absent de ce Python ({0}).\n  Installe-le dans ce Python précis : & \"{1}\" -m pip install pillow","py.oar2glb.erreur_terrain_patch_doit_etre_compris":"[ERREUR] --terrain-patch doit être compris entre 2 et 255 (indices 16 bits : (côté + 1)² sommets au plus 65 536)","py.oar2glb.espace_libre_sur_0_1_1f":"\n  Espace libre sur {0} : {1:.1f} Go","py.oar2glb.etendue_0_objets_de_1_a":"[étendue] {0} objets de {1} à {2}  (glTF : X, hauteur, -Y)","py.oar2glb.fin_de_table_llsd_attendue":"fin de table LLSD attendue","py.oar2glb.fin_de_tableau_llsd_attendue":"fin de tableau LLSD attendue","py.oar2glb.force_terrain_oui":"forcé (--terrain yes)","py.oar2glb.garder_les_fichiers_intermediaires":"garder les fichiers intermédiaires","py.oar2glb.garder_les_prims_entierement_transparents_re":"garder les prims entièrement transparents (retirés par défaut)","py.oar2glb.geometrie_du_llmesh_illisible":"géométrie du .llmesh illisible","py.oar2glb.glb_0_1":"[GLB] {0} -> {1}","py.oar2glb.glb_0_contient_1_fichier_s":"[GLB] {0} contient {1} fichier(s) : ","py.oar2glb.glb_0_texture_s_absente_s":"[GLB] {0} texture(s) absente(s) sur {1}, remplacée(s) par du gris. Exemples : ","py.oar2glb.glb_fichiers_images_presents_exemples":"[GLB] fichiers images présents, exemples : ","py.oar2glb.hauteur_max_m_d_un_objet":"hauteur max (m) d'un objet racine (skybox au-delà), défaut 600","py.oar2glb.help.convoar":"chemin de convoar.exe (défaut : variable CONVOAR, sinon convoar du PATH, sinon convoar.exe à côté de oar2glb.py ; téléchargement : https://github.com/Misterblue/convoar/tree/master/bin)","py.oar2glb.help.oar":"fichier .oar (ou .tgz) de la région à convertir","py.oar2glb.hors_region_node_0_1_a":"[hors région] node {0} '{1}' à {2} retiré","py.oar2glb.invisible_node_0_1_retire_2":"[invisible] node {0} '{1}' retiré : {2}","py.oar2glb.lanceur_0_compile_1":"[lanceur] {0} compilé ({1})","py.oar2glb.lanceur_0_mis_a_jour_loadfromremotesources":"[lanceur] {0} mis à jour (loadFromRemoteSources)","py.oar2glb.le_nud_n_a_pas_de":"le nœud n'a pas de mesh","py.oar2glb.les_patches_de_terrain_sont_deja":"les patches de terrain sont déjà dans ce GLB : inchangé","py.oar2glb.libre_aucune_boite_d_objet_ne":"libre (aucune boîte d'objet ne le contient)","py.oar2glb.list_paren":" (liste : {0})","py.oar2glb.log_0":"[log] {0}","py.oar2glb.lu_dans":"lu dans ","py.oar2glb.materiau_glb_0_r_couleur_1":"      matériau GLB : {0!r} couleur {1} mode {2} image {3}","py.oar2glb.materiaux_transparents_glb":"matériaux transparents (GLB)","py.oar2glb.ne_pas_attendre_entree_a_la":"ne pas attendre Entrée à la fin","py.oar2glb.ne_pas_lancer_convoar_ajouter_le":"ne pas lancer convoar : ajouter le terrain complet à ce GLB (écrit X-terrain.glb, l'original n'est jamais modifié)","py.oar2glb.ne_rien_modifier_lister_les_objets":"ne rien modifier : lister les objets de l'OAR, leur skin et le nœud GLB correspondant","py.oar2glb.node_0_nom_1_r_extras":"       node {0} : nom={1!r} extras={2} clés={3}","py.oar2glb.non_pas_un_mesh":"non (pas un mesh)","py.oar2glb.nud":"nœud","py.oar2glb.nud_0_1_2_echelle_du":"nœud {0} '{1}' [{2}] ; échelle du nœud {3}","py.oar2glb.nud_introuvable":"nœud introuvable","py.oar2glb.nud_terrain_sans_min_max_d":"nœud « Terrain » sans min/max d'accesseur : couverture inconnue, inchangé (--terrain yes pour forcer)","py.oar2glb.oar2glb_0":"[oar2glb] {0}","py.oar2glb.oar2glb_0_2":"oar2glb {0}","py.oar2glb.oar_0_illisible_1":"[OAR] {0} illisible ({1})","py.oar2glb.oar_0_objets_de_1_a":"[OAR] {0} objets de {1} à {2}  (X, Y, Z OpenSim, Z = hauteur)","py.oar2glb.oar_region_0_g_x_1":"[OAR] région {0:g} x {1:g} m","py.oar2glb.ok_0_1_1f_mo_2":"[OK] {0}  ({1:.1f} Mo, {2} meshes, {3} textures, {4} objet(s) hors région retiré(s))","py.oar2glb.pas_de_glb_correspondance_non_evaluee":"pas de GLB : correspondance non évaluée (--glb)","py.oar2glb.pas_de_nud_terrain_de_convoar":"pas de nœud « Terrain » de convoar : inchangé (--terrain yes pour ajouter les patches quand même)","py.oar2glb.reencoder_les_textures_j2k_avant_convoar":"réencoder les textures J2K avant convoar","py.oar2glb.reperes_0_mat_s_rouge_s":"[repères] {0} mât(s) rouge(s) de 15 m ajouté(s), un par animal posé","py.oar2glb.rien":"rien","py.oar2glb.rigge_0_1_ignore":"[riggé] '{0}' : {1}, ignoré","py.oar2glb.rigge_0_1_morceau_x_echelle":"[riggé] '{0}' : {1} morceau(x), échelle du prim {2}, {3:.2f} x {4:.2f} x {5:.2f} m (L x l x h), centré en ({6:.1f}, {7:.1f}), pieds à {8:.2f} m ({9})","py.oar2glb.rigge_0_1_non_corrige":"[riggé] '{0}' : {1}, non corrigé","py.oar2glb.rigge_0_1_nud_glb_introuvable":"[riggé] '{0}' ({1}) : nœud GLB introuvable, non corrigé (voir --diag)","py.oar2glb.rigge_0_reconstruit_depuis_l_oar":"[riggé] '{0}' reconstruit depuis l'OAR : {1} face(s), {2} sommets, {3} triangles (convoar : {4} primitive(s), {5} sommets), échelle du prim ignorée {6}, échelle de bind_shape {7}","py.oar2glb.rigge_0_taille_obtenue_1_2f":"[riggé] '{0}' : taille obtenue {1:.2f} x {2:.2f} x {3:.2f} m implausible (hors de {4:g} à {5:g} m), laissé tel que convoar l'a produit","py.oar2glb.sans_bind_shape_matrix":"sans bind_shape_matrix","py.oar2glb.sans_extension":"(sans extension)","py.oar2glb.sans_textureentry":"sans TextureEntry","py.oar2glb.sommets_du_glb_axes_opensim_x":"      sommets du GLB (axes OpenSim x, y, z) : de {0} à {1} soit {2} m, {3} sommets","py.oar2glb.sommets_du_glb_illisibles_0":"      sommets du GLB illisibles ({0})","py.oar2glb.terrain_0":"[terrain] {0}","py.oar2glb.terrain_0_nud_s_terrain_de":"[terrain] {0} nœud(s) « Terrain » de convoar retiré(s) de la scène","py.oar2glb.terrain_0_nud_s_terrain_retire":"[terrain] {0} nœud(s) « Terrain » retiré(s) de la scène (leurs données restent dans le GLB, inutilisées) ; {1:.1f} Mo lus, par morceaux de {2} Ko au plus","py.oar2glb.terrain_attention_carte_de_0_x":"[terrain] attention : carte de {0} x {1} échantillons pour une région de {2:g} x {3:g} m","py.oar2glb.terrain_aucun_fichier_ecrit":"[terrain] aucun fichier écrit","py.oar2glb.terrain_carte_0_x_1_echantillons":"[terrain] carte {0} x {1} échantillons (1 m) ; niveau d'eau {2:g} m ({3}) ; {4} patch(es) de {5} m ; {6} sommets ; {7:.1f} Mo ajoutés ; {8:.1f} s","py.oar2glb.terrain_cet_oar_n_a_pas":"[terrain] cet OAR n'a pas de carte de hauteurs (terrains/*.r32) : terrain non généré, rien n'est modifié","py.oar2glb.terrain_complet_depuis_la_carte_de":"terrain complet depuis la carte de hauteurs : auto = remplace le terrain de convoar s'il couvre moins que la carte (défaut), oui = toujours, non = jamais","py.oar2glb.terrain_de_convoar_complet_couvre_0":"terrain de convoar complet (couvre {0:.1f} % de la carte) : inchangé","py.oar2glb.terrain_de_convoar_incomplet_couvre_0":"terrain de convoar incomplet (couvre {0:.1f} % de la carte)","py.oar2glb.terrain_desactive_terrain_non":"[terrain] désactivé (--terrain no)","py.oar2glb.texture_0_alpha_1_2f":"texture {0} alpha {1:.2f}","py.oar2glb.textures_0_1_2_3_0f":"[textures] {0}/{1} ({2} %) - {3:.0f} s","py.oar2glb.textures_0_reencodees_1_illisibles_remplacee":"[textures] {0} réencodées, {1} illisibles remplacées par un gris neutre","py.oar2glb.textures_0_sculpt_maps_laissees_intactes":"[textures] {0} sculpt maps laissées intactes","py.oar2glb.textures_0_textures_a_reencoder_sur":"[textures] {0} textures à réencoder sur {1} cœurs ({2:.0f} s)","py.oar2glb.textures_ecriture_de_0":"[textures] écriture de {0}...","py.oar2glb.textures_lecture_de_0":"[textures] lecture de {0}...","py.oar2glb.translation_bind_shape_0":" ; translation bind_shape {0}","py.oar2glb.type_llsd_inconnu_0_r":"type LLSD inconnu {0!r}","py.oar2glb.unknown":"inconnu","py.oar2glb.unreadable":"illisible","py.oar2glb.uuid_du_mesh":"UUID du mesh","py.oar2glb.uuid_du_prim":"UUID du prim","py.oar2glb.var_region_0_objet_s_replace":"[var-region] {0} objet(s) replacé(s) à leur vraie position, {1} reconnu(s), {2} non reconnu(s)","py.presence.0_1_20_jusqu_au_2":"  {0}. {1:<20} jusqu'au {2:<17} {3}","py.presence.0_1_2_autres_appareils_du":" · {0}://{1}:{2} (autres appareils du réseau)","py.presence.0_ejecte":"{0} éjecté","py.presence.0_id_1_cle_2_ip":"{0} [id {1}, clé {2}, ip {3}]","py.presence.adresses_ip_dans_le_journal_masquees":"adresses IP dans le journal : masquées (défaut), en clair, ou absentes","py.presence.aucun_bannissement":"(aucun bannissement)","py.presence.ban_ip":"banni (IP)","py.presence.banned":"banni","py.presence.banned_line":"{0} banni ({1})","py.presence.bannissement_de_0_leve":"bannissement de {0} levé","py.presence.certificat_tls_wss":"certificat TLS (wss://)","py.presence.chat":"chat","py.presence.cle_0_ip_1":"clé {0} ip {1}","py.presence.cle_privee_tls":"clé privée TLS","py.presence.commande_inconnue_0_tape_aide":"commande inconnue : {0} (tape « aide »)","py.presence.commandes_tape_les_ici_puis_entree":"commandes (tape-les ici, puis Entrée) :\n  liste                           visiteurs connectés (n°, nom, rôle, salon, durée, IP)\n  ejecter <n°|nom> [raison]       déconnecte le visiteur (il peut revenir)\n  bannir <n°|nom> [minutes] [raison]   éjecte et interdit sa clé et son IP (IPv6 : son préfixe /64 ; défaut 60 min ; 0 = définitif)\n  bans                            bannissements en cours\n  debannir <n° de bans>           lève un bannissement\n  rooms                           salons connus : connectés, visites, clé (casse exacte)\n  visits-key <salon> [off]        clé du journal des visites d'un salon (nouvelle clé, ou off pour la retirer ; seul : liste)\n  creators                        créateurs (fichier --creators relu) : préfixe, état, salons ouverts, promeneurs, origines\n  oublier <pseudo>                libère un pseudo réservé (son propriétaire le perd ; le premier qui le demande l'obtient)\n  pseudos [filtre]                liste les pseudos réservés (code #XXXX du propriétaire, dernière venue, expiration)\n  version                         numéro de version et révision de ce fichier\n  aide                            ce message\n  (un nom contenant des espaces : utilise le n° de « liste »)","py.presence.comportement_inapproprie":"comportement inapproprié","py.presence.connexions_simultanees_par_adresse_ip":"connexions simultanées par adresse IP (IPv6 : par préfixe /64)","py.presence.debut":"début","py.presence.deconnexion":"déconnexion","py.presence.definitif":"définitif","py.presence.delai_mini_entre_deux_messages_d":"délai mini entre deux messages d'un visiteur (s)","py.presence.derniers_messages_rejoues_aux_nouveaux_arriv":"derniers messages rejoués aux nouveaux arrivants (défaut 200 ; 0 = aucun) ; les plus anciens se demandent par paquets de 50 (message history)","py.presence.derriere_un_reverse_proxy_en_tete":"derrière un reverse proxy : en-tête portant l'IP réelle du visiteur (ex. X-Forwarded-For, CF-Connecting-IP) ; à n'activer que si le serveur n'est joignable que par ce proxy","py.presence.duree_0_min_1_02d_s":"durée {0} min {1:02d} s","py.presence.ejecte_par_l_hote":"éjecté par l'hôte","py.presence.erreur_de_commande_0":"[erreur de commande] {0}","py.presence.ev.ban":"bannissement","py.presence.ev.connect":"connexion","py.presence.ev.end":"fin","py.presence.ev.kick":"éjection","py.presence.ev.name":"nom","py.presence.ev.refuse":"refus","py.presence.ev.empty":"vide","py.presence.ev.http":"requête http","py.presence.empty":"connexion ouverte puis fermée sans requête ({0} depuis la dernière ligne de cette adresse ; préconnexion d'un navigateur, test de port ou robot : sans danger)","py.presence.http":"GET {1}, hôte {2}, agent {3} : ce n'est pas une ouverture de WebSocket ({4}) ({0} depuis la dernière ligne de cette adresse ; navigateur qui ouvre l'adresse du serveur, robot ou test : sans danger)","py.presence.ev.raw":"requête illisible","py.presence.raw":"{1}, début « {2} » ({0} depuis la dernière ligne de cette adresse ; robot qui sonde le port : sans danger)","py.presence.rawkind.misc":"ce n'est pas une requête HTTP","py.presence.rawkind.rdp":"sondage du Bureau à distance Windows (RDP)","py.presence.rawkind.tls":"connexion chiffrée (https) sur un port sans chiffrement","py.presence.ev.walk":"promenade","py.presence.fichier_de_bannissements_illisible_0_ignore":"[!] fichier de bannissements illisible ({0}) : ignoré","py.presence.fichier_de_journal_tourne_chaque_nuit":"fichier de journal (tourné chaque nuit) ; chemin relatif = dossier du script","py.presence.fichier_des_bannissements_chemin_relatif_dos":"fichier des bannissements ; chemin relatif = dossier du script","py.presence.help.host":"adresse d'écoute (0.0.0.0 = toutes les interfaces ; 127.0.0.1 = cette machine seulement)","py.presence.help.maxtotal":"connexions simultanées au total, tous salons confondus","py.presence.help.port":"port d'écoute des visiteurs","py.presence.history_days":"jours de messages relus et conservés dans --history-file au démarrage (défaut 30 ; 0 = tout conserver)","py.presence.history_file":"fichier d'historique du chat (une ligne JSON par message : heure, pseudo, texte, salon ; jamais l'adresse IP) : relu au démarrage pour garder l'historique entre deux relances ; désactivé par défaut. Ce sont des données personnelles","py.presence.history_loaded":"historique : {0} message(s) relu(s), {1} ignoré(s) ou trop ancien(s) ({2})","py.presence.history_write_error":"historique : écriture impossible ({0})","py.presence.jours_de_journal_conserves":"jours de journal conservés","py.presence.leve":"levé","py.presence.limite_de_connexions_par_ip":"limite de connexions par IP","py.presence.list_line":"  n°{0:<4} {1:<26} {2:<10} salon={3:<16} {4} min {5:02d} s   ip {6}","py.presence.log_line":"{0:<11} | salon={1} | {2}","py.presence.longueur_max_d_un_message_de":"longueur max d'un message de chat","py.presence.messages_max_par_fenetre_de_10":"messages max par fenêtre de 10 s et par visiteur","py.presence.moderation_tape_aide_pour_la_liste":"modération : tape « aide » pour la liste des commandes (liste, ejecter, bannir, bans, debannir, oublier, pseudos, rooms, visits-key, creators, version)","py.presence.nobody":"(personne)","py.presence.noms_interdits_a_la_reservation_separes":"noms interdits à la réservation, séparés par des virgules (ex. admin,moderateur)","py.presence.old_name":"ancien : {0}","py.presence.origines_autorisees_separees_par_des_virgule":"origines autorisées, séparées par des virgules (défaut : toutes)","py.presence.personne_ne_correspond_a_0_tape":"personne ne correspond à « {0} » (tape « liste »)","py.presence.plusieurs_visiteurs_correspondent_utilise_le":"plusieurs visiteurs correspondent, utilise le n° :","py.presence.promeneur_0_dans_le_salon":"promeneur ({0} dans le salon)","py.presence.promeneurs_max_par_salon":"promeneurs max par salon","py.presence.registre_des_noms_reserves_vide_en":"registre des noms réservés (vide = en mémoire seulement) ; chemin relatif = dossier du script","py.presence.registre_illisible_0_demarrage_a_vide":"[!] registre illisible ({0}) : démarrage à vide","py.presence.role.spectator":"spectateur","py.presence.role.walker":"promeneur","py.presence.salon_plein":"salon plein","py.presence.serveur_adresse_a_donner_a_presence":"serveur | adresse à donner à --presence-url : {0}://{1}:{2}","py.presence.serveur_adresses_a_donner_a_presence":"serveur | adresses à donner à --presence-url : {0}://127.0.0.1:{1} (cette machine)","py.presence.serveur_de_presence_glb2html_websocket":"presence_server.py {0} : serveur de présence glb2html (WebSocket) : visiteurs, chat, modération.","py.presence.serveur_journal_0_registre_des_noms":"serveur | journal : {0} | registre des noms : {1}","py.presence.serveur_n_utilise_jamais_0_0":"serveur | n'utilise jamais 0.0.0.0 dans --presence-url : c'est une adresse d'écoute, pas une destination","py.presence.star_hint":"serveur | ou {0}://*:{1} : le même nom que la page qui se connecte (conseillé si tes pages sont ouvertes par plusieurs adresses : localhost, réseau, nom public)","py.presence.serveur_presence_server_0_ecoute_sur":"serveur | presence_server {0} | écoute sur {1}:{2}  (Ctrl+C pour arrêter)","py.presence.spectateurs_vue_globale_max_tous_salons":"spectateurs (vue globale) max, tous salons","py.presence.spectator_paren":"(spectateur)","py.presence.trop_de_messages_patiente_quelques_secondes":"Trop de messages, patiente quelques secondes.","py.presence.trop_de_spectateurs":"trop de spectateurs","py.presence.un_nom_non_utilise_depuis_ce":"un nom non utilisé depuis ce nombre de jours est libéré","py.presence.until_date":"jusqu’au {0}","py.presence.usage_ban":"usage : bannir <n°|nom> [minutes] [raison]","py.presence.usage_kick":"usage : ejecter <n°|nom> [raison]","py.presence.usage_unban":"usage : debannir <n° de « bans »>","py.presence.ev.forget":"pseudo libéré","py.presence.forget_done":"pseudo « {0} » libéré : le premier navigateur qui le demandera l'obtiendra","py.presence.forget_logged":"ancien propriétaire #{0}","py.presence.forget_none":"aucun pseudo réservé ne correspond à « {0} »","py.presence.forget_online":"(son ancien propriétaire est connecté : son nom affiché ne change pas avant sa prochaine connexion)","py.presence.usage_forget":"usage : oublier <pseudo>   (le pseudo comme tu veux : casse, accents et espaces sans importance)","py.presence.names_head":"pseudos réservés ({0}) :","py.presence.names_line":"  {0} #{1}  dernière venue {2}, libre le {3} si inutilisé{4}","py.presence.names_none":"(aucun pseudo réservé)","py.presence.names_online":"(connecté)","py.presence.zone":"zone","py.stats.0_16_mediane_1_1f_90":"{0:>16} : médiane {1:,.1f} | 90 % des blocs sous {2:,.1f} | maximum {3:,.1f}","py.stats.attention_geometrie_compressee_0_les_mo":"Attention : géométrie compressée ({0}) : les Mo de géométrie ci-dessus sont la taille décodée, pas celle du fichier.","py.stats.aucun_mesh_positionnable_accessors_sans_min":"Aucun mesh positionnable (accessors sans min/max ?).","py.stats.bloc_0_1_2_1f_mo":"  bloc {0},{1} : {2:.1f} Mo de géométrie, {3} triangles, {4} instances, {5:.1f} Mo de textures","py.stats.blocs_de_0_0f_m_1":"== Blocs de {0:.0f} m : {1} non vides (centre des instances ; géométrie et textures sans doublon dans le bloc) ==","py.stats.ce_fichier_n_est_pas_un":"Ce fichier n'est pas un GLB.","py.stats.cote_des_blocs_en_metres_defaut":"côté des blocs en mètres (défaut 256)","py.stats.cout_de_la_reutilisation_entre_blocs":"== Coût de la réutilisation entre blocs ==","py.stats.desc":"glb-stats.py : analyse rapide d'un GLB, quelle que soit sa taille. Lit uniquement l'en-tête JSON (jamais les données binaires ni les textures) : quelques secondes et très peu de mémoire.","py.stats.ecrit_aussi_le_rapport_dans_ce":"écrit aussi le rapport dans ce fichier (UTF-8)","py.stats.etendue":"== Étendue ==","py.stats.fichier_0_1_1f_mo_en":"Fichier : {0} ({1:,.1f} Mo ; en-tête JSON lu : {2:,.1f} Mo)","py.stats.geometrie_accessors_uniques_0_1f_mo":"Géométrie (accessors uniques) : {0:,.1f} Mo | Textures embarquées : {1:,.1f} Mo | Reste : {2:,.1f} Mo","py.stats.geometrie_mo":"géométrie (Mo)","py.stats.geometrie_utilisee_par_plusieurs_blocs_0":"Géométrie utilisée par plusieurs blocs : {0:,.1f} Mo ({1:.0f} % du total) | textures utilisées par plusieurs blocs : {2:,.1f} Mo ({3:.0f} % du total) : taille d'une bibliothèque commune chargée une fois.","py.stats.help.glb":"fichier .glb à analyser","py.stats.le_premier_bloc_du_glb_n":"Le premier bloc du GLB n'est pas du JSON.","py.stats.les_5_blocs_les_plus_lourds":"Les 5 blocs les plus lourds en géométrie :","py.stats.meshes_reutilises_plusieurs_fois_0_materiaux":"Meshes réutilisés plusieurs fois : {0} | matériaux : {1} | textures (images) : {2} (utilisées : {3})","py.stats.nud_0_1_2_0f_m":"  - nœud {0} « {1} » : {2:.0f} m, {3} mesh(es)","py.stats.nuds_parcourus_0_meshes_1_utilises":"Nœuds parcourus : {0} | meshes : {1} (utilisés : {2}) | instances de meshes : {3}","py.stats.objets_racine_0_plus_grands_qu":"Objets racine : {0} | plus grands qu'un bloc de {1:.0f} m : {2}","py.stats.poids_estime_octets_lus_dans_l":"== Poids estimé (octets lus dans l'en-tête, sans décoder) ==","py.stats.somme_des_blocs_geometrie_0_1f":"Somme des blocs : géométrie {0:,.1f} Mo (contre {1:,.1f} Mo sans doublon dans tout le fichier) : écart = surcoût si les meshes partagés sont dupliqués dans chaque bloc.","py.stats.sommets_uniques_0_sommets_rendus_instances":"Sommets uniques : {0:,} | sommets rendus (instances comprises) : {1:,} | triangles rendus : {2:,}","py.stats.taux_de_reutilisation_sommets_rendus_uniques":"Taux de réutilisation (sommets rendus / uniques) : {0:.1f}","py.stats.x_0_1f_a_1_1f":"X : {0:.1f} à {1:.1f} ({2:.0f} m) | Z : {3:.1f} à {4:.1f} ({5:.0f} m) | hauteur Y : {6:.1f} à {7:.1f}","py.presence.help.visits":"fichier du journal des visites (une ligne JSON par visite, sans IP ; vide = pas de journal ; chemin relatif au dossier du script)","py.presence.help.visits_days":"jours de visites conservés dans ce journal (0 = tous)","py.presence.help.visits_names":"note aussi le pseudo des promeneurs dans le journal des visites","py.presence.help.visits_keys":"fichier des clés d'accès au journal des visites (empreintes seulement, chemin relatif au dossier du script)","py.presence.ev.visits":"visites","py.presence.visits.rate":"trop d'essais de clé","py.presence.visits.badkey":"clé refusée","py.presence.visits.granted":"résumé envoyé","py.presence.visits.yes":"oui","py.presence.visits.no":"non","py.presence.visits_on":"serveur : journal des visites {0} (conservé {1} jours, 0 = tous ; pseudos : {2})","py.presence.map_names_on":"serveur : les pseudos sont donnés aux cartes qui présentent la clé --map-names-key (5 clés refusées par minute et par adresse au plus)","py.presence.help.map_names_key":"donne le pseudo des promeneurs et des visiteurs en vue globale aux cartes ouvertes avec cette clé (carte.html#pseudos=CLÉ ; 8 caractères au moins)","py.presence.map_key_short":"--map-names-key : la clé doit avoir {0} caractères au moins","py.presence.map_names_old":"--map-names n'existe plus : les pseudos de la carte sont protégés par une clé (--map-names-key SECRET) ; aucun pseudo n'est donné","py.presence.ev.mapnames":"pseudos de la carte","py.presence.visits_write_err":"journal des visites {0} : écriture impossible ({1})","py.presence.vkey.unreadable":"fichier des clés de visites illisible : {0} (démarrage sans clé)","py.presence.help.creators":"fichier des créateurs autorisés (origines de leurs pages, préfixe de salon, limites ; relu à chaud, chemin relatif au dossier du script) ; absent : tout le monde est accepté","py.presence.cr.bad":"créateurs : entrée {0} ignorée (id manquant ou invalide : lettres, chiffres, - et _, 32 au plus)","py.presence.cr.badprefix":"créateurs : entrée {0} ignorée (préfixe {1} invalide : lettres, chiffres, espace, - et _, sans point)","py.presence.cr.dup":"créateurs : entrée {0} ignorée ({1} déjà utilisé par une entrée précédente)","py.presence.cr.nulljson":"créateurs : {0} : origine null écrite sans guillemets, ignorée (écrire \"null\" entre guillemets pour une page ouverte depuis le disque)","py.presence.cr.origindup":"créateurs : l'origine {0} appartient déjà à {1}, ignorée pour {2}","py.presence.cr.missing":"fichier des créateurs absent : {0} ; toute connexion est refusée tant qu'il n'existe pas","py.presence.cr.unreadable":"fichier des créateurs illisible : {0} ({1}) ; liste précédente gardée","py.presence.cr.loaded":"créateurs : {0} lus dans {1}","py.presence.cr.on":"serveur : créateurs {0} ({1}) ; une page d'une autre origine est refusée","py.presence.cr.off":"aucun fichier de créateurs (lance le serveur avec --creators FICHIER) : toutes les pages sont acceptées","py.presence.cr.none":"aucun créateur valide dans {0} : toute connexion est refusée","py.presence.cr.line":"  {0:<16} préfixe : {1}   {2}   salons ouverts : {3}{4}   promeneurs : {5}{6}","py.presence.cr.noprefix":"(aucun : tous les autres salons)","py.presence.cr.active":"actif","py.presence.cr.suspended":"suspendu","py.presence.cr.max":" / {0} au plus","py.presence.cr.origins":"      origines : {0}","py.presence.cr.noorigin":"(aucune)","py.presence.cr.refuse.origin":"origine non déclarée : {0}","py.presence.cr.refuse.off":"créateur {0} suspendu","py.presence.cr.refuse.room":"salon {0} hors des salons de {1}","py.presence.cr.refuse.rooms":"{0} : déjà {1} salons ouverts","py.presence.vkey.none":"aucune clé de journal des visites","py.presence.vkey.line":"  salon « {0} » : clé créée le {1}","py.presence.vkey.unknown":"aucune clé pour le salon « {0} »","py.presence.vkey.off":"clé du salon « {0} » retirée","py.presence.vkey.new":"clé du journal des visites du salon « {0} » : {1}\n  (affichée une seule fois ; donne-la au créateur avec l'adresse de sa page suivie de #visits ; l'ancienne clé ne marche plus)","py.presence.vkey.inactive":"attention : le journal des visites est inactif (lance le serveur avec --visits FICHIER)","py.presence.vkey.case":"attention : aucune visite ni aucun visiteur pour le salon « {0} » ; salon connu avec une autre casse : {1}. La casse compte : refais visits-key avec le nom exact (cette clé reste valable pour « {0} »).","py.presence.rooms.none":"aucun salon connu (ni visiteur connecté, ni visite enregistrée, ni clé)","py.presence.rooms.line":"  {0:<24} connectés : {1} ({2} en promenade)   visites : {3}{4}   clé : {5}","py.presence.rooms.last":", dernière le {0}","py.presence.rooms.novisits":"  (journal des visites inactif : lance le serveur avec --visits FICHIER pour compter les visites)","py.presence.rooms.note":"  (casse exacte ; un salon jamais visité et sans clé n'apparaît pas : son nom est la valeur room de NOM.config.json, par défaut le nom de la page)"}}''')


def _load():
    if I18N_DATA is not None:
        return I18N_DATA
    here = _pl.Path(__file__).resolve().parent
    for d in (here / "i18n", here.parent / "src" / "i18n"):
        if d.is_dir():
            return {p.stem: _json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json"))}
    return {}


_DATA = _load()
I18N_CODES = sorted(_DATA)


def _match(tag):
    c = str(tag or "").lower().replace("-", "_").split("_")[0]
    return c if c in _DATA else None


def i18n_system_lang():
    """langue du système (variables d'environnement, locale Python, langue d'interface de Windows) ; None si inconnue"""
    for v in ("LC_ALL", "LC_MESSAGES", "LANGUAGE", "LANG"):
        c = _match(_os.environ.get(v, "").split(":")[0])
        if c:
            return c
    try:
        c = _match((_locale.getlocale()[0] or ""))
        if c:
            return c
    except Exception:
        pass
    try:
        import ctypes
        lid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        c = _match(_locale.windows_locale.get(lid, ""))
        if c:
            return c
    except Exception:
        pass
    return None


def i18n_detect_lang(argv=None):
    """--lang CODE ou --lang=CODE dans argv, sinon WEB3D_LANG, sinon la langue du système, sinon l'anglais ('auto' = laisser le système décider)"""
    argv = list(_sys.argv[1:] if argv is None else argv)
    want = None
    for i, a in enumerate(argv):
        if a == "--lang" and i + 1 < len(argv):
            want = argv[i + 1]
        elif a.startswith("--lang="):
            want = a.split("=", 1)[1]
    for cand in (want, _os.environ.get("WEB3D_LANG")):
        if cand and cand.lower() != "auto" and _match(cand):
            return _match(cand)
    return i18n_system_lang() or ("en" if "en" in _DATA else (I18N_CODES[0] if I18N_CODES else "en"))


I18N_LANG = i18n_detect_lang()


def i18n_set_lang(code):
    global I18N_LANG
    I18N_LANG = _match(code) or I18N_LANG


def _tr(key, *a):
    """texte de la clé dans la langue courante (anglais, français, clé en repli) ; avec des arguments : str.format"""
    s = None
    for lg in (I18N_LANG, "en", "fr"):
        v = _DATA.get(lg, {}).get(key)
        if isinstance(v, str):
            s = v
            break
    if s is None:
        s = key
    return s.format(*a) if a else s


def i18n_lang_help():
    """texte d'aide de l'option --lang (codes disponibles)"""
    return _tr("py.common.lang_help", ", ".join(I18N_CODES))


def i18n_add_common(ap):
    """ajoute -h/--help traduit et --lang à un parseur créé avec add_help=False ; titres des groupes traduits"""
    ap.add_argument("-h", "--help", action="help", help=_tr("py.common.help"))
    ap.add_argument("--lang", default="auto", metavar="CODE", help=i18n_lang_help())
    try:
        ap._positionals.title = _tr("py.common.positionals")
        ap._optionals.title = _tr("py.common.optionals")
    except Exception:
        pass


# <<DEFAULTS>>
ROTATE = 0
HOLE_RADIUS = 180.0
HOLE_FADE = 60.0
HOLE_X = 0.0
HOLE_Z = 0.0
WAVE_AMP = 0.5
SEA_Y = -50.0
ZOOM_RATIO = 1.0
CAM_DIR = (0.0, 0.25, 1.0)
TARGET = (0.0, 15.0, 0.0)
SEA_ENABLED = True
ANIM_ENABLED = False
RETINA_ENABLED = False
LIGHT_ENABLED = False
FOLIAGE_CUTOUT = 0.12
SEA_COLOR = 0x3A9AD9
SKY_COLOR = 0x87CEEB
SEA_SEGMENTS = 400
WALK_ENABLED = True
EYE_HEIGHT = 1.7
WALK_SPEED = 3.5
WALK_IGNORE = "door, porte"
SOLID_MATERIALS = ""
NAMES_ENABLED = False
PRESENCE_URL = ""
ROOM = ""
CHAT_ENABLED = True
CHAT_FADE = 0.0
PROFILE = "public"
ZONES_JSON = "[]"
SPECTATE = None
PANEL = True
ZONES_LIVE = ""
MAP_JSON = "[]"
MAP_URL = ""
ZONE_MARKER = "dot"
SHOW_SPAWNS = False
ZONE_CONE = True
FLY_ENABLED = True
ZONE_INFO_DIST = 150.0
COMPASS = True
NORTH_DEG = 0.0
TARGET_EXPLICIT = False
# <</DEFAULTS>>

SEA_SIZE = 4000
TILE_RADIUS = 150.0         # m : charger les tuiles dont la boîte est à moins de ce rayon de l'avatar (plan X,Z)
TILE_MARGIN = 60.0          # m : décharger au-delà de rayon + marge (hystérésis)
TILE_MAX_MO = 200.0         # Mo de tuiles chargées en même temps
TILE_MAX_TRI = 8000000      # triangles de tuiles chargées en même temps
TILE_CONCURRENCY = 4        # téléchargements simultanés

THREE_VERSION = "0.160.0"
CDN = f"https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/"
CACHE_DIR = pathlib.Path.home() / ".cache" / "glb2html" / f"three@{THREE_VERSION}"

CORE_FILES = {
    "three": "build/three.module.js",
    "three/addons/controls/OrbitControls.js": "examples/jsm/controls/OrbitControls.js",
    "three/addons/loaders/GLTFLoader.js": "examples/jsm/loaders/GLTFLoader.js",
    "three/addons/utils/BufferGeometryUtils.js": "examples/jsm/utils/BufferGeometryUtils.js",
}
DRACO_FILES = {"three/addons/loaders/DRACOLoader.js": "examples/jsm/loaders/DRACOLoader.js"}
DRACO_LIBS = {
    "draco_wasm_wrapper.js": "examples/jsm/libs/draco/gltf/draco_wasm_wrapper.js",
    "draco_decoder.wasm": "examples/jsm/libs/draco/gltf/draco_decoder.wasm",
}
MESHOPT_FILES = {"three/addons/libs/meshopt_decoder.module.js": "examples/jsm/libs/meshopt_decoder.module.js"}


ZONE_TYPES = ("url", "ha", "portal", "spawn", "image")
IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".bmp")
MEDIA_DIR = "medias"   # sous-dossier des medias de la region (cle mediaDir de la config cote page ; ici toujours « medias »)
IMG_DIR = [None]   # dossier ou se cherchent les images des zones « image » (celui de la page), pose par main() ; None : aucune recherche
_IMG_SEEN = set()


def resolve_image_name(t):
    """« 12 » (sans extension, sans chemin ni adresse) -> « 12-Titre.jpg » ou « 12.png » d'apres les fichiers du dossier de la page (premier par ordre alphabetique) ;
    sinon le texte tel quel. Une page hebergee ne peut pas lister un dossier : c'est donc le generateur qui ecrit le vrai nom."""
    s = str(t or "").strip()
    if not s or IMG_DIR[0] is None or re.search(r"[\\/:]", s) or re.search(r"\.[A-Za-z0-9]{2,5}$", s):
        return t
    low = s.lower()
    hits = []
    for d in (IMG_DIR[0] / MEDIA_DIR, IMG_DIR[0]):   # le sous-dossier des medias d'abord, puis le dossier de la page
        try:
            names = [p.name for p in d.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXTS]
        except OSError:
            continue
        hits = sorted((n for n in names if pathlib.Path(n).stem.lower() == low or pathlib.Path(n).stem.lower().startswith(low + "-")), key=lambda n: (n.lower(), n))
        if hits:
            break
    plain = [n for n in hits if pathlib.Path(n).stem.lower() == low]
    if plain:   # « 12.png » existe : la page le trouve toute seule (extensions essayees dans l'ordre), le nom reste « 12 »
        if s not in _IMG_SEEN:
            _IMG_SEEN.add(s)
            print(_tr("py.glb2html.image_nombre", s, plain[0]))
        return t
    if s not in _IMG_SEEN:
        _IMG_SEEN.add(s)
        if not hits:
            print(_tr("py.glb2html.image_sans_fichier", s, IMG_DIR[0]))
        elif len(hits) > 1:
            print(_tr("py.glb2html.image_plusieurs", s, hits[0], len(hits)))
        else:
            print(_tr("py.glb2html.image_completee", s, hits[0]))
    return hits[0] if hits else t
ZONE_MARKERS = ("dot", "range", "none")
# v43 : anciennes valeurs (avant v43), toujours acceptées et converties
ZONE_MARKER_OLD = {"discret": "dot", "portee": "range", "aucun": "none"}
# v43 : profil « perso » renommé « private » (ancienne valeur acceptée et convertie)
PROFILE_OLD = {"perso": "private"}
# v43 : anciens noms d'options (avant la v43), toujours acceptés : remplacés avant la lecture de la ligne de commande
OLD_OPTIONS = {"--maj": "--update", "--tile-max-mo": "--tile-max-mb", "--tile-max-tri": "--tile-max-triangles"}


def old_options(argv):
    """Remplace les anciens noms d'options par les nouveaux (« --nom=valeur » compris)."""
    out = []
    for x in argv:
        k, eq, v = str(x).partition("=")
        out.append(OLD_OPTIONS.get(k, k) + eq + v if k.startswith("--") else x)
    return out


def _slug(s):
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9_-]+", "-", str(s or "").lower()))[:40]


def clean_zones(zones, profile):
    """Valide les zones ; le profil 'public' retire toutes les zones privées (leurs adresses ne sont jamais écrites dans la page)."""
    def num(v, d, lo, hi):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return d
        return d if not math.isfinite(v) else min(hi, max(lo, v))
    out = []
    for i, z in enumerate(zones if isinstance(zones, list) else []):
        if not isinstance(z, dict):
            continue
        if z.get("private") and profile not in ("private", "perso"):
            continue
        t = z.get("type") if z.get("type") in ZONE_TYPES else "portal"
        img = t == "image"   # image : tableau plaque sur un mur ; h = 0 : hauteur d'apres le rapport de l'image
        d = {
            "id": _slug(z.get("id")) or f"z{i + 1}", "type": t, "label": str(z.get("label") or "")[:60],
            "x": num(z.get("x"), 0, -1e5, 1e5), "y": num(z.get("y"), 0, -1e5, 1e5), "z": num(z.get("z"), 0, -1e5, 1e5),
            "yaw": num(z.get("yaw"), 0, -7, 7), "shape": "board" if z.get("shape") == "board" else "ring",
            "trigger": (z.get("trigger") if z.get("trigger") in ("click", "enter", "both") else "click") if t == "portal" else "click",
            "radius": num(z.get("radius"), 2, 0.5, 50), "w": num(z.get("w"), 1.2 if img else 2.4, 0.1 if img else 0.5, 10), "h": num(z.get("h"), 0, 0, 6) if img else num(z.get("h"), 1.2, 0.3, 6),
            "target": str(resolve_image_name(z.get("target")) if img else (z.get("target") or ""))[:600], "spawn": _slug(z.get("spawn")),
            "confirm": bool(z.get("confirm")), "private": bool(z.get("private")), "showName": bool(z.get("showName")),
            "mesh": "" if t in ("spawn", "image") else re.sub(r"[\x00-\x1f]", "", str(z.get("mesh") or ""))[:200],
        }
        if img:   # lien facultatif d'un tableau (page ouverte au clic ou a E) : ecrit seulement s'il est rempli, comme core.js
            lk = re.sub(r"[\x00-\x1f]", "", str(z.get("link") or "")).strip()[:600]
            if lk:
                d["link"] = lk
        out.append(d)
    return out


def clean_rotate(v):
    """Rotation de la région : 0, 90, 180 ou 270 degrés (autre valeur : arrondie au quart de tour le plus proche), comme core.js."""
    try:
        return (round(float(v) / 90) * 90) % 360
    except (TypeError, ValueError, OverflowError):
        return 0


def resolve_mesh_ref(names, ref):
    """Indices (dans `names`, noms des objets du modèle dans l'ordre de parcours de three.js : pré-ordre, enfants dans l'ordre du fichier)
    désignés par le champ `mesh` d'une zone. Même règle que resolveMeshRef de core.js : le nom exact d'abord (zones anciennes, nom unique),
    sinon « base#index » = index-ième objet nommé « base ». Liste vide si introuvable."""
    if not ref:
        return []
    exact = [i for i, n in enumerate(names) if n == ref]
    if exact:
        return exact
    m = re.fullmatch(r"(.*)#(\d+)", ref, re.S)
    if not m:
        return []
    same = [i for i, n in enumerate(names) if n == m.group(1)]
    k = int(m.group(2))
    return [same[k]] if k < len(same) else []


def fix_presence_url(u):
    u = str(u or "").strip()
    if not u:
        return u
    if not re.match(r"^wss?://", u, re.I):
        print(_tr("py.glb2html.avertissement_presence_url_doit_commencer_pa", u), file=sys.stderr)
        return u
    fixed = re.sub(r"^(wss?://)(0\.0\.0\.0)(?=[:/]|$)", r"\g<1>127.0.0.1", u, flags=re.I)
    if fixed != u:
        print(_tr("py.glb2html.avertissement_0_0_0_0_est", fixed), file=sys.stderr)
    return fixed


def map_regions(data):
    """Contenu d'un fichier de carte (v47) : liste simple, ou objet {"showUrl": ..., "regions": [...]} ; toujours la liste des régions."""
    if isinstance(data, dict):
        data = data.get("regions")
    return data if isinstance(data, list) else []


def clean_map(entries):
    """Valide les régions de la carte des mondes (adresses http/https ou relatives uniquement, vignettes d'image uniquement)."""
    def ival(v, lo=-1000000, hi=1000000):
        try:
            return max(lo, min(hi, int(float(v))))
        except (TypeError, ValueError):
            return 0
    def okurl(u):
        u = str(u or "").strip()[:600]
        return u if u and (re.match(r"^https?://", u, re.I) or not re.match(r"^[a-z][a-z0-9+.\-]*:", u, re.I)) else ""
    out, seen = [], set()
    for i, r in enumerate(map_regions(entries)):
        if not isinstance(r, dict):
            continue
        name = str(r.get("name") or "").strip()[:60]
        url = okurl(r.get("url"))
        if not name or not url:
            continue
        thumb = str(r.get("thumb") or "")
        if re.match(r"^data:image/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+$", thumb):
            thumb = thumb if len(thumb) <= 200000 else ""
        else:
            thumb = okurl(thumb) if thumb and not thumb.startswith("data:") else ""
        rid = _slug(r.get("id") or name) or f"r{i + 1}"
        while rid in seen:
            rid += "-2"
        seen.add(rid)
        out.append({"id": rid, "name": name, "url": url, "x": ival(r.get("x")), "y": ival(r.get("y")),
                    "spawn": _slug(r.get("spawn")), "presence": (str(r.get("presence"))[:300] if re.match(r"^wss?://", str(r.get("presence") or ""), re.I) else ""), "room": re.sub(r"[^\w .\-]", "", str(r.get("room") or "")).strip()[:64], "thumb": thumb})
    return out


def find_beside(path):
    """Chemin absolu : tel quel. Relatif : d'abord le dossier de lancement, puis le dossier de ce script."""
    path = pathlib.Path(path).expanduser()
    if path.is_absolute():
        return path if path.is_file() else None
    for base in (pathlib.Path.cwd(), pathlib.Path(__file__).resolve().parent):
        if (base / path).is_file():
            return base / path
    return None


MAP_PAGE_TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<link rel="icon" id="siteIcon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2064%2064'%3E%3Crect%20width='64'%20height='64'%20rx='12'%20fill='%230b3d6e'/%3E%3Ctext%20x='32'%20y='45'%20font-family='Arial%2CHelvetica%2Csans-serif'%20font-size='34'%20font-weight='700'%20text-anchor='middle'%20fill='%23fff'%3E3D%3C/text%3E%3C/svg%3E"/>
<script>(function () { var i = new Image(); i.onload = function () { var l = document.getElementById("siteIcon"); l.type = "image/x-icon"; l.href = "favicon.ico"; }; i.src = "favicon.ico"; })();</script>
<title>__TITLE__</title>
<style>
[hidden]{display:none!important}
body{margin:0;background:#fff;color:#000;font:14px/1.5 ui-monospace,Consolas,monospace}
main{max-width:1000px;margin:0 auto;padding:20px}
h1{font-size:20px;margin:0 0 4px}
#grid{display:grid;gap:12px;justify-content:start;margin:16px 0}
.tile{box-sizing:border-box;display:flex;flex-direction:column;gap:4px;width:170px;padding:6px;border:2px solid #000;border-radius:8px;background:#fff;color:#000;text-decoration:none}
a.tile:hover{background:#eee}
.tile img,.tile .ph{width:100%;aspect-ratio:1;object-fit:cover;background:#ccc;border:1px solid #000;display:block}
.tile b{word-break:break-word}
.cell{display:flex;flex-direction:column;gap:4px;width:170px}
.cell small{font-size:11px;word-break:break-all;opacity:.8}
footer{font-size:11px;opacity:.7}
#who{margin:8px 0}
#who input{font:inherit;width:200px;border:2px solid #000;border-radius:6px;padding:4px 6px}
#who label.chk{display:inline-block;margin-left:12px}
#who label.chk input{width:auto}
.tile span{font-size:12px;white-space:pre-line}
#tools{margin:8px 0}
#tools small{margin-left:8px}
#total{font-weight:bold;margin:4px 0}
.tile.arr{outline:5px dashed #000;outline-offset:2px;background:#ffe9a8;animation:arrblink .9s steps(1,end) infinite}
@keyframes arrblink{0%{outline-width:5px}50%{outline-width:0}}
.tile .arrb{font-weight:bold}
@media (prefers-reduced-motion:reduce){.tile.arr{animation:none}}
#zoom{position:fixed;z-index:60;pointer-events:none;box-sizing:border-box;padding:4px;border:2px solid #000;border-radius:6px;background:#fff;box-shadow:0 4px 16px #0007}
#zoom img{display:block;max-width:min(400px,80vw);max-height:min(400px,80vh)}
#zoom[hidden]{display:none}
</style>
</head>
<body><script>
// ===== langue de la page (v36) =====
// Les textes sont dans src/i18n/<code>.json (un fichier par langue, clés stables, texte pur) ; build.py les intègre ici.
// Ajouter une langue = ajouter un fichier src/i18n/<code>.json (voir docs/fr/MANUEL.md § 21.9) : aucun code à toucher.
// Texte manquant dans une langue : anglais, puis français, puis la clé elle-même.
const I18N = {"en":{"_name":"English","common.auto":"Auto","common.no":"no","common.yes":"yes","core.ban.until":" (until {0})","core.clickable":" · click","core.diag.browser":"Browser","core.diag.btn":"Copy diagnostics","core.diag.cfgver":"region configuration from {0}","core.diag.copied":"Diagnostics copied","core.diag.date":"Date","core.diag.errors":"Recent errors and warnings ({0}):","core.diag.failed":"Failed tiles","core.diag.gpu":"Graphics card","core.diag.gpu.v":"{0} · WebGL {1} · textures up to {2} px","core.diag.cause.none":"nothing (on-demand rendering)","core.diag.cause.peers":"other visitors","core.diag.cause.sea":"animated sea","core.diag.cause.tiles":"tiles loading","core.diag.cause.walk":"walk mode","core.diag.fps":"Frames rendered per second (5 s)","core.diag.fps.v":"{0}; continuous rendering caused by: {1}","core.diag.light":"Light rendering","core.diag.light.nolimit":"no limit","core.diag.light.v":"resolution {0}%; max frames/s: {1}; overview only: {2}; tile radius: {3}; antialiasing: {4}","core.diag.lang":"Language, browser, keyboard","core.diag.image":"Image","core.diag.image.v":"zone {0}; target \"{1}\"; file read: {2}; caption: {3}","core.diag.image.txt":"text file","core.diag.image.name":"file name","core.diag.image.hidden":"hidden","core.diag.line":"{0}: {1}","core.diag.mem":"JavaScript memory","core.diag.mem.v":"{0} MB used of {1} MB","core.diag.na":"not available in this browser","core.diag.noerror":"none","core.diag.page":"Page","core.diag.presence":"Presence","core.diag.presence.conn":"Presence connection","core.diag.presence.conn.v":"was opened: {0}, last code: {1}, reason: {2}","core.diag.render":"Rendering (last frame)","core.diag.render.v":"{0} triangles, {1} draw calls, {2} geometries, {3} textures, {4} programs","core.diag.screen":"Window","core.diag.screen.v":"{0} x {1} px, density {2}, render x{3}","core.diag.state":"Displayed status:","core.diag.tiles":"Tiles","core.diag.tiles.v":"{0} ready of {1}, {2} loading, {3} failed","core.diag.times":"Tile timings","core.diag.times.v":"first ready at {0} s, last at {1} s; per tile (median / maximum): total {2} ms, download {3} ms, parsing {4} ms","core.diag.tip":"Copies the page's technical status and its latest errors, to paste into a help request. No server address, nickname or key is copied.","core.diag.title":"Web 3d diagnostics","core.diag.uptime":"open for {0} s","core.diag.version":"Version","core.dodge.log":"occupied arrival: moved {0} m (ring {1} m)","core.joined":"{0} joined","core.kind.ha":"Command","core.kind.portal":"Portal","core.kind.spawn":"Arrival","core.kind.url":"Web link","core.left":"{0} left","core.manual":"Full manual (online)","core.ov.ignored":"overview ignored (address refused):","core.ov.unavailable":"overview “{0}” unavailable ({1}): the region works without it","core.pick.building":"object: {0}","core.pick.material":"material: {0}","core.pick.mesh":"mesh: {0}","core.pick.noname":"(no name)","core.pick.none":"(none)","core.pick.parents":"parents: {0}","core.pick.point":"point (m): {0}","core.pick.size":"size (m): {0}","core.pres.closed":"connection opened then closed (code {0}){1}","core.pres.never":"connection never established (check address, port or firewall)","core.pres.secerr":"refused by the browser (https page with ws://, or forbidden port)","core.pres.refused.origin":"this page is not declared on this presence server","core.pres.refused.off":"the creator of this page is suspended on this presence server","core.pres.refused.room":"this page's room does not belong to its creator on this server","core.pres.refused.rooms":"its creator already has all allowed rooms open","core.pres.refused.unknown":"connection refused by the server","core.private":" (private)","core.spawn.label":"arrival: {0}","core.tile.badformat":"{0}: unexpected format (no “tiles” list)","core.tile.badpath":"tile address refused “{0}” (relative path, without .., without “:”, “?” or “#”)","core.tile.budget":"tile “{0}”: this tile alone exceeds the budget (tileMaxMB / tileMaxTriangles), loaded anyway (the avatar is on it)","core.tile.fail":"tile “{0}”: failed ({1}), will retry later","core.tile.faillog":"[tile] {0}: failed after {1} ms ({2})","core.tile.ignored":"tile ignored (invalid entry in {0}):","core.tile.off":"tile mode not enabled (no tiles field in the configuration)","core.tile.ready":"[tile] {0} ready: {1} MB · {2} triangles · wait before download {3} ms · download {4} ms · GLB parsing {5} ms · wait in the grid queue {6} ms · grid construction {7} ms of work ({8} ms elapsed) · total {9} ms","core.tip.cmd":"Command: {0}","core.tip.dist":"{0} m","core.tip.region":"Region: {0}","core.tip.thisregion":"this region","core.view.fps":"first person","core.view.free":"free camera","core.view.tps":"third person","core.zone.nogeom":"zone “{0}”: element “{1}” has no geometry","core.zone.nomesh":"zone “{0}”: element “{1}” not found in the model","core.zone.norefs":"zone “{0}” ignored: linked to the element “{1}”, which these tiles cannot resolve (tiles written without object references: split again with glb2tiles v32)","map.alert":"Arrival alert (sound and marker)","map.alert.last":"last arrival: {0}, {1}","map.alert.nosound":"sound unavailable in this browser","map.alert.on":"listening (checked every {0} s)","map.alert.wait":"sound starts at the first click on the page","map.arrived":"● arrival {0}","map.badurl":"(invalid address)","map.empty":"No region in the map.","map.footer":"glb2html {0}: each card is a link that takes you straight into the region, at its arrival point.","map.needserver":"Opened from disk, this map cannot read regions.json: serve it from a web server (http or https address).","map.nofile":"Cannot read {0}: no region to show.","map.novisitor":"no visitors","map.pseudo":"My nickname: ","map.pseudo.note":"remembered in this browser; passed on to the regions you visit","map.regions.one":"{0} region","map.regions.other":"{0} regions","map.showurl":"Show addresses","map.tip":"Click to enter the region (arrival: {0})","map.title":"World map","map.total":"Total: {0}","map.visitor":"Visitor","map.visitors.one":"{0} visitor","map.visitors.other":"{0} visitors","map.mixed.one":"{0} visitor, {1} walking","map.mixed.other":"{0} visitors, {1} walking","map.and":" and ","map.other.one":"{0} other","map.other.other":"{0} others","map.viewers":"global view: {0}","map.walking.one":"{0} walker","map.walking.other":"{0} walkers","page.about.btn":"About this region","page.about.close":"Close (Esc)","page.about.hide":"Don't show again","page.about.opt":"Show the about panel on entry","page.btn.center":"Recenter the view","page.btn.center.tip":"Back to the region's opening framing (global view)","page.btn.fly":"Fly / Land","page.btn.grab":"Capture the mouse","page.btn.help":"Help (H)","page.btn.help.expand":"Expand the help (H)","page.btn.help.hide":"Hide the help (H)","page.btn.home":"Back to the arrival point (R)","page.btn.map":"Map (M)","page.btn.map.ctrl":"Map (Ctrl+M)","page.btn.walk":"Walk (P)","page.chat.connecting":"Chat: connecting…","page.chat.disabled":"Chat is not enabled on this page: regenerate it with --presence-url (and run presence_server.py)","page.chat.error":"Chat offline: retrying…","page.chat.file.head":"Chat of the region “{0}” — saved on {1}","page.chat.file.note":"Messages received or sent since you arrived (local time | name | text). Nothing is kept on the server.","page.chat.full":"Chat: room full","page.chat.help":"↵ Enter: write (the input stays open, Esc closes it)","page.chat.mentions.go":"Go to the first","page.chat.mentions.one":"{0} message mentions you","page.chat.mentions.other":"{0} messages mention you","page.chat.names":"Nicknames","page.chat.offline":"Chat offline","page.chat.offline.sys":"Chat unavailable: offline","page.chat.older":"Older messages","page.chat.placeholder":"Message: Enter to send (stays open), Esc to close","page.chat.save":"Save the chat","page.chat.save.title":"Saves to a text file the messages seen since you arrived","page.chat.saved.one":"Chat saved: {0} message","page.chat.saved.other":"Chat saved: {0} messages","page.compass.dirs":"N NE E SE S SW W NW","page.compass.label":"Heading: {0}","page.cones.off":"Portal markers hidden (T to show them)","page.cones.on":"Portal markers shown (T to hide them)","page.copy.aria":"My position","page.copy.btn":"Copy my position","page.copy.fmt.aria":"Format of the copied position","page.err.load":"Loading error: {0}","page.feat":"This page — visitor settings: {0} · presence: {1} · chat: {2} · global view: {3} · names on click: {4} · glb2html {5}","page.feat.names.no":"no (option --names)","page.feat.panel.yes":"yes (button at the top right)","page.feat.presence.no":"no (option --presence-url)","page.feat.presence.yes":"yes (room {0})","page.feat.spectate.no":"no (option --spectate)","page.goto.aria":"Go to x, y, z","page.goto.bad":"Three numbers expected: x, y, z (e.g. 68.2, 39, -823.3), or an address containing #pos=x,y,z,heading","page.goto.btn":"Go","page.goto.frame.page":"frame of this page, model recentered","page.goto.frame.tiles":"frame of the original model","page.goto.label":"Go to x, y, z (m, {0}): ","page.goto.moved":"Target moved to {0}","page.goto.tp":"Teleporting to {0}","page.ground.loading":"Loading the ground…","page.help.about":"?: about this region","page.help.alt":"Alt + drag: orbit","page.help.center":"\"Recenter the view\" button: opening framing","page.help.chat.arrows":"arrows: in the text (after Esc: move around)","page.help.chat.enter":"Enter: write","page.help.chat.esc":"Esc: close","page.help.down":"Page Down or C: go down","page.help.end":"End or Alt + click: camera behind the avatar","page.help.enter":"P or F: enter","page.help.esc":"Esc: release","page.help.fly":"Home: fly / land (or the button)","page.help.g.chat":"Chat","page.help.g.fly":"Flight","page.help.g.mouse":"Mouse","page.help.g.move":"Movement","page.help.g.orbit":"Global view","page.help.g.page":"Page","page.help.g.view":"View","page.help.g.walk":"Walk","page.help.g.zones":"Zones","page.help.grab":"G: capture / release","page.help.h":"H: help","page.help.home":"R: back to the arrival point","page.help.i":"I: information","page.help.jump":"Space: jump","page.help.l":"L: arrivals (teleport)","page.help.landing":"double-click: choose the landing point","page.help.m":"M: first / third person","page.help.map":"M: world map","page.help.map.ctrl":"Ctrl+M: world map","page.help.mouse":"G or the “Capture the mouse” button, then mouse: look around (or drag with the button held)","page.help.move":"{0} / arrow keys","page.help.o":"O: settings","page.help.orbit.drag":"drag: rotate","page.help.orbit.pan":"right-click + drag: pan","page.help.orbit.reframe":"R: center on the arrival point","page.help.orbit.wheel":"wheel: zoom","page.help.quit":"P or F: leave the walk","page.help.run":"Shift or double-tap {0} {1} ↑ ↓: run","page.help.takeoff":"Page Up held on the ground: take off","page.help.title":"Help","page.help.tp":"double-click: teleport","page.help.up":"Page Up or Space held: go up","page.help.view":"V: change view","page.help.wheel":"wheel: camera distance (third person) or zoom (free camera)","page.help.zone.click":"click or E: signs and portals","page.help.zone.click.orbit":"click: signs and portals","page.help.zone.cone":"T: portal markers","page.help.zone.name":"click: name of the element","page.home.none":"No return point on this page","page.info.title":"Information / Status","page.key.done":"Identity replaced by the link's","page.key.modal":"This personal link replaces this browser's identity (reserved name, history) with its owner's. Replace?","page.landing.chosen":"Landing point chosen: press P (or F) to land there","page.layout.bad":"This file is not a window layout","page.layout.load":"Load a layout","page.layout.loaded":"Layout loaded","page.layout.reset":"Original layout","page.layout.reset.done":"Original layout restored","page.layout.save":"Save the layout","page.layout.saved":"Layout saved: disposition.json","page.layout.title":"Window layout","page.loading":"Loading…","page.map.badurl":"Invalid address: {0}","page.map.close":"Close (Esc)","page.map.count.one":"{0} walker","page.map.count.other":"{0} walkers","page.map.empty":"No region in the map.","page.map.here":"● you are here","page.map.novisitor":"no visitors","page.map.sep":" · ","page.map.tip":"Click to enter the region (arrival: {0})","page.map.tiphere":"You are in this region (a click closes the map)","page.map.title":"World map","page.map.visitors.one":"{0} visitor","page.map.visitors.other":"{0} visitors","page.map.mixed.one":"{0} visitor, {1} walking","page.map.mixed.other":"{0} visitors, {1} walking","page.map.and":" and ","page.map.other.one":"{0} other","page.map.other.other":"{0} others","page.map.viewers":"global view: {0}","page.modal.no":"Cancel","page.modal.yes":"Yes","page.mouse.captured":"captured (G or Esc to release it)","page.mouse.free":"free (G or the “Capture the mouse” button to grab it again)","page.mouse.idle":"G or the “Capture the mouse” button to capture it (otherwise drag, button held, to look around)","page.opt.anim":"Animated sea","page.opt.blink":"Message that mentions my nickname: the author's bubble blinks","page.opt.bold":"Message that mentions my nickname: in bold, preceded by “@”","page.opt.color":"Choose my avatar's color","page.opt.color.note":"Seen at once by the other visitors.\nUnchecked: a random color is used.","page.opt.compass":"Compass (heading at the top of the screen)","page.light.aa":"Antialiasing (on next load)","page.light.ask":"Rendering without a graphics card detected. Turn on light rendering?","page.light.close":"Close","page.light.done":"Light rendering on. Fine settings: button next to the box, in Settings.","page.light.fps":"Frames per second (at most)","page.light.m":"{0} m","page.light.no":"No","page.light.nolimit":"no limit","page.light.note":"Applied at once (except antialiasing) and remembered on this device.","page.light.ovonly":"Global view: overview only (details when walking)","page.light.pct":"{0}%","page.light.preset":"Recommended values","page.light.radius":"Detailed tile radius","page.light.scale":"Render resolution","page.light.title":"Light rendering: fine settings","page.opt.light":"Light rendering","page.opt.light.fine":"Fine settings…","page.opt.histmax":"History messages kept in the chat (20 to 2000)","page.opt.lang":"Language / Langue: ","page.opt.layout":"Keyboard layout: ","page.opt.link":"Copy my personal link","page.opt.link.aria":"Personal link","page.opt.link.note":"This link is a secret: whoever opens it takes your identity (your reserved name). Do not share it.","page.opt.note":"While walking, Esc releases the mouse so you can use this panel. Your choices are remembered on this device.","page.opt.reset":"Default values","page.opt.retina":"High resolution (sharper, heavier)","page.opt.sea":"Show the sea","page.opt.sound.cite":"Beep when a message mentions my nickname","page.opt.sound.msg":"Beep for every message when the page is not focused","page.opt.sound.join":"Sound when a visitor arrives","page.opt.sound.leave":"Sound when a visitor leaves","page.opt.sounds":"Sounds","page.opt.volume":"Volume: ","page.opt.wave":"Waves: ","page.opts":"Settings","page.pick.material":"material: {0}","page.pick.noname":"(no name)","page.pick.part":"part: {0}","page.pos.invalid":"#pos= ignored: x,y,z[,yaw] expected (numbers)","page.pres.banned":"access denied","page.pres.connecting":"connecting…","page.pres.count.one":"{0} visitor online","page.pres.count.other":"{0} visitors online","page.pres.error":"server unreachable ({0}), retrying…","page.pres.error.why":"presence interrupted ({0}): {1}, retrying…","page.pres.error.stopped":"presence interrupted ({0}): {1}, attempts stopped: reload the page to try again","page.pres.refused":"presence refused: {0} (reload the page once fixed)","page.pres.full":"room full","page.pres.kicked":"removed from the room (reload the page to come back)","page.pres.nametaken":"That name is already taken: you are “{0}”","page.pres.nobody":"nobody walking","page.pres.off":"offline (P or F: connect by walking)","page.pres.toast.banned":"Access denied","page.pres.toast.kicked":"Removed by the host","page.pres.walking.one":"{0} visitor walking","page.pres.walking.other":"{0} visitors walking","page.presence.label":"Nickname: ","page.shell.badregion":"region parameter refused “{0}” (a single file name, without / \\ : ? # or .., without a leading dot)","page.shell.error":"Error: {0}","page.shell.file":"This page is in modular mode: it must be served over http or https, not opened from the disk. To test it: python -m http.server in its folder, then http://localhost:8000/{0}","page.shell.network":"network","page.shell.noregion":"No region to open (\"{0}\" not found): add ?region=NAME to the address or create a default.json file containing {\"region\": \"NAME\"}.","page.shell.notfound":"Error: {0} not found ({1})","page.spawn.done":"Teleport: {0}","page.spawn.none":"No arrival point in this region","page.spawn.tip":"List of available teleport points (TP)","page.spawn.title":"Arrivals","page.state.kb":"Keyboard: {0} ({1})","page.state.kb.auto":"Keyboard: {0} ({1}), automatic","page.state.mode":"Mode: {0}","page.state.mode.fly":"flying","page.state.mode.walk":"on foot","page.state.mouse":"Mouse: {0}","page.state.pos.avatar":"Position avatar: x {0} · y {1} · z {2} m","page.state.pos.target":"Position target (global view): x {0} · y {1} · z {2} m","page.state.run":" · running","page.state.view":"View: {0}","page.state.view.global":"global (orbit)","page.tiles.error":"Tile “{0}”: {1} (will retry later)","page.tiles.failed":"{0} failed (will retry)","page.tiles.here":"Tile(s) under the avatar: {0}","page.tiles.loading":"{0} in progress","page.tiles.main.one":"Tiles: {0} loaded / {1} · {2} MB · {3} triangles","page.tiles.main.other":"Tiles: {0} loaded / {1} · {2} MB · {3} triangles","page.tiles.ov":"Overview (counted apart): {0} MB · {1} triangles","page.tiles.ov.failed":"Overview unavailable","page.toast.copied":"Copied","page.toast.copyfail":"Copy failed: the text is selected, press Ctrl+C","page.visitor":"Visitor","page.wait.long":" · long wait (heavy tile or slow network)","page.wait.region":"Loading the region…","page.wait.secs":" · {0} s","page.wait.tiles.one":"{1}/{0} tile ready","page.wait.tiles.other":"{1}/{0} tiles ready","page.win.h.tip":"Help: keys and controls of the current view.\nH: show, expand, hide.","page.win.i.tip":"Information / Status: view, mode, position, tiles, diagnostics.\nI: show, expand, hide.","page.win.l.tip":"Arrivals: list of available teleport points (TP).\nL: show, expand, hide.","page.win.move":"Click the title: collapse or expand. Drag the title: move (dropped on a stack, bottom left or below Settings, the window docks to it; elsewhere, it stays free). Double-click the title: back to its stack.","page.win.o.tip":"Page settings and window layout.\nO: open, close.","page.zone.badcmd":"Invalid command address: {0}","page.zone.badlink":"Invalid link: {0}","page.zone.cmdfail":"Sending failed: {0}","page.zone.cmdsent":"Command sent: {0}","page.zone.confirm":"Send the command “{0}”?","page.zone.noportal":"Portal without a valid destination: {0}","page.zone.nospawn":"Arrival point “{0}” not found in this region","page.zone.opening":"Opening: {0}","page.zone.prompt":"click or E: {0}","core.image.missing":"image not found: {0}","core.webgl.missing":"3D cannot be shown: WebGL is not available in this browser.\nWhen hardware acceleration is off, recent browsers (Edge, Chrome) now refuse software rendering.\nWays out: open this page in Firefox; or start Edge with the --enable-unsafe-swiftshader option (preferably in a profile kept for these pages); or turn hardware acceleration back on.\nTo check: edge://gpu (or chrome://gpu), WebGL line.","page.status.walk":"Walking","page.status.global":"Overview","page.status.pos":"x {0}  y {1}  z {2}","page.status.target":"target x {0}  y {1}  z {2}","page.pad.label":"Movement arrows","page.pad.hold":"Hold to keep going.","page.pad.fwd":"Forward ({0} or ↑)","page.pad.back":"Back ({0} or ↓)","page.pad.left":"Turn left (←)","page.pad.right":"Turn right (→)","page.pad.side.l":"Step left ({0})","page.pad.side.r":"Step right ({0})","page.pad.run":"Run","page.pad.run.tip":"Run (Shift): one click turns it on, another turns it off","page.pad.up":"Up (Page Up)","page.pad.down":"Down (Page Down or C)","page.pad.g.fwd":"Move the view forward","page.pad.g.back":"Move the view back","page.pad.g.left":"Move the view left","page.pad.g.right":"Move the view right","page.pad.g.tl":"Turn the view left","page.pad.g.tr":"Turn the view right","page.pad.g.in":"Zoom in (wheel)","page.pad.g.out":"Zoom out (wheel)","page.btn.pad":"Arrows (K)","page.btn.pad.off":"Arrows (K): hidden","page.btn.pad.tip":"Show or hide the on-screen arrows (K)","page.btn.walk.tip":"Start walking (F or P)","page.btn.fly.tip":"Fly or land (Home)","page.btn.grab.tip":"Capture the mouse to look around (the G key captures and releases it)","page.btn.home.tip":"Go back to the arrival point (R)","page.btn.help.tip":"Help: show, expand, hide (H)","page.btn.map.tip":"World map (M; Ctrl+M while walking)","page.t.label":"Touch controls","page.t.walk":"Walk","page.t.exit":"Exit","page.t.exit.tip":"Stop walking (F)","page.t.jump":"Jump","page.t.jump.tip":"Jump (Space)","page.t.fly":"Fly","page.t.land":"Land","page.t.view":"View","page.t.view.tip":"Change view: first person, third person, free camera (V)","page.t.chat":"Chat","page.t.chat.n":"Chat ({0})","page.t.chat.tip":"Open the chat (Enter)","page.t.pad":"Arrows","page.t.menu":"Menu","page.t.menu.tip":"Help, information, arrivals, map, full screen","page.menu.help":"Help","page.menu.info":"Information","page.menu.spawn":"Arrivals","page.menu.map":"World map","page.menu.home":"Back to arrival","page.menu.center":"Recenter the view","page.menu.full":"Full screen","page.menu.fullexit":"Exit full screen","page.menu.full.fail":"The browser refuses full screen","page.menu.close":"✕ Close the menu","page.win.close":"Close this window","page.chat.send":"Send","page.chat.send.tip":"Send the message (Enter)","page.chat.close":"✕ Close","page.chat.close.tip":"Close the chat input (Esc)","page.opt.pad":"On-screen arrows (K)","page.opt.touch":"Touch controls","page.opt.touch.on":"Yes","page.opt.touch.off":"No","page.opt.zonenums":"Image zone numbers (to find them)","page.help.k":"K: movement pad (on-screen arrows)","page.touch.look":"Drag your finger on the screen to look around","page.diag.touch":"Touch controls","page.diag.touch.v":"{0} (setting: {1}; touch screen detected: {2}; touch points: {3})","page.visits.title":"Visit log","page.visits.intro":"Summary of the visits to this region, for its creator. Enter the key the presence server host gave you.","page.visits.key":"Key: ","page.visits.show":"Show","page.visits.forget":"Forget the key","page.visits.forgotten":"Key forgotten by this browser.","page.visits.csv":"Download (CSV)","page.visits.close":"Close (Esc)","page.visits.wait":"Asking the presence server…","page.visits.nopres":"This page has no presence server: no visit is recorded.","page.visits.err.empty":"Enter the key.","page.visits.err.key":"Key refused for this region.","page.visits.err.rate":"Too many attempts: try again in a minute.","page.visits.err.off":"The presence server does not record visits (--visits option).","page.visits.err.old":"The presence server is too old for the visit log (v48 or newer).","page.visits.err.net":"The presence server does not answer.","page.visits.summary":"Room \"{0}\": visits {1}, distinct visitors {2}. Visits kept {3} days.","page.visits.summary.all":"Room \"{0}\": visits {1}, distinct visitors {2}. Visits kept without limit.","page.visits.none":"No visit recorded for this region.","page.visits.days":"Per day","page.visits.recent":"Visits of the last 30 days","page.visits.recent.cut":"(the {0} most recent)","page.visits.recent.none":"No visit in the last 30 days.","page.visits.c.date":"Date","page.visits.c.visits":"Visits","page.visits.c.visitors":"Distinct visitors","page.visits.c.total":"Total duration","page.visits.c.median":"Median duration","page.visits.c.walked":"With walk","page.visits.c.start":"Arrival","page.visits.c.dur":"Duration","page.visits.c.walk":"Walk","page.visits.c.name":"Nickname","page.visits.yes":"yes","page.visits.no":"no","page.visits.d.h":"{0} h {1} min","page.visits.d.m":"{0} min {1} s","page.visits.file":"visits","page.visits.open":"Visit log…","page.visits.open.tip":"For the region's creator: summary of the visits, with the key given by the presence server host"},"fr":{"_name":"Français","common.auto":"Auto","common.no":"non","common.yes":"oui","core.ban.until":" (jusqu'au {0})","core.clickable":" · clic","core.diag.browser":"Navigateur","core.diag.btn":"Copier le diagnostic","core.diag.cfgver":"configuration de la région en {0}","core.diag.copied":"Diagnostic copié","core.diag.date":"Date","core.diag.errors":"Erreurs et avertissements récents ({0}) :","core.diag.failed":"Tuiles en échec","core.diag.gpu":"Carte graphique","core.diag.gpu.v":"{0} · WebGL {1} · textures de {2} px au plus","core.diag.cause.none":"rien (rendu à la demande)","core.diag.cause.peers":"autres visiteurs","core.diag.cause.sea":"mer animée","core.diag.cause.tiles":"tuiles en chargement","core.diag.cause.walk":"promenade","core.diag.fps":"Images rendues par seconde (5 s)","core.diag.fps.v":"{0} ; rendu continu dû à : {1}","core.diag.light":"Rendu léger","core.diag.light.nolimit":"sans limite","core.diag.light.v":"résolution {0} % ; images/s au plus : {1} ; vue d'ensemble seule : {2} ; rayon des tuiles : {3} ; anticrénelage : {4}","core.diag.lang":"Langue, navigateur, clavier","core.diag.image":"Image","core.diag.image.v":"zone {0} ; cible « {1} » ; fichier lu : {2} ; légende : {3}","core.diag.image.txt":"fichier texte","core.diag.image.name":"nom du fichier","core.diag.image.hidden":"masquée","core.diag.line":"{0} : {1}","core.diag.mem":"Mémoire JavaScript","core.diag.mem.v":"{0} Mo utilisés sur {1} Mo","core.diag.na":"non disponible dans ce navigateur","core.diag.noerror":"aucun","core.diag.page":"Page","core.diag.presence":"Présence","core.diag.presence.conn":"Connexion de présence","core.diag.presence.conn.v":"s'est ouverte : {0}, dernier code : {1}, raison : {2}","core.diag.render":"Rendu (dernière image)","core.diag.render.v":"{0} triangles, {1} appels de dessin, {2} géométries, {3} textures, {4} programmes","core.diag.screen":"Fenêtre","core.diag.screen.v":"{0} x {1} px, densité {2}, rendu x{3}","core.diag.state":"État affiché :","core.diag.tiles":"Tuiles","core.diag.tiles.v":"{0} prêtes sur {1}, {2} en cours, {3} en échec","core.diag.times":"Durées des tuiles","core.diag.times.v":"première prête à {0} s, dernière à {1} s ; par tuile (médiane / maximum) : total {2} ms, téléchargement {3} ms, analyse {4} ms","core.diag.tip":"Copie l'état technique de la page et ses dernières erreurs, à coller dans une demande d'aide. Aucune adresse de serveur, aucun pseudo ni clé n'est copié.","core.diag.title":"Diagnostic Web 3d","core.diag.uptime":"ouverte depuis {0} s","core.diag.version":"Version","core.dodge.log":"arrivée occupée : décalé de {0} m (anneau {1} m)","core.joined":"{0} a rejoint","core.kind.ha":"Commande","core.kind.portal":"Portail","core.kind.spawn":"Arrivée","core.kind.url":"Lien web","core.left":"{0} est parti","core.manual":"Manuel complet (en ligne)","core.ov.ignored":"vue d'ensemble ignorée (adresse refusée) :","core.ov.unavailable":"vue d'ensemble « {0} » indisponible ({1}) : la région fonctionne sans elle","core.pick.building":"objet : {0}","core.pick.material":"matériau : {0}","core.pick.mesh":"mesh : {0}","core.pick.noname":"(sans nom)","core.pick.none":"(aucun)","core.pick.parents":"parents : {0}","core.pick.point":"point (m) : {0}","core.pick.size":"taille (m) : {0}","core.pres.closed":"connexion ouverte puis fermée (code {0}){1}","core.pres.never":"connexion jamais établie (adresse, port ou pare-feu à vérifier)","core.pres.secerr":"refusé par le navigateur (page https avec ws://, ou port interdit)","core.pres.refused.origin":"cette page n'est pas déclarée sur ce serveur de présence","core.pres.refused.off":"le créateur de cette page est suspendu sur ce serveur de présence","core.pres.refused.room":"le salon de cette page n'appartient pas à son créateur sur ce serveur","core.pres.refused.rooms":"son créateur a déjà tous les salons permis ouverts","core.pres.refused.unknown":"connexion refusée par le serveur","core.private":" (privé)","core.spawn.label":"arrivée : {0}","core.tile.badformat":"{0} : format inattendu (liste « tiles » absente)","core.tile.badpath":"adresse de tuiles refusée « {0} » (chemin relatif, sans .., sans « : », sans « ? » ni « # »)","core.tile.budget":"tuile « {0} » : le budget (tileMaxMB / tileMaxTriangles) est dépassé par cette seule tuile, chargée quand même (l'avatar est dessus)","core.tile.fail":"tuile « {0} » : échec ({1}), nouvelle tentative plus tard","core.tile.faillog":"[tuile] {0} : échec après {1} ms ({2})","core.tile.ignored":"tuile ignorée (entrée invalide dans {0}) :","core.tile.off":"mode tuiles non activé (champ tiles absent de la configuration)","core.tile.ready":"[tuile] {0} prête : {1} Mo · {2} triangles · attente avant téléchargement {3} ms · téléchargement {4} ms · analyse du GLB {5} ms · attente en file de grille {6} ms · construction de la grille {7} ms de travail ({8} ms écoulées) · total {9} ms","core.tip.cmd":"Commande : {0}","core.tip.dist":"{0} m","core.tip.region":"Région : {0}","core.tip.thisregion":"cette région","core.view.fps":"subjective","core.view.free":"caméra libre","core.view.tps":"troisième personne","core.zone.nogeom":"zone « {0} » : élément « {1} » sans géométrie","core.zone.nomesh":"zone « {0} » : élément « {1} » introuvable dans le modèle","core.zone.norefs":"zone « {0} » ignorée : liée à l'élément « {1} », ce que ces tuiles ne savent pas résoudre (tuiles écrites sans références d'objets : redécouper avec glb2tiles v32)","map.alert":"Surveillance des arrivées (son et repère)","map.alert.last":"dernière arrivée : {0}, {1}","map.alert.nosound":"son indisponible dans ce navigateur","map.alert.on":"à l'écoute (relevé toutes les {0} s)","map.alert.wait":"le son démarre au premier clic dans la page","map.arrived":"● arrivée {0}","map.badurl":"(adresse invalide)","map.empty":"Aucune région dans la carte.","map.footer":"glb2html {0} : chaque carte est un lien qui emmène directement dans la région, à son point d'arrivée.","map.needserver":"Ouverte depuis le disque, cette carte ne peut pas lire regions.json : servez-la par un serveur web (adresse en http ou https).","map.nofile":"Impossible de lire {0} : aucune région à afficher.","map.novisitor":"aucun visiteur","map.pseudo":"Mon pseudo : ","map.pseudo.note":"mémorisé dans ce navigateur ; transmis aux régions que tu visites","map.regions.one":"{0} région","map.regions.other":"{0} régions","map.showurl":"Afficher les adresses","map.tip":"Cliquer pour entrer dans la région (arrivée : {0})","map.title":"Carte des mondes","map.total":"Total : {0}","map.visitor":"Visiteur","map.visitors.one":"{0} visiteur","map.visitors.other":"{0} visiteurs","map.mixed.one":"{0} visiteur, dont {1} en promenade","map.mixed.other":"{0} visiteurs, dont {1} en promenade","map.and":" et ","map.other.one":"{0} autre","map.other.other":"{0} autres","map.viewers":"en vue globale : {0}","map.walking.one":"{0} promeneur","map.walking.other":"{0} promeneurs","page.about.btn":"À propos de la région","page.about.close":"Fermer (Échap)","page.about.hide":"Ne plus afficher","page.about.opt":"Afficher l'à propos à l'entrée","page.btn.center":"Recentrer la vue","page.btn.center.tip":"Revenir au cadrage d'ouverture de la région (vue globale)","page.btn.fly":"Voler / Atterrir","page.btn.grab":"Capturer la souris","page.btn.help":"Aide (H)","page.btn.help.expand":"Déployer l'aide (H)","page.btn.help.hide":"Masquer l'aide (H)","page.btn.home":"Retour à l'arrivée (R)","page.btn.map":"Carte (M)","page.btn.map.ctrl":"Carte (Ctrl+M)","page.btn.walk":"Promenade (P)","page.chat.connecting":"Chat : connexion…","page.chat.disabled":"Chat non activé sur cette page : régénère-la avec --presence-url (et lance presence_server.py)","page.chat.error":"Chat hors ligne : nouvelle tentative…","page.chat.file.head":"Chat de la région « {0} » — enregistré le {1}","page.chat.file.note":"Messages reçus ou envoyés depuis ton arrivée (heure locale | nom | texte). Rien n'est gardé côté serveur.","page.chat.full":"Chat : salon complet","page.chat.help":"↵ Entrée : écrire (la saisie reste ouverte, Échap la ferme)","page.chat.mentions.go":"Aller au premier","page.chat.mentions.one":"{0} message vous cite","page.chat.mentions.other":"{0} messages vous citent","page.chat.names":"Pseudos","page.chat.offline":"Chat hors ligne","page.chat.offline.sys":"Chat indisponible : hors ligne","page.chat.older":"Messages plus anciens","page.chat.placeholder":"Message : Entrée pour envoyer (reste ouvert), Échap pour fermer","page.chat.save":"Enregistrer le chat","page.chat.save.title":"Enregistre dans un fichier texte les messages vus depuis ton arrivée","page.chat.saved.one":"Chat enregistré : {0} message","page.chat.saved.other":"Chat enregistré : {0} messages","page.compass.dirs":"N NE E SE S SO O NO","page.compass.label":"Cap : {0}","page.cones.off":"Repères de portail masqués (T pour les afficher)","page.cones.on":"Repères de portail affichés (T pour les masquer)","page.copy.aria":"Ma position","page.copy.btn":"Copier ma position","page.copy.fmt.aria":"Format de la position copiée","page.err.load":"Erreur de chargement : {0}","page.feat":"Cette page — réglages visiteur : {0} · présence : {1} · chat : {2} · vue globale : {3} · noms au clic : {4} · glb2html {5}","page.feat.names.no":"non (option --names)","page.feat.panel.yes":"oui (bouton en haut à droite)","page.feat.presence.no":"non (option --presence-url)","page.feat.presence.yes":"oui (salon {0})","page.feat.spectate.no":"non (option --spectate)","page.goto.aria":"Aller à x, y, z","page.goto.bad":"Trois nombres attendus : x, y, z (ex. 68.2, 39, -823.3), ou une adresse contenant #pos=x,y,z,cap","page.goto.btn":"Aller","page.goto.frame.page":"repère de cette page, modèle recentré","page.goto.frame.tiles":"repère du modèle d'origine","page.goto.label":"Aller à x, y, z (m, {0}) : ","page.goto.moved":"Cible déplacée en {0}","page.goto.tp":"Téléportation vers {0}","page.ground.loading":"Chargement du sol…","page.help.about":"? : à propos de la région","page.help.alt":"Alt + glisser : orbiter","page.help.center":"bouton « Recentrer la vue » : cadrage d'ouverture","page.help.chat.arrows":"flèches : dans le texte (après Échap : se déplacer)","page.help.chat.enter":"Entrée : écrire","page.help.chat.esc":"Échap : fermer","page.help.down":"Page Bas ou C : descendre","page.help.end":"Fin ou Alt + clic : caméra derrière l'avatar","page.help.enter":"P ou F : entrer","page.help.esc":"Échap : libérer","page.help.fly":"Début : voler / atterrir (ou le bouton)","page.help.g.chat":"Chat","page.help.g.fly":"Vol","page.help.g.mouse":"Souris","page.help.g.move":"Déplacement","page.help.g.orbit":"Vue globale","page.help.g.page":"Page","page.help.g.view":"Vue","page.help.g.walk":"Promenade","page.help.g.zones":"Zones","page.help.grab":"G : capturer / libérer","page.help.h":"H : aide","page.help.home":"R : retour à l'arrivée","page.help.i":"I : informations","page.help.jump":"Espace : sauter","page.help.l":"L : arrivées (téléportation)","page.help.landing":"double-clic : choisir le point d'atterrissage","page.help.m":"M : subjective / 3e personne","page.help.map":"M : carte des mondes","page.help.map.ctrl":"Ctrl+M : carte des mondes","page.help.mouse":"G ou bouton « Capturer la souris », puis souris : regarder (ou glisser, bouton enfoncé)","page.help.move":"{0} / flèches","page.help.o":"O : réglages","page.help.orbit.drag":"glisser : tourner","page.help.orbit.pan":"clic droit + glisser : déplacer","page.help.orbit.reframe":"R : centrer sur l'arrivée","page.help.orbit.wheel":"molette : zoom","page.help.quit":"P ou F : quitter la promenade","page.help.run":"Maj ou double appui {0} {1} ↑ ↓ : courir","page.help.takeoff":"Page Haut maintenu au sol : décoller","page.help.title":"Aide","page.help.tp":"double-clic : se téléporter","page.help.up":"Page Haut ou Espace maintenu : monter","page.help.view":"V : changer de vue","page.help.wheel":"molette : distance de la caméra (3e personne) ou zoom (caméra libre)","page.help.zone.click":"clic ou E : panneaux et portails","page.help.zone.click.orbit":"clic : panneaux et portails","page.help.zone.cone":"T : repères de portail","page.help.zone.name":"clic : nom de l'élément","page.home.none":"Pas de point de retour sur cette page","page.info.title":"Informations / État","page.key.done":"Identité remplacée par celle du lien","page.key.modal":"Ce lien personnel remplace l'identité de ce navigateur (nom réservé, historique) par celle de son propriétaire. Remplacer ?","page.landing.chosen":"Point d'atterrissage choisi : appuie sur P (ou F) pour t'y poser","page.layout.bad":"Ce fichier n'est pas une disposition de fenêtres","page.layout.load":"Charger une disposition","page.layout.loaded":"Disposition chargée","page.layout.reset":"Disposition d'origine","page.layout.reset.done":"Disposition d'origine rétablie","page.layout.save":"Enregistrer la disposition","page.layout.saved":"Disposition enregistrée : disposition.json","page.layout.title":"Disposition des fenêtres","page.loading":"Chargement…","page.map.badurl":"Adresse invalide : {0}","page.map.close":"Fermer (Échap)","page.map.count.one":"{0} promeneur","page.map.count.other":"{0} promeneurs","page.map.empty":"Aucune région dans la carte.","page.map.here":"● vous êtes ici","page.map.novisitor":"aucun visiteur","page.map.sep":"\n","page.map.tip":"Cliquer pour entrer dans la région (arrivée : {0})","page.map.tiphere":"Vous êtes dans cette région (un clic ferme la carte)","page.map.title":"Carte des mondes","page.map.visitors.one":"{0} visiteur","page.map.visitors.other":"{0} visiteurs","page.map.mixed.one":"{0} visiteur, dont {1} en promenade","page.map.mixed.other":"{0} visiteurs, dont {1} en promenade","page.map.and":" et ","page.map.other.one":"{0} autre","page.map.other.other":"{0} autres","page.map.viewers":"en vue globale : {0}","page.modal.no":"Annuler","page.modal.yes":"Oui","page.mouse.captured":"capturée (G ou Échap pour la libérer)","page.mouse.free":"libre (G ou bouton « Capturer la souris » pour la reprendre)","page.mouse.idle":"G ou bouton « Capturer la souris » pour la capturer (sinon : glisser, bouton enfoncé, pour regarder)","page.opt.anim":"Mer animée","page.opt.blink":"Message qui cite mon pseudo : la bulle de l'auteur clignote","page.opt.bold":"Message qui cite mon pseudo : en gras, précédé de « @ »","page.opt.color":"Choisir la couleur de mon avatar","page.opt.color.note":"Vue aussitôt par les autres visiteurs.\nDécochée : couleur tirée au hasard.","page.opt.compass":"Boussole (cap en haut de l'écran)","page.light.aa":"Anticrénelage (au prochain chargement)","page.light.ask":"Rendu sans carte graphique détecté. Activer le rendu léger ?","page.light.close":"Fermer","page.light.done":"Rendu léger activé. Réglages fins : bouton à côté de la case, dans Réglages.","page.light.fps":"Images par seconde (au plus)","page.light.m":"{0} m","page.light.no":"Non","page.light.nolimit":"sans limite","page.light.note":"Appliqués aussitôt (sauf l'anticrénelage) et retenus sur cet appareil.","page.light.ovonly":"Vue globale : vue d'ensemble seule (détails en promenade)","page.light.pct":"{0} %","page.light.preset":"Valeurs préconisées","page.light.radius":"Rayon des tuiles détaillées","page.light.scale":"Résolution du rendu","page.light.title":"Rendu léger : réglages fins","page.opt.light":"Rendu léger","page.opt.light.fine":"Réglages fins…","page.opt.histmax":"Messages d'historique affichés dans le chat (20 à 2000)","page.opt.lang":"Langue / Language : ","page.opt.layout":"Disposition du clavier : ","page.opt.link":"Copier mon lien personnel","page.opt.link.aria":"Lien personnel","page.opt.link.note":"Ce lien est un secret : quiconque l'ouvre prend ton identité (ton nom réservé). Ne le partage pas.","page.opt.note":"En promenade, Échap libère la souris pour utiliser ce panneau. Tes choix sont mémorisés sur cet appareil.","page.opt.reset":"Valeurs d'origine","page.opt.retina":"Haute résolution (plus net, plus lourd)","page.opt.sea":"Afficher la mer","page.opt.sound.cite":"Bip quand un message cite mon pseudo","page.opt.sound.msg":"Bip à chaque message quand la page n'a pas le focus","page.opt.sound.join":"Son à l'arrivée d'un visiteur","page.opt.sound.leave":"Son au départ d'un visiteur","page.opt.sounds":"Sons","page.opt.volume":"Volume : ","page.opt.wave":"Vagues : ","page.opts":"Réglages","page.pick.material":"matériau : {0}","page.pick.noname":"(sans nom)","page.pick.part":"élément : {0}","page.pos.invalid":"#pos= ignoré : x,y,z[,yaw] attendus (nombres)","page.pres.banned":"accès interdit","page.pres.connecting":"connexion…","page.pres.count.one":"{0} visiteur en ligne","page.pres.count.other":"{0} visiteurs en ligne","page.pres.error":"serveur injoignable ({0}), nouvelle tentative…","page.pres.error.why":"présence interrompue ({0}) : {1}, nouvelle tentative…","page.pres.error.stopped":"présence interrompue ({0}) : {1}, essais arrêtés : recharge la page pour réessayer","page.pres.refused":"présence refusée : {0} (recharge la page une fois corrigé)","page.pres.full":"salon complet","page.pres.kicked":"éjecté du salon (recharge la page pour revenir)","page.pres.nametaken":"Ce nom est déjà pris : tu es « {0} »","page.pres.nobody":"personne en promenade","page.pres.off":"hors ligne (P ou F : te connecter en promenade)","page.pres.toast.banned":"Accès interdit","page.pres.toast.kicked":"Éjecté par l'hôte","page.pres.walking.one":"{0} visiteur en promenade","page.pres.walking.other":"{0} visiteurs en promenade","page.presence.label":"Pseudo : ","page.shell.badregion":"paramètre region refusé « {0} » (un seul nom de fichier, sans / \\ : ? # ni .., sans point au début)","page.shell.error":"Erreur : {0}","page.shell.file":"Cette page est en mode modulaire : elle doit être servie en http ou https, pas ouverte depuis le disque. Pour la tester : python -m http.server dans son dossier, puis http://localhost:8000/{0}","page.shell.network":"réseau","page.shell.noregion":"Aucune région à ouvrir (« {0} » est introuvable) : ajoute ?region=NOM à l'adresse ou crée un fichier default.json contenant {\"region\": \"NOM\"}.","page.shell.notfound":"Erreur : {0} introuvable ({1})","page.spawn.done":"Téléportation : {0}","page.spawn.none":"Pas de point d'arrivée dans cette région","page.spawn.tip":"Liste des points de téléportation disponibles (TP)","page.spawn.title":"Arrivées","page.state.kb":"Clavier : {0} ({1})","page.state.kb.auto":"Clavier : {0} ({1}), automatique","page.state.mode":"Mode : {0}","page.state.mode.fly":"en vol","page.state.mode.walk":"à pied","page.state.mouse":"Souris : {0}","page.state.pos.avatar":"Position avatar : x {0} · y {1} · z {2} m","page.state.pos.target":"Position cible (vue globale) : x {0} · y {1} · z {2} m","page.state.run":" · course","page.state.view":"Vue : {0}","page.state.view.global":"globale (orbite)","page.tiles.error":"Tuile « {0} » : {1} (nouvelle tentative plus tard)","page.tiles.failed":"{0} en échec (nouvelle tentative)","page.tiles.here":"Tuile(s) sous l'avatar : {0}","page.tiles.loading":"{0} en cours","page.tiles.main.one":"Tuiles : {0} chargée / {1} · {2} Mo · {3} triangles","page.tiles.main.other":"Tuiles : {0} chargées / {1} · {2} Mo · {3} triangles","page.tiles.ov":"Vue d'ensemble (à part) : {0} Mo · {1} triangles","page.tiles.ov.failed":"Vue d'ensemble indisponible","page.toast.copied":"Copié","page.toast.copyfail":"Copie impossible : le texte est sélectionné, fais Ctrl+C","page.visitor":"Visiteur","page.wait.long":" · attente longue (tuile lourde ou réseau lent)","page.wait.region":"Chargement de la région…","page.wait.secs":" · {0} s","page.wait.tiles.one":"{1}/{0} tuile prête","page.wait.tiles.other":"{1}/{0} tuiles prêtes","page.win.h.tip":"Aide : touches et commandes de la vue actuelle.\nH : afficher, déployer, masquer.","page.win.i.tip":"Informations / État : vue, mode, position, tuiles, diagnostic.\nI : afficher, déployer, masquer.","page.win.l.tip":"Arrivées : liste des points de téléportation disponibles (TP).\nL : afficher, déployer, masquer.","page.win.move":"Clic sur le titre : réduire ou déplier. Glisser le titre : déplacer (lâchée sur une pile, en bas à gauche ou sous Réglages, la fenêtre s'y accroche ; ailleurs, elle reste libre). Double-clic sur le titre : retour à sa pile.","page.win.o.tip":"Réglages de la page et disposition des fenêtres.\nO : ouvrir, fermer.","page.zone.badcmd":"Adresse de commande invalide : {0}","page.zone.badlink":"Lien invalide : {0}","page.zone.cmdfail":"Échec de l'envoi : {0}","page.zone.cmdsent":"Commande envoyée : {0}","page.zone.confirm":"Envoyer la commande « {0} » ?","page.zone.noportal":"Portail sans destination valide : {0}","page.zone.nospawn":"Point d'arrivée « {0} » introuvable dans cette région","page.zone.opening":"Ouverture : {0}","page.zone.prompt":"clic ou E : {0}","core.image.missing":"image introuvable : {0}","core.webgl.missing":"La 3D ne peut pas s'afficher : WebGL est indisponible dans ce navigateur.\nQuand l'accélération matérielle est coupée, les navigateurs récents (Edge, Chrome) refusent maintenant le rendu logiciel.\nPistes : ouvrir cette page dans Firefox ; ou lancer Edge avec l'option --enable-unsafe-swiftshader (de préférence dans un profil réservé à ces pages) ; ou réactiver l'accélération matérielle.\nPour vérifier : edge://gpu (ou chrome://gpu), ligne WebGL.","page.status.walk":"Promenade","page.status.global":"Vue globale","page.status.pos":"x {0}  y {1}  z {2}","page.status.target":"cible x {0}  y {1}  z {2}","page.pad.label":"Flèches de déplacement","page.pad.hold":"Maintenir pour continuer.","page.pad.fwd":"Avancer ({0} ou ↑)","page.pad.back":"Reculer ({0} ou ↓)","page.pad.left":"Tourner à gauche (←)","page.pad.right":"Tourner à droite (→)","page.pad.side.l":"Pas de côté à gauche ({0})","page.pad.side.r":"Pas de côté à droite ({0})","page.pad.run":"Courir","page.pad.run.tip":"Courir (Maj) : un clic l'allume, un clic l'éteint","page.pad.up":"Monter (Page Haut)","page.pad.down":"Descendre (Page Bas ou C)","page.pad.g.fwd":"Déplacer la vue en avant","page.pad.g.back":"Déplacer la vue en arrière","page.pad.g.left":"Déplacer la vue à gauche","page.pad.g.right":"Déplacer la vue à droite","page.pad.g.tl":"Tourner la vue à gauche","page.pad.g.tr":"Tourner la vue à droite","page.pad.g.in":"Rapprocher (molette)","page.pad.g.out":"Éloigner (molette)","page.btn.pad":"Flèches (K)","page.btn.pad.off":"Flèches (K) : cachées","page.btn.pad.tip":"Afficher ou cacher les flèches à l'écran (K)","page.btn.walk.tip":"Entrer en promenade (F ou P)","page.btn.fly.tip":"Voler ou atterrir (Début)","page.btn.grab.tip":"Capturer la souris pour regarder autour de soi (la touche G la capture et la libère)","page.btn.home.tip":"Revenir au point d'arrivée (R)","page.btn.help.tip":"Aide : afficher, déployer, masquer (H)","page.btn.map.tip":"Carte des mondes (M ; Ctrl+M en promenade)","page.t.label":"Commandes tactiles","page.t.walk":"Promenade","page.t.exit":"Sortir","page.t.exit.tip":"Sortir de la promenade (F)","page.t.jump":"Sauter","page.t.jump.tip":"Sauter (Espace)","page.t.fly":"Voler","page.t.land":"Atterrir","page.t.view":"Vue","page.t.view.tip":"Changer de vue : subjective, troisième personne, caméra libre (V)","page.t.chat":"Chat","page.t.chat.n":"Chat ({0})","page.t.chat.tip":"Ouvrir le chat (Entrée)","page.t.pad":"Flèches","page.t.menu":"Menu","page.t.menu.tip":"Aide, informations, arrivées, carte, plein écran","page.menu.help":"Aide","page.menu.info":"Informations","page.menu.spawn":"Arrivées","page.menu.map":"Carte des mondes","page.menu.home":"Retour à l'arrivée","page.menu.center":"Recentrer la vue","page.menu.full":"Plein écran","page.menu.fullexit":"Quitter le plein écran","page.menu.full.fail":"Le navigateur refuse le plein écran","page.menu.close":"✕ Fermer le menu","page.win.close":"Fermer cette fenêtre","page.chat.send":"Envoyer","page.chat.send.tip":"Envoyer le message (Entrée)","page.chat.close":"✕ Fermer","page.chat.close.tip":"Fermer la saisie du chat (Échap)","page.opt.pad":"Flèches à l'écran (K)","page.opt.touch":"Commandes tactiles","page.opt.touch.on":"Oui","page.opt.touch.off":"Non","page.opt.zonenums":"Numéros des zones image (repérage)","page.help.k":"K : pavé de déplacement (flèches à l'écran)","page.touch.look":"Glisse le doigt sur l'écran pour regarder autour de toi","page.diag.touch":"Commandes tactiles","page.diag.touch.v":"{0} (réglage : {1} ; écran tactile détecté : {2} ; points de contact : {3})","page.visits.title":"Journal des visites","page.visits.intro":"Résumé des visites de cette région, pour son créateur. Entre la clé que l'hôte du serveur de présence t'a donnée.","page.visits.key":"Clé : ","page.visits.show":"Afficher","page.visits.forget":"Oublier la clé","page.visits.forgotten":"Clé oubliée par ce navigateur.","page.visits.csv":"Télécharger (CSV)","page.visits.close":"Fermer (Échap)","page.visits.wait":"Demande au serveur de présence…","page.visits.nopres":"Cette page n'a pas de serveur de présence : aucune visite n'est enregistrée.","page.visits.err.empty":"Entre la clé.","page.visits.err.key":"Clé refusée pour cette région.","page.visits.err.rate":"Trop d'essais : réessaie dans une minute.","page.visits.err.off":"Le serveur de présence n'enregistre pas les visites (option --visits).","page.visits.err.old":"Le serveur de présence est trop ancien pour le journal des visites (v48 ou plus récent).","page.visits.err.net":"Le serveur de présence ne répond pas.","page.visits.summary":"Salon « {0} » : visites {1}, visiteurs distincts {2}. Visites gardées {3} jours.","page.visits.summary.all":"Salon « {0} » : visites {1}, visiteurs distincts {2}. Visites gardées sans limite.","page.visits.none":"Aucune visite enregistrée pour cette région.","page.visits.days":"Par jour","page.visits.recent":"Visites des 30 derniers jours","page.visits.recent.cut":"(les {0} plus récentes)","page.visits.recent.none":"Aucune visite ces 30 derniers jours.","page.visits.c.date":"Date","page.visits.c.visits":"Visites","page.visits.c.visitors":"Visiteurs distincts","page.visits.c.total":"Durée totale","page.visits.c.median":"Durée médiane","page.visits.c.walked":"Avec promenade","page.visits.c.start":"Arrivée","page.visits.c.dur":"Durée","page.visits.c.walk":"Promenade","page.visits.c.name":"Pseudo","page.visits.yes":"oui","page.visits.no":"non","page.visits.d.h":"{0} h {1} min","page.visits.d.m":"{0} min {1} s","page.visits.file":"visites","page.visits.open":"Journal des visites…","page.visits.open.tip":"Pour le créateur de la région : résumé des visites, avec la clé donnée par l'hôte du serveur de présence"}};
const I18N_LANGS = Object.keys(I18N).sort();
const I18N_KEY = 'glb2html_lang';
// v37 : paramètres après # ; le séparateur est & et # est accepté aussi (#name=A&lang=en = #name=A#lang=en). Fonction commune à tous les lecteurs du hash.
const hashParams = h => new URLSearchParams(String(h === undefined ? location.hash : h).replace(/^#/, '').replace(/#/g, '&'));
const i18nName = code => (I18N[code] && I18N[code]._name) || code;
const i18nMatch = tag => { const c = String(tag || '').toLowerCase().split(/[-_]/)[0]; return I18N[c] ? c : null; };
// choix de l'utilisateur : 'auto' ou un code de langue disponible. #lang=xx dans l'adresse est prioritaire et mémorisé.
const LANG_PREF = (() => {
  let pref = 'auto';
  try { const s = localStorage.getItem(I18N_KEY); if (s === 'auto' || I18N[s]) pref = s; } catch (_) {}
  try {
    const h = hashParams().get('lang');
    if (h !== null) { const v = h.toLowerCase() === 'auto' ? 'auto' : i18nMatch(h); if (v) { pref = v; try { localStorage.setItem(I18N_KEY, v); } catch (_) {} } }
  } catch (_) {}
  return pref;
})();
// langue effective : Auto = première langue de navigator.languages qui est disponible, sinon l'anglais
const LANG = (() => {
  if (LANG_PREF !== 'auto') return LANG_PREF;
  const list = (typeof navigator !== 'undefined' && ((navigator.languages && navigator.languages.length) ? navigator.languages : [navigator.language])) || [];
  for (const l of list) { const c = i18nMatch(l); if (c) return c; }
  return I18N.en ? 'en' : (I18N_LANGS[0] || 'en');
})();
const i18nHas = k => [LANG, 'en', 'fr'].some(l => I18N[l] && typeof I18N[l][k] === 'string');
function tr(key, ...a) {
  const v = [LANG, 'en', 'fr'].map(l => I18N[l] && I18N[l][key]).find(x => typeof x === 'string');
  const s = v === undefined ? key : v;
  return a.length ? s.replace(/\{(\d+)\}/g, (m, i) => (a[i] === undefined ? m : String(a[i]))) : s;
}
// pluriel : clé.one / clé.other (et .zero .two .few .many selon la langue) ; {0} = n
const i18nPR = (() => { try { return new Intl.PluralRules(LANG); } catch (_) { return null; } })();
function trn(key, n, ...a) {
  const cat = i18nPR ? i18nPR.select(n) : (n === 1 ? 'one' : 'other');
  return tr(i18nHas(key + '.' + cat) ? key + '.' + cat : key + '.other', n, ...a);
}
// langue des dates et des nombres (jj/mm/aaaa pour le français et l'anglais)
const i18nLocale = LANG === 'en' ? 'en-GB' : (LANG === 'fr' ? 'fr-FR' : LANG);
const i18nNum = (n, d) => Number(n).toLocaleString(LANG, { minimumFractionDigits: d, maximumFractionDigits: d });
// textes du document : data-i18n (contenu), data-i18n-title, data-i18n-ph (placeholder), data-i18n-aria (aria-label)
function applyI18n(root) {
  root = root || document;
  const sets = [['data-i18n', (e, v) => { e.textContent = v; }], ['data-i18n-title', (e, v) => e.setAttribute('title', v)], ['data-i18n-ph', (e, v) => e.setAttribute('placeholder', v)], ['data-i18n-aria', (e, v) => e.setAttribute('aria-label', v)]];
  for (const [attr, set] of sets) for (const e of root.querySelectorAll('[' + attr + ']')) set(e, tr(e.getAttribute(attr)));
  if (root === document) document.documentElement.lang = LANG;
}
// liste pour un sélecteur de langue : Auto puis chaque langue disponible, avec son propre nom
const i18nChoices = () => [['auto', tr('common.auto')]].concat(I18N_LANGS.map(c => [c, i18nName(c)]));
// change la langue : mémorise, retire #lang= de l'adresse (sinon il l'emporterait), recharge la page
function setLangPref(v) {
  try { localStorage.setItem(I18N_KEY, v === 'auto' || I18N[v] ? v : 'auto'); } catch (_) {}
  try { const u = new URL(location.href), hp = hashParams(u.hash); hp.delete('lang'); const hs = hp.toString(); history.replaceState(null, '', u.pathname + u.search + (hs ? '#' + hs : '')); } catch (_) {}
  location.reload();
}

</script><main>
<h1 __TITLE_ATTR__>__TITLE__</h1>
<div id="who"><label><span data-i18n="map.pseudo">Mon pseudo : </span><input id="pseudo" maxlength="24" placeholder="Visiteur" data-i18n-ph="map.visitor" autocomplete="nickname"></label> <small data-i18n="map.pseudo.note">mémorisé dans ce navigateur ; transmis aux régions que tu visites</small> <label class="chk"><input type="checkbox" id="showurl"> <span data-i18n="map.showurl">Afficher les adresses</span></label></div>
<div id="tools"><label class="chk"><input type="checkbox" id="alert"> <span data-i18n="map.alert">Surveillance des arrivées (son et repère)</span></label> <small id="alertState"></small></div>
<div id="total"></div>
<div id="grid"></div>
<footer id="foot">glb2html 1.4.5 (03/11/2026)</footer>
</main>
<script type="application/json" id="cfg">__CONFIG__</script>
<script>
(() => {
  // v52 : delais d'interrogation des serveurs de presence (ms) : a modifier ici si la charge du serveur est trop forte
  const POLL_MS = 10000;        // normal
  const POLL_ALERT_MS = 5000;   // quand « Surveillance sonore » est cochee
  const C = JSON.parse(document.getElementById('cfg').textContent);
  let MAP = C.map || [];
  applyI18n(); document.getElementById('foot').textContent = tr('map.footer', '1.4.5 (03/11/2026)');
  if (document.querySelector('h1[data-i18n]')) document.title = tr('map.title');
  const grid = document.getElementById('grid'), counts = {}, vis = {}, nms = {}, answered = {}, hasVis = {}, MAPKEY = new URLSearchParams(location.hash.replace(/^#/, '').replace(/#/g, '&')).get('pseudos') || '';   // #pseudos=CLE : la cle du serveur (--map-names-key) pour voir les pseudos
   let loadErr = '';
  // v34 : pseudo mémorisé (même clé que les régions) ; les liens des cartes reçoivent #name=PSEUDO
  const pin = document.getElementById('pseudo');
  const pseudo = () => pin.value.replace(/[\u0000-\u001f<>]/g, '').trim().slice(0, 24);
  try { pin.value = localStorage.getItem('glb2html_name') || ''; } catch (e) {}
  pin.addEventListener('input', () => { try { localStorage.setItem('glb2html_name', pseudo()); } catch (e) {} draw(); });
  const srvOf = r => (r.presence || C.presenceUrl || '');
  // v47 : adresses des cartes masquées par défaut ; showUrl de l'en-tête de regions.json, puis la case (choix mémorisé dans ce navigateur) l'emporte
  const urlOn = () => { let v = null; try { v = localStorage.getItem('glb2html_map_showurl'); } catch (e) {} return v === null ? !!C.showUrl : v === '1'; };
  const su = document.getElementById('showurl'); su.checked = urlOn();
  su.addEventListener('change', () => { try { localStorage.setItem('glb2html_map_showurl', su.checked ? '1' : '0'); } catch (e) {} draw(); });
  const regionsOf = v => Array.isArray(v) ? v : (v && Array.isArray(v.regions) ? v.regions : null);
  const emptyText = () => loadErr || (C.mapUrl && !/^https?:$/.test(location.protocol) ? tr('map.needserver') : tr('map.empty'));
  const okUrl = u => { try { const x = new URL(u, location.href); return (x.protocol === 'http:' || x.protocol === 'https:' || (location.protocol === 'file:' && x.protocol === 'file:')) ? x : null; } catch (e) { return null; } };
  const safeThumb = t => typeof t === 'string' && (/^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+\/=]+$/.test(t) || (!/^[a-z][a-z0-9+.-]*:/i.test(t) || /^https?:/i.test(t)));
  const remap = vals => { const u = [...new Set(vals)].sort((a, b) => a - b), m = new Map(); let pos = 0; u.forEach((v, i) => { if (i) pos += Math.min(v - u[i - 1], 2); m.set(v, pos); }); return m; };
  // v52 : agrandissement de la vignette au survol (souris seulement ; une tuile sans vignette n'en a pas)
  const zoom = document.createElement('div'), zim = document.createElement('img'); let zpt = { x: 0, y: 0 };
  zoom.id = 'zoom'; zoom.hidden = true; zim.alt = ''; zoom.append(zim); document.body.append(zoom);
  const hideZoom = () => { zoom.hidden = true; };
  const placeZoom = () => { const w = zoom.offsetWidth, h = zoom.offsetHeight; let x = zpt.x + 16, y = zpt.y + 16; if (x + w > innerWidth - 4) x = zpt.x - w - 16; if (y + h > innerHeight - 4) y = innerHeight - h - 4; zoom.style.left = Math.max(4, x) + 'px'; zoom.style.top = Math.max(4, y) + 'px'; };
  const showZoom = src => { if (zim.getAttribute('src') !== src) zim.src = src; zoom.hidden = false; placeZoom(); };
  zim.onload = () => { if (!zoom.hidden) placeZoom(); };
  const zoomOn = (t, im) => {
    t.addEventListener('pointerenter', e => { if (e.pointerType !== 'mouse') return; zpt = { x: e.clientX, y: e.clientY }; showZoom(im.src); });
    t.addEventListener('pointermove', e => { if (e.pointerType !== 'mouse' || zoom.hidden) return; zpt = { x: e.clientX, y: e.clientY }; placeZoom(); });
    t.addEventListener('pointerleave', hideZoom);
  };
  const reZoom = () => { const el = document.elementFromPoint(zpt.x, zpt.y), t = el && el.closest ? el.closest('.tile') : null, im = t && t.querySelector('img'); if (im) showZoom(im.src); };
  // v52 : total des visiteurs, surveillance sonore des arrivees
  const al = document.getElementById('alert'), alState = document.getElementById('alertState'), tot = document.getElementById('total');
  const AC = window.AudioContext || window.webkitAudioContext, watched = {}, arrMark = {}; let actx = null, acted = false, lastBeep = -1e9, lastArr = null;
  try { al.checked = localStorage.getItem('glb2html_map_alert') === '1'; } catch (e) {}
  const ensure = () => { if (!acted || !AC) return null; try { if (!actx) actx = new AC(); if (actx.state === 'suspended' && actx.resume) actx.resume(); } catch (e) { return null; } return actx; };
  const beep = () => {   // les deux notes montantes de l'arrivee d'un promeneur dans la page, au plus un bip toutes les 2 s
    const now = performance.now(); if (now - lastBeep < 2000) return; const c = ensure(); if (!c) return;
    try { let t = c.currentTime; for (const [f, d] of [[660, 0.08], [880, 0.08]]) { const o = c.createOscillator(), g = c.createGain(); o.type = 'sine'; o.frequency.value = f; g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.2, t + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, t + d); o.connect(g); g.connect(c.destination); o.start(t); o.stop(t + d + 0.02); t += d; } lastBeep = now; } catch (e) {}
  };
  const hm = d => String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
  const showAlert = () => {
    let s = '';
    if (al.checked) { s = !AC ? tr('map.alert.nosound') : (!acted ? tr('map.alert.wait') : tr('map.alert.on', POLL_ALERT_MS / 1000)); if (lastArr) s += ' · ' + tr('map.alert.last', lastArr.name, lastArr.t); }
    alState.textContent = s;
  };
  for (const ev of ['pointerdown', 'keydown', 'touchstart']) addEventListener(ev, () => { if (!acted) { acted = true; if (al.checked) ensure(); showAlert(); } }, true);
  al.addEventListener('change', () => { try { localStorage.setItem('glb2html_map_alert', al.checked ? '1' : '0'); } catch (e) {} if (!al.checked) for (const k of Object.keys(arrMark)) delete arrMark[k]; showAlert(); if (al.checked) fetchCounts(); else draw(); tick(); });
  const vcount = (srv, room) => { const k = srv + '|' + room, w = counts[k] || 0; return hasVis[srv] ? Math.max(vis[k] || 0, w) : w; };
  const beforeOf = srv => { if (!watched[srv]) return null; const b = {}; for (const r of MAP) if (r && r.room && srvOf(r) === srv) b[r.room] = vcount(srv, r.room); return b; };
  const arrivals = (srv, before) => {   // une hausse du nombre de visiteurs d'un salon de la carte entre deux releves = une arrivee ; le premier releve d'un serveur sert de base
    watched[srv] = true; if (!before) return;
    const done = new Set();
    for (const r of MAP) { if (!r || !r.room || srvOf(r) !== srv || done.has(r.room)) continue; done.add(r.room); const b0 = before[r.room]; if (b0 !== undefined && vcount(srv, r.room) > b0) { lastArr = { name: r.name, t: hm(new Date()) }; if (al.checked) { beep(); arrMark[srv + '|' + r.room] = lastArr.t; } } }
    showAlert();
  };
  const countText = (v, w) => v < 0 ? trn('map.walking', w) : !v ? tr('map.novisitor') : !w ? trn('map.visitors', v) : v === w ? trn('map.walking', w) : trn('map.mixed', v, w);   // un seul nombre : celui qui marche n'est pas compte deux fois
  const namesText = (k, w, v) => { const nm = nms[k]; if (!nm) return ''; const lst = (a, rest) => { const shown = a.slice(0, 5), extra = Math.max(rest - shown.length, 0); return shown.join(', ') + (extra ? tr('map.and') + trn('map.other', extra) : ''); }; const out = []; if (nm.w.length) out.push(lst(nm.w, w)); if (nm.v.length) out.push(tr('map.viewers', lst(nm.v, Math.max(v - w, 0)))); return out.join('\n'); };   // pseudos (serveur lance avec --map-names-key, carte ouverte avec #pseudos=CLE) : les promeneurs, le plus recent d'abord, puis les visiteurs en vue globale
  let drawLater = false, lastSig = '';   // apres la v52 : on ne redessine que si les donnees ont change, et jamais tant qu'un texte de la grille est selectionne (sinon chaque releve efface la selection)
  const draw = () => {
    const sel = window.getSelection ? window.getSelection() : null;
    if (sel && !sel.isCollapsed && grid.contains(sel.anchorNode)) { drawLater = true; return; }
    const sig = JSON.stringify([MAP.map(r => r && [r.name, r.url, r.x, r.y, r.spawn, r.room, r.presence, r.thumb ? r.thumb.length : 0]), counts, vis, nms, answered, hasVis, urlOn(), pseudo(), arrMark, al.checked, C.showUrl, emptyText()]);
    if (sig === lastSig && grid.firstChild) return;   // rien n'a change depuis le dernier dessin : le DOM n'est pas touche (selection et zoom restent)
    lastSig = sig;
    const zoomWas = !zoom.hidden; hideZoom();
    let totV = 0, totW = 0, totOld = false, totGot = false; const totSeen = new Set();
    grid.textContent = '';
    const list = MAP.filter(r => r && r.name);
    const mx = remap(list.map(r => r.x | 0)), my = remap(list.map(r => r.y | 0));
    const cols = list.length ? Math.max(...mx.values()) + 1 : 0, rows = list.length ? Math.max(...my.values()) + 1 : 0;
    const placed = list.length > 0 && new Set(list.map(r => (r.x | 0) + ',' + (r.y | 0))).size === list.length && cols <= 14 && rows <= 14;
    grid.style.gridTemplateColumns = placed ? 'repeat(' + cols + ', 170px)' : 'repeat(auto-fill, 170px)';
    for (const r of list) {
      const u = okUrl(r.url); if (u) u.hash = 'spawn=' + encodeURIComponent(r.spawn || 'default') + (pseudo() ? '&name=' + encodeURIComponent(pseudo()) : '');
      const cell = document.createElement('div'); cell.className = 'cell'; const t = document.createElement(u ? 'a' : 'div'); t.className = 'tile'; t.title = u ? tr('map.tip', r.spawn || 'default') : tr('map.badurl');
      if (u) { t.href = u.href; t.rel = 'noopener'; }
      if (placed) { cell.style.gridColumn = String(mx.get(r.x | 0) + 1); cell.style.gridRow = String(rows - my.get(r.y | 0)); }
      if (r.thumb && safeThumb(r.thumb)) { const im = document.createElement('img'); im.src = r.thumb; im.alt = ''; im.referrerPolicy = 'no-referrer'; t.append(im); zoomOn(t, im); } else { const ph = document.createElement('div'); ph.className = 'ph'; t.append(ph); }
      const b = document.createElement('b'); b.textContent = r.name; t.append(b);
      const srv = srvOf(r), k = srv + '|' + (r.room || '');
      if (answered[srv] && r.room) {   // v47 : visiteurs (promeneurs et spectateurs) et promeneurs, en texte ; un ancien serveur ne donne que les promeneurs
        const w = counts[k] || 0, v = hasVis[srv] ? Math.max(vis[k] || 0, w) : -1;
        const s = document.createElement('span');
        const nt = namesText(k, w, v); s.textContent = countText(v, w) + (nt ? '\n' + nt : '');
        if (!totSeen.has(k)) { totSeen.add(k); totGot = true; totW += w; if (v < 0) totOld = true; else totV += v; }
        t.append(s);
      }
      if (al.checked && arrMark[k]) {   // v52 : repere de la region ou quelqu'un vient d'arriver (bordure clignotante ET texte), jusqu'au survol de la tuile
        t.classList.add('arr'); const a = document.createElement('span'); a.className = 'arrb'; a.textContent = tr('map.arrived', arrMark[k]); t.append(a);
        t.addEventListener('pointerenter', () => { delete arrMark[k]; t.classList.remove('arr'); a.remove(); }, { once: true });
      }
      if (!u || urlOn()) { const l = document.createElement('small'); l.textContent = u ? u.href : tr('map.badurl'); cell.append(l); }   // apres la v52 : l'adresse est HORS du lien de la vignette (dans un lien, un clic-glisse ne selectionne pas le texte)
      cell.prepend(t); grid.append(cell);
    }
    if (!list.length) grid.textContent = emptyText();
    tot.textContent = list.length ? trn('map.regions', list.length) + (totGot ? ' · ' + tr('map.total', countText(totOld ? -1 : totV, totW)) : '') : '';   // decompte des regions, puis le total
    document.getElementById('tools').hidden = !MAP.some(r => r && srvOf(r));   // sans serveur de presence, la surveillance n'a rien a surveiller : la case disparait
    if (zoomWas) reZoom();
  };
  document.addEventListener('selectionchange', () => { if (drawLater) { const s = window.getSelection(); if (!s || s.isCollapsed) { drawLater = false; draw(); } } });   // la selection est finie : on redessine
  // v51 : « * » à la place du nom = le même nom que la page (même règle que presUrl de core.js)
  const presUrl = u => String(u || '').trim().replace(/^(wss?:\/\/)(\*|0\.0\.0\.0)(?=[:/]|$)/i, (m, p, h) => p + (h === '*' ? (location.hostname || '127.0.0.1') : '127.0.0.1'));
  const queryServer = srv => {
    try {
      const ws = new WebSocket(presUrl(srv)), to = setTimeout(() => { try { ws.close(); } catch (e) {} }, 4000);
      ws.onopen = () => ws.send(JSON.stringify(MAPKEY ? { t: 'rooms', key: MAPKEY } : { t: 'rooms' }));
      ws.onmessage = ev => {
        try { const m = JSON.parse(ev.data); if (m.t === 'rooms') { const before = beforeOf(srv); for (const o of [counts, vis, nms]) for (const k of Object.keys(o)) if (k.startsWith(srv + '|')) delete o[k]; for (const [room, n] of Object.entries(m.rooms || {})) counts[srv + '|' + room] = n; hasVis[srv] = !!(m.visitors && typeof m.visitors === 'object'); if (hasVis[srv]) for (const [room, n] of Object.entries(m.visitors)) vis[srv + '|' + room] = n; const ob = x => (x && typeof x === 'object' ? x : {}), cl = a => (Array.isArray(a) ? a.filter(x => typeof x === 'string' && x).slice(0, 20) : []); for (const room of new Set([...Object.keys(ob(m.names)), ...Object.keys(ob(m.viewers))])) nms[srv + '|' + room] = { w: cl(ob(m.names)[room]), v: cl(ob(m.viewers)[room]) }; answered[srv] = true; arrivals(srv, before); draw(); } } catch (e) {}
        try { ws.close(); } catch (e) {}
      };
      ws.onclose = () => clearTimeout(to); ws.onerror = () => {};
    } catch (e) {}
  };
  const fetchCounts = () => { for (const srv of new Set(MAP.map(srvOf).filter(Boolean))) queryServer(srv); };
  draw(); fetchCounts(); showAlert();
  let tmr = 0;
  const tick = () => { clearTimeout(tmr); tmr = setTimeout(() => { fetchCounts(); tick(); }, al.checked ? POLL_ALERT_MS : POLL_MS); };   // v52 : delai relu a chaque tour et des que la case change
  tick();
  if (C.mapUrl && /^https?:$/.test(location.protocol)) {
    const urls = String(C.mapUrl).split(',').map(s => s.trim()).filter(Boolean);
    Promise.allSettled(urls.map(u => fetch(new URL(u, location.href).href, { cache: 'no-store' }).then(r => r.ok ? r.json() : Promise.reject(new Error('http ' + r.status))))).then(res => {
      const merged = [], seen = new Set(); let hdr = null, got = false;
      for (const x of res) { const arr = x.status === 'fulfilled' ? regionsOf(x.value) : null; if (!arr) continue; got = true; if (hdr === null && typeof x.value.showUrl === 'boolean') hdr = x.value.showUrl;
       for (const r of arr) {
        if (!r || typeof r.name !== 'string' || typeof r.url !== 'string') continue;
        const e = { name: r.name.slice(0, 60), url: r.url.slice(0, 600), x: Number(r.x) | 0, y: Number(r.y) | 0, spawn: String(r.spawn || '').slice(0, 40), room: String(r.room || '').slice(0, 64), presence: /^wss?:\/\//i.test(String(r.presence || '')) ? String(r.presence).slice(0, 300) : '', thumb: safeThumb(r.thumb) ? String(r.thumb).slice(0, 200000) : '' };
        const k = e.url + '|' + e.room; if (!seen.has(k)) { seen.add(k); merged.push(e); }
       }
      }
      if (hdr !== null) C.showUrl = hdr;
      su.checked = urlOn();
      if (merged.length) { MAP = merged; loadErr = ''; } else if (!got) loadErr = tr('map.nofile', urls.join(', '));
      draw(); if (merged.length) fetchCounts();
    });
  }
})();
</script>
</body>
</html>
"""


def data_path(arg):
    """Fichier de données (carte) : chemin relatif -> dossier de lancement s'il y existe, sinon dossier du script (créé là si absent)."""
    p = pathlib.Path(arg).expanduser()
    if p.is_absolute():
        return p
    here = pathlib.Path.cwd() / p
    return here if here.is_file() else pathlib.Path(__file__).resolve().parent / p


def page_path(arg, base):
    """--update : chemin relatif d'un fichier de carte -> relatif au dossier de la page (-o), jamais au dossier de lancement ni à celui des outils."""
    p = pathlib.Path(arg).expanduser()
    return p if p.is_absolute() else pathlib.Path(base) / p


def where_note(reg, out):
    """Hors --update : une ligne qui dit où le fichier de carte est écrit quand ce n'est pas à côté de la page (-o)."""
    if out and pathlib.Path(reg).resolve().parent != pathlib.Path(out).resolve().parent:
        print(_tr("py.glb2html.carte_0_n_est_pas_a", reg, out))


def thumb_data_url(arg):
    if re.match(r"^https?://", str(arg), re.I):
        return str(arg)[:600]
    p = find_beside(arg)
    if p is None:
        print(_tr("py.glb2html.avertissement_vignette_introuvable_0", arg), file=sys.stderr)
        return ""
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(p.suffix.lower())
    b = p.read_bytes()
    if not mime or len(b) > 140000:
        print(_tr("py.glb2html.avertissement_vignette_ignoree_jpg_png_webp", p), file=sys.stderr)
        return ""
    return f"data:{mime};base64," + base64.b64encode(b).decode("ascii")


def register_region(path, entry):
    """Ajoute ou met à jour (par salon) une région dans le fichier de carte ; les champs non fournis gardent leur valeur."""
    raw = []
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            sys.exit(_tr("py.glb2html.erreur_0_illisible_1", path, e))
    head = {k: v for k, v in raw.items() if k != "regions"} if isinstance(raw, dict) else None   # v47 : l'en-tête (showUrl...) est gardé
    data = [r for r in map_regions(raw) if isinstance(r, dict)]
    i = next((k for k, r in enumerate(data) if (r.get("room") and r.get("room") == entry["room"]) or r.get("id") == entry["id"]), None)
    if i is None:
        data.append({"id": entry["id"], "name": entry["name"], "url": entry["url"], "x": 0, "y": 0, "spawn": "", "room": entry["room"], "thumb": ""})
        i = len(data) - 1
    for k, v in entry.items():
        if v is not None and v != "":
            data[i][k] = v
    out = dict(head, regions=data) if head is not None else data
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def map_page_html(cfg, title):
    return (MAP_PAGE_TEMPLATE.replace("__TITLE_ATTR__", "" if title else 'data-i18n="map.title"').replace("__TITLE__", html.escape(title or "Carte des mondes")).replace("1.4.5 (03/11/2026)", MAP_VERSION)
            .replace("__CONFIG__", json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/")))


def build_map_shell():
    """v47 : la page de carte universelle (dist/carte.html) : même texte, octet pour octet, pour tous les sites ; aucune région dedans, elle lit
    regions.json (à côté d'elle) à chaque ouverture. Titre traduit par la page elle-même ; demande un serveur web (http)."""
    return map_page_html({"map": [], "mapUrl": "regions.json", "presenceUrl": "", "showUrl": False}, None)


SCAN_SKIP = {"lib", "_bak", "node_modules"}
SCAN_IMG = (".jpg", ".jpeg", ".png", ".webp")


def scan_sites(root, dry):
    """v49 : parcourt le dossier des sites (coquille commune à la racine) et met à jour root/regions.json : une fiche par NOM.config.json
    (adresse index.html?region=dossier/NOM, salon, serveur de présence, vignette NOM.jpg/.png/.webp à côté). Reconnaît une fiche par son salon,
    sinon par son adresse ; garde le nom, la place, l'arrivée et l'en-tête ; ne touche pas aux fiches externes ; ne supprime rien."""
    root = pathlib.Path(root).expanduser()
    if not root.is_dir():
        sys.exit(_tr("py.glb2html.scan.nofolder", root))
    if not (root / "index.html").is_file():
        print(_tr("py.glb2html.scan.noshell", root), file=sys.stderr)
    reg = root / "regions.json"
    raw = {"showUrl": False, "regions": []}
    if reg.is_file():
        try:
            raw = json.loads(reg.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            sys.exit(_tr("py.glb2html.erreur_0_illisible_1", reg, e))
    head = {k: v for k, v in raw.items() if k != "regions"} if isinstance(raw, dict) else None
    data = [r for r in map_regions(raw) if isinstance(r, dict)]
    local = lambda u: bool(u) and not re.match(r"^[a-z][a-z0-9+.\-]*:", str(u), re.I)
    found = []
    for cf in sorted(root.rglob("*.config.json")):
        rel = cf.relative_to(root)
        if any(p in SCAN_SKIP or p.startswith(".") for p in rel.parts[:-1]):
            continue
        try:
            c = json.loads(cf.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(_tr("py.glb2html.scan.badcfg", cf, e), file=sys.stderr)
            continue
        if not isinstance(c, dict) or "room" not in c:
            continue
        stem = cf.name[:-len(".config.json")]
        name = "/".join(rel.parts[:-1] + (stem,))
        img = next((cf.with_name(stem + e) for e in SCAN_IMG if cf.with_name(stem + e).is_file()), None)
        found.append({"name": stem, "url": "index.html?region=" + name, "room": str(c.get("room") or "").strip()[:64],
                      "presence": str(c.get("presenceUrl") or ""), "thumb": urllib.parse.quote(img.relative_to(root).as_posix()) if img else ""})
    used = {(int(r.get("x") or 0), int(r.get("y") or 0)) for r in data}
    ids = {str(r.get("id") or "") for r in data}
    added = updated = same = 0
    seen = set()
    for f in found:
        i = next((k for k, r in enumerate(data) if f["room"] and r.get("room") == f["room"]), None)
        if i is None:
            i = next((k for k, r in enumerate(data) if r.get("url") == f["url"]), None)
        if i is None:
            x = 0
            while (x, 0) in used:
                x += 1
            used.add((x, 0))
            rid = _slug(f["room"] or f["name"]) or "region"
            while rid in ids:
                rid += "-2"
            ids.add(rid)
            data.append({"id": rid, "name": f["name"], "url": f["url"], "x": x, "y": 0, "spawn": "", "room": f["room"], "thumb": f["thumb"], "presence": f["presence"]})
            seen.add(len(data) - 1)
            added += 1
            print(_tr("py.glb2html.scan.add", f["name"], f["url"], x, 0))
            continue
        seen.add(i)
        r, ch = data[i], []
        for k in ("url", "room", "presence", "thumb"):
            if f[k] and r.get(k) != f[k]:
                r[k] = f[k]
                ch.append(k)
        if ch:
            updated += 1
            print(_tr("py.glb2html.scan.upd", r.get("name"), ", ".join(ch)))
        else:
            same += 1
    ext = sum(1 for r in data if not local(r.get("url")))
    orph = [r for k, r in enumerate(data) if k not in seen and local(r.get("url"))]
    for r in orph:
        print(_tr("py.glb2html.scan.orphan", r.get("name"), r.get("url")))
    print(_tr("py.glb2html.scan.summary", added, updated, same, ext, len(orph), reg))
    if dry:
        print(_tr("py.glb2html.scan.dry"))
        return
    out = dict(head, regions=data) if head is not None else data
    reg.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


def write_map_page(path, entries, presence_url, map_url, title):
    cfg = {"map": clean_map(entries), "mapUrl": str(map_url or "")[:1200], "presenceUrl": fix_presence_url(presence_url), "showUrl": bool(entries.get("showUrl")) if isinstance(entries, dict) else False}
    page = map_page_html(cfg, title)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")
    print(_tr("py.glb2html.carte_page_carte_0_region_s", len(cfg['map']), path))


def settings_defaults(S):
    """Valeurs par défaut tirées d'un fichier de réglages enregistré par le viewer (« Enregistrer dans un fichier »)."""
    c = S.get("cfg") if isinstance(S.get("cfg"), dict) else {}
    cam = S.get("camera") if isinstance(S.get("camera"), dict) else {}
    d = {}
    def put(dest, v, conv):
        if v is None:
            return
        try:
            d[dest] = conv(v)
        except (TypeError, ValueError, IndexError):
            pass
    vec = lambda v: tuple(float(x) for x in list(v)[:3]) if len(v) >= 3 else (_ for _ in ()).throw(ValueError())
    for k, dest, conv in (("rotate", "rotate", int), ("hole", "hole", float), ("holeFade", "hole_fade", float), ("holeX", "hole_x", float), ("holeZ", "hole_z", float),
                          ("wave", "wave", float), ("seaY", "sea_y", float), ("seaSegments", "sea_segments", int), ("seaColor", "sea_color", int),
                          ("skyColor", "sky_color", int), ("foliageCutout", "foliage_cutout", float), ("anim", "anim_enabled", bool),
                          ("sea", "sea_enabled", bool), ("retina", "retina", bool), ("light", "light", bool), ("walk", "walk", bool), ("eyeHeight", "eye_height", float),
                          ("walkSpeed", "walk_speed", float), ("walkIgnore", "walk_ignore", str), ("solidMaterials", "solid_materials", str), ("names", "names", bool), ("chat", "chat", bool),
                          ("chatFade", "chat_fade", float), ("presenceUrl", "presence_url", str), ("room", "room", str), ("spectate", "spectate", bool),
                          ("panel", "panel", bool), ("mapUrl", "map_url", str), ("zoneMarker", "zone_marker", str), ("showSpawns", "show_spawns", bool), ("zoneCone", "zone_cone", bool), ("fly", "fly", bool), ("zoneInfoDist", "zone_info_dist", float), ("compass", "compass", bool), ("northDeg", "north", float), ("libUrl", "lib_url", str)):
        put(dest, c.get(k), conv)
    put("target_explicit", S.get("targetExplicit"), bool)
    put("zoom", cam.get("zoom"), float)
    put("cam_dir", cam.get("camDir"), vec)
    put("target", cam.get("target"), vec)
    if S.get("profile") in ("public", "private", "perso"):
        d["profile"] = PROFILE_OLD.get(S["profile"], S["profile"])
    return d


def vendor_bytes(rel: str, vendor_dir: pathlib.Path | None) -> bytes:
    if vendor_dir:
        p = vendor_dir / rel
        if not p.is_file():
            sys.exit(_tr("py.glb2html.erreur_0_introuvable_vendor_doit_pointer", p))
        return p.read_bytes()
    p = CACHE_DIR / rel
    if not p.is_file():
        p.parent.mkdir(parents=True, exist_ok=True)
        print(_tr("py.glb2html.cache_telechargement_0", CDN + rel))
        try:
            with urllib.request.urlopen(CDN + rel, timeout=60) as r:
                data = r.read()
        except Exception as e:
            sys.exit(_tr("py.glb2html.erreur_telechargement_impossible_0_utilise_v", e))
        p.write_bytes(data)
    return p.read_bytes()


def fix_imports(src: bytes) -> str:
    # les imports relatifs ne se résolvent pas depuis une URL data: (ni depuis lib/ à plat) -> spécificateurs nus de l'importmap
    return src.decode("utf-8").replace("'../utils/BufferGeometryUtils.js'", "'three/addons/utils/BufferGeometryUtils.js'")


def js_data_url(src: bytes) -> str:
    return "data:text/javascript;base64," + base64.b64encode(fix_imports(src).encode("utf-8")).decode("ascii")


def bin_data_url(src: bytes, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(src).decode("ascii")


def inspect_glb(data: bytes, name: str) -> set:
    if len(data) < 20 or data[:4] != b"glTF":
        raise ValueError(_tr("py.glb2html.0_pas_un_glb_magic_absent", name))
    version, total = struct.unpack_from("<II", data, 4)
    if version != 2:
        raise ValueError(_tr("py.glb2html.0_gltf_version_1_non_supportee", name, version))
    if total != len(data):
        raise ValueError(_tr("py.glb2html.0_taille_annoncee_1_taille_fichier", name, total, len(data)))
    clen, ctype = struct.unpack_from("<II", data, 12)
    if ctype != 0x4E4F534A:
        raise ValueError(_tr("py.glb2html.0_premier_chunk_non_json", name))
    gltf = json.loads(data[20:20 + clen].decode("utf-8"))
    used = set(gltf.get("extensionsUsed", [])) | set(gltf.get("extensionsRequired", []))
    ext_refs = [x.get("uri") for x in gltf.get("buffers", []) + gltf.get("images", [])
                if x.get("uri") and not x["uri"].startswith("data:")]
    if ext_refs:
        raise ValueError(_tr("py.glb2html.0_reference_des_fichiers_externes_1", name, ext_refs[:3]))
    if "KHR_texture_basisu" in used:
        raise ValueError(_tr("py.glb2html.0_textures_ktx2_basis_non_gerees", name))
    return used


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<link rel="icon" id="siteIcon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2064%2064'%3E%3Crect%20width='64'%20height='64'%20rx='12'%20fill='%230b3d6e'/%3E%3Ctext%20x='32'%20y='45'%20font-family='Arial%2CHelvetica%2Csans-serif'%20font-size='34'%20font-weight='700'%20text-anchor='middle'%20fill='%23fff'%3E3D%3C/text%3E%3C/svg%3E"/>
<script>(function () { var i = new Image(); i.onload = function () { var l = document.getElementById("siteIcon"); l.type = "image/x-icon"; l.href = "favicon.ico"; }; i.src = "favicon.ico"; })();</script>
<title>__TITLE__</title>
<style>
[hidden]{display:none!important}
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#__SKY_HEX__}
#view{position:fixed;inset:0}
canvas{display:block;touch-action:none}
#walkBtn,#helpBtn,#mapBtn,#homeBtn,#centerBtn,#flyBtn,#grabBtn,#padBtn,#walkHint,#stateInfo,#spawnInfo{font:12px/1.4 ui-monospace,Consolas,monospace;background:#fffffff0;color:#000;border:1px solid #000;border-radius:6px;padding:7px 10px}
#walkBtn,#helpBtn,#mapBtn,#homeBtn,#centerBtn,#flyBtn,#grabBtn,#padBtn{cursor:pointer}
#dock{position:fixed;left:12px;bottom:12px;display:flex;flex-direction:column;align-items:flex-start;gap:8px}
#bar{display:flex;flex-wrap:wrap;gap:8px;max-width:max(260px,calc(100vw - 430px))}
body.padOn #bar{max-width:max(200px,calc(50vw - 90px))}   /* v46 : la barre passe à la ligne avant le pavé de flèches */
@media (min-width:1361px){#bar{max-width:calc(50vw - 300px)!important}}   /* v46 : et avant la ligne d'état, en bas au centre */
#dock,#hudL,#bar{pointer-events:none}
#walkHint,#stateInfo,#spawnInfo,#bar button{pointer-events:auto}   /* seuls l'aide, l'état et les boutons reçoivent la souris : l'espace vide entre eux laisse passer les clics et le survol */
#presence,#nameTag{position:fixed;font:12px/1.4 ui-monospace,Consolas,monospace;background:#fffffff0;color:#000;border:1px solid #000;border-radius:6px;padding:7px 10px}
#presence{left:12px;top:12px}
#presence input{font:inherit;width:130px;border:1px solid #000;border-radius:4px;padding:2px 4px}
#chat{position:fixed;right:12px;bottom:12px;width:min(380px,calc(100% - 24px));font:12px/1.4 ui-monospace,Consolas,monospace;color:#000}
#chatLog.open{max-height:min(45vh,420px);overflow-y:auto;overscroll-behavior:contain}
#chatOlder,#mentGo{font:inherit;background:#fffffff0;color:#000;border:1px solid #000;border-radius:6px;padding:3px 8px;cursor:pointer}
#chatOlder{margin-bottom:4px}
#chatMentions{margin-bottom:4px;background:#000;color:#fff;border-radius:6px;padding:4px 8px}
#chatLog div{background:#fffffff0;border:1px solid #000;border-radius:6px;padding:4px 8px;margin-top:4px;word-break:break-word}
#chatLog .sys{font-style:italic}
#chatHelp{margin-top:4px;background:#000;color:#fff;border-radius:6px;padding:4px 8px}
#chatSave{margin-top:4px;font:inherit;background:#fffffff0;color:#000;border:1px solid #000;border-radius:6px;padding:3px 8px;cursor:pointer}
#chatComplete{margin-top:6px;background:#fff;border:2px solid #000;border-radius:6px;font-weight:bold}
#chatComplete div{padding:3px 8px;white-space:pre}
#chatComplete div[aria-selected=true]{background:#000;color:#fff}
#walkHint input,#walkHint button{font:inherit;border:1px solid #000;border-radius:4px;padding:2px 6px;background:#fff;color:#000}
#walkHint button{cursor:pointer}
#chatInput{box-sizing:border-box;width:100%;margin-top:6px;font:inherit;padding:6px;border:2px solid #000;border-radius:6px}
#nameTag{pointer-events:none;max-width:320px}
#mapOverlay{position:fixed;inset:0;z-index:45;background:#000c;display:grid;place-items:center}
#mapBox{background:#fff;color:#000;border:2px solid #000;border-radius:10px;padding:14px 16px;max-width:min(980px,94%);max-height:90%;overflow:auto;font:13px/1.4 ui-monospace,Consolas,monospace}
#mapBox h2{margin:0 0 10px;font-size:15px}
#aboutOverlay{position:fixed;inset:0;z-index:46;background:#000c;display:grid;place-items:center}
#aboutBox{box-sizing:border-box;background:#fff;color:#000;border:2px solid #000;border-radius:10px;padding:14px 16px;width:min(640px,94%);max-height:90%;overflow:auto;font:13px/1.5 ui-monospace,Consolas,monospace}
#aboutBox:focus{outline:none}
#aboutBox h2{margin:0 0 10px;font-size:15px}
#aboutText{white-space:pre-wrap;overflow-wrap:anywhere;margin:0 0 12px}
#aboutBox button,#aboutBtn{font:inherit;color:#000;background:#fff;border:2px solid #000;border-radius:6px;padding:4px 10px;margin-right:6px;cursor:pointer}
#aboutBtn{margin:6px 0 0;padding:2px 8px}
#mapGrid{display:grid;gap:10px;justify-content:start;margin-bottom:10px}
.mapTile{box-sizing:border-box;display:flex;flex-direction:column;gap:4px;width:160px;padding:6px;border:2px solid #000;border-radius:8px;background:#fff;cursor:pointer;font:inherit;text-align:left;color:#000}
.mapTile:hover{background:#eee}
.mapTile.here{border-width:5px;cursor:default}
.mapTile img,.mapTile .ph{width:100%;aspect-ratio:1;object-fit:cover;background:#ccc;border:1px solid #000;display:block}
.mapTile b{word-break:break-word}
.mapTile span{white-space:pre-line}
#zoom{position:fixed;z-index:60;pointer-events:none;box-sizing:border-box;padding:4px;border:2px solid #000;border-radius:6px;background:#fff;box-shadow:0 4px 16px #0007}
#zoom img{display:block;max-width:min(400px,80vw);max-height:min(400px,80vh)}
#zoom[hidden]{display:none}
#mapClose{font:inherit;padding:6px 14px;border:2px solid #000;border-radius:6px;background:#fff;cursor:pointer}
#visitsOverlay{position:fixed;inset:0;z-index:46;background:#000c;display:grid;place-items:center}   /* v48 : journal des visites (#visits) */
#visitsBox{box-sizing:border-box;background:#fff;color:#000;border:2px solid #000;border-radius:10px;padding:14px 16px;width:min(760px,96%);max-height:92%;overflow:auto;font:13px/1.4 ui-monospace,Consolas,monospace}
#visitsBox h2{margin:0 0 8px;font-size:15px}
#visitsBox h3{margin:12px 0 4px;font-size:13px}
#visitsBox p{margin:0 0 8px}
#visitsBox button{font:inherit;padding:5px 12px;margin:4px 6px 4px 0;border:2px solid #000;border-radius:6px;background:#fff;color:#000;cursor:pointer}
#visitsKey{font:inherit;padding:5px;border:2px solid #000;border-radius:6px;width:16em;max-width:100%}
#visitsStatus{margin:6px 0;font-weight:bold}
#visitsOut table{border-collapse:collapse;margin-bottom:6px}
#visitsOut th,#visitsOut td{border:1px solid #000;padding:2px 8px;text-align:right;white-space:nowrap}
#visitsOut th{background:#eee}
#visitsOut td:first-child,#visitsOut th:first-child{text-align:left}
.visitsScroll{overflow-x:auto;max-width:100%}
#opts{position:fixed;top:12px;right:12px;z-index:20;font:12px/1.4 ui-monospace,Consolas,monospace;color:#000;text-align:right}
#optsBtn{font:inherit;background:#fffffff0;border:1px solid #000;border-radius:6px;padding:6px 10px;cursor:pointer}
#optsPanel{margin-top:6px;background:#fffffff0;border:1px solid #000;border-radius:6px;padding:8px 12px;text-align:left}
#optsPanel label{display:flex;gap:8px;align-items:center;margin:6px 0}
#optsPanel input[type=range]{width:150px}
#optsPanel button{font:inherit;margin-top:4px;padding:4px 10px;border:1px solid #000;border-radius:6px;background:#fff;cursor:pointer}
#optsPanel small{display:block;margin-top:6px;opacity:.8;contain:inline-size}
#optsPanel small.two{white-space:pre-line}
#optsPanel .sec{margin-top:10px;padding-top:8px;border-top:1px solid #000}
#optsPanel .secT{font-weight:bold}
#optsPanel .btnrow{display:flex;flex-wrap:wrap;gap:6px}
#optsNote{border-top:1px solid #0006;padding-top:6px}
#optsPanel{box-sizing:border-box;max-width:min(420px,calc(100vw - 24px));max-height:calc(100vh - 60px);overflow-y:auto}
#optsPanel .lrow{display:flex;gap:8px;align-items:center}
#optsPanel .lrow button{margin-top:0}
#lightPanel{position:absolute;right:calc(100% + 8px);top:34px;width:max-content;max-width:min(380px,calc(100vw - 100% - 32px));box-sizing:border-box;background:#fffffff0;border:1px solid #000;border-radius:6px;padding:8px 12px;text-align:left}
#optsPanel[hidden]~#lightPanel{display:none}
#lightHead{display:flex;justify-content:space-between;align-items:center;gap:12px;font-weight:bold}
#lightPanel label{display:flex;gap:8px;align-items:center;margin:6px 0}
#lightPanel input[type=range]{width:130px}
#lightPanel button{font:inherit;padding:2px 8px;border:1px solid #000;border-radius:6px;background:#fff;cursor:pointer}
#lightPanel small{display:block;margin-top:6px;opacity:.8;contain:inline-size}
#lightAsk{position:fixed;bottom:56px;left:50%;transform:translateX(-50%);z-index:41;font:13px/1.4 ui-monospace,Consolas,monospace;background:#fff;color:#000;border:2px solid #000;border-radius:6px;padding:8px 12px;width:max-content;max-width:min(340px,90vw);box-sizing:border-box}
#lightAsk button{font:inherit;margin-left:8px;padding:2px 10px;border:1px solid #000;border-radius:6px;background:#fff;cursor:pointer}
#toast{position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:40;font:13px/1.4 ui-monospace,Consolas,monospace;background:#000;color:#fff;border-radius:6px;padding:8px 14px;max-width:90%}
#zonePrompt{position:fixed;left:50%;bottom:84px;transform:translateX(-50%);z-index:30;font:13px/1.4 ui-monospace,Consolas,monospace;background:#000;color:#fff;border-radius:6px;padding:6px 12px}
#fade{position:fixed;inset:0;background:#000;opacity:0;pointer-events:none;transition:opacity .45s;z-index:50}
#fade.on{opacity:1;pointer-events:auto}
#modal{position:fixed;inset:0;display:grid;place-items:center;background:#0008;z-index:60}
#modal div{background:#fff;color:#000;border:2px solid #000;border-radius:8px;padding:16px 20px;font:14px/1.5 ui-monospace,Consolas,monospace;max-width:min(420px,90%)}
#modal button{font:inherit;margin:10px 8px 0 0;padding:6px 14px;border:2px solid #000;border-radius:6px;background:#fff;cursor:pointer}
#modal button.ok{background:#000;color:#fff}
#nameTag div{font-size:11px}
#hudL{display:flex;flex-direction:column;align-items:flex-start;gap:6px}
#walkHint,#stateInfo,#spawnInfo{box-sizing:border-box;max-width:min(440px,45vw);position:relative;border-right:5px double #000}   /* v37 : largeurs par défaut ; le bord droit se tire (voir mkResize), la hauteur suit le contenu */
#walkHint{max-height:calc(100vh - 24px - var(--dockRest, calc(206px + var(--spawnH, 0px))));overflow:auto}   /* v40 : moins la hauteur de la fenêtre Arrivées, pour que la colonne tienne dans l'écran */
#walkHint,#stateInfo{user-select:text;-webkit-user-select:text;cursor:text}
#stateInfo{font-size:11px;padding:5px 9px}
#stateInfo div{margin:0}
#hudR{display:flex;flex-direction:column;align-items:flex-end;gap:6px;margin-top:6px;text-align:left}   /* v41 : pile de droite, sous Réglages (poussée quand Réglages s'ouvre) */
#walkHint.winFree,#stateInfo.winFree,#spawnInfo.winFree{position:fixed;z-index:15;margin:0}   /* v41 : fenêtre libre, posée à la souris */
.winDrag{opacity:.85;box-shadow:0 2px 10px #0006}
#spawnInfo{font-size:11px;padding:5px 9px;max-height:30vh;overflow:auto}   /* v40 : fenêtre Arrivées (touche L) */
#spawnBody button{display:block;width:100%;text-align:left;font:inherit;background:#fff;color:#000;border:1px solid #000;border-radius:4px;padding:1px 6px;margin:2px 0;cursor:pointer;text-decoration:underline}
.fold{display:block;width:100%;text-align:left;font:inherit;font-weight:bold;background:#ececec;color:#000;border:1px solid #000;border-radius:4px;padding:1px 6px;margin:0 0 4px;cursor:pointer}
.grp{margin:2px 0}.grp b{margin-right:8px}
#tilesInfo{font:11px/1.4 ui-monospace,Consolas,monospace;color:#000;white-space:pre-line}   /* 1.4.3 : un élément par ligne (tuiles, tuile sous l'avatar, vue d'ensemble) */
#tilesInfo.alone{position:fixed;left:12px;bottom:54px;background:#fffffff0;border:1px solid #000;border-radius:6px;padding:5px 9px}
#groundWait{position:fixed;left:50%;top:38%;transform:translateX(-50%);z-index:55;max-width:90%;text-align:center;font:14px/1.4 ui-monospace,Consolas,monospace;background:#000;color:#fff;border:2px solid #fff;border-radius:6px;padding:8px 16px}
#compass{position:fixed;top:8px;left:50%;transform:translateX(-50%);z-index:30;pointer-events:none;font:bold 13px/1.3 ui-monospace,Consolas,monospace;background:#fffffff0;color:#000;border:1px solid #000;border-radius:6px;padding:2px 10px}
/* v46 : commandes à l'écran. Ligne d'état (toujours visible), pavé de flèches 3 x 3, mode tactile (colonne de boutons, menu, gestes) */
#statusLine{position:fixed;left:50%;bottom:12px;transform:translateX(-50%);z-index:12;pointer-events:none;box-sizing:border-box;max-width:calc(100vw - 24px);font:12px/1.4 ui-monospace,Consolas,monospace;background:#fffffff0;color:#000;border:1px solid #000;border-radius:6px;padding:3px 12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#pad{position:fixed;left:50%;bottom:44px;transform:translateX(-50%);z-index:12;pointer-events:none;display:grid;grid-template-columns:repeat(3,var(--pb,44px));gap:var(--pg,4px)}
#pad>div{display:contents}
#pad>div[hidden]{display:none!important}
#pad button,#pad .gap{width:var(--pb,44px);height:var(--pb,44px)}
body:not(.touch) #padRun{font-size:10px;letter-spacing:-.3px}
#pad button{pointer-events:auto;display:grid;place-items:center;padding:0;font:11px/1.1 ui-monospace,Consolas,monospace;background:#fffffff0;color:#000;border:1px solid #000;border-radius:6px;cursor:pointer;touch-action:none;user-select:none;-webkit-user-select:none;-webkit-touch-callout:none}
#pad button.held,#pad button[aria-pressed=true]{border-width:3px;font-weight:bold}
#pad svg{width:55%;height:55%;pointer-events:none}
@media (max-width:1360px){body:not(.touch) #statusLine{top:40px;bottom:auto}body:not(.touch) #pad{bottom:12px}}
body.padOn:not(.touch) #lightAsk{bottom:192px}
body.padOn:not(.touch) #zonePrompt{bottom:220px}
#tcol{position:fixed;right:12px;bottom:20px;z-index:12;pointer-events:none;display:flex;flex-direction:column;gap:8px}
#tcol button,#tmenu button{pointer-events:auto;min-width:76px;min-height:48px;font:bold 12px/1.2 ui-monospace,Consolas,monospace;background:#fffffff0;color:#000;border:2px solid #000;border-radius:10px;padding:4px 6px;cursor:pointer;touch-action:manipulation;user-select:none;-webkit-user-select:none;-webkit-touch-callout:none}
#tcol button[aria-pressed=true],#tcol button[aria-expanded=true]{border-width:4px}
#tmenu{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:46;display:flex;flex-direction:column;gap:6px;min-width:220px;max-height:calc(100vh - 40px);overflow-y:auto;background:#fff;border:2px solid #000;border-radius:10px;padding:10px}
#tmenu button{text-align:left;font-weight:normal;border-width:1px;min-height:44px}
#tmenu button.close{font-weight:bold}
#tipBox{position:fixed;z-index:60;pointer-events:none;max-width:min(300px,80vw);background:#000;color:#fff;border-radius:6px;padding:5px 9px;font:12px/1.3 ui-monospace,Consolas,monospace;white-space:pre-line}
#walkHint .winX,#stateInfo .winX,#spawnInfo .winX{display:none;position:absolute;top:4px;right:14px;z-index:1;width:40px;height:40px;padding:0;font:bold 18px/1 ui-monospace,Consolas,monospace;background:#fff;color:#000;border:2px solid #000;border-radius:6px;cursor:pointer}
#chatTouch{display:flex;gap:6px;justify-content:flex-end;margin-top:6px}
#chatTouch button{font:bold 13px/1.2 ui-monospace,Consolas,monospace;min-height:44px;padding:4px 12px;background:#fff;color:#000;border:2px solid #000;border-radius:8px;cursor:pointer}
body.touch #walkHint .winX,body.touch #stateInfo .winX,body.touch #spawnInfo .winX{display:block}
body.touch .fold{min-width:200px}
body.touch #presence{max-width:calc(50vw - 50px);box-sizing:border-box}
body.touch #walkHint .fold,body.touch #stateInfo .fold,body.touch #spawnInfo .fold{min-height:44px;padding-right:56px}
body.touch #bar{display:none}
body.touch #dock{top:var(--ttop,140px);bottom:auto}
body.touch #walkHint,body.touch #stateInfo,body.touch #spawnInfo{max-width:min(440px,55vw)}
body.touch #walkHint{max-height:max(64px,calc(100vh - var(--ttop, 140px) - 220px - var(--dockRest, var(--spawnH, 0px))))}
body.touch #statusLine{top:var(--tstat,70px);bottom:auto;white-space:normal;text-align:center;max-width:calc(100vw - 20px)}
body.touch #pad{left:12px;bottom:20px;transform:none;--pb:56px;--pg:6px}
body.touch #pad button{border-width:2px;border-radius:10px;font-size:12px}
body.touch #pad button.held,body.touch #pad button[aria-pressed=true]{border-width:4px}
body.touch #zonePrompt{bottom:auto;top:var(--ttop,140px)}
body.touch #lightAsk{bottom:auto;top:var(--ttop,140px)}
body.touch #chat{top:var(--ttop,140px);bottom:auto;width:min(380px,42vw)}
body.touch #chatLog:not(.open){max-height:25vh;overflow:hidden;display:flex;flex-direction:column;justify-content:flex-end}
body.touch.chatOpen #chat{left:8px;right:8px;width:auto;top:auto;bottom:8px}
body.touch.chatOpen #chatLog.open{max-height:35vh}
body.touch.chatOpen #pad,body.touch.chatOpen #tcol{display:none}
body.touch #chatInput{font-size:16px}
@media (orientation:landscape){#tcol{display:grid;grid-template-columns:repeat(2,auto)}}
@media (orientation:landscape) and (max-height:500px){#tcol{grid-template-columns:repeat(3,auto)}body.touch #pad{--pb:44px;--pg:4px;bottom:12px}#tcol{bottom:12px}#tcol button{min-height:42px}}
#msg{position:fixed;inset:0;display:grid;place-items:center;font:14px ui-monospace,monospace;color:#123;pointer-events:none}
</style>
<script type="importmap">
__IMPORTMAP__
</script>
</head>
<body>
<script>
// ===== langue de la page (v36) =====
// Les textes sont dans src/i18n/<code>.json (un fichier par langue, clés stables, texte pur) ; build.py les intègre ici.
// Ajouter une langue = ajouter un fichier src/i18n/<code>.json (voir docs/fr/MANUEL.md § 21.9) : aucun code à toucher.
// Texte manquant dans une langue : anglais, puis français, puis la clé elle-même.
const I18N = {"en":{"_name":"English","common.auto":"Auto","common.no":"no","common.yes":"yes","core.ban.until":" (until {0})","core.clickable":" · click","core.diag.browser":"Browser","core.diag.btn":"Copy diagnostics","core.diag.cfgver":"region configuration from {0}","core.diag.copied":"Diagnostics copied","core.diag.date":"Date","core.diag.errors":"Recent errors and warnings ({0}):","core.diag.failed":"Failed tiles","core.diag.gpu":"Graphics card","core.diag.gpu.v":"{0} · WebGL {1} · textures up to {2} px","core.diag.cause.none":"nothing (on-demand rendering)","core.diag.cause.peers":"other visitors","core.diag.cause.sea":"animated sea","core.diag.cause.tiles":"tiles loading","core.diag.cause.walk":"walk mode","core.diag.fps":"Frames rendered per second (5 s)","core.diag.fps.v":"{0}; continuous rendering caused by: {1}","core.diag.light":"Light rendering","core.diag.light.nolimit":"no limit","core.diag.light.v":"resolution {0}%; max frames/s: {1}; overview only: {2}; tile radius: {3}; antialiasing: {4}","core.diag.lang":"Language, browser, keyboard","core.diag.image":"Image","core.diag.image.v":"zone {0}; target \"{1}\"; file read: {2}; caption: {3}","core.diag.image.txt":"text file","core.diag.image.name":"file name","core.diag.image.hidden":"hidden","core.diag.line":"{0}: {1}","core.diag.mem":"JavaScript memory","core.diag.mem.v":"{0} MB used of {1} MB","core.diag.na":"not available in this browser","core.diag.noerror":"none","core.diag.page":"Page","core.diag.presence":"Presence","core.diag.presence.conn":"Presence connection","core.diag.presence.conn.v":"was opened: {0}, last code: {1}, reason: {2}","core.diag.render":"Rendering (last frame)","core.diag.render.v":"{0} triangles, {1} draw calls, {2} geometries, {3} textures, {4} programs","core.diag.screen":"Window","core.diag.screen.v":"{0} x {1} px, density {2}, render x{3}","core.diag.state":"Displayed status:","core.diag.tiles":"Tiles","core.diag.tiles.v":"{0} ready of {1}, {2} loading, {3} failed","core.diag.times":"Tile timings","core.diag.times.v":"first ready at {0} s, last at {1} s; per tile (median / maximum): total {2} ms, download {3} ms, parsing {4} ms","core.diag.tip":"Copies the page's technical status and its latest errors, to paste into a help request. No server address, nickname or key is copied.","core.diag.title":"Web 3d diagnostics","core.diag.uptime":"open for {0} s","core.diag.version":"Version","core.dodge.log":"occupied arrival: moved {0} m (ring {1} m)","core.joined":"{0} joined","core.kind.ha":"Command","core.kind.portal":"Portal","core.kind.spawn":"Arrival","core.kind.url":"Web link","core.left":"{0} left","core.manual":"Full manual (online)","core.ov.ignored":"overview ignored (address refused):","core.ov.unavailable":"overview “{0}” unavailable ({1}): the region works without it","core.pick.building":"object: {0}","core.pick.material":"material: {0}","core.pick.mesh":"mesh: {0}","core.pick.noname":"(no name)","core.pick.none":"(none)","core.pick.parents":"parents: {0}","core.pick.point":"point (m): {0}","core.pick.size":"size (m): {0}","core.pres.closed":"connection opened then closed (code {0}){1}","core.pres.never":"connection never established (check address, port or firewall)","core.pres.secerr":"refused by the browser (https page with ws://, or forbidden port)","core.pres.refused.origin":"this page is not declared on this presence server","core.pres.refused.off":"the creator of this page is suspended on this presence server","core.pres.refused.room":"this page's room does not belong to its creator on this server","core.pres.refused.rooms":"its creator already has all allowed rooms open","core.pres.refused.unknown":"connection refused by the server","core.private":" (private)","core.spawn.label":"arrival: {0}","core.tile.badformat":"{0}: unexpected format (no “tiles” list)","core.tile.badpath":"tile address refused “{0}” (relative path, without .., without “:”, “?” or “#”)","core.tile.budget":"tile “{0}”: this tile alone exceeds the budget (tileMaxMB / tileMaxTriangles), loaded anyway (the avatar is on it)","core.tile.fail":"tile “{0}”: failed ({1}), will retry later","core.tile.faillog":"[tile] {0}: failed after {1} ms ({2})","core.tile.ignored":"tile ignored (invalid entry in {0}):","core.tile.off":"tile mode not enabled (no tiles field in the configuration)","core.tile.ready":"[tile] {0} ready: {1} MB · {2} triangles · wait before download {3} ms · download {4} ms · GLB parsing {5} ms · wait in the grid queue {6} ms · grid construction {7} ms of work ({8} ms elapsed) · total {9} ms","core.tip.cmd":"Command: {0}","core.tip.dist":"{0} m","core.tip.region":"Region: {0}","core.tip.thisregion":"this region","core.view.fps":"first person","core.view.free":"free camera","core.view.tps":"third person","core.zone.nogeom":"zone “{0}”: element “{1}” has no geometry","core.zone.nomesh":"zone “{0}”: element “{1}” not found in the model","core.zone.norefs":"zone “{0}” ignored: linked to the element “{1}”, which these tiles cannot resolve (tiles written without object references: split again with glb2tiles v32)","map.alert":"Arrival alert (sound and marker)","map.alert.last":"last arrival: {0}, {1}","map.alert.nosound":"sound unavailable in this browser","map.alert.on":"listening (checked every {0} s)","map.alert.wait":"sound starts at the first click on the page","map.arrived":"● arrival {0}","map.badurl":"(invalid address)","map.empty":"No region in the map.","map.footer":"glb2html {0}: each card is a link that takes you straight into the region, at its arrival point.","map.needserver":"Opened from disk, this map cannot read regions.json: serve it from a web server (http or https address).","map.nofile":"Cannot read {0}: no region to show.","map.novisitor":"no visitors","map.pseudo":"My nickname: ","map.pseudo.note":"remembered in this browser; passed on to the regions you visit","map.regions.one":"{0} region","map.regions.other":"{0} regions","map.showurl":"Show addresses","map.tip":"Click to enter the region (arrival: {0})","map.title":"World map","map.total":"Total: {0}","map.visitor":"Visitor","map.visitors.one":"{0} visitor","map.visitors.other":"{0} visitors","map.mixed.one":"{0} visitor, {1} walking","map.mixed.other":"{0} visitors, {1} walking","map.and":" and ","map.other.one":"{0} other","map.other.other":"{0} others","map.viewers":"global view: {0}","map.walking.one":"{0} walker","map.walking.other":"{0} walkers","page.about.btn":"About this region","page.about.close":"Close (Esc)","page.about.hide":"Don't show again","page.about.opt":"Show the about panel on entry","page.btn.center":"Recenter the view","page.btn.center.tip":"Back to the region's opening framing (global view)","page.btn.fly":"Fly / Land","page.btn.grab":"Capture the mouse","page.btn.help":"Help (H)","page.btn.help.expand":"Expand the help (H)","page.btn.help.hide":"Hide the help (H)","page.btn.home":"Back to the arrival point (R)","page.btn.map":"Map (M)","page.btn.map.ctrl":"Map (Ctrl+M)","page.btn.walk":"Walk (P)","page.chat.connecting":"Chat: connecting…","page.chat.disabled":"Chat is not enabled on this page: regenerate it with --presence-url (and run presence_server.py)","page.chat.error":"Chat offline: retrying…","page.chat.file.head":"Chat of the region “{0}” — saved on {1}","page.chat.file.note":"Messages received or sent since you arrived (local time | name | text). Nothing is kept on the server.","page.chat.full":"Chat: room full","page.chat.help":"↵ Enter: write (the input stays open, Esc closes it)","page.chat.mentions.go":"Go to the first","page.chat.mentions.one":"{0} message mentions you","page.chat.mentions.other":"{0} messages mention you","page.chat.names":"Nicknames","page.chat.offline":"Chat offline","page.chat.offline.sys":"Chat unavailable: offline","page.chat.older":"Older messages","page.chat.placeholder":"Message: Enter to send (stays open), Esc to close","page.chat.save":"Save the chat","page.chat.save.title":"Saves to a text file the messages seen since you arrived","page.chat.saved.one":"Chat saved: {0} message","page.chat.saved.other":"Chat saved: {0} messages","page.compass.dirs":"N NE E SE S SW W NW","page.compass.label":"Heading: {0}","page.cones.off":"Portal markers hidden (T to show them)","page.cones.on":"Portal markers shown (T to hide them)","page.copy.aria":"My position","page.copy.btn":"Copy my position","page.copy.fmt.aria":"Format of the copied position","page.err.load":"Loading error: {0}","page.feat":"This page — visitor settings: {0} · presence: {1} · chat: {2} · global view: {3} · names on click: {4} · glb2html {5}","page.feat.names.no":"no (option --names)","page.feat.panel.yes":"yes (button at the top right)","page.feat.presence.no":"no (option --presence-url)","page.feat.presence.yes":"yes (room {0})","page.feat.spectate.no":"no (option --spectate)","page.goto.aria":"Go to x, y, z","page.goto.bad":"Three numbers expected: x, y, z (e.g. 68.2, 39, -823.3), or an address containing #pos=x,y,z,heading","page.goto.btn":"Go","page.goto.frame.page":"frame of this page, model recentered","page.goto.frame.tiles":"frame of the original model","page.goto.label":"Go to x, y, z (m, {0}): ","page.goto.moved":"Target moved to {0}","page.goto.tp":"Teleporting to {0}","page.ground.loading":"Loading the ground…","page.help.about":"?: about this region","page.help.alt":"Alt + drag: orbit","page.help.center":"\"Recenter the view\" button: opening framing","page.help.chat.arrows":"arrows: in the text (after Esc: move around)","page.help.chat.enter":"Enter: write","page.help.chat.esc":"Esc: close","page.help.down":"Page Down or C: go down","page.help.end":"End or Alt + click: camera behind the avatar","page.help.enter":"P or F: enter","page.help.esc":"Esc: release","page.help.fly":"Home: fly / land (or the button)","page.help.g.chat":"Chat","page.help.g.fly":"Flight","page.help.g.mouse":"Mouse","page.help.g.move":"Movement","page.help.g.orbit":"Global view","page.help.g.page":"Page","page.help.g.view":"View","page.help.g.walk":"Walk","page.help.g.zones":"Zones","page.help.grab":"G: capture / release","page.help.h":"H: help","page.help.home":"R: back to the arrival point","page.help.i":"I: information","page.help.jump":"Space: jump","page.help.l":"L: arrivals (teleport)","page.help.landing":"double-click: choose the landing point","page.help.m":"M: first / third person","page.help.map":"M: world map","page.help.map.ctrl":"Ctrl+M: world map","page.help.mouse":"G or the “Capture the mouse” button, then mouse: look around (or drag with the button held)","page.help.move":"{0} / arrow keys","page.help.o":"O: settings","page.help.orbit.drag":"drag: rotate","page.help.orbit.pan":"right-click + drag: pan","page.help.orbit.reframe":"R: center on the arrival point","page.help.orbit.wheel":"wheel: zoom","page.help.quit":"P or F: leave the walk","page.help.run":"Shift or double-tap {0} {1} ↑ ↓: run","page.help.takeoff":"Page Up held on the ground: take off","page.help.title":"Help","page.help.tp":"double-click: teleport","page.help.up":"Page Up or Space held: go up","page.help.view":"V: change view","page.help.wheel":"wheel: camera distance (third person) or zoom (free camera)","page.help.zone.click":"click or E: signs and portals","page.help.zone.click.orbit":"click: signs and portals","page.help.zone.cone":"T: portal markers","page.help.zone.name":"click: name of the element","page.home.none":"No return point on this page","page.info.title":"Information / Status","page.key.done":"Identity replaced by the link's","page.key.modal":"This personal link replaces this browser's identity (reserved name, history) with its owner's. Replace?","page.landing.chosen":"Landing point chosen: press P (or F) to land there","page.layout.bad":"This file is not a window layout","page.layout.load":"Load a layout","page.layout.loaded":"Layout loaded","page.layout.reset":"Original layout","page.layout.reset.done":"Original layout restored","page.layout.save":"Save the layout","page.layout.saved":"Layout saved: disposition.json","page.layout.title":"Window layout","page.loading":"Loading…","page.map.badurl":"Invalid address: {0}","page.map.close":"Close (Esc)","page.map.count.one":"{0} walker","page.map.count.other":"{0} walkers","page.map.empty":"No region in the map.","page.map.here":"● you are here","page.map.novisitor":"no visitors","page.map.sep":" · ","page.map.tip":"Click to enter the region (arrival: {0})","page.map.tiphere":"You are in this region (a click closes the map)","page.map.title":"World map","page.map.visitors.one":"{0} visitor","page.map.visitors.other":"{0} visitors","page.map.mixed.one":"{0} visitor, {1} walking","page.map.mixed.other":"{0} visitors, {1} walking","page.map.and":" and ","page.map.other.one":"{0} other","page.map.other.other":"{0} others","page.map.viewers":"global view: {0}","page.modal.no":"Cancel","page.modal.yes":"Yes","page.mouse.captured":"captured (G or Esc to release it)","page.mouse.free":"free (G or the “Capture the mouse” button to grab it again)","page.mouse.idle":"G or the “Capture the mouse” button to capture it (otherwise drag, button held, to look around)","page.opt.anim":"Animated sea","page.opt.blink":"Message that mentions my nickname: the author's bubble blinks","page.opt.bold":"Message that mentions my nickname: in bold, preceded by “@”","page.opt.color":"Choose my avatar's color","page.opt.color.note":"Seen at once by the other visitors.\nUnchecked: a random color is used.","page.opt.compass":"Compass (heading at the top of the screen)","page.light.aa":"Antialiasing (on next load)","page.light.ask":"Rendering without a graphics card detected. Turn on light rendering?","page.light.close":"Close","page.light.done":"Light rendering on. Fine settings: button next to the box, in Settings.","page.light.fps":"Frames per second (at most)","page.light.m":"{0} m","page.light.no":"No","page.light.nolimit":"no limit","page.light.note":"Applied at once (except antialiasing) and remembered on this device.","page.light.ovonly":"Global view: overview only (details when walking)","page.light.pct":"{0}%","page.light.preset":"Recommended values","page.light.radius":"Detailed tile radius","page.light.scale":"Render resolution","page.light.title":"Light rendering: fine settings","page.opt.light":"Light rendering","page.opt.light.fine":"Fine settings…","page.opt.histmax":"History messages kept in the chat (20 to 2000)","page.opt.lang":"Language / Langue: ","page.opt.layout":"Keyboard layout: ","page.opt.link":"Copy my personal link","page.opt.link.aria":"Personal link","page.opt.link.note":"This link is a secret: whoever opens it takes your identity (your reserved name). Do not share it.","page.opt.note":"While walking, Esc releases the mouse so you can use this panel. Your choices are remembered on this device.","page.opt.reset":"Default values","page.opt.retina":"High resolution (sharper, heavier)","page.opt.sea":"Show the sea","page.opt.sound.cite":"Beep when a message mentions my nickname","page.opt.sound.msg":"Beep for every message when the page is not focused","page.opt.sound.join":"Sound when a visitor arrives","page.opt.sound.leave":"Sound when a visitor leaves","page.opt.sounds":"Sounds","page.opt.volume":"Volume: ","page.opt.wave":"Waves: ","page.opts":"Settings","page.pick.material":"material: {0}","page.pick.noname":"(no name)","page.pick.part":"part: {0}","page.pos.invalid":"#pos= ignored: x,y,z[,yaw] expected (numbers)","page.pres.banned":"access denied","page.pres.connecting":"connecting…","page.pres.count.one":"{0} visitor online","page.pres.count.other":"{0} visitors online","page.pres.error":"server unreachable ({0}), retrying…","page.pres.error.why":"presence interrupted ({0}): {1}, retrying…","page.pres.error.stopped":"presence interrupted ({0}): {1}, attempts stopped: reload the page to try again","page.pres.refused":"presence refused: {0} (reload the page once fixed)","page.pres.full":"room full","page.pres.kicked":"removed from the room (reload the page to come back)","page.pres.nametaken":"That name is already taken: you are “{0}”","page.pres.nobody":"nobody walking","page.pres.off":"offline (P or F: connect by walking)","page.pres.toast.banned":"Access denied","page.pres.toast.kicked":"Removed by the host","page.pres.walking.one":"{0} visitor walking","page.pres.walking.other":"{0} visitors walking","page.presence.label":"Nickname: ","page.shell.badregion":"region parameter refused “{0}” (a single file name, without / \\ : ? # or .., without a leading dot)","page.shell.error":"Error: {0}","page.shell.file":"This page is in modular mode: it must be served over http or https, not opened from the disk. To test it: python -m http.server in its folder, then http://localhost:8000/{0}","page.shell.network":"network","page.shell.noregion":"No region to open (\"{0}\" not found): add ?region=NAME to the address or create a default.json file containing {\"region\": \"NAME\"}.","page.shell.notfound":"Error: {0} not found ({1})","page.spawn.done":"Teleport: {0}","page.spawn.none":"No arrival point in this region","page.spawn.tip":"List of available teleport points (TP)","page.spawn.title":"Arrivals","page.state.kb":"Keyboard: {0} ({1})","page.state.kb.auto":"Keyboard: {0} ({1}), automatic","page.state.mode":"Mode: {0}","page.state.mode.fly":"flying","page.state.mode.walk":"on foot","page.state.mouse":"Mouse: {0}","page.state.pos.avatar":"Position avatar: x {0} · y {1} · z {2} m","page.state.pos.target":"Position target (global view): x {0} · y {1} · z {2} m","page.state.run":" · running","page.state.view":"View: {0}","page.state.view.global":"global (orbit)","page.tiles.error":"Tile “{0}”: {1} (will retry later)","page.tiles.failed":"{0} failed (will retry)","page.tiles.here":"Tile(s) under the avatar: {0}","page.tiles.loading":"{0} in progress","page.tiles.main.one":"Tiles: {0} loaded / {1} · {2} MB · {3} triangles","page.tiles.main.other":"Tiles: {0} loaded / {1} · {2} MB · {3} triangles","page.tiles.ov":"Overview (counted apart): {0} MB · {1} triangles","page.tiles.ov.failed":"Overview unavailable","page.toast.copied":"Copied","page.toast.copyfail":"Copy failed: the text is selected, press Ctrl+C","page.visitor":"Visitor","page.wait.long":" · long wait (heavy tile or slow network)","page.wait.region":"Loading the region…","page.wait.secs":" · {0} s","page.wait.tiles.one":"{1}/{0} tile ready","page.wait.tiles.other":"{1}/{0} tiles ready","page.win.h.tip":"Help: keys and controls of the current view.\nH: show, expand, hide.","page.win.i.tip":"Information / Status: view, mode, position, tiles, diagnostics.\nI: show, expand, hide.","page.win.l.tip":"Arrivals: list of available teleport points (TP).\nL: show, expand, hide.","page.win.move":"Click the title: collapse or expand. Drag the title: move (dropped on a stack, bottom left or below Settings, the window docks to it; elsewhere, it stays free). Double-click the title: back to its stack.","page.win.o.tip":"Page settings and window layout.\nO: open, close.","page.zone.badcmd":"Invalid command address: {0}","page.zone.badlink":"Invalid link: {0}","page.zone.cmdfail":"Sending failed: {0}","page.zone.cmdsent":"Command sent: {0}","page.zone.confirm":"Send the command “{0}”?","page.zone.noportal":"Portal without a valid destination: {0}","page.zone.nospawn":"Arrival point “{0}” not found in this region","page.zone.opening":"Opening: {0}","page.zone.prompt":"click or E: {0}","core.image.missing":"image not found: {0}","core.webgl.missing":"3D cannot be shown: WebGL is not available in this browser.\nWhen hardware acceleration is off, recent browsers (Edge, Chrome) now refuse software rendering.\nWays out: open this page in Firefox; or start Edge with the --enable-unsafe-swiftshader option (preferably in a profile kept for these pages); or turn hardware acceleration back on.\nTo check: edge://gpu (or chrome://gpu), WebGL line.","page.status.walk":"Walking","page.status.global":"Overview","page.status.pos":"x {0}  y {1}  z {2}","page.status.target":"target x {0}  y {1}  z {2}","page.pad.label":"Movement arrows","page.pad.hold":"Hold to keep going.","page.pad.fwd":"Forward ({0} or ↑)","page.pad.back":"Back ({0} or ↓)","page.pad.left":"Turn left (←)","page.pad.right":"Turn right (→)","page.pad.side.l":"Step left ({0})","page.pad.side.r":"Step right ({0})","page.pad.run":"Run","page.pad.run.tip":"Run (Shift): one click turns it on, another turns it off","page.pad.up":"Up (Page Up)","page.pad.down":"Down (Page Down or C)","page.pad.g.fwd":"Move the view forward","page.pad.g.back":"Move the view back","page.pad.g.left":"Move the view left","page.pad.g.right":"Move the view right","page.pad.g.tl":"Turn the view left","page.pad.g.tr":"Turn the view right","page.pad.g.in":"Zoom in (wheel)","page.pad.g.out":"Zoom out (wheel)","page.btn.pad":"Arrows (K)","page.btn.pad.off":"Arrows (K): hidden","page.btn.pad.tip":"Show or hide the on-screen arrows (K)","page.btn.walk.tip":"Start walking (F or P)","page.btn.fly.tip":"Fly or land (Home)","page.btn.grab.tip":"Capture the mouse to look around (the G key captures and releases it)","page.btn.home.tip":"Go back to the arrival point (R)","page.btn.help.tip":"Help: show, expand, hide (H)","page.btn.map.tip":"World map (M; Ctrl+M while walking)","page.t.label":"Touch controls","page.t.walk":"Walk","page.t.exit":"Exit","page.t.exit.tip":"Stop walking (F)","page.t.jump":"Jump","page.t.jump.tip":"Jump (Space)","page.t.fly":"Fly","page.t.land":"Land","page.t.view":"View","page.t.view.tip":"Change view: first person, third person, free camera (V)","page.t.chat":"Chat","page.t.chat.n":"Chat ({0})","page.t.chat.tip":"Open the chat (Enter)","page.t.pad":"Arrows","page.t.menu":"Menu","page.t.menu.tip":"Help, information, arrivals, map, full screen","page.menu.help":"Help","page.menu.info":"Information","page.menu.spawn":"Arrivals","page.menu.map":"World map","page.menu.home":"Back to arrival","page.menu.center":"Recenter the view","page.menu.full":"Full screen","page.menu.fullexit":"Exit full screen","page.menu.full.fail":"The browser refuses full screen","page.menu.close":"✕ Close the menu","page.win.close":"Close this window","page.chat.send":"Send","page.chat.send.tip":"Send the message (Enter)","page.chat.close":"✕ Close","page.chat.close.tip":"Close the chat input (Esc)","page.opt.pad":"On-screen arrows (K)","page.opt.touch":"Touch controls","page.opt.touch.on":"Yes","page.opt.touch.off":"No","page.opt.zonenums":"Image zone numbers (to find them)","page.help.k":"K: movement pad (on-screen arrows)","page.touch.look":"Drag your finger on the screen to look around","page.diag.touch":"Touch controls","page.diag.touch.v":"{0} (setting: {1}; touch screen detected: {2}; touch points: {3})","page.visits.title":"Visit log","page.visits.intro":"Summary of the visits to this region, for its creator. Enter the key the presence server host gave you.","page.visits.key":"Key: ","page.visits.show":"Show","page.visits.forget":"Forget the key","page.visits.forgotten":"Key forgotten by this browser.","page.visits.csv":"Download (CSV)","page.visits.close":"Close (Esc)","page.visits.wait":"Asking the presence server…","page.visits.nopres":"This page has no presence server: no visit is recorded.","page.visits.err.empty":"Enter the key.","page.visits.err.key":"Key refused for this region.","page.visits.err.rate":"Too many attempts: try again in a minute.","page.visits.err.off":"The presence server does not record visits (--visits option).","page.visits.err.old":"The presence server is too old for the visit log (v48 or newer).","page.visits.err.net":"The presence server does not answer.","page.visits.summary":"Room \"{0}\": visits {1}, distinct visitors {2}. Visits kept {3} days.","page.visits.summary.all":"Room \"{0}\": visits {1}, distinct visitors {2}. Visits kept without limit.","page.visits.none":"No visit recorded for this region.","page.visits.days":"Per day","page.visits.recent":"Visits of the last 30 days","page.visits.recent.cut":"(the {0} most recent)","page.visits.recent.none":"No visit in the last 30 days.","page.visits.c.date":"Date","page.visits.c.visits":"Visits","page.visits.c.visitors":"Distinct visitors","page.visits.c.total":"Total duration","page.visits.c.median":"Median duration","page.visits.c.walked":"With walk","page.visits.c.start":"Arrival","page.visits.c.dur":"Duration","page.visits.c.walk":"Walk","page.visits.c.name":"Nickname","page.visits.yes":"yes","page.visits.no":"no","page.visits.d.h":"{0} h {1} min","page.visits.d.m":"{0} min {1} s","page.visits.file":"visits","page.visits.open":"Visit log…","page.visits.open.tip":"For the region's creator: summary of the visits, with the key given by the presence server host"},"fr":{"_name":"Français","common.auto":"Auto","common.no":"non","common.yes":"oui","core.ban.until":" (jusqu'au {0})","core.clickable":" · clic","core.diag.browser":"Navigateur","core.diag.btn":"Copier le diagnostic","core.diag.cfgver":"configuration de la région en {0}","core.diag.copied":"Diagnostic copié","core.diag.date":"Date","core.diag.errors":"Erreurs et avertissements récents ({0}) :","core.diag.failed":"Tuiles en échec","core.diag.gpu":"Carte graphique","core.diag.gpu.v":"{0} · WebGL {1} · textures de {2} px au plus","core.diag.cause.none":"rien (rendu à la demande)","core.diag.cause.peers":"autres visiteurs","core.diag.cause.sea":"mer animée","core.diag.cause.tiles":"tuiles en chargement","core.diag.cause.walk":"promenade","core.diag.fps":"Images rendues par seconde (5 s)","core.diag.fps.v":"{0} ; rendu continu dû à : {1}","core.diag.light":"Rendu léger","core.diag.light.nolimit":"sans limite","core.diag.light.v":"résolution {0} % ; images/s au plus : {1} ; vue d'ensemble seule : {2} ; rayon des tuiles : {3} ; anticrénelage : {4}","core.diag.lang":"Langue, navigateur, clavier","core.diag.image":"Image","core.diag.image.v":"zone {0} ; cible « {1} » ; fichier lu : {2} ; légende : {3}","core.diag.image.txt":"fichier texte","core.diag.image.name":"nom du fichier","core.diag.image.hidden":"masquée","core.diag.line":"{0} : {1}","core.diag.mem":"Mémoire JavaScript","core.diag.mem.v":"{0} Mo utilisés sur {1} Mo","core.diag.na":"non disponible dans ce navigateur","core.diag.noerror":"aucun","core.diag.page":"Page","core.diag.presence":"Présence","core.diag.presence.conn":"Connexion de présence","core.diag.presence.conn.v":"s'est ouverte : {0}, dernier code : {1}, raison : {2}","core.diag.render":"Rendu (dernière image)","core.diag.render.v":"{0} triangles, {1} appels de dessin, {2} géométries, {3} textures, {4} programmes","core.diag.screen":"Fenêtre","core.diag.screen.v":"{0} x {1} px, densité {2}, rendu x{3}","core.diag.state":"État affiché :","core.diag.tiles":"Tuiles","core.diag.tiles.v":"{0} prêtes sur {1}, {2} en cours, {3} en échec","core.diag.times":"Durées des tuiles","core.diag.times.v":"première prête à {0} s, dernière à {1} s ; par tuile (médiane / maximum) : total {2} ms, téléchargement {3} ms, analyse {4} ms","core.diag.tip":"Copie l'état technique de la page et ses dernières erreurs, à coller dans une demande d'aide. Aucune adresse de serveur, aucun pseudo ni clé n'est copié.","core.diag.title":"Diagnostic Web 3d","core.diag.uptime":"ouverte depuis {0} s","core.diag.version":"Version","core.dodge.log":"arrivée occupée : décalé de {0} m (anneau {1} m)","core.joined":"{0} a rejoint","core.kind.ha":"Commande","core.kind.portal":"Portail","core.kind.spawn":"Arrivée","core.kind.url":"Lien web","core.left":"{0} est parti","core.manual":"Manuel complet (en ligne)","core.ov.ignored":"vue d'ensemble ignorée (adresse refusée) :","core.ov.unavailable":"vue d'ensemble « {0} » indisponible ({1}) : la région fonctionne sans elle","core.pick.building":"objet : {0}","core.pick.material":"matériau : {0}","core.pick.mesh":"mesh : {0}","core.pick.noname":"(sans nom)","core.pick.none":"(aucun)","core.pick.parents":"parents : {0}","core.pick.point":"point (m) : {0}","core.pick.size":"taille (m) : {0}","core.pres.closed":"connexion ouverte puis fermée (code {0}){1}","core.pres.never":"connexion jamais établie (adresse, port ou pare-feu à vérifier)","core.pres.secerr":"refusé par le navigateur (page https avec ws://, ou port interdit)","core.pres.refused.origin":"cette page n'est pas déclarée sur ce serveur de présence","core.pres.refused.off":"le créateur de cette page est suspendu sur ce serveur de présence","core.pres.refused.room":"le salon de cette page n'appartient pas à son créateur sur ce serveur","core.pres.refused.rooms":"son créateur a déjà tous les salons permis ouverts","core.pres.refused.unknown":"connexion refusée par le serveur","core.private":" (privé)","core.spawn.label":"arrivée : {0}","core.tile.badformat":"{0} : format inattendu (liste « tiles » absente)","core.tile.badpath":"adresse de tuiles refusée « {0} » (chemin relatif, sans .., sans « : », sans « ? » ni « # »)","core.tile.budget":"tuile « {0} » : le budget (tileMaxMB / tileMaxTriangles) est dépassé par cette seule tuile, chargée quand même (l'avatar est dessus)","core.tile.fail":"tuile « {0} » : échec ({1}), nouvelle tentative plus tard","core.tile.faillog":"[tuile] {0} : échec après {1} ms ({2})","core.tile.ignored":"tuile ignorée (entrée invalide dans {0}) :","core.tile.off":"mode tuiles non activé (champ tiles absent de la configuration)","core.tile.ready":"[tuile] {0} prête : {1} Mo · {2} triangles · attente avant téléchargement {3} ms · téléchargement {4} ms · analyse du GLB {5} ms · attente en file de grille {6} ms · construction de la grille {7} ms de travail ({8} ms écoulées) · total {9} ms","core.tip.cmd":"Commande : {0}","core.tip.dist":"{0} m","core.tip.region":"Région : {0}","core.tip.thisregion":"cette région","core.view.fps":"subjective","core.view.free":"caméra libre","core.view.tps":"troisième personne","core.zone.nogeom":"zone « {0} » : élément « {1} » sans géométrie","core.zone.nomesh":"zone « {0} » : élément « {1} » introuvable dans le modèle","core.zone.norefs":"zone « {0} » ignorée : liée à l'élément « {1} », ce que ces tuiles ne savent pas résoudre (tuiles écrites sans références d'objets : redécouper avec glb2tiles v32)","map.alert":"Surveillance des arrivées (son et repère)","map.alert.last":"dernière arrivée : {0}, {1}","map.alert.nosound":"son indisponible dans ce navigateur","map.alert.on":"à l'écoute (relevé toutes les {0} s)","map.alert.wait":"le son démarre au premier clic dans la page","map.arrived":"● arrivée {0}","map.badurl":"(adresse invalide)","map.empty":"Aucune région dans la carte.","map.footer":"glb2html {0} : chaque carte est un lien qui emmène directement dans la région, à son point d'arrivée.","map.needserver":"Ouverte depuis le disque, cette carte ne peut pas lire regions.json : servez-la par un serveur web (adresse en http ou https).","map.nofile":"Impossible de lire {0} : aucune région à afficher.","map.novisitor":"aucun visiteur","map.pseudo":"Mon pseudo : ","map.pseudo.note":"mémorisé dans ce navigateur ; transmis aux régions que tu visites","map.regions.one":"{0} région","map.regions.other":"{0} régions","map.showurl":"Afficher les adresses","map.tip":"Cliquer pour entrer dans la région (arrivée : {0})","map.title":"Carte des mondes","map.total":"Total : {0}","map.visitor":"Visiteur","map.visitors.one":"{0} visiteur","map.visitors.other":"{0} visiteurs","map.mixed.one":"{0} visiteur, dont {1} en promenade","map.mixed.other":"{0} visiteurs, dont {1} en promenade","map.and":" et ","map.other.one":"{0} autre","map.other.other":"{0} autres","map.viewers":"en vue globale : {0}","map.walking.one":"{0} promeneur","map.walking.other":"{0} promeneurs","page.about.btn":"À propos de la région","page.about.close":"Fermer (Échap)","page.about.hide":"Ne plus afficher","page.about.opt":"Afficher l'à propos à l'entrée","page.btn.center":"Recentrer la vue","page.btn.center.tip":"Revenir au cadrage d'ouverture de la région (vue globale)","page.btn.fly":"Voler / Atterrir","page.btn.grab":"Capturer la souris","page.btn.help":"Aide (H)","page.btn.help.expand":"Déployer l'aide (H)","page.btn.help.hide":"Masquer l'aide (H)","page.btn.home":"Retour à l'arrivée (R)","page.btn.map":"Carte (M)","page.btn.map.ctrl":"Carte (Ctrl+M)","page.btn.walk":"Promenade (P)","page.chat.connecting":"Chat : connexion…","page.chat.disabled":"Chat non activé sur cette page : régénère-la avec --presence-url (et lance presence_server.py)","page.chat.error":"Chat hors ligne : nouvelle tentative…","page.chat.file.head":"Chat de la région « {0} » — enregistré le {1}","page.chat.file.note":"Messages reçus ou envoyés depuis ton arrivée (heure locale | nom | texte). Rien n'est gardé côté serveur.","page.chat.full":"Chat : salon complet","page.chat.help":"↵ Entrée : écrire (la saisie reste ouverte, Échap la ferme)","page.chat.mentions.go":"Aller au premier","page.chat.mentions.one":"{0} message vous cite","page.chat.mentions.other":"{0} messages vous citent","page.chat.names":"Pseudos","page.chat.offline":"Chat hors ligne","page.chat.offline.sys":"Chat indisponible : hors ligne","page.chat.older":"Messages plus anciens","page.chat.placeholder":"Message : Entrée pour envoyer (reste ouvert), Échap pour fermer","page.chat.save":"Enregistrer le chat","page.chat.save.title":"Enregistre dans un fichier texte les messages vus depuis ton arrivée","page.chat.saved.one":"Chat enregistré : {0} message","page.chat.saved.other":"Chat enregistré : {0} messages","page.compass.dirs":"N NE E SE S SO O NO","page.compass.label":"Cap : {0}","page.cones.off":"Repères de portail masqués (T pour les afficher)","page.cones.on":"Repères de portail affichés (T pour les masquer)","page.copy.aria":"Ma position","page.copy.btn":"Copier ma position","page.copy.fmt.aria":"Format de la position copiée","page.err.load":"Erreur de chargement : {0}","page.feat":"Cette page — réglages visiteur : {0} · présence : {1} · chat : {2} · vue globale : {3} · noms au clic : {4} · glb2html {5}","page.feat.names.no":"non (option --names)","page.feat.panel.yes":"oui (bouton en haut à droite)","page.feat.presence.no":"non (option --presence-url)","page.feat.presence.yes":"oui (salon {0})","page.feat.spectate.no":"non (option --spectate)","page.goto.aria":"Aller à x, y, z","page.goto.bad":"Trois nombres attendus : x, y, z (ex. 68.2, 39, -823.3), ou une adresse contenant #pos=x,y,z,cap","page.goto.btn":"Aller","page.goto.frame.page":"repère de cette page, modèle recentré","page.goto.frame.tiles":"repère du modèle d'origine","page.goto.label":"Aller à x, y, z (m, {0}) : ","page.goto.moved":"Cible déplacée en {0}","page.goto.tp":"Téléportation vers {0}","page.ground.loading":"Chargement du sol…","page.help.about":"? : à propos de la région","page.help.alt":"Alt + glisser : orbiter","page.help.center":"bouton « Recentrer la vue » : cadrage d'ouverture","page.help.chat.arrows":"flèches : dans le texte (après Échap : se déplacer)","page.help.chat.enter":"Entrée : écrire","page.help.chat.esc":"Échap : fermer","page.help.down":"Page Bas ou C : descendre","page.help.end":"Fin ou Alt + clic : caméra derrière l'avatar","page.help.enter":"P ou F : entrer","page.help.esc":"Échap : libérer","page.help.fly":"Début : voler / atterrir (ou le bouton)","page.help.g.chat":"Chat","page.help.g.fly":"Vol","page.help.g.mouse":"Souris","page.help.g.move":"Déplacement","page.help.g.orbit":"Vue globale","page.help.g.page":"Page","page.help.g.view":"Vue","page.help.g.walk":"Promenade","page.help.g.zones":"Zones","page.help.grab":"G : capturer / libérer","page.help.h":"H : aide","page.help.home":"R : retour à l'arrivée","page.help.i":"I : informations","page.help.jump":"Espace : sauter","page.help.l":"L : arrivées (téléportation)","page.help.landing":"double-clic : choisir le point d'atterrissage","page.help.m":"M : subjective / 3e personne","page.help.map":"M : carte des mondes","page.help.map.ctrl":"Ctrl+M : carte des mondes","page.help.mouse":"G ou bouton « Capturer la souris », puis souris : regarder (ou glisser, bouton enfoncé)","page.help.move":"{0} / flèches","page.help.o":"O : réglages","page.help.orbit.drag":"glisser : tourner","page.help.orbit.pan":"clic droit + glisser : déplacer","page.help.orbit.reframe":"R : centrer sur l'arrivée","page.help.orbit.wheel":"molette : zoom","page.help.quit":"P ou F : quitter la promenade","page.help.run":"Maj ou double appui {0} {1} ↑ ↓ : courir","page.help.takeoff":"Page Haut maintenu au sol : décoller","page.help.title":"Aide","page.help.tp":"double-clic : se téléporter","page.help.up":"Page Haut ou Espace maintenu : monter","page.help.view":"V : changer de vue","page.help.wheel":"molette : distance de la caméra (3e personne) ou zoom (caméra libre)","page.help.zone.click":"clic ou E : panneaux et portails","page.help.zone.click.orbit":"clic : panneaux et portails","page.help.zone.cone":"T : repères de portail","page.help.zone.name":"clic : nom de l'élément","page.home.none":"Pas de point de retour sur cette page","page.info.title":"Informations / État","page.key.done":"Identité remplacée par celle du lien","page.key.modal":"Ce lien personnel remplace l'identité de ce navigateur (nom réservé, historique) par celle de son propriétaire. Remplacer ?","page.landing.chosen":"Point d'atterrissage choisi : appuie sur P (ou F) pour t'y poser","page.layout.bad":"Ce fichier n'est pas une disposition de fenêtres","page.layout.load":"Charger une disposition","page.layout.loaded":"Disposition chargée","page.layout.reset":"Disposition d'origine","page.layout.reset.done":"Disposition d'origine rétablie","page.layout.save":"Enregistrer la disposition","page.layout.saved":"Disposition enregistrée : disposition.json","page.layout.title":"Disposition des fenêtres","page.loading":"Chargement…","page.map.badurl":"Adresse invalide : {0}","page.map.close":"Fermer (Échap)","page.map.count.one":"{0} promeneur","page.map.count.other":"{0} promeneurs","page.map.empty":"Aucune région dans la carte.","page.map.here":"● vous êtes ici","page.map.novisitor":"aucun visiteur","page.map.sep":"\n","page.map.tip":"Cliquer pour entrer dans la région (arrivée : {0})","page.map.tiphere":"Vous êtes dans cette région (un clic ferme la carte)","page.map.title":"Carte des mondes","page.map.visitors.one":"{0} visiteur","page.map.visitors.other":"{0} visiteurs","page.map.mixed.one":"{0} visiteur, dont {1} en promenade","page.map.mixed.other":"{0} visiteurs, dont {1} en promenade","page.map.and":" et ","page.map.other.one":"{0} autre","page.map.other.other":"{0} autres","page.map.viewers":"en vue globale : {0}","page.modal.no":"Annuler","page.modal.yes":"Oui","page.mouse.captured":"capturée (G ou Échap pour la libérer)","page.mouse.free":"libre (G ou bouton « Capturer la souris » pour la reprendre)","page.mouse.idle":"G ou bouton « Capturer la souris » pour la capturer (sinon : glisser, bouton enfoncé, pour regarder)","page.opt.anim":"Mer animée","page.opt.blink":"Message qui cite mon pseudo : la bulle de l'auteur clignote","page.opt.bold":"Message qui cite mon pseudo : en gras, précédé de « @ »","page.opt.color":"Choisir la couleur de mon avatar","page.opt.color.note":"Vue aussitôt par les autres visiteurs.\nDécochée : couleur tirée au hasard.","page.opt.compass":"Boussole (cap en haut de l'écran)","page.light.aa":"Anticrénelage (au prochain chargement)","page.light.ask":"Rendu sans carte graphique détecté. Activer le rendu léger ?","page.light.close":"Fermer","page.light.done":"Rendu léger activé. Réglages fins : bouton à côté de la case, dans Réglages.","page.light.fps":"Images par seconde (au plus)","page.light.m":"{0} m","page.light.no":"Non","page.light.nolimit":"sans limite","page.light.note":"Appliqués aussitôt (sauf l'anticrénelage) et retenus sur cet appareil.","page.light.ovonly":"Vue globale : vue d'ensemble seule (détails en promenade)","page.light.pct":"{0} %","page.light.preset":"Valeurs préconisées","page.light.radius":"Rayon des tuiles détaillées","page.light.scale":"Résolution du rendu","page.light.title":"Rendu léger : réglages fins","page.opt.light":"Rendu léger","page.opt.light.fine":"Réglages fins…","page.opt.histmax":"Messages d'historique affichés dans le chat (20 à 2000)","page.opt.lang":"Langue / Language : ","page.opt.layout":"Disposition du clavier : ","page.opt.link":"Copier mon lien personnel","page.opt.link.aria":"Lien personnel","page.opt.link.note":"Ce lien est un secret : quiconque l'ouvre prend ton identité (ton nom réservé). Ne le partage pas.","page.opt.note":"En promenade, Échap libère la souris pour utiliser ce panneau. Tes choix sont mémorisés sur cet appareil.","page.opt.reset":"Valeurs d'origine","page.opt.retina":"Haute résolution (plus net, plus lourd)","page.opt.sea":"Afficher la mer","page.opt.sound.cite":"Bip quand un message cite mon pseudo","page.opt.sound.msg":"Bip à chaque message quand la page n'a pas le focus","page.opt.sound.join":"Son à l'arrivée d'un visiteur","page.opt.sound.leave":"Son au départ d'un visiteur","page.opt.sounds":"Sons","page.opt.volume":"Volume : ","page.opt.wave":"Vagues : ","page.opts":"Réglages","page.pick.material":"matériau : {0}","page.pick.noname":"(sans nom)","page.pick.part":"élément : {0}","page.pos.invalid":"#pos= ignoré : x,y,z[,yaw] attendus (nombres)","page.pres.banned":"accès interdit","page.pres.connecting":"connexion…","page.pres.count.one":"{0} visiteur en ligne","page.pres.count.other":"{0} visiteurs en ligne","page.pres.error":"serveur injoignable ({0}), nouvelle tentative…","page.pres.error.why":"présence interrompue ({0}) : {1}, nouvelle tentative…","page.pres.error.stopped":"présence interrompue ({0}) : {1}, essais arrêtés : recharge la page pour réessayer","page.pres.refused":"présence refusée : {0} (recharge la page une fois corrigé)","page.pres.full":"salon complet","page.pres.kicked":"éjecté du salon (recharge la page pour revenir)","page.pres.nametaken":"Ce nom est déjà pris : tu es « {0} »","page.pres.nobody":"personne en promenade","page.pres.off":"hors ligne (P ou F : te connecter en promenade)","page.pres.toast.banned":"Accès interdit","page.pres.toast.kicked":"Éjecté par l'hôte","page.pres.walking.one":"{0} visiteur en promenade","page.pres.walking.other":"{0} visiteurs en promenade","page.presence.label":"Pseudo : ","page.shell.badregion":"paramètre region refusé « {0} » (un seul nom de fichier, sans / \\ : ? # ni .., sans point au début)","page.shell.error":"Erreur : {0}","page.shell.file":"Cette page est en mode modulaire : elle doit être servie en http ou https, pas ouverte depuis le disque. Pour la tester : python -m http.server dans son dossier, puis http://localhost:8000/{0}","page.shell.network":"réseau","page.shell.noregion":"Aucune région à ouvrir (« {0} » est introuvable) : ajoute ?region=NOM à l'adresse ou crée un fichier default.json contenant {\"region\": \"NOM\"}.","page.shell.notfound":"Erreur : {0} introuvable ({1})","page.spawn.done":"Téléportation : {0}","page.spawn.none":"Pas de point d'arrivée dans cette région","page.spawn.tip":"Liste des points de téléportation disponibles (TP)","page.spawn.title":"Arrivées","page.state.kb":"Clavier : {0} ({1})","page.state.kb.auto":"Clavier : {0} ({1}), automatique","page.state.mode":"Mode : {0}","page.state.mode.fly":"en vol","page.state.mode.walk":"à pied","page.state.mouse":"Souris : {0}","page.state.pos.avatar":"Position avatar : x {0} · y {1} · z {2} m","page.state.pos.target":"Position cible (vue globale) : x {0} · y {1} · z {2} m","page.state.run":" · course","page.state.view":"Vue : {0}","page.state.view.global":"globale (orbite)","page.tiles.error":"Tuile « {0} » : {1} (nouvelle tentative plus tard)","page.tiles.failed":"{0} en échec (nouvelle tentative)","page.tiles.here":"Tuile(s) sous l'avatar : {0}","page.tiles.loading":"{0} en cours","page.tiles.main.one":"Tuiles : {0} chargée / {1} · {2} Mo · {3} triangles","page.tiles.main.other":"Tuiles : {0} chargées / {1} · {2} Mo · {3} triangles","page.tiles.ov":"Vue d'ensemble (à part) : {0} Mo · {1} triangles","page.tiles.ov.failed":"Vue d'ensemble indisponible","page.toast.copied":"Copié","page.toast.copyfail":"Copie impossible : le texte est sélectionné, fais Ctrl+C","page.visitor":"Visiteur","page.wait.long":" · attente longue (tuile lourde ou réseau lent)","page.wait.region":"Chargement de la région…","page.wait.secs":" · {0} s","page.wait.tiles.one":"{1}/{0} tuile prête","page.wait.tiles.other":"{1}/{0} tuiles prêtes","page.win.h.tip":"Aide : touches et commandes de la vue actuelle.\nH : afficher, déployer, masquer.","page.win.i.tip":"Informations / État : vue, mode, position, tuiles, diagnostic.\nI : afficher, déployer, masquer.","page.win.l.tip":"Arrivées : liste des points de téléportation disponibles (TP).\nL : afficher, déployer, masquer.","page.win.move":"Clic sur le titre : réduire ou déplier. Glisser le titre : déplacer (lâchée sur une pile, en bas à gauche ou sous Réglages, la fenêtre s'y accroche ; ailleurs, elle reste libre). Double-clic sur le titre : retour à sa pile.","page.win.o.tip":"Réglages de la page et disposition des fenêtres.\nO : ouvrir, fermer.","page.zone.badcmd":"Adresse de commande invalide : {0}","page.zone.badlink":"Lien invalide : {0}","page.zone.cmdfail":"Échec de l'envoi : {0}","page.zone.cmdsent":"Commande envoyée : {0}","page.zone.confirm":"Envoyer la commande « {0} » ?","page.zone.noportal":"Portail sans destination valide : {0}","page.zone.nospawn":"Point d'arrivée « {0} » introuvable dans cette région","page.zone.opening":"Ouverture : {0}","page.zone.prompt":"clic ou E : {0}","core.image.missing":"image introuvable : {0}","core.webgl.missing":"La 3D ne peut pas s'afficher : WebGL est indisponible dans ce navigateur.\nQuand l'accélération matérielle est coupée, les navigateurs récents (Edge, Chrome) refusent maintenant le rendu logiciel.\nPistes : ouvrir cette page dans Firefox ; ou lancer Edge avec l'option --enable-unsafe-swiftshader (de préférence dans un profil réservé à ces pages) ; ou réactiver l'accélération matérielle.\nPour vérifier : edge://gpu (ou chrome://gpu), ligne WebGL.","page.status.walk":"Promenade","page.status.global":"Vue globale","page.status.pos":"x {0}  y {1}  z {2}","page.status.target":"cible x {0}  y {1}  z {2}","page.pad.label":"Flèches de déplacement","page.pad.hold":"Maintenir pour continuer.","page.pad.fwd":"Avancer ({0} ou ↑)","page.pad.back":"Reculer ({0} ou ↓)","page.pad.left":"Tourner à gauche (←)","page.pad.right":"Tourner à droite (→)","page.pad.side.l":"Pas de côté à gauche ({0})","page.pad.side.r":"Pas de côté à droite ({0})","page.pad.run":"Courir","page.pad.run.tip":"Courir (Maj) : un clic l'allume, un clic l'éteint","page.pad.up":"Monter (Page Haut)","page.pad.down":"Descendre (Page Bas ou C)","page.pad.g.fwd":"Déplacer la vue en avant","page.pad.g.back":"Déplacer la vue en arrière","page.pad.g.left":"Déplacer la vue à gauche","page.pad.g.right":"Déplacer la vue à droite","page.pad.g.tl":"Tourner la vue à gauche","page.pad.g.tr":"Tourner la vue à droite","page.pad.g.in":"Rapprocher (molette)","page.pad.g.out":"Éloigner (molette)","page.btn.pad":"Flèches (K)","page.btn.pad.off":"Flèches (K) : cachées","page.btn.pad.tip":"Afficher ou cacher les flèches à l'écran (K)","page.btn.walk.tip":"Entrer en promenade (F ou P)","page.btn.fly.tip":"Voler ou atterrir (Début)","page.btn.grab.tip":"Capturer la souris pour regarder autour de soi (la touche G la capture et la libère)","page.btn.home.tip":"Revenir au point d'arrivée (R)","page.btn.help.tip":"Aide : afficher, déployer, masquer (H)","page.btn.map.tip":"Carte des mondes (M ; Ctrl+M en promenade)","page.t.label":"Commandes tactiles","page.t.walk":"Promenade","page.t.exit":"Sortir","page.t.exit.tip":"Sortir de la promenade (F)","page.t.jump":"Sauter","page.t.jump.tip":"Sauter (Espace)","page.t.fly":"Voler","page.t.land":"Atterrir","page.t.view":"Vue","page.t.view.tip":"Changer de vue : subjective, troisième personne, caméra libre (V)","page.t.chat":"Chat","page.t.chat.n":"Chat ({0})","page.t.chat.tip":"Ouvrir le chat (Entrée)","page.t.pad":"Flèches","page.t.menu":"Menu","page.t.menu.tip":"Aide, informations, arrivées, carte, plein écran","page.menu.help":"Aide","page.menu.info":"Informations","page.menu.spawn":"Arrivées","page.menu.map":"Carte des mondes","page.menu.home":"Retour à l'arrivée","page.menu.center":"Recentrer la vue","page.menu.full":"Plein écran","page.menu.fullexit":"Quitter le plein écran","page.menu.full.fail":"Le navigateur refuse le plein écran","page.menu.close":"✕ Fermer le menu","page.win.close":"Fermer cette fenêtre","page.chat.send":"Envoyer","page.chat.send.tip":"Envoyer le message (Entrée)","page.chat.close":"✕ Fermer","page.chat.close.tip":"Fermer la saisie du chat (Échap)","page.opt.pad":"Flèches à l'écran (K)","page.opt.touch":"Commandes tactiles","page.opt.touch.on":"Oui","page.opt.touch.off":"Non","page.opt.zonenums":"Numéros des zones image (repérage)","page.help.k":"K : pavé de déplacement (flèches à l'écran)","page.touch.look":"Glisse le doigt sur l'écran pour regarder autour de toi","page.diag.touch":"Commandes tactiles","page.diag.touch.v":"{0} (réglage : {1} ; écran tactile détecté : {2} ; points de contact : {3})","page.visits.title":"Journal des visites","page.visits.intro":"Résumé des visites de cette région, pour son créateur. Entre la clé que l'hôte du serveur de présence t'a donnée.","page.visits.key":"Clé : ","page.visits.show":"Afficher","page.visits.forget":"Oublier la clé","page.visits.forgotten":"Clé oubliée par ce navigateur.","page.visits.csv":"Télécharger (CSV)","page.visits.close":"Fermer (Échap)","page.visits.wait":"Demande au serveur de présence…","page.visits.nopres":"Cette page n'a pas de serveur de présence : aucune visite n'est enregistrée.","page.visits.err.empty":"Entre la clé.","page.visits.err.key":"Clé refusée pour cette région.","page.visits.err.rate":"Trop d'essais : réessaie dans une minute.","page.visits.err.off":"Le serveur de présence n'enregistre pas les visites (option --visits).","page.visits.err.old":"Le serveur de présence est trop ancien pour le journal des visites (v48 ou plus récent).","page.visits.err.net":"Le serveur de présence ne répond pas.","page.visits.summary":"Salon « {0} » : visites {1}, visiteurs distincts {2}. Visites gardées {3} jours.","page.visits.summary.all":"Salon « {0} » : visites {1}, visiteurs distincts {2}. Visites gardées sans limite.","page.visits.none":"Aucune visite enregistrée pour cette région.","page.visits.days":"Par jour","page.visits.recent":"Visites des 30 derniers jours","page.visits.recent.cut":"(les {0} plus récentes)","page.visits.recent.none":"Aucune visite ces 30 derniers jours.","page.visits.c.date":"Date","page.visits.c.visits":"Visites","page.visits.c.visitors":"Visiteurs distincts","page.visits.c.total":"Durée totale","page.visits.c.median":"Durée médiane","page.visits.c.walked":"Avec promenade","page.visits.c.start":"Arrivée","page.visits.c.dur":"Durée","page.visits.c.walk":"Promenade","page.visits.c.name":"Pseudo","page.visits.yes":"oui","page.visits.no":"non","page.visits.d.h":"{0} h {1} min","page.visits.d.m":"{0} min {1} s","page.visits.file":"visites","page.visits.open":"Journal des visites…","page.visits.open.tip":"Pour le créateur de la région : résumé des visites, avec la clé donnée par l'hôte du serveur de présence"}};
const I18N_LANGS = Object.keys(I18N).sort();
const I18N_KEY = 'glb2html_lang';
// v37 : paramètres après # ; le séparateur est & et # est accepté aussi (#name=A&lang=en = #name=A#lang=en). Fonction commune à tous les lecteurs du hash.
const hashParams = h => new URLSearchParams(String(h === undefined ? location.hash : h).replace(/^#/, '').replace(/#/g, '&'));
const i18nName = code => (I18N[code] && I18N[code]._name) || code;
const i18nMatch = tag => { const c = String(tag || '').toLowerCase().split(/[-_]/)[0]; return I18N[c] ? c : null; };
// choix de l'utilisateur : 'auto' ou un code de langue disponible. #lang=xx dans l'adresse est prioritaire et mémorisé.
const LANG_PREF = (() => {
  let pref = 'auto';
  try { const s = localStorage.getItem(I18N_KEY); if (s === 'auto' || I18N[s]) pref = s; } catch (_) {}
  try {
    const h = hashParams().get('lang');
    if (h !== null) { const v = h.toLowerCase() === 'auto' ? 'auto' : i18nMatch(h); if (v) { pref = v; try { localStorage.setItem(I18N_KEY, v); } catch (_) {} } }
  } catch (_) {}
  return pref;
})();
// langue effective : Auto = première langue de navigator.languages qui est disponible, sinon l'anglais
const LANG = (() => {
  if (LANG_PREF !== 'auto') return LANG_PREF;
  const list = (typeof navigator !== 'undefined' && ((navigator.languages && navigator.languages.length) ? navigator.languages : [navigator.language])) || [];
  for (const l of list) { const c = i18nMatch(l); if (c) return c; }
  return I18N.en ? 'en' : (I18N_LANGS[0] || 'en');
})();
const i18nHas = k => [LANG, 'en', 'fr'].some(l => I18N[l] && typeof I18N[l][k] === 'string');
function tr(key, ...a) {
  const v = [LANG, 'en', 'fr'].map(l => I18N[l] && I18N[l][key]).find(x => typeof x === 'string');
  const s = v === undefined ? key : v;
  return a.length ? s.replace(/\{(\d+)\}/g, (m, i) => (a[i] === undefined ? m : String(a[i]))) : s;
}
// pluriel : clé.one / clé.other (et .zero .two .few .many selon la langue) ; {0} = n
const i18nPR = (() => { try { return new Intl.PluralRules(LANG); } catch (_) { return null; } })();
function trn(key, n, ...a) {
  const cat = i18nPR ? i18nPR.select(n) : (n === 1 ? 'one' : 'other');
  return tr(i18nHas(key + '.' + cat) ? key + '.' + cat : key + '.other', n, ...a);
}
// langue des dates et des nombres (jj/mm/aaaa pour le français et l'anglais)
const i18nLocale = LANG === 'en' ? 'en-GB' : (LANG === 'fr' ? 'fr-FR' : LANG);
const i18nNum = (n, d) => Number(n).toLocaleString(LANG, { minimumFractionDigits: d, maximumFractionDigits: d });
// textes du document : data-i18n (contenu), data-i18n-title, data-i18n-ph (placeholder), data-i18n-aria (aria-label)
function applyI18n(root) {
  root = root || document;
  const sets = [['data-i18n', (e, v) => { e.textContent = v; }], ['data-i18n-title', (e, v) => e.setAttribute('title', v)], ['data-i18n-ph', (e, v) => e.setAttribute('placeholder', v)], ['data-i18n-aria', (e, v) => e.setAttribute('aria-label', v)]];
  for (const [attr, set] of sets) for (const e of root.querySelectorAll('[' + attr + ']')) set(e, tr(e.getAttribute(attr)));
  if (root === document) document.documentElement.lang = LANG;
}
// liste pour un sélecteur de langue : Auto puis chaque langue disponible, avec son propre nom
const i18nChoices = () => [['auto', tr('common.auto')]].concat(I18N_LANGS.map(c => [c, i18nName(c)]));
// change la langue : mémorise, retire #lang= de l'adresse (sinon il l'emporterait), recharge la page
function setLangPref(v) {
  try { localStorage.setItem(I18N_KEY, v === 'auto' || I18N[v] ? v : 'auto'); } catch (_) {}
  try { const u = new URL(location.href), hp = hashParams(u.hash); hp.delete('lang'); const hs = hp.toString(); history.replaceState(null, '', u.pathname + u.search + (hs ? '#' + hs : '')); } catch (_) {}
  location.reload();
}

</script>
<div id="view"></div>
<div id="msg" data-i18n="page.loading">Chargement…</div>
<div id="opts"><button id="optsBtn" hidden data-i18n="page.opts">Réglages</button><div id="optsPanel" hidden></div><div id="lightPanel" hidden></div><div id="hudR"></div></div>
<div id="aboutOverlay" hidden><div id="aboutBox" role="dialog" aria-modal="true" aria-labelledby="aboutTitle" tabindex="-1"><h2 id="aboutTitle"></h2><div id="aboutText"></div><button type="button" id="aboutClose"></button><button type="button" id="aboutHide"></button></div></div>
<div id="mapOverlay" hidden><div id="mapBox"><h2 data-i18n="page.map.title">Carte des mondes</h2><div id="mapGrid"></div><button id="mapClose" data-i18n="page.map.close">Fermer (Échap)</button></div></div>
<div id="visitsOverlay" hidden><div id="visitsBox" role="dialog" aria-labelledby="visitsTitle"><h2 id="visitsTitle" data-i18n="page.visits.title">Journal des visites</h2><p data-i18n="page.visits.intro">Résumé des visites de cette région, pour son créateur. Entre la clé que l'hôte du serveur de présence t'a donnée.</p><div id="visitsForm"><label for="visitsKey" data-i18n="page.visits.key">Clé : </label><input id="visitsKey" autocomplete="off" autocapitalize="characters" spellcheck="false" maxlength="40"> <button id="visitsGo" type="button" data-i18n="page.visits.show">Afficher</button><button id="visitsForget" type="button" hidden data-i18n="page.visits.forget">Oublier la clé</button></div><div id="visitsStatus" role="status" aria-live="polite"></div><div id="visitsOut"></div><button id="visitsCsv" type="button" hidden data-i18n="page.visits.csv">Télécharger (CSV)</button><button id="visitsClose" type="button" data-i18n="page.visits.close">Fermer (Échap)</button></div></div>
<div id="nameTag" hidden></div>
<div id="toast" hidden></div>
<div id="compass" role="status" hidden></div>
<div id="statusLine" role="status" aria-live="off" hidden><b id="statusMode"></b> <span id="statusRest"></span></div><div id="pad" role="group" hidden></div><div id="tcol" role="group" hidden></div><div id="tmenu" role="menu" hidden></div><div id="tipBox" role="tooltip" hidden></div>
<div id="zonePrompt" hidden></div>
<div id="groundWait" role="status" aria-live="polite" hidden data-i18n="page.ground.loading">Chargement du sol…</div>
<div id="tilesInfo" class="alone" hidden></div>
<div id="fade"></div>
<div id="modal" hidden><div><span id="modalText"></span><br><button class="ok" id="modalYes" data-i18n="page.modal.yes">Oui</button><button id="modalNo" data-i18n="page.modal.no">Annuler</button></div></div>
<div id="chat" hidden><div id="chatMentions" hidden><span id="mentCount"></span> <button id="mentGo" type="button" data-i18n="page.chat.mentions.go">Aller au premier</button></div><button id="chatOlder" type="button" hidden data-i18n="page.chat.older">Messages plus anciens</button><div id="chatLog"></div><div id="chatHelp"></div><button id="chatSave" type="button" data-i18n-title="page.chat.save.title" title="Enregistre dans un fichier texte les messages vus depuis ton arrivée" data-i18n="page.chat.save">Enregistrer le chat</button><div id="chatComplete" role="listbox" aria-label="Pseudos" data-i18n-aria="page.chat.names" hidden></div><input id="chatInput" maxlength="200" placeholder="Message : Entrée pour envoyer (reste ouvert), Échap pour fermer" data-i18n-ph="page.chat.placeholder" hidden></div>
<div id="presence" hidden><span data-i18n="page.presence.label">Pseudo : </span><input id="presenceName" maxlength="24" placeholder="Visiteur" data-i18n-ph="page.visitor"><div id="presenceStatus"></div></div>
<div id="dock"><div id="hudL"><div id="walkHint" hidden><button type="button" id="helpHead" class="fold" aria-expanded="true">▾ Aide</button><div id="helpBody"></div></div><div id="stateInfo" hidden><button type="button" id="stateHead" class="fold" aria-expanded="true">▾ État</button><div id="stateBody"></div></div><div id="spawnInfo" hidden><button type="button" id="spawnHead" class="fold" aria-expanded="true">▾ Arrivées</button><div id="spawnBody"></div></div></div>
<div id="bar"><button id="walkBtn" hidden></button><button id="flyBtn" hidden aria-pressed="false" data-i18n="page.btn.fly">Voler / Atterrir</button><button id="grabBtn" hidden data-i18n="page.btn.grab">Capturer la souris</button><button id="homeBtn" hidden data-i18n="page.btn.home">Retour à l'arrivée (R)</button><button id="centerBtn" type="button" hidden data-i18n="page.btn.center" data-i18n-title="page.btn.center.tip">Recentrer la vue</button><button id="helpBtn" hidden></button><button id="mapBtn" hidden data-i18n="page.btn.map">Carte (M)</button><button id="padBtn" type="button" hidden></button></div></div>
<script type="application/json" id="cfg">__CONFIG__</script>
<script type="application/octet-stream" id="glb">__GLB_B64__</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const C = JSON.parse(document.getElementById('cfg').textContent);
// v51 : adresse de présence ; « * » à la place du nom = le même nom que la page (même règle que presUrl de core.js) ; 0.0.0.0 -> 127.0.0.1
const presUrl = u => String(u || '').trim().replace(/^(wss?:\/\/)(\*|0\.0\.0\.0)(?=[:/]|$)/i, (m, p, h) => p + (h === '*' ? (location.hostname || '127.0.0.1') : '127.0.0.1'));
const msg = document.getElementById('msg');
applyI18n();

// ===== core partagé (viewer + export) =====
const FOLIAGE_KEYS = ['leaf','foliage','feuill','canopy','crown','branch','tree','bush','plant','palm','herbe','grass'];
const TRUNK_KEYS = ['bark','trunk','tronc','ecorce'];

function nameHas(name, tokens) {
  if (!name || !tokens.length) return false;
  const low = name.toLowerCase();
  const words = name.replace(/([a-z0-9])([A-Z])/g, '$1 $2').toLowerCase().split(/[^a-z0-9\u00e0-\u00ff]+/).filter(Boolean);
  const compact = words.join('');
  return tokens.some(t => t[0] === '=' ? low === t.slice(1) : (/[^a-z0-9\u00e0-\u00ff]/.test(t) ? low.includes(t) : (compact.startsWith(t) || words.some(w => w.startsWith(t)))));
}
// v36 : disposition du clavier. La marche garde les codes physiques (KeyW, KeyA, KeyS, KeyD : Z Q S D sur AZERTY, W A S D sur QWERTY) ;
// l'aide affiche les lettres RÉELLES. Réglage 'auto' (navigator.keyboard.getLayoutMap() si présent, sinon la langue du navigateur), 'azerty' ou 'qwerty'.
const KB = {
  pref: 'auto', detected: null, listeners: [],
  byLang() { const l = String((typeof navigator !== 'undefined' && (navigator.language || (navigator.languages || [])[0])) || ''); return /^fr(-(fr|be))?$/i.test(l) ? 'azerty' : 'qwerty'; },
  layout() { return this.pref === 'azerty' || this.pref === 'qwerty' ? this.pref : (this.detected || this.byLang()); },
  keys() { return this.layout() === 'azerty' ? { fwd: 'Z', left: 'Q', back: 'S', right: 'D' } : { fwd: 'W', left: 'A', back: 'S', right: 'D' }; },
  setPref(v) { this.pref = v === 'azerty' || v === 'qwerty' ? v : 'auto'; for (const f of this.listeners) { try { f(); } catch (_) {} } },
  detect() {
    try {
      if (typeof navigator !== 'undefined' && navigator.keyboard && navigator.keyboard.getLayoutMap) navigator.keyboard.getLayoutMap().then(m => {
        const w = m.get('KeyW'), q = m.get('KeyQ');
        const d = (w === 'z' || q === 'a') ? 'azerty' : ((w === 'w' && q === 'q') ? 'qwerty' : null);
        if (d && d !== this.detected) { this.detected = d; for (const f of this.listeners) { try { f(); } catch (_) {} } }
      }).catch(() => {});
    } catch (_) {}
  }
};
KB.detect();
// v39 : diagnostic à copier (bouton « Copier le diagnostic » de la page et du viewer) : état technique, durées des tuiles et 10 dernières erreurs.
// Jamais d'adresse de serveur (remplacée par ADRESSE) ni la partie # de l'adresse (pseudo, clé).
const DIAG = { errs: [] };
DIAG.mask = s => String(s).replace(/data:[^,\s]*,[^\s)]*/g, 'data:…').replace(/\b([a-z][a-z0-9+.-]*:\/\/)[^\/\s'"<>)]+/gi, '$1ADRESSE');
DIAG.str = x => {
  if (x && typeof x === 'object' && (x.message || x.stack)) {
    const at = String(x.stack || '').split('\n').map(l => l.trim()).filter(l => /^at |@/.test(l)).slice(0, 2);
    return String(x.message || x) + (at.length ? ' | ' + at.join(' | ') : '');
  }
  if (typeof x === 'string') return x;
  try { return JSON.stringify(x); } catch (_) { return String(x); }
};
DIAG.note = (kind, ...a) => {
  try {
    const s = DIAG.mask(a.map(DIAG.str).join(' ')).replace(/\b\d{1,3}(\.\d{1,3}){3}\b/g, 'ADRESSE').slice(0, 500);
    DIAG.errs.push((performance.now() / 1000).toFixed(1) + ' s [' + kind + '] ' + s);
    if (DIAG.errs.length > 10) DIAG.errs.shift();
  } catch (_) {}
};
if (typeof window !== 'undefined' && !window.__web3dDiag) {
  window.__web3dDiag = DIAG;
  addEventListener('error', e => {
    const t = e.target;
    if (t && t !== window && t.tagName) DIAG.note('load', t.tagName.toLowerCase() + ' ' + (t.currentSrc || t.src || t.href || ''));
    else DIAG.note('error', e.error || ((e.message || '') + (e.filename ? ' (' + e.filename + ':' + e.lineno + ')' : '')));
  }, true);
  addEventListener('unhandledrejection', e => DIAG.note('promise', e.reason));
  for (const k of ['error', 'warn']) { const f = console[k]; console[k] = function (...a) { DIAG.note(k, ...a); return f.apply(this, a); }; }
}
// v40 : manuel complet sur GitHub, dans la langue de la page (français, sinon anglais)
const manualUrl = () => 'https://github.com/Klaatou/Web_3d/blob/main/docs/' + (LANG === 'fr' ? 'fr/MANUEL.md' : 'en/MANUAL.md');
// nom du moteur de rendu WebGL (carte graphique, ou moteur logiciel)
function gpuName(r) {
  let gpu = '?';
  try {
    const gl = r.getContext(); gpu = String(gl.getParameter(gl.RENDERER) || '?');
    if (/^WebKit WebGL$|^Mozilla$/i.test(gpu)) { const ext = gl.getExtension('WEBGL_debug_renderer_info'); if (ext) gpu = String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)); }
  } catch (_) {}
  return gpu;
}
// v42 : rendu sans carte graphique (moteur logiciel) : la page propose le rendu léger
const softGpu = r => /Basic Render|SwiftShader|llvmpipe|softpipe|Software/i.test(gpuName(r));
// texte du diagnostic ; extra = { cfgVersion, lines } : version de la configuration de la région, lignes d'état propres à la page ou au viewer
function diagText(viewer, extra) {
  const x = extra || {}, L = (k, v) => tr('core.diag.line', k, v), out = [tr('core.diag.title')];
  const nb = (v, d) => (Number.isFinite(v) ? i18nNum(v, d || 0) : '?');   // nombres à la manière de la langue (virgule en français)
  out.push(L(tr('core.diag.version'), '__CORE_VERSION__' + (x.cfgVersion && x.cfgVersion !== '__CORE_VERSION__' ? ' ; ' + tr('core.diag.cfgver', x.cfgVersion) : '')));
  out.push(L(tr('core.diag.date'), new Date().toLocaleString(({ fr: 'fr-FR', en: 'en-GB' })[LANG]) + ' ; ' + tr('core.diag.uptime', nb(performance.now() / 1000))));
  out.push(L(tr('core.diag.page'), location.protocol + (location.host ? '//ADRESSE' : '//') + location.pathname + location.search));
  out.push(L(tr('core.diag.lang'), LANG + ' · ' + ((navigator.languages || []).join(',') || navigator.language || '?') + ' · ' + KB.layout().toUpperCase()));
  out.push(L(tr('core.diag.browser'), navigator.userAgent));
  const r = viewer && viewer.renderer;
  out.push(L(tr('core.diag.screen'), tr('core.diag.screen.v', innerWidth, innerHeight, nb(devicePixelRatio, 2), r ? nb(r.getPixelRatio(), 2) : '?')));
  if (r) {
    const gpu = gpuName(r);
    out.push(L(tr('core.diag.gpu'), tr('core.diag.gpu.v', gpu, r.capabilities && r.capabilities.isWebGL2 ? 2 : 1, r.capabilities ? r.capabilities.maxTextureSize : '?')));
    const i = r.info || {}, ri = i.render || {}, mi = i.memory || {};
    out.push(L(tr('core.diag.render'), tr('core.diag.render.v', ri.triangles, ri.calls, mi.geometries, mi.textures, (i.programs || []).length)));
  }
  if (viewer && viewer.cfg && viewer.renderStats) {
    // v42 : réglages du rendu léger en cours, images rendues sur les 5 dernières secondes et ce qui force le rendu continu
    const c = viewer.cfg, s = viewer.renderStats(), yn = v => (v ? tr('common.yes') : tr('common.no'));
    const rad = viewer.tiled && viewer.tilesState ? nb(viewer.tilesState().radius) + ' m' : '\u2014';
    out.push(L(tr('core.diag.light'), tr('core.diag.light.v', nb(Math.round((Number(c.pixelScale) > 0 ? Number(c.pixelScale) : 1) * 100)), Number(c.fpsMax) > 0 ? nb(Number(c.fpsMax)) : tr('core.diag.light.nolimit'), yn(!!c.ovOnly), rad, yn(c.antialias !== false))));
    const why = { sea: tr('core.diag.cause.sea'), peers: tr('core.diag.cause.peers'), walk: tr('core.diag.cause.walk'), tiles: tr('core.diag.cause.tiles') };
    out.push(L(tr('core.diag.fps'), tr('core.diag.fps.v', nb(s.rate, 1), s.causes.length ? s.causes.map(k => why[k]).join(', ') : tr('core.diag.cause.none'))));
  }
  if (viewer && viewer.imageDiag) for (const d of viewer.imageDiag().slice(0, 60)) out.push(L(tr('core.diag.image'), tr('core.diag.image.v', d.id, d.target || '\u2014', d.loaded || '\u2014', d.cap ? '\u00ab ' + d.cap + ' \u00bb (' + (d.src === 'txt' ? tr('core.diag.image.txt') : tr('core.diag.image.name')) + (d.vis ? '' : ', ' + tr('core.diag.image.hidden')) + ')' : '\u2014')));
  const pm = performance.memory;
  out.push(L(tr('core.diag.mem'), pm && pm.usedJSHeapSize ? tr('core.diag.mem.v', nb(pm.usedJSHeapSize / 1048576), nb(pm.jsHeapSizeLimit / 1048576)) : tr('core.diag.na')));
  if (viewer && viewer.tiled && viewer.tilesState) {
    try {
      const s = viewer.tilesState(), ok = (s.log || []).filter(l => l.ok);
      out.push(L(tr('core.diag.tiles'), tr('core.diag.tiles.v', s.loaded, s.total, s.loading, s.failed)));
      if (ok.length) {
        const med = k => { const v = ok.map(l => l[k]).filter(Number.isFinite).sort((a, b) => a - b); return v.length ? v[v.length >> 1] + ' / ' + v[v.length - 1] : '?'; };
        out.push(L(tr('core.diag.times'), tr('core.diag.times.v', nb(ok[0].at / 1000, 1), nb(ok[ok.length - 1].at / 1000, 1), med('totalMs'), med('downloadMs'), med('parseMs'))));
      }
      if ((s.failedFiles || []).length) out.push(L(tr('core.diag.failed'), s.failedFiles.slice(0, 5).join(', ') + (s.failedFiles.length > 5 ? ' …' : '')));
    } catch (_) {}
  }
  if ((x.lines || []).length) { out.push('', tr('core.diag.state')); for (const l of x.lines) out.push('  ' + l); }
  out.push('', tr('core.diag.errors', DIAG.errs.length));
  if (DIAG.errs.length) for (const e of DIAG.errs) out.push('  ' + e); else out.push('  ' + tr('core.diag.noerror'));
  return DIAG.mask(out.join('\n'));
}
// la lettre imprimée par la touche (minuscule) : M, comme toute touche dont la place change d'une disposition à l'autre, se reconnaît à cette lettre et non au code physique
const keyChar = e => (typeof e.key === 'string' && e.key.length === 1 ? e.key.toLowerCase() : '');
function parseIgnore(s) { return String(s || '').toLowerCase().split(/[,;]+/).map(x => x.trim()).filter(Boolean); }

function describeObject(o) {
  const sz = new THREE.Box3().setFromObject(o).getSize(new THREE.Vector3());
  const parents = []; for (let q = o.parent; q; q = q.parent) if (q.name) parents.push(q.name);
  const mats = (Array.isArray(o.material) ? o.material : [o.material]).map(m => m && m.name).filter(Boolean);
  const token = o.name || parents[0] || mats[0] || '';
  // objet racine = plus haut ancetre nomme (OAR : le prim racine du linkset, donc le nom du batiment) ; les enveloppes techniques (modele, tuiles) ne comptent pas
  // nom d'origine du fichier (userData.name) : le chargeur remplace les espaces par _ et ajoute _N aux doublons
  let building = '', rootNode = null; for (let q = o; q; q = q.parent) if (q.name && !(q.userData && q.userData.wrapper)) { building = (q.userData && q.userData.name) || q.name; rootNode = q; }
  return {
    name: token, mesh: o.name || '', building, isRoot: rootNode === o, parents, materials: mats, token, size: sz.toArray(),
    text: (building && rootNode !== o ? tr('core.pick.building', building) + '\n' : '') + tr('core.pick.mesh', o.name || tr('core.pick.noname')) + '\n' + tr('core.pick.parents', parents.slice(0, 3).join(' › ') || tr('core.pick.none')) + '\n' + tr('core.pick.material', mats.join(', ') || tr('core.pick.noname')) + '\n' + tr('core.pick.size', sz.toArray().map(v => v.toFixed(2)).join(' × '))
  };
}

// description d'un clic : nom de l'élément + point touché (x, y, z, 2 décimales)
function describePick(o, point) {
  const d = describeObject(o);
  if (point) { d.point = point; d.text += '\n' + tr('core.pick.point', point.map(v => v.toFixed(2)).join(', ')); }
  return d;
}

// Référence d'un élément pour le champ mesh d'une zone. Nom unique dans le modèle : le nom. Nom partagé par plusieurs objets
// (OAR : des dizaines de prims s'appellent pareil) : « nom#index », index = rang de l'objet parmi les objets de ce nom dans l'ordre
// de parcours (pré-ordre, enfants dans l'ordre du fichier). glb2html.py applique la même règle (resolve_mesh_ref).
function nodesNamed(root, name) { const out = []; root.traverse(o => { if (o.name === name) out.push(o); }); return out; }
function meshRefOf(root, o) {
  const same = nodesNamed(root, o.name);
  return same.length > 1 ? o.name + '#' + same.indexOf(o) : o.name;
}
// objets désignés par une référence : le nom exact d'abord (zones anciennes), sinon « base#index »
function resolveMeshRef(root, ref) {
  if (!root || !ref) return [];
  const exact = nodesNamed(root, ref);
  if (exact.length) return exact;
  const m = /^(.*)#(\d+)$/.exec(ref);
  if (!m) return [];
  const o = nodesNamed(root, m[1])[Number(m[2])];
  return o ? [o] : [];
}

function isIgnoredMesh(o, tokens) {
  if (!tokens.length) return false;
  for (let p = o; p; p = p.parent) if (nameHas(p.name, tokens)) return true;
  const mats = Array.isArray(o.material) ? o.material : [o.material];
  return mats.length > 0 && mats.every(m => !m || nameHas(m.name, tokens));
}

function isFoliageName(n) {
  n = (n || '').toLowerCase();
  return !TRUNK_KEYS.some(k => n.includes(k)) && FOLIAGE_KEYS.some(k => n.includes(k));
}

// Grille XZ de triangles (monde) pour sol et murs : exclut le feuillage.
// Générateur : rend la main toutes les quelques milliers de triangles (mode tuiles : construction par tranches, sans figer l'image) ;
// buildCollisionGrid l'exécute d'une traite (promenade ordinaire, résultat identique).
function buildCollisionGrid(root, cell = 3, tokens = []) {
  const it = collisionGridSteps(root, cell, tokens);
  let r; do { r = it.next(); } while (!r.done);
  return r.value;
}
function* collisionGridSteps(root, cell = 3, tokens = []) {
  let work = 0;
  const meshes = []; let total = 0;
  root.traverseVisible(o => {
    if (!o.isMesh || o.isInstancedMesh || o.isSkinnedMesh || !o.geometry || !o.geometry.attributes.position) return;
    if (tokens.length) for (let p = o; p; p = p.parent) if (nameHas(p.name, tokens)) return;
    const g = o.geometry, cnt = Math.floor((g.index ? g.index.count : g.attributes.position.count) / 3);
    const isArr = Array.isArray(o.material), mats = isArr ? o.material : [o.material];
    const skipMat = m => !m || isFoliageName(m.name) || nameHas(m.name, tokens);
    if (mats.every(skipMat)) return;
    let ranges;
    if (isArr && g.groups.length) {
      ranges = [];
      for (const gr of g.groups) {
        const m = mats[gr.materialIndex];
        if (skipMat(m)) continue;
        const s = Math.floor(gr.start / 3), e = Math.min(Math.floor((gr.start + gr.count) / 3), cnt);
        if (e > s) ranges.push([s, e]);
      }
    } else ranges = [[0, cnt]];
    for (const r of ranges) total += r[1] - r[0];
    meshes.push({ o, g, ranges });
  });
  const T = new Float32Array(total * 9); let t = 0;
  const v = new THREE.Vector3();
  for (const { o, g, ranges } of meshes) {
    o.updateWorldMatrix(true, false);
    const M = o.matrixWorld, p = g.attributes.position, ix = g.index;
    for (const [s, e] of ranges) for (let i = s; i < e; i++, t++) {
      if ((++work & 4095) === 0) yield;
      for (let k = 0; k < 3; k++) {
        v.fromBufferAttribute(p, ix ? ix.getX(i * 3 + k) : i * 3 + k).applyMatrix4(M);
        T[t * 9 + k * 3] = v.x; T[t * 9 + k * 3 + 1] = v.y; T[t * 9 + k * 3 + 2] = v.z;
      }
    }
  }
  const cells = new Map(), big = [];
  const key = (ix, iz) => (ix + 32768) * 65536 + (iz + 32768);
  for (let i = 0; i < total; i++) {
    if ((++work & 2047) === 0) yield;
    const b = i * 9;
    const minX = Math.min(T[b], T[b + 3], T[b + 6]), maxX = Math.max(T[b], T[b + 3], T[b + 6]);
    const minZ = Math.min(T[b + 2], T[b + 5], T[b + 8]), maxZ = Math.max(T[b + 2], T[b + 5], T[b + 8]);
    if (!(maxX - minX < 1e7) || !(maxZ - minZ < 1e7)) continue;
    const x0 = Math.floor(minX / cell), x1 = Math.floor(maxX / cell), z0 = Math.floor(minZ / cell), z1 = Math.floor(maxZ / cell);
    if ((x1 - x0 + 1) * (z1 - z0 + 1) > 400) { big.push(i); continue; }
    for (let ix = x0; ix <= x1; ix++) for (let iz = z0; iz <= z1; iz++) {
      const k = key(ix, iz); let a = cells.get(k);
      if (!a) { a = []; cells.set(k, a); }
      a.push(i);
    }
  }
  // hauteur du sol la plus haute <= y0 en (x,z), sinon null
  function ground(x, z, y0) {
    let best = -Infinity;
    const test = i => {
      const b = i * 9;
      const ax = T[b], ay = T[b + 1], az = T[b + 2], bx = T[b + 3], by = T[b + 4], bz = T[b + 5], cx = T[b + 6], cy = T[b + 7], cz = T[b + 8];
      const d = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz);
      if (Math.abs(d) < 1e-9) return;
      const l1 = ((bz - cz) * (x - cx) + (cx - bx) * (z - cz)) / d;
      const l2 = ((cz - az) * (x - cx) + (ax - cx) * (z - cz)) / d;
      const l3 = 1 - l1 - l2;
      if (l1 < -1e-6 || l2 < -1e-6 || l3 < -1e-6) return;
      const y = l1 * ay + l2 * by + l3 * cy;
      if (y <= y0 + 1e-4 && y > best) best = y;
    };
    const list = cells.get(key(Math.floor(x / cell), Math.floor(z / cell)));
    if (list) for (let i = 0; i < list.length; i++) test(list[i]);
    for (let i = 0; i < big.length; i++) test(big[i]);
    return best === -Infinity ? null : best;
  }
  // premier mur franchi par le rayon horizontal (dx,dz unitaire) sur dist : {t,nx,nz} ou null
  function wall(x, y, z, dx, dz, dist) {
    const ex = x + dx * dist, ez = z + dz * dist;
    const x0 = Math.floor(Math.min(x, ex) / cell), x1 = Math.floor(Math.max(x, ex) / cell);
    const z0 = Math.floor(Math.min(z, ez) / cell), z1 = Math.floor(Math.max(z, ez) / cell);
    let bestT = Infinity, bn = null;
    const test = i => {
      const b = i * 9;
      const ax = T[b], ay = T[b + 1], az = T[b + 2];
      const e1x = T[b + 3] - ax, e1y = T[b + 4] - ay, e1z = T[b + 5] - az;
      const e2x = T[b + 6] - ax, e2y = T[b + 7] - ay, e2z = T[b + 8] - az;
      const nx = e1y * e2z - e1z * e2y, ny = e1z * e2x - e1x * e2z, nz = e1x * e2y - e1y * e2x;
      const nl = Math.hypot(nx, ny, nz);
      if (nl < 1e-12 || Math.hypot(nx, nz) / nl < 0.3) return; // sols / pentes douces : pas des murs
      // Möller–Trumbore, direction (dx,0,dz)
      const px = -dz * e2y, py = dz * e2x - dx * e2z, pz = dx * e2y;
      const det = e1x * px + e1y * py + e1z * pz;
      if (Math.abs(det) < 1e-9) return;
      const inv = 1 / det, tx = x - ax, ty = y - ay, tz = z - az;
      const u = (tx * px + ty * py + tz * pz) * inv;
      if (u < 0 || u > 1) return;
      const qx = ty * e1z - tz * e1y, qy = tz * e1x - tx * e1z, qz = tx * e1y - ty * e1x;
      const w = (dx * qx + dz * qz) * inv;
      if (w < 0 || u + w > 1) return;
      const tt = (e2x * qx + e2y * qy + e2z * qz) * inv;
      if (tt >= 0 && tt <= dist && tt < bestT) { bestT = tt; bn = { t: tt, nx, nz }; }
    };
    for (let ix = x0; ix <= x1; ix++) for (let iz = z0; iz <= z1; iz++) {
      const list = cells.get(key(ix, iz));
      if (list) for (let i = 0; i < list.length; i++) test(list[i]);
    }
    for (let i = 0; i < big.length; i++) test(big[i]);
    return bn;
  }
  return { count: total, ground, wall };
}

const SEA_VERT = `
uniform float uTime, uAmp, uHoleRadius, uHoleFade;
uniform vec2 uHoleCenter;
varying float vWave;
void main(){
  vec3 pos = position;
  float edge = smoothstep(uHoleRadius - uHoleFade, uHoleRadius + uHoleFade, length(pos.xy - uHoleCenter));
  float w1 = sin(pos.x * 0.03 + uTime) * 0.8;
  float w2 = cos(pos.y * 0.025 + uTime * 0.7) * 0.6;
  float w3 = sin(pos.x * 0.012 + pos.y * 0.012 + uTime * 0.5) * 0.35;
  float wave = ((w1 + w2) * uAmp + w3 * uAmp * 0.6) * edge;
  pos.z += wave;
  vWave = wave;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
}`;
const SEA_FRAG = `
uniform vec3 uColor;
varying float vWave;
void main(){
  gl_FragColor = vec4(uColor + vWave * 0.03, 1.0);
  #include <colorspace_fragment>
}`;

function disposeObject(root) {
  root.traverse(o => {
    if (o.geometry) o.geometry.dispose();
    if (!o.material) return;
    for (const m of (Array.isArray(o.material) ? o.material : [o.material])) {
      if (!m) continue;
      for (const k in m) { const v = m[k]; if (v && v.isTexture) v.dispose(); }
      m.dispose();
    }
  });
}

// v43 : valeurs du repère des zones en anglais (dot, range, none) ; les anciennes (discret, portee, aucun) restent lues
const ZM_OLD = { discret: 'dot', portee: 'range', aucun: 'none' };
const zmNorm = v => ZM_OLD[v] || v;
// WebGL indisponible (acceleration materielle coupee : les navigateurs recents ne se replient plus sur le rendu logiciel) : un message clair a la place de « Chargement… »
function webglMissing(host) {
  const text = tr('core.webgl.missing'), m = document.getElementById('msg');
  if (m) { m.removeAttribute('data-i18n'); m.style.cssText += ';white-space:pre-line;text-align:center;padding:2em;pointer-events:auto'; m.textContent = text; return; }
  const d = document.createElement('div');
  d.style.cssText = 'position:fixed;inset:0;display:grid;place-items:center;z-index:99;background:#fff;color:#000;padding:2em;text-align:center;white-space:pre-line;font:15px/1.5 sans-serif';
  d.textContent = text; (host && host.parentNode || document.body).appendChild(d);
}
function createViewer(container, cfg0, loader) {
  const cfg = Object.assign({}, cfg0);
  if (cfg.zoneMarker) cfg.zoneMarker = zmNorm(cfg.zoneMarker);
  let onMouse = null, onView = null, onFly = null, onCfg = null, onWalk = null, onPick = null, onPresence = null, onChat = null, onHistory = null, onBlink = null, onBlinkEnd = null, onPeer = null, onName = null, spectateOn = false, pickOrbit = false, walking = false, linkLock = false;
  const W = { pos: new THREE.Vector3(), spawn: new THREE.Vector3(), vy: 0, grounded: true, yaw: 0, pitch: 0, keys: new Set(), jumpReq: false, drag: false, mouseFree: false, saved: null, grid: null,
    fly: false, flyFloor: undefined, view: 'fps', cam: new THREE.Vector3(), cyaw: 0, cpitch: 0,
    tyaw: 0, tpitch: 0,   // v35 : caméra à la troisième personne (orbite propre) ; W.yaw reste l'orientation de l'avatar
    run: new Set(), tap: {}, upT: 0, moved: false,
    tdist: (() => { let d = 4; try { const v = parseFloat(localStorage.getItem('glb2html_tpsDist')); if (v >= 1 && v <= 30) d = v; } catch (_) {} return d; })() };   // v35 : distance de la caméra à la troisième personne (1 à 30 m, mémorisée)
  let home = null;   // v33 : point de retour { pos, yaw, forF } (arrivée « default » ou cible de départ)
  let model = null, modelRot = 0, fit = 1, sea = null, seaMat = null, dirty = true, foliageMats = [];
  let seaCx = 0, seaCz = 0;   // centre de la mer : l'origine, ou le centre de la région en mode tuiles

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(cfg.skyColor);
  scene.fog = new THREE.Fog(cfg.skyColor, 1500, 4500);
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 5000);
  camera.position.set(0, 22, 45);

  let renderer;
  try { renderer = new THREE.WebGLRenderer({ antialias: cfg.antialias !== false, powerPreference: 'high-performance' }); } catch (e) { webglMissing(container); throw e; }   // v42 : anticrénelage fixé à la création du contexte (rendu léger : pris au chargement)
  renderer.sortObjects = false;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.shadowMap.enabled = false;
  container.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.fromArray(cfg.target);
  controls.enableDamping = true;
  controls.dampingFactor = 0.1;
  controls.minDistance = 1;
  controls.maxDistance = 2000;
  const BASE = { far: camera.far, fogNear: scene.fog.near, fogFar: scene.fog.far, maxDist: controls.maxDistance };   // rétablis par closeTiles()
  controls.maxPolarAngle = Math.PI / 2.05;
  controls.addEventListener('change', () => { dirty = true; });

  scene.add(new THREE.AmbientLight(0xffffff, 1.2));
  const sun = new THREE.DirectionalLight(0xffffff, 1.8); sun.position.set(120, 200, 80); scene.add(sun);
  const sun2 = new THREE.DirectionalLight(0xffffff, 0.7); sun2.position.set(-80, 100, -120); scene.add(sun2);
  const hemi = new THREE.HemisphereLight(cfg.skyColor, 0xffe8b0, 0.8); scene.add(hemi);

  function resize() {
    const w = container.clientWidth || innerWidth, h = container.clientHeight || innerHeight;
    const ps = Number(cfg.pixelScale), k = ps > 0 ? Math.min(1, Math.max(0.25, ps)) : 1;   // v42 : résolution du rendu (rendu léger) ; le navigateur agrandit l'image
    renderer.setPixelRatio((cfg.retina ? Math.min(Math.max(window.devicePixelRatio || 1, 2), 3) : 1) * k);
    renderer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    dirty = true;
  }
  new ResizeObserver(resize).observe(container);
  resize();

  function buildSea() {
    if (sea) { scene.remove(sea); sea.geometry.dispose(); seaMat.dispose(); sea = null; seaMat = null; }
    if (cfg.sea) {
      const seg = cfg.anim ? cfg.seaSegments : 1;
      const geo = new THREE.PlaneGeometry(cfg.seaSize, cfg.seaSize, seg, seg);
      if (cfg.anim) {
        seaMat = new THREE.ShaderMaterial({
          uniforms: {
            uTime: { value: 0 }, uAmp: { value: cfg.wave },
            uHoleRadius: { value: cfg.hole }, uHoleFade: { value: cfg.holeFade },
            uHoleCenter: { value: new THREE.Vector2(cfg.holeX, -cfg.holeZ) },
            uColor: { value: new THREE.Color(cfg.seaColor) }
          },
          vertexShader: SEA_VERT, fragmentShader: SEA_FRAG, side: THREE.FrontSide
        });
      } else {
        seaMat = new THREE.MeshStandardMaterial({ color: cfg.seaColor, roughness: 0.6, metalness: 0.1, side: THREE.DoubleSide });
      }
      seaMat.fog = false;
      seaMat.polygonOffset = true; seaMat.polygonOffsetFactor = -2; seaMat.polygonOffsetUnits = -2;
      sea = new THREE.Mesh(geo, seaMat);
      sea.rotation.x = -Math.PI / 2;
      sea.position.set(seaCx, cfg.seaY, seaCz);
      sea.frustumCulled = false;
      sea.renderOrder = -10;
      sea.userData.isSea = true;
      scene.add(sea);
    }
    dirty = true;
  }
  buildSea();

  // option solidMaterials : materiaux rendus opaques. Un materiau glTF en BLEND ne remplit pas le tampon de profondeur (GLTFLoader : depthWrite = false) :
  // les objets transparents derriere lui sont dessines par-dessus (on voit a travers un mur). « abc » : tout nom qui contient abc ; « =nom » : nom exact.
  function solidApply(m, tokens) {
    const n = (m.name || '').toLowerCase();
    const on = !!n && tokens.some(k => (k[0] === '=' ? n === k.slice(1) : n.includes(k)));
    if (on) {
      if (!m.userData.solidOrig) m.userData.solidOrig = { t: m.transparent, d: m.depthWrite, a: m.alphaTest };
      m.transparent = false; m.depthWrite = true; m.alphaTest = 0.5; m.needsUpdate = true;
    } else if (m.userData.solidOrig) {
      const o = m.userData.solidOrig; m.transparent = o.t; m.depthWrite = o.d; m.alphaTest = o.a; delete m.userData.solidOrig; m.needsUpdate = true;
    }
  }

  function fixMaterials(root, append) {
    if (!append) foliageMats = [];
    const solidTok = parseIgnore(cfg.solidMaterials);
    root.traverse(o => {
      if (!o.isMesh || !o.material) return;
      let foliageMesh = false;
      for (const m of (Array.isArray(o.material) ? o.material : [o.material])) {
        if (!m) continue;
        const n = (m.name || '').toLowerCase();
        const trunk = TRUNK_KEYS.some(k => n.includes(k));
        const foliage = !trunk && FOLIAGE_KEYS.some(k => n.includes(k));
        if (m.map) m.map.colorSpace = THREE.SRGBColorSpace;
        if (m.emissiveMap) m.emissiveMap.colorSpace = THREE.SRGBColorSpace;
        if (foliage) {
          foliageMesh = true;
          foliageMats.push(m);
          m.transparent = false; m.depthWrite = true; m.side = THREE.DoubleSide;
          m.alphaTest = cfg.foliageCutout; m.alphaToCoverage = true; m.fog = false;
        } else {
          if (trunk) m.side = THREE.FrontSide;
          solidApply(m, solidTok);
          if (m.emissive && !m.emissiveMap && m.emissive.getHex() !== 0 && (trunk || !(n.includes('light') || n.includes('emit')))) {
            m.emissive.setHex(0); m.emissiveIntensity = 0;
          }
        }
        if (m.isMeshStandardMaterial && !m.roughness) m.roughness = 0.75;
        m.needsUpdate = true;
      }
      o.castShadow = o.receiveShadow = false;
      o.renderOrder = foliageMesh ? 2 : 0;
    });
  }

  function frame(camDir = cfg.camDir, target = cfg.target, zoom = cfg.zoom) {
    const dir = new THREE.Vector3().fromArray(camDir).normalize();
    controls.target.fromArray(target);
    camera.position.copy(controls.target).addScaledVector(dir, fit * zoom);
    controls.update();
    dirty = true;
  }

  function setModel(root) {
    if (walking) walkStop();
    landY = null; landKey = '';
    if (model) { scene.remove(model); disposeObject(model); }
    model = root; root.userData.wrapper = true;
    fixMaterials(root);
    // rotation de la région autour de l'axe vertical : AVANT recentrage, boîte englobante, sol de promenade et capture de vignette
    modelRot = rotDeg();
    if (modelRot) root.quaternion.premultiply(new THREE.Quaternion().setFromAxisAngle(UPV, modelRot * Math.PI / 180));
    root.updateMatrixWorld(true);
    // centre = moyenne des origines de meshes, puis y+15
    const sum = new THREE.Vector3(), wp = new THREE.Vector3(); let cnt = 0;
    root.traverse(o => { if (o.isMesh) { o.getWorldPosition(wp); sum.add(wp); cnt++; } });
    const center = cnt ? sum.divideScalar(cnt) : new THREE.Box3().setFromObject(root).getCenter(new THREE.Vector3());
    root.position.sub(center); root.position.y += 15;
    root.updateMatrixWorld(true);
    root.traverse(o => { if (o.isMesh) { o.updateMatrix(); o.matrixAutoUpdate = false; } });
    scene.add(root);
    if (zones.length) { resolveLinks(); buildZones(); }
    const size = new THREE.Box3().setFromObject(root).getSize(new THREE.Vector3());
    fit = Math.max(size.x, size.y, size.z) / 2 / Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2) * 1.35 || 1;
    frame();
  }

  // 0, 90, 180 ou 270 (autre valeur : arrondie au quart de tour le plus proche)
  function rotDeg() { return ((Math.round((Number(cfg.rotate) || 0) / 90) * 90) % 360 + 360) % 360; }
  // aligne le modèle déjà chargé sur cfg.rotate : rotation autour de l'axe vertical passant par le centre de la région (origine)
  function applyRotation() {
    if (!model || TL.on) return;
    const d = rotDeg() - modelRot;
    if (!d) return;
    const q = new THREE.Quaternion().setFromAxisAngle(UPV, d * Math.PI / 180);
    model.quaternion.premultiply(q); model.position.applyQuaternion(q);
    modelRot = rotDeg();
    model.updateMatrixWorld(true);
    model.traverse(o => { if (o.isMesh) o.updateMatrix(); });
    if (zones.length) { resolveLinks(); buildZones(); }
    if (walking) W.grid = buildCollisionGrid(model, 3, parseIgnore(cfg.walkIgnore));
    landKey = ''; dirty = true;
  }

  async function loadBuffer(buf) {
    const gltf = await loader.parseAsync(buf, '');
    setModel(gltf.scene);
    return gltf;
  }

  // ---- mode tuiles (champ cfg.tiles) : région découpée par tools/glb2tiles.py (X.tiles.json, docs/fr/MANUEL.md § 17 bis)
  // Les tuiles dont la boîte est proche de l'avatar (en vue globale : de la cible) sont chargées, les lointaines déchargées. Repère = celui du
  // modèle d'origine (aucun recentrage) ; la rotation de la région est appliquée à la racine des tuiles. Une grille de collision par tuile.
  // Zones liées à un élément (champ mesh) : ignorées (la référence nom#index se calcule sur tout le modèle).
  const TL = { on: !!cfg.tiles, src: null, refs: false, refsKnown: false, refIndex: new Map(), linkDirty: false, linkSig: '', root: null, tiles: [], extent: null, inflight: 0, gridQ: [], pending: null, forced: null, forcedUntil: 0,
    waitT: -1e9, waitAt: null, waitSince: 0, anchor: null, log: [], lastUpd: 0, infoKey: '', onInfo: null, onError: null, lastError: '', radius: 150, margin: 60, maxBytes: 200 * 1048576, maxTri: 8e6, conc: 4 };
  // v33 : budget de temps (ms par image) de la construction des grilles de collision : normal, et généreux pour la tuile que l'avatar (ou l'arrivée demandée) attend
  const GRID_MS = 6, GRID_MS_PRIO = 40;
  // vue d'ensemble (X.overview.glb, champ « overview » de X.tiles.json) : un nœud par fichier de tuile, masqué dès que la tuile détaillée est affichée
  // (groupe ajouté à la racine des tuiles) et réaffiché quand elle est déchargée. Jamais utilisée pour les collisions, le sol ni le budget des tuiles.
  const OV = { root: null, bytes: 0, tri: 0, cells: 0, state: 'none' };
  const ovSync = t => { if (t.ov) { const v = !t.grp; if (t.ov.visible !== v) { t.ov.visible = v; dirty = true; } } };
  const ovCells = () => OV.root ? OV.root.children.filter(c => c.visible) : [];
  const TILE_M = 0.5;   // tolérance (m) des tests « le point est dans la boîte de la tuile »
  const safeRel = p => typeof p === 'string' && p !== '' && p.length < 400 && !/^[\/\\]/.test(p) && !/[\\:?#\u0000-\u001f]/.test(p) && !p.split('/').some(s => s === '' || s === '..');
  const relUrl = (p, base) => new URL(p.split('/').map(encodeURIComponent).join('/'), base);
  // source des fichiers d'une région en tuiles : http relatif à la page (coquille, viewer avec ?tiles=) ; le viewer en fournit une autre pour un dossier choisi
  const urlSource = () => ({
    async json(rel) { const r = await fetch(relUrl(rel, location.href).href, { cache: 'no-store' }); if (!r.ok) throw new Error(rel + ' : HTTP ' + r.status); return r.json(); },
    async buf(rel, signal) { const r = await fetch(relUrl(rel, location.href).href, signal ? { signal } : {}); if (!r.ok) throw new Error('HTTP ' + r.status); return r.arrayBuffer(); }
  });
  // références d'objets (extras.ref écrit par glb2tiles v32) : index des nœuds des tuiles chargées, pour les zones liées à un objet
  const refPieces = ref => (TL.refIndex.get(ref) || []).length;
  const zoneOff = z => TL.on && TL.refs && z.mesh && z.type !== 'spawn' && !zoneLink.has(z.id);   // zone liée dont la tuile n'est pas chargée : absente
  function refsAdd(t) {
    t.refObjs = [];
    t.grp.traverse(o => {
      const r = o.userData && o.userData.ref;
      if (typeof r !== 'string') return;
      let l = TL.refIndex.get(r); if (!l) TL.refIndex.set(r, l = []);
      l.push(o); t.refObjs.push(o);
    });
    if (t.refObjs.length) TL.linkDirty = true;
  }
  function refsRemove(t) {
    if (!t.refObjs) return;
    for (const o of t.refObjs) {
      const r = o.userData.ref, l = TL.refIndex.get(r);
      if (l) { const i = l.indexOf(o); if (i >= 0) l.splice(i, 1); if (!l.length) TL.refIndex.delete(r); }
    }
    if (t.refObjs.length) TL.linkDirty = true;
    t.refObjs = null;
  }
  const linkSignature = () => zones.filter(z => z.mesh && z.type !== 'spawn').map(z => z.id + ':' + refPieces(z.mesh)).join('|');
  function relinkZones() {
    if (!TL.on || !TL.refs) return;
    const sig = linkSignature();
    if (sig === TL.linkSig) return;
    resolveLinks(); buildZones();
    if (selId) zoneSelect(selId);
  }
  // fin du mode tuiles (le viewer ouvre un autre fichier) : tout est libéré, caméra, brouillard et distance maximale d'origine
  function closeTiles() {
    if (walking) walkStop();
    for (const t of TL.tiles) { if (t.ac) { try { t.ac.abort(); } catch (e) {} t.ac = null; } }
    if (TL.root) { for (const t of TL.tiles) if (t.grp) tileUnload(t); scene.remove(TL.root); if (model === TL.root) model = null; }
    if (OV.root) { scene.remove(OV.root); disposeObject(OV.root); }
    OV.root = null; OV.bytes = OV.tri = OV.cells = 0; OV.state = 'none';
    TL.tiles = []; TL.root = null; TL.gridQ = []; TL.pending = null; TL.forced = null; TL.anchor = null; TL.waitAt = null; TL.refIndex.clear(); TL.refs = false; TL.refsKnown = false; TL.linkSig = ''; TL.src = null;
    TL.on = false;
    scene.fog.near = BASE.fogNear; scene.fog.far = BASE.fogFar; camera.far = BASE.far; camera.updateProjectionMatrix(); controls.maxDistance = BASE.maxDist;
    seaCx = seaCz = 0; if (sea) sea.position.set(0, cfg.seaY, 0);
    resolveLinks(); buildZones(); landY = null; landKey = ''; dirty = true;
  }
  const inTile = (t, x, z, m) => x >= t.box[0] - m && x <= t.box[2] + m && z >= t.box[1] - m && z <= t.box[3] + m;
  const tileDist = (t, f) => Math.hypot(Math.max(t.box[0] - f.x, 0, f.x - t.box[2]), Math.max(t.box[1] - f.z, 0, f.z - t.box[3]));
  // grille composite : sol et murs des seules tuiles prêtes ; pending(x,z) = une tuile dont la boîte contient ce point n'est pas encore prête
  const TG = {
    tiled: true,
    get count() { let n = 0; for (const t of TL.tiles) if (t.state === 'ready' && t.grid) n += t.grid.count; return n; },
    ground(x, z, y0) {
      let best = null;
      for (const t of TL.tiles) {
        if (t.state !== 'ready' || !t.grid || !inTile(t, x, z, TILE_M)) continue;
        const g = t.grid.ground(x, z, y0);
        if (g !== null && (best === null || g > best)) best = g;
      }
      return best;
    },
    wall(x, y, z, dx, dz, dist) {
      const ex = x + dx * dist, ez = z + dz * dist, x0 = Math.min(x, ex) - TILE_M, x1 = Math.max(x, ex) + TILE_M, z0 = Math.min(z, ez) - TILE_M, z1 = Math.max(z, ez) + TILE_M;
      let best = null;
      for (const t of TL.tiles) {
        if (t.state !== 'ready' || !t.grid || t.box[0] > x1 || t.box[2] < x0 || t.box[1] > z1 || t.box[3] < z0) continue;
        const h = t.grid.wall(x, y, z, dx, dz, dist);
        if (h && (!best || h.t < best.t)) best = h;
      }
      return best;
    },
    pending(x, z) { for (const t of TL.tiles) if (t.state !== 'ready' && inTile(t, x, z, TILE_M)) return true; return false; }
  };
  function disposeTile(grp) {
    const texs = new Set();
    grp.traverse(o => {
      if (o.skeleton) o.skeleton.dispose();
      if (o.material) for (const m of (Array.isArray(o.material) ? o.material : [o.material])) if (m) for (const k in m) { const v = m[k]; if (v && v.isTexture) texs.add(v); }
    });
    disposeObject(grp);
    for (const t of texs) { const im = t.image; if (im && typeof im.close === 'function') { try { im.close(); } catch (e) {} } }   // libère aussi la mémoire CPU des images décodées
  }
  // tuiles qui contiennent le point (x, z) ; à défaut la plus proche dans le rayon de chargement
  function tilesAt(x, z) {
    const set = TL.tiles.filter(t => inTile(t, x, z, TILE_M));
    if (set.length) return set;
    const n = TL.tiles.map(t => [tileDist(t, { x, z }), t]).filter(a => a[0] <= TL.radius).sort((a, b) => a[0] - b[0])[0];
    return n ? [n[1]] : [];
  }
  const tileDone = t => t.state === 'ready' || t.state === 'failed';
  const anchorOpen = () => !!TL.anchor && TL.anchor.tiles.some(t => !tileDone(t));   // l'arrivée demandée attend encore une tuile
  // v33 : ce que « Chargement du sol… » attend : la tuile du téléport en attente, de l'arrivée demandée ou du point où l'avatar est arrêté
  function waitInfo(now) {
    let at, since, kind, set;
    if (TL.pending) { at = TL.pending.at; since = TL.pending.t0 || TL.waitSince; kind = 'pending'; set = tilesAt(at.x, at.z); }
    else if (anchorOpen()) { at = TL.anchor; since = TL.anchor.t0; kind = 'anchor'; set = TL.anchor.tiles; }
    else if (now - TL.waitT < 600 && TL.waitAt) { at = TL.waitAt; since = TL.waitSince; kind = 'walk'; set = tilesAt(at.x, at.z); }
    else return null;
    return { kind, ready: set.filter(t => t.state === 'ready').length, total: set.length, secs: Math.max(0, Math.floor((now - since) / 1000)), files: set.map(t => t.file) };
  }
  function tilesStatus() {
    let loaded = 0, loading = 0, failed = 0, bytes = 0, got = 0, tri = 0;
    for (const t of TL.tiles) {
      // 1.4.4 : bytes = poids de l'index (budget, inchangé) ; got = poids réellement reçu (affichage), bytes tant que la tuile n'est pas arrivée
      if (t.state === 'ready') { loaded++; bytes += t.bytes; got += t.got || t.bytes; tri += t.tri; }
      else if (t.state === 'loading' || t.state === 'building') { loading++; bytes += t.bytes; got += t.got || t.bytes; tri += t.tri; }
      else if (t.state === 'failed') failed++;
    }
    const now = performance.now(), wait = waitInfo(now);
    // v1.4.2 : tuile(s) sous l'avatar (nom du fichier, sans dossier) ; vide hors promenade
    const here = walking ? TL.tiles.filter(t => inTile(t, W.pos.x, W.pos.z, TILE_M)).map(t => String(t.file).split('/').pop()) : [];
    return { total: TL.tiles.length, loaded, loading, failed, bytes, got, tri, here, waiting: !!TL.pending || now - TL.waitT < 600 || !!(wait && wait.kind === 'anchor'), wait, ov: { state: OV.state, bytes: OV.bytes, tri: OV.tri } };
  }
  function tilesInfo() {
    const s = tilesStatus(), w = s.wait, key = [s.loaded, s.loading, s.failed, s.bytes, s.got, s.tri, s.waiting ? 1 : 0, OV.state, OV.bytes, OV.tri, w ? w.kind + w.ready + '/' + w.total + ':' + w.secs : '', s.here.join(',')].join('|');
    if (key === TL.infoKey) return;
    TL.infoKey = key;
    if (TL.onInfo) TL.onInfo(s);
  }
  function tileFail(t, e) {
    t.state = 'failed'; t.fails = (t.fails || 0) + 1; t.retryAt = performance.now() + Math.min(30000, 3000 * Math.pow(2, t.fails - 1));
    const m = e && e.message ? e.message : String(e);
    console.warn(tr('core.tile.fail', t.file, m));
    const L = { file: t.file, ok: false, error: m, ms: Math.round(performance.now() - (t.tStart || performance.now())), at: Math.round(performance.now()) };
    TL.log.push(L); if (TL.log.length > 500) TL.log.shift();
    console.log(tr('core.tile.faillog', t.file, L.ms, m));
    if (TL.onError) TL.onError(t.file, m);
  }
  // v33 : une ligne par tuile qui devient prête (à coller dans le chat pour diagnostiquer un démarrage lent)
  function tileReady(t) {
    const now = performance.now();
    const L = { file: t.file, ok: true, bytes: t.got || t.bytes, tri: t.tri, startWaitMs: Math.round(t.tStart - (t.tWant === undefined ? t.tStart : t.tWant)), downloadMs: Math.round(t.dlMs), parseMs: Math.round(t.parseMs),
      queueMs: Math.round(t.qWait || 0), gridMs: Math.round(t.gridCpu || 0), gridWallMs: Math.round(now - t.qAt), totalMs: Math.round(now - (t.tWant === undefined ? t.tStart : t.tWant)), startAt: Math.round(t.tStart), at: Math.round(now) };
    TL.log.push(L); if (TL.log.length > 500) TL.log.shift();
    console.log(tr('core.tile.ready', t.file, (L.bytes / 1048576).toFixed(1), L.tri, L.startWaitMs, L.downloadMs, L.parseMs, L.queueMs, L.gridMs, L.gridWallMs, L.totalMs));
  }
  function tileUnload(t) {
    if (t.ac) { try { t.ac.abort(); } catch (e) {} t.ac = null; }
    const i = TL.gridQ.indexOf(t); if (i >= 0) TL.gridQ.splice(i, 1);
    if (t.grp) {
      TL.root.remove(t.grp);
      const ms = new Set(); t.grp.traverse(o => { if (o.material) for (const m of (Array.isArray(o.material) ? o.material : [o.material])) if (m) ms.add(m); });
      foliageMats = foliageMats.filter(m => !ms.has(m));
      refsRemove(t);
      disposeTile(t.grp); t.grp = null;
    }
    ovSync(t);
    t.grid = null; t.gen = null; t.state = 'idle'; t.tWant = undefined; dirty = true;
  }
  async function tileStart(t) {
    const ac = new AbortController();
    t.state = 'loading'; t.ac = ac; TL.inflight++;
    t.tStart = performance.now(); t.gridCpu = 0; t.qWait = 0;
    try {
      const buf = await TL.src.buf(t.path, ac.signal);
      if (t.ac !== ac) return;
      t.dlMs = performance.now() - t.tStart; t.got = buf.byteLength;
      const tp = performance.now();
      const gltf = await loader.parseAsync(buf, '');
      t.parseMs = performance.now() - tp;
      if (t.ac !== ac) { disposeTile(gltf.scene); return; }
      const grp = gltf.scene;
      grp.name = 'tile:' + t.file; grp.userData.wrapper = true;
      fixMaterials(grp, true);
      TL.root.add(grp); grp.updateMatrixWorld(true);
      grp.traverse(o => { if (o.isMesh) { o.updateMatrix(); o.matrixAutoUpdate = false; } });
      t.grp = grp; t.state = 'building';
      refsAdd(t);
      ovSync(t);   // même bloc synchrone que l'ajout du groupe : jamais d'image avec les deux, ni avec aucun des deux
      t.gen = collisionGridSteps(grp, 3, parseIgnore(cfg.walkIgnore));   // construite par tranches (tilesTick)
      t.qAt = performance.now(); t.qFirst = true;
      TL.gridQ.push(t);
      dirty = true;
    } catch (e) {
      if (t.ac === ac) { t.ac = null; tileFail(t, e); }
    } finally { TL.inflight--; tilesInfo(); }
  }
  function tilesFocus(now) {
    if (TL.pending) return TL.pending.at;
    if (walking) return { x: W.pos.x, z: W.pos.z };
    if (TL.anchor) return TL.anchor;   // v33 : l'arrivée demandée reste la référence jusqu'à la promenade (plus de délai de 4 s)
    if (TL.forced && now < TL.forcedUntil) return TL.forced;
    return { x: controls.target.x, z: controls.target.z };
  }
  function tilesUsage() {
    let bytes = 0, tri = 0, n = 0;
    for (const t of TL.tiles) if (t.state === 'loading' || t.state === 'building' || t.state === 'ready') { bytes += t.bytes; tri += t.tri; n++; }
    return { bytes, tri, n };
  }
  // choisit les tuiles à charger (rayon, plus proches d'abord) et à décharger (rayon + marge, puis budget : les plus lointaines d'abord)
  function tilesUpdate(now) {
    if (!TL.root) return;
    TL.lastUpd = now;
    // l'ancre (arrivée demandée) est lâchée dès que la cible de la vue globale a bougé : l'utilisateur regarde ailleurs
    if (TL.anchor && Math.hypot(controls.target.x - TL.anchor.tx, controls.target.z - TL.anchor.tz) > 1) TL.anchor = null;
    // v42 : rendu léger, « vue d'ensemble seule » : hors promenade (et sans promenade ni téléport en attente), aucune tuile détaillée
    if (cfg.ovOnly && (OV.state === 'ready' || OV.state === 'loading') && !walking && !TL.pending) {
      releaseAnchor(); TL.forced = null;
      for (const t of TL.tiles) if (t.state !== 'idle' && t.state !== 'failed') tileUnload(t);
      tilesInfo(); return;
    }
    const f = tilesFocus(now);
    for (const t of TL.tiles) t.d = tileDist(t, f);
    for (const t of TL.tiles) if (t.state !== 'idle' && t.state !== 'failed' && t.d > TL.radius + TL.margin) tileUnload(t);
    let want = TL.tiles.filter(t => t.d <= TL.radius && (t.state === 'idle' || (t.state === 'failed' && now >= t.retryAt))).sort((a, b) => a.d - b.d);
    for (const t of want) if (t.tWant === undefined) t.tWant = now;
    // v33 : tant que les tuiles de l'arrivée demandée ne sont pas prêtes, aucune autre tuile ne démarre
    if (anchorOpen()) want = want.filter(t => TL.anchor.tiles.includes(t));
    for (const t of want) {
      if (TL.inflight >= TL.conc) break;
      let u = tilesUsage();
      while (u.bytes + t.bytes > TL.maxBytes || u.tri + t.tri > TL.maxTri) {
        let v = null;
        for (const q of TL.tiles) if ((q.state === 'loading' || q.state === 'building' || q.state === 'ready') && q.d > t.d + 1 && (!v || q.d > v.d)) v = q;
        if (!v) break;
        tileUnload(v); u = tilesUsage();
      }
      if (u.bytes + t.bytes > TL.maxBytes || u.tri + t.tri > TL.maxTri) {
        if (t.d > 0 && u.n > 0) continue;   // plus de place : on attend qu'une tuile plus lointaine parte
        console.warn(tr('core.tile.budget', t.file));
      }
      tileStart(t);
    }
    tilesInfo();
  }
  // point dont la tuile est attendue : le téléport en attente, l'avatar, l'arrivée demandée
  function prioPoint() {
    if (TL.pending) return TL.pending.at;
    if (walking) return { x: W.pos.x, z: W.pos.z };
    return TL.anchor || null;
  }
  function releaseAnchor() { if (TL.anchor) { TL.anchor = null; TL.infoKey = ''; tilesInfo(); } }
  const markWait = (x, z) => { const n = performance.now(); if (n - TL.waitT > 600) TL.waitSince = n; TL.waitT = n; TL.waitAt = { x, z }; };
  function tilesPendingCheck() {
    const p = TL.pending;
    if (!p || TG.pending(p.at.x, p.at.z)) return;
    TL.pending = null;
    if (p.kind === 'walk') walkStart(p.opts); else teleportTo(p.pos, p.yaw);
    tilesInfo();
  }
  function tilesTick(now) {
    if (!TL.root) return;
    const t0 = performance.now();
    // v33 : la grille de la tuile qui contient l'avatar (ou l'arrivée / le téléport attendus) passe avant les autres, avec un budget par image plus généreux
    const foc = prioPoint();
    while (TL.gridQ.length) {
      let k = 0;
      if (foc) { const i = TL.gridQ.findIndex(q => inTile(q, foc.x, foc.z, TILE_M)); if (i > 0) k = i; }
      const t = TL.gridQ[k], prio = !!foc && inTile(t, foc.x, foc.z, TILE_M);
      if (performance.now() - t0 >= (prio ? GRID_MS_PRIO : GRID_MS)) break;
      const s0 = performance.now();
      if (t.qFirst) { t.qFirst = false; t.qWait = s0 - t.qAt; }
      let r;
      try { r = t.gen.next(); } catch (e) { TL.gridQ.splice(k, 1); tileUnload(t); tileFail(t, e); continue; }
      t.gridCpu += performance.now() - s0;
      if (r.done) { TL.gridQ.splice(k, 1); t.grid = r.value; t.gen = null; t.state = 'ready'; t.fails = 0; t.tWant = undefined; dirty = true; landKey = ''; tileReady(t); tilesPendingCheck(); tilesInfo(); }
    }
    if (TL.linkDirty) { TL.linkDirty = false; relinkZones(); }
    if (now - TL.lastUpd > 250) tilesUpdate(now);
    if (TL.waitT > 0 || TL.pending || TL.anchor) tilesInfo();
  }
  // vue d'ensemble : chargée avant les tuiles ; un échec n'est pas fatal (la région fonctionne alors comme en v30)
  async function loadOverview(ov, dir) {
    OV.state = 'loading';
    try {
      const buf = await TL.src.buf(dir + ov.file);
      const gltf = await loader.parseAsync(buf, '');
      const g = gltf.scene; g.name = 'overview'; g.userData.wrapper = true;
      g.quaternion.copy(TL.root.quaternion);
      const byFile = new Map(TL.tiles.map(t => [t.file, t]));
      // v52 : le chemin ecrit dans le .overview.glb (extras.tile) est celui du decoupage ; apres un renommage des dossiers et de l'index il ne correspond plus :
      // repli sur le nom du fichier de la tuile (T_niveau_i_j.glb), unique dans une region (sinon pas de repli : la cellule reste visible)
      const baseOf = p => String(p || '').split('/').pop(), byBase = new Map(), dupBase = new Set();
      for (const t of TL.tiles) { const b = baseOf(t.file); if (byBase.has(b)) dupBase.add(b); else byBase.set(b, t); }
      let tri = 0, cells = 0;
      for (const c of g.children) {
        c.traverse(o => { if (o.isMesh) { o.matrixAutoUpdate = false; o.castShadow = o.receiveShadow = false; const gm = o.geometry; tri += gm.index ? gm.index.count / 3 : gm.attributes.position.count / 3; } });
        const tn = c.userData && c.userData.tile;
        const t = byFile.get(tn) || (dupBase.has(baseOf(tn)) ? undefined : byBase.get(baseOf(tn)));   // extras.tile : GLTFLoader retire « / », « . » et les espaces des noms de nœuds
        if (t) { t.ov = c; c.name = t.file; cells++; }
      }
      g.updateMatrixWorld(true);
      g.traverse(o => { if (o.isMesh) o.updateMatrix(); });
      scene.add(g);
      OV.root = g; OV.bytes = buf.byteLength; OV.tri = Math.round(tri); OV.cells = cells; OV.state = 'ready';
      for (const t of TL.tiles) ovSync(t);
      dirty = true;
    } catch (e) {
      OV.state = 'failed';
      console.warn(tr('core.ov.unavailable', ov.file, e && e.message ? e.message : e));
    }
  }
  // charge X.tiles.json puis les tuiles autour du point de départ ; rend la main quand les tuiles qui contiennent ce point sont prêtes
  // (ou en échec). opts : spawn (id d'arrivée du lien, sinon « default »), radius (?radius=)
  async function loadTiles(rel, opts) {
    opts = opts || {};
    if (opts.force) {
      if (TL.root) closeTiles();
      if (model) { if (walking) walkStop(); scene.remove(model); disposeObject(model); model = null; }   // un GLB unique ouvert avant
      TL.on = true;
    }   // le viewer ouvre une région en tuiles sans champ « tiles » dans une configuration
    if (!TL.on) throw new Error(tr('core.tile.off'));
    if (!safeRel(rel)) throw new Error(tr('core.tile.badpath', rel));
    // source des fichiers : adresses http relatives à la page (coquille, ou viewer avec ?tiles=), ou fichiers choisis dans un dossier (viewer)
    TL.src = opts.source || urlSource();
    const doc = await TL.src.json(rel);
    if (!doc || !Array.isArray(doc.tiles)) throw new Error(tr('core.tile.badformat', rel));
    const dir = rel.lastIndexOf('/') >= 0 ? rel.slice(0, rel.lastIndexOf('/') + 1) : '';
    TL.refs = !!doc.nodeRefs; TL.refsKnown = true; TL.refIndex.clear(); TL.linkSig = '';
    const num = (v, d, lo, hi) => { v = Number(v); return Number.isFinite(v) ? Math.min(hi, Math.max(lo, v)) : d; };
    TL.radius = num(opts.radius, num(cfg.tileRadius, 150, 10, 5000), 10, 5000);
    TL.margin = num(cfg.tileMargin, 60, 0, 5000);
    TL.maxBytes = num(cfg.tileMaxMB !== undefined ? cfg.tileMaxMB : cfg.tileMaxMo, 200, 1, 1e5) * 1048576;
    TL.maxTri = num(cfg.tileMaxTriangles !== undefined ? cfg.tileMaxTriangles : cfg.tileMaxTri, 8e6, 1e3, 1e9);
    TL.conc = Math.round(num(cfg.tileConcurrency, 4, 1, 16));
    modelRot = rotDeg();
    const root = new THREE.Group(); root.name = 'tiles'; root.userData.wrapper = true;
    if (modelRot) root.quaternion.setFromAxisAngle(UPV, modelRot * Math.PI / 180);
    root.updateMatrixWorld(true);
    const v = new THREE.Vector3(), ext = new THREE.Box3();
    for (const d of doc.tiles) {
      const ok = d && safeRel(d.file) && /\.glb$/i.test(d.file) && Array.isArray(d.min) && Array.isArray(d.max) && d.min.length === 3 && d.max.length === 3 && d.min.concat(d.max).every(Number.isFinite);
      if (!ok) { console.warn(tr('core.tile.ignored', rel), d && d.file); continue; }
      const b = new THREE.Box3();
      for (let k = 0; k < 8; k++) b.expandByPoint(v.set(k & 1 ? d.max[0] : d.min[0], k & 2 ? d.max[1] : d.min[1], k & 4 ? d.max[2] : d.min[2]).applyQuaternion(root.quaternion));
      ext.union(b);
      TL.tiles.push({ file: d.file, path: dir + d.file, bytes: Math.max(0, Number(d.bytes) || 0), tri: Math.max(0, Number(d.triangles) || 0),
        box: [b.min.x, b.min.z, b.max.x, b.max.z], ymin: b.min.y, ymax: b.max.y, state: 'idle', d: 0, fails: 0, retryAt: 0, ac: null, grp: null, grid: null, gen: null });
    }
    TL.root = root; model = root; TL.extent = ext; scene.add(root); TL.log = []; TL.anchor = null;
    if (!TL.refs) {   // tuiles sans références d'objets : les zones liées déjà posées sont retirées (avertissement), les libres restent
      const bad = zones.filter(z => z.mesh && z.type !== 'spawn');
      if (bad.length) { for (const z of bad) console.warn(tilesNoRefs(z)); zones = zones.filter(z => !bad.includes(z)); resolveLinks(); buildZones(); }
    }
    // v33 : arrivée demandée (lien #spawn=, #pos=, arrivée « default » à l'ouverture) : point de référence du chargeur jusqu'à la promenade ;
    // les tuiles qui la contiennent démarrent AVANT la vue d'ensemble et avant toute autre tuile
    let f = null;
    if (Array.isArray(opts.anchor) && opts.anchor.length >= 3 && opts.anchor.every(Number.isFinite)) f = { x: opts.anchor[0], z: opts.anchor[2] };
    else if (opts.spawn !== undefined) {
      const id = slug(opts.spawn), s = zones.find(z => z.type === 'spawn' && z.id === id) || zones.find(z => z.type === 'spawn' && z.id === 'default');
      if (s) f = { x: s.x, z: s.z };
    }
    if (f) {
      const now0 = performance.now();
      TL.anchor = { x: f.x, z: f.z, t0: now0, tx: controls.target.x, tz: controls.target.z, tiles: tilesAt(f.x, f.z) };
      tilesUpdate(now0);
    }
    const ovd = doc.overview;
    if (ovd && typeof ovd === 'object' && safeRel(ovd.file) && /\.glb$/i.test(ovd.file)) await loadOverview(ovd, dir);
    else if (ovd) console.warn(tr('core.ov.ignored'), ovd && ovd.file);
    const tanH = Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2);
    if (OV.state === 'ready' && !ext.isEmpty()) {
      // la vue d'ensemble montre toute la région : la caméra se cadre sur l'étendue entière (brouillard et plan lointain suivent)
      fit = Math.max(ext.max.x - ext.min.x, ext.max.z - ext.min.z, ext.max.y - ext.min.y, 200) / 2 / tanH * 1.35;
      const D = fit * Math.max(1, Number(cfg.zoom) || 1);
      controls.maxDistance = Math.max(controls.maxDistance, D * 1.5);
      scene.fog.near = Math.max(scene.fog.near, D * 1.1); scene.fog.far = Math.max(scene.fog.far, D * 3);
      camera.far = Math.max(camera.far, scene.fog.far + D); camera.updateProjectionMatrix();
    } else {
      // pas de vue d'ensemble : la caméra se cadre sur le rayon de chargement, pas sur toute la région
      fit = Math.max(2 * TL.radius, 200) / 2 / tanH * 1.35;
    }
    if (!ext.isEmpty()) { seaCx = (ext.min.x + ext.max.x) / 2; seaCz = (ext.min.z + ext.max.z) / 2; if (sea) sea.position.set(seaCx, cfg.seaY, seaCz); }
    frame(cfg.camDir, opts.target || cfg.target, cfg.zoom);
    if (TL.anchor) { TL.anchor.tx = controls.target.x; TL.anchor.tz = controls.target.z; }
    if (!f) f = { x: controls.target.x, z: controls.target.z };
    const now = performance.now();
    if (!TL.anchor) { TL.forced = f; TL.forcedUntil = now + 4000; }   // le temps que la coquille démarre la promenade (sans arrivée demandée)
    tilesUpdate(now);
    // attend les tuiles qui contiennent le point de départ (sinon la plus proche) : prêtes ou en échec, au plus opts.waitMs (15 s par défaut) ;
    // ensuite la page continue : la promenade démarre dès que la tuile est prête (TL.pending), « Chargement du sol… » reste affiché
    const waitSet = TL.anchor ? TL.anchor.tiles : tilesAt(f.x, f.z);
    const t1 = performance.now(), maxMs = Number.isFinite(opts.waitMs) ? opts.waitMs : 15000;
    await new Promise(res => { const chk = () => (waitSet.every(tileDone) || performance.now() - t1 > maxMs) ? res() : setTimeout(chk, 100); chk(); });
    dirty = true;
    return { tiles: TL.tiles.length, extent: ext.isEmpty() ? null : ext.min.toArray().concat(ext.max.toArray()), ready: waitSet.every(t => t.state === 'ready'), waited: Math.round(performance.now() - t1) };
  }
  function tilesState() {
    const names = t => TL.tiles.filter(q => t.includes(q.state)).map(q => q.file);
    return Object.assign(tilesStatus(), { on: TL.on, radius: TL.radius, margin: TL.margin, maxBytes: TL.maxBytes, maxTri: TL.maxTri, conc: TL.conc,
      overview: { state: OV.state, bytes: OV.bytes, tri: OV.tri, cells: OV.cells, visible: OV.root ? OV.root.children.filter(c => c.visible).map(c => c.name) : [], hidden: OV.root ? OV.root.children.filter(c => !c.visible).map(c => c.name) : [] },
      ready: names(['ready']), loadingFiles: names(['loading', 'building']), failedFiles: names(['failed']), groups: TL.root ? TL.root.children.map(c => c.name) : [], inflight: TL.inflight, gridQueue: TL.gridQ.length,
      anchor: TL.anchor ? { x: TL.anchor.x, z: TL.anchor.z, files: TL.anchor.tiles.map(t => t.file) } : null, log: TL.log.slice() });
  }

  function setCfg(p) {
    Object.assign(cfg, p);
    if ('zoneMarker' in p) cfg.zoneMarker = zmNorm(cfg.zoneMarker);
    if ('skyColor' in p) { scene.background.set(cfg.skyColor); scene.fog.color.set(cfg.skyColor); hemi.color.set(cfg.skyColor); }
    if ('retina' in p || 'pixelScale' in p) resize();
    // v42 : rayon des tuiles et vue d'ensemble seule, pris en compte au prochain tour de choix des tuiles (250 ms au plus)
    if ('tileRadius' in p && TL.on && Number(cfg.tileRadius) > 0) { TL.radius = Math.min(5000, Math.max(10, Number(cfg.tileRadius))); TL.lastUpd = 0; }
    if ('ovOnly' in p && TL.on) TL.lastUpd = 0;
    if ('rotate' in p) applyRotation();
    if ('sea' in p || 'anim' in p || 'seaSegments' in p) buildSea();
    else if (seaMat) {
      if ('seaColor' in p) { if (seaMat.uniforms) seaMat.uniforms.uColor.value.set(cfg.seaColor); else seaMat.color.set(cfg.seaColor); }
      if (seaMat.uniforms) {
        seaMat.uniforms.uAmp.value = cfg.wave;
        seaMat.uniforms.uHoleRadius.value = cfg.hole;
        seaMat.uniforms.uHoleFade.value = cfg.holeFade;
        seaMat.uniforms.uHoleCenter.value.set(cfg.holeX, -cfg.holeZ);
      }
    }
    if (sea) sea.position.set(seaCx, cfg.seaY, seaCz);
    if ('zoneMarker' in p || 'showSpawns' in p) buildZones();
    if ('foliageCutout' in p) foliageMats.forEach(m => { m.alphaTest = cfg.foliageCutout; m.needsUpdate = true; });
    if ('solidMaterials' in p) {
      const tk = parseIgnore(cfg.solidMaterials);
      scene.traverse(o => { if (o.isMesh && o.material) for (const m of (Array.isArray(o.material) ? o.material : [o.material])) if (m && !foliageMats.includes(m)) solidApply(m, tk); });
      dirty = true;
    }
    dirty = true;
    if (onCfg) onCfg(cfg);
  }

  function getCameraState() {
    const off = camera.position.clone().sub(controls.target);
    const dist = off.length();
    return { camDir: off.normalize().toArray(), target: controls.target.toArray(), zoom: dist / fit };
  }

  function setZoom(z) {
    const off = camera.position.clone().sub(controls.target);
    if (off.lengthSq() < 1e-8) off.set(0, 0.25, 1);
    camera.position.copy(controls.target).addScaledVector(off.normalize(), fit * z);
    controls.update();
    dirty = true;
  }

  // ---- promenade à hauteur d'avatar
  const dom = renderer.domElement;
  const STEP_UP = 0.6;
  // v33 : vol (touche Début : E monte, C descend, pas de gravité, murs solides, jamais sous le sol) et trois vues (V) :
  // 'fps' subjective, 'tps' à la troisième personne (la caméra tourne autour de l'avatar), 'free' caméra libre (l'avatar reste sur place)
  const VIEWS = ['fps', 'tps', 'free'], VIEW_NAMES = { fps: tr('core.view.fps'), tps: tr('core.view.tps'), free: tr('core.view.free') };
  let selfAv = null, selfKey = '';
  function updateSelf() {
    const show = walking && W.view !== 'fps';
    if (!show) { if (selfAv && selfAv.visible) { selfAv.visible = false; dirty = true; } return; }
    const col = P.myColor !== null ? P.myColor : (P.serverColor !== null ? P.serverColor : 0x3366cc), key = P.name + '|' + col;
    if (!selfAv || selfKey !== key) { if (selfAv) disposeAvatar(selfAv); selfAv = makeAvatar(P.name || 'Moi', col); scene.add(selfAv); selfKey = key; }
    selfAv.visible = true; selfAv.position.set(W.pos.x, W.pos.y, W.pos.z); selfAv.rotation.y = W.yaw; dirty = true;
  }
  // sol sous un point de caméra : la surface la plus haute à moins de 1 m au-dessus, sinon (point enfoui sous le relief) la plus haute à moins de 12 m au-dessus
  function floorAt(G, x, z, y) { let g = G.ground(x, z, y + 1); if (g === null) g = G.ground(x, z, y + 12); return g; }
  function placeCamera(G, hasGround) {
    const eyeY = W.pos.y + cfg.eyeHeight;
    if (W.view === 'free') { camera.position.copy(W.cam); camera.rotation.set(W.cpitch, W.cyaw, 0); return; }
    if (W.view === 'tps') {
      const cp = Math.cos(W.tpitch), sp = Math.sin(W.tpitch), sy = Math.sin(W.tyaw), cy = Math.cos(W.tyaw);
      const fx = -sy * cp, fy = sp, fz = -cy * cp;   // direction du regard de la caméra (v35 : indépendante de l'orientation de l'avatar)
      let D = W.tdist;
      if (hasGround) {   // un mur entre l'avatar et la caméra : la caméra se rapproche
        const hl = Math.hypot(fx, fz) || 1, hit = G.wall(W.pos.x, eyeY, W.pos.z, -fx / hl, -fz / hl, D * Math.max(cp, 0.3) + 0.3);
        if (hit) D = Math.max(0.5, (hit.t - 0.3) / Math.max(cp, 0.3));
      }
      const cx = W.pos.x - fx * D, cz = W.pos.z - fz * D; let cy2 = eyeY - fy * D;
      if (hasGround) { const g = floorAt(G, cx, cz, cy2); if (g !== null && cy2 < g + 0.3) cy2 = g + 0.3; }   // la caméra ne traverse pas le sol
      camera.position.set(cx, cy2, cz); camera.lookAt(W.pos.x, eyeY, W.pos.z);
      return;
    }
    camera.position.set(W.pos.x, eyeY, W.pos.z);
    camera.rotation.set(W.pitch, W.yaw, 0);
  }
  function walkStep(dt) {
    const k = W.keys, free = W.view === 'free', tps = W.view === 'tps';
    for (const c of W.run) if (!k.has(c)) W.run.delete(c);   // v35 : course par double appui (W, S, ↑, ↓) : tant que la touche reste enfoncée
    const run = k.has('ShiftLeft') || k.has('ShiftRight') || W.run.size > 0 || !!W.runLatch;   // v46 : bouton « Courir » des flèches à l'écran (un clic l'allume, un clic l'éteint)
    if (run !== !!W.runOn) { W.runOn = run; if (onView) onView(); }   // v37 : la ligne « Mode » de l'état affiche la course
    const turn = (k.has('ArrowLeft') ? 1 : 0) - (k.has('ArrowRight') ? 1 : 0);
    if (turn) { if (free) W.cyaw += 1.8 * dt * turn; else if (tps) W.tyaw += 1.8 * dt * turn; else W.yaw += 1.8 * dt * turn; }
    const f = (k.has('KeyW') || k.has('ArrowUp') ? 1 : 0) - (k.has('KeyS') || k.has('ArrowDown') ? 1 : 0);
    const s = (k.has('KeyD') ? 1 : 0) - (k.has('KeyA') ? 1 : 0);
    const up = (k.has('PageUp') || (W.fly && k.has('Space')) ? 1 : 0) - (k.has('KeyC') || k.has('PageDown') ? 1 : 0);   // v36 : monter = Page Haut ou Espace maintenu (en vol) ; E ne sert plus qu'aux zones
    const G = W.grid, hasGround = G && (G.count > 0 || G.tiled);
    let speed = cfg.walkSpeed * (run ? 2.2 : 1);
    if (free) {
      // v35 : la vitesse suit la distance caméra-avatar (au moins la marche, 0,5 x la distance par seconde, 60 m/s au plus) ; Maj la multiplie par 3
      const dd = Math.hypot(W.cam.x - W.pos.x, W.cam.y - (W.pos.y + cfg.eyeHeight), W.cam.z - W.pos.z);
      speed = Math.min(60, Math.max(cfg.walkSpeed, 0.5 * dd)) * ((k.has('ShiftLeft') || k.has('ShiftRight')) ? 3 : 1);
      // caméra libre : les touches déplacent la caméra (dans le sens du regard), l'avatar reste sur place
      const sy = Math.sin(W.cyaw), cy = Math.cos(W.cyaw), cp = Math.cos(W.cpitch), sp = Math.sin(W.cpitch);
      let mx = -sy * cp * f + cy * s, my = sp * f + up, mz = -cy * cp * f - sy * s;
      const len = Math.hypot(mx, my, mz);
      if (len > 0 && dt > 0) {
        const d = speed * dt / len, nx = W.cam.x + mx * d, nz = W.cam.z + mz * d;
        if (hasGround && G.tiled && G.pending(nx, nz)) markWait(nx, nz);
        else { W.cam.x = nx; W.cam.z = nz; W.cam.y += my * d; }
      }
      if (hasGround) { const g = floorAt(G, W.cam.x, W.cam.z, W.cam.y); if (g !== null && W.cam.y < g + 0.3) W.cam.y = g + 0.3; }   // jamais sous le sol
    }
    const mf = free ? 0 : f, ms = free ? 0 : s;
    const my0 = tps ? W.tyaw : W.yaw, sy = Math.sin(my0), cy = Math.cos(my0);   // v35 : à la troisième personne la marche suit la caméra
    let mx = -sy * mf + cy * ms, mz = -cy * mf - sy * ms;
    const len = Math.hypot(mx, mz);
    if (len > 0 && dt > 0) {
      mx /= len; mz /= len;
      if (tps) { let d = Math.atan2(-mx, -mz) - W.yaw; d = Math.atan2(Math.sin(d), Math.cos(d)); W.yaw += d * (1 - Math.exp(-dt * 8)); }   // l'avatar se tourne vers sa direction de déplacement (lissé)
      const dist = speed * dt;
      let dx = mx * dist, dz = mz * dist;
      if (hasGround) {
        const hit = G.wall(W.pos.x, W.pos.y + 0.9, W.pos.z, mx, mz, dist + 0.35);
        if (hit) {
          let nx = hit.nx, nz = hit.nz; const nl = Math.hypot(nx, nz) || 1; nx /= nl; nz /= nl;
          if (nx * mx + nz * mz > 0) { nx = -nx; nz = -nz; }
          const d = dx * nx + dz * nz; dx -= d * nx; dz -= d * nz;
        }
        // mode tuiles : jamais d'avancée vers une zone dont la tuile n'est pas prête (indicateur « Chargement du sol… »)
        if (G.tiled && G.pending(W.pos.x + dx, W.pos.z + dz)) markWait(W.pos.x + dx, W.pos.z + dz);
        else if (W.fly || G.ground(W.pos.x + dx, W.pos.z + dz, W.pos.y + STEP_UP) !== null) { W.pos.x += dx; W.pos.z += dz; }
      } else { W.pos.x += dx; W.pos.z += dz; }
    }
    // v36 : Page Haut maintenu au sol plus de 0,4 s : décollage (vol + montée) ; un appui bref a déjà fait sauter l'avatar
    if (k.has('PageUp') && !W.fly && !free && cfg.fly !== false) { W.upT += dt; if (W.upT > 0.4) startFly(); } else W.upT = 0;
    if (W.fly) {
      // en vol : pas de gravité ; E monte, C descend ; jamais sous le sol des tuiles chargées (tuile dessous pas prête : on ne descend pas)
      W.vy = 0; W.grounded = false; W.jumpReq = false;
      const gF = hasGround ? G.ground(W.pos.x, W.pos.z, W.pos.y + STEP_UP) : null;
      if (gF !== null) W.flyFloor = gF;
      let ny = W.pos.y + (free ? 0 : up) * speed * dt;
      if (hasGround && G.tiled && G.pending(W.pos.x, W.pos.z)) { if (ny < W.pos.y) { ny = W.pos.y; markWait(W.pos.x, W.pos.z); } }
      else if (hasGround) {
        const fl = gF !== null ? gF : W.flyFloor;
        if (fl !== undefined && ny < fl) ny = fl;
        // v34 : en descendant jusqu'au sol, l'avatar atterrit tout seul (le vol s'arrête ; jamais sous le sol)
        if (fl !== undefined && up < 0 && !free && ny <= fl + 1e-3) { W.pos.y = fl; W.fly = false; W.vy = 0; W.grounded = true; W.keys.delete('KeyC'); W.keys.delete('PageDown'); if (onFly) onFly(false); dirty = true; ny = fl; }
      }
      W.pos.y = ny;
    } else {
      if ((W.jumpReq || k.has('Space')) && W.grounded && !free) { W.vy = 5.5; W.grounded = false; W.pos.y += 0.02; }
      W.jumpReq = false;
      const g = hasGround ? G.ground(W.pos.x, W.pos.z, W.pos.y + STEP_UP) : null;
      if (W.grounded) {
        if (g !== null) {
          if (W.pos.y - g > 0.6) W.grounded = false;
          else W.pos.y += (g - W.pos.y) * Math.min(1, dt * 18);
        }
      }
      if (!W.grounded && !(G && G.tiled && G.pending(W.pos.x, W.pos.z))) {
        W.vy -= 15 * dt; W.pos.y += W.vy * dt;
        if (g !== null && W.pos.y <= g) { W.pos.y = g; W.vy = 0; W.grounded = true; }
        if (W.pos.y < W.spawn.y - 400) { W.pos.copy(W.spawn); W.vy = 0; W.grounded = true; }
      }
    }
    placeCamera(G, hasGround);
    updateSelf();
    if (dt > 0) { zoneTick(); if (zoneLabs.length) zoneLabelTick(); }
  }
  function setView(v) {
    if (!walking || !VIEWS.includes(v) || v === W.view) return W.view;
    const fromTps = W.view === 'tps';
    if (v === 'free') { W.cam.copy(camera.position); W.cyaw = fromTps ? W.tyaw : W.yaw; W.cpitch = fromTps ? W.tpitch : W.pitch; }
    else if (W.view === 'free') W.keys.clear();
    if (v === 'tps') { W.tyaw = W.yaw; W.tpitch = fromTps ? W.tpitch : W.pitch; }   // v35 : la caméra repart de la direction du regard
    else if (fromTps) { W.yaw = W.tyaw; W.pitch = W.tpitch; }   // retour à la vue subjective : le regard garde la direction de la caméra
    W.view = v; walkStep(0); dirty = true;
    if (onView) onView(v, VIEW_NAMES[v]);
    return v;
  }
  const cycleView = () => setView(VIEWS[(VIEWS.indexOf(W.view) + 1) % VIEWS.length]);
  function startFly() {   // décollage par touche maintenue : les touches tenues restent actives (la montée continue)
    if (!walking || W.fly || cfg.fly === false) return false;
    W.fly = true; W.vy = 0; W.grounded = false; W.upT = 0;
    if (onFly) onFly(true);
    dirty = true;
    return true;
  }
  // v35 : touche M / Fin / Alt+clic : la caméra revient derrière l'avatar
  function setTpsDist(d) { W.tdist = Math.max(1, Math.min(30, d)); try { localStorage.setItem('glb2html_tpsDist', String(W.tdist)); } catch (_) {} }
  function recenterCam() {
    if (!walking) return false;
    W.tyaw = W.yaw; W.tpitch = 0.12;
    if (W.view === 'tps') setTpsDist(4);
    else if (W.view === 'free') {   // caméra libre : derrière l'avatar, à la distance par défaut, le regard sur lui
      const D = 4, cp = Math.cos(W.tpitch), sp = Math.sin(W.tpitch), eyeY = W.pos.y + cfg.eyeHeight;
      W.cam.set(W.pos.x + Math.sin(W.yaw) * cp * D, eyeY - sp * D, W.pos.z + Math.cos(W.yaw) * cp * D); W.cyaw = W.yaw; W.cpitch = W.tpitch;
      const G = W.grid; if (G && (G.count > 0 || G.tiled)) { const g = floorAt(G, W.cam.x, W.cam.z, W.cam.y); if (g !== null && W.cam.y < g + 0.3) W.cam.y = g + 0.3; }
    }
    walkStep(0); dirty = true; return true;
  }
  function toggleFly() {
    if (!walking || cfg.fly === false) return false;
    W.fly = !W.fly; W.vy = 0; W.keys.clear(); W.upT = 0;
    if (W.fly) W.grounded = false; else W.grounded = false;   // à l'atterrissage la gravité ramène l'avatar sur le sol des tuiles chargées
    if (onFly) onFly(W.fly);
    dirty = true;
    return W.fly;
  }
  // v36 : arrivée occupée. À chaque pose de l'avatar sur un point (ouverture, arrivée par défaut, R, portail, « Aller à », #pos), si un autre visiteur EN PROMENADE
  // est à moins de 1 m en horizontal (2 m en vertical), le NOUVEL ARRIVANT passe au point libre le plus proche : anneaux de 1,2, 2,4 puis 3,6 m (12, 16, 24 candidats),
  // sol à moins de 1 m d'écart de hauteur, aucun mur entre le point demandé et le candidat, aucun visiteur à moins de 1 m. Sans place libre : pose à l'endroit demandé.
  // Présence pas encore connectée (liste des visiteurs inconnue) : le contrôle est refait à la réception de la liste, seulement si l'avatar n'a pas bougé de plus de 0,3 m.
  const DODGE = { pending: null };
  function peerNear(x, y, z, rh, rv) {
    for (const q of P.peers.values()) if (q.g.visible && Math.hypot(q.tx - x, q.tz - z) < rh && Math.abs(q.ty - y) < rv) return true;
    return false;
  }
  // v37 : le point libre le plus proche de l'OCCUPANT (anneaux de 1,5 puis 2,0 puis 3,0 m autour de lui, 16 candidats), le plus proche du point demandé dans l'anneau ;
  // l'arrivant est ensuite tourné vers l'occupant le plus proche (avant = (-sin yaw, -cos yaw), comme getWalk().yaw)
  function dodgeSpot(x, y, z) {
    if (!peerNear(x, y, z, 1, 2)) return null;
    const G = W.grid; if (!G) return null;
    let occ = null, od = 1e9;
    for (const q of P.peers.values()) { if (!q.g.visible || Math.abs(q.ty - y) >= 2) continue; const d = Math.hypot(q.tx - x, q.tz - z); if (d < 1 && d < od) { od = d; occ = q; } }
    if (!occ) return null;
    const ox = occ.tx, oz = occ.tz, oy = occ.ty;
    for (const r of [1.5, 2.0, 3.0]) {
      const n = 16, found = [];
      for (let i = 0; i < n; i++) {
        const a = i / n * Math.PI * 2, cx = ox + Math.cos(a) * r, cz = oz + Math.sin(a) * r;
        if (G.tiled && G.pending(cx, cz)) continue;
        const g = G.ground(cx, cz, y + 1);
        if (g === null || Math.abs(g - y) > 1) continue;
        if (G.wall(ox, oy + 0.9, oz, Math.cos(a), Math.sin(a), r + 0.3)) continue;
        if (peerNear(cx, g, cz, 1, 2)) continue;
        found.push({ x: cx, y: g, z: cz, r, dp: Math.hypot(cx - x, cz - z), dy: Math.abs(g - y) });
      }
      if (found.length) { found.sort((p, q) => (p.dp - q.dp) || (p.dy - q.dy)); return found[0]; }
    }
    return null;
  }
  function dodgeNow() {
    const x0 = W.pos.x, z0 = W.pos.z, s = dodgeSpot(x0, W.pos.y, z0);
    if (!s) return false;
    W.pos.set(s.x, s.y, s.z); W.spawn.copy(W.pos);
    let near = null, nd = 4;
    for (const q of P.peers.values()) { if (!q.g.visible) continue; const d = Math.hypot(q.tx - s.x, q.tz - s.z); if (d < nd) { nd = d; near = q; } }
    if (near) { W.yaw = W.tyaw = Math.atan2(-(near.tx - s.x), -(near.tz - s.z)); W.pitch = 0; }
    console.log(tr('core.dodge.log', (Math.round(Math.hypot(s.x - x0, s.z - z0) * 10) / 10).toFixed(1), s.r.toFixed(1)));
    return true;
  }
  function dodgeApply() {
    DODGE.pending = null;
    if (!cfg.presenceUrl) return;
    if (P.ws && P.ws.readyState === 1 && P.id) dodgeNow();
    else DODGE.pending = { x: W.pos.x, y: W.pos.y, z: W.pos.z, t: performance.now() };
  }
  function dodgeWelcome() {
    const d = DODGE.pending; DODGE.pending = null;
    if (d && walking && W.grid && performance.now() - d.t < 20000 && Math.hypot(W.pos.x - d.x, W.pos.y - d.y, W.pos.z - d.z) <= 0.3) { dodgeNow(); dirty = true; }
  }
  function walkStart(opts) {
    if (!model || walking) return walking;
    // v33 : F sans point demandé démarre à l'arrivée « default » tant que la cible n'a pas bougé (sinon à la cible, comme avant)
    if (!opts && home && home.forF && Math.hypot(controls.target.x - home.pos[0], controls.target.z - home.pos[2]) < 0.05) opts = { pos: home.pos, yaw: home.yaw };
    if (TL.on) {
      // la promenade attend que la tuile sous l'avatar soit prête (F de nouveau : annuler)
      const at = (opts && opts.pos) ? { x: opts.pos[0], z: opts.pos[2] } : { x: controls.target.x, z: controls.target.z };
      if (TG.pending(at.x, at.z)) { TL.pending = { kind: 'walk', opts, at, t0: TL.pending ? TL.pending.t0 : (TL.anchor ? TL.anchor.t0 : performance.now()) }; markWait(at.x, at.z); tilesUpdate(TL.waitT); return false; }
      TL.pending = null; TL.forced = null; releaseAnchor();
    }
    W.grid = TL.on ? TG : buildCollisionGrid(model, 3, parseIgnore(cfg.walkIgnore));
    W.saved = { pos: camera.position.clone(), target: controls.target.clone(), fov: camera.fov };
    const t = (opts && opts.pos) ? new THREE.Vector3().fromArray(opts.pos) : controls.target, fx = t.x - camera.position.x, fz = t.z - camera.position.z;
    W.yaw = (opts && Number.isFinite(opts.yaw)) ? opts.yaw : (Math.hypot(fx, fz) > 1e-3 ? Math.atan2(-fx, -fz) : 0);
    W.pitch = 0; W.tyaw = W.yaw; W.tpitch = 0; W.run.clear(); W.upT = 0; W.runOn = false;
    let g = W.grid.ground(t.x, t.z, t.y + 2);
    if (g === null) g = W.grid.ground(t.x, t.z, 1e6);
    W.pos.set(t.x, g === null ? t.y : g, t.z); W.spawn.copy(W.pos);
    dodgeApply();
    W.vy = 0; W.grounded = true; W.keys.clear(); W.drag = false; W.fly = false; W.flyFloor = undefined; W.view = 'fps'; W.mouseFree = false;
    controls.enabled = false;
    camera.fov = 70; camera.updateProjectionMatrix();
    camera.rotation.order = 'YXZ';
    walking = true;
    if (document.activeElement && document.activeElement.blur) document.activeElement.blur();
    zoneInside.clear(); nearZone = null;
    for (const z of zones) if (z.type === 'portal' && z.trigger !== 'click' && !zoneOff(z) && zoneDist(z).d <= z.radius) zoneInside.add(z.id);
    walkStep(0); dirty = true;
    presenceEnter();
    if (onWalk) onWalk(true);
    return true;
  }
  // P (et le bouton) : entre ou sort de la promenade
  function toggleWalk() {
    if (TL.pending) { TL.pending = null; tilesInfo(); return false; }
    return walking ? walkStop() : walkStart();
  }
  // v36 : F (comme P) entre en promenade et en sort, en vue globale comme en promenade, y compris pendant l'attente d'une tuile (annule) ; le vol se bascule avec Début ou le bouton
  function pressF() { return toggleWalk(); }
  function walkStop() {
    if (!walking) return;
    walking = false; W.keys.clear(); W.drag = false; W.fly = false; W.view = 'fps'; W.runLatch = false; updateSelf();
    if (document.pointerLockElement === dom && document.exitPointerLock) document.exitPointerLock();
    camera.rotation.order = 'XYZ';
    camera.fov = W.saved.fov; camera.updateProjectionMatrix();
    // v31 : la cible de la vue globale (cercle d'atterrissage) passe au sol sous l'avatar ; la caméra garde le décalage (distance et direction)
    // qu'elle avait avant l'entrée en promenade. En mode tuiles le chargeur suit cette cible : les tuiles autour de l'avatar restent.
    const off = W.saved.pos.clone().sub(W.saved.target);
    let gy = W.grid ? W.grid.ground(W.pos.x, W.pos.z, W.pos.y + 2) : null;
    if (gy === null) gy = W.pos.y;
    controls.target.set(W.pos.x, gy, W.pos.z);
    camera.position.copy(controls.target).add(off);
    controls.enabled = true; controls.update();
    landKey = '';
    W.grid = null; dirty = true;
    zoneInside.clear(); if (nearZone) { nearZone = null; if (onNear) onNear(null); }
    DODGE.pending = null;
    presenceLeave();
    if (zoneLabs.length) zoneLabelTick();
    if (onWalk) onWalk(false);
  }

  // téléportation dans la même région (portail interne) : pose l'avatar en pos/yaw sans quitter la promenade
  function teleportTo(pos, yaw) {
    if (!model) return false;
    if (!walking) return walkStart({ pos, yaw });
    const x = pos[0], y = pos[1], z = pos[2];
    if (TL.on && TG.pending(x, z)) { TL.pending = { kind: 'tp', pos, yaw, at: { x, z }, t0: TL.pending ? TL.pending.t0 : performance.now() }; markWait(x, z); tilesUpdate(TL.waitT); return true; }
    let g = W.grid.ground(x, z, y + 2);
    if (g === null) g = W.grid.ground(x, z, 1e6);
    W.pos.set(x, g === null ? y : g, z); W.spawn.copy(W.pos);
    dodgeApply();
    if (Number.isFinite(yaw)) { W.yaw = yaw; W.tyaw = yaw; }
    W.pitch = 0; W.vy = 0; W.grounded = true;
    zoneInside.clear(); nearZone = null; if (onNear) onNear(null);
    for (const q of zones) if (q.type === 'portal' && q.trigger !== 'click' && !zoneOff(q) && zoneDist(q).d <= q.radius) zoneInside.add(q.id);
    walkStep(0); dirty = true;
    return true;
  }
  // v46 : vue globale pas à pas (flèches à l'écran) : fwd, side, dir dans [-1, 1], dt en secondes. Le pas suit la distance de la caméra à la cible
  // (60 % de cette distance par seconde, 2 m au moins) ; tourner : 1,2 rad/s autour de la cible (gauche = sens inverse des aiguilles vu d'en haut) ;
  // rapprocher / éloigner : facteur e^(1,2 dt), dans les bornes d'OrbitControls. Sans effet en promenade.
  function globalMove(fwd, side, dt) {
    if (walking || !Number.isFinite(dt) || dt <= 0) return false;
    const off = camera.position.clone().sub(controls.target), d = off.length();
    const f = new THREE.Vector3(-off.x, 0, -off.z); if (f.lengthSq() < 1e-9) f.set(0, 0, -1); f.normalize();
    const r = new THREE.Vector3(-f.z, 0, f.x), step = Math.max(2, d) * 0.6 * Math.min(dt, 0.25);
    const m = f.multiplyScalar((fwd || 0) * step).add(r.multiplyScalar((side || 0) * step));
    camera.position.add(m); controls.target.add(m); controls.update(); landKey = ''; dirty = true;
    return true;
  }
  function globalTurn(dir, dt) {
    if (walking || !Number.isFinite(dt) || dt <= 0) return false;
    const off = camera.position.clone().sub(controls.target).applyAxisAngle(new THREE.Vector3(0, 1, 0), (dir || 0) * 1.2 * Math.min(dt, 0.25));
    camera.position.copy(controls.target).add(off); controls.update(); dirty = true;
    return true;
  }
  function globalZoom(dir, dt) {
    if (walking || !Number.isFinite(dt) || dt <= 0) return false;
    const off = camera.position.clone().sub(controls.target), d = off.length() || 1;
    const nd = Math.max(controls.minDistance, Math.min(controls.maxDistance, d * Math.exp((dir || 0) * 1.2 * Math.min(dt, 0.25))));
    camera.position.copy(controls.target).add(off.multiplyScalar(nd / d)); controls.update(); dirty = true;
    return true;
  }
  // v33 : aller à un point (champ « Aller à », retour à l'arrivée) : en promenade, téléportation (attend la tuile, « Chargement du sol… ») ;
  // en vue globale, la cible se déplace (la caméra la suit, avec le même décalage) et le chargeur de tuiles aussi
  function goTo(pos, yaw) {
    if (!model || !Array.isArray(pos) || pos.length < 3 || !pos.every(Number.isFinite)) return false;
    if (walking) return teleportTo(pos.slice(0, 3), yaw);
    const d = new THREE.Vector3().fromArray(pos).sub(controls.target);
    camera.position.add(d); controls.target.add(d); controls.update();
    landKey = ''; dirty = true;
    if (TL.on) { TL.forced = { x: pos[0], z: pos[2] }; TL.forcedUntil = performance.now() + 15000; tilesUpdate(performance.now()); }
    return true;
  }
  const returnHome = () => (home ? goTo(home.pos, home.yaw) : false);
  // v34 : souris libre (le pointeur vient d'être libéré en promenade : Échap, perte de focus). Après la v52, un clic, un double-clic ou un clic sur une zone
  // ne capturent JAMAIS la souris : la capture est volontaire (touche G, bouton « Capturer la souris »). L'état « libre » ne sert plus qu'à l'afficher.
  function grabMouse() {
    if (!walking) return false;
    W.mouseFree = false;
    try { const p = dom.requestPointerLock(); if (p && p.catch) p.catch(() => {}); } catch (_) {}
    if (onMouse) onMouse(mouseState());
    return true;
  }
  // après la v52 : la touche G BASCULE (capture si la souris est libre, libère si elle est capturée) ; le bouton « Capturer la souris » ne fait que capturer
  // (un pointeur verrouillé ne peut rien cliquer). exitPointerLock déclenche pointerlockchange : l'état « libre » et l'interface suivent.
  function toggleMouse() {
    if (!walking) return false;
    if (document.pointerLockElement === dom) { try { document.exitPointerLock(); } catch (_) {} return true; }
    return grabMouse();
  }
  const mouseState = () => (document.pointerLockElement === dom ? 'captured' : (W.mouseFree ? 'free' : 'idle'));
  document.addEventListener('pointerlockchange', () => {
    if (!walking) return;   // sortie de promenade : walkStop libère le pointeur lui-même
    W.mouseFree = document.pointerLockElement !== dom;
    if (onMouse) onMouse(mouseState());
  });
  const typing = e => { const n = e.target && e.target.tagName; return n === 'INPUT' || n === 'TEXTAREA' || n === 'SELECT'; };
  const MOVE_KEYS = new Set(['KeyW', 'KeyA', 'KeyS', 'KeyD', 'KeyC', 'PageUp', 'PageDown', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space', 'ShiftLeft', 'ShiftRight']);
  const RUN_TAP = new Set(['KeyW', 'KeyS', 'ArrowUp', 'ArrowDown']);
  window.addEventListener('keydown', e => {
    if (!walking || typing(e)) return;
    if (e.code === 'AltLeft' || e.code === 'AltRight') { e.preventDefault(); return; }   // Alt seul n'ouvre pas le menu du navigateur
    if (e.repeat) return;
    const mod = e.ctrlKey || e.metaKey || e.altKey;
    if (e.code === 'Home' && cfg.fly !== false) { toggleFly(); e.preventDefault(); }
    else if (e.code === 'End' && !mod) { recenterCam(); e.preventDefault(); }
    else if (e.code === 'KeyV' && !mod) cycleView();
    else if (keyChar(e) === 'm' && !mod) setView(W.view === 'tps' ? 'fps' : 'tps');   // v36 : reconnue par la lettre imprimée (« m »), pas par la place de la touche ; v35 : M bascule vue subjective / troisième personne (Ctrl+M : carte des mondes)
    else if (e.code === 'KeyG' && !mod) toggleMouse();
  });
  window.addEventListener('keydown', e => { if (!walking || typing(e) || !MOVE_KEYS.has(e.code) || e.ctrlKey || e.metaKey || e.altKey) return;   // v34 : Ctrl+C copie (le texte de l'aide est sélectionnable)
    const c = e.code;
    if (c === 'Space' && !W.fly) W.jumpReq = true;
    if (!e.repeat) {
      const now = performance.now();
      if (RUN_TAP.has(c)) { if (W.tap[c] !== undefined && now - W.tap[c] < 300) W.run.add(c); W.tap[c] = now; }   // v35 : double appui rapide = course
      if (c === 'PageUp' && !W.fly && W.view !== 'free') W.jumpReq = true;   // appui bref au sol = saut (maintenu plus de 0,4 s : décollage)
    }
    W.keys.add(c); e.preventDefault(); });
  window.addEventListener('keyup', e => { W.keys.delete(e.code); W.run.delete(e.code); if (walking && (e.code === 'AltLeft' || e.code === 'AltRight')) e.preventDefault(); });
  window.addEventListener('blur', () => { W.keys.clear(); W.run.clear(); });
  dom.addEventListener('mousedown', () => { if (walking) { W.drag = true; W.moved = false; } });
  window.addEventListener('mouseup', () => { W.drag = false; });
  window.addEventListener('mousemove', e => {
    if (!walking || !(W.drag || document.pointerLockElement === dom)) return;
    if (W.drag && (e.movementX || e.movementY)) W.moved = true;
    if (W.view === 'free' && e.altKey) {   // v35 : Alt + glisser : la caméra orbite autour de l'avatar en gardant sa distance, le regard sur lui
      const ex = W.pos.x, ey = W.pos.y + cfg.eyeHeight, ez = W.pos.z;
      let ox = W.cam.x - ex, oy = W.cam.y - ey, oz = W.cam.z - ez; const d = Math.hypot(ox, oy, oz) || 1;
      let az = Math.atan2(ox, oz) - (e.movementX || 0) * 0.0022, el = Math.max(-1.45, Math.min(1.45, Math.asin(oy / d) + (e.movementY || 0) * 0.0022));
      W.cam.set(ex + d * Math.cos(el) * Math.sin(az), ey + d * Math.sin(el), ez + d * Math.cos(el) * Math.cos(az));
      const G = W.grid; if (G && (G.count > 0 || G.tiled)) { const g = floorAt(G, W.cam.x, W.cam.z, W.cam.y); if (g !== null && W.cam.y < g + 0.3) W.cam.y = g + 0.3; }
      const fx = ex - W.cam.x, fy = ey - W.cam.y, fz = ez - W.cam.z, fl = Math.hypot(fx, fy, fz) || 1;
      W.cyaw = Math.atan2(-fx, -fz); W.cpitch = Math.asin(fy / fl);
      walkStep(0); dirty = true;
      return;
    }
    lookBy(e.movementX || 0, e.movementY || 0);
  });
  // v46 : regard (souris, doigt) : mx, my en pixels de déplacement de la souris ; caméra libre, troisième personne (orbite autour de l'avatar), subjective
  function lookBy(mx, my) {
    if (W.view === 'free') {
      W.cyaw -= mx * 0.0022;
      W.cpitch = Math.max(-1.45, Math.min(1.45, W.cpitch - my * 0.0022));
      return;
    }
    if (W.view === 'tps') {   // v35 : la souris fait orbiter la caméra autour de l'avatar sans le tourner
      W.tyaw -= mx * 0.0022;
      W.tpitch = Math.max(-1.45, Math.min(1.45, W.tpitch - my * 0.0022));
      return;
    }
    W.yaw -= mx * 0.0022;
    W.pitch = Math.max(-1.45, Math.min(1.45, W.pitch - my * 0.0022));
  }
  // v46 : écran tactile en promenade : un doigt qui glisse sur la scène fait regarder (on tire le décor : doigt vers la droite, regard vers la gauche) ;
  // un seul doigt suivi ; les gestes de la vue globale restent ceux d'OrbitControls
  let touchLook = null;
  dom.addEventListener('pointerdown', e => { if (e.pointerType === 'touch' && walking && !touchLook) touchLook = { id: e.pointerId, x: e.clientX, y: e.clientY }; });
  dom.addEventListener('pointermove', e => {
    if (!touchLook || e.pointerId !== touchLook.id) return;
    if (!walking) { touchLook = null; return; }
    const dx = e.clientX - touchLook.x, dy = e.clientY - touchLook.y; touchLook.x = e.clientX; touchLook.y = e.clientY;
    if (dx || dy) { W.moved = true; lookBy(-dx * 1.6, -dy * 1.6); dirty = true; }
  });
  for (const ev of ['pointerup', 'pointercancel']) dom.addEventListener(ev, e => { if (touchLook && e.pointerId === touchLook.id) touchLook = null; });
  // v35 : molette en promenade. Caméra libre : avance / recule la caméra le long du regard (pas = 15 % de la distance à l'avatar, 0,5 à 20 m) ;
  // troisième personne : règle la distance de la caméra (1 à 30 m) ; vue subjective : rien. La page ne défile pas.
  window.addEventListener('wheel', e => {
    if (!walking) return;
    const t = e.target;
    if (t === dom || t === document.body || t === document.documentElement) e.preventDefault();
    if (t !== dom && t !== document.body && t !== document.documentElement) return;
    const sgn = Math.sign(e.deltaY); if (!sgn) return;
    if (W.view === 'tps') { setTpsDist(W.tdist * (sgn > 0 ? 1.15 : 1 / 1.15)); walkStep(0); dirty = true; }
    else if (W.view === 'free') {
      const dd = Math.hypot(W.cam.x - W.pos.x, W.cam.y - (W.pos.y + cfg.eyeHeight), W.cam.z - W.pos.z);
      const step = Math.max(0.5, Math.min(20, 0.15 * dd)) * -sgn;
      const cp = Math.cos(W.cpitch), sp = Math.sin(W.cpitch), sy = Math.sin(W.cyaw), cy = Math.cos(W.cyaw);
      const G = W.grid, hasGround = G && (G.count > 0 || G.tiled);
      const nx = W.cam.x - sy * cp * step, nz = W.cam.z - cy * cp * step;
      if (hasGround && G.tiled && G.pending(nx, nz)) markWait(nx, nz);
      else { W.cam.x = nx; W.cam.z = nz; W.cam.y += sp * step; }
      if (hasGround) { const g = floorAt(G, W.cam.x, W.cam.z, W.cam.y); if (g !== null && W.cam.y < g + 0.3) W.cam.y = g + 0.3; }
      walkStep(0); dirty = true;
    }
  }, { passive: false });
  // téléportation : double-clic (ou double-clic au centre si la souris est capturée)
  const tpRay = new THREE.Raycaster(), tpV = new THREE.Vector2();
  function walkTeleport(nx, ny) {
    if (!model || !walking) return false;
    camera.updateMatrixWorld(true);
    tpV.set(nx, ny);
    tpRay.setFromCamera(tpV, camera);
    const tokens = parseIgnore(cfg.walkIgnore);
    for (const h of tpRay.intersectObject(model, true)) {
      const o = h.object;
      if (!o.isMesh || !o.visible) continue;
      const m = Array.isArray(o.material) ? o.material[h.face ? h.face.materialIndex : 0] : o.material;
      if (m && (isFoliageName(m.name) || nameHas(m.name, tokens))) continue;
      let skip = false;
      if (tokens.length) for (let p = o; p; p = p.parent) if (nameHas(p.name, tokens)) { skip = true; break; }
      if (skip) continue;
      const n = h.face ? h.face.normal.clone().transformDirection(o.matrixWorld) : new THREE.Vector3(0, 1, 0);
      if (n.dot(tpRay.ray.direction) > 0) n.negate();
      let x = h.point.x, z = h.point.z; const y = h.point.y;
      if (n.y < 0.5) { const hl = Math.hypot(n.x, n.z) || 1; x += n.x / hl * 0.5; z += n.z / hl * 0.5; } // mur : on se place devant
      if (W.grid && W.grid.tiled && W.grid.pending(x, z)) { markWait(x, z); return false; }
      const g = W.grid ? W.grid.ground(x, z, y + STEP_UP + 0.05) : null;
      W.pos.set(x, g === null ? y : g, z); W.vy = 0; W.grounded = true;
      dom.style.transition = 'opacity .12s'; dom.style.opacity = '0.35';
      setTimeout(() => { dom.style.opacity = '1'; }, 120);
      dirty = true;
      return true;
    }
    return false;
  }
  // nom de l'élément visé (clic simple)
  function pickNdc(nx, ny) {
    if (!model) return null;
    camera.updateMatrixWorld(true);
    tpV.set(nx, ny); tpRay.setFromCamera(tpV, camera);
    for (const h of tpRay.intersectObject(model, true)) if (h.object.isMesh && h.object.visible) return describePick(h.object, h.point.toArray());
    return null;
  }
  function doPick(e, locked) {
    if (!onPick) return;
    const r = dom.getBoundingClientRect();
    const info = pickNdc(locked ? 0 : (e.clientX - r.left) / r.width * 2 - 1, locked ? 0 : -((e.clientY - r.top) / r.height) * 2 + 1);
    onPick(info, locked ? r.left + r.width / 2 : e.clientX, locked ? r.top + r.height / 2 : e.clientY);
  }
  let downPos = null, lastClick = { t: 0, x: 0, y: 0 };
  dom.addEventListener('pointerdown', e => { downPos = [e.clientX, e.clientY]; });
  dom.addEventListener('click', e => {
    if (linkLock) return;   // mode « Lier à un élément » : exclusif, aucun autre clic n'agit
    if (walking && e.altKey) { if (!W.moved) recenterCam(); return; }   // v35 : Alt + clic = caméra derrière l'avatar (Alt + glisser : orbite, pas de recentrage)
    const locked = document.pointerLockElement === dom, now = e.timeStamp || performance.now();
    {
      const rc = dom.getBoundingClientRect();
      const cnx = locked ? 0 : (e.clientX - rc.left) / rc.width * 2 - 1, cny = locked ? 0 : -((e.clientY - rc.top) / rc.height) * 2 + 1;
      const still = !!downPos && Math.hypot(e.clientX - downPos[0], e.clientY - downPos[1]) < 6;
      if (zones.length && onZone && (walking || (still && !zoneEditor))) {
        const zc = zoneFromClick(cnx, cny, walking ? zoneInfoDist() : 0, true);
        if (zc) { fireZone(zc, 'click'); return; }
      }
    }
    if (!walking) {
      const still = !!downPos && Math.hypot(e.clientX - downPos[0], e.clientY - downPos[1]) < 6;
      if (pickOrbit && onPick && still) doPick(e, false);
      return;
    }
    if (now - lastClick.t < 400 && (locked || Math.hypot(e.clientX - lastClick.x, e.clientY - lastClick.y) < 12)) {
      lastClick.t = 0;
      const r = dom.getBoundingClientRect();
      walkTeleport(locked ? 0 : (e.clientX - r.left) / r.width * 2 - 1, locked ? 0 : -((e.clientY - r.top) / r.height) * 2 + 1);
      if (onPick) onPick(null, 0, 0);
      return;
    }
    lastClick = { t: now, x: e.clientX, y: e.clientY };
    if (document.activeElement && document.activeElement.blur) document.activeElement.blur();
    // un clic ne capture jamais la souris : seulement G ou le bouton « Capturer la souris » (grabMouse) ; sans capture, glisser bouton enfonce tourne la vue
    doPick(e, locked);
  });

  dom.addEventListener('dblclick', e => { if (!walking && !linkLock) setLanding(e); });

  // ---- présence : autres visiteurs (WebSocket)
  let uid = (() => {
    let u = ''; try { u = localStorage.getItem('glb2html_uid') || ''; } catch (_) {}
    if (u.length < 16) {
      const a = new Uint8Array(16);
      if (window.crypto && crypto.getRandomValues) crypto.getRandomValues(a); else for (let i = 0; i < 16; i++) a[i] = Math.random() * 256;
      u = [...a].map(b => b.toString(16).padStart(2, '0')).join('');
      try { localStorage.setItem('glb2html_uid', u); } catch (_) {}
    }
    return u;
  })();
  const P = { ws: null, id: null, peers: new Map(), last: 0, name: '', state: 'off', retry: 0, timer: 0, sent: [0, 0, 0, 0], myColor: null, serverColor: null, opened: false, closeCode: null, closeReason: '', everOpened: false, stopped: false };
  const PRES_TRIES_NEVER = 5, PRES_TRIES_LOST = 12;   // essais de connexion consecutifs avant d'arreter jusqu'au rechargement : jamais ouverte / ouverte puis perdue
  const r2 = v => Math.round(v * 100) / 100;
  const cleanName = s => String(s || '').replace(/[\u0000-\u001f<>]/g, '').trim().slice(0, 24);
  function pStatus(state, reason, stopped) { P.state = state; if (onPresence) onPresence({ state, count: state === 'online' ? P.peers.size + (walking ? 1 : 0) : 0, spectator: !walking, reason: reason || '', stopped: !!stopped }); }
  function setMyName(n) { n = cleanName(n); if (!n) return; P.name = n; if (onName) onName(n); }
  function makeLabel(text) {
    const cv = document.createElement('canvas'); cv.width = 256; cv.height = 64;
    const g = cv.getContext('2d');
    g.fillStyle = 'rgba(255,255,255,0.92)'; g.fillRect(0, 0, 256, 64);
    g.strokeStyle = '#000'; g.lineWidth = 3; g.strokeRect(1.5, 1.5, 253, 61);
    g.fillStyle = '#000'; g.font = 'bold 30px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText(text || '?', 128, 34, 240);
    const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, fog: false }));
    sp.scale.set(1.6, 0.4, 1);
    return sp;
  }
  // reperage des zones image (page exportee, case « Numeros des zones image ») : un gros numero devant chaque zone, masque par le decor (depthTest), jamais cliquable
  function zoneNumText(z) {
    const f = String(z.target || '').split(/[?#]/)[0].split('/').pop(), m = /^\d+/.exec(f) || /\d+/.exec(f);   // numero au debut du nom de fichier, sinon le premier numero du nom
    return m ? String(parseInt(m[0], 10)) : (z.label || z.id);
  }
  function makeNumber(z) {
    const text = zoneNumText(z), cv = document.createElement('canvas'); cv.width = 256; cv.height = 128;
    const g = cv.getContext('2d');
    g.font = 'bold ' + (text.length > 4 ? 56 : 96) + 'px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.lineJoin = 'round';
    g.lineWidth = 12; g.strokeStyle = '#000'; g.strokeText(text, 128, 68, 240); g.fillStyle = '#fff'; g.fillText(text, 128, 68, 240);
    const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
    const w = Math.min(2, Math.max(0.8, z.w * 0.8));
    const sp = new THREE.Mesh(new THREE.PlaneGeometry(w, w / 2), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthTest: true, depthWrite: false, fog: false }));   // a plat dans le plan de l'image (une etiquette tournee vers la camera s'enfoncait dans le mur et coupait les dizaines)
    sp.position.z = 0.06; sp.userData.zoneNum = text;
    return sp;
  }
  function setZoneNumbers(on) {
    zoneNums = !!on;
    for (const g of zoneGroup.children) {
      const old = g.children.find(o => o.userData && o.userData.zoneNum !== undefined);
      if (old) { g.remove(old); old.geometry.dispose(); old.material.map.dispose(); old.material.dispose(); }
      const z = zoneNums && !zoneEditor ? zones.find(q => q.id === g.userData.zoneId) : null;
      if (z && z.type === 'image') g.add(makeNumber(z));
    }
    dirty = true;
  }
  function makeAvatar(name, color) {
    const g = new THREE.Group();
    const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.26, 0.85, 4, 12), new THREE.MeshStandardMaterial({ color, roughness: 0.7 }));
    body.position.y = 0.69; body.userData.tint = true; g.add(body);
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.17, 16, 12), new THREE.MeshStandardMaterial({ color: 0xf0c8a0, roughness: 0.8 }));
    head.position.y = 1.56; g.add(head);
    const nose = new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.12, 8), new THREE.MeshStandardMaterial({ color: 0x333333 }));
    nose.rotation.x = -Math.PI / 2; nose.position.set(0, 1.56, -0.2); g.add(nose);
    const label = makeLabel(name); label.position.y = 2.1; g.add(label);
    // losange flottant (style « plumbob ») à la couleur du visiteur, avec contour noir : visible sans dépendre de la couleur, masqué par les murs
    const beacon = new THREE.Group();
    const dia = new THREE.Mesh(new THREE.OctahedronGeometry(0.26, 0), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.95, fog: false }));
    dia.scale.y = 1.6; dia.userData.tint = true; beacon.add(dia);
    const edg = new THREE.LineSegments(new THREE.EdgesGeometry(dia.geometry), new THREE.LineBasicMaterial({ color: 0x000000, fog: false }));
    edg.scale.y = 1.6; beacon.add(edg);
    beacon.position.y = 2.75; g.add(beacon);
    g.userData.beacon = beacon;
    return g;
  }
  function makeBubble(text) {
    const m = document.createElement('canvas').getContext('2d'); m.font = '28px sans-serif';
    const lines = []; let cur = '';
    for (const w of String(text).split(/\s+/)) { const t = cur ? cur + ' ' + w : w; if (m.measureText(t).width > 470 && cur) { lines.push(cur); cur = w; } else cur = t; }
    if (cur) lines.push(cur);
    const shown = lines.slice(0, 4); if (lines.length > 4) shown[3] = shown[3].slice(0, 36) + '…';
    const lh = 36, h = shown.length * lh + 20;
    const cv = document.createElement('canvas'); cv.width = 512; cv.height = h;
    const g = cv.getContext('2d');
    g.fillStyle = 'rgba(255,255,255,0.95)'; g.fillRect(0, 0, 512, h);
    g.strokeStyle = '#000'; g.lineWidth = 4; g.strokeRect(2, 2, 508, h - 4);
    g.fillStyle = '#000'; g.font = '28px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
    shown.forEach((l, i) => g.fillText(l, 256, 10 + lh / 2 + i * lh, 480));
    const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, fog: false }));
    sp.scale.set(2.56, h * 0.005, 1);
    sp.userData.isBubble = true; sp.userData.w = 2.56; sp.userData.h = h * 0.005;   // taille de base : agrandie avec le même k que le nom
    return sp;
  }
  // hauteurs (repère de l'avatar) du nom, de la bulle et du losange : bas, haut ; pour les tests
  function avatarStack(q) {
    const box = (o, half) => o ? { y: o.position.y, bottom: o.position.y - half, top: o.position.y + half } : null;
    const lab = q.g.children.find(o => o.isSprite && !o.userData.isBubble), bc = q.g.userData.beacon;
    return { label: box(lab, lab ? lab.scale.y / 2 : 0), bubble: box(q.bubble, q.bubble ? q.bubble.scale.y / 2 : 0), beacon: box(bc, bc ? 0.26 * 1.6 * bc.scale.y : 0), dist: camera.position.distanceTo(q.g.position) };
  }
  function removeBubble(q) { if (q.bubble) { q.g.remove(q.bubble); q.bubble.material.map.dispose(); q.bubble.material.dispose(); q.bubble = null; } }
  function showBubble(q, text) { removeBubble(q); q.bubble = makeBubble(text); q.bubbleUntil = cfg.chatFade > 0 ? performance.now() + cfg.chatFade * 1000 : Infinity; q.g.add(q.bubble); }
  function disposeAvatar(g) {
    scene.remove(g);
    g.traverse(o => { if (o.geometry) o.geometry.dispose(); if (o.material) { if (o.material.map) o.material.map.dispose(); o.material.dispose(); } });
  }
  function addPeer(q) {
    if (!q || q.id === P.id || P.peers.has(q.id)) return;
    const g = makeAvatar(q.name, q.color | 0); g.visible = false; scene.add(g);
    const peer = { id: q.id, name: q.name, color: q.color | 0, g, tx: 0, ty: 0, tz: 0, tyaw: 0 };
    if (Array.isArray(q.p)) { peer.tx = q.p[0]; peer.ty = q.p[1]; peer.tz = q.p[2]; peer.tyaw = q.yaw || 0; g.position.set(peer.tx, peer.ty, peer.tz); g.rotation.y = peer.tyaw; g.visible = true; }
    P.peers.set(q.id, peer);
  }
  // v34 : ma couleur choisie part au serveur au plus toutes les 300 ms (le sélecteur de couleur émet en continu) ; la dernière valeur part toujours (le serveur ignore deux changements à moins de 0,2 s)
  let colorT = 0, colorTimer = 0;
  function pushColor() {
    clearTimeout(colorTimer);
    if (P.myColor === null || !P.ws || P.ws.readyState !== 1 || !P.id) return;
    const wait = 300 - (performance.now() - colorT);
    if (wait > 0) { colorTimer = setTimeout(pushColor, wait); return; }
    colorT = performance.now(); P.ws.send(JSON.stringify({ t: 'color', color: P.myColor }));
  }
  // v34 : un visiteur change de couleur en cours de connexion : corps et losange prennent la nouvelle couleur
  function recolorPeer(q, color) { q.color = color; q.g.traverse(o => { if (o.userData.tint && o.material) o.material.color.setHex(color); }); dirty = true; }
  function removePeer(id) { const q = P.peers.get(id); if (q) { disposeAvatar(q.g); P.peers.delete(id); } }
  function clearPeers() { for (const id of [...P.peers.keys()]) removePeer(id); }
  function presenceMsg(m) {
    if (!m || typeof m !== 'object') return;
    if (m.t === 'welcome') {
      P.id = m.id; (m.peers || []).forEach(addPeer); pStatus('online'); dodgeWelcome();
      P.serverColor = Number.isInteger(m.color) && m.color >= 0 && m.color <= 0xFFFFFF ? m.color : null;
      if (m.name) setMyName(m.name);
      if (m.role === 'spectator' && walking && P.ws) P.ws.send(JSON.stringify({ t: 'role', walker: true, name: P.name }));
      if (onChat && cfg.chat !== false) (m.history || []).forEach(h => onChat({ id: h.id, name: cleanName(h.name) || '?', text: String(h.text || '').slice(0, 200), self: false, history: true, n: Number.isFinite(h.n) ? h.n : undefined, ts: Number.isFinite(h.t) ? h.t : undefined }));
    }
    else if (m.t === 'join') { const had = P.peers.has(m.id) || m.id === P.id; addPeer(m); pStatus('online'); if (onChat && cfg.chat !== false) onChat({ system: true, text: tr('core.joined', cleanName(m.name) || '?') }); if (!had && onPeer) onPeer('join', cleanName(m.name) || '?'); }   // v36 : onPeer = visiteur EN PROMENADE qui arrive ou part (jamais moi, jamais la liste initiale)
    else if (m.t === 'leave') { const q = P.peers.get(m.id); removePeer(m.id); pStatus('online'); if (q && onChat && cfg.chat !== false) onChat({ system: true, text: tr('core.left', q.name) }); if (q && onPeer) onPeer('leave', q.name); }
    else if (m.t === 'chat' && cfg.chat !== false) {
      const text = String(m.text || '').slice(0, 200), q = P.peers.get(m.id);
      if (q) showBubble(q, text);
      if (onChat) onChat({ id: m.id, name: cleanName(m.name) || (q && q.name) || '?', text, self: m.id === P.id, history: false, n: Number.isFinite(m.n) ? m.n : undefined, ts: Number.isFinite(m.ts) ? m.ts : undefined });
    }
    else if (m.t === 'history') {   // v37 : page plus ancienne de l'historique du salon (réponse à requestHistory)
      if (onHistory && cfg.chat !== false) onHistory({ more: m.more === true, msgs: (Array.isArray(m.msgs) ? m.msgs : []).slice(0, 100).map(h => ({ id: h.id, name: cleanName(h.name) || '?', text: String(h.text || '').slice(0, 200), self: false, history: true, n: Number.isFinite(h.n) ? h.n : undefined, ts: Number.isFinite(h.t) ? h.t : undefined })) });
    }
    else if (m.t === 'notice') { if (onChat && cfg.chat !== false) onChat({ system: true, text: String(m.text || '').slice(0, 120) }); }
    else if (m.t === 'pos') {
      const q = P.peers.get(m.id);
      if (q && Array.isArray(m.p) && m.p.every(Number.isFinite)) {
        q.tx = m.p[0]; q.ty = m.p[1]; q.tz = m.p[2]; q.tyaw = Number.isFinite(m.yaw) ? m.yaw : q.tyaw;
        if (!q.g.visible) { q.g.position.set(q.tx, q.ty, q.tz); q.g.rotation.y = q.tyaw; q.g.visible = true; }
      }
    }
    else if (m.t === 'name') {
      const q = P.peers.get(m.id);
      if (q) { q.name = cleanName(m.name); const old = q.g.children.find(o => o.isSprite && !o.userData.isBubble); if (old) { q.g.remove(old); old.material.map.dispose(); old.material.dispose(); } const l = makeLabel(q.name); l.position.y = 2.1; q.g.add(l); }
    }
    else if (m.t === 'you') { setMyName(m.name); }
    else if (m.t === 'color') {
      const q = P.peers.get(m.id);
      if (q && Number.isInteger(m.color) && m.color >= 0 && m.color <= 0xFFFFFF) recolorPeer(q, m.color);
    }
    else if (m.t === 'kicked' || m.t === 'banned') {
      P.blocked = true;
      let r = String(m.reason || '').slice(0, 120);
      if (m.t === 'banned' && m.until) r += tr('core.ban.until', new Date(m.until * 1000).toLocaleString(i18nLocale));
      pStatus(m.t, r);
    }
    else if (m.t === 'refused') {   // v51 : refus d'un serveur à créateurs (origine non déclarée, créateur suspendu, salon hors préfixe, trop de salons) : pas de nouvelle tentative
      P.blocked = true;
      const RF = { origin: tr('core.pres.refused.origin'), off: tr('core.pres.refused.off'), room: tr('core.pres.refused.room'), rooms: tr('core.pres.refused.rooms') };
      pStatus('refused', RF[m.why] || tr('core.pres.refused.unknown'));
    }
    else if (m.t === 'full') { pStatus('full'); }
    dirty = true;
  }
  // v51 : adresse de présence ; « * » à la place du nom = le même nom que la page (la présence au même endroit que la page ; disque et viewer : 127.0.0.1) ; 0.0.0.0 -> 127.0.0.1
  function presUrl(u) { return String(u || '').trim().replace(/^(wss?:\/\/)(\*|0\.0\.0\.0)(?=[:/]|$)/i, (m, p, h) => p + (h === '*' ? (location.hostname || '127.0.0.1') : '127.0.0.1')); }
  function presenceConnect() {
    if (!cfg.presenceUrl || P.ws) return;
    P.blocked = false; P.opened = false; P.stopped = false; P.closeCode = null; P.closeReason = '';
    pStatus('connecting');
    let ws;
    try { ws = new WebSocket(presUrl(cfg.presenceUrl)); } catch (e) { pStatus('error', e && e.name === 'SecurityError' ? tr('core.pres.secerr') : tr('core.pres.never')); return; }
    P.ws = ws;
    ws.onopen = () => { P.retry = 0; P.opened = true; P.everOpened = true; { const h = { t: 'hello', room: cfg.room || cfg.roomDefault || '', name: P.name, uid, spectator: !walking }; if (P.myColor !== null) h.color = P.myColor; ws.send(JSON.stringify(h)); } };
    ws.onmessage = ev => { let m; try { m = JSON.parse(ev.data); } catch (_) { return; } presenceMsg(m); };
    ws.onerror = () => {};
    ws.onclose = ev => {
      if (P.ws !== ws) return;
      const code = ev && Number.isInteger(ev.code) ? ev.code : null, why = String((ev && ev.reason) || '').slice(0, 120);   // v45 : code et raison de la fermeture (jamais ouverte : le navigateur donne 1006 sans raison)
      P.closeCode = code; P.closeReason = why;
      P.ws = null; P.id = null; clearPeers();
      if (P.blocked) return;
      if ((walking || spectateOn) && P.state !== 'full') {
        const why2 = P.opened ? tr('core.pres.closed', code === null ? '?' : code, why ? ' : ' + why : '') : tr('core.pres.never');
        clearTimeout(P.timer);
        if (P.retry + 1 >= (P.everOpened ? PRES_TRIES_LOST : PRES_TRIES_NEVER)) { P.stopped = true; pStatus('error', why2, true); }   // essais arretes jusqu'au rechargement de la page (ou jusqu'a un nouveau passage en promenade)
        else { pStatus('error', why2); P.timer = setTimeout(presenceConnect, Math.min(15000, 1500 * (++P.retry))); }
      }
      else if (!walking) pStatus('off');
    };
  }
  function presenceEnter() {
    if (!cfg.presenceUrl) return;
    if (P.ws && P.ws.readyState === 1 && P.id) { P.ws.send(JSON.stringify({ t: 'role', walker: true, name: P.name })); pStatus('online'); }
    else if (!P.ws) presenceConnect();
  }
  function presenceLeave() {
    if (spectateOn && P.ws && P.ws.readyState === 1) { P.ws.send(JSON.stringify({ t: 'role', walker: false })); pStatus('online'); }
    else presenceDisconnect();
  }
  function presenceDisconnect() {
    clearTimeout(P.timer);
    const ws = P.ws; P.ws = null; P.id = null;
    if (ws) { try { ws.close(); } catch (_) {} }
    clearPeers(); if (P.state !== 'off') pStatus('off');
  }
  // v37 : alerte « pseudo cité » : demi-seconde visible, demi-seconde cachée, SANS limite de durée, jusqu'à ma première action (touche, clic, mouvement de l'avatar, envoi) ;
  // concerne l'étiquette du nom de l'auteur, sa bulle (si elle existe encore) et, côté page, la ligne du message (onBlink / onBlinkEnd). Plusieurs citations : toutes clignotent.
  const BL = { on: false, t0: 0, vis: true, px: 0, pz: 0, yaw: 0 };
  function blinkStop() {
    if (!BL.on) return;
    BL.on = false; BL.vis = true;
    for (const q of P.peers.values()) {
      if (!q.blink) continue;
      q.blink = null;
      const lab = q.g.children.find(o => o.isSprite && !o.userData.isBubble); if (lab) lab.visible = true;
      if (q.bubble) q.bubble.visible = true;
    }
    dirty = true;
    if (onBlinkEnd) onBlinkEnd();
  }
  function blinkStart(id) {
    const q = id === undefined ? null : P.peers.get(id);
    if (!BL.on) { BL.on = true; BL.t0 = performance.now(); BL.vis = true; BL.px = W.pos.x; BL.pz = W.pos.z; BL.yaw = W.yaw; }
    if (q) { q.blink = { t0: BL.t0 }; q.blinkHidden = q.blinkHidden || 0; }
    dirty = true;
    return !!q;
  }
  function blinkTick(now) {
    if (!BL.on) return;
    if (walking && (Math.hypot(W.pos.x - BL.px, W.pos.z - BL.pz) > 0.05 || Math.abs(Math.atan2(Math.sin(W.yaw - BL.yaw), Math.cos(W.yaw - BL.yaw))) > 0.02)) { blinkStop(); return; }
    const v = Math.floor((now - BL.t0) / 500) % 2 === 0;
    if (v !== BL.vis) {
      BL.vis = v; dirty = true;
      if (!v) for (const q of P.peers.values()) if (q.blink) q.blinkHidden = (q.blinkHidden || 0) + 1;
      if (onBlink) onBlink(v);
    }
  }
  for (const ev of ['keydown', 'pointerdown']) window.addEventListener(ev, e => { if (BL.on) blinkStop(); }, true);
  function presenceTick(dt, now) {
    blinkTick(now);
    if (P.peers.size) {
      const a = 1 - Math.exp(-dt * 10);
      for (const q of P.peers.values()) {
        if (q.bubble && now > q.bubbleUntil) removeBubble(q);
        if (!q.g.visible) continue;
        q.g.position.x += (q.tx - q.g.position.x) * a; q.g.position.y += (q.ty - q.g.position.y) * a; q.g.position.z += (q.tz - q.g.position.z) * a;
        const d = Math.atan2(Math.sin(q.tyaw - q.g.rotation.y), Math.cos(q.tyaw - q.g.rotation.y));
        q.g.rotation.y += d * a;
        const dist = camera.position.distanceTo(q.g.position), k = Math.max(1, dist / 28);
        const lab = q.g.children.find(o => o.isSprite && !o.userData.isBubble), bc = q.g.userData.beacon;
        if (q.blink) { if (lab) lab.visible = BL.vis; if (q.bubble) q.bubble.visible = BL.vis; }   // v37 : étiquette du nom et bulle clignotent ensemble
        const ks = Math.max(1, dist / 45), ly = 2.1 + 0.55 * (k - 1);
        if (lab) { lab.scale.set(1.6 * k, 0.4 * k, 1); lab.position.y = ly; }
        // pile de bas en haut : nom, bulle (si elle existe), losange, avec une marge entre chacun ; tailles réelles des sprites (scale.y)
        let top = ly + 0.2 * k;                                        // haut du nom
        if (q.bubble) {
          const u = q.bubble.userData; q.bubble.scale.set(u.w * k, u.h * k, 1);
          q.bubble.position.y = top + 0.1 * k + q.bubble.scale.y / 2; top = q.bubble.position.y + q.bubble.scale.y / 2;
        }
        if (bc) {
          bc.scale.setScalar(ks);
          const want = top + 0.5 * ks;                                  // sans bulle : ly + 0,2 k + 0,5 ks, comme avant
          bc.position.y = q.bcY === undefined ? want : q.bcY + (want - q.bcY) * (1 - Math.exp(-dt * 12));   // glisse à l'apparition / disparition de la bulle
          q.bcY = bc.position.y; bc.rotation.y += dt * 1.2;
        }
      }
      dirty = true;
    }
    if (walking && P.ws && P.ws.readyState === 1 && P.id && now - P.last > 90) {
      const cur = [r2(W.pos.x), r2(W.pos.y), r2(W.pos.z), r2(W.yaw)], s = P.sent;
      if (now - P.last > 1000 || cur.some((v, i) => Math.abs(v - s[i]) > 0.004)) {
        P.last = now; P.sent = cur;
        P.ws.send(JSON.stringify({ t: 'pos', p: cur.slice(0, 3), yaw: cur[3] }));
      }
    }
  }

  // ---- zones : panneaux, portails, liens, commandes
  const zoneGroup = new THREE.Group(); scene.add(zoneGroup);
  let selId = null;
  let zones = [], zoneHit = [], zoneAll = [], zoneInside = new Set(), nearZone = null, zoneEditor = false, selBox = null, onZone = null, onNear = null;
  const imgGone = new Set();   // ids des tableaux dont l'image est introuvable (page exportee) : ni cliquables ni zone proche
  let zoneNums = false;   // reperage des zones image : un gros numero devant chacune (jamais memorise ; voir setZoneNumbers)
  // zones liées à un élément du modèle (champ mesh = nom exact) : id de zone -> { meshes, box } ; mesh 3D -> zone
  const zoneLink = new Map(), meshZone = new Map();
  const zoneOf = o => o.userData.zone || meshZone.get(o) || null;
  // boîte englobante (monde) de ces meshes, matrices à jour depuis la racine (modèle recentré, décalé ou mis à l'échelle) ; null si vide
  function boxOfMeshes(meshes) {
    if (model) model.updateMatrixWorld(true);
    const b = new THREE.Box3();
    for (const m of meshes) b.expandByObject(m);
    return b.isEmpty() || !Number.isFinite(b.min.x + b.max.x + b.min.y + b.max.y + b.min.z + b.max.z) ? null : b;
  }
  function findMeshes(ref) {
    const out = new Set();
    // mode tuiles : nœuds des tuiles chargées dont extras.ref est exactement la référence (calculée par glb2tiles sur le GLB entier)
    const objs = TL.on ? (TL.refIndex.get(ref) || []) : resolveMeshRef(model, ref);
    for (const o of objs) o.traverse(c => { if (c.isMesh) out.add(c); });
    return [...out];
  }
  // boîte (monde) de l'élément : en mode tuiles, celle de l'objet ENTIER (extras.box, même si une partie seulement est chargée), sinon celle des morceaux
  function refBox(ref, meshes) {
    if (TL.on && TL.root) {
      for (const o of TL.refIndex.get(ref) || []) {
        const b = o.userData.box;
        if (!Array.isArray(b) || b.length !== 6 || !b.every(Number.isFinite)) continue;
        TL.root.updateMatrixWorld(true);
        const box = new THREE.Box3(), v = new THREE.Vector3();
        for (let k = 0; k < 8; k++) box.expandByPoint(v.set(k & 1 ? b[3] : b[0], k & 2 ? b[4] : b[1], k & 4 ? b[5] : b[2]).applyMatrix4(TL.root.matrixWorld));
        return box;
      }
    }
    return boxOfMeshes(meshes);
  }
  function resolveLinks() {
    zoneLink.clear();
    for (const z of zones) {
      if (!z.mesh || z.type === 'spawn') continue;
      const meshes = findMeshes(z.mesh);
      if (!meshes.length) { if (!TL.on) console.warn(tr('core.zone.nomesh', z.id, z.mesh)); continue; }
      const box = refBox(z.mesh, meshes);
      if (!box) { console.warn(tr('core.zone.nogeom', z.id, z.mesh)); continue; }
      zoneLink.set(z.id, { meshes, box });
    }
    TL.linkSig = linkSignature();
  }
  // contour d'un élément (noir + blanc décalé, lisible sur tout fond)
  function outlineOf(box) {
    const g = new THREE.Group();
    for (const [b, c] of [[box.clone(), 0x000000], [box.clone().expandByScalar(0.05), 0xffffff]]) {
      const h = new THREE.Box3Helper(b, c); h.material.depthTest = false; h.material.transparent = true; h.material.fog = false; h.renderOrder = 999; g.add(h);
    }
    return g;
  }
  const hoverG = new THREE.Group(); hoverG.visible = false; scene.add(hoverG);
  let hoverZone = null, hoverT = 0;
  // page exportée : marqueur discret au sol (id de zone -> matériaux), infobulle au survol
  const MARK_OP = 0.4, markerMat = new Map();
  let tipEl = null;
  function zoneTipText(z) {
    const name = z.label || z.id;
    if (z.type === 'url') return [name, z.target];
    if (z.type === 'image') return [name, z.link || ''];
    if (z.type === 'ha') return [name, tr('core.tip.cmd', name)];
    return [name, tr('core.tip.region', (String(z.target || '').trim() || tr('core.tip.thisregion')) + (z.spawn ? ' #' + z.spawn : ''))];
  }
  function tipShow(z, cx, cy) {
    if (!z) { if (tipEl) tipEl.hidden = true; return; }
    if (!tipEl) {
      tipEl = document.createElement('div'); tipEl.id = 'zoneTip';
      tipEl.style.cssText = 'position:fixed;left:0;top:0;z-index:40;pointer-events:none;max-width:min(420px,90vw);overflow-wrap:anywhere;font:12px/1.4 ui-monospace,Consolas,monospace;background:#000;color:#fff;border:1px solid #fff;border-radius:6px;padding:5px 9px';
      document.body.appendChild(tipEl);
    }
    const [t, sub] = zoneTipText(z);
    const ds = tipObj ? ' · ' + tr('core.tip.dist', coneDist(tipObj)) : '';   // v37 : distance au visiteur, mise à jour à chaque mouvement
    const key = z.id + '|' + ds;
    if (tipEl.dataset.zone !== key) {
      tipEl.dataset.zone = key; tipEl.textContent = '';
      const b = document.createElement('b'); b.textContent = sub ? t : t + ds; tipEl.appendChild(b);
      if (sub) { tipEl.appendChild(document.createElement('br')); tipEl.appendChild(document.createTextNode(sub + ds)); }
    }
    tipEl.hidden = false;
    const w = tipEl.offsetWidth, h = tipEl.offsetHeight;
    tipEl.style.left = Math.max(4, Math.min(innerWidth - w - 4, cx + 14)) + 'px';
    tipEl.style.top = Math.max(4, Math.min(innerHeight - h - 4, cy + 18)) + 'px';
  }
  const ZONE_TYPES = ['url', 'ha', 'portal', 'spawn', 'image'];
  const slug = s => String(s || '').toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40);
  function cleanZone(z, i) {
    const num = (v, d, lo, hi) => { v = Number(v); return Number.isFinite(v) ? Math.min(hi, Math.max(lo, v)) : d; };
    const type = ZONE_TYPES.includes(z.type) ? z.type : 'portal';
    const img = type === 'image';   // image : tableau plaque sur un mur ; h = 0 : hauteur d'apres le rapport de l'image
    const o = {
      id: slug(z.id) || ('z' + (i + 1)), type, label: String(z.label || '').slice(0, 60),
      x: num(z.x, 0, -1e5, 1e5), y: num(z.y, 0, -1e5, 1e5), z: num(z.z, 0, -1e5, 1e5), yaw: num(z.yaw, 0, -7, 7),
      shape: z.shape === 'board' ? 'board' : 'ring', trigger: ['click', 'enter', 'both'].includes(z.trigger) ? z.trigger : 'click',
      radius: num(z.radius, 2, 0.5, 50), w: num(z.w, img ? 1.2 : 2.4, img ? 0.1 : 0.5, 10), h: img ? num(z.h, 0, 0, 6) : num(z.h, 1.2, 0.3, 6),
      target: String(z.target || '').slice(0, 600), spawn: slug(z.spawn), confirm: !!z.confirm, private: !!z.private, showName: !!z.showName,
      mesh: type === 'spawn' || img ? '' : String(z.mesh || '').replace(/[\u0000-\u001f]/g, '').slice(0, 200)
    };
    if (type !== 'portal') o.trigger = 'click';
    if (img) { const lk = String(z.link || '').replace(/[\u0000-\u001f]/g, '').trim().slice(0, 600); if (lk) o.link = lk; }   // lien facultatif d'un tableau : page ouverte au clic ou a E ; ecrit seulement s'il est rempli
    return o;
  }
  function boardTex(label, sub, w, h) {
    const W2 = 512, H2 = Math.max(96, Math.round(512 * h / w));
    const cv = document.createElement('canvas'); cv.width = W2; cv.height = H2;
    const g = cv.getContext('2d');
    g.fillStyle = '#fff'; g.fillRect(0, 0, W2, H2);
    g.strokeStyle = '#000'; g.lineWidth = 10; g.strokeRect(5, 5, W2 - 10, H2 - 10);
    g.fillStyle = '#000'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.font = 'bold 46px sans-serif';
    const words = String(label).split(/\s+/), lines = []; let cur = '';
    for (const w3 of words) { const t = cur ? cur + ' ' + w3 : w3; if (g.measureText(t).width > W2 - 60 && cur) { lines.push(cur); cur = w3; } else cur = t; }
    if (cur) lines.push(cur);
    const shown = lines.slice(0, 3), lh = 54, y0 = H2 / 2 - 14 - (shown.length - 1) * lh / 2;
    shown.forEach((l, i) => g.fillText(l, W2 / 2, y0 + i * lh, W2 - 60));
    g.font = '28px sans-serif'; g.fillText(sub, W2 / 2, H2 - 34, W2 - 60);
    const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
    return tex;
  }
  // v36 : repère de portail (page exportée seulement) : petit cône pointé vers le bas (0,35 m de large, 0,5 m de haut), sommet à 2,0 m au-dessus du centre de la zone,
  // teinte claire neutre avec contour sombre (lisible sans dépendre de la couleur). Au-dessus de chaque portail et de chaque zone « enter » ou « both » ; les arrivées
  // n'en ont qu'avec --show-spawns (cfg.showSpawns). Visible jusqu'à zoneInfoDist en promenade ; T affiche / masque tous les cônes (choix mémorisé, défaut cfg.zoneCone).
  let coneOn = (() => { let v = cfg.zoneCone !== false; try { const s = localStorage.getItem('glb2html_cones'); if (s === '0' || s === '1') v = s === '1'; } catch (_) {} return v; })();
  let onCones = null;
  function coneFor(g, z, box) {
    if (zoneEditor) return false;
    if (!(z.type === 'spawn' ? cfg.showSpawns : (z.type === 'portal' || z.trigger !== 'click'))) return false;
    const geo = new THREE.ConeGeometry(0.175, 0.5, 16);
    const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: 0xe8e8e8, fog: false }));
    m.rotation.x = Math.PI;   // pointe vers le bas
    if (box) m.position.set((box.min.x + box.max.x) / 2, box.max.y + 0.75, (box.min.z + box.max.z) / 2); else m.position.set(0, 2.25, 0);
    m.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({ color: 0x111111, fog: false })));
    m.userData.cone = true; m.userData.zone = z; m.visible = coneOn; m.userData.base = m.position.clone();
    g.add(m); zoneLabs.push(m); zoneAll.push(m);
    if (z.type !== 'spawn') zoneHit.push(m);
    return true;
  }
  // v37 : taille apparente constante : l'échelle suit la distance à la caméra (distance / 12, entre 1 et 12), la pointe reste au même point
  function coneScaleTick() {
    for (const o of zoneLabs) {
      if (!o.userData.cone || !o.visible || !o.parent) continue;
      const b = o.userData.base, px = o.parent.position.x + b.x, py = o.parent.position.y + b.y, pz = o.parent.position.z + b.z;
      const d = Math.hypot(camera.position.x - px, camera.position.y - py, camera.position.z - pz);
      const k = Math.min(12, Math.max(1, d / 12));
      if (Math.abs(o.scale.x - k) > 1e-3) { o.scale.setScalar(k); o.position.y = b.y - 0.25 + 0.25 * k; }
    }
  }
  // distance affichée dans l'infobulle d'un cône : promeneur -> cône, sinon caméra -> cône (arrondie au mètre)
  function coneDist(o) {
    const b = o.userData.base, p = o.parent ? o.parent.position : { x: 0, y: 0, z: 0 }, ref = walking ? W.pos : camera.position;
    return Math.round(Math.hypot(ref.x - (p.x + b.x), ref.y - (p.y + b.y), ref.z - (p.z + b.z)));
  }
  function setCones(on, quiet) {
    coneOn = !!on; try { localStorage.setItem('glb2html_cones', coneOn ? '1' : '0'); } catch (_) {}
    zoneLabelTick(); if (hoverZone) setHover(null); dirty = true;
    if (onCones && !quiet) onCones(coneOn);
    return coneOn;
  }
  window.addEventListener('keydown', e => {
    if (e.code === 'KeyT' && !e.repeat && !typing(e) && !e.ctrlKey && !e.metaKey && !e.altKey && !zoneEditor && zones.length) setCones(!coneOn);
  });
  // zone « image » : un plan texture, a plat contre un mur ; adresse relative a la page ou http(s) ou data: ; introuvable : rien dans la page exportee, panneau dans l'editeur
  // fichier toujours a jour : une requete HEAD sans cache donne l'empreinte du fichier (ETag ou Last-Modified, et taille) ; le fichier est ensuite lu a l'adresse ?v=empreinte,
  // dans le cache s'il y est (aucun retelechargement si le fichier n'a pas change), sinon sur le reseau : un fichier remplace, plus vieux ou plus recent, change d'adresse.
  // cache: 'no-cache' seul ne suffit pas : un serveur repond inchange a un fichier plus vieux que la copie du navigateur. Sans empreinte (ni ETag ni Last-Modified, HEAD refuse) : cache: 'reload'
  // (toujours juste, mais telechargement complet). Comme fetch : renvoie la reponse (404 comprise) ; rejette si la requete est impossible (autre site sans CORS, file://)
  async function freshFetch(u) {
    const h = await fetch(u, { method: 'HEAD', cache: 'no-store' });
    if (h.status === 404 || h.status === 410) return h;
    const sig = h.ok ? (h.headers.get('etag') || h.headers.get('last-modified')) : '';
    if (!sig) return fetch(u, { cache: 'reload' });
    return fetch(u + (u.includes('?') ? '&' : '?') + 'v=' + encodeURIComponent(sig + '|' + (h.headers.get('content-length') || '')), { cache: 'force-cache' });
  }
  // adresse complete d'une image de zone : http(s):, data:, ou /chemin tels quels ; sinon relative au dossier de la region (cfg.imageBase, pose par la coquille), sinon a la page
  function imageUrl(t) {
    t = String(t || '').trim();
    if (!t) return '';
    try { return new URL(/^([a-z][a-z0-9+.\-]*:|\/)/i.test(t) ? t : (cfg.imageBase || '') + t, document.baseURI).href; } catch (_) { return t; }
  }
  // apercu depuis un dossier choisi (editeur) : f(cible) renvoie une adresse blob: ou null (alors adresse habituelle) ; hors editeur : aucun effet
  let imageResolver = null;
  function setImageResolver(f) { imageResolver = typeof f === 'function' ? f : null; if (zones.length) { buildZones(); dirty = true; } }
  // legende d'une image de zone : texte entre le premier « - » du nom de fichier et l'extension (« 1-Soleil_couchant.jpg » : « Soleil couchant »), « _ » devient espace
  function imageCaption(t) {
    t = String(t || '').trim();
    if (!t || /^data:/i.test(t)) return '';
    let b = t.split(/[?#]/)[0].split(/[\\/]+/).pop() || '';
    try { b = decodeURIComponent(b); } catch (_) {}
    b = b.replace(/\.[A-Za-z0-9]{2,5}$/, '');
    const i = b.indexOf('-');
    return i < 0 ? '' : b.slice(i + 1).replace(/_/g, ' ').trim();
  }
  function captionPlane(text, w) {
    const W2 = 1024, H2 = 96, cv = document.createElement('canvas'); cv.width = W2; cv.height = H2;
    const g = cv.getContext('2d');
    g.fillStyle = 'rgba(255,255,255,0.92)'; g.fillRect(0, 0, W2, H2);
    g.fillStyle = '#111'; g.textAlign = 'center'; g.textBaseline = 'middle';
    let px = 56; g.font = px + 'px sans-serif';
    while (px > 22 && g.measureText(text).width > W2 - 40) { px -= 4; g.font = px + 'px sans-serif'; }
    g.fillText(text, W2 / 2, H2 / 2);
    const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, w * H2 / W2), new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide, transparent: true }));
    m.userData.caption = text; return m;
  }
  function imagePlane(z) {
    const mat = new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide, transparent: true });
    const pl = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat);
    const hOf = (iw, ih) => z.h > 0 ? z.h : z.w * (iw && ih ? ih / iw : 0.75);
    pl.scale.set(z.w, hOf(0, 0), 1);
    const capText = imageCaption(z.target); let cap = capText ? captionPlane(capText, z.w) : null;
    const place = () => { if (cap) cap.position.y = -(pl.scale.y / 2 + z.w * 96 / 2048 + 0.03); };
    place(); if (cap) pl.userData.cap = cap;
    const dg = { id: z.id, target: z.target, loaded: '', cap: capText || '', src: capText ? 'name' : '', vis: () => !!(cap && cap.visible) }; pl.userData.diag = dg;   // lu par « Copier le diagnostic »
    const absent = () => {
      console.warn(tr('core.image.missing', z.target || '-'));
      if (zoneEditor) { mat.map = boardTex(z.label || z.id, tr('core.image.missing', z.target || '-'), z.w, pl.scale.y); mat.needsUpdate = true; } else { pl.visible = false; if (cap) cap.visible = false; imgGone.add(z.id); for (const L of [zoneHit, zoneAll]) { const k = L.indexOf(pl); if (k >= 0) L.splice(k, 1); } }
      dirty = true;
    };
    if (!z.target || /^\s*(javascript|vbscript):/i.test(z.target)) { absent(); return pl; }
    const fromUrl = (u, tmp, fail, ok) => new THREE.TextureLoader().load(u, tex => {
      if (tmp) URL.revokeObjectURL(u);
      tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
      mat.map = tex; mat.needsUpdate = true;
      pl.scale.y = hOf(tex.image.width, tex.image.height); place(); dirty = true; if (ok) ok();
    }, undefined, () => { if (tmp) URL.revokeObjectURL(u); (fail || absent)(); });
    // image toujours a jour (freshFetch) : une image remplacee sous le meme nom, plus vieille ou plus recente, apparait sans vider le cache du navigateur ;
    // une balise img n'offre aucun reglage de cache, d'ou fetch puis adresse blob: (liberee apres chargement par fromUrl)
    const fresh = (cand, fail, ok) => {
      const u = imageUrl(cand);
      if (!u || /^(data|blob):/i.test(u)) return fromUrl(u, false, fail, ok);
      freshFetch(u).then(
        r => r.ok ? r.blob().then(b => fromUrl(URL.createObjectURL(b), true, fail, ok), () => fail()) : fail(),
        () => fromUrl(u, false, fail, ok));   // fetch impossible (autre site sans CORS, file://) : chargement direct, comme avant
    };
    const loadCand = (cand, fail, ok) => {
      if (imageResolver) Promise.resolve().then(() => imageResolver(cand)).then(u => u ? fromUrl(u, true, fail, ok) : fresh(cand, fail, ok), () => fresh(cand, fail, ok));
      else fresh(cand, fail, ok);
    };
    // titre : premiere ligne non vide de <nom>.txt s'il existe (a cote de l'image), qui remplace le texte apres le premier tiret du nom de fichier
    const setCap = txt => {
      txt = String(txt || '').replace(/^\uFEFF/, '').split(/\r?\n/).map(s => s.trim()).find(s => s);
      if (!txt) return;
      txt = txt.replace(/\s+/g, ' ').slice(0, 200);
      if (cap) { if (cap.parent) cap.parent.remove(cap); cap.geometry.dispose(); cap.material.map.dispose(); cap.material.dispose(); }
      cap = captionPlane(txt, z.w); cap.visible = pl.visible; pl.userData.cap = cap; dg.cap = txt; dg.src = 'txt';
      if (pl.parent && pl.parent.parent) pl.parent.add(cap);
      place(); dirty = true;
    };
    const captionFromText = names => {   // essaie les noms dans l'ordre (dossier medias, puis dossier de la region) et prend le premier qui existe
      const next = rest => {
        if (!rest.length) return;
        const name = rest[0], more = () => next(rest.slice(1));
        const direct = () => freshFetch(imageUrl(name)).then(r => r.ok ? r.text() : Promise.reject(new Error('absent'))).then(setCap, more);
        if (imageResolver) Promise.resolve().then(() => imageResolver(name)).then(u => u ? fetch(u).then(r => r.text()).then(t => { URL.revokeObjectURL(u); setCap(t); }, () => { URL.revokeObjectURL(u); more(); }) : direct(), () => direct());
        else direct();
      };
      next(names);
    };
    const tz = String(z.target).trim(), bare = !/^([a-z][a-z0-9+.\-]*:|\/)/i.test(tz), hasExt = /\.[A-Za-z0-9]{2,5}$/.test(tz), stem = tz.replace(/\.[A-Za-z0-9]{2,5}$/, '');
    // sous-dossier des medias de la region (cle facultative mediaDir de la config : « medias » par defaut, vide = aucun) : cherche dedans d'abord, puis dans le dossier de la region
    const md = String(cfg.mediaDir === undefined ? 'medias' : (cfg.mediaDir || '')).replace(/^[\\/]+|[\\/]+$/g, ''), dirs = md ? [md + '/', ''] : [''];
    let cands;
    if (!bare) cands = [z.target];
    else if (hasExt) cands = dirs.map(d => d + tz);
    else {   // « 12 » : la page essaie 12.jpg, 12.png... (cfg.imageExts) dans chaque dossier et garde le premier trouve
      const exts = String(cfg.imageExts || 'jpg,jpeg,png,webp,gif,avif').split(/[\s,;]+/).map(e => e.replace(/^\./, '')).filter(Boolean);
      cands = []; for (const d of dirs) for (const e of exts) cands.push(d + stem + '.' + e);
    }
    const go = i => i >= cands.length ? absent() : loadCand(cands[i], () => go(i + 1), () => { dg.loaded = cands[i]; });
    go(0);
    if (bare) captionFromText(dirs.map(d => d + stem + '.txt'));
    return pl;
  }
  function imageDiag() { const o = []; zoneGroup.traverse(n => { const d = n.userData && n.userData.diag; if (d) o.push({ id: d.id, target: d.target, loaded: d.loaded, cap: d.cap, src: d.src, vis: d.vis() }); }); return o; }
  function buildZones() {
    for (const c of [...zoneGroup.children]) {
      zoneGroup.remove(c);
      c.traverse(o => { if (o.geometry) o.geometry.dispose(); if (o.material) { if (o.material.map) o.material.map.dispose(); o.material.dispose(); } });
    }
    if (selBox) { scene.remove(selBox); selBox.geometry.dispose(); selBox.material.dispose(); selBox = null; }
    zoneHit = []; zoneAll = []; zoneLabs = []; meshZone.clear(); imgGone.clear();
    setHover(null);
    markerMat.clear();
    for (const z of zones) {
      if (zoneOff(z)) continue;   // mode tuiles : zone liée à un objet dont aucune tuile n'est chargée
      const link = zoneLink.get(z.id);
      const g = new THREE.Group(); g.userData.zoneId = z.id;
      if (!link) { g.position.set(z.x, z.y, z.z); g.rotation.y = z.yaw; }
      if (z.type === 'image') {
        const pl = imagePlane(z); g.add(pl); if (pl.userData.cap) g.add(pl.userData.cap);
        if (z.link && !zoneEditor && pl.visible) { pl.userData.zone = z; zoneAll.push(pl); zoneHit.push(pl); }   // tableau avec lien : cliquable (survol, clic, E) ; sans lien ou image absente : il ne reagit pas
        if (zoneEditor) { pl.userData.zone = z; zoneAll.push(pl); const lab = makeLabel(z.label || z.id); lab.position.y = (z.h > 0 ? z.h : z.w * 0.75) / 2 + 0.3; lab.material.depthTest = false; lab.renderOrder = 999; g.add(lab); }   // etiquette toujours entiere : le mur peut avoir des reliefs devant elle
        if (zoneNums && !zoneEditor) g.add(makeNumber(z));   // meme si l'image manque : le numero repere l'emplacement
        zoneGroup.add(g);
        continue;
      }
      const kind = { url: tr('core.kind.url'), ha: tr('core.kind.ha'), portal: tr('core.kind.portal'), spawn: tr('core.kind.spawn') }[z.type];
      const priv = zoneEditor && z.private ? tr('core.private') : '';
      const clickable = z.type !== 'spawn' && z.trigger !== 'enter';
      let main = null;
      if (link) {
        // zone liée à un élément : l'élément est la zone (cliquable, E à moins de radius m). Aucun objet ajouté dans la page exportée.
        for (const m of link.meshes) if (!meshZone.has(m)) meshZone.set(m, z);
        zoneAll.push(...link.meshes); if (clickable) zoneHit.push(...link.meshes);
        const hasCone = coneFor(g, z, link.box);
        if (!zoneEditor && !z.showName && !hasCone) continue;
        if (zoneEditor) g.add(outlineOf(link.box));
        if (zoneEditor || z.showName) { const lab = makeLabel(zoneEditor ? (z.label || kind) + ' ⇢ ' + z.mesh + priv : (z.label || z.id)); lab.position.set((link.box.min.x + link.box.max.x) / 2, link.box.max.y + 0.9, (link.box.min.z + link.box.max.z) / 2); g.add(lab); if (!zoneEditor) zoneLabs.push(lab); }
        zoneGroup.add(g);
        continue;
      }
      if (z.type === 'spawn') {
        if (!zoneEditor) {
          // page exportée : les arrivées ne sont jamais dessinées, sauf avec --show-spawns (cfg.showSpawns) : petit marqueur discret au sol
          if (!cfg.showSpawns) continue;
          const sm = new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: MARK_OP, side: THREE.DoubleSide, depthWrite: false, fog: false });
          const sd = new THREE.Mesh(new THREE.CircleGeometry(0.15, 24), sm); sd.rotation.x = -Math.PI / 2; sd.position.y = 0.04; sd.userData.marker = 'spawn'; g.add(sd);
          const sr = new THREE.Mesh(new THREE.RingGeometry(0.15, 0.2, 24), sm.clone()); sr.material.color.set(0xffffff); sr.rotation.x = -Math.PI / 2; sr.position.y = 0.045; sr.userData.marker = 'spawn'; g.add(sr);
          coneFor(g, z);
          zoneGroup.add(g);
          continue;
        }
        const cone = new THREE.Mesh(new THREE.ConeGeometry(0.3, 0.9, 12), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, depthTest: false, fog: false }));
        cone.rotation.x = -Math.PI / 2; cone.position.y = 0.6; g.add(cone); main = cone;
        const l = makeLabel(tr('core.spawn.label', z.id)); l.position.y = 1.7; g.add(l);
      } else if (zoneEditor) {
        // éditeur : le cylindre (portée de la zone) reste toujours visible, pour repérer et positionner ; le panneau s'y ajoute
        if (z.shape === 'board') {
          const sub = kind + (clickable ? tr('core.clickable') : '') + priv;
          const plane = new THREE.Mesh(new THREE.PlaneGeometry(z.w, z.h), new THREE.MeshBasicMaterial({ map: boardTex(z.label || kind, sub, z.w, z.h), side: THREE.DoubleSide, fog: false }));
          plane.position.y = 0.9 + z.h / 2; g.add(plane); main = plane;
          const post = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.92, 0.1), new THREE.MeshStandardMaterial({ color: 0x333333 })); post.position.y = 0.46; g.add(post);
        }
        const rad = z.shape === 'board' ? Math.max(z.radius, 2) : z.radius;
        const cyl = new THREE.Mesh(new THREE.CylinderGeometry(rad, rad, 2.4, 48, 1, true), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.16, side: THREE.DoubleSide, depthWrite: false, fog: false }));
        cyl.position.y = 1.2; g.add(cyl); if (!main) main = cyl; else { cyl.userData.zone = z; zoneAll.push(cyl); }
        const r1 = new THREE.Mesh(new THREE.RingGeometry(Math.max(0.05, rad - 0.16), rad, 64), new THREE.MeshBasicMaterial({ color: 0x000000, side: THREE.DoubleSide, fog: false }));
        r1.rotation.x = -Math.PI / 2; r1.position.y = 0.05; g.add(r1);
        const r2 = new THREE.Mesh(new THREE.RingGeometry(Math.max(0.02, rad - 0.3), Math.max(0.04, rad - 0.16), 64), new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide, fog: false }));
        r2.rotation.x = -Math.PI / 2; r2.position.y = 0.055; g.add(r2);
        if (z.shape !== 'board') { const lab = makeLabel((z.label || kind) + priv); lab.position.y = 2.9; g.add(lab); }
      } else if (z.showName && z.shape === 'board') {
        // page exportée, « Toujours afficher le nom » : le panneau
        const plane = new THREE.Mesh(new THREE.PlaneGeometry(z.w, z.h), new THREE.MeshBasicMaterial({ map: boardTex(z.label || kind, kind + (clickable ? tr('core.clickable') : ''), z.w, z.h), side: THREE.DoubleSide, fog: false }));
        plane.position.y = 0.9 + z.h / 2; g.add(plane); main = plane; zoneLabs.push(plane);
        const post = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.92, 0.1), new THREE.MeshStandardMaterial({ color: 0x333333 })); post.position.y = 0.46; g.add(post); zoneLabs.push(post);
      } else {
        // page exportée, selon cfg.zoneMarker : « dot » (défaut) disque plat 0,4 m + anneau fin ; « range » anneau fin et net au rayon réel de la zone
        // (visible de loin, sans cylindre) ; « none » rien. La zone de visée plus large et invisible reste dans les trois cas.
        const mkind = cfg.zoneMarker === 'range' || cfg.zoneMarker === 'none' ? cfg.zoneMarker : 'dot';
        if (mkind === 'dot') {
          const mat = new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: MARK_OP, side: THREE.DoubleSide, depthWrite: false, fog: false });
          const disc = new THREE.Mesh(new THREE.CircleGeometry(0.2, 32), mat); disc.rotation.x = -Math.PI / 2; disc.position.y = 0.04; disc.userData.marker = 'disc'; g.add(disc);
          const ring = new THREE.Mesh(new THREE.RingGeometry(0.2, 0.26, 32), mat.clone()); ring.material.color.set(0xffffff); ring.rotation.x = -Math.PI / 2; ring.position.y = 0.045; ring.userData.marker = 'ring'; g.add(ring);
          markerMat.set(z.id, [mat, ring.material]);
        } else if (mkind === 'range') {
          const rad = z.shape === 'board' ? Math.max(z.radius, 2) : z.radius;
          const rb = new THREE.Mesh(new THREE.RingGeometry(Math.max(0.02, rad - 0.1), rad, 96), new THREE.MeshBasicMaterial({ color: 0x000000, side: THREE.DoubleSide, fog: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
          rb.rotation.x = -Math.PI / 2; rb.position.y = 0.05; rb.userData.marker = 'range'; rb.userData.radius = rad; g.add(rb);
          const rw = new THREE.Mesh(new THREE.RingGeometry(Math.max(0.01, rad - 0.17), Math.max(0.02, rad - 0.1), 96), new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide, fog: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
          rw.rotation.x = -Math.PI / 2; rw.position.y = 0.055; rw.userData.marker = 'range'; g.add(rw);
          const pts = []; for (let i = 0; i < 96; i++) { const a = i / 96 * Math.PI * 2; pts.push(new THREE.Vector3(Math.cos(a) * rad, 0.06, Math.sin(a) * rad)); }
          const ln = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: 0x000000, fog: false })); ln.userData.marker = 'range'; g.add(ln);   // trait d'un pixel : reste visible de très loin
        }
        if (clickable) {
          // v34 : zone de survol et de clic = l'anneau visible avec « range » (rayon réel de la zone) ; avec « dot » un peu plus large qu'avant (0,6 m au moins, 1 m au plus)
          const hr = mkind === 'range' ? (z.shape === 'board' ? Math.max(z.radius, 2) : z.radius) : (mkind === 'dot' ? Math.max(0.6, Math.min(z.radius, 1)) : 0.6);
          const hit = new THREE.Mesh(new THREE.CircleGeometry(hr, hr > 1 ? 48 : 16), new THREE.MeshBasicMaterial({ side: THREE.DoubleSide })); hit.visible = false;
          hit.rotation.x = -Math.PI / 2; hit.position.y = 0.06; g.add(hit); main = hit;
        }
        if (z.showName) { const lab = makeLabel(z.label || z.id); lab.position.y = 1.2; g.add(lab); zoneLabs.push(lab); }
      }
      coneFor(g, z);
      if (main) { main.userData.zone = z; zoneAll.push(main); if (clickable) zoneHit.push(main); }
      zoneGroup.add(g);
    }
    dirty = true;
  }
  const tilesNoRefs = z => tr('core.zone.norefs', z.id, z.mesh);
  function setZones(list, opts) {
    zoneEditor = !!(opts && opts.editor);
    const seen = new Set();
    zones = (Array.isArray(list) ? list : []).map((z, i) => cleanZone(z || {}, i)).map(z => {
      let id = z.id, n = 2; while (seen.has(id)) id = z.id + '-' + (n++);
      seen.add(id); z.id = id; return z;
    }).filter(z => {
      if (TL.on && TL.refsKnown && !TL.refs && z.mesh && z.type !== 'spawn') { console.warn(tilesNoRefs(z)); return false; }
      return true;
    });
    nearZone = null; zoneInside.clear();
    resolveLinks();
    buildZones();
    return zones.map(z => Object.assign({}, z));
  }
  function zoneSelect(id) {
    selId = id;
    if (selBox) { scene.remove(selBox); selBox.geometry.dispose(); selBox.material.dispose(); selBox = null; }
    const g = zoneGroup.children.find(c => c.userData.zoneId === id);
    const zl = g && zoneLink.get(id);
    if (zl) { selBox = new THREE.Box3Helper(zl.box.clone(), 0x000000); selBox.material.depthTest = false; selBox.material.transparent = true; selBox.material.fog = false; selBox.renderOrder = 999; scene.add(selBox); }
    else if (g) { selBox = new THREE.BoxHelper(g, 0x000000); selBox.material.depthTest = false; selBox.material.transparent = true; scene.add(selBox); }
    dirty = true;
  }
  function fireZone(z, how) {
    if (walking && P.ws && P.ws.readyState === 1 && P.id) P.ws.send(JSON.stringify({ t: 'zone', id: z.id, type: z.type, label: z.label }));
    if (onZone) onZone(z, how);
  }
  // v35 : distance de survol et de clic des zones en promenade (config zoneInfoDist, 5 à 500 m, défaut 150 depuis la v37) ; les noms affichés (showName) la suivent
  const zoneInfoDist = () => Math.max(5, Math.min(500, Number(cfg.zoneInfoDist) || 150));
  let zoneLabs = [];
  function zoneLabelTick() {
    for (const o of zoneLabs) { let v = !walking || !o.parent || Math.hypot(W.pos.x - (o.parent.position.x + o.position.x), W.pos.z - (o.parent.position.z + o.position.z)) <= zoneInfoDist(); if (o.userData.cone) v = v && coneOn; if (o.visible !== v) { o.visible = v; dirty = true; } }
  }
  let lastHitObj = null, tipObj = null;
  function zoneFromClick(nx, ny, maxDist, forClick) {
    if (!zoneHit.length) return null;
    camera.updateMatrixWorld(true);
    tpV.set(nx, ny); tpRay.setFromCamera(tpV, camera);
    // v36 : un cône masqué (T) ne répond pas ; le cône d'un portail « enter » seul n'a qu'une infobulle (pas de clic)
    const h = tpRay.intersectObjects(zoneHit, false).find(q => !(q.object.userData.cone && (!q.object.visible || !coneOn || (forClick && q.object.userData.zone.trigger === 'enter'))));
    lastHitObj = null;
    if (!h || (maxDist && h.distance > maxDist)) return null;
    lastHitObj = h.object;
    const z = zoneOf(h.object), link = z && zoneLink.get(z.id);
    if (model) {
      // un élément traversable (walkIgnore) ne bloque pas le clic, ni les autres morceaux de l'élément visé
      const tokens = parseIgnore(cfg.walkIgnore);
      for (const m of tpRay.intersectObject(model, true)) {
        if (m.distance >= h.distance - 0.05) break;
        if (isIgnoredMesh(m.object, tokens) || (link && link.meshes.includes(m.object))) continue;
        return null;
      }
    }
    return z;
  }
  function setHover(z, cx, cy) {
    if (z && cx !== undefined) tipShow(z, cx, cy);
    if (z === hoverZone) return;
    if (hoverZone) for (const m of markerMat.get(hoverZone.id) || []) m.opacity = MARK_OP;
    if (!z) tipShow(null);
    hoverZone = z;
    if (z) { const mm = markerMat.get(z.id); if (mm) for (const m of mm) m.opacity = 0.8; }
    const link = z && zoneLink.get(z.id);
    hoverG.visible = !!link;
    if (link) { hoverG.clear(); hoverG.add(outlineOf(link.box)); }
    dom.style.cursor = z ? 'pointer' : '';
    dirty = true;
  }
  dom.addEventListener('pointermove', e => {
    if (linkLock || zoneEditor || !onZone || !zoneHit.length || e.buttons || document.pointerLockElement === dom) { if (hoverZone) setHover(null); return; }
    const now = performance.now(); if (now - hoverT < 50) return; hoverT = now;
    const r = dom.getBoundingClientRect();
    const zh = zoneFromClick((e.clientX - r.left) / r.width * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1, walking ? zoneInfoDist() : 0);
    tipObj = zh && lastHitObj && lastHitObj.userData.cone ? lastHitObj : null;
    setHover(zh, e.clientX, e.clientY);
  });
  dom.addEventListener('pointerleave', () => setHover(null));
  function zonePickAt(cx, cy) {
    if (!zoneAll.length) return null;
    const r = dom.getBoundingClientRect();
    camera.updateMatrixWorld(true);
    tpV.set((cx - r.left) / r.width * 2 - 1, -((cy - r.top) / r.height) * 2 + 1); tpRay.setFromCamera(tpV, camera);
    const h = tpRay.intersectObjects(zoneAll, false)[0];
    return h ? zoneOf(h.object) : null;
  }
  // distance horizontale du marcheur à la zone (ou à son élément s'il est lié) et écart vertical (0 = à hauteur de l'élément)
  function zoneDist(z) {
    const l = zoneLink.get(z.id);
    if (!l) return { d: Math.hypot(W.pos.x - z.x, W.pos.z - z.z), dy: W.pos.y - z.y };
    const b = l.box, p = W.pos;
    return { d: Math.hypot(Math.max(b.min.x - p.x, 0, p.x - b.max.x), Math.max(b.min.z - p.z, 0, p.z - b.max.z)), dy: p.y < b.min.y ? p.y - b.min.y : (p.y > b.max.y ? p.y - b.max.y : 0) };
  }
  function zoneTick() {
    if (!zones.length) return;
    let best = null, bd = 1e9;
    for (const z of zones) {
      if (z.type === 'spawn' || zoneOff(z) || (z.type === 'image' && (!z.link || imgGone.has(z.id)))) continue;   // un tableau sans lien n'est pas une zone proche (pas d'invite « clic ou E »)
      const { d, dy } = zoneDist(z);
      if (z.type === 'portal' && z.trigger !== 'click') {
        const inside = d <= z.radius && dy > -1.5 && dy < 3.5, was = zoneInside.has(z.id);
        if (inside && !was) { zoneInside.add(z.id); fireZone(z, 'enter'); }
        else if (!inside && was) zoneInside.delete(z.id);
      }
      if (z.trigger !== 'enter') {
        const reach = zoneLink.has(z.id) ? z.radius : (z.shape === 'board' ? Math.max(z.radius, 2) : z.radius) + 1.5;
        if (d <= reach && Math.abs(dy) < 3.5 && d < bd) { best = z; bd = d; }
      }
    }
    if (best !== nearZone) { nearZone = best; if (onNear) onNear(best); }
  }
  // v36 : E déclenche la zone proche (déclenchement « clic » ou « both »), comme avant la v35 ; E ne fait rien d'autre
  window.addEventListener('keydown', e => {
    if (e.code === 'KeyE' && !e.repeat && walking && !typing(e) && !e.ctrlKey && !e.metaKey && !e.altKey && nearZone && onZone) fireZone(nearZone, 'key');
  });
  // ---- repère d'atterrissage : un cercle posé sur le sol, sous la cible de la vue globale (où F pose l'avatar)
  let onLanding = null, landY = null, landKey = '', landT = 0, landDirty = false;
  const UPV = new THREE.Vector3(0, 1, 0), landN = new THREE.Vector3(0, 1, 0);
  function faceUp(h, out) {
    out.copy(UPV);
    if (h.face) { const n = h.face.normal.clone().transformDirection(h.object.matrixWorld); if (n.y < 0) n.negate(); if (n.y > 0.6) out.copy(n); }
  }
  const landing = new THREE.Group(); landing.visible = false; scene.add(landing);
  {
    const bm = o => Object.assign({ transparent: true, opacity: 0.85, depthTest: true, depthWrite: false, fog: false, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 }, o);
    const ro = new THREE.Mesh(new THREE.RingGeometry(0.75, 0.9, 40), new THREE.MeshBasicMaterial(bm({ color: 0x000000 })));
    ro.rotation.x = -Math.PI / 2; ro.position.y = 0.06; landing.add(ro);
    const ri = new THREE.Mesh(new THREE.RingGeometry(0.6, 0.75, 40), new THREE.MeshBasicMaterial(bm({ color: 0xffffff })));
    ri.rotation.x = -Math.PI / 2; ri.position.y = 0.065; landing.add(ri);
  }
  const downRay = new THREE.Raycaster(), DOWN = new THREE.Vector3(0, -1, 0);
  function solidHit(h, tokens) {
    const o = h.object;
    if (!o.isMesh || !o.visible) return false;
    const m = Array.isArray(o.material) ? o.material[h.face ? h.face.materialIndex : 0] : o.material;
    if (m && (isFoliageName(m.name) || nameHas(m.name, tokens))) return false;
    return !isIgnoredMesh(o, tokens);
  }
  // même règle que l'atterrissage : surface la plus haute à moins de 2 m au-dessus de la cible, sinon la plus haute du modèle
  function groundUnder(t) {
    if (!model) return null;
    const tokens = parseIgnore(cfg.walkIgnore);
    for (const oy of [t.y + 2, 1e5]) {
      downRay.set(new THREE.Vector3(t.x, oy, t.z), DOWN);
      for (const h of downRay.intersectObject(model, true)) if (solidHit(h, tokens)) { faceUp(h, landN); return h.point.y; }
    }
    return null;
  }
  const tkey = t => t.x.toFixed(2) + ',' + t.y.toFixed(2) + ',' + t.z.toFixed(2);
  function landingTick(now) {
    const show = !!model && !walking && cfg.landingMarker !== false;
    if (landing.visible !== show) { landing.visible = show; dirty = true; }
    if (!show) return;
    const t = controls.target, k = tkey(t);
    if (k !== landKey) { landKey = k; landT = now; landDirty = true; }
    if (landDirty && now - landT > 120) { landDirty = false; landY = groundUnder(t); dirty = true; }
    landing.position.set(t.x, landY === null ? t.y : landY, t.z);
    landing.quaternion.setFromUnitVectors(UPV, landN);
    landing.scale.setScalar(Math.max(1, camera.position.distanceTo(t) / 60));
  }
  function setLanding(e) {
    if (!model) return false;
    const r = dom.getBoundingClientRect();
    camera.updateMatrixWorld(true);
    tpV.set((e.clientX - r.left) / r.width * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1); tpRay.setFromCamera(tpV, camera);
    const tokens = parseIgnore(cfg.walkIgnore);
    for (const h of tpRay.intersectObject(model, true)) {
      if (!solidHit(h, tokens)) continue;
      controls.target.copy(h.point); controls.update(); dirty = true;
      landY = h.point.y; landKey = tkey(controls.target); landDirty = false; faceUp(h, landN);
      if (onLanding) onLanding(h.point.toArray());
      return true;
    }
    // mode tuiles : la vue d'ensemble sert à désigner un point lointain (la cible suit, les tuiles se chargent) ; le sol réel est repris dès que la tuile est prête
    if (OV.root) for (const h of tpRay.intersectObjects(ovCells(), true)) {
      if (!h.object.isMesh) continue;
      controls.target.copy(h.point); controls.update(); dirty = true;
      landY = h.point.y; landKey = tkey(controls.target); landDirty = false; faceUp(h, landN);
      if (onLanding) onLanding(h.point.toArray());
      return true;
    }
    return false;
  }

  const clock = new THREE.Clock();
  const RS = { times: [], last: 0 };   // v42 : instants des derniers rendus (diagnostic), plafond d'images par seconde (cfg.fpsMax, 0 = sans limite)
  function renderStats() {
    const now = performance.now(), causes = [];
    if (seaMat && seaMat.uniforms) causes.push('sea');
    if (P.peers.size) causes.push('peers');
    if (walking) causes.push('walk');
    if (TL.on && (TL.inflight > 0 || TL.gridQ.length)) causes.push('tiles');
    return { rate: RS.times.filter(t => now - t <= 5000).length / 5, causes };
  }
  renderer.setAnimationLoop(() => {
    const dt = Math.min(clock.getDelta(), 0.1);
    let moved = false;
    if (walking) { walkStep(dt); moved = true; } else moved = controls.update();
    if (TL.on) tilesTick(performance.now());
    presenceTick(dt, performance.now());
    landingTick(performance.now());
    if (seaMat && seaMat.uniforms) { seaMat.uniforms.uTime.value = clock.elapsedTime; dirty = true; }
    if (dirty || moved) {
      const now = performance.now(), fm = Number(cfg.fpsMax);
      if (fm > 0 && now - RS.last < 1000 / fm - 2) { dirty = true; return; }   // plafond atteint : l'image attend le tour suivant
      RS.last = now; RS.times.push(now); if (RS.times.length > 400) RS.times.splice(0, RS.times.length - 400);
      if (zoneLabs.length) coneScaleTick(); renderer.render(scene, camera); dirty = false;
    }
  });

  return {
    scene, camera, renderer, controls, cfg, setCfg, setModel, loadBuffer, imageUrl, freshFetch, setImageResolver, frame, getCameraState, setZoom, renderStats,
    get model() { return model; }, get sea() { return sea; }, set onCfg(f) { onCfg = f; }, set onWalk(f) { onWalk = f; }, set onPick(f) { onPick = f; }, set pickOrbit(v) { pickOrbit = !!v; }, set onPresence(f) { onPresence = f; }, set onChat(f) { onChat = f; }, set onPeer(f) { onPeer = f; },
    setZones, setZoneNumbers, zoneSelect, zonePickAt, findMeshes, imageDiag,
    // v36 : repères de portail (cônes) : affichés ou non (T), rappel, état pour les tests
    setCones, get cones() { return coneOn; }, set onCones(f) { onCones = f; },
    getCones() { const out = []; zoneGroup.traverse(o => { if (o.userData && o.userData.cone) { const p = o.getWorldPosition(new THREE.Vector3()); camera.updateMatrixWorld(true); const r = dom.getBoundingClientRect(), pr = p.clone().project(camera), d = camera.position.distanceTo(p); out.push({ id: o.userData.zone.id, visible: o.visible, pos: p.toArray(), scale: o.scale.x, dist: d, sx: r.left + (pr.x + 1) / 2 * r.width, sy: r.top + (1 - pr.y) / 2 * r.height, px: 0.35 * o.scale.x / (2 * d * Math.tan(camera.fov * Math.PI / 360)) * r.height }); } }); return out; },
    // mode tuiles (cfg.tiles) : voir loadTiles ; tilesState sert aux tests
    closeTiles, releaseAnchor, get seaCenter() { return [seaCx, seaCz]; },
    // v32 : le point visé (rayon THREE.Raycaster) sur la vue d'ensemble, hors tuiles chargées ; null si rien
    overviewHit(ray) { for (const h of ray.intersectObjects(ovCells(), true)) if (h.object.isMesh) return h.point.toArray(); return null; },
    // v32 : demande le chargement des tuiles autour de (x, z) pendant 15 s ; rend les fichiers des tuiles qui contiennent ce point
    tilesForce(x, z) { TL.forced = { x, z }; TL.forcedUntil = performance.now() + 15000; tilesUpdate(performance.now()); return TL.tiles.filter(t => inTile(t, x, z, TILE_M)).map(t => t.file); },
    // v32 : état des zones telles que la scène les montre (tests, diagnostic)
    getZoneState() {
      return zones.map(z => {
        const l = zoneLink.get(z.id), g = zoneGroup.children.find(c => c.userData.zoneId === z.id), off = zoneOff(z);
        return { id: z.id, type: z.type, mesh: z.mesh || '', linked: !!l, off, shown: !off, box: l ? l.box.min.toArray().concat(l.box.max.toArray()) : null,
          pos: l ? [(l.box.min.x + l.box.max.x) / 2, l.box.min.y, (l.box.min.z + l.box.max.z) / 2] : (g ? g.position.toArray() : [z.x, z.y, z.z]) };
      });
    },
    // v33 : marqueurs dessinés pour chaque zone (tests, diagnostic) : types (disc, ring, range, spawn) et rayon de l'anneau de portée
    getMarkers() {
      return zoneGroup.children.map(g => { const k = []; let radius = null; g.traverse(o => { if (o.userData && o.userData.marker) { k.push(o.userData.marker); if (o.userData.radius) radius = o.userData.radius; } }); return { id: g.userData.zoneId, kinds: k, radius }; });
    },
    loadTiles, tilesState, get tiled() { return TL.on; }, set onTiles(f) { TL.onInfo = f; TL.infoKey = ''; if (f) tilesInfo(); }, set onTileError(f) { TL.onError = f; },
    // référence (champ mesh d'une zone) de cet objet du modèle : nom, ou nom#index si le nom est partagé
    meshRef(o) {
      if (TL.on && TL.root) { for (let p = o; p && p !== TL.root; p = p.parent) if (p.userData && typeof p.userData.ref === 'string') return p.userData.ref; return ''; }
      return model ? meshRefOf(model, o) : (o.name || '');
    }, get rotation() { return modelRot; },
    // boîte (monde) de l'élément de ce nom : { min, max, center, count } ou null
    meshInfo(name) { const m = findMeshes(name); const b = m.length ? refBox(name, m) : null; if (!b) return null; return { min: b.min.toArray(), max: b.max.toArray(), center: b.getCenter(new THREE.Vector3()).toArray(), size: b.getSize(new THREE.Vector3()).toArray(), count: m.length }; },
    set linkMode(v) { linkLock = !!v; },
    isTraversable(o) { return isIgnoredMesh(o, parseIgnore(cfg.walkIgnore)); }, getZones() { return zones.map(z => Object.assign({}, z)); }, set onZone(f) { onZone = f; }, set onNear(f) { onNear = f; },
    captureTop(size = 320, hide = []) {
      if (!model) return null;
      const box = new THREE.Box3().setFromObject(model), c = box.getCenter(new THREE.Vector3()), sz = box.getSize(new THREE.Vector3());
      const h = (Math.max(sz.x, sz.z) * 0.53) || 50, cv = renderer.domElement, W = cv.width, H = cv.height, a = W / H;
      const cam = new THREE.OrthographicCamera(-h * a, h * a, h, -h, 1, (box.max.y - box.min.y) + 3000);
      cam.position.set(c.x, box.max.y + 500, c.z); cam.up.set(0, 0, -1); cam.lookAt(c.x, 0, c.z);
      cam.updateProjectionMatrix(); cam.updateMatrixWorld(true);
      const hidden = [];
      for (const o of [landing, zoneGroup, hoverG, selfAv, ...hide, ...[...P.peers.values()].map(q => q.g)]) if (o && o.visible) { o.visible = false; hidden.push(o); }
      const fog = scene.fog; scene.fog = null;
      renderer.render(scene, cam);
      const out = document.createElement('canvas'); out.width = out.height = size;
      const s = Math.min(W, H);
      out.getContext('2d').drawImage(cv, (W - s) / 2, (H - s) / 2, s, s, 0, 0, size, size);
      const url = out.toDataURL('image/jpeg', 0.82);
      scene.fog = fog; hidden.forEach(o => { o.visible = true; }); dirty = true;
      return url;
    },
    getName() { return P.name; }, set onLanding(f) { onLanding = f; }, set onName(f) { onName = f; },
    spectate(on) { spectateOn = !!on; if (spectateOn) { if (cfg.presenceUrl && !P.ws) presenceConnect(); } else if (!walking) presenceDisconnect(); },
    // v37 : demande les n messages précédant le message numéro `before` ; un ancien serveur ne répond pas (la page masque alors le bouton)
    requestHistory(before, n) { if (!P.ws || P.ws.readyState !== 1 || !P.id || !Number.isFinite(before)) return false; P.ws.send(JSON.stringify({ t: 'history', before, n: n || 50 })); return true; },
    set onHistory(f) { onHistory = f; },
    sendChat(text) {
      const t = String(text || '').replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, 200);
      if (!t || !P.ws || P.ws.readyState !== 1 || !P.id) return false;
      P.ws.send(JSON.stringify({ t: 'chat', text: t })); return true;
    },
    releaseKeys() { W.keys.clear(); },
    // v33 : touches fléchées tenues depuis la saisie du chat (les lettres vont dans le texte, les flèches déplacent l'avatar)
    holdKey(code, on) { if (!walking || !code.startsWith('Arrow')) return; if (on) W.keys.add(code); else W.keys.delete(code); },
    // v46 : flèches à l'écran : touche tenue (avancer, reculer, tourner, monter, descendre), saut, course allumée par un clic, vue globale pas à pas
    padKey(code, on) { if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'KeyA', 'KeyD', 'PageUp', 'PageDown'].includes(code)) return false; if (!walking) { W.keys.delete(code); return false; } if (on) W.keys.add(code); else W.keys.delete(code); return true; },
    padJump() { if (!walking || W.fly || W.view === 'free') return false; W.jumpReq = true; return true; },
    get runLatch() { return !!W.runLatch && walking; }, set runLatch(v) { W.runLatch = !!v && walking; if (onView) onView(); },
    globalMove, globalTurn, globalZoom,
    // v33 : point de retour ({ pos, yaw, forF }), aller à, retour, vol, vues, couleur choisie, clignotement de bulle
    setHome(h) { home = h && Array.isArray(h.pos) && h.pos.length >= 3 && h.pos.every(Number.isFinite) ? { pos: h.pos.slice(0, 3), yaw: Number.isFinite(h.yaw) ? h.yaw : undefined, forF: !!h.forF } : null; },
    get home() { return home; }, goTo, returnHome, toggleFly, cycleView, setView,
    set onMouse(f) { onMouse = f; }, grabMouse, get mouseState() { return mouseState(); }, set onView(f) { onView = f; }, set onFly(f) { onFly = f; }, tickPresence(dt, now) { presenceTick(dt, now); },   // tickPresence : pas de présence à la main, pour les tests (bulle qui clignote)
    get viewName() { return VIEW_NAMES[W.view]; }, get view() { return W.view; }, get flying() { return W.fly; }, getHeading() {   // v37 : cap en degrés (0 = nord, sens horaire). Nord d'OpenSim = -Z du modèle ; + rotation de la région + cfg.northDeg
      let psi;
      if (walking) psi = W.yaw;
      else { const d = camera.getWorldDirection(new THREE.Vector3()); if (Math.hypot(d.x, d.z) < 1e-4) return null; psi = Math.atan2(-d.x, -d.z); }
      const deg = rotDeg() - psi * 180 / Math.PI + (Number(cfg.northDeg) || 0);
      return ((deg % 360) + 360) % 360;
    },
    get running() { return !!W.runOn && walking; },
    // v34 : la couleur choisie est envoyée au serveur aussitôt si la connexion est ouverte (sinon dans « hello ») ; l'avatar du visiteur la prend
    setMyColor(c) {
      P.myColor = Number.isInteger(c) && c >= 0 && c <= 0xFFFFFF ? c : null;
      pushColor();
      if (walking) updateSelf();
    },
    // v34 : clé d'identité du navigateur (lien personnel) : lecture, remplacement (la connexion est refaite pour que le serveur reconnaisse la clé)
    getUid() { return uid; },
    setUid(k) {
      if (!/^[0-9a-f]{32}$/.test(String(k))) return false;
      uid = String(k); try { localStorage.setItem('glb2html_uid', uid); } catch (_) {}
      if (P.ws) { const ws = P.ws; P.ws = null; P.id = null; try { ws.close(); } catch (_) {} clearPeers(); if (walking || spectateOn) presenceConnect(); }
      return true;
    },
    blinkBubble: blinkStart, blinkStop, get blinking() { return BL.on; }, set onBlink(f) { onBlink = f; }, set onBlinkEnd(f) { onBlinkEnd = f; },
    setName(n) { P.name = cleanName(n); if (P.ws && P.ws.readyState === 1) P.ws.send(JSON.stringify({ t: 'name', name: P.name })); },
    getPresence() { return { state: P.state, id: P.id, opened: P.opened, stopped: P.stopped, tries: P.retry, closeCode: P.closeCode, closeReason: P.closeReason, peers: [...P.peers.values()].map(q => ({ id: q.id, name: q.name, pos: q.g.position.toArray(), visible: q.g.visible, bubble: !!q.bubble, bubbleVisible: !!q.bubble && q.bubble.visible, labelVisible: (q.g.children.find(o => o.isSprite && !o.userData.isBubble) || { visible: null }).visible, blinking: !!q.blink, blinkHidden: q.blinkHidden || 0, color: q.color, stack: avatarStack(q) })) }; }, get walking() { return walking; },
    walkTick(dt) { if (walking) walkStep(dt); },
    refreshCollision() { if (TL.on) { for (const t of TL.tiles) if (t.state === 'ready' && t.grp) { t.state = 'building'; t.grid = null; t.gen = collisionGridSteps(t.grp, 3, parseIgnore(cfg.walkIgnore)); t.qAt = performance.now(); t.qFirst = true; t.gridCpu = 0; TL.gridQ.push(t); } } else if (walking && model) W.grid = buildCollisionGrid(model, 3, parseIgnore(cfg.walkIgnore)); },
    teleportNdc(nx, ny) { return walkTeleport(nx, ny); },
    toggleWalk, pressF, recenterCam, startFly, walkStart, walkStop, teleportTo,
    getWalk() { return { pos: W.pos.toArray(), yaw: W.yaw, pitch: W.pitch, grounded: W.grounded, tris: W.grid ? W.grid.count : 0, flying: W.fly, view: W.view, camYaw: W.view === 'tps' ? W.tyaw : (W.view === 'free' ? W.cyaw : W.yaw), tpsDist: W.tdist, camPitch: W.view === 'tps' ? W.tpitch : (W.view === 'free' ? W.cpitch : W.pitch), running: W.run.size > 0 || W.keys.has('ShiftLeft') || W.keys.has('ShiftRight') || !!W.runLatch, cam: camera.position.toArray(), selfVisible: !!(selfAv && selfAv.visible) }; }, get fit() { return fit; }, requestRender() { dirty = true; }
  };
}


async function b64ToBuffer(b64) {
  try { return await (await fetch('data:application/octet-stream;base64,' + b64)).arrayBuffer(); }
  catch (e) {
    const bin = atob(b64), out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out.buffer;
  }
}

const loader = new GLTFLoader();
__DECODERS__
// v34 : lien personnel (#key=CLE, 32 caractères hexadécimaux) : sans clé déjà mémorisée dans ce navigateur, elle devient la clé de ce navigateur avant la création du visiteur
const KEYH = (() => { const k = hashParams().get('key'); return k && /^[0-9a-f]{32}$/.test(k) ? k : null; })();
let uidStored = ''; try { uidStored = localStorage.getItem('glb2html_uid') || ''; } catch (e) {}
if (KEYH && !uidStored) { try { localStorage.setItem('glb2html_uid', KEYH); uidStored = KEYH; } catch (e) {} }
// v42 : rendu léger. Réglages fins du visiteur, retenus par ce navigateur ; « normal » = valeurs de la page, « préconisé » = mode léger ;
// --light : la page s'ouvre en mode léger tant que le visiteur n'a rien choisi. L'anticrénelage est fixé à la création du contexte WebGL.
const LIGHT = (() => {
  const key = 'glb2html_light_' + (C.room || 'x'), radius = Number(C.tileRadius) > 0 ? Number(C.tileRadius) : 150;
  const normal = { on: false, scale: 1, fps: 0, ovOnly: false, radius, aa: true };
  const preset = { on: true, scale: 0.5, fps: 15, ovOnly: true, radius: Math.min(radius, 80), aa: false };
  const base = () => Object.assign({}, C.light ? preset : normal), st = base();
  let asked = false;
  try {
    const s = JSON.parse(localStorage.getItem(key) || 'null');
    if (s && typeof s === 'object') {
      if (typeof s.on === 'boolean') st.on = s.on;
      if (Number.isFinite(s.scale)) st.scale = Math.min(1, Math.max(0.25, s.scale));
      if (Number.isFinite(s.fps)) st.fps = Math.min(60, Math.max(0, Math.round(s.fps)));
      if (typeof s.ovOnly === 'boolean') st.ovOnly = s.ovOnly;
      if (Number.isFinite(s.radius)) st.radius = Math.min(5000, Math.max(10, s.radius));
      if (typeof s.aa === 'boolean') st.aa = s.aa;
      asked = !!s.asked;
    }
  } catch (e) {}
  const store = v => { try { localStorage.setItem(key, JSON.stringify(v)); } catch (e) {} };
  return { key, normal, preset, base, st, store, get asked() { return asked; }, set asked(v) { asked = !!v; },
    save() { asked = true; store(Object.assign({ asked: true }, st)); },
    cfg() { return { pixelScale: st.scale, fpsMax: st.fps, ovOnly: st.ovOnly, tileRadius: st.radius }; } };
})();
Object.assign(C, LIGHT.cfg(), { antialias: LIGHT.st.aa });
const viewer = createViewer(document.getElementById('view'), C, loader);
let lightSync = null;   // v42 : remet les commandes de la sous-fenêtre aux valeurs en cours (Réglages)
function lightApply(v) { Object.assign(LIGHT.st, v || {}); LIGHT.save(); viewer.setCfg(LIGHT.cfg()); if (lightSync) lightSync(); }
function lightReset() { Object.assign(LIGHT.st, LIGHT.base()); LIGHT.asked = true; LIGHT.store({ asked: true }); viewer.setCfg(LIGHT.cfg()); if (lightSync) lightSync(); }
const H = hashParams();
// #pos=x,y,z[,yaw] : arrivée anonyme à ce point (nombres seulement, repère de la page : modèle d'origine en mode tuiles) ; une valeur invalide est ignorée
const posArr = (() => {
  if (!H.has('pos')) return null;
  const v = (H.get('pos') || '').split(',').map(x => (x.trim() === '' ? NaN : Number(x)));
  if ((v.length !== 3 && v.length !== 4) || !v.every(Number.isFinite) || v.some(x => Math.abs(x) > 1e5)) { console.warn(tr('page.pos.invalid')); return null; }
  return v;
})();
const arrival = H.has('spawn') || !!posArr;
const keepTarget = C.targetExplicit !== false;   // --target explicite (ou configuration sans cette clé, d'avant la v33) : le cadrage de départ reste la cible
const fade = document.getElementById('fade');
// 1.4.5 : « À propos de la région » : NOM.about.<langue>.txt, sinon NOM.about.txt, à côté de NOM.config.json (région chargée par la coquille ; absent d'une page autonome).
// Un site statique ne peut pas lister un dossier : essais par fetch, un 404 est silencieux. Texte brut (textContent) ; première ligne = titre.
const ABOUT = { text: '', title: '', name: '', ready: null, ABOUT_MAX: 20000 };
ABOUT.ready = (async () => {
  if (typeof BOOT === 'undefined' || !BOOT || !BOOT.about) return;
  ABOUT.name = String(BOOT.name || '');
  for (const f of [BOOT.about + '.' + LANG + '.txt', BOOT.about + '.txt']) {
    try {
      const r = await fetch(f, { cache: 'no-store' });
      if (!r.ok || /html/i.test(r.headers.get('content-type') || '')) continue;   // un serveur qui répond une page d'accueil à la place d'un 404 n'est pas un à propos
      let t = (await r.text()).replace(/^\ufeff/, '').replace(/\r\n?/g, '\n').trim();
      if (!t) continue;
      if (t.length > ABOUT.ABOUT_MAX) t = t.slice(0, ABOUT.ABOUT_MAX) + '…';
      const i = t.indexOf('\n');
      ABOUT.title = (i < 0 ? t : t.slice(0, i)).trim(); ABOUT.text = i < 0 ? '' : t.slice(i + 1).trim();
      if (!ABOUT.title) { ABOUT.title = tr('page.about.btn'); }
      ABOUT.found = true; return;
    } catch (e) {}
  }
})();
const slugId = s => String(s || '').toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40);
// arrivée demandée par le lien (#spawn=ID, à défaut « default » ; ou #pos=) ; null sans lien
function startPoint() {
  if (posArr) return { pos: posArr.slice(0, 3), yaw: posArr.length > 3 ? posArr[3] : 0, how: 'pos' };
  if (!arrival) return null;
  const zs = viewer.getZones(), id = slugId(H.get('spawn'));
  const s = zs.find(z => z.type === 'spawn' && z.id === id) || zs.find(z => z.type === 'spawn' && z.id === 'default');
  return s ? { pos: [s.x, s.y, s.z], yaw: s.yaw, how: 'spawn' } : null;
}
// arrivée « default » de la région : sans lien, la page s'ouvre cadrée dessus (sauf --target explicite) et F y démarre
function defaultArrival() {
  const s = viewer.getZones().find(z => z.type === 'spawn' && z.id === 'default');
  return s ? { pos: [s.x, s.y, s.z], yaw: s.yaw } : null;
}
// texte d'attente (jamais d'écran noir sans texte) : « Chargement du sol… » avec les tuiles prêtes sur les tuiles attendues et le temps écoulé
const gw = document.getElementById('groundWait');
const t0Boot = performance.now();
let bootOn = false, bootTimer = 0, lastWait = null;
const waitText = w => (C.tiles ? tr('page.ground.loading') : tr('page.wait.region')) + (w && w.total ? ' ' + trn('page.wait.tiles', w.total, w.ready) : '')
  + (w ? tr('page.wait.secs', w.secs) : '') + (w && w.secs >= 60 ? tr('page.wait.long') : '');
if (arrival) {
  fade.classList.add('on'); bootOn = true;
  const bootRender = () => { gw.textContent = waitText(lastWait || { secs: Math.floor((performance.now() - t0Boot) / 1000) }); gw.hidden = false; };
  bootRender(); bootTimer = setInterval(bootRender, 250);
}
const bootEnd = () => { bootOn = false; clearInterval(bootTimer); gw.hidden = !(viewer.tiled && viewer.tilesState().waiting); };
if (H.has('key')) {   // la clé (secret) ne reste jamais dans l'adresse visible ; une clé différente de celle du navigateur demande confirmation à l'écran
  try { const hp = hashParams(); hp.delete('key'); const hs = hp.toString(); history.replaceState(null, '', location.pathname + location.search + (hs ? '#' + hs : '')); } catch (e) {}
  if (KEYH && uidStored !== KEYH) {
    const m = document.getElementById('modal');
    document.getElementById('modalText').textContent = tr('page.key.modal');
    m.hidden = false;
    document.getElementById('modalYes').onclick = () => { m.hidden = true; if (viewer.setUid(KEYH)) toast(tr('page.key.done')); };
    document.getElementById('modalNo').onclick = () => { m.hidden = true; };
  }
}
if (H.get('name')) { try { localStorage.setItem('glb2html_name', H.get('name').slice(0, 24)); } catch (e) {} viewer.setName(H.get('name')); }
let liveReady = Promise.resolve();
let nearNow = null, refreshNear = () => {};
let refreshSpawns = () => {}, openView = null;   // v40 : liste des arrivées (fenêtre L, remplie à la fin du chargement) ; cadrage d'ouverture (bouton « Recentrer la vue »)
// v40 : bouton « Recentrer la vue » (caché en promenade) : revient au cadrage d'ouverture de la région, mémorisé à la fin du chargement (openView)
{
  const cb = document.getElementById('centerBtn'); cb.hidden = false;
  cb.onmousedown = e => e.preventDefault();
  cb.onclick = () => { if (openView) viewer.frame(openView.camDir, openView.target, openView.zoom); else viewer.frame(); };
}
// fin du chargement : cadrage sur l'arrivée « default », point de retour, promenade à l'arrivée demandée
let arrive = async () => {
  await Promise.race([liveReady, new Promise(r => setTimeout(r, 3000))]);
  const A = startPoint(), D = defaultArrival();
  if (!C.tiles && !A && D && !keepTarget) viewer.frame(viewer.cfg.camDir, D.pos, viewer.cfg.zoom);   // GLB unique : cadré sur l'arrivée par défaut
  viewer.setHome(D ? { pos: D.pos, yaw: D.yaw, forF: !keepTarget } : { pos: viewer.controls.target.toArray(), forF: false });
  openView = viewer.getCameraState(); refreshSpawns();
  if (arrival && C.walk) viewer.walkStart(A ? { pos: A.pos, yaw: A.yaw } : undefined);
  else viewer.releaseAnchor();
  setTimeout(() => fade.classList.remove('on'), 150);
};
const toastEl = document.getElementById('toast'); let toastT = 0;
const toast = t => { toastEl.textContent = t; toastEl.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => { toastEl.hidden = true; }, 4000); };
// v35 : copie dans le presse-papiers qui marche aussi en http (contexte non sécurisé : navigator.clipboard absent) ; rend true si la copie a réussi
async function copyText(text, field) {
  try { if (window.isSecureContext && navigator.clipboard && navigator.clipboard.writeText) { await navigator.clipboard.writeText(text); return true; } } catch (e) {}
  try {
    const ta = document.createElement('textarea'); ta.value = text; ta.setAttribute('readonly', ''); ta.setAttribute('aria-hidden', 'true');
    ta.style.cssText = 'position:fixed;left:-9999px;top:0;opacity:0'; document.body.appendChild(ta); ta.select(); ta.setSelectionRange(0, text.length);
    let ok = false; try { ok = !!document.execCommand('copy'); } catch (e) {} ta.remove();
    if (ok) return true;
  } catch (e) {}
  if (field) { field.hidden = false; field.select(); }
  return false;
}
window.__viewer = viewer;
if ((C.zones || []).length || C.zonesLive) {
  let ZS = viewer.setZones(C.zones || [], { editor: false });
  if (C.zonesLive && /^https?:$/.test(location.protocol)) {
    liveReady = fetch(new URL(C.zonesLive, location.href).href, { cache: 'no-store' })
      .then(r => r.ok ? r.json() : Promise.reject(new Error('http ' + r.status)))
      .then(list => { if (!Array.isArray(list)) throw new Error('format'); ZS = viewer.setZones(list.filter(z => z && (C.profile === 'private' || C.profile === 'perso' || !z.private)), { editor: false }); })
      .catch(() => {});
  }
  const okUrl = u => { try { const x = new URL(u, location.href); return (x.protocol === 'http:' || x.protocol === 'https:' || (location.protocol === 'file:' && x.protocol === 'file:')) ? x : null; } catch (e) { return null; } };
  const visitor = () => viewer.getName() || tr('page.visitor');
  const cool = {};
  const askConfirm = (text, yes) => {
    const m = document.getElementById('modal'); document.getElementById('modalText').textContent = text; m.hidden = false;
    const close = () => { m.hidden = true; };
    document.getElementById('modalYes').onclick = () => { close(); yes(); };
    document.getElementById('modalNo').onclick = close;
  };
  const haSend = z => {
    const now = Date.now(); if (cool[z.id] && now - cool[z.id] < 3000) return; cool[z.id] = now;
    fetch(z.target, { method: 'POST', mode: 'no-cors', body: new URLSearchParams({ zone: z.label || z.id, visitor: visitor() }) })
      .then(() => toast(tr('page.zone.cmdsent', z.label || z.id))).catch(() => toast(tr('page.zone.cmdfail', z.label || z.id)));
  };
  viewer.onZone = z => {
    const label = z.label || z.id;
    if (z.type === 'portal') {
      // destination vide ou égale à cette page : déplacement dans la même région, vers son point d'arrivée
      const same = !String(z.target || '').trim() || (() => { const x = okUrl(z.target); if (!x) return false; x.hash = ''; const h = new URL(location.href); h.hash = ''; return x.href === h.href; })();
      if (same) {
        const id = z.spawn || 'default', s = ZS.find(q => q.type === 'spawn' && q.id === id);
        if (!s) return toast(tr('page.zone.nospawn', id));
        fade.classList.add('on');
        setTimeout(() => { if (viewer.walking) viewer.teleportTo([s.x, s.y, s.z], s.yaw); setTimeout(() => fade.classList.remove('on'), 150); }, 480);
        return;
      }
      const u = okUrl(z.target); if (!u) return toast(tr('page.zone.noportal', label));
      u.hash = 'spawn=' + encodeURIComponent(z.spawn || '') + '&name=' + encodeURIComponent(visitor());
      fade.classList.add('on'); setTimeout(() => { location.href = u.href; }, 480);
    } else if (z.type === 'url' || z.type === 'image') {   // tableau avec lien (zone image) : comme une zone url
      const u = okUrl(z.type === 'image' ? z.link : z.target); if (!u) return toast(tr('page.zone.badlink', label));
      window.open(u.href, '_blank', 'noopener,noreferrer'); toast(tr('page.zone.opening', label));
    } else if (z.type === 'ha') {
      if (!okUrl(z.target)) return toast(tr('page.zone.badcmd', label));
      if (z.confirm) askConfirm(tr('page.zone.confirm', label), () => haSend(z)); else haSend(z);
    }
  };
  const pr = document.getElementById('zonePrompt');
  viewer.onNear = z => { nearNow = z; refreshNear(); };
  refreshNear = () => { pr.hidden = !nearNow; if (nearNow) pr.textContent = tr('page.zone.prompt', nearNow.label || nearNow.id); };   // v36 : E déclenche de nouveau la zone proche (comme avant la v35)
}
if ((C.map || []).length || C.mapUrl) {
  let MAP = (C.map || []).slice();
  const ov = document.getElementById('mapOverlay'), grid = document.getElementById('mapGrid'), mb = document.getElementById('mapBtn');
  const counts = {}, vis = {}, nms = {}, answered = {}, hasVis = {}, MAPKEY = hashParams().get('pseudos') || ''; let tm = 0;   // #pseudos=CLE : la cle du serveur (--map-names-key) pour voir les pseudos

  const srvOf = r => (r.presence || C.presenceUrl || '');
  const norm = u => { try { const x = new URL(u, location.href); x.hash = ''; return x.href; } catch (e) { return ''; } };
  const here = r => (r.room && r.room === C.room) || (r.url && norm(r.url) === norm(location.href));
  const okMapUrl = u => { try { const x = new URL(u, location.href); return (x.protocol === 'http:' || x.protocol === 'https:' || (location.protocol === 'file:' && x.protocol === 'file:')) ? x : null; } catch (e) { return null; } };
  const safeThumb = t => typeof t === 'string' && (/^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+\/=]+$/.test(t) || (!/^[a-z][a-z0-9+.-]*:/i.test(t) || /^https?:/i.test(t)));
  const go = r => {
    const u = okMapUrl(r.url); if (!u) return toast(tr('page.map.badurl', r.name));
    u.hash = 'spawn=' + encodeURIComponent(r.spawn || 'default') + '&name=' + encodeURIComponent(viewer.getName() || tr('page.visitor'));
    close(); fade.classList.add('on'); setTimeout(() => { location.href = u.href; }, 480);
  };
  // v52 : agrandissement de la vignette au survol (souris seulement ; une tuile sans vignette n'en a pas)
  const zoom = document.createElement('div'), zim = document.createElement('img'); let zpt = { x: 0, y: 0 };
  zoom.id = 'zoom'; zoom.hidden = true; zim.alt = ''; zoom.append(zim); document.body.append(zoom);
  const hideZoom = () => { zoom.hidden = true; };
  const placeZoom = () => { const w = zoom.offsetWidth, h = zoom.offsetHeight; let x = zpt.x + 16, y = zpt.y + 16; if (x + w > innerWidth - 4) x = zpt.x - w - 16; if (y + h > innerHeight - 4) y = innerHeight - h - 4; zoom.style.left = Math.max(4, x) + 'px'; zoom.style.top = Math.max(4, y) + 'px'; };
  const showZoom = src => { if (zim.getAttribute('src') !== src) zim.src = src; zoom.hidden = false; placeZoom(); };
  zim.onload = () => { if (!zoom.hidden) placeZoom(); };
  const zoomOn = (t, im) => {
    t.addEventListener('pointerenter', e => { if (e.pointerType !== 'mouse') return; zpt = { x: e.clientX, y: e.clientY }; showZoom(im.src); });
    t.addEventListener('pointermove', e => { if (e.pointerType !== 'mouse' || zoom.hidden) return; zpt = { x: e.clientX, y: e.clientY }; placeZoom(); });
    t.addEventListener('pointerleave', hideZoom);
  };
  const reZoom = () => { const el = document.elementFromPoint(zpt.x, zpt.y), t = el && el.closest ? el.closest('.mapTile') : null, im = t && t.querySelector('img'); if (im) showZoom(im.src); };
  const draw = () => {
    const zoomWas = !zoom.hidden; hideZoom();
    grid.textContent = '';
    const list = MAP.filter(r => r && r.name);
    const remap = vals => { const u = [...new Set(vals)].sort((a, b) => a - b), m = new Map(); let pos = 0; u.forEach((v, i) => { if (i) pos += Math.min(v - u[i - 1], 2); m.set(v, pos); }); return m; };
    const mx = remap(list.map(r => r.x | 0)), my = remap(list.map(r => r.y | 0));
    const cols = list.length ? Math.max(...mx.values()) + 1 : 0, rows = list.length ? Math.max(...my.values()) + 1 : 0;
    const placed = list.length > 0 && new Set(list.map(r => (r.x | 0) + ',' + (r.y | 0))).size === list.length && cols <= 14 && rows <= 14;
    grid.style.gridTemplateColumns = placed ? 'repeat(' + cols + ', 160px)' : 'repeat(auto-fill, 160px)';
    for (const r of list) {
      const t = document.createElement('button'); t.className = 'mapTile' + (here(r) ? ' here' : '');
      if (placed) { t.style.gridColumn = String(mx.get(r.x | 0) + 1); t.style.gridRow = String(rows - my.get(r.y | 0)); }
      if (r.thumb && safeThumb(r.thumb)) { const im = document.createElement('img'); im.src = r.thumb; im.alt = ''; im.referrerPolicy = 'no-referrer'; t.append(im); zoomOn(t, im); } else { const ph = document.createElement('div'); ph.className = 'ph'; t.append(ph); }
      const b = document.createElement('b'); b.textContent = r.name; t.append(b);
      t.title = here(r) ? tr('page.map.tiphere') : tr('page.map.tip', r.spawn || 'default');   // v47 : bulle au survol
      const parts = [], srv = srvOf(r), k = srv + '|' + (r.room || '');
      if (here(r)) parts.push(tr('page.map.here'));
      if (answered[srv] && r.room) {   // v47 : visiteurs (promeneurs et spectateurs) et promeneurs, en texte ; un ancien serveur ne donne que les promeneurs
        const w = counts[k] || 0, v = hasVis[srv] ? Math.max(vis[k] || 0, w) : -1;
        parts.push(v < 0 ? trn('page.map.count', w) : !v ? tr('page.map.novisitor') : !w ? trn('page.map.visitors', v) : v === w ? trn('page.map.count', w) : trn('page.map.mixed', v, w));   // un seul nombre : celui qui marche n'est pas compté deux fois
        const nm = nms[k];   // pseudos (serveur lancé avec --map-names-key, carte ouverte avec #pseudos=CLE) : les promeneurs, le plus récent d'abord, puis les visiteurs en vue globale
        if (nm) {
          if (nm.w.length) { const shown = nm.w.slice(0, 5), extra = Math.max(w - shown.length, 0); parts.push(shown.join(', ') + (extra ? tr('page.map.and') + trn('page.map.other', extra) : '')); }
          if (nm.v.length) { const shown = nm.v.slice(0, 5), extra = Math.max(Math.max(v - w, 0) - shown.length, 0); parts.push(tr('page.map.viewers', shown.join(', ') + (extra ? tr('page.map.and') + trn('page.map.other', extra) : ''))); }
        }
      }
      if (parts.length) { const s = document.createElement('span'); s.textContent = parts.join(tr('page.map.sep')); t.append(s); }
      t.onclick = () => { if (here(r)) close(); else go(r); };
      grid.append(t);
    }
    if (!list.length) grid.textContent = tr('page.map.empty');
    if (zoomWas) reZoom();
  };
  const queryServer = srv => {
    try {
      const ws = new WebSocket(presUrl(srv)); const to = setTimeout(() => { try { ws.close(); } catch (e) {} }, 4000);
      ws.onopen = () => ws.send(JSON.stringify(MAPKEY ? { t: 'rooms', key: MAPKEY } : { t: 'rooms' }));
      ws.onmessage = ev => {
        try { const m = JSON.parse(ev.data); if (m.t === 'rooms') { for (const o of [counts, vis, nms]) for (const k of Object.keys(o)) if (k.startsWith(srv + '|')) delete o[k]; for (const [room, n] of Object.entries(m.rooms || {})) counts[srv + '|' + room] = n; hasVis[srv] = !!(m.visitors && typeof m.visitors === 'object'); if (hasVis[srv]) for (const [room, n] of Object.entries(m.visitors)) vis[srv + '|' + room] = n; const ob = x => (x && typeof x === 'object' ? x : {}), cl = a => (Array.isArray(a) ? a.filter(x => typeof x === 'string' && x).slice(0, 20) : []); for (const room of new Set([...Object.keys(ob(m.names)), ...Object.keys(ob(m.viewers))])) nms[srv + '|' + room] = { w: cl(ob(m.names)[room]), v: cl(ob(m.viewers)[room]) }; answered[srv] = true; draw(); } } catch (e) {}
        try { ws.close(); } catch (e) {}
      };
      ws.onclose = () => clearTimeout(to); ws.onerror = () => {};
    } catch (e) {}
  };
  const fetchCounts = () => { for (const srv of new Set(MAP.map(srvOf).filter(Boolean))) queryServer(srv); };
  function close() { ov.hidden = true; clearInterval(tm); }
  const open = () => { if (document.pointerLockElement && document.exitPointerLock) document.exitPointerLock(); ov.hidden = false; draw(); fetchCounts(); clearInterval(tm); tm = setInterval(fetchCounts, 8000); };
  mb.hidden = false; mb.onclick = () => (ov.hidden ? open() : close());
  document.getElementById('mapClose').onclick = close;
  ov.addEventListener('click', e => { if (e.target === ov) close(); });
  addEventListener('keydown', e => {
    const n = e.target && e.target.tagName;
    if (keyChar(e) === 'm' && !e.repeat && n !== 'INPUT' && n !== 'TEXTAREA' && (!viewer.walking || e.ctrlKey || e.metaKey) && !e.altKey) {   // v36 : reconnue par la lettre imprimée
      e.preventDefault(); (ov.hidden ? open() : close()); }   // v35 : en promenade M bascule la vue ; Ctrl+M ouvre la carte partout
    else if (e.code === 'Escape' && !ov.hidden) close();
  });
  if (C.mapUrl && /^https?:$/.test(location.protocol)) {
    const urls = String(C.mapUrl).split(',').map(s => s.trim()).filter(Boolean);
    Promise.allSettled(urls.map(u => fetch(new URL(u, location.href).href, { cache: 'no-store' }).then(r => r.ok ? r.json() : Promise.reject(new Error('http ' + r.status))))).then(res => {
      const merged = [], seen = new Set(), embedded = (C.map || []).slice();
      for (const x of res) for (const r of (x.status === 'fulfilled' ? (Array.isArray(x.value) ? x.value : (x.value && Array.isArray(x.value.regions) ? x.value.regions : [])) : [])) {   // v47 : liste simple ou {"showUrl": ..., "regions": [...]}
        if (!r || typeof r.name !== 'string' || typeof r.url !== 'string') continue;
        const e = { id: String(r.id || '').slice(0, 40), name: r.name.slice(0, 60), url: r.url.slice(0, 600), x: Number(r.x) | 0, y: Number(r.y) | 0, spawn: String(r.spawn || '').slice(0, 40), room: String(r.room || '').slice(0, 64), presence: /^wss?:\/\//i.test(String(r.presence || '')) ? String(r.presence).slice(0, 300) : '', thumb: safeThumb(r.thumb) ? String(r.thumb).slice(0, 200000) : '' };
        const k = e.url + '|' + e.room; if (!seen.has(k)) { seen.add(k); merged.push(e); }
      }
      if (!merged.length) return;
      for (const r of embedded) if (here(r) && !merged.some(m => here(m))) merged.push(r);
      MAP = merged; if (!ov.hidden) { draw(); fetchCounts(); }
    });
  }
}
// v48 : journal des visites. L'adresse de la page suivie de #visits ouvre cette fenêtre ; la clé (commande « visits-key SALON » du serveur
// de présence) est envoyée au serveur de la page par une connexion brève, qui renvoie le résumé du salon. La clé acceptée est retenue par ce navigateur.
const VISITS = (() => {   // v48 : aussi ouvert par le bouton « Journal des visites… » de la fenêtre Informations (VISITS.open)
  const $v = id => document.getElementById(id);
  const ov = $v('visitsOverlay'), inp = $v('visitsKey'), st = $v('visitsStatus'), out = $v('visitsOut'), csvB = $v('visitsCsv'), fgB = $v('visitsForget');
  const room = String(C.room || ''), SK = 'glb2html_visits_' + room;
  let last = null;
  const esc = x => String(x).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const dur = n => { n = Math.max(0, n | 0); const h = Math.floor(n / 3600), m = Math.floor(n / 60) % 60, s = n % 60; return h ? tr('page.visits.d.h', h, String(m).padStart(2, '0')) : tr('page.visits.d.m', m, String(s).padStart(2, '0')); };
  const stored = () => { try { return localStorage.getItem(SK) || ''; } catch (e) { return ''; } };
  const store = k => { try { if (k) localStorage.setItem(SK, k); else localStorage.removeItem(SK); } catch (e) {} fgB.hidden = !k; };
  const close = () => { ov.hidden = true; };
  const ask = key => new Promise(res => {
    let ws, opened = false, done = false, to = 0;
    const end = r => { if (done) return; done = true; clearTimeout(to); try { ws.close(); } catch (e) {} res(r); };
    try { ws = new WebSocket(presUrl(C.presenceUrl)); } catch (e) { return res({ why: 'net' }); }
    to = setTimeout(() => end({ why: opened ? 'old' : 'net' }), 10000);
    ws.onopen = () => { opened = true; ws.send(JSON.stringify({ t: 'visits', room, key })); };
    ws.onmessage = ev => { let m = null; try { m = JSON.parse(ev.data); } catch (e) {} if (m && m.t === 'visits') end(m); else if (m && (m.t === 'full' || m.t === 'banned')) end({ why: 'net' }); };
    ws.onclose = () => end({ why: opened ? 'old' : 'net' });
    ws.onerror = () => {};
  });
  const table = (head, rows) => '<div class="visitsScroll"><table><tr>' + head.map(h => '<th scope="col">' + esc(h) + '</th>').join('') + '</tr>'
    + rows.map(r => '<tr>' + r.map(c => '<td>' + esc(c) + '</td>').join('') + '</tr>').join('') + '</table></div>';
  const yn = b => tr(b ? 'page.visits.yes' : 'page.visits.no');
  const show = m => {
    last = m;
    st.textContent = (m.keep > 0 ? tr('page.visits.summary', room, m.visits, m.visitors, m.keep) : tr('page.visits.summary.all', room, m.visits, m.visitors));
    if (!m.visits) { out.innerHTML = '<p>' + esc(tr('page.visits.none')) + '</p>'; csvB.hidden = true; return; }
    const dh = ['page.visits.c.date', 'page.visits.c.visits', 'page.visits.c.visitors', 'page.visits.c.total', 'page.visits.c.median', 'page.visits.c.walked'].map(k => tr(k));
    const rh = ['page.visits.c.start', 'page.visits.c.dur', 'page.visits.c.walk'].map(k => tr(k)).concat(m.names ? [tr('page.visits.c.name')] : []);
    out.innerHTML = '<h3>' + esc(tr('page.visits.days')) + '</h3>' + table(dh, (m.days || []).map(d => [d.date, d.visits, d.visitors, dur(d.total), dur(d.median), d.walked]))
      + '<h3>' + esc(tr('page.visits.recent')) + (m.recentAll > (m.recent || []).length ? ' ' + esc(tr('page.visits.recent.cut', (m.recent || []).length)) : '') + '</h3>'
      + ((m.recent || []).length ? table(rh, m.recent.map(r => [r.start, dur(r.dur), yn(r.walk)].concat(m.names ? [r.name || ''] : []))) : '<p>' + esc(tr('page.visits.recent.none')) + '</p>');
    csvB.hidden = false;
  };
  const run = async key => {
    key = String(key || '').trim();
    if (!key) { st.textContent = tr('page.visits.err.empty'); inp.focus(); return; }
    st.textContent = tr('page.visits.wait'); out.innerHTML = ''; csvB.hidden = true;
    const m = await ask(key);
    if (m.ok) { store(key); show(m); return; }
    if (m.why === 'key' && stored() === key) store('');
    st.textContent = tr('page.visits.err.' + (['key', 'rate', 'off', 'old'].includes(m.why) ? m.why : 'net'));
  };
  const csv = () => {
    if (!last) return;
    const sep = (document.documentElement.lang || '').startsWith('fr') ? ';' : ',', q = v => '"' + String(v).replace(/"/g, '""') + '"', sec = k => tr(k) + ' (s)';
    const lines = [[tr('page.visits.days')], ['page.visits.c.date', 'page.visits.c.visits', 'page.visits.c.visitors'].map(k => tr(k)).concat([sec('page.visits.c.total'), sec('page.visits.c.median'), tr('page.visits.c.walked')])];
    for (const d of last.days || []) lines.push([d.date, d.visits, d.visitors, d.total, d.median, d.walked]);
    lines.push([], [tr('page.visits.recent')], [tr('page.visits.c.start'), sec('page.visits.c.dur'), tr('page.visits.c.walk')].concat(last.names ? [tr('page.visits.c.name')] : []));
    for (const r of last.recent || []) lines.push([r.start, r.dur, yn(r.walk)].concat(last.names ? [r.name || ''] : []));
    const blob = new Blob(['\ufeff' + lines.map(l => l.map(q).join(sep)).join('\r\n') + '\r\n'], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a'), d = new Date(), p2 = n => String(n).padStart(2, '0');
    a.href = URL.createObjectURL(blob); a.download = tr('page.visits.file') + '_' + (room || 'room') + '_' + d.getFullYear() + p2(d.getMonth() + 1) + p2(d.getDate()) + '.csv';
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  };
  $v('visitsGo').onclick = () => run(inp.value);
  inp.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); run(inp.value); } });
  fgB.onclick = () => { store(''); inp.value = ''; last = null; out.innerHTML = ''; csvB.hidden = true; st.textContent = tr('page.visits.forgotten'); inp.focus(); };
  csvB.onclick = csv;
  $v('visitsClose').onclick = close;
  addEventListener('keydown', e => { if (e.key === 'Escape' && !ov.hidden) { e.preventDefault(); close(); } });
  const open = () => {
    if (document.pointerLockElement && document.exitPointerLock) document.exitPointerLock();
    ov.hidden = false;
    if (!C.presenceUrl) { $v('visitsForm').hidden = true; st.textContent = tr('page.visits.nopres'); return; }
    if (last) return;
    const k = stored(); fgB.hidden = !k; if (k) { inp.value = k; run(k); } else inp.focus();
  };
  if (H.has('visits')) open();
  return { open };
})();
// réglages visiteur mémorisés dans ce navigateur : couleur de l'avatar (null = tirée au hasard par le serveur), pseudo cité (gras, clignotement),
// sons (général, volume, citation, arrivée, départ), disposition du clavier. v36 : les anciens réglages du bip (clé « sound ») sont ignorés.
const VIS = (() => {
  const d = { color: null, compass: true, histMax: 200, bold: true, blink: true, sounds: true, volume: 50, soundCite: true, soundMsg: true, soundJoin: true, soundLeave: true, layout: 'auto', pad: true, touch: 'auto' };
  try {
    const s = JSON.parse(localStorage.getItem('glb2html_visitor') || '{}');
    if (Number.isInteger(s.color) && s.color >= 0 && s.color <= 0xFFFFFF) d.color = s.color;
    for (const k of ['compass', 'bold', 'blink', 'sounds', 'soundCite', 'soundMsg', 'soundJoin', 'soundLeave', 'pad']) if (typeof s[k] === 'boolean') d[k] = s[k];
    if (['auto', 'on', 'off'].includes(s.touch)) d.touch = s.touch;   // v46 : commandes tactiles (auto = écran tactile détecté)
    if (Number.isFinite(s.histMax)) d.histMax = Math.max(20, Math.min(2000, Math.round(s.histMax)));
    if (Number.isFinite(s.volume)) d.volume = Math.max(0, Math.min(100, Math.round(s.volume)));
    if (['auto', 'azerty', 'qwerty'].includes(s.layout)) d.layout = s.layout;
  } catch (e) {}
  return d;
})();
let chatTrim = () => {};   // v37 : rempli par le chat (réduit la liste quand le réglage « Messages d'historique affichés » baisse)
const visSave = () => { try { localStorage.setItem('glb2html_visitor', JSON.stringify(VIS)); } catch (e) {} };
// v46 : commandes à l'écran (remplies par le bloc promenade) ; Réglages et chat les appellent
const CTL = { apply() {}, tick() {}, sync() {}, chat: null, touch: false };
KB.setPref(VIS.layout);
// sons (Web Audio, sans fichier externe) : le contexte audio démarre à la première action de l'utilisateur sur la page ; au plus un son d'arrivée et un de départ toutes les 2 s
const SND = (() => {
  const AC = window.AudioContext || window.webkitAudioContext;
  let ctx = null, acted = false; const last = { join: -1e9, leave: -1e9, msg: -1e9 };
  const ensure = () => {
    if (!acted || !AC) return null;
    try { if (!ctx) ctx = new AC(); if (ctx.state === 'suspended' && ctx.resume) ctx.resume(); } catch (e) { return null; }
    return ctx;
  };
  for (const ev of ['pointerdown', 'keydown', 'touchstart']) addEventListener(ev, () => { acted = true; if (VIS.sounds) ensure(); }, true);
  const play = notes => {
    if (!VIS.sounds || VIS.volume <= 0) return false;
    const c = ensure(); if (!c) return false;
    try {
      const peak = Math.max(0.0002, VIS.volume / 100 * 0.25);
      let t = c.currentTime;
      for (const [f, dur] of notes) {
        const o = c.createOscillator(), g = c.createGain();
        o.type = 'sine'; o.frequency.value = f;
        g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(peak, t + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
        o.connect(g); g.connect(c.destination); o.start(t); o.stop(t + dur + 0.02);
        t += dur;
      }
      return true;
    } catch (e) { return false; }
  };
  const limited = k => { const now = performance.now(); if (now - last[k] < 2000) return false; if (play(k === 'join' ? [[660, 0.08], [880, 0.08]] : k === 'msg' ? [[988, 0.12]] : [[880, 0.08], [660, 0.08]])) { last[k] = now; return true; } return false; };
  return { cite: () => play([[880, 0.16]]), msg: () => limited('msg'), join: () => limited('join'), leave: () => limited('leave'), sample: () => play([[880, 0.16]]) };
})();
viewer.setMyColor(VIS.color);
if (C.presenceUrl && C.walk) viewer.onPeer = kind => { if (kind === 'join' && VIS.soundJoin) SND.join(); else if (kind === 'leave' && VIS.soundLeave) SND.leave(); };
// v37 : boussole en haut au centre : point cardinal et degrés (« NE 45° »), sans dépendre de la couleur ; masquée par la case des réglages visiteur ou --no-compass
const compassEl = document.getElementById('compass'), CARD = tr('page.compass.dirs').split(' ');
function compassTick() {
  const h = C.compass !== false && VIS.compass ? viewer.getHeading() : null;
  if (h === null) { compassEl.hidden = true; return; }
  const d = Math.round(h) % 360, t = CARD[Math.round(h / 45) % 8] + ' ' + d + '°';
  if (compassEl.textContent !== t) { compassEl.textContent = t; compassEl.setAttribute('aria-label', tr('page.compass.label', t)); }
  compassEl.hidden = false;
}
if (C.compass !== false) setInterval(compassTick, 100);
if (C.panel !== false) {
  const ob = document.getElementById('optsBtn'), op = document.getElementById('optsPanel');
  ob.title = tr('page.win.o.tip');   // v41 : bulle (rôle et touche)
  const key = 'glb2html_opts_' + (C.room || 'x');
  const base = { retina: !!C.retina, sea: !!C.sea, anim: !!C.anim, wave: Number(C.wave) };
  const st = Object.assign({}, base);
  try { const s = JSON.parse(localStorage.getItem(key) || '{}'); if (typeof s.retina === 'boolean') st.retina = s.retina; if (C.sea && typeof s.sea === 'boolean') st.sea = s.sea; if (typeof s.anim === 'boolean') st.anim = s.anim; if (Number.isFinite(s.wave)) st.wave = Math.min(10, Math.max(0, s.wave)); } catch (e) {}
  const mk = (tag, props) => Object.assign(document.createElement(tag), props || {});
  const lab = (text, input) => { const l = mk('label'); l.append(input, mk('span', { textContent: text })); return l; };
  const cbRetina = mk('input', { type: 'checkbox' }), cbAnim = mk('input', { type: 'checkbox' }), cbSea = mk('input', { type: 'checkbox' });
  const rgWave = mk('input', { type: 'range', min: 0, max: 10, step: 0.1 }), vWave = mk('span');
  const save = () => { try { localStorage.setItem(key, JSON.stringify(st)); } catch (e) {} };
  const sync = () => { cbRetina.checked = st.retina; cbSea.checked = st.sea; cbAnim.checked = st.anim; cbAnim.disabled = !st.sea; rgWave.value = st.wave; vWave.textContent = Number(st.wave).toFixed(1); rgWave.disabled = !st.anim || !st.sea; };
  const apply = () => { viewer.setCfg({ retina: st.retina, sea: st.sea, anim: st.anim, wave: st.wave }); sync(); save(); };
  cbRetina.onchange = () => { st.retina = cbRetina.checked; apply(); };
  cbSea.onchange = () => { st.sea = cbSea.checked; apply(); };   // v52 : afficher / masquer la mer
  cbAnim.onchange = () => { st.anim = cbAnim.checked; apply(); };
  rgWave.oninput = () => { st.wave = parseFloat(rgWave.value); apply(); };
  op.append(lab(tr('page.opt.retina'), cbRetina));
  {
    // v42 : case « Rendu léger » (préréglage) et ses réglages fins, dans une sous-fenêtre à gauche de Réglages, modifiables en direct
    const cbL = mk('input', { type: 'checkbox', id: 'lightOn' }), bFine = mk('button', { type: 'button', id: 'lightFineBtn', textContent: tr('page.opt.light.fine') });
    const row = mk('div', { className: 'lrow' }); row.append(lab(tr('page.opt.light'), cbL), bFine); op.append(row);
    cbL.onchange = () => lightApply(cbL.checked ? LIGHT.preset : LIGHT.normal);
    const lp = document.getElementById('lightPanel'), head = mk('div', { id: 'lightHead' });
    const bX = mk('button', { type: 'button', id: 'lightClose', textContent: '\u00d7', title: tr('page.light.close') });
    bX.setAttribute('aria-label', tr('page.light.close'));
    head.append(mk('span', { textContent: tr('page.light.title') }), bX); lp.append(head);
    bFine.onclick = () => { lp.hidden = !lp.hidden; };
    bX.onclick = () => { lp.hidden = true; };
    const rng = (id, min, max, step) => mk('input', { type: 'range', id, min, max, step });
    const line = (input, text, out) => { const l = mk('label'); l.append(input, mk('span', { textContent: text })); if (out) l.append(out); lp.append(l); };
    const rgS = rng('lightScale', 25, 100, 5), vS = mk('span', { id: 'lightScaleV' });
    const rgF = rng('lightFps', 5, 65, 5), vF = mk('span', { id: 'lightFpsV' });   // 65 = sans limite
    const cbO = mk('input', { type: 'checkbox', id: 'lightOv' }), rgR = rng('lightRadius', 20, Math.max(500, LIGHT.normal.radius), 10), vR = mk('span', { id: 'lightRadiusV' });
    const cbA = mk('input', { type: 'checkbox', id: 'lightAa' });
    line(rgS, tr('page.light.scale'), vS);
    line(rgF, tr('page.light.fps'), vF);
    if (C.tiles) { line(cbO, tr('page.light.ovonly')); line(rgR, tr('page.light.radius'), vR); }
    line(cbA, tr('page.light.aa'));
    const bP = mk('button', { type: 'button', id: 'lightPreset', textContent: tr('page.light.preset') });
    lp.append(bP, mk('small', { textContent: tr('page.light.note') }));
    bP.onclick = () => lightApply(LIGHT.preset);
    rgS.oninput = () => lightApply({ scale: Number(rgS.value) / 100 });
    rgF.oninput = () => lightApply({ fps: Number(rgF.value) > 60 ? 0 : Number(rgF.value) });
    cbO.onchange = () => lightApply({ ovOnly: cbO.checked });
    rgR.oninput = () => lightApply({ radius: Number(rgR.value) });
    cbA.onchange = () => lightApply({ aa: cbA.checked });
    lightSync = () => {
      const s = LIGHT.st; cbL.checked = s.on;
      rgS.value = Math.round(s.scale * 100); vS.textContent = tr('page.light.pct', Math.round(s.scale * 100));
      rgF.value = s.fps > 0 ? s.fps : 65; vF.textContent = s.fps > 0 ? String(s.fps) : tr('page.light.nolimit');
      cbO.checked = s.ovOnly; rgR.value = s.radius; vR.textContent = tr('page.light.m', Math.round(s.radius)); cbA.checked = s.aa;
    };
    lightSync();
  }
  if (C.sea) {
    op.append(lab(tr('page.opt.sea'), cbSea));
    op.append(lab(tr('page.opt.anim'), cbAnim));
    const w = mk('label'); w.append(rgWave, mk('span', { textContent: tr('page.opt.wave') }), vWave); op.append(w);
  }
  if (C.presenceUrl && C.walk) {
    // couleur de l'avatar : annoncée au serveur de présence à la connexion (le nom reste le repère principal)
    const cbCol = mk('input', { type: 'checkbox', id: 'visColorOn' }), inCol = mk('input', { type: 'color', id: 'visColor' });
    const showCol = () => { cbCol.checked = VIS.color !== null; inCol.disabled = VIS.color === null; inCol.value = '#' + (VIS.color === null ? 0x3366cc : VIS.color).toString(16).padStart(6, '0'); };
    const setCol = () => { VIS.color = cbCol.checked ? parseInt(inCol.value.slice(1), 16) : null; viewer.setMyColor(VIS.color); visSave(); showCol(); };
    cbCol.onchange = setCol; inCol.oninput = () => { if (cbCol.checked) setCol(); };
    const lc = mk('label'); lc.append(cbCol, mk('span', { textContent: tr('page.opt.color') }), inCol); op.append(lc);
    op.append(mk('small', { className: 'two', textContent: tr('page.opt.color.note') }));   // v42 : deux lignes courtes
    // lien personnel : #name=PSEUDO&key=CLE ; la clé est l'identité de ce navigateur (nom réservé)
    const bl = mk('button', { id: 'visLinkBtn', type: 'button', textContent: tr('page.opt.link') }), lo = mk('input', { id: 'visLinkOut', readOnly: true, size: 24 });
    lo.setAttribute('aria-label', tr('page.opt.link.aria')); lo.hidden = true;
    bl.onclick = async () => {
      const u = new URL(location.href); u.hash = 'name=' + encodeURIComponent(viewer.getName() || (() => { try { return localStorage.getItem('glb2html_name') || ''; } catch (e) { return ''; } })() || tr('page.visitor')) + '&key=' + viewer.getUid();
      lo.value = u.href; lo.hidden = false;
      toast((await copyText(u.href, lo)) ? tr('page.toast.copied') : tr('page.toast.copyfail'));
    };
    op.append(bl, lo, mk('small', { textContent: tr('page.opt.link.note') }));
    showCol();
  }
  if (C.compass !== false) {   // v37 : boussole (cap de l'avatar, de la caméra en vue globale)
    const cb = mk('input', { type: 'checkbox', id: 'visCompass' }); cb.checked = VIS.compass; cb.onchange = () => { VIS.compass = cb.checked; visSave(); compassTick(); }; op.append(lab(tr('page.opt.compass'), cb));
  }
  if ((C.zones || []).some(z => z && z.type === 'image') || C.zonesLive) {   // reperage des zones image : numeros, jamais memorises (decoche a chaque ouverture)
    const cb = mk('input', { type: 'checkbox', id: 'visZoneNums' }); cb.onchange = () => viewer.setZoneNumbers(cb.checked); op.append(lab(tr('page.opt.zonenums'), cb));
  }
  if (C.presenceUrl && C.walk && C.chat) {
    const nh = mk('input', { type: 'number', id: 'visHist', min: 20, max: 2000, step: 10, value: VIS.histMax });
    nh.onchange = () => { const v = Math.max(20, Math.min(2000, Math.round(Number(nh.value) || 200))); nh.value = v; VIS.histMax = v; visSave(); chatTrim(); };
    op.append(lab(tr('page.opt.histmax'), nh));
    for (const [k, t, id] of [['bold', tr('page.opt.bold'), 'visBold'], ['blink', tr('page.opt.blink'), 'visBlink']]) {
      const cb = mk('input', { type: 'checkbox', id }); cb.checked = VIS[k]; cb.onchange = () => { VIS[k] = cb.checked; visSave(); }; op.append(lab(t, cb));
    }
  }
  if (C.presenceUrl && C.walk) {
    // v36 : sons. Case générale + volume, puis une case par événement
    const cbS = mk('input', { type: 'checkbox', id: 'visSounds' }), rgV = mk('input', { type: 'range', min: 0, max: 100, step: 1, id: 'visVolume' }), vV = mk('span');
    const subs = [];
    const syncS = () => { cbS.checked = VIS.sounds; rgV.value = VIS.volume; vV.textContent = String(VIS.volume); rgV.disabled = !VIS.sounds; for (const c of subs) c.disabled = !VIS.sounds; };
    cbS.onchange = () => { VIS.sounds = cbS.checked; visSave(); syncS(); };
    rgV.oninput = () => { VIS.volume = parseInt(rgV.value, 10); vV.textContent = String(VIS.volume); visSave(); };
    rgV.onchange = () => { SND.sample(); };
    op.append(lab(tr('page.opt.sounds'), cbS));
    const wv = mk('label'); wv.append(rgV, mk('span', { textContent: tr('page.opt.volume') }), vV); op.append(wv);
    for (const [k, t, id, need] of [['soundCite', tr('page.opt.sound.cite'), 'visSoundCite', C.chat], ['soundMsg', tr('page.opt.sound.msg'), 'visSoundMsg', C.chat], ['soundJoin', tr('page.opt.sound.join'), 'visSoundJoin', true], ['soundLeave', tr('page.opt.sound.leave'), 'visSoundLeave', true]]) {
      if (!need) continue;
      const cb = mk('input', { type: 'checkbox', id }); cb.checked = VIS[k]; cb.onchange = () => { VIS[k] = cb.checked; visSave(); }; subs.push(cb); op.append(lab(t, cb));
    }
    syncS();
  }
  if (C.walk) {
    // v36 : disposition du clavier (les lettres de l'aide ; la marche reste sur les touches physiques)
    const sel = mk('select', { id: 'visLayout' });
    for (const [v, t] of [['auto', tr('common.auto')], ['azerty', 'AZERTY'], ['qwerty', 'QWERTY']]) sel.append(mk('option', { value: v, textContent: t }));
    sel.value = VIS.layout; sel.onchange = () => { VIS.layout = sel.value; visSave(); KB.setPref(VIS.layout); };
    const l = mk('label'); l.append(mk('span', { textContent: tr('page.opt.layout') }), sel); op.append(l);
    // v46 : flèches à l'écran (aussi : touche K, bouton « Flèches (K) ») et commandes tactiles (Auto : écran tactile détecté)
    const cbPad = mk('input', { type: 'checkbox', id: 'visPad' }); cbPad.checked = VIS.pad;
    cbPad.onchange = () => { VIS.pad = cbPad.checked; visSave(); CTL.apply(); };
    op.append(lab(tr('page.opt.pad'), cbPad));
    const selT = mk('select', { id: 'visTouch' });
    for (const [v, t] of [['auto', tr('common.auto')], ['on', tr('page.opt.touch.on')], ['off', tr('page.opt.touch.off')]]) selT.append(mk('option', { value: v, textContent: t }));
    selT.value = VIS.touch; selT.onchange = () => { VIS.touch = selT.value; visSave(); CTL.apply(); };
    const lt = mk('label'); lt.append(mk('span', { textContent: tr('page.opt.touch') }), selT); op.append(lt);
    CTL.sync = () => { cbPad.checked = VIS.pad; selT.value = VIS.touch; };
  }
  {
    // v36 : langue de la page (Auto = première langue du navigateur disponible, sinon l'anglais) ; changer recharge la page
    const selL = mk('select', { id: 'visLang' });
    for (const [v, tt] of i18nChoices()) selL.append(mk('option', { value: v, textContent: tt }));
    selL.value = LANG_PREF; selL.onchange = () => setLangPref(selL.value);
    const ll = mk('label'); ll.append(mk('span', { textContent: tr('page.opt.lang') }), selL); op.append(ll);
  }
  const rst = mk('button', { textContent: tr('page.opt.reset') });
  rst.onclick = () => { Object.assign(st, base); apply(); lightReset(); };   // v42 : le rendu léger revient aussi aux valeurs de la page
  op.append(rst, mk('small', { id: 'optsNote', textContent: tr('page.opt.note') }));   // v42 : la note reste tout en bas (la section Disposition s'insère avant)
  sync(); ob.hidden = false;
  ob.onclick = () => { op.hidden = !op.hidden; };
  // v37 : O ouvre / ferme la fenêtre Réglages (bascule, comme H et I) ; R est déjà pris (retour à l'arrivée)
  addEventListener('keydown', e => { const n = e.target && e.target.tagName; if (e.code === 'KeyO' && !e.repeat && !e.ctrlKey && !e.metaKey && !e.altKey && n !== 'INPUT' && n !== 'TEXTAREA' && n !== 'SELECT') op.hidden = !op.hidden; });
  if (st.retina !== base.retina || st.sea !== base.sea || st.anim !== base.anim || st.wave !== base.wave) viewer.setCfg({ retina: st.retina, sea: st.sea, anim: st.anim, wave: st.wave });
}
// v42 : rendu sans carte graphique : proposer le rendu léger, une seule fois (la réponse est retenue ; Réglages permet de changer d'avis)
if (!LIGHT.asked && !LIGHT.st.on && softGpu(viewer.renderer)) {
  const box = document.createElement('div'); box.id = 'lightAsk';
  const yes = Object.assign(document.createElement('button'), { type: 'button', id: 'lightAskYes', textContent: tr('page.modal.yes') });
  const no = Object.assign(document.createElement('button'), { type: 'button', id: 'lightAskNo', textContent: tr('page.light.no') });
  box.append(Object.assign(document.createElement('span'), { textContent: tr('page.light.ask') }), yes, no);
  yes.onclick = () => { box.remove(); lightApply(LIGHT.preset); toast(tr('page.light.done')); };
  no.onclick = () => { box.remove(); LIGHT.save(); };
  document.body.append(box);
}
if (C.walk) {
  const wb = document.getElementById('walkBtn'), wh = document.getElementById('walkHint');
  wb.hidden = false; wb.textContent = tr('page.btn.walk');
  const on = !!C.presenceUrl;
  const fly = C.fly !== false;
  // v35 : aide en groupes courts (une ligne par groupe, touches sans phrases)
  const hasZones = !!((C.zones && C.zones.length) || C.zonesLive), hasMap = !!((C.map || []).length || C.mapUrl);
  const grp = (t, items) => ({ t, items: items.filter(Boolean) });
  const lsGet = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };
  const lsSet = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
  const keyLabels = () => KB.keys();
  // v40 : arrivées de la région (« default » d'abord, puis par nom)
  const spawnList = () => viewer.getZones().filter(z => z.type === 'spawn').sort((a, b) => (b.id === 'default') - (a.id === 'default') || String(a.label || a.id).localeCompare(String(b.label || b.id), LANG));
  const walkGroups = () => { const K = keyLabels(); return [
    grp(tr('page.help.g.move'), [tr('page.help.move', K.fwd + K.left + K.back + K.right), tr('page.help.run', K.fwd, K.back), tr('page.help.jump'), tr('page.help.tp'), tr('page.help.home')]),
    fly ? grp(tr('page.help.g.fly'), [tr('page.help.fly'), tr('page.help.up'), tr('page.help.takeoff'), tr('page.help.down')]) : null,
    grp(tr('page.help.g.view'), [tr('page.help.view'), tr('page.help.m'), tr('page.help.wheel'), tr('page.help.end'), tr('page.help.alt')]),
    grp(tr('page.help.g.mouse'), [tr('page.help.mouse'), tr('page.help.esc'), tr('page.help.grab')]),
    (C.chat && on) ? grp(tr('page.help.g.chat'), [tr('page.help.chat.enter'), tr('page.help.chat.esc'), tr('page.help.chat.arrows')]) : null,
    (hasZones || C.names) ? grp(tr('page.help.g.zones'), [hasZones ? tr('page.help.zone.click') : '', hasZones ? tr('page.help.zone.cone') : '', C.names ? tr('page.help.zone.name') : '']) : null,
    grp(tr('page.help.g.page'), [tr('page.help.quit'), tr('page.help.h'), tr('page.help.i'), spawnList().length ? tr('page.help.l') : '', tr('page.help.o'), ABOUT.found ? tr('page.help.about') : '', hasMap ? tr('page.help.map.ctrl') : '', tr('page.help.k')])
  ].filter(Boolean); };
  const orbitGroups = () => [
    grp(tr('page.help.g.orbit'), [tr('page.help.orbit.drag'), tr('page.help.orbit.wheel'), tr('page.help.orbit.pan'), tr('page.help.orbit.reframe')]),
    grp(tr('page.help.g.walk'), [tr('page.help.enter'), tr('page.help.landing')]),
    (hasZones || C.names) ? grp(tr('page.help.g.zones'), [hasZones ? tr('page.help.zone.click.orbit') : '', hasZones ? tr('page.help.zone.cone') : '', C.names ? tr('page.help.zone.name') : '']) : null,
    grp(tr('page.help.g.page'), [tr('page.help.h'), tr('page.help.i'), spawnList().length ? tr('page.help.l') : '', tr('page.help.o'), ABOUT.found ? tr('page.help.about') : '', hasMap ? tr('page.help.map') : '', tr('page.help.center'), tr('page.help.k')])
  ].filter(Boolean);
  const feat = tr('page.feat', C.panel !== false ? tr('page.feat.panel.yes') : tr('common.no'), on ? tr('page.feat.presence.yes', C.room) : tr('page.feat.presence.no'), on && C.chat ? tr('common.yes') : tr('common.no'),
    on && C.spectate ? tr('common.yes') : (on ? tr('page.feat.spectate.no') : tr('common.no')), C.names ? tr('common.yes') : tr('page.feat.names.no'), C.version || '?');
  const l1 = document.createElement('div'), l2 = document.createElement('div');
  l2.style.cssText = 'font-size:11px;margin-top:4px;opacity:.85'; l2.textContent = feat;
  const hbody = document.getElementById('helpBody'), hhead = document.getElementById('helpHead');
  // v40 : lien vers le manuel complet sur GitHub (français si la page est en français, anglais sinon)
  const l3 = document.createElement('div'), man = document.createElement('a');
  l3.style.cssText = 'font-size:11px;margin-top:4px'; man.id = 'manualLink'; man.href = manualUrl(); man.target = '_blank'; man.rel = 'noopener'; man.textContent = tr('core.manual'); l3.append(man);
  hbody.append(l1, l2, l3);
  const fillGroups = groups => {
    l1.textContent = '';
    for (const g of groups) { const d = document.createElement('div'); d.className = 'grp'; const b = document.createElement('b'); b.textContent = g.t; d.append(b, g.items.join(' · ')); l1.append(d); }
    if (ABOUT.found) { const d = document.createElement('div'), b = document.createElement('button'); b.type = 'button'; b.id = 'aboutBtn'; b.textContent = tr('page.about.btn'); b.onclick = () => aboutToggle(); d.append(b); l1.append(d); }   // 1.4.5
  };
  // v34 : bloc d'état (texte sélectionnable, distinct de l'aide) : vue, mode (à pied / en vol), souris, position, tuiles
  const sb = document.getElementById('stateInfo'), sbody = document.getElementById('stateBody'), shead = document.getElementById('stateHead');
  const mkLine = id => { const d = document.createElement('div'); d.id = id; sbody.append(d); return d; };
  const lv = mkLine('viewInfo'), lm = mkLine('modeInfo'), lmo = mkLine('mouseInfo'), lp = mkLine('posInfo'), lkb = mkLine('kbInfo');
  // v39 : bouton « Copier le diagnostic » sous le contenu de la fenêtre (reste visible quand elle est réduite) : lignes affichées + diagText (core.js) ;
  // si le navigateur refuse la copie, le texte s'affiche sélectionné dessous (Ctrl+C)
  {
    const row = document.createElement('div'), bd = document.createElement('button'), dout = document.createElement('textarea');
    row.id = 'diagRow'; bd.type = 'button'; bd.id = 'diagBtn'; bd.textContent = tr('core.diag.btn'); bd.title = tr('core.diag.tip');
    bd.style.cssText = 'font:inherit;margin-top:4px;padding:2px 8px;border:1px solid #000;border-radius:4px;background:#fff;color:#000;cursor:pointer';
    dout.id = 'diagOut'; dout.readOnly = true; dout.rows = 8; dout.hidden = true; dout.setAttribute('aria-label', tr('core.diag.btn'));
    dout.style.cssText = 'display:block;width:100%;box-sizing:border-box;font:inherit;margin-top:4px';
    bd.onmousedown = e => e.preventDefault();   // le bouton ne garde pas le focus : Espace et Entrée restent à la promenade et au chat
    bd.onclick = async () => {
      const lines = [...sbody.children].filter(e => !e.hidden && e.textContent).map(e => e.textContent);
      if (C.presenceUrl) { const ps = document.getElementById('presenceStatus'); lines.push(tr('core.diag.line', tr('core.diag.presence'), String(C.presenceUrl).split(':')[0] + ' · ' + (ps && ps.textContent ? ps.textContent : '?')));
        const pr = viewer.getPresence(); if (pr.state !== 'off' || pr.opened || pr.closeCode !== null) lines.push(tr('core.diag.line', tr('core.diag.presence.conn'), tr('core.diag.presence.conn.v', pr.opened ? tr('common.yes') : tr('common.no'), pr.closeCode === null ? '\u2014' : pr.closeCode, pr.closeReason || '\u2014'))); }
      { const co = !!(window.matchMedia && matchMedia('(pointer: coarse)').matches);   // v46 : commandes tactiles
        lines.push(tr('core.diag.line', tr('page.diag.touch'), tr('page.diag.touch.v', CTL.touch ? tr('common.yes') : tr('common.no'), VIS.touch, co ? tr('common.yes') : tr('common.no'), navigator.maxTouchPoints || 0))); }
      const t = diagText(viewer, { cfgVersion: C.version, lines });
      dout.value = t;
      toast((await copyText(t, dout)) ? tr('core.diag.copied') : tr('page.toast.copyfail'));
    };
    row.append(bd);
    if (C.presenceUrl) {   // v48 : journal des visites, pour le créateur de la région (la clé reste nécessaire)
      const bv = document.createElement('button');
      bv.type = 'button'; bv.id = 'visitsBtn'; bv.textContent = tr('page.visits.open'); bv.title = tr('page.visits.open.tip');
      bv.style.cssText = bd.style.cssText + ';margin-left:6px';
      bv.onmousedown = e => e.preventDefault();
      bv.onclick = () => VISITS.open();
      row.append(bv);
    }
    row.append(dout); sb.append(row);
  }
  const setTxt = (el, t) => { if (el.textContent !== t) el.textContent = t; };
  const fb = document.getElementById('flyBtn'), gb = document.getElementById('grabBtn');
  const MOUSE = { captured: tr('page.mouse.captured'), free: tr('page.mouse.free'), idle: tr('page.mouse.idle') };
  const viewTick = () => {
    const w = viewer.walking;
    setTxt(lv, tr('page.state.view', w ? viewer.viewName : tr('page.state.view.global')));
    { const K = KB.keys(); setTxt(lkb, tr(KB.pref === 'auto' ? 'page.state.kb.auto' : 'page.state.kb', KB.layout().toUpperCase(), K.fwd + ' ' + K.left + ' ' + K.back + ' ' + K.right)); }
    lm.hidden = lmo.hidden = !w;
    if (w) { setTxt(lm, tr('page.state.mode', (viewer.flying ? tr('page.state.mode.fly') : tr('page.state.mode.walk')) + (viewer.running ? tr('page.state.run') : ''))); setTxt(lmo, tr('page.state.mouse', MOUSE[viewer.mouseState])); }
    fb.setAttribute('aria-pressed', viewer.flying ? 'true' : 'false');
    CTL.tick();
  };
  viewer.onView = viewTick; viewer.onFly = () => { viewTick(); refreshNear(); }; viewer.onMouse = viewTick;
  // v37 : largeur réglable (bord droit à tirer) pour l'aide et pour les informations : 260 px au moins, 70 % de la fenêtre au plus, mémorisée ; la hauteur suit le contenu.
  // Les deux fenêtres restent empilées en bas à gauche (l'aide au-dessus) : le bloc est ancré en bas, l'aide descend quand elle raccourcit.
  const mkResize = (el, lsKey) => {
    const hi = () => Math.max(260, Math.floor(innerWidth * 0.7));
    const apply = w => { el.style.maxWidth = '70vw'; el.style.width = Math.max(260, Math.min(hi(), Math.round(w))) + 'px'; };
    const near = e => { const r = el.getBoundingClientRect(); return e.clientX >= r.right - 9 && e.clientX <= r.right + 2 && e.clientY >= r.top && e.clientY <= r.bottom; };
    try { const v = parseInt(localStorage.getItem(lsKey), 10); if (v > 0) apply(v); } catch (e) {}
    let drag = null;
    el.addEventListener('pointermove', e => { if (drag) { apply(drag.w + e.clientX - drag.x); } else el.style.cursor = near(e) ? 'ew-resize' : ''; });
    el.addEventListener('pointerdown', e => { if (e.button !== 0 || !near(e)) return; e.preventDefault(); drag = { x: e.clientX, w: el.getBoundingClientRect().width }; try { el.setPointerCapture(e.pointerId); } catch (x) {} });
    const end = () => { if (!drag) return; drag = null; try { localStorage.setItem(lsKey, String(Math.round(el.getBoundingClientRect().width))); } catch (e) {} };
    el.addEventListener('pointerup', end); el.addEventListener('pointercancel', end);
    return apply;
  };
  const rzH = mkResize(wh, 'glb2html_helpW'), rzI = mkResize(sb, 'glb2html_stateW');
  for (const b of [fb, gb]) b.onmousedown = e => e.preventDefault();   // le bouton ne prend pas le focus (Espace saute, il ne clique pas)
  fb.onclick = () => { viewer.toggleFly(); viewTick(); };
  gb.onclick = () => { viewer.grabMouse(); viewTick(); };
  // position à noter (m, une décimale) : l'avatar en promenade, sinon la cible de la vue globale (le cercle d'atterrissage)
  const f1 = v => (Math.round(v * 10) / 10).toFixed(1);
  const posTick = () => {
    const w = viewer.walking ? viewer.getWalk().pos : null, t = viewer.controls.target;
    setTxt(lp, tr(w ? 'page.state.pos.avatar' : 'page.state.pos.target', f1(w ? w[0] : t.x), f1(w ? w[1] : t.y), f1(w ? w[2] : t.z))); viewTick();
  };
  posTick(); setInterval(posTick, 250);
  // « Aller à x, y, z » : mètres, repère du modèle d'origine en mode tuiles, repère de la page (modèle recentré) en mode GLB unique ; décimale « . » ou « , » (avec « ; » entre les nombres)
  const parseXYZ = txt => {
    let t = String(txt || '').trim(), parts;
    if (t.includes(';')) parts = t.split(';').map(x => x.trim().replace(',', '.'));
    else if (t.split(/\s+/).length === 3 && !/^[^,]*,[^,]*,[^,]*$/.test(t)) parts = t.split(/\s+/).map(x => x.replace(',', '.'));
    else parts = t.split(',').map(x => x.trim());
    if (parts.length !== 3) return null;
    const v = parts.map(x => (x === '' ? NaN : Number(x)));
    return v.every(Number.isFinite) && v.every(x => Math.abs(x) <= 1e5) ? v : null;
  };
  const gt = document.createElement('div'); gt.id = 'gotoRow'; gt.style.cssText = 'margin-top:6px;font-size:11px';
  const gin = document.createElement('input'), gbt = document.createElement('button'), gms = document.createElement('span');
  gin.id = 'gotoIn'; gin.size = 22; gin.placeholder = '68.2, 39, -823.3'; gin.setAttribute('aria-label', tr('page.goto.aria')); gbt.id = 'gotoBtn'; gbt.textContent = tr('page.goto.btn'); gms.id = 'gotoMsg'; gms.style.marginLeft = '6px';
  gt.append(tr('page.goto.label', C.tiles ? tr('page.goto.frame.tiles') : tr('page.goto.frame.page')), gin, ' ', gbt, gms);
  // v36 : une adresse complète contenant #pos=x,y,z[,yaw] est acceptée (position et orientation)
  const parsePosLink = txt => {
    const m = /[#&?]pos=([^&\s]+)/.exec(String(txt || '')); if (!m) return null;
    let raw; try { raw = decodeURIComponent(m[1]); } catch (e) { return null; }
    const v = raw.split(',').map(x => (x.trim() === '' ? NaN : Number(x)));
    return (v.length === 3 || v.length === 4) && v.every(Number.isFinite) && v.every(x => Math.abs(x) <= 1e5) ? v : null;
  };
  const doGoto = () => {
    const link = parsePosLink(gin.value), v = link ? link.slice(0, 3) : parseXYZ(gin.value);
    if (!v) { gms.textContent = tr('page.goto.bad'); return; }
    viewer.goTo(v, link && link.length > 3 ? link[3] : undefined); gms.textContent = viewer.walking ? tr('page.goto.tp', v.join(', ')) : tr('page.goto.moved', v.join(', '));
  };
  gbt.onclick = doGoto; gin.addEventListener('keydown', e => { e.stopPropagation(); if (e.key === 'Enter') { e.preventDefault(); doGoto(); } });   // les touches du champ ne déclenchent ni le chat ni les raccourcis
  // « Copier ma position » : au choix (liste mémorisée) l'adresse de la page + #pos=x,y,z,cap (lue à l'ouverture comme une arrivée anonyme) ou la série « x, y, z » en mètres (une décimale, point décimal)
  const lk = document.createElement('div'); lk.style.cssText = 'margin-top:6px;font-size:11px';
  const lbt = document.createElement('button'), lout = document.createElement('input'), lfmt = document.createElement('select');
  lbt.id = 'linkBtn'; lbt.textContent = tr('page.copy.btn'); lout.id = 'linkOut'; lout.readOnly = true; lout.size = 28; lout.setAttribute('aria-label', tr('page.copy.aria'));
  lfmt.id = 'linkFmt'; lfmt.setAttribute('aria-label', tr('page.copy.fmt.aria'));
  for (const [v, t] of [['url', 'URL'], ['xyz', 'xyz']]) lfmt.append(Object.assign(document.createElement('option'), { value: v, textContent: t }));
  lfmt.value = lsGet('glb2html_copyfmt') === 'xyz' ? 'xyz' : 'url'; lfmt.onchange = () => lsSet('glb2html_copyfmt', lfmt.value);
  lbt.onclick = async () => {
    const w = viewer.walking ? viewer.getWalk() : null, tg = viewer.controls.target, cp = viewer.camera.position;
    const p = w ? w.pos : tg.toArray(), yaw = w ? w.yaw : Math.atan2(-(tg.x - cp.x), -(tg.z - cp.z));
    let text;
    if (lfmt.value === 'xyz') text = p.map(f1).join(', ');
    else { const u = new URL(location.href); u.hash = 'pos=' + p.concat([yaw]).map(x => String(Math.round(x * 100) / 100)).join(','); text = u.href; }
    lout.value = text;
    toast((await copyText(text, lout)) ? tr('page.toast.copied') : tr('page.toast.copyfail'));
  };
  lk.append(lbt, ' ', lfmt, ' ', lout);
  hbody.append(gt, lk);
  const hm = document.getElementById('homeBtn'); hm.hidden = false;
  const goHome = () => { if (!viewer.returnHome()) toast(tr('page.home.none')); };
  hm.onclick = goHome;
  addEventListener('keydown', e => { const n = e.target && e.target.tagName; if (e.code === 'KeyR' && !e.repeat && !e.ctrlKey && !e.metaKey && !e.altKey && n !== 'INPUT' && n !== 'TEXTAREA' && n !== 'SELECT') goHome(); });
  const hb = document.getElementById('helpBtn');
  // v36 : H (aide) et I (informations) tournent en trois temps : masquée -> déployée ; réduite -> déployée ; déployée -> masquée. Réduit / déployé et masqué sont mémorisés.
  const mkPanel = (wrap, head, body, title, openKey, foldKey) => {
    let open = lsGet(openKey) !== '0', folded = lsGet(foldKey) === '1';
    const apply = () => { wrap.hidden = !open; body.hidden = folded; head.textContent = (folded ? '▸ ' : '▾ ') + title; head.setAttribute('aria-expanded', folded ? 'false' : 'true'); };
    const save = () => { lsSet(openKey, open ? '1' : '0'); lsSet(foldKey, folded ? '1' : '0'); };
    head.onclick = () => { folded = !folded; save(); apply(); };
    head.onmousedown = e => e.preventDefault();
    return {
      apply, get open() { return open; }, get folded() { return folded; },
      cycle() { if (!open) { open = true; folded = false; } else if (folded) folded = false; else open = false; save(); apply(); },
      reload() { open = lsGet(openKey) !== '0'; folded = lsGet(foldKey) === '1'; apply(); },   // v41 : après chargement d'une disposition
      hide() { open = false; save(); apply(); },   // v46 : bouton ✕ (écran tactile)
      foldTmp() { if (open && !folded) { folded = true; apply(); } }   // v46 : réduite à l'ouverture sur écran tactile, sans changer le réglage retenu
    };
  };
  const helpP = mkPanel(wh, hhead, hbody, tr('page.help.title'), 'glb2html_help', 'glb2html_helpFold'), stateP = mkPanel(sb, shead, sbody, tr('page.info.title'), 'glb2html_state', 'glb2html_stateFold');
  // v40 : fenêtre « Arrivées » (touche L, même cycle que H et I) : un clic sur un nom téléporte à l'arrivée en promenade, ou y entre en promenade depuis la vue globale.
  // Masquée tant que la région n'a aucune arrivée.
  const spi = document.getElementById('spawnInfo'), spb = document.getElementById('spawnBody'), sph = document.getElementById('spawnHead');
  spi.title = tr('page.spawn.tip');
  const spawnP = mkPanel(spi, sph, spb, tr('page.spawn.title'), 'glb2html_spawn', 'glb2html_spawnFold');
  // la hauteur de la fenêtre est retirée de celle de l'aide (variable --spawnH) : la colonne de gauche ne sort pas de l'écran
  const spawnH = () => document.documentElement.style.setProperty('--spawnH', (spi.hidden || spi.parentElement !== document.getElementById('hudL') ? 0 : spi.offsetHeight + 6) + 'px');
  if (window.ResizeObserver) new ResizeObserver(spawnH).observe(spi);
  let spawnCount = 0;
  const applySpawn = () => { spawnP.apply(); if (!spawnCount) spi.hidden = true; spawnH(); };
  refreshSpawns = () => {
    const list = spawnList(); spawnCount = list.length; spb.textContent = '';
    for (const s of list) {
      const b = document.createElement('button'), name = s.label || s.id;
      b.type = 'button'; b.textContent = name;
      b.onmousedown = e => e.preventDefault();   // pas de focus : Espace et Entrée restent à la promenade et au chat
      b.onclick = () => {
        const p = [s.x, s.y, s.z];
        if (viewer.walking) viewer.goTo(p, s.yaw); else viewer.walkStart({ pos: p, yaw: s.yaw });
        toast(tr('page.spawn.done', name));
      };
      spb.append(b);
    }
    applySpawn(); applyHelp(viewer.walking);
  };
  addEventListener('keydown', e => {
    const n = e.target && e.target.tagName;
    if (e.code !== 'KeyL' || e.repeat || e.ctrlKey || e.metaKey || e.altKey || n === 'INPUT' || n === 'TEXTAREA' || n === 'SELECT') return;
    if (!spawnCount) return toast(tr('page.spawn.none'));
    spawnP.cycle(); applySpawn();
  });
  // v41 : fenêtres H, I, L déplaçables par leur titre. Deux piles : gauche (en bas, d'origine) et droite (sous Réglages : poussée quand Réglages s'ouvre).
  // Lâchée près d'une pile : elle s'y accroche (à la hauteur du lâcher) ; ailleurs : libre, à l'endroit exact. Double-clic sur le titre : retour à la
  // dernière pile où elle était accrochée. Disposition retenue par le navigateur (glb2html_layout) ; Réglages : enregistrer / charger un fichier .json.
  const rzL = mkResize(spi, 'glb2html_spawnW');
  const hudL = document.getElementById('hudL'), hudR = document.getElementById('hudR');
  const WINS = { H: [wh, hhead, 'page.win.h.tip', rzH, 'glb2html_helpW'], I: [sb, shead, 'page.win.i.tip', rzI, 'glb2html_stateW'], L: [spi, sph, 'page.win.l.tip', rzL, 'glb2html_spawnW'] };
  const ORDER = ['H', 'I', 'L'];
  const LKEYS = ['glb2html_help', 'glb2html_helpFold', 'glb2html_state', 'glb2html_stateFold', 'glb2html_spawn', 'glb2html_spawnFold', 'glb2html_helpW', 'glb2html_stateW', 'glb2html_spawnW'];
  const layDefault = () => ({ wins: { H: { pile: 'L', home: 'L' }, I: { pile: 'L', home: 'L' }, L: { pile: 'L', home: 'L' } }, order: { L: ORDER.slice(), R: [] } });
  const layNorm = o => {   // disposition lue (navigateur ou fichier) : remise en forme, ou null si elle n'en est pas une
    if (!o || typeof o !== 'object' || !o.wins || typeof o.wins !== 'object') return null;
    const out = { wins: {}, order: { L: [], R: [] } };
    for (const k of ORDER) {
      const w = o.wins[k] || {}, pile = ['L', 'R', 'F'].includes(w.pile) ? w.pile : 'L', home = w.home === 'R' ? 'R' : 'L';
      out.wins[k] = pile === 'F' ? { pile, home, x: Number.isFinite(w.x) ? Math.round(w.x) : 100, y: Number.isFinite(w.y) ? Math.round(w.y) : 100 } : { pile, home };
    }
    for (const p of ['L', 'R']) {
      const given = (o.order && Array.isArray(o.order[p]) ? o.order[p] : []).filter(k => ORDER.includes(k) && out.wins[k].pile === p);
      out.order[p] = [...new Set(given.concat(ORDER.filter(k => out.wins[k].pile === p)))];
    }
    return out;
  };
  let lay = null;
  try { lay = layNorm(JSON.parse(lsGet('glb2html_layout') || 'null')); } catch (e) {}
  if (!lay) lay = layDefault();
  const laySave = () => lsSet('glb2html_layout', JSON.stringify(lay));
  const clampFree = () => {   // une fenêtre libre reste dans l'écran (titre atteignable) ; la position retenue ne change pas
    for (const k of ORDER) {
      const w = lay.wins[k]; if (w.pile !== 'F') continue;
      const el = WINS[k][0], r = el.getBoundingClientRect(), W = Math.min(r.width || 200, innerWidth);
      el.style.left = Math.max(0, Math.min(innerWidth - W, w.x)) + 'px'; el.style.top = Math.max(0, Math.min(innerHeight - 30, w.y)) + 'px';
    }
  };
  const place = () => {
    for (const p of ['L', 'R']) for (const k of lay.order[p]) { const el = WINS[k][0]; el.classList.remove('winFree'); el.style.left = el.style.top = ''; (p === 'L' ? hudL : hudR).append(el); }
    for (const k of ORDER) if (lay.wins[k].pile === 'F') { const el = WINS[k][0]; el.classList.add('winFree'); document.body.append(el); }
    clampFree(); spawnH();
  };
  const toPile = (k, p, y) => {   // accroche k à la pile p : à la hauteur y du lâcher, sinon à sa place d'origine (ordre H, I, L)
    for (const q of ['L', 'R']) lay.order[q] = lay.order[q].filter(x => x !== k);
    const list = lay.order[p];
    const idx = y === undefined ? list.filter(q => ORDER.indexOf(q) < ORDER.indexOf(k)).length
      : list.filter(q => { const r = WINS[q][0].getBoundingClientRect(); return r.height && r.top + r.height / 2 < y; }).length;
    list.splice(idx, 0, k);
    lay.wins[k] = { pile: p, home: p };
    laySave(); place();
  };
  const inside = (z, x, y) => x >= z.l && x <= z.r && y >= z.t && y <= z.b;
  const drop = (k, x, y, r) => {
    const oR = document.getElementById('opts').getBoundingClientRect(), hR = hudR.getBoundingClientRect();
    const lR = hudL.getBoundingClientRect(), barT = document.getElementById('bar').getBoundingClientRect().top;
    const zR = { l: Math.min(oR.left, innerWidth - 320) - 40, r: innerWidth, t: 0, b: Math.max(oR.bottom, hR.bottom) + 60 };
    const zL = { l: 0, r: Math.max(lR.right, 200) + 60, t: Math.min(lR.height ? lR.top : barT, barT - 40) - 60, b: innerHeight };
    if (inside(zR, x, y)) return toPile(k, 'R', y);
    if (inside(zL, x, y)) return toPile(k, 'L', y);
    for (const q of ['L', 'R']) lay.order[q] = lay.order[q].filter(x2 => x2 !== k);
    lay.wins[k] = { pile: 'F', home: lay.wins[k].home, x: Math.round(r.left), y: Math.round(r.top) };
    laySave(); place();
  };
  for (const k of ORDER) {
    const [el, head, tipKey] = WINS[k];
    head.title = tr(tipKey) + '\n' + tr('page.win.move');
    let d = null, moved = false;
    // le glisser se suit sur la fenêtre du navigateur : déplacer la fenêtre dans la page fait perdre la capture du pointeur au titre
    const mv = e => {
      if (!d || e.pointerId !== d.id) return;
      if (!moved) {
        if (Math.hypot(e.clientX - d.x, e.clientY - d.y) < 5) return;
        moved = true;
        el.style.width = el.style.width || Math.round(d.r.width) + 'px';   // garde sa largeur en quittant la pile
        el.classList.add('winFree', 'winDrag'); document.body.append(el); spawnH();
      }
      el.style.left = (d.r.left + e.clientX - d.x) + 'px'; el.style.top = (d.r.top + e.clientY - d.y) + 'px';
    };
    const end = e => {
      if (!d || e.pointerId !== d.id) return;
      removeEventListener('pointermove', mv); removeEventListener('pointerup', end); removeEventListener('pointercancel', end);
      const was = moved; d = null; el.classList.remove('winDrag');
      if (!was) return;
      head.dataset.noClick = '1'; setTimeout(() => { delete head.dataset.noClick; }, 0);   // le clic qui suit un glisser ne replie pas la fenêtre
      drop(k, e.clientX, e.clientY, el.getBoundingClientRect());
    };
    head.addEventListener('pointerdown', e => {
      if (e.button !== 0) return;
      const r = el.getBoundingClientRect();
      if (e.clientX >= r.right - 12) return;   // bord droit : réservé à la largeur (v37)
      d = { x: e.clientX, y: e.clientY, r, id: e.pointerId }; moved = false;
      addEventListener('pointermove', mv); addEventListener('pointerup', end); addEventListener('pointercancel', end);
    });
    // clic sur le titre : réduire / déplier, 250 ms plus tard à la souris pour qu'un double-clic ne replie pas (le titre bougerait sous la souris).
    // Clic au clavier ou par programme (detail 0) : immédiat. Clic qui termine un glisser : ignoré.
    const tog = head.onclick; let tm = 0;
    head.addEventListener('click', e => {
      e.stopImmediatePropagation(); e.preventDefault();
      if (head.dataset.noClick) return;
      clearTimeout(tm);
      if (!e.detail) return tog && tog.call(head, e);
      if (e.detail === 1) tm = setTimeout(() => tog && tog.call(head, e), 250);
    }, true);
    head.addEventListener('dblclick', e => { e.preventDefault(); toPile(k, lay.wins[k].home); });
  }
  addEventListener('resize', clampFree);
  place();
  // Réglages : enregistrer la disposition dans un fichier, la recharger, revenir à la disposition d'origine
  const opn = document.getElementById('optsPanel');
  if (C.panel !== false && opn) {
    const mkb = (id, key) => Object.assign(document.createElement('button'), { id, type: 'button', textContent: tr(key) });
    const sec = document.createElement('div'), lt = document.createElement('div'), row = document.createElement('div');   // v42 : vraie section (titre, filet, boutons)
    sec.className = 'sec'; sec.id = 'laySec'; lt.className = 'secT'; lt.textContent = tr('page.layout.title'); row.className = 'btnrow';
    const bS = mkb('laySave', 'page.layout.save'), bL = mkb('layLoad', 'page.layout.load'), bR = mkb('layReset', 'page.layout.reset');
    const fi = Object.assign(document.createElement('input'), { type: 'file', accept: '.json,application/json', hidden: true, id: 'layFile' });
    const applyAll = () => {   // relit états et largeurs (navigateur), puis replace les fenêtres
      for (const k of ORDER) { const [el, , , rz, wk] = WINS[k]; const v = parseInt(lsGet(wk), 10); if (v > 0) rz(v); else { el.style.width = ''; el.style.maxWidth = ''; } }
      helpP.reload(); stateP.reload(); spawnP.reload(); applyHelp(viewer.walking); place();
    };
    bS.onclick = () => {
      const ls = {}; for (const key of LKEYS) { const v = lsGet(key); if (v !== null) ls[key] = v; }
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([JSON.stringify({ app: 'web3d-layout', v: 1, layout: lay, ls }, null, 1)], { type: 'application/json' }));
      a.download = 'disposition.json'; document.body.append(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 10000);
      toast(tr('page.layout.saved'));
    };
    bL.onclick = () => fi.click();
    fi.onchange = async () => {
      const f = fi.files && fi.files[0]; fi.value = '';
      if (!f) return;
      let o = null; try { o = JSON.parse(await f.text()); } catch (e) {}
      const nl = o && o.app === 'web3d-layout' ? layNorm(o.layout) : null;
      if (!nl) return toast(tr('page.layout.bad'));
      for (const key of LKEYS) { const v = o.ls && o.ls[key]; if (typeof v === 'string') lsSet(key, v); else try { localStorage.removeItem(key); } catch (e) {} }
      lay = nl; laySave(); applyAll(); toast(tr('page.layout.loaded'));
    };
    bR.onclick = () => {
      for (const key of ['glb2html_helpW', 'glb2html_stateW', 'glb2html_spawnW']) try { localStorage.removeItem(key); } catch (e) {}
      lay = layDefault(); laySave(); applyAll(); toast(tr('page.layout.reset.done'));
    };
    for (const b of [bS, bL, bR]) b.onmousedown = e => e.preventDefault();
    row.append(bS, bL, bR); sec.append(lt, row, fi);
    const note = document.getElementById('optsNote'); if (note && note.parentNode === opn) opn.insertBefore(sec, note); else opn.append(sec);
  }
  const applyHelp = walking => { fillGroups(walking ? walkGroups() : orbitGroups()); viewTick(); stateP.apply(); applySpawn(); helpP.apply(); hb.hidden = false; hb.textContent = !helpP.open ? tr('page.btn.help') : (helpP.folded ? tr('page.btn.help.expand') : tr('page.btn.help.hide')); };
  const toggleHelp = () => { helpP.cycle(); applyHelp(viewer.walking); };
  hb.onclick = toggleHelp;
  KB.listeners.push(() => applyHelp(viewer.walking));
  applyHelp(false);
  addEventListener('keydown', e => { const n = e.target && e.target.tagName; if (e.code === 'KeyH' && !e.repeat && !e.ctrlKey && !e.metaKey && !e.altKey && n !== 'INPUT' && n !== 'TEXTAREA' && n !== 'SELECT') toggleHelp(); });
  addEventListener('keydown', e => {   // I : la fenêtre Informations / État (vue, mode, position, tuiles), indépendante de l'aide
    const n = e.target && e.target.tagName;
    if (e.code === 'KeyI' && !e.repeat && !e.ctrlKey && !e.metaKey && !e.altKey && n !== 'INPUT' && n !== 'TEXTAREA' && n !== 'SELECT') stateP.cycle();
  });
  addEventListener('keydown', e => {
    const n = e.target && e.target.tagName;
    if ((e.code === 'Enter' || e.code === 'NumpadEnter') && viewer.walking && !(on && C.chat) && n !== 'INPUT') toast(tr('page.chat.disabled'));
  });
  wb.onclick = () => viewer.toggleWalk();
  addEventListener('keydown', e => {
    const n = e.target && e.target.tagName;
    if (e.code === 'KeyF' && !e.repeat && !e.ctrlKey && !e.metaKey && !e.altKey && n !== 'INPUT' && n !== 'TEXTAREA' && n !== 'SELECT') viewer.toggleWalk();   // v36 : F entre ET sort de la promenade, comme P ; le vol se bascule avec Début ou le bouton
    if (e.code === 'KeyP' && !e.repeat && !e.ctrlKey && !e.metaKey && !e.altKey && n !== 'INPUT' && n !== 'TEXTAREA' && n !== 'SELECT') viewer.toggleWalk();
  });
  viewer.onCones = on2 => toast(on2 ? tr('page.cones.on') : tr('page.cones.off'));
  viewer.onLanding = () => toast(tr('page.landing.chosen'));
  viewer.onWalk = on2 => { document.getElementById('centerBtn').hidden = on2; fb.hidden = !(on2 && fly); gb.hidden = !on2; wb.hidden = on2; applyHelp(on2); posTick(); { const mbn = document.getElementById('mapBtn'); if (mbn) mbn.textContent = on2 ? tr('page.btn.map.ctrl') : tr('page.btn.map'); } document.getElementById('nameTag').hidden = true; CTL.apply(); };
  // v46 : commandes à l'écran. Ligne d'état (mode, allure, vue, position) toujours visible ; pavé de flèches 3 x 3 (promenade : avancer, reculer,
  // tourner, courir, et en vol monter, descendre ; vue globale : déplacer, tourner, rapprocher, éloigner, recentrer au centre), escamotable
  // (K, bouton « Flèches (K) », Réglages) ; appui maintenu = touche tenue. Mode tactile (écran tactile détecté, ou réglage) : colonne de boutons,
  // menu, fenêtres réduites à l'ouverture avec un ✕, glisser du doigt pour regarder (core.js), bulle par appui long.
  {
    const body = document.body, stl = document.getElementById('statusLine'), stM = document.getElementById('statusMode'), stR = document.getElementById('statusRest');
    const pad = document.getElementById('pad'), tcol = document.getElementById('tcol'), tmenu = document.getElementById('tmenu'), tip = document.getElementById('tipBox');
    const pb = document.getElementById('padBtn'), cbn = document.getElementById('centerBtn'), mbn = document.getElementById('mapBtn');
    const coarse = window.matchMedia ? matchMedia('(pointer: coarse)') : null;
    const isTouch = () => VIS.touch === 'on' || (VIS.touch === 'auto' && !!(coarse && coarse.matches));
    const P = { up: 'M12 19V5M5 12l7-7 7 7', down: 'M12 5v14M5 12l7 7 7-7', left: 'M19 12H5M12 5l-7 7 7 7', right: 'M5 12h14M12 5l7 7-7 7',
      tl: 'M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5', tr: 'M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5', plus: 'M12 5v14M5 12h14', minus: 'M5 12h14',
      center: 'M12 4a8 8 0 1 0 0 16a8 8 0 1 0 0-16M12 10a2 2 0 1 0 0 4a2 2 0 1 0 0-4', fup: 'M6 15l6-6 6 6M6 21l6-6 6 6', fdown: 'M6 3l6 6 6-6M6 9l6 6 6-6' };
    const mkB = (id, cls) => { const b = document.createElement('button'); b.type = 'button'; if (id) b.id = id; if (cls) b.className = cls; b.onmousedown = e => e.preventDefault(); return b; };
    const ico = (b, d) => { b.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="' + d + '"></path></svg>'; };
    const gap = () => { const d = document.createElement('span'); d.className = 'gap'; return d; };
    const setTip = (b, t) => { b.title = t; b.setAttribute('aria-label', t.split('\n')[0]); };
    // bulle par appui long (écran tactile) : 0,5 s ; sur un bouton à action unique, l'appui long montre la bulle sans déclencher l'action
    let tipT = 0;
    const showTip = b => {
      const t = b.title; if (!t) return;
      tip.textContent = t; tip.hidden = false;
      const r = b.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
      tip.style.left = Math.max(8, Math.min(innerWidth - w - 8, r.left + r.width / 2 - w / 2)) + 'px';
      tip.style.top = (r.top - h - 8 >= 8 ? r.top - h - 8 : Math.min(innerHeight - h - 8, r.bottom + 8)) + 'px';
      clearTimeout(tipT); tipT = setTimeout(() => { tip.hidden = true; }, 2500);
    };
    const longPress = (b, keepAction) => {
      let tm = 0;
      b.addEventListener('pointerdown', e => { if (e.pointerType !== 'touch') return; clearTimeout(tm); tm = setTimeout(() => { showTip(b); if (!keepAction) b.dataset.lp = '1'; }, 500); });
      for (const ev of ['pointerup', 'pointercancel', 'pointerleave']) b.addEventListener(ev, () => clearTimeout(tm));
      b.addEventListener('click', e => { if (b.dataset.lp) { delete b.dataset.lp; e.preventDefault(); e.stopImmediatePropagation(); } }, true);
      b.addEventListener('contextmenu', e => e.preventDefault());
    };
    // appui maintenu : start() à l'appui, stop() au relâcher (le pointeur est capturé : glisser hors du bouton ne relâche pas)
    const hold = (b, start, stop) => {
      let on = false;
      const end = () => { if (!on) return; on = false; b.classList.remove('held'); stop(); };
      b.addEventListener('pointerdown', e => { if (e.button !== 0) return; e.preventDefault(); if (on) return; on = true; b.classList.add('held'); try { b.setPointerCapture(e.pointerId); } catch (x) {} start(); });
      for (const ev of ['pointerup', 'pointercancel', 'lostpointercapture']) b.addEventListener(ev, end);
      longPress(b, true);
      return end;
    };
    const ends = [];
    const holdKey = (b, code) => { ends.push(hold(b, () => viewer.padKey(code, true), () => viewer.padKey(code, false))); };
    const holdRep = (b, fn) => {   // vue globale : répétition tant que le bouton est tenu (pas proportionnel au temps écoulé)
      let tm = 0, t = 0;
      ends.push(hold(b, () => { t = performance.now(); fn(0.05); tm = setInterval(() => { const n = performance.now(); fn((n - t) / 1000); t = n; }, 30); }, () => { clearInterval(tm); }));
    };
    const holdTxt = '\n' + tr('page.pad.hold');
    // pavé de la promenade
    const pw = document.createElement('div'), pg = document.createElement('div'); pw.id = 'padWalk'; pg.id = 'padGlobal';
    const K = () => KB.keys();
    const bSl = mkB('padSideL'), bSr = mkB('padSideR');   // pas de côté (Q / D en AZERTY, A / D en QWERTY : codes physiques KeyA, KeyD)
    const bUp = mkB('padUp'), bDn = mkB('padDown'), bL = mkB('padLeft'), bR = mkB('padRight'), bRun = mkB('padRun'), bFu = mkB('padFlyUp'), bFd = mkB('padFlyDown');
    ico(bUp, P.up); ico(bDn, P.down); ico(bL, P.tl); ico(bR, P.tr); ico(bFu, P.fup); ico(bFd, P.fdown); ico(bSl, P.left); ico(bSr, P.right);
    holdKey(bSl, 'KeyA'); holdKey(bSr, 'KeyD');
    bRun.textContent = tr('page.pad.run'); bRun.setAttribute('aria-pressed', 'false');
    holdKey(bUp, 'ArrowUp'); holdKey(bDn, 'ArrowDown'); holdKey(bL, 'ArrowLeft'); holdKey(bR, 'ArrowRight'); holdKey(bFu, 'PageUp'); holdKey(bFd, 'PageDown');
    bRun.onclick = () => { viewer.runLatch = !viewer.runLatch; tick(); }; longPress(bRun);
    // rangé comme le pavé de la vue globale : tourner aux coins du haut, pas de côté au milieu, monter et descendre (en vol) aux coins du bas
    pw.append(bL, bUp, bR, bSl, bRun, bSr, bFu, bDn, bFd);
    // pavé de la vue globale
    const gTl = mkB('padTurnL'), gF = mkB('padFwd'), gTr = mkB('padTurnR'), gL = mkB('padPanL'), gC = mkB('padCenter'), gR = mkB('padPanR'), gO = mkB('padOut'), gB = mkB('padBack'), gI = mkB('padIn');
    ico(gTl, P.tl); ico(gF, P.up); ico(gTr, P.tr); ico(gL, P.left); ico(gC, P.center); ico(gR, P.right); ico(gO, P.minus); ico(gB, P.down); ico(gI, P.plus);
    holdRep(gF, dt => viewer.globalMove(1, 0, dt)); holdRep(gB, dt => viewer.globalMove(-1, 0, dt));
    holdRep(gL, dt => viewer.globalMove(0, -1, dt)); holdRep(gR, dt => viewer.globalMove(0, 1, dt));
    holdRep(gTl, dt => viewer.globalTurn(1, dt)); holdRep(gTr, dt => viewer.globalTurn(-1, dt));
    holdRep(gO, dt => viewer.globalZoom(1, dt)); holdRep(gI, dt => viewer.globalZoom(-1, dt));
    gC.onclick = () => cbn.click(); longPress(gC);
    pg.append(gTl, gF, gTr, gL, gC, gR, gO, gB, gI);
    pad.setAttribute('aria-label', tr('page.pad.label')); pad.append(pw, pg);
    const padTips = () => {
      const k = K();
      setTip(bUp, tr('page.pad.fwd', k.fwd) + holdTxt); setTip(bDn, tr('page.pad.back', k.back) + holdTxt);
      setTip(bL, tr('page.pad.left') + holdTxt); setTip(bR, tr('page.pad.right') + holdTxt);
      setTip(bSl, tr('page.pad.side.l', k.left) + holdTxt); setTip(bSr, tr('page.pad.side.r', k.right) + holdTxt);
      setTip(bRun, tr('page.pad.run.tip')); setTip(bFu, tr('page.pad.up') + holdTxt); setTip(bFd, tr('page.pad.down') + holdTxt);
      setTip(gF, tr('page.pad.g.fwd') + holdTxt); setTip(gB, tr('page.pad.g.back') + holdTxt); setTip(gL, tr('page.pad.g.left') + holdTxt); setTip(gR, tr('page.pad.g.right') + holdTxt);
      setTip(gTl, tr('page.pad.g.tl') + holdTxt); setTip(gTr, tr('page.pad.g.tr') + holdTxt); setTip(gO, tr('page.pad.g.out') + holdTxt); setTip(gI, tr('page.pad.g.in') + holdTxt);
      setTip(gC, tr('page.btn.center') + '\n' + tr('page.btn.center.tip'));
    };
    padTips(); KB.listeners.push(padTips);
    // bulles des boutons de la barre
    wb.title = tr('page.btn.walk.tip'); fb.title = tr('page.btn.fly.tip'); gb.title = tr('page.btn.grab.tip'); hm.title = tr('page.btn.home.tip'); hb.title = tr('page.btn.help.tip');
    mbn.title = tr('page.btn.map.tip'); cbn.title = tr('page.btn.center.tip'); pb.title = tr('page.btn.pad.tip');
    const togglePad = () => { VIS.pad = !VIS.pad; visSave(); CTL.sync(); apply(); };
    pb.onmousedown = e => e.preventDefault(); pb.onclick = togglePad;
    addEventListener('keydown', e => { const n = e.target && e.target.tagName; if (e.code === 'KeyK' && !e.repeat && !e.ctrlKey && !e.metaKey && !e.altKey && n !== 'INPUT' && n !== 'TEXTAREA' && n !== 'SELECT') togglePad(); });
    // colonne de boutons (mode tactile)
    const tWalk = mkB('tWalk'), tJump = mkB('tJump'), tFly = mkB('tFly'), tView = mkB('tView'), tChat = mkB('tChat'), tPad = mkB('tPad'), tMenu = mkB('tMenu');
    tWalk.onclick = () => viewer.toggleWalk();
    tJump.onclick = () => viewer.padJump(); tJump.textContent = tr('page.t.jump'); setTip(tJump, tr('page.t.jump.tip'));
    tFly.onclick = () => { viewer.toggleFly(); viewTick(); }; setTip(tFly, tr('page.btn.fly.tip'));
    tView.onclick = () => { viewer.cycleView(); viewTick(); }; tView.textContent = tr('page.t.view'); setTip(tView, tr('page.t.view.tip'));
    tChat.onclick = () => { if (CTL.chat) CTL.chat.open(); tick(); }; setTip(tChat, tr('page.t.chat.tip'));
    tPad.onclick = togglePad; tPad.textContent = tr('page.t.pad'); setTip(tPad, tr('page.btn.pad.tip'));
    tMenu.textContent = tr('page.t.menu'); setTip(tMenu, tr('page.t.menu.tip')); tMenu.setAttribute('aria-expanded', 'false');
    tcol.setAttribute('aria-label', tr('page.t.label'));
    for (const b of [tWalk, tJump, tFly, tView, tChat, tPad, tMenu]) { longPress(b); tcol.append(b); }
    // menu (mode tactile) : fenêtres, carte, retour, recentrer (quand les flèches sont cachées), plein écran (si le navigateur le permet)
    const fsEl = () => document.fullscreenElement || document.webkitFullscreenElement || null;
    const fsOK = !!(document.fullscreenEnabled || document.webkitFullscreenEnabled);
    const fsToggle = () => {
      try {
        if (fsEl()) { const x = document.exitFullscreen || document.webkitExitFullscreen; if (x) x.call(document); return; }
        const r = document.documentElement, f = r.requestFullscreen || r.webkitRequestFullscreen;
        const q = f ? f.call(r) : null; if (q && q.catch) q.catch(() => toast(tr('page.menu.full.fail')));
      } catch (e) { toast(tr('page.menu.full.fail')); }
    };
    const menuItems = [
      ['mHelp', () => tr('page.menu.help'), () => true, () => toggleHelp()],
      ['mInfo', () => tr('page.menu.info'), () => true, () => { stateP.cycle(); }],
      ['mSpawn', () => tr('page.menu.spawn'), () => spawnCount > 0, () => { spawnP.cycle(); applySpawn(); }],
      ['mMap', () => tr('page.menu.map'), () => !mbn.hidden, () => mbn.click()],
      ['mHome', () => tr('page.menu.home'), () => viewer.walking && !hm.hidden, () => hm.click()],
      ['mCenter', () => tr('page.menu.center'), () => !viewer.walking && !VIS.pad, () => cbn.click()],
      ['mFull', () => (fsEl() ? tr('page.menu.fullexit') : tr('page.menu.full')), () => fsOK, fsToggle]
    ].map(([id, label, when, act]) => { const b = mkB(id); b.setAttribute('role', 'menuitem'); b.onclick = () => { closeMenu(); act(); }; tmenu.append(b); return { b, label, when }; });
    const mClose = mkB('mClose', 'close'); mClose.textContent = tr('page.menu.close'); mClose.onclick = () => closeMenu(); tmenu.append(mClose);
    const closeMenu = () => { tmenu.hidden = true; tMenu.setAttribute('aria-expanded', 'false'); };
    const openMenu = () => { for (const m of menuItems) { m.b.hidden = !m.when(); m.b.textContent = m.label(); } tmenu.hidden = false; tMenu.setAttribute('aria-expanded', 'true'); };
    tMenu.onclick = () => (tmenu.hidden ? openMenu() : closeMenu());
    addEventListener('keydown', e => { if (e.key === 'Escape' && !tmenu.hidden) closeMenu(); });
    // fenêtres H, I, L : bouton ✕ (visible en mode tactile seulement)
    for (const [wrap, pn] of [[wh, helpP], [sb, stateP], [spi, spawnP]]) {
      const x = mkB('', 'winX'); x.textContent = '\u2715'; setTip(x, tr('page.win.close'));
      x.onclick = () => { pn.hide(); applySpawn(); applyHelp(viewer.walking); };
      wrap.append(x);
    }
    // ligne d'état : mode en gras (mot écrit, jamais une couleur), puis allure, vue et position ; en vue globale, la cible
    const statusTick = () => {
      const w = viewer.walking;
      if (w) {
        const g = viewer.getWalk().pos;
        setTxt(stM, tr('page.status.walk'));
        setTxt(stR, '\u00b7 ' + (viewer.flying ? tr('page.state.mode.fly') : tr('page.state.mode.walk')) + (viewer.running ? tr('page.state.run') : '') + ' \u00b7 ' + viewer.viewName + ' \u00b7 ' + tr('page.status.pos', f1(g[0]), f1(g[1]), f1(g[2])));
      } else {
        const t = viewer.controls.target;
        setTxt(stM, tr('page.status.global')); setTxt(stR, '\u00b7 ' + tr('page.status.target', f1(t.x), f1(t.y), f1(t.z)));
      }
    };
    let touchOn = null, folded0 = false, hint = false;
    const topsEls = ['presence', 'compass', 'optsBtn'].map(i => document.getElementById(i)).filter(Boolean), rootSt = document.documentElement.style;
    const setVar = (k, v) => { const t = Math.round(v) + 'px'; if (rootSt.getPropertyValue(k) !== t) rootSt.setProperty(k, t); };
    const touchTops = () => {   // mode tactile : la ligne d'état passe sous le bloc du pseudo, la boussole et Réglages ; fenêtres, chat et invites dessous
      let y = 12; for (const el of topsEls) if (!el.hidden && el.getClientRects().length) y = Math.max(y, el.getBoundingClientRect().bottom);   // éléments fixes : offsetParent est toujours null
      setVar('--tstat', y + 6); setVar('--ttop', stl.getBoundingClientRect().bottom + 8);
    };
    const tick = () => {
      statusTick();
      const w = viewer.walking, fl = w && viewer.flying, t = !!touchOn;
      bFu.style.visibility = bFd.style.visibility = fl ? '' : 'hidden';
      bRun.setAttribute('aria-pressed', viewer.runLatch ? 'true' : 'false');
      if (t) {
        const tw = w ? tr('page.t.exit') : tr('page.t.walk');
        if (tWalk.textContent !== tw) { tWalk.textContent = tw; setTip(tWalk, w ? tr('page.t.exit.tip') : tr('page.btn.walk.tip')); }
        tJump.hidden = !w || fl || viewer.view === 'free';
        tFly.hidden = !(w && fly); setTxt(tFly, fl ? tr('page.t.land') : tr('page.t.fly')); tFly.setAttribute('aria-pressed', fl ? 'true' : 'false');
        tView.hidden = !w;
        const ch = CTL.chat; tChat.hidden = !(w && ch);
        if (ch) setTxt(tChat, ch.unread ? tr('page.t.chat.n', ch.unread) : tr('page.t.chat'));
        tPad.setAttribute('aria-pressed', VIS.pad ? 'true' : 'false');
        body.classList.toggle('chatOpen', !!(w && ch && ch.isOpen));
        if (w && !hint) { hint = true; toast(tr('page.touch.look')); }
        touchTops();
      } else body.classList.remove('chatOpen');
    };
    const apply = () => {
      const t = isTouch();
      if (t !== touchOn) {
        touchOn = t; CTL.touch = t; body.classList.toggle('touch', t);
        if (t && !folded0) { folded0 = true; for (const pn of [helpP, stateP, spawnP]) pn.foldTmp(); applySpawn(); applyHelp(viewer.walking); }
        if (!t) closeMenu();
      }
      const w = viewer.walking, show = !!VIS.pad;
      if (!show) for (const f of ends) f();
      body.classList.toggle('padOn', show);
      pad.hidden = !show; pw.hidden = !w; pg.hidden = w; stl.hidden = false;
      pb.hidden = t; pb.textContent = show ? tr('page.btn.pad') : tr('page.btn.pad.off'); pb.setAttribute('aria-pressed', show ? 'true' : 'false');
      cbn.hidden = w || show;   // vue globale : le centre du pavé recentre ; le bouton ne revient que si les flèches sont cachées
      tcol.hidden = !t;
      tick();
    };
    // la colonne de gauche tient dans l'écran : la hauteur de l'aide est limitée par la hauteur MESURÉE du reste de la colonne (Informations,
    // Arrivées, barre de boutons, qui passe sur plus de rangées quand les flèches sont affichées) ; aide hors de la colonne : ancienne règle
    const dockEl = document.getElementById('dock'), hudLc = document.getElementById('hudL');
    const dockRest = () => {
      if (wh.hidden || wh.parentElement !== hudLc) { if (rootSt.getPropertyValue('--dockRest')) rootSt.removeProperty('--dockRest'); return; }
      setVar('--dockRest', Math.max(0, dockEl.getBoundingClientRect().height - wh.getBoundingClientRect().height));
    };
    if (window.ResizeObserver) { const ro = new ResizeObserver(dockRest); ro.observe(dockEl); ro.observe(wh); }
    CTL.apply = apply; CTL.tick = () => { tick(); dockRest(); };
    if (coarse) { const f = () => apply(); if (coarse.addEventListener) coarse.addEventListener('change', f); else if (coarse.addListener) coarse.addListener(f); }
    apply();
  }
}
if (viewer.tiled) {
  // mode tuiles : ligne d'information (texte seul) dans le panneau d'aide s'il existe, indicateur « Chargement du sol… », message d'échec
  const info = document.getElementById('tilesInfo'), sb2 = document.getElementById('stateInfo');
  if (C.walk) { info.classList.remove('alone'); (document.getElementById('stateBody') || sb2).append(info); }
  const nb = (n, d) => i18nNum(n, d), tri = v => (v >= 1e6 ? nb(v / 1e6, 2) + ' M' : nb(v / 1e3, 0) + ' k');
  viewer.onTiles = s => {
    info.hidden = false;
    info.textContent = trn('page.tiles.main', s.loaded, s.total, nb(s.got / 1048576, 0), tri(s.tri))
      + (s.loading ? ' · ' + tr('page.tiles.loading', s.loading) : '') + (s.failed ? ' · ' + tr('page.tiles.failed', s.failed) : '')
      + (s.here && s.here.length ? '\n' + tr('page.tiles.here', s.here.join(', ')) : '')
      + (s.ov && s.ov.state === 'ready' ? '\n' + tr('page.tiles.ov', nb(s.ov.bytes / 1048576, 1), tri(s.ov.tri)) : '')
      + (s.ov && s.ov.state === 'failed' ? '\n' + tr('page.tiles.ov.failed') : '');
    lastWait = s.wait;
    if (!bootOn) { gw.hidden = !s.waiting; if (s.waiting) gw.textContent = waitText(s.wait); }
  };
  viewer.onTileError = (f, m) => toast(tr('page.tiles.error', f, m));
}
if (C.names) {
  const tag = document.getElementById('nameTag'); let tm = 0;
  viewer.pickOrbit = true;
  viewer.onPick = (info, cx, cy) => {
    clearTimeout(tm);
    if (!info) { tag.hidden = true; return; }
    tag.textContent = '';
    const b = document.createElement('b'); b.textContent = info.building || info.name || tr('page.pick.noname'); tag.appendChild(b);
    const extra = [info.name && !info.isRoot ? tr('page.pick.part', info.name) : '', info.materials.length ? tr('page.pick.material', info.materials.join(', ')) : ''].filter(Boolean).join(' · ');
    if (extra) { const d = document.createElement('div'); d.textContent = extra; tag.appendChild(d); }
    tag.hidden = false;
    tag.style.left = Math.max(8, Math.min(innerWidth - tag.offsetWidth - 8, cx + 12)) + 'px';
    tag.style.top = Math.max(8, Math.min(innerHeight - tag.offsetHeight - 8, cy + 12)) + 'px';
    tm = setTimeout(() => { tag.hidden = true; }, 7000);
  };
}
if (C.presenceUrl && C.walk && C.chat) {
  const chat = document.getElementById('chat'), log = document.getElementById('chatLog'), inp = document.getElementById('chatInput'), help = document.getElementById('chatHelp');
  const comp = document.getElementById('chatComplete'), saveBtn = document.getElementById('chatSave');
  const msgs = [];
  const baseTitle = document.title, ments = [];
  let unread = 0, ext = 0, olderOK = true, olderWait = 0, anchor = null, openChat = null;
  const saved = [];   // messages reçus ou envoyés depuis l'arrivée de ce visiteur (le serveur n'en garde pas ; l'historique rejoué à l'arrivée n'en fait pas partie)
  const render = () => {
    chat.hidden = !viewer.walking;
    const open = !inp.hidden, now = Date.now();
    const fade = (C.chatFade || 0) * 1000;
    const show = open ? msgs : (fade > 0 ? msgs.filter(x => now - x.t < fade) : msgs).slice(-6);
    const top0 = log.scrollTop, stick = !log.classList.contains('open') || log.scrollTop + log.clientHeight >= log.scrollHeight - 6;
    log.classList.toggle('open', open);
    log.textContent = ''; show.forEach(x => log.appendChild(x.el));
    if (anchor) { log.scrollTop = anchor.top + log.scrollHeight - anchor.h; anchor = null; } else if (open) log.scrollTop = stick ? log.scrollHeight : top0;
    olderBtn.hidden = !(open && olderOK && !olderWait && oldestN() !== undefined);
    mentBar.hidden = !ments.length;
    if (ments.length) document.getElementById('mentCount').textContent = trn('page.chat.mentions', ments.length);
    const st = viewer.getPresence().state;
    help.hidden = open;
    { const ct = document.getElementById('chatTouch'); if (ct) ct.hidden = !open || !document.body.classList.contains('touch'); }   // v46 : Envoyer et Fermer (écran tactile)
    CTL.tick();
    help.textContent = st === 'online' ? tr('page.chat.help') : ({ connecting: tr('page.chat.connecting'), error: tr('page.chat.error'), full: tr('page.chat.full') }[st] || tr('page.chat.offline'));
  };
  const olderBtn = document.getElementById('chatOlder'), mentBar = document.getElementById('chatMentions');
  const oldestN = () => { const x = msgs.find(q => q.n !== undefined); return x ? x.n : undefined; };
  const setTitle = () => { document.title = unread ? '(' + unread + ') ' + baseTitle : baseTitle; };
  const resetUnread = () => { if (unread) { unread = 0; setTitle(); } };
  document.addEventListener('visibilitychange', () => { if (!document.hidden && !inp.hidden) resetUnread(); });
  // v37 : messages plus anciens, par paquets de 50 ; un ancien serveur ne répond pas : le bouton se masque
  olderBtn.onclick = () => {
    const b = oldestN(); if (b === undefined || olderWait) return;
    if (!viewer.requestHistory(b, 50)) return;
    olderBtn.hidden = true;
    olderWait = setTimeout(() => { olderWait = 0; olderOK = false; render(); }, 4000);
  };
  chatTrim = () => { while (msgs.length > Math.max(VIS.histMax, ext)) msgs.shift(); render(); };
  const mkMsgEl = (m, hit) => {
    const el = document.createElement('div');
    if (hit && VIS.bold) { el.style.fontWeight = 'bold'; el.appendChild(document.createTextNode('@ ')); el.dataset.cite = '1'; }
    const b = document.createElement('b'); b.textContent = m.name + ' : '; el.appendChild(b); el.appendChild(document.createTextNode(m.text));
    return el;
  };
  viewer.onHistory = r => {
    if (olderWait) { clearTimeout(olderWait); olderWait = 0; }
    if (!r.more) olderOK = false;
    anchor = { top: log.scrollTop, h: log.scrollHeight };
    msgs.unshift(...r.msgs.map(m => ({ t: 0, el: mkMsgEl(m, false), n: m.n })));
    ext = Math.max(ext, msgs.length);
    render();
  };
  openChat = () => {
    if (!viewer.walking || !inp.hidden) return false;
    if (viewer.getPresence().state !== 'online') { viewer.onChat({ system: true, text: tr('page.chat.offline.sys') }); return false; }
    inp.hidden = false; viewer.releaseKeys(); inp.focus(); resetUnread(); render(); return true;
  };
  document.getElementById('mentGo').onclick = () => {
    const first = ments.find(e => e.isConnected) || null;
    openChat(); render();
    const f = ments.find(e => e.isConnected) || first;
    if (f) log.scrollTop = Math.max(0, f.offsetTop - log.clientHeight / 2);
    ments.length = 0; mentBar.hidden = true;
  };
  // pseudo cité : mot entier, sans tenir compte des majuscules, avec ou sans @ devant
  const cites = text => {
    const n = viewer.getName(); if (!n) return false;
    try { return new RegExp('(?<![\\p{L}\\p{N}_])@?' + n.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '(?![\\p{L}\\p{N}_])', 'iu').test(text); } catch (e) { return false; }
  };
  // v37 : la ligne d'un message qui me cite clignote (0,5 s visible, 0,5 s cachée) avec l'étiquette et la bulle de l'auteur, jusqu'à ma première action
  const blinkEls = new Set();
  viewer.onBlink = v => { for (const e of blinkEls) e.style.visibility = v ? '' : 'hidden'; };
  viewer.onBlinkEnd = () => { for (const e of blinkEls) e.style.visibility = ''; blinkEls.clear(); };
  viewer.onChat = m => {
    let el;
    if (m.system) { el = document.createElement('div'); el.className = 'sys'; el.textContent = m.text; }
    else {
      const hit = !m.self && !m.history && cites(m.text);
      el = mkMsgEl(m, hit);
      if (!m.history) saved.push({ t: new Date(), name: m.name, text: m.text });
      if (hit) { ments.push(el); if (VIS.blink) { viewer.blinkBubble(m.id); blinkEls.add(el); } if (VIS.soundCite) SND.cite(); }
      if (!m.self && !m.history && VIS.soundMsg && !(hit && VIS.soundCite) && (document.hidden || !document.hasFocus())) SND.msg();   // bip à chaque message quand la page n'a pas le focus (onglet caché ou autre fenêtre au premier plan), au plus un toutes les 2 s
      if (!m.self && !m.history && (document.hidden || inp.hidden)) { unread++; setTitle(); }
    }
    msgs.push({ t: m.history ? 0 : Date.now(), el, n: m.n });
    while (msgs.length > Math.max(VIS.histMax, ext)) msgs.shift();
    render();
  };
  // enregistrement du chat : fichier texte UTF-8 (avec BOM, lisible dans le Bloc-notes), heure locale, nom, texte ; tout reste dans le navigateur
  const p2 = n => String(n).padStart(2, '0');
  const fmtDate = d => p2(d.getDate()) + '/' + p2(d.getMonth() + 1) + '/' + d.getFullYear() + ' ' + p2(d.getHours()) + ':' + p2(d.getMinutes()) + ':' + p2(d.getSeconds());
  saveBtn.onclick = () => {
    const now = new Date();
    const lines = [tr('page.chat.file.head', C.room || '', fmtDate(now)), tr('page.chat.file.note'), '']
      .concat(saved.map(x => fmtDate(x.t) + ' | ' + x.name + ' | ' + x.text));
    const blob = new Blob(['﻿' + lines.join('\r\n') + '\r\n'], { type: 'text/plain;charset=utf-8' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
    a.download = 'chat_' + String(C.room || 'region').replace(/[^\w-]+/g, '_') + '_' + p2(now.getDate()) + '-' + p2(now.getMonth() + 1) + '-' + now.getFullYear() + '_' + p2(now.getHours()) + p2(now.getMinutes()) + p2(now.getSeconds()) + '.txt';
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    toast(trn('page.chat.saved', saved.length));
  };
  // complétion « @pseudo » : jusqu'à 5 visiteurs en ligne dont le pseudo commence par les lettres tapées après @
  const AT = /@([\p{L}\p{N}_#.-]*)$/u;
  let cItems = [], cSel = 0, cDismissed = null;
  const cOpen = () => !comp.hidden;
  const cHide = () => { comp.hidden = true; cItems = []; };
  const cDraw = () => {
    comp.textContent = '';
    cItems.forEach((n, i) => { const d = document.createElement('div'); d.setAttribute('role', 'option'); d.setAttribute('aria-selected', i === cSel ? 'true' : 'false'); d.textContent = (i === cSel ? '▶ ' : '   ') + n; d.onmousedown = e => { e.preventDefault(); cSel = i; cInsert(); }; comp.appendChild(d); });
  };
  const cUpdate = () => {
    const m = AT.exec(inp.value);
    if (!m || cDismissed === inp.value) { cHide(); return; }
    const pre = m[1].toLowerCase(), seen = new Set();
    cItems = viewer.getPresence().peers.map(p => p.name).filter(n => { if (!n || seen.has(n) || !n.toLowerCase().startsWith(pre)) return false; seen.add(n); return true; }).slice(0, 5);
    if (!cItems.length) { cHide(); return; }
    cSel = Math.min(cSel, cItems.length - 1); comp.hidden = false; cDraw();
  };
  const cInsert = () => { const n = cItems[cSel]; if (n === undefined) return; inp.value = inp.value.replace(AT, '@' + n + ' '); cHide(); inp.focus(); };
  const close = () => { inp.hidden = true; inp.value = ''; cHide(); cDismissed = null; inp.blur(); ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].forEach(c => viewer.holdKey(c, false)); render(); };
  addEventListener('keydown', e => {
    if ((e.code === 'Enter' || e.code === 'NumpadEnter') && viewer.walking && inp.hidden) { e.preventDefault(); openChat(); }
  });
  inp.addEventListener('keydown', e => {
    e.stopPropagation();
    if (cOpen()) {
      if (e.key === 'ArrowDown') { e.preventDefault(); cSel = (cSel + 1) % cItems.length; cDraw(); return; }
      if (e.key === 'ArrowUp') { e.preventDefault(); cSel = (cSel + cItems.length - 1) % cItems.length; cDraw(); return; }
      if (e.key === 'Tab' || e.key === 'Enter') { e.preventDefault(); cInsert(); return; }   // Entrée n'envoie pas tant que la liste est ouverte
      if (e.key === 'Escape') { e.preventDefault(); cDismissed = inp.value; cHide(); return; }   // ferme la liste, pas la saisie
    }
    if (e.key === 'Enter') { e.preventDefault(); const v = inp.value.trim(); if (v) viewer.sendChat(v); inp.value = ''; cHide(); cDismissed = null; }   // envoie ET garde la saisie ouverte
    else if (e.key === 'Escape') close();   // 1.1.9 : les flèches restent dans le texte (curseur) tant que la saisie est ouverte ; Échap la ferme et rend les flèches à la promenade
  });
  inp.addEventListener('keyup', e => { if (e.key.startsWith('Arrow')) viewer.holdKey(e.code, false); });
  inp.addEventListener('input', () => { cDismissed = null; cUpdate(); });
  inp.addEventListener('blur', () => { ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].forEach(c => viewer.holdKey(c, false)); });
  // v46 : écran tactile : le bouton « Chat » de la colonne ouvre la saisie (le clavier du téléphone s'ouvre) ; « Envoyer » et « Fermer » sous le champ
  {
    const ct = document.createElement('div'), bs = document.createElement('button'), bc = document.createElement('button');
    ct.id = 'chatTouch'; ct.hidden = true; bs.type = bc.type = 'button'; bs.id = 'chatSend'; bc.id = 'chatClose';
    bs.textContent = tr('page.chat.send'); bs.title = tr('page.chat.send.tip'); bc.textContent = tr('page.chat.close'); bc.title = tr('page.chat.close.tip');
    bs.onmousedown = e => e.preventDefault();   // le champ garde le focus (le clavier du téléphone reste ouvert)
    bs.onclick = () => { const v = inp.value.trim(); if (v) viewer.sendChat(v); inp.value = ''; cHide(); cDismissed = null; inp.focus(); };
    bc.onclick = () => close();
    ct.append(bs, bc); chat.append(ct);
  }
  CTL.chat = { open: () => !!(openChat && openChat()), get isOpen() { return !inp.hidden; }, get unread() { return unread; } };
  setInterval(render, 1000);
}
if (C.presenceUrl && C.walk) {
  const box = document.getElementById('presence'), st = document.getElementById('presenceStatus'), inp = document.getElementById('presenceName');
  box.hidden = false;
  try { inp.value = localStorage.getItem('glb2html_name') || ''; } catch (e) {}
  viewer.setName(inp.value);
  inp.onchange = () => { viewer.setName(inp.value); try { localStorage.setItem('glb2html_name', inp.value.trim()); } catch (e) {} };
  const T = { off: tr('page.pres.off'), connecting: tr('page.pres.connecting'), error: tr('page.pres.error', presUrl(C.presenceUrl)), full: tr('page.pres.full'), kicked: tr('page.pres.kicked'), banned: tr('page.pres.banned') };
  st.textContent = T.off;
  viewer.onPresence = s => {
    if (s.state === 'kicked' || s.state === 'banned') toast((s.state === 'banned' ? tr('page.pres.toast.banned') : tr('page.pres.toast.kicked')) + (s.reason ? ' : ' + s.reason : ''));
    const n = s.count;
    st.textContent = s.state === 'online' ? (s.spectator ? (n ? trn('page.pres.walking', n) : tr('page.pres.nobody')) : trn('page.pres.count', n)) : (s.state === 'error' && s.reason ? tr(s.stopped ? 'page.pres.error.stopped' : 'page.pres.error.why', presUrl(C.presenceUrl), s.reason) : s.state === 'refused' ? tr('page.pres.refused', s.reason) : (T[s.state] || s.state));
  };
  viewer.onName = n => {
    if (inp.value && inp.value !== n) toast(tr('page.pres.nametaken', n));
    inp.value = n; try { localStorage.setItem('glb2html_name', n); } catch (e) {}
  };
  if (C.spectate) { st.textContent = T.connecting; viewer.spectate(true); }
}
// 1.4.5 : panneau « À propos de la région » : ouverture à l'entrée (sauf « Ne plus afficher », mémorisé par région), touche ?, bouton de l'aide, case des réglages
const aboutOv = document.getElementById('aboutOverlay'), aboutBox = document.getElementById('aboutBox');
const aboutKey = () => 'web3d.about.hide.' + (ABOUT.name || 'x');
const aboutHidden = () => { try { return localStorage.getItem(aboutKey()) === '1'; } catch (e) { return false; } };   // stockage absent : le panneau s'affiche à chaque entrée
const aboutSetHidden = v => { try { if (v) localStorage.setItem(aboutKey(), '1'); else localStorage.removeItem(aboutKey()); } catch (e) {} };
let aboutOpt = null;
function aboutClose() { if (aboutOv.hidden) return; aboutOv.hidden = true; if (document.activeElement && aboutBox.contains(document.activeElement)) document.activeElement.blur(); }
function aboutOpen() {
  if (!ABOUT.found) return;
  if (document.pointerLockElement && document.exitPointerLock) document.exitPointerLock();
  document.getElementById('aboutTitle').textContent = ABOUT.title;
  document.getElementById('aboutText').textContent = ABOUT.text;   // jamais de HTML interprété
  aboutOv.hidden = false; aboutBox.focus();
}
function aboutToggle() { if (aboutOv.hidden) aboutOpen(); else aboutClose(); }
ABOUT.ready.then(() => {
  if (!ABOUT.found) return;
  document.getElementById('aboutClose').textContent = tr('page.about.close');
  document.getElementById('aboutHide').textContent = tr('page.about.hide');
  document.getElementById('aboutClose').onclick = aboutClose;
  document.getElementById('aboutHide').onclick = () => { aboutSetHidden(true); if (aboutOpt) aboutOpt.checked = false; aboutClose(); };
  aboutOv.addEventListener('click', e => { if (e.target === aboutOv) aboutClose(); });
  const opn = document.getElementById('optsPanel');
  if (opn) {   // case des réglages : cochée = le panneau s'ouvre à l'entrée
    const cb = document.createElement('input'), lb = document.createElement('label'), sp = document.createElement('span');
    cb.type = 'checkbox'; cb.id = 'aboutOpt'; cb.checked = !aboutHidden(); sp.textContent = tr('page.about.opt'); lb.append(cb, sp);
    cb.onchange = () => aboutSetHidden(!cb.checked);
    const note = document.getElementById('optsNote'); if (note && note.parentNode === opn) opn.insertBefore(lb, document.getElementById('laySec') || note); else opn.append(lb);
    aboutOpt = cb;
  }
  for (const f of KB.listeners) { try { f(); } catch (e) {} }   // redessine l'aide : ligne de la touche ? et bouton
});
addEventListener('keydown', e => {
  const n = e.target && e.target.tagName;
  if (e.key === 'Escape' && !aboutOv.hidden) { e.preventDefault(); aboutClose(); return; }
  // ? reconnue par le caractère imprimé : Maj + virgule (AZERTY) comme Maj + barre oblique (QWERTY) ; jamais pendant une saisie (le chat doit pouvoir écrire « ? »)
  if (e.key === '?' && ABOUT.found && !e.repeat && !e.ctrlKey && !e.metaKey && !e.altKey && n !== 'INPUT' && n !== 'TEXTAREA' && n !== 'SELECT') { e.preventDefault(); aboutToggle(); }
});
try {
  await viewer.loadBuffer(await b64ToBuffer(document.getElementById('glb').textContent.trim()));
  msg.remove();
  bootEnd();
  await arrive();
  await ABOUT.ready; if (ABOUT.found && !aboutHidden()) aboutOpen();   // à l'entrée, une fois le chargement terminé
} catch (e) {
  console.error(e);
  fade.classList.remove('on'); bootEnd(); gw.hidden = true;   // le message d'erreur ne reste jamais sous l'écran noir
  msg.textContent = tr('page.err.load', e && e.message ? e.message : e);
}
</script>
</body>
</html>
"""

DRACO_JS = r"""const { DRACOLoader } = await import('three/addons/loaders/DRACOLoader.js');
const dracoManager = new THREE.LoadingManager();
const DRACO_LIBS = __DRACO_LIBS__;
dracoManager.setURLModifier(u => DRACO_LIBS[u.split('/').pop()] || u);
const draco = new DRACOLoader(dracoManager);
draco.setDecoderPath('');
loader.setDRACOLoader(draco);"""

MESHOPT_JS = r"""const { MeshoptDecoder } = await import('three/addons/libs/meshopt_decoder.module.js');
loader.setMeshoptDecoder(MeshoptDecoder);"""


def build_cfg(name: str, *, rotate=ROTATE, hole=HOLE_RADIUS, hole_fade=HOLE_FADE, hole_x=HOLE_X, hole_z=HOLE_Z, wave=WAVE_AMP,
               sea_y=SEA_Y, zoom=ZOOM_RATIO, cam_dir=CAM_DIR, target=TARGET, sea_enabled=SEA_ENABLED,
               anim_enabled=ANIM_ENABLED, retina=RETINA_ENABLED, light=LIGHT_ENABLED, foliage_cutout=FOLIAGE_CUTOUT,
               sea_color=SEA_COLOR, sky_color=SKY_COLOR, sea_segments=SEA_SEGMENTS, walk=WALK_ENABLED, eye_height=EYE_HEIGHT, walk_speed=WALK_SPEED, walk_ignore=WALK_IGNORE, solid_materials=SOLID_MATERIALS, names=NAMES_ENABLED, presence_url=PRESENCE_URL, room=ROOM, chat=CHAT_ENABLED, chat_fade=CHAT_FADE, zones=None, profile=PROFILE, spectate=SPECTATE, panel=PANEL, zones_live=ZONES_LIVE, map_entries=None, map_url=MAP_URL, modular=False, zone_marker=ZONE_MARKER, show_spawns=SHOW_SPAWNS, zone_cone=ZONE_CONE, fly=FLY_ENABLED, zone_info_dist=ZONE_INFO_DIST, compass=COMPASS, north=NORTH_DEG, lib_url="", make_default=False, target_explicit=TARGET_EXPLICIT, tiles=None, tile_radius=TILE_RADIUS, tile_margin=TILE_MARGIN, tile_max_mo=TILE_MAX_MO, tile_max_tri=TILE_MAX_TRI, tile_concurrency=TILE_CONCURRENCY) -> dict:
    """Le dictionnaire de réglages `cfg` : identique dans la page autonome et dans <page>.config.json (mode modulaire),
    sauf que le mode modulaire garde les zones hors de la config (fichier <page>.zones.json, relu à chaque ouverture)."""
    presence_url = fix_presence_url(presence_url)
    cfg = {
        "rotate": clean_rotate(rotate), "hole": float(hole), "holeFade": float(hole_fade), "holeX": float(hole_x), "holeZ": float(hole_z), "wave": float(wave), "seaY": float(sea_y),
        "zoom": float(zoom), "camDir": list(map(float, cam_dir)), "target": list(map(float, target)),
        "sea": bool(sea_enabled), "anim": bool(anim_enabled), "retina": bool(retina), "light": bool(light),
        "foliageCutout": float(foliage_cutout), "seaSize": SEA_SIZE, "seaSegments": int(sea_segments),
        "seaColor": int(sea_color), "skyColor": int(sky_color),
        "walk": bool(walk), "eyeHeight": float(eye_height), "walkSpeed": float(walk_speed), "walkIgnore": str(walk_ignore), "solidMaterials": str(solid_materials),
        "names": bool(names), "chat": bool(chat), "profile": PROFILE_OLD.get(profile, profile), "version": VERSION, "panel": bool(panel), "zonesLive": str(zones_live or ""),
        "map": clean_map(json.loads(MAP_JSON) if map_entries is None else map_entries), "mapUrl": str(map_url or "")[:1200], "spectate": bool(presence_url) if spectate is None else bool(spectate),
        "zones": clean_zones(json.loads(ZONES_JSON) if zones is None else zones, profile), "chatFade": float(chat_fade), "presenceUrl": str(presence_url), "room": str(room) or pathlib.Path(name).stem,
        "zoneMarker": ZONE_MARKER_OLD.get(zone_marker, zone_marker) if ZONE_MARKER_OLD.get(zone_marker, zone_marker) in ZONE_MARKERS else "dot", "showSpawns": bool(show_spawns), "zoneCone": bool(zone_cone), "fly": bool(fly), "targetExplicit": bool(target_explicit),
        "zoneInfoDist": max(5.0, min(500.0, float(zone_info_dist))), "compass": bool(compass), "northDeg": float(north) % 360.0, "libUrl": str(lib_url or ""),
    }
    if modular:
        cfg["zones"], cfg["zonesLive"] = [], ""
    if tiles:
        # mode tuiles : clés présentes seulement dans ce cas (sans « tiles », la config est celle d'avant)
        cfg.update({"tiles": str(tiles), "tileRadius": float(tile_radius), "tileMargin": float(tile_margin), "tileMaxMB": float(tile_max_mo),
                    "tileMaxTriangles": int(tile_max_tri), "tileConcurrency": int(tile_concurrency)})
    return cfg


SHELL_BOOT_OLD = "const C = JSON.parse(document.getElementById('cfg').textContent);"
SHELL_MSG_OLD = '<div id="msg" data-i18n="page.loading">Chargement…</div>\n'
# script classique : depuis le disque, les modules sont bloqués par le navigateur et le module de la page ne s'exécute jamais
SHELL_MSG_NEW = SHELL_MSG_OLD + """<script>
if (location.protocol === 'file:') document.getElementById('msg').textContent = tr('page.shell.file', decodeURIComponent(location.pathname.split('/').pop()) + location.search);
</script>
"""
# la coquille ne contient aucun nom : X.html charge X.config.json, X.glb, X.zones.json (puis zones.json) du même dossier
SHELL_BOOT_NEW = r"""// fichiers frères : par défaut déduits du nom de la page (copier X.html en Y.html et ses frères en Y.* suffit) ;
// avec ?region=NOM, de NOM : une seule coquille peut servir plusieurs régions du même dossier
const BOOT = await (async () => {
  const fail = raison => { document.getElementById('msg').textContent = tr('page.shell.error', raison); throw new Error(raison); };
  // même règle que valid_region_name (gen_tpl.py), à garder identique : un nom simple = un seul nom de fichier ; dossier/nom ou a/b/nom = segments de lettres, chiffres,
  // point (pas au début), tiret, souligné, espace et parenthèses ; jamais « .. », « : », « \ », « ? », « # », ni chemin commençant par « / »
  const okRegion = nom => {
    if (!nom || nom.length > 200) return false;
    if (!nom.includes('/')) return !/[\/\\:?#\x00-\x1f]/.test(nom) && !nom.includes('..') && !nom.startsWith('.');
    return nom.split('/').every(s => /^[\p{L}\p{N}_()\- ][\p{L}\p{N}_()\- .]*$/u.test(s) && s.trim() !== '' && !s.includes('..'));
  };
  const clean = s => String(s || '').replace(/\.html?$/i, '');
  // fichiers de la région NOM (ou a/b/NOM) : tous relatifs au dossier de la région (dir) ; les zones se cherchent aussi dans zones.json de ce dossier
  const mk = nom => {
    const i = nom.lastIndexOf('/'), dir = i < 0 ? '' : nom.slice(0, i).split('/').map(encodeURIComponent).join('/') + '/', e = dir + encodeURIComponent(nom.slice(i + 1));
    return { dir, name: nom, config: e + '.config.json', glb: e + '.glb', zones: [e + '.zones.json', dir + 'zones.json'], about: e + '.about' };   // 1.4.5 : about = base de NOM.about.<langue>.txt et NOM.about.txt
  };
  const q = new URLSearchParams(location.search);
  if (q.has('region')) {
    // NOM ne peut être ni une adresse ni un chemin vers un dossier parent (aucune requête avant ce contrôle)
    const nom = clean(q.get('region'));
    if (!okRegion(nom)) fail(tr('page.shell.badregion', nom));
    return mk(nom);
  }
  // sans ?region= : (a) X.config.json du nom de la page ; (b) default.json {"region": "NOM"} ; (c) la première entrée de regions.json d'adresse relative ; (d) message
  let f = location.pathname.split('/').pop() || '';
  try { f = decodeURIComponent(f); } catch (x) {}
  const own = mk(clean(f) || 'index');
  const probe = async b => { try { const r = await fetch(b.config, { cache: 'no-store' }); if (r.ok) { b.res = r; return b; } } catch (x) {} return null; };
  const relRegion = u => {
    u = String(u || '');
    if (/^[a-z][a-z0-9+.\-]*:/i.test(u) || /^[\/\\]/.test(u)) return null;
    try { const nom = clean(new URL(u, 'http://x/').searchParams.get('region')); return okRegion(nom) ? nom : null; } catch (x) { return null; }
  };
  const a = await probe(own); if (a) return a;
  try {
    const r = await fetch('default.json', { cache: 'no-store' });
    if (r.ok) { const d = await r.json(); const nom = clean(d && d.region); if (okRegion(nom)) { const b = await probe(mk(nom)); if (b) return b; } }
  } catch (x) {}
  try {
    const r = await fetch('regions.json', { cache: 'no-store' });
    if (r.ok) {
      const d = await r.json(), liste = Array.isArray(d) ? d : (d && Array.isArray(d.regions) ? d.regions : []);
      for (const e of liste) { const nom = relRegion(e && e.url); if (nom) { const b = await probe(mk(nom)); if (b) return b; } }
    }
  } catch (x) {}
  document.getElementById('msg').textContent = tr('page.shell.noregion', own.config);
  throw new Error('region');
})();
const C = await (async () => {
  const fail = (nom, raison) => { document.getElementById('msg').textContent = tr('page.shell.notfound', nom, raison); throw new Error(nom + ' : ' + raison); };
  let r = BOOT.res;
  if (!r) {
    try { r = await fetch(BOOT.config, { cache: 'no-store' }); } catch (e) { fail(BOOT.config, tr('page.shell.network')); }
    if (!r.ok) fail(BOOT.config, 'HTTP ' + r.status);
  }
  const cfg = await r.json();
  cfg.imageBase = BOOT.dir || '';   // les images des zones « image » se cherchent dans le dossier de la région (à côté du .glb)
  if (cfg.tiles && BOOT.dir) cfg.tiles = BOOT.dir + cfg.tiles;   // région dans un sous-dossier : les chemins de la config sont relatifs à ce dossier
  // zones relues à chaque ouverture : X.zones.json, sinon zones.json du même dossier, sinon aucune
  cfg.zones = [];
  for (const nom of BOOT.zones) {
    try {
      const rz = await fetch(nom, { cache: 'no-store' }); if (!rz.ok) continue;
      const liste = await rz.json(); if (!Array.isArray(liste)) continue;
      cfg.zones = liste.filter(z => z && (cfg.profile === 'private' || cfg.profile === 'perso' || !z.private)); break;
    } catch (e) {}
  }
  return cfg;
})();
document.title = C.room || document.title;
{ const sky = '#' + (Number(C.skyColor) >>> 0).toString(16).padStart(6, '0'); document.documentElement.style.background = sky; document.body.style.background = sky; }"""
SHELL_CFG_TAG = '<script type="application/json" id="cfg">__CONFIG__</script>\n'
SHELL_GLB_TAG = '<script type="application/octet-stream" id="glb">__GLB_B64__</script>\n'
SHELL_LOAD_OLD = "await viewer.loadBuffer(await b64ToBuffer(document.getElementById('glb').textContent.trim()));"
SHELL_LOAD_NEW = """if (C.tiles) {
    // région en tuiles (X.tiles.json, voir docs/fr/MANUEL.md § 17 bis) : pas de X.glb ; ?radius=NNN remplace tileRadius (essais).
    // Arrivée demandée (lien #spawn= ou #pos=) : cadrage et chargement d'abord sur ce point. Sans lien, arrivée « default » si la région en a une
    // (sauf --target explicite) ; sinon la cible de la configuration. La page continue après 15 s même si la tuile n'est pas prête.
    const rayon = Number(new URLSearchParams(location.search).get('radius') || new URLSearchParams(location.search).get('rayon'));   // v43 : ?radius= ; l'ancien ?radius= reste lu
    const A = startPoint(), D = A ? null : defaultArrival(), at = A || (D && !keepTarget ? D : null);
    await viewer.loadTiles(C.tiles, { anchor: at ? at.pos : undefined, target: at ? at.pos : undefined, radius: rayon > 0 ? rayon : undefined });
  } else {
    const rGlb = await viewer.freshFetch(BOOT.glb);   // empreinte (HEAD), puis cache seulement si le .glb n'a pas change : un .glb remplace, plus vieux ou plus recent, s'affiche sans vider le cache
    if (!rGlb.ok) throw new Error(BOOT.glb + ' : HTTP ' + rGlb.status);
    await viewer.loadBuffer(await rGlb.arrayBuffer());
  }"""
SHELL_TITLE_OLD = "<title>__TITLE__</title>"
LIB_REL = "lib/three-" + THREE_VERSION
DRACO_PATH_OLD = "draco.setDecoderPath('');"
# v45 : la table d'import de la coquille est construite par un script classique (avant tout module) a partir d'UNE ligne, const LIB, modifiable a la main
SHELL_IMPORTMAP_OLD = '<script type="importmap">\n__IMPORTMAP__\n</script>'
SHELL_IMPORTMAP_NEW = """<script>
// LIB : dossier de lib (seule ligne a modifier) / folder of lib (the only line to edit)
const LIB = '__LIB__';
(function () {
  const F = __FILES__;
  const im = {};
  for (const k in F) im[k] = LIB + '/three-__THREE__/' + F[k];
  const s = document.createElement('script'); s.type = 'importmap'; s.textContent = JSON.stringify({ imports: im });
  document.head.appendChild(s);
})();
</script>"""
LIB_LINE_RE = re.compile(r"^const LIB = '([^'\r\n]*)';\r?$", re.M)
SHELL_SKY = "87ceeb"   # fond provisoire, remplacé par skyColor dès que la config est lue
# la coquille connaît tous les modules (Draco et Meshopt compris) : elle ne dépend d'aucun .glb
SHELL_MODULES = {**CORE_FILES, **DRACO_FILES, **MESHOPT_FILES}


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError(_tr("py.glb2html.gabarit_modulaire_cible_introuvable_ou_multi", old[:50]))
    return text.replace(old, new)


def lib_name(rel):
    return rel.rsplit("/", 1)[-1]


def write_atomic(path: pathlib.Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def write_modular_lib(out_dir: pathlib.Path, vendor_dir, lib_url=None):
    """Écrit lib/three-X/ à côté des pages (partagé par toutes les pages du dossier) : modules à plat, imports réécrits,
    Draco et Meshopt toujours présents (la coquille ne sait pas ce que contient le .glb). v37 : lib_url déplace le dossier (rien n'est écrit pour une adresse complète)."""
    lib = lib_dir_of(out_dir, lib_url)
    if lib is None:
        return
    for rel in SHELL_MODULES.values():
        write_atomic(lib / lib_name(rel), fix_imports(vendor_bytes(rel, vendor_dir)).encode("utf-8"))
    for rel in DRACO_LIBS.values():
        write_atomic(lib / "draco" / lib_name(rel), vendor_bytes(rel, vendor_dir))


def shell_lib_files():
    """Contenu attendu de lib/three-X/ pour le viewer : ({spécificateur: nom de fichier}, [fichiers de draco/])."""
    return {spec: lib_name(rel) for spec, rel in SHELL_MODULES.items()}, [lib_name(rel) for rel in DRACO_LIBS.values()]


def modular_names(out_path: pathlib.Path):
    """Fichiers frères de la page modulaire : (glb, config, zones)."""
    return out_path.with_suffix(".glb"), out_path.with_suffix(".config.json"), out_path.with_suffix(".zones.json")


DEFAULT_SHELL = "index.html"


def valid_region_name(name) -> bool:
    """Même règle que la coquille (?region=NOM), à garder identique au JS (okRegion dans SHELL_BOOT_NEW). Un nom simple : un seul nom de fichier, sans / \\ : ? # ni ..,
    sans point au début. v37, chemin descendant dossier/nom ou a/b/nom : chaque segment fait de lettres, chiffres, point (pas au début), tiret, souligné, espace et
    parenthèses ; jamais « .. », « : », « \\ », « ? », « # », ni chemin commençant par « / »."""
    name = re.sub(r"\.html?$", "", str(name or ""), flags=re.I)
    if "/" not in name:
        return bool(name) and not re.search(r"[/\\:?#\x00-\x1f]", name) and ".." not in name and not name.startswith(".")
    return len(name) <= 200 and all(re.fullmatch(r"[\w()\- ][\w()\- .]*", seg) is not None and seg.strip() != "" and ".." not in seg for seg in name.split("/"))


def shell_page_address(shell_name: str, region: str) -> str:
    """Adresse d'une région servie par une coquille commune : COQUILLE.html?region=NOM (le #spawn= s'ajoute après)."""
    return f"{shell_name}?region={urllib.parse.quote(region, safe='/')}"


class ShellRef(str):
    """Nom de la coquille commune (le texte), avec son dossier si --shared-shell a reçu un chemin (v37 : région dans un sous-dossier de la coquille)."""
    dir = None


def shell_file(shell, out_path: pathlib.Path) -> pathlib.Path:
    """Fichier de la coquille : dans le dossier donné par l'option, sinon à côté de la région."""
    return (shell.dir if getattr(shell, "dir", None) else out_path.parent) / str(shell)


def shell_dir_of(shell, out_path: pathlib.Path) -> pathlib.Path:
    return shell.dir if (shell is not None and getattr(shell, "dir", None)) else out_path.parent


def region_of(shell, out_path: pathlib.Path):
    """Nom de la région vu de la coquille : chemin de la page sans extension, relatif au dossier de la coquille (a/b/X) ; None si la page est ailleurs."""
    base = shell_dir_of(shell, out_path)
    try:
        return out_path.resolve().with_suffix("").relative_to(base.resolve()).as_posix()
    except ValueError:
        return None


def clean_lib_url(v):
    """--lib-url : chemin relatif (../lib) ou adresse http(s) complète ; rend (texte normalisé, est_distant) ou lève ValueError."""
    v = str(v or "").strip()
    if not v:
        return "", False
    if re.search(r"[\\?#\x00-\x1f\"'<>`]", v):
        raise ValueError(v)
    if re.match(r"https?://", v, re.I):
        return v.rstrip("/"), True
    if re.match(r"[a-zA-Z][a-zA-Z0-9+.\-]*:", v) or v.startswith(("/", "//")):
        raise ValueError(v)
    v = v.rstrip("/")
    return v, False


def lib_prefix(lib_url) -> str:
    """Début des adresses de la table d'import : ./lib par défaut (octet pour octet comme avant), ../lib, ./sous/lib, ou l'adresse complète."""
    v, remote = clean_lib_url(lib_url)
    v = urllib.parse.quote(v, safe="/:%@+=,()-._~")
    if not v:
        return "./lib"
    if remote or v.startswith("./") or v.startswith("../") or v in (".", ".."):
        return v
    return "./" + v


def lib_dir_of(shell_dir: pathlib.Path, lib_url):
    """Dossier lib/three-X/ à écrire (None si lib_url est une adresse complète : rien n'est copié)."""
    v, remote = clean_lib_url(lib_url)
    if remote:
        return None
    return shell_dir / (v or "lib") / ("three-" + THREE_VERSION)


def lib_from_shell(shell_path: pathlib.Path):
    """v45 : valeur de la ligne `const LIB = '...';` d'une coquille existante (texte tel qu'ecrit), ou None si le fichier est absent, sans cette ligne
    (coquille d'avant la v45) ou si la valeur est refusee par clean_lib_url."""
    try:
        m = LIB_LINE_RE.search(pathlib.Path(shell_path).read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError):
        return None
    if not m:
        return None
    try:
        clean_lib_url(m.group(1))
    except ValueError:
        return None
    return m.group(1)


def effective_lib_url(shell_path: pathlib.Path, lib_url, explicit):
    """v45 : dossier lib a utiliser. Ordre : --lib-url donne (explicit) ; la ligne const LIB d'une coquille existante si elle n'est pas le defaut ./lib ;
    lib_url (la config pour --update) ; sinon vide (= ./lib). Ainsi une coquille modifiee a la main garde son dossier."""
    if explicit:
        return lib_url
    cur = lib_from_shell(shell_path)
    if cur is not None and lib_prefix(cur) != "./lib":
        return cur
    return lib_url


def same_shell(existing: bytes, new: bytes) -> bool:
    """Meme coquille, a la fin de ligne pres (un editeur Windows peut enregistrer en CRLF)."""
    return existing.replace(b"\r\n", b"\n") == new


def lib_missing(out_dir: pathlib.Path, lib_url=None):
    """Fichiers de lib/three-X/ absents (la coquille commune et les pages déjà publiées les partagent)."""
    mods, draco = shell_lib_files()
    lib = lib_dir_of(out_dir, lib_url)
    if lib is None:
        return []
    return [str(lib / n) for n in list(mods.values()) + ["draco/" + n for n in draco] if not (lib / n).is_file()]


def build_shell(lib_url=None) -> str:
    """La coquille universelle du mode modulaire : même texte, octet pour octet, pour toutes les régions (le viewer en met
    une copie dans son .zip). Elle charge <nom de la page>.config.json / .glb / .zones.json du même dossier et lib/three-X/.
    Aucun nom, aucun titre, aucune couleur propre à une région n'y est écrit."""
    files = {spec: lib_name(rel) for spec, rel in SHELL_MODULES.items()}
    decoders = [replace_once(DRACO_JS.replace("__DRACO_LIBS__", "{}"), DRACO_PATH_OLD, "draco.setDecoderPath(LIB + '/three-" + THREE_VERSION + "/draco/');"), MESHOPT_JS]
    tpl = HTML_TEMPLATE
    tpl = replace_once(tpl, SHELL_IMPORTMAP_OLD, SHELL_IMPORTMAP_NEW.replace("__LIB__", lib_prefix(lib_url)).replace("__FILES__", json.dumps(files, indent=1)).replace("__THREE__", THREE_VERSION))
    tpl = replace_once(tpl, SHELL_TITLE_OLD, "<title>Chargement…</title>")
    tpl = replace_once(tpl, SHELL_MSG_OLD, SHELL_MSG_NEW)
    tpl = replace_once(tpl, SHELL_CFG_TAG, "")
    tpl = replace_once(tpl, SHELL_GLB_TAG, "")
    tpl = replace_once(tpl, SHELL_BOOT_OLD, SHELL_BOOT_NEW)
    tpl = replace_once(tpl, SHELL_LOAD_OLD, SHELL_LOAD_NEW)
    out = tpl.replace("__SKY_HEX__", SHELL_SKY).replace("__DECODERS__", "\n".join(decoders)).replace("__CORE_VERSION__", SHELL_VERSION)
    left = re.findall(r"__(?:TITLE|SKY_HEX|IMPORTMAP|CONFIG|DECODERS|GLB_B64|CORE|CORE_VERSION)__", out)
    if left:
        raise RuntimeError(_tr("py.glb2html.coquille_modulaire_marqueur_s_non_remplace", sorted(set(left))))
    return out


def build_html(glb: bytes, name: str, vendor_dir=None, **kw) -> str:
    """Page autonome : GLB en base64, three.js et décodeurs en data:, s'ouvre depuis le disque. (La page modulaire est build_shell.)
    Les réglages kw sont ceux de build_cfg + title."""
    title = kw.pop("title", None)
    cfg = build_cfg(name, **kw)
    hole, wave, sea_y, zoom, sky_color = cfg["hole"], cfg["wave"], cfg["seaY"], cfg["zoom"], cfg["skyColor"]
    used = inspect_glb(glb, name)
    need_draco = "KHR_draco_mesh_compression" in used
    need_meshopt = "EXT_meshopt_compression" in used

    modules = dict(CORE_FILES)
    if need_draco:
        modules.update(DRACO_FILES)
    if need_meshopt:
        modules.update(MESHOPT_FILES)
    importmap = {"imports": {spec: js_data_url(vendor_bytes(rel, vendor_dir)) for spec, rel in modules.items()}}

    decoders = []
    if need_draco:
        libs = {
            "draco_wasm_wrapper.js": bin_data_url(vendor_bytes(DRACO_LIBS["draco_wasm_wrapper.js"], vendor_dir), "text/javascript"),
            "draco_decoder.wasm": bin_data_url(vendor_bytes(DRACO_LIBS["draco_decoder.wasm"], vendor_dir), "application/wasm"),
        }
        decoders.append(DRACO_JS.replace("__DRACO_LIBS__", json.dumps(libs)))
    if need_meshopt:
        decoders.append(MESHOPT_JS)

    title = title or f"{pathlib.Path(name).stem} - trou {hole:g} amp {wave:g} y {sea_y:g} zoom {zoom:.2f}"
    out = (HTML_TEMPLATE
           .replace("__TITLE__", html.escape(title))
           .replace("__SKY_HEX__", f"{int(sky_color):06x}")
           .replace("__IMPORTMAP__", json.dumps(importmap, indent=1))
           .replace("__CONFIG__", json.dumps(cfg).replace("</", "<\\/"))
           .replace("__DECODERS__", "\n".join(decoders))
           .replace("__CORE_VERSION__", VERSION))
    # GLB injecté en dernier : rien n'est rescanné dans les Mo de base64
    return out.replace("__GLB_B64__", base64.b64encode(glb).decode("ascii"))


def live_zones_name(out_path, zones_live):
    return out_path.stem + ".zones.json" if zones_live == "auto" else str(zones_live or "")


def write_live_zones(out_path, kw):
    """Écrit à côté de la page le fichier de zones rechargeable (filtré selon le profil : le profil public n'y met jamais de zone privée)."""
    name = live_zones_name(out_path, kw.get("zones_live"))
    if not name:
        return
    zones = kw.get("zones")
    zones = clean_zones(json.loads(ZONES_JSON) if zones is None else zones, kw.get("profile", PROFILE))
    target = out_path.with_name(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(zones, ensure_ascii=False, indent=1), encoding="utf-8")
    print(_tr("py.glb2html.zones_0_zone_s_profil_1", len(zones), kw.get('profile', PROFILE), target))


def zones_given(kw):
    """Vrai si une source de zones a été donnée (--zones, --settings ou ZONES_JSON du script exporté par le viewer)."""
    return kw.get("zones") is not None or bool(json.loads(ZONES_JSON))


def write_modular_zones(zones_path: pathlib.Path, kw):
    """Écrit <page>.zones.json (zones nettoyées, filtrées selon le profil), relu par la page à chaque ouverture."""
    profile = kw.get("profile", PROFILE)
    zones = clean_zones(json.loads(ZONES_JSON) if kw.get("zones") is None else kw["zones"], profile)
    write_atomic(zones_path, json.dumps(zones, ensure_ascii=False, indent=1).encode("utf-8"))
    print(_tr("py.glb2html.zones_0_zone_s_profil_1", len(zones), profile, zones_path))


def write_default_json(shell_dir: pathlib.Path, region: str, force=False):
    """v37 : default.json {"region": NOM} à côté de la coquille = région ouverte quand l'adresse n'a pas de ?region=. Écrit la première fois, ou avec --default."""
    path = shell_dir / "default.json"
    if path.is_file() and not force:
        return
    write_atomic(path, (json.dumps({"region": region}, ensure_ascii=False) + "\n").encode("utf-8"))
    print(_tr("py.glb2html.default_json_ecrit", path, region))


def write_shell_page(out_path: pathlib.Path, shell, page: str):
    """Écrit la coquille : X.html (modulaire simple) ou COQUILLE.html à côté de la région, jamais écrasée si elle existe et diffère."""
    if shell:
        shell_path = shell_file(shell, out_path)
        if not shell_path.is_file():
            write_atomic(shell_path, page.encode("utf-8"))
            print(_tr("py.glb2html.coquille_0_ecrite", shell_path))
        elif same_shell(shell_path.read_bytes(), page.encode("utf-8")):
            print(_tr("py.glb2html.coquille_0_deja_presente_et_identique", shell_path))
        else:
            print(_tr("py.glb2html.avertissement_0_existe_et_differe_de", shell_path), file=sys.stderr)
    else:
        write_atomic(out_path, page.encode("utf-8"))


def generate(glb_path: pathlib.Path, out_path: pathlib.Path, vendor_dir, modular=False, shell=None, **kw):
    """shell : nom de la coquille commune (COQUILLE.html). Alors out_path désigne la région (NOM = son nom sans extension) :
    seuls NOM.glb, NOM.config.json et NOM.zones.json sont écrits, plus la coquille et lib/ s'ils sont absents."""
    data = glb_path.read_bytes()
    make_default = kw.pop("make_default", False)
    rname = out_path.stem
    if shell:
        modular = True
        rname = region_of(shell, out_path)
        if rname is None or not valid_region_name(rname):
            print(_tr("py.glb2html.erreur_nom_de_region_0_refuse", rname or out_path.stem), file=sys.stderr)
            return False
    if modular:
        if kw.get("title"):
            print(_tr("py.glb2html.avertissement_title_est_ignore_en_mode"), file=sys.stderr)
        if kw.get("zones_live"):
            print(_tr("py.glb2html.avertissement_zones_live_est_ignore_en"), file=sys.stderr)
        kw = dict(kw, zones_live="")
        kw = dict(kw, lib_url=effective_lib_url(shell_file(shell, out_path) if shell else out_path, kw.get("lib_url") or "", bool(kw.get("lib_url"))))
    elif kw.get("zones_live"):
        kw = dict(kw, zones_live=live_zones_name(out_path, kw["zones_live"]))
    try:
        inspect_glb(data, glb_path.name)   # valide le GLB (ValueError sinon)
        page = build_shell(kw.get("lib_url")) if modular else build_html(data, glb_path.name, vendor_dir, **kw)
    except ValueError as e:
        print(_tr("py.glb2html.erreur_0", e), file=sys.stderr)
        return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if modular:
        glb_out, cfg_out, zones_out = modular_names(out_path)
        if not shell or lib_missing(shell_dir_of(shell, out_path), kw.get("lib_url")):
            write_modular_lib(shell_dir_of(shell, out_path), vendor_dir, kw.get("lib_url"))
        write_atomic(glb_out, data)
        write_config(cfg_out, glb_path.name, kw)
        # sans source de zones, un X.zones.json existant (peut-être modifié à la main) n'est pas écrasé
        if zones_given(kw) or not zones_out.is_file():
            write_modular_zones(zones_out, kw)
    write_shell_page(out_path, shell, page)
    if shell:
        write_default_json(shell_dir_of(shell, out_path), rname, make_default)
    if not modular:
        write_live_zones(out_path, dict(kw, zones_live=kw.get("zones_live") or ""))
    if shell:
        print(_tr("py.glb2html.ok_0_1_2_3_coquille", glb_path.name, glb_out.name, cfg_out.name, zones_out.name, shell, shell_page_address(shell, rname), VERSION))
    elif modular:
        print(_tr("py.glb2html.ok_0_1_modulaire_coquille_2", glb_path.name, out_path, len(page) / 1024, glb_out.name, len(data) / 2**20, cfg_out.name, zones_out.name, lib_prefix(kw.get("lib_url")).lstrip("./") + "/three-" + THREE_VERSION, VERSION))
    else:
        print(_tr("py.glb2html.ok_0_1_2_2f_mo", glb_path.name, out_path, len(data) / 2**20, len(page) / 2**20, VERSION))
    return True


def safe_rel_path(p) -> bool:
    """Même règle que la coquille (safeRel) pour un chemin de tuile : relatif, sans .., sans : ? # \\, sans segment vide."""
    p = str(p or "")
    return bool(p) and len(p) < 400 and not re.match(r"[/\\]", p) and not re.search(r"[\\:?#\x00-\x1f]", p) and not any(x in ("", "..") for x in p.split("/"))


def read_tiles_index(path: pathlib.Path):
    """Lit X.tiles.json (écrit par glb2tiles.py) ; arrête avec un message clair si le fichier n'est pas utilisable."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        sys.exit(_tr("py.glb2html.erreur_0_illisible_1", path, e))
    tiles = doc.get("tiles") if isinstance(doc, dict) else None
    if not isinstance(tiles, list) or not tiles:
        sys.exit(_tr("py.glb2html.erreur_0_liste_tiles_absente_ou", path))
    for t in tiles:
        ok = isinstance(t, dict) and safe_rel_path(t.get("file")) and str(t["file"]).lower().endswith(".glb")
        for k in ("min", "max"):
            ok = ok and isinstance(t.get(k), list) and len(t[k]) == 3 and all(isinstance(v, (int, float)) and math.isfinite(v) for v in t[k])
        if not ok:
            sys.exit(_tr("py.glb2html.erreur_0_entree_de_tuile_invalide", path, str(t)[:120]))
    ov = doc.get("overview")
    if ov is not None and not (isinstance(ov, dict) and safe_rel_path(ov.get("file")) and str(ov["file"]).lower().endswith(".glb")):
        sys.exit(_tr("py.glb2html.erreur_0_overview_invalide_1_file", path, str(ov)[:120]))
    return doc


def tiles_default_target(doc, rotate=0):
    """Cible de caméra par défaut en mode tuiles : centre de l'étendue en X,Z (repère déjà tourné), hauteur 20 m bornée à l'étendue."""
    lo = [min(t["min"][k] for t in doc["tiles"]) for k in range(3)]
    hi = [max(t["max"][k] for t in doc["tiles"]) for k in range(3)]
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    a = math.radians(clean_rotate(rotate))
    return (round(cx * math.cos(a) + cz * math.sin(a), 2), round(min(max(20.0, lo[1]), hi[1]), 2), round(-cx * math.sin(a) + cz * math.cos(a), 2))


def place_tiles(tiles_path: pathlib.Path, doc, page_dir: pathlib.Path):
    """Met X.tiles.json, ses tuiles et sa vue d'ensemble à côté de la page. Rien n'est copié si elles y sont déjà (une région fait plus d'un Go) ;
    sinon copie, fichier par fichier, ce qui manque ou a une autre taille. Rend le chemin relatif de X.tiles.json depuis la page."""
    src, dst = tiles_path.resolve().parent, page_dir.resolve()
    files = [t["file"] for t in doc["tiles"]]
    ov = doc.get("overview")
    ov_file = ov["file"] if isinstance(ov, dict) else None
    absent = [f for f in files if not (src / f).is_file()]
    if absent:
        print(_tr("py.glb2html.avertissement_0_tuile_s_listee_s", len(absent), tiles_path.name, absent[0]), file=sys.stderr)
    if ov_file and not (src / ov_file).is_file():
        print(_tr("py.glb2html.avertissement_vue_d_ensemble_0_introuvable", ov_file, tiles_path.name), file=sys.stderr)
    ov_txt = _tr("py.glb2html.vue_d_ensemble_0_placee_avec", ov_file) if ov_file else ""
    if src == dst:
        print(_tr("py.glb2html.tuiles_0_tuile_s_et_1", len(files), tiles_path.name, ov_txt))
        return tiles_path.name
    copied = same = size = 0
    for f in files + ([ov_file] if ov_file else []):
        a, b = src / f, dst / f
        if not a.is_file():
            continue
        if b.is_file() and b.stat().st_size == a.stat().st_size:
            same += 1 if f != ov_file else 0
            continue
        b.parent.mkdir(parents=True, exist_ok=True)
        tmp = b.with_name(b.name + ".tmp")
        shutil.copyfile(a, tmp)
        tmp.replace(b)
        if f != ov_file:
            copied += 1
        size += a.stat().st_size
    write_atomic(dst / tiles_path.name, tiles_path.read_bytes())
    print(_tr("py.glb2html.tuiles_0_copie_dans_1_tuiles", tiles_path.name, dst, copied, size / 2**20, same, ov_txt))
    return tiles_path.name


def generate_tiles(tiles_path: pathlib.Path, doc, out_path: pathlib.Path, vendor_dir, shell=None, **kw):
    """Région en tuiles : comme generate() en mode modulaire, mais sans .glb : écrit X.config.json (champ « tiles »), X.zones.json,
    la coquille et lib/ ; X.tiles.json et ses tuiles ne sont copiés que s'ils ne sont pas déjà à côté de la page."""
    make_default = kw.pop("make_default", False)
    rname = out_path.stem
    if shell:
        rname = region_of(shell, out_path)
        if rname is None or not valid_region_name(rname):
            print(_tr("py.glb2html.erreur_nom_de_region_0_refuse", rname or out_path.stem), file=sys.stderr)
            return False
    if kw.get("title"):
        print(_tr("py.glb2html.avertissement_title_est_ignore_en_mode"), file=sys.stderr)
    if kw.get("zones_live"):
        print(_tr("py.glb2html.avertissement_zones_live_est_ignore_en"), file=sys.stderr)
    kw = dict(kw, zones_live="")
    page = build_shell(kw.get("lib_url"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    kw["tiles"] = place_tiles(tiles_path, doc, out_path.parent)
    zones_keep = kw.pop("zones_keep", False)   # --zones désigne déjà X.zones.json de destination : jamais réécrit
    _, cfg_out, zones_out = modular_names(out_path)
    if not shell or lib_missing(shell_dir_of(shell, out_path), kw.get("lib_url")):
        write_modular_lib(shell_dir_of(shell, out_path), vendor_dir, kw.get("lib_url"))
    write_config(cfg_out, out_path.stem, kw)
    if (zones_given(kw) and not zones_keep) or not zones_out.is_file():
        write_modular_zones(zones_out, kw)
    write_shell_page(out_path, shell, page)
    if shell:
        write_default_json(shell_dir_of(shell, out_path), rname, make_default)
    n = len(doc["tiles"])
    if any(z.get("mesh") for z in clean_zones(json.loads(ZONES_JSON) if kw.get("zones") is None else kw["zones"], kw.get("profile", PROFILE))):
        if doc.get("nodeRefs"):
            print(_tr("py.glb2html.tuiles_des_zones_sont_liees_a"))
        else:
            print(_tr("py.glb2html.avertissement_des_zones_sont_liees_a", tiles_path.name), file=sys.stderr)
    adr = shell_page_address(shell, rname) if shell else out_path.name
    print(_tr("py.glb2html.ok_0_tuile_s_1_2", n, cfg_out.name, zones_out.name) + (_tr("py.glb2html.coquille_commune_0_adresse_1", shell, adr) if shell else _tr("py.glb2html.shell_name", out_path.name)) + f" [glb2html {VERSION}]")
    return True


def write_config(cfg_path: pathlib.Path, name: str, kw):
    """Écrit <page>.config.json = le dictionnaire cfg de la page modulaire (carte comprise, zones exclues), JSON sans BOM."""
    cfg = build_cfg(name, **{k: v for k, v in kw.items() if k != "title"}, modular=True)
    write_atomic(cfg_path, json.dumps(cfg, ensure_ascii=False, indent=1).encode("utf-8"))
    return cfg


# --update : option de la ligne de commande (dest argparse) -> clés de la config qu'elle remplace. Les autres clés de la config existante sont gardées telles quelles.
MAJ_KEYS = {
    "rotate": ("rotate",), "hole": ("hole",), "hole_fade": ("holeFade",), "hole_x": ("holeX",), "hole_z": ("holeZ",), "wave": ("wave",), "sea_y": ("seaY",),
    "zoom": ("zoom",), "cam_dir": ("camDir",), "target": ("target", "targetExplicit"), "foliage_cutout": ("foliageCutout",), "sea_color": ("seaColor",),
    "sky_color": ("skyColor",), "sea_segments": ("seaSegments",), "walk": ("walk",), "eye_height": ("eyeHeight",), "walk_speed": ("walkSpeed",),
    "walk_ignore": ("walkIgnore",), "solid_materials": ("solidMaterials",), "names": ("names",), "presence_url": ("presenceUrl",), "chat": ("chat",), "chat_fade": ("chatFade",), "profile": ("profile",),
    "spectate": ("spectate",), "panel": ("panel",), "map_url": ("mapUrl",), "room": ("room",), "sea_enabled": ("sea",), "anim_enabled": ("anim",), "retina": ("retina",), "light": ("light",),
    "zone_marker": ("zoneMarker",), "show_spawns": ("showSpawns",), "zone_cone": ("zoneCone",), "fly": ("fly",), "zone_info_dist": ("zoneInfoDist",), "compass": ("compass",), "north": ("northDeg",), "lib_url": ("libUrl",), "tile_radius": ("tileRadius",), "tile_margin": ("tileMargin",),
    "tile_max_mo": ("tileMaxMB",), "tile_max_tri": ("tileMaxTriangles",), "tile_concurrency": ("tileConcurrency",), "tiles": ("tiles",),
    "map": ("map",), "register": ("map",),
}


def explicit_dests(ap):
    """Options réellement données sur la ligne de commande (et non remplies par leur valeur par défaut) : on relit la ligne avec des défauts « absents"."""
    saved = [(act, act.default) for act in ap._actions]
    saved_def = dict(ap._defaults)
    try:
        for act in ap._actions:
            act.default = argparse.SUPPRESS
        ap._defaults.clear()
        return set(vars(ap.parse_args()))
    finally:
        for act, d in saved:
            act.default = d
        ap._defaults.update(saved_def)


def merge_maj_cfg(old: dict, new: dict, explicit) -> tuple:
    """Config existante + seulement les clés des options explicites ; la version est toujours celle du script. Rend (config, [(clé, ancienne, nouvelle)])."""
    out = dict(old)
    changes = []
    keys = []
    for d in explicit:
        keys += list(MAJ_KEYS.get(d, ()))
    if "presenceUrl" in keys and "spectate" not in keys:
        keys.append("spectate")   # sans --spectate explicite, la vue globale suit l'adresse de présence (comme à la génération)
    for k in keys:
        if k in new and old.get(k) != new[k]:
            changes.append((k, old.get(k), new[k]))
            out[k] = new[k]
    if old.get("version") != VERSION:
        changes.append(("version", old.get("version"), VERSION))
    out["version"] = VERSION
    out.pop("zones", None)
    out["zones"] = []
    return out, changes


def renew_shell(shell_path: pathlib.Path, page: str):
    """--update : écrit la coquille de cette version si elle est absente ou différente (l'ancienne est gardée sous un nom daté). Rend un texte pour le compte rendu."""
    new = page.encode("utf-8")
    if not shell_path.is_file():
        write_atomic(shell_path, new)
        return _tr("py.glb2html.coquille_0_absente_ecrite", shell_path.name)
    if same_shell(shell_path.read_bytes(), new):
        return _tr("py.glb2html.coquille_0_deja_a_jour_identique", shell_path.name, VERSION)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    bak = shell_path.with_name(f"{shell_path.stem}.avant-{stamp}{shell_path.suffix}")
    shutil.copyfile(shell_path, bak)
    write_atomic(shell_path, new)
    return (_tr("py.glb2html.coquille_0_plus_ancienne_que_1", shell_path.name, VERSION, bak.name))


def run_maj(a, kw, explicit, S_reg):
    """glb2html.py --update : met à jour une région déjà générée en mode modulaire. N'applique que les options données, garde le reste de X.config.json
    et X.zones.json (réécrit seulement avec --zones), écrit la version courante et renouvelle la coquille si elle est plus ancienne."""
    if not a.output:
        sys.exit(_tr("py.glb2html.erreur_maj_demande_o_region_html"))
    out = pathlib.Path(a.output)
    if out.is_dir() or str(a.output).endswith(("/", "\\")):
        sys.exit(_tr("py.glb2html.erreur_avec_maj_o_designe_la"))
    if not out.suffix:
        out = out.with_suffix(".html")
    glb_out, cfg_out, zones_out = modular_names(out)
    if not cfg_out.is_file():
        cmd = "glb2html.py " + ("--tiles X.tiles.json" if a.tiles else "X.glb") + f" -o {out.name}" + (f" --shared-shell {a.shared_shell}" if a.shared_shell else "") + " [options]"
        sys.exit(_tr("py.glb2html.erreur_maj_0_introuvable_la_region", cfg_out, cmd))
    try:
        old = json.loads(cfg_out.read_text(encoding="utf-8-sig"))
        if not isinstance(old, dict):
            raise ValueError(_tr("py.glb2html.ce_n_est_pas_un_objet"))
    except (OSError, ValueError) as e:
        sys.exit(_tr("py.glb2html.erreur_0_illisible_1", cfg_out, e))
    shell_path = shell_file(a.shared_shell, out) if a.shared_shell else out
    rname = out.stem
    if not a.shared_shell and not out.is_file():
        sys.exit(_tr("py.glb2html.erreur_maj_0_introuvable_si_la", out, DEFAULT_SHELL))
    if a.shared_shell:
        rname = region_of(a.shared_shell, out)
        if rname is None or not valid_region_name(rname):
            sys.exit(_tr("py.glb2html.erreur_nom_de_region_0_refuse_2", rname or out.stem))
    kw.pop("make_default", None)
    if a.input and a.tiles:
        sys.exit(_tr("py.glb2html.erreur_tiles_remplace_le_glb_ne"))
    explicit = set(explicit) - {"input", "output", "maj", "vendor", "shared_shell", "modular", "config_only", "zones_only", "zones_live", "title", "zones", "map_page", "thumb", "default",
                                  "region_name", "region_url", "region_xy", "region_spawn"}
    kw.update(tile_radius=clamp(a.tile_radius, 10, 5000), tile_margin=clamp(a.tile_margin, 0, 5000), tile_max_mo=clamp(a.tile_max_mo, 1, 100000),
              tile_max_tri=int(clamp(a.tile_max_tri, 1000, 10**9)), tile_concurrency=int(clamp(a.tile_concurrency, 1, 16)))
    if "room" not in explicit:
        kw["room"] = str(old.get("room") or "")
    if "lib_url" not in explicit:
        kw["lib_url"] = str(old.get("libUrl") or "")   # v37 : le choix du dossier lib est retenu dans la config
    cfg_lib = kw["lib_url"]
    kw["lib_url"] = effective_lib_url(shell_path, cfg_lib, "lib_url" in explicit)   # v45 : la ligne const LIB de la coquille existante (modifiee a la main) l'emporte sur la config
    if kw["lib_url"] != cfg_lib:
        explicit.add("lib_url")
        print(_tr("py.glb2html.maj_lib_repris", kw["lib_url"]))
    tdoc = None
    if a.tiles:
        tp = find_beside(a.tiles)
        if tp is None:
            sys.exit(_tr("py.glb2html.erreur_0_introuvable_cherche_dans_1", a.tiles, pathlib.Path.cwd(), pathlib.Path(__file__).resolve().parent))
        tdoc = read_tiles_index(tp)
        kw["tiles"] = place_tiles(tp, tdoc, out.parent)
        explicit.add("tiles")
    if a.register:
        a2 = argparse.Namespace(**vars(a))
        a2.presence_url = a.presence_url or old.get("presenceUrl") or ""
        if a2.thumb and not re.match(r"^https?://", str(a2.thumb), re.I) and page_path(a2.thumb, out.parent).is_file():
            a2.thumb = str(page_path(a2.thumb, out.parent))
        entry = region_entry(a2, S_reg, kw["room"] or out.stem, out.stem, page_name_of(a, out))
        reg = page_path(a.register, out.parent)
        kw["map_entries"] = register_region(reg, entry)
        print(_tr("py.glb2html.carte_0_ajoutee_ou_mise_a", entry['name'], reg, len(map_regions(kw['map_entries']))))
        explicit.add("register")
    elif a.map:
        explicit.add("map")
    elif a.region_name or a.region_url or a.region_xy or a.region_spawn or a.thumb:
        print(_tr("py.glb2html.avertissement_region_name_region_url_region"), file=sys.stderr)
    if not a.register and not a.map and "map" not in explicit:
        kw["map_entries"] = old.get("map") if isinstance(old.get("map"), list) else []
    new = build_cfg(out.stem, **{k: v for k, v in kw.items() if k != "title"}, modular=True)
    cfg, changes = merge_maj_cfg(old, new, explicit)
    if a.input:
        inp = pathlib.Path(a.input)
        if not inp.is_file():
            sys.exit(_tr("py.glb2html.0_introuvable", inp))
        try:
            inspect_glb(inp.read_bytes(), inp.name)
        except ValueError as e:
            sys.exit(_tr("py.glb2html.erreur_0", e))
        write_atomic(glb_out, inp.read_bytes())
        print(_tr("py.glb2html.maj_0_remplace_par_1", glb_out.name, inp.name))
    elif not a.tiles and not old.get("tiles") and not glb_out.is_file():
        print(_tr("py.glb2html.avertissement_0_introuvable_a_cote_de", glb_out.name), file=sys.stderr)
    write_atomic(cfg_out, json.dumps(cfg, ensure_ascii=False, indent=1).encode("utf-8"))
    print(_tr("py.glb2html.maj_0_mis_a_jour_glb2html", cfg_out.name, VERSION) + (_tr("py.glb2html.0_cle_s_changee_s", len(changes)) if changes else _tr("py.glb2html.aucune_cle_changee")) + _tr("py.glb2html.0_gardee_s_telle_s_quelle", len(old) - len([c for c in changes if c[0] in old])))
    for k, o, n in changes:
        print(f"  {k} : {json.dumps(o, ensure_ascii=False)[:80]} -> {json.dumps(n, ensure_ascii=False)[:80]}")
    if "profile" in explicit:
        print(_tr("py.glb2html.maj_le_profil_ne_filtre_les"))
    if a.zones:
        zf = find_beside(a.zones)
        if zf is None:
            sys.exit(_tr("py.glb2html.erreur_0_introuvable", a.zones))
        try:
            kw["zones"] = json.loads(zf.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as e:
            sys.exit(_tr("py.glb2html.erreur_0_illisible_1", zf, e))
        if zones_out.is_file() and zf.resolve() == zones_out.resolve():
            print(_tr("py.glb2html.zones_zones_deja_en_place_0", zones_out))
        else:
            write_modular_zones(zones_out, kw)
    else:
        print(_tr("py.glb2html.maj_0_conserve_tel_quel", zones_out.name) + ("" if zones_out.is_file() else _tr("py.glb2html.absent_paren")))
    lib_url = kw.get("lib_url") or ""
    libtxt = lib_prefix(lib_url).lstrip("./") + "/three-" + THREE_VERSION
    print("[update] " + renew_shell(shell_path, build_shell(lib_url)))
    sdir = shell_dir_of(a.shared_shell, out) if a.shared_shell else out.parent
    if lib_missing(sdir, lib_url):
        write_modular_lib(sdir, a.vendor, lib_url)
        print(_tr("py.glb2html.maj_0_absent_ou_incomplet_ecrit", libtxt))
    else:
        print(_tr("py.glb2html.maj_0_present_conserve", libtxt))
    if a.shared_shell and a.default:   # --update n'écrase jamais default.json sans --default
        write_default_json(sdir, rname, True)
    if a.map_page:
        entries = cfg.get("map") or []
        if clean_map(entries):
            mp = pathlib.Path(a.map_page)
            write_map_page(mp if mp.is_absolute() else out.parent / mp, entries, cfg.get("presenceUrl", ""), cfg.get("mapUrl", ""), a.title or _tr("py.glb2html.carte_des_mondes"))
        else:
            print(_tr("py.glb2html.avertissement_map_page_ignore_aucune_region"), file=sys.stderr)
    if a.register or a.map_page or a.thumb or a.map:
        print(_tr("py.glb2html.carte_avec_maj_les_chemins_relatifs", out.parent.resolve()))
    adr = shell_page_address(a.shared_shell, rname) if a.shared_shell else out.name
    print(_tr("py.glb2html.ok_region_mise_a_jour_adresse", adr, VERSION))
    sys.exit(0)


def vec3(s: str):
    v = tuple(float(x) for x in s.split(","))
    if len(v) != 3:
        raise argparse.ArgumentTypeError(_tr("py.glb2html.format_attendu_x_y_z"))
    return v


def hexcolor(s: str) -> int:
    return int(s.lstrip("#"), 16)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def region_entry(a, S_reg, room, stem, page_name):
    """Fiche de région pour --register avec page (options --region-* > fichier de réglages > défauts)."""
    use_reg = bool(S_reg.get("name") and S_reg.get("url"))
    entry = {"id": _slug(room) or "region", "name": a.region_name or (S_reg.get("name") if use_reg else "") or stem,
             "url": a.region_url or (S_reg.get("url") if use_reg else "") or page_name, "room": room,
             "spawn": a.region_spawn or ((S_reg.get("spawn") if use_reg and S_reg.get("spawn") != "default" else None)) or None,
             "thumb": thumb_data_url(a.thumb) if a.thumb else (S_reg.get("thumb") if use_reg and str(S_reg.get("thumb") or "").startswith("data:image/") else ""),
             "presence": fix_presence_url(a.presence_url) if a.presence_url else None}
    if not a.region_xy and use_reg:
        try:
            entry["x"], entry["y"] = int(S_reg.get("x", 0)), int(S_reg.get("y", 0))
        except (TypeError, ValueError):
            pass
    if a.region_xy:
        try:
            x, y = (int(float(v)) for v in a.region_xy.split(","))
            entry["x"], entry["y"] = x, y
        except ValueError:
            sys.exit(_tr("py.glb2html.erreur_region_xy_attend_deux_nombres"))
    return entry


def page_name_of(a, out):
    """Adresse relative de la région pour la carte : la page elle-même, ou COQUILLE.html?region=NOM avec une coquille commune."""
    return shell_page_address(a.shared_shell, region_of(a.shared_shell, out) or out.stem) if a.shared_shell else out.name


def main():
    ap = argparse.ArgumentParser(description=_tr("py.glb2html.desc", VERSION), epilog=_tr("py.glb2html.epilog"), formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False)
    i18n_add_common(ap)
    ap.add_argument("--version", action="version", version=f"glb2html {VERSION}", help=_tr("py.common.version"))
    ap.add_argument("input", nargs="?", help=_tr("py.glb2html.fichier_glb_ou_dossier_de_glb"))
    ap.add_argument("--zones-live", nargs="?", const="auto", default=(ZONES_LIVE or None), metavar="NAME", help=_tr("py.glb2html.la_page_recharge_ses_zones_a"))
    ap.add_argument("--zones-only", action="store_true", help=_tr("py.glb2html.reecrit_seulement_les_zones_sans_regenerer"))
    ap.add_argument("-o", "--output", help=_tr("py.glb2html.sortie_fichier_html_ou_dossier_cree"))
    ap.add_argument("--rotate", type=int, choices=(0, 90, 180, 270), default=ROTATE, help=_tr("py.glb2html.rotation_de_la_region_autour_de"))
    ap.add_argument("--hole", type=float, default=HOLE_RADIUS, help=_tr("py.glb2html.rayon_du_trou_30_600_zone"))
    ap.add_argument("--hole-fade", type=float, default=HOLE_FADE, help=_tr("py.glb2html.demi_largeur_du_fondu_du_trou"))
    ap.add_argument("--hole-x", type=float, default=HOLE_X, help=_tr("py.glb2html.position_x_du_centre_du_trou"))
    ap.add_argument("--hole-z", type=float, default=HOLE_Z, help=_tr("py.glb2html.position_z_du_centre_du_trou"))
    ap.add_argument("--wave", type=float, default=WAVE_AMP, help=_tr("py.glb2html.amplitude_vagues_0_10"))
    ap.add_argument("--sea-y", type=float, default=SEA_Y, help=_tr("py.glb2html.hauteur_mer_150_60"))
    ap.add_argument("--zoom", type=float, default=ZOOM_RATIO, help=_tr("py.glb2html.ratio_de_cadrage_1_cadrage_auto"))
    ap.add_argument("--cam-dir", type=vec3, default=CAM_DIR, help=_tr("py.glb2html.direction_camera_x_y_z"))
    ap.add_argument("--target", type=vec3, default=TARGET, help=_tr("py.glb2html.cible_camera_x_y_z"))
    ap.add_argument("--foliage-cutout", type=float, default=FOLIAGE_CUTOUT, help=_tr("py.glb2html.seuil_alpha_feuillage_0_0_5"))
    ap.add_argument("--sea-color", type=hexcolor, default=SEA_COLOR, help=_tr("py.glb2html.couleur_mer_ex_3a9ad9"))
    ap.add_argument("--sky-color", type=hexcolor, default=SKY_COLOR, help=_tr("py.glb2html.couleur_ciel_ex_87ceeb"))
    ap.add_argument("--sea-segments", type=int, default=SEA_SEGMENTS, help=_tr("py.glb2html.finesse_du_maillage_de_la_mer"))
    ap.add_argument("--walk", action=argparse.BooleanOptionalAction, default=WALK_ENABLED, help=_tr("py.glb2html.inclure_le_mode_promenade_touche_f"))
    ap.add_argument("--eye-height", type=float, default=EYE_HEIGHT, help=_tr("py.glb2html.hauteur_des_yeux_en_m_promenade"))
    ap.add_argument("--walk-speed", type=float, default=WALK_SPEED, help=_tr("py.glb2html.vitesse_de_marche_en_m_s"))
    ap.add_argument("--walk-ignore", default=WALK_IGNORE, help=_tr("py.glb2html.noms_a_ignorer_en_collision_separes"))
    ap.add_argument("--solid-materials", default=SOLID_MATERIALS, help=_tr("py.glb2html.materiaux_rendus_opaques"))
    ap.add_argument("--names", action=argparse.BooleanOptionalAction, default=NAMES_ENABLED, help=_tr("py.glb2html.afficher_le_nom_de_l_element"))
    ap.add_argument("--presence-url", default=PRESENCE_URL, help=_tr("py.glb2html.serveur_de_presence_ws_ou_wss"))
    ap.add_argument("--chat", action=argparse.BooleanOptionalAction, default=CHAT_ENABLED, help=_tr("py.glb2html.chat_entre_visiteurs_necessite_presence_url"))
    ap.add_argument("--chat-fade", type=float, default=CHAT_FADE, help=_tr("py.glb2html.secondes_avant_disparition_des_messages_et"))
    ap.add_argument("--zones", type=pathlib.Path, help=_tr("py.glb2html.fichier_json_de_zones_exporte_par"))
    ap.add_argument("--profile", type=lambda v: PROFILE_OLD.get(v, v), choices=("public", "private"), default=PROFILE, help=_tr("py.glb2html.public_retire_les_zones_privees_ex"))
    ap.add_argument("--spectate", action=argparse.BooleanOptionalAction, default=SPECTATE, help=_tr("py.glb2html.voir_les_visiteurs_en_promenade_depuis"))
    ap.add_argument("--panel", action=argparse.BooleanOptionalAction, default=PANEL, help=_tr("py.glb2html.panneau_de_reglages_pour_les_visiteurs"))
    ap.add_argument("--map", type=pathlib.Path, help=_tr("py.glb2html.fichier_regions_json_carte_des_mondes"))
    ap.add_argument("--map-url", default=MAP_URL, help=_tr("py.glb2html.adresse_s_de_regions_json_partage"))
    ap.add_argument("--register", help=_tr("py.glb2html.fichier_regions_json_a_mettre_a"))
    ap.add_argument("--scan-sites", metavar="FOLDER", help=_tr("py.glb2html.scan.help"))
    ap.add_argument("--dry-run", action="store_true", help=_tr("py.glb2html.scan.dryhelp"))
    ap.add_argument("--region-name", help=_tr("py.glb2html.nom_affiche_dans_la_carte_defaut"))
    ap.add_argument("--region-url", help=_tr("py.glb2html.adresse_de_la_page_de_cette"))
    ap.add_argument("--region-xy", metavar="X,Y", help=_tr("py.glb2html.position_sur_la_grille_comme_opensim"))
    ap.add_argument("--region-spawn", help=_tr("py.glb2html.identifiant_du_point_d_arrivee_des"))
    ap.add_argument("--thumb", help=_tr("py.glb2html.vignette_de_la_region_fichier_jpg"))
    ap.add_argument("--map-page", metavar="FILE.html", help=_tr("py.glb2html.genere_aussi_une_page_web_carte"))
    ap.add_argument("--settings", nargs="?", const="auto", default=None, metavar="FILE", help=_tr("py.glb2html.reprend_tous_les_reglages_enregistres_par"))
    ap.add_argument("--modular", action="store_true", help=_tr("py.glb2html.mode_modulaire_ecrit_une_coquille_page"))
    ap.add_argument("--shared-shell", nargs="?", const=DEFAULT_SHELL, default=None, metavar="SHELL.html", help=_tr("py.glb2html.mode_modulaire_a_coquille_commune_une", DEFAULT_SHELL))
    ap.add_argument("--tiles", type=pathlib.Path, metavar="X.tiles.json", help=_tr("py.glb2html.region_decoupee_en_tuiles_par_glb2tiles"))
    ap.add_argument("--tile-radius", type=float, default=TILE_RADIUS, help=_tr("py.glb2html.m_charger_les_tuiles_dont_la"))
    ap.add_argument("--tile-margin", type=float, default=TILE_MARGIN, help=_tr("py.glb2html.m_decharger_les_tuiles_au_dela"))
    ap.add_argument("--tile-max-mb", metavar="TILE_MAX_MB", dest="tile_max_mo", type=float, default=TILE_MAX_MO, help=_tr("py.glb2html.mo_de_tuiles_chargees_en_meme"))
    ap.add_argument("--tile-max-triangles", metavar="TILE_MAX_TRIANGLES", dest="tile_max_tri", type=int, default=TILE_MAX_TRI, help=_tr("py.glb2html.triangles_de_tuiles_chargees_en_meme"))
    ap.add_argument("--tile-concurrency", type=int, default=TILE_CONCURRENCY, help=_tr("py.glb2html.telechargements_simultanes_defaut_default_d"))
    ap.add_argument("--config-only", action="store_true", help=_tr("py.glb2html.reecrit_seulement_page_config_json_d"))
    ap.add_argument("--zone-marker", type=lambda v: ZONE_MARKER_OLD.get(v, v), choices=ZONE_MARKERS, default=ZONE_MARKER, help=_tr("py.glb2html.marqueur_des_portails_et_zones_libres"))
    ap.add_argument("--zone-cone", action=argparse.BooleanOptionalAction, default=ZONE_CONE, help=_tr("py.glb2html.petit_cone_pointe_vers_le_bas"))
    ap.add_argument("--show-spawns", action=argparse.BooleanOptionalAction, default=SHOW_SPAWNS, help=_tr("py.glb2html.dessine_aussi_les_arrivees_dans_la"))
    ap.add_argument("--zone-info-dist", type=float, default=ZONE_INFO_DIST, metavar="M", help=_tr("py.glb2html.distance_5_a_200_m_defaut"))
    ap.add_argument("--lib-url", default="", metavar="PATH", help=_tr("py.glb2html.lib_url"))
    ap.add_argument("--default", action="store_true", help=_tr("py.glb2html.default_region"))
    ap.add_argument("--compass", action=argparse.BooleanOptionalAction, default=COMPASS, help=_tr("py.glb2html.compass"))
    ap.add_argument("--north", type=float, default=NORTH_DEG, metavar="DEGREES", help=_tr("py.glb2html.north"))
    ap.add_argument("--fly", action=argparse.BooleanOptionalAction, default=FLY_ENABLED, help=_tr("py.glb2html.vol_en_promenade_touche_f_ou"))
    ap.add_argument("--update", dest="maj", action="store_true", help=_tr("py.glb2html.met_a_jour_une_region_deja"))
    ap.add_argument("--room", default=ROOM, help=_tr("py.glb2html.salon_de_presence_defaut_nom_du"))
    ap.add_argument("--sea", metavar="SEA", dest="sea_enabled", action=argparse.BooleanOptionalAction, default=SEA_ENABLED, help=_tr("py.glb2html.help.sea"))
    ap.add_argument("--anim", metavar="ANIM", dest="anim_enabled", action=argparse.BooleanOptionalAction, default=ANIM_ENABLED, help=_tr("py.glb2html.help.anim"))
    ap.add_argument("--retina", action=argparse.BooleanOptionalAction, default=RETINA_ENABLED, help=_tr("py.glb2html.haute_resolution_rendu_x2_minimum_supersampl"))
    ap.add_argument("--light", action=argparse.BooleanOptionalAction, default=LIGHT_ENABLED, help=_tr("py.glb2html.help.light"))
    ap.add_argument("--title", help=_tr("py.glb2html.titre_de_la_page"))
    ap.add_argument("--vendor", type=pathlib.Path, help=_tr("py.glb2html.racine_d_un_paquet_npm_three"))
    a = ap.parse_args()
    S = {}
    if a.maj and a.settings:
        sys.exit(_tr("py.glb2html.erreur_maj_et_settings_s_excluent"))
    if a.settings:
        if str(a.settings).lower().endswith((".glb", ".gltf")) and not a.input:
            a.input, a.settings = a.settings, "auto"
        if a.settings == "auto":
            if not a.input:
                sys.exit(_tr("py.glb2html.erreur_settings_sans_nom_demande_le"))
            wanted = pathlib.Path(a.input).stem + ".reglages.json"
        else:
            wanted = a.settings
        sp = find_beside(wanted)
        if sp is None:
            sys.exit(_tr("py.glb2html.erreur_fichier_de_reglages_0_introuvable", wanted, pathlib.Path.cwd(), pathlib.Path(__file__).resolve().parent))
        try:
            S = json.loads(sp.read_text(encoding="utf-8"))
            if not isinstance(S, dict) or not isinstance(S.get("cfg"), dict):
                raise ValueError(_tr("py.glb2html.ce_n_est_pas_un_fichier"))
        except (OSError, ValueError) as e:
            sys.exit(_tr("py.glb2html.erreur_0_illisible_1", sp, e))
        defaults = settings_defaults(S)
        ap.set_defaults(**defaults)
        keep_input = a.input
        a = ap.parse_args()
        if str(a.settings).lower().endswith((".glb", ".gltf")) and not a.input:
            a.input, a.settings = a.settings, "auto"
        if not a.input:
            a.input = keep_input
        print(_tr("py.glb2html.reglages_0_parametre_s_repris_de", len(defaults), sp))
    if a.shared_shell:
        raw = str(a.shared_shell)
        sp = pathlib.PurePath(raw.replace("\\", "/"))
        if not sp.name.lower().endswith((".html", ".htm")):
            sys.exit(_tr("py.glb2html.erreur_shared_shell_attend_un_nom", raw))
        a.shared_shell = ShellRef(sp.name)
        if "/" in raw.replace("\\", "/"):
            a.shared_shell.dir = pathlib.Path(raw).parent   # v37 : --shared-shell DOSSIER/index.html, régions en sous-dossiers
        a.modular = True
    try:
        clean_lib_url(a.lib_url)
    except ValueError:
        sys.exit(_tr("py.glb2html.erreur_lib_url_refuse", a.lib_url))
    if a.default and not a.shared_shell:
        print(_tr("py.glb2html.avertissement_default_ignore_sans_shared_shell"), file=sys.stderr)
    S_reg = S.get("thisReg") if isinstance(S.get("thisReg"), dict) else {}
    S_cmd = S.get("cmd") if isinstance(S.get("cmd"), dict) else {}
    if S and not a.output and S_cmd.get("dest"):
        a.output = S_cmd["dest"]
    if S and not a.map_page and S_cmd.get("mapPage"):
        a.map_page = S_cmd["mapPage"]

    map_arg = None
    if a.map and a.maj and a.output and not pathlib.Path(a.map).is_absolute() and page_path(a.map, pathlib.Path(a.output).parent).is_file():
        a.map = str(page_path(a.map, pathlib.Path(a.output).parent))   # --update : chemin relatif = relatif au dossier de la page
    if a.map:
        mf = find_beside(a.map)
        if mf is None:
            sys.exit(_tr("py.glb2html.erreur_0_introuvable_cherche_dans_1", a.map, pathlib.Path.cwd(), pathlib.Path(__file__).resolve().parent))
        try:
            map_arg = json.loads(mf.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            sys.exit(_tr("py.glb2html.erreur_0_illisible_1", mf, e))
        print(_tr("py.glb2html.carte_0_region_s_lue_s", len(clean_map(map_arg)), mf))
    zones_arg = S.get("zones") if (S and not a.zones and isinstance(S.get("zones"), list)) else None
    if a.zones:
        zf = find_beside(a.zones)
        if zf is None:
            sys.exit(_tr("py.glb2html.erreur_0_introuvable_cherche_dans_1", a.zones, pathlib.Path.cwd(), pathlib.Path(__file__).resolve().parent))
        try:
            zones_arg = json.loads(zf.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            sys.exit(_tr("py.glb2html.erreur_0_illisible_1", zf, e))
        print(_tr("py.glb2html.zones_0_zone_s_lue_s", len(zones_arg) if isinstance(zones_arg, list) else 0, zf))

    kw = dict(rotate=a.rotate, hole=clamp(a.hole, 30, 600), hole_fade=max(0.0, a.hole_fade), hole_x=a.hole_x, hole_z=a.hole_z, wave=clamp(a.wave, 0, 10),
              sea_y=clamp(a.sea_y, -150, 60), zoom=clamp(a.zoom, 0.05, 100), cam_dir=a.cam_dir, target=a.target,
              foliage_cutout=clamp(a.foliage_cutout, 0, 1), sea_color=a.sea_color, sky_color=a.sky_color, sea_segments=int(clamp(a.sea_segments, 8, 1000)), walk=a.walk, walk_ignore=a.walk_ignore, solid_materials=a.solid_materials, zones_live=a.zones_live or "", map_entries=map_arg, map_url=a.map_url, names=a.names, presence_url=a.presence_url, room=a.room, chat=a.chat, chat_fade=clamp(a.chat_fade, 0, 3600), zones=zones_arg, profile=a.profile, spectate=a.spectate, panel=a.panel, eye_height=clamp(a.eye_height, 0.3, 5), walk_speed=clamp(a.walk_speed, 0.5, 30),
              sea_enabled=a.sea_enabled, anim_enabled=a.anim_enabled, retina=a.retina, light=a.light, title=a.title,
              zone_marker=a.zone_marker, show_spawns=a.show_spawns, zone_cone=a.zone_cone, fly=a.fly, zone_info_dist=clamp(a.zone_info_dist, 5, 500), compass=a.compass, north=a.north, lib_url=clean_lib_url(a.lib_url)[0], make_default=a.default,
              target_explicit=bool(tuple(a.target) != tuple(TARGET) or TARGET_EXPLICIT or getattr(a, "target_explicit", False)))

    if a.maj:
        run_maj(a, kw, explicit_dests(ap), S_reg)
    if a.zones_live and not a.input and str(a.zones_live).lower().endswith((".glb", ".gltf")):
        a.input, a.zones_live = a.zones_live, "auto"
        kw["zones_live"] = "auto"
    if a.output:   # les images des zones « image » se cherchent a cote de la page, comme imageBase au chargement
        _o = pathlib.Path(a.output)
        IMG_DIR[0] = (_o if _o.is_dir() else _o.parent).resolve()
    if a.zones_only:
        if not a.output:
            sys.exit(_tr("py.glb2html.erreur_zones_only_demande_o_page"))
        out = pathlib.Path(a.output)
        if a.zones_live:   # page autonome qui recharge ses zones
            write_live_zones(out, dict(kw, zones_live=a.zones_live))
            sys.exit(0)
        if not out.suffix:
            out = out.with_suffix(".html")
        if not (modular_names(out)[1].is_file() or a.modular):
            sys.exit(_tr("py.glb2html.erreur_zones_only_demande_zones_live", modular_names(out)[1].name))
        if zones_arg is None:
            sys.exit(_tr("py.glb2html.erreur_zones_only_demande_zones_fichier"))
        write_modular_zones(modular_names(out)[2], kw)
        sys.exit(0)
    if a.config_only and not a.tiles:
        if not a.output:
            sys.exit(_tr("py.glb2html.erreur_config_only_demande_o_page"))
        out = pathlib.Path(a.output)
        if not out.suffix:
            out = out.with_suffix(".html")
        glb_out, cfg_out, zones_out = modular_names(out)
        if a.shared_shell:
            if not glb_out.is_file() or not shell_file(a.shared_shell, out).is_file():
                sys.exit(_tr("py.glb2html.erreur_0_ou_1_introuvable_genere", a.shared_shell, glb_out.name))
        elif not out.is_file() or not glb_out.is_file():
            sys.exit(_tr("py.glb2html.erreur_0_ou_1_introuvable_genere_2", out, glb_out.name))
        name = pathlib.Path(a.input).name if a.input else glb_out.name
        if not a.room and cfg_out.is_file():
            try:
                kw["room"] = str(json.loads(cfg_out.read_text(encoding="utf-8")).get("room") or "")
            except (OSError, ValueError):
                pass
        if a.register:
            entry = region_entry(a, S_reg, kw["room"] or pathlib.Path(name).stem, pathlib.Path(name).stem, page_name_of(a, out))
            reg = data_path(a.register)
            kw["map_entries"] = register_region(reg, entry)
            print(_tr("py.glb2html.carte_0_ajoutee_ou_mise_a", entry['name'], reg, len(map_regions(kw['map_entries']))))
            where_note(reg, a.output)
        write_config(cfg_out, name, kw)
        print(_tr("py.glb2html.ok_reglages_0_coquille_et_glb", cfg_out, VERSION))
        if a.zones:   # les zones ne sont touchées que si --zones est donné
            write_modular_zones(zones_out, kw)
        else:
            print(_tr("py.glb2html.zones_0_non_modifie_donne_zones", zones_out.name))
        if a.map_page and kw.get("map_entries") is not None and clean_map(kw["map_entries"]):
            mp = pathlib.Path(a.map_page)
            write_map_page(mp if mp.is_absolute() else out.parent / mp, kw["map_entries"], kw.get("presence_url", ""), kw.get("map_url", ""), a.title or _tr("py.glb2html.carte_des_mondes"))
        sys.exit(0)
    if a.tiles:
        if a.input:
            sys.exit(_tr("py.glb2html.erreur_tiles_remplace_le_glb_ne"))
        if not a.output:
            sys.exit(_tr("py.glb2html.erreur_tiles_demande_o_region_html"))
        out = pathlib.Path(a.output)
        if out.is_dir() or str(a.output).endswith(("/", "\\")):
            sys.exit(_tr("py.glb2html.erreur_avec_tiles_o_designe_la"))
        if not out.suffix:
            out = out.with_suffix(".html")
        tp = find_beside(a.tiles)
        if tp is None:
            sys.exit(_tr("py.glb2html.erreur_0_introuvable_cherche_dans_1", a.tiles, pathlib.Path.cwd(), pathlib.Path(__file__).resolve().parent))
        tdoc = read_tiles_index(tp)
        if a.target == TARGET:
            kw["target"] = tiles_default_target(tdoc, a.rotate)
            print(_tr("py.glb2html.tuiles_cible_de_camera_par_defaut", kw['target']))
        if a.sea_y == SEA_Y:
            kw["sea_y"] = 20.0
            print(_tr("py.glb2html.tuiles_hauteur_de_la_mer_par"))
        kw.update(tile_radius=clamp(a.tile_radius, 10, 5000), tile_margin=clamp(a.tile_margin, 0, 5000), tile_max_mo=clamp(a.tile_max_mo, 1, 100000),
                  tile_max_tri=int(clamp(a.tile_max_tri, 1000, 10**9)), tile_concurrency=int(clamp(a.tile_concurrency, 1, 16)))
        if a.shared_shell and not valid_region_name(region_of(a.shared_shell, out) or ""):
            sys.exit(_tr("py.glb2html.erreur_nom_de_region_0_refuse_3", region_of(a.shared_shell, out) or out.stem))
        if a.register:
            entry = region_entry(a, S_reg, a.room or out.stem, out.stem, page_name_of(a, out))
            reg = data_path(a.register)
            kw["map_entries"] = register_region(reg, entry)
            print(_tr("py.glb2html.carte_0_ajoutee_ou_mise_a", entry['name'], reg, len(map_regions(kw['map_entries']))))
            where_note(reg, a.output)
        if a.zones and zf is not None:
            zdest = modular_names(out)[2]
            if zdest.is_file() and zf.resolve() == zdest.resolve():
                kw["zones_keep"] = True
                print(_tr("py.glb2html.zones_zones_deja_en_place_0_2", zdest))
        ok = generate_tiles(tp, tdoc, out, a.vendor, shell=a.shared_shell, **kw)
        if ok and a.map_page:
            entries = kw["map_entries"] if kw.get("map_entries") is not None else json.loads(MAP_JSON)
            if clean_map(entries):
                mp = pathlib.Path(a.map_page)
                write_map_page(mp if mp.is_absolute() else out.parent / mp, entries, kw.get("presence_url", ""), kw.get("map_url", ""), a.title or _tr("py.glb2html.carte_des_mondes"))
            else:
                print(_tr("py.glb2html.avertissement_map_page_ignore_aucune_region_2"), file=sys.stderr)
        sys.exit(0 if ok else 1)
    if a.scan_sites and not a.input:   # v49 : mise à jour de regions.json depuis le dossier des sites
        scan_sites(a.scan_sites, a.dry_run)
        sys.exit(0)
    if a.register and not a.input:
        if not (a.region_name and a.region_url and a.room):
            sys.exit(_tr("py.glb2html.erreur_enregistrer_une_region_sans_glb"))
        entry = {"id": _slug(a.room) or "region", "name": a.region_name, "url": a.region_url, "room": a.room,
                 "spawn": a.region_spawn or None, "thumb": thumb_data_url(a.thumb) if a.thumb else "",
                 "presence": fix_presence_url(a.presence_url) if a.presence_url else None}
        if a.region_xy:
            try:
                x, y = (int(float(v)) for v in a.region_xy.split(","))
                entry["x"], entry["y"] = x, y
            except ValueError:
                sys.exit(_tr("py.glb2html.erreur_region_xy_attend_deux_nombres"))
        reg = data_path(a.register)
        data = register_region(reg, entry)
        print(_tr("py.glb2html.carte_0_ajoutee_ou_mise_a", entry['name'], reg, len(map_regions(data))))
        if a.map_page:
            write_map_page(pathlib.Path(a.map_page), data, a.presence_url, a.map_url, a.title or _tr("py.glb2html.carte_des_mondes"))
        sys.exit(0)
    if a.map_page and not a.input:
        entries = map_arg if map_arg is not None else json.loads(MAP_JSON)
        if not clean_map(entries):
            sys.exit(_tr("py.glb2html.erreur_aucune_region_a_afficher_donne"))
        write_map_page(pathlib.Path(a.map_page), entries, a.presence_url, a.map_url, a.title or _tr("py.glb2html.carte_des_mondes"))
        sys.exit(0)
    if not a.input:
        ap.error(_tr("py.glb2html.le_fichier_glb_ou_le_dossier"))
    inp = pathlib.Path(a.input)
    if inp.is_dir() and (a.register or a.map_page):
        print(_tr("py.glb2html.avertissement_register_et_map_page_ne"), file=sys.stderr)
    if inp.is_dir():
        files = sorted(p for p in inp.iterdir() if p.suffix.lower() == ".glb")
        if not files:
            sys.exit(_tr("py.glb2html.aucun_glb_dans_0", inp))
        outdir = pathlib.Path(a.output) if a.output else None
        ok = sum(generate(f, (outdir or f.parent) / (f.stem + (".html" if a.shared_shell else " - Offline.html")), a.vendor, modular=a.modular, shell=a.shared_shell, **kw) for f in files)
        print(_tr("py.glb2html.0_1_fichiers_generes", ok, len(files)))
        sys.exit(0 if ok == len(files) else 1)
    if not inp.is_file():
        sys.exit(_tr("py.glb2html.0_introuvable", inp))
    if inp.suffix.lower() == ".gltf":
        sys.exit(_tr("py.glb2html.entree_gltf_repacker_d_abord_en"))
    if a.output:
        out = pathlib.Path(a.output)
        if out.is_dir() or str(a.output).endswith(("/", "\\")):
            out = out / (inp.stem + (".html" if a.shared_shell else " - Offline.html"))
        elif not out.suffix:
            out = out.with_suffix(".html")
    else:
        out = inp.with_name(inp.stem + (".html" if a.shared_shell else " - Offline.html"))
    if a.shared_shell and not valid_region_name(region_of(a.shared_shell, out) or ""):
        sys.exit(_tr("py.glb2html.erreur_nom_de_region_0_refuse_3", region_of(a.shared_shell, out) or out.stem))
    if a.register:
        entry = region_entry(a, S_reg, a.room or inp.stem, inp.stem, page_name_of(a, out))
        reg = data_path(a.register)
        kw["map_entries"] = register_region(reg, entry)
        print(_tr("py.glb2html.carte_0_ajoutee_ou_mise_a", entry['name'], reg, len(map_regions(kw['map_entries']))))
        where_note(reg, a.output)
    ok = generate(inp, out, a.vendor, modular=a.modular, shell=a.shared_shell, **kw)
    if ok and a.map_page:
        entries = kw["map_entries"] if kw.get("map_entries") is not None else json.loads(MAP_JSON)
        if not clean_map(entries):
            print(_tr("py.glb2html.avertissement_map_page_ignore_aucune_region_2"), file=sys.stderr)
        else:
            mp = pathlib.Path(a.map_page)
            write_map_page(mp if mp.is_absolute() else out.parent / mp, entries, kw.get("presence_url", ""), kw.get("map_url", ""), a.title or _tr("py.glb2html.carte_des_mondes"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    sys.argv = old_options(sys.argv)
    main()
