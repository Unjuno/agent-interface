import copy
import tempfile
import unittest
from pathlib import Path

import audit_core
import candidate


class AuditorMutationTests(unittest.TestCase):
    def test_rejects_forged_decision_and_stale_state_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            row = candidate.run_case({"id": "mut", "external_write": "disjoint_y"}, root)
            forged = copy.deepcopy(row)
            forged["decision"] = "UNKNOWN_JOURNAL_STATE_MISMATCH"
            self.assertIn("decision_mismatch", audit_core.verify_case(forged, root))
            forged = copy.deepcopy(row)
            forged["final"]["state"]["x"] = 99
            self.assertIn("raw_observation_mismatch", audit_core.verify_case(forged, root))
            import sqlite3
            with sqlite3.connect(root / "mut.final.sqlite") as db:
                db.execute("UPDATE artifact SET y=99")
            self.assertIn("compensation_scope_or_final_state", audit_core.verify_case(row, root))


if __name__ == "__main__":
    unittest.main()
