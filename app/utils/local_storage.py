"""
Local storage utilities for cross-tab question persistence.

This module provides constants and helpers for storing question data
in browser localStorage, enabling multi-tab question generation.
"""

import json

# localStorage keys for question persistence and session management
STORAGE_KEYS = {
    "text_questions": "teacheraide_text_questions",
    "image_questions": "teacheraide_image_questions",
    "image_filenames": "teacheraide_image_filenames",
    "session_token": "teacheraide_session_token",
}


def get_save_text_questions_script(questions_json: str) -> str:
    """Generate JavaScript to save text questions to localStorage."""
    return f"localStorage.setItem('{STORAGE_KEYS['text_questions']}', {json.dumps(questions_json)})"


def get_save_image_questions_script(questions_json: str, filenames_json: str) -> str:
    """Generate JavaScript to save image questions and filenames to localStorage."""
    return f"""
        localStorage.setItem('{STORAGE_KEYS['image_questions']}', {json.dumps(questions_json)});
        localStorage.setItem('{STORAGE_KEYS['image_filenames']}', {json.dumps(filenames_json)});
    """


def get_clear_text_questions_script() -> str:
    """Generate JavaScript to clear text questions from localStorage."""
    return f"localStorage.removeItem('{STORAGE_KEYS['text_questions']}')"


def get_clear_image_questions_script() -> str:
    """Generate JavaScript to clear image questions and filenames from localStorage."""
    return f"""
        localStorage.removeItem('{STORAGE_KEYS['image_questions']}');
        localStorage.removeItem('{STORAGE_KEYS['image_filenames']}');
    """


def get_clear_all_questions_script() -> str:
    """Generate JavaScript to clear all question data from localStorage."""
    return f"""
        localStorage.removeItem('{STORAGE_KEYS['text_questions']}');
        localStorage.removeItem('{STORAGE_KEYS['image_questions']}');
        localStorage.removeItem('{STORAGE_KEYS['image_filenames']}');
    """


def get_load_all_questions_script() -> str:
    """Generate JavaScript to load all questions from localStorage."""
    return f"""
        (function() {{
            var textQ = localStorage.getItem('{STORAGE_KEYS['text_questions']}');
            var imageQ = localStorage.getItem('{STORAGE_KEYS['image_questions']}');
            var imageF = localStorage.getItem('{STORAGE_KEYS['image_filenames']}');
            return {{
                text_questions: textQ ? JSON.parse(textQ) : [],
                image_questions: imageQ ? JSON.parse(imageQ) : [],
                image_filenames: imageF ? JSON.parse(imageF) : []
            }};
        }})()
    """


# Session token management for SharedState linking
def get_or_create_session_token_script() -> str:
    """
    Generate JavaScript to get existing session token or create a new one.
    The token is used to link SharedState instances across browser tabs.
    Note: Token cannot contain underscores (Reflex SharedState limitation).
    """
    return f"""
        (function() {{
            var token = localStorage.getItem('{STORAGE_KEYS['session_token']}');
            if (!token) {{
                if (window.crypto && typeof window.crypto.randomUUID === 'function') {{
                    token = 'session-' + window.crypto.randomUUID().replace(/-/g, '');
                }} else if (window.crypto && typeof window.crypto.getRandomValues === 'function') {{
                    var bytes = new Uint8Array(16);
                    window.crypto.getRandomValues(bytes);
                    var hex = Array.from(bytes, function(b) {{
                        return b.toString(16).padStart(2, '0');
                    }}).join('');
                    token = 'session-' + hex;
                }} else {{
                    throw new Error('Secure token generation unavailable: crypto API not found.');
                }}
                localStorage.setItem('{STORAGE_KEYS['session_token']}', token);
            }}
            return token;
        }})()
    """


def get_session_token_script() -> str:
    """Generate JavaScript to get the current session token (may be null)."""
    return f"localStorage.getItem('{STORAGE_KEYS['session_token']}')"


def get_clear_session_token_script() -> str:
    """Generate JavaScript to clear the session token."""
    return f"localStorage.removeItem('{STORAGE_KEYS['session_token']}')"
