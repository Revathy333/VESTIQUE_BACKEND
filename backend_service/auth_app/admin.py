# # Register your models here.
# """
# Django Admin Configuration for Authentication Models
# """

# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.utils.translation import gettext_lazy as _
# from .models import User, EmailOTP, RefreshTokenBlacklist


# @admin.register(User)
# class UserAdmin(BaseUserAdmin):
#     """
#     Custom User Admin Panel
#     """
#     list_display = [
#         'email',
#         'first_name',
#         'last_name',
#         'role',
#         'is_email_verified',
#         'is_active',
#         'is_staff',
#         'date_joined'
#     ]
#     list_filter = [
#         'role',
#         'is_email_verified',
#         'is_2fa_enabled',
#         'is_active',
#         'is_staff',
#         'date_joined'
#     ]
#     search_fields = ['email', 'first_name', 'last_name', 'phone']
#     ordering = ['-date_joined']

#     fieldsets = (
#         (None, {
#             'fields': ('email', 'password')
#         }),
#         (_('Personal Info'), {
#             'fields': ('first_name', 'last_name', 'phone', 'profile_picture')
#         }),
#         (_('Role & Permissions'), {
#             'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
#         }),
#         (_('Verification & Security'), {
#             'fields': ('is_email_verified', 'is_2fa_enabled', 'otp_secret', 'google_id')
#         }),
#         (_('Important Dates'), {
#             'fields': ('last_login', 'date_joined')
#         }),
#     )

#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': (
#                 'email',
#                 'first_name',
#                 'last_name',
#                 'role',
#                 'password1',
#                 'password2',
#                 'is_staff',
#                 'is_active'
#             ),
#         }),
#     )

#     readonly_fields = ['date_joined', 'last_login']


# @admin.register(EmailOTP)
# class EmailOTPAdmin(admin.ModelAdmin):
#     """
#     Email OTP Admin Panel
#     """
#     list_display = [
#         'email',
#         'otp',
#         'purpose',
#         'is_verified',
#         'created_at',
#         'expires_at',
#         'is_valid_display'
#     ]
#     list_filter = ['purpose', 'is_verified', 'created_at']
#     search_fields = ['email', 'otp']
#     ordering = ['-created_at']
#     readonly_fields = ['created_at', 'expires_at']

#     def is_valid_display(self, obj):
#         """Display if OTP is currently valid"""
#         return obj.is_valid()
#     is_valid_display.boolean = True
#     is_valid_display.short_description = 'Currently Valid'


# @admin.register(RefreshTokenBlacklist)
# class RefreshTokenBlacklistAdmin(admin.ModelAdmin):
#     """
#     Refresh Token Blacklist Admin Panel
#     """
#     list_display = ['user', 'blacklisted_at', 'token_preview']
#     list_filter = ['blacklisted_at']
#     search_fields = ['user__email', 'token']
#     ordering = ['-blacklisted_at']
#     readonly_fields = ['blacklisted_at']

#     def token_preview(self, obj):
#         """Show first 20 characters of token"""
#         return f"{obj.token[:20]}..." if len(obj.token) > 20 else obj.token
#     token_preview.short_description = 'Token Preview'

