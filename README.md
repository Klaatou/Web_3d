# web_3d

English | [Français](README.fr.md)

**web_3d** turns a region of an **OpenSim** virtual world (an **OAR** backup) into a web page that visitors can walk around, with nothing to install on their side. The OAR is converted to a **glTF** model (`.glb`), then displayed with **three.js** in a walkable web page: avatar, collisions, real-time visitors, chat, zones and portals, and a world map. The interface of the page, of the viewer and of the Python tools is available in **English and French** (see "Language" below).

The manuals are in English in `docs/en/` (`MANUAL.md`, `PROCEDURES.md`, `HISTORY.md`) and in French in `docs/fr/`. All the options of every tool, in English and in French, are in [`REFERENCE_OPTIONS.md`](REFERENCE_OPTIONS.md); `python glb2html.py --help` (and the same for the other tools) prints them in the tools' language (see "Language" below).

## Files built

| Built file | Role |
|---|---|
| `glb-viewer.html` | Settings and export page: load a `.glb` (or, since v32, the folder of a tiled region), adjust the sea, the hole, the camera, walking, the zones and the region card, then export (for a tiled region: zones and command line only). |
| `glb2html.py` | The same job on the command line (offline, no browser): single page, modular page or shared shell, tiled regions, `--update` to update a published region, `--scan-sites` for the map of a whole site. |
| `index.html` | The shared shell, ready to copy to the root of a site (v45). |
| `carte.html` | The world map page, identical for every site: it reads the `regions.json` next to it (v47). |
| `presence_server.py` | WebSocket server for presence, chat, moderation, visitor counters and the visit log. |
| `oar2glb.py` | Converts an OpenSim backup (`.oar`) to `.glb` (convoar + repair); `--terrain-only` adds the full terrain of regions over 256 m to an existing GLB. |
| `glb2tiles.py` (+ `glb-stats.py` beside it) | Splits a huge GLB into self-contained tiles (`X.tiles/*.glb` + `X.tiles.json`) and builds a light overview `X.overview.glb`; `--analyse` measures and recommends without writing anything; `--exclude` drops catalogue "delivery boxes". |

## Build

```
python build.py
```

The result is in `dist/`. On first run three.js r160 is downloaded into `.cache/` (or use `python build.py --vendor DOSSIER` with an npm `three` package already unpacked). The files of `dist/` are not versioned. The build embeds the language files (`src/i18n/*.json`) in the pages and in each Python tool, so every tool in `dist/` is a standalone file.

## Use

1. Open `dist/glb-viewer.html`, load the `.glb`, adjust, then "Save to a file" (remembered settings): you get `<nom>.reglages.json`.
2. Generate the page with the same settings (one line):

```
python glb2html.py "Region-final.glb" --settings --shared-shell --register regions.json -o "Region.html"
```

3. Start the presence server: `python presence_server.py --log presence.log`.

The full steps (OAR to page, tiled region, update, zones, public presence server, map) are in `PROCEDURES.md`.

## A site: one shell, one folder per region

Recommended layout (manual § 29.8): at the root of the site, a single shell `index.html` (copy of `dist/index.html`), the `lib/` folder, `regions.json` and `carte.html` (copy of `dist/carte.html`); then one folder per region with its `NOM.glb` (or its tiles), `NOM.config.json` and `NOM.zones.json`. A region opens at `index.html?region=dossier/NOM`. The site must be served over http/https (local test: `python -m http.server`).

