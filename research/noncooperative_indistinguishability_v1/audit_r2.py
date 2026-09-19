import json,sys,hashlib,collections
from pathlib import Path

def sha(b):return hashlib.sha256(b).hexdigest()
def main(root):
 root=Path(root);rs=[json.loads(x) for x in (root/'raw.jsonl').read_text().splitlines() if x.strip()];assert len(rs)==120
 bad=[];counts=collections.Counter();by=collections.defaultdict(list)
 for r in rs:
  assert all(r['checks'].values()),r['id'];by[(r['block'],r['mode'])].append(r);eff=json.loads((root/r['effect_file']).read_text()) if r['effect_file'] else None
  expected_n=1 if r['mode']=='one_frame_act' else 10
  if len(r['history'])!=expected_n or r['decision']['frames_seen']!=expected_n:bad.append((r['id'],'history_len'))
  if len({json.dumps(x,sort_keys=True) for x in r['history']})!=1:bad.append((r['id'],'history_changed_within_trial'))
  if not eff:bad.append((r['id'],'no_effect'));continue
  b=eff['before'];a=b['active'];d=b['docs'][a];correct=(a=='A' and d['revision']==0 and d['value']==0);counts[(r['mode'],r['case'],'correct' if correct else 'wrong')]+=1
  if correct!=(r['case']=='stable'):bad.append((r['id'],'class',correct))
 for k,g in by.items():
  if len(g)!=3:bad.append((k,'group_size',len(g)));continue
  histories=[json.dumps(r['history'],sort_keys=True) for r in g]
  if len(set(histories))!=1:bad.append((k,'world_histories_differ'))
 for n,h in json.loads((root/'manifest.json').read_text()).items():
  if sha((root/n).read_bytes())!=h:bad.append(('hash',n))
 if bad:raise AssertionError(bad[:20])
 out={'checked_rows':120,'indistinguishable_world_history_groups':len(by),'counts':{'|'.join(k):v for k,v in counts.items()},'bad':bad};(root/'audit_r2.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main(sys.argv[1])
