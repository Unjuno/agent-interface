"""Small deterministic preflight; never invokes the frozen candidate CLI."""
from __future__ import annotations
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spec

fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
rows = 0
for case in fixture["cases"]:
    case_rows = 0
    for window in case["windows"]:
        for seed in (window["seed_start"], window["seed_start"]+window["n"]//2,
                     window["seed_start"]+window["n"]-1):
            before = spec.response(fixture["base_trace"], seed, window, fixture)
            after = spec.response(fixture["reduced_trace"], seed, window, fixture)
            if before["fingerprint"] == fixture["competing_fingerprint"]:
                assert before["exit_code"] == after["exit_code"] == fixture["same_exit_code"]
            case_rows += 1
        rows += window["n"]
    assert case_rows == 3 * len(case["windows"])
print(f"preflight PASS: {len(fixture['cases'])} cases, {rows} planned paired rows, 3 endpoint probes/window")
