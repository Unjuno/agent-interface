"""Replay bounded typed-health context against the retained v39 event stream."""
import hashlib
import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
report_path = BASE / "report.json"
events_path = BASE / "events.jsonl"
audit_path = BASE / "audit-v2.json"
report = json.loads(report_path.read_text(encoding="utf-8"))
events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
candidate_path = BASE / "coast_hint_candidate.py"
spec = importlib.util.spec_from_file_location("coast_hint_candidate", candidate_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
history = module.CoastHistory()
decisions = []
for decision in report["decisions"]:
    source_name = Path(decision["source_image"]).name
    source = next(row for row in events if row.get("event") == "observation" and
                  Path(row.get("image", "")).name == source_name)
    context = history.prompt_context(source)
    assert source["sequence"] == decision["cover_validity_admission"]["source_signal"]["sequence"]
    assert all(row["sequence"] < source["sequence"] for row in context["coast_history"])
    start, end = decision["controller_model_started_ns"], decision["controller_model_ended_ns"]
    unauthored = decision["cover_validity_admission"]["monitor_mode"] == "unauthored_coast_no_policy"
    accepted = reconciled = 0
    if unauthored:
        interval = [row for row in events if start < row.get("emit_ns", 0) < end and
                    row.get("event") in ("typed_observation", "observation")]
        for row in interval:
            if row["event"] == "typed_observation":
                accepted += int(history.observe_typed(row))
            else:
                reconciled += int(history.observe_full(row) is not None)
    decisions.append({
        "decision": decision["iteration"],
        "monitor_mode": decision["cover_validity_admission"]["monitor_mode"],
        "source_sequence": source["sequence"],
        "historical_context": context["coast_history"],
        "context_bytes": len(json.dumps(context, separators=(",", ":")).encode()),
        "typed_accepted_during_wait": accepted,
        "full_reconciled_during_wait": reconciled,
        "baseline_prior_soft_event_summary": decision.get("prior_soft_event_summary"),
        "final_admission": decision["final_action_admission"]["status"],
    })
value = {
    "schema": "v39-coast-hint-exact-stream-replay-v1",
    "inputs": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
               for path in (report_path, events_path, audit_path)},
    "candidate_sha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
    "rules": "Only events emitted inside an unauthored-coast model wait are fed to CoastHistory. Each typed row must pass schema/binding/value validation and reconcile against a later exact full row. Context is evaluated against each report decision's exact source image/sequence. No interrupt, policy invalidation, input authority, or action is simulated.",
    "decisions": decisions,
    "limits": [
        "Exact deterministic replay of one retained episode; no prospective or randomized comparison.",
        "Prompt-context presence does not establish the model will use a hint correctly or improve actions.",
        "No prediction of cancellation, token savings, task success, or safety.",
        "The live allocation remains consumed; this replay does not rerun or extend it.",
    ],
}
(BASE / "coast-hint-exact-stream-replay.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"decisions": decisions}, indent=2))
