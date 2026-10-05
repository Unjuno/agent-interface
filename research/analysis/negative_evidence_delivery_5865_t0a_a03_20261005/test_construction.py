import copy
import importlib.util
import json
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PREDECESSOR = ROOT.parent / "negative_evidence_delivery_5865_t0a_a02_20261005"


def load_module(name, env_name, fallback):
    path = Path(os.environ.get(env_name, fallback))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConstructionRegressionTests(unittest.TestCase):
    def test_unknown_clock_case_forwards_receipt_before_lookup(self):
        data = json.loads((ROOT / "candidate_input.json").read_text())
        actions = data["cases"]["unknown_clock_offset"]["actions"]
        self.assertEqual(actions[0], {"type": "copy", "from": "A", "to": "B", "time": 4})
        self.assertEqual(actions[1]["type"], "lookup")

    def test_candidate_events_preserve_failure_snapshots(self):
        candidate = load_module(
            "candidate_under_test",
            "CANDIDATE_SOURCE",
            ROOT / "run_candidate.py",
        )
        data = json.loads((ROOT / "candidate_input.json").read_text())
        events = candidate.run_case(
            "failure_cooldown_copy",
            data["cases"]["failure_cooldown_copy"],
            data["query"],
            data["ttl"],
            "origin_bound_typed",
        )["events"]
        forwarded = next(row for row in events if row["event"] == "failure_forward")
        self.assertEqual(forwarded["failure_entries"], len(forwarded["failure_snapshot"]))
        self.assertEqual(forwarded["failure_snapshot"]["B:A"]["retry_after"], 5)
        self.assertEqual(forwarded["failure_snapshot"]["B:A"]["retained_until"], 15)

    def test_failure_forward_mutation_targets_broker_route_key(self):
        auditor = load_module(
            "auditor_under_test",
            "AUDITOR_SOURCE",
            ROOT / "audit_result.py",
        )
        mutation = getattr(auditor, "mutate_failure_forward_for_control", None)
        self.assertTrue(callable(mutation))
        row = {
            "retry_after": 5,
            "failure_snapshot": {
                "B:A": {"retry_after": 5, "retained_until": 15}
            },
        }
        changed = mutation(copy.deepcopy(row))
        self.assertEqual(changed["retry_after"], 9)
        self.assertEqual(changed["failure_snapshot"]["B:A"]["retry_after"], 9)
        self.assertEqual(changed["failure_snapshot"]["B:A"]["retained_until"], 15)

    def test_full_construction_stream_passes_core_and_all_mutation_controls(self):
        candidate = load_module(
            "candidate_full_under_test",
            "CANDIDATE_SOURCE",
            ROOT / "run_candidate.py",
        )
        auditor = load_module(
            "auditor_full_under_test",
            "AUDITOR_SOURCE",
            ROOT / "audit_result.py",
        )
        data = json.loads((ROOT / "candidate_input.json").read_text())
        truth = json.loads((ROOT / "oracle_truth.json").read_text())
        results = candidate.run(data)
        raw_rows = [
            event
            for case in results["cases"].values()
            for policy in case.values()
            for event in policy["events"]
        ]
        checked = auditor.audit(data, truth, results, raw_rows)
        self.assertEqual(checked["errors"], [])
        self.assertTrue(all(checked["mutation_controls"].values()))


if __name__ == "__main__":
    unittest.main()
