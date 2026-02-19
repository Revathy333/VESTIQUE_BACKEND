# """
# Authentication models for Virtual Boutique Platform.
# """

# from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
# from django.db import models
# from django.utils import timezone
# from django.utils.translation import gettext_lazy as _
# from datetime import timedelta
# import random

# from .managers import UserManager


# class User(AbstractBaseUser, PermissionsMixin):
#     """
#     Custom User model with email-based authentication.
#     Supports multiple roles: customer, designer, boutique owner, tailor.
#     """

#     class Role(models.TextChoices):
#         CUSTOMER = 'customer', _('Customer')
#         DESIGNER = 'designer', _('Designer')
#         BOUTIQUE = 'boutique', _('Boutique Owner')
#         TAILOR = 'tailor', _('Tailor')

#     class VerificationStatus(models.TextChoices):
#         PENDING = 'pending', _('Pending Verification')
#         APPROVED = 'approved', _('Approved')
#         REJECTED = 'rejected', _('Rejected')
#         NOT_REQUIRED = 'not_required', _('Not Required')

#     # Core Fields
#     email = models.EmailField(_('email address'), unique=True, db_index=True)
#     first_name = models.CharField(_('first name'), max_length=150, blank=True)
#     last_name = models.CharField(_('last name'), max_length=150, blank=True)
#     phone = models.CharField(_('phone number'), max_length=15, blank=True, null=True)

#     # Role
#     role = models.CharField(
#         _('role'),
#         max_length=20,
#         choices=Role.choices,
#         default=Role.CUSTOMER,
#         db_index=True
#     )

#      # Professional Details (for designers/tailors)
#     business_name = models.CharField(_('business/professional name'), max_length=200, blank=True)
#     experience = models.CharField(_('years of experience'), max_length=20, blank=True)
#     specialization = models.CharField(_('specialization'), max_length=200, blank=True)

#     # Verification Status
#     verification_status = models.CharField(
#         _('verification status'),
#         max_length=20,
#         choices=VerificationStatus.choices,
#         default=VerificationStatus.NOT_REQUIRED
#     )
#     verification_notes = models.TextField(_('verification notes'), blank=True)
#     verified_at = models.DateTimeField(_('verified at'), null=True, blank=True)

#     # Django Required Fields
#     is_staff = models.BooleanField(_('staff status'), default=False)
#     is_active = models.BooleanField(_('active'), default=True)

#     # Verification & Security
#     is_email_verified = models.BooleanField(_('email verified'), default=False)
#     is_2fa_enabled = models.BooleanField(_('2FA enabled'), default=False)
#     otp_secret = models.CharField(_('OTP secret'), max_length=100, blank=True)

#     # OAuth Fields
#     google_id = models.CharField(_('Google ID'), max_length=255, blank=True, null=True, unique=True)
#     profile_picture = models.URLField(_('profile picture'), max_length=500, blank=True, null=True)

#     # Timestamps
#     date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
#     last_login = models.DateTimeField(_('last login'), blank=True, null=True)
#     updated_at = models.DateTimeField(_('updated at'), auto_now=True)

#     # Custom Manager
#     objects = UserManager()

#     # Authentication
#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['first_name', 'last_name']

#     class Meta:
#         verbose_name = _('user')
#         verbose_name_plural = _('users')
#         db_table = 'users'
#         ordering = ['-date_joined']

#     def __str__(self):
#         return self.email

#     def get_full_name(self):
#         full_name = f'{self.first_name} {self.last_name}'.strip()
#         return full_name or self.email

#     def get_short_name(self):
#         return self.first_name or self.email.split('@')[0]

#     def requires_verification(self):
#         """Check if user role requires document verification"""
#         return self.role in [self.Role.DESIGNER, self.Role.TAILOR]

#     def is_verified(self):
#         """Check if user is verified (or doesn't need verification)"""
#         if not self.requires_verification():
#             return True
#         return self.verification_status == self.VerificationStatus.APPROVED

# class VerificationDocument(models.Model):
#     """
#     Model to store verification documents for designers and tailors.
#     """

#     class DocumentType(models.TextChoices):
#         CERTIFICATE = 'certificate', _('Certificate/Diploma')
#         ID_PROOF = 'id_proof', _('ID Proof')
#         PORTFOLIO = 'portfolio', _('Portfolio Image')

#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_documents')
#     document_type = models.CharField(_('document type'), max_length=20, choices=DocumentType.choices)
#     file = models.FileField(_('document file'), upload_to='verification_documents/%Y/%m/')
#     uploaded_at = models.DateTimeField(_('uploaded at'), auto_now_add=True)

#     class Meta:
#         verbose_name = _('Verification Document')
#         verbose_name_plural = _('Verification Documents')
#         db_table = 'verification_documents'
#         ordering = ['-uploaded_at']

#     def __str__(self):
#         return f'{self.user.email} - {self.get_document_type_display()}'


# class EmailOTP(models.Model):
#     """
#     Model to store email OTP for verification.
#     """

