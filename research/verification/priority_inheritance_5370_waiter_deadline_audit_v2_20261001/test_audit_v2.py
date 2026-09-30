"""Pre-freeze construction and corruption controls for audit-v2."""
import copy
import unittest

from audit_v2 import ALLOCATION, BASE_MAIN, audit


def event(tick, run, priority=None):
    item = {"tick": tick, "run": run}
    if priority is not None:
        item["effective_priority"] = priority
    return item


def row(case, inheritance, order, completed, stale, rejected, release,
        owner_ticks, max_priority, schedule):
    return {
        "case": case,
        "policy": {"inheritance": inheritance, "waiter_order": order},
        "holder_release": release,
        "inherited_owner_ticks": owner_ticks,
        "max_inherited_priority": max_priority,
        "medium_service": 5,
        "completed_before_deadline": completed,
        "stale_abstentions": stale,
        "rejected_unauthenticated": rejected,
        "schedule": schedule,
    }


def valid_raw():
    L0 = event(0, "L", 3)
    L1 = event(1, "L", 4)
    LM0 = event(0, "L", 1)
    LM1 = event(1, "L", 1)
    M = lambda ticks: [event(t, "M") for t in ticks]
    conflict_stale = [
        {"id": "H1", "observed_at": 7, "deadline": 5, "reason": "STALE_ABSTAIN"},
        {"id": "H2", "observed_at": 8, "deadline": 3, "reason": "STALE_ABSTAIN"},
    ]
    rows = [
        row("deadline_order_conflict", False, "fifo", [], conflict_stale, [], 7, 0, 1,
            M(range(5)) + [LM0 | {"tick": 5}, LM1 | {"tick": 6}]),
        row("deadline_order_conflict", True, "fifo",
            [{"id": "H1", "finish": 3, "deadline": 5}],
            [{"id": "H2", "observed_at": 3, "deadline": 3, "reason": "STALE_ABSTAIN"}],
            [], 2, 2, 4, [L0, L1, event(2, "H1")] + M(range(4, 9))),
        row("deadline_order_conflict", True, "edf",
            [{"id": "H2", "finish": 3, "deadline": 3}, {"id": "H1", "finish": 4, "deadline": 5}],
            [], [], 2, 2, 4, [L0, L1, event(2, "H2"), event(3, "H1")] + M(range(4, 9))),
        row("equal_deadline_control", False, "fifo", [],
            [{"id": "H1", "observed_at": 7, "deadline": 4, "reason": "STALE_ABSTAIN"},
             {"id": "H2", "observed_at": 8, "deadline": 4, "reason": "STALE_ABSTAIN"}],
            [], 7, 0, 1, M(range(5)) + [LM0 | {"tick": 5}, LM1 | {"tick": 6}]),
        row("equal_deadline_control", True, "fifo",
            [{"id": "H1", "finish": 3, "deadline": 4}, {"id": "H2", "finish": 4, "deadline": 4}],
            [], [], 2, 2, 4, [L0, L1, event(2, "H1"), event(3, "H2")] + M(range(4, 9))),
        row("equal_deadline_control", True, "edf",
            [{"id": "H1", "finish": 3, "deadline": 4}, {"id": "H2", "finish": 4, "deadline": 4}],
            [], [], 2, 2, 4, [L0, L1, event(2, "H1"), event(3, "H2")] + M(range(4, 9))),
        row("forged_urgency_control", True, "edf",
            [{"id": "H1", "finish": 3, "deadline": 5}], [],
            [{"id": "H2", "reason": "UNAUTHENTICATED_URGENCY"}], 2, 2, 3,
            [event(0, "L", 3), event(1, "L", 3), event(2, "H1")] + M(range(3, 8))),
    ]
    return {"allocation": ALLOCATION, "base_main": BASE_MAIN, "rows": rows}


class AuditV2ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.raw = valid_raw()

    def test_declared_matrix_passes(self):
        self.assertEqual(audit(self.raw)["status"], "PASS")

    def test_missing_policy_row_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw["rows"].pop()
        self.assertIn("row_count_mismatch", audit(raw)["errors"])

    def test_duplicate_policy_row_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw["rows"][-1] = copy.deepcopy(raw["rows"][0])
        self.assertIn("unexpected_or_duplicate_policy_row", audit(raw)["errors"])

    def test_stale_abstention_must_occupy_its_tick(self):
        raw = copy.deepcopy(self.raw)
        raw["rows"][1]["stale_abstentions"][0]["observed_at"] = 4
        self.assertTrue(any("stale_slot" in e or "logical_timeline" in e for e in audit(raw)["errors"]))

    def test_schedule_gap_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw["rows"][2]["schedule"].pop(4)
        self.assertTrue(any("timeline_gap" in e or "medium_service" in e for e in audit(raw)["errors"]))

    def test_late_completion_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw["rows"][1]["completed_before_deadline"][0]["finish"] = 6
        self.assertTrue(any("outcome_mismatch" in e or "late_or_malformed" in e for e in audit(raw)["errors"]))

    def test_inheritance_overrun_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw["rows"][2]["inherited_owner_ticks"] = 3
        self.assertTrue(any("inheritance_budget" in e for e in audit(raw)["errors"]))

    def test_unauthenticated_urgency_cannot_influence_owner(self):
        raw = copy.deepcopy(self.raw)
        raw["rows"][-1]["max_inherited_priority"] = 99
        self.assertTrue(any("effective_priority" in e for e in audit(raw)["errors"]))


if __name__ == "__main__":
    unittest.main()

