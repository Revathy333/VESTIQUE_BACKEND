from django.urls import path
from .views import SaveFCMTokenView

app_name = 'notifications_app'

urlpatterns = [
    path('save-token/', SaveFCMTokenView.as_view(), name='save-fcm-token'),
]