import asyncio
import re

from .analyser_decorator import AnalyserDecorator
from ..types import Position, Positions, PII, Analyser as AnalyserSource

class RegexDecorator(AnalyserDecorator):
    """Ajoute la détection des PII reconnaissables par expressions régulières."""

    NIR_PATTERN = r"\b[12]\d{2}(0[1-9]|1[0-2])\d{8}\b"
    IBAN_PATTERN = r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"
    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    TEL_PATTERN = r"\b(?:\+33|0)[1-9](?:[\s.-]*\d{2}){4}\b"
    EX_NUM_CNI_PATTERN = r"\b[0-9]{2}(0[1-9]|1[0-2])[A-Z0-9]{3}\d{5}\b"
    NV_NUM_CNI_PATTERN = r"\b[A-Z0-9]{9}\b"
    IMMAT_PATTERN = r"\b[A-Z]{2}[-\s]?\d{3}[-\s]?[A-Z]{2}\b"    
    IP_PATTERN = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    SIREN_PATTERN = r"\b\d{3}\s?\d{3}\s?\d{3}\b"
    


    async def _detect_emails(self, content: str):
        return list(re.finditer(self.EMAIL_PATTERN, content))

    async def _detect_tels(self, content: str):
        return list(re.finditer(self.TEL_PATTERN, content))

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
