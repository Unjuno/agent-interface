"""Fixed ABBA integration check; primary-assistant selected plan, no model calls."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image
from native_exchange_v1 import run

ROOT = Path.cwd()
OUT = ROOT / 'results-local/native-key-boundary-study-01'
OUT.mkdir(exist_ok=False)
REFERENCE = ROOT / 'runtime/results/native-terminal-cleanup-01/run-2'
reference = json.loads((REFERENCE / 'source-1.json').read_text())
reference_path = REFERENCE / 'bridge/images' / Path(reference['native']['artifact']['path']).name
box = (588, 371, 612, 385)
with Image.open(reference_path) as image:
    anchor = image.convert('RGB').crop(box).tobytes()
plan = {'seed': 991105, 'waits_ms': [0, 50, 50, 0], 'point': [600, 378],
        'right_count': 18, 'post_key_wait_ms': 50, 'correction': False,
        'reference_image_sha256': hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        'reference_anchor_sha256': hashlib.sha256(anchor).hexdigest(),
        'scope': 'scripted existing native exchange; no model judgment comparison'}
(OUT / 'PLAN.json').write_text(json.dumps(plan, indent=2))
rows = []
for index, delay in enumerate(plan['waits_ms'], 1):
    folder = OUT / f'run-{index}'
    log = open(OUT / f'owner-{index}.txt', 'x')
    process = subprocess.Popen([sys.executable, 'research/live_control/run_native_calc_self_use_v1.py',
        '--app', 'inkscape', '--max-stages', '2', '--seed', str(plan['seed']), '--out', str(folder)],
        stdout=log, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic() + 30
        while not (folder / 'source-1.json').exists():
            if process.poll() is not None:
                raise RuntimeError('owner ended before source')
            if time.monotonic() > deadline:
                raise TimeoutError('initial source timeout; no restart')
            time.sleep(.05)
        source = json.loads((folder / 'source-1.json').read_text())
        with Image.open(source['native']['artifact']['path']) as image:
            assert image.convert('RGB').crop(box).tobytes() == anchor, 'initial anchor changed'
        tail = ([{'op': 'wait_update', 'timeout_ms': delay}] if delay else [])
        tail += [{'op': 'key_chord', 'keys': ['Right']} for _ in range(18)]
        tail += [{'op': 'wait_update', 'timeout_ms': 50}, {'op': 'key_chord', 'keys': ['CTRL', 's']}]
        decision = {'source_sequence': source['sequence'], 'point': plan['point'],
                    'expected_title': 'shape.svg - Inkscape', 'tail': tail}
        response = run(str(folder), 1, decision, timeout=5)
        (OUT / f'exchange-{index}-1.json').write_text(json.dumps(response, indent=2))
        reply = json.loads((folder / 'reply-1.json').read_text())
        if reply['status'] != 'boundary':
            raise RuntimeError('action did not complete; no replay')
        final = run(str(folder), 2, {'source_sequence': reply['observation']['sequence'], 'finish': True}, timeout=5)
        (OUT / f'exchange-{index}-2.json').write_text(json.dumps(final, indent=2))
        process.wait(timeout=15)
        terminal = json.loads((folder / 'reply-2.json').read_text())
        row = {'index': index, 'delay_ms': delay, 'owner_exit': process.returncode,
               'evaluation': terminal['evaluation'], 'cleanup': terminal['cleanup'],
               'program_ns': reply['action']['result']['execution']['ended_ns'] -
                             reply['action']['result']['execution']['started_ns']}
        rows.append(row)
        (OUT / 'SUMMARY.json').write_text(json.dumps(rows, indent=2))
        print(json.dumps(row), flush=True)
    finally:
        log.close()
    if process.returncode != 0:
        raise RuntimeError('owner failed; remaining allocations cancelled')
