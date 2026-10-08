"""Read-only audit of the frozen local-Docker modal-effect construction."""
import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
audit_dir = Path(sys.argv[2])
audit_dir.mkdir(parents=True, exist_ok=False)
errors = []

def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"unreadable:{path.relative_to(root)}:{type(exc).__name__}")
        return {}

result = load(root / "result.json")
trace = result.get("trace", {})
expected = ["observe", "dispatch", "inspect_target", "review_target", "observe",
            "dispatch", "dispatch", "inspect_target", "review_target", "observe",
            "dispatch", "dispatch", "close"]
calls = trace.get("calls", [])
ops = [row.get("operation") for row in calls]
runner_decision = result.get("decision")
if runner_decision == "PASS_PUBLIC_MCP_MODAL_EFFECT_SCOPED":
    if ops != expected:
        errors.append("call_order")
elif runner_decision == "STOP_CONSTRUCTION_EXCEPTION_NO_RETRY":
    prefix = expected[:len(ops)]
    if ops and ops[-1] == "close" and len(ops) <= len(expected):
        prefix = expected[:len(ops)-1] + ["close"]
    if ops != prefix:
        errors.append("stop_call_prefix")
else:
    errors.append("unknown_runner_decision")
if result.get("decision") != trace.get("decision"):
    errors.append("runner_trace_decision_mismatch")
if result.get("model_calls") != 0 or result.get("network_calls") != 0 or result.get("authority_granted") is not False:
    errors.append("scope_counters")

root_id = trace.get("root_window_id")
before = trace.get("effect_before_open", [])
after_open = trace.get("effect_after_open", [])
after_escape = trace.get("effect_after_escape", [])
final_effect = trace.get("effect_final", [])
if runner_decision == "PASS_PUBLIC_MCP_MODAL_EFFECT_SCOPED":
    if before:
        errors.append("dialog_preexisted")
    if len(after_open) != 1 or after_open[0].get("window_id") == root_id:
        errors.append("dialog_appearance_or_identity")
if len(after_open) == 1:
    modal = after_open[0]
    try:
        transient = int(modal.get("transient_for"), 16) if modal.get("transient_for") else None
    except ValueError:
        transient = None
    if transient != root_id:
        errors.append("modal_parent_not_original_root")
if runner_decision == "PASS_PUBLIC_MCP_MODAL_EFFECT_SCOPED" and (after_escape or final_effect):
    errors.append("dialog_absence_not_retained")

initial = trace.get("01_observe", {})
open_effect = trace.get("open_dispatch_result", {})
inspect = trace.get("03_inspect_target", {})
review = trace.get("04_review_target", {})
stale_dialog = trace.get("stale_dialog_result", {})
dismiss = trace.get("dismiss_dispatch_result", {})
root_inspect = trace.get("08_inspect_target", {})
root_review = trace.get("09_review_target", {})
stale_root = trace.get("stale_root_result", {})
final_dispatch = trace.get("final_dispatch_result", {})
if runner_decision == "PASS_PUBLIC_MCP_MODAL_EFFECT_SCOPED":
    if initial.get("session", {}).get("binding_revision") != 1:
        errors.append("initial_binding_revision")
    if open_effect.get("status") != "completed":
        errors.append("open_dispatch_not_completed")
    evidence = inspect.get("evidence", {})
    if (inspect.get("status") != "needs_review" or evidence.get("window_id") != (after_open[0].get("window_id") if len(after_open)==1 else None)
            or evidence.get("family_root") != root_id):
        errors.append("dialog_inspect_binding")
    if review.get("status") != "target_reviewed" or review.get("binding_revision") != 2:
        errors.append("dialog_review_revision")
    for label, row in (("dialog", stale_dialog), ("root", stale_root)):
        if row.get("error") != "STALE_BINDING" or row.get("backend_emissions") != 0 or row.get("status") != "refused":
            errors.append(f"{label}_stale_control")
    for label, row in (("dismiss", dismiss), ("final", final_dispatch)):
        releases = row.get("execution", {}).get("releases", [])
        if row.get("status") != "completed" or not releases or not all(
                r.get("verified") is True and r.get("keys_down") == [] and r.get("buttons_down") == []
                for r in releases):
            errors.append(f"{label}_release")
    if root_inspect.get("status") != "needs_review" or root_inspect.get("evidence", {}).get("window_id") != root_id:
        errors.append("root_return_inspect")
    if root_review.get("status") != "target_reviewed" or root_review.get("window_id") != root_id or root_review.get("binding_revision") != 3:
        errors.append("root_return_review")
