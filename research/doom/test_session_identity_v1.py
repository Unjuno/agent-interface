import unittest
import json
import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

from session_identity_v1 import (bind_session_identity,
                                 session_bound_event_sidecar,
                                 SessionBoundEventSidecar,
                                 emit_event_row)
import session_map01_v16 as session_v16


class SessionIdentityTests(unittest.TestCase):
    def test_default_stream_is_unchanged(self):
        row = {"event": "input_admission", "key": "w"}
        self.assertIs(bind_session_identity(row, None), row)
        self.assertEqual(row, {"event": "input_admission", "key": "w"})

    def test_opt_in_identity_is_added_without_mutating_source(self):
        row = {"event": "input_admission", "key": "w"}
        actual = bind_session_identity(row, "session-a")
        self.assertEqual(actual, {**row, "session_id": "session-a"})
        self.assertNotIn("session_id", row)

    def test_matching_existing_identity_is_idempotent(self):
        row = {"event": "input_release_transition", "session_id": "session-a"}
        self.assertEqual(bind_session_identity(row, "session-a"), row)

    def test_conflicting_existing_identity_fails_closed(self):
        row = {"event": "owner_explicit_keyup", "session_id": "session-b"}
        with self.assertRaisesRegex(ValueError, "session identity mismatch"):
            bind_session_identity(row, "session-a")

    def test_invalid_session_identity_is_rejected(self):
        for session_id in ("", "  ", 1, None):
            if session_id is None:
                continue  # None explicitly selects unchanged legacy behavior.
            with self.subTest(session_id=session_id):
                with self.assertRaisesRegex(ValueError, "nonempty string"):
                    bind_session_identity({}, session_id)

    def test_private_event_sidecar_links_without_mutating_controller_row(self):
        row = {"event": "input_admission", "key": "w"}
        source_line = json.dumps(row)
        bound = session_bound_event_sidecar(row, "session-a", source_line, 3)
        self.assertEqual(bound["session_id"], "session-a")
        self.assertEqual(bound["source_event_ordinal"], 3)
        self.assertEqual(bound["source_event_sha256"], __import__("hashlib").sha256(
            source_line.encode("utf-8")).hexdigest())
        self.assertNotIn("session_id", row)
        self.assertIsNone(session_bound_event_sidecar(row, None, source_line, 3))

    def test_serialized_controller_row_is_unchanged_when_identity_is_opted_in(self):
        row = {"event": "input_admission", "key": "w", "emit_ns": 42}
        expected = json.dumps(row)
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            sidecar = SessionBoundEventSidecar(out, "session-a")
            sidecar.record(row, expected, 1)
            sidecar.finalize()
            self.assertEqual(json.dumps(row), expected)
            self.assertNotIn("session_id", json.loads(expected))
            bound = json.loads((out / "session-bound-events.jsonl").read_text())
        self.assertIsInstance(bound, dict)
        self.assertEqual(bound["source_event_sha256"], __import__("hashlib").sha256(
            expected.encode("utf-8")).hexdigest())

    def test_sidecar_write_failure_does_not_escape_and_marks_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out / "session-bound-events.jsonl").mkdir()
            sidecar = SessionBoundEventSidecar(out, "session-a")
            row = {"event": "cancel_requested", "id": "plan-1"}
            encoded = json.dumps(row)

            sidecar.record(row, encoded, 1)
            sidecar.record(row, encoded, 2)
            status = sidecar.finalize()

            self.assertEqual(status["event_count"], 2)
            self.assertEqual(status["records_written"], 0)
            self.assertFalse(status["complete"])
            self.assertEqual(status["failure"], {
                "first_failed_ordinal": 1,
                "error_type": "IsADirectoryError",
            })
            saved = json.loads((out / "session-bound-events-status.json").read_text())
            self.assertEqual(saved, status)

    def test_sidecar_write_failure_preserves_legacy_event_sinks(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out / "session-bound-events.jsonl").mkdir()
            sidecar = SessionBoundEventSidecar(out, "session-a")
            stdout_rows = []
            row = {"event": "cancel_requested", "id": "plan-1", "emit_ns": 42}
            expected = json.dumps(row)

            encoded = emit_event_row(out, row, 1, sidecar, stdout_rows.append)

            self.assertEqual(encoded, expected)
            self.assertEqual(stdout_rows, [expected])
            self.assertEqual((out / "events.jsonl").read_text(), expected + "\n")
            self.assertEqual((out / "delivered.jsonl").read_text(), expected + "\n")
            self.assertFalse(sidecar.finalize()["complete"])

    def test_complete_sidecar_status_counts_all_serialized_events(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            sidecar = SessionBoundEventSidecar(out, "session-a")
            rows = [{"event": "input_admission"}, {"event": "terminal"}]
            for ordinal, row in enumerate(rows, 1):
                sidecar.record(row, json.dumps(row), ordinal)
            status = sidecar.finalize()
            self.assertTrue(status["complete"])
            self.assertEqual(status["event_count"], 2)
            self.assertEqual(status["records_written"], 2)

    def test_private_event_sidecar_rejects_invalid_ordinal(self):
        for ordinal in (0, -1, True, 1.5):
            with self.subTest(ordinal=ordinal), self.assertRaises(ValueError):
                session_bound_event_sidecar({}, "session-a", "{}", ordinal)

    def test_v16_binds_owner_event_identity_and_restores_environment(self):
        identity_key = "AGENT_INTERFACE_SESSION_ID"
        run_id = str(uuid.UUID("6c9a2084-71b1-4777-8f3a-4f85e6014b17"))
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)

            def session_main():
                self.assertEqual(os.environ.get(identity_key), run_id)
                (out / "sources.json").write_text("{}", encoding="utf-8")

            with patch.dict(os.environ, {identity_key: "outer-session"}):
                with patch.object(session_v16.previous, "_option", return_value=directory), \
                     patch.object(session_v16.uuid, "uuid4", return_value=uuid.UUID(run_id)), \
                     patch.object(session_v16.previous, "main", side_effect=session_main):
                    session_v16.main()
                self.assertEqual(os.environ[identity_key], "outer-session")

            sources = json.loads((out / "sources.json").read_text(encoding="utf-8"))
            for name in ("session_map01_v12.py", "session_identity_v1.py",
                         "session_map01_v16.py", "acknowledged_scorer_v1.py"):
                self.assertIn("doom/" + name, sources)

    def test_v16_restores_environment_after_session_failure(self):
        identity_key = "AGENT_INTERFACE_SESSION_ID"
        run_id = uuid.UUID("89c0ec2a-d6e0-4e31-a8d7-7db12d78e190")
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {identity_key: "outer-session"}):
                with patch.object(session_v16.previous, "_option", return_value=directory), \
                     patch.object(session_v16.uuid, "uuid4", return_value=run_id), \
                     patch.object(session_v16.previous, "main", side_effect=RuntimeError("session failed")):
                    with self.assertRaisesRegex(RuntimeError, "session failed"):
                        session_v16.main()
                self.assertEqual(os.environ[identity_key], "outer-session")

    def test_v16_removes_generated_identity_after_session(self):
        identity_key = "AGENT_INTERFACE_SESSION_ID"
        run_id = uuid.UUID("b26c2a71-a9c0-4c8e-b926-ceef789c6f46")
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ):
            os.environ.pop(identity_key, None)
            with patch.object(session_v16.previous, "_option", return_value=directory), \
                 patch.object(session_v16.uuid, "uuid4", return_value=run_id), \
                 patch.object(session_v16.previous, "main", return_value=None):
                session_v16.main()
            self.assertNotIn(identity_key, os.environ)


if __name__ == "__main__":
    unittest.main()
