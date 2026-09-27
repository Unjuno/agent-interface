from __future__ import annotations
from itertools import combinations,product
import argparse,copy,json
from pathlib import Path
TASK='OBSERVATION-GATING-O3-MANIPULATE-DYNAMIC-CERTIFICATE-20260919-001'
DOMS=('T','D','E','S'); PHASES=('PREPARE','EFFECT_PENDING','TERMINAL')
UNION={'PREPARE':frozenset(('T','D','S')),'EFFECT_PENDING':frozenset(DOMS),'TERMINAL':frozenset(('E','S'))}

def dec(p,s):
 T,D,E,S=s
 if p=='PREPARE': return 'ABORT' if S else ('READY' if T and D else 'WAIT')
 if p=='EFFECT_PENDING': return 'ABORT' if S else ('COMPLETE' if E else ('CONTINUE' if T and D else 'WAIT'))
 return 'ABORT' if S else ('COMPLETE' if E else 'TERMINAL_UNRESOLVED')

def masks():
 for n in range(5):
  for c in combinations(DOMS,n): yield frozenset(c)

def valid(p,s,m):
 idx={d:i for i,d in enumerate(DOMS)}; d0=dec(p,s)
 for q in product((0,1),repeat=4):
  if all(s[idx[x]]==q[idx[x]] for x in m) and dec(p,q)!=d0:return False
 return True

def choose(p,s):
 vs=[m for m in masks() if valid(p,s,m)]
 vs.sort(key=lambda m:(len(m),tuple(DOMS.index(x) for x in DOMS if x in m)))
 return vs[0]

def derive():
 metrics={k:0 for k in ['current_states','transition_rows','certificate_validity_errors','minimality_errors','dynamic_false_suppressions','phase_union_false_suppressions','global_false_suppressions','dynamic_safe_suppressions','phase_union_safe_suppressions','dynamic_false_forwards','phase_union_false_forwards','global_false_forwards','strict_narrowing_states']}; sizes={p:{} for p in PHASES}; sel={}
 for p in PHASES:
  for s in product((0,1),repeat=4):
   c=choose(p,s); key=f'{p}:{"".join(map(str,s))}';sel[key]=''.join(x for x in DOMS if x in c) or '-';sizes[p][str(len(c))]=sizes[p].get(str(len(c)),0)+1;metrics['current_states']+=1
   if not valid(p,s,c):metrics['certificate_validity_errors']+=1
   if any(valid(p,s,m) and len(m)<len(c) for m in masks()):metrics['minimality_errors']+=1
   if c < UNION[p]:metrics['strict_narrowing_states']+=1
   for q in product((0,1),repeat=4):
    delta=frozenset(d for d,a,b in zip(DOMS,s,q) if a!=b);must=dec(p,s)!=dec(p,q);dyn=not bool(delta&c);uni=not bool(delta&UNION[p]);glob=not bool(delta);metrics['transition_rows']+=1
    metrics['dynamic_false_suppressions']+=int(dyn and must);metrics['phase_union_false_suppressions']+=int(uni and must);metrics['global_false_suppressions']+=int(glob and must);metrics['dynamic_safe_suppressions']+=int(dyn and not must);metrics['phase_union_safe_suppressions']+=int(uni and not must);metrics['dynamic_false_forwards']+=int((not dyn) and not must);metrics['phase_union_false_forwards']+=int((not uni) and not must);metrics['global_false_forwards']+=int((not glob) and not must)
 return metrics,sizes,sel

def evaluate(r):
 e=[];m,s,c=derive()
 if r.get('task')!=TASK:e.append('task')
 if (r.get('formal_invocations'),r.get('reruns'),r.get('replacements'),r.get('tuning'))!=(1,0,0,0):e.append('invocation')
 if r.get('metrics')!=m:e.append('metrics')
 if r.get('certificate_size_distribution')!=s:e.append('sizes')
 if r.get('selected_certificates')!=c:e.append('certificates')
 if m['dynamic_false_suppressions']!=0 or m['phase_union_false_suppressions']!=0 or m['global_false_suppressions']!=0:e.append('safety')
 if not (m['dynamic_false_forwards']<m['phase_union_false_forwards']<m['global_false_forwards']):e.append('narrowing_order')
 if not (m['dynamic_safe_suppressions']>m['phase_union_safe_suppressions']):e.append('suppression_gain')
 if m['strict_narrowing_states']<=0:e.append('strict_narrowing')
 if not isinstance(r.get('source_sha256'),dict) or not r['source_sha256']:e.append('source')
 return {'decision':'PASS_O3_MANIPULATE_DYNAMIC_CERTIFICATE_SCOPED' if not e else 'FAIL_INTEGRITY','pass':not e,'integrity_errors':sorted(e),'expected_metrics':m}

def controls(r):
 out={}
 def ck(n,fn):q=copy.deepcopy(r);fn(q);out[n]=not evaluate(q)['pass']
 ck('escape',lambda q:q['metrics'].__setitem__('dynamic_false_suppressions',1));ck('gain_loss',lambda q:q['metrics'].__setitem__('dynamic_safe_suppressions',q['metrics']['phase_union_safe_suppressions']));ck('minimality',lambda q:q['metrics'].__setitem__('minimality_errors',1));ck('cert',lambda q:q['selected_certificates'].__setitem__('PREPARE:1101','TDS'));ck('source',lambda q:q.__setitem__('source_sha256',{}));return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out');a=ap.parse_args();r=json.loads(Path(a.result).read_text());v=evaluate(r);cc=controls(r);v['corruption_controls']=cc;v['controls_pass']=all(cc.values());v['pass']=v['pass'] and v['controls_pass'];s=json.dumps(v,indent=2,sort_keys=True)+'\n';print(s,end='')
 if a.out:Path(a.out).write_text(s)
 raise SystemExit(0 if v['pass'] else 4)
if __name__=='__main__':main()
