"""
Celery tasks for sending push notifications via AWS Lambda
"""

from celery import shared_task
import boto3
import json
import logging
from .models import Notification, FCMToken
from django.conf import settings
from datetime import datetime

logger = logging.getLogger(__name__)


def _invoke_lambda(fcm_token, title, body, data=None):
    """Legacy function - kept for backward compatibility"""
    client = boto3.client('lambda', region_name='us-east-1')
    payload = {'fcm_token': fcm_token, 'title': title, 'body': body, 'data': data or {}}
    return client.invoke(
        FunctionName='vestique-send-notification',
        InvocationType='Event',
        Payload=json.dumps(payload),
    )


@shared_task(bind=True, max_retries=3)
def send_push_notification(self, user_id, title, body, data=None):
    """Legacy task - kept for backward compatibility"""
    try:
        fcm = FCMToken.objects.get(user_id=user_id)
        _invoke_lambda(fcm.token, title, body, data or {})
    except FCMToken.DoesNotExist:
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_notification_via_lambda(
    self,
    action='send_to_user',
    fcm_token=None,
    fcm_tokens=None,
    title=None,
    body=None,
    data=None,
    topic=None,
    icon=None,
    click_action=None,
    notification_ids=None,
    **kwargs
):
    """
    Send notification via AWS Lambda
    
    Args:
        action: 'send_to_user' | 'send_bulk' | 'send_to_topic'
        fcm_token: Single token for send_to_user
        fcm_tokens: List of tokens for send_bulk
        title: Notification title
        body: Notification body
        data: Additional data dict
        topic: Topic name for send_to_topic
        icon: Icon URL
        click_action: Click action URL
        notification_ids: List of notification DB IDs to update
    """
    
    try:
        lambda_client = boto3.client(
            'lambda',
            region_name=getattr(settings, 'AWS_REGION', 'us-east-1'),
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        # Build Lambda event payload
        payload = {
            'action': action,
            'title': title,
            'body': body,
            'data': data or {},
            'icon': icon,
            'click_action': click_action,
        }
        
        if action == 'send_to_user' and fcm_token:
            payload['fcm_token'] = fcm_token
        elif action == 'send_bulk' and fcm_tokens:
            payload['fcm_tokens'] = fcm_tokens
        elif action == 'send_to_topic' and topic:
            payload['topic'] = topic
        else:
            logger.error(f"Invalid payload for action {action}")
            raise ValueError(f"Invalid or missing parameters for action {action}")
        
        lambda_function_name = getattr(settings, 'LAMBDA_FUNCTION_NAME', 'vestique-send-notification')
        logger.info(f"Invoking Lambda function '{lambda_function_name}' with action: {action}")
        
        # Invoke Lambda asynchronously
        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(payload)
        )
        
        logger.info(f"Lambda invoked successfully. Status code: {response['StatusCode']}")
        
        # Update notification records with sent status
        if notification_ids:
            Notification.objects.filter(id__in=notification_ids).update(
                status='sent',
                sent_at=datetime.now()
            )
            logger.info(f"Updated {len(notification_ids)} notifications to 'sent' status")
        
        return {
            'status': 'success',
            'lambda_response_code': response['StatusCode'],
            'action': action,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as exc:
        logger.error(f"Error invoking Lambda: {str(exc)}")
        
        # Update notification records with failed status
        if notification_ids:
            Notification.objects.filter(id__in=notification_ids).update(
                status='failed',
                error_message=str(exc)
            )
        
        # Retry with exponential backoff
        retry_count = self.request.retries
        if retry_count < self.max_retries:
            countdown = 2 ** retry_count  # 2, 4, 8 seconds
            logger.info(f"Retrying Lambda invocation in {countdown}s (attempt {retry_count + 1}/{self.max_retries})")
            raise self.retry(exc=exc, countdown=countdown)
        else:
            logger.error(f"Max retries reached for Lambda invocation: {str(exc)}")
            return {
                'status': 'failed',
                'error': str(exc),
                'timestamp': datetime.now().isoformat()
            }


@shared_task
def cleanup_old_notifications(days=30):
    """
    Delete old notifications from the database
    
    Args:
        days: Number of days to keep notifications (default: 30 days)
    """
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count, _ = Notification.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Deleted {deleted_count} old notifications")
        
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error cleaning up old notifications: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


@shared_task
def sync_notification_status(notification_id, status, message_id=None):
    """
    Update notification status from Lambda callback
    
    Args:
        notification_id: ID of notification to update
        status: Status to set ('sent', 'failed', 'read')
        message_id: FCM message ID (optional)
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.status = status
        if message_id:
            notification.lambda_message_id = message_id
        if status == 'sent':
            notification.sent_at = datetime.now()
        notification.save(update_fields=['status', 'sent_at', 'lambda_message_id'])
        
        logger.info(f"Updated notification {notification_id} status to {status}")
        
        return {
            'status': 'success',
            'notification_id': notification_id,
            'updated_status': status
        }
    
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return {
            'status': 'failed',
            'error': f"Notification {notification_id} not found"
        }
    except Exception as e:
        logger.error(f"Error updating notification status: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }


"""
Add this task to your existing notifications_app/tasks.py
(paste it at the bottom, above nothing — it imports from the same file's models)
"""

@shared_task(bind=True, max_retries=3)
def notify_all_users_new_post_task(self, post_id, author_id, designer_name, post_title):
    """
    Called automatically via signal when a designer uploads a new post.
    Fetches every user's FCM token (except the designer's own),
    creates a Notification record per user, then sends a bulk push via Lambda.

    FCM multicast supports up to 500 tokens per call, so we chunk them.
    """
    try:
        FCM_CHUNK_SIZE = 500  # FCM hard limit per multicast request

        # 1. Collect all FCM tokens except the designer's own
        tokens_qs = (
            FCMToken.objects
            .exclude(user_id=author_id)
            .select_related('user')
            .values('user_id', 'token')
        )

        if not tokens_qs.exists():
            logger.info(f"No FCM tokens found — skipping push for post {post_id}")
            return {'status': 'skipped', 'reason': 'no_tokens'}

        # Build token list and a user_id→token map
        all_entries = list(tokens_qs)
        all_tokens  = [e['token'] for e in all_entries]
        user_ids    = [e['user_id'] for e in all_entries]

        title = f"✨ {designer_name} just posted!"
        body  = post_title if post_title else "Check out the latest post"
        data  = {
            'type':      'new_post',
            'post_id':   str(post_id),
            'author_id': str(author_id),
        }

        # 2. Bulk-create one Notification record per recipient
        #    (do this in a single query — much faster than one-by-one)
        try:
            author = __import__('django.contrib.auth', fromlist=['get_user_model']).get_user_model()
            from django.contrib.auth import get_user_model
            User = get_user_model()
            author_obj = User.objects.get(id=author_id)
        except Exception:
            author_obj = None

        notifications = Notification.objects.bulk_create([
            Notification(
                sender=author_obj,
                recipient_id=uid,
                title=title,
                body=body,
                data=data,
                notification_type='announcement',
                status='pending',
            )
            for uid in user_ids
        ])
        notification_ids = [n.id for n in notifications]
        logger.info(f"Created {len(notification_ids)} notification records for post {post_id}")

        # 3. Send in chunks of 500 (FCM multicast limit)
        for i in range(0, len(all_tokens), FCM_CHUNK_SIZE):
            chunk_tokens = all_tokens[i : i + FCM_CHUNK_SIZE]
            chunk_notif_ids = notification_ids[i : i + FCM_CHUNK_SIZE]

            send_notification_via_lambda.delay(
                action='send_bulk',
                fcm_tokens=chunk_tokens,
                title=title,
                body=body,
                data=data,
                notification_ids=chunk_notif_ids,
            )
            logger.info(
                f"Queued bulk push chunk {i // FCM_CHUNK_SIZE + 1} "
                f"({len(chunk_tokens)} tokens) for post {post_id}"
            )

        return {
            'status': 'queued',
            'post_id': post_id,
            'total_recipients': len(all_tokens),
            'chunks': (len(all_tokens) + FCM_CHUNK_SIZE - 1) // FCM_CHUNK_SIZE,
        }

    except Exception as exc:
        logger.error(f"notify_all_users_new_post_task failed for post {post_id}: {exc}")
        retry_count = self.request.retries
        countdown = 2 ** retry_count  # 2, 4, 8 s
        raise self.retry(exc=exc, countdown=countdown)