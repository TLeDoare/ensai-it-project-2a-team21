import json
import re

from ..types import Analyser as AnalyserSource
from ..types import Position
from .prompt_templates import LLM_PII_TYPES

TYPES = {pii.name: pii for pii in LLM_PII_TYPES}


class OutputVerifier:
    """Vérifie la sortie du LLM, gère les omissions et journalise les suspicions."""

    def verify(self, raw: str, content: str, regex_positions: set | None = None) -> tuple[set, bool]:
        spans = []
        try:
            parsed = json.loads(raw)
            spans = parsed.get("spans", [])
        except json.JSONDecodeError:
            pass # Format invalide

        llm_positions = set()
        for span in spans:
            texte = span.get("text", "")
            pii = TYPES.get(span.get("type"))
            if pii is None or not any(c.isalnum() for c in texte):
                continue
            
            mots = texte.split()
            if not mots:
                continue
            flexible_pattern = r"\s+".join(re.escape(mot) for mot in mots)
            
            for match in re.finditer(flexible_pattern, content):
                llm_positions.add(Position((match.start(), match.end()), pii, 0.8, AnalyserSource.LLM))

        # Indicateur de suspicion d'omission / attaque
        suspicion_omission = False
        if regex_positions and len(ll_m_positions := llm_positions) == 0 and len(regex_positions) > 0:
            # Le LLM ne renvoie rien alors que les regex trouvent des éléments : forte suspicion d'omission/contournement
            suspicion_omission = True

        # Union finale pour garantir le rappel (fail-safe)
        final_positions = llm_positions.union(regex_positions or set())
        
        return final_positions, suspicion_omission
