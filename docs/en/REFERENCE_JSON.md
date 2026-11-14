# JSON file reference (v43)

This document describes **every JSON file of the project, field by field**, the way `opensim.sample.ini` and `robust.sample.ini` do for OpenSim. It used to be chapter 11 of the manual (`MANUAL.md`); **the numbering 11.1 to 11.12 is kept**, so that the "§ 11.x" references written elsewhere stay valid. The references "§ N" where N is not 11 point to `MANUAL.md`.

A JSON file does not accept comments. The explanations are therefore here, and the samples are separate, in the `docs/samples/` folder: they are **real, complete and valid files**. To use one, copy the sample, rename it and change the values. The `tests/samples.py` test checks that each sample is accepted by the real code that reads that file: the page, the viewer, the tools and the presence server. The samples therefore stay correct when the code changes.

## 11.1 The files and their samples

| Real file                                        | Sample in `docs/samples/`          | Written by                                  | Read by                                             |
| ------------------------------------------------ | ---------------------------------- | ------------------------------------------- | --------------------------------------------------- |
| `NOM.config.json`                                | `region.config.sample.json`        | `glb2html.py`                               | the page                                            |
| `NOM.zones.json`                                 | `region.zones.sample.json`         | the viewer, `glb2html.py --zones`, by hand  | the page, the viewer, `glb2html.py --zones`         |
| `default.json`                                   | `default.sample.json`              | `glb2html.py --default`                     | the shell                                           |
| `regions.json`                                   | `regions.sample.json`              | `glb2html.py --register`, the viewer        | the page (`mapUrl`), the shell, `glb2html.py --map` |
| `NOM.tiles.json`                                 | `region.tiles.sample.json`         | `glb2tiles.py`                              | the page, the viewer, `glb2html.py --tiles`         |
| `NOM.reglages.json`                              | `region.reglages.sample.json`      | the viewer ("Save to a file")               | the viewer, `glb2html.py --settings`                |
| `disposition.json`                               | `disposition.sample.json`          | the page (Settings, "Save")                 | the page (Settings, "Load")                         |
| `presence_identities.json`                       | `presence_identities.sample.json`  | `presence_server.py`                        | `presence_server.py`                                |
| `presence_bans.json`                             | `presence_bans.sample.json`        | `presence_server.py` (`bannir` command)     | `presence_server.py`                                |
| `--history-file` file (for example `chat.jsonl`) | `chat_history.sample.jsonl`        | `presence_server.py`                        | `presence_server.py`                                |
| `--visits` file (for example `visits.jsonl`)     | `visits.sample.jsonl`              | `presence_server.py`                        | `presence_server.py`                                |
| `presence_visits_keys.json`                      | `presence_visits_keys.sample.json` | `presence_server.py` (`visits-key` command) | `presence_server.py`                                |
| `presence_creators.json`                         | `presence_creators.sample.json`    | by hand (§ 10.10)                              | `presence_server.py` (`--creators`)                 |

Two other files have **exactly the format** of `NOM.zones.json`:

- `zones.json`, the zones shared by the regions of a folder, read when a region has no `NOM.zones.json` of its own (§ 11.12);
- `NOM.zones.bak.json`, the backup copy the viewer leaves when it saves the zones in the region's folder.

In the samples, the region is called `Region`. For a region "Atoll", rename `region.config.sample.json` to `Atoll.config.json` and replace `Region` with `Atoll` in the values that contain it (`room`, `tiles`, the addresses). The addresses in the samples are written `ADRESSE`: put your own there.

## 11.2 How to read the tables

- **Text**: a value in quotes, for example `"door, porte"`.
- **Number**: without quotes, with a dot for decimals, for example `18.5`.
- **Yes / no**: `true` (yes) or `false` (no), without quotes.
- **List**: values in square brackets, for example `[392, 68, -373]` for an x, y, z position.
- **Object**: fields in curly braces, like a card within the card.
- **Color**: a whole number, which is the usual color code written in base 10. The sea blue `#3A9AD9` is written `3840729`. To convert in PowerShell, typing `0x3A9AD9` gives `3840729`, and `'{0:X6}' -f 3840729` gives back `3A9AD9`. The `--sea-color` and `--sky-color` options accept the code `3a9ad9` directly.
- **Option**: the `glb2html.py` option that writes this field. A dash "—" means that no option sets it.

Positions are in meters, in the page's frame: x towards the east, y upwards, z towards the south (north is the -z direction). Angles (`yaw`) are in radians: 1.57 is a quarter turn, 3.14 a half turn.

## 11.3 `NOM.config.json`: the page settings

`glb2html.py` writes it; the page reads it again at each opening, so **F5 is enough** after a change. The preferred way to change it is `glb2html.py --update -o NOM.html --shared-shell` followed by the wanted options: only the fields of the given options change, the rest is kept, including a field added by hand. It can also be edited by hand; a syntax error (forgotten comma, missing quote) then prevents the page from opening.

**Sea and sky**

