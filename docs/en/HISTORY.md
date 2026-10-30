# Finding each version

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

## Useful commands

- See the history: `git log --oneline --decorate`
- See what changed in a version: `git show v16 --stat`
- Get the sources of a version: `git switch --detach v14` (then `git switch main` to go back)
- Compare two versions: `git diff v16 v17 --stat`