"""
Django Admin Configuration for Authentication Models
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import EmailOTP, RefreshTokenBlacklist, User, VerificationDocument


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User Admin Panel with verification management
    """

    list_display = [
        "email",
        "first_name",
        "last_name",
        "role",
        "verification_status_badge",
        "is_email_verified",
        "is_active",
        "date_joined",
    ]
    list_filter = [
        "role",
        "verification_status",
        "is_email_verified",
        "two_fa_method",
        "is_active",
        "is_staff",
        "date_joined",
    ]
    search_fields = ["email", "first_name", "last_name", "phone", "business_name"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal Info"),
            {"fields": ("first_name", "last_name", "phone", "profile_picture")},
        ),
        (
            _("Professional Info"),
            {
                "fields": ("business_name", "experience", "specialization"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Role & Permissions"),
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            _("Verification"),
            {
                "fields": ("verification_status", "verification_notes", "verified_at"),
                "classes": ("wide",),
            },
        ),
        (
            _("Security"),
            {
                "fields": (
                    "is_email_verified",
                    "is_phone_verified",
                    "two_fa_method",
                    "totp_secret",
                    "google_id",
                )
            },
        ),
        (_("Important Dates"), {"fields": ("last_login", "date_joined", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )

    readonly_fields = ["date_joined", "last_login", "updated_at", "verified_at"]

    def verification_status_badge(self, obj):
        """Display verification status with color badge"""
        colors = {
            "pending": "#fbbf24",
            "approved": "#10b981",
            "rejected": "#ef4444",
            "not_required": "#6b7280",
        }
        color = colors.get(obj.verification_status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_verification_status_display(),
        )

    verification_status_badge.short_description = "Verification Status"

    actions = ["approve_verification", "reject_verification"]

    def approve_verification(self, request, queryset):
        """Approve selected users"""
        from django.utils import timezone

        updated = queryset.filter(
            verification_status=User.VerificationStatus.PENDING
        ).update(
            verification_status=User.VerificationStatus.APPROVED,
            verified_at=timezone.now(),
        )
        self.message_user(request, f"{updated} user(s) approved successfully.")

    approve_verification.short_description = "Approve selected users"

    def reject_verification(self, request, queryset):
        """Reject selected users"""
        updated = queryset.filter(
            verification_status=User.VerificationStatus.PENDING
        ).update(verification_status=User.VerificationStatus.REJECTED)
        self.message_user(request, f"{updated} user(s) rejected.")

    reject_verification.short_description = "Reject selected users"


@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    """
    Verification Document Admin Panel
    """

    list_display = ["user_email", "document_type", "uploaded_at", "view_document"]
    list_filter = ["document_type", "uploaded_at"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    ordering = ["-uploaded_at"]
    readonly_fields = ["uploaded_at", "document_preview"]

    fieldsets = (
        (None, {"fields": ("user", "document_type", "file")}),
        (
            _("Document Preview"),
            {"fields": ("document_preview",), "classes": ("wide",)},
        ),
        (_("Metadata"), {"fields": ("uploaded_at",)}),
    )

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User Email"
    user_email.admin_order_field = "user__email"

    def view_document(self, obj):
        """Link to view/download document"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank" style="color: #0066cc;">View Document</a>',
                obj.file.url,
            )
        return "-"

    view_document.short_description = "Document"

    def document_preview(self, obj):
        """Show image preview for portfolio images"""
        if obj.document_type == "portfolio" and obj.file:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 400px;" />',
                obj.file.url,
            )
        elif obj.file:
            return format_html(
                '<a href="{}" target="_blank">View Document</a>', obj.file.url
            )
        return "-"

    document_preview.short_description = "Preview"


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    """
    Email OTP Admin Panel
    """

    list_display = [
        "email",
        "otp",
        "purpose",
        "is_verified",
        "created_at",
        "expires_at",
        "is_valid_display",
    ]
    list_filter = ["purpose", "is_verified", "created_at"]
    search_fields = ["email", "otp"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "expires_at"]

    def is_valid_display(self, obj):
        """Display if OTP is currently valid"""
        return obj.is_valid()

    is_valid_display.boolean = True
    is_valid_display.short_description = "Currently Valid"


@admin.register(RefreshTokenBlacklist)
class RefreshTokenBlacklistAdmin(admin.ModelAdmin):
    """
    Refresh Token Blacklist Admin Panel
    """

    list_display = ["user", "blacklisted_at", "token_preview"]
    list_filter = ["blacklisted_at"]
    search_fields = ["user__email", "token"]
    ordering = ["-blacklisted_at"]
    readonly_fields = ["blacklisted_at"]

    def token_preview(self, obj):
        """Show first 20 characters of token"""
        return f"{obj.token[:20]}..." if len(obj.token) > 20 else obj.token

    token_preview.short_description = "Token Preview"
