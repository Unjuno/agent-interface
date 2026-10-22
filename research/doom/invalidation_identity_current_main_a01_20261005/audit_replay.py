"""Independent integrity audit for current-main WSLc replay outputs."""
import hashlib
import argparse
import json
from pathlib import Path
import re


PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
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
        actual = sha256(ROOT / name)
        if actual != expected:
            errors.append(f"source hash mismatch: {name}")
    for label, expected_tests in (("focused", 16), ("adjacent", 40)):
        row = runs.get(label)
        if type(row) is not dict:
            errors.append(f"missing run receipt: {label}")
            continue
        if row.get("returncode") != 0:
            errors.append(f"nonzero candidate exit: {label}")
        for stream in ("stdout", "stderr"):
            path = OUT / f"{label}.{stream}.log"
            if not path.is_file() or sha256(path) != row.get(f"{stream}_sha256"):
                errors.append(f"{stream} hash mismatch: {label}")
        text = (OUT / f"{label}.stderr.log").read_text(errors="replace")
        counts = re.findall(r"Ran (\d+) tests? in", text)
        if counts != [str(expected_tests)]:
            errors.append(f"unexpected test count {counts!r}: {label}")
        if re.search(r"\b(FAILED|ERROR)\b", text):
            errors.append(f"failure marker in unittest log: {label}")
    report = {"disposition": "PASS_CURRENT_MAIN_INTEGRATION_REPLAY" if not errors
              else "FAIL_CURRENT_MAIN_INTEGRATION_REPLAY_AUDIT",
              "errors": errors,
              "test_methods": {"focused": 16, "adjacent": 40},
              "live_allocation": False}
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
