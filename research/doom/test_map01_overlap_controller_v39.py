"""Regression for the v38 rejected-action -> unauthored coast interrupt loop."""
import sys
import unittest
import queue
import tempfile
import ast
from argparse import Namespace
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import map01_overlap_controller_v39 as controller


class Map01V39CoastTests(unittest.TestCase):
    def test_retired_process_identity_terminal_carries_rotation_generation_into_recovery(self):
        import io
        import json
        import sys
        from types import ModuleType

        # Isolate the method under test from the backend's historical import
        # chain (which pulls optional desktop spreadsheet dependencies).
        stubs = {
            "doom_owner_thread_release_batch_backend_v1": {"Backend": type("Previous", (), {})},
            "input_transition_owner_v4": {"InputOwner": type("TransitionOwner", (), {})},
            "input_owner_v12": {"InputOwner": type("NativeOwner", (), {})},
            "target_process_identity_v1": {"IdentityReader": type("IdentityReader", (), {})},
            "executor_v3": {"DecisionRequired": type("DecisionRequired", (Exception,), {})},
            "verified_interruption_release_v1": {
                "qualified_interruption_release": lambda *_args, **_kwargs: False,
            },
        }
        previous_modules = {name: sys.modules.get(name) for name in stubs}
        for name, members in stubs.items():
            module = ModuleType(name)
            for key, value in members.items():
                setattr(module, key, value)
            sys.modules[name] = module
        try:
            from doom_process_identity_backend_v1 import Backend
        finally:
            for name, previous_module in previous_modules.items():
                if previous_module is None:
                    del sys.modules[name]
                else:
                    sys.modules[name] = previous_module

        emitted = []
        backend = Namespace(
            _external_emit=emitted.append,
            _provided_input_owner=None,
            capture_identity=object(),
            _owner_generation=4,
            owner=Namespace(owner_id="owner-generation-4"),
        )
        raw_terminal = {
            "event": "terminal", "id": "cover-after-focus-loss",
            "status": "cancelled", "terminal_ns": 500,
            "input_owner_generation": 99,
            "release": {
                "verified": True, "keys_down": [], "buttons_down": [],
                "keys_unknown": [], "key_state_errors": [],
                "target_process_identity_reader": {"retired": True},
            },
        }
        Backend._emit_identity(backend, raw_terminal)
        terminal = emitted[0]
        self.assertEqual(terminal["input_owner_generation"], 4)
        self.assertEqual(terminal["input_owner_id"], "owner-generation-4")
        receipt = {
            "event": "input_owner_generation",
            "terminal_id": terminal["id"],
            "generation": 5,
            "previous_generation": 4,
            "previous_owner_id": "owner-generation-4",
            "owner_id": "owner-generation-5",
            "source_invalidated": True,
            "grants_input_authority": False,
        }
        observation = {
            "event": "observation", "id": "owner-generation-source-5-1",
            "input_owner_generation": 5, "sequence": 8,
            "pointer_binding": {"surface": 17},
            "target_process_identity": {
                "sequence": 8, "surface": 17, "digest": "d" * 64,
            },
        }
        refreshed = {
            "event": "input_owner_source_refreshed",
            "terminal_id": terminal["id"], "generation": 5,
            "owner_id": "owner-generation-5", "attempt": 1,
            "observation_id": observation["id"], "sequence": 8,
            "surface": 17, "digest": "d" * 64,
            "source_invalidated": False, "grants_input_authority": False,
        }
        events = [receipt, observation, refreshed]

        def wait(predicate, timeout=40):
            return next(row for row in events if predicate(row))

        process = Namespace(stdin=io.StringIO())
        recovery = controller.rotate_retired_owner_after_cancel(
            process, wait, terminal, minimum_sequence=7)
        self.assertEqual(recovery["source_observation"], observation)
        self.assertEqual(recovery["source_refresh"], refreshed)
        commands = [json.loads(row) for row in process.stdin.getvalue().splitlines()]
        self.assertEqual(
            commands,
            [
                {"op": "rotate_input_owner", "id": terminal["id"]},
                {"op": "refresh_owner_source", "id": terminal["id"]},
            ],
        )

    def test_retired_owner_rotation_requires_verified_cancel_and_matches_generation(self):
        import io
        terminal = {"event": "terminal", "id": "plan-old", "status": "cancelled",
                    "input_owner_generation": 1,
                    "input_owner_id": "old-owner",
                    "release": {"verified": True, "keys_down": [], "buttons_down": [],
                                "keys_unknown": [], "key_state_errors": [],
                                "target_process_identity_reader": {"retired": True}}}
        process = Namespace(stdin=io.StringIO())
        receipt = {"event": "input_owner_generation", "terminal_id": "plan-old",
                   "generation": 2, "previous_generation": 1,
                   "previous_owner_id": "old-owner",
                   "owner_id": "fresh-owner", "source_invalidated": True,
                   "grants_input_authority": False}
        observation = {"event": "observation", "id": "owner-generation-source-2-1",
                       "input_owner_generation": 2, "sequence": 8,
                       "pointer_binding": {"surface": 17},
                       "target_process_identity": {"sequence": 8, "surface": 17,
                                                    "digest": "d" * 64}}
        refreshed = {"event": "input_owner_source_refreshed", "terminal_id": "plan-old",
                     "generation": 2, "owner_id": "fresh-owner",
                     "observation_id": observation["id"], "sequence": 8,
                     "attempt": 1,
                     "surface": 17, "digest": "d" * 64,
                     "source_invalidated": False, "grants_input_authority": False}
        events = [receipt, observation, refreshed]
        def wait(predicate, timeout=40):
            return next(row for row in events if predicate(row))
        result = controller.rotate_retired_owner_after_cancel(
            process, wait, terminal, minimum_sequence=7)
        self.assertEqual(result["event"], "input_owner_generation")
        self.assertEqual(result["source_observation"], observation)
        self.assertEqual(result["source_refresh"], refreshed)
        command = process.stdin.getvalue()
        self.assertIn('"op": "rotate_input_owner"', command)
        self.assertIn('"op": "refresh_owner_source"', command)
        self.assertIn('"id": "plan-old"', command)

    def test_post_rotation_source_refresh_stops_after_four_refusals(self):
        import json
        terminal = {"event": "terminal", "id": "plan-old", "status": "cancelled",
                    "input_owner_generation": 1, "input_owner_id": "old-owner",
                    "release": {"verified": True, "keys_down": [], "buttons_down": [],
                                "keys_unknown": [], "key_state_errors": [],
                                "target_process_identity_reader": {"retired": True}}}
        events = [{"event": "input_owner_generation", "terminal_id": "plan-old",
                   "generation": 2, "previous_generation": 1,
                   "previous_owner_id": "old-owner", "owner_id": "fresh-owner",
                   "source_invalidated": True, "grants_input_authority": False}]
        class Stdin:
            def __init__(self): self.commands = []
            def write(self, payload):
                command = json.loads(payload)
                self.commands.append(command)
                if command["op"] == "refresh_owner_source":
                    events.append({"event": "rejected", "id": "plan-old",
                                   "terminal_id": "plan-old",
                                   "operation": "refresh_owner_source",
                                   "attempt": len(self.commands) - 1,
                                   "reason": "synthetic capture refusal"})
            def flush(self): pass
        stdin = Stdin()
        def wait(predicate, timeout=40):
            return next(row for row in reversed(events) if predicate(row))
        with self.assertRaisesRegex(RuntimeError, "bounded post-rotation source refresh failed"):
            controller.rotate_retired_owner_after_cancel(
                Namespace(stdin=stdin), wait, terminal, minimum_sequence=7)
        refreshes = [row for row in stdin.commands if row["op"] == "refresh_owner_source"]
        self.assertEqual(len(refreshes), 4)
        self.assertEqual(len(stdin.commands), 5)

    def test_owner_rotation_refuses_unverified_or_wrong_generation_receipts(self):
        import io
        base = {"event": "terminal", "id": "plan-old", "status": "cancelled",
                "input_owner_generation": 1,
                "input_owner_id": "old-owner",
                "release": {"verified": True, "keys_down": [], "buttons_down": [],
                            "keys_unknown": [], "key_state_errors": [],
                            "target_process_identity_reader": {"retired": True}}}
        for mutate in (
                lambda row: row.update(status="completed"),
                lambda row: row["release"].update(keys_down=["space"]),
                lambda row: row["release"].pop("target_process_identity_reader"),
        ):
            terminal = {**base, "release": dict(base["release"])}
            mutate(terminal)
            with self.subTest(terminal=terminal), self.assertRaises(ValueError):
                controller.rotate_retired_owner_after_cancel(
                    Namespace(stdin=io.StringIO()), lambda _predicate: None, terminal,
                    minimum_sequence=7)

        terminal = dict(base)
        process = Namespace(stdin=io.StringIO())
        wrong_generation = {"event": "input_owner_generation", "terminal_id": "plan-old",
                            "generation": 3, "previous_generation": 2,
                            "previous_owner_id": "other-owner",
                            "owner_id": "fresh-owner", "source_invalidated": True,
                            "grants_input_authority": False}
        with self.assertRaisesRegex(RuntimeError, "refused or malformed"):
            controller.rotate_retired_owner_after_cancel(
                process, lambda predicate: wrong_generation if predicate(wrong_generation) else None,
                terminal, minimum_sequence=7)

    def test_post_rotation_observation_must_advance_sequence(self):
        import io
        terminal = {"event": "terminal", "id": "plan-old", "status": "cancelled",
                    "input_owner_generation": 1, "input_owner_id": "old-owner",
                    "release": {"verified": True, "keys_down": [], "buttons_down": [],
                                "keys_unknown": [], "key_state_errors": [],
                                "target_process_identity_reader": {"retired": True}}}
        receipt = {"event": "input_owner_generation", "terminal_id": "plan-old",
                   "generation": 2, "previous_generation": 1,
                   "previous_owner_id": "old-owner", "owner_id": "fresh-owner",
                   "source_invalidated": True, "grants_input_authority": False}
        stale = {"event": "observation", "id": "owner-generation-source-2-1",
                 "input_owner_generation": 2, "sequence": 10,
                 "pointer_binding": {"surface": 17},
                 "target_process_identity": {"sequence": 10, "surface": 17,
                                              "digest": "d" * 64}}
        def wait(predicate, timeout=40):
            return next(row for row in (receipt, stale) if predicate(row))
        with self.assertRaisesRegex(RuntimeError, "fresh post-rotation"):
            controller.rotate_retired_owner_after_cancel(
                Namespace(stdin=io.StringIO()), wait, terminal, minimum_sequence=10)

    def test_pending_observation_hard_crossing_cancels_old_cover_after_model_wait(self):
        from observable_signal_guard_v2 import (
            ObservableSignalGuard, ObservableSignalPolicyMonitor)

        binding = {"surface": 7, "geometry": [0, 0, 640, 480]}
        wad = "b" * 64

        def health_signal(value, sequence, capture_ns):
            return {"format": "observable-signal-v1", "status": "observed",
                    "signal_id": "health", "value": value, "sequence": sequence,
                    "capture_ns": capture_ns, "binding": binding, "wad_sha256": wad}

        source = health_signal(73, 1, 1_000)
        spec = {"op": "observable_signal_guard", "guard_id": "cover-health",
                "source_sequence": 1, "signal_id": "health", "source_value": 73,
                "hard_minimum": 67, "max_source_age_ms": 30_000,
                "on_soft_change": "preserve_existing_policy",
                "on_hard_change": "needs_decision", "on_unknown": "needs_decision"}
        monitor = ObservableSignalPolicyMonitor(
            ObservableSignalGuard(spec, source, binding),
            type("UnusedExtractor", (), {"read": lambda self, row: None})())

        def observation(value, sequence, capture_ns):
            health = health_signal(value, sequence, capture_ns)
            ammo = dict(health, signal_id="ammo", value=40)
            return {"event": "typed_observation", "schema": "doom-typed-observation-v1",
                    "sequence": sequence, "capture_ns": capture_ns,
                    "pointer_binding": binding, "frame_size": [640, 480],
                    "frame_rgb_sha256": "a" * 64,
                    "typed_extraction_started_ns": capture_ns + 1,
                    "typed_ready_ns": capture_ns + 2,
                    "signals": {"health": health, "ammo": ammo},
                    "artifact_published": False, "grants_input_authority": False}

        incoming = queue.Queue()
        incoming.put(observation(70, 2, 2_000))  # soft loss preserves this policy
        incoming.put(observation(65, 3, 3_000))  # authored hard floor is crossed
        drained = controller.drain_pending_observation_events(
            incoming, monitor, "cover-7")
        self.assertEqual(monitor.soft_event_count, 1)
        self.assertEqual(drained["invalidation"]["outcome"]["status"],
                         "HARD_INVALIDATED")
        self.assertEqual(drained["invalidation"]["sequence"], 3)

        class Stdin:
            def __init__(self): self.writes = []
            def write(self, value): self.writes.append(value)
            def flush(self): pass
        class Process:
            def __init__(self): self.stdin = Stdin()
        class Planner:
            def __init__(self): self.interrupted = []
            def invalidate_turn(self, handle): return {"outcome": "locally_invalidated"}
            def abort_pending_turn(self): pass
            def interrupt(self, handle):
                self.interrupted.append(handle)
                return {"status": "interrupted"}

        terminal = {"event": "terminal", "id": "cover-7", "status": "cancelled",
                    "release": {"event": "owner_release", "verified": True,
                                "keys_down": [], "buttons_down": [],
                                "keys_unknown": [], "key_state_errors": []}}
        process, planner, pending_turn = Process(), Planner(), object()
        interruption, closed = controller.cancel_invalidated_cover(
            planner, pending_turn, process,
            lambda predicate: terminal if predicate(terminal) else None,
            "cover-7")
        self.assertIn('"op": "cancel"', process.stdin.writes[0])
        self.assertEqual(planner.interrupted, [pending_turn])
        self.assertEqual(interruption["status"], "interrupted")
        self.assertIs(closed, terminal)
        self.assertEqual(closed["release"]["keys_down"], [])

    def test_stale_executor_rejection_replans_from_new_image_and_hud(self):
        from test_running_action_guard_v2 import (ready as ready_admission,
            action as guarded_action, compiler)
        from running_action_guard_v3 import RunningActionGuardV3

        binding = {"focus": 1, "surface": 7, "geometry": [0, 0, 640, 480]}
        old = {"event": "observation", "sequence": 3, "capture_ns": 100,
               "pointer_binding": binding,
               "image": "old.png", "frame_rgb_sha256": "a" * 64}
        fresh = {"event": "observation", "sequence": 4, "capture_ns": 400,
                 "pointer_binding": binding,
                 "image": "fresh.png", "frame_rgb_sha256": "b" * 64}
        for obs, health, ammo in ((old, 88, 12), (fresh, 61, 9)):
            obs["signals"] = {
                "health": {"status": "observed", "signal_id": "health",
                           "value": health, "sequence": obs["sequence"],
                           "capture_ns": obs["capture_ns"], "binding": binding},
                "ammo": {"status": "observed", "signal_id": "ammo",
                         "value": ammo, "sequence": obs["sequence"],
                         "capture_ns": obs["capture_ns"], "binding": binding}}

        admission = ready_admission()
        from action_validity_admission_v1 import (
            action_fingerprint, evaluate_action_validity)
        action = guarded_action()
        contract = admission["action_validity"]["contract"]
        contract["action_fingerprint"] = action_fingerprint(action["commands"])
        contract["source"]["sequence"] = 3
        contract["source"]["capture_ns"] = 100
        contract["source"]["binding"] = binding
        contract["source"]["signals"]["health"]["value"] = 88
        contract["predicates"][0]["value"] = 40
        snapshot = admission["action_validity"]["snapshot"]
        snapshot.update({"sequence": 4, "capture_ns": 200, "binding": binding})
        snapshot["signals"]["health"]["value"] = 88
        validity = evaluate_action_validity(action["commands"], contract,
            snapshot, 201)
        admission["controller_decided_ns"] = 201
        admission["action_validity"] = validity
        guard = RunningActionGuardV3(
            action, admission, compiler, "test-compiler-v1")
        incoming = queue.Queue()
        recovery_signals = {key: dict(value, sequence=5, capture_ns=500)
                            for key, value in fresh["signals"].items()}
        recovery_signals["ammo"].update(status="unknown", value=None)
        incoming.put({"event": "observation", "sequence": 5,
                      "capture_ns": 500, "pointer_binding": binding,
                      "image": "fresh.png", "frame_rgb_sha256": "b" * 64,
                      "signals": recovery_signals})
        incoming.put({"event": "typed_observation", "sequence": 5,
                      "capture_ns": 500, "pointer_binding": binding,
                      "image": "fresh.png", "frame_rgb_sha256": "b" * 64,
                      "signals": recovery_signals})
        recovered = controller.recover_stale_executor_rejection(
            {"event": "rejected", "reason":
             "latest observation sequence required before input"},
            identifier="plan-0-primary-0-0", expected_sequence=4,
            controller_received_ns=220, latest=dict(old, sequence=4), incoming=incoming,
            wait=lambda predicate, **kwargs: self.fail(
                "queued full observation should satisfy recovery"),
            final_action_admission=admission, running_guard=guard)

        self.assertEqual(recovered["latest"]["sequence"], 5)
        self.assertEqual(recovered["latest"]["signals"]["health"]["value"], 61)
        self.assertEqual(recovered["guard"]["state"], controller.RUNNING_REJECTED)
        self.assertFalse(recovered["guard"]["current_input_authority"])
        self.assertEqual(recovered["admission"]["status"], "REJECTED_EXECUTOR_STALE_SEQUENCE")

        with tempfile.TemporaryDirectory() as directory:
            from unittest.mock import patch
            from PIL import Image
            root = Path(directory)
            for name, color in (("old.png", (1, 2, 3)), ("fresh.png", (4, 5, 6)),
                                ("refreshed.png", (7, 8, 9))):
                Image.new("RGB", (2, 2), color).save(root / name)
            model_root = root / "decision-1"
            model_root.mkdir()
            recovered_source = dict(recovered["latest"])
            refresh_source = dict(recovered_source, sequence=6, capture_ns=600,
                image="refreshed.png", frame_rgb_sha256="c" * 64)
            refresh_source["signals"] = {
                key: dict(value, status="observed", sequence=6, capture_ns=600,
                          value=(60 if key == "health" else 8))
                for key, value in recovered_source["signals"].items()}
            sent = []
            replies = [
                {"event": "accepted", "id": "refresh-0", "intent_token": "refresh-lease"},
                 dict(refresh_source, event="observation", id="refresh-0"),
                 {"event": "terminal", "id": "refresh-0", "status": "completed",
                 "release": {"event": "owner_release", "verified": True,
                             "keys_down": [], "buttons_down": [],
                             "keys_unknown": [], "key_state_errors": [],
                             "intent_token": "refresh-lease"}},
            ]
            def refresh_wait(predicate, **kwargs):
                row = replies.pop(0)
                self.assertTrue(predicate(row))
                return row
            source, refresh_receipt = controller.refresh_source(
                recovered_source,
                type("HealthReader", (), {"read": lambda self, row: row["signals"]["health"]})(),
                type("AmmoReader", (), {"read": lambda self, row: row["signals"]["ammo"]})(),
                sent.append, refresh_wait, "refresh", clock=lambda: 1.0,
                lease_clock=lambda: 1_000_000_000)
            self.assertEqual(refresh_receipt["status"], "recovered")
            self.assertEqual(sent[0]["expected_sequence"], 5)
            self.assertEqual(source["sequence"], 6)
            health = source["signals"]["health"]["value"]
            ammo = source["signals"]["ammo"]["value"]
            planner = type("Planner", (), {"begin_turn": lambda self, prompt_text,
                output_schema, image_path: (prompt_text, image_path)})()
            with patch.object(controller, "win", side_effect=lambda path: str(path)):
                turn = controller.begin_model_turn(
                    planner, model_root, root / source["image"], [], health, ammo, {}, {})
            self.assertEqual(Path(turn[1]), root / "refreshed.png")
            self.assertIn("health: 60", turn[0])
            self.assertIn("ammo: 8", turn[0])

            from doom_source_refresh_v1 import SourceRefreshRefused
            bad_replies = [
                {"event": "accepted", "id": "bad-refresh-0", "intent_token": "lease-a"},
                dict(refresh_source, event="observation", id="bad-refresh-0"),
                {"event": "terminal", "id": "bad-refresh-0", "status": "completed",
                 "release": {"event": "owner_release", "verified": True,
                             "keys_down": [], "buttons_down": [],
                             "intent_token": "different-lease"}},
            ]
            def bad_refresh_wait(predicate, **kwargs):
                row = bad_replies.pop(0)
                self.assertTrue(predicate(row))
                return row
            with self.assertRaises(SourceRefreshRefused) as refused:
                controller.refresh_source(
                    recovered_source,
                    type("HealthReader", (), {"read": lambda self, row: row["signals"]["health"]})(),
                    type("AmmoReader", (), {"read": lambda self, row: row["signals"]["ammo"]})(),
                    lambda command: None, bad_refresh_wait, "bad-refresh",
                    clock=lambda: 1.0, lease_clock=lambda: 1_000_000_000)
            self.assertEqual(refused.exception.receipt["reason"], "refresh_release_unqualified")

        source = Path(controller.__file__).read_text(encoding="utf-8")
        rejected = source.index('if accepted["event"]!="accepted":')
        recovery = source.index("recover_stale_executor_rejection(", rejected)
        assign_latest = source.index('latest = recovered["latest"]', recovery)
        outer_continue = source.index('if stale_rejection is not None:', assign_latest)
        tree = ast.parse(source)
        main = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "main")
        loops = [node for node in ast.walk(main)
                 if isinstance(node, ast.For) and
                 any(isinstance(child, ast.Call) and
                     isinstance(child.func, ast.Name) and child.func.id == "begin_model_turn"
                     for child in ast.walk(node))]
        self.assertEqual(len(loops), 1)
        outer_loop = loops[0]
        loop_body = ast.get_source_segment(source, outer_loop)
        next_source = loop_body.index("action_source_observation=dict(latest)")
        next_begin = loop_body.index("planner_handle=begin_model_turn(", next_source)
        loop_start = source.index("for index in range(args.iterations):")
        recovery_branch = source[source.index('if stale_rejection is not None:', assign_latest):]
        continue_at = recovery_branch.index("continue")
        self.assertLess(rejected, recovery)
        self.assertLess(recovery, assign_latest)
        self.assertLess(loop_start, source.index("action_source_observation=dict(latest)"))
        self.assertLess(next_source, next_begin)
        self.assertLess(next_source, next_begin)

    def test_session_command_keeps_v12_default_and_selects_v15_only_when_opted_in(self):
        args = Namespace(seed=990605, load_fixture_manifest=Path("fixture.json"))
        default = controller.session_command(args, Path("runtime"))
        self.assertEqual(Path(default[1]).name, "session_map01_v12.py")
        self.assertIn("--out", default)
        self.assertIn("--load-fixture-manifest", default)

        args.measurement_session = True
        measured = controller.session_command(args, Path("runtime"))
        self.assertEqual(Path(measured[1]).name, "session_map01_v15.py")
        self.assertEqual(measured[2:], default[2:])

    def test_rejected_action_followup_keeps_model_turn_alive_on_damage(self):
        previous = {"iteration": 1, "model_action_discarded": True,
                    "action": {"state": "active", "next_cover": [
                        {"action": "strafe_left", "extent": "short"}],
                        "next_cover_validity": [{"signal_id": "health",
                            "critical_health_minimum": 35,
                            "maximum_health_loss": 12,
                            "max_source_age_ms": 30000}]}}
        commands, validity, source = controller.reusable_cover([previous])
        self.assertEqual((commands, validity, source), ([], None, None))
        default_receipt = {"authored": None, "effective": {
            "hard_minimum": 85, "maximum_health_loss": 0}}
        selected, receipt = controller.select_cover_monitor(
            object(), default_receipt, commands, source)
        self.assertIsInstance(selected, controller.UnauthoredCoastMonitor)
        self.assertEqual(receipt["monitor_mode"], "unauthored_coast_no_policy")
        self.assertEqual(selected.event_types, frozenset())
        self.assertEqual(selected.soft_event_count, 0)
        self.assertIsNone(selected.latest_soft_event)
        # The exact frame still updates latest in the caller, while the
        # unauthored coast publishes no policy event that can interrupt.
        self.assertEqual(default_receipt["effective"]["hard_minimum"], 85)

    def test_stale_partial_action_does_not_reuse_discarded_remaining_cover(self):
        previous = {"iteration": 1, "model_action_discarded": False,
                    "remaining_action_discarded": True,
                    "executor_preacceptance_rejection": {
                        "reason": "latest observation sequence required before input"},
                    "action": {"state": "active", "next_cover": [
                        {"action": "fire", "extent": "short"}],
                        "next_cover_validity": [{"signal_id": "health",
                            "critical_health_minimum": 35,
                            "maximum_health_loss": 12,
                            "max_source_age_ms": 30000}]}}

        self.assertEqual(controller.reusable_cover([previous]), ([], None, None))

    def test_completed_and_legacy_actions_preserve_authored_cover_reuse(self):
        cover = [{"action": "strafe_left", "extent": "short"}]
        validity = [{"signal_id": "health", "critical_health_minimum": 35,
                     "maximum_health_loss": 12, "max_source_age_ms": 30000}]
        for decision in (
            {"iteration": 2, "model_action_discarded": False,
             "remaining_action_discarded": False,
             "action": {"state": "active", "next_cover": cover,
                        "next_cover_validity": validity}},
            {"iteration": 3, "model_action_discarded": False,
             "action": {"state": "active", "next_cover": cover,
                        "next_cover_validity": validity}},
        ):
            with self.subTest(iteration=decision["iteration"]):
                self.assertEqual(controller.reusable_cover([decision]),
                                 (cover, validity[0], decision["iteration"]))

    def test_authored_cover_still_uses_original_guard(self):
        guard = object()
        authored = {"signal_id": "health", "critical_health_minimum": 35,
                    "maximum_health_loss": 12, "max_source_age_ms": 30000}
        selected, receipt = controller.select_cover_monitor(
            guard, {"authored": authored},
            [{"action": "strafe_left", "extent": "short"}], 0)
        self.assertIs(selected, guard)
        self.assertEqual(receipt["monitor_mode"], "authored_policy_guard")
        self.assertEqual(receipt["authored"], authored)

    def test_running_invalidation_interrupts_planner_and_requires_verified_empty_release(self):
        class Stdin:
            def __init__(self): self.writes = []
            def write(self, value): self.writes.append(value)
            def flush(self): pass
        class Process:
            def __init__(self): self.stdin = Stdin()
        class Planner:
            def invalidate_turn(self, handle):
                return {"outcome": "locally_invalidated"}
            def __init__(self): self.interrupted = []
            def interrupt(self, handle, before_transport=None):
                if before_transport is not None: before_transport()
                self.interrupted.append(handle)
                return {"status": "interrupted"}
        terminal = {"event": "terminal", "id": "cover-0", "status": "cancelled",
                    "release": {"event": "owner_release", "verified": True, "keys_down": [],
                                "buttons_down": [], "keys_unknown": [],
                                "key_state_errors": []}}
        process, planner, handle = Process(), Planner(), object()

        interruption, result = controller.cancel_invalidated_cover(
            planner, handle, process, lambda predicate: terminal, "cover-0")

        self.assertIs(result, terminal)
        self.assertEqual(planner.interrupted, [handle])
        self.assertEqual(interruption, {"status": "interrupted"})
        self.assertIn('"op": "cancel"', process.stdin.writes[0])

    def test_initial_cover_invalidation_cancels_before_planner_and_requires_empty_release(self):
        class Stdin:
            def __init__(self): self.writes = []
            def write(self, value): self.writes.append(value)
            def flush(self): pass
        class Process:
            def __init__(self): self.stdin = Stdin()

        terminal = {"event": "terminal", "id": "cover-0",
                    "status": "cancelled",
                    "release": {"event": "owner_release", "verified": True, "keys_down": [],
                                "buttons_down": [], "keys_unknown": [],
                                "key_state_errors": []}}
        process = Process()
        result = controller.cancel_initial_cover_before_planner(
            process, lambda predicate: terminal if predicate(terminal) else None,
            "cover-0")

        self.assertIs(result, terminal)
        self.assertIn('"op": "cancel"', process.stdin.writes[0])
        for release in (
            {"verified": False, "keys_down": [], "buttons_down": [],
             "keys_unknown": [], "key_state_errors": []},
            {"verified": True, "keys_down": ["W"], "buttons_down": []},
            {"event": "owner_release", "verified": True,
             "keys_down": [], "buttons_down": ["fire"]},
        ):
            unsafe_terminal = dict(terminal, release=release)
            with self.subTest(release=release), self.assertRaisesRegex(
                    RuntimeError, "allowed status and verified empty release"):
                controller.cancel_initial_cover_before_planner(
                    Process(),
                    lambda predicate: unsafe_terminal if predicate(unsafe_terminal) else None,
                    "cover-0")

    def test_cover_invalidation_receipt_distinguishes_preacceptance_from_cancel(self):
        invalidation = {"event": "paired_signal_invalidation",
                        "reason": "health:below_hard_minimum",
                        "sequence": 12}
        coherent = {"required_after_sequence": 11, "fresh_sequence": 13,
                    "additional_invalidations": []}
        rejected = {"ack": {"event": "rejected", "id": "cover-0"},
                    "submitted_sequence": 11, "invalidation": invalidation,
                    "coherent_source_recovery": coherent}
        accepted = {"ack": {"event": "accepted", "id": "cover-0"},
                    "submitted_sequence": 11, "invalidation": invalidation,
                    "coherent_source_recovery": coherent}
        terminal = {"event": "terminal", "id": "cover-0",
                    "status": "cancelled",
                    "release": {"event": "owner_release", "verified": True, "keys_down": [],
                                "buttons_down": [], "keys_unknown": [],
                                "key_state_errors": []}}

        before_admission = controller.cover_submission_invalidation_receipt(rejected)
        after_admission = controller.cover_submission_invalidation_receipt(
            accepted, terminal)

        self.assertIsNone(before_admission["cover_cancel_terminal"])
        self.assertEqual(before_admission["ack"]["event"], "rejected")
        self.assertEqual(before_admission["coherent_source_recovery"], coherent)
        self.assertIs(after_admission["cover_cancel_terminal"], terminal)
        self.assertEqual(after_admission["ack"]["event"], "accepted")

    def test_stale_initial_cover_caller_recovers_fresh_planner_source_without_cancel(self):
        source = {"event": "observation", "sequence": 11,
                  "image": "old.png"}
        fresh = {"event": "observation", "sequence": 12,
                 "image": "fresh.png"}
        incoming = queue.Queue()
        incoming.put(fresh)
        monitor = controller.UnauthoredCoastMonitor()
        calls = []

        result = controller.submit_initial_cover_with_recovery(
            lambda consumed: {"event": "rejected", "id": "cover-0",
                              "reason": "latest observation sequence required before input"},
            identifier="cover-0", latest_reader=lambda: source,
            incoming=incoming,
            wait=lambda predicate, **kwargs: self.fail(
                "queued fresh observation should satisfy recovery"),
            observation_monitor=monitor)
        reset = controller.reset_cover_after_preacceptance_rejection(
            result,
            build_monitor=lambda latest: (calls.append(("build", latest)) or
                                          (object(), {"authored": None})),
            select_monitor=lambda guard, admission, commands, iteration: (
                calls.append(("select", admission, commands, iteration)) or
                controller.select_cover_monitor(guard, admission, commands,
                                                iteration)))

        self.assertEqual(result["ack"]["event"], "rejected")
        self.assertEqual(reset["latest"], fresh)
        self.assertIsInstance(reset["monitor"], controller.UnauthoredCoastMonitor)
        self.assertEqual(reset["admission"]["monitor_mode"],
                         "unauthored_coast_no_policy")
        self.assertIsNone(reset["receipt"])
        self.assertEqual(calls[0], ("build", fresh))
        self.assertEqual(calls[1][2:], ([], None))

    def test_production_source_refresh_stops_loop_on_terminal_health_zero(self):
        source_path = Path(__file__).resolve().parent / "map01_overlap_controller_v39.py"
        source = source_path.read_text(encoding="utf-8")
        execute = source.index("def main(")
        refresh = source.index("latest, source_refresh = refresh_source(", execute)
        terminal_predicate = source.index("terminal_predicate=lambda row, health, ammo:", refresh)
        terminal_break = source.index('if source_refresh.get("status") == "terminal":', terminal_predicate)
        loop_break = source.index("break", terminal_break)
        next_input_path = source.index('failure_cleanup.set_stage("cover_validity_admission")', loop_break)
        finish_path = source.index('failure_cleanup.set_stage("session_finish")', next_input_path)
        report_path = source.index('failure_cleanup.set_stage("report_write")', finish_path)
        model_session_filter = source.index(
            'row["model_session_id"] for row in decisions if "model_session_id" in row',
            finish_path, report_path)
        model_wall_sum = source.index('x.get("model_ns", 0)', finish_path, report_path)
        self.assertLess(refresh, terminal_predicate)
        self.assertLess(terminal_predicate, terminal_break)
        self.assertLess(terminal_break, loop_break)
        self.assertLess(loop_break, next_input_path)
        self.assertLess(next_input_path, finish_path)
        self.assertLess(finish_path, report_path)
        self.assertLess(model_session_filter, report_path)
        self.assertLess(model_wall_sum, report_path)

    def test_terminal_health_observation_is_reported_outside_planner_decisions(self):
        source_path = Path(__file__).resolve().parent / "map01_overlap_controller_v39.py"
        source = source_path.read_text(encoding="utf-8")
        execute = source.index("def main(")
        loop = source.index("for index in range(args.iterations):", execute)
        terminal_branch = source.index('if source_refresh.get("status") == "terminal":', loop)
        terminal_break = source.index("break", terminal_branch)
        next_input_path = source.index('failure_cleanup.set_stage("cover_validity_admission")', terminal_break)
        report_path = source.index('"terminal_health_observation":terminal_health_observation', next_input_path)
        branch = source[terminal_branch:terminal_break]
        self.assertIn("terminal_health_observation =", branch)
        self.assertNotIn("decisions.append", branch)
        self.assertLess(terminal_branch, terminal_break)
        self.assertLess(terminal_break, next_input_path)
        self.assertLess(next_input_path, report_path)
        self.assertIn('"planner_turns":len(decisions)', source[report_path - 5000:report_path])
        self.assertIn('x["final_action_admission"]["status"] for x in decisions', source[report_path - 3000:report_path])

    def test_invalidated_planner_answer_is_discarded_before_motor_admission(self):
        source = Path(controller.__file__).read_text(encoding="utf-8")
        execute = source.index("def main(")
        loop = source.index("for index in range(args.iterations):", execute)
        planner_source = source.index("action_source_observation=dict(latest)", loop)
        invalidation = source.index("if invalidation is not None:", planner_source)
        recover = source.index("recover_pending_observation_backlog(", invalidation)
        fresh_source = source.index('latest = recovery["latest"]', recover)
        discard = source.index('"model_action_discarded":True', fresh_source)
        discard_reason = source.index(
            '"discard_reason":"policy_dependency_invalidated"', discard)
        continue_to_replan = source.index("continue", discard)
        answer_gate = source.index("if not planner_result.answer_eligible:", continue_to_replan)
        action_validation = source.index("validate_action(action)", continue_to_replan)
        action_admission = source.index(
            'failure_cleanup.set_stage("action_admission")', action_validation)
        compile_for_input = source.index("steps=compile_commands(commands)", action_admission)

        self.assertLess(loop, planner_source)
        self.assertLess(planner_source, invalidation)
        self.assertLess(invalidation, recover)
        self.assertLess(recover, fresh_source)
        self.assertLess(fresh_source, discard)
        self.assertLess(discard, discard_reason)
        self.assertLess(discard, continue_to_replan)
        self.assertLess(continue_to_replan, answer_gate)
        self.assertLess(answer_gate, action_validation)
        self.assertLess(action_validation, action_admission)
        self.assertLess(action_admission, compile_for_input)

    def test_production_initial_cover_rejection_branch_uses_caller_reset(self):
        source = Path(controller.__file__).read_text(encoding="utf-8")
        execute = source.index("def main(")
        rejected = source.index('if cover_ack["event"] == "rejected":', execute)
        reset = source.index("reset_cover_after_preacceptance_rejection(", rejected)
        fresh_source = source.index('latest = reset["latest"]', reset)
        planner_input = source.index("action_source_observation=dict(latest)", fresh_source)
        self.assertLess(rejected, reset)
        self.assertLess(reset, fresh_source)
        self.assertLess(fresh_source, planner_input)

    def test_observations_consumed_during_executor_ack_are_replayed_after_admission(self):
        class Monitor:
            event_types = {"typed_observation"}
            def __init__(self): self.seen = []
            def observe(self, row):
                self.seen.append(row["sequence"])
                if row["sequence"] == 12:
                    return {"event": "running_action_invalidation",
                            "reason": "health:below_hard_minimum",
                            "source_event": row}
                return None

        monitor = Monitor()
        consumed = [
            {"event": "typed_observation", "sequence": 12},
            {"event": "accepted", "id": "plan-0"},
        ]

        boundary = controller.replay_action_observations_before_wait(
            consumed, monitor)

        self.assertEqual(boundary["event"], "running_action_invalidation")
        self.assertEqual(monitor.seen, [12])

    def test_soft_ack_observation_is_replayed_without_false_invalidation(self):
        class Monitor:
            event_types = {"typed_observation"}
            def __init__(self): self.seen = []
            def observe(self, row):
                self.seen.append(row["sequence"])
                return None

        monitor = Monitor()
        consumed = [
            {"event": "typed_observation", "sequence": 12},
            {"event": "accepted", "id": "plan-0"},
        ]

        boundary = controller.replay_action_observations_before_wait(
            consumed, monitor)

        self.assertIsNone(boundary)
        self.assertEqual(monitor.seen, [12])

    def test_production_action_ack_replay_follows_guard_admission_before_terminal_wait(self):
        source = Path(controller.__file__).read_text(encoding="utf-8")
        execute = source.index("def execute_segment(")
        ack_buffer = source.index("ack_wait_events=[]", execute)
        accepted_wait = source.index("consumed_events=ack_wait_events", ack_buffer)
        guard_admission = source.index("running_guard.admit_program(", accepted_wait)
        replay = source.index("replay_action_observations_before_wait(", guard_admission)
        terminal_wait = source.index('r["event"]=="terminal"', replay)

        self.assertLess(ack_buffer, accepted_wait)
        self.assertLess(accepted_wait, guard_admission)
        self.assertLess(guard_admission, replay)
        self.assertLess(replay, terminal_wait)

    def test_running_invalidation_accepts_naturally_completed_cover_only_when_neutral(self):
        class Stdin:
            def write(self, value): pass
            def flush(self): pass
        class Process:
            stdin = Stdin()
        class Planner:
            def invalidate_turn(self, handle):
                return {"outcome": "locally_invalidated"}
            def interrupt(self, handle, before_transport=None):
                if before_transport is not None: before_transport()
                return {"status": "interrupted"}

        def wait_for_matching_terminal(terminal):
            unrelated = dict(terminal, id="other-cover")
            rows = (unrelated, terminal)

            def wait(predicate):
                return next((row for row in rows if predicate(row)), None)

            return wait

        for status in ("completed", "expired"):
            neutral_terminal = {
                "event": "terminal", "id": "cover-0", "status": status,
                "release": {"event": "owner_release", "verified": True, "keys_down": [],
                            "buttons_down": [], "keys_unknown": [],
                            "key_state_errors": []}}
            result = controller.cancel_invalidated_cover(
                Planner(), object(), Process(), wait_for_matching_terminal(neutral_terminal),
                "cover-0")
            self.assertIs(result[1], neutral_terminal)

            held_terminal = {
                "event": "terminal", "id": "cover-0", "status": status,
                "release": {"verified": True, "keys_down": ["space"],
                            "buttons_down": [], "keys_unknown": [],
                            "key_state_errors": []}}
            with self.assertRaisesRegex(RuntimeError, "verify empty release"):
                controller.cancel_invalidated_cover(
                    Planner(), object(), Process(), wait_for_matching_terminal(held_terminal),
                    "cover-0")

        for status in ("failed", "needs_decision"):
            terminal = {
                "event": "terminal", "id": "cover-0", "status": status,
                "release": {"event": "owner_release", "verified": True, "keys_down": [],
                            "buttons_down": [], "keys_unknown": [],
                            "key_state_errors": []}}
            with self.subTest(status=status):
                with self.assertRaisesRegex(RuntimeError, "verify empty release"):
                    controller.cancel_invalidated_cover(
                        Planner(), object(), Process(), wait_for_matching_terminal(terminal),
                        "cover-0")

    def test_running_invalidation_rejects_nonempty_or_unverified_release(self):
        class Stdin:
            def write(self, value): pass
            def flush(self): pass
        class Process:
            stdin = Stdin()
        class Planner:
            def invalidate_turn(self, handle):
                return {"outcome": "locally_invalidated"}
            def interrupt(self, handle, before_transport=None):
                if before_transport is not None: before_transport()
                return {"status": "interrupted"}
        for release in (
            {"verified": False, "keys_down": [], "buttons_down": []},
            {"verified": True, "keys_down": ["W"], "buttons_down": [],
             "keys_unknown": [], "key_state_errors": []},
            {"event": "owner_release", "verified": True,
             "keys_down": [], "buttons_down": ["fire"],
             "keys_unknown": [], "key_state_errors": []},
        ):
            terminal = {"event": "terminal", "id": "cover-0", "status": "cancelled",
                        "release": release}
            with self.subTest(release=release):
                with self.assertRaisesRegex(RuntimeError, "verify empty release"):
                    controller.cancel_invalidated_cover(
                        Planner(), object(), Process(), lambda predicate: terminal, "cover-0")


if __name__ == "__main__":
    unittest.main()
