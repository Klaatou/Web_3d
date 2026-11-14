# My procedures: sites and presence server

*03/11/2026. For the host (Klaatou): his published sites and his presence server. Creating a region: `GUIDE.md`. Deliveries and versions: `DEVELOPPEMENT.md` (in English: `DEVELOPMENT.md`). In the commands, `NOM` is the name of the region, `ANCIEN` and `NOUVEAU` the old and new name, `CHEMIN` a path, `UTILISATEUR` and `ADRESSE_VM` the account and address of the VM.*

## 1. Bring a published region up to a new version

To do after a new version of the tools: the page gets the new `index.html` shell (the old one is kept under a dated name) and its configuration is updated, without retyping anything; the zones do not move. Then Ctrl+F5 in the page.

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --update -o "P:\_OpenSim\SL&OS\Web_3d\Sites\houses\houses.html" --shared-shell "P:\_OpenSim\SL&OS\Web_3d\Sites\index.html"
```

## 2. Set the title shown in the tab

The same command with `--title "Houses"`, or by hand the line `"title": "Houses",` in `NOM.config.json`. The files and the room stay in lowercase.

## 3. Rename a region split into tiles

The script `renommer_region.py` (outside the repository, in `P:\_OpenSim\SL&OS\Web_3d`) renames the files and the tiles folder, and fixes the index, the configuration, `default.json`, the zone links and the card in `regions.json`. Every old file it modifies is copied to `_avant_renommage\` (one dated folder per run). The simulation first:

```powershell
python "P:\_OpenSim\SL&OS\Web_3d\renommer_region.py" "P:\_OpenSim\SL&OS\Web_3d\Sites\houses" ANCIEN NOUVEAU --dry-run
```

Then the renaming (add `--remplacer` if the new name already exists: the old file is set aside, never deleted):

```powershell
python "P:\_OpenSim\SL&OS\Web_3d\renommer_region.py" "P:\_OpenSim\SL&OS\Web_3d\Sites\houses" ANCIEN NOUVEAU
```

Finish with the map update (§ 4). The script can be run again: if the region is already renamed, it only makes the corrections.

## 4. Update the world map

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --scan-sites "P:\_OpenSim\SL&OS\Web_3d\Sites"
```

To also remove the cards whose region no longer exists (external cards are kept), add `--prune-missing`, preferably with `--dry-run` the first time:

```powershell
python .\glb2html.py --scan-sites "P:\_OpenSim\SL&OS\Web_3d\Sites" --prune-missing --dry-run
```

The names key is typed in the collapsed "Names key" block at the bottom of `carte.html`: the browser keeps it (`MANUAL.md` § 9.16). If the map shows no nicknames, `diag_carte.py` queries the presence server with and without the key and says what is missing (it needs `pip install websockets`; the site address at the end is only useful if the server only accepts some sites):

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\diag_carte.py wss://ADRESSE CLE https://VOTRE-SITE
```

Exit codes: 0 server fine, 1 unreachable, 2 old server, 3 no nickname with the key, 4 origin refused (`MANUAL.md` § 9.22).

## 5. Compress a big region already split

For a new region, `--compress` of `glb2tiles.py` is enough (`GUIDE.md` § 1.3). For tiles already split and not compressed: by hand, from the folder that contains `NOM.tiles`, into a `sortie` folder (Node required; never recompress a file that is already compressed):

```powershell
New-Item -ItemType Directory -Force ".\sortie" | Out-Null; Get-ChildItem ".\NOM.tiles" -Filter *.glb | ForEach-Object { npx -y gltfpack -i $_.FullName -o ".\sortie\$($_.Name)" -cc -kn -ke -km -vpf -vtf }
```

```powershell
npx -y gltfpack -i ".\NOM.overview.glb" -o ".\sortie\NOM.overview.glb" -cc -kn -ke -km -vpf -vtf
```

Then replace the files with those in `sortie`. Keep a backup first.

## 6. Extract objects from a region (buildings, furniture...)

The script `extraire_batiments.py` (in `web_3d\dist`) outputs one GLB per object group of the OAR, recentred, with a `.json` that keeps its original position. Its name comes from the buildings of a big OAR of houses it was written for, but **it is an object extraction**: a group can be a house, a piece of furniture, a tree, a vehicle. In its messages and files, "building" reads "object". It reads the OAR and the GLB made by `oar2glb.py`; the first reading is long, later ones come from a cache.

Run the script **from the working folder** `P:\_OpenSim\SL&OS\Web_3d`, not from `dist\`: the output folder `batiments` and the cache folder `extraire_batiments.cache` are created where the command is run. List the groups of at least 5 parts:

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d"; python ".\web_3d\dist\extraire_batiments.py" "CHEMIN\NOM.oar" "CHEMIN\NOM.glb" --list --min-parts 5
```

Extract by name (or `--group 12`, `--group 15,18,100-150`); `--ground 5` adds a test floor of 5 m around:

