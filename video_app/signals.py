from functools import partial

import django_rq
from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from video_app.models import Video
from video_app.utils import VIDEO_QUEUE, delete_video_files, process_video


def enqueue_processing(video_id):
    """Put the processing job into the video queue with its long timeout."""
    django_rq.get_queue(VIDEO_QUEUE).enqueue(process_video, video_id)


@receiver(post_save, sender=Video)
def queue_video_processing(sender, instance, created, **kwargs):
    """Start the background processing once a new video is saved."""
    if created:
        transaction.on_commit(partial(enqueue_processing, instance.pk))


@receiver(post_delete, sender=Video)
def delete_files_of_video(sender, instance, **kwargs):
    """Remove all files of a deleted video once the deletion is saved."""
    transaction.on_commit(partial(
        delete_video_files, instance.video_file, instance.thumbnail,
        instance.pk,
    ))


@receiver([post_save, post_delete], sender=Video)
def clear_cached_video_list(sender, **kwargs):
    """Empty the cache so changed videos show up in the list at once."""
    cache.clear()