| Field            | Type         | Default   | What it does                                                                                       | Option                 |
| ---------------- | ------------ | --------- | -------------------------------------------------------------------------------------------------- | ---------------------- |
| `sea`            | yes / no     | `true`    | shows the sea                                                                                      | `--sea`, `--no-sea`    |
| `seaY`           | number       | `-50`     | height of the sea in meters (from -150 to 60)                                                      | `--sea-y`              |
| `seaM`           | number       | (absent)  | height of the sea in metres of the region's frame, like the Settings slider (from -50 to 250); written by `glb2html.py` from the water level of the GLB or of the OAR (1.10.26); wins over `seaY` | `--sea-m`, `--water-from` |
| `seaColor`       | color        | `3840729` | color of the sea (`#3A9AD9`)                                                                       | `--sea-color`          |
| `skyColor`       | color        | `8900331` | color of the sky and of the fog (`#87CEEB`)                                                        | `--sky-color`          |
| `anim`           | yes / no     | `false`   | animated waves; otherwise the sea is still                                                         | `--anim`, `--no-anim`  |
| `wave`           | number       | `0.5`     | height of the waves (from 0 to 10)                                                                 | `--wave`               |
| `seaSegments`    | whole number | `400`     | fineness of the sea surface (from 8 to 1000); only matters with animated waves                     | `--sea-segments`       |
| `seaSize`        | number       | `4000`    | width of the sea in meters                                                                         | —                      |
| `hole`           | number       | `180`     | radius in meters of the **calm area** around the island, where the waves fade out (from 30 to 600) | `--hole`               |
| `holeFade`       | number       | `60`      | width of the transition between the calm area and the waves                                        | `--hole-fade`          |
| `holeX`, `holeZ` | number       | `0`       | center of the calm area                                                                            | `--hole-x`, `--hole-z` |

**Region and starting camera**

| Field            | Type              | Default        | What it does                                                                                                 | Option                      |
| ---------------- | ----------------- | -------------- | ------------------------------------------------------------------------------------------------------------ | --------------------------- |
| `rotate`         | whole number      | `0`            | rotation of the region: 0, 90, 180 or 270 degrees                                                            | `--rotate`                  |
| `target`         | list of 3 numbers | `[0, 15, 0]`   | point the camera looks at on opening                                                                         | `--target`                  |
| `targetExplicit` | yes / no          | `false`        | `true` when `--target` was given: the page keeps this framing instead of starting from the `default` arrival | `--target`                  |
| `camDir`         | list of 3 numbers | `[0, 0.25, 1]` | direction the camera looks from                                                                              | `--cam-dir`                 |
| `zoom`           | number            | `1`            | camera distance (1 = automatic framing, 2 = twice as far)                                                    | `--zoom`                    |
| `compass`        | yes / no          | `true`         | compass at the top of the page                                                                               | `--compass`, `--no-compass` |
| `northDeg`       | number            | `0`            | compass offset in degrees, for a model that does not come from OpenSim                                       | `--north`                   |

**Display**

| Field           | Type     | Default             | What it does                                                                                                                                | Option                    |
| --------------- | -------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| `retina`        | yes / no | `false`             | high resolution (sharper, about four times heavier)                                                                                         | `--retina`, `--no-retina` |
| `light`         | yes / no | `false`             | the page opens in light rendering as long as the visitor has chosen nothing (§ 7.45)                                                          | `--light`, `--no-light`   |
| `credit` | yes / no | (absent: yes) | `false` removes the "Made with Web_3d" icon (§ 7.62); the key is only written in that case | `--credit`, `--no-credit` |
| `foliageCutout` | number   | `0.12`              | transparency threshold of foliage (from 0 to 0.5): higher, the leaf edges are cut more                                                      | `--foliage-cutout`        |
| `solidMaterials` | text     | `""`                | materials drawn solid (§ 6.13): names or pieces of names separated by commas, `=name` for an exact name; empty = nothing changes            | `--solid-materials`       |
| `names`         | yes / no | `false`             | shows the name of the building (root object) and of the element aimed at (§ 7.61)                                                                                                       | `--names`, `--no-names`   |
| `panel`         | yes / no | `true`              | Settings button for visitors                                                                                                                | `--panel`, `--no-panel`   |
| `libUrl`        | text     | `""`                | folder or address of `lib` (three.js) when it is not next to the page; `--update` aligns it with the `const LIB` line of the shell (§ 6.4) | `--lib-url`               |
| `version`       | text     | version of the tool | version of `glb2html.py` that wrote the file; `--update` replaces it; `fabriquer_paquets.py` writes the release version into the packages                                  | —                         |

**Walk mode**

| Field        | Type     | Default         | What it does                                                                                                                           | Option                |
| ------------ | -------- | --------------- | -------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| `walk`       | yes / no | `true`          | walk mode (F key)                                                                                                                      | `--walk`, `--no-walk` |
| `fly`        | yes / no | `true`          | flight in walk mode                                                                                                                    | `--fly`, `--no-fly`   |
| `eyeHeight`  | number   | `1.7`           | eye height in meters                                                                                                                   | `--eye-height`        |
| `walkSpeed`  | number   | `3.5`           | walking speed in meters per second (running: 2.2 times more)                                                                           | `--walk-speed`        |
| `walkIgnore` | text     | `"door, porte"` | objects you walk through, separated by commas: `door` = any name starting with this word, `=mesh_346_5` = this exact name, `""` = none | `--walk-ignore`       |

**Visitors and chat**

