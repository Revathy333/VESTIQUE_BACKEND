import boto3
import json
from celery import shared_task
from .models import FCMToken

def _invoke_lambda(fcm_token, title, body, data=None):
    client = boto3.client('lambda', region_name='us-east-1')
    payload = {'fcm_token': fcm_token, 'title': title, 'body': body, 'data': data or {}}
    return client.invoke(
        FunctionName='vestique-send-notification',
        InvocationType='Event',
        Payload=json.dumps(payload),
    )

@shared_task(bind=True, max_retries=3)
def send_push_notification(self, user_id, title, body, data=None):
    try:
        fcm = FCMToken.objects.get(user_id=user_id)
        _invoke_lambda(fcm.token, title, body, data or {})
    except FCMToken.DoesNotExist:
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
