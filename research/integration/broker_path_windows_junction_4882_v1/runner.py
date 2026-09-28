"""Run the frozen Windows path cases once; no broker/model subprocess exists."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from path_policy import resolve_host_path


CASES = [
    ("repo_root", "/repo", "accept-root"),
    ("workspace_root", "/workspace", "accept-root"),
    ("regular_file", "/repo/input.txt", "accept-file"),
    ("in_root_junction", "/workspace/in-junction/data.txt", "accept-file"),
    ("external_junction", "/repo/external-junction/secret.txt", "reject-value-error"),
    ("lexical_traversal", "/repo/../outside/secret.txt", "reject-value-error"),
    ("encoded_traversal", "/repo/%2e%2e/outside/secret.txt", "reject-value-error"),
    ("absolute_host_path", None, "reject-value-error"),
    ("missing_path", "/repo/missing.txt", "reject-file-not-found"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_junction(link: Path, target: Path) -> dict:
    command = f'mklink /J "{link}" "{target}"'
    completed = subprocess.run(
        ["cmd.exe", "/d", "/c", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=10,
    )
    return {
        "command": "cmd.exe /d /c mklink /J <link> <target>",
        "returncode": completed.returncode,
        "setup_ok": completed.returncode == 0 and link.is_junction(),
    }


def run(output: Path) -> int:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite frozen output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter_ns()
    fixture = Path(tempfile.mkdtemp(prefix="broker-path-junction-4882-02-"))
    root = fixture / "repo"
    outside = fixture / "outside"
    internal = root / "internal"
    root.mkdir()
    outside.mkdir()
    internal.mkdir()
    (root / "input.txt").write_text("in-root\n", encoding="utf-8")
    (internal / "data.txt").write_text("internal-junction\n", encoding="utf-8")
    (outside / "secret.txt").write_text("outside\n", encoding="utf-8")

    setup = [
        create_junction(root / "in-junction", internal),
        create_junction(root / "external-junction", outside),
    ]
    if not all(item["setup_ok"] for item in setup):
        result = {
            "schema": "broker_path_windows_junction_4882_raw_v1",
            "allocation": "broker-path-windows-junction-4882-20260928-02",
            "source_main": "020db8709de3321332ef22ea3aa60bd4dacdca77",
            "candidate_git_blob": "cdd0e3d57e08a316fc9df6b55abca8c740db070d",
            "candidate_sha256": sha256(Path(__file__).with_name("path_policy.py")),
            "runner_sha256": sha256(Path(__file__).resolve()),
            "environment": {"python": sys.version, "platform": sys.platform, "os_name": os.name},
            "fixture": {"setup": setup, "broker_subprocess_invocations": 0},
            "status": "STOP_SETUP_JUNCTION_UNAVAILABLE",
            "rows": [],
        }
        output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"allocation": result["allocation"], "status": result["status"],
                          "output": "results/allocation-02/RAW.json"}))
        return 2
    rows = []
    absolute = str(outside / "secret.txt")
    for case_id, value, expected in CASES:
        value = absolute if case_id == "absolute_host_path" else value
        try:
            actual = resolve_host_path(value, root)
            actual_rel = Path(actual).resolve(strict=True).relative_to(fixture).as_posix()
            rows.append({
                "case_id": case_id,
                "input": "<absolute-outside-secret>" if case_id == "absolute_host_path" else value,
                "input_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest()
                if case_id == "absolute_host_path" else None,
                "expected": expected,
                "outcome": "accepted",
                "actual_relative_to_fixture": actual_rel,
                "exception": None,
            })
        except Exception as exc:  # Raw type is audited against a fixed case table.
            rows.append({
                "case_id": case_id,
                "input": "<absolute-outside-secret>" if case_id == "absolute_host_path" else value,
                "input_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest()
                if case_id == "absolute_host_path" else None,
                "expected": expected,
                "outcome": "rejected",
                "actual_relative_to_fixture": None,
                "exception": type(exc).__name__,
            })

    result = {
        "schema": "broker_path_windows_junction_4882_raw_v1",
        "allocation": "broker-path-windows-junction-4882-20260928-02",
        "source_main": "020db8709de3321332ef22ea3aa60bd4dacdca77",
        "candidate_git_blob": "cdd0e3d57e08a316fc9df6b55abca8c740db070d",
        "candidate_sha256": sha256(Path(__file__).with_name("path_policy.py")),
        "runner_sha256": sha256(Path(__file__).resolve()),
        "environment": {"python": sys.version, "platform": sys.platform, "os_name": os.name},
        "fixture": {
            "root_relative_to_fixture": "repo",
            "outside_relative_to_fixture": "outside",
            "internal_target_relative_to_fixture": "repo/internal",
            "in_root_junction_relative_to_fixture": "repo/in-junction",
            "external_junction_relative_to_fixture": "repo/external-junction",
            "setup": setup,
            "broker_subprocess_invocations": 0,
        },
        "started_ns": started,
        "ended_ns": time.perf_counter_ns(),
        "status": "RUN_COMPLETE",
        "rows": rows,
        "cleanup": "pending independent audit",
    }
    output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"allocation": result["allocation"], "rows": len(rows), "status": result["status"],
                      "output": "results/allocation-02/RAW.json"}))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: runner.py RAW.json")
    raise SystemExit(run(Path(sys.argv[1])))
