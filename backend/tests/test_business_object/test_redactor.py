import pytest
from business_object.redactor.anonym_redactor import AnonymRedactor

from business_object.redactor.mask_redactor import MaskRedactor


@pytest.mark.parametrize("redactor, positions, attendu", [
    (
        MaskRedactor(),
        [{"start": 21, "end": 32, "type": "name"}],
        "Bonjour je m'appelle [NAME]."
    ),
    (
        AnonymRedactor(),
        [{"start": 21, "end": 32, "type": "name"}],
        "Bonjour je m'appelle [NAME]."
    ),
])
def test_redactor_strategies(redactor, positions, attendu):
    text = "Bonjour, je m'appelle Tanguy LeDoaré"
    result = redactor.redact(text, positions)
    assert result == attendu
