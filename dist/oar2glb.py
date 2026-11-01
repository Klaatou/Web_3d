#!/usr/bin/env python3
"""
oar2glb.py - OAR OpenSim -> GLB unique (convoar + réparation + empaquetage)

Usage :  python oar2glb.py --version
         python oar2glb.py "P:\\chemin\\MaRegion.oar" [--reencode] [--max 600] [--convoar chemin\\convoar.exe] [--keep] [--keep-invisible] [--markers]
         python oar2glb.py "P:\\chemin\\MaRegion.oar" --diag [--glb MaRegion.glb]     (ne modifie rien, ne lance pas convoar)

Étapes :
 1. (option --reencode) textures J2K de l'OAR décodées puis réencodées proprement avec Pillow
    dans un OAR temporaire -> supprime les "unhandled number of components: 0" de convoar.
 2. convoar lancé via un petit lanceur convoar_inv.exe (compilé une fois avec le csc.exe de Windows)
    qui force la culture invariante : nombres en 0.5 et pas 0,5, sans toucher aux réglages Windows.
 3. Réparation du .gltf (backslashes orphelins) + contrôle de cohérence (tailles des vecteurs).
 4. Retrait des objets hors région (skybox à 3000 m...) : |coordonnée| > --max mètres.
 5. Meshes riggés (animesh) : bloc skin lu dans assets/*_mesh.llmesh ; échelle du prim ignorée, bind_shape_matrix
    appliquée aux sommets, modèle posé au sol (terrain de l'OAR) à la position de la racine de l'objet.
    Prims entièrement transparents (faces alpha 0 ou texture invisible standard) retirés (--keep-invisible pour les garder).
 6. Empaquetage en un seul .glb (buffers + textures intégrés), pur Python.
Sortie : MaRegion.glb à côté de l'OAR.
"""
import argparse, base64, io, json, math, os, re, shutil, struct, subprocess, sys, tarfile, time, traceback, uuid, zlib
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


VERSION = "1.0.1 (31/10/2026)"      # remplacé par build.py (fichier VERSION) dans dist/oar2glb.py
MARK = "7ca846fa"      # empreinte du fichier fabriqué, inscrite par build.py ; reste telle quelle depuis tools/


def version_tag():
    """version, suivie de l'empreinte du fichier quand build.py l'a inscrite"""
    return VERSION if MARK.startswith("__") else _tr("py.common.version_mark", VERSION, MARK)
CONVOAR_URL = "https://github.com/Misterblue/convoar/tree/master/bin"


def default_convoar():
    """convoar.exe quand --convoar n'est pas donné : variable CONVOAR, sinon convoar du PATH, sinon convoar.exe à côté de oar2glb.py"""
    return os.environ.get("CONVOAR") or shutil.which("convoar") or str(Path(__file__).resolve().with_name("convoar.exe"))

LAUNCHER_CS = r"""
using System; using System.Globalization; using System.IO; using System.Threading;
class ConvoarInvariant {
  static int Main(string[] a) {
    CultureInfo c = CultureInfo.InvariantCulture;
    CultureInfo.DefaultThreadCurrentCulture = c; CultureInfo.DefaultThreadCurrentUICulture = c;
    Thread.CurrentThread.CurrentCulture = c; Thread.CurrentThread.CurrentUICulture = c;
    return AppDomain.CurrentDomain.ExecuteAssembly(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "convoar.exe"), a);
  }
}
"""


# ---------- 1. réencodage des textures ----------
def reencode_one(data):
    # décode une texture J2K et la réencode proprement ; None si illisible (laissée telle quelle)
    from PIL import Image
    try:
        im = Image.open(io.BytesIO(data)); im.load()
        if im.mode not in ("L", "LA", "RGB", "RGBA"):
            im = im.convert("RGBA")
        n = max(1, min(6, int(math.log2(max(1, min(im.size)))) + 1))
        buf = io.BytesIO()
        im.save(buf, "JPEG2000", num_resolutions=n, no_jp2=True)   # codestream J2C brut, comme les assets OpenSim
        return buf.getvalue()
    except Exception:
        return None


def neutral_texture():
    # petit J2K gris, même format que reencode_one : remplace une texture que Pillow ne sait pas lire
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), (128, 128, 128)).save(buf, "JPEG2000", num_resolutions=3, no_jp2=True)
    return buf.getvalue()


REENC_BATCH = 512      # textures envoyées aux workers par lot : borne la mémoire (ex.map sur tout enverrait tout d'un coup)


