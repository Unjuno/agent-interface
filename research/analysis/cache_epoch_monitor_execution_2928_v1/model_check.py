"""Execute the retained decision-policy monitor against hidden epoch/dependency states."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import platform
import subprocess
import sys
from itertools import product
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SUBJECT = ROOT / "research/measurement/decision_policy_cache_rung0_v1"
sys.path.insert(0, str(SUBJECT))
from cache import CacheEntry, Evidence, monitor  # noqa: E402


def main() -> None:
    subject = (SUBJECT / "cache.py").read_bytes()
    entry = CacheEntry(
        cache_id="cache-1",
        intent_id="intent-1",
        strategy_id="strategy-1",
        generation=7,
        provenance="source-1",
        macro_id="macro-1",
        allowed_action="ADVANCE_STEP",
        max_age=12,
        max_updates=16,
    )
    entry_fields = {field.name for field in dataclasses.fields(CacheEntry)}
    evidence_fields = {field.name for field in dataclasses.fields(Evidence)}
    missing_fields = sorted(
        {"request_epoch", "dependency_completeness"} - (entry_fields | evidence_fields)
    )
    rows = []
    for request_epoch, dependencies_complete in product(
        ("same", "changed", "missing"), (True, False)
    ):
        # The subject has no slots for these two truth dimensions. All represented
        # evidence is deliberately held at the exact KEEP boundary.
        evidence = Evidence(
            intent_id=entry.intent_id,
            strategy_id=entry.strategy_id,
            generation=entry.generation,
            provenance=entry.provenance,
            age=0,
            update_index=0,
            regime="VALID_CONTINUATION",
        )
        decision = monitor(entry, evidence)
        oracle_allowed = request_epoch == "same" and dependencies_complete
        rows.append(
            {
                "request_epoch": request_epoch,
                "dependencies_complete": dependencies_complete,
                "candidate_disposition": decision["disposition"],
                "candidate_reason": decision["reason"],
                "oracle_replay_allowed": oracle_allowed,
                "unsafe_keep": decision["disposition"] == "KEEP" and not oracle_allowed,
            }
        )

    result = {
        "schema": "cache_epoch_monitor_execution_2928_v1",
        "allocation": "cache-epoch-monitor-execution-2928-v1-20260928",
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "subject_path": "research/measurement/decision_policy_cache_rung0_v1/cache.py",
        "subject_sha256": hashlib.sha256(subject).hexdigest(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "docker_used": False,
        "docker_reason": "Shared Docker slot remains assigned to Issue #5074; no release observed.",
        "candidate_fields": {
            "CacheEntry": sorted(entry_fields),
            "Evidence": sorted(evidence_fields),
        },
        "missing_required_fields": missing_fields,
        "rows": rows,
        "row_count": len(rows),
        "candidate_keep": sum(row["candidate_disposition"] == "KEEP" for row in rows),
        "oracle_allowed": sum(row["oracle_replay_allowed"] for row in rows),
        "unsafe_keep": sum(row["unsafe_keep"] for row in rows),
        "decision": "FAIL_REPLAY_SAFETY_BOUNDARY_SCOPED",
        "scope": "Historical synthetic monitor only; not production cache/runtime behavior.",
    }
    out = Path(__file__).with_name("RESULT.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("allocation", "source_commit", "subject_sha256", "row_count", "candidate_keep", "oracle_allowed", "unsafe_keep", "decision")}, sort_keys=True))


if __name__ == "__main__":
    main()
