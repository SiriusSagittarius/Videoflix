from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    name = 'video_app'

    def ready(self):
        """Connect the signal handlers of this app."""
        from video_app import signals  # noqa: F401
