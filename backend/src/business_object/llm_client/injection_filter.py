import re


class InjectionFilter:
    """Filtre en amont pour détecter les tentatives d'injection de prompt dans le document."""

    INJECTION_PATTERNS = [
        r"ignore\s+(previous|all)\s+instructions?",
        r"oublie\s+(tes|les)\s+instructions?",
        r"system\s*[:=]",
        r"tu\s+es\s+maintenant",
        r"nouveau\s+rôle",
        r"désactive\s+le\s+caviardage",
        r"<\|im_start\|>",
        r"```system",
        r"réponds\s+uniquement\s+par",
    ]

    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]

    def detect_injection(self, document: str) -> bool:
        """Renvoie True si un motif d'injection suspect est détecté dans le document."""
        for pattern in self.patterns:
            if pattern.search(document):
                return True
        return False
