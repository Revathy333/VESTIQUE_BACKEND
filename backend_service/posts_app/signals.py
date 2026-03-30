"""
signals.py  —  place this inside your POSTS app (e.g. posts/signals.py)

Fires whenever a designer creates a new post and bulk-notifies
every other user who has an FCM token saved.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


# ─── Replace 'posts.Post' with your actual model path ───────────────────────
# e.g.  from posts.models import Post
#       from products.models import Product
from posts_app.models import Post          # ← CHANGE THIS to your Post model
# ────────────────────────────────────────────────────────────────────────────


@receiver(post_save, sender=Post)
def notify_all_users_on_new_post(sender, instance, created, **kwargs):
    """
    Triggered every time a Post is saved.
    Only acts on CREATION (not edits) and only when the author is a designer.
    """
    if not created:
        return  # skip edits/updates


    author = getattr(instance, 'user', None) or getattr(instance, 'author', None)

    if author is None:
        logger.warning(f"Post {instance.id} has no author field — skipping notification.")
        return

    if not getattr(author, 'is_designer', False):  # ← CHANGE condition to match your model
        return
    # ────────────────────────────────────────────────────────────────────────

    designer_name = author.get_full_name() or author.email
    post_title    = getattr(instance, 'title', '') or getattr(instance, 'caption', '') or 'New post'

    # Fire the Celery task asynchronously — does NOT block the upload request
    from notifications_app.tasks import notify_all_users_new_post_task
    notify_all_users_new_post_task.delay(
        post_id=instance.id,
        author_id=author.id,
        designer_name=designer_name,
        post_title=post_title,
    )

    logger.info(
        f"notify_all_users_new_post_task queued for post {instance.id} "
        f"by designer {author.id}"
    )