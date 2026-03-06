

"""
URL Configuration for Admin Panel API.
All routes under: /api/admin/
"""

from django.urls import path

from .views import (
    AdminLoginView,
    AdminStatsView,
    AdminUsersListView,
    AdminUserDetailView,
    AdminToggleUserStatusView,
    AdminVerificationView,
    AdminListView,
    AdminCreateAdminView,
    AdminDeleteAdminView,
)

app_name = "admin_panel"

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────────
    path("login/", AdminLoginView.as_view(), name="admin-login"),

    # ── Dashboard ─────────────────────────────────────────────────────────────
    path("stats/", AdminStatsView.as_view(), name="admin-stats"),

    # ── User Management ───────────────────────────────────────────────────────
    path("users/", AdminUsersListView.as_view(), name="admin-users"),
    path("users/<int:user_id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("users/<int:user_id>/toggle-status/", AdminToggleUserStatusView.as_view(), name="admin-toggle-status"),
    path("users/<int:user_id>/verify/", AdminVerificationView.as_view(), name="admin-verify-user"),

    # ── Admin Account Management (superuser only) ─────────────────────────────
    path("admins/", AdminListView.as_view(), name="admin-list"),
    path("admins/create/", AdminCreateAdminView.as_view(), name="admin-create"),
    path("admins/<int:admin_id>/", AdminDeleteAdminView.as_view(), name="admin-delete"),
]