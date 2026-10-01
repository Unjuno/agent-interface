"""Read-only auditor for the consumed #4536 seed-990639 allocation."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    event_path = ROOT / "runtime/events.jsonl"
    events = [json.loads(line) for line in event_path.read_text().splitlines()]
    owner_path = ROOT / "runtime/owner-events.json"
    owners = json.loads(owner_path.read_text())
    protocol_path = ROOT / "planner-protocol.jsonl"
    protocol = [json.loads(line) for line in protocol_path.read_text().splitlines()]
    turn_completions = [row["message"]["params"]["turn"] for row in protocol
                        if row.get("direction") == "received" and
                        row.get("message", {}).get("method") == "turn/completed"]
    raw_files = sorted(path for path in ROOT.rglob("*") if path.is_file() and
                       path.name != "FORMAL_AUDIT.json")
    report = {
        "classification": "STOP_ADAPTER_INVALIDATION_RECEIPT_SCHEMA_REJECTION",
        "formal_allocation_consumed": True,
        "seed": 990639,
        "decision_limit": 24,
        "runtime_event_counts": dict(Counter(row.get("event") for row in events)),
        "physical_input_admissions": sum(row.get("event") == "input_admission"
                                          for row in events),
        "planner_turn_count": len(turn_completions),
        "planner_turn_status_counts": dict(Counter(row.get("status", "unknown")
                                                    for row in turn_completions)),
        "owner_release_count": len(owners),
        "all_owner_releases_verified_empty": bool(owners) and all(
            row.get("event") == "owner_release" and row.get("verified") is True and
            row.get("keys_down") == [] and row.get("buttons_down") == []
            for row in owners),
        "policy_invalidation_translation_log_present":
            (ROOT / "runtime/policy-invalidation-clock-translations.jsonl").exists(),
        "report_present": (ROOT / "report.json").exists(),
        "score_present": (ROOT / "runtime/score.json").exists(),
        "retained_file_count": len(raw_files),
        "retained_total_bytes": sum(path.stat().st_size for path in raw_files),
        "sha256": {str(path.relative_to(ROOT)): sha256(path) for path in raw_files},
    }
    (ROOT / "FORMAL_AUDIT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "sha256"},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
