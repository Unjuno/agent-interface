"""Cross-platform integrity audit for retained pointer release transfer."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/pointer-release-transfer-live-01"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    retention, plan = read(ROOT / "retention.json"), read(ROOT / "preregistration.json")
    report, original = read(ROOT / "report.json"), read(ROOT / "audit.json")
    events, owners = read(ROOT / "events.json"), read(ROOT / "owner-events.json")
    released = next(row for row in events if row.get("event") == "input_released")
    terminal = next(row for row in events if row.get("event") == "terminal")
    checks = {
        "manifest": all(sha(ROOT / name) == digest
                        for name, digest in retention["manifest"].items()),
        "frozen_sources": all(sha(REPO / name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "first_pass": retention["decision"] == "RETAIN_FIRST_PASS_NO_RETRY" and
                      report["passed"] is True and original["passed"] is True,
        "all_original_checks": all(report["checks"].values()) and
                               all(original["checks"].values()),
        "exact_owner_cause": released["owner_release"] in owners and
            released["owner_release"] == terminal["interruption"]["record"],
        "release_before_terminal": events.index(released) < events.index(terminal) and
            released["published_ns"] < terminal["terminal_ns"],
        "token_bound": released["intent_token"] == report["accepted"]["intent_token"],
        "no_cancel_model_retry": not any(row.get("event") == "cancel_requested" for row in events) and
            report["model_calls"] == report["retry_count"] == 0,
        "thresholds": report["metrics_ms"]["focus_request_to_physical_release_ms"] <= 50 and
            report["metrics_ms"]["focus_request_to_release_publication_ms"] <= 75 and
            report["metrics_ms"]["focus_request_to_terminal_ms"] <= 150,
    }
    audit = {"passed": all(checks.values()), "checks": checks,
        "metrics_ms": report["metrics_ms"],
        "files_in_manifest": len(retention["manifest"]),
        "retained_bytes_before_receipt": retention["bytes"], "scope": report["scope"]}
    (ROOT / "retained-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2)); return 0 if audit["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
