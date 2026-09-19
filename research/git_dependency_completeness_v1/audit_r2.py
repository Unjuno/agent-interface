import json,sys,collections
from pathlib import Path

def main(root):
 root=Path(root);rs=[json.loads(x) for x in (root/'raw.jsonl').read_text().splitlines()];assert len(rs)==900;bad=[];c=collections.Counter()
 for r in rs:
  if r['ns']<=0:bad.append((r['i'],'time'))
  c[(r['case'],r['mode'],r['classification'])]+=1
 expected={
 ('stable','write_only','correct_effect'):100,('stable','exact_guard','correct_effect'):100,('stable','overbroad','correct_effect'):100,
 ('guard_changed','write_only','stale_effect'):100,('guard_changed','exact_guard','safe_reject'):100,('guard_changed','overbroad','safe_reject'):100,
 ('unrelated_changed','write_only','correct_unrelated_progress'):100,('unrelated_changed','exact_guard','correct_unrelated_progress'):100,('unrelated_changed','overbroad','false_reject_unrelated'):100}
 if c!=collections.Counter(expected):bad.append(('counts',c))
 if bad:raise AssertionError(bad[:3])
 out={'passed':True,'rows':900,'counts':{'|'.join(k):v for k,v in c.items()}};(root/'audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main(sys.argv[1])
