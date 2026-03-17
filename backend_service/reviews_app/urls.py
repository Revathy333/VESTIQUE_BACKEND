from django.urls import path
from .views import (
    GeneralReviewListCreateView,
    GeneralReviewEditView,
    GeneralReviewReplyView,
    GeneralReviewReplyEditView,
    ProfileReviewListCreateView,
    ProfileReviewEditView,
    ProfileReviewReplyView,
    SearchDesignersView,
)

app_name = 'reviews_app'

urlpatterns = [

    # ── General Reviews ───────────────────────────────────────────────────────
    path('general/', GeneralReviewListCreateView.as_view(), name='general-list-create'),
    path('general/<int:review_id>/', GeneralReviewEditView.as_view(), name='general-edit'),
    path('general/<int:review_id>/reply/', GeneralReviewReplyView.as_view(), name='general-reply'),
    path('general/<int:review_id>/reply/<int:reply_id>/', GeneralReviewReplyEditView.as_view(), name='general-reply-edit'),

    # ── Profile Reviews ───────────────────────────────────────────────────────
    path('profile/<int:user_id>/', ProfileReviewListCreateView.as_view(), name='profile-list-create'),
    path('profile/edit/<int:review_id>/', ProfileReviewEditView.as_view(), name='profile-edit'),
    path('profile/<int:review_id>/reply/', ProfileReviewReplyView.as_view(), name='profile-reply'),

    # ── Search for mentions ───────────────────────────────────────────────────
    path('search-designers/', SearchDesignersView.as_view(), name='search-designers'),
]