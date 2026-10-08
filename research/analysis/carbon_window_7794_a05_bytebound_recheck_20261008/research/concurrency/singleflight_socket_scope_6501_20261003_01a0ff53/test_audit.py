"""Copied-data oracle corruption controls; construction sockets are separate."""
import copy
import json
import unittest
from pathlib import Path

from audit import audit
from study import run


class AuditControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = json.loads((Path(__file__).parent / "fixtures.json").read_text())
        cls.raw = run(cls.fixtures)

    def rejected(self, data):
        with self.assertRaises(ValueError):
            audit(data, self.fixtures)

    def test_complete_construction(self):
        self.assertEqual(audit(self.raw, self.fixtures)["status"], "PASS_SOCKET_SCOPE_TRANSFER_SCOPED")

    def test_missing_trial(self):
        data = copy.deepcopy(self.raw); data["trials"].pop(); self.rejected(data)

    def test_duplicate_trial(self):
        data = copy.deepcopy(self.raw); data["trials"][-1] = copy.deepcopy(data["trials"][0]); self.rejected(data)

    def test_missing_waiter(self):
        data = copy.deepcopy(self.raw); data["trials"][0]["callers"].pop(); self.rejected(data)

    def test_wrong_scope_claim_upgraded(self):
        data = copy.deepcopy(self.raw)
        trial = next(t for t in data["trials"] if t["case_id"] == "different_target" and t["mode"] == "predicate_inflight")
        trial["callers"][1]["descriptive_match"] = True; self.rejected(data)

    def test_wire_hash_changed(self):
        data = copy.deepcopy(self.raw); data["trials"][0]["server_events"][0]["sha256"] = "0"*64; self.rejected(data)

    def test_cleanup_integer_bool_alias(self):
        data = copy.deepcopy(self.raw); data["trials"][0]["active_server_threads_after_cleanup"] = False; self.rejected(data)

    def test_unknown_authority_field(self):
        data = copy.deepcopy(self.raw); data["trials"][0]["callers"][0]["authority"] = True; self.rejected(data)

    def test_omitted_transport_triple(self):
        data = copy.deepcopy(self.raw); data["trials"][0]["server_events"].pop(); self.rejected(data)


if __name__ == "__main__":
    unittest.main()
