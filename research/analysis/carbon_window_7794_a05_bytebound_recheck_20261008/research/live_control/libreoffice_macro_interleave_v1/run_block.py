#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    root = Path(args.root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    schedule = json.loads((root / "schedule.json").read_text(encoding="utf-8"))["cases"]
    ledger = []
    for index, scenario in enumerate(schedule):
        case_id = f"{index:02d}-{scenario}"
        cp = subprocess.run([
            "/usr/bin/python3", str(root / "run_case.py"),
            "--scenario", scenario,
            "--case-id", case_id,
            "--out-dir", str(out / case_id),
            "--macro-source", str(root / "conditional_window_macro.py"),
            "--writer", str(root / "writer_wait.py"),
            "--invoker", str(root / "macro_invoker.py"),
        ], capture_output=True, text=True)
        row = {
            "index": index, "case_id": case_id, "scenario": scenario,
            "returncode": cp.returncode, "stdout": cp.stdout, "stderr": cp.stderr,
        }
        result_path = out / case_id / "result.json"
        if result_path.exists():
            row["result"] = json.loads(result_path.read_text(encoding="utf-8"))
        ledger.append(row)
        (out / "ledger.json").write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if cp.returncode != 0:
            print(json.dumps(row, indent=2, sort_keys=True))
            return 2
    print(json.dumps({"completed": len(ledger), "out": str(out)}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
