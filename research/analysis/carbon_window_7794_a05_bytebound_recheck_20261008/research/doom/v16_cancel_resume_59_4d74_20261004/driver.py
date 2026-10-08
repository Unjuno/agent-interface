import hashlib
import json
from pathlib import Path
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'out'
OUT.mkdir(exist_ok=False)
prior = ROOT.parent / 'v16-one-hold-01/out/FREEZE.json'
freeze = json.loads(prior.read_bytes())
argv = freeze['argv'][:]
argv[argv.index('--seed') + 1] = '40114'
for i, value in enumerate(argv):
    if value.endswith('v16-one-hold-01\\out:/out:rw'):
        argv[i] = str(OUT) + ':/out:rw'
assert str(OUT) + ':/out:rw' in argv
freeze['argv'] = argv
freeze['driver_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
freeze['protocol'] = 'initial:Left1000ms+observe; keys_held:cancel; cancelled terminal:observe-only; observe terminal:Right250ms+observe; recovery terminal:finish. Missing joins HOLD, no retries.'
(OUT / 'FREEZE.json').write_bytes(json.dumps(freeze, indent=2).encode())
inputs = []
rows = []
state = 'initial'
latest = None
p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
err = []
thread = threading.Thread(target=lambda: err.append(p.stderr.read()))
thread.start()
def send(command):
    inputs.append({'host_ns': time.perf_counter_ns(), 'command': command})
    (OUT / 'INPUTS.json').write_bytes(json.dumps(inputs, indent=2).encode())
    p.stdin.write((json.dumps(command) + '\n').encode())
    p.stdin.flush()
def submit(identifier, steps):
    send({'op': 'submit', 'id': identifier, 'expected_sequence': latest['sequence'],
          'valid_until_ns': latest['capture_ns'] + 30_000_000_000, 'steps': steps})
with (OUT / 'stdout.txt').open('wb') as stream:
    for raw in p.stdout:
        stream.write(raw)
        stream.flush()
        row = json.loads(raw)
        rows.append(row)
        if row.get('event') == 'observation':
            latest = row
            if state == 'initial':
                state = 'holding'
                submit('cancel-left-01', [{'op':'hold','keys':['Left'],'duration_ms':1000}, {'op':'observe'}])
        if row.get('event') == 'keys_held' and row.get('id') == 'cancel-left-01' and state == 'holding':
            state = 'cancelling'
            send({'op':'cancel','id':'cancel-left-01'})
        if row.get('event') == 'terminal':
            if row.get('id') == 'cancel-left-01':
                release = row.get('release', {})
                if row.get('status') != 'cancelled' or release.get('verified') is not True or release.get('keys_down') != [] or release.get('buttons_down') != []:
                    state = 'hold'
                    send({'op':'finish'})
                else:
                    state = 'refreshing'
                    submit('fresh-observe-01', [{'op':'observe'}])
            elif row.get('id') == 'fresh-observe-01':
                if row.get('status') == 'completed' and latest.get('id') == 'fresh-observe-01':
                    state = 'recovering'
                    submit('resume-right-01', [{'op':'hold','keys':['Right'],'duration_ms':250}, {'op':'observe'}])
                else:
                    state = 'hold'
                    send({'op':'finish'})
            elif row.get('id') == 'resume-right-01':
                state = 'finished'
                send({'op':'finish'})
code = p.wait(timeout=5)
thread.join(timeout=5)
(OUT / 'stderr.txt').write_bytes(b''.join(err))
(OUT / 'exit.json').write_bytes(json.dumps({'exit_code':code,'driver_state':state}).encode())
print(json.dumps({'exit_code':code,'state':state,'events':len(rows),'terminals':[r for r in rows if r.get('event')=='terminal']}))
