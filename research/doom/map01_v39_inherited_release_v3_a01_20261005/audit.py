"""Read-only audit of A01 source pins and retained raw result."""
import hashlib
import json
import subprocess
from pathlib import Path

PKG = Path(__file__).resolve().parent
ROOT = PKG.parents[2]
lock = json.loads((PKG / "SOURCE_LOCK.json").read_text())
base = lock["base_main_sha"]
for item in lock["files"]:
    path = PKG / item["path"]
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == item["sha256"], item["path"]
    blob = subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()
    assert blob == item["git_blob"], item["path"]
    source = subprocess.check_output(["git", "show", f"{item['source_commit']}:{item['repo_path']}"])
    assert source == data, item["repo_path"]
    if item.get("runtime_dependency"):
        runtime_path = ROOT / item["repo_path"]
        assert runtime_path.read_bytes() == data, item["repo_path"]

result_path = PKG / "results" / "RESULT.json"
result_bytes = result_path.read_bytes()
result = json.loads(result_bytes)
stdout = (PKG / "results" / "stdout.txt").read_text().strip()
assert json.loads(stdout) == result
assert (PKG / "results" / "exit_code.txt").read_text().strip() == "0"
assert result["result"] == "PASS_SCOPED_FINAL_DRAIN"
assert lock["candidate_commits"]["baseline"] == "8ed40fcbc52a9ffd2da1fa14b9b9b2a22f4111a3"
assert lock["candidate_commits"]["a08"] == "adfa5c9ccbf2ca4f82b85b164f0439740f63cc80"
assert result["candidate_commits"] == lock["candidate_commits"]
control, candidate = result["control"], result["candidate"]
assert control["contextual_up_receipt_count"] == 0
assert candidate["contextual_up_receipt_count"] == 1
for arm in (control, candidate):
    assert arm["inherited_release_method_owner"] == "session_v5.Backend"
    assert arm["terminal_status"] == "expired"
    assert arm["terminal_release_verified"] is True
    assert arm["owner_release_record_count"] == 2
    assert arm["owner_release_reasons"] == ["expired", "release"]
    assert arm["physical_state_empty"] is True
    assert arm["bridge_ledger_empty"] is True
assert candidate["event_order"].index("input_release_measurement") < candidate["event_order"].index("terminal")
assert control["release_method_owner"] == "session_v5.Backend"
assert candidate["release_method_owner"] == "bridge_v2_candidate.Backend"
assert candidate["candidate_final_drain_implementation"] is True
assert control["candidate_final_drain_implementation"] is False
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
        if (path.is_file() and path != manifest_path and path.name != "AUDIT.json"
            and "__pycache__" not in path.parts and path.suffix != ".pyc")
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
