import pytest


from business_object.redactor.mask_redactor import MaskRedactor
from business_object.types import Position, PII, Analyser as AnalyserSource

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
