import copy
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from action_validity_admission_v1 import CONTRACT_FORMAT, SNAPSHOT_FORMAT, action_fingerprint, evaluate_action_validity
from final_action_admission_v2 import decide_final_admission, record_action_validity
from running_action_guard_v2 import RunningActionGuardV2
from executor_v10 import program_sha256


BINDING = {"focus": 7, "surface": 8, "geometry": [0, 0, 640, 480]}
COMMANDS = [{"action": "forward", "extent": "short"},
            {"action": "fire", "extent": "pulse"}]
FALLBACK = [{"action": "retreat_fire", "extent": "short"}]


def snapshot(sequence, capture_ns, health=90):
    return {"format": SNAPSHOT_FORMAT, "sequence": sequence, "capture_ns": capture_ns,
            "binding": BINDING, "signals": {"health": {"status": "observed", "value": health}}}


def action():
    return {"commands": copy.deepcopy(COMMANDS),
            "contingencies": [{"after_command": 0, "condition": "no_visible_effect",
                               "commands": copy.deepcopy(FALLBACK)}],
            "action_validity": [{"critical_health_minimum": 40}]}


def ready():
    contract = {"format": CONTRACT_FORMAT, "action_fingerprint": action_fingerprint(COMMANDS),
        "source": {"sequence": 1, "capture_ns": 100, "binding": BINDING,
                   "signals": {"health": {"status": "observed", "value": 90}}},
        "max_current_age_ms": 500,
        "predicates": [{"signal_id": "health", "operator": "minimum", "value": 40}]}
    validity = evaluate_action_validity(COMMANDS, contract, snapshot(2, 200), 201)
    receipt = decide_final_admission({"turn_id": "t", "status": "completed",
        "answer_eligible": True, "terminal_observed_ns": 10}, None, 11)
    return record_action_validity(receipt, COMMANDS, validity)


def program(role, commands, indices, after=None):
    return {"role": role, "semantic_commands": copy.deepcopy(commands),
            "command_indices": indices, "contingency_after": after,
            "compiled_steps": [{"op": "hold", "keys": ["x"], "duration_ms": 10}
                               for _ in commands]}


def compiler(commands):
    return [{"op": "hold", "keys": ["x"], "duration_ms": 10}
            for _ in commands]


def guard_v2():
    return RunningActionGuardV2(action(), ready(), compiler, "test-compiler-v1")


def admission(identifier, program_value, sent=210, accepted_ns=211):
    command = {"op": "submit", "id": identifier, "expected_sequence": 2,
               "valid_until_ns": 1000, "steps": copy.deepcopy(program_value["compiled_steps"])}
    submit = {"command": command, "sent_ns": sent}
    accepted = {"event": "accepted", "id": identifier,
                "steps": len(command["steps"]),
                "program_sha256": program_sha256(command["steps"]),
                "accepted_ns": accepted_ns}
    return submit, accepted


def terminal(identifier, status, when):
    return {"event": "terminal", "id": identifier, "status": status,
            "terminal_ns": when, "release": {"verified": True,
            "keys_down": [], "buttons_down": [], "verified_ns": when - 1}}


