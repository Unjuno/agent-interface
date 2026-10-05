"""Run frozen V10 release-admission cases against baseline and candidate."""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if any(args.out.iterdir()):
        raise SystemExit("output directory must be empty")
    summaries = []
    for variant in ("baseline", "candidate"):
        case_dir = args.source_root / variant
        for mode in ("normal", "optimized"):
            command = [sys.executable]
            if mode == "optimized":
                command.append("-O")
            command.extend(("-m", "unittest", "discover", "-s", str(case_dir),
                            "-p", "test_input_owner_v10_release_retry.py", "-v"))
            completed = subprocess.run(command, cwd=case_dir, text=True,
                                       capture_output=True, check=False)
            record = {
                "variant": variant,
                "mode": mode,
                "command": command,
                "cwd": str(case_dir),
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
            path = args.out / f"{variant}-{mode}.json"
            path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            summaries.append({"variant": variant, "mode": mode,
                              "exit_code": completed.returncode,
                              "raw": path.name})
    print(json.dumps({"runs": summaries}, indent=2))


if __name__ == "__main__":
    main()
