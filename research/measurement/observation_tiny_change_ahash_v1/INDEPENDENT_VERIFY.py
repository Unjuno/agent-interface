from __future__ import annotations
import argparse,json,random,copy
from pathlib import Path
SEED=155920260918001
COUNTS=[('UNCHANGED',30000),('SINGLE_PIXEL',30000),('STATUS_DOT_2X2',25000),('CURSOR_1X3',20000),('GLYPH_STROKE_1X4',20000),('LOCAL_BLOCK_4X4',15000),('HASH_FLIP',10000)]
POSITIONS={'SINGLE_PIXEL':[0],'STATUS_DOT_2X2':[0,1,8,9],'CURSOR_1X3':[0,8,16],'GLYPH_STROKE_1X4':[0,1,2,3],'LOCAL_BLOCK_4X4':[0,1,2,3,8,9,10,11,16,17,18,19,24,25,26,27],'HASH_FLIP':list(range(64))}

def block_values(i):
 sh=i&1
 return [((176 if ((b+sh)&1) else 80)+(((i*17+b*13)%11)-5)) for b in range(64)]

def independent_hash_pair(i,fam):
 vals=block_values(i)
 before=[v*64 for v in vals]
 after=before[:]
 changed=fam!='UNCHANGED'
 if changed:
  b=(i*7+3)%64; target=255 if vals[b]<128 else 0
  after[b]+=sum(target-vals[b] for _ in POSITIONS[fam])
 def bits(sums):
  total=sum(sums); result=0
  for b,s in enumerate(sums):
   if 64*s>=total: result |= (1<<b)
  return result
 return bits(before)==bits(after), changed

def expected():
 sched=[]
 for fam,n in COUNTS:sched.extend([fam]*n)
 random.Random(SEED).shuffle(sched)
 fm={fam:{'pairs':0,'must_forward':0,'hash_equal':0,'hash_diff':0,'ahash_false_suppress':0,'ahash_false_forward':0,'fallback_calls':0,'fallback_false_suppress':0,'fallback_suppressed_exact':0,'fallback_forwarded_change':0} for fam,_ in COUNTS}
 for i,fam in enumerate(sched):
  heq,changed=independent_hash_pair(i,fam); m=fm[fam]
  m['pairs']+=1; m['must_forward']+=int(changed); m['hash_equal']+=int(heq); m['hash_diff']+=int(not heq)
  m['ahash_false_suppress']+=int(changed and heq); m['ahash_false_forward']+=int((not changed) and (not heq))
  m['fallback_calls']+=int(heq); m['fallback_false_suppress']+=0
  m['fallback_suppressed_exact']+=int((not changed) and heq)
  m['fallback_forwarded_change']+=int(changed)
 return fm

def verify(result):
 exp=expected(); errors=[]
 if result.get('family_metrics')!=exp: errors.append('family_metrics')
 totals={k:sum(m[k] for m in exp.values()) for k in next(iter(exp.values()))}
 if result.get('totals')!=totals: errors.append('totals')
 if result.get('corpus_errors')!=0: errors.append('corpus_errors')
 return {'pass':not errors,'errors':errors,'expected_family_metrics':exp,'expected_totals':totals}

def controls(result):
 out={}
 q=copy.deepcopy(result); q['family_metrics']['SINGLE_PIXEL']['hash_equal']-=1; out['hash_equal']=not verify(q)['pass']
 q=copy.deepcopy(result); q['totals']['ahash_false_suppress']-=1; out['total']=not verify(q)['pass']
 q=copy.deepcopy(result); q['family_metrics']['HASH_FLIP']['hash_diff']=0; out['positive_control']=not verify(q)['pass']
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out');a=ap.parse_args()
 r=json.loads(Path(a.result).read_text());v=verify(r);v['corruption_controls']=controls(r);v['controls_pass']=all(v['corruption_controls'].values());v['pass']=v['pass'] and v['controls_pass']
 s=json.dumps(v,indent=2,sort_keys=True)+'\n';print(s,end='')
 if a.out:Path(a.out).write_text(s)
 raise SystemExit(0 if v['pass'] else 4)
if __name__=='__main__':main()
