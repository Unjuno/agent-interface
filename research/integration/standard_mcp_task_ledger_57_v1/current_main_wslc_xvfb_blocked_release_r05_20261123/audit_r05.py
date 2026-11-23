#!/usr/bin/env python3
"""Strictly classify the frozen R05 WSLc raw evidence; never claim product PASS."""
import hashlib, json, re, sys
from pathlib import Path

packet = Path(__file__).resolve().parent
repo = packet.parents[3]
def need(condition, message):
    if not condition:
        raise RuntimeError(message)
def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

# Verify the exact runtime inputs used by the experiment.
for row in (packet / "SOURCE_SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
    digest, rel = row.split(None, 1)
    actual = hashlib.sha256((repo / rel.strip().replace("\\", "/")).read_bytes()).hexdigest()
    need(actual == digest, f"source hash mismatch: {rel}")

normal = packet / "runs/normal"
optimized = packet / "runs/optimized"
n = load(normal / "result.json")
o = load(optimized / "result.json")
need((normal / "exit-code.txt").read_text().strip() == "0", "normal unittest process did not exit 0")
need("Ran 1 test" in (normal / "test.log").read_text() and "OK" in (normal / "test.log").read_text(), "normal unittest log incomplete")
need((normal / "container.exit-code.txt").read_text().strip() == "2", "normal wrapper defect not preserved")
need(n["cancel"]["owner_client_disconnect"]["status"] == "disconnected", "normal XRes disconnect was not observed")
need(n["cancel"]["owner_release_attempt"]["status"] == "readback_verified", "normal owner release worker receipt missing")
need(n["independent_release_readback"]["neutral"] is True, "normal independent release readback not neutral")
need(n["independent_task_oracle"]["task_success"] is False, "normal old-task oracle failure missing")
need(n["independent_task_oracle"]["measurements"]["initial_effect_count"] == [1], "normal initial effect count unexpected")
need(n["independent_task_oracle"]["measurements"]["final_effect_count"] == [9], "normal final effect count unexpected")
need(n["late_request_horizon_readback"]["late_keypress_a_observed"] is True, "normal late A event missing")
need(n["fresh_session_recovery"]["task_oracle"]["task_success"] is True, "fresh-generation task oracle failed")
need(n["fresh_session_recovery"]["old_cancellation_fence"]["cleanup_status"] == "UNKNOWN", "old UNKNOWN fence not preserved")
need(n["fresh_session_recovery"]["late_old_keypress_after_new_session"] is False, "old task contaminated fresh session")
need(all(v is False for v in n["final_cleanup"]["keys_down"].values()), "normal final cleanup keys not all up")

need((optimized / "exit-code.txt").read_text().strip() == "1", "optimized unittest did not preserve failure exit")
need("FAILED (failures=1)" in (optimized / "test.log").read_text(), "optimized unittest failure missing")
need(o["status"] == "FAIL", "optimized result status missing")
d = o["cancel"]["owner_client_disconnect"]
need(d["status"] == "unknown" and d["reason"] == "supervision_timeout", "optimized XRes timeout not preserved")
need(490 <= d["elapsed_ms"] <= 530, f"optimized timeout outside expected 0.5s envelope: {d['elapsed_ms']}")
need(o["cancel"]["owner_release_attempt"]["status"] == "not_attempted", "optimized path unexpectedly attempted owner release")
need(all(v is False for v in o["final_cleanup"]["keys_down"].values()), "optimized final cleanup keys not all up")

report = {
  "status": "SCOPED_EVIDENCE_CAPTURED_NOT_PRODUCT_PASS",
  "source_revision": "26152e5aaebf678d19f2e7431f57b7012a0064b1",
  "normal": {"unittest_exit": 0, "outer_wrapper_exit": 2, "xres": "disconnected", "old_task_oracle": False, "effect_count": "1 -> 9", "late_a": True, "fresh_task_oracle": True, "fresh_contamination": False, "release_readback_neutral": True, "runtime_cancel_release_confirmed": n["cancel"]["release_confirmed"]},
  "optimized": {"unittest_exit": 1, "xres": "unknown/supervision_timeout", "elapsed_ms": d["elapsed_ms"], "owner_release_attempt": "not_attempted", "final_keys_up": True},
  "conclusion": "The 0.5s XRes budget completed normally but exceeded in this optimized WSLc sample. Old-generation task completion remains untrusted; delayed repeated A effects occurred despite neutral release/readback. A fresh generation completed one independently scored task without old-input contamination while the old fence stayed UNKNOWN.",
  "limits": ["one normal and one optimized sample", "synthetic Xvfb only", "not MAP01/live GUI", "not matched economics or reliability rate", "not research-preview acceptance", "WSLc memory cap warning: swap limit unavailable"]
}
print(json.dumps(report, indent=2, sort_keys=True))
