# Finding each version


> **Manual numbering.** The "manual § N" references of this file date from before the manual was rebuilt (03/11/2026) and follow the old plan; the correspondence table is in `CLOUD_RAPPORT.md` (and chapter 13 of the manual summarises what each version brought).
The first versions were all made on 18/10/2026. This history was **reconstructed afterwards** from the source backups made during the day; it is accurate about what exists, but incomplete.

## What you need to know

- Each line below is a state of the sources (`src/` folder) at the end of a series of changes. The date is in dd/mm/yyyy format. The time (Paris time) is only given for the reconstructed entries; from v19 on, a line is added at each delivery (see "Livraison d'une version" in `CLAUDE.md`).
- **Before 12:05, nothing was kept**: the work had started around 09:28 (first request), with the basic export, the sea hole and high resolution.
- Version numbers are only displayed in the pages from v5 on (around 16:13). The tags **v14 to v18** are set; v19 (commit `5632bd5`) and the following ones are to be set with the command given at each delivery. v14 was checked byte for byte against the v14 files supplied to the project; v15 to v17 are the states recorded at the start of each following version; v18 is the last state.
- The message of each entry was written afterwards, from the differences between states and the order of the requests.
- The built files (`dist/`) are not in the repository. Only the last state contains `build.py`: to rebuild an old version, get its `src/` and build them with the `build.py` of the last state.
- The author of the entries is `Klaatou` for convenience; the next entries will take the identity configured on your machine.

## History

