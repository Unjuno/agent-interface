import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]).resolve(); q=Path(sys.argv[2]); allocation=sys.argv[3]; r=json.loads(p.read_text()); e=[]
if r.get('schema')!='tk-map-barrier-v1': e.append('schema')
if r.get('allocation')!=allocation: e.append('allocation')
if r.get('app_exit')!=0: e.append('app_exit')
for k in ('Map','Configure'):
 if type(r.get('events',{}).get(k)) is not int or r['events'][k]>r.get('post',{}).get('t',0): e.append(k+'_order')
x=r.get('post',{}); root=x.get('root',[0,0,0,0]); cx=x.get('x',0)+x.get('w',0)//2; cy=x.get('y',0)+x.get('h',0)//2
if x.get('mapped')!=1 or x.get('w',0)<=1 or x.get('h',0)<=1: e.append('mapped_geometry')
if not(root[0]<=cx<root[0]+root[2] and root[1]<=cy<root[1]+root[3]): e.append('center')
if x.get('t',0)<r.get('pre',{}).get('t',0): e.append('clock')
z={'decision':'PASS_GEOMETRY_MAP_BARRIER_CONSTRUCTION_ONLY' if not e else 'STOP_GEOMETRY_MAP_BARRIER','errors':e,'raw_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'no input; no focus or delivery claim'}
q.write_text(json.dumps(z,sort_keys=True,indent=2)+'\n');print(json.dumps(z,sort_keys=True));raise SystemExit(bool(e))
