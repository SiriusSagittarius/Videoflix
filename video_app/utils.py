import subprocess
from pathlib import Path

from django.conf import settings

from video_app.models import Video

THUMBNAIL_DIR = "thumbnails"
THUMBNAIL_WIDTH = 640
HLS_DIR = "hls"
HLS_SEGMENT_SECONDS = 6
HLS_RESOLUTIONS = {
    "480p": {"height": 480, "max_bitrate": "1400k"},
    "720p": {"height": 720, "max_bitrate": "2800k"},
    "1080p": {"height": 1080, "max_bitrate": "5000k"},
}
PROCESSING_TIMEOUT = 60 * 60


def build_thumbnail_command(source, target):
    """Return the ffmpeg command that saves a typical frame as JPEG."""
    return [
        "ffmpeg", "-y", "-i", str(source),
        "-vf", f"thumbnail,scale={THUMBNAIL_WIDTH}:-2",
        "-frames:v", "1",
        str(target),
    ]


def build_hls_command(source, target_dir, height, max_bitrate):
    """Return the ffmpeg command that converts a video to one HLS stream."""
    return [
        "ffmpeg", "-y", "-i", str(source), "-vf", f"scale=-2:{height}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-maxrate", max_bitrate, "-bufsize", max_bitrate,
        "-force_key_frames", f"expr:gte(t,n_forced*{HLS_SEGMENT_SECONDS})",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2",
        "-hls_time", str(HLS_SEGMENT_SECONDS), "-hls_playlist_type", "vod",
        "-hls_segment_filename", str(target_dir / "%03d.ts"),
        str(target_dir / "index.m3u8"),
    ]


def get_hls_dir(video_id, resolution):
    """Return the folder with the HLS files of a video in one resolution."""
    return Path(settings.MEDIA_ROOT) / HLS_DIR / str(video_id) / resolution


def get_hls_file(video_id, resolution, file_name):
    """Return the path of an existing HLS file or None.

    Only known resolutions are allowed, so the URL cannot point to other
    folders on the server.
    """
    if resolution not in HLS_RESOLUTIONS:
        return None
    path = get_hls_dir(video_id, resolution) / file_name
    return path if path.is_file() else None


def create_thumbnail(video):
    """Create the thumbnail of a video with ffmpeg and store its path."""
    relative_path = f"{THUMBNAIL_DIR}/{video.pk}.jpg"
    target = Path(settings.MEDIA_ROOT) / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    command = build_thumbnail_command(video.video_file.path, target)
    subprocess.run(command, check=True, capture_output=True)
    video.thumbnail.name = relative_path
    video.save(update_fields=["thumbnail"])


def convert_to_hls(video, resolution):
    """Convert a video with ffmpeg to an HLS stream in one resolution."""
    target_dir = get_hls_dir(video.pk, resolution)
    target_dir.mkdir(parents=True, exist_ok=True)
    command = build_hls_command(
        video.video_file.path, target_dir, **HLS_RESOLUTIONS[resolution]
    )
    subprocess.run(command, check=True, capture_output=True)


def process_video(video_id):
    """Background job: prepare a newly uploaded video for streaming."""
    video = Video.objects.get(pk=video_id)
    create_thumbnail(video)
    for resolution in HLS_RESOLUTIONS:
        convert_to_hls(video, resolution)
    video.is_converted = True
    video.save(update_fields=["is_converted"])
