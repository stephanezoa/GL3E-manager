"""
Assignment model
"""
from sqlalchemy import Column, Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    verified = Column(Boolean, default=False)
    
    # Relationships
    student = relationship("Student", back_populates="assignments")
    project = relationship("Project", back_populates="assignments")
    
    def __repr__(self):
        return f"<Assignment(id={self.id}, student_id={self.student_id}, project_id={self.project_id})>"
