from django.contrib.auth import get_user_model
from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import (
    GeneralReview, GeneralReviewMention, GeneralReviewReply,
    ProfileReview, ProfileReviewReply
)

User = get_user_model()


def serialize_general_review(review, request_user=None):
    mentions = [
        {
            "user_id": m.mentioned_user.id,
            "name": m.mentioned_user.get_full_name() or m.mentioned_user.email,
            "role": m.mentioned_user.role,
            "avatar": m.mentioned_user.profile_picture,
        }
        for m in review.mentions.select_related('mentioned_user').all()
    ]
    replies = [
        {
            "id": r.id,
            "author_id": r.author.id,
            "author_name": r.author.get_full_name() or r.author.email,
            "author_role": r.author.role,
            "author_avatar": r.author.profile_picture,
            "text": r.text,
            "created_at": r.created_at.isoformat(),
            "is_owner": request_user and r.author == request_user,
        }
        for r in review.replies.select_related('author').all()
    ]
    return {
        "id": review.id,
        "author_id": review.author.id,
        "author_name": review.author.get_full_name() or review.author.email,
        "author_role": review.author.role,
        "author_avatar": review.author.profile_picture,
        "text": review.text,
        "rating": review.rating,
        "mentions": mentions,
        "replies": replies,
        "created_at": review.created_at.isoformat(),
        "is_owner": request_user and review.author == request_user,
    }


def serialize_profile_review(review, request_user=None):
    reply = None
    if hasattr(review, 'reply'):
        reply = {
            "id": review.reply.id,
            "author_id": review.reply.author.id,
            "author_name": review.reply.author.get_full_name() or review.reply.author.email,
            "text": review.reply.text,
            "created_at": review.reply.created_at.isoformat(),
            "is_owner": request_user and review.reply.author == request_user,
        }
    return {
        "id": review.id,
        "reviewer_id": review.reviewer.id,
        "reviewer_name": review.reviewer.get_full_name() or review.reviewer.email,
        "reviewer_avatar": review.reviewer.profile_picture,
        "text": review.text,
        "rating": review.rating,
        "reply": reply,
        "created_at": review.created_at.isoformat(),
        "is_owner": request_user and review.reviewer == request_user,
    }


# ── General Reviews ──────────────────────────────────────────────────────────

class GeneralReviewListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        reviews = GeneralReview.objects.prefetch_related(
            'mentions__mentioned_user', 'replies__author'
        ).select_related('author').all()
        user = request.user if request.user.is_authenticated else None
        data = [serialize_general_review(r, user) for r in reviews]
        return Response({"reviews": data, "count": len(data)})

    def post(self, request):
        text = request.data.get('text', '').strip()
        rating = request.data.get('rating')
        mention_ids = request.data.get('mention_ids', [])  # list of user IDs

        if not text:
            return Response({"error": "Review text is required."}, status=400)
        if not rating or int(rating) not in range(1, 6):
            return Response({"error": "Rating must be between 1 and 5."}, status=400)

        review = GeneralReview.objects.create(
            author=request.user,
            text=text,
            rating=int(rating)
        )

        # Handle mentions
        for uid in mention_ids:
            try:
                mentioned_user = User.objects.get(
                    id=uid, role__in=['designer', 'tailor', 'boutique']
                )
                GeneralReviewMention.objects.create(
                    review=review, mentioned_user=mentioned_user
                )
            except User.DoesNotExist:
                pass

        return Response(
            serialize_general_review(review, request.user),
            status=status.HTTP_201_CREATED
        )


