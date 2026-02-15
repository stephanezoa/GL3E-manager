"""
Admin User model
"""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base


class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AdminUser(id={self.id}, username='{self.username}')>"
