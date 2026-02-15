"""
Data validation utilities
"""
import re
from typing import Tuple


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
    
    return text