#     class Purpose(models.TextChoices):
#         EMAIL_VERIFICATION = 'email_verification', _('Email Verification')
#         PASSWORD_RESET = 'password_reset', _('Password Reset')
#         LOGIN_2FA = 'login_2fa', _('Login 2FA')

#     email = models.EmailField(_('email address'), db_index=True)
#     otp = models.CharField(_('OTP code'), max_length=6)
#     purpose = models.CharField(
#         _('purpose'),
#         max_length=30,
#         choices=Purpose.choices,
#         default=Purpose.EMAIL_VERIFICATION
#     )

#     is_verified = models.BooleanField(_('verified'), default=False)
#     created_at = models.DateTimeField(_('created at'), auto_now_add=True)
#     expires_at = models.DateTimeField(_('expires at'))

#     class Meta:
#         verbose_name = _('Email OTP')
#         verbose_name_plural = _('Email OTPs')
#         db_table = 'email_otps'
#         ordering = ['-created_at']

#     def __str__(self):
#         return f'{self.email} - {self.purpose} - {self.otp}'

#     def is_valid(self):
#         """Check if OTP is still valid"""
#         return timezone.now() < self.expires_at and not self.is_verified

#     def save(self, *args, **kwargs):
#         """Set expiry time on creation (10 minutes)"""
#         if not self.expires_at:
#             self.expires_at = timezone.now() + timedelta(minutes=10)
#         super().save(*args, **kwargs)

#     @staticmethod
#     def generate_otp():
#         """Generate a random 6-digit OTP"""
#         return str(random.randint(100000, 999999))


# class RefreshTokenBlacklist(models.Model):
#     """
#     Store blacklisted refresh tokens for logout functionality.
#     """

#     token = models.CharField(_('refresh token'), max_length=500, unique=True, db_index=True)
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blacklisted_tokens')
#     blacklisted_at = models.DateTimeField(_('blacklisted at'), auto_now_add=True)

#     class Meta:
#         verbose_name = _('Blacklisted Token')
#         verbose_name_plural = _('Blacklisted Tokens')
#         db_table = 'refresh_token_blacklist'
#         ordering = ['-blacklisted_at']

#     def __str__(self):
#         return f'{self.user.email} - {self.blacklisted_at}'


"""
Authentication models for Virtual Boutique Platform.
"""

import random
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with email-based authentication.
    Supports multiple roles: customer, designer, boutique owner, tailor.
    """

    class Role(models.TextChoices):
        CUSTOMER = "customer", _("Customer")
        DESIGNER = "designer", _("Designer")
        BOUTIQUE = "boutique", _("Boutique Owner")
        TAILOR = "tailor", _("Tailor")

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", _("Pending Verification")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")
        NOT_REQUIRED = "not_required", _("Not Required")

    class TwoFAMethod(models.TextChoices):
        DISABLED = "disabled", _("Disabled")
        TOTP = "totp", _("Authenticator App (TOTP)")
        SMS = "sms", _("SMS OTP")

    # ── Core Fields ───────────────────────────────────────────────────────────
    email = models.EmailField(_("email address"), unique=True, db_index=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    phone = models.CharField(
        _("phone number"),
        max_length=20,  # E.164 format e.g. +919876543210
        blank=True,
        null=True,
    )

    # ── Role ──────────────────────────────────────────────────────────────────
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        db_index=True,
    )

    # ── Professional Details (designers / tailors) ────────────────────────────
    business_name = models.CharField(
        _("business/professional name"), max_length=200, blank=True
    )
    experience = models.CharField(_("years of experience"), max_length=20, blank=True)
    specialization = models.CharField(_("specialization"), max_length=200, blank=True)

    # ── Verification Status ───────────────────────────────────────────────────
    verification_status = models.CharField(
        _("verification status"),
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.NOT_REQUIRED,
    )
    verification_notes = models.TextField(_("verification notes"), blank=True)
    verified_at = models.DateTimeField(_("verified at"), null=True, blank=True)

    # ── Django Required Fields ────────────────────────────────────────────────
    is_staff = models.BooleanField(_("staff status"), default=False)
    is_active = models.BooleanField(_("active"), default=True)

    # ── Email Verification ────────────────────────────────────────────────────
    is_email_verified = models.BooleanField(_("email verified"), default=False)

    # ── Phone Verification ────────────────────────────────────────────────────
    is_phone_verified = models.BooleanField(_("phone verified"), default=False)

    # ── 2FA ───────────────────────────────────────────────────────────────────
    two_fa_method = models.CharField(
        _("2FA method"),
        max_length=10,
        choices=TwoFAMethod.choices,
        default=TwoFAMethod.DISABLED,
    )
    # TOTP secret (base32 string scanned into Google Authenticator etc.)
    totp_secret = models.CharField(_("TOTP secret"), max_length=64, blank=True)
    # Temporary secret during TOTP setup (not yet confirmed/activated)
    totp_secret_pending = models.CharField(
        _("pending TOTP secret"), max_length=64, blank=True
    )

    # ── OAuth Fields ──────────────────────────────────────────────────────────
    google_id = models.CharField(
        _("Google ID"), max_length=255, blank=True, null=True, unique=True
    )
    profile_picture = models.URLField(
        _("profile picture"), max_length=500, blank=True, null=True
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    last_login = models.DateTimeField(_("last login"), blank=True, null=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    # ── Manager & Auth config ─────────────────────────────────────────────────
    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        db_table = "users"
        ordering = ["-date_joined"]

    # ── String / helpers ──────────────────────────────────────────────────────
    def __str__(self):
        return self.email

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def get_short_name(self):
        return self.first_name or self.email.split("@")[0]

    # ── 2FA helpers ───────────────────────────────────────────────────────────
    @property
    def is_2fa_enabled(self):
        """True if any 2FA method is active."""
        return self.two_fa_method != self.TwoFAMethod.DISABLED

    # ── Verification helpers ──────────────────────────────────────────────────
    def requires_verification(self):
        """Check if user role requires document verification."""
        return self.role in [self.Role.DESIGNER, self.Role.TAILOR]

    def is_verified(self):
        """Check if user is verified (or doesn't need verification)."""
        if not self.requires_verification():
            return True
        return self.verification_status == self.VerificationStatus.APPROVED


class VerificationDocument(models.Model):
    """
    Stores verification documents for designers and tailors.
    """

    class DocumentType(models.TextChoices):
        CERTIFICATE = "certificate", _("Certificate/Diploma")
        ID_PROOF = "id_proof", _("ID Proof")
        PORTFOLIO = "portfolio", _("Portfolio Image")

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="verification_documents"
    )
    document_type = models.CharField(
        _("document type"), max_length=20, choices=DocumentType.choices
    )
    file = models.FileField(
        _("document file"), upload_to="verification_documents/%Y/%m/"
    )
    uploaded_at = models.DateTimeField(_("uploaded at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Verification Document")
        verbose_name_plural = _("Verification Documents")
        db_table = "verification_documents"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.user.email} - {self.get_document_type_display()}"


