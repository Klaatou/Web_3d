"""vider_tube.py : aide des tests (ce n'est pas un test ; tout.py le saute).

Sous Windows, un tube ne garde que 4 Ko (voir DEVELOPPEMENT.md) : un programme dont personne ne lit la sortie finit par se bloquer sur son prochain
« print ». Le serveur de presence lance par un test avec stdout=PIPE etait dans ce cas : au bout d'une quinzaine de visites (environ 240 octets
chacune), il ne repondait plus (« timed out during opening handshake », page jamais « en ligne »).

vider(proc) lit en continu la sortie d'un Popen(stdout=PIPE, text=True) dans un fil. proc.stdout.read() et proc.communicate() rendent ensuite tout ce
qui a ete lu : les tests qui relisent la sortie du serveur a la fin continuent de marcher.
"""
import threading


class _Sortie:
    def __init__(self, flux):
        self.flux, self.morceaux, self.fini = flux, [], threading.Event()
        threading.Thread(target=self._lire, daemon=True).start()

    def _lire(self):
        try:
            for ligne in iter(self.flux.readline, ""):
                self.morceaux.append(ligne)
        except (OSError, ValueError):
            pass
        finally:
            self.fini.set()

    def texte(self, attente=10):
        self.fini.wait(attente)           # apres un kill ou un terminate, le flux se ferme : la lecture se termine
        return "".join(self.morceaux)

    def read(self, *_):
        return self.texte()


def vider(proc):
    sortie = _Sortie(proc.stdout)

    def communicate(timeout=None, input=None):
        proc.wait(timeout=timeout)
        return sortie.texte(), None
    proc.stdout, proc.communicate = sortie, communicate
    return proc