def reencode_oar(src, dst):
    try:
        import PIL  # noqa: F401
    except ImportError:
        sys.exit(_tr("py.oar2glb.erreur_reencode_demande_pillow_absent_de", sys.executable, sys.executable))
    import time
    from concurrent.futures import ProcessPoolExecutor
    t0 = time.time()
    print(_tr("py.oar2glb.textures_lecture_de_0", src.name))
    members = []
    with tarfile.open(src, "r:*") as tin:
        for m in tin:
            f = tin.extractfile(m) if m.isfile() else None
            members.append((m, f.read() if f else None))
    sculpts = set()
    for m, d in members:
        if d is not None and m.name.startswith("objects/") and m.name.endswith(".xml"):
            sculpts.update(re.findall(r"<SculptTexture>\s*(?:<(?:UUID|Guid)>)?\s*([0-9a-fA-F-]{36})", d.decode("utf-8", "replace")))
    sculpts = {u.lower() for u in sculpts}
    idx = [i for i, (m, d) in enumerate(members)
           if d is not None and m.name.startswith("assets/") and m.name.endswith("_texture.jp2")
           and m.name[7:43].lower() not in sculpts]
    print(_tr("py.oar2glb.textures_0_sculpt_maps_laissees_intactes", len(sculpts)))
    workers = max(1, min(8, (os.cpu_count() or 2) - 1))   # 8 au plus : chaque worker garde ses textures décodées en mémoire
    print(_tr("py.oar2glb.textures_0_textures_a_reencoder_sur", len(idx), workers, time.time() - t0))
    ok = bad = k = 0
    grey, illisibles = neutral_texture(), []
    step = max(1, len(idx) // 20)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for b in range(0, len(idx), REENC_BATCH):
            sub = idx[b:b + REENC_BATCH]
            for i, res in zip(sub, ex.map(reencode_one, [members[i][1] for i in sub], chunksize=8)):
                k += 1
                m, _ = members[i]
                if res is None:      # illisible pour Pillow : le décodeur de convoar peut planter dessus, on met un gris neutre
                    bad += 1
                    illisibles.append(m.name)
                    res = grey
                else:
                    ok += 1
                m.size = len(res)
                members[i] = (m, res)
                if k % step == 0 or k == len(idx):
                    print(_tr("py.oar2glb.textures_0_1_2_3_0f", k, len(idx), 100 * k // len(idx), time.time() - t0), flush=True)
    print(_tr("py.oar2glb.textures_ecriture_de_0", dst.name))
    with tarfile.open(dst, "w:gz", compresslevel=1) as tout:
        for m, d in members:
            tout.addfile(m, io.BytesIO(d) if d is not None else None)
    liste = dst.with_name(dst.stem + "-illisibles.txt")
    if illisibles:
        liste.write_text("\n".join(illisibles) + "\n", encoding="utf-8")
    print(_tr("py.oar2glb.textures_0_reencodees_1_illisibles_remplacee", ok, bad)
          + (_tr("py.oar2glb.list_paren", liste.name) if illisibles else "") + f" - {time.time() - t0:.0f} s")


# ---------- lecture de l'OAR : objets, blocs skin des meshes, terrain ----------
# Textures « invisibles » standard (SL/OpenSim) : « Transparent » du sélecteur et IMG_INVISIBLE (invisiprim)
INVISIBLE_TEX = {"8dcd4a48-2d37-4909-9f78-f7a9eb4ef903", "3a367d1c-bef1-6d43-7595-e88c1e3aadb3"}
UUID_RX = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def llsd_bin(d, p=0):
    # LLSD binaire (en-têtes et blocs des .llmesh) -> (valeur, position suivante)
    t = d[p:p + 1]
    p += 1
    if t == b"{":
        n = struct.unpack_from(">I", d, p)[0]
        p += 4
        out = {}
        for _ in range(n):
            if d[p:p + 1] != b"k":
                raise ValueError(_tr("py.oar2glb.cle_llsd_attendue"))
            ln = struct.unpack_from(">I", d, p + 1)[0]
            key = d[p + 5:p + 5 + ln].decode("utf-8", "replace")
            out[key], p = llsd_bin(d, p + 5 + ln)
        if d[p:p + 1] != b"}":
            raise ValueError(_tr("py.oar2glb.fin_de_table_llsd_attendue"))
        return out, p + 1
    if t == b"[":
        n = struct.unpack_from(">I", d, p)[0]
        p += 4
        out = []
        for _ in range(n):
            v, p = llsd_bin(d, p)
            out.append(v)
        if d[p:p + 1] != b"]":
            raise ValueError(_tr("py.oar2glb.fin_de_tableau_llsd_attendue"))
        return out, p + 1
    if t == b"!":
        return None, p
    if t == b"1":
        return True, p
    if t == b"0":
        return False, p
    if t == b"i":
        return struct.unpack_from(">i", d, p)[0], p + 4
    if t == b"r":
        return struct.unpack_from(">d", d, p)[0], p + 8
    if t == b"d":
        return struct.unpack_from(">d", d, p)[0], p + 8
    if t == b"u":
        return d[p:p + 16], p + 16
    if t in (b"s", b"l", b"b"):
        ln = struct.unpack_from(">I", d, p)[0]
        v = d[p + 4:p + 4 + ln]
        return (v if t == b"b" else v.decode("utf-8", "replace")), p + 4 + ln
    raise ValueError(_tr("py.oar2glb.type_llsd_inconnu_0_r", t))


def llmesh_skin(data):
    # (skin, erreur) : skin = dict du bloc skin (zlib + LLSD), None si le mesh n'en a pas
    try:
        start = data.find(b"\n") + 1 if data[:2] == b"<?" else 0
        hdr, end = llsd_bin(data, start)
        sk = hdr.get("skin")
        if not isinstance(sk, dict) or not sk.get("size"):
            return None, None
        off, size = int(sk.get("offset", 0)), int(sk["size"])
        for base in (end, end + 1):     # les décalages partent de la fin de l'en-tête (un \n éventuel)
            try:
                skin, _ = llsd_bin(zlib.decompress(data[base + off:base + off + size]), 0)
                if isinstance(skin, dict):
                    return skin, None
            except Exception:
                continue
        return None, _tr("py.oar2glb.bloc_skin_present_mais_illisible")
    except Exception as e:
        return None, _tr("py.oar2glb.en_tete_du_mesh_illisible_0", e)


def llmesh_domains(data, n=256):
    # domaines de position (min, max) des premiers sous-maillages du plus haut niveau de détail ; [] si illisible
    try:
        start = data.find(b"\n") + 1 if data[:2] == b"<?" else 0
        hdr, end = llsd_bin(data, start)
        hl = hdr.get("high_lod")
        if not isinstance(hl, dict) or not hl.get("size"):
            return []
        for base in (end, end + 1):
            try:
                subs, _ = llsd_bin(zlib.decompress(data[base + int(hl.get("offset", 0)):base + int(hl.get("offset", 0)) + int(hl["size"])]), 0)
                out = []
                for sm in subs[:n]:
                    d = sm.get("PositionDomain") or {}
                    if "Min" in d and "Max" in d:
                        out.append((d["Min"], d["Max"]))
                return out
            except Exception:
                continue
    except Exception:
        pass
    return []


def llmesh_geometry(data, lod="high_lod"):
    # géométrie du plus haut niveau de détail d'un .llmesh : liste (une entrée par face, None si vide) de
    # {"pos": [(x, y, z)], "nor": [...] ou None, "uv": [(u, v)] ou None, "tri": [indices]} ; None si illisible
    import array
    try:
        start = data.find(b"\n") + 1 if data[:2] == b"<?" else 0
        hdr, end = llsd_bin(data, start)
        blk = hdr.get(lod)
        if not isinstance(blk, dict) or not blk.get("size"):
            return None
        off, size = int(blk.get("offset", 0)), int(blk["size"])
        subs = None
        for base in (end, end + 1):
            try:
                subs, _ = llsd_bin(zlib.decompress(data[base + off:base + off + size]), 0)
                break
            except Exception:
                continue
        if not isinstance(subs, list):
            return None

        def u16(b):
            a = array.array("H")
            a.frombytes(bytes(b[:len(b) // 2 * 2]))
            if sys.byteorder == "big":
                a.byteswap()
            return a
        out = []
        for sm in subs:
            if not isinstance(sm, dict) or sm.get("NoGeometry") or not sm.get("Position") or not sm.get("TriangleList"):
                out.append(None)
                continue
            d = sm.get("PositionDomain") or {}
            mn, mx = d.get("Min", [-0.5] * 3), d.get("Max", [0.5] * 3)
            a = u16(sm["Position"])
            n = len(a) // 3
            pos = [tuple(mn[k] + a[3 * i + k] / 65535.0 * (mx[k] - mn[k]) for k in range(3)) for i in range(n)]
            nor = None
            if sm.get("Normal"):
                b = u16(sm["Normal"])
                if len(b) >= 3 * n:
                    nor = [tuple(b[3 * i + k] / 65535.0 * 2.0 - 1.0 for k in range(3)) for i in range(n)]
            uv = None
            if sm.get("TexCoord0"):
                t = u16(sm["TexCoord0"])
                td = sm.get("TexCoord0Domain") or {}
                tmn, tmx = td.get("Min", [0.0, 0.0]), td.get("Max", [1.0, 1.0])
                if len(t) >= 2 * n:
                    uv = [tuple(tmn[k] + t[2 * i + k] / 65535.0 * (tmx[k] - tmn[k]) for k in range(2)) for i in range(n)]
            tri = list(u16(sm["TriangleList"]))
            tri = tri[:len(tri) // 3 * 3]
            out.append({"pos": pos, "nor": nor, "uv": uv, "tri": tri})
        return out
    except Exception:
        return None


def bind_shape(skin):
    m = skin.get("bind_shape_matrix") if skin else None
    if isinstance(m, list) and len(m) == 16 and all(isinstance(v, (int, float)) for v in m):
        return [float(v) for v in m]
    return None


def parse_texture_entry(b64):
    # TextureEntry OpenSim -> ({face: texture UUID}, {face: alpha 0..255}), clé None = face par défaut
    try:
        d = base64.b64decode(b64)
    except Exception:
        return None
    p = 0

    def faces():
        nonlocal p
        if p >= len(d):
            return None
        bits = 0
        while True:
            b = d[p]
            bits = (bits << 7) | (b & 0x7F)
            p += 1
            if not b & 0x80 or p >= len(d):
                break
        return [f for f in range(32) if bits >> f & 1] if bits else None

    def section(size, conv):
        nonlocal p
        out = {}
        if p + size > len(d):
            raise ValueError
        out[None] = conv(d[p:p + size])
        p += size
        while True:
            fs = faces()
            if fs is None:
                break
            if p + size > len(d):
                raise ValueError
            v = conv(d[p:p + size])
            p += size
            for f in fs:
                out[f] = v
        return out
    try:
        tex = section(16, lambda s: str(uuid.UUID(bytes=bytes(s))))
        col = section(4, lambda s: 255 - s[3])      # couleur stockée inversée : alpha = 255 - octet
        return tex, col
    except Exception:
        return None


def part_invisible(tex_entry):
    # vrai si CHAQUE face (0..31) est entièrement transparente ou porte une texture invisible standard
    if not tex_entry:
        return False
    tex, col = tex_entry
    for f in range(32):
        t = tex.get(f, tex[None])
        a = col.get(f, col[None])
        if not (a == 0 or t.lower() in INVISIBLE_TEX):
            return False
    return True


def tex_summary(tex_entry):
    if not tex_entry:
        return _tr("py.oar2glb.sans_textureentry")
    tex, col = tex_entry
    n = len({f for f in list(tex) + list(col) if f is not None})
    return _tr("py.oar2glb.texture_0_alpha_1_2f", tex[None][:8], col[None] / 255) + (_tr("py.oar2glb.0_face_s_a_part", n) if n else "")


def _txt(el, path):
    e = el.find(path)
    return (e.text or "").strip() if e is not None and e.text else ""


def _vec(el, path, keys="XYZ"):
    e = el.find(path)
    if e is None:
        return None
    try:
        return [float(_txt(e, k)) for k in keys]
    except ValueError:
        return None


def parse_object(xml_bytes):
    # un fichier objects/*.xml -> liste de parties (la première est la racine)
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_bytes.lstrip(b"\xef\xbb\xbf"))
    els = list(root.iter("SceneObjectPart"))
    parts = []
    for el in els:
        sh = el.find("Shape")
        mesh = None
        if sh is not None and (int(float(_txt(sh, "SculptType") or 0)) & 7) == 5:
            mesh = (_txt(sh, "SculptTexture/Guid") or _txt(sh, "SculptTexture/UUID") or _txt(sh, "SculptTexture")).lower() or None
        te = _txt(sh, "TextureEntry") if sh is not None else ""
        tex_e = parse_texture_entry(te) if te else None
        parts.append({
            "uuid": (_txt(el, "UUID/Guid") or _txt(el, "UUID/UUID") or _txt(el, "UUID")).lower(),
            "name": _txt(el, "Name"),
            "gpos": _vec(el, "GroupPosition"), "off": _vec(el, "OffsetPosition"),
            "rot": _vec(el, "RotationOffset", "XYZW"), "scale": _vec(el, "Scale"),
            "mesh": mesh, "invisible": part_invisible(tex_e), "tex": tex_summary(tex_e),
        })
    return parts


def oar_scan(oar, terrain_seul=False):
    # terrain_seul : ne lit que archive.xml, settings/ et terrains/ (ni objets ni meshes)
    size, groups, skins, terrain, water = (256.0, 256.0), [], {}, None, None
    with tarfile.open(oar, "r:*") as t:
        for m in t:
            if not m.isfile():
                continue
            if m.name == "archive.xml":
                x = t.extractfile(m).read().decode("utf-8", "replace")
                ms = re.search(r"<size_in_meters>\s*([\d.]+)\s*,\s*([\d.]+)", x)
                if ms:
                    size = (float(ms.group(1)), float(ms.group(2)))
            elif m.name.startswith("settings/") and m.name.endswith(".xml") and water is None:
                mw = re.search(r"<WaterHeight>\s*([-+0-9.eE]+)\s*</WaterHeight>", t.extractfile(m).read().decode("utf-8", "replace"))
                if mw:
                    try:
                        water = (float(mw.group(1)), m.name)
                    except ValueError:
                        pass
            elif terrain_seul and not m.name.startswith("terrains/"):
                continue
            elif m.name.startswith("objects/") and m.name.endswith(".xml"):
                try:
                    parts = parse_object(t.extractfile(m).read())
                except Exception as e:
                    print(_tr("py.oar2glb.oar_0_illisible_1", m.name, e))
                    continue
                if parts and parts[0]["gpos"]:
                    groups.append({"file": m.name, "parts": parts})
            elif m.name.startswith("assets/") and m.name.endswith("_mesh.llmesh"):
                raw = t.extractfile(m).read()
                skin, err = llmesh_skin(raw)
                if skin is not None or err:
                    skins[m.name[7:43].lower()] = {"skin": skin, "err": err, "bsm": bind_shape(skin),
                                                   "dom": llmesh_domains(raw) if skin is not None else [],
                                                   "raw": raw if skin is not None else None}
            elif m.name.startswith("terrains/") and m.name.endswith(".r32") and terrain is None:
                raw = t.extractfile(m).read()
                n = int(math.isqrt(len(raw) // 4))
                if n * n * 4 == len(raw):
                    terrain = (n, struct.unpack(f"<{n * n}f", raw))
    # position monde des parties (la racine : GroupPosition ; les autres : racine + décalage tourné)
    for g in groups:
        r = g["parts"][0]
        for i, p in enumerate(g["parts"]):
            gp = p["gpos"] or r["gpos"]
            if i == 0 or not p["off"]:
                p["wpos"] = list(gp)
            else:
                q = r["rot"] or [0, 0, 0, 1]
                o = p["off"]
                tq = [2 * (q[1] * o[2] - q[2] * o[1]), 2 * (q[2] * o[0] - q[0] * o[2]), 2 * (q[0] * o[1] - q[1] * o[0])]
                rv = [o[0] + q[3] * tq[0] + (q[1] * tq[2] - q[2] * tq[1]),
                      o[1] + q[3] * tq[1] + (q[2] * tq[0] - q[0] * tq[2]),
                      o[2] + q[3] * tq[2] + (q[0] * tq[1] - q[1] * tq[0])]
                p["wpos"] = [gp[k] + rv[k] for k in range(3)]
            p["gpos"] = gp
    return {"size": size, "groups": groups, "skins": skins, "terrain": terrain, "water": water}


def oar_info(scan):
    # objets racines au format utilisé par fix_positions : pos, rot, nom
    objs = [{"pos": g["parts"][0]["gpos"], "rot": g["parts"][0]["rot"], "name": g["parts"][0]["name"]}
            for g in scan["groups"]]
    size = scan["size"]
    print(_tr("py.oar2glb.oar_region_0_g_x_1", size[0], size[1]))
    if objs:
        pts = [o["pos"] for o in objs]
        lo = [round(min(p[k] for p in pts), 1) for k in range(3)]
        hi = [round(max(p[k] for p in pts), 1) for k in range(3)]
        print(_tr("py.oar2glb.oar_0_objets_de_1_a", len(objs), lo, hi))
    return size, objs


def terrain_height(terrain, x, y):
    # hauteur du sol (interpolation bilinéaire, 1 échantillon par mètre) ; None sans terrain
    if not terrain:
        return None
    n, h = terrain
    x = min(max(x, 0.0), n - 1.001)
    y = min(max(y, 0.0), n - 1.001)
    i, j = int(x), int(y)
    fx, fy = x - i, y - j
    a, b = h[j * n + i], h[j * n + i + 1]
    c, d = h[(j + 1) * n + i], h[(j + 1) * n + i + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


# ---------- var-region : convoar ramène tout dans 256 m, on remet les vraies positions ----------
def fix_positions(g, objs):
    # glTF = (X, Z, -Y) OpenSim ; la hauteur n'est jamais tronquée, X/Y le sont aux bords 0..256
    def ok(n, o):
        if 0.0 <= o <= 256.0:
            return abs(n - o) < 0.05
        return n > 254.0 if o > 256.0 else n < 2.0
    def qdot(a, b):
        return abs(sum(x * y for x, y in zip(a, b)))
    roots = [i for sc in g.get("scenes", []) for i in sc.get("nodes", [])]
    cand = {}
    for i in roots:
        n = g["nodes"][i]
        tx, ty, tz = node_pos(n)
        cs = [j for j, o in enumerate(objs)
              if abs(ty - o["pos"][2]) < 0.05 and ok(tx, o["pos"][0]) and ok(-tz, o["pos"][1])]
        nm = n.get("name", "")
        same = [j for j in cs if objs[j]["name"] and objs[j]["name"] == nm]
        if same:
            cs = same
        q = n.get("rotation")
        if q and len(cs) > 1:
            cs.sort(key=lambda j: -qdot(q, [objs[j]["rot"][0], objs[j]["rot"][2], -objs[j]["rot"][1], objs[j]["rot"][3]])
                    if objs[j]["rot"] else 0)
        cand[i] = cs
    used, moved, lost = set(), 0, 0
    for i in sorted(roots, key=lambda i: len(cand[i])):
        j = next((j for j in cand[i] if j not in used), None)
        if j is None:
            lost += 1
            continue
        used.add(j)
        x, y, z = objs[j]["pos"]
        new = [x, z, -y]
        n = g["nodes"][i]
        old = node_pos(n)
        if any(abs(a - b) > 0.01 for a, b in zip(old, new)):
            if "matrix" in n:
                n["matrix"][12:15] = new
            else:
                n["translation"] = new
            moved += 1
    print(_tr("py.oar2glb.var_region_0_objet_s_replace", moved, len(used), lost))


# ---------- 2. lanceur culture invariante ----------
def pe_platform(exe):
    d = Path(exe).read_bytes()
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    machine, nsec = struct.unpack_from("<HH", d, pe + 4)
    optsz = struct.unpack_from("<H", d, pe + 20)[0]
    opt = pe + 24
    magic = struct.unpack_from("<H", d, opt)[0]
    rva, size = struct.unpack_from("<II", d, opt + (96 if magic == 0x10B else 112) + 14 * 8)
    if machine == 0x8664:
        return "x64"
    if not rva:
        return "x86"
    sec = opt + optsz
    for i in range(nsec):
        vsz, va, rsz, raw = struct.unpack_from("<IIII", d, sec + i * 40 + 8)
        if va <= rva < va + max(vsz, rsz):
            flags = struct.unpack_from("<I", d, rva - va + raw + 16)[0]
            return "x86" if flags & 0x20002 else "anycpu"
    return "anycpu"


def ensure_config(convoar, launcher):
    # config du lanceur = config de convoar + loadFromRemoteSources (dist issu d'un ZIP téléchargé = "zone internet")
    src = convoar.with_name("convoar.exe.config")
    txt = src.read_text(encoding="utf-8-sig") if src.exists() else "<?xml version=\"1.0\"?>\n<configuration>\n</configuration>\n"
    tag = '<loadFromRemoteSources enabled="true"/>'
    if "loadFromRemoteSources" not in txt:
        if re.search(r"<runtime\s*>", txt):
            txt = re.sub(r"<runtime\s*>", "<runtime>\n    " + tag, txt, count=1)
        else:
            txt = txt.replace("</configuration>", "  <runtime>\n    " + tag + "\n  </runtime>\n</configuration>")
    dst = launcher.with_name("convoar_inv.exe.config")
    if not dst.exists() or dst.read_text(encoding="utf-8-sig") != txt:
        dst.write_text(txt, encoding="utf-8")
        print(_tr("py.oar2glb.lanceur_0_mis_a_jour_loadfromremotesources", dst.name))


def ensure_launcher(convoar):
    convoar = Path(convoar)
    launcher = convoar.with_name("convoar_inv.exe")
    if launcher.exists():
        ensure_config(convoar, launcher)
        return launcher
    win = os.environ.get("WINDIR", r"C:\Windows")
    csc = next((p for p in (Path(win, r"Microsoft.NET\Framework64\v4.0.30319\csc.exe"),
                            Path(win, r"Microsoft.NET\Framework\v4.0.30319\csc.exe")) if p.exists()), None)
    if not csc:
        sys.exit(_tr("py.oar2glb.erreur_csc_exe_net_framework_4"))
    plat = pe_platform(convoar)
    src = convoar.with_name("convoar_inv.cs")
    src.write_text(LAUNCHER_CS, encoding="utf-8")
    r = subprocess.run([str(csc), "/nologo", "/target:exe", f"/platform:{plat}", f"/out:{launcher}", str(src)],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(_tr("py.oar2glb.erreur_compilation_du_lanceur_0_1", r.stdout, r.stderr))
    ensure_config(convoar, launcher)
    print(_tr("py.oar2glb.lanceur_0_compile_1", launcher, plat))
    return launcher


def run_convoar(convoar, oar, outdir):
    exe = ensure_launcher(convoar) if os.name == "nt" else Path(convoar)
    args = [str(exe), "--outputdir", outdir.name, oar.name]   # options AVANT le fichier
    print(_tr("py.oar2glb.convoar"), " ".join(f'"{a}"' if " " in a else a for a in args))
    enc = "oem" if os.name == "nt" else "utf-8"
    p = subprocess.Popen(args, cwd=oar.parent, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding=enc, errors="replace")
    for line in p.stdout:
        print(line.rstrip())
    p.wait()
    print(_tr("py.oar2glb.convoar_code_retour_0", p.returncode))


# ---------- 3. lecture + contrôle ----------
MAX_RETRY = 2


def missing_images(outdir):
    gl = sorted(Path(outdir).glob("*.gltf"), key=lambda q: q.stat().st_mtime)
    if not gl:
        return []
    from urllib.parse import unquote
    g = load_gltf(gl[-1])
    return sorted({unquote(i["uri"]) for i in g.get("images", []) if "uri" in i and not i["uri"].startswith("data:")
                   and find_file(Path(outdir), unquote(i["uri"])) is None})


def load_gltf(path):
    txt = path.read_text(encoding="utf-8", errors="replace")
    txt = re.sub(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'\\\\', txt)
    try:
        return json.loads(txt)
    except json.JSONDecodeError as e:
        line = txt.splitlines()[e.lineno - 1] if e.lineno <= len(txt.splitlines()) else ""
        sys.exit(_tr("py.oar2glb.erreur_gltf_invalide_0_ligne_1", e, e.lineno, line.strip()[:120]))


def check(g):
    tl = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}
    errs = []
    for i, n in enumerate(g.get("nodes", [])):
        for k, l in (("translation", 3), ("rotation", 4), ("scale", 3), ("matrix", 16)):
            if k in n and len(n[k]) != l:
                errs.append(f"node {i} {k} = {n[k]}")
    for i, a in enumerate(g.get("accessors", [])):
        for k in ("min", "max"):
            if k in a and len(a[k]) != tl.get(a["type"], len(a[k])):
                errs.append(f"accessor {i} {k} = {a[k]}")
    if errs:
        sys.exit(_tr("py.oar2glb.erreur_0_vecteurs_de_mauvaise_taille", len(errs))
                 + "\n  ".join(errs[:5]))


def node_pos(n):
    if "translation" in n:
        return n["translation"]
    if "matrix" in n:
        return n["matrix"][12:15]
    return [0, 0, 0]


# ---------- matrices glTF (colonnes d'abord : indice = colonne * 4 + ligne) ----------
def quat_mat(q, s=(1, 1, 1), t=(0, 0, 0)):
    x, y, z, w = q
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    m = [0.0] * 16
    for c in range(3):
        for k in range(3):
            m[c * 4 + k] = r[k][c] * s[c]
    m[12:15] = t
    m[15] = 1.0
    return m


def node_local(n):
    if "matrix" in n:
        return list(n["matrix"])
    return quat_mat(n.get("rotation", [0, 0, 0, 1]), n.get("scale", [1, 1, 1]), n.get("translation", [0, 0, 0]))


def mat_mul(a, b):
    return [sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4)) for c in range(4) for r in range(4)]


def mat_inv(m):
    a = [[m[c * 4 + r] for c in range(4)] + [1.0 if r == i else 0.0 for i in range(4)] for r in range(4)]
    for i in range(4):
        piv = max(range(i, 4), key=lambda r: abs(a[r][i]))
        if abs(a[piv][i]) < 1e-12:
            return None
        a[i], a[piv] = a[piv], a[i]
        d = a[i][i]
        a[i] = [v / d for v in a[i]]
        for r in range(4):
            if r != i:
                f = a[r][i]
                a[r] = [v - f * w for v, w in zip(a[r], a[i])]
    return [a[r][4 + c] for c in range(4) for r in range(4)]


def mat_trs(m):
    # matrice -> (translation, rotation quaternion, échelle), sans cisaillement
    s = [math.sqrt(sum(m[c * 4 + r] ** 2 for r in range(3))) or 1.0 for c in range(3)]
    r = [[m[c * 4 + k] / s[c] for c in range(3)] for k in range(3)]
    tr = r[0][0] + r[1][1] + r[2][2]
    if tr > 0:
        k = math.sqrt(tr + 1) * 2
        q = [(r[2][1] - r[1][2]) / k, (r[0][2] - r[2][0]) / k, (r[1][0] - r[0][1]) / k, k / 4]
    elif r[0][0] > r[1][1] and r[0][0] > r[2][2]:
        k = math.sqrt(1 + r[0][0] - r[1][1] - r[2][2]) * 2
        q = [k / 4, (r[0][1] + r[1][0]) / k, (r[0][2] + r[2][0]) / k, (r[2][1] - r[1][2]) / k]
    elif r[1][1] > r[2][2]:
        k = math.sqrt(1 + r[1][1] - r[0][0] - r[2][2]) * 2
        q = [(r[0][1] + r[1][0]) / k, k / 4, (r[1][2] + r[2][1]) / k, (r[0][2] - r[2][0]) / k]
    else:
        k = math.sqrt(1 + r[2][2] - r[0][0] - r[1][1]) * 2
        q = [(r[0][2] + r[2][0]) / k, (r[1][2] + r[2][1]) / k, k / 4, (r[1][0] - r[0][1]) / k]
    return list(m[12:15]), q, s


def rot_vec(q, v):
    m = quat_mat(q)
    return [sum(m[c * 4 + r] * v[c] for c in range(3)) for r in range(3)]


class Tree:
    # parents et matrices monde des nœuds d'un glTF
    def __init__(self, g):
        self.g, self.parent, self._w = g, {}, {}
        for i, n in enumerate(g.get("nodes", [])):
            for c in n.get("children", []):
                self.parent[c] = i

    def world(self, i):
        if i not in self._w:
            m = node_local(self.g["nodes"][i])
            self._w[i] = mat_mul(self.world(self.parent[i]), m) if i in self.parent else m
        return self._w[i]

    def pos_os(self, i):
        w = self.world(i)
        return [w[12], -w[14], w[13]]       # glTF (X, Y, Z) -> OpenSim (x, y, z) = (X, -Z, Y)


# ---------- correspondance nœud GLB <-> objets de l'OAR ----------
def node_uuids(g):
    # UUID lisibles dans chaque nœud : nom, extras, nom/extras du mesh, matériaux, images
    out = {}
    for i, n in enumerate(g.get("nodes", [])):
        s = [n.get("name", ""), json.dumps(n.get("extras", ""))]
        if "mesh" in n:
            me = g["meshes"][n["mesh"]]
            s += [me.get("name", ""), json.dumps(me.get("extras", ""))]
            for pr in me.get("primitives", []):
                if "material" in pr:
                    s.append(json.dumps(g["materials"][pr["material"]]))
        for u in UUID_RX.findall(" ".join(map(str, s))):
            out.setdefault(u.lower(), []).append(i)
    return out


def match_nodes(g, scan):
    # {uuid de la partie: (nœud, méthode)} ; méthodes : « UUID du prim », « UUID du mesh », « nom + position »
    tree, uu = Tree(g), node_uuids(g)
    names = {}
    for i, n in enumerate(g.get("nodes", [])):
        if n.get("name"):
            names.setdefault(n["name"], []).append(i)
    res, used = {}, set()
    for grp in scan["groups"]:
        for p in grp["parts"]:
            cand, how = [], None
            if p["uuid"] in uu:
                cand, how = uu[p["uuid"]], _tr("py.oar2glb.uuid_du_prim")
            elif p["mesh"] and p["mesh"] in uu:
                cand, how = uu[p["mesh"]], _tr("py.oar2glb.uuid_du_mesh")
            elif p["name"] in names:
                cand, how = names[p["name"]], "nom + position"
            if not cand:
                continue
            if how == "UUID du prim" and len(cand) == 1:
                res[p["uuid"]] = (cand[0], how)
                used.add(cand[0])
                continue
            def dist(i):
                q = tree.pos_os(i)
                return min(math.dist(q, p["wpos"]), math.dist(q, grp["parts"][0]["gpos"]))
            free = [i for i in cand if i not in used] or cand
            best = min(free, key=lambda i: (round(dist(i), 2), i))      # à égalité : ordre des nœuds = ordre de l'OAR
            if dist(best) <= 2.0:
                res[p["uuid"]] = (best, how)
                used.add(best)
    return res


# ---------- matériaux invisibles ----------
def material_invisible(g, mi, cache):
    if mi not in cache:
        m = g["materials"][mi]
        a = (m.get("pbrMetallicRoughness") or {}).get("baseColorFactor")
        inv = bool(a and len(a) == 4 and a[3] <= 0.004)
        if not inv:
            s = [json.dumps(m)]
            ti = ((m.get("pbrMetallicRoughness") or {}).get("baseColorTexture") or {}).get("index")
            if ti is not None and ti < len(g.get("textures", [])):
                src = g["textures"][ti].get("source")
                if src is not None and src < len(g.get("images", [])):
                    s.append(json.dumps({k: v for k, v in g["images"][src].items() if k != "uri" or not str(v).startswith("data:")}))
            inv = any(u in " ".join(s).lower() for u in INVISIBLE_TEX)
        cache[mi] = inv
    return cache[mi]


def node_all_invisible(g, n, cache):
    if "mesh" not in n:
        return False
    prims = g["meshes"][n["mesh"]].get("primitives", [])
    return bool(prims) and all("material" in p and material_invisible(g, p["material"], cache) for p in prims)


def remove_node(g, i):
    n = g["nodes"][i]
    if n.get("children"):
        n.pop("mesh", None)         # les enfants restent
        return
    for sc in g.get("scenes", []):
        sc["nodes"] = [k for k in sc.get("nodes", []) if k != i]
    for o in g["nodes"]:
        if i in o.get("children", []):
            o["children"] = [k for k in o["children"] if k != i]
    n.pop("mesh", None)


def rig_box_roots(scan):
    # boîtes racines d'animesh : prim simple (pas un mesh) racine d'un objet dont TOUTES les autres parties sont des meshes
    # riggés. Invisible en jeu (cadre de l'animal), mais pas forcément alpha 0 dans l'OAR : convoar la sort en boîte laiteuse.
    out = set()
    for grp in scan["groups"]:
        ps = grp["parts"]
        sk = lambda q: bool(q["mesh"] and (scan["skins"].get(q["mesh"]) or {}).get("bsm"))
        if len(ps) > 1 and ps[0]["mesh"] is None and all(sk(q) for q in ps[1:]):
            out.add(ps[0]["uuid"])
    return out


def remove_invisible(g, scan, match):
    # prims entièrement transparents : par l'OAR (faces alpha 0 / texture invisible), par les matériaux du GLB,
    # et boîtes racines d'animesh. convoar sort un nœud par partie : on retire le nœud de la partie.
    cache, victims = {}, {}
    boxes = rig_box_roots(scan)
    for grp in scan["groups"]:
        for p in grp["parts"]:
            if p["uuid"] in match and (p["invisible"] or p["uuid"] in boxes):
                victims.setdefault(match[p["uuid"]][0], _tr("py.oar2glb.boite_racine_d_animesh") if p["uuid"] in boxes and not p["invisible"] else "transparent (OAR)")
    for i, n in enumerate(g.get("nodes", [])):
        if i not in victims and node_all_invisible(g, n, cache):
            victims[i] = _tr("py.oar2glb.materiaux_transparents_glb")
    for i in sorted(victims):
        print(_tr("py.oar2glb.invisible_node_0_1_retire_2", i, g['nodes'][i].get('name', '?'), victims[i]))
        remove_node(g, i)
    return len(victims)


# ---------- meshes riggés ----------
class ExtraBuffer:
    # données ajoutées en mémoire (accesseurs recalculés), placées dans un buffer final en data: URI
    def __init__(self, g):
        self.g, self.data, self.idx = g, bytearray(), len(g.get("buffers", []))

    def add_vec3(self, pts):
        g = self.g
        g.setdefault("bufferViews", []).append({"buffer": self.idx, "byteOffset": len(self.data), "byteLength": len(pts) * 12, "target": 34962})
        for p in pts:
            self.data += struct.pack("<3f", *p)
        acc = {"bufferView": len(g["bufferViews"]) - 1, "componentType": 5126, "count": len(pts), "type": "VEC3"}
        if pts:
            acc["min"] = [min(p[k] for p in pts) for k in range(3)]
            acc["max"] = [max(p[k] for p in pts) for k in range(3)]
        g.setdefault("accessors", []).append(acc)
        return len(g["accessors"]) - 1

    def add_vec2(self, pts):
        g = self.g
        g.setdefault("bufferViews", []).append({"buffer": self.idx, "byteOffset": len(self.data), "byteLength": len(pts) * 8, "target": 34962})
        for p in pts:
            self.data += struct.pack("<2f", *p)
        g.setdefault("accessors", []).append({"bufferView": len(g["bufferViews"]) - 1, "componentType": 5126, "count": len(pts), "type": "VEC2"})
        return len(g["accessors"]) - 1

    def add_indices(self, idx):
        g = self.g
        big = bool(idx) and max(idx) > 65535
        fmt, size, ct = ("I", 4, 5125) if big else ("H", 2, 5123)
        g.setdefault("bufferViews", []).append({"buffer": self.idx, "byteOffset": len(self.data), "byteLength": len(idx) * size, "target": 34963})
        self.data += struct.pack(f"<{len(idx)}{fmt}", *idx)
        self.data += b"\x00" * ((4 - len(self.data) % 4) % 4)
        g.setdefault("accessors", []).append({"bufferView": len(g["bufferViews"]) - 1, "componentType": ct, "count": len(idx), "type": "SCALAR"})
        return len(g["accessors"]) - 1

    def finish(self):
        if self.data:
            self.g.setdefault("buffers", []).append({"byteLength": len(self.data),
                                                     "uri": "data:application/octet-stream;base64," + base64.b64encode(bytes(self.data)).decode()})


def read_vec3(g, base, cache, ai):
    a = g["accessors"][ai]
    if a.get("componentType") != 5126 or a.get("type") != "VEC3" or "sparse" in a or "bufferView" not in a:
        raise ValueError(_tr("py.oar2glb.accesseur_0_non_gere_float_vec3", ai))
    bv = g["bufferViews"][a["bufferView"]]
    bi = bv.get("buffer", 0)
    if bi not in cache:
        cache[bi] = read_uri(g["buffers"][bi]["uri"], base)
    data, stride = cache[bi], bv.get("byteStride") or 12
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    return [struct.unpack_from("<3f", data, off + k * stride) for k in range(a["count"])]


def inv3(a):
    c = [[a[1][1] * a[2][2] - a[1][2] * a[2][1], a[0][2] * a[2][1] - a[0][1] * a[2][2], a[0][1] * a[1][2] - a[0][2] * a[1][1]],
         [a[1][2] * a[2][0] - a[1][0] * a[2][2], a[0][0] * a[2][2] - a[0][2] * a[2][0], a[0][2] * a[1][0] - a[0][0] * a[1][2]],
         [a[1][0] * a[2][1] - a[1][1] * a[2][0], a[0][1] * a[2][0] - a[0][0] * a[2][1], a[0][0] * a[1][1] - a[0][1] * a[1][0]]]
    det = a[0][0] * c[0][0] + a[0][1] * c[1][0] + a[0][2] * c[2][0]
    return None if abs(det) < 1e-12 else [[v / det for v in row] for row in c]


def rigged_scale_mode(node, scale):
    # comment convoar a appliqué l'échelle du prim : « nœud » (scale du nœud GLB), « cuite » (dans les sommets) ou « aucune »
    exp = (scale[0], scale[2], scale[1])        # axes glTF
    s = node.get("scale")
    if "matrix" in node:
        s = mat_trs(node["matrix"])[2]
    if s and any(abs(v - 1) > 1e-4 for v in s):
        return _tr("py.oar2glb.nud")
    return "cuite" if any(abs(v - 1) > 1e-4 for v in exp) else _tr("py.oar2glb.aucune")


def union_domain(dom):
    # (min, max) englobant les domaines de position des sous-maillages, ou None
    if not dom:
        return None
    lo = [min(d[0][k] for d in dom) for k in range(3)]
    hi = [max(d[1][k] for d in dom) for k in range(3)]
    return lo, hi


def read_acc(g, base, cache, ai, n):
    a = g["accessors"][ai]
    if a.get("componentType") != 5126 or a.get("type") != f"VEC{n}" or "sparse" in a or "bufferView" not in a:
        raise ValueError(_tr("py.oar2glb.accesseur_0_non_gere", ai))
    bv = g["bufferViews"][a["bufferView"]]
    bi = bv.get("buffer", 0)
    if bi not in cache:
        cache[bi] = read_uri(g["buffers"][bi]["uri"], base)
    stride = bv.get("byteStride") or 4 * n
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    return [struct.unpack_from(f"<{n}f", cache[bi], off + k * stride) for k in range(a["count"])]


def rig_mesh(g, base, cache, part, bsm, ni, raw):
    # Un mesh riggé est reconstruit depuis son .llmesh dans l'OAR (positions, normales, UV, triangles, domaine de position) :
    # la géométrie que convoar écrit pour ces meshes est inutilisable (mêmes étendues et mêmes nombres de sommets pour des
    # animaux différents, échelle cuite inconnue de l'OAR). L'échelle du prim est ignorée ; bind_shape_matrix s'applique.
    # Les matériaux viennent du nœud GLB (face i du mesh = primitive i). -> (mesh, points, "asset") ou message d'erreur
    node = g["nodes"][ni]
    if "mesh" not in node:
        return _tr("py.oar2glb.le_nud_n_a_pas_de")
    geo = llmesh_geometry(raw) if raw else None
    if not geo or not any(geo):
        return _tr("py.oar2glb.geometrie_du_llmesh_illisible")
    lin = [[bsm[0], bsm[4], bsm[8]], [bsm[1], bsm[5], bsm[9]], [bsm[2], bsm[6], bsm[10]]]
    t = bsm[12:15]
    li = inv3(lin)
    if li is None:
        return _tr("py.oar2glb.bind_shape_matrix_non_inversible")
    old = g["meshes"][node["mesh"]]
    oprims = old.get("primitives", [])
    prims, allp, nv = [], [], 0
    for i, sm in enumerate(geo):
        if not sm:
            continue
        pts = []
        for x, y, z in sm["pos"]:
            pts.append([lin[0][0] * x + lin[0][1] * y + lin[0][2] * z + t[0],
                        lin[2][0] * x + lin[2][1] * y + lin[2][2] * z + t[2],
                        -(lin[1][0] * x + lin[1][1] * y + lin[1][2] * z + t[1])])
        pr = {"attributes": {}, "_pts": pts, "_idx": [k for k in sm["tri"] if k < len(pts)]}
        if sm["nor"]:
            ns = []
            for v in sm["nor"]:
                nx, ny, nz = (sum(li[j][k] * v[j] for j in range(3)) for k in range(3))
                ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
                ns.append([nx / ln, nz / ln, -ny / ln])
            pr["_nrm"] = ns
        if sm["uv"]:
            flip = True                      # UV de Second Life : v vers le haut ; glTF : v vers le bas
            if i < len(oprims) and "TEXCOORD_0" in oprims[i].get("attributes", {}):
                try:
                    cu = read_acc(g, base, cache, oprims[i]["attributes"]["TEXCOORD_0"], 2)
                    if len(cu) == len(sm["uv"]):
                        m = min(len(cu), 16)
                        e_raw = sum(abs(cu[k][1] - sm["uv"][k][1]) for k in range(m))
                        e_flip = sum(abs(cu[k][1] - (1 - sm["uv"][k][1])) for k in range(m))
                        flip = e_flip <= e_raw
                except Exception:
                    pass
            pr["_uv"] = [(u, 1.0 - v if flip else v) for u, v in sm["uv"]]
        mat = oprims[i] if i < len(oprims) else (oprims[-1] if oprims else None)
        if mat is not None and "material" in mat:
            pr["material"] = mat["material"]
        prims.append(pr)
        allp += pts
        nv += len(pts)
    if not allp:
        return _tr("py.oar2glb.aucune_geometrie")
    mesh = {k: v for k, v in old.items() if k != "primitives"}
    mesh["primitives"] = prims
    oldn = sum(g["accessors"][pr["attributes"]["POSITION"]]["count"] for pr in oprims if "POSITION" in pr.get("attributes", {}))
    print(_tr("py.oar2glb.rigge_0_reconstruit_depuis_l_oar", part['name'], len(prims), nv, sum(len(p['_idx']) for p in prims) // 3, len(oprims), oldn, fmt3(part['scale'] or [1, 1, 1]), fmt3([math.sqrt(sum(bsm[c * 4 + r] ** 2 for r in range(3))) for c in range(3)])))
    return mesh, allp, "asset"


PLACED = []
PLACED_NODES = set()


def node_aabb(g, tree, i):
    # boîte englobante monde (glTF) d'un nœud d'après les min/max de ses accesseurs POSITION, sans lire les sommets
    n = g["nodes"][i]
    if "mesh" not in n:
        return None
    lo, hi = [1e30] * 3, [-1e30] * 3
    for pr in g["meshes"][n["mesh"]].get("primitives", []):
        a = g["accessors"][pr["attributes"]["POSITION"]] if "POSITION" in pr.get("attributes", {}) else None
        if not a or "min" not in a or "max" not in a:
            continue
        lo = [min(lo[k], a["min"][k]) for k in range(3)]
        hi = [max(hi[k], a["max"][k]) for k in range(3)]
    if lo[0] > hi[0]:
        return None
    w = tree.world(i)
    pts = [[w[r] * x + w[4 + r] * y + w[8 + r] * z + w[12 + r] for r in range(3)] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    return [min(p[k] for p in pts) for k in range(3)], [max(p[k] for p in pts) for k in range(3)]


def report_buried(g):
    # pour chaque animal posé : objets du GLB dont la boîte englobante contient le centre de l'animal (animal enfoui ?)
    tree = Tree(g)
    boxes = {}
    for i, n in enumerate(g["nodes"]):
        if n.get("name", "").startswith("REPERE") or i in PLACED_NODES:
            continue
        b = node_aabb(g, tree, i)
        if b:
            boxes[i] = b
    for name, gx, gy, ground, ext in PLACED:
        c = [gx, ground + ext[2] / 2, -gy]
        inside = sorted(((math.prod(b[1][k] - b[0][k] for k in range(3)), i) for i, b in boxes.items()
                         if all(b[0][k] <= c[k] <= b[1][k] for k in range(3))))
        txt = ", ".join(f"'{g['nodes'][i].get('name', '?')[:30]}' (sommet {boxes[i][1][1]:.1f} m)" for _, i in inside[:3])
        print(_tr("py.oar2glb.controle_0_pieds_a_1_2f", name, ground, c[1]) + (_tr("py.oar2glb.dans_la_boite_de_0_objet", len(inside), txt) if inside else _tr("py.oar2glb.libre_aucune_boite_d_objet_ne")))


def add_beacons(g, ebuf):
    # option --markers : un mât rouge de 15 m à chaque animal posé, pour le retrouver dans le viewer
    g.setdefault("materials", []).append({"name": "repere", "pbrMetallicRoughness": {"baseColorFactor": [1, 0, 0, 1], "metallicFactor": 0},
                                          "emissiveFactor": [1, 0, 0], "doubleSided": True})
    mat = len(g["materials"]) - 1
    h, w = 15.0, 0.15
    pts = [(x, y, z) for x in (-w, w) for y in (0, h) for z in (-w, w)]
    idx = [0, 1, 3, 0, 3, 2, 4, 6, 7, 4, 7, 5, 0, 4, 5, 0, 5, 1, 2, 3, 7, 2, 7, 6, 0, 2, 6, 0, 6, 4, 1, 5, 7, 1, 7, 3]
    pa = ebuf.add_vec3(pts)
    g["bufferViews"].append({"buffer": ebuf.idx, "byteOffset": len(ebuf.data), "byteLength": len(idx) * 2, "target": 34963})
    ebuf.data += struct.pack(f"<{len(idx)}H", *idx)
    ebuf.data += b"\x00\x00" * (len(idx) % 2)
    g["accessors"].append({"bufferView": len(g["bufferViews"]) - 1, "componentType": 5123, "count": len(idx), "type": "SCALAR"})
    g["meshes"].append({"name": "repere", "primitives": [{"attributes": {"POSITION": pa}, "indices": len(g["accessors"]) - 1, "material": mat}]})
    mi = len(g["meshes"]) - 1
    for name, gx, gy, ground, ext in PLACED:
        g["nodes"].append({"name": f"REPERE {name} ({ext[0]:.1f} x {ext[2]:.1f} x {ext[1]:.1f} m)", "mesh": mi, "translation": [gx, ground, -gy]})
        g["scenes"][0]["nodes"].append(len(g["nodes"]) - 1)
    print(_tr("py.oar2glb.reperes_0_mat_s_rouge_s", len(PLACED)))


MAX_ANIMAL, MIN_ANIMAL = 12.0, 0.1       # garde-fou : un animal fait entre 10 cm et 12 m dans sa plus grande dimension


def place_rigged_group(g, base, cache, extra, tree, grp, items):
    # items : [(partie riggée, bind_shape, nœud GLB)] d'UN objet. Les morceaux d'un même animal (chacun avec sa
    # bind_shape_matrix) partagent le même repère : on les déplace ENSEMBLE (même décalage, même rotation), sans
    # jamais les poser séparément. Retourne le nombre de morceaux corrigés.
    built = []
    for part, bsm, ni, raw in items:
        r = rig_mesh(g, base, cache, part, bsm, ni, raw)
        if isinstance(r, str):
            print(_tr("py.oar2glb.rigge_0_1_non_corrige", part['name'], r))
        else:
            built.append((part, ni) + r)
    if not built:
        return 0
    allp = [p for b in built for p in b[3]]
    lo = [min(p[k] for p in allp) for k in range(3)]
    hi = [max(p[k] for p in allp) for k in range(3)]
    root = grp["parts"][0]
    ext = [hi[k] - lo[k] for k in range(3)]
    if max(ext) > MAX_ANIMAL or max(ext) < MIN_ANIMAL:
        print(_tr("py.oar2glb.rigge_0_taille_obtenue_1_2f", root['name'], ext[0], ext[2], ext[1], MIN_ANIMAL, MAX_ANIMAL))
        return 0
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2          # centré à l'horizontale sur la racine
    gx, gy, gz = root["gpos"]
    q = root["rot"] or [0, 0, 0, 1]
    pq = built[0][0]["rot"] if built[0][0] is not root and built[0][0]["rot"] else [0, 0, 0, 1]
    a, b = q, pq                                                 # rotation monde du 1er morceau = racine x enfant
    q = [a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1], a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0],
         a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3], a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2]]
    rot = [q[0], q[2], -q[1], q[3]]                              # repère glTF, appliquée à tous les morceaux
    corners = [rot_vec(rot, [x, y, z]) for x in (lo[0] - cx, hi[0] - cx) for y in (lo[1], hi[1]) for z in (lo[2] - cz, hi[2] - cz)]
    yoff = min(c[1] for c in corners)
    # sol : le dessous de la boîte racine (prim simple posé au sol) ; racine elle-même riggée : sa position
    if root["mesh"] is None and root["scale"]:
        ground, src = gz - root["scale"][2] / 2, _tr("py.oar2glb.dessous_de_la_boite_racine")
    else:
        ground, src = gz, _tr("py.oar2glb.altitude_de_la_racine")
    for part, ni, mesh, pts, mode in built:
        for pr in mesh["primitives"]:
            if "_pts" in pr:
                pr["attributes"]["POSITION"] = extra.add_vec3([[p[0] - cx, p[1], p[2] - cz] for p in pr.pop("_pts")])
            if "_nrm" in pr:
                pr["attributes"]["NORMAL"] = extra.add_vec3(pr.pop("_nrm"))
            if "_uv" in pr:
                pr["attributes"]["TEXCOORD_0"] = extra.add_vec2(pr.pop("_uv"))
            if "_idx" in pr:
                pr["indices"] = extra.add_indices(pr.pop("_idx"))
        g["meshes"].append(mesh)
        node = g["nodes"][ni]
        PLACED_NODES.add(ni)
        node["mesh"] = len(g["meshes"]) - 1
        w = quat_mat(rot, t=[gx, ground - yoff, -gy])
        if ni in tree.parent:
            inv = mat_inv(tree.world(tree.parent[ni]))
            if inv:
                w = mat_mul(inv, w)
        tr, qq, _ = mat_trs(w)
        node.pop("matrix", None)
        node.pop("scale", None)
        node["translation"], node["rotation"] = tr, qq
        tree._w.clear()
    ext = [hi[k] - lo[k] for k in range(3)]
    PLACED.append((root["name"], gx, gy, ground, ext))
    print(_tr("py.oar2glb.rigge_0_1_morceau_x_echelle", root['name'], len(built), built[0][4], ext[0], ext[2], ext[1], gx, gy, ground, src))
    return len(built)


def repair(g, base, scan, keep_invisible, reperes=False):
    match = match_nodes(g, scan)
    extra, cache, tree = ExtraBuffer(g), {}, Tree(g)
    n_rig = n_inv = 0
    for grp in scan["groups"]:
        items = []
        for p in grp["parts"]:
            sk = scan["skins"].get(p["mesh"]) if p["mesh"] else None
            if not sk or not sk["bsm"]:
                if sk and sk["err"]:
                    print(_tr("py.oar2glb.rigge_0_1_ignore", p['name'], sk['err']))
                continue
            if p["uuid"] not in match:
                print(_tr("py.oar2glb.rigge_0_1_nud_glb_introuvable", p['name'], p['uuid']))
                continue
            items.append((p, sk["bsm"], match[p["uuid"]][0], sk.get("raw")))
        if items:
            n_rig += place_rigged_group(g, base, cache, extra, tree, grp, items)
    if reperes and PLACED:
        add_beacons(g, extra)
    extra.finish()
    if not keep_invisible:
        n_inv = remove_invisible(g, scan, match)
    if PLACED:
        report_buried(g)
    print(_tr("py.oar2glb.correctif_0_mesh_es_rigge_s", n_rig, n_inv))
    return n_rig, n_inv


# ---------- --diag ----------
def read_glb_json(path):
    path = Path(path)
    if path.suffix.lower() == ".gltf":
        return load_gltf(path)
    d = path.read_bytes()
    if d[:4] != b"glTF":
        sys.exit(_tr("py.oar2glb.erreur_0_n_est_pas_un", path))
    ln, kind = struct.unpack_from("<I4s", d, 12)
    return json.loads(d[20:20 + ln].decode("utf-8"))


def fmt3(v):
    return "(" + ", ".join(f"{x:.3g}" for x in v) + ")" if v else "?"


def diag(scan, g, glb_label, base=None):
    match = match_nodes(g, scan) if g else {}
    parts = [(grp, p) for grp in scan["groups"] for p in grp["parts"]]
    print(_tr("py.oar2glb.diag_0_objet_s_1_partie", len(scan['groups']), len(parts), 'oui' if scan['terrain'] else 'non', 'GLB ' + glb_label if g else _tr('py.oar2glb.pas_de_glb_correspondance_non_evaluee')))
    nr = ni = nm = 0
    boxes = rig_box_roots(scan)
    for k, (grp, p) in enumerate(parts, 1):
        sk = scan["skins"].get(p["mesh"]) if p["mesh"] else None
        if sk and sk["bsm"]:
            rig, nr = "oui", nr + 1
        elif sk:
            rig = "oui (" + (sk["err"] or _tr("py.oar2glb.sans_bind_shape_matrix")) + ")"
        else:
            rig = "non" if p["mesh"] else _tr("py.oar2glb.non_pas_un_mesh")
        bsm = sk["bsm"] if sk and sk["bsm"] else None
        bs = fmt3([math.sqrt(sum(bsm[c * 4 + r] ** 2 for r in range(3))) for c in range(3)]) if bsm else "-"
        ni += p["invisible"]
        if g:
            if p["uuid"] in match:
                n, how = match[p["uuid"]]
                nm += 1
                node = g["nodes"][n]
                sc = node.get("scale") or (mat_trs(node["matrix"])[2] if "matrix" in node else None)
                gl = _tr("py.oar2glb.nud_0_1_2_echelle_du", n, node.get('name', ''), how, fmt3(sc) if sc else 'aucune') + (_tr("py.oar2glb.echelle_du_prim_appliquee_0", rigged_scale_mode(node, p['scale'] or [1, 1, 1])) if bsm else "")
            else:
                gl = _tr("py.oar2glb.nud_introuvable")
        else:
            gl = "-"
        racine = "racine" if p is grp["parts"][0] else "enfant"
        print(_tr("py.oar2glb.0_5d_1_2_3_rigge", k, p['name'] or '(sans nom)', p['uuid'], racine, rig, fmt3(p['scale']), bs, 'oui' if p['invisible'] else 'non', 'oui' if p['uuid'] in boxes else 'non', gl))
        if bsm or p["uuid"] in boxes or p["invisible"]:
            gz = terrain_height(scan["terrain"], p["gpos"][0], p["gpos"][1])
            print(_tr("py.oar2glb.diag_pos", fmt3(p['gpos']), ('%.2f m' % gz) if gz is not None else _tr("py.oar2glb.unknown"), p['tex']) + (_tr("py.oar2glb.translation_bind_shape_0", fmt3(bsm[12:15])) if bsm else ""))
            if bsm:
                sk = scan["skins"][p["mesh"]]
                print(_tr("py.oar2glb.bind_shape_matrix_0", [round(v, 4) for v in bsm]))
                ud = union_domain(sk["dom"])
                print(_tr("py.oar2glb.domaine_de_position_du_mesh_0", len(sk['dom'])) + (f"{fmt3(ud[0])} .. {fmt3(ud[1])}" if ud else _tr("py.oar2glb.unreadable")))
                if g and base is not None and p["uuid"] in match and "mesh" in g["nodes"][match[p["uuid"]][0]]:
                    try:
                        pts, cc = [], {}
                        for pr in g["meshes"][g["nodes"][match[p["uuid"]][0]]["mesh"]].get("primitives", []):
                            pts += read_vec3(g, base, cc, pr["attributes"]["POSITION"])
                        lo_ = [min(q[k] for q in pts) for k in range(3)]
                        hi_ = [max(q[k] for q in pts) for k in range(3)]
                        pa = g["meshes"][g["nodes"][match[p["uuid"]][0]]["mesh"]]["primitives"][0]["attributes"]["POSITION"]
                        ac = g["accessors"][pa]
                        bv = g["bufferViews"][ac["bufferView"]]
                        bf = g["buffers"][bv.get("buffer", 0)]
                        print(_tr("py.oar2glb.accesseur_position_0_bufferview_1_buffer", ac, bv, str(bf.get('uri'))[:60], bf.get('byteLength'), pts[:3]))
                        print(_tr("py.oar2glb.sommets_du_glb_axes_opensim_x", fmt3([lo_[0], -hi_[2], lo_[1]]), fmt3([hi_[0], -lo_[2], hi_[1]]), fmt3([hi_[0] - lo_[0], hi_[2] - lo_[2], hi_[1] - lo_[1]]), len(pts)))
                    except Exception as e:
                        print(_tr("py.oar2glb.sommets_du_glb_illisibles_0", e))
            if g and p["uuid"] in match:
                node = g["nodes"][match[p["uuid"]][0]]
                if "mesh" in node:
                    for pr in g["meshes"][node["mesh"]].get("primitives", [])[:3]:
                        m = g["materials"][pr["material"]] if "material" in pr else {}
                        ti = ((m.get("pbrMetallicRoughness") or {}).get("baseColorTexture") or {}).get("index")
                        im = ""
                        if ti is not None and ti < len(g.get("textures", [])):
                            src = g["textures"][ti].get("source")
                            if src is not None and src < len(g.get("images", [])):
                                im = str(g["images"][src].get("uri") or g["images"][src].get("name") or "")[:60]
                        print(_tr("py.oar2glb.materiau_glb_0_r_couleur_1", m.get('name'), (m.get('pbrMetallicRoughness') or {}).get('baseColorFactor'), m.get('alphaMode', 'OPAQUE'), im or '-'))
    print(_tr("py.oar2glb.diag_rigges_0_transparents_1_boites", nr, ni, len(boxes), nm, len(parts)))
    if g:
        cache, nv = {}, 0
        for n in g.get("nodes", []):
            nv += node_all_invisible(g, n, cache)
        print(_tr("py.oar2glb.diag_nuds_glb_dont_tous_les", nv))
        print(_tr("py.oar2glb.diag_uuid_lisibles_dans_les_nuds", len(node_uuids(g))))
        for i, n in enumerate(g.get("nodes", [])[:6]):
            print(_tr("py.oar2glb.node_0_nom_1_r_extras", i, n.get('name'), json.dumps(n.get('extras'))[:100], sorted(k for k in n if k not in ('name', 'extras'))))


# ---------- 4. hors région ----------
def drop_far(g, vmax, size):
    # hors région : au-delà de la taille de la région (+10 m) en horizontal, ou de --max en hauteur
    sx, sy = size
    n = 0
    for sc in g.get("scenes", []):
        keep = []
        for i in sc.get("nodes", []):
            p = node_pos(g["nodes"][i])
            if g["nodes"][i].get("extras", {}).get("terrain"):
                keep.append(i)         # patches de terrain : jamais retirés
            elif not (-10 <= p[0] <= sx + 10 and -10 <= -p[2] <= sy + 10 and abs(p[1]) <= vmax):
                print(_tr("py.oar2glb.hors_region_node_0_1_a", i, g['nodes'][i].get('name', '?'), [round(c, 1) for c in p]))
                n += 1
            else:
                keep.append(i)
        sc["nodes"] = keep
    pts = [node_pos(g["nodes"][i]) for sc in g.get("scenes", []) for i in sc["nodes"]]
    if pts:
        lo = [round(min(p[k] for p in pts), 1) for k in range(3)]
        hi = [round(max(p[k] for p in pts), 1) for k in range(3)]
        print(_tr("py.oar2glb.etendue_0_objets_de_1_a", len(pts), lo, hi))
    return n


# ---------- 5. GLB ----------
GREY_PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNoAAAAggCBd81ytgAAAABJRU5ErkJggg==")


def find_file(base, name):
    names = [name]
    # convoar écrit parfois le hash en signé et l'annonce en non signé 64 bits (18446744071783355852 = -1926195764)
    m = re.match(r"^(\d{19,20})(_.*)$", name)
    if m and int(m.group(1)) >= 2**63:
        v = int(m.group(1)) - 2**64
        names += [f"{v}{m.group(2)}", f"{v % 2**32}{m.group(2)}"]
    for n in names:
        if (base / n).exists():
            return base / n
    for n in names:
        for root in (base, base.parent):
            hit = next(root.rglob(n), None)
            if hit:
                return hit
    return None


def read_uri(uri, base, image=False):
    if uri.startswith("data:"):
        return base64.b64decode(uri.split(",", 1)[1])
    from urllib.parse import unquote
    name = unquote(uri)
    hit = find_file(base, name)
    if hit:
        if hit.name != Path(name).name or hit.parent != (base / name).parent:
            print(_tr("py.oar2glb.glb_0_1", name, hit.name))
        return hit.read_bytes()
    if image:
        MISSING.append(name)
        return GREY_PNG
    files = sorted(base.rglob("*"))
    bufs = [x for x in files if x.suffix.lower() == ".buf"]
    sys.exit(_tr("py.oar2glb.erreur_0_introuvable_annonce_par_le", name, base, len(files), len(bufs))
             + ", ".join(f"{x.name} ({x.stat().st_size} o)" for x in bufs[:10])
             + _tr("py.oar2glb.espace_libre_sur_0_1_1f", base.anchor, shutil.disk_usage(base).free / 2**30))


MISSING = []


def report_missing(base, total):
    if not MISSING:
        return
    from collections import Counter
    files = [f for f in Path(base).rglob("*") if f.is_file()]
    ext = Counter(f.suffix.lower() for f in files)
    print(_tr("py.oar2glb.glb_0_texture_s_absente_s", len(MISSING), total) + ", ".join(MISSING[:3]))
    print(_tr("py.oar2glb.glb_0_contient_1_fichier_s", base, len(files)) + ", ".join(f"{k or _tr('py.oar2glb.sans_extension')} {v}" for k, v in ext.most_common(8)))
    print(_tr("py.oar2glb.glb_fichiers_images_presents_exemples") + ", ".join(f.name for f in files if f.suffix.lower() in (".jpg", ".png"))[:300])


def pad4(b, fill=b"\x00"):
    return b + fill * ((4 - len(b) % 4) % 4)


def pack_glb(g, base, out):
    blob, offs = bytearray(), []
    for b in g.get("buffers", []):
        offs.append(len(blob))
        blob += pad4(read_uri(b["uri"], base))
    for bv in g.get("bufferViews", []):
        bv["byteOffset"] = bv.get("byteOffset", 0) + offs[bv.get("buffer", 0)]
        bv["buffer"] = 0
    g.setdefault("bufferViews", [])
    for img in g.get("images", []):
        if "uri" not in img:
            continue
        data = read_uri(img["uri"], base, image=True)
        img["mimeType"] = "image/png" if data[:4] == b"\x89PNG" else "image/jpeg"
        g["bufferViews"].append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data)})
        img["bufferView"] = len(g["bufferViews"]) - 1
        del img["uri"]
        blob += pad4(data)
    g["buffers"] = [{"byteLength": len(blob)}]
    js = pad4(json.dumps(g, separators=(",", ":")).encode("utf-8"), b" ")
    total = 12 + 8 + len(js) + 8 + len(blob)
    with open(out, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total))
        f.write(struct.pack("<I4s", len(js), b"JSON") + js)
        f.write(struct.pack("<I4s", len(blob), b"BIN\x00") + blob)
    return total


# ---------- 6. terrain complet (régions de plus de 256 m) ----------
# convoar ne produit qu'un morceau de terrain sur les grandes régions : on le remplace par des carrés (patches)
# construits depuis la carte de hauteurs de l'OAR (terrains/*.r32, 1 échantillon par mètre).
TERRAIN_PATCH = 64            # côté d'un patch en mètres (--terrain-patch)
TERRAIN_COUVERT_MIN = 0.95    # le terrain de convoar est gardé s'il couvre au moins cette part de la carte
EAU_DEFAUT = 20.0             # WaterHeight par défaut d'OpenSim
LECTURE = 8 * 1024 * 1024     # taille des lectures du GLB en mode --terrain-only
PENTE_ROCHE = (32.0, 38.0)    # degrés : la roche apparaît à 32, pleine à 38 (environ 35)
# palette (rouge, vert, bleu) : documentée dans docs/fr/MANUEL.md § 15
SABLE_SEC, SABLE_HUMIDE = (214, 196, 142), (166, 150, 104)
HERBE_BASSE, HERBE_HAUTE, ROCHE = (98, 146, 66), (132, 140, 78), (122, 120, 116)


def mix(a, b, t):
    t = min(max(t, 0.0), 1.0)
    return [a[k] + (b[k] - a[k]) * t for k in range(3)]


def couleur_terrain(h, pente, eau):
    # h : altitude (m), pente : degrés, eau : niveau d'eau (m) -> (r, v, b) entiers
    alt = h - eau
    if alt <= 0:
        c = list(SABLE_HUMIDE)                                           # sous l'eau : sable humide
    else:
        herbe = mix(HERBE_BASSE, HERBE_HAUTE, (alt - 4.0) / 76.0)        # dégradé léger de 4 m à 80 m au-dessus de l'eau
        c = mix(SABLE_SEC, herbe, (alt - 1.0) / 3.0)                     # sable jusqu'à 1 m, herbe à partir de 4 m
    c = mix(c, ROCHE, (pente - PENTE_ROCHE[0]) / (PENTE_ROCHE[1] - PENTE_ROCHE[0]))
    return int(c[0] + 0.5), int(c[1] + 0.5), int(c[2] + 0.5)


def terrain_patch_data(h, n, x0, y0, x1, y1, eau):
    # patch couvrant les échantillons x0..x1, y0..y1 (bornes comprises) ; repère glTF : X = x, hauteur = h, Z = -y.
    # Normales et pente par différences centrées sur TOUTE la carte : les bords partagés sont identiques des deux côtés.
    nx, ny = x1 - x0 + 1, y1 - y0 + 1
    pos, nor, col = [], [], bytearray()
    lo, hi = [math.inf] * 3, [-math.inf] * 3
    for y in range(y0, y1 + 1):
        yl, yh = max(y - 1, 0), min(y + 1, n - 1)
        r0, rl, rh = y * n, yl * n, yh * n
        for x in range(x0, x1 + 1):
            xl, xh = max(x - 1, 0), min(x + 1, n - 1)
            v = h[r0 + x]
            hx = (h[r0 + xh] - h[r0 + xl]) / (xh - xl)
            hy = (h[rh + x] - h[rl + x]) / (yh - yl)
            g = math.sqrt(hx * hx + hy * hy)
            ln = math.sqrt(g * g + 1.0)
            pos += (x, v, -y)
            nor += (-hx / ln, 1.0 / ln, hy / ln)
            col += bytes(couleur_terrain(v, math.degrees(math.atan(g)), eau)) + b"\xff"
            if v < lo[1]:
                lo[1] = v
            if v > hi[1]:
                hi[1] = v
    lo[0], hi[0], lo[2], hi[2] = x0, x1, -y1, -y0
    idx = []
    for cy in range(ny - 1):
        for cx in range(nx - 1):
            a = cy * nx + cx
            b, c = a + 1, a + nx
            idx += (a, b, c, b, c + 1, c)            # triangles tournés vers le haut (+Y)
    return {"nv": nx * ny, "pos": struct.pack(f"<{len(pos)}f", *pos), "nor": struct.pack(f"<{len(nor)}f", *nor),
            "col": bytes(col), "idx": struct.pack(f"<{len(idx)}H", *idx), "ni": len(idx), "min": lo, "max": hi}


def terrain_donnees(terrain, eau, P):
    # tous les patches : tampon binaire + vues + accesseurs + meshes + nœuds, indices RELATIFS (voir terrain_ajouter)
    n, h = terrain
    blob, views, accs, meshes, nodes = bytearray(), [], [], [], []
    def vue(data, target):
        views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data), "target": target})
        blob.extend(data)
        blob.extend(b"\x00" * ((4 - len(blob) % 4) % 4))
        return len(views) - 1
    nv = 0
    for j, y0 in enumerate(range(0, n - 1, P)):
        for i, x0 in enumerate(range(0, n - 1, P)):
            d = terrain_patch_data(h, n, x0, y0, min(x0 + P, n - 1), min(y0 + P, n - 1), eau)
            nv += d["nv"]
            a0 = len(accs)
            accs.append({"bufferView": vue(d["pos"], 34962), "componentType": 5126, "count": d["nv"], "type": "VEC3", "min": d["min"], "max": d["max"]})
            accs.append({"bufferView": vue(d["nor"], 34962), "componentType": 5126, "count": d["nv"], "type": "VEC3"})
            accs.append({"bufferView": vue(d["col"], 34962), "componentType": 5121, "normalized": True, "count": d["nv"], "type": "VEC4"})
            accs.append({"bufferView": vue(d["idx"], 34963), "componentType": 5123, "count": d["ni"], "type": "SCALAR"})
            nom = f"Terrain {i},{j}"
            meshes.append({"name": nom, "primitives": [{"attributes": {"POSITION": a0, "NORMAL": a0 + 1, "COLOR_0": a0 + 2},
                                                        "indices": a0 + 3, "material": 0, "mode": 4}]})
            nodes.append({"name": nom, "mesh": len(meshes) - 1, "extras": {"terrain": True}})
    return {"blob": blob, "views": views, "accessors": accs, "meshes": meshes, "nodes": nodes, "vertices": nv}


