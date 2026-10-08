#!/usr/bin/env python3
"""Custody wrapper: persist exact child exit status without zsh special variables."""
from __future__ import annotations

import json
import hashlib
import subprocess
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
RECORD = HERE / "RUN_RECORD.json"
EXPECTED_CASES = 441
ALLOCATION = "LABEL-CONTROL-AMBIGUITY-1998-T0-A04-20261009"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def write_record(record: dict) -> None:
    RECORD.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture_process(command: list[str], cwd: Path, stdout_path: Path, stderr_path: Path) -> tuple[int | None, str | None]:
    try:
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            completed = subprocess.run(command, cwd=cwd, stdout=stdout, stderr=stderr, check=False)
            return completed.returncode, None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def run_child(phase: str) -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    if not RECORD.exists():
        shutil.copyfile(HERE / "RUN_RECORD.template.json", RECORD)
    record = read_record()
    if record.get("allocation") != ALLOCATION:
        raise SystemExit("STOP_RUN_RECORD_ALLOCATION_MISMATCH")
    if phase == "candidate":
        if record["candidate"]["invocations"] != 0 or record["auditor"]["invocations"] != 0:
            raise SystemExit("STOP_CANDIDATE_ALREADY_ATTEMPTED")
        child = HERE / "candidate.py"
        stdout_path, stderr_path = RESULTS / "candidate.stdout", RESULTS / "candidate.stderr"
        record["candidate"]["invocations"] = 1
    elif phase == "auditor":
        if (record["candidate"].get("invocations") != 1
                or record["candidate"].get("exit_code") != 0
                or record["candidate"].get("output_completeness") != "PASS_STRUCTURAL_441_CASES"):
            raise SystemExit("STOP_CANDIDATE_GATE_NOT_CONFIRMED")
        if record["auditor"]["invocations"] != 0:
            raise SystemExit("STOP_AUDITOR_ALREADY_ATTEMPTED")
        child = HERE / "auditor.py"
        stdout_path, stderr_path = RESULTS / "audit.stdout", RESULTS / "auditor.stderr"
        record["auditor"]["invocations"] = 1
    else:
        raise SystemExit("unknown formal phase")

    started = now()
    if not record.get("freeze_commit"):
        try:
            get_commit = lambda ref: subprocess.run(
                ["git", "rev-parse", ref], cwd=HERE.parents[2], check=True,
                capture_output=True, text=True).stdout.strip()
            record["freeze_commit"] = get_commit("HEAD")
            record["source_commit"] = get_commit("HEAD^")
            if get_commit("HEAD^^") != record["base_commit"]:
                raise RuntimeError("freeze/source commits are not anchored directly to declared base")
        except Exception as exc:
            raise SystemExit("STOP_FREEZE_COMMIT_UNAVAILABLE:" + type(exc).__name__)
    record["freeze_sha256"] = file_sha(HERE / "FREEZE.json")
    record["network_policy"] = "sandbox-exec profile: (version 1) (allow default) (deny network*)"
    record[phase]["started_utc"] = started
    record[phase]["command"] = ["CODEX_BUNDLED_PYTHON3", child.name]
    record[phase]["outer_command_template"] = ["/usr/bin/sandbox-exec", "-p",
        "(version 1) (allow default) (deny network*)", "CODEX_BUNDLED_PYTHON3",
        "formal_runner.py", phase]
    record["formal_disposition"] = "IN_PROGRESS_" + phase.upper()
    write_record(record)
    code, error = capture_process([sys.executable, str(child)], HERE, stdout_path, stderr_path)
    finished = now()
    record = read_record()
    record[phase]["finished_utc"] = finished
    record[phase]["exit_code"] = code
    record[phase]["runner_error"] = error
    if stdout_path.is_file():
        record[phase]["stdout_bytes"] = stdout_path.stat().st_size
        record[phase]["stdout_sha256"] = file_sha(stdout_path)
    if stderr_path.is_file():
        record[phase]["stderr_bytes"] = stderr_path.stat().st_size
        record[phase]["stderr_sha256"] = file_sha(stderr_path)
    if phase == "candidate":
        completeness = "NOT_CHECKED"
        if code == 0:
            try:
                raw = json.loads(stdout_path.read_text(encoding="utf-8"))
                if (raw.get("allocation") == ALLOCATION and raw.get("case_count") == EXPECTED_CASES
                        and len(raw.get("rows", [])) == EXPECTED_CASES and raw.get("frame_count") == 21):
                    completeness = "PASS_STRUCTURAL_441_CASES"
                else:
                    completeness = "FAIL_STRUCTURAL_SCHEMA_OR_COVERAGE"
            except Exception as exc:
                completeness = "FAIL_STRUCTURAL_PARSE:" + type(exc).__name__
        record[phase]["output_completeness"] = completeness
        if code == 0 and completeness == "PASS_STRUCTURAL_441_CASES":
            record["formal_disposition"] = "CANDIDATE_OK_AUDIT_PENDING"
        else:
            record["formal_disposition"] = "HOLD_CANDIDATE_OR_RUNNER_CUSTODY"
    else:
        audit_status = None
        try:
            audit_status = json.loads(stdout_path.read_text(encoding="utf-8")).get("status")
        except Exception:
            audit_status = None
        record[phase]["reported_status"] = audit_status
        record["formal_disposition"] = audit_status or ("HOLD_AUDITOR_RUNNER_CUSTODY" if code is None else "FAIL_AUDIT")
    write_record(record)
    return 0 if code == 0 else 1


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: formal_runner.py candidate|auditor")
    return run_child(sys.argv[1])


if __name__ == "__main__":
    raise SystemExit(main())
