"""Read-only auditor for the consumed #4544 seed-990641 allocation."""
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
    events = [json.loads(line) for line in
              (ROOT / "runtime/events.jsonl").read_text().splitlines()]
    owners = json.loads((ROOT / "runtime/owner-events.json").read_text())
    protocol = [json.loads(line) for line in
                (ROOT / "planner-protocol.jsonl").read_text().splitlines()]
    turns = [row["message"]["params"]["turn"] for row in protocol
             if row.get("direction") == "received" and
             row.get("message", {}).get("method") == "turn/completed"]
    raw_files = sorted(path for path in ROOT.rglob("*") if path.is_file() and
                       path.name != "FORMAL_AUDIT.json")
    report = {
        "classification": "HOLD_INCOMPLETE_ACTION_VALIDITY_CLOCK_BOUNDARY_BEFORE_POLICY_INVALIDATION",
        "formal_allocation_consumed": True,
        "seed": 990641,
        "decision_limit": 24,
        "runtime_event_counts": dict(Counter(row.get("event") for row in events)),
        "physical_input_admissions": sum(row.get("event") == "input_admission"
                                          for row in events),
        "exact_observations": sum(row.get("event") == "observation" for row in events),
        "typed_observations": sum(row.get("event") == "typed_observation" for row in events),
        "planner_turn_count": len(turns),
        "planner_turn_status_counts": dict(Counter(row.get("status", "unknown")
                                                    for row in turns)),
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
