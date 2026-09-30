from django.db import models


class Video(models.Model):
    """A video with its metadata, the uploaded file and a thumbnail."""

    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=50)
    video_file = models.FileField(upload_to="videos/")
    thumbnail = models.FileField(upload_to="thumbnails/", blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        """Show the title in the admin and in the shell."""
        return self.title
