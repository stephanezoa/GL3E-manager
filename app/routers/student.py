"""
Student router - handles student-facing endpoints
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Student, Project, Assignment, OTPCode
from app.services.otp_service import create_otp, verify_otp, get_active_otp
from app.services.email_service import email_service
from app.services.sms_service import sms_service
from app.services.assignment_service import (
    assign_project_to_student,
    get_all_assignments,
    get_latest_assignment_for_student,
)
from app.services.pdf_service import generate_student_theme_pdf
from app.services.logging_service import log_activity
from app.config import settings
from app.utils.validators import (
    validate_email,
    sanitize_input,
    validate_student_name,
    has_disallowed_input,
)
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


class ThemePDFExportRequest(BaseModel):
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
        student_name = sanitize_input(otp_request.student_name, max_length=120)
        contact_value = sanitize_input(otp_request.contact_value, max_length=255)
        contact_type = (otp_request.contact_type or "").strip().lower()

        if has_disallowed_input(student_name) or has_disallowed_input(contact_value):
            raise HTTPException(status_code=400, detail="Entrée invalide détectée")

        is_valid_name, name_err = validate_student_name(student_name)
        if not is_valid_name:
            raise HTTPException(status_code=400, detail=name_err)
        
        # Find student
        student = db.query(Student).filter(Student.full_name == student_name).first()
        if not student:
            raise HTTPException(status_code=404, detail="Étudiant introuvable")
        
        # Check if student already has a project
        if student.has_project:
            await log_activity(
                db, student.id, "otp_request_blocked",
                contact_type, contact_value,
                ip_address=request.client.host,
                success=False,
                error_message="Student already has a project"
            )
            raise HTTPException(
                status_code=400,
                detail="Vous avez déjà un projet attribué. Contactez l'administration si nécessaire."
            )
        
        # Validate contact method
        if contact_type == "email":
            is_valid, error_msg = validate_email(contact_value)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
            contact_value = contact_value.strip().lower()
            if len(contact_value) > 254:
                raise HTTPException(status_code=400, detail="Email trop long")
        elif contact_type == "sms":
            is_valid, normalized_phone, error_msg = validate_and_normalize_phone(contact_value)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
            contact_value = normalized_phone
        else:
            raise HTTPException(status_code=400, detail="Méthode de contact invalide")

        # Limit abuse by contact method/value (email/phone)
        request_count = (
            db.query(OTPCode)
            .filter(
                OTPCode.contact_method == contact_type,
                OTPCode.contact_value == contact_value,
            )
            .count()
        )
        if request_count >= settings.OTP_CONTACT_MAX_REQUESTS:
            detail_msg = (
                f"Limite atteinte: ce {contact_type} a déjà demandé un thème "
                f"{request_count} fois (maximum {settings.OTP_CONTACT_MAX_REQUESTS}). "
                "Contactez l'administration."
            )
            await log_activity(
                db, student.id, "otp_request_limit_reached",
                contact_type, contact_value,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                success=False,
                error_message=detail_msg
            )
            raise HTTPException(status_code=429, detail=detail_msg)
        
        # Create OTP
        otp = await create_otp(db, student.id, contact_type, contact_value)
        
        # Send OTP
        sms_provider = None
        if contact_type == "email":
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
            contact_type, contact_value,
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
        if verification.otp_id <= 0:
            raise HTTPException(status_code=400, detail="Référence OTP invalide")
        if not verification.code or not verification.code.isdigit() or len(verification.code) != 6:
            raise HTTPException(status_code=400, detail="Code OTP invalide")

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

        assignment = get_latest_assignment_for_student(db, otp.student_id)

        # If OTP channel is email, automatically send assignment PDF by email
        pdf_email_sent = False
        pdf_email_error = None
        if otp.contact_method == "email" and assignment:
            try:
                pdf_buffer = generate_student_theme_pdf(
                    student_name=assignment["student_name"],
                    student_matricule=assignment["student_matricule"],
                    project_title=assignment["project_title"],
                    project_description=assignment.get("project_description") or "",
                    assigned_at=assignment["assigned_at"],
                    signature_name="Stephane Zoa",
                )
                email_result = await email_service.send_theme_pdf_email(
                    email=otp.contact_value,
                    student_name=assignment["student_name"],
                    student_matricule=assignment["student_matricule"],
                    project_title=assignment["project_title"],
                    project_description=assignment.get("project_description") or "",
                    assigned_at=assignment["assigned_at"],
                    pdf_bytes=pdf_buffer.getvalue(),
                )
                pdf_email_sent = bool(email_result.get("success"))
                pdf_email_error = email_result.get("error")
            except Exception as e:
                pdf_email_error = str(e)
                pdf_email_sent = False

            await log_activity(
                db, otp.student_id, "project_pdf_email_sent" if pdf_email_sent else "project_pdf_email_failed",
                otp.contact_method, otp.contact_value,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                success=pdf_email_sent,
                error_message=pdf_email_error if not pdf_email_sent else None
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
            },
            "assignment": assignment,
            "project_pdf_email_sent": pdf_email_sent,
            "project_pdf_email_error": pdf_email_error,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in verify_otp: {e}")
        raise HTTPException(status_code=500, detail="Une erreur est survenue")


@router.post("/api/export-my-theme-pdf")
async def export_my_theme_pdf(payload: ThemePDFExportRequest, db: Session = Depends(get_db)):
    """Export student assignment details as a personalized PDF."""
    if payload.otp_id <= 0:
        raise HTTPException(status_code=400, detail="Référence OTP invalide")
    if not payload.code or not payload.code.isdigit() or len(payload.code) != 6:
        raise HTTPException(status_code=400, detail="Code OTP invalide")

    otp = db.query(OTPCode).filter(OTPCode.id == payload.otp_id).first()
    if not otp:
        raise HTTPException(status_code=404, detail="Référence OTP introuvable")
    if not otp.verified:
        raise HTTPException(status_code=403, detail="OTP non vérifié")
    if otp.code != payload.code:
        raise HTTPException(status_code=403, detail="Code OTP invalide pour l'export")

    assignment = get_latest_assignment_for_student(db, otp.student_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Aucun thème attribué pour cet étudiant")

    pdf_buffer = generate_student_theme_pdf(
        student_name=assignment["student_name"],
        student_matricule=assignment["student_matricule"],
        project_title=assignment["project_title"],
        project_description=assignment.get("project_description") or "",
        assigned_at=assignment["assigned_at"],
        signature_name="Stephane Zoa",
    )

    filename = f"theme_{assignment['student_matricule']}.pdf".replace(" ", "_")
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'},
    )


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
