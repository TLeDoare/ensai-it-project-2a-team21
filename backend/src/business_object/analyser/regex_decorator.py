import asyncio
import re

from .analyser_decorator import AnalyserDecorator
from ..types import Position, Positions, PII, Analyser as AnalyserSource

class RegexDecorator(AnalyserDecorator):
    """Ajoute la détection des PII reconnaissables par expressions régulières."""

    # NIR : commence par un 1 ou un 2, puis la date de 
    NIR_PATTERN = r"\b[12]\d{2}(0[1-9]|1[0-2])\d{8}\b"

    # IBAN : 2 lettres majuscules pour le pays + 11 à 30 chiffres
    # (on va considérer l'IBAN sans espace prcq sinon le découpage est dur à coder)
    IBAN_PATTERN = r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"

    # Adresse mail : des symboles, puis un @, puis des symboles, puis un point
    # et au moins deux lettres
    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

    # Numéro de téléphone : +33 ou 0, puis un chiffre entre 0 et 9,
    # puis 4 groupes de 2 chiffres séparés ou non par un espace, un point ou un tiret
    TEL_PATTERN = r"\b(?:\+33|0)[1-9](?:[\s.-]*\d{2}){4}\b"

    # Numéro de la CNI : 2 types possibles (ancien et nouveau format)
    # Ancien format : 2 chiffres pour l'année, 2 chiffres pour le mois, 3 lettres ou 
    # chiffres, et 5 chiffres
    EX_NUM_CNI_PATTERN = r"\b[0-9]{2}(0[1-9]|1[0-2])[A-Z0-9]{3}\d{5}\b"
    # Nouveau format : 9 caractères alphanumériques (majuscules)
    NV_NUM_CNI_PATTERN = r"\b[A-Z0-9]{9}\b"

    # Numéro de compte principal PAN : 12 à 19 chiffres, éventuellement séparés par 
    # des espaces ou des tirets
    PAN_PATTERN = r"\b(?:\d[ -]*?){12,19}\b"

    # Numéro de plaque d'immatriculation : 2 lettres majuscules, un tiret ou un espace,
    # 3 chiffres, un tiret ou un espace, et 2 lettres majuscules
    IMMAT_PATTERN = r"\b[A-Z]{2}[-\s]?\d{3}[-\s]?[A-Z]{2}\b"  
    
    # Adresse IP : 2 types possibles (IPv4 et IPv6)
    # IPv4 : 4 nombres de 0 à 255 séparés par des points
    IP_V4_PATTERN = r"\b[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b"
    # IPv6 : 8 groupes de 4 chiffres hexadécimaux séparés par des deux points
    IP_V6_PATTERN = r"\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b"

    # SIREN : 9 chiffres, éventuellement séparés par des espaces
    SIREN_PATTERN = r"\b\d{3}\s?\d{3}\s?\d{3}\b"
    REF_CADASTR_PATTERN = r"\b\d{1,5}[A-Z]{1,2}\s?\d{1,4}\s?\d{1,4}\b"
    GPS_PATTERN = r"\b[-+]?[0-180]\.[0-9]{6,8}\b"
    


    async def _detect_emails(self, content: str):
        return list(re.finditer(self.EMAIL_PATTERN, content))

    async def _detect_tels(self, content: str):
        return list(re.finditer(self.TEL_PATTERN, content))

    async def analyse(self, content: str) -> Positions:
        # On place self._detect_emails ici car on considère que c'est la fonction
        # qu'il faut paralléliser. La boucle for match [...] qui suit est considérée
        # comme quelque chose qui a un temps d'exécution négligeable et qui ne sert qu'à
        # concaténer les PII détectées
        analyses = await asyncio.gather(
            super().analyse(content),
            self._detect_emails(content)
        )

        positions = analyses[0]

        for match in analyses[1]:
            position = Position(
                # Les indices sont finalements dans un tuple plutôt qu'une liste car il est impossible de réaliser des ensembles de liste en python
                # pourquoi range et pas juste tuple ?
                indices=(match.start(), match.end()),
                PII=PII.email,
                confidence=1.0,
                analyser_source=AnalyserSource.Regex,
            )

            positions.add(position)

        return positions
        # possibilité de factoriser plutard pour avoir une méthode commune
