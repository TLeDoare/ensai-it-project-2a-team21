"""Tests du chargement et de l'affichage des variables d'environnement (masquage des secrets)."""

import logging
from unittest.mock import patch

import pytest

from utils.env_variables import display_values, load_environment_variables, mask_value


@pytest.mark.parametrize(
    "cle, masquee",
    [
        ("POSTGRES_PASSWORD", True),
        ("DOC_HASH_SECRET", True),
        ("SSPCLOUD_API_KEY", True),
        ("ACCESS_TOKEN", True),
        ("postgres_password", True),  # insensible à la casse
        ("POSTGRES_HOST", False),
        ("LLM_MODEL", False),
    ],
)
def test_mask_value(cle, masquee):
    """Les valeurs sensibles sont remplacées par des étoiles, les autres sont gardées."""
    attendu = "*******" if masquee else "valeur"
    assert mask_value(cle, "valeur") == attendu


@patch("utils.env_variables.dotenv.load_dotenv", return_value=True)
def test_load_environment_variables(mock_load, caplog):
    """Le chargement du .env est journalisé, en écrasant les variables déjà présentes."""
    with caplog.at_level(logging.INFO):
        load_environment_variables()

    mock_load.assert_called_once_with(override=True)
    assert "SUCCES" in caplog.text


VALEURS = {"POSTGRES_HOST": "localhost", "POSTGRES_PASSWORD": "secret", "LLM_MODEL": "gemma"}


@patch("utils.env_variables.dotenv.dotenv_values", return_value=VALEURS)
def test_display_values_masque_les_secrets(mock_values, caplog):
    """Toutes les variables sont affichées, mais jamais la valeur d'un secret."""
    with caplog.at_level(logging.INFO):
        display_values()

    assert "POSTGRES_HOST=localhost" in caplog.text
    assert "POSTGRES_PASSWORD=*******" in caplog.text
    assert "secret" not in caplog.text


@patch("utils.env_variables.dotenv.dotenv_values", return_value=VALEURS)
def test_display_values_filtre_par_prefixe(mock_values, caplog):
    """include_prefix garde seulement les clés qui commencent par le préfixe, exclude_prefix les retire."""
    with caplog.at_level(logging.INFO):
        display_values(include_prefix="POSTGRES", exclude_prefix="POSTGRES_PASS")

    assert "POSTGRES_HOST" in caplog.text
    assert "POSTGRES_PASSWORD" not in caplog.text
    assert "LLM_MODEL" not in caplog.text
