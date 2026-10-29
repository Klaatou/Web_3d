# File examples (`docs/samples/`)

This folder holds **one example of each JSON file** that the page, the viewer, the tools and the presence server read or write. A JSON file cannot hold comments: the meaning of each field is explained in `MANUAL.md` § 27. What you find here are **real files, complete and valid**.

**Using them**: copy the example, rename it, change the values. In the examples the region is called `Region`: for a region "Ankh", `region.config.sample.json` becomes `Ankh.config.json` and `Ankh` replaces `Region` in the values that contain it (`room`, `tiles`, the addresses). The addresses are written `ADRESSE`: put yours. The `tests/samples.py` test checks that each example is accepted by the real code that reads it: they therefore stay correct when the code changes.

## Files of a region and of the site

| Example | Real file | What it is for | Manual |
| --- | --- | --- | --- |
| `region.config.sample.json` | `NOM.config.json` | the settings the page reads at start-up (sea, walking, chat, presence, map, tiles); written by `glb2html.py`; flat | § 27.3 |
| `region.zones.sample.json` | `NOM.zones.json` | the zones: arrivals, portals, web links, Home Assistant | § 27.4 |
| `region.tiles.sample.json` | `NOM.tiles.json` | the tile index of a large region, written by `glb2tiles.py`; not to be edited by hand | § 27.7 |
| `region.reglages.sample.json` | `NOM.reglages.json` | the viewer's working state, written by the "Save to a file" button: the settings, **all** the zones (private ones included), the camera framing, the region's card for the map and the command summary; nested; read back by the viewer and by `glb2html.py --settings` | § 27.8 |
| `default.sample.json` | `default.json` | the region opened when the address has no `?region=` | § 27.5 |
| `regions.sample.json` | `regions.json` | the world map: one card per region (name, place, address, presence, thumbnail) | § 27.6 |
| `disposition.sample.json` | `disposition.json` | the place of the help, information and arrivals windows, saved by the page's Settings | § 27.9 |

## Files of the presence server

| Example | Real file | What it is for | Manual |
| --- | --- | --- | --- |
| `presence_identities.sample.json` | `presence_identities.json` | the reserved nicknames, kept as fingerprints | § 27.10 |
| `presence_bans.sample.json` | `presence_bans.json` | the bans set by the `bannir` command (key and address as fingerprints, optional end) | § 27.10 |
| `chat_history.sample.jsonl` | file of `--history-file` | the chat history, one line per message | § 27.10 |
| `visits.sample.jsonl` | file of `--visits` | the visit log, one line per visit, no IP address | § 27.10 |
| `presence_visits_keys.sample.json` | `presence_visits_keys.json` | the keys (as fingerprints) that give access to a room's visit log, `visits-key` command | § 27.10 |
| `presence_creators.sample.json` | `presence_creators.json` | the hosted creators (`--creators`); written by hand | § 34 |

## What never goes into the tools' repository

The real files (not these examples) `*.zones.json` and `zones*.json` (Home Assistant addresses), `*.reglages.json` (private zones included), `regions.json`, `presence_identities.json`, `presence_bans.json`, `presence_visits_keys.json`, `presence_creators.json`, the logs and the `*.jsonl` files (chat history, visit log). The `.gitignore` excludes the usual ones.
