"""
Serializers for Authentication API.
Handles data validation and serialization for all auth flows.
"""

import phonenumbers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import SMSOTP, EmailOTP, User, VerificationDocument

# ──────────────────────────────────────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────────────────────────────────────


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Handles user registration including document uploads for designers/tailors.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    # Document fields — required only for designers / tailors
    certificate = serializers.FileField(write_only=True, required=False)
    id_proof = serializers.FileField(write_only=True, required=False)
    portfolio_images = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "business_name",
            "experience",
            "specialization",
            "password",
            "password_confirm",
            "certificate",
            "id_proof",
            "portfolio_images",
        ]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
            "email": {"required": True},
        }

    def validate_email(self, value):
        """Ensure email is unique and normalised."""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_phone(self, value):
        """
        Validate phone number and normalise to E.164 format (+919876543210).
        Phone is optional at registration, but if provided it must be valid.
        Without a valid phone the user won't be able to use SMS 2FA later.
        """
        if not value:
            return value
        try:
            parsed = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError(
                    "Enter a valid phone number with country code, e.g. +919876543210"
                )
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError(
                "Enter a valid phone number with country code, e.g. +919876543210"
            )

    def validate(self, attrs):
        """Validate passwords match and documents provided for designers/tailors."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )

        role = attrs.get("role", User.Role.CUSTOMER)
        if role in [User.Role.DESIGNER, User.Role.TAILOR]:
            required = {
                "business_name": "Business/Professional name is required.",
                "experience": "Experience is required.",
                "specialization": "Specialization is required.",
                "certificate": "Certificate/Diploma is required for verification.",
                "id_proof": "ID Proof is required for verification.",
            }
            for field, msg in required.items():
                if not attrs.get(field):
                    raise serializers.ValidationError({field: msg})

        return attrs

    def create(self, validated_data):
        """Create user and save verification documents."""
        validated_data.pop("password_confirm")
        certificate = validated_data.pop("certificate", None)
        id_proof = validated_data.pop("id_proof", None)
        portfolio_images = validated_data.pop("portfolio_images", [])

        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            phone=validated_data.get("phone", ""),
            role=validated_data.get("role", User.Role.CUSTOMER),
            business_name=validated_data.get("business_name", ""),
            experience=validated_data.get("experience", ""),
            specialization=validated_data.get("specialization", ""),
        )

        if user.requires_verification():
            user.verification_status = User.VerificationStatus.PENDING
        else:
            user.verification_status = User.VerificationStatus.NOT_REQUIRED
        user.save()

        if certificate:
            VerificationDocument.objects.create(
                user=user,
                document_type=VerificationDocument.DocumentType.CERTIFICATE,
                file=certificate,
            )
        if id_proof:
            VerificationDocument.objects.create(
                user=user,
                document_type=VerificationDocument.DocumentType.ID_PROOF,
                file=id_proof,
            )
        for image in portfolio_images:
            VerificationDocument.objects.create(
                user=user,
                document_type=VerificationDocument.DocumentType.PORTFOLIO,
                file=image,
            )

        return user


# ──────────────────────────────────────────────────────────────────────────────
# Email OTP Verification (registration + password reset)
# ──────────────────────────────────────────────────────────────────────────────


class EmailOTPVerificationSerializer(serializers.Serializer):
    """
    Validates email OTP for registration verification and password reset.
    No longer handles login 2FA — that is handled by Verify2FASerializer.
    """

    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, max_length=6, min_length=6)
    purpose = serializers.ChoiceField(
        choices=EmailOTP.Purpose.choices,
        default=EmailOTP.Purpose.EMAIL_VERIFICATION,
    )

    def validate_email(self, value):
        if not User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value.lower()

    def validate(self, attrs):
        email = attrs["email"]
        otp = attrs["otp"]
        purpose = attrs["purpose"]

        otp_obj = (
            EmailOTP.objects.filter(
                email=email,
                otp=otp,
                purpose=purpose,
                is_verified=False,
            )
            .order_by("-created_at")
            .first()
        )

        if not otp_obj:
            raise serializers.ValidationError({"otp": "Invalid OTP code."})
        if not otp_obj.is_valid():
            raise serializers.ValidationError(
                {"otp": "OTP has expired. Please request a new one."}
            )

        attrs["otp_obj"] = otp_obj
        return attrs


class ResendOTPSerializer(serializers.Serializer):
    """Resend an email OTP."""

    email = serializers.EmailField(required=True)
    purpose = serializers.ChoiceField(
        choices=EmailOTP.Purpose.choices,
        default=EmailOTP.Purpose.EMAIL_VERIFICATION,
    )

    def validate_email(self, value):
        if not User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value.lower()


# ──────────────────────────────────────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────────────────────────────────────


class UserLoginSerializer(serializers.Serializer):
    """
    Validates credentials at login step 1.
    If 2FA is enabled the view will NOT issue tokens yet.
    """

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        email = attrs["email"].lower()
        password = attrs["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Invalid email or password."})

        if not user.is_email_verified:
            raise serializers.ValidationError(
                {"email": "Please verify your email before logging in."}
            )

        if user.requires_verification():
            if user.verification_status == User.VerificationStatus.PENDING:
                raise serializers.ValidationError(
                    {
                        "email": "Your account is pending verification. We'll notify you within 24-48 hours."
                    }
                )
            elif user.verification_status == User.VerificationStatus.REJECTED:
                raise serializers.ValidationError(
                    {
                        "email": (
                            f"Your account verification was rejected. "
                            f"Reason: {user.verification_notes or 'Please contact support.'}"
                        )
                    }
                )

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError(
                {"password": "Invalid email or password."}
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {"email": "This account has been deactivated."}
            )

        attrs["user"] = user
        return attrs


# ──────────────────────────────────────────────────────────────────────────────
# 2FA Verification at Login (step 2)
# ──────────────────────────────────────────────────────────────────────────────


class Verify2FASerializer(serializers.Serializer):
    """
    Step-2 login serializer.
    Validates the 2FA code (either TOTP digit or SMS OTP) and returns the user.

    Fields:
        email  : user's email (to look them up)
        code   : 6-digit code from authenticator app or SMS
    """

    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, max_length=6, min_length=6)

    def validate_email(self, value):
        if not User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("User not found.")
        return value.lower()

    def validate(self, attrs):
        from .totp_service import TOTPService

        email = attrs["email"]
        code = attrs["code"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User not found."})

        if not user.is_2fa_enabled:
            raise serializers.ValidationError(
                {"code": "This account does not have 2FA enabled."}
            )

        # ── TOTP path ─────────────────────────────────────────────────────────
        if user.two_fa_method == User.TwoFAMethod.TOTP:
            if not TOTPService.verify_totp(user.totp_secret, code):
                raise serializers.ValidationError(
                    {"code": "Invalid authenticator code. Please try again."}
                )

        # ── SMS path ──────────────────────────────────────────────────────────
        elif user.two_fa_method == User.TwoFAMethod.SMS:
            from .services import SMSOTPService

            success, message = SMSOTPService.verify_otp(
                phone=user.phone,
                otp_code=code,
                purpose=SMSOTP.Purpose.LOGIN_2FA,
            )
            if not success:
                raise serializers.ValidationError({"code": message})

        attrs["user"] = user
        return attrs


# ──────────────────────────────────────────────────────────────────────────────
# 2FA Setup
# ──────────────────────────────────────────────────────────────────────────────


class TwoFASetupSerializer(serializers.Serializer):
    """
    Initiate 2FA setup. User chooses 'totp' or 'sms'.
    For SMS, a phone number must be on the account (or provided here).
    """

    method = serializers.ChoiceField(
        choices=[(User.TwoFAMethod.TOTP, "TOTP"), (User.TwoFAMethod.SMS, "SMS")]
    )
    # Only needed when method=sms and user wants to update/add phone
    phone = serializers.CharField(required=False, allow_blank=True)

    def validate_phone(self, value):
        if not value:
            return value
        try:
            parsed = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError(
                    "Enter a valid phone number with country code, e.g. +919876543210"
                )
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError(
                "Enter a valid phone number with country code, e.g. +919876543210"
            )

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None

        if attrs["method"] == User.TwoFAMethod.SMS:
            phone = attrs.get("phone") or (user.phone if user else None)
            if not phone:
                raise serializers.ValidationError(
                    {
                        "phone": (
                            "A phone number is required for SMS 2FA. "
                            "Please provide your phone number."
                        )
                    }
                )
        return attrs


class TwoFAConfirmSetupSerializer(serializers.Serializer):
    """
    Confirm 2FA setup by verifying the first code from the app/SMS.
    This activates 2FA on the account.
    """

    code = serializers.CharField(required=True, max_length=6, min_length=6)


class TwoFADisableSerializer(serializers.Serializer):
    """
    Disable 2FA. Requires current password for security.
    """

    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )


# ──────────────────────────────────────────────────────────────────────────────
# User Profile
# ──────────────────────────────────────────────────────────────────────────────


class UserSerializer(serializers.ModelSerializer):
    """Read-only user profile serializer."""

    full_name = serializers.CharField(source="get_full_name", read_only=True)
    is_verified = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "is_phone_verified",
            "role",
            "business_name",
            "experience",
            "specialization",
            "verification_status",
            "is_verified",
            "is_email_verified",
            "two_fa_method",
            "is_2fa_enabled",
            "profile_picture",
            "date_joined",
            "last_login",
        ]
        read_only_fields = [
            "id",
            "email",
            "verification_status",
            "is_email_verified",
            "is_phone_verified",
            "two_fa_method",
            "date_joined",
            "last_login",
        ]

    def get_is_verified(self, obj):
        return obj.is_verified()


# ──────────────────────────────────────────────────────────────────────────────
# Logout & Token
# ──────────────────────────────────────────────────────────────────────────────


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)


# ──────────────────────────────────────────────────────────────────────────────
# Google OAuth
# ──────────────────────────────────────────────────────────────────────────────


class GoogleAuthSerializer(serializers.Serializer):
    """Validates Google ID token and extracts user info."""

    token = serializers.CharField(required=True, write_only=True)
    role = serializers.ChoiceField(
        choices=User.Role.choices, required=False, default=User.Role.CUSTOMER
    )

    def validate_token(self, value):
        from django.conf import settings
        from google.auth.transport import requests
        from google.oauth2 import id_token

        try:
            idinfo = id_token.verify_oauth2_token(
                value, requests.Request(), settings.GOOGLE_CLIENT_ID
            )
            return idinfo
        except ValueError as e:
            raise serializers.ValidationError(f"Invalid Google token: {e}")

    def validate(self, attrs):
        idinfo = attrs["token"]
        attrs["email"] = idinfo.get("email")
        attrs["google_id"] = idinfo.get("sub")
        attrs["first_name"] = idinfo.get("given_name", "")
        attrs["last_name"] = idinfo.get("family_name", "")
        attrs["profile_picture"] = idinfo.get("picture", "")
        attrs["email_verified"] = idinfo.get("email_verified", False)
        return attrs


# ──────────────────────────────────────────────────────────────────────────────
# Password Reset
# ──────────────────────────────────────────────────────────────────────────────


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        email = value.lower()
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                "No account found with this email address."
            )
        return email


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, max_length=6, min_length=6)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )

    def validate_email(self, value):
        email = value.lower()
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return email

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password": "Passwords do not match."}
            )

        otp_obj = (
            EmailOTP.objects.filter(
                email=attrs["email"],
                otp=attrs["otp"],
                purpose=EmailOTP.Purpose.PASSWORD_RESET,
                is_verified=False,
            )
            .order_by("-created_at")
            .first()
        )

        if not otp_obj:
            raise serializers.ValidationError({"otp": "Invalid OTP code."})
        if not otp_obj.is_valid():
            raise serializers.ValidationError(
                {"otp": "OTP has expired. Please request a new one."}
            )

        attrs["otp_obj"] = otp_obj
        return attrs
