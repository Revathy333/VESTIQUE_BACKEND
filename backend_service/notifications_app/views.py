# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated, IsAdminUser
# from django.db import transaction
# from django.core.cache import cache
# from .models import FCMToken, Notification
# from .serializers import NotificationSerializer
# from .tasks import send_notification_via_lambda
# import logging

# logger = logging.getLogger(__name__)


# class SaveFCMTokenView(APIView):
#     """
#     Save or update Firebase Cloud Messaging token for current user
    
#     POST /notifications/save-token/
#     {
#         "fcm_token": "firebase_device_token_here"
#     }
#     """
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         try:
#             token = request.data.get('fcm_token', '').strip()
            
#             if not token:
#                 return Response(
#                     {'error': 'fcm_token is required'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             if len(token) < 100:
#                 return Response(
#                     {'error': 'Invalid FCM token format'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             # Update or create FCM token
#             fcm_token_obj, created = FCMToken.objects.update_or_create(
#                 user=request.user,
#                 defaults={'token': token}
#             )
            
#             logger.info(f"FCM token saved for user {request.user.id}: {'created' if created else 'updated'}")
            
#             return Response({
#                 'message': 'FCM token saved successfully',
#                 'token_id': fcm_token_obj.id,
#                 'created': created
#             }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
#         except Exception as e:
#             logger.error(f"Error saving FCM token: {str(e)}")
#             return Response(
#                 {'error': 'Failed to save FCM token'},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# class SendNotificationToUserView(APIView):
#     """
#     Send notification to a specific user via Lambda
    
#     POST /notifications/send-to-user/
#     {
#         "user_id": "user_to_notify_id",
#         "title": "Notification Title",
#         "body": "Notification body text",
#         "data": {"key": "value"},
#         "icon": "https://example.com/icon.png",
#         "click_action": "https://example.com/page"
#     }
#     """
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         try:
#             from django.contrib.auth import get_user_model
#             User = get_user_model()
            
#             user_id = request.data.get('user_id')
#             title = request.data.get('title', 'Vestique')
#             body = request.data.get('body', 'You have a new message')
#             data = request.data.get('data', {})
#             icon = request.data.get('icon')
#             click_action = request.data.get('click_action')
            
#             # Validation
#             if not user_id:
#                 return Response(
#                     {'error': 'user_id is required'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             if not title or not body:
#                 return Response(
#                     {'error': 'title and body are required'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             # Check if user exists and has FCM token
#             try:
#                 target_user = User.objects.get(id=user_id)
#             except User.DoesNotExist:
#                 return Response(
#                     {'error': 'User not found'},
#                     status=status.HTTP_404_NOT_FOUND
#                 )
            
#             # Check if user has FCM token
#             try:
#                 fcm_token = FCMToken.objects.get(user=target_user)
#             except FCMToken.DoesNotExist:
#                 return Response(
#                     {'error': 'Target user has not saved FCM token'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             # Create notification record
#             notification = Notification.objects.create(
#                 sender=request.user,
#                 recipient=target_user,
#                 title=title,
#                 body=body,
#                 data=data,
#                 icon=icon,
#                 click_action=click_action,
#                 notification_type='user'
#             )
            
#             # Send via Lambda asynchronously
#             send_notification_via_lambda.delay(
#                 notification_id=notification.id,
#                 action='send_to_user',
#                 fcm_token=fcm_token.token,
#                 title=title,
#                 body=body,
#                 data=data,
#                 icon=icon,
#                 click_action=click_action
#             )
            
#             logger.info(f"Notification {notification.id} scheduled for sending from {request.user.id} to {target_user.id}")
            
#             return Response({
#                 'message': 'Notification sent successfully',
#                 'notification_id': notification.id,
#                 'recipient_id': target_user.id,
#                 'status': 'queued'
#             }, status=status.HTTP_200_OK)
        
