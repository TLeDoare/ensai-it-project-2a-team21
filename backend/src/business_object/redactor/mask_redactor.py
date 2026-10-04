from itertools import groupby
from operator import itemgetter

from ..types import Positions
from .redactor_strategy import RedactorStrategy


class MaskRedactor(RedactorStrategy):
    """Remplace les données sensibles par une chaîne de caractères comme [Masqué] ou une série de *
    """
    """
    Version naïve :
    def redact(self, content, positions: Positions):
        # on inverse l'ordre des positions pour remplacer depuis la fin
        # (pour préserver les index en remplaçant)
        sorted_positions = sorted(positions, key=lambda x: x['debut'], reverse=True)
        # la liste de dictionnaires positions pouvant être triée de
        # plusieurs manières, on indique la clé de tri avec une petite
        # fonction lambda
        redacted_content = content
        for pos in sorted_positions:
            debut, fin = pos['debut'], pos['fin']
            # on concatène pour remplacer à chaque itération
            redacted_content = redacted_content[:debut] + "[MASQUÉ]" + redacted_content[fin:]
        return redacted_content
    """
    # Pour gérer des zones non continues, remplace chaque sous-groupe d'index "collés" de positions
    def redact(self, content: str, positions: Positions) -> str:
        # Fusion de tous les indices uniques
        all_indices = sorted({idx for pos in positions for idx in pos.indices})

        if not all_indices:
            return content

        # Regroupement des indices contigus en plages (ex: [10, 11, 12] -> start=10, end=13)
        ranges = []
        for _, group in groupby(enumerate(all_indices), lambda ix: ix[0] - ix[1]):
            group_list = list(map(itemgetter(1), group))
            start = group_list[0]
            end = group_list[-1] + 1  # Borne supérieure (exclue) pour le découpage
            ranges.append((start, end))

        # Application du masquage de la fin vers le début pour préserver les index
        redacted_content = content
        for start, end in sorted(ranges, key=lambda r: r[0], reverse=True):
            redacted_content = redacted_content[:start] + "[MASQUÉ]" + redacted_content[end:]

        return redacted_content
