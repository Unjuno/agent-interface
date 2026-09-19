#!/usr/bin/env python3
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path

def main(root: Path):
    summary=json.loads((root/'result.json').read_text()); errors=[]
    if summary.get('rerun_budget') != 0: errors.append('rerun_budget')
    rows=summary.get('rows',[])
    if len(rows)!=6: errors.append('row_count')
    seen=set(); broad_truth=0; observed_truth=0; broad_false_contention=0
    for r in rows:
        cid=r['case_id'];
        if cid in seen: errors.append(f'duplicate:{cid}')
        seen.add(cid)
        db=root/cid/'case.sqlite'; c=sqlite3.connect(db)
        kv={k:(v,int(rev)) for k,v,rev in c.execute('select key,value,revision from kv order by key')}
        generation=int(c.execute('select generation from coordination where id=1').fetchone()[0])
        events=list(c.execute('select kind,detail from events order by seq')); c.close()
        expected_keys=['A','B','U'] if r['policy']=='broad' else ['A','B']
        if [x['key'] for x in r['token']] != expected_keys: errors.append(f'token_keys:{cid}')
        truth_commit=r['scenario']!='relevant_A_change'
        if r['truth_commit'] != truth_commit or r['truthful'] != (r['committed']==truth_commit): errors.append(f'truth:{cid}')
        if generation != (2 if r['committed'] else 1): errors.append(f'generation:{cid}')
        gen_events=[e for e in events if e[0]=='generation']
        if len(gen_events)!=(1 if r['committed'] else 0): errors.append(f'gen_events:{cid}')
        if r['scenario']=='relevant_A_change' and kv['A'] != ('a2',2): errors.append(f'A_mutation:{cid}')
        if r['scenario']=='unrelated_U_change' and kv['U'] != ('u2',2): errors.append(f'U_mutation:{cid}')
        if r['policy']=='broad':
            broad_truth += int(r['truthful'])
            if r['scenario']=='unrelated_U_change' and not r['committed'] and not r['truthful']: broad_false_contention += 1
        else: observed_truth += int(r['truthful'])
    decision='PASS_OBSERVED_READ_RECEIPTS_SCOPED' if not errors and observed_truth==3 and broad_truth==2 and broad_false_contention==1 else 'FAIL'
    audit={'decision':decision,'errors':errors,'observed_truth':observed_truth,'broad_truth':broad_truth,'broad_false_contention':broad_false_contention,'rows':len(rows)}
    (root/'audit.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n'); print(json.dumps(audit,sort_keys=True)); return 0 if decision.startswith('PASS_') else 1
if __name__=='__main__': raise SystemExit(main(Path(sys.argv[1]).resolve()))
