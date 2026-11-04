
from unittest.mock import MagicMock, patch

import pytest
from psycopg2.errors import UniqueViolation

from business_object.person import Person
from business_object.types import Role
from dao.person_dao import PersonDAO
from service.person_service import PersonService
from utils.exceptions import AuthError, EmailAlreadyUsed, PersonNotFound, WrongCredError

person_list = [
    Person(id=1, email="admin@mail.fr", password="1234", role=Role.Administrateur),
    Person(id=2, email="superviseur@mail.fr", password="0000", role=Role.Superviseur),
    Person(id=3, email="user@mail.fr", password="abcd", role=Role.Utilisateur),
]


# -------------------------
# CREATE
# -------------------------

@patch("service.person_service.hash_any", return_value="hashed_password")
def test_create_ok(mock_hash):
    """Successfully create a Person"""

    # GIVEN
    email = "new@mail.fr"
    password = "1234"
    role = Role.Utilisateur

    dao = PersonDAO()
    dao.find_by_email = MagicMock(return_value=None)
    dao.find_by_id = MagicMock(return_value=person_list[0])
    dao.create = MagicMock(return_value=Person(
        id=4,
        email=email,
        password="hashed_password",
        role=role
    ))

    # WHEN
    with patch("service.person_service.PersonDAO", return_value=dao):
        person = PersonService().create(email, password, role, person_list[0])

    # THEN
    assert person is not None
    assert person.email == email
    assert person.role == role
    mock_hash.assert_called_once_with(password, email)


def test_create_fail_email_already_used():
    """Fail to create a Person because the email is already used"""

    # GIVEN
    dao = PersonDAO()
    dao.find_by_email = MagicMock(return_value=person_list[0])

    with patch("service.person_service.PersonDAO", return_value=dao):
        # WHEN
        person = PersonService().create(
            "admin@mail.fr", "1234", Role.Utilisateur, person_list[0]
        )

    # THEN
    assert person is None


def test_create_fail_auth():
    """Fail to create a Person because the author is not an administrator"""

    # GIVEN
    dao = PersonDAO()
    dao.find_by_email = MagicMock(return_value=None)
    dao.find_by_id = MagicMock(return_value=person_list[2])

    with patch("service.person_service.PersonDAO", return_value=dao):
        # WHEN / THEN
        with pytest.raises(AuthError):
            PersonService().create(
                "new@mail.fr", "1234", Role.Utilisateur, person_list[2]
            )


def test_create_email_already_used_exception():
    """Raise EmailAlreadyUsed when DAO raises UniqueViolation"""

    # GIVEN
    dao = PersonDAO()
    dao.find_by_email = MagicMock(return_value=None)
    dao.find_by_id = MagicMock(return_value=person_list[0])
    dao.create = MagicMock(side_effect=UniqueViolation())

    with patch("service.person_service.PersonDAO", return_value=dao):
        # WHEN / THEN
        with pytest.raises(EmailAlreadyUsed):
            PersonService().create(
                "new@mail.fr", "1234", Role.Utilisateur, person_list[0]
            )


# -------------------------
# FIND ALL
# -------------------------

def test_find_all_admin():
    """An administrator can list all persons"""

    # GIVEN
    dao = PersonDAO()
    dao.find_by_id = MagicMock(return_value=person_list[0])
    dao.find_all = MagicMock(return_value=person_list)

    with patch("service.person_service.PersonDAO", return_value=dao):
        # WHEN
        res = PersonService().find_all(sent_by=person_list[0])

    # THEN
    assert len(res) == 3


def test_find_all_supervisor():
    """A supervisor can list all persons"""

    # GIVEN
    dao = PersonDAO()
    dao.find_by_id = MagicMock(return_value=person_list[1])
    dao.find_all = MagicMock(return_value=person_list)

    with patch("service.person_service.PersonDAO", return_value=dao):
        # WHEN
        res = PersonService().find_all(sent_by=person_list[1])

    # THEN
    assert len(res) == 3


