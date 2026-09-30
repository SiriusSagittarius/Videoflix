from django.urls import path, re_path

from video_app.api.views import (
    HlsPlaylistView,
    HlsSegmentView,
    VideoListView,
)

urlpatterns = [
    path('video/', VideoListView.as_view(), name='video-list'),
    path(
        'video/<int:movie_id>/<str:resolution>/index.m3u8',
        HlsPlaylistView.as_view(),
        name='video-playlist',
    ),
    re_path(
        r'^video/(?P<movie_id>\d+)/(?P<resolution>[^/]+)/'
        r'(?P<segment>\d+\.ts)/?$',
        HlsSegmentView.as_view(),
        name='video-segment',
    ),
]
