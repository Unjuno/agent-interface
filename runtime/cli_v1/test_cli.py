from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from runtime.cli_v1.api import dispatch, doctor


class FakeSession:
    def __init__(self):
        self.calls = []
    def dispatch(self, program, *, current_observation_seq, current_binding_revision):
        self.calls.append((program, current_observation_seq, current_binding_revision))
        return {"status": "completed", "echo_program": program}


class ApiTests(unittest.TestCase):
    def test_doctor_is_side_effect_free(self):
        row = doctor(platform="win32", environ={})
        self.assertEqual(row["selection"]["backend_id"], "win32-v1")
        self.assertFalse(row["side_effect_authority"])

    def test_dispatch_preserves_program_and_freshness_inputs(self):
        session = FakeSession()
        program = {"schema": "agent-interface/program-v1", "source": {"observation_seq": 7, "binding_revision": 3}}
        with mock.patch("runtime.cli_v1.api.open_session", return_value=session):
            row = dispatch(program, {"fixture": 1}, current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(row["status"], "returned")
        self.assertIs(session.calls[0][0], program)
        self.assertEqual(session.calls[0][1:], (7, 3))

    def test_invalid_targets_fail_before_backend_construction(self):
        row = dispatch({}, {}, current_observation_seq=0, current_binding_revision=0)
        self.assertEqual(row["status"], "backend_unavailable")

    def test_invalid_sequence_and_revision_fail_closed(self):
        row = dispatch({}, {"x": 1}, current_observation_seq=-1, current_binding_revision=0)
        self.assertEqual(row["error"], "INVALID_OBSERVATION_SEQ")
        row = dispatch({}, {"x": 1}, current_observation_seq=0, current_binding_revision=-1)
        self.assertEqual(row["error"], "INVALID_BINDING_REVISION")


class CliTests(unittest.TestCase):
    def test_doctor_outputs_one_json_record(self):
        proc = subprocess.run([sys.executable, "-m", "runtime.cli_v1", "doctor"], capture_output=True, text=True, check=True)
        rows = proc.stdout.strip().splitlines()
        self.assertEqual(len(rows), 1)
        data = json.loads(rows[0])
        self.assertEqual(data["schema"], "agent-interface/runtime-doctor-v1")
        self.assertFalse(data["side_effect_authority"])

    def test_malformed_json_is_nonzero_and_json_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bad = root / "bad.json"; bad.write_text("{bad", encoding="utf-8")
            targets = root / "targets.json"; targets.write_text('{"fixture":1}', encoding="utf-8")
            proc = subprocess.run([
                sys.executable, "-m", "runtime.cli_v1", "dispatch",
                "--program", str(bad), "--targets", str(targets),
                "--current-observation-seq", "0", "--current-binding-revision", "0",
            ], capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(len(proc.stdout.strip().splitlines()), 1)
            self.assertEqual(json.loads(proc.stdout)["status"], "invalid_request")


if __name__ == "__main__":
    unittest.main()
