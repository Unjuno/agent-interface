import json,pathlib,sys
R=pathlib.Path(__file__).parent; D=json.loads((R/'FORMAL_V2.json').read_text())
DEPS=['form_generation','required_form_generation','intent_version','producer_version','source_generation','source_current','intent']
def truth(s):
 if type(s.get('source_current')) is not bool:return None
 if any(type(s.get(k)) is not int or s[k]<0 for k in DEPS[:5]):return None
 if s.get('intent') not in {'submit','inspect'}:return None
 if not s['source_current']:return 'UNKNOWN'
 return 'TRUE' if s['form_generation']==s['required_form_generation'] and s['intent']=='submit' else 'FALSE'
def key(s): return tuple(s.get(k) for k in DEPS)
errs=[]; seen=set(); m={'candidate_hits':0,'candidate_stale_hits':0,'candidate_wrong_rows':0,'naive_hits':0,'naive_wrong_rows':0,'naive_unsafe_exec_rows':0,'naive_stale_provenance_reuse_rows':0}
for r in D.get('rows',[]):
 ident=(r.get('rep'),r.get('case'),r.get('policy'))
 if ident in seen: errs.append('duplicate');
 seen.add(ident)
 o=truth(r.get('after',{})); res=r.get('result',{}); same=key(r.get('before',{}))==key(r.get('after',{}))
 if o is None: errs.append('state')
 if res.get('oracle')!=o or res.get('value') not in {'TRUE','FALSE','UNKNOWN'}: errs.append('oracle')
 if r.get('prepare_exit')!=0 or r.get('consume_exit')!=0 or r.get('prepare_stderr') or r.get('consume_stderr'): errs.append('exit')
 if r.get('policy')=='DEPENDENCY_BOUND_PERSIST':
  m['candidate_hits']+=int(res.get('reused') is True); m['candidate_stale_hits']+=int(res.get('reused') is True and not same); m['candidate_wrong_rows']+=int(res.get('value')!=o)
 elif r.get('policy')=='VALUE_ONLY_PERSIST':
  m['naive_hits']+=int(res.get('reused') is True); m['naive_wrong_rows']+=int(res.get('value')!=o); m['naive_unsafe_exec_rows']+=int(res.get('executable') is True and o!='TRUE'); m['naive_stale_provenance_reuse_rows']+=int(res.get('reused') is True and not same)
 else: errs.append('policy')
if len(D.get('rows',[]))!=48 or len(seen)!=48: errs.append('denominator')
cs=D.get('controls',[])
if len(cs)!=4 or any(c.get('exit')!=0 or c.get('stderr') or c.get('result',{}).get('reused') is True for c in cs): errs.append('controls')
expected={'candidate_hits':6,'candidate_stale_hits':0,'candidate_wrong_rows':0,'naive_hits':24,'naive_wrong_rows':9,'naive_unsafe_exec_rows':6,'naive_stale_provenance_reuse_rows':18}
if m!=expected: errs.append('metric_gate')
out={'status':'PASS_POSTFORMAL_DIAGNOSTIC_ONLY','errors':sorted(set(errs)),'metrics':m,'expected':expected,'rows':len(D.get('rows',[])),'controls':len(cs),'does_not_override_formal_hold':True}
out['pass']=not out['errors']
(R/'AUDIT_POSTFORMAL_V3.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n'); print(json.dumps(out,sort_keys=True)); sys.exit(0 if out['pass'] else 1)
