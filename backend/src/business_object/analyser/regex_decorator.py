import asyncio
import re

from .analyser_decorator import AnalyserDecorator
from ..types import Position, Positions, PII, Analyser as AnalyserSource

class RegexDecorator(AnalyserDecorator):
    """Ajoute la détection des PII reconnaissables par expressions régulières."""

    # NIR : 1 ou 2, 2 chiffres pour l'année, 2 chiffres pour le mois, puis 8 chiffres
    NIR_PATTERN = r"\b[12]\s?\d{2}\s?(0[1-9]|1[0-2])\s?\d{2}\s?\d{3}\s?\d{3}(\s?\d{2})?\b"
    
    # IBAN : 2 lettres majuscules pour le pays + 11 à 30 chiffres avec des espaces possibles
    IBAN_PATTERN = r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]){11,30}\b"

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
    PAN_PATTERN = r"\b\d(?:[ -]?\d){12,18}\b"

    # Numéro de plaque d'immatriculation : 2 lettres majuscules, un tiret ou un espace,
    # 3 chiffres, un tiret ou un espace, et 2 lettres majuscules
    IMMAT_PATTERN = r"\b[A-Z]{2}[-\s]?\d{3}[-\s]?[A-Z]{2}\b"  
    
    # Adresse IP : 2 types possibles (IPv4 et IPv6)
    # IPv4 : 4 nombres de 0 à 255 séparés par des points
    IP_V4_PATTERN = r"\b(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\b"
    # IPv6 : 8 groupes de 4 chiffres hexadécimaux séparés par des deux points
    IP_V6_PATTERN = r"\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b"

    # SIREN : 9 chiffres, éventuellement séparés par des espaces
    SIREN_PATTERN = r"\b\d{3}\s?\d{3}\s?\d{3}\b"

    # Référence cadastrale : 
    REF_CADASTR_PATTERN = r"\b\d{1,5}[A-Z]{1,2}\s?\d{1,4}\s?\d{1,4}\b"

    # Coordonnées GPS : système DMS (sexagésimal)
    # Exemple : 48°51'29.99"N 2°17'40.98"E
    GPS_PATTERN = r"\d{1,3}°\d{1,2}'\d{1,2}(?:\.\d+)?\"[NSEWO]"
    

    PATTERNS: dict[PII, str] = {
        PII.NIR: NIR_PATTERN,
        PII.IBAN: IBAN_PATTERN,
        PII.email: EMAIL_PATTERN,
        PII.phone_number: TEL_PATTERN,
        PII.EX_CNI: EX_NUM_CNI_PATTERN,
        PII.CNI: NV_NUM_CNI_PATTERN,
        PII.PAN: PAN_PATTERN,
        PII.immatriculation: IMMAT_PATTERN,
        PII.IP_V4: IP_V4_PATTERN,
        PII.IP_V6: IP_V6_PATTERN,
        PII.SIREN: SIREN_PATTERN,
        PII.cadastre: REF_CADASTR_PATTERN,
        PII.GPS: GPS_PATTERN
    }

    async def _detect(self, content: str, type_pii: PII, pattern: str):
        return [
            Position(
                indices=(m.start(), m.end()),
                PII=type_pii,
                confidence=1.0,
                analyser_source=AnalyserSource.Regex,
            )
            for m in re.finditer(pattern, content)
        ]

    async def analyse(self, content: str) -> Positions:
        taches = [super().analyse(content)]
        taches += [self._detect(content, t, p) for t, p in self.PATTERNS.items()]
        resultats = await asyncio.gather(*taches)

        positions: Positions = set() 
        for element in resultats:
            positions.update(element)
        return positions