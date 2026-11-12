from utils.exceptions import RedactorError

from ..types import Positions
from .redactor_strategy import RedactorStrategy


class RedactorContext:
    def set_strategy(self, redactor_strategy: RedactorStrategy):
        self.redactor_strategy = redactor_strategy

    def execute_strategy(self, content: str, positions: Positions) -> str:
        try:
            return self.redactor_strategy.redact(content, positions)
        except Exception as err:
            raise RedactorError from err
