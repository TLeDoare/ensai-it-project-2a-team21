
from secrets import choice

from utils.exceptions import PseudonymisationImpossible

from ..types import PII, Positions
from .redactor_strategy import RedactorStrategy


class PseudonimiseRedactor(RedactorStrategy):

    def __init__(self, pseudonymes: dict[PII, list[str]]):
        self.pseudonymes = pseudonymes

    def redact(self, content: str, positions: Positions) -> str:

        # Créer des listes indépendantes pour chaque document
        disponibles = {
            type_pii: valeurs.copy()
            for type_pii, valeurs in self.pseudonymes.items()
        }

        correspondances = {}
        utilises = set()

        # Récupérer et trier les positions
        intervalles = []

        for position in positions:
            debut, fin = position.indices

            if not (0 <= debut < fin <= len(content)):
                raise PseudonymisationImpossible(
                    "Position de PII invalide. Veuillez utiliser le masquage."
                )

            intervalles.append((debut, fin, position.PII))

        intervalles.sort(key=lambda x: (x[0], -x[1], x[2].name))

        # Conserver les valeurs originales pour éviter de les réutiliser
        valeurs_originales = {
            content[debut:fin].casefold()
            for debut, fin, _ in intervalles
        }

        # Fusionner les intervalles qui se chevauchent
        intervalles_fusionnes = []

        for debut, fin, type_pii in intervalles:

            if intervalles_fusionnes and debut < intervalles_fusionnes[-1][1]:

                ancien_debut, ancien_fin, ancien_type = intervalles_fusionnes[-1]

                if ancien_type != type_pii:
                    raise PseudonymisationImpossible(
                        "Chevauchement de types de PII différents. "
                        "Veuillez utiliser le masquage."
                    )

                intervalles_fusionnes[-1] = (
                    ancien_debut,
                    max(ancien_fin, fin),
                    ancien_type
                )

            else:
                intervalles_fusionnes.append((debut, fin, type_pii))

        # Construire les remplacements
        remplacements = []

        for debut, fin, type_pii in intervalles_fusionnes:

            valeur = content[debut:fin]
            cle = (type_pii, valeur)

            if cle not in correspondances:

                if type_pii not in disponibles:
                    raise PseudonymisationImpossible(
                        f"Type de PII non pris en charge : {type_pii.name}. "
                        "Veuillez utiliser le masquage."
                    )

                # Ne garder que les pseudonymes utilisables
                candidats = [
                    candidat
                    for candidat in disponibles[type_pii]
                    if candidat
                    and candidat.casefold() not in utilises
                    and candidat.casefold() not in valeurs_originales
                ]

                if not candidats:
                    raise PseudonymisationImpossible(
                        f"Plus de pseudonymes disponibles pour "
                        f"{type_pii.name}. Veuillez utiliser le masquage."
                    )

                # Tirer un pseudonyme au hasard
                pseudonyme = choice(candidats)

                # Le retirer des valeurs disponibles
                disponibles[type_pii].remove(pseudonyme)

                # Mémoriser la correspondance
                correspondances[cle] = pseudonyme
                utilises.add(pseudonyme.casefold())

            remplacements.append(
                (debut, fin, correspondances[cle])
            )

        # Remplacer les PII de droite à gauche
        redacted_content = content

        for debut, fin, pseudonyme in reversed(remplacements):
            redacted_content = (
                redacted_content[:debut]
                + pseudonyme
                + redacted_content[fin:]
            )

        return redacted_content
