"""Independent synthetic adversaries for no-input epoch custody."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from audit_epoch import validate, verify_files, validate_launch


def fixture():
    freeze = {"image_id": "pinned", "source_sha256": {
        "readiness_once.py": "a", "probe_app.py": "b", "probe_epoch.py": "c"}}
    raw = {"schema": "5260-a03-epoch-construction01-v1",
        "allocation": "5260-a03-wslc-no-input-construction01-20261003",
        "status": "CONSTRUCTION_ONLY_NO_INPUT", "image_id": "pinned",
        "source_sha256": freeze["source_sha256"], "xvfb_exit": 0, "openbox_exit": 0,
        "rows": []}
    schedule = [("LEGACY", 0), ("FIXED", 0), ("FIXED", 1), ("LEGACY", 1),
                ("LEGACY", 2), ("FIXED", 2), ("FIXED", 3), ("LEGACY", 3)]
    for index, (mode, replicate) in enumerate(schedule):
        ready = {"epoch": 1, "ready_ns": 30, "mapped": True, "root_id": 10,
            "target_id": 11, "root_width": 520, "root_height": 250,
            "target_width": 366, "target_height": 23}
        app = {"schema": "5260-a03-no-input-app-v1", "mode": mode, "pid": index + 20,
            "scheduled": 1, "focus_callbacks": 1, "finalizations": 1,
            "input_events": 0, "target_text": "", "decoy_text": "", "ended_ns": 40,
            "events": [{"kind": "Map", "ns": 10}, {"kind": "Configure", "ns": 11},
                       {"kind": "schedule", "ns": 20},
                       {"kind": "decoy_focus_callback", "ns": 25}],
            "first_ready": ready, "last_ready": ready}
        raw["rows"].append({"index": index, "mode": mode, "replicate": replicate,
            "pid": app["pid"], "exit": 0, "app": app, "first_observer_read": ready,
            "final_ready_file": ready, "stdout": json.dumps(app) + "\n", "stderr": ""})
    return raw, freeze


class EpochAuditTests(unittest.TestCase):
    def test_launch_custody_rejects_changed_argv_exit_stream_and_time(self):
        freeze = {"command": ["wslc", "run", "owned"]}
        attempt = {"argv": freeze["command"], "started_utc": "2026-10-03T13:30:18+00:00"}
        blobs = {"attempt.json": json.dumps(attempt).encode(),
                 "stdout.bin": b'{"rows":8,"input_events":0}\n', "stderr.bin": b"warning\n"}
        receipt = {**attempt, "finished_utc": "2026-10-03T13:30:31+00:00",
                   "wall_seconds": 13, "exit_code": 0, "launch_error": None,
                   "output_sha256": {n: hashlib.sha256(b).hexdigest() for n, b in blobs.items()}}
        self.assertEqual(validate_launch(attempt, receipt, freeze, blobs), [])
        for change in ({"argv": ["other"]}, {"exit_code": 1},
                       {"finished_utc": "2026-10-03T13:00:00+00:00"}):
            self.assertTrue(validate_launch(attempt, {**receipt, **change}, freeze, blobs))
        self.assertTrue(validate_launch(attempt, receipt, freeze, {**blobs, "stderr.bin": b""}))

    def test_literal_accepts_without_requiring_legacy_failure(self):
        raw, freeze = fixture()
        self.assertEqual(validate(raw, freeze), [])

    def reject(self, mutate):
        raw, freeze = fixture()
        mutate(raw)
        for row in raw["rows"]:
            row["stdout"] = json.dumps(row["app"]) + "\n"
        self.assertTrue(validate(raw, freeze))

    def test_missing_row(self):
        self.reject(lambda r: r["rows"].pop())

    def test_source_and_image_drift(self):
        self.reject(lambda r: r.update(image_id="other"))
        self.reject(lambda r: r.update(source_sha256={}))

    def test_wrong_pid(self):
        self.reject(lambda r: r["rows"][1].update(pid=20))

    def test_nonzero_input(self):
        self.reject(lambda r: r["rows"][1]["app"].update(input_events=1))

    def test_fixed_epoch_overwrite(self):
        self.reject(lambda r: r["rows"][1].update(
            final_ready_file={**r["rows"][1]["final_ready_file"], "ready_ns": 31}))

    def test_counter_without_event(self):
        self.reject(lambda r: r["rows"][1]["app"].update(scheduled=2))

    def test_wrong_geometry_and_clock(self):
        self.reject(lambda r: r["rows"][1].update(first_observer_read={
            **r["rows"][1]["first_observer_read"], "mapped": False}))
        self.reject(lambda r: r["rows"][1]["app"].update(ended_ns=1))

    def test_exit_failure(self):
        self.reject(lambda r: r["rows"][1].update(exit=1))

    def test_cross_file_changes(self):
        raw, _ = fixture()
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            for row in raw["rows"]:
                directory = out / f"row-{row['index']:02d}"
                directory.mkdir()
                (directory / "stdout.bin").write_bytes(row["stdout"].encode())
                (directory / "stderr.bin").write_bytes(row["stderr"].encode())
                (directory / "ready.json").write_text(json.dumps(row["final_ready_file"]))
                (directory / "app_result.json").write_text(json.dumps(row["app"]))
            self.assertEqual(verify_files(raw, out), [])
            for name in ("stdout.bin", "stderr.bin", "ready.json", "app_result.json"):
                path = out / "row-01" / name
                first = path.read_bytes()
                path.write_bytes(b"{}")
                self.assertTrue(verify_files(raw, out), name)
                path.write_bytes(first)


if __name__ == "__main__":
    unittest.main()
