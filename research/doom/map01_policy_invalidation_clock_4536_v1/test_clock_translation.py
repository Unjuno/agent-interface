from pathlib import Path
import json
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
LIVE_CONTROL = HERE.parents[2] / "research" / "live_control"
sys.path.insert(0, str(LIVE_CONTROL))

from clock_translation import SCHEMA, translate_invalidation
from final_action_admission_v1 import decide_final_admission


def calibration(offset=-739_170_000_000, width=100_000):
    base = 8_577_270_000_000
    samples = []
    for i in range(3):
        send = base + i * 100_000
        receive = send + width
        samples.append({"host_send_ns": send, "host_receive_ns": receive,
                        "runtime_ns": send + offset + width // 2})
    return {"schema": SCHEMA, "same_session": True,
            "host_domain": "host_monotonic_ns",
            "runtime_domain": "runtime_monotonic_ns", "samples": samples}


def invalidation(host_ns):
    return {"timestamp_domain": "host_monotonic_ns",
            "outcome_evaluated_ns": host_ns,
            "outcome": {"status": "HARD_INVALIDATED",
                        "reason": "below_hard_minimum",
                        "requires_new_decision": True,
                        "grants_input_authority": False}}


def retained_decision8_evidence():
    repo = HERE.parents[2]
    log = (repo / "research/doom/map01_model_loop_finite_v10/results/"
           "map01-model-loop-finite-v10-20260927-02/runtime/"
           "action-freshness-clock-translations.jsonl")
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    row = next(item for item in rows
               if item.get("iteration") == 8 and "planner_terminal_runtime_ns" in item)
    cal = {"schema": SCHEMA, "same_session": True,
           "host_domain": "host_monotonic_ns",
           "runtime_domain": "runtime_monotonic_ns",
           "samples": row["samples"]}
    return row, cal


def observed_preflight_releases():
    repo = HERE.parents[2]
    path = (repo / "research/doom/map01_policy_invalidation_clock_4536_v1/"
            "preflight/container-startup-zero-decision-20260927-01/"
            "runtime/owner-events.json")
    return json.loads(path.read_text())


class PolicyInvalidationClockTranslationTests(unittest.TestCase):
    def test_mixed_domain_counterexample_then_translated_fail_closed_rejection(self):
        prior, retained_calibration = retained_decision8_evidence()
        host_event = 8_577_271_000_000  # synthetic: predecessor did not persist this receipt
        host_receipt = invalidation(host_event)
        planner_terminal = {"turn_id": "stale-turn", "status": "interrupted",
                            "answer_eligible": False,
                            "terminal_observed_ns": prior["planner_terminal_runtime_ns"]}
        runtime_decision = prior["controller_decided_runtime_ns"]

        with self.assertRaisesRegex(ValueError, "precedes observed boundary"):
            decide_final_admission(planner_terminal,
                                   {k: v for k, v in host_receipt.items()
                                    if k != "timestamp_domain"},
                                   runtime_decision)

        record, runtime_receipt = translate_invalidation(
            host_receipt, retained_calibration)
        rejected = decide_final_admission(
            planner_terminal, runtime_receipt, runtime_decision)
        self.assertLessEqual(record["runtime_timestamp_ns"], runtime_decision)
        self.assertEqual(record["source_receipt"], host_receipt)
        self.assertEqual(record["runtime_receipt"], runtime_receipt)
        self.assertEqual(rejected["status"], "REJECTED_POLICY_INVALIDATED")
        self.assertFalse(rejected["input_authority_admitted"])
        self.assertIsNone(rejected["executor_admission"])

        # The stale action was not admitted. Separately, the zero-model
        # preflight records actual runtime owner-release receipts.
        releases = observed_preflight_releases()
        self.assertEqual(len(releases), 3)
        self.assertTrue(all(r["event"] == "owner_release" and
                            r["verified"] is True and
                            r["keys_down"] == [] and
                            r["buttons_down"] == [] for r in releases))

    def test_refuses_wrong_clock_domain(self):
        bad = invalidation(8_577_269_000_000)
        bad["timestamp_domain"] = "runtime_monotonic_ns"
        with self.assertRaisesRegex(ValueError, "not host monotonic"):
            translate_invalidation(bad, calibration())

    def test_refuses_missing_same_session_provenance(self):
        bad = calibration()
        bad["same_session"] = False
        with self.assertRaisesRegex(ValueError, "same-session"):
            translate_invalidation(invalidation(8_577_269_000_000), bad)

    def test_refuses_overwide_offset_interval(self):
        with self.assertRaisesRegex(ValueError, "uncertainty"):
            translate_invalidation(invalidation(8_577_269_000_000),
                                   calibration(width=1_100_000_000))

    def test_refuses_stale_or_future_timestamp(self):
        cal = calibration()
        latest = max(s["host_receive_ns"] for s in cal["samples"])
        for timestamp in (latest - 5_000_000_001, latest + 1):
            with self.subTest(timestamp=timestamp):
                with self.assertRaisesRegex(ValueError, "outside calibration age"):
                    translate_invalidation(invalidation(timestamp), cal)

    def test_refuses_bad_or_incomplete_probe_sets(self):
        cal = calibration()
        cal["samples"] = cal["samples"][:2]
        with self.assertRaisesRegex(ValueError, "three clock-offset"):
            translate_invalidation(invalidation(8_577_269_000_000), cal)


if __name__ == "__main__":
    unittest.main()
