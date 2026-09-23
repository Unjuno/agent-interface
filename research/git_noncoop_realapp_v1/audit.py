import json,hashlib,collections,sys,statistics
from pathlib import Path

def sha(b):return hashlib.sha256(b).hexdigest()
def main(root):
 root=Path(root);rs=[json.loads(x) for x in (root/'raw.jsonl').read_text().splitlines()];assert len(rs)==12;m=json.loads((root/'prereg.json').read_text());A,B,C=m['A'],m['B'],m['C'];bad=[];by=collections.defaultdict(list);cnt=collections.Counter()
 for r in rs:
  by[(r['block'],r['policy'])].append(r)
  if len(r['observation']['pixel_hashes'])!=5:bad.append((r['block'],r['policy'],r['world'],'history'))
  if len(set(r['observation']['pixel_hashes']))!=1:bad.append((r['block'],r['policy'],r['world'],'visual_changed_within_history'))
  if r['policy']=='visible_blind_act':
   if not r['terminal'] or not r['action_events']:bad.append(('missing_action',r['block'],r['world']))
   if r['world']=='stable':ok=r['final_ref']==B and r['classification']=='correct'
   else:ok=r['final_ref']==B and r['classification']=='wrong_overwrite'
  else:
   if r['action_events'] or r['terminal']:bad.append(('yield_acted',r['block'],r['world']))
   ok=(r['final_ref']==A and r['classification']=='yield_completeness_loss') if r['world']=='stable' else (r['final_ref']==C and r['classification']=='safe_yield')
  if not ok:bad.append(('outcome',r))
  cnt[(r['policy'],r['world'],r['classification'])]+=1
 for k,g in by.items():
  if len(g)!=2:bad.append((k,'pair_size'));continue
  o=[r['observation'] for r in g];sig=[(x['pixel_hashes'],x['focus'],x['window_id'],x['geometry']) for x in o]
  if sig[0]!=sig[1]:bad.append((k,'world_observation_diff'))
 for n,h in json.loads((root/'manifest.json').read_text()).items():
  if sha((root/n).read_bytes())!=h:bad.append(('hash',n))
 if bad:raise AssertionError(bad[:20])
 spans=[(r['observation']['end_ns']-r['observation']['start_ns'])/1e6 for r in rs];out={'passed':True,'rows':12,'identical_world_pairs':len(by),'history_span_ms':{'median':statistics.median(spans),'min':min(spans),'max':max(spans)},'counts':{'|'.join(k):v for k,v in cnt.items()}};(root/'audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main(sys.argv[1])
