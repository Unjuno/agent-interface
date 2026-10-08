import hashlib,json,sys
from pathlib import Path

def H(b): return hashlib.sha256(b).hexdigest()
def ch(x): return H(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode())
def expand(seq,m):
 out=[]
 for x in seq:
  if x.get('op')=='repeat':
   n=x.get('count')
   if type(n)!=int or not 0<=n<=m['bounds']['max_repeat']: raise ValueError('repeat_bound')
   out.extend(expand(x.get('body',[]),m)*n)
  else: out.append(x)
  if len(out)>m['bounds']['max_expanded_steps']: raise ValueError('step_bound')
 return out
def env(c,k): return c['transition_state'] if c['transition_after'] is not None and k>=c['transition_after'] else c['initial_state']
def src(code,c):
 e=[]; auth=None
 for x in code:
  if c['cancel_after'] is not None and len(e)==c['cancel_after']: return e+[['release'],['abort','cancel']]
  s=env(c,len(e)); op=x['op']
  if op=='guard':
   if not s['fresh'] or s['active_target']!=x['target']: return e+[['release'],['abort','stale' if not s['fresh'] else 'wrong_target']]
   auth=x['target']
  elif op=='write':
   if auth!=x['target'] or not s['fresh'] or s['active_target']!=x['target']: return e+[['release'],['abort','unauthorized']]
   e.append(['effect',x['target'],x['effect'],x['value']]); auth=None
  elif op=='wait': e.append(['wait',x['ticks']])
  elif op=='observe': e.append(['observe',x['channel']])
  elif op=='release': e.append(['release'])
  elif op=='abort': return e+[['release'],['abort',x['reason']]]
  elif op=='yield': return e+[['yield']]
  else: raise ValueError('unsupported_source:'+str(op))
 return e
def tgt(t,c):
 e=[]
 for x in t.get('program',[]):
  if c['cancel_after'] is not None and len(e)==c['cancel_after']:
   for h in t.get('on_cancel',[]): e.append(['release'] if h.get('op')=='RELEASE' else ['abort','cancel'] if h.get('op')=='ABORT_CANCEL' else ['trap','cancel_handler'])
   return e
  s=env(c,len(e)); op=x.get('op')
  if op=='CHECK':
   if not s['fresh'] or s['active_target']!=x.get('target'): return e+[['release'],['abort','stale' if not s['fresh'] else 'wrong_target']]
  elif op=='EMIT': e.append(['effect',x.get('target'),x.get('effect'),x.get('value')])
  elif op=='WAIT': e.append(['wait',x.get('ticks')])
  elif op=='OBSERVE': e.append(['observe',x.get('channel')])
  elif op=='RELEASE': e.append(['release'])
  elif op=='ABORT': return e+[['release'],['abort',x.get('reason')]]
  elif op=='ABORT_NO_RELEASE': return e+[['abort',x.get('reason')]]
  elif op=='YIELD': return e+[['yield']]
  elif op=='CONTINUE': pass
  elif op=='INTERNAL' and 'side_effect' in x: e.append(['forbidden',x['side_effect']])
  elif op!='INTERNAL': e.append(['trap',str(op)])
 return e
def contexts(code,m):
 st=[{'active_target':t,'fresh':f} for t in m['contexts']['active_targets'] for f in m['contexts']['fresh']]; n=len(code)
 trans=[(None,None)]+[(i,s) for i in range(1,n+1) for s in st]
 if len(st)*len(trans)*(n+1)>m['bounds']['max_contexts_per_artifact']: raise ValueError('context_bound')
 return [{'initial_state':a,'transition_after':i,'transition_state':b,'cancel_after':z} for a in st for i,b in trans for z in [None,*range(n)]]
def validate(s,t,m,mh,fh):
 try:
  code=expand(s['program'],m); cx=contexts(code,m)
  for c in cx:
   a,b=src(code,c),tgt(t,c)
   if a!=b: return {'status':'COUNTEREXAMPLE','contexts_checked':len(cx),'counterexample':{'context':c,'source_trace':a,'target_trace':b},'certificate':None}
  return {'status':'VALID','contexts_checked':len(cx),'counterexample':None,'certificate':{'source_sha256':ch(s),'target_sha256':ch(t),'model_sha256':mh,'fixture_sha256':fh,'contexts_checked':len(cx)}}
 except (ValueError,KeyError,TypeError) as e: return {'status':'UNKNOWN','contexts_checked':0,'reason':str(e),'counterexample':None,'certificate':None}
def main():
 fp,mp=sys.argv[1:3]; fb=Path(fp).read_bytes(); mb=Path(mp).read_bytes(); f=json.loads(fb); m=json.loads(mb); fh=H(fb); mh=H(mb); by={p['id']:p for p in f['valid']}; good=[]; bad=[]
 for p in f['valid']: good.append({'id':p['id'],**validate(p['source'],p['target'],m,mh,fh)})
 for x in f['mutations']:
  s=by[x['source_id']]['source']; r=validate(s,x['target'],m,mh,fh)
  try:
   code=expand(s['program'],m); nominal={'initial_state':{'active_target':'editor','fresh':True},'transition_after':None,'transition_state':None,'cancel_after':None}
   caught=src(code,nominal)!=tgt(x['target'],nominal)
  except Exception: caught=False
  bad.append({'id':x['id'],**r,'baseline_caught':caught})
 u=f['unknown']; ur=validate(u['source'],u['target'],m,mh,fh)
 gates={'all_valid_accepted':all(x['status']=='VALID' for x in good),'all_mutations_rejected':all(x['status']=='COUNTEREXAMPLE' for x in bad),'baseline_misses_mutation':any(not x['baseline_caught'] for x in bad),'unknown_never_certifies':ur['status']=='UNKNOWN' and ur['certificate'] is None,'certificates_bind_inputs':all(x['certificate'] and x['certificate']['fixture_sha256']==fh and x['certificate']['model_sha256']==mh for x in good)}
 status='PASS_TRANSLATION_VALIDATION_METHOD_SCOPED' if all(gates.values()) else 'METHOD_FAIL_OR_INCONCLUSIVE'
 print(json.dumps({'allocation':'UNJUNO-7827-TV-A01-20261005-01','candidate':'finite_trace_validator_v1','fixture_sha256':fh,'model_sha256':mh,'valid':good,'mutations':bad,'unknown':ur,'gates':gates,'candidate_status':status},sort_keys=True,indent=2))
if __name__=='__main__': main()
