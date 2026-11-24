"""Compare les détecteurs de PII (regex, LLM, regex + LLM) sur un jeu d'essai fixe, annoté à la main.

Métrique prioritaire : le rappel (une PII oubliée est une fuite), sous contrainte de précision.
Les configurations avec LLM sont évaluées plusieurs fois, car la sortie d'un LLM est aléatoire.
Les regex sont déterministes : un seul passage suffit.
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from statistics import mean

# Rend importables les modules du backend (comme le fait --app-dir backend/src pour l'API)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from business_object.analyser.empty_analyser import EmptyAnalyser  # noqa: E402
from business_object.analyser.llm_decorator import LLMDecorator  # noqa: E402
from business_object.analyser.regex_decorator import RegexDecorator  # noqa: E402
from business_object.types import AnalysisFail  # noqa: E402

# Modèles de texte disponibles sur SSPCloud
MODELES = ["gemma4-26b-moe", "qwen3-6-35b-moe", "qwen3-8-27b"]
# Nombre de passages pour les configurations avec LLM : un seul tirage ne suffit pas à comparer
NB_REPETITIONS = 3

# Jeu d'essai fixe : textes fictifs et PII attendues, annotées à la main selon les types confiés aux détecteurs
JEU_DE_TEST = [
    {
        "texte": "Bonjour, je suis Marie Lefèvre, née le 12/03/1985. Écrivez-moi à marie.lefevre@exemple.fr.",
        "pii": ["Marie", "Lefèvre", "12/03/1985", "marie.lefevre@exemple.fr"],
    },
    {
        "texte": "Merci de rappeler M. Karim Benali au 06 12 34 56 78 avant vendredi.",
        "pii": ["Karim", "Benali", "06 12 34 56 78"],
    },
    {
        "texte": "Le virement doit partir sur l'IBAN FR76 3000 6000 0112 3456 7890 189 au nom de Paul Martin.",
        "pii": ["FR76 3000 6000 0112 3456 7890 189", "Paul", "Martin"],
    },
    {
        "texte": "Mme Sophie Durand habite au 14 rue des Lilas, 35000 Rennes, avec son mari.",
        # « mari » : lien familial (family_relationships), révèle la situation conjugale
        "pii": ["Sophie", "Durand", "14 rue des Lilas", "35000", "Rennes", "mari"],
    },
    {
        "texte": "Le patient Jean Morel est suivi pour un diabète de type 2 depuis 2019.",
        "pii": ["Jean", "Morel", "diabète de type 2"],
    },
    {
        "texte": "Lucas Petit, ingénieur chez Airbus, gagne 4 500 euros nets par mois.",
        "pii": ["Lucas", "Petit", "ingénieur", "Airbus", "4 500 euros"],
    },
    {
        "texte": "Son numéro de sécurité sociale est 1 85 03 75 112 345 67 et sa plaque AB-123-CD.",
        "pii": ["1 85 03 75 112 345 67", "AB-123-CD"],
    },
    {
        "texte": "Claire Rousseau a été condamnée en 2021 ; sa fille Emma vit chez ses grands-parents.",
        # « fille » et « grands-parents » : liens familiaux (family_relationships), révèlent la situation familiale
        "pii": ["Claire", "Rousseau", "condamnée", "fille", "Emma", "grands-parents"],
    },
]


def normaliser(texte: str) -> str:
    """Met en minuscules et retire les espaces en trop, pour comparer sans tenir compte de la mise en forme."""
    return " ".join(texte.lower().split())


def se_recouvrent(a: str, b: str) -> bool:
    """Deux passages correspondent si l'un contient l'autre (« Marie Lefèvre » contient « Marie »)."""
    return a in b or b in a


def construire_analyseur(configuration: str):
    """Assemble la chaîne de décorateurs, comme le fait l'API (AnalyserFactory)."""
    if configuration == "Regex seules":
        return RegexDecorator(EmptyAnalyser(), {})
    if configuration == "LLM seul":
        return LLMDecorator(EmptyAnalyser(), {})
    # Regex + LLM : le LLM reçoit les positions déjà trouvées par les regex
    return LLMDecorator(RegexDecorator(EmptyAnalyser(), {}), {})


def extraire_passages(positions: set, texte: str) -> tuple[list[str], int]:
    """Transforme les Position en passages de texte ; compte à part les échecs d'analyse (AnalysisFail)."""
    passages, echecs = [], 0
    for position in positions:
        if isinstance(position, AnalysisFail):
            echecs += 1
            continue
        debut, fin = position.indices[0], position.indices[-1]
        passages.append(normaliser(texte[debut:fin]))
    return passages, echecs


