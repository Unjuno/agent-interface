import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "live_control"))
for _name in ("map01_scorer_stdio_adapter_v1", "independent_progress_clock_v2"):
    sys.modules.setdefault(_name, types.ModuleType(_name))
sys.modules["map01_scorer_stdio_adapter_v1"].MainThreadScorerStdin = type("Polling", (), {})
sys.modules["map01_scorer_stdio_adapter_v1"].ScorerFileSink = type("Sink", (), {})
sys.modules["independent_progress_clock_v2"].ProgressSample = type("ProgressSample", (), {})
import session_map01_v15 as candidate
from executor_v13 import Executor as ReleaseOrderedExecutor


class SessionSelectionTests(unittest.TestCase):
    def test_timed_hold_is_explicit_and_requires_owned_process_identity(self):
        candidate.validate_timed_hold_options([])
        candidate.validate_timed_hold_options(["--owner-timed-hold","--owned-input-service","--target-process-identity"])
        for argv in (["--owner-timed-hold"],
                     ["--owner-timed-hold","--owned-input-service"],
                     ["--owner-timed-hold","--owned-input-service","--target-process-identity","--owner-timed-hold"],
                     ["--owner-timed-hold=yes","--owned-input-service","--target-process-identity"]):
            with self.subTest(argv=argv),self.assertRaises(ValueError):candidate.validate_timed_hold_options(argv)
    def test_v15_selects_release_ordered_executor_and_hashes_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "sources.json").write_text("{}", encoding="utf-8")
            scorer = types.ModuleType("map01_scorer_stdio_adapter_v1")
            scorer.MainThreadScorerStdin = type("Polling", (), {
                "__init__": lambda self, *args, **kwargs: None,
                "stats": lambda self: {},
            })
            scorer.ScorerFileSink = type("Sink", (), {
                "__init__": lambda self, *args, **kwargs: None,
                "finalize": lambda self, *args: None,
            })
            clock = types.ModuleType("independent_progress_clock_v2")
            clock.ProgressSample = type("ProgressSample", (), {})
            old_scorer = sys.modules.get("map01_scorer_stdio_adapter_v1")
            old_clock = sys.modules.get("independent_progress_clock_v2")
            sys.modules["map01_scorer_stdio_adapter_v1"] = scorer
            sys.modules["independent_progress_clock_v2"] = clock
            base = types.ModuleType("session_map01_v12")
            base.vd = types.SimpleNamespace(DoomGame=object)
            base.sys = sys
            telemetry = types.ModuleType("doom_owner_thread_release_batch_backend_v1")
            telemetry.Backend = type("SelectedBackend", (), {})
            conflicting = types.ModuleType("doom_typed_release_backend_v3")
            conflicting.Backend = type("ConflictingBackend", (), {})
            names = {
                "session_map01_v12": sys.modules.get("session_map01_v12"),
                "doom_typed_release_backend_v3": sys.modules.get("doom_typed_release_backend_v3"),
                "doom_owner_thread_release_batch_backend_v1": sys.modules.get("doom_owner_thread_release_batch_backend_v1"),
            }
            sys.modules.update({"session_map01_v12": base,
                                "doom_typed_release_backend_v3": conflicting,
                                "doom_owner_thread_release_batch_backend_v1": telemetry})
            try:
                with patch.object(candidate, "MainThreadScorerStdin") as polling, \
                     patch.object(candidate, "ScorerFileSink") as sink:
                    with patch.object(base, "main", return_value=None, create=True) as run_base:
                        oldargv, oldstdin = sys.argv, sys.stdin
                        sys.argv = ["session", "--out", str(out)]
                        try:
                            candidate.main()
                        finally:
                            sys.argv, sys.stdin = oldargv, oldstdin
                    self.assertIs(base.Backend, telemetry.Backend)
                    self.assertIs(base.Executor, ReleaseOrderedExecutor)
                    run_base.assert_called_once()
                manifest = json.loads((out / "sources.json").read_text(encoding="utf-8"))
                manifest = {name.replace("\\", "/"): value
                            for name, value in manifest.items()}
                for name in (
                    "doom/doom_owner_thread_release_batch_backend_v1.py",
                    "doom/doom_typed_release_backend_v2.py",
                    "live_control/executor_v13.py",
                    "live_control/executor_v12.py",
                    "live_control/input_transition_owner_v4.py",
                    "live_control/input_transition_owner_v3.py",
                    "live_control/input_owner_v12.py",
                    "live_control/input_owner_v11.py",
                ):
                    self.assertIn(name, manifest)
                    self.assertEqual(len(manifest[name]), 64)
            finally:
                for name, old in names.items():
                    if old is None:
                        sys.modules.pop(name, None)
                    else:
                        sys.modules[name] = old
                if old_scorer is None:
                    sys.modules.pop("map01_scorer_stdio_adapter_v1", None)
                else:
                    sys.modules["map01_scorer_stdio_adapter_v1"] = old_scorer
                if old_clock is None:
                    sys.modules.pop("independent_progress_clock_v2", None)
                else:
                    sys.modules["independent_progress_clock_v2"] = old_clock


