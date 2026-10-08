import copy
import unittest

from audit_t1 import audit_result
from transport_model import build_raw, run_trace


class TransportT1Tests(unittest.TestCase):
    def test_all_single_source_erasures_fixed_fec_completes_before_arq(self):
        for source_slot in range(4):
            with self.subTest(source_slot=source_slot):
                loss_mask = 1 << source_slot
                fixed = run_trace(loss_mask, 0, "fixed")
                retransmit = run_trace(loss_mask, 0, "retransmit")
                adaptive = run_trace(loss_mask, 0, "adaptive")
                self.assertEqual(fixed["semantic_status"], "SEMANTICALLY_CONFIRMED")
                self.assertEqual(fixed["completion_round"], 0)
                self.assertEqual(retransmit["completion_round"], 1)
                self.assertEqual(adaptive["completion_round"], 1)

    def test_clean_window_adaptive_repair_avoids_fixed_overhead(self):
        fixed = run_trace(0, 0, "fixed")
        adaptive = run_trace(0, 0, "adaptive")
        self.assertEqual(fixed["completion_round"], adaptive["completion_round"])
        self.assertEqual(fixed["completion_round"], 0)
        self.assertLess(adaptive["packets_sent"], fixed["packets_sent"])

    def test_deterministic_grid_size_and_faults_never_false_confirm(self):
        raw = build_raw()
        self.assertEqual(len(raw["trace_runs"]), 512 * 3)
        self.assertEqual(len(raw["fault_runs"]), 5 * 3)
        for row in raw["fault_runs"]:
            if row["semantic_status"] == "SEMANTICALLY_CONFIRMED":
                self.assertEqual(row["decoded_values"], row["expected_values"])
                self.assertTrue(row["window_metadata_valid"])
                self.assertTrue(row["manifest_complete"])
        self.assertEqual(audit_result(raw), [])

    def test_independent_auditor_rejects_corrupted_completion_and_erasure(self):
        raw = build_raw()
        changed = copy.deepcopy(raw)
        changed["trace_runs"][0]["completion_round"] = 4
        self.assertTrue(audit_result(changed))

        changed = copy.deepcopy(raw)
        changed["trace_runs"][0]["packets"] = []
        self.assertTrue(audit_result(changed))

    def test_independent_auditor_rejects_forged_semantic_receipt(self):
        raw = build_raw()
        changed = copy.deepcopy(raw)
        row = changed["fault_runs"][0]
        row["semantic_status"] = "SEMANTICALLY_CONFIRMED"
        row["decoded_values"] = [0, 0, 0, 0]
        self.assertTrue(audit_result(changed))


if __name__ == "__main__":
    unittest.main(verbosity=2)
