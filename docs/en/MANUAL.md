# User manual: zones, portals and arrival points (v52)

> **Summary (v52).** This file is the detailed user manual; it is not meant to be read from end to end. For **all the options** of the tools, with their effect and their default, in French and English: `REFERENCE_OPTIONS.md` (generated from the tools by `gen_reference.py`). To **do a task step by step** (OAR to page, tiled region, update, zones, presence server, map): `PROCEDURES.md`. Here: zones and portals (§§ 1 to 10), keys (§ 2), settings and their files (§§ 11 to 19) and the new features version by version (§§ 18 to 34; § 27 is the JSON file reference). Language of the page and of the tools: § 21.8 to 21.11.

## 1. The rule that explains 90 % of failures

Each zone has two names:

| Field              | What it is for                              | Who reads it                            |
| ------------------ | ------------------------------------------- | --------------------------------------- |
| **Identifier**     | the technical name of the zone              | portals, the world map, `#spawn=` links |
| **Displayed name** | the text seen by the visitor ("E: Emperor") | the screen only                         |

**A portal always designates an arrival by its Identifier, never by its Displayed name.**
The identifier is automatically lowercased, and any character other than an unaccented letter, a digit, `-` or `_` becomes a hyphen (`Salle du Trône` becomes `salle-du-tr-ne`). Write it directly in lowercase, without accents or spaces, to avoid surprises.

Correct example:

- Arrival: Identifier `empereur`, Displayed name `Salle de l'Empereur`
- Portal: Arrival point `empereur`

## 2. The keys

| Key                                    | Effect                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **F** (v36)                            | **enters and leaves walk mode**, from the global view as from walk mode (like **P**); flight is toggled with **Home** (in v35, F toggled flight). **When leaving (v31)**, the small landing circle and the target of the global view are placed **on the ground, under the last place where the avatar was**; the camera comes back at the **same distance and in the same direction** from this target as before entering walk mode (it no longer returns to the exact spot you had left from). In tiles mode, the tiles around the avatar therefore stay loaded. |
| **P** (v35)                            | **enter or leave walk mode** (the "Walk (P)" button stays in the global view; there is no "Leave the walk" button any more). In the **viewer**, P places a zone in walk mode: leave with **F**, **Shift+P** or the button                                                                                                                                                                                                                                                                                                                                          |
| **E** (v36)                            | **triggers the nearby zone** (trigger "on click" or "both", as before v35; a "walking into it" portal fires when entering its radius, § 8). The name of the nearby zone is shown at the bottom: "click or E: …". **E does nothing else** (it no longer jumps nor goes up)                                                                                                                                                                                                                                                                                          |
| **Page Up** (v35)                      | **short press on the ground = jump** (like Space); **held more than 0.4 s on the ground = take off**; in flight, held = go up                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| **Space** (v36)                        | on the ground: jump; **in flight, held: go up**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| **T** (v36)                            | shows or hides the **portal markers** (small cones, § 21.4); the choice is remembered                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **Home** (v33)                         | take off or land (toggle; v36: F no longer toggles flight). In flight: **Page Up** or **Space** held goes up, **C** / **Page Down** goes down, no gravity, walls stay solid, never below the ground. Can be removed with `--no-fly` (§ 18.4)                                                                                                                                                                                                                                                                                                                       |
| **M** (v35)                            | **in walk mode: toggles first person / third person**; outside walk mode: opens the world map (as before). **Ctrl+M opens the world map everywhere**. **v36: the key is recognised by the printed letter "m"**, not by its position: on an AZERTY keyboard it is the real M key (before, it was the "," key)                                                                                                                                                                                                                                                       |
| **End**, **Alt + click** (v35)         | put the camera back **behind the avatar** (third person). **Alt + drag** orbits the camera (in third person the mouse already orbits; in first person, Alt + drag looks around like the mouse)                                                                                                                                                                                                                                                                                                                                                                     |
| **wheel** (v35)                        | in walk mode, the page does not scroll. **Third person**: sets the camera distance (1 to 30 m, 4 m by default, remembered); **free camera**: moves the camera forwards / backwards along the line of sight; first person: nothing (§ 20.9)                                                                                                                                                                                                                                                                                                                         |
| **double press** on W, S, ↑ or ↓ (v35) | **running** as long as the key stays down (two presses less than 300 ms apart); **Shift** still runs. No permanent running (Ctrl+R reloads the page)                                                                                                                                                                                                                                                                                                                                                                                                               |
| **V** (v33)                            | change view: first person → third person → free camera → first person. The current view is written as text in the status block ("View: …", v34)                                                                                                                                                                                                                                                                                                                                                                                                                    |
| **R** (v33)                            | **back to the arrival point**: in walk mode, teleports to the `default` arrival (failing that, to the starting target) while waiting for the tile; in the global view, reframes the target and the camera on this point. The "Back to the arrival point (R)" button does the same                                                                                                                                                                                                                                                                                  |
| **Enter** (v33)                        | open the chat input; **Enter sends and keeps the input open**, **Esc** closes it. The arrows keep moving the avatar (§ 18.5)                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **Page Up** / **Page Down** (v34)      | in flight, go up / down (in addition to **Space** held / **C**, v36); the page does not scroll. **Going down to the ground lands the avatar**: flight stops by itself. "Fly / Land" button in the bottom bar for those who have no Home key (§ 19.3)                                                                                                                                                                                                                                                                                                               |
| **Esc** (v34)                          | releases the mouse in walk mode. The mouse then stays **free** (a click or a double-click no longer grabs the pointer) until **G** or the "Capture the mouse" button (§ 19.4)                                                                                                                                                                                                                                                                                                                                                                                      |
| **G** (v34)                            | capture the mouse again after Esc                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **O** (v37)                            | opens / closes the **Settings** window (toggle, like **H** and **I**); **R** is already taken by the return to the arrival point                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **I** (v34)                            | the **Information / Status** window (v36: formerly the "status block": view, mode, mouse, keyboard, position, tiles): hidden → expanded; collapsed → expanded; expanded → hidden. **H** does the same for the help alone (§ 19.1, § 21.3)                                                                                                                                                                                                                                                                                                                          |
| **K** (v46)                            | shows or hides the **on-screen arrows** (like the "Arrows (K)" button and the Settings checkbox; remembered by the browser; same place on AZERTY and QWERTY, § 29.3)                                                                                                                                                                                                                                                                                                                                                                                               |
| **L** (v40)                            | the **Arrivals** window: list of the region's teleport points; clicking a name teleports there (in walk mode) or enters walk mode there (in global view). Same cycle as **H** and **I**; absent if the region has no arrival point                                                                                                                                                                                                                                                                                                                                 |

Portals only work in walk mode.

### Click and double-click (global view of the viewer)

| Gesture                       | Effect                                                                                                                                                                                                                                 |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **single click** on the model | shows, in the "picked" block and the status bar, the **name of the element** and the **coordinates of the touched point** (x, y, z, 2 decimals). Nothing moves: neither the target nor the landing circle.                             |
| **double-click** on the model | chooses the **target** of the view and the **landing point** (as in the exported page). In tiles mode (§ 17 bis), the double-click also works on the **overview**: the target is placed on the distant point and the tiles load there. |

Two circles not to be confused:

- the **small circle** (black and white, lying on the ground) is the **landing marker**: it shows where the avatar will appear when you press F. It follows the target, so it only changes on a double-click;
- the **large circle** (translucent cylinder with its name) is a **zone**: its radius is the one in the zone's form. **It only exists in the viewer** (see § 2 bis).

## 2 bis. What the visitor sees: links behave as on the web

In the **viewer** (editing), each unlinked zone keeps its **translucent cylinder**, always visible, to find and position it (signs too); a zone linked to an element is outlined there. None of this is exported.

In the **exported page** (standalone or modular), there is **no cylinder** for web link, Home Assistant command and portal zones:

| Zone                     | What is added to the scene                                                                         | On hover                                                                                                              |
| ------------------------ | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **linked to an element** | **nothing**                                                                                        | the cursor becomes a **hand**, the element gets a light **outline**, a **tooltip** shows the name and the destination |
| **unlinked**             | a **discreet marker on the ground** (small flat disc of 0.4 m, semi-transparent, with a thin ring) | same thing: hand, tooltip, the marker brightens                                                                       |

The tooltip gives the **name** then the **destination**: the web address for a link, "Region: address (#arrival)" for a portal ("this region" if the destination is empty), "Command: name" for a Home Assistant command (the webhook address is **never** shown). A **click** follows the link. A portal set to "walking into it" has no hover (it triggers by itself).

No permanent text sign: the name only appears on hover, or when you are within range ("click: …" at the bottom of the screen).

**Always show the name** (zone form, **unchecked by default**): keeps a name permanently visible, above the element or the marker; for an unlinked zone of "sign" shape, the whole sign is displayed.

*Change since v23*: unlinked zones of "sign" shape are no longer drawn in the exported page, unless **Always show the name** is checked.

## 3. Place a zone

In the viewer, section **Zones: signs, portals, links, commands**:

1. **Type to place**: choose the type.
2. Place it, either way:
   - click **Place a zone with a click on the scene**, then click in the scene;
   - or, in walk mode, stand at the right spot and press **P** (a circle under your feet, or a sign 2 m in front of you, facing you).
3. The zone appears in the list: open its form to set it up.
4. **See this zone** reframes the view on it; **Delete** erases it.
5. **Place here (last clicked point)** copies x, y, z of the last single click on the model into the zone's position: click on the model (the coordinates are shown in "picked"), open the form, then click this button.

## 4. Arrival point

This is the place where a visitor appears.

| Field              | Setting                                                          |
| ------------------ | ---------------------------------------------------------------- |
| Identifier         | the name the portals will use (`empereur`, `temple`, `default`…) |
| Displayed name     | free                                                             |
| Position X / Y / Z | Y is the height                                                  |
| Heading (degrees)  | the direction the visitor faces when arriving                    |

Place it in walk mode with **P**, looking in the desired direction: position and heading are taken in one go.

The arrival whose identifier is **`default`** is special: it is where a visitor arrives when nothing else is specified (portal without an arrival point, requested arrival not found, coming from the map without a setting). Put one in each region.

**`default` arrival and opening without a link (v33)**: if the region has a `default` arrival, the page opens **framed on it** (the camera target becomes its position) and **F starts at its point, with its heading** (as long as the target has not been moved, for example by a double-click). A target given explicitly on the command line (`--target`) keeps priority for the framing: see the exact rule in § 18.2.

## 5. Portal to another spot in the same region

| Field                      | Setting                                            |
| -------------------------- | -------------------------------------------------- |
| Destination page           | **empty** (the name of the page itself also works) |
| Arrival point in that page | the **Identifier** of the target arrival           |
| Trigger                    | see § 8                                            |

Effect: fade to black, then the visitor is placed on the arrival, facing like it. The page is not reloaded: they stay connected to presence and chat.

If the arrival does not exist, a message "Arrival point … not found in this region" is shown.

## 6. Portal to another region

| Field                      | Setting                                                                                                                                                                                                                  |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Destination page           | the other page: `autre-region.html` if it is in the same folder, otherwise its full address `https://…/autre-region.html`. With a common shell (§ 16): `index.html?region=AutreRegion` (the `#spawn=` is added after it) |
| Arrival point in that page | the **Identifier** of an arrival **of the other page** (empty = `default`)                                                                                                                                               |

Effect: fade, loading of the other page, the visitor arrives there directly in walk mode, with their nickname.

To check:

- the other page must exist at this address and have walk mode enabled;
- the target arrival must exist **in the other page**, not in this one;
- only `http` and `https` addresses and local files are accepted.

## 7. Signs

### Web link

| Field       | Setting     |
| ----------- | ----------- |
| Web address | `https://…` |

Walk up to it and press **E** (or click): the page opens in a new tab.

Accepted formats for the address (also for the destination page of a portal):

| Format                | Example                         | Note                                                                      |
| --------------------- | ------------------------------- | ------------------------------------------------------------------------- |
| web address           | `https://monsite.fr/ile.html`   | works everywhere                                                          |
| relative `.html` file | `autre-ile.html`                | relative to the page that contains the zone                               |
| local file            | `file:///P:/web/autre-ile.html` | **without quotes**; only works if the page itself is opened from the disk |

Spaces are written `%20` (`file:///P:/mes%20pages/ile.html`). Any other form (`javascript:`, `ftp:`…) is refused.

### Home Assistant command

| Field                          | Setting                                          |
| ------------------------------ | ------------------------------------------------ |
| Home Assistant webhook address | the webhook address of your automation           |
| Ask for confirmation           | checked: the visitor must confirm before sending |

Effect: a POST request is sent to the webhook with two values, `zone` (the displayed name) and `visitor` (the nickname). The same command cannot be sent again within 3 s. The page does not receive Home Assistant's answer: "Command sent" means sent, not executed.

## 8. Trigger, shape and size

**Trigger** (portals):

| Choice          | Effect                                                            |
| --------------- | ----------------------------------------------------------------- |
| walking into it | the portal fires as soon as you enter the circle                  |
| on click        | you have to click on it (v35: the E key no longer triggers zones) |
| both            | one or the other                                                  |

A "walking into it" portal on which you arrive does not trigger immediately: you have to leave it and enter it again. Two portals that send to each other therefore do not play ping-pong.

**Shape**:

| Choice               | Size setting                                                 |
| -------------------- | ------------------------------------------------------------ |
| circle on the ground | Radius (m)                                                   |
| sign                 | Width, Height, and Approach range for the "click" prompt (m) |

## 9. Link a zone to an element of the model

To make an object of the scene act as the trigger itself (a door, a box…):

1. In the zone's form, click **Link to an element**.
2. Click on the object in the scene.
3. The form shows the linked element. The size field becomes "Trigger distance… (m, from the element)".

The visitor then triggers the zone by clicking on the object, or with E when close enough to it. **Unlink** puts the zone back at its own position.

**Only one piece is linked**: the one you clicked on. If several objects of the model have the same name (frequent in an OAR), the zone stores `nom#index` (the rank of the object among those with this name) instead of the name alone: the other objects with the same name are not affected.

**Limit: 10 m.** An element with a dimension over 10 m is refused with the message "Element too big (L × W × H m): probably merged with a building in the OAR…". Cause: an object belonging to an OpenSim **linkset** is merged with it in the GLB; it no longer exists on its own, and it cannot be linked. Two remedies:

- **unlink it in OpenSim** (Unlink) before exporting the OAR, then generate the GLB again;
- or keep the building as it is and place a **circle zone** on it (Shape: circle on the ground), with the **Place here** button to position it.

## 10. Private zones

**Private (absent from the public export)** checked: the zone stays in your "private" exports, but disappears from the "public" exports. The choice is made in **Export profile**:

- **private: all the zones** (called "perso" before v43)
- **public: without the private zones**

A private arrival also disappears from the public export: a public portal that targets it will land on `default`.

## 11. World map

In the **World map** section, the **Arrival point of the visitors (identifier)** field tells where someone coming from the map arrives. The viewer shows under this field:

- ✔ if this arrival exists in the region;
- ⚠ otherwise (the visitor then appears at the usual starting point of the F key).

### Rotation of the region

When the OAR arrives rotated (or the island flipped north-south on the map), the **Region** section of the viewer offers **Rotation of the region**: 0, 90, 180 or 270° around the vertical axis. The model turns, and by the same angle, around the centre of the region: the zones (position and heading), the arrival points, the target and the landing circle, the sea hole. Linked zones follow their element. The status bar announces "Region rotated by N°: M zone(s) moved. Capture the thumbnail again."

The rotation is remembered like the other settings, and carried into the command (`--rotate 180`), into `.reglages.json` and into `<page>.config.json`. The generated page applies the rotation on loading; the zones of the file are already in the rotated frame: do not rotate twice.

**After a rotation**, the map thumbnail no longer matches the model:

1. **World map** section: **Capture the thumbnail (top view)**;
2. **Add / update this region in the map**;
3. **Export regions.json** (then generate again or republish the pages that embed it).

## 12. Publish the changes

Zones are set up in the viewer, but a page already published only sees them after publication:

| Your page is…                      | What to do after changing the zones                                                                         |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **standalone** (a single .html)    | **Export standalone HTML**, then replace the old page                                                       |
| **modular** (shell + .glb + .json) | **Export zones (.json)**, rename to `<nom de la page>.zones.json`, replace the old one, then F5 in the page |

Zones can also be saved and reloaded with **Export zones (.json)** / **Import zones (.json)**, for example to copy them from one region to another.

**After a version change** of glb2html (such as v21 → v22), existing pages keep the old behaviour: they must be generated again. In modular mode, it is the `.html` shell that changes: generate it again, simply replacing the `.json` files is not enough.

## 13. Troubleshooting

| Symptom                                       | Likely cause                                                                                                       | Remedy                                                                                                                                        |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Nothing happens when entering a portal        | not in walk mode                                                                                                   | press P (or F in the global view)                                                                                                             |
|                                               | trigger set to "on click"                                                                                          | click on the portal (v35: E no longer triggers it), or switch to "walking into it"                                                            |
|                                               | you were already in the circle when arriving                                                                       | leave the circle, then enter again                                                                                                            |
| "Arrival point … not found"                   | the portal contains the **Displayed name** instead of the **Identifier**                                           | copy the exact Identifier of the arrival (§ 1)                                                                                                |
| Arrival at the wrong place in another region  | the target arrival does not exist in the **other** page, or it is private and the page is public                   | create it in the other page, or uncheck Private                                                                                               |
| Black screen after an internal portal         | page generated before v22                                                                                          | generate the page again                                                                                                                       |
| "Portal without a valid destination"          | address badly written, or protocol not accepted                                                                    | `https://…` or a `.html` file name                                                                                                            |
| The zone works in the viewer, not in the page | page not republished                                                                                               | see § 12                                                                                                                                      |
| HA command "sent" but nothing moves           | wrong webhook, or automation disabled                                                                              | test the webhook directly from Home Assistant                                                                                                 |
| A deleted zone comes back after reloading     | the viewer restores the settings remembered for this file, or the old `.reglages.json` / `zones.json` was reloaded | delete it (**Delete**), wait 2 s (automatic saving), or **Forget this file's settings** (§ 14); also check `zones.json` / `<page>.zones.json` |
| The link takes a 30 m object                  | (before v23) the object is merged with a building in the OAR; the limit was 30 m                                   | v23: 10 m limit and explicit message; unlink the object in OpenSim (Unlink) or place a circle zone (§ 9)                                      |
| The landing circle "jumps"                    | (before v23) each single click moved the target                                                                    | v23: only the **double-click** moves it; the single click shows name and coordinates                                                          |
| The island is flipped north-south on the map  | the OAR was exported in the other orientation                                                                      | **Rotation of the region**: 180° (§ 11), then capture the thumbnail again, update the region in the map and export `regions.json` again       |

## 14. Remembered settings

The viewer remembers **everything** (zones included, but also hole, waves, camera, rotation, map, region card…) **per `.glb` file** in the browser (key: name + size of the file). It saves by itself, about every 1.5 s after a change. When the same `.glb` is reloaded, everything is restored, and the status bar shows "Settings restored from the browser's memory (N zone(s))".

Consequences:

- a zone added or deleted is found as it was when reloading; to **delete a zone**, open its form and click **Delete** (wait 2 s before closing the tab);
- the memory belongs to the browser and to the address of the viewer page: another browser or another computer sees nothing. To carry the settings: **Save to a file** (`.reglages.json`) then **Load from a file**, or `glb2html.py --settings`;
- **Forget this file's settings** (Remembered settings section) erases the memory of this `.glb`: the current values stay on screen, but are no longer protected, and they will be remembered again at the next change. To start from scratch: click this button, then reload the viewer page and open the `.glb` again.

## 15. Convert an OAR to GLB (`tools/oar2glb.py`)

`oar2glb.py` turns an OpenSim region backup (`.oar`) into a single `.glb` file ready for the viewer and for `glb2html.py`. It runs convoar¹, repairs its output and assembles everything. The output is written next to the OAR: `X.oar` gives `X.glb`.

¹ **Prerequisites**: **oar2glb.py** relies on the external converter **convoar.exe**
  Download: https://github.com/Misterblue/convoar/tree/master/bin
  Without convoar.exe, oar2glb.py cannot perform the OAR → GLB conversion.

### The commands (PowerShell, a single line)

First go to the script's folder: `cd "P:\_OpenSim\SL&OS\Web_3d"`.

| Need                                                                       | Command                                                                                   |
| -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Normal conversion                                                          | `python oar2glb.py "J:\...\X.oar"`                                                        |
| Conversion that keeps the intermediate folders (needed for `--diag`)       | `python oar2glb.py "J:\...\X.oar" --keep`                                                 |
| Find the animals in the viewer (a 15 m red mast on each)                   | `python oar2glb.py "J:\...\X.oar" --keep --markers`                                       |
| Keep invisible prims                                                       | `python oar2glb.py "J:\...\X.oar" --keep-invisible`                                       |
| Check what the script sees, without changing anything                      | `python oar2glb.py "J:\...\X.oar" --diag`                                                 |
| Same, naming the GLB or the `.gltf` to compare                             | `python oar2glb.py "J:\...\X.oar" --diag --glb "J:\...\X-GLTF\fichier.gltf"`              |
| Do not wait for "Enter" at the end                                         | add `--nopause`                                                                           |
| Add the complete terrain to an existing GLB, without running convoar again | `python oar2glb.py "J:\...\X.oar" --terrain-only "J:\...\X.glb"` (writes `X-terrain.glb`) |

Before converting again, delete the old intermediate folder: `Remove-Item -Recurse -Force "J:\...\X-GLTF*"`.

### The options