class GameProxyLifecycleTests(unittest.TestCase):
    class InnerGame:
        def __init__(self, events, close_error=None):
            self.events = events
            self.close_error = close_error

        def init(self):
            self.events.append("init")
            return "initialized"

        def close(self):
            self.events.append("inner_close")
            if self.close_error is not None:
                raise self.close_error
            return "closed"

    def test_inner_game_is_closed_when_final_sample_raises(self):
        events = []
        inner = self.InnerGame(events)
        sample_error = RuntimeError("final scorer sample failed")

        def final_sample():
            self.assertFalse(proxy.closed)
            self.assertTrue(proxy.closing)
            events.append("final_sample")
            raise sample_error

        proxy = candidate._GameProxy(inner, final_sample)
        proxy.init()
        for _ in range(2):
            with self.assertRaisesRegex(RuntimeError, "final scorer sample failed") as raised:
                proxy.close()
            self.assertIs(raised.exception, sample_error)
        self.assertEqual(events, ["init", "final_sample", "inner_close"])
        self.assertTrue(proxy.closed)
        self.assertEqual(events.count("inner_close"), 1)

    def test_successful_sample_preserves_inner_close_result_and_is_idempotent(self):
        events = []
        inner = self.InnerGame(events)
        proxy = candidate._GameProxy(inner, lambda: events.append("final_sample"))
        proxy.init()
        self.assertEqual(proxy.close(), "closed")
        self.assertIsNone(proxy.close())
        self.assertEqual(events, ["init", "final_sample", "inner_close"])

    def test_sample_and_cleanup_errors_are_both_grouped(self):
        events = []
        inner = self.InnerGame(events, OSError("underlying close failed"))
        proxy = candidate._GameProxy(
            inner, lambda: (_ for _ in ()).throw(RuntimeError("sample failed")))
        proxy.init()
        with self.assertRaises(BaseExceptionGroup) as raised:
            proxy.close()
        self.assertEqual(
            [(type(error), str(error)) for error in raised.exception.exceptions],
            [(RuntimeError, "sample failed"), (OSError, "underlying close failed")],
        )
        self.assertEqual(events, ["init", "inner_close"])

    def test_repeated_close_reports_the_original_cleanup_failure(self):
        events = []
        inner = self.InnerGame(events, OSError("underlying close failed"))
        proxy = candidate._GameProxy(inner, lambda: events.append("final_sample"))
        proxy.init()

        with self.assertRaisesRegex(OSError, "underlying close failed") as first:
            proxy.close()
        with self.assertRaisesRegex(OSError, "underlying close failed") as second:
            proxy.close()

        self.assertIs(second.exception, first.exception)
        self.assertEqual(events, ["init", "final_sample", "inner_close"])

    def test_reentrant_close_during_final_sample_does_not_repeat_cleanup(self):
        events = []
        inner = self.InnerGame(events)
        proxy = None

        def final_sample():
            events.append("final_sample")
            self.assertTrue(proxy.closing)
            self.assertFalse(proxy.closed)
            self.assertIsNone(proxy.close())

        proxy = candidate._GameProxy(inner, final_sample)
        proxy.init()
        self.assertEqual(proxy.close(), "closed")
        self.assertEqual(events, ["init", "final_sample", "inner_close"])

    def test_wrapped_close_failure_is_replayed_without_a_false_success(self):
        events = []
        close_error = OSError("underlying close failed")
        inner = self.InnerGame(events, close_error)
        proxy = candidate._GameProxy(inner, lambda: events.append("final_sample"))
        proxy.init()

        for _ in range(2):
            with self.assertRaisesRegex(OSError, "underlying close failed") as raised:
                proxy.close()
            self.assertIs(raised.exception, close_error)

        self.assertTrue(proxy.closed)
        self.assertEqual(events, ["init", "final_sample", "inner_close"])

    def test_session_unwind_preserves_controller_sample_and_close_errors(self):
        events = []
        inner = self.InnerGame(events, OSError("underlying close failed"))
        proxy = candidate._GameProxy(
            inner, lambda: (_ for _ in ()).throw(RuntimeError("sample failed")))
        proxy.init()
        with self.assertRaises(BaseExceptionGroup) as raised:
            try:
                raise ValueError("controller failed")
            finally:
                proxy.close()

        def leaves(error):
            if isinstance(error, BaseExceptionGroup):
                return [leaf for child in error.exceptions for leaf in leaves(child)]
            return [error]

        messages = {(type(error), str(error)) for error in leaves(raised.exception)}
        self.assertEqual(messages, {
            (ValueError, "controller failed"),
            (RuntimeError, "sample failed"),
            (OSError, "underlying close failed"),
        })
        self.assertEqual(events, ["init", "inner_close"])
        self.assertTrue(proxy.closed)