```powershell
python ".\web_3d\dist\extraire_batiments.py" "CHEMIN\NOM.oar" "CHEMIN\NOM.glb" --name "Jewel Box House" -o "CHEMIN\batiments"
```

The other options (delivery boxes, neighbours, merging, extracting everything): `--help` or `docs/REFERENCE_OPTIONS.md`. The old French option names (`--groupe`, `--nom`, `--sol`...) are still accepted. The cache moves with the command; it is read again only if the OAR, the GLB, `glb2tiles.py` and `oar2glb.py` have not changed (path, size, date). If the script is copied alone somewhere else, `--tools FOLDER` (or the `WEB3D_TOOLS` variable) says where `glb2tiles.py` and `oar2glb.py` are.

### Extract objects from an IAR (inventory)

The script `iar2oar.py` (in `web_3d\dist`, next to `oar2glb.py`) turns an inventory archive (IAR) into a minimal OAR, which the rest handles as a region: each inventory object gets a cell on a grid (the region grows in steps of 256 m if needed), combined objects are split into groups, the contents of boxes are added. See what the IAR contains (writes nothing; `--filter REGEX` and `--no-nested` narrow the list):

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d"; python ".\web_3d\dist\iar2oar.py" "CHEMIN\NOM.iar" --list
```

Make the OAR:

```powershell
python ".\web_3d\dist\iar2oar.py" "CHEMIN\NOM.iar" -o "CHEMIN\NOM.oar"
```

Make the GLB (`oar2glb.py` writes it next to the OAR, named `NOM.glb`; `--keep-invisible` keeps the transparent prims; convoar is supplied in `dist/convoar/`, no need to name it):

```powershell
python ".\web_3d\dist\oar2glb.py" "CHEMIN\NOM.oar"
```

Then list and extract as above, with `NOM.oar` and `NOM.glb`. The old French option names (`--liste`, `--filtre`, `--sans-imbriques`, `--marge`, `--sortie`) are still accepted. The texture errors from convoar ("could not fetch texture asset", "unhandled number of components") can come from the IAR itself (missing or empty assets, seen on the first IAR tried): the faces concerned are grey. Attachments and clothing are not supported.

On Linux, the command is the same with `python3` and `mono` installed (manual, § 3.11). If the OAR contains PBR (OpenSim 0.9.3), `oar2glb.py` applies it; Pillow (`pip install pillow`) is needed for the textures, and `--pbr-size 256` lightens the GLB (manual, § 3.10).

## 7. Update the online demo

To do when `index.html`, `carte.html` or the icon change. `ajout_og.py` (outside the repository) puts back into `index.html` the sharing preview tags (image and title shown when the link is shared); the path given is to be confirmed:

```powershell
Copy-Item "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\index.html", "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\carte.html", "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\favicon.ico" "P:\_OpenSim\SL&OS\Web_3d\Web_3d_demo"; cd "P:\_OpenSim\SL&OS\Web_3d\Web_3d_demo"; python "P:\_OpenSim\SL&OS\Web_3d\ajout_og.py"; git add index.html carte.html favicon.ico; git commit -m "mise a jour"; git push
```

## 8. The presence server on the VM

Open the moderation console from the PC; to leave it without stopping the server: Ctrl+B then D.

```powershell
ssh -t UTILISATEUR@ADRESSE_VM "tmux attach -t presence"
```

In the console: `version` gives the version and fingerprint of the server; `liste`, `ejecter`, `bannir`, `creators`, `aide`. Update the server **only** if the fingerprint shown by `version` differs from the one `python build.py` lists for `presence_server.py`: send the file, then, on the VM as root, `systemctl restart web3d-presence`.

```powershell
scp "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\presence_server.py" UTILISATEUR@ADRESSE_VM:/home/UTILISATEUR/presence/
```

Full installation of the VM: `PROCEDURES.md` § 11.

## 9. Host a creator on my presence server

What I send them (message to copy):

```text
To connect your region to my presence server (positions, chat), send me:
1. the origin of your page: the start of its address, without a path (for example https://alice.example; also give the www version if it works);
2. a short identifier (for example alice).
I reply with the server address (wss://...) and your room prefix (alice.NOM).
On your side, in NOM.config.json, set presenceUrl = the address you received and room = alice.NOM, then reload the page.
If presence is refused, the page says why (creators note, § 5).
```

What I do next:

- On the VM, open my copy of `presence_creators.json` and add the creator's entry (model: `docs/samples/presence_creators.sample.json`), for example `{"id": "alice", "origins": ["https://alice.example"]}`. No restart: the file is re-read within 2 seconds at most.
- In the console (§ 8), type `creators`: it lists the creator, their origins and their state.
- Send them the `wss://` address of my server, their prefix (`alice.`) and the creators note (`CREATEURS.md`, in English `CREATORS.md`).
- Optional: `visits-key alice.NOM` gives the key of their visits log, to send with the address of their page followed by `#visits`.

If their region is not yet in a web page: send them `GUIDE.md`.

## 10. Update a package that is already published

**Do not unzip the new zip over your folder**: the zip contains the example configuration, zones and images, which would overwrite yours.

For a package (`galerie-photos.zip`, `region-simple.zip`) put online from an older zip: download the new zip, unzip it somewhere else, then copy into the published `site` folder **only the HTML pages that depend on the version**: `index.html` and `carte.html`. Publish, then Ctrl+F5 in the page.

- **Do not overwrite**: `NOM.config.json`, `NOM.zones.json`, `NOM.glb`, `medias\`, `regions.json`, `vignette.jpg`, `NOM.about.*.txt`, and `aide.html` if you adapted it.
- **`aide.html`**: copy it from the new zip only if you have not changed it (it carries the new help texts); otherwise keep yours.
- **`favicon.ico`**: the new zip contains one (the logo since 1.6.14). Copy it only if you have not placed your own: a `favicon.ico` already next to the page is still preferred to the embedded icon, so the tab would keep the old icon.
- **Package from before 1.5.0**: the map (`carte.html`) reads `regions.json` and `vignette.jpg`, which it did not have; without them it says "Cannot read regions.json". Copy them too from the new zip, then adapt them.
- **`lib\` folder**: only if the `lib\three-…` folder of the new zip has a different name from yours.
- **Displayed number** (Status window, I key, "Version" line): the "page" is the version of `index.html` (it follows your copy); the "configuration" is the `version` key of `NOM.config.json`, which you can change by hand (the number is in `VERSION.txt` of the zip).
- **Presence server**: if you host it, replace `presence\presence_server.py` with the one from the new zip and restart it.

Tried (07/11/2026, Chromium on Linux): the current `index.html` opens without error a package whose config, zones and `default.json` date from 1.2.3; without `regions.json`, the map shows the message above. Not tried: Windows, other browsers, an update from a version other than 1.2.3.

## 11. Open the tools in a window, with shortcuts on the desktop

To avoid typing a command: a window offers the seven tools, with the help of every option (`MANUAL.md` § 3.9). From the root of the repository:

```powershell
python .\dist\web3d_gui.py
```

Under the tool list, the "Examples" list offers basic uses of each tool: choosing one fills the fields; all that is left is to replace the example names with your own, then click Run.

For shortcuts on the desktop (one for the window, one per tool), first what would be created, writing nothing:

```powershell
python .\dist\web3d_gui.py --shortcuts --dry-run
```

then, if the paths suit you:

```powershell
python .\dist\web3d_gui.py --shortcuts
```

![The eight shortcuts](../images/raccourcis.png)

Running the same command again replaces the shortcuts. To remove them: `python .\dist\web3d_gui.py --remove-shortcuts`. Tried by Klaatou on Windows (08/11/2026).

## 12. Fix the sea of an already published region

Since 1.10.26, a conversion places the sea from the OAR's water level. For a region published before, or whose sea looks too high or too low, without converting it again (the command reads the water level in the OAR and writes it into the region's config; its zones do not move):

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --update -o "P:\_OpenSim\SL&OS\Web_3d\Sites\houses\houses.html" --shared-shell "P:\_OpenSim\SL&OS\Web_3d\Sites\index.html" --water-from "J:\...\houses.oar"
```

Then Ctrl+F5 in the page. Without the OAR at hand, give the height yourself with `--sea-m 9` instead of `--water-from ...`: the number is the one that the Settings "Sea height" slider shows when the sea looks right (same frame). The choice made with that slider stays specific to each visitor (in his browser): only the config fixes the page for everyone.

For a whole folder of OARs, each with a region of the same name in the site (not tried):

```powershell
Get-ChildItem "J:\...\OAR" -Filter *.oar | ForEach-Object { $n = $_.BaseName; python .\glb2html.py --update -o "P:\...\Sites\$n\$n.html" --shared-shell "P:\...\Sites\index.html" --water-from $_.FullName }
```

An OAR without `WaterHeight` is refused with a message: the loop goes on, and those regions are set with `--sea-m`. Tried (14/11/2026, Chromium under Linux, `tests/mer_auto.py`): the single command.

## 13. Lighten the textures of an already converted region

To choose the value without guessing, read the size table: `oar2glb.py` prints it at the end of each conversion, and `glb-stats.py` gives it for a GLB that already exists:

```powershell
python .\glb-stats.py "J:\...\NOM.glb"
```

Then try values without doing the conversion again: each trial writes a new file beside it, the original is never modified:

```powershell
python .\oar2glb.py --tex-only "J:\...\NOM.glb" --tex-size 1024
```

Look at the result (`NOM-tex1024.glb`), then copy the chosen file over the region's GLB in the site. `--tex-quality 60` adds a stronger JPEG compression without changing the pixels; transparent textures are only reduced by `--tex-size`. Details: manual § 3.12. Tried (13/11/2026, fake convoar and hand-made GLBs): not tried on a real GLB of several hundred MB.
