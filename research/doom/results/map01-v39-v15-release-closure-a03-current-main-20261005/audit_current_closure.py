from __future__ import annotations
import ast, hashlib, json, pathlib, subprocess, sys

OUT = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path(__file__).resolve().parents[4]
MANIFEST_PATH = OUT / 'IMPORT_CLOSURE.json'
manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
COMMIT = manifest['source_commit']
actual_main = subprocess.check_output(['git', 'rev-parse', 'origin/main'], cwd=REPO, text=True).strip()
assert actual_main == COMMIT, f'origin/main advanced: expected={COMMIT} actual={actual_main}'
ENTRYPOINTS = manifest['entrypoints']
FLAT_ROOTS = {'research/doom', 'research/live_control', 'research/observation_gating'}
EXTERNAL_ALLOWLIST = {'vizdoom', 'Xlib', 'PIL', 'numpy', 'cv2', 'mss', 'requests', 'psutil', 'yaml'}
LOCAL_PREFIXES = ('executor_', 'lease', 'input_owner_', 'input_transition_owner_', 'doom_', 'map01_', 'session_', 'independent_', 'main_thread_', 'action_', 'coast_')
all_paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', COMMIT], cwd=REPO, text=True).splitlines()
assert all(entry in all_paths for entry in ENTRYPOINTS), 'entrypoint missing from pinned source commit'
modules: dict[str, list[str]] = {}
for rel in all_paths:
    parent, name = rel.rsplit('/', 1) if '/' in rel else ('', rel)
    if name.endswith('.py') and parent in FLAT_ROOTS:
        modules.setdefault(name[:-3], []).append(rel)
seen: set[str] = set(); external: set[str] = set(); unresolved: set[str] = set(); queue = list(ENTRYPOINTS)
while queue:
    rel = queue.pop(0)
    if rel in seen: continue
    raw = subprocess.check_output(['git', 'show', f'{COMMIT}:{rel}'], cwd=REPO)
    tree = ast.parse(raw.decode('utf-8')); seen.add(rel)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module: names = [node.module]
        else: continue
        for name in names:
            top = name.split('.')[0]
            if top in sys.stdlib_module_names: continue
            choices = modules.get(top, [])
            if choices:
                candidate = next((p for p in choices if p.startswith('research/doom/')), None)
                candidate = candidate or next((p for p in choices if p.startswith('research/live_control/')), None)
                queue.append(candidate or choices[0])
            elif top in EXTERNAL_ALLOWLIST: external.add(top)
            elif top.startswith(LOCAL_PREFIXES): unresolved.add(name)
assert not unresolved, f'unresolved repository imports: {sorted(unresolved)}'
assert seen, 'empty import closure'
assert len(seen) == len(set(seen)), 'duplicate source closure entries'
source_rows=[]
for path in sorted(seen):
    raw=subprocess.check_output(['git','show',f'{COMMIT}:{path}'], cwd=REPO)
    source_rows.append({'path':path,'git_blob_sha1':subprocess.check_output(['git','hash-object','--stdin'], cwd=REPO,input=raw).decode().strip(),'sha256':hashlib.sha256(raw).hexdigest()})
manifest={
 'schema':'static-python-import-closure-v1','run_id':'MAP01-V39-V15-RELEASE-CLOSURE-A03-CURRENT-MAIN-20261005',
 'classification':'current-main static source preflight only; not candidate or formal experiment',
 'source_ref':'origin/main','source_commit':COMMIT,'entrypoints':ENTRYPOINTS,
 'closure_method':'Recursive Python AST scan of import/import-from statements over flat module directories research/doom, research/live_control, research/observation_gating; repository-only module resolution prefers research/doom then research/live_control.',
 'source_count':len(seen),'sources':source_rows,'external_import_roots':sorted(external),'unresolved_repository_imports':[],
 'limitations':['Does not execute or import candidate or production code.','Does not prove dynamic imports, native/runtime dependency closure, package side effects, GUI/display behavior, or OS input release.','A future candidate needs a new exact source, image, dependency, configuration, and raw-output freeze.','Does not satisfy Issue #59 live threat-exposure, useful-recovery, or task-effect gates.'],
 'execution':{'candidate_executed':False,'container_started':False,'display_or_game_used':False,'model_or_input_used':False},
 'next_gate':'Treat this exact static source closure as input to a separately frozen deterministic Fake-X startup/owner-identity candidate only after the relevant local resource and allocation policy permit it; never treat static closure as dynamic startup evidence.'}
expected = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
assert manifest == expected, 'derived closure differs from the frozen current-main manifest'
for row in expected['sources']:
 raw = subprocess.check_output(['git','show',f"{COMMIT}:{row['path']}"], cwd=REPO)
 assert subprocess.check_output(['git','hash-object','--stdin'],input=raw,cwd=REPO).decode().strip() == row['git_blob_sha1'], row['path']
 assert hashlib.sha256(raw).hexdigest() == row['sha256'], row['path']
print(f"PASS_STATIC_IMPORT_CLOSURE: commit={COMMIT} files={len(seen)} unresolved=0 external={','.join(sorted(external))}")

