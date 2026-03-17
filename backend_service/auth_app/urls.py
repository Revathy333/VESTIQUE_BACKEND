

"""
URL Configuration for Authentication API.
"""

from django.urls import path

from .views import (
    ChangePasswordView,
    ForgotPasswordView,
    GoogleAuthView,
    LoginView,
    LogoutView,
    RefreshTokenView,
    RegisterView,
    ResendOTPView,
    ResetPasswordView,
    TwoFAConfirmSetupView,
    TwoFADisableView,
    TwoFASetupView,
    UserProfileView,
    Verify2FAView,
    VerifyEmailView,
)

app_name = "auth_app"

urlpatterns = [
    # ── Registration & Email Verification ─────────────────────────────────────
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    # ── Login (2 steps when 2FA is active) ────────────────────────────────────
    path("login/", LoginView.as_view(), name="login"),
    path("verify-2fa/", Verify2FAView.as_view(), name="verify-2fa"),  # step 2
    # ── Logout & Token Refresh ────────────────────────────────────────────────
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    # ── User Profile & Password ───────────────────────────────────────────────
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    # ── 2FA Management (requires login) ──────────────────────────────────────
    path("2fa/setup/", TwoFASetupView.as_view(), name="2fa-setup"),
    path("2fa/confirm/", TwoFAConfirmSetupView.as_view(), name="2fa-confirm"),
    path("2fa/disable/", TwoFADisableView.as_view(), name="2fa-disable"),
    # ── Google OAuth ──────────────────────────────────────────────────────────
    path("google/", GoogleAuthView.as_view(), name="google-auth"),
]
