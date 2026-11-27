#!/bin/bash
set -euo pipefail
cd /mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-5/work/v15-owner-integration-20261012
python3 - <<'PY'
import hashlib, json, pathlib
root = pathlib.Path('research/doom/v39_v15_xvfb_shared_key_source_a37_20261012')
freeze = json.loads((root / 'FREEZE.json').read_text(encoding='utf-8-sig'))
if freeze.get('allocation_id') != 'V39-XVFB-SECOND-DEVICE-HELD-KEY-A37-20261012-01':
    raise SystemExit('STOP: allocation id mismatch')
required = {'candidate.py', 'PLAN.md'}
seen = {pathlib.Path(item['path']).name for item in freeze.get('files', [])}
if not required.issubset(seen):
    raise SystemExit('STOP: frozen candidate/plan missing')
for item in freeze.get('files', []):
    path = pathlib.Path(item['path'])
    if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        raise SystemExit(f'STOP: frozen hash mismatch: {path}')
print('freeze hashes verified')
PY
mount --make-rprivate /
mount -t tmpfs -o size=64m tmpfs /tmp
chmod 1777 /tmp
mkdir -m 1777 /tmp/.X11-unix
export PYTHONPATH=research/live_control
export V15_OWNER_OUT=/mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-5/work/v15-owner-integration-20261012/research/doom/v39_v15_xvfb_shared_key_source_a37_20261012/results/A01
python3 -B research/doom/v39_v15_xvfb_shared_key_source_a37_20261012/candidate.py
