"""Independent audit of observation indistinguishability and outcomes."""
import json,sys,hashlib,collections
from pathlib import Path

def sha(b):return hashlib.sha256(b).hexdigest()
def main(root):
 root=Path(root);rows=[json.loads(x) for x in (root/'raw.jsonl').read_text().splitlines() if x.strip()];assert len(rows)==180
 counts=collections.Counter();bad=[];by=collections.defaultdict(list)
 for r in rows:
  assert all(r['checks'].values()),r['id'];by[(r['block'],r['mode'])].append(r);eff=json.loads((root/r['effect_file']).read_text()) if r['effect_file'] else None
  if r['mode']=='visible_act':
   if not eff:bad.append((r['id'],'visible_did_not_act'))
   else:
    b=eff['before'];a=b['active'];d=b['docs'][a];correct=(a=='A' and d['revision']==0 and d['value']==0);counts[(r['mode'],r['case'],'correct' if correct else 'wrong')]+=1
    if correct!=(r['case']=='stable'):bad.append((r['id'],'effect_class',correct))
  elif r['mode']=='dependency_required':
   if eff or r['decision']['act']:bad.append((r['id'],'yield_failed'))
   counts[(r['mode'],r['case'],'yield')]+=1
  else:bad.append((r['id'],'mode'))
 for k,group in by.items():
  if len(group)!=3:bad.append((k,'group_size',len(group)));continue
  sigs=[json.dumps(r['signature'],sort_keys=True) for r in group]
  if len(set(sigs))!=1:bad.append((k,'observable_signatures_differ'))
  frames=[r['frames'][1]['pixels_sha256'] for r in group]
  if len(set(frames))!=1:bad.append((k,'frame_pixels_differ'))
 for n,h in json.loads((root/'manifest.json').read_text()).items():
  if sha((root/n).read_bytes())!=h:bad.append(('hash',n))
 if bad:raise AssertionError(bad[:20])
 out={'checked_rows':180,'indistinguishable_triplets':len(by),'counts':{'|'.join(k):v for k,v in counts.items()},'bad':bad};(root/'audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main(sys.argv[1])
