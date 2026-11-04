import pytest


from business_object.redactor.mask_redactor import MaskRedactor
from business_object.types import Position, PII, Analyser as AnalyserSource
from business_object.redactor.pseudonimise_redactor import PseudonimiseRedactor
from utils.exceptions import PseudonymisationImpossible

def creer_position(content: str, valeur: str, pii: PII, occurrence: int = 0) -> Position:
    """Crée une Position correspondant à une occurrence dans le texte."""

    debut = -1

    for _ in range(occurrence + 1):
        debut = content.find(valeur, debut + 1)

        if debut == -1:
            raise ValueError(f"Valeur introuvable : {valeur}")

    return Position(
        indices=(debut, debut + len(valeur)),
        PII=pii,
        confidence=1.0,
        analyser_source=AnalyserSource.Regex,
    )

@pytest.mark.parametrize(
    "content, detections, attendu",
    [
        (
            "Contact : noah@example.com",
            [("noah@example.com", PII.email, 0)],
            "Contact : [EMAIL_1]",
        ),
        (
            "noah@example.com et ryan@example.com",
            [
                ("noah@example.com", PII.email, 0),
                ("ryan@example.com", PII.email, 0),
            ],
            "[EMAIL_1] et [EMAIL_2]",
        ),
        (
            "noah@example.com puis noah@example.com",
            [
                ("noah@example.com", PII.email, 0),
                ("noah@example.com", PII.email, 1),
            ],
            "[EMAIL_1] puis [EMAIL_1]",
        ),
        (
            "Jean Dupont",
            [
                ("Jean Dupont", PII.last_name, 0),
                ("Dupont", PII.last_name, 0),
            ],
            "[LAST_NAME_1]",
        ),
        (
            "Jean Dupont",
            [
                ("Jean Dupont", PII.first_name, 0),
                ("Dupont", PII.last_name, 0),
            ],
            "[PII_1]",
        ),
        (
            "Document sans PII",
            [],
            "Document sans PII",
        ),
    ],
)
def test_mask_redactor(content, detections, attendu):
    # GIVEN
    positions = {
        creer_position(content, valeur, pii, occurrence)
        for valeur, pii, occurrence in detections
    }

    # WHEN
    result = MaskRedactor().redact(content, positions)

    # THEN
    assert result == attendu


def test_position_invalide():
    # GIVEN
    content = "Bonjour"

    positions = {
        Position(
            indices=(3, 50),
            PII=PII.email,
            confidence=1.0,
            analyser_source=AnalyserSource.Regex,
        )
    }

    # WHEN / THEN
    with pytest.raises(ValueError):
        MaskRedactor().redact(content, positions)


def test_pseudonimisation_simple():
    # GIVEN
    content = "Bonjour Jean"
    positions = {
        creer_position(content, "Jean", PII.first_name)
    }
    pseudonymes = {
        PII.first_name: ["Lucas"]
    }

    # WHEN
    result = PseudonimiseRedactor(pseudonymes).redact(
        content, positions
    )

    # THEN
    assert result == "Bonjour Lucas"


def test_pseudonimisation_repetition():
    # GIVEN
    content = "Jean parle avec Jean"
    positions = {
        creer_position(content, "Jean", PII.first_name, 0),
        creer_position(content, "Jean", PII.first_name, 1),
    }
    pseudonymes = {
        PII.first_name: ["Lucas", "Thomas"]
    }

    # WHEN
    result = PseudonimiseRedactor(pseudonymes).redact(
        content, positions
    )

    # THEN
    assert result in {
        "Lucas parle avec Lucas",
        "Thomas parle avec Thomas",
    }


def test_pseudonimisation_valeurs_differentes():
    # GIVEN
    content = "Jean et Pierre"
    positions = {
        creer_position(content, "Jean", PII.first_name),
        creer_position(content, "Pierre", PII.first_name),
    }
    pseudonymes = {
        PII.first_name: ["Lucas", "Thomas"]
    }

    # WHEN
    result = PseudonimiseRedactor(pseudonymes).redact(
        content, positions
    )

    # THEN
    assert result in {
        "Lucas et Thomas",
        "Thomas et Lucas",
    }


def test_pseudonimisation_liste_vide():
    # GIVEN
    content = "Bonjour Jean"
    positions = {
        creer_position(content, "Jean", PII.first_name)
    }
    pseudonymes = {
        PII.first_name: []
    }

    # WHEN / THEN
    with pytest.raises(PseudonymisationImpossible):
        PseudonimiseRedactor(pseudonymes).redact(
            content, positions
        )


def test_pseudonimisation_valeur_originale_exclue():
    # GIVEN
    content = "Jean et Marc"
    positions = {
        creer_position(content, "Jean", PII.first_name),
        creer_position(content, "Marc", PII.first_name),
    }
    pseudonymes = {
        PII.first_name: ["Marc", "Lucas", "Thomas"]
    }

    # WHEN
    result = PseudonimiseRedactor(pseudonymes).redact(
        content, positions
    )

    # THEN
    assert result in {
        "Lucas et Thomas",
        "Thomas et Lucas",
    }


def test_pseudonimisation_documents_independants():
    # GIVEN
    pseudonymes = {
        PII.first_name: ["Lucas"]
    }
    redactor = PseudonimiseRedactor(pseudonymes)

    document1 = "Bonjour Jean"
    positions1 = {
        creer_position(document1, "Jean", PII.first_name)
    }

    document2 = "Bonjour Pierre"
    positions2 = {
        creer_position(document2, "Pierre", PII.first_name)
    }

    # WHEN
    resultat1 = redactor.redact(document1, positions1)
    resultat2 = redactor.redact(document2, positions2)

    # THEN
    assert resultat1 == "Bonjour Lucas"
    assert resultat2 == "Bonjour Lucas"
    assert pseudonymes[PII.first_name] == ["Lucas"]
