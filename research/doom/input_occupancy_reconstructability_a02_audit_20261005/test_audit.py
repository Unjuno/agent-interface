import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
try:
    import audit  # noqa: E402
except ModuleNotFoundError:
    audit = None


RUNS = (
    "map01-v38-integrated-threat-live-01",
    "map01-v39-coast-liveness-live-01",
)


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def retained_inputs():
    evidence = {}
    for run in RUNS:
        base = ROOT / "research/doom/results" / run
        evidence[run] = {
            "report": json.loads((base / "report.json").read_text(encoding="utf-8")),
            "events": read_jsonl(base / "runtime/events.jsonl"),
            "owner_events": json.loads((base / "runtime/owner-events.json").read_text()),
        }
    result_path = (ROOT / "research/doom/input_occupancy_reconstructability_a01_20261005"
                   / "results/a01/RESULT.json")
    return json.loads(result_path.read_text(encoding="utf-8")), evidence


class OccupancyAuditIntegrityTests(unittest.TestCase):
    def test_independent_raw_auditor_is_present(self):
        self.assertIsNotNone(audit, "A02 raw-derived auditor has not been implemented")

    def test_retained_a01_result_matches_per_key_counts_recomputed_from_raw(self):
        if audit is None:
            self.skipTest("A02 raw-derived auditor is not implemented")
        result, evidence = retained_inputs()
        self.assertEqual(audit.audit_result(result, evidence), [])

    def test_fabricated_down_up_counts_and_ids_are_rejected(self):
        if audit is None:
            self.skipTest("A02 raw-derived auditor is not implemented")
        result, evidence = retained_inputs()
        forged = copy.deepcopy(result)
        for row in forged["runs"]:
            count = row["input_admission_count"]
            fake_ids = [f"forged-actuation-{index}" for index in range(count)]
            row["admissions_with_physical_down_interval_and_actuation_id"] = count
            row["down_actuation_ids"] = fake_ids
            row["up_actuation_ids"] = fake_ids.copy()
            row["per_key_up_measurements_in_event_release_payloads"] = count
        self.assertTrue(audit.audit_result(forged, evidence))

    def test_fabricated_owner_up_measurement_count_is_rejected(self):
        if audit is None:
            self.skipTest("A02 raw-derived auditor is not implemented")
        result, evidence = retained_inputs()
        forged = copy.deepcopy(result)
        forged["runs"][0]["per_key_up_measurements_in_owner_event_ledger"] = 1
        self.assertTrue(audit.audit_result(forged, evidence))

    def test_boolean_event_count_alias_is_rejected(self):
        if audit is None:
            self.skipTest("A02 raw-derived auditor is not implemented")
        result, evidence = retained_inputs()
        forged = copy.deepcopy(result)
        forged["runs"][0]["event_type_counts"]["clock_probe"] = True
        self.assertTrue(audit.audit_result(forged, evidence))

    def test_reconstructable_claim_without_raw_edge_receipts_is_rejected(self):
        if audit is None:
            self.skipTest("A02 raw-derived auditor is not implemented")
        result, evidence = retained_inputs()
        forged = copy.deepcopy(result)
        forged["runs"][0]["exact_per_key_occupancy_reconstructable"] = True
        self.assertTrue(audit.audit_result(forged, evidence))

    def test_duplicate_actuation_ids_do_not_satisfy_one_to_one_join(self):
        if audit is None:
            self.skipTest("A02 raw-derived auditor is not implemented")
        result, evidence = retained_inputs()
        forged = copy.deepcopy(result)
        rows = [
            {"event": "input_admission", "physical_key_measurement": {
                "actuation_id": "duplicate", "bracket": {"physical_down_interval": [1, 2]}}},
            {"event": "input_admission", "physical_key_measurement": {
                "actuation_id": "duplicate", "bracket": {"physical_down_interval": [3, 4]}}},
            {"event": "input_released", "physical_key_measurement": {"actuation_id": "duplicate"}},
            {"event": "input_released", "physical_key_measurement": {"actuation_id": "duplicate"}},
        ]
        evidence[RUNS[0]]["events"] = rows
        first = forged["runs"][0]
        first.update(audit.derive_run(evidence[RUNS[0]]["report"], rows,
                                      evidence[RUNS[0]]["owner_events"]))
        first["exact_per_key_occupancy_reconstructable"] = True
        self.assertTrue(audit.audit_result(forged, evidence))


if __name__ == "__main__":
    unittest.main()
