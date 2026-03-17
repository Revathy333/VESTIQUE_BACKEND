from django.urls import path
from .views import PostListCreateView, PostDetailView, LikeToggleView, CommentCreateView, GeneratePresignedURLView


app_name = 'posts_app'

urlpatterns = [
    path('', PostListCreateView.as_view(), name='post-list-create'),
    path('<int:post_id>/', PostDetailView.as_view(), name='post-detail'),
    path('<int:post_id>/like/', LikeToggleView.as_view(), name='post-like'),
    path('<int:post_id>/comments/', CommentCreateView.as_view(), name='post-comments'),
    path('presigned-url/', GeneratePresignedURLView.as_view(), name='post-presigned-url'),
]