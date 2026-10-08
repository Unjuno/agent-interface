#!/usr/bin/env python3
import json, pathlib, sys
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'formal')
rows=[]
for b in [0,1]:
 r=json.loads((root/f'BATCH{b}.json').read_text())
 if r['status']!='COMPLETE' or len(r['rows'])!=8: raise SystemExit('batch incomplete')
 for meta in r['rows']:
  case_dir=pathlib.Path(meta['cmd'][meta['cmd'].index('--out')+1])
  d=json.loads((case_dir/'CASE.json').read_text()); d['meta']=meta; rows.append(d)
if len(rows)!=16 or len({(r['scenario'],r['rep']) for r in rows})!=16: raise SystemExit('denominator')
out={'allocation':'degraded-temporal-monitor-2255-20260922-01','cases':rows,'formal_reruns':0,'replacements':0,'tuning':0}
(root/'RUN.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':'AGGREGATED','cases':16},sort_keys=True))
