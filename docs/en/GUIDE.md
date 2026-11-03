# Creating and managing your region

*03/11/2026. For anyone who wants to put an OpenSim region in a web page: the path in order, from the simplest to the most complete. The § numbers refer to `MANUAL.md`. In the commands, `CHEMIN` is a path and `NOM` the name of the region.*

## 1. Getting your region in 3D

### 1.1 The simplest: a ready-made package

Two packages are on the releases page of the GitHub repository. Nothing to install to visit; the small local server needs Python 3.7 or later.

- `galerie-photos.zip`: a 3D photo gallery, ready to fill.
- `region-simple.zip`: an example region; you put your own `.glb` in it under the name `site\region.glb` to see it in the browser. It is also the simplest way to try a GLB you have just made (§ 1.2).

In each package, `lancer-…` opens the region (`.bat` on Windows, `.sh` on Linux, `.command` on macOS) and `renommer-…` changes its name. The package's `README.txt` and `readme.html` detail everything.

### 1.2 From your OAR: `oar2glb.py` (Windows only)

An OpenSim region backup (`.oar`) becomes a `.glb`, written next to the OAR.

- You need Python 3.8 or later and **convoar**: the whole `dist` folder of the `github.com/Misterblue/convoar` repository (`convoar.exe` alone does not work, it needs the DLLs of that folder), with .NET Framework 4.8, already present on Windows 10 and 11.
- Linux and macOS: not planned. convoar works with Mono, but `oar2glb.py` starts it through a small program built with a Windows tool; this case is neither planned nor tried.

```powershell
python oar2glb.py "CHEMIN\NOM.oar" --convoar "CHEMIN\convoar\dist\convoar.exe"
```

To try it: copy the GLB to `site\region.glb` of the `region-simple` package (§ 1.1). Options and troubleshooting: § 15.

### 1.3 Heavy region: split it into tiles

Beyond about 150 MB or 3 million triangles, the page must load the region in pieces. `--analyse` says whether to split, without writing anything:

```powershell
python glb2tiles.py "CHEMIN\NOM.glb" --analyse
```

The splitting, with the compression that makes the files about half the size (Node required):

```powershell
python glb2tiles.py "CHEMIN\NOM.glb" --compress
```

Details: § 17 and § 38.3.

## 2. Placing the zones: the viewer `glb-viewer.html`

The viewer opens in the browser; you open your `.glb` in it and place the zones: arrival point, portals, panels, links, images (§ 3 to 12). It saves `NOM.zones.json`, to put next to the page.

## 3. Making the page: `glb2html.py`

Two forms of page:

- **Standalone**: a single file `NOM.html` that contains everything, model included. Easy to send, but everything must be redone at each change.
- **With a shell** (`--shared-shell`): an `index.html` shared by all the regions of the folder, plus `NOM.glb`, `NOM.config.json` and `NOM.zones.json`; address `index.html?region=NOM`. To be preferred: several regions, settings that can be changed without redoing everything, tool updates, "About", world map.

```powershell
python glb2html.py "CHEMIN\NOM.glb" --shared-shell -o "CHEMIN\site\NOM.html" --title "Ma région"
```

| Option | Role |
|---|---|
| `-o` | file of the page (its name gives the name of the region) |
| `--shared-shell` | page with a shared shell |
| `--title` | title shown in the tab (§ 38.4) |
| `--sea-y` | height of the sea |
| `--presence-url`, `--room`, `--chat` | presence server, room, chat (§ 5) |
| `--tiles` | region split into tiles (§ 17 bis) |
| `--update` | bring a page up to a new version of the tools without retyping anything |

All the options: `REFERENCE_OPTIONS.md`.

## 4. Publishing

- Copy the page folder to a web host (GitHub Pages or any web server). A page opened by double-click does not work; to try it at home:

```powershell
python -m http.server 8000
```

  then open `http://localhost:8000/index.html?region=NOM`.
- File names in lowercase: a host tells capitals apart. The readable name goes in `title`.
- Optional: a presentation of the region in `NOM.about.fr.txt` (§ 38.2) and a world map (`--scan-sites`, § 32).

## 5. The other visitors: presence

Seeing the other walkers and chatting needs a presence server: that of a host who welcomes you (note `CREATEURS.md`, in English `CREATORS.md`), or your own (`presence_server.py`, `PROCEDURES.md` § 6 and § 11).

## 6. The tools and their role

All are in the `dist` folder of the repository.

| Tool | Role |
|---|---|
| `oar2glb.py` | OAR to GLB (Windows, with convoar) |
| `glb-stats.py` | quick analysis of a GLB (weight, extent, distribution), without loading it whole |
| `glb2tiles.py` | splits a big GLB into tiles, compression with `--compress` |
| `glb-viewer.html` | see a GLB, place the zones |
| `glb2html.py` | makes the page, updates it (`--update`), updates the map (`--scan-sites`) |
| `index.html` | the shared shell of the regions |
| `carte.html` | the world map as a page on its own |
| `presence_server.py` | presence server: positions, chat, moderation |
