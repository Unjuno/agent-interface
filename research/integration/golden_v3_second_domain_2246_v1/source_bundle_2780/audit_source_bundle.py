"""Fail-closed offline audit for the #2780 GTK source bundle."""
from __future__ import annotations
import argparse, ast, hashlib, json
from pathlib import Path

REQUIRED = (
    "research/integration/golden_v3_second_domain_2246_v1/formal_matrix_runner.py",
    "research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py",
    "research/integration/golden_v3_second_domain_2246_v1/formal_matrix_2606/matrix_gate.py",
    "runtime/cli_v1/golden_v3.py",
    "runtime/core_v1/contract.py",
)
LOCAL_ROOTS = ("runtime", "research")

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def module_path(root: Path, module: str) -> Path | None:
    if module.split(".", 1)[0] not in LOCAL_ROOTS:
        return None
    rel = Path(*module.split("."))
    candidate = root / (str(rel) + ".py")
    if candidate.is_file():
        return candidate
    package = root / rel / "__init__.py"
    return package if package.is_file() else None

def imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module)
    return names

def audit(root: Path) -> dict[str, object]:
    missing = [item for item in REQUIRED if not (root / item).is_file()]
    discovered: set[str] = set()
    queue = [root / item for item in REQUIRED if (root / item).is_file()]
    unresolved: list[str] = []
    while queue:
        path = queue.pop()
        rel = path.relative_to(root).as_posix()
        if rel in discovered:
            continue
        discovered.add(rel)
        for name in imports(path):
            resolved = module_path(root, name)
            if resolved is not None and resolved.relative_to(root).as_posix() not in discovered:
                queue.append(resolved)
            elif name.split(".", 1)[0] in LOCAL_ROOTS and resolved is None:
                unresolved.append(f"{rel}:{name}")
    hashes = {item: sha256(root / item) for item in sorted(discovered)}
    reasons = []
    if missing:
        reasons.append("missing_required:" + ",".join(missing))
    if unresolved:
        reasons.append("unresolved_local_import:" + ",".join(sorted(unresolved)))
    return {
        "decision": "PASS_SOURCE_BUNDLE_FREEZE" if not reasons else "STOP_SOURCE_BUNDLE",
        "required": list(REQUIRED),
        "discovered": sorted(discovered),
        "hashes": hashes,
        "reasons": reasons,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    result = audit(args.root.resolve())
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.manifest:
        args.manifest.write_text(text, encoding="utf-8")
    return 0 if result["decision"] == "PASS_SOURCE_BUNDLE_FREEZE" else 1

if __name__ == "__main__":
    raise SystemExit(main())
