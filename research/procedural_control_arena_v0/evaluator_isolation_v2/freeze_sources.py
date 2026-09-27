"""Freeze v2 source, container IDs, successor seed, and prior STOP lineage."""
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BASE = 'python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9'

def git(*args):
    return subprocess.run(['git', *args], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()

if git('status', '--porcelain'):
    raise SystemExit('STOP: commit and push v2 source before freeze')
source_commit = git('rev-parse', 'HEAD')
spec = importlib.util.spec_from_file_location('arena_engine_v2_freeze', REPO / 'research/procedural_control_arena_v0/engine.py')
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)
episode = engine.generate_episode(2003, 1.0)
if episode.stages[0].kind != 'target' or abs(episode.stages[0].payload['deadline'] - 2.6) > 1e-9:
    raise SystemExit('STOP: seed-2003 canary contract mismatch')

build = json.loads((HERE / 'construction/BUILD_RECORD.json').read_text(encoding='utf-8'))
images = {}
for row in build['images']:
    actual = json.loads(subprocess.run(['docker', 'image', 'inspect', row['tag']], check=True, capture_output=True, text=True).stdout)[0]
    if actual['Id'] != row['id'] or row['base'] != BASE:
        raise SystemExit(f"STOP: image changed or base mismatch: {row['name']}")
    images[row['name']] = {'tag': row['tag'], 'id': row['id'], 'base': row['base']}

files = ['RESEARCH.md', 'research/procedural_control_arena_v0/arena.py', 'research/procedural_control_arena_v0/engine.py',
         'research/procedural_control_arena_v0/evaluator_isolation_v1/formal/001/STOP_RECORD.md',
         'research/procedural_control_arena_v0/evaluator_isolation_v1/formal/001/STOP_RAW_MANIFEST.json']
files.extend(path.relative_to(REPO).as_posix() for path in HERE.rglob('*')
             if path.is_file() and path.name != 'FREEZE.json' and 'formal' not in path.relative_to(HERE).parts
             and '__pycache__' not in path.parts and path.suffix != '.pyc')
hashes = {}
for rel in files:
    hashes[rel] = {'sha256_worktree_bytes': hashlib.sha256((REPO / rel).read_bytes()).hexdigest(), 'git_blob_oid': git('hash-object', rel)}
for canonical, copied in [('research/procedural_control_arena_v0/arena.py', 'research/procedural_control_arena_v0/evaluator_isolation_v2/images/evaluator/arena.py'),
                          ('research/procedural_control_arena_v0/engine.py', 'research/procedural_control_arena_v0/evaluator_isolation_v2/images/evaluator/engine.py')]:
    if hashes[canonical]['sha256_worktree_bytes'] != hashes[copied]['sha256_worktree_bytes']:
        raise SystemExit(f'STOP: copied source differs: {canonical}')

manifest = {
    'schema': 'agent-interface-arena-isolation-v2-freeze-v1', 'issue': 4666,
    'predecessor': 'evaluator_isolation_v1/formal/001 STOP; not retried',
    'source_commit': source_commit, 'freeze_commit_parent_must_equal': source_commit,
    'created_utc': datetime.now(timezone.utc).isoformat(), 'base_image': BASE,
    'images': images, 'source_hashes': hashes,
    'trial': {'seed': 2003, 'difficulty': 1.0, 'clock': 'fixed', 'first_stage': 'target', 'deadline_seconds': 2.6,
              'controller_action': 'send exactly one w key-down/key-up', 'allocation': 'formal/002 only; one attempt',
              'evaluator_report_persistence': 'evaluator-only host bind at /evidence', 'auto_close_seconds_after_terminal': 30},
}
target = HERE / 'FREEZE.json'
if target.exists():
    raise SystemExit('STOP: FREEZE.json already exists')
target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps({'freeze_file': str(target), 'source_commit': source_commit, 'first_stage': episode.stages[0].kind, 'images': images}, indent=2))
