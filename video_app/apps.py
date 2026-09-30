from importlib import import_module

from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    """Videos, their processing with FFmpeg and the streaming endpoints."""

    name = 'video_app'

    def ready(self):
        """Load the signal handlers, so Django connects them on startup."""
        import_module("video_app.signals")
