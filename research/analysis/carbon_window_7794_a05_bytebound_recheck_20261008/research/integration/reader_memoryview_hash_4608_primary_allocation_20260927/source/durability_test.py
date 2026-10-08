import json, os, subprocess, sys, tempfile, time
from pathlib import Path
import argparse

def append(path, value):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()
    with open(path, 'ab', buffering=0) as f:
        f.write(raw); os.fsync(f.fileno())

p = argparse.ArgumentParser(); p.add_argument('--out'); args = p.parse_args()
with tempfile.TemporaryDirectory() as td:
    root = Path(td); journal = root / 'journal.jsonl'; journal.touch()
    started = time.time_ns()
    proc = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(5)'],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    append(journal, {'event':'worker_started','worker_id':'injected-timeout','pid':proc.pid,'started_ns':started})
    try:
        proc.communicate(timeout=.1)
        raise AssertionError('timeout control did not time out')
    except subprocess.TimeoutExpired:
        proc.kill(); proc.communicate()
        append(journal, {'event':'worker_completed','worker_id':'injected-timeout','pid':proc.pid,
                         'category':'TIMEOUT','exit':124,'ended_ns':time.time_ns()})
        stop = {'classification':'STOP_WORKER_TIMEOUT','worker_id':'injected-timeout'}
        with (root/'STOP.json').open('xb',buffering=0) as f:
            f.write((json.dumps(stop,sort_keys=True)+'\n').encode()); os.fsync(f.fileno())
    events=[json.loads(x) for x in journal.read_text().splitlines()]
    observed=json.loads((root/'STOP.json').read_text())
    assert [e['event'] for e in events]==['worker_started','worker_completed']
    assert events[1]['category']=='TIMEOUT' and observed['classification']=='STOP_WORKER_TIMEOUT'
    result={'decision':'PASS_DURABLE_TIMEOUT_STOP','journal_events':len(events),
            'stop':observed,'elapsed_s':round((time.time_ns()-started)/1e9,3)}
    text=json.dumps(result,sort_keys=True)+'\n'
    if args.out:
        with Path(args.out).open('x') as f: f.write(text); f.flush()
    else: print(text,end='')