class RunningActionGuardV2Tests(unittest.TestCase):
    def test_malformed_semantic_command_fails_at_guard_construction(self):
        for bad in ("forward", {"action": "forward"},
                    {"action": "forward", "extent": "short", "extra": True}):
            candidate = action()
            candidate["commands"][0] = bad
            with self.assertRaises(ValueError):
                RunningActionGuardV2(candidate, ready(), compiler,
                                     "test-compiler-v1")

    def test_first_program_binds_planner_slice_submit_and_historical_acceptance(self):
        guard = guard_v2()
        p = program("primary", COMMANDS[:1], [0]); submit, accepted = admission("p1", p)
        receipt = guard.admit_program(p, submit, accepted)
        self.assertTrue(receipt["current_input_authority"])
        self.assertEqual(receipt["historical_first_admission"]["id"], "p1")
        self.assertEqual(receipt["program_bindings"][0]["program"]["semantic_commands"], COMMANDS[:1])
        self.assertIn("root current_input_authority is authoritative", receipt["authority_semantics"])

    def test_wrong_slice_indices_or_compiled_submit_are_rejected(self):
        for mutate in (lambda p: p["command_indices"].__setitem__(0, 1),
                       lambda p: p["semantic_commands"].__setitem__(0, COMMANDS[1])):
            guard = guard_v2(); p = program("primary", COMMANDS[:1], [0])
            mutate(p); submit, accepted = admission("p1", p)
            with self.assertRaises(ValueError): guard.admit_program(p, submit, accepted)
        guard = guard_v2(); p = program("primary", COMMANDS[:1], [0])
        submit, accepted = admission("p1", p); submit["command"]["steps"][0]["keys"] = ["wrong"]
        with self.assertRaises(ValueError): guard.admit_program(p, submit, accepted)

        guard = guard_v2(); p = program("primary", COMMANDS[:1], [0])
        p["compiled_steps"][0]["keys"] = ["wrong"]
        submit, accepted = admission("p1", p)
        with self.assertRaises(ValueError): guard.admit_program(p, submit, accepted)

        guard = guard_v2(); p = program("primary", COMMANDS[:1], [0])
        submit, accepted = admission("p1", p)
        accepted["program_sha256"] = "0" * 64
        with self.assertRaises(ValueError): guard.admit_program(p, submit, accepted)

    def test_second_primary_requires_contiguous_slice_and_fresh_check(self):
        guard = guard_v2()
        p1 = program("primary", COMMANDS[:1], [0]); guard.admit_program(p1, *admission("p1", p1))
        guard.check_current(snapshot(3, 300), 301)
        guard.record_completed_terminal(terminal("p1", "completed", 310))
        p2 = program("primary", COMMANDS[1:], [1])
        with self.assertRaises(ValueError): guard.admit_program(p2, *admission("p2", p2, 320, 321))
        guard.check_current(snapshot(4, 315), 316)
        receipt = guard.admit_program(p2, *admission("p2", p2, 320, 321))
        self.assertEqual(len(receipt["program_bindings"]), 2)

    def test_fallback_requires_exact_authored_branch_and_effect_evidence(self):
        guard = guard_v2()
        primary = program("primary", COMMANDS[:1], [0]); guard.admit_program(primary, *admission("p1", primary))
        guard.check_current(snapshot(3, 300), 301)
        guard.record_completed_terminal(terminal("p1", "completed", 310))
        guard.check_current(snapshot(4, 315), 316)
        fallback = program("fallback", FALLBACK, [0], 0)
        with self.assertRaises(ValueError):
            guard.admit_program(fallback, *admission("f1", fallback, 320, 321))
        evidence = {"after_command": 0, "condition": "no_visible_effect",
                    "primary_program_id": "p1", "command_index": 0,
                    "semantic_command": COMMANDS[0],
                    "effect_receipt": {"action": "forward", "extent": "short",
                        "result": "no_visible_effect", "effect_observed_ns": 309}}
        receipt = guard.admit_program(
            fallback, *admission("f1", fallback, 320, 321), branch_evidence=evidence)
        self.assertEqual(receipt["program_bindings"][-1]["program"]["role"], "fallback")

        for path, bad in (
                (("primary_program_id",), "wrong"),
                (("effect_receipt", "result"), "visible_change"),
                (("semantic_command",), COMMANDS[1])):
            fresh = guard_v2()
            first = program("primary", COMMANDS[:1], [0])
            fresh.admit_program(first, *admission("p1", first))
            fresh.check_current(snapshot(3, 300), 301)
            fresh.record_completed_terminal(terminal("p1", "completed", 310))
            fresh.check_current(snapshot(4, 315), 316)
            forged = copy.deepcopy(evidence)
            if len(path) == 1:
                forged[path[0]] = bad
            else:
                forged[path[0]][path[1]] = bad
            with self.assertRaises(ValueError):
                fresh.admit_program(
                    fallback, *admission("f1", fallback, 320, 321),
                    branch_evidence=forged)

    def test_running_rejection_and_release_update_one_root_authority(self):
        guard = guard_v2()
        p = program("primary", COMMANDS[:1], [0]); guard.admit_program(p, *admission("p1", p))
        receipt = guard.check_current(snapshot(3, 300, health=20), 301)
        self.assertFalse(receipt["current_input_authority"])
        self.assertTrue(receipt["physical_input_may_be_down"])
        guard.record_cancel_requested({"event": "cancel_requested", "id": "p1",
                                       "matched": True, "requested_ns": 302})
        receipt = guard.record_cancelled_terminal(terminal("p1", "cancelled", 305))
        self.assertFalse(receipt["current_input_authority"])
        self.assertTrue(receipt["physical_release_verified"])
        self.assertEqual(receipt["state"], "REVOKED_ACTION_NOT_CURRENT")

    def test_completed_action_has_no_current_authority_and_keeps_history(self):
        guard = guard_v2()
        p = program("primary", COMMANDS, [0, 1]); guard.admit_program(p, *admission("p", p))
        guard.check_current(snapshot(3, 300), 301)
        receipt = guard.record_completed_terminal(terminal("p", "completed", 310), final=True)
        self.assertEqual(receipt["state"], "COMPLETED")
        self.assertFalse(receipt["current_input_authority"])
        self.assertEqual(receipt["historical_first_admission"]["id"], "p")


if __name__ == "__main__": unittest.main()
