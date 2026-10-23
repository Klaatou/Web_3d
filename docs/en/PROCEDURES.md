# How do I… (step-by-step procedures)

*Written on 23/10/2026 for version v36. The commands are for PowerShell, on a single line, with the paths of your machine. The full list of options is in `REFERENCE_OPTIONS.md`; zones, keys and settings are described in detail in `MODE_EMPLOI.md`.*

**What was tried here:** the `glb2html` and `glb2tiles` commands (including `--maj`, `--register`, `--map-page`) on test regions, as a single GLB and as tiles. **What was not:** converting an OAR with convoar (convoar is not available in the sandbox), and the PowerShell commands themselves (tried under Linux with equivalent paths).

**The three reference folders**

| Role | Path |
|---|---|
| Tools (built by `python build.py`) | `P:\_OpenSim\SL&OS\Web_3d\web_3d\dist` |
| Source OAR and GLB | `J:\Download\Com\Chat\_Monde virtuel en ligne_\_OpenSim_\_Contenu_\OAR` |
| Regions published as tiles | `P:\_OpenSim\SL&OS\Web_3d\tuiles` |

**Golden rule:** always run the tools from the tools folder (`cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"`). Give **full paths** for every file written, except with `--maj` (relative paths are then relative to the page's folder).

---

## 1. From an OAR to a web page, light region (a single GLB)

Choose this when `glb2tiles --analyse` does not recommend splitting (roughly: GLB under 150 MB and under 3 million triangles).

1. **Convert the OAR.** The GLB is written next to the OAR (`MaRegion.oar` gives `MaRegion.glb`). The complete terrain is added automatically if convoar's is incomplete.
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python oar2glb.py "J:\Download\Com\Chat\_Monde virtuel en ligne_\_OpenSim_\_Contenu_\OAR\MaRegion.oar"`
2. **Check whether splitting would be needed** (read-only, writes nothing):
   `python glb2tiles.py "J:\Download\Com\Chat\_Monde virtuel en ligne_\_OpenSim_\_Contenu_\OAR\MaRegion.glb" --analyse`
3. **Build the page** in a publishing folder (for example `P:\_OpenSim\SL&OS\Web_3d\sites\MaRegion`, to be created):
   `python glb2html.py "J:\Download\Com\Chat\_Monde virtuel en ligne_\_OpenSim_\_Contenu_\OAR\MaRegion.glb" --shared-shell -o "P:\_OpenSim\SL&OS\Web_3d\sites\MaRegion\MaRegion.html" --sea-y 18.5 --presence-url "ws://ADRESSE:8765" --chat`
   Written: `MaRegion.glb`, `MaRegion.config.json`, `MaRegion.zones.json`, `index.html` and `lib\`.
4. **Serve and open.** The page must go through a web server, not a double-click.
   `cd "P:\_OpenSim\SL&OS\Web_3d\sites\MaRegion"; python -m http.server 8000`
   Then `http://localhost:8000/index.html?region=MaRegion`.
5. **Place the zones** (portals, arrivals, signs) in `glb-viewer.html`: see `MODE_EMPLOI.md` §§ 3 to 12. When you are done, the viewer exports `MaRegion.zones.json`: copy it into the page's folder, then F5.

## 2. From an OAR to a web page, heavy region (tiles)

The case of the 4X4: a 1.2 GB GLB does not fit in one piece in the browser. Tiles load around the avatar and the rest is unloaded; the overview shows the whole region from afar.

1. **Convert the OAR** as in 1.1. It can take several hours and several tens of GB of memory (4 h 20 and 45 GB for the 4X4). If convoar crashes while reading the JPEG 2000 textures, run it again with `--reencode` (see `MODE_EMPLOI.md` § 15: only as a last resort).
2. **Analyse** (read-only):
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python glb2tiles.py "J:\...\OAR\X.glb" --analyse`
3. **Split.** `--sortie` is the folder where `X.tiles\`, `X.tiles.json` and `X.overview.glb` are written. `--exclure` removes from the split the objects whose name matches (safeguards: at most 24 triangles and 1 mesh), for example the delivery boxes of catalogues.
   `python glb2tiles.py "J:\...\OAR\X.glb" --sortie "P:\_OpenSim\SL&OS\Web_3d\tuiles" --exclure "RAKis Freebies"`
4. **Build the page.** Replace `ADRESSE` with your public address and `--target` with an open spot (coordinates read in the viewer), or place an arrival named `default` and remove `--target`.
   `python glb2html.py --shared-shell -o "P:\_OpenSim\SL&OS\Web_3d\tuiles\X.html" --tiles "P:\_OpenSim\SL&OS\Web_3d\tuiles\X.tiles.json" --sea-y 18.5 --presence-url "ws://ADRESSE:8765" --chat --target 392,68,-373`
5. **Serve and open**:
   `cd "P:\_OpenSim\SL&OS\Web_3d\tuiles"; python -m http.server 8000`
   Then `http://localhost:8000/index.html?region=X`.
6. **Place the zones.** Open `glb-viewer.html`, button "Open a tiled region (folder)", choose the `tuiles` folder. Place your zones, then "Save the zones in the region folder" (Edge or Chrome; otherwise the export is a download, to be copied into the folder under the name `X.zones.json`). F5 on the page: the zones are taken into account, without rebuilding.

To link a zone to an object of the tiled region, the tiles must have been split with `glb2tiles` v32 or later (otherwise, split again).

## 3. Change a setting of a region already published (sea, starting point, presence…)

**One value: edit the config file and reload.** The page reads `X.config.json` again at each opening, without cache.
`notepad "P:\_OpenSim\SL&OS\Web_3d\tuiles\X.config.json"`
Useful keys: `seaY` (sea level, in m), `target` (`[x, y, z]`), `presenceUrl`, `chat` (`true` or `false`), `zoneInfoDist`, `tileRadius`, `tileMaxMo`, `tileMaxTri`. The JSON is strict: keep the commas and the quotes. **Colours are stored there as decimal numbers** (`seaColor` 3840729 is `3a9ad9`): to change them, use `--maj` instead.

**Several values, or a colour: `--maj`.** It applies only the options you write, and keeps the rest of the config and the zone file.
`cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python glb2html.py --maj --shared-shell -o "P:\_OpenSim\SL&OS\Web_3d\tuiles\X.html" --sea-y 10`

**Never run the full build command again (procedure 2.4) to change a detail**: it rewrites the whole config from the options on the line alone, and erases what you had set by hand.

## 4. After a new version of the tools

1. Merge the session's branch, build, push, tag (the session gives the exact line):
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d"; git checkout main; git pull; git fetch; git merge origin/NOM -m "Fusion vNN"; python build.py; git push; git tag vNN HASH; git push origin vNN`
2. Update each region with `--maj`. The `index.html` shell is renewed if it is older (the old one is kept under a dated name); the config and the zones are kept.
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python glb2html.py --maj --shared-shell -o "P:\_OpenSim\SL&OS\Web_3d\tuiles\X.html"`
3. Reload the page with Ctrl+F5. The bottom line of the help panel gives the version displayed (for example "glb2html v36"): if it is old, the update did not happen.
4. Restart the presence server: **yes for v36** (its messages and its help are translated; an old copy keeps working but stays in French). Procedure 6.
5. The tile split only needs to be redone if the session says so, for example for new information in the tiles.

## 5. Place and edit zones

| Need | Where |
|---|---|
| Place a portal, arrival, sign, link | viewer, `MODE_EMPLOI.md` §§ 3 to 8 |
| Arrival used when the page is opened without a link | an arrival named `default` (§ 4); an explicit `--target` keeps the framing |
| Portal to another region | `MODE_EMPLOI.md` § 6 |
| Zone linked to an object of the model | `MODE_EMPLOI.md` § 9 (as tiles: § 17 ter) |
| Private zone (visible only with the "perso" profile) | `MODE_EMPLOI.md` § 10 |

The zones of a tiled region are written in the model's original frame (no recentring). The viewer in tiles mode produces these coordinates directly; do not copy by hand coordinates from another GLB.

## 6. Presence server (positions, chat, moderation)

1. **Install** once: `pip install websockets`
2. **Run** (a relative log is written in the script's folder; `--log-ip raw` writes IP addresses in clear, `--log-days` limits retention, **`--log-days 0` keeps the logs without limit**):
   `python ".\presence_server.py" --log presence.log --log-ip raw --log-days 0`
   Chat history (v37): the last 200 messages are replayed to newcomers (`--history`); `--history-file chat.jsonl` keeps it between two restarts (messages are personal data, never an IP address in this file), `--history-days N` (30; 0 = keep everything) limits what is read back at startup.
3. **Open the port** (8765 by default, `--port` to change it) on the router, towards the machine running the server.
4. **Connect the page**: `--presence-url "ws://ADRESSE:8765"` when building, or the `presenceUrl` key of `X.config.json`. If the page is served over https, the address must use `wss://` (see `--cert` and `--key`, or a reverse proxy with `--proxy-header`).
5. **Moderate** in the server console: `list` (visitors), `kick <no.|name> [reason]`, `ban <no.|name> [minutes] [reason]` (0 = permanent), `bans`, `unban <no. in bans>`, `help`.
6. **Update**: stop the server (Ctrl+C) and run it again from the `presence_server.py` of the `dist` folder after `python build.py`. An old copy ignores new features (for example the chosen colour).

IP addresses and chat messages are personal data: inform your visitors and limit how long they are kept.

## 7. World map

Two steps, with `--maj` (relative paths are then relative to the page's folder).

1. **Register each region** in `regions.json`:
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python glb2html.py --maj -o "P:\_OpenSim\SL&OS\Web_3d\tuiles\X.html" --shared-shell --register "P:\_OpenSim\SL&OS\Web_3d\tuiles\regions.json" --region-name "Display name"`
   For another region, same command with its page and its name (`--region-xy x,y` gives its place on the map).
2. **Generate the map page** (after each registration):
   `python glb2html.py --maj -o "P:\_OpenSim\SL&OS\Web_3d\tuiles\X.html" --shared-shell --map-page "P:\_OpenSim\SL&OS\Web_3d\tuiles\carte.html"`
3. Open `carte.html` through the web server. A "My nickname" field at the top adds `name=` to the region links.

With a single region, the map brings nothing: it is used to link several regions together.

## 8. What to restart when

| What changed | What to do | Page reload |
|---|---|---|
| A setting value (sea, target, presence) | edit `X.config.json`, or `--maj` with the option | F5 |
| The zones | save `X.zones.json` in the region's folder | F5 |
| New version of the tools | procedure 4 (`--maj`) | Ctrl+F5 |
| New version of the presence server (v37: chat history; v36: translated messages) | stop and restart `presence_server.py` | F5 |
| The OAR changed | convert again (1.1 or 2.1), split again (2.3), then `--maj` | Ctrl+F5 |
| The objects excluded from the split | split again (2.3) with another `--exclure` | Ctrl+F5 |
| Rotation of the region (`--rotate`) | `--maj --rotate 180`, then redo the map thumbnail | Ctrl+F5 |
| First publication of a region | procedure 1 or 2 (full command) | — |

## 9. When it does not work

| Symptom | Likely cause | What to do |
|---|---|---|
| Black page with `#spawn=…` | the arrival's tile is loading | since v33, a "Loading the ground…" text should appear; otherwise, console (F12) and `[tile] …` lines |
| "Loading the ground…" that lasts | large tile | wait; note the `[tile] …` lines of the console |
| The zones do not appear | zone file elsewhere than in the page's folder, private zone, discreet marker | check `X.zones.json` in the served folder, F5 in a private window, `--zone-marker portee` |
| The settings do not change | old shell, cache | `--maj`, then Ctrl+F5 |
| "Couldn't load texture" errors | 0-byte images in tiles from before v31 | split again with glb2tiles v31 or later |
| No chat | page built without `--presence-url` or without `--chat` | add the options with `--maj`, restart the server |
| The avatar colour does not change | old presence server | restart the `presence_server.py` of the `dist` folder |
| Copy the help text | — | select with the mouse, Ctrl+C; otherwise, in the console: `copy(document.body.innerText)` |

For any bug report, paste the text of the status and help panels, and the console messages (ignoring those of LastPass).

## 10. Useful keys and language (v36)

| Need | Action |
|---|---|
| Enter or leave walk mode | **F** or **P** (in the viewer, P places a zone: leave with **F** or **Shift+P**) |
| Trigger a nearby zone | click on it, or **E** ("walk into it" portal: when entering its radius) |
| Fly | **Home**, the fly button, or **Page Up** held more than 0.4 s; go up: **Page Up** or **Space** held; go down: **Page Down** or **C**; jump: **Space** or a short press on **Page Up** |
| Show the portal markers | **T** (removed from the build with `--no-zone-cone`) |
| AZERTY or QWERTY keyboard | "Keyboard layout" setting of the page (Auto by default): the physical keys do not change, the help shows the letters of your layout |
| Page language | "Language / Langue" setting (Auto, français, English), or `#lang=en` in the address |
| Tools language | `--lang fr` or `--lang en` on each tool, or the `WEB3D_LANG` environment variable; with nothing, the system language. PowerShell, for one session: `$env:WEB3D_LANG = "fr"` |
| Copy my position | "Copy my position" button (URL / xyz list); "Go to" accepts the `#pos=…` URL and `x, y, z` |
| Open or close the Settings | **O** key (toggle, like **H** and **I**) |
| Compass (heading at the top of the page) | "Compass" box in the Settings; `--no-compass` to remove it from the build, `--north DEGRES` for a GLB that does not come from OpenSim |
| Adjust the width of the help and information windows | drag their right edge (260 px to 70 % of the window), remembered |
| Chat: older messages, unread, mentions | "Older messages" button (chat open), tab title "(3) Region", "N messages mention you"; "History messages kept in the chat" setting |
| Default region (address without `?region=`) | `default.json` written for the first region of a folder, `--default` to change it; otherwise the first relative entry of `regions.json` |
| Put `lib/` elsewhere | `--lib-url ../lib` (or an `https://…/lib` address) when building the shell; remembered for `--maj` |
| Region in a subfolder | `glb2html.py X.glb --shared-shell "P:\site\index.html" -o "P:\site\sous\dossier\X.html"`; address `index.html?region=sous/dossier/X` |
| Address parameters | separated by `&`; `#` is also accepted (`#name=Klaatou&lang=en` = `#name=Klaatou#lang=en`) |

Details: `MODE_EMPLOI.md` §§ 2, 21 and 22.
