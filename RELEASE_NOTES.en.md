# GitHub Releases notes (English) — v35, v36, v37

Paste each section into the matching Release (`v35`, `v36`, `v37`).

## v35 (22/10/2026)
- **Firestorm-style controls**: P enters/leaves walking; run with Shift or a quick double-press on forward/back; Page Down/C to descend; Alt+click or End recenters the camera behind the avatar.
- **Third person**: the mouse orbits the camera without turning the avatar; the avatar turns smoothly toward its travel direction; camera distance 1–30 m, remembered. Presence sends the avatar's heading, not the camera's.
- **Free camera**: mouse wheel moves forward/back, Alt+drag orbits, key speed scales with distance; the camera never goes below the ground.
- **Help and Info windows** split into short groups, with collapsible title bars (state remembered).
- **Zone tooltips and labels** now reach 40 m by default (`--zone-info-dist`, 5–200 m); farther labels are hidden while walking.
- **Clipboard copy works over plain http** (fallback to a hidden textarea, then to a selected field).
- **`glb2html.py --maj` now handles the world map**: `--register`, `--map`, `--map-page`, `--thumb`… with paths relative to the page folder.

## v36 (23/10/2026)
- **Keys**: F and P both enter and leave walking; fly with Home, the button, or by holding Page Up > 0.4 s; E triggers the nearby zone again.
- **Keyboard layout (AZERTY/QWERTY)**: movement uses physical keys; help shows the real letters; auto-detected, overridable in Settings. M is recognised by its printed character.
- **Busy arrival**: a newcomer landing within 1 m of someone is moved to the nearest free spot (never someone who is walking).
- **Portal cones**: small cone above each portal/enter zone, shown up to `zoneInfoDist`; T toggles them (`--zone-cone`).
- **Sounds** (Web Audio, no files): volume, mention beep, join and leave sounds — walkers only, never the initial list.
- **Copy my position** as URL or `x, y, z`; "Go to" accepts a full address with `#pos=`.
- **Languages**: the page, the viewer and the Python tools are now in English and French (one JSON file per language; add a language by adding a file). `#lang=en`, `--lang`, `WEB3D_LANG`.

## v37 (23/10/2026)
- **Page**: run indicator, constant-size portal cones (visible up to 150 m by default, 5–500), arrival offset toward the nearest free spot facing the occupant, a quoted nickname keeps blinking until your first action, `&` or `#` both separate address parameters.
- **Compass** (top centre; OpenSim north = −Z, honours `rotate`): `--compass`, `--north DEG`. **O** opens Settings. Help and Info windows are resizable.
- **Chat history**: server `--history N` (200 by default), `--history-file`, `--history-days` (0 = keep all); the page has a scrollable panel, "Older messages", unread count in the tab title (reset when the chat is opened), "N messages quote you". The history file never stores IP addresses. Restart `presence_server.py` to benefit.
- **Default region**: with no `?region=`, the page's own `X.config.json`, then `default.json`, then the first relative entry of `regions.json`, otherwise a clear message. `?region=a/b/name` (subfolders) and `--shared-shell DIR/index.html` are supported.
- **`--lib-url`** places `lib/` elsewhere (kept for `--maj`); **`--default`** writes `default.json`.
