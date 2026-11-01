#!/usr/bin/env python3
"""glb2tiles.py : découpe un GLB énorme en tuiles autonomes (un GLB valide par tuile).

Usage :  python glb2tiles.py --version
         python glb2tiles.py "Region.glb" --analyse
         python glb2tiles.py "Region.glb" [--budget 32] [--budget-triangles 1500000] [--min 16] [--output DOSSIER] [--no-overview]
         python glb2tiles.py "Region.glb" --overview-only [mêmes options de découpage] [--ov-budget 25] [--ov-threshold 3]

Python standard seulement. Le GLB d'entrée n'est jamais chargé en entier : l'en-tête JSON est lu, puis les accessors
et les images sont lus par seek/read, par morceaux, à la demande. Chaque tuile (quelques dizaines de Mo) est
assemblée en mémoire puis écrite.

Sorties (à côté du GLB, ou dans --output) : X.tiles/T_<niveau>_<i>_<j>.glb, X.tiles.json et (v31) X.overview.glb.
Le journal est glb2tiles.log, écrit à côté du script (sa première ligne donne la version).

Principe : quadtree adaptatif sur le plan X,Z (glTF : Y vers le haut), uniquement sur les cellules non vides. Une cellule
est subdivisée tant que son poids autonome dépasse --budget (Mo) ou ses triangles --budget-triangles, et que son côté dépasse
--min (m). Un objet racine (nœud de premier niveau) reste entier si son poids autonome ne dépasse pas --whole-weight (Mo)
ET si son étendue ne dépasse pas --whole-extent (m) ; sinon il est réparti instance par instance. Un objet portant un
skin n'est jamais réparti. Les meshes partagés entre tuiles sont dupliqués dans chaque tuile qui les utilise.
Les sommets de chaque primitive sont compactés (seuls les sommets indexés sont gardés). Coordonnées inchangées.

Images (v31) : une image embarquée de 0 octet, d'un autre format que PNG/JPEG/WebP ou tronquée fait échouer le chargement de la tuile
dans le navigateur ; elle est remplacée par un petit PNG gris (un seul par tuile). --analyse et le rapport en donnent le nombre.

Vue d'ensemble (v31, X.overview.glb) : toute la région en géométrie légère, sans image, un nœud par fichier de tuile ; chaque primitive
unique est simplifiée une seule fois (regroupement de sommets), le terrain est rééchantillonné sur un réseau commun. Écrite avec les
tuiles (--no-overview pour s'en passer) ou seule (--overview-only, mêmes options de découpage). Options --ov-*.

Hors lot : découpage par triangles d'un mesh unique plus grand qu'une cellule (terrain, mer), compression des tuiles.
Les GLB compressés (Draco, meshopt) sont refusés.

Les fonctions communes de mesure (lecture de l'en-tête, matrices, instances) viennent de glb-stats.py, qui doit se
trouver à côté de ce script (build.py le recopie dans dist/).
"""
import argparse
import array
import base64
import collections
import importlib.util
import itertools
import json
import math
import os
import re
import statistics
import struct
import sys
import time
import traceback
import zlib
from pathlib import Path

# ---- langue des messages (v36) : textes intégrés par build.py (src/i18n/*.json, clés py.*) ; --lang fr|en|auto ou WEB3D_LANG ----
import json as _json, locale as _locale, os as _os, pathlib as _pl, sys as _sys

