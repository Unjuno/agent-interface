"""Synthetic 24-stage composition of the production MAP01 caller and contract.

No VizDoom/X11 process or allocation is started. The fixture only checks
pure state-machine composition; it cannot establish a live task effect.
"""
import unittest

from map01_door_driver_protocol import DoorDriverProtocol
from map01_door_task_contract import DoorTaskContract, validate_initial_cover
from map01_reverse_program import reverse_manifest, reverse_stages
from test_map01_door_task_contract import accepted, finish, release


OWNER = "owner"
GENERATION = 0
SURFACE = 7
PROCESS = "abc"
WINDOW = "def"


def observation(identifier, sequence, capture_ns, *, typed=False):
    binding = {"surface": SURFACE, "focus": SURFACE}
    row = {
        "event": "typed_observation" if typed else "observation",
        "id": identifier, "step": 0, "sequence": sequence,
        "capture_ns": capture_ns, "pointer_binding": binding,
        "renewal_owner_id": OWNER, "input_owner_generation": GENERATION,
        "target_process_identity": {"sequence": sequence, "surface": SURFACE, "digest": PROCESS},
        "target_renewal_window_identity": {"sequence": sequence, "surface": SURFACE, "digest": WINDOW},
        "frame_rgb_sha256": f"{sequence:064x}", "exact": True,
        "focus_samples_match": True, "input_focus_before": SURFACE,
        "input_focus_after": SURFACE,
    }
    if typed:
        row["signals"] = {
            name: {"status": "observed", "value": value, "sequence": sequence,
                   "capture_ns": capture_ns, "binding": binding, "signal_id": name}
            for name, value in (("health", 100), ("ammo", 50))
        }
    return row


class CoverAdapter:
    def __init__(self, source):
        self.source = source

    def completed(self, identifier, terminal, accepted_row, events):
        validate_initial_cover(self.source, terminal, accepted_row, events)


