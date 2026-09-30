import django_rq
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from video_app.models import Video
from video_app.utils import process_video


@receiver(post_save, sender=Video)
def queue_video_processing(sender, instance, created, **kwargs):
    """Start the background processing once a new video is saved."""
    if created:
        transaction.on_commit(
            lambda: django_rq.enqueue(process_video, instance.pk)
        )
