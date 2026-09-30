from .analyser import Analyser


class EmptyAnalyser(Analyser):
    """Analyseur vide servant de base aux décorateurs."""

    def analyse(self, content: str):
        return set() # Les positions sont stockées dans un ensemble afin d'éviter les doublons entre détecteurs.