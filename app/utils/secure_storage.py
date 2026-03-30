"""Secure local storage helpers for API keys."""

from __future__ import annotations

import importlib
import logging

API_KEY_FIELDS: tuple[str, ...] = (
    "openai_api_key",
    "anthropic_api_key",
    "gemini_api_key",
)

_KEYRING_SERVICE = "TeacherAIde.APIKeys"
_KEYRING_USERNAMES = {
    "openai_api_key": "openai",
    "anthropic_api_key": "anthropic",
    "gemini_api_key": "gemini",
}


def _get_keyring_module():
    try:
        return importlib.import_module("keyring")
    except Exception:
        return None


def load_api_keys() -> tuple[dict[str, str], bool, list[str]]:
    """Load provider API keys from OS-backed keyring if available."""
    keyring = _get_keyring_module()
    if keyring is None:
        return {}, False, []

    warnings: list[str] = []
    keys: dict[str, str] = {}
    for field in API_KEY_FIELDS:
        username = _KEYRING_USERNAMES[field]
        try:
            value = keyring.get_password(_KEYRING_SERVICE, username)
            keys[field] = value or ""
        except Exception as e:
            warnings.append(f"Failed to read {field} from secure storage: {str(e)}")
            keys[field] = ""
            logging.warning("Failed to read %s from keyring: %s", field, str(e))

    return keys, True, warnings


def save_api_keys(api_keys: dict[str, str]) -> tuple[bool, bool, list[str]]:
    """Persist provider API keys to OS-backed keyring if available."""
    keyring = _get_keyring_module()
    if keyring is None:
        return (
            False,
            False,
            ["Secure key storage unavailable; API keys are not persisted to disk."],
        )

    warnings: list[str] = []
    all_saved = True

    for field in API_KEY_FIELDS:
        username = _KEYRING_USERNAMES[field]
        value = str(api_keys.get(field, "") or "")
        try:
            if value:
                keyring.set_password(_KEYRING_SERVICE, username, value)
            else:
                try:
                    keyring.delete_password(_KEYRING_SERVICE, username)
                except Exception:
                    # Clearing a missing secret should not fail save flow.
                    pass
        except Exception as e:
            all_saved = False
            warnings.append(f"Failed to save {field} to secure storage: {str(e)}")
            logging.warning("Failed to save %s to keyring: %s", field, str(e))

    return all_saved, True, warnings
