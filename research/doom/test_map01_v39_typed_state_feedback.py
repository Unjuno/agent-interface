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
        self.assertEqual(receipt["input_admitted_ns"], 87811364887583)
        self.assertEqual(receipt["down_press_request_ns"], 87811364891916)
        self.assertEqual(receipt["down_sync_return_ns"], 87811364893458)
        self.assertEqual(receipt["up_release_request_ns"], 87811364946750)
        self.assertEqual(receipt["up_sync_return_ns"], 87811364948750)
        self.assertFalse(receipt["grants_input_authority"])
        self.assertFalse(receipt["application_consumption_observed"])
        self.assertIn("X-server", receipt["scope"])
        self.assertNotIn("intent-v39-a01", repr(receipts))

    def test_input_edge_receipt_pairs_retained_absolute_pair_release_trace(self):
        retained = (HERE / "absolute_pair_59_4d74_20261004" / "05-pulse" /
                    "runtime" / "events.jsonl")
        events = [json.loads(line) for line in retained.read_text().splitlines()]

        receipts = controller.input_edge_receipts(events)

        self.assertEqual(len(receipts), 2)
        self.assertTrue(all(row["status"] == "paired" for row in receipts))
        self.assertTrue(all(
            row["input_ack_ns"] <= row["release_call_started_ns"] <=
            row["owner_keyrelease_started_ns"] <= row["owner_sync_returned_ns"] <=
            row["release_call_returned_ns"] for row in receipts))
        self.assertTrue(all(not row["physical_verification_authoritative"]
                            for row in receipts))

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

    def test_adapter_edges_must_match_owner_generated_brackets(self):
        retained = (HERE / "map01_v39_perkey_bridge_a01" / "results" /
                    "construction-a01" / "candidate-events.jsonl")
        template = [json.loads(line) for line in retained.read_text().splitlines()]
        mutations = (
            (0, "physical_down_interval", [1, 2]),
            (0, "key", "other-key"),
            (0, "owner_id", "other-owner"),
            (0, "intent_token", "other-token"),
            (0, "status", "CONTRADICTORY"),
            (0, "grants_input_authority", True),
            (0, "application_consumption_observed", True),
            (1, "physical_up_interval", [1, 2]),
            (1, "key", "other-key"),
            (1, "owner_id", "other-owner"),
            (1, "intent_token", "other-token"),
            (1, "status", "CONTRADICTORY"),
            (1, "grants_input_authority", True),
            (1, "application_consumption_observed", True),
        )

        for row_index, field, value in mutations:
            events = json.loads(json.dumps(template))
            events[row_index]["physical_key_measurement"]["bracket"][field] = value

            with self.subTest(row_index=row_index, field=field):
                receipt = controller.input_edge_receipts(events)[0]

                self.assertEqual(receipt["status"],
                                 "adapter_edge_receipt_incomplete")
                self.assertIsNone(receipt["down_edge_interval_ns"])
                self.assertIsNone(receipt["up_edge_interval_ns"])

    def test_adapter_event_kind_must_match_nested_edge(self):
        retained = (HERE / "map01_v39_perkey_bridge_a01" / "results" /
                    "construction-a01" / "candidate-events.jsonl")
        template = [json.loads(line) for line in retained.read_text().splitlines()]

        for row_index, wrong_outer_event in (
                (0, "input_release_measurement"),
                (1, "input_admission")):
            events = json.loads(json.dumps(template))
            events[row_index]["event"] = wrong_outer_event

            with self.subTest(row_index=row_index,
                              wrong_outer_event=wrong_outer_event):
                receipts = controller.input_edge_receipts(events)

                self.assertEqual(len(receipts), 1)
                self.assertEqual(receipts[0]["status"],
                                 "adapter_edge_receipt_incomplete")
                self.assertIsNone(receipts[0]["down_edge_interval_ns"])
                self.assertIsNone(receipts[0]["up_edge_interval_ns"])

    def test_measurement_edge_discriminator_must_match_outer_and_nested_edge(self):
        retained = (HERE / "map01_v39_perkey_bridge_a01" / "results" /
                    "construction-a01" / "candidate-events.jsonl")
        template = [json.loads(line) for line in retained.read_text().splitlines()]

        for row_index, contradictory_edge in ((0, "up"), (1, "down")):
            events = json.loads(json.dumps(template))
            events[row_index]["physical_key_measurement"]["edge"] = contradictory_edge

            with self.subTest(row_index=row_index,
                              contradictory_edge=contradictory_edge):
                receipt = controller.input_edge_receipts(events)[0]

                self.assertEqual(receipt["status"],
                                 "adapter_edge_receipt_incomplete")
                self.assertIsNone(receipt["down_edge_interval_ns"])
                self.assertIsNone(receipt["up_edge_interval_ns"])

    def test_application_consumption_claim_must_not_contradict_adapter_projection(self):
        retained = (HERE / "map01_v39_perkey_bridge_a01" / "results" /
                    "construction-a01" / "candidate-events.jsonl")
        template = [json.loads(line) for line in retained.read_text().splitlines()]
        baseline = controller.input_edge_receipts(template)[0]
        self.assertEqual(baseline["status"], "adapter_edge_brackets_paired")

        layers = ("event", "measurement", "adapter_edge", "bracket",
                  "pre_sample", "post_sample")
        conflicting_values = (True, 1, 0, None, "false")
        for row_index in range(2):
            for layer in layers:
                for value in conflicting_values:
                    events = json.loads(json.dumps(template))
                    row = events[row_index]
                    if layer == "event":
                        row["application_consumption_observed"] = value
                    elif layer == "measurement":
                        row["physical_key_measurement"][
                            "application_consumption_observed"] = value
                    else:
                        row["physical_key_measurement"][layer][
                            "application_consumption_observed"] = value

                    with self.subTest(row_index=row_index, layer=layer, value=value):
                        receipt = controller.input_edge_receipts(events)[0]
                        self.assertEqual(receipt["status"],
                                         "adapter_edge_receipt_incomplete")
                        for field in ("input_admitted_ns", "down_press_request_ns",
                                      "down_sync_return_ns", "down_edge_interval_ns",
                                      "up_release_request_ns", "up_sync_return_ns",
                                      "up_edge_interval_ns"):
                            self.assertIsNone(receipt[field])

    def test_adapter_pair_requires_consistent_samples_and_request_timing(self):
        retained = (HERE / "map01_v39_perkey_bridge_a01" / "results" /
                    "construction-a01" / "candidate-events.jsonl")
        template = [json.loads(line) for line in retained.read_text().splitlines()]
        mutations = (
            (0, "pre_sample.available", False),
            (0, "pre_sample.down", True),
            (0, "post_sample.down", False),
            (0, "pre_sample.started_ns", 87811364890959),
            (0, "pre_sample.finished_ns", 87811364891917),
            (0, "press_request_ns", 87811364890957),
            (0, "sync_return_ns", 87811364893751),
            (0, "input_ack_ns", 87811364893459),
            (0, "input_ack_ns", True),
            (0, "admitted_ns", "unavailable"),
            (0, "admitted_ns", 87811364887959),
            (1, "pre_sample.available", False),
            (1, "pre_sample.down", False),
            (1, "post_sample.down", True),
            (1, "post_sample.finished_ns", 87811364949417),
            (1, "release_request_ns", 87811364946332),
            (1, "sync_return_ns", 87811364949001),
            (1, "release_attempted", False),
        )

        for row_index, field, value in mutations:
            events = json.loads(json.dumps(template))
            measurement = events[row_index]["physical_key_measurement"]
            if "." in field:
                name, nested = field.split(".", 1)
                measurement[name][nested] = value
            elif field in ("input_ack_ns", "admitted_ns"):
                events[row_index][field] = value
            else:
                measurement[field] = value

            with self.subTest(row_index=row_index, field=field):
                receipt = controller.input_edge_receipts(events)[0]

                self.assertEqual(receipt["status"],
                                 "adapter_edge_receipt_incomplete")
                for field in ("input_admitted_ns", "down_press_request_ns",
                              "down_sync_return_ns", "down_edge_interval_ns",
                              "up_release_request_ns", "up_sync_return_ns",
                              "up_edge_interval_ns"):
                    self.assertIsNone(receipt[field])

    def test_adapter_edge_pairs_reject_interval_conflicting_with_owner_bracket(self):
        retained = (HERE / "map01_v39_perkey_bridge_a01" / "results" /
                    "construction-a01" / "candidate-events.jsonl")
        template = [json.loads(line) for line in retained.read_text().splitlines()]
        for event_name in ("input_admission", "input_release_measurement"):
            events = json.loads(json.dumps(template))
            row = next(row for row in events if row.get("event") == event_name)
            row["physical_key_measurement"]["adapter_edge"]["interval"] = [1, 2]
            receipt = controller.input_edge_receipts(events)[0]
            with self.subTest(event=event_name):
                self.assertEqual(receipt["status"], "adapter_edge_receipt_incomplete")
                self.assertIsNone(receipt["down_edge_interval_ns"])
                self.assertIsNone(receipt["up_edge_interval_ns"])

    def test_adapter_edge_pairs_require_strictly_separated_down_and_up_intervals(self):
        retained = (HERE / "map01_v39_perkey_bridge_a01" / "results" /
                    "construction-a01" / "candidate-events.jsonl")
        template = [json.loads(line) for line in retained.read_text().splitlines()]
        endpoints = range(4)
        intervals = [(start, end) for start in endpoints for end in endpoints
                     if start <= end]
        paired = incomplete = 0

        def set_interval(row, edge_name, start, finish):
            measurement = row["physical_key_measurement"]
            measurement["adapter_edge"]["interval"] = [start, finish]
            interval_name = ("physical_down_interval" if edge_name == "down"
                             else "physical_up_interval")
            measurement["bracket"][interval_name] = [start, finish]
            measurement["pre_sample"].update(started_ns=start, finished_ns=start)
            measurement["post_sample"].update(started_ns=start, finished_ns=finish)
            request_name = "press_request_ns" if edge_name == "down" else "release_request_ns"
            measurement[request_name] = start
            measurement["sync_return_ns"] = start
            if edge_name == "down":
                row["admitted_ns"] = start
                row["input_ack_ns"] = start

        for down_start, down_end in intervals:
            for up_start, up_end in intervals:
                events = json.loads(json.dumps(template))
                down = next(row for row in events
                            if row.get("event") == "input_admission")
                up = next(row for row in events
                          if row.get("event") == "input_release_measurement")
                set_interval(down, "down", down_start, down_end)
                set_interval(up, "up", up_start, up_end)

                receipt = controller.input_edge_receipts(events)[0]
                strictly_ordered = down_end < up_start
                with self.subTest(down=(down_start, down_end),
                                  up=(up_start, up_end)):
                    if strictly_ordered:
                        paired += 1
                        self.assertEqual(receipt["status"],
                                         "adapter_edge_brackets_paired")
                        self.assertEqual(receipt["down_edge_interval_ns"],
                                         [down_start, down_end])
                        self.assertEqual(receipt["up_edge_interval_ns"],
                                         [up_start, up_end])
                    else:
                        incomplete += 1
                        self.assertEqual(receipt["status"],
                                         "adapter_edge_receipt_incomplete")
                        self.assertIsNone(receipt["down_edge_interval_ns"])
                        self.assertIsNone(receipt["up_edge_interval_ns"])

        self.assertEqual((paired, incomplete), (15, 85))
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

    def test_input_edge_receipt_allows_owner_lock_wait_after_release_wrapper_starts(self):
        events = [
            {"event": "input_admission", "id": "program-1", "step": 0,
             "key": "Up", "intent_token": "token", "admitted_ns": 100,
             "input_ack_ns": 110},
            {"event": "input_release_transition", "id": "program-1", "step": 0,
             "key": "Up", "intent_token": "token", "operation": "up",
             "release_call_started_ns": 150, "release_call_returned_ns": 220,
             "owner_thread_keyup_receipt": {"event": "owner_explicit_keyup",
                 "key": "Up", "intent_token": "token",
                 "owner_keyrelease_started_ns": 180,
                 "owner_sync_returned_ns": 200,
                 "server_sync_completed": True},
             "owner_thread_keyup_verified": True,
             "owner_thread_keyup_history_complete": True},
        ]

        receipt = controller.input_edge_receipts(events)[0]

        self.assertEqual(receipt["status"], "paired")
        self.assertEqual(receipt["input_ack_to_owner_keyup_start_ms"], 0.00007)

    def test_input_edge_receipt_rejects_release_wrapper_before_input_ack(self):
        events = [
            {"event": "input_admission", "id": "program-1", "step": 0,
             "key": "Up", "intent_token": "token", "admitted_ns": 100,
             "input_ack_ns": 110},
            {"event": "input_release_transition", "id": "program-1", "step": 0,
             "key": "Up", "intent_token": "token", "operation": "up",
             "release_call_started_ns": 105, "release_call_returned_ns": 220,
             "owner_thread_keyup_receipt": {"event": "owner_explicit_keyup",
                 "key": "Up", "intent_token": "token",
                 "owner_keyrelease_started_ns": 180,
                 "owner_sync_returned_ns": 200,
                 "server_sync_completed": True},
             "owner_thread_keyup_verified": True,
             "owner_thread_keyup_history_complete": True},
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

    def test_running_action_snapshot_rejects_noninteger_step_aliases(self):
        source_health = {"format": "observable-signal-v1",
                         "status": "observed", "signal_id": "health",
                         "value": 91, "sequence": 88, "capture_ns": 100,
                         "binding": BINDING}
        contract = controller.build_action_contract(
            [{"action": "move", "extent": "pulse"}],
            {"critical_health_minimum": 1, "maximum_health_loss": 5,
             "minimum_ammo": 0, "max_current_age_ms": 1000},
            source_health)
        event = {
            "event": "typed_observation",
            "schema": "doom-typed-observation-v1",
            "id": "cover-1",
            "step": 1,
            "sequence": 89,
            "capture_ns": 200,
            "pointer_binding": BINDING,
            "signals": {},
            "frame_rgb_sha256": "a" * 64,
            "frame_size": [640, 480],
            "typed_extraction_started_ns": 200,
            "typed_ready_ns": 200,
            "capture_to_typed_ready_ms": 0,
            "artifact_published": False,
            "grants_input_authority": False,
        }
        for name, value in (("health", 91), ("ammo", 45)):
            event["signals"][name] = {
                "signal_id": name, "sequence": 89, "capture_ns": 200,
                "binding": BINDING, "status": "observed", "value": value}

        for invalid_step in (True, 1.0, -1):
            with self.subTest(invalid_step=invalid_step):
                malformed = dict(event, step=invalid_step)

                with self.assertRaisesRegex(ValueError, "exact early typed"):
                    controller.build_typed_action_snapshot(malformed, contract)

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

    def test_feedback_rejects_noninteger_step_aliases_on_observation_and_typed_row(self):
        for mutation in ("observation", "typed_row", "both"):
            for invalid_step in (True, 1.0, -1):
                before = observation(83, 100)
                after = observation(89, 200)
                before["step"] = 0
                after["step"] = 1
                before_typed = typed_observation(83, 100, 91, 45)
                after_typed = typed_observation(89, 200, 90, 44)
                before_typed["step"] = 0
                after_typed["step"] = 1
                if mutation in ("observation", "both"):
                    after["step"] = invalid_step
                if mutation in ("typed_row", "both"):
                    after_typed["step"] = invalid_step

                with self.subTest(mutation=mutation,
                                  invalid_step=invalid_step):
                    result = controller.action_state_feedback(
                        before, after, [before_typed, after_typed])

                    self.assertEqual(result["status"], "unavailable")
                    self.assertEqual(result["reason"],
                                     "typed_frame_identity_mismatch")

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

    def test_feedback_baseline_advances_to_previous_action_last_sample(self):
        before = observation(0, 100)
        before.update({"image": "before.png", "step": -1})
        samples = []
        typed = [typed_observation(0, 100, 100, 50)]
        for sequence, step, capture_ns, health, ammo in (
                (1, 0, 200, 99, 49),
                (2, 0, 300, 70, 30),
                (3, 1, 400, 70, 30),
                (4, 1, 500, 70, 30)):
            row = observation(sequence, capture_ns)
            row.update({"image": f"sample-{sequence}.png", "step": step,
                        "capture_ms": 0.5})
            samples.append(row)
            typed.append(typed_observation(sequence, capture_ns, health, ammo))
            typed[-1]["step"] = step

        with patch.object(controller, "descriptor",
                          side_effect=["before", "step-0-last", "step-1-last"]), \
                patch.object(controller, "normalized_mae", return_value=0.1):
            receipts = controller.effect_receipts(
                [{"action": "move", "extent": "hold"},
                 {"action": "turn", "extent": "hold"}],
                before, samples, 100, typed_observations=typed)

        feedback = receipts[1]["state_feedback"]
        self.assertEqual(feedback["from_sequence"], 2)
        self.assertEqual(feedback["to_sequence"], 3)
        self.assertEqual(feedback["signals"]["health"]["delta"], 0)
        self.assertEqual(feedback["signals"]["ammo"]["delta"], 0)


if __name__ == "__main__":
    unittest.main()
