from django.conf import settings
from django_rq.queues import get_queues
from rq import Worker


class AllQueuesWorker(Worker):
    """RQ worker that listens to every queue from RQ_QUEUES.

    The given entrypoint starts `rqworker default` and must not be
    changed. This worker adds the email and the video queue itself and
    works through the queues in the order of RQ_QUEUES, so waiting
    emails are always sent before the next video is converted.
    """

    def __init__(self, queues, *args, **kwargs):
        """Replace the queue from the command line by all queues."""
        all_queues = get_queues(
            *settings.RQ_QUEUES,
            queue_class=kwargs.get("queue_class"),
            job_class=kwargs.get("job_class"),
        )
        super().__init__(all_queues, *args, **kwargs)
