from django.http import FileResponse, Http404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView

from video_app.api.serializers import VideoSerializer
from video_app.models import Video
from video_app.utils import get_hls_file

VIDEO_LIST_CACHE_SECONDS = 60 * 15
PLAYLIST_TYPE = "application/vnd.apple.mpegurl"
SEGMENT_TYPE = "video/MP2T"


class VideoListView(ListAPIView):
    """List all converted videos, newest first, for logged in users."""

    queryset = Video.objects.filter(is_converted=True)
    serializer_class = VideoSerializer

    @method_decorator(cache_page(VIDEO_LIST_CACHE_SECONDS))
    def get(self, request, *args, **kwargs):
        """Return the video list from the Redis cache if possible."""
        return super().get(request, *args, **kwargs)


class HlsPlaylistView(APIView):
    """Deliver the HLS playlist of a video in one resolution."""

    def get(self, request, movie_id, resolution):
        """Return the index.m3u8 file or 404 if it does not exist."""
        path = get_hls_file(movie_id, resolution, "index.m3u8")
        if path is None:
            raise Http404("Video or playlist not found.")
        return FileResponse(path.open("rb"), content_type=PLAYLIST_TYPE)


class HlsSegmentView(APIView):
    """Deliver one HLS segment of a video in one resolution."""

    def get(self, request, movie_id, resolution, segment):
        """Return the .ts segment or 404 if it does not exist."""
        path = get_hls_file(movie_id, resolution, segment)
        if path is None:
            raise Http404("Video or segment not found.")
        return FileResponse(path.open("rb"), content_type=SEGMENT_TYPE)
