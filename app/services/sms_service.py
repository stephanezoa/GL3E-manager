"""
Advanced SMS service with mTarget primary provider and Twilio fallback.
"""
from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Optional

import httpx
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.config import settings
from app.logging_config import get_service_logger
from app.utils.phone_validator import normalize_cameroon_phone

# Defaults
DEFAULT_MAX_RETRIES = 1
DEFAULT_RETRY_DELAY_SECONDS = 2.0
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_CIRCUIT_THRESHOLD = 5
DEFAULT_CIRCUIT_TIMEOUT_SECONDS = 60.0
DEFAULT_TWILIO_TIMEOUT_SECONDS = 20.0
DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60.0

logger = get_service_logger("sms")


@dataclass
class SMSServiceConfig:
    """Runtime SMS service configuration."""

    # Provider credentials from .env / settings
    mtarget_username: str
    mtarget_password: str
    mtarget_service_id: str
    mtarget_sender: str
    mtarget_url: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str

    # Retry / timeout / resilience
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    twilio_timeout_seconds: float = DEFAULT_TWILIO_TIMEOUT_SECONDS
    circuit_threshold: int = DEFAULT_CIRCUIT_THRESHOLD
    circuit_timeout_seconds: float = DEFAULT_CIRCUIT_TIMEOUT_SECONDS
    rate_limit_requests: int = DEFAULT_RATE_LIMIT_REQUESTS
    rate_limit_window_seconds: float = DEFAULT_RATE_LIMIT_WINDOW_SECONDS


class CircuitBreaker:
    """Simple circuit breaker for provider calls."""

    def __init__(self, threshold: int, timeout_seconds: float) -> None:
        self._threshold = threshold
        self._timeout_seconds = timeout_seconds
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._state = "closed"  # closed | open | half-open
        self._lock = Lock()

    def can_attempt(self) -> bool:
        with self._lock:
            if self._state == "closed":
                return True
            if self._state == "open":
                if (time.monotonic() - self._last_failure_time) > self._timeout_seconds:
                    self._state = "half-open"
                    return True
                return False
            return True  # half-open

    def record_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            if self._state == "half-open":
                self._state = "closed"

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._failure_count >= self._threshold:
                self._state = "open"

    def state(self) -> str:
        with self._lock:
            return self._state


