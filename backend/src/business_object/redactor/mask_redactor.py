
from ..types import Positions
from .redactor_strategy import RedactorStrategy


class MaskRedactor(RedactorStrategy):
    """Masque les données personnelles détectées dans un texte."""

    def redact(self, content: str, positions: Positions) -> str:
        """Remplace les intervalles détectés par [MASQUÉ]."""

        # récupérer les intervalles et les trier
        intervalles = sorted(
            (
                position.indices[0],
                position.indices[1],
                position.PII.name.upper()
            )
            for position in positions
        )

        # Vérifier et fusionner les intervalles qui se chevauchent
        intervalles_fusionnes = []

        for debut, fin, type_pii in intervalles:

            if not (0 <= debut < fin <= len(content)):
                raise ValueError("Position de PII invalide.")

            if intervalles_fusionnes and debut < intervalles_fusionnes[-1][1]:
                ancien_debut, ancien_fin, ancien_type = intervalles_fusionnes[-1]

                intervalles_fusionnes[-1] = (
                    ancien_debut,
                    max(ancien_fin, fin),
                    ancien_type if ancien_type == type_pii else "PII"
                )
            else:
                intervalles_fusionnes.append((debut, fin, type_pii))

        # Attribuer un marqueur à chaque donnée personnelle
        compteurs = {}
        correspondances = {}
        remplacements = []

        for debut, fin, type_pii in intervalles_fusionnes:

            valeur = content[debut:fin]
            cle = (type_pii, valeur)

            if cle not in correspondances:
                compteurs[type_pii] = compteurs.get(type_pii, 0) + 1
                correspondances[cle] = f"[{type_pii}_{compteurs[type_pii]}]"

            remplacements.append(
                (debut, fin, correspondances[cle])
            )

        # remplacer les PII de la fin vers le début
        redacted_content = content

        for debut, fin, marqueur in reversed(remplacements):
            redacted_content = (
                redacted_content[:debut]
                + marqueur
                + redacted_content[fin:]
            )

        return redacted_content
