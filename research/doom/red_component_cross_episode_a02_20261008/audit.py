from pathlib import Path
import argparse,json,hashlib
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--repo-root',required=True);root=Path(ap.parse_args().repo_root)
run=root/'research/doom/results/map01-fixed-threat-v28-live-01';inp=json.loads((P/'INPUTS.json').read_text());res=json.loads((P/'RESULT.json').read_text())
manifest_bytes=(run/'retention-manifest.json').read_bytes();events_bytes=(run/'runtime/events.jsonl').read_bytes();source_audit_bytes=(run/'audit.json').read_bytes()
assert hashlib.sha256(manifest_bytes).hexdigest()==inp['manifest_sha256']
assert hashlib.sha256(events_bytes).hexdigest()==inp['events_sha256']
assert hashlib.sha256(source_audit_bytes).hexdigest()==inp['source_audit_sha256']
manifest=json.loads(manifest_bytes);events=[json.loads(s) for s in events_bytes.splitlines() if s.strip()]
source_audit=json.loads(source_audit_bytes);assert source_audit['threat_exposed_by_exact_frame_review'] is True
x0,y0,x1,y1=inp['crop_xyxy']
def counts(mask):
 h,w=mask.shape;parent=[0];area=[0];prev=[]
 def find(i):
  while i!=parent[i]:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def union(a,b):
  a=find(a);b=find(b)
  if a!=b:parent[b]=a
 for y in range(h):
  xs=np.flatnonzero(mask[y]);spans=[]
  if len(xs):
   starts=[int(xs[0])];ends=[]
   for a,b in zip(xs[:-1],xs[1:]):
    if b>a+1:ends.append(int(a));starts.append(int(b))
   ends.append(int(xs[-1]))
   for a,b in zip(starts,ends):
    label=len(parent);parent.append(label);area.append(b-a+1)
    for pa,pb,pl in prev:
     if pb<a-1:continue
     if pa>b+1:break
     union(label,pl)
    spans.append((a,b,label))
  prev=spans
 out={}
 for i in range(1,len(parent)):
  r=find(i);out[r]=out.get(r,0)+area[i]
 return sum(8<=n<=256 for n in out.values())
rows=[]
for r in inp['positive_sequences']:
 seq=r['sequence'];rel=r['manifest_path'];entry=next(f for f in manifest['files'] if f['path']==rel)
 path=run/rel;digest=hashlib.sha256(path.read_bytes()).hexdigest()
 assert entry['sha256']==digest==r['sha256']
 ev=next(e for e in events if e.get('event')=='observation' and e.get('sequence')==seq)
 assert ev['image'].replace('\\','/').endswith('/'+rel)
 rgb=np.asarray(Image.open(path).convert('RGB'))[y0:y1,x0:x1]
 R,G,B=[rgb[:,:,i].astype(np.int16) for i in range(3)];mask=(R>70)&(R*4>5*G)&(R*4>5*B)
 c=counts(mask);pred=c<inp['fixed_threshold'];claimed=next(x for x in res['rows'] if x['sequence']==seq)
 assert c==claimed['small_component_count'] and pred==claimed['predicted_enemy']
 rows.append({'sequence':seq,'component_count':c,'predicted_enemy':pred})
assert len(rows)==7 and sum(r['predicted_enemy'] for r in rows)==0 and res['decision']=='FAIL_SCOPED'
report={'status':'PASS_INDEPENDENT_CROSS_EPISODE_AUDIT_SCOPED','source_episode':inp['episode'],'source_hashes':{'retention_manifest':inp['manifest_sha256'],'events':inp['events_sha256'],'source_audit':inp['source_audit_sha256']},'rows_recomputed':rows,'audit_scope':'provenance, event/image joins, and arithmetic only; labels are not independently adjudicated','checks':['source retention manifest hash','source event stream hash','source audit hash','per-frame hash against manifest and INPUTS','observation sequence to image-path join','8-connected component counts via row-run union-find','result rows and fail disposition match']}
(P/'AUDIT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
