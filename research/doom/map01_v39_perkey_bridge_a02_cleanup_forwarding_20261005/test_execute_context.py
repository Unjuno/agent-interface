from __future__ import annotations

import time
import unittest

from . import test_bridge


class ExecuteContextDrainTests(unittest.TestCase):
    def test_execute_finally_drains_cancel_cleanup_before_clearing_context(self):
        source, h = test_bridge.harness()
        backend_type = test_bridge.Backend
        previous = backend_type.__mro__[1]
        old_execute = getattr(previous, "execute", None)
        lease = source.Lease(intent="intent-v39-execute-a02")
        backend = object.__new__(backend_type)
        backend.owner, backend.lease, backend.held = h.owner, lease, set()
        backend._input_event_context = None
        backend._owner_records_cursor = 0
        backend._active_actuations, backend._actuation_context = {}, {}
        backend.events = []
        backend.emit = backend.events.append

        def inherited_execute(self, step, cancel, identifier, index):
            self.raw("F8", True)
            cancel.cancel.set()
            for _ in range(1000):
                if any(row.get("event") == "owner_release"
                       for row in self.owner.records):
                    return "parent-execute-returned"
                time.sleep(.001)
            raise AssertionError("owner cleanup did not arrive during execute")

        previous.execute = inherited_execute
        try:
            result = backend.execute({}, lease, "execute-cover", 6)
            self.assertEqual(result, "parent-execute-returned")
            rows = [row for row in backend.events
                    if row.get("event") == "input_release_measurement"]
            self.assertEqual(len(rows), 1)
            self.assertEqual((rows[0]["id"], rows[0]["step"],
                              rows[0]["intent_token"]),
                             ("execute-cover", 6, "intent-v39-execute-a02"))
            self.assertEqual(rows[0]["physical_key_measurement"]["classification"],
                             "CONFIRMED_PHYSICAL_UP")
            self.assertIsNone(backend._input_event_context)
            self.assertEqual(h.d.physical, set())
        finally:
            if old_execute is None:
                delattr(previous, "execute")
            else:
                previous.execute = old_execute
            h.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
