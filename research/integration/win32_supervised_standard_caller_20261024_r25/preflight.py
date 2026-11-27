"""Input-free source, packet, and R24 predecessor integrity check."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

PACKET = Path(__file__).resolve().parent
ROOT = PACKET.parents[2]
CONDITIONS = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
PRED = CONDITIONS["predecessor"]
result = {"schema": "win32-supervised-standard-caller-r25-preflight-v1",
          "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
          "native_input_sent": False, "checks": {}}
try:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                      text=True).strip()
    result["source_commit"] = commit
    result["checks"]["frozen_commit"] = commit == CONDITIONS["source_commit"]
    result["checks"]["tracked_tree_clean"] = (
        subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=ROOT).returncode == 0
        and subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0)
    source_hashes = {}
    for relative, expected in CONDITIONS["source_sha256"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        source_hashes[relative] = actual
        if actual != expected:
            raise RuntimeError(f"source hash mismatch: {relative}")
    result["source_sha256"] = source_hashes
    result["checks"]["frozen_source_hashes"] = True
    packet_hashes = {}
    for relative, expected in CONDITIONS["frozen_files"].items():
        actual = hashlib.sha256((PACKET / relative).read_bytes()).hexdigest()
        packet_hashes[relative] = actual
        if actual != expected:
            raise RuntimeError(f"frozen packet hash mismatch: {relative}")
    result["frozen_packet_hashes"] = packet_hashes
    result["checks"]["frozen_packet_hashes"] = True

    raw_path = ROOT / PRED["raw_path"]
    report_path = ROOT / PRED["report_path"]
    audit_path = ROOT / PRED["followup_audit_path"]
    actual_hashes = {"raw": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                     "report": hashlib.sha256(report_path.read_bytes()).hexdigest(),
                     "followup_audit": hashlib.sha256(audit_path.read_bytes()).hexdigest()}
    result["predecessor_hashes"] = actual_hashes
    expected_hashes = {"raw": PRED["raw_sha256"], "report": PRED["report_sha256"],
                       "followup_audit": PRED["followup_audit_sha256"]}
    result["checks"]["predecessor_hashes_match"] = actual_hashes == expected_hashes
    if actual_hashes != expected_hashes:
        raise RuntimeError("R24 predecessor receipt hash mismatch")
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    followup = json.loads(audit_path.read_text(encoding="utf-8"))
    action = report["supervision"]["action"]
    custody = action["completion_custody"]
    receipt = custody["completion_release_receipt"]
    result["predecessor_semantics"] = {
        "formal_outcome_fail_unknown": raw.get("status") == "FAIL_OR_UNKNOWN",
        "public_pending_and_close_busy": (
            raw.get("public_response", {}).get("status") == "pending"
            and raw.get("public_close", {}).get("response", {}).get("status") == "busy"),
        "persisted_dispatch_completed": (
            report.get("result", {}).get("status") == "completed"
            and action.get("status") == "completed"),
        "release_verified": (
            action.get("release_confirmed") is True and receipt.get("verified") is True
            and receipt.get("keys_down") == [] and receipt.get("buttons_down") == []
            and receipt.get("keys_unknown") == [] and receipt.get("buttons_unknown") == []),
        "independent_effect_and_cleanup": (
            raw.get("oracle", {}).get("task_pass") is True
            and raw.get("fixture_exit_code") == 0
            and raw.get("foreground_restore", {}).get("observed_hwnd")
                == raw.get("previous_foreground_hwnd")),
        "followup_audit_classification": (
            followup.get("classification") ==
            "POST_DISPATCH_EFFECT_AND_RELEASE_VERIFIED_BUT_PUBLIC_PENDING_AND_CLOSE_RELEASE_UNCONFIRMED"),
    }
    result["checks"]["predecessor_semantics"] = all(result["predecessor_semantics"].values())
    if not result["checks"]["predecessor_semantics"]:
        raise RuntimeError("R24 predecessor facts no longer match the recorded boundary")
    result["predecessor_generation"] = raw["observed_target_generation"]
    if sys.platform != "win32":
        raise RuntimeError("R25 requires native Windows")
    result["platform"] = platform.platform()
    result["python"] = sys.version
    result["checks"]["native_windows"] = True
    for name in ("probe.py", "fixture_app.py", "audit.py"):
        compile((PACKET / name).read_text(encoding="utf-8"), name, "exec")
    result["checks"]["python_sources_compile"] = True
    result["status"] = "PASS" if all(result["checks"].values()) else "FAIL_OR_UNKNOWN"
except BaseException as exc:
    result["status"] = "FAIL_OR_UNKNOWN"
    result["error"] = {"type": type(exc).__name__, "detail": str(exc)}
(PACKET / "preflight.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                       encoding="utf-8")
print(json.dumps({"status": result["status"], "checks": result["checks"],
                  "native_input_sent": False}, sort_keys=True))
raise SystemExit(0 if result["status"] == "PASS" else 1)