| Field         | Type     | Default                           | What it does                                                                                       | Option                        |
| ------------- | -------- | --------------------------------- | -------------------------------------------------------------------------------------------------- | ----------------------------- |
| `presenceUrl` | text     | `""`                              | address of the presence server (`ws://...` or `wss://...`); empty = alone, without avatars or chat | `--presence-url`              |
| `room`        | text     | name of the page                  | presence room: visitors of the same room see each other                                            | `--room`                      |
| `title`       | text     | absent (the title is the room)    | title of the browser tab (60 characters at most), optional, shell only                             | `--title`                     |
| `spectate`    | yes / no | `true` if `presenceUrl` is filled | see the walkers from the global view                                                               | `--spectate`, `--no-spectate` |
| `chat`        | yes / no | `true`                            | chat between visitors (a presence server is needed)                                                | `--chat`, `--no-chat`         |
| `chatFade`    | number   | `0`                               | seconds before messages and bubbles disappear; 0 = they stay                                       | `--chat-fade`                 |

**Zones**

| Field          | Type     | Default    | What it does                                                                                                     | Option                              |
| -------------- | -------- | ---------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| `profile`      | text     | `"public"` | `"public"`: private zones are not shown; `"private"`: all zones are                                              | `--profile`                         |
| `zones`        | list     | `[]`       | always empty in this file: the zones are in `NOM.zones.json`                                                     | —                                   |
| `zonesLive`    | text     | `""`       | always empty in this file (used by standalone pages, `--zones-live`)                                             | `--zones-live`                      |
| `imageExts`    | text     | `"jpg,jpeg,png,webp,gif,avif"` | extensions tried, in order, for an image name without an extension (§ 5.11); optional key, absent from the file the generator writes | —                                   |
| `mediaDir`     | text     | `"medias"` | subfolder of the images and text files of `image` zones (§ 5.11); `""` = none; optional key, absent from the file the generator writes | —                                   |
| `zoneMarker`   | text     | `"dot"`    | marker of portals and free zones: `"dot"` small disc, `"range"` ring at the zone's real radius, `"none"` nothing | `--zone-marker`                     |
| `zoneCone`     | yes / no | `true`     | small cone above the portals and the links triggered by walking into them (T key); adjustable zone by zone with the `cone` key                                                                             | `--zone-cone`, `--no-zone-cone`     |
| `showSpawns`   | yes / no | `false`    | also draws the arrivals                                                                                          | `--show-spawns`, `--no-show-spawns` |
| `zoneInfoDist` | number   | `150`      | distance in meters (from 5 to 500) up to which zones react to hovering and clicking in walk mode                 | `--zone-info-dist`                  |

**World map**

| Field    | Type | Default | What it does                                                                  | Option                |
| -------- | ---- | ------- | ----------------------------------------------------------------------------- | --------------------- |
| `map`    | list | `[]`    | map embedded in the page: same cards as `regions.json` (§ 11.6)               | `--map`, `--register` |
| `mapUrl` | text | `""`    | address(es) of `regions.json` read again at each opening, separated by commas | `--map-url`           |

**Tiled region**: these six fields only exist for a region split by `glb2tiles.py`. For a region made of a single `.glb` file, **remove** them from the sample, otherwise the page looks for tiles.

| Field              | Type         | Default   | What it does                                                     | Option                 |
| ------------------ | ------------ | --------- | ---------------------------------------------------------------- | ---------------------- |
| `tiles`            | text         | —         | name of the tile index, for example `"Region.tiles.json"`        | `--tiles`              |
| `tileRadius`       | number       | `150`     | radius in meters around the avatar within which tiles are loaded | `--tile-radius`        |
| `tileMargin`       | number       | `60`      | margin in meters beyond that radius before a tile is removed     | `--tile-margin`        |
| `tileMaxMB`        | number       | `200`     | megabytes of tiles loaded at the same time, at most              | `--tile-max-mb`        |
| `tileMaxTriangles` | whole number | `8000000` | triangles of tiles loaded at the same time, at most              | `--tile-max-triangles` |
| `tileConcurrency`  | whole number | `4`       | tile downloads at the same time                                  | `--tile-concurrency`   |

The light rendering settings chosen by a visitor (resolution, frames per second, overview only, antialiasing) are kept **by their browser**, not in this file: the page ignores `pixelScale`, `fpsMax`, `ovOnly` or `antialias` written here.

## 11.4 `NOM.zones.json`: the zones

A **list** of zones, read again at each opening of the page. Each zone has the fields below; a missing field takes its default value, and a value outside the limits is brought back within them.

There are **five kinds** of zones (`type` field): `"spawn"` (arrival), `"portal"` (portal), `"url"` (web link), `"ha"` (command) and `"image"` (picture on a wall, § 5.11). "Private", "linked to an object" and "name shown" are not kinds: they are boxes (`private`, `mesh`, `showName`) valid for all kinds.

