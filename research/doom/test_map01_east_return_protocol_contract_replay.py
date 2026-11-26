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
    def replay(self, stop_after=None):
        protocol = DoorDriverProtocol(
            "use", "a" * 64, "b" * 64, "c" * 64, 870,
            traverse=True, reverse_arm="east-return")
        contract = DoorTaskContract("use", traverse=True, reverse_arm="east-return")
        now = 1_100_000_000
        fixture = {
            "manifest_sha256": "a" * 64, "save_sha256": "b" * 64,
            "after_load_tic": 870,
            "setup_candidate_evidence": {"evidence_sha256": "c" * 64},
        }
        ready = {
            "event": "ready", "fixture": fixture,
            "post_load_clock_gate": {"passed": True},
            "reverse_door_program": reverse_manifest("east-return"),
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
        program.extend(reverse_stages("east-return"))
        self.assertEqual(len(program), 24)

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


if __name__ == "__main__":
    unittest.main()
