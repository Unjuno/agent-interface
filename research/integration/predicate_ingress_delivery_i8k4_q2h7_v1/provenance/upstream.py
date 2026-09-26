import json, hashlib, sys

SCHEMA='agent-interface/predicate-cache-persist-v1'

def strict_int(x): return type(x) is int and x >= 0

def truth(state, predicate):
    if predicate == 'FORM_READY':
        if not state.get('source_current', False): return 'UNKNOWN'
        return 'TRUE' if state['form_generation'] == state['required_form_generation'] and state['intent'] == 'submit' else 'FALSE'
    raise ValueError('unknown predicate')

def dep_key(state):
    return {
      'form_generation': state['form_generation'],
      'required_form_generation': state['required_form_generation'],
      'intent_version': state['intent_version'],
      'producer_version': state['producer_version'],
      'source_generation': state['source_generation'],
      'source_current': state['source_current'],
      'intent': state['intent'],
    }

def prepare(state, predicate='FORM_READY'):
    value=truth(state,predicate)
    payload={'schema':SCHEMA,'predicate':predicate,'value':value,'key':dep_key(state)}
    body=json.dumps(payload,sort_keys=True,separators=(',',':')).encode()
    payload['digest']=hashlib.sha256(body).hexdigest()
    return payload

def valid_artifact(a):
    if not isinstance(a,dict) or set(a) != {'schema','predicate','value','key','digest'}: return False
    if a['schema']!=SCHEMA or a['predicate']!='FORM_READY' or a['value'] not in {'TRUE','FALSE','UNKNOWN'}: return False
    k=a['key']
    if not isinstance(k,dict) or set(k)!=set(dep_key({'form_generation':0,'required_form_generation':0,'intent_version':0,'producer_version':0,'source_generation':0,'source_current':True,'intent':'submit'})): return False
    for f in ['form_generation','required_form_generation','intent_version','producer_version','source_generation']:
        if not strict_int(k[f]): return False
    if type(k['source_current']) is not bool or k['intent'] not in {'submit','inspect'}: return False
    body=json.dumps({'schema':a['schema'],'predicate':a['predicate'],'value':a['value'],'key':a['key']},sort_keys=True,separators=(',',':')).encode()
    return hashlib.sha256(body).hexdigest()==a['digest']

def consume(policy, artifact, state):
    current=truth(state,'FORM_READY')
    if policy=='VALUE_ONLY_PERSIST':
        if isinstance(artifact,dict) and artifact.get('value') in {'TRUE','FALSE','UNKNOWN'}:
            value=artifact['value']; reused=True; reason='value_only_hit'
        else: value=current; reused=False; reason='recompute'
    elif policy=='DEPENDENCY_BOUND_PERSIST':
        if valid_artifact(artifact) and artifact['key']==dep_key(state):
            value=artifact['value']; reused=True; reason='exact_dependency_hit'
        else:
            value=current; reused=False; reason='recompute_or_refuse_invalid'
    else: raise ValueError(policy)
    executable = (value=='TRUE' and state.get('source_current',False))
    return {'policy':policy,'value':value,'reused':reused,'reason':reason,'oracle':current,'correct':value==current,'executable':executable}

def main():
    req=json.load(sys.stdin)
    if req['op']=='prepare': print(json.dumps(prepare(req['state']),sort_keys=True))
    elif req['op']=='consume': print(json.dumps(consume(req['policy'],req['artifact'],req['state']),sort_keys=True))
    else: raise SystemExit(2)
if __name__=='__main__': main()
