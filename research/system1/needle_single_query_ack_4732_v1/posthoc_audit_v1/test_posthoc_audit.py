import importlib.util
from pathlib import Path
import unittest


def load():
    path = Path(__file__).with_name("posthoc_audit.py")
    spec = importlib.util.spec_from_file_location("posthoc_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StubAudit:
    MODES = ("INLINE_512", "ONLINE_QUERY_ONLY")

    @staticmethod
    def p95(values):
        return max(values) / 1_000_000


class PosthocGateTests(unittest.TestCase):
    def test_gate_reads_nested_query_only_field_and_ratio(self):
        audit = load()
        rows = []
        for mode, ack, query, full in (("INLINE_512", 100_000_000, 1, 8),
                                       ("ONLINE_QUERY_ONLY", 40_000_000, 1, 8)):
            rows.append({"ack_elapsed_ns": ack,
                         "ack": {"update_ns": 2, "commit_ns": 3,
                                 "one_prediction_ns": query,
                                 "full_prediction_ns": full},
                         "post_ack_audit": {"full_prediction_ns": full}})
        obj = {"seed": 1, "arm_order": list(StubAudit.MODES),
               "arms": {"INLINE_512": [rows[0]], "ONLINE_QUERY_ONLY": [rows[1]]},
               "arm_total_elapsed_ns": {"INLINE_512": 100, "ONLINE_QUERY_ONLY": 40}}
        summary = audit.summarize(StubAudit, obj)
        self.assertEqual(summary["online_query_only"]["ack_p95_ms"], 40)
        self.assertEqual(summary["ratio"], .4)


    def test_gate_does_not_pass_when_ratio_exceeds_half(self):
        audit = load()
        rows = []
        for ack in (100_000_000, 51_000_000):
            rows.append({"ack_elapsed_ns": ack, "ack": {"update_ns": 1, "commit_ns": 1,
                         "one_prediction_ns": 1, "full_prediction_ns": 2},
                         "post_ack_audit": {"full_prediction_ns": 2}})
        obj = {"seed": 1, "arm_order": list(StubAudit.MODES),
               "arms": {"INLINE_512": [rows[0]], "ONLINE_QUERY_ONLY": [rows[1]]},
               "arm_total_elapsed_ns": {"INLINE_512": 100, "ONLINE_QUERY_ONLY": 51}}
        summary = audit.summarize(StubAudit, obj)
        self.assertEqual(summary["ratio"], .51)
        self.assertFalse(summary["online_query_only"]["ack_p95_ms"] <= 60 and summary["ratio"] <= .5)


if __name__ == "__main__":
    unittest.main()
