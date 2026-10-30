# How do I… (step-by-step procedures)

*Written on 23/10/2026, revised on 29/10/2026 for version 1.0.0 (the "vNN" in the text are the versions before 1.0.0: v52 became 1.0.0). The commands are for PowerShell, on a single line, with the paths of your machine. The full list of options is in `REFERENCE_OPTIONS.md`; zones, keys and settings are described in detail in `MANUAL.md`.*

**What was tried here:** the `glb2html` and `glb2tiles` commands (including `--update`, `--register`, `--map-page`) on test regions, as a single GLB and as tiles. **What was not:** converting an OAR with convoar (convoar is not available in the sandbox), and the PowerShell commands themselves (tried under Linux with equivalent paths).

**The three reference folders**

| Role | Path |
|---|---|
| Tools (built by `python build.py`) | `P:\_OpenSim\SL&OS\Web_3d\web_3d\dist` |
| Source OAR and GLB | `J:\Download\Com\Chat\_Monde virtuel en ligne_\_OpenSim_\_Contenu_\OAR` |
| Regions published as tiles | `P:\_OpenSim\SL&OS\Web_3d\tuiles` |

**Golden rule:** always run the tools from the tools folder (`cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"`). Give **full paths** for every file written, except with `--update` (relative paths are then relative to the page's folder).

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
5. **Place the zones** (portals, arrivals, signs) in `glb-viewer.html`: see `MANUAL.md` §§ 3 to 12. When you are done, the viewer exports `MaRegion.zones.json`: copy it into the page's folder, then F5.

## 2. From an OAR to a web page, heavy region (tiles)

The case of the 4X4: a 1.2 GB GLB does not fit in one piece in the browser. Tiles load around the avatar and the rest is unloaded; the overview shows the whole region from afar.

1. **Convert the OAR** as in 1.1. It can take several hours and several tens of GB of memory (4 h 20 and 45 GB for the 4X4). If convoar crashes while reading the JPEG 2000 textures, run it again with `--reencode` (see `MANUAL.md` § 15: only as a last resort).
2. **Analyse** (read-only):
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python glb2tiles.py "J:\...\OAR\X.glb" --analyse`
3. **Split.** `--output` is the folder where `X.tiles\`, `X.tiles.json` and `X.overview.glb` are written. `--exclude` removes from the split the objects whose name matches (safeguards: at most 24 triangles and 1 mesh), for example the delivery boxes of catalogues.
   `python glb2tiles.py "J:\...\OAR\X.glb" --output "P:\_OpenSim\SL&OS\Web_3d\tuiles" --exclude "RAKis Freebies"`
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
Useful keys: `seaY` (sea level, in m), `target` (`[x, y, z]`), `presenceUrl`, `chat` (`true` or `false`), `zoneInfoDist`, `tileRadius`, `tileMaxMB`, `tileMaxTriangles`. The JSON is strict: keep the commas and the quotes. **Colours are stored there as decimal numbers** (`seaColor` 3840729 is `3a9ad9`): to change them, use `--update` instead.

**Several values, or a colour: `--update`.** It applies only the options you write, and keeps the rest of the config and the zone file.
`cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python glb2html.py --update --shared-shell -o "P:\_OpenSim\SL&OS\Web_3d\tuiles\X.html" --sea-y 10`

**Never run the full build command again (procedure 2.4) to change a detail**: it rewrites the whole config from the options on the line alone, and erases what you had set by hand.

## 4. After a new version of the tools

1. **Apply the patch and build** (the conversation gives the exact lines, each on one line):
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d"; git pull; python .\patch_NOM.py; if ($LASTEXITCODE -eq 0) { python build.py }`
   then the `git add …; git commit …; git push` line delivered with the patch, and, only when you decide on a release, `git tag v1.0.0; git push origin v1.0.0` (the number is the one in `VERSION`).
2. **Copy the shell and the map** to the root of the site (`Sites\` layout, `MANUAL.md` § 29.8); the shell's `const LIB` line stays `./lib`:
   `Copy-Item "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\index.html" "P:\_OpenSim\SL&OS\Web_3d\Sites\index.html"; Copy-Item "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\carte.html" "P:\_OpenSim\SL&OS\Web_3d\Sites\carte.html"`
3. **Update each region** with `--update` (the config and the zones are kept). Give the path of the root shell, otherwise a useless shell and `lib` are written in the region's folder:
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --update -o "P:\_OpenSim\SL&OS\Web_3d\Sites\houses\NOM.html" --shared-shell "P:\_OpenSim\SL&OS\Web_3d\Sites\index.html"`
   Region alone in its folder (shell next to it): `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --update --shared-shell -o "P:\dossier\X.html"`. The `index.html` shell is renewed if it is older (the old one is kept under a dated name).
4. Reload the page with Ctrl+F5. The bottom line of the help panel gives the version displayed (for example "glb2html 1.0.0 (29/10/2026)"): if it is old, the update did not happen.
5. **Restart the presence server** from `dist\` (procedure 6) after each new version: an old copy keeps working but lacks the new features (v47: map counters; v48: visit log).
6. The tile split only needs to be redone if the conversation says so, for example for new information in the tiles.

## 5. Place and edit zones

| Need | Where |
|---|---|
| Place a portal, arrival, sign, link | viewer, `MANUAL.md` §§ 3 to 8 |
| Arrival used when the page is opened without a link | an arrival named `default` (§ 4); an explicit `--target` keeps the framing |
| Portal to another region | `MANUAL.md` § 6 |
| Zone linked to an object of the model | `MANUAL.md` § 9 (as tiles: § 17 ter) |
| Private zone (visible only with the "private" profile) | `MANUAL.md` § 10 |

The zones of a tiled region are written in the model's original frame (no recentring). The viewer in tiles mode produces these coordinates directly; do not copy by hand coordinates from another GLB.

## 6. Presence server (positions, chat, moderation)

1. **Install** once: `pip install websockets`
2. **Run** (a relative log is written in the script's folder; `--log-ip raw` writes IP addresses in clear, `--log-days` limits retention, **`--log-days 0` keeps the logs without limit**):
   `python ".\presence_server.py" --log presence.log --log-ip raw --log-days 0`
   Chat history (v37): the last 200 messages are replayed to newcomers (`--history`); `--history-file chat.jsonl` keeps it between two restarts (messages are personal data, never an IP address in this file), `--history-days N` (30; 0 = keep everything) limits what is read back at startup.
3. **Open the port** (8765 by default, `--port` to change it) on the router, towards the machine running the server.
4. **Connect the page**: `--presence-url "ws://ADRESSE:8765"` when building, or the `presenceUrl` key of `X.config.json`. If the page is served over https, the address must use `wss://` (see `--cert` and `--key`, or a reverse proxy with `--proxy-header`). If your pages are opened through several addresses (`localhost`, network, public name), use `ws://*:8765`: the star takes the name the page was opened with (manual § 34.10).
5. **Moderate** in the server console: `list` (visitors), `kick <no.|name> [reason]`, `ban <no.|name> [minutes] [reason]` (0 = permanent), `bans`, `unban <no. in bans>`, `pseudos` (lists the reserved names), `oublier <pseudo>` (releases a reserved name), `help`. A ban targets the visitor's key (if it is not anonymous) and their IP address: the exact IPv4 address, IPv6 by `/64` prefix (never a wider range).
6. **Visit log** (v48): add `--visits visits.jsonl` to the start line; in the console, `rooms` lists the known rooms (exact case) and `visits-key ROOM` gives a room's key (shown only once). Send the creator their page address followed by `#visits` and the key (manual § 31).
7. **Welcome a creator** (v51, manual § 34): add `--creators presence_creators.json` to the start line; in this file (copy of `docs\samples\presence_creators.sample.json`), keep an entry for yourself (`"prefix": ""`, your origins and `null`) and add theirs (`id`, origins of their pages). The creator sets `room` to `ID.NAME` (for example `alice.galerie`) and your `wss://` address in `presenceUrl` of their config. Check with `creators` in the console; key of their visits: `visits-key alice.galerie`; card on your map: `--register` without a glb (manual § 27.6).
8. **Update**: stop the server (Ctrl+C) and run it again from the `presence_server.py` of the `dist` folder after `python build.py`. An old copy ignores new features (for example the chosen colour).
9. **Permanent server on a VM**: a plain systemd service gives the moderation console no keyboard; the way that worked (a `tmux` session started by systemd) is described in § 11, "Debian 13 VM: permanent service with a moderation console".

IP addresses and chat messages are personal data: inform your visitors and limit how long they are kept. The visit log never contains an IP address.

## 7. World map

With the `Sites\` layout (one shell at the root, one folder per region, `MANUAL.md` § 29.8):

1. **Update `regions.json` from the folder** (v49):
   `cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --scan-sites "P:\_OpenSim\SL&OS\Web_3d\Sites" --dry-run`
   then the same line without `--dry-run`. One card per region found, with its `NOM.jpg` thumbnail next to `NOM.config.json` (a 320-pixel square is recommended); the names, places and arrivals already recorded are kept; nothing is deleted (`MANUAL.md` § 32).
2. **Name and place the regions** once: `name`, `x`, `y` and `spawn` in `Sites\regions.json`, by hand or with the viewer ("Import regions.json", edit, "Export regions.json": the header and every field are kept since v50). The next scans keep them.
3. **Show the map**: `carte.html` (copied to the root, procedure 4) reads `regions.json` again each time it opens, nothing to regenerate (`MANUAL.md` § 30.4). Open it through the web server, for example `http://localhost:8000/carte.html` after `cd "P:\_OpenSim\SL&OS\Web_3d\Sites"; python -m http.server 8000`. A "My nickname" field at the top adds `name=` to the region links.

Without a site folder: `--register regions.json` adds the region at each generation (`--region-name`, `--region-xy x,y`), and `--map-page carte.html` writes a standalone page that contains the list (`MANUAL.md` § 30.4).

With a single region, the map brings nothing: it is used to link several regions together.

## 8. What to restart when

| What changed | What to do | Page reload |
|---|---|---|
| A setting value (sea, target, presence) | edit `X.config.json`, or `--update` with the option | F5 |
| The zones | save `X.zones.json` in the region's folder | F5 |
| New version of the tools | procedure 4 (`--update`) | Ctrl+F5 |
| New version of the presence server (v48: visit log; v47: map counters; v37: chat history) | stop and restart `presence_server.py` | F5 |
| The OAR changed | convert again (1.1 or 2.1), split again (2.3), then `--update` | Ctrl+F5 |
| The objects excluded from the split | split again (2.3) with another `--exclude` | Ctrl+F5 |
| Rotation of the region (`--rotate`) | `--update --rotate 180`, then redo the map thumbnail | Ctrl+F5 |
| First publication of a region | procedure 1 or 2 (full command) | — |

## 9. When it does not work

| Symptom | Likely cause | What to do |
|---|---|---|
| Black page with `#spawn=…` | the arrival's tile is loading | since v33, a "Loading the ground…" text should appear; otherwise, console (F12) and `[tile] …` lines |
| "Loading the ground…" that lasts | large tile | wait; note the `[tile] …` lines of the console |
| The zones do not appear | zone file elsewhere than in the page's folder, private zone, discreet marker | check `X.zones.json` in the served folder, F5 in a private window, `--zone-marker range` |
| The settings do not change | old shell, cache | `--update`, then Ctrl+F5 |
| "Couldn't load texture" errors | 0-byte images in tiles from before v31 | split again with glb2tiles v31 or later |
| No chat | page built without `--presence-url` or without `--chat` | add the options with `--update`, restart the server |
| The avatar colour does not change | old presence server | restart the `presence_server.py` of the `dist` folder |
| Copy the help text | — | select with the mouse, Ctrl+C; otherwise, in the console: `copy(document.body.innerText)` |

For any bug report, paste the text of the status and help panels, and the console messages (ignoring those of LastPass).

## 10. Useful keys and language

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
| Mouse in walk mode | **G** toggles the capture (captures it if it is free, releases it if it is captured); the "Capture the mouse" button only captures; **Esc** releases it; a click never captures it |
| Change the view | **V**: first person, third person, free camera; **M**: first / third person in walk mode, world map outside walk mode (**Ctrl+M**: map everywhere) |
| Go back to the arrival point | **R** |
| Compass (heading at the top of the page) | "Compass" box in the Settings; `--no-compass` to remove it from the build, `--north DEGRES` for a GLB that does not come from OpenSim |
| Adjust the width of the help and information windows | drag their right edge (260 px to 70 % of the window), remembered |
| Chat: older messages, unread, mentions | "Older messages" button (chat open), tab title "(3) Region", "N messages mention you"; "History messages kept in the chat" setting |
| Default region (address without `?region=`) | `default.json` written for the first region of a folder, `--default` to change it; otherwise the first relative entry of `regions.json` |
| Put `lib/` elsewhere | `--lib-url ../lib` (or an `https://…/lib` address) when building the shell, or edit by hand the `const LIB = './lib';` line at the start of `index.html`; `--update` keeps it |
| Region in a subfolder | `glb2html.py X.glb --shared-shell "P:\site\index.html" -o "P:\site\sous\dossier\X.html"`; address `index.html?region=sous/dossier/X` |
| On-screen arrows (v46) | **K**, "Arrows (K)" button or "On-screen arrows (K)" checkbox in Settings; press and hold = key held |
| Phone, tablet (v46) | automatic touch mode ("Touch controls" setting): column of buttons, "Menu", drag a finger to look around, long press = tooltip |
| Address parameters | separated by `&`; `#` is also accepted (`#name=Klaatou&lang=en` = `#name=Klaatou#lang=en`) |

Details: `MANUAL.md` §§ 2, 21 and 22.

---

## 11. Making the presence server public without showing your IP address

*Written on 24/10/2026, completed on 29/10/2026. **Tried on 24/10/2026**: Tailscale Funnel (way A), with a page served over `http` and a visitor outside the network. **Tried on 29/10/2026**: way A on a Debian 13 VM, with a page published on GitHub Pages (https), a visitor outside the network, a restart of the VM and of the service (see "Debian 13 VM: permanent service with a moderation console"). **Not tried**: Caddy (way B), Cloudflare Tunnel (way C), way D with Apache under Tailscale (Apache, service and configuration lines tried in the design sandbox, but not Tailscale) and the commands of the case "another service is already published". Always check the result with the control of the final step ("Checking the address seen by the server").*

**Principle.** A browser refuses a `ws://` connection from an https page: an https page therefore needs a presence address in `wss://NOM`. The visitor only connects to that `NOM`, never to your IP. A relay receives the `wss://` and passes it on as `ws://` to `presence_server.py`, which then only listens on `127.0.0.1` (hence without `--cert` or `--key`). Choose **one** of the four ways.

**Rule learned on 24/10/2026: the presence must be in the same place as the page**: same name, or an https page also published by Funnel. On a device where Tailscale is active, the browser blocks the presence connection when the page comes from another address (the `.ts.net` name gives a private 100.x address there); with Tailscale switched off on the phone, the same page connects.

### Way A: at home, Tailscale Funnel (no port to open on the router)
1. Install Tailscale on the machine that runs the server and connect it to your account. In the Tailscale admin console, enable **HTTPS** (DNS) and allow **Funnel** for this machine (see the "Tailscale Funnel" documentation).
2. Before publishing, look at what is already published: `tailscale serve status` and `tailscale funnel status`. **`tailscale funnel` takes the root of the port and replaces what `tailscale serve` was publishing there** (observed: the service that was there was overwritten). If a service is already published, go to the case "another service is already published" below. Only use `tailscale funnel reset` to erase everything.
3. Start the server on the local address only (PowerShell, one line): `python ".\presence_server.py" --host 127.0.0.1 --port 8765 --proxy-header X-Forwarded-For --origins "https://TONSITE" --log presence.log --log-ip raw --log-days 0 --history-file chat.jsonl --history-days 0`
4. Expose it: `tailscale funnel --bg 8765`. The public address is `https://MACHINE.TAILNET.ts.net`; the presence address is therefore `wss://MACHINE.TAILNET.ts.net`.
5. Your IP does not appear; on the other hand, the name of your machine and the name of your Tailscale network are public.

Results of the 24/10/2026 test:
- the WebSocket goes through Funnel (response 101);
- with `--proxy-header X-Forwarded-For`, the log shows the visitor's real IP;
- a visitor outside the network walked around through Funnel;
- on devices where Tailscale is active, the connection is blocked if the page comes from another address (see the rule above);
- a detour through the machine's `hosts` file did not work.

### Way B: small VPS, Caddy (automatic https certificate)
You need a domain name with an `A` record pointing to the VPS, and root access **only once**, for the installation (open ports 80 and 443 only).
1. Install Python, `pip install websockets` and Caddy.
2. `Caddyfile`: a block `presence.TONDOMAINE.tld { reverse_proxy 127.0.0.1:8765 }`. Caddy handles WebSockets and sends the visitor's address in `X-Forwarded-For`.
3. Start the server: `python3 presence_server.py --host 127.0.0.1 --port 8765 --proxy-header X-Forwarded-For --origins "https://TONSITE" --log presence.log --history-file chat.jsonl`
4. Presence address: `wss://presence.TONDOMAINE.tld`. Here the VPS's IP is public in the DNS; way C hides it.

### Way C: Cloudflare Tunnel (IP hidden, no port open, at home or on a VPS)
You need a domain name managed by Cloudflare (free account).
1. Install `cloudflared`, then `cloudflared tunnel login` and `cloudflared tunnel create presence`.
2. In the tunnel's configuration file, route `presence.TONDOMAINE.tld` to `http://127.0.0.1:8765` (`cloudflared tunnel route dns presence presence.TONDOMAINE.tld`, then `cloudflared tunnel run presence`).
3. Start the server: `python3 presence_server.py --host 127.0.0.1 --port 8765 --proxy-header CF-Connecting-IP --origins "https://TONSITE"`
4. Presence address: `wss://presence.TONDOMAINE.tld`.

### Way D: Linux VM, Tailscale Funnel and Apache (page and presence under the same name)
For a page served by Apache on a Linux VM. A single public name (`https://MACHINE.TAILNET.ts.net`) serves the page at the root and the presence under `/presence`: the page and the presence are in the same place. Apache and the presence only listen on `127.0.0.1`; no port is opened on the router.
1. **Tailscale inside the VM**: install it, connect the VM, enable **HTTPS** and allow **Funnel** (as in step 1 of way A).
2. **Apache on `127.0.0.1` only** (Debian or Ubuntu; tried with Apache 2.4.58 on Ubuntu 24.04). In `/etc/apache2/ports.conf`, replace `Listen 80` with `Listen 127.0.0.1:80`. File `/etc/apache2/sites-available/web3d.conf`:

```
<VirtualHost 127.0.0.1:80>
    DocumentRoot /var/www/web3d
    <Directory /var/www/web3d>
        Require all granted
    </Directory>
    RemoteIPHeader X-Forwarded-For
    RemoteIPInternalProxy 127.0.0.1
    ErrorLog ${APACHE_LOG_DIR}/web3d-error.log
    CustomLog ${APACHE_LOG_DIR}/web3d-access.log combined
</VirtualHost>
```

   Then `a2enmod remoteip`, `a2dissite 000-default`, `a2ensite web3d`, `apache2ctl configtest` (expected message: `Syntax OK`), and reload Apache. The two `RemoteIP` lines make Apache's log show the visitor's IP instead of `127.0.0.1` (tried here with a simulated header; behind Funnel: to be checked). The page files go in `/var/www/web3d`.
3. **Presence as a system service.** Account and Python environment (tried): `useradd --system --home /opt/web3d --shell /usr/sbin/nologin web3d`, then `mkdir -p /opt/web3d`, `python3 -m venv /opt/web3d/venv` and `/opt/web3d/venv/bin/pip install websockets`. Copy `presence_server.py` (the file from `dist\`) into `/opt/web3d/`. File `/etc/systemd/system/web3d-presence.service`:

```
[Unit]
Description=Web 3d presence server
After=network-online.target
Wants=network-online.target

[Service]
User=web3d
StateDirectory=web3d
ExecStart=/opt/web3d/venv/bin/python /opt/web3d/presence_server.py --host 127.0.0.1 --port 8765 --proxy-header X-Forwarded-For --origins https://MACHINE.TAILNET.ts.net --log /var/lib/web3d/presence.log --log-ip raw --identities /var/lib/web3d/presence_identities.json --bans /var/lib/web3d/presence_bans.json --log-days 0 --history-file /var/lib/web3d/chat.jsonl --history-days 0
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

   Then `systemctl daemon-reload` and `systemctl enable --now web3d-presence`. **Tried here**: the file passes `systemd-analyze verify`; the `ExecStart` line started by hand under the `web3d` account starts, accepts the origin given to `--origins`, refuses another origin (HTTP 403) and writes into the log the IP sent in `X-Forwarded-For`. **Not tried here**: the start by systemd itself (no active systemd in the sandbox). The server's files are in `/var/lib/web3d/`: without the `--identities` and `--bans` options, the server writes next to the script, a folder the service account cannot modify (start-up error observed).
4. **Funnel** (syntax from the Tailscale documentation; not tried here, as root if needed): `tailscale funnel --bg --set-path=/presence http://127.0.0.1:8765` then `tailscale funnel --bg http://127.0.0.1:80`. The presence server accepts any path (tried with `/`, `/presence` and `/x/y`).
5. **Connect the page**: `--presence-url "wss://MACHINE.TAILNET.ts.net/presence"` (section "Connecting the pages"). The page is at `https://MACHINE.TAILNET.ts.net/`.
6. **Check**: `tailscale funnel status` lists both paths; open the page from a phone where Tailscale is switched off; read `presence.log` (control of the final step) and Apache's log.

### Debian 13 VM: permanent service with a moderation console (tried on 29/10/2026)
Way A on a Debian 13 VM (VMware, NAT network), published through Tailscale Funnel, page published on GitHub Pages. The service must start by itself **and** keep the moderation console (typed commands), which a plain systemd service cannot offer for lack of a keyboard.
1. **Install**: `python3`, `python3-websockets` and `tmux` come from `apt` (no virtual environment); Tailscale (`tailscale up`); publication with `tailscale funnel --bg 8765`. The origin of the page (`https://NOMDUSITE.github.io`) is declared in the VM's `presence_creators.json` (`--creators` option, no `--origins`).
2. **Server options**: `--host 127.0.0.1 --port 8765 --proxy-header X-Forwarded-For --log presence.log --log-ip raw --log-days 0 --history-file chat.jsonl --history-days 0 --visits visits.jsonl --creators presence_creators.json`. The author's choice: `--log-ip raw` and no time limit (strangers' IP addresses and messages are personal data, see "Keep in mind"; the server's defaults: `--log-ip hash` and 30 days).
3. **Start-up**: a systemd unit (`web3d-presence.service`, `Type=forking`, `Restart=always`, `RestartSec=5`) starts a `tmux` session named `presence` that runs a `lance_presence.sh` script. That script is a loop that restarts `presence_server.py` 5 seconds after it stops. The server thus keeps its console in the `tmux` session.

`lance_presence.sh`, in the server's folder (here `/home/UTILISATEUR/presence`, next to `presence_server.py`), made executable with `chmod +x lance_presence.sh`:

```bash
#!/bin/bash
# Lance le serveur de presence dans une boucle : s'il s'arrete, il repart apres 5 secondes.
# A ranger dans le dossier du serveur (a cote de presence_server.py), rendre executable : chmod +x lance_presence.sh
cd "$(dirname "$0")" || exit 1
while true; do
  python3 presence_server.py --host 127.0.0.1 --port 8765 --proxy-header X-Forwarded-For --log presence.log --log-ip raw --log-days 0 --history-file chat.jsonl --history-days 0 --visits visits.jsonl --creators presence_creators.json
  echo "Serveur arrete (code $?). Relance dans 5 secondes (pour l'arreter pour de bon : systemctl stop web3d-presence)."
  sleep 5
done
```

`/etc/systemd/system/web3d-presence.service` (replace `UTILISATEUR` with the VM's user):

```
[Unit]
Description=Web 3d presence server (console dans tmux)
After=network-online.target
Wants=network-online.target

[Service]
Type=forking
Restart=always
RestartSec=5
User=UTILISATEUR
WorkingDirectory=/home/UTILISATEUR/presence
ExecStart=/usr/bin/tmux new-session -d -s presence /home/UTILISATEUR/presence/lance_presence.sh
ExecStop=/usr/bin/tmux kill-session -t presence

[Install]
WantedBy=multi-user.target
```

Then `systemctl daemon-reload` and `systemctl enable --now web3d-presence`. These are the copies of the two files of the author's VM.

4. **Console**: under the VM's user (not `root`), `tmux attach -t presence`; from the PC, `ssh -t UTILISATEUR@ADRESSE_VM "tmux attach -t presence"` (copy and paste work); to leave without stopping the server: **Ctrl+B** then **D**; to stop it for good: `systemctl stop web3d-presence` (`root`).
5. **Update the server** after a `python build.py` that changes `presence_server.py`: send the file from `dist\` with `scp`, then `systemctl restart web3d-presence`. Then type `version` in the console: the revision shown must be that of the `REVISION` file at the root of the repository. The VM has **its own copy** of `presence_creators.json` and `presence_identities.json` (reserved names).
6. **Tried on 29/10/2026**: `reboot` (the `presence` session and the Funnel publication come back by themselves); `tmux kill-server` (the service comes back within a few seconds); a visitor from outside, from a GitHub Pages page.
7. **Debian 13 pitfalls**:
   - the `python` package no longer exists: `python3`;
   - the `cdrom` line of `/etc/apt/sources.list` makes `apt-get update` fail (remove it with `sed`) and **blocks** `apt-get update && apt-get install`: do not chain them;
   - `su` without the dash does not put `/usr/sbin` in the path (`usermod` not found): use `su -`;
   - `sudo` is not installed by default;
   - a service file **pasted** into the VM console was copied wrongly (no clipboard without the VMware extensions): sending it with `scp` is reliable.
8. **Seen twice (29/10/2026 and 30/10/2026), cause not established**: the VM console screen (VMware Workstation) goes black; `ssh` answers and the presence server runs, so only the display is at fault. On 30/10/2026, Ctrl+Alt+Del sent from VMware brought the login screen back. Ruled out on 30/10/2026: the desktop screen blanking (`idle-delay` already at 0) and the text console blanking (`consoleblank` at 0). The desktop session is Wayland and `open-vm-tools` is active; the only warning seen (`gsd-xsettings`) has no established link. If it comes back: first try an `ssh` connection before restarting, then, **before** Ctrl+Alt+Del, run `loginctl show-session 2 -p Active -p LockedHint -p IdleHint; journalctl -b --no-pager -p warning -n 40`. To read the whole journal, the user must be in the `systemd-journal` group (`usermod -aG systemd-journal UTILISATEUR`, as `root` with `su -`).

### Case: another service is already published (example: an LLM published by `tailscale serve` on port 443)
Do not run `tailscale funnel` on port 443: it would replace that service. Funnel also accepts ports 8443 and 10000 (Tailscale documentation): publish the page and the presence under the same name on port 8443, and the existing service keeps 443. **Proposed commands, not tried** (`PORT_PAGE` is the local port of the server that serves the page):
- `tailscale funnel --bg --https=8443 --set-path=/presence http://127.0.0.1:8765`
- `tailscale funnel --bg --https=8443 http://127.0.0.1:PORT_PAGE`
- presence started with `--host 127.0.0.1 --proxy-header X-Forwarded-For --origins "https://MACHINE.TAILNET.ts.net:8443"`
- presence address: `wss://MACHINE.TAILNET.ts.net:8443/presence`; page address: `https://MACHINE.TAILNET.ts.net:8443/`.

Before running anything: `tailscale serve status` and `tailscale funnel status`, then the same check afterwards.

### Connecting the pages (all four ways)
One region at a time: `glb2html.py --update -o "CHEMIN\X.html" --shared-shell --presence-url "wss://ADRESSE"` (the `--update` line of section 4 plus `--presence-url`). Or the `presenceUrl` key of `X.config.json`. The page's shell is not updated by `build.py`: redo `--update` for each region after a new version.

### Checking the address seen by the server (to do once, with `--log-ip raw`)
Open a page from a phone on 4G (not from your network, and with Tailscale switched off), then read `presence.log`: the address written must be the phone's. If you see `127.0.0.1` or the relay's address, the header given to `--proxy-header` is wrong or missing: **IP bans would not work**. The expected headers: `X-Forwarded-For` (Caddy, nginx, Tailscale Funnel: checked on 24/10/2026), `CF-Connecting-IP` (Cloudflare).

### To keep in mind
- `--origins` restricts connections to the pages of your site; without it, any page can connect to your server. Several sites: a comma-separated list.
- The existing limits stay active: `--max-per-ip` (10), `--max-per-room` (50), `--chat-burst`, messages of 4,096 bytes at most.
- Hiding the IP protects the machine, not the service: abuse (messages, nicknames) is handled by moderation (section 6, step 5). Run as a plain system service, the server has no keyboard: the solution that was tried (a `tmux` session started by systemd) is described above.
- The relay (Tailscale, Cloudflare) sees the decrypted traffic. Messages and addresses remain personal data: inform the visitors.
- Always restart the server after `python build.py` (section 6, step 6).
