"""Regressions for source-bound HUD state feedback in V39 planner context."""
import hashlib
from itertools import product
import json
from types import SimpleNamespace
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import map01_overlap_controller_v39 as controller


WAD_SHA256 = "a" * 64
BINDING = {"focus": 11, "surface": 11, "geometry": [0, 0, 640, 480]}


def observation(sequence, capture_ns):
    return {"sequence": sequence, "capture_ns": capture_ns,
            "pointer_binding": BINDING,
            "frame_rgb_sha256": f"{sequence:064x}",
            "id": "program-1", "step": sequence}


def typed_observation(sequence, capture_ns, health, ammo, *, binding=BINDING):
    signals = {}
    for name, value in (("health", health), ("ammo", ammo)):
        signals[name] = {
            "format": "observable-signal-v1", "status": "observed",
            "signal_id": name, "value": value, "sequence": sequence,
            "capture_ns": capture_ns, "binding": binding,
            "wad_sha256": WAD_SHA256,
        }
    return {"event": "typed_observation", "schema": "doom-typed-observation-v1",
            "sequence": sequence, "capture_ns": capture_ns,
            "pointer_binding": binding,
            "frame_rgb_sha256": f"{sequence:064x}", "signals": signals,
            "id": "program-1", "step": sequence}


class FakePlanner:
    def __init__(self):
        self.calls = []

    def begin_turn(self, prompt, **params):
        self.calls.append((prompt, params))
        return "handle"


