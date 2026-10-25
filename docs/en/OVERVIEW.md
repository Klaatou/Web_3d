# Web 3d: overview on one page

*State on 25/10/2026, version v52.*

An OpenSim region (`.oar` backup) becomes a **3D web page** you can walk around in, with nothing to install. Repository: `github.com/Klaatou/Web_3d` (MIT licence). This page says where things stand; the detail is in the manual, the technical state in `REPRISE.md`.

## 1. What works today

- **Building**: `tools/oar2glb.py` (OAR to GLB), `tools/glb2tiles.py` (splits huge regions into tiles and an overview), `glb2html.py` (the page); `python build.py` puts everything in `dist\`.
- **Walking around**: walking, running, jumping, flying; first person, third person, free camera; collisions; named arrivals, zones, portals to another region; on-screen controls and touch mode.
- **Being several**: the presence server (`presence_server.py`): avatars, chat, visit log, hosted creators (`--creators`), console moderation.
- **Linking the worlds**: the world map (`regions.json`), the `carte.html` page with live visitors and the arrival alert (sound and marker), `--scan-sites` to build the list from the sites folder.
- **Settings**: the Settings window (high resolution, light rendering, sea, sounds, window layout); French and English.

## 2. What has been tried, and what has not

- **Tried**: Chromium (automatic tests), Edge and JJ's phone ("a bit crowded on a small screen, but it works"), the reference region of 1,024 x 1,024 m in 106 tiles.
- **Not tried**: Firefox and Safari; route D (Linux VM, Tailscale Funnel, Apache); `wss://` behind Funnel; a creator from another origin; the real sound (the tests simulate it); a `carte.html` tab kept in the background for a long time.

## 3. What is left to do

1. **Test from the VM**: access through Tailscale, and a creator from another origin (`--creators`).
2. **A note for the creators** hosted on the presence server, written after that test.
3. **Mouse**: capture it only on purpose (button or G), removing the capture on click.
4. **Public demo**: candidate region Hobbit (small, it opens by itself); configuration without an IP address; GitHub Pages does not run PHP.
5. **Numbering**: move to `1.0.0` after the tests above (proposed, not decided).
6. **GitHub release** with notes in English (to be decided).
7. **Ideas**: show an image or a page on an object, play music when entering a zone (studied, not started); guest book (optional, can be external).

## 4. Where to read what

- `README.md`: presentation and getting started.
- The manual: all the detail (zones, options, server, what's new by version).
- The procedures: step by step (publishing, server, network).
- `REFERENCE_OPTIONS.md`: all the options of the tools.
- `CHANGELOG.md` and the history: what changed and when.
- `REPRISE.md`: the technical state to resume the work.