class GeneralReviewEditView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, review_id):
        try:
            review = GeneralReview.objects.get(id=review_id)
        except GeneralReview.DoesNotExist:
            return Response({"error": "Review not found."}, status=404)

        if review.author != request.user:
            return Response({"error": "You can only edit your own reviews."}, status=403)

        text = request.data.get('text', '').strip()
        rating = request.data.get('rating')
        mention_ids = request.data.get('mention_ids', [])

        if text:
            review.text = text
        if rating and int(rating) in range(1, 6):
            review.rating = int(rating)
        review.save()

        # Update mentions
        if mention_ids is not None:
            review.mentions.all().delete()
            for uid in mention_ids:
                try:
                    mentioned_user = User.objects.get(
                        id=uid, role__in=['designer', 'tailor', 'boutique']
                    )
                    GeneralReviewMention.objects.create(
                        review=review, mentioned_user=mentioned_user
                    )
                except User.DoesNotExist:
                    pass

        return Response(serialize_general_review(review, request.user))

    def delete(self, request, review_id):
        try:
            review = GeneralReview.objects.get(id=review_id)
        except GeneralReview.DoesNotExist:
            return Response({"error": "Review not found."}, status=404)

        if review.author != request.user:
            return Response({"error": "You can only delete your own reviews."}, status=403)

        review.delete()
        return Response({"message": "Review deleted."})


class GeneralReviewReplyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):
        try:
            review = GeneralReview.objects.get(id=review_id)
        except GeneralReview.DoesNotExist:
            return Response({"error": "Review not found."}, status=404)

        text = request.data.get('text', '').strip()
        if not text:
            return Response({"error": "Reply text is required."}, status=400)

        reply = GeneralReviewReply.objects.create(
            review=review, author=request.user, text=text
        )
        return Response({
            "id": reply.id,
            "author_name": reply.author.get_full_name() or reply.author.email,
            "text": reply.text,
            "created_at": reply.created_at.isoformat(),
        }, status=201)


class GeneralReviewReplyEditView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, review_id, reply_id):
        try:
            reply = GeneralReviewReply.objects.get(id=reply_id, review_id=review_id)
        except GeneralReviewReply.DoesNotExist:
            return Response({"error": "Reply not found."}, status=404)

        if reply.author != request.user:
            return Response({"error": "You can only edit your own replies."}, status=403)

        text = request.data.get('text', '').strip()
        if text:
            reply.text = text
            reply.save()

        return Response({"id": reply.id, "text": reply.text})

    def delete(self, request, review_id, reply_id):
        try:
            reply = GeneralReviewReply.objects.get(id=reply_id, review_id=review_id)
        except GeneralReviewReply.DoesNotExist:
            return Response({"error": "Reply not found."}, status=404)

        if reply.author != request.user:
            return Response({"error": "You can only delete your own replies."}, status=403)

        reply.delete()
        return Response({"message": "Reply deleted."})


# ── Profile Reviews ──────────────────────────────────────────────────────────

class ProfileReviewListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, user_id):
        try:
            reviewed_user = User.objects.get(
                id=user_id, role__in=['designer', 'tailor', 'boutique']
            )
        except User.DoesNotExist:
            return Response({"error": "Designer/tailor not found."}, status=404)

        reviews = ProfileReview.objects.filter(
            reviewed_user=reviewed_user
        ).select_related('reviewer', 'reply__author')

        user = request.user if request.user.is_authenticated else None
        data = [serialize_profile_review(r, user) for r in reviews]

        # Average rating
        avg = sum(r.rating for r in reviews) / len(reviews) if reviews else 0

        return Response({
            "reviewed_user": {
                "id": reviewed_user.id,
                "name": reviewed_user.get_full_name(),
                "role": reviewed_user.role,
                "avatar": reviewed_user.profile_picture,
            },
            "average_rating": round(avg, 1),
            "reviews": data,
            "count": len(data),
        })

    def post(self, request, user_id):
        # Only customers can write profile reviews
        if request.user.role != 'customer':
            return Response(
                {"error": "Only customers can write profile reviews."},
                status=403
            )

        try:
            reviewed_user = User.objects.get(
                id=user_id, role__in=['designer', 'tailor', 'boutique']
            )
        except User.DoesNotExist:
            return Response({"error": "Designer/tailor not found."}, status=404)

        if reviewed_user == request.user:
            return Response({"error": "You cannot review yourself."}, status=400)

        if ProfileReview.objects.filter(
            reviewer=request.user, reviewed_user=reviewed_user
        ).exists():
            return Response(
                {"error": "You have already reviewed this person."},
                status=400
            )

        text = request.data.get('text', '').strip()
        rating = request.data.get('rating')

        if not text:
            return Response({"error": "Review text is required."}, status=400)
        if not rating or int(rating) not in range(1, 6):
            return Response({"error": "Rating must be between 1 and 5."}, status=400)

        review = ProfileReview.objects.create(
            reviewer=request.user,
            reviewed_user=reviewed_user,
            text=text,
            rating=int(rating)
        )
        return Response(
            serialize_profile_review(review, request.user),
            status=201
        )


