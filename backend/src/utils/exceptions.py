class DocRegistrationError(Exception):
    """Erreur métier levée quand l'enregistrement d'un document échoue."""

class AuthError(Exception):
    """Erreur levée quand un individu réalise une action qu'il n'a pas le droit de réaliser."""

class DocNotFound(Exception):
    """Erreur levée quand un ou plusieurs documents ne sont pas trouvés"""
