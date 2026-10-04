"""Focused supplemental test for owner cleanup forwarded during backend close."""
from __future__ import annotations

import unittest

from .test_bridge import Backend, harness


class TeardownForwardingTests(unittest.TestCase):
    def test_close_drains_verified_cleanup_after_owner_stops(self):
        source, h = harness()
        lease = source.Lease(intent="intent-v39-close-a02")
        backend = object.__new__(Backend)
        backend.owner, backend.lease, backend.held = h.owner, lease, set()
        backend._input_event_context = ("close-cover", 4)
        backend._owner_records_cursor = 0
        backend._active_actuations, backend._actuation_context = {}, {}
        backend.events = []
        backend.emit = backend.events.append
        try:
            backend.raw("F8", True)
            backend.close()
            release = [row for row in backend.events
                       if row.get("event") == "input_release_measurement"]
            self.assertEqual(len(release), 1)
            row = release[0]
            self.assertEqual((row["id"], row["step"], row["intent_token"]),
                             ("close-cover", 4, "intent-v39-close-a02"))
            self.assertEqual(row["physical_key_measurement"]["classification"],
                             "CONFIRMED_PHYSICAL_UP")
            self.assertTrue(row["owner_cleanup_record"]["verified"])
            self.assertTrue(h.owner.closed)
            self.assertEqual(h.d.physical, set())
        finally:
            h.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
