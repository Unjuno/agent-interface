"""Read MAP01 v15 JSONL artifacts and classify one intent's scorer interval."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from candidate_v2 import classify_intent


def _read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                raise ValueError(f"blank JSONL row at {line_number}")
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"JSONL row {line_number} is not an object")
            rows.append(row)
    return rows


def classify_files(events_path, scorer_samples_path, intent_id, *, max_gap_ns):
    """Load events.jsonl and scorer-samples.jsonl, failing closed on file errors."""
    try:
        events = _read_jsonl(events_path)
        samples = _read_jsonl(scorer_samples_path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        return {"decision": "POST_CANCELLATION_COOCCURRENCE",
                "reason": "invalid_or_missing_runtime_jsonl",
                "error_type": type(exc).__name__, "causal_attribution": False}
    return classify_intent(events, samples, intent_id, max_gap_ns=max_gap_ns)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--scorer-samples", required=True, type=Path)
    parser.add_argument("--intent-id", required=True)
    parser.add_argument("--max-gap-ns", required=True, type=int)
    args = parser.parse_args()
    result = classify_files(args.events, args.scorer_samples, args.intent_id,
                            max_gap_ns=args.max_gap_ns)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
