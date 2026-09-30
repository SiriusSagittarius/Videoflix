from django.contrib import admin

from video_app.models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Upload and manage videos in the Django admin."""

    list_display = ("title", "category", "created_at", "is_converted")
    list_filter = ("category", "is_converted")
    search_fields = ("title", "description")
    readonly_fields = ("created_at", "thumbnail", "is_converted")

    def get_readonly_fields(self, request, obj=None):
        """Lock the file after the upload, a new file needs a new video.

        The HLS files are only created once, so a replaced file would
        never be converted.
        """
        if obj is None:
            return self.readonly_fields
        return self.readonly_fields + ("video_file",)