class EastReturnCompositionReplayTests(unittest.TestCase):
    def replay(self, stop_after=None, arm="east-return"):
        protocol = DoorDriverProtocol(
            "use", "a" * 64, "b" * 64, "c" * 64, 870,
            traverse=True, reverse_arm=arm)
        contract = DoorTaskContract("use", traverse=True, reverse_arm=arm)
        now = 1_100_000_000
        fixture = {
            "manifest_sha256": "a" * 64, "save_sha256": "b" * 64,
            "after_load_tic": 870,
            "setup_candidate_evidence": {"evidence_sha256": "c" * 64},
        }
        ready = {
            "event": "ready", "fixture": fixture,
            "post_load_clock_gate": {"passed": True},
            "reverse_door_program": reverse_manifest(arm),
        }
        self.assertIsNone(protocol.receive(ready, now))
        initial_typed = observation("initial", 1, now - 1, typed=True)
        initial = observation("initial", 1, now - 1)
        self.assertIsNone(protocol.receive(initial_typed, now))
        command = protocol.receive(initial, now)

        program = [
            ("cover-0", [{"op": "coast", "duration_ms": 200, "sample_ms": 100}]),
        ]
        program.extend((f"approach-{i}", [{"op": "hold", "keys": ["Up"], "duration_ms": 600}])
                       for i in range(1, 5))
        program.extend([
            ("intervention", [{"op": "hold", "keys": ["e"], "duration_ms": 120}]),
            ("traverse-1", [{"op": "hold", "keys": ["Up"], "duration_ms": 300}]),
        ])
        program.extend(reverse_stages(arm))
        self.assertEqual(len(program), 26 if arm=="east-return-reopen" else 24)

        previous = "cover-0"
        for index, (identifier, steps) in enumerate(program):
            self.assertEqual((command.get("id"), command.get("steps")), (identifier, steps))
            if identifier == "cover-0":
                finish(CoverAdapter(initial), command)
                contract.identity = (OWNER, GENERATION, SURFACE, PROCESS, WINDOW)
            else:
                source = protocol.latest
                self.assertEqual(source["id"], previous)
                terminal = release(previous)
                accepted_row = accepted(previous)
                deadline = contract.authorize(command, source, now, terminal, accepted_row)
                self.assertGreater(deadline, now)
                contract.deadline = deadline
                finish(contract, command)

            sequence = protocol.latest["sequence"] + 1
            capture = now + 1
            typed = observation(identifier, sequence, capture, typed=True)
            full = observation(identifier, sequence, capture)
            self.assertIsNone(protocol.receive(typed, capture + 1))
            self.assertIsNone(protocol.receive(full, capture + 1))
            terminal_row = {"event": "terminal", "id": identifier, "status": "completed"}
            settle = protocol.receive(terminal_row, capture + 2)
            self.assertEqual(settle, {"op": "door-settle"})
            wait = {"event": "door_settle", "operation_id": identifier, "status": "WAIT"}
            self.assertEqual(protocol.receive(wait, capture + 3), {"op": "door-settle"})
            done = {"event": "door_settle", "operation_id": identifier, "status": "DONE"}
            command = protocol.receive(done, capture + 4)
            previous = identifier
            now = capture + 5
            if identifier == stop_after:
                return protocol, contract, command, protocol.latest

        self.assertEqual(command, {"op": "finish"})
        self.assertTrue(protocol.stage == "finish")
        self.assertTrue(contract.finished)
        return protocol, contract, command, protocol.latest

    def test_reopen_arm_composes_all_26_registered_stages(self):
        protocol, contract, command, _ = self.replay(arm="east-return-reopen")
        self.assertEqual(command, {"op": "finish"})
        self.assertEqual(protocol.index, 26)
        self.assertTrue(contract.finished)

    def test_synthetic_positive_composes_all_24_registered_stages(self):
        protocol, contract, command, _ = self.replay()
        self.assertEqual(command, {"op": "finish"})
        self.assertEqual(protocol.index, 24)
        self.assertTrue(contract.finished)

    def test_release_unknown_after_cross_is_rejected_before_caller_write(self):
        protocol, _, command, _ = self.replay(stop_after="reverse-cross")
        self.assertEqual(command["id"], "east-turn-1")
        with self.assertRaisesRegex(ValueError, "runtime rejected"):
            protocol.receive(
                {"event": "input_release_unverified", "id": "reverse-cross"},
                2_000_000_000)

    def test_contract_rejects_tampered_first_east_turn(self):
        _, contract, _, source = self.replay(stop_after="reverse-cross")
        # Reuse the valid prior receipts; only the registered turn duration changes.
        bad = {
            "op": "submit", "id": "east-turn-1",
            "steps": [{"op": "hold", "keys": ["Right"], "duration_ms": 601}],
            "expected_sequence": source["sequence"],
            "valid_until_ns": source["capture_ns"] + 20_000_000_000,
        }
        with self.assertRaisesRegex(ValueError, "invalid source or command"):
            contract.authorize(
                bad, source, source["capture_ns"] + 1,
                release("reverse-cross"), accepted("reverse-cross"))



