from rest_framework import status

from video_app.tests.helpers import (
    MediaTestCase,
    create_hls_files,
    create_video,
)


class HlsStreamingTests(MediaTestCase):
    """GET /api/video/<movie_id>/<resolution>/index.m3u8 and segments."""

    def setUp(self):
        """Log a user in and create a video with HLS files."""
        super().setUp()
        self.log_in()
        self.video = create_video()
        create_hls_files(self.video)
        self.base_url = f"/api/video/{self.video.pk}/480p"

    def get_file(self, url):
        """Request a file and return the response and its content.

        Reading the streaming content also closes the file, the test
        client takes care of that.
        """
        response = self.client.get(url)
        content = b"".join(getattr(response, "streaming_content", []))
        return response, content

    def test_returns_playlist(self):
        """The playlist is sent with the HLS content type."""
        response, content = self.get_file(f"{self.base_url}/index.m3u8")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response["Content-Type"], "application/vnd.apple.mpegurl"
        )
        self.assertTrue(content.startswith(b"#EXTM3U"))

    def test_returns_segment_with_and_without_slash(self):
        """The documented URL and the URL used by hls.js both work."""
        for url in (f"{self.base_url}/000.ts/", f"{self.base_url}/000.ts"):
            with self.subTest(url=url):
                response, content = self.get_file(url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response["Content-Type"], "video/MP2T")
                self.assertEqual(content, b"segment")

    def test_returns_404_for_unknown_files(self):
        """Unknown videos, resolutions, segments and paths give 404."""
        urls = [
            "/api/video/999/480p/index.m3u8",
            f"/api/video/{self.video.pk}/360p/index.m3u8",
            f"{self.base_url}/001.ts",
            f"/api/video/{self.video.pk}/../index.m3u8",
        ]
        for url in urls:
            with self.subTest(url=url):
                response, _ = self.get_file(url)
                self.assertEqual(response.status_code, 404)

    def test_requires_login(self):
        """Playlists and segments are only for logged in users."""
        self.client.cookies.clear()
        for url in (f"{self.base_url}/index.m3u8", f"{self.base_url}/000.ts"):
            with self.subTest(url=url):
                response, _ = self.get_file(url)
                self.assertEqual(response.status_code, 401)
