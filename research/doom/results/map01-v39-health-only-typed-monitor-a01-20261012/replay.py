import hashlib
import json
import sys
from pathlib import Path

repo, report_path, events_path, output_path = map(Path, sys.argv[1:5])
sys.path.insert(0, str(repo / "research" / "live_control"))
from observable_signal_guard_v2 import ObservableSignalGuard, ObservableSignalPolicyMonitor


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ArtifactExtractor:
    def __init__(self, signal):
        self.signal = signal
        self.calls = 0

    def read(self, observation):
        self.calls += 1
        return self.signal


report = json.loads(report_path.read_text(encoding="utf-8"))
events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
typed = {row["sequence"]: row for row in events if row.get("event") == "typed_observation"}
full = {row["sequence"]: row for row in events if row.get("event") == "observation"}
checks = []
for decision in report["decisions"]:
    for policy in (decision.get("cover_validity_latest_soft_event"), decision.get("policy_invalidation")):
        if not policy:
            continue
        sequence = policy["sequence"]
        source = decision["cover_validity_admission"]["source_signal"]
        effective = decision["cover_validity_admission"]["effective"]
        expected = policy["outcome"]
        source_row = typed[sequence]["signals"]["health"]
        actual = policy["signal"]
        compare_fields = ("format", "status", "signal_id", "value", "sequence", "capture_ns", "binding", "wad_sha256")
        assert all(source_row.get(key) == actual.get(key) for key in compare_fields), sequence
        spec = {
            "op": "observable_signal_guard",
            "guard_id": expected["guard_id"],
            "source_sequence": source["sequence"],
            "signal_id": "health",
            "source_value": source["value"],
            "hard_minimum": effective["hard_minimum"],
            "max_source_age_ms": effective["max_source_age_ms"],
            "on_soft_change": "preserve_existing_policy",
            "on_hard_change": "needs_decision",
            "on_unknown": "needs_decision",
        }
        guard = ObservableSignalGuard(spec, source, source["binding"])
        extractor = ArtifactExtractor(actual)
        monitor = ObservableSignalPolicyMonitor(guard, extractor)
        early_result = monitor.observe(typed[sequence])
        assert extractor.calls == 0, f"artifact reader used for early typed event {sequence}"
        outcome = (early_result["outcome"] if early_result is not None
                   else monitor.latest_soft_event["outcome"])
        compare_outcome = ("status", "reason", "source_value", "current_value", "hard_minimum",
                           "keep_existing_policy", "requires_new_decision", "grants_input_authority",
                           "may_only_preserve_or_reduce_existing_authority", "semantic_change_identified",
                           "task_success_verified")
        assert all(outcome[key] == expected[key] for key in compare_outcome), sequence
        if expected["status"] == "SOFT_CHANGED":
            assert early_result is None and monitor.latest_soft_event["signal"]["value"] == actual["value"]
        else:
            assert early_result is not None and early_result["outcome"]["status"] == "HARD_INVALIDATED"
        artifact_result = monitor.observe({
            "event": "observation", "sequence": sequence,
            "frame_rgb_sha256": full[sequence]["frame_rgb_sha256"],
        })
        assert artifact_result is None, sequence
        assert extractor.calls == 1, sequence
        checks.append({
            "sequence": sequence,
            "policy_status": expected["status"],
            "typed_monitor_status": outcome["status"],
            "artifact_reader_calls_before_typed_decision": 0,
            "matching_artifact_duplicate_suppressed": True,
            "authority_fields_match": True,
            "task_success_verified": outcome["task_success_verified"],
        })
assert len(checks) == 4, len(checks)
out = {
    "schema": "v39-health-only-typed-monitor-replay-v1",
    "source_sha256": {"report": sha(report_path), "events": sha(events_path)},
    "monitor_source_git_blob": hashlib.sha1(
        b"blob " + str((repo / "research/live_control/observable_signal_guard_v2.py").stat().st_size).encode()
        + b"\0" + (repo / "research/live_control/observable_signal_guard_v2.py").read_bytes()
    ).hexdigest(),
    "event_count": len(checks),
    "checks": checks,
    "all_match": True,
    "scope": "Offline replay of retained event pairs; no live process, input, or task-effect claim.",
}
Path(output_path).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(out, indent=2, sort_keys=True))