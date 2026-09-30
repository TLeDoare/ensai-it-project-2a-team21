from .analyser import Analyser
from .empty_analyser import EmptyAnalyser


class AnalyserFactory:
    """Construit l'analyseur correspondant aux paramètres demandés."""

    def get_analyser(self, params: dict) -> Analyser:
        analyser = EmptyAnalyser()
        # je continuerais la méthode une fois regex_decorator pleinement implémenté

        return analyser