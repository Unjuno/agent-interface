#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import statistics
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
BIN = ROOT / "facility"


def parse_values(raw: str) -> list[float]:
    if ":" in raw:
        parts = [float(x) for x in raw.split(":")]
        if len(parts) != 3:
            raise ValueError("range must be start:stop:step")
        start, stop, step = parts
        if step == 0:
            raise ValueError("step cannot be zero")
        out = []
        x = start
        if step > 0:
            while x <= stop + abs(step) * 1e-9:
                out.append(x); x += step
        else:
            while x >= stop - abs(step) * 1e-9:
                out.append(x); x += step
        return out
    return [float(x) for x in raw.split(",") if x.strip()]


def run_one(seed: int, difficulty: float, axis: str, value: float) -> dict:
    with tempfile.TemporaryDirectory() as td:
        report = Path(td) / "report.json"
        cp = subprocess.run(
            [str(BIN), "--headless", "--auto-reference", "--seed", str(seed),
             "--difficulty", str(difficulty), "--set", f"{axis}={value}", "--report", str(report)],
            cwd=ROOT, text=True, capture_output=True,
        )
        if not report.exists():
            raise RuntimeError(f"run produced no report: rc={cp.returncode} stderr={cp.stderr}")
        return json.loads(report.read_text())


def main() -> int:
    ap = argparse.ArgumentParser(description="Fixed-seed parameter sweep for Facility v0 construction/regression")
    ap.add_argument("--axis", required=True)
    ap.add_argument("--values", required=True, help="comma list or start:stop:step")
    ap.add_argument("--difficulty", type=float, default=0.45)
    ap.add_argument("--suite", default=str(ROOT / "FIXED_SUITE.json"))
    ap.add_argument("--min-success", type=float, default=0.95)
    ap.add_argument("--output")
    args = ap.parse_args()

    suite = json.loads(Path(args.suite).read_text())
    seeds = [int(x) for x in suite["seeds"]]
    rows = []
    for value in parse_values(args.values):
        reports = [run_one(seed, args.difficulty, args.axis, value) for seed in seeds]
        successes = sum(bool(r["success"]) for r in reports)
        failures = Counter(r["failure"] for r in reports if not r["success"])
        rows.append({
            "value": value,
            "episodes": len(reports),
            "successes": successes,
            "success_rate": successes / len(reports),
            "mean_ticks": statistics.mean(r["ticks"] for r in reports),
            "failure_reasons": dict(sorted(failures.items())),
        })
    qualifying = [r["value"] for r in rows if r["success_rate"] >= args.min_success]
    result = {
        "schema": "procedural-ops-facility-sweep-v0",
        "controller": "private-reference-construction-only",
        "axis": args.axis,
        "base_difficulty": args.difficulty,
        "fixed_suite": suite,
        "min_success": args.min_success,
        "rows": rows,
        "qualifying_values": qualifying,
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
