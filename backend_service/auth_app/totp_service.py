"""
TOTP (Time-based One-Time Password) Service.
Handles secret generation, QR code creation, and code verification
for Google Authenticator / Authy style 2FA.
"""

import base64
import io
import logging

import pyotp
import qrcode
from django.conf import settings

logger = logging.getLogger(__name__)


class TOTPService:
    """
    Service class for TOTP-based 2FA.

    How it works:
      1. generate_secret()  → gives user a base32 secret
      2. generate_qr_code() → encodes that secret into a QR code
      3. User scans QR code in Google Authenticator / Authy
      4. verify_totp()      → validates the 6-digit code the app generates
    """

    @staticmethod
    def generate_secret() -> str:
        """
        Generate a new random base32 TOTP secret.
        Store this on the user model (totp_secret_pending until confirmed).

        Returns:
            A base32 secret string
        """
        return pyotp.random_base32()

    @staticmethod
    def get_totp_uri(secret: str, email: str) -> str:
        """
        Build the otpauth:// URI used inside QR codes.

        Args:
            secret: User's TOTP secret
            email:  User's email (used as account label in the auth app)

        Returns:
            otpauth:// URI string
        """
        issuer = getattr(settings, "TOTP_ISSUER_NAME", "Virtual Boutique")
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name=issuer)

    @staticmethod
    def generate_qr_code(secret: str, email: str) -> str:
        """
        Generate a QR code image as a base64-encoded PNG string.
        The frontend can render it directly: <img src="data:image/png;base64,..." />

        Args:
            secret: User's TOTP secret
            email:  User's email address

        Returns:
            Base64-encoded PNG string
        """
        uri = TOTPService.get_totp_uri(secret, email)
        qr = qrcode.make(uri)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    @staticmethod
    def verify_totp(secret: str, code: str) -> bool:
        """
        Verify a 6-digit TOTP code against the given secret.
        Allows ±1 time window (30 seconds) to handle clock drift.

        Args:
            secret: User's stored TOTP secret (totp_secret field)
            code:   The 6-digit code from the authenticator app

        Returns:
            True if valid, False otherwise
        """
        if not secret or not code:
            logger.warning("TOTP verify called with empty secret or code")
            return False
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=1)
        except Exception as e:
            logger.error(f"TOTP verification error: {e}")
            return False
