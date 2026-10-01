import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from video_app.models import Video
from video_app.utils import get_hls_dir

MEDIA_DIR = tempfile.mkdtemp(prefix="videoflix-tests-")
TEST_CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}
TEST_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}


@override_settings(
    MEDIA_ROOT=MEDIA_DIR, CACHES=TEST_CACHES, STORAGES=TEST_STORAGES
)
class MediaTestCase(APITestCase):
    """Test case with its own media folder and an in-memory cache.

    Real videos, the Redis cache and the collected static files stay
    untouched by the tests.
    """

    def setUp(self):
        """Start every test with an empty cache."""
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary media folder."""
        super().tearDownClass()
        shutil.rmtree(MEDIA_DIR, ignore_errors=True)

    def log_in(self):
        """Create a user and give the client a valid access cookie."""
        user = User.objects.create_user("max@example.com", "max@example.com")
        self.client.cookies["access_token"] = str(AccessToken.for_user(user))
        return user


def create_video(title="Testvideo", is_converted=True, **fields):
    """Create a video with a small dummy file."""
    upload = SimpleUploadedFile(f"{title}.mp4", b"not a real video")
    return Video.objects.create(
        title=title, description="Beschreibung", category="Drama",
        video_file=upload, is_converted=is_converted, **fields,
    )


def create_hls_files(video, resolution="480p"):
    """Write a playlist and one segment like FFmpeg creates them."""
    folder = get_hls_dir(video.pk, resolution)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "index.m3u8").write_text("#EXTM3U\n000.ts\n")
    (folder / "000.ts").write_bytes(b"segment")
    return folder
