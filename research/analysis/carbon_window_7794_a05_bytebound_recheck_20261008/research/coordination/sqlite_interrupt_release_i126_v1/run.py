"""Consume each new batch directory once; retain actual actor pipes and DB bytes."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parent
STATES = ('IDLE','IMPLICIT_ONE','EXPLICIT_ONE','EXPLICIT_DONE','IMPLICIT_TWO')
MODES = ('INTERRUPT_ONLY','AWAIT_TARGET','FINALIZE_ALL')


def snapshot(db):
    return {suffix: base64.b64encode(Path(str(db)+suffix).read_bytes()).decode() if Path(str(db)+suffix).exists() else None for suffix in ('','-wal','-shm')}


class Peer:
    def __init__(self, role, db, directory):
        self.role, self.wire = role, []
        self.directory = directory
        self.err = open(directory / (role+'.stderr'), 'xb')
        self.argv = [sys.executable, '-I', '-S', '-B', str(ROOT/'actor.py'), role, str(db), str(directory/(role+'.jsonl'))]
        self.started = time.monotonic_ns()
        self.proc = subprocess.Popen(self.argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.err, text=True)

    def call(self, **q):
        sent = time.monotonic_ns()
        raw = json.dumps(q, sort_keys=True, separators=(',', ':'))+'\n'
        self.proc.stdin.write(raw); self.proc.stdin.flush()
        if not select.select([self.proc.stdout], [], [], 3)[0]:
            raise TimeoutError(self.role)
        reply = self.proc.stdout.readline()
        ended = time.monotonic_ns()
        self.wire.append({'request': raw, 'response': reply, 'sent_ns': sent, 'received_ns': ended})
        return json.loads(reply)['value']

    def finish(self):
        forced = self.proc.poll() is None
        if forced:
            self.proc.kill()
        code = self.proc.wait(timeout=3)
        self.err.close()
        return {'argv': self.argv, 'pid': self.proc.pid, 'exit': code, 'forced': forced, 'start_ns': self.started, 'end_ns': time.monotonic_ns(), 'wire': self.wire, 'stderr': (self.directory/(self.role+'.stderr')).read_text(), 'actor_log': (self.directory/(self.role+'.jsonl')).read_text()}


def case(directory, identity, state, mode, n):
    directory.mkdir()
    db = directory/'state.db'
    peers = []
    record = {'id': identity, 'state': state, 'mode': mode, 'n': n, 'authority_granted': False, 'task_success': None, 'complete': False, 'snapshots': {}}
    try:
        w = Peer('writer', db, directory); peers.append(w)
        record['init'] = w.call(op='INIT', n=n)
        record['snapshots']['initial'] = snapshot(db)
        r = Peer('reader', db, directory); peers.append(r)
        record['arm'] = r.call(op='ARM', state=state)
        record['update'] = w.call(op='UPDATE')
        record['snapshots']['updated'] = snapshot(db)
        record['cancel'] = r.call(op='CANCEL', mode=mode)
        record['primary'] = w.call(op='CHECK')
        record['snapshots']['primary'] = snapshot(db)
        record['cleanup'] = r.call(op='CLEAN')
        record['after_cleanup'] = w.call(op='CHECK')
        record['snapshots']['cleanup'] = snapshot(db)
        r.call(op='QUIT'); r.proc.wait(timeout=3)
        w.call(op='QUIT'); w.proc.wait(timeout=3)
        record['complete'] = True
    except Exception:
        record['error'] = traceback.format_exc()
    finally:
        record['processes'] = {p.role: p.finish() for p in peers}
        record['snapshots']['final'] = snapshot(db) if db.exists() else {}
        (directory/'CASE.json').write_text(json.dumps(record, sort_keys=True)+'\n')
    return record


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('kind', choices=['construction','formal'])
    ap.add_argument('batch', type=int)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    schedule = [(s,m,r) for s in STATES for m in MODES for r in range(2 if args.kind=='formal' else 1)]
    subset = schedule[args.batch*10:(args.batch+1)*10] if args.kind=='formal' else schedule
    if not subset or (args.kind=='construction' and args.batch!=0):
        raise SystemExit('invalid batch')
    args.output.mkdir(parents=True, exist_ok=False)
    start = time.monotonic_ns()
    records = []
    with (args.output/'RECORDS.jsonl').open('x') as stream:
        for index, (state,mode,rep) in enumerate(subset):
            identity = f'{args.kind}-b{args.batch}-c{index}'
            row = case(args.output/identity, identity, state, mode, 64 if args.kind=='formal' else 16)
            row['rep'] = rep
            records.append(row)
            stream.write(json.dumps(row,sort_keys=True)+'\n'); stream.flush()
            if not row['complete'] or any(p['exit']!=0 for p in row['processes'].values()):
                break
    result = {'kind':args.kind,'batch':args.batch,'pid':os.getpid(),'start_ns':start,'end_ns':time.monotonic_ns(),'rows':len(records),'expected':len(subset),'complete':len(records)==len(subset) and all(r['complete'] for r in records)}
    (args.output/'BATCH.json').write_text(json.dumps(result,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if result['complete'] else 1)