#         except Exception as e:
#             logger.error(f"Error sending notification to user: {str(e)}")
#             return Response(
#                 {'error': 'Failed to send notification'},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# class SendBulkNotificationView(APIView):
#     """
#     Send notification to multiple users via Lambda
    
#     POST /notifications/send-bulk/
#     {
#         "user_ids": [1, 2, 3, ...],
#         "title": "Notification Title",
#         "body": "Notification body text",
#         "data": {"key": "value"}
#     }
#     """
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         try:
#             from django.contrib.auth import get_user_model
#             User = get_user_model()
            
#             user_ids = request.data.get('user_ids', [])
#             title = request.data.get('title', 'Vestique')
#             body = request.data.get('body', 'You have a new message')
#             data = request.data.get('data', {})
#             icon = request.data.get('icon')
#             click_action = request.data.get('click_action')
            
#             # Validation
#             if not user_ids or not isinstance(user_ids, list):
#                 return Response(
#                     {'error': 'user_ids must be a non-empty list'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             if len(user_ids) > 1000:
#                 return Response(
#                     {'error': 'Maximum 1000 users per request'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             if not title or not body:
#                 return Response(
#                     {'error': 'title and body are required'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             # Get FCM tokens for all users
#             fcm_tokens = FCMToken.objects.filter(
#                 user_id__in=user_ids
#             ).select_related('user').values_list('token', flat=True)
            
#             if not fcm_tokens.exists():
#                 return Response(
#                     {'error': 'No users with FCM tokens found'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             token_list = list(fcm_tokens)
            
#             # Create notification records for each user
#             users = User.objects.filter(id__in=user_ids)
#             notifications = []
#             with transaction.atomic():
#                 for user in users:
#                     notification = Notification.objects.create(
#                         sender=request.user,
#                         recipient=user,
#                         title=title,
#                         body=body,
#                         data=data,
#                         icon=icon,
#                         click_action=click_action,
#                         notification_type='bulk'
#                     )
#                     notifications.append(notification)
            
#             # Send via Lambda asynchronously
#             send_notification_via_lambda.delay(
#                 action='send_bulk',
#                 fcm_tokens=token_list,
#                 title=title,
#                 body=body,
#                 data=data,
#                 icon=icon,
#                 click_action=click_action,
#                 notification_ids=[n.id for n in notifications]
#             )
            
#             logger.info(f"Bulk notification from {request.user.id} to {len(token_list)} users scheduled")
            
#             return Response({
#                 'message': 'Bulk notification sent successfully',
#                 'total_users': len(users),
#                 'notifications_created': len(notifications),
#                 'status': 'queued'
#             }, status=status.HTTP_200_OK)
        
#         except Exception as e:
#             logger.error(f"Error sending bulk notification: {str(e)}")
#             return Response(
#                 {'error': 'Failed to send bulk notification'},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# class SendTopicNotificationView(APIView):
#     """
#     Send notification to all users subscribed to a topic
    
#     POST /notifications/send-to-topic/
#     {
#         "topic": "announcements",
#         "title": "New Announcement",
#         "body": "Important update",
#         "data": {"type": "announcement"}
#     }
#     """
#     permission_classes = [IsAdminUser]

#     def post(self, request):
#         try:
#             topic = request.data.get('topic', '').strip()
#             title = request.data.get('title', 'Vestique')
#             body = request.data.get('body', 'You have a new message')
#             data = request.data.get('data', {})
#             icon = request.data.get('icon')
#             click_action = request.data.get('click_action')
            
#             # Validation
#             if not topic:
#                 return Response(
#                     {'error': 'topic is required'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             if not title or not body:
#                 return Response(
#                     {'error': 'title and body are required'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             # Send via Lambda asynchronously
#             send_notification_via_lambda.delay(
#                 action='send_to_topic',
#                 topic=topic,
#                 title=title,
#                 body=body,
#                 data=data,
#                 icon=icon,
#                 click_action=click_action
#             )
            
