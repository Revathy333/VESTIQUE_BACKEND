from django.db import models
from django.conf import settings

class FCMToken(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fcm_token',
    )
    token = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fcm_tokens'

    def __str__(self):
        return f'{self.user.email} - FCM'
