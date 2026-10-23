#!/usr/bin/env python3
"""Langue des outils Python (v36, hors navigateur) : --lang fr|en|auto, WEB3D_LANG, --help sans accents français en anglais.
Lance les outils de dist/ (fichiers autonomes) : python build.py d'abord."""
import os, re, subprocess, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
ACC = re.compile(r"[éèêëàâùûôîïçœÉÈÀÙÎÔ]")
NB = 0
def rapport(ok, msg, detail=""):
    global NB
    print(("[OK]    " if ok else "[ECHEC] ") + msg + ("" if ok else "  " + str(detail)))
    if not ok: NB += 1
def run(tool, *args, env=None):
    e = dict(os.environ); e.pop("WEB3D_LANG", None)
    for v in ("LC_ALL", "LC_MESSAGES", "LANGUAGE"): e.pop(v, None)
    e["LANG"] = "C"; e["PYTHONIOENCODING"] = "utf-8"
    e.update(env or {})
    r = subprocess.run([sys.executable, str(DIST / tool), *args], capture_output=True, text=True, encoding="utf-8", env=e, stdin=subprocess.DEVNULL)
    return r.stdout + r.stderr
for tool in ("glb2html.py", "glb2tiles.py", "oar2glb.py", "presence_server.py"):
    en = run(tool, "--lang", "en", "--help"); fr = run(tool, "--lang", "fr", "--help")
    rapport("usage:" in en and "--lang" in en, f"{tool} --lang en --help s'affiche")
    rapport(not ACC.search(en), f"{tool} --lang en --help : aucune lettre accentuée française", [l for l in en.splitlines() if ACC.search(l)][:3])
    rapport(bool(ACC.search(fr)), f"{tool} --lang fr --help : en français")
# WEB3D_LANG et priorité de --lang
a = run("glb2html.py", "--help", env={"WEB3D_LANG": "en"})
rapport(not ACC.search(a), "WEB3D_LANG=en : aide en anglais")
b = run("glb2html.py", "--help", env={"WEB3D_LANG": "en"} ) ; c = run("glb2html.py", "--lang", "fr", "--help", env={"WEB3D_LANG": "en"})
rapport(bool(ACC.search(c)), "--lang prime sur WEB3D_LANG")
d = run("glb2html.py", "--help", env={"LANG": "fr_FR.UTF-8"})
rapport(bool(ACC.search(d)), "langue du système (LANG=fr_FR) : français")
e = run("glb2html.py", "--help", env={"LANG": "de_DE.UTF-8"})
rapport(not ACC.search(e), "langue du système inconnue : anglais")
# un message d'erreur dans chaque langue
m_fr = run("glb2html.py", "--lang", "fr", "inexistant.glb"); m_en = run("glb2html.py", "--lang", "en", "inexistant.glb")
rapport("introuvable" in m_fr.lower() or "inexistant" in m_fr.lower(), "message d'erreur en français", m_fr[-200:])
rapport("not found" in m_en.lower() and not ACC.search(m_en), "message d'erreur en anglais", m_en[-200:])
print("\nRÉSULTAT :", "tout est passé" if not NB else f"{NB} échec(s)")
sys.exit(1 if NB else 0)
