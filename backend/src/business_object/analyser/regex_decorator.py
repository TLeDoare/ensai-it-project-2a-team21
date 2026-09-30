import re

from .analyser_decorator import AnalyserDecorator


class RegexDecorator(AnalyserDecorator):
    """Ajoute la détection des PII reconnaissables par expressions régulières."""

    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

    def _detect_emails(self, content: str):
        return list(re.finditer(self.EMAIL_PATTERN, content))
    # ajout de l'analyse une fois les positions bien définies dans types