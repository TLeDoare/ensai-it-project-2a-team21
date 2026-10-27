from business_object.analyser.analyser_factory import AnalyserFactory
from business_object.analyser.llm_decorator import LLMDecorator
from business_object.analyser.regex_decorator import RegexDecorator


def test_analyser_factory_regex():
    # GIVEN
    params = {"detecteur": "regex"}

    # WHEN
    analyser = AnalyserFactory().get_analyser(params)

    # THEN (on vérifie la bonne encapsulation)
    assert isinstance(analyser, RegexDecorator)
