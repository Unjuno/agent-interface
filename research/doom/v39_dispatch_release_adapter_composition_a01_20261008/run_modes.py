"""Run the deterministic composition candidate once normally and once with -O."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def run_modes(out_dir: Path) -> dict:
    if out_dir.exists():
        raise FileExistsError(f"refusing to reuse run output: {out_dir}")
    out_dir.mkdir(parents=True)
    records = []
    for mode, optimize in (("normal", False), ("optimized", True)):
        candidate_out = out_dir / mode
        command = [sys.executable]
        if optimize:
            command.append("-O")
        command += [str(HERE / "candidate.py"), "--out-dir", str(candidate_out)]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        (out_dir / f"{mode}.stdout").write_text(completed.stdout, encoding="utf-8")
        (out_dir / f"{mode}.stderr").write_text(completed.stderr, encoding="utf-8")
        (out_dir / f"{mode}.exit").write_text(f"{completed.returncode}\n", encoding="ascii")
        (out_dir / f"{mode}.command.json").write_text(
            json.dumps(command, indent=2) + "\n", encoding="utf-8"
        )
        records.append({"mode": mode, "exit": completed.returncode, "command": command})
        if completed.returncode != 0:
            run = {"schema": "v39-dispatch-release-adapter-run-v1", "modes": records,
                   "disposition": "STOP_CANDIDATE_EXIT_NONZERO"}
            (out_dir / "RUN_RECORD.json").write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
            return run

    normal_result = (out_dir / "normal/result.json").read_bytes()
    optimized_result = (out_dir / "optimized/result.json").read_bytes()
    normal_manifest = (out_dir / "normal/sources.json").read_bytes()
    optimized_manifest = (out_dir / "optimized/sources.json").read_bytes()
    equal = normal_result == optimized_result and normal_manifest == optimized_manifest
    run = {
        "schema": "v39-dispatch-release-adapter-run-v1",
        "modes": records,
        "normal_equals_optimized_result": normal_result == optimized_result,
        "normal_equals_optimized_manifest": normal_manifest == optimized_manifest,
        "disposition": "PASS_REPRODUCIBLE" if equal else "FAIL_MODE_DIVERGENCE",
    }
    (out_dir / "RUN_RECORD.json").write_text(json.dumps(run, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not equal:
        raise AssertionError("normal and optimized outputs differ")
    return run


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_modes(args.out_dir.resolve()), sort_keys=True))
