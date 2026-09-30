from django.contrib import admin

from video_app.models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Upload and manage videos in the Django admin."""

    list_display = ("title", "category", "created_at", "is_converted")
    list_filter = ("category", "is_converted")
    search_fields = ("title", "description")
    readonly_fields = ("created_at", "thumbnail", "is_converted")
