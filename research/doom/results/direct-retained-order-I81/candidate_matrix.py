"""Run the candidate parser on a frozen exhaustive four-timestamp matrix."""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "analyze_map01_direct_retained_input_v1.py"
parser = argparse.ArgumentParser()
parser.add_argument("--output-dir", type=Path, default=HERE)
args = parser.parse_args()
OUTPUT_DIR = args.output_dir.resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
INPUT = OUTPUT_DIR / "raw_cases.json"
OUTPUT = OUTPUT_DIR / "candidate_results.json"

if INPUT.exists() or OUTPUT.exists():
    raise FileExistsError("refusing to overwrite frozen construction output")

spec = importlib.util.spec_from_file_location("direct_candidate", SOURCE)
candidate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(candidate)

cases = []
for case_id, stamps in enumerate(itertools.product(range(4), repeat=4)):
    admitted_ns, input_ack_ns, release_start_ns, release_return_ns = stamps
    events = [
        {"event": "input_admission", "intent_token": "t", "key": "a",
         "admitted_ns": admitted_ns, "input_ack_ns": input_ack_ns},
        {"event": "input_release_transition", "intent_token": "t", "operation": "up",
         "key": "a", "release_call_started_ns": release_start_ns,
         "release_call_returned_ns": release_return_ns,
         "owner_transition_verified": True},
    ]
    cases.append({"case_id": case_id, "timestamps_ns": list(stamps), "events": events})

INPUT.write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")
results = [
    {"case_id": case["case_id"], "result": candidate.analyze(case["events"])}
    for case in cases
]
payload = {
    "schema": "map01-direct-retained-input-order-matrix-candidate-v1",
    "candidate_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "case_count": len(cases),
    "results": results,
}
OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"case_count": len(cases),
                  "candidate_source_sha256": payload["candidate_source_sha256"],
                  "input": str(INPUT), "output": str(OUTPUT)}, indent=2))
