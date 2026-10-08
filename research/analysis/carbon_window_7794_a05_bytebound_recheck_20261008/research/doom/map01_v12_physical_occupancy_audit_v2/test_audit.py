"""Offline trace-integrity controls; no X11, game, model or live allocation."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from audit import REPO, R1, STEPS, expected_sources, program_sha, verify
sys.path.insert(0, str(R1))
spec = importlib.util.spec_from_file_location("r1_frozen_evaluate", R1 / "evaluate.py")
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)

PID = "r1-physical-occupancy-1"
EXPECTED_SOURCES = {"external/input_owner_v12.py": "a" * 64,
                    "doom/session_map01_v13.py": "b" * 64}


def fixture():
    """Positive trace, with matching admitted plan, physical evidence and end."""
    rows = [
        {"event": "command", "received_ns": 90, "command": {
            "op": "submit", "id": PID, "steps": copy.deepcopy(STEPS),
            "expected_sequence": 1, "valid_until_ns": 1000}},
        {"event": "accepted", "id": PID, "steps": 2,
         "program_sha256": program_sha(STEPS), "intent_token": "intent-1",
         "accepted_ns": 100, "valid_until_ns": 1000},
    ]
    for position, key in enumerate(("a", "d")):
        lineage = {"actuation_id": f"act-{key}", "owner_id": "owner-1",
                   "intent_token": "intent-1", "key": key}
        rows.append({"event": "input_admission", "key": key,
                     "intent_token": "intent-1", "physical_key_measurement": {
                         "adapter_edge": {**lineage, "edge": "down",
                            "status": "CONFIRMED_PHYSICAL_DOWN",
                            "interval": [110 + 10 * position, 112 + 10 * position]}}})
    rows.append({"event": "keys_held", "id": PID, "step": 0,
                 "keys": ["a", "d"], "input_ack_ns": 150})
    for position, key in enumerate(("a", "d")):
        lineage = {"actuation_id": f"act-{key}", "owner_id": "owner-1",
                   "intent_token": "intent-1", "key": key}
        rows.append({"event": "input_release_transition", **lineage,
            "operation": "up", "transition_schema": "input-release-transition-v3",
            "release_batch_schema": "input-release-batch-v3",
            "release_batch_identifier": PID, "release_batch_step": 0,
            "release_batch_size": 2, "release_batch_position": position,
            "ordinary_release_candidate": True, "owner_transition_verified": True,
            "physical_verification_authoritative": False, "grants_input_authority": False,
            "valid_until_ns": 1000,
            "release_call_started_ns": 300 + 10 * position,
            "release_call_returned_ns": 307 + 10 * position,
            "owned_keycodes_after_batch": [], "physical_key_measurement": {
                "post_sample": {"down": False}, "adapter_edge": {
                    **lineage, "edge": "up", "status": "CONFIRMED_PHYSICAL_UP",
                    "interval": [302 + 10 * position, 305 + 10 * position]}}})
    rows.extend([
        {"event": "step_completed", "id": PID, "step": 0, "completed_ns": 350},
        {"event": "step_completed", "id": PID, "step": 1, "completed_ns": 400},
        {"event": "terminal", "id": PID, "status": "completed", "steps_completed": 2,
         "terminal_ns": 450, "release": {"verified": True, "keys_down": [],
            "buttons_down": [], "verified_ns": 440}}])
    return rows, dict(EXPECTED_SOURCES)


def event(rows, kind):
    return next(row for row in rows if row["event"] == kind)


def corruptions():
    def missing_acceptance(rows, sources):
        rows[:] = [r for r in rows if r["event"] != "accepted"]
    def duplicate_acceptance(rows, sources):
        rows.append(copy.deepcopy(event(rows, "accepted")))
    def missing_submit(rows, sources):
        rows[:] = [r for r in rows if r["event"] != "command"]
    def different_submit(rows, sources):
        event(rows, "command")["command"]["steps"][0]["keys"] = ["Up"]
    def batch_attached_to_observe(rows, sources):
        for r in rows:
            if r["event"] == "input_release_transition": r["release_batch_step"] = 1
    return {
        "missing_acceptance": missing_acceptance,
        "duplicate_acceptance": duplicate_acceptance,
        "accepted_token_mismatch": lambda r, s: event(r, "accepted").update(intent_token="foreign"),
        "accepted_program_mismatch": lambda r, s: event(r, "accepted").update(program_sha256="0" * 64),
        "accepted_program_id_mismatch": lambda r, s: event(r, "accepted").update(id="other-plan"),
        "missing_submit": missing_submit,
        "different_submitted_keys": different_submit,
        "release_batch_attached_to_observe": batch_attached_to_observe,
        "acceptance_after_down": lambda r, s: event(r, "accepted").update(accepted_ns=140),
        "terminal_before_up": lambda r, s: event(r, "terminal").update(terminal_ns=200),
        "terminal_keys_not_empty": lambda r, s: event(r, "terminal")["release"].update(keys_down=[38]),
        "terminal_release_unverified": lambda r, s: event(r, "terminal")["release"].update(verified=False),
        "terminal_step_count_wrong": lambda r, s: event(r, "terminal").update(steps_completed=1),
        "missing_sources": lambda r, s: s.clear(),
        "source_digest_mismatch": lambda r, s: s.update({"external/input_owner_v12.py": "c" * 64}),
        "accepted_deadline_mismatch": lambda r, s: event(r, "accepted").update(valid_until_ns=999),
        "terminal_release_before_up": lambda r, s: event(r, "terminal")["release"].update(verified_ns=200),
        "terminal_buttons_not_empty": lambda r, s: event(r, "terminal")["release"].update(buttons_down=[1]),
        "terminal_noninteger_step_count": lambda r, s: event(r, "terminal").update(steps_completed=2.0),
        "accepted_noninteger_step_count": lambda r, s: event(r, "accepted").update(steps=2.0),
        "down_outer_token_mismatch": lambda r, s: event(r, "input_admission").update(intent_token="foreign"),
        "observe_before_hold_completion": lambda r, s: r[-2].update(completed_ns=340),
        "observe_completion_time_missing": lambda r, s: r[-2].pop("completed_ns"),
    }


def legacy_pass(rows):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "events.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return legacy.evaluate(root, PID)["pass"]


def controls():
    rows, sources = fixture()
    result = {"positive_legacy_pass": legacy_pass(rows),
              "positive_supplement": verify(rows, sources, PID, EXPECTED_SOURCES),
              "corruptions": []}
    for name, mutate in corruptions().items():
        rows, sources = fixture()
        mutate(rows, sources)
        verdict = verify(rows, sources, PID, EXPECTED_SOURCES)
        result["corruptions"].append({"name": name, "legacy_pass": legacy_pass(rows),
                                      "supplement_pass": verdict["passed"],
                                      "errors": verdict["errors"]})
    return result


def executor_fixture():
    """Use real Executor v12 lifecycle with synthetic edges, without OS input.

    The fake backend does not run a 250 ms hold or measure physical occupancy.
    This checks compatibility with emitted lifecycle fields, not timing accuracy.
    """
    sys.path.insert(0, str(REPO / "research/live_control"))
    from executor_v12 import Executor

    rows = []
    terminal = threading.Event()

    def emit(row):
        rows.append(row)
        if row["event"] == "terminal":
            terminal.set()

    class SyntheticBackend:
        sequence = 1

        def validate(self, steps):
            if steps != STEPS:
                raise ValueError("synthetic backend accepts only the fixed R1 program")

        def execute(self, step, cancel, identifier, index):
            if index != 0:
                return
            template, _ = fixture()
            for row in template:
                if row["event"] not in ("input_admission", "keys_held", "input_release_transition"):
                    continue
                if row["event"] == "keys_held":
                    row["input_ack_ns"] = time.perf_counter_ns()
                else:
                    row["intent_token"] = self.lease.intent_token
                    edge = row["physical_key_measurement"]["adapter_edge"]
                    edge["intent_token"] = self.lease.intent_token
                    if row["event"] == "input_release_transition":
                        row["valid_until_ns"] = self.lease.deadline
                        row["release_call_started_ns"] = time.perf_counter_ns()
                    edge["interval"] = [time.perf_counter_ns(), time.perf_counter_ns()]
                    if row["event"] == "input_release_transition":
                        row["release_call_returned_ns"] = time.perf_counter_ns()
                emit(row)

        def release_all(self):
            return {"verified": True, "keys_down": [], "buttons_down": [],
                    "verified_ns": time.perf_counter_ns()}

    executor = Executor(SyntheticBackend(), emit)
    deadline = time.perf_counter_ns() + 5_000_000_000
    rows.append({"event": "command", "received_ns": time.perf_counter_ns(),
                 "command": {"op": "submit", "id": PID, "steps": copy.deepcopy(STEPS),
                             "expected_sequence": 1, "valid_until_ns": deadline}})
    try:
        executor.submit(PID, STEPS, 1, deadline)
        if not terminal.wait(2):
            raise TimeoutError("synthetic executor did not finish")
    finally:
        executor.close()
    return rows, dict(EXPECTED_SOURCES)


class PhysicalAdmissionAuditTests(unittest.TestCase):
    def test_correct_two_key_trace(self):
        rows, sources = fixture()
        self.assertTrue(legacy_pass(rows))
        self.assertTrue(verify(rows, sources, PID, EXPECTED_SOURCES)["passed"])

    def test_distinct_provenance_corruptions(self):
        for row in controls()["corruptions"]:
            with self.subTest(case=row["name"]):
                self.assertTrue(row["legacy_pass"], "frozen evaluator behavior changed")
                self.assertFalse(row["supplement_pass"])

    def test_incomplete_legacy_physical_evidence_stays_rejected(self):
        rows, sources = fixture()
        event(rows, "input_admission")["physical_key_measurement"]["adapter_edge"].update(
            status="PRESS_UNCONFIRMED", interval=None)
        self.assertFalse(legacy_pass(rows))
        self.assertFalse(verify(rows, sources, PID, EXPECTED_SOURCES)["passed"])

    def test_empty_expectations_never_authorize(self):
        rows, sources = fixture()
        verdict = verify(rows, sources, PID, {})
        self.assertFalse(verdict["passed"])
        self.assertFalse(verdict["full_r1_gate_eligible"])

    def test_actual_executor_lifecycle_with_synthetic_backend(self):
        rows, sources = executor_fixture()
        self.assertTrue(legacy_pass(rows))
        verdict = verify(rows, sources, PID, EXPECTED_SOURCES)
        self.assertTrue(verdict["passed"], verdict)
        self.assertFalse(verdict["full_r1_gate_eligible"])

    def test_source_freeze_still_matches_git(self):
        self.assertEqual(len(expected_sources()), 6)

    def test_malformed_evidence_returns_refusal(self):
        rows, sources = fixture()
        for kind, field in (("accepted", "program_sha256"), ("terminal", "release"),
                            ("command", "command"), ("input_admission", "physical_key_measurement")):
            for value in (None, [], "bad", 1, True):
                altered = copy.deepcopy(rows)
                event(altered, kind)[field] = value
                with self.subTest(kind=kind, field=field, value=value):
                    self.assertFalse(verify(altered, sources, PID, EXPECTED_SOURCES)["passed"])
        self.assertFalse(verify([None], sources, PID, EXPECTED_SOURCES)["passed"])
        self.assertFalse(verify(rows, sources, PID, {"bad": None})["passed"])


if __name__ == "__main__":
    unittest.main()
