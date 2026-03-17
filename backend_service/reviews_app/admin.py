from django.contrib import admin
from .models import (
    GeneralReview,
    GeneralReviewMention,
    GeneralReviewReply,
    ProfileReview,
    ProfileReviewReply
)


@admin.register(GeneralReview)
class GeneralReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "rating", "created_at")
    search_fields = ("author__email", "text")
    list_filter = ("rating", "created_at")


@admin.register(GeneralReviewMention)
class GeneralReviewMentionAdmin(admin.ModelAdmin):
    list_display = ("id", "review", "mentioned_user")


@admin.register(GeneralReviewReply)
class GeneralReviewReplyAdmin(admin.ModelAdmin):
    list_display = ("id", "review", "author", "created_at")


@admin.register(ProfileReview)
class ProfileReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "reviewer", "reviewed_user", "rating", "created_at")


@admin.register(ProfileReviewReply)
class ProfileReviewReplyAdmin(admin.ModelAdmin):
    list_display = ("id", "review", "author", "created_at")