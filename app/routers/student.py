"""
Student router - handles student-facing endpoints
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Student, Project, Assignment
from app.services.otp_service import create_otp, verify_otp, get_active_otp
from app.services.email_service import email_service
from app.services.sms_service import sms_service
from app.services.assignment_service import assign_project_to_student, get_all_assignments
from app.services.logging_service import log_activity
from app.utils.validators import validate_email, sanitize_input
from app.utils.phone_validator import validate_and_normalize_phone
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


class OTPRequest(BaseModel):
    student_name: str
    contact_type: str  # 'email' or 'sms'
    contact_value: str


class OTPVerification(BaseModel):
    otp_id: int
    code: str


@router.get("/api/students")
async def get_students_list(db: Session = Depends(get_db)):
    """Get list of all students for dropdown"""
    students = db.query(Student).order_by(Student.full_name).all()
    return [{"id": s.id, "name": s.full_name, "matricule": s.matricule} for s in students]


@router.post("/api/request-project")
async def request_project(
    request: Request,
    otp_request: OTPRequest,
    db: Session = Depends(get_db)
):
    """Request a project - sends OTP"""
    try:
        # Sanitize inputs
        student_name = sanitize_input(otp_request.student_name)
        contact_value = sanitize_input(otp_request.contact_value)
        
        # Find student
        student = db.query(Student).filter(Student.full_name == student_name).first()
        if not student:
            raise HTTPException(status_code=404, detail="Étudiant introuvable")
        
        # Check if student already has a project
        if student.has_project:
            await log_activity(
                db, student.id, "otp_request_blocked",
                otp_request.contact_type, contact_value,
                ip_address=request.client.host,
                success=False,
                error_message="Student already has a project"
            )
            raise HTTPException(
                status_code=400,
                detail="Vous avez déjà un projet attribué. Contactez l'administration si nécessaire."
            )
        
        # Validate contact method
        if otp_request.contact_type == "email":
            is_valid, error_msg = validate_email(contact_value)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
        elif otp_request.contact_type == "sms":
            is_valid, normalized_phone, error_msg = validate_and_normalize_phone(contact_value)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
            contact_value = normalized_phone
        else:
            raise HTTPException(status_code=400, detail="Méthode de contact invalide")
        
        # Create OTP
        otp = await create_otp(db, student.id, otp_request.contact_type, contact_value)
        
        # Send OTP
        sms_provider = None
        if otp_request.contact_type == "email":
            result = await email_service.send_otp_email(contact_value, otp.code, student.full_name)
            if not result["success"]:
                await log_activity(
                    db, student.id, "otp_send_failed",
                    "email", contact_value,
                    ip_address=request.client.host,
                    success=False,
                    error_message=result["error"]
                )
                raise HTTPException(status_code=500, detail="Échec d'envoi de l'email. Réessayez.")
        else:  # SMS
            result = await sms_service.send_otp_sms(contact_value, otp.code)
            if not result["success"]:
                await log_activity(
                    db, student.id, "otp_send_failed",
                    "sms", contact_value,
                    ip_address=request.client.host,
                    success=False,
                    error_message=result["error"]
                )
                raise HTTPException(status_code=500, detail=result["error"])
            sms_provider = result["provider"]
        
        # Update OTP with SMS provider
        if sms_provider:
            otp.sms_provider = sms_provider
            db.commit()
        
        # Log success
        await log_activity(
            db, student.id, "otp_requested",
            otp_request.contact_type, contact_value,
            sms_provider=sms_provider,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            success=True
        )
        
        return {
            "success": True,
            "message": f"Code OTP envoyé à {contact_value}",
            "otp_id": otp.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in request_project: {e}")
        raise HTTPException(status_code=500, detail="Une erreur est survenue")


@router.post("/api/verify-otp")
async def verify_otp_endpoint(
    request: Request,
    verification: OTPVerification,
    db: Session = Depends(get_db)
):
    """Verify OTP and assign project"""
    try:
        # Verify OTP
        is_valid, error_msg, otp = await verify_otp(db, verification.otp_id, verification.code)
        
        if not is_valid:
            if otp:
                await log_activity(
                    db, otp.student_id, "otp_verification_failed",
                    otp.contact_method, otp.contact_value,
                    sms_provider=otp.sms_provider,
                    ip_address=request.client.host,
                    success=False,
                    error_message=error_msg
                )
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Assign project
        success, assign_error, project = await assign_project_to_student(db, otp.student_id)
        
        if not success:
            await log_activity(
                db, otp.student_id, "project_assignment_failed",
                otp.contact_method, otp.contact_value,
                sms_provider=otp.sms_provider,
                ip_address=request.client.host,
                success=False,
                error_message=assign_error
            )
            raise HTTPException(status_code=400, detail=assign_error)
        
        # Log success
        await log_activity(
            db, otp.student_id, "project_assigned",
            otp.contact_method, otp.contact_value,
            sms_provider=otp.sms_provider,
            ip_address=request.client.host,
            success=True
        )
        
        return {
            "success": True,
            "project": {
                "id": project.id,
                "title": project.title,
                "description": project.description
            },
            "student": {
                "name": otp.student.full_name,
                "matricule": otp.student.matricule
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in verify_otp: {e}")
        raise HTTPException(status_code=500, detail="Une erreur est survenue")


@router.get("/projets-attribues", response_class=HTMLResponse)
async def projets_attribues_page(request: Request, db: Session = Depends(get_db)):
    """Public page showing all assigned projects"""
    assignments = get_all_assignments(db)
    return templates.TemplateResponse(
        "public/projets_attribues.html",
        {"request": request, "assignments": assignments}
    )


@router.get("/api/projets-attribues")
async def get_projets_attribues(search: Optional[str] = None, db: Session = Depends(get_db)):
    """API endpoint for assigned projects"""
    assignments = get_all_assignments(db, search)
    return {"assignments": assignments}
