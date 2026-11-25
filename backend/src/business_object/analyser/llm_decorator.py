import asyncio

from business_object.types import AnalysisFail
from utils.exceptions import LLMInjectionError

from ..llm_client.llm_client import detect_pii
from ..llm_client.output_verifier import OutputVerifier
from .analyser_decorator import AnalyserDecorator


class LLMDecorator(AnalyserDecorator):
    """Ajoute la détection des PII par le LLM, avec mode dégradé."""

    async def _appeler_llm(self, content: str) -> str | AnalysisFail:
        """Interroge le LLM et renvoie sa réponse brute (JSON sous forme de texte).

        Si le LLM est injoignable, renvoie un AnalysisFail au lieu de faire échouer
        toute l'analyse : c'est le mode dégradé (F2).
        """
        try:
            return await detect_pii(content)
        except Exception as e:
            return AnalysisFail(e, "LLM")

    async def analyse(self, content: str) -> set:
        # Les analyseurs enveloppés (regex) et le LLM tournent en parallèle
        positions, reponse_llm = await asyncio.gather(
            super().analyse(content),
            self._appeler_llm(content),
        )

        if isinstance(reponse_llm, AnalysisFail):
            # LLM indisponible : on garde les résultats des regex et on signale l'échec
            return positions | {reponse_llm}

        # Vérification de la sortie du LLM (F5). Elle est faite ici, après le gather,
        # car c'est le seul endroit où les résultats des regex sont connus : ils servent
        # à repérer une omission suspecte (le LLM ne renvoie rien alors que les regex trouvent).
        try:
            positions_finales, suspicion = OutputVerifier().verify(reponse_llm, content, positions)
        except Exception as e:
            # Réponse illisible (JSON invalide) : même traitement qu'un LLM indisponible
            return positions | {AnalysisFail(e, "LLM")}

        if suspicion:
            # On garde toutes les PII trouvées ET on ajoute une alerte
            positions_finales.add(AnalysisFail(LLMInjectionError("Omission suspecte du LLM"), "LLM"))
        return positions_finales
