# from django.contrib.auth import get_user_model
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.parsers import  JSONParser

# # NEW
# import boto3
# import uuid
# import os
# from botocore.exceptions import ClientError
# from django.conf import settings

# from .models import Post, PostMedia, Like, Comment
# from .permissions import IsDesignerOrTailor

# User = get_user_model()

# def serialize_post(post, request_user):
#     media = [
#         {
#             "id": m.id,
#             "media_type": m.media_type,
#             "file_url": m.file.url,
#             "order": m.order,
#         }
#         for m in post.media.all()
#     ]
#     comments = [
#         {
#             "id": c.id,
#             "author_name": c.author.get_full_name() or c.author.email,
#             "author_role": c.author.role,
#             "text": c.text,
#             "created_at": c.created_at.isoformat(),
#         }
#         for c in post.comments.all()
#     ]
#     user_liked = post.likes.filter(user=request_user).exists() if request_user.is_authenticated else False

#     return {
#         "id": post.id,
#         "author_id": post.author.id,
#         "author_name": post.author.get_full_name() or post.author.email,
#         "author_role": post.author.role,
#         "author_avatar": post.author.profile_picture,
#         "caption": post.caption,
#         "description": post.description,
#         "media": media,
#         "likes_count": post.likes_count(),
#         "comments_count": post.comments_count(),
#         "comments": comments,
#         "user_liked": user_liked,
#         "is_owner": post.author == request_user,
#         "created_at": post.created_at.isoformat(),
#     }


# class GeneratePresignedURLView(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = [JSONParser]

#     def post(self, request):
#         if request.user.role not in ['designer', 'tailor']:
#             return Response({"error": "Only designers and tailors can upload media."}, status=status.HTTP_403_FORBIDDEN)

#         files = request.data.get('files', [])
#         if not files or not isinstance(files, list):
#             return Response({"error": "'files' must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)

#         ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
#         ALLOWED_VIDEO_TYPES = {'video/mp4', 'video/quicktime', 'video/webm'}
#         ALLOWED_CONTENT_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES

#         s3 = boto3.client('s3',
#             region_name=settings.AWS_S3_REGION_NAME,
#             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#         )
#         presigned_urls = []

#         for item in files:
#             filename = item.get('filename', '').strip()
#             content_type = item.get('content_type', '').strip()

#             if not filename or not content_type:
#                 return Response({"error": "Each file needs 'filename' and 'content_type'."}, status=status.HTTP_400_BAD_REQUEST)
#             if content_type not in ALLOWED_CONTENT_TYPES:
#                 return Response({"error": f"Unsupported type: {content_type}"}, status=status.HTTP_400_BAD_REQUEST)

#             media_type = 'video' if content_type in ALLOWED_VIDEO_TYPES else 'image'
#             ext = os.path.splitext(filename)[-1].lower()
#             s3_key = f"posts/{uuid.uuid4().hex}{ext}"

#             try:
#                 upload_url = s3.generate_presigned_url('put_object',
#                     Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': s3_key, 'ContentType': content_type},
#                     ExpiresIn=300,
#                 )
#             except ClientError as e:
#                 return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#             presigned_urls.append({"upload_url": upload_url, "s3_key": s3_key, "media_type": media_type})

#         return Response({"presigned_urls": presigned_urls}, status=status.HTTP_200_OK)

# class PostListCreateView(APIView):
#     permission_classes = [IsAuthenticated]
#     # parser_classes = [MultiPartParser, FormParser, JSONParser]
#     parser_classes = [JSONParser]

#     def get(self, request):
#         posts = Post.objects.prefetch_related('media', 'likes', 'comments__author').all()
#         data = [serialize_post(p, request.user) for p in posts]
#         return Response({"posts": data, "count": len(data)})

#     def post(self, request):
#         # Only designers and tailors can create
#         if request.user.role not in ['designer', 'tailor']:
#             return Response(
#                 {"error": "Only designers and tailors can create posts."},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         caption = request.data.get('caption', '').strip()
#         description = request.data.get('description', '').strip()
#         media_items = request.data.get('media', [])

