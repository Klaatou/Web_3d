GALERIE DE PHOTOS 3D / 3D PHOTO GALLERY
=======================================

FRANCAIS
--------
Une galerie de photos en 3D qui s'ouvre dans le navigateur, sans rien installer.
Produite avec Web_3d (https://github.com/Klaatou/Web_3d, licence MIT).

Pour commencer
  (Vous avez deja ce paquet ? Ne dezippez pas le nouveau zip par-dessus votre dossier : il ecraserait votre config, vos zones et vos images.
   Dezippez-le a part : voir "Mettre a jour un paquet deja publie" plus bas.)
  1. Windows : double-cliquez sur lancer-galerie.bat. Laissez ouverte la fenetre noire qui affiche
     "Galerie sur http://localhost:8000/ - fermez cette fenetre pour arreter." tant que vous regardez la
     galerie (le numero peut etre un autre que 8000 si 8000 est deja pris).
     Linux et macOS : ouvrez un terminal dans ce dossier et tapez  sh lancer-galerie.sh  (il faut Python 3.7
     ou plus ; arret : Ctrl+C). macOS : on peut aussi double-cliquer sur lancer-galerie.command (la premiere
     fois : clic droit, Ouvrir). L'adresse http://localhost:8000/ s'affiche alors dans le terminal.
     (Meme lanceur que celui du paquet region-simple, qu'un testeur a essaye sous macOS Ventura
     13.7.8 avec Firefox 159.0.1 : la region s'affiche. Ce paquet-ci n'a pas ete essaye separement.)
  2. La galerie s'ouvre dans le navigateur. Adresses utiles (avec le numero de la fenetre noire) :
       http://localhost:8000/               la galerie
       http://localhost:8000/aide.html      l'aide des visiteurs (a adapter a votre galerie)
       http://localhost:8000/galerie.html   la documentation du createur : tout y est detaille
       http://localhost:8000/carte.html     la carte de votre galerie (page de presentation : nom, vignette)
       (la carte : remplacez site/vignette.jpg - carre, 320 x 320 pixels - et changez le nom affiche dans site/regions.json ; voir galerie.html, section 8)
  3. Dans la galerie 3D, l'aide s'ouvre en cliquant sur le petit panneau "?" au devant du comptoir.
     Un second panneau, "Lien vers OpenSim" (lien hop://, image site/medias/hop.jpg), est un exemple a personnaliser :
     galerie.html, section 4, explique comment changer l'image, la position et l'adresse.
  4. Remplacez les photos de site/medias/ : 1.jpg a 30.jpg, noms en MINUSCULES.
     Un GIF anime marche aussi : posez-le dans site/medias/ sous le meme numero (30.gif) et retirez 30.jpg. La zone 30 a pour cible "30" :
     la page essaie jpg, jpeg, png, webp, gif puis avif, dans cet ordre. (Si une cible de galerie.zones.json porte une extension, par exemple
     "30.jpg", changez-la en "30.gif".) Il s'anime avec le index.html de la version 1.6.15 ou plus recente.
  5. Un autre nom que "galerie" ? Double-cliquez sur renommer-galerie.bat (macOS : renommer-galerie.command ; Linux : sh renommer-galerie.sh NOUVEAU_NOM).

Dossiers
  site/       tout ce qui se publie : copiez le CONTENU de ce dossier sur un hebergement web
              La carte (carte.html) est publiee avec le reste : une fois en ligne, elle est a l'adresse https://VOTRE-SITE/carte.html ; il suffit d'adapter la vignette site/vignette.jpg et le nom dans site/regions.json.
  presence/   le serveur de presence (facultatif : voir les autres visiteurs, chat)
  lancer-galerie.bat, renommer-galerie.bat   lanceur et renommage (Windows)
  lancer-galerie.sh, renommer-galerie.sh et les .command   les memes, pour Linux et macOS
Double-cliquer sur site/index.html ne marche pas : un message demande un serveur web.

Mettre a jour un paquet deja publie (nouvelle version)
  Telechargez le nouveau zip, dezippez-le a part, puis copiez dans votre dossier site/ publie SEULEMENT index.html et carte.html. Publiez, puis Ctrl+F5 dans la page.
  Ne remplacez pas : la config (galerie.config.json), les zones (galerie.zones.json), le modele (galerie.glb), medias/, regions.json, vignette.jpg, ni aide.html si vous l'avez adaptee.
  Dossier lib/ : seulement si le nouveau zip a un autre dossier lib/three-... que le votre.
  favicon.ico : recopiez-le seulement si vous n'avez pas pose le votre (un favicon.ico deja a cote de la page est prefere a l'icone incorporee).
  Version affichee (touche I, ligne "Version") : "page" est celle de index.html ; "configuration" est la cle "version" de galerie.config.json, a changer a la main si vous voulez (le numero est dans VERSION.txt du zip).
  Serveur de presence : remplacez presence/presence_server.py et relancez-le.
  Paquet d'avant la 1.5.0 : copiez aussi regions.json et vignette.jpg du nouveau zip et adaptez-les (la carte en a besoin).

ENGLISH
-------
A 3D photo gallery that opens in the browser, nothing to install.
Made with Web_3d (https://github.com/Klaatou/Web_3d, MIT licence).

To start
  (Already have this package? Do not unzip the new zip over your folder: it would overwrite your config, your zones and your images.
   Unzip it somewhere else: see "Updating a package that is already published" below.)
  1. Windows: double-click lancer-galerie.bat. Keep open the black window that shows
     "Galerie sur http://localhost:8000/ - fermez cette fenetre pour arreter." while you look at the
     gallery (the number may differ from 8000 if 8000 is already taken).
     Linux and macOS: open a terminal in this folder and type  sh lancer-galerie.sh  (Python 3.7 or later
     is needed; stop with Ctrl+C). macOS: you can also double-click lancer-galerie.command (the first time:
     right-click, Open). The address http://localhost:8000/ is then shown in the terminal.
     (Same launcher as the region-simple package, which a tester tried on macOS Ventura 13.7.8
     with Firefox 159.0.1: the region is displayed. This package itself has not been tried separately.)
  2. The gallery opens in the browser. Useful addresses (with the number from the black window):
       http://localhost:8000/               the gallery
       http://localhost:8000/aide.html      the visitors' help (to adapt to your gallery)
       http://localhost:8000/galerie.html   the creator's documentation: everything is detailed there
       http://localhost:8000/carte.html     the map of your gallery (a presentation page: name, thumbnail)
       (map: replace site/vignette.jpg - square, 320 x 320 pixels - and change the displayed name in site/regions.json; see galerie.html, section 8)
  3. In the 3D gallery, the help opens by clicking the small "?" panel on the front of the counter.
     A second panel, "Lien vers OpenSim" (hop:// link, image site/medias/hop.jpg), is an example to customise:
     galerie.html, section 4, explains how to change the image, the position and the address.
  4. Replace the photos in site/medias/: 1.jpg to 30.jpg, LOWERCASE names.
     An animated GIF works too: put it in site/medias/ under the same number (30.gif) and remove 30.jpg. Zone 30 has the target "30":
     the page tries jpg, jpeg, png, webp, gif then avif, in that order. (If a target in galerie.zones.json carries an extension, for example
     "30.jpg", change it to "30.gif".) It animates with the index.html of version 1.6.15 or later.
  5. A name other than "galerie"? Double-click renommer-galerie.bat (macOS: renommer-galerie.command; Linux: sh renommer-galerie.sh NEW_NAME).

Folders
  site/       everything that gets published: copy the CONTENTS of this folder to a web host
              The map (carte.html) is published with the rest: once online, it is at https://YOUR-SITE/carte.html; you only need to adapt the thumbnail site/vignette.jpg and the name in site/regions.json.
  presence/   the presence server (optional: see other visitors, chat)
  lancer-galerie.bat, renommer-galerie.bat   launcher and renaming (Windows)
  lancer-galerie.sh, renommer-galerie.sh and the .command files   the same, for Linux and macOS
Double-clicking site/index.html does not work: a message asks for a web server.

Updating a package that is already published (new version)
  Download the new zip, unzip it somewhere else, then copy into your published site/ folder ONLY index.html and carte.html. Publish, then Ctrl+F5 in the page.
  Do not replace: the config (galerie.config.json), the zones (galerie.zones.json), the model (galerie.glb), medias/, regions.json, vignette.jpg, nor aide.html if you adapted it.
  lib/ folder: only if the new zip has a different lib/three-... folder from yours.
  favicon.ico: copy it only if you have not placed your own (a favicon.ico already next to the page is preferred to the embedded icon).
  Displayed version (I key, "Version" line): "page" is that of index.html; "configuration" is the "version" key of galerie.config.json, to change by hand if you wish (the number is in VERSION.txt of the zip).
  Presence server: replace presence/presence_server.py and restart it.
  Package from before 1.5.0: also copy regions.json and vignette.jpg from the new zip and adapt them (the map needs them).