class ProgressExitValidationTests(unittest.TestCase):
    class Variables:
        KILLCOUNT = 'kills'
        DEATHCOUNT = 'deaths'

    class Game:
        def __init__(self, finished=True, dead=False, timeout=False):
            self.finished, self.dead, self.timeout = finished, dead, timeout
        def get_episode_time(self): return 100
        def get_ticrate(self): return 35
        def get_game_variable(self, variable): return 0
        def is_episode_finished(self): return self.finished
        def is_player_dead(self): return self.dead
        def is_episode_timeout_reached(self): return self.timeout

    def test_unknown_terminal_flags_do_not_become_proven_exit(self):
        for kwargs in ({'finished':None}, {'dead':None}, {'timeout':None},
                       {'finished':1}, {'dead':0}, {'timeout':0}):
            with self.subTest(kwargs=kwargs), patch.object(candidate, 'ProgressSample', side_effect=lambda *args: args):
                with self.assertRaises(ValueError):
                    candidate._coherent_progress_sample(self.Game(**kwargs), self.Variables, 75)

    def test_unavailable_timeout_api_requires_valid_engine_clock(self):
        class Fallback(self.Game):
            is_episode_timeout_reached = None
            def __init__(self, tic, rate): super().__init__(); self.tic, self.rate=tic,rate
            def get_episode_time(self): return self.tic
            def get_ticrate(self): return self.rate
        with patch.object(candidate, 'ProgressSample', side_effect=lambda *args: args):
            for tic in (0,100,2625,2626):
                with self.subTest(tic=tic), self.assertRaises(ValueError):
                    candidate._coherent_progress_sample(Fallback(tic,35), self.Variables,75)
            dead=Fallback(100,35);dead.dead=True
            self.assertFalse(candidate._coherent_progress_sample(dead, self.Variables,75)[-1])
            running=Fallback(100,35);running.finished=False
            self.assertFalse(candidate._coherent_progress_sample(running, self.Variables,75)[-1])
            for tic,rate in ((-1,35),(100,0),(100,-1),(False,35),(100,True),('100',35),(100.1,35)):
                with self.subTest(tic=tic,rate=rate), self.assertRaises(ValueError):
                    candidate._coherent_progress_sample(Fallback(tic,rate), self.Variables,75)

    def test_invalid_counter_cannot_become_zero_deaths(self):
        class BadCount(self.Game):
            def __init__(self, value): super().__init__(); self.value=value
            def get_game_variable(self, variable): return self.value if variable=='deaths' else 0.0
        with patch.object(candidate,'ProgressSample',side_effect=lambda *args:args):
            self.assertEqual(candidate._coherent_progress_sample(BadCount(0.0),self.Variables,75)[2],0)
            for value in (0.5,-0.5,False,float('nan'),float('inf')):
                with self.subTest(value=value),self.assertRaises(ValueError):
                    candidate._coherent_progress_sample(BadCount(value),self.Variables,75)

    def test_valid_finished_alive_and_non_timeout_proves_exit(self):
        with patch.object(candidate, 'ProgressSample', side_effect=lambda *args: args):
            self.assertTrue(candidate._coherent_progress_sample(self.Game(), self.Variables, 75)[-1])
            self.assertFalse(candidate._coherent_progress_sample(self.Game(timeout=True), self.Variables, 75)[-1])
            self.assertFalse(candidate._coherent_progress_sample(self.Game(dead=True), self.Variables, 75)[-1])

if __name__ == "__main__":
    unittest.main()
