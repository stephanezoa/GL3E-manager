"""
Phone validation utilities for Cameroon phone numbers
"""
import re
from typing import Tuple


def is_valid_cameroon_phone(phone: str) -> bool:
    """
    Validate Cameroon phone number formats:
    - 6XX XX XX XX (with spaces)
    - 6XXXXXXXX (without spaces)
    - 237XXXXXXXXX (with country code)
    - +237XXXXXXXXX (international format)
    
    Args:
        phone: Phone number string to validate
        
    Returns:
        bool: True if valid Cameroon number, False otherwise
    """
    if not phone:
        return False
    
    phone = phone.strip()
    
    patterns = [
        r'^6\d{2}\s?\d{2}\s?\d{2}\s?\d{2}$',  # 6XX XX XX XX or 6XXXXXXXX
        r'^237\d{9}$',  # 237XXXXXXXXX
        r'^\+237\d{9}$'  # +237XXXXXXXXX
    ]
    
    return any(re.match(pattern, phone) for pattern in patterns)


def normalize_cameroon_phone(phone: str) -> str:
    """
    Normalize Cameroon phone number to international format (+237XXXXXXXXX)
    
    Args:
        phone: Phone number to normalize
        
    Returns:
        str: Normalized phone number
        
    Raises:
        ValueError: If phone number is invalid
    """
    if not is_valid_cameroon_phone(phone):
        raise ValueError(f"Invalid Cameroon phone number: {phone}")
    
    # Remove all spaces
    phone = phone.replace(" ", "")
    
    # If starts with 6, add country code
    if phone.startswith("6"):
        return f"+237{phone}"
    
    # If starts with 237, add +
    if phone.startswith("237"):
        return f"+{phone}"
    
    # Already in correct format
    return phone


def validate_and_normalize_phone(phone: str) -> Tuple[bool, str, str]:
    """
    Validate and normalize phone number
    
    Args:
        phone: Phone number to validate
        
    Returns:
        Tuple[bool, str, str]: (is_valid, normalized_phone, error_message)
    """
    try:
        if not is_valid_cameroon_phone(phone):
            return False, "", "Format de numéro invalide. Utilisez: 6XX XX XX XX, 237XXXXXXXXX ou +237XXXXXXXXX"
        
        normalized = normalize_cameroon_phone(phone)
        return True, normalized, ""
    except Exception as e:
        return False, "", str(e)
