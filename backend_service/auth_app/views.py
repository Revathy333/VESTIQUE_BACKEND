# """
# Authentication API Views
# Handles user registration, login, OTP verification, logout, and token management.
# """

# from rest_framework import status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny, IsAuthenticated
# from rest_framework_simplejwt.tokens import RefreshToken
# from rest_framework_simplejwt.exceptions import TokenError
# from django.contrib.auth import get_user_model
# from django.db import models
# from .serializers import GoogleAuthSerializer,ForgotPasswordSerializer,ResetPasswordSerializer

# from .serializers import (
#     UserRegistrationSerializer,
#     EmailOTPVerificationSerializer,
#     ResendOTPSerializer,
#     UserLoginSerializer,
#     UserSerializer,
#     LogoutSerializer
# )
# from .services import OTPService, AuthenticationService
# from .models import RefreshTokenBlacklist,EmailOTP

# User = get_user_model()


# class RegisterView(APIView):
#     """
#     API endpoint for user registration.

#     POST /api/auth/register/

#     Request Body:
#     {
#         "email": "user@example.com",
#         "first_name": "John",
#         "last_name": "Doe",
#         "phone": "+1234567890",
#         "role": "customer",
#         "password": "SecurePassword123!",
#         "password_confirm": "SecurePassword123!"
#     }

#     Response:
#     {
#         "message": "Registration successful. Please check your email for OTP.",
#         "email": "user@example.com",
#         "user": {...}
#     }
#     """
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = UserRegistrationSerializer(data=request.data)

#         if serializer.is_valid():
#             # Create user
#             user = serializer.save()

#             # Generate and send OTP
#             success, message = OTPService.create_otp(
#                 email=user.email,
#                 purpose='email_verification'
#             )

#             if success:
#                 return Response({
#                     'message': 'Registration successful. Please check your email for OTP.',
#                     'email': user.email,
#                     'user': UserSerializer(user).data
#                 }, status=status.HTTP_201_CREATED)
#             else:
#                 # User created but OTP failed to send
#                 return Response({
#                     'message': 'User registered but failed to send OTP. Please request a new OTP.',
#                     'email': user.email,
#                     'user': UserSerializer(user).data
#                 }, status=status.HTTP_201_CREATED)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class VerifyEmailView(APIView):
#     """
#     API endpoint for email OTP verification.

#     POST /api/auth/verify-email/

#     Request Body:
#     {
#         "email": "user@example.com",
#         "otp": "123456"
#     }

#     Response:
#     {
#         "message": "Email verified successfully. You can now log in.",
#         "user": {...}
#     }
#     """
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = EmailOTPVerificationSerializer(data=request.data)

#         if serializer.is_valid():
#             email = serializer.validated_data['email']
#             otp_obj = serializer.validated_data['otp_obj']

#             # Get user
#             try:
#                 user = User.objects.get(email=email)
#             except User.DoesNotExist:
#                 return Response({
#                     'error': 'User not found.'
#                 }, status=status.HTTP_404_NOT_FOUND)

#             # Mark OTP as verified
#             otp_obj.is_verified = True
#             otp_obj.save()

#             # ── 2FA LOGIN: return tokens instead ───────────────────
#             if otp_obj.purpose == EmailOTP.Purpose.LOGIN_2FA:
#                 refresh = RefreshToken.for_user(user)
#                 return Response({
#                     'message': 'Login successful',
#                     'tokens': {
#                         'access': str(refresh.access_token),
#                         'refresh': str(refresh),
#                     },
#                     'user': UserSerializer(user).data
#                 }, status=status.HTTP_200_OK)

#             # Mark user email as verified
#             AuthenticationService.verify_email(user)

#             return Response({
#                 'message': 'Email verified successfully. You can now log in.',
#                 'user': UserSerializer(user).data
#             }, status=status.HTTP_200_OK)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class ResendOTPView(APIView):
#     """
#     API endpoint to resend OTP.

#     POST /api/auth/resend-otp/

#     Request Body:
#     {
#         "email": "user@example.com",
#         "purpose": "email_verification"
#     }

