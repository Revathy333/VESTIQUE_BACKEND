"""
Custom permissions for the admin panel.
"""

from rest_framework.permissions import BasePermission


class IsAdminStaff(BasePermission):
    """
    Allows access to any user with is_staff=True OR is_superuser=True.
    Used for all admin panel endpoints.
    """
    message = "Access denied. Administrator privileges required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


class IsSuperUser(BasePermission):
    """
    Allows access ONLY to is_superuser=True users.
    Used for: creating/deleting admin accounts.
    """
    message = "Access denied. Superuser privileges required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )