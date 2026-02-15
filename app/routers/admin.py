"""
Admin router - handles admin dashboard and management
"""
from fastapi import APIRouter, Depends, Request, HTTPException, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Student, AdminUser
from app.services.assignment_service import get_assignment_stats, get_all_assignments
from app.services.logging_service import get_recent_logs, get_logs_by_student
from app.utils.security import verify_password, create_access_token, decode_access_token
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


class LoginRequest(BaseModel):
    username: str
    password: str


def get_current_admin(request: Request, db: Session = Depends(get_db)) -> AdminUser:
    """Dependency to get current admin from token"""
    token = request.cookies.get("admin_token")
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide")
    
    username = payload.get("sub")
    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Administrateur introuvable")
    
    return admin


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login page"""
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.post("/api/login")
async def admin_login(login_req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Admin login endpoint"""
    admin = db.query(AdminUser).filter(AdminUser.username == login_req.username).first()
    
    if not admin or not verify_password(login_req.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    
    # Create access token
    token = create_access_token({"sub": admin.username})
    
    # Set cookie
    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        max_age=86400,  # 24 hours
        samesite="lax"
    )
    
    return {"success": True, "message": "Connexion réussie"}


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin dashboard page"""
    stats = get_assignment_stats(db)
    assignments = get_all_assignments(db)
    recent_logs = get_recent_logs(db, limit=10)
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "admin": admin,
            "stats": stats,
            "assignments": assignments,
            "recent_logs": recent_logs
        }
    )


@router.get("/api/stats")
async def get_stats(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get assignment statistics"""
    return get_assignment_stats(db)


@router.get("/api/assignments")
async def get_assignments(
    search: Optional[str] = None,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all assignments with optional search"""
    assignments = get_all_assignments(db, search)
    return {"assignments": assignments}


@router.get("/api/logs")
async def get_logs(
    limit: int = 50,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get activity logs"""
    logs = get_recent_logs(db, limit)
    return {
        "logs": [
            {
                "id": log.id,
                "student_name": log.student.full_name if log.student else "N/A",
                "action": log.action,
                "contact_method": log.contact_method,
                "contact_value": log.contact_value,
                "sms_provider": log.sms_provider,
                "success": log.success,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    }


@router.get("/api/search")
async def search_students(
    q: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Search students by name"""
    students = db.query(Student).filter(
        Student.full_name.ilike(f"%{q}%")
    ).limit(20).all()
    
    return {
        "students": [
            {
                "id": s.id,
                "name": s.full_name,
                "matricule": s.matricule,
                "has_project": s.has_project
            }
            for s in students
        ]
    }


@router.post("/api/logout")
async def admin_logout(response: Response):
    """Admin logout"""
    response.delete_cookie("admin_token")
    return {"success": True, "message": "Déconnexion réussie"}
