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
     (Les lanceurs macOS n'ont pas encore ete essayes sur un Mac.)
  2. La galerie s'ouvre dans le navigateur. Adresses utiles (avec le numero de la fenetre noire) :
       http://localhost:8000/               la galerie
       http://localhost:8000/aide.html      l'aide des visiteurs (a adapter a votre galerie)
       http://localhost:8000/galerie.html   la documentation du createur : tout y est detaille
  3. Dans la galerie 3D, l'aide s'ouvre en cliquant sur le petit panneau "?" au devant du comptoir.
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
     (The macOS launchers have not been tried on a Mac yet.)
  2. The gallery opens in the browser. Useful addresses (with the number from the black window):
       http://localhost:8000/               the gallery
       http://localhost:8000/aide.html      the visitors' help (to adapt to your gallery)
       http://localhost:8000/galerie.html   the creator's documentation: everything is detailed there
  3. In the 3D gallery, the help opens by clicking the small "?" panel on the front of the counter.
  4. Replace the photos in site/medias/: 1.jpg to 30.jpg, LOWERCASE names.
  5. A name other than "galerie"? Double-click renommer-galerie.bat (macOS: renommer-galerie.command; Linux: sh renommer-galerie.sh NEW_NAME).

Folders
  site/       everything that gets published: copy the CONTENTS of this folder to a web host
  presence/   the presence server (optional: see other visitors, chat)
  lancer-galerie.bat, renommer-galerie.bat   launcher and renaming (Windows)
  lancer-galerie.sh, renommer-galerie.sh and the .command files   the same, for Linux and macOS
Double-clicking site/index.html does not work: a message asks for a web server.
