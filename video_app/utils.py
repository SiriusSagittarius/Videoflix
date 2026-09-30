import subprocess
from pathlib import Path

from django.conf import settings

from video_app.models import Video

THUMBNAIL_DIR = "thumbnails"
THUMBNAIL_WIDTH = 640


def build_thumbnail_command(source, target):
    """Return the ffmpeg command that saves a typical frame as JPEG."""
    return [
        "ffmpeg", "-y", "-i", str(source),
        "-vf", f"thumbnail,scale={THUMBNAIL_WIDTH}:-2",
        "-frames:v", "1",
        str(target),
    ]


def create_thumbnail(video):
    """Create the thumbnail of a video with ffmpeg and store its path."""
    relative_path = f"{THUMBNAIL_DIR}/{video.pk}.jpg"
    target = Path(settings.MEDIA_ROOT) / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    command = build_thumbnail_command(video.video_file.path, target)
    subprocess.run(command, check=True, capture_output=True)
    video.thumbnail.name = relative_path
    video.save(update_fields=["thumbnail"])


def process_video(video_id):
    """Background job: prepare a newly uploaded video for streaming."""
    video = Video.objects.get(pk=video_id)
    create_thumbnail(video)
