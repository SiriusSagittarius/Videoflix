from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from video_app.models import Category, Video
from video_app.tests.helpers import MediaTestCase, create_video

ADD_URL = "/admin/video_app/video/add/"


def upload_data(file_name="film.mp4", category="Other"):
    """Return the admin form data for uploading a video."""
    return {
        "title": "Upload", "description": "x", "category": category,
        "video_file": SimpleUploadedFile(file_name, b"video"),
    }


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
        response = self.client.post(ADD_URL, upload_data("notizen.txt"))
        self.assertContains(response, "File extension")
        self.assertFalse(Video.objects.exists())

    def test_category_is_a_dropdown_with_fixed_choices(self):
        """The admin offers exactly the fixed categories."""
        response = self.client.get(ADD_URL)
        self.assertContains(response, '<select name="category"')
        for category in Category.values:
            with self.subTest(category=category):
                self.assertContains(response, f'value="{category}"')

    def test_rejects_unknown_category(self):
        """A category outside the list cannot be saved."""
        response = self.client.post(ADD_URL, upload_data(category="Krimi"))
        self.assertContains(response, "Select a valid choice")
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
