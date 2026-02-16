"""
Email service for sending OTP codes
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Dict
from app.config import settings
from app.logging_config import get_service_logger

logger = get_service_logger("email")


class EmailService:
    """Email service for sending OTP codes"""

    SMTP_TIMEOUT_SECONDS = 20
    
    async def send_otp_email(self, email: str, otp_code: str, student_name: str) -> Dict:
        """
        Send OTP code via email
        
        Args:
            email: Recipient email address
            otp_code: OTP code to send
            student_name: Student's name for personalization
            
        Returns:
            Dict: {"success": bool, "error": str}
        """
        masked_email = f"{email[:3]}***{email[email.find('@'):]}" if "@" in email else "***"
        logger.info(
            "email_send_attempt",
            extra={"channel": "email", "recipient": masked_email, "student_name": student_name},
        )
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"Code de vérification GL3E - {otp_code}"
            message["From"] = settings.SMTP_FROM
            message["To"] = email
            
            # Create HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f9f9f9;
                    }}
                    .header {{
                        background-color: #1e3a8a;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 5px 5px 0 0;
                    }}
                    .content {{
                        background-color: white;
                        padding: 30px;
                        border-radius: 0 0 5px 5px;
                    }}
                    .otp-code {{
                        font-size: 32px;
                        font-weight: bold;
                        color: #1e3a8a;
                        text-align: center;
                        padding: 20px;
                        background-color: #f3f4f6;
                        border-radius: 5px;
                        margin: 20px 0;
                        letter-spacing: 5px;
                    }}
                    .warning {{
                        color: #dc2626;
                        font-weight: bold;
                        margin-top: 20px;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 20px;
                        color: #666;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Institut Africain d'Informatique</h1>
                        <p>Attribution de Projets GL3E</p>
                    </div>
                    <div class="content">
                        <p>Bonjour <strong>{student_name}</strong>,</p>
                        
                        <p>Voici votre code de vérification pour l'attribution de votre projet :</p>
                        
                        <div class="otp-code">{otp_code}</div>
                        
                        <p>Ce code est valide pendant <strong>{settings.OTP_EXPIRY_MINUTES} minutes</strong>.</p>
                        
                        <p class="warning">⚠️ Ne partagez JAMAIS ce code avec qui que ce soit !</p>
                        
                        <p>Si vous n'avez pas demandé ce code, veuillez ignorer cet email.</p>
                        
                        <p>Cordialement,<br>
                        L'équipe GL3E</p>
                    </div>
                    <div class="footer">
                        <p>Institut Africain d'Informatique - GL3E</p>
                        <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version
            text_content = f"""
            Institut Africain d'Informatique
            Attribution de Projets GL3E
            
            Bonjour {student_name},
            
            Voici votre code de vérification pour l'attribution de votre projet :
            
            {otp_code}
            
            Ce code est valide pendant {settings.OTP_EXPIRY_MINUTES} minutes.
            
            ⚠️ Ne partagez JAMAIS ce code avec qui que ce soit !
            
            Si vous n'avez pas demandé ce code, veuillez ignorer cet email.
            
            Cordialement,
            L'équipe GL3E
            """
            
            # Attach parts
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            message.attach(part1)
            message.attach(part2)
            
            await self._send_message(message, masked_email, student_name)
            
            logger.info(
                "email_send_success",
                extra={"channel": "email", "recipient": masked_email, "student_name": student_name},
            )
            return {"success": True, "error": None}
            
        except Exception as e:
            error_msg = f"Email sending failed: {str(e)}"
            logger.error(
                "email_send_failed",
                extra={
                    "channel": "email",
                    "recipient": masked_email,
                    "student_name": student_name,
                    "error": error_msg,
                },
            )
            return {"success": False, "error": error_msg}

    async def send_theme_pdf_email(
        self,
        email: str,
        student_name: str,
        student_matricule: str,
        project_title: str,
        project_description: str,
        assigned_at: str,
        pdf_bytes: bytes,
    ) -> Dict:
        """Send student's assigned theme as PDF attachment."""
        masked_email = f"{email[:3]}***{email[email.find('@'):]}" if "@" in email else "***"
        logger.info(
            "theme_pdf_email_send_attempt",
            extra={
                "channel": "email",
                "recipient": masked_email,
                "student_name": student_name,
                "student_matricule": student_matricule,
            },
        )
        try:
            message = MIMEMultipart("mixed")
            message["Subject"] = "Votre thème GL3E (PDF)"
            message["From"] = settings.SMTP_FROM
            message["To"] = email

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"></head>
            <body style="font-family: Arial, sans-serif; color: #1f2937; line-height: 1.6;">
                <h2 style="color:#1e3a8a;">Attribution de projet GL3E</h2>
                <p>Bonjour <strong>{student_name}</strong>,</p>
                <p>Votre thème a été attribué avec succès. Le document PDF est joint à cet email.</p>
                <p><strong>Matricule:</strong> {student_matricule}<br/>
                <strong>Thème:</strong> {project_title}<br/>
                <strong>Date:</strong> {assigned_at}</p>
                <p>Cordialement,<br/>Équipe GL3E</p>
            </body>
            </html>
            """
            text_content = (
                "Attribution de projet GL3E\n\n"
                f"Bonjour {student_name},\n\n"
                "Votre thème a été attribué. Le document PDF est joint.\n\n"
                f"Matricule: {student_matricule}\n"
                f"Thème: {project_title}\n"
                f"Date: {assigned_at}\n"
            )

            alt = MIMEMultipart("alternative")
            alt.attach(MIMEText(text_content, "plain", "utf-8"))
            alt.attach(MIMEText(html_content, "html", "utf-8"))
            message.attach(alt)

            attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=f"theme_{student_matricule.replace(' ', '_')}.pdf",
            )
            message.attach(attachment)

            await self._send_message(message, masked_email, student_name)

            logger.info(
                "theme_pdf_email_send_success",
                extra={
                    "channel": "email",
                    "recipient": masked_email,
                    "student_name": student_name,
                    "student_matricule": student_matricule,
                },
            )
            return {"success": True, "error": None}
        except Exception as e:
            error_msg = f"Theme PDF email failed: {str(e)}"
            logger.error(
                "theme_pdf_email_send_failed",
                extra={
                    "channel": "email",
                    "recipient": masked_email,
                    "student_name": student_name,
                    "student_matricule": student_matricule,
                    "error": error_msg,
                },
            )
            return {"success": False, "error": error_msg}

    async def _send_message(self, message: MIMEMultipart, masked_email: str, student_name: str) -> None:
        """Shared SMTP send logic with retries across secure modes."""
        smtp_modes = self._build_smtp_modes()
        last_error = None

        for mode in smtp_modes:
            try:
                logger.info(
                    "email_smtp_attempt",
                    extra={
                        "channel": "email",
                        "recipient": masked_email,
                        "student_name": student_name,
                        "smtp_host": settings.SMTP_HOST,
                        "smtp_port": settings.SMTP_PORT,
                        "use_tls": mode["use_tls"],
                        "start_tls": mode["start_tls"],
                        "timeout": self.SMTP_TIMEOUT_SECONDS,
                    },
                )
                await aiosmtplib.send(
                    message,
                    hostname=settings.SMTP_HOST,
                    port=settings.SMTP_PORT,
                    username=settings.SMTP_USER,
                    password=settings.SMTP_PASSWORD,
                    sender=settings.SMTP_USER,
                    use_tls=mode["use_tls"],
                    start_tls=mode["start_tls"],
                    timeout=self.SMTP_TIMEOUT_SECONDS,
                )
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "email_smtp_attempt_failed",
                    extra={
                        "channel": "email",
                        "recipient": masked_email,
                        "student_name": student_name,
                        "smtp_host": settings.SMTP_HOST,
                        "smtp_port": settings.SMTP_PORT,
                        "use_tls": mode["use_tls"],
                        "start_tls": mode["start_tls"],
                        "error": f"{type(exc).__name__}: {exc}",
                    },
                )

        if last_error is not None:
            raise last_error

    def _build_smtp_modes(self) -> list[dict]:
        """
        Build SMTP strategy list.
        - 465 should use implicit TLS.
        - 587/25 usually use STARTTLS.
        """
        modes: list[dict] = []

        def push(use_tls: bool, start_tls):
            mode = {"use_tls": use_tls, "start_tls": start_tls}
            if mode not in modes:
                modes.append(mode)

        # 1) Force secure mode for SMTPS
        if settings.SMTP_PORT == 465:
            push(True, False)   # SMTPS implicit TLS only
            return modes

        # 2) Primary mode from config for other ports
        push(bool(settings.SMTP_USE_TLS), None)

        # 3) Common recovery paths
        if settings.SMTP_PORT in (587, 25):
            push(False, True)   # STARTTLS
            push(True, False)   # fallback implicit TLS (non-standard)
        else:
            push(False, True)
            push(True, False)

        return modes


# Global email service instance
email_service = EmailService()
