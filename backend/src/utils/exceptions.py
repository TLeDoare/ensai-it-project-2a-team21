class DocRegistrationError(Exception):
    """Erreur métier levée quand l'enregistrement d'un document échoue."""

class AuthError(Exception):
    """Erreur levée quand un individu réalise une action qu'il n'a pas le droit de réaliser."""

class DocNotFound(Exception):
    """Erreur levée quand un ou plusieurs documents ne sont pas trouvés."""

class PersonNotFound(Exception):
    """Erreur levée quand une ou plusieurs personnes ne sont pas trouvées."""

class EmailAlreadyUsed(Exception):
    """L'adresse e-mail est déjà utilisée par un autre compte."""

class PseudonymisationImpossible(Exception):
    """Erreur levée lorsque la pseudonymisation ne peut pas être effectuée."""

class WrongCredError(Exception):
    """Erreur levée lorsque l'email ou le mot de passe utilisé pour le login sont mauvais"""

class LLMInjectionError(Exception):
    """Erreur levée lors de tentative d'injection"""

class LLMParseError(Exception):
    """Erreur levée lors de tentative d'injection"""

class RedactorError(Exception):
    """Erreur levée lorsque le caviardeur rencontre un problème."""