close = trace.get("13_close", trace.get("99_close", {}))
if close and (close.get("status") != "closed" or close.get("release_attempted") is not True or
              close.get("release", {}).get("verified") is not True or
              close.get("release", {}).get("keys_down") != [] or
              close.get("release", {}).get("buttons_down") != []):
    errors.append("close_release")

server_ops = []
session_ids = set()
for row in calls:
    call_id = row.get("call_id")
    if not call_id:
        errors.append(f"missing_call_id:{row.get('index')}")
        continue
    folder = root / "server-receipts" / call_id
    request = load(folder / "request.json")
    report = load(folder / "report.json")
    server_ops.append(request.get("operation"))
    if request.get("operation") != row.get("operation"):
        errors.append(f"server_operation:{call_id}")
    sid = request.get("session", {}).get("session_id")
    if sid:
        session_ids.add(sid)
    if row.get("operation") != "close" and report.get("session", {}).get("session_id") != trace.get("session_id"):
        errors.append(f"session_lineage:{call_id}")
    for image in row.get("images", []):
        image_path = root / image["path"]
        if not image_path.is_file():
            errors.append(f"missing_image:{image['path']}")
        elif image_path.stat().st_size != image.get("bytes") or hashlib.sha256(image_path.read_bytes()).hexdigest() != image.get("sha256"):
            errors.append(f"image_digest:{image['path']}")
if server_ops != ops:
    errors.append("server_request_order")
if calls and trace.get("session_id") is None:
    errors.append("session_identity_missing")
if calls and session_ids != {trace.get("session_id")}:
    errors.append("request_session_lineage")
reads = trace.get("retained_reads", [])
if runner_decision == "PASS_PUBLIC_MCP_MODAL_EFFECT_SCOPED" and len(reads) != len(calls):
    errors.append("retained_read_count")
for i, (prior, read) in enumerate(zip(calls, reads), start=1):
    if read.get("call_id") != prior.get("call_id") or read.get("state") != "finished" or read.get("operation_invoked") is not False:
        errors.append(f"retained_read_binding:{i}")
    response_path = root / "mcp" / f"14-retained-{i:02d}.json"
    response = load(response_path)
    texts = [x.get("text", "") for x in response.get("content", []) if x.get("type") == "text"]
    try:
        read_payload = json.loads(texts[0]) if len(texts) == 1 else {}
    except Exception:
        read_payload = {}
    if (read_payload.get("call_id") != prior.get("call_id") or
            read_payload.get("retained_call", {}).get("state") != "finished" or
            read_payload.get("operation_invoked") is not False):
        errors.append(f"retained_read_receipt:{i}")
cleanup = load(root / "post-cleanup.json")
if cleanup.get("x_socket_exists") is not False:
    errors.append("x_socket_remains")
env = load(root / "environment.json")
if env.get("network") != "none" or env.get("authority_granted") is not False:
    errors.append("environment_scope")
runner_sha = hashlib.sha256(Path(__file__).with_name("runner.py").read_bytes()).hexdigest()
if env.get("runner_sha256") != runner_sha:
    errors.append("runner_hash")

audit = {
    "schema": "agent-interface/2907-public-mcp-modal-effect-audit-v1",
    "decision": "PASS_RAW_AUDIT" if not errors else "FAIL_RAW_AUDIT",
    "errors": errors,
    "formal_allocation": False,
    "runner_decision": runner_decision,
    "call_order": server_ops,
    "root_window_id": root_id,
    "dialog_ids": [row.get("window_id") for row in after_open],
    "effect_oracle": {"before": len(before), "after_ctrl_o": len(after_open),
                       "after_escape": len(after_escape), "final": len(final_effect)},
    "binding_revisions": [trace.get("revision_initial"), trace.get("revision_dialog"), trace.get("revision_root")],
    "stale_results": [stale_dialog, stale_root],
    "session_id": trace.get("session_id"),
    "scope": "single public-MCP Calc transient-dialog effect construction; not full mixed-app/controller or #2789 acceptance",
}
(audit_dir / "AUDIT.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(audit, sort_keys=True, indent=2))
raise SystemExit(0 if not errors else 2)
