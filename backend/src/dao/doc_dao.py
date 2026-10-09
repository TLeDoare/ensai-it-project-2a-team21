import json

from ..business_object.redacted_doc import RedactedDoc
from ..utils.singleton import Singleton
from .db_connection import DBConnection


class DocDAO(metaclass=Singleton):
    def register_document(self, doc: RedactedDoc, id_person: int) -> RedactedDoc:
        """To register a document in the database"""
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO redacteddoc (filename, upload_date, pii_count, pii_positions, file_path)        "
                    "     VALUES (%(filename)s, %(upload_date)s, %(pii_count)s, %(pii_positions)s, %(file_path)s)"
                    "  RETURNING id;                                                                 ",
                    {"filename": doc.filename,
                    "upload_date": doc.upload_date,
                    "pii_count": doc.params["count"],  # pas sûr, peut-être agréger avec un len(doc.positions)
                    # ouais, y a un risque d'avoir une keyError prcq params a pas forcément de clé count
                    # len(doc.details) nan? y a pas d'arg positions dans redacteddoc
                    "pii_positions": json.dumps(doc.details),
                    #details pas sérialisable? c'est un dict, ça alors que json c'est des tableaux
                    "file_path": doc.file_path}
                )
                id_généré = cursor.fetchone()["id"]
                doc.id = id_généré  # ajout à l'instance de classe
                cursor.execute(
                    "INSERT INTO traitement (id_person, id_doc)"
                    "     VALUES (%(id_person)s, %(id_doc)s)   ",
                    {"id_person": id_person ,  # ici il faut faire attention : on met sent_by... ou on fait autrement ?
                     # pas besoin de sent_by, id_person est fournie en argument nan? risque d'incohérence aussi
                     # ou sinon on supprime l'argument et on utilise que sent_by, en tt cas pas les 2 en mm temps
                    "id_doc": id_généré}
                )
        return doc