| Field         | Type     | Default       | What it does                                                                                                                                                  |
| ------------- | -------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`          | text     | `z1`, `z2`... | short, unique name: lowercase letters, digits, `-` and `_`, 40 characters at most. The `default` arrival is the region's entry point                          |
| `type`        | text     | `"portal"`    | `"spawn"`, `"portal"`, `"url"`, `"ha"` or `"image"`                                                                                                                      |
| `label`       | text     | `""`          | name shown (tooltip, sign), 60 characters at most                                                                                                             |
| `x`, `y`, `z` | number   | `0`           | position in meters                                                                                                                                            |
| `yaw`         | number   | `0`           | orientation in radians: direction of the gaze on arrival, or front of the sign                                                                                |
| `shape`       | text     | `"ring"`      | `"ring"` (ring on the ground) or `"board"` (sign on a post)                                                                                                   |
| `trigger`     | text     | `"click"`     | portals and links (`"url"`, `hop://` included): `"click"` (click or E), `"enter"` (walking into it) or `"both"` (both). The other kinds are always `"click"`                                    |
| `radius`      | number   | `2`           | radius of the zone in meters (from 0.5 to 50)                                                                                                                 |
| `w`, `h`      | number   | `2.4`, `1.2`  | width and height of the sign in meters; for `image`: 1.2 wide by default, height 0 = from the image                                                                                                                        |
| `target`      | text     | `""`          | portal: address of the destination region, or empty for a point of the same region; link: address of the web page; command: address called; image: file name or address of the image                    |
| `link`        | text     | `""`          | image only, optional: page opened on click or E in front of the picture (an `http(s)` or `hop://` address, or a path relative to the open page, for example `galerie.html`); at most 600 characters; the key is only written when filled in (§ 5.11) |
| `spawn`       | text     | `""`          | portal: `id` of the targeted arrival (empty = `default`)                                                                                                      |
| `confirm`     | yes / no | `false`       | asks for a confirmation before acting                                                                                                                         |
| `private`     | yes / no | `false`       | private zone: absent from public pages (`public` profile)                                                                                                     |
| `showName`    | yes / no | `false`       | writes the `label` above the zone in walk mode                                                                                                                |
| `cone`        | yes / no | (absent: follows the trigger) | marker (cone) above the zone: `true` always shows it, even for an "on click" zone; `false` never shows it; absent: a cone for the portals and the links triggered by walking into them (`"enter"` or `"both"`). The T key hides all cones. No effect on an arrival (`--show-spawns`) or on a picture; the key is written only when it is `true` or `false` |
| `mesh`        | text     | `""`          | zone **linked to an object** of the model: its name, or `name#number` when several objects have that name; the object becomes clickable. Never for an arrival |

The sample contains nine zones, one for each case:

| `id`              | Kind    | What it shows                                                                                 |
| ----------------- | ------- | --------------------------------------------------------------------------------------------- |
| `default`         | arrival | entry point of the region                                                                     |
| `gallery`         | arrival | second arrival, targeted by a portal                                                          |
| `to-gallery`      | portal  | to another point of the same region (empty `target`, `spawn` = `gallery`), by walking into it |
| `to-other-region` | portal  | to another region, sign, click or walk, with confirmation                                     |
| `website`         | link    | opens a web page, sign                                                                        |
| `light-on`        | command | call to an address (for example a Home Assistant webhook), private, with confirmation         |
| `door-info`       | link    | linked to the model's `Door#2` object                                                         |
| `back-home`       | portal  | name shown above the zone (`showName`)                                                        |
| `painting-1`      | image   | picture on a wall: file `paintings/painting-1.jpg`, height from the image                     |

In a tiled region, a linked zone finds its object thanks to the `extras.ref` tag that `glb2tiles.py` writes in the objects of the tiles. This tag is in the tiles' `.glb` files, **not** in `NOM.zones.json`.

## 11.5 `default.json`: the default region

| Field    | Type | Default | What it does                                            | Option      |
| -------- | ---- | ------- | ------------------------------------------------------- | ----------- |
| `region` | text | —       | region opened when the address has no `?region=` (§ 11.12) | `--default` |

## 11.6 `regions.json`: the world map

A **list** of regions (plain form), or, since v47, an **object** with a header: `{"showUrl": false, "regions": [ ... ]}`. Both forms are read everywhere (`carte.html` map, standalone map, map opened with M, shell). A card without `name` or without `url` is ignored.

| Header field | Type    | Default | What it does                                                                                                                                                 | Option |
| ------------ | ------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------ |
| `showUrl`    | boolean | `false` | shows the address under each tile of the map page; the checkbox on the map page, once ticked or unticked by the visitor, wins (choice kept by their browser) | —      |
| `credit`     | boolean | (absent: yes) | `false` removes the "Made with Web_3d" icon from the hosted `carte.html` (§ 7.62); standalone map: `--map-page` with `--no-credit` | —      |
| `regions`    | list    | —       | the region cards (next table)                                                                                                                                | —      |

`--register` and `--scan-sites` keep the header and the shape of the file (list or object). So does the viewer since v50: "Import regions.json" accepts both shapes, "Export regions.json" gives back the imported shape with its header, and every card keeps all its fields (§ 9.13).

| Field      | Type         | Default             | What it does                                                                           | Option           |
| ---------- | ------------ | ------------------- | -------------------------------------------------------------------------------------- | ---------------- |
| `id`       | text         | taken from the name | short identifier, unique in the map                                                    | —                |
| `name`     | text         | —                   | name shown, 60 characters at most                                                      | `--region-name`  |
| `url`      | text         | —                   | address of the page: complete (`https://...`) or relative (`index.html?region=Region`) | `--region-url`   |
| `x`, `y`   | whole number | `0`                 | place on the grid, as in OpenSim (x towards the east, y towards the north)             | `--region-xy`    |
| `spawn`    | text         | `""`                | arrival used when coming from the map (empty = `default`)                              | `--region-spawn` |
| `presence` | text         | `""`                | presence server of this region, if it is not the page's (to count the visitors)        | —                |
| `room`     | text         | `""`                | presence room of this region                                                           | `--room`         |
| `thumb`    | text         | `""`                | thumbnail: embedded image (`data:image/...`) or address of an image                    | `--thumb`        |

