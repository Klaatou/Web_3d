# Web 3d: overview on one page

*State on 31/10/2026, version 1.1.0.*

An OpenSim region (`.oar` backup) becomes a **3D web page** you can walk around in, with nothing to install. Repository: `github.com/Klaatou/Web_3d` (MIT licence). This page says where things stand; the detail is in the manual, the technical state in `REPRISE.md`.

## 1. What works today

- **Building**: `tools/oar2glb.py` (OAR to GLB), `tools/glb2tiles.py` (splits huge regions into tiles and an overview), `glb2html.py` (the page); `python build.py` puts everything in `dist\`.
- **Walking around**: walking, running, jumping, flying; first person, third person, free camera; collisions; named arrivals, zones, portals to another region; on-screen controls and touch mode.
- **Being several**: the presence server (`presence_server.py`): avatars, chat, visit log, hosted creators (`--creators`), console moderation.
- **Linking the worlds**: the world map (`regions.json`), the `carte.html` page with live visitors and the arrival alert (sound and marker), `--scan-sites` to build the list from the sites folder.
- **Settings**: the Settings window (high resolution, light rendering, sea, sounds, window layout); French and English.
- **Exhibition pictures**: an `image` zone lays a picture on a wall; the files go in the region's `medias` subfolder, with no new conversion and no need to go through OpenSim; caption in the file name or in a `.txt` file.
- **Online demo**: `https://klaatou.github.io/Web_3d_demo/` (two regions linked by portals, world map, presence).

## 2. What has been tried, and what has not

- **Tried**: Chromium (automatic tests), Edge and Klaatou's phone ("a bit crowded on a small screen, but it works"), the reference region of 1,024 x 1,024 m in 106 tiles, the latest batches (icon, mouse, G key, map, presence) on the online demo, the public presence server on a Debian 13 VM (Tailscale Funnel, page on GitHub Pages, visitor from outside, restarts of the VM and of the service), the `image` zone (automatic tests; by Klaatou on a real region: the pictures are displayed, choosing the region folder works).
- **Not tried**: Firefox and Safari; Caddy and Cloudflare Tunnel (routes B and C); route D with Apache; `wss://` outside Funnel; a domain of one's own; the real sound (the tests simulate it); a `carte.html` tab kept in the background for a long time; the `image` zone in a tiled region; the editor's real folder picker on Windows and Edge.

## 3. What is left to do

1. **Domain name**: for the presentation site and for a stable name for the presence server.
2. **Presentation page**: clickable GIF leading to the demo, a button to try it, contact, removal procedure, legal notices.
3. **GitHub release** of 1.1.0: tag `v1.1.0` and notes in English (the "1.1.0" entry of `CHANGELOG.md`), to be set by Klaatou.
4. **Ideas**: remaining media zones (music, page), pictures in a tiled region, GLB insertion, guest book (optional, can be external); extract each building of a large OAR into a separate GLB to recompose regions (a script exists, outside the repository).

## 4. Where to read what

- `README.md`: presentation and getting started.
- The manual: all the detail (zones, options, server, what's new by version).
- The procedures: step by step (publishing, server, network).
- `REFERENCE_OPTIONS.md`: all the options of the tools.
- `CHANGELOG.md` and the history: what changed and when.
- `REPRISE.md`: the technical state to resume the work.
