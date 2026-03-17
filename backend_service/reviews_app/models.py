from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class GeneralReview(models.Model):
    """Review about the Vestique platform — can mention designers/tailors."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='general_reviews'
    )
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'general_reviews'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.email} - {self.rating}★"


class GeneralReviewMention(models.Model):
    """Tracks which designers/tailors are mentioned in a general review."""

    review = models.ForeignKey(
        GeneralReview,
        on_delete=models.CASCADE,
        related_name='mentions'
    )
    mentioned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentioned_in_reviews'
    )

    class Meta:
        db_table = 'general_review_mentions'
        unique_together = ('review', 'mentioned_user')

    def __str__(self):
        return f"Review {self.review.id} mentions {self.mentioned_user.email}"


class GeneralReviewReply(models.Model):
    """Any logged-in user or mentioned designer/tailor can reply."""

    review = models.ForeignKey(
        GeneralReview,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='general_review_replies'
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'general_review_replies'
        ordering = ['created_at']

    def __str__(self):
        return f"Reply by {self.author.email} on review {self.review.id}"


class ProfileReview(models.Model):
    """Review written by a customer about a specific designer/tailor."""

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='written_profile_reviews'
    )
    reviewed_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_profile_reviews'
    )
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profile_reviews'
        ordering = ['-created_at']
        unique_together = ('reviewer', 'reviewed_user')  # one review per person

    def __str__(self):
        return f"{self.reviewer.email} → {self.reviewed_user.email} {self.rating}★"


class ProfileReviewReply(models.Model):
    """Only the reviewed designer/tailor can reply to their profile review."""

    review = models.OneToOneField(
        ProfileReview,
        on_delete=models.CASCADE,
        related_name='reply'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile_review_replies'
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profile_review_replies'

    def __str__(self):
        return f"Reply by {self.author.email} on profile review {self.review.id}"