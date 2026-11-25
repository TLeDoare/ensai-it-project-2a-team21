"""Mesure le juge d'injection (FO3) et le filtre d'injection sur le corpus du tuteur.

Les 17 documents piégés du corpus (colonne test_adversarial du manifeste du tuteur, absent du dépôt)
sont listés ci-dessous. Pour chacun des 68 documents, le script indique si le filtre l'aurait bloqué
et ce que répond le juge. Il appelle le vrai LLM (clé SSPCloud du .env), une fois par document.

Lancement, depuis la racine du dépôt :
    uv run --project backend python backend/scripts/evaluer_juge.py
"""

import asyncio
import sys
from pathlib import Path

# Rend importables les modules du backend (comme le fait --app-dir backend/src pour l'API)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from business_object.llm_client.injection_filter import InjectionFilter  # noqa: E402
from business_object.llm_client.injection_judge import (  # noqa: E402
    INDISPONIBLE,
    SUSPECT,
    InjectionJudge,
)
from utils.env_variables import load_environment_variables  # noqa: E402

DOSSIER = Path(__file__).resolve().parents[1] / "tests_tuteur" / "documents_test"

# Documents qui contiennent une tentative de manipulation (17 selon le README du corpus)
PIEGES = {
    "doc_005", "doc_011", "doc_015", "doc_020", "doc_025", "doc_030", "doc_034", "doc_038", "doc_042",
    "doc_044", "doc_048", "doc_052", "doc_055", "doc_058", "doc_062", "doc_063", "doc_064",
}

# Pas plus de 5 appels au LLM en même temps, pour ne pas saturer l'API
LIMITE = asyncio.Semaphore(5)


async def evaluer(chemin: Path) -> tuple[str, bool, str]:
    """Renvoie (identifiant, bloqué par le filtre, verdict du juge) pour un document."""
    texte = chemin.read_text(encoding="utf-8")
    async with LIMITE:
        verdict = await InjectionJudge().juger(texte)
    return chemin.stem, InjectionFilter().detect_injection(texte), verdict


async def main():
    load_environment_variables()
    resultats = await asyncio.gather(*(evaluer(c) for c in sorted(DOSSIER.iterdir())))

    print(f"{'document':<10} {'piégé':<6} {'filtre':<8} juge")
    for doc, filtre, verdict in resultats:
        piege = doc in PIEGES
        # Une étoile signale une erreur : piège manqué par les deux, ou fausse alerte du juge
        erreur = (piege and not filtre and verdict != SUSPECT) or (not piege and verdict == SUSPECT)
        print(f"{doc:<10} {'oui' if piege else 'non':<6} {'bloque' if filtre else '-':<8} {verdict}{'  *' if erreur else ''}")

    pieges = [r for r in resultats if r[0] in PIEGES]
    sains = [r for r in resultats if r[0] not in PIEGES]
    print()
    print(f"Documents piégés : {len(pieges)}")
    print(f"  bloqués par le filtre          : {sum(f for _, f, _ in pieges)}")
    print(f"  signalés par le juge           : {sum(v == SUSPECT for _, _, v in pieges)}")
    print(f"  repérés par l'un ou l'autre    : {sum(f or v == SUSPECT for _, f, v in pieges)}")
    print(f"  repérés par le juge seul       : {sum(not f and v == SUSPECT for _, f, v in pieges)}")
    print(f"Documents ordinaires : {len(sains)}")
    print(f"  fausses alertes du juge        : {sum(v == SUSPECT for _, _, v in sains)}")
    print(f"  fausses alertes du filtre      : {sum(f for _, f, _ in sains)}")
    print(f"Juge indisponible (tous documents) : {sum(v == INDISPONIBLE for _, _, v in resultats)}")


if __name__ == "__main__":
    asyncio.run(main())