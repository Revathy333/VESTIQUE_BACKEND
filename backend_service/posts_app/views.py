import json
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Post, PostMedia, Like, Comment
from .permissions import IsDesignerOrTailor

User = get_user_model()

def serialize_post(post, request_user):
    media = [
        {
            "id": m.id,
            "media_type": m.media_type,
            "file_url": f"http://localhost{m.file.url}",
            "order": m.order,
        }
        for m in post.media.all()
    ]
    comments = [
        {
            "id": c.id,
            "author_name": c.author.get_full_name() or c.author.email,
            "author_role": c.author.role,
            "text": c.text,
            "created_at": c.created_at.isoformat(),
        }
        for c in post.comments.all()
    ]
    user_liked = post.likes.filter(user=request_user).exists() if request_user.is_authenticated else False

    return {
        "id": post.id,
        "author_id": post.author.id,
        "author_name": post.author.get_full_name() or post.author.email,
        "author_role": post.author.role,
        "author_avatar": post.author.profile_picture,
        "caption": post.caption,
        "media": media,
        "likes_count": post.likes_count(),
        "comments_count": post.comments_count(),
        "comments": comments,
        "user_liked": user_liked,
        "is_owner": post.author == request_user,
        "created_at": post.created_at.isoformat(),
    }


class PostListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        posts = Post.objects.prefetch_related('media', 'likes', 'comments__author').all()
        data = [serialize_post(p, request.user) for p in posts]
        return Response({"posts": data, "count": len(data)})

    def post(self, request):
        # Only designers and tailors can create
        if request.user.role not in ['designer', 'tailor']:
            return Response(
                {"error": "Only designers and tailors can create posts."},
                status=status.HTTP_403_FORBIDDEN
            )

        caption = request.data.get('caption', '').strip()
        files = request.FILES.getlist('media')

        if not caption and not files:
            return Response(
                {"error": "Post must have a caption or at least one media file."},
                status=status.HTTP_400_BAD_REQUEST
            )

        post = Post.objects.create(author=request.user, caption=caption)

        for i, f in enumerate(files):
            content_type = f.content_type or ''
            media_type = 'video' if content_type.startswith('video') else 'image'
            PostMedia.objects.create(post=post, file=f, media_type=media_type, order=i)

        return Response(serialize_post(post, request.user), status=status.HTTP_201_CREATED)


class PostDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        if post.author != request.user:
            return Response({"error": "You can only delete your own posts."}, status=status.HTTP_403_FORBIDDEN)

        post.delete()
        return Response({"message": "Post deleted."}, status=status.HTTP_200_OK)


class LikeToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        # Customers cannot like
        if request.user.role == 'customer':
            return Response(
                {"error": "Customers can only view posts."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        like, created = Like.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
            return Response({"liked": False, "likes_count": post.likes_count()})

        return Response({"liked": True, "likes_count": post.likes_count()})


class CommentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        # Customers cannot comment
        if request.user.role == 'customer':
            return Response(
                {"error": "Customers can only view posts."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        text = request.data.get('text', '').strip()
        if not text:
            return Response({"error": "Comment cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        comment = Comment.objects.create(post=post, author=request.user, text=text)
        return Response({
            "id": comment.id,
            "author_name": comment.author.get_full_name() or comment.author.email,
            "author_role": comment.author.role,
            "text": comment.text,
            "created_at": comment.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)

    def delete(self, request, post_id):
        comment_id = request.data.get('comment_id')
        try:
            comment = Comment.objects.get(id=comment_id, post_id=post_id)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)

        if comment.author != request.user:
            return Response({"error": "You can only delete your own comments."}, status=status.HTTP_403_FORBIDDEN)

        comment.delete()
        return Response({"message": "Comment deleted."})