class RateLimiter:
    """In-memory sliding-window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._timestamps: list[float] = []
        self._lock = Lock()

    def allow(self) -> bool:
        now = time.monotonic()
        cutoff = now - self._window_seconds
        with self._lock:
            self._timestamps = [ts for ts in self._timestamps if ts > cutoff]
            if len(self._timestamps) >= self._max_requests:
                return False
            self._timestamps.append(now)
            return True


class SMSMetrics:
    """Simple in-memory metrics snapshot."""

    def __init__(self) -> None:
        self._lock = Lock()
        self.total_sent = 0
        self.total_failed = 0
        self.total_retries = 0
        self.sent_by_provider: dict[str, int] = {}
        self.failed_by_provider: dict[str, int] = {}
        self.avg_duration_ms = 0.0

    def record_success(self, provider: str, duration_ms: float) -> None:
        with self._lock:
            self.total_sent += 1
            self.sent_by_provider[provider] = self.sent_by_provider.get(provider, 0) + 1
            if self.avg_duration_ms == 0:
                self.avg_duration_ms = duration_ms
            else:
                self.avg_duration_ms = (self.avg_duration_ms * 0.9) + (duration_ms * 0.1)

    def record_failure(self, provider: str) -> None:
        with self._lock:
            self.total_failed += 1
            self.failed_by_provider[provider] = self.failed_by_provider.get(provider, 0) + 1

    def record_retry(self) -> None:
        with self._lock:
            self.total_retries += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            total = self.total_sent + self.total_failed
            success_rate = (self.total_sent / total * 100.0) if total > 0 else 0.0
            return {
                "total_sent": self.total_sent,
                "total_failed": self.total_failed,
                "total_retries": self.total_retries,
                "success_rate_percent": round(success_rate, 2),
                "average_duration_ms": round(self.avg_duration_ms, 2),
                "sent_by_provider": dict(self.sent_by_provider),
                "failed_by_provider": dict(self.failed_by_provider),
            }


class SMSService:
    """SMS service with mTarget-first strategy and Twilio fallback."""

    def __init__(self) -> None:
        mtarget_url = self._normalize_mtarget_url(settings.MTARGET_API_URL)
        self.config = SMSServiceConfig(
            mtarget_username=settings.MTARGET_USERNAME,
            mtarget_password=settings.MTARGET_PASSWORD,
            mtarget_service_id=settings.MTARGET_SERVICE_ID,
            mtarget_sender=settings.MTARGET_SENDER,
            mtarget_url=mtarget_url,
            twilio_account_sid=settings.TWILIO_ACCOUNT_SID,
            twilio_auth_token=settings.TWILIO_AUTH_TOKEN,
            twilio_phone_number=settings.TWILIO_PHONE_NUMBER,
        )

        self.mtarget_circuit = CircuitBreaker(
            threshold=self.config.circuit_threshold,
            timeout_seconds=self.config.circuit_timeout_seconds,
        )
        self.twilio_circuit = CircuitBreaker(
            threshold=self.config.circuit_threshold,
            timeout_seconds=self.config.circuit_timeout_seconds,
        )
        self.rate_limiter = RateLimiter(
            max_requests=self.config.rate_limit_requests,
            window_seconds=self.config.rate_limit_window_seconds,
        )
        self.metrics = SMSMetrics()

        self.twilio_client: Optional[Client] = None
        if self.config.twilio_account_sid and self.config.twilio_auth_token:
            self.twilio_client = Client(
                self.config.twilio_account_sid,
                self.config.twilio_auth_token,
            )

        logger.info(
            "sms_service_initialized",
            extra={
                "channel": "sms",
                "mtarget_configured": bool(
                    self.config.mtarget_username and self.config.mtarget_password
                ),
                "twilio_configured": bool(self.twilio_client),
                "max_retries": self.config.max_retries,
                "timeout_seconds": self.config.timeout_seconds,
                "circuit_threshold": self.config.circuit_threshold,
                "mtarget_url": self.config.mtarget_url,
                "mtarget_sender": self.config.mtarget_sender,
            },
        )

    @staticmethod
    def _mask_phone(phone: str) -> str:
        return f"{phone[:8]}***" if phone else "***"

    @staticmethod
    def _is_valid_e164(phone_number: str) -> bool:
        clean = (phone_number or "").strip()
        if not clean.startswith("+"):
            return False
        if not re.fullmatch(r"\+\d{10,15}", clean):
            return False
        return True

    @staticmethod
    def _is_cameroon_number(phone_number: str) -> bool:
        clean = (phone_number or "").strip().replace(" ", "").replace("-", "")
        return (
            clean.startswith("+237")
            or clean.startswith("00237")
            or clean.startswith("237")
            or (clean.startswith("6") and len(clean) == 9)
        )

    def _normalize_phone_for_mtarget(self, phone_number: str) -> str:
        """
        Normalize to mTarget expected format: 00237XXXXXXXXX.
        """
        clean = (phone_number or "").strip().replace(" ", "").replace("-", "")
        if clean.startswith("+"):
            clean = clean[1:]
        if clean.startswith("00237"):
            return clean
        if clean.startswith("237"):
            return f"00{clean}"
        if clean.startswith("6") and len(clean) == 9:
            return f"00237{clean}"
        # fallback keeps numeric chars only; provider will reject if invalid
        return re.sub(r"\D", "", clean)

    def _normalize_phone_for_twilio(self, phone_number: str) -> str:
        """
        Normalize to E.164 for Twilio.
        """
        clean = (phone_number or "").strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if clean.startswith("00"):
            clean = f"+{clean[2:]}"
        elif clean.startswith("237") and len(clean) == 12:
            clean = f"+{clean}"
        elif clean.startswith("6") and len(clean) == 9:
            clean = f"+237{clean}"
        elif clean.startswith("+"):
            pass
        else:
            raise ValueError("Format de numero invalide pour Twilio (E.164 requis)")

        if not self._is_valid_e164(clean):
            raise ValueError("Numero invalide: format E.164 attendu (ex: +33659029118)")
        return clean

    @staticmethod
    def _normalize_mtarget_url(url: str) -> str:
        """
        Normalize legacy mTarget endpoint to current public endpoint.
        """
        cleaned = (url or "").strip()
        if cleaned.endswith("/send") or "api.mtarget.fr/send" in cleaned:
            return "https://api-public-2.mtarget.fr/messages"
        if not cleaned:
            return "https://api-public-2.mtarget.fr/messages"
        return cleaned

    async def _send_via_mtarget_once(self, phone: str, message: str) -> dict[str, Any]:
        sender = (self.config.mtarget_sender or "FM OTP").strip()
        normalized_phone = self._normalize_phone_for_mtarget(phone)
        payload = {
            "username": self.config.mtarget_username,
            "password": self.config.mtarget_password,
            "msisdn": normalized_phone,
            "msg": message,
            "service_id": self.config.mtarget_service_id,
            "sender": sender,
        }

        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(
                    self.config.mtarget_url,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
            err = f"mTarget exception {type(exc).__name__}: {repr(exc)}"
            return {
                "success": False,
                "provider": "mtarget",
                "error": err,
                "duration_ms": duration_ms,
                "normalized_phone": normalized_phone,
            }
        duration_ms = round((time.perf_counter() - start) * 1000.0, 2)

        if response.status_code == 200:
            response_text = (response.text or "").strip()
            # mTarget can return HTTP 200 with business error in body.
            if "error" in response_text.lower() or "ko" in response_text.lower():
                return {
                    "success": False,
                    "provider": "mtarget",
                    "error": f"mTarget business error: {response_text[:250]}",
                    "duration_ms": duration_ms,
                }
            return {
                "success": True,
                "provider": "mtarget",
                "error": None,
                "duration_ms": duration_ms,
                "sender": sender,
                "response_preview": response_text[:250],
                "normalized_phone": normalized_phone,
            }
        return {
            "success": False,
            "provider": "mtarget",
            "error": f"mTarget API error: {response.status_code} - {(response.text or '')[:250]}",
            "duration_ms": duration_ms,
            "normalized_phone": normalized_phone,
        }

    async def _send_via_twilio_once(self, phone: str, message: str) -> dict[str, Any]:
        if not self.twilio_client:
            return {
                "success": False,
                "provider": "twilio",
                "error": "Twilio non configuré",
                "duration_ms": 0.0,
            }

        try:
            twilio_phone = self._normalize_phone_for_twilio(phone)
        except ValueError as exc:
            return {
                "success": False,
                "provider": "twilio",
                "error": str(exc),
                "duration_ms": 0.0,
            }

        start = time.perf_counter()
        try:
            message_obj = await asyncio.wait_for(
                asyncio.to_thread(
                    self.twilio_client.messages.create,
                    body=message,
                    from_=self.config.twilio_phone_number,
                    to=twilio_phone,
                ),
                timeout=self.config.twilio_timeout_seconds,
            )
        except asyncio.TimeoutError:
            duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
            return {
                "success": False,
                "provider": "twilio",
                "error": f"Twilio timeout after {self.config.twilio_timeout_seconds:.0f}s",
                "duration_ms": duration_ms,
                "normalized_phone": twilio_phone,
            }
        except TwilioRestException as exc:
            duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
            return {
                "success": False,
                "provider": "twilio",
                "error": f"Twilio error {exc.code}: {exc.msg}",
                "duration_ms": duration_ms,
                "normalized_phone": twilio_phone,
            }
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
            return {
                "success": False,
                "provider": "twilio",
                "error": f"Twilio exception: {exc}",
                "duration_ms": duration_ms,
                "normalized_phone": twilio_phone,
            }

        duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
        return {
            "success": True,
            "provider": "twilio",
            "error": None,
            "sid": getattr(message_obj, "sid", None),
            "duration_ms": duration_ms,
            "normalized_phone": twilio_phone,
        }

    async def _send_with_retries(
        self,
        provider: str,
        phone: str,
        message: str,
    ) -> dict[str, Any]:
        circuit = self.mtarget_circuit if provider == "mtarget" else self.twilio_circuit
        sender = self._send_via_mtarget_once if provider == "mtarget" else self._send_via_twilio_once

        if not circuit.can_attempt():
            error_msg = f"{provider} circuit breaker open"
            logger.warning(
                "sms_provider_circuit_open",
                extra={"channel": "sms", "provider": provider, "recipient": self._mask_phone(phone), "error": error_msg},
            )
            self.metrics.record_failure(provider)
            return {"success": False, "provider": provider, "error": error_msg}

        last_result: dict[str, Any] = {"success": False, "provider": provider, "error": "Unknown error"}
        for attempt in range(1, self.config.max_retries + 1):
            if attempt > 1:
                self.metrics.record_retry()
                backoff = self.config.retry_delay_seconds * (attempt - 1)
                await asyncio.sleep(backoff)

            try:
                result = await sender(phone, message)
            except Exception as exc:
                result = {
                    "success": False,
                    "provider": provider,
                    "error": f"Unhandled provider exception {type(exc).__name__}: {repr(exc)}",
                    "duration_ms": 0.0,
                }

            last_result = result
            if result.get("success"):
                circuit.record_success()
                self.metrics.record_success(provider, float(result.get("duration_ms", 0.0)))
                logger.info(
                    "sms_send_success",
                    extra={
                        "channel": "sms",
                        "provider": provider,
                        "recipient": self._mask_phone(phone),
                        "attempt": attempt,
                        "duration_ms": result.get("duration_ms"),
                        "sid": result.get("sid"),
                        "sender": result.get("sender"),
                    },
                )
                return result

            logger.warning(
                "sms_send_retry_or_fail",
                extra={
                    "channel": "sms",
                    "provider": provider,
                    "recipient": self._mask_phone(phone),
                    "attempt": attempt,
                    "max_retries": self.config.max_retries,
                    "error": result.get("error"),
                },
            )

        circuit.record_failure()
        self.metrics.record_failure(provider)
        logger.error(
            "sms_send_failed",
            extra={
                "channel": "sms",
                "provider": provider,
                "recipient": self._mask_phone(phone),
                "error": last_result.get("error"),
            },
        )
        return last_result

    async def send_otp_sms(self, phone: str, otp_code: str) -> dict[str, Any]:
        """
        Send OTP SMS with mTarget first and Twilio fallback.
        """
        if not self.rate_limiter.allow():
            error_msg = "Rate limit SMS atteint, réessayez plus tard."
            logger.error(
                "sms_rate_limited",
                extra={"channel": "sms", "provider": "system", "recipient": self._mask_phone(phone), "error": error_msg},
            )
            return {"success": False, "provider": None, "error": error_msg}

        phone_clean = (phone or "").strip()
        if not phone_clean:
            return {"success": False, "provider": None, "error": "Numero de telephone manquant"}

        message = (
            f"Votre code OTP GL3E: {otp_code}\n\n"
            f"Valide pendant {settings.OTP_EXPIRY_MINUTES} minutes.\n"
            "Ne partagez JAMAIS ce code!"
        )

        is_cm = self._is_cameroon_number(phone_clean)
        primary_provider = "mtarget" if is_cm else "twilio"
        fallback_provider = "twilio" if is_cm else "mtarget"

        logger.info(
            "sms_send_attempt",
            extra={
                "channel": "sms",
                "provider": primary_provider,
                "recipient": self._mask_phone(phone_clean),
                "sender": (self.config.mtarget_sender or "FM OTP").strip(),
                "mtarget_url": self.config.mtarget_url,
                "routing": "cameroon_primary_mtarget" if is_cm else "international_primary_twilio",
            },
        )

        primary_result = await self._send_with_retries(primary_provider, phone_clean, message)
        if primary_result.get("success"):
            return primary_result

        logger.warning(
            "sms_fallback_provider",
            extra={
                "channel": "sms",
                "provider": fallback_provider,
                "recipient": self._mask_phone(phone_clean),
                "error": primary_result.get("error"),
            },
        )

        fallback_result = await self._send_with_retries(fallback_provider, phone_clean, message)
        if fallback_result.get("success"):
            return fallback_result

        logger.error(
            "sms_all_providers_failed",
            extra={
                "channel": "sms",
                "recipient": self._mask_phone(phone_clean),
                "primary_provider": primary_provider,
                "primary_error": primary_result.get("error"),
                "fallback_provider": fallback_provider,
                "fallback_error": fallback_result.get("error"),
                "metrics": self.metrics.snapshot(),
            },
        )
        return {
            "success": False,
            "provider": None,
            "error": "Echec d'envoi SMS. Veuillez reessayer ou utiliser l'email.",
        }

    def get_metrics(self) -> dict[str, Any]:
        data = self.metrics.snapshot()
        data["circuit_breakers"] = {
            "mtarget": self.mtarget_circuit.state(),
            "twilio": self.twilio_circuit.state(),
        }
        return data

    def health_check(self) -> dict[str, Any]:
        mtarget_state = self.mtarget_circuit.state()
        twilio_state = self.twilio_circuit.state()
        status = "healthy"
        if mtarget_state == "open" and twilio_state == "open":
            status = "unhealthy"
        elif mtarget_state == "open" or twilio_state == "open":
            status = "degraded"
        return {
            "status": status,
            "providers": {
                "mtarget": {
                    "configured": bool(
                        self.config.mtarget_username
                        and self.config.mtarget_password
                        and self.config.mtarget_service_id
                    ),
                    "circuit_state": mtarget_state,
                },
                "twilio": {
                    "configured": bool(self.twilio_client),
                    "circuit_state": twilio_state,
                },
            },
            "metrics": self.metrics.snapshot(),
        }


# Global service instance
sms_service = SMSService()
