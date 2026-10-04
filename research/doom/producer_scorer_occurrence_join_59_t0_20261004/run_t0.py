from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "dependencies"))

from producer_scorer_occurrence_join import attribute_acknowledged_events
from test_producer_scorer_occurrence_join import source_records


def main() -> None:
    samples, events, admissions, raw_releases, bindings, producer_updates = source_records()
    results = attribute_acknowledged_events(
        samples, events, admissions, raw_releases, bindings)
    result = {
        "schema": "producer-scorer-occurrence-join-raw-v1",
        "run_id": "run-A",
        "samples": samples,
        "producer_updates": producer_updates,
        "events": events,
        "admissions": admissions,
        "raw_releases": raw_releases,
        "semantic_bindings": bindings,
        "attribution": results,
    }
    output = ROOT / "results" / "t0-01" / "raw.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({"raw": str(output), "events": len(events),
                      "attribution": results}, sort_keys=True))


if __name__ == "__main__":
    main()
