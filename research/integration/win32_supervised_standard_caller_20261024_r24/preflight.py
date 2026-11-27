"""Input-free freeze and predecessor verification for R24."""
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
result = {
    "schema": "win32-supervised-standard-caller-r24-preflight-v1",
    "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "native_input_sent": False,
    "checks": {},
}

try:
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    result["source_commit"] = commit
    result["checks"]["frozen_commit"] = commit == CONDITIONS["source_commit"]
    tracked_clean = (
        subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=ROOT).returncode == 0
        and subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0
    )
    result["tracked_tree_clean"] = tracked_clean
    result["checks"]["tracked_tree_clean"] = tracked_clean
    actual_source_hashes = {}
    for relative, expected in CONDITIONS["source_sha256"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        actual_source_hashes[relative] = actual
        if actual != expected:
            raise RuntimeError(f"source hash mismatch: {relative}")
    result["source_sha256"] = actual_source_hashes
    result["checks"]["frozen_source_hashes"] = True
    frozen_packet_hashes = {}
    for relative, expected in CONDITIONS["frozen_files"].items():
        actual = hashlib.sha256((PACKET / relative).read_bytes()).hexdigest()
        frozen_packet_hashes[relative] = actual
        if actual != expected:
            raise RuntimeError(f"frozen packet hash mismatch: {relative}")
    result["frozen_packet_hashes"] = frozen_packet_hashes
    result["checks"]["frozen_packet_hashes"] = True

    predecessor = CONDITIONS["predecessor"]
    old_raw = subprocess.check_output(
        ["git", "show", f"{commit}:{predecessor['raw_path']}"], cwd=ROOT)
    old_raw_sha256 = hashlib.sha256(old_raw).hexdigest()
    result["predecessor_raw_sha256"] = old_raw_sha256
    manifest_text = subprocess.check_output(
        ["git", "show", f"{commit}:{predecessor['manifest_path']}"],
        cwd=ROOT, text=True)
    manifest_hashes = {
        line.split(maxsplit=1)[1].strip(): line.split(maxsplit=1)[0]
        for line in manifest_text.splitlines() if len(line.split(maxsplit=1)) == 2
    }
    declared_manifest_sha256 = manifest_hashes.get("raw.json")
    old_audit = json.loads(subprocess.check_output(
        ["git", "show", f"{commit}:{predecessor['audit_path']}"],
        cwd=ROOT, text=True))
    result["predecessor_audit_status"] = old_audit.get("status")
    result["predecessor_hash_integrity"] = {
        "current_main_raw_sha256": old_raw_sha256,
        "frozen_current_main_raw_sha256": predecessor["raw_sha256"],
        "final_manifest_raw_sha256": declared_manifest_sha256,
        "followup_audit_raw_sha256": old_audit.get("raw_sha256"),
        "raw_matches_manifest": old_raw_sha256 == declared_manifest_sha256,
        "raw_matches_followup_audit": old_raw_sha256 == old_audit.get("raw_sha256"),
        "limitation": predecessor["hash_discrepancy_note"],
    }
    result["checks"]["predecessor_current_blob_hash"] = (
        old_raw_sha256 == predecessor["raw_sha256"])
    if not result["checks"]["predecessor_current_blob_hash"]:
        raise RuntimeError("merged predecessor R23 raw differs from its frozen current-blob hash")
    old = json.loads(old_raw)
    old_generation = predecessor["target_generation"]
    callback_return_ns = old.get("hook_trace_after_recovery", {}).get("callback_return_ns")
    q_up_callback_ns = old.get("hook_trace_after_recovery", {}).get("q_up_callback_ns")
    independent = old.get("independent_readback", {})
    post_refusal = old.get("post_recovery_dispatch", {}).get("response", {})
    predecessor_semantics = {
        "recovered_action_and_release": (
            old.get("retained_report", {}).get("result", {}).get("status") == "recovered"
            and old.get("retained_report", {}).get("release_confirmed") is True),
        "producer_exit_and_post_callback_q_up": (
            old.get("producer_exit_witness", {}).get("status") == "exited"
            and isinstance(callback_return_ns, int)
            and isinstance(q_up_callback_ns, int)
            and q_up_callback_ns > callback_return_ns),
        "independent_same_generation_q_up": (
            independent.get("status") == "observed"
            and independent.get("q_down") is False
            and independent.get("expected_generation") == old_generation
            and independent.get("generation_before") == old_generation
            and independent.get("generation_after") == old_generation),
        "same_generation_continuation_refused_before_input": (
            post_refusal.get("status") == "invalid_request"
            and post_refusal.get("error") == "fresh target generation required after cancellation"
            and post_refusal.get("operation_invoked") is False
            and post_refusal.get("input_dispatched") is False),
        "effect_and_owned_cleanup": (
            old.get("effect_readback") == {
                "clicked": True,
                "saved": True,
                "text": "SUPERVISED-MCP-PRECANCEL-20261024-R23"}
            and old.get("public_close", {}).get("response", {}).get("status") == "closed"
            and old.get("fixture", {}).get("exit_code") == 0
            and old.get("fixture", {}).get("window_exists_after_exit") is False
            and old.get("hook_stopped", {}).get("thread_exited") is True
            and old.get("foreground_restore", {}).get("restored") is True),
    }
    result["predecessor_semantic_checks"] = predecessor_semantics
    result["checks"]["predecessor_semantics"] = all(predecessor_semantics.values())
    if not result["checks"]["predecessor_semantics"]:
        raise RuntimeError("predecessor R23 raw did not independently verify the frozen recovery facts")

    if sys.platform != "win32":
        raise RuntimeError("R24 requires native Windows")
    result["python"] = sys.version
    result["platform"] = platform.platform()
    result["checks"]["native_windows"] = True
    for name in ("probe.py", "fixture_app.py", "audit.py"):
        compile((PACKET / name).read_text(encoding="utf-8"), name, "exec")
    result["checks"]["python_sources_compile"] = True
    if all(result["checks"].values()):
        result["status"] = (
            "PASS" if result["predecessor_hash_integrity"]["raw_matches_manifest"]
            and result["predecessor_hash_integrity"]["raw_matches_followup_audit"]
            else "PASS_WITH_RECORDED_PREDECESSOR_HASH_LIMITATION")
    else:
        result["status"] = "FAIL_OR_UNKNOWN"
except BaseException as exc:
    result["status"] = "FAIL_OR_UNKNOWN"
    result["error"] = {"type": type(exc).__name__, "detail": str(exc)}

(PACKET / "preflight.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "checks": result["checks"],
                  "predecessor_hash_integrity": result.get("predecessor_hash_integrity"),
                  "native_input_sent": result["native_input_sent"]}, sort_keys=True))
if result["status"] not in ("PASS", "PASS_WITH_RECORDED_PREDECESSOR_HASH_LIMITATION"):
    raise SystemExit(1)
