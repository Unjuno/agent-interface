"""Eight effective, well-formed copied-record challenges to raw auditor."""
import copy
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit import audit_records


def main():
    root=Path(__file__).resolve().parent
    fixtures=json.loads((root/'FIXTURES.json').read_text())
    directory=Path(sys.argv[1]); construction='--construction' in sys.argv
    path=directory/'RAW.jsonl' if construction else directory/'n8/RAW.jsonl'
    original=[json.loads(x) for x in path.read_text().splitlines()]
    base=audit_records(original,fixtures,8,construction)
    if base['errors']:raise ValueError('baseline must pass before mutations')
    def report(r):
        obj=json.loads(r[0]['responses'][0]['stdout']);obj['task_success']=True
        r[0]['responses'][0]['stdout']=json.dumps(obj,sort_keys=True)+'\n'
    def stale(r):r[0]['responses'][1]['stdout']=r[0]['responses'][0]['stdout']
    mutations=[('drop_response',lambda r:r[0]['responses'].pop()),
               ('missing_exit',lambda r:r[0]['processes'][0].update(exit=None)),
               ('stale_report',stale),('wrong_pid',lambda r:r[0]['responses'][0].update(pid=-1)),
               ('false_task_success',report),
               ('clock_reversed',lambda r:r[0].update(end_ns=r[0]['start_ns']-1)),
               ('input_changed',lambda r:r[0]['responses'][0].update(after_sha256='0'*64)),
               ('phase_relabel',lambda r:r[0].update(phase='measured'))]
    results=[]
    for name,mutate in mutations:
        data=copy.deepcopy(original);mutate(data)
        before=json.dumps(original,sort_keys=True).encode();after=json.dumps(data,sort_keys=True).encode()
        assert before!=after
        audit=audit_records(data,fixtures,8,construction)
        assert audit['errors'],name
        results.append(dict(name=name,changed_sha256=hashlib.sha256(after).hexdigest(),errors=audit['errors']))
    print(json.dumps(dict(baseline_checks=base['checks'],rejected=len(results),controls=results),sort_keys=True,indent=2))


if __name__=='__main__':main()
