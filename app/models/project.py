"""
Project model
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    features = Column(Text, nullable=True)  # JSON string
    assigned_count = Column(Integer, default=0)
    max_assignments = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    assignments = relationship("Assignment", back_populates="project")
    
    def __repr__(self):
        return f"<Project(id={self.id}, title='{self.title}', assigned={self.assigned_count})>"
