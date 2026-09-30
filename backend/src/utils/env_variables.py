import logging

import dotenv


def load_environment_variables():
    """Loads environment variables from the .env file."""
    succes = dotenv.load_dotenv(override=True)
    logging.info(f"Load environment variables: {'SUCCES' if succes else 'FAIL'}")


def mask_value(key, value):
    """Masks sensitive values based on their key name.
    Args:
        key (str): The name of the environment variable.
        value (str): The actual value of the environment variable.
    Returns:
        str: A masked string ("*******") if the key contains sensitive
            keywords, otherwise the original value.
    """
    sensitive_keywords = ["PASSWORD", "SECRET", "KEY", "TOKEN"]

    if any(word in key.upper() for word in sensitive_keywords):
        return "*******"
    return value


def display_values(include_prefix=None, exclude_prefix=None):
    """
    Logs all environment variables filtering and masking sensitive values.
    Args:
        include_prefix (str, optional): If provided, only keys starting with
            this prefix will be logged.
        exclude_prefix (str, optional): If provided, keys starting with this
            prefix will be skipped.
    """
    for key, value in dotenv.dotenv_values().items():
        if include_prefix and not key.startswith(include_prefix):
            continue
        if exclude_prefix and key.startswith(exclude_prefix):
            continue
        logging.info(f"{key}={mask_value(key, value)}")
