import json
import unittest
from pathlib import Path

import audit
import candidate


HERE = Path(__file__).resolve().parent


class FiniteCutoverMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
        cls.raw = {"schema":"revision-timed-cutover-raw-v1", "rows":[
            row for case in spec["cases"] for row in candidate.run_case(case, spec["preparation_ticks"])
        ]}

    def row(self, case, arm):
        return next(r for r in self.raw["rows"] if r["scenario_id"] == case and r["arm"] == arm)

    def events(self, case, arm, kind):
        return [e for e in self.row(case, arm)["events"] if e["kind"] == kind]

    def test_roster_is_complete(self):
        self.assertEqual(len(self.raw["rows"]), 30)

    def test_stable_authenticated_turn_reuses_read_only_preparation(self):
        final_time = self.events("C01", "version_bound_read_only", "final")[0]["time"]
        fast_effect = self.events("C01", "version_bound_read_only", "effect_verified")[0]["time"]
        baseline_effect = self.events("C01", "final_only", "effect_verified")[0]["time"]
        self.assertLess(fast_effect - final_time, baseline_effect - final_time)

    def test_revision_and_quotation_block_safe_arm_effects(self):
        for case in ("C02", "C04"):
            for arm in audit.SAFE:
                self.assertEqual(self.events(case, arm, "consequential_input"), [])
        for case in ("C02", "C04"):
            self.assertTrue(any(e.get("disposition", "").startswith("discarded_") for e in self.events(case, "version_bound_read_only", "prepared_candidate_disposition")))

    def test_changed_recipient_and_speaker_are_bound_to_final_receipt(self):
        self.assertEqual(self.events("C03", "version_bound_read_only", "consequential_input")[0]["intent"], "send:bob")
        speaker_input = self.events("C05", "version_bound_read_only", "consequential_input")[0]
        self.assertEqual((speaker_input["principal"], speaker_input["turn"], speaker_input["intent"]), ("P2", "T2", "archive:bob"))

    def test_late_stale_completion_is_discarded(self):
        events = self.row("C06", "version_bound_read_only")["events"]
        stale_done = [e for e in events if e["kind"] == "readonly_prepare_complete" and e.get("epoch") == 1][0]
        self.assertGreater(stale_done["time"], 10)
        inputs = self.events("C06", "version_bound_read_only", "consequential_input")
        self.assertEqual([e["intent"] for e in inputs], ["archive:bob"])

    def test_stop_states_and_independent_physical_release(self):
        self.assertEqual(self.events("C07", "version_bound_read_only", "consequential_input"), [])
        self.assertEqual(len(self.events("C08", "version_bound_read_only", "effect_unknown")), 1)
        self.assertEqual(self.events("C08", "version_bound_read_only", "retry")[0]["allowed"], False)
        self.assertEqual(self.events("C08", "version_bound_read_only", "blind_inverse")[0]["allowed"], False)
        self.assertEqual(self.events("C09", "version_bound_read_only", "effect_disposition")[0]["automatic_undo"], False)
        release = self.events("C10", "version_bound_read_only", "release_verified")[0]
        self.assertLess(release["time"], 20)

    def test_independent_raw_auditor_and_mutation_controls(self):
        errors, metrics = audit.audit(self.raw)
        self.assertEqual(errors, [])
        self.assertEqual(metrics["stable_latency_saving_ticks"], 3)
        controls = audit.mutation_controls(self.raw)
        self.assertEqual(set(controls), {"old_epoch", "partial_as_final", "speaker_merge", "cancel_as_undo"})
        self.assertTrue(all(x["rejected"] for x in controls.values()))


if __name__ == "__main__":
    unittest.main()
