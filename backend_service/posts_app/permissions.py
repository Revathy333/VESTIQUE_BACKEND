from rest_framework.permissions import BasePermission

CREATOR_ROLES = ['designer', 'tailor']

class IsDesignerOrTailor(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in CREATOR_ROLES
        )

class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated