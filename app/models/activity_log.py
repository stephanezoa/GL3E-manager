"""
Activity Log model for admin audit trail
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    action = Column(String(50), nullable=False, index=True)  # otp_requested, otp_verified, project_assigned, etc.
    contact_method = Column(String(10), nullable=True)  # 'email' or 'sms'
    contact_value = Column(String, nullable=True)
    sms_provider = Column(String(20), nullable=True)  # 'mtarget' or 'twilio'
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    student = relationship("Student", back_populates="activity_logs")
    
    def __repr__(self):
        return f"<ActivityLog(id={self.id}, action='{self.action}', success={self.success})>"
