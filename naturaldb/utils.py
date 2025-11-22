from lock import lock_manager
import os

def sanitize_name(name: str) -> str:
    """
    Sanitize a name to be filesystem-friendly.
    """
    return "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()

def xss_sanitize(input_str: str) -> str:
    """
    Sanitize input to prevent XSS attacks.
    """
    replacements = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
        "/": "&#x2F;",
    }
    for old, new in replacements.items():
        input_str = input_str.replace(old, new)
    return input_str