"""
Student model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False, index=True)
    matricule = Column(String, unique=True, index=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    has_project = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    assignments = relationship("Assignment", back_populates="student")
    otp_codes = relationship("OTPCode", back_populates="student")
    activity_logs = relationship("ActivityLog", back_populates="student")
    
    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.full_name}', matricule='{self.matricule}')>"
