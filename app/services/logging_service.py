"""
Activity logging service for admin audit trail
"""
from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog
from typing import Optional
from datetime import datetime


async def log_activity(
    db: Session,
    student_id: Optional[int],
    action: str,
    contact_method: Optional[str] = None,
    contact_value: Optional[str] = None,
    sms_provider: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> ActivityLog:
    """
    Log an activity to the database for admin audit
    
    Args:
        db: Database session
        student_id: ID of the student (if applicable)
        action: Action performed (otp_requested, otp_verified, project_assigned, etc.)
        contact_method: Contact method used (email/sms)
        contact_value: Email or phone number
        sms_provider: SMS provider used (mtarget/twilio)
        ip_address: Client IP address
        user_agent: Client user agent
        success: Whether the action was successful
        error_message: Error message if action failed
        
    Returns:
        ActivityLog: Created log entry
    """
    log_entry = ActivityLog(
        student_id=student_id,
        action=action,
        contact_method=contact_method,
        contact_value=contact_value,
        sms_provider=sms_provider,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        error_message=error_message,
        created_at=datetime.utcnow()
    )
    
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    
    return log_entry


def get_recent_logs(db: Session, limit: int = 10) -> list[ActivityLog]:
    """
    Get recent activity logs
    
    Args:
        db: Database session
        limit: Number of logs to retrieve
        
    Returns:
        list[ActivityLog]: Recent activity logs
    """
    return db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit).all()


def get_logs_by_student(db: Session, student_id: int) -> list[ActivityLog]:
    """
    Get all logs for a specific student
    
    Args:
        db: Database session
        student_id: Student ID
        
    Returns:
        list[ActivityLog]: Activity logs for the student
    """
    return db.query(ActivityLog).filter(
        ActivityLog.student_id == student_id
    ).order_by(ActivityLog.created_at.desc()).all()
