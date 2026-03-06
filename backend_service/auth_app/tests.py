from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import EmailOTP

User = get_user_model()


class AuthenticationTests(APITestCase):

    def setUp(self):
        self.register_url = reverse("auth_app:register")
        self.verify_email_url = reverse("auth_app:verify-email")
        self.login_url = reverse("auth_app:login")

        self.user_data = {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "role": "customer"
        }

    # ──────────────────────────────────────────────
    # Registration
    # ──────────────────────────────────────────────
    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

    # ──────────────────────────────────────────────
    # Email Verification
    # ──────────────────────────────────────────────
    def test_email_verification(self):
        # Register user
        self.client.post(self.register_url, self.user_data)

        user = User.objects.get(email="test@example.com")

        # Create OTP manually
        otp = EmailOTP.objects.create(
            email=user.email,
            otp="123456",
            purpose=EmailOTP.Purpose.EMAIL_VERIFICATION
        )

        verify_data = {
            "email": user.email,
            "otp": "123456",
            "purpose": "email_verification"
        }

        response = self.client.post(self.verify_email_url, verify_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

    # ──────────────────────────────────────────────
    # Login success
    # ──────────────────────────────────────────────
    def test_login_success(self):
        user = User.objects.create_user(
            email="login@example.com",
            password="StrongPass123!",
            first_name="Login",
            last_name="User"
        )
        user.is_email_verified = True
        user.save()

        login_data = {
            "email": "login@example.com",
            "password": "StrongPass123!"
        }

        response = self.client.post(self.login_url, login_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)

    # ──────────────────────────────────────────────
    # Login fails if email not verified
    # ──────────────────────────────────────────────
    def test_login_fails_if_email_not_verified(self):
        User.objects.create_user(
            email="fail@example.com",
            password="StrongPass123!",
            first_name="Fail",
            last_name="User"
        )

        login_data = {
            "email": "fail@example.com",
            "password": "StrongPass123!"
        }

        response = self.client.post(self.login_url, login_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)