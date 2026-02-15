"""
SMS service with mTarget (primary) and Twilio (fallback)
"""
import httpx
import logging
from twilio.rest import Client
from typing import Dict, Optional
from app.config import settings
from app.utils.phone_validator import normalize_cameroon_phone

logger = logging.getLogger(__name__)


class SMSService:
    """SMS service with automatic fallback between providers"""
    
    def __init__(self):
        # Initialize Twilio client
        self.twilio_client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
    
    async def send_via_mtarget(self, phone: str, message: str) -> Dict:
        """
        Send SMS via mTarget API
        
        Args:
            phone: Phone number (normalized)
            message: Message content
            
        Returns:
            Dict: {"success": bool, "provider": str, "error": str}
        """
        try:
            # Prepare request data
            data = {
                "username": settings.MTARGET_USERNAME,
                "password": settings.MTARGET_PASSWORD,
                "msisdn": phone.replace("+", ""),  # mTarget expects without +
                "msg": message,
                "service_id": settings.MTARGET_SERVICE_ID,
                "sender": settings.MTARGET_SENDER
            }
            
            # Send request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    settings.MTARGET_API_URL,
                    data=data
                )
                
                if response.status_code == 200:
                    logger.info(f"SMS sent successfully via mTarget to {phone[:8]}***")
                    return {"success": True, "provider": "mtarget", "error": None}
                else:
                    error_msg = f"mTarget API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return {"success": False, "provider": "mtarget", "error": error_msg}
                    
        except Exception as e:
            error_msg = f"mTarget exception: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "provider": "mtarget", "error": error_msg}
    
    async def send_via_twilio(self, phone: str, message: str) -> Dict:
        """
        Send SMS via Twilio API
        
        Args:
            phone: Phone number (normalized with +)
            message: Message content
            
        Returns:
            Dict: {"success": bool, "provider": str, "error": str}
        """
        try:
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone
            )
            
            logger.info(f"SMS sent successfully via Twilio to {phone[:8]}*** (SID: {message_obj.sid})")
            return {"success": True, "provider": "twilio", "error": None, "sid": message_obj.sid}
            
        except Exception as e:
            error_msg = f"Twilio exception: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "provider": "twilio", "error": error_msg}
    
    async def send_otp_sms(self, phone: str, otp_code: str) -> Dict:
        """
        Send OTP SMS with automatic fallback
        
        Args:
            phone: Phone number (will be normalized)
            otp_code: OTP code to send
            
        Returns:
            Dict: {"success": bool, "provider": str, "error": str}
        """
        # Normalize phone number
        try:
            normalized_phone = normalize_cameroon_phone(phone)
        except ValueError as e:
            return {"success": False, "provider": None, "error": str(e)}
        
        # Prepare message
        message = f"Votre code OTP GL3E: {otp_code}\n\nValide pendant {settings.OTP_EXPIRY_MINUTES} minutes.\nNe partagez JAMAIS ce code!"
        
        # Try mTarget first
        logger.info(f"Attempting to send OTP via mTarget to {normalized_phone[:8]}***")
        result = await self.send_via_mtarget(normalized_phone, message)
        
        if result["success"]:
            return result
        
        # Fallback to Twilio
        logger.warning(f"mTarget failed, falling back to Twilio for {normalized_phone[:8]}***")
        result = await self.send_via_twilio(normalized_phone, message)
        
        if result["success"]:
            return result
        
        # Both failed
        logger.error(f"Both SMS providers failed for {normalized_phone[:8]}***")
        return {
            "success": False,
            "provider": None,
            "error": "Échec d'envoi SMS. Veuillez réessayer ou utiliser l'email."
        }


# Global SMS service instance
sms_service = SMSService()
