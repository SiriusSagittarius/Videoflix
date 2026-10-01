from django.core.validators import FileExtensionValidator
from django.db import models

VIDEO_EXTENSIONS = ["mp4", "mov", "mkv", "webm", "avi", "m4v"]


class Category(models.TextChoices):
    """Fixed categories, so uploads cannot create new spellings."""

    ACTION = "Action"
    COMEDY = "Comedy"
    DOCUMENTARY = "Documentary"
    DRAMA = "Drama"
    NATURE = "Nature"
    ROMANCE = "Romance"
    OTHER = "Other"


class Video(models.Model):
    """A video with its metadata, the uploaded file and a thumbnail."""

    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=Category.choices)
    video_file = models.FileField(
        upload_to="videos/",
        validators=[FileExtensionValidator(VIDEO_EXTENSIONS)],
    )
    thumbnail = models.FileField(upload_to="thumbnails/", blank=True)
    is_converted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        """Show the title in the admin and in the shell."""
        return self.title
