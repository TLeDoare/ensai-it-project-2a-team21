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
    def redact(self, content: str, positions: Positions) -> str:
        redacted_content = content

        # Je ne suis pas totalement sûr de cette nouvelle implémentation.

        # Application du masquage de la fin vers le début pour préserver les index
        for position in sorted(positions, key=lambda r: r.indices[0], reverse=True):
            redacted_content = redacted_content[:position.indices[0]] + "[MASQUÉ]" + redacted_content[position.indices[1]:]

        return redacted_content