#     Response:
#     {
#         "message": "OTP sent successfully to your email."
#     }
#     """
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = ResendOTPSerializer(data=request.data)

#         if serializer.is_valid():
#             email = serializer.validated_data['email']
#             purpose = serializer.validated_data['purpose']

#             # Create and send new OTP
#             success, message = OTPService.create_otp(email, purpose)

#             if success:
#                 return Response({
#                     'message': message
#                 }, status=status.HTTP_200_OK)
#             else:
#                 return Response({
#                     'error': message
#                 }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class LoginView(APIView):
#     """
#     API endpoint for user login.

#     POST /api/auth/login/

#     Request Body:
#     {
#         "email": "user@example.com",
#         "password": "SecurePassword123!"
#     }

#     Response:
#     {
#         "message": "Login successful",
#         "tokens": {
#             "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#             "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
#         },
#         "user": {...}
#     }
#     """
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = UserLoginSerializer(data=request.data)

#         if serializer.is_valid():
#             user = serializer.validated_data['user']
#             # ── 2FA CHECK ──────────────────────────────────────────
#             if user.is_2fa_enabled:
#                 success, message = OTPService.create_otp(
#                     email=user.email,
#                     purpose=EmailOTP.Purpose.LOGIN_2FA
#                 )
#                 if success:
#                     return Response({
#                         'requires_2fa': True,
#                         'email': user.email,
#                         'message': 'A verification code has been sent to your email.',
#                     }, status=status.HTTP_200_OK)
#                 else:
#                     return Response({
#                         'error': 'Failed to send 2FA code. Please try again.'
#                     }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#             # Generate JWT tokens
#             refresh = RefreshToken.for_user(user)

#             return Response({
#                 'message': 'Login successful',
#                 'tokens': {
#                     'access': str(refresh.access_token),
#                     'refresh': str(refresh),
#                 },
#                 'user': UserSerializer(user).data
#             }, status=status.HTTP_200_OK)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class LogoutView(APIView):
#     """
#     API endpoint for user logout.
#     Blacklists the refresh token.

#     POST /api/auth/logout/

#     Headers:
#     Authorization: Bearer <access_token>

#     Request Body:
#     {
#         "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
#     }

#     Response:
#     {
#         "message": "Logout successful"
#     }
#     """
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = LogoutSerializer(data=request.data)

#         if serializer.is_valid():
#             try:
#                 refresh_token = serializer.validated_data['refresh']

#                 # Blacklist the refresh token
#                 RefreshTokenBlacklist.objects.create(
#                     token=refresh_token,
#                     user=request.user
#                 )

#                 # Also try to blacklist using simplejwt (if token is valid)
#                 try:
#                     token = RefreshToken(refresh_token)
#                     token.blacklist()
#                 except Exception:
#                     pass  # Token might already be invalid

#                 return Response({
#                     'message': 'Logout successful'
#                 }, status=status.HTTP_200_OK)

#             except TokenError:
#                 return Response({
#                     'error': 'Invalid token'
#                 }, status=status.HTTP_400_BAD_REQUEST)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class RefreshTokenView(APIView):
#     """
#     API endpoint to refresh access token.

#     POST /api/auth/token/refresh/

#     Request Body:
#     {
#         "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
#     }

#     Response:
#     {
#         "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#         "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."  (if rotation enabled)
#     }
#     """
#     permission_classes = [AllowAny]

#     def post(self, request):
#         refresh_token = request.data.get('refresh')

#         if not refresh_token:
#             return Response({
#                 'error': 'Refresh token is required'
#             }, status=status.HTTP_400_BAD_REQUEST)

#         # Check if token is blacklisted
#         if RefreshTokenBlacklist.objects.filter(token=refresh_token).exists():
#             return Response({
#                 'error': 'Token has been blacklisted'
#             }, status=status.HTTP_401_UNAUTHORIZED)

#         try:
#             refresh = RefreshToken(refresh_token)

#             response_data = {
#                 'access': str(refresh.access_token),
#             }

