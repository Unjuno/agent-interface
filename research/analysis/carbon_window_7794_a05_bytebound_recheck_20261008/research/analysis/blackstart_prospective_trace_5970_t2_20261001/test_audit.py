import copy
import unittest

from candidate import classify


def fixture():
    actions = []
    app = []
    observer = []
    for index, (kind, suffix) in enumerate((("KeyPress", "shift-1"), ("KeyRelease", "shift-2")), start=1):
        act = f"epoch:{suffix}"
        for seq, phase in enumerate(("arm_request", "both_armed", "dispatch_request", "dispatch_sync_complete"), start=1):
            actions.append({"driver_seq": (index - 1) * 4 + seq, "phase": phase, "actuation_id": act, "event_kind": kind, "keycode": 50})
        parent = [f"act:{act}"]
        app.extend(
            [
                {"kind": "arm_ack", "actuation_id": act},
                {"source": "app", "kind": kind, "source_seq": index, "event_id": f"app:{index}", "actuation_id": act, "causal_parent_ids": parent, "keycode": 50, "x_time": index, "mono_ns": 999999},
            ]
        )
        observer.extend(
            [
                {"kind": "arm_ack", "actuation_id": act},
                {"source": "observer", "kind": kind, "source_seq": index, "event_id": f"observer:epoch:{index}", "epoch": "epoch", "actuation_id": act, "causal_parent_ids": parent, "keycode": 50, "x_time": index, "mono_ns": 1},
            ]
        )
    return actions, app, observer


class ProspectiveTraceTests(unittest.TestCase):
    def test_explicit_parent_pair_passes_even_with_reversed_clock_values(self):
        actions, app, observer = fixture()
        self.assertEqual(classify(actions, app, observer, False), "PASS_PROSPECTIVE_CAUSAL_IDS")

    def test_missing_observer_event_holds(self):
        actions, app, observer = fixture()
        observer = [r for r in observer if not (r.get("source") == "observer" and r.get("actuation_id") == "epoch:shift-1")]
        self.assertEqual(classify(actions, app, observer, False), "HOLD_INCOMPLETE_OR_NONNEUTRAL")

    def test_mismatched_parent_holds(self):
        actions, app, observer = fixture()
        next(r for r in observer if r.get("source") == "observer")["causal_parent_ids"] = ["act:other"]
        self.assertEqual(classify(actions, app, observer, False), "HOLD_MISMATCHED_CAUSAL_RECORDS")

    def test_duplicate_source_sequence_holds(self):
        actions, app, observer = fixture()
        next(r for r in observer if r.get("source") == "observer" and r.get("actuation_id") == "epoch:shift-2")["source_seq"] = 1
        self.assertEqual(classify(actions, app, observer, False), "HOLD_INCOMPLETE_OR_NONNEUTRAL")

    def test_missing_arm_ack_holds(self):
        actions, app, observer = fixture()
        observer = [r for r in observer if not (r.get("kind") == "arm_ack" and r.get("actuation_id") == "epoch:shift-1")]
        self.assertEqual(classify(actions, app, observer, False), "HOLD_INCOMPLETE_OR_DUPLICATE_PROVENANCE")

    def test_non_neutral_terminal_state_holds(self):
        actions, app, observer = fixture()
        self.assertEqual(classify(actions, app, observer, True), "HOLD_INCOMPLETE_OR_NONNEUTRAL")

    def test_wrong_dispatch_event_is_not_admitted(self):
        actions, app, observer = fixture()
        next(r for r in actions if r["phase"] == "dispatch_request")["event_kind"] = "KeyRelease"
        self.assertEqual(classify(actions, app, observer, False), "HOLD_MISMATCHED_CAUSAL_RECORDS")

    def test_shared_source_local_event_id_is_rejected(self):
        actions, app, observer = fixture()
        next(r for r in observer if r.get("source") == "observer")["event_id"] = next(r for r in app if r.get("source") == "app")["event_id"]
        self.assertEqual(classify(actions, app, observer, False), "HOLD_MISMATCHED_CAUSAL_RECORDS")


if __name__ == "__main__":
    unittest.main()
