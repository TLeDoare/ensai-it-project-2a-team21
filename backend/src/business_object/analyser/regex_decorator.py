import re

from .analyser_decorator import AnalyserDecorator
from ..types import Position, Positions, PII, Analyser as AnalyserSource

class RegexDecorator(AnalyserDecorator):
    """Ajoute la détection des PII reconnaissables par expressions régulières."""

    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

    def _detect_emails(self, content: str):
        return list(re.finditer(self.EMAIL_PATTERN, content))

    def analyse(self, content: str) -> Positions:
        positions = super().analyse(content)

        for match in self._detect_emails(content):
            position = Position(
                indices=(match.start(), match.end()),
                PII=PII.email,
                confiance=1.0,
                analyser_source=AnalyserSource.Regex,
            )

            positions.add(position)

        return positions
        # possibilité de factoriser plutard pour avoir une méthode commune