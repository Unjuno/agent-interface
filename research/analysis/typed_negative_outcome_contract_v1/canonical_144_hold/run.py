from __future__ import annotations
import hashlib, json, pathlib, sys, time
from candidate import classify, coarse_compare
from corpus import build_rows


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def main(out_path: str):
    rows=[]
    started=time.time_ns()
    for src in build_rows():
        candidate=classify(src)
        comparator=coarse_compare(src)
        rows.append({'input':src,'candidate':candidate,'comparator':comparator})
    result={
        'schema':'agent-interface/typed-negative-outcome-contract-v1',
        'started_ns':started,
        'finished_ns':time.time_ns(),
        'formal_invocations':1,
        'reruns':0,
        'replacements':0,
        'tuning':0,
        'rows':rows,
    }
    data=(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)+'\n').encode()
    pathlib.Path(out_path).write_bytes(data)
    print(json.dumps({'rows':len(rows),'sha256':hashlib.sha256(data).hexdigest()},sort_keys=True))

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: run.py OUT.json')
    main(sys.argv[1])
