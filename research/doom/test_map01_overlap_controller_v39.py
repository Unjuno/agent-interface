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
                 "release": {"verified": True, "keys_down": [], "buttons_down": [],
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
                 "release": {"verified": True, "keys_down": [], "buttons_down": [],
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
            def __init__(self): self.interrupted = []
            def interrupt(self, handle, before_transport=None):
                if before_transport is not None: before_transport()
                self.interrupted.append(handle)
                return {"status": "interrupted"}
        terminal = {"event": "terminal", "id": "cover-0", "status": "cancelled",
                    "release": {"verified": True, "keys_down": [], "buttons_down": []}}
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
                    "release": {"verified": True, "keys_down": [],
                                "buttons_down": []}}
        process = Process()
        result = controller.cancel_initial_cover_before_planner(
            process, lambda predicate: terminal if predicate(terminal) else None,
            "cover-0")

        self.assertIs(result, terminal)
        self.assertIn('"op": "cancel"', process.stdin.writes[0])
        for release in (
            {"verified": False, "keys_down": [], "buttons_down": []},
            {"verified": True, "keys_down": ["W"], "buttons_down": []},
            {"verified": True, "keys_down": [], "buttons_down": ["fire"]},
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
                    "release": {"verified": True, "keys_down": [],
                                "buttons_down": []}}

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
        model_session_filter = source.index('row["model_session_id"] for row in decisions if "model_session_id" in row', report_path - 8000)
        model_wall_sum = source.index('x.get("model_ns", 0)', report_path - 1000)
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
                "release": {"verified": True, "keys_down": [], "buttons_down": []}}
            result = controller.cancel_invalidated_cover(
                Planner(), object(), Process(), wait_for_matching_terminal(neutral_terminal),
                "cover-0")
            self.assertIs(result[1], neutral_terminal)

            held_terminal = {
                "event": "terminal", "id": "cover-0", "status": status,
                "release": {"verified": True, "keys_down": ["space"], "buttons_down": []}}
            with self.assertRaisesRegex(RuntimeError, "verify empty release"):
                controller.cancel_invalidated_cover(
                    Planner(), object(), Process(), wait_for_matching_terminal(held_terminal),
                    "cover-0")

        for status in ("failed", "needs_decision"):
            terminal = {
                "event": "terminal", "id": "cover-0", "status": status,
                "release": {"verified": True, "keys_down": [], "buttons_down": []}}
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
            def interrupt(self, handle, before_transport=None):
                if before_transport is not None: before_transport()
                return {"status": "interrupted"}
        for release in (
            {"verified": False, "keys_down": [], "buttons_down": []},
            {"verified": True, "keys_down": ["W"], "buttons_down": []},
            {"verified": True, "keys_down": [], "buttons_down": ["fire"]},
        ):
            terminal = {"event": "terminal", "id": "cover-0", "status": "cancelled",
                        "release": release}
            with self.subTest(release=release):
                with self.assertRaisesRegex(RuntimeError, "verify empty release"):
                    controller.cancel_invalidated_cover(
                        Planner(), object(), Process(), lambda predicate: terminal, "cover-0")


if __name__ == "__main__":
    unittest.main()
