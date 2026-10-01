from __future__ import annotations
import argparse, hashlib, json, os, queue, subprocess, threading, time
from pathlib import Path
import numpy as np
from PIL import Image

THRESHOLD = 0.015
REANCHOR_BUDGET = 1

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def mae(a, b):
    with Image.open(a) as ia, Image.open(b) as ib:
        aa = np.asarray(ia.convert('RGB'), dtype=np.float32)
        bb = np.asarray(ib.convert('RGB'), dtype=np.float32)
    return float(np.abs(aa - bb).mean() / 255.0)

def wait_event(q, proc, pred, timeout=35):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            item = q.get(timeout=.25)
        except queue.Empty:
            if proc.poll() is not None:
                raise RuntimeError('session died: ' + proc.stderr.read())
            continue
        if pred(item): return item
    raise TimeoutError('expected event')

def decision(old, fresh, *, same_session, fresh_observation, budget, duplicate=False, ambiguous=False):
    """Pure bounded reanchor gate; no hidden state or model call is used."""
    fresh_mae = None if fresh is None else mae(old['image'], fresh['image'])
    source_valid = same_session and fresh_observation and not duplicate and not ambiguous
    if budget > REANCHOR_BUDGET: source_valid = False
    if fresh_mae is None: return {'admission': 'REJECT_NO_FRESH_OBSERVATION', 'fresh_mae': None}
    if not source_valid: return {'admission': 'REJECT_PROVENANCE', 'fresh_mae': fresh_mae}
    return {'admission': 'ADMIT' if fresh_mae <= THRESHOLD else 'REJECT_CONTEXT_CHANGED', 'fresh_mae': fresh_mae}

def run_live(case, out, runtime_root, python):
    out.mkdir(parents=True, exist_ok=False)
    doom = runtime_root / 'research/doom'; live = runtime_root / 'research/live_control'
    fixture = doom / 'fixtures/map01-threat-contact-v2/fixture.json'
    env = os.environ.copy(); env['PYTHONPATH'] = f'{doom}:{live}'
    proc = subprocess.Popen([str(python), str(doom/'session_map01_v12.py'), '--out', str(out/'runtime'), '--seed', str(case['seed']), '--timeout-seconds', '60', '--skill', '1', '--load-fixture-manifest', str(fixture)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, env=env)
    q = queue.Queue(); events = []
    def reader():
        for line in proc.stdout:
            try: item = json.loads(line)
            except Exception: continue
            events.append(item); q.put(item)
    threading.Thread(target=reader, daemon=True).start()
    wait = lambda pred, timeout=35: wait_event(q, proc, pred, timeout)
    ready = wait(lambda x: x.get('event') == 'ready')
    source_t = wait(lambda x: x.get('event') == 'typed_observation')
    source_o = wait(lambda x: x.get('event') == 'observation' and x.get('sequence') == source_t['sequence'])
    proc.stdin.write(json.dumps({'op':'clock'})+'\n'); proc.stdin.flush(); clock = wait(lambda x: x.get('event') == 'clock')
    if case['arm'] == 'coast':
        steps = [{'op':'coast','duration_ms':600,'sample_ms':50}, {'op':'observe'}]
    else:
        steps = ([{'op':'hold','keys':['d'],'duration_ms':50},{'op':'observe'}] * 5) + [{'op':'coast','duration_ms':350,'sample_ms':50},{'op':'observe'}]
    if case['fresh_mode'] == 'observe':
        steps.append({'op':'observe'})
    ident = case['id']; program = {'op':'submit','id':ident,'expected_sequence':source_o['sequence'],'valid_until_ns':clock['runtime_ns']+5_000_000_000,'steps':steps}
    proc.stdin.write(json.dumps(program)+'\n'); proc.stdin.flush()
    accepted = wait(lambda x: x.get('event') in ('accepted','rejected') and (x.get('id') == ident or x.get('event') == 'rejected'))
    if accepted.get('event') != 'accepted': raise RuntimeError(('unexpected rejection', accepted))
    terminal = wait(lambda x: x.get('event') == 'terminal' and x.get('id') == ident)
    typed_after = [x for x in events if x.get('event') == 'typed_observation' and x.get('sequence', 0) > source_t['sequence']]
    post_t = typed_after[-2] if case['fresh_mode'] == 'observe' else typed_after[-1]
    post_o = [x for x in events if x.get('event') == 'observation' and x.get('sequence') == post_t['sequence']][-1]
    rejected = {'image': source_o['image'], 'sequence': source_o['sequence'], 'session_id': ready.get('session_id'), 'frame_sha256': source_t['frame_rgb_sha256']}
    fresh = None
    if case['fresh_mode'] == 'observe':
        fresh_t = typed_after[-1]
        fresh = [x for x in events if x.get('event') == 'observation' and x.get('sequence') == fresh_t['sequence']][-1]
    proc.stdin.write(json.dumps({'op':'finish'})+'\n'); proc.stdin.flush(); score = wait(lambda x: x.get('event') == 'post_control_score')
    proc.stdin.close(); proc.wait(timeout=12)
    old = {'image': post_o['image'], 'sequence': post_o['sequence'], 'session_id': ready.get('session_id'), 'frame_sha256': post_t['frame_rgb_sha256']}
    fresh_ref = None if fresh is None else {'image': fresh['image'], 'sequence': fresh['sequence'], 'session_id': ready.get('session_id'), 'frame_sha256': next(x['frame_rgb_sha256'] for x in events if x.get('event') == 'typed_observation' and x.get('sequence') == fresh['sequence'])}
    guard = {'admission': 'ADMIT' if mae(rejected['image'], old['image']) <= THRESHOLD else 'REJECT_CONTEXT_CHANGED', 'fresh_mae': mae(rejected['image'], old['image'])}
    reanchor = decision(old, fresh_ref, same_session=case['same_session'], fresh_observation=case['fresh_mode'] == 'observe', budget=case['budget'], duplicate=case.get('duplicate', False), ambiguous=case.get('ambiguous', False))
    result = {**case, 'schema':'bounded-fresh-reanchor-case-v1', 'session_id':ready.get('session_id'), 'source_sequence':source_t['sequence'], 'rejected_sequence':post_t['sequence'], 'fresh_sequence':None if fresh is None else fresh['sequence'], 'rejected_frame_sha256':post_t['frame_rgb_sha256'], 'fresh_frame_sha256':None if fresh_ref is None else fresh_ref['frame_sha256'], 'guard_only':guard, 'reanchor':reanchor, 'event_count':len(events), 'terminal_status':terminal.get('status'), 'release':terminal.get('release'), 'score':{k:score.get(k) for k in ('kill_count','death_count','map_exit','player_dead')}, 'runtime_sources_sha256':sha256(out/'runtime'/'sources.json')}
    (out/'result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    return result

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--plan', type=Path, required=True); ap.add_argument('--out', type=Path, required=True); ap.add_argument('--runtime-root', type=Path, required=True); ap.add_argument('--python', type=Path, required=True); a = ap.parse_args()
    plan = json.loads(a.plan.read_text()); results = []
    for case in plan['cases']: results.append(run_live(case, a.out/case['id'], a.runtime_root, a.python))
    (a.out/'results.json').write_text(json.dumps(results, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'cases': len(results), 'results': results}, sort_keys=True))
if __name__ == '__main__': main()
