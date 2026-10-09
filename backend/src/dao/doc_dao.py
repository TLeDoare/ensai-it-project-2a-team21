import json

from ..business_object.redacted_doc import RedactedDoc
from ..utils.singleton import Singleton
from .db_connection import DBConnection


class DocDAO(metaclass=Singleton):
    def register_document(self, doc: RedactedDoc, id_person: int) -> bool:
        """To register a document in the database"""
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO redacteddoc (filename, upload_date, pii_count, pii_positions, file_path)        "
                    "     VALUES (%(filename)s, %(upload_date)s, %(pii_count)s, %(pii_positions)s, %(file_path)s)"
                    "  RETURNING id;",
                    {
                        "filename": doc.filename,
                        "upload_date": doc.upload_date,
                        "pii_count": len(doc.positions),
                        "pii_positions": json.dumps(doc.details),
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
