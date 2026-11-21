"""Create the finite synthetic A/B/C adapter integration evidence packet."""

import json
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--output-root", default="raw-generated")
args = parser.parse_args()
OUTPUT = Path(args.output_root)
if not OUTPUT.is_absolute():
    OUTPUT = ROOT / OUTPUT
OUTPUT.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(ROOT.parent))

from comparison_measurement_v1 import validate_matched_block
from test_recorded_comparison_adapter_v1 import (
    RecordedComparisonAdapterTests,
)
builder = RecordedComparisonAdapterTests.make_run
runs = []
for order, arm in enumerate(("A", "B", "C"), start=1):
    run_root = OUTPUT / arm
    run_root.mkdir(parents=True, exist_ok=True)
    measured = builder(run_root, arm, order)
    (run_root / "measured-run.json").write_text(
        json.dumps(measured, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    runs.append(measured)

summary = validate_matched_block(runs)
(OUTPUT / "matched-summary.json").write_text(
    json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(summary, sort_keys=True))
