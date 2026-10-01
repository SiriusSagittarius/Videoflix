from pathlib import Path
from unittest.mock import patch

from django.conf import settings

from video_app.tests.helpers import (
    MediaTestCase,
    create_hls_files,
    create_video,
)
from video_app.utils import PROCESSING_TIMEOUT, process_video

THUMBNAIL = "thumbnails/test.jpg"


def create_thumbnail_file():
    """Write a dummy thumbnail into the media folder."""
    path = Path(settings.MEDIA_ROOT) / THUMBNAIL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"jpg")
    return path


@patch("django_rq.enqueue")
class VideoSignalTests(MediaTestCase):
    """Processing and cleanup that run when videos are saved or deleted."""

    def test_new_video_is_queued_after_commit(self, enqueue):
        """A new video starts the processing job once it is saved."""
        with self.captureOnCommitCallbacks(execute=True):
            video = create_video(is_converted=False)
        enqueue.assert_called_once_with(
            process_video, video.pk, job_timeout=PROCESSING_TIMEOUT
        )

    def test_changed_video_is_not_processed_again(self, enqueue):
        """Editing the title of a video does not start a new job."""
        video = create_video()
        with self.captureOnCommitCallbacks(execute=True):
            video.title = "Neuer Titel"
            video.save()
        enqueue.assert_not_called()

    def test_deleting_video_removes_all_files(self, enqueue):
        """Original file, thumbnail and HLS folder are deleted as well."""
        thumbnail = create_thumbnail_file()
        video = create_video(thumbnail=THUMBNAIL)
        original = Path(video.video_file.path)
        hls_root = create_hls_files(video).parent
        with self.captureOnCommitCallbacks(execute=True):
            video.delete()
        for path in (original, thumbnail, hls_root):
            with self.subTest(path=path.name):
                self.assertFalse(path.exists())
