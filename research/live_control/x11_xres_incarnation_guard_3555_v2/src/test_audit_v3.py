import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import audit_v3


HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent / "artifacts" / "formal_01"
RAW = EVIDENCE / "raw.json"
FREEZE = HERE.parent / "FREEZE.json"


class AuditV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads(RAW.read_text(encoding="utf-8"))

    def test_untouched_raw_passes_and_is_bound_to_freeze(self):
        self.assertEqual([], audit_v3.errors_for(self.raw))

    def test_rejects_structural_and_semantic_mutations(self):
        mutations = {
            "mutate_xid": lambda r: r["events"][1]["identity"].__setitem__("xid", -1),
            "admit_stale": lambda r: r["events"][3].__setitem__("admitted", True),
            "hide_emission": lambda r: r["events"][4]["click"].__setitem__("emissions", 0),
            "extra_event": lambda r: r["events"].append({"event": "unexpected"}),
            "duplicate_stale": lambda r: r["events"].insert(4, copy.deepcopy(r["events"][3])),
            "would_call_bridge": lambda r: r["events"][3].__setitem__("would_call_bridge", True),
            "missing_precondition": lambda r: r["events"].pop(2),
            "reordered_transitions": lambda r: r["events"].reverse(),
            "extra_stale_field": lambda r: r["events"][3].__setitem__("extra", 1),
            "stale_emission": lambda r: r["events"][3].__setitem__("emissions", True),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                damaged = copy.deepcopy(self.raw)
                mutate(damaged)
                self.assertTrue(audit_v3.errors_for(damaged), name)

    def test_cli_uses_same_checks_and_preserves_raw(self):
        original = RAW.read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "audit.json"
            result = subprocess.run(
                [sys.executable, str(HERE / "audit_v3.py"), str(RAW),
                 "--freeze", str(FREEZE), "--output", str(output)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr + result.stdout)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("PASS_INDEPENDENT_AUDIT", report["status"])
            self.assertEqual(original, RAW.read_bytes())


if __name__ == "__main__":
    unittest.main()
