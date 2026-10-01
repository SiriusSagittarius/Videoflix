from django.conf import settings
from django.test import SimpleTestCase
from django_rq.workers import get_worker

from core.workers import AllQueuesWorker


class AllQueuesWorkerTests(SimpleTestCase):
    """The worker that the entrypoint starts with `rqworker default`."""

    def test_rqworker_uses_all_queues_worker(self):
        """The worker class from the RQ settings is used."""
        self.assertIsInstance(get_worker("default"), AllQueuesWorker)

    def test_listens_to_emails_before_videos(self):
        """The worker gets every queue, the email queue before videos."""
        queue_names = [queue.name for queue in get_worker("default").queues]
        self.assertEqual(queue_names, ["default", "emails", "video"])

    def test_queues_have_their_own_timeouts(self):
        """Emails get a short timeout, video conversions a long one."""
        queues = settings.RQ_QUEUES
        self.assertEqual(queues["emails"]["DEFAULT_TIMEOUT"], 2 * 60)
        self.assertEqual(queues["video"]["DEFAULT_TIMEOUT"], 60 * 60)
