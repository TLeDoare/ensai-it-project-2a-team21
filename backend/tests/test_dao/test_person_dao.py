import pytest

from pathlib import Path
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from dotenv import load_dotenv
from psycopg2 import errors
from business_object.person import Person
from business_object.types import Role
from dao.db_connection import DBConnection
from dao.person_dao import PersonDAO


@pytest.fixture
def personne_test(connexion_test):
    """Crée un utilisateur fictif et le supprime après le test."""

    email = f"test-{uuid4().hex}@example.com"

    person = Person(
        email=email,
        password="hash_fictif",
        role=Role.Utilisateur,
    )

    dao = PersonDAO()
    person = dao.create(person)

    try:
        yield person
    finally:
        with connexion_test:
            with connexion_test.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM Person WHERE id = %s",
                    (person.id,),
                )



def test_create_person(connexion_test):
    """Vérifie la création d'un utilisateur dans la BDD."""

    # GIVEN
    email = f"test-{uuid4().hex}@example.com"

    person = Person(
        email=email,
        password="hash_fictif",
        role=Role.Utilisateur,
        access_token=None,
    )

    dao = PersonDAO()

    try:
        # WHEN
        created_person = dao.create(person)

        # THEN
        assert created_person.id is not None
        assert created_person.email == email

        # Vérifier les données réellement stockées dans PostgreSQL
        with connexion_test.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM Person WHERE email = %s",
                (email,),
            )
            result = cursor.fetchone()

        assert result is not None
        assert result["id"] == created_person.id
        assert result["email"] == email
        assert result["password"] == "hash_fictif"
        assert result["role"] == "utilisateur"

    finally:
        # CLEANUP
        with connexion_test:
            with connexion_test.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM Person WHERE email = %s",
                    (email,),
                )


def test_find_by_id(personne_test):
    # GIVEN
    dao = PersonDAO()

    # WHEN
    result = dao.find_by_id(personne_test.id)

    # THEN
    assert result is not None
    assert result.id == personne_test.id
    assert result.email == personne_test.email
    assert result.role == Role.Utilisateur


def test_find_by_id_inexistant(connexion_test):
    # GIVEN
    dao = PersonDAO()

    # WHEN
    result = dao.find_by_id(-1)

    # THEN
    assert result is None


def test_find_by_email(personne_test):
    # GIVEN
    dao = PersonDAO()

    # WHEN
    result = dao.find_by_email(personne_test.email)

    # THEN
    assert result is not None
    assert result.id == personne_test.id
    assert result.email == personne_test.email


def test_find_by_email_inexistant(connexion_test):
    # GIVEN
    dao = PersonDAO()
    email = f"inexistant-{uuid4().hex}@example.com"

    # WHEN
    result = dao.find_by_email(email)

    # THEN
    assert result is None


def test_find_by_token(personne_test):
    """Vérifie qu'un jeton valide permet de retrouver l'utilisateur."""

    # GIVEN
    dao = PersonDAO()
    token = f"jeton-{uuid4().hex}"
    expiration = datetime.now(timezone.utc) + timedelta(hours=24)

    dao.update_access_token(personne_test.id, token, expiration)

    # WHEN
    resultat = dao.find_by_token(token)

    # THEN
    assert resultat is not None
    assert resultat.id == personne_test.id
    assert resultat.email == personne_test.email
    assert resultat.access_token is None


def test_find_by_token_inexistant(connexion_test):
    # GIVEN
    dao = PersonDAO()

    # WHEN
    result = dao.find_by_token("jeton-inexistant")

    # THEN
    assert result is None


def test_find_all(personne_test):
    # GIVEN
    dao = PersonDAO()

    # WHEN
    results = dao.find_all()

    # THEN
    assert isinstance(results, list)
    assert any(person.id == personne_test.id for person in results)

    person = next(
        p for p in results if p.id == personne_test.id
    )
    assert person.role == Role.Utilisateur



