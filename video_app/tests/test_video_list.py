from rest_framework import status

from video_app.models import Video
from video_app.tests.helpers import MediaTestCase, create_video

URL = "/api/video/"
FIELDS = {
    "id", "created_at", "title", "description", "thumbnail_url", "category",
}


class VideoListTests(MediaTestCase):
    """GET /api/video/"""

    def setUp(self):
        """Log a user in."""
        super().setUp()
        self.log_in()

    def test_requires_login(self):
        """Without a login the list is not available."""
        self.client.cookies.clear()
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lists_converted_videos_newest_first(self):
        """Only converted videos are listed, the newest one first."""
        create_video("Alt")
        create_video("Neu")
        create_video("Wird noch umgewandelt", is_converted=False)
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([v["title"] for v in response.data], ["Neu", "Alt"])
        self.assertEqual(set(response.data[0]), FIELDS)

    def test_thumbnail_url_is_absolute_or_none(self):
        """The frontend needs a full URL, a missing thumbnail is None."""
        create_video("Mit Bild", thumbnail="thumbnails/1.jpg")
        create_video("Ohne Bild")
        response = self.client.get(URL)
        urls = {v["title"]: v["thumbnail_url"] for v in response.data}
        self.assertEqual(
            urls["Mit Bild"], "http://testserver/media/thumbnails/1.jpg"
        )
        self.assertIsNone(urls["Ohne Bild"])

    def test_list_is_cached_until_a_video_changes(self):
        """The cached list is used until a video is saved again."""
        video = create_video("Original")
        self.client.get(URL)
        Video.objects.filter(pk=video.pk).update(title="Ohne Signal")
        self.assertEqual(self.client.get(URL).data[0]["title"], "Original")
        video.title = "Gespeichert"
        video.save()
        self.assertEqual(self.client.get(URL).data[0]["title"], "Gespeichert")

    def test_browser_does_not_cache_the_list(self):
        """No cache headers, so the list is gone after a logout."""
        response = self.client.get(URL)
        self.assertNotIn("Cache-Control", response.headers)
        self.assertNotIn("Expires", response.headers)