#             # If rotation is enabled, include new refresh token
#             if hasattr(refresh, 'refresh_token'):
#                 response_data['refresh'] = str(refresh)

#             return Response(response_data, status=status.HTTP_200_OK)

#         except TokenError as e:
#             return Response({
#                 'error': str(e)
#             }, status=status.HTTP_401_UNAUTHORIZED)


# class UserProfileView(APIView):
#     """
#     API endpoint to get current user profile.

#     GET /api/auth/profile/

#     Headers:
#     Authorization: Bearer <access_token>

#     Response:
#     {
#         "user": {...}
#     }
#     """
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         serializer = UserSerializer(request.user)
#         return Response({
#             'user': serializer.data
#         }, status=status.HTTP_200_OK)


# class ChangePasswordView(APIView):
#     """
#     API endpoint to change user password.

#     POST /api/auth/change-password/

#     Headers:
#     Authorization: Bearer <access_token>

#     Request Body:
#     {
#         "old_password": "OldPassword123!",
#         "new_password": "NewPassword123!",
#         "new_password_confirm": "NewPassword123!"
#     }

#     Response:
#     {
#         "message": "Password changed successfully"
#     }
#     """
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         old_password = request.data.get('old_password')
#         new_password = request.data.get('new_password')
#         new_password_confirm = request.data.get('new_password_confirm')

#         # Validate input
#         if not all([old_password, new_password, new_password_confirm]):
#             return Response({
#                 'error': 'All fields are required'
#             }, status=status.HTTP_400_BAD_REQUEST)

#         # Check if new passwords match
#         if new_password != new_password_confirm:
#             return Response({
#                 'error': 'New passwords do not match'
#             }, status=status.HTTP_400_BAD_REQUEST)

#         # Check if old password is correct
#         if not request.user.check_password(old_password):
#             return Response({
#                 'error': 'Old password is incorrect'
#             }, status=status.HTTP_400_BAD_REQUEST)

#         # Set new password
#         request.user.set_password(new_password)
#         request.user.save()

#         return Response({
#             'message': 'Password changed successfully'
#         }, status=status.HTTP_200_OK)


# class GoogleAuthView(APIView):
#     """
#     API endpoint for Google OAuth authentication.

#     POST /api/auth/google/
#     """
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = GoogleAuthSerializer(data=request.data)

#         if serializer.is_valid():
#             email = serializer.validated_data['email']
#             google_id = serializer.validated_data['google_id']
#             first_name = serializer.validated_data['first_name']
#             last_name = serializer.validated_data['last_name']
#             profile_picture = serializer.validated_data['profile_picture']
#             email_verified = serializer.validated_data['email_verified']
#             role = serializer.validated_data.get('role', User.Role.CUSTOMER)

#             # Check if user exists with this email or google_id
#             user = User.objects.filter(
#                 models.Q(email=email) | models.Q(google_id=google_id)
#             ).first()

#             is_new_user = False

#             if user:
#                 # User exists - update Google info if needed
#                 if not user.google_id:
#                     user.google_id = google_id
#                 if not user.profile_picture:
#                     user.profile_picture = profile_picture
#                 if not user.is_email_verified and email_verified:
#                     user.is_email_verified = True
#                 user.save()
#             else:
#                 # Create new user
#                 is_new_user = True
#                 user = User.objects.create(
#                     email=email,
#                     google_id=google_id,
#                     first_name=first_name,
#                     last_name=last_name,
#                     profile_picture=profile_picture,
#                     is_email_verified=email_verified,
#                     role=role,
#                     is_active=True
#                 )

#                 # Set verification status
#                 if user.requires_verification():
#                     user.verification_status = User.VerificationStatus.PENDING
#                 else:
#                     user.verification_status = User.VerificationStatus.NOT_REQUIRED
#                 user.save()

#             # Generate JWT tokens
#             refresh = RefreshToken.for_user(user)

