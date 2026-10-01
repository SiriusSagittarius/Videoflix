import shutil
import subprocess
from pathlib import Path
from unittest import skipUnless

from django.conf import settings
from django.test import SimpleTestCase

from video_app.models import Video
from video_app.tests.helpers import MediaTestCase
from video_app.utils import (
    HLS_RESOLUTIONS,
    build_hls_command,
    build_thumbnail_command,
    get_hls_dir,
    process_video,
)

TEST_VIDEO = "videos/clip.mp4"
TEST_SOURCE = "testsrc2=duration=2:size=640x360:rate=25"


def create_real_video():
    """Let FFmpeg create a short test video and store it as a Video."""
    target = Path(settings.MEDIA_ROOT) / TEST_VIDEO
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", TEST_SOURCE,
        "-pix_fmt", "yuv420p", str(target),
    ]
    subprocess.run(command, check=True, capture_output=True)
    return Video.objects.create(
        title="Echtes Video", description="FFmpeg", category="Other",
        video_file=TEST_VIDEO,
    )


def read_video_height(path):
    """Return the height of the first video stream of a file.

    For .ts files ffprobe prints the value once for the program and once
    for the stream, so only the first value is used.
    """
    command = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=height", "-of", "csv=p=0", str(path),
    ]
    result = subprocess.run(command, check=True, capture_output=True)
    return int(result.stdout.decode().split()[0])


class FfmpegCommandTests(SimpleTestCase):
    """The FFmpeg commands that are built for a video."""

    def test_thumbnail_command(self):
        """The thumbnail is a typical frame, scaled to 640 pixels."""
        command = build_thumbnail_command("in.mp4", "out.jpg")
        self.assertEqual(command[:4], ["ffmpeg", "-y", "-i", "in.mp4"])
        self.assertIn("thumbnail,scale=640:-2", command)
        self.assertEqual(command[-1], "out.jpg")

    def test_hls_command(self):
        """The HLS command scales the video and names the segments."""
        target_dir = Path("out")
        command = build_hls_command("in.mp4", target_dir, 720, "2800k")
        self.assertIn("scale=-2:720", command)
        self.assertIn("2800k", command)
        self.assertIn(str(target_dir / "%03d.ts"), command)
        self.assertEqual(command[-1], str(target_dir / "index.m3u8"))


@skipUnless(shutil.which("ffmpeg"), "FFmpeg is not installed")
class ProcessVideoTests(MediaTestCase):
    """The background job with real FFmpeg runs."""

    def test_creates_thumbnail_and_all_hls_streams(self):
        """A processed video has a thumbnail and three HLS resolutions."""
        video = create_real_video()
        process_video(video.pk)
        video.refresh_from_db()
        self.assertTrue(video.is_converted)
        self.assertTrue(Path(video.thumbnail.path).is_file())
        for resolution, options in HLS_RESOLUTIONS.items():
            with self.subTest(resolution=resolution):
                folder = get_hls_dir(video.pk, resolution)
                self.assertTrue((folder / "index.m3u8").is_file())
                height = read_video_height(folder / "000.ts")
                self.assertEqual(height, options["height"])