## 11.7 `NOM.tiles.json`: the tile index

`glb2tiles.py` writes it; it is **not edited by hand**. The page only reads a few fields: `tiles` (for each tile `file`, `min`, `max`, `bytes`, `triangles`), `nodeRefs` and `overview.file`. The others are for the report.

| Field            | Type          | What it contains                                                                                                                                                                                                                                                                          |
| ---------------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `version`        | whole number  | format version (1)                                                                                                                                                                                                                                                                        |
| `generator`      | text          | tool and version that wrote the file                                                                                                                                                                                                                                                      |
| `source`         | text          | name of the split `.glb`                                                                                                                                                                                                                                                                  |
| `extent`         | object        | box of the whole region: `min` and `max`, each x, y, z                                                                                                                                                                                                                                    |
| `params`         | object        | splitting settings: `budgetMB`, `budgetTriangles`, `minCell`, `wholeWeightMB`, `wholeExtent`, `thresholdMB`, `thresholdTriangles`, `outlier` (options `--budget`, `--budget-triangles`, `--min`, `--whole-weight`, `--whole-extent`, `--threshold`, `--threshold-triangles`, `--outlier`) |
| `warnings`       | list of texts | warnings of the splitting                                                                                                                                                                                                                                                                 |
| `roots`          | object        | objects kept whole (`whole`) and spread (`split`)                                                                                                                                                                                                                                         |
| `duplication`    | number        | geometry of all tiles divided by that of the model (1 = nothing duplicated)                                                                                                                                                                                                               |
| `nodeRefs`       | number        | 1 if the objects carry `extras.ref` (linked zones possible), 0 with `--no-refs`                                                                                                                                                                                                           |
| `replacedImages` | object        | unreadable images replaced by grey: `distinct`, `occurrences`, `grey`                                                                                                                                                                                                                     |
| `waterHeight`    | number          | the OAR's water level in metres (region frame), written by `oar2glb.py` into the GLB and carried here; absent from older indexes; `glb2html.py` makes it `seaM` (1.10.26) |
| `tiles`          | list          | one card per tile (below)                                                                                                                                                                                                                                                                 |
| `excluded`       | object        | only with `--exclude`: patterns, limits, number of removed objects, triangles and bytes saved, most frequent names                                                                                                                                                                        |
| `overview`       | object        | only with the overview: `file` (the `.glb`), weight, triangles, objects kept and omitted, duration, `params` (`budgetMB`, `budgetTriangles`, `minExtent`, `maxExtent`, `resolution`, `terrainStep`)                                                                                       |

Each card of `tiles`:

| Field                         | Type              | What it contains                                 |
| ----------------------------- | ----------------- | ------------------------------------------------ |
| `file`                        | text              | path of the tile's `.glb`, relative to the index |
| `level`, `i`, `j`             | whole number      | level and place of the tile in the grid          |
| `min`, `max`                  | list of 3 numbers | box of the tile                                  |
| `instances`                   | whole number      | number of objects in the tile                    |
| `triangles`                   | whole number      | triangles of the tile                            |
| `bytes`                       | whole number      | weight of the file                               |
| `geometryBytes`, `imageBytes` | whole number      | of which geometry, of which images               |
| `replacedImages`              | whole number      | images replaced by grey in this tile             |

## 11.8 `NOM.reglages.json`: the viewer's working state

Written by the viewer's "Save to a file" button, read by "Load a file" and by `glb2html.py --settings`. Unlike `NOM.config.json`, it is **nested** (§ 11.12).

| Field            | Type         | What it contains                                                                                                              |
| ---------------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `v`              | whole number | format version: always `1`                                                                                                    |
| `file`           | text         | name of the `.glb` open in the viewer                                                                                         |
| `saved`          | text         | date and time of the save                                                                                                     |
| `cfg`            | object       | the settings: same names and same meaning as in `NOM.config.json` (§ 11.3), plus five settings specific to the viewer (below) |
| `zones`          | list         | all the zones, private ones included (format of § 11.4)                                                                       |
| `camera`         | object       | `camDir`, `target`, `zoom`: the framing chosen in the viewer                                                                  |
| `profile`        | text         | `"public"` or `"private"` ("Export profile" menu)                                                                             |
| `thisReg`        | object       | card of this region for the map: `name`, `url`, `x`, `y`, `spawn`, `thumb` (§ 11.6)                                           |
| `cmd`            | object       | fields of the command summary: `script`, `glb`, `dest`, `mapPage`                                                             |
| `targetExplicit` | yes / no     | the camera target was moved by hand                                                                                           |

The five `cfg` settings specific to the viewer: `pixelScale`, `fpsMax` and `ovOnly` (light rendering, tried in the viewer), `guide` (guide of the calm area shown in the viewer) and `ignoreViz` (objects walked through shown as wireframe). `--settings` does not take them.

