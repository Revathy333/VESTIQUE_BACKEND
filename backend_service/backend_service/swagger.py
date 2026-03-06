from django.conf import settings
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAdminUser

_permission = [AllowAny] if settings.DEBUG else [IsAdminUser]

class PublicSchemaView(SpectacularAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = _permission

class PublicSwaggerView(SpectacularSwaggerView):
    authentication_classes = [SessionAuthentication]
    permission_classes = _permission

class PublicRedocView(SpectacularRedocView):
    authentication_classes = [SessionAuthentication]
    permission_classes = _permission