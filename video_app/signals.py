import django_rq
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from video_app.models import Video
from video_app.utils import PROCESSING_TIMEOUT, process_video


def enqueue_processing(video_id):
    """Queue the processing job with enough time for long videos."""
    django_rq.enqueue(
        process_video, video_id, job_timeout=PROCESSING_TIMEOUT
    )


@receiver(post_save, sender=Video)
def queue_video_processing(sender, instance, created, **kwargs):
    """Start the background processing once a new video is saved."""
    if created:
        transaction.on_commit(lambda: enqueue_processing(instance.pk))
