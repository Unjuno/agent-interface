import copy,json,pathlib,sys,subprocess,tempfile
R=pathlib.Path(__file__).parent; base=json.loads((R/'FORMAL_V2.json').read_text())
def check(d):
 # Inline corrected gate, deliberately independent of frozen audit.py.
 DEPS=['form_generation','required_form_generation','intent_version','producer_version','source_generation','source_current','intent']
 def truth(s):
  if type(s.get('source_current')) is not bool:return None
  if any(type(s.get(k)) is not int or s[k]<0 for k in DEPS[:5]):return None
  if s.get('intent') not in {'submit','inspect'}:return None
  if not s['source_current']:return 'UNKNOWN'
  return 'TRUE' if s['form_generation']==s['required_form_generation'] and s['intent']=='submit' else 'FALSE'
 def key(s): return tuple(s.get(k) for k in DEPS)
 if d.get('schema')!='predicate-persist-formal-v1' or len(d.get('rows',[]))!=48 or len(d.get('controls',[]))!=4:return False
 seen=set(); vals={'ch':0,'cs':0,'cw':0,'nh':0,'nw':0,'nu':0,'ns':0}
 for r in d['rows']:
  ident=(r.get('rep'),r.get('case'),r.get('policy'))
  if ident in seen:return False
  seen.add(ident); o=truth(r.get('after',{})); res=r.get('result',{}); same=key(r.get('before',{}))==key(r.get('after',{}))
  if o is None or res.get('oracle')!=o or r.get('prepare_exit')!=0 or r.get('consume_exit')!=0:return False
  if r.get('policy')=='DEPENDENCY_BOUND_PERSIST': vals['ch']+=int(res.get('reused') is True); vals['cs']+=int(res.get('reused') is True and not same); vals['cw']+=int(res.get('value')!=o)
  elif r.get('policy')=='VALUE_ONLY_PERSIST': vals['nh']+=int(res.get('reused') is True); vals['nw']+=int(res.get('value')!=o); vals['nu']+=int(res.get('executable') is True and o!='TRUE'); vals['ns']+=int(res.get('reused') is True and not same)
  else:return False
 if vals!={'ch':6,'cs':0,'cw':0,'nh':24,'nw':9,'nu':6,'ns':18}:return False
 if any(c.get('exit')!=0 or c.get('result',{}).get('reused') is True for c in d['controls']):return False
 return True
m=[]
def add(n,f): d=copy.deepcopy(base); f(d); m.append((n,d))
add('DROP_ROW',lambda d:d['rows'].pop()); add('DUP_ROW',lambda d:d['rows'].append(copy.deepcopy(d['rows'][0]))); add('ALTER_VALUE',lambda d:d['rows'][0]['result'].__setitem__('value','FALSE')); add('ALTER_REUSED',lambda d:d['rows'][0]['result'].__setitem__('reused',False)); add('ALTER_CASE',lambda d:d['rows'][0].__setitem__('case','BOGUS')); add('ALTER_AFTER_GENERATION',lambda d:d['rows'][0]['after'].__setitem__('form_generation',99)); add('BOOL_GENERATION',lambda d:d['rows'][0]['after'].__setitem__('intent_version',True)); add('MISSING_EXIT',lambda d:d['rows'][0].pop('consume_exit')); add('ALTER_ORACLE',lambda d:d['rows'][0]['result'].__setitem__('oracle','FALSE')); add('DROP_CONTROL',lambda d:d['controls'].pop())
expected_cases={'SAME','IRRELEVANT_CHANGE','FORM_DEP_CHANGE','SEMANTIC_ABA_NEW_GENERATION','INTENT_CHANGE','PRODUCER_CHANGE','SOURCE_REPLACED','SOURCE_STALE'}
def robust(d):
 if not check(d): return False
 return {r.get('case') for r in d['rows']}==expected_cases
res=[{'name':n,'rejected':not robust(d)} for n,d in m]
out={'baseline_pass':robust(base),'results':res,'rejected':sum(x['rejected'] for x in res),'total':len(res),'pass':robust(base) and all(x['rejected'] for x in res),'diagnostic_only':True}
(R/'CONTROLS_POSTFORMAL_V3.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n'); print(json.dumps(out,sort_keys=True)); sys.exit(0 if out['pass'] else 1)
