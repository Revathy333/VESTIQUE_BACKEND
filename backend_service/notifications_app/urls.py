from django.urls import path
from .views import (
    DeleteNotificationView,
    MarkAllNotificationsAsReadView,
    SaveFCMTokenView,
    SendNotificationToUserView,
    SendBulkNotificationView,
    SendTopicNotificationView,
    NotificationHistoryView,
    MarkNotificationAsReadView,
    CreateMessageNotificationView,
)

app_name = 'notifications_app'

urlpatterns = [
    # Token management
    path('save-token/', SaveFCMTokenView.as_view(), name='save-fcm-token'),
    
    # Notification sending
    path('send-to-user/', SendNotificationToUserView.as_view(), name='send-to-user'),
    path('send-bulk/', SendBulkNotificationView.as_view(), name='send-bulk'),
    path('send-to-topic/', SendTopicNotificationView.as_view(), name='send-to-topic'),
    
    # Notification history and management
    path('history/', NotificationHistoryView.as_view(), name='notification-history'),
    path('<int:notification_id>/mark-read/', MarkNotificationAsReadView.as_view(), name='mark-notification-read'),
    
    # Internal endpoints for service-to-service communication
    path('create-message/', CreateMessageNotificationView.as_view(), name='create-message-notification'),

    path('<int:notification_id>/delete/', DeleteNotificationView.as_view(), name='delete-notification'),
    path('mark-all-read/', MarkAllNotificationsAsReadView.as_view(), name='mark-all-read'),
]