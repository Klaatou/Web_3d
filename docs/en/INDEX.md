# Documentation index

This page says **which document to read for what**. The French documents carry the same content under other names: `VUE_ENSEMBLE.md`, `MANUEL.md`, `PROCEDURES_SIMPLES.md`, `CREATEURS.md`, `DEVELOPPEMENT.md`, `CONVERTIR_OARS.md` and `HISTORIQUE.md`; `GUIDE.md`, `PROCEDURES.md`, `REFERENCE_JSON.md` and `INDEX.md` keep the same name. The "§" numbers are those of the headings of the document quoted.

## 1. Where to start

1. `README.md` (at the root): what the project is and the quick start.
2. `OVERVIEW.md`: what works, what has been tried or not, what remains to be done.
3. `GUIDE.md`: the getting-started guide, from the region to the published page.

## 2. By task

| I want to… | Where to read |
| --- | --- |
| get a region in 3D with nothing to install | `GUIDE.md` § 1.1; `PROCEDURES.md` § 12 |
| convert my OAR to GLB | `GUIDE.md` § 1.2; `MANUAL.md` § 3; `PROCEDURES.md` § 1 |
| handle a heavy region (tiles) | `GUIDE.md` § 1.3; `MANUAL.md` § 4 and § 8; `PROCEDURES.md` § 2 |
| compress a region already cut up | `MANUAL.md` § 4.2; `SIMPLE_PROCEDURES.md` § 5 |
| extract objects (buildings, furniture...) from a region | `MANUAL.md` § 3.7; `SIMPLE_PROCEDURES.md` § 6 |
| extract objects from an inventory (IAR) | `MANUAL.md` § 3.8; `SIMPLE_PROCEDURES.md` § 6 |
| turn a folder of OARs into a web site, one region after the other | `CONVERT_OARS.md` |
| fix the sea of an already published region | `SIMPLE_PROCEDURES.md` § 12; `MANUAL.md` § 3.13 |
| lighten the textures of a region | `SIMPLE_PROCEDURES.md` § 13; `MANUAL.md` § 3.12 |
| place zones (arrivals, portals, signs, pictures) | `GUIDE.md` § 2; `MANUAL.md` § 5; `PROCEDURES.md` § 5 |
| build or update the page | `GUIDE.md` § 3; `MANUAL.md` § 6; `PROCEDURES.md` § 3, § 4 and § 8; `SIMPLE_PROCEDURES.md` § 1 |
| set the tab title, rename a tiled region | `SIMPLE_PROCEDURES.md` § 2 and § 3 |
| publish, update the online demo | `GUIDE.md` § 4; `SIMPLE_PROCEDURES.md` § 7 |
| know what the visitor can do (keys, flight, chat) | `MANUAL.md` § 7; `PROCEDURES.md` § 10 |
| link several regions with a world map | `MANUAL.md` § 9; `PROCEDURES.md` § 7; `SIMPLE_PROCEDURES.md` § 4 |
| understand why the map shows no nicknames | `MANUAL.md` § 9.22; `PROCEDURES.md` § 7; `SIMPLE_PROCEDURES.md` § 4 |
| open the tools in a window, create shortcuts on the desktop | `MANUAL.md` § 3.9; `SIMPLE_PROCEDURES.md` § 11 |
| convert an OAR that contains PBR (OpenSim 0.9.3) | `MANUAL.md` § 3.10 |
| convert an OAR on Linux (Mono) | `MANUAL.md` § 3.11 |
| set the metal reflections (PBR) in the page | `MANUAL.md` § 7.65 |
| remove the "Made with Web_3d" icon | `MANUAL.md` § 7.62 |
| type the names key of the map | `MANUAL.md` § 9.16 |
| set the sea height in the page | `MANUAL.md` § 9.19 |
| ask a question, get help | the Discord server: https://discord.gg/BDG9r5gXwr |
| see other visitors, chat, moderate | `GUIDE.md` § 5; `MANUAL.md` § 10; `PROCEDURES.md` § 6 |
| install the presence server on a VM | `SIMPLE_PROCEDURES.md` § 8; `PROCEDURES.md` § 11 |
| make the presence server public without showing my IP address | `PROCEDURES.md` § 11 |
| welcome a creator on my server | `SIMPLE_PROCEDURES.md` § 9; `MANUAL.md` § 10.10 |
| use somebody else's presence server | `CREATORS.md` |
| open a `hop://` link | `PROCEDURES.md` § 13 |
| build the ready-to-use packages (zips) | `PROCEDURES.md` § 12 |
| update a package that is already published | `SIMPLE_PROCEDURES.md` § 10 |
| understand a failure | `PROCEDURES.md` § 9; `MANUAL.md` § 12 |

## 3. References

| I am looking for… | Where |
| --- | --- |
| all the options of every tool, in English and in French | `docs/REFERENCE_OPTIONS.md`; the tool's `--help` |
| the meaning of each field of a JSON file | `REFERENCE_JSON.md` |
| a complete example of each JSON file | folder `docs/samples/` |
| the French option names from before v43 | `REFERENCE_JSON.md` § 11.11 |

## 4. The state of the project and the work on the code

| I want to know… | Where |
| --- | --- |
| what has been tried, and what has not | `OVERVIEW.md` § 2 |
| what changed, and when | `CHANGELOG.md` (at the root); `HISTORY.md`; `MANUAL.md` § 13 |
| how to apply a delivery, build, test, publish a version | `DEVELOPMENT.md` § 1 to § 5 |
| how to edit the README diagrams | `DEVELOPMENT.md` § 6 |
| the technical state to resume the work | `REPRISE.md` (at the root) |
