REGION CLE EN MAIN / TURNKEY REGION
===================================

FRANCAIS
--------
Votre region OpenSim (un fichier GLB) dans un navigateur, sans rien installer pour la visiter.
Produite avec Web_3d (https://github.com/Klaatou/Web_3d, licence MIT).

Pour commencer
  (Vous avez deja ce paquet ? Ne dezippez pas le nouveau zip par-dessus votre dossier : il ecraserait votre config, vos zones et vos images.
   Dezippez-le a part : voir "Mettre a jour un paquet deja publie" plus bas.)
  1. Windows : double-cliquez sur lancer-region.bat : une petite region d'exemple s'ouvre dans le
     navigateur. Laissez ouverte la fenetre noire qui affiche "Region sur http://localhost:8000/ - fermez
     cette fenetre pour arreter." tant que vous regardez la region (le numero peut etre un autre que
     8000 si 8000 est deja pris).
     Linux et macOS : ouvrez un terminal dans ce dossier et tapez  sh lancer-region.sh  (il faut Python 3.7
     ou plus ; arret : Ctrl+C). macOS : on peut aussi double-cliquer sur lancer-region.command (la premiere
     fois : clic droit, Ouvrir). L'adresse http://localhost:8000/ s'affiche alors dans le terminal.
     (Lanceur macOS essaye par un testeur sous macOS Ventura 13.7.8, avec Firefox 159.0.1 :
     la region s'affiche.)
  2. Adresses utiles (avec le numero de la fenetre noire) :
       http://localhost:8000/                la region
       http://localhost:8000/aide.html       l'aide des visiteurs (a adapter a votre region)
       http://localhost:8000/readme.html   la documentation du createur : tout y est detaille
       http://localhost:8000/carte.html    la carte de votre region (page de presentation : nom, vignette)
       (la carte : remplacez site/vignette.jpg - carre, 320 x 320 pixels - et changez le nom affiche dans site/regions.json ; voir readme.html, section 10)
  3. Dans la region 3D, l'aide s'ouvre en cliquant sur le petit panneau "?" du mur est de la maison
     d'exemple (visible en promenade). A REVOIR avec votre propre GLB : ce panneau flotterait dans le
     vide. Supprimez-le (remplacez le contenu de site/region.zones.json par []) ou deplacez-le avec le
     viewer : voir readme.html, section 8.
     Un second panneau, "Lien vers OpenSim" (lien hop://, image site/medias/hop.jpg), est un exemple a personnaliser :
     readme.html, section 8, explique comment changer l'image, la position et l'adresse.
  4. Mettez VOTRE GLB dans le dossier site sous le nom region.glb (il remplace l'exemple), puis F5.
  5. Un autre nom que "region" ? Double-cliquez sur renommer-region.bat (macOS : renommer-region.command ; Linux : sh renommer-region.sh NOUVEAU_NOM).

Dossiers
  site/       tout ce qui se publie : copiez le CONTENU de ce dossier sur un hebergement web
              La carte (carte.html) est publiee avec le reste : une fois en ligne, elle est a l'adresse https://VOTRE-SITE/carte.html ; il suffit d'adapter la vignette site/vignette.jpg et le nom dans site/regions.json.
  presence/   le serveur de presence (facultatif : voir les autres visiteurs, chat)
  lancer-region.bat, renommer-region.bat   lanceur et renommage (Windows)
  lancer-region.sh, renommer-region.sh et les .command   les memes, pour Linux et macOS
Double-cliquer sur site/index.html ne marche pas : un message demande un serveur web.

Mettre a jour un paquet deja publie (nouvelle version)
  Telechargez le nouveau zip, dezippez-le a part, puis copiez dans votre dossier site/ publie SEULEMENT index.html et carte.html. Publiez, puis Ctrl+F5 dans la page.
  Ne remplacez pas : la config (region.config.json), les zones (region.zones.json), le modele (region.glb), medias/, regions.json, vignette.jpg, ni aide.html si vous l'avez adaptee.
  Dossier lib/ : seulement si le nouveau zip a un autre dossier lib/three-... que le votre.
  Version affichee (touche I, ligne "Version") : "page" est celle de index.html ; "configuration" est la cle "version" de region.config.json, a changer a la main si vous voulez (le numero est dans VERSION.txt du zip).
  Serveur de presence : remplacez presence/presence_server.py et relancez-le.
  Paquet d'avant la 1.5.0 : copiez aussi regions.json et vignette.jpg du nouveau zip et adaptez-les (la carte en a besoin).

ENGLISH
-------
Your OpenSim region (a GLB file) in a browser, with nothing to install to visit it.
Made with Web_3d (https://github.com/Klaatou/Web_3d, MIT licence).

To start
  (Already have this package? Do not unzip the new zip over your folder: it would overwrite your config, your zones and your images.
   Unzip it somewhere else: see "Updating a package that is already published" below.)
  1. Windows: double-click lancer-region.bat: a small example region opens in the browser. Keep open
     the black window that shows "Region sur http://localhost:8000/ - fermez cette fenetre pour
     arreter." while you look at the region (the number may differ from 8000 if 8000 is already taken).
     Linux and macOS: open a terminal in this folder and type  sh lancer-region.sh  (Python 3.7 or later
     is needed; stop with Ctrl+C). macOS: you can also double-click lancer-region.command (the first time:
     right-click, Open). The address http://localhost:8000/ is then shown in the terminal.
     (macOS launcher tried by a tester on macOS Ventura 13.7.8, with Firefox 159.0.1:
     the region is displayed.)
  2. Useful addresses (with the number from the black window):
       http://localhost:8000/                the region
       http://localhost:8000/aide.html       the visitors' help (to adapt to your region)
       http://localhost:8000/readme.html   the creator's documentation: everything is detailed there
       http://localhost:8000/carte.html    the map of your region (a presentation page: name, thumbnail)
       (map: replace site/vignette.jpg - square, 320 x 320 pixels - and change the displayed name in site/regions.json; see readme.html, section 10)
  3. In the 3D region, the help opens by clicking the small "?" panel on the east wall of the example
     house (visible while walking). TO REVIEW with your own GLB: that panel would float in empty space.
     Delete it (replace the contents of site/region.zones.json with []) or move it with the viewer:
     see readme.html, section 8.
     A second panel, "Lien vers OpenSim" (hop:// link, image site/medias/hop.jpg), is an example to customise:
     readme.html, section 8, explains how to change the image, the position and the address.
  4. Put YOUR GLB in the site folder under the name region.glb (it replaces the example), then F5.
  5. A name other than "region"? Double-click renommer-region.bat (macOS: renommer-region.command; Linux: sh renommer-region.sh NEW_NAME).

Folders
  site/       everything that gets published: copy the CONTENTS of this folder to a web host
              The map (carte.html) is published with the rest: once online, it is at https://YOUR-SITE/carte.html; you only need to adapt the thumbnail site/vignette.jpg and the name in site/regions.json.
  presence/   the presence server (optional: see other visitors, chat)
  lancer-region.bat, renommer-region.bat   launcher and renaming (Windows)
  lancer-region.sh, renommer-region.sh and the .command files   the same, for Linux and macOS
Double-clicking site/index.html does not work: a message asks for a web server.

Updating a package that is already published (new version)
  Download the new zip, unzip it somewhere else, then copy into your published site/ folder ONLY index.html and carte.html. Publish, then Ctrl+F5 in the page.
  Do not replace: the config (region.config.json), the zones (region.zones.json), the model (region.glb), medias/, regions.json, vignette.jpg, nor aide.html if you adapted it.
  lib/ folder: only if the new zip has a different lib/three-... folder from yours.
  Displayed version (I key, "Version" line): "page" is that of index.html; "configuration" is the "version" key of region.config.json, to change by hand if you wish (the number is in VERSION.txt of the zip).
  Presence server: replace presence/presence_server.py and restart it.
  Package from before 1.5.0: also copy regions.json and vignette.jpg from the new zip and adapt them (the map needs them).
