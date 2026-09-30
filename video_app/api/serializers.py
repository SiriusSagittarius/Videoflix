from rest_framework import serializers

from video_app.models import Video


class VideoSerializer(serializers.ModelSerializer):
    """Video data for the dashboard with an absolute thumbnail URL."""

    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            "id", "created_at", "title", "description", "thumbnail_url",
            "category",
        ]

    def get_thumbnail_url(self, video):
        """Return the full URL of the thumbnail or None if there is none."""
        if not video.thumbnail:
            return None
        return self.context["request"].build_absolute_uri(video.thumbnail.url)
