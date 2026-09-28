"""One-shot Windows NTFS junction candidate-resolver experiment."""
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

ALLOCATION = "broker-path-windows-junction-4882-20260928-03"
SOURCE_MAIN = "442ef765598971806dc5d671a223af7b3a711a5f"
CANDIDATE_BLOB = "cdd0e3d57e08a316fc9df6b55abca8c740db070d"
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


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def setup_junctions(script: Path, fixture: Path, root: Path, outside: Path) -> dict:
    cp = subprocess.run(
        ["pwsh.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-File", str(script),
         str(fixture), str(root), str(outside)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20,
        check=False,
    )
    def sanitize(text: str) -> str:
        return text.replace(str(fixture), "<fixture>").replace(str(fixture).replace("\\", "/"), "<fixture>")
    return {
        "command": "pwsh.exe -NoLogo -NoProfile -NonInteractive -File make_junctions.ps1 <fixture> <repo> <outside>",
        "returncode": cp.returncode,
        "stdout_sanitized": sanitize(cp.stdout),
        "stderr_sanitized": sanitize(cp.stderr),
        "setup_ok": cp.returncode == 0 and "JUNCTION_SETUP_OK" in cp.stdout,
    }


def main(output: Path) -> int:
    if output.exists():
        raise FileExistsError("refusing to overwrite allocation output")
    output.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter_ns()
    fixture = Path(tempfile.mkdtemp(prefix="broker-path-junction-4882-03-"))
    root, outside = fixture / "repo", fixture / "outside"
    (root / "internal").mkdir(parents=True)
    outside.mkdir()
    (root / "input.txt").write_text("in-root\n", encoding="utf-8")
    (root / "internal" / "data.txt").write_text("internal-junction\n", encoding="utf-8")
    (outside / "secret.txt").write_text("outside\n", encoding="utf-8")
    setup = setup_junctions(Path(__file__).with_name("make_junctions.ps1"), fixture, root, outside)
    common = {
        "schema": "broker_path_windows_junction_4882_v2_raw_v1",
        "allocation": ALLOCATION,
        "source_main": SOURCE_MAIN,
        "candidate_git_blob": CANDIDATE_BLOB,
        "candidate_sha256": sha(Path(__file__).with_name("path_policy.py")),
        "runner_sha256": sha(Path(__file__).resolve()),
        "fixture": {"root_relative": "repo", "outside_relative": "outside", "setup": setup,
                    "broker_subprocess_invocations": 0},
    }
    if not setup["setup_ok"]:
        result = {**common, "environment": {"python": sys.version, "platform": sys.platform, "os_name": os.name},
                  "status": "STOP_SETUP_JUNCTION_UNAVAILABLE", "rows": [], "started_ns": started,
                  "ended_ns": time.perf_counter_ns()}
        output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"allocation": ALLOCATION, "status": result["status"], "rows": 0}))
        return 2
    rows = []
    absolute = str(outside / "secret.txt")
    for case_id, value, expected in CASES:
        value = absolute if case_id == "absolute_host_path" else value
        try:
            actual = resolve_host_path(value, root)
            resolved = Path(actual).resolve(strict=True)
            rows.append({"case_id": case_id, "input": "<absolute-outside-secret>" if case_id == "absolute_host_path" else value,
                         "input_sha256": hashlib.sha256(value.encode()).hexdigest() if case_id == "absolute_host_path" else None,
                         "expected": expected, "outcome": "accepted",
                         "actual_relative_to_fixture": resolved.relative_to(fixture.resolve()).as_posix(), "exception": None})
        except Exception as exc:
            rows.append({"case_id": case_id, "input": "<absolute-outside-secret>" if case_id == "absolute_host_path" else value,
                         "input_sha256": hashlib.sha256(value.encode()).hexdigest() if case_id == "absolute_host_path" else None,
                         "expected": expected, "outcome": "rejected", "actual_relative_to_fixture": None,
                         "exception": type(exc).__name__})
    result = {**common, "environment": {"python": sys.version, "platform": sys.platform, "os_name": os.name},
              "started_ns": started, "ended_ns": time.perf_counter_ns(), "status": "RUN_COMPLETE", "rows": rows,
              "cleanup": "pending independent audit"}
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"allocation": ALLOCATION, "status": result["status"], "rows": len(rows)}))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: runner.py RAW.json")
    raise SystemExit(main(Path(sys.argv[1])))
