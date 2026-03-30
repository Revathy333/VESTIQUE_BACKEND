from rest_framework import serializers
from .models import FCMToken, Notification
from django.contrib.auth import get_user_model

User = get_user_model()


class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMToken
        fields = ['id', 'token', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user info for notification serialization"""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']


class NotificationSerializer(serializers.ModelSerializer):
    sender = UserMinimalSerializer(read_only=True)
    recipient = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'sender',
            'recipient',
            'title',
            'body',
            'data',
            'icon',
            'click_action',
            'notification_type',
            'status',
            'is_read',
            'created_at',
            'updated_at',
            'sent_at'
        ]
        read_only_fields = [
            'id',
            'status',
            'created_at',
            'updated_at',
            'sent_at'
        ]
