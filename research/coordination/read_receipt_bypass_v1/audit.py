#!/usr/bin/env python3
from pathlib import Path
import json,sqlite3,sys

def main(root:Path):
    s=json.loads((root/'result.json').read_text()); errors=[]; rows=s.get('rows',[]); seen=set()
    if s.get('rerun_budget')!=0: errors.append('rerun_budget')
    if len(rows)!=4: errors.append('row_count')
    for r in rows:
        cid=r['case_id'];
        if cid in seen: errors.append(f'duplicate:{cid}')
        seen.add(cid); c=sqlite3.connect(root/cid/'case.sqlite'); kv={k:(v,int(rev)) for k,v,rev in c.execute('select key,value,revision from kv order by key')}; g=int(c.execute('select generation from coordination where id=1').fetchone()[0]); events=list(c.execute('select kind,detail from events order by seq')); c.close()
        expected_keys=['A','B'] if r['mode']=='tracked' else ['A']
        if [x['key'] for x in r['token']]!=expected_keys: errors.append(f'token:{cid}')
        if r['decision']!='a1|b1': errors.append(f'decision:{cid}')
        truth=r['scenario']=='stable'
        if r['truth_commit']!=truth or r['truthful']!=(r['committed']==truth): errors.append(f'truth:{cid}')
        if r['scenario']=='B_change' and kv['B']!=('b2',2): errors.append(f'B:{cid}')
        if g!=(2 if r['committed'] else 1): errors.append(f'generation:{cid}')
        if len([e for e in events if e[0]=='generation'])!=(1 if r['committed'] else 0): errors.append(f'event:{cid}')
    by={(r['mode'],r['scenario']):r for r in rows}
    expected=(by.get(('tracked','stable'),{}).get('committed') is True and by.get(('tracked','B_change'),{}).get('committed') is False and by.get(('bypass','stable'),{}).get('committed') is True and by.get(('bypass','B_change'),{}).get('committed') is True and by.get(('bypass','B_change'),{}).get('truthful') is False)
    decision='RETAIN_READ_RECEIPT_BYPASS_BOUNDARY_SCOPED' if not errors and expected else 'FAIL'
    a={'decision':decision,'errors':errors,'rows':len(rows),'unsafe_bypass_stale_commit':bool(by.get(('bypass','B_change'),{}).get('committed') and not by.get(('bypass','B_change'),{}).get('truthful'))}; (root/'audit.json').write_text(json.dumps(a,indent=2,sort_keys=True)+'\n'); print(json.dumps(a,sort_keys=True)); return 0 if decision.startswith('RETAIN_') else 1
if __name__=='__main__': raise SystemExit(main(Path(sys.argv[1]).resolve()))
