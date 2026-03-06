"""
Admin Panel API Views.
All endpoints require is_staff=True minimum.
Delete admin endpoint requires is_superuser=True.

URL prefix: /api/admin/
"""

import logging

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.models import VerificationDocument
from .permissions import IsAdminStaff, IsSuperUser
from auth_app.tasks import send_approval_email

User = get_user_model()
logger = logging.getLogger(__name__)


def _issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


# ──────────────────────────────────────────────────────────────────────────────
# Admin Login
# ──────────────────────────────────────────────────────────────────────────────


class AdminLoginView(APIView):
    """
    POST /api/admin/login/

    Admin-ONLY login. Regular users (customers/designers/tailors) are REJECTED.
    Body: { email, password }
    Returns: { tokens, admin }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        password = request.data.get("password", "")

        if not email or not password:
            return Response(
                {"error": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Only staff/superusers allowed
        if not (user.is_staff or user.is_superuser):
            return Response(
                {"error": "Access denied. This login is for administrators only."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.is_active:
            return Response(
                {"error": "This admin account has been deactivated."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        return Response(
            {
                "message": "Admin login successful.",
                "tokens": _issue_tokens(user),
                "admin": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_superuser": user.is_superuser,
                    "is_staff": user.is_staff,
                    "last_login": user.last_login,
                },
            },
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Dashboard Stats
# ──────────────────────────────────────────────────────────────────────────────


class AdminStatsView(APIView):
    """GET /api/admin/stats/ — Dashboard statistics"""

    permission_classes = [IsAdminStaff]

    def get(self, request):
        total_users = User.objects.filter(is_staff=False).count()
        role_counts = {
            role.value: User.objects.filter(role=role, is_staff=False).count()
            for role in User.Role
        }
        pending_verifications = User.objects.filter(
            verification_status=User.VerificationStatus.PENDING
        ).count()
        active_users = User.objects.filter(is_active=True, is_staff=False).count()
        inactive_users = User.objects.filter(is_active=False, is_staff=False).count()
        admin_count = User.objects.filter(is_staff=True).count()

        return Response(
            {
                "total_users": total_users,
                "role_counts": role_counts,
                "pending_verifications": pending_verifications,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "admin_count": admin_count,
            },
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Users Management
# ──────────────────────────────────────────────────────────────────────────────


class AdminUsersListView(APIView):
    """
    GET /api/admin/users/
    Query params: role, status (active|inactive), verification, search
    """

    permission_classes = [IsAdminStaff]

    def get(self, request):
        queryset = User.objects.filter(is_staff=False)

        if role := request.query_params.get("role"):
            queryset = queryset.filter(role=role)

        user_status = request.query_params.get("status")
        if user_status == "active":
            queryset = queryset.filter(is_active=True)
        elif user_status == "inactive":
            queryset = queryset.filter(is_active=False)

        if verification := request.query_params.get("verification"):
            queryset = queryset.filter(verification_status=verification)

        if search := request.query_params.get("search", "").strip():
            queryset = queryset.filter(
                models.Q(email__icontains=search)
                | models.Q(first_name__icontains=search)
                | models.Q(last_name__icontains=search)
                | models.Q(phone__icontains=search)
            )

        users = queryset.order_by("-date_joined")
        data = [
            {
                "id": u.id,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "phone": u.phone,
                "role": u.role,
                "is_active": u.is_active,
                "is_email_verified": u.is_email_verified,
                "verification_status": u.verification_status,
                "two_fa_method": u.two_fa_method,
                "date_joined": u.date_joined,
                "last_login": u.last_login,
            }
            for u in users
        ]
        return Response({"users": data, "count": len(data)}, status=status.HTTP_200_OK)


class AdminUserDetailView(APIView):
    """
    GET    /api/admin/users/<user_id>/  → Full user details + documents
    PATCH  /api/admin/users/<user_id>/  → Update allowed fields
    DELETE /api/admin/users/<user_id>/  → Permanently delete user (any admin)
    """

    permission_classes = [IsAdminStaff]

    def _get_user(self, user_id):
        try:
            return User.objects.get(id=user_id, is_staff=False)
        except User.DoesNotExist:
            return None

    def get(self, request, user_id):
        user = self._get_user(user_id)
        if not user:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        docs = VerificationDocument.objects.filter(user=user)
        documents = [
            {
                "id": doc.id,
                "document_type": doc.document_type,
                # "file_url": request.build_absolute_uri(doc.file.url) if doc.file else None,
                # NEW
                "file_url": f"http://localhost{doc.file.url}" if doc.file else None,
                "uploaded_at": doc.uploaded_at,
            }
            for doc in docs
        ]

        return Response(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone": user.phone,
                    "role": user.role,
                    "business_name": user.business_name,
                    "experience": user.experience,
                    "specialization": user.specialization,
                    "is_active": user.is_active,
                    "is_email_verified": user.is_email_verified,
                    "is_phone_verified": user.is_phone_verified,
                    "verification_status": user.verification_status,
                    "verification_notes": user.verification_notes,
                    "verified_at": user.verified_at,
                    "two_fa_method": user.two_fa_method,
                    "profile_picture": user.profile_picture,
                    "date_joined": user.date_joined,
                    "last_login": user.last_login,
                    "documents": documents,
                }
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, user_id):
        """Permanently delete a user. Any admin can delete regular users."""
        user = self._get_user(user_id)
        if not user:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        email = user.email
        user.delete()
        logger.info(f"Admin {request.user.email} deleted user {email}")

        return Response(
            {"message": f"User {email} has been permanently deleted."},
            status=status.HTTP_200_OK,
        )


class AdminToggleUserStatusView(APIView):
    """
    POST /api/admin/users/<user_id>/toggle-status/
    Body: { is_active: bool }  — Block or unblock a user
    """

    permission_classes = [IsAdminStaff]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, is_staff=False)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        is_active = request.data.get("is_active")
        if is_active is None:
            return Response(
                {"error": "is_active field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = bool(is_active)
        user.save(update_fields=["is_active"])
        action = "unblocked" if user.is_active else "blocked"

        return Response(
            {
                "message": f"User has been {action} successfully.",
                "user_id": user.id,
                "is_active": user.is_active,
            },
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Verification Management
# ──────────────────────────────────────────────────────────────────────────────


class AdminVerificationView(APIView):
    """
    POST /api/admin/users/<user_id>/verify/
    Body: { action: 'approve'|'reject', notes: '...' }
    """

    permission_classes = [IsAdminStaff]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, is_staff=False)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if not user.requires_verification():
            return Response(
                {"error": "This user role does not require verification."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        action = request.data.get("action")
        notes = request.data.get("notes", "")

        if action == "approve":
            user.verification_status = User.VerificationStatus.APPROVED
            user.verified_at = timezone.now()
            user.verification_notes = notes
            user.save(update_fields=["verification_status", "verified_at", "verification_notes"])

            send_approval_email.delay(user.email, user.first_name, user.role)
            return Response(
                {"message": "User verification approved successfully."},
                status=status.HTTP_200_OK,
            )

        elif action == "reject":
            user.verification_status = User.VerificationStatus.REJECTED
            user.verified_at = None
            user.verification_notes = notes
            user.save(update_fields=["verification_status", "verified_at", "verification_notes"])
            return Response(
                {"message": "User verification rejected."},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "action must be 'approve' or 'reject'."},
            status=status.HTTP_400_BAD_REQUEST,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Admin Account Management  (Superuser only)
# ──────────────────────────────────────────────────────────────────────────────


class AdminListView(APIView):
    """GET /api/admin/admins/  — List all admin (staff) users"""

    permission_classes = [IsAdminStaff]

    def get(self, request):
        admins = User.objects.filter(is_staff=True).order_by("-date_joined")
        data = [
            {
                "id": a.id,
                "email": a.email,
                "first_name": a.first_name,
                "last_name": a.last_name,
                "is_superuser": a.is_superuser,
                "is_active": a.is_active,
                "date_joined": a.date_joined,
                "last_login": a.last_login,
            }
            for a in admins
        ]
        return Response({"admins": data, "count": len(data)}, status=status.HTTP_200_OK)


class AdminCreateAdminView(APIView):
    """
    POST /api/admin/admins/create/
    SUPERUSER ONLY — creates a new staff/admin account.
    Body: { email, first_name, last_name, password, is_superuser }
    """

    permission_classes = [IsSuperUser]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        first_name = request.data.get("first_name", "").strip()
        last_name = request.data.get("last_name", "").strip()
        password = request.data.get("password", "")
        make_superuser = bool(request.data.get("is_superuser", False))

        if not all([email, first_name, last_name, password]):
            return Response(
                {"error": "email, first_name, last_name, and password are all required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "An account with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(password) < 8:
            return Response(
                {"error": "Password must be at least 8 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        admin_user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
            is_superuser=make_superuser,
            is_active=True,
            is_email_verified=True,
        )

        return Response(
            {
                "message": f"Admin account created for {email}.",
                "admin": {
                    "id": admin_user.id,
                    "email": admin_user.email,
                    "first_name": admin_user.first_name,
                    "last_name": admin_user.last_name,
                    "is_superuser": admin_user.is_superuser,
                    "date_joined": admin_user.date_joined,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class AdminDeleteAdminView(APIView):
    """
    DELETE /api/admin/admins/<admin_id>/
    SUPERUSER ONLY — permanently deletes an admin account.
    A superuser cannot delete their own account.
    """

    permission_classes = [IsSuperUser]

    def delete(self, request, admin_id):
        # Cannot delete yourself
        if request.user.id == admin_id:
            return Response(
                {"error": "You cannot delete your own admin account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            admin = User.objects.get(id=admin_id, is_staff=True)
        except User.DoesNotExist:
            return Response(
                {"error": "Admin account not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        email = admin.email
        admin.delete()
        logger.info(f"Superuser {request.user.email} deleted admin account {email}")

        return Response(
            {"message": f"Admin account {email} has been permanently deleted."},
            status=status.HTTP_200_OK,
        )


















































