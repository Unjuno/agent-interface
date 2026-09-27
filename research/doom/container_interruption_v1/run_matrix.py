"""One-shot local real-MAP01 normal/cancel/expiry development matrix.

No model calls, no scorer feedback to control, no old allocation replay. Uses the
unchanged v13 session from the manifest-pinned source bundle. Save state is loaded
only as the existing setup fixture; control is X11 through the Executor.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import queue
import signal
import subprocess
import sys
import threading
import time

from occupancy import analyze_program

HERE = Path(__file__).resolve().parent
BASE = '9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245'
CASES = [
    {'name': 'coast', 'keys': [], 'duration_ms': 300, 'lease_ms': 4000, 'status': 'completed'},
    {'name': 'normal-single', 'keys': ['a'], 'duration_ms': 240, 'lease_ms': 4000, 'status': 'completed'},
    {'name': 'normal-chord', 'keys': ['a', 'd'], 'duration_ms': 240, 'lease_ms': 4000, 'status': 'completed'},
    {'name': 'cancel-chord', 'keys': ['a', 'd'], 'duration_ms': 2000, 'lease_ms': 4000, 'status': 'cancelled', 'cancel_after_held_ms': 120},
    {'name': 'expire-chord', 'keys': ['a', 'd'], 'duration_ms': 2000, 'lease_ms': 500, 'status': 'expired'},
]


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path, value): Path(path).write_text(json.dumps(value, indent=2, sort_keys=True)+'\n', encoding='utf-8')
def read_rows(path): return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def run_case(repo, out, spec, seed):
    out.mkdir()
    runtime = out/'runtime'
    fixture = repo/'research/doom/fixtures/map01-threat-contact-v2/fixture.json'
    command = [sys.executable, str(repo/'research/doom/session_map01_v13.py'),
               '--out', str(runtime), '--seed', str(seed), '--skill', '1',
               '--timeout-seconds', '60', '--load-fixture-manifest', str(fixture)]
    write(out/'launch.json', {'argv':command, 'spec':spec, 'base_commit':BASE})
    q = queue.Queue(); latest = None; received = []; sent = []; timer = None
    lock = threading.Lock(); timer_errors = []
    stderr = (out/'stderr.txt').open('w')
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=stderr, text=True, bufsize=1, start_new_session=True, cwd=repo)
    def reader():
        try:
            for line in proc.stdout:
                try: q.put(json.loads(line))
                except Exception as exc: q.put({'event':'reader_error','error':repr(exc),'line':line})
        finally: q.put(None)
    thread = threading.Thread(target=reader, daemon=True); thread.start()
    def send(row):
        with lock:
            sent.append({'sent_ns':time.perf_counter_ns(), 'command':row})
            proc.stdin.write(json.dumps(row)+'\n'); proc.stdin.flush()
    def wait(predicate, timeout=20):
        nonlocal latest
        end = time.monotonic()+timeout
        while True:
            try: row=q.get(timeout=max(0,end-time.monotonic()))
            except queue.Empty: raise TimeoutError('runtime event timeout')
            if row is None: raise RuntimeError('runtime stdout closed; see stderr.txt')
            received.append({'received_ns':time.perf_counter_ns(), 'row':row})
            if row.get('event') == 'reader_error': raise RuntimeError(row)
            if row.get('event') == 'observation': latest = row
            if predicate(row): return row
    pid = 'matrix-'+spec['name']; failure = None
    try:
        wait(lambda r:r.get('event')=='ready')
        wait(lambda r:r.get('event')=='observation' and r.get('id')=='initial')
        initial_sequence = latest['sequence']
        send({'op':'clock'}); clock = wait(lambda r:r.get('event')=='clock')
        step = ({'op':'hold','keys':spec['keys'],'duration_ms':spec['duration_ms']} if spec['keys']
                else {'op':'coast','duration_ms':spec['duration_ms'],'sample_ms':50})
        send({'op':'submit','id':pid,'expected_sequence':initial_sequence,
              'valid_until_ns':clock['runtime_ns']+spec['lease_ms']*1_000_000,'steps':[step]})
        accepted = wait(lambda r:r.get('event') in ('accepted','rejected'))
        if accepted.get('event') != 'accepted': raise RuntimeError('primary program rejected')
        if 'cancel_after_held_ms' in spec:
            wait(lambda r:r.get('event')=='keys_held' and r.get('id')==pid)
            def cancel():
                try: send({'op':'cancel','id':pid})
                except Exception as exc: timer_errors.append(repr(exc))
            timer = threading.Timer(spec['cancel_after_held_ms']/1000, cancel); timer.start()
        terminal = wait(lambda r:r.get('event')=='terminal' and r.get('id')==pid)
        if timer: timer.join()
        if timer_errors: raise RuntimeError(timer_errors)
        if terminal['status'] != spec['status']: raise RuntimeError('unexpected terminal '+repr(terminal))
        # The old exact sequence must not authorize another input after new frames.
        if latest['sequence'] <= initial_sequence: raise RuntimeError('stale-sequence negative control not exposed')
        send({'op':'clock'}); clock = wait(lambda r:r.get('event')=='clock')
        stale_id = pid+'-stale'
        send({'op':'submit','id':stale_id,'expected_sequence':initial_sequence,
              'valid_until_ns':clock['runtime_ns']+1_000_000_000,
              'steps':[{'op':'hold','keys':['a'],'duration_ms':10}]})
        rejected = wait(lambda r:r.get('event') in ('accepted','rejected'))
        if rejected.get('event') != 'rejected': raise RuntimeError('stale sequence admitted')
        send({'op':'finish'}); wait(lambda r:r.get('event')=='post_control_score')
        proc.stdin.close()
        if proc.wait(timeout=10) != 0: raise RuntimeError('session exit nonzero')
    except Exception as exc:
        failure = repr(exc)
    finally:
        if timer: timer.cancel(); timer.join(timeout=2)
        if proc.poll() is None:
            try: send({'op':'finish'}); proc.wait(timeout=5)
            except Exception: os.killpg(proc.pid, signal.SIGKILL); proc.wait(timeout=5)
        thread.join(timeout=2); stderr.close()
        write(out/'controller.json', {'sent':sent,'received':received,'failure':failure})
    if failure: raise RuntimeError(failure)
    events = read_rows(runtime/'events.jsonl')
    accepted = next(r for r in events if r.get('event')=='accepted' and r.get('id')==pid)
    terminal = next(r for r in events if r.get('event')=='terminal' and r.get('id')==pid)
    occupancy = analyze_program(events,pid,accepted['accepted_ns'],terminal['terminal_ns'])
    sys.path.insert(0,str(repo/'research/doom'))
    from audit_map01_terminal_score_agreement_v1 import audit
    agreement = audit(runtime)
    scorer = json.loads((runtime/'scorer-summary.json').read_text())
    leak = [r for r in events+read_rows(runtime/'delivered.jsonl')
            if str(r.get('schema','')).startswith('independent-progress-')]
    verified = terminal['release']
    empty = verified.get('verified') is True and verified.get('keys_down') == [] and verified.get('buttons_down') == []
    result = {'case':spec['name'], 'terminal_status':terminal['status'], 'occupancy':occupancy,
              'terminal_score_agreement':agreement, 'scorer_summary':scorer,
              'terminal_empty_verified':empty, 'scorer_leak_count':len(leak),
              'stale_sequence_rejected':not any(r.get('event')=='accepted' and r.get('id')==stale_id for r in events),
              'interruption':terminal.get('interruption'), 'scientific_efficacy_claim':False}
    cause = (terminal.get('interruption') or {}).get('record') or {}
    result['expected_interruption_exposed'] = (spec['status'] == 'completed' or
        cause.get('reason') == spec['status'] and cause.get('verified') is True)
    result['pass'] = bool(empty and agreement['pass'] and not leak and result['stale_sequence_rejected']
                          and occupancy['admission_count']==len(spec['keys'])
                          and result['expected_interruption_exposed'])
    write(out/'result.json',result)
    if not result['pass']: raise RuntimeError('case gates failed')
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--bundle-manifest',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    args.repo=args.repo.resolve(); args.out=args.out.resolve()
    plan=json.loads((HERE/'plan.json').read_text());manifest=json.loads(args.bundle_manifest.read_text())
    if plan['base_commit']!=BASE or manifest['base_commit']!=BASE or plan['cases']!=CASES:raise RuntimeError('base/plan mismatch')
    for name,expected in plan['source_sha256'].items():
        if digest(HERE/name)!=expected:raise RuntimeError('frozen candidate hash mismatch '+name)
    for name,item in manifest['files'].items():
        if digest(args.repo/name)!=item['sha256']:raise RuntimeError('bundle base drift '+name)
    args.out.mkdir(parents=True,exist_ok=False)
    write(args.out/'plan.json',plan)
    import vizdoom, PIL, numpy
    cpu=next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),'unknown')
    environment={'python':sys.version,'platform':platform.platform(),'cpu':cpu,'cpu_affinity':sorted(os.sched_getaffinity(0)),
                 'cpu_frequency':'uncontrolled/shared virtualized host','clock':vars(time.get_clock_info('perf_counter')),
                 'vizdoom':vizdoom.__version__,'pillow':PIL.__version__,'numpy':numpy.__version__,
                 'source_bundle_manifest_sha256':digest(args.bundle_manifest), 'base_commit':BASE}
    write(args.out/'environment.json',environment)
    results=[];error=None
    for case in CASES:
        try:
            result=run_case(args.repo,args.out/case['name'],case,plan['seed']);results.append(result)
            print(json.dumps({'case':case['name'],'pass':result['pass'],'status':result['terminal_status'],
                              'occupancy':result['occupancy']}),flush=True)
        except Exception as exc:error=repr(exc);break
    write(args.out/'summary.json',{'schema':'container-map01-interruption-matrix-v1',
          'allocation_id':plan['allocation_id'],'cases_completed':len(results),'planned_cases':len(CASES),
          'pass':error is None and len(results)==len(CASES),'error':error,'results':results,'model_calls':0})
    hashes={str(p.relative_to(args.out)):{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(args.out.rglob('*')) if p.is_file()}
    write(args.out/'artifact-manifest.json',hashes)
    raise SystemExit(0 if error is None and len(results)==len(CASES) else 1)

if __name__=='__main__':main()
