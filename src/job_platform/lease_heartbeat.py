import logging
import threading
import uuid

from job_platform.job_queue import JobQueue, LEASE_SECONDS

logger = logging.getLogger(__name__)


class LeaseHeartbeat:
    def __init__(
        self,
        queue: JobQueue,
        job_id: uuid.UUID,
        lease_token: str,
        interval: float = 60,
    ):
        if interval <= 0 or interval >= LEASE_SECONDS:
            raise ValueError(
                "interval must be greater than 0 "
                "and less than LEASE_SECONDS"
            )

        self.queue = queue
        self.job_id = job_id
        self.lease_token = lease_token
        self.interval = interval
        self._stop_event = threading.Event()
        self.lease_lost = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
        )

    def _run(self):
        while not self._stop_event.wait(self.interval):
            try:
                renewed = self.queue.renew_lease(self.job_id, self.lease_token)
            except Exception:
                logger.exception(
                    "Failed to renew lease for job %s",
                    self.job_id,
                )
                self.lease_lost.set()
                return

            if not renewed:
                logger.error(
                    "Lease ownership lost for job %s",
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