class V39TypedStateFeedbackTests(unittest.TestCase):
    def test_session_command_forwards_per_key_measurement_only_when_opted_in(self):
        args = SimpleNamespace(seed=7, load_fixture_manifest=HERE / "fixture.json",
                               per_key_input_measurement=True)

        command = controller.session_command(args, HERE / "runtime")

        self.assertEqual(command[-1], "--per-key-input-measurement")
        args.per_key_input_measurement = False
        self.assertNotIn("--per-key-input-measurement",
                         controller.session_command(args, HERE / "runtime"))

    def test_input_edge_receipt_projects_retained_a01_adapter_edges_separately(self):
        retained = (HERE / "map01_v39_perkey_bridge_a01" / "results" /
                    "construction-a01" / "candidate-events.jsonl")
        events = [json.loads(line) for line in retained.read_text().splitlines()]

        receipts = controller.input_edge_receipts(events)

        self.assertEqual(len(receipts), 1)
        receipt = receipts[0]
        self.assertEqual(receipt["status"], "adapter_edge_brackets_paired")
        self.assertEqual(receipt["step"], 2)
        self.assertEqual(receipt["key"], "F8")
        self.assertEqual(receipt["down_edge_interval_ns"],
                         [87811364890958, 87811364895916])
        self.assertEqual(receipt["up_edge_interval_ns"],
                         [87811364946333, 87811364949416])
        self.assertFalse(receipt["grants_input_authority"])
        self.assertFalse(receipt["application_consumption_observed"])
        self.assertIn("X-server", receipt["scope"])
        self.assertNotIn("intent-v39-a01", repr(receipts))

    def test_retained_v39_trace_with_unscoped_admissions_stays_unpaired(self):
        retained = (HERE / "results" / "map01-v39-coast-liveness-live-01" /
                    "runtime" / "events.jsonl")
        events = [json.loads(line) for line in retained.read_text().splitlines()]
        admissions = [row for row in events if row.get("event") == "input_admission"]

        receipts = controller.input_edge_receipts(events)

        self.assertEqual(len(admissions), 39)
        self.assertEqual(len(receipts), len(admissions))
        self.assertEqual({row["status"] for row in receipts}, {"identity_unavailable"})
        self.assertTrue(all(row.get("input_ack_to_owner_keyup_start_ms") is None
                            for row in receipts))

    def test_input_edge_receipt_rejects_adapter_actuation_identity_mismatch(self):
        retained = (HERE / "map01_v39_perkey_bridge_a01" / "results" /
                    "construction-a01" / "candidate-events.jsonl")
        events = [json.loads(line) for line in retained.read_text().splitlines()]
        events[1]["physical_key_measurement"]["adapter_edge"]["actuation_id"] = "other"

        receipt = controller.input_edge_receipts(events)[0]

        self.assertEqual(receipt["status"], "adapter_edge_receipt_incomplete")
        self.assertIsNone(receipt["down_edge_interval_ns"])
        self.assertIsNone(receipt["up_edge_interval_ns"])

    def test_input_edge_receipt_pairs_per_key_admission_and_server_keyup_without_secrets(self):
        token = "ephemeral-intent-token"
        events = [
            {"event": "input_admission", "id": "program-1", "step": 2,
             "key": "d", "intent_token": token, "admitted_ns": 1_000_000,
             "input_ack_ns": 1_100_000},
            {"event": "input_release_transition", "id": "program-1", "step": 2,
             "key": "d", "intent_token": token, "operation": "up",
             "release_call_started_ns": 2_500_000,
             "release_call_returned_ns": 2_800_000,
             "owner_thread_keyup_receipt": {
                 "event": "owner_explicit_keyup", "key": "d",
                 "intent_token": token,
                 "owner_keyrelease_started_ns": 2_600_000,
                 "owner_sync_returned_ns": 2_700_000,
                 "server_sync_completed": True,
                 "physical_verification_authoritative": False},
             "owner_thread_keyup_receipt_count": 1,
             "owner_thread_keyup_history_complete": True,
             "owner_thread_keyup_verified": True,
             "physical_verification_authoritative": False},
        ]

        receipts = controller.input_edge_receipts(events)

        self.assertEqual(len(receipts), 1)
        receipt = receipts[0]
        self.assertEqual(receipt["status"], "paired")
        self.assertEqual(receipt["key"], "d")
        self.assertEqual(receipt["step"], 2)
        self.assertEqual(receipt["admitted_ns"], 1_000_000)
        self.assertEqual(receipt["input_ack_ns"], 1_100_000)
        self.assertEqual(receipt["owner_keyrelease_started_ns"], 2_600_000)
        self.assertEqual(receipt["owner_sync_returned_ns"], 2_700_000)
        self.assertEqual(receipt["input_ack_to_owner_keyup_start_ms"], 1.5)
        self.assertTrue(receipt["server_sync_completed"])
        self.assertFalse(receipt["physical_verification_authoritative"])
        self.assertNotIn("ephemeral-intent-token", repr(receipts))
        self.assertNotIn("owner_thread_keyup_receipt", receipt)

    def test_input_edge_receipt_keeps_missing_release_unpaired(self):
        receipts = controller.input_edge_receipts([{
            "event": "input_admission", "id": "program-1", "step": 0,
            "key": "space", "intent_token": "token", "admitted_ns": 100,
            "input_ack_ns": 110,
        }])

        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["status"], "admission_without_release")
        self.assertIsNone(receipts[0]["owner_keyrelease_started_ns"])
        self.assertIsNone(receipts[0]["input_ack_to_owner_keyup_start_ms"])

    def test_input_edge_receipt_does_not_join_different_intent_tokens(self):
        events = [
            {"event": "input_admission", "id": "program-1", "step": 1,
             "key": "Up", "intent_token": "token-a", "admitted_ns": 100,
             "input_ack_ns": 110},
            {"event": "input_release_transition", "id": "program-1", "step": 1,
             "key": "Up", "intent_token": "token-b", "operation": "up",
             "owner_thread_keyup_receipt": {"event": "owner_explicit_keyup",
                 "key": "Up", "intent_token": "token-b",
                 "owner_keyrelease_started_ns": 200,
                 "owner_sync_returned_ns": 210,
                 "server_sync_completed": True}},
        ]

        receipts = controller.input_edge_receipts(events)

        self.assertEqual([row["status"] for row in receipts], [
            "admission_without_release", "release_without_admission"])

    def test_input_edge_receipt_does_not_derive_interval_outside_release_bracket(self):
        events = [
            {"event": "input_admission", "id": "program-1", "step": 0,
             "key": "Up", "intent_token": "token", "admitted_ns": 100,
             "input_ack_ns": 110},
            {"event": "input_release_transition", "id": "program-1", "step": 0,
             "key": "Up", "intent_token": "token", "operation": "up",
             "release_call_started_ns": 250, "release_call_returned_ns": 290,
             "owner_thread_keyup_receipt": {"event": "owner_explicit_keyup",
                 "key": "Up", "intent_token": "token",
                 "owner_keyrelease_started_ns": 240,
                 "owner_sync_returned_ns": 260,
                 "server_sync_completed": True},
        }
        ]

        receipt = controller.input_edge_receipts(events)[0]

        self.assertEqual(receipt["status"], "release_receipt_incomplete")
        self.assertIsNone(receipt["input_ack_to_owner_keyup_start_ms"])

    def test_input_edge_receipt_requires_all_sync_and_owner_history_confirmations(self):
        for server_sync, verified, history in product((None, False, True), repeat=3):
            events = [
                {"event": "input_admission", "id": "program-1", "step": 0,
                 "key": "d", "intent_token": "token", "admitted_ns": 100,
                 "input_ack_ns": 110},
                {"event": "input_release_transition", "id": "program-1", "step": 0,
                 "key": "d", "intent_token": "token", "operation": "up",
                 "release_call_started_ns": 190, "release_call_returned_ns": 240,
                 "owner_thread_keyup_receipt": {
                     "event": "owner_explicit_keyup", "key": "d",
                     "intent_token": "token", "owner_keyrelease_started_ns": 200,
                     "owner_sync_returned_ns": 220,
                     "server_sync_completed": server_sync},
                 "owner_thread_keyup_verified": verified,
                 "owner_thread_keyup_history_complete": history},
            ]
            row = events[1]
            owner = row["owner_thread_keyup_receipt"]
            if server_sync is None:
                owner.pop("server_sync_completed")
            if verified is None:
                row.pop("owner_thread_keyup_verified")
            if history is None:
                row.pop("owner_thread_keyup_history_complete")

            receipt = controller.input_edge_receipts(events)[0]
            with self.subTest(server_sync=server_sync, verified=verified, history=history):
                if (server_sync, verified, history) == (True, True, True):
                    self.assertEqual(receipt["status"], "paired")
                    self.assertEqual(receipt["input_ack_to_owner_keyup_start_ms"], 0.00009)
                else:
                    self.assertEqual(receipt["status"], "release_receipt_incomplete")
                    self.assertIsNone(receipt["admitted_to_owner_keyup_start_ms"])
                    self.assertIsNone(receipt["input_ack_to_owner_keyup_start_ms"])

    def test_feedback_reports_exact_health_and_ammo_deltas_for_matching_frames(self):
        before = observation(83, 100)
        after = observation(89, 200)
        typed = [typed_observation(83, 100, 97, 48),
                 typed_observation(89, 200, 91, 45)]

        result = controller.action_state_feedback(before, after, typed)

        self.assertEqual(result, {
            "status": "observed",
            "from_sequence": 83,
            "to_sequence": 89,
            "signals": {
                "health": {"before": 97, "after": 91, "delta": -6},
                "ammo": {"before": 48, "after": 45, "delta": -3},
            },
            "scope": "public HUD transition observed after action; not causal or beneficial evidence",
        })

    def test_unchanged_ammo_after_fire_is_reported_as_zero_resource_delta(self):
        result = controller.action_state_feedback(
            observation(83, 100), observation(89, 200),
            [typed_observation(83, 100, 91, 45),
             typed_observation(89, 200, 91, 45)])

        self.assertEqual(result["status"], "observed")
        self.assertEqual(result["signals"]["ammo"],
                         {"before": 45, "after": 45, "delta": 0})

    def test_feedback_refuses_typed_frame_with_mismatched_capture_time(self):
        before = observation(83, 100)
        after = observation(89, 200)
        typed = [typed_observation(83, 100, 91, 45),
                 typed_observation(89, 199, 91, 44)]

        result = controller.action_state_feedback(before, after, typed)

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "typed_frame_identity_mismatch")

    def test_feedback_refuses_typed_frame_with_mismatched_rgb_hash(self):
        before = observation(83, 100)
        after = observation(89, 200)
        mismatched = typed_observation(89, 200, 91, 44)
        mismatched["frame_rgb_sha256"] = "b" * 64

        result = controller.action_state_feedback(
            before, after, [typed_observation(83, 100, 91, 45), mismatched])

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "typed_frame_identity_mismatch")

    def test_feedback_refuses_typed_frame_from_another_program(self):
        before = observation(83, 100)
        after = observation(89, 200)
        wrong_program = typed_observation(89, 200, 91, 44)
        wrong_program["id"] = "other-program"

        result = controller.action_state_feedback(
            before, after, [typed_observation(83, 100, 91, 45), wrong_program])

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "typed_frame_identity_mismatch")

    def test_feedback_refuses_typed_event_schema_and_top_level_binding_mismatch(self):
        before, after = observation(83, 100), observation(89, 200)
        wrong_schema = typed_observation(89, 200, 91, 44)
        wrong_schema["schema"] = "unexpected-schema"
        wrong_binding = typed_observation(89, 200, 91, 44)
        wrong_binding["pointer_binding"] = {
            "focus": 99, "surface": 99, "geometry": [0, 0, 640, 480]}
        for bad in (wrong_schema, wrong_binding):
            with self.subTest(schema=bad["schema"], binding=bad["pointer_binding"]):
                result = controller.action_state_feedback(
                    before, after, [typed_observation(83, 100, 91, 45), bad])
                self.assertEqual(result["status"], "unavailable")
                self.assertEqual(result["reason"], "typed_frame_identity_mismatch")

    def test_feedback_refuses_out_of_domain_typed_hud_values(self):
        before = observation(83, 100)
        after = observation(89, 200)

        result = controller.action_state_feedback(
            before, after, [typed_observation(83, 100, 91, 45),
                            typed_observation(89, 200, 201, 45)])

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "typed_signal_unavailable")

    def test_feedback_refuses_wad_identity_change_between_frames(self):
        before = observation(83, 100)
        after = observation(89, 200)
        changed_wad = typed_observation(89, 200, 91, 44)
        changed_wad["signals"]["ammo"]["wad_sha256"] = "b" * 64

        result = controller.action_state_feedback(
            before, after, [typed_observation(83, 100, 91, 45), changed_wad])

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "typed_signal_binding_mismatch")

    def test_feedback_refuses_nonforward_capture_order(self):
        result = controller.action_state_feedback(
            observation(89, 200), observation(83, 100),
            [typed_observation(83, 100, 91, 45),
             typed_observation(89, 200, 91, 44)])

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "typed_frame_order_invalid")

    def test_planner_prompt_receives_prior_state_delta_as_observation_only(self):
        planner = FakePlanner()
        feedback = [{"action": "fire", "extent": "pulse",
                     "viewport_result": "visible_change",
                     "state_feedback": {"status": "observed", "signals": {
                         "health": {"before": 91, "after": 91, "delta": 0},
                         "ammo": {"before": 45, "after": 45, "delta": 0}}}}]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "sheet.png"
            image.write_bytes(b"fixture")
            with patch.object(controller, "win", return_value=r"C:\sheet.png"):
                controller.begin_model_turn(
                    planner, root, image, [], 91, 45, None,
                    {"type": "object"}, prior_state_feedback=feedback)

        prompt, _ = planner.calls[0]
        self.assertIn('"ammo":{"before":45,"after":45,"delta":0}', prompt)
        self.assertIn("not causal or beneficial evidence", prompt)

    def test_action_receipt_has_join_key_for_per_key_timing_and_state_capture(self):
        before = observation(83, 100)
        before.update({"image": "before.png", "step": 0})
        first = observation(89, 200)
        first.update({"image": "first.png", "step": 0, "capture_ms": 0.5})
        last = observation(90, 300)
        last.update({"image": "last.png", "step": 0, "capture_ms": 0.5})
        typed = [typed_observation(83, 100, 91, 45),
                 typed_observation(89, 200, 91, 44),
                 typed_observation(90, 300, 80, 42)]
        for row in typed:
            row["step"] = 0
        with patch.object(controller, "descriptor", side_effect=["before", "last"]), \
             patch.object(controller, "normalized_mae", return_value=0.1):
            receipts = controller.effect_receipts(
                [{"action": "fire", "extent": "pulse"}], before,
                [first, last], 100, typed_observations=typed)

        receipt = receipts[0]
        self.assertEqual(receipt["program_id_sha256"],
                         hashlib.sha256(b"program-1").hexdigest())
        self.assertEqual(receipt["executor_step"], 0)
        self.assertEqual(receipt["after_sequence"], 90)
        self.assertEqual(receipt["effect_observed_ns"], 300)
        self.assertEqual(receipt["feedback_sequence"], 89)
        self.assertEqual(receipt["feedback_capture_ns"], 200)
        self.assertEqual(receipt["plan_accept_to_first_capture_ms"], 0.0001)
        self.assertEqual(receipt["plan_accept_to_last_capture_ms"], 0.0002)
        self.assertEqual(receipt["state_feedback"]["to_sequence"], 89)
        self.assertEqual(receipt["state_feedback"]["signals"]["ammo"]["delta"], -1)


if __name__ == "__main__":
    unittest.main()