#             logger.info(f"Topic notification from admin {request.user.id} to topic '{topic}' scheduled")
            
#             return Response({
#                 'message': 'Topic notification sent successfully',
#                 'topic': topic,
#                 'status': 'queued'
#             }, status=status.HTTP_200_OK)
        
#         except Exception as e:
#             logger.error(f"Error sending topic notification: {str(e)}")
#             return Response(
#                 {'error': 'Failed to send topic notification'},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# class NotificationHistoryView(APIView):
#     """
#     Get notification history for current user
    
#     GET /notifications/history/?limit=50&offset=0
#     """
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         try:
#             limit = int(request.query_params.get('limit', 50))
#             offset = int(request.query_params.get('offset', 0))
            
#             # Validate limits
#             if limit > 100:
#                 limit = 100
#             if limit < 1:
#                 limit = 10
            
#             notifications = Notification.objects.filter(
#                 recipient=request.user
#             ).select_related('sender').order_by('-created_at')[offset:offset+limit]
            
#             serializer = NotificationSerializer(notifications, many=True)
            
#             return Response({
#                 'notifications': serializer.data,
#                 'count': Notification.objects.filter(recipient=request.user).count(),
#                 'limit': limit,
#                 'offset': offset
#             }, status=status.HTTP_200_OK)
        
#         except Exception as e:
#             logger.error(f"Error fetching notification history: {str(e)}")
#             return Response(
#                 {'error': 'Failed to fetch notifications'},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# class MarkNotificationAsReadView(APIView):
#     """
#     Mark notification as read
    
#     PATCH /notifications/{notification_id}/mark-read/
#     """
#     permission_classes = [IsAuthenticated]

#     def patch(self, request, notification_id):
#         try:
#             notification = Notification.objects.get(id=notification_id)
            
#             # Check if user is recipient
#             if notification.recipient != request.user:
#                 return Response(
#                     {'error': 'Unauthorized'},
#                     status=status.HTTP_403_FORBIDDEN
#                 )
            
#             notification.is_read = True
#             notification.save(update_fields=['is_read'])
            
#             return Response({
#                 'message': 'Notification marked as read',
#                 'notification_id': notification_id
#             }, status=status.HTTP_200_OK)
        
#         except Notification.DoesNotExist:
#             return Response(
#                 {'error': 'Notification not found'},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         except Exception as e:
#             logger.error(f"Error marking notification as read: {str(e)}")
#             return Response(
#                 {'error': 'Failed to mark notification'},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# class CreateMessageNotificationView(APIView):
#     """
#     Internal endpoint for creating message notifications (called by chat service)
#     No authentication required - internal service-to-service call
    
#     POST /notifications/create-message/
#     {
#         "recipient_id": "recipient_user_id",
#         "sender_id": "sender_user_id",
#         "title": "Notification Title",
#         "body": "Message preview",
#         "data": {"message_id": 123, "type": "message"}
#     }
#     """
#     permission_classes = []  # Allow unauthenticated access for internal calls

#     def post(self, request):
#         try:
#             from django.contrib.auth import get_user_model
#             User = get_user_model()
            
#             recipient_id = request.data.get('recipient_id')
#             sender_id = request.data.get('sender_id')
#             title = request.data.get('title', 'New Message')
#             body = request.data.get('body', 'You have a new message')
#             data = request.data.get('data', {})
#             click_action = request.data.get('click_action')
            
#             # Validation
#             if not recipient_id:
#                 return Response(
#                     {'error': 'recipient_id is required'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             # Get recipient user
#             try:
#                 recipient = User.objects.get(id=recipient_id)
#             except User.DoesNotExist:
#                 return Response(
#                     {'error': 'Recipient not found'},
#                     status=status.HTTP_404_NOT_FOUND
#                 )
            
