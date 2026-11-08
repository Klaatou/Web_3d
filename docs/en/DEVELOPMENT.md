# Development: deliveries and versions

*03/11/2026. For whoever maintains the repository (Klaatou). The state of the work is in `REPRISE.md`. In the commands, `NOM` is the name of the patch or test, `MESSAGE` the commit message, `X.Y.Z` the version number.*

## 1. Apply a delivery

The delivered files go at the root of the repository; a new file (test, document) is put in place by the line given with the delivery (`Move-Item`). Dry run first:

```powershell
cd "P:\_OpenSim\SL&OS\Web_3d\web_3d"; git pull; python .\patch_NOM.py --dry-run; if ($LASTEXITCODE -eq 0) { python .\patch_NOM.py }
```

Every patch keeps a copy of the files it modifies in `_bak\` and refuses to be applied twice.

## 2. Build and check

Without this step, `dist\` stays at the old version. `python build.py` shows the number of every file: only a file whose content changed takes the batch number.

```powershell
python build.py; python .\tests\dist_a_jour.py
```

## 3. Publish on GitHub

The list of files is shown, then everything goes:

```powershell
git status --short; git add -A; git commit -m "MESSAGE"; git push
```

## 4. Run a test

One test at a time, never several at once:

```powershell
python .\tests\NOM.py
```

The full suite has more than 70 files and takes long. Already failing in the sandbox and in cloud sessions: `doc_options`, `image_dossier`, `marque`.

## 5. Publish a version

Klaatou's decision. A delivery sets `VERSION` to the version number (minor + 1 if features were added since the previous one). When everything is pushed:

```powershell
python .\fabriquer_paquets.py; git tag vX.Y.Z; git push origin vX.Y.Z
```

Then, on GitHub, create the release of the tag `vX.Y.Z` with the two zips of the `paquets-zip\` folder attached.

## 6. README images

The diagrams in `README.md` and `README.fr.md` are **hand-drawn SVGs** kept in `docs/images/`: `fonctionnement.fr.svg` and `fonctionnement.en.svg` (the tool chain, "How it works" section), `site.fr.svg` and `site.en.svg` (the tree of a site, as an explorer window). No script in the repository produces them: an SVG is text, so it is edited by hand (texts, positions, legend) and then looked at in a browser. The two languages are kept up to date together. Nothing in them is carried by colour alone (outlines, dotted lines, numbers, legend). The folder also holds the demonstration GIF (`PalmIsland_demo.gif`) and `carte.jpg`.

Check: `python .\tests\readme_liens.py` verifies that every image and every relative link in the two READMEs and in the documents of `docs/` points to a file that exists (it was written after the demonstration GIF vanished, swept away by a `git add -A`). It does not judge the drawing: the rendering was only looked at in Chromium, not on GitHub.