#         if not caption and not media_items:
#             return Response(
#                 {"error": "Post must have a caption or at least one media file."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         post = Post.objects.create(author=request.user, caption=caption, description=description)

#         # for i, f in enumerate(files):
#         #     content_type = f.content_type or ''
#         #     media_type = 'video' if content_type.startswith('video') else 'image'
#         #     PostMedia.objects.create(post=post, file=f, media_type=media_type, order=i)
#         for i, item in enumerate(media_items):
#             PostMedia.objects.create(post=post, file=item['s3_key'], media_type=item['media_type'], order=i)

#         return Response(serialize_post(post, request.user), status=status.HTTP_201_CREATED)


# class PostDetailView(APIView):
#     permission_classes = [IsAuthenticated]

#     def delete(self, request, post_id):
#         try:
#             post = Post.objects.get(id=post_id)
#         except Post.DoesNotExist:
#             return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

#         if post.author != request.user:
#             return Response({"error": "You can only delete your own posts."}, status=status.HTTP_403_FORBIDDEN)

#         post.delete()
#         return Response({"message": "Post deleted."}, status=status.HTTP_200_OK)
    
#     def patch(self, request, post_id):
#         try:
#             post = Post.objects.get(id=post_id)
#         except Post.DoesNotExist:
#             return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)
    
#         if post.author != request.user:
#             return Response({"error": "You can only edit your own posts."}, status=status.HTTP_403_FORBIDDEN)
    
#         caption = request.data.get('caption', '').strip()
#         description = request.data.get('description', '').strip()
#         post.caption = caption
#         post.description = description
#         post.save()
#         return Response(serialize_post(post, request.user), status=status.HTTP_200_OK)


# class LikeToggleView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, post_id):
#         # # Customers cannot like
#         # if request.user.role == 'customer':
#         #     return Response(
#         #         {"error": "Customers can only view posts."},
#         #         status=status.HTTP_403_FORBIDDEN
#         #     )

#         try:
#             post = Post.objects.get(id=post_id)
#         except Post.DoesNotExist:
#             return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

#         like, created = Like.objects.get_or_create(post=post, user=request.user)
#         if not created:
#             like.delete()
#             return Response({"liked": False, "likes_count": post.likes_count()})

#         return Response({"liked": True, "likes_count": post.likes_count()})


# class CommentCreateView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, post_id):
#         # Customers cannot comment
#         # if request.user.role == 'customer':
#         #     return Response(
#         #         {"error": "Customers can only view posts."},
#         #         status=status.HTTP_403_FORBIDDEN
#         #     )

#         try:
#             post = Post.objects.get(id=post_id)
#         except Post.DoesNotExist:
#             return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

#         text = request.data.get('text', '').strip()
#         if not text:
#             return Response({"error": "Comment cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

#         comment = Comment.objects.create(post=post, author=request.user, text=text)
#         return Response({
#             "id": comment.id,
#             "author_name": comment.author.get_full_name() or comment.author.email,
#             "author_role": comment.author.role,
#             "text": comment.text,
#             "created_at": comment.created_at.isoformat(),
#         }, status=status.HTTP_201_CREATED)

#     def delete(self, request, post_id):
#         comment_id = request.data.get('comment_id')
#         try:
#             comment = Comment.objects.get(id=comment_id, post_id=post_id)
#         except Comment.DoesNotExist:
#             return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)

#         if comment.author != request.user:
#             return Response({"error": "You can only delete your own comments."}, status=status.HTTP_403_FORBIDDEN)

#         comment.delete()
#         return Response({"message": "Comment deleted."})

from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser

import boto3
import uuid
import os
import logging
import requests as http_requests
from botocore.exceptions import ClientError
from django.conf import settings

from .models import Post, PostMedia, Like, Comment
from .permissions import IsDesignerOrTailor

User = get_user_model()
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────
# Helper: fire a notification for post activity
# Calls the notifications app's internal endpoint
# ─────────────────────────────────────────────────────────

