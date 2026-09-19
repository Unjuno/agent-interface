"""Run the preregistered opaque/transparent sign targeting ABBA once."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
ROOT = HERE / 'results/openttd-sign-target-pair-01'
plan = json.loads((ROOT / 'preregistration.json').read_text(encoding='utf-8'))
assert plan['status'] == 'PREREGISTERED_BEFORE_MODEL_CALLS' and plan['no_retry'] is True
for index, condition in enumerate(plan['order'], 1):
    image = HERE / plan['conditions'][condition]['image']
    output = ROOT / f'call-{index}-{condition}'
    args = [sys.executable, str(HERE / 'model_pair_runner_v2.py'),
            r'C:\Program Files\nodejs\node.exe',
            str(Path.home() / 'AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js'),
            str(image), str(ROOT / 'prompt.txt'), str(REPO), str(output),
            plan['model'], plan['effort']]
    completed = subprocess.run(args, capture_output=True, timeout=120)
    (ROOT / f'runner-{index}-stdout.txt').write_bytes(completed.stdout)
    (ROOT / f'runner-{index}-stderr.txt').write_bytes(completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError(f'model call {index} failed; no retry')
print('run_openttd_sign_target_pair_v1: COMPLETE')
