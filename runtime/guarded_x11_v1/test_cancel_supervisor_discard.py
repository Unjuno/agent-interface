import unittest
from unittest.mock import patch

from runtime.guarded_x11_v1.cancel_supervisor import _serve_one


class Endpoint:
    def __init__(self, received=None):
        self.received = received
        self.sent = []
    def recv(self): return self.received
    def send(self, value): self.sent.append(value)
    def close(self): pass


class SupervisorDiscardTests(unittest.TestCase):
    def test_pinned_worker_unknown_does_not_flush_pending_input(self):
        class Display:
            def __init__(self):
                self.display = self
                self.pending = []
                self.delivered = []
            def close_internal(self, _): self.pending.clear()
            def close(self):
                self.delivered.extend(self.pending)
                self.pending.clear()
        class Backend:
            def __init__(self, *_): self.d = connection
            def close(self): self.d.close()
        def worker(request, *, pinned_backend):
            pinned_backend.d.pending.append('key-release')
            return {'status': 'unknown', 'reason': 'transaction_deadline_before_sync'}
        connection = Display()
        request = {'deadline_monotonic_ns': 100, 'display_name': ':88',
                   'owner_pid': 23, 'x_resource_base': 45}
        command = Endpoint({'op': 'run', 'request': request})
        output, ready = Endpoint(), Endpoint()
        with (patch('runtime.backends.x11_v1.backend.X11Backend', Backend),
              patch('runtime.guarded_x11_v1.xres_client_fence.client_pid_at_base', return_value=23),
              patch('runtime.guarded_x11_v1.cancel_supervisor.time.monotonic_ns', return_value=1)):
            _serve_one(command, output, ready, worker, pinned_display_name=':88',
                       expected_owner={'pid': 23, 'resource_base': 45})
        self.assertEqual(output.sent[0]['result']['status'], 'unknown')
        self.assertEqual(connection.delivered, [])