def terrain_ajouter(g, td, buffer_index, base):
    # ajoute les patches au glTF : tampon n° buffer_index, données placées à partir de l'octet base ; retourne les nœuds ajoutés
    g.setdefault("materials", []).append({"name": "terrain", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 1},
                                          "doubleSided": False})
    mat = len(g["materials"]) - 1
    vo, ao, mo = len(g.setdefault("bufferViews", [])), len(g.setdefault("accessors", [])), len(g.setdefault("meshes", []))
    for v in td["views"]:
        g["bufferViews"].append({**v, "buffer": buffer_index, "byteOffset": v["byteOffset"] + base})
    for a in td["accessors"]:
        g["accessors"].append({**a, "bufferView": a["bufferView"] + vo})
    for m in td["meshes"]:
        pr = m["primitives"][0]
        g["meshes"].append({"name": m["name"], "primitives": [{**pr, "attributes": {k: v + ao for k, v in pr["attributes"].items()},
                                                               "indices": pr["indices"] + ao, "material": mat}]})
    first = len(g.setdefault("nodes", []))
    for nd in td["nodes"]:
        g["nodes"].append({**nd, "mesh": nd["mesh"] + mo})
    if not g.get("scenes"):
        g["scenes"] = [{"nodes": []}]
    g["scenes"][g.get("scene", 0)].setdefault("nodes", []).extend(range(first, len(g["nodes"])))
    return list(range(first, len(g["nodes"])))