## 11.9 `disposition.json`: where the windows are

Written by Settings, "Save" ("Window layout" section), read by "Load" (§ 7.44).

| Field    | Type         | What it contains                                                                                                                                                                                                                                                                                      |
| -------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app`    | text         | always `"web3d-layout"`: another file is refused                                                                                                                                                                                                                                                      |
| `v`      | whole number | format version: `1`                                                                                                                                                                                                                                                                                   |
| `layout` | object       | `wins`: for each window (`H` help, `I` information / status, `L` arrivals), `pile` (`"L"` left stack, `"R"` right stack, `"F"` free), `home` (`"L"` or `"R"`, the stack the window returns to on double-click), and for a free window `x`, `y` in pixels; `order`: order of the windows in each stack |
| `ls`     | object       | state of the windows: `glb2html_help`, `glb2html_state`, `glb2html_spawn` (`"1"` shown, `"0"` hidden), `glb2html_helpFold`, `glb2html_stateFold`, `glb2html_spawnFold` (`"1"` collapsed), `glb2html_helpW`, `glb2html_stateW`, `glb2html_spawnW` (width in pixels)                                    |

## 11.10 Presence server files

The server writes them itself; edit them by hand only with the server stopped. "Hashed" values are fingerprints: the original key or IP address cannot be recovered, which protects the visitors. The fingerprints in the samples are made up and match nobody.

**`presence_identities.json`** (`--identities` option): the reserved nicknames (the `oublier <pseudo>` console command releases one without touching the file, § 10.19).

| Field   | Type   | What it contains                                                                                                                                                                                               |
| ------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `salt`  | text   | secret "salt" drawn at random on the first start, mixed into the keys before hashing them. Changing it frees all the nicknames                                                                                 |
| `names` | object | for each simplified nickname (lowercase, without accents or spaces), the fingerprint of the browser key that owns it                                                                                           |
| `users` | object | for each fingerprint: `name` (nickname as written), `key` (simplified nickname), `first` and `last` (first and last visit, in seconds since 1970). A nickname unused for `--name-ttl-days` days (365) is freed |

**`presence_bans.json`** (`--bans` option): a list of bans.

| Field    | Type   | What it contains                                                                                                 |
| -------- | ------ | ---------------------------------------------------------------------------------------------------------------- |
| `key`    | text   | fingerprint of the banned browser's key (empty for a visitor without a key)                                      |
| `ip`     | text   | fingerprint of their IP address                                                                                  |
| `until`  | number | end of the ban in seconds since 1970; `0` = permanent. A finished ban is removed from the file at the next check |
| `name`   | text   | nickname at the time of the ban                                                                                  |
| `reason` | text   | reason given                                                                                                     |
| `added`  | number | date of the ban in seconds since 1970                                                                            |

**Chat history** (`--history-file` option): this is not a single-block JSON file, but **one message per line**, each line being a small JSON. Never an IP address.

| Field  | Type         | What it contains                                                      |
| ------ | ------------ | --------------------------------------------------------------------- |
| `n`    | whole number | number of the message                                                 |
| `t`    | whole number | time in seconds since 1970 (this is what counts for `--history-days`) |
| `d`    | text         | the same time in readable form (dd/mm/yyyy hh:mm:ss)                  |
| `room` | text         | room                                                                  |
| `name` | text         | nickname                                                              |
| `text` | text         | message                                                               |

Messages older than `--history-days` days (30 by default) are removed at startup; with `--history-days 0`, nothing is removed.

**Visit log** (`--visits` option, v48): like the history, **one visit per line**, each line being a small JSON. Never an IP address.

| Field   | Type         | What it contains                                                                                                                                  |
| ------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `room`  | text         | room                                                                                                                                              |
| `start` | whole number | arrival in seconds since 1970 (this is what counts for `--visits-days`)                                                                           |
| `dur`   | whole number | duration of the connection in seconds                                                                                                             |
| `walk`  | whole number | seconds spent walking                                                                                                                             |
| `v`     | text         | browser fingerprint (10 characters), different from the key in the `presence.log` log: used to count distinct visitors and to merge reconnections |
| `name`  | text         | walker's nickname, only with `--visits-names`                                                                                                     |

Visits older than `--visits-days` days (365 by default) are removed at startup and then every 6 hours, together with unreadable lines; with `--visits-days 0`, nothing is removed.

**`presence_visits_keys.json`** (`--visits-keys` option, v48): the visit log keys, written by the `visits-key` command.

| Field   | Type   | What it contains                                                                                                                                                                                                      |
| ------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `rooms` | object | for each room: `salt` (random salt), `hash` (SHA-256 fingerprint of the salt followed by the key in upper case, without dashes or spaces), `added` (creation, in seconds since 1970). The key itself is never written |

**`presence_creators.json`** (`--creators` option, v51): the hosted creators, written by hand and re-read without restarting the server (§ 10.10). An object `{"creators": [...]}`; for each creator:

| Field        | Type          | What it contains                                                                                                                                   |
| ------------ | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`         | text          | unique identifier: letters, digits, `-` and `_`, 32 at most                                                                                        |
| `prefix`     | text          | prefix of their rooms, without a dot; absent = `id`; `""` = the host, who keeps every room that belongs to no creator (a single entry)             |
| `origins`    | list of texts | origins of their pages (`https://alice.example`, `null` for a page opened from the disk and for the viewer, written in quotes; without quotes it is ignored with a warning); an origin belongs to one creator only |
| `maxWalkers` | integer       | walkers at most over all their rooms; `0` or absent = only the general limits                                                                      |
| `maxRooms`   | integer       | rooms open at the same time at most; `0` or absent = no limit of their own                                                                         |
| `off`        | boolean       | `true`: suspended, their new connections are refused                                                                                               |
| `note`       | text          | free note of the host, ignored by the server                                                                                                       |

