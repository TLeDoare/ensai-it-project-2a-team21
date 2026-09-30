from abc import ABC, abstractmethod


class Analyser(ABC):
    """Interface commune à tous les analyseurs de PII."""

    @abstractmethod
    def analyse(self, content: str):
        """Analyse un texte et retourne les positions des PII détectées."""
        pass