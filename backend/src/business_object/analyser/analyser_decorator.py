from abc import ABC, abstractmethod

from .analyser import Analyser
from ..types import Positions

class AnalyserDecorator(Analyser, ABC):
    """Classe de base des décorateurs d'analyse."""

    def __init__(self, wrapper: Analyser, params: dict):
        self.wrapper = wrapper
        self.params = params

    @abstractmethod
    async def analyse(self, content: str) -> Positions:
        return await self.wrapper.analyse(content)