## 11.11 English names since v43

So that all names are in the same language, v43 put the last French names into English: tool options, values in the JSON files and address parameters. **The old names are still accepted**: commands, files and links already written keep working. An old name is replaced by the new one when read; when a tool rewrites a file, it writes the new one. `--update` keeps a field you do not change as it is: an old `tileMaxMo` therefore stays in `NOM.config.json`, and the page still reads it.

| Where                                  | Old name                                                           | New name                                                       |
| -------------------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------- |
| `glb2html.py`                          | `--maj`                                                            | `--update`                                                     |
| `glb2html.py`                          | `--tile-max-mo`, `--tile-max-tri`                                  | `--tile-max-mb`, `--tile-max-triangles`                        |
| `glb2html.py`                          | `--zone-marker discret`, `portee`, `aucun`                         | `--zone-marker dot`, `range`, `none`                           |
| `glb2html.py`                          | `--profile perso`                                                  | `--profile private`                                            |
| `glb2tiles.py`                         | `--budget-tri`, `--ov-budget-tri`                                  | `--budget-triangles`, `--ov-budget-triangles`                  |
| `glb2tiles.py`                         | `--entier-poids`, `--entier-etendue`                               | `--whole-weight`, `--whole-extent`                             |
| `glb2tiles.py`                         | `--seuil`, `--seuil-tri`, `--aberrant`                             | `--threshold`, `--threshold-triangles`, `--outlier`            |
| `glb2tiles.py`                         | `--exclure`, `--exclure-max-tri`, `--exclure-max-meshes`           | `--exclude`, `--exclude-max-triangles`, `--exclude-max-meshes` |
| `glb2tiles.py`                         | `--sans-references`, `--sans-vue-ensemble`, `--vue-ensemble-seule` | `--no-refs`, `--no-overview`, `--overview-only`                |
| `glb2tiles.py`                         | `--ov-seuil`, `--ov-seuil-max`, `--ov-terrain-pas`                 | `--ov-threshold`, `--ov-threshold-max`, `--ov-terrain-step`    |
| `glb2tiles.py`                         | `--bloc`, `--forcer`, `--sortie`                                   | `--block`, `--force`, `--output`                               |
| `oar2glb.py`                           | `--reperes`, `--terrain-seul`, `--sortie`                          | `--markers`, `--terrain-only`, `--output`                      |
| `oar2glb.py`                           | `--terrain oui`, `--terrain non`                                   | `--terrain yes`, `--terrain no`                                |
| `glb-stats.py`                         | `--bloc`, `--sortie`                                               | `--block`, `--output`                                          |
| `extraire_batiments.py` (1.6.3)        | `--filtre`, `--min-parties`, `--boite`                             | `--filter`, `--min-parts`, `--box`                             |
| `extraire_batiments.py` (1.6.3)        | `--voisin`, `--rayon`, `--rayon-nom`, `--parties-voisin`           | `--neighbor`, `--radius`, `--name-radius`, `--neighbor-parts`  |
| `extraire_batiments.py` (1.6.3)        | `--groupe`, `--nom`, `--tous`, `--exclure`, `--limite`             | `--group`, `--name`, `--all`, `--exclude`, `--limit`           |
| `extraire_batiments.py` (1.6.3)        | `--simuler`, `--oui`, `--fusionner`, `--sol`                       | `--dry-run`, `--yes`, `--merge`, `--ground`                    |
| `extraire_batiments.py` (1.6.3)        | `--sortie`, `--sans-cache`, `--vider-cache`                        | `--output`, `--no-cache`, `--clear-cache`                      |
| `iar2oar.py` (1.6.4)                   | `--liste`, `--filtre`, `--sans-imbriques`, `--marge`, `--sortie`   | `--list`, `--filter`, `--no-nested`, `--margin`, `--output`    |
| `gen_reference.py` (v44)               | `--outils`, `--sortie`, `--verifier`                               | `--tools`, `--output`, `--check`                               |
| `verif_trad.py` (v44)                  | `--glossaire`                                                      | `--glossary`                                                   |
| `NOM.config.json`                      | `tileMaxMo`, `tileMaxTri`                                          | `tileMaxMB`, `tileMaxTriangles`                                |
| `NOM.config.json`, `NOM.reglages.json` | `zoneMarker`: `discret`, `portee`, `aucun`                         | `dot`, `range`, `none`                                         |
| `NOM.config.json`, `NOM.reglages.json` | `profile`: `perso`                                                 | `private`                                                      |
| `NOM.tiles.json`                       | `budgetMo`, `wholeWeightMo`, `thresholdMo`                         | `budgetMB`, `wholeWeightMB`, `thresholdMB`                     |
| address of the page                    | `?rayon=`                                                          | `?radius=`                                                     |
| address of the viewer                  | `?tuiles=`                                                         | `?tiles=`                                                      |

