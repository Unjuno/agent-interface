"""Read-only audit of A01 source pins and retained raw result."""
import hashlib
import json
import subprocess
from pathlib import Path

PKG = Path(__file__).resolve().parent
lock = json.loads((PKG / "SOURCE_LOCK.json").read_text())
base = lock["base_main_sha"]
for item in lock["files"]:
    path = PKG / item["path"]
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == item["sha256"], item["path"]
    blob = subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()
    assert blob == item["git_blob"], item["path"]
    source_path = "research/live_control/" + path.name
    source = subprocess.check_output(["git", "show", f"{base}:{source_path}"])
    assert source == data, source_path

result_path = PKG / "results" / "RESULT.json"
result_bytes = result_path.read_bytes()
result = json.loads(result_bytes)
stdout = (PKG / "results" / "stdout.txt").read_text().strip()
assert json.loads(stdout) == result
assert (PKG / "results" / "exit_code.txt").read_text().strip() == "0"
assert result["result"] == "PASS_SCOPED_FINAL_DRAIN"
control, candidate = result["control"], result["candidate"]
assert control["contextual_up_receipt_count"] == 0
assert candidate["contextual_up_receipt_count"] == 1
for arm in (control, candidate):
    assert arm["release_method_owner"] == "session_v5.Backend"
    assert arm["terminal_status"] == "expired"
    assert arm["terminal_release_verified"] is True
    assert arm["owner_release_record_count"] == 2
    assert arm["owner_release_reasons"] == ["expired", "release"]
    assert arm["physical_state_empty"] is True
    assert arm["bridge_ledger_empty"] is True
assert candidate["event_order"].index("input_release_measurement") < candidate["event_order"].index("terminal")
assert control["event_order"].count("input_release_measurement") == 0
assert candidate["event_order"].count("input_release_measurement") == 1
manifest_path = PKG / "SHA256SUMS.txt"
if manifest_path.exists():
    expected = {}
    for line in manifest_path.read_text().splitlines():
        digest, relative = line.split("  ", 1)
        expected[relative] = digest
    actual = {
        str(path.relative_to(PKG)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in PKG.rglob("*")
        if path.is_file() and path != manifest_path and path.name != "AUDIT.json"
    }
    assert actual == expected, {"missing_or_changed": sorted(set(expected.items()) ^ set(actual.items()))}
report = {
    "audit": "PASS",
    "base_main_sha": base,
    "source_files_verified": len(lock["files"]),
    "result_sha256": hashlib.sha256(result_bytes).hexdigest(),
    "package_files_verified": len(expected) if manifest_path.exists() else None,
    "source_execution": False,
}
(PKG / "results" / "AUDIT.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, sort_keys=True))