def test_update_access_token(personne_test, connexion_test):
    """Vérifie que le jeton est stocké sous forme d'empreinte."""

    # GIVEN
    dao = PersonDAO()
    token = f"jeton-{uuid4().hex}"
    expiration = datetime.now(timezone.utc) + timedelta(hours=24)

    # WHEN
    dao.update_access_token(personne_test.id, token, expiration)

    # THEN
    with connexion_test.cursor() as cursor:
        cursor.execute(
            """
            SELECT access_token_hash,
                   access_token_expires_at
            FROM Person
            WHERE id = %s
            """,
            (personne_test.id,),
        )
        resultat = cursor.fetchone()

    assert resultat["access_token_hash"] == sha256(
        token.encode("utf-8")
    ).hexdigest()
    assert resultat["access_token_expires_at"] == expiration


def test_update_person(personne_test):
    # GIVEN
    dao = PersonDAO()

    personne_test.email = f"modifie-{uuid4().hex}@example.com"
    personne_test.password = "nouveau_hash_fictif"
    personne_test.role = Role.Superviseur

    # WHEN
    updated = dao.update(personne_test)

    # THEN
    assert updated is True

    result = dao.find_by_id(personne_test.id)

    assert result is not None
    assert result.email == personne_test.email
    assert result.password == "nouveau_hash_fictif"
    assert result.role == Role.Superviseur


def test_update_person_inexistante(connexion_test):
    # GIVEN
    dao = PersonDAO()

    person = Person(
        id=-1,
        email="inexistant@example.com",
        password="hash_fictif",
        role=Role.Utilisateur,
        access_token=None,
    )

    # WHEN
    updated = dao.update(person)

    # THEN
    assert updated is False


def test_create_email_deja_utilise(personne_test):
    """Vérifie que deux utilisateurs ne peuvent pas avoir le même email."""

    # GIVEN
    dao = PersonDAO()

    autre_personne = Person(
        email=personne_test.email,
        password="autre_hash",
        role=Role.Utilisateur,
        access_token=None,
    )

    # WHEN / THEN
    with pytest.raises(errors.UniqueViolation):
        dao.create(autre_personne)

    # Vérifier que l'utilisateur initial existe toujours
    result = dao.find_by_email(personne_test.email)

    assert result is not None
    assert result.id == personne_test.id


def test_create_sans_email(connexion_test):
    """Vérifie que la BDD refuse un utilisateur sans email."""

    # GIVEN
    dao = PersonDAO()

    personne = Person(
        email=None,
        password="hash_fictif",
        role=Role.Utilisateur,
        access_token=None,
    )

    # WHEN / THEN
    with pytest.raises(errors.NotNullViolation):
        dao.create(personne)


def test_find_by_token_expire(personne_test):
    """Un jeton expiré ne permet plus de retrouver l'utilisateur."""

    # GIVEN
    dao = PersonDAO()
    token = f"jeton-{uuid4().hex}"

    # Date d'expiration située dans le passé
    expiration = datetime.now(timezone.utc) - timedelta(hours=1)

    dao.update_access_token(personne_test.id, token, expiration)

    # WHEN
    resultat = dao.find_by_token(token)

    # THEN
    assert resultat is None


def test_revoke_access_token(personne_test, connexion_test):
    """Un jeton révoqué ne peut plus être utilisé."""

    # GIVEN
    dao = PersonDAO()
    token = f"jeton-{uuid4().hex}"
    expiration = datetime.now(timezone.utc) + timedelta(hours=24)

    dao.update_access_token(personne_test.id, token, expiration)

    # Vérifie que le jeton fonctionne avant révocation
    assert dao.find_by_token(token) is not None

    # WHEN
    resultat = dao.revoke_access_token(token)

    # THEN
    assert resultat is True

    # L'ancien jeton n'est plus valide
    assert dao.find_by_token(token) is None

    # Les informations de session ont disparu de PostgreSQL
    with connexion_test.cursor() as cursor:
        cursor.execute(
            """
            SELECT access_token_hash, access_token_expires_at
            FROM Person
            WHERE id = %s
            """,
            (personne_test.id,),
        )
        ligne = cursor.fetchone()

    assert ligne["access_token_hash"] is None
    assert ligne["access_token_expires_at"] is None
