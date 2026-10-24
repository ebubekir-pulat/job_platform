
import threading
import uuid

from job_platform.lease_heartbeat import LeaseHeartbeat


class FakeQueue:
    def __init__(self):
        self.renewal_event = threading.Event()
        self.renewal_count = 0

    def renew_lease(self, job_id):
        self.renewal_count += 1
        self.renewal_event.set()
        return True


def test_heartbeat_renews_lease():
    queue = FakeQueue()
    job_id = uuid.uuid4()

    with LeaseHeartbeat(queue, job_id, interval=0.02):
        renewed = queue.renewal_event.wait(timeout=1)

    assert renewed
    assert queue.renewal_count >= 1