# fabrication (build.py) : la ligne suivante devient I18N_DATA = { "fr": {...}, "en": {...} }
I18N_DATA = _json.loads(r'''{"en":{"_name":"English","py.common.help":"show this help message and exit","py.common.lang_help":"language of the messages and of this help: fr, en or auto (default: the system's language; environment variable WEB3D_LANG is equivalent). Available: {0}","py.common.optionals":"options","py.common.positionals":"arguments","py.common.version_mark":"{0}, fingerprint {1}","py.common.version":"show the version and exit","py.glb2html.0_1_fichiers_generes":"{0}/{1} files generated","py.glb2html.0_cle_s_changee_s":"{0} key(s) changed","py.glb2html.0_gardee_s_telle_s_quelle":", {0} kept as they are","py.glb2html.0_gltf_version_1_non_supportee":"{0}: glTF version {1} not supported","py.glb2html.0_introuvable":"{0} not found","py.glb2html.0_pas_un_glb_magic_absent":"{0}: not a GLB (magic number missing)","py.glb2html.0_premier_chunk_non_json":"{0}: first chunk is not JSON","py.glb2html.0_reference_des_fichiers_externes_1":"{0}: references external files {1} -> repack as a standalone GLB (npx @gltf-transform/cli copy in.gltf out.glb)","py.glb2html.0_taille_annoncee_1_taille_fichier":"{0}: announced size {1} != file size {2} (truncated?)","py.glb2html.0_textures_ktx2_basis_non_gerees":"{0}: KTX2/Basis textures not handled offline -> npx @gltf-transform/cli png in.glb out.glb","py.glb2html.absent_paren":" (missing)","py.glb2html.adresse_de_la_page_de_cette":"address of the page of this region (default: the name of the .html file, relative)","py.glb2html.adresse_s_de_regions_json_partage":"address(es) of shared regions.json, comma-separated: the page reads them again at each opening (http/https), merges them and completes them with the embedded map. Another site must allow access (CORS)","py.glb2html.afficher_le_nom_de_l_element":"show the name of the clicked element","py.glb2html.amplitude_vagues_0_10":"wave amplitude 0..10","py.glb2html.aucun_glb_dans_0":"No .glb in {0}","py.glb2html.aucune_cle_changee":"no key changed","py.glb2html.avertissement_0_0_0_0_est":"[WARNING] 0.0.0.0 is a listening address of the server, not a destination: replaced by 127.0.0.1 -> {0}","py.glb2html.avertissement_0_existe_et_differe_de":"[WARNING] {0} exists and differs from this version's shell: kept (the other regions share it). Delete it to renew it","py.glb2html.avertissement_0_introuvable_a_cote_de":"[WARNING] {0} not found beside the page (the region has neither .glb nor tiles here)","py.glb2html.avertissement_0_tuile_s_listee_s":"[WARNING] {0} tile(s) listed in {1} not found beside it (first: {2}); the page will report them and retry","py.glb2html.avertissement_default_ignore_sans_shared_shell":"Warning: --default is ignored without --shared-shell.","py.glb2html.avertissement_des_zones_sont_liees_a":"[WARNING] some zones are linked to a model element (mesh field), but {0} was written without object references (glb2tiles before v32): the page will ignore these zones (console warning). Split again with glb2tiles v32 to benefit from them.","py.glb2html.avertissement_map_page_ignore_aucune_region":"[WARNING] --map-page ignored: no region to show (give --register to register this region, or --map)","py.glb2html.avertissement_map_page_ignore_aucune_region_2":"[WARNING] --map-page ignored: no region to show (give --register or --map)","py.glb2html.avertissement_presence_url_doit_commencer_pa":"[WARNING] --presence-url must start with ws:// or wss:// (received: {0})","py.glb2html.avertissement_region_name_region_url_region":"[WARNING] --region-name, --region-url, --region-xy, --region-spawn and --thumb are only used with --register: ignored","py.glb2html.avertissement_register_et_map_page_ne":"[WARNING] --register and --map-page only apply to a .glb file, not to a folder","py.glb2html.avertissement_title_est_ignore_en_mode":"[WARNING] --title is ignored in modular mode: the page title is the room (--room) of the config","py.glb2html.avertissement_vignette_ignoree_jpg_png_webp":"[WARNING] thumbnail ignored (jpg/png/webp of 140 KB at most expected): {0}","py.glb2html.avertissement_vignette_introuvable_0":"[WARNING] thumbnail not found: {0}","py.glb2html.avertissement_vue_d_ensemble_0_introuvable":"[WARNING] overview {0} not found beside {1}; the page will work without it","py.glb2html.avertissement_zones_live_est_ignore_en":"[WARNING] --zones-live is ignored in modular mode: the zones are always read again from <page>.zones.json","py.glb2html.cache_telechargement_0":"[cache] downloading {0}","py.glb2html.image_nombre":"[image] \"{0}\": {1} exists, the name stays \"{0}\" (the page looks for the file by itself)","py.glb2html.image_completee":"[image] \"{0}\" -> {1}","py.glb2html.image_plusieurs":"[image] \"{0}\" -> {1} ({2} files match: the first in alphabetical order is used)","py.glb2html.image_sans_fichier":"[image] \"{0}\": no file \"{0}.jpg\", \"{0}-...\" in {1} (name left as is)","py.glb2html.carte_0_ajoutee_ou_mise_a":"[map] “{0}” added or updated in {1} ({2} region(s))","py.glb2html.carte_0_n_est_pas_a":"[map] {0} is not beside the page {1} (a relative path of --register is searched in the launch folder, otherwise in the tools folder). To write it beside the page: give a full path, or update the region with --update (paths relative to the page)","py.glb2html.carte_0_region_s_lue_s":"[map] {0} region(s) read from {1}","py.glb2html.carte_avec_maj_les_chemins_relatifs":"[map] with --update, the relative paths of --register, --map, --map-page and --thumb are relative to the page folder: {0}","py.glb2html.carte_des_mondes":"World map","py.glb2html.carte_page_carte_0_region_s":"[map] map page ({0} region(s)) -> {1}","py.glb2html.ce_n_est_pas_un_fichier":"this is not a viewer settings file","py.glb2html.ce_n_est_pas_un_objet":"this is not a JSON object","py.glb2html.chat_entre_visiteurs_necessite_presence_url":"chat between visitors (needs --presence-url; Enter key while walking)","py.glb2html.cible_camera_x_y_z":"camera target x,y,z","py.glb2html.compass":"compass at the top of the page: heading of the avatar (of the camera in global view) with the cardinal point and degrees (default: on)","py.glb2html.coquille_0_absente_ecrite":"shell {0} missing: written","py.glb2html.coquille_0_deja_a_jour_identique":"shell {0} already up to date (identical to the one from {1})","py.glb2html.coquille_0_deja_presente_et_identique":"[shell] {0} already present and identical","py.glb2html.coquille_0_ecrite":"[shell] {0} written","py.glb2html.coquille_0_plus_ancienne_que_1":"shell {0} older than {1}: renewed, old copy kept as {2}. This shell is shared by the other regions of the folder: they keep their behavior (old configurations are still understood)","py.glb2html.coquille_commune_0_adresse_1":"shared shell {0}; address: {1}","py.glb2html.coquille_modulaire_marqueur_s_non_remplace":"modular shell: marker(s) not replaced {0}","py.glb2html.couleur_ciel_ex_87ceeb":"sky color, e.g. 87ceeb","py.glb2html.couleur_mer_ex_3a9ad9":"sea color, e.g. 3a9ad9","py.glb2html.default_json_ecrit":"default.json written: {0} (default region: {1})","py.glb2html.default_region":"with --shared-shell: this region becomes the default region (default.json), opened when the address has no ?region=; without this option default.json is only written if it does not exist yet","py.glb2html.demi_largeur_du_fondu_du_trou":"half-width of the hole fade","py.glb2html.desc":"glb2html.py {0}: builds the web page of a region from a .glb (or from tiles), updates a region, registers it in the world map.","py.glb2html.dessine_aussi_les_arrivees_dans_la":"also draws the arrivals in the page (small discreet marker on the ground; default: never)","py.glb2html.direction_camera_x_y_z":"camera direction x,y,z","py.glb2html.distance_5_a_200_m_defaut":"distance (5 to 500 m, default 150) up to which the tooltip, the click, the portal marker (cone) and the displayed name (showName) of the zones work while walking","py.glb2html.entree_gltf_repacker_d_abord_en":".gltf input: repack as a .glb first (npx @gltf-transform/cli copy in.gltf out.glb)","py.glb2html.epilog":"Examples:\n  python glb2html.py island.glb\n  python glb2html.py island.glb -o island.html --hole 90 --wave 1.2 --sea-y -30 --zoom 1.3\n  python glb2html.py island.glb --shared-shell -o Island.html --presence-url ws://ADDRESS:8765\n  python glb2html.py -o Island.html --shared-shell --update --zone-info-dist 60\n  python glb2html.py glb_folder/ --no-sea\nThe first time, three.js is downloaded once into ~/.cache/glb2html (or --vendor FOLDER: no download).","py.glb2html.erreur_0":"[ERROR] {0}","py.glb2html.erreur_0_entree_de_tuile_invalide":"[ERROR] {0}: invalid tile entry ({1}): \"file\" must be a relative .glb path (without .. or :), \"min\" and \"max\" three numbers","py.glb2html.erreur_0_illisible_1":"[ERROR] {0} unreadable ({1})","py.glb2html.erreur_0_introuvable":"[ERROR] {0} not found","py.glb2html.erreur_0_introuvable_cherche_dans_1":"[ERROR] {0} not found (searched in {1} then in {2})","py.glb2html.erreur_0_introuvable_vendor_doit_pointer":"[ERROR] {0} not found (--vendor must point to the root of the npm three package)","py.glb2html.erreur_0_liste_tiles_absente_ou":"[ERROR] {0}: “tiles” list missing or empty (a file written by glb2tiles.py is expected)","py.glb2html.erreur_0_ou_1_introuvable_genere":"[ERROR] {0} or {1} not found: first generate the region with --shared-shell","py.glb2html.erreur_0_ou_1_introuvable_genere_2":"[ERROR] {0} or {1} not found: first generate the page with --modular","py.glb2html.erreur_0_overview_invalide_1_file":"[ERROR] {0}: invalid “overview” ({1}): “file” must be a relative .glb path (without .. or :)","py.glb2html.erreur_aucune_region_a_afficher_donne":"[ERROR] no region to show: give --map regions.json","py.glb2html.erreur_avec_maj_o_designe_la":"[ERROR] with --update, -o designates the region (e.g. -o Region.html), not a folder","py.glb2html.erreur_avec_tiles_o_designe_la":"[ERROR] with --tiles, -o designates the region (e.g. -o Region.html), not a folder","py.glb2html.erreur_config_only_demande_o_page":"[ERROR] --config-only needs -o <page.html> (the already generated modular page)","py.glb2html.erreur_enregistrer_une_region_sans_glb":"[ERROR] registering a region without .glb needs --region-name, --region-url and --room","py.glb2html.erreur_fichier_de_reglages_0_introuvable":"[ERROR] settings file {0} not found (searched in {1} then in {2})","py.glb2html.erreur_lib_url_refuse":"Error: --lib-url \"{0}\" refused (expected: relative path such as ../lib, or a full http(s) address, without ? # \\ or quotes).","py.glb2html.erreur_maj_0_introuvable_la_region":"[ERROR] --update: {0} not found, the region has not been generated yet. Generate it first, without --update: {1}","py.glb2html.erreur_maj_0_introuvable_si_la":"[ERROR] --update: {0} not found. If the region uses a shared shell, give --shared-shell NAME.html (default {1})","py.glb2html.erreur_maj_demande_o_region_html":"[ERROR] --update needs -o <Region.html> (the already generated region)","py.glb2html.erreur_maj_et_settings_s_excluent":"[ERROR] --update and --settings exclude each other: --update only takes the options given and the existing config","py.glb2html.erreur_nom_de_region_0_refuse":"[ERROR] region name “{0}” refused by the shared shell (a single file name, without / \\ : ? # or .., without a leading dot)","py.glb2html.erreur_nom_de_region_0_refuse_2":"[ERROR] region name “{0}” refused by the shared shell","py.glb2html.erreur_nom_de_region_0_refuse_3":"[ERROR] region name \"{0}\" refused by the shared shell (a single file name, without / \\ : ? # or .., no leading dot): choose another -o","py.glb2html.erreur_region_xy_attend_deux_nombres":"[ERROR] --region-xy expects two numbers: X,Y","py.glb2html.erreur_settings_sans_nom_demande_le":"[ERROR] --settings without a name needs the .glb (the file searched is <name of the .glb>.reglages.json)","py.glb2html.erreur_shared_shell_attend_un_nom":"[ERROR] --shared-shell expects an .html file (a name, or a path FOLDER/index.html for regions in sub-folders) (received \"{0}\")","py.glb2html.erreur_telechargement_impossible_0_utilise_v":"[ERROR] download impossible ({0}). Use --vendor <three folder>.","py.glb2html.erreur_tiles_demande_o_region_html":"[ERROR] --tiles needs -o <Region.html> (its name without extension is the region's)","py.glb2html.erreur_tiles_remplace_le_glb_ne":"[ERROR] --tiles replaces the .glb: do not give a .glb file with --tiles","py.glb2html.erreur_zones_only_demande_o_page":"[ERROR] --zones-only needs -o <page.html>","py.glb2html.erreur_zones_only_demande_zones_fichier":"[ERROR] --zones-only needs --zones FILE (or --settings): no zone to write","py.glb2html.erreur_zones_only_demande_zones_live":"[ERROR] --zones-only needs --zones-live (standalone page) or an already generated modular page ({0} not found beside the page)","py.glb2html.fichier_glb_ou_dossier_de_glb":".glb file or folder of .glb files","py.glb2html.fichier_json_de_zones_exporte_par":"zones .json file exported by the viewer; relative path: searched in the launch folder, then in the script folder. A zone can carry a mesh field (exact name of an element of the model): the element becomes clickable","py.glb2html.scan.help":"sites folder (shared shell at the root): updates its regions.json with the regions found (NAME.config.json) and their thumbnails (NAME.jpg, .png or .webp next to it); keeps names, places, arrivals, the header and external cards; deletes nothing","py.glb2html.scan.dryhelp":"with --scan-sites: shows the changes without writing anything","py.glb2html.scan.nofolder":"[ERROR] folder not found: {0}","py.glb2html.scan.noshell":"[WARNING] no index.html in {0}: the index.html?region=... addresses of the cards need the shell at the root","py.glb2html.scan.badcfg":"[WARNING] {0} unreadable, skipped: {1}","py.glb2html.scan.add":"  + {0} ({1}), place {2},{3}","py.glb2html.scan.upd":"  ~ {0}: {1}","py.glb2html.scan.orphan":"  ? {0}: {1} not found in the folder, card kept","py.glb2html.scan.summary":"regions.json: {0} added, {1} updated, {2} unchanged, {3} external kept, {4} orphan(s) -> {5}","py.glb2html.scan.dry":"--dry-run: nothing was written","py.glb2html.fichier_regions_json_a_mettre_a":"regions.json file to update with THIS region (added or updated per room); relative: launch folder if it exists there, otherwise script folder. The generated page embeds the up-to-date map","py.glb2html.fichier_regions_json_carte_des_mondes":"regions.json file (world map: name, address, position, thumbnail) exported by the viewer; relative path: launch folder, then script folder","py.glb2html.finesse_du_maillage_de_la_mer":"fineness of the sea mesh 8..1000 (cell = 4000/segments; only with --anim)","py.glb2html.format_attendu_x_y_z":"expected format: x,y,z","py.glb2html.gabarit_modulaire_cible_introuvable_ou_multi":"modular template: target not found or multiple ({0}...)","py.glb2html.genere_aussi_une_page_web_carte":"also generates a “world map” web page (clickable links to each region); without .glb: generates only this page from --map. Relative: beside the page of the region","py.glb2html.haute_resolution_rendu_x2_minimum_supersampl":"high resolution: x2 rendering at least (supersampling, sharper but ~4x heavier)","py.glb2html.hauteur_des_yeux_en_m_promenade":"eye height in m (walk)","py.glb2html.hauteur_mer_150_60":"sea height -150..60","py.glb2html.help.anim":"animate the sea (waves); --no-anim: still sea","py.glb2html.help.light":"the page opens in light rendering (half resolution, at most 15 frames/s, overview only in global view, no antialiasing) until the visitor chooses otherwise in Settings; --no-light: normal rendering","py.glb2html.help.sea":"show the sea (--no-sea: without the sea)","py.glb2html.identifiant_du_point_d_arrivee_des":"identifier of the arrival point of the visitors in this region (default: default)","py.glb2html.inclure_le_mode_promenade_touche_f":"include the walk mode (P and F keys) in the page","py.glb2html.la_page_recharge_ses_zones_a":"the page reloads its zones at each opening from a .zones.json file placed beside it (served over http/https; otherwise the embedded zones are used). Without NAME: <page>.zones.json. The file is written by the script, filtered according to --profile","py.glb2html.le_fichier_glb_ou_le_dossier":"the .glb file (or the folder) is required","py.glb2html.lib_url":"relative path (../lib) or full http(s) address where to find three.js and its modules; written in the \"const LIB\" line of the shell (editable by hand; --update keeps it) when it is written and kept in the config for --update. Relative path: lib/ is created there if missing; full address: nothing is copied","py.glb2html.m_charger_les_tuiles_dont_la":"m: load the tiles whose box is within this radius of the avatar, in the X,Z plane (default %(default)g; ?radius=NNN in the address to try)","py.glb2html.m_decharger_les_tuiles_au_dela":"m: unload the tiles beyond radius + margin (default %(default)g)","py.glb2html.maj_0_absent_ou_incomplet_ecrit":"[update] {0}/ missing or incomplete: written","py.glb2html.maj_0_conserve_tel_quel":"[update] {0} kept as is","py.glb2html.maj_0_mis_a_jour_glb2html":"[update] {0} updated (glb2html {1}): ","py.glb2html.maj_0_present_conserve":"[update] {0}/ present: kept","py.glb2html.maj_0_remplace_par_1":"[update] {0} replaced by {1}","py.glb2html.maj_le_profil_ne_filtre_les":"[update] the profile only filters the zones when the zone list is written: add --zones FILE to write it again","py.glb2html.maj_lib_repris":"[update] lib folder taken from the \"const LIB\" line of the shell: {0}","py.glb2html.marqueur_des_portails_et_zones_libres":"marker of the portals and free zones in the page: dot (default: 0.4 m disc and thin ring), range (thin sharp ring at the real radius of the zone, visible from afar) or none; the old values discret, portee and aucun are still accepted. The arrivals are never drawn (see --show-spawns)","py.glb2html.met_a_jour_une_region_deja":"updates an already generated region (-o REGION.html [--shared-shell [SHELL.html]] [--tiles X.tiles.json | X.glb]): reads X.config.json, applies ONLY the options given on the line, keeps everything else and X.zones.json (rewritten only with --zones), writes the current version and renews the shell if it is older (old copy kept under a dated name). Fails if X.config.json does not exist","py.glb2html.mo_de_tuiles_chargees_en_meme":"MB of tiles loaded at the same time (file weight; default %(default)g); beyond that, the farthest ones go first","py.glb2html.mode_modulaire_a_coquille_commune_une":"modular mode with a shared shell: a single shell (default {0}) serves several regions, at the address SHELL.html?region=NAME. -o designates the region (NAME = its name without extension, e.g. -o Ankh.html): only NAME.glb, NAME.config.json and NAME.zones.json are written, plus the shell, lib/three-X/ and (the first time) default.json if they are missing (an existing shell is never overwritten). With a path (--shared-shell FOLDER/index.html), -o may be in a sub-folder of FOLDER: address SHELL.html?region=sub/folder/NAME. --register writes this address in regions.json. Implies --modular","py.glb2html.mode_modulaire_ecrit_une_coquille_page":"modular mode: writes a shell <page>.html identical for all regions (it deduces its files from its name) + <page>.glb (raw bytes) + <page>.config.json (settings) + <page>.zones.json (zones, read again at each opening; otherwise zones.json of the folder) + shared lib/three-X/ (Draco and Meshopt included). Needs http(s) to open (not from the disk)","py.glb2html.nom_affiche_dans_la_carte_defaut":"name shown in the map (default: name of the .glb)","py.glb2html.materiaux_rendus_opaques":"names of materials drawn opaque (they then hide what is behind), comma-separated: \"1471516\" = any name containing this text, \"=pbrmat-123\" = exact name; \"\" = none","py.glb2html.noms_a_ignorer_en_collision_separes":"names to ignore in collisions, comma-separated: \"door\" = start of word, \"=mesh_346_5\" = exact name; \"\" = nothing","py.glb2html.north":"offset in degrees added to the displayed heading; 0 = north is the -Z direction of the model (OpenSim); for a GLB that does not come from OpenSim (default 0)","py.glb2html.ok_0_1_2_2f_mo":"[OK] {0} -> {1} ({2:.2f} MB glb, {3:.2f} MB html) [glb2html {4}]","py.glb2html.ok_0_1_2_3_coquille":"[OK] {0} -> {1} + {2} + {3}, shared shell {4}; address: {5} [glb2html {6}]","py.glb2html.ok_0_1_modulaire_coquille_2":"[OK] {0} -> {1} (modular: shell {2:.0f} KB + {3} {4:.2f} MB + {5} + {6} + {7}/) [glb2html {8}]","py.glb2html.ok_0_tuile_s_1_2":"[OK] {0} tile(s) -> {1} + {2}, ","py.glb2html.ok_region_mise_a_jour_adresse":"[OK] region updated ; address: {0} [glb2html {1}]","py.glb2html.ok_reglages_0_coquille_et_glb":"[OK] settings -> {0} (shell and .glb unchanged) [glb2html {1}]","py.glb2html.panneau_de_reglages_pour_les_visiteurs":"settings panel for the visitors (high resolution, animated sea, wave strength), button at the top right","py.glb2html.petit_cone_pointe_vers_le_bas":"small cone pointing down above each portal and each “enter” or “both” zone (marker visible up to --zone-info-dist; T key to show or hide it; default: shown; the arrivals only have one with --show-spawns)","py.glb2html.position_sur_la_grille_comme_opensim":"position on the grid, as in OpenSim (X to the east, Y to the north), e.g. 1000,1001","py.glb2html.position_x_du_centre_du_trou":"X position of the hole center (world)","py.glb2html.position_z_du_centre_du_trou":"Z position of the hole center (world)","py.glb2html.public_retire_les_zones_privees_ex":"public: removes the private zones (e.g. Home Assistant); private: keeps them (old value perso accepted)","py.glb2html.racine_d_un_paquet_npm_three":"root of a local npm three package (otherwise cache + download)","py.glb2html.ratio_de_cadrage_1_cadrage_auto":"framing ratio (1 = automatic framing)","py.glb2html.rayon_du_trou_30_600_zone":"hole radius 30..600 (flat zone = radius - fade)","py.glb2html.reecrit_seulement_les_zones_sans_regenerer":"rewrites only the zones, without regenerating the HTML: <page>.zones.json of an already generated modular page (with --zones FILE), or, with --zones-live, the zones file of a standalone page","py.glb2html.reecrit_seulement_page_config_json_d":"rewrites only <page>.config.json of an already generated modular page (given by -o), without touching the .glb or the shell; visitors reload. <page>.zones.json is only rewritten if --zones is given. With --register, also updates the map","py.glb2html.region_decoupee_en_tuiles_par_glb2tiles":"region split into tiles by glb2tiles.py: no .glb as input; -o designates the region. Writes X.config.json (“tiles” field), X.zones.json, the shell and lib/; X.tiles.json and its tiles are only copied if they are not already beside the page. Implies --modular. Frame = that of the original model (no recentering); zones linked to an object: possible if the tiles come from glb2tiles v32, ignored otherwise","py.glb2html.reglages_0_parametre_s_repris_de":"[settings] {0} parameter(s) taken from {1}","py.glb2html.reprend_tous_les_reglages_enregistres_par":"takes ALL the settings saved by the viewer (“Save to a file” button: hole, waves, camera, zones, region card, thumbnail…). Without a name: <name of the .glb>.reglages.json. The command-line options take precedence. Relative: launch folder, then script folder","py.glb2html.rotation_de_la_region_autour_de":"rotation of the region around the vertical axis (0, 90, 180 or 270 degrees), applied at loading before recentering. The zones, arrivals, target and hole of the zones / settings file are ALREADY in the rotated frame (the viewer rotates them with the region)","py.glb2html.salon_de_presence_defaut_nom_du":"presence room (default: file name)","py.glb2html.secondes_avant_disparition_des_messages_et":"seconds before messages and bubbles disappear; 0 = they stay until new messages replace them","py.glb2html.serveur_de_presence_ws_ou_wss":"presence server ws:// or wss:// (see presence_server.py); \"*\" instead of the name = the same name as the page (ws://*:8765, advised for a page opened through several addresses); empty = disabled","py.glb2html.seuil_alpha_feuillage_0_0_5":"foliage alpha threshold 0..0.5","py.glb2html.shell_name":"shell {0}","py.glb2html.sortie_fichier_html_ou_dossier_cree":"output: .html file, or folder (created if needed). Folder input: output folder. Default: \"<name> - Offline.html\" beside the .glb","py.glb2html.telechargements_simultanes_defaut_default_d":"simultaneous downloads (default %(default)d)","py.glb2html.titre_de_la_page":"page title","py.glb2html.triangles_de_tuiles_chargees_en_meme":"triangles of tiles loaded at the same time (default %(default)d)","py.glb2html.tuiles_0_copie_dans_1_tuiles":"[tiles] {0} copied into {1} ; tiles: {2} copied ({3:.1f} MB), {4} already present with the same size (neither checked nor copied again){5}","py.glb2html.tuiles_0_tuile_s_et_1":"[tiles] {0} tile(s) and {1} already beside the page: nothing is copied{2}","py.glb2html.tuiles_cible_de_camera_par_defaut":"[tiles] default camera target: {0} (center of the extent, original model frame; --target to change it)","py.glb2html.tuiles_des_zones_sont_liees_a":"[tiles] some zones are linked to an object (mesh field): the page places them with the object as soon as the tile that contains it is loaded","py.glb2html.tuiles_hauteur_de_la_mer_par":"[tiles] default sea height: 20 m (original model frame, like OpenSim water; --sea-y to change it, --no-sea to remove it)","py.glb2html.vignette_de_la_region_fichier_jpg":"thumbnail of the region: jpg/png/webp file of 140 KB at most (embedded), or http(s) address (kept as is, lighter map)","py.glb2html.vitesse_de_marche_en_m_s":"walking speed in m/s (Shift = x2.2)","py.glb2html.voir_les_visiteurs_en_promenade_depuis":"see the walking visitors from the global view (connects as soon as the page opens; on by default as soon as a --presence-url is given; --no-spectate to avoid it)","py.glb2html.vol_en_promenade_touche_f_ou":"flight while walking (Home key or button; Page Up / Space held goes up, Page Down / C goes down): on by default, --no-fly removes it","py.glb2html.vue_d_ensemble_0_placee_avec":" ; overview {0} placed with the tiles","py.glb2html.zones_0_non_modifie_donne_zones":"[zones] {0} unchanged (give --zones FILE to rewrite it)","py.glb2html.zones_0_zone_s_lue_s":"[zones] {0} zone(s) read from {1}","py.glb2html.zones_0_zone_s_profil_1":"[zones] {0} zone(s), profile {1} -> {2}","py.glb2html.zones_zones_deja_en_place_0":"[zones] zones already in place: {0} (not rewritten)","py.glb2html.zones_zones_deja_en_place_0_2":"[zones] zones already in place: {0} (read for checking, neither rewritten nor copied)","py.glb2tiles.0_1_0f_m_du_centre":"\"{0}\" ({1:.0f} m from the center, extent {2:.0f} m)","py.glb2tiles.0_1_2f_mo_2_triangles":"  - \"{0}\": {1:.2f} MB, {2} triangles, extent (X x Y x Z) {3}, {4} instance(s)","py.glb2tiles.0_distance_1_0f_m_etendue":"  - \"{0}\": distance {1:.0f} m, extent {2:.0f} m","py.glb2tiles.0_illisible_1":"{0} unreadable ({1}).","py.glb2tiles.0_instance_s_aberrante_s_a":"{0} outlying instance(s) (farther than {1:g} m from the median center or with a larger extent): {2}.","py.glb2tiles.0_introuvable_vue_ensemble_seule_suppose":"{0} not found: --overview-only assumes the split has already been done (in {1}).","py.glb2tiles.0_nud_s_avec_camera_ou":"{0} node(s) with a camera or node extensions: these fields are not copied into the tiles.","py.glb2tiles.0_objet_s_au_nom_correspondant":"  {0} object(s) with a matching name kept by the safeguards (too many triangles or meshes)","py.glb2tiles.0_octet_gagne_toute_la_geometrie":"  0 bytes gained: all the geometry and images of the excluded objects are shared with kept objects (same primitive or same texture, typically a common cube); removing these objects removes nodes and triangles, not bytes.","py.glb2tiles.0_scenes_seule_la_scene_1":"{0} scenes: only scene {1} is split.","py.glb2tiles.accessor_0_accessor_sparse_non_gere":"Accessor {0}: \"sparse\" accessor not supported by glb2tiles.","py.glb2tiles.accessor_0_bytestride_1_plus_petit":"Accessor {0}: byteStride ({1}) smaller than an element ({2}).","py.glb2tiles.accessor_0_depasse_son_bufferview_fichier":"Accessor {0}: exceeds its bufferView (invalid file).","py.glb2tiles.accessor_0_indices_avec_bytestride_non":"Accessor {0}: indices with byteStride not supported.","py.glb2tiles.accessor_0_inexistant":"Accessor {0} does not exist.","py.glb2tiles.accessor_0_positions_non_gerees":"Accessor {0}: positions not handled.","py.glb2tiles.accessor_0_sans_bufferview_valeurs_a":"Accessor {0}: without bufferView (zero values) not supported by glb2tiles.","py.glb2tiles.accessor_0_type_1_2_inconnu":"Accessor {0}: unknown type {1}/{2}.","py.glb2tiles.accessor_0_type_d_indices_non":"Accessor {0}: unsupported index type.","py.glb2tiles.accessor_0_un_indice_depasse_le":"Accessor {0}: an index exceeds the number of vertices ({1}): invalid file.","py.glb2tiles.analyse_0_primitives_distinctes_a_mesurer":"[analysis] {0} distinct primitives to measure (indices read in chunks)","py.glb2tiles.aucun_mesh_positionnable_dans_la_scene":"No placeable mesh in the scene: nothing to split.","py.glb2tiles.avec_exclure_meshes_au_plus_dans":"with --exclude: at most this many meshes in the root object (default 1)","py.glb2tiles.avec_exclure_triangles_au_plus_dans":"with --exclude: at most this many triangles in the root object, all meshes included (default 24)","py.glb2tiles.avertissement_0_d_une_execution_precedente":"Warning: {0} from a previous run is not removed, but the index no longer mentions it (--no-overview).","py.glb2tiles.avertissement_0_existe_deja_mais_ses":"Warning: {0} already exists but its tiles do not carry object references (glb2tiles before v32): to link zones to objects in tile mode, redo the split.","py.glb2tiles.avertissement_ces_tuiles_ont_ete_ecrites":"Warning: these tiles were written without object references (glb2tiles before v32): zones linked to an object remain ignored in tile mode. Redo the split (without --overview-only) to benefit from them.","py.glb2tiles.bufferview_0_inexistant":"bufferView {0} does not exist.","py.glb2tiles.bufferview_0_seul_le_tampon_0":"bufferView {0}: only buffer 0 is supported.","py.glb2tiles.ce_glb_est_compresse":"This GLB is compressed (","py.glb2tiles.cellules_sur_la_plus_grande_dimension":"cells along the largest dimension of a primitive for vertex clustering (default %(default)d)","py.glb2tiles.cote_des_blocs_de_la_section":"side of the blocks of the glb-stats section of --analyse (default 256)","py.glb2tiles.cote_minimal_d_une_cellule_en":"minimum side of a cell in m (default 16)","py.glb2tiles.couleurs_moyenne_de_texture_pour_0":"  colors: texture average for {0} image(s), {1} unreadable (base color)","py.glb2tiles.couleurs_pillow_absent_couleur_de_base":"  colors: Pillow missing, material base color ({0} textured material(s) concerned); install Pillow for average colors","py.glb2tiles.decoupage_prevu_budget_0_g_mo":"== Planned split (budget {0:g} MB, {1} triangles, minimum cell {2:g} m) ==","py.glb2tiles.decouper_meme_si_la_recommandation_est":"split even if the recommendation is \"no split\"","py.glb2tiles.des_primitives_portent_des_extensions_elles":"Some primitives carry extensions: they are not copied into the tiles.","py.glb2tiles.desc":"glb2tiles.py {0}: splits a huge GLB into standalone tiles and writes X.tiles.json and the overview X.overview.glb (standard Python only).","py.glb2tiles.dossier_de_sortie_defaut_a_cote":"output folder (default: beside the GLB)","py.glb2tiles.duplication_reelle_de_la_geometrie_somme":"Actual geometry duplication (sum of the tiles / unique geometry): {0}","py.glb2tiles.entree_pour_fermer":"Press Enter to close...","py.glb2tiles.epilog":"Examples:\n  python glb2tiles.py Region.glb --analyse\n  python glb2tiles.py Region.glb --budget 32 --budget-triangles 1500000\n  python glb2tiles.py Region.glb --overview-only\nThe log is glb2tiles.log, written beside the script. glb-stats.py must be beside this script.","py.glb2tiles.erreur_0":"[ERROR] {0}","py.glb2tiles.etendue_des_instances_plus_grande_dimension":"Extent of the instances (largest dimension): instances and triangles above each threshold","py.glb2tiles.etendue_minimale_effective_0_g_m":"  effective minimum extent {0:g} m (requested threshold {1:g} m), resolution {2}, terrain step {3:g} m (requested {4:g} m)","py.glb2tiles.expression_reguliere_invalide_pour_exclure_0":"Invalid regular expression for --exclude: {0!r} ({1}).","py.glb2tiles.fichier_glb_tronque":"Truncated GLB file.","py.glb2tiles.glb2tiles_0":"[glb2tiles] {0}","py.glb2tiles.glb2tiles_0_1_1f_mo":"[glb2tiles] {0}: {1:.1f} MB","py.glb2tiles.glb2tiles_0_2":"glb2tiles {0}","py.glb2tiles.glb2tiles_ne_lit_pas_les_glb":"): glb2tiles does not read compressed GLBs (out of scope). Decompress the GLB first, then run again.","py.glb2tiles.glb_d_entree":"input GLB","py.glb2tiles.glb_introuvable_0":"GLB not found: {0}","py.glb2tiles.glb_stats_py_introuvable_a_cote":"glb-stats.py not found beside glb2tiles.py ({0}): copy it to the same place.","py.glb2tiles.image_externe_uri_non_geree_seuls":"External image (uri) not supported: only GLBs with embedded images are.","py.glb2tiles.images_vides_ou_invalides_remplacees_par":"Empty or invalid images replaced by a gray {0} PNG: {1} distinct, {2} occurrence(s) (one occurrence = one image written in a tile); materials and texture coordinates unchanged.","py.glb2tiles.la_tuile_0_n_a_plus":"Tile {0} no longer has the content of {1}: use the same options as for the original split.","py.glb2tiles.la_vue_d_ensemble_depasse_la":"The overview exceeds the 4 GB limit of a GLB.","py.glb2tiles.le_decoupage_recalcule_0_tuiles_ne":"The recomputed split ({0} tiles) does not match {1} ({2} tiles): use the same options (--budget, --budget-triangles, --min, --entier-*, --exclude...) as for the original split.","py.glb2tiles.le_tampon_0_a_une_adresse":"Buffer 0 has an address (uri): only GLBs with an embedded buffer are supported.","py.glb2tiles.lecture_0_octets_lus_sur_1":"Reading: {0} bytes read out of {1} (largest read {2} bytes; positions read again for {3} bytes, primitives sharing a vertex buffer).","py.glb2tiles.lecture_hors_du_tampon_du_glb":"Read outside the GLB buffer (offset {0}, {1} bytes): invalid or truncated file.","py.glb2tiles.lecture_seule_mesures_decoupage_prevu_recomm":"read-only: measurements, planned split, recommendation; writes nothing","py.glb2tiles.les_10_instances_les_plus_eloignees":"== The 10 instances farthest from the median center (X {0:.0f} m, Z {1:.0f} m) ==","py.glb2tiles.les_10_meshes_les_plus_lourds":"== The 10 heaviest meshes (compacted bytes, vertices really used) ==","py.glb2tiles.log_0":"[log] {0}","py.glb2tiles.m_distance_ou_etendue_au_dela":"m: distance or extent beyond which an instance is reported (default 1000)","py.glb2tiles.m_etendue_maximale_d_un_objet":"m: maximum extent of a root object kept whole (default 256)","py.glb2tiles.m_les_objets_dont_la_plus":"m: objects whose largest dimension is smaller are omitted (default %(default)g); the budget may raise it","py.glb2tiles.m_pas_du_reseau_du_terrain":"m: step of the terrain grid in the overview (default %(default)g)","py.glb2tiles.m_si_le_budget_oblige_a":"m: if the budget forces larger objects to be omitted, the resolution drops (default %(default)g)","py.glb2tiles.machine_big_endian_non_geree":"Big-endian machine not supported.","py.glb2tiles.mesh_0_primitive_sans_position_non":"Mesh {0}: primitive without POSITION not supported.","py.glb2tiles.mesures_de_glb_stats":"== glb-stats measurements ==","py.glb2tiles.mo_par_tuile_defaut_32":"MB per tile (default 32)","py.glb2tiles.mo_poids_maximal_de_la_vue":"MB: maximum weight of the overview (default %(default)g)","py.glb2tiles.mo_sous_ce_poids_et_sous":"MB: under this weight (and under --threshold-triangles) \"no split\" (default 150)","py.glb2tiles.mo_un_objet_racine_plus_leger":"MB: a root object lighter than this and smaller than --whole-extent stays whole (default 16)","py.glb2tiles.n_ecrire_que_x_overview_glb":"write only X.overview.glb (and its mention in X.tiles.json): existing tiles are not rewritten; the split parameters must be those of the original split","py.glb2tiles.ne_pas_attendre_entree_a_la":"do not wait for Enter at the end","py.glb2tiles.ne_pas_ecrire_extras_ref_extras":"do not write extras.ref / extras.box in the tile nodes (v31 format: zones linked to an object are then ignored in tile mode)","py.glb2tiles.ne_pas_ecrire_x_overview_glb":"do not write X.overview.glb (light overview of the whole region)","py.glb2tiles.nud_0":"node {0}","py.glb2tiles.nud_0_mesh_1_inexistant":"Node {0}: mesh {1} does not exist.","py.glb2tiles.objets_exclus_exclure_au_plus_0":"Excluded objects (--exclude, at most {0} triangles and {1} mesh(es) per root object): {2} | triangles removed: {3} | bytes gained: {4} ({5:.1f} MB)","py.glb2tiles.objets_omis_0_trop_petits_etendue":"  objects omitted: {0} too small (extent under the threshold), {1} by the budget, {2} with a skeleton; translucent primitives omitted: {3}","py.glb2tiles.objets_racine_0_gardes_entiers_1":"Root objects: {0} | kept whole: {1} (of which {2} with a skin) | spread instance by instance: {3}","py.glb2tiles.objets_racine_gardes_entiers_0_repartis":"Root objects kept whole: {0} | spread: {1}","py.glb2tiles.octets_des_exclus_qu_un_objet":"  bytes of excluded objects that a kept object also uses (not gained): {0} ({1:.1f} MB)","py.glb2tiles.poids_mo_mediane_0_1f_90":"Weight (MB): median {0:.1f} | 90 % under {1:.1f} | maximum {2:.1f}","py.glb2tiles.poids_par_tuile_mo_mediane_0":"Weight per tile (MB): median {0:.1f} | 90 % under {1:.1f} | maximum {2:.1f}","py.glb2tiles.primitive_les_attributs_n_ont_pas":"Primitive: the attributes do not all have {0} vertices (accessor {1}).","py.glb2tiles.rapport":"== Report ==","py.glb2tiles.recommandation_decouper_budget_0_g_mo":"Recommendation: split: budget {0:g} MB, {1} tiles, duplication {2}.","py.glb2tiles.recommandation_pas_de_decoupage_necessaire_0":"Recommendation: no split needed ({0:.1f} MB under {1:g} MB and {2} triangles under {3}).","py.glb2tiles.references_d_objets_extras_ref_extras":"Object references (extras.ref, extras.box): {0} named node(s), {1} name(s) shared by several nodes (name#index reference): zones linked to an object possible in tile mode.","py.glb2tiles.references_d_objets_non_ecrites_sans":"Object references not written (--no-refs): zones linked to an object will be ignored in tile mode.","py.glb2tiles.retire_du_decoupage_les_objets_racine":"removes from the split the root objects whose name matches (case-insensitive, repeatable), provided --exclude-max-triangles and --exclude-max-meshes are respected","py.glb2tiles.rien_n_est_ecrit_forcer_pour":"Nothing is written (--force to split anyway).","py.glb2tiles.sans_instance":"no instance","py.glb2tiles.sans_vue_ensemble_et_vue_ensemble":"--no-overview and --overview-only are mutually exclusive.","py.glb2tiles.skin_0_inexistant":"Skin {0} does not exist.","py.glb2tiles.temps_0_1f_s":"[time] {0:.1f} s","py.glb2tiles.temps_0_1f_s_1_octets":"[time] {0:.1f} s; {1} bytes read out of {2}","py.glb2tiles.texture_0_inexistante":"Texture {0} does not exist.","py.glb2tiles.triangles_de_la_vue_d_ensemble":"triangles of the overview (default %(default)d)","py.glb2tiles.triangles_mediane_0_90_sous_1":"Triangles: median {0} | 90 % under {1} | maximum {2}","py.glb2tiles.triangles_par_tuile_defaut_1500000":"triangles per tile (default 1500000)","py.glb2tiles.triangles_par_tuile_mediane_0_90":"Triangles per tile: median {0} | 90 % under {1} | maximum {2}","py.glb2tiles.triangles_pour_la_recommandation_pas_de":"triangles for the \"no split\" recommendation (default 3000000)","py.glb2tiles.tuile_0_1_2f_go_au":"Tile {0}: {1:.2f} GB, beyond the 4 GB limit of a GLB.","py.glb2tiles.tuile_0_hors_budget_1_1f":"Tile {0} over budget ({1:.1f} MB, {2} triangles): {3}. A single mesh larger than a cell cannot be spread at this stage.","py.glb2tiles.tuiles_0_dans_1":"Tiles: {0} in {1}","py.glb2tiles.tuiles_0_duplication_prevue_geometrie_1":"Tiles: {0} | planned duplication: geometry {1}, images {2}","py.glb2tiles.tuiles_d_une_execution_precedente_absentes":"Tiles from a previous run absent from the new index: {0} T_*.glb file(s) deleted","py.glb2tiles.vue_d_ensemble_0_1_1f":"Overview {0}: {1:.1f} MB, {2} triangles (of which terrain {3}), {4} object(s) kept out of {5}, in {6:g} s","py.glb2tiles.vue_d_ensemble_0_1f_mo":"[overview] {0:.1f} MB, {1} triangles, {2} object(s) out of {3}, {4} tile(s) in {5:.1f} s","py.glb2tiles.vue_d_ensemble_budget_0_g":"[overview] budget {0:g} MB and {1} triangles, extent threshold {2:g} m, resolution {3}, terrain step {4:g} m","py.glb2tiles.vue_d_ensemble_budget_atteint_avant":"[overview] budget reached before objects of {0:.0f} m: resolution reduced to {1}","py.glb2tiles.vue_d_ensemble_terrain_0_piece":"[overview] terrain: {0} piece(s), {1} triangles, grid of {2:g} m","py.glb2tiles.vue_d_ensemble_terrain_trop_lourd":"[overview] terrain too heavy for half the budget: step raised to {0:g} m","py.glb2tiles.warning_prefix":"Warning: ","py.oar2glb.0_5d_1_2_3_rigge":"{0:5d} | {1} | {2} | {3} | rigged: {4} | prim scale {5} | bind_shape scale {6} | transparent: {7} | animesh root box: {8} | GLB: {9}","py.oar2glb.0_face_s_a_part":" (+{0} separate face(s))","py.oar2glb.accesseur_0_non_gere":"accessor {0} not supported","py.oar2glb.accesseur_0_non_gere_float_vec3":"accessor {0} not supported (plain float VEC3 expected)","py.oar2glb.accesseur_position_0_bufferview_1_buffer":"      POSITION accessor {0}; bufferView {1}; buffer {2} {3} B; first 3 vertices {4}","py.oar2glb.ajouter_un_mat_rouge_de_15":"add a red 15 m pole to each placed rigged animal (to find it in the viewer)","py.oar2glb.altitude_de_la_racine":"altitude of the root","py.oar2glb.args":"[args]","py.oar2glb.aucune":"none","py.oar2glb.aucune_geometrie":"no geometry","py.oar2glb.avec_diag_glb_ou_gltf_a":"with --diag: GLB or .gltf to compare; default: the .gltf of the <oar>-GLTF folder (kept by --keep), otherwise the neighbouring .glb","py.oar2glb.avec_terrain_seul_fichier_glb_de":"with --terrain-only: output GLB file (default: X-terrain.glb beside the original)","py.oar2glb.bind_shape_matrix_0":"      bind_shape_matrix: {0}","py.oar2glb.bind_shape_matrix_non_inversible":"non-invertible bind_shape_matrix","py.oar2glb.bloc_skin_present_mais_illisible":"skin block present but unreadable","py.oar2glb.boite_racine_d_animesh":"animesh root box","py.oar2glb.cle_llsd_attendue":"LLSD key expected","py.oar2glb.controle_0_pieds_a_1_2f":"[check] '{0}' feet at {1:.2f} m, center {2:.2f} m: ","py.oar2glb.convoar":"[convoar]","py.oar2glb.convoar_0_image_s_annoncee_s":"[convoar] {0} image(s) announced by the .gltf but missing from the folder (examples: {1}): new attempt {2}/{3}, images already written are kept","py.oar2glb.convoar_0_image_s_recuperee_s":"[convoar] {0} image(s) recovered from the previous attempt","py.oar2glb.convoar_code_retour_0":"[convoar] return code {0}","py.oar2glb.correctif_0_mesh_es_rigge_s":"[fix] {0} rigged mesh(es) rescaled, {1} invisible prim(s) removed","py.oar2glb.cote_d_un_patch_de_terrain":"side of a terrain patch in meters, 2 to 255 (default {0})","py.oar2glb.dans_la_boite_de_0_objet":"inside the box of {0} object(s): {1}","py.oar2glb.defaut_d_opensim_aucun_waterheight_dans":"OpenSim default, no WaterHeight in settings/","py.oar2glb.desc":"oar2glb.py {0}: converts an OpenSim region backup (.oar) into a single GLB (convoar, repair, full terrain, packing).","py.oar2glb.dessous_de_la_boite_racine":"underside of the root box","py.oar2glb.diag_0_objet_s_1_partie":"[diag] {0} object(s), {1} part(s); terrain {2}; {3}","py.oar2glb.diag_nuds_glb_dont_tous_les":"[diag] GLB nodes whose materials are all transparent: {0}","py.oar2glb.diag_pos":"      position {0} ; terrain {1} ; {2}","py.oar2glb.diag_rigges_0_transparents_1_boites":"[diag] rigged: {0}; transparent: {1}; animesh root boxes: {2}; GLB nodes found: {3}/{4}","py.oar2glb.diag_uuid_lisibles_dans_les_nuds":"[diag] readable UUIDs in GLB nodes: {0}; example nodes:","py.oar2glb.domaine_de_position_du_mesh_0":"      mesh position domain ({0} submesh(es)): ","py.oar2glb.echelle_du_prim_appliquee_0":" ; prim scale applied: {0}","py.oar2glb.en_tete_du_mesh_illisible_0":"unreadable mesh header ({0})","py.oar2glb.entree_pour_fermer":"Press Enter to close...","py.oar2glb.epilog":"Examples:\n  python oar2glb.py \"P:\\path\\MyRegion.oar\"\n  python oar2glb.py \"P:\\path\\MyRegion.oar\" --keep --markers\n  python oar2glb.py \"P:\\path\\MyRegion.oar\" --diag        (changes nothing, does not run convoar)\n  python oar2glb.py --terrain-only MyRegion.glb \"P:\\path\\MyRegion.oar\"","py.oar2glb.erreur_0_introuvable":"[ERROR] {0} not found","py.oar2glb.erreur_0_introuvable_annonce_par_le":"[ERROR] {0} not found (announced by the .gltf).\n  {1} contains {2} file(s), of which {3} .buf: ","py.oar2glb.erreur_0_le_premier_chunk_n":"[ERROR] {0}: the first chunk is not JSON","py.oar2glb.erreur_0_le_tampon_0_n":"[ERROR] {0}: buffer 0 is not the BIN chunk's","py.oar2glb.erreur_0_n_est_pas_un":"[ERROR] {0} is not a GLB","py.oar2glb.erreur_0_n_est_pas_un_2":"[ERROR] {0} is not a version 2 GLB","py.oar2glb.erreur_0_tronque":"[ERROR] {0} truncated","py.oar2glb.erreur_0_vecteurs_de_mauvaise_taille":"[ERROR] {0} vectors of the wrong size: numbers written with a decimal comma.\n  ","py.oar2glb.erreur_aucun_gltf_produit_dans_0":"[ERROR] no .gltf produced in {0}","py.oar2glb.erreur_compilation_du_lanceur_0_1":"[ERROR] launcher compilation:\n{0}{1}","py.oar2glb.erreur_convoar_introuvable_0_utilise_convoar":"[ERROR] convoar not found: {0}\n  convoar.exe is the external converter oar2glb.py needs. Download: {1}\n  Give its location with --convoar PATH (or the CONVOAR variable, or put it in the PATH).","py.oar2glb.erreur_csc_exe_net_framework_4":"[ERROR] csc.exe (.NET Framework 4) not found","py.oar2glb.erreur_gltf_invalide_0_ligne_1":"[ERROR] invalid .gltf: {0}\n  line {1}: {2}","py.oar2glb.erreur_la_sortie_ne_peut_pas":"[ERROR] the output cannot be the original GLB (never overwritten)","py.oar2glb.erreur_reencode_demande_pillow_absent_de":"[ERROR] --reencode needs Pillow, missing from this Python ({0}).\n  Install it in this exact Python: & \"{1}\" -m pip install pillow","py.oar2glb.erreur_terrain_patch_doit_etre_compris":"[ERROR] --terrain-patch must be between 2 and 255 (16-bit indices: (side + 1)² vertices at most 65,536)","py.oar2glb.espace_libre_sur_0_1_1f":"\n  Free space on {0}: {1:.1f} GB","py.oar2glb.etendue_0_objets_de_1_a":"[extent] {0} objects from {1} to {2}  (glTF: X, height, -Y)","py.oar2glb.fin_de_table_llsd_attendue":"end of LLSD map expected","py.oar2glb.fin_de_tableau_llsd_attendue":"end of LLSD array expected","py.oar2glb.force_terrain_oui":"forced (--terrain yes)","py.oar2glb.garder_les_fichiers_intermediaires":"keep the intermediate files","py.oar2glb.garder_les_prims_entierement_transparents_re":"keep fully transparent prims (removed by default)","py.oar2glb.geometrie_du_llmesh_illisible":"unreadable .llmesh geometry","py.oar2glb.glb_0_1":"[GLB] {0} -> {1}","py.oar2glb.glb_0_contient_1_fichier_s":"[GLB] {0} contains {1} file(s): ","py.oar2glb.glb_0_texture_s_absente_s":"[GLB] {0} texture(s) missing out of {1}, replaced by gray. Examples: ","py.oar2glb.glb_fichiers_images_presents_exemples":"[GLB] image files present, examples: ","py.oar2glb.hauteur_max_m_d_un_objet":"maximum height (m) of a root object (skybox beyond), default 600","py.oar2glb.help.convoar":"path of convoar.exe (default: the CONVOAR variable, otherwise convoar from the PATH, otherwise convoar.exe next to oar2glb.py; download: https://github.com/Misterblue/convoar/tree/master/bin)","py.oar2glb.help.oar":"the .oar (or .tgz) file of the region to convert","py.oar2glb.hors_region_node_0_1_a":"[outside region] node {0} '{1}' at {2} removed","py.oar2glb.invisible_node_0_1_retire_2":"[invisible] node {0} '{1}' removed: {2}","py.oar2glb.lanceur_0_compile_1":"[launcher] {0} compiled ({1})","py.oar2glb.lanceur_0_mis_a_jour_loadfromremotesources":"[launcher] {0} updated (loadFromRemoteSources)","py.oar2glb.le_nud_n_a_pas_de":"the node has no mesh","py.oar2glb.les_patches_de_terrain_sont_deja":"the terrain patches are already in this GLB: unchanged","py.oar2glb.libre_aucune_boite_d_objet_ne":"free (no object box contains it)","py.oar2glb.list_paren":" (list: {0})","py.oar2glb.log_0":"[log] {0}","py.oar2glb.lu_dans":"read in ","py.oar2glb.materiau_glb_0_r_couleur_1":"      GLB material: {0!r} color {1} mode {2} image {3}","py.oar2glb.materiaux_transparents_glb":"transparent materials (GLB)","py.oar2glb.ne_pas_attendre_entree_a_la":"do not wait for Enter at the end","py.oar2glb.ne_pas_lancer_convoar_ajouter_le":"do not run convoar: add the full terrain to this GLB (writes X-terrain.glb, the original is never modified)","py.oar2glb.ne_rien_modifier_lister_les_objets":"modify nothing: list the objects of the OAR, their skin and the matching GLB node","py.oar2glb.node_0_nom_1_r_extras":"       node {0}: name={1!r} extras={2} keys={3}","py.oar2glb.non_pas_un_mesh":"no (not a mesh)","py.oar2glb.nud":"node","py.oar2glb.nud_0_1_2_echelle_du":"node {0} '{1}' [{2}]; node scale {3}","py.oar2glb.nud_introuvable":"node not found","py.oar2glb.nud_terrain_sans_min_max_d":"\"Terrain\" node without accessor min/max: coverage unknown, unchanged (--terrain yes to force)","py.oar2glb.oar2glb_0":"[oar2glb] {0}","py.oar2glb.oar2glb_0_2":"oar2glb {0}","py.oar2glb.oar_0_illisible_1":"[OAR] {0} unreadable ({1})","py.oar2glb.oar_0_objets_de_1_a":"[OAR] {0} objects from {1} to {2}  (OpenSim X, Y, Z, Z = height)","py.oar2glb.oar_region_0_g_x_1":"[OAR] region {0:g} x {1:g} m","py.oar2glb.ok_0_1_1f_mo_2":"[OK] {0}  ({1:.1f} MB, {2} meshes, {3} textures, {4} object(s) outside the region removed)","py.oar2glb.pas_de_glb_correspondance_non_evaluee":"no GLB: match not evaluated (--glb)","py.oar2glb.pas_de_nud_terrain_de_convoar":"no convoar \"Terrain\" node: unchanged (--terrain yes to add the patches anyway)","py.oar2glb.reencoder_les_textures_j2k_avant_convoar":"re-encode J2K textures before convoar","py.oar2glb.reperes_0_mat_s_rouge_s":"[markers] {0} red 15 m pole(s) added, one per placed animal","py.oar2glb.rien":"nothing","py.oar2glb.rigge_0_1_ignore":"[rigged] '{0}': {1}, ignored","py.oar2glb.rigge_0_1_morceau_x_echelle":"[rigged] '{0}': {1} piece(s), prim scale {2}, {3:.2f} x {4:.2f} x {5:.2f} m (L x W x H), centered at ({6:.1f}, {7:.1f}), feet at {8:.2f} m ({9})","py.oar2glb.rigge_0_1_non_corrige":"[rigged] '{0}': {1}, not corrected","py.oar2glb.rigge_0_1_nud_glb_introuvable":"[rigged] '{0}' ({1}): GLB node not found, not corrected (see --diag)","py.oar2glb.rigge_0_reconstruit_depuis_l_oar":"[rigged] '{0}' rebuilt from the OAR: {1} face(s), {2} vertices, {3} triangles (convoar: {4} primitive(s), {5} vertices), prim scale ignored {6}, bind_shape scale {7}","py.oar2glb.rigge_0_taille_obtenue_1_2f":"[rigged] '{0}': obtained size {1:.2f} x {2:.2f} x {3:.2f} m implausible (outside {4:g} to {5:g} m), left as convoar produced it","py.oar2glb.sans_bind_shape_matrix":"without bind_shape_matrix","py.oar2glb.sans_extension":"(no extension)","py.oar2glb.sans_textureentry":"without TextureEntry","py.oar2glb.sommets_du_glb_axes_opensim_x":"      GLB vertices (OpenSim axes x, y, z): from {0} to {1}, i.e. {2} m, {3} vertices","py.oar2glb.sommets_du_glb_illisibles_0":"      unreadable GLB vertices ({0})","py.oar2glb.terrain_0":"[terrain] {0}","py.oar2glb.terrain_0_nud_s_terrain_de":"[terrain] {0} convoar \"Terrain\" node(s) removed from the scene","py.oar2glb.terrain_0_nud_s_terrain_retire":"[terrain] {0} \"Terrain\" node(s) removed from the scene (their data stay in the GLB, unused); {1:.1f} MB read, in chunks of at most {2} KB","py.oar2glb.terrain_attention_carte_de_0_x":"[terrain] warning: map of {0} x {1} samples for a region of {2:g} x {3:g} m","py.oar2glb.terrain_aucun_fichier_ecrit":"[terrain] no file written","py.oar2glb.terrain_carte_0_x_1_echantillons":"[terrain] map {0} x {1} samples (1 m); water level {2:g} m ({3}); {4} patch(es) of {5} m; {6} vertices; {7:.1f} MB added; {8:.1f} s","py.oar2glb.terrain_cet_oar_n_a_pas":"[terrain] this OAR has no height map (terrains/*.r32): terrain not generated, nothing is modified","py.oar2glb.terrain_complet_depuis_la_carte_de":"full terrain from the height map: auto = replaces the convoar terrain if it covers less than the map (default), oui = always, non = never","py.oar2glb.terrain_de_convoar_complet_couvre_0":"complete convoar terrain (covers {0:.1f} % of the map): unchanged","py.oar2glb.terrain_de_convoar_incomplet_couvre_0":"incomplete convoar terrain (covers {0:.1f} % of the map)","py.oar2glb.terrain_desactive_terrain_non":"[terrain] disabled (--terrain no)","py.oar2glb.texture_0_alpha_1_2f":"texture {0} alpha {1:.2f}","py.oar2glb.textures_0_1_2_3_0f":"[textures] {0}/{1} ({2} %) - {3:.0f} s","py.oar2glb.textures_0_reencodees_1_illisibles_remplacee":"[textures] {0} re-encoded, {1} unreadable ones replaced by a neutral gray","py.oar2glb.textures_0_sculpt_maps_laissees_intactes":"[textures] {0} sculpt maps left untouched","py.oar2glb.textures_0_textures_a_reencoder_sur":"[textures] {0} textures to re-encode on {1} cores ({2:.0f} s)","py.oar2glb.textures_ecriture_de_0":"[textures] writing {0}...","py.oar2glb.textures_lecture_de_0":"[textures] reading {0}...","py.oar2glb.translation_bind_shape_0":" ; bind_shape translation {0}","py.oar2glb.type_llsd_inconnu_0_r":"unknown LLSD type {0!r}","py.oar2glb.unknown":"unknown","py.oar2glb.unreadable":"unreadable","py.oar2glb.uuid_du_mesh":"mesh UUID","py.oar2glb.uuid_du_prim":"prim UUID","py.oar2glb.var_region_0_objet_s_replace":"[var-region] {0} object(s) moved back to their real position, {1} recognized, {2} not recognized","py.presence.0_1_20_jusqu_au_2":"  {0}. {1:<20} until {2:<17} {3}","py.presence.0_1_2_autres_appareils_du":" · {0}://{1}:{2} (other devices on the network)","py.presence.0_ejecte":"{0} ejected","py.presence.0_id_1_cle_2_ip":"{0} [id {1}, key {2}, ip {3}]","py.presence.adresses_ip_dans_le_journal_masquees":"IP addresses in the log: masked (default), in clear, or absent","py.presence.aucun_bannissement":"(no ban)","py.presence.ban_ip":"banned (IP)","py.presence.banned":"banned","py.presence.banned_line":"{0} banned ({1})","py.presence.bannissement_de_0_leve":"ban on {0} lifted","py.presence.certificat_tls_wss":"TLS certificate (wss://)","py.presence.chat":"chat","py.presence.cle_0_ip_1":"key {0} ip {1}","py.presence.cle_privee_tls":"TLS private key","py.presence.commande_inconnue_0_tape_aide":"unknown command: {0} (type \"aide\")","py.presence.commandes_tape_les_ici_puis_entree":"commands (type them here, then Enter):\n  liste                           connected visitors (no., name, role, room, duration, IP)\n  ejecter <no.|name> [reason]       disconnects the visitor (they can come back)\n  bannir <no.|name> [minutes] [reason]   ejects and bans their key and IP (IPv6: its /64 prefix; default 60 min; 0 = permanent)\n  bans                            current bans\n  debannir <ban no.>           lifts a ban\n  rooms                           known rooms: connected, visits, key (exact case)\n  visits-key <room> [off]         visit log key of a room (new key, or off to remove it; alone: list)\n  creators                        creators (--creators file re-read): prefix, state, open rooms, walkers, origins\n  oublier <name>                  releases a reserved name (its owner loses it; the first to ask for it gets it)\n  pseudos [filtre]                lists the reserved names (owner's #XXXX code, last seen, expiry)\n  version                         version number and revision of this file\n  aide                            this message\n  (a name containing spaces: use the no. from \"liste\")","py.presence.comportement_inapproprie":"inappropriate behavior","py.presence.connexions_simultanees_par_adresse_ip":"simultaneous connections per IP address (IPv6: per /64 prefix)","py.presence.debut":"start","py.presence.deconnexion":"disconnection","py.presence.definitif":"permanent","py.presence.delai_mini_entre_deux_messages_d":"minimum delay between two messages from a visitor (s)","py.presence.derniers_messages_rejoues_aux_nouveaux_arriv":"last messages replayed to newcomers (default 200; 0 = none); older ones are requested in batches of 50 (history message)","py.presence.derriere_un_reverse_proxy_en_tete":"behind a reverse proxy: header carrying the visitor's real IP (e.g. X-Forwarded-For, CF-Connecting-IP); enable only if the server is reachable only through that proxy","py.presence.duree_0_min_1_02d_s":"duration {0} min {1:02d} s","py.presence.ejecte_par_l_hote":"ejected by the host","py.presence.erreur_de_commande_0":"[command error] {0}","py.presence.ev.ban":"ban","py.presence.ev.connect":"connection","py.presence.ev.end":"end","py.presence.ev.kick":"kick","py.presence.ev.name":"name","py.presence.ev.refuse":"refusal","py.presence.ev.empty":"empty","py.presence.ev.http":"http request","py.presence.empty":"connection opened then closed without a request ({0} since the last line for this address; browser preconnection, port test or robot: harmless)","py.presence.http":"GET {1}, host {2}, agent {3}: not a WebSocket opening ({4}) ({0} since the last line for this address; a browser opening the server address, a robot or a test: harmless)","py.presence.ev.raw":"unreadable request","py.presence.raw":"{1}, start '{2}' ({0} since the last line for this address; a robot probing the port: harmless)","py.presence.rawkind.misc":"not an HTTP request","py.presence.rawkind.rdp":"probe of Windows Remote Desktop (RDP)","py.presence.rawkind.tls":"encrypted (https) connection on a port without encryption","py.presence.ev.walk":"walk","py.presence.fichier_de_bannissements_illisible_0_ignore":"[!] ban file unreadable ({0}): ignored","py.presence.fichier_de_journal_tourne_chaque_nuit":"log file (rotated every night); relative path = script folder","py.presence.fichier_des_bannissements_chemin_relatif_dos":"ban file; relative path = script folder","py.presence.help.host":"listening address (0.0.0.0 = all interfaces; 127.0.0.1 = this machine only)","py.presence.help.maxtotal":"simultaneous connections in total, all rooms together","py.presence.help.port":"port the visitors connect to","py.presence.history_days":"days of messages read back and kept in --history-file at startup (default 30; 0 = keep everything)","py.presence.history_file":"chat history file (one JSON line per message: time, name, text, room; never the IP address): read back at startup to keep the history across restarts; off by default. These are personal data","py.presence.history_loaded":"history: {0} message(s) read back, {1} ignored or too old ({2})","py.presence.history_write_error":"history: cannot write ({0})","py.presence.jours_de_journal_conserves":"days of log kept","py.presence.leve":"lifted","py.presence.limite_de_connexions_par_ip":"connection limit per IP","py.presence.list_line":"  #{0:<4} {1:<26} {2:<10} room={3:<16} {4} min {5:02d} s   ip {6}","py.presence.log_line":"{0:<11} | room={1} | {2}","py.presence.longueur_max_d_un_message_de":"maximum length of a chat message","py.presence.messages_max_par_fenetre_de_10":"maximum messages per 10 s window and per visitor","py.presence.moderation_tape_aide_pour_la_liste":"moderation: type \"aide\" for the list of commands (liste, ejecter, bannir, bans, debannir, oublier, pseudos, rooms, visits-key, creators, version)","py.presence.nobody":"(nobody)","py.presence.noms_interdits_a_la_reservation_separes":"names forbidden for reservation, comma-separated (e.g. admin,moderator)","py.presence.old_name":"previous: {0}","py.presence.origines_autorisees_separees_par_des_virgule":"allowed origins, comma-separated (default: all)","py.presence.personne_ne_correspond_a_0_tape":"nobody matches \"{0}\" (type \"liste\")","py.presence.plusieurs_visiteurs_correspondent_utilise_le":"several visitors match, use the number:","py.presence.promeneur_0_dans_le_salon":"walker ({0} in the room)","py.presence.promeneurs_max_par_salon":"maximum walkers per room","py.presence.registre_des_noms_reserves_vide_en":"registry of reserved names (empty = in memory only); relative path = script folder","py.presence.registre_illisible_0_demarrage_a_vide":"[!] registry unreadable ({0}): starting empty","py.presence.role.spectator":"spectator","py.presence.role.walker":"walker","py.presence.salon_plein":"room full","py.presence.serveur_adresse_a_donner_a_presence":"server | address to give to --presence-url: {0}://{1}:{2}","py.presence.serveur_adresses_a_donner_a_presence":"server | addresses to give to --presence-url: {0}://127.0.0.1:{1} (this machine)","py.presence.serveur_de_presence_glb2html_websocket":"presence_server.py {0}: glb2html presence server (WebSocket): visitors, chat, moderation.","py.presence.serveur_journal_0_registre_des_noms":"server | log: {0} | name registry: {1}","py.presence.serveur_n_utilise_jamais_0_0":"server | never use 0.0.0.0 in --presence-url: it is a listening address, not a destination","py.presence.star_hint":"server | or {0}://*:{1}: the same name as the page that connects (advised if your pages are opened through several addresses: localhost, network, public name)","py.presence.serveur_presence_server_0_ecoute_sur":"server | presence_server {0} | listening on {1}:{2}  (Ctrl+C to stop)","py.presence.spectateurs_vue_globale_max_tous_salons":"maximum spectators (global view), all rooms","py.presence.spectator_paren":"(spectator)","py.presence.trop_de_messages_patiente_quelques_secondes":"Too many messages, please wait a few seconds.","py.presence.trop_de_spectateurs":"too many spectators","py.presence.un_nom_non_utilise_depuis_ce":"a name unused for this many days is released","py.presence.until_date":"until {0}","py.presence.usage_ban":"usage: ban <#|name> [minutes] [reason]","py.presence.usage_kick":"usage: kick <#|name> [reason]","py.presence.usage_unban":"usage: unban <number from “bans”>","py.presence.ev.forget":"name released","py.presence.forget_done":"name “{0}” released: the first browser to ask for it will get it","py.presence.forget_logged":"former owner #{0}","py.presence.forget_none":"no reserved name matches “{0}”","py.presence.forget_online":"(its former owner is connected: the displayed name does not change before their next connection)","py.presence.usage_forget":"usage: oublier <name>   (the name as you like: case, accents and spaces do not matter)","py.presence.names_head":"reserved names ({0}):","py.presence.names_line":"  {0} #{1}  last seen {2}, released on {3} if unused{4}","py.presence.names_none":"(no reserved name)","py.presence.names_online":"(connected)","py.presence.zone":"zone","py.stats.0_16_mediane_1_1f_90":"{0:>16}: median {1:,.1f} | 90 % of blocks under {2:,.1f} | maximum {3:,.1f}","py.stats.attention_geometrie_compressee_0_les_mo":"Warning: compressed geometry ({0}): the MB of geometry above are the decoded size, not the file's.","py.stats.aucun_mesh_positionnable_accessors_sans_min":"No placeable mesh (accessors without min/max?).","py.stats.bloc_0_1_2_1f_mo":"  block {0},{1}: {2:.1f} MB of geometry, {3} triangles, {4} instances, {5:.1f} MB of textures","py.stats.blocs_de_0_0f_m_1":"== Blocks of {0:.0f} m: {1} non-empty (instance center; geometry and textures without duplicates within the block) ==","py.stats.ce_fichier_n_est_pas_un":"This file is not a GLB.","py.stats.cote_des_blocs_en_metres_defaut":"block side in meters (default 256)","py.stats.cout_de_la_reutilisation_entre_blocs":"== Cost of reuse between blocks ==","py.stats.desc":"glb-stats.py: quick analysis of a GLB, whatever its size. Reads only the JSON header (never the binary data or the textures): a few seconds and very little memory.","py.stats.ecrit_aussi_le_rapport_dans_ce":"also writes the report to this file (UTF-8)","py.stats.etendue":"== Extent ==","py.stats.fichier_0_1_1f_mo_en":"File: {0} ({1:,.1f} MB; JSON header read: {2:,.1f} MB)","py.stats.geometrie_accessors_uniques_0_1f_mo":"Geometry (unique accessors): {0:,.1f} MB | Embedded textures: {1:,.1f} MB | Rest: {2:,.1f} MB","py.stats.geometrie_mo":"geometry (MB)","py.stats.geometrie_utilisee_par_plusieurs_blocs_0":"Geometry used by several blocks: {0:,.1f} MB ({1:.0f} % of the total) | textures used by several blocks: {2:,.1f} MB ({3:.0f} % of the total): size of a shared library loaded once.","py.stats.help.glb":"the .glb file to analyze","py.stats.le_premier_bloc_du_glb_n":"The first GLB chunk is not JSON.","py.stats.les_5_blocs_les_plus_lourds":"The 5 blocks heaviest in geometry:","py.stats.meshes_reutilises_plusieurs_fois_0_materiaux":"Meshes reused several times: {0} | materials: {1} | textures (images): {2} (used: {3})","py.stats.nud_0_1_2_0f_m":"  - node {0} \"{1}\": {2:.0f} m, {3} mesh(es)","py.stats.nuds_parcourus_0_meshes_1_utilises":"Nodes visited: {0} | meshes: {1} (used: {2}) | mesh instances: {3}","py.stats.objets_racine_0_plus_grands_qu":"Root objects: {0} | larger than a {1:.0f} m block: {2}","py.stats.poids_estime_octets_lus_dans_l":"== Estimated weight (bytes read from the header, without decoding) ==","py.stats.somme_des_blocs_geometrie_0_1f":"Sum of blocks: geometry {0:,.1f} MB (against {1:,.1f} MB without duplicates across the whole file): difference = extra cost if shared meshes are duplicated in each block.","py.stats.sommets_uniques_0_sommets_rendus_instances":"Unique vertices: {0:,} | rendered vertices (instances included): {1:,} | rendered triangles: {2:,}","py.stats.taux_de_reutilisation_sommets_rendus_uniques":"Reuse ratio (rendered / unique vertices): {0:.1f}","py.stats.x_0_1f_a_1_1f":"X: {0:.1f} to {1:.1f} ({2:.0f} m) | Z: {3:.1f} to {4:.1f} ({5:.0f} m) | height Y: {6:.1f} to {7:.1f}","py.presence.help.visits":"visit log file (one JSON line per visit, no IP; empty = no log; path relative to the script's folder)","py.presence.help.visits_days":"days of visits kept in this log (0 = all)","py.presence.help.visits_names":"also record walkers' nicknames in the visit log","py.presence.help.visits_keys":"file of the visit log access keys (fingerprints only, path relative to the script's folder)","py.presence.ev.visits":"visits","py.presence.visits.rate":"too many key attempts","py.presence.visits.badkey":"key refused","py.presence.visits.granted":"summary sent","py.presence.visits.yes":"yes","py.presence.visits.no":"no","py.presence.visits_on":"server: visit log {0} (kept {1} days, 0 = all; nicknames: {2})","py.presence.visits_write_err":"visit log {0}: cannot write ({1})","py.presence.vkey.unreadable":"unreadable visit keys file: {0} (starting without keys)","py.presence.help.creators":"file of allowed creators (origins of their pages, room prefix, limits; re-read on change, path relative to the script's folder); absent: everyone is accepted","py.presence.cr.bad":"creators: entry {0} ignored (missing or invalid id: letters, digits, - and _, 32 at most)","py.presence.cr.badprefix":"creators: entry {0} ignored (invalid prefix {1}: letters, digits, space, - and _, no dot)","py.presence.cr.dup":"creators: entry {0} ignored ({1} already used by a previous entry)","py.presence.cr.nulljson":"creators: {0}: origin null written without quotes, ignored (write \"null\" in quotes for a page opened from the disk)","py.presence.cr.origindup":"creators: origin {0} already belongs to {1}, ignored for {2}","py.presence.cr.missing":"creators file missing: {0}; every connection is refused until it exists","py.presence.cr.unreadable":"unreadable creators file: {0} ({1}); previous list kept","py.presence.cr.loaded":"creators: {0} read from {1}","py.presence.cr.on":"server: creators {0} ({1}); a page from another origin is refused","py.presence.cr.off":"no creators file (start the server with --creators FILE): every page is accepted","py.presence.cr.none":"no valid creator in {0}: every connection is refused","py.presence.cr.line":"  {0:<16} prefix: {1}   {2}   open rooms: {3}{4}   walkers: {5}{6}","py.presence.cr.noprefix":"(none: all other rooms)","py.presence.cr.active":"active","py.presence.cr.suspended":"suspended","py.presence.cr.max":" / {0} at most","py.presence.cr.origins":"      origins: {0}","py.presence.cr.noorigin":"(none)","py.presence.cr.refuse.origin":"undeclared origin: {0}","py.presence.cr.refuse.off":"creator {0} suspended","py.presence.cr.refuse.room":"room {0} outside the rooms of {1}","py.presence.cr.refuse.rooms":"{0}: already {1} open rooms","py.presence.vkey.none":"no visit log key","py.presence.vkey.line":"  room \"{0}\": key created on {1}","py.presence.vkey.unknown":"no key for room \"{0}\"","py.presence.vkey.off":"key of room \"{0}\" removed","py.presence.vkey.new":"visit log key of room \"{0}\": {1}\n  (shown only once; give it to the creator with their page address followed by #visits; the old key no longer works)","py.presence.vkey.inactive":"warning: the visit log is off (start the server with --visits FILE)","py.presence.vkey.case":"warning: no visit and no visitor for room \"{0}\"; room known with a different case: {1}. Case matters: run visits-key again with the exact name (this key stays valid for \"{0}\").","py.presence.rooms.none":"no known room (no connected visitor, no recorded visit, no key)","py.presence.rooms.line":"  {0:<24} connected: {1} ({2} walking)   visits: {3}{4}   key: {5}","py.presence.rooms.last":", last on {0}","py.presence.rooms.novisits":"  (visit log off: start the server with --visits FILE to count visits)","py.presence.rooms.note":"  (exact case; a room never visited and without a key is not shown: its name is the room value of NAME.config.json, the page name by default)"},"fr":{"_name":"Français","py.common.help":"afficher ce message d'aide et quitter","py.common.lang_help":"langue des messages et de l'aide : fr, en ou auto (défaut : langue du système ; variable d'environnement WEB3D_LANG équivalente). Disponibles : {0}","py.common.optionals":"options","py.common.positionals":"arguments","py.common.version_mark":"{0}, empreinte {1}","py.common.version":"afficher la version et quitter","py.glb2html.0_1_fichiers_generes":"{0}/{1} fichiers générés","py.glb2html.0_cle_s_changee_s":"{0} clé(s) changée(s)","py.glb2html.0_gardee_s_telle_s_quelle":", {0} gardée(s) telle(s) quelle(s)","py.glb2html.0_gltf_version_1_non_supportee":"{0} : glTF version {1} non supportée","py.glb2html.0_introuvable":"{0} introuvable","py.glb2html.0_pas_un_glb_magic_absent":"{0} : pas un GLB (magic absent)","py.glb2html.0_premier_chunk_non_json":"{0} : premier chunk non JSON","py.glb2html.0_reference_des_fichiers_externes_1":"{0} : référence des fichiers externes {1} -> repacker en GLB autonome (npx @gltf-transform/cli copy in.gltf out.glb)","py.glb2html.0_taille_annoncee_1_taille_fichier":"{0} : taille annoncée {1} != taille fichier {2} (tronqué ?)","py.glb2html.0_textures_ktx2_basis_non_gerees":"{0} : textures KTX2/Basis non gérées hors ligne -> npx @gltf-transform/cli png in.glb out.glb","py.glb2html.absent_paren":" (absent)","py.glb2html.adresse_de_la_page_de_cette":"adresse de la page de cette région (défaut : le nom du fichier .html, relatif)","py.glb2html.adresse_s_de_regions_json_partage":"adresse(s) de regions.json partagé(s), séparées par des virgules : la page les relit à chaque ouverture (http/https), les fusionne et complète avec la carte intégrée. Un autre site doit autoriser l'accès (CORS)","py.glb2html.afficher_le_nom_de_l_element":"afficher le nom de l'élément cliqué","py.glb2html.amplitude_vagues_0_10":"amplitude vagues 0..10","py.glb2html.aucun_glb_dans_0":"Aucun .glb dans {0}","py.glb2html.aucune_cle_changee":"aucune clé changée","py.glb2html.avertissement_0_0_0_0_est":"[AVERTISSEMENT] 0.0.0.0 est une adresse d'écoute du serveur, pas une destination : remplacée par 127.0.0.1 -> {0}","py.glb2html.avertissement_0_existe_et_differe_de":"[AVERTISSEMENT] {0} existe et diffère de la coquille de cette version : conservée (les autres régions la partagent). Supprime-la pour la renouveler","py.glb2html.avertissement_0_introuvable_a_cote_de":"[AVERTISSEMENT] {0} introuvable à côté de la page (la région n'a ni .glb ni tuiles ici)","py.glb2html.avertissement_0_tuile_s_listee_s":"[AVERTISSEMENT] {0} tuile(s) listée(s) dans {1} introuvable(s) à côté de lui (première : {2}) ; la page les signalera et réessaiera","py.glb2html.avertissement_default_ignore_sans_shared_shell":"Avertissement : --default est ignoré sans --shared-shell.","py.glb2html.avertissement_des_zones_sont_liees_a":"[AVERTISSEMENT] des zones sont liées à un élément du modèle (champ mesh), mais {0} a été écrit sans références d'objets (glb2tiles avant la v32) : ces zones seront ignorées par la page (avertissement en console). Refaire le découpage avec glb2tiles v32 pour en profiter.","py.glb2html.avertissement_map_page_ignore_aucune_region":"[AVERTISSEMENT] --map-page ignoré : aucune région à afficher (donne --register pour enregistrer cette région, ou --map)","py.glb2html.avertissement_map_page_ignore_aucune_region_2":"[AVERTISSEMENT] --map-page ignoré : aucune région à afficher (donne --register ou --map)","py.glb2html.avertissement_presence_url_doit_commencer_pa":"[AVERTISSEMENT] --presence-url doit commencer par ws:// ou wss:// (reçu : {0})","py.glb2html.avertissement_region_name_region_url_region":"[AVERTISSEMENT] --region-name, --region-url, --region-xy, --region-spawn et --thumb ne servent qu'avec --register : ignorés","py.glb2html.avertissement_register_et_map_page_ne":"[AVERTISSEMENT] --register et --map-page ne s'appliquent qu'à un fichier .glb, pas à un dossier","py.glb2html.avertissement_title_est_ignore_en_mode":"[AVERTISSEMENT] --title est ignoré en mode modulaire : le titre de la page est le salon (--room) de la config","py.glb2html.avertissement_vignette_ignoree_jpg_png_webp":"[AVERTISSEMENT] vignette ignorée (jpg/png/webp de 140 Ko maximum attendus) : {0}","py.glb2html.avertissement_vignette_introuvable_0":"[AVERTISSEMENT] vignette introuvable : {0}","py.glb2html.avertissement_vue_d_ensemble_0_introuvable":"[AVERTISSEMENT] vue d'ensemble {0} introuvable à côté de {1} ; la page fonctionnera sans elle","py.glb2html.avertissement_zones_live_est_ignore_en":"[AVERTISSEMENT] --zones-live est ignoré en mode modulaire : les zones sont toujours relues dans <page>.zones.json","py.glb2html.cache_telechargement_0":"[cache] téléchargement {0}","py.glb2html.image_nombre":"[image] « {0} » : {1} existe, le nom reste « {0} » (la page cherche le fichier toute seule)","py.glb2html.image_completee":"[image] « {0} » → {1}","py.glb2html.image_plusieurs":"[image] « {0} » → {1} ({2} fichiers correspondent : le premier par ordre alphabétique est pris)","py.glb2html.image_sans_fichier":"[image] « {0} » : aucun fichier « {0}.jpg », « {0}-… » dans {1} (nom laissé tel quel)","py.glb2html.carte_0_ajoutee_ou_mise_a":"[carte] « {0} » ajoutée ou mise à jour dans {1} ({2} région(s))","py.glb2html.carte_0_n_est_pas_a":"[carte] {0} n'est pas à côté de la page {1} (un chemin relatif de --register est cherché dans le dossier de lancement, sinon dans celui des outils). Pour l'écrire à côté de la page : donne un chemin complet, ou mets la région à jour avec --update (chemins relatifs à la page)","py.glb2html.carte_0_region_s_lue_s":"[carte] {0} région(s) lue(s) dans {1}","py.glb2html.carte_avec_maj_les_chemins_relatifs":"[carte] avec --update, les chemins relatifs de --register, --map, --map-page et --thumb sont relatifs au dossier de la page : {0}","py.glb2html.carte_des_mondes":"Carte des mondes","py.glb2html.carte_page_carte_0_region_s":"[carte] page carte ({0} région(s)) -> {1}","py.glb2html.ce_n_est_pas_un_fichier":"ce n'est pas un fichier de réglages du viewer","py.glb2html.ce_n_est_pas_un_objet":"ce n'est pas un objet JSON","py.glb2html.chat_entre_visiteurs_necessite_presence_url":"chat entre visiteurs (nécessite --presence-url ; touche Entrée en promenade)","py.glb2html.cible_camera_x_y_z":"cible caméra x,y,z","py.glb2html.compass":"boussole en haut de la page : cap de l'avatar (de la caméra en vue globale) avec le point cardinal et les degrés (défaut : activée)","py.glb2html.coquille_0_absente_ecrite":"coquille {0} absente : écrite","py.glb2html.coquille_0_deja_a_jour_identique":"coquille {0} déjà à jour (identique à celle de {1})","py.glb2html.coquille_0_deja_presente_et_identique":"[coquille] {0} déjà présente et identique","py.glb2html.coquille_0_ecrite":"[coquille] {0} écrite","py.glb2html.coquille_0_plus_ancienne_que_1":"coquille {0} plus ancienne que {1} : renouvelée, ancienne copie gardée sous {2}. Cette coquille est partagée par les autres régions du dossier : elles gardent leur comportement (les anciennes configurations restent comprises)","py.glb2html.coquille_commune_0_adresse_1":"coquille commune {0} ; adresse : {1}","py.glb2html.coquille_modulaire_marqueur_s_non_remplace":"coquille modulaire : marqueur(s) non remplacé(s) {0}","py.glb2html.couleur_ciel_ex_87ceeb":"couleur ciel, ex 87ceeb","py.glb2html.couleur_mer_ex_3a9ad9":"couleur mer, ex 3a9ad9","py.glb2html.default_json_ecrit":"default.json écrit : {0} (région par défaut : {1})","py.glb2html.default_region":"avec --shared-shell : cette région devient la région par défaut (default.json), ouverte quand l'adresse n'a pas de ?region= ; sans cette option default.json n'est écrit que s'il n'existe pas encore","py.glb2html.demi_largeur_du_fondu_du_trou":"demi-largeur du fondu du trou","py.glb2html.desc":"glb2html.py {0} : fabrique la page web d'une région à partir d'un .glb (ou de tuiles), met une région à jour, l'enregistre dans la carte des mondes.","py.glb2html.dessine_aussi_les_arrivees_dans_la":"dessine aussi les arrivées dans la page (petit marqueur discret au sol ; défaut : jamais)","py.glb2html.direction_camera_x_y_z":"direction caméra x,y,z","py.glb2html.distance_5_a_200_m_defaut":"distance (5 à 500 m, défaut 150) jusqu'à laquelle l'infobulle, le clic, le repère de portail (cône) et le nom affiché (showName) des zones marchent en promenade","py.glb2html.entree_gltf_repacker_d_abord_en":"Entrée .gltf : repacker d'abord en .glb (npx @gltf-transform/cli copy in.gltf out.glb)","py.glb2html.epilog":"Exemples :\n  python glb2html.py ile.glb\n  python glb2html.py ile.glb -o ile.html --hole 90 --wave 1.2 --sea-y -30 --zoom 1.3\n  python glb2html.py ile.glb --shared-shell -o Ile.html --presence-url ws://ADRESSE:8765\n  python glb2html.py -o Ile.html --shared-shell --update --zone-info-dist 60\n  python glb2html.py dossier_glb/ --no-sea\nAu premier lancement, three.js est téléchargé une fois dans ~/.cache/glb2html (ou --vendor FOLDER : aucun téléchargement).","py.glb2html.erreur_0":"[ERREUR] {0}","py.glb2html.erreur_0_entree_de_tuile_invalide":"[ERREUR] {0} : entrée de tuile invalide ({1}) : « file » doit être un chemin relatif .glb (sans .. ni :), « min » et « max » trois nombres","py.glb2html.erreur_0_illisible_1":"[ERREUR] {0} illisible ({1})","py.glb2html.erreur_0_introuvable":"[ERREUR] {0} introuvable","py.glb2html.erreur_0_introuvable_cherche_dans_1":"[ERREUR] {0} introuvable (cherché dans {1} puis dans {2})","py.glb2html.erreur_0_introuvable_vendor_doit_pointer":"[ERREUR] {0} introuvable (--vendor doit pointer sur la racine du paquet npm three)","py.glb2html.erreur_0_liste_tiles_absente_ou":"[ERREUR] {0} : liste « tiles » absente ou vide (fichier écrit par glb2tiles.py attendu)","py.glb2html.erreur_0_ou_1_introuvable_genere":"[ERREUR] {0} ou {1} introuvable : génère d'abord la région avec --shared-shell","py.glb2html.erreur_0_ou_1_introuvable_genere_2":"[ERREUR] {0} ou {1} introuvable : génère d'abord la page avec --modular","py.glb2html.erreur_0_overview_invalide_1_file":"[ERREUR] {0} : « overview » invalide ({1}) : « file » doit être un chemin relatif .glb (sans .. ni :)","py.glb2html.erreur_aucune_region_a_afficher_donne":"[ERREUR] aucune région à afficher : donne --map regions.json","py.glb2html.erreur_avec_maj_o_designe_la":"[ERREUR] avec --update, -o désigne la région (ex. -o Region.html), pas un dossier","py.glb2html.erreur_avec_tiles_o_designe_la":"[ERREUR] avec --tiles, -o désigne la région (ex. -o Region.html), pas un dossier","py.glb2html.erreur_config_only_demande_o_page":"[ERREUR] --config-only demande -o <page.html> (la page modulaire déjà générée)","py.glb2html.erreur_enregistrer_une_region_sans_glb":"[ERREUR] enregistrer une région sans .glb demande --region-name, --region-url et --room","py.glb2html.erreur_fichier_de_reglages_0_introuvable":"[ERREUR] fichier de réglages {0} introuvable (cherché dans {1} puis dans {2})","py.glb2html.erreur_lib_url_refuse":"Erreur : --lib-url « {0} » refusé (attendu : chemin relatif comme ../lib, ou adresse http(s) complète, sans ? # \\ ni guillemet).","py.glb2html.erreur_maj_0_introuvable_la_region":"[ERREUR] --update : {0} introuvable, la région n'a pas encore été générée. Génère-la d'abord, sans --update : {1}","py.glb2html.erreur_maj_0_introuvable_si_la":"[ERREUR] --update : {0} introuvable. Si la région utilise une coquille commune, donne --shared-shell NAME.html (par défaut {1})","py.glb2html.erreur_maj_demande_o_region_html":"[ERREUR] --update demande -o <Region.html> (la région déjà générée)","py.glb2html.erreur_maj_et_settings_s_excluent":"[ERREUR] --update et --settings s'excluent : --update ne reprend que les options données et la config existante","py.glb2html.erreur_nom_de_region_0_refuse":"[ERREUR] nom de région « {0} » refusé par la coquille commune (un seul nom de fichier, sans / \\ : ? # ni .., sans point au début)","py.glb2html.erreur_nom_de_region_0_refuse_2":"[ERREUR] nom de région « {0} » refusé par la coquille commune","py.glb2html.erreur_nom_de_region_0_refuse_3":"[ERREUR] nom de région « {0} » refusé par la coquille commune (un seul nom de fichier, sans / \\ : ? # ni .., sans point au début) : choisis un autre -o","py.glb2html.erreur_region_xy_attend_deux_nombres":"[ERREUR] --region-xy attend deux nombres : X,Y","py.glb2html.erreur_settings_sans_nom_demande_le":"[ERREUR] --settings sans nom demande le .glb (le fichier cherché est <nom du .glb>.reglages.json)","py.glb2html.erreur_shared_shell_attend_un_nom":"[ERREUR] --shared-shell attend un fichier .html (nom, ou chemin FOLDER/index.html pour des régions en sous-dossiers) (reçu « {0} »)","py.glb2html.erreur_telechargement_impossible_0_utilise_v":"[ERREUR] téléchargement impossible ({0}). Utilise --vendor <dossier three>.","py.glb2html.erreur_tiles_demande_o_region_html":"[ERREUR] --tiles demande -o <Region.html> (son nom sans extension est celui de la région)","py.glb2html.erreur_tiles_remplace_le_glb_ne":"[ERREUR] --tiles remplace le .glb : ne donne pas de fichier .glb avec --tiles","py.glb2html.erreur_zones_only_demande_o_page":"[ERREUR] --zones-only demande -o <page.html>","py.glb2html.erreur_zones_only_demande_zones_fichier":"[ERREUR] --zones-only demande --zones FILE (ou --settings) : aucune zone à écrire","py.glb2html.erreur_zones_only_demande_zones_live":"[ERREUR] --zones-only demande --zones-live (page autonome) ou une page modulaire déjà générée ({0} introuvable à côté de la page)","py.glb2html.fichier_glb_ou_dossier_de_glb":"fichier .glb ou dossier de .glb","py.glb2html.fichier_json_de_zones_exporte_par":"fichier .json de zones exporté par le viewer ; chemin relatif : cherché dans le dossier de lancement, puis dans le dossier du script. Une zone peut porter un champ mesh (nom exact d'un élément du modèle) : l'élément devient cliquable","py.glb2html.scan.help":"dossier des sites (coquille commune à la racine) : met à jour son regions.json avec les régions trouvées (NOM.config.json) et leurs vignettes (NOM.jpg, .png ou .webp à côté) ; garde les noms, places, arrivées, l'en-tête et les fiches externes ; ne supprime rien","py.glb2html.scan.dryhelp":"avec --scan-sites : affiche les changements sans rien écrire","py.glb2html.scan.nofolder":"[ERREUR] dossier introuvable : {0}","py.glb2html.scan.noshell":"[AVERTISSEMENT] pas de index.html dans {0} : les adresses index.html?region=… des fiches demandent la coquille à la racine","py.glb2html.scan.badcfg":"[AVERTISSEMENT] {0} illisible, ignoré : {1}","py.glb2html.scan.add":"  + {0} ({1}), place {2},{3}","py.glb2html.scan.upd":"  ~ {0} : {1}","py.glb2html.scan.orphan":"  ? {0} : {1} introuvable dans le dossier, fiche gardée","py.glb2html.scan.summary":"regions.json : {0} ajoutée(s), {1} mise(s) à jour, {2} inchangée(s), {3} externe(s) gardée(s), {4} orpheline(s) -> {5}","py.glb2html.scan.dry":"--dry-run : rien n'a été écrit","py.glb2html.fichier_regions_json_a_mettre_a":"fichier regions.json à mettre à jour avec CETTE région (ajoutée ou mise à jour par salon) ; relatif : dossier de lancement s'il y existe, sinon dossier du script. La page générée embarque la carte à jour","py.glb2html.fichier_regions_json_carte_des_mondes":"fichier regions.json (carte des mondes : nom, adresse, position, vignette) exporté par le viewer ; chemin relatif : dossier de lancement, puis dossier du script","py.glb2html.finesse_du_maillage_de_la_mer":"finesse du maillage de la mer 8..1000 (maille = 4000/segments ; seulement avec --anim)","py.glb2html.format_attendu_x_y_z":"format attendu : x,y,z","py.glb2html.gabarit_modulaire_cible_introuvable_ou_multi":"gabarit modulaire : cible introuvable ou multiple ({0}…)","py.glb2html.genere_aussi_une_page_web_carte":"génère aussi une page web « carte des mondes » (liens cliquables vers chaque région) ; sans .glb : génère seulement cette page depuis --map. Relatif : à côté de la page de la région","py.glb2html.haute_resolution_rendu_x2_minimum_supersampl":"haute résolution : rendu x2 minimum (supersampling, plus net mais ~4x plus lourd)","py.glb2html.hauteur_des_yeux_en_m_promenade":"hauteur des yeux en m (promenade)","py.glb2html.hauteur_mer_150_60":"hauteur mer -150..60","py.glb2html.help.anim":"animer la mer (vagues) ; --no-anim : mer fixe","py.glb2html.help.light":"la page s'ouvre en rendu léger (résolution divisée par deux, 15 images/s au plus, vue d'ensemble seule en vue globale, sans anticrénelage) tant que le visiteur n'a rien choisi dans Réglages ; --no-light : rendu normal","py.glb2html.help.sea":"afficher la mer (--no-sea : sans mer)","py.glb2html.identifiant_du_point_d_arrivee_des":"identifiant du point d'arrivée des visiteurs dans cette région (défaut : default)","py.glb2html.inclure_le_mode_promenade_touche_f":"inclure le mode promenade (touche F) dans la page","py.glb2html.la_page_recharge_ses_zones_a":"la page recharge ses zones à chaque ouverture depuis un fichier .zones.json placé à côté d'elle (servie en http/https ; sinon les zones intégrées servent). Sans NAME : <page>.zones.json. Le fichier est écrit par le script, filtré selon --profile","py.glb2html.le_fichier_glb_ou_le_dossier":"le fichier .glb (ou le dossier) est obligatoire","py.glb2html.lib_url":"chemin relatif (../lib) ou adresse http(s) complète où trouver three.js et ses modules ; écrit dans la ligne « const LIB » de la coquille (modifiable à la main ; --update la garde) quand elle est écrite et retenu dans la config pour --update. Chemin relatif : lib/ y est créé s'il manque ; adresse complète : rien n'est copié","py.glb2html.m_charger_les_tuiles_dont_la":"m : charger les tuiles dont la boîte est à moins de ce rayon de l'avatar, en plan X,Z (défaut %(default)g ; ?radius=NNN dans l'adresse pour essayer)","py.glb2html.m_decharger_les_tuiles_au_dela":"m : décharger les tuiles au-delà de rayon + marge (défaut %(default)g)","py.glb2html.maj_0_absent_ou_incomplet_ecrit":"[update] {0}/ absent ou incomplet : écrit","py.glb2html.maj_0_conserve_tel_quel":"[update] {0} conservé tel quel","py.glb2html.maj_0_mis_a_jour_glb2html":"[update] {0} mis à jour (glb2html {1}) : ","py.glb2html.maj_0_present_conserve":"[update] {0}/ présent : conservé","py.glb2html.maj_0_remplace_par_1":"[update] {0} remplacé par {1}","py.glb2html.maj_le_profil_ne_filtre_les":"[update] le profil ne filtre les zones qu'à l'écriture de la liste de zones : ajoute --zones FILE pour la réécrire","py.glb2html.maj_lib_repris":"[update] dossier lib repris de la ligne « const LIB » de la coquille : {0}","py.glb2html.marqueur_des_portails_et_zones_libres":"marqueur des portails et zones libres dans la page : dot (défaut : disque de 0,4 m et anneau fin), range (anneau fin et net au rayon réel de la zone, visible de loin) ou none ; les anciennes valeurs discret, portee et aucun restent acceptées. Les arrivées ne sont jamais dessinées (voir --show-spawns)","py.glb2html.met_a_jour_une_region_deja":"met à jour une région déjà générée (-o REGION.html [--shared-shell [SHELL.html]] [--tiles X.tiles.json | X.glb]) : lit X.config.json, n'applique QUE les options données sur la ligne, garde tout le reste et X.zones.json (réécrit seulement avec --zones), écrit la version courante et renouvelle la coquille si elle est plus ancienne (ancienne copie gardée sous un nom daté). Échoue si X.config.json n'existe pas","py.glb2html.mo_de_tuiles_chargees_en_meme":"Mo de tuiles chargées en même temps (poids des fichiers ; défaut %(default)g) ; au-delà, les plus lointaines partent d'abord","py.glb2html.mode_modulaire_a_coquille_commune_une":"mode modulaire à coquille commune : une seule coquille (défaut {0}) sert plusieurs régions, à l'adresse SHELL.html?region=NAME. -o désigne la région (NAME = son nom sans extension, ex. -o Ankh.html) : seuls NAME.glb, NAME.config.json et NAME.zones.json sont écrits, plus la coquille, lib/three-X/ et (la première fois) default.json s'ils sont absents (une coquille existante n'est jamais écrasée). Avec un chemin (--shared-shell FOLDER/index.html), -o peut être dans un sous-dossier de FOLDER : adresse SHELL.html?region=sous/dossier/NAME. --register écrit cette adresse dans regions.json. Implique --modular","py.glb2html.mode_modulaire_ecrit_une_coquille_page":"mode modulaire : écrit une coquille <page>.html identique pour toutes les régions (elle déduit ses fichiers de son nom) + <page>.glb (octets bruts) + <page>.config.json (réglages) + <page>.zones.json (zones, relues à chaque ouverture ; à défaut zones.json du dossier) + lib/three-X/ partagé (Draco et Meshopt compris). Demande http(s) pour l'ouverture (pas depuis le disque)","py.glb2html.nom_affiche_dans_la_carte_defaut":"nom affiché dans la carte (défaut : nom du .glb)","py.glb2html.materiaux_rendus_opaques":"noms de matériaux rendus opaques (ils masquent alors ce qui est derrière), séparés par des virgules : \"1471516\" = tout nom qui contient ce texte, \"=pbrmat-123\" = nom exact ; \"\" = aucun","py.glb2html.noms_a_ignorer_en_collision_separes":"noms à ignorer en collision, séparés par des virgules : \"door\" = début de mot, \"=mesh_346_5\" = nom exact ; \"\" = rien","py.glb2html.north":"décalage en degrés ajouté au cap affiché ; 0 = le nord est la direction -Z du modèle (OpenSim) ; pour un GLB qui ne vient pas d'OpenSim (défaut 0)","py.glb2html.ok_0_1_2_2f_mo":"[OK] {0} -> {1} ({2:.2f} Mo glb, {3:.2f} Mo html) [glb2html {4}]","py.glb2html.ok_0_1_2_3_coquille":"[OK] {0} -> {1} + {2} + {3}, coquille commune {4} ; adresse : {5} [glb2html {6}]","py.glb2html.ok_0_1_modulaire_coquille_2":"[OK] {0} -> {1} (modulaire : coquille {2:.0f} Ko + {3} {4:.2f} Mo + {5} + {6} + {7}/) [glb2html {8}]","py.glb2html.ok_0_tuile_s_1_2":"[OK] {0} tuile(s) -> {1} + {2}, ","py.glb2html.ok_region_mise_a_jour_adresse":"[OK] région mise à jour ; adresse : {0} [glb2html {1}]","py.glb2html.ok_reglages_0_coquille_et_glb":"[OK] réglages -> {0} (coquille et .glb inchangés) [glb2html {1}]","py.glb2html.panneau_de_reglages_pour_les_visiteurs":"panneau de réglages pour les visiteurs (haute résolution, mer animée, force des vagues), bouton en haut à droite","py.glb2html.petit_cone_pointe_vers_le_bas":"petit cône pointé vers le bas au-dessus de chaque portail et de chaque zone « enter » ou « both » (repère visible jusqu'à --zone-info-dist ; touche T pour l'afficher ou le masquer ; défaut : affiché ; les arrivées n'en ont qu'avec --show-spawns)","py.glb2html.position_sur_la_grille_comme_opensim":"position sur la grille, comme OpenSim (X vers l'est, Y vers le nord), ex. 1000,1001","py.glb2html.position_x_du_centre_du_trou":"position X du centre du trou (monde)","py.glb2html.position_z_du_centre_du_trou":"position Z du centre du trou (monde)","py.glb2html.public_retire_les_zones_privees_ex":"public : retire les zones privées (ex. Home Assistant) ; private : les garde (ancienne valeur perso acceptée)","py.glb2html.racine_d_un_paquet_npm_three":"racine d'un paquet npm three local (sinon cache + téléchargement)","py.glb2html.ratio_de_cadrage_1_cadrage_auto":"ratio de cadrage (1 = cadrage auto)","py.glb2html.rayon_du_trou_30_600_zone":"rayon du trou 30..600 (zone plate = rayon - fondu)","py.glb2html.reecrit_seulement_les_zones_sans_regenerer":"réécrit seulement les zones, sans régénérer le HTML : <page>.zones.json d'une page modulaire déjà générée (avec --zones FILE), ou, avec --zones-live, le fichier de zones d'une page autonome","py.glb2html.reecrit_seulement_page_config_json_d":"réécrit seulement <page>.config.json d'une page modulaire déjà générée (indiquée par -o), sans toucher au .glb ni à la coquille ; les visiteurs rechargent. <page>.zones.json n'est réécrit que si --zones est donné. Avec --register, met aussi la carte à jour","py.glb2html.region_decoupee_en_tuiles_par_glb2tiles":"région découpée en tuiles par glb2tiles.py : pas de .glb en entrée ; -o désigne la région. Écrit X.config.json (champ « tiles »), X.zones.json, la coquille et lib/ ; X.tiles.json et ses tuiles ne sont copiés que s'ils ne sont pas déjà à côté de la page. Implique --modular. Repère = celui du modèle d'origine (aucun recentrage) ; zones liées à un objet : possibles si les tuiles viennent de glb2tiles v32, ignorées sinon","py.glb2html.reglages_0_parametre_s_repris_de":"[réglages] {0} paramètre(s) repris de {1}","py.glb2html.reprend_tous_les_reglages_enregistres_par":"reprend TOUS les réglages enregistrés par le viewer (bouton « Enregistrer dans un fichier » : trou, vagues, caméra, zones, fiche de région, vignette…). Sans nom : <nom du .glb>.reglages.json. Les options de la ligne de commande l'emportent. Relatif : dossier de lancement, puis dossier du script","py.glb2html.rotation_de_la_region_autour_de":"rotation de la région autour de l'axe vertical (0, 90, 180 ou 270 degrés), appliquée au chargement avant le recentrage. Les zones, arrivées, cible et trou du fichier de zones / de réglages sont DÉJÀ dans le repère tourné (le viewer les fait tourner avec la région)","py.glb2html.salon_de_presence_defaut_nom_du":"salon de présence (défaut : nom du fichier)","py.glb2html.secondes_avant_disparition_des_messages_et":"secondes avant disparition des messages et bulles ; 0 = restent jusqu'à ce que de nouveaux messages les remplacent","py.glb2html.serveur_de_presence_ws_ou_wss":"serveur de présence ws:// ou wss:// (voir presence_server.py) ; « * » à la place du nom = le même nom que la page (ws://*:8765, conseillé pour une page ouverte par plusieurs adresses) ; vide = désactivé","py.glb2html.seuil_alpha_feuillage_0_0_5":"seuil alpha feuillage 0..0.5","py.glb2html.shell_name":"coquille {0}","py.glb2html.sortie_fichier_html_ou_dossier_cree":"sortie : fichier .html, ou dossier (créé si besoin). Entrée dossier : dossier de sortie. Défaut : \"<nom> - Offline.html\" à côté du .glb","py.glb2html.telechargements_simultanes_defaut_default_d":"téléchargements simultanés (défaut %(default)d)","py.glb2html.titre_de_la_page":"titre de la page","py.glb2html.triangles_de_tuiles_chargees_en_meme":"triangles de tuiles chargées en même temps (défaut %(default)d)","py.glb2html.tuiles_0_copie_dans_1_tuiles":"[tuiles] {0} copié dans {1} ; tuiles : {2} copiée(s) ({3:.1f} Mo), {4} déjà présente(s) de même taille (ni vérifiées ni recopiées){5}","py.glb2html.tuiles_0_tuile_s_et_1":"[tuiles] {0} tuile(s) et {1} déjà à côté de la page : rien n'est copié{2}","py.glb2html.tuiles_cible_de_camera_par_defaut":"[tuiles] cible de caméra par défaut : {0} (centre de l'étendue, repère du modèle d'origine ; --target pour la changer)","py.glb2html.tuiles_des_zones_sont_liees_a":"[tuiles] des zones sont liées à un objet (champ mesh) : la page les place avec l'objet dès que la tuile qui le contient est chargée","py.glb2html.tuiles_hauteur_de_la_mer_par":"[tuiles] hauteur de la mer par défaut : 20 m (repère du modèle d'origine, comme l'eau d'OpenSim ; --sea-y pour la changer, --no-sea pour la retirer)","py.glb2html.vignette_de_la_region_fichier_jpg":"vignette de la région : fichier jpg/png/webp de 140 Ko maximum (intégré), ou adresse http(s) (gardée telle quelle, carte plus légère)","py.glb2html.vitesse_de_marche_en_m_s":"vitesse de marche en m/s (Maj = x2.2)","py.glb2html.voir_les_visiteurs_en_promenade_depuis":"voir les visiteurs en promenade depuis la vue globale (se connecte dès l'ouverture de la page ; actif par défaut dès qu'une --presence-url est donnée ; --no-spectate pour l'éviter)","py.glb2html.vol_en_promenade_touche_f_ou":"vol en promenade (touche F ou Début ; Page Haut / E monte, Page Bas / C descend) : activé par défaut, --no-fly le retire","py.glb2html.vue_d_ensemble_0_placee_avec":" ; vue d'ensemble {0} placée avec les tuiles","py.glb2html.zones_0_non_modifie_donne_zones":"[zones] {0} non modifié (donne --zones FILE pour le réécrire)","py.glb2html.zones_0_zone_s_lue_s":"[zones] {0} zone(s) lue(s) dans {1}","py.glb2html.zones_0_zone_s_profil_1":"[zones] {0} zone(s), profil {1} -> {2}","py.glb2html.zones_zones_deja_en_place_0":"[zones] zones déjà en place : {0} (non réécrit)","py.glb2html.zones_zones_deja_en_place_0_2":"[zones] zones déjà en place : {0} (lu pour vérification, non réécrit ni copié)","py.glb2tiles.0_1_0f_m_du_centre":"« {0} » ({1:.0f} m du centre, étendue {2:.0f} m)","py.glb2tiles.0_1_2f_mo_2_triangles":"  - « {0} » : {1:.2f} Mo, {2} triangles, étendue (X x Y x Z) {3}, {4} instance(s)","py.glb2tiles.0_distance_1_0f_m_etendue":"  - « {0} » : distance {1:.0f} m, étendue {2:.0f} m","py.glb2tiles.0_illisible_1":"{0} illisible ({1}).","py.glb2tiles.0_instance_s_aberrante_s_a":"{0} instance(s) aberrante(s) (à plus de {1:g} m du centre médian ou d'étendue supérieure) : {2}.","py.glb2tiles.0_introuvable_vue_ensemble_seule_suppose":"{0} introuvable : --overview-only suppose que le découpage a déjà été fait (dans {1}).","py.glb2tiles.0_nud_s_avec_camera_ou":"{0} nœud(s) avec caméra ou extensions de nœud : ces champs ne sont pas recopiés dans les tuiles.","py.glb2tiles.0_objet_s_au_nom_correspondant":"  {0} objet(s) au nom correspondant conservé(s) par les garde-fous (trop de triangles ou de meshes)","py.glb2tiles.0_octet_gagne_toute_la_geometrie":"  0 octet gagné : toute la géométrie et toutes les images des objets exclus sont partagées avec des objets conservés (même primitive ou même texture, typiquement un cube commun) ; retirer ces objets enlève des nœuds et des triangles, pas des octets.","py.glb2tiles.0_scenes_seule_la_scene_1":"{0} scènes : seule la scène {1} est découpée.","py.glb2tiles.accessor_0_accessor_sparse_non_gere":"Accessor {0} : accessor « sparse » non géré par glb2tiles.","py.glb2tiles.accessor_0_bytestride_1_plus_petit":"Accessor {0} : byteStride ({1}) plus petit qu'un élément ({2}).","py.glb2tiles.accessor_0_depasse_son_bufferview_fichier":"Accessor {0} : dépasse son bufferView (fichier invalide).","py.glb2tiles.accessor_0_indices_avec_bytestride_non":"Accessor {0} : indices avec byteStride non gérés.","py.glb2tiles.accessor_0_inexistant":"Accessor {0} inexistant.","py.glb2tiles.accessor_0_positions_non_gerees":"Accessor {0} : positions non gérées.","py.glb2tiles.accessor_0_sans_bufferview_valeurs_a":"Accessor {0} : sans bufferView (valeurs à zéro) non géré par glb2tiles.","py.glb2tiles.accessor_0_type_1_2_inconnu":"Accessor {0} : type {1}/{2} inconnu.","py.glb2tiles.accessor_0_type_d_indices_non":"Accessor {0} : type d'indices non géré.","py.glb2tiles.accessor_0_un_indice_depasse_le":"Accessor {0} : un indice dépasse le nombre de sommets ({1}) : fichier invalide.","py.glb2tiles.analyse_0_primitives_distinctes_a_mesurer":"[analyse] {0} primitives distinctes à mesurer (lecture des indices par morceaux)","py.glb2tiles.aucun_mesh_positionnable_dans_la_scene":"Aucun mesh positionnable dans la scène : rien à découper.","py.glb2tiles.avec_exclure_meshes_au_plus_dans":"avec --exclude : meshes au plus dans l'objet racine (défaut 1)","py.glb2tiles.avec_exclure_triangles_au_plus_dans":"avec --exclude : triangles au plus dans l'objet racine, tous meshes compris (défaut 24)","py.glb2tiles.avertissement_0_d_une_execution_precedente":"Avertissement : {0} d'une exécution précédente n'est pas retiré, mais l'index ne le mentionne plus (--no-overview).","py.glb2tiles.avertissement_0_existe_deja_mais_ses":"Avertissement : {0} existe déjà mais ses tuiles ne portent pas les références d'objets (glb2tiles avant la v32) : pour lier des zones à des objets en mode tuiles, refaire le découpage.","py.glb2tiles.avertissement_ces_tuiles_ont_ete_ecrites":"Avertissement : ces tuiles ont été écrites sans les références d'objets (glb2tiles avant la v32) : les zones liées à un objet restent ignorées en mode tuiles. Refaire le découpage (sans --overview-only) pour en profiter.","py.glb2tiles.bufferview_0_inexistant":"bufferView {0} inexistant.","py.glb2tiles.bufferview_0_seul_le_tampon_0":"bufferView {0} : seul le tampon 0 est géré.","py.glb2tiles.ce_glb_est_compresse":"Ce GLB est compressé (","py.glb2tiles.cellules_sur_la_plus_grande_dimension":"cellules sur la plus grande dimension d'une primitive pour le regroupement de sommets (défaut %(default)d)","py.glb2tiles.cote_des_blocs_de_la_section":"côté des blocs de la section glb-stats de --analyse (défaut 256)","py.glb2tiles.cote_minimal_d_une_cellule_en":"côté minimal d'une cellule en m (défaut 16)","py.glb2tiles.couleurs_moyenne_de_texture_pour_0":"  couleurs : moyenne de texture pour {0} image(s), {1} illisible(s) (couleur de base)","py.glb2tiles.couleurs_pillow_absent_couleur_de_base":"  couleurs : Pillow absent, couleur de base du matériau ({0} matériau(x) texturé(s) concerné(s)) ; installer Pillow pour les couleurs moyennes","py.glb2tiles.decoupage_prevu_budget_0_g_mo":"== Découpage prévu (budget {0:g} Mo, {1} triangles, cellule minimale {2:g} m) ==","py.glb2tiles.decouper_meme_si_la_recommandation_est":"découper même si la recommandation est « pas de découpage »","py.glb2tiles.des_primitives_portent_des_extensions_elles":"Des primitives portent des extensions : elles ne sont pas recopiées dans les tuiles.","py.glb2tiles.desc":"glb2tiles.py {0} : découpe un GLB énorme en tuiles autonomes et écrit X.tiles.json et la vue d'ensemble X.overview.glb (Python standard seulement).","py.glb2tiles.dossier_de_sortie_defaut_a_cote":"dossier de sortie (défaut : à côté du GLB)","py.glb2tiles.duplication_reelle_de_la_geometrie_somme":"Duplication réelle de la géométrie (somme des tuiles / géométrie unique) : {0}","py.glb2tiles.entree_pour_fermer":"Entrée pour fermer...","py.glb2tiles.epilog":"Exemples :\n  python glb2tiles.py Region.glb --analyse\n  python glb2tiles.py Region.glb --budget 32 --budget-triangles 1500000\n  python glb2tiles.py Region.glb --overview-only\nLe journal est glb2tiles.log, écrit à côté du script. glb-stats.py doit se trouver à côté de ce script.","py.glb2tiles.erreur_0":"[ERREUR] {0}","py.glb2tiles.etendue_des_instances_plus_grande_dimension":"Étendue des instances (plus grande dimension) : instances et triangles au-dessus de chaque seuil","py.glb2tiles.etendue_minimale_effective_0_g_m":"  étendue minimale effective {0:g} m (seuil demandé {1:g} m), résolution {2}, pas du terrain {3:g} m (demandé {4:g} m)","py.glb2tiles.expression_reguliere_invalide_pour_exclure_0":"Expression régulière invalide pour --exclude : {0!r} ({1}).","py.glb2tiles.fichier_glb_tronque":"Fichier GLB tronqué.","py.glb2tiles.glb2tiles_0":"[glb2tiles] {0}","py.glb2tiles.glb2tiles_0_1_1f_mo":"[glb2tiles] {0} : {1:.1f} Mo","py.glb2tiles.glb2tiles_0_2":"glb2tiles {0}","py.glb2tiles.glb2tiles_ne_lit_pas_les_glb":") : glb2tiles ne lit pas les GLB compressés (hors de son périmètre). Décompresser le GLB d'abord, puis relancer.","py.glb2tiles.glb_d_entree":"GLB d'entrée","py.glb2tiles.glb_introuvable_0":"GLB introuvable : {0}","py.glb2tiles.glb_stats_py_introuvable_a_cote":"glb-stats.py introuvable à côté de glb2tiles.py ({0}) : le copier au même endroit.","py.glb2tiles.image_externe_uri_non_geree_seuls":"Image externe (uri) non gérée : seuls les GLB à images intégrées le sont.","py.glb2tiles.images_vides_ou_invalides_remplacees_par":"Images vides ou invalides remplacées par un PNG gris de {0} : {1} distincte(s), {2} occurrence(s) (une occurrence = une image écrite dans une tuile) ; matériaux et coordonnées de texture inchangés.","py.glb2tiles.la_tuile_0_n_a_plus":"La tuile {0} n'a plus le contenu de {1} : utiliser les mêmes options que pour le découpage d'origine.","py.glb2tiles.la_vue_d_ensemble_depasse_la":"La vue d'ensemble dépasse la limite de 4 Go d'un GLB.","py.glb2tiles.le_decoupage_recalcule_0_tuiles_ne":"Le découpage recalculé ({0} tuiles) ne correspond pas à {1} ({2} tuiles) : utiliser les mêmes options (--budget, --budget-triangles, --min, --entier-*, --exclude…) que pour le découpage d'origine.","py.glb2tiles.le_tampon_0_a_une_adresse":"Le tampon 0 a une adresse (uri) : seuls les GLB à tampon intégré sont gérés.","py.glb2tiles.lecture_0_octets_lus_sur_1":"Lecture : {0} octets lus sur {1} (plus grande lecture {2} octets; positions relues pour {3} octets, primitives qui partagent un tampon de sommets).","py.glb2tiles.lecture_hors_du_tampon_du_glb":"Lecture hors du tampon du GLB (décalage {0}, {1} octets) : fichier invalide ou tronqué.","py.glb2tiles.lecture_seule_mesures_decoupage_prevu_recomm":"lecture seule : mesures, découpage prévu, recommandation ; n'écrit rien","py.glb2tiles.les_10_instances_les_plus_eloignees":"== Les 10 instances les plus éloignées du centre médian (X {0:.0f} m, Z {1:.0f} m) ==","py.glb2tiles.les_10_meshes_les_plus_lourds":"== Les 10 meshes les plus lourds (octets compactés, sommets réellement utilisés) ==","py.glb2tiles.log_0":"[log] {0}","py.glb2tiles.m_distance_ou_etendue_au_dela":"m : distance ou étendue au-delà de laquelle une instance est signalée (défaut 1000)","py.glb2tiles.m_etendue_maximale_d_un_objet":"m : étendue maximale d'un objet racine gardé entier (défaut 256)","py.glb2tiles.m_les_objets_dont_la_plus":"m : les objets dont la plus grande dimension est plus petite sont omis (défaut %(default)g) ; le budget peut le relever","py.glb2tiles.m_pas_du_reseau_du_terrain":"m : pas du réseau du terrain dans la vue d'ensemble (défaut %(default)g)","py.glb2tiles.m_si_le_budget_oblige_a":"m : si le budget oblige à omettre des objets plus grands, la résolution baisse (défaut %(default)g)","py.glb2tiles.machine_big_endian_non_geree":"Machine big-endian non gérée.","py.glb2tiles.mesh_0_primitive_sans_position_non":"Mesh {0} : primitive sans POSITION non gérée.","py.glb2tiles.mesures_de_glb_stats":"== Mesures de glb-stats ==","py.glb2tiles.mo_par_tuile_defaut_32":"Mo par tuile (défaut 32)","py.glb2tiles.mo_poids_maximal_de_la_vue":"Mo : poids maximal de la vue d'ensemble (défaut %(default)g)","py.glb2tiles.mo_sous_ce_poids_et_sous":"Mo : sous ce poids (et sous --threshold-triangles) « pas de découpage » (défaut 150)","py.glb2tiles.mo_un_objet_racine_plus_leger":"Mo : un objet racine plus léger et plus petit que --whole-extent reste entier (défaut 16)","py.glb2tiles.n_ecrire_que_x_overview_glb":"n'écrire que X.overview.glb (et sa mention dans X.tiles.json) : les tuiles existantes ne sont pas réécrites ; les paramètres de découpage doivent être ceux du découpage d'origine","py.glb2tiles.ne_pas_attendre_entree_a_la":"ne pas attendre Entrée à la fin","py.glb2tiles.ne_pas_ecrire_extras_ref_extras":"ne pas écrire extras.ref / extras.box dans les nœuds des tuiles (format de la v31 : les zones liées à un objet sont alors ignorées en mode tuiles)","py.glb2tiles.ne_pas_ecrire_x_overview_glb":"ne pas écrire X.overview.glb (vue d'ensemble légère de toute la région)","py.glb2tiles.nud_0":"nœud {0}","py.glb2tiles.nud_0_mesh_1_inexistant":"Nœud {0} : mesh {1} inexistant.","py.glb2tiles.objets_exclus_exclure_au_plus_0":"Objets exclus (--exclude, au plus {0} triangles et {1} mesh(es) par objet racine) : {2} | triangles retirés : {3} | octets gagnés : {4} ({5:.1f} Mo)","py.glb2tiles.objets_omis_0_trop_petits_etendue":"  objets omis : {0} trop petits (étendue sous le seuil), {1} par le budget, {2} avec squelette ; primitives translucides omises : {3}","py.glb2tiles.objets_racine_0_gardes_entiers_1":"Objets racine : {0} | gardés entiers : {1} (dont {2} avec skin) | répartis instance par instance : {3}","py.glb2tiles.objets_racine_gardes_entiers_0_repartis":"Objets racine gardés entiers : {0} | répartis : {1}","py.glb2tiles.octets_des_exclus_qu_un_objet":"  octets des exclus qu'un objet conservé utilise aussi (non gagnés) : {0} ({1:.1f} Mo)","py.glb2tiles.poids_mo_mediane_0_1f_90":"Poids (Mo) : médiane {0:.1f} | 90 % sous {1:.1f} | maximum {2:.1f}","py.glb2tiles.poids_par_tuile_mo_mediane_0":"Poids par tuile (Mo) : médiane {0:.1f} | 90 % sous {1:.1f} | maximum {2:.1f}","py.glb2tiles.primitive_les_attributs_n_ont_pas":"Primitive : les attributs n'ont pas tous {0} sommets (accessor {1}).","py.glb2tiles.rapport":"== Rapport ==","py.glb2tiles.recommandation_decouper_budget_0_g_mo":"Recommandation : découper : budget {0:g} Mo, {1} tuiles, duplication {2}.","py.glb2tiles.recommandation_pas_de_decoupage_necessaire_0":"Recommandation : pas de découpage nécessaire ({0:.1f} Mo sous {1:g} Mo et {2} triangles sous {3}).","py.glb2tiles.references_d_objets_extras_ref_extras":"Références d'objets (extras.ref, extras.box) : {0} nœud(s) nommé(s), {1} nom(s) partagé(s) par plusieurs nœuds (référence nom#index) : zones liées à un objet possibles en mode tuiles.","py.glb2tiles.references_d_objets_non_ecrites_sans":"Références d'objets non écrites (--no-refs) : les zones liées à un objet seront ignorées en mode tuiles.","py.glb2tiles.retire_du_decoupage_les_objets_racine":"retire du découpage les objets racine dont le nom correspond (insensible à la casse, répétable), à condition de respecter --exclude-max-triangles et --exclude-max-meshes","py.glb2tiles.rien_n_est_ecrit_forcer_pour":"Rien n'est écrit (--force pour découper quand même).","py.glb2tiles.sans_instance":"sans instance","py.glb2tiles.sans_vue_ensemble_et_vue_ensemble":"--no-overview et --overview-only s'excluent.","py.glb2tiles.skin_0_inexistant":"Skin {0} inexistant.","py.glb2tiles.temps_0_1f_s":"[temps] {0:.1f} s","py.glb2tiles.temps_0_1f_s_1_octets":"[temps] {0:.1f} s ; {1} octets lus sur {2}","py.glb2tiles.texture_0_inexistante":"Texture {0} inexistante.","py.glb2tiles.triangles_de_la_vue_d_ensemble":"triangles de la vue d'ensemble (défaut %(default)d)","py.glb2tiles.triangles_mediane_0_90_sous_1":"Triangles : médiane {0} | 90 % sous {1} | maximum {2}","py.glb2tiles.triangles_par_tuile_defaut_1500000":"triangles par tuile (défaut 1500000)","py.glb2tiles.triangles_par_tuile_mediane_0_90":"Triangles par tuile : médiane {0} | 90 % sous {1} | maximum {2}","py.glb2tiles.triangles_pour_la_recommandation_pas_de":"triangles pour la recommandation « pas de découpage » (défaut 3000000)","py.glb2tiles.tuile_0_1_2f_go_au":"Tuile {0} : {1:.2f} Go, au-delà de la limite de 4 Go d'un GLB.","py.glb2tiles.tuile_0_hors_budget_1_1f":"Tuile {0} hors budget ({1:.1f} Mo, {2} triangles) : {3}. Un mesh unique plus grand qu'une cellule ne peut pas être réparti à ce stade.","py.glb2tiles.tuiles_0_dans_1":"Tuiles : {0} dans {1}","py.glb2tiles.tuiles_0_duplication_prevue_geometrie_1":"Tuiles : {0} | duplication prévue : géométrie {1}, images {2}","py.glb2tiles.tuiles_d_une_execution_precedente_absentes":"Tuiles d'une exécution précédente absentes du nouvel index : {0} fichier(s) T_*.glb supprimé(s)","py.glb2tiles.vue_d_ensemble_0_1_1f":"Vue d'ensemble {0} : {1:.1f} Mo, {2} triangles (dont terrain {3}), {4} objet(s) gardés sur {5}, en {6:g} s","py.glb2tiles.vue_d_ensemble_0_1f_mo":"[vue d'ensemble] {0:.1f} Mo, {1} triangles, {2} objet(s) sur {3}, {4} tuile(s) en {5:.1f} s","py.glb2tiles.vue_d_ensemble_budget_0_g":"[vue d'ensemble] budget {0:g} Mo et {1} triangles, seuil d'étendue {2:g} m, résolution {3}, pas du terrain {4:g} m","py.glb2tiles.vue_d_ensemble_budget_atteint_avant":"[vue d'ensemble] budget atteint avant des objets de {0:.0f} m : résolution réduite à {1}","py.glb2tiles.vue_d_ensemble_terrain_0_piece":"[vue d'ensemble] terrain : {0} pièce(s), {1} triangles, réseau de {2:g} m","py.glb2tiles.vue_d_ensemble_terrain_trop_lourd":"[vue d'ensemble] terrain trop lourd pour la moitié du budget : pas porté à {0:g} m","py.glb2tiles.warning_prefix":"Avertissement : ","py.oar2glb.0_5d_1_2_3_rigge":"{0:5d} | {1} | {2} | {3} | riggé : {4} | échelle du prim {5} | échelle bind_shape {6} | transparent : {7} | boîte racine d'animesh : {8} | GLB : {9}","py.oar2glb.0_face_s_a_part":" (+{0} face(s) à part)","py.oar2glb.accesseur_0_non_gere":"accesseur {0} non géré","py.oar2glb.accesseur_0_non_gere_float_vec3":"accesseur {0} non géré (float VEC3 simple attendu)","py.oar2glb.accesseur_position_0_bufferview_1_buffer":"      accesseur POSITION {0} ; bufferView {1} ; buffer {2} {3} o ; 3 premiers sommets {4}","py.oar2glb.ajouter_un_mat_rouge_de_15":"ajouter un mât rouge de 15 m à chaque animal riggé posé (pour le retrouver dans le viewer)","py.oar2glb.altitude_de_la_racine":"altitude de la racine","py.oar2glb.args":"[args]","py.oar2glb.aucune":"aucune","py.oar2glb.aucune_geometrie":"aucune géométrie","py.oar2glb.avec_diag_glb_ou_gltf_a":"avec --diag : GLB ou .gltf à comparer ; défaut : le .gltf du dossier <oar>-GLTF (conservé par --keep), sinon le .glb voisin","py.oar2glb.avec_terrain_seul_fichier_glb_de":"avec --terrain-only : fichier GLB de sortie (défaut : X-terrain.glb à côté de l'original)","py.oar2glb.bind_shape_matrix_0":"      bind_shape_matrix : {0}","py.oar2glb.bind_shape_matrix_non_inversible":"bind_shape_matrix non inversible","py.oar2glb.bloc_skin_present_mais_illisible":"bloc skin présent mais illisible","py.oar2glb.boite_racine_d_animesh":"boîte racine d'animesh","py.oar2glb.cle_llsd_attendue":"clé LLSD attendue","py.oar2glb.controle_0_pieds_a_1_2f":"[contrôle] '{0}' pieds à {1:.2f} m, centre {2:.2f} m : ","py.oar2glb.convoar":"[convoar]","py.oar2glb.convoar_0_image_s_annoncee_s":"[convoar] {0} image(s) annoncée(s) par le .gltf mais absente(s) du dossier (exemples : {1}) : nouvel essai {2}/{3}, les images déjà écrites sont conservées","py.oar2glb.convoar_0_image_s_recuperee_s":"[convoar] {0} image(s) récupérée(s) de l'essai précédent","py.oar2glb.convoar_code_retour_0":"[convoar] code retour {0}","py.oar2glb.correctif_0_mesh_es_rigge_s":"[correctif] {0} mesh(es) riggé(s) remis à l'échelle, {1} prim(s) invisible(s) retiré(s)","py.oar2glb.cote_d_un_patch_de_terrain":"côté d'un patch de terrain en mètres, 2 à 255 (défaut {0})","py.oar2glb.dans_la_boite_de_0_objet":"dans la boîte de {0} objet(s) : {1}","py.oar2glb.defaut_d_opensim_aucun_waterheight_dans":"défaut d'OpenSim, aucun WaterHeight dans settings/","py.oar2glb.desc":"oar2glb.py {0} : convertit une sauvegarde de région OpenSim (.oar) en un seul GLB (convoar, réparation, terrain complet, empaquetage).","py.oar2glb.dessous_de_la_boite_racine":"dessous de la boîte racine","py.oar2glb.diag_0_objet_s_1_partie":"[diag] {0} objet(s), {1} partie(s) ; terrain {2} ; {3}","py.oar2glb.diag_nuds_glb_dont_tous_les":"[diag] nœuds GLB dont tous les matériaux sont transparents : {0}","py.oar2glb.diag_pos":"      position {0} ; terrain {1} ; {2}","py.oar2glb.diag_rigges_0_transparents_1_boites":"[diag] riggés : {0} ; transparents : {1} ; boîtes racines d'animesh : {2} ; nœuds GLB trouvés : {3}/{4}","py.oar2glb.diag_uuid_lisibles_dans_les_nuds":"[diag] UUID lisibles dans les nœuds GLB : {0} ; exemples de nœuds :","py.oar2glb.domaine_de_position_du_mesh_0":"      domaine de position du mesh ({0} sous-maillage(s)) : ","py.oar2glb.echelle_du_prim_appliquee_0":" ; échelle du prim appliquée : {0}","py.oar2glb.en_tete_du_mesh_illisible_0":"en-tête du mesh illisible ({0})","py.oar2glb.entree_pour_fermer":"Entrée pour fermer...","py.oar2glb.epilog":"Exemples :\n  python oar2glb.py \"P:\\chemin\\MaRegion.oar\"\n  python oar2glb.py \"P:\\chemin\\MaRegion.oar\" --keep --markers\n  python oar2glb.py \"P:\\chemin\\MaRegion.oar\" --diag        (ne modifie rien, ne lance pas convoar)\n  python oar2glb.py --terrain-only MaRegion.glb \"P:\\chemin\\MaRegion.oar\"","py.oar2glb.erreur_0_introuvable":"[ERREUR] {0} introuvable","py.oar2glb.erreur_0_introuvable_annonce_par_le":"[ERREUR] {0} introuvable (annoncé par le .gltf).\n  {1} contient {2} fichier(s), dont {3} .buf : ","py.oar2glb.erreur_0_le_premier_chunk_n":"[ERREUR] {0} : le premier chunk n'est pas JSON","py.oar2glb.erreur_0_le_tampon_0_n":"[ERREUR] {0} : le tampon 0 n'est pas celui du chunk BIN","py.oar2glb.erreur_0_n_est_pas_un":"[ERREUR] {0} n'est pas un GLB","py.oar2glb.erreur_0_n_est_pas_un_2":"[ERREUR] {0} n'est pas un GLB version 2","py.oar2glb.erreur_0_tronque":"[ERREUR] {0} tronqué","py.oar2glb.erreur_0_vecteurs_de_mauvaise_taille":"[ERREUR] {0} vecteurs de mauvaise taille : nombres écrits avec virgule décimale.\n  ","py.oar2glb.erreur_aucun_gltf_produit_dans_0":"[ERREUR] aucun .gltf produit dans {0}","py.oar2glb.erreur_compilation_du_lanceur_0_1":"[ERREUR] compilation du lanceur :\n{0}{1}","py.oar2glb.erreur_convoar_introuvable_0_utilise_convoar":"[ERREUR] convoar introuvable : {0}\n  convoar.exe est le convertisseur externe dont oar2glb.py a besoin. Téléchargement : {1}\n  Indiquer son emplacement avec --convoar CHEMIN (ou la variable CONVOAR, ou le mettre dans le PATH).","py.oar2glb.erreur_csc_exe_net_framework_4":"[ERREUR] csc.exe (.NET Framework 4) introuvable","py.oar2glb.erreur_gltf_invalide_0_ligne_1":"[ERREUR] .gltf invalide : {0}\n  ligne {1} : {2}","py.oar2glb.erreur_la_sortie_ne_peut_pas":"[ERREUR] la sortie ne peut pas être le GLB d'origine (jamais écrasé)","py.oar2glb.erreur_reencode_demande_pillow_absent_de":"[ERREUR] --reencode demande Pillow, absent de ce Python ({0}).\n  Installe-le dans ce Python précis : & \"{1}\" -m pip install pillow","py.oar2glb.erreur_terrain_patch_doit_etre_compris":"[ERREUR] --terrain-patch doit être compris entre 2 et 255 (indices 16 bits : (côté + 1)² sommets au plus 65 536)","py.oar2glb.espace_libre_sur_0_1_1f":"\n  Espace libre sur {0} : {1:.1f} Go","py.oar2glb.etendue_0_objets_de_1_a":"[étendue] {0} objets de {1} à {2}  (glTF : X, hauteur, -Y)","py.oar2glb.fin_de_table_llsd_attendue":"fin de table LLSD attendue","py.oar2glb.fin_de_tableau_llsd_attendue":"fin de tableau LLSD attendue","py.oar2glb.force_terrain_oui":"forcé (--terrain yes)","py.oar2glb.garder_les_fichiers_intermediaires":"garder les fichiers intermédiaires","py.oar2glb.garder_les_prims_entierement_transparents_re":"garder les prims entièrement transparents (retirés par défaut)","py.oar2glb.geometrie_du_llmesh_illisible":"géométrie du .llmesh illisible","py.oar2glb.glb_0_1":"[GLB] {0} -> {1}","py.oar2glb.glb_0_contient_1_fichier_s":"[GLB] {0} contient {1} fichier(s) : ","py.oar2glb.glb_0_texture_s_absente_s":"[GLB] {0} texture(s) absente(s) sur {1}, remplacée(s) par du gris. Exemples : ","py.oar2glb.glb_fichiers_images_presents_exemples":"[GLB] fichiers images présents, exemples : ","py.oar2glb.hauteur_max_m_d_un_objet":"hauteur max (m) d'un objet racine (skybox au-delà), défaut 600","py.oar2glb.help.convoar":"chemin de convoar.exe (défaut : variable CONVOAR, sinon convoar du PATH, sinon convoar.exe à côté de oar2glb.py ; téléchargement : https://github.com/Misterblue/convoar/tree/master/bin)","py.oar2glb.help.oar":"fichier .oar (ou .tgz) de la région à convertir","py.oar2glb.hors_region_node_0_1_a":"[hors région] node {0} '{1}' à {2} retiré","py.oar2glb.invisible_node_0_1_retire_2":"[invisible] node {0} '{1}' retiré : {2}","py.oar2glb.lanceur_0_compile_1":"[lanceur] {0} compilé ({1})","py.oar2glb.lanceur_0_mis_a_jour_loadfromremotesources":"[lanceur] {0} mis à jour (loadFromRemoteSources)","py.oar2glb.le_nud_n_a_pas_de":"le nœud n'a pas de mesh","py.oar2glb.les_patches_de_terrain_sont_deja":"les patches de terrain sont déjà dans ce GLB : inchangé","py.oar2glb.libre_aucune_boite_d_objet_ne":"libre (aucune boîte d'objet ne le contient)","py.oar2glb.list_paren":" (liste : {0})","py.oar2glb.log_0":"[log] {0}","py.oar2glb.lu_dans":"lu dans ","py.oar2glb.materiau_glb_0_r_couleur_1":"      matériau GLB : {0!r} couleur {1} mode {2} image {3}","py.oar2glb.materiaux_transparents_glb":"matériaux transparents (GLB)","py.oar2glb.ne_pas_attendre_entree_a_la":"ne pas attendre Entrée à la fin","py.oar2glb.ne_pas_lancer_convoar_ajouter_le":"ne pas lancer convoar : ajouter le terrain complet à ce GLB (écrit X-terrain.glb, l'original n'est jamais modifié)","py.oar2glb.ne_rien_modifier_lister_les_objets":"ne rien modifier : lister les objets de l'OAR, leur skin et le nœud GLB correspondant","py.oar2glb.node_0_nom_1_r_extras":"       node {0} : nom={1!r} extras={2} clés={3}","py.oar2glb.non_pas_un_mesh":"non (pas un mesh)","py.oar2glb.nud":"nœud","py.oar2glb.nud_0_1_2_echelle_du":"nœud {0} '{1}' [{2}] ; échelle du nœud {3}","py.oar2glb.nud_introuvable":"nœud introuvable","py.oar2glb.nud_terrain_sans_min_max_d":"nœud « Terrain » sans min/max d'accesseur : couverture inconnue, inchangé (--terrain yes pour forcer)","py.oar2glb.oar2glb_0":"[oar2glb] {0}","py.oar2glb.oar2glb_0_2":"oar2glb {0}","py.oar2glb.oar_0_illisible_1":"[OAR] {0} illisible ({1})","py.oar2glb.oar_0_objets_de_1_a":"[OAR] {0} objets de {1} à {2}  (X, Y, Z OpenSim, Z = hauteur)","py.oar2glb.oar_region_0_g_x_1":"[OAR] région {0:g} x {1:g} m","py.oar2glb.ok_0_1_1f_mo_2":"[OK] {0}  ({1:.1f} Mo, {2} meshes, {3} textures, {4} objet(s) hors région retiré(s))","py.oar2glb.pas_de_glb_correspondance_non_evaluee":"pas de GLB : correspondance non évaluée (--glb)","py.oar2glb.pas_de_nud_terrain_de_convoar":"pas de nœud « Terrain » de convoar : inchangé (--terrain yes pour ajouter les patches quand même)","py.oar2glb.reencoder_les_textures_j2k_avant_convoar":"réencoder les textures J2K avant convoar","py.oar2glb.reperes_0_mat_s_rouge_s":"[repères] {0} mât(s) rouge(s) de 15 m ajouté(s), un par animal posé","py.oar2glb.rien":"rien","py.oar2glb.rigge_0_1_ignore":"[riggé] '{0}' : {1}, ignoré","py.oar2glb.rigge_0_1_morceau_x_echelle":"[riggé] '{0}' : {1} morceau(x), échelle du prim {2}, {3:.2f} x {4:.2f} x {5:.2f} m (L x l x h), centré en ({6:.1f}, {7:.1f}), pieds à {8:.2f} m ({9})","py.oar2glb.rigge_0_1_non_corrige":"[riggé] '{0}' : {1}, non corrigé","py.oar2glb.rigge_0_1_nud_glb_introuvable":"[riggé] '{0}' ({1}) : nœud GLB introuvable, non corrigé (voir --diag)","py.oar2glb.rigge_0_reconstruit_depuis_l_oar":"[riggé] '{0}' reconstruit depuis l'OAR : {1} face(s), {2} sommets, {3} triangles (convoar : {4} primitive(s), {5} sommets), échelle du prim ignorée {6}, échelle de bind_shape {7}","py.oar2glb.rigge_0_taille_obtenue_1_2f":"[riggé] '{0}' : taille obtenue {1:.2f} x {2:.2f} x {3:.2f} m implausible (hors de {4:g} à {5:g} m), laissé tel que convoar l'a produit","py.oar2glb.sans_bind_shape_matrix":"sans bind_shape_matrix","py.oar2glb.sans_extension":"(sans extension)","py.oar2glb.sans_textureentry":"sans TextureEntry","py.oar2glb.sommets_du_glb_axes_opensim_x":"      sommets du GLB (axes OpenSim x, y, z) : de {0} à {1} soit {2} m, {3} sommets","py.oar2glb.sommets_du_glb_illisibles_0":"      sommets du GLB illisibles ({0})","py.oar2glb.terrain_0":"[terrain] {0}","py.oar2glb.terrain_0_nud_s_terrain_de":"[terrain] {0} nœud(s) « Terrain » de convoar retiré(s) de la scène","py.oar2glb.terrain_0_nud_s_terrain_retire":"[terrain] {0} nœud(s) « Terrain » retiré(s) de la scène (leurs données restent dans le GLB, inutilisées) ; {1:.1f} Mo lus, par morceaux de {2} Ko au plus","py.oar2glb.terrain_attention_carte_de_0_x":"[terrain] attention : carte de {0} x {1} échantillons pour une région de {2:g} x {3:g} m","py.oar2glb.terrain_aucun_fichier_ecrit":"[terrain] aucun fichier écrit","py.oar2glb.terrain_carte_0_x_1_echantillons":"[terrain] carte {0} x {1} échantillons (1 m) ; niveau d'eau {2:g} m ({3}) ; {4} patch(es) de {5} m ; {6} sommets ; {7:.1f} Mo ajoutés ; {8:.1f} s","py.oar2glb.terrain_cet_oar_n_a_pas":"[terrain] cet OAR n'a pas de carte de hauteurs (terrains/*.r32) : terrain non généré, rien n'est modifié","py.oar2glb.terrain_complet_depuis_la_carte_de":"terrain complet depuis la carte de hauteurs : auto = remplace le terrain de convoar s'il couvre moins que la carte (défaut), oui = toujours, non = jamais","py.oar2glb.terrain_de_convoar_complet_couvre_0":"terrain de convoar complet (couvre {0:.1f} % de la carte) : inchangé","py.oar2glb.terrain_de_convoar_incomplet_couvre_0":"terrain de convoar incomplet (couvre {0:.1f} % de la carte)","py.oar2glb.terrain_desactive_terrain_non":"[terrain] désactivé (--terrain no)","py.oar2glb.texture_0_alpha_1_2f":"texture {0} alpha {1:.2f}","py.oar2glb.textures_0_1_2_3_0f":"[textures] {0}/{1} ({2} %) - {3:.0f} s","py.oar2glb.textures_0_reencodees_1_illisibles_remplacee":"[textures] {0} réencodées, {1} illisibles remplacées par un gris neutre","py.oar2glb.textures_0_sculpt_maps_laissees_intactes":"[textures] {0} sculpt maps laissées intactes","py.oar2glb.textures_0_textures_a_reencoder_sur":"[textures] {0} textures à réencoder sur {1} cœurs ({2:.0f} s)","py.oar2glb.textures_ecriture_de_0":"[textures] écriture de {0}...","py.oar2glb.textures_lecture_de_0":"[textures] lecture de {0}...","py.oar2glb.translation_bind_shape_0":" ; translation bind_shape {0}","py.oar2glb.type_llsd_inconnu_0_r":"type LLSD inconnu {0!r}","py.oar2glb.unknown":"inconnu","py.oar2glb.unreadable":"illisible","py.oar2glb.uuid_du_mesh":"UUID du mesh","py.oar2glb.uuid_du_prim":"UUID du prim","py.oar2glb.var_region_0_objet_s_replace":"[var-region] {0} objet(s) replacé(s) à leur vraie position, {1} reconnu(s), {2} non reconnu(s)","py.presence.0_1_20_jusqu_au_2":"  {0}. {1:<20} jusqu'au {2:<17} {3}","py.presence.0_1_2_autres_appareils_du":" · {0}://{1}:{2} (autres appareils du réseau)","py.presence.0_ejecte":"{0} éjecté","py.presence.0_id_1_cle_2_ip":"{0} [id {1}, clé {2}, ip {3}]","py.presence.adresses_ip_dans_le_journal_masquees":"adresses IP dans le journal : masquées (défaut), en clair, ou absentes","py.presence.aucun_bannissement":"(aucun bannissement)","py.presence.ban_ip":"banni (IP)","py.presence.banned":"banni","py.presence.banned_line":"{0} banni ({1})","py.presence.bannissement_de_0_leve":"bannissement de {0} levé","py.presence.certificat_tls_wss":"certificat TLS (wss://)","py.presence.chat":"chat","py.presence.cle_0_ip_1":"clé {0} ip {1}","py.presence.cle_privee_tls":"clé privée TLS","py.presence.commande_inconnue_0_tape_aide":"commande inconnue : {0} (tape « aide »)","py.presence.commandes_tape_les_ici_puis_entree":"commandes (tape-les ici, puis Entrée) :\n  liste                           visiteurs connectés (n°, nom, rôle, salon, durée, IP)\n  ejecter <n°|nom> [raison]       déconnecte le visiteur (il peut revenir)\n  bannir <n°|nom> [minutes] [raison]   éjecte et interdit sa clé et son IP (IPv6 : son préfixe /64 ; défaut 60 min ; 0 = définitif)\n  bans                            bannissements en cours\n  debannir <n° de bans>           lève un bannissement\n  rooms                           salons connus : connectés, visites, clé (casse exacte)\n  visits-key <salon> [off]        clé du journal des visites d'un salon (nouvelle clé, ou off pour la retirer ; seul : liste)\n  creators                        créateurs (fichier --creators relu) : préfixe, état, salons ouverts, promeneurs, origines\n  oublier <pseudo>                libère un pseudo réservé (son propriétaire le perd ; le premier qui le demande l'obtient)\n  pseudos [filtre]                liste les pseudos réservés (code #XXXX du propriétaire, dernière venue, expiration)\n  version                         numéro de version et révision de ce fichier\n  aide                            ce message\n  (un nom contenant des espaces : utilise le n° de « liste »)","py.presence.comportement_inapproprie":"comportement inapproprié","py.presence.connexions_simultanees_par_adresse_ip":"connexions simultanées par adresse IP (IPv6 : par préfixe /64)","py.presence.debut":"début","py.presence.deconnexion":"déconnexion","py.presence.definitif":"définitif","py.presence.delai_mini_entre_deux_messages_d":"délai mini entre deux messages d'un visiteur (s)","py.presence.derniers_messages_rejoues_aux_nouveaux_arriv":"derniers messages rejoués aux nouveaux arrivants (défaut 200 ; 0 = aucun) ; les plus anciens se demandent par paquets de 50 (message history)","py.presence.derriere_un_reverse_proxy_en_tete":"derrière un reverse proxy : en-tête portant l'IP réelle du visiteur (ex. X-Forwarded-For, CF-Connecting-IP) ; à n'activer que si le serveur n'est joignable que par ce proxy","py.presence.duree_0_min_1_02d_s":"durée {0} min {1:02d} s","py.presence.ejecte_par_l_hote":"éjecté par l'hôte","py.presence.erreur_de_commande_0":"[erreur de commande] {0}","py.presence.ev.ban":"bannissement","py.presence.ev.connect":"connexion","py.presence.ev.end":"fin","py.presence.ev.kick":"éjection","py.presence.ev.name":"nom","py.presence.ev.refuse":"refus","py.presence.ev.empty":"vide","py.presence.ev.http":"requête http","py.presence.empty":"connexion ouverte puis fermée sans requête ({0} depuis la dernière ligne de cette adresse ; préconnexion d'un navigateur, test de port ou robot : sans danger)","py.presence.http":"GET {1}, hôte {2}, agent {3} : ce n'est pas une ouverture de WebSocket ({4}) ({0} depuis la dernière ligne de cette adresse ; navigateur qui ouvre l'adresse du serveur, robot ou test : sans danger)","py.presence.ev.raw":"requête illisible","py.presence.raw":"{1}, début « {2} » ({0} depuis la dernière ligne de cette adresse ; robot qui sonde le port : sans danger)","py.presence.rawkind.misc":"ce n'est pas une requête HTTP","py.presence.rawkind.rdp":"sondage du Bureau à distance Windows (RDP)","py.presence.rawkind.tls":"connexion chiffrée (https) sur un port sans chiffrement","py.presence.ev.walk":"promenade","py.presence.fichier_de_bannissements_illisible_0_ignore":"[!] fichier de bannissements illisible ({0}) : ignoré","py.presence.fichier_de_journal_tourne_chaque_nuit":"fichier de journal (tourné chaque nuit) ; chemin relatif = dossier du script","py.presence.fichier_des_bannissements_chemin_relatif_dos":"fichier des bannissements ; chemin relatif = dossier du script","py.presence.help.host":"adresse d'écoute (0.0.0.0 = toutes les interfaces ; 127.0.0.1 = cette machine seulement)","py.presence.help.maxtotal":"connexions simultanées au total, tous salons confondus","py.presence.help.port":"port d'écoute des visiteurs","py.presence.history_days":"jours de messages relus et conservés dans --history-file au démarrage (défaut 30 ; 0 = tout conserver)","py.presence.history_file":"fichier d'historique du chat (une ligne JSON par message : heure, pseudo, texte, salon ; jamais l'adresse IP) : relu au démarrage pour garder l'historique entre deux relances ; désactivé par défaut. Ce sont des données personnelles","py.presence.history_loaded":"historique : {0} message(s) relu(s), {1} ignoré(s) ou trop ancien(s) ({2})","py.presence.history_write_error":"historique : écriture impossible ({0})","py.presence.jours_de_journal_conserves":"jours de journal conservés","py.presence.leve":"levé","py.presence.limite_de_connexions_par_ip":"limite de connexions par IP","py.presence.list_line":"  n°{0:<4} {1:<26} {2:<10} salon={3:<16} {4} min {5:02d} s   ip {6}","py.presence.log_line":"{0:<11} | salon={1} | {2}","py.presence.longueur_max_d_un_message_de":"longueur max d'un message de chat","py.presence.messages_max_par_fenetre_de_10":"messages max par fenêtre de 10 s et par visiteur","py.presence.moderation_tape_aide_pour_la_liste":"modération : tape « aide » pour la liste des commandes (liste, ejecter, bannir, bans, debannir, oublier, pseudos, rooms, visits-key, creators, version)","py.presence.nobody":"(personne)","py.presence.noms_interdits_a_la_reservation_separes":"noms interdits à la réservation, séparés par des virgules (ex. admin,moderateur)","py.presence.old_name":"ancien : {0}","py.presence.origines_autorisees_separees_par_des_virgule":"origines autorisées, séparées par des virgules (défaut : toutes)","py.presence.personne_ne_correspond_a_0_tape":"personne ne correspond à « {0} » (tape « liste »)","py.presence.plusieurs_visiteurs_correspondent_utilise_le":"plusieurs visiteurs correspondent, utilise le n° :","py.presence.promeneur_0_dans_le_salon":"promeneur ({0} dans le salon)","py.presence.promeneurs_max_par_salon":"promeneurs max par salon","py.presence.registre_des_noms_reserves_vide_en":"registre des noms réservés (vide = en mémoire seulement) ; chemin relatif = dossier du script","py.presence.registre_illisible_0_demarrage_a_vide":"[!] registre illisible ({0}) : démarrage à vide","py.presence.role.spectator":"spectateur","py.presence.role.walker":"promeneur","py.presence.salon_plein":"salon plein","py.presence.serveur_adresse_a_donner_a_presence":"serveur | adresse à donner à --presence-url : {0}://{1}:{2}","py.presence.serveur_adresses_a_donner_a_presence":"serveur | adresses à donner à --presence-url : {0}://127.0.0.1:{1} (cette machine)","py.presence.serveur_de_presence_glb2html_websocket":"presence_server.py {0} : serveur de présence glb2html (WebSocket) : visiteurs, chat, modération.","py.presence.serveur_journal_0_registre_des_noms":"serveur | journal : {0} | registre des noms : {1}","py.presence.serveur_n_utilise_jamais_0_0":"serveur | n'utilise jamais 0.0.0.0 dans --presence-url : c'est une adresse d'écoute, pas une destination","py.presence.star_hint":"serveur | ou {0}://*:{1} : le même nom que la page qui se connecte (conseillé si tes pages sont ouvertes par plusieurs adresses : localhost, réseau, nom public)","py.presence.serveur_presence_server_0_ecoute_sur":"serveur | presence_server {0} | écoute sur {1}:{2}  (Ctrl+C pour arrêter)","py.presence.spectateurs_vue_globale_max_tous_salons":"spectateurs (vue globale) max, tous salons","py.presence.spectator_paren":"(spectateur)","py.presence.trop_de_messages_patiente_quelques_secondes":"Trop de messages, patiente quelques secondes.","py.presence.trop_de_spectateurs":"trop de spectateurs","py.presence.un_nom_non_utilise_depuis_ce":"un nom non utilisé depuis ce nombre de jours est libéré","py.presence.until_date":"jusqu’au {0}","py.presence.usage_ban":"usage : bannir <n°|nom> [minutes] [raison]","py.presence.usage_kick":"usage : ejecter <n°|nom> [raison]","py.presence.usage_unban":"usage : debannir <n° de « bans »>","py.presence.ev.forget":"pseudo libéré","py.presence.forget_done":"pseudo « {0} » libéré : le premier navigateur qui le demandera l'obtiendra","py.presence.forget_logged":"ancien propriétaire #{0}","py.presence.forget_none":"aucun pseudo réservé ne correspond à « {0} »","py.presence.forget_online":"(son ancien propriétaire est connecté : son nom affiché ne change pas avant sa prochaine connexion)","py.presence.usage_forget":"usage : oublier <pseudo>   (le pseudo comme tu veux : casse, accents et espaces sans importance)","py.presence.names_head":"pseudos réservés ({0}) :","py.presence.names_line":"  {0} #{1}  dernière venue {2}, libre le {3} si inutilisé{4}","py.presence.names_none":"(aucun pseudo réservé)","py.presence.names_online":"(connecté)","py.presence.zone":"zone","py.stats.0_16_mediane_1_1f_90":"{0:>16} : médiane {1:,.1f} | 90 % des blocs sous {2:,.1f} | maximum {3:,.1f}","py.stats.attention_geometrie_compressee_0_les_mo":"Attention : géométrie compressée ({0}) : les Mo de géométrie ci-dessus sont la taille décodée, pas celle du fichier.","py.stats.aucun_mesh_positionnable_accessors_sans_min":"Aucun mesh positionnable (accessors sans min/max ?).","py.stats.bloc_0_1_2_1f_mo":"  bloc {0},{1} : {2:.1f} Mo de géométrie, {3} triangles, {4} instances, {5:.1f} Mo de textures","py.stats.blocs_de_0_0f_m_1":"== Blocs de {0:.0f} m : {1} non vides (centre des instances ; géométrie et textures sans doublon dans le bloc) ==","py.stats.ce_fichier_n_est_pas_un":"Ce fichier n'est pas un GLB.","py.stats.cote_des_blocs_en_metres_defaut":"côté des blocs en mètres (défaut 256)","py.stats.cout_de_la_reutilisation_entre_blocs":"== Coût de la réutilisation entre blocs ==","py.stats.desc":"glb-stats.py : analyse rapide d'un GLB, quelle que soit sa taille. Lit uniquement l'en-tête JSON (jamais les données binaires ni les textures) : quelques secondes et très peu de mémoire.","py.stats.ecrit_aussi_le_rapport_dans_ce":"écrit aussi le rapport dans ce fichier (UTF-8)","py.stats.etendue":"== Étendue ==","py.stats.fichier_0_1_1f_mo_en":"Fichier : {0} ({1:,.1f} Mo ; en-tête JSON lu : {2:,.1f} Mo)","py.stats.geometrie_accessors_uniques_0_1f_mo":"Géométrie (accessors uniques) : {0:,.1f} Mo | Textures embarquées : {1:,.1f} Mo | Reste : {2:,.1f} Mo","py.stats.geometrie_mo":"géométrie (Mo)","py.stats.geometrie_utilisee_par_plusieurs_blocs_0":"Géométrie utilisée par plusieurs blocs : {0:,.1f} Mo ({1:.0f} % du total) | textures utilisées par plusieurs blocs : {2:,.1f} Mo ({3:.0f} % du total) : taille d'une bibliothèque commune chargée une fois.","py.stats.help.glb":"fichier .glb à analyser","py.stats.le_premier_bloc_du_glb_n":"Le premier bloc du GLB n'est pas du JSON.","py.stats.les_5_blocs_les_plus_lourds":"Les 5 blocs les plus lourds en géométrie :","py.stats.meshes_reutilises_plusieurs_fois_0_materiaux":"Meshes réutilisés plusieurs fois : {0} | matériaux : {1} | textures (images) : {2} (utilisées : {3})","py.stats.nud_0_1_2_0f_m":"  - nœud {0} « {1} » : {2:.0f} m, {3} mesh(es)","py.stats.nuds_parcourus_0_meshes_1_utilises":"Nœuds parcourus : {0} | meshes : {1} (utilisés : {2}) | instances de meshes : {3}","py.stats.objets_racine_0_plus_grands_qu":"Objets racine : {0} | plus grands qu'un bloc de {1:.0f} m : {2}","py.stats.poids_estime_octets_lus_dans_l":"== Poids estimé (octets lus dans l'en-tête, sans décoder) ==","py.stats.somme_des_blocs_geometrie_0_1f":"Somme des blocs : géométrie {0:,.1f} Mo (contre {1:,.1f} Mo sans doublon dans tout le fichier) : écart = surcoût si les meshes partagés sont dupliqués dans chaque bloc.","py.stats.sommets_uniques_0_sommets_rendus_instances":"Sommets uniques : {0:,} | sommets rendus (instances comprises) : {1:,} | triangles rendus : {2:,}","py.stats.taux_de_reutilisation_sommets_rendus_uniques":"Taux de réutilisation (sommets rendus / uniques) : {0:.1f}","py.stats.x_0_1f_a_1_1f":"X : {0:.1f} à {1:.1f} ({2:.0f} m) | Z : {3:.1f} à {4:.1f} ({5:.0f} m) | hauteur Y : {6:.1f} à {7:.1f}","py.presence.help.visits":"fichier du journal des visites (une ligne JSON par visite, sans IP ; vide = pas de journal ; chemin relatif au dossier du script)","py.presence.help.visits_days":"jours de visites conservés dans ce journal (0 = tous)","py.presence.help.visits_names":"note aussi le pseudo des promeneurs dans le journal des visites","py.presence.help.visits_keys":"fichier des clés d'accès au journal des visites (empreintes seulement, chemin relatif au dossier du script)","py.presence.ev.visits":"visites","py.presence.visits.rate":"trop d'essais de clé","py.presence.visits.badkey":"clé refusée","py.presence.visits.granted":"résumé envoyé","py.presence.visits.yes":"oui","py.presence.visits.no":"non","py.presence.visits_on":"serveur : journal des visites {0} (conservé {1} jours, 0 = tous ; pseudos : {2})","py.presence.visits_write_err":"journal des visites {0} : écriture impossible ({1})","py.presence.vkey.unreadable":"fichier des clés de visites illisible : {0} (démarrage sans clé)","py.presence.help.creators":"fichier des créateurs autorisés (origines de leurs pages, préfixe de salon, limites ; relu à chaud, chemin relatif au dossier du script) ; absent : tout le monde est accepté","py.presence.cr.bad":"créateurs : entrée {0} ignorée (id manquant ou invalide : lettres, chiffres, - et _, 32 au plus)","py.presence.cr.badprefix":"créateurs : entrée {0} ignorée (préfixe {1} invalide : lettres, chiffres, espace, - et _, sans point)","py.presence.cr.dup":"créateurs : entrée {0} ignorée ({1} déjà utilisé par une entrée précédente)","py.presence.cr.nulljson":"créateurs : {0} : origine null écrite sans guillemets, ignorée (écrire \"null\" entre guillemets pour une page ouverte depuis le disque)","py.presence.cr.origindup":"créateurs : l'origine {0} appartient déjà à {1}, ignorée pour {2}","py.presence.cr.missing":"fichier des créateurs absent : {0} ; toute connexion est refusée tant qu'il n'existe pas","py.presence.cr.unreadable":"fichier des créateurs illisible : {0} ({1}) ; liste précédente gardée","py.presence.cr.loaded":"créateurs : {0} lus dans {1}","py.presence.cr.on":"serveur : créateurs {0} ({1}) ; une page d'une autre origine est refusée","py.presence.cr.off":"aucun fichier de créateurs (lance le serveur avec --creators FICHIER) : toutes les pages sont acceptées","py.presence.cr.none":"aucun créateur valide dans {0} : toute connexion est refusée","py.presence.cr.line":"  {0:<16} préfixe : {1}   {2}   salons ouverts : {3}{4}   promeneurs : {5}{6}","py.presence.cr.noprefix":"(aucun : tous les autres salons)","py.presence.cr.active":"actif","py.presence.cr.suspended":"suspendu","py.presence.cr.max":" / {0} au plus","py.presence.cr.origins":"      origines : {0}","py.presence.cr.noorigin":"(aucune)","py.presence.cr.refuse.origin":"origine non déclarée : {0}","py.presence.cr.refuse.off":"créateur {0} suspendu","py.presence.cr.refuse.room":"salon {0} hors des salons de {1}","py.presence.cr.refuse.rooms":"{0} : déjà {1} salons ouverts","py.presence.vkey.none":"aucune clé de journal des visites","py.presence.vkey.line":"  salon « {0} » : clé créée le {1}","py.presence.vkey.unknown":"aucune clé pour le salon « {0} »","py.presence.vkey.off":"clé du salon « {0} » retirée","py.presence.vkey.new":"clé du journal des visites du salon « {0} » : {1}\n  (affichée une seule fois ; donne-la au créateur avec l'adresse de sa page suivie de #visits ; l'ancienne clé ne marche plus)","py.presence.vkey.inactive":"attention : le journal des visites est inactif (lance le serveur avec --visits FICHIER)","py.presence.vkey.case":"attention : aucune visite ni aucun visiteur pour le salon « {0} » ; salon connu avec une autre casse : {1}. La casse compte : refais visits-key avec le nom exact (cette clé reste valable pour « {0} »).","py.presence.rooms.none":"aucun salon connu (ni visiteur connecté, ni visite enregistrée, ni clé)","py.presence.rooms.line":"  {0:<24} connectés : {1} ({2} en promenade)   visites : {3}{4}   clé : {5}","py.presence.rooms.last":", dernière le {0}","py.presence.rooms.novisits":"  (journal des visites inactif : lance le serveur avec --visits FICHIER pour compter les visites)","py.presence.rooms.note":"  (casse exacte ; un salon jamais visité et sans clé n'apparaît pas : son nom est la valeur room de NOM.config.json, par défaut le nom de la page)"}}''')


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


