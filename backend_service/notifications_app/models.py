from django.db import models
from django.conf import settings
import json


class FCMToken(models.Model):
    """Firebase Cloud Messaging token for push notifications"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fcm_token',
    )
    token = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fcm_tokens'
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f'{self.user.email} - FCM'


class Notification(models.Model):
    """Track sent notifications"""
    NOTIFICATION_TYPE_CHOICES = [
        ('user', 'Single User'),
        ('bulk', 'Bulk'),
        ('topic', 'Topic'),
        ('personal', 'Personal'),
        ('announcement', 'Announcement'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    ]
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        null=True,
        blank=True
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_notifications',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    icon = models.URLField(blank=True, null=True)
    click_action = models.URLField(blank=True, null=True)
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        default='user'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    is_read = models.BooleanField(default=False)
    lambda_message_id = models.CharField(max_length=255, blank=True, null=True)
    lambda_response = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['notification_type']),
        ]

    def __str__(self):
        return f'{self.title} - {self.recipient.email if self.recipient else "Topic: " + self.data.get("topic", "unknown")}'

