import json
from contextlib import contextmanager
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from runtime import native_comparison_candidate_v1 as candidate


USAGE = {"input_tokens": 20, "cached_input_tokens": 4,
         "cache_write_input_tokens": 0, "output_tokens": 5,
         "reasoning_output_tokens": 1}


def stage_fake_effects(out, arm, seed, *, exact=True):
    runtime = out / "arms" / arm / "runtime"
    runtime.mkdir(parents=True)
    history = [{"task_id": f"task-{i}", "layout": "A" if i < 4 else "B",
                "schema": "integrated_efficiency_submission_v1", "exact": True,
                "expected_token": f"t{seed:06d}-{i}", "submitted_values": [f"t{seed:06d}-{i}"]}
               for i in range(1, 7)]
    if not exact:
        history[0]["submitted_values"] = ["incorrect"]
    events = []
    for i in range(1, 7):
        events.extend([{"event": "accepted", "id": i}, {"event": "terminal", "id": i,
                      "release": {"verified": True, "keys_down": [], "buttons_down": []}}])
    (runtime / "submission-history.jsonl").write_text("\n".join(map(json.dumps, history)))
    (runtime / "events.jsonl").write_text("\n".join(map(json.dumps, events)))
    (runtime / "delivered.jsonl").write_text("\n".join(map(json.dumps, events)))
    (runtime.parent / "task-details.json").write_text(json.dumps(
        [{"trace": {"task_id": f"task-{i}"}, "program_count": 1} for i in range(1, 7)]))


