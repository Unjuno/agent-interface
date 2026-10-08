"""One-shot synthetic formal runner."""
import json
import sys
from pathlib import Path

from .model import POLICIES, SCENARIOS, all_traces, summarize


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.analysis.stpa_feedback_constraint_5327_t0_v1.run OUTPUT_DIR")
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit(f"STOP_OUTPUT_EXISTS: {out}")
    out.mkdir(parents=True)
    rows = all_traces()
    raw = {"schema": "stpa-feedback-constraint-5327-t0-v1", "policies": list(POLICIES), "scenarios": list(SCENARIOS), "traces": rows}
    (out / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    summary = summarize(rows)
    (out / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["status"] == "PASS_FEEDBACK_CONSTRAINT_SCOPED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
