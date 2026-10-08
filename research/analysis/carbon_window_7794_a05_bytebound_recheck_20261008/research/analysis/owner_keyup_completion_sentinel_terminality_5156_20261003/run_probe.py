"""One-shot synthetic order probe for the frozen #5156 T3 auditor."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
T3 = ROOT / "research/live_control/owner_keyup_keymap_witness_5156_t3_v1"
FREEZE_PATH = PACKAGE / "FREEZE.json"
OUT = PACKAGE / "results/formal-01"


def dump_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    source_commit = git("rev-parse", "HEAD")
    source_problems = []
    if source_commit != freeze["main_commit"]:
        source_problems.append("HEAD differs from frozen main commit")
    for relpath, identity in freeze["source_files"].items():
        path = ROOT / relpath
        if git("rev-parse", f"{freeze['main_commit']}:{relpath}") != identity["git_blob"]:
            source_problems.append(f"Git blob mismatch: {relpath}")
        if sha256(path.read_bytes()) != identity["sha256"]:
            source_problems.append(f"SHA-256 mismatch: {relpath}")
    if platform.python_version() != "3.14.5":
        source_problems.append("runtime differs from frozen Python 3.14.5")
    if source_problems:
        dump_json(OUT / "PREFLIGHT_STOP.json", {
            "status": "STOP_SOURCE_OR_RUNTIME_BINDING",
            "source_problems": source_problems,
            "candidate_invocations": 0,
        })
        return 2

    sys.path.insert(0, str(T3))
    old_cwd = Path.cwd()
    try:
        os.chdir(T3)
        import test_audit_formal_x11 as frozen_fixture  # noqa: E402
    finally:
        os.chdir(old_cwd)

    rows = copy.deepcopy(frozen_fixture.fixture_rows())
    completion = [row for row in rows if row.get("event") == "runner_complete"]
    if len(completion) != 1:
        dump_json(OUT / "PREFLIGHT_STOP.json", {
            "status": "STOP_INVALID_POSITIVE_FIXTURE",
            "completion_count": len(completion),
            "candidate_invocations": 0,
        })
        return 2
    marker = completion[0]
    body = [row for row in rows if row is not marker]
    marker = dict(marker)
    marker["raw_rows"] = len(body) + 1
    control_rows = body + [marker]
    treatment_rows = [marker] + copy.deepcopy(body)

    control_dir = OUT / "control"
    treatment_dir = OUT / "nonterminal"
    control_dir.mkdir(parents=True, exist_ok=False)
    treatment_dir.mkdir(parents=True, exist_ok=False)
    control_raw = control_dir / "raw.jsonl"
    treatment_raw = treatment_dir / "raw.jsonl"
    write_jsonl(control_raw, control_rows)
    write_jsonl(treatment_raw, treatment_rows)

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    rel_auditor = (T3 / "audit_formal_x11.py").relative_to(ROOT).as_posix()
    rel_expected = (T3 / "EXPECTED.json").relative_to(ROOT).as_posix()
    rel_package = PACKAGE.relative_to(ROOT).as_posix()
    command_records = []
    case_records = {}
    for name, raw_path, case_dir in (
        ("control", control_raw, control_dir),
        ("nonterminal", treatment_raw, treatment_dir),
    ):
        rel_raw = raw_path.relative_to(ROOT).as_posix()
        rel_audit = (case_dir / "audit.json").relative_to(ROOT).as_posix()
        command = ["python3", "-B", rel_auditor, rel_raw, rel_expected, rel_audit, "synthetic-cli"]
        started = datetime.now(timezone.utc).isoformat()
        completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, check=False)
        ended = datetime.now(timezone.utc).isoformat()
        (case_dir / "stdout.bin").write_bytes(completed.stdout)
        (case_dir / "stderr.bin").write_bytes(completed.stderr)
        (case_dir / "exit_code.txt").write_text(f"{completed.returncode}\n", encoding="ascii")
        case_records[name] = {
            "command": command,
            "started_utc": started,
            "ended_utc": ended,
            "exit_code": completed.returncode,
            "raw_sha256": sha256(raw_path.read_bytes()),
            "raw_rows": len(raw_path.read_text(encoding="utf-8").splitlines()),
            "stdout_sha256": sha256(completed.stdout),
            "stderr_sha256": sha256(completed.stderr),
            "audit_sha256": sha256((case_dir / "audit.json").read_bytes())
            if (case_dir / "audit.json").exists() else None,
        }
        command_records.append({"case": name, "command": command, "cwd": "."})

    control_rc = case_records["control"]["exit_code"]
    treatment_rc = case_records["nonterminal"]["exit_code"]
    if control_rc != 0:
        status = "STOP_INVALID_CONTROL_OR_PROVENANCE"
    elif treatment_rc == 0:
        status = "FINDING_NONTERMINAL_COMPLETION_ACCEPTED"
    elif treatment_rc == 1:
        status = "TERMINALITY_GUARD_ENFORCED"
    else:
        status = "FAIL_TARGET_INVOCATION"
    dump_json(OUT / "COMMANDS.json", command_records)
    dump_json(OUT / "ENVIRONMENT.json", {
        "python_version": sys.version,
        "platform": platform.platform(),
        "system": platform.system(),
        "source_commit": source_commit,
        "network_calls": 0,
        "resource_scope": "host-only Python CLI; no container, X server, GUI, input, game, model, or GPU",
    })
    dump_json(OUT / "CANDIDATE.json", {
        "status": status,
        "source_commit": source_commit,
        "candidate_cli_invocations": 2,
        "retry_count": 0,
        "cases": case_records,
    })
    print(json.dumps({"status": status, "control_exit": control_rc,
                      "nonterminal_exit": treatment_rc}, sort_keys=True))
    return 0 if status in {
        "FINDING_NONTERMINAL_COMPLETION_ACCEPTED",
        "TERMINALITY_GUARD_ENFORCED",
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())
