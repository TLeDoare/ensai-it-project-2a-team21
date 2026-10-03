from .analyser import Analyser
from .empty_analyser import EmptyAnalyser
from .regex_decorator import RegexDecorator

class AnalyserFactory:
    """Construit l'analyseur correspondant aux paramètres demandés."""

    def get_analyser(self, params: dict) -> Analyser:
        analyser = EmptyAnalyser()
        
        analyser = RegexDecorator(analyser, params)

        return analyser