#             return Response({
#                 'message': 'Login successful' if not is_new_user else 'Account created successfully',
#                 'tokens': {
#                     'access': str(refresh.access_token),
#                     'refresh': str(refresh),
#                 },
#                 'user': UserSerializer(user).data,
#                 'is_new_user': is_new_user
#             }, status=status.HTTP_200_OK)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class ForgotPasswordView(APIView):
#     """
#     API endpoint to request password reset.
#     Sends OTP to user's email.

#     POST /api/auth/forgot-password/

#     Request Body:
#     {
#         "email": "user@example.com"
#     }

#     Response:
#     {
#         "message": "Password reset code has been sent to your email.",
#         "email": "user@example.com"
#     }
#     """
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = ForgotPasswordSerializer(data=request.data)

#         if serializer.is_valid():
#             email = serializer.validated_data['email']

#             # Generate and send OTP
#             success, message = OTPService.create_otp(
#                 email=email,
#                 purpose=EmailOTP.Purpose.PASSWORD_RESET
#             )

#             if success:
#                 return Response({
#                     'message': 'Password reset code has been sent to your email.',
#                     'email': email
#                 }, status=status.HTTP_200_OK)
#             else:
#                 return Response({
#                     'error': 'Failed to send reset code. Please try again.'
#                 }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class ResetPasswordView(APIView):
#     """
#     API endpoint to reset password using OTP.

#     POST /api/auth/reset-password/

#     Request Body:
#     {
#         "email": "user@example.com",
#         "otp": "123456",
#         "new_password": "NewPassword123!",
#         "new_password_confirm": "NewPassword123!"
#     }

#     Response:
#     {
#         "message": "Password has been reset successfully. You can now log in with your new password."
#     }
#     """
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = ResetPasswordSerializer(data=request.data)

#         if serializer.is_valid():
#             email = serializer.validated_data['email']
#             new_password = serializer.validated_data['new_password']
#             otp_obj = serializer.validated_data['otp_obj']

#             # Get user
#             try:
#                 user = User.objects.get(email=email)
#             except User.DoesNotExist:
#                 return Response({
#                     'error': 'User not found.'
#                 }, status=status.HTTP_404_NOT_FOUND)

#             # Mark OTP as verified
#             otp_obj.is_verified = True
#             otp_obj.save()

#             # Reset password
#             user.set_password(new_password)
#             user.save()

#             return Response({
#                 'message': 'Password has been reset successfully. You can now log in with your new password.'
#             }, status=status.HTTP_200_OK)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


"""
Authentication API Views.
Handles registration, login, OTP verification, 2FA setup/verify, logout, and tokens.
"""

import logging

from django.contrib.auth import get_user_model
from django.db import models
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import SMSOTP, EmailOTP, RefreshTokenBlacklist
from .serializers import (
    EmailOTPVerificationSerializer,
    ForgotPasswordSerializer,
    GoogleAuthSerializer,
    LogoutSerializer,
    ResendOTPSerializer,
    ResetPasswordSerializer,
    TwoFAConfirmSetupSerializer,
    TwoFADisableSerializer,
    TwoFASetupSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    Verify2FASerializer,
)
from .services import AuthenticationService, OTPService, SMSOTPService

User = get_user_model()
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _issue_tokens(user):
    """Generate a JWT token pair for the given user."""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Registration & Email Verification
# ──────────────────────────────────────────────────────────────────────────────


