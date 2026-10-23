"""Real injected factory/backend methods over inert X request doubles."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from runtime.backends.x11_v1.backend import X11Backend
from runtime.cli_v1 import test_mcp_xvfb_blocked_release_integration as harness


class QueuedReleaseReceiptTests(unittest.TestCase):
    def test_tap_records_queued_up_before_entering_reply_wait(self):
        backend = object.__new__(X11Backend)
        backend.held_keycodes = {}
        backend.held_buttons = set()
        backend.emissions = 0
        backend._keycode = {'a':38, 'b':56}.__getitem__
        backend.d = SimpleNamespace(sync=Mock(), flush=Mock(),
            display=SimpleNamespace(info=SimpleNamespace(resource_id_base=6291456)))
        owner = SimpleNamespace(get=lambda:SimpleNamespace(backend=backend),
                                cancel_guarded=Mock(return_value={}))
        with tempfile.TemporaryDirectory() as td, \
             patch.object(harness, 'GuardedSessionOwner', return_value=owner), \
             patch('runtime.backends.x11_v1.backend.xtest.fake_input') as emit:
            harness._xvfb_blocking_owner_factory({'app':1}, td, ':88', {}).get()
            backend.key_chord(['a'])
            queued = json.loads((Path(td)/'xvfb-target-release-queued.json').read_text())
            synced = json.loads((Path(td)/'xvfb-owner-sync-entered.json').read_text())
            self.assertEqual(queued['keycode'], 38)
            self.assertEqual(queued['resource_base'], 6291456)
            self.assertLessEqual(queued['queued_ns'], synced['entered_ns'])
            self.assertFalse(queued['server_release_confirmed'])
            self.assertEqual([c.args[1:3] for c in emit.call_args_list],
                             [(2,), (2,), (3,)])


if __name__ == '__main__':
    unittest.main()
