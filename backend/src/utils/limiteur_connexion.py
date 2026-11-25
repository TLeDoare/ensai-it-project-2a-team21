"""Limite le nombre d'essais de connexion ratés pour une même adresse e-mail (constat d'audit ER3-04)."""

import time


class LimiteurConnexion:
    """Compte les échecs de connexion par e-mail et bloque l'adresse après trop d'échecs rapprochés.

    Les compteurs sont gardés en mémoire : ils repartent de zéro au redémarrage de l'API,
    ce qui suffit à rendre une attaque par force brute beaucoup trop lente.
    """

    MAX_ECHECS = 5  # nombre d'échecs tolérés...
    FENETRE = 15 * 60  # ... sur 15 minutes (en secondes)
    DUREE_BLOCAGE = 15 * 60  # durée du blocage une fois la limite atteinte (en secondes)

    def __init__(self, horloge=time.monotonic):
        # horloge est remplaçable dans les tests, pour simuler le temps qui passe
        self.horloge = horloge
        self.echecs = {}  # e-mail -> dates des échecs récents
        self.bloque_jusqu_a = {}  # e-mail -> fin du blocage

    @staticmethod
    def _cle(email: str) -> str:
        # « A@a.com » et « a@a.com » désignent le même compte
        return email.strip().lower()

    def est_bloque(self, email: str) -> bool:
        """Renvoie True si l'adresse est bloquée en ce moment."""
        fin = self.bloque_jusqu_a.get(self._cle(email))
        return fin is not None and self.horloge() < fin

    def enregistrer_echec(self, email: str) -> bool:
        """Note un échec ; au MAX_ECHECS-ième échec dans la fenêtre, l'adresse est bloquée.

        Renvoie True seulement quand cet échec déclenche le blocage, pour que le service puisse l'écrire dans le log.
        """
        cle = self._cle(email)
        maintenant = self.horloge()
        # On ne garde que les échecs encore dans la fenêtre de 15 minutes
        recents = [t for t in self.echecs.get(cle, []) if maintenant - t < self.FENETRE]
        recents.append(maintenant)
        self.echecs[cle] = recents
        if len(recents) >= self.MAX_ECHECS:
            self.bloque_jusqu_a[cle] = maintenant + self.DUREE_BLOCAGE
            self.echecs[cle] = []
            return True
        return False

    def reinitialiser(self, email: str) -> None:
        """Efface les échecs d'une adresse après une connexion réussie."""
        cle = self._cle(email)
        self.echecs.pop(cle, None)
        self.bloque_jusqu_a.pop(cle, None)


# Instance unique, partagée par toutes les requêtes de l'API
limiteur_connexion = LimiteurConnexion()
