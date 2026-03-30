from django.contrib import admin
from .models import FCMToken, Notification


@admin.register(FCMToken)
class FCMTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token_preview', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('token', 'created_at', 'updated_at')
    
    def token_preview(self, obj):
        return f"{obj.token[:50]}..." if obj.token else "N/A"
    token_preview.short_description = "Token Preview"
    
    def has_add_permission(self, request):
        return False  # Only saved via API


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'sender',
        'recipient',
        'notification_type',
        'status',
        'is_read',
        'created_at'
    )
    list_filter = (
        'status',
        'notification_type',
        'is_read',
        'created_at',
        'sent_at'
    )
    search_fields = (
        'title',
        'body',
        'sender__email',
        'recipient__email'
    )
    readonly_fields = (
        'lambda_message_id',
        'lambda_response',
        'created_at',
        'updated_at',
        'sent_at'
    )
    fieldsets = (
        ('Notification Info', {
            'fields': ('title', 'body', 'data', 'icon', 'click_action')
        }),
        ('Recipients', {
            'fields': ('sender', 'recipient', 'notification_type')
        }),
        ('Status', {
            'fields': ('status', 'is_read', 'error_message')
        }),
        ('Lambda Details', {
            'fields': ('lambda_message_id', 'lambda_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'sent_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Only created via API

