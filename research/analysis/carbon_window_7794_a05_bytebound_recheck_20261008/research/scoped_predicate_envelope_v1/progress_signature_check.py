import itertools,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
def sig(vals,keys):return tuple((k,vals.get(k,'MISSING')) for k in keys)
def classify_effect(pre,post,mode):
 keys=['a','c'] if mode=='full_digest' else ['a']
 if sig(pre,keys)==sig(post,keys):return 'NO_RELEVANT_PROGRESS'
 if post['a']=='unknown':return 'EFFECT_UNAVAILABLE'
 if post['a'] is not True:return 'EFFECT_FAILED'
 return 'SUCCEEDED'
def truth_effect(pre,post):
 if post['a']==pre['a']:return 'NO_RELEVANT_PROGRESS'
 if post['a']=='unknown':return 'EFFECT_UNAVAILABLE'
 if post['a'] is not True:return 'EFFECT_FAILED'
 return 'SUCCEEDED'
rows=[];pre={'a':False,'c':False}
for a,c in itertools.product([False,True,'unknown'],[False,True]):
 post={'a':a,'c':c};truth=truth_effect(pre,post)
 for mode in ('full_digest','effect_signature'):
  got=classify_effect(pre,post,mode);rows.append({'experiment':'effect','post':post,'mode':mode,'truth':truth,'got':got,'match':got==truth})
def classify_verifier(pre,post,mode):
 keys=['a'] if mode=='effect_only' else ['a','b']
 if sig(pre,keys)==sig(post,keys):return 'NO_RELEVANT_PROGRESS'
 if post['a']=='unknown':return 'EFFECT_UNAVAILABLE'
 if post['a'] is not True:return 'EFFECT_FAILED'
 if post['b']=='unknown':return 'VERIFY_UNAVAILABLE'
 if post['b'] is not True:return 'VERIFY_FAILED'
 return 'SUCCEEDED'
def truth_verifier(pre,post):return classify_verifier(pre,post,'effect_plus_verifier')
pre2={'a':True,'b':False}
for a,b in itertools.product([True,'unknown'],[False,True,'unknown']):
 post={'a':a,'b':b};truth=truth_verifier(pre2,post)
 for mode in ('effect_only','effect_plus_verifier'):
  got=classify_verifier(pre2,post,mode);rows.append({'experiment':'verifier','post':post,'mode':mode,'truth':truth,'got':got,'match':got==truth})
summary={}
for exp in ('effect','verifier'):
 for mode in sorted({r['mode'] for r in rows if r['experiment']==exp}):
  rs=[r for r in rows if r['experiment']==exp and r['mode']==mode];summary[f'{exp}:{mode}']={'matches':sum(r['match'] for r in rs),'cases':len(rs),'mismatches':[r for r in rs if not r['match']]}
assert summary['effect:effect_signature']['matches']==6 and summary['effect:full_digest']['matches']<6
assert summary['verifier:effect_plus_verifier']['matches']==6 and summary['verifier:effect_only']['matches']<6
result={'summary':summary,'rows':rows,'decision':'SEPARATE_CANONICAL_EVIDENCE_IDENTITY_FROM_PROGRESS_SIGNATURE; PROGRESS_SIGNATURE_DEPENDS_ON_PENDING_EFFECT_PLUS_VERIFIER_DEPS'}
(OUT/'progress_signature_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