def test_find_all_empty():
    """Raise PersonNotFound if there are no persons"""

    # GIVEN
    dao = PersonDAO()
    dao.find_by_id = MagicMock(return_value=person_list[0])
    dao.find_all = MagicMock(return_value=[])

    with patch("service.person_service.PersonDAO", return_value=dao):
        # WHEN / THEN
        with pytest.raises(PersonNotFound):
            PersonService().find_all(sent_by=person_list[0])


def test_find_all_unauthorized():
    """A regular user cannot list all persons"""

    # GIVEN
    dao = PersonDAO()
    dao.find_by_id = MagicMock(return_value=person_list[2])

    with patch("service.person_service.PersonDAO", return_value=dao):
        # WHEN / THEN
        with pytest.raises(AuthError):
            PersonService().find_all(sent_by=person_list[2])


# -------------------------
# FIND BY ID
# -------------------------

def test_find_by_id_ok():
    """An administrator can find a person by ID"""

    # GIVEN
    dao = PersonDAO()
    dao.find_by_id = MagicMock(return_value=person_list[1])

    with patch("service.person_service.PersonDAO", return_value=dao):
        # WHEN
        person = PersonService().find_by_id(id=2, sent_by=person_list[0])

    # THEN
    assert person.email == "superviseur@mail.fr"
    dao.find_by_id.assert_called_once_with(2)


def test_find_by_id_not_found():
    """Raise PersonNotFound if the person does not exist"""

    # GIVEN
    dao = PersonDAO()
    dao.find_by_id = MagicMock(return_value=None)

    with patch("service.person_service.PersonDAO", return_value=dao):
        # WHEN / THEN
        with pytest.raises(PersonNotFound):
            PersonService().find_by_id(id=99, sent_by=person_list[0])
    dao.find_by_id.assert_called_once_with(99)


def test_find_by_id_unauthorized():
    """A regular user cannot find a person by ID"""

    # GIVEN
    dao = PersonDAO()
    dao.find_by_id = MagicMock(return_value=person_list[2])

    with patch("service.person_service.PersonDAO", return_value=dao):
        # WHEN / THEN
        with pytest.raises(AuthError):
            PersonService().find_by_id(id=1, sent_by=person_list[2])


# -------------------------
# LOGIN
# -------------------------

@patch("service.person_service.verify_password", return_value=True)
@patch("service.person_service.secrets.token_urlsafe", return_value="fake_token")
def test_login_ok(mock_token, mock_verify):
    """Successfully authenticate a Person"""

    # GIVEN
    person = person_list[0]
    dao = PersonDAO()
    dao.find_by_email = MagicMock(return_value=person)
    dao.update_access_token = MagicMock()

    with patch("service.person_service.PersonDAO", return_value=dao):
        # WHEN
        res = PersonService().login(person.email, "1234")

    # THEN
    assert res == person
    assert res.access_token == "fake_token"
    dao.update_access_token.assert_called_once_with(
        person.id, "fake_token"
    )


def test_login_email_not_found():
    """Return None if the email does not exist"""

    # GIVEN
    dao = PersonDAO()
    dao.find_by_email = MagicMock(return_value=None)

    with patch("service.person_service.PersonDAO", return_value=dao):
        # WHEN / THEN
        with pytest.raises(WrongCredError):
            res = PersonService().login("unknown@mail.fr", "1234")


@patch("service.person_service.verify_password", return_value=False)
def test_login_wrong_password(mock_verify):
    """Return None if the password is incorrect"""

    # GIVEN
    person = person_list[0]
    dao = PersonDAO()
    dao.find_by_email = MagicMock(return_value=person)
    dao.update_access_token = MagicMock()

    with patch("service.person_service.PersonDAO", return_value=dao):
        # WHEN/THEN
        with pytest.raises(WrongCredError):
            res = PersonService().login(person.email, "wrong_password")

    dao.update_access_token.assert_not_called()
