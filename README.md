# web_3d

English | [Français](README.fr.md)

**web_3d** turns a region of an **OpenSim** virtual world (an **OAR** backup) into a web page that visitors can walk around, with nothing to install on their side. The OAR is converted to a **glTF** model (`.glb`), then displayed with **three.js** in a walkable web page: avatar, collisions, real-time visitors, chat, zones and portals, and a map of worlds. The interface of the page, of the viewer and of the Python tools is available in **English and French** (see "Language" below).

The manuals are in English in `docs/en/` (`MANUAL.md`, `PROCEDURES.md`, `HISTORY.md`) and in French in `docs/fr/`. All the options of every tool, in English and in French, are in [`REFERENCE_OPTIONS.md`](REFERENCE_OPTIONS.md); `python glb2html.py --lang en --help` (and the same for the other tools) prints them in English.

## Files built

| Built file | Role |
|---|---|
| `glb-viewer.html` | Settings and export page: load a `.glb` (or, since v32, the folder of a tiled region), adjust the sea, the hole, the camera, walking, the zones and the region card, then export (for a tiled region: zones and command line only). |
| `glb2html.py` | The same job on the command line (offline, no browser). Single page, modular page or shared shell, tiled regions, `--update` to update a published region. |
| `presence_server.py` | WebSocket server for presence, chat, moderation and visitor counters. |
| `oar2glb.py` | Converts an OpenSim backup (`.oar`) to `.glb` (convoar + repair); `--terrain-only` adds the full terrain of regions over 256 m to an existing GLB. |
| `glb2tiles.py` (+ `glb-stats.py` beside it) | Splits a huge GLB into self-contained tiles (`X.tiles/*.glb` + `X.tiles.json`) and builds a light overview `X.overview.glb`; `--analyse` measures and recommends without writing anything; `--exclude` drops catalogue "delivery boxes". |

## Build

```
python build.py
```

The result is in `dist/`. On first run three.js r160 is downloaded into `.cache/` (or use `python build.py --vendor FOLDER` with an npm `three` package already unpacked). The files of `dist/` are not versioned: publish them in the repository "Releases". The build embeds the language files (`src/i18n/*.json`) in the pages and in each Python tool, so every tool in `dist/` is a standalone file.

## Use

1. Open `dist/glb-viewer.html`, load the `.glb`, adjust, then "Save to a file" (remembered settings): you get `<name>.reglages.json`.
2. Generate the page with the same settings (one line):

```
python glb2html.py "Region-final.glb" --settings --register regions.json --map-page map.html -o "Region.html"
```

3. Start the presence server: `python presence_server.py --log presence.log`.

## Modular mode and shared shell

`--modular` writes `Region.html` (a shell, identical for every region), `Region.glb`, `Region.config.json`, `Region.zones.json` and `lib/three-0.160.0/`. The folder must be served over http/https (local test: `python -m http.server`). With `--shared-shell`, one shell (`index.html` by default) and one `lib/` serve several regions of the same folder, opened at `index.html?region=NAME`. NAME must be a single file name: addresses, paths, an empty name or a name starting with a dot are refused without any network request.

```
python glb2html.py "Ankh.glb" --settings --shared-shell --register regions.json -o "Ankh.html"
```

## Tiled regions

For a huge model, `glb2tiles.py` writes the tiles, and `glb2html.py --tiles X.tiles.json -o X.html --shared-shell` builds the page: the tiles around the avatar are loaded and unloaded as it walks, a light overview is always shown, and zones can be linked to objects of the tiles (v32).

## Map of worlds

`regions.json` is the map: a list of regions (name, address, X, Y, arrival point, room, presence server, thumbnail). `--register` adds or updates the region being generated; `--map-page` writes a web page of the map with one link per region; `--map-url a.json,b.json` merges the maps of several owners each time the page opens.

## What is new in v37 (details: `docs/en/MANUAL.md` § 22)

- **Page**: run indicator ("on foot · running"), **compass** at the top (`--compass`, `--north`), portal marker (cone) with a **constant size on screen** and the distance in its tooltip (`--zone-info-dist`: 150 m by default, up to 500), better placed occupied arrival turned toward the occupant, a cited nickname that **blinks until your first action**, **resizable** Help and Information windows, **O** key for Settings, address parameters separated by `&` or `#`.
- **Chat**: 200-message history (`--history`), `--history-file` and `--history-days` on the server, scrollable panel, "Older messages", unread count in the tab title, "N messages mention you".
- **Shell**: default region (`default.json`, `--default`, fallback to `regions.json`), `--lib-url` (`lib` folder elsewhere), regions in **sub-folders** (`?region=a/b/name`).

## Walking: main keys (v36)

| Key | Effect |
|---|---|
| **F** or **P** | enter / leave the walk (in the viewer P places a zone: leave with **F**, **Shift+P** or the button) |
| **E** or click | trigger the nearby zone |
| **Home**, the fly button, or **Page Up** held > 0.4 s | take off / land; **Page Up** or **Space** held = climb, **Page Down** or **C** = descend |
| **Space** / short **Page Up** | jump |
| **T** | show or hide the portal markers (cones; `--no-zone-cone` removes them at build time) |
| **H** / **I** | help / information windows |
| **M** | first / third person while walking, map of worlds otherwise |

The keyboard layout (setting "Keyboard": Auto, AZERTY or QWERTY) only changes the letters shown in the help; the physical keys stay the same. The full table is in `docs/en/MANUAL.md` § 2.

## Language

- **Page and viewer**: setting "Language / Language" (Auto = the first language of the browser that is available, otherwise English); `#lang=en` or `#lang=fr` in the address overrides it. Texts you type yourself (zone names, signs, nicknames) are never translated.
- **Python tools**: `--lang fr|en|auto` (default `auto`), otherwise the `WEB3D_LANG` environment variable, otherwise the system language, otherwise English. `--lang` wins over `WEB3D_LANG`. Option names and the presence server moderation commands (`liste`, `ejecter`, `bannir`, `bans`, `debannir`, `aide`) are not translated.
- **Adding a language**: copy `src/i18n/en.json` to `src/i18n/<code>.json`, translate the values (never the keys), run `python build.py`. A missing key falls back to English, then French, then the key itself. `python tests/i18n.py` checks the files.

## Develop

See `CLAUDE.md` (architecture, decisions, roadmap, in French) and `docs/en/HISTORY.md`. Tests: `python build.py`, then `tests/smoke.py`, `modulaire.py`, `portail_interne.py`, `tuiles.py`, `v23.py` to `v37.py`, `v37_chat.py`, `v37_region.py`, `v36_lang.py`, `v36_viewer_lang.py`, `i18n.py`, `tools_lang.py`, `doc_options.py`, `glb2tiles.py`, `oar2glb.py`, `terrain.py` (browser tests need Playwright and Chromium; set `THREE_DIR` and `CHROMIUM`).

## Security

Never commit: Home Assistant addresses (`zones*.json`), `*.reglages.json`, `presence_identities.json`, `presence_bans.json`, logs. The `.gitignore` excludes them. `--profile public` removes the private zones from published pages.

## License

MIT License (see the `LICENSE` file). three.js (MIT) and the embedded decoders: see `THIRD-PARTY.md`.
