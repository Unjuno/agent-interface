import argparse,json,pathlib
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--out',required=True); a=ap.parse_args()
root=pathlib.Path(a.root); rows=[]
for i in range(4):
 b=root/f'batch-{i}'
 end=json.loads((b/'END.json').read_text())
 if end.get('status')!='COMPLETE' or end.get('batch')!=i or end.get('cases')!=12: raise SystemExit(f'bad batch {i}')
 rows.extend(json.loads((b/'ROWS.json').read_text()))
if [r.get('case_index') for r in rows]!=list(range(48)): raise SystemExit('index/order mismatch')
pathlib.Path(a.out).write_text(json.dumps(rows,sort_keys=True,separators=(',',':'))+'\n')
print(json.dumps({'cases':len(rows),'status':'AGGREGATED'}))
