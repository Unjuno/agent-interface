import copy
import unittest

import audit_raw


class SavedActionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.source_records = audit_raw.load_inputs()

    def test_retained_trace_reconstructs_scoped_state_and_stop(self):
        result = audit_raw.audit(copy.deepcopy(self.source_records))
        self.assertEqual(result["active_sample_tics"], [1375, 1376, 1377, 1379, 1380, 1381, 1382, 1383])
        self.assertEqual(result["unobserved_tic_inside_active_span"], 1378)
        self.assertEqual(result["outer_child_exit"], -9)
        self.assertFalse(result["damage_or_ammo_measured"])

    def test_rejects_non_left_active_value(self):
        records = copy.deepcopy(self.source_records)
        records["scorer_last_action"][4]["action"][6] = 1.0
        with self.assertRaisesRegex(audit_raw.AuditError, "non-Left button"):
            audit_raw.audit(records)

    def test_rejects_release_with_wrong_key(self):
        records = copy.deepcopy(self.source_records)
        release = next(e for e in records["runtime_events"] if e.get("event") == "input_release_transition")
        release["owner_thread_keyup_receipt"]["key"] = "Right"
        with self.assertRaisesRegex(audit_raw.AuditError, "wrong nested key-up"):
            audit_raw.audit(records)

    def test_rejects_missing_release_boundary(self):
        records = copy.deepcopy(self.source_records)
        records["runtime_events"] = [e for e in records["runtime_events"] if e.get("event") != "input_release_transition"]
        with self.assertRaisesRegex(audit_raw.AuditError, "event count mismatch"):
            audit_raw.audit(records)

    def test_rejects_false_outer_cleanup_success(self):
        records = copy.deepcopy(self.source_records)
        records["outer_probe_final"].update(child_exit=0, external_rescue_used=False, reader_alive=False)
        with self.assertRaisesRegex(audit_raw.AuditError, "outer cleanup STOP"):
            audit_raw.audit(records)

    def test_rejects_positive_task_effect_counter(self):
        records = copy.deepcopy(self.source_records)
        records["runtime_scorer_samples"][0]["payload"]["kill_count"] = 1
        with self.assertRaisesRegex(audit_raw.AuditError, "positive kill count"):
            audit_raw.audit(records)


if __name__ == "__main__":
    unittest.main()
