import logging
import random
import redis

from app.core.config import settings
from app.services.exceptions import (
    OtpExpiredException,
    OtpInvalidException,
    OtpMaxAttemptsException,
)

logger = logging.getLogger(__name__)

OTP_TTL_SECONDS = 600
MAX_ATTEMPTS = 5
KEY_PREFIX = "otp:"


class OtpService:
    def __init__(self, redis_client: redis.Redis | None = None):
        """
        Accepts an optional Redis client for dependency injection (useful in tests).
        Falls back to a client built from settings.REDIS_URL.
        """
        if redis_client is not None:
            self._redis = redis_client
        else:
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _key(self, phone: str) -> str:
        return f"{KEY_PREFIX}{phone}"

    def _encode(self, otp: str, attempts: int) -> str:
        return f"{otp}|{attempts}"

    def _decode(self, raw: str) -> tuple[str, int]:
        otp, attempts_str = raw.split("|", 1)
        return otp, int(attempts_str)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, phone: str) -> str:
        """
        Generate a 6-digit OTP, store it in Redis with a 600-second TTL,
        and return the OTP string.

        Also prints the OTP to console/log so the auth flow can be tested
        without real SMS (Twilio not yet configured).
        """
        otp = f"{random.randint(0, 999_999):06d}"
        value = self._encode(otp, 0)
        self._redis.set(self._key(phone), value, ex=OTP_TTL_SECONDS)

        # DEV convenience — remove / gate behind a feature flag once Twilio is live
        print(f"[DEV OTP] Phone: {phone} Code: {otp}")
        logger.info("[DEV OTP] Phone: %s Code: %s", phone, otp)

        return otp

    def verify(self, phone: str, otp: str) -> bool:
        """
        Verify the supplied OTP for a given phone number.

        Raises:
            OtpExpiredException      – key not present in Redis
            OtpMaxAttemptsException  – 5 or more failed attempts recorded
            OtpInvalidException      – OTP does not match (attempt counter incremented)

        Returns True on a successful match (key is deleted from Redis).
        """
        key = self._key(phone)
        raw = self._redis.get(key)

        if raw is None:
            raise OtpExpiredException()

        stored_otp, attempts = self._decode(raw)

        if attempts >= MAX_ATTEMPTS:
            raise OtpMaxAttemptsException()

        if otp != stored_otp:
            # Increment attempt count while preserving the remaining TTL
            ttl = self._redis.ttl(key)
            new_value = self._encode(stored_otp, attempts + 1)
            # ttl can be -1 (no expiry, shouldn't happen) or -2 (gone); guard both
            if ttl > 0:
                self._redis.set(key, new_value, ex=ttl)
            else:
                self._redis.set(key, new_value)
            raise OtpInvalidException()

        # Correct OTP — clean up and signal success
        self._redis.delete(key)
        return True

    def invalidate(self, phone: str) -> None:
        """Delete the OTP key for the given phone number."""
        self._redis.delete(self._key(phone))
