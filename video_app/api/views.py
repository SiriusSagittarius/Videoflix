from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.generics import ListAPIView

from video_app.api.serializers import VideoSerializer
from video_app.models import Video

VIDEO_LIST_CACHE_SECONDS = 60 * 15


class VideoListView(ListAPIView):
    """List all converted videos, newest first, for logged in users."""

    queryset = Video.objects.filter(is_converted=True)
    serializer_class = VideoSerializer

    @method_decorator(cache_page(VIDEO_LIST_CACHE_SECONDS))
    def get(self, request, *args, **kwargs):
        """Return the video list from the Redis cache if possible."""
        return super().get(request, *args, **kwargs)
