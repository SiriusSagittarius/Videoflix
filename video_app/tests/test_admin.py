from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from video_app.models import Video
from video_app.tests.helpers import MediaTestCase, create_video

ADD_URL = "/admin/video_app/video/add/"


class VideoAdminTests(MediaTestCase):
    """Uploading and editing videos in the Django admin."""

    def setUp(self):
        """Log the admin in."""
        super().setUp()
        admin = User.objects.create_superuser(
            "admin", "admin@example.com", "adminpassword"
        )
        self.client.force_login(admin)

    def test_rejects_files_that_are_no_videos(self):
        """Only video formats can be uploaded."""
        data = {
            "title": "Notizen", "description": "x", "category": "Test",
            "video_file": SimpleUploadedFile("notizen.txt", b"text"),
        }
        response = self.client.post(ADD_URL, data)
        self.assertContains(response, "File extension")
        self.assertFalse(Video.objects.exists())

    def test_video_file_is_locked_after_upload(self):
        """A new video has an upload field, an existing one does not."""
        video = create_video()
        change_url = f"/admin/video_app/video/{video.pk}/change/"
        self.assertContains(self.client.get(ADD_URL), 'name="video_file"')
        self.assertNotContains(
            self.client.get(change_url), 'name="video_file"'
        )

    def test_title_is_shown_for_a_video(self):
        """Admin and shell show a video by its title."""
        self.assertEqual(str(create_video("Mein Film")), "Mein Film")
