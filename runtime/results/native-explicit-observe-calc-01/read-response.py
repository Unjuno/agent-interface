import json,sys,time
from pathlib import Path
p=Path('results-local/native-explicit-observe-calc-01-responses.jsonl'); target=int(sys.argv[1]); deadline=time.monotonic()+15
while True:
    data=p.read_bytes() if p.exists() else b''
    for line in data.splitlines(keepends=True):
        if not line.endswith(b'\n'):continue
        row=json.loads(line)
        if row.get('id')==target:
            print(json.dumps(row));sys.exit(0)
    if time.monotonic()>=deadline:raise TimeoutError('response absent; inspect same relay, do not replay')
    time.sleep(.05)
