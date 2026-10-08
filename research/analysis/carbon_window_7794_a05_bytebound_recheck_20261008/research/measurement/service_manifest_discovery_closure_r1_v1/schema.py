from __future__ import annotations
import copy, hashlib, json

REQUIRED = (
 'service_identity','protocol_identity','control','observation','operation_schema','capability_snapshot',
 'observation_catalog','events','authority','freshness','handback','fallback'
)
REL = {
 'control':'control','observation':'observation','operation_schema':'operation_schema',
 'capability_snapshot':'capability_snapshot','observation_catalog':'observation_catalog','events':'events'
}
SEM = {'authority':'authority','freshness':'freshness','handback':'handback'}

def reference_manifest():
    return {
      'schema':'agent-interface/service-manifest-r1',
      'service':{'id':'agent-interface'},
      'protocol':{'id':'agent-interface','major':1},
      'relations':{
        'control':'control://session','observation':'observation://session','operation_schema':'schema://operations',
        'capability_snapshot':'cap://session','observation_catalog':'observation://catalog','events':'events://session'
      },
      'semantics':{'authority':'runtime_grant_required','freshness':'generation_bound','handback':'typed_receipt'},
      'fallback':'universal_raw_control'
    }

def canonical_bytes(m):
    return json.dumps(m,sort_keys=True,separators=(',',':')).encode()

def canonical_sha256(m):
    return hashlib.sha256(canonical_bytes(m)).hexdigest()

def _s(x): return isinstance(x,str) and bool(x)

def resolve(m):
    if not isinstance(m,dict): return {'status':'INVALID','errors':['manifest_type'],'values':{}}
    errors=[]; vals={}
    if 'session_capabilities' in m: errors.append('forbidden_session_state')
    service=m.get('service')
    if isinstance(service,dict) and _s(service.get('id')): vals['service_identity']=service['id']
    else: errors.append('service_identity')
    protocol=m.get('protocol')
    if isinstance(protocol,dict) and _s(protocol.get('id')) and isinstance(protocol.get('major'),int):
        if protocol['major']!=1: errors.append('protocol_major')
        else: vals['protocol_identity']=(protocol['id'],protocol['major'])
    else: errors.append('protocol_identity')
    rel=m.get('relations')
    for q,k in REL.items():
        if isinstance(rel,dict) and _s(rel.get(k)): vals[q]=rel[k]
        else: errors.append(q)
    sem=m.get('semantics')
    for q,k in SEM.items():
        if isinstance(sem,dict) and _s(sem.get(k)): vals[q]=sem[k]
        else: errors.append(q)
    if _s(m.get('fallback')): vals['fallback']=m['fallback']
    else: errors.append('fallback')
    status='PASS' if not errors and len(vals)==len(REQUIRED) else 'INVALID'
    return {'status':status,'errors':sorted(set(errors)),'values':vals}

def omit(m,q):
    x=copy.deepcopy(m)
    if q=='service_identity': x['service'].pop('id',None)
    elif q=='protocol_identity': x['protocol'].pop('id',None)
    elif q in REL: x['relations'].pop(REL[q],None)
    elif q in SEM: x['semantics'].pop(SEM[q],None)
    elif q=='fallback': x.pop('fallback',None)
    else: raise KeyError(q)
    return x
