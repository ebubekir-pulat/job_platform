import logging
import threading

from job_platform.job_queue import JobQueue, LEASE_SECONDS

logger = logging.getLogger(__name__)


class LeaseHeartbeat:
    def __init__(
        self,
        queue: JobQueue,
        job_id,
        interval: float = 60,
    ):
        if interval <= 0 or interval >= LEASE_SECONDS:
            raise ValueError(
                "interval must be greater than 0 "
                "and less than LEASE_SECONDS"
            )

        self.queue = queue
        self.job_id = job_id
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
        )
        self.lease_lost = threading.Event()

    def _run(self):
        while not self._stop_event.wait(self.interval):
            try:
                renewed = self.queue.renew_lease(self.job_id)
            except Exception:
                logger.exception(
                    "Failed to renew lease for job %s",
                    self.job_id,
                )
                self.lease_lost.set()
                return

            if not renewed:
                logger.error(
                    "Lease no longer exists for job %s",
                    self.job_id,
                )
                self.lease_lost.set()
                return

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._stop_event.set()
        self._thread.join()
