# Turn a folder of OARs into a web site (`oars2site.py`)

`oars2site.py` turns a folder of OpenSim region backups (`.oar`, `.tgz`) into a complete web site, one region after the other. It only runs the existing tools, in this order: `oar2glb.py`, `glb2tiles.py`, `glb2html.py` (shared shell mode), then the update of the world map. It changes neither the OARs nor the tools.

## 1. What you need

- Python 3 and Pillow (`pip install pillow`).
- The tools `oar2glb.py`, `glb2tiles.py` and `glb2html.py`: they are in `dist/`, beside `oars2site.py`. On Linux, see `MANUAL.md` § 3.11 (convoar with Mono).
- Disk space and time: converting an OAR is heavy (§ 8).

## 2. Run it

One PowerShell line, the first folder holds the OARs, the second one will be the site:

```powershell
python .\oars2site.py "P:\chemin\OAR" "P:\chemin\site"
```

To see what would be done, without writing anything:

```powershell
python .\oars2site.py "P:\chemin\OAR" "P:\chemin\site" --dry-run
```

The OARs are processed one at a time, never in parallel. An OAR that is already converted (its `NOM.config.json` is newer than the OAR) is skipped; an OAR that fails is noted in its log, leaves no half-made folder if the region is new, and the next one goes on. The exit code is 1 if at least one OAR failed.

## 3. What is produced

In the site folder:

- `index.html`, `lib/`, `default.json` and `regions.json` at the root: the shared shell, created once then kept up to date; `regions.json` feeds the world map;
- `carte.html` at the root: the world map page, copied at the start if it does not exist (a map already there is never overwritten);
- one folder per region, `NOM/`, with `NOM.config.json`, `NOM.zones.json` and the GLB: `NOM.glb`, or `NOM.tiles.json`, `NOM.tiles/` and `NOM.overview.glb` when `glb2tiles.py` decides that tiles are needed (heavy regions);
- a region is then at the address `index.html?region=NOM/NOM`, served by any static web server.

The region name comes from the file name, reduced to letters, digits, `_` and `-`: `Plage Sud.oar` gives `Plage_Sud`. Two OARs that give the same name stop the tool before any work.

## 4. The main options

| Option | Effect |
| --- | --- |
| `--only` | regular expression: only the OARs whose name matches |
| `--tex-size` | reduces the ordinary textures to N pixels on a side at most (§ 5) |
| `--tex-quality` | compresses the ordinary textures as JPEG of quality Q (§ 5) |
| `--pbr-size` | maximum side of the PBR textures (default 512) |
| `--split` | `auto` (default: `glb2tiles.py` decides), `never` (a single GLB) or `always` (tiles) |
| `--thumbs` | folder of thumbnails `NOM.jpg`, `NOM.png` or `NOM.webp` for the world map |
| `--force` | redoes the regions already converted (overwrites their config and zones) |
| `--reuse-glb` | uses a `NOM.glb` already beside the OAR instead of running `oar2glb.py` |
| `--keep-work` | keeps the work files of each region |
| `--work` | work and log folder (default: beside the site) |
| `--timeout-min` | stops one step after this many minutes |
| `--vendor` | local three.js folder, to work offline |
| `--tools` | folder of the three tools (default: beside the script, then `dist`) |
| `--oar2glb-arg`, `--html-arg` | extra argument passed to `oar2glb.py` or to `glb2html.py` (repeatable) |
| `--lang` | language of the messages: `fr`, `en` or `auto` |

Every option, with its default value: `docs/REFERENCE_OPTIONS.md`.

## 5. Setting the textures

`--tex-size` changes the number of pixels; `--tex-quality` sets the JPEG compression without changing the pixels; the two can be combined. The GLB gets lighter and the textures are less useful to whoever saves them; the geometry is not touched and the region looks softer up close. Transparent textures stay PNG (reduced if they are too large, never recompressed) and the images of PBR materials are not concerned.

To choose N without guessing:

1. At the end of each conversion, `oar2glb.py` prints the number and weight of the ordinary textures by longest-side range, before any reduction. It is in the region's log, `NOM_work/logs/NOM.log`. Example (test images):

```
[textures] 3 ordinary textures, 0.9 MB (largest side: 512 px), original sizes:
    up to 256 px: 1 textures, 0.0 MB
    257 to 512 px: 2 textures, 0.9 MB
```

2. For a GLB that already exists, `glb-stats.py NOM.glb` gives the same table.
3. To try values without redoing the conversion, `oar2glb.py --tex-only NOM.glb --tex-size 1024` writes `NOM-tex1024.glb` beside the original, which is never modified, and prints the weight before and after and the time it took. Then copy the chosen file over the region's GLB in the site.

## 6. Logs and report

The work files and the logs are written outside the site folder (by default `SITE_NAME_work`, beside it), so that they are never served by the web server:

- `logs/NOM.log`: everything the tools printed for the region, in the script's language;
- `logs/_scan-sites.log`: the update of `regions.json`;
- `conversion_report.json`: for each OAR, its state (`ok`, `skipped` or `failed`), its address, its mode (`glb` or `tiles`) and its duration, for a site's own scripts to use.

A region's work folder is removed at the end, including after a failure: the log is enough to understand.

## 7. The published GLB can be downloaded

The page loads the region by downloading its GLB (or its tiles) and its JSON files over plain HTTP. Web_3d neither encrypts nor hides them: anyone who can open the page can save the GLB, with the geometry and the textures of the OAR, and an unreadable region name changes nothing, because `default.json` gives it.

For paid OARs, it is therefore up to you to decide what you accept to show:

- degrade the textures (§ 5);
- show only free OARs or a preview region;
- on the web server, outside Web_3d: require a login for the site folder, or refuse the requests that do not come from your own pages (this stops links from other sites, not a determined visitor).

## 8. Limits and what is not tried

- A single load measurement: an OAR of 1.45 GB took about 2 min 12 s with `--pbr-size 256`, under Windows, and memory rose to 61 GB (cause not established). Run the largest OARs first as a trial, one at a time.
- Tried with a fake convoar only: a folder of OARs converted into a site, an OAR skipped, a failure that does not block the others, tiles then back to a single GLB, thumbnails, `carte.html` copied, a `glb2html.py` failure without a half-made folder, texture options, languages, a time limit exceeded.
- Not tried: a real OAR with the real convoar, Windows, macOS, and a large region through the tiles path.
