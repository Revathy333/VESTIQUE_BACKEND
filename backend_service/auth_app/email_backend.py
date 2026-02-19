"""
Custom Email Backend
Sends real emails to users AND prints them to the console for debugging.
"""

from django.core.mail.backends.smtp import EmailBackend as SMTPBackend


class EmailAndConsoleBackend(SMTPBackend):
    """
    Custom email backend that:
    1. Sends real emails via SMTP (Gmail)
    2. Also prints emails to console for debugging
    """

    def send_messages(self, email_messages):
        """
        Send emails via SMTP and also print to console.
        """
        # First, send the real email via SMTP
        smtp_result = super().send_messages(email_messages)

        # Then, also print to console for debugging
        print("\n" + "=" * 80)
        print("📧 EMAIL SENT - Console Debug Output")
        print("=" * 80)

        for message in email_messages:
            print(f"\n🔹 Subject: {message.subject}")
            print(f"🔹 From: {message.from_email}")
            print(f"🔹 To: {', '.join(message.to)}")
            print("\n📝 Message Body:")
            print("-" * 80)
            print(message.body)
            print("-" * 80)

        print("=" * 80 + "\n")

        return smtp_result