VERSION = "1.0.1 (31/10/2026)"      # remplacé par build.py (fichier VERSION) dans dist/glb2tiles.py
MARK = "e47b6fd1"      # empreinte du fichier fabriqué, inscrite par build.py ; reste telle quelle depuis tools/


def version_tag():
    """version, suivie de l'empreinte du fichier quand build.py l'a inscrite"""
    return VERSION if MARK.startswith("__") else _tr("py.common.version_mark", VERSION, MARK)
FORMAT_TUILES = 1            # version du format de X.tiles.json
BLOC_LECTURE = 4 << 20       # octets lus d'un coup dans le GLB d'entrée (lectures toujours par morceaux)
MO = 1048576
LIMITE_GLB = 0xFFFFFFFF      # un GLB ne dépasse jamais 4 Go (longueurs sur 32 bits)
COMPRESSIONS = ("KHR_draco_mesh_compression", "EXT_meshopt_compression", "KHR_meshopt_compression")
CODE = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
U32 = next(c for c in "IL" if array.array(c).itemsize == 4)
CODE[5125] = U32
TAILLE = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}
LOG_PATH = None              # fixé par main() : fichier du journal (None = écran seulement)


class ErreurGlb(Exception):
    """Cas non géré ou fichier invalide : message clair pour l'utilisateur, arrêt propre."""