def terrain_boite(g, tree, i):
    # boîte monde (glTF) du mesh du nœud i d'après les min/max de ses accesseurs POSITION ; None si inconnue
    pts = []
    for pr in g["meshes"][g["nodes"][i]["mesh"]].get("primitives", []):
        a = g["accessors"][pr["attributes"]["POSITION"]]
        if "min" not in a or "max" not in a:
            return None
        pts += [(x, y, z) for x in (a["min"][0], a["max"][0]) for y in (a["min"][1], a["max"][1]) for z in (a["min"][2], a["max"][2])]
    if not pts:
        return None
    w = tree.world(i)
    pw = [[w[r] * p[0] + w[4 + r] * p[1] + w[8 + r] * p[2] + w[12 + r] for r in range(3)] for p in pts]
    return [min(q[k] for q in pw) for k in range(3)], [max(q[k] for q in pw) for k in range(3)]


def terrain_decision(g, terrain, mode):
    # (action, nœuds convoar à retirer, message) ; action : "ajouter" ou "rien"
    n = terrain[0]
    if any(x.get("name", "").startswith("Terrain ") and x.get("extras", {}).get("terrain") for x in g.get("nodes", [])):
        return _tr("py.oar2glb.rien"), [], _tr("py.oar2glb.les_patches_de_terrain_sont_deja")
    tree = Tree(g)
    anciens = [i for i, x in enumerate(g.get("nodes", [])) if x.get("name") == "Terrain" and "mesh" in x]
    if mode == "yes":
        return "ajouter", anciens, _tr("py.oar2glb.force_terrain_oui")
    if not anciens:
        return _tr("py.oar2glb.rien"), [], _tr("py.oar2glb.pas_de_nud_terrain_de_convoar")
    surf, couvert = (n - 1.0) ** 2, 0.0
    for i in anciens:
        b = terrain_boite(g, tree, i)
        if b is None:
            return _tr("py.oar2glb.rien"), [], _tr("py.oar2glb.nud_terrain_sans_min_max_d")
        (x0, _, z0), (x1, _, z1) = b
        couvert += max(0.0, min(x1, n - 1.0) - max(x0, 0.0)) * max(0.0, min(z1, 0.0) - max(z0, -(n - 1.0)))
    part = couvert / surf
    if part >= TERRAIN_COUVERT_MIN:
        return _tr("py.oar2glb.rien"), [], _tr("py.oar2glb.terrain_de_convoar_complet_couvre_0", part * 100)
    return "ajouter", anciens, _tr("py.oar2glb.terrain_de_convoar_incomplet_couvre_0", part * 100)


