"""
Email service for sending OTP codes
"""
import aiosmtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending OTP codes"""
    
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
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_TLS
            )
            
            logger.info(f"OTP email sent successfully to {email}")
            return {"success": True, "error": None}
            
        except Exception as e:
            error_msg = f"Email sending failed: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}


# Global email service instance
email_service = EmailService()
