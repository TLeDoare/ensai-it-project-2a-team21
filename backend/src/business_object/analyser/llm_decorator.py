import asyncio

from business_object.types import AnalysisFail

from ..llm_client.llm_client import detect_pii
from ..llm_client.output_verifier import OutputVerifier
from .analyser_decorator import AnalyserDecorator


class LLMDecorator(AnalyserDecorator):
    """Ajoute la détection des PII par le LLM, avec mode dégradé."""

    async def _detect_llm(self, content: str) -> set:
        try:
            raw = await detect_pii(content)
            return OutputVerifier().verify(raw, content)
        except Exception as e:
            return {AnalysisFail(e, "LLM")}

    async def analyse(self, content: str) -> set:
        positions, positions_llm = await asyncio.gather(
            super().analyse(content),
            self._detect_llm(content),
        )
        return positions | positions_llm
