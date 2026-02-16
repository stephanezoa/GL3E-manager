"""
Data validation utilities
"""
import re
from typing import Tuple


_STUDENT_NAME_PATTERN = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ' -]{2,120}$")
_DISALLOWED_INPUT_PATTERN = re.compile(r"[<>{}\\;$`]")


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not email:
        return False, "Email requis"
    
    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email.strip()):
        return False, "Format d'email invalide"
    
    return True, ""


def validate_student_name(name: str) -> Tuple[bool, str]:
    """
    Validate student name with strict character whitelist.
    """
    if not name:
        return False, "Nom étudiant requis"

    clean = name.strip()
    if len(clean) < 2 or len(clean) > 120:
        return False, "Nom étudiant invalide (longueur)"

    if not _STUDENT_NAME_PATTERN.match(clean):
        return False, "Nom étudiant invalide (caractères non autorisés)"

    return True, ""


def has_disallowed_input(value: str) -> bool:
    """
    Detect obvious dangerous characters or payload markers.
    """
    if not value:
        return False
    return bool(_DISALLOWED_INPUT_PATTERN.search(value))


def sanitize_input(text: str, max_length: int = 255) -> str:
    """
    Sanitize user input by removing potentially dangerous characters
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Limit length
    text = text[:max_length]
    
    # Remove any HTML tags (basic protection)
    text = re.sub(r'<[^>]+>', '', text)

    # Normalize internal spacing
    text = re.sub(r"\s+", " ", text)
    
    return text
