import json
from ast import literal_eval

import psycopg2

from business_object.redacted_doc import RedactedDoc
from utils.exceptions import DocRegistrationError
from utils.log_utils import get_logger
from utils.singleton import Singleton

from .db_connection import DBConnection

logger = get_logger(__name__)


class DocDAO(metaclass=Singleton):
    def register_document(self, doc: RedactedDoc) -> bool:
        """To register a document in the database"""
        try:
            with DBConnection().connection as connection:
                with connection.cursor() as cursor:
                        cursor.execute(
                            "INSERT INTO redacteddoc (doc_hash, upload_date, pii_count, pii_positions, params, author_email)        "
                            "     VALUES (%(doc_hash)s, %(upload_date)s, %(pii_count)s, %(pii_positions)s, %(params)s, %(author)s)"
                            "  RETURNING id;",
                            {
                                "doc_hash": doc.hash,
                                "upload_date": doc.upload_date,
                                "pii_count": len(doc.details),
                                "pii_positions": json.dumps(list(doc.details)),
                                "params": str(doc.params),
                                "author": doc.sent_by
                            }
                        )
                        res = cursor.fetchone()
                        id_généré = res["id"]
                        doc.id = id_généré  # ajout à l'instance de classe

        except psycopg2.Error as erreur:
            logger.error(
                "Échec de l'enregistrement du document '%s' : %s",
                doc.hash, erreur,
            )
            raise DocRegistrationError(
                "Impossible d'enregistrer le document en base."
            ) from erreur

        logger.info(
            "Document '%s' enregistré (id=%s, %d PII)",
            doc.hash, doc.id, len(doc.details),
        )
        return True

    def find_by_id(self, id: int) -> RedactedDoc:
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, doc_hash, upload_date, pii_positions, params, author_email
                    FROM redacteddoc
                    WHERE id = %(id)s
                    """,
                    {
                        "id": id
                    }
                )
                doc_found = cursor.fetchone()
                redacted_doc = None
                if doc_found:
                    redacted_doc = RedactedDoc(
                        hash=doc_found["doc_hash"],
                        upload_date=doc_found["upload_date"],
                        params=literal_eval(doc_found["params"]),
                        details=literal_eval(doc_found["pii_positions"]),
                        id=doc_found["id"],
                        sent_by=doc_found["author_email"]
                    )
        return redacted_doc

    def find_all(self) -> list[RedactedDoc]:
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM redacteddoc
                    """
                )
                doc_bdd = cursor.fetchall()
        liste_doc = []
        if doc_bdd:
            for doc in doc_bdd:
                liste_doc.append(
                    RedactedDoc(
                        hash=doc["doc_hash"],
                        upload_date=doc["upload_date"],
                        params=literal_eval(doc["params"]),
                        details=literal_eval(doc["pii_positions"]),
                        id=doc["id"],
                        sent_by=doc["author_email"]
                    )
                )
        return liste_doc
