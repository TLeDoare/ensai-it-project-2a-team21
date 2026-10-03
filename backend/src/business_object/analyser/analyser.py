from abc import ABC, abstractmethod

from ..types import Positions

class Analyser(ABC):
    """Interface commune à tous les analyseurs de PII."""

    @abstractmethod
    def analyse(self, content: str) -> Positions:
        """Analyse un texte et retourne les positions des PII détectées."""
        pass