- Update a region after a new version: `python glb2html.py --update -o "SITE/dossier/NOM.html" --shared-shell "SITE/index.html"` (the path of the root shell avoids writing a useless shell into the region's folder).
- Update the map of the whole site: `python glb2html.py --scan-sites SITE --dry-run`, then without `--dry-run` (v49, manual § 32).

## Modular mode and shared shell

`--modular` writes `Region.html` (a shell, identical for every region: it derives its files from its own name), `Region.glb`, `Region.config.json` (settings, read again on every F5), `Region.zones.json` (zones, read again on every F5) and `lib/three-0.160.0/`. With `--shared-shell`, one shell and one `lib/` serve several regions: `-o` names the region, and the shell and `lib/` are only written when missing. NAME must be a file name or a path of sub-folders (`a/b/nom`): addresses, `..`, an empty name or a name starting with a dot are refused without any network request.

`--config-only` rewrites only the config, `--zones-only` only the zones. The viewer exports the same structure as a `.zip`, next to "Export standalone HTML" (a single page that opens from disk). Details: manual § 16, JSON file reference: § 27.

## Tiled regions

For a huge model, `glb2tiles.py` writes the tiles, and `glb2html.py --tiles X.tiles.json -o X.html --shared-shell` builds the page: the tiles near the avatar are loaded and unloaded while walking, a light overview stays visible, and zones can be linked to objects of the tiles. Details: manual § 17.

## World map

`regions.json` is the map: a list of cards (name, address, X, Y, arrival point, room, presence server, thumbnail), or, since v47, an object `{"showUrl": ..., "regions": [...]}` with a header. It is fed in three ways, which all keep the header and the shape of the file: `--register` (the region being generated), `--scan-sites` (every region of a site, with their thumbnails) and the viewer's "Import / Export regions.json" buttons (v50). `carte.html` reads it again each time it opens; `--map-page` writes instead a standalone page that contains the list; `--map-url a.json,b.json` merges the maps of several owners. Each tile shows the number of visitors. Details: manual § 27.6, § 30, § 32 and § 33.

## The page

- **Walking**: avatar, collisions, running, jumping, flying, three views (first person, third person, free camera), compass, arrival points and portals, teleport through the Arrivals window (L) or by double-click.
- **Windows**: Help (H), Information (I), Arrivals (L), Settings (O), movable and remembered by the browser (v41); "Copy diagnostics" button (v39); "Visit log…" when the page has a presence server (v48).
- **On-screen controls** (v46): status line, 3 x 3 arrows (K key), touch mode for phones and tablets.
- **Light rendering** (v42): resolution, frames per second, overview only, tile radius, anti-aliasing (`--light`).
- **Presence and chat**: real-time visitors, avatar colour, chat with history, cited nickname; the page says why the connection closed (v45).

## Main keys

| Key | Effect |
|---|---|
| **F** or **P** | enter / leave the walk |
| **WASD** or **ZQSD**, arrow keys | move; **Shift** or double-tap: run |
| **Space** | jump; held while flying: go up |
| **Home**, the fly button, or **Page Up** held on the ground | take off / land; **Page Down** or **C**: go down |
| **E** or click | trigger the nearby zone (signs and portals) |
| **V** / **M** | change view / first or third person (outside the walk: world map); **Ctrl+M**: world map everywhere |
| **R** | back to the arrival point (global view: center on the arrival point) |
| **H**, **I**, **L**, **O** | Help, Information, Arrivals, Settings windows |
| **K** | on-screen arrows |
| **T** | portal markers (cones) |
| **G** | grab the mouse again after **Esc** |
| **Enter** | write in the chat |

The "Keyboard" setting (Auto, AZERTY or QWERTY) only changes the letters shown in the help; the physical keys stay the same. Full table: manual § 2 and § 20.2.

## Presence server

Positions, chat (history `--history-file`), moderation from its console (`liste`, `ejecter`, `bannir`, `bans`, `debannir`, `rooms`, `visits-key`, `creators`, `aide`; English aliases `list`, `kick`, `ban`, `unban`, `help`), visitor counters for the map, a visit log without IP addresses (`--visits`, v48) that the creator reads with `#visits` and their key, hosting of other creators (`--creators`, v51: declared pages, rooms reserved by a prefix, manual § 34). Making it public without showing its IP address: procedures § 11. Details: manual § 31.

## Language

- **Page and viewer**: setting "Language / Langue" (Auto = the first language of the browser that is available, otherwise English); `#lang=en` or `#lang=fr` in the address overrides it. Texts you type yourself (zone names, signs, nicknames) are never translated.
- **Python tools**: `--lang fr|en|auto` (default `auto`), otherwise the `WEB3D_LANG` environment variable, otherwise the system language, otherwise English. `--lang` wins over `WEB3D_LANG`. Option names and the presence server console commands are not translated.
- **Adding a language**: copy `src/i18n/en.json` to `src/i18n/<code>.json`, translate the values (never the keys), run `python build.py`. A missing key falls back to English, then French, then the key itself. `python tests/i18n.py` checks the files.

## Develop

`REPRISE.md` (at the root, in French) gives the state of the repository, the decisions and what is left to do; `CHANGELOG.md` and `HISTORY.md` the details of each version. Tests: `python build.py`, then the scripts of `tests/`: `smoke.py`, `i18n.py`, `samples.py`, `doc_options.py`, `tools_lang.py`, `modulaire.py`, `tuiles.py`, `glb2tiles.py`, `oar2glb.py`, `terrain.py` and one file per version (`v23.py` to `v52.py`). Browser tests need Playwright and Chromium; variables `THREE_DIR` (npm `three` package, offline) and `CHROMIUM` (executable).

## Security

Never commit: Home Assistant addresses (`zones*.json`), `*.reglages.json`, `regions.json`, `presence_identities.json`, `presence_bans.json`, logs, the visit log, `presence_visits_keys.json` and `presence_creators.json`. The `.gitignore` excludes the usual ones. `--profile public` removes the private zones from published pages.

## License

MIT License (see the `LICENSE` file). three.js (MIT) and the embedded decoders: see `THIRD-PARTY.md`.
