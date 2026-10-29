#!/usr/bin/env python3
"""Tests : adresses IPv6 groupees par prefixe /64 pour la limite par adresse et les bannissements (vrai presence_server.py).

Un abonne a plusieurs adresses IPv6 (et elles changent) : compter ou bannir l'adresse exacte se contournait en changeant la fin de l'adresse.
Verifie : la fonction ip_group ; --max-per-ip (deux adresses d'un meme /64 = une seule ; un autre /64 passe ; IPv4 inchange ; IPv4 ecrit en IPv6 = l'IPv4) ;
un bannissement d'un visiteur IPv6 vaut pour tout son /64 et pas pour un autre.
Les adresses des visiteurs sont donnees par l'en-tete X-Forwarded-For (--proxy-header), comme derriere Tailscale Funnel.

Prerequis : pip install websockets ; python build.py avant. Lancer : python tests/ipv6.py
"""
import asyncio, importlib.util, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h37 import *
import h37
import websockets

print("--- 1. la fonction ip_group")
spec = importlib.util.spec_from_file_location("ps", str(DIST / "presence_server.py"))
ps = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ps)
for a, b in (("203.0.113.5", "203.0.113.5"), ("::ffff:203.0.113.5", "203.0.113.5"), ("2001:db8:aaaa:bbbb::1", "2001:db8:aaaa:bbbb::/64"),
             ("2001:DB8:AAAA:BBBB:1234:5678:9abc:def0", "2001:db8:aaaa:bbbb::/64"), ("fe80::1%eth0", "fe80::/64"), ("?", "?"), ("pas une adresse", "pas une adresse")):
    rapport(ps.ip_group(a) == b, f"ip_group({a!r}) = {b!r}", ps.ip_group(a))

port = port_libre()
sortie = open(tmp / "sortie.txt", "w", encoding="utf-8")
proc = subprocess.Popen([sys.executable, str(DIST / "presence_server.py"), "--lang", "fr", "--host", "127.0.0.1", "--port", str(port), "--identities", "", "--bans", str(tmp / "bans.json"),
                         "--max-per-ip", "1", "--proxy-header", "X-Forwarded-For", "--log-ip", "raw"],
                        stdin=subprocess.PIPE, stdout=sortie, stderr=subprocess.STDOUT, text=True, env=dict(os.environ, PYTHONUNBUFFERED="1"))
attendre_port(port, proc, "presence_server")


async def venir(ip, uid, name="T", spectator=True):
    ws = await websockets.connect(f"ws://127.0.0.1:{port}", additional_headers={"X-Forwarded-For": ip})
    try:
        await ws.send(json.dumps({"t": "hello", "room": "salon", "name": name, "uid": uid, "spectator": spectator}))
    except websockets.exceptions.ConnectionClosed:      # « full » ou « banned » : le serveur ferme aussitot, le message reste lisible
        pass
    return ws, json.loads(await asyncio.wait_for(ws.recv(), 5))


def uid(n):
    return f"{n:020x}"


async def main():
    print("--- 2. --max-per-ip 1 : une seule connexion par adresse, l'IPv6 comptee par /64")
    ouverts = []
    ws, m = await venir("2001:db8:aaaa:bbbb::1", uid(1)); ouverts.append(ws)
    rapport(m.get("t") == "welcome", "premiere connexion IPv6 : accueillie", m)
    ws, m = await venir("2001:db8:aaaa:bbbb:1234:5678:9abc:def0", uid(2)); ouverts.append(ws)
    rapport(m.get("t") == "full", "autre adresse du meme /64 : refusee (limite par adresse)", m)
    ws, m = await venir("2001:db8:aaaa:cccc::1", uid(3)); ouverts.append(ws)
    rapport(m.get("t") == "welcome", "adresse d'un autre /64 : accueillie", m)
    ws, m = await venir("203.0.113.5", uid(4)); ouverts.append(ws)
    rapport(m.get("t") == "welcome", "IPv4 : premiere connexion accueillie", m)
    ws, m = await venir("203.0.113.5", uid(5)); ouverts.append(ws)
    rapport(m.get("t") == "full", "IPv4 : la meme adresse deux fois est refusee (inchange)", m)
    ws, m = await venir("::ffff:203.0.113.5", uid(6)); ouverts.append(ws)
    rapport(m.get("t") == "full", "IPv4 ecrite en IPv6 (::ffff:...) : comptee comme l'IPv4", m)
    ws, m = await venir("203.0.113.6", uid(7)); ouverts.append(ws)
    rapport(m.get("t") == "welcome", "IPv4 voisine : accueillie", m)
    for w in ouverts:
        await w.close()
    await asyncio.sleep(0.8)

    print("--- 3. un bannissement vaut pour tout le /64")
    ws, m = await venir("2001:db8:aaaa:bbbb::1", uid(10), name="Mauvais", spectator=False)
    rapport(m.get("t") == "welcome", "le futur banni se connecte", m)
    proc.stdin.write(f"bannir {m['id']} 60 test\n"); proc.stdin.flush()
    await asyncio.sleep(1.0)
    ws2, m2 = await venir("2001:db8:aaaa:bbbb:9999::7", uid(11))
    rapport(m2.get("t") == "banned", "une autre adresse du meme /64 est refusee comme bannie", m2)
    ws3, m3 = await venir("2001:db8:aaaa:dddd::1", uid(12))
    rapport(m3.get("t") == "welcome", "un autre /64 n'est pas touche", m3)
    await ws3.close(); await asyncio.sleep(0.3)
    ws4, m4 = await venir("203.0.113.9", uid(13))
    rapport(m4.get("t") == "welcome", "une IPv4 n'est pas touchee", m4)
    for w in (ws, ws2, ws4):
        try:
            await w.close()
        except Exception:
            pass


try:
    asyncio.run(main())
finally:
    proc.terminate()
    try:
        proc.wait(5)
    except Exception:
        proc.kill()
    sortie.close()
print("\nRÉSULTAT : " + ("tout est passé" if not h37.resultat() else f"{h37.resultat()} échec(s)"))
sys.exit(1 if h37.resultat() else 0)
