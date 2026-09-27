import json,hashlib,collections,sys,statistics
from pathlib import Path

def sha(b):return hashlib.sha256(b).hexdigest()
def main(root):
 root=Path(root);rs=[json.loads(x) for x in (root/'raw.jsonl').read_text().splitlines()];assert len(rs)==18;m=json.loads((root/'prereg.json').read_text());A,B,C=m['A'],m['B'],m['C'];bad=[];cnt=collections.Counter();by=collections.defaultdict(list)
 for r in rs:
  by[(r['block'],r['case'])].append(r);assert r['checked']['refs']=={'r1':A,'r2':A,'guard':A};assert r['competitor_start_ns']>=r['checked']['ns'];assert r['terminal']['start_ns']>=r['competitor_end_ns'];a=r['after']
  if r['case']=='stable':ok=a=={'r1':B,'r2':B,'guard':A,'other':A} and r['terminal']['rc']==0;cl='correct_effect'
  elif r['case']=='unrelated_changed':ok=a=={'r1':B,'r2':B,'guard':A,'other':C} and r['terminal']['rc']==0;cl='correct_unrelated_progress'
  elif r['mode']=='write_set_only':ok=a=={'r1':B,'r2':B,'guard':C,'other':A} and r['terminal']['rc']==0;cl='stale_effect_missing_dependency'
  else:ok=a=={'r1':A,'r2':A,'guard':C,'other':A} and r['terminal']['rc']!=0;cl='safe_reject_complete_dependency'
  if not ok or r['classification']!=cl:bad.append(r)
  cnt[(r['case'],r['mode'],cl)]+=1
 for k,g in by.items():
  if len(g)!=2 or {r['mode'] for r in g}!={'write_set_only','complete_dependency'}:bad.append((k,'pair'))
 for n,h in json.loads((root/'manifest.json').read_text()).items():
  if sha((root/n).read_bytes())!=h:bad.append(('hash',n))
 if bad:raise AssertionError(bad[:5])
 d={m:[(r['terminal']['end_ns']-r['terminal']['start_ns'])/1e6 for r in rs if r['mode']==m] for m in ['write_set_only','complete_dependency']};out={'passed':True,'rows':18,'counts':{'|'.join(k):v for k,v in cnt.items()},'timing_ms':{m:{'median':statistics.median(x),'min':min(x),'max':max(x)} for m,x in d.items()}};(root/'audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main(sys.argv[1])
