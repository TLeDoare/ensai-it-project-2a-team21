from collections import namedtuple
from enum import IntEnum, StrEnum, auto

Position = namedtuple("Position", ["indices", "PII", "confidence", "analyser_source"])
type Positions = set[Position]

class PII(IntEnum):
    last_name = auto()
    first_name = auto()
    birthdate = auto()
    NIR = auto()
    IBAN = auto()
    email = auto()
    phone_number = auto()
    CNI = auto()
    PAN = auto()
    postal_code = auto()
    immatriculation = auto()
    IP = auto()
    SIREN = auto()
    cadastre = auto()
    GPS = auto()
    place = auto()
    organism = auto()
    job = auto()
    family_relationships = auto()
    private_life = auto()
    judiciary_situation = auto()
    income = auto()
    medical = auto()
    ethnicity = auto()
    gender = auto()

    def __str__(self):
        return f"PII.{self.name}"


class Analyser(IntEnum):
    Regex = auto()
    LLM = auto()

    def __str__(self):
        return f"Analyser.{self.name}"


class Role(StrEnum):
    Utilisateur = "UTILISATEUR"
    Superviseur = "SUPERVISEUR"
    Administrateur = "ADMINISTRATEUR"
