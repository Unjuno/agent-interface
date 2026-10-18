from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import subprocess
import sys

OUT = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path(__file__).resolve().parents[4]
MANIFEST_PATH = OUT / "IMPORT_CLOSURE.json"
expected = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
commit = expected["source_commit"]
assert subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=REPO, text=True).strip() == commit

roots = {"research/doom", "research/live_control", "research/observation_gating"}
allow = {"vizdoom", "Xlib", "PIL", "numpy", "cv2", "mss", "requests", "psutil", "yaml"}
prefixes = ("executor_", "lease", "input_owner_", "input_transition_owner_", "doom_", "map01_", "session_", "independent_", "main_thread_", "action_", "coast_")
paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", commit], cwd=REPO, text=True).splitlines()
modules: dict[str, list[str]] = {}
for rel in paths:
    parent, name = rel.rsplit("/", 1) if "/" in rel else ("", rel)
    if name.endswith(".py") and parent in roots:
        modules.setdefault(name[:-3], []).append(rel)
seen: set[str] = set()
external: set[str] = set()
unresolved: set[str] = set()
queue = list(expected["entrypoints"])
assert all(p in paths for p in queue), "entrypoint missing from pinned source"
while queue:
    rel = queue.pop(0)
    if rel in seen:
        continue
    raw = subprocess.check_output(["git", "show", f"{commit}:{rel}"], cwd=REPO)
    seen.add(rel)
    for node in ast.walk(ast.parse(raw.decode("utf-8"))):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        else:
            continue
        for name in names:
            top = name.split(".")[0]
            if top in sys.stdlib_module_names:
                continue
            choices = modules.get(top, [])
            if choices:
                candidate = next((p for p in choices if p.startswith("research/doom/")), None)
                candidate = candidate or next((p for p in choices if p.startswith("research/live_control/")), None)
                queue.append(candidate or choices[0])
            elif top in allow:
                external.add(top)
            elif top.startswith(prefixes):
                unresolved.add(name)
assert not unresolved, f"unresolved repository imports: {sorted(unresolved)}"
derived = []
for path in sorted(seen):
    raw = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=REPO)
    derived.append({
        "path": path,
        "git_blob_sha1": subprocess.check_output(["git", "hash-object", "--stdin"], cwd=REPO, input=raw).decode().strip(),
        "sha256": hashlib.sha256(raw).hexdigest(),
    })
assert len(derived) == len({r["path"] for r in derived})
assert len(derived) == expected["source_count"]
assert derived == expected["sources"], "source path/blob/content digest mismatch"
assert sorted(external) == expected["external_import_roots"]
assert expected["unresolved_repository_imports"] == []
print(f"PASS_STATIC_IMPORT_CLOSURE: commit={commit} files={len(derived)} unresolved=0 external={','.join(sorted(external))}")
