GALERIE DE PHOTOS 3D / 3D PHOTO GALLERY
=======================================

FRANCAIS
--------
Une galerie de photos en 3D qui s'ouvre dans le navigateur, sans rien installer.
Produite avec Web_3d (https://github.com/Klaatou/Web_3d, licence MIT).

Pour commencer
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
  5. Un autre nom que "galerie" ? Double-cliquez sur renommer-galerie.bat (macOS : renommer-galerie.command ; Linux : sh renommer-galerie.sh NOUVEAU_NOM).

Dossiers
  site/       tout ce qui se publie : copiez le CONTENU de ce dossier sur un hebergement web
  presence/   le serveur de presence (facultatif : voir les autres visiteurs, chat)
  lancer-galerie.bat, renommer-galerie.bat   lanceur et renommage (Windows)
  lancer-galerie.sh, renommer-galerie.sh et les .command   les memes, pour Linux et macOS
Double-cliquer sur site/index.html ne marche pas : un message demande un serveur web.

ENGLISH
-------
A 3D photo gallery that opens in the browser, nothing to install.
Made with Web_3d (https://github.com/Klaatou/Web_3d, MIT licence).

To start
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
  5. A name other than "galerie"? Double-click renommer-galerie.bat (macOS: renommer-galerie.command; Linux: sh renommer-galerie.sh NEW_NAME).

Folders
  site/       everything that gets published: copy the CONTENTS of this folder to a web host
  presence/   the presence server (optional: see other visitors, chat)
  lancer-galerie.bat, renommer-galerie.bat   launcher and renaming (Windows)
  lancer-galerie.sh, renommer-galerie.sh and the .command files   the same, for Linux and macOS
Double-clicking site/index.html does not work: a message asks for a web server.
