"""Source-first, non-executing dependency inventory for #2256."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCES = {
    "runtime/kernel/contracts.py": "3d24fb5b28ae7812c71c6c1fedd3439d1473f0b3",
    "runtime/kernel/lifecycle.py": "0735f1b2bc4f8c8c66a16cd0687a8b631c99f0b3",
    "runtime/cli_v1/api.py": "5674bd39e3cb2170095f476dac90e2a781f4f77a",
}

def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def inventory(path: Path) -> dict:
    data = path.read_bytes()
    tree = ast.parse(data.decode("utf-8"), filename=str(path))
    imports = []
    calls = []
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append((node.module or "") + (":" + ",".join(a.name for a in node.names)))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            calls.append(node.func.attr)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
    return {
        "blob_sha": blob_sha(data),
        "imports": sorted(set(imports)),
        "calls": sorted(set(calls)),
        "classes": sorted(set(classes)),
    }

def main() -> None:
    rows = {}
    for rel, expected in SOURCES.items():
        path = ROOT / rel
        row = inventory(path)
        assert row["blob_sha"] == expected, (rel, row["blob_sha"], expected)
        rows[rel] = row
    assert "runtime.kernel.lifecycle:RequestLifecycle" not in rows["runtime/kernel/lifecycle.py"]["imports"]
    required = {"close", "open_session", "dispatch"}
    assert required <= set(rows["runtime/cli_v1/api.py"]["calls"])
    result = {
        "status": "HOLD_RUNTIME_FAULT_INJECTION_REQUIRED",
        "issue": 2256,
        "source_rows": len(rows),
        "source_blobs_verified": True,
        "execution": "AST_ONLY_NO_RUNTIME_IMPORT_OR_EXECUTION",
        "declared_boundaries": [
            "kernel contracts and lifecycle",
            "CLI backend selection/open/dispatch/close facade",
        ],
        "observed_dependency_classes": [
            "Python stdlib/dataclasses/enum/typing/AST audit",
            "runtime selector/backend session",
            "backend close cleanup hook",
            "observation/binding/authority/receipt objects",
        ],
        "not_observed": [
            "IPC/display-server/scheduler/kernel failure domains",
            "wall-clock release latency",
            "actuator residual state",
            "fault injection",
            "task/effect outcome",
        ],
        "claims_excluded": ["PASS safety-plane completeness", "timely release", "GUI", "model", "network", "production"],
    }
    print(json.dumps(result, sort_keys=True))
    print("INDEPENDENT_AUDIT_PASS source_blobs=3 ast_only=1 runtime_fault_injection=0")

if __name__ == "__main__":
    main()
