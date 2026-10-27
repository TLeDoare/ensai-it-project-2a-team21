import pytest

from business_object.analyser.empty_analyser import EmptyAnalyser
from business_object.analyser.regex_decorator import RegexDecorator
from business_object.types import PII, Position, Positions
from business_object.types import Analyser as AnalyserSource


@pytest.mark.asyncio
async def test_regex_decorator_detects_email():
    # GIVEN
    text = "Contactez-moi à l'adresse test.user@example.com pour plus d'infos."

    wrapper = EmptyAnalyser()

    # On instancie le RegexDecorator avec son wrapper et des paramètres vides
    decorator = RegexDecorator(wrapper=wrapper, params={})

    # WHEN : On appelle la méthode asynchrone analyse
    positions = await decorator.analyse(text)

    # THEN : On vérifie que la PII a bien été détectée et transformée en Position
    assert len(positions) == 1
    position = list(positions)[0]

    assert position.PII == PII.email
    assert position.analyser_source == AnalyserSource.Regex
    assert position.confiance == 1.0
    # Vérification que les indices extraits correspondent bien à l'email dans le texte
    start, end = position.indices
    assert text[start:end] == "test.user@example.com"
