import datetime

from utils.log_utils import get_logger
from utils.singleton import Singleton

from .db_connection import DBConnection

logger = get_logger(__name__)


class InjectionAttemptDAO(metaclass=Singleton):
    def register_attempt(self, email: str, content_hash: str, pattern_detected: str):
        """Enregistre une tentative d'injection de prompt."""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO prompt_injection_attempt (attempt_date, user_email, content_hash, pattern_detected)
                        VALUES (%(attempt_date)s, %(user_email)s, %(content_hash)s, %(pattern_detected)s)
                        """,
                        {
                            "attempt_date": datetime.datetime.now(),
                            "user_email": email,
                            "content_hash": content_hash,
                            "pattern_detected": pattern_detected
                        }
                    )
        except Exception as e:
            logger.error(f"Échec de l'enregistrement de la tentative d'injection : {e}")

    def get_all_attempts(self):
        """Récupère toutes les tentatives pour le dashboard."""
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM prompt_injection_attempt ORDER BY attempt_date DESC")
                return cursor.fetchall()
