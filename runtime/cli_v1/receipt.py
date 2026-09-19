"""Read-only presentation of a retained prepared-exchange receipt."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


# Only routine records with retained raw evidence may leave the default view.
# Unknown event types always remain visible.
ROUTINE = {"observation", "command", "decision_evidence", "accepted", "step_started", "step_completed"}


def receipt_view(path: str, *, raw: bool = False) -> dict:
    source = Path(path).resolve(strict=True)
    data = source.read_bytes()
    report = json.loads(data)
    if not isinstance(report, dict):
        raise ValueError("receipt must be an object")
    if raw:
        return report
    records = report.get("records", [])
    if not isinstance(records, list) or any(not isinstance(r, dict) for r in records):
        raise ValueError("receipt records must be objects")
    if not isinstance(report.get("status"), str):
        raise ValueError("receipt status required")
    observations = [r for r in records if r.get("event") == "observation"]
    if any(type(r.get("sequence")) is not int for r in observations):
        raise ValueError("observation sequence required")
    newest = max((r["sequence"] for r in observations), default=None)
    # Keep all equal-sequence records: conflicting evidence must stay visible.
    latest = [r for r in observations if r["sequence"] == newest]
    visible = [r for r in records if r.get("event") not in ROUTINE]
    counts = Counter(str(r.get("event", "<missing>")) for r in records)
    return {
        "schema": "agent-interface/receipt-view-v1",
        "authority": "none",
        "source": {"path": str(source), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)},
        "report": {k: v for k, v in report.items() if k != "records"},
        "latest_observations": latest,
        "events": visible,
        "record_counts": dict(sorted(counts.items())),
        "omitted_from_view": len(records) - len(latest) - len(visible),
        "scope": "Historical receipt only. Earlier observations and routine records remain in source; use --raw for history. No input or freshness granted.",
    }
