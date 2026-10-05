import copy
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import session_map01_v19 as candidate


class MeasuredTailCompositionTests(unittest.TestCase):
    def test_unmatched_release_pair_is_censored_and_final_sample_runs(self):
        import map01_scorer_stdio_adapter_v3 as adapter

        raw = HERE / "map01_v39_perkey_measurement_consumer_a03_20261005" / "INPUT_EVENTS.jsonl"
        events = [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines()]
        down = next(row for row in events if row["event"] == "input_admission")
        up = copy.deepcopy(next(row for row in events
                                if row["event"] == "input_release_measurement"))
        # A reverse-order multi-key release can pair B's down with A's up.
        up["key"] = "F9"
        measurement = up["physical_key_measurement"]
        measurement["adapter_edge"]["key"] = "F9"
        measurement["bracket"]["key"] = "F9"

        class Polling:
            def sample_measured_tail(self, **kwargs):
                return adapter.validate_measured_release_pair(
                    kwargs["admission_event"], kwargs["release_measurement"],
                    backend_held_after=kwargs["backend_held_after"])

        events_seen = []
        with tempfile.TemporaryDirectory() as tmp:
            result = candidate._run_measured_tail(
                Polling(), tmp, (down, up, []), lambda: events_seen.append("final"))
            saved = json.loads((Path(tmp) / "scorer-post-release-tail.json").read_text())
        self.assertEqual(result["termination"], "no_matched_release_pair")
        self.assertEqual(result["disposition"], "CENSORED")
        self.assertEqual(result["error_type"], "MeasuredReleaseError")
        self.assertEqual(result, saved)
        self.assertEqual(events_seen, ["final"])
        self.assertFalse(result["grants_input_authority"])

    def test_unexpected_tail_error_remains_distinct_from_censoring(self):
        class Polling:
            def sample_measured_tail(self, **_kwargs):
                raise RuntimeError("polling failed")

        events_seen = []
        pair = ({"event": "input_admission"},
                {"event": "input_release_measurement"}, [])
        with tempfile.TemporaryDirectory() as tmp:
            result = candidate._run_measured_tail(
                Polling(), tmp, pair, lambda: events_seen.append("final"))
        self.assertEqual(result["termination"], "tail_error")
        self.assertEqual(result["error_type"], "RuntimeError")
        self.assertEqual(events_seen, ["final"])

    def test_backend_capture_keeps_raw_event_names_and_requires_empty_backend(self):
        events, state = [], {}

        class Backend:
            def __init__(self, session, out, emit, signal_readers):
                self.emit = emit
                self.held = set()

        wrapped = candidate._capture_backend(Backend, state)
        backend = wrapped(None, None, events.append, None)
        down = {"event": "input_admission", "id": "p", "step": 1}
        up = {"event": "input_release_measurement", "id": "p", "step": 1}
        backend.held.add("F8")
        backend.emit(down)
        backend.held.clear()
        backend.emit(up)
        self.assertEqual(events, [down, up])
        self.assertEqual(state["candidate"], (down, up, []))

        backend.held.add("F9")
        backend.emit(down)
        backend.emit(up)
        self.assertIsNone(state["candidate"])

    def test_emit_failure_does_not_publish_candidate(self):
        state = {}

        class Backend:
            def __init__(self, session, out, emit, signal_readers):
                self.emit = emit
                self.held = set()

        def fail(_row):
            raise OSError("event sink failed")

        backend = candidate._capture_backend(Backend, state)(None, None, fail, None)
        with self.assertRaisesRegex(OSError, "event sink failed"):
            backend.emit({"event": "input_admission", "id": "p", "step": 1})
        self.assertNotIn("admission", state)
        self.assertNotIn("candidate", state)

    def test_measured_tail_runs_before_final_sample_and_records_boundary(self):
        events = []

        class Polling:
            def sample_measured_tail(self, **kwargs):
                events.append("tail")
                self.arguments = kwargs
                return {"termination": "command_ready", "disposition": "CENSORED",
                        "tail_samples": 0, "source_event_types": [
                            "input_admission", "input_release_measurement"]}

        candidate_pair = ({"event": "input_admission"},
                          {"event": "input_release_measurement"}, [])
        with tempfile.TemporaryDirectory() as tmp:
            outcome = candidate._run_measured_tail(
                Polling(), tmp, candidate_pair, lambda: events.append("final"))
            saved = json.loads((Path(tmp) / "scorer-post-release-tail.json").read_text())
        self.assertEqual(events, ["tail", "final"])
        self.assertEqual(outcome, saved)
        self.assertFalse(saved["controller_visible"])
        self.assertFalse(saved["grants_input_authority"])

    def test_missing_candidate_skips_tail_but_keeps_final_sample(self):
        events = []

        class Polling:
            def sample_measured_tail(self, **kwargs):
                self.fail("unverified evidence must not reach scorer")

        with tempfile.TemporaryDirectory() as tmp:
            result = candidate._run_measured_tail(
                Polling(), tmp, None, lambda: events.append("final"))
        self.assertEqual(events, ["final"])
        self.assertEqual(result["termination"], "no_verified_perkey_release")

    def test_controller_selects_v19_only_for_new_explicit_flag(self):
        sys.path.insert(0, str(HERE.parent / "live_control"))
        import map01_overlap_controller_v39 as controller
        base = {"seed": 7, "load_fixture_manifest": Path("fixture.json")}
        self.assertTrue(controller.session_command(
            types.SimpleNamespace(**base), Path("out"))[1].endswith("session_map01_v12.py"))
        self.assertTrue(controller.session_command(
            types.SimpleNamespace(**base, post_release_scorer_tail=True), Path("out"))[1]
            .endswith("session_map01_v18.py"))
        self.assertTrue(controller.session_command(
            types.SimpleNamespace(**base, post_release_perkey_scorer_tail=True), Path("out"))[1]
            .endswith("session_map01_v19.py"))

    def test_main_patches_session_backend_to_the_perkey_bridge(self):
        class BaseBackend:
            pass

        class PerKeyBackend(BaseBackend):
            def __init__(self, session, out, emit, signal_readers):
                self.emit = emit
                self.held = set()

        session_module = types.ModuleType("session_map01_v12")
        session_module.Backend = BaseBackend
        package = types.ModuleType("map01_v39_perkey_bridge_a01")
        bridge = types.ModuleType("map01_v39_perkey_bridge_a01.bridge")
        bridge.Backend = PerKeyBackend
        telemetry = types.ModuleType("doom_owner_thread_release_batch_backend_v1")
        telemetry.Backend = BaseBackend
        state_seen = {}

        def run_previous():
            wrapper = telemetry.Backend
            session_module.Backend = wrapper
            self.assertIsNot(wrapper, BaseBackend)
            self.assertIs(wrapper.__bases__[0], PerKeyBackend)
            backend = wrapper(None, None, lambda _row: None, None)
            backend.held.add("F8")
            backend.emit({"event": "input_admission", "id": "p", "step": 1})
            backend.held.clear()
            backend.emit({"event": "input_release_measurement", "id": "p", "step": 1})
            state_seen.update(backend._v19_state)
            return "ok"

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "sources.json").write_text("{}", encoding="utf-8")
            with patch.object(candidate.previous, "_option", return_value=tmp), \
                    patch.object(candidate.previous, "main", side_effect=run_previous), \
                    patch.dict(sys.modules, {
                        "session_map01_v12": session_module,
                        "map01_v39_perkey_bridge_a01": package,
                        "map01_v39_perkey_bridge_a01.bridge": bridge,
                        telemetry.__name__: telemetry,
                    }):
                self.assertEqual(candidate.main(), "ok")
            self.assertEqual(state_seen["candidate"][0]["event"], "input_admission")
            self.assertEqual(state_seen["candidate"][1]["event"], "input_release_measurement")
            self.assertEqual(state_seen["candidate"][2], [])
        self.assertIs(session_module.Backend, BaseBackend)
        self.assertIs(telemetry.Backend, BaseBackend)

    def test_real_v15_chain_keeps_capture_and_restores_backend_bindings(self):
        class BaseBackend:
            pass

        class PerKeyBackend:
            def __init__(self, session, out, emit, signal_readers):
                self.emit = emit
                self.held = set()

        class Polling:
            def __init__(self, *args, **kwargs):
                pass

            def stats(self):
                return {"inert": True}

        class Sink:
            def __init__(self, out):
                pass

            def finalize(self, stats):
                pass

        for fail_leaf in (False, True):
            with self.subTest(fail_leaf=fail_leaf):
                leaf_error = RuntimeError("inert V12 leaf failure")
                session = types.ModuleType("session_map01_v12")
                session.Backend = BaseBackend
                game_constructor = lambda: self.fail("game must not start")
                session.vd = types.SimpleNamespace(DoomGame=game_constructor)
                session.sys = sys
                telemetry = types.ModuleType("doom_owner_thread_release_batch_backend_v1")
                telemetry.Backend = BaseBackend
                executor = types.ModuleType("executor_v13")
                executor.Executor = type("InertExecutor", (), {})
                package = types.ModuleType("map01_v39_perkey_bridge_a01")
                bridge = types.ModuleType("map01_v39_perkey_bridge_a01.bridge")
                bridge.Backend = PerKeyBackend
                reached = []
                original_main = candidate.previous.main
                original_proxy = candidate.previous._GameProxy
                original_polling = candidate.previous.MainThreadScorerStdin
                original_stdin = sys.stdin

                def leaf():
                    self.assertIs(sys._getframe(1).f_code, original_main.__code__)
                    self.assertIs(session.Backend, telemetry.Backend)
                    self.assertIs(session.Backend.__bases__[0], PerKeyBackend)
                    rows = []
                    backend = session.Backend(None, None, rows.append, None)
                    down = {"event": "input_admission", "id": "p", "step": 1}
                    up = {"event": "input_release_measurement", "id": "p", "step": 1}
                    backend.held.add("F8")
                    backend.emit(down)
                    backend.held.clear()
                    backend.emit(up)
                    self.assertEqual(rows, [down, up])
                    self.assertEqual(backend._v19_state["candidate"], (down, up, []))
                    reached.append(True)
                    if fail_leaf:
                        raise leaf_error

                session.main = leaf
                modules = {session.__name__: session, telemetry.__name__: telemetry,
                           executor.__name__: executor, package.__name__: package,
                           bridge.__name__: bridge}
                with patch.dict(sys.modules, modules), \
                        patch.object(sys, "argv", ["v19", "--out", "inert-output"]), \
                        patch.object(candidate, "MeasuredScorerStdin", Polling), \
                        patch.object(candidate.previous, "ScorerFileSink", Sink), \
                        patch.object(candidate.previous, "_merge_sources", return_value=False), \
                        patch.object(candidate, "_record_source_manifest", return_value=False):
                    if fail_leaf:
                        with self.assertRaises(RuntimeError) as raised:
                            candidate.main()
                        self.assertIs(raised.exception, leaf_error)
                    else:
                        candidate.main()
                self.assertEqual(reached, [True])
                self.assertIs(session.Backend, BaseBackend)
                self.assertIs(telemetry.Backend, BaseBackend)
                self.assertIs(candidate.previous.main, original_main)
                self.assertIs(candidate.previous._GameProxy, original_proxy)
                self.assertIs(candidate.previous.MainThreadScorerStdin, original_polling)
                self.assertIs(session.vd.DoomGame, game_constructor)
                self.assertIs(sys.stdin, original_stdin)


if __name__ == "__main__":
    unittest.main(verbosity=2)