async def un_passage(configuration: str) -> dict:
    """Analyse tout le jeu d'essai une fois et compte les PII trouvées, oubliées et signalées à tort."""
    analyseur = construire_analyseur(configuration)
    attendues = trouvees = detections_total = detections_justes = echecs = 0
    oublis, faux_positifs = [], []

    for exemple in JEU_DE_TEST:
        pii_attendues = [normaliser(p) for p in exemple["pii"]]
        attendues += len(pii_attendues)
        try:
            detections, nb_echecs = extraire_passages(await analyseur.analyse(exemple["texte"]), exemple["texte"])
            echecs += nb_echecs
        except Exception as erreur:  # Erreur imprévue : les PII du texte comptent comme oubliées
            echecs += 1
            print(f"  [{configuration}] erreur : {erreur}")
            detections = []

        # Rappel : part des PII attendues retrouvées dans au moins une détection
        for pii, pii_brute in zip(pii_attendues, exemple["pii"]):
            if any(se_recouvrent(pii, d) for d in detections):
                trouvees += 1
            else:
                oublis.append(pii_brute)

        # Précision : part des détections qui correspondent à une vraie PII ; les autres sont des faux positifs
        for d in detections:
            detections_total += 1
            if any(se_recouvrent(d, p) for p in pii_attendues):
                detections_justes += 1
            else:
                faux_positifs.append(d)

    return {
        "rappel": trouvees / attendues,
        "precision": detections_justes / detections_total if detections_total else 0.0,
        "echecs": echecs,
        "oublis": oublis,
        "faux_positifs": faux_positifs,
    }


async def evaluer(configuration: str, modele: str | None, repetitions: int) -> dict:
    """Répète l'évaluation d'une configuration et résume les résultats (moyenne, minimum, maximum)."""
    if modele:
        os.environ["LLM_MODEL"] = modele  # detect_pii lit cette variable à chaque appel
    nom = f"{configuration} ({modele})" if modele else configuration
    print(f"Évaluation : {nom}")

    debut = time.perf_counter()
    passages = []
    for i in range(repetitions):
        print(f"  passage {i + 1}/{repetitions}")
        passages.append(await un_passage(configuration))

    rappels = [p["rappel"] for p in passages]
    return {
        "nom": nom,
        "rappel": mean(rappels),
        "rappel_min": min(rappels),
        "rappel_max": max(rappels),
        "precision": mean(p["precision"] for p in passages),
        "echecs": sum(p["echecs"] for p in passages),
        "duree": (time.perf_counter() - debut) / repetitions,
        "oublis": sorted({o for p in passages for o in p["oublis"]}),
        "faux_positifs": sorted({f for p in passages for f in p["faux_positifs"]}),
    }


async def main():
    """Évalue les regex une fois, puis chaque modèle seul et combiné aux regex ; affiche le tableau trié par rappel."""
    resultats = [await evaluer("Regex seules", None, 1)]
    for modele in MODELES:
        resultats.append(await evaluer("LLM seul", modele, NB_REPETITIONS))
        resultats.append(await evaluer("Regex + LLM", modele, NB_REPETITIONS))

    total_pii = sum(len(e["pii"]) for e in JEU_DE_TEST)
    print(f"\n{total_pii} PII attendues par passage ; {NB_REPETITIONS} passages pour les configurations avec LLM.\n")
    print("| Configuration | Rappel moyen | Rappel min-max | Précision moyenne | Échecs d'analyse | Durée par passage |")
    print("|---|---|---|---|---|---|")
    for r in sorted(resultats, key=lambda r: r["rappel"], reverse=True):
        print(f"| {r['nom']} | {r['rappel']:.0%} | {r['rappel_min']:.0%}-{r['rappel_max']:.0%} "
              f"| {r['precision']:.0%} | {r['echecs']} | {r['duree']:.0f} s |")

    print("\nPII oubliées au moins une fois :")
    for r in resultats:
        print(f"- {r['nom']} : {', '.join(r['oublis']) or 'aucune'}")

    print("\nFaux positifs (signalés à tort au moins une fois) :")
    for r in resultats:
        print(f"- {r['nom']} : {', '.join(r['faux_positifs']) or 'aucun'}")


if __name__ == "__main__":
    asyncio.run(main())