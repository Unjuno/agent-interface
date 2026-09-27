import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = 'python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9'
BUILD = HERE / 'construction'
BUILD.mkdir(exist_ok=True)
for source in ('arena.py', 'engine.py'):
    src, dst = ROOT / source, HERE / 'images' / 'evaluator' / source
    shutil.copyfile(src, dst)
    if hashlib.sha256(src.read_bytes()).digest() != hashlib.sha256(dst.read_bytes()).digest():
        raise SystemExit(f'copy mismatch: {source}')
records = []
source_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in ('arena.py', 'engine.py')}
for name in ('evaluator', 'controller'):
    context = HERE / 'images' / name
    tag = f'agent-arena-isolation-{name}:20260927'
    cmd = ['docker', 'build', '--pull', '--platform', 'linux/amd64', '--tag', tag, str(context)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log = BUILD / f'{name}-build.log'
    log.write_text(proc.stdout, encoding='utf-8')
    if proc.returncode:
        raise SystemExit(f'build failed for {name}; see {log}')
    inspected = subprocess.run(['docker', 'image', 'inspect', tag], check=True, capture_output=True, text=True)
    (BUILD / f'{name}-image-inspect.json').write_text(inspected.stdout, encoding='utf-8')
    image = json.loads(inspected.stdout)[0]
    records.append({'name': name, 'tag': tag, 'image_id': image['Id'], 'repo_digests': image.get('RepoDigests', []), 'base': BASE, 'build_command': cmd, 'log_sha256': hashlib.sha256(proc.stdout.encode()).hexdigest()})
(BUILD / 'BUILD_RECORD.json').write_text(json.dumps({'built_unix': time.time(), 'arena_source_sha256': source_hashes, 'images': records}, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps(records, indent=2))
