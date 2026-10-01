import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import audit


ROOT = Path(__file__).parent
RAW_PATH = ROOT / "evidence" / "raw.json"
FREEZE_PATH = ROOT / "evidence" / "predecessor_FREEZE.json"
STUDY_FREEZE_PATH = ROOT / "evidence" / "FREEZE.json"


class StrictAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))

    def test_original_raw_and_freeze_are_byte_bound(self):
        self.assertEqual(hashlib.sha256(FREEZE_PATH.read_bytes()).hexdigest(), self.raw["freeze_sha256"])
        self.assertEqual(audit.errors_for(self.raw), [])

    def test_prior_three_controls_still_rejected(self):
        for mutate in (
            lambda r: r["events"][1]["identity"].__setitem__("xid", -1),
            lambda r: r["events"][3].__setitem__("admitted", True),
            lambda r: r["events"][4]["click"].__setitem__("emissions", 0),
        ):
            changed = copy.deepcopy(self.raw)
            mutate(changed)
            self.assertTrue(audit.errors_for(changed))

    def test_contradiction_and_noncanonical_trace_controls_rejected(self):
        changes = (
            lambda r: r["events"].append({"event": "unexpected"}),
            lambda r: r["events"].append(copy.deepcopy(r["events"][3])),
            lambda r: r["events"][3].__setitem__("would_call_bridge", True),
            lambda r: r["events"].__setitem__(slice(2, 5), [r["events"][3], r["events"][2], r["events"][4]]),
            lambda r: r["events"][0].__setitem__("extra", True),
            lambda r: r["events"].pop(3),
            lambda r: r["events"][0]["identity"].pop("pid"),
            lambda r: r.__setitem__("unrecognized", 1),
        )
        for mutate in changes:
            changed = copy.deepcopy(self.raw)
            mutate(changed)
            self.assertTrue(audit.errors_for(changed))

    def test_direct_and_documented_cli_routes_match(self):
        direct = audit.audit(RAW_PATH, FREEZE_PATH, STUDY_FREEZE_PATH)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "audit.json"
            completed = subprocess.run(
                [sys.executable, str(ROOT / "audit.py"), str(RAW_PATH), "--freeze", str(FREEZE_PATH),
                 "--study-freeze", str(STUDY_FREEZE_PATH), "--output", str(output)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout), direct)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), direct)


if __name__ == "__main__":
    unittest.main()
