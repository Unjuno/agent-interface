"""Synthetic corruption tests for the lifecycle-complete raw auditor."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from raw_allocation_audit_v2 import audit, reconstruct  # noqa: E402
from raw_allocation_audit_v1 import RawAuditError  # noqa: E402
from test_private_reset_audit import snapshot  # noqa: E402
from test_raw_allocation_audit import ARMS, raw_allocation  # noqa: E402


def raw_v2():
    raw = raw_allocation()
    raw["schema"] = "mindustry_three_arm_raw_events_v2"
    transitions = []
    for arm in ARMS:
        for index, task in enumerate(raw["arms"][arm]):
            start = task["started_ns"]
            before = snapshot()
            before["tick"] = 100.0 + index
            after = copy.deepcopy(before)
            after["tick"] += 1
            task["reset_event"] = {
                "request_ns": start + 4_500, "witness_ns": start + 5_000,
                "receipt_id": f"reset-{arm}-{task['task_id']}",
                "before": before, "after": after}
        a3_start = raw["arms"][arm][2]["started_ns"]
        b1_start = raw["arms"][arm][3]["started_ns"]
        transitions.append({"arm": arm, "after_task": "A3", "before_task": "B1",
            "from_layout": "A", "to_layout": "B", "at_ns": a3_start + 6_000,
            "before_binding": {"surface": 91, "geometry": [0, 24, 1280, 760]},
            "after_binding": {"surface": 91, "geometry": [0, 24, 1216, 760]}})
        assert a3_start + 6_000 < b1_start
    raw["transition_events"] = transitions
    return raw


class RawAllocationAuditV2Tests(unittest.TestCase):
    def test_full_raw_event_reset_and_geometry_reconstruction(self):
        trace = reconstruct(raw_v2())
        result = audit((json.dumps(raw_v2(), sort_keys=True) + "\n").encode())
        self.assertEqual(result["audit"], "PASS_CONSTRUCTION_ONLY")
        self.assertEqual(result["evaluation"]["disposition"], "RETAIN")
        self.assertEqual(result["evaluation"]["observed_break_even_task"], 2)
        self.assertEqual(result["lifecycle"], {
            "resets_verified": 18, "geometry_transitions_verified": 3})

    def test_modified_guard_tile_holds_audit(self):
        raw = raw_v2()
        raw["arms"]["plain"][0]["reset_event"]["after"]["tiles"][0]["block"] = "copper-wall"
        self.assertRaises(RawAuditError, reconstruct, raw)

    def test_adversarial_huge_tick_is_audited_as_hold_not_auditor_crash(self):
        raw = raw_v2()
        raw["arms"]["plain"][0]["reset_event"]["before"]["tick"] = 10 ** 400
        result = audit(json.dumps(raw).encode())
        self.assertEqual(result["audit"], "HOLD_RAW_RECONSTRUCTION")
        self.assertIn("reset tick", result["errors"][0])

    def test_missing_reset_evidence_holds_audit(self):
        raw = raw_v2()
        del raw["arms"]["ephemeral"][1]["reset_event"]
        self.assertRaises(RawAuditError, reconstruct, raw)

    def test_reset_must_follow_independent_score(self):
        raw = raw_v2()
        task = raw["arms"]["plain"][0]
        task["reset_event"]["request_ns"] = task["score_event"]["checked_ns"]
        self.assertRaises(RawAuditError, reconstruct, raw)

    def test_next_task_must_follow_reset_witness(self):
        raw = raw_v2()
        raw["arms"]["plain"][1]["started_ns"] = raw["arms"]["plain"][0]["reset_event"]["witness_ns"]
        self.assertRaises(RawAuditError, reconstruct, raw)

    def test_geometry_must_change_on_same_surface_after_reset(self):
        raw = raw_v2()
        raw["transition_events"][0]["after_binding"]["geometry"] = [0, 24, 1280, 760]
        self.assertRaises(RawAuditError, reconstruct, raw)

    def test_geometry_surface_identity_must_remain_stable(self):
        raw = raw_v2()
        raw["transition_events"][0]["after_binding"]["surface"] = 92
        self.assertRaises(RawAuditError, reconstruct, raw)

    def test_geometry_must_be_between_a3_reset_and_b1_start(self):
        raw = raw_v2()
        raw["transition_events"][0]["at_ns"] = raw["arms"]["plain"][3]["started_ns"]
        self.assertRaises(RawAuditError, reconstruct, raw)

    def test_missing_arm_geometry_event_holds_audit(self):
        raw = raw_v2()
        raw["transition_events"].pop()
        self.assertRaises(RawAuditError, reconstruct, raw)


if __name__ == "__main__":
    unittest.main()
