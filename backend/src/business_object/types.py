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
    EX_CNI = auto()
    PAN = auto()
    postal_code = auto()
    immatriculation = auto()
    IP_V4 = auto()
    IP_V6 = auto()
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
    address = auto()
    name = auto()


class Analyser(IntEnum):
    Regex = auto()
    LLM = auto()


class Role(StrEnum):
    Utilisateur = "UTILISATEUR"
    Superviseur = "SUPERVISEUR"
    Administrateur = "ADMINISTRATEUR"


class Access(IntEnum):
    ReadDoc = auto()
    CreateDoc = auto()
    ReadPerson = auto()
    CreatePerson = auto()
    UpdatePerson = auto()
    DeletePerson = auto()