def _trigger_post_notification(activity_type, post, actor):
    """
    Sends a POST to the internal notifications endpoint.
    activity_type: 'like' | 'comment'
    """
    # Don't notify when you interact with your own post
    if post.author == actor:
        return

    try:
        from notifications_app.models import FCMToken, Notification
        from notifications_app.tasks import send_notification_via_lambda

        actor_name = actor.get_full_name().strip() or actor.email

        # Get actor avatar safely
        actor_avatar = None
        for attr in ('profile_picture', 'avatar', 'photo', 'picture'):
            val = getattr(actor, attr, None)
            if val:
                try:
                    actor_avatar = val.url
                except Exception:
                    actor_avatar = str(val)
                break

        if activity_type == 'like':
            title = f"{actor_name} liked your post"
            body  = "Tap to see the post"
            notif_type_data = 'like'
        else:  # comment
            title = f"{actor_name} commented on your post"
            body  = "Tap to see the comment"
            notif_type_data = 'comment'

        data = {
            'type':          notif_type_data,
            'post_id':       post.id,
            'actor_id':      actor.id,
            'sender_name':   actor_name,
            'sender_avatar': actor_avatar or '',
        }
        click_action = f"/feed?post={post.id}"

        # Create the in-app notification record
        notification = Notification.objects.create(
            sender=actor,
            recipient=post.author,
            title=title,
            body=body,
            data=data,
            click_action=click_action,
            notification_type='personal',
        )

        # Fire the push notification via Lambda if recipient has FCM token
        try:
            fcm = FCMToken.objects.get(user=post.author)
            send_notification_via_lambda.delay(
                action='send_to_user',
                fcm_token=fcm.token,
                title=title,
                body=body,
                data=data,
                click_action=click_action,
                notification_ids=[notification.id],
            )
        except FCMToken.DoesNotExist:
            # No push token — in-app notification still saved
            notification.status = 'sent'
            notification.save(update_fields=['status'])

    except Exception as e:
        # Never let notification errors break the like/comment response
        logger.error(f"Failed to send {activity_type} notification: {e}")


def _trigger_new_post_notification(post, follower_ids):
    """
    Notify followers when a designer/tailor publishes a new post.
    follower_ids: list of user IDs who follow the author
    """
    if not follower_ids:
        return
    try:
        from notifications_app.models import FCMToken, Notification
        from notifications_app.tasks import send_notification_via_lambda

        author      = post.author
        author_name = author.get_full_name().strip() or author.email

        author_avatar = None
        for attr in ('profile_picture', 'avatar', 'photo', 'picture'):
            val = getattr(author, attr, None)
            if val:
                try:
                    author_avatar = val.url
                except Exception:
                    author_avatar = str(val)
                break

        title        = f"{author_name} posted something new"
        body         = "Tap to see the latest post"
        click_action = f"/feed?post={post.id}"
        data         = {
            'type':          'new_post',
            'post_id':       post.id,
            'user_id':       author.id,
            'sender_name':   author_name,
            'sender_avatar': author_avatar or '',
        }

        followers = User.objects.filter(id__in=follower_ids)
        for follower in followers:
            if follower == author:
                continue
            notif = Notification.objects.create(
                sender=author,
                recipient=follower,
                title=title,
                body=body,
                data=data,
                click_action=click_action,
                notification_type='announcement',
            )
            try:
                fcm = FCMToken.objects.get(user=follower)
                send_notification_via_lambda.delay(
                    action='send_to_user',
                    fcm_token=fcm.token,
                    title=title,
                    body=body,
                    data=data,
                    click_action=click_action,
                    notification_ids=[notif.id],
                )
            except FCMToken.DoesNotExist:
                notif.status = 'sent'
                notif.save(update_fields=['status'])

    except Exception as e:
        logger.error(f"Failed to send new-post notifications: {e}")


# ─────────────────────────────────────────────────────────
# Serializer helper
# ─────────────────────────────────────────────────────────

