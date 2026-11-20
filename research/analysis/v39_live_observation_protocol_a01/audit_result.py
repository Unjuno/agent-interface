"""Independently audit saved A01 loopback protocol outcomes."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_IMAGE = "0e6b6570944c3e0c60ca3eff5e84bc9371187cd8cea6a7d237e66cc06645483c"

def verify_checksums() -> None:
    sums = ROOT / "SHA256SUMS"
    require(sums.is_file(), "SHA256SUMS missing")
    for line in sums.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = ROOT / relative
        require(path.is_file(), f"checksum input missing: {relative}")
        actual = __import__("hashlib").sha256(path.read_bytes()).hexdigest()
        require(actual == expected, f"SHA-256 mismatch: {relative}")

def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(f"FAIL: {message}")

def load(name: str) -> dict:
    return json.loads((ROOT / "results" / name).read_text(encoding="utf-8"))

verify_checksums()
auto = load("a01-auto.json")
low = load("a01-low-control.json")
for label, row in (("auto", auto), ("low", low)):
    require(row.get("cli_version") == "codex-cli 0.160.0", f"{label}: unexpected CLI version")
    require(row.get("loopback_only") is True and row.get("temporary_codex_home") is True, f"{label}: isolation markers absent")
    require(row.get("initialization_ok") is True and row.get("thread_started") is True, f"{label}: protocol setup failed")
    require(row.get("external_turn_accepted") is True and row.get("turn_completed") is True, f"{label}: turn did not complete")
    require(row.get("initial_turn_id") and row.get("external_turn_id"), f"{label}: turn ID missing from a protocol reply")
    require(row["same_turn_id"] is (row["initial_turn_id"] == row["external_turn_id"]), f"{label}: same-turn flag does not match IDs")
    require(row["initial_turn_id"] == row["external_turn_id"], f"{label}: external observation left the active turn")
    require(row.get("mock_request_count") == 2, f"{label}: expected two mock requests")
    require(row.get("image_sha256") == EXPECTED_IMAGE == row.get("frame_sha256_expected"), f"{label}: wrong source image")
    require(row.get("text_delivered") is True, f"{label}: observation text absent")
    require(not row.get("server_errors"), f"{label}: mock server errors")
require(auto.get("image_detail") == "auto" and auto.get("image_delivered") is True and auto.get("input_image_count") == 1, "auto: expected exactly one image delivery")
require(low.get("image_detail") == "low" and low.get("image_delivered") is False and low.get("input_image_count") == 0, "low: negative image-delivery control failed")
result = {"status":"PASS_SCOPED_LOOPBACK_PROTOCOL_AUDIT", "cli_version":auto["cli_version"], "same_turn_ids":True, "auto":{"text_delivered":True,"image_delivered":True,"input_image_count":1}, "low":{"text_delivered":True,"image_delivered":False,"input_image_count":0}, "source_image_sha256":EXPECTED_IMAGE, "scope":"Mock Responses transport and App Server turn-ID continuity only; no model inference, visual comprehension, V39 runtime integration, game, GUI, native input, or live allocation."}
print(json.dumps(result, indent=2))