| Option                    | Effect                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--keep`                  | keeps the `X-GLTF` folder (images, buffers, `.gltf`); required to run `--diag` afterwards                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `--keep-invisible`        | keeps fully transparent prims (removed by default)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `--markers`               | adds a 15 m red mast on each rigged animal placed; the node name gives the animal and its size; remove them by running again without the option                                                                                                                                                                                                                                                                                                                                                                                   |
| `--diag`                  | changes nothing and does not run convoar: lists each part of the OAR (see below)                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `--glb CHEMIN`            | with `--diag`: GLB or `.gltf` to compare; by default the `.gltf` of the `X-GLTF` folder, otherwise the neighbouring `X.glb`                                                                                                                                                                                                                                                                                                                                                                                                       |
| `--max N`                 | maximum height (m) of a root object; above it (skybox) it is removed; default 600                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `--convoar CHEMIN`        | path of `convoar.exe` if it is not the default one                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `--reencode`              | **to be avoided**: re-encodes the textures before convoar; on Jungle_Isle it made about 150 textures out of 353 go missing (grey textures). Only use it if convoar shows many "unhandled number of components" errors or crashes in `OpenJPEG.DotNetDecode64` (return code 3221225477). Textures that Pillow cannot read are replaced by a 4x4 grey (list in `X-reenc-illisibles.txt`, next to the OAR) so as not to leave them to convoar's decoder; sculpt maps stay intact; at most 8 cores and batches of 512 to limit memory |
| `--nopause`               | do not wait for "Enter" at the end (the pause is also skipped when there is no console, and with `--terrain-only`)                                                                                                                                                                                                                                                                                                                                                                                                                |
| `--terrain auto\|yes\|no` | complete terrain from the height map (see below); `auto` by default                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `--terrain-patch N`       | side of a terrain patch in metres, from 2 to 255; default 64                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `--terrain-only GLB`      | does not run convoar: adds the complete terrain to this GLB and writes `X-terrain.glb` next to it (the original is never modified)                                                                                                                                                                                                                                                                                                                                                                                                |
| `--output FICHIER`        | with `--terrain-only`: output file instead of `X-terrain.glb` (never the original)                                                                                                                                                                                                                                                                                                                                                                                                                                                |

### Complete terrain for regions larger than 256 m (v29)

convoar produces only **one** "Terrain" node whose extent is capped (for example 257 x 267 m on a 1,024 m region: one sixteenth of the region has no ground). The complete height map is in the OAR (`terrains/*.r32`, one sample per metre). `oar2glb.py` uses it to build the ground:

- **Patches.** Squares of P x P metres (`--terrain-patch`, 64 by default), each a mesh of (P+1)² vertices. Edges are shared between neighbours (same heights, same normals, same colours: no crack, continuous lighting). The last patch of a row is smaller when n-1 is not a multiple of P. Each patch is a root object named `Terrain i,j` (i: column towards the east, j: row towards the north). World frame: X = x, height = h, Z = -y. A single "terrain" material (white, metal 0, roughness 1, single-sided), 16-bit indices, **no texture coordinates**: the look comes from the vertex colour (`COLOR_0`).
- **Normals** by central differences over the whole map (a single difference at the edges of the map).
- **Vertex colour** from the altitude `a` above the water level and the slope:

| Situation                   | Colour (red, green, blue)                                                             |
| --------------------------- | ------------------------------------------------------------------------------------- |
| `a` ≤ 0 (under water)       | wet sand (166, 150, 104)                                                              |
| 0 < `a` ≤ 1 m               | dry sand (214, 196, 142)                                                              |
| 1 to 4 m                    | gradual transition from dry sand to grass                                             |
| `a` ≥ 4 m                   | grass, light gradient from (98, 146, 66) at `a` = 4 m to (132, 140, 78) at `a` = 80 m |
| slope from 32 to 38 degrees | gradual transition towards grey rock (122, 120, 116); beyond 38 degrees: rock         |

- **Water level.** `WaterHeight` read from `settings/*.xml` in the OAR, otherwise 20 m (OpenSim's default). The log says which value is used and where it comes from.
- **When to replace.** `--terrain auto` (default): if convoar's "Terrain" node exists and covers less than 95 % of the map (boxes compared in the world frame), it is removed from the scene and the patches are added. Otherwise (256 m region, terrain already complete, no "Terrain" node) the GLB is **not modified**: it is identical to the one from `--terrain no`. `--terrain yes` always adds the patches (and removes convoar's "Terrain" if it exists); `--terrain no` does nothing. A GLB that already contains patches does not get any more. The filter of objects outside the region never removes the patches.
- **`--terrain-only GLB`** (without running convoar again, for a GLB of several GB): the GLB is **not loaded in full**. The JSON header is rewritten, the binary chunk is copied in pieces of 8 MB, the new buffers are added at the end. Output `X-terrain.glb` next to the original (or `--output`); the original is never overwritten, and nothing is written if convoar's terrain is already complete. The data of the old "Terrain" stay in the file, unused (a few MB). No "Enter" pause at the end.
- **Log.** Line `[terrain] map N x N samples (1 m); water level E m (origin); K patch(es) of P m; V vertices; B MB added; duration`. An OAR without a height map gives `this OAR has no height map ... nothing is modified` (return code 0, no error).
- **Not in this batch**: OpenSim terrain textures (the four textures blended according to altitude), level of detail of the terrain for the overview.

Test: `python tests/terrain.py` (synthetic OAR and GLB).

### What the script fixes

- **Rigged animals (animesh).** The geometry convoar writes for these meshes is unusable (giant hippos, tiny or flying elephants, shapes shared between animals). The script rebuilds it from the OAR's `.llmesh` file: positions, normals, UVs, triangles, then `bind_shape_matrix`; the prim's scale is ignored. The pieces of one animal stay together. The animal is centred on the position of the object's root and its feet are placed under the root box (at the altitude of the root if it is itself rigged). The textures come from convoar (face n of the mesh = material n). No rule depends on an animal's name. An animal whose computed size falls outside 0.1 to 12 m stays as convoar produced it (the log says so).
- **Invisible prims.** Removed: prims whose faces all have alpha 0 or carry a standard invisible texture, nodes whose materials are all transparent, and the root box of an animesh (simple prim, root of an object whose other pieces are all rigged meshes). The children of a removed root stay.
- **Textures.** The script compares the images announced by the `.gltf` with the files present; if some are missing, it runs convoar again (at most 2 more attempts), keeping the images already written.
- **Positions of regions larger than 256 m** and objects outside the region: processing unchanged. The terrain of these regions is completed by the patches (see "Complete terrain").

### Reading the log (`oar2glb.log`, next to the script)

| Line                                                                      | Meaning                                                                                             |
| ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `[rigged] 'Name' rebuilt from the OAR: N face(s), M vertices...`          | a piece of an animal was rebuilt; the "convoar" figures next to it show what convoar had written    |
| `[rigged] 'Name': 5 piece(s)... feet at 27.11 m (bottom of the root box)` | animal placed; size L x W x H and altitude of the feet                                              |
| `[rigged] ... GLB node not found`                                         | the piece was not found in the GLB; run `--diag`                                                    |
| `[rigged] ... obtained size ... implausible`                              | safeguard: the animal is left as convoar produced it                                                |
| `[invisible] node N 'Name' removed: ...`                                  | prim removed, with the reason                                                                       |
| `[fix] N rigged mesh(es) rescaled, M invisible prim(s) removed`           | summary                                                                                             |
| `[check] 'Name' feet at ...: inside the box of N object(s)`               | objects whose bounding box contains the centre of the animal (a clue if an animal is inside a rock) |
| `[GLB] N texture(s) missing out of M`                                     | missing images, replaced by grey                                                                    |
| `[terrain] ...`                                                           | decision (coverage of convoar's terrain) then summary of the patches added                          |
| `[OK] ...glb (taille, meshes, textures)`                                  | normal end                                                                                          |

### Diagnostic: `--diag`

Run it after a conversion made with `--keep`. The log is `oar2glb.diag.log`. Each part of the OAR gives one line: name, UUID, root or child, rigged yes/no, prim scale, `bind_shape_matrix` scale, transparent yes/no, animesh root box yes/no, and the GLB node found with the method (prim UUID, mesh UUID, name + position). Animals and invisible prims also show the summary of the `TextureEntry`, the full matrix, the position domain and the GLB material. A "node not found" line on an animal or a transparent prim means that the fix will not apply to it.

### If something goes wrong

| Symptom                                   | Likely cause                                                            | Remedy                                                                       |
| ----------------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Many grey textures                        | `--reencode`, or images not written by convoar                          | run again without `--reencode`; read `[GLB] N texture(s) missing`            |
| An animal invisible or in the wrong place | node not found, or hidden animal                                        | `--keep --markers`, then `--diag`; send `oar2glb.log` and `oar2glb.diag.log` |
| An animal with the wrong texture          | the order of the mesh faces does not follow that of convoar's materials | report the animal with its log                                               |
| Transparent prims you wanted to keep      | removed by default                                                      | `--keep-invisible`                                                           |
| "convoar not found"                       | different path                                                          | `--convoar "P:\...\convoar.exe"`                                             |

`python oar2glb.py --version` shows the version (`oar2glb v29 (22/10/2026)`) without running anything; the first line of the log (`oar2glb.log`, `oar2glb.diag.log`) repeats it: `[oar2glb] v29 (22/10/2026)`. Attaching this log to any report therefore gives the version used. The file is built in `dist/` by `python build.py`.

Test of the script: `python tests/oar2glb.py` (synthetic OAR and fake convoar, without network).

## 16. JSON files of a modular region

For a `Region.html` page produced by `--modular` (or by "Export the modular structure (.zip)" in the viewer), the folder contains:

These files are those of a region with its own shell (`--modular`). For several regions in the same folder with **a single** shell, see "Single shell for several regions" below.

| File                 | Role                                                                                      | Read again at each F5 |
| -------------------- | ----------------------------------------------------------------------------------------- | --------------------- |
| `Region.html`        | shell identical for all regions, it deduces its files from its own name                   | no                    |
| `Region.glb`         | the model                                                                                 | no                    |
| `Region.config.json` | settings for **rendering the page** (see below)                                           | yes                   |
| `Region.zones.json`  | zones, portals, arrivals                                                                  | yes                   |
| `zones.json`         | fallback zones, shared by the pages of the folder that have no `.zones.json` of their own | yes                   |
| `lib/three-0.160.0/` | three.js, Draco, Meshopt, shared by all the pages of the folder                           | no                    |

### Single shell for several regions (`--shared-shell`, v26)

A single shell (`index.html` by default) serves all the regions of the same folder, with a single `lib/`. Each region only adds three files. The region opens at **`index.html?region=NOM`**, where NOM is the name of the files without extension (`?region=NOM.html` is accepted: the extension is removed).

```
dossier/
  index.html            the shell, identical for all regions
  lib/three-0.160.0/    shared
  Ankh.glb   Ankh.config.json   Ankh.zones.json
  Jungle.glb Jungle.config.json Jungle.zones.json
```

| Need                  | Command (PowerShell, a single line)                                                                                                                             |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Generate a region     | `python glb2html.py "Ankh.glb" --settings --shared-shell --register regions.json -o "Ankh.html"`                                                                |
| Another shell name    | `--shared-shell monde.html` (address `monde.html?region=Ankh`)                                                                                                  |
| Change a setting      | `python glb2html.py --settings "Ankh.glb" --config-only --shared-shell --wave 2 -o "Ankh.html"`                                                                 |
| Change only the zones | `python glb2html.py -o "Ankh.html" --zones-only --zones zones.json`                                                                                             |
| Update a region (v34) | `python glb2html.py --update -o "Ankh.html" --shared-shell --sea-y 12`: applies **only** the options given, keeps the rest of the config and the zones (§ 19.6) |

Rules:

- `-o` designates the **region**: its name without extension gives NOM. `Ankh.html` is not written; written are `Ankh.glb`, `Ankh.config.json`, `Ankh.zones.json`, plus `index.html` and `lib/three-0.160.0/` **if they are missing**. An existing shell is never overwritten (the other regions share it): if it differs from the one of the current version, the script warns; delete it to renew it.
- `--register` writes the address `index.html?region=NOM` into `regions.json` (unless `--region-url` or a card in `.reglages.json`). Portals and the map add `#spawn=…` after the query string: `index.html?region=NOM#spawn=default&name=…`. "● you are here" recognises the region by its room, then by the full address (query string included).
- **Without a `region` parameter**, the shell behaves as before: it deduces its files from the page's name (`index.html` loads `index.config.json`, `index.glb`, `index.zones.json`). Pages already published and their shells therefore keep working, without changing anything. Without a parameter or a matching file, the page shows "Error: … not found (HTTP 404)" with the name of the file looked for.
- **Security.** NOM must be a single file name. Refused, with an error message in the page and **no network request**: an empty name, a name containing `/` `\` `:` `?` `#` or `..` (even encoded in the address), or starting with a dot. Without this, `?region=https://autre-site/x` would load config, zones and model from a foreign site (trapped portals, Home Assistant webhooks sent elsewhere). The script refuses in the same way an `-o` whose name would be refused.
- Viewer: "Export the modular structure (.zip)" gives the same structure (`index.html`, `NOM.glb`, `NOM.config.json`, `NOM.zones.json`, `lib/`); the "Shared shell" box of the summary for the script adds `--shared-shell` instead of `--modular`. The `.zip` overwrites `index.html` when unpacked: for a folder that already has several regions, copy only the NOM files if the shell has not changed.
- Like any modular mode, the page needs http/https (no opening from the disk).

### Which zone file is read

In this order, stopping at the first one that gives a valid JSON list:

1. `Region.zones.json`
2. `zones.json` of the same folder, **only if** the first one is missing, inaccessible (HTTP error) or is not a list
3. otherwise: no zone

There is **no merging**: as soon as `Region.zones.json` is read, `zones.json` is ignored. A `zones.json` placed next to a region that already has its `.zones.json` therefore has no effect.

Zones marked **private** are removed when reading, in either file, unless `profile` is `private` in `Region.config.json`.

### Region.config.json: the page rendering, not the viewer

It is the dictionary of settings that the page reads at startup (the same as the one embedded in a standalone page). It is **flat**. The complete list of its fields, with their type, default value, role and the option that sets them, is in **§ 27.3**; a complete sample is in `docs/samples/region.config.sample.json`.

`zones` is **always empty** there (`[]`) and `zonesLive` always empty: in modular mode, the zones are only in `Region.zones.json`.

The viewer never reads this file: it works with its own settings file (below).

### `.reglages.json` and `.config.json` do not have the same structure

`<nom>.reglages.json` is the working state of the viewer ("Save to a file"). It is **nested**:

```
{ v, file, saved,
  cfg:     { rotate, hole, holeFade, ..., mapUrl, guide, ignoreViz },
  camera:  { camDir, target, zoom },
  zones:   [ ...all the zones, private ones included ],
  profile, thisReg: { card of this region for the map },
  cmd:     { script, glb, dest, mapPage } }
```

|            | `<nom>.reglages.json` (viewer)           | `<page>.config.json` (page)              |
| ---------- | ---------------------------------------- | ---------------------------------------- |
| Structure  | nested (`cfg`, `camera`, ...)            | flat                                     |
| Camera     | `camera` sub-object                      | at the root (`camDir`, `target`, `zoom`) |
| Zones      | all, private ones included               | always empty                             |
| Map        | only the card of this region (`thisReg`) | complete resolved map (`map`)            |
| Its own    | `guide`, `ignoreViz`, `cmd`, `thisReg`   | `seaSize`, `version`                     |
| Written by | the viewer                               | `glb2html.py`                            |
| Read by    | the viewer, `glb2html.py --settings`     | the exported page                        |

The conversion only goes one way:

```
<nom>.reglages.json  ->  glb2html.py --settings  ->  <page>.config.json + <page>.zones.json
```

A `.config.json` cannot be given to `--settings` (the script looks for the `cfg` key and refuses the file), nor reloaded in the viewer ("settings file not recognized"). To keep your settings, you must therefore keep the `.reglages.json`: the `.config.json` is only a derived product of it.

### Which file to edit, and what overwrites it

| I want to change...                 | I edit / I run                                                  | What can overwrite it afterwards                                           |
| ----------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------- |
| a rendering setting (waves, sky...) | `--config-only` (see below), or `Region.config.json` by hand    | any new `--modular` or `--config-only` rewrites `Region.config.json`       |
| a zone                              | `Region.zones.json` by hand, or **Export zones (.json)** (§ 12) | `--modular` with `--zones` or `--settings`; `--config-only` with `--zones` |
| the working state of the viewer     | **Save to a file**                                              | nothing (it is the source)                                                 |

Without `--zones` or `--settings`, a `Region.zones.json` already present (edited by hand, for example) is not overwritten. As soon as a source of zones is given, it is rewritten.

Change a setting without touching the `.glb`, the shell or the zones:

```
python glb2html.py --settings "Region-final.glb" --config-only --wave 2 -o "Region.html"
```

The command-line options take precedence over the `.reglages.json`. Visitors see the change at their next reload.

## 17. Split a huge GLB into tiles (`tools/glb2tiles.py`, v28; `--exclude` and pause in v29; invalid images and overview in v31)

`glb2tiles.py` splits a GLB that is too heavy into **standalone tiles**: each one is a valid GLB (can be opened alone in `glb-viewer.html`), with its own nodes, meshes, materials and images, at the original coordinates (no recentring). This tool **writes the tiles, their list and (v31) a light overview of the whole region**; it is the shell that loads them around the avatar (v30, see § 17 bis). Standard Python only. The input GLB is never loaded in full: the JSON header is read, then the indices, positions and images in pieces.

`glb-stats.py` must stay **next to** `glb2tiles.py` (shared measuring functions); `python build.py` puts both in `dist/`.

### The commands (PowerShell, a single line)

| To                                                         | Command                                                                                                                                            |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| See the version                                            | `python glb2tiles.py --version`                                                                                                                    |
| Measure and get a recommendation, without writing anything | `python glb2tiles.py "P:\...\Region.glb" --analyse`                                                                                                |
| Split (recommendation "split")                             | `python glb2tiles.py "P:\...\Region.glb"`                                                                                                          |
| Split even if the recommendation is "no split"             | `python glb2tiles.py "P:\...\Region.glb" --force`                                                                                                  |
| Write somewhere other than next to the GLB                 | `python glb2tiles.py "P:\...\Region.glb" --output "P:\...\tuiles"`                                                                                 |
| Split without the overview                                 | `python glb2tiles.py "P:\...\Region.glb" --no-overview`                                                                                            |
| Redo **only** the overview (tiles untouched)               | `python glb2tiles.py "P:\...\Region.glb" --overview-only` with **the same split options** (`--output`, `--budget`, `--exclude`…) as the first time |
| Leave out a supplier's "delivery boxes"                    | `python glb2tiles.py "P:\...\Region.glb" --analyse --exclude "Freebies 20"` then the same command without `--analyse`                              |

Start with `--analyse`: it gives the measurements of `glb-stats.py`, the 10 heaviest meshes (compacted bytes, extent in metres), the 10 instances furthest from the median centre (outliers), the number of tiles expected with the chosen parameters, the expected duplication factor, the number of root objects kept whole or spread, and a recommendation sentence: "no split needed" or "split: budget N MB, T tiles, duplication F". A light GLB answers "no split needed" and nothing is written (even without `--analyse`, except with `--force`).

### The parameters

| Option                                 | Default         | Meaning                                                                                                                                                                                     |
| -------------------------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--budget`                             | 32              | MB per tile (standalone weight: distinct compacted primitives + distinct images)                                                                                                            |
| `--budget-triangles`                   | 1500000         | triangles per tile (the weight in MB is not enough: a block can have 5 M triangles for 70 MB)                                                                                               |
| `--min`                                | 16              | minimum side of a cell, in m: no further subdivision below it                                                                                                                               |
| `--whole-weight`                       | 16              | MB: a root object lighter than this can stay whole                                                                                                                                          |
| `--whole-extent`                       | 256             | m: …and smaller than this (both conditions together; the extent alone does not decide)                                                                                                      |
| `--threshold`, `--threshold-triangles` | 150, 3000000    | under these two values: "no split needed"                                                                                                                                                   |
| `--outlier`                            | 1000            | m: an instance further than this from the median centre, or larger, is reported                                                                                                             |
| `--block`                              | 256             | side of the blocks of the `glb-stats` part of `--analyse`                                                                                                                                   |
| `--output`                             | next to the GLB | output folder                                                                                                                                                                               |
| `--force`                              |                 | split even under the thresholds                                                                                                                                                             |
| `--exclude REGEX`                      |                 | removes from the split the root objects whose name matches (case-insensitive, repeatable; see below)                                                                                        |
| `--exclude-max-triangles`              | 24              | at most this many triangles in the root object, all meshes included, to be excluded                                                                                                         |
| `--exclude-max-meshes`                 | 1               | at most this many meshes in the root object to be excluded                                                                                                                                  |
| `--no-refs`                            |                 | do not write `extras.ref` / `extras.box` in the nodes of the tiles (v31 format: zones linked to an object impossible in tiles mode)                                                         |
| `--no-overview`                        |                 | do not write `X.overview.glb`                                                                                                                                                               |
| `--overview-only`                      |                 | write only `X.overview.glb` and its mention in `X.tiles.json`; the recomputed split must find exactly the tiles of `X.tiles.json` (otherwise: "does not match" error, use the same options) |
| `--ov-budget`, `--ov-budget-triangles` | 25, 1500000     | MB and triangles of the whole overview                                                                                                                                                      |
| `--ov-threshold`                       | 3               | m: objects whose largest dimension is smaller are omitted (the budget can raise this threshold)                                                                                             |
| `--ov-threshold-max`                   | 24              | m: if the budget forces omitting objects larger than this, the resolution goes down                                                                                                         |
| `--ov-resolution`                      | 10              | cells on the largest dimension of a primitive for vertex clustering (larger = finer and heavier)                                                                                            |
| `--ov-terrain-step`                    | 4               | m: grid step of the terrain in the overview                                                                                                                                                 |
| `--nopause`                            |                 | do not wait for Enter at the end (the pause is also skipped when there is no console: script, scheduled task)                                                                               |

### Excluding objects (`--exclude`, v29)

Some catalogues place next to each building a "delivery box" (textured cube of 12 triangles, a single mesh) whose name ends with the supplier's, for example "City Stores - Box - RAKis Freebies 2019". `--exclude "Freebies"` removes them, **provided that** the root object also has at most `--exclude-max-triangles` triangles (all meshes included) **and** at most `--exclude-max-meshes` meshes. Without these safeguards the supplier's name would also remove real buildings ("Jewel Box House V17 with Stairs - RAKis Freebies 2": 143 meshes, kept). The decision **never depends on the extent**: the bounding box of a small mesh that shares a vertex buffer with others is inflated, up to several tens of metres for a cube of 12 triangles.

- Several `--exclude` add up. An invalid expression gives a clear message (`Invalid regular expression for --exclude`) and nothing is read.
- The nodes removed are the root object and all its descendants; no other object changes. Excluded objects enter neither the tiles nor the weight, triangle and budget calculations (the "no split" recommendation also removes their bytes from the size of the GLB). The original GLB is not modified; the `glb-stats` part of `--analyse` describes the original file.
- `--analyse` and the final report give: the number of excluded objects, the triangles removed, the bytes saved (geometry and images that no kept object uses; **0** when all excluded objects share their primitives or their images with kept objects, for example a common cube: the report then says so, and counts the shared bytes not saved), the number of objects with a matching name but kept by the safeguards, and the 20 most frequent names with their count. `X.tiles.json` gets an `excluded` key (patterns, safeguards, `count`, `triangles`, `bytesSaved`, `bytesShared`, `names`) only when `--exclude` is used.

### Object references (v32): link a zone to an object in tiles mode

Each node copied into a tile gets in its `extras`: **`ref`**, its stable reference in the original model, and **`box`**, the box (world, 6 numbers in m) of **the whole object**, even when it is spread over several tiles (each piece carries the same box). `X.tiles.json` carries `"nodeRefs": 1`.

- **Reference rule** (the one of `nom#index` in single-GLB mode, computed on the whole GLB): the **name** of the node (failing that, the name of its mesh) if it is unique in the whole model; otherwise **`nom#index`**, index = rank of the node among the nodes with this name, in traversal order (pre-order, children in file order). Objects removed by `--exclude` count in the ranks (a reference does not change when something else is excluded). A node without a name has no reference; a reference longer than 200 characters is not written.
- These references are those of the **GLB names**, not those the viewer would see when opening the same whole GLB (the three.js loader renames duplicates): a linked zone written in tiles mode is used in tiles mode.
- **Measured cost** (synthetic GLB of 40,000 nodes): +0.5 s out of 8 s, +3 MB out of 230 MB of tiles.
- Tiles written **before v32** do not have these extras: linked zones are still ignored there. `glb2tiles.py --analyse` (and `--overview-only`) report it when `X.tiles.json` already exists without `nodeRefs`; `glb2html.py --tiles` too, if there are linked zones. You must **split again** (without `--overview-only`).

### Empty or invalid images (v31)

An embedded image **of 0 bytes**, of **another format** than PNG, JPEG or WebP, or **truncated** makes the loading of the tile fail in the browser ("THREE.GLTFLoader: Couldn't load texture"): measured in Chromium, `createImageBitmap` also fails on a cut PNG, JPEG or WebP, not only on an empty image. On the "Free House Gallery 4X4" region, 778 images out of 19,799 were in this case (all with a `bufferView` of `byteLength` 0).

- When writing, each image of this kind is replaced by **a grey PNG of 4 x 4 pixels** (grey 128, the one of the textures replaced by `oar2glb.py`), **written only once per tile** and shared by all the references of this tile (name `image-remplacee`). Materials, textures and texture coordinates do not change.
- Check without decoding: PNG = chained chunks up to `IEND`; JPEG = end marker `FFD9` last (give or take padding zeros and spaces); WebP = RIFF size contained in the file. Only the header, the end and the chunk headers are read (never the whole image). A file that Chromium would decode despite an unusual ending would be replaced wrongly: the reported number lets you notice it.
- `--analyse` and the final report give "Empty or invalid images replaced…: N distinct, M occurrence(s)" (an occurrence = an image written in a tile). `X.tiles.json` gets `"replacedImages": {"distinct": N, "occurrences": M, "grey": 128}` and each tile its own number.

### Overview (`X.overview.glb`, v31)

Purpose: in the global view, see the **whole** region; in walk mode, see **into the distance** beyond the loaded tiles. The detailed tiles remain the only source of collisions and ground.

- **Written with the tiles** (or alone with `--overview-only`), next to `X.tiles.json`, and referenced in `X.tiles.json` (`overview` key: `file`, `bytes`, `triangles`, `terrainTriangles`, `objects`, `candidates`, `omitted`, `effectiveMinExtent`, `effectiveTerrainStep`, `resolution`, `seconds`, `colors`, `params`).
- **One node per tile file**, named like the tile (`X.tiles/T_3_2_5.glb`, and `extras.tile`): the page hides the cell as soon as the detailed tile is **displayed** and shows it again when the tile is unloaded or has failed. The objects of a cell are exactly those of the tile: no double display, no hole during loading.
- **No image.** A single material; the colours are **vertex colours**. Each material becomes a flat colour: the **average colour of its texture** if Pillow is installed (average in linear space, weighted by opacity), otherwise its **base colour**. The vertex colours of the terrain are kept. No normals: the page shows the overview with flat shading. Translucent primitives (`alphaMode` BLEND: glass, effects) and skinned objects are omitted.
- **Each UNIQUE primitive is simplified only once**, then copied with the matrix of each of its instances (never simplified per instance). Method: vertex clustering on a grid of side (largest dimension of the primitive) / `--ov-resolution`; one vertex per cell (average), degenerate and duplicate triangles removed. Standard Python only; Pillow is optional (average colours).
- **Terrain simplified separately.** The pieces marked `extras.terrain` (patches from `oar2glb.py`) are resampled on a **common regular grid** of step `--ov-terrain-step`: height and colour interpolated in the original triangles, a cell belongs to a single piece (so to a single tile). A grid point on a shared edge gets the same height on both sides: **no gap between the patches** (tested). The terrain takes at most half of the budgets; otherwise its step grows (× 1.5) until it fits (stated in the log).
- **Omitted objects.** Those whose largest dimension is under `--ov-threshold` (3 m by default: at 600 m, the distance at which the overview makes most of the image, 3 m cover about 8 pixels on a screen 1,080 pixels high with the 38-degree field of view; at 210 m, the limit of the loading radius, 22 pixels). This choice comes from a calculation of size on screen, **not from a measurement on your region**: `--analyse` prints the number of instances and triangles above 1, 2, 3, 4, 8, 16, 32 and 64 m to decide on your data. If the budget is reached, the **largest objects are kept first** and the effective threshold rises (`effectiveMinExtent`); beyond `--ov-threshold-max` the resolution goes down and the calculation is redone.
- **Budgets**: 25 MB and 1,500,000 triangles for the whole region (`--ov-budget`, `--ov-budget-triangles`). The report gives the weight, the triangles (terrain included), the objects kept out of the candidates, the objects omitted (too small / by the budget / skinned), the translucent primitives omitted, the colours (texture averages, unreadable, Pillow missing) and the time.
- **The GLB is never loaded in full** (same reading in pieces of at most 4 MB as for the tiles), with a progress line ("[overview: primitives] …"); the terrain pieces are read one by one.
- **Duration.** Throughput measured on synthetic GLBs of increasing size (0.5; 2; 8; 24 million unique triangles): about 1.8 million unique triangles per second, linear (0.3; 1.2; 4.5; 13 s), i.e. 14 to 680 MB of GLB for 25 to 164 MB of memory; 20,000 small meshes (4 million triangles, 40,000 instances): 15 s, 377 MB; 1,024 m terrain in 256 patches of 4,225 vertices: 3.6 s, 57 MB. The estimate for the 1.3 GB region is given in `CHANGELOG.md` (v31).

### How the split is decided

- Adaptive quadtree on the X,Z plane (Y is the height), only on non-empty cells. A cell is subdivided as long as its standalone weight exceeds `--budget` **or** its triangles exceed `--budget-triangles`, and its side exceeds `--min`.
- A **root object** (first-level node of the scene) stays **whole**, in the cell of the centre of its box, if its standalone weight ≤ `--whole-weight` **and** its extent ≤ `--whole-extent`. Otherwise it is **spread instance by instance**: each instance goes into the cell of its own centre, and the parent nodes are copied (without mesh) with their original transforms.
- An object carrying a **skin** is never spread: its whole root object goes into the tile of the centre of its box, with the skin, the joint nodes (even if they are outside the object) and the `inverseBindMatrices`.
- Meshes shared between tiles are **duplicated** in each tile that uses them (standalone tiles). The actual duplication is written in the report.
- The vertices of each primitive are **compacted**: only indexed vertices are kept and renumbered, with the smallest index type (16 bits if possible). Triangles are identical.
- A **single** mesh heavier than the budget (terrain, sea) cannot be spread at this stage: its cell stays as it is, over budget, with a warning (name, extent, MB).
- A compressed GLB (Draco, meshopt) is refused with a clear message. `sparse` accessors: refused with a message.

### Files produced

`X.tiles/T_<niveau>_<i>_<j>.glb` (level and position of the cell in the quadtree), `X.tiles.json` (UTF-8 without BOM) and `X.overview.glb` (v31), next to the GLB `X.glb`:

```
{
 "version": 1,                      format version
 "generator": "glb2tiles v28 (21/10/2026)",
 "source": "X.glb",
 "extent": {"min": [x,y,z], "max": [x,y,z]},     overall extent of the content
 "params": {"budgetMB": 32, "budgetTriangles": 1500000, "minCell": 16, "wholeWeightMB": 16, "wholeExtent": 256,
            "thresholdMB": 150, "thresholdTriangles": 3000000, "outlier": 1000},
 "warnings": ["..."],               tiles over budget, outliers, extensions not copied
 "roots": {"whole": 1700, "split": 125},         root objects kept whole / spread
 "duplication": 1.8,                sum of geometry bytes of the tiles / unique geometry of the GLB
 "nodeRefs": 1,                     extras.ref / extras.box in the nodes of the tiles (v32; 0 with --no-refs)
 "replacedImages": {"distinct": 778, "occurrences": 1200, "grey": 128},    empty or invalid images replaced (v31)
 "overview": {"file": "X.overview.glb", "bytes": 23000000, "triangles": 1400000, "terrainTriangles": 131072,
              "objects": 21000, "candidates": 30000, "omitted": {"small": 9000, "skinned": 12, "translucentPrimitives": 800, "budget": 0},
              "effectiveMinExtent": 3, "effectiveTerrainStep": 4, "resolution": 10, "seconds": 95.0, "colors": {...}, "params": {...}},   (v31)
 "tiles": [{"file": "X.tiles/T_3_2_5.glb", "level": 3, "i": 2, "j": 5,
            "min": [x,y,z], "max": [x,y,z],   box of the actual content of the tile (an object overflowing its cell stays covered)
            "instances": 812, "triangles": 410233,
            "bytes": 21345678, "geometryBytes": 9001234, "imageBytes": 12000000, "replacedImages": 2}]
}
```

Running again rewrites the `T_*_*_*.glb` of the `X.tiles/` folder; **then** (v31), the `T_*_*_*.glb` of a previous run that are no longer in the new index are **deleted** and the report gives their number (the other files of the folder are not touched). `--overview-only` touches no tile.

### Reading the log (`glb2tiles.log`, next to the script)

First line: `[glb2tiles] v31 (22/10/2026)`. Progress is written every 5 % or 10 s. The final report gives: number of tiles, median / 90 % / maximum of weight and triangles, actual duplication, number of whole and spread roots, warnings, total time. `python glb2tiles.py --version` shows the version without log or pause.

In `--analyse`, the "Reading" line gives the bytes read. Positions are only read for primitives that use only part of a shared vertex buffer (the accessor's box would be too large); the other boxes come from the header.

### If something goes wrong

| Symptom                                                             | Likely cause                                                                             | What to do                                                                                                   |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| "compressed GLB"                                                    | the GLB uses Draco or meshopt                                                            | decompress the GLB first (outside this batch)                                                                |
| "glb-stats.py not found"                                            | the script is alone in its folder                                                        | copy `glb-stats.py` next to it                                                                               |
| "Tile … over budget"                                                | a single mesh (terrain, sea) exceeds the budget, or the minimum cell is reached          | normal at this stage: see the roadmap (split by triangles)                                                   |
| Many tiles for a small GLB                                          | `--budget` too small or strong duplication                                               | run `--analyse` again with other values                                                                      |
| "THREE.GLTFLoader: Couldn't load texture" on a tile made before v31 | 0-byte or truncated image in the GLB                                                     | split again with v31 (images replaced by grey)                                                               |
| "The recomputed split … does not match X.tiles.json"                | `--overview-only` run with other split options                                           | use exactly the options of the original split                                                                |
| "Pillow missing" in the report                                      | the overview uses the base colour of the materials (often white for a textured material) | `pip install pillow` then `--overview-only`                                                                  |
| Overview too heavy or objects missing                               | budget reached, `effectiveMinExtent` raised                                              | larger `--ov-budget` / `--ov-budget-triangles`, or higher `--ov-threshold`; read the "objects omitted" lines |
| Instance at 3,000 m reported                                        | a giant prim or a stray object                                                           | the tool keeps it; fix it in the model if it is a mistake                                                    |

Test: `python tests/glb2tiles.py` (synthetic GLBs, without browser or network); `python tests/v31.py` (invalid images, overview, leaving walk mode).

## 17 bis. Load a tiled region in the page (`glb2html.py --tiles`, v30)

A region of several hundred MB or several GB does not fit in a browser: after `glb2tiles.py` (§ 17), the **shell** loads only the tiles close to the avatar and unloads the distant ones, and (v31) shows in the distance the **light overview** `X.overview.glb` when it exists. Without the `tiles` field in `X.config.json`, the page behaves exactly as before (a single `X.glb`).

### The commands (PowerShell, a single line)

| To                         | Command                                                                                                                    |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Split                      | `python glb2tiles.py "P:\regions\4X4.glb" --exclude "Freebies"` (writes `4X4.tiles.json` and `4X4.tiles\` next to the GLB) |
| Put the region in the site | `python glb2html.py --shared-shell -o "P:\site\4X4.html" --tiles "P:\regions\4X4.tiles.json"`                              |
| Open                       | `http://…/index.html?region=4X4` (the common shell, as in § 16)                                                            |
| Try another radius         | `index.html?region=4X4&radius=300`                                                                                         |
| Change a setting           | run the same command again with the option: nothing heavy is copied again                                                  |

`-o` designates the region (its name without extension). No `.glb` as input. `--tiles` alone (without `--shared-shell`) gives a shell of its own, `4X4.html`. Written: `4X4.config.json` (`tiles` field), `4X4.zones.json` (if missing or if a source of zones is given), the shell and `lib/` if they are missing. **`4X4.tiles.json` and the tiles folder are only copied if they are not already next to the page**: putting `-o` in the tiles folder avoids any copy ("already beside the page: nothing is copied"); otherwise the script copies what is missing or has another size, file by file, and says how many. There is no `4X4.glb`. Like any modular mode, the page needs http/https.

### The parameters (in `X.config.json`, with their options)

| Key / option                                | Default   | Meaning                                                                                                                                                          |
| ------------------------------------------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tileRadius` / `--tile-radius`              | 150       | m: load the tiles whose **box** (min / max of `X.tiles.json`) is closer than this radius to the avatar, on the X,Z plane (distance 0 = the avatar is in the box) |
| `tileMargin` / `--tile-margin`              | 60        | m: unload beyond radius + margin (hysteresis: no back-and-forth at the limit)                                                                                    |
| `tileMaxMB` / `--tile-max-mb`               | 200       | MB of tiles loaded at the same time (weight of the `.glb` files)                                                                                                 |
| `tileMaxTriangles` / `--tile-max-triangles` | 8 000 000 | triangles of tiles loaded at the same time                                                                                                                       |
| `tileConcurrency` / `--tile-concurrency`    | 4         | simultaneous downloads                                                                                                                                           |

`?radius=NNN` in the address replaces `tileRadius` for this opening (10 to 5 000). These keys only exist in the config for a tiled region.

### What the page does

- **Start.** The tiles around the starting point load first, the closest first: the arrival of the link (`#spawn=…`, otherwise the `default` arrival) if the page is opened by a portal, otherwise the camera target. "Loading…" stays displayed until the tiles containing this point are ready (or have failed); the others come afterwards. A partial ground is normal as long as everything is not there: a tile only contains its terrain patches and its objects.
- **During the visit.** The reference point is the avatar in walk mode, or the target (the landing circle) in the global view. Every 250 ms: unloading of the tiles beyond radius + margin, loading of those within the radius. If `tileMaxMB` or `tileMaxTriangles` would be exceeded, the **most distant loaded tiles** (more distant than the one to load) go first; a tile containing the avatar is loaded even if it alone exceeds the budget (warning in the console).
- **Memory.** An unloaded tile frees its geometries, materials, textures and decoded images. The budget counts the **weight of the files**: decoded textures weigh much more in graphics memory than their compressed file; if the page is heavy, lower `tileMaxMB` or `tileRadius`. The collision grid of each tile costs about 36 bytes per ground and wall triangle, plus the index: at 8 million triangles, count several hundred MB.
- **Walk mode and collisions.** A collision grid is built per tile, in slices so as not to freeze the image, and deleted with the tile. Ground and walls only come from ready tiles. The avatar **never moves towards a point whose tile is not ready**: it stays where it is, the text "Loading the ground…" is shown, and it moves again as soon as the tile is ready (never a fall). **F** waits for the tile under the avatar before starting walk mode (F again: cancel); an internal portal or a double-click towards a zone not loaded waits in the same way. The terrain patches have shared edges: the ground continues from one tile to the next without a step.
- **Failed tile** (missing file, HTTP 404, unreadable GLB): message at the top of the page and in the information line, warning in the console, new attempt after 3 s, 6 s, 12 s… up to 30 s. The other tiles are not delayed. An avatar does not cross the box of a failed tile (same rule as "not ready").
- **Information line** (text only), in the help panel at the bottom left (can be hidden with H), otherwise in a small frame: "Tiles: 7 loaded / 106 · 74 MB · 2.10 M triangles", with "· 2 in progress" and "· 1 failed (will retry)" when there are some, then (v31) "· Overview (counted apart): 23.1 MB · 1.40 M triangles": the overview is counted apart, outside the 200 MB / 8 M triangles of the budget.
- **Overview (v31).** If `X.tiles.json` mentions `overview`, the page loads it **first** (before any tile), with the same path security rules as the tiles. It shows the whole region in light geometry, without images. Each cell (one node per tile file) is **hidden as soon as the matching detailed tile is displayed** and shown again when the tile is unloaded or has failed: never both, never a hole during loading. It is used **neither for collisions, nor for the ground, nor for "Loading the ground…"** (walk mode always waits for the tile), and does not count in the `tileMaxMB` / `tileMaxTriangles` budget. A **double-click** on it in the global view places the target on the distant point; the real ground takes over when its tile is ready. If it cannot be found or read: warning in the console, "Overview unavailable" in the information line, the region works as in v30.
- **Global view.** With the overview, the camera frames **the whole region** (maximum distance, fog and far plane follow the extent). Without it (old `X.tiles.json` or `--no-overview`), as in v30: only the tiles loaded around the target, and the camera frames the loading radius.
- **Leaving walk mode (v31).** F to leave places the target of the global view on the ground under the avatar and keeps the camera offset from before entering walk mode; the loader follows this target, so the tiles around the avatar are not unloaded.

### Frame, rotation, sea, zones

- **Frame.** That of the original model: **no recentring** (the tiles keep their coordinates). The coordinates of the zones, arrivals, camera target and sea hole are therefore in this frame, not in the viewer's (which recentres the whole model, something that cannot be done with tiles). `--rotate` (0, 90, 180, 270) turns the root of the tiles around the vertical axis through the origin; as in § 11, the stored values are in the already rotated frame, and so is the default target written by `--tiles`.
- **Default target and sea.** Without `--target`, the camera target is the centre of the extent of the tiles, at a height of 20 m; without `--sea-y`, the sea is at 20 m (OpenSim's water). The sea is centred on the centre of the extent; the hole (`--hole`, `--hole-x`, `--hole-z`) is relative to this centre. To remove the sea: `--no-sea`.
- **Free zones** (cylinders with coordinates, arrivals, portals, signs): as before. **Zones linked to an object** (`mesh` field, v32): if the tiles carry the object references (`glb2tiles.py` v32, § 17), the zone **appears when the tile containing the object is loaded** and disappears when it is unloaded: clickable, E key closer than `radius` m from the object, as in single-GLB mode. An object spread over several tiles: the zone follows the **box of the whole object** (stored in the tiles), as soon as **one** piece is loaded. Tiles from before v32: zone **ignored**, with "zone “id” ignored: linked to the element “…” … (tiles written without object references: split again with glb2tiles v32)" in the console, and a warning from `glb2html.py` when generating. Presence, chat, world map, portals: unchanged. The viewer now opens a tiled region (§ 17 ter).
- **Displayed position (v32).** The help panel (H key, bottom left) gives as text the **position of the target** in the global view, or of the **avatar** in walk mode: "Position target (global view): x 123.5 · y 15.0 · z -77.7 m", in metres, one decimal, in the frame of the original model: that of the zones. Handy to note a spot.

### Limits of this version

- The overview is coarse: small objects (under `--ov-threshold`), glass and skinned objects are not in it, the colours are flat, the terrain has a 4 m step; at the edge of a loaded tile, the ground height can differ by a few decimetres between the tile (1 m) and the overview (4 m).
- Meshes shared between tiles are duplicated in each tile that uses them (standalone tiles): more MB downloaded.
- A single mesh heavier than the `glb2tiles.py` budget stays in a single tile (no split by triangles).
- A tile very heavy in triangles stays costly to process: the construction of its collision grid is sliced, not removed.
- No meshopt compression of the tiles, no OpenSim terrain textures yet (vertex colours from `oar2glb.py`).

### If something goes wrong

| Symptom                                   | Likely cause                                                                                                                                    | What to do                                                                                                                        |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| "Loading error: … X.tiles.json: HTTP 404" | `X.tiles.json` is not next to the page, or the `tiles` field of the config is wrong                                                             | run `glb2html.py --tiles` again; check the folder                                                                                 |
| "tile address refused"                    | the `tiles` field contains `..`, `:`, `?`, `#` or starts with `/`                                                                               | a simple relative path (`X.tiles.json`)                                                                                           |
| Partial ground, holes                     | tiles outside the radius, or failed                                                                                                             | raise `tileRadius` (or `?radius=`), see the information line and the console                                                      |
| "Loading the ground…" that stays          | a failed tile in front of the avatar                                                                                                            | fix the file; the page retries by itself                                                                                          |
| Nothing or a hole in the distance         | no overview (region split before v31, or `--no-overview`)                                                                                       | `glb2tiles.py … --overview-only` with the original options, then run `glb2html.py --tiles` again (copies the file with the tiles) |
| "Overview unavailable"                    | `X.overview.glb` missing next to the page, or unreadable                                                                                        | copy it next to `X.tiles.json`; run `glb2html.py --tiles` again                                                                   |
| Heavy, slowed-down page                   | too many textures loaded                                                                                                                        | lower `tileMaxMB`, `tileMaxTriangles` or `tileRadius`                                                                             |
| Linked zones do not appear                | the object's tile is not loaded (they only exist while the tile is loaded), or the tiles date from before v32 (ignored, warning in the console) | get closer / `?radius=`; otherwise split again with `glb2tiles.py` v32 (§ 17), or use free zones with coordinates                 |
| The zones are shifted                     | they come from the viewer (recentred frame)                                                                                                     | write them in the frame of the original model                                                                                     |

Test: `python tests/tuiles.py` (synthetic region of 16 tiles, headless Chromium) and `python tests/v31.py` (overview in the shell, leaving walk mode).

## 17 ter. Place zones in a tiled region (viewer, v32)

The viewer (`glb-viewer.html`) opens a region split into tiles and shows it **in the frame of the original model** (no recentring): the coordinates of zones, arrivals, camera and sea hole that it produces are directly those `glb2html.py --tiles` expects. It shows the overview everywhere and loads the detailed tiles **around the target** (with the same loader and the same limits as the page: radius 150 m, 200 MB, 8 million triangles).

**Step by step** (recent Edge or Chrome):

1. Open `glb-viewer.html` (double-click on the file, or in a browser).
2. Click **"Open a tiled region (folder)"** and choose the **folder that contains `X.tiles.json`** (the one where `glb2tiles.py` wrote `X.tiles.json`, `X.overview.glb` and the `X.tiles` folder). Or **drag this folder** into the window. The browser may ask to confirm sending the files: nothing is sent anywhere, it reads them in place, one by one, when a tile is needed. If there are several regions in the folder, a "Region in the folder" list appears.
3. The text under the buttons says what is open (tiles, overview, object references). The whole region appears; the tiles around the target (the small black and white circle on the ground) load.
4. **Move the target**: double-click on the terrain (even on the overview: the tiles of that spot load). Wheel to zoom, drag to rotate, right click + drag to pan.
5. In the **"Zones"** section, choose the type, click **"Place a zone with a click on the scene"**, then click on the ground or an object **once the tile is displayed**. If you click outside a loaded tile (on the overview), the viewer tells you so as text ("No detailed tile loaded at this spot…"), loads the tile, and you click again a few seconds later. Everything else is as in single-GLB mode: radius and height, portals (§ 5, 6), arrivals (§ 4), signs, Home Assistant (§ 7, 8), P key in walk mode.
6. **Link a zone to an object** (§ 9): in the zone's form, **"Link to an element"**, then click on the object. The zone takes the position of the object. A linked zone is only visible when the object's tile is loaded (the text of the form says so: "tile not loaded"; **"See this zone"** loads it). If the viewer answers that the element has no reference, the tiles date from before v32: split again (§ 17).
7. **"Coordinates (m)"** section: the targeted point (single click on the model) and the target, as text (x, y, z, one decimal), with **"Copy the targeted point"** and **"Copy the target"**.
8. **Export the zones**: "Export zones (.json)" writes **`X.zones.json`** (X = name of the region) into your downloads folder. To **complete** a region already done: open the region, "Import zones (.json)" with the existing `X.zones.json`, add the new zones, export again.
9. **Generate the page again**: fill in "Path of glb2html.py" and click **"Generate the PowerShell command line"**: the viewer writes the full command (`--tiles`, `--zones`, `-o`, common shell, sea level, presence, chat…). Run it from the folder of `glb2html.py`, correcting the path of `X.zones.json` if it is not next to it. If the page already exists and the `index.html` shell has changed version, delete it first (an existing different shell is never overwritten: the warning says so).

Another way to open: by address, if the viewer is served over http (for example `python -m http.server` run in a folder that contains `glb-viewer.html` and, below it, the region): `http://localhost:8000/glb-viewer.html?tiles=region/X.tiles.json`. The path is relative to the page, without `..`, without `:`, `?` or `#`.

**What differs from single-GLB mode**: no standalone HTML export and no `.zip` (there is no single GLB; the buttons are disabled); no rotation of the region (original frame; with `glb2html.py --tiles --rotate`, the zones must already be in the rotated frame); the sea hole is relative to the **centre of the region** (as in the page); the sea is at 20 m by default (`--sea-y` to change it, the command writes it); the wireframe of walk-through elements only shows the tiles already loaded; the text of a linked zone's form ("tile not loaded") is only updated at the next change of the list (edit or add a zone, click a zone in the scene), not when the tile arrives; the zone itself appears at once in the scene.

Test: `python tests/v32.py` (synthetic region of 16 tiles: free, portal, arrival and linked zones placed in the viewer, export, then generated page).

## 18. New in v33 (22/10/2026)

### 18.1 Starting at an arrival (`#spawn=`, `#pos=`) in a tiled region

**What used to happen (measured, 22/10/2026).** With a `#spawn=chateau` link, the loader took the arrival as its reference for **only 4 seconds**, then went back to the default camera target. If the arrival's tile was not ready at that moment (heavy tile, slow processor or network), it was **unloaded and its download abandoned**, the tiles around the target loaded instead, and the page waited 120 seconds before going on, **behind a black screen without any text**. Reproduced on a synthetic region of 16 tiles, two of them with more than a million triangles (23 MB, `tests/glbfab.py`), processor slowed down 10 times (Chromium developer tools): black screen **121.6 s**, avatar in walk mode at **125.7 s**; with v33: walk mode at **7.1 s**. Without slowdown: 2.6 s before, 1.6 s after. The measured cause is the 4 s window (the arrival's tile, unloaded, was requested again later); the construction of the collision grid was not the cause on this synthetic region (142 ms of computation for 1 million triangles without slowdown, 2 s at x10).

**What v33 does.**

- The requested arrival point (`#spawn=ID`, or `#pos=x,y,z,yaw`, or the `default` arrival when opening without a link) is the **loader's reference until walk mode starts** (or until the target of the global view is moved), never the camera target.
- The tile or tiles containing this point start **before the overview and before any other tile**; **no other tile starts** until those are ready (or have failed).
- Their collision grid goes first in the queue, with a **time budget per frame of 40 ms** (6 ms for the other tiles). During walk mode, the grid of the tile containing the avatar **always** goes before the others.
- **Never a black screen without text**: from the start, "Loading the ground… 0/1 tile ready · 3 s" (tiles ready out of tiles expected, elapsed time), on a black background with framed white text. **After 15 s**, the black screen is removed: you see the scene (overview included) with the text, and walk mode starts as soon as the tile is ready. After 60 s, the text adds "long wait (heavy tile or slow network)"; the 120 s delay no longer exists.
- If loading fails, the error message is no longer hidden behind the black screen.

**`#pos=x,y,z[,yaw]`** (numbers only, decimal point, values limited to ±100 000; anything else is ignored): anonymous arrival at this point, with the same loading rules. The frame is that of the original model in tiles mode, that of the page (recentred model) in single-GLB mode. The help panel offers **"Copy the link to my position"**: address of the page (with `?region=`) followed by `#pos=x,y,z,yaw` (2 decimals), readable when opening; without a clipboard, the link is written in a field of the panel.

**One line per tile in the console** (the browser's F12 key) when it becomes ready or fails, to paste into the diagnostic chat:

```
[tile] X.tiles/T_3_0_1.glb ready: 14.0 MB · 1002668 triangles · wait before download 0 ms · download 278 ms · GLB parsing 28 ms · wait in the grid queue 53 ms · grid construction 142 ms of work (1004 ms elapsed) · total 1310 ms
[tile] X.tiles/T_3_2_4.glb: failed after 2100 ms (HTTP 404)
```

"Grid construction" = computation time actually used; "elapsed" = clock time between entering the queue and the end (includes rendering the frames). `viewer.tilesState().log` (browser console: `__viewer.tilesState().log`) gives the same values as numbers.

### 18.2 Default arrival and back to the arrival point

Exact rule, **without a link** (neither `#spawn=` nor `#pos=`):

| Situation                                                           | Starting framing (camera target)                                                       | F key (without having moved the target) |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | --------------------------------------- |
| the region has a `default` arrival, no `--target`                   | **the position of this arrival**                                                       | **its point and its heading**           |
| the region has a `default` arrival, `--target` given                | the given target                                                                       | the target (as before)                  |
| no `default` arrival                                                | the target (the one from the configuration, or the centre of the extent in tiles mode) | the target (as before)                  |
| configuration written before v33 (without the `targetExplicit` key) | the target (as before)                                                                 | the target (as before)                  |

With a link (`#spawn=`, `#pos=`), the framing and walk mode happen at the requested arrival. In tiles mode, this point is the loading reference at the start.

The viewer writes `targetExplicit` as true when the target of its camera is not the default target (same test as the `--target` command line). A `default` arrival placed in the viewer therefore changes nothing for a page whose camera you framed by hand.

**Back to the arrival point**: "Back to the arrival point (R)" button or **R** key. In walk mode: teleport to the `default` arrival (failing that: to the starting target), with "Loading the ground…" if the tile is not ready, like an internal portal. In the global view: the target and the camera move to this point (same camera offset).

### 18.3 Zone markers in the exported page

| Option          | Value                                 | Effect                                                                                                                                                                 |
| --------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--zone-marker` | `dot` (default; `discret` before v43) | previous behaviour: flat semi-transparent 0.4 m disc and thin ring                                                                                                     |
|                 | `range` (`portee` before v43)         | **thin sharp ring at the real radius of the zone**, without a cylinder; a one-pixel line is added to the flat ring so that it is still drawn from afar                 |
|                 | `none` (`aucun` before v43)           | no marker; the zone stays clickable and triggers as before                                                                                                             |
| `--show-spawns` | (none)                                | also draws the **arrivals**: small 0.3 m disc and thin ring on the ground. Without this option, arrivals are **never** drawn in the exported page (only in the editor) |

They concern portals and free zones (web link, command). Setting in the viewer: "Zones" section ("Marker of portals and free zones" menu, "Draw the arrivals" box); it appears in the summary of the command line. Config: `zoneMarker`, `showSpawns`.

### 18.4 Flight, three views, "Go to"

- **Flight** (`--fly`, default; `--no-fly` removes it from the page and the help): **Home** takes off or lands. In flight, **Page Up** (or **Space** held, v36) goes up and **C** goes down (same speed as walking, **Shift** speeds up), no gravity, walls block as on the ground, the avatar never goes below the ground of the loaded tiles. Towards a tile not yet ready, the avatar stops at the edge ("Loading the ground…"), as on foot. On landing, gravity brings it back to the ground (or onto a roof). Presence transmits the height normally. In flight, E triggers the nearby zone as on the ground (v36).
- **Views** (**V**): first person (the previous view); **third person** (the camera turns around the avatar, at 4 m, comes closer if a wall is behind it, never goes below the ground, the mouse sets the height); **free camera** (the avatar stays in place, the movement keys and the arrows move and turn the camera, **Page Up** and **C** raise and lower it, it does not go through the ground). In free camera, **V** again gives control back to the avatar (v36: **F** leaves walk mode, like **P**). The avatar is drawn with the same model as the other visitors, with the visitor's name and colour. The view is written as text in the help panel (v34: "View: third person" and "Mode: on foot" in the status block, § 19.1).
- **"Go to x, y, z"** (help panel): metres, **frame of the original model in tiles mode, frame of the page (recentred model) in single-GLB mode** (the panel says so). Formats: `68.2, 39, -823.3`; `68.2 39 -823.3`; `68,2 ; 39,0 ; -823,3` (decimal comma with semicolons). In walk mode: teleport, waiting for the tile; in the global view: the target moves.

### 18.5 Chat

- **Persistent input**: **Enter** opens the input, **Enter sends and keeps it open** (field emptied), **Esc** closes it and gives the keys back to walk mode. While it is open, letters go into the text, but the **arrows** move and turn the avatar. The state is written in the help. Nothing changes for those who do not use the chat.
- **Save the chat**: button under the chat. Downloads a UTF-8 text file (with byte order mark, readable in Notepad, Windows line endings): one line `jj/mm/aaaa hh:mm:ss | Nom | texte` per message received or sent **since your arrival**. Everything happens in the browser: **nothing is stored on the server side for you**. Note: the presence server keeps in memory the last messages of a room (`--history`, 20 by default) and replays them when a visitor arrives; they are displayed but **are not in the file** (they come before the arrival).
- **Mentioned nickname**: when your nickname appears in a received message **as a whole word**, ignoring case, with or without `@` in front (`@alice`, `ALICE,`, `l'alice` yes; `Alicex`, `Alicia` no), the message is shown **in bold and preceded by "@"**, the **author's bubble blinks** 6 times (visible 150 ms, hidden 150 ms) and a **short beep** is played (Web Audio, moderate volume, no file; only after a first interaction with the page, a browser rule). Three boxes in "Settings": bold, blinking (checked by default), sound (unchecked by default), remembered in the browser. No change on the server side. Everything is redundant with the text: nothing depends on colour.
- **`@` completion**: when the text ends with `@` followed by letters, a list of **at most 5 nicknames** (online visitors whose nickname starts with these letters) is shown above the input; **up and down arrows** to choose (the choice is marked by `▶`, in bold and inverted), **Tab or Enter** insert `@Pseudo ` (Enter does not send while the list is open), **Esc** closes the list without closing the input. Empty list: nothing is shown.

### 18.6 Avatar colour (client and server)

Settings → "Choose my avatar's color": the value is remembered in the browser and **sent in the `hello` message** (integer from 0 to 0xFFFFFF). `presence_server.py` accepts it if it is **an integer between 0 and 0xFFFFFF**; otherwise (out of range, float, text, boolean, null, list) it **rejects it silently** and picks a random colour, as before, then broadcasts it as the current colour. An old client (without colour) works; an old server simply ignores the field. Since v34, the change is **sent at once** (§ 19.5). **The displayed name stays the main marker** (label above the avatar); nothing is based on colour alone.

**To do on the server side: restart `presence_server.py` with the new version** (the chosen colour is only taken into account by v33 of the server). Typical command (a single line, to adapt to your options):

```
python .\presence_server.py --host 0.0.0.0 --port 8765 --log presence.log --log-days 30 --log-ip raw
```

(Since v37 the recommended launch example is `python .\presence_server.py --log presence.log --log-ip raw --log-days 0`; see § 22.6 for `--log-days 0`, the chat history and personal data.)

### 18.7 IP addresses in the log: `--log-ip raw`

The existing `--log-ip` option accepts `hash` (default: 8-character fingerprint), `raw` (**address in clear**) or `none`. With `raw`, the address appears **from the connection**, in the console and in the log (`--log`): `connection | room=… | Name [id 3, key a1b2c3, ip ADRESSE]`. Checked by `tests/v33.py` (default: fingerprint; `raw`: address in clear, in the console and in the file).

**Reminder: an IP address is personal data.** Tell your visitors that the log records them (and for what purpose), limit the retention period with `--log-days` (30 days by default; the log rotates every night), and never publish the log.

### 18.8 Save the zones directly in the region folder (viewer)

In tiles mode, "Zones" section of the viewer: **"Save the zones in the region folder"** button.

1. **Edge or Chrome** (File System Access API): the button asks **only once** for the region folder (the one containing `X.tiles.json`, read-write access). It is remembered for the session (and in IndexedDB when the browser allows it, so as not to ask again; the browser may ask again to confirm access).
2. `X.zones.json` is written there (X = name of `X.tiles.json` without extension), **after keeping the old one as `X.zones.bak.json`** (a single copy, overwritten at each save).
3. The viewer shows as text the folder, the file, the date dd/mm/yyyy and the time. (The browser does not give the full path, only the folder name.) If the chosen folder does not contain `X.tiles.json`, nothing is written.
4. **Without the API (Firefox, Safari), or if access is refused**: the file is downloaded and the viewer says "save this file in the region folder, under the name X.zones.json, replacing the old one". Folder choice cancelled: nothing is written.

**The shell reads `X.zones.json` again at each opening**: after this save, **F5 is enough** in the browser, **without generating the page again** — unless you change the options of the page (`--zone-marker`, `--target`, `--presence-url`…), which are in `X.config.json`.

### 18.9 `glb2html.py --tiles --zones` with the file already in place

If `--zones FICHIER` designates **the destination `X.zones.json`** (same path once resolved, absolute or relative), nothing is copied, nothing is rewritten, nothing fails: the script says "zones already in place". The file is therefore not filtered by the `public` profile nor reformatted. Without `--zones`, an existing `X.zones.json` is kept anyway.

### 18.10 Update a region already published

The shell (`index.html`), `core.js` and `X.config.json` change; **the tiles and `X.tiles.json` do not change** (no new split). Delete the region's `index.html` shell (an existing and different shell is never overwritten), generate the page again **without `--zones`** (the existing `X.zones.json` is kept), restart `presence_server.py` (§ 18.6).

## 19. New in v34 (22/10/2026)

### 19.1 Selectable help panel and status block

- The **help text** (**H** key) can be selected with the mouse and copied with **Ctrl+C**, without a "copy" button; **Ctrl+C is no longer intercepted** by walk mode (the **C** key alone still goes down in flight). The help receives the mouse: hovering over zone markers no longer works **under** the help, it works everywhere else. Its size is limited (width of at most 440 px and 45 % of the window, height of 42 % of the window with scrolling).
- New **status block**, separate from the help, below it, with selectable text too: `View: …` (first person, third person, free camera, or global in orbit), `Mode: on foot` / `Mode: flying`, `Mouse: …` (§ 19.4), `Position avatar: x … y … z …` (or target of the global view), then the lines of the tiles and of the overview. The help only keeps the keys and the settings.
- **H** hides the help alone (the status stays). **I** hides or shows the status block (choice remembered in the browser, key `glb2html_state`).
- The label "View: third person · on the ground" is replaced by two lines: "View: third person" and "Mode: on foot".

### 19.2 Hover and click area of the markers

| Option                        | Radius of the hover / click area (invisible disc on the ground)                                                                                      |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--zone-marker range`         | **the radius of the visible ring** (real radius of the zone; at least 2 m for a sign): the tooltip appears when hovering over the ring or its inside |
| `--zone-marker dot` (default) | the radius of the zone limited between **0.6 m** (as before) and **1 m**                                                                             |
| `--zone-marker none`          | 0.6 m, as before                                                                                                                                     |

### 19.3 Flight

**Page Up** goes up, **Page Down** goes down (in addition to **Space** held and **C**, v36), without scrolling the page. **Home** keeps the toggle. When you go down to the ground, **the avatar lands by itself** (flight stops, gravity resumes); it never goes below the ground. The **"Fly / Land"** button in the bottom bar (visible in walk mode, absent with `--no-fly`) toggles flight; its state (`aria-pressed`) and the "Mode: …" line say it as text.

### 19.4 Free mouse after Esc

In walk mode, when the pointer is released (Esc, or loss of focus), the page remembers **"free mouse"**, writes "Mouse: free (G or the “Capture the mouse” button to grab it again)" in the status block and **no longer asks for the lock again**: a single click, a double-click (teleport to the spot under the cursor) and a click on a zone work where the cursor is; dragging with the button held still turns the view. **Capture again**: **G** key or **"Capture the mouse"** button (bottom bar). The state is reset each time walk mode is entered (the first click captures as before).

### 19.5 Live colour

Changing the colour in the Settings while connected sends `{"t":"color","color":N}` (at most every 300 ms, the last value is always sent). `presence_server.py` accepts an **integer from 0 to 0xFFFFFF** (otherwise silently ignored), ignores two changes less than 0.2 s apart, updates the visitor and broadcasts `{"t":"color","id":…,"color":N}` to the others; a visitor arriving afterwards gets the updated colour. The visitor's own avatar (third-person view) takes it too. Compatible: an old server ignores the message, an old client does not send it. **Restart `presence_server.py`** to benefit from it.

### 19.6 `glb2html.py --update`: update a region without typing anything again

| Option     | Effect                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--update` | reads the existing `X.config.json`, **applies only the options explicitly given** (a value equal to the default value, but given, is applied), keeps everything else (unknown keys included) and `X.zones.json` (rewritten only with `--zones`), writes the current version, **renews the shell** if it differs from the one of this version (old copy kept as `index.avant-AAAAMMJJ-HHMMSS.html`) and writes `lib/` if it is missing. Without `X.config.json`, fails and suggests the command without `--update`. Excludes `--settings` |

Form: `python glb2html.py --update -o "X.html" [--shared-shell [COQUILLE.html]] [--tiles "X.tiles.json" | "X.glb"] [options]`. Without `--shared-shell`, the page `X.html` must exist. The shell is **shared by the other regions of the folder**: they keep their behaviour (old configurations are still understood; no config key is new in v34). The report lists the keys changed. The profile (`--profile`) only filters the zones when the list is written: add `--zones` to rewrite it.

### 19.7 Nickname, personal link, launch page

- **`#name=PSEUDO`** in the address sets the nickname (remembered in the browser); portals and the map already add it.
- Settings → **"Copy my personal link"**: copies the address of the page with `#name=PSEUDO&key=CLE`, where CLE is the **identity key of the browser** (32 hexadecimal characters, `glb2html_uid`, the one the server associates with the reserved name). **This link is a secret: whoever opens it takes the identity** (the reserved name). When opening, a key in the right format becomes the browser's; if this browser already has a **different** one, a message on screen asks for confirmation before replacing it. The key is then **removed from the visible address**. A key in the wrong format is ignored (and removed). No change to the server.
- **Map page** (`--map-page`): **"My nickname"** field at the top, remembered in the browser; the links to the regions get `#spawn=…&name=PSEUDO`.

## 20. New in v35 (22/10/2026)

### 20.1 Help in groups, collapsible panels

- The help is written in **short groups**, one line per group, without sentences: **Movement**, **Flight**, **View**, **Mouse**, **Chat**, **Zones**, **Page** (in the global view: **Global view**, **Walk**, **Zones**, **Page**). The mention "Ctrl+C copies" and the explanation of the selection are gone; the text stays selectable.
- The help and the status block each have a **title bar** ("▾ Help", "▾ Status"): a click **collapses** it ("▸ Help", only the bar stays) or expands it. The title says the state as text (arrow and `aria-expanded`), never by colour. The collapsed or expanded state is **remembered in the browser** (keys `glb2html_helpFold` and `glb2html_stateFold`). **H** and **I** still hide the help and the status completely.
- The "Leave the walk (F)" button is removed (the **P** key is enough). In the global view, the button is called "Walk (P)".

### 20.2 Firestorm keys / keys of this page

Left column: the defaults of the official viewer according to the Second Life wiki (Quick Start Guide, "Keyboard Shortcuts"), which Firestorm takes over as far as I know; they were not compared here with an installation of Firestorm.

| Command                   | Firestorm                                             | This page                                                                                                                                                 |
| ------------------------- | ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Walk forwards / backwards | W or ↑ / S or ↓                                       | W or ↑ / S or ↓ (ZQSD on AZERTY; v36: the help shows the real letters)                                                                                    |
| Step sideways             | A / D (or Shift + arrows)                             | A / D (Q / D on AZERTY)                                                                                                                                   |
| Turn                      | ← / →                                                 | ← / → (in third person: turns the camera)                                                                                                                 |
| Run                       | double press on W / S / ↑ / ↓; Ctrl+R toggles running | **Shift**, or **double press** (less than 300 ms) on W, S, ↑ or ↓, as long as the key is held. **No permanent running** (Ctrl+R reloads the browser page) |
| Jump                      | E or Page Up (short press)                            | **Page Up** (short press) or **Space** (v36: E no longer jumps)                                                                                           |
| Fly / land                | Home                                                  | **Home** or the "Fly / Land" button (v36: F no longer toggles flight)                                                                                     |
| Take off                  | E or Page Up held                                     | **Page Up** held **more than 0.4 s** on the ground: flight + climb                                                                                        |
| Go up in flight           | E or Page Up                                          | **Page Up** or **Space** held                                                                                                                             |
| Go down in flight         | C or Page Down                                        | **C** or **Page Down** held; **automatic landing** on the ground                                                                                          |
| First-person view         | M                                                     | **M** toggles first person / third person; **V** cycles through the three views (including the free camera)                                               |
| Orbit the camera          | Alt + drag                                            | **Alt + drag** (in third person, the mouse already orbits around the avatar without turning it)                                                           |
| Camera behind the avatar  | Esc                                                   | **End** or **Alt + click** (Esc is reserved for the browser: it releases the mouse)                                                                       |
| Camera zoom               | wheel                                                 | **wheel** (3rd person: camera distance; free camera: forwards / backwards)                                                                                |
| World map                 | Ctrl+M                                                | **Ctrl+M** everywhere; **M** alone also opens it outside walk mode                                                                                        |
| Chat                      | Enter                                                 | **Enter**                                                                                                                                                 |
| Enter / leave walk mode   | (does not exist)                                      | **P** or **F** (v36)                                                                                                                                      |
| Touch an object, a zone   | click                                                 | **click** or **E** (v36); a "walking into it" portal fires when entering its radius                                                                       |
| Teleport                  | (map, double-click depending on the setting)          | **double-click**                                                                                                                                          |
| On-screen arrows          | (does not exist)                                      | **K** or the "Arrows (K)" button hides or shows them (v46, § 29)                                                                                          |

Kept as they are: ZQSD / WASD / arrows, Space, Enter, G, R, V, H, I, Shift.

### 20.3 Flight and jump

- On the ground, **Page Up**: a short press **jumps** (like Space); **held more than 0.4 s**, the avatar **takes off** and climbs as long as the key is held. When released, it stays in flight, motionless in height.
- **Home** toggles flight (v36: F no longer does); the "Fly / Land" button stays. Going down to the ground (C or Page Down) lands the avatar: flight stops by itself (v34). With `--no-fly`, none of this makes you fly: Page Up only jumps.

### 20.4 Third person

- The **mouse orbits the camera** around the avatar (yaw and pitch of the camera itself) **without turning it**; when standing still, the avatar keeps its heading: you can turn around it and see its front.
- When a walking key is pressed, **the avatar turns towards its direction of movement** (smoothed rotation, a few tenths of a second); walking forwards goes **in the direction of the camera**. The camera goes through neither ground nor wall, as before.
- **Presence transmits the heading of the avatar**, not that of the camera: turning the camera by 180° without walking changes nothing for the other visitors. First person and free camera are unchanged. **M** (or V) changes view; when switching to first person the gaze keeps the direction of the camera.

### 20.5 Zone tooltip and click: `--zone-info-dist`

| Option               | Config         | Effect                                                                                                                                                                                                                                                                                                                                                                                                                            |
| -------------------- | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--zone-info-dist M` | `zoneInfoDist` | distance, **in walk mode**, up to which the tooltip, the click and the **displayed name** ("Always show the name") of the zones work. **150 m by default since v37** (40 m in v35 and v36), from **5 to 500** (out of range: brought back to the limit). Adjustable in the viewer ("Walk" section), carried into the command line. A name further away than this distance is hidden in walk mode and reappears in the global view |

`glb2html.py --update --zone-info-dist 60` is enough to apply it to a region already published (§ 20.7).

### 20.6 Copy to the clipboard

All the "copy" buttons (personal link, link to my position, targeted point, target, command) use `navigator.clipboard.writeText` in a **secure context** (https, localhost), and otherwise, **over http on a public address**, a fallback: temporary off-screen field, selection, `document.execCommand('copy')`, removal. The page shows **"Copied"** for a few seconds. If everything fails, the link field stays **displayed and selected**, with "Copy failed: the text is selected, press Ctrl+C".

### 20.7 `--update` and the world map

`glb2html.py --update` now also accepts `--register FICHIER`, `--region-name`, `--region-xy`, `--region-url`, `--region-spawn`, `--thumb`, `--map`, `--map-url` and `--map-page FICHIER.html`: it applies what is given and keeps everything else (config and zones, as before). The room and the presence of the card come from the existing config when you do not give them again.

**With `--update`, the relative paths of `--register`, `--map`, `--map-page` and `--thumb` are relative to the page's folder (that of `-o`)**, and not to the tools folder or to the launch folder; the final message repeats it with the folder. An absolute path is respected. `--region-name`, `--region-url`, `--region-xy`, `--region-spawn` and `--thumb` without `--register` are ignored with a warning.

**Without `--update`**, the old behaviour is kept (a relative path of `--register` is looked for in the launch folder, otherwise in the tools folder, where it is created); when the file is not next to the `-o` page, a line says where `regions.json` is written and suggests `--update` or a full path.

### 20.8 Create the world map

1. **Each region is registered in the same `regions.json`**, next to the pages (a single folder of pages, a common shell). For each region already generated, a `--update --register` command, **a single PowerShell line** (name, position on the OpenSim grid, optional thumbnail of at most 140 KB next to the page):
   
   `python glb2html.py --update -o "X.html" --shared-shell --register regions.json --region-name "Display name" --region-xy 1000,1001 --thumb vignette.png`
   
   The card gets the address `index.html?region=X`, the room and the presence server of the region's config. Giving the command again updates the card (identified by the room), without duplicates.

2. **Generate the web page of the map**: `python glb2html.py --update -o "X.html" --shared-shell --map-page carte.html` (it reads the regions of `regions.json` registered in the config of region `X`). For it to contain all the regions, run it **after** the registrations, or give `--map regions.json --map-page carte.html`.

3. **Open it through the web server**, not from the disk: the folder containing `carte.html`, `index.html`, `lib/` and the regions is served over http(s) (`python -m http.server` for a test, or any web server), then open `http://ADRESSE/carte.html`. Each link of the map opens the region at its arrival point, with the nickname typed at the top of the page.

4. **The region pages** show the map with the **M** key (**Ctrl+M** in walk mode): `--map-url http://ADRESSE/regions.json` (several addresses separated by commas, merged) makes them read `regions.json` again at each opening, without generating the pages again.

**Since v47**: the map page can also be a universal `carte.html`, with no region inside, that re-reads `regions.json` at every opening (§ 30.4).

### 20.9 Free camera and wheel

- **Third person**: the **wheel** sets the camera distance (from **1 to 30 m**, **4 m by default**, remembered in the browser, key `glb2html_tpsDist`), with the pull-back in front of a wall and the ground protection already in place. **End** puts the camera back behind the avatar at the default distance.
- **Free camera**: the wheel **moves the camera forwards or backwards along the line of sight**, by a step proportional to the camera-avatar distance (15 %, at least 0.5 m and at most 20 m per notch), never below the ground. The **speed of the keys** is `max(walking speed, 0.5 x camera-avatar distance)` m/s, capped at **60 m/s**; **Shift multiplies it by 3**. **Alt + drag** orbits the camera around the avatar keeping its distance (yaw and pitch), the gaze staying on it. **End** puts it back behind the avatar, at 4 m.
- **First person**: the wheel does nothing. In all cases the page does not scroll in walk mode (over the view; the help and the status keep their scrolling).

## 21. New in v36 (23/10/2026)

### 21.1 Keys: F and P, E, flight

- **F** and **P** enter and leave walk mode (from the global view as from walk mode). In the **viewer**, P places a zone in walk mode; leave with **F**, **Shift+P** or the button.
- **F no longer toggles flight.** Fly / land: **Home**, the "Fly / Land" button, or **Page Up** held more than 0.4 s on the ground. Go up in flight: **Page Up** or **Space** held. Go down: **Page Down** or **C** (automatic landing on the ground). Jump on the ground: **Space**, or **Page Up** with a short press.
- **E** is again the action key of the zones (trigger "on click" or "both"): the prompt says "click or E: …". E does nothing else (it no longer jumps, no longer goes up).

### 21.2 Keyboard layout: AZERTY or QWERTY

Walking keeps the **physical** keys (those that are Z, Q, S, D on an AZERTY keyboard are W, A, S, D on a QWERTY one): nothing changes to play. The **help** and the **Information / Status** window show the **real** letters of your layout ("Z Q S D" or "W A S D", never both at once). The layout is detected with `navigator.keyboard.getLayoutMap()` when the browser has it (Chrome, Edge; only over https or on localhost), otherwise with the browser language (fr, fr-FR and fr-BE: AZERTY; the rest: QWERTY). Visitor setting **"Keyboard layout: Auto / AZERTY / QWERTY"** (Settings, remembered); same setting in the viewer. **M** (first person / third person in walk mode, world map otherwise; Ctrl+M: map everywhere) is recognised by the **printed letter "m"**, not by the position of the key: on an AZERTY keyboard it is the real M key (before v36, it was the "," key).

### 21.3 Help and information: three steps

The "Status" window is called **Information / Status**. **H** (help) and **I** (information) cycle the window: **hidden → shown expanded**; **collapsed → expanded**; **expanded → hidden**. A click on the title bar collapses / expands; the state (hidden, collapsed, expanded) is remembered in the browser.

### 21.4 Portal markers (cones): `--zone-cone`, T key

Above each portal and each "walking into it" or "both" zone, the page draws a small **cone pointing downwards** (about 0.35 m wide, 0.5 m high, tip 2 m above the centre of the zone; light neutral tint, dark outline: it can be read without depending on colour). It is added to `--zone-marker` (it does not replace it). Visible up to `--zone-info-dist` (150 m by default since v37); hovering over the cone shows the same tooltip as the zone, with the **distance** to the visitor (§ 22.2). Since v37 its **apparent size is constant** (§ 22.2). **T** shows or hides all the cones (choice remembered). `--no-zone-cone` hides them at the start (config `zoneCone`); arrivals only have a cone with `--show-spawns`.

### 21.5 Occupied arrival

When the avatar is placed on a point (opening, `#spawn=`, `#pos=`, default arrival, **R**, internal portal or portal to another region, "Go to"), if another visitor in walk mode is less than **1 m** away (2 m in height), the **newcomer** is shifted to the nearest free point: rings of 1.2, 2.4 then 3.6 m, ground less than 1 m apart in height, no wall between the two points, no visitor closer than 1 m. **(Rule replaced in v37: see § 22.3; the rings are now around the occupant.)** If presence is not connected yet, the check is done again when the list of visitors arrives, only if the avatar has not moved more than 0.3 m (someone who is walking is never moved). Without a free place within 3.6 m, the avatar is placed at the requested spot. Visitors in the global view are invisible: ignored.

### 21.6 Sounds

Visitor settings: general **"Sounds"** box (checked) with a **volume** from 0 to 100 (50), then three checked boxes: "Beep when a message mentions my nickname", "Sound when a visitor arrives" (two rising notes), "Sound when a visitor leaves" (two falling notes). The sounds are synthesised (Web Audio), without files; they only concern visitors **in walk mode** in your room (never spectators, never you, never those already present when you arrive), at most one arrival sound and one departure sound every 2 s. The browser only allows sound after a first action on your part on the page. The old beep settings (key `sound`) are ignored.

### 21.7 Copy my position, "Go to"

"**Copy my position**" (help panel) copies, depending on the list next to it (remembered): **URL** = the address of the page with `#pos=x,y,z,cap`; **xyz** = `68.2, 39.0, -823.3` (metres, decimal point, one decimal). The "**Go to**" field accepts both, as well as the earlier formats; with a full address containing `#pos=x,y,z,cap`, it also takes the heading.

### 21.8 Page language

The whole interface (help, settings, information, prompts, loading and error messages, chat, map, "world map" page, viewer) exists in **French** and in **English**. Visitor setting **"Language / Langue"**: **Auto** (the first language of `navigator.languages` that is available, otherwise English), then each available language. Changing the language reloads the page. The **`#lang=en`** parameter (or `#lang=fr`, `#lang=auto`) in the address takes priority and is remembered; it combines with `#spawn=`, `#pos=`, `#name=`. The texts **you** type (zone names, signs, nicknames) are never translated.

### 21.9 Add a language (without touching the code)

1. Copy `src/i18n/en.json` to `src/i18n/<code>.json` (the code is that of `navigator.language`: `de`, `es`, `pt`…).
2. Translate the **values** (never the keys). `_name` = the name of the language in that language ("Deutsch"). `{0}`, `{1}`… are markers to keep as they are (they can move); keys ending in `.one` / `.other` (plural) can also have `.zero`, `.two`, `.few`, `.many` if your language needs them. A missing key is replaced by English, then French, then the key itself: a partial translation works.
3. Keys starting with `page.`, `core.`, `viewer.`, `map.` and `common.` are those of the pages and the viewer; those starting with `py.` are those of the Python tools (`--lang`, § 21.11).
4. Build with `python build.py` (the language folder is chosen with `--i18n DOSSIER`): the "Language / Langue" list offers the new language, the pages and the tools of `dist\` embed it. No code to change. `python tests/i18n.py` checks the language files (same keys, same markers, no unused key).

### 21.10 Viewer language

The viewer (`glb-viewer.html`) has the same "**Language / Langue**" list as the exported pages (Auto, then each available language), the same fallback (English, then French, then the key) and the same `#lang=` parameter. All its texts are translated (settings, buttons, messages, help), including the "Keyboard" section (Auto / AZERTY / QWERTY) and the commands it builds; the zone names you type never are. The pages the viewer exports (standalone HTML, modular `.zip`) contain the same shell as `glb2html.py`: their language is set on the exported page, not in the viewer.

### 21.11 Language of the Python tools: `--lang`, `WEB3D_LANG`

`glb2html.py`, `glb2tiles.py`, `oar2glb.py` and `presence_server.py` (and `glb-stats.py`, used by `glb2tiles.py`) show their messages, warnings, errors and help (`--help`) in French or in English. **Choice of language**: `--lang fr`, `--lang en` or `--lang auto` (default); otherwise the `WEB3D_LANG` environment variable; otherwise the system language; otherwise English. `--lang` takes precedence over `WEB3D_LANG`. The options themselves (`--budget`, `--exclude`…) and the moderation commands of the server (`list`, `kick`, `ban`, `bans`, `unban`, `help`, and their French equivalents) do not depend on the language. Output files (JSON, tool logs) keep their keys; the logs are written in the chosen language.

**Standalone files**: `build.py` embeds the texts of `src/i18n/*.json` (`py.*` keys) in each tool of `dist\`: a tool copied alone to another machine keeps its two languages (a build choice, documented in `CLAUDE.md`). From the sources (`tools\`, `src\`), the tools read `i18n_py.py` and `i18n\` next to them or in `src\`. Adding a language: § 21.9, no code to change. A new option of a tool must have its `py.*` key in **both** files (`python tests/i18n.py` checks it); `python gen_reference.py` regenerates `REFERENCE_OPTIONS.md` (French then English in each "Effect" cell), `python tests/doc_options.py` checks that no option is missing from it and that no description is empty.

## 22. New in v37 (23/10/2026)

### 22.1 Running indicator, compass, resizable windows, O key

- The **Mode** line of the Information / Status window shows **"on foot · running"** or **"flying · running"** as long as running is active (**Shift** key held, or fast double press in progress), then goes back to "on foot" or "flying".
- **Compass**: at the top of the page, in the centre, the heading as text, cardinal point then degrees ("NE 45°"). It is the heading of the **avatar** in walk mode, of the **camera** in the global view. OpenSim convention: north is the **-Z** direction of the model (z = -y of OpenSim); the rotation of the region (`rotate`) is taken into account. Letters: French N, NE, E, SE, S, SO, O, NO; English N, NE, E, SE, S, SW, W, NW. **"Compass"** box in the visitor Settings (checked by default, remembered). Options of `glb2html.py`: `--compass` / `--no-compass` (config `compass`, enabled by default) and `--north DEGRES` (config `northDeg`, default 0) for a GLB that does not come from OpenSim: the offset is **added** to the heading displayed (180: facing -Z, the compass shows S). `--update` applies them.
- **Help and Information windows**: a **right edge to drag** (resize cursor, double line on the edge) sets the width of each, from **260 px** to **70 %** of the browser window; the width is **remembered** in the browser. The text reflows and the **height follows the content** (the help's scroll bar only appears if the browser window is too low: at 260 px wide the help needs about 730 px of height). The two windows stay stacked at the bottom left: when the help loses height, it moves down to stay stuck to the information window. The 440 px / 45 % of v34 are the default values.
- **O** key: opens / closes the **Settings** window (R is already taken).

### 22.2 Portal marker (cone): constant size, distance

The cone keeps the **same apparent size**: its scale follows the distance to the camera (distance / 12, between 1 and 12), its tip stays at the same point and its shape does not change. It stays visible up to `zoneInfoDist`, **150 m by default** (range 5 to 500). Its tooltip adds the **distance to the visitor**, rounded to the metre and updated when you move: "Portal → château · 120 m" (in the global view: distance to the camera).

### 22.3 Occupied arrival, improved

The free point chosen is the one closest to the **occupant** (and not to the requested point): rings of **1.5, 2.0 then 3.0 m** around them (16 candidates per ring), same ground, wall and distance-to-other-visitors conditions as in v36; within the ring, the candidate closest to the requested point. The newcomer is then **turned towards the occupant** (the closest one if there are several). A line is written in the browser console: "occupied arrival: moved X m (ring R m)".

### 22.4 Mentioned nickname: continuous blinking

When a message mentions my nickname, the alert blinks on **my page only**: half a second visible, half a second hidden, on the **author's name label** (which stays even when their bubble has disappeared), their **bubble** if it still exists, and the **message line** in the chat. **Without a time limit**: the blinking goes on until my first action (key, click, movement of the avatar, sending a message), then everything stays visible. Several mentions before my action all blink. The text is not just a colour: the element disappears and reappears. (Replaces the 6 blinks of 300 ms of v33.)

### 22.5 Link parameters after `#`

The separator is **`&`**; **`#` is also accepted**: `#name=Klaatou&lang=en` and `#name=Klaatou#lang=en` are equivalent (`name`, `lang`, `spawn`, `pos`, `key`). A single function (`hashParams`) reads the link in the page, the shell and the map page.

### 22.6 Chat history

- `presence_server.py --history N`: last messages replayed to newcomers, **200 by default** (20 before), 0 = none.
- `--history-file FICHIER` (disabled by default): each message is appended to the file, one JSON line per message: `{"n":number,"t":Unix seconds,"d":"dd/mm/yyyy hh:mm:ss","room":room,"name":nickname,"text":text}`. **Never the IP address.** The file is read back at startup: the history survives restarts (up to 20,000 messages per room in memory).
- `--history-days N` (default 30; **0 = keep everything**): at startup, older messages are neither read back nor kept (the file is rewritten without them).
- **Protocol**: the client sends `{t:'history', before:N, n:50}` (N = number of the oldest message displayed); the server answers `{t:'history', msgs:[…], more:true|false}` for its room (at most 100 messages, one request every 0.2 s). Each message (welcome, broadcast, history page) also carries `n` and `t`/`ts`; old clients ignore them. An old server does not answer: the "Older messages" button hides itself after 4 s.
- **Page**: the open chat panel **scrolls**. Visitor setting **"History messages kept in the chat"** (200 by default, from 20 to 2000, remembered). **"Older messages"** button (in batches of 50, inserted at the top; hidden if `more` is false or if the server does not answer). **Tab title**: "(3) RegionName" = unread messages when the page is hidden or the chat collapsed, reset to zero when the chat is opened (intended behaviour: opening the chat counts as reading all the messages, even without scrolling through them). **"N messages mention you"** with a "Go to the first" button (these messages keep the blinking of § 22.4 until my first action).
- **Personal data.** The messages (nickname, text, time) are personal data: inform your visitors, limit the duration with `--history-days`, protect the file. Likewise **`--log-days 0` keeps the logs without limit** (the nightly rotation continues but no file is deleted any more): only use it if you take responsibility for it.
- Command to launch the server (a single line; **restart the server** to benefit from the history): `python .\presence_server.py --log presence.log --log-ip raw --log-days 0`; add `--history-file chat.jsonl` to keep the history between two restarts.

### 22.7 Default region (`default.json`)

When the address of the shell has no `region` parameter, it tries in this order: (a) `X.config.json` of the page's name (previous behaviour); (b) **`default.json`** of the folder, of the form `{"region": "NOM"}`; (c) the **first entry of `regions.json`** whose address is relative and whose `?region=NOM` parameter is valid; (d) otherwise a one-sentence message saying what to do. The name goes through the same security checks as `?region=`. `glb2html.py --shared-shell` writes `default.json` the **first time** it builds a region in a folder where it does not exist; **`--default`** makes the region being built the default region even if `default.json` exists. `--update` never overwrites it, except with `--default`.

### 22.8 lib folder: `--lib-url`

`--lib-url CHEMIN`: relative path (for example `../lib`) or full `http(s)` address where three.js and its modules are found. It is written into the `const LIB = './lib';` line at the start of the shell (§ 28.4) when the shell is written, and kept in the config (`libUrl`) so that `--update` finds it again. Relative path: `lib/three-X/` is created there if it is missing; full address: nothing is copied. An existing shell is never overwritten: to change the folder of a shell already in place, edit the `const LIB` line by hand (§ 28.4) or use `--update --lib-url CHEMIN` (dated copy of the old one). Refused values: `?`, `#`, `\`, quotes, other schemes (`javascript:`), paths starting with `/`.

### 22.9 Regions in subfolders

`?region=` accepts `dossier/nom` or `a/b/nom`: segments made of letters, digits, dot (not at the start), hyphen, underscore, space and parentheses; never `..`, `:`, `\`, `?`, `#`, nor a path starting with `/`. The config, the GLB or the tiles, the zones (and `zones.json` of that folder) and the overview are resolved from the **region's folder** (the paths of the config are relative to this folder). Build: `glb2html.py X.glb --shared-shell P:\site\index.html -o P:\site\sous\dossier\Ile.html` (the path of the shell designates the parent folder; the region must be below it; shell, `lib/` and `default.json` are written in this parent folder; combines with `--lib-url`). The address becomes `index.html?region=sous/dossier/Ile`.

### 22.10 Tests of v37

`tests/v37.py` (batch 1), `tests/v37_chat.py` (batch 2), `tests/v37_region.py` (batch 3), shared helper `tests/h37.py`. Expectations adapted because a v37 rule requires it: `v33.py` (the blinking no longer stops by itself: it stops on a key), `v35.py` (zoneInfoDist 150 by default, limits 5 and 500; the 40 m tests ask for `--zone-info-dist 40`), `v36.py` (the tip of the cone stays in place when the scale changes).

## 23. New in v39 (23/10/2026)

### 23.1 "Copy diagnostics" button

At the bottom of the **Information / Status** window (**I** key), the **"Copy diagnostics"** button copies to the clipboard a text to paste as is into a help conversation: it replaces readings from the F12 console. The button stays visible when the window is collapsed; it does not keep the focus (Space and Enter stay with walking and the chat). The same button is at the top of the viewer panel (`glb-viewer.html`).

The text contains: the code version (and the region configuration version if it differs), the date, the time since opening, the page address, the language, the keyboard, the browser, the window size, the graphics card as seen by WebGL, the rendering of the last frame (triangles, draw calls, geometries, textures), the JavaScript memory (Chrome and Edge only), the tiles (ready, loading, failed) and their timings (first and last ready, median and maximum per tile), the lines shown in the Information / Status window, the presence status, then **the last 10 errors and warnings** of the page (uncaught errors, rejected promises, `console.error`, `console.warn`, files that fail to load).

**Nothing private**: the host of the page and of any server is replaced by `ADRESSE`, and so are IP addresses; the `#` part of the address (nickname, key) is never copied.

If the browser refuses to copy (page over `http://` other than `localhost`), the text is shown **already selected** under the button: **Ctrl+C**. A page built with `--no-walk` has no Information / Status window, hence no button.

### 23.2 v39 tests

`tests/v39.py`: button present in the page and in the viewer, in French and in English, addresses masked, errors captured, timings of a region split into tiles.

## 24. New in v40 (24/10/2026)

### 24.1 "Arrivals" window (L key)

Below the **Information / Status** window, the **Arrivals** window lists the region's arrival points (`default` first, then by name; the label replaces the identifier when there is one). On hover, a tooltip recalls its role: list of available teleport points (TP).

- **In walk mode**, clicking a name teleports to that arrival point.
- **In global view**, clicking a name enters walk mode at that arrival point.
- **L** cycles the window like **H** and **I**: hidden → expanded; collapsed → expanded; expanded → hidden. The "▾ Arrivals" title collapses or expands it. The states are remembered in the browser (keys `glb2html_spawn` and `glb2html_spawnFold`).
- A region without an arrival point has no such window; **L** says so with a message, and the help does not mention **L**.

### 24.2 "Recenter the view" button

In the bottom bar, outside walk mode only: the **"Recenter the view"** button restores the region's opening framing (same center, same angle, same distance as at the end of loading). **R** stays the return to the arrival point: in global view, it centers the view on the arrival point while keeping the angle and distance.

### 24.3 "Full manual" link and diagnostics tooltip

The help window (**H**) ends with a **"Full manual (online)"** link to this manual on GitHub, in French if the page is in French, in English otherwise (an Internet connection is needed). The viewer has the same link under the "Copy diagnostics" button. That button now has a tooltip explaining what it copies and what it never copies.

### 24.4 v40 tests

`tests/v40.py`: list and order of the arrival points, L key, teleport on click (global view and walk mode), "Recenter the view" button (exact opening framing), region without an arrival point, help, manual link and diagnostics tooltip in French and in English, viewer.

## 25. New in v41 (24/10/2026)

### 25.1 Window tooltips

On hovering the title, each window gives its role and its key: **Help** (H), **Information / Status** (I), **Arrivals** (L), then how to collapse it, move it and put it back in its stack. The **Settings** button has its tooltip too (O).

### 25.2 Movable windows

The **Help**, **Information / Status** and **Arrivals** windows move by **dragging their title**. There are two stacks:

- **the left stack**, at the bottom of the screen: the original place of the three windows;
- **the right stack**, below the **Settings** button: when Settings opens, it moves down by as much; when it closes, it moves back up.

A window dropped on a stack docks to it, at the height where it is dropped. Dropped elsewhere, it stays **free**, exactly where it was put, above the view. A **double-click on the title** sends it back to the last stack it was docked to (the left one if it never knew another). If the browser window shrinks, a free window is brought back on screen; its remembered position does not change.

A **click** on the title still collapses or expands the window, but **250 ms after the click** when made with the mouse: a double-click therefore does not collapse it. The right edge keeps its v37 role (drag to change the width); the width of the Arrivals window can be set too.

### 25.3 Remembered layout and layout file

The layout (stack or position of each window, order in the stacks) is remembered by the browser (key `glb2html_layout`), together with the open / collapsed states and the widths. It depends on the browser and on the page address.

In **Settings**, **Window layout** section:

- **"Save the layout"** downloads a `disposition.json` file (Downloads folder, or the location the browser asks for);
- **"Load a layout"** opens the file picker and applies the chosen `.json` at once, without reloading the page. A file that is not a layout is refused and nothing changes;
- **"Original layout"** puts the three windows back in the left stack and clears the widths.

A web page cannot write on its own into a file chosen in advance: saving therefore goes through a download.

### 25.4 v41 tests

`tests/v41.py`: tooltips, drag to the view (free), to Settings (right stack pushed by Settings), reload, double-click back without collapsing, delayed click, save, original layout, load, refused file, free window kept on screen. `tests/v35.py` and `tests/v36.py` now wait 300 ms after a mouse click on a title.

## 26. New in v42 (24/10/2026)

### 26.1 Light rendering

Without a graphics card (software rendering, for example "Microsoft Basic Render Driver" in Edge), or on a very large region, every frame is expensive and the page responds slowly. **Light rendering** makes the image lighter: fewer pixels computed, fewer frames per second and, in global view, the overview only.

In **Settings**, the **"Light rendering"** box sits below **"High resolution"**. Checking it applies the recommended values; unchecking it restores the page's normal values. The choice is remembered by this browser, for this region.

### 26.2 Fine settings

The **"Fine settings…"** button, next to the box, opens a small window to the left of Settings; it hides when Settings closes. Each setting applies at once, whether the box is checked or not:

| Setting                     | Normal                              | Recommended | Effect                                                          |
| --------------------------- | ----------------------------------- | ----------- | --------------------------------------------------------------- |
| Render resolution           | 100%                                | 50%         | fewer pixels computed; the browser enlarges the image, blurrier |
| Frames per second (at most) | no limit                            | 15          | leaves the browser time between two frames (windows, keyboard)  |
| Global view: overview only  | no                                  | yes         | outside walk mode, no detailed tile is loaded                   |
| Detailed tile radius        | the page's (`--tile-radius`, 150 m) | 80 m        | fewer tiles around the avatar                                   |
| Antialiasing                | yes                                 | no          | smoothed edges; applied on the next page load                   |

The two tile settings only appear on a region split into tiles. **"Recommended values"** restores the five values of the "Recommended" column. **"Default values"**, at the bottom of Settings, also returns light rendering to the page's values. The recommended values are an estimate: they have not been measured on Edge in software rendering.

With the overview only, detailed tiles load when entering walk mode and go away when leaving it. Zones linked to an object of a tile are therefore only visible in walk mode.

### 26.3 Automatic offer

When the page sees rendering without a graphics card ("Basic Render Driver", "SwiftShader", "llvmpipe"), a message at the bottom of the screen, above the buttons, offers to turn on light rendering: **Yes** applies the recommended values, **No** keeps normal rendering. The question is asked only once; you change your mind in Settings.

### 26.4 `--light` option

`glb2html.py --light`: the page opens in light rendering until the visitor chooses otherwise; `--no-light` returns to normal rendering (default). The option is carried over by `--update`. In the viewer, the "Exported page opens in light rendering (--light)" box does the same for exported pages; three lines of the rendering section (resolution, frames per second, overview only) set the viewer itself.

### 26.5 Narrower Settings window

Settings is at most 420 px wide: long labels wrap, and the window scrolls if it is taller than the screen. The note about the avatar color fits on two lines. **Window layout** becomes a real section (bold title, line above, three buttons in a row), and the note "While walking, Esc releases the mouse…" is now at the very bottom of the window.

### 26.6 Diagnostics

"Copy diagnostics" adds two lines: the current light rendering settings, and the number of frames rendered per second over the last 5 seconds, with what forces continuous rendering (animated sea, other visitors, walk mode, tiles loading; "nothing" when the page only redraws on demand).

### 26.7 v42 tests

`tests/v42.py`: offer in software rendering, Yes, choice remembered, antialiasing off at load, box and sub-window, live settings, recommended values, frames per second cap, diagnostics, default values, `--light` page, `--update`, overview only on a region split into tiles (unloading, walk mode, return), live radius, viewer lines, color note on two lines, Settings width, Layout section, note at the bottom.

## 27. JSON file reference (v43)

This section describes **every JSON file of the project, field by field**, the way `opensim.sample.ini` and `robust.sample.ini` do for OpenSim.

A JSON file does not accept comments. The explanations are therefore here, and the samples are separate, in the `docs/samples/` folder: they are **real, complete and valid files**. To use one, copy the sample, rename it and change the values. The `tests/samples.py` test checks that each sample is accepted by the real code that reads that file: the page, the viewer, the tools and the presence server. The samples therefore stay correct when the code changes.

### 27.1 The files and their samples

| Real file                                        | Sample in `docs/samples/`          | Written by                                  | Read by                                             |
| ------------------------------------------------ | ---------------------------------- | ------------------------------------------- | --------------------------------------------------- |
| `NOM.config.json`                                | `region.config.sample.json`        | `glb2html.py`                               | the page                                            |
| `NOM.zones.json`                                 | `region.zones.sample.json`         | the viewer, `glb2html.py --zones`, by hand  | the page, the viewer, `glb2html.py --zones`         |
| `default.json`                                   | `default.sample.json`              | `glb2html.py --default`                     | the shell                                           |
| `regions.json`                                   | `regions.sample.json`              | `glb2html.py --register`, the viewer        | the page (`mapUrl`), the shell, `glb2html.py --map` |
| `NOM.tiles.json`                                 | `region.tiles.sample.json`         | `glb2tiles.py`                              | the page, the viewer, `glb2html.py --tiles`         |
| `NOM.reglages.json`                              | `region.reglages.sample.json`      | the viewer ("Save to a file")               | the viewer, `glb2html.py --settings`                |
| `disposition.json`                               | `disposition.sample.json`          | the page (Settings, "Save")                 | the page (Settings, "Load")                         |
| `presence_identities.json`                       | `presence_identities.sample.json`  | `presence_server.py`                        | `presence_server.py`                                |
| `presence_bans.json`                             | `presence_bans.sample.json`        | `presence_server.py` (`bannir` command)     | `presence_server.py`                                |
| `--history-file` file (for example `chat.jsonl`) | `chat_history.sample.jsonl`        | `presence_server.py`                        | `presence_server.py`                                |
| `--visits` file (for example `visits.jsonl`)     | `visits.sample.jsonl`              | `presence_server.py`                        | `presence_server.py`                                |
| `presence_visits_keys.json`                      | `presence_visits_keys.sample.json` | `presence_server.py` (`visits-key` command) | `presence_server.py`                                |
| `presence_creators.json`                         | `presence_creators.sample.json`    | by hand (§ 34)                              | `presence_server.py` (`--creators`)                 |

Two other files have **exactly the format** of `NOM.zones.json`:

- `zones.json`, the zones shared by the regions of a folder, read when a region has no `NOM.zones.json` of its own (§ 16);
- `NOM.zones.bak.json`, the backup copy the viewer leaves when it saves the zones in the region's folder.

In the samples, the region is called `Region`. For a region "Ankh", rename `region.config.sample.json` to `Ankh.config.json` and replace `Region` with `Ankh` in the values that contain it (`room`, `tiles`, the addresses). The addresses in the samples are written `ADRESSE`: put your own there.

### 27.2 How to read the tables

- **Text**: a value in quotes, for example `"door, porte"`.
- **Number**: without quotes, with a dot for decimals, for example `18.5`.
- **Yes / no**: `true` (yes) or `false` (no), without quotes.
- **List**: values in square brackets, for example `[392, 68, -373]` for an x, y, z position.
- **Object**: fields in curly braces, like a card within the card.
- **Color**: a whole number, which is the usual color code written in base 10. The sea blue `#3A9AD9` is written `3840729`. To convert in PowerShell, typing `0x3A9AD9` gives `3840729`, and `'{0:X6}' -f 3840729` gives back `3A9AD9`. The `--sea-color` and `--sky-color` options accept the code `3a9ad9` directly.
- **Option**: the `glb2html.py` option that writes this field. A dash "—" means that no option sets it.

Positions are in meters, in the page's frame: x towards the east, y upwards, z towards the south (north is the -z direction). Angles (`yaw`) are in radians: 1.57 is a quarter turn, 3.14 a half turn.

### 27.3 `NOM.config.json`: the page settings

`glb2html.py` writes it; the page reads it again at each opening, so **F5 is enough** after a change. The preferred way to change it is `glb2html.py --update -o NOM.html --shared-shell` followed by the wanted options: only the fields of the given options change, the rest is kept, including a field added by hand. It can also be edited by hand; a syntax error (forgotten comma, missing quote) then prevents the page from opening.

**Sea and sky**

| Field            | Type         | Default   | What it does                                                                                       | Option                 |
| ---------------- | ------------ | --------- | -------------------------------------------------------------------------------------------------- | ---------------------- |
| `sea`            | yes / no     | `true`    | shows the sea                                                                                      | `--sea`, `--no-sea`    |
| `seaY`           | number       | `-50`     | height of the sea in meters (from -150 to 60)                                                      | `--sea-y`              |
| `seaColor`       | color        | `3840729` | color of the sea (`#3A9AD9`)                                                                       | `--sea-color`          |
| `skyColor`       | color        | `8900331` | color of the sky and of the fog (`#87CEEB`)                                                        | `--sky-color`          |
| `anim`           | yes / no     | `false`   | animated waves; otherwise the sea is still                                                         | `--anim`, `--no-anim`  |
| `wave`           | number       | `0.5`     | height of the waves (from 0 to 10)                                                                 | `--wave`               |
| `seaSegments`    | whole number | `400`     | fineness of the sea surface (from 8 to 1000); only matters with animated waves                     | `--sea-segments`       |
| `seaSize`        | number       | `4000`    | width of the sea in meters                                                                         | —                      |
| `hole`           | number       | `180`     | radius in meters of the **calm area** around the island, where the waves fade out (from 30 to 600) | `--hole`               |
| `holeFade`       | number       | `60`      | width of the transition between the calm area and the waves                                        | `--hole-fade`          |
| `holeX`, `holeZ` | number       | `0`       | center of the calm area                                                                            | `--hole-x`, `--hole-z` |

**Region and starting camera**

| Field            | Type              | Default        | What it does                                                                                                 | Option                      |
| ---------------- | ----------------- | -------------- | ------------------------------------------------------------------------------------------------------------ | --------------------------- |
| `rotate`         | whole number      | `0`            | rotation of the region: 0, 90, 180 or 270 degrees                                                            | `--rotate`                  |
| `target`         | list of 3 numbers | `[0, 15, 0]`   | point the camera looks at on opening                                                                         | `--target`                  |
| `targetExplicit` | yes / no          | `false`        | `true` when `--target` was given: the page keeps this framing instead of starting from the `default` arrival | `--target`                  |
| `camDir`         | list of 3 numbers | `[0, 0.25, 1]` | direction the camera looks from                                                                              | `--cam-dir`                 |
| `zoom`           | number            | `1`            | camera distance (1 = automatic framing, 2 = twice as far)                                                    | `--zoom`                    |
| `compass`        | yes / no          | `true`         | compass at the top of the page                                                                               | `--compass`, `--no-compass` |
| `northDeg`       | number            | `0`            | compass offset in degrees, for a model that does not come from OpenSim                                       | `--north`                   |

**Display**

| Field           | Type     | Default             | What it does                                                                                                                                | Option                    |
| --------------- | -------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| `retina`        | yes / no | `false`             | high resolution (sharper, about four times heavier)                                                                                         | `--retina`, `--no-retina` |
| `light`         | yes / no | `false`             | the page opens in light rendering as long as the visitor has chosen nothing (§ 26)                                                          | `--light`, `--no-light`   |
| `foliageCutout` | number   | `0.12`              | transparency threshold of foliage (from 0 to 0.5): higher, the leaf edges are cut more                                                      | `--foliage-cutout`        |
| `names`         | yes / no | `false`             | shows the name of the clicked element                                                                                                       | `--names`, `--no-names`   |
| `panel`         | yes / no | `true`              | Settings button for visitors                                                                                                                | `--panel`, `--no-panel`   |
| `libUrl`        | text     | `""`                | folder or address of `lib` (three.js) when it is not next to the page; `--update` aligns it with the `const LIB` line of the shell (§ 28.5) | `--lib-url`               |
| `version`       | text     | version of the tool | version of `glb2html.py` that wrote the file; `--update` replaces it                                                                        | —                         |

**Walk mode**

| Field        | Type     | Default         | What it does                                                                                                                           | Option                |
| ------------ | -------- | --------------- | -------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| `walk`       | yes / no | `true`          | walk mode (F key)                                                                                                                      | `--walk`, `--no-walk` |
| `fly`        | yes / no | `true`          | flight in walk mode                                                                                                                    | `--fly`, `--no-fly`   |
| `eyeHeight`  | number   | `1.7`           | eye height in meters                                                                                                                   | `--eye-height`        |
| `walkSpeed`  | number   | `3.5`           | walking speed in meters per second (running: 2.2 times more)                                                                           | `--walk-speed`        |
| `walkIgnore` | text     | `"door, porte"` | objects you walk through, separated by commas: `door` = any name starting with this word, `=mesh_346_5` = this exact name, `""` = none | `--walk-ignore`       |

**Visitors and chat**

| Field         | Type     | Default                           | What it does                                                                                       | Option                        |
| ------------- | -------- | --------------------------------- | -------------------------------------------------------------------------------------------------- | ----------------------------- |
| `presenceUrl` | text     | `""`                              | address of the presence server (`ws://...` or `wss://...`); empty = alone, without avatars or chat | `--presence-url`              |
| `room`        | text     | name of the page                  | presence room: visitors of the same room see each other                                            | `--room`                      |
| `spectate`    | yes / no | `true` if `presenceUrl` is filled | see the walkers from the global view                                                               | `--spectate`, `--no-spectate` |
| `chat`        | yes / no | `true`                            | chat between visitors (a presence server is needed)                                                | `--chat`, `--no-chat`         |
| `chatFade`    | number   | `0`                               | seconds before messages and bubbles disappear; 0 = they stay                                       | `--chat-fade`                 |

**Zones**

| Field          | Type     | Default    | What it does                                                                                                     | Option                              |
| -------------- | -------- | ---------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| `profile`      | text     | `"public"` | `"public"`: private zones are not shown; `"private"`: all zones are                                              | `--profile`                         |
| `zones`        | list     | `[]`       | always empty in this file: the zones are in `NOM.zones.json`                                                     | —                                   |
| `zonesLive`    | text     | `""`       | always empty in this file (used by standalone pages, `--zones-live`)                                             | `--zones-live`                      |
| `zoneMarker`   | text     | `"dot"`    | marker of portals and free zones: `"dot"` small disc, `"range"` ring at the zone's real radius, `"none"` nothing | `--zone-marker`                     |
| `zoneCone`     | yes / no | `true`     | small cone above the portals (T key)                                                                             | `--zone-cone`, `--no-zone-cone`     |
| `showSpawns`   | yes / no | `false`    | also draws the arrivals                                                                                          | `--show-spawns`, `--no-show-spawns` |
| `zoneInfoDist` | number   | `150`      | distance in meters (from 5 to 500) up to which zones react to hovering and clicking in walk mode                 | `--zone-info-dist`                  |

**World map**

| Field    | Type | Default | What it does                                                                  | Option                |
| -------- | ---- | ------- | ----------------------------------------------------------------------------- | --------------------- |
| `map`    | list | `[]`    | map embedded in the page: same cards as `regions.json` (§ 27.6)               | `--map`, `--register` |
| `mapUrl` | text | `""`    | address(es) of `regions.json` read again at each opening, separated by commas | `--map-url`           |

**Tiled region**: these six fields only exist for a region split by `glb2tiles.py`. For a region made of a single `.glb` file, **remove** them from the sample, otherwise the page looks for tiles.

| Field              | Type         | Default   | What it does                                                     | Option                 |
| ------------------ | ------------ | --------- | ---------------------------------------------------------------- | ---------------------- |
| `tiles`            | text         | —         | name of the tile index, for example `"Region.tiles.json"`        | `--tiles`              |
| `tileRadius`       | number       | `150`     | radius in meters around the avatar within which tiles are loaded | `--tile-radius`        |
| `tileMargin`       | number       | `60`      | margin in meters beyond that radius before a tile is removed     | `--tile-margin`        |
| `tileMaxMB`        | number       | `200`     | megabytes of tiles loaded at the same time, at most              | `--tile-max-mb`        |
| `tileMaxTriangles` | whole number | `8000000` | triangles of tiles loaded at the same time, at most              | `--tile-max-triangles` |
| `tileConcurrency`  | whole number | `4`       | tile downloads at the same time                                  | `--tile-concurrency`   |

The light rendering settings chosen by a visitor (resolution, frames per second, overview only, antialiasing) are kept **by their browser**, not in this file: the page ignores `pixelScale`, `fpsMax`, `ovOnly` or `antialias` written here.

### 27.4 `NOM.zones.json`: the zones

A **list** of zones, read again at each opening of the page. Each zone has the fields below; a missing field takes its default value, and a value outside the limits is brought back within them.

There are **four kinds** of zones (`type` field): `"spawn"` (arrival), `"portal"` (portal), `"url"` (web link) and `"ha"` (command). "Private", "linked to an object" and "name shown" are not kinds: they are boxes (`private`, `mesh`, `showName`) valid for all kinds.

| Field         | Type     | Default       | What it does                                                                                                                                                  |
| ------------- | -------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`          | text     | `z1`, `z2`... | short, unique name: lowercase letters, digits, `-` and `_`, 40 characters at most. The `default` arrival is the region's entry point                          |
| `type`        | text     | `"portal"`    | `"spawn"`, `"portal"`, `"url"` or `"ha"`                                                                                                                      |
| `label`       | text     | `""`          | name shown (tooltip, sign), 60 characters at most                                                                                                             |
| `x`, `y`, `z` | number   | `0`           | position in meters                                                                                                                                            |
| `yaw`         | number   | `0`           | orientation in radians: direction of the gaze on arrival, or front of the sign                                                                                |
| `shape`       | text     | `"ring"`      | `"ring"` (ring on the ground) or `"board"` (sign on a post)                                                                                                   |
| `trigger`     | text     | `"click"`     | portals only: `"click"` (click or E), `"enter"` (walking into it) or `"both"` (both). The other kinds are always `"click"`                                    |
| `radius`      | number   | `2`           | radius of the zone in meters (from 0.5 to 50)                                                                                                                 |
| `w`, `h`      | number   | `2.4`, `1.2`  | width and height of the sign in meters                                                                                                                        |
| `target`      | text     | `""`          | portal: address of the destination region, or empty for a point of the same region; link: address of the web page; command: address called                    |
| `spawn`       | text     | `""`          | portal: `id` of the targeted arrival (empty = `default`)                                                                                                      |
| `confirm`     | yes / no | `false`       | asks for a confirmation before acting                                                                                                                         |
| `private`     | yes / no | `false`       | private zone: absent from public pages (`public` profile)                                                                                                     |
| `showName`    | yes / no | `false`       | writes the `label` above the zone in walk mode                                                                                                                |
| `mesh`        | text     | `""`          | zone **linked to an object** of the model: its name, or `name#number` when several objects have that name; the object becomes clickable. Never for an arrival |

The sample contains eight zones, one for each case:

| `id`              | Kind    | What it shows                                                                                 |
| ----------------- | ------- | --------------------------------------------------------------------------------------------- |
| `default`         | arrival | entry point of the region                                                                     |
| `gallery`         | arrival | second arrival, targeted by a portal                                                          |
| `to-gallery`      | portal  | to another point of the same region (empty `target`, `spawn` = `gallery`), by walking into it |
| `to-other-region` | portal  | to another region, sign, click or walk, with confirmation                                     |
| `website`         | link    | opens a web page, sign                                                                        |
| `light-on`        | command | call to an address (for example a Home Assistant webhook), private, with confirmation         |
| `door-info`       | link    | linked to the model's `Door#2` object                                                         |
| `back-home`       | portal  | name shown above the zone (`showName`)                                                        |

In a tiled region, a linked zone finds its object thanks to the `extras.ref` tag that `glb2tiles.py` writes in the objects of the tiles. This tag is in the tiles' `.glb` files, **not** in `NOM.zones.json`.

### 27.5 `default.json`: the default region

| Field    | Type | Default | What it does                                            | Option      |
| -------- | ---- | ------- | ------------------------------------------------------- | ----------- |
| `region` | text | —       | region opened when the address has no `?region=` (§ 16) | `--default` |

### 27.6 `regions.json`: the world map

A **list** of regions (plain form), or, since v47, an **object** with a header: `{"showUrl": false, "regions": [ ... ]}`. Both forms are read everywhere (`carte.html` map, standalone map, map opened with M, shell). A card without `name` or without `url` is ignored.

| Header field | Type    | Default | What it does                                                                                                                                                 | Option |
| ------------ | ------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------ |
| `showUrl`    | boolean | `false` | shows the address under each tile of the map page; the checkbox on the map page, once ticked or unticked by the visitor, wins (choice kept by their browser) | —      |
| `regions`    | list    | —       | the region cards (next table)                                                                                                                                | —      |

`--register` and `--scan-sites` keep the header and the shape of the file (list or object). So does the viewer since v50: "Import regions.json" accepts both shapes, "Export regions.json" gives back the imported shape with its header, and every card keeps all its fields (§ 33).

| Field      | Type         | Default             | What it does                                                                           | Option           |
| ---------- | ------------ | ------------------- | -------------------------------------------------------------------------------------- | ---------------- |
| `id`       | text         | taken from the name | short identifier, unique in the map                                                    | —                |
| `name`     | text         | —                   | name shown, 60 characters at most                                                      | `--region-name`  |
| `url`      | text         | —                   | address of the page: complete (`https://...`) or relative (`index.html?region=Region`) | `--region-url`   |
| `x`, `y`   | whole number | `0`                 | place on the grid, as in OpenSim (x towards the east, y towards the north)             | `--region-xy`    |
| `spawn`    | text         | `""`                | arrival used when coming from the map (empty = `default`)                              | `--region-spawn` |
| `presence` | text         | `""`                | presence server of this region, if it is not the page's (to count the visitors)        | —                |
| `room`     | text         | `""`                | presence room of this region                                                           | `--room`         |
| `thumb`    | text         | `""`                | thumbnail: embedded image (`data:image/...`) or address of an image                    | `--thumb`        |

### 27.7 `NOM.tiles.json`: the tile index

`glb2tiles.py` writes it; it is **not edited by hand**. The page only reads a few fields: `tiles` (for each tile `file`, `min`, `max`, `bytes`, `triangles`), `nodeRefs` and `overview.file`. The others are for the report.

| Field            | Type          | What it contains                                                                                                                                                                                                                                                                          |
| ---------------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `version`        | whole number  | format version (1)                                                                                                                                                                                                                                                                        |
| `generator`      | text          | tool and version that wrote the file                                                                                                                                                                                                                                                      |
| `source`         | text          | name of the split `.glb`                                                                                                                                                                                                                                                                  |
| `extent`         | object        | box of the whole region: `min` and `max`, each x, y, z                                                                                                                                                                                                                                    |
| `params`         | object        | splitting settings: `budgetMB`, `budgetTriangles`, `minCell`, `wholeWeightMB`, `wholeExtent`, `thresholdMB`, `thresholdTriangles`, `outlier` (options `--budget`, `--budget-triangles`, `--min`, `--whole-weight`, `--whole-extent`, `--threshold`, `--threshold-triangles`, `--outlier`) |
| `warnings`       | list of texts | warnings of the splitting                                                                                                                                                                                                                                                                 |
| `roots`          | object        | objects kept whole (`whole`) and spread (`split`)                                                                                                                                                                                                                                         |
| `duplication`    | number        | geometry of all tiles divided by that of the model (1 = nothing duplicated)                                                                                                                                                                                                               |
| `nodeRefs`       | number        | 1 if the objects carry `extras.ref` (linked zones possible), 0 with `--no-refs`                                                                                                                                                                                                           |
| `replacedImages` | object        | unreadable images replaced by grey: `distinct`, `occurrences`, `grey`                                                                                                                                                                                                                     |
| `tiles`          | list          | one card per tile (below)                                                                                                                                                                                                                                                                 |
| `excluded`       | object        | only with `--exclude`: patterns, limits, number of removed objects, triangles and bytes saved, most frequent names                                                                                                                                                                        |
| `overview`       | object        | only with the overview: `file` (the `.glb`), weight, triangles, objects kept and omitted, duration, `params` (`budgetMB`, `budgetTriangles`, `minExtent`, `maxExtent`, `resolution`, `terrainStep`)                                                                                       |

Each card of `tiles`:

| Field                         | Type              | What it contains                                 |
| ----------------------------- | ----------------- | ------------------------------------------------ |
| `file`                        | text              | path of the tile's `.glb`, relative to the index |
| `level`, `i`, `j`             | whole number      | level and place of the tile in the grid          |
| `min`, `max`                  | list of 3 numbers | box of the tile                                  |
| `instances`                   | whole number      | number of objects in the tile                    |
| `triangles`                   | whole number      | triangles of the tile                            |
| `bytes`                       | whole number      | weight of the file                               |
| `geometryBytes`, `imageBytes` | whole number      | of which geometry, of which images               |
| `replacedImages`              | whole number      | images replaced by grey in this tile             |

### 27.8 `NOM.reglages.json`: the viewer's working state

Written by the viewer's "Save to a file" button, read by "Load a file" and by `glb2html.py --settings`. Unlike `NOM.config.json`, it is **nested** (§ 16).

| Field            | Type         | What it contains                                                                                                              |
| ---------------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `v`              | whole number | format version: always `1`                                                                                                    |
| `file`           | text         | name of the `.glb` open in the viewer                                                                                         |
| `saved`          | text         | date and time of the save                                                                                                     |
| `cfg`            | object       | the settings: same names and same meaning as in `NOM.config.json` (§ 27.3), plus five settings specific to the viewer (below) |
| `zones`          | list         | all the zones, private ones included (format of § 27.4)                                                                       |
| `camera`         | object       | `camDir`, `target`, `zoom`: the framing chosen in the viewer                                                                  |
| `profile`        | text         | `"public"` or `"private"` ("Export profile" menu)                                                                             |
| `thisReg`        | object       | card of this region for the map: `name`, `url`, `x`, `y`, `spawn`, `thumb` (§ 27.6)                                           |
| `cmd`            | object       | fields of the command summary: `script`, `glb`, `dest`, `mapPage`                                                             |
| `targetExplicit` | yes / no     | the camera target was moved by hand                                                                                           |

The five `cfg` settings specific to the viewer: `pixelScale`, `fpsMax` and `ovOnly` (light rendering, tried in the viewer), `guide` (guide of the calm area shown in the viewer) and `ignoreViz` (objects walked through shown as wireframe). `--settings` does not take them.

### 27.9 `disposition.json`: where the windows are

Written by Settings, "Save" ("Window layout" section), read by "Load" (§ 25).

| Field    | Type         | What it contains                                                                                                                                                                                                                                                                                      |
| -------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app`    | text         | always `"web3d-layout"`: another file is refused                                                                                                                                                                                                                                                      |
| `v`      | whole number | format version: `1`                                                                                                                                                                                                                                                                                   |
| `layout` | object       | `wins`: for each window (`H` help, `I` information / status, `L` arrivals), `pile` (`"L"` left stack, `"R"` right stack, `"F"` free), `home` (`"L"` or `"R"`, the stack the window returns to on double-click), and for a free window `x`, `y` in pixels; `order`: order of the windows in each stack |
| `ls`     | object       | state of the windows: `glb2html_help`, `glb2html_state`, `glb2html_spawn` (`"1"` shown, `"0"` hidden), `glb2html_helpFold`, `glb2html_stateFold`, `glb2html_spawnFold` (`"1"` collapsed), `glb2html_helpW`, `glb2html_stateW`, `glb2html_spawnW` (width in pixels)                                    |

### 27.10 Presence server files

The server writes them itself; edit them by hand only with the server stopped. "Hashed" values are fingerprints: the original key or IP address cannot be recovered, which protects the visitors. The fingerprints in the samples are made up and match nobody.

**`presence_identities.json`** (`--identities` option): the reserved nicknames.

| Field   | Type   | What it contains                                                                                                                                                                                               |
| ------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `salt`  | text   | secret "salt" drawn at random on the first start, mixed into the keys before hashing them. Changing it frees all the nicknames                                                                                 |
| `names` | object | for each simplified nickname (lowercase, without accents or spaces), the fingerprint of the browser key that owns it                                                                                           |
| `users` | object | for each fingerprint: `name` (nickname as written), `key` (simplified nickname), `first` and `last` (first and last visit, in seconds since 1970). A nickname unused for `--name-ttl-days` days (365) is freed |

**`presence_bans.json`** (`--bans` option): a list of bans.

| Field    | Type   | What it contains                                                                                                 |
| -------- | ------ | ---------------------------------------------------------------------------------------------------------------- |
| `key`    | text   | fingerprint of the banned browser's key (empty for a visitor without a key)                                      |
| `ip`     | text   | fingerprint of their IP address                                                                                  |
| `until`  | number | end of the ban in seconds since 1970; `0` = permanent. A finished ban is removed from the file at the next check |
| `name`   | text   | nickname at the time of the ban                                                                                  |
| `reason` | text   | reason given                                                                                                     |
| `added`  | number | date of the ban in seconds since 1970                                                                            |

**Chat history** (`--history-file` option): this is not a single-block JSON file, but **one message per line**, each line being a small JSON. Never an IP address.

| Field  | Type         | What it contains                                                      |
| ------ | ------------ | --------------------------------------------------------------------- |
| `n`    | whole number | number of the message                                                 |
| `t`    | whole number | time in seconds since 1970 (this is what counts for `--history-days`) |
| `d`    | text         | the same time in readable form (dd/mm/yyyy hh:mm:ss)                  |
| `room` | text         | room                                                                  |
| `name` | text         | nickname                                                              |
| `text` | text         | message                                                               |

Messages older than `--history-days` days (30 by default) are removed at startup; with `--history-days 0`, nothing is removed.

**Visit log** (`--visits` option, v48): like the history, **one visit per line**, each line being a small JSON. Never an IP address.

| Field   | Type         | What it contains                                                                                                                                  |
| ------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `room`  | text         | room                                                                                                                                              |
| `start` | whole number | arrival in seconds since 1970 (this is what counts for `--visits-days`)                                                                           |
| `dur`   | whole number | duration of the connection in seconds                                                                                                             |
| `walk`  | whole number | seconds spent walking                                                                                                                             |
| `v`     | text         | browser fingerprint (10 characters), different from the key in the `presence.log` log: used to count distinct visitors and to merge reconnections |
| `name`  | text         | walker's nickname, only with `--visits-names`                                                                                                     |

Visits older than `--visits-days` days (365 by default) are removed at startup and then every 6 hours, together with unreadable lines; with `--visits-days 0`, nothing is removed.

**`presence_visits_keys.json`** (`--visits-keys` option, v48): the visit log keys, written by the `visits-key` command.

| Field   | Type   | What it contains                                                                                                                                                                                                      |
| ------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `rooms` | object | for each room: `salt` (random salt), `hash` (SHA-256 fingerprint of the salt followed by the key in upper case, without dashes or spaces), `added` (creation, in seconds since 1970). The key itself is never written |

**`presence_creators.json`** (`--creators` option, v51): the hosted creators, written by hand and re-read without restarting the server (§ 34). An object `{"creators": [...]}`; for each creator:

| Field        | Type          | What it contains                                                                                                                                   |
| ------------ | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`         | text          | unique identifier: letters, digits, `-` and `_`, 32 at most                                                                                        |
| `prefix`     | text          | prefix of their rooms, without a dot; absent = `id`; `""` = the host, who keeps every room that belongs to no creator (a single entry)             |
| `origins`    | list of texts | origins of their pages (`https://alice.example`, `null` for a page opened from the disk and for the viewer, written in quotes; without quotes it is ignored with a warning); an origin belongs to one creator only |
| `maxWalkers` | integer       | walkers at most over all their rooms; `0` or absent = only the general limits                                                                      |
| `maxRooms`   | integer       | rooms open at the same time at most; `0` or absent = no limit of their own                                                                         |
| `off`        | boolean       | `true`: suspended, their new connections are refused                                                                                               |
| `note`       | text          | free note of the host, ignored by the server                                                                                                       |

### 27.11 English names since v43

So that all names are in the same language, v43 put the last French names into English: tool options, values in the JSON files and address parameters. **The old names are still accepted**: commands, files and links already written keep working. An old name is replaced by the new one when read; when a tool rewrites a file, it writes the new one. `--update` keeps a field you do not change as it is: an old `tileMaxMo` therefore stays in `NOM.config.json`, and the page still reads it.

| Where                                  | Old name                                                           | New name                                                       |
| -------------------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------- |
| `glb2html.py`                          | `--maj`                                                            | `--update`                                                     |
| `glb2html.py`                          | `--tile-max-mo`, `--tile-max-tri`                                  | `--tile-max-mb`, `--tile-max-triangles`                        |
| `glb2html.py`                          | `--zone-marker discret`, `portee`, `aucun`                         | `--zone-marker dot`, `range`, `none`                           |
| `glb2html.py`                          | `--profile perso`                                                  | `--profile private`                                            |
| `glb2tiles.py`                         | `--budget-tri`, `--ov-budget-tri`                                  | `--budget-triangles`, `--ov-budget-triangles`                  |
| `glb2tiles.py`                         | `--entier-poids`, `--entier-etendue`                               | `--whole-weight`, `--whole-extent`                             |
| `glb2tiles.py`                         | `--seuil`, `--seuil-tri`, `--aberrant`                             | `--threshold`, `--threshold-triangles`, `--outlier`            |
| `glb2tiles.py`                         | `--exclure`, `--exclure-max-tri`, `--exclure-max-meshes`           | `--exclude`, `--exclude-max-triangles`, `--exclude-max-meshes` |
| `glb2tiles.py`                         | `--sans-references`, `--sans-vue-ensemble`, `--vue-ensemble-seule` | `--no-refs`, `--no-overview`, `--overview-only`                |
| `glb2tiles.py`                         | `--ov-seuil`, `--ov-seuil-max`, `--ov-terrain-pas`                 | `--ov-threshold`, `--ov-threshold-max`, `--ov-terrain-step`    |
| `glb2tiles.py`                         | `--bloc`, `--forcer`, `--sortie`                                   | `--block`, `--force`, `--output`                               |
| `oar2glb.py`                           | `--reperes`, `--terrain-seul`, `--sortie`                          | `--markers`, `--terrain-only`, `--output`                      |
| `oar2glb.py`                           | `--terrain oui`, `--terrain non`                                   | `--terrain yes`, `--terrain no`                                |
| `glb-stats.py`                         | `--bloc`, `--sortie`                                               | `--block`, `--output`                                          |
| `gen_reference.py` (v44)               | `--outils`, `--sortie`, `--verifier`                               | `--tools`, `--output`, `--check`                               |
| `verif_trad.py` (v44)                  | `--glossaire`                                                      | `--glossary`                                                   |
| `NOM.config.json`                      | `tileMaxMo`, `tileMaxTri`                                          | `tileMaxMB`, `tileMaxTriangles`                                |
| `NOM.config.json`, `NOM.reglages.json` | `zoneMarker`: `discret`, `portee`, `aucun`                         | `dot`, `range`, `none`                                         |
| `NOM.config.json`, `NOM.reglages.json` | `profile`: `perso`                                                 | `private`                                                      |
| `NOM.tiles.json`                       | `budgetMo`, `wholeWeightMo`, `thresholdMo`                         | `budgetMB`, `wholeWeightMB`, `thresholdMB`                     |
| address of the page                    | `?rayon=`                                                          | `?radius=`                                                     |
| address of the viewer                  | `?tuiles=`                                                         | `?tiles=`                                                      |

The two development tools (`gen_reference.py`, `verif_trad.py`) followed in v44, and the `--update` messages start with `[update]`. Unchanged: `--analyse` (also British English) and the values that are object names, such as `door, porte`. In the tools' help, the example names of the values are also in English (`FILE`, `PATH`, `NAME`, `DEGREES`, `SHELL.html`). The history (`CHANGELOG.md`, `HISTORY.md`) keeps the names of the time.

## 28. New in v45 (24/10/2026)

### 28.1 The page says why presence was cut

When the connection to the presence server closes, the presence line (Information / Status window, viewer panel) no longer always says "server unreachable": it gives what the browser knows.

- **the connection never opened**: "connection never established (check address, port or firewall)";
- **the connection had opened, then the server or the network cut it**: "connection opened then closed (code N)", followed by the reason sent by the server when it gives one;
- **the browser refused to create the connection** (https page with a `ws://` address, or forbidden port): "refused by the browser".

Limit: the browser never gives the cause of a connection that does not open (code 1006, no reason). The page therefore cannot tell an unknown name, a closed port, a firewall or a browser block apart; only a server that cuts an already open connection supplies a code and a reason.

### 28.2 Diagnostics

"Copy diagnostics" adds the "Presence connection" line: whether the connection opened (yes or no), last closing code and last reason. Addresses stay replaced by `ADRESSE`.

### 28.3 Presence test

`tests/v45.py`: absent server, server that closes with a code and a reason, constructor refused by the browser, English, viewer.

### 28.4 One line for the `lib` folder

The shell (the `index.html` file shared by all the regions of a folder) starts with a `const LIB = './lib';` line: it is **the only line to edit** to put the `lib` folder elsewhere (for example `'../lib'`, or an `https://…/lib` address). The three.js import map and the path of the Draco decoders are built from that line by a small script run before any module. Accepted values: the same as `--lib-url` (§ 22.8); a refused value is ignored.

### 28.5 `--update` keeps the line

Priority of the `lib` folder: the `--lib-url` option if given; the `const LIB` line of an existing shell if it is not `./lib`; the `libUrl` key of `NOM.config.json`; otherwise `./lib`. When the shell's line wins, `--update` says so in its report and aligns `libUrl`. A shell saved with Windows line endings (CRLF) is recognised as identical. A new region created in a folder whose shell was edited by hand keeps the same `lib` folder, without any warning.

### 28.6 `dist\index.html`

`python build.py` now puts the ready-made shell in `dist\index.html` (`lib` folder: `./lib`), byte for byte the same as the one `glb2html.py` writes. It can be copied into a folder of regions instead of running `--update`; if the `lib` folder is elsewhere, the `const LIB` line has to be carried over. `--update` is still needed to update a region's configuration.

### 28.7 Browsers

Tried in Chromium (`tests/v45_lib.py`). **Not tried: Firefox and Safari.** The `tests/essai_importmap.html` file (open it in the browser; the result is written in plain words) checks that a browser accepts an import map built by a script; if the test fails in a browser, the shell does not start in it.

### 28.8 Shell test

`tests/v45_lib.py`: single line, no import map tag left in the shell, identical `dist\index.html`, unchanged standalone page, start-up in Chromium with `./lib` then with `../lib` (one line changed), `--update` keeping the line (message, aligned config, no dated copy), CRLF, refused value, `--lib-url` priority, new region, test page.

## 29. New in v46 (25/10/2026)

### 29.1 Status line

An always visible line gives, without opening the Information window: the **mode** in bold ("Walking" or "Overview"), then while walking the gait (on foot, flying, running), the view (first person, third person, free camera) and the `x y z` position; in the overview, the target. It sits at the bottom centre; on a screen narrower than 1361 px, and on a touch screen, it moves to the top, under the compass (and under the name box). No information in it is carried by a colour.

### 29.2 On-screen arrows

A pad of 3 x 3 buttons, above the status line, is clicked with the mouse or touched with a finger. **Press and hold = key held**: the movement lasts as long as the button is pressed.

While walking (the arrows reuse the keyboard keys: walking does not change):

| Row    | Left                            | Middle                                                       | Right                                    |
| ------ | ------------------------------- | ------------------------------------------------------------ | ---------------------------------------- |
| top    | turn left (←)                   | forward (Z or W, ↑)                                          | turn right (→)                           |
| middle | step left (Q or A)              | **Run**: one click turns it on, another turns it off (Shift) | step right (D)                           |
| bottom | up, while flying only (Page Up) | back (S, ↓)                                                  | down, while flying only (Page Down or C) |

In the overview:

| Row    | Left               | Middle                                  | Right               |
| ------ | ------------------ | --------------------------------------- | ------------------- |
| top    | turn the view left | move the view forward                   | turn the view right |
| middle | move the view left | **recenter the view** (opening framing) | move the view right |
| bottom | zoom out (−)       | move the view back                      | zoom in (+)         |

Moving and zooming do different things: **move** slides the camera and the target together, at constant height and distance (the landscape scrolls, tiles load around the new point); **zoom in / out** keeps the target and only changes the camera distance, like the wheel.

The middle of the pad replaces the "Recenter the view" button: that button only comes back in the bar when the arrows are hidden. While walking, a captured mouse (after a click in the view) cannot click the arrows: **Esc** frees it, **G** or the "Capture the mouse" button takes it back.

The zone prompt and the light rendering offer move up above the pad.

### 29.3 Hiding or showing the arrows

Three ways, which do the same thing and are remembered by the browser: the **K** key (same place on AZERTY and QWERTY), the "Arrows (K)" button of the bar ("Arrows (K): hidden" when they are; on a touch screen, the "Arrows" button of the column), and the "On-screen arrows (K)" checkbox in Settings. The arrows are shown by default.

### 29.4 Touch screen (phone, tablet)

The page switches to touch mode when the browser reports a touch screen as the main pointer ("Touch controls" setting: Auto; Yes forces touch mode, No refuses it, for example on a computer with a touch screen). In touch mode:

- the button bar is replaced by a **column of buttons** at the bottom right: "Walk" ("Exit" while walking), "Jump", "Fly" ("Land" while flying), "View", "Chat" (with the number of unread messages), "Arrows", "Menu"; the active button has a thick border;
- the **menu** offers: Help, Information, Arrivals, World map, Back to arrival (while walking), Recenter the view (when the arrows are hidden) and **Full screen** when the browser allows it (not on iPhone, where Safari only grants it to videos);
- the Help, Information and Arrivals windows are **folded on opening** (without changing the remembered setting) and have a **✕** button to close them;
- the arrows are large (56 px), at the bottom left;
- while walking, **dragging a finger** on the scene looks around: you pull the scenery (finger to the right, gaze to the left); a tooltip explains it on the first walk. In the overview, the gestures are the same as before (one finger: turn; two fingers: move and zoom);
- "Chat" opens a real input field (the phone keyboard opens) with "Send" and "✕ Close"; arrows and column hide while typing;
- landscape orientation is supported: the column switches to two or three columns;
- "Capture the mouse" does not exist (nothing to capture with a finger).

On a small phone screen, the page remains busy: windows and chat can be closed to clear the view.

### 29.5 Tooltips

Every button of the bar and every arrow has a tooltip: its role and its key (the letter follows the keyboard layout). On a touch screen, **a long press** (half a second) shows the tooltip; on a single-action button, the long press does not trigger the action.

### 29.6 Chat counter

The number in brackets in the tab title ("(3) Region") and on the "Chat" button counts the messages from other visitors received while the chat is closed or the tab hidden (the history replayed on arrival is not counted); it goes back to zero **when the chat is opened**, even without reading the messages (intended behaviour).

### 29.7 Diagnostics

"Copy diagnostics" adds the "Touch controls" line: touch mode yes or no, setting, touch screen detected, number of touch points.

### 29.8 One shell for a whole site

Recommended layout: at the root of the site, a single `index.html` shell, the `lib` folder, `regions.json` and `default.json`; one folder per region. Address of a region: `index.html?region=dossier/NOM`. To update a region **and** the root shell, give the shell path to `--shared-shell`:

`python glb2html.py --update -o "P:\site\dossier\NOM.html" --shared-shell "P:\site\index.html"`

With `--shared-shell` and no path, the shell and a `lib` folder are written **in the region folder**, where they are of no use with this layout. Another way after `python build.py`: copy `dist\index.html` over `index.html` (the `const LIB` line stays `./lib`). `--update` compares the shell with the one it contains itself: run the `glb2html.py` of `dist`, built last (an older copy elsewhere writes its older shell). A shell edited by hand is renewed, the old one kept under a dated name (`index.avant-AAAAMMJJ-HHMMSS.html`).

### 29.9 Tests of v46

`tests/v46.py` (Chromium, touch screen simulated with real touch events): status line, placement of the elements (nothing overlaps, at 1440 x 900, 390 x 844, 844 x 390 and 1180 x 820), arrows held with the mouse and the finger (forward, step, turn, up, overview), Run, K and "Arrows (K)" button, Recenter, tooltips, long press, menu, touch chat, ✕, settings, diagnostics, English.

### 29.10 Not tested

A real phone, a real tablet, iPhone and iPad, Edge, Windows, real full screen.

## 30. New in v47 (25/10/2026)

### 30.1 The map tile

Under the name, one line of text (never colour alone): "3 visitors · 1 walker" on one line (v52; in French "3 visiteurs" then "1 promeneur" on two lines), or "no visitors". Visitors count the walkers **and** the spectators (pages open in the overview); walkers are only shown when there are some. The line only appears if the card has a room (`room`) and a presence server (`presence`, or the page's own). The word "visit →" is gone: a **tooltip** on hover says what the click does ("Click to enter the region (arrival: default)"). The region you are in keeps "● you are here". A finger has no hover, so no tooltip. Same display on the map page and in the map opened with M.

### 30.2 Optional address

The address under each tile is **hidden by default**. It is shown if `showUrl` is `true` in the header of `regions.json` (§ 27.6), or if the visitor ticks the "Show addresses" checkbox at the top of the map page (next to the nickname). The visitor's choice is kept by their browser and wins over the file. An invalid address keeps its "(invalid address)" message.

### 30.3 `regions.json` with a header

Two forms, the plain list and the object `{"showUrl": ..., "regions": [...]}` (§ 27.6). `--register` reads and rewrites the file keeping the header and the shape. An older `glb2html.py` wipes a file that is not a list: do not use it on a file with a header.

### 30.4 Two ways to make the map

- **Standalone mode**: `--map-page` writes a page with the list of regions inside. It opens from disk and is regenerated when the list changes (except with `--map-url`, which makes it re-read `regions.json`). The header's `showUrl` is taken over.
- **Hosted mode**: `python build.py` writes `dist\carte.html`, one page identical for every site, **with no region inside**. It reads the `regions.json` next to it at every opening, like `index.html` reads the `NOM.config.json` files. Copy it once next to `index.html`: `Copy-Item "P:\site\web_3d\dist\carte.html" "P:\site\carte.html"`. Nothing to regenerate when `regions.json` changes. It needs a web server: opened from disk, it says so; without `regions.json`, it says "Cannot read regions.json".

The two modes live side by side.

### 30.5 Presence server

The reply to a `rooms` request adds `visitors` (walkers and spectators, per room) to `rooms` (walkers) and `spectators` (total). With an older server, the map only shows the walkers: restart the `presence_server.py` from `dist\` after `python build.py`.

### 30.6 v47 tests

`tests/v47.py` (Chromium, real presence server): `visitors` per room, universal `carte.html`, plain list and header, checkbox (start, kept choice, priority), English, `--register` keeping the header, older server, missing `regions.json`, opening from disk, map opened with M.

### 30.7 Not tested

A real phone (no tooltip with a finger), Edge, Windows, the PowerShell lines themselves.

## 31. New in v48 (25/10/2026): visit log

### 31.1 What it is for

The creator of a region (for example an artist showing their gallery) sees how many people visited it, when and for how long, even when they were not there. Visits are recorded by the presence server in a separate file; the creator reads them from their region's page, with a key. They only get a summary, never the file.

### 31.2 Host side: the presence server

1. Run the server with `--visits visits.jsonl` (a relative path means the script's folder, like `--log`). `--visits-days N` sets how long visits are kept (365 days by default; `0` = keep everything). `--visits-names` also records walkers' nicknames (off by default):
   `python ".\presence_server.py" --log presence.log --log-ip raw --log-days 0 --history-file chat.jsonl --history-days 0 --visits visits.jsonl`
2. In the server console, type `visits-key ROOM`. The room is the `room` value of the page's config (by default, the page name). The key is shown **only once**, for example `K7QF-29MD-XR4P`; only its fingerprint is kept, in `presence_visits_keys.json` (`--visits-keys` option). Running the command again gives a new key: the old one stops working. `visits-key ROOM off` removes the key; `visits-key` alone lists the rooms that have a key. `cle-visites` is accepted instead of `visits-key`. **Case matters** in the room name, as everywhere in the server (`Houses` and `houses` are two rooms): if the typed name only exists with a different case, the console says so. The `rooms` command (alias `salons`) lists the known rooms, with their exact case: connected visitors (walkers among them), number of visits and date of the last one, key or not. A room never visited and without a key is not shown: its name is the `room` value of `NOM.config.json`, the page name by default.
3. Send the creator their page address followed by `#visits`, and the key: `https://ADRESSE/index.html?region=galerie#visits`.

### 31.3 Creator side: the "Visit log" window

They open this link, from any device, with nothing to install. The region opens with the "Visit log" window. Without `#visits`, the "Visit log…" button of the Information window (I), next to "Copy diagnostics", opens the same window; it only exists on a page that has a presence server. They type the key (upper or lower case, dashes or spaces: it does not matter), then "Show" or Enter:

- "Per day" table: Date, Visits, Distinct visitors, Total duration, Median duration, With walk;
- "Visits of the last 30 days" table: Arrival, Duration, Walk (yes or no), and Nickname if the server has `--visits-names` (1000 visits at most);
- "Download (CSV)" button: both tables for a spreadsheet, durations in seconds, separator `;` in French and `,` in English.

The accepted key is kept by the browser: next time, the summary is shown at once. "Forget the key" erases it (do it on a shared computer). Esc or "Close (Esc)" closes the window; the region stays usable behind it.

Possible messages: key refused; too many attempts (5 refused keys per minute and per IP address, then a minute's wait); server started without `--visits`; server too old (before v48); server not answering; page without a presence server.

### 31.4 What is counted

- **A visit** is a connection to the presence server: an open page (spectator, when `spectate` is on, which is the default with a presence address) or a walk. Time spent walking is recorded separately ("With walk" column).
- **Reconnections**: a page reload, a network drop or a switch between walking and overview less than 2 minutes after the end counts as the same visit (same browser, same room).
- **Distinct visitors**: counted by the browser fingerprint. The same visitor on two devices counts twice; a browser that clears its data counts as a new visitor.
- **Not counted**: pages without a presence server, visitors whose connection fails (firewall, https page with a `ws://` address), pages built with `--no-spectate` as long as nobody walks. Reading the log itself counts as a visit (the page is open). The number of pages served is read in the web server's log (Apache).
- Days follow the clock of the server machine.
- A visit is written when it ends. Clean server stop (Ctrl+C): visits in progress are written. Sudden stop of the server or the machine: they are lost.

### 31.5 Personal data

The visit file **never contains an IP address**. The browser fingerprint is pseudonymous data, the nickname (with `--visits-names`) personal data: inform visitors and keep a reasonable duration (`--visits-days`). The `presence.log` log does not change. On a `ws://` address, the key travels in clear: for access from outside, page and presence over https and `wss://` (procedures § 11).

### 31.6 Files

Format of the visit file and of `presence_visits_keys.json`: § 27.10. Samples: `docs/samples/visits.sample.jsonl` and `docs/samples/presence_visits_keys.sample.json` (sample key `ABCD-EFGH-JKMN`, never to be used).

### 31.7 v48 tests

`tests/v48.py` (real presence server, Chromium): visits written without IP or nickname, reconnections merged, walking time, key fingerprint only, lower-case key accepted, wrong key, 5-attempt limit, `visits-key ROOM off`, purge, nicknames with `--visits-names`, clean stop, page window (key refused, summary, CSV, key kept then forgotten, Esc), page without presence, server without `--visits`, older server, missing server, English. `tests/samples.py` reads the two new samples.

### 31.8 Not tested

Windows (Ctrl+C in the Windows console), Edge, a real phone, Tailscale Funnel, the PowerShell lines themselves.

## 32. New in v49 (25/10/2026): updating `regions.json` from the sites folder

### 32.1 The command

`cd "P:\_OpenSim\SL&OS\Web_3d\web_3d\dist"; python .\glb2html.py --scan-sites "P:\_OpenSim\SL&OS\Web_3d\Sites" --dry-run`

`--dry-run` shows what would change without writing anything; the same line without `--dry-run` writes `Sites\regions.json`. The folder given is the one of the shared shell (`index.html` at the root); without `index.html`, a warning says so.

### 32.2 What the scan does

- One card per `NOM.config.json` file found in the folder and its subfolders (the `lib` and `_bak` folders and those starting with a dot are skipped, as is a file without a `room` field).
- Card address: `index.html?region=dossier/NOM`; room and presence server: those of the config (`room`, `presenceUrl`).
- An existing card is recognised by its room, otherwise by its address. Its name, place (`x`, `y`), arrival (`spawn`) and `id` are kept: only the address, room, server and thumbnail are updated. The name of a new card is the file name: change it once in `regions.json`, it is kept afterwards.
- A new region gets the first free cell of the `y = 0` row (never a place already taken: two cards at the same place make the map fall back to a plain list).
- The creators' cards (full address in `http` or `https`) are never touched. The header (`showUrl`) and the shape of the file (object or list) are kept. Without `regions.json`, the file is created with the header.
- Nothing is deleted: a local card whose region is no longer in the folder is reported as an "orphan" and kept.

### 32.3 Thumbnails

An image `NOM.jpg` (or `.jpeg`, `.png`, `.webp`) next to `NOM.config.json` becomes the card's thumbnail, through a relative path (`houses/NOM.jpg`): `regions.json` stays light, and the path works from `carte.html` as from the map opened with M, both at the root. Without an image, the thumbnail already recorded is kept.

Recommended: a **square image of 320 x 320 pixels**, medium-quality JPEG (a few tens of KB, estimate). The tile shows it as a square about 155 pixels wide (`aspect-ratio: 1`); 320 pixels stay sharp on high-density screens. An image that is not square is cropped in the centre (`object-fit: cover`).

### 32.4 v49 tests

`tests/v49.py` (no browser): cards created and updated, thumbnails (encoded path), name, place and arrival kept, header kept, external card untouched, orphan kept, no duplicate places, skipped folders, `--dry-run`, second run without change, plain list, missing folder, missing `index.html`, English.

### 32.5 Not tested

Windows, Klaatou's paths, the PowerShell lines themselves.

## 33. What is new in v50 (25/10/2026): the world map in the viewer

### 33.1 Importing and exporting `regions.json`

"World map" section of the viewer:

- **Import regions.json** accepts the plain list as well as the object with a header (`{"showUrl": ..., "regions": [...]}`, § 27.6). Before v50, the object shape was refused ("array expected"): it is the one `--scan-sites` writes when it creates the file.
- **Export regions.json** gives back the imported shape: an object with the same header, or a list. The header is remembered by the browser, like the list of regions. Without an import, the export is a plain list.
- Every card keeps all its fields, including `presence` (presence server of an external region), which used to be lost on import.
- A file without regions is refused with the message "map file expected: list of regions, or object {"regions": [...]}".

### 33.2 Adding or updating this region

The **Add / update this region in the map** button updates the card of the same room in place, like `--register`: its position in the list no longer changes, an empty field (a thumbnail not captured, for instance) does not erase the old one, and the fields the viewer does not show (`presence`...) stay. The name, address, place and arrival come from the viewer's fields.

### 33.3 v50 tests

`tests/v50.py` (Chromium): import of the object shape, identical export (header and unknown fields kept), viewer reload, in-place "Add", plain list exported as a list, refused file (French and English).

### 33.4 Not tested

Edge, Windows.

## 34. What's new in v51 (25/10/2026): creators on the presence server

### 34.1 What it is for

The host of a presence server welcomes the regions of other creators, hosted wherever they like. Without care, any page that knows the server address can connect to it and take someone else's room, and adding an origin (`--origins`) means restarting the server. With `--creators`, the server only accepts declared pages, each in its own rooms. Without `--creators`, nothing changes.

### 34.2 The creators file

Start: add `--creators presence_creators.json` to the server line (path relative to the script's folder). The file is written by hand, from `docs/samples/presence_creators.sample.json` (fields in § 27.10). It is re-read without restarting the server: a change applies to the next connections (checked at most every 2 s); connections already open stay (to cut one: `ejecter`).

- **Origin**: the beginning of the page address, without a path: `https://alice.example`, with the port if it is not the usual one (`http://localhost:8000`). A page opened from the disk and the viewer have the origin `null`.
- **Prefix**: creator `alice` only opens `alice.NAME` rooms (case of the prefix ignored); the `room` value of their config must therefore start with `alice.`. Only one entry may have `"prefix": ""`: the host, who keeps every room that belongs to no creator (their current rooms keep their names).
- **Limits**: `maxWalkers` (walkers at most over all their rooms; beyond it, "room full", also when switching to walking), `maxRooms` (rooms open at the same time). The general limits (`--max-per-room`, `--max-total`, `--max-per-ip`) still apply.
- **`"off": true`** suspends the creator.
- Missing file: every connection is refused. Unreadable file (for example while it is being written): the previous list is kept. Invalid entry: reported in the console and ignored.

### 34.3 What the visitor sees

The page shows "presence refused:" followed by the reason, and does not retry (reload the page once fixed): page not declared on this server, creator suspended, room that does not belong to the creator, too many open rooms. The viewer shows the same reason. The server closes the connection with code 4003, which "Copy diagnostics" shows.

### 34.4 Console and log

- `creators` (alias `createurs`) re-reads the file and lists each creator: prefix, active or suspended, open rooms, walkers, origins.
- Each refusal is logged as "refusal" in `presence.log` with its reason; an accepted connection is recognised by the prefix of its room.
- Visit log keys remain per room: `visits-key alice.galerie`.

### 34.5 Welcoming a creator

Procedures § 6, item 7.

### 34.6 Limits

- The origin is announced by the browser: it stops another web page from taking a room, not a program written on purpose that would announce a false origin. Against it remain `--max-per-ip`, `ejecter` and `bannir`.
- An https page can only reach a `wss://` server (procedures § 11).
- The world map counters (room request) follow the same origin rule.

### 34.7 v51 tests

`tests/v51.py` (real server, then Chromium): without a file, everything is accepted; refusal by origin, suspension, prefix, number of rooms; walkers at most on arrival and when switching to walking; host without prefix; re-reading on change; console; log; refusal shown by the page (French, English) and by the viewer. `tests/samples.py` reads the sample.

### 34.8 Not tested

Windows, Edge, `wss://` behind Funnel, a creator's page on another domain.

### 34.9 Empty connections

A connection opened on the presence server port then closed without sending anything (browser preconnection, port test, robot) filled the console with a long "opening handshake failed" trace with versions 14 and 15 of `websockets`. Since v51, it gives a short "empty" line in the console and in `presence.log`, with the caller's address (masked according to `--log-ip`) and the number of empty connections, at most one line per minute and per address. It is harmless; other `websockets` errors are still shown in full.

`tests/v51_vides.py`: with the installed version, then with an old version given by the `WS_OLD` variable (tried here with 13.1, 14.2 and 15.0.1). Not tested: Windows, Edge.

### 34.10 Presence address "same name as the page"

A presence address can be written with a star instead of the name: `ws://*:8765`. The page replaces the star with the name it was opened with: opened through `http://localhost:8096`, it targets `ws://localhost:8765`; opened through the network address or the public name of the machine, it targets that same address. A page opened from the disk, and the viewer, target `127.0.0.1`. The rule "presence at the same place as the page" (procedures § 11) is thus kept automatically.

Why: each config or card carried a single address (network address, public IP address or public name), right for only one of the access paths. A page opened through the public name that targets a local network address is cut by Edge before the request is sent: the map stays without counters and the server logs an "empty" connection at each query (every 10 s for `carte.html`, every 8 s for the Map window). This blocking is deduced from Klaatou's observations; it is not reproduced here and was not tried under Edge.

The star works everywhere: `--presence-url`, `presenceUrl` of `NOM.config.json`, `presence` field of `regions.json`, presence field of the viewer. The server recalls this form at start-up. Limit: for a visitor coming from the Internet, the presence server port must be reachable under the same name as the page (box port forwarding, or Funnel, procedures § 11).

`tests/v51_etoile.py` (Chromium): page opened through `127.0.0.1` then `localhost`, Map window, `carte.html`, visit log, viewer opened from the disk, `ws://0.0.0.0` still corrected, error message with the resolved address. Not tested: Windows, Edge.

## 35. What's new in v52 (25/10/2026)

### 35.1 `carte.html`: count, total, two lines

Above the grid: "12 regions · Total: 3 visitors · 2 walkers". Each room is counted once; with an old server that does not answer `visitors`, only the walkers are counted (no invented visitors). In the cards, visitors and walkers go on two lines in French ("2 visiteurs", then "1 promeneur") and stay on one line in English ("2 visitors · 1 walker"): this is the language key `map.sep` (`page.map.sep` for the map opened with M), a line break in French and " · " in English; a new language chooses its own. The total stays on one line.

### 35.2 Arrival alert (sound and marker)

A checkbox at the top of `carte.html`, "Arrival alert (sound and marker)", remembered in this browser (key `glb2html_map_alert`). When ticked:

- A **rise in the visitor count** of a room on the map between two polls is an arrival: two rising notes (660 then 880 Hz, like a walker arriving in the page), at most one beep every 2 s, and the **region's card is marked**: dashed outline that blinks, yellow background and the text "● arrival hh:mm" (never colour alone; no blinking if the system asks for reduced motion). The marker stays until the card is hovered; unticking the box clears it. The status line says "last arrival: region, hh:mm".
- A server's **first poll** never sounds (it is the baseline). An arrival and a departure within the same poll interval cancel out: no beep.
- The browser forbids any sound before a click or a key press on the page: after a reload, the ticked box shows "sound starts at the first click on the page". Ticking the box is already a click.
- **Delays**: at the top of the `carte.html` script (in the repository, `MAP_PAGE_TEMPLATE` of `src/gen_tpl.py`), `const POLL_MS = 10000;` (normal poll) and `const POLL_ALERT_MS = 5000;` (box ticked), in milliseconds. The delay is re-read at each round and as soon as the box changes. Each poll opens one short connection per presence server: raising these values lightens the server (load not measured).

The alert only concerns `carte.html` (and the standalone `--map-page`); the map opened with M keeps the page's sounds (§ 21.6).

### 35.3 Thumbnail enlarged on hover

Hovering a card that has a thumbnail, **with a mouse only** (not with a finger), shows the thumbnail large, 400 px at most, moved to stay inside the window. It is the same code in `carte.html` and in the map opened with M. The recommended thumbnails are 320 x 320 px (§ 32.3): the image is enlarged, not improved. A card without a thumbnail has nothing to enlarge.

### 35.4 "Show the sea" checkbox

In Settings, before "Animated sea", only if the page has a sea (not made with `--no-sea`). Unticked: the sea disappears from the scene, "Animated sea" and "Waves" are greyed out. The choice is kept with the other settings (key `glb2html_opts_SALON`); "Default values" restores the page's own. Useful for a region without water made without `--no-sea` (the sea is on by default). The sea height is only used to place the water plane: hiding the sea changes no collision. A page made with `--no-sea` ignores an old remembered choice.

### 35.5 Presence server: ordinary HTTP requests

With `websockets` 14 and 15, an ordinary HTTP request on the server port (a browser opening its address, a robot, a test) wrote a full trace ("opening handshake failed", `InvalidUpgrade`, "invalid Connection header: keep-alive"), although the client does get "426 Upgrade Required". The log now writes an `http request` line instead: address, path, host, agent and reason, at most one per minute and per address. It says who came. Any control character (terminal escape, bell) is replaced with a space, in this line and in the whole log. Malformed requests and other errors are still shown in full. **Restart the presence server** from `dist\`. Recent versions of `websockets` (17.3 tried) do not write this trace: nothing to filter.

### 35.6 Renamed tiled region

`NOM.overview.glb` keeps in each node the path of its tile as it was when the region was split (`NOM.tiles/T_3_0_0.glb`). Up to v51, renaming the folders and the index paths by hand left the overview **visible under the detailed tiles**: overlapping surfaces, moire and dark patches on the terrain and the rocks (Klaatou's case, Houses region, 25/10/2026). Since v52, the page finds the cell by the **tile's file name** when the full path does not match (unique in a region; otherwise the cell stays visible, never a hole). To rename a tiled region: rename `NOM.tiles`, `NOM.overview.glb`, `NOM.tiles.json`, `NOM.config.json` and `NOM.zones.json`, fix in the index the tiles' `file` paths and `overview.file`, fix the `tiles` field of the config, then copy the v52 `index.html` shell. There is no need to regenerate the overview.

### 35.7 Tests of v52

`tests/v52.py` (Chromium, real presence server, fake `AudioContext`): `carte.html` ("walker", total and count, no sound on the first poll or with the box unticked, two notes 660 and 880 Hz on an arrival, visual marker and its disappearance on hover, delay re-read when the box is ticked, constants `POLL_MS` and `POLL_ALERT_MS`), enlarged thumbnail (map and M map), old server, English, "Show the sea" checkbox; `tests/v52_http.py` (real server, installed `websockets` then `WS_OLD` and `WS_OLD2`); `tests/v52_renom.py` (split region, copied under two other names); `tests/i18n.py` accepts a blank value for keys ending in `.sep`; `tests/v47.py` adapted to the "walker" text.

### 35.8 Not tested

The real sound (the test replaces `AudioContext`), Edge, Windows, a real phone, a tab kept in the background for a long time (the browser may slow its timers: not measured), the server load at 5 s. The renaming of § 35.6 was confirmed by Klaatou on his Houses region (25/10/2026).
