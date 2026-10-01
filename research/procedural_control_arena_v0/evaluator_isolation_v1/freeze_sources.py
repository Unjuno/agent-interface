"""Create a pre-trial manifest after source/build commit is clean and pushed."""
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
REL = HERE.relative_to(REPO).as_posix()
BASE_IMAGE = 'python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9'
FILES = ['RESEARCH.md', 'research/procedural_control_arena_v0/arena.py', 'research/procedural_control_arena_v0/engine.py']
FILES.extend(path.relative_to(REPO).as_posix() for path in HERE.rglob('*')
             if path.is_file() and path.name != 'FREEZE.json' and 'formal' not in path.relative_to(HERE).parts
             and '__pycache__' not in path.parts and path.suffix != '.pyc')

def git(*args):
    return subprocess.run(['git', *args], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()

if git('status', '--porcelain'):
    raise SystemExit('STOP: commit and push source before freezing')
source_commit = git('rev-parse', 'HEAD')
engine_path = REPO / 'research/procedural_control_arena_v0/engine.py'
spec = importlib.util.spec_from_file_location('arena_engine_freeze', engine_path)
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)
episode = engine.generate_episode(2001, 1.0)
if episode.stages[0].kind != 'target' or abs(episode.stages[0].payload['deadline'] - 2.6) > 1e-9:
    raise SystemExit('STOP: preregistered seed-2001 canary contract changed')

build = json.loads((HERE / 'construction/BUILD_RECORD.json').read_text(encoding='utf-8'))
images = {}
for row in build['images']:
    inspected = json.loads(subprocess.run(['docker', 'image', 'inspect', row['tag']], check=True, capture_output=True, text=True).stdout)[0]
    if inspected['Id'] != row['image_id']:
        raise SystemExit(f"STOP: built image id changed for {row['name']}")
    images[row['name']] = {'tag': row['tag'], 'id': row['image_id'], 'base': row['base']}
    if row['base'] != BASE_IMAGE:
        raise SystemExit(f"STOP: base image digest differs for {row['name']}")

hashes = {}
for rel in FILES:
    raw = (REPO / rel).read_bytes()
    hashes[rel] = {'sha256_worktree_bytes': hashlib.sha256(raw).hexdigest(), 'git_blob_oid': git('hash-object', rel)}
for canonical, copied in [('research/procedural_control_arena_v0/arena.py', f'{REL}/images/evaluator/arena.py'),
                          ('research/procedural_control_arena_v0/engine.py', f'{REL}/images/evaluator/engine.py')]:
    if hashes[canonical]['sha256_worktree_bytes'] != hashes[copied]['sha256_worktree_bytes']:
        raise SystemExit(f'STOP: copied source differs: {canonical}')
manifest = {
    'schema': 'agent-interface-arena-isolation-freeze-v1', 'issue': 4666, 'source_commit': source_commit,
    'freeze_commit_parent_must_equal': source_commit, 'created_utc': datetime.now(timezone.utc).isoformat(),
    'base_image': BASE_IMAGE, 'images': images, 'source_hashes': hashes,
    'trial': {'seed': 2001, 'difficulty': 1.0, 'clock': 'fixed', 'first_stage': 'target', 'deadline_seconds': 2.6,
              'controller_action': 'send exactly one w key-down/key-up', 'formal_allocation': 'formal/001 only; one attempt'},
}
target = HERE / 'FREEZE.json'
if target.exists():
    raise SystemExit('STOP: FREEZE.json already exists; do not overwrite a frozen allocation')
target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps({'freeze_file': str(target), 'source_commit': source_commit, 'images': images,
                  'seed_2001_first_stage': episode.stages[0].kind}, indent=2))
