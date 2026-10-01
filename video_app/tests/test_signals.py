from pathlib import Path
from unittest.mock import patch

from django.conf import settings

from video_app.tests.helpers import (
    MediaTestCase,
    create_hls_files,
    create_video,
)
from video_app.utils import process_video

THUMBNAIL = "thumbnails/test.jpg"


def create_thumbnail_file():
    """Write a dummy thumbnail into the media folder."""
    path = Path(settings.MEDIA_ROOT) / THUMBNAIL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"jpg")
    return path


@patch("django_rq.get_queue")
class VideoSignalTests(MediaTestCase):
    """Processing and cleanup that run when videos are saved or deleted."""

    def test_new_video_is_queued_after_commit(self, get_queue):
        """A new video starts the processing job once it is saved."""
        with self.captureOnCommitCallbacks(execute=True):
            video = create_video(is_converted=False)
        get_queue.assert_called_once_with("video")
        get_queue.return_value.enqueue.assert_called_once_with(
            process_video, video.pk
        )

    def test_changed_video_is_not_processed_again(self, get_queue):
        """Editing the title of a video does not start a new job."""
        video = create_video()
        with self.captureOnCommitCallbacks(execute=True):
            video.title = "Neuer Titel"
            video.save()
        get_queue.assert_not_called()

    def test_deleting_video_removes_all_files(self, get_queue):
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
