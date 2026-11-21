#!/usr/bin/env python3
"""Aide des tests video (zone_video, zone_video_liste) : trouve ffmpeg.

Ordre : le PATH ; sinon le fichier tests/ffmpeg.chemin.txt (une ligne : le chemin complet de ffmpeg.exe ; fichier personnel, ignore par git).
Renvoie le chemin de ffmpeg, ou None s'il est introuvable. Ce module n'est pas un test (tout.py ne le lance pas).
"""
import pathlib, shutil


def trouver():
    chemin = shutil.which("ffmpeg")
    if chemin:
        return chemin
    fichier = pathlib.Path(__file__).resolve().parent / "ffmpeg.chemin.txt"
    if fichier.is_file():
        texte = fichier.read_text(encoding="utf-8-sig").strip().strip('"')   # Set-Content de PowerShell peut ajouter une marque d'ordre des octets
        if texte and pathlib.Path(texte).is_file():
            return texte
    return None
