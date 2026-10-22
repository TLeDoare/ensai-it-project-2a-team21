import asyncio
import re

from .analyser_decorator import AnalyserDecorator
from ..types import Position, Positions, PII, Analyser as AnalyserSource

class RegexDecorator(AnalyserDecorator):
    """Ajoute la détection des PII reconnaissables par expressions régulières."""

    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

    async def _detect_emails(self, content: str):
        return list(re.finditer(self.EMAIL_PATTERN, content))

    async def analyse(self, content: str) -> Positions:
        # On place self._detect_emails ici car on considère que c'est la fonction
        # qu'il faut paralléliser. La boucle for match [...] qui suit est considérée
        # comme quelque chose qui a un temps d'exécution négligeable et qui ne sert qu'à
        # concaténer les PII détectées
        analyses = await asyncio.gather(
            super().analyse(content),
            self._detect_emails(content)
        )

        positions = analyses[0]

        for match in analyses[1]:
            position = Position(
                # Les indices sont finalements dans un tuple plutôt qu'une liste car il est impossible de réaliser des ensembles de liste en python
                # pourquoi range et pas juste tuple ?
                indices=(match.start(), match.end()),
                PII=PII.email,
                confidence=1.0,
                analyser_source=AnalyserSource.Regex,
            )

            positions.add(position)

        return positions
        # possibilité de factoriser plutard pour avoir une méthode commune
