from ..types import Positions
from .redactor_strategy import RedactorStrategy


class PseudonimiseRedactor(RedactorStrategy):
    def redact(self, content: str, positions: Positions) -> str:
        pass