class ProfileReviewEditView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, review_id):
        try:
            review = ProfileReview.objects.get(id=review_id)
        except ProfileReview.DoesNotExist:
            return Response({"error": "Review not found."}, status=404)

        if review.reviewer != request.user:
            return Response({"error": "You can only edit your own reviews."}, status=403)

        text = request.data.get('text', '').strip()
        rating = request.data.get('rating')

        if text:
            review.text = text
        if rating and int(rating) in range(1, 6):
            review.rating = int(rating)
        review.save()

        return Response(serialize_profile_review(review, request.user))

    def delete(self, request, review_id):
        try:
            review = ProfileReview.objects.get(id=review_id)
        except ProfileReview.DoesNotExist:
            return Response({"error": "Review not found."}, status=404)

        if review.reviewer != request.user:
            return Response({"error": "You can only delete your own reviews."}, status=403)

        review.delete()
        return Response({"message": "Review deleted."})


class ProfileReviewReplyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):
        try:
            review = ProfileReview.objects.get(id=review_id)
        except ProfileReview.DoesNotExist:
            return Response({"error": "Review not found."}, status=404)

        # Only the reviewed designer/tailor can reply
        if review.reviewed_user != request.user:
            return Response(
                {"error": "Only the reviewed person can reply."},
                status=403
            )

        if hasattr(review, 'reply'):
            return Response(
                {"error": "You have already replied to this review."},
                status=400
            )

        text = request.data.get('text', '').strip()
        if not text:
            return Response({"error": "Reply text is required."}, status=400)

        reply = ProfileReviewReply.objects.create(
            review=review, author=request.user, text=text
        )
        return Response({
            "id": reply.id,
            "text": reply.text,
            "created_at": reply.created_at.isoformat(),
        }, status=201)

    def put(self, request, review_id):
        try:
            review = ProfileReview.objects.get(id=review_id)
            reply = review.reply
        except (ProfileReview.DoesNotExist, ProfileReviewReply.DoesNotExist):
            return Response({"error": "Reply not found."}, status=404)

        if reply.author != request.user:
            return Response({"error": "You can only edit your own reply."}, status=403)

        text = request.data.get('text', '').strip()
        if text:
            reply.text = text
            reply.save()

        return Response({"id": reply.id, "text": reply.text})

    def delete(self, request, review_id):
        try:
            review = ProfileReview.objects.get(id=review_id)
            reply = review.reply
        except (ProfileReview.DoesNotExist, ProfileReviewReply.DoesNotExist):
            return Response({"error": "Reply not found."}, status=404)

        if reply.author != request.user:
            return Response({"error": "You can only delete your own reply."}, status=403)

        reply.delete()
        return Response({"message": "Reply deleted."})


# ── Search designers/tailors for mentions ────────────────────────────────────

class SearchDesignersView(APIView):
    """Search designers/tailors by name for mention suggestions."""
    permission_classes = [AllowAny]  # public — needed for mention dropdown

    def get(self, request):
        query = request.query_params.get('q', '').strip()

        base_qs = User.objects.filter(
            role__in=['designer', 'tailor', 'boutique'],
            is_active=True
        )

        # Empty query → return ALL designers/tailors (for @ with no text)
        if not query:
            users = base_qs[:20]
        else:
            users = base_qs.filter(
                models.Q(first_name__icontains=query) |
                models.Q(last_name__icontains=query) |
                models.Q(business_name__icontains=query)
            )[:10]

        data = [
            {
                "id": u.id,
                "name": u.get_full_name() or u.email,
                "business_name": u.business_name,
                "role": u.role,
                "avatar": u.profile_picture,
            }
            for u in users
        ]
        return Response({"users": data})