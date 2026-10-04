import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import session_map01_v18 as candidate


def verified_release():
    return {
        "event": "input_release_transition", "operation": "up",
        "id": "program-1", "step": 3, "key": "d",
        "owner_id": "owner-1", "intent_token": "token-1",
        "owner_transition_verified": True,
        "owner_thread_keyup_verified": True,
        "owner_thread_keyup_verified_after_batch": True,
        "owner_identity_matches_after_batch": True,
        "intent_token_matches_after_batch": True,
        "owned_keycodes_after_batch": [],
        "release_call_returned_ns": 100,
        "owner_thread_keyup_receipt": {
            "event": "owner_explicit_keyup", "operation": "up",
            "owner_id": "owner-1", "key": "d", "intent_token": "token-1",
            "server_sync_completed": True,
        },
    }


class TailCompositionTests(unittest.TestCase):
    def test_verified_release_tail_runs_before_preserved_final_sample(self):
        events = []

        class Polling:
            def sample_tail(self, **kwargs):
                events.append("tail")
                self.arguments = kwargs
                return {"disposition": "CENSORED", "termination": "deadline",
                        "tail_samples": 4, "release_id": "program-1",
                        "release_step": 3, "release_key": "d"}

        with tempfile.TemporaryDirectory() as tmp:
            outcome = candidate.run_tail_then_final_sample(
                Polling(), tmp, verified_release(), lambda: events.append("final"))
            saved = json.loads((Path(tmp) / "scorer-post-release-tail.json").read_text())
        self.assertEqual(events, ["tail", "final"])
        self.assertEqual(outcome, saved)
        self.assertEqual(saved["tail_samples"], 4)
        self.assertFalse(saved["controller_visible"])
        self.assertFalse(saved["grants_input_authority"])

    def test_missing_or_unverified_release_skips_tail_but_runs_final_sample(self):
        for receipt in (None, {**verified_release(), "owner_transition_verified": False}):
            with self.subTest(receipt=receipt), tempfile.TemporaryDirectory() as tmp:
                events = []

                class Polling:
                    def sample_tail(self, **_kwargs):
                        events.append("tail")
                        raise AssertionError("unverified release reached scorer")

                outcome = candidate.run_tail_then_final_sample(
                    Polling(), tmp, receipt, lambda: events.append("final"))
                self.assertEqual(events, ["final"])
                self.assertEqual(outcome["termination"], "no_verified_release_receipt")
                self.assertEqual(outcome["tail_samples"], 0)

    def test_tail_error_is_recorded_and_final_sample_still_runs(self):
        events = []

        class Polling:
            def sample_tail(self, **_kwargs):
                events.append("tail")
                raise RuntimeError("tail unavailable")

        with tempfile.TemporaryDirectory() as tmp:
            result = candidate.run_tail_then_final_sample(
                Polling(), tmp, verified_release(), lambda: events.append("final"))
            saved = json.loads((Path(tmp) / "scorer-post-release-tail.json").read_text())
        self.assertEqual(events, ["tail", "final"])
        self.assertEqual(result, saved)
        self.assertEqual(saved["termination"], "tail_error")
        self.assertEqual(saved["error_type"], "RuntimeError")

    def test_capture_backend_only_retains_verified_release_rows(self):
        emitted = []
        holder = {}

        class Backend:
            def __init__(self, session, out, emit, signal_readers):
                self.emit = emit

        wrapped = candidate._capture_backend(Backend, holder)
        backend = wrapped(None, None, emitted.append, None)
        backend.emit({"event": "input_release_transition", "key": "d"})
        row = verified_release()
        backend.emit(row)
        self.assertEqual(holder["latest"], row)
        self.assertEqual(emitted, [{"event": "input_release_transition", "key": "d"}, row])

    def test_capture_backend_does_not_retain_unpublished_release(self):
        holder = {}

        class Backend:
            def __init__(self, session, out, emit, signal_readers):
                self.emit = emit

        def refuse(_row):
            raise OSError("release publication failed")

        backend = candidate._capture_backend(Backend, holder)(None, None, refuse, None)
        with self.assertRaisesRegex(OSError, "publication failed"):
            backend.emit(verified_release())
        self.assertEqual(holder, {})

    def test_main_composes_capture_backend_polling_and_tail_proxy(self):
        events = []
        receipts = []
        row = verified_release()

        class Backend:
            def __init__(self, session, out, emit, signal_readers):
                self.emit = emit

        class InnerGame:
            def init(self):
                events.append("game_init")

            def close(self):
                events.append("game_close")

        class Stream:
            def fileno(self):
                return 0

        def fake_previous_main():
            self.assertIsNot(candidate.previous._GameProxy, original_proxy)
            polling = candidate.previous.MainThreadScorerStdin(
                Stream(), lambda: None, lambda _row: None, sample_hz=35)
            proxy = candidate.previous._GameProxy(
                InnerGame(), lambda: events.append("final_sample"))
            backend = telemetry.Backend(None, None, lambda _row: None, None)
            backend.emit(row)
            proxy.init()
            proxy.close()
            return "session-returned"

        original_proxy = candidate.previous._GameProxy
        original_backend = Backend
        telemetry = types.ModuleType("doom_owner_thread_release_batch_backend_v1")
        telemetry.Backend = original_backend

        def tail_stub(polling, out, receipt, final_sample):
            self.assertTrue(callable(polling.sample_tail))
            receipts.append(receipt)
            events.append("tail")
            final_sample()

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "sources.json").write_text("{}", encoding="utf-8")
            with patch.object(candidate.previous, "_option", return_value=tmp), \
                    patch.object(candidate.previous, "main", side_effect=fake_previous_main), \
                    patch.object(candidate, "run_tail_then_final_sample", side_effect=tail_stub), \
                    patch.dict(sys.modules, {telemetry.__name__: telemetry}):
                self.assertEqual(candidate.main(), "session-returned")
            manifest = json.loads((Path(tmp) / "sources.json").read_text(encoding="utf-8"))
            manifest = {key.replace("\\", "/"): value for key, value in manifest.items()}
            self.assertIn("doom/session_map01_v18.py", manifest)
            self.assertIn("doom/map01_overlap_controller_v39.py", manifest)

        self.assertEqual(receipts, [row])
        self.assertEqual(events, ["game_init", "tail", "final_sample", "game_close"])
        self.assertIs(candidate.previous._GameProxy, original_proxy)
        self.assertIs(telemetry.Backend, original_backend)

    def test_main_preserves_session_and_provenance_failures(self):
        telemetry = types.ModuleType("doom_owner_thread_release_batch_backend_v1")
        telemetry.Backend = type("Backend", (), {})
        session_error = RuntimeError("session failed")
        provenance_error = OSError("manifest failed")
        original_proxy = candidate.previous._GameProxy
        original_polling = candidate.previous.MainThreadScorerStdin
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(candidate.previous, "_option", return_value=tmp), \
                    patch.object(candidate.previous, "main", side_effect=session_error), \
                    patch.object(candidate, "_record_source_manifest",
                                 side_effect=provenance_error), \
                    patch.dict(sys.modules, {telemetry.__name__: telemetry}):
                with self.assertRaises(BaseExceptionGroup) as raised:
                    candidate.main()
        self.assertIs(raised.exception.exceptions[0], session_error)
        self.assertIs(raised.exception.exceptions[1], provenance_error)
        self.assertIs(candidate.previous._GameProxy, original_proxy)
        self.assertIs(candidate.previous.MainThreadScorerStdin, original_polling)


if __name__ == "__main__":
    unittest.main()