class RegisterView(APIView):
    """
    POST /api/auth/register/

    Register a new user. Sends an email OTP to verify the email address.
    Designers and tailors must also upload certificate, id_proof, and optional portfolio.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        success, message = OTPService.create_otp(
            email=user.email,
            purpose=EmailOTP.Purpose.EMAIL_VERIFICATION,
        )

        return Response(
            {
                "message": (
                    "Registration successful. Please check your email for the verification code."
                    if success
                    else "Registered but failed to send OTP. Use resend-otp endpoint."
                ),
                "email": user.email,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    """
    POST /api/auth/verify-email/

    Verify email using OTP received during registration.
    After success the user can log in.

    Body: { email, otp, purpose }   (purpose defaults to 'email_verification')
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailOTPVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        otp_obj = serializer.validated_data["otp_obj"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Mark OTP as used
        otp_obj.is_verified = True
        otp_obj.save()

        # Mark email verified + send welcome email
        AuthenticationService.verify_email(user)

        return Response(
            {
                "message": "Email verified successfully. You can now log in.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class ResendOTPView(APIView):
    """
    POST /api/auth/resend-otp/

    Resend an email OTP (email_verification or password_reset).
    Body: { email, purpose }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        purpose = serializer.validated_data["purpose"]

        success, message = OTPService.create_otp(email, purpose)

        if success:
            return Response({"message": message}, status=status.HTTP_200_OK)
        return Response(
            {"error": message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ──────────────────────────────────────────────────────────────────────────────
# Login (step 1 — credentials)
# ──────────────────────────────────────────────────────────────────────────────


class LoginView(APIView):
    """
    POST /api/auth/login/

    Step 1 of login. Validates email + password.

    If 2FA is OFF  → returns JWT tokens immediately.
    If 2FA is TOTP → returns { requires_2fa: true, two_fa_method: 'totp' }
                     Frontend should show TOTP input. No code is sent.
    If 2FA is SMS  → sends SMS OTP to phone, returns { requires_2fa: true, two_fa_method: 'sms' }
                     Frontend should show SMS OTP input.

    After a 2FA prompt the frontend calls POST /api/auth/verify-2fa/
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]

        # ── 2FA enabled ───────────────────────────────────────────────────────
        if user.is_2fa_enabled:
            if user.two_fa_method == User.TwoFAMethod.SMS:
                if not user.phone:
                    return Response(
                        {"error": "SMS 2FA is enabled but no phone number is on file."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                success, message = SMSOTPService.create_otp(
                    phone=user.phone,
                    purpose=SMSOTP.Purpose.LOGIN_2FA,
                )
                if not success:
                    return Response(
                        {"error": f"Failed to send 2FA SMS: {message}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            # For TOTP we don't send anything — the code is already in the app
            return Response(
                {
                    "requires_2fa": True,
                    "two_fa_method": user.two_fa_method,
                    "email": user.email,
                    "message": (
                        "Enter the code from your authenticator app."
                        if user.two_fa_method == User.TwoFAMethod.TOTP
                        else "A verification code has been sent to your phone."
                    ),
                },
                status=status.HTTP_200_OK,
            )

        # ── No 2FA — issue tokens straight away ───────────────────────────────
        return Response(
            {
                "message": "Login successful.",
                "tokens": _issue_tokens(user),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Login (step 2 — 2FA verification)
# ──────────────────────────────────────────────────────────────────────────────


class Verify2FAView(APIView):
    """
    POST /api/auth/verify-2fa/

    Step 2 of login when 2FA is enabled.
    Submit the 6-digit code (TOTP or SMS OTP).
    On success returns JWT tokens.

    Body: { email, code }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = Verify2FASerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]

        return Response(
            {
                "message": "Login successful.",
                "tokens": _issue_tokens(user),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────────────────────────────────────
# 2FA Setup (authenticated)
# ──────────────────────────────────────────────────────────────────────────────


class TwoFASetupView(APIView):
    """
    POST /api/auth/2fa/setup/

    Initiate 2FA setup. Requires authentication.

    Body: { method: 'totp' | 'sms', phone: '+91...' }   (phone only needed for SMS)

    TOTP response includes a base64 QR code to scan in Google Authenticator.
    SMS response sends an OTP to the phone to confirm ownership.

    After this, call POST /api/auth/2fa/confirm/ with the first code to activate.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TwoFASetupSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        method = serializer.validated_data["method"]
        phone = serializer.validated_data.get("phone")

        # ── TOTP setup ────────────────────────────────────────────────────────
        if method == User.TwoFAMethod.TOTP:
            from .totp_service import TOTPService

            secret = TOTPService.generate_secret()
            # Store temporarily — only activated after the user confirms a code
            user.totp_secret_pending = secret
            user.save(update_fields=["totp_secret_pending"])

            qr_code = TOTPService.generate_qr_code(secret, user.email)

            return Response(
                {
                    "message": (
                        "Scan the QR code with Google Authenticator or Authy, "
                        "then call /2fa/confirm/ with the first 6-digit code."
                    ),
                    "method": method,
                    "qr_code": f"data:image/png;base64,{qr_code}",
                    # Also expose the raw secret for manual entry in the app
                    "secret": secret,
                },
                status=status.HTTP_200_OK,
            )

        # ── SMS setup ─────────────────────────────────────────────────────────
        if phone:
            user.phone = phone
            user.is_phone_verified = False
            user.save(update_fields=["phone", "is_phone_verified"])

        success, message = SMSOTPService.create_otp(
            phone=user.phone,
            purpose=SMSOTP.Purpose.PHONE_VERIFY,
        )
        if not success:
            return Response(
                {"error": f"Failed to send SMS: {message}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": (
                    f"A verification code has been sent to {user.phone}. "
                    "Enter it at /2fa/confirm/ to activate SMS 2FA."
                ),
                "method": method,
            },
            status=status.HTTP_200_OK,
        )


class TwoFAConfirmSetupView(APIView):
    """
    POST /api/auth/2fa/confirm/

    Confirm 2FA setup by verifying the first code.
    This activates 2FA on the account.

    Body: { code: '123456' }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TwoFAConfirmSetupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        code = serializer.validated_data["code"]

        # Determine which method is being confirmed based on what's pending
        if user.totp_secret_pending:
            # ── Confirm TOTP ──────────────────────────────────────────────────
            from .totp_service import TOTPService

            if not TOTPService.verify_totp(user.totp_secret_pending, code):
                return Response(
                    {
                        "error": "Invalid code. Make sure your app's time is synced and try again."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.totp_secret = user.totp_secret_pending
            user.totp_secret_pending = ""
            user.two_fa_method = User.TwoFAMethod.TOTP
            user.save(
                update_fields=["totp_secret", "totp_secret_pending", "two_fa_method"]
            )

            return Response(
                {
                    "message": "TOTP 2FA has been activated. Your account is now more secure.",
                    "two_fa_method": user.two_fa_method,
                },
                status=status.HTTP_200_OK,
            )

        elif user.phone:
            # ── Confirm SMS ───────────────────────────────────────────────────
            success, message = SMSOTPService.verify_otp(
                phone=user.phone,
                otp_code=code,
                purpose=SMSOTP.Purpose.PHONE_VERIFY,
            )
            if not success:
                return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

            user.is_phone_verified = True
            user.two_fa_method = User.TwoFAMethod.SMS
            user.save(update_fields=["is_phone_verified", "two_fa_method"])

            return Response(
                {
                    "message": "SMS 2FA has been activated. Your account is now more secure.",
                    "two_fa_method": user.two_fa_method,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "No pending 2FA setup found. Please start setup again."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class TwoFADisableView(APIView):
    """
    POST /api/auth/2fa/disable/

    Disable 2FA. Requires current password for security.
    Body: { password: '...' }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TwoFADisableSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        password = serializer.validated_data["password"]

        if not user.check_password(password):
            return Response(
                {"error": "Incorrect password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_2fa_enabled:
            return Response(
                {"message": "2FA is not currently enabled on your account."},
                status=status.HTTP_200_OK,
            )

        user.two_fa_method = User.TwoFAMethod.DISABLED
        user.totp_secret = ""
        user.totp_secret_pending = ""
        user.save(update_fields=["two_fa_method", "totp_secret", "totp_secret_pending"])

        return Response(
            {"message": "2FA has been disabled on your account."},
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Logout
# ──────────────────────────────────────────────────────────────────────────────


class LogoutView(APIView):
    """
    POST /api/auth/logout/

    Blacklist the refresh token so it can no longer be used.
    Body: { refresh: '<token>' }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        refresh_token = serializer.validated_data["refresh"]

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass

        # Also store in our own blacklist table
        RefreshTokenBlacklist.objects.get_or_create(
            token=refresh_token, user=request.user
        )

        return Response(
            {"message": "Logged out successfully."}, status=status.HTTP_200_OK
        )


# ──────────────────────────────────────────────────────────────────────────────
# Token Refresh
# ──────────────────────────────────────────────────────────────────────────────


class RefreshTokenView(APIView):
    """
    POST /api/auth/token/refresh/

    Get a new access token using a valid refresh token.
    Body: { refresh: '<token>' }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reject if the token has been blacklisted
        if RefreshTokenBlacklist.objects.filter(token=refresh_token).exists():
            return Response(
                {"error": "Token has been invalidated. Please log in again."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            token = RefreshToken(refresh_token)
            return Response(
                {"access": str(token.access_token)}, status=status.HTTP_200_OK
            )
        except TokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


# ──────────────────────────────────────────────────────────────────────────────
# User Profile
# ──────────────────────────────────────────────────────────────────────────────


class UserProfileView(APIView):
    """
    GET  /api/auth/profile/  → Returns the authenticated user's profile.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {"user": UserSerializer(request.user).data}, status=status.HTTP_200_OK
        )


# ──────────────────────────────────────────────────────────────────────────────
# Change Password
# ──────────────────────────────────────────────────────────────────────────────


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/

    Body: { old_password, new_password, new_password_confirm }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        new_password_confirm = request.data.get("new_password_confirm")

        if not all([old_password, new_password, new_password_confirm]):
            return Response(
                {"error": "All fields are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if new_password != new_password_confirm:
            return Response(
                {"error": "New passwords do not match."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not request.user.check_password(old_password):
            return Response(
                {"error": "Old password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.save()

        return Response(
            {"message": "Password changed successfully."}, status=status.HTTP_200_OK
        )


# ──────────────────────────────────────────────────────────────────────────────
# Google OAuth
# ──────────────────────────────────────────────────────────────────────────────


class GoogleAuthView(APIView):
    """
    POST /api/auth/google/

    Body: { token: '<google_id_token>', role: 'customer' }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user = User.objects.filter(
            models.Q(email=data["email"]) | models.Q(google_id=data["google_id"])
        ).first()

        is_new_user = False

        if user:
            if not user.google_id:
                user.google_id = data["google_id"]
            if not user.profile_picture:
                user.profile_picture = data["profile_picture"]
            if not user.is_email_verified and data["email_verified"]:
                user.is_email_verified = True
            user.save()
        else:
            is_new_user = True
            user = User.objects.create(
                email=data["email"],
                google_id=data["google_id"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                profile_picture=data["profile_picture"],
                is_email_verified=data["email_verified"],
                role=data.get("role", User.Role.CUSTOMER),
                is_active=True,
            )
            user.verification_status = (
                User.VerificationStatus.PENDING
                if user.requires_verification()
                else User.VerificationStatus.NOT_REQUIRED
            )
            user.save()

        return Response(
            {
                "message": (
                    "Account created successfully."
                    if is_new_user
                    else "Login successful."
                ),
                "tokens": _issue_tokens(user),
                "user": UserSerializer(user).data,
                "is_new_user": is_new_user,
            },
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Password Reset
# ──────────────────────────────────────────────────────────────────────────────


class ForgotPasswordView(APIView):
    """
    POST /api/auth/forgot-password/

    Body: { email }
    Sends a password-reset OTP to the email.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        success, message = OTPService.create_otp(
            email=email,
            purpose=EmailOTP.Purpose.PASSWORD_RESET,
        )

        if success:
            return Response(
                {
                    "message": "Password reset code has been sent to your email.",
                    "email": email,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": "Failed to send reset code. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ResetPasswordView(APIView):
    """
    POST /api/auth/reset-password/

    Body: { email, otp, new_password, new_password_confirm }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        new_password = serializer.validated_data["new_password"]
        otp_obj = serializer.validated_data["otp_obj"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        otp_obj.is_verified = True
        otp_obj.save()

        user.set_password(new_password)
        user.save()

        return Response(
            {
                "message": (
                    "Password has been reset successfully. "
                    "You can now log in with your new password."
                )
            },
            status=status.HTTP_200_OK,
        )