def serialize_post(post, request_user):
    media = [
        {
            "id": m.id,
            "media_type": m.media_type,
            "file_url": m.file.url,
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
        "description": post.description,
        "media": media,
        "likes_count": post.likes_count(),
        "comments_count": post.comments_count(),
        "comments": comments,
        "user_liked": user_liked,
        "is_owner": post.author == request_user,
        "created_at": post.created_at.isoformat(),
    }


# ─────────────────────────────────────────────────────────
# Views
# ─────────────────────────────────────────────────────────

class GeneratePresignedURLView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request):
        if request.user.role not in ['designer', 'tailor']:
            return Response({"error": "Only designers and tailors can upload media."}, status=status.HTTP_403_FORBIDDEN)

        files = request.data.get('files', [])
        if not files or not isinstance(files, list):
            return Response({"error": "'files' must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)

        ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
        ALLOWED_VIDEO_TYPES = {'video/mp4', 'video/quicktime', 'video/webm'}
        ALLOWED_CONTENT_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES

        s3 = boto3.client('s3',
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        presigned_urls = []

        for item in files:
            filename     = item.get('filename', '').strip()
            content_type = item.get('content_type', '').strip()

            if not filename or not content_type:
                return Response({"error": "Each file needs 'filename' and 'content_type'."}, status=status.HTTP_400_BAD_REQUEST)
            if content_type not in ALLOWED_CONTENT_TYPES:
                return Response({"error": f"Unsupported type: {content_type}"}, status=status.HTTP_400_BAD_REQUEST)

            media_type = 'video' if content_type in ALLOWED_VIDEO_TYPES else 'image'
            ext   = os.path.splitext(filename)[-1].lower()
            s3_key = f"posts/{uuid.uuid4().hex}{ext}"

            try:
                upload_url = s3.generate_presigned_url('put_object',
                    Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': s3_key, 'ContentType': content_type},
                    ExpiresIn=300,
                )
            except ClientError as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            presigned_urls.append({"upload_url": upload_url, "s3_key": s3_key, "media_type": media_type})

        return Response({"presigned_urls": presigned_urls}, status=status.HTTP_200_OK)


class PostListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request):
        posts = Post.objects.prefetch_related('media', 'likes', 'comments__author').all()
        data  = [serialize_post(p, request.user) for p in posts]
        return Response({"posts": data, "count": len(data)})

    def post(self, request):
        if request.user.role not in ['designer', 'tailor']:
            return Response(
                {"error": "Only designers and tailors can create posts."},
                status=status.HTTP_403_FORBIDDEN,
            )

        caption     = request.data.get('caption', '').strip()
        description = request.data.get('description', '').strip()
        media_items = request.data.get('media', [])
        # Optional: list of follower user IDs to notify (passed from frontend or resolved here)
        follower_ids = request.data.get('follower_ids', [])

        if not caption and not media_items:
            return Response(
                {"error": "Post must have a caption or at least one media file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        post = Post.objects.create(author=request.user, caption=caption, description=description)

        for i, item in enumerate(media_items):
            PostMedia.objects.create(post=post, file=item['s3_key'], media_type=item['media_type'], order=i)

        # Notify followers about the new post
        if follower_ids:
            _trigger_new_post_notification(post, follower_ids)

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

    def patch(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        if post.author != request.user:
            return Response({"error": "You can only edit your own posts."}, status=status.HTTP_403_FORBIDDEN)

        post.caption     = request.data.get('caption', '').strip()
        post.description = request.data.get('description', '').strip()
        post.save()
        return Response(serialize_post(post, request.user), status=status.HTTP_200_OK)


class LikeToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        try:
            post = Post.objects.select_related('author').get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        like, created = Like.objects.get_or_create(post=post, user=request.user)

        if not created:
            # Unlike — no notification needed
            like.delete()
            return Response({"liked": False, "likes_count": post.likes_count()})

        # New like — notify post author
        _trigger_post_notification('like', post, actor=request.user)

        return Response({"liked": True, "likes_count": post.likes_count()})


class CommentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        try:
            post = Post.objects.select_related('author').get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        text = request.data.get('text', '').strip()
        if not text:
            return Response({"error": "Comment cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        comment = Comment.objects.create(post=post, author=request.user, text=text)

        # Notify post author about the new comment
        _trigger_post_notification('comment', post, actor=request.user)

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