"""
Business logic services for authentication.
Handles email sending, OTP generation, SMS OTP, and authentication operations.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import SMSOTP, EmailOTP, User

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Email Service
# ──────────────────────────────────────────────────────────────────────────────


class EmailService:
    """
    Handles all outgoing emails.
    """

    @staticmethod
    def _send(subject: str, message: str, recipient: str) -> bool:
        """Internal helper — wraps send_mail with error handling."""
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(
                    settings, "DEFAULT_FROM_EMAIL", "noreply@virtualboutique.com"
                ),
                recipient_list=[recipient],
                fail_silently=False,
            )
            logger.info(f"Email sent to {recipient}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            return False

    @staticmethod
    def send_otp_email(
        email: str, otp_code: str, purpose: str = "email_verification"
    ) -> bool:
        """
        Send OTP code to user's email.
        Used for: email_verification and password_reset ONLY.
        Login 2FA no longer sends email OTPs — it uses SMS or TOTP.

        Args:
            email:    Recipient email address
            otp_code: 6-digit OTP code
            purpose:  'email_verification' or 'password_reset'

        Returns:
            True if sent successfully
        """
        subjects = {
            "email_verification": "Verify Your Email - Virtual Boutique",
            "password_reset": "Password Reset Request - Virtual Boutique",
        }
        subject = subjects.get(purpose, "Verification Code - Virtual Boutique")

        message = (
            f"Hello,\n\n"
            f"Your verification code is: {otp_code}\n\n"
            f"This code will expire in 10 minutes.\n\n"
            f"If you did not request this code, please ignore this email.\n\n"
            f"Best regards,\n"
            f"Virtual Boutique Team"
        )
        return EmailService._send(subject, message, email)

    @staticmethod
    def send_welcome_email(user: User) -> bool:
        """
        Send welcome email after successful email verification.

        Args:
            user: The newly verified User object

        Returns:
            True if sent successfully
        """
        subject = "Welcome to Virtual Boutique!"
        message = (
            f"Hello {user.get_full_name()},\n\n"
            f"Welcome to Virtual Boutique Platform!\n\n"
            f"Your account has been successfully created and verified.\n\n"
            f"Role  : {user.get_role_display()}\n"
            f"Email : {user.email}\n\n"
            f"You can now log in and start exploring our platform.\n\n"
            f"Best regards,\n"
            f"Virtual Boutique Team"
        )
        return EmailService._send(subject, message, user.email)


# ──────────────────────────────────────────────────────────────────────────────
# Email OTP Service
# ──────────────────────────────────────────────────────────────────────────────


class OTPService:
    """
    Manages email OTPs (registration verification and password reset).
    """

    @staticmethod
    def create_otp(
        email: str, purpose: str = EmailOTP.Purpose.EMAIL_VERIFICATION
    ) -> tuple[bool, str]:
        """
        Invalidate old OTPs, create a new one, and send it.

        Args:
            email:   User's email address
            purpose: EmailOTP.Purpose choice

        Returns:
            (success: bool, message: str)
        """
        try:
            # Invalidate any existing unused OTPs for this email + purpose
            EmailOTP.objects.filter(
                email=email,
                purpose=purpose,
                is_verified=False,
            ).update(is_verified=True)

            otp_code = EmailOTP.generate_otp()
            EmailOTP.objects.create(email=email, otp=otp_code, purpose=purpose)

            sent = EmailService.send_otp_email(email, otp_code, purpose)
            if sent:
                return True, "OTP sent successfully to your email."
            return False, "Failed to send OTP email. Please try again."

        except Exception as e:
            logger.error(f"Failed to create email OTP for {email}: {e}")
            return False, "An error occurred. Please try again."

    @staticmethod
    def verify_otp(
        email: str,
        otp_code: str,
        purpose: str = EmailOTP.Purpose.EMAIL_VERIFICATION,
    ) -> tuple[bool, str]:
        """
        Verify an email OTP code.

        Args:
            email:    User's email address
            otp_code: Code submitted by user
            purpose:  EmailOTP.Purpose choice

        Returns:
            (success: bool, message: str)
        """
        try:
            otp_obj = (
                EmailOTP.objects.filter(
                    email=email,
                    otp=otp_code,
                    purpose=purpose,
                    is_verified=False,
                )
                .order_by("-created_at")
                .first()
            )

            if not otp_obj:
                return False, "Invalid OTP code."
            if not otp_obj.is_valid():
                return False, "OTP has expired. Please request a new one."

            otp_obj.is_verified = True
            otp_obj.save()
            return True, "OTP verified successfully."

        except Exception as e:
            logger.error(f"Failed to verify email OTP for {email}: {e}")
            return False, "An error occurred. Please try again."


# ──────────────────────────────────────────────────────────────────────────────
# SMS OTP Service
# ──────────────────────────────────────────────────────────────────────────────


class SMSOTPService:
    """
    Manages SMS OTPs (login 2FA and phone number verification).
    """

    @staticmethod
    def create_otp(
        phone: str, purpose: str = SMSOTP.Purpose.LOGIN_2FA
    ) -> tuple[bool, str]:
        """
        Invalidate old SMS OTPs, create a new one, and send it.

        Args:
            phone:   E.164 phone number e.g. +919876543210
            purpose: SMSOTP.Purpose choice

        Returns:
            (success: bool, message: str)
        """
        from .sms_service import SMSService

        try:
            # Invalidate existing unused OTPs for this phone + purpose
            SMSOTP.objects.filter(
                phone=phone,
                purpose=purpose,
                is_verified=False,
            ).update(is_verified=True)

            otp_code = SMSOTP.generate_otp()
            SMSOTP.objects.create(phone=phone, otp=otp_code, purpose=purpose)

            sent = SMSService.send_otp_sms(phone, otp_code, purpose)
            if sent:
                return True, "OTP sent to your phone number."
            return False, "Failed to send SMS. Please try again."

        except Exception as e:
            logger.error(f"Failed to create SMS OTP for {phone}: {e}")
            return False, "An error occurred. Please try again."

    @staticmethod
    def verify_otp(
        phone: str,
        otp_code: str,
        purpose: str = SMSOTP.Purpose.LOGIN_2FA,
    ) -> tuple[bool, str]:
        """
        Verify an SMS OTP code.

        Args:
            phone:    E.164 phone number
            otp_code: Code submitted by user
            purpose:  SMSOTP.Purpose choice

        Returns:
            (success: bool, message: str)
        """
        try:
            otp_obj = (
                SMSOTP.objects.filter(
                    phone=phone,
                    otp=otp_code,
                    purpose=purpose,
                    is_verified=False,
                )
                .order_by("-created_at")
                .first()
            )

            if not otp_obj:
                return False, "Invalid OTP code."
            if not otp_obj.is_valid():
                return False, "OTP has expired. Please request a new one."

            otp_obj.is_verified = True
            otp_obj.save()
            return True, "OTP verified successfully."

        except Exception as e:
            logger.error(f"Failed to verify SMS OTP for {phone}: {e}")
            return False, "An error occurred. Please try again."


# ──────────────────────────────────────────────────────────────────────────────
# Authentication Service
# ──────────────────────────────────────────────────────────────────────────────


class AuthenticationService:
    """
    High-level authentication operations.
    """

    @staticmethod
    def verify_email(user: User) -> bool:
        """
        Mark user's email as verified and send welcome email.

        Args:
            user: User object

        Returns:
            True if successful
        """
        try:
            user.is_email_verified = True
            user.save()
            EmailService.send_welcome_email(user)
            return True
        except Exception as e:
            logger.error(f"Failed to verify email for {user.email}: {e}")
            return False
