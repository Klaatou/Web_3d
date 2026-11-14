**Web_3d 1.11.0: radio zones, metallic reflections, lighter textures, automatic sea, `oars2site.py`**

### What's new

**1. Radio zones** (manual § 5.19)
- A new zone type `cast` plays an Icecast / SHOUTcast stream while walking within range, louder when closer; one radio at a time, stopped out of range and in the global view.
- The track title is shown when the presence server reads it in the stream (`--radios FILE`, manual § 10.25).
- The "Radio" line of the State block says why a stream does not play (mixed content, refused or unreadable stream).

**2. Web page**
- Metallic reflections: new "Metallic reflections" slider in Settings (0 % by default; the page offers 60 % when the region has metals; § 7.65); diagnostic shown in a resizable window (§ 7.53).
- Automatic sea: `oar2glb.py` reads the region's water height from the OAR and the page starts at it (`seaM`; `--sea-m`, `--water-from` to fix a region already converted; § 3.13).
- `url` zones open on entering (`trigger` `enter` / `both`, `hop://` in the same tab); `cone` key per zone (§ 5.7.1).
- `--no-credit` removes the "Made with Web_3d" icon; the world map remembers the nicknames key (§ 9.16).

**3. Conversion tools**
- Lighter textures: `oar2glb.py --tex-size`, `--tex-quality`, `--tex-only GLB` (on a GLB already made), table of texture sizes, `glb-stats.py` (§ 3.12).
- New `oars2site.py`: a folder of OARs becomes a complete site, one region after another, with the world map (`CONVERT_OARS.md`).
- Python 3.14: `glb2html.py` opens again. Tools no longer stop on a redirected output on Windows.

**4. Graphical launcher** (§ 3.9)
- Project icon, `glb-stats.py` in the list, "Function" line, File / Folder buttons for `OAR` and `GLB` parameters, no "press Enter" after `--help`.

**5. Presence server** (§ 10)
- Bounded nickname registry (`--max-names`), last address of the relay header, no more `KeyError` on simultaneous disconnections, visits log with the nicknames of visitors in the global view (`--visits-names`).
- Silent walker: a walker whose page is in the background is no longer counted nor shown after `--idle-walk` minutes (3 by default, `0` = never; § 10.26).
- Security review of the pages and the server (no page flaw found).

**6. Documentation**
- Manual § 3.12, § 3.13, § 5.19, § 7.65, § 10.25, § 10.26; `CONVERT_OARS.md`; simple procedures § 12 to § 14; `REFERENCE_JSON.md` (`cast` zones, `seaM`, `credit`).

### Updating

- If you already have one of the packages, copy only `index.html` and `carte.html` into your folder.
- Do not unzip the new zip over it: that would overwrite your configuration, zones and images.
- Presence server hosts: replace `presence_server.py` and restart it; the new options are optional.

---

**Web_3d 1.11.0 : zones radio, reflets métalliques, textures allégées, mer automatique, `oars2site.py`**

### Nouveautés

**1. Zones radio** (manuel § 5.19)
- Un nouveau type de zone `cast` joue un flux Icecast / SHOUTcast en promenade à portée, plus fort quand on s'approche ; une radio à la fois, arrêtée hors de portée et en vue globale.
- Le titre du morceau s'affiche quand le serveur de présence le lit dans le flux (`--radios FICHIER`, manuel § 10.25).
- La ligne « Radio » du bloc État dit pourquoi un flux ne joue pas (contenu mixte, flux refusé ou illisible).

**2. Page web**
- Reflets métalliques : nouveau curseur « Reflets métalliques » dans Réglages (0 % par défaut ; la page propose 60 % quand la région a des métaux ; § 7.65) ; diagnostic affiché dans une fenêtre redimensionnable (§ 7.53).
- Mer automatique : `oar2glb.py` lit le niveau d'eau de la région dans l'OAR et la page démarre à ce niveau (`seaM` ; `--sea-m`, `--water-from` pour corriger une région déjà convertie ; § 3.13).
- Les zones `url` s'ouvrent en entrant (`trigger` `enter` / `both`, `hop://` dans le même onglet) ; clé `cone` par zone (§ 5.7.1).
- `--no-credit` retire l'icône « Réalisé avec Web_3d » ; la carte des mondes mémorise la clé des pseudos (§ 9.16).

**3. Outils de conversion**
- Textures allégées : `oar2glb.py --tex-size`, `--tex-quality`, `--tex-only GLB` (sur un GLB déjà fait), tableau des tailles de textures, `glb-stats.py` (§ 3.12).
- Nouvel outil `oars2site.py` : un dossier d'OAR devient un site complet, une région après l'autre, avec la carte des mondes (`CONVERTIR_OARS.md`).
- Python 3.14 : `glb2html.py` s'ouvre de nouveau. Les outils ne s'arrêtent plus sur une sortie redirigée sous Windows.

**4. Lanceur graphique** (§ 3.9)
- Icône du projet, `glb-stats.py` dans la liste, ligne « Fonction », boutons Fichier / Dossier pour les paramètres `OAR` et `GLB`, plus de « Entrée » après `--help`.

**5. Serveur de présence** (§ 10)
- Registre des pseudos borné (`--max-names`), dernière adresse de l'en-tête du relais, plus de `KeyError` à des déconnexions simultanées, journal des visites avec les pseudos des visiteurs en vue globale (`--visits-names`).
- Promeneur muet : un promeneur dont la page est en arrière-plan n'est plus compté ni montré après `--idle-walk` minutes (3 par défaut, `0` = jamais ; § 10.26).
- Audit de sécurité des pages et du serveur (aucune faille trouvée dans les pages).

**6. Documentation**
- Manuel § 3.12, § 3.13, § 5.19, § 7.65, § 10.25, § 10.26 ; `CONVERTIR_OARS.md` ; procédures simples § 12 à § 14 ; `REFERENCE_JSON.md` (zones `cast`, `seaM`, `credit`).

### Mise à jour

- Si vous avez déjà un des paquets, copiez seulement `index.html` et `carte.html` dans votre dossier.
- Ne dézippez pas le nouveau zip par-dessus : cela écraserait votre configuration, vos zones et vos images.
- Hébergeurs d'un serveur de présence : remplacez `presence_server.py` et relancez-le ; les nouvelles options sont facultatives.