| Date | Time | Tag | Content |
|---|---|---|---|
| 18/10/2026 | 12:05 |  | First-person walk (F key): first draft of the core |
| 18/10/2026 | 12:44 |  | Grid collisions and walk-through elements |
| 18/10/2026 | 13:23 |  | Element name on click; real-time visitors |
| 18/10/2026 | 13:50 |  | Viewer: first state kept |
| 18/10/2026 | 14:28 |  | Chat: bubbles and adjustable duration; first states of the script and of the page template |
| 18/10/2026 | 14:54 |  | Server: chat rate limits, history, proxy |
| 18/10/2026 | 14:55 |  | Zones: portals, web link and Home Assistant signs, arrival points |
| 18/10/2026 | 15:42 |  | Viewer: zone editor and public/perso profiles |
| 18/10/2026 | 16:32 |  | Global view: visitors in walk mode visible (spectator) |
| 18/10/2026 | 16:39 |  | Landing marker on the ground and choice of the arrival point |
| 18/10/2026 | 16:55 |  | Export: zones, profiles and PowerShell command line |
| 18/10/2026 | 17:17 |  | Reliable double-click teleport despite lag |
| 18/10/2026 | 17:55 |  | Visitors' diamond hidden behind walls; names remembered |
| 18/10/2026 | 18:02 |  | Settings panel for visitors |
| 18/10/2026 | 19:25 | v14 | v14: reloadable zones, kick and ban |
| 18/10/2026 | 20:14 | v15 | v15: world map (M key) |
| 18/10/2026 | 20:52 | v16 | v16: settings remembered per file; map oriented X east / Y north |
| 18/10/2026 | 21:04 | v17 | v17: --register, map page, thumbnail that can be saved, compact placement |
| 18/10/2026 | 21:20 |  | v18: --settings, registration without .glb, multi-source maps |
| 18/10/2026 |  | v19 | v19: modular mode (`--modular`, `--config-only`, "Modular mode" box in the viewer), commit `5632bd5` |
| 18/10/2026 |  | v20 | v20: universal modular mode (identical shell for all regions, zones read again from `<page>.zones.json` or `zones.json`, `.zip` export from the viewer, zones linked to an element of the model) |
| 19/10/2026 |  | v21 | v21: "Link to an element" fix (exclusive mode, box in world coordinates, named mesh hit, refused beyond 30 m, wireframe outline) |
| 19/10/2026 |  | v22 | v22: portal to an arrival point of the same region, user manual |
| 19/10/2026 |  | v23 | v23: single click with no effect on the target, link to the clicked piece (name#index, 10 m limit), rotation of the region, user manual |
| 19/10/2026 |  | v24 | v24: links behave as on the web (no more cylinders in the exported page, ground marker, tooltip on hover, "Always show the name" option), user manual |
| 20/10/2026 |  | v25 | v25: oar2glb.py, rigged meshes rebuilt from the OAR's .llmesh, invisible prims and animesh boxes removed, --diag, --reperes, --keep-invisible, convoar run again if images are missing, user manual |
| 21/10/2026 |  | v26 | v26: single shell in modular mode (`--shared-shell`, `index.html?region=NOM`, name refused without a network request), `.zip` export from the viewer as `index.html`, `oar2glb.py --version` built in `dist/`, "huge regions" notes |
| 21/10/2026 |  | v27 | v27: stacked avatar markers (name, chat bubble, diamond): the bubble is no longer covered, `tests/v27.py` |
| 21/10/2026 |  | v28 | v28: `tools/glb2tiles.py` (splits a huge GLB into standalone tiles, `--analyse`), `glb-stats.py` as shared functions, `tests/glb2tiles.py` |
| 22/10/2026 |  | v29 | v29: oar2glb.py complete terrain for regions larger than 256 m (patches from the height map, `--terrain`, `--terrain-patch`, `--terrain-seul`), glb2tiles.py `--exclure` and pause without a console, `tests/terrain.py` |
| 22/10/2026 |  | v30 | v30: the shell loads a tiled region (`tiles` in `X.config.json`, radius, hysteresis, MB / triangle budget, collision grid per tile, ground locked until the tile is ready, `?rayon=`), `glb2html.py --tiles`, `glb2tiles.py` explains the "bytes saved" at 0, `tests/tuiles.py` |
| 22/10/2026 |  | v31 | v31: `glb2tiles.py` replaces empty, invalid or truncated images with a grey PNG (one per tile) and writes a light overview `X.overview.glb` (`--vue-ensemble-seule`, `--ov-*`); the shell loads it before the tiles, hides each cell when its tile is displayed, frames the whole region; leaving walk mode: target under the avatar, same camera offset; old tiles deleted; `tests/v31.py`, `tests/glbfab.py` |
| 22/10/2026 |  | v32 | v32: the viewer opens a tiled region (folder chosen or dropped, `?tuiles=`, original frame, overview, zones placed on the loaded tiles, `X.zones.json` export and `--tiles` command), coordinates of the aimed point and of the target with copy, position shown in the help panel of the shell, zones linked to an object in tiles mode (`extras.ref` / `extras.box` written by `glb2tiles.py`, `--sans-references`), `tests/v32.py` |
| 22/10/2026 |  | v33 | v33: start at an arrival fixed (loader reference = arrival, the arrival's tiles first, "Loading the ground…" text and no more silent black screen, log per tile), `default` arrival and return (R), `#pos=` and "Go to", flight and three views, persistent / saved chat, mentioned nickname, completion, avatar colour, `--zone-marker`, `--show-spawns`, `--fly`, zones saved in the region folder, `tests/v33.py` |
| 22/10/2026 |  | v34 | v34: selectable help and separate status block (view, mode, mouse, position), hover area of the markers at the ring's radius, flight (Page Up / Page Down, automatic landing, button), free mouse after Esc (G, button), live colour, `glb2html.py --maj`, personal link `#name=…&key=…`, nickname of the map page, `tests/v34.py` |
| 22/10/2026 |  | v35 | v35: help in groups and collapsible panels, Firestorm-style controls (F / P / E / Page Up / running / M / Ctrl+M / End / Alt), flight by long press, third person (orbiting camera, avatar turning towards its walking direction), zone tooltips at 40 m (`--zone-info-dist`), copy without a secure context, wheel and orbit of the free camera, `--maj` with the world map |
| 23/10/2026 |  | v36 | v36 (batch A): F and P enter and leave walk mode, E is again the zone key, flight with Home / Page Up held / Space, AZERTY / QWERTY layout (real letters in the help, M by the printed letter), help and information in three steps, occupied arrival (the newcomer is shifted), cone-shaped portal markers (`--zone-cone`, T), arrival / departure / mention sounds with volume, "Copy my position" (URL / xyz) and "Go to" with `#pos=`, `tests/v36.py`; batches B to D: interface of the page, the viewer and the Python tools in French and English (`src/i18n/*.json`, "Language / Langue" setting, `--lang`, `WEB3D_LANG`), bilingual `REFERENCE_OPTIONS.md`, `README.en.md`, `tests/i18n.py`, `v36_lang.py`, `v36_viewer_lang.py`, `tools_lang.py`, `doc_options.py` |
| 23/10/2026 |  | v37 | v37: running indicator, compass (`--compass`, `--north`), constant-size cone with distance (`--zone-info-dist` 150 m, up to 500), occupied arrival around the occupant and facing them, mentioned nickname blinking until the first action, hash separated by & or #, resizable Help / Information windows, O key (Settings); chat history (`--history` 200, `--history-file`, `--history-days`, `history` message, "Older messages" button, unread, mentions); default region (`default.json`, `--default`), `--lib-url`, subfolders (`?region=a/b/nom`); tools' `--help` with name and version |
| 23/10/2026 |  | v38 | v38: manual, procedures and history translated into English (`docs/en/`), French documents in `docs/fr/` (`MODE_EMPLOI.md` becomes `MANUEL.md`), `README.md` in English and `README.fr.md`, `verif_trad.py` |
| 23/10/2026 |  | v39 | v39: "Copy diagnostics" button (page and viewer: version, graphics card, rendering, tiles, status, presence, last errors; addresses masked), `tests/v39.py` |
| 24/10/2026 |  | v40 | v40: Arrivals window (L key, teleport), "Recenter the view" button, "Full manual" link, diagnostics tooltip, `tests/v40.py` |
| 24/10/2026 |  | v41 | v41: tooltips of the H, I, L windows and Settings, windows dragged by their title (left and right stacks, free), layout remembered and `disposition.json` file, `tests/v41.py` |
| 24/10/2026 |  | v42 | v42: light rendering (box and "Fine settings…": resolution, frames per second, overview only, tile radius, antialiasing; `--light`), narrower Settings, `tests/v42.py` |
| 24/10/2026 |  | v43 | v43: manual § 27 "JSON file reference", samples in `docs/samples/`, `tests/samples.py`, English names (options, values, keys, addresses; old names accepted), `gen_reference.py` without pause |
| 24/10/2026 |  | v44 | v44: last names in English (`gen_reference.py`, `verif_trad.py`, `[update]` messages, example names in the help, viewer "Marker of portals and free zones" menu), automatic check of old names in `tests/samples.py`, history completed (v38 to v44) |
| 24/10/2026 |  | v45 | v45: the page says why the presence connection closed (`tests/v45.py`, manual § 28), "Presence connection" diagnostics line; procedures § 11 completed (Tailscale Funnel tried, way D Linux VM + Funnel + Apache, case of another service already published); the shell's `lib` folder is set by a single line (`const LIB`), `--update` keeps it, `dist/index.html` built by `build.py`, test page `tests/essai_importmap.html` (`tests/v45_lib.py`) |
| 25/10/2026 |  | v46 | v46: on-screen controls (manual § 29): always visible status line, 3 x 3 arrows while walking (forward, back, turn, step, Run, up and down while flying) and in the overview (move, turn, zoom, recenter), K key and "Arrows (K)" button; touch mode (column of buttons, menu, full screen, folded windows with ✕, drag a finger to look around, touch chat, landscape orientation, tooltip on long press); tooltips on all buttons; one shell for a whole site (§ 29.8); `tests/v46.py` |
| 25/10/2026 |  | v47 | v47: world map (manual § 30): tile "N visitors · N walking" and tooltip on hover, optional address (`showUrl`, "Show addresses" checkbox), `regions.json` with a header kept by `--register`, `visitors` in the presence server reply, universal `dist/carte.html`; `tests/v47.py` |
| 25/10/2026 |  | v48 | v48: visit log (manual § 31): the presence server records each visit in a separate file (`--visits`, no IP; `--visits-days`, `--visits-names`), `visits-key ROOM` command; the creator opens their page with `#visits` and the key: summary per day, visits of the last 30 days, CSV; `tests/v48.py` |
| 25/10/2026 |  | v49 | v49: `glb2html.py --scan-sites` updates `regions.json` from the sites folder (cards, `NOM.jpg` thumbnails, nothing deleted), manual § 32; `tests/v49.py` |
| 25/10/2026 |  | v50 | v50: viewer, world map: import and export of `regions.json` with a header, card fields kept, in-place "Add" (manual § 33); `tests/v50.py`; README, procedures § 4 and § 7, `CLAUDE.md` updated |
| 25/10/2026 |  | v51 | v51: creators on the presence server (manual § 34): `--creators` (`presence_creators.json` re-read on change: origins, room prefix, limits, suspension), refusal shown by the page and the viewer, `creators` command; `tests/v51.py` |
| 25/10/2026 |  | v51 | v51 (continued, first delivered as v52): presence server, a connection closed without a request gives an "empty" line with the address instead of a trace (manual § 34.9); `tests/v51_vides.py` |
| 25/10/2026 |  | v51 | v51 (continued): presence address `ws://*:PORT` (the star takes the page's name) for the page, the Map window, `carte.html`, the visit log and the viewer (manual § 34.10); `tests/v51_etoile.py` |
| 25/10/2026 |  | v52 | v52: `carte.html` (region count, total, arrival alert with sound and marker, thumbnail enlarged to 400 px, visitors and walkers on two lines in French), "walker", "Show the sea" checkbox (manual § 35.1 to 35.4); `tests/v52.py` |
| 25/10/2026 |  | v52 | v52 (continued): presence server, an ordinary HTTP request gives an "http request" line instead of a trace (manual § 35.5); `tests/v52_http.py` |
| 25/10/2026 |  | v52 | v52 (continued): renamed tiled region, the overview stays linked to the tiles by file name (manual § 35.6); `tests/v52_renom.py` |
| 25/10/2026 |  | after v52 | Documents: overview on one page (`docs/fr/VUE_ENSEMBLE.md`, `docs/en/OVERVIEW.md`); "Credits" section of the READMEs |
| 26/10/2026 |  | after v52 | README: prerequisite of the external converter `convoar.exe` for `oar2glb.py`; `.gitattributes` (LF line endings in the repository) |
| 27/10/2026 |  | after v52 | Corrective batch after an audit: presence server log without control characters, `.gitignore` (`*.zones.json`, `*.jsonl`), `null` origin without quotes reported, READMEs, manual § 20.8, § 34 and § 35.5, repaired tests, code hygiene; `tests/correctifs_v52.py` |
| 27/10/2026 |  | after v52 | `oar2glb.py`: no more personal default path for `convoar.exe` (`CONVOAR` variable, PATH, next to the tool), help message with the download address; `tests/correctifs_v52.py` |
| 27/10/2026 |  | after v52 | README: demonstration GIF (`docs/images/PalmIsland_demo.gif`, PalmIsland region) |
| 28/10/2026 |  | after v52 | Online demo: `Web_3d_demo` repository published with GitHub Pages (PalmIsland and Hobbit regions, relative portals, no presence); README: link to the demo, clickable GIF |
| 28/10/2026 |  | after v52 | Demo: bilingual README of the `Web_3d_demo` repository, share preview (`ajout_og.py` and `preview.jpg`, outside the repository), description, topics and social preview image of the GitHub repositories |
| 28/10/2026 |  | after v52 | `carte.html`: alert checkbox hidden without a presence server; presence server: unreadable requests (RDP, TLS probes) in one line; `tests/v52.py`, `tests/v52_http.py` |
| 28/10/2026 |  | after v52 | Mouse: a click in the view no longer captures it, only **G** or the "Capture the mouse" button; help texts, manual, `tests/v34.py` |
| 28/10/2026 |  | after v52 | Mouse: the **G** key becomes a toggle (capture / release); the button only captures; help texts, manual, `tests/v34.py` |
| 29/10/2026 |  | after v52 | "3D" icon of the pages, replaceable by a `favicon.ico` next to the page (`src/favicon.ico`, `build.py`, manual § 36.1); `tests/icone.py` |
| 29/10/2026 |  | after v52 | `carte.html`: the displayed address moves out of the card's link (selectable and copyable), zoom kept; `tests/v52.py`, `tests/v47.py` |
| 29/10/2026 |  | after v52 | Presence server: IPv6 by `/64` prefix (limit and bans), `oublier <pseudo>` command; page: presence connection attempts stop; `tests/ipv6.py`, `tests/oublier.py`, `tests/essais_presence.py`; manual § 36.2 to 36.4 |
| 29/10/2026 |  | after v52 | Presence server: `pseudos [filtre]` console command (list of the reserved names); `tests/oublier.py` |
| 29/10/2026 |  | 1.0.0 | `1.0.0` numbering (v52 = 1.0.0, `X.Y.Z` scheme, manual § 36.5); `PROCEDURES` revised (Debian 13 VM: service and `tmux` console, texts of `lance_presence.sh` and of the unit); overview, manual, `CLAUDE.md`; `docs/samples/README.fr.md` and `README.md`; `tests/samples.py` |
| 29/10/2026 |  | after 1.0.0 | `web3d-presence.service`: `NOM_USER` becomes `UTILISATEUR` (as `PROCEDURES` § 11) |
| 29/10/2026 |  | after 1.0.0 | Note for creators welcomed on a presence server: `docs/fr/CREATEURS.md` and `docs/en/CREATORS.md` (manual § 34.5) |
| 30/10/2026 |  | after 1.0.0 | `PROCEDURES` § 11: black VM console screen, two sightings and what to do |
| 30/10/2026 |  | after 1.0.0 | `presence_server.py`: the "http request" lines show the address of the `--proxy-header` header; test `tests/http_proxy.py` |
| 30/10/2026 |  | after 1.0.0 | Moderation console: terminal sequences removed, `version` command, `REVISION` file; test `tests/console.py` |
| 30/10/2026 |  | after 1.0.0 | `image` zone: picture laid flat on a wall, placed by click in the editor; images looked for in the region's folder; editor label never cut off; `tests/image_zone.py` |
| 30/10/2026 |  | after 1.0.0 | Mark (fingerprint) of every built file, listed by `build.py` and shown by the tools; end of the `REVISION` file; `tests/marque.py` |
| 30/10/2026 |  | after 1.0.0 | Clear message when WebGL is unavailable (region page and viewer); `tests/webgl_absent.py` |
| 30/10/2026 |  | after 1.0.0 | Editor: "Choose the region folder (image preview)" button (read-only, handle shared with the saving of zones); `tests/image_dossier.py` |
| 30/10/2026 |  | after 1.0.0 | Pointer: name of the root object (`--names` label, "Targeted" panel); hole guide unchecked by default; `tests/pointeur_objet.py` |
| 30/10/2026 |  | after 1.0.0 | `--solid-materials` option (`solidMaterials` key, "Materials drawn solid" field): end of the see-through `BLEND` walls; `tests/solid_materiaux.py` |
| 30/10/2026 |  | after 1.0.0 | `image` zone: flexible name (`1` gives `1.jpg` or `1-Titre.png`), caption under the image, names completed after the folder is chosen; `tests/image_legende.py` |
| 31/10/2026 |  | after 1.0.0 | Generator: image names without an extension completed from the page's folder; "bare number" mode (`imageExts`, `12.txt` file); `tests/image_noms_gen.py`, `tests/image_numero.py` |
| 31/10/2026 |  | after 1.0.0 | Batch 1.0.1: `VERSION` takes a patch number with every patch; `medias` subfolder (`mediaDir`); "Copy diagnostics" lists the image zones; `tests/image_medias.py`, `tests/image_diag.py` |
| 31/10/2026 |  | after 1.0.0 | Batch 1.0.2: images, captions and the whole `.glb` of the modular page always revalidated (no stale cache); `tests/image_cache.py` |
| 31/10/2026 |  | after 1.0.0 | Batch 1.0.3: same when the replaced file is older (`HEAD` request, `ETag` or `Last-Modified` fingerprint); `tests/image_cache_vieux.py` |
| 31/10/2026 |  | after 1.0.0 | Batch 1.0.4: one version number per built file (`VERSIONS.json` written by `build.py`) |
| 31/10/2026 |  | 1.1.0 | Release 1.1.0: `VERSION` 1.1.0; manual (§ 37 and §§ 3, 27.3, 27.4, 34.4, 36.5), `PROCEDURES` (§§ 4, 5, 9, 11), histories, README, samples, overview, `CLAUDE.md`, `CHANGELOG.md`, French and English |
| 31/10/2026 |  | after 1.1.0 | Batch 1.1.1: optional `link` key of an `image` zone (click or E opens the page); no more "click or E" prompt on an image zone without a link; `tests/lien_image.py` |
| 31/10/2026 |  | after 1.1.0 | Batch 1.1.2: documents for the image zone link (manual, zones sample, samples README) |
| 31/10/2026 |  | after 1.1.0 | Batch 1.1.3: "Image zone numbers (to find them)" box in Settings; the zone placement click also works while walking; `tests/zones_numeros.py`, `tests/pose_promenade.py` |
| 31/10/2026 |  | after 1.1.0 | Batch 1.1.4: image zone numbers flat, in the image's plane |
| 31/10/2026 |  | after 1.1.0 | Batch 1.1.5: histories, `PROCEDURES` and overview; `image_zone` and `image_dossier` tests: file names without a hyphen (the caption was read instead of the image) |
| 01/11/2026 |  | after 1.1.0 | Batch 1.1.6: `dist/` tracked by git (`.gitignore`), `tests/dist_a_jour.py` test, `README` and `PROCEDURES` § 6: where to find `presence_server.py` |
| 01/11/2026 |  | after 1.1.0 | Batch 1.1.7: `build.py` writes LF everywhere (no more CRLF warnings from git) |
| 01/11/2026 |  | after 1.1.0 | Batch 1.1.8: ready-to-use packages: sources in `paquets/`, `fabriquer_paquets.py`, `tests/paquets.py`, `README` section, `PROCEDURES` § 12, overview |
| 01/11/2026 |  | 1.2.0 | Release 1.2.0: `VERSION` 1.2.0; `CHANGELOG.md` (batches 1.1.1 to 1.1.8 gathered), histories; `galerie-photos.zip` and `region-simple.zip` attached to the GitHub release |
| 01/11/2026 |  | after 1.2.0 | Batch 1.2.1: chat: the arrows stay in the text while typing; packages: `README.txt` and help; `README`: packages under the demo; `tests/chat_fleches.py` |
| 01/11/2026 |  | after 1.2.0 | Batch 1.2.2: packages: `readme.html` (reordered sections, world map, help panel to review); movement pad (K key) in the help; clearer `tests/chat_fleches.py` |
| 01/11/2026 |  | after 1.2.0 | Batch 1.2.3: `tests/chat_fleches.py` waits for the real presence state and prints the full state on failure |
| 02/11/2026 |  | after 1.2.0 | Batch 1.2.4: packages: launchers and renaming for Linux and macOS (`.sh`, `.command`); `fabriquer_paquets.py` marks the launchers executable; `tests/paquets.py` tries them for real |
| 02/11/2026 |  | 1.3.0 | Release 1.3.0: `VERSION` 1.3.0; `CHANGELOG.md`; gathers batches 1.2.1 to 1.2.4 (Linux and macOS launchers for the packages); no built file changes |
| 02/11/2026 |  | after 1.3.0 | Batch 1.3.1: world map: `--map-names` option (walkers' nicknames); a number is no longer counted twice; `tests/carte_pseudos.py` |
| 02/11/2026 |  | after 1.3.0 | Batch 1.3.2: launchers: guard against the repository's source folder ("Download ZIP"); `paquets/README.txt`; test in `tests/paquets.py` |
| 02/11/2026 |  | after 1.3.0 | Batch 1.3.3: world map: nicknames protected by a key (`--map-names-key`, `#pseudos=`); visitors in the global view; `tests/carte_pseudos.py` rewritten |
| 02/11/2026 |  | after 1.3.0 | Batch 1.3.4: standalone map: several `#` in the address (`#name=...#pseudos=...`); step 5b in `tests/carte_pseudos.py` |
| 02/11/2026 |  | after 1.3.0 | Batch 1.3.5: chat: a beep for every message when the page is not focused (`soundMsg` setting); `tests/chat_bip.py` |
| 02/11/2026 |  | 1.4.0 | Release 1.4.0: `VERSION` 1.4.0; `CHANGELOG.md`; gathers the batches since 1.3.0 (nicknames on the map protected by a key, chat beep, launcher guard) |
| 02/11/2026 |  | after 1.4.0 | Batch 1.4.1: `CLAUDE.md` removed (out of date since v37); `tests/samples.py` and the manual no longer cite it |
| 03/11/2026 |  | after 1.4.0 | Batch 1.4.2 : the name of the tile under the avatar in the state panel (`tilesState().here`); `tests/tuile_ici.py` |
| 03/11/2026 |  | after 1.4.0 | Batch 1.4.3 : tiles line: one element per line (page and viewer) |
| 03/11/2026 |  | after 1.4.0 | Batch 1.4.4 : weight shown = weight received (`got`); viewer: the tiles line as soon as the handler is plugged in |
| 03/11/2026 |  | after 1.4.0 | Batch 1.4.5 : "About this region" panel (`NOM.about.<langue>.txt`, `?` key); `tests/apropos.py` |
| 03/11/2026 |  | after 1.4.0 | Batch 1.4.6 : `glb2tiles.py --compress` (`gltfpack`); `tests/compress.py` |
| 03/11/2026 |  | after 1.4.0 | Batch 1.4.7 : `title` key and `--title` active in shell mode; `--scan-sites --prune-missing`; `tests/titre.py` |
| 03/11/2026 |  | after 1.4.0 | Batch 1.4.8 : documents: manual § 38, `PROCEDURES_SIMPLES.md`, creators note |
| 03/11/2026 |  | after 1.4.0 | Batch 1.4.9 : about: clickable links, "Visitors' help" button, `?` key in the help button; documents: `GUIDE.md`, `DEVELOPPEMENT.md`, host procedures |
| 03/11/2026 |  | after 1.4.0 | Batch 1.4.10: each Python tool embeds only its own texts (`build.py`); "Loading…" in a clearly visible frame; `tests/textes_outils.py` |
| 03/11/2026 |  | after 1.4.0 | Batch 1.4.11: manual rebuilt by theme in 13 chapters (cloud session); "Visitors' help" link in the Help window; `tests/samples.py` and the code comments follow the new plan |
| 04/11/2026 |  | after 1.4.0 | Batch 1.4.12: the "About" panel no longer dims the page |
| 04/11/2026 |  | after 1.4.0 | Batch 1.4.13: each package has its map (`carte.html`, `regions.json`, `vignette.jpg` 320 x 320); the renaming script keeps the card up to date |
| 04/11/2026 |  | 1.5.0 | Release 1.5.0: `VERSION` 1.5.0; `CHANGELOG.md`; gathers the batches since 1.4.0 (compressed tiles, "About this region", package maps, new documentation) |
| 04/11/2026 |  | 1.5.1 | Release 1.5.1: `VERSION` 1.5.1; `CHANGELOG.md`; the version shown by the packages is the release version (`fabriquer_paquets.py`) |
| 04/11/2026 |  | after 1.5.1 | Batch 1.5.2: chat: a text selection in the log is no longer erased |
| 05/11/2026 |  | after 1.5.1 | Batch 1.5.3: url and image zones accept `hop://` links |
| 05/11/2026 |  | after 1.5.1 | Batch 1.5.4: signs, pictures and captions readable from both sides; "Virtual world" subtitle |
| 05/11/2026 |  | 1.6.0 | Release 1.6.0: `VERSION` 1.6.0; `CHANGELOG.md`; the `yaw` in "Position avatar", an example "Lien vers OpenSim" panel in both packages, documents up to date (manual, procedures § 13) |
| 05/11/2026 |  | after 1.6.0 | Batch 1.6.1: neutral names in the examples and tests of the public repository |
| 06/11/2026 |  | after 1.6.0 | Batch 1.6.2: procedure to extract objects from an IAR (documents) |
| 06/11/2026 |  | after 1.6.0 | Batch 1.6.3: `extraire_batiments.py` enters the repository (French and English messages, `--lang`, `--tools`, cache in the current folder, options in English) |
| 06/11/2026 |  | after 1.6.0 | Batch 1.6.4: `iar2oar.py` enters the repository (French and English messages, `--lang`, options in English) |
| 07/11/2026 |  | after 1.6.0 | Batch 1.6.5: documents for both scripts (procedures § 6, manual § 3.7 and § 3.8, README, old names § 11.11) |
| 07/11/2026 |  | after 1.6.0 | Batch 1.6.6: feedback from a macOS tester (launcher, Firefox 159.0.1): the "not tried" texts of the packages and documents are corrected |
| 07/11/2026 |  | after 1.6.0 | Batch 1.6.7: `INDEX.md` (which document to read for what); chapter 11 of the manual becomes `REFERENCE_JSON.md` (11.x numbering kept) |
| 07/11/2026 |  | after 1.6.0 | Batch 1.6.8: `README.txt` of the packages: the `carte.html` map is published with the site, you only need to adapt the thumbnail |
| 07/11/2026 |  | after 1.6.0 | Batch 1.6.10: "Made with Web_3d" mention (link to the repository) at the bottom of `carte.html` and in the `aide.html` of the packages; procedure to update a package that is already published (procedures § 10) |
| 07/11/2026 |  | after 1.6.0 | Batch 1.6.12: warning "do not unzip over a package already in place" (README, `README.txt` of the packages, procedures, release notes) |
| 07/11/2026 |  | after 1.6.0 | Batch 1.6.13: "Made with Web_3d" icon (square, bottom right, bubble and link to the repository) on the page and the map |
| 07/11/2026 |  | after 1.6.0 | Batch 1.6.14: the logo becomes the default page icon and the sample `favicon.ico` |
| 07/11/2026 |  | after 1.6.0 | Batch 1.6.15: animated GIFs animate on image zones (GIF decoder in the page) |
| 07/11/2026 |  | after 1.6.0 | Batch 1.6.16: "Copy diagnostics" gives an "Animated GIFs" line |
| 07/11/2026 |  | after 1.6.0 | Batch 1.6.17: the Status window shows the page version (`index.html`) and the configuration version |
| 07/11/2026 |  | after 1.6.0 | Batch 1.6.18: documents: "Made with Web_3d" icon (§ 7.62), GIF in the GUIDE and the packages, `favicon.ico` in the package update, manual appendix completed up to 1.6.17, dead reference in `CREATORS.md` |
| 07/11/2026 |  | after 1.6.0 | Batch 1.6.19: the old `--map-names` option has a description (fr and en); `REFERENCE_OPTIONS.md` regenerated |
| 07/11/2026 |  | 1.7.0 | Release 1.7.0: `VERSION` 1.7.0; `CHANGELOG.md`; gathers batches 1.6.1 to 1.6.19 (extraction scripts in the repository, icon and logo, animated GIFs, reorganised documentation, page version in the status) |
| 07/11/2026 |  | after 1.7.0 | Batch 1.7.1: the 1.7.0 release notes in `CHANGELOG.md` aligned with the published description |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.2: `tests/marque.py`: `--version` asked in French; five files with a mark (`extraire_batiments.py` and `iar2oar.py` added) |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.3: `tests/image_zone.py`: the `file://` message that Chromium writes itself is ignored |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.4: new `tests/readme_liens.py`: images and relative links of the READMEs and the documents |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.5: README fr and en: introduction first, glossary, version labels removed |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.6: README fr and en: features, two kinds of page, package contents, update |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.7: `diag_carte.py` enters `tools` and `dist` (fr and en messages, `--lang`, `--version`, test, README) |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.8: README fr and en: tool chain diagram and tree of a site |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.9: README fr and en: "How it works" diagram as SVG |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.10: README fr and en: site tree as a file explorer, diagram corrected |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.11: `REPRISE.md`: state on 08/11/2026 |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.12: documents up to date: `diag_carte.py` (manual § 9.22, procedures), README diagrams (`DEVELOPMENT.md` § 6), real-life tries of the extraction scripts, GIFs checked on Windows and in Firefox, overview on 08/11/2026 |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.13: tests `v37` and `v32`: wait for the condition, not for a duration |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.14: graphical launcher `web3d_gui.py` for `glb2html.py` |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.15: name of the macOS tester in the documents, with their consent |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.16: `tools_lang`: the "unknown system language" check is skipped on Windows |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.17: `web3d_gui.py`: all the tools, repeatable option, default described in the help, `--tool` |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.18: `web3d_gui.py`: Windows shortcuts (`--shortcuts`) |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.19: shortcuts with the project icon; `textes_outils` no longer blocks in a console |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.20: link to the Discord server in the READMEs |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.21: documents: graphical launcher (manual § 3.9, procedures § 11, README, overview), shortcuts picture, new Discord link |
| 08/11/2026 |  | after 1.7.0 | Batch 1.7.22: `web3d_gui.py`: File and Folder buttons on the output fields and `--convoar` |
| 08/11/2026 |  | 1.8.0 | Release 1.8.0: `VERSION` 1.8.0; `CHANGELOG.md`; gathers batches 1.7.1 to 1.7.22 (graphical launcher `web3d_gui.py` and Windows shortcuts, `diag_carte.py`, README and documents rewritten, Discord link) |
| 08/11/2026 |  | after 1.8.0 | Batch 1.8.1: `tests/gui.py`: a single Tk window (no more Tcl message under Windows) |
| 08/11/2026 |  | after 1.8.0 | Batch 1.8.2: graphical launcher: label "Equivalent command (for information)" |
| 08/11/2026 |  | after 1.8.0 | Batch 1.8.3: `REPRISE.md` lightened (appendix `REPRISE_ARCHIVE.md`) |
| 08/11/2026 |  | after 1.8.0 | Batch 1.8.4: `REPRISE.md`: rule 25 is already up to date |
| 10/11/2026 |  | after 1.8.0 | Batch 1.8.5: "Walk (P)" button that blinks in global view; Discord link in the help window (manual § 7.63, § 7.64) |
| 10/11/2026 |  | after 1.8.0 | Batch 1.8.6: `#spawn=` link on a tiled region: no black background while loading (manual § 8.6) |
| 10/11/2026 |  | after 1.8.0 | Batch 1.8.7: root cleanup: `deploy/`, the mega-region study in `docs/fr/` |
| 10/11/2026 |  | after 1.8.0 | Batch 1.8.8: `REFERENCE_OPTIONS.md` in `docs/` |
| 10/11/2026 |  | after 1.8.0 | Batch 1.8.9: `build.py` regenerates `docs/REFERENCE_OPTIONS.md`; test `build_reference.py` |
| 10/11/2026 |  | after 1.8.0 | Batch 1.8.10: `build.py` and its test read the processes' output as UTF-8 under Windows |
| 10/11/2026 |  | after 1.8.0 | Batch 1.8.11: convoar supplied in `dist/convoar/`; convoar's address fixed (`dist`, not `bin`); test `convoar_dist.py` |
| 10/11/2026 |  | after 1.8.0 | Batch 1.8.12: three tests read the processes' output as UTF-8 under Windows |
| 10/11/2026 |  | after 1.8.0 | Batch 1.8.13: `correctifs_v52` no longer hangs under Windows; `console.py` shows its output on failure |
| 10/11/2026 |  | after 1.8.0 | Batch 1.8.14: `console.py` reads the server's output during the test (4 KB pipe under Windows) |
| 10/11/2026 |  | after 1.8.0 | Batch 1.8.15: `compress.py` shows gltfpack's error on failure |
| 10/11/2026 |  | after 1.8.0 | Batch 1.8.16: documents: manual § 7.63 and § 7.64, `dist/convoar/`, `deploy/`, tests under Windows (`DEVELOPMENT.md`), history |
| 10/11/2026 |  | after 1.8.0 | Batch 1.8.17: graphical launcher: basic-use examples list for every tool (`EXEMPLES`, `lire_exemple`), `gui.py` test |
| 10/11/2026 |  | after 1.8.0 | Batch 1.8.18: documents: manual § 3.9, simple procedures § 11, history |
| 10/11/2026 |  | 1.9.0 | Release 1.9.0: `VERSION` 1.9.0; `CHANGELOG.md`; gathers batches 1.8.1 to 1.8.18 (blinking Walk button, Discord link in Help, no more black screen on a tiled region, convoar supplied, launcher examples list) |
| 10/11/2026 |  | after 1.9.0 | Batch 1.9.1: `CHANGELOG.fr.md` created (the French history); `CHANGELOG.md` becomes the English version; the French documents' references updated |
| 10/11/2026 |  | after 1.9.0 | Batch 1.9.2: `CHANGELOG.md` translated into English (header, 1.9.0 section); "decided by Klaatou" removed from the 1.9.0 release entry |
| 10/11/2026 |  | after 1.9.0 | Batch 1.9.3: `CHANGELOG.md`: 1.8.0 section translated into English; "decided by Klaatou" removed from the 1.8.0 release entry |
| 10/11/2026 |  | after 1.9.0 | Batch 1.9.4: documents: convoar's PBR limitation (manual § 3, READMEs) |
| 10/11/2026 |  | after 1.9.0 | Batch 1.9.5: `CHANGELOG.md`: 1.7.0 section translated into English; "decided by Klaatou" removed from the 1.7.0 release entry |
| 10/11/2026 |  | after 1.9.0 | Batch 1.9.6: `CHANGELOG.md`: 1.6.0 section translated into English; "decided by Klaatou" removed from the 1.6.0 release entry |
| 10/11/2026 |  | after 1.9.0 | Batch 1.9.7: `CHANGELOG.md`: 1.5.1 and 1.5.0 sections translated into English; "decided by Klaatou" removed from the two release entries |
| 10/11/2026 |  | after 1.9.0 | Batch 1.9.8: `CHANGELOG.md`: 1.4.0 and 1.3.0 sections translated into English; "decided by Klaatou" removed from the two release entries |
| 10/11/2026 |  | after 1.9.0 | Batch 1.9.9: `CHANGELOG.md`: 1.2.0 and 1.1.0 sections translated into English; "decided by Klaatou" removed from the two release entries |
| 10/11/2026 |  | after 1.9.0 | Batch 1.9.10: `CHANGELOG.md`: 1.0.0 section translated into English; end of the translation (the entries before 1.0.0 stay in French) |
| 11/11/2026 |  | after 1.9.0 | Batch 1.9.11: `oar2glb.py` runs `convoar.exe` with Mono on Linux (`commande_convoar`), `tests/mono_linux.py` |
| 11/11/2026 |  | after 1.9.0 | Batch 1.9.12: `oar2glb.py` applies the OpenSim 0.9.3 PBR materials to the GLB (`pbr_appliquer`, `--no-pbr`, `--pbr-size`), `tests/pbr_oar.py` |
| 11/11/2026 |  | after 1.9.0 | Batch 1.9.13: PBR: a whole sphere has one face (`pbr_nb_faces`) |
| 11/11/2026 |  | after 1.9.0 | Batch 1.9.14: PBR: OpenSim's default material (`PBR_DEFAUT`), null UUID ignored |
| 11/11/2026 |  | after 1.9.0 | Batch 1.9.15: viewer: "Sea height" slider in Settings (`cfg.seaM`, `seaShift`), `tests/mer_hauteur.py` |
| 11/11/2026 |  | after 1.9.0 | Batch 1.9.16: documents: manual § 3.10, § 3.11 and § 9.19, guide, README, simple procedures, index, history |
| 11/11/2026 |  | after 1.9.0 | Batch 1.9.17: the graphical launcher opens `oar2glb` without a console (`Tee`, `lire_parser`), PBR example |
| 11/11/2026 |  | after 1.9.0 | Batch 1.9.18: PBR picture of the README (`docs/images/pbr.jpg`) and credit of the sandbox's grid; two stand-alone scripts kept out of the repository |
| 11/11/2026 |  | after 1.9.0 | Batch 1.9.19: credit "Thanks to its owner, Vlad" (README, manual), `tests/tout.py` (the whole suite in one command) |
| 11/11/2026 |  | after 1.9.0 | Batch 1.9.20: `tests/tout.py` runs each test in the same environment as a direct run |
| 11/11/2026 |  | after 1.9.0 | Batch 1.9.21: Windows: `oar2glb.py` accepts a `.py` convoar and no longer prints a trace at its pause; tests `marque`, `v48`, `mono_linux` |
| 11/11/2026 |  | after 1.9.0 | Batch 1.9.22: tests: `oar2glb` re-encodes in a child interpreter (Windows); `tout.py` shows the last traceback |
| 11/11/2026 |  | after 1.9.0 | Batch 1.9.23: tests: `tout.py` restores the UTF-8 environment (correction of batch 1.9.20); the tests' presence servers no longer block on a full pipe (`tests/vider_tube.py`) |
| 12/11/2026 |  | 1.10.0 | Release 1.10.0: `VERSION` 1.10.0; `CHANGELOG.md`; gathers batches 1.9.1 to 1.9.23 (OpenSim 0.9.3 PBR materials, conversion on Linux with Mono, "Sea height" slider, graphical launcher fixed, `tests/tout.py`) |
| 12/11/2026 |  | after 1.10.0 | Batch 1.10.1: documents: Firefox tried by Klaatou with the regions and the maps (overview, manual) |
| 12/11/2026 |  | after 1.10.0 | Batch 1.10.2: tools: `errors="replace"` on the output streams of `glb2html`, `oar2glb`, `diag_carte` and the presence server (output redirected in cp1252); `tests/sortie_cp1252.py` |
| 12/11/2026 |  | after 1.10.0 | Batch 1.10.3: launcher: window icon, `glb-stats` in the list; `glb2tiles` and `oar2glb`: no more pause after `--help`; `tests/aide_sans_pause.py` |
| 12/11/2026 |  | after 1.10.0 | Batch 1.10.4: Python 3.14: `glb2html` opens again (`metavar` removed from `--sea` and `--anim`); the launcher shows the function of the tool; `tests/python_recent.py` |
| 12/11/2026 |  | after 1.10.0 | Batch 1.10.5: map: remembered "Names key" field and key status line (a refused key is no longer sent again); `tests/carte_pseudos.py` |
| 12/11/2026 |  | after 1.10.0 | Batch 1.10.6: map: the names key becomes discreet (folded block at the bottom of the page); `tests/carte_pseudos.py` |

## Useful commands

- See the history: `git log --oneline --decorate`
- See what changed in a version: `git show v16 --stat`
- Get the sources of a version: `git switch --detach v14` (then `git switch main` to go back)
- Compare two versions: `git diff v16 v17 --stat`
