from pathlib import Path
p=Path('research/doom/v39_v15_process_owner_xvfb_a07_20261012/candidate.py')
s=p.read_text().replace('v39_v15_process_owner_xvfb_a06_20261012','v39_v15_process_owner_xvfb_a07_20261012').replace('a06-raw-v1','a07-raw-v1')
p.write_text(s)
runner='''#!/bin/bash
set -euo pipefail
mount --make-rprivate /
mount -t tmpfs -o size=64m tmpfs /tmp
chmod 1777 /tmp
mkdir -m 1777 /tmp/.X11-unix
cd /mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-5/work/v15-owner-integration-20261012
export PYTHONPATH="$HOME/.cache/v15-owner-a03-deps"
export V15_OWNER_OUT=/mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-5/work/v15-owner-integration-20261012/research/doom/v39_v15_process_owner_xvfb_a07_20261012/results/A01
python3 -B research/doom/v39_v15_process_owner_xvfb_a07_20261012/candidate.py
'''
Path('research/doom/v39_v15_process_owner_xvfb_a07_20261012/run_candidate.sh').write_bytes(runner.encode())
''@ | python -; @'
# A07 LF-runner successor

A06 is preserved as `STOP_INFRA_RUNNER_LINE_ENDINGS`: its Bash runner failed on CRLF before Python launched, so candidate invocation count was zero. A07 carries the allowlisted `a` probe and durable JSONL observation from A06, with a newly authored LF-only runner and unique absent results/A01 leaf. All other controls and decision gates are unchanged. This is a new successor allocation, not an A06 retry.

One candidate invocation; no retries. The scoped recovery decision requires independent key down/up evidence, session-only SIGKILL, verified fsynced matching receipt, owner clean exit without forced kill, and controlled Xvfb exit. No full product claim.