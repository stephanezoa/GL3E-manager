"""
Database models package
"""
from app.models.student import Student
from app.models.project import Project
from app.models.assignment import Assignment
from app.models.otp import OTPCode
from app.models.activity_log import ActivityLog
from app.models.admin import AdminUser

__all__ = [
    "Student",
    "Project",
    "Assignment",
    "OTPCode",
    "ActivityLog",
    "AdminUser",
]
