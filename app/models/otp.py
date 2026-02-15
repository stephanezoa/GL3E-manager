"""
OTP Code model
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class OTPCode(Base):
    __tablename__ = "otp_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    code = Column(String(6), nullable=False)
    contact_method = Column(String(10), nullable=False)  # 'email' or 'sms'
    contact_value = Column(String, nullable=False)
    sms_provider = Column(String(20), nullable=True)  # 'mtarget' or 'twilio'
    expires_at = Column(DateTime, nullable=False)
    verified = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="otp_codes")
    
    def __repr__(self):
        return f"<OTPCode(id={self.id}, student_id={self.student_id}, method='{self.contact_method}')>"
