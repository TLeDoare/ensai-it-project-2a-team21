from collections import namedtuple
from enum import Enum, auto

Position = namedtuple("Position", ["indices", "PII", "confidence", "analyser_source"])
type Positions = set[Position]

class PII(Enum):
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


class Analyser(Enum):
    Regex = auto()
    LLM = auto()


class Role(Enum):
    Utilisateur = auto()
    Superviseur = auto()
    Administrateur = auto()
