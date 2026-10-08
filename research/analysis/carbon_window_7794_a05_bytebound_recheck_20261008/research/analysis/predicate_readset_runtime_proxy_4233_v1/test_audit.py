import json
import unittest
from pathlib import Path

from audit import audit
from study import run


ROOT = Path(__file__).resolve().parent


class ProtocolTests(unittest.TestCase):
    def test_formal_trace_has_preregistered_denominator(self):
        trace = json.loads((ROOT / "trace.json").read_text(encoding="utf-8"))
        rows = run(trace)
        self.assertEqual(64, len(rows))

    def test_audit_and_corruption_controls(self):
        trace = json.loads((ROOT / "trace.json").read_text(encoding="utf-8"))
        rows = run(trace)
        result = audit(trace, rows)
        self.assertEqual("PASS_DYNAMIC_READSET_SCOPED", result["result"])
        self.assertEqual([], result["errors"])
        self.assertEqual(8, result["metrics"]["mutation_controls_rejected"])

    def test_tracer_records_conditional_nested_reads(self):
        trace = json.loads((ROOT / "trace.json").read_text(encoding="utf-8"))
        rows = run(trace)
        get = lambda state: next(r for r in rows if r["policy"] == "DYNAMIC_READSET" and r["state"] == state and r["predicate"] == "READY_TO_SUBMIT")
        self.assertEqual(["form", "form.mode", "risk", "risk.level"], get("s0")["reads"])
        self.assertEqual(["form", "form.mode"], get("s3")["reads"])
        self.assertTrue(get("s4")["cache_hit"])


if __name__ == "__main__":
    unittest.main()