class NativeComparisonCandidateTests(unittest.TestCase):
    def test_arm_owns_one_app_server_with_fresh_threads_and_retains_groundings(self):
        timeline = []

        class Owner:
            def __init__(self, windows_python, convert, root):
                timeline.append(("job", windows_python, root.name))
                self.reference = {"windows_executable": "native.exe"}

        class Client:
            def __init__(self, argv, *, cwd, journal_path, windows_owner):
                self.closed = False
                timeline.append(("launch", argv, cwd.name, journal_path.name,
                                 windows_owner.reference["windows_executable"]))

            def initialize(self):
                timeline.append("initialize")

            def close(self):
                self.closed = True
                timeline.append("close")

        class Model:
            def __init__(self, session_root, workspace, **kwargs):
                self.client = kwargs["client"]
                self.root = session_root
                timeline.append(("thread", session_root.name, kwargs["contract"],
                                 kwargs["model"], kwargs["effort"],
                                 kwargs["allow_missing_cache_write"]))

            def call(self, root, prompt, image, contract, workspace):
                if self.client.closed:
                    raise RuntimeError("grounding ran outside the owned client")
                timeline.append(("turn", root.name, contract))
                return {"usage": dict(USAGE), "call_id": root.name,
                        "thread_id": self.root.name}

        with TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            with patch.object(candidate, "WindowsAppServerOwner", Owner), \
                 patch.object(candidate, "CodexAppServerClient", Client), \
                 patch.object(candidate, "PersistentGroundingModel", Model), \
                 patch.object(candidate, "direct_command", return_value=["native.exe"]):
                with candidate.owned_grounding(root / "plain", workspace, contract="plain",
                                               executable=Path("native.exe"),
                                               windows_python=Path("python.exe"),
                                               allowed_groundings=(root / "first", root / "second")) as call:
                    for name in ("first", "second"):
                        self.assertEqual(call(root / name, "prompt", root / "image.png",
                                              "plain", workspace)["usage"], USAGE)
            self.assertEqual(timeline, [
                ("job", Path("python.exe"), "plain"),
                ("launch", ["native.exe"], "workspace", "protocol.jsonl", "native.exe"),
                "initialize",
                ("thread", "01", "plain", "gpt-5.6-luna", "low", True),
                ("turn", "first", "plain"),
                ("thread", "02", "plain", "gpt-5.6-luna", "low", True),
                ("turn", "second", "plain"),
                "close",
            ])

    def test_startup_error_preserves_original_and_still_retires_client(self):
        close_attempted = []

        class Client:
            def __init__(self, *args, **kwargs):
                pass

            def initialize(self):
                raise RuntimeError("initialize failed")

            def close(self):
                close_attempted.append(True)
                raise ValueError("retirement failed")

        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(candidate, "CodexAppServerClient", Client), \
                 patch.object(candidate, "direct_command", return_value=["native.exe"]):
                with self.assertRaisesRegex(RuntimeError, "initialize failed") as raised:
                    with candidate.owned_grounding(root / "native", root, contract="compiled",
                                                   executable=Path("native.exe"),
                                                   windows_python=Path("python.exe"),
                                                   allowed_groundings=(root / "task",)):
                        self.fail("failed initialization admitted an arm")
        self.assertEqual(close_attempted, [True])
        self.assertIn("ValueError", raised.exception.__notes__[0])

    def test_failed_known_and_unacknowledged_attempts_are_not_counted_as_zero(self):
        for known_turn in (True, False):
            with self.subTest(known_turn=known_turn), TemporaryDirectory() as directory:
                root = Path(directory)
                session = root / "native"
                error = RuntimeError("turn failed")
                if known_turn:
                    error.call_id = "provider-turn"
                    error.thread_id = "provider-thread"
                    error.usage = {**USAGE, "input_tokens": 13}
                    del error.usage["cache_write_input_tokens"]

                class Model:
                    def __init__(self, *args, **kwargs):
                        self.start = json.loads(
                            (session / "attempts/01/start.json").read_text())

                    def call(self, *args):
                        if self.start["generation"] != 1:
                            raise ValueError("attempt was not recorded before the turn")
                        raise error

                with patch.object(candidate, "CodexAppServerClient"), \
                     patch.object(candidate, "PersistentGroundingModel", Model), \
                     patch.object(candidate, "direct_command", return_value=["native.exe"]):
                    with self.assertRaises(RuntimeError) as raised:
                        with candidate.owned_grounding(session, root, contract="compiled",
                                                       executable=Path("native.exe"),
                                                       windows_python=Path("python.exe"),
                                                       allowed_groundings=(root / "task",)) as call:
                            call(root / "task", "prompt", root / "image.png", "compiled", root)
                self.assertIs(raised.exception, error)
                terminal = json.loads((session / "attempts/01/terminal.json").read_text())
                self.assertEqual(terminal["status"], "failed")
                self.assertIs(terminal["provider_turn_observed"], True if known_turn else None)
                self.assertEqual(terminal["usage"], error.usage if known_turn else None)

    def test_forbidden_or_repeated_repair_cannot_start_a_provider_thread(self):
        for repeated in (False, True):
            with self.subTest(repeated=repeated), TemporaryDirectory() as directory:
                out = Path(directory)
                session = out / "native-app-server/persistent"
                slots = candidate.scheduled_grounding_roots(out, "persistent")
                self.assertEqual([slot.relative_to(out).as_posix() for slot in slots], [
                    "model-calls/persistent/task-1/anchor", "model-calls/persistent/task-4/repair"])
                with patch.object(candidate, "CodexAppServerClient"), \
                     patch.object(candidate, "PersistentGroundingModel") as model, \
                     patch.object(candidate, "direct_command", return_value=["native.exe"]):
                    model.return_value.call.return_value = {
                        "usage": USAGE, "call_id": "provider-call", "thread_id": "provider-thread"}
                    with candidate.owned_grounding(session, out, contract="compiled",
                                                   executable=Path("native.exe"),
                                                   windows_python=Path("python.exe"),
                                                   allowed_groundings=slots) as call:
                        if repeated:
                            call(slots[0], "prompt", out / "image.png", "compiled", out)
                        invalid = slots[0] if repeated else out / "model-calls/persistent/task-2/repair"
                        with self.assertRaisesRegex(ValueError, "scheduled"):
                            call(invalid, "prompt", out / "image.png", "compiled", out)
                    self.assertEqual(model.call_count, 1 if repeated else 0)
                refusal = json.loads((session / "refused-groundings/01.json").read_text())
                self.assertIs(refusal["provider_turn_observed"], False)

    def test_terminal_publication_failure_retains_known_provider_usage(self):
        with TemporaryDirectory() as directory:
            out = Path(directory)
            session = out / "native"
            published = candidate.write_record
            failure = OSError("simulated fsync failure")

            def save(path, payload):
                if path.name == "terminal.json":
                    raise failure
                return published(path, payload)

            with patch.object(candidate, "CodexAppServerClient"), \
                 patch.object(candidate, "PersistentGroundingModel") as model, \
                 patch.object(candidate, "direct_command", return_value=["native.exe"]), \
                 patch.object(candidate, "write_record", side_effect=save):
                model.return_value.call.return_value = {
                    "usage": USAGE, "call_id": "provider-call", "thread_id": "provider-thread"}
                with self.assertRaises(candidate.GroundingCallError) as reported:
                    with candidate.owned_grounding(session, out, contract="compiled",
                                                   executable=Path("native.exe"),
                                                   windows_python=Path("python.exe"),
                                                   allowed_groundings=(out / "task",)) as call:
                        call(out / "task", "prompt", out / "image.png", "compiled", out)
            self.assertEqual(reported.exception.call_id, "provider-call")
            self.assertEqual(reported.exception.thread_id, "provider-thread")
            self.assertEqual(reported.exception.usage, USAGE)
            self.assertIs(reported.exception.__cause__, failure)
            self.assertTrue((session / "attempts/01/start.json").is_file())
            recovered = json.loads(
                (session / "attempts/01/terminal-publication-failure.json").read_text())
            self.assertEqual(recovered["status"], "terminal_publication_failed")
            self.assertEqual(recovered["call_id"], reported.exception.call_id)
            self.assertEqual(recovered["usage"], USAGE)

    def test_capture_schedules_all_arms_for_one_seed_then_holds_for_raw_audit(self):
        observed = []
        counts = {"plain": 6, "ephemeral": 6, "persistent": 2}

        def preflight(arm, contract, workspace):
            observed.append(("preflight", arm, contract))
            workspace.mkdir(parents=True)
            return {"usage": USAGE}

        @contextmanager
        def grounding(arm, contract, workspace):
            observed.append(("open", arm, contract))
            yield lambda: observed.append(("turn", arm))
            observed.append(("close", arm))

        def run_arm(arm, seed, workspace, model_call):
            self.assertEqual(seed, 991032)
            self.assertEqual(workspace.name, arm)
            for _ in range(counts[arm]):
                model_call()
            stage_fake_effects(workspace.parent.parent, arm, seed)
            return [{"typed_outcome": "completed", "exact_submission": True,
                     "submission_count": 1, "releases_verified": True}] * 6, {"success": True}

        with TemporaryDirectory() as directory:
            out = Path(directory) / "fresh"
            result = candidate.capture_block(out, 991032, preflight=preflight,
                                             run_arm=run_arm, open_grounding=grounding)
            self.assertEqual(result["disposition"], "HOLD")
            self.assertEqual(result["reason"], "independent_raw_audit_required")
            self.assertEqual(result["arms"], dict.fromkeys(counts, "captured"))
            self.assertEqual(json.loads((out / "capture.json").read_text()), result)
            with self.assertRaises(FileExistsError):
                candidate.capture_block(out, 991032, preflight=preflight,
                                        run_arm=run_arm, open_grounding=grounding)
        for arm, count in counts.items():
            self.assertEqual(observed.count(("turn", arm)), count)
        self.assertEqual([entry for entry in observed if entry[0] == "preflight"], [
            ("preflight", "plain", "plain"), ("preflight", "ephemeral", "compiled"),
            ("preflight", "persistent", "compiled")])

    def test_capture_stops_before_next_arm_on_effect_or_release_disagreement(self):
        for failure in ("raw_effect", "release"):
            with self.subTest(failure=failure), TemporaryDirectory() as directory:
                out = Path(directory) / "fresh"
                preflights = []

                def preflight(arm, contract, workspace):
                    preflights.append(arm)
                    return {"usage": USAGE}

                @contextmanager
                def grounding(*args):
                    yield None

                def run_arm(arm, seed, workspace, model_call):
                    stage_fake_effects(out, arm, seed, exact=failure != "raw_effect")
                    return [{"typed_outcome": "completed", "exact_submission": True,
                             "submission_count": 1, "releases_verified": failure != "release"}] * 6, {
                                 "success": True}

                result = candidate.capture_block(out, 991032, preflight=preflight,
                                                 run_arm=run_arm, open_grounding=grounding)
                self.assertEqual(preflights, ["plain"])
                self.assertEqual(result["arms"]["plain"], "incomplete")
                self.assertEqual(result["arms"]["ephemeral"], "not_run")

    def test_capture_preserves_first_failure_and_explicitly_marks_unstarted_arms(self):
        def fail(arm, contract, workspace):
            raise TimeoutError("preflight result unobserved")

        with TemporaryDirectory() as directory:
            out = Path(directory) / "fresh"
            result = candidate.capture_block(out, 991032, preflight=fail,
                                             run_arm=None, open_grounding=None)
            self.assertEqual(result["disposition"], "HOLD")
            self.assertEqual(result["arms"], {"plain": "interrupted", "ephemeral": "not_run",
                                              "persistent": "not_run"})
            self.assertTrue((out / "capture-arms/plain/preflight-start.json").is_file())
            self.assertFalse((out / "capture-arms/ephemeral").exists())
            failure = json.loads((out / "capture-arms/plain/failure.json").read_text())
            self.assertEqual(failure, {"stage": "preflight", "error_type": "TimeoutError",
                                       "provider_calls_observed": None})

    def test_independent_effect_and_terminal_audit_uses_raw_values(self):
        seed = 991032
        with TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "arms/plain/runtime"
            stage_fake_effects(root, "plain", seed)
            submissions = runtime / "submission-history.jsonl"
            trace = runtime / "events.jsonl"
            good = candidate.audit_local_effects(root, seed, "plain")
            self.assertTrue(good["exact_once_in_allocation_order"])
            self.assertTrue(good["all_accepted_programs_released"])
            history = [json.loads(line) for line in submissions.read_text().splitlines()]
            history[3]["submitted_values"] = ["wrong-even-if-exact-flag-is-true"]
            submissions.write_text("\n".join(map(json.dumps, history)))
            subset = "\n".join(trace.read_text().splitlines()[:2])
            trace.write_text(subset)
            (runtime / "delivered.jsonl").write_text(subset)
            invalid = candidate.audit_local_effects(root, seed, "plain")
            self.assertEqual(invalid["exact_tasks"], 5)
            self.assertFalse(invalid["exact_once_in_allocation_order"])
            self.assertFalse(invalid["all_accepted_programs_released"])

    @unittest.skipUnless(os.name == "posix", "checked GUI runtime imports POSIX fcntl")
    def test_native_binding_reuses_checked_arm_and_restores_frozen_paths(self):
        from runtime import golden_desktop_demo_v3 as golden
        import run_integrated_efficiency_live_v1 as implementation
        import schema_preflight_v1

        original_out = implementation.OUT
        original_client = implementation.RuntimeClient
        original_executable = schema_preflight_v1.CLI_EXE_WSL
        with TemporaryDirectory() as directory:
            out = Path(directory).resolve() / "fresh"
            config = {"windows_codex_exe": Path("native.exe"), "windows_python": Path("python.exe"),
                      "chromium": Path("chromium")}
            health = {"passed": True, "native_codex": {}}
            with patch.object(golden.previous.base, "configuration", return_value=config), \
                 patch.object(golden, "doctor", return_value=health):
                with candidate.bind_golden_runner(out) as (checked, bindings):
                    self.assertIs(checked, health)
                    self.assertEqual(implementation.OUT, out)
                    self.assertIsNot(implementation.RuntimeClient, original_client)
                    self.assertIs(bindings["run_arm"], implementation.run_arm)
                    self.assertEqual(schema_preflight_v1.CLI_EXE_WSL, config["windows_codex_exe"])
                    with self.assertRaisesRegex(ValueError, "workspace"):
                        bindings["preflight"]("plain", "plain", out)
        self.assertEqual(implementation.OUT, original_out)
        self.assertIs(implementation.RuntimeClient, original_client)
        self.assertIs(schema_preflight_v1.CLI_EXE_WSL, original_executable)


if __name__ == "__main__":
    unittest.main()
