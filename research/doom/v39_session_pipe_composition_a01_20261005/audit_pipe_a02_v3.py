"""Independent read-only audit of the V39 child-pipe A01 raw result."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(REPO), *args], text=True).strip()


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(REPO), *args])


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    freeze = json.loads((HERE / "FREEZE-A02.json").read_text(encoding="utf-8"))
    out = HERE / "results" / "a02"
    input_path = HERE / "INPUT_EVENT.json"
    input_event = json.loads(input_path.read_text(encoding="utf-8"))
    stdout = (out / "CHILD_STDOUT.jsonl").read_text(encoding="utf-8")
    stderr = (out / "CHILD_STDERR.txt").read_text(encoding="utf-8")
    received = json.loads((out / "CONTROLLER_RECEIVED.json").read_text(encoding="utf-8"))
    result = json.loads((out / "RESULT.json").read_text(encoding="utf-8"))
    receipt = json.loads((out / "RUN_RECEIPT.json").read_text(encoding="utf-8"))

    checks: list[dict[str, object]] = []
    for field in ("candidate", "auditor"):
        record = freeze[field]
        actual = sha(HERE / record["file"])
        checks.append({"check": f"{field}_sha256", "pass": actual == record["sha256"], "actual": actual})

    for name, ref in {
        "main": ("origin/main", freeze["main"]),
        "pr_7602": ("refs/remotes/pr/7602", freeze["components"]["pr_7602"]),
        "pr_7750": ("refs/remotes/pr/7750", freeze["components"]["pr_7750"]),
        "pr_7769": ("refs/remotes/pr/7769", freeze["components"]["pr_7769"]),
    }.items():
        actual = git("rev-parse", ref[0])
        checks.append({"check": f"{name}_ref", "pass": actual == ref[1], "actual": actual})

    tree = freeze["composition_tree"]
    for path, expected in freeze["source_blobs"].items():
        actual = git("rev-parse", f"{tree}:{path}")
        raw = git_bytes("show", f"{tree}:{path}")
        expected_sha256 = (freeze["input"]["sha256"] if path.endswith("published-events.jsonl") else freeze["source_sha256"][Path(path).name])
        raw_sha256 = hashlib.sha256(raw).hexdigest()
        checks.append({
            "check": f"source_blob:{path}",
            "pass": actual == expected and raw_sha256 == expected_sha256,
            "actual": actual,
            "sha256": raw_sha256,
        })

    session_source = git_bytes("show", f"{tree}:research/doom/session_map01_v12.py")
    nodes = [node for node in ast.walk(ast.parse(session_source))
             if isinstance(node, ast.FunctionDef) and node.name == "emit"]
    if len(nodes) == 1:
        class NonlocalToGlobal(ast.NodeTransformer):
            def visit_Nonlocal(self, node: ast.Nonlocal) -> ast.Global:
                return ast.Global(names=node.names)
        emit_node = NonlocalToGlobal().visit(nodes[0])
        emit_source = ast.unparse(emit_node)
        emitter_hash = hashlib.sha256(emit_source.encode("utf-8")).hexdigest()
    else:
        emitter_hash = None
    checks.append({
        "check": "emitter_ast_hash",
        "pass": emitter_hash is not None and emitter_hash == receipt.get("exact_emitter_function_sha256"),
        "actual": emitter_hash,
    })

    input_hash = sha(input_path)
    checks.append({
        "check": "input_hash_and_size",
        "pass": input_hash == freeze["input"]["sha256"]
        and input_path.stat().st_size == freeze["input"]["bytes"],
        "actual": input_hash,
    })
    lines = [line for line in stdout.splitlines() if line]
    parsed = [json.loads(line) for line in lines]
    checks.append({
        "check": "one_pipe_row_and_roundtrip",
        "pass": (
            len(parsed) == 1
            and parsed[0] == received
            and received.get("event") == "input_released"
            and received.get("id") == input_event.get("id")
            and received.get("emit_ns").__class__ is int
            and {key: value for key, value in received.items() if key != "emit_ns"} == input_event
        ),
    })

    event_log = (out / "events.jsonl").read_text(encoding="utf-8")
    delivered_log = (out / "delivered.jsonl").read_text(encoding="utf-8")
    checks.append({
        "check": "writer_logs_match_pipe",
        "pass": (
            len(event_log.splitlines()) == 1
            and len(delivered_log.splitlines()) == 1
            and json.loads(event_log) == parsed[0]
            and json.loads(delivered_log) == parsed[0]
        ),
    })

    per_key = received.get("owner_release", {}).get("per_key_release_measurements", [])
    checks.append({
        "check": "authority_and_nested_release",
        "pass": (
            received.get("grants_input_authority") is False
            and len(per_key) == freeze["input"]["per_key_release_count"]
            and all(row.get("grants_input_authority") is False for row in per_key)
        ),
    })
    checks.append({
        "check": "process_closure",
        "pass": (
            receipt.get("child_returncode") == 0
            and receipt.get("stderr_bytes") == 0
            and receipt.get("stdout_line_count") == 1
            and receipt.get("controller_received_count") == 1
            and result.get("reader_errors") == []
            and result.get("reader_thread_joined") is True
            and stderr == ""
        ),
    })
    checks.append({
        "check": "result_disposition",
        "pass": (
            result.get("disposition") == "PASS_CHILD_PIPE_TRANSPORT_SCOPED"
            and result.get("child_exit_code") == 0
            and result.get("stdout_lines") == 1
            and result.get("controller_rows") == 1
            and result.get("authority_granted") is False
            and result.get("per_key_release_count") == 2
        ),
    })

    raw_paths = [input_path, out / "CHILD_STDOUT.jsonl", out / "CHILD_STDERR.txt",
                 out / "events.jsonl", out / "delivered.jsonl",
                 out / "CONTROLLER_RECEIVED.json", out / "RESULT.json", out / "RUN_RECEIPT.json"]
    audit = {
        "schema": "v39-session-child-pipe-audit-a02-v3",
        "disposition": "PASS_AUDIT" if all(check["pass"] for check in checks) else "FAIL_AUDIT",
        "checks": checks,
        "raw_sha256": {path.name: sha(path) for path in raw_paths},
    }
    (HERE / "AUDIT_A02_V3.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0 if audit["disposition"] == "PASS_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
