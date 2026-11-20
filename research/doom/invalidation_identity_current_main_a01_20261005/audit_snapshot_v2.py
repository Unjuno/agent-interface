"""Verify frozen candidate snapshots and WSLc replay outputs independently."""
import argparse
import hashlib
import json
from pathlib import Path
import re


PACKAGE = Path(__file__).resolve().parent
SNAPSHOT = PACKAGE / "source_snapshot"
OUT = PACKAGE / "results" / "current-main-a01"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text())
    runs = json.loads((OUT / "runs.json").read_text())
    errors = []

    for name, expected in freeze["implementation_files"].items():
        path = SNAPSHOT / name
        if not path.is_file() or sha256(path) != expected:
            errors.append(f"candidate snapshot hash mismatch: {name}")

    expected_counts = {"focused": 16, "adjacent": 40}
    for label, expected_count in expected_counts.items():
        row = runs.get(label)
        if type(row) is not dict:
            errors.append(f"missing run receipt: {label}")
            continue
        if row.get("returncode") != 0:
            errors.append(f"nonzero exit: {label}")
        if row.get("source_sha256") != freeze["implementation_files"]:
            errors.append(f"receipt source identities differ from freeze: {label}")
        if row.get("mount_path_redacted") is not True or type(
                row.get("executed_argv_sha256")) is not str or len(
                row["executed_argv_sha256"]) != 64:
            errors.append(f"receipt command provenance is incomplete: {label}")
        argv = row.get("argv", [])
        if "--network" not in argv or argv[argv.index("--network") + 1] != "none":
            errors.append(f"network was not disabled: {label}")
        if "--cpus" not in argv or argv[argv.index("--cpus") + 1] != "1":
            errors.append(f"one CPU was not requested: {label}")
        mount_args = [arg for arg in argv if arg.startswith("type=bind,")]
        if len(mount_args) != 1 or not mount_args[0].endswith(",readonly"):
            errors.append(f"source bind is not uniquely read-only: {label}")
        for stream in ("stdout", "stderr"):
            path = OUT / f"{label}.{stream}.log"
            if not path.is_file() or sha256(path) != row.get(f"{stream}_sha256"):
                errors.append(f"{stream} digest mismatch: {label}")
        text = (OUT / f"{label}.stderr.log").read_text(errors="replace")
        counts = re.findall(r"Ran (\d+) tests? in", text)
        if counts != [str(expected_count)]:
            errors.append(f"unexpected test count {counts!r}: {label}")
        if re.search(r"\b(FAILED|ERROR)\b", text):
            errors.append(f"unittest failure marker: {label}")

    report = {
        "disposition": "PASS_SNAPSHOT_AND_REPLAY_AUDIT" if not errors
        else "FAIL_SNAPSHOT_AND_REPLAY_AUDIT",
        "errors": errors,
        "candidate_source_snapshot_files": len(freeze["implementation_files"]),
        "test_methods": expected_counts,
        "live_allocation": False,
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
