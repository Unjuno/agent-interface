from __future__ import annotations
import ast
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
manifest = json.loads((ROOT / 'IMPORT_CLOSURE.json').read_text(encoding='utf-8'))
commit = manifest['source_commit']
resolved = subprocess.check_output(['git', 'rev-parse', commit], text=True).strip()
assert resolved == commit, 'source commit is no longer resolvable'
all_paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', commit], text=True, encoding='utf-8').splitlines()
flat_roots = {'research/doom', 'research/live_control', 'research/observation_gating'}
modules: dict[str, list[str]] = {}
for rel in all_paths:
    if rel.endswith('.py') and rel.rsplit('/', 1)[0] in flat_roots:
        modules.setdefault(rel.rsplit('/', 1)[-1][:-3], []).append(rel)
seeds = manifest['entrypoints']
seen: set[str] = set()
external: set[str] = set()
unresolved: set[str] = set()
queue = list(seeds)
external_allowlist = {'vizdoom', 'Xlib', 'PIL', 'numpy', 'cv2', 'mss', 'requests', 'psutil', 'yaml'}
local_prefixes = ('executor_', 'lease', 'input_owner_', 'input_transition_owner_', 'doom_', 'map01_', 'session_', 'independent_', 'main_thread_', 'action_', 'coast_')
while queue:
    rel = queue.pop(0)
    if rel in seen:
        continue
    raw = subprocess.check_output(['git', 'show', f'{commit}:{rel}'])
    tree = ast.parse(raw.decode('utf-8'))
    seen.add(rel)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        else:
            continue
        for name in names:
            top = name.split('.')[0]
            if top in sys.stdlib_module_names:
                continue
            choices = modules.get(top, [])
            if choices:
                candidate = next((path for path in choices if path.startswith('research/doom/')), None)
                candidate = candidate or next((path for path in choices if path.startswith('research/live_control/')), None)
                queue.append(candidate or choices[0])
            elif top in external_allowlist:
                external.add(top)
            elif top.startswith(local_prefixes):
                unresolved.add(name)
rows = {row['path']: row['git_blob_sha1'] for row in manifest['sources']}
assert set(rows) == seen, f"closure mismatch: missing={sorted(seen-set(rows))}; extra={sorted(set(rows)-seen)}"
assert not unresolved, f'unresolved local imports: {sorted(unresolved)}'
assert sorted(external) == manifest['external_import_roots'], 'external import set changed'
for path, expected in rows.items():
    raw = subprocess.check_output(['git', 'show', f'{commit}:{path}'])
    actual = subprocess.check_output(['git', 'hash-object', '--stdin'], input=raw).decode().strip()
    assert actual == expected, f'blob mismatch: {path}'
assert manifest['execution'] == {
    'candidate_executed': False,
    'container_started': False,
    'display_or_game_used': False,
    'model_or_input_used': False,
}
print(f"PASS_STATIC_IMPORT_CLOSURE: commit={commit} files={len(seen)} unresolved=0 external={','.join(sorted(external))}")