def terrain_eau(scan):
    w = scan.get("water")
    return (w[0], _tr("py.oar2glb.lu_dans") + w[1]) if w else (EAU_DEFAUT, _tr("py.oar2glb.defaut_d_opensim_aucun_waterheight_dans"))


def terrain_resume(terrain, scan, P, td, t0):
    n = terrain[0]
    eau = terrain_eau(scan)
    print(_tr("py.oar2glb.terrain_carte_0_x_1_echantillons", n, n, eau[0], eau[1], len(td['nodes']), P, td['vertices'], len(td['blob']) / 1048576, time.time() - t0))


def terrain_prepare(scan, mode):
    # contrôles communs ; retourne la carte ou None (message déjà écrit)
    if mode == "no":
        print(_tr("py.oar2glb.terrain_desactive_terrain_non"))
        return None
    t = scan.get("terrain")
    if not t or t[0] < 2:
        print(_tr("py.oar2glb.terrain_cet_oar_n_a_pas"))
        return None
    if t[0] != scan["size"][0] or t[0] != scan["size"][1]:
        print(_tr("py.oar2glb.terrain_attention_carte_de_0_x", t[0], t[0], scan['size'][0], scan['size'][1]))
    return t


def terrain_pipeline(g, scan, mode, P):
    # chaîne convoar : remplace le terrain incomplet ; les données vont dans un nouveau tampon (data: URI, lu par pack_glb)
    t0 = time.time()
    terrain = terrain_prepare(scan, mode)
    if not terrain:
        return
    action, anciens, msg = terrain_decision(g, terrain, mode)
    print(_tr("py.oar2glb.terrain_0", msg))
    if action == "rien":
        return
    td = terrain_donnees(terrain, terrain_eau(scan)[0], P)
    for i in anciens:
        remove_node(g, i)
    bi = len(g.setdefault("buffers", []))
    terrain_ajouter(g, td, bi, 0)
    g["buffers"].append({"byteLength": len(td["blob"]), "uri": "data:application/octet-stream;base64," + base64.b64encode(bytes(td["blob"])).decode()})
    terrain_resume(terrain, scan, P, td, t0)
    if anciens:
        print(_tr("py.oar2glb.terrain_0_nud_s_terrain_de", len(anciens)))


