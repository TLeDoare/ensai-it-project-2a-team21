"""FO3 : juge d'injection. Un second appel au LLM décide si le document tente de manipuler le système."""

import json

from utils.log_utils import get_logger

from .llm_client import juger_injection

logger = get_logger(__name__)

# Les trois verdicts possibles, enregistrés dans le journal (F4)
SUSPECT = "suspect"
SAIN = "sain"
INDISPONIBLE = "indisponible"


class InjectionJudge:
    """Donne un verdict sur le document, sans jamais bloquer le caviardage."""

    async def juger(self, content: str) -> str:
        """Renvoie SUSPECT, SAIN ou INDISPONIBLE (LLM injoignable ou réponse illisible)."""
        try:
            reponse = json.loads(await juger_injection(content))
        except Exception as erreur:
            # Le juge est un complément : son échec ne doit pas faire échouer le traitement
            logger.warning(f"Juge d'injection indisponible : {type(erreur).__name__}")
            return INDISPONIBLE
        if not isinstance(reponse, dict) or not isinstance(reponse.get("injection"), bool):
            return INDISPONIBLE
        return SUSPECT if reponse["injection"] else SAIN
