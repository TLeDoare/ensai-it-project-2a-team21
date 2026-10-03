from .analyser import Analyser
from ..types import Positions

class EmptyAnalyser(Analyser):
    """Analyseur vide servant de base aux décorateurs."""

    def analyse(self, content: str) -> Positions:
        return set() # Les positions sont stockées dans un ensemble afin d'éviter les doublons entre détecteurs.