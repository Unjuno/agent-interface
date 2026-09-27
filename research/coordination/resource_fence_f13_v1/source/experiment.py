"""One-time bounded case batches; exact IPC, SQLite bytes and real waits retained."""
import base64
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import time

MODES = ['ISSUER_ONLY', 'MAX_SEEN', 'INSTALLED_EPOCH']
SCENARIOS = ['STABLE', 'IDLE_RETIRE', 'NEW_FIRST', 'DELAYED_FENCE', 'PREINSTALL_NEW', 'RESOURCE_RESTART']
ROOT = Path(__file__).resolve().parent


def dumps(x):
    return json.dumps(x, sort_keys=True, indent=2) + '\n'


class Peer:
    def __init__(self, role, mode, work, scope, number, record):
        self.name = role + str(number)
        self.trace = work / (self.name + '.sql')
        args = [sys.executable, '-S', '-B', str(ROOT / 'actor.py'), role, mode,
                str(work / (role + '.db')), scope, str(self.trace)]
        self.err = open(work / (self.name + '.stderr'), 'xb')
        self.p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.err, bufsize=0)
        self.receipt = {'name': self.name, 'role': role, 'mode': mode, 'argv': args, 'pid': self.p.pid}
        self.record = record
        record['peers'].append(self.receipt)
        self.receipt['boot_raw'] = self.line()

    def line(self):
        out = bytearray()
        with selectors.DefaultSelector() as sel:
            sel.register(self.p.stdout, selectors.EVENT_READ)
            deadline = time.monotonic() + 3
            while not out.endswith(b'\n'):
                if not sel.select(max(0, deadline - time.monotonic())):
                    raise TimeoutError('child response')
                b = os.read(self.p.stdout.fileno(), 1)
                if not b:
                    raise EOFError('child closed')
                out.extend(b)
                if len(out) > 200000:
                    raise ValueError('response limit')
        return out.decode('utf-8')

    def send(self, q):
        raw = json.dumps(q, sort_keys=True, separators=(',', ':')) + '\n'
        t0 = time.monotonic_ns()
        self.p.stdin.write(raw.encode())
        self.p.stdin.flush()
        reply = self.line()
        self.record['io'].append({'peer': self.name, 'request_raw': raw, 'response_raw': reply,
                                  'start_ns': t0, 'end_ns': time.monotonic_ns()})
        return json.loads(reply)

    def finish(self, abrupt=False):
        self.send({'op': 'exit23' if abrupt else 'close'})
        self.receipt['exit'] = self.p.wait(timeout=3)
        self.p.stdin.close()
        self.p.stdout.close()
        self.err.close()
        self.receipt['stderr'] = self.err.name and Path(self.err.name).read_text()
        self.receipt['sql'] = self.trace.read_text()


def images(work):
    return {p.name: base64.b64encode(p.read_bytes()).decode() for p in sorted(work.glob('*.db*')) if p.is_file()}


def case(work, phase, scenario, mode, rep):
    work.mkdir(parents=True, exist_ok=False)
    scope = f'{phase}-{scenario}-{mode}-{rep}'
    r = {'id': scope, 'scenario': scenario, 'mode': mode, 'rep': rep, 'peers': [], 'io': []}
    issuer = Peer('issuer', mode, work, scope, 0, r)
    resource = Peer('resource', mode, work, scope, 0, r)
    r['initial_db'] = images(work)
    a = issuer.send({'op': 'grant', 'id': 'old-A', 'value': 11})['grant']
    b = issuer.send({'op': 'grant', 'id': 'old-B', 'value': 12})['grant']

    def apply(g):
        return resource.send({'op': 'apply', 'grant': g})

    def fresh(label):
        return issuer.send({'op': 'grant', 'id': label, 'value': 21})['grant']

    def install():
        if mode == 'INSTALLED_EPOCH':
            resource.send({'op': 'install', 'expected': 7, 'next': 8})

    if scenario == 'STABLE':
        apply(a)
    else:
        issuer.send({'op': 'retire', 'expected': 7, 'next': 8})
        if scenario == 'DELAYED_FENCE':
            apply(a)
            install()
            apply(b)
            apply(fresh('new-A'))
        elif scenario == 'PREINSTALL_NEW':
            apply(fresh('new-A'))
            install()
            apply(fresh('new-B'))
            apply(a)
        else:
            install()
            if scenario == 'NEW_FIRST':
                apply(fresh('new-A'))
            if scenario == 'RESOURCE_RESTART':
                r['restart_db'] = images(work)
                resource.finish(abrupt=True)
                resource = Peer('resource', mode, work, scope, 1, r)
            apply(a)
            if scenario == 'RESOURCE_RESTART':
                apply(fresh('new-A'))
    resource.finish()
    issuer.finish()
    r['final_db'] = images(work)
    (work / 'CASE.json').write_text(dumps(r))
    return r


def batch(destination, phase, index):
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=False)
    schedule = [(s, m, k) for s in SCENARIOS for m in MODES for k in range(2)]
    selected = schedule[index * 6:(index + 1) * 6]
    records = []
    for n, (s, m, k) in enumerate(selected):
        records.append(case(out / f'c{index * 6 + n:02}', phase, s, m, k))
    result = {'phase': phase, 'batch': index, 'cases': records,
              'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.iterdir() if p.is_file()}}
    (out / 'BATCH.json').write_text(dumps(result))
    print(json.dumps({'cases': len(records), 'batch': index}))


if __name__ == '__main__':
    batch(sys.argv[1], sys.argv[2], int(sys.argv[3]))
