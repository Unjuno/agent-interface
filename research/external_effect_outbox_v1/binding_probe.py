"""Ten original/replay/conflict sequences against the separate deduplicating receiver."""
import json,subprocess,sys,time
from pathlib import Path
from experiment import send,save,connect,canonical
HERE=Path(__file__).resolve().parent

def run(root):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=False)
    stderr=(root/'receiver.stderr').open('w')
    proc=subprocess.Popen([sys.executable,str(HERE/'experiment.py'),'receiver',str(root),'--dedup'],stdout=stderr,stderr=stderr)
    results=[]
    try:
        deadline=time.monotonic()+5
        while not (root/'receiver_ready.json').exists():
            if proc.poll() is not None or time.monotonic()>deadline: raise RuntimeError('receiver setup')
            time.sleep(.01)
        port=json.loads((root/'receiver_ready.json').read_text())['port']
        for i in range(10):
            key=f'binding-{i:02d}'
            original={'context':'document-A','operation':'record_effect','value':1}
            changed={**original,'value':2}
            responses=[send(port,key,x) for x in [original,original,changed]]
            if [x['status'] for x in responses]!=['applied','duplicate','conflict']:
                raise AssertionError(responses)
            if len({x['effect_seq'] for x in responses})!=1:
                raise AssertionError('effect identity changed')
            row={'key':key,'original':original,'changed':changed,'responses':responses}
            results.append(row)
            with (root/'rows.jsonl').open('a') as f: f.write(canonical(row)+'\n')
        con=connect(root/'receiver.sqlite')
        effects=[dict(r) for r in con.execute('SELECT * FROM effects ORDER BY seq')]
        requests=[dict(r) for r in con.execute('SELECT * FROM requests ORDER BY seq')]
        con.close()
        assert len(effects)==10 and len(requests)==30
        assert all(json.loads(r['payload'])['value']==1 for r in effects)
        save(root/'database_snapshot.json',{'effects':effects,'requests':requests})
        save(root/'audit.json',{'sequences':10,'requests':30,'effects':10,'identical_replays_suppressed':10,
                               'changed_payloads_rejected':10,'audit':'PASS'})
    finally:
        proc.terminate();proc.wait(timeout=5);stderr.close()
if __name__=='__main__': run(sys.argv[1])