def terrain_seul(glb, scan, out, mode, P, chunk=LECTURE):
    """Ajoute les patches à un GLB existant sans le charger : en-tête JSON réécrit, chunk binaire recopié par morceaux,
    nouveaux tampons ajoutés à la fin. Retourne un dict de mesures, ou None si rien n'est écrit."""
    t0 = time.time()
    terrain = terrain_prepare(scan, mode)
    if not terrain:
        return None
    mesures = {"lu": 0, "lecture_max": 0}
    with open(glb, "rb") as f:
        def lire(k):
            d = f.read(k)
            mesures["lu"] += len(d)
            mesures["lecture_max"] = max(mesures["lecture_max"], len(d))
            return d
        taille = os.fstat(f.fileno()).st_size
        mag, ver, _ = struct.unpack("<4sII", lire(12))
        if mag != b"glTF" or ver != 2:
            sys.exit(_tr("py.oar2glb.erreur_0_n_est_pas_un_2", glb))
        chunks, pos = [], 12
        while pos + 8 <= taille:
            f.seek(pos)
            ln, kind = struct.unpack("<I4s", lire(8))
            chunks.append((kind, pos + 8, ln))
            pos += 8 + ln + (-ln % 4)
        if not chunks or chunks[0][0] != b"JSON":
            sys.exit(_tr("py.oar2glb.erreur_0_le_premier_chunk_n", glb))
        f.seek(chunks[0][1])
        g = json.loads(lire(chunks[0][2]).decode("utf-8"))
        binc = next((c for c in chunks if c[0] == b"BIN\x00"), None)
        autres = [c for c in chunks[1:] if c is not binc]
        action, anciens, msg = terrain_decision(g, terrain, mode)
        print(_tr("py.oar2glb.terrain_0", msg))
        if action == "rien":
            return None
        td = terrain_donnees(terrain, terrain_eau(scan)[0], P)
        for i in anciens:
            remove_node(g, i)
        bin_len = binc[2] if binc else 0
        base = bin_len + (-bin_len % 4)
        if binc and (not g.get("buffers") or "uri" in g["buffers"][0]):
            sys.exit(_tr("py.oar2glb.erreur_0_le_tampon_0_n", glb))
        if not g.get("buffers"):
            g["buffers"] = [{"byteLength": 0}]
        terrain_ajouter(g, td, 0, base)
        bin_total = base + len(td["blob"])
        g["buffers"][0]["byteLength"] = bin_total
        js = pad4(json.dumps(g, separators=(",", ":")).encode("utf-8"), b" ")
        total = 12 + 8 + len(js) + 8 + bin_total + sum(8 + c[2] + (-c[2] % 4) for c in autres)
        part = Path(str(out) + ".part")
        try:
            with open(part, "wb") as o:
                o.write(struct.pack("<4sII", b"glTF", 2, total))
                o.write(struct.pack("<I4s", len(js), b"JSON") + js)
                o.write(struct.pack("<I4s", bin_total, b"BIN\x00"))
                def copier(debut, longueur):
                    f.seek(debut)
                    while longueur > 0:
                        d = lire(min(chunk, longueur))
                        if not d:
                            sys.exit(_tr("py.oar2glb.erreur_0_tronque", glb))
                        o.write(d)
                        longueur -= len(d)
                if binc:
                    copier(binc[1], bin_len)
                o.write(b"\x00" * (base - bin_len))
                o.write(bytes(td["blob"]))
                for kind, debut, ln in autres:
                    o.write(struct.pack("<I4s", ln, kind))
                    copier(debut, ln)
                    o.write(b"\x00" * (-ln % 4))
            os.replace(part, out)
        finally:
            part.unlink(missing_ok=True)
    terrain_resume(terrain, scan, P, td, t0)
    print(_tr("py.oar2glb.terrain_0_nud_s_terrain_retire", len(anciens), mesures['lu'] / 1048576, chunk // 1024))
    mesures.update(patches=len(td["nodes"]), sommets=td["vertices"], ajoutes=len(td["blob"]), retires=len(anciens))
    return mesures


def main():
    ap = argparse.ArgumentParser(description=_tr("py.oar2glb.desc", VERSION), epilog=_tr("py.oar2glb.epilog"), formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False)
    i18n_add_common(ap)
    ap.add_argument("--version", action="version", version=f"oar2glb {version_tag()}", help=_tr("py.common.version"))
    ap.add_argument("oar", help=_tr("py.oar2glb.help.oar"))
    ap.add_argument("--reencode", action="store_true", help=_tr("py.oar2glb.reencoder_les_textures_j2k_avant_convoar"))
    ap.add_argument("--max", type=float, default=600.0, help=_tr("py.oar2glb.hauteur_max_m_d_un_objet"))
    ap.add_argument("--convoar", help=_tr("py.oar2glb.help.convoar"))
    ap.add_argument("--keep", action="store_true", help=_tr("py.oar2glb.garder_les_fichiers_intermediaires"))
    ap.add_argument("--keep-invisible", action="store_true", help=_tr("py.oar2glb.garder_les_prims_entierement_transparents_re"))
    ap.add_argument("--markers", dest="reperes", action="store_true", help=_tr("py.oar2glb.ajouter_un_mat_rouge_de_15"))
    ap.add_argument("--diag", action="store_true", help=_tr("py.oar2glb.ne_rien_modifier_lister_les_objets"))
    ap.add_argument("--glb", help=_tr("py.oar2glb.avec_diag_glb_ou_gltf_a"))
    ap.add_argument("--nopause", action="store_true", help=_tr("py.oar2glb.ne_pas_attendre_entree_a_la"))
    ap.add_argument("--terrain", type=lambda v: {"oui": "yes", "non": "no"}.get(v, v), choices=("auto", "yes", "no"), default="auto",
                    help=_tr("py.oar2glb.terrain_complet_depuis_la_carte_de"))
    ap.add_argument("--terrain-patch", type=int, default=TERRAIN_PATCH, help=_tr("py.oar2glb.cote_d_un_patch_de_terrain", TERRAIN_PATCH))
    ap.add_argument("--terrain-only", dest="terrain_seul", metavar="GLB", help=_tr("py.oar2glb.ne_pas_lancer_convoar_ajouter_le"))
    ap.add_argument("--output", metavar="OUTPUT", dest="sortie", help=_tr("py.oar2glb.avec_terrain_seul_fichier_glb_de"))
    a = ap.parse_args()
    a.convoar = a.convoar or default_convoar()
    if not 2 <= a.terrain_patch <= 255:
        sys.exit(_tr("py.oar2glb.erreur_terrain_patch_doit_etre_compris"))

    oar = Path(a.oar).resolve()
    if not oar.exists():
        sys.exit(_tr("py.oar2glb.erreur_0_introuvable", oar))
    if a.terrain_seul:
        glb = Path(a.terrain_seul).resolve()
        if not glb.is_file():
            sys.exit(_tr("py.oar2glb.erreur_0_introuvable", glb))
        out = Path(a.sortie).resolve() if a.sortie else glb.with_name(glb.stem + "-terrain.glb")
        if out == glb:
            sys.exit(_tr("py.oar2glb.erreur_la_sortie_ne_peut_pas"))
        r = terrain_seul(glb, oar_scan(oar, terrain_seul=True), out, a.terrain, a.terrain_patch)
        print(f"[OK] {out}" if r else _tr("py.oar2glb.terrain_aucun_fichier_ecrit"))
        return
    if a.diag:
        scan = oar_scan(oar)
        auto = sorted((oar.parent / (oar.stem + "-GLTF")).glob("*.gltf"), key=lambda q: q.stat().st_mtime)
        glb = Path(a.glb) if a.glb else (auto[-1] if auto else oar.with_suffix(".glb"))
        diag(scan, read_glb_json(glb) if glb.exists() else None, glb.name, glb.parent if glb.suffix.lower() == ".gltf" else None)
        return
    if not Path(a.convoar).exists():
        sys.exit(_tr("py.oar2glb.erreur_convoar_introuvable_0_utilise_convoar", a.convoar, CONVOAR_URL))
    scan = oar_scan(oar)
    size, objs = oar_info(scan)
    src, tmp_oar = oar, None
    if a.reencode:
        tmp_oar = oar.with_name(oar.stem + "-reenc.oar")
        reencode_oar(oar, tmp_oar)
        src = tmp_oar
    out = oar.with_suffix(".glb")
    if out.exists():
        out.unlink()   # pas d'ancien GLB qui ferait croire à un succès si la suite échoue
    outdir = oar.parent / (oar.stem + "-GLTF")
    if outdir.exists():
        shutil.rmtree(outdir)

    run_convoar(a.convoar, src, outdir)
    for essai in range(1, MAX_RETRY + 1):
        time.sleep(3)                      # laisse finir les écritures de fichiers
        miss = missing_images(outdir)
        if not miss:
            break
        print(_tr("py.oar2glb.convoar_0_image_s_annoncee_s", len(miss), ', '.join(miss[:2]), essai, MAX_RETRY))
        old = outdir.with_name(outdir.name + f"-essai{essai}")
        shutil.rmtree(old, ignore_errors=True)
        outdir.rename(old)
        run_convoar(a.convoar, src, outdir)
        n_rec = 0
        for f in old.rglob("*"):
            if f.is_file() and f.suffix.lower() in (".jpg", ".png", ".gif", ".bmp"):
                dst = outdir / f.relative_to(old)
                if not dst.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dst)
                    n_rec += 1
        print(_tr("py.oar2glb.convoar_0_image_s_recuperee_s", n_rec))
        if not a.keep:
            shutil.rmtree(old, ignore_errors=True)

    gltfs = sorted(outdir.glob("*.gltf"), key=lambda p: p.stat().st_mtime)
    if not gltfs:
        sys.exit(_tr("py.oar2glb.erreur_aucun_gltf_produit_dans_0", outdir))
    g = load_gltf(gltfs[-1])
    check(g)
    if objs and any(not (0 <= o["pos"][0] <= 256 and 0 <= o["pos"][1] <= 256) for o in objs):
        fix_positions(g, objs)
    repair(g, outdir, scan, a.keep_invisible, a.reperes)
    n = drop_far(g, a.max, size)
    terrain_pipeline(g, scan, a.terrain, a.terrain_patch)      # après drop_far : les patches ne sont jamais retirés
    size = pack_glb(g, outdir, out)
    report_missing(outdir, len(g.get("images", [])))
    print(_tr("py.oar2glb.ok_0_1_1f_mo_2", out, size/1048576, len(g.get('meshes', [])), len(g.get('images', [])), n))
    if not a.keep:
        shutil.rmtree(outdir, ignore_errors=True)
        if tmp_oar:
            tmp_oar.unlink(missing_ok=True)


class Tee:
    def __init__(self, *s): self.s = s
    def write(self, x):
        for t in self.s:
            t.write(x); t.flush()
    def flush(self):
        for t in self.s:
            t.flush()


# v43 : anciens noms d'options (avant la v43), toujours acceptés : remplacés avant la lecture de la ligne de commande
OLD_OPTIONS = {"--reperes": "--markers", "--terrain-seul": "--terrain-only", "--sortie": "--output"}


def old_options(argv):
    """Remplace les anciens noms d'options par les nouveaux (« --nom=valeur » compris)."""
    out = []
    for x in argv:
        k, eq, v = str(x).partition("=")
        out.append(OLD_OPTIONS.get(k, k) + eq + v if k.startswith("--") else x)
    return out


if __name__ == "__main__":
    sys.argv = old_options(sys.argv)
    if "--version" in sys.argv[1:]:      # ni journal ni pause « Entrée »
        print(_tr("py.oar2glb.oar2glb_0_2", version_tag()))
        sys.exit(0)
    log = Path(__file__).resolve().with_name("oar2glb.diag.log" if "--diag" in sys.argv else "oar2glb.log")
    lf = open(log, "w", encoding="utf-8")
    sys.stdout, sys.stderr = Tee(sys.__stdout__, lf), Tee(sys.__stderr__, lf)
    print(_tr("py.oar2glb.oar2glb_0", version_tag()))
    print(_tr("py.oar2glb.args"), sys.argv[1:])
    code = 0
    try:
        main()
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code)
        code = e.code if isinstance(e.code, int) else 1
    except Exception:
        traceback.print_exc()
        code = 1
    print(_tr("py.oar2glb.log_0", log))
    if "--nopause" not in sys.argv and "--terrain-only" not in sys.argv and sys.stdin and sys.stdin.isatty():
        input(_tr("py.oar2glb.entree_pour_fermer"))
    sys.exit(code)
