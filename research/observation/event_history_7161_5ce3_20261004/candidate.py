"""One prospectively frozen finite T0; no physical/native/model work."""
import hashlib,itertools,json,sys
from pathlib import Path
from fixtures import CASES,COUNTS
from policy import classify_complete
def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':'))
def main():
    out=Path(sys.argv[1]); rows=[]
    for name,events,_ in CASES:
        for delivery,perm in enumerate(itertools.permutations(events)):
            chain=list(perm)
            count=COUNTS[name]
            capsule={'object_ref':'object-A','events':chain,'expected_count':count,'predictions_are_observed':False,'input_authority':False}
            rows.append(dict(case=name,delivery=delivery,final_state=0,chain=chain,expected_count=count,capsule=capsule,
                final_only='NOT_RUN',raw_chain=classify_complete(chain,count),typed_event=classify_complete(capsule['events'],count),
                raw_input_bytes=len(canonical({'events':chain,'expected_count':count}).encode()),
                raw_bytes=len(canonical(chain).encode()),event_bytes=len(canonical(capsule).encode())))
    with (out/'raw.jsonl').open('x') as f:
        for row in rows: f.write(canonical(row)+'\n')
    resources={}
    for name in ['cpu.max','memory.max','memory.swap.max','pids.max']:
        p=Path('/sys/fs/cgroup')/name; resources[name]=p.read_text().strip() if p.exists() else 'UNAVAILABLE'
    with (out/'ENV.json').open('x') as f: json.dump({'python':sys.version,'cgroups':resources,'scope':'SYNTHETIC_FINITE_T0','native_calls':0,'model_calls':0},f,indent=2)
    print(json.dumps({'rows':len(rows),'raw_sha256':hashlib.sha256((out/'raw.jsonl').read_bytes()).hexdigest()}))
if __name__=='__main__':main()
