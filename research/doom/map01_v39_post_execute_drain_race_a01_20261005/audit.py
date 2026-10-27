import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
result = json.loads((root / "RESULT.json").read_text())
raw = json.loads((root / "RAW_RUN_R02.json").read_text())
lock = json.loads((root / "SOURCE_LOCK.json").read_text())
assert result["records_at_bridge_drain"] == 0
assert result["release_rows_at_bridge_drain"] == 0
assert result["bridge_held_at_drain"] == ["F8"]
assert result["owner_cleanup_reasons"] == ["expired"]
assert result["owner_cleanup_release_rows"] == 1
assert result["terminal_status"] == "expired"
assert result["terminal_release_verified"] is True
assert result["release_rows_published"] == 0
assert result["owner_keys_after_terminal"] == []
assert result["fake_physical_keys_after_terminal"] == []
assert result["bridge_held_after_terminal"] == ["F8"]
assert result["cleanup_record_cursor"] == 0
assert result["event_names"] == ["accepted", "step_started", "input_admission", "terminal"]
for key in (
    "records_at_bridge_drain", "release_rows_at_bridge_drain", "bridge_held_at_drain",
    "event_names", "terminal_status", "terminal_release_verified", "release_rows_published",
    "owner_cleanup_reasons", "owner_cleanup_release_rows", "owner_keys_after_terminal",
    "fake_physical_keys_after_terminal", "bridge_held_after_terminal", "cleanup_record_cursor",
):
    assert result[key] == raw[key], key
assert raw["terminal_event"]["release"]["verified"] is True
assert hashlib.sha256((root / "RAW_RUN_R02.json").read_bytes()).hexdigest() == lock["raw_run_r02_sha256"]
assert hashlib.sha256((root / "probe.py").read_bytes()).hexdigest() == lock["probe_sha256"]
for relative, metadata in lock["files"].items():
    digest = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    assert metadata["sha256"] == digest, (relative, digest)
print("PASS raw-only: race observations and all vendored-source SHA256 values match")
