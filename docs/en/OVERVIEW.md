# Web 3d: overview on one page

*State on 12/11/2026, version 1.10.0 (last release: 1.10.0, on 12/11/2026).*

An OpenSim region (`.oar` backup) becomes a **3D web page** you can walk around in, with nothing to install. Repository: `github.com/Klaatou/Web_3d` (MIT licence). This page says where things stand; the detail is in the manual, the technical state in `REPRISE.md`.

**Questions, help, news**: [Discord server](https://discord.gg/BDG9r5gXwr).

## 1. What works today

- **Building**: `tools/oar2glb.py` (OAR to GLB), `tools/glb2tiles.py` (splits huge regions into tiles and an overview), `glb2html.py` (the page); `extraire_batiments.py` and `iar2oar.py` (take one GLB per group of objects out of an OAR or an IAR); `web3d_gui.py` (opens all these tools in a window, with the help of the options and Windows shortcuts); `python build.py` puts everything in `dist\`.
- **Walking around**: walking, running, jumping, flying; first person, third person, free camera; collisions; named arrivals, zones, portals to another region; on-screen controls and touch mode.
- **Being several**: the presence server (`presence_server.py`): avatars, chat, visit log, hosted creators (`--creators`), console moderation.
- **Linking the worlds**: the world map (`regions.json`), the `carte.html` page with live visitors and the arrival alert (sound and marker), `--scan-sites` to build the list from the sites folder; `diag_carte.py` says why the map shows no nicknames.
- **Settings**: the Settings window (high resolution, light rendering, sea, sounds, window layout); French and English.
- **Exhibition pictures**: an `image` zone lays a picture on a wall; the files go in the region's `medias` subfolder, with no new conversion and no need to go through OpenSim; caption in the file name or in a `.txt` file; an image zone can open a page on click (`link`), and a Settings box shows the zone numbers to find the positions.
- **Animations, links, about**: an animated GIF animates in the page; the `url` and `image` zones also open a `hop://` link (virtual world); an "About the region" panel opens on entry (`?` key).
- **Ready-to-use packages**: `galerie-photos.zip` (a 3D gallery of 30 photos) and `region-simple.zip` (a region from a GLB), to download from the releases page; each opens with a double-click (Windows, macOS) or a command (Linux), with an optional presence server; sources in `paquets/`.
- **Online demo**: `https://klaatou.github.io/Web_3d_demo/` (several regions linked by portals, world map, presence).

## 2. What has been tried, and what has not

- **Tried**: Chromium (automatic tests), Edge and Klaatou's phone ("a bit crowded on a small screen, but it works"), the reference region of 1,024 x 1,024 m in 106 tiles, the latest batches (icon, mouse, G key, map, presence) on the online demo, the public presence server on a Debian 13 VM (Tailscale Funnel, page on GitHub Pages, visitor from outside, restarts of the VM and of the service), the `image` zone (automatic tests; by Klaatou on a real region: the pictures are displayed, choosing the region folder works); by Klaatou, `extraire_batiments.py` on a real region, `iar2oar.py` on a real IAR (then convoar and Blender), `diag_carte.py` against a real presence server, animated GIFs on Windows and in Firefox, and `web3d_gui.py` on Windows (the window, the tool list, the shortcuts with the project icon).
- **Tried by a third party (NightshadeCeres)**: Firefox 159.0.1 on macOS Ventura 13.7.8, with the `.command` launcher of the `region-simple` package: the region is displayed (the only result reported). The `galerie-photos` package, same launcher, has not been tried separately.
- **Not tried**: Safari, Firefox on Windows and Linux; Caddy and Cloudflare Tunnel (routes B and C); route D with Apache; `wss://` outside Funnel; a domain of one's own; the real sound (the tests simulate it); a `carte.html` tab kept in the background for a long time; the `image` zone in a tiled region; the editor's real folder picker on Windows and Edge; GIF animation in Safari (tried in Chromium, on Windows and in Firefox); the "Made with Web_3d" icon on Windows, in Firefox, Safari and on a real touch screen.

## 3. What is left to do

1. **Domain name**: for the presentation site and for a stable name for the presence server.
2. **Presentation page**: clickable GIF leading to the demo, a button to try it, contact, removal procedure, legal notices.
3. **Option to remove the "Made with Web_3d" icon** (key `credit`): to be decided in a few weeks.
4. **Ideas**: remaining media zones (music, page), pictures in a tiled region, GLB insertion, guest book (optional, can be external); extract each building of a large OAR into a separate GLB to recompose regions (done: `extraire_batiments.py`, the composition is done in Blender); mega-region (study in `docs/fr/ETUDE_MEGAREGION.md`, in French, nothing coded); animated PNG and WebP.

## 4. Where to read what

- `README.md`: presentation and getting started.
- `INDEX.md`: which document to read for what.
- The manual: all the detail (zones, options, server, what's new by version).
- `REFERENCE_JSON.md`: the meaning of each field of the JSON files.
- The procedures: step by step (publishing, server, network).
- `docs/REFERENCE_OPTIONS.md`: all the options of the tools.
- `deploy/`: the templates for the presence server's VM (`lance_presence.sh`, `web3d-presence.service`).
- `dist/convoar/`: convoar, the OAR converter of `oar2glb.py`, supplied (Windows only).
- `CHANGELOG.md` and the history: what changed and when.
- `REPRISE.md`: the technical state to resume the work.
