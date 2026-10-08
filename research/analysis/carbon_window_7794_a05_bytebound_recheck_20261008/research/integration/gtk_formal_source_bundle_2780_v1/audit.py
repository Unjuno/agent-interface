"""Offline immutable-source audit for the GTK #2606 successor."""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ROOTS = (
    "research/integration/golden_v3_second_domain_2246_v1/formal_matrix_runner.py",
    "research/integration/golden_v3_second_domain_2246_v1/formal_matrix_2606/matrix_gate.py",
    "research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py",
)

def resolve_module(module: str, current: Path, level: int) -> Path | None:
    if level:
        base = current.parent
        for _ in range(level - 1): base = base.parent
        return base / module.replace(".", "/") if module else base
    if module.startswith(("runtime", "research")):
        return ROOT / module.replace(".", "/")
    return None

def closure() -> set[Path]:
    seen, todo = set(), [ROOT / p for p in ROOTS]
    while todo:
        path = todo.pop()
        if path in seen: continue
        if not path.exists(): raise AssertionError(f"missing root: {path.relative_to(ROOT)}")
        seen.add(path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): imports += [(a.name, 0) for a in node.names]
            elif isinstance(node, ast.ImportFrom): imports.append((node.module or "", node.level))
        for module, level in imports:
            candidate = resolve_module(module, path, level)
            if candidate is None: continue
            matches = [candidate.with_suffix(".py"), candidate / "__init__.py"]
            local = next((item for item in matches if item.exists()), None)
            if local is not None: todo.append(local)
    return seen

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    actual = closure()
    manifest = {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(actual)}
    manifest_path = HERE / "MANIFEST.json"
    if not manifest_path.exists():
        manifest_path.write_text(json.dumps({"roots": list(ROOTS), "files": manifest}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    prior = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = prior["files"]
    if set(expected) != set(manifest): raise AssertionError("closure changed")
    for name, sha in expected.items():
        path = ROOT / name
        if not path.exists() or digest(path) != sha: raise AssertionError(f"hash mismatch: {name}")
    print(json.dumps({"status": "PASS_SOURCE_BUNDLE_FREEZE", "files": len(manifest), "bytes": sum((ROOT / n).stat().st_size for n in manifest)}, sort_keys=True))
    return 0

if __name__ == "__main__": raise SystemExit(main())
