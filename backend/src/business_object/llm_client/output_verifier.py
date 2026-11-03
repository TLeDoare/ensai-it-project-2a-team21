import json
import re

from ..types import Position, Analyser as AnalyserSource
from .prompt_templates import LLM_PII_TYPES

TYPES = {pii.name: pii for pii in LLM_PII_TYPES}


class OutputVerifier:
    """Vérifie la sortie du LLM et retrouve les positions dans le document."""

    def verify(self, raw: str, content: str) -> set:
        spans = json.loads(raw)["spans"]
        positions = set()
        for span in spans:
            texte = span.get("text", "")
            pii = TYPES.get(span.get("type"))
            if pii is None or not any(c.isalnum() for c in texte):
                continue
            for match in re.finditer(re.escape(texte), content):
                positions.add(Position((match.start(), match.end()), pii, 0.8, AnalyserSource.LLM))
        return positions