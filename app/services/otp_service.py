"""
OTP generation and validation service
"""
import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.otp import OTPCode
from app.models.student import Student
from app.config import settings


def generate_otp_code(length: int = None) -> str:
    """
    Generate a random OTP code
    
    Args:
        length: Length of OTP code (default from settings)
        
    Returns:
        str: Generated OTP code
    """
    if length is None:
        length = settings.OTP_LENGTH
    
    return ''.join(random.choices(string.digits, k=length))


async def create_otp(
    db: Session,
    student_id: int,
    contact_method: str,
    contact_value: str,
    sms_provider: str = None
) -> OTPCode:
    """
    Create and store a new OTP code
    
    Args:
        db: Database session
        student_id: Student ID
        contact_method: 'email' or 'sms'
        contact_value: Email address or phone number
        sms_provider: SMS provider used ('mtarget' or 'twilio')
        
    Returns:
        OTPCode: Created OTP record
    """
    # Generate OTP code
    code = generate_otp_code()
    
    # Calculate expiration time
    expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    
    # Create OTP record
    otp = OTPCode(
        student_id=student_id,
        code=code,
        contact_method=contact_method,
        contact_value=contact_value,
        sms_provider=sms_provider,
        expires_at=expires_at,
        verified=False,
        attempts=0
    )
    
    db.add(otp)
    db.commit()
    db.refresh(otp)
    
    return otp


async def verify_otp(
    db: Session,
    otp_id: int,
    code: str
) -> tuple[bool, str, OTPCode]:
    """
    Verify an OTP code
    
    Args:
        db: Database session
        otp_id: OTP record ID
        code: OTP code to verify
        
    Returns:
        tuple[bool, str, OTPCode]: (is_valid, error_message, otp_record)
    """
    # Get OTP record
    otp = db.query(OTPCode).filter(OTPCode.id == otp_id).first()
    
    if not otp:
        return False, "Code OTP introuvable", None
    
    # Check if already verified
    if otp.verified:
        return False, "Ce code a déjà été utilisé", otp
    
    # Check if expired
    if datetime.utcnow() > otp.expires_at:
        return False, "Code OTP expiré. Veuillez demander un nouveau code", otp
    
    # Check attempts
    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        return False, "Nombre maximum de tentatives atteint. Veuillez demander un nouveau code", otp
    
    # Increment attempts
    otp.attempts += 1
    db.commit()
    
    # Verify code
    if otp.code != code:
        db.commit()
        remaining = settings.OTP_MAX_ATTEMPTS - otp.attempts
        return False, f"Code incorrect. {remaining} tentative(s) restante(s)", otp
    
    # Mark as verified
    otp.verified = True
    db.commit()
    db.refresh(otp)
    
    return True, "", otp


def get_active_otp(db: Session, student_id: int) -> OTPCode:
    """
    Get the most recent active (unverified, non-expired) OTP for a student
    
    Args:
        db: Database session
        student_id: Student ID
        
    Returns:
        OTPCode: Active OTP or None
    """
    now = datetime.utcnow()
    
    return db.query(OTPCode).filter(
        OTPCode.student_id == student_id,
        OTPCode.verified == False,
        OTPCode.expires_at > now,
        OTPCode.attempts < settings.OTP_MAX_ATTEMPTS
    ).order_by(OTPCode.created_at.desc()).first()
