import asyncio

from .analyser_decorator import AnalyserDecorator
from ..llm_client.llm_client import detect_pii
from ..llm_client.output_verifier import OutputVerifier


class LLMDecorator(AnalyserDecorator):
    """Ajoute la détection des PII par le LLM, avec mode dégradé."""

    async def _detect_llm(self, content: str) -> set:
        try:
            raw = await detect_pii(content)
            return OutputVerifier().verify(raw, content)
        except Exception as erreur:
            print ("Mode dégradé :", repr(erreur))
            return set()

    async def analyse(self, content: str) -> set:
        positions, positions_llm = await asyncio.gather(
            super().analyse(content),
            self._detect_llm(content),
        )
        return positions | positions_llm


if __name__ == "__main__":

    class Vide:
        async def analyse(self, content):
            return set()

    texte = "Monsieur Pierre Dupont, domicilié 12 rue de la Paix, 75002 Paris."
    print(asyncio.run(LLMDecorator(Vide(), {}).analyse(texte)))