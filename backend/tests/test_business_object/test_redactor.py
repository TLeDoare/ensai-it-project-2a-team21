import pytest

from business_object.redactor.mask_redactor import MaskRedactor
from business_object.redactor.pseudonimise_redactor import PseudonimiseRedactor
from business_object.types import PII, Position
from business_object.types import Analyser as AnalyserSource
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

    # WHEN
    result = PseudonimiseRedactor().redact(
        content, positions
    )

    # THEN
    assert result[8:] != "Jean"


def test_pseudonimisation_repetition():
    # GIVEN
    content = "Jean parle avec Jean"
    positions = {
        creer_position(content, "Jean", PII.first_name, 0),
        creer_position(content, "Jean", PII.first_name, 1),
    }

    # WHEN
    result = PseudonimiseRedactor().redact(
        content, positions
    )

    # THEN
    liste_res = result.split(" ")
    assert liste_res[0] != "Jean"
    assert liste_res[-1] != "Jean"
    assert liste_res[0] == liste_res[-1]


def test_pseudonimisation_valeurs_differentes():
    # GIVEN
    content = "Jean et Pierre"
    positions = {
        creer_position(content, "Jean", PII.first_name),
        creer_position(content, "Pierre", PII.first_name),
    }

    # WHEN
    result = PseudonimiseRedactor().redact(
        content, positions
    )

    # THEN

    liste_res = result.split(" ")
    assert liste_res[0] != liste_res[2]


def test_pseudonimisation_valeur_originale_exclue():
    # GIVEN
    content = "Jean et Marc"
    positions = {
        creer_position(content, "Jean", PII.first_name),
        creer_position(content, "Marc", PII.first_name),
    }

    # WHEN
    result = PseudonimiseRedactor().redact(
        content, positions
    )

    # THEN

    liste_res = result.split(" ")
    liste_content = content.split(" ")
    assert liste_res[0] != liste_content[0] and liste_res[0] != liste_content[2] or liste_res[2] != liste_content[0] and liste_res[2] != liste_content[2]


def test_fusion_chevauchement_PII_differentes():
    # GIVEN
    # Contenu : "0123456789 48.8584"
    # On veut créer un chevauchement sur les chiffres "456789"
    content = "0123456789 48.8584"

    positions = {
        # Le numéro de téléphone (index 0 à 10)
        Position(
            indices=(0, 10),
            PII=PII.phone_number,
            confidence=1.0,
            analyser_source=AnalyserSource.Regex,
        ),
        # Une coordonnée GPS qui commence au milieu du téléphone (index 5 à 15)
        Position(
            indices=(5, 15),
            PII=PII.GPS,
            confidence=1.0,
            analyser_source=AnalyserSource.Regex,
        ),
    }

    # WHEN / THEN
    # L'algorithme de fusion va rencontrer l'intervalle (5, 15) alors qu'il traite (0, 10).
    # Comme 5 < 10, il fusionne mais voit que PII.phone_number != PII.GPS
    with pytest.raises(PseudonymisationImpossible) as excinfo:
        PseudonimiseRedactor().redact(content, positions)

    assert "Chevauchement de types de PII différents" in str(excinfo.value)
