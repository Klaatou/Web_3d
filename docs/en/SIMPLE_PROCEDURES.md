# Simple procedures

*03/11/2026. The everyday tasks, one command per block, to copy as written (PowerShell). The details are in `PROCEDURES.md` and `MANUAL.md`. In the commands, `NOM` is the region name, `ANCIEN` its old name, `NOUVEAU` its new name, `CHEMIN` a path, `MESSAGE` a commit message.*

## 1. Apply a delivery

Fetch and apply the patch (dry run first):

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d\web_3d"; git pull; python .\patch_NOM.py --dry-run; if ($LASTEXITCODE -eq 0) { python .\patch_NOM.py }
```

Build and check. Without this step, `dist\` stays at the old version:

```powershell
python build.py; python .\tests\dist_a_jour.py
```

Publish: the status first, then everything:

```powershell
git status --short
```

```powershell
git add -A; git commit -m "MESSAGE"; git push
```

## 2. Update the page of a published region

Keeps the configuration and the zones, renews the `index.html` shell if it is older. Add `--title "Houses"` to set the title shown in the tab (the files and the room stay in lowercase). Then Ctrl+F5 in the page.

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --update -o "P:\_OpenSim\SL&OS\Web_3d\Sites\houses\houses.html" --shared-shell "P:\_OpenSim\SL&OS\Web_3d\Sites\index.html"
```

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

## 5. Split and compress a big region

New region: split with compression (Node required, `gltfpack` is started by `npx`):

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2tiles.py "CHEMIN\Region.glb" --compress
```

Tiles already split and not compressed: by hand, from the folder that contains `NOM.tiles`, into a `sortie` folder (never recompress a file that is already compressed):

```powershell
New-Item -ItemType Directory -Force ".\sortie" | Out-Null; Get-ChildItem ".\NOM.tiles" -Filter *.glb | ForEach-Object { npx -y gltfpack -i $_.FullName -o ".\sortie\$($_.Name)" -cc -kn -ke -km -vpf -vtf }
```

```powershell
npx -y gltfpack -i ".\NOM.overview.glb" -o ".\sortie\NOM.overview.glb" -cc -kn -ke -km -vpf -vtf
```

Then replace the files with those in `sortie`. Keep a backup first.

## 6. Update the online demo

Do this when `index.html`, `carte.html` or the icon change (the path of `ajout_og.py` is to be confirmed):

```powershell
Copy-Item "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist\index.html" "P:\_OpenSim\SL&OS\Web_3d\Web_3d_demo"; cd "P:\_OpenSim\SL&OS\Web_3d\Web_3d_demo"; python "P:\_OpenSim\SL&OS\Web_3d\ajout_og.py"; git add index.html; git commit -m "mise a jour"; git push
```

## 7. Host a creator on my presence server

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
- In the server console (`tmux attach -t presence`), type `creators`: it lists the creator, their origins and their state.
- Send them the `wss://` address of my server and their prefix (`alice.`).
- Optional: `visits-key alice.NOM` gives the key of their visits log, to send with the address of their page followed by `#visits`.

If they do not have a GLB yet:

- They already have a `.glb`: the `region-simple.zip` package (releases page of the GitHub repository) shows it without installing anything.
- They only have an OAR: the conversion needs `convoar.exe` (Windows) and `oar2glb.py`. The simplest is that they send me the OAR, that I convert it (§ 5) and send the region files back. The OAR to GLB conversion has so far only been tried by Klaatou.
