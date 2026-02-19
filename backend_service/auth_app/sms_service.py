"""
SMS Service using Twilio.
Handles sending OTP codes via SMS for 2FA and phone verification.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class SMSService:
    """
    Service class for sending SMS messages via Twilio.
    """

    @staticmethod
    def send_sms(phone_number: str, message: str) -> bool:
        """
        Send an SMS message to the given phone number.

        Args:
            phone_number: E.164 formatted phone number e.g. +919876543210
            message: The text message content

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            from twilio.rest import Client

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number,
            )
            logger.info(f"SMS sent successfully to {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {e}")
            return False

    @staticmethod
    def send_otp_sms(
        phone_number: str, otp_code: str, purpose: str = "login_2fa"
    ) -> bool:
        """
        Send an OTP code via SMS with a purpose-specific message.

        Args:
            phone_number: E.164 formatted phone number
            otp_code: The 6-digit OTP
            purpose: 'login_2fa' or 'phone_verify'

        Returns:
            True if sent successfully, False otherwise
        """
        messages = {
            "login_2fa": (
                f"Your Virtual Boutique login verification code is: {otp_code}\n"
                f"Valid for 5 minutes. Do not share this code with anyone."
            ),
            "phone_verify": (
                f"Your Virtual Boutique phone verification code is: {otp_code}\n"
                f"Valid for 5 minutes. Do not share this code with anyone."
            ),
        }
        message = messages.get(purpose, f"Your Virtual Boutique code: {otp_code}")

        # Also print to console in development for easy debugging
        print("\n" + "=" * 60)
        print("📱 SMS DEBUG OUTPUT")
        print("=" * 60)
        print(f"📞 To      : {phone_number}")
        print(f"📝 Purpose : {purpose}")
        print(f"💬 Message : {message}")
        print("=" * 60 + "\n")

        return SMSService.send_sms(phone_number, message)
