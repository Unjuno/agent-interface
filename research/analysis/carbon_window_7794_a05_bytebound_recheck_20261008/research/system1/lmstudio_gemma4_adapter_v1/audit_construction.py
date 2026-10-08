"""Independent raw-only audit for the host-only adapter construction run."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEFAULT_RUNNER = HERE / "results" / "construction-01" / "runner.json"
DEFAULT_OUTPUT = HERE / "results" / "construction-01" / "audit.json"
EXPECTED_COMMAND = "python -m pytest -q research/system1/lmstudio_gemma4_adapter_v1/test_lmstudio_chat.py"
EXPECTED_FILES = (
    "README.md",
    "lmstudio_chat.py",
    "test_lmstudio_chat.py",
    "run_construction.py",
    "audit_construction.py",
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit(report, runner_path):
    errors = []
    if report.get("experiment") != "lmstudio_gemma4_adapter_v1_construction":
        errors.append("wrong experiment identity")
    if report.get("command_display") != EXPECTED_COMMAND:
        errors.append("unexpected test command")
    if report.get("status") != "PASS" or report.get("returncode") != 0:
        errors.append("runner did not exit successfully")
    if report.get("test_count_from_pytest_summary") != 10:
        errors.append("runner summary does not report ten passing tests")
    summary = re.search(r"\b(\d+) passed\b", report.get("stdout", ""))
    if summary is None or int(summary.group(1)) != 10:
        errors.append("raw stdout does not independently confirm ten passing tests")
    if re.search(r"\b\d+ failed\b|\bERROR collecting\b", report.get("stdout", "")):
        errors.append("raw stdout contains a failure or collection error")
    if report.get("stderr", "").strip():
        errors.append("runner stderr is not empty")
    for key in ("model_calls", "gpu_calls", "container_invocations", "external_network_calls"):
        if report.get(key) != 0:
            errors.append(f"{key} is not zero")
    if report.get("network_scope") != "loopback mock HTTP server only":
        errors.append("network scope is not the frozen loopback mock")

    recorded = report.get("source_sha256")
    if not isinstance(recorded, dict) or set(recorded) != set(EXPECTED_FILES):
        errors.append("source hash manifest has an unexpected path set")
    else:
        for name in EXPECTED_FILES:
            path = HERE / name
            if not path.is_file() or recorded[name] != sha256(path):
                errors.append(f"source hash mismatch: {name}")

    return {
        "audit": "lmstudio_gemma4_adapter_v1_construction_raw_only",
        "status": "PASS_ADAPTER_CONSTRUCTION_ONLY" if not errors else "FAIL_AUDIT",
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "runner_sha256": sha256(runner_path),
        "errors": errors,
        "model_calls_attributed": 0,
        "scientific_model_claim": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", type=Path, default=DEFAULT_RUNNER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    runner = args.runner.resolve()
    output = args.output.resolve()
    if not runner.is_relative_to(HERE) or not runner.is_file():
        raise SystemExit("runner must be an existing file under this evidence directory")
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing audit: {output}")
    if not output.is_relative_to(HERE):
        raise SystemExit("audit output must remain under this evidence directory")
    with runner.open("r", encoding="utf-8") as stream:
        report = json.load(stream)
    result = audit(report, runner)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
