from abc import ABC, abstractmethod

from ..types import Positions


class RedactorStrategy(ABC):
    """Interface abstraite pour les stratégies de caviardage"""

    @abstractmethod
    def redact(self, content: str, positions: Positions) -> str:
        """
        Applique le caviardage sur le texte fourni selon les positions des PII

        Parameters
        ----------
        content: texte original du document
        positions: liste des positions des PII détectées (type, début, fin)

        Return
        ------
        texte caviardé
        """
        pass
