import itertools,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
def decide(obs,mode):
 expected={'a':True}
 if mode=='full':projected=dict(obs)
 elif mode=='effect_only':projected={k:obs[k] for k in expected}
 elif mode=='effect_plus_verifier':projected={k:obs[k] for k in {'a','b'}}
 else:raise ValueError(mode)
 if any(k not in projected for k in expected):return 'EFFECT_UNAVAILABLE'
 if any(projected[k]!=v for k,v in expected.items()):return 'EFFECT_FAILED'
 if 'b' not in projected:return 'VERIFY_UNAVAILABLE'
 if projected['b'] is not True:return 'VERIFY_FAILED'
 return 'SUCCEEDED'
rows=[]
for a,b,c in itertools.product([False,True],repeat=3):
 obs={'a':a,'b':b,'c':c};base=decide(obs,'full')
 for mode in ('effect_only','effect_plus_verifier'):
  got=decide(obs,mode);rows.append({'obs':obs,'mode':mode,'baseline':base,'got':got,'match':got==base})
summary={m:{'matches':sum(r['match'] for r in rows if r['mode']==m),'cases':sum(1 for r in rows if r['mode']==m)} for m in ('effect_only','effect_plus_verifier')}
assert summary['effect_only']['matches']<summary['effect_only']['cases']
assert summary['effect_plus_verifier']['matches']==summary['effect_plus_verifier']['cases']
result={'pass':True,'summary':summary,'rows':rows,'conclusion':'effect-scoped acquisition is incomplete if verifier reads extra observation predicates; explicit verifier deps restore equivalence'}
(OUT/'verifier_dependency_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
