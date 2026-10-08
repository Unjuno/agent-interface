"""Current-main, source-first dependency inventory for #2256."""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCES = {
    "runtime/kernel/contracts.py": "3d24fb5b28ae7812c71c6c1fedd3439d1473f0b8",
    "runtime/kernel/lifecycle.py": "0735f1b2bc4f8c8c66a16cd0687a8b631c99f0b3",
    "runtime/cli_v1/api.py": "58e5489796959f120d973b595f36ed3d808533b3",
}

def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def inventory(path: Path) -> dict:
    data = path.read_bytes()
    tree = ast.parse(data.decode("utf-8"), filename=str(path))
    imports, calls, classes = [], [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append((node.module or "") + ":" + ",".join(a.name for a in node.names))
        elif isinstance(node, ast.Call):
            calls.append(node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", ""))
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
    return {"blob_sha": blob_sha(data), "imports": sorted(set(imports)),
            "calls": sorted(set(filter(None, calls))), "classes": sorted(set(classes))}

def main() -> None:
    rows = {}
    for rel, expected in SOURCES.items():
        row = inventory(ROOT / rel)
        head_blob = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", f"HEAD:{rel}"], text=True
        ).strip()
        assert head_blob == expected, (rel, head_blob, expected)
        row["head_blob"] = head_blob
        rows[rel] = row
    assert "runtime.kernel.lifecycle:RequestLifecycle" not in rows["runtime/kernel/lifecycle.py"]["imports"]
    assert {"open_session", "dispatch"} <= set(rows["runtime/cli_v1/api.py"]["calls"])
    result = {"status": "HOLD_RUNTIME_FAULT_INJECTION_REQUIRED", "issue": 2256,
              "base_ref": "main", "source_rows": len(rows),
              "source_blobs_verified": True, "execution": "AST_ONLY_NO_RUNTIME_IMPORT_OR_EXECUTION",
              "runtime_fault_injection": "NOT_RUN", "rows": rows}
    out = Path(__file__).with_name("RESULT.json")
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("INDEPENDENT_AUDIT_PASS source_blobs=3 ast_only=1 runtime_fault_injection=0")

if __name__ == "__main__":
    main()
