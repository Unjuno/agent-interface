import argparse,json,hashlib
from pathlib import Path
OPS=('OBS0','OBS1','VALIDATE','COMMIT','ADVANCE','CONTRADICT','REOBSERVE','ACTION')
KEYS=('transitions','mismatch','candidate_stale_safe','candidate_contradicted_safe','commit_from_unvalidated','fresh_recommit_safe','history_retained_after_advance','committed_only_unsafe','candidate_safe','candidate_blocked')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--dir',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();rows=[];digests=[]
 for op in OPS:
  p=Path(a.dir)/f'batch_{op}.json';r=json.loads(p.read_text());assert r['prefix']==op and not r['construction'] and r['depth']==8;rows.append(r);digests.append(r['digest'])
 st={k:0 for k in KEYS};st['nodes']=1
 for r in rows:
  st['nodes']+=r['stats']['nodes']
  for k in KEYS:st[k]+=r['stats'][k]
 good=(st['mismatch']==0 and st['candidate_stale_safe']==0 and st['candidate_contradicted_safe']==0 and st['commit_from_unvalidated']==0 and st['fresh_recommit_safe']>0 and st['history_retained_after_advance']>0 and st['committed_only_unsafe']>0)
 z={'decision':'PASS_TRANSACTIONAL_BELIEF_ACTION_SAFE_BATCHED_SCOPED' if good else 'FAIL_INTEGRITY','depth':8,'prefixes':list(OPS),'batch_processes':8,'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,'stats':st,'batch_digests':digests}
 z['digest']=hashlib.sha256(json.dumps(z,sort_keys=True,separators=(',',':')).encode()).hexdigest();o.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True))
if __name__=='__main__':main()
