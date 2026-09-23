"""Run and retain Research Preview acceptance on the intended WSLg host.

This runner does not weaken gates or retry a failed live allocation. Each command is
executed once and its stdout/stderr/return code are retained under a new output dir.
Use --live to consume the one fresh no-retry golden run required for final acceptance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys
import time


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def run_step(root: Path, out: Path, index: int, name: str, command: list[str]) -> dict:
    started = time.time_ns()
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True)
    ended = time.time_ns()
    stem = f"{index:02d}-{name}"
    (out / f"{stem}.stdout.txt").write_text(completed.stdout, encoding="utf-8", newline="\n")
    (out / f"{stem}.stderr.txt").write_text(completed.stderr, encoding="utf-8", newline="\n")
    parsed = None
    for candidate in (completed.stdout, completed.stderr):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        else:
            break
    row = {
        "name": name,
        "command": command,
        "returncode": completed.returncode,
        "started_ns": started,
        "ended_ns": ended,
        "elapsed_ns": ended - started,
        "parsed_json": parsed,
    }
    dump(out / f"{stem}.json", row)
    return row


def git_revision(root: Path) -> str | None:
    if not (root / ".git").exists():
        return None
    completed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True)
    return completed.stdout.strip() if completed.returncode == 0 else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out", type=Path, required=True,
                        help="New acceptance directory; refusing overwrite preserves first outcome.")
    parser.add_argument("--live", action="store_true",
                        help="Run the one fresh no-retry golden allocation and audit-live.")
    parser.add_argument("--seed", type=int, default=991029)
    args = parser.parse_args()
    root = args.root.resolve(); out = args.out.resolve()
    if out.exists():
        parser.exit(2, f"refusing to reuse acceptance directory: {out}\n")
    out.mkdir(parents=True)
    steps: list[dict] = []
    base = {
        "schema": "agent_interface_supported_host_acceptance_v1",
        "root": str(root),
        "revision": git_revision(root),
        "host": {"platform": platform.platform(), "python": sys.version},
        "live_requested": args.live,
        "seed": args.seed,
        "automatic_retry": False,
    }
    dump(out / "context.json", base)

    commands = [
        ("preflight", [sys.executable, "release/first_run_smoke_v1/preflight.py", "--root", "."]),
        ("setup", ["./runtime/setup-golden-demo-v3.sh"]),
        ("doctor", ["./runtime/golden-demo-v3.sh", "doctor"]),
        ("audit-retained", ["./runtime/golden-demo-v3.sh", "audit-retained"]),
    ]
    for index, (name, command) in enumerate(commands, 1):
        row = run_step(root, out, index, name, command); steps.append(row)
        if row["returncode"] != 0:
            report = {**base, "status": "FAIL_SUPPORTED_HOST_ACCEPTANCE", "passed": False,
                      "failed_step": name, "steps": steps}
            dump(out / "acceptance.json", report)
            print(json.dumps(report, indent=2))
            return 1

    if not args.live:
        report = {**base, "status": "PASS_SUPPORTED_HOST_PREFIX_ONLY", "passed": False,
                  "release_ready": False,
                  "open_gate": "fresh no-retry run + audit-live require explicit --live",
                  "steps": steps}
        dump(out / "acceptance.json", report)
        print(json.dumps(report, indent=2))
        return 0

    live_out = out / "fresh-golden-run"
    live = run_step(root, out, 5, "run",
                    ["./runtime/golden-demo-v3.sh", "run", "--out", str(live_out),
                     "--seed", str(args.seed)])
    steps.append(live)
    if live["returncode"] != 0:
        report = {**base, "status": "FAIL_SUPPORTED_HOST_ACCEPTANCE", "passed": False,
                  "failed_step": "run", "steps": steps, "live_output": str(live_out)}
        dump(out / "acceptance.json", report); print(json.dumps(report, indent=2)); return 1
    audit = run_step(root, out, 6, "audit-live",
                     ["./runtime/golden-demo-v3.sh", "audit-live", str(live_out)])
    steps.append(audit)
    audit_pass = audit["returncode"] == 0 and isinstance(audit["parsed_json"], dict) and audit["parsed_json"].get("passed") is True
    report = {**base,
              "status": "PASS_SUPPORTED_HOST_ACCEPTANCE" if audit_pass else "FAIL_SUPPORTED_HOST_ACCEPTANCE",
              "passed": audit_pass, "release_ready": audit_pass,
              "failed_step": None if audit_pass else "audit-live",
              "steps": steps, "live_output": str(live_out)}
    dump(out / "acceptance.json", report)
    print(json.dumps(report, indent=2))
    return 0 if audit_pass else 1

if __name__ == "__main__":
    raise SystemExit(main())
