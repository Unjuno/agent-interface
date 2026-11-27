"""Run one positive and one missing-usage control with retained raw evidence."""

from __future__ import annotations

import json
from pathlib import Path

from composition import run_case


ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "runs"


def main() -> None:
    if RUNS.exists() and any(RUNS.iterdir()):
        raise SystemExit(f"refusing to overwrite retained runs: {RUNS}")
    RUNS.mkdir(parents=True, exist_ok=True)
    results = [
        run_case(RUNS / "positive", late_usage_available=True),
        run_case(RUNS / "missing-usage", late_usage_available=False),
    ]
    positive, negative = results
    if not (positive["usage_status"] == "complete" and
            positive["input_tokens"] == 18 and
            positive["output_tokens"] == 3 and
            negative["usage_status"] == "incomplete" and
            negative["input_tokens"] is None and
            negative["output_tokens"] is None and
            all(item["task_success"] is None for item in results) and
            all(item["relay_calls"] == 0 for item in results)):
        raise SystemExit("frozen positive/negative decision rule failed")
    result = {"status": "PASS_SCOPED_SYNTHETIC_COMPOSITION",
              "source_revision": "d08596ee0590ba6a9531075a5769c0ac4abc1ec1",
              "conditions": results}
    (ROOT / "experiment-result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