class EmailOTP(models.Model):
    """
    Stores email OTPs — used for registration verification and password reset ONLY.
    Login 2FA now uses SMS OTP or TOTP (see SMSOTP model).
    """

    class Purpose(models.TextChoices):
        EMAIL_VERIFICATION = "email_verification", _("Email Verification")
        PASSWORD_RESET = "password_reset", _("Password Reset")

    email = models.EmailField(_("email address"), db_index=True)
    otp = models.CharField(_("OTP code"), max_length=6)
    purpose = models.CharField(
        _("purpose"),
        max_length=30,
        choices=Purpose.choices,
        default=Purpose.EMAIL_VERIFICATION,
    )
    is_verified = models.BooleanField(_("verified"), default=False)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    expires_at = models.DateTimeField(_("expires at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Email OTP")
        verbose_name_plural = _("Email OTPs")
        db_table = "email_otps"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} - {self.purpose} - {self.otp}"

    def is_valid(self):
        """Check if OTP is still valid (not expired, not used)."""
        return timezone.now() < self.expires_at and not self.is_verified

    def save(self, *args, **kwargs):
        """Set expiry time on creation (10 minutes)."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    @staticmethod
    def generate_otp():
        """Generate a random 6-digit OTP."""
        return str(random.randint(100000, 999999))


class SMSOTP(models.Model):
    """
    Stores SMS OTPs — used for:
      - login_2fa  : second factor during login when user chose SMS 2FA
      - phone_verify: verifying phone number ownership during 2FA setup
    """

    class Purpose(models.TextChoices):
        LOGIN_2FA = "login_2fa", _("Login 2FA")
        PHONE_VERIFY = "phone_verify", _("Phone Verification")

    phone = models.CharField(_("phone number"), max_length=20, db_index=True)
    otp = models.CharField(_("OTP code"), max_length=6)
    purpose = models.CharField(
        _("purpose"),
        max_length=20,
        choices=Purpose.choices,
        default=Purpose.LOGIN_2FA,
    )
    is_verified = models.BooleanField(_("verified"), default=False)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    expires_at = models.DateTimeField(_("expires at"), null=True, blank=True)

    class Meta:
        verbose_name = _("SMS OTP")
        verbose_name_plural = _("SMS OTPs")
        db_table = "sms_otps"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.phone} - {self.purpose} - {self.otp}"

    def is_valid(self):
        """Check if OTP is still valid (5 minute window)."""
        return timezone.now() < self.expires_at and not self.is_verified

    def save(self, *args, **kwargs):
        """Set expiry time on creation (5 minutes)."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

    @staticmethod
    def generate_otp():
        """Generate a random 6-digit OTP."""
        return str(random.randint(100000, 999999))


class RefreshTokenBlacklist(models.Model):
    """
    Stores blacklisted refresh tokens for logout functionality.
    """

    token = models.CharField(
        _("refresh token"), max_length=500, unique=True, db_index=True
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blacklisted_tokens"
    )
    blacklisted_at = models.DateTimeField(_("blacklisted at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Blacklisted Token")
        verbose_name_plural = _("Blacklisted Tokens")
        db_table = "refresh_token_blacklist"
        ordering = ["-blacklisted_at"]

    def __str__(self):
        return f"{self.user.email} - {self.blacklisted_at}"