The two development tools (`gen_reference.py`, `verif_trad.py`) followed in v44, and the `--update` messages start with `[update]`. Unchanged: `--analyse` (also British English) and the values that are object names, such as `door, porte`. In the tools' help, the example names of the values are also in English (`FILE`, `PATH`, `NAME`, `DEGREES`, `SHELL.html`). The history (`CHANGELOG.md`, `HISTORY.md`) keeps the names of the time.

## 11.12 JSON files of a modular region

For a `Region.html` page produced by `--modular` (or by "Export the modular structure (.zip)" in the viewer), the folder contains:

These files are those of a region with its own shell (`--modular`). For several regions in the same folder with **a single** shell, see "Single shell for several regions" below.

| File                 | Role                                                                                      | Read again at each F5 |
| -------------------- | ----------------------------------------------------------------------------------------- | --------------------- |
| `Region.html`        | shell identical for all regions, it deduces its files from its own name                   | no                    |
| `Region.glb`         | the model                                                                                 | no                    |
| `Region.config.json` | settings for **rendering the page** (see below)                                           | yes                   |
| `Region.zones.json`  | zones, portals, arrivals                                                                  | yes                   |
| `zones.json`         | fallback zones, shared by the pages of the folder that have no `.zones.json` of their own | yes                   |
| `lib/three-0.160.0/` | three.js, Draco, Meshopt, shared by all the pages of the folder                           | no                    |

### 11.12.1 Which zone file is read

In this order, stopping at the first one that gives a valid JSON list:

1. `Region.zones.json`
2. `zones.json` of the same folder, **only if** the first one is missing, inaccessible (HTTP error) or is not a list
3. otherwise: no zone

There is **no merging**: as soon as `Region.zones.json` is read, `zones.json` is ignored. A `zones.json` placed next to a region that already has its `.zones.json` therefore has no effect.

Zones marked **private** are removed when reading, in either file, unless `profile` is `private` in `Region.config.json`.

### 11.12.2 Region.config.json: the page rendering, not the viewer

It is the dictionary of settings that the page reads at startup (the same as the one embedded in a standalone page). It is **flat**. The complete list of its fields, with their type, default value, role and the option that sets them, is in **§ 11.3**; a complete sample is in `docs/samples/region.config.sample.json`.

`zones` is **always empty** there (`[]`) and `zonesLive` always empty: in modular mode, the zones are only in `Region.zones.json`.

The viewer never reads this file: it works with its own settings file (below).

### 11.12.3 `.reglages.json` and `.config.json` do not have the same structure

`<nom>.reglages.json` is the working state of the viewer ("Save to a file"). It is **nested**:

```
{ v, file, saved,
  cfg:     { rotate, hole, holeFade, ..., mapUrl, guide, ignoreViz },
  camera:  { camDir, target, zoom },
  zones:   [ ...all the zones, private ones included ],
  profile, thisReg: { card of this region for the map },
  cmd:     { script, glb, dest, mapPage } }
```

|            | `<nom>.reglages.json` (viewer)           | `<page>.config.json` (page)              |
| ---------- | ---------------------------------------- | ---------------------------------------- |
| Structure  | nested (`cfg`, `camera`, ...)            | flat                                     |
| Camera     | `camera` sub-object                      | at the root (`camDir`, `target`, `zoom`) |
| Zones      | all, private ones included               | always empty                             |
| Map        | only the card of this region (`thisReg`) | complete resolved map (`map`)            |
| Its own    | `guide`, `ignoreViz`, `cmd`, `thisReg`   | `seaSize`, `version`                     |
| Written by | the viewer                               | `glb2html.py`                            |
| Read by    | the viewer, `glb2html.py --settings`     | the exported page                        |

The conversion only goes one way:

```
<nom>.reglages.json  ->  glb2html.py --settings  ->  <page>.config.json + <page>.zones.json
```

A `.config.json` cannot be given to `--settings` (the script looks for the `cfg` key and refuses the file), nor reloaded in the viewer ("settings file not recognized"). To keep your settings, you must therefore keep the `.reglages.json`: the `.config.json` is only a derived product of it.

### 11.12.4 Which file to edit, and what overwrites it

| I want to change...                 | I edit / I run                                                  | What can overwrite it afterwards                                           |
| ----------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------- |
| a rendering setting (waves, sky...) | `--config-only` (see below), or `Region.config.json` by hand    | any new `--modular` or `--config-only` rewrites `Region.config.json`       |
| a zone                              | `Region.zones.json` by hand, or **Export zones (.json)** (§ 6.16) | `--modular` with `--zones` or `--settings`; `--config-only` with `--zones` |
| the working state of the viewer     | **Save to a file**                                              | nothing (it is the source)                                                 |

Without `--zones` or `--settings`, a `Region.zones.json` already present (edited by hand, for example) is not overwritten. As soon as a source of zones is given, it is rewritten.

Change a setting without touching the `.glb`, the shell or the zones:

```
python glb2html.py --settings "Region-final.glb" --config-only --wave 2 -o "Region.html"
```

The command-line options take precedence over the `.reglages.json`. Visitors see the change at their next reload.
