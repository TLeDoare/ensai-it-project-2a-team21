import json

from business_object.redacted_doc import RedactedDoc
from utils.singleton import Singleton
from .db_connection import DBConnection


class DocDAO(metaclass=Singleton):
    def register_document(self, doc: RedactedDoc, id_person: int) -> bool:
        """To register a document in the database"""
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO redacteddoc (filename, upload_date, pii_count, pii_positions, params)        "
                    "     VALUES (%(filename)s, %(upload_date)s, %(pii_count)s, %(pii_positions)s, %(params)s)"
                    "  RETURNING id;",
                    {
                        "filename": doc.filename,
                        "upload_date": doc.upload_date,
                        "pii_count": len(doc.details),
                        "pii_positions": str(doc.details),
                        "params": json.dumps(doc.params)
                    }
                )
                res = cursor.fetchone()
                id_généré = res["id"]
                doc.id = id_généré  # ajout à l'instance de classe
                cursor.execute(
                    "INSERT INTO traitement (id_person, id_doc)"
                    "     VALUES (%(id_person)s, %(id_doc)s)   ",
                    {
                        "id_person": id_person,
                        "id_doc": id_généré
                    }
                )
        return res is not None

    def find_by_id(self, id: int) -> RedactedDoc:
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, filename, upload_date, pii_count, pii_positions, params
                    FROM redactedoc
                    WHERE id = %(id)s
                    """,
                    {
                        "id": id
                    }
                )
                doc_found = cursor.fetchone()
                RedactedDoc = None
                if doc_found:
                    RedactedDoc = RedactedDoc(
                        filename=doc_found["filename"],
                        upload_date=doc_found["upload_date"],
                        sent_by=doc_found["sent_by"],
                        params=doc_found["params"],
                        details=doc_found["details"],
                        id=doc_found["id"]
                    )
        return RedactedDoc

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
                        filename=doc["filename"],
                        upload_date=doc["upload_date"],
                        sent_by=doc["sent_by"],
                        params=doc["params"],
                        details=doc["details"],
                        id=doc["id"]
                    )
                )
        return liste_doc

    def find_by_user(self, id_person: int) -> list[RedactedDoc]:
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM redacteddoc
                    WHERE sent_by = %(id_person)s
                    """,
                    {
                        "id_person": id_person
                    }
                )
                doc_bdd = cursor.fetchall()
        liste_doc = []
        if doc_bdd:
            for doc in doc_bdd:
                liste_doc.append(
                    RedactedDoc(
                        filename=doc["filename"],
                        upload_date=doc["upload_date"],
                        sent_by=doc["sent_by"],
                        params=doc["params"],
                        details=doc["details"],
                        id=doc["id"]
                    )
                )
        return liste_doc

    def find_with_filter(self, filter) -> list[RedactedDoc]:
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM redacteddoc
                    WHERE filter = %(filter)s
                    """,
                    {
                        "filter": filter
                    }
                )
                doc_bdd = cursor.fetchall()
        liste_doc = []
        if doc_bdd:
            for doc in doc_bdd:
                liste_doc.append(
                    RedactedDoc(
                        filename=doc["filename"],
                        upload_date=doc["upload_date"],
                        sent_by=doc["sent_by"],
                        params=doc["params"],
                        details=doc["details"],
                        id=doc["id"]
                    )
                )
        return liste_doc

    def update(self, doc) -> bool:
        """Update a doc in the database.
        Args:
            doc to be updated
        Returns:
            True if update is successful, False otherwise
        """
        nb_affected_rows = 0
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE redacteddoc                                                  "
                    "   SET filename = %(filename)s,                                "
                    "       upload_date = %(upload_date)s,            "
                    "       sent_by = %(sent_by)s,                                          "
                    "       params = %(params)s,                                      "
                    "       details = %(details)s,                          "
                    "       id = %(id)s "
                    " WHERE id_doc = %(id_doc)s;                              ",
                    {
                        "filename": doc.filename,
                        "upload_date": doc.upload_date,
                        "sent_by": doc.sent_by,
                        "params": doc.params,
                        "details": doc.details,
                        "id": doc.id,
                        "id_doc": doc.id_doc,
                    },
                )
                nb_affected_rows = cursor.rowcount
        return nb_affected_rows == 1

    def delete(self, doc) -> bool:
        """Delete a doc from the database.
        Args:
            Doc to delete from the database
        Returns:
            True if the doc was successfully deleted, False otherwise
        """
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM doc                               "
                    " WHERE id_doc = %(id_doc)s                 ",
                    {"id_doc": doc.id_doc},
                )
                res = cursor.rowcount
        return res > 0