class EastReturnWireValidationTests(unittest.TestCase):
    def test_protocol_trace_raw_contract_owner_and_audit_validators_join(self):
        import copy
        from map01_east_return_audit import (
            validate_caller_policy, validate_contract_replay, validate_owner_events,
            validate_raw_delivery, validate_trace,
        )

        protocol = DoorDriverProtocol(
            "use", "a" * 64, "b" * 64, "c" * 64, 870,
            traverse=True, reverse_arm="east-return")
        events = []
        driver = []
        samples = []
        owner = []
        def receive(row, stamp):
            row = dict(row)
            row.setdefault("emit_ns", stamp)
            events.append(row)
            driver.append({"phase": "received", "event": row["event"],
                           "id": row.get("id"), "emit_ns": row["emit_ns"],
                           "recorded_ns": stamp})
            result = protocol.receive(row, stamp)
            if result is not None:
                send(result, stamp + 1)
            return result

        def send(command, stamp):
            driver.append({"phase": "sent", "command": command, "recorded_ns": stamp})
            receive({"event": "command", "command": command,
                     "received_ns": stamp + 1}, stamp + 1)

        base = 10_000_000_000
        ready = {
            "event": "ready",
            "fixture": {
                "manifest_sha256": "a" * 64, "save_sha256": "b" * 64,
                "after_load_tic": 870,
                "setup_candidate_evidence": {"evidence_sha256": "c" * 64},
            },
            "post_load_clock_gate": {"passed": True},
            "reverse_door_program": reverse_manifest("east-return"),
        }
        receive(ready, base)
        receive(observation("initial", 1, base - 10, typed=True), base + 1)
        receive(observation("initial", 1, base - 10), base + 2)

        program = [
            ("cover-0", [{"op": "coast", "duration_ms": 200, "sample_ms": 100}]),
        ]
        program.extend((f"approach-{i}", [{"op": "hold", "keys": ["Up"], "duration_ms": 600}])
                       for i in range(1, 5))
        program.extend([
            ("intervention", [{"op": "hold", "keys": ["e"], "duration_ms": 120}]),
            ("traverse-1", [{"op": "hold", "keys": ["Up"], "duration_ms": 300}]),
        ])
        program.extend(reverse_stages("east-return"))
        for index, (stage, steps) in enumerate(program):
            command_row = next(row for row in events
                               if row.get("event") == "command"
                               and row.get("command", {}).get("op") == "submit"
                               and row.get("command", {}).get("id") == stage)
            command = command_row["command"]
            self.assertEqual(command["steps"], steps)
            t = command_row["received_ns"] + 10
            token = "token-" + stage
            accepted_ns = t + 10
            program_sha = __import__("hashlib").sha256(
                __import__("json").dumps(steps, sort_keys=True, separators=(",", ":"),
                                         ensure_ascii=False, allow_nan=False).encode()).hexdigest()
            accepted = {
                "event": "accepted", "id": stage, "intent_token": token,
                "steps": len(steps), "program_sha256": program_sha,
                "accepted_ns": accepted_ns,
            }
            receive(accepted, accepted_ns)

            keyup = None
            if steps[0]["op"] == "hold":
                key = steps[0]["keys"][0]
                admitted = t + 20
                ack = t + 30
                admission_deadline = accepted_ns + 100
                admission = {
                    "event": "input_admission", "id": stage, "step": 0,
                    "key": key, "keycode": 111, "owner_id": "owner",
                    "intent_token": token, "admitted_ns": admitted,
                    "input_ack_ns": ack,
                    "first_press_deadline_ns": admission_deadline,
                    "first_press_submission_checked_before_deadline": True,
                    "valid_until_ns": command["valid_until_ns"],
                    "target_process_identity": [command["expected_sequence"], 7, "abc",
                                                command["valid_until_ns"]],
                }
                receive(admission, admitted)
                receive({"event": "keys_held", "id": stage, "step": 0,
                         "keys": [key], "input_ack_ns": ack}, ack)
                release_started = ack + steps[0]["duration_ms"] * 1_000_000
                sync_returned = release_started + 10_000_000
                keymap_sampled = release_started + 20_000_000
                keyup = {
                    "event": "owner_explicit_keyup", "operation": "up",
                    "owner_id": "owner", "key": key, "keycode": 111,
                    "intent_token": token, "valid_until_ns": command["valid_until_ns"],
                    "owner_keyrelease_started_ns": release_started,
                    "owner_sync_returned_ns": sync_returned,
                    "owner_keymap_sampled_ns": keymap_sampled,
                    "server_keyup_verified": True, "server_keyup_attempt_count": 1,
                    "server_keyup_attempts": [{
                        "attempt": 1, "keyrelease_started_ns": release_started,
                        "sync_returned_ns": sync_returned, "keymap_sampled_ns": keymap_sampled,
                        "server_key_down_before": True, "server_key_down_after": False,
                    }],
                    "server_key_down_after_keyup": False,
                    "key_state_source": "x11_query_keymap",
                    "server_sync_completed": True, "physical_verification_authoritative": False,
                    "cancel_requested_after_sync": False,
                    "release_batch_initial_up_count": 1,
                    "release_batch_key_order": [key],
                }
                transition = {
                    "event": "input_release_transition", "id": stage, "step": 0,
                    "operation": "up", "key": key, "owner_id": "owner",
                    "intent_token": token, "owner_transition_verified": True,
                    "admission_receipt_valid": True,
                    "admission_receipt": dict(admission, operation="down"),
                    "owner_thread_keyup_receipt": keyup,
                }
                receive(transition, sync_returned + 1)
                owner.append(keyup)
                capture = keymap_sampled + 1
                step_done_ns = keymap_sampled + 10
                terminal_ns = keymap_sampled + 30
                release_token = token
                release_verified_ns = keymap_sampled + 5
            else:
                receive({"event": "step_started", "id": stage, "step": 0,
                         "operation": "coast", "issued_ns": t + 20}, t + 20)
                capture = t + steps[0]["duration_ms"] * 1_000_000 + 10_000_000
                step_done_ns = capture + 10
                terminal_ns = capture + 20
                release_token = None
                release_verified_ns = terminal_ns - 5

            sequence = command["expected_sequence"] + 1
            receive(observation(stage, sequence, capture, typed=True), capture)
            receive(observation(stage, sequence, capture), capture + 1)
            if steps[0]["op"] == "coast":
                receive({
                    "event": "coast_result", "id": stage, "step": 0,
                    "samples": 1, "elapsed_ms": float(steps[0]["duration_ms"]),
                    "input_admissions": 0, "sequence": sequence,
                }, capture + 2)
            receive({"event": "step_completed", "id": stage, "step": 0,
                     "completed_ns": step_done_ns}, step_done_ns)
            release = {
                "event": "owner_release", "intent_token": release_token,
                "verified": True, "verified_ns": release_verified_ns,
                "keys_down": [], "buttons_down": [],
                "keys_unknown": [], "key_state_errors": [],
            }
            if steps[0]["op"] == "hold":
                release["intent_token"] = token
            terminal = {
                "event": "terminal", "id": stage, "status": "completed",
                "input_owner_id": "owner", "input_owner_generation": 0,
                "release": release, "terminal_ns": terminal_ns,
                "steps_completed": len(steps),
            }
            receive(terminal, terminal_ns)
            owner.append(dict(release))

            settle_request_1 = terminal_ns + 1
            receive({"event": "door_settle", "operation_id": stage,
                     "status": "WAIT"}, terminal_ns + 50)
            settle_request_2 = terminal_ns + 51
            # The receive helper records the command rows when the protocol
            # requests settlement; the synthetic sample occurs between the
            # last request and its DONE response.
            command_rows_for_stage = [row for row in events
                                      if row.get("event") == "command"
                                      and row.get("command", {}).get("op") == "door-settle"
                                      and row.get("command", {}).get("id") is None]
            del command_rows_for_stage
            receive({"event": "door_settle", "operation_id": stage,
                     "status": "DONE"}, terminal_ns + 100)
            done = next(row for row in reversed(events)
                        if row.get("event") == "door_settle"
                        and row.get("operation_id") == stage
                        and row.get("status") == "DONE")
            samples.append({
                "stage": stage, "status": "observed", "terminal_ns": terminal_ns,
                "started_ns": terminal_ns + 70, "finished_ns": terminal_ns + 80,
                "terminal_to_sample_ns": 70, "terminal_to_refresh_ns": 72,
                "terminal_to_state_ns": 80, "tic_before": index * 3,
                "getter_before_state": index * 3 + 1, "state_tic": index * 3 + 1,
                "getter_after_state": index * 3 + 1, "state_number": index + 1,
                "refresh_count": 1, "physical_neutral_before_after": True,
                "position_x": 0.0, "position_y": 0.0, "angle": 0.0,
                "health": 100.0, "death_count": 0.0, "kill_count": 0.0,
                "gap": 64.0, "floor_d": 0.0, "ceiling_d": 64.0,
                "sector_index": 27, "last_action": [0.0] * 9,
            })

        owner.append({"event": "owner_release", "reason": "close", "verified": True,
                      "keys_down": [], "buttons_down": [], "keys_unknown": [],
                      "key_state_errors": []})
        self.assertEqual(protocol.stage, "finish")
        self.assertEqual(validate_trace(events, samples), 24)
        validate_raw_delivery(events, copy.deepcopy(events), driver)
        validate_caller_policy(
            events, driver, manifest_sha="a" * 64, save_sha="b" * 64,
            evidence_sha="c" * 64, restore_tic=870)
        durations = validate_contract_replay(events)
        self.assertEqual(len(durations), 16)
        self.assertEqual(validate_owner_events(events, owner), 16)

        altered_raw = copy.deepcopy(events)
        altered_raw[0]["emit_ns"] += 1
        with self.assertRaisesRegex(ValueError, "raw event delivery differs"):
            validate_raw_delivery(events, altered_raw, driver)

if __name__ == "__main__":
    unittest.main()
