# Composants tiers embarqués dans les pages générées

- **three.js** (r160) — licence MIT. Copyright © 2010-2024 three.js authors.
  Permission est accordée, gratuitement, à toute personne obtenant une copie de ce logiciel et des fichiers de documentation associés, d'utiliser, copier, modifier, fusionner, publier, distribuer, concéder en sous-licence et/ou vendre des copies du logiciel, sous réserve que la présente mention de droits d'auteur et la présente autorisation figurent dans toutes les copies ou parties substantielles du logiciel. LE LOGICIEL EST FOURNI « TEL QUEL », SANS GARANTIE D'AUCUNE SORTE. Texte officiel : https://github.com/mrdoob/three.js/blob/master/LICENSE
- **Décodeur Draco** (Google) — licence Apache 2.0 (embarqué seulement si le modèle est compressé en Draco).
- **Décodeur meshoptimizer** (Arseny Kapoulkine) — licence MIT (embarqué seulement si le modèle est compressé en Meshopt).

Ces fichiers sont téléchargés depuis jsDelivr (paquet npm `three@0.160.0`) à la fabrication ; ils ne sont pas stockés dans ce dépôt.

## Outil externe fourni dans le dépôt (pas dans les pages générées)

- **convoar** (dépôt `Misterblue/convoar`, version 2.0.6, commit `be7abbedc0d7d295a76800b2fe2e1fc9a58a7934`) — licence Apache 2.0 : convertit un OAR OpenSim en glTF pour `oar2glb.py`. Copie du dossier `dist` de ce commit dans `dist/convoar/`, **sans** les fichiers de débogage (`*.pdb`) ni la documentation XML de NLog (`NLog.xml`) ; aucun fichier n'est modifié, `SHA256SUMS.txt` donne l'empreinte de chacun et `ORIGINE.txt` la provenance. Le texte de la licence (`LICENSE`) et les licences que convoar fournit pour ses composants (`THIRDPARTYLICENSES/` : OpenSimulator, libopenmetaverse, Radegast, LookingGlass et Intel, licences BSD à trois clauses ; InWorldz.PrimExporter, Apache 2.0) sont dans le même dossier, comme ces licences le demandent pour une redistribution en binaire. Les autres composants embarqués par convoar (par exemple NLog, Mono.Addins, Nini, log4net, SmartThreadPool, nunit, openjpeg, zlib.net et les assemblages `System.*`) n'ont pas de licence fournie par convoar : **leurs licences n'ont pas été vérifiées une à une**. Windows seulement (.NET Framework 4.8).
