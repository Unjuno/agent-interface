"""Offline source-completeness and import/hash audit for #2780."""
from hashlib import sha256
from importlib import import_module
from pathlib import Path
import json
import sys
import ast

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
REQUIRED = [
    ROOT / "research/integration/golden_v3_second_domain_2246_v1/formal_matrix_runner.py",
    ROOT / "research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py",
    ROOT / "research/integration/golden_v3_second_domain_2246_v1/formal_matrix_2606/matrix_gate.py",
]

def digest(path: Path) -> str:
    h = sha256()
    if path.is_file():
        h.update(path.read_bytes())
    else:
        for item in sorted(path.rglob("*")):
            if item.is_file():
                h.update(str(item.relative_to(ROOT)).replace("\\", "/").encode())
                h.update(item.read_bytes())
    return h.hexdigest()

def runtime_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names if alias.name.startswith("runtime"))
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("runtime"):
            found.add(node.module)
    return found

def module_exists(name: str) -> bool:
    rel = ROOT.joinpath(*name.split("."))
    return rel.with_suffix(".py").exists() or (rel / "__init__.py").exists()

def main() -> int:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED + [ROOT / "runtime"] if not p.exists()]
    if missing:
        print(json.dumps({"passed": False, "missing": missing}, sort_keys=True))
        return 1
    roots = REQUIRED
    pending = set()
    seen = set()
    while roots:
        path = roots.pop()
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        for name in runtime_imports(path):
            if not module_exists(name):
                print(json.dumps({"passed": False, "missing_runtime_import": name}, sort_keys=True))
                return 1
            rel = ROOT.joinpath(*name.split("."))
            candidate = rel.with_suffix(".py")
            roots.append(candidate if candidate.exists() else rel / "__init__.py")
    import_module("runtime.cli_v1.golden_v3")
    import_module("runtime.core_v1.contract")
    paths = REQUIRED + [ROOT / "runtime"]
    print(json.dumps({"passed": True, "paths": {str(p.relative_to(ROOT)): digest(p) for p in paths}}, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
