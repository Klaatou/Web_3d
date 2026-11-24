# Version history

Dates are in dd/mm/yyyy format.

French version: [`CHANGELOG.fr.md`](CHANGELOG.fr.md). The entries before 1.0.0 (v52 down to v1) are kept in French, as they were written; the complete history in French is in `CHANGELOG.fr.md`.

## Unreleased (after 1.13.0)

### 24/11/2026: README: 3D models, combinable picture, mini player (batch 1.13.9)

- **Request** (Klaatou): announce the new zones in the README (the `.glb` models placed separately, which he also puts in the demo regions).
- **Done**: `README.fr.md` and `README.md` (feature list and "Zones" section): 3D models placed separately (§ 5.23), a picture can also be a portal, a radio, a music player or a command (§ 5.11), the floating window is called the "mini player".
- **Checked**: `tests/readme_liens.py`; `verif_trad.py` on the histories: 0 errors; on the README pair: the same 3 errors as before the batch (document names `docs/fr/...` and `docs/en/...`), unchanged.
- **Not done**: the demo line of the README ("two regions linked by portals") is out of date, the demo has five; outside this batch.
- Files: `README.fr.md`, `README.md`, FR and EN histories, `VERSION`, both CHANGELOGs.

### 23/11/2026: documents of batch 1.13.7 (batch 1.13.8)

- **Request** (Klaatou): update the documents for batch 1.13.7 (first image of the video screens, click out of range).
- **Done**: `docs/fr/MANUEL.md` and `docs/en/MANUAL.md` section 5.21 (opening paragraph, preview, click out of range, tests, not tried) and the appendix (section 13, block "1.13.7"); `docs/fr/REFERENCE_JSON.md` and `docs/en/REFERENCE_JSON.md` section 11.4 (row `radius`); `docs/fr/HISTORIQUE.md` and `docs/en/HISTORY.md`: one row.
- **Checked**: `verif_trad` on the three pairs: 0 errors; `readme_liens` passes.
- Files: `docs/fr/MANUEL.md`, `docs/en/MANUAL.md`, `docs/fr/REFERENCE_JSON.md`, `docs/en/REFERENCE_JSON.md`, `docs/fr/HISTORIQUE.md`, `docs/en/HISTORY.md`, `VERSION`, both CHANGELOGs; `dist\` is unchanged.

### 23/11/2026: video screens show their first image, and a click starts them out of range (batch 1.13.7)

- **Request** (Klaatou): on arriving in a region, video screens were black boxes, not even with the right proportions; they should show their first image (started but paused), and a click should start a screen even out of range.
- **Cause**: `src/core.js`, `videoPlane`: the screen was created dark (`color: 0x111111`) in 16:9, and the video was only created at the first play request, i.e. within `radius` and in view.
- **Done**: a screen in view and closer than `zoneInfoDist` (150 m by default) loads the start of its file (`preload="metadata"`, 4 loads at a time at most) without playing: its first image and its proportions replace the dark box; a screen behind the visitor or out of view loads nothing. The current image of a paused video is now sent to the graphics card (a `VideoTexture` only follows played frames: without this the preview stayed dark). Out of range, a click on a screen starts it, without sound, as long as it stays in view; a second click stops it; once out of view it stops and does not start again without a new click. Within range, nothing changes.
- **Tests**: `tests/zone_video.py` updated: the checks "nothing requested out of range" encoded the replaced behavior; they become: first image loaded, paused, right proportions, drawn on screen (pixels), `preload` metadata, no play, nothing requested for screens out of view; new checks for the click out of range (start, second click stops, does not restart by itself, stops when turning away, no sound for a sound screen).
- **Checked** (sandbox, Chromium): `zone_video`, `zone_video_liste`, `editeur_video_action`, `arbitrage_son`, `lien_image`, `zones_unifiees`, `zone_labels`, `v24`, `v34`, `v40`, `build_reference`, `samples`, `dist_a_jour`, `i18n`, `doc_options` and `readme_liens` pass.
- **Not tried**: Edge, Windows; the network volume of a large real file with `preload="metadata"` (only a small test file here).
- **Remaining to update**: the manual (section on video screens), at the validation of the batch.
- Files: `src/core.js`, `tests/zone_video.py`, `VERSION`, both CHANGELOGs; `dist\` and `VERSIONS.json` come from `python build.py`.

### 22/11/2026: documents of batch 1.13.5 (batch 1.13.6)

- **Request** (Klaatou): fix the documents concerned by batch 1.13.5 (zone names by language, title of a YouTube link).
- **Done**: `docs/fr/REFERENCE_JSON.md` and `docs/en/REFERENCE_JSON.md` section 11.4: new rows `labels` (in the "where it is" table) and `linkTitle` (in the settings table), `labels` in the keys used by an arrival point, new paragraph "Title of a YouTube link" (option `--link-titles`); `docs/fr/MANUEL.md` and `docs/en/MANUAL.md`: zone format paragraph (section 5), what the bubble shows (section 7.13) and the appendix (section 13, block "1.13.5"); `docs/fr/HISTORIQUE.md` and `docs/en/HISTORY.md`: one row.
- **Checked**: `verif_trad` on the four pairs (reference, manual, histories): 0 errors; `readme_liens`, `i18n`, `dist_a_jour` pass.
- **Not done**: `REPRISE.md` (only delivered when Klaatou asks, rule 23); the options reference (`docs/REFERENCE_OPTIONS.md`) already comes from `python build.py`.
- Files: `docs/fr/REFERENCE_JSON.md`, `docs/en/REFERENCE_JSON.md`, `docs/fr/MANUEL.md`, `docs/en/MANUAL.md`, `docs/fr/HISTORIQUE.md`, `docs/en/HISTORY.md`, `VERSION`, both CHANGELOGs; `dist\` is unchanged.

### 22/11/2026: zone names by language and the bubble of a YouTube link (batch 1.13.5)

- **Request** (Klaatou): the name of a zone must follow the language of the page, and the bubble over a YouTube link must show the title of the video, not the address.
- **Done**: new optional key `labels` in the zones file, `{"fr": "...", "en": "..."}` (60 characters at most, other languages ignored): the page shows the name of its own language everywhere a zone name is shown (bubble, spawn list and buttons, prompts, toasts, Sound and State windows), then `label`, then the id. A zone without `labels` behaves as before; the same `{"fr", "en"}` object written in `label` itself is read as `labels` (never shown as "[object Object]"). Internally the key is `labs` (`labels` is already the list of stream names of the old radio format, which is still read as before). New optional key `linkTitle` on a link zone (or an image or video screen that opens a link): the title of the page of the link, shown on the second line of the bubble in place of the address. Without it, a YouTube link shows `youtube.com` (not the whole address); any other link still shows its address.
- **Where the title comes from**: not from the visitors' browsers (a hover would contact YouTube for each visitor). New option `glb2html.py --link-titles FILE` (a zones file, or a settings file with `zones`): asks the oEmbed service of YouTube once per YouTube link that has no `linkTitle`, writes it into the file (original kept in `FILE.bak`), then stops; a link whose title is not found is left as it is and reported; a `linkTitle` already written is never touched. The title is then in the generated page like any other key.
- **Mirrors**: `zoneIn`, `zoneOut`, `cleanZone`, `cleanLabs` (`core.js`) and `zone_in`, `zone_out`, `clean_zones`, `clean_labs` (`gen_tpl.py`) written together; `docs/REFERENCE_OPTIONS.md` rebuilt (new option).
- **Tests**: new `tests/zone_labels.py` (35 checks: names in `fr-FR` and `en-GB`, fallback to `label` then id, bubble with title / without title / other link, JS and Python give the same zones and the same output, round trip, old radio `labels` list not taken for a name, `--link-titles` on a list and on a settings file with a simulated oEmbed service, title already written, link not YouTube, title not found, service unreachable, second run).
- **Checked** (sandbox, Chromium): `zone_labels`, `zones_unifiees`, `zone_cast`, `radio_flux`, `radio_titre`, `bulle_radio`, `radio_memoire`, `zone_model`, `zone_frame`, `lien_image`, `zone_video`, `zones_url_cone`, `zone_audio`, `zone_apercu`, `zone_pochette`, `zone_distance`, `zones_numeros`, `image_zone`, `editeur_cone`, `editeur_video_action`, `arbitrage_son`, `v24`, `v34`, `v40`, `build_reference`, `samples`, `i18n`, `doc_options`, `readme_liens` and `dist_a_jour` pass.
- **Not tried**: the real oEmbed service of YouTube (no network in the sandbox: simulated by `WEB3D_OEMBED`, a variable that only exists for the tests); Edge, Windows.
- **Not done**: the editor of the viewer still shows and edits the raw `label` (the `labels` and `linkTitle` keys are kept and written back unchanged).
- **Remaining to update**: `docs/REFERENCE_JSON` section 11.4 (keys `labels` and `linkTitle`), the manual (zone names, bubble, option `--link-titles`) and the histories, at the validation of the batch.
- Files: `src/core.js`, `src/template.html`, `src/gen_tpl.py`, `src/i18n/fr.json`, `src/i18n/en.json`, `tests/zone_labels.py` (new), `docs/REFERENCE_OPTIONS.md`, `VERSION`, both CHANGELOGs; `dist\` and `VERSIONS.json` come from `python build.py`.

### 22/11/2026: documents of batches 1.13.2 and 1.13.3 (batch 1.13.4)

- **Request** (Klaatou): fix the documents concerned by the radio batches 1.13.2 (bubble) and 1.13.3 (stream remembered).
- **Done**: `docs/fr/MANUEL.md` and `docs/en/MANUAL.md`: section 5.19 (the stream chosen is remembered for the zone; the sentence "leaving the zone goes back to the first stream" is removed), section 7.13 (what the bubble of a radio shows), section 7.66 (the `glb2html_radio_` key in the list of what the page keeps in the browser) and the appendix (section 13, block "1.13.2 to 1.13.4"); `docs/fr/HISTORIQUE.md` and `docs/en/HISTORY.md`: one row per batch (1.13.2, 1.13.3, 1.13.4).
- **Checked**: `verif_trad` on the manual and on the histories: 0 errors; the old wording ("premier flux", "first stream", "+N") searched in the documents and READMEs: only the sentence above was concerned.
- **Not done**: `REPRISE.md` (section 5, rule "leaving the zone brings back the first stream"), only delivered when Klaatou asks for it (rule 23).
- Files: `docs/fr/MANUEL.md`, `docs/en/MANUAL.md`, `docs/fr/HISTORIQUE.md`, `docs/en/HISTORY.md`, `VERSION`, both CHANGELOGs; `dist\` is unchanged.

### 22/11/2026: the stream chosen on a radio is remembered (batch 1.13.3)

- **Request** (Klaatou): the radio being listened to should be remembered, to be found again on coming back to the region.
- **Cause**: `RADIO.set` (`template.html`) put the chosen stream back to the first one at every entry into the zone (`selIdx = 0`), and the choice was kept nowhere. This was the rule noted in `REPRISE.md` ("leaving the zone brings back the first stream"); this batch replaces it.
- **Done**: choosing a stream in a radio zone with several streams is remembered **per zone**, as zone id -> stream address, in the browser (key `glb2html_radio_` + region, next to the other per-region keys). It is found again when coming back into the zone, after a reload of the page and at the next visit. If the remembered address no longer exists in the zone, the first stream is used; a damaged stored value is ignored; a radio with a single stream stores nothing; 200 zones at most. The bubble of a radio (batch 1.13.2) shows the remembered stream even when that radio is not the one playing. New in `template.html`: `pickIdx`, `pickSave`, `picks`; `RADIO.idxOf` uses them.
- **Tests**: new `tests/radio_memoire.py` (12 checks: first visit, choice kept, leaving and coming back, single stream, reload, bubble, vanished address, four kinds of damaged value; 5 of them fail without the batch); `tests/radio_flux.py` (the check "leaving the zone brings back the first stream" now expects the chosen stream) and `tests/bulle_radio.py` (global view: the remembered stream) follow the new rule.
- **Checked** (sandbox, Chromium): `radio_memoire`, `radio_flux`, `radio_titre`, `bulle_radio`, `zone_cast`, `arbitrage_son`, `zone_model`, `v24`, `v34`, `i18n` and `dist_a_jour` pass.
- **Not tried**: Edge, Windows; the choice made from the Sound window list (same `RADIO.setIdx` as the State window list, tested through the latter).
- **Remaining to update**: manual section on the radio (the sentence "leaving the zone brings back the first stream", FR `docs/fr/MANUEL.md` line 750 and its English counterpart), at the validation of the batch.
- Files: `src/template.html`, `tests/radio_memoire.py` (new), `tests/radio_flux.py`, `tests/bulle_radio.py`, `VERSION`, both CHANGELOGs; `dist\` and `VERSIONS.json` come from `python build.py`.

### 22/11/2026: the bubble of a radio shows the stream name (batch 1.13.2)

- **Request** (Klaatou): the bubble that appears over a radio showed the stream address; it should show the stream label, and best of all the label of the stream chosen and playing.
- **Cause**: `zoneTipText` (`core.js`) built the second line from `streams[0][1]`, the address of the first stream, followed by " ... +N" when there were several; the stream chosen in the Sound window (`selIdx`, inside `RADIO`) was out of its reach.
- **Done**: the second line is now the name of the chosen stream when this radio is the one being listened to, otherwise the name of its first stream (the one that would start); a stream without a name keeps its address; the " ... +N" is gone. New function `castTipSub` and hook `viewer.castTipIdx` in `core.js`, set by `template.html` to the new `RADIO.idxOf`; the cache key of the bubble now includes its second line (a change of stream shows at the next mouse move).
- **Numbering**: 1.13.2; 1.13.1 stays reserved for the README batch, not applied yet.
- **Checked** (sandbox, Chromium): new test `tests/bulle_radio.py` (fails on 1.13.0, passes now); `zone_cast`, `radio_flux`, `radio_titre`, `arbitrage_son`, `zone_model`, `v24`, `v34`, `i18n` and `dist_a_jour` pass.
- **Not tried**: Edge, Windows, touch screens (no hover there).
- **Remaining to update**: manual and procedures, if they describe the bubble of a radio zone (to check at the validation of the batch).
- Files: `src/core.js`, `src/template.html`, `tests/bulle_radio.py` (new), `VERSION`, both CHANGELOGs; `dist\` and `VERSIONS.json` come from `python build.py`.

## 1.13.0 (21/11/2026)

### 21/11/2026: release 1.13.0: video screens, private messages, one sound at a time, unified zones and placed models

- **Release**: 1.13.0 (21/11/2026), decided by Klaatou, gathers batches 1.12.1 to 1.12.45 (described below, under this same heading). The minor number goes up: features were added since 1.12.0. This batch only changes `VERSION` and the documents (manual title, overview, histories, this log); `dist\` and `VERSIONS.json` are unchanged.
- **Per-file numbers**: `index.html`, `glb-viewer.html`, `glb2html.py` 1.12.42; `carte.html` 1.12.39; `oar2glb.py` 1.12.27; `presence_server.py` 1.12.30; unchanged: `glb2tiles.py` 1.11.12, `oars2site.py` 1.10.25, `web3d_gui.py` 1.10.31, `diag_carte.py` 1.10.2, `extraire_batiments.py` 1.6.3, `iar2oar.py` 1.6.4. **`presence_server.py` changes** (1.10.37 to 1.12.30): hosts must replace it for private messages.
- **Tried by Klaatou**: private messages (21/11/2026, "it works"); the click on the model of a radio (1.12.40, "perfect"); the video tests pass on his machine (21/11/2026). **Not tried here** (Linux sandbox): Windows, Edge, Firefox, Safari, a real touch screen; on his screen: the cone off on his own zones, a large `.glb` in `modelLazy` on a real network, `solid` on a real building, a video screen with `link` or `portal` / `ha`.
- **Known documentation debt**: none; the French / English pairs of documents give 0 error in `verif_trad` (21/11/2026).
- **GitHub release notes** (to attach: `galerie-photos.zip` and `region-simple.zip`, rebuilt by `python fabriquer_paquets.py` after `VERSION` is set to 1.13.0), English then French:

  > **Web_3d 1.13.0: mini player, video screens, one sound at a time, private messages**
  >
  > **Do not unzip over an existing package**: copy `index.html`, `carte.html` (and `favicon.ico`) into your folder instead. **Presence server hosts**: replace `presence_server.py` (now 1.12.30) to get private messages.
  >
  > ### What's new
  >
  > **1. Mini player (floating window)**
  >
  > - A link zone, or an image zone that has a link, can now open its page, or a YouTube video or playlist, in a small floating window on top of the page. You can move it, resize it and close it; you never leave the region.
  > - It is not a video screen: the mini player floats over the page, while a video screen (next item) is part of the 3D scene, on a wall.
  >
  > **2. Video screens (inside the 3D scene)**
  >
  > - New zone type `video`: a screen on a wall of the region. The video starts when you walk up to it, a click pauses it, and only the nearest screen talks.
  > - A screen can play a list of videos (previous / next buttons), and can also be a link, a portal or a Home Assistant command.
  >
  > **3. One sound at a time**
  >
  > - The radio, the music, the video screens and the YouTube mini player no longer play over each other: you hear the nearest source. New mute button and **N** key (for No sound).
  >
  > **4. Private messages**
  >
  > - Click a visitor's avatar, or their name in the chat, to write to them, or type `/dm name message` (`/mp` and `/pm` work too). Each conversation has its own window: you can move it, shrink it or close it without losing the text, and a new message makes it blink. Buttons Ignore and Save the chat. Hosts can turn private messages off.
  >
  > **5. Zones**
  >
  > - An image zone can now also be a portal, a radio, a music player or a Home Assistant command: the picture itself is the door, the radio, and so on.
  > - New zone type `model`: place your own 3D model (a `.glb` file) in the region. On its own it is just decoration; give it a link, a portal, a command, a radio or a music and it becomes clickable.
  > - Radio and music zones also work in the overview of the region (outside walk mode).
  > - A radio or music zone can show an illustration (an image) in the Sound window, with an optional link that opens a web page in a new tab.
  > - Creators who have their own zone files in the old format can convert them using this script: `python glb2html.py --convert-zones FILE`; the original is preserved as a `.bak` file.
  >
  > **6. Other changes**
  >
  > - Effect proposals: when a region has shiny materials, the page used to pop up a message offering to turn on Reflections (and Light rendering). It now shows a blinking ✦ icon next to Settings; click it to see the question. Settings > "Effect proposals" brings the message back.
  > - The **B** key, which hides the chat panel, works again after a chat message is sent.
  > - The OAR conversion process (`oar2glb`, used by `oars2site`) no longer halts when `convoar` writes an object name ending in a backslash, and it now clearly indicates when an OAR file is corrupted.
  > - Documents and examples brought up to date, in English and French.

  > **Web_3d 1.13.0 : mini lecteur, écrans vidéo, un seul son à la fois, messages privés**
  >
  > **Ne pas dézipper par-dessus un paquet existant** : copier `index.html`, `carte.html` (et `favicon.ico`) dans votre dossier. **Hébergeurs du serveur de présence** : remplacer `presence_server.py` (maintenant 1.12.30) pour avoir les messages privés.
  >
  > ### Nouveautés
  >
  > **1. Mini lecteur (fenêtre flottante)**
  >
  > - Une zone lien, ou une zone image qui a un lien, peut maintenant ouvrir sa page, ou une vidéo ou une liste YouTube, dans une petite fenêtre flottante par-dessus la page. On peut la déplacer, la redimensionner et la fermer ; on ne quitte jamais la région.
  > - Ce n'est pas un écran vidéo : le mini lecteur flotte au-dessus de la page, alors qu'un écran vidéo (point suivant) fait partie de la scène 3D, sur un mur.
  >
  > **2. Écrans vidéo (dans la scène 3D)**
  >
  > - Nouveau type de zone `video` : un écran sur un mur de la région. La vidéo démarre quand on s'en approche, un clic la met en pause, et seul l'écran le plus proche parle.
  > - Un écran peut jouer une liste de vidéos (boutons précédent / suivant), et servir aussi de lien, de portail ou de commande Home Assistant.
  >
  > **3. Un seul son à la fois**
  >
  > - La radio, la musique, les écrans vidéo et le mini lecteur YouTube ne se superposent pas : on entend la source la plus proche. Nouveau bouton muet et touche **N** (comme No sound).
  >
  > **4. Messages privés**
  >
  > - Un clic sur l'avatar d'un visiteur, ou sur son nom dans le chat, pour lui écrire, ou taper `/mp pseudo message`. Chaque conversation a sa fenêtre : on peut la déplacer, la réduire ou la fermer sans perdre le texte, et un nouveau message la fait clignoter. Boutons Ignorer et Enregistrer le dialogue. Les hébergeurs peuvent couper les messages privés (ils passent aussi par le serveur de présence).
  >
  > **5. Zones**
  >
  > - Une zone image peut maintenant être aussi un portail, une radio, une musique ou une commande Home Assistant : l'image elle-même est la porte, la radio, etc.
  > - Nouveau type de zone `model` : on pose son propre modèle 3D (un fichier `.glb`) dans la région. Seul, c'est un décor ; avec un lien, un portail, une commande, une radio ou une musique, il devient cliquable.
  > - Les zones radio et musique marchent aussi en vue d'ensemble de la région (hors Promenade).
  > - Une zone radio ou musique peut afficher une illustration (une image) dans la fenêtre Son, avec un lien facultatif qui ouvre une page web dans un nouvel onglet.
  > - Les Créateurs qui ont leurs propres fichiers de zones selon l'ancien format peuvent les convertir avec ce script : `python glb2html.py --convert-zones FICHIER` ; l'original est gardé en `.bak`.
  >
  > **6. Autres changements**
  >
  > - Propositions d'effets : quand une région a des matériaux brillants, la page affichait un message pour proposer d'activer les Reflets (et le Rendu léger). Elle affiche maintenant une icône ✦ qui clignote à côté de Réglages ; un clic affiche la question. Dans Réglages la case « Propositions d'effets » remet le message.
  > - La touche **B** qui masque le pavé du chat marche de nouveau après l'envoi d'un message du chat.
  > - La conversion des OAR (`oar2glb`, utilisé par `oars2site`) ne s'arrête plus quand `convoar` écrit un nom d'objet qui finit par une barre oblique inverse, et dit clairement quand un fichier OAR est abîmé.
  > - Documents et exemples remis à jour, en français et en anglais.

### 21/11/2026: verif_trad at zero errors (batch 1.12.45)

- **Request** (Klaatou): fix the 6 `verif_trad` errors left by batches 1.12.30 to 1.12.44.
- **Done**: `docs/en/MANUAL.md` line 1240: the `/mp`, `/ignore` and `/unignore` commands are written as in the French manual (`pseudo`, `tous`), inline code being identical in both languages (the command accepts `all` and `tous`); `docs/en/SIMPLE_PROCEDURES.md` § 18: `NOM.zones.json` (not `NAME.zones.json`).
- **Checked**: `verif_trad` on the manual and on the simple procedures: 0 errors.
- **Not done**: nothing.
- Files: `docs/en/MANUAL.md`, `docs/en/SIMPLE_PROCEDURES.md`, FR and EN histories, `VERSION`, both CHANGELOGs.

### 21/11/2026: documents of batches 1.12.39 to 1.12.43 (batch 1.12.44)

- **Request** (Klaatou): bring the documents up to date, JSON examples included.
- **Done**:
  - `REFERENCE_JSON.md` (FR, EN) § 11.4: `model`, `scale`, `pitch`, `roll`, `solid`, `actionRadius`, `modelLazy`; cone default (false in the unified format); combinations (video screen with `link`, `portal`, `ha`; `model` alone or carrying an action); three JSON examples;
  - sample `region.zones.sample.json`: 17 zones (`screen-link`, `screen-portal` added; the READMEs said 14 while the file had 15); samples README, FR and EN;
  - manual: § 5.21 (screen action), § 5.23 (new, model placed on its own, `--model-lazy`), § 5.19, § 5.20 and § 7.17 (cone), appendix;
  - `PROCEDURES.md`, `SIMPLE_PROCEDURES.md` (variant of § 17, new § 18), `DEVELOPMENT.md` (ffmpeg of the video tests), index, histories FR and EN.
- **Checked**: `samples.py` (17 zones, 16 public, video screens with an action), `doc_options`, `build_reference`, `readme_liens`, `i18n`; the three JSON examples added to `REFERENCE_JSON.md` are valid and identical to those of the sample file.
- **Not done**: `docs/REFERENCE_OPTIONS.md` is rebuilt by `python build.py` on Klaatou's side; `CREATORS.md` does not talk about zones: unchanged.
- Files: `docs/` (documents above), `docs/samples/`, `tests/samples.py`, `VERSION`, both CHANGELOGs.

### 21/11/2026: the video tests find ffmpeg by themselves (batch 1.12.43)

- **Request** (Klaatou): `zone_video.py` and `zone_video_liste.py` stop on "ffmpeg absent" when `ffmpeg.exe` is not in the PATH; the tests have to find it.
- **Done**: new helper `tests/ffmpeg_chemin.py`: ffmpeg is looked for in the PATH, otherwise in the file `tests/ffmpeg.chemin.txt` (one line: the full path of `ffmpeg.exe`, a personal file ignored by git); both tests use it, the missing message says where to put it; `tests/tout.py` does not take the helper for a test.
- **Checked**: the helper in the three cases (PATH, file, nothing); `zone_video_liste.py` run with a PATH without ffmpeg and the path in the file; `tout.py --liste` does not count the helper.
- **Not done**: a mention in `docs/en/DEVELOPMENT.md` (done in batch 1.12.44).
- Files: `tests/ffmpeg_chemin.py` (new), `tests/zone_video.py`, `tests/zone_video_liste.py`, `tests/tout.py`, `.gitignore`.

### 21/11/2026: actions on `video` screens: link, portal, command (batch 1.12.42)

- **Request** (Klaatou): a `video` screen can carry a link, a portal or a Home Assistant command; the video shows what the action opens.
- **Done**:
  - `video` accepts one action among `link`, `portal`, `ha`; `video` with `radio` or `music` stays refused (`combo` message), like `mesh` with `radio` or `music`.
  - **`link`**: the title becomes a clickable segment of the bar under the screen (underlined, with a drawn arrow, never colour); title = the zone `label`, otherwise the video name; the bar also exists for a single video (title only, without the three icons); with a list, the "2/4" counter stays in front of the title and the three icons do not change; `frame: true` opens the floating window; a click on the screen stays pause / play.
  - **`portal` and `ha`**: the action fires **when you walk up to the screen** (the E key stays inactive on a screen); new key **`actionRadius`** (metres, 2 by default, 0.5 to 50); `radius` keeps its meaning (playback range). Same height band as the boards (`boardReach`). A missing video file hides the screen but does not remove the action.
  - `trigger` and `cone` (with `video`) and `actionRadius` (with `link`) are reported as ignored; a screen never has a cone (`coneAuto` / `cone_auto` leave out `video`).
  - internal keys `act` (`url`, `portal`, `ha`), `atarget`, `aradius`; `cleanZone` / `clean_zones`, `zoneIn` / `zone_in` and `zoneOut` / `zone_out` stay exact mirrors.
  - viewer: "Screen action" menu (none, link, portal, command) with its fields and the trigger distance.
- **Checked**: `tests/zones_unifiees.py` (Python and JavaScript cases, round trip of the old format, a screen with a portal teleports within `actionRadius` and not at the playback range); `tests/zone_video_liste.py` (title link of a single video and of a list, click on the title, rest of the bar and click on the screen unchanged); new `tests/editeur_video_action.py` (viewer form, reverse direction, generated page and zones file). All three fail without the fix. `i18n`, `dist_a_jour`, `samples`, `zone_video`, `zone_model`, `zones_url_cone`, `zone_cast`, `zone_audio`, `editeur_cone`, `fenetre_son`, `arbitrage_son`, `image_zone`, `pose_promenade`, `v32`, `v36_viewer_lang`, `zone_frame`, `smoke` pass. Not tested here: Edge, Windows, touch.
- **Not done**: documents (`REFERENCE_JSON.md`, manual, procedures, histories) at Klaatou's validation.
- Files: `src/core.js`, `src/gen_tpl.py`, `src/viewer_tpl.html`, `src/i18n/fr.json`, `src/i18n/en.json`, `tests/zones_unifiees.py`, `tests/zone_video_liste.py`, `tests/editeur_video_action.py`.

### 21/11/2026: `cone` defaults to `false` in the unified format (batch 1.12.41)

- **Request** (Klaatou): no more mixture; the cone is no longer switched on by default for some kinds only; it has to be asked for.
- **Done**:
  - unified format: without the `cone` key there is **no cone** for every kind (radio, music, portal, or any zone with an `enter` or `both` trigger); `"cone": true` switches it on. `zoneIn` / `zone_in` always give a boolean; `zoneOut` / `zone_out` write the key only when it is true.
  - old format (a `type` key): read as it is, with the previous behaviour (cone by default for portal, radio, music and any trigger other than `click`). **An old zone opened then saved by the viewer** keeps its look: `zoneOut` writes `"cone": true` where the old default switched the cone on (`coneAuto` in JS, `cone_auto` in Python, exact mirrors of `coneFor`).
  - viewer: a zone you place has `cone: false`; the "automatic / always / never" choice stays (for zones of the old format).
  - sample `region.zones.sample.json`: `"cone": true` added to the three portals and the radio, which keep their cone.
  - the cone stays the click target of a radio or music zone with no visual: without it (new default), the Sound window opens with ▲ in the State window or through a clickable model or board.
- **Checked**: `tests/zones_unifiees.py` (default in Python and JavaScript, old format written explicitly, round trip compared with the former cone made explicit); `tests/zone_model.py` (zones placed from the viewer: cone false, nothing written). Each new check fails without the fix. `samples`, `zones_url_cone`, `zone_cast`, `zone_audio`, `editeur_cone`, `fenetre_son`, `arbitrage_son`, `image_zone`, `pose_promenade`, `v32`, `v36_viewer_lang`, `zone_video` pass.
- **Not done**: documents (`REFERENCE_JSON.md`, manual, procedures) await Klaatou's approval.
- Files: `src/core.js`, `src/gen_tpl.py`, `src/viewer_tpl.html`, `docs/samples/region.zones.sample.json`, `tests/zones_unifiees.py`, `tests/zone_model.py`.

### 21/11/2026: the model of a radio or music zone is clickable (batch 1.12.40)

- **Request** (Klaatou): clicking the model of a radio (`radio.glb`) did nothing; only the cone opened or closed the Sound window.
- **Cause**: in 1.12.39, `mdlReady` (`src/core.js`) left `cast` and `audio` out of a model's click targets, copying the rule of a radio zone without a model (`clickable`, whose only target is the cone).
- **Done**: the meshes of the model of a radio (`radio`) or music (`music`) zone are click targets; the click calls the same handler as the cone (opens or closes the Sound window, in range only). The `enter` trigger still has no click for `link`, `portal` and `ha`. A radio or music zone without a model is unchanged (the cone stays its only target).
- **Checked**: `tests/zone_model.py`: two cases added (click on the model of a radio zone, then of a music zone); both fail without the fix and pass with it; `zones_unifiees`, `zone_cast`, `zone_audio`, `image_zone` pass.
- Files: `src/core.js`, `tests/zone_model.py`.

### 21/11/2026: `model` zone, a separate .glb file (batch 1.12.39)

- **Request** (Klaatou): place a small `.glb` (a radio set where a radio zone is, for example) with independent position, rotation and size, with an optional collision, and a loading that can be switched off.
- **Done**:
  - key `model`: a fourth "what you see" (with `image`, `video`, `mesh`); the file is looked up like an image (relative to the region folder, or a full address);
  - settings: `x`, `y`, `z` (or `pos`) = origin of the `.glb`; `yaw` (existing), `pitch` and `roll` (radians, like `yaw`; shown in degrees in the viewer); `scale` (0.01 to 100, 1 by default); `solid: true` (the model cannot be walked through);
  - `model` alone is a decoration (no radius, marker or name: `radius`, `showName`, `cone` are reported); with `link`, `portal`, `ha`, `radio` or `music` it carries the action (clickable like a board, cone, trigger when walking in, a radio set standing on a radio zone);
  - `solid`: the model triangles are added to the walking collision grid (ground and walls) and its meshes to the teleport (double click) and click occlusion rays; the landing marker and zone placement in the viewer ignore it;
  - on-demand loading: a model loads when the visitor (or the camera outside walking) is within `modelLazy` meters of its zone (150 by default, option `--model-lazy M`, config key `modelLazy`); **`0` = all loaded at start, no cap** (switches on-demand loading off); otherwise at most 16 models at a time (the farthest is released), 2 loads at a time; in the viewer everything loads;
  - measured in the sandbox (software Chromium, local server, **estimate** for a real network): 30 models of 20 KB, 0.8 MB and 9 MB, 8 of them near: on demand 6 loaded in 1.8 s and 42 MB of JavaScript memory, `--model-lazy 0` 30 loaded in 20 s and 110 to 130 MB; the page is ready in 0.4 s in both cases;
  - a missing or unreadable file leaves nothing in the page and writes a warning in the console (no error); page opened from disk (`file://`): the browser refuses the read, as for track lists;
  - viewer: "3D model" type in the list, fields file, size, tilt forward / back, tilt sideways, solid; the "model file" field also exists on the link, portal, command, radio and music sheets; the zone is written in the file format (`model`, `scale`, `pitch`, `roll`, `solid`);
  - exact mirrors: `zoneIn` / `zoneOut` / `cleanZone` (`src/core.js`) and `zone_in` / `zone_out` / `clean_zones` (`src/gen_tpl.py`); internal keys `mdl`, `mscale`, `pitch`, `roll`, `solid`; internal type `model` for a model without an action.
- **Checked**: new test `tests/zone_model.py` (loading, size, heading, pitch, roll, `pos` position, model at 1 km not loaded, missing file, click on a model with a link, solid stops the visitor and the model without `solid` does not, `--model-lazy 0`, cap of 16 out of 20 near models, viewer); removing the `solid` walls on purpose makes the test fail; `zones_unifiees.py` extended (six cases, Python and JavaScript identical); `samples.py` (sample `statue` zone and `modelLazy` key); `i18n`, `dist_a_jour`, `build_reference`, `smoke`, `paquets`, `image_zone`, `zone_frame`, `zone_video`, `zone_video_liste`, `zone_cast`, `zone_audio`, `zone_pochette`, `zone_apercu`, `zone_distance`, `zones_url_cone`, `zones_numeros`, `lien_image`, `image_noms_gen`, `editeur_cone`, `tuiles`, `tuile_ici`, `pose_promenade`, `portail_interne`, `yaw_etat`, `v32`, `v34`, `v35`, `v36`.
- **Not done**: documents (`REFERENCE_JSON.md`, manual, procedures, histories) when Klaatou validates; `docs/REFERENCE_OPTIONS.md` is regenerated by `python build.py` on Klaatou's machine (option `--model-lazy`).
- Files: `src/core.js`, `src/gen_tpl.py`, `src/viewer_tpl.html`, `src/i18n/fr.json`, `src/i18n/en.json`, `tests/zone_model.py`, `tests/zones_unifiees.py`, `tests/samples.py`, `docs/samples/region.config.sample.json`, `docs/samples/region.zones.sample.json`.

### 21/11/2026: `pos` key for a zone position (batch 1.12.38)

- **Request** (Klaatou): paste into `zones.json` a coordinate copied from the H window as is, with the syntax of `config.json` (`"target": [0, 13, 7]`).
- **Done**:
  - key `pos`: `[x, y, z]`, another way to write `x`, `y`, `z`; with both, `pos` wins and a message says so; a list that is not three numbers is ignored and reported (`zoneIn` in `src/core.js` and `zone_in` in `src/gen_tpl.py`, exact mirrors, messages `posboth` and `posbad`);
  - read only: the viewer and `glb2html.py` still write `x`, `y`, `z`, existing files stay valid;
  - "Copy my position": new `[x, y, z]` (JSON) format, next to `URL` and `xyz` (unchanged).
- **Checked**: `zones_unifiees.py` (pos alone, pos with x, y, z, invalid pos, arrival with pos; JavaScript and Python identical), `v36.py` (copied format, remembered).
- **Documents**: `REFERENCE_JSON.md` § 11.4, manual (copied position), procedures, FR and EN histories.
- Files: `src/core.js`, `src/gen_tpl.py`, `src/template.html`, `src/i18n/fr.json`, `src/i18n/en.json`, `tests/zones_unifiees.py`, `tests/v36.py`, documents above.

### 21/11/2026: end of the unified zones (batch 1.12.36)

- **Request** (Klaatou): finish the unified zones; keep the small script that adapts old zone JSON files, for the few creators who made their own.
- **Done**:
  - a picture (`image`) combines with `portal`, `ha`, `radio` or `music`: it becomes the portal, the command, the radio or the music; no ground marker; `radius` and `trigger` work as for a ring (portal on approach); internal key `pic` (exact mirrors `zoneIn`/`zoneOut` and `zone_in`/`zone_out`, lossless round trip);
  - without `poster`, the picture is the cover in the Sound window;
  - viewer: a « board picture » field in the portal, command, radio and music sheets;
  - still refused, with a message: a video screen with an action, an object of the model with radio or music;
  - the adaptation script `python glb2html.py --convert-zones FILE` (delivered in 1.12.35, original kept as `.bak`) is the one to give to creators with their own zones; it is described in `REFERENCE_JSON.md` § 11.4 and manual § 5.
- **Checked**: `zones_unifiees.py` (new picture + portal / command / radio / music cases, Python and JavaScript identical, picture-portal fires when walking into the circle), `image_zone.py`, `zone_frame.py`, `lien_image.py`, `image_noms_gen.py`, `paquets.py`, `samples.py`.
- **Not done**: placing a separate `.glb` file (`model`).
- **Documents**: `REFERENCE_JSON.md` § 11.4, manual § 5.11 and annex, FR and EN histories.
- Files: `src/core.js`, `src/gen_tpl.py`, `src/template.html`, `src/viewer_tpl.html`, `src/i18n/fr.json`, `src/i18n/en.json`, `tests/zones_unifiees.py`, documents above.

### 21/11/2026: unified zone format (batch 1.12.35)

- **Request** (Klaatou): simplify the zones ("not a gas factory"); compatibility with the old format is only required for the zones of the published packages.
- **Done**:
  - a zone is described by what is shown (`image`, `video`, `mesh`, otherwise a ring or a sign with `shape`) and what happens (`link`, `portal`, `ha`, `radio`, `music`); `arrival` for an arrival point; no more `type` or `target`; each key has a single meaning (the cover link of a radio or music becomes `posterLink`, the videos folder `videoFolder`);
  - reading: `zoneIn` (`src/core.js`, in `setZones`: page, shell, reloaded zones, viewer) and `zone_in` (`src/gen_tpl.py`, in `clean_zones`), exact mirrors; the old format is still read as is (it is the internal format: keeping it costs nothing);
  - writing in the new format everywhere: `glb2html.py` (`NOM.zones.json`, reloaded zones), viewer (zones export, saving in the region folder, modular export, `.reglages.json` file); default settings are not written;
  - messages: unknown key, key that does not apply to this zone, two things to show, two actions, combination not possible yet (picture with an action other than a link, video screen with an action, object of the model with radio or music), empty zone; shown by `glb2html.py`, by the viewer on import, in the console for the page;
  - `glb2html.py --convert-zones FILE`: rewrites a list of zones or a `.reglages.json`, the original in `FILE.bak`;
  - picture hung high: it can be reached when the feet are between 4 m below its bottom edge and 0.5 m above its top edge (before: 3.5 m around its centre, a high picture could not be reached);
  - samples (`docs/samples`), zones of the packages (galerie-photos, region-simple) and their notes in the new format.
- **Checked**: new test `zones_unifiees.py` (Python and JavaScript identical zone by zone and message by message, round trip of each old-format type, `glb2html.py` reads, reports and writes the new format, `--convert-zones` on a list and on a settings file, high picture reachable and counter-test: fails with the old height rule); full test run.
- **Not done** (next batch): the new combinations (picture that plays music, picture-portal…) and the cover taken from the picture's image; placing a separate `.glb` file (`model`).
- **Documents**: `REFERENCE_JSON.md` § 11.4 rewritten (tables by part, combinations, old format and correspondence), JSON examples converted; manual (note in § 5, § 5.11, § 5.19 to § 5.21, § 10.25, annex); index, overview, procedures, creators, `docs/samples/README`; FR and EN.
- Files: `src/core.js`, `src/gen_tpl.py`, `src/template.html`, `src/viewer_tpl.html`, `src/i18n/fr.json`, `src/i18n/en.json`, `tests/zones_unifiees.py`, `docs/samples/*.json`, `paquets/*/site/*.zones.json`, package notes, documents above, `dist\`.

### 21/11/2026: an image board opens its link in the floating window (batch 1.12.34)

- **Request** (Klaatou): an image that opens the YouTube mini player (the `poster` key of a `url` zone is ignored: it only serves radio and music zones).
- **Done**: an `image` zone with `link` accepts `"frame": true`; a click or E opens the link in the floating window, with the same rules as a `url` zone (YouTube, playlists, fallback to a new tab for `hop://`, mixed content and same origin). The key is only written when true, for `url` and `image` (`cleanZone` and `clean_zones`). A board with `link` also keeps its `trigger` (`"enter"`, `"both"`: the link opens when walking in front of the board, within its `radius`, at the height where the "click or E" prompt appears); before, it was forced to `"click"`. New box "Open in a floating window of the page" and trigger choice in the sheet of a board in the editor. Without `frame` or `trigger`, nothing changes.
- **Checked**: `lien_image.py` (board with `frame`: E opens the YouTube player, no tab; `"enter"` board: the window opens when walking in front, fails without the height fix) and `zone_frame.py` (key kept for `url` and `image`, Python and JavaScript identical); `dist\` rebuilt.
- **Documents**: manual § 5.7.1 and § 5.11 (board link), `REFERENCE_JSON.md` (`frame`), annex, FR and EN histories.
- Files: `src/core.js`, `src/gen_tpl.py`, `src/template.html`, `src/viewer_tpl.html`, `tests/lien_image.py`, `tests/zone_frame.py`, `dist\`, documents above.

### 21/11/2026: full check of the documents against the code (batch 1.12.33)

- **Request** (Klaatou): check everything and update everything, in French and in English.
- **Checked against the code**: zones table (`cleanZone`, `clean_zones`), command-line options of all the tools (old names included), section cross-references, cited files, configuration keys (`build_cfg` and `REFERENCE_JSON.md` § 11.3), cited interface labels (`fr.json`, `en.json`), keys, presence server defaults, `localStorage` keys, paths cited in `DEVELOPMENT.md`, `GUIDE.md` and `PROCEDURES.md`.
- **Corrected**: `REFERENCE_JSON.md` § 11.9 named neither the Sound window (`S`) nor the keys `glb2html_sound`, `glb2html_soundFold`, `glb2html_soundW`, `glb2html_padPos` that the layout file stores; manual § 7.66: new bullet listing what the page keeps in the browser (so far missing from the documents).
- **Left as is**: the configuration keys `landingMarker`, `metalEnv`, `roomDefault` and `imageBase` are set by no generator option (page setting or internal value); they do not belong in `REFERENCE_JSON.md`.
- Files: `docs/fr/REFERENCE_JSON.md`, `docs/en/REFERENCE_JSON.md`, `docs/fr/MANUEL.md`, `docs/en/MANUAL.md`, `docs/fr/HISTORIQUE.md`, `docs/en/HISTORY.md`, `CHANGELOG.fr.md`, `CHANGELOG.md`, `VERSION`.

### 21/11/2026: documents brought up to date for batches 1.12.16 to 1.12.31, histories put back in order (batch 1.12.32)

- **Request** (Klaatou): check all the documents and catch up on what was missing, keeping chronological order where it matters.
- **Finding**: (a) `HISTORIQUE.md` and `HISTORY.md`: the lines of batches 1.12.15 to 1.12.26 were in reverse order (each line had been inserted at the same place) and batches 1.12.27 to 1.12.31 were missing; (b) manual annex (§ 13): sound arbitration (batch 1.12.21) was filed under "1.11.24 to 1.11.29" and nothing described the batches after 1.12.15; (c) manual § 10: no section on private messages on the server side (`--no-dm`, `dm` message, `k` key); (d) README, overview, index, guide and procedures said nothing about the Sound window, sound arbitration (N key), video screens (overview, index) or private messages, and the overview showed "version 1.12.0"; (e) `CONVERT_OARS.md`: the messages of batch 1.12.27 were described nowhere; (f) two statements that had become false: manual § 5.20 ("the stronger one wins" between radio and music, replaced by the source nearest in metres in batch 1.12.25) and § 7.25 (`--history` "20 by default": 200 since v37); `SIMPLE_PROCEDURES.md` § 15 (two boxes that exclude each other: three since batch 1.12.21) and § 14 (cover and link of batch 1.12.26 missing).
- **Done** (documents only, no code): FR and EN histories put back in batch order with the lines 1.12.27 to 1.12.32; manual annex (§ 13): the sound arbitration bullet put back in its place, new block "1.12.16 to 1.12.32"; manual § 7.25 (click on the avatar, line replayed from the history) and new § 10.27 (`--no-dm`, `dm` / `dmerr` protocol, `k` key, personal data); README FR and EN (N key, Sound window, sound arbitration, private messages, server); overview (state on 21/11/2026, video screens, link in a floating window, one sound source, private messages, Klaatou's tries); index (four entries); guide § 5; procedures § 6 (item 10); `SIMPLE_PROCEDURES.md` § 14 and § 15; `CONVERT_OARS.md` (messages of batch 1.12.27); manual § 5.20 and § 7.25 (two statements corrected). Every modified document is modified in both languages.
- **Checked**: `verif_trad.py` on each modified pair (same number of errors as before the batch); section numbers cited re-read in the manual; patch anchors unique; nothing in `dist\` changes.
- **Not done, agreed with Klaatou**: `REPRISE.md` (delivered separately, rule 23).
- Files: `docs/fr/HISTORIQUE.md`, `docs/en/HISTORY.md`, `docs/fr/MANUEL.md`, `docs/en/MANUAL.md`, `README.fr.md`, `README.md`, `docs/fr/VUE_ENSEMBLE.md`, `docs/en/OVERVIEW.md`, `docs/fr/INDEX.md`, `docs/en/INDEX.md`, `docs/fr/GUIDE.md`, `docs/en/GUIDE.md`, `docs/fr/PROCEDURES.md`, `docs/en/PROCEDURES.md`, `docs/fr/PROCEDURES_SIMPLES.md`, `docs/en/SIMPLE_PROCEDURES.md`, `docs/fr/CONVERTIR_OARS.md`, `docs/en/CONVERT_OARS.md`, `CHANGELOG.fr.md`, `CHANGELOG.md`, `VERSION`.

### 21/11/2026: private messages, click on the avatar or its name (batch 1.12.31)

- **Request** (Klaatou): clicking a name in the chat did not work in his try; a click on the avatar or its name would be useful, with a confirmation against accidental clicks.
- **Finding**: clicking a chat name works in the test with a real mouse (Chromium); a likely cause in his try: for a message **replayed from the history**, the visitor's id is no longer today's and the click ended with "is no longer here". **Fixed**: the visitor is then found by name. If the defect remains after this batch, describe what is displayed (message, window, nothing).
- **Done**: single click on the avatar, its name or its bubble in the scene (`core.js`, `peerFromClick`, `viewer.onPeerClick`): the page asks "Send a private message to X?" (Yes / No, disappears by itself after 10 s) and opens the window only after "Yes". A double click is still the teleport (the single click only acts after 350 ms without a second click); a visitor hidden behind a solid element is not reached; without DMs on the server the click does nothing; an ignored visitor opens nothing. `getPresence().peers[].screen` gives the on-screen position (tests). Clicking a chat name stays direct, without confirmation.
- **Tests**: `tests/presence_mp_page.py` extended (avatar click: question, No, Yes).
- Files: `src/core.js`, `src/template.html`, `src/i18n/fr.json`, `src/i18n/en.json`, `tests/presence_mp_page.py`, `docs/fr/MANUEL.md`, `docs/en/MANUAL.md`, `CHANGELOG.fr.md`, `CHANGELOG.md`, `VERSION`.

### 21/11/2026: private messages between walkers, page side (batch 1.12.30)

- **Request** (Klaatou): follow-up to batch 1.12.29: one floating window per conversation, "Ignore", local save; closing a window does not delete its text; the in-page archive has no limit while the page is displayed.
- **Finding**: the `k` key was only published with DMs; without it in the public data (`welcome`, `join`), "Ignore" could hide neither the public chat nor the bubbles. **Server** (`presence_server.py`): `Peer.public()` now carries `k` (truncated, non-reversible hash).
- **Done, page** (`core.js`, `template.html`): `core.js` handles `dm` and `dmerr` (`viewer.sendDM`, `onDM`, `onDMErr`, `setIgnored`, `dmOK`), knows each visitor's key, and shows neither chat line nor bubble of an ignored visitor. Page: one floating window per correspondent (draggable, minimized or closed without losing the text, at most 8 open), incoming DM = minimized blinking window (inverted header, no colour) without taking focus, click on a chat name, `/mp name message`, `/ignore name`, `/unignore name|all`, Save / Ignore / Ignored (n) buttons per window, ignore list kept in the browser (`web3d.ignore`). Everything is hidden (names not clickable, `/mp` refused) if the server does not offer DMs (`--no-dm`, older server).
- **Limits**: the history replayed on arrival is not filtered by "Ignore" (its old messages have no reliable key); a visitor without a persistent identifier is ignored only for the length of their connection.
- **Tests**: `tests/presence_mp_page.py` (minimized blinking reception without focus, reply and echo, closing without loss, click on a name, `/mp`, save with BOM, ignoring chat, bubble and DMs, persistence after reload, `/unignore`, `--no-dm` server). `tests/presence_mp.py` unchanged.
- **Not tried here**: Windows, Edge, touch.
- Files: `src/presence_server.py`, `src/core.js`, `src/template.html`, `src/i18n/fr.json`, `src/i18n/en.json`, `tests/presence_mp_page.py`, `docs/fr/MANUEL.md`, `docs/en/MANUAL.md`, `CHANGELOG.fr.md`, `CHANGELOG.md`, `VERSION`.

### 20/11/2026: private messages between walkers, server side (batch 1.12.29)

- **Request** (Klaatou): private messages between visitors, one floating window per conversation, an "Ignore" feature, local save of the logs. This first batch is the presence server and its protocol; the page comes next.
- **Done** (`presence_server.py`): new `dm` message `{t:'dm', to:id, text}`. The recipient gets `{t:'dm', id, name, k, text, ts}`; the sender gets the same message with `self:true` and the recipient's id, name and key. `k` is a short stable key of the visitor (hash of the internal identifier), published only with private messages, so that the page can ignore someone even if they change nickname (without a persistent `uid` it changes at each connection). A failure answers `{t:'dmerr', to, why}` with `why` = `off`, `rate`, `gone` (unknown, spectator, another room) or `self`. Rate limit of its own, same values as the chat (`--chat-gap`, `--chat-burst`). Walkers only: a spectator cannot send. Never broadcast, never kept in the history, never written to the console (only the event, sender -> recipient). New option `--no-dm`; the `welcome` message carries `dm` (true unless `--no-dm`), absent on an older server, so the page will hide the feature there.
- **Decisions** (Klaatou, 20/11/2026), for the next batches (page): closing a conversation window does not erase its text (it is shown again when the window is reopened); the archive of a conversation kept while the page is open has no size limit; one "Ignore" mechanism (by key, remembered in the browser: private messages, public messages and bubbles of that person); local save by a button, same text format as the chat save.
- **Tests**: `tests/presence_mp.py` (delivery and echo, bystanders, errors, invalid values, spectator, key stability, history, rate limit, `--no-dm`, console without the text). On 1.12.28 it fails at the first check.
- **Not tried here**: Windows, Edge, touch.
- Files: `src/presence_server.py`, `src/i18n/fr.json`, `src/i18n/en.json`, `tests/presence_mp.py`, `docs/REFERENCE_OPTIONS.md` (regenerated by the build), `CHANGELOG.md`, `CHANGELOG.fr.md`, `VERSION`.

### 19/11/2026: effect suggestions: blinking icon instead of the bubble (batch 1.12.28)

- **Request** (Klaatou): no more message forced on the screen ("This region contains 27 shiny materials… Turn on the reflections at 60 %?"); a blinking icon to offer it instead, with a selector.
- **Done** (`template.html`): the light rendering offer and the reflections offer go through `fxPropose`: by default an `#fxHint` icon (✦, the black and white blink of the "Walk" button, steady with reduced motion, tooltip) appears left of "Settings"; clicking it shows the Yes / No question(s), unchanged. Touching the reflections slider drops the pending offer. Settings > "Effect suggestions": blinking icon (default) or message right away; remembered in `glb2html_visitor` (`fxAsk`).
- **Tests**: `tests/reflets_metal.py` (section 9: icon, click, remembered "No", slider, selector, reload; sections 8 onward in message mode), `tests/v42.py` (goes through the icon). `v36_lang` and `v37` already failed before this batch in the sandbox.
- **Not tried here**: Windows, Edge, touch.
- Files: `src/template.html`, `src/i18n/fr.json`, `src/i18n/en.json`, `docs/fr/MANUEL.md`, `docs/en/MANUAL.md`, `tests/reflets_metal.py`, `tests/v42.py`, `CHANGELOG.md`, `CHANGELOG.fr.md`, `VERSION`.

### 19/11/2026: oars2site: convoar names with a trailing backslash and damaged OAR (batch 1.12.27)

- **Finding** (Klaatou): out of 195 regions, 5 failures. Three (`breakout-zone-oscc13-2013`, `knowledge-transfer-center`, `quest-for-illumination`): `invalid .gltf: Invalid control character`, because convoar writes `"name": "bench\",` (trailing backslash not doubled); one (`adult-dragonfyre-2023-update`): damaged archive, `zlib.error` traceback; one (`winterland`): convoar does not write a `.buf` (not handled here).
- **Done** (`tools/oar2glb.py`): `load_gltf` repairs, only when the normal read fails, text values ending in an odd number of backslashes (one added) and says so in the log; the pattern that doubles lone backslashes now consumes pairs (a name like `C:\\x` was no longer read correctly). `oar_scan` turns `zlib.error`, `EOFError` and `tarfile.ReadError` into an "the OAR is damaged" message (download or export again), no traceback.
- **Test**: `tests/gltf_barre_finale.py` (broken names, CRLF, valid file unchanged, truly invalid JSON, damaged, empty, truncated OAR).
- **Left**: `winterland` (`.buf` never written by convoar, exit code 0); to be decided.
- Files: `tools/oar2glb.py`, `src/i18n/fr.json`, `src/i18n/en.json`, `tests/gltf_barre_finale.py`, `CHANGELOG.fr.md`, `CHANGELOG.md`, `VERSION`.

### 19/11/2026: samples: cover and link on the radio zone (fix of batch 1.12.26, no version change)

- **Finding** (Klaatou): `poster` and `link` were only on the sample `audio` zone, not on the radio zone.
- **Done**: `dance-floor` (`cast`) carries `poster` and `link` in `docs/samples/region.zones.sample.json` and in the `REFERENCE_JSON.md` example (FR and EN); the two sample `README` files say so. `tests/samples.py` passes (the cleaning keeps the keys).

### 19/11/2026: manual: cover and link of radio and music zones (documentation of batch 1.12.26, no version change)

- **Request** (Klaatou): the help docs to try a cover on a `cast` zone.
- **Done**: § 5.19 (`cast`) and § 5.20 (`audio`) of the manual, in French and English: `poster` and `link` keys, viewer fields, hand-written example in `NOM.zones.json`. Files: `docs/fr/MANUEL.md`, `docs/en/MANUAL.md`.

### 19/11/2026: cover and link of radio and music zones (batch 1.12.26)

- **Request** (Klaatou): a cover in the Sound window for the radio and music that are playing, with an optional link.
- **Done**: `cast` and `audio` zones accept `poster` (image: name relative to the region or `http(s)` address, extension included) and `link` (`http(s)` or `hop://` address, 600 characters at most); the keys are only written when filled in. The Sound window shows the cover (96 px at most, 128 on touch) of the source that is speaking, above the lines; with `link`, a click or Enter opens the page in a new tab (`hop://` in the tab); without a link the cover is not clickable; image not found or zone without a cover: nothing. Viewer: "Cover" and "Cover link" fields for radio and music.
- **Mirror**: `cleanZone` (`core.js`) and `clean_zones` (`gen_tpl.py`) write the same keys; `poster` and `link` are ignored for the other kinds.
- **Not tried here**: Windows, Edge, real touch. No 3D panel (later).
- Files: `src/core.js`, `src/gen_tpl.py`, `src/template.html`, `src/viewer_tpl.html`, `src/i18n/fr.json`, `src/i18n/en.json`, `docs/fr/REFERENCE_JSON.md`, `docs/en/REFERENCE_JSON.md`, `docs/samples/region.zones.sample.json`, `tests/zone_pochette.py`, history, `VERSION` `1.12.26`. Still to update: manual (§ 5.19 and 5.20).

### 19/11/2026: the nearest source in metres speaks (batch 1.12.25)

- **Finding** (Klaatou): (1) after his tests of the YouTube window, the screen no longer takes over from the radio when he approaches it; after F5, it does; (2) nose on the radio, the screen 14 m away is the one speaking.
- **Causes** (`template.html`): (1) ticking a source, choosing a stream or skipping a track makes it the priority (1.12.22), and the priority lasts while its zone is in range: the wide radio kept it; (2) 1.12.22 always gave the floor to the playing screen (gain + 1), without looking at the distance.
- **Done**: the source nearest **in metres** speaks (the gain compared different ranges); when a screen with sound comes into view (new talker in `onVideoTalk`), the stuck priority is cleared; a gesture then sets it again.
- Files: `src/template.html`, `tests/arbitrage_son.py`, manual (§ 5.22), history, `VERSION` `1.12.25`.

### 19/11/2026: the floating window no longer keeps the keyboard (batch 1.12.24)

- **Finding** (Klaatou, `tests/zone_frame.py`): "other https zone: a single window" fails on his machine, never here (YouTube is unreachable here); the diagnostic line added to the test gives `IFRAME` for the focused element.
- **Cause** (`template.html`, `frameOpen`): the real YouTube player takes the keyboard focus when it loads; keys (E, and walking) then go to the iframe instead of the page.
- **Done**: when the iframe has finished loading, then 0.3, 0.8, 1.5 and 3 s later, the page takes the focus back if the iframe holds it; a click in the player gives it back to the player afterwards.
- **Limit**: focus taken more than 3 s after loading is not taken back; to be tried on a real player by Klaatou (`zone_frame.py` and walking with the window open).
- Files: `src/template.html`, `tests/arbitrage_son.py`, manual (§ 5.7.1), history, `VERSION` `1.12.24`.

### 19/11/2026: YouTube player and mute button icon (batch 1.12.23)

- **Finding** (Klaatou, trying 1.12.22): the two speaker icons (mute and volume) are identical when the sound is not muted; the YouTube player of the window no longer starts by itself and no longer handles its playlist.
- **Cause** (`template.html`, `ytEmbed`): 1.12.22 had added `enablejsapi=1` to the player address line with a `//` comment in the middle of the line: the rest (`list`, the playlist, and `autoplay`) had become a comment.
- **Done**: line restored, `enablejsapi` removed and the pause request with it (the page cannot stop the player: a gesture on a source takes over for the radio, the music and the screens, and the YouTube video keeps playing); the mute button always draws a cross on the speaker and turns to a black background while muted.
- Files: `src/template.html`, `tests/arbitrage_son.py`, manual (§ 5.22), history, `VERSION` `1.12.23`.

### 19/11/2026: sound arbitration fixes (batch 1.12.22)

- **Finding** (Klaatou, trying 1.12.21): the screen with sound does not take over from the radio; after a click on the screen, the radio line and stream choice disappear; no crossed speaker button; the YouTube window does not silence the radio; a page other than YouTube has no reason to cut the sound.
- **Causes** (`template.html`): (1) the "strongest gain" rule compares different ranges: a wide-range radio won even 5 m from a screen; (2) the arbitration gave `null` to the source that does not speak, so its line and stream choice disappeared (the manual said they stayed); (3) the button had the `sndV` class, hence the same position as the volume button, under it; (4) the iframe is in the page only after `load()`: `srcRefresh()` did not see it, only the video (re-read continuously) went quiet; (5) any iframe cut the sound.
- **Done**: a playing screen with sound goes ahead of the radio and the music (a visitor gesture still wins); the source that does not speak keeps its line ("another source is speaking"), its stream choice and ⏮ ⏭; mute button at `right:70px`; `srcRefresh()` also after the window is added to the document; only a YouTube page silences the sources, and a gesture on a source (box, stream, track, screen) brings it back, with a pause request to the player (`enablejsapi`, not tried); "sound muted: N key or YouTube window" texts.
- Files: `src/template.html`, `src/i18n/fr.json`, `src/i18n/en.json`, `tests/arbitrage_son.py`, manual (§ 5.22), history, `VERSION` `1.12.22`.

### 19/11/2026: one sound source at a time, mute button, N key (batch 1.12.21)

- **Request** (Klaatou): music, radio, video sound and YouTube must no longer overlap; a mute button for videos too, in the Sound window.
- **Done** (`template.html`, `core.js`): one arbitration for the radio, the music and the video screen sound (the nearest speaks; a visitor gesture wins: chosen stream, next or previous track, click on a screen); `core.js` reports the nearest screen with sound (`onVideoTalk`) and the visitor's click (`onVideoAct`) to the page; "Zone videos" box (Settings and Sound window), exclusive with the other two; "Video" line in the Sound window; mute button (crossed speaker) and N key; a floating window that loads a page silences the three sources (the sound of an iframe cannot be controlled).
- **Limits**: pausing a YouTube video of the window is not tried; two real screens with a real radio together are not tried.
- **Check**: new `tests/arbitrage_son.py`; `fenetre_son`, `zone_video`, `radio_flux`, `zone_cast`, `touche_b`, `chat_replie` and `i18n` pass again.
- Files: `src/template.html`, `src/core.js`, `src/i18n/fr.json`, `src/i18n/en.json`, `tests/arbitrage_son.py`, manual (§ 5.22, § 7.66, N key), history, `VERSION` `1.12.21`.

### 18/11/2026: B key without effect after a sent message (batch 1.12.20)

- **Finding** (Klaatou): at times the B key does nothing, the chat block does not move, while the chat works; no other visitor; `--idle-walk` at 0; the time the page has been open is not the cause.
- **Cause** (`template.html`, the chat key handler): after sending with Enter, the input stays open; a click on the scene takes the focus away from the field (`core.js`, `blur`) without closing the input (`inp.hidden` stays false). Enter, Esc and B required `inp.hidden` or the focus in the field: none of them could act any more. Reproduced in a test browser: message sent, click on the scene, B without effect.
- **Fix**: input open without focus: **Enter** gives it the focus back, **Esc** closes it, **B** closes it and folds the block. Nothing changes when the field has the focus or the input is closed.
- **Check**: new `tests/touche_b.py` (send, click on the scene, B, Enter, Esc; B after choosing a radio stream, after walking).
- `VERSION`: `1.12.20`.

### 18/11/2026: README brought up to date (multimedia zones)

- **`README.fr.md` and `README.md`**: the feature list adds video screens and floating-window links; the Zones section only mentioned pictures, it now lists radio, music, video and floating window, with the manual references (§ 5.7.1, 5.19 to 5.21).
- No code touched: `dist\` does not change. `VERSION`: `1.12.19`.

### 18/11/2026: manual § 5.19 to 5.21: dense bullets split into sub-lists; radio tried on a phone

- **Requested by Klaatou**: the very dense bullets of the radio, music and video zones in the manual are split into sub-lists.
- **`MANUEL.md` and `MANUAL.md`** (§ 5.19, 5.20, 5.21): each bullet of more than 420 characters keeps its first sentence (the bold title) and moves its following sentences to sub-bullets; the "three cases" of the radio that does not play and the two ways of redoing `playlist.json` (**(1)**, **(2)**) become second-level sub-bullets. The text is not changed, only split.
- **Tried** (§ 5.19): a tester tried, on a phone, the region with the several-stream radio, stream changes included: everything works (model and browser not recorded).
- No code touched: `dist\` does not change. `VERSION`: `1.12.18`.
### 18/11/2026: more readable lists in the documents

- **Requested by Klaatou**: the cell of the examples `README` that lists the zones was unreadable (and a comma had been missing before "radio" since batch 1.12.16).
- **`docs/samples/README.fr.md` and `README.md`**: the `region.zones.sample.json` cell is short; a section "The zones of the sample" gives the list, one line per kind, with the `id`s.
- **Manual appendix** (§ 13, `MANUEL.md` and `MANUAL.md`): the "Version / What it brought" table (cells of 10 to 18 items separated by semicolons) becomes, per version, a bold title followed by a list. Same content, same pointers; the introductory sentence says "the list" instead of "the table".
- **Not touched**: the long cells that describe one single option (`--reencode`, `--update`, F key): they are explanations, not enumerations.
- No code touched: `dist\` does not change. `VERSION`: `1.12.17`.
### 18/11/2026: multimedia zone examples (JSON) and sample file brought up to date

- **Requested by Klaatou**: JSON block examples with all the parameters of the multimedia zones.
- **`REFERENCE_JSON.md`** (FR and EN, § 11.4): eight complete examples (video screen with one file and sound, with a list read from a folder, with `tracks`; music with a folder, with `tracks`; radio with several `streams`; picture with `link`; link with `frame`), each under a title (JSON has no comments: the title and the `id` say what it shows). The sample table goes to fourteen zones.
- **`docs/samples/region.zones.sample.json`**: 14 zones. **Updated**: the `dance-floor` radio uses `streams` (it still had the old `target` key); **added**: `ambiance` (`audio`), `screen-clip` and `screen-list` (`video`), `video-page` (`url` with `frame`). The file is written by `clean_zones`, so it is identical to what the page writes. `tests/samples.py`: 13 public zones instead of 9.
- **Finding**: on `main`, three checks of `tests/samples.py` were already failing (zones "already clean", "one zone of each kind", `perso` profile) because the sample had stayed at the 1.10.35 state; they pass with this batch.
- No code touched: `dist\` does not change. `VERSION`: `1.12.16`.
### 18/11/2026: documents of batches 1.12.3 to 1.12.14 (link zones in a floating window, video screens)

- **Requested by Klaatou**: bring the documents that have been behind since batch 1.12.3 up to date in one go.
- **`REFERENCE_JSON.md`** (FR and EN, § 11.4): eight kinds of zones; type `"video"`; `radius`, `w`, `h`, `target` for the video screen; `folder` and `tracks` valid for `video`; new keys `sound` and `frame`; `cone` has no effect on a video screen.
- **Manual** (`MANUEL.md`, `MANUAL.md`): § 5.7.1 (floating window, `frame` key, YouTube and lists, cases without a frame, **known limit: Edge without hardware acceleration may leave a ghost rectangle**); new § 5.21 (`video` zone: file, playback, click, sound, lists, `--video-list`, track bar, radio and music in the overview, diagnostic, tried and not tried); appendix (§ 13): line for batches 1.12.3 to 1.12.15.
- **`PROCEDURES_SIMPLES.md`** (FR and EN): new § 17 "Put a video screen in a region"; § 16 step 3: pointer to § 17. `VUE_ENSEMBLE.md` and `OVERVIEW.md`: video on a screen is no longer an idea.
- **Histories** (`HISTORIQUE.md`, `HISTORY.md`): one line per batch, 1.12.3 to 1.12.15.
- No code touched: `dist\` does not change. `VERSION`: `1.12.15`.
- **Still to update**: `REPRISE.md` (when Klaatou asks, rule 23).

### 18/11/2026: video screens: sound no longer falls back to muted at a track change

- **Reported by Klaatou**: on a playlist screen, the sound came about 2 s after the picture at each track change (the Diagnostic said "sound requested but muted").
- **Cause**: a fallback guessed from the element's "paused" state muted the sound for 5 s whenever a track changed, because loading a new track briefly puts the element in the paused state.
- **Fix**: that fallback is removed. The sound is muted only when the browser really refuses playback with sound (`NotAllowedError`): the screen then plays muted and the sound is retried 5 s later.
- Tests: end of track and previous / next icons keep the sound; simulated browser refusal. A real Edge refusal is not tested here.

### 18/11/2026: video screens: retractable track bar (icons); sound set before playback starts

- **Request from Klaatou**: icons to move through the videos of a list, on a retractable status line under the screen; and the sound started a little late.
- **Track bar**: under a screen with a **list of several tracks**, a black bar as wide as the screen shows "2/4 name" and three drawn icons (no characters, so no font dependency): previous, pause / play (the icon follows the state), next. It is **retracted**: visible while the mouse hovers the screen or the bar, while the walking crosshair (captured pointer) is on the screen, and 3 seconds after every click or track change. A click on the bar's text does nothing. A single-file or one-track screen has no bar: a click on the screen stays pause / play.
- **The clickable edges of 1.12.12 are removed**: a click on the screen, edges included, is always pause / play. The tooltip of a list mentions the bar.
- **Sound**: it was applied at the next playback decision (up to ~150 ms after the muted start); it is now computed for every screen at each decision and applied right before the first `play()` of each track. Cause established by measurement: without this, the three starts of the test were muted.
- Tests: `tests/zone_video_liste.py` (bar: hover, retracting, icons, text, 3 s delay, no bar on a single file) and `tests/zone_video.py` (sound before start).

### 18/11/2026: video zones, step 3: video playlists, previous / next

- **Request from Klaatou**: a list of videos for one screen, like the sound files of an audio zone, with previous / next.
- **`folder` and `tracks` keys** on a `video` zone **without `target`**: `tracks` is the list written in the zone; without it the list is the file `<folder>/playlist.json` (array of names or `{ "tracks": [...] }`), looked up in `medias/<folder>/` then `<folder>/`, as for audio. With a `target`, it wins (single file). A name may be an `http(s)` address or a `/…` path.
- **Playback**: tracks follow one another in order and wrap to the first after the last; a one-track list loops. Each track has its own aspect ratio (the screen adapts when `h` is 0). An unreadable track is skipped; if none can be read, or the list is empty, the screen disappears (message in the console).
- **Previous / next**: a click on the **right edge** (20% of the width) of the screen goes to the next track, on the **left edge** to the previous one; elsewhere, pause / play as in 1.12.10. Without a list (or with one track) the whole screen stays pause / play. The tooltip explains it; the Diagnostic gives "track N/total: name".
- **Tool**: `glb2html.py --video-list FOLDER` writes `FOLDER/playlist.json` (mp4, webm, m4v, ogv; alphabetical, numbers compared as numbers), with `--dry-run`. **Viewer editor**: "Video folder" field and "Update the list (playlist.json)" button (choose the region folder, as for audio).
- Tests: `tests/zone_video_liste.py` (new).
- Limits: no shuffle; lists do not play in the viewer editor (the editor panel does not play video); local viewer files untested; Edge without hardware acceleration and big files untested.

### 18/11/2026: zone radio and music in overview (range measured from the camera)

- **Request from Klaatou**: media must be available all the time, like images and video screens, not only while walking.
- **Outside walking mode** (overview, before the walk), zone radio and music play when the **camera** is within range: 3D distance (height counts) from the camera to the zone, or to its element if linked; no more −4 / +8 m height window. The "Radio" / "Music" line shows the camera distance, as when walking. While walking nothing changes: the visitor counts.
- Outside walking mode only radio and music are tracked: no "click or E" prompt, no zone entry, no editor (zones do not play in the viewer editor).
- Sound still needs a first click or key press in the page, and the Sound setting (zone Radio / Music boxes, volume) applies as before.
- Caveat: in orbit the camera is often high and far; a 20 m zone is then rarely in range.
- Test added: `tests/zone_apercu.py`. `tests/zone_cast.py`: returning to the global view no longer requires the line to be hidden (the camera may stay within 2x the range: it then says "out of range").

### 18/11/2026: video zones: click on the screen = pause / play

- **Request from Klaatou**: stop or restart a video by clicking it, like a player.
- A click on a playing screen stops it; another click restarts it. The hover tooltip now says "click: pause / play" (it used to show the target).
- A click-stop lasts while the visitor stays within range: leaving the range and coming back makes the screen play again by itself. Turning away does not cancel it.
- The click triggers no zone action and sends nothing to presence. It does nothing on a screen out of range, not yet loaded or failed; a hidden screen (missing file) no longer catches clicks.
- Diagnostic: a "stopped by a click" state is added to the existing ones.

### 18/11/2026: video zones, step 2: sound (`sound` key)

- **`sound: true` key** on a `video` zone: the screen has sound. Without the key it stays muted as in 1.12.7.
- **Only one screen speaks**: among playing screens with sound, the one nearest the visitor; the others keep playing, muted. Volume = (1 − distance / range) × the radio / music volume of the Sound window (at least 5% of that level), like audio zones.
- Sound follows the Sound setting ("Sounds" ticked) and only starts after a first click or key press, as browsers require. If the browser still refuses the sound, the screen falls back to muted and retries 5 seconds later.
- **Editor**: "Screen sound" field (muted / with sound). **Diagnostic**: the Video line shows "sound N%" or "sound requested but muted".
- Limits: zone radio and music keep playing alongside a screen with sound; no file list yet (step 3).

### 18/11/2026: video zones: range follows the visitor, not the camera

- **Defect reported by Klaatou**: in free view the video did not stop when the visitor moved away (the camera stayed near the screen).
- **Fix**: while walking, the distance to the screen is measured from the visitor (eye height), like audio zones; the field-of-view test (screen in frame or not) still uses the camera. Outside walking mode the camera is still the reference.
- Test added: free view, camera in front of the screen, visitor far away → pause; visitor back in range → play.

### 18/11/2026: video zones, step 1 (`video` type)

- **Request from Klaatou**: video screens as in OpenSim, working like the "image" boards for the target. Agreed steps: 1) a screen with one file, played when within range; 2) sound by distance (`sound: true`); 3) a list of files (`folder`, `playlist.json`, like audio zones). Klaatou's choices: muted by default, every screen within range plays, sound only from the nearest (step 2).
- **`video` zone**: a board placed on a wall (like `image`) whose texture is a video file. Keys: `target` (file name or address), `w`, `h` (0 = from the video's aspect ratio), `radius` (20 m by default, 0.5 to 200), `x y z yaw`, `label`. No `mesh`, `cone`, `link` or useful `trigger`: nothing to click.
- **File name**: as for an image. Bare name (`clip`): `medias/clip.mp4`, `.webm`, `.m4v`, `.ogv`, then the region folder; with an extension: as is in `medias/` then in the folder; an `https:` address or `/…` path as is (another site must allow CORS, otherwise WebGL refuses the texture). `javascript:`, `data:`, `blob:` refused.
- **Playback**: nothing is requested from the server before being within range (`radius`) and in the camera's field of view. The video then plays, looped, **without sound**, and pauses one second after turning away or leaving the range, or when the tab is hidden. At most 8 videos play at once (the nearest). Reduced motion requested from the system (`prefers-reduced-motion`): first frame only.
- **Editor**: type "Video (screen on a wall)", fields file, width, height, range; in the editor the screen is a board showing the file name and the video does not play. `Copy the diagnostic` gives one line per screen (file read, state).
- **Code**: `core.js` (`videoPlane`, `videoTick`, `cleanZone`), `gen_tpl.py` (`clean_zones`, same result), `viewer_tpl.html`, `i18n`. Video screens are not near zones (no "click or E" prompt).
- **Test**: `tests/zone_video.py` (23 checks, test videos made with ffmpeg, page served over http): JavaScript = Python cleaning, nothing requested out of range, bare name, muted looped playback, pause on turning away and on leaving, resume, far screen loaded only on approach, missing file, `javascript:`, H.264 mp4, cap of 8, texture really drawn, reduced motion. Five defects introduced on purpose (never pausing, immediate loading, no cap, texture not applied, no field-of-view test) make it fail.
- **Changes in `dist\`** after `python build.py`: `glb2html.py`, `index.html`, `glb-viewer.html`, `carte.html` (it embeds the language dictionary). `VERSION`: `1.12.7`.
- **Limits of step 1**: no sound; no `.txt` caption (the title is read from the file name, after the first dash, like images); the file is downloaded whole (`preload`) once within range; in `glb-viewer.html` (local files without a server) the video does not load: the page must be served over http. Not tried: Edge without hardware acceleration (software rendering), large videos, a server without CORS.

### 18/11/2026: floating window: opened on the left, vertically centred; ↗ closes the window

- **Request from Klaatou**: at the bottom right the window showed Edge's ghost rectangle (without hardware acceleration) right above it as soon as it opened; at the centre left there is no ghost as long as nothing is moved.
- **Why it works**: the ghost is the mirror image of the player's area about the screen's horizontal midline. A vertically centred window contains that mirror image, which is therefore hidden under it. Once moved up or down the ghost comes back (known limit, see 1.12.5).
- **Changed** (`src/template.html`): `#frameWin` is placed with `left:16px` and `top:calc((100vh - height) / 2)` instead of `right:16px;bottom:72px`. Dragging (which sets `left`/`top`) is untouched.
- **↗ button** (request from Klaatou): opens the address in a new tab **and closes** the mini window (`src/template.html`).
- **Test**: `tests/zone_frame.py` goes to 28 checks (opening position: on the left, and the player's mirror image contained in the window; ↗ closes the window). The move check now drags the window to the right (it starts at `left:16px` and stops at 0 going left).
- **Changes in `dist\`** after `python build.py`: `glb2html.py`, `index.html`, `glb-viewer.html`. `VERSION`: `1.12.6`.

### 18/11/2026: floating window: hiding while dragging removed

- **Finding from Klaatou** (Edge, hardware acceleration turned off on purpose to keep the GPU for AI; `edge://gpu`: WebGL, rasterization and compositing in software): the ghost rectangle, sky-coloured, the size of the player and mirrored about the screen's horizontal midline, appears as soon as the window opens and stays fixed on screen while the scene moves; it covers no page panel; it disappears when the canvases are hidden. Hiding during the drag (1.12.4) changes nothing: the ghost comes back on release. A `will-change: transform` on the window or on the canvases does not remove it either.
- **Cause**: a drawing defect of Edge's software compositor (WebGL canvas layer under a frame from another site), not of the page code. Not reproduced in the sandbox (Chrome, software rendering). Known limit: Edge without hardware acceleration may leave a ghost rectangle next to the floating player.
- **Removed** (`src/template.html`): hiding the frame while dragging and the `grab` counter that only served it. Back to `#frameWin.drag iframe{pointer-events:none}` and to the immediate removal of `drag` of 1.12.3; the YouTube lists of 1.12.4 are kept.
- **Test**: `tests/zone_frame.py` goes to 26 checks (the two hiding checks are removed; moving by the header is still checked).
- **Changes in `dist\`** after `python build.py`: `glb2html.py`, `index.html`, `glb-viewer.html`. `VERSION`: `1.12.5`.

### 18/11/2026: floating window: YouTube lists, no more ghost rectangle when moving

- **Finding from Klaatou** (screenshot): moving the floating window of a YouTube link zone leaves an empty sky-coloured rectangle, the size of the player, displayed lower down after release; and a list link (`&list=`) only played the video.
- **Ghost rectangle**: not reproduced in the sandbox (Chrome on Linux, software rendering, a real video in a frame from another site: the window moves cleanly). Cause not established; hypothesis: a region badly refreshed by the browser when a player from another site moves over the 3D background. **Fix** (`src/template.html`): while the header is dragged, the frame is hidden (`visibility:hidden`, playback continues); it is shown again two frames after release. To be confirmed on screen at Klaatou's. **Defect found in this first fix** (`zone_frame.py` failed at Klaatou's, software rendering, slow frames): the deferred removal of `drag` from an earlier release (two `requestAnimationFrame`) also applied to a grab made in the meantime, so the player became visible again during the drag. Reproduced by slowing `requestAnimationFrame` (250 ms). Fixed with a grab counter (`grab`): the removal applies only if no new grab happened.
- **Lists** (`ytEmbed`, `src/template.html`): `watch?v=ID&list=L` (also `youtu.be/ID?list=L`, `embed/ID?list=L`) plays the video within its list (`embed/ID?list=L`); `playlist?list=L` opens the list player (`embed/videoseries?list=L`). A list id is kept only if it is 10 to 80 characters among letters, digits, `_` and `-`; otherwise the video alone (or, for `playlist?list=` without a valid list, the address as is). **`RD…` mix**: YouTube only documents `PL…` lists for embedding; a mix may be refused (the ↗ button remains the fallback).
- **Test**: `tests/zone_frame.py` goes to 28 checks (mix list, list alone, invalid list, playlist without list, hiding while dragging and return after release, re-grab before the previous release has finished with slowed frames). Three defects introduced on purpose (hiding removed, lists removed, deferred removal unprotected) make it fail. Zones family rerun without regression.
- **Changes in `dist\`** after `python build.py`: `glb2html.py`, `index.html`, `glb-viewer.html`. `VERSION`: `1.12.4`.
- **Not tried**: the real display of the player and of the list (sandbox without access to YouTube), the `RD…` mix, the effect of hiding on the ghost rectangle (Edge, software rendering), touch.
- **Still to update**: manual (§ 5.7), `REFERENCE_JSON.md` (`frame` key), procedures, histories.

### 18/11/2026: link zones in a floating window (`frame` key)

- **Request from Klaatou**: show a YouTube video or a page in the region, like OpenSim screens, without leaving the page.
- **`frame` key** (`url` zones only, written only when true; `cleanZone` in `src/core.js` and `clean_zones` in `src/gen_tpl.py` identical): the link opens in a movable, resizable window of the page (`frameOpen`, `src/template.html`) instead of a new tab. Same triggers as the other link zones: `click`, the E key, `enter`, `both`.
- **YouTube**: the `watch?v=`, `youtu.be/`, `shorts/`, `live/` and `embed/` forms become a `youtube-nocookie.com/embed/ID` player (start from `t=` or `start=` in seconds; autoplay requested on click or E).
- **No frame** (the link opens as before): `hop://`, `http` from an https page (mixed content blocked by the browser), an address of the same origin as the page (the `sandbox` would not protect it). An `http` address is framed from a page that is not https.
- **Walking into it (`enter`)**: the window opens with a "Load (contacts HOST)" button; no site is contacted before the visitor clicks.
- **Window**: title = zone name; the ↗ button opens the original address in a new tab (sites that refuse to be framed); the cross closes it and stops playback; one window at a time; `sandbox` and `referrerpolicy` set on the frame; not part of the window layout file.
- **Viewer**: "Open in a floating window of the page" box in the link zone form. Texts in French and English: `page.frame.newtab`, `page.frame.close`, `page.frame.load`, `viewer.zf.frame`.
- **Test**: `tests/zone_frame.py` (new, 22 checks: address given to the frame, YouTube, http and hop, https page by request interception, enter without loading, move, cross, Python and JavaScript mirror of the validation). Two defects introduced on purpose (mixed-content and same-origin guard removed; immediate loading on `enter`) make it fail. Zones family rerun without regression: `zones_url_cone`, `zone_cast`, `zone_audio`, `zone_distance`, `zones_numeros`, `image_zone`, `editeur_cone`, `radio_flux`, `i18n`, `modulaire`, `smoke`, `dist_a_jour`. `samples` (3 failures) and `lien_image` (4 failures) fail identically on `main` in the sandbox.
- **Changes in `dist\`** after `python build.py`: `glb2html.py`, `index.html`, `carte.html`, `glb-viewer.html`. `VERSION`: `1.12.3`.
- **Not tried** (sandbox without access to YouTube or other sites): the real display of the player and of pages, Edge and Windows, touch, autoplay, videos whose embedding is forbidden or that ask for a sign-in, a YouTube player from a page opened as a file (try from an https address).
- **Still to update**: manual (§ 5.7, editor), `REFERENCE_JSON.md` (`frame` key), procedures, histories.

### 17/11/2026: manual appendix completed, double terrain in § 3.3, CHANGELOG and histories fixed

- **Finding**: batch 1.12.1 had replaced the batch 1.11.30 entry (both CHANGELOG files) and its history row (`HISTORIQUE.md`, `HISTORY.md`) with its own texts; its CHANGELOG entry was filed under 1.12.0 instead of "Unreleased", and its history row sat at the place of 1.11.30.
- **Fixed**: batch 1.11.30 entry and rows restored (text of commit `45a459f`); batch 1.12.1 entry and rows under "Unreleased" and after the 1.12.0 release.
- **Manual appendix (§ 13)**: three rows added, in French and in English (batches 1.11.6 to 1.11.12, 1.11.13 to 1.11.23, 1.11.30 to 1.11.35), with references to the sections that describe each addition.
- **Manual § 3.3**: new bullet "Never two overlapping terrains" (`oar2glb` 1.11.11, `glb2tiles` 1.11.12), in French and in English.
- **`REPRISE.md`**: state at batch 1.12.2; `presence_server.py` on the VM read by Klaatou (1.10.37, fingerprint `0168d70b`); demo up to date; rule 27 present in `REGLES.md`; documentation debt updated.
- No code changed. `VERSION`: `1.12.2`.

### 17/11/2026: `REPRISE.md` up to date (release 1.12.0)

- `REPRISE.md`: state at batch 1.12.1, last release 1.12.0, per-file numbers, batches 1.11.24 to 1.11.35, documentation debt.
- No code changed. `VERSION`: `1.12.1`.

## 1.12.0 (17/11/2026)

### 17/11/2026: release 1.12.0: audio zones, radio with several streams, Sound window and volume

- **Release**: 1.12.0 (17/11/2026), decided by Klaatou, gathers batches 1.11.1 to 1.11.35 (described below, under this same heading). The minor number goes up: features were added since 1.11.0. This batch only changes `VERSION` and the documents (manual title, overview, histories, this log); `dist\` and `VERSIONS.json` are unchanged.
- **Per-file numbers**: `index.html`, `glb-viewer.html`, `glb2html.py` 1.11.34; `carte.html` 1.11.29; `glb2tiles.py` 1.11.12; `oar2glb.py` 1.11.11; unchanged: `presence_server.py` 1.10.37, `oars2site.py` 1.10.25, `web3d_gui.py` 1.10.31, `diag_carte.py` 1.10.2, `extraire_batiments.py` 1.6.3, `iar2oar.py` 1.6.4. Nothing to redo on the VM: `presence_server.py` does not change.
- **Tried by Klaatou** (17/11/2026): the Sound window and the volume sliders, the demo update. **Not tried here** (Linux sandbox): Windows, Edge, Firefox, Safari, a real touch screen, a real mp3 stream in the page, measuring the music volume (same formula as the radio, only the radio is measured).
- **Known documentation debt**: the manual annex (§ 13) has no row for batches 1.11.13 to 1.11.23; the "double terrain" (`oar2glb` 1.11.11, `glb2tiles` 1.11.12) was not re-read in manual § 3.
- **GitHub release notes** (to attach: `galerie-photos.zip` and `region-simple.zip`, rebuilt by `python fabriquer_paquets.py` after `VERSION` is set to 1.12.0), English then French:

  > **Web_3d 1.12.0: audio zones, radio with several streams, Sound window and volume**
  >
  > **Do not unzip over an existing package**: copy `index.html`, `carte.html` (and `favicon.ico`) into your folder instead.
  >
  > ### What's new
  >
  > **1. Audio zones** (manual § 5.20)
  > - New zone type `audio`: the sound files of a folder play in a loop within range while walking; `playlist.json`, ⏮ / ⏭ buttons and a track counter; remote sounds through `tracks`.
  >
  > **2. Radio zones** (manual § 5.19)
  > - A radio zone can offer several streams (`streams`, `[["name", "address"], ...]`), chosen from a list in the State block; the old keys `urls`, `labels` and `target` are still read.
  > - The Radio and Music lines show the distance and stay displayed (blinking distance) up to twice the range; tooltip with the zone and the stream name.
  > - A box on the line cuts the radio or the music.
  >
  > **3. Sound window and volume** (manual § 7.66)
  > - A small **Sound** window follows the radio and the music (▲ arrow on the State lines, click on the zone cone); it is part of the window layout.
  > - Its own **volume** for the radio and the music (50 % by default), independent of the Settings "Sounds" volume (beeps).
  > - The arrow pad can be moved (§ 7.33).
  >
  > **4. Other changes**
  > - The chat block folds with the **B** key and unfolds by itself on a message, an arrival or a departure; the help shows keys and titles in bold.
  > - New project icon; `oar2glb.py` never leaves two overlapping terrains in the GLB; `glb2tiles.py` no longer tiles the convoar "Terrain" when the "Terrain i,j" patches are there; the world map grid follows the page width.
  > - Documents: manual, overview, procedures, `CREATORS.md` (radio streams and the `--radios` list).
  >
  > **Presence server hosts**: nothing to do, `presence_server.py` is unchanged (1.10.37).

  > **Web_3d 1.12.0 : zones audio, radio à plusieurs flux, fenêtre Son et volume**
  >
  > **Ne pas dézipper par-dessus un paquet existant** : copier `index.html`, `carte.html` (et `favicon.ico`) dans votre dossier.
  >
  > ### Nouveautés
  >
  > **1. Zones audio** (manuel § 5.20)
  > - Nouveau type de zone `audio` : les fichiers son d'un dossier jouent en boucle à portée en promenade ; `playlist.json`, boutons ⏮ / ⏭ et compteur de pistes ; sons distants par `tracks`.
  >
  > **2. Zones radio** (manuel § 5.19)
  > - Une zone radio peut proposer plusieurs flux (`streams`, `[["nom", "adresse"], ...]`), au choix dans une liste du bloc État ; les anciennes clés `urls`, `labels` et `target` sont toujours lues.
  > - Les lignes Radio et Musique donnent la distance et restent affichées (distance qui clignote) jusqu'à 2 fois la portée ; bulle avec le nom de la zone et du flux.
  > - Une case sur la ligne coupe la radio ou la musique.
  >
  > **3. Fenêtre Son et volume** (manuel § 7.66)
  > - Une petite fenêtre **Son** suit la radio et la musique (flèche ▲ sur les lignes de l'État, clic sur le cône de la zone) ; elle fait partie de la disposition des fenêtres.
  > - Un **volume** propre à la radio et à la musique (50 % au départ), indépendant du volume des « Sons » de Réglages (les bips).
  > - Le pavé de flèches est déplaçable (§ 7.33).
  >
  > **4. Autres changements**
  > - Le bloc de chat se replie avec la touche **B** et se déplie seul à un message, une arrivée ou un départ ; l'aide met les touches et les titres en gras.
  > - Nouvelle icône du projet ; `oar2glb.py` ne laisse jamais deux terrains superposés dans le GLB ; `glb2tiles.py` ne tuile plus le « Terrain » de convoar quand les patches « Terrain i,j » sont là ; la grille de la carte des mondes suit la largeur de la page.
  > - Documents : manuel, vue d'ensemble, procédures, `CREATEURS.md` (flux radio et liste `--radios`).
  >
  > **Hébergeurs d'un serveur de présence** : rien à faire, `presence_server.py` ne change pas (1.10.37).

### 17/11/2026: `CREATORS.md`: radio streams and the `--radios` list

- `CREATEURS.md` and `CREATORS.md`: § 2 (the creator gives the host the addresses of their `streams` to get the track title), § 7 (what the server does with `--radios`: only the listed addresses, one connection every 30 s while a visitor listens, only the title is noted); the demo server state moves to 17/11/2026 (`--visits-names` and `--radios` active, from the launch line given by Klaatou).
- **Not done**: the silent walker (`--idle-walk`, absent from the demo launch line, so without effect there) and the bounded nickname registry (`--max-names`) are not in the note.
- No code changed. `VERSION`: `1.11.35`.

### 17/11/2026: Sound window: the volume slider takes the colour of the other sliders

- **Finding by Klaatou**: the volume slider of the Sound window was black while the other sliders of the page are blue. **Cause**: `#soundVolRow input` forced `accent-color:#000` (`src/template.html`); the Settings and light sliders have none and keep the browser colour.
- **Done**: `accent-color` removed from the slider; `tests/fenetre_son.py` checks that its accent colour is the one of the Settings slider.
- **Not tried**: the real look on Windows, Edge and touch (the test compares styles, not the picture). The checkboxes of the Radio and Music lines stay black (`accent-color:#000`); nobody asked to change them: to be decided.
- `VERSION`: `1.11.34`.

### 17/11/2026: overview up to date (Sound window, `streams`, volume); `MODE_EMPLOI` = the manual

- `VUE_ENSEMBLE.md` and `OVERVIEW.md`: the Radio line mentions multiple streams (`streams`) and the Sound window with its own radio and music volume.
- **Fix**: the batch 1.11.27 entry said `MODE_EMPLOI` was not in the repository; it is the old name of the manual, now `docs/fr/MANUEL.md` since v38, and the manual was up to date. Same fix in `REPRISE.md`.
- No code changed. `VERSION`: `1.11.33`.

### 17/11/2026: `verif_trad`: the inline code of `streams` is the same in French and English

- `verif_trad.py` gave 3 errors on the pairs changed by batches 1.11.27 and 1.11.29 (the inline code `["name", "address"]` translated into English): `["label", "url"]` in `MANUEL.md` / `MANUAL.md` and `REFERENCE_JSON.md` (fr and en). Appendix line of the manual: batches 1.11.24 to 1.11.29. The check had not been run before these batches were delivered.
- No code changed. `VERSION`: `1.11.32`.

### 17/11/2026: delivery mechanics moved from `REGLES.md` to `REPRISE.md` (section 8)

- `REPRISE.md`: new section 8 (setting and particulars, delivering a change, before any delivery, what each delivery gives, visible texts and documents); the old section 8 becomes section 9. The content comes from rules 10, 11, 13 to 16, 18, 19, 21, 23 and the sandbox note of `REGLES.md` (a Project file, rewritten by Klaatou: those rules are now only a pointer, numbers kept; rule 25 stays there, because it names names that cannot be written in the repository).
- **New convention** (Klaatou's decision): in a series of PowerShell commands, only the first starts with the `cd`; section 0 and section 8.4 of `REPRISE.md`.
- No code changed. `VERSION`: `1.11.31`.

### 17/11/2026: initials removed from the batch 1.11.27 entry (rule 25)

- The batch 1.11.27 entry named the reviewer by initials; replaced by "Klaatou". No other text of the repository contains them. If batch 1.11.27 was committed before this fix, the initials stay in the git history.
- No code changed. `VERSION`: `1.11.30`.

### 17/11/2026: independent radio / music volume, speaker icon as a black drawing

- **Fix to batch 1.11.28**: the slider of the Sound window is no longer multiplied by the Sounds volume of Settings (its maximum was Settings' one). It alone sets the radio and music, from 1 to 100, **50 by default**; the Sounds volume now only sets the beeps. With no saved value (first start after the update), the slider takes the Sounds volume, so nothing changes to the ear.
- **Icon**: a black drawing (SVG) with 0, 1 or 2 waves replaces the emoji, too pale.
- **Tooltip** rewritten: it says what the slider sets, that the beeps and the Sounds volume are separate, and how to mute.
- Documents: manual § 5.19, § 5.20, § 7.66 (and the Sound window text).
- Files: `src/template.html`, `src/i18n/fr.json`, `src/i18n/en.json`, `tests/fenetre_son.py`, `tests/zone_cast.py`, `docs/*/MANUAL.md`, `VERSION` `1.11.29`. **Not tried**: Windows, Edge, touch, how it looks on screen.

### 17/11/2026: own volume for the radio and music, in the Sound window

- **New**: a loudspeaker icon in the header of the Sound window, left of the cross, shows and hides a volume **slider** (1 to 100, 100 by default) that only sets the **radio and music of the zones**. The real volume is the Sounds volume of Settings x this slider: chat and arrival beeps do not change. The value is kept by the browser (`srcVolume` in `glb2html_visitor`), not in the layout file. The icon drawing changes with the level (never the color). Escape hides the slider. To mute, use the line's box (the slider minimum is 1).
- Files: `src/template.html`, `src/i18n/fr.json`, `src/i18n/en.json`, `tests/fenetre_son.py`, `VERSION` `1.11.28`. **Not tried**: Windows, Edge, touch, how the emoji look. Still to update: manual § 7.66.

### 17/11/2026: documents for batches 1.11.24 to 1.11.26

- **Manual**: § 5.19 (`streams`, stream name, tooltip, mind the comma), § 7.66 (Sound window), movable pad (§ 7.33), § 7.44 (original layout), § 10.25 (`streams` and `--radios`), appendix § 13.3; `SIMPLE_PROCEDURES.md` § 14; histories fr and en.
- No code changed. `VERSION`: `1.11.27`. **Not checked**: Klaatou's review; `MODE_EMPLOI`, named by batch 1.11.24, is the old name of the manual (now `docs/fr/MANUEL.md` since v38): the manual is up to date.

### 17/11/2026: radio streams in one array: `streams` = `[["label", "url"], ...]`

- **New**: a radio zone (`cast`) lists its streams in one array of pairs, the name first (`""` without a name): `"streams": [["Label 1", "url1"], ["Label 2", "url2"]]`. Moving, adding or removing a stream is moving, adding or removing one pair. Only `streams` is written (editor of the viewer, `--update`, `--zones`).
- **Compatibility**: the old keys `urls`, `labels` and `target` are still read and converted to `streams` (zones files and pages already made keep working). A missing label is kept empty; the page falls back to the zone name, then the zone id.
- **Tooltip of the Radio line**: without a zone `label` and with several streams, it starts with the stream line ("Flux : ..."), no longer with the zone id.
- Files: `src/core.js` (`cleanZone`, tooltip of the zone), `src/gen_tpl.py` (`clean_zones`, same result), `src/template.html` (radio module), `src/viewer_tpl.html` (editor), `docs/*/REFERENCE_JSON.md`, `tests/radio_flux.py`, `tests/fenetre_son.py`, `VERSION` `1.11.26`. Still to update: manual (section 5.19), procedures, history.

### 17/11/2026: Sound window title shows the type of the active zone

- The title of the Sound window shows the type of the zone whose line is displayed (the nearest one, or the one whose box is ticked: only one is active at a time): "Sound · Radio" or "Sound · Audio playlist" ("Son · PL Audio" in French).
- Files: `src/template.html`, `src/i18n/fr.json`, `src/i18n/en.json`, `tests/fenetre_son.py`, `VERSION` `1.11.25`.

### 17/11/2026: movable arrow pad, Sound window (zone radio and music) in the window layout

- **Arrow pad**: a grip above the pad; dragging the grip moves it (mouse and finger), double-click puts it back; the position is kept by the browser (`glb2html_padPos`) and is part of the layout file (save / load / reset).
- **Sound window** (new, fourth window after H, I, L): repeats the Radio and Music lines of the Status window (text, distance, previous / next with n/N, "mute" box, stream choice). The arrow on those lines opens it **and closes the Status window**; the cross closes it. It is movable, resizable by its right edge, dockable on the piles, saved in the layout file; its size follows its content. The Status window lines are unchanged.
- **Cone click**: a click on the cone of a zone radio or audio zone in range shows or closes the Sound window (a click on a zone out of range does nothing; the click is no longer reported to the presence server as a zone activation).
- Files: `src/template.html`, `src/core.js`, `tests/v41.py`, `src/i18n/fr.json`, `src/i18n/en.json`, `VERSION` `1.11.24`. Still to update: manual (windows, pad), `MODE_EMPLOI`.

### 17/11/2026: `REPRISE.md` trimmed (601 lines, 166 KB, down to 150 lines, 36 KB)

- **Finding**: `REPRISE.md` duplicated the changelog (log of batches 1.7.12 to 1.11.12: about 49 KB), stacked eleven "Decisions of the period" blocks and eleven "Pitfalls of the period" blocks, and kept three "Documents behind" paragraphs for different states (1.11.9, 1.11.1, 1.10.31). Every conversation reads it first.
- **Done**: new `REPRISE.md` sorted by topic (start of a conversation, project, state, architecture, commands, settled decisions, to do, documents behind, pitfalls); a single "Documents behind" block; state at 17/11/2026 (1.11.23, per-file numbers); lessons of batch 1.11.20 added (reviewing a local LLM's batch, checking version numbers with `git log`, `git checkout -- .` wipes uncommitted patches). The old file is kept **as it was** in `REPRISE_ARCHIVE.md` (annex "REPRISE.md of 15/11/2026"). History rows for batches 1.11.22 (missed) and 1.11.23.
- No code changed. `VERSION`: `1.11.23`. **Not checked**: that nothing essential is missing (Klaatou's review wanted).

### 17/11/2026: version numbers of batches 1.11.13 to 1.11.16 fixed

- **Finding**: Qwen's batches carried wrong numbers: `urls` and `labels` (batch 1.11.13) were called 1.11.12 in the code comments, and the entry for the ⏮ ⏭ buttons with counter announced `VERSION` 1.11.15 while the batch is 1.11.16 (`git log`).
- **Fix**: `1.11.12` comments → `1.11.13` (`src/core.js`, `src/template.html`); entry of the buttons with counter: 1.11.16; 1.11.20 entry: "batches 1.11.13 to 1.11.16". Entries 1.11.12 and earlier are not touched. `VERSION`: `1.11.22`.

### 17/11/2026: documents of batches 1.11.13 to 1.11.20: multi-stream radio, distance, out of range, tooltips

- **Documents**: `docs/fr/MANUEL.md` and `docs/en/MANUAL.md`: § 5.19 (several streams `urls` and `labels`, distance and out of range), § 5.20 (distance, ⏮ ⏭ buttons and counter), § 7.66 (checkbox and tooltip of the lines), § 10.25 (each `urls` stream in `--radios`); `REFERENCE_JSON.md` (French and English: a radio's `target`, new `urls` and `labels` rows); `PROCEDURES_SIMPLES.md` and `SIMPLE_PROCEDURES.md` § 14 (pointer); `HISTORIQUE.md` and `HISTORY.md` (batches 1.11.10 to 1.11.21).
- No code changed. `VERSION`: `1.11.21`. **Changes in `dist\`** after `python build.py`: only `docs\REFERENCE_OPTIONS.md` (its generation date).

### 17/11/2026: multi-stream radio and Radio / Music lines: fixes from the review of lots 1.11.13 to 1.11.16

- **Finding** (review and measurements in Chromium): (1) `glb2html.py --zones` dropped `urls` and `labels` of a radio zone (`clean_zones` in `gen_tpl.py` had not been adapted: the zone came out with `"target": ""`, so silent, with no message); (2) after a stream error, choosing another stream in the list did not play it (the error flag was per zone, the line showed the new stream's name with the old one's cause); (3) the stream list was rebuilt on every `selSync()` call (24 DOM mutations for 6 steps of one metre: an open list could close while walking); (4) in the viewer editor, with several streams, editing the address had no effect (`urls` takes precedence over `target`); (5) unchecking the Radio or Music checkbox of the State window stopped the sound but the matching Settings checkbox stayed checked (only the other source was unchecked).
- **Fixes**: (1) `clean_zones` keeps `urls`, `labels` and `target` (= first address) like `cleanZone` in `core.js` (same limits: 500 addresses, 600 and 60 characters, control characters removed, an empty address removes its label); (2) the error is remembered per zone **and** per stream (`bk()`), forgotten when leaving the zone and when that stream is chosen in the list (it is then tried again); (3) the list is rebuilt only when the zone changes (`selFor`); (4) the editor also rewrites the first address of `urls`; (5) the State window checkbox also updates the Settings checkbox of the same source. Tidying: working comments left in the code removed, comments deleted by mistake restored (1.11.1, 1.10.34, role of `bad`), `1.11.x` replaced by `1.11.13`, unused language key `page.opt.radio.stream` removed (`tests/i18n.py` passes again), indentation of `page.opt.sounds`.
- **Test**: new `tests/radio_flux.py` (18 checks: `--zones` with `urls` and `labels`, same result in Python and JavaScript on dirty values, stream list and labels, broken stream then another stream, broken stream tried again, list not rebuilt at each step, back to the first stream when leaving the zone, State window checkbox, ⏮ ⏭ buttons and n/N counter with wrap-around, shape of the editor fix). **Not tried**: the viewer editor on screen (the fix is read in the code), Windows and Edge.

### 17/11/2026: radio and music zones: tooltip on the State window lines

- **Request**: a tooltip when hovering the Radio and Music lines, explaining what they contain (zone name, title, distances, commands).
- **Feature** (`src/template.html`, `RADIO`, `MUSIC` blocks and the State window): `title` attribute (the browser's native tooltip) on each line, rewritten whenever the line changes and every metre; the checkbox and the ⏮ ⏭ buttons keep their own tooltip. Radio: zone, current stream (n/N when there are several), track title when known, distance, range and state (in range, or out of range: the sound is stopped), commands (checkbox; stream list when there are several). Music: zone, current track (n/N), distance, range and state, commands (checkbox; ⏮ ⏭ when there are several tracks). Eleven `page.tip.*` language keys (French and English).
- **Limits**: the native tooltip appears after about a second, does not follow the mouse and does not exist on touch screens; a custom bubble would be possible, not done.
- **Test**: `tests/zone_distance.py` (3 checks added: radio tooltip in range, out of range, music tooltip).

### 17/11/2026: radio and music zones: the line stays displayed out of range, the distance blinks

- **Request**: when walking past the range the line vanished from the State window; it must stay, with the distance, and show that the range is exceeded by blinking the distance.
- **Cause**: `zoneTick` (`core.js`) only kept zones within range (`d <= z.radius`); outside, `onCast(null)` hid the line.
- **Fix**: `zoneTick` also keeps the nearest radio zone and audio zone **out of range, up to twice the range** (estimate, to be calibrated); `onCast` and `onAudio` get a 4th argument (out of range); `RADIO` and `MUSIC` then stop the stream (nothing is downloaded) and show "♪ Radio: NAME — out of range (63 m / 50 m)"; a zone in range takes precedence over one out of range; when back in range, a failed stream is tried again; beyond twice the range the line disappears as before. The distance is a `<span>` (`srcFar`): it blinks through opacity (no colour: colour blindness); with the system's "reduced motion" setting (`prefers-reduced-motion`) it does not blink: bold and underlined. Two language keys (`page.radio.far`, `page.music.far`, French and English).
- **Test**: `tests/zone_distance.py` (line kept out of range with the blinking, removed beyond twice the range, stream stopped, resumed on return); `tests/zone_cast.py` adapted (the line now stays up to twice the range).

### 17/11/2026: radio and music zones: the status line shows the distance to the source

- **Request**: after the radio name and the title, show the distance to the source, to explain the lower volume and warn before the cut-off when walking away.
- **Finding**: `zoneTick` (`core.js`) already computed the distance every frame (volume `1 - d / range`) but only called the page back when the zone or the gain (within 0.01) changed; the "Radio" and "Music" lines are rewritten only on a state change. No message goes to the presence server: everything is local.
- **Fix**: `onCast` and `onAudio` receive the distance as 3rd argument and are called again when the whole metres change (`castM`, `audM`); `RADIO.set` and `MUSIC.set` keep it and rewrite the line only while playing or connecting; `distTxt` appends "(37 m / 50 m)" (rounded distance, range of the zone). Not shown on error, muted sound or waiting for a click. No language key added (same unit in French and English). The volume curve is unchanged (5 % floor up to the range limit, then cut-off).
- **Test**: `tests/zone_distance.py`.

### 16/11/2026: Audio playback: ⏮/⏭ buttons and track counter for the playlist

- **Requested by Klaatou**: add buttons to skip to the next and previous track in an audio zone, and display the current track number (e.g., "1/14") between them.
- **Function** (`src/template.html`, `MUSIC` block and State window): added `next()` and `prev()` (looping at ends) and `trackIndex()` functions to the `MUSIC` object. Added ⏮ and ⏭ buttons and the counter in the State window, next to the "♪ Music: …" line, visible only if the playlist has more than one track.
- **Change in `dist\`** after `python build.py`: `index.html`, `glb-viewer.html` and `glb2html.py`. `VERSION`: `1.11.16`.

### 16/11/2026: Audio playback: ⏭ (next) and ⏮ (previous) buttons for audio zones playlist

- **Requested by Klaatou**: add a button to skip to the next track in an audio zone playlist (type `audio`), and a button to go back to the previous track.
- **Function** (`src/template.html`, `MUSIC` block and State window): added `next()` and `prev()` functions to the `MUSIC` object. Added buttons in the State window, next to the "♪ Music: …" line, visible only if the current zone's playlist has more than one track (`MUSIC.count() > 1`). The index loops: at the end of the playlist, `next()` goes back to the first track, and `prev()` on the first track goes to the last one.
- **Change in `dist\`** after `python build.py`: `index.html`, `glb-viewer.html` and `glb2html.py`. `VERSION`: `1.11.15`.

### 16/11/2026: state window: checkbox to cut the radio or the music sound, next to the line

- **Klaatou's request**: a checkbox right next to the "Radio: [name]" line (or the track title for an audio zone) of the state window, with the same action as the matching Réglages checkbox: cut the sound, bring it back on re-check; the checkbox state must follow the logic of `RADIO.refresh0()`.
- **Function** (`src/template.html`, state block, `C.walk`): each "♪ Radio: ..." / "♪ Music: ..." line carries a checkbox (`stateRadioCk` / `stateMusicCk`) in front of its text, which moves into a `<span>` (the checkbox is no longer overwritten by the line). The change repeats exactly the Réglages checkbox action: `VIS.radio` / `VIS.music` updated, the other source unticked everywhere (Réglages checkboxes `visRadio`/`visMusic` **and** the other state checkbox), `visSave()`, `audioArbitre()`, `RADIO.refresh()`, `MUSIC.refresh()`. The checkbox state is re-synchronised on every pass of `RADIO.show()` / `MUSIC.show()` — that is, on every decision of `RADIO.refresh0()` / `MUSIC.refresh()`, including the "off" pass (`lvl() <= 0`): ticked when `VIS.radio` / `VIS.music`, disabled when sounds are off (like the Réglages sub-checkboxes). The line text and "Copy the diagnostic" are unchanged (the checkbox contributes no text to `textContent`).
- **Also in this lot**: the previous change, support for the `urls` array and `labels` for radio zones (several streams per zone, stream titles, stream selection in the state window).
- **Changes in `dist\`** after `python build.py`: `index.html`, `glb-viewer.html` and `glb2html.py` (they embed the template). `VERSION`: `1.11.13`. **Not tried**: a real browser (the code follows exactly the existing `RADIO`/`MUSIC` paths).

### 15/11/2026: glb2tiles: the convoar `Terrain` is not tiled when the `Terrain i,j` patches are there

- **Report** (ship region of a third party's site, ground still striped cream/navy with the sea off, although the duplicate had been removed from the tile): the overview `region.overview.glb` (read directly: 177 triangles of 26 m at y = 1.0000, colour (3,16,29), over x 12 to 252, z -12 to -252 of the ship's cell) lies at the same level as the 4 m sand cells of the patches. With the overview file removed, the ground is clean.
- **Cause**: the convoar `Terrain` node (16 384 vertices, textured material) has no `extras.terrain`, so `vue_ensemble` treats it as an object: simplified into large triangles, coloured with the texture average (a very dark blue), laid over the patches. Measured on the original tile: the old code gives 200 dark triangles in the overview, the new one 0. Also, tiling a GLB that had both terrains put both in the tiles.
- **Fix** (`tools/glb2tiles.py`, `construire_racines`): if at least one root carries `extras.terrain` and a root named exactly `Terrain` still has a mesh and no `extras.terrain`, that root is not tiled (same rule as `terrain_doublon` of `oar2glb.py`): neither in the tiles nor in the overview. Without patches nothing changes. The plan report gives one line: number, triangles, MB saved. Unrelated to `--exclude` (separate counter).
- **Test**: `tests/glb2tiles.py`, 2 checks (with patches: `Terrain` in no tile, the patch is there; without patches: `Terrain` kept). The first fails with the old code. The `dist` journal check of the same file now reads the tool's output as UTF-8 (the tool writes UTF-8 on purpose; it was read with the Windows code page and could not pass there). **Not covered**: tiles and overviews already made are not repaired: tile again from the repaired complete `region.glb`.
- **Changes in `dist\`** after `python build.py`: `glb2tiles.py`. `VERSION`: `1.11.12`.

### 15/11/2026: oar2glb: never two overlapping terrains in the GLB

- **Report** (GLB of a region on a third party's site): the page's ground was striped, cream and green fighting for the screen. The GLB held convoar's `Terrain` node **with its mesh** and the 16 `Terrain i,j` patches of `oar2glb.py`, at the same level.
- **Guard**: `terrain_doublon` (`oar2glb.py`), called after `terrain_pipeline`: if `Terrain i,j` patches are in the GLB, the mesh of any convoar `Terrain` node that still has it is removed (same rule as `remove_node`), with the message "[terrain] N convoar "Terrain" node(s) still had their mesh on top of the patches (striped ground): mesh removed". Without patches, or without a `Terrain` node: nothing changes. **Not covered**: `--terrain-only` (a GLB already made is repaired with the separate tool `glb_terrain_fix.py`, outside the repository).
- **Cause not established**: the current code already removes that mesh when it adds the patches; we do not know which step put both terrains together in this GLB.
- **Checked**: on the real GLB, `terrain_doublon` gives the same nodes and the same scene as `glb_terrain_fix.py`. **Test**: `tests/terrain.py`, six checks added (duplicate removed and patch kept, message, second pass without effect, convoar terrain alone untouched, patches alone untouched, node with children).
- **Changes in `dist\`** after `python build.py`: `oar2glb.py`. `VERSION`: `1.11.11`. **Not tried**: a full conversion with the real convoar.

### 15/11/2026: world map: the grid follows the page width

- **Klaatou's report**: `carte.html` shows the thumbnails in rows of 5, however wide the page is; when the page is made narrower the number of columns adapts.
- **Cause**: `main{max-width:1000px}` (`src/gen_tpl.py`, style of the map page) capped the usable area at 960 px; 5 thumbnails of 170 px with their 12 px gaps take 898, a sixth would need 1090. Measured in Chromium before the fix (14 regions): 4 columns at 800 px, 5 at 1300 px, 5 at 1900 px.
- **Fix**: `main{max-width:none}`: in automatic layout (regions without distinct positions) the grid shows as many columns as fit. The title and the footer keep the room they take. The position layout (distinct `x`, `y`) still follows the coordinates and does not change.
- **Test**: `tests/carte_largeur.py` (new, 3 checks: 800 px, 1900 px, growth). Fails before the fix (5 columns at 1900 px), passes after.
- **Changes in `dist\`** after `python build.py`: `carte.html`, `glb-viewer.html` and `glb2html.py` (they embed the map template, including the standalone `--map-page`). `VERSION`: `1.11.10`. **Not tried**: Edge and Windows.

### 15/11/2026: documents: audio zones, formats, remote sound and `tracks`

- **Klaatou's request**: correct the audio zones documentation.
- **Manual** (`MANUEL.md` and `MANUAL.md`, § 5.20): "mp3 and m4a/aac play everywhere" (never checked) replaced by "depends on the browser" (tried by Klaatou: `.aac`); new: a remote sound over `https://` is accepted, a page served over `https` refuses an `http` sound (mixed content), the remote site must accept being played from another site (not tried), `tracks` is entered by hand in `NOM.zones.json` (no field in the viewer). **`REFERENCE_JSON.md`** (`tracks` key) and histories (FR and EN).
- **No code changes**. `VERSION`: `1.11.9`.

### 15/11/2026: tab icon without the yellow ring

- **Klaatou's request**: the icon is fine at the bottom right of the pages, but nothing can be seen in the browser tabs; remove the yellow ring to get a bigger sphere.
- **Replaced**: `src/favicon.ico` only (ICO 16, 32, 48 and 64 px, transparent background): the sphere alone, cropped, fills the whole square (the useful image only filled 43 of 64 pixels); a yellow arc remains in front of the sphere. `src/credit.png` (the "Made with Web_3d" icon at the bottom right) does not change.
- **To do after `python build.py`**: `dist\favicon.ico` changes; **copy this file next to each published `index.html`** (the page uses it for the tab; without it, it takes the embedded PNG icon, with the ring). The desktop shortcuts (`web3d_gui.py --shortcuts`) use it too, but Explorer keeps the old image in its cache (see `ie4uinit.exe -show`). `VERSION`: `1.11.8`.
- **Not tried**: the look in a real Edge or Chrome tab on Windows (seen only as enlarged images, light and dark backgrounds).

### 15/11/2026: reflections message: "shiny or metallic"

- **Klaatou's request**: the bar said "metallic (PBR) materials" for PalmIsland, an old OAR without PBR. Found in the GLB: 27 of 210 materials carry a `metallicFactor` of 0.25, 0.5 or 0.75 (the shiny materials of old OARs); the page's count is exact, the word "PBR" was misleading.
- **Text** (`src/i18n`, FR and EN): "This region contains N shiny or metallic material(s). Turn on the reflections at 60 %?". **Test**: `tests/reflets_metal.py` (two expected texts). **Manual** § 7.65 (FR and EN): the message and the PalmIsland case. The detection does not change.

### 15/11/2026: tutorials corrected, and "update the zones of a region already online"

- **Klaatou's remark**: after the `--audio-list` command, the tutorial still made him click "Update the list" in the viewer (both do the same thing: my tutorial asked for both); publishing was too short; a beginner needs the export and the update of an existing region in detail.
- **`SIMPLE_PROCEDURES.md` and `PROCEDURES_SIMPLES.md`**: § 14 (radio) and § 15 (playlist) rewritten: the playlist is made **once** (command, or button as a variant), the existing zones are imported before adding one, publishing points to the new **§ 16 "Update the zones of a region already online"**: which case is yours (shared shell, tiles, standalone page), import of the current zones (otherwise they vanish from the export), edit, export (`zones.json`), keep a copy then rename to `NOM.zones.json` and replace, try at home, publish only what changed, check online, go back.
- **Manual** (§ 5.20) and **indexes**: pointers to § 15 and § 16; histories (FR and EN). **No code changes**. `VERSION`: `1.11.6`.

### 15/11/2026: documents for batch 1.11.4 (audio zones) and step-by-step tutorials

- **Klaatou's request**: the documents of the audio zones, with complete tutorials "I want to put a radio" and "I want to put a playlist".
- **Manual** (`MANUEL.md` and `MANUAL.md`): new § 5.20 (`audio` zone: folder, order, `playlist.json` by command or viewer button, `tracks`, range and volume, radio or music, "does not play?", publishing, tried / not tried); § 7.66: "Music" line and "Zone music" box; `--audio-list` in the tools table; "Additions of 1.11.4" row of the appendix.
- **Tutorials** (`PROCEDURES_SIMPLES.md` and `SIMPLE_PROCEDURES.md`): § 14 "Put a radio in a region" rewritten step by step (choose the stream, place, try, save, publish, try again, title); new § 15 "Put a playlist of my own sounds in a region".
- **`REFERENCE_JSON.md`** (FR and EN): seven kinds of zones, `type`, `radius`, `cone`, new keys `folder` and `tracks`, example `ambiance`. **Index, overview, README, histories** (FR and EN).
- **No code changes** (`dist\` and `VERSIONS.json` identical). `VERSION`: `1.11.5`. **Not done**: a button of the launcher for `--audio-list` (not in batch 1.11.4 either). **Still to update**: nothing known.

### 15/11/2026: local audio zones (new `audio` zone type)

- **Klaatou's request**: play sound files (mp3 or other formats) from a folder as a playlist when walking near a zone.
- **New zone type `audio`**: a sub-folder of sound files (`"folder": "audio"`) is the playlist; files are played in alphabetical order (numbers compared as numbers: `2` before `10`, case ignored), in a loop, while the visitor walks inside the range (1 to 200 m). Volume = (1 - distance / radius) x Sounds volume; only the nearest audio zone plays. The zone is never linked to an element and has no "click or E" prompt. Formats: mp3, ogg, oga, opus, wav, m4a, aac, flac, weba, webm.
- **Playlist**: a static host cannot list a folder, so the page reads `playlist.json` (`{"tracks": [...]}`, a plain array is accepted) in the folder, searched like images (region folder, `medias` sub-folder first). A zone may carry an optional `tracks` array instead (names or http(s) addresses). An unreadable track is skipped; a missing, empty or unreadable list is said in the new "Music" line.
- **Producing `playlist.json`**: `python glb2html.py --audio-list "PATH\NAME\audio"` (also with `--dry-run`), or the viewer button "Update the list" of the zone (Chrome/Edge, region folder connected); both give the same order.
- **Radio and music exclusive**: two checkboxes in Settings, "Zone radio" and "Zone music"; ticking one unticks the other. Both ticked (default): the stronger of the two zones wins, the radio on a tie.
- **Test**: `tests/zone_audio.py` (command, page in Chromium with WAV tracks, viewer with a simulated folder). Not tried by Klaatou yet; MP3 playback not tried in the sandbox (no MP3 decoder there). **Documents**: in one later batch.

### 15/11/2026: documents for batches 1.11.1 and 1.11.2

- **Klaatou's request**: bring the documents that were behind for 1.11.1 up to date (and the 1.11.2 icon).
- **Manual** (`MANUEL.md` and `MANUAL.md`): **B** key in the key tables (§ 7.1 and § 7.2); foldable chat block (§ 7.25); help: keys and titles in bold, "B" line of the Chat group (§ 7.39); radio title requested only when listened to, requests spaced at least 1.5 s apart (§ 5.19 and § 10.25); "Additions of 1.11.1 and 1.11.2" row of the appendix (§ 13).
- **README** (`README.md` and `README.fr.md`): "B" row of the key table. **Histories** (`HISTORIQUE.md` and `HISTORY.md`): three rows (batches 1.11.1 to 1.11.3).
- **Tried by Klaatou** (15/11/2026): the B key, the unfolding when a visitor arrives, the bold help; his system and browser are not noted. **Not tried**: a real touch screen ("Close" folding the block).
- **No code changes** (`dist\` and `VERSIONS.json` identical). `VERSION`: `1.11.3`. **Still to update**: nothing known.

### 15/11/2026: new project icon ("Web 3D" globe)

- **Klaatou's request**: replace the project icon with the "Web 3D" globe (everywhere it is used).
- **Replaced**: `src/favicon.ico` (a real ICO file, 16, 32, 48 and 64 px, transparent background) and `src/credit.png` (64 px, the "Made with Web_3d" icon and the icon embedded in the pages: the same image). The supplied file was a PNG named `.ico`: converted to ICO.
- **Change in `dist\` after `python build.py`**: `favicon.ico`, `index.html`, `glb2html.py`, `glb-viewer.html`, `carte.html` (the PNG icon is embedded in the pages). `VERSION`: `1.11.2`.
- **Note**: at 16 px (browser tab) the "Web 3D" text is not readable, only the globe and the ring show; pages already built keep the old embedded icon until they are rebuilt (`glb2html.py --update`); a `favicon.ico` placed next to a page is still preferred to the embedded icon.

### 15/11/2026: foldable chat block (B key), bold help, radio title requested only when listened to

- **Klaatou's request**: be able to fold the chat, have it unfold by itself when someone writes, arrives or leaves, and have the help show keys and titles in bold; then, seen in the presence server console: with the radio unchecked in Settings, the server kept reading the stream title every 30 s for nobody.
- **Chat block**: the **B** key folds / unfolds the chat block ("Bloc de chat"), with no delay and no Settings checkbox. Folded, nothing is left on screen; a message, or another visitor arriving or leaving, unfolds it and it stays unfolded until folded again with B. **Enter** unfolds it and opens the input. Replaying the history on connection does not unfold it. The state is kept (`web3d.chat.fold`). On touch, "Close" closes the input and folds the block. Fixed on the way: when opening the input the block was made visible after taking focus, so focus was lost while folded.
- **Help**: in each line, the text before the first ":" (keys, gestures) is bold; group titles are bold capitals. New line "B: fold / unfold the chat block"; "arrow keys: walk" replaces the old movement wording.
- **Radio**: the page only asks the server for the stream title when it is really listened to (radio checkbox on, sounds on, volume above 0, stream with no error or mixed content); otherwise it withdraws its request and the server stops reading the stream when nobody listens. Since the server ignores a "radio" message received less than 1 s after the previous one (withdrawal included), the page spaces its requests by at least 1.5 s and sends the last wanted value when due. `presence_server.py` is not changed.
- **Change in `dist\`**: `glb2html.py`, `index.html`, `carte.html`, `glb-viewer.html` 1.11.1. `VERSION`: `1.11.1`.
- **Tests**: `tests/chat_replie.py` (new, 16 checks: fold, unfold on message, arrival, departure, Enter, history, bold help); `tests/radio_titre.py` extended (radio unchecked: no request; checked: request; unchecked again: request withdrawn). Pass: `radio_titre`, `chat_replie`, `i18n`, `dist_a_jour`, `smoke`, `chat_fleches`, `apropos`, `v36`, `v37_chat`, `v46`. `v33` (too long here) fails two checks (cursor of the "none" zone, label blinking) **also on 1.11.0**; its "@Bo" check could not be compared (timeout). **Not tested here**: Windows, Edge, real touch.

## 1.11.0 (15/11/2026)

### 15/11/2026: release 1.11.0: radio zones, metallic reflections, lighter textures, automatic sea, `oars2site.py`

- **Release**: 1.11.0 (15/11/2026), decided by Klaatou, gathers batches 1.10.1 to 1.10.38 (described below, under this same heading). The minor number goes up: features were added since 1.10.0. This batch only changes `VERSION` and the documents (manual title, § 13 lines, overview, histories, this log); `dist\` and `VERSIONS.json` are unchanged.
- **Per-file numbers**: `index.html`, `carte.html`, `glb-viewer.html`, `glb2html.py` 1.10.36; `presence_server.py` 1.10.37; `oar2glb.py`, `glb2tiles.py` 1.10.26; `oars2site.py` 1.10.25; `web3d_gui.py` 1.10.31; `diag_carte.py` 1.10.2; unchanged: `extraire_batiments.py` 1.6.3, `iar2oar.py` 1.6.4. To do on the VM: `presence_server.py` 1.10.37 (`scp`, restart; `--idle-walk 0` in `lance_presence.sh`, Klaatou's decision).
- **Tried by Klaatou** (Windows, Edge, demo): the radio zones and their titles, the reflections, the automatic sea, the launcher, `--tex-only`, the full suite on 12/11 (93 tests out of 95, `websockets` 16.0). **Not tried**: a real background tab for the silent walker; `oars2site.py` with the real convoar; macOS; Safari.
- **GitHub release notes** (to attach: `galerie-photos.zip` and `region-simple.zip`, rebuilt by `python fabriquer_paquets.py` after `VERSION` is set to 1.11.0 so that they contain the 1.10.36 pages), English then French:

  > **Web_3d 1.11.0: radio zones, metallic reflections, lighter textures, automatic sea, `oars2site.py`**
  >
  > ### What's new
  >
  > **1. Radio zones** (manual § 5.19)
  > - A new zone type `cast` plays an Icecast / SHOUTcast stream while walking within range, louder when closer; one radio at a time, stopped out of range and in the global view.
  > - The track title is shown when the presence server reads it in the stream (`--radios FILE`, manual § 10.25).
  > - The "Radio" line of the State block says why a stream does not play (mixed content, refused or unreadable stream).
  >
  > **2. Web page**
  > - Metallic reflections: new "Metallic reflections" slider in Settings (0 % by default; the page offers 60 % when the region has metals; § 7.65); diagnostic shown in a resizable window (§ 7.53).
  > - Automatic sea: `oar2glb.py` reads the region's water height from the OAR and the page starts at it (`seaM`; `--sea-m`, `--water-from` to fix a region already converted; § 3.13).
  > - `url` zones open on entering (`trigger` `enter` / `both`, `hop://` in the same tab); `cone` key per zone (§ 5.7.1).
  > - `--no-credit` removes the "Made with Web_3d" icon; the world map remembers the nicknames key (§ 9.16).
  >
  > **3. Conversion tools**
  > - Lighter textures: `oar2glb.py --tex-size`, `--tex-quality`, `--tex-only GLB` (on a GLB already made), table of texture sizes, `glb-stats.py` (§ 3.12).
  > - New `oars2site.py`: a folder of OARs becomes a complete site, one region after another, with the world map (`CONVERT_OARS.md`).
  > - Python 3.14: `glb2html.py` opens again. Tools no longer stop on a redirected output on Windows.
  >
  > **4. Graphical launcher** (§ 3.9)
  > - Project icon, `glb-stats.py` in the list, "Function" line, File / Folder buttons for `OAR` and `GLB` parameters, no "press Enter" after `--help`.
  >
  > **5. Presence server** (§ 10)
  > - Bounded nickname registry (`--max-names`), last address of the relay header, no more `KeyError` on simultaneous disconnections, visits log with the nicknames of visitors in the global view (`--visits-names`).
  > - Silent walker: a walker whose page is in the background is no longer counted nor shown after `--idle-walk` minutes (3 by default, `0` = never; § 10.26).
  > - Security review of the pages and the server (no page flaw found).
  >
  > **6. Documentation**
  > - Manual § 3.12, § 3.13, § 5.19, § 7.65, § 10.25, § 10.26; `CONVERT_OARS.md`; simple procedures § 12 to § 14; `REFERENCE_JSON.md` (`cast` zones, `seaM`, `credit`).
  >
  > ### Updating
  >
  > - If you already have one of the packages, copy only `index.html` and `carte.html` into your folder.
  > - Do not unzip the new zip over it: that would overwrite your configuration, zones and images.
  > - Presence server hosts: replace `presence_server.py` and restart it; the new options are optional.

  > ---
  >
  > **Web_3d 1.11.0 : zones radio, reflets métalliques, textures allégées, mer automatique, `oars2site.py`**
  >
  > ### Nouveautés
  >
  > **1. Zones radio** (manuel § 5.19)
  > - Un nouveau type de zone `cast` joue un flux Icecast / SHOUTcast en promenade à portée, plus fort quand on s'approche ; une radio à la fois, arrêtée hors de portée et en vue globale.
  > - Le titre du morceau s'affiche quand le serveur de présence le lit dans le flux (`--radios FICHIER`, manuel § 10.25).
  > - La ligne « Radio » du bloc État dit pourquoi un flux ne joue pas (contenu mixte, flux refusé ou illisible).
  >
  > **2. Page web**
  > - Reflets métalliques : nouveau curseur « Reflets métalliques » dans Réglages (0 % par défaut ; la page propose 60 % quand la région a des métaux ; § 7.65) ; diagnostic affiché dans une fenêtre redimensionnable (§ 7.53).
  > - Mer automatique : `oar2glb.py` lit le niveau d'eau de la région dans l'OAR et la page démarre à ce niveau (`seaM` ; `--sea-m`, `--water-from` pour corriger une région déjà convertie ; § 3.13).
  > - Les zones `url` s'ouvrent en entrant (`trigger` `enter` / `both`, `hop://` dans le même onglet) ; clé `cone` par zone (§ 5.7.1).
  > - `--no-credit` retire l'icône « Réalisé avec Web_3d » ; la carte des mondes mémorise la clé des pseudos (§ 9.16).
  >
  > **3. Outils de conversion**
  > - Textures allégées : `oar2glb.py --tex-size`, `--tex-quality`, `--tex-only GLB` (sur un GLB déjà fait), tableau des tailles de textures, `glb-stats.py` (§ 3.12).
  > - Nouvel outil `oars2site.py` : un dossier d'OAR devient un site complet, une région après l'autre, avec la carte des mondes (`CONVERTIR_OARS.md`).
  > - Python 3.14 : `glb2html.py` s'ouvre de nouveau. Les outils ne s'arrêtent plus sur une sortie redirigée sous Windows.
  >
  > **4. Lanceur graphique** (§ 3.9)
  > - Icône du projet, `glb-stats.py` dans la liste, ligne « Fonction », boutons Fichier / Dossier pour les paramètres `OAR` et `GLB`, plus de « Entrée » après `--help`.
  >
  > **5. Serveur de présence** (§ 10)
  > - Registre des pseudos borné (`--max-names`), dernière adresse de l'en-tête du relais, plus de `KeyError` à des déconnexions simultanées, journal des visites avec les pseudos des visiteurs en vue globale (`--visits-names`).
  > - Promeneur muet : un promeneur dont la page est en arrière-plan n'est plus compté ni montré après `--idle-walk` minutes (3 par défaut, `0` = jamais ; § 10.26).
  > - Audit de sécurité des pages et du serveur (aucune faille trouvée dans les pages).
  >
  > **6. Documentation**
  > - Manuel § 3.12, § 3.13, § 5.19, § 7.65, § 10.25, § 10.26 ; `CONVERTIR_OARS.md` ; procédures simples § 12 à § 14 ; `REFERENCE_JSON.md` (zones `cast`, `seaM`, `credit`).
  >
  > ### Mise à jour
  >
  > - Si vous avez déjà un des paquets, copiez seulement `index.html` et `carte.html` dans votre dossier.
  > - Ne dézippez pas le nouveau zip par-dessus : cela écraserait votre configuration, vos zones et vos images.
  > - Hébergeurs d'un serveur de présence : remplacez `presence_server.py` et relancez-le ; les nouvelles options sont facultatives.


### 15/11/2026: documents for batch 1.10.37: silent walker (batch 1.10.38)

- **Done**: manual (French and English): new § 10.26 (`--idle-walk`, what a silent walker is, what they keep, log lines, "silent" role of `liste`, the author's choice), additions line of § 13 (batches 1.10.30 to 1.10.38); `PROCEDURES.md` § 11 (French and English): `--idle-walk 0` in the server options and in `lance_presence.sh` (Klaatou's decision: a radio listener in the background stays counted as present); histories (batches 1.10.37 and 1.10.38). No code changes (`dist\` and `VERSIONS.json` identical). `deploy\lance_presence.sh` is not touched by this batch: Klaatou changed it himself.
- **Checks**: `verif_trad.py` on the three pairs touched (manual, procedures, histories); `dist_a_jour`.
- **Still to update** (rule 16): nothing known; `REPRISE.md` (rule 23).

### 15/11/2026: server: silent walker (no position for `--idle-walk` minutes) neither counted nor shown (batch 1.10.37)

- **Observation** (Klaatou, 14/11/2026): a visitor stayed "present" walking on the demo without moving or answering. Their page, open on another machine, was in the background: the browser freezes the animation loop, from which the page sends its positions (`src/core.js`, at most one per second), but the connection stays; the server had no timeout on the last received position (`peer.last` only served the 40 ms rate).
- **Done** (`src/presence_server.py`): option **`--idle-walk MIN`** (minutes, default **3**, estimate; `0` = never). A loop (`idle_loop`, step of 20 s at most) makes a walker **silent** when no position arrived within that delay (counted from the last position or the start of the walk): the others receive `leave`, the walker leaves `walkers()` (list sent to newcomers, counts of the `rooms` request and of the map, map nicknames), the walking time of the visits log is suspended, log line "silent (no position for N min)". At the next position: `join` with the position, counted again, log line "back (position received)". The walker **keeps the slot** (`--max-per-room`, creator maximum: `walkers(room, True)`) while connected. A silent walker switching to the global view or disconnecting causes no second `leave`. Console: `liste` shows "silent" as the role. Startup line "walker silent after N min without a position" or "never".
- **Texts** (`src/i18n`, fr and en): `py.presence.help.idle_walk`, `py.presence.idle_since`, `py.presence.idle_back`, `py.presence.idle_on`, `py.presence.idle_off`, `py.presence.role.idle`. No page change.
- **Checks**: new `tests/promeneur_muet.py` (`--idle-walk 0.05`: `leave` received, absent from a newcomer's `welcome`, `rooms` counts only the active one, slot kept with `--max-per-room 2`, `join` with the position on return, a single `leave` on disconnect, log lines, `--idle-walk 0` never silent); on the 1.10.36 code (`SANS_IDLE=1`): 3 checks fail. Also pass: `i18n`, `dist_a_jour`, `smoke`, `presence_noms`, `radio_titre`, `v51_vides`, `v52_http`, `http_proxy`, `correctifs_v52`, `python_recent`, `samples`. Per-file numbers after the build: only `presence_server.py` takes 1.10.37; `docs/REFERENCE_OPTIONS.md` regenerated (`--idle-walk`).
- **To do on the VM**: `scp` of `dist\presence_server.py`, restart (`systemctl restart web3d-presence`); the 3 min default applies without changing `lance_presence.sh`.
- **Not tried**: a real background tab (the test cuts the positions); Windows; the full suite.
- **Still to update** (rule 16): manual § 10 (`--idle-walk`, "silent" / "back" lines, "silent" role of `liste`), `PROCEDURES.md` § 11; histories; `REPRISE.md` (rule 23).

### 14/11/2026: documents for batches 1.10.30 to 1.10.35 (radio zones, titles, launcher); texts "stream refused or unreadable" and "empty title in the stream" (batch 1.10.36)

- **Manual** (`MANUEL.md`, `MANUAL.md`): new § 5.19 (`cast` zone: place, play, title, why a radio does not play: mixed content, 403 by `Referer`, SHOUTcast v1; rights; tried / not tried), § 7.66 ("Radio" line of the State block, Sounds and Zone radio boxes without presence), § 10.25 (`--radios`, `--radios-every`, `radio` protocol, reading in the stream, log lines, `curl` line to know whether a radio sends its titles); appendix § 13: row for batches 1.10.30 to 1.10.36.
- **`REFERENCE_JSON.md`**: six kinds of zones, `type` `cast`, `radius` up to 200 for a radio, `target` = stream address, default cone of radios, `dance-floor` sample, `presence_radios.json` file (table 11.1 and § 11.10). **`PROCEDURES.md`** § 11: `--radios presence_radios.json` in the options and in `lance_presence.sh`. **`PROCEDURES_SIMPLES.md`** / `SIMPLE_PROCEDURES.md`: new § 14 "Put a radio in a region". **`HISTORIQUE.md`** / `HISTORY.md`: batches 1.10.30 to 1.10.36. **`VUE_ENSEMBLE.md`** / `OVERVIEW.md`, **`README.fr.md`** / `README.md`, **`INDEX.md`** (fr and en): the radio in the feature list and the index. **`docs/samples/README`**: zones row; `dance-floor` sample → `https://ADRESSE/flux` (rule 18: no real address any more).
- **Code** (texts only): the "Radio" line says "stream **refused or** unreadable" (the browser does not tell a 403 from an unknown format); server log: "no title: empty title in the stream (the radio does not write its titles in it)" instead of an empty cause (`py.presence.radio.empty`).
- **Checked**: `verif_trad.py` on the nine pairs touched (0 errors; `README.fr.md` / `README.md` keeps its 3 errors already present on `main`, `docs/fr/…` links without counterpart); tests `i18n`, `samples`, `zone_cast`, `radio_titre`, `dist_a_jour`, `smoke`, `readme_liens`, `lien_image`, `build_reference`. Per-file numbers after the build: `index.html`, `carte.html`, `glb-viewer.html`, `glb2html.py` and `presence_server.py` take 1.10.36.
- **Klaatou's finding** (14/11/2026): with a radio that writes its titles in the stream and its address in `presence_radios.json`, the line does give "♪ Radio: NAME — Artist – Title" in the demo (Edge, Windows).
- **Not tried**: the full suite. **Remaining**: the demo (`index.html`, `carte.html`, `glb-viewer.html`, `glb2html.py` change), `presence_server.py` on the VM (log texts only); `REPRISE.md` (rule 23).

### 14/11/2026: server: `KeyError` on two simultaneous disconnections; radio title log; cone by default on a radio zone (batch 1.10.35)

- **`KeyError: 'ROOM'`** (Klaatou's finding when stopping the server with Ctrl+C, "connection handler failed" trace): `handler`, `finally` block: between `ROOMS[room].pop(peer.id)` and `if not ROOMS[room]`, the `await broadcast(...)` lets another visitor's `finally` run, which empties and **deletes** the room; on return, `ROOMS[room]` no longer exists. Present since empty rooms are deleted; no consequence for visitors (it only happens on simultaneous disconnections). Fix: `ROOMS.get(room)` and `ROOMS.pop(room, None)`.
- **Title log** (`presence_server.py`): "radio" lines: "title asked for URL" or "address not in --radios, no title: URL" at each request of a page; "title “…”" at each change, or "no title: CAUSE" (stream without ICY metadata with the `icy-metaint` value, stream cut before the block, block without `StreamTitle`, or the exception with its message). `radio_title_sync` returns `(title, cause)`.
- **Cone by default** on a radio zone (`core.js` `cleanZone` and `coneFor`, `gen_tpl.py`): a radio without a marker was seen by nobody (Klaatou's finding); `cone: false` removes it; the viewer offers the choice (auto / always / never) on the zone's card.
- **Check**: `tests/radio_titre.py`: log lines (request, two titles, not listed) and six simultaneous disconnections (on the 1.10.34 code: `KeyError: 'r2'` three times; with the fix: nothing); `tests/zone_cast.py`: cone of both radio zones, no cone for the click url zone; also pass `i18n`, `zones_url_cone`, `samples`, `dist_a_jour`. Per-file numbers after the build: `index.html`, `glb-viewer.html`, `glb2html.py` and `presence_server.py` take 1.10.35 (`carte.html` does not change).
- **To do on the VM**: `scp` of `dist\presence_server.py`, restart (`systemctl restart web3d-presence`); then, entering the demo's zone, read the "radio" lines of the console.
- **Not tried**: a real stream from the server; Windows, Edge; the full suite.
- **Still to update** (rule 16): as batches 1.10.32 and 1.10.34 (manual § 5: default cone of a radio zone; § 10: "radio" log lines); the demo; `REPRISE.md` (rule 23).

### 14/11/2026: radio zones: the track title, read in the stream by the presence server (batch 1.10.34)

- **Done, server** (`src/presence_server.py`): option **`--radios FILE`** (JSON list of the allowed stream addresses; reread when the file changes; missing or unreadable: no title) and `--radios-every N` (seconds between two readings, 30 by default, 5 at least). The server **never queries any other address** than those of the file (a page cannot make it read anything). The title is read **in the stream** (`radio_title_sync`: `Icy-MetaData: 1` header, `icy-metaint` bytes skipped, `StreamTitle='…';` block, then close: ~16 KB per reading, 1 MB of `icy-metaint` at most): Icecast and SHOUTcast, no status address needed. One reading per stream every N s **while a visitor listens to it** (all rooms together), stop otherwise. Messages: the page sends `{t:"radio", url}` (empty url on leaving; one request per second at most), the server answers `{t:"radio", url, title}` at once then at every change; address not in the list: answer without `title`. Start-up line "radio titles for N address(es)" or "no radio titles". Example `docs/samples/presence_radios.sample.json` (samples README, French and English).
- **Done, page** (`src/core.js`: `radioAsk(url)`, `onRadio`, `radio` message, asked again on reconnection; `src/template.html`: `RADIO.title`): the line becomes "♪ Radio: NAME — Artist – Title" while the stream plays; without a server, without `--radios`, address not in the list or stream without metadata: NAME only.
- **Texts** (`src/i18n`, fr and en): `py.presence.help.radios`, `py.presence.help.radios_every`, `py.presence.radios_on`, `py.presence.radios_off`, `py.presence.radios.missing`, `py.presence.radios.bad`.
- **Check**: new `tests/radio_titre.py` (local fake Icecast server that interleaves the metadata only with `Icy-MetaData: 1`, real presence server with `--radios` and `--radios-every 5`, page with two radio zones): no reading before entering, name then title in the line, reading with the header, title change followed, readings stop outside the zone, address not in the list: stream played without title, no JavaScript error; `tests/samples.py`: 14 samples. Also pass: `zone_cast`, `i18n`, `samples`, `dist_a_jour`, `v36`, `correctifs_v52`, `v51_vides`, `v52_http`, `http_proxy`, `python_recent`, `aide_sans_pause`. Per-file numbers after the build: `index.html`, `glb-viewer.html`, `glb2html.py` and **`presence_server.py`** take 1.10.34 (`carte.html` does not change); `docs/REFERENCE_OPTIONS.md` is remade by `build.py` (two more options: to commit with the batch).
- **To do on the VM**: `scp` of `dist\presence_server.py`, a `presence_radios.json` next to it with the demo's stream addresses, `--radios presence_radios.json` in `lance_presence.sh`, restart of the `tmux` session.
- **Not tried**: a real Icecast or SHOUTcast stream from the server (not reachable from here); a SHOUTcast v1 server (`ICY 200 OK` answer: `urllib` refuses it, the title stays empty, the stream still plays); Windows, Edge; the full suite.
- **Still to update** (rule 16): manual (§ 10: `--radios`, `--radios-every`, the `radio` protocol; § 5 and § 7 with batch 1.10.32), `PROCEDURES.md` § 11 (`lance_presence.sh` line), `REFERENCE_JSON.md` (`presence_radios.json`), histories; the demo (`index.html`, `glb-viewer.html`, `glb2html.py` change); `REPRISE.md` (rule 23).

### 14/11/2026: radio zone: the cause of an unreadable stream in the "Radio" line, retry on coming back into the zone (batch 1.10.33)

- **Finding** (Klaatou): the same radio zone plays on a page served locally and says "stream unreadable" on the demo (GitHub Pages), while the stream opens in a tab. The page dropped the cause of the `<audio>` `error` event; a failed zone stayed blocked until the page was reloaded.
- **Done** (`src/template.html`, `RADIO`): the line "♪ Radio: NAME: stream unreadable (CAUSE)" and the message give the code (`MEDIA_ERR_ABORTED`, `MEDIA_ERR_NETWORK`, `MEDIA_ERR_DECODE`, `MEDIA_ERR_SRC_NOT_SUPPORTED`) and the browser's message; the diagnostic includes the line. `https` page with an `http:` stream: the page says so (`page.radio.mixed`) instead of letting the browser refuse silently. A zone's cause is forgotten when leaving its range: the stream is tried again on return. Viewer: "Try the stream" also gives the code and the message.
- **Check**: `tests/zone_cast.py`: the line contains `MEDIA_ERR_`, leaving the failed zone, return: a new request to the server (request count); `i18n`, `dist_a_jour`. Per-file numbers after the build: `index.html`, `carte.html`, `glb-viewer.html` and `glb2html.py` take 1.10.33, the others keep theirs.
- **Not tried**: the demo case itself (not reachable from here: the line will tell the cause); mixed content (no `https` page in the sandbox); Windows, Edge.
- **Still to update** (rule 16): as batch 1.10.32; the demo (`index.html`, `carte.html`, `glb-viewer.html`, `glb2html.py` change); `REPRISE.md` (rule 23).

### 14/11/2026: radio zones: an Icecast / SHOUTcast stream plays while walking within range (batch 1.10.32)

- **Done**: new zone type **`cast`** (`src/core.js`, `src/gen_tpl.py`, `ZONE_TYPES`): `target` = stream address (`https://` preferably: an `https` page refuses an `http` stream), `radius` = range (0.5 to **200 m**; the other types stay at 50), ring on the ground; no click, no "E" prompt, no link to an element, no cone. While walking, `zoneTick` keeps the nearest radio zone within range (in x and z; from 4 m below the zone to 8 m above) and its gain `1 - distance / range` (0.05 at least), and calls `onCast(zone, gain)` at every change; `null` out of range, in global view and when the zones are reloaded.
- **Page** (`src/template.html`, `RADIO`): a single `<audio>` (`preload="none"`), created when first needed; volume = gain x the **Sounds** volume of Settings; out of range or in global view the stream is **stopped** (`src` removed: no longer downloaded); as the browser only allows sound after an action by the visitor, the line says "click or press a key to hear it" and the stream starts at the first action. New **"♪ Radio: NAME"** line in the state block (connecting…, sound off in Settings, stream unreadable; the diagnostic includes it); an unreadable stream (format, network, 404) is reported once (line and message) and the zone is not tried again until the page is reloaded. Settings: the **"Sounds"** box and the volume now exist **without a presence server** (the mention, message, arrival and departure boxes stay tied to the server); new **"Zone radio"** box (checked, remembered: `radio` in `glb2html_visitor`).
- **Viewer** (`src/viewer_tpl.html`): "Radio" type in the list, "Stream address" field, **"Try the stream (5 s)"** button (`castTry`), "Range" field; the radio **does not play** while walking in the viewer (decision: the test only). Example: `dance-floor` zone in `docs/samples/region.zones.sample.json` (SomaFM stream, Creative Commons).
- **Texts** (`src/i18n`, fr and en): `core.kind.cast`, `page.opt.sound.radio`, `page.radio.*`, `viewer.kind.cast`, `viewer.zone.t.cast`, `viewer.zf.cast*`, `viewer.zf.r.cast`.
- **Check**: new `tests/zone_cast.py` (WAV stream served locally: the sandbox Chromium has no MP3 decoder): ranges, type kept, Settings boxes without presence, nothing in global view nor out of range, "click or press a key" line before the first action, start after a key, volume 0.45 at the centre and nearly nil at the edge, stop on leaving, second zone, box unchecked / rechecked, volume at 100, unreadable stream, back to global view, no JavaScript error; `tests/samples.py`: 9 sample zones. Also pass: `i18n`, `samples`, `dist_a_jour`, `smoke`, `zones_url_cone`, `zones_numeros`, `v36` (sounds), `chat_bip`, `image_zone`, `v34`, `version_page`, `marque`. Per-file numbers after the build: `index.html`, `carte.html`, `glb-viewer.html` and `glb2html.py` take 1.10.32, the others keep theirs.
- **Tried by Klaatou** (14/11/2026, outside the page): an Icecast stream (SomaFM, `audio/mpeg`, HTTP 206) played in Edge on Windows by an `<audio>` tag; the server's `/7.html` status gives the track title.
- **Not tried**: Windows, Edge, Firefox, Safari; a real Icecast or SHOUTcast stream in the page (not reachable from the sandbox); a SHOUTcast v1 server (`ICY 200 OK` answer, which browsers sometimes refuse); the track title (next batch: through the presence server); the full suite.
- **Still to update** (rule 16): manual (§ 5: the radio zone; § 7: the "Radio" line of the state block and the Sounds / Zone radio boxes of Settings without presence; appendix § 13), `REFERENCE_JSON.md` (type `cast`, range 200), `docs/samples/README.md` and `README.fr.md` (line of `region.zones.sample.json`), procedures, histories, in French and in English; the demo (`index.html`, `carte.html`, `glb-viewer.html`, `glb2html.py` change); `REPRISE.md` (rule 23).

### 14/11/2026: launcher without a Folder button for a single file; `websockets` 16 tests (batch 1.10.31)

- **Launcher** (`tools/web3d_gui.py`): `--water-from` (metavar `OAR`), `--terrain-only` and `--tex-only` (metavar `GLB`) always name **one** file: `fichier_seul` removes their Folder button (outputs, `convoar` and the other path fields keep File and Folder). `tests/gui.py`: one more check; opposite direction (`fichier_seul` always false): one failure.
- **`websockets` 16 tests** (Klaatou's finding, `websockets` 16.0, suite run): `v51_vides` and `v52_http` failed ("nothing to filter"), `http_proxy` skipped its checks. **Cause**: these three tests took `websockets` 16 for a version that no longer writes the trace of empty connections and HTTP requests; measured: **16.0 still writes it** (like 14 and 15), **17.4 no longer does**. The server is unchanged (it filters that trace, `aucune trace` already passed); the tests now take 14 to 16 as the old versions (`correctifs_v52`: message). Same failure on the `main` before 1.10.28 with 16.0: unrelated to batch 1.10.28. **Consequence**: `http_proxy` (last address of the header, batch 1.10.28) had never run with 16.0; it now runs and passes.
- **Documents**: manual sections 10.16, 10.18 and 10.24 (French and English): "14 to 16" instead of "14 and 15".
- **Check**: with `websockets` 16.0 then 17.4: `v51_vides`, `v52_http`, `http_proxy` pass; with 16.0: `correctifs_v52` passes; `gui`, `dist_a_jour`.
- **Not tried**: the window part of `tests/gui.py` (no tkinter in the sandbox); Windows; `websockets` 14 or 15 (`WS_OLD`); `presence_server.py` does not change (no `scp` to the VM).

### 14/11/2026: launcher: Browse buttons for the `OAR` and `GLB` parameters (batch 1.10.30)

- **Cause**: `web3d_gui.py` (`champs_depuis` for the field kind, and the row creation for the buttons) recognised a file only by a word of the metavar (`FILE`, `FOLDER`, `DIR`), `.html` / `.json` or two name lists. `--water-from` (metavar `OAR`), `--terrain-only` and `--tex-only` (metavar `GLB`) were not among them: text field without buttons. Two places decided separately, with the same criterion copied.
- **Done**: `metavar_chemin` (exact metavars `OAR`, `GLB`, `IAR` besides the words) and `a_boutons_fichier`, used in both places. `--lib-url` (metavar `PATH`, also accepts a web address) stays a text field.
- **Check**: `tests/gui.py`: three fields added to the expected fields and three checks (buttons on the three fields, `--lib-url`, `--title` and `--exclude` without buttons, no flag or number with buttons); opposite direction (`MV_CHEMIN` emptied): two failures; `dist_a_jour`.
- **Not tried**: the window part of `tests/gui.py` (no tkinter in the sandbox) and Windows.
- **Remains to update** (rule 16): nothing (manual section 3.9 describes the buttons in general); `REPRISE.md` (rule 23).

### 14/11/2026: documents for batch 1.10.28 (batch 1.10.29)

- **Done**: manual (French and English): section 10.19 (nickname registry bounded by `--max-names`, at most one nickname change every 2 s), section 10.24 (last address of the relay header with `--proxy-header`), additions row of section 13 (batches 1.10.18 to 1.10.29); `PROCEDURES.md` (Funnel, French and English: last address of the header); histories (batches 1.10.28 and 1.10.29). No code changes (`dist\` and `VERSIONS.json` identical).
- **Check**: `verif_trad.py` without error on the three touched pairs (manual, procedures, histories); `dist_a_jour`.
- **Remains to update** (rule 16): `REPRISE.md` (rule 23).

### 14/11/2026: presence server: bounded nickname registry, last address of the proxy header (batch 1.10.28)

- **`presence_server.py`** (`src/presence_server.py`, `Registry`, `Peer`, `remote_ip`, `empty_conn_ip`): (a) a script could register nicknames without end (any 16-character `uid` is "persistent", the `name` message had no minimum delay, and every new nickname rewrote `presence_identities.json`): new option **`--max-names N`** (default 10000; beyond, a newcomer keeps a suffixed, non-reserved name) and at most one nickname change every 2 s per connection; (b) with **`--proxy-header`**, the address kept is now the **last** one of the header (the only one written by the trusted relay: nginx, Caddy and Cloudflare append the client address to a header the client may have sent itself; `tailscale serve` overwrites it, so the demo VM was not affected). Before, a client could appear under any address in the log and bypass the per-address limit and the address bans.
- Tests: `tests/http_proxy.py` (last address), new `tests/presence_noms.py` (3 checks: nickname change rate, registry cap with `--max-names 3`, last address of the header on a WebSocket connection; all 3 fail on the original `main`, run with `SANS_MAXNAMES=1` since `--max-names` does not exist there).
- Texts: `py.presence.help.max_names` (fr, en). Remains to update: manual (section 10, `--max-names`, proxy header), `PROCEDURES.md` section 11 (nothing changes for the VM).

### 14/11/2026: documents for batches 1.10.18 to 1.10.26 (batch 1.10.27)

- **Done**: manual (French and English): command lines of § 3.1 and options of § 3.2 (`--tex-size`, `--tex-quality`, `--tex-only`, `--nopause` and `--output` completed), new § 3.12 (lightening the textures and reading their sizes) and new § 3.13 (the OAR's water level places the sea of the pages), § 9.19 (sea in tiles mode checked, slider start), `--update --water-from` line of the commands table, tiles index example (`waterHeight`) and default sea in tiles mode, appendix § 13 (line for batches 1.10.18 to 1.10.27); `REFERENCE_JSON.md` (`seaM`, `waterHeight`); `PROCEDURES.md` (useful keys); simple procedures § 12 (fix the sea of an already published region) and § 13 (lighten the textures); index (two lines); `CONVERTIR_OARS.md` and `CONVERT_OARS.md` (the sea); histories (batches 1.10.18 to 1.10.27).
- **Checks**: `verif_trad.py` without error on the seven pairs touched (manual, `REFERENCE_JSON.md`, `PROCEDURES.md`, simple procedures, index, `oars2site.py` manual, histories); a first version of the history had an error (a document name as inline code in French only), fixed. `apropos_liens` and `readme_liens` pass; `doc_options` fails as on `main` (same check: `REFERENCE_OPTIONS.md` is regenerated differently by the sandbox's Python 3.12; Klaatou's build redoes it). No code changes: `dist\` is not touched. The file names, values and results written in the documents come from the tests (fake convoar, hand-made GLBs, Chromium).
- **Not tried**: the PowerShell loop of § 12 of the procedures (marked "not tried" in the text); the "not tried" points of the documented batches (a real OAR, Windows, a real shop region).
- **Still to update** (rule 16): nothing known for batches 1.10.18 to 1.10.26; `REPRISE.md` (rule 23).

### 14/11/2026: automatic sea: the OAR's water level becomes the sea height of the pages (batch 1.10.26)

- **Finding** (Klaatou, about a region of an OAR shop whose sea cut through the buildings): a page's sea had no link with the region. `oar2glb.py` read the OAR's `WaterHeight` (20 by default) but only used it to colour the terrain; pages received a constant (`seaY` -50 for a single GLB, 20 in tiles mode), in the frame recentred by the viewer, whose shift depends on each region. The Settings "Sea height" slider is in the region's frame but belongs to each visitor; the config only had `seaY`, in the other frame: two frames for the same sea.
- **Done**: `oar2glb.py` writes into the GLB's `asset.extras` `waterHeight` (read from the OAR's `settings/*.xml`, otherwise 20) and `waterSource` (`oar` or `default`), prints "[water] region water level: N m (read in ...)" and, without `WaterHeight`, a warning. `glb2tiles.py` carries `waterHeight` into the tiles index. `glb2html.py`: new config key `seaM` (metres, region frame, -50 to 250, like the slider); without an explicit `--sea-y` or `--sea-m`, it is the water level of the GLB (or of the tiles index, where the old fixed 20 is now only a fallback); new options `--sea-m M` and `--water-from OAR` (reads an OAR's `WaterHeight`: to fix an already converted region with `--update`, without converting again); `--update` keeps `seaM`; `--update --sea-y` removes it (the sea goes back to the page's frame); the help of `--sea-y` says it is in the page's frame. The page (`template.html`): the Settings slider starts from `seaM` when the config has one; the visitor's choice replaces it; "Original values" goes back to it. Pages without `seaM` (all the old ones) do not change. Two texts for `oar2glb.py`, seven for `glb2html.py`, in French and English.
- **Not touched**: `glb-viewer.html` (its "sea" row stays `seaY`, the page's frame), `--sea-y` and `seaY` keep their meaning.
- **Checks**: new `tests/mer_auto.py` (34 checks, Chromium: water level written by `oar2glb.py` with and without `WaterHeight`, kept by `--tex-only`; carried by the tiles index; automatic `seaM`, absent with `--sea-y`, replaced by `--sea-m`; sea at `seaM` + the model's shift; starting slider, visitor's choice, "Original values"; old page unchanged; `--update --water-from`, `--sea-m`, `--sea-y`, and `seaM` kept by another `--update`; OAR without `WaterHeight` and a file that is not an OAR refused; tiles mode without shift; help in French and English). Opposite direction: eight defects introduced on purpose (the page ignores `seaM`, automatic sea disabled, explicit `--sea-y` without effect on the automatic one, `--update --sea-y` not removing `seaM`, tiles index without water level, `oar2glb.py` not writing it, tiles without water level, `--water-from` outside `--update`): the test fails each time; code restored. Also pass, after `build.py`: `mer_hauteur`, `modulaire`, `v32`, `v34`, `v35`, `samples`, `oar2glb`, `glb2tiles`, `pbr_oar`, `tex_size`, `tex_tableau`, `tex_seul`, `oars2site`, `tools_lang`, `textes_outils`, `i18n`, `marque`, `python_recent`, `gui`, `dist_a_jour`, `smoke`.
- **Not tried**: the shop's region itself (its config was not readable from here: the diagnosis comes from the code and from the `seaY: 20` it contains); a real OAR; Windows and Edge; `glb-viewer.html` does not use the automatic level yet; when the OAR has no `WaterHeight`, the sea stays at 20 with a warning (no estimate from the terrain); GLBs already made have no water level: `--update --water-from` fixes them.
- **Still to update** (rule 16): the manual (§ "Sea height (1.9.15)": `seaM`, `--sea-m`, `--water-from`, automatic sea; § `oar2glb.py`: the "[water]" line), `REFERENCE_JSON.md` (`seaM`), the tiles format (`waterHeight`), histories and procedures; `REFERENCE_OPTIONS.md` is regenerated by `build.py` (to commit with the batch); `REPRISE.md` (rule 23).

### 14/11/2026: `oars2site.py` copies `carte.html` and leaves no half-made folder (batch 1.10.25)

- **Finding** (Klaatou, comparing the produced site to his diagram): the produced site had no `carte.html` (the world map page), although `regions.json` was kept up to date; and, while looking, a `glb2html.py` failure left an empty region folder in the site.
- **Done**: at the start, `oars2site.py` copies `carte.html` (the one in the tools folder, `dist\`) to the root of the site if it is not there; a map already there is never overwritten; if the tools folder has no `carte.html`, a warning is shown and the conversion goes on; `--dry-run` announces the copy without writing anything. A new region whose `glb2html.py` fails no longer leaves a folder in the site. Removing the other mode (an old single GLB or old tiles) now happens after `glb2html.py` succeeds instead of before: a region already there whose conversion fails stays as it was (before, its GLB was deleted beforehand). Three more texts in French and English; the French and English manual completed.
- **Checks**: `tests/oars2site.py` extended (46 checks, 7 more: map copied, never overwritten, copied again if deleted, announced by `--dry-run`, tools without `carte.html`, failure on a new region with no folder left, failure on a region already there losing nothing). Opposite direction: map never copied, always overwritten, folder not cleaned after a failure, GLB deleted before success, removal of the other mode removed: one check fails each time; code restored. A first version of the failure check distinguished nothing (the refused option fails before any folder is created): it now causes the failure with a missing `three.js` (`--vendor` pointing to an empty folder) for a new region. Also pass: `tools_lang`, `textes_outils`, `i18n`, `marque`, `python_recent`, `gui`, `dist_a_jour`, `smoke`; `verif_trad.py` without error on the manual.
- **Not tried**: as for batch 1.10.24 (a real OAR with the real convoar; Windows; macOS; a large region through the tiles path; time and memory on real OARs; graphical launcher).
- **Still to update** (rule 16): the manual (§ 3.1, § 3.2, § 3.10: `--tex-size`, `--tex-quality`, `--tex-only`, `glb-stats.py`), histories and procedures for batches 1.10.19 to 1.10.25; `REFERENCE_OPTIONS.md` is regenerated by `build.py` (to commit with the batch); `REPRISE.md` (rule 23).

### 13/11/2026: new tool `oars2site.py`: a folder of OARs becomes a web site (batch 1.10.24)

- **Need** (Klaatou): an OAR shop would like to show its regions in the browser; for each OAR, `oar2glb.py`, `glb2tiles.py`, `glb2html.py` and the world map must be chained. The script, first written outside the repository, enters the repository with its manual.
- **Done**: new `tools/oars2site.py`, built into `dist\` with its own version number and mark like the other tools, messages and help in French and English in `src/i18n` (`--lang`). For each `.oar` or `.tgz` of a folder, one region after the other: `oar2glb.py`, `glb2tiles.py` (which decides by itself about tiles; `--split never` or `always` to force), `glb2html.py --shared-shell`, then `--scan-sites`. A region that is already done is skipped; a failure is noted without blocking the others; exit code 1 if a region failed; logs, work files and `conversion_report.json` outside the site. Options: `--only`, `--thumbs`, `--force`, `--reuse-glb`, `--keep-work`, `--work`, `--timeout-min`, `--vendor`, `--tools`, `--oar2glb-arg`, `--html-arg`, `--dry-run`; `--tex-size`, `--tex-quality` and `--pbr-size` are passed to `oar2glb.py`, whose version is checked (1.10.20 and 1.10.21); an old GLB or old tiles are removed from the site when the mode changes. The tools it runs speak the script's language. New documents `docs/fr/CONVERTIR_OARS.md` and `docs/en/CONVERT_OARS.md` (manual, with the warning: the published GLB can be downloaded); lines added in `README.md`, `README.fr.md`, `VUE_ENSEMBLE.md`, `OVERVIEW.md`, § 2 of the manual (French and English) and both indexes; `build.py`, `gen_reference.py` (`REFERENCE_OPTIONS.md`) and four tests (`marque`, `python_recent`, `textes_outils`, `tools_lang`) know the new tool.
- **Defect found by the test**: in `dist\`, the translation block is inlined as is and `_I18N` no longer exists; the script's language is therefore read by `langue_courante()`, valid from the sources and from `dist\`.
- **Checks**: new `tests/oars2site.py` (39 checks, on `dist\`, with a fake convoar: list without writing anything; four OARs including a name with a space, one that fails and one whose GLB already exists beside it; complete site; regions already done skipped; tiles then back to a single GLB without old files; thumbnails; `--tex-size` and `--tex-quality`; `--keep-work`; `--reuse-glb`; version check of `oar2glb.py`; time limit exceeded; languages; errors; `--version`; help). Opposite direction: six defects introduced on purpose (cleanup of old files, language not passed on, done regions not skipped, work folder kept, version check, exit code): the test fails each time; code restored. `verif_trad.py`: manual, indexes and overview without error; the README pair already had path errors specific to each language, the new line adds one of the same kind. Also pass: `tools_lang`, `textes_outils`, `i18n`, `marque`, `python_recent`, `gui`, `dist_a_jour`, `readme_liens`, `apropos_liens`, `smoke`, `tex_size`, `tex_tableau`, `tex_seul`, `oar2glb`, `pbr_oar`, `sortie_cp1252`, `aide_sans_pause`, `terrain`, `glb2tiles`.
- **Not tried**: a real OAR with the real convoar; Windows; macOS; a large region through the tiles path; time and memory on real OARs (a single measurement, by Klaatou under Windows: a 1.45 GB OAR in about 2 min 12 s with `--pbr-size 256`, memory rose to 61 GB, cause not established); the graphical launcher does not know the tool yet.
- **Still to update** (rule 16): the manual (§ 3.1, § 3.2, § 3.10: `--tex-size`, `--tex-quality`, `--tex-only`, `glb-stats.py`), histories and procedures for batches 1.10.19 to 1.10.24; `REFERENCE_OPTIONS.md` is regenerated by `build.py` (to commit with the batch); `REPRISE.md` (rule 23).

### 13/11/2026: `oar2glb.py --tex-only GLB`: lighten the textures of an existing GLB (batch 1.10.23)

- **Need** (Klaatou): to try several values of `--tex-size` and `--tex-quality` without redoing the OAR conversion (long on a large region), on an already built GLB.
- **Done**: option `--tex-only GLB` (like `--terrain-only`, but without an OAR: the parser no longer requires it, a clear message asks for it outside `--tex-only`): applies `--tex-size` and/or `--tex-quality` to the GLB's ordinary textures and writes a new GLB, `NAME-tex512.glb`, `NAME-q60.glb` or `NAME-tex512-q60.glb` beside the original, or the file given by `--output`; the original is never modified (an output identical to the original is refused). Each image is read then processed by the same function as during a conversion: same bytes as with the option given directly to the conversion (tested). The images of PBR materials (`pbr-…`) and those that are not in the file are not touched. The JSON and the geometry are kept; the binary data is copied in 8 MB pieces without loading the whole GLB; the modified images go through a buffer (in memory up to 256 MB, then on disk); offsets stay aligned on 4 bytes; the `EXT_meshopt_compression` zones of buffer 0 are copied and re-pointed. No file is written if nothing changes. Prints the original size table (batch 1.10.22), then "N of M changed: A MB -> B MB; GLB: X MB -> Y MB (duration)". No final pause (like `--terrain-only`). Help and example in French and English.
- **Effect to know**: the OAR became an optional argument for the parser; the graphical launcher therefore no longer marks it as required (a clear message is shown if it is forgotten).
- **Checks**: new `tests/tex_seul.py` (48 checks: size, quality, both; same image bytes as the direct conversion; JSON unchanged apart from offsets and MIME types; geometry copied identically; original intact; valid GLB; `--output` and refusal; hand-made GLB with a PBR image, an image outside the file, two images on one view, a 61-byte view and meshopt zones; nothing to change; reading in 777-byte pieces; invalid or truncated files; Pillow missing; help). Opposite direction: geometry shifted (failure), PBR images not excluded (2 checks fail), MIME type not updated (4), alignment removed (failure), meshopt zones ignored (1); code restored. Also pass, after `build.py`: `tex_tableau`, `tex_size`, `oar2glb`, `pbr_oar`, `i18n`, `tools_lang`, `aide_sans_pause`, `sortie_cp1252`, `textes_outils`, `python_recent`, `gui`.
- **Not tried**: a real OAR with the real convoar; Windows; time and memory on a real GLB of several hundred MB or GB with thousands of images (not measured; the tool prints the duration); the graphical launcher on screen; GLBs really compressed with Draco or meshopt (only hand-made GLBs were used).
- **Still to update** (rule 16): the manual (§ 3.1, § 3.2, § 3.10; `--tex-only`), histories, procedures; `REFERENCE_OPTIONS.md` is regenerated by `build.py` (to commit with the batch); `REPRISE.md` (rule 23).

### 13/11/2026: texture size table, in `oar2glb.py` and `glb-stats.py` (batch 1.10.22)

- **Need** (Klaatou): to choose the value of `--tex-size` without trial and error and without knowing the original size of the textures; no tool gave their size in pixels (`glb-stats.py` only gave their weight).
- **Done**: at the end of each conversion, `oar2glb.py` prints the number and weight of the ordinary textures by longest-side range (up to 256 px, 257 to 512, 513 to 1024, 1025 to 2048, over 2048; unread sizes apart), with the largest side and the total weight. These are the original sizes, before any reduction by `--tex-size` or `--tex-quality`; the reduction report ("N of M reduced") follows. `glb-stats.py` gives the same table for an existing GLB, with the images of PBR materials (`pbr-…`) apart (`--tex-size` does not touch them). Sizes are read from the image headers (PNG, JPEG, GIF, BMP), without decoding them and without Pillow; this reading code is duplicated in both tools (keep it identical; a test compares their results). `glb-stats.py` therefore now reads the start of each image: its description (file header, help in French and English) no longer says "only the JSON header".
- **Checks**: new `tests/tex_tableau.py` (27 checks: PNG, JPEG including progressive and with large segments before the size, GIF, BMP; unknown or truncated bytes; range limits; a hand-made GLB with ordinary images, an image outside the GLB and an image of a PBR material; full conversion with a fake convoar, with and without `--tex-size`, and without Pillow; `glb-stats.py` help). Opposite direction: the `oar2glb.py` table emptied (4 checks fail), lower limit shifted (1), JPEG segment reading broken (failure), PBR images not separated (3); code restored. `tests/tex_size.py`: one check adapted (the table now prints a "textures" line at every conversion). Also pass, after `build.py`: `tex_size`, `oar2glb`, `pbr_oar`, `i18n`, `tools_lang`, `aide_sans_pause`, `sortie_cp1252`, `textes_outils`, `python_recent`, `glb2tiles`, `terrain`, `gui`.
- **Not tried**: a real OAR with the real convoar; Windows; how long reading the image headers takes on a GLB of several GB with thousands of images (not measured); images of a GLB that are not in the file (address or `data:`): their size is shown as "not read".
- **Still to update** (rule 16): the manual (§ 3.1, § 3.2, § 3.10; `glb-stats.py`), histories, procedures; `REFERENCE_OPTIONS.md` is regenerated by `build.py` (to commit with the batch); `REPRISE.md` (rule 23).

### 13/11/2026: `oar2glb.py`: independent `--tex-size` and `--tex-quality`, help rewritten (batch 1.10.21)

- **Finding** (Klaatou): the help of `--tex-size` gave neither the possible values of N nor the consequence on quality; and `--tex-quality` only acted on textures reduced by `--tex-size`, without saying so: alone, it did nothing. Yet compressing without changing the dimensions is a separate setting.
- **Done**: the two options are independent. `--tex-size N` changes the number of pixels (0 = nothing, otherwise 16 to 8192). `--tex-quality Q` (1 to 95) compresses as JPEG without changing the dimensions. Alone, `--tex-quality` recompresses every opaque texture; a texture whose compressed version is not lighter keeps its original bytes. With both: textures that are too large are reduced then compressed at the requested quality, the other opaque textures are recompressed. A transparent texture stays PNG: reduced if it is too large, never recompressed. With `--tex-size` alone, the quality is 85, as in batch 1.10.20.
- **Behaviour change from 1.10.20**: `--tex-quality` alone had no effect, it now recompresses; with both options, opaque textures smaller than N are now recompressed (before, only reduced textures were).
- **Help**: rewritten in French and English (values of N with examples, range of the quality, effect on weight and look, transparent textures, PBR textures); the report has one message per case (size alone, quality alone, both); the Pillow error message names both options.
- **Checks**: `tests/tex_size.py` adapted and extended (51 checks: size alone, quality alone, both; the original kept when recompression does not lighten; transparent texture never recompressed; packing and full conversion; refused values; Pillow missing; the help gives 0, 16 to 8192 and 1 to 95). Opposite direction: quality alone made a no-op (10 checks fail), the keep-the-original guard removed (1), recompression of transparent textures allowed (5); code restored. Also pass: `oar2glb`, `pbr_oar`, `i18n`, `tools_lang`, `aide_sans_pause`, `sortie_cp1252`.
- **Not tried**: a real OAR with the real convoar; Windows; the weight saved by quality alone on real textures (not measured); the look in the page; time and memory with thousands of textures.
- **Still to update** (rule 16): the manual (§ 3.1, § 3.2, § 3.10, appendix § 13), histories, procedures; `REFERENCE_OPTIONS.md` is regenerated by `build.py` (to commit with the batch); `REPRISE.md` (rule 23).

### 13/11/2026: `oar2glb.py --tex-size`: reduce the GLB's ordinary textures (batch 1.10.20)

- **Need** (an OAR shop that wants to show its regions in the browser): the page downloads the GLB, so anyone who opens the page can save it with its textures; no tool could reduce ordinary textures (`--pbr-size` only touches PBR textures). This does not protect the geometry; it makes the GLB lighter (not measured) and the textures less useful to whoever downloads it.
- **Done**: two options in `oar2glb.py`. `--tex-size N` (default 0: nothing changes): an ordinary texture whose longest side exceeds N pixels is reduced when the GLB is packed, keeping its proportions; JPEG, or PNG if it has transparency (foliage, grilles: they stay cut out); a texture that is already small enough or unreadable keeps its original bytes. `--tex-quality Q` (1 to 95, default 85): JPEG quality. N must be 0 or between 16 and 8192; Pillow is needed (clear message before any conversion if it is missing). The report says how many textures were reduced and the weight before and after. PBR textures are not concerned (`--pbr-size`).
- **Checks**: new `tests/tex_size.py` (30 checks: reduction of a large opaque texture and of a large texture with transparency, palette with transparency, fully opaque RGBA, small texture and unreadable bytes unchanged, packing with and without reduction, full conversion with a minimal OAR and a fake convoar, refused values, Pillow missing). Opposite direction: transparency lost on purpose, then the reduction removed on purpose: 6 checks fail each time, code restored. Also pass: `oar2glb`, `pbr_oar`, `i18n`, `tools_lang`, `aide_sans_pause`, `sortie_cp1252`.
- **Not tried**: a real OAR with the real convoar; Windows; time and memory with thousands of textures (not measured); how the reduced textures look in the page; how the two options appear in the graphical launcher (it reads `oar2glb.py`'s parser).
- **Still to update** (rule 16): the manual (`oar2glb.py` options), procedures, histories; `REFERENCE_OPTIONS.md` is regenerated by `build.py` (to commit with the batch); `REPRISE.md` (rule 23).

### 13/11/2026: test of the viewer's zone editor, Trigger and Cone menus (batch 1.10.19)

- **Finding**: the viewer's zone editor (`glb-viewer.html`) has offered, for a `url` zone, a "Trigger" menu (`trigger`) and a "Marker (cone)" menu (`cone`) since batch 1.10.16; no test ran them ("not tried" in the 1.10.16 entry).
- **Done** (test only: no code changes, `dist\` and `VERSIONS.json` identical): new `tests/editeur_cone.py` (headless Chromium). A zone opened by clicking its title, as with the mouse: "on click" + cone "always" gives `trigger` `click` and `cone` `true`; "when walking into it" + "never" gives `enter` and `cone` `false`; "depending on the trigger" removes the `cone` key; "both" is saved. The viewer shows no cone at all (editor mode, intended since v36: `coneFor` returns false while the editor is active): checked. End to end: the zones the editor outputs, given to `glb2html.py`, give a page with the cone of the "on click + always" and "when walking into it + depending on the trigger" zones, and without the cone of "when walking into it + never" and "on click + depending on the trigger". No JavaScript error.
- **Checks**: the test passes on `main`; opposite direction: the Cone menu broken on purpose in a copy of `dist\glb-viewer.html` (it no longer writes `cone`): 3 checks fail, copy restored. `smoke` and `dist_a_jour` pass. Klaatou also saw the `url` zone with a cone and `hop://` work on his side (demo and local), and `zones_url_cone.py` pass on Windows, in Edge and in Comet.
- **Not tried**: Windows, Edge, Firefox, Safari for `editeur_cone.py` itself (Chromium on Linux only); an https `url` zone triggered by walking into it (the browser may block opening a tab without a click).
- **Still to update**: nothing for this batch; `REPRISE.md` (rule 23): the "`therejs` topic" line of § 6.2 is wrong (fixed on GitHub), to remove at the next handover.

### 13/11/2026: tests `v35` and `v36`: wait for the state instead of a 300 ms pause (batch 1.10.18)

- **Finding**: `tests/v35.py` failed intermittently on "a second click expands them" (about one run in three or four in the sandbox, including on the original `main`; seen once during batch 1.10.16). The page was not at fault.
- **Cause**: with the mouse, the title of a collapsible panel acts only 250 ms after the click, so that a double-click does not collapse it (`template.html:1167`); the test waited a fixed 300 ms and then read the state. On the software-rendered Chromium the page can act later: the test read too early. Measured on the isolated section: when the failure happens, the two clicks are 360 ms apart, the browser counts 1 for each (no double-click, no `dblclick`), and a read 1.5 s later shows both panels expanded. Same defect as batch 1.7.13 (fixed pause instead of waiting for the condition).
- **Done** (tests only: no code changes, `dist\` and `VERSIONS.json` identical): an `attendre` function in `tests/v35.py` and `tests/v36.py` waits for the wanted state (8 s at most; if the condition does not come, the check that follows fails as before) in place of the six 300 ms pauses: three in `v35.py`, three in `v36.py` (same class of defect).
- **Checks**: isolated section of `v35` (up to "a second click expands them") rerun 8 times: 8 passes; before the fix, about 3 failures in 4 runs. Full `v35`: 2 passes, everything passes; full `v36`: 2 passes, everything passes. Opposite direction: with the page's collapse deliberately broken (temporary trial, restored to the state of `main`), `v35` fails on the collapse (three checks), so the test still detects a real defect. `dist_a_jour` passes, build with `--vendor`: `dist\` and `VERSIONS.json` unchanged.
- **Not tried**: Windows, Edge. The same pattern (fixed pause) may exist in other tests; only those carrying the comment "v41: with the mouse, the title collapses 250 ms after the click" were fixed (search in `tests/`).

### 13/11/2026: documents for batch 1.10.16; Sandbox_BMoG demo announced (batch 1.10.17)

- **Asked by Klaatou** (batch 1.10.16 works on his side): bring the documents up to date, with the presentation of the Sandbox_BMoG demo.
- **Done** (documents only: no code changes, `dist\` and `VERSIONS.json` identical, no built file changes number):
  - `MANUEL.md` and `MANUAL.md`: § 5.7.1 (a web link zone also fires when you walk onto it; for a `hop://`: same tab, browser confirmation; a web address opens in a new tab that the browser may block for lack of a click, **not tried**), § 5.8 (trigger: portals and web links), E and T keys and the gestures table, § 7.17 (`cone` key per zone, editor list), the additions-after-1.10.0 table;
  - `PROCEDURES.md` § 13 (set "Trigger" to "both" or "walking into it"); `VUE_ENSEMBLE.md` and `OVERVIEW.md`, `README.fr.md` and `README.md`: the Sandbox_BMoG demo (a region of the BloodMoon Pack OpenSim grid, thanks to Vlad; OpenSim 0.9.3 PBR materials and their new lighting; `hop://` jump circle to the same region in the grid); `HISTORIQUE.md` and `HISTORY.md`: batches 1.10.16 and 1.10.17.
- **Checks**: `verif_trad.py` on the four modified pairs (manual, procedures, history, overview): 0 errors, and the same number of warnings as `main` before the batch; passing: `readme_liens`, `apropos_liens`, `lien_image`, `i18n`, `marque`, `dist_a_jour`; build with `--vendor`: `dist\` and `VERSIONS.json` unchanged; `docs/REFERENCE_OPTIONS.md`, rewritten by the sandbox build, restored to the state of `main`. `git grep` for forbidden names (rule 25): none.
- **Not tried**: how the new paragraphs render on GitHub; `doc_options` (it fails in the sandbox with or without this batch).
- **Still to update**: the demo (`index.html`, `glb-viewer.html`, `glb2html.py` from batch 1.10.16 to copy into the demo repository, Sandbox_BMoG's `zones.json` as `url` / `both`); `REPRISE.md` (rule 23).

### 13/11/2026: "link" zones triggered by walking onto them; marker (cone) adjustable zone by zone, `cone` key (batch 1.10.16)

- **Asked by Klaatou**: a ring zone that opens a `hop://` to the OpenSim region (the sandbox demo), triggered **also by walking onto it**, with the marker cone above it, **adjustable zone by zone in the JSON** (not only with the T key).
- **Finding**: his zone (type `portal` with a `link` key) did nothing: `link` is read only for the `image` type (`core.js:1960`), and a portal does not read `hop:` (`okUrl`). With the `url` type and the `hop://` in `target`, click and E worked, but walking onto it did not: `trigger` was forced to `click` for every type other than `portal` (`core.js:1959`, `gen_tpl.py:205`), entering a zone counted only for `portal` (`core.js:1286`, `1335`, `2446`), and the cone existed only for a portal or a trigger other than `click` (`core.js:1987`).
- **Done**:
  - a `url` zone accepts `trigger`: `click` (as before), `enter` or `both`; the address then opens when you walk into the zone (a `hop://` in the same tab: the browser asks for confirmation); `ha` stays always on click;
  - optional **`cone`** key (`true` or `false`): `true` puts a cone even on an "on click" zone, `false` never puts one (even on a portal), absent: as before (cone for a portal or an `enter` / `both` trigger); the T key still hides all cones; the key is written only when it is `true` or `false`; no effect on an arrival (`--show-spawns`) or a picture;
  - viewer editor: a "Trigger" list for `url` zones, and a "Marker (cone) above the zone" list (follows the trigger / always / never); French and English texts;
  - `docs/fr/REFERENCE_JSON.md` and `docs/en/REFERENCE_JSON.md`: `trigger`, new `cone` row, `zoneCone`.
- **For Klaatou's zone**: `"type": "url"`, `"target": "hop://…"`, `"trigger": "both"` (or `"enter"`), `"shape": "ring"`, and `"cone": true` for the cone whatever the trigger; remove `link`.
- **Checks**: new `tests/zones_url_cone.py` (8 checks: trigger kept, `ha` on click, `cone` key, list of cones, walking into a `both` `url` zone opens the `hop://` in the same tab, E on an on-click `url` zone, walking through it does not open it); on the original `main` 4 checks fail, with the fix everything passes. Also passing: `smoke`, `i18n`, `samples`, `dist_a_jour`, `marque`, `version_page`, `portail_interne`, `image_zone`, `v36`; `verif_trad` on `REFERENCE_JSON`: 0 errors. `v35`: one failure ("a second click expands them") on one run, absent on the rerun, and present on the original `main`: unstable, unrelated to this batch. Full suite not run. Per-file numbers: `glb2html.py`, `index.html` and `glb-viewer.html` take 1.10.16; `carte.html`, `presence_server.py` and the others keep theirs (nothing to send to the VM).
- **Not tried**: Windows, Edge; the viewer editor (the two lists); a real OpenSim viewer registered for `hop://`.
- **Still to update** (rule 16): the manual (`url` zones: trigger, cone; § 5 and the T key), `HISTORIQUE.md` / `HISTORY.md`; the demo (`index.html`, `glb-viewer.html`, `glb2html.py` change); `REPRISE.md` (rule 23).

### 13/11/2026: documents brought up to date for batches 1.10.13 and 1.10.14; image of the eight shortcuts (batch 1.10.15)

- **Requested by Klaatou**: bring the documents up to date (rule 16); his screenshot of the Windows desktop shows the eight shortcuts, the launcher window with its icon and the "Function" line.
- **Done** (documents only: no code changes, `dist\` and `VERSIONS.json` identical, no built file changes its number):
  - `MANUEL.md` and `MANUAL.md`: § 3.9 (the image caption, and "Tried by Klaatou on Windows" for the window icon, `glb-stats`, the "Function" line and the eight shortcuts); § 7.62 (removing the icon: `--no-credit`, `--update`, `--map-page`, the `regions.json` header, the footer link of the map that stays); § 7.65 (the sea is no longer counted); § 10.3 (nicknames of visitors who stayed in global view, not reserved; a visit is only written when it ends; the loop of `lance_presence.sh` keeps its command line: restart the `tmux` session); § 13;
  - `REFERENCE_JSON.md`: `credit` key of the configuration and of the `regions.json` header; `CREATORS.md`; `PROCEDURES.md` (§ 11: `--visits-names` in both start lines and in "The author's choice"; the map key does not enter the repository); `SIMPLE_PROCEDURES.md` and `PROCEDURES_SIMPLES.md` (caption); `INDEX.md`; `HISTORY.md` and `HISTORIQUE.md` (batches 1.10.13 to 1.10.15);
  - **image** `docs/images/raccourcis.png`: replaced by Klaatou's screenshot, cropped to the eight desktop icons (delivered separately, outside the patch).
- **Check**: `verif_trad.py` on the seven modified pairs (manual, procedures, simple procedures, index, history, creators, JSON reference): 0 errors, as before the batch; build with `--vendor`: `dist\` and `VERSIONS.json` unchanged; `readme_liens`, `apropos_liens`, `lien_image`, `i18n`, `samples`, `dist_a_jour`, `marque` pass; `doc_options` not run (it fails in the sandbox with or without the document batches); `docs/REFERENCE_OPTIONS.md`, rewritten by the sandbox build, put back to the state of `main`.
- **Not tested**: how the new paragraphs render on GitHub; the taskbar (the window icon is only seen in the title bar).
- **Still to update**: the demo (batches 1.10.13 and 1.10.14 change `index.html`, `carte.html`, `glb-viewer.html`, `glb2html.py`); `REPRISE.md` (delivered at the resumption, rule 23).

### 13/11/2026: reflections: the sea is no longer counted as a metallic material (batch 1.10.14)

- **Reported by Klaatou** (screenshot and diagnostic of the `ShowRoom3D` demo, page 1.10.11): the page offers the reflections ("This region contains 1 metallic (PBR) material") although the region has no PBR (it predates the PBR extraction). The diagnostic says "Metal reflections: 0 % ; metallic materials loaded: 1 of 16, of which 0 with reflections".
- **Cause** (`src/core.js`, `metalInfo`): the count walks the whole scene, **sea included**. When the sea is a standard material it has `metalness: 0.1` (`core.js:444`), above the `METAL_MIN` threshold of 0.05: it counted as a metal, and the page offered reflections on any region with a sea. The tests of batches 1.10.7 to 1.10.11 were all made with `--no-sea`: they could not see it. Read in the package's `galerie.glb`: 15 materials, none with a `metallicFactor` above 0.05; with the sea, 16: consistent with "1 of 16" (the `ShowRoom3D` GLB itself was not read). The `pbrmat-…` name of a material (seen in the tooltip) is not written by any of our tools (code search): it does not prove the material is PBR.
- **Done**: `metalInfo` ignores the sea material (`m !== seaMat`): no false offer and no false diagnostic line; the region's materials are counted as before. The diagnostic total no longer counts the sea (here "0 of 15").
- **Check**: `tests/reflets_metal.py`: two pages with a sea (animated and not animated) and no metal at all: no offer, no metallic material counted, and the scene does contain a standard material with `metalness` above 0.05 (the sea). On the 1.10.13 code both checks fail, with the fix everything passes. `smoke`, `i18n`, `dist_a_jour`, `marque`, `version_page`, `image_diag`, `v39`, `v42`, `mer_hauteur` also pass. File numbers: `index.html`, `glb-viewer.html` and `glb2html.py` take 1.10.14; `carte.html` and `presence_server.py` keep 1.10.13 (nothing to send to the VM).
- **Not tested**: Windows, Edge; the `ShowRoom3D` region itself.
- **Still to update** (rule 16): manual § 7.65 (the count excludes the sea), in French and English; the demo (`index.html`, `glb-viewer.html` and `glb2html.py` change).

### 13/11/2026: visit log: nicknames of global-view visitors; `--no-credit` option (batch 1.10.13)

- **Requested by Klaatou**: (1) the visit log should show nicknames, including those of visitors who never went into walking mode (the log is not public); (2) a parameter to remove the "Made with Web_3d" icon at the bottom right.
- **Finding** (1): `--visits-names` already existed but only recorded walkers (`presence_server.py` sets `vname` when a visitor starts walking): a visitor who stayed in global view never had a nickname. The `lance_presence.sh` sent by Klaatou did not have the option at the start of the conversation. The log only writes a visit when it ends (disconnection): only visits that end after the restart have a nickname.
- **Done**:
  - **server** (`src/presence_server.py`): with `--visits-names`, the nickname the page of a global-view visitor sends in its `hello` is recorded (`clean_name`). It is **not reserved**: any browser can send one. If the visitor starts walking, the reserved nickname replaces it. Without the option nothing is recorded. Help text of `--visits-names` updated;
  - **`glb2html.py --no-credit`** (default `--credit`): the region configuration gets `"credit": false` and the page does not add the icon (`src/template.html`). The key exists **only** in that case: the sample configuration and `tests/samples.py` do not change. `--update --no-credit` writes it, `--update` without option keeps it, `--update --credit` removes it (`merge_maj_cfg`);
  - **map**: `--map-page FILE --no-credit` writes `credit: false` in the page configuration; the hosted map (`carte.html`) reads `"credit": false` at the root of `regions.json`, like `showUrl`;
  - the text link "Made with Web_3d" in the footer of the map stays (only the corner icon is removed); the chat and the button column keep their place (bottom right);
  - texts (`src/i18n`): `py.glb2html.help.credit` and `py.presence.help.visits_names`, in French and English.
- **Check**: `tests/v48.py`: a named spectator is recorded with `--visits-names` (fails on the 1.10.12 code) and is not recorded without the option; `tests/credit.py`: 10 checks added (page and map without icon, no JavaScript error, footer link of the map kept, `--update` in the four cases, `--map-page` with and without the option), 6 fail on the 1.10.12 code, all pass with the fix. `i18n`, `samples`, `smoke`, `dist_a_jour`, `marque`, `version_page`, `textes_outils`, `gui`, `v47`, `carte_pseudos`, `v52`, `python_recent` also pass. File numbers after the build: `index.html`, `carte.html`, `glb-viewer.html`, `glb2html.py` and `presence_server.py` take 1.10.13, the others keep theirs.
- **To do on the VM**: send `presence_server.py` from `dist\` with `scp`, then `systemctl restart web3d-presence` (without it, the VM server only writes the walkers' nicknames).
- **Not tested**: Windows, Edge, Firefox, Safari; how long the icon stays visible before it is removed when the configuration loads (not measured).
- **Still to update** (rule 16): manual (§ 10.3: visitors' nicknames; `--no-credit` and the `credit` key), `REFERENCE_JSON.md` (`credit` key of the configuration and of the `regions.json` header) and `CREATEURS.md`, in French and English; the demo (`index.html`, `carte.html`, `glb-viewer.html` and `glb2html.py` change).

### 13/11/2026: documents brought up to date for batches 1.10.3 to 1.10.11 (batch 1.10.12)

- **Requested by Klaatou**: bring the late documents up to date (rule 16), at the resumption of 13/11/2026.
- **Done** (documents only: no code changes, `dist\` and `VERSIONS.json` identical, so no built file changes its number):
  - `MANUEL.md` and `MANUAL.md`: § 3.9 (seven tools with `glb-stats`, the "Function" line, the window icon, eight shortcuts, the image caption, Python 3.10 to 3.14 and the 3.14 defect fixed in 1.10.4); no more "Enter" pause after `--help` (tables of `oar2glb.py` and `glb2tiles.py`); § 7.46 ("Original values"); § 7.53 (the diagnostic in a window); **new § 7.65** (metal reflections: slider, 0 % by default, the offer at 60 %, "Original values", the diagnostic line, cost, estimates); § 9.16 (the collapsed "Names key" block, a refused key no longer sent); § 13 ("Additions after 1.10.0" row);
  - `PROCEDURES_SIMPLES.md` and `SIMPLE_PROCEDURES.md` (§ 11: seven tools, image caption; names key), `PROCEDURES.md` (names key), `INDEX.md` (two lines), `HISTORIQUE.md` and `HISTORY.md` (one line);
  - in the English manual the slider and the button carry the name of the English interface ("Metal reflections", "Default values"); `HISTORY.md` still says "Original values" in the old batch 1.10.11 line, left as it is.
- **Check**: `verif_trad.py` on the five modified pairs (manual, procedures, simple procedures, index, history): 0 errors; the first try had two errors (`glb2html_opts_SALON` and `glb2html_metal_asked_SALON` written `ROOM` in English), fixed; build with `--vendor`: `dist\` and `VERSIONS.json` unchanged; `readme_liens`, `apropos_liens`, `lien_image`, `i18n`, `samples`, `dist_a_jour`, `marque` pass. `doc_options` fails (1 failure) with or without this batch: same result on the original `main` in the sandbox (Python 3.12 writes the `--x`/`--no-x` options differently); `docs/REFERENCE_OPTIONS.md`, rewritten by the sandbox build, was put back to the state of `main`. Facts quoted were re-read in `src/` (slider 0 to 200 in steps of 5, polled every 2 s for 60 tries, window 820 px and 90 % of the screen at most, text area height 80 % at most, browser keys) and in `tools/web3d_gui.py` (`for nom, fichier in OUTILS`, seven tools).
- **Not tested**: Windows (window icon, eight shortcuts: read in the code, not run); how the new paragraphs render on GitHub.
- **Still to update**: the image `docs/images/raccourcis.png` still shows seven shortcuts (the caption says so): a new screenshot is needed from Klaatou on Windows; the demo (`index.html`, `carte.html`, `glb-viewer.html`, `glb2html.py` have changed since 1.10.0).

### 12/11/2026: "Original values" also brings back the reflections offer (batch 1.10.11)

- **Reported by Klaatou**: after putting the reflections back to 0 % with the slider, the bar that spots the PBR metals does not come back, and he has no way to call it again.
- **Cause** (`src/template.html`): touching the slider counts as an answer and is remembered for the region (`glb2html_metal_asked_<region>`, batch 1.10.10), and nothing cleared it.
- **Done**: "Original values" (Settings) also clears this answer, puts the reflections back to 0 % and the page offers the reflections again at once if the region contains metals. No other manipulation in the browser.
- **Check**: `tests/reflets_metal.py` (section 8): after a slider setting, a reload without the bar, then "Original values": reflections at 0 %, answer cleared and the bar is back. On the 1.10.10 code this check fails, with the fix all pass. `mer_hauteur`, `v36`, `v36_lang`, `v42`, `v45_lib`, `v46`, `v52`, `smoke`, `samples`, `i18n`, `tuiles`, `dist_a_jour`, `marque`, `version_page`, `credit` and `icone` also pass.
- **Not tried**: real Windows, Edge, Firefox, Safari (Chromium under Linux only).
- **Still to update** (rule 16): manual (Settings: "Original values" also brings back the reflections offer), in French and English; the demo (`index.html`, `glb-viewer.html` and `glb2html.py` change).

### 12/11/2026: diagnostic window adjusted; the page offers the reflections when it sees PBR metals (batch 1.10.10)

- **Reported and requested by Klaatou** (screenshot): the diagnostic window is not the size of what it shows (cut lines, horizontal bar) and can only be resized vertically; and `index.html` must spot the PBR materials and offer to turn on a certain percentage of reflections.
- **Done**:
  - **diagnostic window** (`src/core.js`, `diagShow`): width follows the content (820 px at most, 90 % of the screen), resizable in **both directions** (`resize: both`, bottom-right corner), long lines **wrapped** (`white-space: pre-wrap`: no more horizontal bar), height of the size of the text up to 80 % of the screen;
  - **reflections offer** (`src/template.html`): when the region contains metallic materials (`metalInfo`) and the reflections are at 0 %, a `#metalAsk` bar, in the style of the light-rendering offer, says "This region contains N metallic (PBR) materials. Turn on the reflections at 60 %?" with Yes and No (without a graphics card it adds "this may slow things down"). **Once per region**: Yes, No or a slider setting is remembered (`glb2html_metal_asked_<region>`); Yes sets the slider to 60 % and remembers it with the other settings. As the tiles arrive little by little, the page looks every 2 s for 2 minutes. Texts `page.metal.*` in French and English;
  - **change of behaviour**: the default of the reflections is now **0 % everywhere** (batch 1.10.7: 60 % with a graphics card, 0 % otherwise); the offer is what turns them on, with the visitor's consent. The 60 % remains an estimate.
- **Check**: `tests/reflets_metal.py`, new section 8 (10 checks: the bar and its text with 2 metals, Yes, reload, No, slider, region without metal, English, tile mode); `tests/v39.py`: size and resizing of the window. On the 1.10.9 code both fail, with the fix all pass. `v36`, `v36_lang`, `v40`, `v42`, `v45`, `v46`, `v47`, `v52`, `image_diag`, `gif_anim`, `version_page`, `i18n`, `smoke`, `samples`, `tuiles`, `mer_hauteur`, `paquets`, `dist_a_jour`, `marque`, `credit` and `icone` also pass.
- **Not tried**: real Windows, Edge, Firefox, Safari; the look of the bar on a touch screen or with the pad shown (positions set from those of the light rendering, without seeing them); two bars together (light rendering and reflections).
- **Still to update** (rule 16): manual (Settings: "Metal reflections" and the offer; the diagnostic in a window), in French and English; the demo (`index.html`, `carte.html`, `glb-viewer.html` and `glb2html.py` change).

### 12/11/2026: diagnostic: shown in a window as well as copied, and correction of a conclusion of batch 1.10.8 (batch 1.10.9)

- **Requested by Klaatou**: the diagnostic should be shown in a window in addition to being placed in the clipboard.
- **Done** (`src/core.js`, `diagShow`; `src/template.html`, `src/viewer_tpl.html`): a click on "Copy diagnostics" (Information / State window of the page, panel of `glb-viewer.html`) always copies the text, and also shows it in a centred window: title "Diagnostic", copy message (the same as the toast: "Diagnostic copied" or "Copy impossible…"), cross and Esc to close it, readable and selectable text (`#diagOut`, read-only), height limited to the screen. A new click reopens it and updates the text. If the copy is refused, the text is selected as before. The old hidden field under the button (page) and in the panel (viewer) is gone. Texts `core.diag.win.title` and `core.diag.win.close`.
- **Correction of batch 1.10.8**: I had concluded from Klaatou's measurement (15 frames per second at 0 % and at 60 %) that there was "no measurable cost" with software rendering. That was wrong: his diagnostic shows an **NVIDIA GeForce RTX 3090** (hardware rendering, so the default is 60 %), and the "Light rendering" capped at **15 frames per second** ("max frames/s: 15"): the measurement was capped, it said nothing about the cost. To measure the cost of the reflections: untick "Light rendering", walk while looking at metals, then compare the "Frames rendered per second" line at 0 % and at 60 %. The batch 1.10.8 entry is corrected accordingly.
- **Check**: `tests/v39.py`: the window (visible, text, same message as the copy, fits the screen, cross, new click, Esc, title and cross in English, viewer); the "copy succeeded, nothing displayed" check is replaced. On the 1.10.8 code the window check fails, with the fix all pass. `tests/gif_anim.py` closes the window before reading the page image (it hides the centre of the screen). `v36`, `v36_lang`, `v39`, `v40`, `v42`, `v45`, `v46`, `v47`, `v52`, `image_diag`, `version_page`, `reflets_metal`, `i18n`, `smoke`, `samples`, `tuiles`, `paquets`, `dist_a_jour`, `marque`, `credit` and `icone` also pass.
- **Not tried**: real Windows, Edge, Firefox, Safari (Chromium under Linux only); the look on small screens (only the "fits the screen" check is done, with a 1000 x 700 window).
- **Still to update** (rule 16): manual (the diagnostic is shown in a window), in French and English; the demo (`index.html`, `carte.html`, `glb-viewer.html` and `glb2html.py` change). `REPRISE.md` says Klaatou's Edge uses software rendering: to correct (his diagnostic shows an RTX 3090 in Chrome).

### 12/11/2026: diagnostic: "Metal reflections" line (batch 1.10.8)

- **Requested by Klaatou**: after trying the slider (lighting effect clearly visible in front of the spheres of the complete sandbox), a line in the diagnostic to know whether a region contains metals and whether the slider acts. **Klaatou's measurement** (RTX 3090, in front of the sandbox spheres): 15 frames per second with 0 % as with 60 %, but the "Light rendering" capped at 15 frames per second: the measurement says nothing about the cost (conclusion corrected in batch 1.10.9).
- **Done** (`src/core.js`, `diagText` and `metalInfo`): the diagnostic copied by "Copy the diagnostic" contains "Metal reflections: N %; metallic materials loaded: A of B, of which C with reflections". A, B and C count the unique standard materials of the scene (in tile mode, only those already loaded); "metallic" means `metalness` above 0.05, as for the reflections. Texts `core.diag.metal` and `core.diag.metal.v` in French and English.
- **Check**: `tests/reflets_metal.py`, new section 7 (3 checks: 2 metallic materials out of 3 at 0 %, then 2 with reflections at 60 %, then English); on the 1.10.7 code all 3 fail. `image_diag`, `v39`, `v40`, `v42`, `v45`, `v46`, `gif_anim`, `version_page`, `i18n`, `smoke`, `samples`, `tuiles`, `dist_a_jour` and `marque` also pass.
- **Not tried**: Windows, Edge (Chromium only); the line on a tiled region whose tiles are still loading.
- **Still to update** (rule 16): manual (the diagnostic line), in French and English; the demo (`index.html`, `carte.html`, `glb-viewer.html` and `glb2html.py` change).

### 12/11/2026: viewer: metal reflections and "Metal reflections" slider in Settings (batch 1.10.7)

- **Reported and accepted by Klaatou**: PBR metals are darker in the page than in Blender; he accepted the proposal of an environment given only to the metallic materials, adjustable in Settings.
- **Cause** (`src/core.js`, the "AmbientLight", "DirectionalLight" and "HemisphereLight" lines; no `scene.environment`): a fully metallic material (`metalness` 1) does not receive ambient light, it only reflects its environment, and the scene had none. Measured (Chromium, three 0.160.0, same lights as the page): a grey metallic sphere of roughness 0.7 gives 52 out of 255, the same non-metallic one 114 (seen from the front); seen from above, 52 against 249.
- **Done**:
  - **environment**: a small backdrop (sky, light horizon, warm ground, one bright spot) filtered once (`PMREMGenerator`), created on first use and **given only to materials with `metalness` above 0.05** (`metalApply`, called by `fixMaterials` for the single GLB and for each tile, and by `setCfg`); the rest of the scene does not change;
  - **setting** `cfg.metalEnv` (in %, 0 = no reflection and no environment created) and a "Metal reflections: N %" slider in Settings (0 to 200 %), remembered with the other settings (`metal` in `glb2html_opts_*`); "Original values" puts it back to the page value;
  - **default value according to the renderer** (`metalEnvDefault`, using the software-rendering detection that already offers the light rendering): **60 % with a graphics card, 0 % with software rendering** (Basic Render, SwiftShader, llvmpipe). Reason, measured under SwiftShader at 1440 x 900: a metallic surface with reflections costs about 3 times more per frame (9 then 25 ms on a ground, 27 then 85 ms on three spheres). The 60 % is an **estimate**, to be adjusted by looking at real PBR OARs;
  - the real GLBs of the packages (`region.glb`, `galerie.glb`) declare `metallicFactor` 0: only PBR metals and materials without `metallicFactor` (1 by default in glTF, like the ground without material of several tests) are concerned.
- **Check**: new `tests/reflets_metal.py` (brightness measured on a screenshot, materials, default value for six renderer names, slider and its memory, model replacement, tile mode, English); on the original `main` it fails at the first check. `tests/tuiles.py`: the memory check after a full unload takes the shared environment into account, a resource created once (test accessor `metalEnvReady`). A first try with 60 % everywhere made `v46` fail (slower frames under SwiftShader, the avatar moved 0.37 m instead of more than 0.5 m): this led to the default by renderer. Pass: `reflets_metal`, `v46`, `tuiles`, `mer_hauteur`, `solid_materiaux`, `double_face`, `terrain`, `image_diag`, `i18n`, `smoke`, `samples`, `credit`, `icone`, `v36`, `v36_lang`, `v35`, `v34`, `v42`, `v45_lib`, `v47`, `v52`, `paquets`, `dist_a_jour`, `marque`, `version_page`, `modulaire`.
- **Not tried**: Windows, Edge, a real graphics card (the 60 % path is only measured as a still image, not in frames per second), the real renderer names of Windows (only their form is tested), the comparison with Blender or an OpenSim viewer. Unexplained observation: a test sphere with zero-area triangles at the poles raises "Cannot read properties of null (reading 'dot')" in the ray casting, even with the 1.10.5 code; effect on real regions unknown.
- **Still to update** (rule 16): manual (Settings: "Metal reflections" line, default value by renderer) and procedures, in French and English; the demo (`index.html`, `glb-viewer.html` and `glb2html.py` change).

### 12/11/2026: map: the names key becomes discreet, at the bottom of the page and folded (batch 1.10.6)

- **Requested by Klaatou**: the information about the names key must be more discreet: at the end of the page or on request, through a discreet button.
- **Done** (`src/gen_tpl.py`, `carte.html`): the "Names key" row (field, "Show the key", note, status line) is no longer under the arrivals watch. It is in a `<details>` block placed **under the grid, before the footer**, **folded by default**: only the title "Names key" shows, small and dimmed; a click (or Enter on the title) opens the block. It stays folded each time the page is opened, even with a remembered key or one read from the address (the key keeps working without opening it). Nothing else changes: remembering, priority of `#pseudos=`, status line, refused key not sent again, map of the region (key M). The block still disappears without a presence server. Text `map.key.title` in French and English.
- **Check**: `tests/carte_pseudos.py`, section 7b adapted (15 checks): block folded by default, under the grid and before the footer, only the title visible, field not displayed while the block is closed, folded again after a reload, then the 1.10.5 checks on the open block. On the 1.10.5 structure the two new structure checks fail, with the fix all pass. `i18n`, `credit`, `icone`, `samples`, `smoke`, `v36_lang`, `v47`, `v51_etoile`, `v52`, `dist_a_jour`, `marque` and `paquets` also pass.
- **Not tried**: real Windows, Edge, Firefox, Safari (Chromium only); the look of the folded title (measured only by its presence and visibility, not by eye). `index.html` and `carte.html` change: to copy into the demo.
- **Still to update** (rule 16): manual (the map: the folded "Names key" block) and procedures, in French and English.

### 12/11/2026: map: remembered "Names key" field and key status line (batch 1.10.5)

- **Requested by Klaatou**: a status line for the names key and a "names key" field remembered in the browser, so that `#pseudos=` no longer has to be handled by hand.
- **Done** (`carte.html`: `src/gen_tpl.py`; map of the region, key M: `src/template.html`):
  - **field** "Names key" under the arrivals watch: hidden, with a "Show the key" box; the value is remembered in the browser (`glb2html_map_key`, in clear) when it is edited; empty field: key forgotten; the row disappears without a presence server, like the watch;
  - **priority**: `#pseudos=` of the address, otherwise the remembered key; a key read from the address is not remembered; the map of the region (key M) takes the remembered key when the address gives none;
  - **status line**: "key remembered in this browser (14 characters); accepted by the server". The page knows whether the key is accepted because the server adds `names` to its answer only with the right key (`presence_server.py`, `map_key_ok`). Verdicts: waiting, accepted, not accepted (wrong, too many tries, or a server without a key), accepted by only some of the servers. The key is never shown, only its length;
  - **change of behaviour**: a key refused by a server is no longer sent to it (until it is edited or the page is reloaded). Before, the map sent it again at every poll (every 10 s); with a remembered key that had become wrong, this would have written a line in the server log at every poll and used up the 5 tries per minute the server grants to each address. The server is not modified.
- **Check**: `tests/carte_pseudos.py`, new section 7b (14 checks): row and field, "Show the key", typed key accepted by only some of the servers, remembered, sent again at every poll, taken back after a reload, map of the region, field emptied, wrong key sent only once despite several polls, `#pseudos=` takes priority without overwriting the remembered key, English. On the original `main` the section fails (no field), with the fix all pass. `i18n`, `credit`, `icone`, `samples`, `smoke`, `v34`, `v35`, `v36`, `v36_lang`, `v46`, `v47`, `v51_etoile`, `v52`, `paquets`, `dist_a_jour`, `marque`, `version_page` and `titre` also pass.
- **Not tried**: real Windows, Edge, Firefox, Safari (Chromium only). `presence_server.py` is not modified: nothing to send to the VM. For the demo, `index.html` and `carte.html` change.
- **Still to update** (rule 16): manual (the map: key field and status line) and procedures (names key), in French and English.

### 12/11/2026: Python 3.14: `glb2html.py` opens again; the launcher shows the function of the tool (batch 1.10.4)

- **Reported by Klaatou**: "at times", the launcher writes "ERREUR : impossible de lire les options de glb2html.py (TypeError : BooleanOptionalAction.__init__() got …" (ERROR: cannot read the options of glb2html.py). **Requested**: the launcher shows the main function of the chosen tool.
- **Cause** (reproduced with Python 3.14.6): `--sea` and `--anim` passed `metavar` to `argparse.BooleanOptionalAction` (`src/gen_tpl.py`). Python 3.12 declares it deprecated, 3.14 refuses it: `TypeError: BooleanOptionalAction.__init__() got an unexpected keyword argument 'metavar'`. The defect was not in the launcher: `python glb2html.py` stopped the same way under 3.14. That Klaatou's launcher sometimes runs under 3.14 is a deduction from the error message; the Python version he uses was not read. The help does not change without `metavar` (measured: same usage line `[--sea | --no-sea]`). The other six tools already opened under 3.14.
- **Done**: both `metavar` removed; new "Function: …" line under the tool choice of the launcher (`fonction_principale` takes the description of the tool without its beginning "name, version, fingerprint:"; wraps to the window width; text `py.gui.function` in French and English).
- **Check**: new `tests/python_recent.py`: (1) reading the code, no `BooleanOptionalAction` receives `metavar`, `type` or `choices`; (2) `--help` of the six tools with "deprecated" warnings treated as errors; (3) `WEB3D_PYTHONS`: other interpreters. On the original `main` 3 checks fail (code reading, warning under 3.12, `TypeError` under 3.14), with the fix all pass, including real Python 3.10, 3.11, 3.13 and 3.14. `tests/gui.py`: 4 checks of the "Function" line. Under Python 3.14 pass: page built by `glb2html.py`, `gui` (83), `diag_carte`, `oar2glb`, `glb2tiles`, `textes_outils`, `i18n`, `console`, `tools_lang`, `correctifs_v52`, `sortie_cp1252`, `aide_sans_pause`. Under 3.12 pass `gui`, `smoke`, `v52`, `v45_lib`, `marque`, `dist_a_jour`, `samples`, `build_reference`.
- **Not tried**: real Windows; the browser under Python 3.14 (Playwright not installed for that version: `smoke` and `v52` ran only under 3.12); the presence server under 3.14 only through `console` and `diag_carte`.
- **Still to update** (rule 16): manual § 3.9 (the "Function" line) and the mention of the Python versions tried (3.10 to 3.14), in French and English.

### 12/11/2026: launcher: window icon, `glb-stats` in the list, no more "Enter" pause after `--help` (batch 1.10.3)

- **Requested by Klaatou**: (1) give the project icon to the window of the graphical launcher; (2) put `glb-stats.py` in the launcher's list of tools; (3) `glb2tiles.py` and `oar2glb.py` no longer wait for Enter after `--help`, provided nothing else changes.
- **Done**:
  - **icon**: `appliquer_icone` (`web3d_gui.py`). Under Windows `iconbitmap` sets `favicon.ico` (the file of the shortcuts); elsewhere Tk cannot read ICO, Pillow reads it and `iconphoto` sets it (without Pillow the default icon stays). Never an error: a missing icon does not stop the launcher;
  - **`glb-stats`**: one line in `OUTILS`, two examples (`py.gui.ex.glb_stats.1` and `.2`, in French and English), the text of `py.gui.desc`; `--shortcuts` therefore creates one more shortcut (eight in all: the window and seven tools);
  - **pause**: `glb2tiles.py` and `oar2glb.py` no longer ask for Enter when the command line contains `--help` or `-h`. The rest is unchanged: a normal run still waits for Enter in a console, `--nopause`, `--version` and `--terrain-only` as before; `extraire_batiments.py` and `iar2oar.py` had no pause.
- **Check**: new `tests/aide_sans_pause.py` (8 checks, fake terminal `pty`): on the original `main` 4 checks fail (`--help` and `-h` of both tools wait for Enter), with the fix all pass; opposite direction: without `--help` the tool still waits for Enter. `tests/gui.py`: 4 icon checks (found, applied, missing, window without icon support) and `glb-stats` (options read, one by one, examples); passed under `xvfb-run` with Pillow. `textes_outils`, `i18n`, `tools_lang`, `oar2glb`, `glb2tiles`, `correctifs_v52`, `console`, `dist_a_jour`, `marque`, `samples` and `build_reference` also pass.
- **Not tried**: real Windows (`iconbitmap`, taskbar icon, the new shortcut), macOS. The pause check under Windows (`pty` does not exist there): the test says so and skips it.
- **Still to update** (rule 16): manual § 3.9 and `SIMPLE_PROCEDURES` § 5 ("six tools"; the "seven shortcuts" images become eight), in French and English.

### 12/11/2026: tools: a character outside the code page no longer stops the tool when its output is redirected (batch 1.10.2)

- **Known issue** (1.10.0 notes): `glb2html.py` stopped on `→` when its output goes into a pipe or a Windows cp1252 file (`> journal.txt`).
- **Cause**: `sys.stdout` is encoded with the code page of the console or the file, in strict mode; `print` of a character it does not know raises `UnicodeEncodeError`. `sys.stderr` is not concerned (Python writes it with `backslashreplace`). Same defect in `oar2glb.py` (the `Tee` writes to `sys.__stdout__`), `diag_carte.py` and the presence server (a nickname or a path outside cp1252 in a log line).
- **Done**: `errors="replace"` on the output streams, as `extraire_batiments.py` and `iar2oar.py` already did: in the `__main__` block of `glb2html.py` (`src/gen_tpl.py`) and of `diag_carte.py`, on `sys.__stdout__` and `sys.__stderr__` before the `Tee` of `oar2glb.py`, and on `sys.stdout` of `presence_server.py`. A character that cannot be written becomes `?`; with a UTF-8 stream nothing changes. `glb2tiles.py` and `glb-stats.py` already write in UTF-8: unchanged. The graphical launcher is not concerned.
- **Check**: new `tests/sortie_cp1252.py` (12 checks: the four tools, output in cp1252 then in UTF-8). On the original `main` 8 checks fail (the four tools crash on `UnicodeEncodeError`), with the fix all pass; in UTF-8 the arrow is kept in both cases.
- **Not tried**: real Windows (cp1252 is simulated with `PYTHONIOENCODING=cp1252` under Linux). Presence server on the VM: only the console output changes, copying the file is optional.

### 12/11/2026: documents: Firefox was tried by Klaatou with the regions and the maps (batch 1.10.1)

- **Reported by Klaatou**: Firefox has been tried with the regions and the maps; the documents still said "not tried" or reported only a third party's result.
- **Done**: `VUE_ENSEMBLE.md` and `OVERVIEW.md`: new line "Tried by Klaatou in Firefox" (display of regions and maps, 12/11/2026, on his PC, version not noted) and the "Not tried" line now says Firefox on Linux instead of Windows and Linux (the PC of Klaatou runs Windows: assumed from the rest of the project, to be corrected if wrong); `MANUEL.md` and `MANUAL.md`: the Firefox sentence about the modular library names his result before the third party's. The lines about the GIF animation (already "tried in Firefox") and the "Made with Web_3d" icon (not tried in Firefox) are unchanged.
- **Check**: `verif_trad.py` on the three pairs (manual, overview, history): same result as before; `dist_a_jour.py` and `readme_liens.py` pass.
- **Not tried**: nothing new (documents only); the Firefox version and the system of that try are not noted.

## 1.10.0 (12/11/2026)

### 12/11/2026: release 1.10.0: PBR materials, Linux with Mono, sea height

- **Release**: 1.10.0 (12/11/2026), decided by Klaatou, gathers batches 1.9.1 to 1.9.23 (described below, in this same section). The minor number goes up: functions were added since 1.9.0.
- **New since 1.9.0**:
  - **(1)** OpenSim 0.9.3 PBR materials: `oar2glb.py` reads them in the OAR and applies them to the GLB (manual § 3.10; `--no-pbr`, `--pbr-size N`; Pillow needed for the textures).
  - **(2)** Conversion on Linux: `oar2glb.py` runs convoar with Mono (manual § 3.11).
  - **(3)** "Sea height" slider in the Settings of the page (manual § 9.19).
  - **(4)** The graphical launcher opens `oar2glb` again from its shortcuts (it did not open without a console); PBR example in its list.
  - **(5)** `tests/tout.py`: the whole test suite in one command (`DEVELOPPEMENT.md`); `CHANGELOG.fr.md` created and `CHANGELOG.md` becomes the English version; PBR picture and credit in the README; documents up to date.
- **Version numbers per built file**: `index.html`, `glb2html.py`, `glb-viewer.html`, `carte.html` 1.9.15 ; `oar2glb.py` 1.9.21 ; `web3d_gui.py` 1.9.17 ; unchanged: `glb2tiles.py` 1.4.10, `extraire_batiments.py` 1.6.3, `iar2oar.py` 1.6.4, `diag_carte.py` 1.7.7, `presence_server.py` 1.6.19 (no `scp` to the VM).
- **Tried by Klaatou on Windows**: the conversion of a real 1.45 GB sandbox OAR with PBR (`--pbr-size 256`), the result in Blender and in the viewer, the sea slider, the launcher, the whole test suite (93 tests out of 95; `v51_vides` and `v52_http` fail with websockets 16.0, which only adds noise to the presence server's log). **Tried**: Linux with Mono, on Debian 13 (Klaatou) and Ubuntu 24 (sandbox), small regions. **Not tried**: Edge, macOS, a large region on Linux, the sea slider in tiles mode.
- **Known points** (to correct later, probably in 1.10.1): `glb2html.py` stops on `→` when its output goes to a Windows pipe or file in cp1252; without `--pbr-size` a region with many PBR materials gives a heavy GLB; under Mono, convoar did not write its `.buf` on a 20-object extract.
- **GitHub release notes** (to attach: `galerie-photos.zip` and `region-simple.zip`, built by `python fabriquer_paquets.py` after `VERSION` is set to 1.10.0), English then French:

  > **Web_3d 1.10.0: PBR materials, Linux, sea height**
  >
  > ### What's new
  >
  > **1. OpenSim 0.9.3 PBR materials**
  > - OARs that contain PBR materials are converted with their real materials: colour, metallic and roughness, relief (normal), occlusion, emissive, and each object's own settings.
  > - It is automatic. `--no-pbr` to skip it; `--pbr-size 256` for smaller textures (lighter GLB).
  > - Pillow is needed for the textures: `pip install pillow`.
  > - Tried on the BloodMoon Pack grid's sandbox (1.45 GB). Thanks to its owner, Vlad.
  >
  > **2. Conversion on Linux**
  > - `oar2glb.py` runs convoar with Mono. The packages to install are in the manual, § 3.11.
  > - Tried on Debian 13 and Ubuntu 24. **Your feedback is welcome** (other distributions, large regions) to validate it completely.
  >
  > **3. Web page: sea height**
  > - New "Sea height" slider in Settings.
  > - It fixes the case where the sea hid the lower part of buildings on some large regions.
  > - Existing pages do not change.
  >
  > **4. Graphical launcher**
  > - `oar2glb` opens again from the launcher and its shortcuts (it did not open without a console).
  > - New PBR example in the list.
  >
  > **5. Documentation**
  > - Manual: § 3.10 (PBR), § 3.11 (Linux), § 9.19 (sea).
  > - README with a PBR picture.
  > - Changelog in French (`CHANGELOG.fr.md`) and in English (`CHANGELOG.md`).
  >
  > ### Updating
  >
  > - If you already have one of the packages, copy only `index.html` and `carte.html` into your folder.
  > - Do not unzip the new zip over it: that would overwrite your configuration, zones and images.
  >
  > ---
  >
  > **Web_3d 1.10.0 : matériaux PBR, Linux, hauteur de la mer**
  >
  > ### Nouveautés
  >
  > **1. Matériaux PBR d'OpenSim 0.9.3**
  > - Les OAR qui contiennent des matériaux PBR sont convertis avec leurs vrais matériaux : couleur, métal et rugosité, relief (normale), occlusion, émissif, et les réglages propres à chaque objet.
  > - C'est automatique. `--no-pbr` pour s'en passer ; `--pbr-size 256` pour des textures plus petites (GLB plus léger).
  > - Pillow est nécessaire pour les textures : `pip install pillow`.
  > - Essayé sur la sandbox de la grille BloodMoon Pack (1,45 Go). Merci à son propriétaire, Vlad.
  >
  > **2. Conversion sous Linux**
  > - `oar2glb.py` lance convoar avec Mono. Les paquets à installer sont dans le manuel, § 3.11.
  > - Essayé sur Debian 13 et Ubuntu 24. **Vos retours sont les bienvenus** (autres distributions, grandes régions) pour le valider complètement.
  >
  > **3. Page web : hauteur de la mer**
  > - Nouveau curseur « Hauteur de la mer » dans Réglages.
  > - Il règle le cas où la mer cachait le bas des bâtiments sur certaines grandes régions.
  > - Les pages existantes ne changent pas.
  >
  > **4. Lanceur graphique**
  > - `oar2glb` s'ouvre de nouveau depuis le lanceur et ses raccourcis (il ne s'ouvrait pas sans console).
  > - Nouvel exemple PBR dans la liste.
  >
  > **5. Documentation**
  > - Manuel : § 3.10 (PBR), § 3.11 (Linux), § 9.19 (mer).
  > - README avec une image PBR.
  > - Journal des modifications en français (`CHANGELOG.fr.md`) et en anglais (`CHANGELOG.md`).
  >
  > ### Mise à jour
  >
  > - Si vous avez déjà un des paquets, copiez seulement `index.html` et `carte.html` dans votre dossier.
  > - Ne dézippez pas le nouveau zip par-dessus : cela écraserait votre configuration, vos zones et vos images.

### 11/11/2026: tests: UTF-8 environment restored in `tout.py` (correction of batch 1.9.20); the presence servers of the tests no longer block on a full pipe (batch 1.9.23)

- **Reported by Klaatou**: second full run on Windows (24 min 31 s): 79 OK and 16 to look at, against 83 OK and 12 in the first run.
- **Correction of batch 1.9.20 (my mistake)**: I had taken `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1` out of `tout.py` on an unverified hypothesis, that the failures of the first run came from them. They did not: those failures were the `.py` convoar, the pause, `marque`, `v48` and the re-encoding (batches 1.9.21 and 1.9.22). Without the two variables, nine tests that passed in the first run failed: `glb2tiles`, `image_medias`, `image_noms_gen`, `lien_image`, `oublier`, `portail_interne`, `v31`, `v32` and `v35`. Their logs show the cause: a child program writes its output in one encoding and the test reads it with another (accented letters turned into garbage), and `glb2html.py` stops on `'charmap' codec can't encode character '\u2192'` when its output goes into a pipe. These tests do not follow the rule of `DEVELOPPEMENT.md` (a test that reads the output of a child program must start it with `PYTHONIOENCODING=utf-8`). `tout.py` sets the two variables again and starts each test with `python -u` (no wrapper any more); `DEVELOPPEMENT.md` explains it and gives the line for one test on Windows: `$env:PYTHONUTF8="1"; python .\tests\NAME.py`.
- **Tool problem seen on the way, not corrected here**: `glb2html.py` stops on `→` when its output goes to a Windows pipe or file in cp1252 (`python glb2html.py ... > log.txt`); the graphical launcher is not concerned. To decide later: make the tools write with `errors="replace"`, as `extraire_batiments.py` already does.
- **Presence tests** (`v33`, `v34`, `v36`, `v37`, `v37_chat`: "timed out during opening handshake", or a page that never gets "online"; the same in both runs): they start `presence_server.py` with `stdout=PIPE` and never read the pipe. A Windows pipe keeps 4 KB; the server writes about 490 bytes at start and about 240 bytes per visit (measured here), so after some fifteen visits it blocks on its next `print` and stops answering; a Linux pipe keeps 64 KB. **Cause not proved on Windows**: it fits the code, the numbers and the symptoms (the tests pass here, also with websockets 16.0), and the re-run decides.
- **Done**: new helper `tests/vider_tube.py` (`vider(proc)`: a thread reads the pipe continuously; `proc.stdout.read()` and `proc.communicate()` return what was read, so the tests that read the server's output at the end still work), used by `h37.py` (hence `v37` and `v37_chat`), `v33.py`, `v34.py` and `v36.py`; `tout.py` skips it like `h37` and `glbfab`. Described in `DEVELOPPEMENT.md` and `DEVELOPMENT.md`.
- **Check**: the helper on a program that writes 300 KB: without it the program blocks on the full pipe (even on Linux), with it the program ends and `communicate()` returns the 300 KB, and `read()` after a `kill` returns the beginning. `v36`, `v34`, `v37_chat`, `v37` and `v33` (158 checks, 12 minutes here) pass here with the helper; `oar2glb`, `pbr_oar`, `i18n` pass with the new `tout.py`.
- **Not tested**: Windows, which decides: the re-run of the 14 failed tests there. Still open after it, if it fixes the above: `v51_vides` and `v52_http` (websockets 16.0).

### 11/11/2026: tests: `oar2glb` can run on Windows (re-encoding in a child interpreter); `tout.py` shows the last traceback (batch 1.9.22)

- **Reported by Klaatou**: re-run of the five failed tests on Windows: `marque`, `terrain`, `textes_outils` and `v48` pass (`v48` with one `[IGNORE]`); `oar2glb` still fails after 52 s, its summary stopping at "2 textures to re-encode on 8 cores".
- **Diagnosis** (reproduced on Linux by forcing the `spawn` start method, which is the one Windows and macOS use): `tests/oar2glb.py` calls `T.reencode_oar(...)` in its own process, and `reencode_oar` starts 8 worker processes. With `spawn`, each worker re-imports the main module, here the test file, which has no `if __name__ == "__main__"` guard: the whole test runs again in every worker, which fails with `RuntimeError ... bootstrapping phase` and then `BrokenProcessPool`. `oar2glb.py --reencode` itself is not concerned (the tool has its guard). `tout.py` hid the traceback: the output of a child process is buffered when it goes to a pipe, so the traceback (standard error) came before the end of the standard output in the log, and the summary only showed the last lines.
- **Done**: `tests/oar2glb.py` runs `reencode_oar` in an interpreter started with `-c` (its main module has no file to re-import), checks its return code and still checks the re-encoded files. `tests/tout.py` starts each test with `python -u` (unbuffered for that one process only, no environment variable) so that the log is in order, and its summary now shows the lines `[ECHEC]` then the last `Traceback` block (24 lines at most).
- **Check**: `tests/oar2glb.py` passes on Linux, also when the main process is forced to `spawn` (before: `RuntimeError` and `BrokenProcessPool`); `reencode_oar` run from `-c` with `spawn` forced writes its OAR; `tout.py` tried on fake tests (an output followed by an exception, a test that uses a `spawn` pool with its guard) and on three real tests. No other test uses a process pool.
- **Not tested**: Windows, which decides: the re-run of `oar2glb` there.

### 11/11/2026: Windows: `oar2glb.py` accepts a `.py` convoar and no longer prints a trace at its pause; tests `marque`, `v48`, `mono_linux` (batch 1.9.21)

- **Reported by Klaatou**: the first full run of the suite on Windows with `tests/tout.py` (21 min 49 s, 95 tests): 83 OK, 12 to look at. Causes found, one by one:
  - `oar2glb` and `terrain`: the tests give oar2glb a fake convoar written in Python. On Windows, `run_convoar` always built the launcher `convoar_inv.exe`, which needs a real `.exe` (`pe_platform` read a 271-byte `.py` as a PE file). The code was the same in 1.9.10 (`exe = ensure_launcher(convoar) if os.name == "nt"`): these two tests could never pass on Windows.
  - `textes_outils`: `oar2glb.py --help` ended with the "Press Enter" pause. On Windows `isatty()` is true for NUL (the empty input of a test), so `input()` raised `EOFError` and printed a trace; `glb2tiles.py` already caught it.
  - `marque`: the test read every line after "marques" of the output of `build.py` as "name hash"; the line "[OK] docs/REFERENCE_OPTIONS.md: refait" broke it. It also failed in the sandbox (listed in `DEVELOPPEMENT.md`).
  - `v48`: the test stops the presence server with `SIGINT`, which a child process does not receive on Windows.
  - `v51_vides` and `v52_http`: reproduced here with websockets 16.0 (the version of the Windows run); both pass with 17.4. With 16.0 the presence server does not filter the "empty connection" and "http request" log lines. Not corrected in this batch, and not caused by the batches since 1.9.0.
  - `v33`, `v34`, `v36`, `v37`, `v37_chat`: websocket handshake timeouts, or the page never reaches "online". Not reproduced here (they pass here, also with websockets 16.0): to be investigated with the Windows logs.
- **Done**: `commande_convoar(convoar, windows=None)` (`tools/oar2glb.py`): on Windows a `.exe` goes through the launcher as before, a `.py` script is run with `sys.executable`, any other program as it is (the parameter lets the tests try this branch anywhere). The pause of `oar2glb.py` catches `EOFError`, like `glb2tiles.py`. Tests: `marque` only reads the "name  hash" lines; `v48` skips the clean-stop part on Windows with an `[IGNORE]` line; `mono_linux` gets two checks of the Windows branch.
- **Check**: on Linux (sandbox): `mono_linux`, `oar2glb`, `terrain`, `textes_outils`, `marque` (it failed here before), `v48`, `gui`, `i18n`, `pbr_oar` and `dist_a_jour` pass.
- **Not tested**: Windows, which decides: the re-run of `oar2glb`, `terrain`, `textes_outils`, `marque` and `v48` there. The `.exe` branch on Windows is unchanged.
- **Still open**: the presence tests above; websockets 16.0.

### 11/11/2026: `tests/tout.py`: each test is started in the same environment as `python .\tests\NAME.py` (batch 1.9.20)

- **Reported by Klaatou**: during the first full run on Windows, four tests failed within a few seconds: `marque`, `oar2glb`, `terrain` and `textes_outils` (the first three pass here in the sandbox; `marque` already fails in the sandbox and the cloud, as listed in `DEVELOPPEMENT.md`).
- **Cause suspected (to be confirmed by the re-run)**: `tout.py` forced `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1` in the environment of every test. These variables are inherited by the programs that the tests start themselves (`subprocess.run(..., text=True)`), which the tests read with Windows' default encoding: their text could be decoded differently from a normal `python .\tests\NAME.py` run. The variable is a design mistake in any case: the run must look like the one described in `DEVELOPPEMENT.md`.
- **Done**: `tests/tout.py` no longer sets any variable. Each test is run through a small wrapper (`python -c ... runpy.run_path`) that only switches the output of that one process to UTF-8, so that the log is readable; `sys.argv`, `__file__`, `__main__` and the import of the neighbouring modules (`h37`, `glbfab`) are the same as in a direct run.
- **Check**: tried on 4 fake tests (success, failure, too slow, a test that imports a neighbouring module; no environment variable seen by the test, accents kept in the log) and on 8 real tests (`i18n`, `mer_hauteur`, `oar2glb`, `pbr_oar`, `terrain`, `textes_outils`, `gui`, `v52`: all OK here); syntax checked for Python 3.8.
- **Not tested**: Windows (the point of the correction): the re-run of the four failed tests there decides whether this was the cause.

### 11/11/2026: README and manual: credit worded "Thanks to its owner, Vlad"; `tests/tout.py` (batch 1.9.19)

- **Requested by Klaatou**: the sandbox's owner agreed to be named (his pseudonym, Vlad). The credit now says "sandbox" (even in French) and "Thanks to its owner, Vlad" instead of "with the owner's agreement": README (caption and Credits), manual sections 3.10, 3.11 and 9.19. Rule 25: an explicit exception, like NightshadeCeres; `REGLES.md` is updated by Klaatou (rule 25: "plus Vlad (agreement of dd/mm/yyyy)").
- **Done**: new `tests/tout.py` runs every test of `tests\` one by one and reports the failures: `ECHEC` (return code not 0, or an `[ECHEC]` line with return code 0), `DELAI` (timeout), `SUSPECT` (an error trace printed by a test that says it passed); the `[IGNORE]` parts are counted. Full outputs in `tests_logs\NAME.log`, summary in `tests_logs\resume.txt` (the folder hides itself from git). Options `--liste`, `--seulement`, `--sauf`, `--reprendre`, `--arreter`, `--delai`. Described in `DEVELOPPEMENT.md` and `DEVELOPMENT.md`. The two stand-alone scripts (outside the repository) now print their whole description with `--help`.
- **Check**: `tout.py` tried on 7 fake tests (success, failure, failure hidden behind return code 0, too slow, crash, ignored part, suspicious trace: all detected, return code 1) and on 5 real tests (all OK); `readme_liens.py`, `dist_a_jour.py` pass; `verif_trad.py` gives the same result as before on the manual.
- **Not tested**: Windows; the full duration of the suite.

### 11/11/2026: README: PBR picture and credit to the sandbox's grid; two stray files out of the repository (batch 1.9.18)

- **Requested by Klaatou**: use the PBR picture, with the agreement of the sandbox's owner, crediting his grid with a link and saying that the test data come from that sandbox.
- **Done**: `docs/images/pbr.jpg` (1600 x 900, 215 KB, cropped from a screenshot of the page; it had been committed at the repository root by `git add -A` in batch 1.9.17 and is moved with `git mv`); picture and caption in both READMEs after the paragraph on `oar2glb.py`; credit in the "Credits" section of both READMEs and a mention in manual section 3.10 ("Tried"). The link `https://bloodmoonpack.com/grid/` is a deliberate public link to a third party, like the Outworldz and NightshadeCeres links already in the README; no name of a person is written (rule 25).
- **Also**: `inspecter_objets.py` had been committed at the repository root by the same `git add -A`; it is removed from git (`git rm --cached`, the local copy stays) and `inspecter_objets.py` and `analyser_oar_pbr.py` are added to `.gitignore`. They stay stand-alone scripts (French-only messages, outside the i18n rules), kept out of the repository until they become proper tools: decision pending.
- **Check**: `tests/readme_liens.py`, `tests/apropos_liens.py`, `tests/dist_a_jour.py` pass; `verif_trad.py` gives the same result as before on the README and the manual.
- **Not tested**: how the picture looks on GitHub.

### 11/11/2026: `oar2glb.py` and `web3d_gui.py`: the launcher could not open oar2glb without a console; PBR example (batch 1.9.17)

- **Reported by Klaatou**: the graphical launcher does not open the oar2glb part, neither from the tool list nor from its desktop shortcut.
- **Diagnosis**: the shortcuts run `pythonw.exe`, which has no console: `sys.__stdout__` and `sys.__stderr__` are `None`. At start, `oar2glb.py` doubles the real console into its log (`Tee(sys.__stdout__, lf)`), so its first printed line raised `AttributeError: 'NoneType' object has no attribute 'write'`, before `parse_args`; `lire_parser` (`web3d_gui.py`) only caught `SystemExit`, so the error left the window silent. Reproduced by setting both streams to `None`: only `oar2glb.py` fails among the six tools, and already in 1.9.10 (not caused by the PBR batches).
- **Done**: `Tee` (`tools/oar2glb.py`) ignores a missing stream. `lire_parser` (`tools/web3d_gui.py`) now catches any error of the tool before its `parse_args`, returns no parser and keeps the reason in `lire_parser.erreur`; the status line shows it after the existing "cannot read the options" message. New example for oar2glb in the launcher: `Atoll.oar --pbr-size 256` (`py.gui.ex.oar2glb.5`, French and English).
- **Check**: `tests/gui.py` (run with `xvfb-run` and Tk in the sandbox, window part included): three new checks (the six tools read without a console, a tool that fails before its `parse_args`, the reason cleared after a good read) pass, and the first one fails on the previous `dist\`; `tests/i18n.py`, `oar2glb.py`, `pbr_oar.py`, `mono_linux.py`, `dist_a_jour.py` pass.
- **Not tested**: Windows and a real `pythonw.exe` (the missing console is simulated); running a conversion from the launcher.

### 11/11/2026: documents: PBR, Linux with Mono, sea height (batch 1.9.16)

- **Requested by Klaatou**: bring the documents up to date after batches 1.9.11 to 1.9.15 (list "still to update" of the 1.9.12 entry).
- **Done**: manual (`MANUEL.md`, `MANUAL.md`): footnote and PBR paragraph of section 3, two rows in the command table and two in the option table of sections 3.1 and 3.2, new sections 3.10 (PBR) and 3.11 (Linux with Mono), paragraph "Sea height" in section 9.19; guide (Linux line); `README.md` and `README.fr.md` (PBR, Linux, `oar2glb.py` row); simple procedures (Linux and PBR paragraph); index (three rows); history (batches 1.9.11 to 1.9.16). French and English edited together.
- **Check**: `tests/readme_liens.py`, `tests/apropos_liens.py`, `tests/dist_a_jour.py`: pass (no code changed).
- **Not done**: the PBR picture in the README (waiting for the sandbox owner's agreement; the cropped file `pbr.jpg` is ready); `REPRISE.md` (delivered at the next resume, rule 23); the two stand-alone scripts `analyser_oar_pbr.py` and `inspecter_objets.py` stay outside the repository for now.

### 11/11/2026: viewer and page: sea height slider in Settings (batch 1.9.15)

- **Reported by Klaatou**: on a whole sandbox region, the page cut the lower part of every wall and sphere board (the visitor, rising, flew through the sea plane); unchecking "Show the sea" showed everything.
- **Diagnosis**: `setModel` (`src/core.js`) recentres the model so that the mean of the mesh origins is at y = 15, and `seaY` is in that shifted frame. On this GLB the mean is 38.8 m (many mesh origins sit far above the ground), so the model went down by about 24 m: terrain at about -2.8 m, sea at the page's `seaY` of 10 m, about 13 m above the ground. The "simple region" page had `seaY: 10`, set for a small region.
- **Done**: `src/core.js`: `cfg.seaM` (sea height in metres in the region's own frame, the one the OpenSim water uses: 20 m by default) and `seaShift()` (vertical shift applied to the loaded model; 0 in tiles mode, which does not recentre); `seaYNow()` is used wherever the sea is placed (creation, `setCfg`, `setModel`, tiles). `src/template.html`: Settings gets a "Sea height" slider (-50 to 250 m, step 0.5) with the other sea rows, applied live, kept on the device like the other choices (`seaM` in the same key), grayed when the sea is hidden, reset by "Original values". New texts `page.opt.seaY` and `page.opt.seaY.m` (French, English). `cfg.seaY` and `--sea-y` keep their meaning (shifted frame): existing pages do not change.
- **Check**: new `tests/mer_hauteur.py` (start value, slider moves the sea, kept after reload, original values, grayed, English, `--no-sea` page, no page error): passes, and fails on the previous `dist\` (no `seaShift`); `tests/v52.py`, `v42.py`, `v37.py`, `i18n.py` and `dist_a_jour.py` pass.
- **Not tested**: tiles mode with the slider (shift 0 from reading the code, not run); a real graphics card, Edge, Windows.
- **Still to update**: manual (Settings, sea height, the recentring), simple procedures, `HISTORY.md`, `HISTORIQUE.md`, and the list of the 1.9.12 entry.

### 11/11/2026: `oar2glb.py`: PBR: OpenSim's default material (batch 1.9.14)

- **Reported by Klaatou**: on the whole sandbox region, many spheres stay beige (convoar's default texture).
- **Diagnosis**: `inspecter_objets.py` (stand-alone, outside the repository) shows that most beige objects are not PBR at all (3,241 "Primitive" parts without `0x80` or `<MatOvrd>`: prototypes, sculpts, flexi prims), but that "Many PBRs" (97 parts, all with `0x80` and `<MatOvrd>`) were left beige in `region.glb` (15 nodes). OpenSim's default PBR material, `968cbad0-4dad-d64e-71b5-72bf13ad051a` (`OpenSim.Framework.Constants.DefaultMaterial`), is never written in an OAR; prims that cite it carry only their overrides. `pbr_appliquer` found no material for it, so those faces kept convoar's material and lost their overrides (`tex`, `bc`, `mf`, `rf`...). It is very probably the one material reported as missing in the full run (several boards cite it in the analysis report).
- **Done** (`tools/oar2glb.py`): `PBR_DEFAUT` and `PBR_VIERGE`: the default material is a blank glTF material (white, metallic 1, roughness 1: the glTF defaults, which are also the Second Life viewer `LLGLTFMaterial` defaults, `llgltfmaterial.cpp` line 67) and the overrides apply to it. A null material UUID (no PBR on that face) is no longer counted as a missing material.
- **Source checked** (Second Life viewer, `llgltfmaterial.cpp`): in a `tex` override a null UUID means "no override" and `ffffffff-ffff-ffff-ffff-ffffffffffff` means "remove the texture", as `pbr_slots` already did; this settles the 1.9.12 doubt in the code, not in a viewer.
- **Check**: `tests/pbr_oar.py` (default material with overrides, without overrides, null UUID left as convoar made it): passes.
- **Not tested**: a real conversion with these objects (my extracts do not contain them; the 20-object extract still hits convoar's unwritten `.buf` under Mono in the sandbox); Windows; that OpenSim viewers show the default material as blank white/metal 1/rough 1 (taken from the Second Life viewer defaults).
- **Still open**: the cut-looking spheres of the top rows (not explained yet); documents as listed in the 1.9.12 entry.

### 11/11/2026: `oar2glb.py`: PBR: a whole sphere has one face (batch 1.9.13)

- **Reported by Klaatou**: in the page, seen from behind the sphere boards, each sphere shows a disc with another texture.
- **Diagnosis**: convoar (libomv) gives a whole sphere two glTF primitives (the sphere, 576 triangles, and a small cap, 48 triangles). The cap received the material that the OAR gives to face 1, whereas OpenSim counts ONE face for a whole sphere (`SceneObjectPart.GetNumberOfSides`: `SPHERE`, `ret = 1`, plus faces only for a cut, skew, twist or hollow).
- **Done** (`tools/oar2glb.py`): the new `pbr_nb_faces` returns 1 for a whole sphere (half-circle profile, path 32 or 48, no cut, hollow, skew or twist, not a sculpt) and `None` for any other shape; `pbr_appliquer` gives a primitive beyond the OpenSim faces the material of face 0.
- **Check**: `tests/pbr_oar.py` (whole, hollow, cut and twisted sphere, box/cylinder, and the two primitives sharing the face 0 material): passes. On the 3-object extract of the sandbox OAR (convoar under Mono, in the sandbox): 98 to 75 materials, 336 to 245 textures, GLB 22.1 to 16.9 MB; Chromium render from behind: the discs are gone.
- **Not tested**: Windows; hollow or cut spheres (left as before: their extra faces can still show discs); other shapes for which libomv makes more faces than OpenSim (to be seen in the page); the look in a real OpenSim viewer.
- **Still to update**: the documents listed in the 1.9.12 entry.

### 11/11/2026: `oar2glb.py`: OpenSim 0.9.3 PBR materials are applied to the GLB (batch 1.9.12)

- **Requested by Klaatou**: convoar ignores PBR (it rebuilds an ordinary material from the old textures: metallic 0). A real OpenSim 0.9.3 region with PBR (a 1.45 GB sandbox OAR) was analysed first with the new stand-alone helper `analyser_oar_pbr.py` (outside the repository).
- **Formats read** (OpenSim `master` source, then checked on that OAR): `ExtraParams` type `0x80` of each prim (face, material UUID); `assets/UUID_prmat.dat` (LLSD binary header around a glTF 2.0 text); `<MatOvrd>` (per-face overrides in LLSD notation: `bc`, `mf`, `rf`, `ec`, `am`, `ac`, `ds`, `tex`, `ti`).
- **Done** (`tools/oar2glb.py`): `oar_scan` reads the prims' PBR data and the `*_prmat.dat` assets; after `repair`, the new `pbr_appliquer` gives glTF primitive *j* the material of face *j* (convoar writes one primitive per face that has geometry, in face order): base colour, metallic/roughness, normal, occlusion (shares the metallic/roughness image, as in OpenSim), emissive, factors, alpha mode, double sided, and the overrides (`KHR_texture_transform` for `ti`). A mesh shared by prims with different materials is copied. The textures (JPEG 2000 in the OAR) are read in a second pass over the OAR, decoded with Pillow, reduced to 512 px and stored as JPEG (PNG when transparent). New options `--no-pbr` and `--pbr-size N` (0 = original size). Without Pillow: materials without textures, with a message.
- **Check**: new `tests/pbr_oar.py` (formats, overrides, copied meshes, images in the final GLB, no-Pillow case): passes. On the 3-object extract of the sandbox OAR (74 PBR prims, 98 materials, 336 textures, 22 MB GLB), converted with the supplied `convoar.exe` under Mono in the sandbox: rendered in Chromium with three.js (normal maps, metal and gloss visible on the spheres); `glb2tiles.py --force` on that GLB keeps `KHR_texture_transform`.
- **Not tested**: Windows (PBR step); a whole sandbox region (size and time of the second pass over a 1.45 GB OAR: estimation only); the meaning of a null texture UUID in a `tex` override (taken as "no override"; `ffffffff-ffff-ffff-ffff-ffffffffffff` as "remove the texture"); prims whose faces have no geometry (the primitive/face correspondence assumes none is skipped); alpha-blended PBR sorting in the viewer; viewer-side look of the metallic surfaces (they need light and reflections).
- **Known, separate**: on the 20-object extract convoar (Mono, sandbox) leaves its `.buf` unwritten: its asset writer does not wait for the end of the writes (`BAssetStorage.cs:138`, `stream.WriteAsync(...)` without `await`); not fixed here.
- **Still to update**: manual (section 3: PBR, `--no-pbr`, `--pbr-size`, Pillow), simple procedures, README, `HISTORY.md` and `HISTORIQUE.md`.

### 11/11/2026: `oar2glb.py`: on Linux, convoar.exe is run with Mono (batch 1.9.11)

- **Requested by Klaatou**: offer the conversion on Linux. A .NET 8 port of convoar (his forks, branch `net8-pbr`) was tried first: on a Debian 13 VM it stops at the first `System.Drawing.Bitmap` (`PlatformNotSupportedException`, `Terrain.cs:91`), so it is not pursued.
- **Reported by Klaatou**: the `convoar.exe` supplied in `dist/convoar`, run by hand with Mono on the same VM (`LC_ALL=C mono convoar.exe --outputdir ... region.oar`), wrote a `.gltf`, a `.buf` and three images (content not checked).
- **Done**: `run_convoar` (`tools/oar2glb.py`) now goes through the new `commande_convoar`. Windows is unchanged (launcher `convoar_inv.exe`). Elsewhere, a `convoar.exe` is run with `mono`: path made absolute, `LC_ALL=C` (numbers as `0.5`), `LD_LIBRARY_PATH` starting with the folder of `convoar.exe` so that the supplied openjpeg library is found. A program without `.exe` (a script, or `convoar` found in the PATH) is run as before. Without `mono`: stop with a message that gives the Debian/Ubuntu packages (`py.oar2glb.erreur_mono_introuvable_0`, French and English).
- **Check**: new `tests/mono_linux.py` with a fake `mono` (command, `LC_ALL`, `LD_LIBRARY_PATH`, working folder, relative path, `mono` missing, program without `.exe`): passes; the same test on the previous `oar2glb.py` fails (it tries to run the `.exe` directly); `tests/oar2glb.py` and `tests/i18n.py` pass.
- **Not tested**: a whole conversion through `oar2glb.py` on Linux (only the manual run above); PBR (unchanged: convoar reads no PBR material, and the OAR used for the test was made by hand, not exported by OpenSim); macOS (the `dllmap` of `OpenMetaverse.dll.config` expects a `.dylib` that is not supplied); Windows.
- **Still to update**: manual (section 3: Linux with Mono), simple procedures, README (Linux prerequisites), `HISTORY.md` and `HISTORIQUE.md`.

### 10/11/2026: `CHANGELOG.md`: 1.0.0 section translated into English; end of the translation (batch 1.9.10)

- **Requested by Klaatou**: stop the translation at the 1.0.0 section.
- **Done**: the 1.0.0 section (entries of 25/10/2026 to 29/10/2026) is now in English: the headings are translated; these entries already carried an English twin of each French bullet, so the French bullets are removed here (they stay in `CHANGELOG.fr.md`) and the English ones are kept as they are. The note under the title no longer says "translation in progress": it now says that the entries before 1.0.0 (v52 down to v1) stay in French, as they were written. They are not translated (decision of Klaatou).
- **Check**: in each batch, the number of kept English bullets equals the number of removed French bullets (18 batches, all balanced); technical identifiers are those of the existing English text (not retyped); no script or test reads the history; no file of `dist/` changes.
- **Still to update**: `REGLES.md` (rules 15 and 16: one entry in each of the two files); `REPRISE.md` (the translation plan of § 6.1 is finished: to be removed at the next handover).

### 10/11/2026: `CHANGELOG.md`: 1.2.0 and 1.1.0 sections translated into English (batch 1.9.9)

- **Requested by Klaatou**: continue the translation of the history, with the 1.2.0 and 1.1.0 sections.
- **Done**: the two sections (release entries and batches of 29/10/2026 to 01/11/2026, 1.0.1 to 1.1.8 and the entries before them) are now in English: the headings are translated; these entries already carried an English twin of each French bullet, so the French bullets are removed here (they stay in `CHANGELOG.fr.md`) and the English ones are kept as they are; the six "Test" lines that were only a file name and had no twin are kept, in the English form; in the two release entries, only the English GitHub release notes are kept and "decided by Klaatou" is removed (here and in `CHANGELOG.fr.md`); the note under the title now says that the sections from 1.0.0 down are still in French.
- **Check**: for each batch, the kept English bullets are the ones the language check (stop words, then reading) classifies as English; the one doubtful line (1.1.1) is the French twin of an English bullet and is removed; technical identifiers are those of the existing English text (not retyped); no script or test reads the history; no file of `dist/` changes.
- **Still to update**: translation of the sections from 1.0.0 down (1.0.0, then the v52 to v14 sections, to be decided with Klaatou); `REGLES.md` (rules 15 and 16: one entry in each of the two files); `REPRISE.md`.

### 10/11/2026: `CHANGELOG.md`: 1.4.0 and 1.3.0 sections translated into English (batch 1.9.8)

- **Requested by Klaatou**: continue the translation of the history, with the 1.4.0 and 1.3.0 sections.
- **Done**: the two sections (release entries and batches 1.2.1 to 1.3.5) are now in English: the headings are translated; these entries already carried an English twin of each French bullet, so the French bullets are removed here (they stay in `CHANGELOG.fr.md`) and the English ones are kept as they are; in the two release entries, only the English GitHub release notes are kept and "decided by Klaatou" is removed (here and in `CHANGELOG.fr.md`); the note under the title now says that the sections from 1.2.0 down are still in French.
- **Check**: for each batch, the number of kept English bullets equals the number of removed French bullets; technical identifiers are those of the existing English text (not retyped); no script or test reads the history; no file of `dist/` changes.
- **Still to update**: translation of the sections from 1.2.0 down (1.2.0, 1.1.0, 1.0.0, then the v52 to v14 sections, to be decided with Klaatou); `REGLES.md` (rules 15 and 16: one entry in each of the two files); `REPRISE.md`.

### 10/11/2026: `CHANGELOG.md`: 1.5.1 and 1.5.0 sections translated into English (batch 1.9.7)

- **Requested by Klaatou**: continue the translation of the history, with the 1.5.1 and 1.5.0 sections.
- **Done**: the two sections (release entries and batches 1.4.1 to 1.4.13) are now in English: the headings are translated; these entries already carried an English twin of each French bullet, so the French bullets are removed here (they stay in `CHANGELOG.fr.md`) and the English ones are kept as they are; in the two release entries, only the English GitHub release notes are kept and "decided by Klaatou" is removed (here and in `CHANGELOG.fr.md`); the note under the title now says that the sections from 1.4.0 down are still in French.
- **Check**: for each batch, the number of kept English bullets equals the number of removed French bullets; technical identifiers are those of the existing English text (not retyped); no script or test reads the history; no file of `dist/` changes.
- **Still to update**: translation of the sections from 1.4.0 down (1.4.0, 1.3.0, 1.2.0, 1.1.0, 1.0.0, then the v52 to v14 sections, to be decided with Klaatou); `REGLES.md` (rules 15 and 16: one entry in each of the two files); `REPRISE.md`.

### 10/11/2026: `CHANGELOG.md`: 1.6.0 section translated into English (batch 1.9.6)

- **Requested by Klaatou**: continue the translation of the history, with the 1.6.0 section.
- **Done**: the whole 1.6.0 section (release entry and batches 1.5.2 to 1.5.4) translated; in the release entry, "decided by Klaatou" is removed (here and in `CHANGELOG.fr.md`); the English notes of the GitHub release and the English "Fixed" bullets, already in English, are kept as they are; the note under the title now says that the sections from 1.5.1 down are still in French. Messages printed by the tools and labels of the interface that are quoted stay in their language, followed by a translation in parentheses.
- **Check**: each translation re-read against the French text; technical identifiers (options, files, tests, `file:line`) identical in both languages; no script or test reads the history; no file of `dist/` changes.
- **Still to update**: translation of the sections from 1.5.1 down (1.5.1, 1.5.0, 1.4.0, and so on); `REGLES.md` (rules 15 and 16: one entry in each of the two files); `REPRISE.md`.

### 10/11/2026: `CHANGELOG.md`: 1.7.0 section translated into English (batch 1.9.5)

- **Requested by Klaatou**: continue the translation of the history, with the 1.7.0 section.
- **Done**: the whole 1.7.0 section (release entry and batches 1.6.1 to 1.6.19, with the entries of 05/11/2026 to 07/11/2026) translated; in the release entry, only the English GitHub release notes are kept (the French ones stay in `CHANGELOG.fr.md`) and "decided by Klaatou" is removed (here and in `CHANGELOG.fr.md`); the note under the title now says that the sections from 1.6.0 down are still in French. Messages printed by the tools and labels of the interface that are quoted stay in their language, followed by a translation in parentheses.
- **Check**: each translation re-read against the French text; technical identifiers (options, files, tests, `file:line`) compared between the two languages; no script or test reads the history; no file of `dist/` changes.
- **Still to update**: translation of the sections from 1.6.0 down (1.6.0, 1.5.1 and 1.5.0, 1.4.0, and so on); `REGLES.md` (rules 15 and 16: one entry in each of the two files); `REPRISE.md`.

### 10/11/2026: documents: convoar does not recover PBR materials (batch 1.9.4)

- **Requested by Klaatou**: say in the documents that, given convoar's age, no PBR material is recovered for the moment, and say whether going further can be considered.
- **Done, in French and in English**: manual § 3: new note "Limitation: PBR materials" (convoar dates from May 2022; according to a reading of its code it does not read PBR materials; not measured; lead: read them from the OAR in `oar2glb.py`; nothing decided); one sentence in `README.md` and `README.fr.md`. No code changes (`dist\` identical).
- **Basis** (reading of code, no measurement): `convoar/convoar.csproj:11` (.NET Framework 4.8), last commit of convoar on 26/05/2022, no handling of PBR or glTF materials in its code; in OpenSim, the face's material reference is in the `ExtraParams` parameter `0x80` (`PrimitiveBaseShape.cs:1094`, `:1367-1383`), the material assets are written as `*_prmat.dat` (`ArchiveConstants.cs:129`), the per-face overrides as `<MatOvrd>` (`SceneObjectSerializer.cs:622`, `:1886`); `oar_scan` reads none of these (`oar2glb.py:418`, `:459`).
- **Not tested**: any real OAR with PBR (none available); the real output of convoar on PBR.
- **Check**: `python verif_trad.py` on the manual pair; no new error on the README pair.
- **Still to update**: `REPRISE.md` (note the subject at the next handover); translation of the sections from 1.7.0 down; `REGLES.md` (rules 15 and 16).

### 10/11/2026: `CHANGELOG.md`: 1.8.0 section translated into English (batch 1.9.3)

- **Requested by Klaatou**: continue the translation of the history, with the 1.8.0 section.
- **Done**: the whole 1.8.0 section (release entry and batches 1.7.1 to 1.7.22, with the entries of 07/11/2026 and 08/11/2026) translated; in the release entry, only the English GitHub release notes are kept (the French ones stay in `CHANGELOG.fr.md`) and "decided by Klaatou" is removed (here and in `CHANGELOG.fr.md`); the note under the title now says that the sections from 1.7.0 down are still in French. Messages printed by the tools and labels of the interface that are quoted stay in their language, followed by a translation in parentheses.
- **Check**: each translation re-read against the French text; technical identifiers (options, files, tests, `file:line`) identical in both languages; no script or test reads the history; no file of `dist/` changes.
- **Still to update**: translation of the sections from 1.7.0 down (1.7.0, 1.6.0, 1.5.1 and 1.5.0, 1.4.0, and so on); `REGLES.md` (rules 15 and 16: one entry in each of the two files); `REPRISE.md`.

### 10/11/2026: `CHANGELOG.md` translated into English: header and 1.9.0 section (batch 1.9.2)

- **Reported by Klaatou**: after batch 1.9.1, `CHANGELOG.md` still had a French title, French headings and a French 1.9.0 section, which makes no sense for an English-speaking reader.
- **Done**: title, introduction and "Unreleased" heading in English; the whole 1.9.0 section (release entry and batches 1.8.1 to 1.8.18) translated; in the release entry, only the English GitHub release notes are kept (the French ones stay in `CHANGELOG.fr.md`) and the phrase "decided by Klaatou" is removed (here and in `CHANGELOG.fr.md`); the batch 1.9.1 entry below is reworded in the same style. A note under the title says that the sections from 1.8.0 down are still in French; the next batches translate them, newest first (1.8.0, 1.7.0, 1.6.0, 1.5.1 and 1.5.0, 1.4.0 and so on), and the note is removed when the last one is done.
- **Check**: each translation re-read against the French text; technical identifiers (options, files, tests, `file:line`) identical in both languages; no script or test reads the history; no file of `dist/` changes.
- **Still to update**: translation of the sections from 1.8.0 down; `REGLES.md` (rules 15 and 16: one entry in each of the two files); `REPRISE.md`.

### 10/11/2026: `CHANGELOG.fr.md` created, `CHANGELOG.md` becomes the English version (batch 1.9.1)

- **Requested by Klaatou**: the version history must be readable in French and in English; decided: two files, like `README.md` and `README.fr.md`.
- **Done**: `CHANGELOG.fr.md` (copy of the history as it was, with a link to the English version). `CHANGELOG.md` becomes the English version: translated piece by piece, the 1.9.0 section first (batch 1.9.2), then 1.8.0, 1.7.0 and the following ones; until then the sections not yet translated stay in French. New entries are written in both files, with the same title and the same technical identifiers. The French documents that point to the history (manual, overview, index, `README.fr.md`, JSON reference) now point to `CHANGELOG.fr.md`; `HISTORIQUE.md` keeps `CHANGELOG.md` (names of the time). `verif_trad.py` treats `CHANGELOG.md` (quoted by an English document) and `CHANGELOG.fr.md` (quoted by its French counterpart) as the same name.
- **Checked**: no script or test reads the history; no file of `dist/` changes.
- **Still to update**: the translation of `CHANGELOG.md` (next batches); `REGLES.md` (rules 15 and 16: one entry in each of the two files); `REPRISE.md`.

## 1.9.0 (10/11/2026)

### 10/11/2026: release 1.9.0: blinking Walk button, Discord link in Help, no more black screen on tiled regions, convoar supplied, launcher examples list

- **Release**: 1.9.0 (10/11/2026) gathers batches 1.8.1 to 1.8.18 (described below, in this same section). New since 1.8.0: **(1)** in the global view, the "Walk (P)" button blinks after 8 s without action (black and white, never colour alone; it stops at the slightest action, and for good after a first walk); **(2)** link to the Discord server in the Help window; **(3)** opening a tiled region with a `#spawn=` or `#pos=` link: no more black screen, the global view stays visible while the ground loads; **(4)** convoar supplied in `dist\convoar\` (Windows only; copy of the `dist` folder of its repository, without the `*.pdb` files and `NLog.xml`, licences included), found by `oar2glb.py` by itself; convoar's address corrected in the READMEs, the manuals and the tool; **(5)** `web3d_gui.py`: a list of basic-use examples for every tool (it fills the fields); **(6)** `python build.py` regenerates `docs/REFERENCE_OPTIONS.md`; root of the repository tidied (`deploy\` folder); tests fixed under Windows. Documents up to date (manual § 3.9, § 7.63, § 7.64, simple procedures § 11, `DEVELOPMENT.md`). **Version numbers per built file**: `index.html`, `glb2html.py`, `glb-viewer.html` 1.8.6; `carte.html` 1.8.5; `oar2glb.py` 1.8.11; `web3d_gui.py` 1.8.17; unchanged: `glb2tiles.py` 1.4.10, `extraire_batiments.py` 1.6.3, `iar2oar.py` 1.6.4, `diag_carte.py` 1.7.7, `presence_server.py` 1.6.19 (no `scp` to the VM). **Tried by Klaatou under Windows**: the launcher and its examples list, a small conversion with the slimmed-down convoar. **Not tried**: Edge, Safari, the launcher on macOS and on Linux with a real display, the "Houses" region loading without a black screen.
- **GitHub release notes** (to attach: `galerie-photos.zip` and `region-simple.zip`, built by `python fabriquer_paquets.py` after `VERSION` is set to 1.9.0):

  > The two packages contain the new `index.html` and `carte.html` (and the `region-simple` readme has the corrected convoar address). If you already have one, copy only `index.html` and `carte.html` into your folder: do not unzip over it, that would overwrite your config, zones and images. See docs/en/SIMPLE_PROCEDURES.md section 10.
  >
  > **Release** 1.9.0. New:
  > - in the global view, the "Walk (P)" button blinks after a few seconds without action (it stops at the first action, and for good after a first walk);
  > - the Help window links to the Discord server;
  > - opening a tiled region with a `#spawn=` or `#pos=` link no longer shows a black screen: the global view stays visible while the ground loads;
  > - convoar is now supplied in `dist/convoar/` (Windows only; copy of the `dist` folder of its repository, without debug symbols, licences included) and `oar2glb.py` finds it by itself; its address is corrected in the READMEs and manuals;
  > - `web3d_gui.py` (graphical launcher): a list of basic-use examples for every tool; choosing one fills the fields;
  > - `python build.py` regenerates `docs/REFERENCE_OPTIONS.md`; the repository root is tidied (`deploy/` folder); tests fixed under Windows;
  > - documentation: manual sections 3.9, 7.63 and 7.64, simple procedures section 11, `DEVELOPMENT.md`.
  >
  > Tested on Windows by Klaatou: the graphical launcher and its examples list, a small conversion with the supplied convoar. The page changes were tested in Chromium under Linux. Not tried: Edge, Safari, the graphical launcher on macOS and on Linux with a real display.

### 10/11/2026: documents: the launcher's examples list (batch 1.8.18)

- **Requested by Klaatou**: bring the documents up to date (rule 16) after batch 1.8.17.
- **Done, in French and in English**: manual § 3.9 (the "Examples" list: what it offers, that it clears and then fills the fields, that it launches nothing, its behaviour during a launch and when the tool is changed, the `EXEMPLES` table, the message shown for an example that does not match the installed tool; "Tried" and "Not tried" lines: the examples list has not been tried under Windows), the tool's row in the § 3 table and the "Additions of 1.8.x" row; `SIMPLE_PROCEDURES.md` § 11 (one sentence); `HISTORIQUE.md` and `HISTORY.md`: batches 1.8.17 and 1.8.18. No code changes (`dist\` identical, and `VERSIONS.json` too).
- **Check**: `python verif_trad.py` on the three modified pairs: 0 errors, same warnings as before.
- **Still to update**: `REPRISE.md` (to be redone at the end of the conversation).

### 10/11/2026: examples list of basic uses in the graphical launcher (batch 1.8.17)

- **Requested by Klaatou**: review the graphical launcher; for each tool, examples of basic uses.
- **Finding**: the tools already have an "Examples" block in their help (`py.*.epilog`), but the launcher only read the options: those examples were visible only with `--help`, and written for the console.
- **Done** (`web3d_gui.py`): an "Examples" list under the tool choice. Choosing an example clears the fields and then fills them; the equivalent command is updated; the help says to replace the example names (files, address, key) with your own; nothing launches by itself. The list is inactive during a launch and goes back to its prompt when the tool is changed. `EXEMPLES` table: 5 examples for `glb2html`, 4 for `glb2tiles`, 4 for `oar2glb`, 6 for `extraire_batiments`, 4 for `iar2oar`, 2 for `diag_carte`; titles in `src/i18n` (`py.gui.ex.*`, French and English), arguments written as in a console (example names `Atoll.glb`, `ADRESSE`, `MA_CLE`). Function `lire_exemple` (the inverse of `construire`, no window); an example that does not match the options of the installed tool shows a message instead of crashing.
- **Test** (`tests/gui.py`): every example of every tool is accepted by the tool's real parser and has a title in French and in English; `lire_exemple` then `construire` give back the same parse as the example; with a window: choosing each example of the six tools gives the equivalent command, clears what was typed before and leaves no field marked "!". No tool is modified (only `dist\web3d_gui.py` changes).
- **Still to update** (rule 16, to be done when Klaatou validates): manual § 3.9 and procedures § 11 (the examples list), `HISTORIQUE.md`, `HISTORY.md`; `REPRISE.md`.

### 10/11/2026: documents up to date for 1.8.x (batch 1.8.16)

- **Requested by Klaatou**: bring the documents up to date (rule 16) after batches 1.8.1 to 1.8.15.
- **Done, in French and in English**: manual: new § 7.63 (the blinking "Walk (P)" button) and § 7.64 (Discord link in the Help window), a sentence on the end of the black background on tiles in § 8.6, "Additions of 1.8.x" row of the table of novelties; `PROCEDURES.md`: convoar supplied (§ 1.1) and the "Black page with `#spawn=…`" row of the troubleshooting table; `SIMPLE_PROCEDURES.md`: no more `--convoar` option in the example; `DEVELOPMENT.md`: `build.py` regenerates the options reference, `dist/convoar/` (not built, `-text`, `convoar_inv.*` ignored), tests added, rules for tests under Windows (`PYTHONIOENCODING`, closed input, output read during the test); `OVERVIEW.md`: `deploy/` and `dist/convoar/`; `HISTORIQUE.md` and `HISTORY.md`: batches 1.8.1 to 1.8.16. No code changes (`dist\` identical).
- **Check**: `python verif_trad.py` on the five modified pairs (0 errors required).
- **Still to update**: `REPRISE.md` (to be redone at the end of the conversation).

### 10/11/2026: `tests/compress.py` shows gltfpack's error on failure (batch 1.8.15)

- **Reported by Klaatou** (Windows): five checks of `tests/compress.py` fail; the compression of the first tile (`T_1_0_0.glb`) gives a gltfpack error whose message, cut at 400 characters by the test, ends with "sync.c, line 76"; the other tiles are compressed. The other four failures follow from it (file not compressed, not skipped on the rerun).
- **Cause not established**: the test passes here (Linux, gltfpack through `npx`); nothing in `glb2tiles.py` has changed since 1.4.10, and the only change to this test, in the previous batches (1.8.12), is `PYTHONIOENCODING=utf-8` for the `glb2tiles.py` program itself. Unverified hypothesis: the first tile's error comes from the first launch of gltfpack (installation through `npx`); only a second attempt or the full message will tell. **Done**: on failure, the test prints the "erreur, original laissé intact" ("error, original left untouched") lines in full. No blind fix.

### 10/11/2026: `tests/console.py` reads the server's output during the test (batch 1.8.14)

- **Reported by Klaatou** (Windows): "aide" (help) recognised 2 times out of 6 and 3 version lines out of 9; the end of the output (shown by batch 1.8.13) showed the help and then a single version line.
- **Cause**: the test only opened the server's output at the end (`communicate()`). A Windows pipe holds only 4 KB, the help takes about 2: after two helps, the server blocks in its `print` and processes nothing more. Under Linux the pipe holds 64 KB, hence no failure here. **Reproduced here** by reducing the pipe to 4 KB: 2 helps out of 6 and 3 version lines out of 9, as on Klaatou's machine; with the output read continuously: 6 out of 6 and 9 out of 9. The server has no defect (a real terminal reads its output).
- **Done**: a reading thread in `session()` (like `tests/v48.py` and `tests/v51.py`, which already do it). **Tested in both directions**: with the pipe reduced to 4 KB, the test failed before and passes after. `tests/ipv6.py` and `tests/oublier.py` write the output to a file: not concerned. **Not tested**: Windows itself.

### 10/11/2026: `correctifs_v52` no longer hangs under Windows; `console.py` shows its output on failure (batch 1.8.13)

- **Reported by Klaatou** (Windows): `tests/correctifs_v52.py` freezes until he presses Enter; `tests/console.py` fails ("aide" recognised 2 times out of 6, and 2 version lines instead of 9).
- **Cause of the hang**: the test launches `oar2glb.py --help` without `--nopause` and without closing the input; in a console, `oar2glb.py` waits for Enter at the end of the program, even after `--help` (`oar2glb.py:1835`, `sys.stdin.isatty()`). Without a console (sandbox) nothing blocks. Done: `stdin=subprocess.DEVNULL` for this call; the other tests that launch a tool with `--help` already close the input. The tool's behaviour does not change ("useless pause after `--help`" remains an undecided idea).
- **`console.py`, cause not established**: the test passes here (Linux) and the console reading (`console_loop`, `for line in sys.stdin`) contains nothing specific to Windows; the most plausible hypothesis is that the server does not process all the lines before the test stops it, but nothing proves it. **Done**: on failure, the test now prints the end of the server's output and the number of version lines obtained, to settle it at the next try under Windows. No blind fix.

### 10/11/2026: three tests read the processes' output as UTF-8 under Windows (batch 1.8.12)

- **Reported by Klaatou** (Windows): `tests/correctifs_v52.py` fails ("avertissement : null sans guillemets, ignore", unreadable accents: "r�ateurs").
- **Cause**: same defect as batch 1.8.10. The presence server writes into a pipe in cp1252 under Windows, and the test decodes its output as UTF-8 (`decode("utf-8")`) before looking for accented text. Reproduced here with `PYTHONIOENCODING=cp1252`, **before** the convoar batch too: it has nothing to do with it.
- **Class of the defect** (rule 7): all the tests that explicitly decode as UTF-8 the output of a child process and look for accented text in it, without forcing `PYTHONIOENCODING`: `tests/correctifs_v52.py`, `tests/console.py` and `tests/compress.py` (the others already do it, or read in text mode with the local encoding, hence consistently).
- **Done**: these three tests launch their child processes with `PYTHONIOENCODING=utf-8`. No tool code changes. **Tested in both directions**: with the output in cp1252, the three failed before and pass after; with the output in UTF-8, they pass. **Not tested**: Windows itself.

### 10/11/2026: convoar supplied in the repository, `dist\convoar\`; convoar's address corrected (batch 1.8.11)

- **Requested by Klaatou**: have convoar with Web_3d, like three.js, rather than downloading it by hand; decision: copy the folder into the repository (no automatic download).
- **Verified** (clone of `Misterblue/convoar`): `convoar.exe` is in the **`dist`** folder, not in `bin` (only 25 DLLs): the address `.../tree/master/bin` was wrong in `oar2glb.py` (`CONVOAR_URL`), the two READMEs, the two manuals, the `region-simple` package's `readme.html` and the `correctifs_v52` test; it becomes `.../tree/master/dist` everywhere. `dist`: 148 files, 19.6 MB; copy without `*.pdb` (15 files, debug symbols) and `NLog.xml` (NLog's documentation, not a configuration): 132 files, about 11 MB, 3.7 MB compressed. Last commit of convoar: `be7abbedc0d7d295a76800b2fe2e1fc9a58a7934` (26/05/2022, version 2.0.6), Apache 2.0 licence.
- **Done**: `dist\convoar\` (supplied as a zip, unpacked into `dist\`; `LICENSE`, `THIRDPARTYLICENSES\`, `ORIGINE.txt`, `SHA256SUMS.txt` with the hash of each file); `oar2glb.py` looks for convoar in this order: `--convoar`, the `CONVOAR` variable, `convoar` in the PATH, `convoar\convoar.exe` next to it, `convoar.exe` next to it (old location, still accepted), and names `convoar\convoar.exe` if it finds none (`default_convoar()`); help and error texts, READMEs, manuals, `GUIDE.md` § 1.2, the package's `readme.html`: convoar is supplied, the address is the source's; `.gitattributes`: `dist/convoar/** -text` (git does not touch line endings: otherwise the hashes no longer match); `.gitignore`: `dist/convoar/convoar_inv.*` (launcher that `oar2glb.py` builds at the first conversion); `tests/dist_a_jour.py` ignores `dist/convoar/` (supplied copy, not built); `THIRD-PARTY.md`.
- **Licences**: convoar is under Apache 2.0; its components under three-clause BSD licences (OpenSimulator, libopenmetaverse, Radegast, LookingGlass, Intel) or Apache 2.0 (InWorldz.PrimExporter): the texts supplied by convoar are copied into `dist\convoar\THIRDPARTYLICENSES\`. **Not verified**: the licences of the components that convoar ships without any licence (NLog, Mono.Addins, Nini, log4net, SmartThreadPool, nunit, openjpeg, zlib.net, `System.*`). No `NOTICE` in convoar. No LGPL library in `dist`.
- **Test**: new `tests/convoar_dist.py` (SHA-256 manifest, content, search order of `default_convoar()`, git attributes); `tests/correctifs_v52.py` adapted (isolated copy of `oar2glb.py`). **Not tested**: convoar itself (no Windows or .NET in the sandbox): **to be tried by Klaatou with a small conversion before committing**; removing `*.pdb` and `NLog.xml` changes nothing at run time in .NET, but this has not been tried. The 3.7 MB compressed enter the public history for ever.

### 10/11/2026: `build.py` and `tests/build_reference.py`: processes' output read as UTF-8 under Windows (batch 1.8.10)

- **Reported by Klaatou** (Windows): two checks of `tests/build_reference.py` fail ("relance sans changement" (rerun without change), "date seule différente" (only the date differs)); the console shows "� jour (inchang�)".
- **Cause** (reproduced here with `PYTHONIOENCODING=cp1252`): under Windows, a Python process whose output goes into a pipe writes in the system code page (cp1252), while the test read this output as UTF-8: "à jour (inchangé)" became unreadable and was not recognised. `build.py` read the output of `gen_reference.py` (`[manque]` lines) in the same way. The written file, for its part, was correct (UTF-8).
- **Done**: `build.py` and the test launch their child processes with `PYTHONIOENCODING=utf-8`. **Tested in both directions**: with the output in cp1252 and then in UTF-8, the whole test passes (it failed in cp1252 before). **Not tested**: Windows itself (to be run again on Klaatou's machine).

### 10/11/2026: `build.py` regenerates `docs/REFERENCE_OPTIONS.md` (batch 1.8.9)

- **Requested by Klaatou**: have `gen_reference.py` launched automatically by the build, instead of a manual step that must not be forgotten.
- **Done** (`build.py`): at the end of the build, when the output is the real `dist\`, the options reference is regenerated from the freshly built `dist\` ("[OK] docs/REFERENCE_OPTIONS.md : refait" (regenerated)) and rewritten only if its content changes apart from the "Générée le jj/mm/aaaa" (generated on) line (otherwise "à jour (inchangé)" (up to date, unchanged): no modification every day). Written in bytes, LF everywhere. With `--out` other than `dist\`: nothing is written, like `VERSIONS.json` (so `tests/dist_a_jour.py` changes nothing). An option without a description is reported (`[manque]`, "missing") without stopping the build; a failure of the generation (for example `websockets` missing to read `presence_server.py`) gives a warning, not an error. About 1.5 s more (measured). `python gen_reference.py` remains usable by hand. `git add -A` takes the file with the batch.
- **Test**: new `tests/build_reference.py` (copy of the repository in a temporary folder: missing file recreated, rerun without change, date-only difference not rewritten, different content rewritten, `--out` without writing). **Sandbox warning**: Python 3.12 produces a slightly different text from Klaatou's; the verification builds rewrite the file, which is never delivered from the sandbox. Manuals `MANUEL.md` § 7.50 and `MANUAL.md`: one sentence corrected.

### 10/11/2026: `REFERENCE_OPTIONS.md` moved into `docs\` (batch 1.8.8)

- **Requested by Klaatou**: put `REFERENCE_OPTIONS.md` (a generated, bilingual file) with the documents.
- **Done**: the file goes to `docs\REFERENCE_OPTIONS.md` (`git mv`). `gen_reference.py` now writes it there by default (docstring, help of `--output` and default output); `tests/doc_options.py` and `tests/samples.py` look for it there; the mentions in the two READMEs, the manuals, guides, indexes, overviews, procedures and the `region-simple` package's `readme.html` give the new path (`docs/REFERENCE_OPTIONS.md`). The content of the file does not change. The old mentions in the history (`CHANGELOG.md`, `HISTORIQUE.md`, `HISTORY.md`) are left as they are.
- **Still to update**: `REPRISE.md` and `REPRISE_ARCHIVE.md` still cite the file at the root (to be corrected at the next handover, rule 23). The `region-simple.zip` and `galerie-photos.zip` packages only contain the new path after the next build (`fabriquer_paquets.py`).

### 10/11/2026: tidying the repository root (batch 1.8.7)

- **Requested by Klaatou**: clean up the repository. Result: nothing to delete (every file is cited by the code, the tests or the documents).
- **Done**: `lance_presence.sh` and `web3d-presence.service` moved into `deploy\` (templates for the VM: no test cites them, the documents only give their names); `ETUDE_MEGAREGION.md` moved into `docs\fr\`; mentions corrected in `docs/fr/VUE_ENSEMBLE.md` and `docs/en/OVERVIEW.md`. No code changes (`dist\` identical).
- **Left at the root**: `README.md`, `README.fr.md`, `LICENSE`, `THIRD-PARTY.md`, `CHANGELOG.md`, `VERSION`, `VERSIONS.json`, `build.py` (cited everywhere), `REPRISE.md` and `REPRISE_ARCHIVE.md` (rule 1 of `REGLES.md`), `REFERENCE_OPTIONS.md` (generated file, read at the root by `tests/doc_options.py`). `gen_reference.py`, `verif_trad.py` and `fabriquer_paquets.py` do not move: each computes its root from its own location, four tests refer to them and about forty lines of documents give their commands; a `dev\` folder remains possible, in a separate batch.
- **Still to update**: `REPRISE.md` still cites `ETUDE_MEGAREGION.md` at the root (to be corrected at the next handover, rule 23).

### 10/11/2026: arriving through a link (`#spawn=`) on a tiled region: no more black screen, the global view stays visible (batch 1.8.6)

- **Reported by Klaatou**: with a `#spawn=default` link, the window stays black with "Chargement du sol… N s" (Loading the ground… N s) during the whole loading of a large region (Houses); from the global view, the region is visible.
- **Cause** (reproduced in Chromium, region of 16 tiles, tiles retained): `template.html` put the black `#fade` background on as soon as the page opened when the link asks for an arrival; it was only removed after `viewer.loadBuffer`, which waits for the arrival tile (15 s at most, `core.js`). Measurement: overview ready at 4.7 s, black screen (94 % of dark pixels) until the tile arrives.
- **Done** (`src/template.html`): tiled region: no more black background at startup through a link; the global view, then the overview as soon as it is ready, stay visible under the "Chargement du sol… n/m tuiles prêtes · N s" (Loading the ground… n/m tiles ready · N s) frame, as from the global view. The walk still starts as soon as the tile is ready; the switch to the avatar is clean, as with the P key. Single-GLB region: black fade unchanged. The loading time does not change, only the display changes. **Decision of v33 modified** ("never a black screen without text": the text stays, the black disappears for tiles).
- **Tests**: new `tests/demarrage_lien.py` (tiles: no black, text, walk when the tiles arrive; single GLB: black kept); `tests/v33.py`: five lines adapted (black is no longer expected for tiles). **Not tested**: Edge, Windows, the real Houses region.

### 10/11/2026: the "Walk (P)" button blinks in the global view, Discord link in Help (batch 1.8.5)

- **Requested by Klaatou**: show visibly, in the global view, that P has to be pressed to switch to walking; Discord link in the Help window (decision expected from § 6.1 of `REPRISE.md`: yes).
- **Done** (`src/template.html`): in the global view, after 8 s without action (mouse, wheel, keyboard, touch), the Walk button blinks (class `pulse`, background and text alternating black/white, 1.2 s per cycle: no dependence on colour, fewer than 3 flashes per second). The slightest action stops it; 8 s of inactivity start it again; once in walk mode, it no longer blinks until the page is reloaded; the model's loading time does not count. If the system asks for reduced motion: no blinking, thick border. The 8 s delay is an estimate (constant `IDLE`). The label stays "Promenade (P)" (Walk (P)). A "Discord (questions, aide, nouveautés)" (questions, help, news) link added under "Aide des visiteurs" (visitors' help) in the Help window (`page.help.discord`, French and English), same address as the READMEs.
- **Test**: `tests/bouton_promenade.py` (delay, black/white alternation, stop on action, restart, stop after the walk, reduced motion, Discord link in French and in English). **Not tested**: Edge, Windows, a real touch screen (the bar is hidden there).
- **Note**: the two commits of 10/11/2026 ("Where to start?" sections in `README.md` and "Getting Started" in `README.fr.md`, made by Klaatou on GitHub) touch no code.

### 08/11/2026: `REPRISE.md`: rule 25 is already up to date (batch 1.8.4)

- **Error corrected**: `REPRISE.md` (batch 1.8.3) said that Klaatou had to update rule 25 of `REGLES.md`; the Project's `REGLES.md` already contains "plus NightshadeCeres (accord du 08/11/2026)" (plus NightshadeCeres, agreement of 08/11/2026). § 5 now says so, and the matching bullet of § 6.1 is removed. Documents only; no file of `dist/` changes.

### 08/11/2026: `REPRISE.md` up to date and lighter, appendix in `REPRISE_ARCHIVE.md` (batch 1.8.3)

- **Requested by Klaatou**: move to a new conversation with an up-to-date `REPRISE.md` (rules 22 and 23); lighten the file (116 KB).
- **Done**: `REPRISE.md` (69 KB): header rewritten (state after 1.8.0, numbers per file, list of batches 1.7.12 to 1.8.3), § 2.1 and § 6 rewritten, decisions and pitfalls of 08/11/2026 added (convoar kept, graphical launcher, Discord, exception to rule 25, release 1.8.0; sandbox commands and pitfalls); § 1, 2.2, 2.3, 3, 4, 5 and 7 kept as they were (four small updates: sections 2.2 and 3). Everything that left the file (old header, old § 2.1, old § 6.1 to 6.2) is taken up **word for word** in the appendix of `REPRISE_ARCHIVE.md` (192 KB): no line is lost, except one bullet of § 2.2 modified in place (presence VM version).
- **Check**: no mention of colour blindness and no personal names in the file (the only proper name added is the macOS tester's, with his agreement).

### 08/11/2026: `web3d_gui.py`: clearer command label (batch 1.8.2)

- **Reported by Klaatou**: "Commande (à taper dans le dossier de l'outil)" (Command (to type in the tool's folder)) suggests that the command has to be typed; some users will not see the Run button.
- **Done**: the label becomes "Commande équivalente (à titre d'information : le bouton Lancer l'exécute pour vous)" (English: "Equivalent command (for information: the Run button runs it for you):"). Text only (`py.gui.command`), in French and in English; no code changes.
- **Not tested**: the look of the window under Windows (the line is longer than before).

### 08/11/2026: `tests/gui.py`: no more Tcl message "application has been destroyed" (batch 1.8.1)

- **Reported by Klaatou** (Windows): when running `tests/gui.py`, Tcl writes "can't invoke "event" command: application has been destroyed" (`ttk::ThemeChanged` procedure); the test nevertheless ends with "tout est passé" (all passed).
- **Probable cause** (not reproduced here: Tk 8.6.14 under Linux writes nothing): the test opened a first Tk window to check that a display exists, destroyed it at once, then opened the launcher's window; a theme task left pending for the first one then ran, its window already destroyed.
- **Done**: there is no first window any more: the test creates the launcher's window directly. Without a display (Tcl error mentioning "display"), it skips the window part as before; any other error of the window is raised again, not mistaken for the absence of a display. No file of `dist/` changes.
- **Test**: without a display: `[IGNORE]` and code 0; with a display: the 55 checks; a deliberate fault (unknown option given to a widget) makes the test fail instead of being ignored. **Not tested**: under Windows (disappearance of the message).

## 1.8.0 (08/11/2026)

### 08/11/2026: release 1.8.0: graphical launcher and Windows shortcuts, `diag_carte.py`, READMEs and documents rewritten

- **Release**: 1.8.0 (08/11/2026) gathers batches 1.7.1 to 1.7.22 (described below, in this same section). New since 1.7.0: **(1)** `web3d_gui.py`, a graphical launcher for the six tools (`glb2html`, `glb2tiles`, `oar2glb`, `extraire_batiments`, `iar2oar`, `diag_carte`): tool list, one line per option read from the tool itself, help for each option, command line, launch and output, repeatable options, `--tool`, File and Folder buttons; **(2)** `--shortcuts` creates Windows shortcuts on the desktop (one for the window, one per tool) with the project icon; `--dry-run`, `--remove-shortcuts`, `--shortcuts-folder`; **(3)** `diag_carte.py` enters `tools` and `dist`: it tells you why the map shows no nicknames; **(4)** READMEs rewritten (introduction, glossary, SVG diagrams, features) with a link to the Discord server; **(5)** documents: manual § 3.9 and § 9.22, simple procedures § 11, `DEVELOPMENT.md` § 6, `INDEX.md`, histories, shortcuts image; **(6)** tests: `gui.py`, `diag_carte.py` and `readme_liens.py` are new; `v32`, `v37`, `textes_outils` and `tools_lang` fixed (waiting for a condition, closed input, Windows language); **(7)** the macOS tester's name (NightshadeCeres, with his agreement) in the documents. **Unchanged since 1.7.0**: the page, the viewer, `glb2html.py`, `glb2tiles.py`, `oar2glb.py`, `extraire_batiments.py`, `iar2oar.py`, the presence server (1.6.19) and the two packages (their zips only write "Web_3d 1.8.0" in `VERSION.txt`).
- **GitHub release notes** (to attach: `galerie-photos.zip` and `region-simple.zip`, built by `python fabriquer_paquets.py` after `VERSION` is set to 1.8.0):

  > The two packages are unchanged since 1.7.0 (only the version written in their `VERSION.txt` changes): if you already have one, there is nothing to update. If you do update, do not unzip over your folder: it would overwrite your config, zones and images. See docs/en/SIMPLE_PROCEDURES.md section 10.
  >
  > **Release** 1.8.0. New:
  > - `web3d_gui.py`: a graphical launcher for the tools (`glb2html`, `glb2tiles`, `oar2glb`, `extraire_batiments`, `iar2oar`, `diag_carte`): choose the tool in a list, fill in the options (the help of each option shows under the pointer), see the resulting command, run it and read its output; `--tool NAME` opens it on one tool;
  > - `python web3d_gui.py --shortcuts` creates Windows shortcuts on the desktop (one for the window, one per tool) with the Web_3d icon; `--dry-run` shows what would be done, `--remove-shortcuts` removes them;
  > - `diag_carte.py`: tells you why the world map shows no nicknames (it queries the presence server with and without the key);
  > - the READMEs are rewritten (introduction, glossary, diagrams, features) and link to the Discord server;
  > - documentation: manual sections 3.9 (graphical launcher) and 9.22 (map nicknames), simple procedures section 11, `INDEX.md`;
  > - the page, the viewer, the other tools, the presence server and the packages are unchanged since 1.7.0.
  >
  > Tested on Windows by Klaatou: the graphical launcher, the tool list, the file and folder pickers and the shortcuts. Reported earlier by NightshadeCeres: the macOS launcher and the region display work on macOS Ventura 13.7.8 with Firefox 159.0.1. Not tried: the graphical launcher on macOS and Linux, Safari.

### 08/11/2026: `web3d_gui.py`: File and Folder buttons on the output fields (batch 1.7.22)

- **Finding** (while answering Klaatou, who found that the pickers worked well): the **output** fields did not have the File… and Folder… buttons: `-o` of `glb2html.py`, `--output` of `glb2tiles.py` and `oar2glb.py`, `-o` of `extraire_batiments.py`, and `--convoar` of `oar2glb.py`. **Cause**: the launcher recognises a path by its type, its metavar or its name (`DEST_CHEMIN`), and the internal name of these options (`output`, `sortie`, `convoar`) was not in it.
- **Done**: `output`, `sortie` and `convoar` added to `DEST_CHEMIN`. The buttons offer both a file and a folder, because several of these fields accept either (`-o` of `glb2html.py`: ".html file, or folder") or a folder (`glb2tiles.py`, `extraire_batiments.py`).
- **Test**: `tests/gui.py`: eleven file or folder fields (inputs, outputs, `convoar`) must have the buttons; a deliberate fault (removing `sortie`) is detected.

### 08/11/2026: documents of the graphical launcher, shortcuts image, new Discord link (batch 1.7.21)

- **Requested by Klaatou**: document the graphical launcher; add its shortcuts image; put the Discord link where it is useful; new Discord invitation without expiry (the old one is replaced).
- **Done**: manual § 3.9 (launcher `web3d_gui.py`: tools, window, fields to correct, default values, shortcuts, trials), row in the § 2 table, § 7.50, "Additions of 1.7" row of the appendix, in French and in English; `PROCEDURES_SIMPLES.md` § 11 (French and English); `INDEX.md`: two lines (window and shortcuts, asking a question); `README.md` and `README.fr.md`: `web3d_gui.py` row of the table of built files and the new Discord link; `VUE_ENSEMBLE.md` and `OVERVIEW.md`: version 1.7.21, `web3d_gui.py`, trials, Discord link; `HISTORIQUE.md` and `HISTORY.md`: rows for batches 1.7.13 to 1.7.21; new image `docs/images/raccourcis.png` (Klaatou's capture: the seven shortcuts on the Windows desktop).
- **Not done**: the Discord link in the page's Help window (a code change, to be decided); `REPRISE.md` (delivered at the handover).

### 08/11/2026: link to the Discord server in the READMEs (batch 1.7.20)

- **Requested by Klaatou**: a link to his Discord server in the repository.
- **Done**: a line under the demo link, at the top of `README.md` and `README.fr.md` ("Questions, aide, nouvelles : rejoindre le serveur Discord" (Questions, help, news: join the Discord server) in the French one). The link is a public Discord invitation; it could not be opened here: if the invitation expires, the link stops working (Discord allows creating an invitation that never expires).

### 08/11/2026: shortcuts with the project icon, and `textes_outils` no longer hangs in a console (batch 1.7.19)

- **Requested by Klaatou**: the shortcuts created by `--shortcuts` (1.7.18) show Python's icon; they must have the project icon.
- **Done**: `$s.IconLocation` points to `favicon.ico` (next to `web3d_gui.py` in `dist/`, copied by `build.py`, otherwise in `src/`): it is exactly the 64 x 64 image of the "Made with Web_3d" icon (`src/credit.png`), in an `.ico` file of four sizes (16, 32, 48, 64). Without this file, the shortcuts keep Python's icon and the script says so. `--dry-run` states the icon chosen. For shortcuts already created: running `--shortcuts` again replaces them.
- **Test**: `tests/gui.py`: the icon is set before `Save` when it exists, and only in that case; `--dry-run` names it. **Not tested**: the display of the icon under Windows (Explorer's icon cache).
- **Reported by Klaatou**: `tests/textes_outils.py` stopped under Windows with `TimeoutExpired` (60 s) on `glb2tiles.py --help`, twice in a row. **Cause**: at the end of `glb2tiles.py` (and of `oar2glb.py`), the tool waits for Enter ("Entrée pour fermer", Enter to close) when the standard input is a console and `--nopause` is not given, **even after `--help`** (`glb2tiles.py` line 2249: the `SystemExit` of `--help` is caught, then the pause). The test launched the tool without closing its input: it inherited Klaatou's console. In the sandbox the input is not a console, hence green tests. **Reproduced** here with a pseudo-terminal as input: `glb2tiles.py --help` and `oar2glb.py --help` do not finish; with `--nopause` or a closed input, they finish in 0.1 s; `extraire_batiments.py`, `iar2oar.py`, `diag_carte.py`, `glb2html.py` and `web3d_gui.py` do not have this defect.
- **Done**: `tests/textes_outils.py` launches the tools with the input closed (`stdin=subprocess.DEVNULL`); the other tests that launch these two tools already close the input (`tools_lang.py`, `v37.py`) or pass `--nopause`. The tools are not modified (the pause is intended for windows opened by double-click).

### 08/11/2026: `web3d_gui.py`: Windows shortcuts (batch 1.7.18)

- **Requested by Klaatou**: shortcuts to launch the interface, from the desktop or elsewhere.
- **Done**: `python web3d_gui.py --shortcuts` creates seven shortcuts (`.lnk`): "Web_3d - lanceur" (the window) and one per tool (`--tool NAME`). They launch `pythonw.exe`, hence without a black console window; the program is the one that ran the script (if Python is moved or reinstalled, run `--shortcuts` again). `--dry-run` shows the plan without writing or deleting anything; `--remove-shortcuts` deletes those only; `--shortcuts-folder FOLDER` chooses another folder; without a folder, the desktop is asked from PowerShell (a OneDrive redirection is followed). The creation goes through a PowerShell script written in UTF-8 with BOM (accents in paths) and launched with `-ExecutionPolicy Bypass` for this single call only. Texts in French and English (`py.gui.*`).
- **Test**: `tests/gui.py`: plan of the shortcuts (one for the window, one per tool), PowerShell script (doubled apostrophe, quoted arguments), `--dry-run` (nothing written), clear refusal outside Windows, removal (only the shortcuts of `web3d_gui.py` go). Two deliberately introduced faults (apostrophe not doubled; deletion of any `.lnk`) are detected.
- **Not tested**: the real creation of the `.lnk` files (Windows only), the detection of the desktop, the behaviour when a group policy forbids PowerShell. **Not done**: Linux and macOS.

### 08/11/2026: `web3d_gui.py`: all the tools (batch 1.7.17)

- **Requested by Klaatou**: extend the graphical launcher to the other tools; reported by Klaatou: `--spectate` and `-o` showed no default value.
- **Done**: a "Tool" list at the top of the window: `glb2html`, `glb2tiles`, `oar2glb`, `extraire_batiments`, `iar2oar`, `diag_carte` (the options of each are read from the tool, no tool is modified); `--tool NAME` opens the window on one tool (useful for a shortcut). Repeatable option (`--exclude`, `--group`): a multi-line field, one line = one repetition of the option. File… and Folder… buttons also for the `oar`, `glb` and `iar` arguments. Changing tool is refused while a tool is running.
- **Default described in the help**: when an option has no numeric default but its help text talks about it, the line shows "défaut : voir l'aide" (default: see the help) (instead of nothing) and the help panel says "voir le texte ci-dessus" (see the text above). Cases: `--spectate` (active as soon as a `--presence-url` is given) and `-o` ("<name> - Offline.html" next to the `.glb`, and not the launch folder).
- **Test**: `tests/gui.py`: for each of the 6 tools, each option, alone, gives a line accepted by the tool's real parser; repeatable option; tool change; default described in the help. A deliberately introduced fault (only the first line repeated) is detected.
- **Limits**: reading the options of `oar2glb.py` writes its journal `oar2glb.log` next to the tool (behaviour of this tool, already true for `gen_reference.py`); `presence_server.py` is not in the list (a server that stays running). **Not tested**: under Windows.

### 08/11/2026: `tools_lang`: "unknown system language" check ignored under Windows (batch 1.7.16)

- **Reported by Klaatou**: under Windows in French, `tests/tools_lang.py` fails on "langue du système inconnue : anglais" (unknown system language: English) (1 failure); the other tests pass.
- **Cause**: `i18n_py.py` (`i18n_system_lang`) falls back on Windows' interface language when `LANG` gives no known language; on a Windows in French, the help therefore comes out in French. This fallback has existed since v36, and `dist/glb2html.py` did not change in batch 1.7.14. Not reproduced here: Linux does not have this fallback.
- **Done**: the test ignores this single check (`[IGNORE]` line) when it runs under Windows and Windows' interface language is French or English; elsewhere it is unchanged. No file of `dist/` changes.
- **Not tested**: under Windows; the Windows branch was tried here with a fake `ctypes`.

### 08/11/2026: macOS tester's name in the documents (batch 1.7.15)

- **Requested by Klaatou**: put the macOS tester's name in the documentation. **Agreement**: NightshadeCeres gave it in the demo's discussion thread ("of course"), seen by Klaatou on 08/11/2026.
- **Done**: the name appears in `README.md` and `README.fr.md` (with a link to his profile), in the manual (Firefox, French and English), in the overview (French and English) and in the 07/11/2026 entry of this file. The 1.7.0 notes remain anonymous: they are aligned with the description already published.
- **Exception to rule 25** (no personal name in the public repository): only for this person, with his explicit agreement.

### 08/11/2026: graphical launcher `web3d_gui.py` for `glb2html.py` (batch 1.7.14)

- **Requested by Klaatou**: a graphical interface for the tools, first for `glb2html.py`, with the help of the options; no 3D preview.
- **Done**: new tool `tools/web3d_gui.py` (built into `dist\`, `tkinter` only, no other dependency). One line per option of `glb2html.py` (70), read from the tool itself with the technique of `gen_reference.py`: `glb2html.py` is not modified. The option's help shows on hover and on entering the field; search filter; checkboxes; yes/no for the `--x` / `--no-x` options; lists for the choices; File… and Folder… buttons; "option alone" checkbox for options with an optional value; decimal comma accepted; negative value written `--option=-5`; unreadable field marked with a "!" (never by colour alone) and launch refused with the message; command line displayed and copyable; Run button (Ctrl+Enter) that executes the tool and shows its output; Stop button. Texts in French and English (`py.gui.*`). `build.py`, `gen_reference.py` and the tests `marque`, `textes_outils` and `tools_lang` know the new tool.
- **Test**: new `tests/gui.py`. Without a window: the 70 options, one by one, give a line that the real parser of `glb2html.py` accepts; construction of the line; checking of the fields. With a display (`xvfb-run`): window, command, filter, help, real launch of the tool. Two deliberately introduced faults (yes/no inverted, decimal comma kept) are detected.
- **Not tested**: under Windows (window, file pickers, clipboard, absence of a console window) and under macOS; the file pickers are not opened by the test.
- **Not done**: manual, procedures and READMEs (rule 16, at validation); the other tools (one line in `OUTILS` for each); 3D preview.

### 08/11/2026: tests `v37` and `v32`: wait for the condition, not for a duration (batch 1.7.13)

- **Requested by Klaatou**: review the unstable tests.
- **Cause**: `v37` read the compass 250 or 300 ms after a heading change, while the page updates it every 100 ms (`compassTick`, `setInterval`); `v32` waited 500 ms then read the viewer's tiles line, filled by `afterLoadTiles`, which runs after the end of `loadTiles`. On a slow processor (single-core sandbox), the reading came before the update: `v37` failed on "NE 45°" and `v32` on two checks, **even when launched alone**.
- **Done**: the fixed pauses become waits for the condition (10 s at most for the compass, helper `attendre_js` in `tests/v37.py`; `wait_for_function` in `tests/v32.py`); all the compass readings of `v37` that followed a fixed pause are fixed (global view heading, N 0°, the five headings, unchecked box, rotation, English). The check that follows still says whether the condition is true: a real defect still fails.
- **Measured** (sandbox, Chromium, one core): before, `v37` and `v32` failed alone; after, they pass. `v35`, `v36` and `v41` pass alone and with the processor saturated by two loops: their instability was not reproduced, they are not modified. `image_dossier` fails alone on `main`: Chromium stops (`int3` trace in `chrome-headless-shell`) when opening the second page of the same context, also when the first is not closed before; cause not elucidated, test not modified.

### 08/11/2026: documents up to date (batch 1.7.12)

- **Requested by Klaatou**: "il faut qu'on soit à jour" (we have to be up to date) (rule 16, documents behind).
- **Done**: `diag_carte.py`: new manual § 9.22 (French and English), row of the § 2 table, `--lang` in § 7.50, step 4 of `PROCEDURES.md` § 7 and paragraph of `PROCEDURES_SIMPLES.md` § 4; README images: new § 6 of `DEVELOPPEMENT.md` / `DEVELOPMENT.md` (hand-drawn SVGs, `tests/readme_liens.py`); `INDEX.md`: two lines added; the "not tested" mentions of `extraire_batiments.py` (§ 3.7) and `iar2oar.py` (§ 3.8) become "tried by Klaatou" (reported by Klaatou on 08/11/2026); animated GIFs: checked by Klaatou under Windows and Firefox (§ 5.11); `VUE_ENSEMBLE.md` and `OVERVIEW.md` brought back to the state of 08/11/2026 (version, extraction and diagnostic tools, trials, what is left to do); manual appendix (§ 13: "Additions of 1.7" row and § 13.3); `HISTORIQUE.md` and `HISTORY.md`: rows for batches 1.7.2 to 1.7.12.
- **Not done**: `REPRISE.md` (delivered only at the handover, rule 23); no file of `dist\` or `VERSIONS.json` changes.

### 08/11/2026: `REPRISE.md` updated for the handover to a new conversation

- **Requested by Klaatou**: handover after 9 batches in the same conversation (rule 22).
- **Done**: state on 08/11/2026 (`VERSION` 1.7.11, number of each built file including `diag_carte.py` 1.7.7); new paragraph on batches 1.7.2 to 1.7.11 with the decision on the French names and the sandbox notes; § 6.1 "To do and to remember" updated (tests fixed, GIF checked under Windows and Firefox, convoar subject to resume, documents behind); the three references to `CLOUD_RAPPORT.md` say where to find it in the git history. Updated by passages (the file is 111 KB), not in full. No file of `dist\` changes.

### 08/11/2026: READMEs (fr and en): SVG diagrams corrected, site tree as a file explorer

- **Requested by Klaatou**: a site tree closer to what you see in the file explorer, with `aide.html` and the `about` files; take into account a reviewer's remarks on the diagram.
- **Done**: `docs/images/site.en.svg` and `site.fr.svg` replace the text tree (explorer window: chevrons, folder and file icons by type, "Nom" (Name) and "Rôle" (Role) columns, "une région" (one region) brace; `aide.html` at the root, `NAME.about.fr.txt` and `NAME.about.en.txt` in the region's folder, according to the manual). "How it works" diagram corrected: direct input of a `.glb` without OAR, `NAME.tiles.json` added to the tiles (it is the file that `glb2html.py --tiles` reads), "GLB or tiles" labels on the arrows to the viewer and to `glb2html.py`, steps `3a` and `3b` separated by "OR" with the settings files repeated, viewer "exports the page (except in tiles)", "The model" frame in solid line (dotted now only means optional). No file of `dist\` changes.

### 08/11/2026: READMEs (fr and en): the "How it works" diagram becomes an SVG image

- **Requested by Klaatou**: a diagram more readable than the text drawing, and exact about the viewer, which also exports the page.
- **Done**: `docs/images/fonctionnement.en.svg` and `fonctionnement.fr.svg` (hand-drawn, editable SVG text; white background so readable in dark mode; nothing carried by colour alone: thick outline for a tool, dotted lines for optional, numbered steps, legend). The diagram shows the model (GLB, optional tiles), the two ways of doing step 3 (interactive viewer that exports the page; `glb2html.py` on the command line, indispensable for a tiled region), the page and the optional presence server. The paragraph under the diagram is corrected: the viewer does not only prepare, it exports the page; for a tiled region it only places the zones. The tree of a site stays in text. The test `tests/readme_liens.py` checks that the two images exist. Rendering checked in Chromium only, not on GitHub. No file of `dist\` changes.

### 08/11/2026: READMEs (fr and en): diagram of the tool chain and tree of a site

- **Requested by Klaatou**: show the organisation of the tools and that of a site (shell at the root, one folder per region).
- **Done**: "How it works" section (OAR, `oar2glb.py`, GLB, `glb2tiles.py` for huge regions, viewer for the settings and zones, `glb2html.py`, page; the presence server is a separate program to which the page connects); tree of a site in the section "A site: a shell, one folder per region" (`index.html`, `carte.html`, `regions.json`, `default.json`, `lib/`, one folder per region with `NAME.glb` or the tile files, `NAME.config.json`, `NAME.zones.json`, `medias/`), in plain text, without colour, with legends in French and English. Layout re-read in the manual § 6.2, § 6.7 and in the section on image zones (`medias` folder next to the `.glb`). No file of `dist\` changes.

### 08/11/2026: `diag_carte.py` enters the repository (tools, dist, messages fr/en, `--lang`, `--version`)

- **Requested by Klaatou**: integrate the map diagnostic tool, which was lying at the root of the repository without being cited anywhere.
- **Done**: `diag_carte.py` moves from the root to `tools/` (same mechanism as `extraire_batiments.py`: `MARK` line, version, French and English texts in `src/i18n`, `--lang`, `--version`, translated help), built into `dist/` by `build.py`; same diagnostics and same exit codes as before (0 good server, 1 unreachable, 2 old server, 3 no nickname with the key, 4 origin refused); the origin example uses `https://VOTRE-SITE` instead of a real address; added to `build.py`, `gen_reference.py` (`REFERENCE_OPTIONS.md` regenerated), `tests/marque.py`, `tests/textes_outils.py`, `tests/tools_lang.py` and to the file table of the two READMEs; new test `tests/diag_carte.py` (fake presence server: good case, old server, no key, nobody online, unreachable, origin refused, help and version in French and English). English README: the French names `carte.html`, `lancer-*` and `renommer-*` are translated at their first mention.
- **Defect fixed along the way**: the old script decided "origin refused" from the digits of the error message (`403` or `4003`); an unreachable server whose port number contains `403` (for example 54003) was therefore taken for an origin refusal. The refusal is now recognised by the HTTP 403 response or the 4003 closure, never by the text; the test tries a port ending in `403`.
- **To complete at validation (rule 16)**: manual and procedures (French and English) do not yet mention `diag_carte.py`.

### 08/11/2026: READMEs (fr and en): features, two kinds of page, package contents, update

- **Requested by Klaatou**: present to the newcomer what web_3d does, the difference between a standalone page and a page with a shell, what a package contains and what needs a server.
- **Done**: sentence about the GLB corrected (it is the web_3d page that displays it, in an ordinary browser); new sections "What you can do", "Two kinds of page" (the standalone page is shared as a single file, with its limits: image zones from disk, no standalone export in tiles), "Ready-to-use packages"; only the presence server needs something other than basic web hosting; contents of a package (`site/` is published, `presence/` never on web hosting, `.bat` launchers for Windows, `.sh` for Linux, `.command` for macOS); trying at home and publishing presented as two separate things; update: `aide.html` copied only if it has not been adapted; viewer on a tiled region: zones only, no longer the command line written; false sentence corrected ("the files of `dist/` are not versioned"); last tag `v49` removed. No file of `dist\` changes.

### 08/11/2026: READMEs (fr and en): introduction at the top, glossary, version tags removed

- **Requested by Klaatou**: a README lighter at the entrance, in both languages, without touching the rest.
- **Done**: the paragraph saying what web_3d is moves right after the demo link, followed by three glossary lines (OAR, GLB, tiles); the `vNN` tags in the text (table of files, map, windows, commands, light rendering, visit journal, hosting) are removed, they stay in the CHANGELOG and the history; the list of tests `v23.py` to `v51.py` is kept (they are file names). No file of `dist\` changes.

### 08/11/2026: new test `tests/readme_liens.py`: local links and images of the documents

- **Cause**: the README's demo GIF (`docs/images/PalmIsland_demo.gif`) had been deleted from the repository on 07/11/2026 (commit `74fe691`, swept away by a `git add -A`) without anything reporting it; the README no longer displayed the image.
- **Fix**: the test checks that every image and every relative link of `README.md`, `README.fr.md` and `docs/**/*.md` points to an existing file; it ignores http(s) links, anchors and code blocks. Tried in both directions: GIF present, the test passes; GIF removed, it fails on both READMEs. No file of `dist\` changes.

### 08/11/2026: `tests/image_zone.py`: Chromium's `file://` message ignored

- **Cause**: opened from disk, the page requests the images by `fetch`, which the browser refuses; the page handles the refusal (`.catch`, no JavaScript error: `pageerror` stays empty), but Chromium itself writes "URL scheme 'file' is not supported" in the console. The test's filter only knew "Failed to load resource" and "blocked by CORS".
- **Fix**: this browser message is added to the filter; a real error of the page (`pageerror`) still makes the test fail. No file of `dist\` changes.

### 08/11/2026: `tests/marque.py`: five marked files, `--version` in French

- **Cause 1**: `--version` follows the system language ("fingerprint" in English) while the test looks for "empreinte"; the test now passes `--lang fr`.
- **Cause 2**: `extraire_batiments.py` and `iar2oar.py` have carried a `MARK` line since batches 1.6.3 and 1.6.4, but the test still treated them as files without a mark; the list of marked files (a constant `MARQUES`) now has five.
- No file of `dist\` changes. The test had not been fixed before this batch (failures already present on `main`).

### 07/11/2026: 1.7.0 release notes aligned with the published description

- **Requested by Klaatou**: `CHANGELOG.md` takes up the description he published on GitHub for 1.7.0 (lists, English then French, "do not unzip over it" warning, the trap of the order of extensions, precaution for `aide.html`). **Done**: the "GitHub release notes" block of 1.7.0 is replaced by this text, as a quotation. **One single difference, reported**: the bullet "`carte.html` is published with the site" / "inclus dans la publication du site" suggested a novelty of 1.7.0, whereas the map has been in the packages since v1.5.0 (`regions.json` and `vignette.jpg` are in the packages of tag `v1.5.0`); what is new is that the packages' `README.txt` files say so. The bullet is reworded in this way here (and in the "Release" bullet of the same entry); the release description on GitHub can be corrected in the same way, in one line per language. `VERSION` goes from `1.7.0` to `1.7.1` (batch counter; not a release).

## 1.7.0 (07/11/2026)

### 07/11/2026: 1.7.0 release: scripts in the repository, icon and logo, animated GIFs, reorganized documentation

- **Release**: 1.7.0 (07/11/2026) gathers batches 1.6.1 to 1.6.19 (described below, in this same section). New since 1.6.0: **(1)** `extraire_batiments.py` and `iar2oar.py` join the repository (French and English messages, `--lang`, English option names with the old French names still accepted, cache in the current folder); **(2)** documentation: `INDEX.md`, the JSON reference as a separate document (`REFERENCE_JSON.md`), procedure to update a package that is already published, "do not unzip over it" warnings; **(3)** "Made with Web_3d" icon at the bottom right of the page and of the map, and the logo as the default tab icon (sample `favicon.ico` replaced); **(4)** animated GIFs on image zones (decoder in the page); **(5)** Status window: "Version: page … · configuration …", and "Copy diagnostics": "Animated GIFs" line; **(6)** packages: image targets without extension (any image), the packages' `README.txt` files say that `carte.html` is published with the site (it has been there since 1.5.0); **(7)** `REFERENCE_OPTIONS.md` regenerated, `--map-names` described. Report from a tester: macOS launcher and region display on macOS Ventura 13.7.8 with Firefox 159.0.1. **Updating a package that is already published**: copy `index.html` and `carte.html` (and `favicon.ico` if you do not have your own), never unzip over it (`SIMPLE_PROCEDURES.md` § 10). `VERSION` goes from `1.6.19` to `1.7.0`; no built file changes at the release (each keeps the number of its last batch).
- **GitHub release notes** (attach: `galerie-photos.zip` and `region-simple.zip`, built by `python fabriquer_paquets.py`), as Klaatou published them on 07/11/2026 (English; the French ones stay in `CHANGELOG.fr.md`), except the bullet on `carte.html`, reworded here because the map has been in the packages since 1.5.0:

  > Already have one of these packages? Do not unzip over your folder: it would overwrite your config, zones and images. See docs/en/SIMPLE_PROCEDURES.md section 10.
  >
  > **Release** 1.7.0. New:
  > - animated GIFs on image zones (the page decodes the GIF itself, animates only the planes you can see, and keeps the first frame when the system asks for less motion);
  > - the Status window shows "Version: page … · configuration …" and "Copy diagnostics" gives an "Animated GIFs" line;
  > - the packages' image zones now use targets without extension, so any image type (jpg, jpeg, png, webp, gif, avif <- note that this is the order in which the image is searched for; if the target exists as both a .jpg and a .gif, the .jpg version will be displayed!) can be dropped in `medias/` under the same number;
  > - the packages' `README.txt` files now explain that `carte.html` is published with the site (it has been in the packages since 1.5.0): only the thumbnail and the name need adapting;
  > - `extraire_batiments.py` (one GLB per object group of an OAR) and `iar2oar.py` (OpenSim inventory archive to a minimal OAR) join the repository, with French and English messages, `--lang`, English option names (the old French names are still accepted);
  > - documentation: `INDEX.md`, the JSON reference as a separate document, the procedure to update a package that is already published, `REFERENCE_OPTIONS.md` regenerated;
  > - a small "Made with Web_3d" icon (the Web_3d logo) at the bottom right of the page and of the map, with a bubble linking to the repository; the logo is also the default tab icon (sample `favicon.ico` replaced).
  >
  > **Upgrading a package**: copy `index.html` and `carte.html` and `aide.html` (be careful if you have customized your aide.html file!) from the new zip (and `favicon.ico` if you have not placed your own); do not unzip over your folder.
  >
  > Reported by a tester: the macOS launcher and the region display work on macOS Ventura 13.7.8 with Firefox 159.0.1. Not tried: Safari, Firefox on Windows, GIF animation outside Chromium.

### 07/11/2026: `--map-names` described; `REFERENCE_OPTIONS.md` regenerated

- **Found** (`tests/doc_options.py`, 2 failures present since before 06/11/2026): (1) "`presence_server` `--map-names`: description missing (fr)"; (2) "`REFERENCE_OPTIONS.md` is up to date" fails. **Cause (read in the code)**: `--map-names` is an old option (1.3.1), kept to warn that it no longer has any effect (the map's nicknames are protected by `--map-names-key`), declared with `help=argparse.SUPPRESS`: hidden from the help, hence without a description; it was the only hidden option of the tools. **Done**: it gets a description in French and in English (key `py.presence.help.map_names`: "old option (1.3.1), no effect (a warning says so): use --map-names-key SECRET"), so it appears in the help and in `REFERENCE_OPTIONS.md`; `src/presence_server.py` changes (the built file gets the number of this batch). **`REFERENCE_OPTIONS.md` regenerated** by `python gen_reference.py` after the build: it had drifted since 30/10/2026 (the mention "(default: %(default)s)" was left in the description of the options `--walk`, `--names`, `--chat`, `--panel`, `--show-spawns`, `--compass`, `--fly`, `--sea`, `--anim`, `--retina`, `--light`, `--zone-cone`; `--map-names-key` was missing). `VERSION` goes from `1.6.18` to `1.6.19`.

### 07/11/2026: documents: icon, GIF, manual appendix, `favicon.ico`, dead reference

- **Requested by Klaatou**: bring the documentation up to date (check done on 07/11/2026: 7 gaps found in `main` 1.6.17). **Done**: (1) manual **§ 7.62** (fr and en): the "Made with Web_3d" icon (place, bubble, link, touch, image `src/credit.png` to replace and then `python build.py`, no setting to remove it, tried and not tried); (2) **animated GIFs**: one sentence in `GUIDE.md` § 2 (fr and en), a paragraph in the `README.txt` of `galerie-photos` (step 4) and a point in `galerie.html` § 1 (fr and en): put the GIF in `medias/` and **change the zone's target** (`"30.jpg"` becomes `"30.gif"`), which was the trap found; (3) **`favicon.ico` when updating a package** (found by Klaatou: Edge's tab kept the old icon): `PROCEDURES_SIMPLES` § 10, the `README.txt` of both packages and manual § 6.9 say that a `favicon.ico` already placed next to the page is still preferred to the embedded icon (so it must be copied back if you do not have your own), and that browsers keep tab icons in cache (general behavior, not tried); (4) **manual appendix** (chapter 13): three lines added (1.4.8 to 1.4.13, 1.5.0 to 1.5.4, 1.6.0 to 1.6.17); (5) `VUE_ENSEMBLE` / `OVERVIEW`: "not tried" completed (GIF on Firefox, Safari and Windows; icon on Windows, Firefox, Safari and a real touch screen); (6) dead reference "manual § 38" in `CREATEURS.md` and `CREATORS.md` replaced by § 6.10. (7) **`tests/paquets.py` red on `main` since commit `74fe691`**: this commit removed the extensions from the image zone targets of both packages (`"1.jpg"` becomes `"1"`, `"aide.jpg"` becomes `"aide"`, `"hop.jpg"` becomes `"hop"`, in `galerie.zones.json` and `region.zones.json`); 6 failures (image `zhop`, file of each zone in `medias`, help zone, for each package). A target without extension makes the page look for `jpg`, `jpeg`, `png`, `webp`, `gif` and then `avif`, so a GIF placed under the same number works without touching the JSON (provided the `.jpg` is removed). **The test follows the page** (a target without extension is resolved like the page does, a target with an extension designates that file: both forms pass); the texts about the GIF cover both cases. **Not done**: `REPRISE.md` (behind `main`, to be delivered at the handover: rule 23); `REFERENCE_OPTIONS.md` and the description of `--map-names` (`doc_options`: 2 failures already present, a small separate batch). No code and no file of `dist\\` changed. `VERSION` goes from `1.6.17` to `1.6.18`.

### 07/11/2026: the Status window shows the page version (`index.html`)

- **Requested by Klaatou**: show the version of `index.html` in the information. **Finding (read in `src/template.html`)**: the **Help** window showed "glb2html {version}" at the end of a line, but this number was the `version` key of `NAME.config.json` (`C.version`), frozen when the region was prepared: it stayed "1.1.1" after `index.html` was replaced, hence the confusion. **Done**: (1) the **Status** window (key I) has a line **"Version: page X · configuration Y"**: X is the number of the page (`__CORE_VERSION__`: that of `index.html` for a shell site, of `glb2html.py` for a standalone page), Y the `version` key of the configuration; it goes into "Copy diagnostics" (which already had the substance of it in its "Version" line); (2) the **Help** window no longer shows a version (key `page.feat`: the term "glb2html {5}" is removed, fr and en); (3) `tests/version_page.py` (new): the two lines, in French and in English, with the version read from `VERSIONS.json`; (4) manual § 7.53, simple procedures § 10 and the `README.txt` of both packages (the sentence about "the number displayed" corrected). `dist\\`: `glb2html.py`, `index.html` and `glb-viewer.html` change. `VERSION` goes from `1.6.16` to `1.6.17`.

### 07/11/2026: "Copy diagnostics": "Animated GIFs" line

- **Found by Klaatou** (his gallery, `index.html` of build 1.6.15 copied): the GIF is displayed but does not animate, and the help window still says "glb2html 1.1.1 (31/10/2026)". **Read in the code**: this number is the `version` key of `NAME.config.json` (`C.version`, `src/template.html`), written when the package was prepared: it says nothing about the version of the page (the diagnostics give both: version of the page, then "configuration version"). Possible causes of the missing animation, in order: an old `index.html` still being served (cache); **the Windows "animation effects" setting turned off, which the browser passes on as `prefers-reduced-motion: reduce` and which, as intended, leaves the GIF on its first frame**; a plane too small on screen (under 8 px). **Done**: a line **"Animated GIFs"** in "Copy diagnostics", when the page has image zones: number of GIFs decoded (`animInfo().planes`), number of frame changes (`ticks`) and "reduced motion requested by the system: yes/no" (keys `core.diag.anim`, fr and en). `imageDiag()` is not modified (`tests/image_diag.py` compares its objects). `tests/gif_anim.py`: two more checks (the test page switches to `fr-FR`). Manual § 5.11 (fr and en). `dist\\`: `glb2html.py`, `index.html` and `glb-viewer.html` change. `VERSION` goes from `1.6.15` to `1.6.16`.

### 07/11/2026: animated GIFs on image zones

- **Requested by Klaatou**: be able to put animated GIFs on image zones. **Finding (read in `src/core.js`, `imagePlane`)**: GIFs were already accepted (`gif` is in `imageExts`) but displayed frozen: the texture comes from a `THREE.TextureLoader`, which sends the image to the graphics card only once, hence the first frame only. **Tests before writing the code** (Chromium on Linux): returning the texture from the `img` tag is useless: `drawImage` of an animated GIF **always gives the first frame**, even when the image is attached to the page and animated on screen (screenshots: it alternates; canvas: it does not change); a GIF made with PIL behaves like the one made by hand. **Done**: (1) **the page decodes the GIF itself**: `gifLzw` (LZW), `decodeGif` (global and local palettes, transparency, disposal modes 0 to 3, interlacing, frame durations; 100 ms if the duration is zero or 10 ms); it keeps the composed frames (64 MB decoded at most, otherwise a still image and a console warning, key `core.image.gifbig`); `gifAnime(u)` reads in full only files that start with `GIF8`, and only `blob:` and `data:` addresses (images read by the page itself, including those of `freshFetch`); (2) a GIF of at least two frames becomes a `CanvasTexture` (without mipmaps) and its plane is entered in `animPlanes`; a one-frame GIF and any other format follow the ordinary path; a plane whose zone was rebuilt is removed; (3) `animTick`, called by the render loop, changes the frame according to the clock **at most 15 times per second**, for the planes visible in the camera's field, **at least 8 pixels wide** on screen, **the 8 largest** at a time, and then requests a render; out of view or too small: no work (a distance criterion was tried first and then dropped: the default camera is 82 m from the center of a 40 m region); **if the system asks for less animation** (`prefers-reduced-motion`), nothing moves; (4) `animInfo()` (planes, ticks) for the tests; (5) `tests/gif_anim.py` (new, test GIF of 1 pixel written by hand) and `tests/gif_decode.py` (new, decoder against PIL); (6) manual § 5.11 (fr and en). **Limits**: an image from another site loaded without CORS stays still (the fetch fails); animated PNG and animated WebP not handled; Firefox, Safari and Windows not tried; the decoder is compared pixel for pixel with PIL by `tests/gif_decode.py` (6 GIFs: noise, interlaced 256-color gradient, large 200 x 150 image, transparency with disposals 1, 2 and 3; test skipped if Node or Pillow is missing) but the tests in the browser only use a 1-pixel GIF; a visible GIF redraws the scene up to 15 times per second (power consumption). `dist\\`: `glb2html.py`, `index.html`, `glb-viewer.html` change (`carte.html` has no image zone). `VERSION` goes from `1.6.14` to `1.6.15`.

### 07/11/2026: the logo becomes the default icon of the pages and the sample `favicon.ico`

- **Requested by Klaatou**: make the logo the favicon. **Done**: (1) **`src/favicon.ico`** (copied by `build.py` into `dist\\`, and into the packages by `fabriquer_paquets.py`) is replaced by an ICO made from the logo, in four sizes 16, 32, 48 and 64 px (14.5 KB; the old one, 8 KB, had a white "3D" on blue); (2) **the default embedded icon** of the four pages (shell and standalone page: `src/template.html`; map: `src/gen_tpl.py`; editor: `src/viewer_tpl.html`) is no longer a "3D" SVG but the same PNG as the corner icon (`src/credit.png`, token `__CREDIT_ICON__`), so **a single image** to replace to change the logo of the pages and of the icon; (3) `tests/icone.py` now expects an embedded PNG (and no token left over); (4) manual § 6.9 (fr and en). The patch checks the SHA-256 fingerprint of the old `favicon.ico` before replacing it and keeps a copy in `_bak\\`. `dist\\`: `glb2html.py`, `index.html`, `carte.html` and `glb-viewer.html` change, plus `favicon.ico`. The zips only change at the next release; a site that has already placed its `favicon.ico` next to its pages keeps its own. `VERSION` goes from `1.6.13` to `1.6.14`.

### 07/11/2026: "Made with Web_3d" icon on the page and on the map

- **Requested by Klaatou**: an icon that leads to the repository, at the very bottom right, under the chat, square and no taller than the buttons, with a bubble and the link to the repository; visible in the global view as well as when walking, and on the map; with no way to turn it off for now. **Done**: `#credit` (32 px, the height of the page's buttons: 33 px) in `src/template.html` (hence the `index.html` shell and the standalone page) and in the map template (`src/gen_tpl.py`); link to `https://github.com/Klaatou/Web_3d` in a new tab (`noopener`); bubble on hover and on keyboard focus (key `common.credit.tip`, French and English); **the chat moves up by 38 px** (`bottom: 50px`) to pass above it; **on a touch screen** the button column `#tcol` moves up by 38 px and the icon hides when the chat input takes the bottom; the footer text of the map (batch 1.6.10) stays. **The image is Klaatou's logo** (transparent cube, "3D" and walker; square 64 px PNG taken from his file, transparent corners): `src/credit.png`, written by the patch, injected at build time into the page and the map (`build.py`, token `__CREDIT_ICON__`); **to change it, replace this file and run `python build.py` again**. **Not in** `glb-viewer.html` (the editor). `tests/credit.py` (new): link, image loaded, no `__CREDIT_ICON__` token left in `dist\`, shape, place, bubble (fr and en), chat above, walking, touch, map. `PROCEDURES_SIMPLES` / `SIMPLE_PROCEDURES` § 10: `aide.html` to be copied back only if it has not been modified. **To remind Klaatou of in a while, if he does not bring it up**: an option to turn the icon off (configuration key `credit`, like the page's other settings). `dist\`: `glb2html.py`, `index.html`, `carte.html` and `glb-viewer.html` change; `VERSION` goes from `1.6.12` to `1.6.13`.

### 07/11/2026: warning when downloading the packages: do not unzip over a package already in place

- **Requested by Klaatou**: warn, at download time, not to unzip a zip when you already have the package. **Finding**: the update procedure (§ 10) already said to unzip separately, but nothing was visible **before** the download, and the zip contains the configuration, the zones and the 30 sample images (or the model), which would overwrite the creator's own. **Done**: a bold paragraph in `README.md` and `README.fr.md` (above "In both: unzip"); a parenthesis at the head of "To start" in the `README.txt` of `galerie-photos` and `region-simple`; a sentence at the head of `PROCEDURES_SIMPLES` / `SIMPLE_PROCEDURES` § 10; and in `PROCEDURES.md` § 12 (publishing a release): the warning to place at the head of the notes of the GitHub release page. **Not done**: the release page itself (to be filled in at the next release, by Klaatou); the packages' HTML pages. The zips only change at the next release. `VERSION` goes from `1.6.11` to `1.6.12`.

### 07/11/2026: `tests/paquets.py`: more complete diagnostics of the gallery click

- **Found by Klaatou** (his machine, after batch 1.6.10): the failure "galerie-photos: a click on the counter's help panel opens aide.html" comes back, with `{'ouvert': [], 'clic': [625, 288], 'fenetre': [1200, 700, 1], 'about_ouvert': False, 'en_promenade': False}`. **Measured here**: the click lands at the **same point** (625, 288), in the same window, and does open `aide.html`: the geometry is therefore not at fault, and neither is batch 1.6.10 (texts, map footer). **Cause unknown**: the click reaches the page but does not trigger the zone on Klaatou's machine. **Added**: on failure, the test also writes the number of zones known to the page, the zone found under the clicked point (`zonePickAt`) and the loading state of the zones' images. Reading: `zones: 0` = the zones were not loaded; `zone_sous_clic: null` with zones = the panel is not under the point; zone found but click without effect = something hides the panel or the click is refused. `VERSION` goes from `1.6.10` to `1.6.11`.

### 07/11/2026: mention of Web_3d in `carte.html` and in `aide.html`; updating a package that is already published

- **Requested by Klaatou**: an "ad" for the repository, and the procedure to update a package ("copy only the html files"). **Done**: (1) **`carte.html`**: the footer now carries, after the existing text, the link "Made with Web_3d" ("Réalisé avec Web_3d") to `https://github.com/Klaatou/Web_3d` (key `map.credit`, French and English; the existing text goes into a `<span id="footText">`); **the same page is also used for the maps made by `glb2html.py --map`**, which therefore receive the mention; (2) **`aide.html`** of both packages: a paragraph in French and in English "Made with Web_3d (free software, MIT license)", under the comment where the creator writes their introduction, so removable by them; (3) **update procedure**: `docs/fr/PROCEDURES_SIMPLES.md` and `docs/en/SIMPLE_PROCEDURES.md` § 10, and a block in the `README.txt` of both packages (French and English): copy only `index.html` and `carte.html`, do not overwrite the config, the zones, the model, `medias\`, `regions.json`, `vignette.jpg` or an adapted `aide.html`; `lib\` only if the `three-…` folder changes; the `version` key of the config gives the number displayed; a package from before 1.5.0 has no `regions.json` or `vignette.jpg`, which the map needs. **Tried** (Chromium on Linux): the current `index.html` opens without error a package whose config, zones and `default.json` are those of 1.2.3; the map without `regions.json` shows "Impossible de lire regions.json" ("Cannot read regions.json"). **Not tried**: Windows, the other browsers, an update from other versions. `tests/paquets.py` checks the mention in the map and in `aide.html`; `INDEX.md` and `HISTORIQUE`/`HISTORY` updated. **Build**: `dist/carte.html` and `VERSIONS.json` change (the other files of `dist\` keep their number). The zips only change at the next release. `VERSION` goes from `1.6.9` to `1.6.10`.

### 07/11/2026: `tests/paquets.py`: waiting for the arrival point of `region-simple`, and what is needed to understand the gallery click failure

- **Found by Klaatou** (his machine): `tests/paquets.py` gives 2 failures. **(1) `region-simple`: "the walking arrival point is outside the sample house", `[22.5, 16.7, 18.5]`**: failure **already present on `main`** (same result on a clone of `main` before this batch). **Cause (read in the code)**: the test required `|x| < 0.01` and `|z| < 0.01` (arrival at (0, 0)), but the package has no arrival zone: walking starts at the config's target point (`target` = `[22.5, 15.0, 18.5]` in `region.config.json`, the house having been moved), and the eyes are at 1.7 m: `[22.5, 16.7, 18.5]` is therefore the right result, outside the house. **Fixed**: the test reads `target` in the config of the built package and compares. **(2) `galerie-photos`: "a click on the counter's help panel opens aide.html", `[]`**: **not reproduced here** (passes at every try on Linux and Chromium); no `window.open` was triggered by the click. **No fix**: cause unknown (rendering, window or timing of Klaatou's machine; Windows and graphics card not tested here). **Added**: on failure, the test writes the position of the click, the window size, the state of the "About" panel and the walking mode, so that a single run is enough to understand. `VERSION` goes from `1.6.8` to `1.6.9`.

### 07/11/2026: packages' `README.txt`: the map is published with the site

- **Requested by Klaatou** (a creator hosted on his server found `carte.html` at the address of their Netlify site): say in the packages that `/carte.html` is available once the site is published and that only the thumbnail needs adapting. **Finding**: the mention existed for the local address (`README.txt`) and in § 8 of `galerie.html` / § 10 of `readme.html`, not for the published site. **Done**: a sentence added under the `site/` line of the "Folders" section of the `README.txt` of `galerie-photos` and `region-simple` (French and English): address `https://YOUR-SITE/carte.html`, thumbnail `site/vignette.jpg` and name in `site/regions.json`. The packages' HTML pages have not changed. **Not modified**: the page's help (`aide.html`, key H) does not mention the map, and the M key only appears if the config has a map (`map` or `mapUrl`): Klaatou's decision, do not touch it. The zips only change at the next release. `VERSION` goes from `1.6.7` to `1.6.8`.

### 07/11/2026: documentation index and JSON reference separated from the manual

- **Requested by Klaatou**: the documentation is scattered; make an index and move chapter 11 of the manual into a separate document, like `REFERENCE_OPTIONS.md`. **Done**: `docs/fr/INDEX.md` and `docs/en/INDEX.md` (by intent, then by reference, then project status); `docs/fr/REFERENCE_JSON.md` and `docs/en/REFERENCE_JSON.md` (chapter 11 of the manual, identical text, headings raised by one level; **the numbering 11.1 to 11.12 is kept**, so the references "§ 11.x" remain valid); chapter 11 of the manual is now only a pointer; in the manual, the 10 references "§ 11.x" and the line of § 1.3 name the file; references updated in `README.md`, `README.fr.md`, `PROCEDURES.md` (fr and en), `docs/samples/README*.md` (including the old reference "§ 27") and `VUE_ENSEMBLE` / `OVERVIEW` § 4. `verif_trad.py` knows the English names of all the documents. **Two damaged sentences of the original chapter 11 are fixed** in `REFERENCE_JSON.md` (§ 11.1, the name of the sample region, which gave `nomregionregion.config.json` in French and `region.config.sampleregion.json` in English: now "Atoll", as in `docs/samples/`). `tests/samples.py` also checks both `REFERENCE_JSON.md` files (the table 11.11 of old names stays excluded). **Not modified**: the packages' pages (`paquets/`, "manual § 11.6") and `CLOUD_RAPPORT.md` (history): their reference remains correct thanks to chapter 11 of the manual, which points to the new file; the zips only change at the next release. **To update at the next handover**: `REPRISE.md` (the decision "JSON files (v43): every added or changed field is carried over into manual § 11" becomes: into `REFERENCE_JSON.md` and into `docs/samples/`). `VERSION` goes from `1.6.6` to `1.6.7`.

### 07/11/2026: report from a tester on macOS ("not tried" texts corrected)

- **Report received** (discussion thread of the demo): a tester (NightshadeCeres, named since 08/11/2026 with his agreement) tried the packages on **macOS Ventura 13.7.8 with Firefox 159.0.1**: the zips open, the `.command` launcher works after "right click, Open" (macOS warning, then Open), the region is displayed (the little world of `region-simple`). He had first tried dragging `index.html` into the browser, which does not work; he found the README. Only the display is reported. **Fixed**: the sentence "the macOS launchers have not yet been tried on a Mac" in `paquets/region-simple/README.txt`, `paquets/region-simple/site/readme.html`, `paquets/galerie-photos/README.txt` and `paquets/galerie-photos/site/galerie.html` (French and English; for the gallery: same launcher, **extrapolated, not tried separately**); "Not tried: Firefox and Safari" in `docs/fr/VUE_ENSEMBLE.md`, `docs/en/OVERVIEW.md`, `docs/fr/MANUEL.md` and `docs/en/MANUAL.md` (Safari and Firefox on Windows and Linux remain not tried); a sentence in `README.md` and `README.fr.md`; `HISTORIQUE` and `HISTORY`. The tester is not named (agreement to be asked for first). **The zips on the releases page only change at the next release** (Klaatou's decision). OAR to GLB conversion on macOS remains not planned (`GUIDE` § 1.2). No code and no file of `dist\` modified. `VERSION` goes from `1.6.5` to `1.6.6`.

### 07/11/2026: documents of `extraire_batiments.py` and `iar2oar.py`

- **Requested by Klaatou**: update the documents after the two scripts entered the repository (batches 1.6.3 and 1.6.4). **Done**: `docs/fr/PROCEDURES_SIMPLES.md` and `docs/en/SIMPLE_PROCEDURES.md` § 6 rewritten (scripts in `web_3d\dist`, run from the working folder, English option names, `--tools`, cache in the current folder, no more "outside the repository" mention); manual: lines of the table in § 2, new § 3.7 (`extraire_batiments.py`) and § 3.8 (`iar2oar.py`), § 7.50 (tools concerned by `--lang`), table of old names in § 11.11 (French names of the two tools); French and English README: two lines in the tools table; `HISTORIQUE` and `HISTORY`: lines for batches 1.6.1 to 1.6.5. **The name "bâtiment" (building) is explained** (procedures § 6, manual § 3.7): it comes from the buildings of a big OAR of houses, but the tool extracts any group of objects. No code and no file of `dist\` modified. `VERSION` goes from `1.6.4` to `1.6.5`.

### 06/11/2026: `iar2oar.py` enters the repository (`tools\`, `dist\`)

- **Requested by Klaatou**: bring into the repository the script that turns an IAR into a minimal OAR (second batch after `extraire_batiments.py`), without changing what it does. **Done**: `tools/iar2oar.py` (behavior unchanged); messages and help in `src/i18n` (keys `py.iar2oar.*`, French and English); options **`--lang`** and `--version`; **options switched to English** (`--list`, `--filter`, `--no-nested`, `--margin`, `--output`) with the old French names still accepted (`--liste`, `--filtre`, `--sans-imbriques`, `--marge`, `--sortie`, also in the form `--marge=4`); they are added to `ANCIENS` of `tests/samples.py`. The script imports nothing from `oar2glb.py` or `glb2tiles.py`. **Build**: the file is in `FICHIERS_VERSION` (own version in `VERSIONS.json`). **Tests**: `tests/iar2oar.py` (new), `tests/tools_lang.py` and `tests/textes_outils.py` (the script is added to the lists). `gen_reference.py` and `REFERENCE_OPTIONS.md` know the new tool. `VERSION` goes from `1.6.3` to `1.6.4`. **Documents**: `PROCEDURES_SIMPLES` § 6 (commands in English, remove "outside the repository"), manual (table of old names § 27.11, section of the tool), README, `HISTORIQUE`/`HISTORY` remain to be updated when Klaatou validates (rule 16).

### 06/11/2026: `extraire_batiments.py` enters the repository (`tools\`, `dist\`)

- **Requested by Klaatou**: bring into the repository the script that extracts object groups from an OAR (until then outside the repository), without changing what it does. **Done**: `tools/extraire_batiments.py` (behavior and options unchanged); all its messages and its help go through `src/i18n` (keys `py.extraire.*`, French and English); option **`--lang`**; option **`--tools FOLDER`** (and variable `WEB3D_TOOLS`) to say where `glb2tiles.py` and `oar2glb.py` are (default: next to the script; the old search in `web_3d\dist` and `dist` is removed), like `--convoar` for `oar2glb.py`; `--version`; the help works even without the two neighboring tools. **Cache**: the `extraire_batiments.cache` folder is created in the **current folder** (where the command is run), no longer next to the script (`dist\` is tracked by git); it moves with the command; the old cache is not read again, the first run rebuilds it; `.gitignore` ignores `extraire_batiments.cache/`. **Build**: the file is in `FICHIERS_VERSION` (own version in `VERSIONS.json`). **Tests**: `tests/extraire_batiments.py` (new), `tests/tools_lang.py` and `tests/textes_outils.py` (the script is added to the lists). `gen_reference.py` and `REFERENCE_OPTIONS.md` know the new tool. The script's French option names (`--filtre`, `--groupe`, `--boite`...) are kept as they are; `VERSION` goes from `1.6.2` to `1.6.3`. **Documents**: `PROCEDURES_SIMPLES` § 6 and the manual remain to be updated when Klaatou validates (rule 16), with the explanation of the name "bâtiment" (the name comes from the buildings of a big OAR, the tool extracts any group of objects).

### 06/11/2026: `iar2oar.py` (outside the repository) and procedure to extract objects from an IAR

- **Requested by Klaatou**: handle IARs (OpenSim inventory archives) and extract objects from them as GLBs, like the buildings of an OAR. **Added outside the repository**: `iar2oar.py` (next to `oar2glb.py`, importing nothing from them) turns an IAR into a minimal OAR: one grid cell per object (or per combined object), combined objects split into groups, the contents of boxes (`TaskInventory`) added on 3 levels, final null byte of the XML files removed, only meshes, textures and materials copied. Tried on an IAR of 34 items (25 with an object asset, 275 object assets in total, 1,182 groups, 10,562 parts): the resulting OAR is read without error by `oar_scan` of `oar2glb.py`, then converted to GLB with convoar and opened in Blender by Klaatou. Not supported: attachments and clothing; no terrain. The convoar texture errors in this test come from the IAR (3-byte textures, missing material maps). **Documents**: `docs/fr/PROCEDURES_SIMPLES.md` and `docs/en/SIMPLE_PROCEDURES.md` § 6 (IAR subsection), `REPRISE.md`. `VERSION` goes from `1.6.1` to `1.6.2`.

### 05/11/2026: no more personal region names or nicknames in the examples and tests

- **Found by Klaatou**: an old sample region name and a personal nickname appeared in documents, tests and examples of the public repository. They are replaced by neutral names (`Atoll`, `klaat`): `docs/samples/README.md` and `README.fr.md`, `src/i18n` (example of the `-o` option, hence `REFERENCE_OPTIONS.md` and `dist\`), `tests/modulaire.py`, `tests/v37_region.py`, `tests/samples.py`, `tests/v51.py`, `CHANGELOG.md`. `VERSION` goes from `1.6.0` to `1.6.1`.
## 1.6.0 (05/11/2026)

### 05/11/2026: 1.6.0 release: `yaw` in the status, "Link to OpenSim" panel in the packages, documents up to date

- **Release**: 1.6.0 (05/11/2026) gathers the batches noted "Unreleased" since 1.5.1 (described below: 1.5.2, 1.5.3, 1.5.4) and adds: **(1)** the "Avatar position" line of Information / Status ends with the `yaw`, in radians, 2 decimals (`template.html`, `fr.json`, `en.json`: `page.state.pos.avatar`), the same value as the `yaw` of "Copy my position" and of the zones; in the global view, the "Target position" line has no `yaw`; **(2)** both packages have the image zone `zhop` added by Klaatou (commit `b3b35b6`); the batch replaces the copy of `aide.jpg` with a real image `medias/hop.jpg` "Lien vers OpenSim" ("Link to OpenSim", 1200 x 600) and adds a notice (README, `readme.html` § 8, `galerie.html` § 4): note the position on foot ("Copy my position", `xyz` format), `y` = ground + height of the board's center, `yaw` read in Information / Status, name of the image, `hop://` address; **(3)** the documents that were behind: manual (§ 5.7.1, § 5.11, § 7.38, table of zones), `PROCEDURES` § 13 (registering the `hop://` protocol on Windows), `HISTORIQUE` / `HISTORY`. `VERSION` goes from `1.5.4` to `1.6.0` (the minor number goes up: features were added). New test: `tests/yaw_etat.py`; `tests/paquets.py` checks the `zhop` zone, its image and the notices, and closes the "About the region" panel (files `galerie.about.fr.txt` and `galerie.about.en.txt` of the gallery package, opened on entry) before clicking the counter's help: without this the click landed on this panel.
- **GitHub release notes** (attach: `galerie-photos.zip` and `region-simple.zip`, built by `python fabriquer_paquets.py`): **Release** 1.6.0. New: the "Position avatar" line of Information / Status now ends with the `yaw` (radians, 2 decimals), the value to copy into a zone; both packages ship an example "Lien vers OpenSim" panel (`hop://` link) with step-by-step instructions to change its image, position and address; zones accept `hop://` links, and signs, pictures and captions read correctly from both sides (1.5.2 to 1.5.4). Documents updated, including how a visitor registers the `hop://` protocol on Windows.

### 05/11/2026: panels, picture boards and captions readable from both sides; label of `hop://` links

- **Found by Klaatou**: the inscription of a panel is backwards when seen from behind; picture boards (image zones) and their captions are also placed right in the middle of a place; the panel of a `hop://` link carried the subtitle "Web link". **Cause**: a panel, a picture board and a caption were a single `DoubleSide` plane (`core.js`), whose texture is seen mirrored from the other side; the subtitle came from `core.kind.url`. **Fix**: each is made of two back-to-back planes, each visible from its own side only (`FrontSide`), the second turned by 180 degrees (`backOf`), same image, same material. The back plane follows the front plane: click and hover (panel, board with a link), missing image, caption replaced by a text file, selection in the editor. No one-sided or two-sided option (the mirror is never wanted; against a wall the back is hidden). A `url` zone whose target is `hop:` shows the subtitle "Monde virtuel" ("Virtual world", `core.kind.hop`, French and English). `VERSION`: `1.5.4`. Changed in `dist\`: `glb2html.py`, `index.html`, `carte.html`, `glb-viewer.html` (the interface texts are in all four).
- **Tests**: `tests/image_cache.py` and `tests/image_cache_vieux.py` ignore the back planes (mark `userData.back`) when they look for the displayed image; `tests/double_face.py` (new: two back-to-back planes for panels, board and caption; click in front and behind; `hop://` subtitle; on 1.5.3, 5 checks fail). **Not tested here**: the text being the right way round to the eye (only the structure, the normals and the clicks are measured), Windows, Edge.
- **Fixed**: panels, picture boards and their captions are readable from both sides: each is now two back-to-back planes, each visible from its own side only (`FrontSide`), so text and image are never mirrored from behind; the back plane follows the front one (click, hover, missing image, caption file, editor selection). No one-sided option (a mirror is never wanted). A url zone whose target is `hop:` shows the subtitle "Virtual world" instead of "Web link". New test `tests/double_face.py` (fails on 1.5.3). Not tested here: reading the text by eye, Windows, Edge.

### 05/11/2026: url and image zones: `hop://` links allowed

- **Found by Klaatou**: a link zone whose target is `hop://grid.virtual-worlds.zone:8002` did not open (the viewer, which only previews, just showed "[preview] Link … triggered"). **Cause**: `okUrl` (`template.html`) only accepted `http:` and `https:`; the page answered "Lien invalide" ("Invalid link"). **Fix**: `okLink`, for **url** and **image** zones (key `link`) only, also accepts `hop:`; a `hop:` link opens by direct navigation (`window.open(..., '_self')`), without an empty tab, the browser offering to open the OpenSim or SL viewer. Unchanged: portals, Home Assistant commands and the map stay on `http`/`https`; `ftp:`, `javascript:` and the rest stay refused. `VERSION`: `1.5.3`. Changed in `dist\`: `glb2html.py`, `index.html`, `glb-viewer.html`.
- **Tests**: `tests/lien_image.py` extended (board and url zone with a `hop://` link: opened, without "Lien invalide"; `ftp://` zone refused; portal to `hop://` refused; on 1.5.2, 3 checks fail). **Not tested here**: the real opening by an OpenSim or SL viewer, Windows, Edge.
- **Fixed**: `hop://` links are now accepted in url and image zones (they were refused as "Lien invalide"; only http and https were allowed). They open by direct navigation so the browser offers to launch the viewer. Portals, Home Assistant commands and the map still accept http and https only. Test `tests/lien_image.py` extended (fails on 1.5.2). Not tested here: opening in a real viewer, Windows, Edge.

### 04/11/2026: chat: a text selection in the log is no longer erased

- **Found by Klaatou**: impossible to copy a chat message, the selection was lost. **Cause**: the page rebuilt the whole log every second (`setInterval(render, 1000)`, `template.html`), which erases a text selection. **Fix**: the log is touched only if the displayed list changes, and one more message is appended at the end without rebuilding everything; in the viewer, one more message is appended to the log without rewriting it. Nothing changes on the network side: `render()` does not talk to the presence server. `VERSION`: `1.5.2`. Changed in `dist\`: `glb2html.py`, `index.html`, `glb-viewer.html`.
- **Tests**: `tests/chat_selection.py` (new: triple click on a message, the selection holds for 3.5 s and when a message arrives; more than 6 messages: correct rebuild; on 1.5.1, 2 checks fail). **Not tested here**: Windows, Edge.
- **Fixed**: a text selection in the chat log is no longer erased. The page rebuilt the whole log every second (`setInterval(render, 1000)`), which cleared any selection; the log is now touched only when the displayed list changes, and a new message is appended without rebuilding. In the viewer, a new message is appended to the log without rewriting it. Nothing changes on the network side. New test `tests/chat_selection.py` (fails on 1.5.1). Not tested here: Windows, Edge.
## 1.5.1 (04/11/2026)

### 04/11/2026: 1.5.1 release: the version shown by the packages follows the release

- **GitHub release notes** (to attach: `galerie-photos.zip` and `region-simple.zip`, built by `python fabriquer_paquets.py`): the bullet below (the French one stays in `CHANGELOG.fr.md`).
- **Release** 1.5.1 fixes a detail of 1.5.0: the Help window of the two packages showed an old version (1.1.0 or 1.1.1), the one written in the config when the package was prepared. `fabriquer_paquets.py` now writes the release version into the `version` key of each package's config at every build: nothing left to update by hand. Test: `tests/paquets.py` (134 checks). `VERSION` goes from `1.5.0` to `1.5.1`. No file of `dist\` changes; the manual (§ 11.3) says so.

## 1.5.0 (04/11/2026)

### 04/11/2026: 1.5.0 release: compressed tiles, "About this region", package maps, new documentation

- **GitHub release notes** (to attach: `galerie-photos.zip` and `region-simple.zip`, built by `python fabriquer_paquets.py`): the two bullets below (the French ones stay in `CHANGELOG.fr.md`).
- **Release** 1.5.0 gathers the batches noted "Unreleased" since 1.4.0 (described below). `VERSION` goes from `1.4.13` to `1.5.0` (the minor number goes up: features were added).
- **What is new in 1.5.0**: tiled regions: the name of the tile under the avatar is shown in the state window (one element per line), with the weight actually received; `glb2tiles.py --compress` compresses the tiles with `gltfpack` (about half the size); page: "About this region" panel (file `NOM.about.<language>.txt`, clickable links, `?` key, checkbox in Settings), "Visitors' help" link in the Help window, "Loading…" message in a clearly visible frame, adjustable tab title (`title` key, `--title`); world map: `--scan-sites --prune-missing` removes the cards that cannot be found; each package (`galerie-photos.zip`, `region-simple.zip`) has its own map with its thumbnail; each Python tool now embeds only its own texts; documentation rebuilt: manual by theme in 13 chapters, "Creating and managing a region" guide, the host's procedures, development. OAR to GLB conversion remains Windows-only.

### 04/11/2026: version 1.4.13: a map in every package

- **New** (Klaatou's request: a creator's presentation page): `galerie-photos.zip` and `region-simple.zip` now contain their own map, even with a single region: `site/carte.html` (copied from `dist\` at build time by `fabriquer_paquets.py`), `site/regions.json` (the region's card: displayed name, place, relative address, thumbnail, presence off) and `site/vignette.jpg` (320 x 320 JPEG, 8 KB and 3 KB, cropped from Klaatou's captures). The thumbnail's name does not depend on the region's name: renaming does not touch it.
- **Renaming**: `renommer-galerie` and `renommer-region` (`.sh` and `.ps1`, hence `.bat` and `.command`) also update the card in `regions.json` (`id`, `room`, `region=` of the address); back to the original name included.
- **Documents**: `README.txt` of both packages (map address, thumbnail), "Appearing on a world map" sections and the renaming table of `readme.html` and `galerie.html` (FR and EN), guide § 1.1, manual ch. 9. **Fixed**: four "manual § 27.6" references left on the old plan in the package documents (now § 11.6).
- **Test**: `tests/paquets.py` (132 checks): files, card, thumbnail (320 x 320 JPEG, under 60 KB), documents, `carte.html` in Chromium (one tile, address to the region, thumbnail loaded), renaming of the card and back. On 1.4.12 it fails 15 times. **Not tested here**: the `.ps1` and `.bat` scripts (no PowerShell), the macOS launchers.

### 04/11/2026: version 1.4.12: the "About" panel no longer greys out the page

- **Fixed** (Klaatou's request: the very dark background looked like an error): the "About this region" panel no longer darkens the page; its 80% black background is removed and the page stays visible and usable behind the frame, like the "Loading…" message. Only the frame receives the mouse (`pointer-events`), `aria-modal` becomes `false` (the panel is no longer blocking), and a click beside it no longer closes it: it closes with Esc, the "Close" button, "Don't show again" or the `?` key. Test: `tests/apropos_liens.py` extended (transparent background, page reachable behind, frame clickable); on 1.4.11 it fails.

### 03/11/2026: version 1.4.11: manual by theme; visitors' help in the Help window

- **Rebuilt manual** (cloud session, branch `claude/manuel`, reviewed and completed): `docs/fr/MANUEL.md` and `docs/en/MANUAL.md` now follow the project from end to end in **13 chapters** (getting started, the tools, converting an OAR, measuring and splitting, placing the zones, making the page, the page on the visitor's side, tiled regions, the world map, the presence server, the JSON files reference, troubleshooting, the annex "what each version brought") instead of a pile of "What's new in vNN". No fact removed: 228 titles relocated, the only deletions are the "Tests of vNN" lists; old-plan to new-plan correspondence table in `CLOUD_RAPPORT.md`. References updated in `GUIDE`, `PROCEDURES`, `CREATEURS` / `CREATORS`, `README`, `docs/samples/README*`, `REPRISE.md`; `HISTORIQUE` / `HISTORY` keep their period references, with a note.
- **New** (Klaatou's request): the "Visitors' help" link (`aide.html` next to the shell) is also in the Help window (H key), **even without an "About" file**; the existence of `aide.html` is tested once (`AIDE` in `template.html`) for the Help window and the "About" panel.
- **Fixed**: `tests/samples.py` looked for the old § 27.11 (now § 11.11); two code comments quoted the old manual plan (`gen_tpl.py`, `oar2glb.py`); § 2.1 of the manual said every tool embeds all the texts (false since 1.4.10).
- **Test**: `tests/apropos_liens.py` extended (three sites: about and help, about only, help only); on 1.4.10 it fails 3 times.

### 03/11/2026: version 1.4.10: tool-specific texts; visible "Loading…"

- **Cleanup** (Klaatou's request): `build.py` copied into **every** Python tool the table of **all** the texts of the Python tools; each tool now embeds only its own (`py.<tool>.*`), the common texts (`py.common.*`) and `_name`. Effects: smaller files (`glb2html.py` 670 KB -> 580 KB), and a tool no longer changes number when a text is added to another. The families were already separate (no tool uses another's texts; `glb2tiles.py` loads `glb-stats.py`, which keeps its own texts). Test `tests/textes_outils.py` (new: no foreign text, every cited text present in French and English, `--help` in both languages, `glb2tiles.py --analyse`; it fails on 1.4.9).
- **Fixed** (Klaatou's report): "Loading…" was a bare text, hard to read over the overview of a big region; it is now in a white frame with a black border, centred, in bold (`#msg`, `template.html`). Same frame for the loading error messages.

### 03/11/2026: version 1.4.9: about (links, visitors' help); documents reorganized

- **New** (Klaatou's requests): in the "About this region" panel, the `http(s)://` addresses of the text become links (underlined, new tab, `rel="noopener noreferrer"`, trailing punctuation left to the text; text set as nodes, never interpreted HTML); "Visitors' help" button when `aide.html` is next to the shell (`HEAD` check, over http(s) only); the help button is called "About this region (? key)" (`page.about.btnkey`, `page.about.helpbtn`). Test `tests/apropos_liens.py` (new; it fails on 1.4.8).
- **Documents**: **new** `docs/fr/GUIDE.md` and `docs/en/GUIDE.md` (creating and managing a region, for everyone: packages, OAR to GLB on Windows only, tiles, viewer, standalone page or with a shell, useful options, publishing, presence, role of the tools) and `docs/fr/DEVELOPPEMENT.md` / `docs/en/DEVELOPMENT.md` (deliveries, build, tests, publishing a version); `PROCEDURES_SIMPLES.md` / `SIMPLE_PROCEDURES.md` become the host's procedures (bringing a published region up to date, title, renaming, map, compression, extracting buildings, demo, server on the VM, hosting a creator, with no conversion done by the host); pointers in `PROCEDURES.md`, the `README` files and manual § 38.2.

### 03/11/2026: version 1.4.8: documents (manual, simple procedures, note to creators)

- **Documents** (French and English, `verif_trad.py` with no error): manual § 38 (tiles line, "About this region", `--compress`, `title` key, `--prune-missing`, tried and not tried) and the `title` row of the § 27.3 table; **new** `docs/fr/PROCEDURES_SIMPLES.md` and `docs/en/SIMPLE_PROCEDURES.md` (everyday tasks, one command per block, including hosting a creator on the presence server: message to send and steps to take); creators note (`title`, `about` file); `PROCEDURES.md` (pointer to the short version); `HISTORIQUE` / `HISTORY` (batches 1.4.2 to 1.4.8). No code and no `dist\` modified.

### 03/11/2026: version 1.4.7: displayed title distinct from the room; `--prune-missing`

- **New** (Klaatou's request: "Houses" in the tab, `houses` in the files): optional **`title`** key in `NAME.config.json` (60 characters at most). The tab title becomes `title`, otherwise `room` as before (`gen_tpl.py`, shell: `document.title = C.title || C.room`). `--title` of `glb2html.py`, until now **ignored** in shell and tiles modes (with a warning), writes it to the config; `--update` keeps it when not given again. Without `--title`, no key is added: existing configs do not change. The presence room (`room`) and the file names do not change.
- **New**: `--scan-sites` gives a **new** card the config's `title` as its name (otherwise the file name); existing cards keep their name.
- **New**: `--prune-missing` (with `--scan-sites`) removes from `regions.json` the **local** cards whose region is not found in the folder; external cards are kept; `--dry-run` shows the list without writing. Without this option nothing is deleted, as before. The only new flag of the batch.
- **Removed**: the "`--title` is ignored" warning (text `py.glb2html.avertissement_title_est_ignore_en_mode`, no longer needed).
- **Test**: `tests/titre.py` (new); documents behind: manual § 27 (`title` key), manual (`--prune-missing`), `PROCEDURES`, `HISTORIQUE`/`HISTORY`.

### 03/11/2026: version 1.4.6: `glb2tiles.py --compress`

- **New** (Klaatou's request: the "Houses" region goes from 1,434 MB to about 650 MB, which allows publishing it on GitHub Pages; limit of about 1 GB per site, to be re-checked): the `--compress` option of `glb2tiles.py` compresses, **after** the tiles and the overview are written (also with `--overview-only`), every `.glb` with `gltfpack` and the options `-cc -kn -ke -km -vpf -vtf` (never `-tc`: KTX2 is not read by the viewer; without `-vtf`, `gltfpack` reports texture-coordinate errors). Klaatou's measurements (03/11/2026): 33.2 MB tile → 15.9 MB; overview 23 MB → 4.43 MB.
- **Safeguards**: `gltfpack` is looked up in the `PATH`, otherwise run through `npx -y gltfpack` (Node required); when absent the tool stops **before writing anything** with a clear message and a non-zero code. An already compressed file (`COMPRESSIONS`) is **skipped with a message**, never recompressed; running the tool again on an already compressed folder therefore leaves the tiles unchanged. Written to a temporary file then replaced atomically; an error on one file does not stop the others, leaves the original untouched and gives exit code 3. `gltfpack` warnings are counted and shown.
- **Unchanged**: `X.tiles.json` is not modified (its `bytes` stay those from before compression: the loading budget stays cautious, and the displayed weight follows the received files since 1.4.4); no field added. Named nodes, `extras` and materials are kept (`-kn -ke -km`).
- **Test**: `tests/compress.py` (new: gltfpack absent; `EXT_meshopt_compression` extension, names, extras, materials, triangles, identical index, re-run with no effect, file in error, the page loading the compressed region with the "Tile(s) under the avatar" line). Without `gltfpack` available, the compression part is skipped with a message.

### 03/11/2026: version 1.4.5: "About this region" panel

- **New** (Klaatou's idea): an introduction text for the region, shown on entry. Files next to `NOM.config.json`: `NOM.about.fr.txt`, `NOM.about.en.txt` (one per language; the page tries the current language) then `NOM.about.txt` (fallback). A static site cannot list a folder, so the page tries these addresses with `fetch` (a 404 is silent; an HTML answer from a server that returns its home page instead of a 404 is ignored). **No file: no panel, no button, no checkbox.** First line = title, the rest = paragraphs; plain text only (`textContent`, `white-space: pre-wrap`: a tag written in the text stays visible as is, addresses are not clickable); beyond 20,000 characters the text is cut with "…" (estimate, to be tuned).
- **Panel**: `role="dialog"`, `aria-modal`, opened on entry once loading is over (region with or without tiles); closed by **Esc**, by "Close (Esc)" or by the backdrop; "Don't show again" closes it and remembers the choice **per region** (`localStorage`, key `web3d.about.hide.NOM`, everything in `try/catch`: without storage the page works and the panel shows at every entry). "Show the about panel on entry" checkbox in Settings (checked by default; unchecking it equals "Don't show again").
- **`?` key**: recognised by the printed character (`e.key === '?'`: Shift + comma on AZERTY, Shift + slash on QWERTY), toggles the panel; not with Ctrl, Meta or Alt, not repeated, not in an input field (`INPUT`, `TEXTAREA`, `SELECT`: the chat can type "?"). **F1 rejected** (Edge intercepts it). The key is listed in the help (`page.help.about`), which also gets an "About this region" button (only when an about exists). `H` stays the key help.
- **How**: the shell's `mk()` (`gen_tpl.py`, hence `glb2html.py`) adds `name` and `about` to `BOOT`; `template.html`: `ABOUT` object, `#aboutOverlay` panel, `page.about.*` and `page.help.about` texts in `fr.json` and `en.json`. A standalone page (no shell) has no about.
- **Test**: `tests/apropos.py` (new: no file, fr and en files, fallback, `?` AZERTY and QWERTY, input field, "Don't show again" and reload, Settings checkbox, literal tag, tiles, no `localStorage`, no JavaScript error). Counter-test: it fails on 1.4.4.

### 03/11/2026: version 1.4.4: displayed weight = received weight; viewer: the tiles line from the start

- **Fixed** (a): the weight on the "Tiles: …" line (page and viewer) summed the index `bytes`; after `gltfpack` compression the index keeps the old sizes, so the display showed almost twice the weight actually received. `tilesStatus()` (`core.js`) adds a `got` field (sum of `t.got`, the downloaded size, or of `t.bytes` until the tile has arrived); the display (`template.html`, `viewer_tpl.html`) uses it. **The loading budget stays on the index `bytes`** (Klaatou's decision); `bytes` is neither removed nor renamed; `got` is part of the `tilesInfo()` key.
- **Fixed** (b): in the viewer the tiles line stayed empty until the next change, because the `onTiles` handler is attached after `loadTiles`; the `onTiles` setter (`core.js`) now replays the state when attached.
- **Test**: `tests/tuile_ici.py` (index inflated by 2 MB per tile: `bytes` follows the index, `got` and the displayed line follow the served files; viewer: line present as soon as the handler is attached). Counter-test: without the fix these checks fail.

### 03/11/2026: version 1.4.3: tiles line: one element per line

- **Fixed** (Klaatou's report: the Information / State window was hard to read): since 1.4.2 the tiles line joined everything with "·": "Tiles: … · Tile(s) under the avatar: … · Overview (counted apart): …". Each element now has its own line: loaded tiles (with "in progress" and "failed"), tile(s) under the avatar, overview. Same fix in the viewer (`#tilesLoad`): the tile under the avatar on its own line.
- **How**: `#tilesInfo` is a single `div` whose text is built in `template.html`; elements are separated by a newline, displayed through `white-space: pre-line` (CSS of `#tilesInfo` and `#tilesLoad`). The text copied by the diagnostics keeps the newlines.
- **Test**: `tests/tuile_ici.py` checks the real display (`innerText`: three lines in the page, two in the viewer); counter-test: it fails on 1.4.2.

### 03/11/2026: version 1.4.2: the name of the tile under the avatar in the status panel

- **New** (Klaatou's request): in a region split into tiles, the "Tiles: N loaded / …" line of the Information / state panel (and the viewer's line) now adds "Tile(s) under the avatar: T_3_0_5.glb": the file(s) whose box contains the walking avatar's position (0.5 m tolerance; two names when boxes overlap). No more F12 to know where one is. Outside walking (global view) the mention disappears. `tilesState().here` returns the same list (diagnostics).
- **How**: `tilesStatus()` (`core.js`) computes `here` with `inTile`; the `tilesInfo()` key includes it, otherwise the line would not redraw when crossing a border with nothing loading. Texts: `page.tiles.here` (fr and en); `template.html` and `viewer_tpl.html` (both pages show the same mention).
- **Test**: `tests/tuile_ici.py` (new: synthetic region, 300 m walk in steps, teleport, leaving the walk; compared with an independent computation of the boxes).

### 02/11/2026: version 1.4.1: `CLAUDE.md` removed

- **Removed** (Klaatou's request, after reading it): `CLAUDE.md` served the Claude Code sessions up to v37 (23/10/2026); it said so at its very top. The current state is in `REPRISE.md`, the detail in `CHANGELOG.md` and the histories, the usage in the manual. It also held decisions reversed since (for example the chat arrows going through `viewer.holdKey`, changed in 1.2.1). It stays in the git history. `tests/samples.py` no longer checks it; the manual ("Standalone files", FR and EN) no longer cites it. The file itself is removed with `git rm CLAUDE.md` (or by deleting it before `git add -A`).
## 1.4.0 (02/11/2026)

### 02/11/2026: 1.4.0 release: map nicknames, chat beep, launchers' guard

- **GitHub release notes** (to attach: `galerie-photos.zip` and `region-simple.zip`, built by `python fabriquer_paquets.py`): the two bullets below (the French ones stay in `CHANGELOG.fr.md`).
- **Release** 1.4.0 gathers the batches noted "Unreleased" since 1.3.0 (described below). `VERSION` goes from `1.3.5` to `1.4.0` (the minor number goes up: features were added). Built files that change compared to 1.3.0: `glb2html.py`, `index.html`, `carte.html`, `glb-viewer.html`, `presence_server.py`, `oar2glb.py` and `glb2tiles.py`; the packages (`paquets/`) change too.
- **What is new in 1.4.0**: world map: nicknames of walkers and of visitors in the global view, protected by a key (`--map-names-key` of the presence server, `carte.html#pseudos=KEY`), numbers without double counting ("1 walker", "2 visitors, 1 walking"), several `#` accepted in the map's address; chat: a beep for every message when the page is not focused (setting among the sounds); packages: launcher guard against the repository's source folder ("Download ZIP"), `paquets/README.txt`.

### 02/11/2026: version 1.3.5: chat: a beep for every message when the page is not focused

- **New** (Klaatou's request): a beep for every message from another visitor when the page is not focused (hidden tab or another window in front: `document.hidden` or `!document.hasFocus()`). One note (988 Hz), at most one beep every 2 s; never for one's own messages nor for the history reloaded on connection; if the message mentions the nickname and the "mentions" beep is checked, only that one sounds. Setting "Beep for every message when the page is not focused" among the sounds (`soundMsg`, checked by default, follows the general "Sounds" setting and the volume). The sound remains subject to the browser rule: a first action on the page is needed. `src/template.html` (the `SND` sound system, settings, message reception), `page.opt.sound.msg` FR and EN, manual § 21.6 FR and EN. **Built**: `glb2html.py`, `index.html`, `glb-viewer.html`, `oar2glb.py` and `glb2tiles.py` change.
- **Test**: `tests/chat_bip.py` (new: real presence server, Chromium, fake audio context counting the notes); counter-test: on the previous code the test fails (no beep without focus).

### 02/11/2026: version 1.3.4: standalone map: several # in the address

- **Fix** (Klaatou's finding: address `carte.html?region=X#name=Klaatou#pseudos=SECRET`). The standalone map read the `#` part as a single parameter (`name=Klaatou#pseudos=SECRET`) and did not see `pseudos=`, hence not the nicknames key; the region pages already accepted `#` as a separator (`hashParams`, `src/i18n.js`). `src/gen_tpl.py` now does the same. The manual says so (FR and EN). Test: `tests/carte_pseudos.py`, step 5b. **Built**: `carte.html` changes.

### 02/11/2026: version 1.3.3: world map: nicknames are protected by a key

- **Changed** (1.3.1 gave the nicknames to any page that queries the presence server; Klaatou's request: only to whoever has the key). The `--map-names` option is replaced by `--map-names-key SECRET` (at least 8 characters): the `rooms` answer only contains `names` (walkers, most recent first) and `viewers` (visitors in the global view) if the request presents the right key. The maps read it in the `#` part of their address: `carte.html#pseudos=SECRET`, and likewise behind a region's address for the map opened with M. Without a key or with a wrong key: only the numbers, exactly the same answer. The server compares the key in constant time and stops listening after 5 wrong keys per minute and per address (like the visits log). On a `ws://` address the key travels in clear: `wss://` for a real secret (said in the manual). The old `--map-names` option is kept but does nothing: it gives no nickname and the server writes so at start-up.
- **New**: visitors **in the global view** have their nickname on the map ("global view: ..." line), and a walker who goes back to the global view no longer disappears (the server erased the nickname: `peer.name = ""`, the v33 anonymous-spectators rule). The display nickname is only kept if `--map-names-key` is active, in memory, with no registry or file, and is only given with the key.
- **Tests**: `tests/carte_pseudos.py` rewritten (no key, wrong key, right key, global view, walker back in the global view, 5 attempts per minute, key too short, old option, map in French and English, map opened with M, booby-trapped nicknames). **Built**: `presence_server.py`, `glb2html.py`, `index.html`, `carte.html`, `glb-viewer.html`, `oar2glb.py` and `glb2tiles.py` change (embedded translations). FR and EN manual.

### 02/11/2026: version 1.3.2: launchers: guard against the repository's source folder

- **Fix** (Klaatou's finding: a user downloaded `web_3d.main.zip`, the repository's "Download ZIP", and ran the launcher in `paquets/`). That folder only holds the sources, without `site/index.html` or `site/lib/` (which `fabriquer_paquets.py` adds when building the zips): the launcher served an incomplete folder and the page was not found (404). The four launchers (`lancer-region.ps1`, `lancer-galerie.ps1`, `lancer-region.sh`, `lancer-galerie.sh`) now refuse that folder and print "Ce dossier est le CODE SOURCE du depot Web_3d..." with the address of the ready-to-use package (exit code 1 on Windows, 3 on Linux and macOS). `paquets/README.txt` (new, FR and EN) says the same; both repository READMEs warn not to use "Download ZIP".
- **Tests**: `tests/paquets.py` runs the launcher from the source folder (message, exit code, no server), checks the Windows launcher's text and `paquets/README.txt`. **Not tried under PowerShell**: the Windows guard's text is checked, not executed.

### 02/11/2026: version 1.3.1: world map: walkers' nicknames (option) and numbers without double counting

- **New**: `--map-names` option of the presence server (off by default). The `rooms` answer then adds `names`, the walkers' nicknames of each room, most recent first (20 at most). The maps (`carte.html` and the map opened with M) show a line of nicknames under the count: five at most, then "and 2 others". Without the option nothing changes: no nickname in the answer. A nickname is personal data and the server answers any page that asks: the manual says so (world map). Nicknames go through `textContent` (test with a booby-trapped nickname).
- **Changed** (Klaatou's request): a number is no longer counted twice. "1 walker" when every visitor is walking (before: "1 visitor" then "1 walker"), "2 visitors, 1 walking" when there are also spectators, "1 visitor" when nobody is walking; one line, in the cards and in the total. The language key `map.sep` goes away (no longer needed); new keys `map.mixed`, `map.and`, `map.other` and their `page.map.*` equivalents.
- **Tests**: `tests/carte_pseudos.py` (new: real presence servers with and without the option, Chromium, French, English, map opened with M, booby-trapped nickname); `tests/v47.py` and `tests/v52.py`: expected texts updated.
- **Built**: `presence_server.py`, `glb2html.py`, `index.html`, `carte.html`, `glb-viewer.html`, `oar2glb.py` and `glb2tiles.py` change (the translation texts are embedded in them). FR and EN manual.

## 1.3.0 (02/11/2026)

### 02/11/2026: 1.3.0 release: Linux and macOS launchers for the packages

- **GitHub release notes** (to attach: `galerie-photos.zip` and `region-simple.zip`, built by `python fabriquer_paquets.py`): the two bullets below (the French ones stay in `CHANGELOG.fr.md`).
- **Release**: 1.3.0 (02/11/2026) gathers batches 1.2.1 to 1.2.4 described below; 1.2.3 had already been published on GitHub (tags 1.2.0 to 1.2.2 never existed). `VERSION` goes from `1.2.4` to `1.3.0` (the minor number goes up: features were added). No built file changes compared to 1.2.3: only the packages, tests and documents change.
- **What is new in 1.3.0**: launchers and renaming for Linux and macOS in both packages (`.sh`, `.command`), next to the Windows scripts; the zips mark these files executable; documentation for the three systems. **Not tried on macOS.**

### 02/11/2026: version 1.2.4: Linux and macOS launchers for the packages

- **Packages**: `lancer-galerie.sh` and `lancer-region.sh` (local server on the first free port from 8000 to 8020, `localhost` address, browser opened by Python; `python3` 3.7 or later is needed), `renommer-galerie.sh` and `renommer-region.sh` (the same five changes as the Windows scripts) and their `.command` files for a double-click on macOS. They are ASCII with LF line endings, marked executable (0755) in the zips by `fabriquer_paquets.py`; `.gitattributes` forces LF for `*.sh` and `*.command`. `README.txt`, `galerie.html` and `readme.html` cover the three systems. **Not tried on macOS** (the documents say so); the Windows scripts do not change.
- **Tests**: `tests/paquets.py` checks the files, the permissions in the zip, the syntax (`sh -n`), a real launch (port, MIME types, nothing outside `site/`, next port when the first is taken, stop with Ctrl+C) and the renaming (refusal, full renaming, conflict, back to the original name). Counter-test: without the executable permission, eight checks fail.
- **Documents**: `README` and overview, FR and EN.

### 01/11/2026: version 1.2.3: more rigorous chat test

- **Test** `tests/chat_fleches.py`: it waits for the real presence state (`online`) instead of a help text that exists from the start, gives the page 1.5 s before pressing Enter, and prints the full state (presence, window focus, field, active element, caret) when a check fails. Klaatou's finding: the test failed on his machine while the page worked (diagnostic: Enter opens the field with focus, the left arrow moves the caret, Esc closes it). No change to the page.

### 01/11/2026: version 1.2.2: package documentation (readme.html), movement pad

- **Packages**: `lisezmoi.html` becomes `readme.html` (same name as `README.txt`); its first section is now "What is where" and the settings, starting view, zones and renaming move to the end of the page (sections 6 to 9); new section "Appearing on a world map" (what to send to a shared map: name, complete address, thumbnail, place on the grid, presence), also in `galerie.html` (section 8); the example house's help panel is flagged "to review with your GLB", with how to delete or move it (viewer or `region.zones.json`) and why the coordinates are the page's; links to the repository (convoar, `dist` folder, procedures); `README.txt`: same flag for the panel; `aide.html`: the K key is described as the movement pad.
- **Page help** (H key): `page.help.k` says "movement pad (on-screen arrows)", in French and English; manual (key table); `tests/v46.py`.
- **Test** `tests/chat_fleches.py`: it checks that `websockets` is installed and that the presence server answers, and says so clearly otherwise (failure seen on Klaatou's machine: without a presence server, the Enter key does not open the chat).
- **Repository**: `paquets-sources.zip` (a delivery archive, committed by mistake at the root) is removed by this patch; `.gitignore` now ignores it.

### 01/11/2026: version 1.2.1: chat, help and README.txt of the packages, README

- **Fix** (chat): while typing in the chat, the arrows moved the avatar instead of the cursor in the text (a v33 decision: you could walk while writing), which made it impossible to correct a message (Klaatou's finding). They now stay in the text while the input is open; Esc closes it and gives the arrows back to walk mode. `template.html` (the chat's key handler), help (`page.help.chat.arrows`), FR/EN manual (§ 18.5, § 22.6 and the key table). Tests: `tests/chat_fleches.py` (new, with a real presence server) and `tests/v33.py` (two checks inverted).
- **Packages**: `LISEZMOI.txt` becomes `README.txt` (international name), gives the addresses of the help (`aide.html`) and of the documentation, and says where to find the help in the 3D world (the “?” panel); `aide.html`: the K key is described exactly (shows or hides the arrow buttons), the chat follows the new help.
- **Documents**: the FR/EN `README` presents the two packages right under the demo; `PROCEDURES` § 12, step 4: creating the GitHub release step by step.
## 1.2.0 (01/11/2026)

### 01/11/2026: 1.2.0 release: clickable image zones, numbers, `dist/` and ready-to-use packages

- **GitHub release notes** (to attach: `galerie-photos.zip` and `region-simple.zip`, built by `python fabriquer_paquets.py`): the three bullets below (the French ones stay in `CHANGELOG.fr.md`).
- **Release**: 1.2.0 (01/11/2026) gathers batches 1.1.1 to 1.1.8 described below. `VERSION` goes from `1.1.8` to `1.2.0` (the minor number goes up: features were added). No built file changes compared to 1.1.8.
- **What is new in 1.2.0**: optional `link` key on an `image` zone (a click or E opens a page); image zone numbers (a Settings box, drawn flat); the zone placement click also works while walking (viewer); `dist/` is tracked by git (`tests/dist_a_jour.py` test); `build.py` writes LF everywhere; ready-to-use packages `galerie-photos.zip` and `region-simple.zip` (sources in `paquets/`, `fabriquer_paquets.py` script).
- **Documents**: manual (`link` row of § 27.3, § 37.1), `PROCEDURES` (§§ 6 and 12), README, zones sample and samples README, overview, histories, FR and EN.

### 01/11/2026: version 1.1.8: ready-to-use packages in the repository

- **Change**: the sources of two packages are in `paquets/`: `galerie-photos` (a 30-photo gallery: zones, generic images, sign, help panel, `galerie.html` page) and `region-simple` (a region from a GLB named `region.glb`: sample GLB, template config, `lisezmoi.html` documentation, help zone on the example house). Each has a visitors' help (`aide.html`, opened by a “?” panel), its creator documentation (`galerie.html`, `lisezmoi.html`), a renaming script (`renommer-*.bat`), a Windows launcher (`lancer-*.bat`, PowerShell mini-server on `localhost`, ports 8000 to 8020) and a `presence/` folder.
- **`fabriquer_paquets.py`** (root) assembles the zips into `paquets-zip/`: sources + `index.html`, `favicon.ico` and `presence_server.py` from `dist/`, `lib/three-X/` written by `glb2html.write_modular_lib`, `VERSION.txt`, the presence server's version in the notices, `.bat` and `.ps1` as CRLF, zip dates = the version's date: two builds give identical zips.
- **Test** `tests/paquets.py` (new): build, structure, JSON, zones and region consistent with their files, presence off, no `file://` or real host name in the texts, launchers in ASCII and CRLF, faithful copy of `presence_server.py`, opening in Chromium (click on the gallery's help panel, walking in the region).
- **Documents**: "Ready-to-use packages" section of the FR/EN `README`, `PROCEDURES` § 12, overview, histories (batches 1.1.6 to 1.1.8). `.gitignore`: `!paquets/**` exception and `paquets-zip/`; `.gitattributes`: `.bat` and `.ps1` as CRLF.

### 01/11/2026: version 1.1.7: `build.py` writes LF everywhere

- **Fix**: `build.py` wrote the `.py` files of `dist/` and `glb-viewer.html` with `write_text`, i.e. as CRLF on Windows, while `.gitattributes` forces LF in git: every `git add` printed "CRLF will be replaced by LF" for six `dist/` files. All built files (and `VERSIONS.json`, the fingerprint file) are now written as bytes, LF everywhere. `dist/` bytes do not change on Linux; on Windows, no more warnings.

### 01/11/2026: version 1.1.6: `dist/` in the repository

- **Change**: the `dist/` folder (built files: viewer, generator, presence server, tools) is now tracked by git (removed from `.gitignore`): a creator who downloads the repository has everything, with no `python build.py`. Klaatou's decision: the presence server was hard for a novice to find (the source `src/presence_server.py` does run, but the docs pointed to `dist\`, which did not exist without building).
- **Test**: `tests/dist_a_jour.py` (new) builds into a temporary folder and compares byte for byte with `dist/`: fails if `dist/` is stale compared to `src/`. Run it before every commit; after each batch, `python build.py` then `git add -A dist`.
- **Documents**: FR/EN `README` (the ready-to-use files are in `dist/`), `PROCEDURES` § 6 step 1 FR/EN (where to find `presence_server.py`).

### 31/10/2026: version 1.1.5: histories, procedures, overview, image tests

- **Documents**: `HISTORIQUE`/`HISTORY` (batches 1.1.1 to 1.1.5), `PROCEDURES` (steps 5 and 6: link, numbers), `VUE_ENSEMBLE`/`OVERVIEW` (image zones: link and numbers), FR and EN, `verif_trad.py` OK.
- **Tests**: `image_zone.py` and `image_dossier.py`: the test images were called `reg-only.png`, `dossier-only.png`, `dossier-only2.png`; since the caption comes from the file name, the text after the hyphen ("only") creates a caption strip (1024 px wide, `core.js` `W2`) that the test read instead of the image. Names without a hyphen: `image_dossier` passes entirely, `image_zone` keeps only the known `file://` console error (refused `HEAD` request, no visible effect).

### 31/10/2026: version 1.1.4: image zone numbers laid flat

- **Fix**: image zone numbers are now flat planes in the image's plane (same direction as the image), no longer camera-facing labels: seen at an angle those sank into the image and the wall and the tens digits (19, 20, 21) were cut off (Klaatou's finding). `core.js`: `makeNumber`. `zones_numeros.py` test: checks the orientation.

### 31/10/2026: version 1.1.3: image zone numbers, placing by click while walking

- **Change**: new **"Image zone numbers (to find them)"** box in the exported page's Settings (unticked at every opening, never remembered; absent if the region has no image zone): a big number in front of each image zone, even if its image is missing, to find positions 1, 2, 3... without the viewer. Number = the one in the targeted file name, otherwise the display name, otherwise the `id`. Hidden by the scenery (`depthTest`), not clickable.
- **Fix** (viewer): the zone placement click was ignored while walking although the button stayed on "Placement ACTIVE". It now places while walking too (ray through the screen centre when the mouse is captured).
- **Tests**: `tests/zones_numeros.py`, `tests/pose_promenade.py` (new). **Not tried**: Edge, Windows, real mouse capture (simulated), graphics card.

### 31/10/2026: version 1.1.2: documents on a picture's link

- **Documents**: FR/EN manual (field table: `link` row; § 37.1: the link, its address rules, placing in global view or while walking, the `lien_image.py` test); `docs/samples/region.zones.sample.json` (the `painting-1` zone carries a `link`); samples README FR/EN. `HISTORIQUE`/`HISTORY`: still to do.
- **Finding documented, not fixed**: the placement click is ignored while walking (`viewer_tpl.html`, `viewer.walking`) while the button stays on "Placement ACTIVE"; only the P key places. Fixing the button or allowing click placement while walking: Klaatou's decision pending.

### 31/10/2026: version 1.1.1: link of a picture (`image` zone)

- **Change**: an `image` zone accepts an optional `link` key (an `http(s)` address or a page relative to the page, for example `galerie.html`). Clicking the picture, or pressing E in front of it, opens the link in a new tab, like a `url` zone; tooltip and hand cursor on hover. Editor: field "Link (page opened on click or E, optional)". `link` is only written to the zones when filled in (`core.js` `cleanZone`, `gen_tpl.py` `clean_zones`): existing zone files do not change. An older page ignores `link` (the picture shows with no action). **Warning**: an older editor (`glb-viewer.html`) that saves zones loses the `link` keys: keep the viewer and the page at the same version.
- **Fix**: a picture without a link is no longer a "near zone": no more "click or E: Image 8" prompt in front of it (E had no action, `zoneTick` in `core.js`). A picture whose image is missing is not clickable.
- **Security**: only `http(s)` addresses pass (`okUrl`); `javascript:` is refused ("Invalid link" message).
- **Test**: `tests/lien_image.py` (new). **Not tried**: Edge, Windows, graphics card, tiles mode.

## 1.1.0 (31/10/2026)

### 31/10/2026: 1.1.0 release: bilingual documents up to date

- **GitHub release notes** (to attach: `galerie-photos.zip` and `region-simple.zip`, built by `python fabriquer_paquets.py`): the three bullets below (the French ones stay in `CHANGELOG.fr.md`).
- **Release**: 1.1.0 (31/10/2026) gathers batches 1.0.1 to 1.0.4 and those of 30/10/2026 described below. `VERSION` goes from `1.0.4` to `1.1.0` (the minor number goes up: features were added). No built file changes: `VERSIONS.json` stays as it is (`glb2html.py` and `glb-viewer.html` 1.0.4, `index.html` 1.0.3, `carte.html`, `presence_server.py`, `oar2glb.py`, `glb2tiles.py` 1.0.1).
- **What is new in 1.1.0**: `image` zone (a picture on a wall, placed by click; `medias` subfolder; flexible name, "bare number" mode and `imageExts`; caption in the file name or in `12.txt`; images, captions and `.glb` always revalidated); editor: region folder and image preview; `--solid-materials` (`solidMaterials` key); pointer: building name (root object); clear message when WebGL is unavailable; one version number per file (`VERSIONS.json`) and a mark for every file; presence server: console (terminal sequences, `version` command) and "http request" lines behind a relay; note for creators.
- **Documents**: manual § 37 (new) and §§ 3, 27.3, 27.4, 34.4, 36.5; `PROCEDURES` §§ 4, 5, 9, 11 (the `version` command is compared with `build.py`'s list, no longer with the `REVISION` file); histories; README; `docs/samples/README`; overview; `CLAUDE.md`; `REPRISE.md`; all in French and English. `REFERENCE_OPTIONS.md` did not change (the `--solid-materials` line is already there).

### 31/10/2026: version 1.0.4: one version number per file

- **Change**: every built file that carries a version number (`glb2html.py`, `index.html`, `carte.html`, `glb-viewer.html`, `presence_server.py`, `oar2glb.py`, `glb2tiles.py`) shows **its own** number, which changes only when the content of THAT file changes. `VERSION` stays the batch counter. Before, `build.py` wrote the batch number in all these files, even when their code had not moved.
- **Mechanism**: `build.py` builds everything with a neutral number, computes each file's fingerprint and compares it with the one in `VERSIONS.json` (new repository file: last fingerprint and number of the batch that modified the file). Only a file whose fingerprint changed takes the current batch number; then everything is built again with the real numbers. `python build.py` prints each file's number and marks those modified in the batch; it updates `VERSIONS.json` (to commit with the batch, except with `--out`). Option `--empreintes FILE`: writes the neutral fingerprints and stops (used to rebuild the history).
- **Numbers rebuilt from the history** (each batch 1.0.0 to 1.0.3 built with a neutral number): `glb2html.py` 1.0.3, `glb-viewer.html` 1.0.3, `index.html` 1.0.3, `carte.html` 1.0.1, `presence_server.py` 1.0.1, `oar2glb.py` 1.0.1, `glb2tiles.py` 1.0.1. In this batch, `glb2html.py` and `glb-viewer.html` move to 1.0.4 (the build code changed); `index.html` is byte for byte the 1.0.3 one.
- **Detail**: the number shown by a page (\"Copy diagnostics\") is that of its file: exported page = `glb2html.py`, modular shell = `index.html`, viewer = `glb-viewer.html`. `core.js` carries the `__CORE_VERSION__` marker for this (replaced when the page or shell is generated); `gen_tpl.py` gets the `SHELL_VERSION` and `MAP_VERSION` constants.
- **Test**: `glb2tiles`, `oar2glb`, `v34`, `v36_viewer_lang`, `v37`, `v39` and `image_diag` read the right file's number in `VERSIONS.json` instead of the `VERSION` file.

### 31/10/2026: version 1.0.3: images, captions and `.glb` up to date also when the replaced file is older

- **Fix**: 1.0.2 revalidated with `cache: 'no-cache'`, which only detects a **newer** file: a server (`http.server`, measured) answers "not modified" for a file older than the browser's copy, e.g. a previous folder put back with its old dates. Now, before each image, caption or `.glb`, the page sends a `HEAD` request without cache, builds a fingerprint (`ETag` or `Last-Modified`, plus size) and reads the file at the address `file?v=fingerprint`: from the cache if the fingerprint is known (no re-download of an unchanged file), from the network otherwise. A replaced file, older or newer, gets another fingerprint hence another address. Without a possible fingerprint (no `ETag` nor `Last-Modified`, `HEAD` refused): `cache: 'reload'`, always right but a full download at every opening. A missing file (404) is detected by the `HEAD`, without downloading.
- **Unchanged**: tiles, `index.html`, `lib/` and `favicon.ico` keep the browser's normal cache.
- **Test**: `tests/image_cache_vieux.py` (older file, unchanged file not downloaded again, server without `Last-Modified`); `tests/image_zone.py` also waits for the image-less zone to be hidden before reading it.

### 31/10/2026: version 1.0.2: images, captions and `.glb` always revalidated (no more stale cache)

- **Fix**: an image replaced under the same name (a copy keeps the file's old date) stayed displayed until the browser cache was cleared, even after Ctrl+F5: an `img` tag has no cache setting. The page now requests each image with `fetch` and `cache: 'no-cache'` (the browser revalidates with the server: unchanged file = "not modified" answer, no new download), then loads it from a `blob:` address. Same setting for the caption text files and for the whole `.glb` of the modular page. An HTTP error is still a failure (next candidate); if `fetch` is impossible (another site without CORS, `file://`), the previous direct load is the fallback; `data:` and `blob:` addresses unchanged.
- **Unchanged**: tiles (tiled regions), `index.html`, `lib/` and `favicon.ico` keep the browser's normal cache.
- **Test**: `tests/image_cache.py`; `tests/image_medias.py` and `tests/image_numero.py` now read the file read from the image diagnostics (`imageDiag`), the image address having become `blob:`; `tests/image_diag.py` reads the number from `VERSION` instead of hard-coding it; `tests/image_zone.py` waits for all images before reading them.

### 31/10/2026: version 1.0.1 (batch number) and image diagnostics

- **Change**: from this batch on, `VERSION` gets a patch number with every delivered patch (`1.0.1`, `1.0.2`...), to see at a glance whether the generator, the page and the viewer are up to date: the version shows in the generator's `[OK]` line, in the page help, in the viewer title and in "Copy diagnostics"; `config.json` receives it (`--update` reports the change). Klaatou's decision of 31/10/2026 (it replaces rule 15 "never on my initiative" for these patch numbers). Publication (tag, `1.1.0` since features were added) remains his call.
- **Addition**: "Copy diagnostics" lists one line per image zone: zone, target, file actually read (`medias` folder or region folder) and caption with its source (file name or text file), or hidden.
- **Test**: `tests/image_diag.py`.

### 31/10/2026: `medias` subfolder of the region

- **Addition**: images of `image` zones and their text files (`12.txt`) go in a **`medias`** subfolder of the region (next to the `.glb`). The page, the editor and the generator look in `medias/` first, then in the region folder: images already in place keep working. The name in the zone stays the file name (`12`, `12-Title.jpg`), without `medias/`. Optional config key `mediaDir` (`"mediaDir": ""`: no subfolder; another name, e.g. `"medias2"`, for the page and the editor; the generator always looks for `medias`). Search order for a bare number: every extension in `medias/`, then every extension in the region folder.
- **Test**: `tests/image_medias.py`.

### 31/10/2026: "number only" mode: the page finds the image and its title itself

- **Addition**: an `image` zone whose name has no extension (`12`) no longer needs completing: the page tries `12.jpg`, `12.jpeg`, `12.png`, `12.webp`, `12.gif`, `12.avif` in that order and keeps the first file found (optional config key `imageExts`, e.g. `"imageExts": "png,jpg"`; absent: the order above). Missing extensions show up as 404 responses in the browser console: that is expected. Works over `http` only, like every image.
- **Addition**: caption in a neighbouring text file: the first non-empty line of `12.txt` (UTF-8, at most 200 characters) becomes the caption under the image; without `12.txt` the caption comes from the file name after the first dash (`12-Title.jpg`). The text file is read at every page load: editing `12.txt` is enough, no need to run the generator again. In the editor both are read from the chosen region folder.
- **Change**: when `12.jpg` (or another extension) exists, the editor and the generator **leave** the name `12` (and say so); they only complete names like `12-Title.jpg`, which the page cannot guess.
- **Test**: `tests/image_numero.py`.

### 30/10/2026: the generator completes image names without extension

- **Addition**: `glb2html.py` itself completes the name of an `image` zone written without an extension (`12`) from the files of the page's folder (the one of `-o`, next to the `.glb`): `12-Cezanne - Apples and Oranges.jpg`. Same rule as in the editor (jpg, jpeg, png, webp, gif, avif, bmp; `12.ext` or `12-...`; `12` does not take `120-...`; first in alphabetical order, reported). Applies at generation, with `--update`, `--zones-only` and for modular zones; a hosted page cannot list a folder, so the generator writes the real name. It prints each completed name, duplicates and names with no file (left as is). A name with an extension, a path or an address is never changed. After **adding** an image to the folder, run the generator again.
- **Test**: `tests/image_noms_gen.py`.

### 30/10/2026: flexible image: names without extension are completed after choosing the folder

- **Fix**: with `patch_image`, a name typed without an extension (`12`) stayed as is when the region folder was not yet authorised in the editor session (cause read: `regionDirQuiet` only returns an already-authorised folder), and nothing retried afterwards. Now: (1) after "Choose the region folder", every image name without an extension is completed at once; (2) opening a zone whose name has no extension completes it when the folder is already authorised; (3) until it is completed, the line under the "Image" field says so plainly.

### 30/10/2026: flexible image field and caption (`1` → `1.jpg` or `1-Titre.png`)

- **Addition**: in the editor's `image` zone you can just type `1`. With the region folder chosen, the editor looks for `1.jpg`, `1.png`, `1.webp`... (jpg, jpeg, png, webp, gif, avif, bmp, case-insensitive) or `1-Name.jpg` (`1` does not take `10-...`), and **writes the real file name** into the zone: the exported page has no list to read. Several files match: the first in alphabetical order is taken and the editor says so. No file, or no folder chosen: the editor says so and leaves the text as is. A name with an extension, a path or an address is never changed.
- **Addition**: small caption under the image, in the editor and in the exported page: the text between the first `-` of the file name and the extension (`1-Soleil_couchant.jpg`: "Soleil couchant", `_` becomes a space). No dash: no caption. Image not found in the exported page: the caption disappears with it.
- **Test**: `tests/image_legende.py`.

### 30/10/2026: materials made opaque (`--solid-materials`): end of seeing through BLEND walls

- **Addition**: option `--solid-materials TEXTS` (config key `solidMaterials`, empty by default: nothing changes). Materials whose name contains one of the texts (comma-separated, case-insensitive; `=name`: exact name) are drawn solid: `transparent = false`, `depthWrite = true`, `alphaTest = 0.5` (texels at least half transparent are cut out, the rest is solid; without this threshold the zero-alpha texels, black underneath, made a black plate). Applies to the exported page, the editor and the tiles; live-changeable through `setCfg` (a material removed from the list goes back to its original state). Foliage keeps its own treatment. `--update` keeps the key. In the editor, the "Materials drawn solid" field of the settings (render section, under the foliage threshold) sets it live; it is saved with the settings and exported as `--solid-materials`.
- **Fix**: a wall whose glTF material is `BLEND` let you see the counter, the plinth and the lighting through it (reproduced on `Mesh_Store.glb`, material `pbrmat-229153941891471516`). Cause read in the code: `GLTFLoader.js:3514-3517` (three 0.160.0) sets `depthWrite = false` on every `BLEND` material and `core.js` only reset it for foliage: the wall does not fill the depth buffer and the transparent objects behind it are drawn over it. Not the alpha (the `OPAQUE` copy), not back faces (`doubleSided: true` changes nothing in the render).
- **Test**: `tests/solid_materiaux.py`.

### 30/10/2026: the pointer gives the name of the root object; hole guide unchecked by default

- **Addition**: the pointer tag (exported page, `--names`) and the editor's "Visé" panel now show the **root object** name in bold (the topmost named ancestor, i.e. the building name as `extraire_batiments.py --list` gives it), and the sub-element in small ("part: prim0-mesh"). Before: the sub-element in bold and only the nearest parent. Technical wrappers (model, tiles) are ignored. Names used by zones (`mesh` field) are unchanged. Key `page.pick.parent` replaced by `page.pick.part`. Test: `tests/pointeur_objet.py`.
- **Change**: the viewer's "Show the hole guide (not exported)" box is unchecked by default (`guide: false`). A value already saved in a settings file still wins.

### 30/10/2026: "image" zone, preview from the region folder (editor)

- **Addition**: in the editor (`glb-viewer.html`), the button "Choose the region folder (image preview)", under the "Image" field of an `image` zone, reads the images from the region folder, next to the `.glb` (subfolders accepted, `..` refused), instead of looking them up next to the page. The folder is read-only and remembered per region together with the zone-saving one (Edge and Chrome only); without it, or if the image is not there, nothing changes. Exported pages are unchanged. Test: `tests/image_dossier.py` (OPFS stand-in folder; the real folder dialog is not tried).

### 30/10/2026: "image" zone, editor label

- **Fix**: in the editor, the label of an `image` zone is no longer cut off when the wall has relief in front of it (depth test off for this label). Test: `tests/image_zone.py`.

### 30/10/2026: "image" zone, region folder

- **Fix**: in a page that loads a region through the shell (`index.html?region=folder/NAME`), the pictures of `image` zones are looked up in the region folder, next to the `.glb`, not next to the page; a page inside the region folder or a standalone file is unchanged. The editor shows, under the "Image" field, the exact address the image is looked up at. Test: `tests/image_zone.py` (region in a subfolder, shell at the root).

### 30/10/2026: mark (fingerprint) of every built file

- **Added**: `build.py` computes a mark for every file in `dist\`, the first 8 characters of its SHA-256, and lists them at the end of the build. `presence_server.py`, `oar2glb.py` and `glb2tiles.py` show it (`--version`, the console "version" command, first line of the log, start-up line): it changes if and only if the file changes. The `REVISION` file and its rule are gone. Test: `tests/marque.py`.

### 30/10/2026: clear message when WebGL is unavailable

- **Fix**: when the browser refuses to create the WebGL context (hardware acceleration off: recent Chromium browsers no longer fall back to software rendering), the region page and the viewer show a message with the ways out (another browser, the `--enable-unsafe-swiftshader` option, acceleration back on) instead of staying on "Loading…" or doing nothing (`core.js`, `webglMissing`). Test: `tests/webgl_absent.py`.

### 30/10/2026: "image" zone

- **Added**: `image` zone type, a picture laid flat against a wall. Placed by clicking a wall in the editor (turned to the face hit, 2 cm in front; floor and ceiling refused), width and height adjustable (height 0 = from the image), file relative to the page or http(s) or `data:` address. Missing image: nothing in the exported page, a panel in the editor. Opened from disk, the page cannot load the image (the browser refuses it): nothing is shown. Test: `tests/image_zone.py`. Documents not updated yet (see `REPRISE.md`).

### 30/10/2026: moderation console, version and revision

- **Fix**: the sequences the terminal sends into the server console (replies to tmux, arrow keys, mouse wheel, text colour) are removed from the line before it runs; before, they made the first commands answer "unknown command" (`presence_server.py`, `clean_console_line`).
- **Added**: `version` console command, and first line of `aide`: the version followed by the **revision**, taken from the new `REVISION` file at the root (date dd/mm/yyyy and letter, `30/10/2026a`) and replaced by `build.py` in the `dist\` file. The revision changes with every patch that modifies the shipped code; `VERSION` and the tag still change only at a release. It is also shown on the start-up line and with `--version`. Test: `tests/console.py`.

### 30/10/2026: address of the "http request" lines behind a relay

- **Fix**: behind a relay (`--proxy-header`, for example Tailscale Funnel), the "http request" lines showed the relay's address (`127.0.0.1`) instead of the visitor's, and the "since the last line for this address" count mixed all visitors. They now show the first address of the header, like WebSocket connections (`presence_server.py`, `empty_conn_ip`). The "empty connection" and "unreadable request" lines have no header read: they keep the relay's address. Only visible with `websockets` 14 and 15. Test: `tests/http_proxy.py`. `VERSION` does not change.

### 30/10/2026: VM, black screen

- **Documents**: `PROCEDURES` § 11, item 8: the black VM console screen was seen twice, what was ruled out (screen blanking, text console), what brought it back (Ctrl+Alt+Del from VMware) and the two commands to run before doing it. Cause still not established. No code change, no version number change.

### 29/10/2026: note for creators

- **Documents**: new note `docs/en/CREATORS.md` (and `docs/fr/CREATEURS.md`) to give to a creator welcomed on a presence server: origin to give, room prefix and `room`, `--presence-url`, refusals shown by the page, visit log, what the server records (code defaults, then the choice of Klaatou's demo server), what the creator does not control, what was tried. Linked from manual § 34.5. No code change, no version number change.

### 29/10/2026: alignment of the service file

- **Documents**: `web3d-presence.service` (repository root): `NOM_USER` becomes `UTILISATEUR`, as in `PROCEDURES` § 11 and `REPRISE.md`. No code change, no version number change.
## 1.0.0 (29/10/2026)

### 29/10/2026: 1.0.0 numbering, documents revised

- **Numbering**: v52 becomes **1.0.0** (the `v14` to `v52` tags stay). `X.Y.Z` scheme (major.minor.patch): a release that adds a feature gives `1.1.0`, `1.2.0`...; a release of fixes only gives `1.0.1`; a change that breaks existing things (renaming without an alias, incompatible file format) gives `2.0.0`. `VERSION` is written `1.0.0 (29/10/2026)`, the tag `v1.0.0`. `VERSION` and the tag only change when Klaatou decides on a release; the intermediate batches stay "Unreleased" entries. The names of `patch_vNNx.py` and `tests/vNN.py` do not change. Manual § 36.5.
- **Documents**: `PROCEDURES` (FR and EN) revised: header, tag command, version example, G / V / M / R keys, bans (exact IPv4, IPv6 by `/64`), new paragraph "Debian 13 VM: permanent service with a moderation console" (tried on 29/10/2026: `reboot`, `tmux kill-server`); overview, manual titles, `CLAUDE.md` updated; new `docs/samples/README.fr.md` and `docs/samples/README.md` (presentation of the 13 example files, checked by `tests/samples.py`).
- **Documents**: `PROCEDURES` § 11 (FR and EN): texts of `lance_presence.sh` and of the `web3d-presence.service` unit of the Debian 13 VM (user and folder replaced by `UTILISATEUR`), `tmux` added to the `apt` packages.

### 29/10/2026: `pseudos` command

- **Presence server**: the `pseudos [filtre]` console command (aliases `names`, `noms`) lists the reserved names: name as written, owner's `#XXXX` code, last seen, automatic release date, "(connected)" if the owner is online; the filter keeps the names containing a piece of text. Completes `oublier <pseudo>`. `tests/oublier.py` extended. Manual § 36.2. **Restart the presence server.** Requested by Klaatou.

### 29/10/2026: IPv6 by `/64`, `oublier` command, connection attempts stop

- **Presence server, IPv6**: `--max-per-ip` and bans (`bannir`) now count IPv6 by `/64` prefix (`ip_group`): a subscriber who changes the end of their address no longer dodges them. IPv4 unchanged; an IPv4 written as IPv6 counts as the IPv4; an old ban keeps its exact address. The console and the log keep the full address. `tests/ipv6.py` (new). Manual § 36.3. **Restart the presence server.**
- **Presence server, `oublier <name>` command**: releases a reserved name without stopping the server or touching `presence_identities.json` (written to the log; says if the owner is connected). `tests/oublier.py` (new). Manual § 36.2.
- **Page, connection attempts**: after **5 attempts** without ever connecting (12 if the connection had opened and was lost), the page stops instead of retrying forever (`core.js`, `PRES_TRIES_NEVER` and `PRES_TRIES_LOST` constants); the name box says "attempts stopped: reload the page to try again". `tests/essais_presence.py` (new, one minute). Manual § 36.4. Requested by Klaatou.

### 29/10/2026: `carte.html`, selectable addresses

- **`carte.html`**: the address shown by the "Show addresses" checkbox was **inside the link** of the card: inside a link, a click-drag does not select text (it was not the zoom: a test without the zoom behaved the same). It is now shown **under the card, outside the link**: selectable and copyable; the hover zoom stays on the card. Each card is wrapped in a cell (`.cell`). **Redrawing the grid also cleared the selection** (at every presence-server poll): the grid is only redrawn when the data changed (`lastSig` signature), and never while text in the grid is selected (`drawLater`). The zoom no longer disappears at every poll. `tests/v52.py` (section 10), `tests/v47.py` adapted. Requested by Klaatou.

### 29/10/2026: "3D" icon of the pages, replaceable by a `favicon.ico` file

- **All pages** (shell `index.html`, standalone page, `carte.html`, `glb-viewer.html`): a "3D" icon (white text on dark blue) is embedded by default (a small SVG in the `<link rel="icon">` tag); **if a `favicon.ico` file sits next to the page, it adopts it**: to change a site's icon, just replace that file, without rebuilding any page. `python build.py` writes a sample `favicon.ico` in `dist\` (16, 32, 48 and 64 px, from `src/favicon.ico`); copy it with `index.html`. Without that file the page keeps the embedded icon but the web server sees an unanswered `favicon.ico` request (as before). Safari was not tried. `tests/icone.py` (new). Manual § 36.1. **For the online demo**: copy `index.html`, `carte.html` and `favicon.ico` from `dist\`, rerun `ajout_og.py` (see `REPRISE.md`, point 11).

### 28/10/2026: the G key becomes a toggle

- **Page and viewer (`core.js`)**: while walking, **G** captures the mouse if it is free and **releases** it if it is captured (`toggleMouse`). The "Capture the mouse" button only captures: a captured pointer cannot click, so its label does not change. Status and help texts, manual (keys, § 19.4, arrows pad), `CLAUDE.md` and `tests/v34.py` adapted. Requested by Klaatou.

### 28/10/2026: the mouse is captured only on request

- **Page and viewer (`core.js`)**: a click in the view, while walking, no longer captures the mouse (the first click used to). Capturing is on purpose: the **G** key or the "Capture the mouse" button. Without capture, a click, a double-click (teleport) and a click on a zone work where the cursor is, and dragging with the button held turns the view (as after Esc). Help, status and viewer bar texts, manual (keys, § 19.4, § 29), `CLAUDE.md` and `tests/v34.py` adapted. Requested by Klaatou.

### 28/10/2026: presence server, unreadable requests

- **Presence server**: a request that is not HTTP (Windows Remote Desktop probe `mstshash`, start of a TLS connection, arbitrary bytes) wrote a full trace (`InvalidMessage`, "did not receive a valid HTTP request"). An "unreadable request" line replaces it: recognised kind and start of the request, at most one per minute, per address and per kind. Seen on Klaatou's server (probes from the Internet). `tests/v51_vides.py` and `tests/v52_http.py` adapted. Manual § 35.5. **Restart the presence server.**

### 28/10/2026: `carte.html` without a presence server

- **`carte.html`**: the "Arrival alert (sound and marker)" checkbox only appears if at least one region has a presence server (the online demo has none). `tests/v52.py` (section 9); manual § 35.2.

### 28/10/2026: online demo

- **Demo**: separate repository `Klaatou/Web_3d_demo` published with GitHub Pages (`https://klaatou.github.io/Web_3d_demo/`): PalmIsland and Hobbit regions linked by portals with relative targets, world map, no presence server. **README FR and EN**: "Try the online demo" link, clickable GIF.

### 27/10/2026: link to the GIF's source

- **README FR and EN**: in the GIF caption, "Outworldz" links to the site's OAR page.

### 27/10/2026: demonstration GIF in the READMEs

- **README FR and EN**: GIF of the PalmIsland region (`docs/images/PalmIsland_demo.gif`) under the title, with alternative text and caption (source: Outworldz site).

### 27/10/2026: oar2glb, convoar not found

- **`oar2glb.py`**: the default path of `convoar.exe` is no longer written in the code (it was a personal path): the `CONVOAR` variable, otherwise `convoar` from the PATH, otherwise `convoar.exe` next to `oar2glb.py`. When it is not found, the message says what it is for, gives the download address and the `--convoar CHEMIN` option. Help, manual and README updated; `tests/correctifs_v52.py`.

### 27/10/2026: history (table) and README

- **Documents**: in `docs/fr/HISTORIQUE.md` and `docs/en/HISTORY.md`, the v49 to v52 rows were under the "Useful commands" heading, outside the table (which stopped at v48): they are back in the table, with the "after v52" rows. README FR and EN: `--convoar CHEMIN` in the convoar prerequisite note.

### 27/10/2026: history up to date

- **Documents**: `docs/fr/HISTORIQUE.md` and `docs/en/HISTORY.md`: "after v52" rows (overview, credits, convoar prerequisite, line endings, corrective batch).

### 27/10/2026: corrective batch after the audit

- **Presence server**: no control character left in the log (terminal escape, bell); since the v52 "http request" line an HTTP request could put them there through its path. Creators: an origin `null` written without quotes is reported and ignored.
- **`.gitignore`**: adds `*.zones.json` (the real zone files, with possible Home Assistant addresses; `zones*.json` did not cover them) and `*.jsonl` (chat history, visit log), except `docs/samples/*.jsonl`.
- **Documents**: README FR and EN (Python 3.9 or later, files never to commit, convoar note on three lines); manual § 20.8 (non-existent option removed), § 34 (`null` in quotes), § 35.5 (log without control characters).
- **Tests**: `tests/portail_interne.py` and `tests/v24.py` dismiss the light rendering offer, the on-screen controls and the Information window, which covered their target (v41, v42, v46); `tests/v33.py` checks the grid rebuild at normal speed and expects the v40 help text; new `tests/correctifs_v52.py`. Code: duplicate imports and unused variables removed (`gen_tpl.py`, `oar2glb.py`, `glb-stats.py`).

### 25/10/2026: credits in the READMEs

- **README**: "Credits" section (French and English).

### 25/10/2026: one-page overview

- **Documents**: `docs/fr/VUE_ENSEMBLE.md` and `docs/en/OVERVIEW.md`: what works, what has been tried or not, what is left to do (test from the VM, note for creators, mouse, public demo, numbering, release), where to read what. No code change, no version number change.
## v52 (25/10/2026)
### 25/10/2026 : région en tuiles renommée, vue d'ensemble reliée aux tuiles
- **Page et viewer (`core.js`, `loadOverview`)** : le fichier `X.overview.glb` porte dans chaque nœud le chemin de sa tuile tel qu'il était au découpage (`extras.tile`, « X.tiles/T_3_0_0.glb »). Après un renommage des dossiers et des chemins de l'index (le binaire restant intact), plus aucune cellule n'était reliée à sa tuile : la vue d'ensemble restait visible sous les tuiles détaillées et les surfaces se recouvraient (moirures, plaques sombres, surtout sur le terrain et les rochers). La cellule est maintenant retrouvée par le nom du fichier de la tuile quand le chemin complet ne correspond pas (nom unique dans une région ; sinon la cellule reste visible, jamais de trou). On peut renommer une région à la main sans régénérer la vue d'ensemble. `tests/v52_renom.py`.
- **Page and viewer (`core.js`, `loadOverview`)**: the `X.overview.glb` file carries in each node the path of its tile as it was when the region was split (`extras.tile`, "X.tiles/T_3_0_0.glb"). After renaming the folders and the index paths (the binary being untouched), no cell was linked to its tile any more: the overview stayed visible under the detailed tiles and the surfaces overlapped (moire, dark patches, mostly on terrain and rocks). The cell is now found by the tile's file name when the full path does not match (unique in a region; otherwise the cell stays visible, never a hole). A region can be renamed by hand without regenerating the overview. `tests/v52_renom.py`.

### 25/10/2026 : serveur de présence, requêtes HTTP ordinaires sur le port
- **Serveur de présence** : avec `websockets` 14 et 15, une requête HTTP ordinaire sur le port du serveur (navigateur qui ouvre son adresse, robot, test) écrivait une trace complète (« opening handshake failed », `InvalidUpgrade`, « invalid Connection header: keep-alive ») alors que le client reçoit bien « 426 Upgrade Required ». Une ligne `requête http` la remplace : adresse, chemin, hôte, agent et raison, au plus une par minute et par adresse. Les requêtes mal formées et les autres erreurs restent affichées en entier. `tests/v52_http.py` (variables `WS_OLD`, `WS_OLD2`). **Relancer le serveur de présence.**
- **Presence server**: with `websockets` 14 and 15, an ordinary HTTP request on the server port (a browser opening its address, a robot, a test) wrote a full trace ("opening handshake failed", `InvalidUpgrade`, "invalid Connection header: keep-alive") although the client does get "426 Upgrade Required". An `http request` line replaces it: address, path, host, agent and reason, at most one per minute and per address. Malformed requests and other errors are still shown in full. `tests/v52_http.py` (variables `WS_OLD`, `WS_OLD2`). **Restart the presence server.**

### 25/10/2026 : repère visuel des arrivées, agrandissement des vignettes à 400 px
- **`carte.html`** : quand la surveillance est cochée, la tuile de la région où quelqu'un vient d'arriver est marquée : contour en pointillés qui clignote, fond jaune et le texte « ● arrivée hh:mm » (jamais la couleur seule ; sans clignotement si le système demande de réduire les animations). Le repère reste jusqu'au survol de la tuile ; décocher la case l'efface. La case devient « Surveillance des arrivées (son et repère) ». Agrandissement des vignettes porté de 320 à 400 px au plus (`carte.html` et carte ouverte par M). **Décompte des régions** (« 12 régions · Total : … ») au-dessus de la grille. **Français : visiteurs et promeneurs sur deux lignes** dans les tuiles (cle `map.sep` / `page.map.sep`, « \n » en français, « · » en anglais ; `white-space: pre-line`), le total reste sur une ligne.
- **`carte.html`**: when the alert is checked, the tile of the region where someone just arrived is marked: dashed outline that blinks, yellow background and the text "● arrival hh:mm" (never colour alone; no blinking if the system asks for reduced motion). The marker stays until the tile is hovered; unchecking the box clears it. The checkbox becomes "Arrival alert (sound and marker)". Thumbnail enlargement raised from 320 to 400 px at most (`carte.html` and the map opened with M). **Region count** ("12 regions · Total: …") above the grid. **French: visitors and walkers on two lines** in the tiles (key `map.sep` / `page.map.sep`, line break in French, " · " in English; `white-space: pre-line`), the total stays on one line.

### 25/10/2026 : carte.html (total, surveillance sonore, agrandissement), « promeneur », case « Afficher la mer »
- **`carte.html` et carte autonome `--map-page`** : ligne « Total : N visiteurs · N promeneurs » au-dessus de la grille (chaque salon compté une fois ; avec un ancien serveur sans `visitors`, promeneurs seulement) ; case « Surveillance sonore » (mémorisée, clé `glb2html_map_alert`) : une hausse du nombre de visiteurs d'un salon de la carte entre deux relevés joue les deux notes montantes de l'arrivée d'un promeneur et note « dernière arrivée : région, hh:mm » ; le premier relevé d'un serveur ne sonne jamais ; le son démarre au premier clic dans la page (règle du navigateur, dite en texte). Délais d'interrogation en tête du script de la page : `POLL_MS` (10 000 ms) et `POLL_ALERT_MS` (5 000 ms, surveillance cochée). Agrandissement de la vignette au survol (souris seulement, 320 px au plus), aussi dans la carte ouverte par M.
- **Texte** : « 1 promeneur », « N promeneurs » à la place de « en promenade » (français) ; « walker » / « walkers » à la place de « walking » (anglais) ; `tests/v47.py` adapté.
- **Réglages de la page** : case « Afficher la mer » avant « Mer animée » (seulement si la page a une mer) ; mer masquée : « Mer animée » et « Vagues » grisés ; choix retenu avec les autres réglages (`glb2html_opts_SALON`), « Valeurs d'origine » la remet. Une page faite avec `--no-sea` ignore un ancien choix retenu.
- **`carte.html` and `--map-page`**: a line "Total: N visitors · N walkers" above the grid (each room counted once; with an old server without `visitors`, walkers only); "Sound alert" checkbox (remembered, key `glb2html_map_alert`): a rise in a map room's visitor count between two polls plays the two rising notes of a walker arrival and notes "last arrival: region, hh:mm"; a server's first poll never sounds; sound starts at the first click on the page (browser rule, stated in text). Polling delays at the top of the page script: `POLL_MS` (10,000 ms) and `POLL_ALERT_MS` (5,000 ms, alert checked). Thumbnail enlarged on hover (mouse only, 320 px at most), also in the map opened with M.
- **Text**: "1 promeneur" / "N promeneurs" instead of "en promenade" (French); "walker" / "walkers" instead of "walking" (English); `tests/v47.py` adapted.
- **Page settings**: "Show the sea" checkbox before "Animated sea" (only if the page has a sea); sea hidden: "Animated sea" and "Waves" greyed out; choice kept with the other settings (`glb2html_opts_ROOM`), "Default values" restores it. A page made with `--no-sea` ignores an old remembered choice.

## v51 (25/10/2026)
### 25/10/2026 : adresse de présence « même nom que la page »
- **Page, fenêtre Carte, `carte.html`, journal des visites, viewer** : une adresse de présence peut s'écrire `ws://*:PORT` ; l'étoile est remplacée par le nom avec lequel la page a été ouverte (`presUrl` dans `core.js`, `template.html` et la page de carte de `gen_tpl.py` ; disque et viewer : `127.0.0.1` ; `ws://0.0.0.0` toujours corrigé). Corrige les connexions vides et les compteurs absents quand `carte.html` ouverte par un nom public visait une adresse du réseau local. Message d'erreur de présence avec l'adresse résolue. Aide de `--presence-url` et message de démarrage du serveur (`py.presence.star_hint`), `REFERENCE_OPTIONS.md`. Manuel § 34.10 (FR, EN), procédures § 6 point 4, historique, `tests/v51_etoile.py`.
- **Page, Map window, `carte.html`, visit log, viewer**: a presence address can be written `ws://*:PORT`; the star is replaced with the name the page was opened with (`presUrl` in `core.js`, `template.html` and the map page of `gen_tpl.py`; disk and viewer: `127.0.0.1`; `ws://0.0.0.0` still corrected). Fixes the empty connections and missing counters when `carte.html` opened through a public name targeted a local network address. Presence error message with the resolved address. `--presence-url` help and server start-up message (`py.presence.star_hint`), `REFERENCE_OPTIONS.md`. Manual § 34.10 (FR, EN), procedures § 6 item 4, history, `tests/v51_etoile.py`.

### 25/10/2026 : connexions vides du serveur de présence
- **Serveur de présence** : avec `websockets` 14 et 15, chaque connexion TCP fermée sans requête (préconnexion d'un navigateur, test de port, robot) écrivait une trace complète « opening handshake failed » (EOFError) dans la console. Un filtre sur le journal `websockets.server` la remplace par une ligne « vide » (console et `presence.log`) avec l'adresse de l'appelant, masquée selon `--log-ip`, au plus une par minute et par adresse ; les autres erreurs restent affichées. Livré d'abord en v52, rattaché à la v51 le 25/10/2026 (étiquette `v52` supprimée). Manuel § 34.9 (FR, EN), historique, README, `tests/v51_vides.py` (variable `WS_OLD` pour une ancienne version de `websockets`).
- **Presence server**: with `websockets` 14 and 15, each TCP connection closed without a request (browser preconnection, port test, robot) wrote a full "opening handshake failed" trace (EOFError) to the console. A filter on the `websockets.server` log replaces it with an "empty" line (console and `presence.log`) with the caller's address, masked according to `--log-ip`, at most one per minute and per address; other errors are still shown. First delivered as v52, attached to v51 on 25/10/2026 (`v52` tag removed). Manual § 34.9 (FR, EN), history, README, `tests/v51_vides.py` (`WS_OLD` variable for an old `websockets` version).

### 25/10/2026 : documents des créateurs
- **Manuel** (FR et EN) : § 34 (créateurs sur le serveur de présence : fichier, origine, préfixe, limites, ce que voit le visiteur, console, limites de la méthode), § 27.1 et § 27.10 (`presence_creators.json` champ par champ), titre et résumé (v51). **Procédures** § 6, point 7 : accueillir un créateur. **Historique** et **README** (FR et EN) : v51, commande `creators`, `presence_creators.json` à ne jamais committer.
- **Manual** (FR and EN): § 34 (creators on the presence server: file, origin, prefix, limits, what the visitor sees, console, limits of the method), § 27.1 and § 27.10 (`presence_creators.json` field by field), title and summary (v51). **Procedures** § 6, item 7: welcoming a creator. **History** and **README** (FR and EN): v51, `creators` command, `presence_creators.json` never to be committed.

### 25/10/2026 : créateurs sur le serveur de présence
- **Serveur de présence** : option `--creators FICHIER` (`presence_creators.json`, relu à chaud, sans relancer le serveur). Chaque créateur déclare les origines de ses pages, un préfixe de salon (`alice.` ; l'hôte n'en a pas et garde tous les autres salons), `maxWalkers`, `maxRooms`, `off`. Une page d'une origine non déclarée, d'un créateur suspendu, un salon hors du préfixe ou un salon de trop sont refusés (message `refused`, code 4003, ligne « refus » au journal) ; promeneurs au plus par créateur à l'arrivée et au passage en promenade. Commande de console `creators`. Sans `--creators`, rien ne change. Correction : un refus (bannissement, salon complet) ne laisse plus de salon vide. **Page et viewer** : le refus est affiché avec sa raison, sans nouvelle tentative. `.gitignore` : `presence_creators.json`. Exemple `docs/samples/presence_creators.sample.json`, `tests/v51.py`, `tests/samples.py`.
- **Presence server**: `--creators FILE` option (`presence_creators.json`, re-read on change, no server restart). Each creator declares the origins of their pages, a room prefix (`alice.`; the host has none and keeps all other rooms), `maxWalkers`, `maxRooms`, `off`. A page from an undeclared origin, from a suspended creator, a room outside the prefix or one room too many are refused (`refused` message, code 4003, "refusal" log line); walkers at most per creator on arrival and when switching to walking. Console command `creators`. Without `--creators`, nothing changes. Fix: a refusal (ban, full room) no longer leaves an empty room. **Page and viewer**: the refusal is shown with its reason, without retrying. `.gitignore`: `presence_creators.json`. Sample `docs/samples/presence_creators.sample.json`, `tests/v51.py`, `tests/samples.py`.

## v50 (25/10/2026)
### 25/10/2026 : textes et documents à jour
- **README** (FR et EN, même plan) : à jour jusqu'à la v50 (fichiers `index.html` et `carte.html`, organisation d'un site, `--scan-sites`, carte des mondes, résumé de la page, tableau des touches complet avec K, L, O, serveur de présence, tests) au lieu des nouveautés v33 à v37. **Manuel** (FR et EN) : titre et résumé (v50), touche K au § 2. **Procédures** (FR et EN) : § 4 (patch, copie de `index.html` et `carte.html` dans `Sites\`, `--update` avec la coquille de la racine, serveur relancé à chaque version), § 7 (carte par `--scan-sites` et `carte.html`), § 8. **Serveur de présence** : le message de démarrage cite `rooms` et `visits-key`. **`CLAUDE.md`** : renvoie à `REPRISE.md` et aux règles de travail, feuille de route et liste des tests périmées retirées (`git show v49:CLAUDE.md`). **`.gitignore`** : `presence_visits_keys.json` exclu.
- **README** (FR and EN, same outline): up to date to v50 (`index.html` and `carte.html` files, site layout, `--scan-sites`, world map, page summary, full key table with K, L, O, presence server, tests) instead of the v33 to v37 news. **Manual** (FR and EN): title and summary (v50), K key in § 2. **Procedures** (FR and EN): § 4 (patch, copy of `index.html` and `carte.html` into `Sites\`, `--update` with the root shell, server restarted at each version), § 7 (map through `--scan-sites` and `carte.html`), § 8. **Presence server**: the start-up message lists `rooms` and `visits-key`. **`CLAUDE.md`**: points to `REPRISE.md` and the working rules, outdated roadmap and test list removed (`git show v49:CLAUDE.md`). **`.gitignore`**: `presence_visits_keys.json` excluded.

### 25/10/2026 : carte des mondes du viewer (import, export, ajout)
- **Viewer, section Carte des mondes** : « Importer regions.json » accepte la forme objet avec en-tête (v47, celle que crée `--scan-sites`) au lieu de répondre « tableau attendu » ; « Exporter regions.json » rend la forme importée avec son en-tête (retenu par le navigateur) ; chaque fiche garde tous ses champs (`presence` était perdu) ; « Ajouter / mettre à jour cette région » met à jour sur place la fiche du même salon sans effacer un champ par un vide, comme `--register`. `tests/v50.py`, manuel § 27.6 et § 33.
- **Viewer, World map section**: "Import regions.json" accepts the object shape with a header (v47, the one `--scan-sites` creates) instead of answering "array expected"; "Export regions.json" gives back the imported shape with its header (remembered by the browser); every card keeps all its fields (`presence` was lost); "Add / update this region" updates the card of the same room in place without erasing a field with an empty one, like `--register`. `tests/v50.py`, manual § 27.6 and § 33.

## v49 (25/10/2026)
### 25/10/2026 : documents de la v49
- **Manuel § 32** (FR et EN) : `--scan-sites`, vignettes (320 x 320 conseillé), `REPRISE.md` (créateurs sur le serveur de Klaatou : conception notée, à faire).
- **Manual § 32** (FR and EN): `--scan-sites`, thumbnails (320 x 320 recommended), `REPRISE.md` (creators on Klaatou's server: design noted, to do).

### 25/10/2026 : mise à jour de regions.json depuis le dossier des sites
- **`glb2html.py --scan-sites DOSSIER`** (et `--dry-run`) : une fiche par `NOM.config.json` (adresse `index.html?region=dossier/NOM`, salon, serveur), vignette `NOM.jpg`, `.png` ou `.webp` à côté ; fiche reconnue par son salon puis son adresse ; nom, place, arrivée, en-tête et fiches externes gardés ; nouvelle région sur une case libre ; rien n'est supprimé (orphelines signalées). `tests/v49.py`, `REFERENCE_OPTIONS.md`.
- **`glb2html.py --scan-sites FOLDER`** (and `--dry-run`): one card per `NOM.config.json` (address `index.html?region=folder/NAME`, room, server), thumbnail `NAME.jpg`, `.png` or `.webp` next to it; card recognised by its room then its address; name, place, arrival, header and external cards kept; new region on a free cell; nothing is deleted (orphans reported). `tests/v49.py`, `REFERENCE_OPTIONS.md`.

## v48 (25/10/2026)
### 25/10/2026 : bouton « Journal des visites… »
- **Page** : bouton « Journal des visites… » dans la fenêtre Informations (I), à côté de « Copier le diagnostic », seulement si la page a un serveur de présence ; il ouvre la même fenêtre que `#visits` (fermée puis rouverte, le résumé reste). `tests/v48.py`, manuel § 31.3.
- **Page**: "Visit log…" button in the Information window (I), next to "Copy diagnostics", only when the page has a presence server; it opens the same window as `#visits` (closed then reopened, the summary stays). `tests/v48.py`, manual § 31.3.

### 25/10/2026 : commande rooms
- **Console du serveur de présence** : `rooms` (alias `salons`) liste les salons connus avec leur casse exacte : connectés (dont promeneurs), visites (reconnexions fusionnées) et date de la dernière, clé ou non. `tests/v48.py`, manuel § 31.2, procédures § 6.
- **Presence server console**: `rooms` (alias `salons`) lists the known rooms with their exact case: connected (walkers among them), visits (reconnections merged) and date of the last one, key or not. `tests/v48.py`, manual § 31.2, procedures § 6.

### 25/10/2026 : visits-key et la casse du salon
- **`visits-key ROOM`** : la casse du nom du salon compte partout dans le serveur ; si le nom tapé n'existe qu'avec une autre casse (salons connectés et fichier des visites), la console le signale (la clé est quand même créée). `tests/v48.py`, manuel § 31.2.
- **`visits-key ROOM`**: case matters in the room name throughout the server; if the typed name only exists with a different case (connected rooms and visit file), the console says so (the key is still created). `tests/v48.py`, manual § 31.2.

### 25/10/2026 : documents de la v48
- **Manuel § 31** (FR et EN) : journal des visites, côté hôte et côté créateur, ce qui est compté, données personnelles ; § 27.1 et § 27.10 (fichier des visites, `presence_visits_keys.json`) ; procédures § 6 ; exemples `docs/samples/visits.sample.jsonl` et `docs/samples/presence_visits_keys.sample.json` (lus par `tests/samples.py`) ; `REFERENCE_OPTIONS.md` régénéré ; historique (la ligne v47 était sous « Commandes utiles » : remise dans le tableau) ; `REPRISE.md`.
- **Manual § 31** (FR and EN): visit log, host side and creator side, what is counted, personal data; § 27.1 and § 27.10 (visit file, `presence_visits_keys.json`); procedures § 6; samples `docs/samples/visits.sample.jsonl` and `docs/samples/presence_visits_keys.sample.json` (read by `tests/samples.py`); `REFERENCE_OPTIONS.md` regenerated; history (the v47 line was under "Useful commands": moved back into the table); `REPRISE.md`.

### 25/10/2026 : journal des visites (code)
- **Serveur de présence** : `--visits FICHIER` note chaque visite à sa fin, une ligne JSON (`room`, `start`, `dur`, `walk`, `v` empreinte du navigateur ; `name` seulement avec `--visits-names`), jamais d'adresse IP ; `--visits-days N` (365, 0 = tout garder) purge au démarrage et toutes les 6 h ; arrêt propre : les visites en cours sont écrites. Commande de console `visits-key ROOM` (clé affichée une seule fois, seule son empreinte gardée dans `--visits-keys`, par défaut `presence_visits_keys.json`), `visits-key ROOM off`, `visits-key` seul. Message `visits` (avant `hello`) : résumé par jour et visites des 30 derniers jours, reconnexions de moins de 2 min fusionnées, 5 clés refusées par minute et par IP au plus. `presence.log` inchangé.
- **Page** : l'adresse suivie de `#visits` ouvre la fenêtre « Journal des visites » (clé, Afficher, Oublier la clé, Télécharger (CSV), Fermer (Échap)) ; clé acceptée retenue par le navigateur ; messages clé refusée, trop d'essais, serveur sans `--visits`, serveur trop ancien, serveur absent, page sans présence. Textes dans `src/i18n`. `tests/v48.py`.
- **Presence server**: `--visits FILE` records each visit when it ends, one JSON line (`room`, `start`, `dur`, `walk`, `v` browser fingerprint; `name` only with `--visits-names`), never an IP address; `--visits-days N` (365, 0 = keep everything) purges at startup and every 6 h; clean stop: visits in progress are written. Console command `visits-key ROOM` (key shown only once, only its fingerprint kept in `--visits-keys`, `presence_visits_keys.json` by default), `visits-key ROOM off`, `visits-key` alone. `visits` message (before `hello`): summary per day and visits of the last 30 days, reconnections within 2 min merged, at most 5 refused keys per minute and per IP. `presence.log` unchanged.
- **Page**: the address followed by `#visits` opens the "Visit log" window (key, Show, Forget the key, Download (CSV), Close (Esc)); accepted key kept by the browser; messages key refused, too many attempts, server without `--visits`, server too old, missing server, page without presence. Texts in `src/i18n`. `tests/v48.py`.

## v47 (25/10/2026)
### 25/10/2026 : documents de la v47
- **Manuel § 30** (FR et EN) : tuile de la carte, adresse facultative, `regions.json` avec en-tête (§ 27.6), deux façons de faire la carte, serveur de présence ; procédures § 4 ; exemple `docs/samples/regions.sample.json` en forme objet ; `REPRISE.md`.
- **Manual § 30** (FR and EN): map tile, optional address, `regions.json` with a header (§ 27.6), two ways to make the map, presence server; procedures § 4; sample `docs/samples/regions.sample.json` in object form; `REPRISE.md`.

### 25/10/2026 : carte des mondes (visiteurs, adresse facultative, carte.html universelle)
- **Tuile** (page carte et carte ouverte par M) : « N visiteurs · N en promenade » ou « aucun visiteur » à la place de « visiter → », bulle au survol. **Adresse** masquée par défaut : `showUrl` dans l'en-tête de `regions.json` et case « Afficher les adresses » (choix du visiteur mémorisé, prioritaire). **`regions.json`** en liste ou en objet `{"showUrl", "regions"}` ; `--register` garde l'en-tête et la forme (il effaçait un fichier qui n'était pas une liste). **Serveur** : `rooms` reçoit `visitors` par salon. **`build.py`** écrit `dist/carte.html`, la page de carte universelle (lit `regions.json` à côté d'elle ; messages distincts si le fichier manque ou si elle est ouverte depuis le disque). `tests/v47.py` ; `tests/v36_lang.py`, `tests/modulaire.py`, `tests/samples.py` adaptés.
- **Map tile** (map page and map opened with M): "N visitors · N walking" or "no visitors" instead of "visit →", tooltip on hover. **Address** hidden by default: `showUrl` in the `regions.json` header and an "Show addresses" checkbox (visitor's choice kept, takes priority). **`regions.json`** as a list or an object `{"showUrl", "regions"}`; `--register` keeps the header and the shape (it used to wipe a file that was not a list). **Server**: `rooms` gets `visitors` per room. **`build.py`** writes `dist/carte.html`, the universal map page (reads the `regions.json` next to it; distinct messages when the file is missing or when it is opened from disk). `tests/v47.py`; `tests/v36_lang.py`, `tests/modulaire.py`, `tests/samples.py` adapted.

## v46 (25/10/2026)
### 25/10/2026 : documents de la v46
- **Manuel § 29** (FR et EN) : ligne d'état, flèches (promenade et vue globale, déplacer et rapprocher), K, écran tactile, bulles, compteur du chat (remise à zéro à l'ouverture, comportement voulu), diagnostic, une coquille pour tout un site (`--update -o … --shared-shell CHEMIN_DE_LA_COQUILLE`). Tableau des touches (§ 20.2), procédures §§ 4 et 10, historique.
- **Manual § 29** (FR and EN): status line, arrows (walking and overview, move and zoom), K, touch screen, tooltips, chat counter (reset when opened, intended behaviour), diagnostics, one shell for a whole site (`--update -o … --shared-shell SHELL_PATH`). Key table (§ 20.2), procedures §§ 4 and 10, history.

### 25/10/2026 : pas de côté sur le pavé de promenade
- **Flèches de promenade** : pas de côté à gauche et à droite (Q et D en AZERTY, A et D en QWERTY) au milieu du pavé ; tourner passe aux coins du haut, monter et descendre (en vol) aux coins du bas, comme le pavé de la vue globale. `tests/v46.py` complété.
- **Walking arrows**: step left and right (Q and D on AZERTY, A and D on QWERTY) in the middle of the pad; turning moves to the top corners, up and down (while flying) to the bottom corners, like the overview pad. `tests/v46.py` extended.

### 25/10/2026 : commandes à l'écran (code)
- **Ligne d'état** toujours visible (en bas au centre ; en haut sous la boussole sur un écran étroit ou tactile) : mode en toutes lettres (Promenade, Vue globale), allure, vue, position ou cible.
- **Flèches à l'écran** (pavé 3 x 3) : en promenade avancer, reculer, tourner, Courir (un clic l'allume, un clic l'éteint), et en vol monter, descendre ; en vue globale déplacer, tourner, rapprocher, éloigner, et Recentrer au centre (le bouton « Recentrer la vue » ne revient que si les flèches sont cachées). Appui maintenu = touche tenue. Escamotables : touche K, bouton « Flèches (K) », case de Réglages (retenu par le navigateur).
- **Mode tactile** (écran tactile détecté, ou réglage « Commandes tactiles » Auto / Oui / Non) : colonne de boutons (Promenade ou Sortir, Sauter, Voler, Vue, Chat, Flèches, Menu), menu (Aide, Informations, Arrivées, Carte, Retour à l'arrivée, Recentrer, Plein écran si le navigateur le permet), fenêtres réduites à l'ouverture avec un ✕, glisser du doigt pour regarder en promenade, vrai champ de chat avec Envoyer et Fermer, bulle par appui long ; écran tourné à l'horizontale pris en charge. « Capturer la souris » caché.
- **Bulles** sur tous les boutons de la barre et les flèches ; aide : K ; diagnostic : ligne « Commandes tactiles ».
- **Correction** : la hauteur de l'aide se règle sur la hauteur mesurée du reste de la colonne de gauche (le titre sortait de l'écran quand la barre passait sur plus de rangées).
- `src/core.js` : `lookBy` (souris et doigt), `padKey`, `padJump`, `runLatch`, `globalMove`, `globalTurn`, `globalZoom`. `tests/v46.py` ; `tests/v34.py` et `tests/v40.py` adaptés.
- **Status line** always visible (bottom centre; top, under the compass, on a narrow or touch screen): mode spelled out (Walking, Overview), gait, view, position or target.
- **On-screen arrows** (3 x 3 pad): while walking forward, back, turn, Run (one click on, one click off), and while flying up, down; in the overview move, turn, zoom in, zoom out, and Recenter in the middle (the "Recenter the view" button only comes back when the arrows are hidden). Press and hold = key held. Can be hidden: K key, "Arrows (K)" button, Settings checkbox (remembered by the browser).
- **Touch mode** (touch screen detected, or "Touch controls" setting Auto / Yes / No): column of buttons (Walk or Exit, Jump, Fly, View, Chat, Arrows, Menu), menu (Help, Information, Arrivals, Map, Back to arrival, Recenter, Full screen when the browser allows it), windows folded on opening with a ✕, drag a finger to look around while walking, real chat field with Send and Close, tooltip on long press; landscape orientation supported. "Capture the mouse" hidden.
- **Tooltips** on all bar buttons and arrows; help: K; diagnostics: "Touch controls" line.
- **Fix**: the help height follows the measured height of the rest of the left column (its title went off screen when the bar wrapped onto more rows).
- `src/core.js`: `lookBy` (mouse and finger), `padKey`, `padJump`, `runLatch`, `globalMove`, `globalTurn`, `globalZoom`. `tests/v46.py`; `tests/v34.py` and `tests/v40.py` adapted.

## v45 (24/10/2026)
### 24/10/2026 : la page dit pourquoi la connexion de présence s'est fermée
- **Présence** : la ligne de présence (page et viewer) donne la cause au lieu de toujours « serveur injoignable » : connexion jamais établie, ouverte puis fermée (code et raison du serveur), ou refusée par le navigateur (`SecurityError`). Le navigateur ne donne jamais la cause d'une connexion qui ne s'ouvre pas (code 1006) : la page ne distingue donc pas un nom introuvable, un port fermé ou un blocage.
- **Diagnostic** : nouvelle ligne « Connexion de présence » (s'est ouverte, dernier code, dernière raison). `getPresence()` expose `opened`, `closeCode`, `closeReason`. `tests/v45.py`, manuel § 28.
- **Presence**: the presence line (page and viewer) gives the cause instead of always "server unreachable": connection never established, opened then closed (server code and reason), or refused by the browser (`SecurityError`). The browser never gives the cause of a connection that does not open (code 1006): the page cannot tell an unknown name, a closed port or a block apart.
- **Diagnostics**: new "Presence connection" line (was opened, last code, last reason). `getPresence()` exposes `opened`, `closeCode`, `closeReason`. `tests/v45.py`, manual § 28.

### 24/10/2026 : procédures § 11 complétées
- **Procédures § 11** (français et anglais) : Tailscale Funnel essayé le 24/10/2026 (WebSocket en 101, vraie IP avec `--proxy-header X-Forwarded-For`, visiteur extérieur connecté) ; règle « la présence au même endroit que la page » (blocage sur les appareils où Tailscale est actif quand la page vient d'une autre adresse) ; avertissement : `tailscale funnel` prend la racine du port et remplace ce que `tailscale serve` y publiait ; nouvelle voie D « VM Linux + Tailscale Funnel + Apache » (Apache sur `127.0.0.1` avec `mod_remoteip`, présence en service système, funnel `/` et `/presence`, essayée sauf Tailscale et le démarrage par systemd) ; cas « un autre service est déjà publié » (port 8443, commandes non essayées).
- **Procedures § 11** (French and English): Tailscale Funnel tried on 24/10/2026 (WebSocket 101, real IP with `--proxy-header X-Forwarded-For`, outside visitor connected); rule "the presence in the same place as the page" (blocked on devices where Tailscale is active when the page comes from another address); warning: `tailscale funnel` takes the root of the port and replaces what `tailscale serve` was publishing there; new way D "Linux VM + Tailscale Funnel + Apache" (Apache on `127.0.0.1` with `mod_remoteip`, presence as a system service, funnel `/` and `/presence`, tried except Tailscale and the start by systemd); case "another service is already published" (port 8443, commands not tried).
- **Documents** : `REPRISE.md` remis à jour (demandes du 24/10/2026 au § 6) ; lignes v45 de l'historique (français et anglais).
- **Documents**: `REPRISE.md` updated (requests of 24/10/2026 in § 6); v45 lines of the history (French and English).

### 24/10/2026 : le dossier `lib` de la coquille se règle par une seule ligne
- **Coquille** : elle commence par `const LIB = './lib';`, seule ligne à modifier pour mettre `lib` ailleurs ; la table d'import de three.js et le chemin Draco sont construits à partir de cette ligne par un script classique, avant tout module (`SHELL_IMPORTMAP_NEW` dans `src/gen_tpl.py`). La page autonome ne change pas.
- **`--update`** garde la ligne modifiée à la main : ordre `--lib-url` donné, ligne `const LIB` de la coquille si elle n'est pas `./lib`, `libUrl` de la config, `./lib` (`lib_from_shell`, `effective_lib_url`) ; `libUrl` est aligné, message `[update]` ; une nouvelle région créée dans un tel dossier garde le même `lib` ; les fins de ligne CRLF sont reconnues identiques (`same_shell`).
- **`build.py`** écrit `dist/index.html` : la coquille prête, identique octet pour octet à celle de `glb2html.py`, à copier à la place de `--update`.
- **Documents et tests** : manuel § 28 (et § 22.8, § 27), procédures § 4, `REFERENCE_OPTIONS.md` régénéré, `tests/v45_lib.py`, `tests/essai_importmap.html` (Firefox et Safari : non essayés ici), `tests/v37_region.py` suivi.
- **Shell**: it starts with `const LIB = './lib';`, the only line to edit to put `lib` elsewhere; the three.js import map and the Draco path are built from that line by a classic script, before any module (`SHELL_IMPORTMAP_NEW` in `src/gen_tpl.py`). The standalone page does not change.
- **`--update`** keeps the line edited by hand: order `--lib-url` given, `const LIB` line of the shell if it is not `./lib`, `libUrl` of the config, `./lib` (`lib_from_shell`, `effective_lib_url`); `libUrl` is aligned, `[update]` message; a new region created in such a folder keeps the same `lib`; CRLF line endings are recognised as identical (`same_shell`).
- **`build.py`** writes `dist/index.html`: the ready-made shell, byte for byte the same as `glb2html.py`'s, to copy instead of `--update`.
- **Documents and tests**: manual § 28 (and § 22.8, § 27), procedures § 4, `REFERENCE_OPTIONS.md` regenerated, `tests/v45_lib.py`, `tests/essai_importmap.html` (Firefox and Safari: not tried here), `tests/v37_region.py` followed.

## v44 (24/10/2026)
### 24/10/2026 : derniers noms en anglais, historique complété
- **Noms en anglais (suite de la v43)** : `gen_reference.py` `--tools`, `--output`, `--check` (anciens `--outils`, `--sortie`, `--verifier` acceptés) ; `verif_trad.py` `--glossary` (ancien `--glossaire` accepté) ; messages de `--update` en français commencent par `[update]` (et non plus `[maj]`) ; noms d'exemple des textes d'aide alignés sur l'aide (`FILE`, `FOLDER`, `SHELL.html`, `NAME`) ; menu du viewer « Point (dot) » et « Portée (range) » en français, « Dot » en anglais ; `CLAUDE.md`, `README.fr.md` et les procédures citaient encore `discret` / `portee` : corrigés. Manuel § 27.11 complété.
- **Contrôle** : `tests/samples.py` cherche les anciens noms dans les textes d'aide et les messages (`src/i18n`), `REFERENCE_OPTIONS.md`, les README, `CLAUDE.md`, le manuel et les procédures ; un ancien nom n'y est permis que présenté comme ancien.
- **Historique** : `docs/fr/HISTORIQUE.md` et `docs/en/HISTORY.md` complétés de la v38 à la v44.
- **English names (continuation of v43)**: `gen_reference.py` `--tools`, `--output`, `--check` (old `--outils`, `--sortie`, `--verifier` accepted); `verif_trad.py` `--glossary` (old `--glossaire` accepted); French `--update` messages start with `[update]` (no longer `[maj]`); example names in the help texts aligned with the help (`FILE`, `FOLDER`, `SHELL.html`, `NAME`); viewer menu "Point (dot)" and "Portée (range)" in French, "Dot" in English; `CLAUDE.md`, `README.fr.md` and the procedures still cited `discret` / `portee`: fixed. Manual § 27.11 completed.
- **Check**: `tests/samples.py` looks for the old names in the help texts and messages (`src/i18n`), `REFERENCE_OPTIONS.md`, the READMEs, `CLAUDE.md`, the manual and the procedures; an old name is only allowed there when presented as old.
- **History**: `docs/fr/HISTORIQUE.md` and `docs/en/HISTORY.md` completed from v38 to v44.

## v43 (24/10/2026)
### 24/10/2026 : référence des fichiers JSON, fichiers d'exemple, noms en anglais
- **Fichiers JSON** : manuel § 27 « Référence des fichiers JSON » (français et anglais) : chaque fichier (`NOM.config.json`, `NOM.zones.json`, `default.json`, `regions.json`, `NOM.tiles.json`, `NOM.reglages.json`, `disposition.json`, `presence_identities.json`, `presence_bans.json`, historique du chat), chaque champ avec son type, sa valeur par défaut, son rôle et l'option qui le règle ; le § 16 y renvoie. Dossier `docs/samples/` : un exemple complet et valide de chaque fichier (zones : deux arrivées, portail dans la région, portail vers une autre région, lien, commande privée, zone liée à un objet, nom affiché). `tests/samples.py` vérifie que chaque exemple est accepté par le vrai code (outils, page, viewer, serveur de présence).
- **Noms en anglais** : options `--update` (`--maj`), `--tile-max-mb`, `--tile-max-triangles`, options de `glb2tiles.py` (`--threshold`, `--exclude`, `--no-overview`, `--overview-only`, `--output`...), de `oar2glb.py` (`--markers`, `--terrain-only`, `--terrain yes|no`) et de `glb-stats.py` (`--block`, `--output`) ; valeurs `zoneMarker` `dot`, `range`, `none` et profil `private` ; clés `tileMaxMB`, `tileMaxTriangles`, `budgetMB`, `wholeWeightMB`, `thresholdMB` ; adresses `?radius=` et `?tiles=` ; noms d'exemple de l'aide (`FILE`, `PATH`, `NAME`...). Les anciens noms restent acceptés (tableau au § 27.11). La valeur traduite « none » de `--zone-marker` en anglais n'était pas comprise par la page (repère discret affiché) : corrigé.
- **gen_reference.py** : `oar2glb.py` ne demande plus « Entrée pour fermer » (`--nopause`).
- **JSON files**: manual § 27 "JSON file reference" (French and English): each file (`NOM.config.json`, `NOM.zones.json`, `default.json`, `regions.json`, `NOM.tiles.json`, `NOM.reglages.json`, `disposition.json`, `presence_identities.json`, `presence_bans.json`, chat history), each field with its type, default value, role and the option that sets it; § 16 points to it. `docs/samples/` folder: a complete and valid sample of each file (zones: two arrivals, portal within the region, portal to another region, link, private command, zone linked to an object, name shown). `tests/samples.py` checks that each sample is accepted by the real code (tools, page, viewer, presence server).
- **English names**: options `--update` (`--maj`), `--tile-max-mb`, `--tile-max-triangles`, options of `glb2tiles.py` (`--threshold`, `--exclude`, `--no-overview`, `--overview-only`, `--output`...), of `oar2glb.py` (`--markers`, `--terrain-only`, `--terrain yes|no`) and of `glb-stats.py` (`--block`, `--output`); `zoneMarker` values `dot`, `range`, `none` and `private` profile; keys `tileMaxMB`, `tileMaxTriangles`, `budgetMB`, `wholeWeightMB`, `thresholdMB`; addresses `?radius=` and `?tiles=`; example names in the help (`FILE`, `PATH`, `NAME`...). The old names are still accepted (table in § 27.11). The translated value "none" of `--zone-marker` in English was not understood by the page (discreet marker shown): fixed.
- **gen_reference.py**: `oar2glb.py` no longer asks "Press Enter to close" (`--nopause`).

## v42 (24/10/2026)
### 24/10/2026 : rendu léger, fenêtre Réglages plus étroite
- **Rendu léger** : case « Rendu léger » dans Réglages (sous « Haute résolution ») et sous-fenêtre « Réglages fins… » à gauche de Réglages, réglages appliqués en direct et retenus par le navigateur : résolution du rendu (50 % préconisé), images par seconde au plus (15), vue d'ensemble seule en vue globale (aucune tuile détaillée hors promenade), rayon des tuiles détaillées (80 m), anticrénelage (non, au prochain chargement) ; bouton « Valeurs préconisées » ; « Valeurs d'origine » remet aussi le rendu léger. Rendu sans carte graphique détecté (Basic Render Driver, SwiftShader, llvmpipe) : la page propose le rendu léger une fois. Option `--light` / `--no-light` de `glb2html.py` (reprise par `--maj`), case et réglages dans le viewer. Diagnostic : réglages du rendu léger, images rendues par seconde sur 5 s et causes du rendu continu. Réglages : 420 px de large au plus, défilement au-delà de la hauteur de l'écran, note de couleur de l'avatar sur deux lignes, section « Disposition des fenêtres » mise en forme, note sur Échap tout en bas. Manuel § 26, `tests/v42.py`.
- **Light rendering**: "Light rendering" box in Settings (below "High resolution") and "Fine settings…" sub-window to the left of Settings, settings applied live and remembered by the browser: render resolution (50% recommended), frames per second at most (15), overview only in global view (no detailed tile outside walk mode), detailed tile radius (80 m), antialiasing (no, on next load); "Recommended values" button; "Default values" also resets light rendering. Rendering without a graphics card detected (Basic Render Driver, SwiftShader, llvmpipe): the page offers light rendering once. `--light` / `--no-light` option of `glb2html.py` (carried over by `--maj`), box and settings in the viewer. Diagnostics: light rendering settings, frames rendered per second over 5 s and causes of continuous rendering. Settings: at most 420 px wide, scrolls beyond the screen height, avatar color note on two lines, "Window layout" section laid out, Esc note at the very bottom. Manual § 26, `tests/v42.py`.

## v41 (24/10/2026)
### 24/10/2026 : bulles des fenêtres, fenêtres déplaçables, fichier de disposition
- **Fenêtres** : bulle sur les titres H, I, L et sur Réglages (rôle, touche, déplacement). Aide, Informations / État et Arrivées se glissent par le titre : pile de gauche (origine), pile de droite sous Réglages (poussée quand Réglages s'ouvre), ou libres ; double-clic sur le titre : retour à la dernière pile ; clic de souris sur le titre retardé de 250 ms (un double-clic ne replie pas) ; fenêtre libre gardée dans l'écran. Disposition retenue par le navigateur ; Réglages : enregistrer dans `disposition.json`, charger, disposition d'origine. Manuel § 25, `tests/v41.py` ; `tests/v35.py` et `tests/v36.py` attendent 300 ms après un clic de souris sur un titre.
- **Procédures** : § 11 « Rendre le serveur de présence public sans montrer son adresse IP » (Tailscale Funnel, Caddy, Cloudflare Tunnel ; `--host 127.0.0.1`, `--origins`, `--proxy-header`, contrôle en 4G), rédigé dans une session cloud, repris dans `docs/fr/PROCEDURES.md` et traduit dans `docs/en/PROCEDURES.md`. Non testé.
- **Windows**: tooltip on the H, I, L titles and on Settings (role, key, moving). Help, Information / Status and Arrivals are dragged by their title: left stack (original), right stack below Settings (pushed when Settings opens), or free; double-click on the title: back to the last stack; mouse click on the title delayed by 250 ms (a double-click does not collapse); free window kept on screen. Layout remembered by the browser; Settings: save to `disposition.json`, load, original layout. Manual § 25, `tests/v41.py`; `tests/v35.py` and `tests/v36.py` wait 300 ms after a mouse click on a title.
- **Procedures**: § 11 "Making the presence server public without showing your IP address" (Tailscale Funnel, Caddy, Cloudflare Tunnel; `--host 127.0.0.1`, `--origins`, `--proxy-header`, 4G check), written in a cloud session, brought into `docs/fr/PROCEDURES.md` and translated into `docs/en/PROCEDURES.md`. Not tested.

## v40 (24/10/2026)
### 24/10/2026 : fenêtre Arrivées, Recentrer la vue, lien Manuel, bulle du diagnostic
- **Arrivées** : fenêtre « Arrivées » (touche **L**, même cycle que H et I, bulle « Liste des points de téléportation disponibles (TP) ») sous la fenêtre Informations / État ; un clic sur un nom téléporte (promenade) ou entre en promenade (vue globale) ; absente sans arrivée. **Recentrer la vue** : bouton hors promenade, rend le cadrage d'ouverture. **Manuel** : lien « Manuel complet (en ligne) » vers GitHub dans l'aide de la page et dans le viewer, selon la langue. **Diagnostic** : bulle sur le bouton (page et viewer). Aide : L, bouton Recentrer, « R : centrer sur l'arrivée » en vue globale. Manuel § 24 et tableau des touches, `tests/v40.py`.
- **Arrivals**: "Arrivals" window (**L** key, same cycle as H and I, tooltip "List of available teleport points (TP)") below the Information / Status window; clicking a name teleports (walk mode) or enters walk mode (global view); absent without arrival points. **Recenter the view**: button outside walk mode, restores the opening framing. **Manual**: "Full manual (online)" link to GitHub in the page help and in the viewer, by language. **Diagnostics**: tooltip on the button (page and viewer). Help: L, Recenter button, "R: center on the arrival point" in global view. Manual § 24 and key table, `tests/v40.py`.

## v39 (23/10/2026)
### 23/10/2026 : bouton « Copier le diagnostic »
- **Diagnostic** : bouton « Copier le diagnostic » en bas de la fenêtre Informations / État de la page et en haut du panneau du viewer ; il copie la version, la date, la page (hôte masqué), la langue, le clavier, le navigateur, la fenêtre, la carte graphique, le rendu, la mémoire, les tuiles et leurs durées, les lignes d'état, la présence et les 10 dernières erreurs et avertissements (adresses remplacées par `ADRESSE`, partie `#` de l'adresse jamais copiée) ; copie refusée : texte affiché sélectionné. Code commun dans `src/core.js` (`DIAG`, `diagText`), textes `core.diag.*` en français et en anglais, manuel § 23, `tests/v39.py`.
- **Diagnostics**: "Copy diagnostics" button at the bottom of the page's Information / Status window and at the top of the viewer panel; it copies the version, date, page (host masked), language, keyboard, browser, window, graphics card, rendering, memory, tiles and their timings, status lines, presence and the last 10 errors and warnings (addresses replaced by `ADRESSE`, `#` part of the address never copied); copy refused: text shown selected. Shared code in `src/core.js` (`DIAG`, `diagText`), `core.diag.*` texts in French and English, manual § 23, `tests/v39.py`.

## v38 (23/10/2026)
### 23/10/2026 : traductions
- **Traductions** : `verif_trad.py` compare un document français et sa traduction (titres, tableaux, listes, code, liens, glossaire de l'interface) ; code de sortie 1 en cas d'erreur. `docs/en/PROCEDURES.md` et `docs/en/HISTORY.md` : traductions de `PROCEDURES.md` et `HISTORIQUE.md`, contrôlées par ce script.
- **Translations**: `verif_trad.py` compares a French document with its translation (headings, tables, lists, code, links, UI glossary); exit code 1 on error. `docs/en/PROCEDURES.md` and `docs/en/HISTORY.md`: translations of `PROCEDURES.md` and `HISTORIQUE.md`, checked by this script.
- **Manuel** : `docs/en/MANUAL.md`, traduction de `MODE_EMPLOI.md` (1 066 lignes), contrôlée par `verif_trad.py` ; détection du français dans le code affinée (mots propres au français, espace avant le deux-points, virgule décimale).
- **Manual**: `docs/en/MANUAL.md`, translation of `MODE_EMPLOI.md` (1,066 lines), checked by `verif_trad.py`; finer detection of French in code (French-only words, space before the colon, decimal comma).
- **Documents** : `MODE_EMPLOI.md` devient `docs/fr/MANUEL.md`, `PROCEDURES.md` et `HISTORIQUE.md` passent dans `docs/fr/` ; `README.md` est désormais en anglais (page d'accueil GitHub), `README.fr.md` en français, avec une ligne `English | Français` ; renvois mis à jour (documents, commentaires du code, `CLAUDE.md`) ; `verif_trad.py` tient `MANUAL.md` pour équivalent de `MANUEL.md`.
- **Documents**: `MODE_EMPLOI.md` becomes `docs/fr/MANUEL.md`, `PROCEDURES.md` and `HISTORIQUE.md` move to `docs/fr/`; `README.md` is now in English (GitHub home page), `README.fr.md` in French, with an `English | Français` line; references updated (documents, code comments, `CLAUDE.md`); `verif_trad.py` treats `MANUAL.md` as equivalent to `MANUEL.md`.

## v37 (23/10/2026)
### Lot 1 : corrections et ajouts de la page
- **Course** : la ligne « Mode » affiche « à pied · course » / « en vol · course » tant que la course est active.
- **Cône de portail** : taille apparente constante (échelle = distance / 12 entre 1 et 12, pointe immobile), visible jusqu'à `zoneInfoDist` (**150 m par défaut**, plage 5 à 500), infobulle avec la distance (« Portail → château · 120 m »).
- **Arrivée occupée** : le point libre le plus proche de l'occupant (anneaux 1,5 / 2,0 / 3,0 m autour de lui, 16 candidats), l'arrivant est tourné vers l'occupant, ligne console « arrivée occupée : décalé de X m (anneau R m) ».
- **Pseudo cité** : étiquette du nom de l'auteur, bulle et ligne du chat clignotent (0,5 s / 0,5 s) **sans limite de durée**, jusqu'à ma première action (touche, clic, mouvement, envoi). Remplace les 6 x 300 ms de la v33.
- **Hash** : `&` ou `#` séparent les paramètres (`hashParams`, une fonction pour la page, la coquille et la page carte).
- **Boussole** : cap en haut au centre (« NE 45° »), nord d'OpenSim = -Z, `rotate` pris en compte, case dans les Réglages visiteur ; `--compass` / `--no-compass`, `--north DEGRES` (config `compass`, `northDeg`).
- **`--help`** des quatre outils : première ligne « NOM vNN (jj/mm/aaaa) : fonction ».
- **Fenêtres Aide et Informations** : largeur réglable (bord droit, 260 px à 70 %), mémorisée, hauteur qui suit le contenu, empilées et collées.
- **Touche O** : ouvre / ferme la fenêtre Réglages (demande de Klaatou en cours de session ; R est déjà pris).
### Lot 2 : historique du chat
- Serveur : `--history` 200 par défaut, `--history-file`, `--history-days` (30 ; 0 = tout), message `history` (`before`, `n`, réponse `msgs`, `more`), numéros `n` et heures `t` sur les messages (anciens clients inchangés).
- Page : panneau défilable, réglage « Messages d'historique affichés » (200, 20 à 2000), bouton « Messages plus anciens », non lus dans le titre de l'onglet, « N messages vous citent ».
### Lot 3 : région par défaut, dossier lib, sous-dossiers
- Sans `?region=` : `X.config.json` de la page, puis `default.json`, puis `regions.json` (première adresse relative valide), sinon un message. `glb2html.py` écrit `default.json` la première fois ; `--default` ; `--maj` ne l'écrase pas sans `--default`.
- `--lib-url CHEMIN` (relatif ou `http(s)`), inscrit dans la table d'import de la coquille et retenu dans la config (`libUrl`) pour `--maj`.
- `?region=a/b/nom` (sous-dossiers) ; `--shared-shell DOSSIER/index.html` accepte un chemin ; les chemins de la config sont relatifs au dossier de la région.
- Tests : `tests/v37.py`, `tests/v37_chat.py`, `tests/v37_region.py`, `tests/h37.py` ; attentes adaptées dans `v33.py`, `v35.py`, `v36.py` (voir `CLAUDE.md`).

## v36 (23/10/2026)
### Lot A : touches, fenêtres, arrivées, repères, sons, copie de position
- **Touches (décisions de Klaatou).** **F** et **P** entrent en promenade et en sortent (en vue globale comme en promenade) ; dans le viewer, P pose une zone en promenade, **F**, **Maj+P** ou le bouton sortent. **F ne fait plus basculer le vol** : voler / atterrir = **Début** ou le bouton « Voler / Atterrir », ou **Page Haut** maintenu plus de 0,4 s au sol. Monter en vol : **Page Haut** ou **Espace** maintenu ; descendre : **Page Bas** ou **C** (atterrissage automatique au sol) ; sauter au sol : **Espace** ou **Page Haut** en appui bref. **E redevient la touche d'action des zones** (déclenchement « clic » ou « both »), invite « clic ou E : … » ; E ne saute plus, ne monte plus et ne fait rien d'autre.
- **Disposition du clavier (AZERTY / QWERTY).** La marche garde les codes physiques ; l'aide et la fenêtre Informations / État affichent les **lettres réelles** (Z Q S D ou W A S D, jamais les deux). Détection : `navigator.keyboard.getLayoutMap()` si présent (Chrome, Edge), sinon la langue du navigateur (fr, fr-FR, fr-BE : AZERTY ; le reste : QWERTY). Réglage visiteur « Disposition du clavier : Auto / AZERTY / QWERTY », mémorisé ; même règle dans le viewer. **M** est reconnue par la lettre imprimée (`e.key` = « m »), plus par le code physique : sur AZERTY c'était la touche « , ».
- **Aide et informations en trois temps.** La fenêtre « État » s'appelle **Informations / État**. **H** (aide) et **I** (informations) : masquée → déployée ; réduite → déployée ; déployée → masquée. Réduit / déployé et masqué sont mémorisés.
- **Arrivée occupée.** À chaque pose de l'avatar (ouverture, `#spawn=`, `#pos=`, arrivée par défaut, R, portail interne ou vers une autre région, « Aller à »), si un visiteur en promenade est à moins de 1 m (2 m en vertical), le nouvel arrivant passe au point libre le plus proche (anneaux de 1,2 / 2,4 / 3,6 m, sol à moins de 1 m d'écart, aucun mur, aucun visiteur à moins de 1 m). Présence pas encore connectée : contrôle refait à la réception de la liste (`welcome`), seulement si l'avatar n'a pas bougé de plus de 0,3 m. Sans place libre : pose à l'endroit demandé.
- **Repères de portail (cônes).** Petit cône pointé vers le bas (0,35 x 0,5 m, sommet à 2 m au-dessus du centre de la zone, teinte claire neutre, contour sombre) au-dessus de chaque portail et de chaque zone « enter » ou « both » ; arrivées seulement avec `--show-spawns`. Visible jusqu'à `zoneInfoDist` ; l'infobulle de la zone s'affiche au survol. **T** affiche / masque tous les cônes (mémorisé). `--zone-cone` / `--no-zone-cone` (défaut : affiché), config `zoneCone`, `MAJ_KEYS`, viewer (case + ligne de commande).
- **Sons.** Réglages visiteur : « Sons » (général) avec volume 0 à 100 (50), puis « Bip quand un message cite mon pseudo » (ne dit plus « sonore »), « Son à l'arrivée d'un visiteur » (deux notes montantes 660 puis 880 Hz) et « Son au départ d'un visiteur » (880 puis 660 Hz), toutes cochées par défaut. Web Audio sans fichier ; seulement pour les visiteurs en promenade du salon (jamais les spectateurs, jamais moi, jamais la liste initiale), au plus un son d'arrivée et un de départ toutes les 2 s ; le contexte audio démarre à la première action de l'utilisateur. Les anciens réglages du bip (`sound`) sont ignorés.
- **Copier ma position.** Bouton renommé « Copier ma position » avec une liste mémorisée **URL / xyz** (xyz = « 68.2, 39.0, -823.3 », point décimal, une décimale). Le champ « Aller à » accepte aussi une adresse complète contenant `#pos=x,y,z,yaw` (position et orientation).
- Tests : nouveau `tests/v36.py` ; attentes adaptées là où une règle de la v36 l'impose (voir `CLAUDE.md`, décisions de la v36).

### Lot B : langue de la page (français et anglais)
- **Un fichier de textes par langue** : `src/i18n/fr.json` et `src/i18n/en.json` (clés stables, texte pur, `{0}` `{1}` pour les valeurs, `.one` / `.other` pour les pluriels, `_name` = nom de la langue). `build.py` les intègre (`src/i18n.js` pour l'exécution) dans la coquille, la page autonome, la page « carte » et le viewer ; `build.py --i18n DOSSIER` choisit un autre dossier de langues. **Ajouter une langue = ajouter un fichier** (MODE_EMPLOI § 21.9). Texte absent : anglais, puis français, puis la clé.
- **Réglage « Langue / Language »** dans les Réglages visiteur : Auto (première langue de `navigator.languages` disponible, sinon l'anglais) puis chaque langue présente ; changer recharge la page. `#lang=en` (ou `fr`, `auto`) dans l'adresse est prioritaire et mémorisé. Tout texte visible est traduit : aide et groupes de touches, réglages, informations / état, invites de zones, chargement et erreurs (coquille comprise), chat, présence, carte des mondes, page `carte.html`. Les textes saisis par le propriétaire (noms de zones, panneaux) ne le sont pas.
- Tests : les autres tests fixent la locale française des contextes de navigateur (`new_context(locale="fr-FR", ...)`) ; nouveaux `tests/i18n.py` (mêmes clés, mêmes marqueurs, clés citées existantes et utilisées, aucun accent français en anglais) et `tests/v36_lang.py` (Auto, aucune lettre accentuée française dans l'interface en anglais, réglage, `#lang=`, repli, langue ajoutée par un fichier).

### Lot C : langue du viewer (`glb-viewer.html`)
- Même mécanisme que la page (lot B) : tous les textes du viewer (réglages, boutons, messages, aide, section « Clavier », commandes fabriquées) viennent de `src/i18n/*.json` (clés `viewer.*`), liste « **Langue / Language** » (Auto par défaut), `#lang=`, repli anglais, français, clé. Les noms de zones saisis ne sont jamais traduits. Le viewer ne reçoit pas les clés `py.*` (outils Python) ; les pages n'ont pas les clés `viewer.*`.
- Nouveau `tests/v36_viewer_lang.py` (Auto, aucune lettre accentuée française dans le viewer en anglais, réglage, `#lang=`, repli).

### Lot D : langue des outils Python, documentation
- **`--lang fr|en|auto`** (défaut `auto`) sur `glb2html.py`, `glb2tiles.py`, `oar2glb.py`, `presence_server.py` : messages, avertissements, erreurs et `--help`. Sans `--lang` : variable d'environnement `WEB3D_LANG`, puis langue du système, puis anglais. Les textes (clés `py.*`) sont intégrés dans chaque outil de `dist\` à la fabrication (fichiers autonomes) ; depuis `tools\` et `src\`, `i18n_py.py` et `i18n\` sont lus à côté ou dans `src\`. Options et commandes de modération du serveur (`liste`, `ejecter`, `bannir`, `bans`, `debannir`, `aide`) inchangées.
- Aide ajoutée aux options qui n'en avaient pas : `--host`, `--port`, `--max-total` (serveur), `--convoar` (oar2glb), `--sea`, `--anim`, l'argument `oar`.
- **`REFERENCE_OPTIONS.md` bilingue** : `gen_reference.py` lit chaque outil en français puis en anglais, écrit les deux textes dans chaque case « Effet » séparés par `<br>`, et échoue si une description manque dans une langue ; le mécanisme des descriptions de secours (« * ») est supprimé.
- **README.md** présente le projet (OpenSim, OAR, glTF, three.js, page promenable) et renvoie vers le nouveau **README.en.md**. `MODE_EMPLOI.md` : résumé en tête, § 21.10 (langue du viewer), § 21.11 (langue des outils). `PROCEDURES.md` : section 10 (touches et langue), serveur de présence à relancer pour la v36.
- Tests : nouveaux `tests/tools_lang.py` (aide anglaise sans lettre accentuée française pour chaque outil, `WEB3D_LANG`, priorité de `--lang`, langue du système, messages d'erreur) et `tests/doc_options.py` (toutes les options dans la référence, description non vide dans les deux langues, fichier à jour). Les autres tests fixent `WEB3D_LANG=fr`, et ceux qui copient un outil des sources copient aussi `i18n_py.py` et `i18n\` (`tests/glb2tiles.py`, `tests/terrain.py`).

## v35 (22/10/2026)
- **Aide en groupes courts** (Déplacement, Vol, Vue, Souris, Chat, Zones, Page), sans phrases ; plus de « Ctrl+C copie » ni d'explication de la sélection (le texte reste sélectionnable). **L'aide et le bloc d'état ont une barre de titre cliquable** qui les replie / déplie (état mémorisé : `glb2html_helpFold`, `glb2html_stateFold`) ; H et I masquent toujours tout. Bouton « Quitter la promenade (F) » supprimé ; en vue globale « Promenade (P) ».
- **Commandes à la Firestorm.** **F** ou **Début** : bascule le vol (en vue globale, F entre encore en promenade) ; **P** entre et sort de la promenade ; **E** / **Page Haut** : appui bref au sol = saut, maintenu plus de 0,4 s au sol = décollage (puis montée), maintenu en vol = monter ; **C** / **Page Bas** : descendre (atterrissage automatique) ; **course** : Maj ou double appui (moins de 300 ms) sur W, S, ↑, ↓ ; **M** : bascule vue subjective / troisième personne en promenade (carte des mondes hors promenade), **Ctrl+M** : carte des mondes partout ; **Fin** et **Alt + clic** : caméra derrière l'avatar ; Alt + glisser : orbiter. **E ne déclenche plus les zones** (clic, ou entrée dans le rayon d'un portail « en marchant dedans »). Tableau « Touches Firestorm / touches de cette page » : `MODE_EMPLOI.md` § 20.2.
- **Troisième personne** : la souris fait orbiter la caméra (lacet et tangage propres) sans tourner l'avatar ; l'avatar se tourne, de façon lissée, vers sa direction de déplacement quand une touche de marche est pressée ; la marche avant suit la caméra ; à l'arrêt on voit le devant de l'avatar. La présence transmet l'orientation de l'avatar, pas celle de la caméra.
- **Infobulle, clic et noms des zones en promenade** : 40 m au lieu de 14 m, réglable (`--zone-info-dist M`, config `zoneInfoDist`, de 5 à 200 ; champ dans le viewer ; `MAJ_KEYS`). Un nom affiché (showName) plus loin que la distance est masqué en promenade.
- **Copie dans le presse-papiers en http** : `navigator.clipboard.writeText` en contexte sécurisé, sinon textarea hors écran + `document.execCommand('copy')` ; « Copié » affiché ; si tout échoue, champ sélectionné et « Copie impossible : le texte est sélectionné, fais Ctrl+C ». Concerne les liens (personnel, position), les coordonnées et la commande du viewer.
- **`glb2html.py --maj` et la carte des mondes** : accepte `--register`, `--region-name`, `--region-xy`, `--region-url`, `--region-spawn`, `--thumb`, `--map`, `--map-url`, `--map-page`. Avec `--maj`, les chemins relatifs de `--register`, `--map`, `--map-page` et `--thumb` sont relatifs au dossier de la page (`-o`), et le message de fin le dit. Sans `--maj`, comportement conservé, avec une ligne qui dit où `regions.json` est écrit quand ce n'est pas à côté de la page. Le salon et la présence de la fiche viennent de la config existante.
- **Caméra libre et molette** : molette en promenade (page sans défilement) ; troisième personne : distance de la caméra 1 à 30 m (4 m, mémorisée) ; caméra libre : la molette avance / recule la caméra (pas de 15 % de la distance, 0,5 à 20 m, jamais sous le sol), vitesse des touches `max(marche, 0,5 x distance)` plafonnée à 60 m/s (Maj x3), Alt + glisser orbite autour de l'avatar à distance constante ; Fin remet la caméra derrière l'avatar à la distance par défaut.
- Viewer : F bascule le vol / entre en promenade ; P entre en promenade (en promenade P y pose toujours une zone ; **Maj+P** quitte) ; libellés « au clic » (plus « au clic ou touche E »).
- Tests : nouveau `tests/v35.py` ; attentes adaptées là où une règle de la v35 l'impose (voir `CLAUDE.md`, décisions de la v35) ; `MODE_EMPLOI.md` § 2 et nouveau § 20 (dont « Créer la carte des mondes »).

## v34 (22/10/2026)
- **Panneau d'aide sélectionnable.** Il reçoit de nouveau la souris (en v33 il la laissait passer au canvas) : son texte se sélectionne et se copie avec Ctrl+C (Ctrl+C n'est plus intercepté par la promenade ; C seule descend toujours). Le survol des marqueurs marche partout **sauf sous le panneau** ; son encombrement est borné (440 px / 45 % de la largeur, 42 % de la hauteur avec défilement).
- **Bloc d'état** distinct de l'aide (texte sélectionnable) : `Vue : …`, `Mode : à pied` / `Mode : en vol`, `Souris : …`, position, lignes des tuiles et de la vue d'ensemble. L'aide ne garde que les touches et réglages. **H** masque l'aide seule, **I** masque / affiche l'état. L'étiquette « Vue : … · au sol » disparaît.
- **Marqueurs** : avec `--zone-marker portee`, la zone de survol et de clic prend le rayon de l'anneau visible (l'infobulle apparaît sur l'anneau et dedans) ; avec `discret`, entre 0,6 m (comme avant) et 1 m.
- **Vol** : Page Haut / Page Bas (en plus de E / C), sans défilement de la page ; descendre jusqu'au sol pose l'avatar (le vol s'arrête, jamais sous le sol) ; bouton « Voler / Atterrir » dans la barre du bas.
- **Souris libre après Échap** : à la libération du pointeur (événement `pointerlockchange`, hors sortie de promenade), un clic, un double-clic ou un clic sur une zone ne redemandent plus le verrouillage ; le glisser-déposer tourne la vue ; touche **G** et bouton « Capturer la souris » recapturent ; état affiché dans le bloc d'état, remis à zéro à l'entrée en promenade.
- **Couleur en direct** : message `{t:'color', color:N}` (envoi limité à 300 ms côté page, dernière valeur toujours envoyée) ; `presence_server.py` valide (entier de 0 à 0xFFFFFF, sinon ignoré), ignore deux changements à moins de 0,2 s, diffuse aux autres ; l'avatar du visiteur prend la couleur. Compatible anciens clients et serveurs. **Relancer `presence_server.py`.**
- **`glb2html.py --maj`** : met à jour une région déjà générée en n'appliquant que les options explicitement données (une valeur égale au défaut mais donnée est appliquée), garde le reste de `X.config.json` et `X.zones.json`, écrit la version courante, renouvelle la coquille si elle diffère (copie datée `index.avant-AAAAMMJJ-HHMMSS.html`, dit en clair que la coquille est partagée), écrit `lib/` s'il manque ; échoue sans `X.config.json` en proposant la commande sans `--maj`.
- **Pseudo et lien personnel** : `#name=PSEUDO` documenté ; Réglages → « Copier mon lien personnel » (`#name=PSEUDO&key=CLE`, CLE = clé d'identité du navigateur, lien secret) ; à l'ouverture une clé au bon format devient celle du navigateur (confirmation à l'écran si le navigateur en a une différente) puis disparaît de l'adresse visible ; aucune modification du serveur. Page carte (`--map-page`) : champ « Mon pseudo » mémorisé, liens avec `#name=`.
- Tests : nouveau `tests/v34.py` ; `tests/v33.py` et `tests/v24.py` : attentes adaptées là où une règle de la v34 l'impose (aide qui ne contient plus « Vue : … », atterrissage automatique en descendant, aide masquée pour survoler les marqueurs ; voir `CLAUDE.md`, décisions de la v34). Docs : `MODE_EMPLOI.md` § 2, § 16 et nouveau § 19, `README.md`, `CLAUDE.md`.

## v33 (22/10/2026)
- **Démarrage avec une arrivée (`#spawn=`), région en tuiles : cause mesurée et corrigée.** Sur une région synthétique de 16 tuiles dont deux de plus d'un million de triangles (23 Mo, `tests/glbfab.py region_lourde`), avec le processeur ralenti 10 fois : écran noir de **121,6 s** (promenade à 125,7 s). Cause : le chargeur ne prenait l'arrivée pour référence que 4 s, puis revenait à la cible de caméra ; la tuile de l'arrivée, hors du rayon de la cible, était **déchargée et son téléchargement abandonné** (`TL.forcedUntil`), puis `loadTiles` attendait 120 s. Ce n'était pas la grille de collision (142 ms de calcul pour 1 million de triangles à vitesse normale, 2 s à x10). v33 : promenade à **7,1 s** (x10), 1,6 s à vitesse normale (2,6 s avant).
  - L'arrivée demandée est la **référence du chargeur** (`TL.anchor`) jusqu'au début de la promenade ; ses tuiles démarrent **avant la vue d'ensemble** et **aucune autre tuile ne démarre** avant qu'elles soient prêtes. Leur grille passe en premier (budget 40 ms par image contre 6) ; en promenade, la grille de la tuile de l'avatar passe toujours avant les autres.
  - **Jamais d'écran noir sans texte** : « Chargement du sol… n/m tuiles prêtes · N s », texte blanc sur fond noir encadré. Après 15 s l'écran noir est retiré (vue d'ensemble visible) et la promenade démarre dès que la tuile est prête (`TL.pending`) ; le délai de 120 s a disparu (après 60 s : « attente longue »). Une erreur de chargement n'est plus cachée par le fondu.
  - **Une ligne de console par tuile** prête ou en échec (`[tuile] … prête : 23.0 Mo · 1002668 triangles · téléchargement … · analyse du GLB … · attente en file de grille … · construction de la grille …`) et `tilesState().log`.
- **Arrivée par défaut.** Sans lien, si une arrivée `default` existe, la page s'ouvre cadrée dessus et F démarre à son point avec son orientation ; `--target` explicite garde la priorité pour le cadrage (nouvelle clé de config `targetExplicit` ; une config sans cette clé garde l'ancien comportement). **Retour à l'arrivée** : bouton et touche **R** (téléportation avec attente de la tuile en promenade, recadrage en vue globale).
- **Marqueurs** : `--zone-marker discret|portee|aucun` (défaut = comportement d'avant) et `--show-spawns` (arrivées jamais dessinées sans cette option) ; réglage dans l'export du viewer et dans le récapitulatif de la ligne de commande.
- **Promenade** : **vol** (touche Début ; E monte, C descend ; murs solides ; jamais sous le sol ; `--fly` / `--no-fly`), **trois vues** (V : subjective, troisième personne, caméra libre ; la vue est écrite dans l'aide), champ **« Aller à x, y, z »** (virgule ou point décimal), **« Copier le lien de ma position »** (`#pos=x,y,z,yaw`, lu à l'ouverture comme une arrivée anonyme).
- **Chat** : saisie persistante (Entrée envoie et garde la saisie ouverte, Échap la ferme, les flèches déplacent l'avatar), **enregistrement** dans un fichier texte UTF-8 côté navigateur, **pseudo cité** (gras et « @ », bulle qui clignote 6 fois, bip Web Audio ; trois cases mémorisées), **complétion `@`** (5 pseudos au plus).
- **Couleur de l'avatar** : sélecteur mémorisé, envoyé dans `hello` ; `presence_server.py` accepte un entier de 0 à 0xFFFFFF et rejette sans bruit tout le reste. **Relancer `presence_server.py`.** `--log-ip raw` vérifié par un test (IP en clair dans la console et le journal) et documenté avec le rappel RGPD.
- **Zones enregistrées dans le dossier de la région** (viewer, Edge et Chrome, File System Access) : `X.zones.json` écrit directement, ancien gardé sous `X.zones.bak.json`, chemin et heure affichés ; sans l'API ou si refusé : téléchargement et phrase « enregistre ce fichier dans le dossier de la région… ». **F5 suffit** ensuite. `glb2html.py --tiles --zones` avec le fichier déjà en place : « zones déjà en place ».
- **Correctif (v32) découvert par les tests** : le script `glb2html.py` exporté par le viewer (bouton « Exporter le script Python ») plantait (`NameError: ZONES_LIVE`) : la constante manquait dans le bloc des défauts. Corrigé et testé (le script exporté génère une page).
- Le panneau d'aide laisse passer les clics (il s'agrandit : champ « Aller à », lien) ; `tests/tuiles.py` : le texte attendu **commence par** « Chargement du sol… » (le décompte et le temps sont ajoutés).
- Tests : nouveau `tests/v33.py` (159 contrôles ; navigateur : Chromium sans tête, vrai `presence_server.py`, région de tuiles lourdes) ; toutes les suites précédentes passent.
- Docs : `MODE_EMPLOI.md` § 2 et nouveau § 18, `README.md`, `CLAUDE.md` (décisions v33).

## v32 (22/10/2026)
- **Le viewer ouvre une région en tuiles.** Bouton « Ouvrir une région en tuiles (dossier) » (dossier qui contient `X.tiles.json`, choix ou glisser-déposer ; fichiers lus sur place, un par un, à la demande : jamais 1,3 Go en mémoire), ou `glb-viewer.html?tuiles=chemin/X.tiles.json` quand le viewer est servi en http (chemin relatif à la page, mêmes règles de sécurité que la coquille). Il utilise le chargeur de la coquille (`loadTiles` de `core.js`, source de fichiers abstraite : adresses http ou dossier choisi), donc mêmes rayon, marge, budgets et vue d'ensemble. **Repère du modèle d'origine, aucun recentrage** : zones, arrivées, cible et trou de la mer produits sont ceux de `glb2html.py --tiles`. Cible initiale = centre de l'étendue (même règle que `--tiles`). Toutes les fonctions d'édition de zones fonctionnent (créer, déplacer, rayon et hauteur, portails, arrivées, panneaux, Home Assistant, P en promenade). Le placement par clic se fait sur les tuiles détaillées chargées ; un clic hors tuile chargée dit en texte « Pas de tuile détaillée chargée à cet endroit… » et charge la tuile. Export `X.zones.json` (nom de la région), import d'un `X.zones.json` existant pour le compléter, récapitulatif de commande `glb2html.py --shared-shell -o X.html --tiles X.tiles.json --zones X.zones.json …` (hauteur de mer par défaut 20 m comme `--tiles`, cible écrite seulement si elle diffère). Export HTML autonome et `.zip` désactivés (pas de GLB unique), rotation non proposée, trou de la mer relatif au centre de la région. Ouvrir ensuite un `.glb` ferme le mode tuiles (tuiles et vue d'ensemble libérées, caméra, brouillard et distance maximale d'origine : `closeTiles`). Testé : dossier choisi, glisser-déposer (entrées de dossier simulées, sous-dossier), `?tuiles=`, refus de `..`.
- **Coordonnées.** Nouvelle section « Coordonnées (m) » du viewer : point visé (clic simple) et cible en texte (x, y, z, une décimale), boutons « Copier le point visé » et « Copier la cible ». La coquille affiche dans le panneau d'aide la position de la cible en vue globale ou de l'avatar en promenade (« Position cible (vue globale) : x 123.5 · y 15.0 · z -77.7 m »).
- **Zones liées à un objet en mode tuiles.** `glb2tiles.py` écrit dans les `extras` de chaque nœud copié `ref` (référence stable dans le GLB entier : le nom s'il est unique, sinon `nom#index`, rang dans l'ordre de parcours) et `box` (boîte monde de l'objet ENTIER, identique dans chaque morceau d'un objet réparti sur plusieurs tuiles) ; `X.tiles.json` porte `nodeRefs: 1`. Coût mesuré (GLB synthétique de 40 000 nœuds) : +0,5 s sur 8 s, +3 Mo sur 230 Mo. La coquille et le viewer indexent les nœuds des tuiles chargées par `ref` et résolvent les zones liées : la zone **apparaît quand la tuile de l'objet est chargée** (boîte de l'objet entier, même si un seul morceau est chargé) et disparaît au déchargement (absente de la scène, de la détection de proximité et des portails ; reconstruction des seules zones quand la résolution change). Le viewer lie une zone à l'objet cliqué (référence lue dans `extras.ref` en remontant les parents). Les références sont celles des noms du GLB, pas celles du chargeur de three.js (qui renomme les doublons) : une zone liée écrite en mode tuiles s'utilise en mode tuiles. **Anciennes tuiles** (sans `nodeRefs`) : zones liées ignorées avec « …redécouper avec glb2tiles v32 » en console ; `glb2html.py --tiles` avertit quand des zones sont liées ; `glb2tiles.py --analyse` et `--vue-ensemble-seule` signalent des tuiles existantes sans références. `--sans-references` écrit l'ancien format.
- **Coquille changée** (`core.js`, `template.html`) : une coquille `index.html` existante est différente et n'est jamais écrasée ; la supprimer avant de régénérer.
- Tests : nouveau `tests/v32.py` (53 contrôles : références d'objets dans les tuiles, objet réparti sur 4 tuiles, nom partagé, ancien format ; viewer en mode tuiles : dossier, glisser-déposer, `?tuiles=`, zone libre, portail, arrivée, zones liées à « Statue » et « Banc#1 », clic hors tuile, coordonnées et copie, export, commande, réimport, retour à un GLB ; coquille avec `glb2html.py --tiles --zones` : positions à 0,05 m, zone liée absente puis présente au chargement de la tuile, objet réparti, déchargement, arrivée par lien, positions affichées ; anciennes tuiles), `tests/glbfab.py` étendu (option `village`, terrain à face avant vers le haut pour le lancer de rayon). **`tests/tuiles.py` : la génération de ses tuiles reçoit `--sans-references`** (ses attentes ne changent pas : en format v31 les zones liées restent ignorées) ; toutes les autres suites passent sans modification.
- Docs : `MODE_EMPLOI.md` § 17, 17 bis et nouveau § 17 ter (pas à pas), `README.md`, `CLAUDE.md`.

## v31 (22/10/2026)
- **Images vides ou invalides (`glb2tiles.py`).** Sur la région « Free House Gallery 4X4 », 778 images sur 19 799 avaient un `bufferView` de 0 octet et faisaient échouer leur tuile (« THREE.GLTFLoader: Couldn't load texture »). Toute image embarquée de 0 octet, d'un autre format que PNG/JPEG/WebP ou **tronquée** (mesuré dans Chromium : un PNG, un JPEG ou un WebP coupé échoue comme une image vide, d'où la vérification de la fin du fichier) est remplacée à l'écriture par un PNG gris de 4 x 4 pixels (gris 128, celui de `oar2glb.py`), écrit une seule fois par tuile et partagé par toutes les références de la tuile. Matériaux, textures et coordonnées de texture inchangés. Vérification par en-tête, fin de fichier et en-têtes de blocs (l'image n'est pas lue en entier). `--analyse` et le rapport donnent le nombre d'images remplacées (distinctes et occurrences) ; `X.tiles.json` reçoit `replacedImages` (et un nombre par tuile).
- **Sortie de promenade (F).** `walkStop()` ne remet plus la caméra exactement où elle était : la cible de la vue globale (cercle d'atterrissage) est posée **au sol sous la dernière position de l'avatar** ; la caméra garde **le même décalage** (distance et direction) qu'avant l'entrée en promenade. En mode tuiles le chargeur suit cette cible : les tuiles autour de l'avatar restent chargées (avec l'ancien comportement elles partaient, testé). Valable aussi pour un GLB unique.
- **Vue d'ensemble légère `X.overview.glb`.** Produite par `glb2tiles.py` avec le découpage (`--sans-vue-ensemble` pour s'en passer) ou seule (`--vue-ensemble-seule`, mêmes options de découpage ; le découpage recalculé doit retrouver exactement les tuiles de `X.tiles.json`, sinon erreur claire). Un nœud par fichier de tuile (nom et `extras.tile` = clé de la tuile), un seul matériau, **aucune image**, couleurs de sommets : couleur moyenne de la texture de chaque matériau avec Pillow (facultatif), sinon couleur de base ; couleurs de sommets du terrain conservées. Chaque primitive **unique** est simplifiée une seule fois (regroupement de sommets sur une grille proportionnelle à sa boîte, Python standard) puis recopiée avec la matrice de chaque instance (testé : 25 simplifications pour 64 instances). Le terrain (pièces `extras.terrain`) est rééchantillonné à part sur un réseau régulier commun de 4 m : aucune fente entre patches (testé sur les arêtes ouvertes), hauteurs à moins de 5 cm. Omis : objets de plus grande dimension sous `--ov-seuil` (3 m), primitives translucides (BLEND), objets à squelette. Budgets `--ov-budget` 25 Mo et `--ov-budget-tri` 1 500 000 : le terrain prend au plus la moitié (son pas grossit sinon), puis les plus grands objets d'abord ; le seuil effectif monte, et la résolution baisse si le budget oblige à omettre des objets de plus de `--ov-seuil-max` (24 m). Rapport : poids, triangles, objets gardés et omis (par cause), couleurs, temps. `--analyse` imprime en plus la répartition des instances par étendue (1 à 64 m) pour choisir le seuil. Lecture du GLB par morceaux de 4 Mo au plus (testé), progression affichée.
- **Valeur par défaut du seuil (3 m).** Calcul de taille à l'écran, pas mesure sur la région : avec un champ de 38 degrés sur 1 080 pixels de haut, 3 m couvrent environ 22 pixels à 210 m (limite du rayon de chargement) et environ 8 pixels à 600 m. Le budget relève le seuil si besoin ; sur la vraie région, le tableau de `--analyse` donne les effectifs réels.
- **Coquille.** Si `X.tiles.json` mentionne `overview` (chemin relatif de même règle de sécurité que les tuiles), la vue d'ensemble est chargée **avant** les tuiles. Cellule masquée dès que la tuile détaillée est affichée (même bloc synchrone que l'ajout du groupe : jamais les deux, jamais aucun), réaffichée au déchargement ou en échec. Elle n'est utilisée ni pour les collisions, ni pour le sol, ni pour « Chargement du sol… », et n'entre pas dans `tileMaxMo` / `tileMaxTri` ; la ligne d'information (texte) la compte à part (« Vue d'ensemble (à part) : … Mo · … triangles »). La vue globale se cadre sur toute la région (distance maximale, brouillard et plan lointain suivent l'étendue) ; double-clic dessus : la cible se place au point lointain et les tuiles s'y chargent. Panne de la vue d'ensemble (404, fichier illisible) : avertissement, « Vue d'ensemble indisponible », comportement de la v30. Ancien `X.tiles.json` : comportement de la v30, cadrage sur le rayon. Le chargeur retire `/`, `.` et les espaces des noms de nœuds : la correspondance se fait par `extras.tile` (`userData.tile`).
- **`glb2html.py --tiles`** place aussi `X.overview.glb` à côté de la page (même règle que les tuiles : rien n'est copié si tout est déjà là) ; une entrée `overview` dangereuse (`..`, `:`…) est refusée avant toute écriture.
- **Tuiles d'une précédente exécution.** `glb2tiles.py` écrit les nouvelles tuiles, puis supprime les `T_*_*_*.glb` du dossier qui ne figurent plus dans le nouvel index (avant : tous supprimés d'abord) et en donne le nombre. Les autres fichiers ne sont pas touchés.
- **Durées mesurées** (GLB synthétiques de maillage régulier, Python 3.13 sans numpy) : 0,5 / 2 / 8 / 24 millions de triangles uniques en 0,3 / 1,2 / 4,5 / 13 s (environ 1,8 M triangles uniques par seconde, linéaire), mémoire 25 / 31 / 68 / 164 Mo ; 20 000 petits meshes et 40 000 instances : 15 s, 377 Mo ; terrain de 1 024 m (256 patches de 4 225 sommets) : 3,6 s, 57 Mo. Pillow (couleur moyenne d'une texture) : 2 ms (JPEG 512²), 5 ms (JPEG 1 024²), 19 ms (JPEG 2 048²), 21 ms (PNG 1 024²), 106 ms (PNG 2 048²).
- **Estimation pour « Free House Gallery 4X4 » (1,27 Go), à vérifier : aucune mesure sur le vrai fichier.** Vue d'ensemble seule, hors lecture et écriture des tuiles : terrain ≈ 4 s ; objets de 25 à 70 millions de triangles uniques (889 Mo de géométrie à 12 à 35 octets par triangle) : de 15 s (débit des maillages réguliers) à 4,5 min (débit des petits meshes : 0,26 M triangles par seconde) ; couleurs moyennes : 10 905 images distinctes à 2 à 20 ms, soit 20 s à 4 min. Total : de l'ordre de **1 à 9 minutes, probablement 3 à 5**, mémoire sous 1 Go. L'analyse et l'écriture des tuiles (déjà dans la v30) s'y ajoutent ; la vérification des 19 799 images ne lit que des en-têtes.
- Tests : nouveau `tests/v31.py` (65 contrôles : images invalides dont un témoin Chromium, vue d'ensemble, budgets, terrain sans fente, une simplification par primitive unique, tuiles obsolètes, sortie de promenade avec et sans tuiles, vue d'ensemble dans la coquille, panne, ancien index), `tests/glbfab.py` (GLB synthétiques), `tests/tuiles.py` ajusté (la géométrie de la vue d'ensemble fait partie de la base mémoire). Les autres tests passent sans modification.
- Docs : `MODE_EMPLOI.md` § 2, 17 et 17 bis, `README.md`, `CLAUDE.md`.

## v30 (22/10/2026)
- **La coquille charge une région découpée en tuiles par `glb2tiles.py`.** Champ `tiles` dans `X.config.json` (chemin relatif de `X.tiles.json`) ; sans lui, rien ne change (aucune clé de tuiles n'est écrite, les tests v23, v24, v27, portail_interne, modulaire et smoke passent sans modification). La page charge les tuiles dont la boîte est à moins de `tileRadius` m de l'avatar (en vue globale : de la cible), les plus proches d'abord, `tileConcurrency` téléchargements à la fois ; elle décharge au-delà de `tileRadius + tileMargin` (hystérésis), puis, si `tileMaxMo` ou `tileMaxTri` sont dépassés, les plus lointaines d'abord. Distance mesurée à la boîte réelle de la tuile (`min` / `max` de `X.tiles.json`), en plan X,Z. `?rayon=NNN` dans l'adresse remplace `tileRadius` (essais).
- Chargement par le chargeur existant (GLTFLoader, Draco, Meshopt) à partir d'un `ArrayBuffer`, analyse asynchrone, ajout à la scène seulement quand la tuile est prête, un groupe nommé `tile:<fichier>` par tuile. Déchargement complet : `disposeObject` (géométries, matériaux, textures) plus fermeture des images décodées ; `renderer.info.memory` revient au niveau de base (testé). Échec (404, GLB corrompu) : message dans la page, ligne d'information, nouvelle tentative plus tard (3 s, puis 6, 12… jusqu'à 30 s), sans bloquer les autres tuiles.
- **Promenade et collisions par tuile.** `buildCollisionGrid` devient un générateur (`collisionGridSteps`) : la promenade ordinaire l'exécute d'une traite (résultat identique) ; en mode tuiles, une grille par tuile est construite par tranches de 6 ms au plus par image, dès le chargement de la tuile, et supprimée au déchargement. Sol et murs viennent des seules tuiles prêtes (grille composite). L'avatar n'avance jamais vers un point dont une tuile n'est pas prête : déplacement bloqué, indicateur texte « Chargement du sol… », reprise dès que la tuile est prête ; ni chute ni saut. La touche F attend la tuile sous l'avatar (F de nouveau : annuler) ; une téléportation (portail interne) vers une zone non chargée attend de même. Les sols des patches de terrain, qui ont des bords communs, se prolongent d'une tuile à l'autre sans saut (testé sur 8 frontières).
- **Repère** : celui du modèle d'origine, sans recentrage (les tuiles gardent leurs coordonnées) ; `rotate` est appliqué à la racine des tuiles. La mer est centrée sur le centre de l'étendue des tuiles. La caméra se cadre sur le rayon de chargement. **Zones** : les zones libres fonctionnent comme avant ; les zones liées à un élément du modèle (champ `mesh`, référence `nom#index` calculée sur tout le modèle) sont ignorées avec un avertissement en console. Présence, chat, carte des mondes, portails : inchangés.
- **Ligne d'information** (texte seul, dans le panneau d'aide s'il existe) : tuiles chargées / total, Mo, triangles, tuiles en cours et en échec. En mode tuiles, la vue globale ne montre que les tuiles chargées (la vue d'ensemble légère viendra dans un autre lot).
- **`glb2html.py --tiles X.tiles.json`** (sans .glb ; `-o` désigne la région ; avec `--shared-shell` ou seul, implique `--modular`) : écrit `X.config.json` (champ `tiles` et `tileRadius` 150, `tileMargin` 60, `tileMaxMo` 200, `tileMaxTri` 8 000 000, `tileConcurrency` 4, réglables par `--tile-radius`, `--tile-margin`, `--tile-max-mo`, `--tile-max-tri`, `--tile-concurrency`), `X.zones.json`, la coquille et `lib/` comme d'habitude. `X.tiles.json` et ses tuiles ne sont copiés que s'ils ne sont pas déjà à côté de la page (sinon : « rien n'est copié » ; copie fichier par fichier de ce qui manque ou de taille différente) ; le message dit ce qui est fait. Cible de caméra par défaut : centre de l'étendue (hauteur 20 m) ; hauteur de la mer par défaut : 20 m. Chemins de tuiles refusés s'ils contiennent `..`, `:`, `?`, `#`, `\`, un segment vide ou commencent par `/` (règle identique dans la coquille, qui refuse aussi un champ `tiles` de ce genre sans aucune requête).
- La coquille change (chargement des tuiles) : une coquille existante différente n'est pas écrasée (avertissement habituel) ; la supprimer pour la renouveler.
- **`glb2tiles.py` : « octets gagnés » de `--exclure`.** Le calcul (géométrie et images qu'aucun objet conservé n'utilise) était correct : il vaut 0 quand tous les objets exclus partagent leurs primitives ou leurs images avec des objets conservés (cas d'un cube commun). Le rapport et `--analyse` le disent maintenant : ligne « octets des exclus qu'un objet conservé utilise aussi (non gagnés) » et phrase d'explication quand le gain est 0 ; clé `bytesShared` dans `excluded` de `X.tiles.json`. Test ajouté.
- Tests : nouveau `tests/tuiles.py` (région synthétique de 64 patches et 24 maisons découpée en 16 tuiles ; Chromium sans tête, réponses des tuiles retenues ou remplacées avec `page.route`) ; `tests/glb2tiles.py` étendu.
- Docs : `MODE_EMPLOI.md` § 17 bis, `README.md`, `CLAUDE.md` (décisions v30, limites, feuille de route).

## v29 (22/10/2026)
- **`tools/oar2glb.py` : terrain complet des régions de plus de 256 m.** convoar ne produit qu'un nœud « Terrain » plafonné (257 x 267 m sur une région de 1 024 m). La carte de hauteurs de l'OAR (`terrains/*.r32`) sert maintenant à construire des patches de `--terrain-patch` m (défaut 64), un mesh de (P+1)² sommets chacun, nommés « Terrain i,j », objets racine de la scène. Bords partagés identiques (hauteurs, normales, couleurs), dernier patch plus petit si n-1 n'est pas multiple de P, normales par différences centrées sur toute la carte, un seul matériau « terrain » simple face, indices 16 bits, pas de coordonnées de texture, couleur par sommet (`COLOR_0`) : sable humide sous l'eau, sable sec puis herbe en dégradé léger selon l'altitude, roche grise au-delà d'environ 35 degrés (palette dans `MODE_EMPLOI.md` § 15). Niveau d'eau : `WaterHeight` de `settings/*.xml`, sinon 20 m ; journalisé.
- `--terrain auto|oui|non` (défaut `auto`) : en `auto`, le nœud « Terrain » de convoar est remplacé seulement s'il couvre moins de 95 % de la carte ; région de 256 m ou terrain complet : GLB identique octet pour octet à celui de `--terrain non`. Le filtre des objets hors région épargne les patches.
- `--terrain-seul GLB OAR` (sans convoar, GLB de plusieurs Go) : le GLB n'est pas chargé en entier (JSON réécrit, chunk binaire recopié par morceaux de 8 Mo, nouveaux tampons ajoutés à la fin) ; sortie `X-terrain.glb` ou `--sortie`, l'original n'est jamais écrasé, aucune pause. OAR sans carte de hauteurs : message clair, code 0, rien d'écrit.
- Journal `[terrain]` : carte, niveau d'eau et son origine, patches, sommets, octets ajoutés, durée.
- **`tools/glb2tiles.py` : pause finale.** `input("Entrée pour fermer...")` ne lève plus `EOFError` sans console (script, tâche planifiée) : la pause est ignorée si stdin n'est pas interactif ; `--nopause` existait déjà. Même garde dans `oar2glb.py`.
- **`tools/glb2tiles.py --exclure REGEX`** (insensible à la casse, répétable) avec `--exclure-max-tri` (24) et `--exclure-max-meshes` (1) : retire du découpage les objets racine (et leurs descendants) dont le nom correspond ET qui respectent les deux garde-fous (par exemple les « boîtes de livraison » de 12 triangles d'un catalogue) ; jamais de décision sur l'étendue (boîte gonflée par les tampons partagés). Les exclus n'entrent pas dans les tuiles ni dans les calculs de poids, triangles et budget. `--analyse` et le rapport final : nombre d'exclus, triangles retirés, octets gagnés, objets conservés par les garde-fous, 20 noms les plus fréquents ; clé `excluded` dans `X.tiles.json` (seulement avec l'option). Expression invalide : message clair.
- Tests : nouveau `tests/terrain.py` ; `tests/glb2tiles.py` étendu (`--exclure`, pause sans console).
- Docs : `MODE_EMPLOI.md` § 15 et § 17, `README.md`, `CLAUDE.md` (décisions v29, feuille de route).

## v28 (21/10/2026)
- **Nouvel outil `tools/glb2tiles.py`** (fabriqué dans `dist/glb2tiles.py`) : découpe un GLB énorme en tuiles autonomes `X.tiles/T_<niveau>_<i>_<j>.glb` + `X.tiles.json`. Ni le viewer ni la coquille ne sont modifiés : le chargement des tuiles viendra dans un autre lot.
- **Lecture par morceaux** : le GLB n'est jamais chargé en entier (en-tête JSON, puis indices, positions et images par seek/read). Avancement dans le journal toutes les 5 % ou 10 s. GLB compressé (Draco, meshopt) et accessors `sparse` : refus avec message.
- **Découpage** : quadtree adaptatif sur X,Z, cellules non vides seulement, budget en Mo **et** en triangles (`--budget`, `--budget-tri`, `--min`). Objet racine gardé entier si poids autonome ≤ `--entier-poids` ET étendue ≤ `--entier-etendue`, sinon réparti instance par instance (parents recopiés avec leurs transformations). Objet avec skin : jamais réparti (joints hors de l'objet, `inverseBindMatrices` recopiés). Mesh unique plus lourd que le budget : avertissement. Meshes partagés dupliqués dans chaque tuile.
- **Compactage** : seuls les sommets indexés sont gardés (positions, normales, tangentes, UV, couleurs, joints, poids, cibles), renumérotés, indices en 16 bits si possible, min/max des positions recalculés, `byteStride` et `normalized` gérés (éléments de 3 octets complétés à 4).
- **`--analyse`** (lecture seule) : mesures de `glb-stats`, 10 meshes les plus lourds, 10 instances les plus éloignées, nombre de tuiles et duplication prévus, racines entières/réparties, recommandation en une phrase (« pas de découpage nécessaire » sous `--seuil` Mo et `--seuil-tri` triangles). Les positions ne sont lues que pour les primitives qui n'utilisent qu'une partie d'un tampon partagé (boîte exacte) ; le résumé le chiffre.
- `tools/glb-stats.py` : le calcul est découpé en fonctions communes `modele(g)` et `rapport(...)`, réutilisées par `glb2tiles.py` ; sortie inchangée (vérifié octet pour octet). `build.py` copie `glb-stats.py` dans `dist/` à côté de `glb2tiles.py`.
- `--version` (`glb2tiles vNN (jj/mm/aaaa)`, sans journal ni pause), version en première ligne de `glb2tiles.log`.
- Tests : nouveau `tests/glb2tiles.py` (GLB synthétiques : léger, accessor partagé, racine de 80 m, racine de 600 m à 1 000 enfants, mesh hors budget, mesh réutilisé, skin, instance à 3 km, Draco refusé, lecture par morceaux, version).
- Docs : `MODE_EMPLOI.md` § 17, `README.md`, `CLAUDE.md` (décisions v28, feuille de route).

## v27 (21/10/2026)
- **Repère des avatars visiteurs : la bulle de chat n'est plus recouverte.** Les repères sont empilés de bas en haut : nom, bulle (si elle existe), losange, avec une marge entre chacun, calculée sur les tailles réelles des sprites (`scale.y`). Le nom et la bulle suivent le même facteur d'éloignement k (la bulle grossit avec la distance comme le nom, donc le nom ne la recouvre plus de loin) ; le bas du losange est toujours au-dessus du haut de la bulle, de 1 à 4 lignes, de près comme de loin. Sans bulle, le losange est exactement à sa hauteur d'avant ; à l'apparition ou à la disparition d'une bulle il glisse (environ 0,2 s) au lieu de sauter. Ni couleur ni forme modifiées, protocole de présence inchangé.
- `getPresence()` expose en plus, par visiteur, `stack` (hauteurs bas / haut du nom, de la bulle et du losange, distance à la caméra), pour les tests.
- Tests : nouveau `tests/v27.py` (faux WebSocket injecté, sans serveur ni réseau) : nom < bulle < losange pour 1 et 4 lignes, à 8 m et à 120 m ; sans bulle, hauteur inchangée ; retour à la hauteur d'origine quand la bulle expire.

## v26 (21/10/2026)
- **Coquille unique en mode modulaire.** Une seule coquille (par défaut `index.html`) et un seul `lib/three-0.160.0/` servent plusieurs régions d'un même dossier ; chaque région n'ajoute que `NOM.glb`, `NOM.config.json` et `NOM.zones.json`. Adresse : `index.html?region=NOM` (`NOM.html` accepté : l'extension est retirée).
- La coquille reste identique, octet pour octet, pour toutes les régions (elle lit `?region=` à l'exécution). **Sans paramètre `region`, comportement inchangé** (fichiers déduits du nom de la page) : les pages déjà publiées et leurs coquilles continuent de marcher. Sans paramètre ni fichier correspondant : « Erreur : … introuvable (HTTP …) ».
- **Sécurité.** NOM doit être un seul nom de fichier : un nom vide, contenant `/` `\` `:` `?` `#` ou `..`, des caractères de contrôle, ou commençant par un point est refusé avec un message dans la page et **aucune requête réseau** (sinon `?region=https://autre-site/x` ferait charger config, zones et modèle depuis un site étranger). Contrôle fait avant toute requête ; le script `glb2html.py` applique la même règle à `-o`.
- `glb2html.py --shared-shell [COQUILLE.html]` (implique `--modular`) : `-o` désigne la région ; n'écrit que `X.glb`, `X.config.json`, `X.zones.json`, plus la coquille et `lib/` **s'ils sont absents** (une coquille existante et différente est conservée, avec avertissement). `--register` écrit l'adresse `COQUILLE.html?region=NOM` dans `regions.json` ; `--config-only` et `--zones-only` marchent avec cette structure. Vérifiés : `#spawn=` ajouté après la query string (carte, portails), « vous êtes ici » (reconnu par le salon puis par l'adresse complète), portail vers la même région (aucune navigation) ou vers une autre région de la même coquille.
- Viewer : « Exporter la structure modulaire (.zip) » donne `index.html`, `NOM.glb`, `NOM.config.json`, `NOM.zones.json`, `lib/` (la région s'ouvre à `index.html?region=NOM`) ; le récapitulatif pour le script a une case « Coquille commune » (`--shared-shell` à la place de `--modular`). **Changement** : le `.zip` ne contient plus `NOM.html` mais `index.html`.
- `tools/oar2glb.py` : `--version` (affiche `oar2glb vNN (jj/mm/aaaa)` sans journal ni pause), version en première ligne du journal (`[oar2glb] …`), fabriqué dans `dist/oar2glb.py` par `build.py` (marqueur `__VERSION__`, comme `presence_server.py`).
- `tools/oar2glb.py --reencode` : les textures que Pillow ne sait pas lire sont remplacées par un gris neutre 4x4 au lieu d'être laissées à convoar (constat : convoar plante dans `OpenJPEG.DotNetDecode64` après environ 30 minutes sur une région 4x4 de 17 173 textures dont 762 illisibles) ; liste écrite dans `X-reenc-illisibles.txt` ; 8 cœurs au plus et lots de 512 pour borner la mémoire ; test ajouté dans `tests/oar2glb.py`.
- Tests : `tests/modulaire.py` étendu (deux régions avec la même coquille, région simple inchangée, absence de fichier, paramètres refusés `../x`, `https://…`, `a/b`, vide, point initial, encodés en pourcentage, sans aucune requête réseau ; carte, `#spawn=`, portails) ; `tests/oar2glb.py` (version source et `dist/`, première ligne du journal).
- Docs : `MODE_EMPLOI.md` § 16 (coquille unique), § 6 et § 15 ; `README.md` ; `CLAUDE.md` (décisions v26 ; feuille de route : régions énormes, notes seulement, rien d'implémenté).

## v25 (20/10/2026)
`tools/oar2glb.py` : correction des animaux riggés (animesh) et des prims invisibles, validée sur un vrai OAR (Jungle_Isle : 771 parties, 34 meshes riggés). Cette version regroupe les itérations de mise au point du 20/10/2026.
- **Meshes riggés reconstruits depuis l'OAR.** Pour tout mesh riggé, le `.llmesh` de l'OAR (`assets/*_mesh.llmesh`) est décodé (positions, normales, UV, triangles, domaine de position, bloc skin zlib + LLSD binaire) et `bind_shape_matrix` est appliquée ; l'échelle du prim est ignorée. Raison : la géométrie que convoar écrit pour ces meshes est inutilisable (étendues de sommets identiques pour des animaux différents, échelle cuite inconnue de l'OAR). Aucune règle propre à un animal. Matériaux et textures repris du nœud GLB (face i = primitive i), sens des UV détecté. Si le `.llmesh` est illisible, le mesh reste tel que convoar l'a produit.
- **Placement.** Les morceaux d'un même animal (un cheval = 6 meshes de même nom, chacun avec sa `bind_shape_matrix`) sont déplacés ensemble : centrés à l'horizontale sur la racine, rotation = racine x rotation du premier morceau, pieds sous la boîte racine (z moins la moitié de son échelle) ou à l'altitude de la racine si elle est elle-même riggée. Le terrain de l'OAR n'est pas utilisé. Garde-fou : une taille hors de 0,1 à 12 m laisse le mesh tel quel.
- **Prims invisibles retirés** (`--keep-invisible` pour les garder) : toutes les faces à alpha 0, ou texture invisible standard (`8dcd4a48-…`, `3a367d1c-…` ; `e97cf410-…` est le dégradé alpha, visible), nœuds dont tous les matériaux sont à alpha 0, et boîte racine d'animesh (prim simple, racine d'un objet dont toutes les autres parties sont des meshes riggés). Les enfants d'une racine retirée restent.
- **Correspondance nœud GLB ↔ partie de l'OAR** : UUID du prim, sinon UUID du mesh, sinon nom + position (2 m), ordre de l'OAR à distance égale. convoar ne conserve aucun UUID : sur Jungle_Isle tout passe par nom + position.
- **`--diag`** : ne modifie rien, ne lance pas convoar ; une ligne par partie de l'OAR (nom, UUID, riggé, échelle du prim, `bind_shape_matrix`, domaine de position, transparent, boîte racine d'animesh, nœud GLB trouvé et méthode, matériau GLB). Lit le `.gltf` de `<oar>-GLTF` (conservé par `--keep`), sinon le `.glb` voisin, ou `--glb`. Journal dans `oar2glb.diag.log` (la conversion écrit `oar2glb.log`).
- **`--reperes`** : un mât rouge de 15 m à chaque animal riggé posé, pour les retrouver dans le viewer.
- **Textures** : constat sur Jungle_Isle : `--reencode` faisait manquer environ 150 images sur 353 (textures grises) ; sans lui, aucune absente. Le script compare les images annoncées par le `.gltf` aux fichiers présents, relance convoar (2 essais de plus au maximum) en gardant les images déjà écrites, et résume les absentes en une ligne.
- Journal : « N mesh(es) riggé(s) remis à l'échelle, M prim(s) invisible(s) retiré(s) » et une ligne `[contrôle]` par animal (objets dont la boîte englobante contient son centre).
- Tests : `tests/oar2glb.py` (OAR synthétique, faux convoar, deux variantes de GLB : UUID dans les extras ou noms seuls ; cheval en 2 morceaux, mesh non normalisé, racine tournée, taille implausible, image manquante).
- `MODE_EMPLOI.md` : section 15 complète (commandes de `oar2glb.py`).

## v24 (19/10/2026)
- Page exportée (autonome et modulaire) : plus aucun cylindre pour les zones lien web, commande HA et portail. Zone liée à un élément : aucun objet ajouté ; au survol, curseur main, léger contour de l'élément et infobulle (nom + destination : adresse web, « Région : … », « Commande : … » ; jamais le webhook). Zone non liée : marqueur discret au sol (disque plat de 0,4 m + anneau fin, semi-transparent) avec le même survol ; la surface de visée est plus large que le marqueur et masquée par le relief. Clic = suivre le lien. Plus de panneau de texte permanent : le nom ne s'affiche qu'au survol ou à portée (« E : … »).
- Nouvelle option par zone « Toujours afficher le nom » (champ `showName`, décochée par défaut ; viewer, `clean_zones`, `.zones.json`, `.reglages.json`) : nom permanent au-dessus de l'élément ou du marqueur ; panneau complet pour une zone non liée de forme « panneau ».
- Viewer (édition) : cylindres conservés et toujours visibles pour toutes les zones non liées, panneaux compris (portée), contour pour les zones liées. Pas d'infobulle en édition.
- Changement de comportement : les zones non liées de forme « panneau » ne sont plus dessinées dans la page exportée sauf avec « Toujours afficher le nom ».
- La page exportée expose `window.__viewer` (comme le viewer) pour les tests.
- Tests : nouveau `tests/v24.py` (aucun mesh de cylindre, zone liée sans objet ajouté, marqueurs, infobulle avec destination exacte, webhook non affiché, marqueur masqué par le relief, clic, nom permanent, cylindres du viewer, case à cocher), en modulaire et en autonome.
- `MODE_EMPLOI.md` : nouvelle section 2 bis.

## v23 (19/10/2026)
- Viewer, clic : un clic simple sur le modèle n'a plus d'effet sur la cible caméra ni sur le cercle d'atterrissage, dans aucun mode. Il affiche le nom de l'élément ET les coordonnées du point touché (x, y, z, 2 décimales) dans « picked » et la barre d'état. Seul le double-clic choisit la cible / l'atterrissage, comme la page exportée.
- Viewer, zone : bouton « Placer ici (dernier point cliqué) » (copie x, y, z du dernier clic simple).
- Liaison à un élément : on lie le morceau réellement cliqué. Si son nom est partagé par plusieurs objets (OAR : prims répétés), la zone stocke `nom#index` (rang de l'objet parmi ceux de ce nom, ordre de parcours three.js). Nom unique : le nom seul, comme avant (zones existantes inchangées). Règle commune : `resolveMeshRef` (core.js) et `resolve_mesh_ref` (glb2html.py). glb2html.py n'ouvre pas le GLB : il ne fait que transporter la référence.
- `LINK_MAX` passe de 30 à 10 m. Refus : « Élément trop grand (L × l × h m) : probablement fusionné avec un bâtiment dans l'OAR. Délie-le dans OpenSim ou utilise une zone cercle. »
- Viewer : au chargement d'un GLB dont les réglages sont restaurés depuis le navigateur, la barre d'état dit « Réglages restaurés depuis la mémoire du navigateur (N zone(s)) ».
- Correctif : « Oublier les réglages de ce fichier » était annulé en 1,5 s par l'enregistrement automatique ; la mémoire reste maintenant vide jusqu'à la prochaine modification.
- Rotation de la région (0, 90, 180, 270°, axe vertical) : réglage `rotate` (liste dans le viewer, `--rotate` dans glb2html.py, `rotate` dans la config, `.reglages.json` et la commande générée ; relu par `--settings`). Appliquée à la racine du modèle au chargement, avant recentrage, boîte englobante, sol de promenade, trou et vignette. Changer la valeur dans le viewer fait tourner du même angle, autour du centre de la région : zones (position + orientation), arrivées, caméra, cible (donc atterrissage), dernier point cliqué, et le trou de la mer (non demandé, mais il resterait hors de l'île sinon). Zones liées : elles suivent leur élément. Les zones d'un fichier donné à `--rotate` sont déjà dans le repère tourné.
- `MODE_EMPLOI.md` mis à jour pour la v23 : clic et double-clic, « Placer ici », formats de lien web, limite de 10 m et linksets OpenSim, rotation et vignette, dépannage, nouvelle section 14 « Réglages mémorisés ».
- Tests : nouveau `tests/v23.py` (clic simple sans effet, double-clic, « Placer ici », deux meshes de même nom à 100 m, mesh de 30 m refusé, rotation 180 avec zone sur le mesh nord, mémorisation, page générée `--rotate 180` aux mêmes positions que le viewer, « Oublier »). Pour obtenir de vrais doublons de nom, le modèle de test instancie un mesh à deux primitives : three.js rend uniques les noms de nœuds (`_instance_N`), mais les enfants des clones gardent leur nom.

## v22 (19/10/2026)
- Portail interne : un portail dont la « Page de destination » est vide, ou désigne la page elle-même, pose le visiteur sur le point d'arrivée indiqué de la même région (fondu, sans rechargement : présence et chat conservés). Avant, la page restait sur un écran noir. Arrivée absente : message « Point d'arrivée … introuvable dans cette région ».
- Noyau : `teleportTo(pos, yaw)` (hors promenade : `walkStart`). Les portails « en marchant dedans » sous les pieds à l'arrivée ne se déclenchent pas tout de suite (pas de ping-pong).
- Viewer : libellé « Page de destination (adresse ou fichier .html ; vide = cette région) » ; l'aperçu applique le portail interne en promenade.
- `MODE_EMPLOI.md` : zones, arrivées, portails (même région et autre région), panneaux, liaison, zones privées, publication, dépannage.
- Tests : nouveau `tests/portail_interne.py` ; `tests/modulaire.py` attend le chargement réel des pages exportées au lieu d'un délai fixe (échouait sur une machine lente).

## v21 (19/10/2026)
- Correctif viewer, « Lier à un élément » sur un gros modèle (Atoll) : le contour affiché était un énorme cube noir ou un petit cube sous la région, et le cercle d'atterrissage pouvait se déplacer.
- Mode liaison exclusif : le noyau ignore clics, double-clics et survol pendant la liaison (le double-clic déclenchait l'atterrissage) ; il reste verrouillé 600 ms après une liaison réussie. Le mode se quitte en cliquant sur le bouton, en posant une zone ou en plaçant le trou.
- On lie le mesh nommé touché (éléments traversables ignorés), non un parent. Boîte englobante calculée en coordonnées monde après mise à jour des matrices depuis la racine (`boxOfMeshes`). Boîte vide ou non finie : élément refusé.
- Un élément de plus de 30 m est refusé avec un message ; le refus laisse le mode actif.
- Le viewer affiche le nom choisi, sa taille en mètres et un contour fil de fer. La sélection d'une zone liée contourne l'élément lui-même (la boîte du groupe de repère, non rendue, produisait le cube parasite).
- Test : modèle à racine décalée et mise à l'échelle ×2 avec voile traversable et sol géant (`tests/modulaire.py`, `test_liaison`).

## v20 (18/10/2026)
- Mode modulaire universel : la coquille `<page>.html` est la même, octet pour octet, pour toutes les régions (~85 Ko). Elle déduit ses fichiers de son propre nom (`X.html` charge `X.config.json`, `X.glb` et `X.zones.json` du même dossier) : aucun nom écrit en dur, elle se copie sous un autre nom avec ses trois fichiers frères renommés. Titre de l'onglet = champ `room` de la config, fond = `skyColor`. `lib/three-0.160.0/` contient toujours Draco et Meshopt (la coquille ne dépend plus du contenu du `.glb`).
- Zones relues à chaque rechargement : `X.zones.json`, sinon `zones.json` du même dossier, sinon aucune zone, sans erreur. Corrige la v19, où modifier `zones.json` dans le dossier du site n'avait aucun effet (les zones étaient figées dans la config). Le mode modulaire écrit les zones dans `X.zones.json`, jamais dans `config.json` (`zones: []`).
- `--config-only` ne touche pas `X.zones.json`, sauf si `--zones` est donné. `--zones-only` marche sur une page modulaire (`-o X.html --zones z.json`). Régénérer avec `--modular` sans source de zones n'écrase pas un `X.zones.json` existant.
- Viewer : bouton « Exporter la structure modulaire (.zip) » à côté de « Exporter HTML autonome » (inchangé) : `X.html`, `X.glb`, `X.config.json`, `X.zones.json`, `lib/three-0.160.0/` (`draco/` compris). Le `X.html` du zip est identique octet pour octet à celui de `glb2html.py --modular` : `build.py` prend le texte de la coquille dans `gen_tpl.py` (`build_shell`), sans le recopier.
- Zones liées à un élément du modèle (champ `mesh`, nom exact) : l'élément devient cliquable (curseur main, contour au survol), touche E à moins de `radius` mètres de l'élément, portail déclenché en s'approchant. Un élément traversable (`walkIgnore`) ne bloque pas le clic (valable pour toutes les zones). Si l'élément est introuvable dans le modèle, la zone reste à sa position.
- Viewer : boutons « Lier à un élément » (le clic ignore les éléments traversables : il lie la boîte, pas le voile transparent devant) et « Délier » dans chaque zone. `mesh` est validé dans `clean_zones`.
- `--title` et `--zones-live` sont ignorés (avec avertissement) en mode modulaire.
- Tests : nouveau `tests/modulaire.py` (coquille identique, copie renommée, rechargement des zones, secours `zones.json`, `--config-only` / `--zones-only`, zones liées, voile traversable, touche E, portail à l'approche, deux exports du viewer, zip) ; `tests/smoke.py` inchangé.

## v19 (18/10/2026)
- Mode modulaire : `--modular` écrit une coquille légère `<page>.html` (~80 Ko), `<page>.glb` (octets bruts, non encodés), `<page>.config.json` (le même `cfg` que la page autonome, zones et carte comprises) et `lib/three-0.160.0/` partagé par toutes les pages du dossier (modules à plat, décodeurs Draco/Meshopt ajoutés au besoin). La page se charge par `fetch` : elle exige http(s) (message explicatif si ouverte depuis le disque). Le mode autonome reste le défaut.
- `--config-only -o page.html` : réécrit seulement `<page>.config.json` (et `regions.json` / la page carte avec `--register` / `--map-page`), sans toucher au `.glb` ni à la coquille. Le salon (`room`) existant est conservé si `--room` n'est pas donné. Les visiteurs rechargent la page pour voir le changement.
- `build_html` est scindé : `build_cfg` fabrique le dictionnaire de réglages (commun aux deux modes) ; `build_html` accepte `modular=True`.
- Viewer : case « Mode modulaire » (ajoute `--modular` à la commande, courte ou non). L'export de page depuis le viewer reste autonome.
- `tests/smoke.py` : teste le mode modulaire sous `python -m http.server` (chargement des 3 GLB, cfg identique au mode autonome, modification de `config.json` puis rechargement, `--config-only`, config absente, ouverture depuis le disque).

## v18 (18/10/2026)
- `--settings [FICHIER]` : le script relit tous les réglages enregistrés par le viewer (trou, vagues, caméra, zones, fiche de région, vignette). La ligne de commande l'emporte sur le fichier.
- Viewer : case « Commande courte » (utilise `--settings`).
- `--register` sans `.glb` : ajoute ou met à jour une région dans `regions.json` sans rien régénérer (région d'un collègue, par exemple).
- Chaque région peut porter son propre serveur de présence (`presence`) ; la carte interroge chaque serveur.
- `--map-url` accepte plusieurs adresses séparées par des virgules (cartes de plusieurs propriétaires, fusionnées).
- `--thumb` accepte une adresse http(s) (vignette en lien).
- `--map-page` n'écrase plus la page carte par une page vide.

## v17 (18/10/2026)
- Carte : `--register`, `--region-name`, `--region-url`, `--region-xy`, `--region-spawn`, `--thumb`.
- Page web « carte des mondes » : `--map-page` (liens réels vers chaque région, compteurs de visiteurs).
- Viewer : bouton « Enregistrer la vignette (.jpg) », champ « page carte », ligne de commande avec `--register`.
- Placement compact de la carte : les grands vides entre régions sont compressés.

## v16 (18/10/2026)
- Mémorisation des réglages par fichier, carte des mondes (touche M), zones/portails, présence, chat, modération.

## v1 à v15
- Développement initial (viewer, export HTML autonome, promenade, présence). Les décisions sont dans CLAUDE.md.
