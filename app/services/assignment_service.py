"""
Project assignment service
"""
import random
from sqlalchemy.orm import Session
from app.models.student import Student
from app.models.project import Project
from app.models.assignment import Assignment
from datetime import datetime
from typing import Optional


async def assign_project_to_student(db: Session, student_id: int) -> tuple[bool, str, Optional[Project]]:
    """
    Assign a random project to a student
    
    Logic:
    1. Get projects with assigned_count = 0 (not yet assigned)
    2. If none, get projects with assigned_count = 1 (assigned once)
    3. Randomly select one
    4. Create assignment
    5. Update project assigned_count
    6. Mark student has_project = True
    
    Args:
        db: Database session
        student_id: Student ID
        
    Returns:
        tuple[bool, str, Optional[Project]]: (success, error_message, assigned_project)
    """
    # Check if student already has a project
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return False, "Étudiant introuvable", None
    
    if student.has_project:
        return False, "Vous avez déjà un projet attribué", None
    
    # Get available projects (not assigned yet)
    available_projects = db.query(Project).filter(Project.assigned_count == 0).all()
    
    # If no unassigned projects, get projects assigned only once
    if not available_projects:
        available_projects = db.query(Project).filter(Project.assigned_count == 1).all()
    
    # If still no projects (all assigned twice), return error
    if not available_projects:
        return False, "Tous les projets ont été attribués", None
    
    # Randomly select a project
    selected_project = random.choice(available_projects)
    
    # Create assignment
    assignment = Assignment(
        student_id=student_id,
        project_id=selected_project.id,
        assigned_at=datetime.utcnow(),
        verified=True
    )
    
    db.add(assignment)
    
    # Update project assigned count
    selected_project.assigned_count += 1
    
    # Mark student as having a project
    student.has_project = True
    
    # Commit changes
    db.commit()
    db.refresh(selected_project)
    
    return True, "", selected_project


def get_assignment_stats(db: Session) -> dict:
    """
    Get assignment statistics
    
    Returns:
        dict: Statistics about assignments
    """
    total_students = db.query(Student).count()
    students_with_projects = db.query(Student).filter(Student.has_project == True).count()
    total_projects = db.query(Project).count()
    projects_assigned_once = db.query(Project).filter(Project.assigned_count == 1).count()
    projects_assigned_twice = db.query(Project).filter(Project.assigned_count >= 2).count()
    projects_not_assigned = db.query(Project).filter(Project.assigned_count == 0).count()
    
    return {
        "total_students": total_students,
        "students_with_projects": students_with_projects,
        "students_without_projects": total_students - students_with_projects,
        "total_projects": total_projects,
        "projects_not_assigned": projects_not_assigned,
        "projects_assigned_once": projects_assigned_once,
        "projects_assigned_twice": projects_assigned_twice
    }


def get_all_assignments(db: Session, search: str = None):
    """
    Get all assignments with student and project details
    
    Args:
        db: Database session
        search: Optional search term for student name
        
    Returns:
        list: List of assignments with details
    """
    query = db.query(Assignment).join(Student).join(Project)
    
    if search:
        query = query.filter(Student.full_name.ilike(f"%{search}%"))
    
    assignments = query.order_by(Assignment.assigned_at.desc()).all()
    
    return [
        {
            "id": a.id,
            "student_name": a.student.full_name,
            "student_matricule": a.student.matricule,
            "project_title": a.project.title,
            "assigned_at": a.assigned_at.isoformat(),
        }
        for a in assignments
    ]
