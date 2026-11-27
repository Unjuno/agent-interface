import unittest
from unittest.mock import patch

from runtime.cli_v1.owned_guarded_session import _release_retired_inputs_worker


class ReleaseWorkerFailureTests(unittest.TestCase):
    def test_failed_release_discards_unsent_requests_instead_of_flushing(self):
        class Connection:
            def __init__(self):
                self.sent = []
            def send(self, value):
                self.sent.append(value)
            def close(self):
                pass

        class Display:
            def __init__(self):
                self.queued = []
                self.delivered = []
                self.display = self
            def close(self):
                self.delivered.extend(self.queued)
                self.queued.clear()
            def close_internal(self, whom):
                self.queued.clear()

        class Backend:
            def __init__(self, *_):
                self.d = display
            def release_all(self, **_):
                self.d.queued.append('key-release')
                raise RuntimeError('injected failure')
            def close(self):
                self.d.close()

        display = Display()
        connection = Connection()
        with patch('runtime.backends.x11_v1.backend.X11Backend', Backend):
            _release_retired_inputs_worker(connection, ':88', {'a': 38}, [])
        self.assertEqual(display.delivered, [])
        self.assertEqual(connection.sent[0]['status'], 'unknown')
