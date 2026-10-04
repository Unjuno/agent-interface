"""Independent read-only audit of the saved timeout result and freeze hashes."""
import hashlib
import json
from pathlib import Path

PKG = Path(__file__).resolve().parent
freeze = json.loads((PKG / "FREEZE.json").read_text(encoding="utf-8"))
for item in freeze["locked_files"]:
    data = (PKG / item["path"]).read_bytes()
    assert len(data) == item["bytes"], f"byte-count mismatch: {item['path']}"
    assert hashlib.sha256(data).hexdigest() == item["sha256"], f"hash mismatch: {item['path']}"

provenance = json.loads((PKG / "SOURCE_PROVENANCE.json").read_text(encoding="utf-8"))
assert provenance["all_match"] is True
assert all(item["matches"] is True for item in provenance["comparisons"])

result_bytes = (PKG / "results" / "RESULT.json").read_bytes()
result = json.loads(result_bytes)
stdout = (PKG / "TOOL_STDOUT_CAPTURE.txt").read_text(encoding="utf-8")
assert stdout == json.dumps(result, sort_keys=True) + "\n", "captured stdout differs from saved result"
timing = result["timing"]
elapsed = timing["barrier_elapsed_ns"]
assert 1_800_000_000 <= elapsed <= 2_500_000_000, "owner-call timeout outside frozen bound"
assert timing["call_error"] == "RuntimeError('input owner reply timed out; cleanup unverified')"
terminal = result["at_terminal"]
assert terminal == {
    "terminal_status": "failed",
    "release_verified": False,
    "bridge_held": ["F8"],
    "owner_release_records": 0,
    "physical": [],
    "up_receipts": 0,
}
after = result["after_owner_stop"]
assert after == {
    "bridge_held": ["F8"],
    "owner_release_records": 3,
    "owner_stopped": True,
    "physical": [],
    "up_receipts": 0,
}
manifest_lines = (PKG / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
manifest = {}
for line in manifest_lines:
    digest, rel = line.split("  ", 1)
    assert rel not in manifest, f"duplicate manifest path: {rel}"
    manifest[rel] = digest
actual_files = {
    path.relative_to(PKG).as_posix()
    for path in PKG.rglob("*")
    if path.is_file() and "__pycache__" not in path.parts and path.name != "SHA256SUMS.txt"
}
assert set(manifest) == actual_files, "manifest inventory differs from package files"
for rel, digest in manifest.items():
    assert hashlib.sha256((PKG / rel).read_bytes()).hexdigest() == digest, f"manifest mismatch: {rel}"
print(json.dumps({
    "disposition": "FAIL_BARRIER_TIMEOUT_LEAVES_BRIDGE_STALE_AFTER_OWNER_STOP",
    "frozen_owner_call_timeout_ns": elapsed,
    "failed_terminal_before_gate_open": True,
    "eventual_fake_physical_state_empty": True,
    "bridge_up_receipt_count_zero": True,
    "bridge_stale_key": "F8",
    "audit_scope": "saved candidate summary and frozen source/result bytes only; no candidate rerun or independent physical-input audit",
    "source_provenance_comparisons": len(provenance["comparisons"]),
    "manifest_files": len(manifest),
}, sort_keys=True))
