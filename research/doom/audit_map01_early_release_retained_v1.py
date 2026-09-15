"""Cross-platform integrity audit of the retained two-phase release pass."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/map01-early-release-live-01"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    retention, prereg = read(ROOT / "retention.json"), read(ROOT / "preregistration.json")
    report, original = read(ROOT / "report.json"), read(ROOT / "audit.json")
    events = [json.loads(line) for line in
              (ROOT / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    released = next(row for row in events if row.get("event") == "input_released")
    terminal = next(row for row in events if row.get("event") == "terminal" and
                    row.get("id") == released["id"])
    checks = {
        "manifest": all(sha(ROOT / name) == digest
                        for name, digest in retention["manifest"].items()),
        "frozen_sources": all(sha(REPO / name) == digest
                              for name, digest in prereg["source_sha256"].items()),
        "first_pass_retained": retention["decision"] == "RETAIN_FIRST_PASS_NO_RETRY" and
                               report["passed"] is True and original["passed"] is True,
        "all_frozen_checks_pass": all(report["checks"].values()) and
                                  all(original["checks"].values()),
        "exact_order": report["cancel_event"]["requested_ns"] <=
            released["owner_release"]["verified_ns"] <= released["published_ns"] <
            report["invalidating_full_observation"]["artifact_ready_ns"] <
            terminal["terminal_ns"],
        "lease_identity": released["intent_token"] ==
            report["physical_release_event"]["intent_token"],
        "two_phase_state": report["release_pending_guard"]["state"] ==
            "REVOKED_INPUT_RELEASED_AWAITING_TERMINAL" and
            report["release_pending_guard"]["program_terminal_pending"] is True and
            report["running_guard"]["program_terminal_pending"] is False,
        "measured_thresholds": report["metrics_ms"]["capture_to_guard_decision_ms"] <= 60 and
            report["metrics_ms"]["capture_to_cancel_requested_ms"] <= 75 and
            report["metrics_ms"]["capture_to_physical_release_ms"] <= 90 and
            report["metrics_ms"]["capture_to_terminal_closure_ms"] <= 200,
        "zero_model": report["model_calls"] == 0 and
                      not list(ROOT.rglob("planner-protocol.jsonl")),
    }
    audit = {"passed": all(checks.values()), "checks": checks,
        "metrics_ms": report["metrics_ms"],
        "files_in_retention_manifest": len(retention["manifest"]),
        "retained_bytes_before_receipt": retention["bytes"],
        "scope": report["scope"]}
    (ROOT / "retained-audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))
    return 0 if audit["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
