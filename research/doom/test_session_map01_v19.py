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
        state_seen = {}

        def run_previous():
            wrapper = session_module.Backend
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
                    }):
                self.assertEqual(candidate.main(), "ok")
            self.assertEqual(state_seen["candidate"][0]["event"], "input_admission")
            self.assertEqual(state_seen["candidate"][1]["event"], "input_release_measurement")
            self.assertEqual(state_seen["candidate"][2], [])
        self.assertIs(session_module.Backend, BaseBackend)


if __name__ == "__main__":
    unittest.main(verbosity=2)