# ---------------------------------------------------------------- journal et avancement
def log(msg=""):
    print(msg, flush=True)
    if LOG_PATH:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")


class Progres:
    """Écrit l'avancement dans le journal toutes les 5 % ou 10 s."""

    def __init__(self, titre, total):
        self.titre, self.total = titre, max(1, total)
        self.t0 = self.t = time.time()
        self.pct = -5.0

    def avance(self, fait):
        pct = 100.0 * fait / self.total
        now = time.time()
        if pct - self.pct >= 5 or now - self.t >= 10:
            log(f"[{self.titre}] {pct:.0f} % ({fait}/{self.total}, {now - self.t0:.0f} s)")
            self.pct, self.t = pct, now


# ---------------------------------------------------------------- mesures communes (glb-stats.py)
_stats = None


def stats():
    global _stats
    if _stats is None:
        p = Path(__file__).resolve().with_name("glb-stats.py")
        if not p.is_file():
            raise ErreurGlb(_tr("py.glb2tiles.glb_stats_py_introuvable_a_cote", p.parent))
        spec = importlib.util.spec_from_file_location("glb_stats", p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _stats = m
    return _stats


def fmt(n):
    return stats().fmt(int(n))


def mo(o):
    return o / MO


def virg(x, nd=2):
    return f"{x:.{nd}f}".replace(".", ",")


# ---------------------------------------------------------------- lecture du GLB par morceaux
Acc = collections.namedtuple("Acc", "i comp ncomp count es stride off norm type mn mx")


class Glb:
    """Accès au GLB d'entrée : JSON en mémoire, données lues à la demande (compteurs pour les tests)."""

    def __init__(self, chemin):
        if sys.byteorder != "little":
            raise ErreurGlb(_tr("py.glb2tiles.machine_big_endian_non_geree"))
        self.chemin = str(chemin)
        self.taille = os.path.getsize(chemin)
        self.g, njson = stats().lire_json(self.chemin)
        self.njson = njson
        self.octets_lus = 20 + njson        # en-tête + JSON (lus par lire_json)
        self.plus_grande_lecture = 0
        self.nb_lectures = 0
        comp = [e for e in self.g.get("extensionsUsed", []) if e in COMPRESSIONS]
        if comp:
            raise ErreurGlb(_tr("py.glb2tiles.ce_glb_est_compresse") + ", ".join(comp) + _tr("py.glb2tiles.glb2tiles_ne_lit_pas_les_glb"))
        self.f = open(self.chemin, "rb")
        self.f.seek(20 + njson)
        ent = self.f.read(8)
        self.bin_off, self.bin_len = 0, 0
        if len(ent) == 8:
            ln, typ = struct.unpack("<II", ent)
            if typ == 0x004E4942:
                self.bin_off, self.bin_len = 28 + njson, ln
        self.octets_lus += len(ent)
        bufs = self.g.get("buffers", [])
        if bufs and "uri" in bufs[0]:
            raise ErreurGlb(_tr("py.glb2tiles.le_tampon_0_a_une_adresse"))
        self._acc = {}

    def fermer(self):
        self.f.close()

    def lire(self, off, n):
        """Lit n octets à partir de off (relatif au tampon BIN), par morceaux de BLOC_LECTURE."""
        if off < 0 or n < 0 or off + n > self.bin_len:
            raise ErreurGlb(_tr("py.glb2tiles.lecture_hors_du_tampon_du_glb", off, n))
        out = bytearray()
        self.f.seek(self.bin_off + off)
        reste = n
        while reste > 0:
            k = min(reste, BLOC_LECTURE)
            b = self.f.read(k)
            if len(b) != k:
                raise ErreurGlb(_tr("py.glb2tiles.fichier_glb_tronque"))
            self.octets_lus += k
            self.nb_lectures += 1
            self.plus_grande_lecture = max(self.plus_grande_lecture, k)
            out += b
            reste -= k
        return out

    def vue(self, i):
        bvs = self.g.get("bufferViews", [])
        if i is None or not (0 <= i < len(bvs)):
            raise ErreurGlb(_tr("py.glb2tiles.bufferview_0_inexistant", i))
        bv = bvs[i]
        if bv.get("buffer", 0) != 0:
            raise ErreurGlb(_tr("py.glb2tiles.bufferview_0_seul_le_tampon_0", i))
        return bv

    def acc(self, i):
        a = self._acc.get(i)
        if a is not None:
            return a
        accs = self.g.get("accessors", [])
        if i is None or not (0 <= i < len(accs)):
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_inexistant", i))
        x = accs[i]
        if "sparse" in x:
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_accessor_sparse_non_gere", i))
        if "bufferView" not in x:
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_sans_bufferview_valeurs_a", i))
        bv = self.vue(x["bufferView"])
        comp, typ = x.get("componentType"), x.get("type")
        if comp not in TAILLE or typ not in NCOMP:
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_type_1_2_inconnu", i, typ, comp))
        nc = NCOMP[typ]
        es = nc * TAILLE[comp]
        stride = bv.get("byteStride") or es
        off = bv.get("byteOffset", 0) + x.get("byteOffset", 0)
        count = x.get("count", 0)
        if stride < es:
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_bytestride_1_plus_petit", i, stride, es))
        if count and off + (count - 1) * stride + es > bv.get("byteOffset", 0) + bv.get("byteLength", 0):
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_depasse_son_bufferview_fichier", i))
        a = Acc(i, comp, nc, count, es, stride, off, bool(x.get("normalized")), typ, x.get("min"), x.get("max"))
        self._acc[i] = a
        return a

    def blocs_indices(self, ai):
        """Indices d'un accessor, par morceaux (array non signé)."""
        a = self.acc(ai)
        if a.comp not in (5121, 5123, 5125) or a.ncomp != 1:
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_type_d_indices_non", ai))
        if a.stride != a.es:
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_indices_avec_bytestride_non", ai))
        n_par = max(1, BLOC_LECTURE // a.es)
        for debut in range(0, a.count, n_par):
            n = min(n_par, a.count - debut)
            arr = array.array(CODE[a.comp])
            arr.frombytes(self.lire(a.off + debut * a.es, n * a.es))
            yield arr

    def rangee(self, a, r0, n):
        """Octets bruts de n lignes de l'accessor a à partir de la ligne r0 (longueur (n-1)*stride + es)."""
        if n <= 0:
            return bytearray()
        return self.lire(a.off + r0 * a.stride, (n - 1) * a.stride + a.es)


# ---------------------------------------------------------------- sommets utilisés
class Marques:
    """Ensemble des sommets indexés, sous forme de drapeaux sur la plage [base, base+len(flags))."""

    def __init__(self):
        self.base = 0
        self.flags = bytearray()

    def ajouter(self, arr):
        if not len(arr):
            return
        mn, mx = min(arr), max(arr)
        if not self.flags:
            self.base = mn
            self.flags = bytearray(mx - mn + 1)
        else:
            if mn < self.base:
                self.flags = bytearray(self.base - mn) + self.flags
                self.base = mn
            fin = self.base + len(self.flags)
            if mx >= fin:
                self.flags.extend(bytes(mx - fin + 1))
        src = map(self.base.__rsub__, arr) if self.base else arr
        collections.deque(map(self.flags.__setitem__, src, itertools.repeat(1)), maxlen=0)

    def compter(self):
        return self.flags.count(1)

    @property
    def imin(self):
        return self.base

    @property
    def imax(self):
        return self.base + len(self.flags) - 1


def tri_mode(mode, n):
    if mode == 4:
        return n // 3
    if mode in (5, 6):
        return max(0, n - 2)
    return 0


def taille_indices(used):
    return 2 if used <= 65535 else 4


def es_sortie(es):
    return (es + 3) // 4 * 4


def decode_norm(v, comp, norm):
    if not norm or comp == 5126:
        return v
    if comp in (5120, 5122):
        return max(v / (2 ** (8 * TAILLE[comp] - 1) - 1), -1.0)
    return v / (2 ** (8 * TAILLE[comp]) - 1)


def minmax_donnees(data, a, stride_out):
    """min/max par composante d'un tampon compact (lignes de stride_out octets) ; None si non fini."""
    arr = array.array(CODE[a.comp])
    arr.frombytes(bytes(data) if not isinstance(data, (bytes, bytearray)) else data)
    se = stride_out // TAILLE[a.comp]
    mins, maxs = [], []
    for k in range(a.ncomp):
        col = arr[k::se]
        if not len(col):
            return None
        mins.append(decode_norm(min(col), a.comp, a.norm))
        maxs.append(decode_norm(max(col), a.comp, a.norm))
    if a.comp == 5126 and not all(math.isfinite(v) for v in mins + maxs):
        return None
    return mins, maxs


class Prim:
    """Géométrie distincte (clé : mode, indices, attributs, cibles) ; les matériaux n'en font pas partie."""
    __slots__ = ("key", "mode", "indices", "attrs", "targets", "tri", "used", "n_idx", "imin", "imax", "lo", "hi", "cbytes", "vide")


def cle_prim(pr):
    attrs = tuple(sorted(pr.get("attributes", {}).items()))
    tg = tuple(tuple(sorted(t.items())) for t in pr.get("targets", ()))
    return (pr.get("mode", 4), pr.get("indices"), attrs, tg)


def parcourir_textures(obj, f):
    """Appelle f(dict) pour chaque référence de texture (clé finissant par « Texture », avec « index »)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.endswith("Texture") and isinstance(v, dict) and isinstance(v.get("index"), int):
                f(v)
            parcourir_textures(v, f)
    elif isinstance(obj, list):
        for v in obj:
            parcourir_textures(v, f)


def images_de_texture(t):
    src = [t.get("source")]
    src += [e.get("source") for e in t.get("extensions", {}).values() if isinstance(e, dict)]
    return [s for s in src if isinstance(s, int)]


GRIS_IMAGE = 128             # niveau du gris des images remplacées (celui de oar2glb.py, GREY_PNG)
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def png_gris(niveau=GRIS_IMAGE, cote=4):
    """PNG RVB uni de cote x cote pixels (zlib et struct seulement)."""
    def chunk(typ, data):
        c = typ + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    ligne = b"\x00" + bytes([niveau]) * (3 * cote)
    return PNG_SIG + chunk(b"IHDR", struct.pack(">IIBBBBB", cote, cote, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(ligne * cote, 9)) + chunk(b"IEND", b"")


def image_valide(lecteur, n):
    """PNG, JPEG ou WebP complet (structure seulement, sans décoder) ; faux pour 0 octet, autre format ou image tronquée.
    lecteur(décalage, longueur) rend des octets, n est la taille de l'image : seuls l'en-tête, la fin et les en-têtes de blocs sont lus.
    Mesuré dans Chromium (createImageBitmap) : une image tronquée échoue comme une image vide, d'où la vérification de la fin du fichier :
    PNG = chaînage des blocs jusqu'à IEND ; JPEG = marqueur EOI (FFD9) en dernier, aux zéros et espaces de bourrage près, ou dans les 64
    derniers octets ; WebP = taille RIFF contenue dans le fichier."""
    tete = bytes(lecteur(0, min(n, 12)))
    if tete[:8] == PNG_SIG:
        p = 8
        for _ in range(100000):
            if p + 12 > n:
                return False
            ln, typ = struct.unpack(">I4s", bytes(lecteur(p, 8)))
            p += 12 + ln
            if typ == b"IEND":
                return p <= n
        return False
    if tete[:3] == b"\xff\xd8\xff":
        fin = bytes(lecteur(max(0, n - 64), min(n, 64)))
        return fin.rstrip(b"\x00 \r\n").endswith(b"\xff\xd9") or b"\xff\xd9" in fin
    if tete[:4] == b"RIFF" and tete[8:12] == b"WEBP":
        return struct.unpack("<I", tete[4:8])[0] + 8 <= n
    return False


def extensions_presentes(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "extensions" and isinstance(v, dict):
                out.update(v.keys())
            extensions_presentes(v, out)
    elif isinstance(obj, list):
        for v in obj:
            extensions_presentes(v, out)


# ---------------------------------------------------------------- plan : mesures, objets racine, unités, quadtree
Mi = collections.namedtuple("Mi", "prims cles imgs tri lo hi poids")


class Inst:
    __slots__ = ("node", "mesh", "lo", "hi", "centre", "tri", "racine")


class Racine:
    __slots__ = ("id", "nodes", "insts", "cles", "imgs", "tri", "lo", "hi", "centre", "etendue", "poids", "skin", "entier", "terrain")


class Unite:
    __slots__ = ("racine", "node", "entier", "cles", "imgs", "tri", "cx", "cz", "ninst", "nom", "etendue")


class Tuile:
    def __init__(self, niveau, i, j, units):
        self.niveau, self.i, self.j, self.units = niveau, i, j, units
        self.nom = f"T_{niveau}_{i}_{j}"


def compiler_exclusions(motifs):
    """Expressions de --exclude compilées (insensibles à la casse) ; message clair si l'une est invalide."""
    res = []
    for m in motifs:
        try:
            res.append(re.compile(m, re.IGNORECASE))
        except re.error as e:
            raise ErreurGlb(_tr("py.glb2tiles.expression_reguliere_invalide_pour_exclure_0", m, e))
    return res


class Params:
    """Paramètres du découpage (les poids sont convertis en octets)."""

    def __init__(self, budget=32.0, budget_tri=1500000, cote_min=16.0, entier_poids=16.0, entier_etendue=256.0,
                 seuil=150.0, seuil_tri=3000000, aberrant=1000.0, bloc=256.0, exclure=(), exclure_max_tri=24, exclure_max_meshes=1, references=True):
        self.budget_mo, self.budget = budget, budget * MO
        self.budget_tri = budget_tri
        self.cote_min = max(cote_min, 1e-3)
        self.entier_poids_mo, self.entier_poids = entier_poids, entier_poids * MO
        self.entier_etendue = entier_etendue
        self.seuil_mo, self.seuil_tri = seuil, seuil_tri
        self.aberrant = aberrant
        self.bloc = bloc
        self.exclure_motifs = list(exclure)             # expressions régulières (texte) ; vérifiées par compiler_exclusions
        self.exclure = compiler_exclusions(self.exclure_motifs)
        self.exclure_max_tri, self.exclure_max_meshes = exclure_max_tri, exclure_max_meshes
        self.references = references                    # v32 : extras.ref / extras.box sur chaque nœud copié (zones liées en mode tuiles)

    def dict(self):
        return {"budgetMB": self.budget_mo, "budgetTriangles": self.budget_tri, "minCell": self.cote_min,
                "wholeWeightMB": self.entier_poids_mo, "wholeExtent": self.entier_etendue,
                "thresholdMB": self.seuil_mo, "thresholdTriangles": self.seuil_tri, "outlier": self.aberrant}


class Plan:
    def __init__(self, glb, P):
        self.glb, self.P = glb, P
        g = glb.g
        self.nodes, self.meshes = g.get("nodes", []), g.get("meshes", [])
        self.mats, self.texs = g.get("materials", []), g.get("textures", [])
        self.avertissements = []
        self.parent = {}
        for i, n in enumerate(self.nodes):
            for c in n.get("children", []):
                self.parent.setdefault(c, i)
        scs = g.get("scenes", [])
        if len(scs) > 1:
            self.avertissements.append(_tr("py.glb2tiles.0_scenes_seule_la_scene_1", len(scs), g.get('scene', 0)))
        sc = scs[g.get("scene", 0)] if scs else {}
        self.racines_ids = sc.get("nodes") if scs else [i for i in range(len(self.nodes)) if i not in self.parent]
        self.cb = {}            # clé (primitive, skin) -> octets compactés
        self.prims = {}         # clé de primitive -> Prim
        self.img_oct = [self.glb.vue(i["bufferView"]).get("byteLength", 0) + 3 & ~3 if "bufferView" in i else 0
                        for i in g.get("images", [])]
        for i in g.get("images", []):
            if "bufferView" not in i and not str(i.get("uri", "")).startswith("data:"):
                raise ErreurGlb(_tr("py.glb2tiles.image_externe_uri_non_geree_seuls"))
        self._imgs_mat = {}
        self.parcourir()
        self.analyser_prims()
        self.construire_racines()
        self.construire_unites()
        self.verifier_images()
        self.calculer_references()

    # -- parcours de la scène
    def parcourir(self):
        S = stats()
        self.noeuds_racine = {}
        self.monde = {}
        ignores = set()
        vus = set()
        ident = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        for r in self.racines_ids:
            lst = []
            pile = [(r, ident)]
            while pile:
                ni, pm = pile.pop()
                if ni in vus:
                    continue
                vus.add(ni)
                n = self.nodes[ni]
                m = S.mat_mul(pm, S.mat_noeud(n))
                lst.append(ni)
                if "mesh" in n:
                    self.monde[ni] = m
                if "camera" in n or "extensions" in n:
                    ignores.add(ni)
                for c in reversed(n.get("children", [])):
                    pile.append((c, m))
            self.noeuds_racine[r] = lst
        if ignores:
            self.avertissements.append(_tr("py.glb2tiles.0_nud_s_avec_camera_ou", len(ignores)))

    def textures_materiau(self, mi):
        res = self._imgs_mat.get(mi)
        if res is None:
            ts = set()
            parcourir_textures(self.mats[mi], lambda d: ts.add(d["index"]))
            res = set()
            for t in ts:
                if 0 <= t < len(self.texs):
                    res.update(images_de_texture(self.texs[t]))
            self._imgs_mat[mi] = res
        return res

    # -- primitives
    def analyser_prims(self):
        ext_prim = False
        self.mesh_prims = {}
        for ni in self.monde:
            m = self.nodes[ni]["mesh"]
            if m in self.mesh_prims:
                continue
            if not (0 <= m < len(self.meshes)):
                raise ErreurGlb(_tr("py.glb2tiles.nud_0_mesh_1_inexistant", ni, m))
            lst = []
            for pr in self.meshes[m].get("primitives", []):
                if "extensions" in pr:
                    ext_prim = True
                if "POSITION" not in pr.get("attributes", {}):
                    raise ErreurGlb(_tr("py.glb2tiles.mesh_0_primitive_sans_position_non", m))
                lst.append((cle_prim(pr), pr))
            self.mesh_prims[m] = lst
        if ext_prim:
            self.avertissements.append(_tr("py.glb2tiles.des_primitives_portent_des_extensions_elles"))
        cles = []
        vu = set()
        for lst in self.mesh_prims.values():
            for k, _ in lst:
                if k not in vu:
                    vu.add(k)
                    cles.append(k)
        log(_tr("py.glb2tiles.analyse_0_primitives_distinctes_a_mesurer", len(cles)))
        pg = Progres("primitives", len(cles))
        self.positions_lues = 0
        for n, k in enumerate(cles):
            self.prims[k] = self.analyser_prim(k)
            self.cb[k] = self.prims[k].cbytes
            pg.avance(n + 1)
        # meshes
        self.mesh_info = {}
        for m, lst in self.mesh_prims.items():
            cl, im, tri = [], set(), 0
            lo, hi = [1e30] * 3, [-1e30] * 3
            for k, pr in lst:
                p = self.prims[k]
                if p.vide:
                    continue
                cl.append(k)
                tri += p.tri
                for q in range(3):
                    lo[q], hi[q] = min(lo[q], p.lo[q]), max(hi[q], p.hi[q])
                if isinstance(pr.get("material"), int) and 0 <= pr["material"] < len(self.mats):
                    im |= self.textures_materiau(pr["material"])
            if cl:
                poids = sum(self.cb[k] for k in set(cl)) + sum(self.img_oct[i] for i in im)
                self.mesh_info[m] = Mi(cl, frozenset(cl), frozenset(im), tri, lo, hi, poids)

    def analyser_prim(self, key):
        glb = self.glb
        mode, ai, attrs, tg = key
        d = dict(attrs)
        pa = glb.acc(d["POSITION"])
        p = Prim()
        p.key, p.mode, p.indices, p.attrs, p.targets = key, mode, ai, d, [dict(t) for t in tg]
        for ac in list(d.values()) + [v for t in p.targets for v in t.values()]:
            if glb.acc(ac).count != pa.count:
                raise ErreurGlb(_tr("py.glb2tiles.primitive_les_attributs_n_ont_pas", pa.count, ac))
        mq = None
        if ai is None:
            p.n_idx = p.used = pa.count
            p.imin, p.imax = 0, pa.count - 1
        else:
            ia = glb.acc(ai)
            p.n_idx = ia.count
            mq = Marques()
            for bloc in glb.blocs_indices(ai):
                mq.ajouter(bloc)
            p.used = mq.compter()
            p.imin, p.imax = (mq.imin, mq.imax) if p.used else (0, -1)
            if p.used and p.imax >= pa.count:
                raise ErreurGlb(_tr("py.glb2tiles.accessor_0_un_indice_depasse_le", ai, pa.count))
        p.tri = tri_mode(mode, p.n_idx)
        p.vide = p.used == 0
        p.lo = p.hi = None
        p.cbytes = 0
        if p.vide:
            return p
        p.lo, p.hi = self.boite_prim(p, pa, mq)
        o = 0
        for ac in list(d.values()) + [v for t in p.targets for v in t.values()]:
            o += p.used * es_sortie(glb.acc(ac).es)
        if ai is not None:
            o += (p.n_idx * taille_indices(p.used) + 3) & ~3
        p.cbytes = o
        return p

    def boite_prim(self, p, pa, mq):
        """Boîte locale exacte des sommets utilisés (accessor min/max seulement s'il est exact)."""
        glb = self.glb
        if pa.mn and pa.mx and len(pa.mn) >= 3 and len(pa.mx) >= 3 and p.used == pa.count:
            return [float(v) for v in pa.mn[:3]], [float(v) for v in pa.mx[:3]]
        if pa.ncomp < 3 or pa.stride % TAILLE[pa.comp]:
            raise ErreurGlb(_tr("py.glb2tiles.accessor_0_positions_non_gerees", pa.i))
        lo, hi = [math.inf] * 3, [-math.inf] * 3
        se = pa.stride // TAILLE[pa.comp]
        lignes = max(1, BLOC_LECTURE // max(pa.stride, 1))
        r = p.imin
        while r <= p.imax:
            n = min(lignes, p.imax - r + 1)
            raw = bytes(glb.rangee(pa, r, n)) + bytes(pa.stride - pa.es)
            self.positions_lues += len(raw)
            arr = array.array(CODE[pa.comp])
            arr.frombytes(raw)
            fl = mq.flags[r - mq.base:r - mq.base + n] if mq is not None else None
            for k in range(3):
                col = arr[k::se]
                if fl is not None:
                    col = list(itertools.compress(col, fl))
                if len(col):
                    lo[k] = min(lo[k], min(col))
                    hi[k] = max(hi[k], max(col))
            r += n
        return ([decode_norm(v, pa.comp, pa.norm) for v in lo], [decode_norm(v, pa.comp, pa.norm) for v in hi])

    # -- objets racine
    def construire_racines(self):
        S = stats()
        self.racines = []
        self.insts = []
        self.exclus = []        # objets racine retirés par --exclude : {"nom", "tri", "meshes", "cles", "imgs"}
        self.gardes = 0         # noms qui correspondent à --exclude mais conservés par les garde-fous
        for r in self.racines_ids:
            rac = Racine()
            rac.id, rac.nodes = r, self.noeuds_racine[r]
            rac.insts = []
            rac.skin = False
            ex = self.nodes[r].get("extras")
            rac.terrain = isinstance(ex, dict) and bool(ex.get("terrain"))      # pièce de terrain d'oar2glb.py (extras.terrain)
            cles, imgs = set(), set()
            for ni in rac.nodes:
                n = self.nodes[ni]
                if "mesh" not in n:
                    continue
                mi = self.mesh_info.get(n["mesh"])
                if mi is None:
                    continue
                it = Inst()
                it.node, it.mesh, it.tri, it.racine = ni, n["mesh"], mi.tri, rac
                pts = S.coins_monde(self.monde[ni], mi.lo, mi.hi)
                it.lo = [min(c[k] for c in pts) for k in range(3)]
                it.hi = [max(c[k] for c in pts) for k in range(3)]
                it.centre = [sum(c[k] for c in pts) / 8 for k in range(3)]
                rac.insts.append(it)
                cles |= mi.cles
                imgs |= mi.imgs
                if isinstance(n.get("skin"), int):
                    rac.skin = True
                    self.cle_skin(n["skin"], cles)
            if not rac.insts:
                continue
            rac.cles, rac.imgs = frozenset(cles), frozenset(imgs)
            rac.tri = sum(i.tri for i in rac.insts)
            if self.P.exclure:
                # décision sur le nom, le nombre de triangles et le nombre de meshes de l'objet racine ; JAMAIS sur l'étendue
                # (la boîte d'un petit mesh qui partage un tampon de sommets est gonflée)
                nd = self.nodes[r]
                nom = nd.get("name") or (self.meshes[nd["mesh"]].get("name") if "mesh" in nd else "") or ""
                if any(rx.search(nom) for rx in self.P.exclure):
                    if rac.tri <= self.P.exclure_max_tri and len(rac.insts) <= self.P.exclure_max_meshes:
                        self.exclus.append({"nom": nom or _tr("py.glb2tiles.nud_0", r), "tri": rac.tri, "meshes": len(rac.insts), "cles": rac.cles, "imgs": rac.imgs})
                        continue
                    self.gardes += 1
            rac.lo = [min(i.lo[k] for i in rac.insts) for k in range(3)]
            rac.hi = [max(i.hi[k] for i in rac.insts) for k in range(3)]
            rac.centre = [(rac.lo[k] + rac.hi[k]) / 2 for k in range(3)]
            rac.etendue = max(rac.hi[0] - rac.lo[0], rac.hi[2] - rac.lo[2])
            rac.poids = sum(self.cb[k] for k in rac.cles) + sum(self.img_oct[i] for i in rac.imgs)
            rac.entier = rac.skin or (rac.poids <= self.P.entier_poids and rac.etendue <= self.P.entier_etendue)
            self.racines.append(rac)
            self.insts.extend(rac.insts)
        # octets gagnés : géométrie et images qu'aucun objet conservé n'utilise
        ks, im = set(), set()
        for rac in self.racines:
            ks |= rac.cles
            im |= rac.imgs
        ek, ei = set(), set()
        for x in self.exclus:
            ek |= x["cles"]
            ei |= x["imgs"]
        self.octets_exclus = sum(self.cb[k] for k in ek - ks) + sum(self.img_oct[i] for i in ei - im)
        # géométrie et images des exclus que des objets conservés utilisent aussi (même primitive, même texture) : retirer l'objet ne les économise pas
        self.octets_partages = sum(self.cb[k] for k in ek & ks) + sum(self.img_oct[i] for i in ei & im)

    def nom_noeud(self, ni):
        """Nom d'un nœud pour les références : son nom, sinon celui de son mesh (comme les objets nommés que voit le chargeur)."""
        n = self.nodes[ni]
        nm = n.get("name") or ""
        if not nm and isinstance(n.get("mesh"), int) and 0 <= n["mesh"] < len(self.meshes):
            nm = self.meshes[n["mesh"]].get("name") or ""
        return re.sub(r"[\x00-\x1f]", "", str(nm))

    def calculer_references(self):
        """Référence stable de chaque nœud dans le GLB ENTIER (v32), même règle que resolveMeshRef de core.js : le nom s'il est unique, sinon
        « nom#index », index = rang du nœud parmi les nœuds de ce nom dans l'ordre de parcours (pré-ordre, enfants dans l'ordre du fichier).
        Les nœuds exclus par --exclude comptent (la référence ne dépend pas de ce qu'on retire). Boîte (monde) de l'objet entier : union des
        boîtes de toutes les instances de ses descendants, y compris celles qui sont dans d'autres tuiles."""
        self.ref_de, self.box_de = {}, {}
        if not self.P.references:
            return
        ordre = [ni for r in self.racines_ids for ni in self.noeuds_racine.get(r, ())]
        noms = {ni: self.nom_noeud(ni) for ni in ordre}
        total = collections.Counter(nm for nm in noms.values() if nm)
        vu = collections.Counter()
        for ni in ordre:
            nm = noms[ni]
            if not nm:
                continue
            ref = nm if total[nm] == 1 else f"{nm}#{vu[nm]}"
            vu[nm] += 1
            if len(ref) <= 200:
                self.ref_de[ni] = ref
        for it in self.insts:
            n = it.node
            while n is not None:
                b = self.box_de.get(n)
                if b is None:
                    self.box_de[n] = [list(it.lo), list(it.hi)]
                else:
                    for k in range(3):
                        b[0][k] = min(b[0][k], it.lo[k])
                        b[1][k] = max(b[1][k], it.hi[k])
                n = self.parent.get(n)
        self.nb_refs, self.nb_partages = len(self.ref_de), sum(1 for nm, c in total.items() if c > 1)

    def est_terrain(self, rac):
        return rac.terrain

    def cle_skin(self, si, cles):
        skins = self.glb.g.get("skins", [])
        if not (0 <= si < len(skins)):
            raise ErreurGlb(_tr("py.glb2tiles.skin_0_inexistant", si))
        k = ("skin", si)
        if k not in self.cb:
            ib = skins[si].get("inverseBindMatrices")
            self.cb[k] = self.glb.acc(ib).count * 64 if ib is not None else 0
        cles.add(k)

    def construire_unites(self):
        self.unites = []
        for rac in self.racines:
            if rac.entier:
                u = Unite()
                u.racine, u.node, u.entier, u.cles, u.imgs, u.tri = rac, None, True, rac.cles, rac.imgs, rac.tri
                u.cx, u.cz, u.ninst, u.etendue = rac.centre[0], rac.centre[2], len(rac.insts), rac.etendue
                u.nom = self.nodes[rac.id].get("name") or _tr("py.glb2tiles.nud_0", rac.id)
                self.unites.append(u)
            else:
                for it in rac.insts:
                    mi = self.mesh_info[it.mesh]
                    u = Unite()
                    u.racine, u.node, u.entier, u.cles, u.imgs, u.tri = rac, it.node, False, mi.cles, mi.imgs, it.tri
                    u.cx, u.cz, u.ninst = it.centre[0], it.centre[2], 1
                    u.etendue = max(it.hi[0] - it.lo[0], it.hi[2] - it.lo[2])
                    u.nom = self.nodes[it.node].get("name") or self.meshes[it.mesh].get("name") or _tr("py.glb2tiles.nud_0", it.node)
                    self.unites.append(u)

    def donnees_image(self, ii):
        """Octets d'une image (bufferView lu dans le GLB, ou adresse data:) ; None si l'adresse data: est illisible."""
        src = self.glb.g["images"][ii]
        if "bufferView" in src:
            bv = self.glb.vue(src["bufferView"])
            return self.glb.lire(bv.get("byteOffset", 0), bv.get("byteLength", 0))
        try:
            return base64.b64decode(src["uri"].split(",", 1)[1], validate=False) if ";base64," in src["uri"][:80] else None
        except (ValueError, IndexError):
            return b""

    def verifier_images(self):
        """Images embarquées vides ou invalides (0 octet, autre format que PNG/JPEG/WebP, tronquées) parmi celles que les unités utilisent.
        img_ko = leurs numéros ; elles seront remplacées par un petit PNG gris dans chaque tuile qui les utilise."""
        utilisees = sorted({i for u in self.unites for i in u.imgs})
        self.img_ko = set()
        if not utilisees:
            return
        pg = Progres("images", len(utilisees))
        for n, ii in enumerate(utilisees):
            src = self.glb.g["images"][ii]
            if "bufferView" in src:
                bv = self.glb.vue(src["bufferView"])
                off, ln = bv.get("byteOffset", 0), bv.get("byteLength", 0)
                ok = image_valide(lambda o, k: self.glb.lire(off + o, k), ln)
            else:
                d = self.donnees_image(ii)
                ok = d is None or image_valide(lambda o, k: d[o:o + k], len(d))
            if not ok:
                self.img_ko.add(ii)
            pg.avance(n + 1)

    def images_remplacees(self, tuiles):
        """(images distinctes remplacées, occurrences) : une occurrence = une image invalide dans une tuile (elle y serait écrite une fois)."""
        tous = set()
        occ = 0
        for t in tuiles:
            im = {i for u in t.units for i in u.imgs} & self.img_ko
            tous |= im
            occ += len(im)
        return len(tous), occ

    # -- poids d'un groupe d'unités
    def poids(self, units):
        ks, im, tri = set(), set(), 0
        for u in units:
            ks |= u.cles
            im |= u.imgs
            tri += u.tri
        geo = sum(map(self.cb.__getitem__, ks))
        img = sum(self.img_oct[i] for i in im)
        return geo, img, tri

    # -- quadtree adaptatif sur X,Z
    def decouper(self):
        P = self.P
        units = self.unites
        if not units:
            return []
        x0, z0 = min(u.cx for u in units), min(u.cz for u in units)
        cote = max(max(u.cx for u in units) - x0, max(u.cz for u in units) - z0, 1e-6)
        res = []

        def rec(niveau, i, j, ox, oz, c, liste):
            geo, img, tri = self.poids(liste)
            if (geo + img > P.budget or tri > P.budget_tri) and c > P.cote_min and len(liste) > 1 and niveau < 40:
                demi = c / 2
                enf = {}
                for u in liste:
                    a = 1 if u.cx >= ox + demi else 0
                    b = 1 if u.cz >= oz + demi else 0
                    enf.setdefault((a, b), []).append(u)
                for (a, b), sous in sorted(enf.items()):
                    rec(niveau + 1, 2 * i + a, 2 * j + b, ox + a * demi, oz + b * demi, demi, sous)
            else:
                res.append(Tuile(niveau, i, j, liste))

        rec(0, 0, 0, x0, z0, cote, list(units))
        res.sort(key=lambda t: (t.niveau, t.i, t.j))
        return res

    def stats_tuiles(self, tuiles):
        out = []
        for t in tuiles:
            geo, img, tri = self.poids(t.units)
            out.append((geo, img, tri))
        return out

    def hors_budget(self, tuiles):
        """Avertissements pour les tuiles qui dépassent le budget (mesh unique trop lourd, cellule minimale atteinte)."""
        P = self.P
        res = []
        for t in tuiles:
            geo, img, tri = self.poids([*t.units])
            if geo + img <= P.budget and tri <= P.budget_tri:
                continue
            lourds = sorted(t.units, key=lambda u: -(sum(self.cb[k] for k in u.cles) + sum(self.img_oct[i] for i in u.imgs)))[:3]
            noms = "; ".join(f"« {u.nom} » {u.etendue:.0f} m, "
                             f"{mo(sum(self.cb[k] for k in u.cles) + sum(self.img_oct[i] for i in u.imgs)):.1f} Mo" for u in lourds)
            res.append(_tr("py.glb2tiles.tuile_0_hors_budget_1_1f", t.nom, mo(geo + img), fmt(tri), noms))
        return res

    def aberrantes(self):
        """Instances très éloignées du centre médian ou d'étendue démesurée."""
        if not self.insts:
            return [], (0, 0)
        mx = statistics.median(i.centre[0] for i in self.insts)
        mz = statistics.median(i.centre[2] for i in self.insts)
        lst = []
        for it in self.insts:
            d = math.hypot(it.centre[0] - mx, it.centre[2] - mz)
            ext = max(it.hi[k] - it.lo[k] for k in range(3))
            lst.append((d, ext, it))
        return lst, (mx, mz)


# ---------------------------------------------------------------- écriture d'une tuile
class Assemblage:
    """Construit un GLB de tuile en mémoire : nœuds, meshes, matériaux, textures, images, accessors."""

    def __init__(self, plan):
        self.plan, self.glb = plan, plan.glb
        self.g = plan.glb.g
        self.parts = []
        self.bin_len = 0
        self.views, self.accessors = [], []
        self.o_geo = self.o_img = 0
        self.gris, self.nb_remplacees = None, 0
        self.prim_out = {}
        self.mesh_idx, self.mat_idx, self.tex_idx, self.img_idx, self.samp_idx, self.skin_idx = {}, {}, {}, {}, {}, {}
        self.meshes_o, self.mats_o, self.texs_o, self.imgs_o, self.samps_o, self.skins_o = [], [], [], [], [], []

    def vue(self, data, cible=None, stride=None, geo=True):
        if self.bin_len % 4:
            pad = 4 - self.bin_len % 4
            self.parts.append(bytes(pad))
            self.bin_len += pad
        v = {"buffer": 0, "byteOffset": self.bin_len, "byteLength": len(data)}
        if stride:
            v["byteStride"] = stride
        if cible:
            v["target"] = cible
        self.parts.append(data)
        self.bin_len += len(data)
        reel = (len(data) + 3) & ~3
        if geo:
            self.o_geo += reel
        else:
            self.o_img += reel
        self.views.append(v)
        return len(self.views) - 1

    def accessor(self, vue, comp, count, typ, norm=False, mn=None, mx=None):
        d = {"bufferView": vue, "componentType": comp, "count": count, "type": typ}
        if norm:
            d["normalized"] = True
        if mn is not None:
            d["min"], d["max"] = mn, mx
        self.accessors.append(d)
        return len(self.accessors) - 1

    # -- compactage d'une primitive
    def prim(self, key):
        r = self.prim_out.get(key)
        if r is not None:
            return r
        glb = self.glb
        p = self.plan.prims[key]
        idx = None
        rel = None
        if p.indices is None:
            used, contiguo, imin = p.used, True, 0
            nouveau = None
        else:
            ia = glb.acc(p.indices)
            code = CODE[ia.comp]
            idx = array.array(code)
            mq = Marques()
            for bloc in glb.blocs_indices(p.indices):
                mq.ajouter(bloc)
                idx.extend(bloc)
            used, imin = mq.compter(), mq.imin
            contiguo = used == len(mq.flags)
            sortie = "H" if taille_indices(used) == 2 else U32
            if contiguo:
                if imin:
                    nouveau = array.array(sortie, map(imin.__rsub__, idx))
                elif sortie != code:
                    nouveau = array.array(sortie, idx)
                else:
                    nouveau = idx
            else:
                rel = list(itertools.compress(range(len(mq.flags)), mq.flags))
                remap = array.array(U32, bytes(4 * len(mq.flags)))
                collections.deque(map(remap.__setitem__, rel, range(len(rel))), maxlen=0)
                src = map(imin.__rsub__, idx) if imin else idx
                nouveau = array.array(sortie, map(remap.__getitem__, src))
            del idx
        res = {"targets": [], "indices": None}
        res["attrs"] = {nom: self.attribut(ai, nom == "POSITION", imin, used, contiguo, rel) for nom, ai in p.attrs.items()}
        for t in p.targets:
            res["targets"].append({nom: self.attribut(ai, False, imin, used, contiguo, rel) for nom, ai in t.items()})
        if nouveau is not None:
            v = self.vue(nouveau.tobytes(), 34963)
            res["indices"] = self.accessor(v, 5123 if nouveau.typecode == "H" else 5125, len(nouveau), "SCALAR")
        self.prim_out[key] = res
        return res

    def attribut(self, ai, avec_minmax, imin, used, contiguo, rel):
        glb = self.glb
        a = glb.acc(ai)
        es, so = a.es, es_sortie(a.es)
        n = used if rel is None else (rel[-1] + 1 if rel else 0)     # lignes de la plage lue
        raw = glb.rangee(a, imin, n)
        if contiguo and a.stride == so == es:
            data = bytes(raw[:used * es])
        else:
            mv = memoryview(raw)
            offs = range(0, used * a.stride, a.stride) if rel is None else [r * a.stride for r in rel]
            if so == es:
                data = b"".join([mv[o:o + es] for o in offs])
            else:
                pad = bytes(so - es)
                data = b"".join([bytes(mv[o:o + es]) + pad for o in offs])
        mm = minmax_donnees(data, a, so) if avec_minmax else None
        v = self.vue(data, 34962, stride=so if so != es else None)
        return self.accessor(v, a.comp, used, a.type, a.norm, mm[0] if mm else None, mm[1] if mm else None)

    # -- mesh, matériau, texture, image, skin
    def mesh(self, m):
        if m in self.mesh_idx:
            return self.mesh_idx[m]
        src = self.plan.meshes[m]
        prims = []
        for pr in src.get("primitives", []):
            key = cle_prim(pr)
            if self.plan.prims[key].vide:
                continue
            o = self.prim(key)
            d = {"attributes": dict(o["attrs"])}
            if o["indices"] is not None:
                d["indices"] = o["indices"]
            if pr.get("mode", 4) != 4:
                d["mode"] = pr["mode"]
            if isinstance(pr.get("material"), int) and 0 <= pr["material"] < len(self.plan.mats):
                d["material"] = self.materiau(pr["material"])
            if o["targets"]:
                d["targets"] = [dict(t) for t in o["targets"]]
            if "extras" in pr:
                d["extras"] = pr["extras"]
            prims.append(d)
        if not prims:
            self.mesh_idx[m] = None
            return None
        d = {"primitives": prims}
        for k in ("name", "weights", "extras"):
            if k in src:
                d[k] = src[k]
        self.meshes_o.append(d)
        self.mesh_idx[m] = len(self.meshes_o) - 1
        return self.mesh_idx[m]

    def materiau(self, mi):
        if mi in self.mat_idx:
            return self.mat_idx[mi]
        d = json.loads(json.dumps(self.plan.mats[mi]))

        def remap(t):
            t["index"] = self.texture(t["index"])
        parcourir_textures(d, remap)
        self.mats_o.append(d)
        self.mat_idx[mi] = len(self.mats_o) - 1
        return self.mat_idx[mi]

    def texture(self, ti):
        if ti in self.tex_idx:
            return self.tex_idx[ti]
        if not (0 <= ti < len(self.plan.texs)):
            raise ErreurGlb(_tr("py.glb2tiles.texture_0_inexistante", ti))
        d = json.loads(json.dumps(self.plan.texs[ti]))
        if isinstance(d.get("source"), int):
            d["source"] = self.image(d["source"])
        for e in d.get("extensions", {}).values():
            if isinstance(e, dict) and isinstance(e.get("source"), int):
                e["source"] = self.image(e["source"])
        if isinstance(d.get("sampler"), int):
            si = d["sampler"]
            if si not in self.samp_idx:
                self.samps_o.append(self.g["samplers"][si])
                self.samp_idx[si] = len(self.samps_o) - 1
            d["sampler"] = self.samp_idx[si]
        self.texs_o.append(d)
        self.tex_idx[ti] = len(self.texs_o) - 1
        return self.tex_idx[ti]

    def image(self, ii):
        if ii in self.img_idx:
            return self.img_idx[ii]
        if ii in self.plan.img_ko:
            # image vide, d'un autre format ou tronquée : un seul PNG gris par tuile, partagé par toutes ses références
            if self.gris is None:
                self.imgs_o.append({"name": "image-remplacee", "mimeType": "image/png", "bufferView": self.vue(png_gris(), geo=False)})
                self.gris = len(self.imgs_o) - 1
            self.img_idx[ii] = self.gris
            self.nb_remplacees += 1
            return self.gris
        src = self.g["images"][ii]
        d = {k: v for k, v in src.items() if k in ("name", "mimeType", "extras")}
        if "bufferView" in src:
            bv = self.glb.vue(src["bufferView"])
            data = self.glb.lire(bv.get("byteOffset", 0), bv.get("byteLength", 0))
            d["bufferView"] = self.vue(data, geo=False)
        else:
            d["uri"] = src["uri"]
        self.imgs_o.append(d)
        self.img_idx[ii] = len(self.imgs_o) - 1
        return self.img_idx[ii]

    def skin(self, si, new_id):
        if si in self.skin_idx:
            return self.skin_idx[si]
        src = self.g["skins"][si]
        d = {"joints": [new_id[j] for j in src["joints"]]}
        if isinstance(src.get("skeleton"), int) and src["skeleton"] in new_id:
            d["skeleton"] = new_id[src["skeleton"]]
        ib = src.get("inverseBindMatrices")
        if ib is not None:
            a = self.glb.acc(ib)
            raw = self.glb.rangee(a, 0, a.count)
            mv = memoryview(raw)
            data = b"".join([mv[o:o + a.es] for o in range(0, a.count * a.stride, a.stride)]) if a.stride != a.es else bytes(raw)
            d["inverseBindMatrices"] = self.accessor(self.vue(data), a.comp, a.count, a.type)
        if "name" in src:
            d["name"] = src["name"]
        self.skins_o.append(d)
        self.skin_idx[si] = len(self.skins_o) - 1
        return self.skin_idx[si]


def ecrire_tuile(plan, tuile, chemin):
    """Écrit le GLB d'une tuile ; renvoie sa fiche pour X.tiles.json."""
    nodes = plan.nodes
    asm = Assemblage(plan)
    affectes, avec_mesh, insts = set(), [], []
    for u in tuile.units:
        if u.entier:
            affectes.update(u.racine.nodes)
            insts.extend(u.racine.insts)
        else:
            affectes.add(u.node)
            insts.extend(i for i in u.racine.insts if i.node == u.node)
    avec_mesh = {i.node for i in insts}
    ens = set(affectes)
    for n in affectes:                         # joints d'un skin : dans la tuile, même hors de l'objet
        si = nodes[n].get("skin")
        if isinstance(si, int):
            sk = plan.glb.g["skins"][si]
            ens.update(j for j in sk["joints"])
            if isinstance(sk.get("skeleton"), int):
                ens.add(sk["skeleton"])
    for n in list(ens):                        # ancêtres : transformations d'origine conservées
        p = plan.parent.get(n)
        while p is not None and p not in ens:
            ens.add(p)
            p = plan.parent.get(p)
    racines = sorted(n for n in ens if plan.parent.get(n) not in ens)
    ordre = []
    pile = list(reversed(racines))
    while pile:
        n = pile.pop()
        ordre.append(n)
        pile.extend(reversed([c for c in nodes[n].get("children", []) if c in ens]))
    new_id = {n: k for k, n in enumerate(ordre)}
    nodes_o = []
    for n in ordre:
        src = nodes[n]
        d = {}
        if "name" in src:
            d["name"] = src["name"]
        for k in ("matrix", "translation", "rotation", "scale", "weights", "extras"):
            if k in src:
                d[k] = src[k]
        ref = plan.ref_de.get(n)
        if ref is not None and isinstance(d.get("extras", {}), dict):
            # v32 : référence stable dans le modèle d'origine et boîte monde de l'objet ENTIER (même quand il est réparti sur plusieurs tuiles)
            d["extras"] = dict(d.get("extras", {}), ref=ref)
            b = plan.box_de.get(n)
            if b is not None:
                d["extras"]["box"] = [round(v, 3) for v in b[0] + b[1]]
        if n in avec_mesh:
            mi = asm.mesh(src["mesh"])
            if mi is not None:
                d["mesh"] = mi
        if n in affectes and isinstance(src.get("skin"), int) and "mesh" in d:
            d["skin"] = asm.skin(src["skin"], new_id)
        ch = [new_id[c] for c in src.get("children", []) if c in ens]
        if ch:
            d["children"] = ch
        nodes_o.append(d)
    js = {"asset": {"version": "2.0", "generator": f"glb2tiles {VERSION}"}, "scene": 0,
          "scenes": [{"nodes": [new_id[n] for n in racines]}], "nodes": nodes_o}
    for nom, lst in (("meshes", asm.meshes_o), ("materials", asm.mats_o), ("textures", asm.texs_o), ("samplers", asm.samps_o),
                     ("images", asm.imgs_o), ("skins", asm.skins_o), ("accessors", asm.accessors), ("bufferViews", asm.views)):
        if lst:
            js[nom] = lst
    present = set()
    extensions_presentes(js, present)
    for cle in ("extensionsUsed", "extensionsRequired"):
        liste = [e for e in plan.glb.g.get(cle, []) if e in present]
        if liste:
            js[cle] = liste
    total_bin = (asm.bin_len + 3) & ~3
    js["buffers"] = [{"byteLength": total_bin}]
    jb = json.dumps(js, separators=(",", ":")).encode("utf-8")
    jb += b" " * (-len(jb) % 4)
    total = 12 + 8 + len(jb) + 8 + total_bin
    if total > LIMITE_GLB:
        raise ErreurGlb(_tr("py.glb2tiles.tuile_0_1_2f_go_au", tuile.nom, total / 1024 ** 3))
    tmp = str(chemin) + ".tmp"
    with open(tmp, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total))
        f.write(struct.pack("<II", len(jb), 0x4E4F534A))
        f.write(jb)
        f.write(struct.pack("<II", total_bin, 0x004E4942))
        for part in asm.parts:
            f.write(part)
        f.write(bytes(total_bin - asm.bin_len))
    os.replace(tmp, chemin)
    lo = [min(i.lo[k] for i in insts) for k in range(3)]
    hi = [max(i.hi[k] for i in insts) for k in range(3)]
    return {"file": None, "level": tuile.niveau, "i": tuile.i, "j": tuile.j, "min": lo, "max": hi,
            "instances": len(insts), "triangles": sum(i.tri for i in insts), "bytes": total,
            "geometryBytes": asm.o_geo, "imageBytes": asm.o_img, "replacedImages": asm.nb_remplacees}


# ---------------------------------------------------------------- rapports
def quantile(v, q):
    v = sorted(v)
    return v[min(len(v) - 1, max(0, math.ceil(q * len(v)) - 1))] if v else 0


def recommandation(glb, plan, tuiles):
    P = plan.P
    tri = sum(i.tri for i in plan.insts)
    taille = glb.taille - getattr(plan, "octets_exclus", 0)        # sans les objets exclus
    if mo(taille) <= P.seuil_mo and tri <= P.seuil_tri:
        return False, (_tr("py.glb2tiles.recommandation_pas_de_decoupage_necessaire_0", mo(taille), P.seuil_mo, fmt(tri), fmt(P.seuil_tri)))
    geo_u = sum(plan.cb[k] for k in {k for u in plan.unites for k in u.cles})
    st = plan.stats_tuiles(tuiles)
    dup = sum(s[0] for s in st) / geo_u if geo_u else 1.0
    return True, _tr("py.glb2tiles.recommandation_decouper_budget_0_g_mo", P.budget_mo, len(tuiles), virg(dup))


def lignes_exclusions(plan):
    """Récapitulatif de --exclude : nombre, 20 noms les plus fréquents, octets gagnés ; liste vide sans option."""
    P = plan.P
    if not P.exclure:
        return []
    out = [_tr("py.glb2tiles.objets_exclus_exclure_au_plus_0", P.exclure_max_tri, P.exclure_max_meshes, len(plan.exclus), fmt(sum(x['tri'] for x in plan.exclus)), fmt(plan.octets_exclus), mo(plan.octets_exclus))]
    if plan.exclus:
        out.append(_tr("py.glb2tiles.octets_des_exclus_qu_un_objet", fmt(plan.octets_partages), mo(plan.octets_partages)))
        if plan.octets_exclus == 0:
            out.append(_tr("py.glb2tiles.0_octet_gagne_toute_la_geometrie"))
    if plan.gardes:
        out.append(_tr("py.glb2tiles.0_objet_s_au_nom_correspondant", plan.gardes))
    for nom, n in collections.Counter(x["nom"] for x in plan.exclus).most_common(20):
        out.append(f"  - {n} x « {nom[:70]} »")
    return out


def ligne_images(plan, tuiles):
    """Images vides ou invalides remplacées par un PNG gris (une phrase)."""
    dist, occ = plan.images_remplacees(tuiles)
    return (_tr("py.glb2tiles.images_vides_ou_invalides_remplacees_par", GRIS_IMAGE, fmt(dist), fmt(occ)))


def rapport_analyse(glb, plan, tuiles):
    P = plan.P
    out = []
    out.append(_tr("py.glb2tiles.mesures_de_glb_stats"))
    out.extend(stats().rapport(glb.chemin, P.bloc, glb.g, glb.njson))
    out.append("")
    # meshes les plus lourds
    insts_mesh = collections.defaultdict(list)
    for it in plan.insts:
        insts_mesh[it.mesh].append(it)
    lourds = sorted(plan.mesh_info.items(), key=lambda kv: -sum(plan.cb[k] for k in set(kv[1].prims)))[:10]
    out.append(_tr("py.glb2tiles.les_10_meshes_les_plus_lourds"))
    for m, mi in lourds:
        o = sum(plan.cb[k] for k in set(mi.prims))
        its = insts_mesh.get(m, [])
        if its:
            e = its[0]
            dim = f"{e.hi[0] - e.lo[0]:.1f} x {e.hi[1] - e.lo[1]:.1f} x {e.hi[2] - e.lo[2]:.1f} m"
        else:
            dim = _tr("py.glb2tiles.sans_instance")
        nom = plan.meshes[m].get("name") or f"mesh {m}"
        out.append(_tr("py.glb2tiles.0_1_2f_mo_2_triangles", nom[:40], mo(o), fmt(mi.tri), dim, len(its)))
    # instances aberrantes
    lst, (mx, mz) = plan.aberrantes()
    out.append("")
    out.append(_tr("py.glb2tiles.les_10_instances_les_plus_eloignees", mx, mz))
    for d, ext, it in sorted(lst, key=lambda t: -t[0])[:10]:
        nom = plan.nodes[it.node].get("name") or _tr("py.glb2tiles.nud_0", it.node)
        out.append(_tr("py.glb2tiles.0_distance_1_0f_m_etendue", nom[:40], d, ext))
    # découpage prévu
    st = plan.stats_tuiles(tuiles)
    geo_u = sum(plan.cb[k] for k in {k for u in plan.unites for k in u.cles})
    img_u = sum(plan.img_oct[i] for i in {i for u in plan.unites for i in u.imgs})
    dup_g = sum(s[0] for s in st) / geo_u if geo_u else 1.0
    dup_i = sum(s[1] for s in st) / img_u if img_u else 1.0
    out.append("")
    out.append(_tr("py.glb2tiles.decoupage_prevu_budget_0_g_mo", P.budget_mo, fmt(P.budget_tri), P.cote_min))
    out.append(_tr("py.glb2tiles.tuiles_0_duplication_prevue_geometrie_1", len(tuiles), virg(dup_g), virg(dup_i)))
    if st:
        poids = [(s[0] + s[1]) / MO for s in st]
        tris = [s[2] for s in st]
        out.append(_tr("py.glb2tiles.poids_par_tuile_mo_mediane_0", quantile(poids, 0.5), quantile(poids, 0.9), max(poids)))
        out.append(_tr("py.glb2tiles.triangles_par_tuile_mediane_0_90", fmt(quantile(tris, 0.5)), fmt(quantile(tris, 0.9)), fmt(max(tris))))
    ent = sum(1 for r in plan.racines if r.entier)
    skin = sum(1 for r in plan.racines if r.skin)
    out.extend(lignes_exclusions(plan))
    out.append(ligne_images(plan, tuiles))
    out.append(_tr("py.glb2tiles.objets_racine_0_gardes_entiers_1", len(plan.racines), ent, skin, len(plan.racines) - ent))
    avert = plan.avertissements + signalements(plan) + plan.hors_budget(tuiles)
    if avert:
        out.append("Avertissements :")
        out.extend("  - " + a for a in avert)
    out.append(_tr("py.glb2tiles.lecture_0_octets_lus_sur_1", fmt(glb.octets_lus), fmt(glb.taille), fmt(glb.plus_grande_lecture), fmt(plan.positions_lues)))
    out.append("")
    out.append(recommandation(glb, plan, tuiles)[1])
    return out


def signalements(plan):
    """Valeurs aberrantes (distance au centre médian ou étendue au-delà de --outlier)."""
    lst, _ = plan.aberrantes()
    seuil = plan.P.aberrant
    mauvais = sorted([t for t in lst if t[0] > seuil or t[1] > seuil], key=lambda t: -max(t[0], t[1]))
    if not mauvais:
        return []
    ex = ", ".join(_tr("py.glb2tiles.0_1_0f_m_du_centre", (plan.nodes[t[2].node].get('name') or 'nœud ' + str(t[2].node))[:30], t[0], t[1]) for t in mauvais[:3])
    return [_tr("py.glb2tiles.0_instance_s_aberrante_s_a", len(mauvais), seuil, ex)]


# ---------------------------------------------------------------- vue d'ensemble (X.overview.glb)
# Une seule géométrie légère pour toute la région, sans image : un nœud par fichier de tuile (mêmes clés que X.tiles.json), pour que la
# coquille masque la partie d'une cellule dès que la tuile détaillée correspondante est affichée. Les couleurs sont des couleurs de sommets
# (COLOR_0) : un seul matériau, donc au plus un appel de dessin par tuile. Sans normales : la coquille (GLTFLoader) rend alors en ombrage plat.
# Chaque primitive UNIQUE est simplifiée une seule fois (regroupement de sommets sur une grille proportionnelle à sa boîte), puis recopiée
# avec la matrice de chaque instance. Le terrain est rééchantillonné à part sur un réseau régulier commun à toutes ses pièces.
OV_PAS_TERRAIN = 4.0
OV_SEUIL = 3.0
OV_SEUIL_MAX = 24.0
OV_RESOLUTION = 10
OV_BUDGET_MO = 25.0
OV_BUDGET_TRI = 1500000
OV_GRIS_DEFAUT = (0.8, 0.8, 0.8)
LUT_LIN = [(c / 255 / 12.92 if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4) for c in range(256)]


class ParamsOv:
    def __init__(self, budget_mo=OV_BUDGET_MO, budget_tri=OV_BUDGET_TRI, seuil=OV_SEUIL, seuil_max=OV_SEUIL_MAX, resolution=OV_RESOLUTION,
                 pas_terrain=OV_PAS_TERRAIN):
        self.budget_mo, self.budget = budget_mo, budget_mo * MO
        self.budget_tri = budget_tri
        self.seuil, self.seuil_max = seuil, max(seuil, seuil_max)
        self.resolution = max(2, int(resolution))
        self.pas_terrain = max(0.25, float(pas_terrain))

    def dict(self):
        return {"budgetMB": self.budget_mo, "budgetTriangles": self.budget_tri, "minExtent": self.seuil, "maxExtent": self.seuil_max,
                "resolution": self.resolution, "terrainStep": self.pas_terrain}


class Couleurs:
    """Couleur unie (linéaire, octets RGBA) de chaque matériau : couleur moyenne de sa texture si Pillow est disponible, sinon couleur de base."""

    def __init__(self, plan):
        self.plan = plan
        self.cache, self.moy = {}, {}
        self.pil = None
        try:
            from PIL import Image
            self.pil = Image
        except ImportError:
            pass
        self.sans_pillow = self.illisibles = self.moyennes = 0

    def moyenne_image(self, ii):
        """Couleur moyenne linéaire (r, v, b) d'une image, pondérée par l'opacité ; None si illisible."""
        if ii in self.moy:
            return self.moy[ii]
        res = None
        if self.pil is not None and ii not in self.plan.img_ko:
            try:
                import io
                import warnings
                d = self.plan.donnees_image(ii)
                if d:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        im = self.pil.open(io.BytesIO(bytes(d)))
                        try:
                            im.draft("RGB", (32, 32))
                        except Exception:
                            pass
                        box = getattr(getattr(self.pil, "Resampling", self.pil), "BOX")
                        px = list(im.convert("RGBA").resize((8, 8), box).getdata())
                    sa = sum(p[3] for p in px)
                    if sa > 0:
                        res = tuple(sum(LUT_LIN[p[k]] * p[3] for p in px) / sa for k in range(3))
                        self.moyennes += 1
            except Exception:
                res = None
            if res is None:
                self.illisibles += 1
        self.moy[ii] = res
        return res

    def materiau(self, mi):
        """(r, v, b, a) en octets, ou None si le matériau est translucide (alphaMode BLEND : verre, effets), omis de la vue d'ensemble."""
        if mi is None or not (0 <= mi < len(self.plan.mats)):
            c = tuple(int(v * 255 + 0.5) for v in OV_GRIS_DEFAUT)
            return c + (255,)
        if mi in self.cache:
            return self.cache[mi]
        m = self.plan.mats[mi]
        res = None
        if m.get("alphaMode") != "BLEND":
            pbr = m.get("pbrMetallicRoughness", {})
            fac, tex = pbr.get("baseColorFactor", [1, 1, 1, 1]), pbr.get("baseColorTexture")
            sg = m.get("extensions", {}).get("KHR_materials_pbrSpecularGlossiness")
            if isinstance(sg, dict):
                fac, tex = sg.get("diffuseFactor", [1, 1, 1, 1]), sg.get("diffuseTexture")
            fac = [float(v) for v in fac[:3]] if isinstance(fac, list) and len(fac) >= 3 and all(isinstance(v, (int, float)) for v in fac[:3]) else [1.0, 1.0, 1.0]
            moy = None
            if isinstance(tex, dict) and isinstance(tex.get("index"), int) and 0 <= tex["index"] < len(self.plan.texs):
                if self.pil is None:
                    self.sans_pillow += 1
                else:
                    for ii in images_de_texture(self.plan.texs[tex["index"]]):
                        if 0 <= ii < len(self.plan.glb.g.get("images", [])):
                            moy = self.moyenne_image(ii)
                            break
            if moy is None:
                moy = (1.0, 1.0, 1.0)
            res = tuple(int(min(1.0, max(0.0, moy[k] * fac[k])) * 255 + 0.5) for k in range(3)) + (255,)
        self.cache[mi] = res
        return res


def lire_geometrie(plan, key):
    """Indices d'origine, plage de lignes et colonnes X, Y, Z des positions d'une primitive : (idx, imin, drapeaux, (xs, ys, zs))."""
    glb = plan.glb
    p = plan.prims[key]
    pa = glb.acc(p.attrs["POSITION"])
    if p.indices is None:
        idx, flags = array.array(U32, range(pa.count)), None
    else:
        idx, mq = array.array(CODE[glb.acc(p.indices).comp]), Marques()
        for bloc in glb.blocs_indices(p.indices):
            mq.ajouter(bloc)
            idx.extend(bloc)
        flags = mq.flags
    n = p.imax - p.imin + 1
    if pa.ncomp < 3 or pa.stride % TAILLE[pa.comp]:
        raise ErreurGlb(_tr("py.glb2tiles.accessor_0_positions_non_gerees", pa.i))
    raw = bytes(glb.rangee(pa, p.imin, n)) + bytes(pa.stride - pa.es)
    arr = array.array(CODE[pa.comp])
    arr.frombytes(raw)
    se = pa.stride // TAILLE[pa.comp]
    cols = [arr[k::se] for k in range(3)]
    if pa.comp != 5126 and pa.norm:
        cols = [[decode_norm(v, pa.comp, True) for v in c] for c in cols]
    return idx, p.imin, flags, cols


def regrouper(idx, imin, flags, cols, origine, cell):
    """Regroupement de sommets : un sommet par cellule de côté `cell` (moyenne des sommets de la cellule), triangles dégénérés et doublons
    retirés. cell=None : pas de regroupement (sommets utilisés seulement). Rend (sommets à plat array('f'), triangles à plat list d'indices)."""
    xs, ys, zs = cols
    n = len(xs)
    rows = list(itertools.compress(range(n), flags)) if flags is not None else range(n)
    ux, uy, uz = [xs[r] for r in rows], [ys[r] for r in rows], [zs[r] for r in rows]
    if cell is None:
        cid = list(range(len(ux)))
        nc = len(ux)
        px, py, pz = ux, uy, uz
    else:
        ox, oy, oz = origine
        inv = 1.0 / cell
        M = 4096
        keys = [(int((x - ox) * inv) * M + int((y - oy) * inv)) * M + int((z - oz) * inv) for x, y, z in zip(ux, uy, uz)]
        ids = {}
        cid = [ids.setdefault(k, len(ids)) for k in keys]
        nc = len(ids)
        sx, sy, sz, cnt = [0.0] * nc, [0.0] * nc, [0.0] * nc, [0] * nc
        for c, x, y, z in zip(cid, ux, uy, uz):
            sx[c] += x
            sy[c] += y
            sz[c] += z
            cnt[c] += 1
        px, py, pz = [a / b for a, b in zip(sx, cnt)], [a / b for a, b in zip(sy, cnt)], [a / b for a, b in zip(sz, cnt)]
    rowcid = array.array("i", bytes(4 * n))
    collections.deque(map(rowcid.__setitem__, rows, cid), maxlen=0)
    it = iter([rowcid[i - imin] for i in idx[:len(idx) // 3 * 3]])
    vus, tris = set(), []
    for a, b, c in zip(it, it, it):
        if a == b or b == c or a == c:
            continue
        k = (a, b, c) if a < b and a < c else ((b, c, a) if b < c else (c, a, b))
        if k in vus:
            continue
        vus.add(k)
        tris.append(a)
        tris.append(b)
        tris.append(c)
    # sommets réellement utilisés
    new = {}
    for c in tris:
        if c not in new:
            new[c] = len(new)
    verts = array.array("f")
    for c in new:
        verts.append(px[c])
        verts.append(py[c])
        verts.append(pz[c])
    return verts, [new[c] for c in tris]


class Simplif:
    """Primitives simplifiées, une fois chacune (clé : primitive, résolution), puis réutilisées par toutes les instances."""

    def __init__(self, plan, resolution):
        self.plan, self.res = plan, resolution
        self.cache = {}
        self.lus = 0

    def prim(self, key):
        r = self.cache.get(key)
        if r is not None:
            return r
        p = self.plan.prims[key]
        idx, imin, flags, cols = lire_geometrie(self.plan, key)
        etendue = max(p.hi[k] - p.lo[k] for k in range(3))
        cell = None if p.tri <= 24 or etendue <= 0 else etendue / self.res
        verts, tris = regrouper(idx, imin, flags, cols, p.lo, cell)
        self.lus += p.used
        r = (verts, array.array(U32, tris))
        self.cache[key] = r
        return r


def matrice_pos(m, verts):
    """Positions à plat transformées par la matrice monde m (16 nombres, colonnes)."""
    it = iter(verts)
    out = array.array("f")
    m0, m1, m2, m4, m5, m6, m8, m9, m10, m12, m13, m14 = m[0], m[1], m[2], m[4], m[5], m[6], m[8], m[9], m[10], m[12], m[13], m[14]
    for x, y, z in zip(it, it, it):
        out.append(m0 * x + m4 * y + m8 * z + m12)
        out.append(m1 * x + m5 * y + m9 * z + m13)
        out.append(m2 * x + m6 * y + m10 * z + m14)
    return out


class AccTuile:
    """Géométrie de la vue d'ensemble pour une tuile : primitives de 65 535 sommets au plus (indices 16 bits)."""

    def __init__(self):
        self.morceaux = []        # chacun : [positions array('f'), couleurs bytearray, indices list]
        self.tri = 0

    def ajouter(self, pos, col, tris):
        nv = len(pos) // 3
        if not self.morceaux or (self.morceaux[-1][0] and len(self.morceaux[-1][0]) // 3 + nv > 65535):
            self.morceaux.append([array.array("f"), bytearray(), array.array(U32)])
        m = self.morceaux[-1]
        base = len(m[0]) // 3
        m[0].extend(pos)
        m[1].extend(col)
        m[2].extend(base + i for i in tris)
        self.tri += len(tris) // 3


def terrain_vue(plan, tuiles_de, couleurs, pas, acc):
    """Réseau régulier de pas `pas` commun à toutes les pièces du terrain : hauteur et couleur interpolées dans les triangles d'origine, donc
    aucune fente entre pièces (un point du réseau sur un bord commun reçoit la même hauteur des deux côtés). tuiles_de : liste (instance, tuile).
    Les pièces sont lues l'une après l'autre (jamais toutes en mémoire)."""
    if not tuiles_de:
        return 0
    ox = min(it.lo[0] for it, _ in tuiles_de)
    oz = min(it.lo[2] for it, _ in tuiles_de)
    ech = {}                      # (i, j) -> (y, couleur RGBA)
    e = 1e-6
    for it, nom in tuiles_de:
        for key, pr in plan.mesh_prims[it.mesh]:
            p = plan.prims[key]
            if p.vide or p.mode != 4:
                continue
            idx, imin, flags, cols = lire_geometrie(plan, key)
            n = len(cols[0])
            rows = list(itertools.compress(range(n), flags)) if flags is not None else range(n)
            m = plan.monde[it.node]
            xs, ys, zs = cols
            wx = [m[0] * xs[r] + m[4] * ys[r] + m[8] * zs[r] + m[12] for r in rows]
            wy = [m[1] * xs[r] + m[5] * ys[r] + m[9] * zs[r] + m[13] for r in rows]
            wz = [m[2] * xs[r] + m[6] * ys[r] + m[10] * zs[r] + m[14] for r in rows]
            col = couleur_sommets(plan, pr, rows, couleurs)
            ou = array.array("i", [-1]) * n
            collections.deque(map(ou.__setitem__, rows, itertools.count()), maxlen=0)
            t3 = [ou[i - imin] for i in idx[:len(idx) // 3 * 3]]
            for a, b, c in zip(t3[0::3], t3[1::3], t3[2::3]):
                x1, x2, x3, z1, z2, z3 = wx[a], wx[b], wx[c], wz[a], wz[b], wz[c]
                ia, ib = math.ceil((min(x1, x2, x3) - ox) / pas - e), math.floor((max(x1, x2, x3) - ox) / pas + e)
                ja, jb = math.ceil((min(z1, z2, z3) - oz) / pas - e), math.floor((max(z1, z2, z3) - oz) / pas + e)
                if ia > ib or ja > jb:
                    continue
                den = (z2 - z3) * (x1 - x3) + (x3 - x2) * (z1 - z3)
                if abs(den) < 1e-12:
                    continue
                for i in range(ia, ib + 1):
                    px = ox + i * pas
                    for j in range(ja, jb + 1):
                        if (i, j) in ech:
                            continue
                        pz = oz + j * pas
                        l1 = ((z2 - z3) * (px - x3) + (x3 - x2) * (pz - z3)) / den
                        l2 = ((z3 - z1) * (px - x3) + (x1 - x3) * (pz - z3)) / den
                        l3 = 1.0 - l1 - l2
                        if l1 < -e or l2 < -e or l3 < -e:
                            continue
                        ca, cb, cc = col[a], col[b], col[c]
                        ech[(i, j)] = (l1 * wy[a] + l2 * wy[b] + l3 * wy[c],
                                       bytes(int(l1 * ca[k] + l2 * cb[k] + l3 * cc[k] + 0.5) for k in range(4)))
    total = 0
    for it, nom in tuiles_de:
        # cases possédées par la pièce : coin bas dans [min, max[ (intervalle semi-ouvert : jamais deux pièces pour une case, jamais de case sans pièce)
        i0, i1 = math.ceil((it.lo[0] - ox) / pas - e), math.ceil((it.hi[0] - ox) / pas - e)
        j0, j1 = math.ceil((it.lo[2] - oz) / pas - e), math.ceil((it.hi[2] - oz) / pas - e)
        pos, cols, tris, local = array.array("f"), bytearray(), [], {}

        def sommet(i, j):
            v = local.get((i, j))
            if v is None:
                s = ech[(i, j)]
                v = local[(i, j)] = len(local)
                pos.extend((ox + i * pas, s[0], oz + j * pas))
                cols.extend(s[1])
            return v
        for i in range(i0, i1):
            for j in range(j0, j1):
                if (i, j) in ech and (i + 1, j) in ech and (i, j + 1) in ech and (i + 1, j + 1) in ech:
                    v00, v10, v01, v11 = sommet(i, j), sommet(i + 1, j), sommet(i, j + 1), sommet(i + 1, j + 1)
                    tris.extend((v00, v01, v10, v10, v01, v11))
        if tris:
            acc.setdefault(nom, AccTuile()).ajouter(pos, cols, tris)
            total += len(tris) // 3
    return total


def couleur_sommets(plan, pr, rows, couleurs):
    """Couleurs RGBA (octets) des sommets utilisés : COLOR_0 s'il existe (terrain d'oar2glb), sinon la couleur du matériau."""
    ai = pr.get("attributes", {}).get("COLOR_0")
    fond = couleurs.materiau(pr.get("material")) or (200, 200, 200, 255)
    if ai is None:
        return [fond] * len(rows)
    glb = plan.glb
    a = glb.acc(ai)
    if a.ncomp not in (3, 4) or a.stride % TAILLE[a.comp]:
        return [fond] * len(rows)
    p = plan.prims[cle_prim(pr)]
    n = p.imax - p.imin + 1
    arr = array.array(CODE[a.comp])
    arr.frombytes(bytes(glb.rangee(a, p.imin, n)) + bytes(a.stride - a.es))
    se = a.stride // TAILLE[a.comp]
    out = []
    for r in rows:
        v = [decode_norm(arr[r * se + k], a.comp, a.norm) for k in range(3)]
        out.append(tuple(int(min(1.0, max(0.0, c)) * 255 + 0.5) for c in v) + (255,))
    return out


def fusionner(morceaux):
    """Regroupe les morceaux consécutifs tant que le total reste à 65 535 sommets au plus : une primitive (un appel de dessin) par tuile en général."""
    out = []
    for pos, col, idx in morceaux:
        nv = len(pos) // 3
        if out and len(out[-1][0]) // 3 + nv <= 65535:
            base = len(out[-1][0]) // 3
            out[-1][0].extend(pos)
            out[-1][1].extend(col)
            out[-1][2].extend(base + i for i in idx)
        else:
            out.append([array.array("f", pos), bytearray(col), array.array(U32, idx)])
    return out


def ecrire_vue_ensemble(plan, groupes, chemin, tuiles_fichiers):
    """Écrit X.overview.glb : un nœud par tuile (nom = fichier de la tuile), un seul matériau (couleurs de sommets). Rend (octets, triangles, nœuds)."""
    parts, bin_len = [], 0
    views, accessors, meshes, nodes = [], [], [], []

    def vue(data, cible):
        nonlocal bin_len
        if bin_len % 4:
            parts.append(bytes(4 - bin_len % 4))
            bin_len += 4 - bin_len % 4
        views.append({"buffer": 0, "byteOffset": bin_len, "byteLength": len(data), "target": cible})
        parts.append(bytes(data))
        bin_len += len(data)
        return len(views) - 1
    tri = 0
    for nom in tuiles_fichiers:
        morceaux = fusionner([m for acc in groupes for m in (acc[nom].morceaux if nom in acc else ())])
        if not morceaux:
            continue
        prims = []
        for pos, col, idx in morceaux:
            nv = len(pos) // 3
            if not idx:
                continue
            mn = [min(pos[k::3]) for k in range(3)]
            mx = [max(pos[k::3]) for k in range(3)]
            ap = len(accessors)
            accessors.append({"bufferView": vue(pos.tobytes(), 34962), "componentType": 5126, "count": nv, "type": "VEC3", "min": mn, "max": mx})
            accessors.append({"bufferView": vue(col, 34962), "componentType": 5121, "normalized": True, "count": nv, "type": "VEC4"})
            if nv <= 65535:
                ib, comp = array.array("H", idx).tobytes(), 5123
            else:
                ib, comp = array.array(U32, idx).tobytes(), 5125
            accessors.append({"bufferView": vue(ib, 34963), "componentType": comp, "count": len(idx), "type": "SCALAR"})
            prims.append({"attributes": {"POSITION": ap, "COLOR_0": ap + 1}, "indices": ap + 2, "material": 0, "mode": 4})
            tri += len(idx) // 3
        if not prims:
            continue
        meshes.append({"name": "vue:" + nom, "primitives": prims})
        nodes.append({"name": nom, "mesh": len(meshes) - 1, "extras": {"tile": nom}})
    js = {"asset": {"version": "2.0", "generator": f"glb2tiles {VERSION} (vue d'ensemble)"}, "scene": 0,
          "scenes": [{"nodes": list(range(len(nodes)))}], "nodes": nodes, "meshes": meshes, "accessors": accessors, "bufferViews": views,
          "materials": [{"name": "vue-ensemble", "doubleSided": True,
                         "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 1}}]}
    total_bin = (bin_len + 3) & ~3
    js["buffers"] = [{"byteLength": total_bin}]
    if not nodes:
        for k in ("meshes", "accessors", "bufferViews", "buffers"):
            js.pop(k)
    jb = json.dumps(js, separators=(",", ":")).encode("utf-8")
    jb += b" " * (-len(jb) % 4)
    total = 12 + 8 + len(jb) + (8 + total_bin if nodes else 0)
    if total > LIMITE_GLB:
        raise ErreurGlb(_tr("py.glb2tiles.la_vue_d_ensemble_depasse_la"))
    tmp = str(chemin) + ".tmp"
    with open(tmp, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total))
        f.write(struct.pack("<II", len(jb), 0x4E4F534A))
        f.write(jb)
        if nodes:
            f.write(struct.pack("<II", total_bin, 0x004E4942))
            for part in parts:
                f.write(part)
            f.write(bytes(total_bin - bin_len))
    os.replace(tmp, chemin)
    return total, tri, len(nodes)


def instances_de(plan, tuile):
    """(instances, terrain) d'une tuile : toutes les instances de ses unités, séparées selon que la racine est du terrain (extras.terrain)."""
    objets, terrain, vus = [], [], set()
    for u in tuile.units:
        lst = u.racine.insts if u.entier else [i for i in u.racine.insts if i.node == u.node]
        for it in lst:
            if it.node in vus:
                continue
            vus.add(it.node)
            (terrain if plan.est_terrain(u.racine) else objets).append(it)
    return objets, terrain


def vue_ensemble(plan, tuiles, noms, OP, chemin):
    """Construit et écrit la vue d'ensemble. noms : fichier de chaque tuile (même ordre que `tuiles`). Rend le dictionnaire du rapport."""
    t0 = time.time()
    log(_tr("py.glb2tiles.vue_d_ensemble_budget_0_g", OP.budget_mo, fmt(OP.budget_tri), OP.seuil, OP.resolution, OP.pas_terrain))
    couleurs = Couleurs(plan)
    omis = {"petits": 0, "squelette": 0, "translucides": 0, "budget": 0}
    tp, cand = [], []             # pièces de terrain (instance, tuile) ; objets candidats (étendue, instance, tuile)
    for t, nom in zip(tuiles, noms):
        objets, terrain = instances_de(plan, t)
        tp += [(it, nom) for it in terrain]
        for it in objets:
            if isinstance(plan.nodes[it.node].get("skin"), int):
                omis["squelette"] += 1
                continue
            cand.append((max(it.hi[k] - it.lo[k] for k in range(3)), it, nom))
    # terrain : au plus la moitié des budgets ; sinon le pas du réseau grossit (x 1,5) jusqu'à ce qu'il tienne
    pas = OP.pas_terrain
    while True:
        acc_t = {}
        tri_terrain = terrain_vue(plan, tp, couleurs, pas, acc_t) if tp else 0
        oct_terrain = sum(len(p) * 4 + len(c) + len(ix) * 2 for a in acc_t.values() for p, c, ix in a.morceaux)
        if not tp or (tri_terrain <= OP.budget_tri / 2 and oct_terrain <= OP.budget / 2) or pas > 4096:
            break
        pas *= 1.5
        log(_tr("py.glb2tiles.vue_d_ensemble_terrain_trop_lourd", pas))
    log(_tr("py.glb2tiles.vue_d_ensemble_terrain_0_piece", len(tp), fmt(tri_terrain), pas))
    res = OP.resolution
    while True:
        base = sorted((c for c in cand if c[0] >= OP.seuil), key=lambda c: -c[0])
        omis["petits"] = len(cand) - len(base)
        simp = Simplif(plan, res)
        meshes = sorted({c[1].mesh for c in base})
        pg = Progres("vue d'ensemble : primitives", len(meshes))
        info, transl = {}, 0       # mesh -> (parties (sommets, triangles, couleur), triangles, sommets)
        for n, m in enumerate(meshes):
            parts, tri, nv = [], 0, 0
            for key, pr in plan.mesh_prims[m]:
                p = plan.prims[key]
                if p.vide or p.mode != 4:
                    continue
                col = couleurs.materiau(pr.get("material"))
                if col is None:
                    transl += 1
                    continue
                v, tr = simp.prim(key)
                if len(tr):
                    parts.append((v, tr, col))
                    tri += len(tr) // 3
                    nv += len(v) // 3
            info[m] = (parts, tri, nv)
            pg.avance(n + 1)
        omis["translucides"] = transl
        # les plus grands d'abord, tant que le budget le permet : le seuil effectif est l'étendue du dernier objet gardé
        reste_tri, reste_oct = OP.budget_tri - tri_terrain, OP.budget - oct_terrain
        gardes, tri_tot, oct_tot = [], 0, 0
        for c in base:
            parts, tri, nv = info[c[1].mesh]
            if not parts:
                continue
            ob = tri * 6 + nv * 16
            if tri_tot + tri > reste_tri or oct_tot + ob > reste_oct:
                break
            gardes.append(c)
            tri_tot += tri
            oct_tot += ob
        coupes = [c for c in base[len(gardes):] if info[c[1].mesh][0]]
        limite = max((c[0] for c in coupes), default=0.0)
        if limite > OP.seuil_max and res > 3:
            res = max(3, int(res * 0.7))
            log(_tr("py.glb2tiles.vue_d_ensemble_budget_atteint_avant", limite, res))
            continue
        break

    def assembler(liste):
        acc = {}
        for e, it, nom in liste:
            a = acc.setdefault(nom, AccTuile())
            m = plan.monde[it.node]
            for v, tr, col in info[it.mesh][0]:
                a.ajouter(matrice_pos(m, v), bytes(col) * (len(v) // 3), list(tr))
        return acc
    acc_o = assembler(gardes)
    total, tri, nn = ecrire_vue_ensemble(plan, [acc_t, acc_o], chemin, noms)
    while total > OP.budget and gardes:            # poids réel au-dessus du budget (estimation trop optimiste) : on retire les plus petits
        gardes = gardes[:len(gardes) - max(1, len(gardes) // 10)]
        acc_o = assembler(gardes)
        total, tri, nn = ecrire_vue_ensemble(plan, [acc_t, acc_o], chemin, noms)
    omis["budget"] = len(base) - len(gardes) - sum(1 for c in base if not info[c[1].mesh][0])
    seuil_eff = min((c[0] for c in gardes), default=OP.seuil)
    log(_tr("py.glb2tiles.vue_d_ensemble_0_1f_mo", total / MO, fmt(tri), len(gardes), len(cand), nn, time.time() - t0))
    return {"file": chemin.name, "bytes": total, "triangles": tri, "terrainTriangles": tri_terrain, "objects": len(gardes), "candidates": len(cand),
            "omitted": {"small": omis["petits"], "skinned": omis["squelette"], "translucentPrimitives": omis["translucides"], "budget": omis["budget"]},
            "effectiveMinExtent": round(seuil_eff, 2), "resolution": res, "effectiveTerrainStep": round(pas, 3), "seconds": round(time.time() - t0, 1),
            "colors": {"textureAverages": couleurs.moyennes, "unreadable": couleurs.illisibles, "withoutPillow": couleurs.sans_pillow,
                       "pillow": couleurs.pil is not None},
            "params": OP.dict()}


def ecrire_tout(glb, plan, tuiles, sortie, nom):
    """Écrit les tuiles ; ensuite seulement, supprime les T_*.glb d'une exécution précédente qui ne figurent plus dans le nouvel index.
    Rend (fiches, dossier, nombre de fichiers supprimés)."""
    dossier = Path(sortie) / f"{nom}.tiles"
    dossier.mkdir(parents=True, exist_ok=True)
    fiches = []
    pg = Progres("tuiles", len(tuiles))
    for n, t in enumerate(tuiles):
        f = ecrire_tuile(plan, t, dossier / f"{t.nom}.glb")
        f["file"] = f"{nom}.tiles/{t.nom}.glb"
        fiches.append(f)
        pg.avance(n + 1)
    nouveaux = {Path(f["file"]).name for f in fiches}
    supprimes = 0
    for ancien in dossier.glob("T_*_*_*.glb"):
        if ancien.name not in nouveaux:
            ancien.unlink()
            supprimes += 1
    return fiches, dossier, supprimes


def lignes_taille_instances(plan):
    """Répartition des instances par étendue (plus grande dimension) : aide à choisir --ov-threshold de la vue d'ensemble."""
    out = [_tr("py.glb2tiles.etendue_des_instances_plus_grande_dimension")]
    tot_i, tot_t = len(plan.insts), sum(i.tri for i in plan.insts)
    for sv in (1, 2, 3, 4, 8, 16, 32, 64):
        n = t = 0
        for i in plan.insts:
            if max(i.hi[k] - i.lo[k] for k in range(3)) >= sv:
                n += 1
                t += i.tri
        out.append(f"  - au moins {sv} m : {fmt(n)} instances ({100 * n / max(1, tot_i):.0f} %), {fmt(t)} triangles ({100 * t / max(1, tot_t):.0f} %)")
    return out


# v43 : anciens noms d'options (avant la v43), toujours acceptés : remplacés avant la lecture de la ligne de commande
OLD_OPTIONS = {"--budget-tri": "--budget-triangles", "--entier-poids": "--whole-weight", "--entier-etendue": "--whole-extent", "--seuil": "--threshold",
               "--seuil-tri": "--threshold-triangles", "--aberrant": "--outlier", "--bloc": "--block", "--exclure": "--exclude",
               "--exclure-max-tri": "--exclude-max-triangles", "--exclure-max-meshes": "--exclude-max-meshes", "--sans-references": "--no-refs",
               "--sans-vue-ensemble": "--no-overview", "--vue-ensemble-seule": "--overview-only", "--ov-budget-tri": "--ov-budget-triangles",
               "--ov-seuil": "--ov-threshold", "--ov-seuil-max": "--ov-threshold-max", "--ov-terrain-pas": "--ov-terrain-step", "--forcer": "--force",
               "--sortie": "--output"}


def old_options(argv):
    """Remplace les anciens noms d'options par les nouveaux (« --nom=valeur » compris)."""
    out = []
    for x in argv:
        k, eq, v = str(x).partition("=")
        out.append(OLD_OPTIONS.get(k, k) + eq + v if k.startswith("--") else x)
    return out


def main(argv=None, log_path=None):
    global LOG_PATH
    LOG_PATH = log_path
    ap = argparse.ArgumentParser(description=_tr("py.glb2tiles.desc", VERSION), epilog=_tr("py.glb2tiles.epilog"), formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False)
    i18n_add_common(ap)
    ap.add_argument("glb", help=_tr("py.glb2tiles.glb_d_entree"))
    ap.add_argument("--version", action="version", version=f"glb2tiles {version_tag()}", help=_tr("py.common.version"))
    ap.add_argument("--analyse", action="store_true", help=_tr("py.glb2tiles.lecture_seule_mesures_decoupage_prevu_recomm"))
    ap.add_argument("--budget", type=float, default=32.0, help=_tr("py.glb2tiles.mo_par_tuile_defaut_32"))
    ap.add_argument("--budget-triangles", metavar="BUDGET_TRIANGLES", dest="budget_tri", type=int, default=1500000, help=_tr("py.glb2tiles.triangles_par_tuile_defaut_1500000"))
    ap.add_argument("--min", metavar="MIN", type=float, default=16.0, dest="cote_min", help=_tr("py.glb2tiles.cote_minimal_d_une_cellule_en"))
    ap.add_argument("--whole-weight", metavar="WHOLE_WEIGHT", dest="entier_poids", type=float, default=16.0, help=_tr("py.glb2tiles.mo_un_objet_racine_plus_leger"))
    ap.add_argument("--whole-extent", metavar="WHOLE_EXTENT", dest="entier_etendue", type=float, default=256.0, help=_tr("py.glb2tiles.m_etendue_maximale_d_un_objet"))
    ap.add_argument("--threshold", metavar="THRESHOLD", dest="seuil", type=float, default=150.0, help=_tr("py.glb2tiles.mo_sous_ce_poids_et_sous"))
    ap.add_argument("--threshold-triangles", metavar="THRESHOLD_TRIANGLES", dest="seuil_tri", type=int, default=3000000, help=_tr("py.glb2tiles.triangles_pour_la_recommandation_pas_de"))
    ap.add_argument("--outlier", metavar="OUTLIER", dest="aberrant", type=float, default=1000.0, help=_tr("py.glb2tiles.m_distance_ou_etendue_au_dela"))
    ap.add_argument("--block", metavar="BLOCK", dest="bloc", type=float, default=256.0, help=_tr("py.glb2tiles.cote_des_blocs_de_la_section"))
    ap.add_argument("--exclude", dest="exclure", action="append", default=[], metavar="REGEX",
                    help=_tr("py.glb2tiles.retire_du_decoupage_les_objets_racine"))
    ap.add_argument("--exclude-max-triangles", metavar="EXCLUDE_MAX_TRIANGLES", dest="exclure_max_tri", type=int, default=24, help=_tr("py.glb2tiles.avec_exclure_triangles_au_plus_dans"))
    ap.add_argument("--exclude-max-meshes", metavar="EXCLUDE_MAX_MESHES", dest="exclure_max_meshes", type=int, default=1, help=_tr("py.glb2tiles.avec_exclure_meshes_au_plus_dans"))
    ap.add_argument("--no-refs", dest="sans_references", action="store_true", help=_tr("py.glb2tiles.ne_pas_ecrire_extras_ref_extras"))
    ap.add_argument("--no-overview", dest="sans_vue_ensemble", action="store_true", help=_tr("py.glb2tiles.ne_pas_ecrire_x_overview_glb"))
    ap.add_argument("--overview-only", dest="vue_ensemble_seule", action="store_true", help=_tr("py.glb2tiles.n_ecrire_que_x_overview_glb"))
    ap.add_argument("--ov-budget", type=float, default=OV_BUDGET_MO, help=_tr("py.glb2tiles.mo_poids_maximal_de_la_vue"))
    ap.add_argument("--ov-budget-triangles", metavar="OV_BUDGET_TRIANGLES", dest="ov_budget_tri", type=int, default=OV_BUDGET_TRI, help=_tr("py.glb2tiles.triangles_de_la_vue_d_ensemble"))
    ap.add_argument("--ov-threshold", metavar="OV_THRESHOLD", dest="ov_seuil", type=float, default=OV_SEUIL, help=_tr("py.glb2tiles.m_les_objets_dont_la_plus"))
    ap.add_argument("--ov-threshold-max", metavar="OV_THRESHOLD_MAX", dest="ov_seuil_max", type=float, default=OV_SEUIL_MAX, help=_tr("py.glb2tiles.m_si_le_budget_oblige_a"))
    ap.add_argument("--ov-resolution", type=int, default=OV_RESOLUTION, help=_tr("py.glb2tiles.cellules_sur_la_plus_grande_dimension"))
    ap.add_argument("--ov-terrain-step", metavar="OV_TERRAIN_STEP", dest="ov_terrain_pas", type=float, default=OV_PAS_TERRAIN, help=_tr("py.glb2tiles.m_pas_du_reseau_du_terrain"))
    ap.add_argument("--force", dest="forcer", action="store_true", help=_tr("py.glb2tiles.decouper_meme_si_la_recommandation_est"))
    ap.add_argument("--output", metavar="OUTPUT", dest="sortie", help=_tr("py.glb2tiles.dossier_de_sortie_defaut_a_cote"))
    ap.add_argument("--nopause", action="store_true", help=_tr("py.glb2tiles.ne_pas_attendre_entree_a_la"))
    a = ap.parse_args(old_options(sys.argv[1:] if argv is None else list(argv)))
    P = Params(a.budget, a.budget_tri, a.cote_min, a.entier_poids, a.entier_etendue, a.seuil, a.seuil_tri, a.aberrant, a.bloc,
               a.exclure, a.exclure_max_tri, a.exclure_max_meshes, not a.sans_references)
    OP = ParamsOv(a.ov_budget, a.ov_budget_tri, a.ov_seuil, a.ov_seuil_max, a.ov_resolution, a.ov_terrain_pas)
    if a.sans_vue_ensemble and a.vue_ensemble_seule:
        raise ErreurGlb(_tr("py.glb2tiles.sans_vue_ensemble_et_vue_ensemble"))
    t0 = time.time()
    chemin = Path(a.glb)
    if not chemin.is_file():
        raise ErreurGlb(_tr("py.glb2tiles.glb_introuvable_0", chemin))
    glb = Glb(chemin)
    try:
        log(_tr("py.glb2tiles.glb2tiles_0_1_1f_mo", chemin.name, mo(glb.taille)))
        plan = Plan(glb, P)
        if not plan.insts:
            raise ErreurGlb(_tr("py.glb2tiles.aucun_mesh_positionnable_dans_la_scene"))
        tuiles = plan.decouper()
        sortie = Path(a.sortie) if a.sortie else chemin.resolve().parent
        nom = chemin.stem
        if a.vue_ensemble_seule and not a.analyse:
            return vue_ensemble_seule(glb, plan, tuiles, sortie, nom, OP, t0)
        decoupe, phrase = recommandation(glb, plan, tuiles)
        if a.analyse:
            for ligne in rapport_analyse(glb, plan, tuiles):
                log(ligne)
            for ligne in lignes_taille_instances(plan):
                log(ligne)
            ancien = sortie / f"{nom}.tiles.json"       # v32 : tuiles déjà écrites sans les références d'objets
            if ancien.is_file():
                try:
                    d_anc = json.loads(ancien.read_text(encoding="utf-8-sig"))
                except ValueError:
                    d_anc = {}
                if isinstance(d_anc, dict) and d_anc.get("tiles") and not d_anc.get("nodeRefs"):
                    log(_tr("py.glb2tiles.avertissement_0_existe_deja_mais_ses", ancien.name))
            log(_tr("py.glb2tiles.temps_0_1f_s", time.time() - t0))
            return 0
        log(phrase)
        if not decoupe and not a.forcer:
            log(_tr("py.glb2tiles.rien_n_est_ecrit_forcer_pour"))
            return 0
        fiches, dossier, supprimes = ecrire_tout(glb, plan, tuiles, sortie, nom)
        geo_u = sum(plan.cb[k] for k in {k for u in plan.unites for k in u.cles})
        dup = sum(f["geometryBytes"] for f in fiches) / geo_u if geo_u else 1.0
        ent = sum(1 for r in plan.racines if r.entier)
        avert = plan.avertissements + signalements(plan) + plan.hors_budget(tuiles)
        img_dist, img_occ = plan.images_remplacees(tuiles)
        lo = [min(i.lo[k] for i in plan.insts) for k in range(3)]
        hi = [max(i.hi[k] for i in plan.insts) for k in range(3)]
        doc = {"version": FORMAT_TUILES, "generator": f"glb2tiles {VERSION}", "source": chemin.name,
               "extent": {"min": lo, "max": hi}, "params": P.dict(), "warnings": avert,
               "roots": {"whole": ent, "split": len(plan.racines) - ent},
               "duplication": round(dup, 3), "nodeRefs": 1 if P.references else 0, "replacedImages": {"distinct": img_dist, "occurrences": img_occ, "grey": GRIS_IMAGE}, "tiles": fiches}
        if P.exclure:
            doc["excluded"] = {"patterns": P.exclure_motifs, "maxTriangles": P.exclure_max_tri, "maxMeshes": P.exclure_max_meshes,
                               "count": len(plan.exclus), "triangles": sum(x["tri"] for x in plan.exclus), "bytesSaved": plan.octets_exclus, "bytesShared": plan.octets_partages,
                               "names": dict(collections.Counter(x["nom"] for x in plan.exclus).most_common(20))}
        ov = None
        if not a.sans_vue_ensemble:
            ov = vue_ensemble(plan, tuiles, [f["file"] for f in fiches], OP, Path(sortie) / f"{nom}.overview.glb")
            doc["overview"] = ov
        else:
            ancien = Path(sortie) / f"{nom}.overview.glb"
            if ancien.is_file():
                log(_tr("py.glb2tiles.avertissement_0_d_une_execution_precedente", ancien.name))
        ecrire_index(Path(sortie) / f"{nom}.tiles.json", doc)
        poids = [x["bytes"] / MO for x in fiches]
        tris = [x["triangles"] for x in fiches]
        log("")
        log(_tr("py.glb2tiles.rapport"))
        log(_tr("py.glb2tiles.tuiles_0_dans_1", len(fiches), dossier))
        if supprimes:
            log(_tr("py.glb2tiles.tuiles_d_une_execution_precedente_absentes", supprimes))
        log(_tr("py.glb2tiles.poids_mo_mediane_0_1f_90", quantile(poids, 0.5), quantile(poids, 0.9), max(poids)))
        log(_tr("py.glb2tiles.triangles_mediane_0_90_sous_1", fmt(quantile(tris, 0.5)), fmt(quantile(tris, 0.9)), fmt(max(tris))))
        log(_tr("py.glb2tiles.duplication_reelle_de_la_geometrie_somme", virg(dup)))
        log(_tr("py.glb2tiles.objets_racine_gardes_entiers_0_repartis", ent, len(plan.racines) - ent))
        for ligne in lignes_exclusions(plan):
            log(ligne)
        log(ligne_images(plan, tuiles))
        if P.references:
            log(_tr("py.glb2tiles.references_d_objets_extras_ref_extras", fmt(plan.nb_refs), fmt(plan.nb_partages)))
        else:
            log(_tr("py.glb2tiles.references_d_objets_non_ecrites_sans"))
        if ov:
            for ligne in lignes_vue_ensemble(ov):
                log(ligne)
        for w in avert:
            log(_tr("py.glb2tiles.warning_prefix") + w)
        log(_tr("py.glb2tiles.temps_0_1f_s_1_octets", time.time() - t0, fmt(glb.octets_lus), fmt(glb.taille)))
        return 0
    finally:
        glb.fermer()


def ecrire_index(chemin, doc):
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")


def lignes_vue_ensemble(ov):
    om = ov["omitted"]
    out = [_tr("py.glb2tiles.vue_d_ensemble_0_1_1f", ov['file'], ov['bytes'] / MO, fmt(ov['triangles']), fmt(ov['terrainTriangles']), fmt(ov['objects']), fmt(ov['candidates']), ov['seconds']),
           _tr("py.glb2tiles.objets_omis_0_trop_petits_etendue", fmt(om['small']), fmt(om['budget']), fmt(om['skinned']), fmt(om['translucentPrimitives'])),
           _tr("py.glb2tiles.etendue_minimale_effective_0_g_m", ov['effectiveMinExtent'], ov['params']['minExtent'], ov['resolution'], ov['effectiveTerrainStep'], ov['params']['terrainStep'])]
    c = ov["colors"]
    if c["pillow"]:
        out.append(_tr("py.glb2tiles.couleurs_moyenne_de_texture_pour_0", fmt(c['textureAverages']), fmt(c['unreadable'])))
    else:
        out.append(_tr("py.glb2tiles.couleurs_pillow_absent_couleur_de_base", fmt(c['withoutPillow'])))
    return out


def vue_ensemble_seule(glb, plan, tuiles, sortie, nom, OP, t0):
    """--overview-only : les tuiles et X.tiles.json existent ; le découpage recalculé doit correspondre à l'index (mêmes fichiers)."""
    idx = Path(sortie) / f"{nom}.tiles.json"
    if not idx.is_file():
        raise ErreurGlb(_tr("py.glb2tiles.0_introuvable_vue_ensemble_seule_suppose", idx, sortie))
    try:
        doc = json.loads(idx.read_text(encoding="utf-8-sig"))
    except ValueError as e:
        raise ErreurGlb(_tr("py.glb2tiles.0_illisible_1", idx, e))
    noms = [f"{nom}.tiles/{t.nom}.glb" for t in tuiles]
    index = {f.get("file"): f for f in doc.get("tiles", []) if isinstance(f, dict)}
    if set(noms) != set(index):
        raise ErreurGlb(_tr("py.glb2tiles.le_decoupage_recalcule_0_tuiles_ne", len(noms), idx.name, len(index)))
    for t, f in zip(tuiles, noms):
        if index[f].get("triangles") != sum(u.tri for u in t.units) or index[f].get("instances") != sum(u.ninst for u in t.units):
            raise ErreurGlb(_tr("py.glb2tiles.la_tuile_0_n_a_plus", f, idx.name))
    if not doc.get("nodeRefs"):
        log(_tr("py.glb2tiles.avertissement_ces_tuiles_ont_ete_ecrites"))
    ov = vue_ensemble(plan, tuiles, noms, OP, Path(sortie) / f"{nom}.overview.glb")
    doc["overview"] = ov
    ecrire_index(idx, doc)
    log("")
    log(_tr("py.glb2tiles.rapport"))
    for ligne in lignes_vue_ensemble(ov):
        log(ligne)
    log(_tr("py.glb2tiles.temps_0_1f_s_1_octets", time.time() - t0, fmt(glb.octets_lus), fmt(glb.taille)))
    return 0


if __name__ == "__main__":
    sys.argv = old_options(sys.argv)
    if "--version" in sys.argv[1:]:      # ni journal ni pause « Entrée »
        print(_tr("py.glb2tiles.glb2tiles_0_2", version_tag()))
        sys.exit(0)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    journal = Path(__file__).resolve().with_name("glb2tiles.log")
    with open(journal, "w", encoding="utf-8") as lf:
        lf.write(f"[glb2tiles] {version_tag()}\n")
    print(_tr("py.glb2tiles.glb2tiles_0", version_tag()))
    code = 0
    try:
        code = main(log_path=journal)
    except SystemExit as e:
        if isinstance(e.code, str):
            log(e.code)
        code = e.code if isinstance(e.code, int) else 1
    except ErreurGlb as e:
        log(_tr("py.glb2tiles.erreur_0", e))
        code = 2
    except Exception:
        log(traceback.format_exc())
        code = 1
    print(_tr("py.glb2tiles.log_0", journal))
    if "--nopause" not in sys.argv and sys.stdin and sys.stdin.isatty():      # ni console (script, tâche planifiée) : pas de pause
        try:
            input(_tr("py.glb2tiles.entree_pour_fermer"))
        except EOFError:
            pass
    sys.exit(code)
