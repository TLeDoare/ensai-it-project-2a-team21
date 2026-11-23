"""Compare plusieurs modèles LLM de SSPCloud sur un jeu d'essai fixe, annoté à la main.

Métrique prioritaire : le rappel (une PII oubliée est une fuite), sous contrainte de précision.
Chaque modèle est évalué plusieurs fois, car la sortie d'un LLM est aléatoire .
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from statistics import mean

# Rend importables les modules du backend (comme le fait --app-dir backend/src pour l'API)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from business_object.llm_client.llm_client import detect_pii  # noqa: E402

# Modèles de texte disponibles sur SSPCloud
MODELES = ["gemma4-26b-moe", "qwen3-6-35b-moe", "qwen3-8-27b"]

# Nombre de passages par modèle : un seul tirage ne suffit pas à comparer
NB_REPETITIONS = 3

# Jeu d'essai fixe : textes fictifs et PII attendues, annotées à la main
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
        "pii": ["Sophie", "Durand", "14 rue des Lilas", "35000", "Rennes"],
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
        "pii": ["Claire", "Rousseau", "condamnée", "Emma"],
    },
]


def normaliser(texte: str) -> str:
    """Met en minuscules et retire les espaces en trop, pour comparer sans tenir compte de la mise en forme."""
    return " ".join(texte.lower().split())


def pii_trouvees(reponse_brute: str) -> list[str]:
    """Extrait les passages détectés de la réponse JSON du LLM ({"spans": [{"text": ...}]})."""
    donnees = json.loads(reponse_brute)
    return [normaliser(span.get("text", "")) for span in donnees.get("spans", []) if span.get("text")]


def se_recouvrent(a: str, b: str) -> bool:
    """Deux passages correspondent si l'un contient l'autre (« Marie Lefèvre » contient « Marie »)."""
    return a in b or b in a


async def un_passage(modele: str) -> dict:
    """Analyse tout le jeu d'essai une fois et compte les vrais positifs, oublis et fausses alertes."""
    os.environ["LLM_MODEL"] = modele  # detect_pii lit cette variable à chaque appel
    attendues = trouvees = detections_total = detections_justes = erreurs = 0
    oublis = []

    for exemple in JEU_DE_TEST:
        pii_attendues = [normaliser(p) for p in exemple["pii"]]
        attendues += len(pii_attendues)
        try:
            detections = pii_trouvees(await detect_pii(exemple["texte"]))
        except Exception as erreur:  # JSON invalide ou modèle injoignable : ses PII comptent comme oubliées
            erreurs += 1
            print(f"  [{modele}] erreur : {erreur}")
            detections = []

        # Rappel : part des PII attendues retrouvées dans au moins une détection
        for pii, pii_brute in zip(pii_attendues, exemple["pii"]):
            if any(se_recouvrent(pii, d) for d in detections):
                trouvees += 1
            else:
                oublis.append(pii_brute)

        # Précision : part des détections qui correspondent à une vraie PII
        detections_total += len(detections)
        detections_justes += sum(any(se_recouvrent(d, p) for p in pii_attendues) for d in detections)

    return {
        "rappel": trouvees / attendues,
        "precision": detections_justes / detections_total if detections_total else 0.0,
        "erreurs": erreurs,
        "oublis": oublis,
    }


async def evaluer(modele: str) -> dict:
    """Répète l'évaluation d'un modèle et résume les résultats (moyenne, minimum, maximum)."""
    debut = time.perf_counter()
    passages = []
    for i in range(NB_REPETITIONS):
        print(f"  passage {i + 1}/{NB_REPETITIONS}")
        passages.append(await un_passage(modele))

    rappels = [p["rappel"] for p in passages]
    precisions = [p["precision"] for p in passages]
    return {
        "modele": modele,
        "rappel": mean(rappels),
        "rappel_min": min(rappels),
        "rappel_max": max(rappels),
        "precision": mean(precisions),
        "erreurs": sum(p["erreurs"] for p in passages),
        "duree": (time.perf_counter() - debut) / NB_REPETITIONS,
        "oublis": sorted({o for p in passages for o in p["oublis"]}),
    }


async def main():
    """Évalue chaque modèle, puis affiche le tableau comparatif trié par rappel."""
    resultats = []
    for modele in MODELES:
        print(f"Évaluation de {modele}...")
        resultats.append(await evaluer(modele))

    print(f"\n{NB_REPETITIONS} passages par modèle, {sum(len(e['pii']) for e in JEU_DE_TEST)} PII attendues par passage.\n")
    print("| Modèle | Rappel moyen | Rappel min-max | Précision moyenne | Erreurs JSON | Durée par passage |")
    print("|---|---|---|---|---|---|")
    for r in sorted(resultats, key=lambda r: r["rappel"], reverse=True):
        print(f"| {r['modele']} | {r['rappel']:.0%} | {r['rappel_min']:.0%}-{r['rappel_max']:.0%} "
              f"| {r['precision']:.0%} | {r['erreurs']} | {r['duree']:.0f} s |")

    print("\nPII oubliées au moins une fois :")
    for r in resultats:
        print(f"- {r['modele']} : {', '.join(r['oublis']) or 'aucune'}")


if __name__ == "__main__":
    asyncio.run(main())