#             # Get sender user if provided
#             sender = None
#             sender_name = None
#             if sender_id:
#                 try:
#                     sender = User.objects.get(id=sender_id)
#                     sender_name = sender.get_full_name() or sender.email
#                 except User.DoesNotExist:
#                     pass

#             # Build a more descriptive title and click action for chat notifications
#             if not title:
#                 title = f"New message from {sender_name or 'Someone'}"
#             if not click_action:
#                 click_action = f"/chat?userId={sender_id}" if sender_id else "/chat"

#             # Add sender metadata to payload (used by frontend)
#             if sender_name:
#                 data = {**data, 'sender_name': sender_name}

#             # Check if recipient has FCM token
#             try:
#                 fcm_token = FCMToken.objects.get(user=recipient)
#             except FCMToken.DoesNotExist:
#                 # User hasn't set up FCM, create notification record but skip push
#                 notification = Notification.objects.create(
#                     sender=sender,
#                     recipient=recipient,
#                     title=title,
#                     body=body,
#                     data=data,
#                     click_action=click_action,
#                     notification_type='personal',
#                     status='sent'
#                 )
#                 logger.info(f"Message notification {notification.id} created (no FCM token for user {recipient_id})")
#                 return Response({
#                     'message': 'Notification created (no FCM token)',
#                     'notification_id': notification.id
#                 }, status=status.HTTP_201_CREATED)

#             # Create notification record
#             notification = Notification.objects.create(
#                 sender=sender,
#                 recipient=recipient,
#                 title=title,
#                 body=body,
#                 data=data,
#                 click_action=click_action,
#                 notification_type='personal'
#             )

#             # Send via Lambda asynchronously
#             send_notification_via_lambda.delay(
#                 action='send_to_user',
#                 fcm_token=fcm_token.token,
#                 title=title,
#                 body=body,
#                 data=data,
#                 click_action=click_action,
#                 notification_ids=[notification.id],
#             )

#             logger.info(f"Message notification {notification.id} scheduled for user {recipient_id}")
            
#             return Response({
#                 'message': 'Notification created and queued',
#                 'notification_id': notification.id,
#                 'status': 'queued'
#             }, status=status.HTTP_201_CREATED)
        
#         except Exception as e:
#             logger.error(f"Error creating message notification: {str(e)}")
#             return Response(
#                 {'error': 'Failed to create notification'},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import transaction
from django.core.cache import cache
from .models import FCMToken, Notification
from .serializers import NotificationSerializer
from .tasks import send_notification_via_lambda
import logging

logger = logging.getLogger(__name__)


class SaveFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = request.data.get('fcm_token', '').strip()
            if not token:
                return Response({'error': 'fcm_token is required'}, status=status.HTTP_400_BAD_REQUEST)
            if len(token) < 100:
                return Response({'error': 'Invalid FCM token format'}, status=status.HTTP_400_BAD_REQUEST)

            fcm_token_obj, created = FCMToken.objects.update_or_create(
                user=request.user,
                defaults={'token': token}
            )
            logger.info(f"FCM token saved for user {request.user.id}: {'created' if created else 'updated'}")
            return Response({
                'message': 'FCM token saved successfully',
                'token_id': fcm_token_obj.id,
                'created': created
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error saving FCM token: {str(e)}")
            return Response({'error': 'Failed to save FCM token'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendNotificationToUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()

            user_id = request.data.get('user_id')
            title = request.data.get('title', 'Vestique')
            body = request.data.get('body', 'You have a new message')
            data = request.data.get('data', {})
            icon = request.data.get('icon')
            click_action = request.data.get('click_action')

            if not user_id:
                return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            if not title or not body:
                return Response({'error': 'title and body are required'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            try:
                fcm_token = FCMToken.objects.get(user=target_user)
            except FCMToken.DoesNotExist:
                return Response({'error': 'Target user has not saved FCM token'}, status=status.HTTP_400_BAD_REQUEST)

            notification = Notification.objects.create(
                sender=request.user, recipient=target_user,
                title=title, body=body, data=data,
                icon=icon, click_action=click_action,
                notification_type='user'
            )
            send_notification_via_lambda.delay(
                notification_id=notification.id,
                action='send_to_user',
                fcm_token=fcm_token.token,
                title=title, body=body, data=data,
                icon=icon, click_action=click_action
            )
            logger.info(f"Notification {notification.id} scheduled from {request.user.id} to {target_user.id}")
            return Response({
                'message': 'Notification sent successfully',
                'notification_id': notification.id,
                'recipient_id': target_user.id,
                'status': 'queued'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error sending notification to user: {str(e)}")
            return Response({'error': 'Failed to send notification'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendBulkNotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()

            user_ids = request.data.get('user_ids', [])
            title = request.data.get('title', 'Vestique')
            body = request.data.get('body', 'You have a new message')
            data = request.data.get('data', {})
            icon = request.data.get('icon')
            click_action = request.data.get('click_action')

            if not user_ids or not isinstance(user_ids, list):
                return Response({'error': 'user_ids must be a non-empty list'}, status=status.HTTP_400_BAD_REQUEST)
            if len(user_ids) > 1000:
                return Response({'error': 'Maximum 1000 users per request'}, status=status.HTTP_400_BAD_REQUEST)
            if not title or not body:
                return Response({'error': 'title and body are required'}, status=status.HTTP_400_BAD_REQUEST)

            fcm_tokens = FCMToken.objects.filter(
                user_id__in=user_ids
            ).select_related('user').values_list('token', flat=True)

            if not fcm_tokens.exists():
                return Response({'error': 'No users with FCM tokens found'}, status=status.HTTP_400_BAD_REQUEST)

            token_list = list(fcm_tokens)
            users = User.objects.filter(id__in=user_ids)
            notifications = []
            with transaction.atomic():
                for user in users:
                    notification = Notification.objects.create(
                        sender=request.user, recipient=user,
                        title=title, body=body, data=data,
                        icon=icon, click_action=click_action,
                        notification_type='bulk'
                    )
                    notifications.append(notification)

            send_notification_via_lambda.delay(
                action='send_bulk', fcm_tokens=token_list,
                title=title, body=body, data=data,
                icon=icon, click_action=click_action,
                notification_ids=[n.id for n in notifications]
            )
            logger.info(f"Bulk notification from {request.user.id} to {len(token_list)} users scheduled")
            return Response({
                'message': 'Bulk notification sent successfully',
                'total_users': len(users),
                'notifications_created': len(notifications),
                'status': 'queued'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error sending bulk notification: {str(e)}")
            return Response({'error': 'Failed to send bulk notification'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendTopicNotificationView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            topic = request.data.get('topic', '').strip()
            title = request.data.get('title', 'Vestique')
            body = request.data.get('body', 'You have a new message')
            data = request.data.get('data', {})
            icon = request.data.get('icon')
            click_action = request.data.get('click_action')

            if not topic:
                return Response({'error': 'topic is required'}, status=status.HTTP_400_BAD_REQUEST)
            if not title or not body:
                return Response({'error': 'title and body are required'}, status=status.HTTP_400_BAD_REQUEST)

            send_notification_via_lambda.delay(
                action='send_to_topic', topic=topic,
                title=title, body=body, data=data,
                icon=icon, click_action=click_action
            )
            logger.info(f"Topic notification from admin {request.user.id} to topic '{topic}' scheduled")
            return Response({
                'message': 'Topic notification sent successfully',
                'topic': topic,
                'status': 'queued'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error sending topic notification: {str(e)}")
            return Response({'error': 'Failed to send topic notification'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 50))
            offset = int(request.query_params.get('offset', 0))

            if limit > 100:
                limit = 100
            if limit < 1:
                limit = 10

            notifications = Notification.objects.filter(
                recipient=request.user
            ).select_related('sender').order_by('-created_at')[offset:offset+limit]

            serializer = NotificationSerializer(notifications, many=True)

            # ✅ CHANGED: added unread_count to response (badge needs this)
            total = Notification.objects.filter(recipient=request.user).count()
            unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()

            return Response({
                'notifications': serializer.data,
                'count': total,
                'unread_count': unread_count,
                'limit': limit,
                'offset': offset
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching notification history: {str(e)}")
            return Response({'error': 'Failed to fetch notifications'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarkNotificationAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        try:
            notification = Notification.objects.get(id=notification_id)

            if notification.recipient != request.user:
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

            # ✅ CHANGED: also set status='read'
            notification.is_read = True
            notification.status = 'read'
            notification.save(update_fields=['is_read', 'status'])

            return Response({
                'message': 'Notification marked as read',
                'notification_id': notification_id
            }, status=status.HTTP_200_OK)

        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return Response({'error': 'Failed to mark notification'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ NEW: Delete a single notification
class DeleteNotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=request.user
            )
            notification.delete()
            return Response({
                'message': 'Notification deleted',
                'notification_id': notification_id
            }, status=status.HTTP_200_OK)

        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting notification: {str(e)}")
            return Response({'error': 'Failed to delete notification'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ NEW: Mark ALL notifications as read in one DB query
class MarkAllNotificationsAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            updated = Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).update(is_read=True, status='read')

            return Response({
                'message': f'{updated} notifications marked as read',
                'updated': updated
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            return Response({'error': 'Failed to mark all as read'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateMessageNotificationView(APIView):
    permission_classes = []

    def post(self, request):
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()

            recipient_id = request.data.get('recipient_id')
            sender_id = request.data.get('sender_id')
            title = request.data.get('title', 'New Message')
            body = request.data.get('body', 'You have a new message')
            data = request.data.get('data', {})
            click_action = request.data.get('click_action')

            if not recipient_id:
                return Response({'error': 'recipient_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                recipient = User.objects.get(id=recipient_id)
            except User.DoesNotExist:
                return Response({'error': 'Recipient not found'}, status=status.HTTP_404_NOT_FOUND)

            sender = None
            sender_name = None
            if sender_id:
                try:
                    sender = User.objects.get(id=sender_id)
                    sender_name = sender.get_full_name() or sender.email
                except User.DoesNotExist:
                    pass

            if not title:
                title = f"New message from {sender_name or 'Someone'}"
            if not click_action:
                click_action = f"/chat?userId={sender_id}" if sender_id else "/chat"

            if sender_name:
                data = {**data, 'sender_name': sender_name}

            try:
                fcm_token = FCMToken.objects.get(user=recipient)
            except FCMToken.DoesNotExist:
                notification = Notification.objects.create(
                    sender=sender, recipient=recipient,
                    title=title, body=body, data=data,
                    click_action=click_action,
                    notification_type='personal', status='sent'
                )
                logger.info(f"Message notification {notification.id} created (no FCM token for user {recipient_id})")
                return Response({
                    'message': 'Notification created (no FCM token)',
                    'notification_id': notification.id
                }, status=status.HTTP_201_CREATED)

            notification = Notification.objects.create(
                sender=sender, recipient=recipient,
                title=title, body=body, data=data,
                click_action=click_action,
                notification_type='personal'
            )
            send_notification_via_lambda.delay(
                action='send_to_user',
                fcm_token=fcm_token.token,
                title=title, body=body, data=data,
                click_action=click_action,
                notification_ids=[notification.id],
            )
            logger.info(f"Message notification {notification.id} scheduled for user {recipient_id}")
            return Response({
                'message': 'Notification created and queued',
                'notification_id': notification.id,
                'status': 'queued'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating message notification: {str(e)}")
            return Response({'error': 'Failed to create notification'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)